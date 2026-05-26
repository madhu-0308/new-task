# Cricket CV Detection System

A production-ready Python computer vision pipeline for automated cricket match analysis.  
Detects the ball, bat, wide balls, and no-balls in real-time from broadcast video.

---

## Features

| Feature | Method | Output |
|---------|--------|--------|
| **Ball Detection & Tracking** | YOLOv8 + SORT Kalman tracker | Green bounding box + trajectory trail |
| **Bat Detection** | YOLOv8 + MediaPipe Pose refinement | Blue bounding box + contact flash |
| **Wide Ball Detection** | Hough crease lines + homography projection | Red "WIDE" overlay |
| **No-Ball Detection** | MediaPipe Pose front-foot check + pixel subtraction | Red "NO BALL" overlay |

---

## Project Structure

```
cricket-cv/
├── main.py                     # Entry point — process a video
├── api.py                      # Flask REST API (integrates with Next.js)
├── train_model.py              # Fine-tune YOLOv8 on cricket dataset
├── requirements.txt
├── detectors/
│   ├── ball_detector.py        # YOLOv8 + SORT ball tracker
│   ├── bat_detector.py         # YOLOv8 + MediaPipe bat detector
│   ├── wide_detector.py        # Wide ball classifier
│   └── noball_detector.py      # No-ball classifier
└── utils/
    ├── tracker.py              # SORT multi-object tracker implementation
    └── homography.py           # Pitch perspective transform utilities
```

---

## Installation

### Prerequisites
- Python 3.10 or higher
- FFmpeg installed and in PATH
- NVIDIA GPU recommended (works on CPU, but slower)

### Setup

```bash
cd cricket-cv

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Quick Start

### 1. Run on a video

```bash
python main.py --video path/to/match.mp4
```

Output video is saved as `output.mp4` with all overlays.

### 2. All options

```bash
python main.py \
    --video match.mp4 \
    --output result.mp4 \
    --model cricket_yolo.pt \   # custom fine-tuned model
    --conf 0.35 \               # YOLO confidence threshold
    --json detections.json \    # save per-frame JSON
    --show                      # display video in real time
```

### 3. With homography calibration (for accurate wide detection)

```bash
python main.py --video match.mp4 --calibrate
```

A window will open. **Click the 4 pitch corners in order**:
`top-left → top-right → bottom-right → bottom-left`, then press **Enter**.

### 4. Faster mode (no MediaPipe)

```bash
python main.py --video match.mp4 --no-mediapipe
```

---

## Per-Frame JSON Output

```bash
python main.py --video match.mp4 --json results.json
```

Each frame entry:

```json
{
  "frame": 42,
  "ball_pos": [640.5, 380.2],
  "ball_track_id": 1,
  "bat_bbox": [550.0, 300.0, 700.0, 500.0],
  "contact": false,
  "is_wide": false,
  "wide_conf": 0.0,
  "is_noball": false,
  "noball_conf": 0.0,
  "wide_decision": "LEGAL",
  "noball_decision": "LEGAL"
}
```

---

## Fine-Tuning on Cricket Dataset

The pretrained `yolov8n.pt` works out of the box for general objects.  
For best cricket-specific accuracy, fine-tune on the Roboflow cricket dataset:

### 1. Get a Roboflow API key
Sign up at [roboflow.com](https://roboflow.com) → copy your API key.

### 2. Run training

```bash
python train_model.py --roboflow-key YOUR_API_KEY --epochs 50 --batch 16
```

Training takes ~30 min on a GPU. The best weights are saved at:
`runs/train/cricket_yolo/weights/best.pt`

### 3. Use the fine-tuned model

```bash
python main.py --video match.mp4 --model runs/train/cricket_yolo/weights/best.pt
```

### Training options

```bash
python train_model.py \
    --roboflow-key YOUR_KEY \
    --base yolov8s.pt \    # larger = more accurate, slower
    --epochs 100 \
    --imgsz 1280 \         # higher resolution for small ball
    --batch 8 \
    --device 0             # GPU device id
```

---

## Flask API

The API allows the Next.js frontend to upload videos and receive structured detections.

### Start the API server

```bash
python api.py --port 5001
```

### POST /analyze

Upload a video and receive per-frame detections:

```bash
curl -X POST http://localhost:5001/analyze \
     -F "video=@match.mp4" \
     -F "conf=0.30"
```

**Response:**

```json
{
  "status": "ok",
  "request_id": "abc123",
  "total_frames": 450,
  "summary": {
    "wide_count": 1,
    "noball_count": 0,
    "contact_count": 12,
    "ball_detected_frames": 300
  },
  "frames": [...],
  "output_video": "/download/output_abc123.mp4"
}
```

### Next.js integration

In your Next.js component or API route:

```typescript
const form = new FormData()
form.append("video", videoFile)

const res = await fetch("http://localhost:5001/analyze", {
  method: "POST",
  body: form,
})

const data = await res.json()
console.log(data.summary)   // { wide_count, noball_count, contact_count, ... }
console.log(data.frames[0]) // first frame detections
```

---

## Visual Overlays

| Colour | Meaning |
|--------|---------|
| Green box | Cricket ball (with trail) |
| Blue box | Cricket bat |
| Red flash | Bat-ball contact |
| Yellow lines | Crease zone boundaries |
| Red text "WIDE" | Wide ball detected |
| Red text "NO BALL" | No-ball detected |
| Green text "LEGAL" | Ball confirmed legal |

---

## Technical Details

### Ball Tracking (SORT)
- YOLOv8 detects ball candidates each frame
- Kalman filter predicts ball position when detection fails (occlusion)
- Hungarian algorithm matches predictions to new detections
- Trajectory trail shows last 30 positions
- Hough circle fallback for frames where YOLO misses the ball

### Wide Detection
- Hough transform detects crease lines in each frame
- Homography maps camera view → bird's-eye top-down pitch view
- ICC standard: ball must cross batting crease outside 89cm from middle stump
- Pixel-position fallback when homography calibration is unavailable

### No-Ball Detection
- MediaPipe Pose detects bowler's ankle, heel, and toe keypoints
- Any keypoint below the popping crease line at delivery = no-ball
- Fallback: MOG2 background subtractor detects foot motion in crease ROI

### Bat-Ball Contact
- Ball centre within `CONTACT_MARGIN_PX` (default: 25px) of bat bounding box
- Contact point highlighted with filled circle

---

## Requirements

- Python 3.10+
- `ultralytics` — YOLOv8
- `mediapipe` — pose estimation
- `filterpy` — Kalman filter
- `opencv-python` — video I/O and drawing
- `scipy` — Hungarian algorithm
- `Flask` + `flask-cors` — REST API
- `roboflow` — dataset download (training only)
