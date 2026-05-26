"""Interactive demo of the cricket coach personalization system."""

from __future__ import annotations

import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from user_manager import UserManager
from analytics import AnalyticsTracker
from personalized_coach import PersonalizedCoach

DEMO_USER = "demo_player"
SHOTS = [
    "Cover Drive", "Straight Drive", "Pull", "Hook", "Sweep",
    "Reverse Sweep", "Scoop", "Square Cut", "Defensive", "Flick",
]


def demo_header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def demo_1_create_user() -> UserManager:
    demo_header("1. Create User Profile")
    um = UserManager()
    tracker = AnalyticsTracker()
    tracker.delete_user_data(DEMO_USER)
    um.purge_user(DEMO_USER)
    profile = um.create_user(DEMO_USER, "Demo Player", "advanced")
    print(f"Created: {profile.display_name} ({profile.skill_level})")
    um.set_user_preferences(
        DEMO_USER,
        feedback_style="motivational",
        focus_shots=["Cover Drive", "Hook"],
        practice_frequency="daily",
    )
    print("Set preferences: motivational feedback, daily practice")
    return um


def demo_2_record_predictions(tracker: AnalyticsTracker) -> None:
    demo_header("2. Record Sample Predictions")
    random.seed(42)
    for i in range(12):
        shot = random.choice(SHOTS)
        conf = round(random.uniform(0.55, 0.95), 3)
        pred_id = tracker.record_prediction(DEMO_USER, f"clip_{i}.mp4", shot, conf)
        actual = shot if random.random() > 0.25 else random.choice(SHOTS)
        tracker.record_feedback(pred_id, actual)
        mark = "OK" if actual.lower() == shot.lower() else "MISS"
        print(f"  [{mark}] pred={shot} actual={actual} conf={conf:.2f}")
    print("Recorded 12 predictions with feedback.")


def demo_3_user_stats(tracker: AnalyticsTracker) -> None:
    demo_header("3. User Statistics")
    stats = tracker.get_user_stats(DEMO_USER)
    print(f"Total predictions: {stats['total_predictions']}")
    print(f"Overall accuracy: {stats['overall_accuracy']}%")
    print(f"Avg confidence: {stats['avg_confidence']}")
    print("\nPer-shot (top 5 by attempts):")
    ranked = sorted(
        stats["per_shot"].items(),
        key=lambda x: x[1]["attempts"],
        reverse=True,
    )[:5]
    for shot, d in ranked:
        print(f"  {shot}: {d['accuracy']}% ({d['attempts']} attempts)")


def demo_4_weak_shots(tracker: AnalyticsTracker) -> None:
    demo_header("4. Weak Shot Analysis")
    weak = tracker.get_weak_shots(DEMO_USER)
    if weak:
        for w in weak:
            print(f"  {w['shot']}: {w['accuracy']}% accuracy")
    else:
        print("  No shots below 60% threshold yet (need more labeled data).")


def demo_5_trajectory(tracker: AnalyticsTracker) -> None:
    demo_header("5. Improvement Trajectory (30 days)")
    traj = tracker.get_improvement_trajectory(DEMO_USER, days=30)
    for point in traj[-5:]:
        print(f"  {point['date']}: {point['accuracy']}% ({point['predictions']} shots)")


def demo_6_session_feedback(coach: PersonalizedCoach) -> None:
    demo_header("6. Session Feedback")
    session = coach.get_session_feedback(DEMO_USER)
    print(session["greeting"])
    print(session["session_message"])
    for r in session["recommendations"]:
        print(f"  • {r}")
    for t in session["technical_tips"][:3]:
        print(f"  Tip: {t}")


def demo_7_coaching_report(coach: PersonalizedCoach) -> None:
    demo_header("7. Comprehensive Coaching Report")
    report = coach.get_overall_coaching_report(DEMO_USER)
    print(
        f"Overall: {report['overall_accuracy']}% | "
        f"{report['total_predictions']} predictions | {report['skill_level']}"
    )
    if report["strongest_shots"]:
        print(f"Strongest: {', '.join(report['strongest_shots'])}")
    if report["weakest_shots"]:
        print(f"Weakest: {', '.join(report['weakest_shots'])}")
    print("\nTraining plan:")
    for phase, lines in report["training_plan"].items():
        if phase != "priority_shots":
            for line in lines:
                print(f"  [{phase}] {line}")


def demo_8_list_users(um: UserManager) -> None:
    demo_header("8. List All Users")
    for u in um.list_users():
        print(f"  {u.user_id}: {u.display_name} ({u.skill_level})")


def main() -> None:
    print("Cricket Coach Personalization — Interactive Demo")
    print("Database:", PROJECT_ROOT / "data" / "user_data.db")
    um = demo_1_create_user()
    tracker = AnalyticsTracker()
    demo_2_record_predictions(tracker)
    demo_3_user_stats(tracker)
    demo_4_weak_shots(tracker)
    demo_5_trajectory(tracker)
    coach = PersonalizedCoach(um, tracker)
    demo_6_session_feedback(coach)
    demo_7_coaching_report(coach)
    demo_8_list_users(um)
    demo_header("Demo Complete")
    print("Next steps:")
    print("  python src/coach_cli.py user create YOUR_ID --name \"Your Name\" --skill-level expert")
    print("  python src/predict_personalized.py YOUR_ID video.mp4 --actual-shot \"Cover Drive\" --feedback")
    print("  python src/coach_cli.py report YOUR_ID")
    print("  python scripts/coach_api.py")


if __name__ == "__main__":
    main()
