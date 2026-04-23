"""Standalone amplitude damping torch module.

This file is the first standalone family-level torch module extracted from the
family sims. The module remains intentionally small: one differentiable
nn.Module surface, plus a helper to inspect Kraus operators.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class AmplitudeDamping(nn.Module):
    """Differentiable amplitude damping channel parameterized by gamma."""

    def __init__(self, gamma: float = 0.5):
        super().__init__()
        self.gamma = nn.Parameter(torch.tensor(float(gamma)))

    def forward(self, rho: torch.Tensor) -> torch.Tensor:
        g = self.gamma
        one_r = torch.tensor(1.0, dtype=torch.float32, device=rho.device)
        zero_c = torch.tensor(0.0, dtype=rho.dtype, device=rho.device)
        one_c = torch.tensor(1.0, dtype=rho.dtype, device=rho.device)

        sqrt_1mg = torch.sqrt(torch.clamp(one_r - g, min=1e-30)).to(rho.dtype)
        sqrt_g = torch.sqrt(torch.clamp(g, min=1e-30)).to(rho.dtype)

        K0 = torch.stack([
            torch.stack([one_c, zero_c]),
            torch.stack([zero_c, sqrt_1mg]),
        ])
        K1 = torch.stack([
            torch.stack([zero_c, sqrt_g]),
            torch.stack([zero_c, zero_c]),
        ])

        return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

    def kraus_operators(self) -> tuple[torch.Tensor, torch.Tensor]:
        """Return Kraus operators for inspection/debugging."""
        g = self.gamma
        one = torch.tensor(1.0, dtype=torch.complex64)
        zero = torch.tensor(0.0, dtype=torch.complex64)
        sqrt_1mg = torch.sqrt(torch.clamp((one - g.to(torch.complex64)), min=0.0))
        sqrt_g = torch.sqrt(torch.clamp(g.to(torch.complex64), min=0.0))

        K0 = torch.tensor([[1, 0], [0, 0]], dtype=torch.complex64)
        K0[1, 1] = sqrt_1mg
        K1 = torch.tensor([[0, 0], [0, 0]], dtype=torch.complex64)
        K1[0, 1] = sqrt_g
        return K0, K1


__all__ = ["AmplitudeDamping"]
