"""PyTorch Dataset over pose-sequence .npy files."""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


# COCO-17 left/right pairs (left, right). Index 0 (nose) has no pair.
_LR_PAIRS = [(1, 2), (3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14), (15, 16)]


def flip_horizontal(arr: np.ndarray) -> np.ndarray:
    """Mirror keypoints in x and swap left/right indices. Confidence untouched."""
    out = arr.copy()
    out[:, :, 0] *= -1.0
    for l, r in _LR_PAIRS:
        out[:, [l, r]] = out[:, [r, l]]
    return out


class PoseDataset(Dataset):
    """Loads (T, 17, 3) pose arrays from a split file.

    Each split line: '<class>/<file.npy>\\t<class_id>'.
    Returns (x: (T, 51) float32, y: int64).
    """

    def __init__(self, split_file: Path, poses_root: Path, augment: bool = False):
        self.poses_root = Path(poses_root)
        self.augment = augment
        self.samples: list[tuple[Path, int]] = []
        for line in Path(split_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            rel, cid = line.split("\t")
            self.samples.append((self.poses_root / rel, int(cid)))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, i: int):
        path, cid = self.samples[i]
        arr = np.load(path).astype(np.float32)  # (T, 17, 3)

        if self.augment:
            # horizontal flip — handedness invariance
            if random.random() < 0.5:
                arr = flip_horizontal(arr)
            # small gaussian noise on (x, y)
            arr[:, :, :2] += np.random.normal(0.0, 0.02, arr[:, :, :2].shape).astype(np.float32)
            # random scale (zoom)
            s = float(np.random.uniform(0.9, 1.1))
            arr[:, :, :2] *= s

        T = arr.shape[0]
        x = arr.reshape(T, -1)  # (T, 51)
        return torch.from_numpy(x), torch.tensor(cid, dtype=torch.long)