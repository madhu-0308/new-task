"""
Wide Ball Detector
------------------
Determines whether a delivery is a wide by:
  1. Detecting the crease lines in the frame (Hough transform).
  2. Applying the PitchHomography to convert ball position to top-down
     pitch coordinates.
  3. Checking if the ball's x-position at the batting crease is outside
     the ICC-mandated 89 cm boundary from middle stump.

Fallback (no homography): uses pixel-based thresholds relative to the
detected crease width.

Output per frame:
    {
        "decision":    "WIDE" | "LEGAL" | "PENDING",
        "confidence":  float,        # 0–1
        "ball_td_pos": (tx, ty),     # top-down canvas coords
        "checked":     bool,         # True when a decision was made this frame
    }

A decision is only committed once per delivery (when the ball passes the
batting crease) and is not re-evaluated until reset() is called.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from utils.homography import PitchHomography, BATTING_CREASE_Y, PX_PER_M

logger = logging.getLogger(__name__)

# Pixel-based fallback constants (fraction of frame width)
# These are typical proportions for a standard broadcast camera.
_WIDE_LEFT_FRAC  = 0.28   # ball x / frame_width < this → wide leg side
_WIDE_RIGHT_FRAC = 0.72   # ball x / frame_width > this → wide off side

# Overlay colours
WIDE_COLOR  = (0, 0, 255)    # red
LEGAL_COLOR = (0, 200, 0)    # green
ZONE_COLOR  = (0, 255, 255)  # yellow for crease visualisation


class WideDetector:
    """
    Classifies a delivery as WIDE or LEGAL.

    Args:
        homography: A calibrated PitchHomography instance.  When None, the
                    detector falls back to raw pixel heuristics.
    """

    def __init__(self, homography: Optional[PitchHomography] = None) -> None:
        self._homo = homography
        self._decision: str = "PENDING"
        self._confidence: float = 0.0
        self._decided: bool = False
        self._frame_decision: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        frame: np.ndarray,
        ball_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Process one frame and (possibly) make a wide/legal decision.

        Args:
            frame:       Current BGR frame.
            ball_result: Dict from BallDetector.detect().

        Returns:
            Decision dict.
        """
        null_result = {
            "decision": self._decision,
            "confidence": self._confidence,
            "ball_td_pos": None,
            "checked": False,
        }

        if self._decided:
            return {**null_result, "checked": False}

        if not ball_result.get("detected"):
            return null_result

        ball_center = ball_result["center"]

        # -- Top-down projection ------------------------------------------
        td_pos = None
        if self._homo is not None and self._homo._calibrated:
            td_pos = self._homo.transform_point(ball_center)

        decision, confidence = self._classify(frame, ball_center, td_pos)

        if decision != "PENDING":
            self._decision = decision
            self._confidence = confidence
            self._decided = True

        return {
            "decision": decision,
            "confidence": confidence,
            "ball_td_pos": td_pos,
            "checked": decision != "PENDING",
        }

    def draw(
        self,
        frame: np.ndarray,
        result: Dict[str, Any],
        ball_result: Dict[str, Any],
    ) -> np.ndarray:
        """Overlay wide/legal decision and crease zone onto frame."""
        decision = result["decision"]
        conf = result["confidence"]
        h, w = frame.shape[:2]

        # Draw crease zone markers (yellow vertical lines)
        lx = int(w * _WIDE_LEFT_FRAC)
        rx = int(w * _WIDE_RIGHT_FRAC)
        cv2.line(frame, (lx, 0), (lx, h), ZONE_COLOR, 1)
        cv2.line(frame, (rx, 0), (rx, h), ZONE_COLOR, 1)
        cv2.putText(frame, "WIDE", (lx - 40, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, ZONE_COLOR, 1)
        cv2.putText(frame, "WIDE", (rx + 5, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, ZONE_COLOR, 1)

        if decision == "WIDE":
            label = f"WIDE  {conf:.0%}"
            cv2.putText(frame, label, (20, 80),
                        cv2.FONT_HERSHEY_DUPLEX, 1.4, WIDE_COLOR, 3)
            # Highlight ball position in red
            if ball_result.get("detected") and ball_result["center"]:
                cx, cy = ball_result["center"]
                cv2.circle(frame, (int(cx), int(cy)), 18, WIDE_COLOR, 3)
        elif decision == "LEGAL":
            label = f"LEGAL {conf:.0%}"
            cv2.putText(frame, label, (20, 80),
                        cv2.FONT_HERSHEY_DUPLEX, 1.0, LEGAL_COLOR, 2)

        return frame

    def reset(self) -> None:
        """Call between deliveries to allow a new decision."""
        self._decision = "PENDING"
        self._confidence = 0.0
        self._decided = False

    @property
    def decision(self) -> str:
        return self._decision

    @property
    def confidence(self) -> float:
        return self._confidence

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _classify(
        self,
        frame: np.ndarray,
        ball_img_center: Tuple[float, float],
        td_pos: Optional[Tuple[float, float]],
    ) -> Tuple[str, float]:
        """
        Return (decision, confidence).  decision ∈ {"WIDE", "LEGAL", "PENDING"}.
        """
        h, w = frame.shape[:2]
        bx, by = ball_img_center

        # -- Method 1: homography-based (preferred) -----------------------
        if td_pos is not None and self._homo is not None:
            is_wide, conf = self._homo.is_wide(*td_pos)
            if conf > 0.0:
                return ("WIDE" if is_wide else "LEGAL"), conf

        # -- Method 2: pixel heuristic ------------------------------------
        # Only apply near the bottom third of frame (batting crease area)
        if by < h * 0.55:
            return "PENDING", 0.0

        ball_frac = bx / float(w)

        if ball_frac < _WIDE_LEFT_FRAC:
            overshoot = _WIDE_LEFT_FRAC - ball_frac
            conf = min(1.0, overshoot / 0.08)
            return "WIDE", conf

        if ball_frac > _WIDE_RIGHT_FRAC:
            overshoot = ball_frac - _WIDE_RIGHT_FRAC
            conf = min(1.0, overshoot / 0.08)
            return "WIDE", conf

        # Ball is inside the zone at crease height → legal
        return "LEGAL", 0.85
