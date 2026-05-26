# Cricket Shot Classifier with Personalized Coach

## Quick Start

### Setup
```powershell
cd C:\Users\madhu\OneDrive\Desktop\next-level\cricket-trained-model
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Demo the Coaching System
```powershell
python demo_coaching.py
```

This runs 3 scenarios showing how the personalized coach analyzes shots.

---

## Features

### 1. **Shot Classification**
- Detects 15 cricket shot types: Cover Drive, Defensive, Pull, Sweep, Square Cut, Hook, Flick, Lofted Offside, Lofted Legside, Scoop, Reverse Sweep, Straight Drive, Late Cut, Down The Wicket, Upper Cut
- Uses YOLO-Pose + Transformer model on pose keypoint sequences
- Returns confidence score for each prediction

### 2. **Automatic Mistake Detection**
The personalized coach identifies:
- **Head movement**: Is the head stable during the shot?
- **Upper body alignment**: Is the torso leaning too much?
- **Base stability**: Are feet committed or moving too much?
- **Pose confidence**: Is the pose extraction reliable?
- **Shot ambiguity**: Is the model confident or confused between shots?

### 3. **Personalized Coaching Feedback**
For each shot analysis:
- **Issue**: Main technical problem detected
- **Notes**: Specific observations
- **Advice**: Actionable improvement tips
- **Metrics**: Pose quality data (head stillness, wrist motion, ankle motion, torso tilt)

---

## Running Inference on a Video

When a trained model is available:

```powershell
python src/predict.py path\to\cricket_clip.mp4
```

Output includes:
```
Prediction for clip.mp4:
  class          prob
  -------------- -----
  Cover Drive    0.78
  Straight Drive 0.12
  Defensive      0.05

Personalized coach feedback:
  Coach: personalized
  predicted shot : Cover Drive
  confidence     : 0.78
  main issue     : Good balance and stable posture.
  notes          : No serious mistakes detected.
  advice         : Keep the same motion and focus on consistency.
```

---

## Project Pipeline

| Step | Script | Status |
|------|--------|--------|
| 1 | scaffold | ✓ Done |
| 2 | `download_videos.py` | Download cricket compilations |
| 3 | `segment_clips.py` | Cut per-shot clips |
| 4 | `review_clips.py` | Keep/trash clips |
| 5 | `extract_poses.py` | YOLO-Pose → keypoints |
| 6 | `make_splits.py` | Train/val/test splits |
| 7 | `train.py` | Train Transformer model |
| 8 | `predict.py` | **Inference + Coaching** |

---

## Coaching Module Architecture

### File: `src/coach.py`

**Main function**: `generate_coaching_feedback(seq, shot, probs, id_to_name)`

**Inputs:**
- `seq`: Pose sequence (50 frames, 17 keypoints, 3 values per keypoint)
- `shot`: Predicted shot class name
- `probs`: Model prediction probabilities
- `id_to_name`: Shot class mapping

**Outputs:**
```python
{
    "coach": "Coach: personalized",
    "shot": "Cover Drive",
    "shot_confidence": 0.78,
    "issue": "Good balance and stable posture.",
    "notes": "No serious mistakes detected.",
    "advice": "Keep the same motion and focus on consistency.",
    "visible_ratio": 0.92,        # % of frames with visible batsman
    "avg_confidence": 0.84,       # Pose detection confidence
    "head_stillness": 0.05,       # Lower = more stable
    "wrist_motion": 0.12,         # Bat hand motion
    "ankle_motion": 0.08,         # Foot movement
    "torso_tilt": 0.14,          # Upper body lean
}
```

**Metrics Analyzed:**
- **visible_ratio**: Fraction of frames where batsman is reliably detected
- **avg_confidence**: Average YOLO-Pose keypoint confidence
- **head_stillness**: Mean distance of head (nose) from sequence center
- **wrist_motion**: Movement of bat-hand relative to body
- **ankle_motion**: Foot stability during shot
- **torso_tilt**: Lateral lean of upper body

---

## Sample Coaching Messages

### Good Technique
```
Shot Detected    : Cover Drive
Confidence       : 78%
Main Issue       : Good balance and stable posture.
Notes            : No serious mistakes detected.
Advice           : Keep the same motion and focus on consistency.
```

### Head Movement Issue
```
Shot Detected    : Sweep
Confidence       : 62%
Main Issue       : Head movement is too large.
Notes            : Model is unsure of the exact shot type.
Advice           : Keep your head steady during the shot.
```

### Unstable Base
```
Shot Detected    : Pull
Confidence       : 55%
Main Issue       : Feet are moving too much before impact.
Notes            : Model is unsure.
Advice           : Commit your front foot and maintain a stable base.
```

### Ambiguous Shot
```
Shot Detected    : Pull
Confidence       : 35%
Main Issue       : Shot is ambiguous between Pull and Defensive.
Notes            : Try a cleaner clip with a clearer bat path.
Advice           : Keep your head steady during the shot.
```

---

## Next Steps

1. **Collect Videos**: Gather cricket shot compilations
2. **Extract Clips**: Run `segment_clips.py` to cut per-shot videos
3. **Review Clips**: Use `review_clips.py` to validate quality
4. **Extract Poses**: Run `extract_poses.py` to get keypoint sequences
5. **Create Splits**: Run `make_splits.py` to prepare train/val/test
6. **Train Model**: Run `src/train.py` to train the Transformer
7. **Use Coach**: Run `src/predict.py` on new videos for personalized coaching!

---

## Summary

**What you get:**
- ✓ Shot detection (15 cricket shot types)
- ✓ Automatic mistake identification
- ✓ Personalized coaching feedback
- ✓ Pose quality metrics
- ✓ Confidence scores

**One word summary:** A personalized cricket coach powered by pose-sequence analysis!
