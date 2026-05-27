# Next-Level Cricket Analysis Platform

A full-stack cricket AI system that combines a **Next.js web frontend** with a **Python computer-vision backend** to detect and analyze cricket deliveries in real time.

---

## Project Structure

```
next-level/
├── Gaara_Main/              # Next.js 14 frontend (React + Tailwind CSS)
├── cricket-cv/              # Python CV backend (Flask API + YOLOv8)
├── cricket-trained-model/   # Pre-trained model weights & training scripts
└── README.md
```

---

## Features

| Feature | Description |
|---|---|
| 🏏 Ball Detection & Tracking | YOLOv8 + SORT Kalman-filter tracker with trail overlay |
| 🦇 Bat Detection | YOLOv8 + MediaPipe Pose wrist refinement + contact detection |
| ↔️ Wide Ball Detection | Homography top-down transform + ICC wide-line rules |
| 🦶 No-Ball Detection | Front-foot crease overstepping via MediaPipe keypoints |
| 🎬 Video Analyzer UI | Upload a video, see annotated output + stats in the browser |

---

## Requirements

### System
- **Python 3.11** (recommended)
- **Node.js 18+** and **npm**
- Git

### Python libraries
See [`cricket-cv/requirements.txt`](cricket-cv/requirements.txt) for the full list. Key packages:
- `ultralytics` (YOLOv8)
- `opencv-python`
- `filterpy`, `scipy` (SORT tracker)
- `mediapipe` (pose estimation)
- `Flask`, `flask-cors` (REST API)

---

## Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/madhu-0308/new-task.git
cd new-task
```

### 2. Start the Python CV API
```bash
cd cricket-cv

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Start the API server on port 5001
python api.py --port 5001
```

The API will be available at `http://localhost:5001`.

### 3. Start the Next.js Frontend
Open a new terminal:
```bash
cd Gaara_Main
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### 4. Open the Delivery Analyzer
Navigate to: [http://localhost:3000/products/cricket/analyze](http://localhost:3000/products/cricket/analyze)

Upload any cricket match video and the system will:
1. Detect and track the ball with a motion trail
2. Detect the bat and any bat–ball contact
3. Draw wide-ball boundary lines with overshoot distances
4. Highlight no-ball foot overstepping with crease analysis
5. Return an annotated output video + summary stats in the browser

---

## Running the CV Pipeline via CLI (no frontend)

```bash
cd cricket-cv
.venv\Scripts\activate

python main.py --video path/to/match.mp4 --output output_annotated.mp4
```

Optional flags:
```
--model   path/to/custom_weights.pt   (default: yolov8n.pt)
--conf    0.30                         (detection confidence threshold)
--json    results.json                 (save frame-level JSON results)
--mobile                               (enable portrait/mobile video mode)
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/analyze` | Upload a video; returns JSON results + output filename |
| `GET` | `/download/<filename>` | Download the annotated output video |
| `GET` | `/` | Health check |

### Example
```bash
curl -X POST http://localhost:5001/analyze \
  -F "video=@match.mp4" \
  -F "conf=0.3"
```

---

## Fine-tuning the Model

To train on your own cricket dataset (e.g. from Roboflow):
```bash
cd cricket-cv
python train_model.py --dataset path/to/dataset.yaml --epochs 50
```

---

## Environment Variables

Create `Gaara_Main/.env.local`:
```
NEXT_PUBLIC_CV_API_URL=http://localhost:5001
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React, Tailwind CSS |
| Backend API | Python 3.11, Flask 3.x, flask-cors |
| Object Detection | Ultralytics YOLOv8 |
| Object Tracking | SORT (Kalman filter + Hungarian algorithm) |
| Pose Estimation | MediaPipe Pose |
| Video Processing | OpenCV (cv2) |
| Geometric Transform | Homography (`cv2.findHomography`) |

---

## License

MIT
