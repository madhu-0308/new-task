"""Small Transformer over pose-keypoint sequences."""

from __future__ import annotations

import torch
import torch.nn as nn


class PoseTransformer(nn.Module):
    def __init__(
        self,
        num_classes: int,
        T: int = 50,
        in_dim: int = 51,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 2,
        dim_ff: int = 128,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.in_proj = nn.Linear(in_dim, d_model)
        self.pos_emb = nn.Parameter(torch.zeros(1, T, d_model))
        layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_ff,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=num_layers)
        self.head = nn.Sequential(
            nn.LayerNorm(d_model),
            nn.Dropout(dropout),
            nn.Linear(d_model, num_classes),
        )
        nn.init.trunc_normal_(self.pos_emb, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, T, in_dim)
        h = self.in_proj(x) + self.pos_emb[:, : x.size(1)]
        h = self.encoder(h)
        h = h.mean(dim=1)  # mean-pool over time
        return self.head(h)
