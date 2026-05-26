# Personalization Guide

## User management

```powershell
python src/coach_cli.py user create virat --name "Virat Kohli" --skill-level expert
python src/coach_cli.py user preferences virat --feedback-style motivational --focus-shots "Cover Drive,Hook"
python src/coach_cli.py user list
```

Skill levels: `beginner`, `intermediate`, `advanced`, `expert`.

## Recording predictions

Each prediction stores shot type, confidence, and optional ground truth:

```powershell
python src/predict_personalized.py virat video.mp4 --actual-shot "Cover Drive" --feedback
```

Without a video (programmatic):

```python
from src.analytics import AnalyticsTracker
t = AnalyticsTracker()
pid = t.record_prediction("virat", "clip.mp4", "Cover Drive", 0.87)
t.record_feedback(pid, "Cover Drive")
```

## Coaching output

- **Session feedback** — last 5 predictions, recommendations, technical tips
- **Report** — overall accuracy, strongest/weakest shots, daily training plan
- **Stats** — per-shot accuracy, weak shots (&lt;60%), 30-day trajectory

## Weak shot threshold

Shots with at least 2 attempts and accuracy below 60% are flagged as weak areas.

## Shot names

Use exact class names from `classes.yaml` / `data/splits/class_index.json` (e.g. `Cover Drive`, not `cover drive`).
