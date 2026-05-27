"""
No-Ball Detector
----------------
Determines whether a delivery is a no-ball by checking if the bowler's
front foot has crossed the popping crease at the moment of release.

Two-tier approach:
  Tier 1 (MediaPipe Pose): Detects front foot keypoints (ankle/heel/toe)
          and checks if any point is beyond the popping crease line.
  Tier 2 (pixel subtraction): When pose is unavailable, detect foot
          motion in the popping crease ROI using background subtraction.

Crease line detection:
  The popping crease ROI is taken as a horizontal band in the upper
  portion of the frame (bowler's end — top half for typical broadcast).

Output per frame:
    {
        "decision":    "NO BALL" | "LEGAL" | "PENDING",
        "confidence":  float,
        "method":      "pose" | "pixel" | "none",
        "foot_pts":    [(x, y), ...],   # detected foot keypoints
        "crease_y":    int,             # y-coordinate of popping crease
        "checked":     bool,
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

logger = logging.getLogger(__name__)


# ── Shared drawing helpers ────────────────────────────────────────────────────

def _draw_dashed_hline(img, y, x0, x1, color, thickness=1, dash=10):
    """Draw a horizontal dashed line."""
    on = True
    x = x0
    while x < x1:
        xe = min(x + dash, x1)
        if on:
            cv2.line(img, (x, y), (xe, y), color, thickness)
        x = xe
        on = not on


def _draw_banner(img, text, pos, color, scale=1.0, thickness=2):
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, scale, thickness)
    x, y = pos
    pad = 6
    overlay = img.copy()
    cv2.rectangle(overlay, (x - pad, y - th - pad), (x + tw + pad, y + pad),
                  (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, img, 0.45, 0, img)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, scale, color,
                thickness, cv2.LINE_AA)


def _draw_reason_panel(img, title: str, lines: List[str], x: int, y: int,
                       color=(0, 255, 255)):
    line_h = 18
    panel_h = len(lines) * line_h + 26
    panel_w = 220
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + panel_w, y + panel_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.65, img, 0.35, 0, img)
    cv2.rectangle(img, (x, y), (x + panel_w, y + panel_h), color, 1)
    cv2.putText(img, title, (x + 4, y + 14),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    cv2.line(img, (x, y + 18), (x + panel_w, y + 18), color, 1)
    for i, line in enumerate(lines):
        cv2.putText(img, line, (x + 4, y + 18 + (i + 1) * line_h),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1, cv2.LINE_AA)


# Overlay colours
NOBALL_COLOR = (0, 0, 255)    # red
LEGAL_COLOR  = (0, 200, 0)    # green
CREASE_COLOR = (0, 255, 255)  # yellow

# MediaPipe Pose landmark indices for feet / ankles
_RIGHT_HEEL      = 30
_LEFT_HEEL       = 29
_RIGHT_ANKLE     = 28
_LEFT_ANKLE      = 27
_RIGHT_FOOT_INDEX = 32
_LEFT_FOOT_INDEX  = 31
_FRONT_FOOT_LMS  = [_RIGHT_HEEL, _LEFT_HEEL,
                    _RIGHT_ANKLE, _LEFT_ANKLE,
                    _RIGHT_FOOT_INDEX, _LEFT_FOOT_INDEX]

# Pixel subtraction parameters
_MOG2_HISTORY    = 200
_MOG2_THRESHOLD  = 40
_MIN_FOOT_AREA   = 500      # px² — minimum blob area to qualify as a foot

# Popping crease is in the upper portion of the frame (bowler's end)
_CREASE_Y_FRAC   = 0.35     # crease is at ~35% height in broadcast view
_CREASE_BAND_H   = 30       # pixel height of the crease ROI


class NoBallDetector:
    """
    Detects no-balls by checking if the bowler's front foot crosses the popping crease.

    Args:
        use_mediapipe:     Use MediaPipe Pose (Tier 1).
        use_pixel_fallback: Use background subtraction fallback (Tier 2).
    """

    def __init__(
        self,
        use_mediapipe: bool = True,
        use_pixel_fallback: bool = True,
    ) -> None:
        self._pose = None
        if use_mediapipe and _MP_AVAILABLE:
            try:
                self._pose = mp.solutions.pose.Pose(  # type: ignore[attr-defined]
                    static_image_mode=False,
                    model_complexity=1,
                    min_detection_confidence=0.5,
                    min_tracking_confidence=0.5,
                )
                logger.info("MediaPipe Pose loaded for no-ball detection.")
            except Exception as exc:
                logger.warning("MediaPipe Pose init failed: %s", exc)
        elif use_mediapipe and not _MP_AVAILABLE:
            logger.warning("MediaPipe not installed. No-ball pose detection disabled.")

        # Background subtractor for pixel fallback
        self._bg_subtractor = None
        if use_pixel_fallback:
            self._bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                history=_MOG2_HISTORY,
                varThreshold=_MOG2_THRESHOLD,
                detectShadows=False,
            )

        self._decision: str = "PENDING"
        self._confidence: float = 0.0
        self._decided: bool = False
        self._detected_crease_y: Optional[int] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        frame: np.ndarray,
        ball_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Analyse one frame for a no-ball condition.

        The check is triggered once the ball has been detected leaving the
        hand (ball detected, moving upward/forward) — approximated here
        by ball being in the upper half of the frame.

        Args:
            frame:       BGR frame.
            ball_result: BallDetector result.

        Returns:
            Decision dict.
        """
        null_result: Dict[str, Any] = {
            "decision": self._decision,
            "confidence": self._confidence,
            "method": "none",
            "foot_pts": [],
            "crease_y": self._detected_crease_y,
            "checked": False,
        }

        if self._decided:
            return null_result

        h, w = frame.shape[:2]

        # Estimate popping crease y from Hough lines or fall back to fraction
        crease_y = self._detect_crease_y(frame)
        if crease_y is None:
            crease_y = int(h * _CREASE_Y_FRAC)
        self._detected_crease_y = crease_y

        # Only trigger when the ball is near the delivery stride area
        ball_in_range = False
        if ball_result.get("detected") and ball_result["center"]:
            _, by = ball_result["center"]
            ball_in_range = by < h * 0.6   # ball in upper/mid frame

        if not ball_in_range:
            return null_result

        # --- Tier 1: MediaPipe Pose ---
        foot_pts, decision, conf, method = self._pose_check(frame, crease_y, w, h)
        if decision != "PENDING":
            self._decision = decision
            self._confidence = conf
            self._decided = True
            return {
                "decision": decision,
                "confidence": conf,
                "method": method,
                "foot_pts": foot_pts,
                "crease_y": crease_y,
                "checked": True,
            }

        # --- Tier 2: Pixel subtraction fallback ---
        decision, conf = self._pixel_check(frame, crease_y, h, w)
        if decision != "PENDING":
            self._decision = decision
            self._confidence = conf
            self._decided = True
            return {
                "decision": decision,
                "confidence": conf,
                "method": "pixel",
                "foot_pts": [],
                "crease_y": crease_y,
                "checked": True,
            }

        return {**null_result, "crease_y": crease_y}

    def draw(self, frame: np.ndarray, result: Dict[str, Any]) -> np.ndarray:
        """
        Draw rich no-ball overlay:
          - Popping crease line (dashed yellow) with safe/danger zones
          - Foot keypoints with violation arrows
          - Reason panel explaining WHY it is no-ball or legal
          - Method used (pose / pixel subtraction)
        """
        decision  = result["decision"]
        conf      = result["confidence"]
        method    = result.get("method", "none")
        crease_y  = result.get("crease_y")
        foot_pts  = result.get("foot_pts", [])
        h, w      = frame.shape[:2]

        if crease_y is None:
            crease_y = int(h * _CREASE_Y_FRAC)

        # ── 1. Shade danger zone (below crease = bowler side) ────────────────
        overlay = frame.copy()
        # Green above crease = safe (behind crease)
        cv2.rectangle(overlay, (0, 0), (w, crease_y), (0, 120, 0), -1)
        # Red below crease = danger zone
        cv2.rectangle(overlay, (0, crease_y), (w, min(h, crease_y + 60)),
                      (0, 0, 150), -1)
        cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

        # ── 2. Popping crease line (dashed yellow) ────────────────────────────
        _draw_dashed_hline(frame, crease_y, 0, w, CREASE_COLOR, thickness=2, dash=16)
        # Label
        cv2.putText(frame, "POPPING CREASE", (w // 2 - 70, crease_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, CREASE_COLOR, 1, cv2.LINE_AA)
        cv2.putText(frame, "SAFE (behind)", (4, crease_y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (100, 255, 100), 1, cv2.LINE_AA)
        cv2.putText(frame, "DANGER (overstepped)", (4, crease_y + 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, NOBALL_COLOR, 1, cv2.LINE_AA)

        # ── 3. Foot keypoints + violation arrows ──────────────────────────────
        reason_lines: List[str] = []
        max_violation_px = 0.0
        method_label = {"pose": "MediaPipe Pose", "pixel": "Pixel Subtraction",
                        "none": "—"}.get(method, method)

        if foot_pts:
            for pt in foot_pts:
                px, py = int(pt[0]), int(pt[1])
                violation = py - crease_y
                if violation > 0:
                    # Foot past crease → red circle + downward arrow to show depth
                    cv2.circle(frame, (px, py), 9, NOBALL_COLOR, -1)
                    cv2.circle(frame, (px, py), 11, (255, 255, 255), 1)
                    # Arrow from crease down to foot
                    cv2.arrowedLine(frame, (px, crease_y), (px, py),
                                    NOBALL_COLOR, 2, tipLength=0.25)
                    cv2.putText(frame, f"+{violation:.0f}px",
                                (px + 5, (crease_y + py) // 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.38, NOBALL_COLOR, 1, cv2.LINE_AA)
                    max_violation_px = max(max_violation_px, violation)
                else:
                    # Foot behind crease → green circle
                    cv2.circle(frame, (px, py), 7, (0, 220, 0), -1)

            if max_violation_px > 0:
                reason_lines = [
                    f"Foot crossed crease",
                    f"Overstep: {max_violation_px:.0f}px",
                    f"Method: {method_label}",
                    f"Conf: {conf:.0%}",
                ]
            else:
                reason_lines = [
                    "Foot behind crease",
                    f"Method: {method_label}",
                    f"Conf: {conf:.0%}",
                ]
        else:
            if decision == "NO BALL":
                reason_lines = [
                    "Motion in crease ROI",
                    f"Method: {method_label}",
                    f"Blob area > threshold",
                    f"Conf: {conf:.0%}",
                ]
            elif decision == "LEGAL":
                reason_lines = [
                    "No foot overstepping",
                    f"Method: {method_label}",
                    f"Conf: {conf:.0%}",
                ]

        # ── 4. Decision banner ────────────────────────────────────────────────
        if decision == "NO BALL":
            # Red flashing bar along crease
            cv2.rectangle(frame, (0, crease_y - 3), (w, crease_y + 3),
                          NOBALL_COLOR, -1)
            _draw_banner(frame, f"NO BALL  {conf:.0%}",
                         (w // 2 - 80, crease_y - 14),
                         NOBALL_COLOR, scale=0.85, thickness=2)
        elif decision == "LEGAL":
            _draw_banner(frame, f"✓ LEGAL  {conf:.0%}",
                         (w // 2 - 70, crease_y - 14),
                         LEGAL_COLOR, scale=0.72, thickness=1)

        # ── 5. Reason panel (top-right) ───────────────────────────────────────
        if reason_lines:
            panel_color = NOBALL_COLOR if decision == "NO BALL" else (
                LEGAL_COLOR if decision == "LEGAL" else CREASE_COLOR)
            _draw_reason_panel(frame, "NO-BALL ANALYSIS", reason_lines,
                               x=w - 224, y=4, color=panel_color)

        return frame

    def reset(self) -> None:
        """Call between deliveries."""
        self._decision = "PENDING"
        self._confidence = 0.0
        self._decided = False

    @property
    def decision(self) -> str:
        return self._decision

    def close(self) -> None:
        if self._pose is not None:
            self._pose.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_crease_y(self, frame: np.ndarray) -> Optional[int]:
        """
        Detect the popping crease y-position using Hough lines in the
        upper half of the frame.
        """
        h, w = frame.shape[:2]
        roi = frame[:h // 2, :]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        edges = cv2.Canny(thresh, 50, 150, apertureSize=3)

        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180, threshold=60,
            minLineLength=w // 4, maxLineGap=20,
        )
        if lines is None:
            return None

        # Collect horizontal lines
        y_vals = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
            if angle < 10 or angle > 170:
                y_vals.append((y1 + y2) / 2.0)

        if not y_vals:
            return None

        # Return the lowest horizontal line in the upper half
        return int(max(y_vals))

    def _pose_check(
        self,
        frame: np.ndarray,
        crease_y: int,
        w: int,
        h: int,
    ) -> Tuple[List[Tuple[float, float]], str, float, str]:
        """
        Use MediaPipe to check if any front foot keypoint is below the crease.

        A foot "below" (in y) the crease line means it has crossed into the
        batting crease side → no-ball condition.

        Returns: (foot_pts, decision, confidence, method)
        """
        if self._pose is None:
            return [], "PENDING", 0.0, "none"

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._pose.process(rgb)

        if results.pose_landmarks is None:
            return [], "PENDING", 0.0, "none"

        lm = results.pose_landmarks.landmark
        foot_pts: List[Tuple[float, float]] = []
        max_violation = 0.0   # how far beyond the crease (in px)

        for lm_idx in _FRONT_FOOT_LMS:
            landmark = lm[lm_idx]
            if landmark.visibility < 0.4:
                continue
            px = landmark.x * w
            py = landmark.y * h
            foot_pts.append((px, py))
            violation = py - crease_y   # positive = past the crease
            if violation > 0:
                max_violation = max(max_violation, violation)

        if not foot_pts:
            return [], "PENDING", 0.0, "none"

        if max_violation > 5:
            conf = min(1.0, max_violation / 40.0)
            return foot_pts, "NO BALL", conf, "pose"

        if max_violation <= 0 and foot_pts:
            # All foot points are clearly behind the crease
            return foot_pts, "LEGAL", 0.90, "pose"

        return foot_pts, "PENDING", 0.0, "none"

    def _pixel_check(
        self,
        frame: np.ndarray,
        crease_y: int,
        h: int,
        w: int,
    ) -> Tuple[str, float]:
        """
        Background-subtraction pixel fallback.
        Detect moving foreground blobs below the crease line.
        """
        if self._bg_subtractor is None:
            return "PENDING", 0.0

        # ROI: band just below the crease line
        y_start = crease_y
        y_end   = min(h, crease_y + _CREASE_BAND_H)
        roi = frame[y_start:y_end, :]

        fg_mask = self._bg_subtractor.apply(roi)

        # Remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.dilate(fg_mask, kernel, iterations=2)

        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > _MIN_FOOT_AREA:
                conf = min(1.0, area / (_MIN_FOOT_AREA * 4))
                return "NO BALL", conf

        return "PENDING", 0.0
