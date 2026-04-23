#!/usr/bin/env python3
"""
Standalone torch.nn.Module for the single-qubit depolarizing channel.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class Depolarizing(nn.Module):
    """Differentiable depolarizing channel parameterized by strength p."""

    def __init__(self, p: float = 0.5):
        super().__init__()
        self.p = nn.Parameter(torch.tensor(float(p)))

    def forward(self, rho: torch.Tensor) -> torch.Tensor:
        dim = rho.shape[-1]
        identity = torch.eye(dim, dtype=rho.dtype, device=rho.device)
        p = self.p.to(rho.dtype)
        return (1 - p) * rho + p * identity / dim

    def kraus_operators(self) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        p = self.p
        identity = torch.eye(2, dtype=torch.complex64)
        x_gate = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64)
        y_gate = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex64)
        z_gate = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64)

        k0 = torch.sqrt((1 - 3 * p / 4).to(torch.complex64)) * identity
        k1 = torch.sqrt((p / 4).to(torch.complex64)) * x_gate
        k2 = torch.sqrt((p / 4).to(torch.complex64)) * y_gate
        k3 = torch.sqrt((p / 4).to(torch.complex64)) * z_gate
        return k0, k1, k2, k3
