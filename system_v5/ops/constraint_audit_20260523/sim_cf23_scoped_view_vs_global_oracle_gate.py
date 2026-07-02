#!/usr/bin/env python3
"""CF-23 scoped-view vs global-oracle gate."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch


HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / "cf23_scoped_view_vs_global_oracle_gate_results.json"

CDTYPE = torch.complex128
EPS = 1e-10


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
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def hermitize(rho: torch.Tensor) -> torch.Tensor:
    return (rho + torch.conj(rho).T) / 2


def density(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def bell(sign: int) -> torch.Tensor:
    psi = torch.zeros(4, dtype=CDTYPE)
    psi[0] = 1.0
    psi[3] = float(sign)
    psi = psi / torch.linalg.vector_norm(psi)
    return density(psi)


def partial_trace_a(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abcb->ac", rho_ab.reshape(2, 2, 2, 2))


def partial_trace_b(rho_ab: torch.Tensor) -> torch.Tensor:
    return torch.einsum("abad->bd", rho_ab.reshape(2, 2, 2, 2))


def trace_distance(a: torch.Tensor, b: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(hermitize(a - b)).real
    return float(0.5 * torch.sum(torch.abs(vals)).item())


def positive_scoped_view_gate() -> dict[str, Any]:
    plus = bell(+1)
    minus = bell(-1)
    local_gap_a = trace_distance(partial_trace_a(plus), partial_trace_a(minus))
    local_gap_b = trace_distance(partial_trace_b(plus), partial_trace_b(minus))
    global_gap = trace_distance(plus, minus)
    return {
        "pass": local_gap_a < EPS and local_gap_b < EPS and global_gap > 0.9,
        "scoped_view_declared": ["A", "B"],
        "partial_trace_or_projection": True,
        "local_gap_a": local_gap_a,
        "local_gap_b": local_gap_b,
        "global_oracle_gap": global_gap,
    }


def global_oracle_negative_gate() -> dict[str, Any]:
    plus = bell(+1)
    minus = bell(-1)
    global_gap = trace_distance(plus, minus)
    scoped_a_plus = partial_trace_a(plus)
    scoped_a_minus = partial_trace_a(minus)
    scoped_b_plus = partial_trace_b(plus)
    scoped_b_minus = partial_trace_b(minus)
    local_a_gap = trace_distance(scoped_a_plus, scoped_a_minus)
    local_b_gap = trace_distance(scoped_b_plus, scoped_b_minus)
    global_oracle_decision = global_gap > 0.9
    scoped_a_process_decision = local_a_gap > 0.1
    rejected = global_oracle_decision and not scoped_a_process_decision and local_b_gap < EPS
    return {
        "pass": False,
        "expected": "fail",
        "negative_case_type": "executable_rejection",
        "negative_rejected": rejected,
        "attempted_claim": {
            "claim": "global state difference decides the scoped A process",
            "scope_declared": False,
            "global_oracle_load_bearing": True,
        },
        "global_oracle_decision": global_oracle_decision,
        "scoped_a_process_decision": scoped_a_process_decision,
        "global_gap": global_gap,
        "local_a_gap": local_a_gap,
        "local_b_gap": local_b_gap,
    }


def diagnostic_global_boundary_gate() -> dict[str, Any]:
    plus = bell(+1)
    minus = bell(-1)
    global_gap = trace_distance(plus, minus)
    return {
        "pass": global_gap > 0.9,
        "global_summary_declared_diagnostic_only": True,
        "projection_scope": "full_AB_diagnostic",
        "global_gap": global_gap,
        "interpretation": "global readout is allowed as a named diagnostic projection, not as omniscient primitive context",
    }


def main() -> int:
    started = time.time()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    positive = positive_scoped_view_gate()
    negative = global_oracle_negative_gate()
    boundary = diagnostic_global_boundary_gate()
    result = {
        "schema": "cf23_scoped_view_vs_global_oracle_gate_result_v1",
        "name": "cf23_scoped_view_vs_global_oracle_gate",
        "classification": "constraint_gate",
        "candidate_fence": "CF-23",
        "gate": "EG-CF23-scoped-view-vs-global-oracle",
        "claim_ceiling": "Candidate gate receipt only. Passing does not promote CF-23 to accepted DC without non-redundancy audit.",
        "uses_numpy": False,
        "TOOL_MANIFEST": {
            "torch": {
                "tried": True,
                "used": True,
                "reason": "load-bearing finite bipartite density states, scoped partial traces, and global-oracle negative control",
            },
            "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "python_json": "supportive"},
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "all_pass": positive["pass"] and negative["pass"] is False and negative["negative_rejected"] and boundary["pass"],
    }
    OUT.write_text(json.dumps(as_jsonable(result), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
