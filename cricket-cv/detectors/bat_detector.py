"""
Bat Detector
------------
Uses YOLOv8 to detect the cricket bat and MediaPipe Pose to refine the
bat region using wrist/hand keypoints. Also detects bat-ball proximity
(contact events).

Output per frame:
    {
        "detected": bool,
        "bbox":     [x1, y1, x2, y2],
        "center":   (cx, cy),
        "conf":     float,
        "contact":  bool,           # True when ball is near bat
        "contact_point": (x, y),    # pixel where contact occurred
    }
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

try:
    import mediapipe as mp
    _MP_AVAILABLE = True
except ImportError:
    _MP_AVAILABLE = False
    mp = None  # type: ignore

from ultralytics import YOLO

logger = logging.getLogger(__name__)

# YOLO class names that correspond to a bat
BAT_CLASS_NAMES = {"bat", "cricket bat"}

# Contact detection: ball centre must be within this many pixels of the bat box
CONTACT_MARGIN_PX = 25

# Drawing colours (BGR)
BOX_COLOR     = (255, 100, 0)    # blue
TEXT_COLOR    = (255, 100, 0)
CONTACT_COLOR = (0, 0, 255)      # red flash on contact

# MediaPipe pose landmark indices for wrist/elbow
_MP_RIGHT_WRIST = 16
_MP_LEFT_WRIST  = 15
_MP_RIGHT_ELBOW = 14
_MP_LEFT_ELBOW  = 13


class BatDetector:
    """
    Detects the cricket bat and ball-bat contact in video frames.

    Args:
        model_path:    YOLOv8 weights for bat detection.
        conf_thresh:   YOLO confidence threshold.
        use_mediapipe: Whether to use MediaPipe Pose to refine bat region.
        contact_margin_px: Pixel tolerance for contact detection.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf_thresh: float = 0.30,
        use_mediapipe: bool = True,
        contact_margin_px: int = CONTACT_MARGIN_PX,
    ) -> None:
        logger.info("Loading YOLO model for bat detection: %s", model_path)
        self.model = YOLO(model_path)
        self.conf_thresh = conf_thresh
        self.contact_margin = contact_margin_px

        self._bat_class_ids: Optional[List[int]] = None

        # MediaPipe Pose (optional refinement)
        self._pose = None
        if use_mediapipe and _MP_AVAILABLE:
            try:
                self._pose = mp.solutions.pose.Pose(  # type: ignore[attr-defined]
                    static_image_mode=False,
                    model_complexity=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                logger.info("MediaPipe Pose loaded for bat refinement.")
            except Exception as exc:
                logger.warning("MediaPipe init failed: %s", exc)
        elif use_mediapipe and not _MP_AVAILABLE:
            logger.warning("MediaPipe not installed. Bat refinement disabled.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect(
        self,
        frame: np.ndarray,
        ball_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Detect bat in frame and check for ball-bat contact.

        Args:
            frame:       BGR image.
            ball_result: Output from BallDetector.detect() (for contact check).

        Returns:
            Detection dict.
        """
        bbox, conf = self._yolo_detect(frame)

        if bbox is None:
            bbox = self._mediapipe_fallback(frame)
            conf = 0.40 if bbox is not None else 0.0

        if bbox is not None:
            # Optionally refine box with pose wrist keypoints
            bbox = self._refine_with_pose(frame, bbox)

        # Contact detection
        contact = False
        contact_point = None
        if bbox is not None and ball_result and ball_result.get("detected"):
            contact, contact_point = self._check_contact(bbox, ball_result["center"])

        if bbox is None:
            return {
                "detected": False,
                "bbox": None,
                "center": None,
                "conf": 0.0,
                "contact": False,
                "contact_point": None,
            }

        x1, y1, x2, y2 = bbox
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0

        return {
            "detected": True,
            "bbox": [float(x1), float(y1), float(x2), float(y2)],
            "center": (float(cx), float(cy)),
            "conf": float(conf),
            "contact": contact,
            "contact_point": contact_point,
        }

    def draw(self, frame: np.ndarray, result: Dict[str, Any]) -> np.ndarray:
        """Draw bat bounding box and contact indicator onto frame."""
        if not result["detected"]:
            return frame

        x1, y1, x2, y2 = [int(v) for v in result["bbox"]]
        color = CONTACT_COLOR if result["contact"] else BOX_COLOR

        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        label = f"Bat {result['conf']:.2f}"
        if result["contact"]:
            label += " CONTACT!"
        cv2.putText(frame, label, (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)

        if result["contact"] and result["contact_point"]:
            cpx, cpy = result["contact_point"]
            cv2.circle(frame, (int(cpx), int(cpy)), 10, CONTACT_COLOR, -1)
            cv2.circle(frame, (int(cpx), int(cpy)), 14, (255, 255, 255), 2)

        return frame

    def close(self) -> None:
        """Release MediaPipe resources."""
        if self._pose is not None:
            self._pose.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_bat_class_ids(self) -> List[int]:
        if self._bat_class_ids is None:
            names = self.model.names
            self._bat_class_ids = [
                idx for idx, name in names.items()
                if name.lower() in BAT_CLASS_NAMES
            ]
            if not self._bat_class_ids:
                # Fine-tuned: assume class 1 is bat
                logger.warning("No bat class found in model names. Defaulting to class 1.")
                self._bat_class_ids = [1]
        return self._bat_class_ids

    def _yolo_detect(self, frame: np.ndarray) -> Tuple[Optional[List[float]], float]:
        """Run YOLO and return best bat bbox + confidence."""
        bat_ids = self._get_bat_class_ids()
        results = self.model(frame, verbose=False, conf=self.conf_thresh)[0]

        best_conf = 0.0
        best_bbox = None
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in bat_ids:
                continue
            conf = float(box.conf[0])
            if conf > best_conf:
                best_conf = conf
                best_bbox = box.xyxy[0].tolist()

        return best_bbox, best_conf

    def _mediapipe_fallback(self, frame: np.ndarray) -> Optional[List[float]]:
        """
        Use MediaPipe Pose wrist landmarks to estimate bat region when YOLO fails.
        The bat is held in the hands, so we expand the wrist keypoint into a box.
        """
        if self._pose is None:
            return None

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._pose.process(rgb)

        if results.pose_landmarks is None:
            return None

        lm = results.pose_landmarks.landmark
        wrists = [lm[_MP_RIGHT_WRIST], lm[_MP_LEFT_WRIST]]

        # Pick the wrist that is lower in the frame (bat side)
        visible = [w_lm for w_lm in wrists if w_lm.visibility > 0.5]
        if not visible:
            return None

        best_wrist = max(visible, key=lambda l: l.y)  # lower = higher y
        wx = best_wrist.x * w
        wy = best_wrist.y * h

        # Bat is roughly 60×20 cm; approximate as 120×40 px at typical broadcast scale
        pad_x, pad_y = 60, 120
        return [
            max(0, wx - pad_x),
            max(0, wy - pad_y),
            min(w, wx + pad_x),
            min(h, wy + pad_y * 2),
        ]

    def _refine_with_pose(
        self,
        frame: np.ndarray,
        bbox: List[float],
    ) -> List[float]:
        """
        Expand the YOLO bat box to include the nearest wrist keypoint if MediaPipe
        is available and the wrist is outside the current box.
        """
        if self._pose is None:
            return bbox

        h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._pose.process(rgb)

        if results.pose_landmarks is None:
            return bbox

        lm = results.pose_landmarks.landmark
        x1, y1, x2, y2 = bbox

        for wrist_idx in [_MP_RIGHT_WRIST, _MP_LEFT_WRIST]:
            wlm = lm[wrist_idx]
            if wlm.visibility < 0.5:
                continue
            wx, wy = wlm.x * w, wlm.y * h
            # If wrist is close to the bat box, expand the box to include it
            if (x1 - 40 < wx < x2 + 40) and (y1 - 40 < wy < y2 + 40):
                x1 = min(x1, wx - 10)
                y1 = min(y1, wy - 10)
                x2 = max(x2, wx + 10)
                y2 = max(y2, wy + 10)

        return [x1, y1, x2, y2]

    def _check_contact(
        self,
        bat_bbox: List[float],
        ball_center: Optional[Tuple[float, float]],
    ) -> Tuple[bool, Optional[Tuple[float, float]]]:
        """
        Check if the ball centre is within (or very close to) the bat bounding box.

        Returns (contact_bool, contact_point).
        """
        if ball_center is None:
            return False, None

        bx, by = ball_center
        x1, y1, x2, y2 = bat_bbox
        margin = self.contact_margin

        inside_x = (x1 - margin) <= bx <= (x2 + margin)
        inside_y = (y1 - margin) <= by <= (y2 + margin)

        if inside_x and inside_y:
            # Clamp contact point to bat bbox boundary
            cpx = max(x1, min(x2, bx))
            cpy = max(y1, min(y2, by))
            return True, (cpx, cpy)

        return False, None
