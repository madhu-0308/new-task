"""Personalized feedback and training plan generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from analytics import AnalyticsTracker
from user_manager import UserManager

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SHOT_TIPS: dict[str, str] = {
    "Cover Drive": "Keep your head steady, drive through the line with a high elbow.",
    "Straight Drive": "Lean into the ball and drive with full face of the bat.",
    "Defensive": "Soft hands, bat close to body, minimal follow-through.",
    "Pull": "Rotate hips quickly and watch the ball onto the bat.",
    "Hook": "Compact pull-back and swivel; eyes level at contact.",
    "Sweep": "Low base, head still, sweep across the line of the ball.",
    "Reverse Sweep": "Switch grip early, stable base, control the reverse angle.",
    "Square Cut": "Late hands, high backlift, cut behind point.",
    "Late Cut": "Wait for the ball, open face late toward third man.",
    "Scoop": "Bend knees, scoop with controlled wrist, avoid over-extension.",
    "Flick": "Wristy work off the pads, close to the body.",
    "Lofted Offside": "Transfer weight and time the loft without losing shape.",
    "Lofted Legside": "Open hips slightly and swing through the line.",
    "Down The Wicket": "Quick feet, head forward, commit to the length.",
    "Upper Cut": "Guide the ball with soft hands over the slips cordon.",
}

SHOT_CATEGORIES: dict[str, str] = {
    "Cover Drive": "drives",
    "Straight Drive": "drives",
    "Defensive": "defensive",
    "Pull": "aggressive",
    "Hook": "aggressive",
    "Sweep": "sweeps",
    "Reverse Sweep": "sweeps",
    "Square Cut": "cuts",
    "Late Cut": "cuts",
    "Upper Cut": "cuts",
    "Scoop": "innovative",
    "Flick": "wrist",
    "Lofted Offside": "aggressive",
    "Lofted Legside": "aggressive",
    "Down The Wicket": "aggressive",
}


class PersonalizedCoach:
    def __init__(
        self,
        user_manager: UserManager | None = None,
        tracker: AnalyticsTracker | None = None,
    ) -> None:
        self.users = user_manager or UserManager()
        self.tracker = tracker or AnalyticsTracker()

    def get_session_feedback(self, user_id: str) -> dict[str, Any]:
        profile = self.users.get_user(user_id)
        recent = self.tracker.get_recent_predictions(user_id, limit=5)
        labeled = [p for p in recent if p.get("is_correct") is not None]
        correct = sum(1 for p in labeled if p["is_correct"])
        session_acc = (correct / len(labeled) * 100) if labeled else 0.0

        weak = self.tracker.get_weak_shots(user_id)[:3]
        stats = self.tracker.get_user_stats(user_id)
        per_shot = stats.get("per_shot", {})
        strong = sorted(
            per_shot.items(),
            key=lambda x: (x[1]["accuracy"], x[1]["attempts"]),
            reverse=True,
        )[:2]

        recommendations = self._generate_recommendations(user_id, weak, strong)
        tips = self._technical_tips(weak, recent)

        style = profile.feedback_style
        greeting = self._greeting(profile.display_name, style)
        session_msg = self._session_message(session_acc, len(labeled), style)

        return {
            "user_id": user_id,
            "display_name": profile.display_name,
            "session_accuracy": round(session_acc, 1),
            "shots_analyzed": len(recent),
            "greeting": greeting,
            "session_message": session_msg,
            "recommendations": recommendations,
            "technical_tips": tips,
            "recent_predictions": recent,
        }

    def get_overall_coaching_report(self, user_id: str) -> dict[str, Any]:
        profile = self.users.get_user(user_id)
        stats = self.tracker.get_user_stats(user_id)
        weak = self.tracker.get_weak_shots(user_id)
        trajectory = self.tracker.get_improvement_trajectory(user_id, days=30)

        per_shot = stats.get("per_shot", {})
        ranked = sorted(
            per_shot.items(),
            key=lambda x: (x[1]["accuracy"], x[1]["attempts"]),
            reverse=True,
        )
        strongest = [s for s, _ in ranked[:3] if per_shot[s]["attempts"] > 0]
        weakest = sorted(
            per_shot.items(),
            key=lambda x: (x[1]["accuracy"], -x[1]["attempts"]),
        )
        weakest_names = [s for s, d in weakest[:3] if d["attempts"] >= 1]

        categories = self._category_breakdown(per_shot)
        training_plan = self._create_training_plan(profile, weakest_names)

        return {
            "user_id": user_id,
            "display_name": profile.display_name,
            "skill_level": profile.skill_level,
            "overall_accuracy": stats["overall_accuracy"],
            "total_predictions": stats["total_predictions"],
            "avg_confidence": stats["avg_confidence"],
            "per_shot_breakdown": per_shot,
            "strongest_shots": strongest,
            "weakest_shots": weakest_names,
            "weak_shots_detail": weak,
            "category_performance": categories,
            "improvement_trajectory": trajectory,
            "recommendations": self._generate_recommendations(
                user_id, weak, ranked[:3]
            ),
            "training_plan": training_plan,
            "motivational": self._motivational(stats["overall_accuracy"], style=profile.feedback_style),
        }

    def _greeting(self, name: str, style: str) -> str:
        if style == "brief":
            return f"Hi {name}."
        if style == "motivational":
            return f"Hey {name}! Great to see you back on the nets."
        return f"Hey {name}!"

    def _session_message(self, acc: float, n: int, style: str) -> str:
        if n == 0:
            return "No labeled shots in this session yet — record predictions with --actual-shot."
        if style == "brief":
            return f"Session accuracy: {acc:.0f}% ({n} shots)."
        if acc >= 80:
            return f"Great session! Session accuracy: {acc:.0f}% ({n} shots analyzed)."
        if acc >= 60:
            return f"Solid work. Session accuracy: {acc:.0f}% ({n} shots analyzed)."
        return f"Room to improve — session accuracy: {acc:.0f}% ({n} shots analyzed)."

    def _generate_recommendations(
        self,
        user_id: str,
        weak: list[dict[str, Any]],
        strong: list[tuple[str, dict[str, Any]]] | list[dict[str, Any]],
    ) -> list[str]:
        recs: list[str] = []
        if weak:
            names = ", ".join(w["shot"] for w in weak[:3])
            recs.append(f"Focus on improving: {names}")
        if strong:
            if isinstance(strong[0], tuple):
                top = strong[0][0]
            else:
                top = strong[0].get("shot", "")
            if top:
                recs.append(f"Build on your strength in {top}")
        profile = self.users.get_user(user_id)
        if profile.focus_shots:
            recs.append(f"Your focus list: {', '.join(profile.focus_shots)}")
        if not recs:
            recs.append("Keep recording sessions to unlock personalized recommendations.")
        return recs

    def _technical_tips(
        self, weak: list[dict[str, Any]], recent: list[dict[str, Any]]
    ) -> list[str]:
        tips: list[str] = []
        for w in weak[:2]:
            shot = w["shot"]
            if shot in SHOT_TIPS:
                tips.append(f"{shot}: {SHOT_TIPS[shot]}")
        for p in recent[:2]:
            shot = p["predicted_shot"]
            if shot in SHOT_TIPS and f"{shot}:" not in " ".join(tips):
                tips.append(f"{shot}: {SHOT_TIPS[shot]}")
        return tips or ["Record more shots with feedback to get targeted technical tips."]

    def _create_training_plan(
        self, profile: Any, weak_shots: list[str]
    ) -> dict[str, list[str]]:
        focus = weak_shots[:2] if weak_shots else (profile.focus_shots or ["Cover Drive", "Defensive"])
        main = focus[0] if focus else "Cover Drive"
        secondary = focus[1] if len(focus) > 1 else "Defensive"
        freq = profile.practice_frequency

        return {
            "warm_up": [f"5 min — shadow all shots ({freq} routine)"],
            "main_training": [f"20 min — {main} + {secondary} reps"],
            "targeted_work": [f"10 min — {main}-specific drills"],
            "cool_down": ["5 min — defensive blocks and footwork"],
            "priority_shots": focus,
        }

    def _category_breakdown(self, per_shot: dict[str, dict[str, Any]]) -> dict[str, float]:
        cats: dict[str, list[float]] = {}
        for shot, data in per_shot.items():
            cat = SHOT_CATEGORIES.get(shot, "other")
            cats.setdefault(cat, []).append(data["accuracy"])
        return {c: round(sum(v) / len(v), 1) for c, v in cats.items() if v}

    def _motivational(self, accuracy: float, style: str) -> str:
        if style == "brief":
            return ""
        if accuracy >= 85:
            return "Outstanding consistency — keep pushing your limits!"
        if accuracy >= 70:
            return "You're on the right track. Small tweaks will unlock the next level."
        return "Every rep counts. Focus on weak areas and you'll see gains quickly."
