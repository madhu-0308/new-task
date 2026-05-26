"""Flask REST API for personalized cricket coaching.

Run:
    python scripts/coach_api.py
    http://localhost:5000/api/docs
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from user_manager import UserManager, SKILL_LEVELS
from analytics import AnalyticsTracker
from personalized_coach import PersonalizedCoach

app = Flask(__name__)
CORS(app)

users = UserManager()
tracker = AnalyticsTracker()
coach = PersonalizedCoach(users, tracker)


API_DOCS = {
    "users": {
        "GET /api/users": "List all users",
        "POST /api/users": "Create user {user_id, display_name, skill_level}",
        "GET /api/users/<id>": "Get user profile",
        "DELETE /api/users/<id>": "Delete user",
        "PUT /api/users/<id>/preferences": "Update preferences",
    },
    "predictions": {
        "POST /api/users/<id>/predictions": "Record prediction {predicted_shot, confidence, video_path?}",
        "POST /api/predictions/<id>/feedback": "Record feedback {actual_shot, is_correct?}",
    },
    "coaching": {
        "GET /api/users/<id>/session": "Session feedback",
        "GET /api/users/<id>/report": "Full coaching report",
        "GET /api/users/<id>/stats?days=30": "User statistics",
        "GET /api/users/<id>/weak-shots": "Weak shot analysis",
    },
}


@app.route("/api/docs")
def api_docs():
    return jsonify(API_DOCS)


@app.route("/api/users", methods=["GET"])
def list_users():
    return jsonify([u.to_dict() for u in users.list_users()])


@app.route("/api/users", methods=["POST"])
def create_user():
    data = request.get_json(force=True) or {}
    user_id = data.get("user_id")
    display_name = data.get("display_name")
    skill_level = data.get("skill_level", "intermediate")
    if not user_id or not display_name:
        return jsonify({"error": "user_id and display_name required"}), 400
    if skill_level not in SKILL_LEVELS:
        return jsonify({"error": f"skill_level must be one of {SKILL_LEVELS}"}), 400
    try:
        profile = users.create_user(user_id, display_name, skill_level)
        return jsonify(profile.to_dict()), 201
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409


@app.route("/api/users/<user_id>", methods=["GET"])
def get_user(user_id: str):
    try:
        return jsonify(users.get_user(user_id).to_dict())
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/users/<user_id>", methods=["DELETE"])
def delete_user(user_id: str):
    try:
        users.delete_user(user_id)
        return jsonify({"deleted": user_id})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/users/<user_id>/preferences", methods=["PUT"])
def set_preferences(user_id: str):
    data = request.get_json(force=True) or {}
    try:
        profile = users.set_user_preferences(
            user_id,
            feedback_style=data.get("feedback_style"),
            focus_shots=data.get("focus_shots"),
            practice_frequency=data.get("practice_frequency"),
        )
        return jsonify(profile.to_dict())
    except (KeyError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/api/users/<user_id>/predictions", methods=["POST"])
def record_prediction(user_id: str):
    data = request.get_json(force=True) or {}
    shot = data.get("predicted_shot")
    confidence = data.get("confidence")
    if shot is None or confidence is None:
        return jsonify({"error": "predicted_shot and confidence required"}), 400
    try:
        users.get_user(user_id)
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    pred_id = tracker.record_prediction(
        user_id, data.get("video_path"), shot, float(confidence)
    )
    return jsonify({"prediction_id": pred_id, "predicted_shot": shot}), 201


@app.route("/api/predictions/<int:prediction_id>/feedback", methods=["POST"])
def record_feedback(prediction_id: int):
    data = request.get_json(force=True) or {}
    actual = data.get("actual_shot")
    if not actual:
        return jsonify({"error": "actual_shot required"}), 400
    try:
        tracker.record_feedback(
            prediction_id, actual, data.get("is_correct")
        )
        return jsonify({"ok": True, "prediction_id": prediction_id})
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/users/<user_id>/session", methods=["GET"])
def session_feedback(user_id: str):
    try:
        return jsonify(coach.get_session_feedback(user_id))
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/users/<user_id>/report", methods=["GET"])
def coaching_report(user_id: str):
    try:
        return jsonify(coach.get_overall_coaching_report(user_id))
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/users/<user_id>/stats", methods=["GET"])
def user_stats(user_id: str):
    days = request.args.get("days", type=int)
    try:
        users.get_user(user_id)
        return jsonify(tracker.get_user_stats(user_id, days=days))
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/users/<user_id>/weak-shots", methods=["GET"])
def weak_shots(user_id: str):
    try:
        users.get_user(user_id)
        return jsonify(tracker.get_weak_shots(user_id))
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404


@app.route("/api/users/<user_id>/predict-video", methods=["POST"])
def predict_video(user_id: str):
    """Upload a video file and run full inference + tracking."""
    if "video" not in request.files:
        return jsonify({"error": "multipart field 'video' required"}), 400
    try:
        users.get_user(user_id)
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404

    sys.path.insert(0, str(PROJECT_ROOT / "src"))
    from predict_personalized import run_prediction, PROJECT_ROOT as PR  # noqa: E402

    f = request.files["video"]
    suffix = Path(f.filename or "clip.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        f.save(tmp.name)
        tmp_path = Path(tmp.name)

    ckpt = PR / "runs" / "exp1" / "best.pt"
    device = "cpu"
    try:
        shot, confidence, seq, id_to_name, probs = run_prediction(
            tmp_path, ckpt, "yolov8n-pose.pt", device
        )
        pred_id = tracker.record_prediction(user_id, f.filename, shot, confidence)
        actual = request.form.get("actual_shot")
        if actual:
            tracker.record_feedback(pred_id, actual)
        from coach import generate_coaching_feedback  # noqa: E402
        pose_fb = generate_coaching_feedback(seq, shot, probs, id_to_name)
        session = coach.get_session_feedback(user_id) if request.form.get("feedback") else None
        return jsonify({
            "prediction_id": pred_id,
            "shot": shot,
            "confidence": confidence,
            "pose_feedback": pose_fb,
            "session_feedback": session,
        })
    except SystemExit as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    print("Coach API — http://localhost:5000/api/docs")
    app.run(host="0.0.0.0", port=5000, debug=False)
