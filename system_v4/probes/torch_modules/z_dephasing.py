"""Standalone Z-dephasing torch module."""

from __future__ import annotations

import torch
import torch.nn as nn


class ZDephasing(nn.Module):
    """Differentiable Z-dephasing channel parameterized by strength p."""

    def __init__(self, p: float = 0.5):
        super().__init__()
        self.p = nn.Parameter(torch.tensor(float(p)))

    def forward(self, rho: torch.Tensor) -> torch.Tensor:
        z_op = torch.tensor([[1, 0], [0, -1]], dtype=rho.dtype, device=rho.device)
        p = self.p.to(rho.dtype)
        return (1 - p) * rho + p * (z_op @ rho @ z_op)

    def kraus_operators(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Return Kraus operators for inspection/debugging."""
        p = self.p
        identity = torch.eye(2, dtype=torch.complex64)
        z_op = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex64)
        k0 = torch.sqrt((1 - p).to(torch.complex64)) * identity
        k1 = torch.sqrt(p.to(torch.complex64)) * z_op
        return k0, k1


__all__ = ["ZDephasing"]
