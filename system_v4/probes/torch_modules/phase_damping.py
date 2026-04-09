#!/usr/bin/env python3
"""
Standalone torch.nn.Module for the single-qubit phase damping channel.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class PhaseDamping(nn.Module):
    """Differentiable phase damping channel parameterized by lam (lambda)."""

    def __init__(self, lam: float = 0.5):
        super().__init__()
        self.lam = nn.Parameter(torch.tensor(float(lam)))

    def forward(self, rho: torch.Tensor) -> torch.Tensor:
        lam = self.lam.to(rho.dtype)
        decay = torch.sqrt((1 - lam).to(rho.dtype))
        out = rho.clone()
        out[0, 1] = decay * rho[0, 1]
        out[1, 0] = decay * rho[1, 0]
        return out

    def kraus_operators(self) -> tuple[torch.Tensor, torch.Tensor]:
        lam = self.lam
        k0 = torch.zeros(2, 2, dtype=torch.complex64)
        k0[0, 0] = 1.0
        k0[1, 1] = torch.sqrt((1 - lam).to(torch.complex64))

        k1 = torch.zeros(2, 2, dtype=torch.complex64)
        k1[1, 1] = torch.sqrt(lam.to(torch.complex64))
        return k0, k1
