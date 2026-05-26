# Implementation Summary — Personalization System

## Modules (`src/`)

| Module | Purpose |
|--------|---------|
| `user_manager.py` | SQLite user profiles and preferences |
| `analytics.py` | Prediction logging, accuracy metrics, trajectories |
| `personalized_coach.py` | Session feedback, reports, training plans |
| `predict_personalized.py` | Video inference + automatic tracking |
| `coach_cli.py` | CLI for users, reports, stats |

## Data

- **Database:** `data/user_data.db`
- **Tables:** `users`, `user_preferences`, `predictions`, `performance_metrics`

## Scripts

- `scripts/demo_personalization.py` — end-to-end demo with sample data
- `scripts/coach_api.py` — Flask REST API

## Integration

- **Minimal:** call `AnalyticsTracker.record_prediction()` after `predict.py`
- **Full:** use `predict_personalized.py` with `--feedback` and `--actual-shot`
- **API:** `POST /api/users/<id>/predict-video` with multipart upload

Existing `predict.py`, `model.py`, `dataset.py`, and `train.py` are unchanged.
