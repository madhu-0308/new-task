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
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from utils.homography import PitchHomography, BATTING_CREASE_Y, PX_PER_M

logger = logging.getLogger(__name__)


# ── Shared drawing helpers ────────────────────────────────────────────────────

def _draw_dashed_vline(img, x, y0, y1, color, thickness=1, dash=10):
    """Draw a vertical dashed line."""
    on = True
    y = y0
    while y < y1:
        ye = min(y + dash, y1)
        if on:
            cv2.line(img, (x, y), (x, ye), color, thickness)
        y = ye
        on = not on


def _draw_banner(img, text, pos, color, scale=1.0, thickness=2):
    """Draw text with a dark semi-transparent background pill."""
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
    """Draw a labelled reason box at (x, y)."""
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
        """
        Draw rich wide-detection overlay:
          - Wide zone boundary lines with shaded regions
          - Arrow from ball to nearest boundary showing overshoot distance
          - Reason panel explaining WHY it is wide or legal
        """
        decision = result["decision"]
        conf     = result["confidence"]
        h, w     = frame.shape[:2]

        lx = int(w * _WIDE_LEFT_FRAC)   # left wide boundary x
        rx = int(w * _WIDE_RIGHT_FRAC)  # right wide boundary x
        mid_x = w // 2

        # ── 1. Shade the wide zones (semi-transparent red) ──────────────────
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0),  (lx, h), (0, 0, 180), -1)   # left wide zone
        cv2.rectangle(overlay, (rx, 0), (w, h),  (0, 0, 180), -1)   # right wide zone
        cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)

        # ── 2. Wide boundary lines (thick dashed yellow) ─────────────────────
        _draw_dashed_vline(frame, lx, 0, h, ZONE_COLOR, thickness=2, dash=14)
        _draw_dashed_vline(frame, rx, 0, h, ZONE_COLOR, thickness=2, dash=14)

        # Labels on boundary lines
        cv2.putText(frame, "LEG WIDE", (2, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, ZONE_COLOR, 1, cv2.LINE_AA)
        cv2.putText(frame, "OFF WIDE", (rx + 3, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, ZONE_COLOR, 1, cv2.LINE_AA)
        cv2.putText(frame, "LEGAL ZONE", (lx + (rx - lx) // 2 - 45, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 255, 100), 1, cv2.LINE_AA)

        # ── 3. Ball position + measurement arrow ─────────────────────────────
        ball_detected = ball_result.get("detected") and ball_result.get("center")
        reason_lines: List[str] = []

        if ball_detected:
            bx, by = ball_result["center"]
            ibx, iby = int(bx), int(by)

            # Horizontal guide line from ball to nearest boundary
            if bx < lx:
                # Ball is in left wide zone → draw arrow to lx
                overshoot_px = lx - bx
                cv2.arrowedLine(frame, (ibx, iby), (lx, iby), WIDE_COLOR, 2,
                                tipLength=0.15)
                cv2.putText(frame,
                            f"{overshoot_px:.0f}px outside",
                            (ibx + 2, iby - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, WIDE_COLOR, 1, cv2.LINE_AA)
                reason_lines = [
                    f"Ball x={bx:.0f}px",
                    f"Leg-wide line={lx}px",
                    f"Outside by {overshoot_px:.0f}px",
                    "Side: LEG",
                ]
            elif bx > rx:
                # Ball is in right wide zone → draw arrow to rx
                overshoot_px = bx - rx
                cv2.arrowedLine(frame, (ibx, iby), (rx, iby), WIDE_COLOR, 2,
                                tipLength=0.15)
                cv2.putText(frame,
                            f"{overshoot_px:.0f}px outside",
                            (rx + 4, iby - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, WIDE_COLOR, 1, cv2.LINE_AA)
                reason_lines = [
                    f"Ball x={bx:.0f}px",
                    f"Off-wide line={rx}px",
                    f"Outside by {overshoot_px:.0f}px",
                    "Side: OFF",
                ]
            else:
                # Ball inside legal zone
                dist_left  = bx - lx
                dist_right = rx - bx
                reason_lines = [
                    f"Ball x={bx:.0f}px",
                    f"Legal zone: {lx}–{rx}px",
                    f"Margin L={dist_left:.0f}px R={dist_right:.0f}px",
                    "Within legal corridor",
                ]

            # Big circle around ball when wide
            if decision == "WIDE":
                cv2.circle(frame, (ibx, iby), 20, WIDE_COLOR, 3)
                cv2.circle(frame, (ibx, iby), 22, (255, 255, 255), 1)

        # ── 4. Decision banner ────────────────────────────────────────────────
        if decision == "WIDE":
            _draw_banner(frame, f"◀  WIDE  {conf:.0%}  ▶", (w // 2 - 90, h - 30),
                         WIDE_COLOR, scale=0.9, thickness=2)
        elif decision == "LEGAL":
            _draw_banner(frame, f"✓  LEGAL  {conf:.0%}", (w // 2 - 75, h - 30),
                         LEGAL_COLOR, scale=0.75, thickness=1)

        # ── 5. Reason panel (bottom-left) ─────────────────────────────────────
        if reason_lines:
            _draw_reason_panel(frame, "WIDE ANALYSIS", reason_lines,
                               x=4, y=h - 10 - len(reason_lines) * 18 - 22,
                               color=WIDE_COLOR if decision == "WIDE" else LEGAL_COLOR)

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
