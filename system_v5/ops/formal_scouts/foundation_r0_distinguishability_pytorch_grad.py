#!/usr/bin/env python3
"""PyTorch torch.func sensitivity leg for foundation_r0_distinguishability."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_r0_distinguishability_pytorch_grad.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_r0_distinguishability_pytorch_grad_results.json"
DTYPE = torch.float64
TOL = 1.0e-12

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed


def rho_from_coherence(t: torch.Tensor) -> torch.Tensor:
    half = torch.tensor(0.5, dtype=DTYPE)
    return torch.stack(
        (
            torch.stack((half, half * t)),
            torch.stack((half * t, half)),
        )
    )


def projectors() -> dict[str, list[torch.Tensor]]:
    z0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=DTYPE)
    z1 = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=DTYPE)
    xp = torch.tensor([[0.5, 0.5], [0.5, 0.5]], dtype=DTYPE)
    xm = torch.tensor([[0.5, -0.5], [-0.5, 0.5]], dtype=DTYPE)
    return {"Z": [z0, z1], "X": [xp, xm]}


def born_vector(rho: torch.Tensor, effects: list[torch.Tensor]) -> torch.Tensor:
    return torch.stack([torch.trace(effect @ rho) for effect in effects])


def distinguishability_metric(t: torch.Tensor, family: tuple[str, ...]) -> torch.Tensor:
    effects = projectors()
    rho_a = rho_from_coherence(t)
    rho_b = rho_from_coherence(torch.tensor(-1.0, dtype=DTYPE))
    total = torch.tensor(0.0, dtype=DTYPE)
    for probe in family:
        diff = born_vector(rho_a, effects[probe]) - born_vector(rho_b, effects[probe])
        total = total + torch.sum(diff * diff)
    return total


def metric_and_grad(family: tuple[str, ...], t_value: float) -> dict[str, float]:
    t = torch.tensor(t_value, dtype=DTYPE)
    metric = distinguishability_metric(t, family)
    grad = jacrev(lambda x: distinguishability_metric(x, family))(t)
    return {"metric": float(metric.detach()), "jacrev_grad": float(grad.detach())}


def constraint_report() -> dict[str, Any]:
    rows = {}
    for state_id, t_value in {"rho_a_x_plus": 1.0, "rho_b_x_minus": -1.0, "maximally_mixed": 0.0}.items():
        rho = rho_from_coherence(torch.tensor(t_value, dtype=DTYPE))
        eigenvalues = torch.linalg.eigvalsh(rho)
        norms = {probe: float(torch.sum(born_vector(rho, rows)).detach()) for probe, rows in projectors().items()}
        rows[state_id] = {
            "trace": float(torch.trace(rho).detach()),
            "trace_is_one": abs(float(torch.trace(rho).detach()) - 1.0) <= TOL,
            "hermitian_max_gap": float(torch.max(torch.abs(rho - rho.T)).detach()),
            "psd_min_eigenvalue": float(torch.min(eigenvalues).detach()),
            "probability_normalizations": norms,
        }
    return rows


def main() -> int:
    z = metric_and_grad(("Z",), 1.0)
    zx = metric_and_grad(("Z", "X"), 1.0)
    constraints = constraint_report()
    all_constraints_ok = all(
        row["trace_is_one"]
        and row["hermitian_max_gap"] <= TOL
        and row["psd_min_eigenvalue"] >= -TOL
        and all(abs(v - 1.0) <= TOL for v in row["probability_normalizations"].values())
        for row in constraints.values()
    )
    all_pass = (
        abs(z["metric"]) <= TOL
        and abs(z["jacrev_grad"]) <= TOL
        and zx["metric"] > 1.0
        and abs(zx["jacrev_grad"]) > 1.0
        and all_constraints_ok
    )
    result = {
        "schema": "foundation_r0_distinguishability_engine_leg_v2",
        "object_id": "foundation_r0_distinguishability_pytorch_grad",
        "rung_id": "foundation_r0_distinguishability",
        "classification": CLASSIFICATION,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": False,
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "packages_used": ["torch", "torch.func", "json"],
        "aligned_packages_load_bearing": ["torch.func"],
        "claim_path_tools": ["torch", "torch.func"],
        "torch_dtype": "float64",
        "M": {"M1": ["Z"], "M2": ["Z", "X"]},
        "C": {
            "trace_one": True,
            "psd": True,
            "hermitian": True,
            "probability_normalization": True,
            "rung_specific_constraint": "differentiable coherence parameter t changes X distinguishability but not Z distinguishability for the witness direction",
            "per_state": constraints,
        },
        "S_mod_M": {
            "sensitivity_parameter": "rho(t)=1/2[[1,t],[t,1]], rho_b=rho(-1), witness rho_a=rho(1)",
            "D_Z": z,
            "D_ZX": zx,
        },
        "witness_pair": {
            "rho_a": "rho(1)=|+><+|",
            "rho_b": "rho(-1)=|-><-|",
            "D_Z": z["metric"],
            "D_ZX": zx["metric"],
            "jacrev_grad_D_Z": z["jacrev_grad"],
            "jacrev_grad_D_ZX": zx["jacrev_grad"],
        },
        "negative_control_flip": {
            "control": "erase_X_from_D_ZX",
            "D_Z_grad_zero": abs(z["jacrev_grad"]) <= TOL,
            "D_ZX_grad_nonzero": abs(zx["jacrev_grad"]) > 1.0,
        },
        "summary": {
            "D_Z": z["metric"],
            "D_ZX": zx["metric"],
            "jacrev_grad_D_Z": z["jacrev_grad"],
            "jacrev_grad_D_ZX": zx["jacrev_grad"],
            "all_pass": all_pass,
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote: {RESULT_PATH}")
    print(
        "PYTORCH_FOUNDATION_R0_DONE "
        f"all_pass={str(all_pass).lower()} "
        f"D_Z={z['metric']} grad_Z={z['jacrev_grad']} "
        f"D_ZX={zx['metric']} grad_ZX={zx['jacrev_grad']}"
    )
    return 0 if all_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
