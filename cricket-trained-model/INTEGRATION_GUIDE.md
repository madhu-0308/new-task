# Integration Guide

## Option 1 — Minimal (keep `predict.py`)

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path("src").resolve()))
from analytics import AnalyticsTracker

tracker = AnalyticsTracker()
pred_id = tracker.record_prediction(user_id, str(video_path), shot, confidence)
tracker.record_feedback(pred_id, actual_shot)  # optional
```

## Option 2 — Full CLI (recommended)

```powershell
python src/predict_personalized.py USER video.mp4 --actual-shot "Pull" --feedback
```

## Option 3 — REST API

```powershell
python scripts/coach_api.py
```

```bash
curl -X POST http://localhost:5000/api/users -H "Content-Type: application/json" \
  -d '{"user_id":"p1","display_name":"Player 1","skill_level":"intermediate"}'
curl http://localhost:5000/api/users/p1/report
```

## Option 4 — Python API

```python
from personalized_coach import PersonalizedCoach
coach = PersonalizedCoach()
report = coach.get_overall_coaching_report("p1")
session = coach.get_session_feedback("p1")
```

## Web UI (`src/server.py`)

Add tracking after prediction in `predict_file()` using the same `AnalyticsTracker` pattern; pass `user_id` via form field or session cookie.
