#!/usr/bin/env python3
"""
Standalone torch.nn.Module for the single-qubit bit-flip channel.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class BitFlip(nn.Module):
    """Differentiable bit-flip channel parameterized by flip probability p."""

    def __init__(self, p: float = 0.5):
        super().__init__()
        self.p = nn.Parameter(torch.tensor(float(p)))

    def forward(self, rho: torch.Tensor) -> torch.Tensor:
        x_gate = torch.tensor([[0, 1], [1, 0]], dtype=rho.dtype, device=rho.device)
        p = self.p.to(rho.dtype)
        return (1 - p) * rho + p * (x_gate @ rho @ x_gate)

    def kraus_operators(self) -> tuple[torch.Tensor, torch.Tensor]:
        p = self.p
        identity = torch.eye(2, dtype=torch.complex64)
        x_gate = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex64)
        k0 = torch.sqrt((1 - p).to(torch.complex64)) * identity
        k1 = torch.sqrt(p.to(torch.complex64)) * x_gate
        return k0, k1
