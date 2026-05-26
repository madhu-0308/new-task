"""
SORT: Simple Online and Realtime Tracking
------------------------------------------
Kalman-filter based multi-object tracker with Hungarian algorithm
for data association. Used to maintain persistent ball/bat IDs
across frames even when detection temporarily fails.

Reference: Bewley et al. 2016 — https://arxiv.org/abs/1602.00763
"""

from __future__ import annotations

import logging
from typing import List

import numpy as np
from filterpy.kalman import KalmanFilter
from scipy.optimize import linear_sum_assignment

logger = logging.getLogger(__name__)


def iou_batch(bb_test: np.ndarray, bb_gt: np.ndarray) -> np.ndarray:
    """
    Compute IoU matrix between two sets of bounding boxes.

    Args:
        bb_test: (N, 4) array [x1, y1, x2, y2]
        bb_gt:   (M, 4) array [x1, y1, x2, y2]

    Returns:
        (N, M) IoU matrix
    """
    bb_gt = np.expand_dims(bb_gt, 0)     # (1, M, 4)
    bb_test = np.expand_dims(bb_test, 1)  # (N, 1, 4)

    xx1 = np.maximum(bb_test[..., 0], bb_gt[..., 0])
    yy1 = np.maximum(bb_test[..., 1], bb_gt[..., 1])
    xx2 = np.minimum(bb_test[..., 2], bb_gt[..., 2])
    yy2 = np.minimum(bb_test[..., 3], bb_gt[..., 3])

    w = np.maximum(0.0, xx2 - xx1)
    h = np.maximum(0.0, yy2 - yy1)
    intersection = w * h

    area_test = (bb_test[..., 2] - bb_test[..., 0]) * (bb_test[..., 3] - bb_test[..., 1])
    area_gt   = (bb_gt[..., 2]   - bb_gt[..., 0])   * (bb_gt[..., 3]   - bb_gt[..., 1])
    union = area_test + area_gt - intersection

    return np.where(union > 0, intersection / union, 0.0)


def _bbox_to_z(bbox: np.ndarray) -> np.ndarray:
    """Convert [x1, y1, x2, y2] → [cx, cy, area, aspect_ratio] (column vector)."""
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x = bbox[0] + w / 2.0
    y = bbox[1] + h / 2.0
    s = w * h
    r = w / float(h) if h > 1e-6 else 1.0
    return np.array([[x], [y], [s], [r]], dtype=float)


def _x_to_bbox(x: np.ndarray) -> np.ndarray:
    """Convert Kalman state [cx, cy, area, r, ...] → [x1, y1, x2, y2]."""
    s = float(x[2])
    r = float(x[3])
    if s <= 0:
        s = 1e-6
    w = np.sqrt(max(s * r, 1e-6))
    h = s / w if w > 1e-6 else 1.0
    return np.array([
        x[0] - w / 2.0,
        x[1] - h / 2.0,
        x[0] + w / 2.0,
        x[1] + h / 2.0,
    ], dtype=float)


class KalmanBoxTracker:
    """
    Tracks a single bounding box using a Kalman Filter.

    State vector: [cx, cy, area, r, d_cx, d_cy, d_area]
    Measurement:  [cx, cy, area, r]
    """

    _id_counter: int = 0

    def __init__(self, bbox: np.ndarray) -> None:
        self.kf = KalmanFilter(dim_x=7, dim_z=4)

        # Constant-velocity motion model
        self.kf.F = np.array([
            [1, 0, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 0, 1],
            [0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 0, 1],
        ], dtype=float)

        # Observation matrix: observe position + size
        self.kf.H = np.array([
            [1, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0],
        ], dtype=float)

        # Measurement noise (larger for area/ratio)
        self.kf.R[2:, 2:] *= 10.0
        # High uncertainty in velocity at init
        self.kf.P[4:, 4:] *= 1000.0
        self.kf.P *= 10.0
        # Low process noise for velocities
        self.kf.Q[-1, -1] *= 0.01
        self.kf.Q[4:, 4:] *= 0.01

        self.kf.x[:4] = _bbox_to_z(bbox)

        self.time_since_update: int = 0
        self.id: int = KalmanBoxTracker._id_counter
        KalmanBoxTracker._id_counter += 1

        self.history: List[np.ndarray] = []
        self.hits: int = 0
        self.hit_streak: int = 0
        self.age: int = 0

    def update(self, bbox: np.ndarray) -> None:
        """Feed a new detection into the Kalman filter."""
        self.time_since_update = 0
        self.history.clear()
        self.hits += 1
        self.hit_streak += 1
        self.kf.update(_bbox_to_z(bbox))

    def predict(self) -> np.ndarray:
        """Advance the state estimate and return predicted bounding box."""
        # Clamp area velocity so area never goes negative
        if (self.kf.x[6] + self.kf.x[2]) <= 0:
            self.kf.x[6] *= 0.0

        self.kf.predict()
        self.age += 1

        if self.time_since_update > 0:
            self.hit_streak = 0
        self.time_since_update += 1

        pred = _x_to_bbox(self.kf.x)
        self.history.append(pred)
        return pred

    def get_state(self) -> np.ndarray:
        """Return current best estimate of bounding box [x1, y1, x2, y2]."""
        return _x_to_bbox(self.kf.x)

    @classmethod
    def reset_id_counter(cls) -> None:
        cls._id_counter = 0


def _associate_detections_to_trackers(
    detections: np.ndarray,
    trackers: np.ndarray,
    iou_threshold: float = 0.3,
):
    """
    Hungarian algorithm assignment.

    Returns:
        matches:         (K, 2) matched [det_idx, trk_idx]
        unmatched_dets:  indices of unmatched detections
        unmatched_trks:  indices of unmatched trackers
    """
    if len(trackers) == 0:
        return (
            np.empty((0, 2), dtype=int),
            np.arange(len(detections), dtype=int),
            np.empty(0, dtype=int),
        )

    iou_mat = iou_batch(detections[:, :4], trackers[:, :4])
    row_ind, col_ind = linear_sum_assignment(-iou_mat)

    unmatched_dets = [d for d in range(len(detections)) if d not in row_ind]
    unmatched_trks = [t for t in range(len(trackers)) if t not in col_ind]

    matches = []
    for r, c in zip(row_ind, col_ind):
        if iou_mat[r, c] < iou_threshold:
            unmatched_dets.append(r)
            unmatched_trks.append(c)
        else:
            matches.append([r, c])

    matches_arr = np.array(matches, dtype=int).reshape(-1, 2) if matches else np.empty((0, 2), dtype=int)
    return matches_arr, np.array(unmatched_dets, dtype=int), np.array(unmatched_trks, dtype=int)


class Sort:
    """
    SORT multi-object tracker.

    Usage:
        tracker = Sort()
        for frame in video:
            dets = detector.detect(frame)  # [[x1,y1,x2,y2,score], ...]
            tracks = tracker.update(dets)   # [[x1,y1,x2,y2,id], ...]
    """

    def __init__(
        self,
        max_age: int = 5,
        min_hits: int = 3,
        iou_threshold: float = 0.3,
    ) -> None:
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers: List[KalmanBoxTracker] = []
        self.frame_count: int = 0

    def update(self, dets: np.ndarray = np.empty((0, 5))) -> np.ndarray:
        """
        Update tracker with new detections.

        Args:
            dets: (N, 5) array [[x1, y1, x2, y2, score], ...]
                  Pass np.empty((0, 5)) when no detections in a frame.

        Returns:
            (M, 5) array [[x1, y1, x2, y2, track_id], ...]
            Only returns confirmed tracks (hit_streak >= min_hits).
        """
        self.frame_count += 1

        # Predict all existing trackers
        trks = np.zeros((len(self.trackers), 5))
        to_delete: List[int] = []
        for t, trk_arr in enumerate(trks):
            pos = self.trackers[t].predict()
            trk_arr[:] = [pos[0], pos[1], pos[2], pos[3], 0]
            if np.any(np.isnan(pos)):
                to_delete.append(t)

        trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
        for t in reversed(to_delete):
            self.trackers.pop(t)

        matched, unmatched_dets, unmatched_trks = _associate_detections_to_trackers(
            dets, trks, self.iou_threshold
        )

        # Update matched trackers with new detections
        for m in matched:
            self.trackers[m[1]].update(dets[m[0]])

        # Create new trackers for unmatched detections
        for i in unmatched_dets:
            self.trackers.append(KalmanBoxTracker(dets[i]))

        # Collect active tracks and remove stale ones
        results = []
        for trk in reversed(self.trackers):
            state = trk.get_state()
            active = (trk.time_since_update < 1) and (
                trk.hit_streak >= self.min_hits or self.frame_count <= self.min_hits
            )
            if active:
                results.append(np.concatenate([state, [trk.id + 1]]).reshape(1, -1))
            if trk.time_since_update > self.max_age:
                self.trackers.remove(trk)

        return np.concatenate(results) if results else np.empty((0, 5))

    def reset(self) -> None:
        """Reset tracker state (call between video clips)."""
        self.trackers.clear()
        self.frame_count = 0
