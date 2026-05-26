"""
Homography utilities for cricket pitch analysis.
--------------------------------------------------
Computes a perspective transform (homography) from the camera image to
a bird's-eye top-down view of the pitch so that distances in the
transformed frame correspond to real-world ICC pitch dimensions.

ICC pitch reference dimensions
-------------------------------
  Pitch length  : 20.12 m  (22 yards)
  Pitch width   : 3.05  m  (10 feet)
  Popping crease: 1.22  m  in front of stumps (each end)
  Bowling crease: at the stumps
  Wide zone     : 89 cm from middle stump (each side) at batting crease
                  → total wide corridor = 178 cm between inner boundary lines

Coordinate convention in the top-down view:
  (0, 0) = top-left of the padded output canvas
  x-axis → across pitch width
  y-axis ↓ along pitch length (bowler → batsman)
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# ICC pitch dimensions (metres → scaled to pixels in top-down view)
# --------------------------------------------------------------------------
PITCH_LENGTH_M: float = 20.12   # end to end (stump to stump)
PITCH_WIDTH_M: float = 3.05
POPPING_CREASE_OFFSET_M: float = 1.22  # in front of batting stumps
WIDE_HALF_WIDTH_M: float = 0.89        # from middle stump to inner wide line

# Top-down canvas pixel dimensions (scale: 50 px / metre)
PX_PER_M: float = 50.0
CANVAS_W: int = int(PITCH_WIDTH_M * PX_PER_M) + 100   # padding
CANVAS_H: int = int(PITCH_LENGTH_M * PX_PER_M) + 100  # padding
CANVAS_ORIGIN_X: int = 50   # left padding
CANVAS_ORIGIN_Y: int = 50   # top padding

# Wide zone boundaries in top-down canvas pixels (from centre)
MID_X: float = CANVAS_ORIGIN_X + (PITCH_WIDTH_M / 2.0) * PX_PER_M
WIDE_LEFT_X: float  = MID_X - WIDE_HALF_WIDTH_M * PX_PER_M
WIDE_RIGHT_X: float = MID_X + WIDE_HALF_WIDTH_M * PX_PER_M

# Batting crease y-position in canvas (bottom of pitch)
BATTING_CREASE_Y: float = CANVAS_ORIGIN_Y + (PITCH_LENGTH_M - POPPING_CREASE_OFFSET_M) * PX_PER_M
# Bowling crease y-position (top of pitch — bowler's end)
BOWLING_CREASE_Y: float = CANVAS_ORIGIN_Y + POPPING_CREASE_OFFSET_M * PX_PER_M


def _detect_crease_lines(frame: np.ndarray) -> Optional[List[Tuple[float, float, float, float]]]:
    """
    Detect white crease lines in a video frame using Canny + HoughLinesP.

    Returns a list of (x1, y1, x2, y2) line segments, or None if not found.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Enhance white regions (crease lines are bright white)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Morphological close to connect broken lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    edges = cv2.Canny(thresh, 50, 150, apertureSize=3)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=80,
        minLineLength=frame.shape[1] // 6,
        maxLineGap=30,
    )

    if lines is None:
        return None

    # Filter roughly horizontal lines (crease lines are horizontal)
    horizontal = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if angle < 15 or angle > 165:
            horizontal.append((float(x1), float(y1), float(x2), float(y2)))

    return horizontal if horizontal else None


def _pick_crease_pair(
    lines: List[Tuple[float, float, float, float]],
    frame_h: int,
) -> Optional[Tuple[float, float]]:
    """
    From a list of detected horizontal lines pick the two y-positions
    that best correspond to the batting and bowling creases.

    Returns (bowling_y, batting_y) in image pixels, or None.
    """
    y_positions = sorted(set(round((l[1] + l[3]) / 2.0) for l in lines))

    if len(y_positions) < 2:
        return None

    # The bowling crease is roughly in the upper half, batting in the lower half
    upper_candidates = [y for y in y_positions if y < frame_h * 0.5]
    lower_candidates = [y for y in y_positions if y >= frame_h * 0.5]

    if not upper_candidates or not lower_candidates:
        # Fall back: pick the two most spread-apart lines
        bowling_y = float(y_positions[0])
        batting_y = float(y_positions[-1])
    else:
        bowling_y = float(upper_candidates[-1])   # closest upper line to centre
        batting_y = float(lower_candidates[0])    # closest lower line to centre

    return (bowling_y, batting_y)


class PitchHomography:
    """
    Manages the perspective → top-down homography for a single camera angle.

    Call `calibrate()` with a representative frame to fit the transform.
    Then use `transform_point()` to map any (x, y) pixel to top-down coords,
    or `draw_topdown()` to render the full warped view.
    """

    def __init__(self) -> None:
        self._H: Optional[np.ndarray] = None          # 3×3 homography matrix
        self._H_inv: Optional[np.ndarray] = None      # inverse (topdown → image)
        self._src_pts: Optional[np.ndarray] = None    # 4 source points in image
        self._calibrated: bool = False

        # Crease y-positions in the camera image (updated on calibrate)
        self.img_bowling_y: float = 0.0
        self.img_batting_y: float = 0.0
        self.img_frame_w:   int   = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calibrate(self, frame: np.ndarray, manual_pts: Optional[np.ndarray] = None) -> bool:
        """
        Estimate the homography from frame → top-down view.

        Args:
            frame:      BGR video frame
            manual_pts: Optional (4, 2) array of manually labelled corner points
                        [top-left, top-right, bottom-right, bottom-left] in image coords.
                        When provided, line detection is skipped.

        Returns:
            True if calibration succeeded.
        """
        h, w = frame.shape[:2]
        self.img_frame_w = w

        if manual_pts is not None:
            src = manual_pts.astype(np.float32)
        else:
            src = self._auto_detect_pitch_corners(frame)
            if src is None:
                logger.warning("Homography: auto-detection failed, using fallback corners.")
                src = self._fallback_corners(h, w)

        # Destination rectangle in top-down canvas
        td_x0 = float(CANVAS_ORIGIN_X)
        td_y0 = float(CANVAS_ORIGIN_Y)
        td_x1 = td_x0 + PITCH_WIDTH_M * PX_PER_M
        td_y1 = td_y0 + PITCH_LENGTH_M * PX_PER_M

        dst = np.array([
            [td_x0, td_y0],
            [td_x1, td_y0],
            [td_x1, td_y1],
            [td_x0, td_y1],
        ], dtype=np.float32)

        self._H, status = cv2.findHomography(src, dst, cv2.RANSAC, 5.0)

        if self._H is None or not np.all(status):
            logger.warning("Homography computation failed.")
            return False

        self._H_inv = np.linalg.inv(self._H)
        self._src_pts = src
        self._calibrated = True
        logger.info("Homography calibrated successfully.")
        return True

    def transform_point(self, pt: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Map an image-space point to top-down canvas coordinates.

        Args:
            pt: (x, y) in image pixels

        Returns:
            (tx, ty) in top-down canvas pixels, or None if not calibrated.
        """
        if not self._calibrated or self._H is None:
            return None

        src = np.array([[[pt[0], pt[1]]]], dtype=np.float32)
        dst = cv2.perspectiveTransform(src, self._H)
        return float(dst[0, 0, 0]), float(dst[0, 0, 1])

    def is_wide(self, ball_topdown_x: float, ball_topdown_y: float) -> Tuple[bool, float]:
        """
        Determine if a ball position (top-down coords) qualifies as a wide.

        The check only applies when the ball is near the batting crease
        (within ±1m tolerance in y-direction).

        Returns:
            (is_wide, confidence)  confidence ∈ [0, 1]
        """
        # Only check near the batting crease
        y_margin_px = 1.0 * PX_PER_M
        if abs(ball_topdown_y - BATTING_CREASE_Y) > y_margin_px:
            return False, 0.0

        if ball_topdown_x < WIDE_LEFT_X:
            overshoot = WIDE_LEFT_X - ball_topdown_x
            conf = min(1.0, overshoot / (WIDE_HALF_WIDTH_M * PX_PER_M * 0.5))
            return True, conf

        if ball_topdown_x > WIDE_RIGHT_X:
            overshoot = ball_topdown_x - WIDE_RIGHT_X
            conf = min(1.0, overshoot / (WIDE_HALF_WIDTH_M * PX_PER_M * 0.5))
            return True, conf

        return False, 0.0

    def draw_topdown(self, frame: np.ndarray) -> np.ndarray:
        """Return a warped top-down view of the frame with pitch markings."""
        if not self._calibrated or self._H is None:
            canvas = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
            cv2.putText(canvas, "Not calibrated", (10, CANVAS_H // 2),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            return canvas

        warped = cv2.warpPerspective(frame, self._H, (CANVAS_W, CANVAS_H))
        self._draw_pitch_lines(warped)
        return warped

    def draw_overlay_on_frame(self, frame: np.ndarray) -> np.ndarray:
        """Draw detected crease lines and wide zone onto the original frame."""
        if not self._calibrated or self._src_pts is None:
            return frame

        out = frame.copy()
        pts = self._src_pts.astype(np.int32)
        cv2.polylines(out, [pts], isClosed=True, color=(0, 255, 255), thickness=2)
        return out

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auto_detect_pitch_corners(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Try to extract 4 pitch corners from Hough crease lines."""
        h, w = frame.shape[:2]
        lines = _detect_crease_lines(frame)
        if not lines:
            return None

        crease_pair = _pick_crease_pair(lines, h)
        if not crease_pair:
            return None

        bowling_y, batting_y = crease_pair
        self.img_bowling_y = bowling_y
        self.img_batting_y = batting_y

        # Estimate pitch width as a fraction of frame width (typical broadcast)
        pitch_half_w = w * 0.15

        # 4 corners: top-left, top-right, bottom-right, bottom-left
        src = np.array([
            [w / 2.0 - pitch_half_w, bowling_y],
            [w / 2.0 + pitch_half_w, bowling_y],
            [w / 2.0 + pitch_half_w, batting_y],
            [w / 2.0 - pitch_half_w, batting_y],
        ], dtype=np.float32)

        return src

    @staticmethod
    def _fallback_corners(h: int, w: int) -> np.ndarray:
        """Generate a plausible set of source corners for a typical broadcast view."""
        cx = w / 2.0
        top_y    = h * 0.25
        bot_y    = h * 0.85
        top_half = w * 0.10
        bot_half = w * 0.20
        return np.array([
            [cx - top_half, top_y],
            [cx + top_half, top_y],
            [cx + bot_half, bot_y],
            [cx - bot_half, bot_y],
        ], dtype=np.float32)

    @staticmethod
    def _draw_pitch_lines(canvas: np.ndarray) -> None:
        """Overlay ICC pitch line markings on a top-down canvas."""
        # Batting crease
        by = int(BATTING_CREASE_Y)
        x0 = int(CANVAS_ORIGIN_X)
        x1 = int(CANVAS_ORIGIN_X + PITCH_WIDTH_M * PX_PER_M)
        cv2.line(canvas, (x0, by), (x1, by), (255, 255, 255), 2)

        # Bowling crease
        bowy = int(BOWLING_CREASE_Y)
        cv2.line(canvas, (x0, bowy), (x1, bowy), (255, 255, 255), 2)

        # Wide zone lines (yellow)
        wl = int(WIDE_LEFT_X)
        wr = int(WIDE_RIGHT_X)
        cv2.line(canvas, (wl, bowy), (wl, by), (0, 255, 255), 1)
        cv2.line(canvas, (wr, bowy), (wr, by), (0, 255, 255), 1)

        # Middle stump
        mx = int(MID_X)
        cv2.line(canvas, (mx, bowy), (mx, by), (0, 128, 255), 1)
