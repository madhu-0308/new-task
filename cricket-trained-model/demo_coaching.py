"""Demo script showing the personalized coaching feedback system."""

import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from coach import generate_coaching_feedback

# Create a synthetic pose sequence (T=50, 17 keypoints, 3 values per keypoint: x,y,confidence)
# This simulates a batsman playing a drive shot
print("=" * 70)
print("Cricket Shot Classifier — Personalized Coaching Demo")
print("=" * 70)

# Scenario 1: Good drive shot
print("\n[Scenario 1] Good Drive Shot with Stable Base")
print("-" * 70)
good_seq = np.random.randn(50, 17, 3) * 0.05  # Small random noise
good_seq[:, :, 2] = np.clip(np.random.randn(50, 17) * 0.15 + 0.85, 0, 1)  # High confidence
good_seq[:, 11:13, :2] *= 0.1  # Stable ankles/hips (low motion)
good_seq[:, 0, :2] *= 0.08    # Stable head (nose keypoint)
good_seq = good_seq.astype(np.float32)

probs_good = np.array([0.78, 0.12, 0.05, 0.03, 0.02] + [0.0]*10)
id_to_name = {
    0: "Cover Drive", 1: "Defensive", 2: "Pull", 3: "Sweep", 4: "Square Cut",
    5: "Hook", 6: "Flick", 7: "Lofted Offside", 8: "Lofted Legside", 9: "Scoop",
    10: "Reverse Sweep", 11: "Straight Drive", 12: "Late Cut", 13: "Down The Wicket", 14: "Upper Cut"
}

feedback1 = generate_coaching_feedback(good_seq, "Cover Drive", probs_good, id_to_name)
print(f"Shot Detected       : {feedback1['shot']}")
print(f"Confidence          : {feedback1['shot_confidence']:.2%}")
print(f"Main Issue          : {feedback1['issue']}")
print(f"Notes               : {feedback1['notes']}")
print(f"Advice              : {feedback1['advice']}")
print(f"\nCoach says: {feedback1['coach']}")

# Scenario 2: Shaky sweep with head movement
print("\n\n[Scenario 2] Sweep Shot with Head Movement & Unstable Feet")
print("-" * 70)
shaky_seq = np.random.randn(50, 17, 3) * 0.12  # Higher variance
shaky_seq[:, :, 2] = np.clip(np.random.randn(50, 17) * 0.2 + 0.65, 0, 1)  # Lower confidence
shaky_seq[:, 0, :2] *= 0.25   # More head movement (nose)
shaky_seq[:, 15:17, :2] *= 0.5  # More ankle/foot movement
shaky_seq = shaky_seq.astype(np.float32)

probs_shaky = np.array([0.05, 0.08, 0.12, 0.62, 0.08] + [0.05]*10)

feedback2 = generate_coaching_feedback(shaky_seq, "Sweep", probs_shaky, id_to_name)
print(f"Shot Detected       : {feedback2['shot']}")
print(f"Confidence          : {feedback2['shot_confidence']:.2%}")
print(f"Main Issue          : {feedback2['issue']}")
print(f"Notes               : {feedback2['notes']}")
print(f"Advice              : {feedback2['advice']}")
print(f"\nCoach says: {feedback2['coach']}")

# Scenario 3: Ambiguous shot (low confidence gap)
print("\n\n[Scenario 3] Ambiguous Shot (Model Unsure)")
print("-" * 70)
ambig_seq = np.random.randn(50, 17, 3) * 0.08
ambig_seq[:, :, 2] = np.clip(np.random.randn(50, 17) * 0.18 + 0.72, 0, 1)
ambig_seq = ambig_seq.astype(np.float32)

probs_ambig = np.array([0.35, 0.32, 0.15, 0.12, 0.04] + [0.02]*10)  # Close predictions

feedback3 = generate_coaching_feedback(ambig_seq, "Pull", probs_ambig, id_to_name)
print(f"Shot Detected       : {feedback3['shot']}")
print(f"Confidence          : {feedback3['shot_confidence']:.2%}")
print(f"Main Issue          : {feedback3['issue']}")
print(f"Notes               : {feedback3['notes']}")
print(f"Advice              : {feedback3['advice']}")
print(f"\nCoach says: {feedback3['coach']}")

print("\n" + "=" * 70)
print("Demo Complete — Personalized Coaching Features:")
print("  - Shot classification with confidence scores")
print("  - Automatic mistake detection (head movement, unstable feet, etc.)")
print("  - Personalized coaching advice")
print("  - Pose quality metrics")
print("=" * 70)
