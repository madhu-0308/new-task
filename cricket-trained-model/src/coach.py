"""Lightweight shot coaching and feedback for pose-sequence inference."""

from __future__ import annotations

import numpy as np

NOSE = 0
L_WRIST = 9
R_WRIST = 10
L_ANKLE = 15
R_ANKLE = 16
L_SHOULDER = 5
R_SHOULDER = 6
L_HIP = 11
R_HIP = 12


def _valid_frames(seq: np.ndarray) -> np.ndarray:
    return np.any(np.abs(seq[:, :, :2]) > 1e-6, axis=(1, 2))


def compute_pose_metrics(seq: np.ndarray) -> dict[str, float]:
    valid = _valid_frames(seq)
    visible_ratio = float(np.mean(valid))
    if visible_ratio <= 0:
        return {
            "visible_ratio": 0.0,
            "avg_confidence": 0.0,
            "head_stillness": 0.0,
            "wrist_motion": 0.0,
            "ankle_motion": 0.0,
            "torso_tilt": 0.0,
        }

    frames = seq[valid]
    confidences = frames[:, :, 2]
    avg_confidence = float(np.nanmean(confidences))

    nose = frames[:, NOSE, :2]
    head_stillness = float(np.mean(np.linalg.norm(nose - nose.mean(axis=0), axis=1)))

    wrists = frames[:, [L_WRIST, R_WRIST], :2]
    wrist_mean = wrists.mean(axis=1, keepdims=True)
    wrist_motion = float(np.mean(np.linalg.norm(wrists - wrist_mean, axis=2)))

    ankles = frames[:, [L_ANKLE, R_ANKLE], :2]
    ankle_mean = ankles.mean(axis=1, keepdims=True)
    ankle_motion = float(np.mean(np.linalg.norm(ankles - ankle_mean, axis=2)))

    shoulder_mid = (frames[:, L_SHOULDER, :2] + frames[:, R_SHOULDER, :2]) / 2.0
    hip_mid = (frames[:, L_HIP, :2] + frames[:, R_HIP, :2]) / 2.0
    torso_tilt = float(np.mean(np.abs(shoulder_mid[:, 0] - hip_mid[:, 0])))

    return {
        "visible_ratio": visible_ratio,
        "avg_confidence": avg_confidence,
        "head_stillness": head_stillness,
        "wrist_motion": wrist_motion,
        "ankle_motion": ankle_motion,
        "torso_tilt": torso_tilt,
    }


def generate_coaching_feedback(
    seq: np.ndarray,
    shot: str,
    probs: np.ndarray,
    id_to_name: dict[int, str],
) -> dict[str, str | float]:
    metrics = compute_pose_metrics(seq)
    topk = np.argsort(probs)[::-1]
    primary_confidence = float(probs[topk[0]])
    second_confidence = float(probs[topk[1]]) if len(topk) > 1 else 0.0
    confidence_gap = primary_confidence - second_confidence

    issue = "Good balance and stable posture."
    notes: list[str] = []
    advice: list[str] = []

    if metrics["visible_ratio"] < 0.6:
        issue = "The batsman is not visible enough."
        notes.append("Keep the full batsman frame in view.")
    if metrics["avg_confidence"] < 0.55:
        issue = "Pose extraction is weak."
        notes.append("Improve lighting or framing for clearer pose detection.")
    if metrics["head_stillness"] > 0.08:
        issue = "Head movement is too large."
        advice.append("Keep your head steady during the shot.")
    if metrics["torso_tilt"] > 0.18:
        issue = "Your upper body is leaning too much."
        advice.append("Keep your torso aligned and balanced over your base.")
    if metrics["ankle_motion"] > 0.24:
        issue = "Feet are moving too much before impact."
        advice.append("Commit your front foot and maintain a stable base.")
    if primary_confidence < 0.7:
        issue = "Shot prediction is not confident."
        notes.append("The model is unsure of the exact shot type.")
    if confidence_gap < 0.12 and len(topk) > 1:
        issue = f"Shot is ambiguous between {shot} and {id_to_name[topk[1]]}."
        notes.append("Try a cleaner clip with a clearer bat path.")

    # Shot-specific tips and drills (short, safe guidance)
    shot_tips = {
        "cover drive": (
            "Front-foot weight transfer and head-over-ball.",
            "Drill: practice front-foot step-and-pause drives focusing on head stability."
        ),
        "straight drive": (
            "Lean into the line and drive through the ball.",
            "Drill: shadow drives with a focus on chest-over-front-knee."
        ),
        "hook": (
            "Watch the short ball; rotate hips and keep eyes on the contact point.",
            "Drill: short-ball throwdowns to practise timing and compact bat path."
        ),
        "pull": (
            "Transfer weight and open hips for horizontal bat swing.",
            "Drill: side-net drills focusing on timing and hip rotation."
        ),
        "sweep": (
            "Low body position and stable head while reaching across the line.",
            "Drill: kneeling sweep reps to fix head and torso alignment."
        ),
        "square cut": (
            "Quick bat-lift and late hand speed for late, low balls.",
            "Drill: short lateral bat-speed drills with a coach or throwdown."
        ),
        "defensive": (
            "Soft hands and block with the bat close to the body.",
            "Drill: block-and-hold drills to feel the bat face on contact."
        ),
    }
    tip_key = shot.lower()
    if tip_key in shot_tips:
        t_short, t_drill = shot_tips[tip_key]
        advice.append(t_short)
        notes.append(t_drill)

    if not notes:
        notes.append("No serious mistakes detected.")
    if not advice:
        advice.append("Keep the same motion and focus on consistency.")

    one_word_coach = "Coach: personalized"
    summary = (
        f"Shot detected: {shot}. "
        f"Confidence {primary_confidence:.2f}. "
        f"{issue}"
    )

    # Compose a concise corrections field that a user can act on
    corrections: list[str] = []
    if metrics["head_stillness"] > 0.08:
        corrections.append("Head: reduce lateral movement; keep eyes on the ball.")
    if metrics["torso_tilt"] > 0.18:
        corrections.append("Torso: avoid excessive lean; balance over your base.")
    if metrics["ankle_motion"] > 0.24:
        corrections.append("Feet: stabilize your base; commit the front foot.")
    if metrics["avg_confidence"] < 0.55:
        corrections.append("Pose quality: improve lighting/framing for clearer feedback.")
    if not corrections:
        corrections.append("No major body-mechanics corrections detected — focus on consistency.")

    return {
        "coach": one_word_coach,
        "shot": shot,
        "shot_confidence": primary_confidence,
        "issue": issue,
        "notes": " ".join(notes),
        "advice": " ".join(advice),
        "corrections": " ".join(corrections),
        "summary": summary,
        **metrics,
    }
