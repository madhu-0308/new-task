"""Performance tracking and statistics for personalized coaching."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "user_data.db"

WEAK_ACCURACY_THRESHOLD = 60.0


class AnalyticsTracker:
    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    video_path TEXT,
                    predicted_shot TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    actual_shot TEXT,
                    is_correct INTEGER,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    user_id TEXT NOT NULL,
                    shot_type TEXT NOT NULL,
                    total_attempts INTEGER NOT NULL DEFAULT 0,
                    correct_count INTEGER NOT NULL DEFAULT 0,
                    avg_confidence REAL NOT NULL DEFAULT 0.0,
                    PRIMARY KEY (user_id, shot_type)
                );
                CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id);
                CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at);
                """
            )

    def record_prediction(
        self,
        user_id: str,
        video_path: str | None,
        predicted_shot: str,
        confidence: float,
    ) -> int:
        user_id = user_id.strip().lower()
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO predictions (user_id, video_path, predicted_shot, confidence, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, video_path, predicted_shot, confidence, created_at),
            )
            pred_id = int(cur.lastrowid)
            self._update_metrics_on_prediction(conn, user_id, predicted_shot, confidence)
        return pred_id

    def _update_metrics_on_prediction(
        self, conn: sqlite3.Connection, user_id: str, shot: str, confidence: float
    ) -> None:
        row = conn.execute(
            "SELECT total_attempts, correct_count, avg_confidence FROM performance_metrics "
            "WHERE user_id = ? AND shot_type = ?",
            (user_id, shot),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO performance_metrics (user_id, shot_type, total_attempts, correct_count, avg_confidence) "
                "VALUES (?, ?, 1, 0, ?)",
                (user_id, shot, confidence),
            )
        else:
            n = row["total_attempts"] + 1
            avg = (row["avg_confidence"] * row["total_attempts"] + confidence) / n
            conn.execute(
                "UPDATE performance_metrics SET total_attempts = ?, avg_confidence = ? "
                "WHERE user_id = ? AND shot_type = ?",
                (n, avg, user_id, shot),
            )

    def record_feedback(
        self,
        prediction_id: int,
        actual_shot: str,
        is_correct: bool | None = None,
    ) -> None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id, predicted_shot FROM predictions WHERE id = ?",
                (prediction_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Prediction {prediction_id} not found")
            predicted = row["predicted_shot"]
            if is_correct is None:
                is_correct = predicted.strip().lower() == actual_shot.strip().lower()
            conn.execute(
                "UPDATE predictions SET actual_shot = ?, is_correct = ? WHERE id = ?",
                (actual_shot, int(is_correct), prediction_id),
            )
            if is_correct:
                self._increment_correct(conn, row["user_id"], predicted)

    def _increment_correct(
        self, conn: sqlite3.Connection, user_id: str, shot: str
    ) -> None:
        conn.execute(
            "UPDATE performance_metrics SET correct_count = correct_count + 1 "
            "WHERE user_id = ? AND shot_type = ?",
            (user_id, shot),
        )

    def get_user_stats(self, user_id: str, days: int | None = None) -> dict[str, Any]:
        user_id = user_id.strip().lower()
        where = "user_id = ?"
        params: list[Any] = [user_id]
        if days is not None:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
            where += " AND created_at >= ?"
            params.append(cutoff)

        with self._connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) AS c FROM predictions WHERE {where}", params
            ).fetchone()["c"]
            with_feedback = conn.execute(
                f"SELECT COUNT(*) AS c FROM predictions WHERE {where} AND is_correct IS NOT NULL",
                params,
            ).fetchone()["c"]
            correct = conn.execute(
                f"SELECT COUNT(*) AS c FROM predictions WHERE {where} AND is_correct = 1",
                params,
            ).fetchone()["c"]
            avg_conf = conn.execute(
                f"SELECT AVG(confidence) AS a FROM predictions WHERE {where}", params
            ).fetchone()["a"]

            per_shot_rows = conn.execute(
                "SELECT shot_type, total_attempts, correct_count, avg_confidence "
                "FROM performance_metrics WHERE user_id = ? ORDER BY shot_type",
                (user_id,),
            ).fetchall()

        per_shot: dict[str, dict[str, float | int]] = {}
        for r in per_shot_rows:
            attempts = r["total_attempts"]
            acc = (r["correct_count"] / attempts * 100) if attempts else 0.0
            per_shot[r["shot_type"]] = {
                "attempts": attempts,
                "correct": r["correct_count"],
                "accuracy": round(acc, 1),
                "avg_confidence": round(r["avg_confidence"], 3),
            }

        overall_acc = (correct / with_feedback * 100) if with_feedback else 0.0
        return {
            "user_id": user_id,
            "total_predictions": total,
            "labeled_predictions": with_feedback,
            "overall_accuracy": round(overall_acc, 1),
            "avg_confidence": round(float(avg_conf or 0), 3),
            "per_shot": per_shot,
        }

    def get_improvement_trajectory(self, user_id: str, days: int = 30) -> list[dict[str, Any]]:
        user_id = user_id.strip().lower()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT DATE(created_at) AS day, "
                "COUNT(*) AS total, "
                "SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) AS correct, "
                "SUM(CASE WHEN is_correct IS NOT NULL THEN 1 ELSE 0 END) AS labeled "
                "FROM predictions WHERE user_id = ? AND created_at >= ? "
                "GROUP BY DATE(created_at) ORDER BY day",
                (user_id, cutoff),
            ).fetchall()
        trajectory = []
        for r in rows:
            labeled = r["labeled"] or 0
            acc = (r["correct"] / labeled * 100) if labeled else 0.0
            trajectory.append({
                "date": r["day"],
                "predictions": r["total"],
                "accuracy": round(acc, 1),
            })
        return trajectory

    def get_weak_shots(
        self, user_id: str, threshold: float = WEAK_ACCURACY_THRESHOLD
    ) -> list[dict[str, Any]]:
        stats = self.get_user_stats(user_id)
        weak = []
        for shot, data in stats["per_shot"].items():
            if data["attempts"] >= 2 and data["accuracy"] < threshold:
                weak.append({"shot": shot, **data})
        weak.sort(key=lambda x: x["accuracy"])
        return weak

    def delete_user_data(self, user_id: str) -> None:
        user_id = user_id.strip().lower()
        with self._connect() as conn:
            conn.execute("DELETE FROM predictions WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM performance_metrics WHERE user_id = ?", (user_id,))

    def get_recent_predictions(self, user_id: str, limit: int = 5) -> list[dict[str, Any]]:
        user_id = user_id.strip().lower()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, predicted_shot, confidence, actual_shot, is_correct, created_at "
                "FROM predictions WHERE user_id = ? ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
