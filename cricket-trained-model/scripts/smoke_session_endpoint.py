"""Local smoke-test for /api/analyze-session.

Starts the Flask app in-process (no gunicorn), POSTs the sample video, prints
the JSON response.

Usage:
    python scripts/smoke_session_endpoint.py "C:\\Users\\KARTHIKK\\Downloads\\vid\\6shots.mp4"
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HF_DIR = PROJECT_ROOT.parent / "hf-space-cricket"
sys.path.insert(0, str(HF_DIR))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video", type=Path)
    ap.add_argument("--port", type=int, default=7861)
    args = ap.parse_args()

    if not args.video.exists():
        sys.exit(f"Video not found: {args.video}")

    # Import app AFTER setting sys.path. Start it in a daemon thread.
    print("[smoke] importing flask app ...")
    from app import app, _load_done

    def _serve():
        app.run(host="127.0.0.1", port=args.port, debug=False, use_reloader=False)

    th = threading.Thread(target=_serve, daemon=True)
    th.start()

    base = f"http://127.0.0.1:{args.port}"
    print(f"[smoke] waiting for model warmup ...")
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            r = requests.get(base + "/healthz", timeout=5)
            if r.ok and r.json().get("model_ready"):
                print(f"[smoke] model_ready=true ({r.json().get('model_load_seconds')}s)")
                break
        except requests.RequestException:
            pass
        time.sleep(2)
    else:
        sys.exit("Model didn't warm up in 2 min")

    print(f"[smoke] POSTing {args.video.name} -> /api/analyze-session ...")
    t0 = time.time()
    with args.video.open("rb") as f:
        r = requests.post(
            base + "/api/analyze-session",
            files={"video": (args.video.name, f, "video/mp4")},
            data={"consent_training": "0"},   # don't pollute /tmp during smoke tests
            timeout=300,
        )
    dt = time.time() - t0
    print(f"[smoke] HTTP {r.status_code} in {dt:.1f}s")
    if not r.ok:
        print(r.text)
        sys.exit(1)

    body = r.json()
    print("\n--- response ---")
    print(f"video_seconds: {body.get('video_seconds')}")
    print(f"balls_detected: {body.get('balls_detected')}")
    print(f"elapsed_seconds: {body.get('elapsed_seconds')}")
    print(f"saved_for_training: {body.get('saved_for_training')}")
    print(f"\nballs:")
    for b in body.get("balls", []):
        print(f"  #{b['index']}  {b['shot']:<12} grade={b['grade']:.1f}  notes={b['notes']}")
    print(f"\nsummary: {json.dumps(body.get('summary', {}), indent=2)}")

    print("\nDone. (Process exits when main returns; flask thread is daemon.)")


if __name__ == "__main__":
    main()
