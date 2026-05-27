"""
Cricket CV Detection System — Entry Point
==========================================
Processes a cricket video through all four detection modules:

  1. Ball detection & tracking  (green box + trail)
  2. Bat detection              (blue box + contact flash)
  3. Wide ball detection        (red "WIDE" overlay)
  4. No-ball detection          (red "NO BALL" overlay)

Usage
-----
    python main.py --video path/to/match.mp4
    python main.py --video match.mp4 --output out.mp4 --model cricket_yolo.pt
    python main.py --video match.mp4 --calibrate          # interactive homography calibration
    python main.py --video match.mp4 --no-mediapipe       # skip MediaPipe (faster)
    python main.py --video match.mp4 --json results.json  # also save per-frame JSON

Options
-------
  --video      Path to input video file (required)
  --output     Output video path (default: output.mp4)
  --model      YOLOv8 weights (.pt) — fine-tuned or pretrained yolov8n.pt
  --conf       YOLO confidence threshold (default: 0.30)
  --no-mediapipe   Disable MediaPipe pose estimation (faster)
  --calibrate  Enter interactive homography calibration mode (click 4 corners)
  --json       Save per-frame detections to a JSON file
  --show       Display video in real time (requires display)
  --delivery-gap  Frames of inactivity after which a new delivery is assumed (default: 60)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

# Ensure project root is on the path (supports running from any CWD)
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from detectors.ball_detector import BallDetector
from detectors.bat_detector import BatDetector
from detectors.wide_detector import WideDetector
from detectors.noball_detector import NoBallDetector
from utils.homography import PitchHomography

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cricket_cv.main")

# Frames without a ball detection that trigger a delivery reset
_DEFAULT_DELIVERY_GAP = 60


# ---------------------------------------------------------------------------
# Homography calibration helper
# ---------------------------------------------------------------------------

_calibration_pts: List[List[int]] = []
_calibration_frame: Optional[np.ndarray] = None


def _mouse_callback(event: int, x: int, y: int, _flags: int, _param: Any) -> None:
    global _calibration_pts, _calibration_frame
    if event == cv2.EVENT_LBUTTONDOWN and len(_calibration_pts) < 4:
        _calibration_pts.append([x, y])
        logger.info("Calibration point %d: (%d, %d)", len(_calibration_pts), x, y)
        if _calibration_frame is not None:
            cv2.circle(_calibration_frame, (x, y), 6, (0, 255, 0), -1)
            cv2.imshow("Calibrate — click 4 pitch corners", _calibration_frame)


def interactive_calibrate(frame: np.ndarray, homo: PitchHomography) -> bool:
    """
    Opens a window where the user clicks the 4 corners of the pitch
    (top-left, top-right, bottom-right, bottom-left) to calibrate the
    homography.

    Returns True if calibration succeeded.
    """
    global _calibration_pts, _calibration_frame
    _calibration_pts = []
    _calibration_frame = frame.copy()

    win = "Calibrate — click 4 pitch corners"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, _mouse_callback)
    cv2.putText(
        _calibration_frame,
        "Click: top-left, top-right, bottom-right, bottom-left",
        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2,
    )
    cv2.imshow(win, _calibration_frame)

    logger.info("Click the 4 pitch corners in order: TL, TR, BR, BL. Press ENTER when done.")
    while True:
        key = cv2.waitKey(50) & 0xFF
        if key == 13 and len(_calibration_pts) == 4:  # Enter
            break
        if key == 27:  # Esc
            logger.warning("Calibration cancelled.")
            cv2.destroyWindow(win)
            return False

    cv2.destroyWindow(win)
    pts = np.array(_calibration_pts, dtype=np.float32)
    return homo.calibrate(frame, manual_pts=pts)


# ---------------------------------------------------------------------------
# Main processing loop
# ---------------------------------------------------------------------------

def process_video(
    video_path: str,
    output_path: str = "output.mp4",
    model_path: str = "yolov8n.pt",
    conf_thresh: float = 0.30,
    use_mediapipe: bool = True,
    do_calibrate: bool = False,
    json_output_path: Optional[str] = None,
    show: bool = False,
    delivery_gap: int = _DEFAULT_DELIVERY_GAP,
) -> List[Dict[str, Any]]:
    """
    Run the full detection pipeline on a video file.

    Returns a list of per-frame result dicts.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Cannot open video: {video_path}")

    fps    = cap.get(cv2.CAP_PROP_FPS) or 25.0
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    logger.info("Video: %s  %dx%d  %.1f fps  %d frames", video_path, width, height, fps, total)

    # Video writer — prefer H.264 (browser-playable); fall back to mp4v
    fourcc = cv2.VideoWriter_fourcc(*"avc1")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not writer.isOpened():
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # Initialise modules
    homography   = PitchHomography()
    ball_det     = BallDetector(model_path=model_path, conf_thresh=conf_thresh)
    bat_det      = BatDetector(model_path=model_path, conf_thresh=conf_thresh,
                               use_mediapipe=use_mediapipe)
    wide_det     = WideDetector(homography=homography)
    noball_det   = NoBallDetector(use_mediapipe=use_mediapipe)

    all_results: List[Dict[str, Any]] = []
    frames_no_ball = 0
    calibrated     = False
    frame_idx      = 0
    t_start        = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1

        # --- Auto-calibrate homography on first frame ---
        if not calibrated:
            if do_calibrate:
                calibrated = interactive_calibrate(frame, homography)
            else:
                calibrated = homography.calibrate(frame)
            if not calibrated:
                logger.warning("Homography calibration failed on frame %d. "
                               "Wide detection will use pixel heuristics.", frame_idx)

        # --- Run detectors ---
        ball_r   = ball_det.detect(frame)
        bat_r    = bat_det.detect(frame, ball_result=ball_r)
        wide_r   = wide_det.update(frame, ball_r)
        noball_r = noball_det.update(frame, ball_r)

        # --- Delivery boundary detection ---
        if ball_r["detected"]:
            frames_no_ball = 0
        else:
            frames_no_ball += 1

        if frames_no_ball >= delivery_gap:
            # New delivery — reset per-delivery state
            ball_det.reset()
            wide_det.reset()
            noball_det.reset()
            frames_no_ball = 0

        # --- Draw overlays ---
        annotated = frame.copy()
        annotated = ball_det.draw(annotated, ball_r)
        annotated = bat_det.draw(annotated, bat_r)
        annotated = wide_det.draw(annotated, wide_r, ball_r)
        annotated = noball_det.draw(annotated, noball_r)
        _draw_status_bar(annotated, frame_idx, total, fps, ball_r, bat_r, wide_r, noball_r)

        writer.write(annotated)

        if show:
            cv2.imshow("Cricket CV", annotated)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("User quit.")
                break

        # --- Collect results ---
        frame_result: Dict[str, Any] = {
            "frame": frame_idx,
            "ball_pos": ball_r["center"],
            "ball_track_id": ball_r["track_id"],
            "bat_pos": bat_r["center"],
            "bat_bbox": bat_r["bbox"],
            "contact": bat_r["contact"],
            "is_wide":   wide_r["decision"] == "WIDE",
            "wide_conf": wide_r["confidence"],
            "is_noball":    noball_r["decision"] == "NO BALL",
            "noball_conf":  noball_r["confidence"],
            "wide_decision":   wide_r["decision"],
            "noball_decision": noball_r["decision"],
        }
        all_results.append(frame_result)

        # Progress log
        if frame_idx % 100 == 0:
            elapsed = time.time() - t_start
            fps_actual = frame_idx / elapsed if elapsed > 0 else 0
            pct = frame_idx / total * 100 if total > 0 else 0
            logger.info("Frame %d/%d (%.0f%%)  %.1f fps", frame_idx, total, pct, fps_actual)

    cap.release()
    writer.release()
    if show:
        cv2.destroyAllWindows()
    bat_det.close()
    noball_det.close()

    elapsed = time.time() - t_start
    logger.info(
        "Done. %d frames in %.1f s (%.1f fps). Output: %s",
        frame_idx, elapsed, frame_idx / elapsed if elapsed > 0 else 0, output_path,
    )

    if json_output_path:
        with open(json_output_path, "w") as f:
            json.dump(all_results, f, indent=2, default=str)
        logger.info("Per-frame JSON saved: %s", json_output_path)

    return all_results


# ---------------------------------------------------------------------------
# Status bar
# ---------------------------------------------------------------------------

def _draw_status_bar(
    frame: np.ndarray,
    frame_idx: int,
    total: int,
    fps: float,
    ball_r: Dict, bat_r: Dict, wide_r: Dict, noball_r: Dict,
) -> None:
    """
    Render a comprehensive HUD:
      - Top-left: frame counter + ball/bat/contact status
      - Bottom-centre: ball trajectory info (track ID + trail length)
    """
    h, w = frame.shape[:2]

    # ── Top-left info panel ───────────────────────────────────────────────────
    panel_w, panel_h = 230, 112
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (panel_w, panel_h), (10, 10, 10), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    cv2.rectangle(frame, (0, 0), (panel_w, panel_h), (80, 80, 80), 1)

    def put(text: str, row: int, color=(200, 200, 200)) -> None:
        cv2.putText(frame, text, (6, 16 + row * 19),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, color, 1, cv2.LINE_AA)

    pct = int(frame_idx / total * 100) if total > 0 else 0
    put(f"Frame {frame_idx}/{total}  [{pct}%]", 0, (180, 180, 180))

    ball_color = (80, 255, 80) if ball_r["detected"] else (100, 100, 100)
    put(f"Ball: {'TRACKED #' + str(ball_r.get('track_id','?')) if ball_r['detected'] else 'NOT DETECTED'}",
        1, ball_color)

    trail = ball_r.get("trail", [])
    put(f"Trail: {len(trail)} pts  Conf: {ball_r.get('conf', 0):.0%}", 2, (150, 220, 150))

    bat_color = (255, 160, 60) if bat_r["detected"] else (100, 100, 100)
    put(f"Bat: {'DETECTED' if bat_r['detected'] else 'NOT DETECTED'}", 3, bat_color)

    contact_color = (0, 80, 255) if bat_r["contact"] else (150, 150, 150)
    put(f"Contact: {'⚡ HIT!' if bat_r['contact'] else 'none'}", 4, contact_color)

    wide_txt   = wide_r["decision"]
    wide_color = (60, 60, 255) if wide_txt == "WIDE" else \
                 (60, 200, 60) if wide_txt == "LEGAL" else (160, 160, 160)
    put(f"Wide: {wide_txt}  {wide_r['confidence']:.0%}", 5, wide_color)

    # ── Ball trajectory legend (bottom-centre) ────────────────────────────────
    if ball_r["detected"] and ball_r.get("center"):
        bx, by = ball_r["center"]
        legend = f"Ball @ ({bx:.0f}, {by:.0f})"
        (tw, _), _ = cv2.getTextSize(legend, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        lx = w // 2 - tw // 2
        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (lx - 4, h - 22), (lx + tw + 4, h - 4),
                      (0, 0, 0), -1)
        cv2.addWeighted(overlay2, 0.5, frame, 0.5, 0, frame)
        cv2.putText(frame, legend, (lx, h - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (80, 255, 80), 1, cv2.LINE_AA)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cricket CV — ball/bat/wide/noball detection pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--video",    required=True,  help="Path to input video file")
    parser.add_argument("--output",   default="output.mp4", help="Output video path")
    parser.add_argument("--model",    default="yolov8n.pt",
                        help="YOLOv8 weights (.pt)")
    parser.add_argument("--conf",     type=float, default=0.30,
                        help="YOLO confidence threshold")
    parser.add_argument("--no-mediapipe", action="store_true",
                        help="Disable MediaPipe pose (faster)")
    parser.add_argument("--calibrate", action="store_true",
                        help="Interactive homography calibration (click 4 corners)")
    parser.add_argument("--json",     default=None,
                        help="Save per-frame detections to JSON")
    parser.add_argument("--show",     action="store_true",
                        help="Display video in real time")
    parser.add_argument("--delivery-gap", type=int, default=_DEFAULT_DELIVERY_GAP,
                        help="Frames of ball absence to trigger delivery reset")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    if not Path(args.video).exists():
        logger.error("Video file not found: %s", args.video)
        sys.exit(1)

    results = process_video(
        video_path=args.video,
        output_path=args.output,
        model_path=args.model,
        conf_thresh=args.conf,
        use_mediapipe=not args.no_mediapipe,
        do_calibrate=args.calibrate,
        json_output_path=args.json,
        show=args.show,
        delivery_gap=args.delivery_gap,
    )

    # Summary statistics
    total_frames   = len(results)
    wide_frames    = sum(1 for r in results if r["is_wide"])
    noball_frames  = sum(1 for r in results if r["is_noball"])
    contact_frames = sum(1 for r in results if r["contact"])
    ball_frames    = sum(1 for r in results if r["ball_pos"] is not None)

    print("\n" + "=" * 50)
    print(f"  Total frames processed : {total_frames}")
    print(f"  Ball detected in       : {ball_frames} frames")
    print(f"  Bat-ball contact       : {contact_frames} frames")
    print(f"  Wide decisions         : {wide_frames}")
    print(f"  No-ball decisions      : {noball_frames}")
    print(f"  Output video           : {args.output}")
    if args.json:
        print(f"  JSON results           : {args.json}")
    print("=" * 50)
