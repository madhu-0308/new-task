# Cricket Shot Analysis

Pose-sequence based cricket shot classifier. Companion project to a Roboflow-trained
bat/ball/stump detector — here we focus on **what shot the batsman just played**.

## Approach

Each clip (~2 sec around point-of-contact) is converted into a sequence of
batsman keypoints with YOLO-Pose. A small Transformer is trained over those
sequences to predict the shot class. This is far more sample-efficient than
training a video model from raw RGB and is robust to camera angle.

## Shot classes (8)

drive, cut, pull_hook, sweep, defensive, glance, innovative, other.
See `classes.yaml` for variant lists. Folder names under `data/clips/` are the source of truth.

## Pipeline

| Step | Script | Output |
|------|--------|--------|
| 1 | (scaffold) | folder tree, configs |
| 2 | `scripts/download_videos.py` | `data/raw_videos/<class>/*.mp4` (URLs from `scripts/urls_by_class.yaml`) |
| 3 | `scripts/segment_clips.py` | `data/clips/<class>/*.mp4` (class inherited from source folder) |
| 4 | `scripts/review_clips.py` | keep/trash review pass — junk moves to `data/clips/_trash/` |
| 5 | `scripts/extract_poses.py` | `data/poses/<class>/*.npy` (auto-mirrors left-handers) |
| 6 | `scripts/make_splits.py` | `data/splits/{train,val,test}.txt` |
| 7 | `src/train.py` | `runs/<exp>/best.pt` |

## Setup

```powershell
cd C:\Users\KARTHIKK\OneDrive\Desktop\cricket-shot-analysis
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

You also need **ffmpeg** on PATH (download from https://ffmpeg.org or `winget install ffmpeg`).

## Personalized coaching (new)

Multi-user profiles, prediction tracking, analytics, and coaching reports.

| Command | Description |
|---------|-------------|
| `python scripts/demo_personalization.py` | Interactive demo |
| `python src/coach_cli.py user create ID --name "Name"` | Create player profile |
| `python src/predict_personalized.py ID video.mp4 --feedback` | Predict + track |
| `python src/coach_cli.py report ID` | Full coaching report |
| `python scripts/coach_api.py` | REST API on port 5000 |

See **QUICK_START.md** for a 5-minute walkthrough.

## Status

- [x] Step 1 — Scaffold
- [ ] Step 2 — Per-class video collection
- [ ] Step 3 — Per-class clip segmentation
- [ ] Step 4 — Keep/trash review
- [ ] Step 5 — Pose extraction
- [ ] Step 6 — Splits
- [ ] Step 7 — Training
