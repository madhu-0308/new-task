"""User profile and preference management for personalized coaching."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = PROJECT_ROOT / "data" / "user_data.db"

SKILL_LEVELS = ("beginner", "intermediate", "advanced", "expert")
FEEDBACK_STYLES = ("brief", "detailed", "motivational")
PRACTICE_FREQUENCIES = ("daily", "every_other_day", "weekly", "custom")


@dataclass
class UserProfile:
    user_id: str
    display_name: str
    skill_level: str
    created_at: str
    feedback_style: str = "detailed"
    focus_shots: list[str] | None = None
    practice_frequency: str = "daily"

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "skill_level": self.skill_level,
            "created_at": self.created_at,
            "feedback_style": self.feedback_style,
            "focus_shots": self.focus_shots or [],
            "practice_frequency": self.practice_frequency,
        }


class UserManager:
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
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    skill_level TEXT NOT NULL DEFAULT 'intermediate',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    feedback_style TEXT NOT NULL DEFAULT 'detailed',
                    focus_shots TEXT NOT NULL DEFAULT '[]',
                    practice_frequency TEXT NOT NULL DEFAULT 'daily',
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                """
            )

    def create_user(
        self,
        user_id: str,
        display_name: str,
        skill_level: str = "intermediate",
    ) -> UserProfile:
        user_id = user_id.strip().lower().replace(" ", "_")
        skill_level = skill_level.lower()
        if skill_level not in SKILL_LEVELS:
            raise ValueError(f"skill_level must be one of {SKILL_LEVELS}")
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            try:
                conn.execute(
                    "INSERT INTO users (user_id, display_name, skill_level, created_at) VALUES (?, ?, ?, ?)",
                    (user_id, display_name, skill_level, created_at),
                )
                conn.execute(
                    "INSERT INTO user_preferences (user_id) VALUES (?)",
                    (user_id,),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError(f"User '{user_id}' already exists") from exc
        return self.get_user(user_id)

    def get_user(self, user_id: str) -> UserProfile:
        user_id = user_id.strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT u.*, p.feedback_style, p.focus_shots, p.practice_frequency "
                "FROM users u LEFT JOIN user_preferences p ON u.user_id = p.user_id "
                "WHERE u.user_id = ?",
                (user_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"User '{user_id}' not found")
        focus = json.loads(row["focus_shots"] or "[]")
        return UserProfile(
            user_id=row["user_id"],
            display_name=row["display_name"],
            skill_level=row["skill_level"],
            created_at=row["created_at"],
            feedback_style=row["feedback_style"] or "detailed",
            focus_shots=focus,
            practice_frequency=row["practice_frequency"] or "daily",
        )

    def set_user_preferences(
        self,
        user_id: str,
        *,
        feedback_style: str | None = None,
        focus_shots: list[str] | None = None,
        practice_frequency: str | None = None,
    ) -> UserProfile:
        _ = self.get_user(user_id)
        updates: list[str] = []
        params: list[Any] = []
        if feedback_style is not None:
            if feedback_style not in FEEDBACK_STYLES:
                raise ValueError(f"feedback_style must be one of {FEEDBACK_STYLES}")
            updates.append("feedback_style = ?")
            params.append(feedback_style)
        if focus_shots is not None:
            updates.append("focus_shots = ?")
            params.append(json.dumps(focus_shots))
        if practice_frequency is not None:
            if practice_frequency not in PRACTICE_FREQUENCIES:
                raise ValueError(f"practice_frequency must be one of {PRACTICE_FREQUENCIES}")
            updates.append("practice_frequency = ?")
            params.append(practice_frequency)
        if not updates:
            return self.get_user(user_id)
        params.append(user_id.strip().lower())
        with self._connect() as conn:
            conn.execute(
                f"UPDATE user_preferences SET {', '.join(updates)} WHERE user_id = ?",
                params,
            )
        return self.get_user(user_id)

    def purge_user(self, user_id: str) -> None:
        """Remove user and preferences (idempotent, no error if missing)."""
        user_id = user_id.strip().lower()
        with self._connect() as conn:
            conn.execute("DELETE FROM user_preferences WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))

    def delete_user(self, user_id: str) -> None:
        user_id = user_id.strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"User '{user_id}' not found")
        self.purge_user(user_id)

    def list_users(self) -> list[UserProfile]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT user_id FROM users ORDER BY display_name"
            ).fetchall()
        return [self.get_user(r["user_id"]) for r in rows]
