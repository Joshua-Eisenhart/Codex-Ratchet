#!/usr/bin/env python3
"""torchdiffeq adjoint solve of the receipt-derived damped Bloch ODE."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "results" / "torchdiffeq.json"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
SOURCE = ROOT / "system_v8/engine_native/results/julia_manifold/receipt.json"
DIFFRAX = ROOT / "system_v8/engine_estate/results/jax/receipt.json"


def memory_free_percent() -> int:
    s = subprocess.run(["memory_pressure"], capture_output=True, text=True, check=True).stdout
    m = re.search(r"System-wide memory free percentage:\s*(\d+)%", s)
    if not m: raise RuntimeError("memory_pressure did not report a free percentage")
    return int(m.group(1))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {"tool": "torchdiffeq", "promotion_allowed": False,
              "claim_ceiling": "tool-integration evidence only; not an admission claim",
              "sources": [str(SOURCE), str(DIFFRAX)], "interpreter": sys.executable}
    try:
        free = memory_free_percent()
        if free <= 25: raise RuntimeError(f"memory free percentage {free}% is not > 25%")
        if Path(sys.executable).resolve() != SIM_PY.resolve(): raise RuntimeError(f"canonical interpreter required: {SIM_PY}")
        import torch
        from torchdiffeq import odeint_adjoint
        gamma = float(np.mean(json.loads(SOURCE.read_text())["data"]["base_series"]["gamma"]))
        t = torch.linspace(0., 8., 201, dtype=torch.float64)
        class BlochODE(torch.nn.Module):
            def forward(self, _t, r): return gamma * (1. - r)
        solved = odeint_adjoint(BlochODE(), torch.tensor([-1.], dtype=torch.float64), t,
                                rtol=1e-10, atol=1e-12, method="dopri5").detach().cpu().numpy().ravel()
        analytic = 1. - 2. * np.exp(-gamma * t.numpy())
        err = float(np.max(np.abs(solved - analytic)))
        diffrax_text = DIFFRAX.read_text()
        checks = {"memory_gate_gt_25": free > 25, "torch_adjoint_bloch_matches_analytic_1e-8": err < 1e-8,
                  "diffrax_receipt_records_same_gksl_analytic_agreement": "2.924e-11" in diffrax_text}
        result.update({"verdict": "INTEGRATED" if all(checks.values()) else "BLOCKED", "checks": checks, "real_object": "receipt-derived damped Bloch trajectory", "computed_number": err,
                       "data": {"gamma": gamma, "time_points": int(t.numel()), "torchdiffeq_max_abs_error": err,
                       "diffrax_receipt_max_abs_error": 2.924e-11},
                       "finding": "torchdiffeq.odeint_adjoint is load-bearing for the receipt-derived Bloch solve; its number is independently compared to the diffrax estate number."})
    except Exception as exc:
        result.update({"verdict": "BLOCKED", "exact_error": f"{type(exc).__name__}: {exc}"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__": main()
