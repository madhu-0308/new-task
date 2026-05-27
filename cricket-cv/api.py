"""
Cricket CV — Flask API
=======================
Exposes the detection pipeline as a REST API that the Next.js frontend can
call.  Uploads a video, runs all four detectors, returns per-frame JSON.

Endpoints
---------
POST /analyze
    Upload a video file for analysis.
    Content-Type: multipart/form-data
    Field name:   video
    Optional query params:
        model  — path to YOLOv8 weights (default: yolov8n.pt)
        conf   — YOLO confidence threshold (default: 0.30)
        mediapipe — "1" / "0" (default: "1")

    Response 200:
    {
        "status": "ok",
        "total_frames": 450,
        "fps": 25.0,
        "summary": {
            "wide_count":   1,
            "noball_count": 0,
            "contact_count": 12,
            "ball_detected_frames": 300
        },
        "frames": [
            {
                "frame": 1,
                "ball_pos": [cx, cy],
                "bat_bbox": [x1, y1, x2, y2],
                "contact":  false,
                "is_wide":  false,
                "wide_conf": 0.0,
                "is_noball":  false,
                "noball_conf": 0.0,
                "wide_decision":   "PENDING",
                "noball_decision": "PENDING"
            },
            ...
        ],
        "output_video": "/download/output_<uuid>.mp4"
    }

GET /download/<filename>
    Download a processed output video.

GET /health
    Health check — returns {"status": "ok"}.

Integration with Next.js
------------------------
In your Next.js API route or component, POST to:
    http://localhost:5001/analyze

Example fetch call (from frontend):

    const form = new FormData()
    form.append("video", videoFile)
    const res = await fetch("http://localhost:5001/analyze", {
        method: "POST", body: form
    })
    const data = await res.json()
"""

from __future__ import annotations

import logging
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS

# Ensure project root is importable
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from main import process_video  # noqa: E402  (import after path setup)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("cricket_cv.api")

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_DIR  = Path(tempfile.gettempdir()) / "cricket_cv_uploads"
OUTPUT_DIR  = Path(tempfile.gettempdir()) / "cricket_cv_outputs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024   # 500 MB
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

DEFAULT_MODEL = str(_HERE / "yolov8n.pt")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def _summarise(frames: list) -> Dict[str, Any]:
    wide_count     = sum(1 for f in frames if f["is_wide"])
    noball_count   = sum(1 for f in frames if f["is_noball"])
    contact_count  = sum(1 for f in frames if f["contact"])
    ball_det_count = sum(1 for f in frames if f["ball_pos"] is not None)
    return {
        "wide_count":             wide_count,
        "noball_count":           noball_count,
        "contact_count":          contact_count,
        "ball_detected_frames":   ball_det_count,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
def health() -> Any:
    return jsonify({"status": "ok", "service": "cricket-cv-api"})


@app.route("/analyze", methods=["POST"])
def analyze() -> Any:
    """
    Main endpoint: accept video upload → run pipeline → return JSON results.
    """
    # --- Validate request ---------------------------------------------------
    if "video" not in request.files:
        return jsonify({"error": "No video file in request. "
                                 "Use field name 'video'."}), 400

    video_file = request.files["video"]
    if not video_file.filename:
        return jsonify({"error": "Empty filename."}), 400

    if not _allowed_file(video_file.filename):
        return jsonify({
            "error": f"Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}"
        }), 415

    # --- Optional parameters ------------------------------------------------
    model_path   = request.args.get("model", DEFAULT_MODEL)
    conf_thresh  = float(request.args.get("conf", "0.30"))
    use_mediapipe = request.args.get("mediapipe", "1") != "0"

    # --- Save upload --------------------------------------------------------
    req_id       = uuid.uuid4().hex
    suffix       = Path(video_file.filename).suffix.lower()
    upload_path  = UPLOAD_DIR / f"{req_id}_input{suffix}"
    output_path  = OUTPUT_DIR / f"output_{req_id}.mp4"

    try:
        video_file.save(str(upload_path))
        logger.info("[%s] Saved upload: %s", req_id, upload_path)
    except OSError as exc:
        logger.exception("Failed to save upload: %s", exc)
        return jsonify({"error": "Failed to save video file."}), 500

    # --- Run detection pipeline --------------------------------------------
    try:
        logger.info("[%s] Starting analysis (model=%s conf=%.2f mediapipe=%s)",
                    req_id, model_path, conf_thresh, use_mediapipe)

        frame_results = process_video(
            video_path=str(upload_path),
            output_path=str(output_path),
            model_path=model_path,
            conf_thresh=conf_thresh,
            use_mediapipe=use_mediapipe,
            do_calibrate=False,
            json_output_path=None,
            show=False,
        )

    except FileNotFoundError as exc:
        logger.error("Video file error: %s", exc)
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        logger.exception("[%s] Analysis failed: %s", req_id, exc)
        return jsonify({"error": f"Analysis failed: {exc}"}), 500
    finally:
        # Clean up upload (keep output for download)
        try:
            upload_path.unlink(missing_ok=True)
        except Exception:
            pass

    # --- Build response -----------------------------------------------------
    response: Dict[str, Any] = {
        "status":       "ok",
        "request_id":   req_id,
        "total_frames": len(frame_results),
        "summary":      _summarise(frame_results),
        "frames":       frame_results,
        "output_video": f"/download/{output_path.name}",
    }

    logger.info("[%s] Analysis complete. %d frames. output=%s",
                req_id, len(frame_results), output_path.name)
    return jsonify(response), 200


@app.route("/download/<filename>", methods=["GET"])
def download(filename: str) -> Any:
    """Stream a processed output video with range-request support for browser playback."""
    safe_name = Path(filename).name   # prevent path traversal
    fp = OUTPUT_DIR / safe_name
    if not fp.exists():
        return jsonify({"error": "File not found."}), 404

    file_size = fp.stat().st_size
    range_header = request.headers.get("Range")

    if range_header:
        # Parse "bytes=start-end"
        byte_range = range_header.replace("bytes=", "").split("-")
        start = int(byte_range[0]) if byte_range[0] else 0
        end   = int(byte_range[1]) if byte_range[1] else file_size - 1
        end   = min(end, file_size - 1)
        length = end - start + 1

        def stream_chunk():
            with open(fp, "rb") as f:
                f.seek(start)
                remaining = length
                chunk_size = 64 * 1024
                while remaining > 0:
                    data = f.read(min(chunk_size, remaining))
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        resp = Response(
            stream_chunk(),
            status=206,
            mimetype="video/mp4",
            direct_passthrough=True,
        )
        resp.headers["Content-Range"]  = f"bytes {start}-{end}/{file_size}"
        resp.headers["Accept-Ranges"]  = "bytes"
        resp.headers["Content-Length"] = str(length)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    # Full file
    resp = send_from_directory(str(OUTPUT_DIR), safe_name,
                               mimetype="video/mp4", as_attachment=False)
    resp.headers["Accept-Ranges"] = "bytes"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.route("/", methods=["GET"])
def index() -> Any:
    return jsonify({
        "service": "Cricket CV API",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze":        "Upload video, returns per-frame detections",
            "GET  /download/<file>": "Download processed output video",
            "GET  /health":         "Health check",
        },
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cricket CV Flask API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logger.info("Cricket CV API starting on http://%s:%d", args.host, args.port)
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
