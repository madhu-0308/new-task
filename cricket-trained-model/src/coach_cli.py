"""Command-line interface for personalized cricket coaching.

Usage:
    python src/coach_cli.py user create USER --name "Name" --skill-level expert
    python src/coach_cli.py user list
    python src/coach_cli.py report USER
    python src/coach_cli.py session USER
    python src/coach_cli.py stats USER --days 30
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from user_manager import UserManager, SKILL_LEVELS, FEEDBACK_STYLES, PRACTICE_FREQUENCIES
from analytics import AnalyticsTracker
from personalized_coach import PersonalizedCoach


def cmd_user_create(args: argparse.Namespace) -> None:
    um = UserManager()
    profile = um.create_user(args.user_id, args.name, args.skill_level)
    print(f"Created user: {profile.user_id} ({profile.display_name}, {profile.skill_level})")


def cmd_user_list(_: argparse.Namespace) -> None:
    um = UserManager()
    users = um.list_users()
    if not users:
        print("No users yet.")
        return
    print(f"{'user_id':<20} {'name':<24} {'skill':<14} created")
    print("-" * 70)
    for u in users:
        print(f"{u.user_id:<20} {u.display_name:<24} {u.skill_level:<14} {u.created_at[:10]}")


def cmd_user_delete(args: argparse.Namespace) -> None:
    UserManager().delete_user(args.user_id)
    print(f"Deleted user: {args.user_id}")


def cmd_user_preferences(args: argparse.Namespace) -> None:
    um = UserManager()
    focus = None
    if args.focus_shots:
        focus = [s.strip() for s in args.focus_shots.split(",")]
    profile = um.set_user_preferences(
        args.user_id,
        feedback_style=args.feedback_style,
        focus_shots=focus,
        practice_frequency=args.practice_frequency,
    )
    print(f"Updated preferences for {profile.user_id}:")
    print(f"  feedback_style: {profile.feedback_style}")
    print(f"  focus_shots: {profile.focus_shots}")
    print(f"  practice_frequency: {profile.practice_frequency}")


def cmd_report(args: argparse.Namespace) -> None:
    coach = PersonalizedCoach()
    report = coach.get_overall_coaching_report(args.user_id)
    print(f"\n=== Coaching Report: {report['display_name']} ===")
    print(
        f"Overall Accuracy: {report['overall_accuracy']}% | "
        f"Predictions: {report['total_predictions']} | "
        f"Skill: {report['skill_level'].upper()}"
    )
    if report["per_shot_breakdown"]:
        print("\nShot Breakdown:")
        for shot, data in sorted(report["per_shot_breakdown"].items()):
            if data["attempts"]:
                print(f"  {shot}: {data['accuracy']}% ({data['attempts']} attempts)")
    if report["strongest_shots"]:
        print(f"\nStrongest: {', '.join(report['strongest_shots'])}")
    if report["weakest_shots"]:
        print(f"Weakest: {', '.join(report['weakest_shots'])}")
    if report["recommendations"]:
        print("\nRecommendations:")
        for r in report["recommendations"]:
            print(f"  • {r}")
    plan = report["training_plan"]
    print("\nDaily Routine:")
    for phase in ("warm_up", "main_training", "targeted_work", "cool_down"):
        for line in plan.get(phase, []):
            print(f"  - {line}")
    if report["motivational"]:
        print(f"\n{report['motivational']}")


def cmd_session(args: argparse.Namespace) -> None:
    coach = PersonalizedCoach()
    session = coach.get_session_feedback(args.user_id)
    print(f"\n{session['greeting']}")
    print(session["session_message"])
    if session["recommendations"]:
        print("\nRecommendations:")
        for r in session["recommendations"]:
            print(f"  • {r}")
    if session["technical_tips"]:
        print("\nTechnical Tips:")
        for t in session["technical_tips"]:
            print(f"  • {t}")


def cmd_stats(args: argparse.Namespace) -> None:
    tracker = AnalyticsTracker()
    stats = tracker.get_user_stats(args.user_id, days=args.days)
    print(f"\n=== Stats: {stats['user_id']} (last {args.days} days) ===")
    print(f"Total predictions: {stats['total_predictions']}")
    print(f"Labeled: {stats['labeled_predictions']}")
    print(f"Overall accuracy: {stats['overall_accuracy']}%")
    print(f"Avg confidence: {stats['avg_confidence']}")
    weak = tracker.get_weak_shots(args.user_id)
    if weak:
        print("\nWeak shots (<60% accuracy):")
        for w in weak:
            print(f"  {w['shot']}: {w['accuracy']}%")
    traj = tracker.get_improvement_trajectory(args.user_id, days=args.days)
    if traj:
        print("\nImprovement trajectory:")
        for point in traj[-7:]:
            print(f"  {point['date']}: {point['accuracy']}% ({point['predictions']} preds)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    user_p = sub.add_parser("user", help="User management")
    user_sub = user_p.add_subparsers(dest="user_cmd", required=True)

    p_create = user_sub.add_parser("create")
    p_create.add_argument("user_id")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--skill-level", default="intermediate", choices=SKILL_LEVELS)
    p_create.set_defaults(func=cmd_user_create)

    p_list = user_sub.add_parser("list")
    p_list.set_defaults(func=cmd_user_list)

    p_del = user_sub.add_parser("delete")
    p_del.add_argument("user_id")
    p_del.set_defaults(func=cmd_user_delete)

    p_pref = user_sub.add_parser("preferences")
    p_pref.add_argument("user_id")
    p_pref.add_argument("--feedback-style", choices=FEEDBACK_STYLES)
    p_pref.add_argument("--focus-shots", help="Comma-separated shot names")
    p_pref.add_argument("--practice-frequency", choices=PRACTICE_FREQUENCIES)
    p_pref.set_defaults(func=cmd_user_preferences)

    p_report = sub.add_parser("report")
    p_report.add_argument("user_id")
    p_report.set_defaults(func=cmd_report)

    p_session = sub.add_parser("session")
    p_session.add_argument("user_id")
    p_session.set_defaults(func=cmd_session)

    p_stats = sub.add_parser("stats")
    p_stats.add_argument("user_id")
    p_stats.add_argument("--days", type=int, default=30)
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    try:
        args.func(args)
    except (KeyError, ValueError) as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
