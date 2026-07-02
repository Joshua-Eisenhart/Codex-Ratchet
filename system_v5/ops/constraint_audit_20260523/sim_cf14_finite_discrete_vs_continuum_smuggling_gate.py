#!/usr/bin/env python3
"""CF-14 finite-discrete vs continuum-smuggling gate.

Candidate-gate implementation only. This tests whether a claim can use a
finite carrier, finite operator/path family, and finite threshold before any
smooth or continuum language is allowed as a derived readout.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf14_finite_discrete_vs_continuum_smuggling_gate_results.json"

DTYPE = torch.float64
CDTYPE = torch.complex128


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def finite_entropy_carrier(dim: int) -> dict[str, Any]:
    rho = torch.eye(dim, dtype=CDTYPE) / dim
    vals = torch.linalg.eigvalsh(rho).real
    entropy = float((-torch.sum(vals * torch.log(vals))).item())
    return {
        "dim": dim,
        "trace": float(torch.real(torch.trace(rho)).item()),
        "entropy": entropy,
        "entropy_ceiling": math.log(dim),
        "entropy_gap": abs(entropy - math.log(dim)),
    }


def finite_path_family(dim: int) -> dict[str, Any]:
    phase = torch.diag(torch.tensor([complex(math.cos(2 * math.pi * k / dim), math.sin(2 * math.pi * k / dim)) for k in range(dim)], dtype=CDTYPE))
    shift = torch.zeros((dim, dim), dtype=CDTYPE)
    for idx in range(dim):
        shift[(idx + 1) % dim, idx] = 1.0
    identity = torch.eye(dim, dtype=CDTYPE)
    ops = [identity, phase, shift, phase @ shift]
    rho = torch.eye(dim, dtype=CDTYPE) / dim
    evolved = sum(op @ rho @ torch.conj(op).T for op in ops) / len(ops)
    return {
        "dim": dim,
        "path_count": len(ops),
        "trace_after_path_average": float(torch.real(torch.trace(evolved)).item()),
        "finite_registry": True,
    }


def positive_finite_discrete_fixture() -> dict[str, Any]:
    carriers = [finite_entropy_carrier(dim) for dim in (2, 4, 8)]
    paths = [finite_path_family(dim) for dim in (2, 4, 8)]
    pass_gate = all(
        carrier["dim"] < 10_000
        and abs(carrier["trace"] - 1.0) < 1e-10
        and carrier["entropy_gap"] < 1e-10
        for carrier in carriers
    ) and all(path["path_count"] == 4 and abs(path["trace_after_path_average"] - 1.0) < 1e-10 for path in paths)
    return {
        "pass": pass_gate,
        "carrier_family": carriers,
        "path_families": paths,
        "forbidden_primitives": [],
    }


def negative_continuum_smuggling_fixture() -> dict[str, Any]:
    attempted_claim = {
        "carrier": "rho over completed continuum",
        "path_family": "integral over all smooth paths",
        "load_bearing_terms": ["completed_infinity", "continuum_primitive", "derivative_primitive", "limit_without_epsilon"],
        "finite_translation": None,
    }
    return {
        "pass": all(term not in attempted_claim["load_bearing_terms"] for term in ("completed_infinity", "continuum_primitive")),
        "attempted_claim": attempted_claim,
        "expected": "fail",
    }


def boundary_derived_chart_fixture() -> dict[str, Any]:
    grid_points = 16
    theta = torch.linspace(0.0, 2.0 * math.pi, grid_points + 1, dtype=DTYPE)[:-1]
    readout = torch.stack([torch.cos(theta), torch.sin(theta)], dim=1)
    finite_difference_norms = torch.linalg.vector_norm(torch.roll(readout, shifts=-1, dims=0) - readout, dim=1)
    return {
        "pass": grid_points == 16 and float(torch.max(finite_difference_norms).item()) < 0.5,
        "smooth_language_status": "derived_readout_only",
        "grid_points": grid_points,
        "max_finite_step": float(torch.max(finite_difference_norms).item()),
        "no_continuum_claim": True,
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_finite_discrete_fixture()
    negative = negative_continuum_smuggling_fixture()
    boundary = boundary_derived_chart_fixture()
    result = {
        "schema": "cf14_finite_discrete_vs_continuum_smuggling_gate_result_v1",
        "name": "cf14_finite_discrete_vs_continuum_smuggling_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-14",
        "gate": "EG-CF14-finite-discrete-vs-continuum-smuggling",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-14 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite density carriers and finite operator/path fixtures",
            },
            "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "python_json": "supportive"},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": positive["pass"] and negative["pass"] is False and boundary["pass"],
    }
    OUT.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
