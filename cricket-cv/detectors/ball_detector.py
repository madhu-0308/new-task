"""
Ball Detector
-------------
Uses YOLOv8 to detect the cricket ball in each video frame and SORT to
maintain a persistent track ID across frames. Draws a green bounding box
and a trajectory trail on the ball.

Output per frame:
    {
        "detected": bool,
        "bbox":     [x1, y1, x2, y2],   # in image pixels
        "center":   (cx, cy),            # centre of ball
        "track_id": int,
        "conf":     float,
        "trail":    [(cx, cy), ...],     # last N positions
    }
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

from utils.tracker import Sort

logger = logging.getLogger(__name__)

# YOLO class names that correspond to a ball
BALL_CLASS_NAMES = {"ball", "cricket ball", "sports ball"}

# Colours (BGR)
BOX_COLOR   = (0, 255, 0)     # green
TEXT_COLOR  = (0, 255, 0)
TRAIL_COLOR = (0, 200, 100)

TRAIL_LEN   = 30   # number of frames to draw trail


class BallDetector:
    """
    Detects and tracks the cricket ball in video frames.

    Args:
        model_path: Path to a YOLOv8 weights file (.pt).
                    Defaults to 'yolov8n.pt' (downloads if not present).
        conf_thresh: Minimum detection confidence.
        trail_len:   Number of past positions kept for the trajectory trail.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf_thresh: float = 0.30,
        trail_len: int = TRAIL_LEN,
    ) -> None:
        logger.info("Loading YOLO model for ball detection: %s", model_path)
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh

        # SORT tracker — tuned for a fast, small object
        self.tracker = Sort(max_age=8, min_hits=2, iou_threshold=0.15)

        # Ring buffer of (cx, cy) for the trajectory trail
        self.trail: deque = deque(maxlen=trail_len)

        # Map YOLO class-index → class name for the loaded model
        self._ball_class_ids: Optional[List[int]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Run ball detection + tracking on a single frame.

        Args:
            frame: BGR image (H, W, 3).

        Returns:
            Dictionary with detection results.
        """
        dets = self._run_yolo(frame)
        tracks = self.tracker.update(dets)

        if len(tracks) == 0:
            return {
                "detected": False,
                "bbox": None,
                "center": None,
                "track_id": None,
                "conf": 0.0,
                "trail": list(self.trail),
            }

        # Pick the track with highest confidence (first row = best IoU match)
        best = tracks[0]
        x1, y1, x2, y2, track_id = best
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        self.trail.append((cx, cy))

        return {
            "detected": True,
            "bbox": [float(x1), float(y1), float(x2), float(y2)],
            "center": (float(cx), float(cy)),
            "track_id": int(track_id),
            "conf": float(dets[0, 4]) if len(dets) > 0 else 0.0,
            "trail": list(self.trail),
        }

    def draw(self, frame: np.ndarray, result: Dict[str, Any]) -> np.ndarray:
        """
        Draw ball bounding box and trajectory trail onto a frame.

        Args:
            frame:  BGR image to draw on (in-place).
            result: Dict returned by `detect()`.

        Returns:
            Annotated frame.
        """
        # Draw trajectory trail (fading green dots)
        trail = result.get("trail", [])
        for i, pt in enumerate(trail):
            alpha = (i + 1) / max(len(trail), 1)
            radius = max(2, int(4 * alpha))
            color = tuple(int(c * alpha) for c in TRAIL_COLOR)
            cv2.circle(frame, (int(pt[0]), int(pt[1])), radius, color, -1)

        if result["detected"]:
            x1, y1, x2, y2 = [int(v) for v in result["bbox"]]
            tid = result["track_id"]

            cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)
            label = f"Ball #{tid} {result['conf']:.2f}"
            cv2.putText(frame, label, (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, TEXT_COLOR, 2)

            # Draw centre dot
            cx, cy = result["center"]
            cv2.circle(frame, (int(cx), int(cy)), 4, BOX_COLOR, -1)

        return frame

    def reset(self) -> None:
        """Reset tracker and trail (call between deliveries)."""
        self.tracker.reset()
        self.trail.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_ball_class_ids(self) -> List[int]:
        """Lazily resolve which YOLO class indices correspond to the ball."""
        if self._ball_class_ids is None:
            names = self.model.names  # {0: 'person', 1: 'ball', ...}
            self._ball_class_ids = [
                idx for idx, name in names.items()
                if name.lower() in BALL_CLASS_NAMES
            ]
            if not self._ball_class_ids:
                # Fine-tuned model: assume class 0 is the ball
                logger.warning(
                    "No ball class found in YOLO model names %s. "
                    "Defaulting to class 0.",
                    names,
                )
                self._ball_class_ids = [0]
        return self._ball_class_ids

    def _run_yolo(self, frame: np.ndarray) -> np.ndarray:
        """
        Run YOLOv8 inference and return detections as (N, 5) array
        [[x1, y1, x2, y2, score], ...].
        """
        ball_ids = self._get_ball_class_ids()
        results = self.model(frame, verbose=False, conf=self.conf_thresh)[0]

        dets: List[List[float]] = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in ball_ids:
                continue
            conf = float(box.conf[0])
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            dets.append([x1, y1, x2, y2, conf])

        if dets:
            return np.array(dets, dtype=float)

        # Fallback: use color-based Hough circle detection for small ball
        return self._hough_circle_fallback(frame)

    def _hough_circle_fallback(self, frame: np.ndarray) -> np.ndarray:
        """
        Colour + Hough-circle based ball detection when YOLO misses.
        Looks for small reddish/white circles in the frame.
        """
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=4,
            maxRadius=30,
        )

        if circles is None:
            return np.empty((0, 5))

        dets = []
        for cx, cy, r in circles[0]:
            x1 = max(0, cx - r)
            y1 = max(0, cy - r)
            x2 = min(w, cx + r)
            y2 = min(h, cy + r)
            dets.append([x1, y1, x2, y2, 0.35])  # low confidence for fallback

        return np.array(dets[:1], dtype=float)  # take only best candidate
