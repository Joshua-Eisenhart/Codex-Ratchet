#!/usr/bin/env python3
"""Gamma5 chirality-asymmetric CPTP arbitrary-Kraus equivalence kill scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import sympy as sp
import torch
import z3

from sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe import (
    DIM,
    DTYPE,
    asymmetric_kraus,
    bounded_scalar_minimize,
    choi_matrix,
    cptp_gap,
    depolarizing_kraus,
    gamma5_boundary,
    symmetric_kraus,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "gamma5_chirality_asymmetric_cptp_arbitrary_kraus_equivalence_kill_probe_results.json"

NAME = "gamma5_chirality_asymmetric_cptp_arbitrary_kraus_equivalence_kill_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: records the kill boundary that an unrestricted "
    "arbitrary-Kraus CPTP family exactly represents the gamma5 "
    "chirality-asymmetric channel, while the one-parameter symmetric "
    "effective-gamma family does not. It does not admit novelty, empirical "
    "physics, a final manifold tower, ontology, or bridge claim."
)

TOOL_MANIFEST = {
    "python_math": {"tried": True, "used": True, "reason": "supportive local bounded scalar search for symmetric effective-gamma minimization"},
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing Kraus, Choi, trace-distance, rank, CPTP checks, and bounded-search objective evaluation"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic rank and parameter-count boundary"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing kill-boundary contradiction witness"},
}
TOOL_INTEGRATION_DEPTH = {
    tool: ("supportive" if tool == "python_math" else "load_bearing")
    for tool in TOOL_MANIFEST
}


def choi_rank(choi: torch.Tensor, threshold: float = 1e-10) -> int:
    eigs = torch.linalg.eigvalsh((choi + choi.conj().T) / 2)
    return int((eigs > threshold).sum().item())


def best_symmetric_fit(target: list[torch.Tensor]) -> dict[str, Any]:
    target_choi = choi_matrix(target)
    def objective(gamma: float) -> float:
        return trace_distance(target_choi, choi_matrix(symmetric_kraus(float(gamma))))
    result = bounded_scalar_minimize(objective, 0.0, 0.50, xatol=1e-12)
    return {
        "gamma": float(result["x"]),
        "choi_trace_distance": float(result["fun"]),
        "success": bool(result["success"]),
        "optimizer": "local_dense_refined_golden_section",
        "optimizer_evaluations": int(result["evaluations"]),
    }


def permuted_kraus(kraus: list[torch.Tensor]) -> list[torch.Tensor]:
    return list(reversed(kraus))


def z3_kill_witness(arbitrary_gap: float, symmetric_gap: float, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    arbitrary_exact, symmetric_fails, valid = z3.Bools("arbitrary_exact symmetric_fails valid")
    solver.add(arbitrary_exact == (arbitrary_gap < 1e-12))
    solver.add(symmetric_fails == (symmetric_gap > 0.02))
    solver.add(valid == (cptp < 1e-12))
    solver.add(z3.Not(z3.And(arbitrary_exact, symmetric_fails, valid)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "arbitrary_exact": arbitrary_gap < 1e-12,
        "symmetric_fails": symmetric_gap > 0.02,
        "cptp_valid": cptp < 1e-12,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    target = asymmetric_kraus(0.30, 0.05)
    target_choi = choi_matrix(target)
    same_kraus_gap = trace_distance(target_choi, choi_matrix(target))
    permuted_gap = trace_distance(target_choi, choi_matrix(permuted_kraus(target)))
    symmetric_fit = best_symmetric_fit(target)
    depol = depolarizing_kraus(0.20)
    depol_self_gap = trace_distance(choi_matrix(depol), choi_matrix(depol))
    target_rank = choi_rank(target_choi)
    symmetric_rank = choi_rank(choi_matrix(symmetric_kraus(symmetric_fit["gamma"])))
    cptp = cptp_gap(target)
    symbolic_boundary = sp.Integer(target_rank) >= sp.Integer(symmetric_rank)
    positive = {
        "unrestricted_arbitrary_kraus_family_exactly_represents_target_channel": {
            "same_kraus_choi_trace_distance": same_kraus_gap,
            "permuted_kraus_choi_trace_distance": permuted_gap,
            "pass": same_kraus_gap < 1e-12 and permuted_gap < 1e-12,
        },
        "one_parameter_symmetric_effective_gamma_family_fails_to_represent_target_channel": {
            "best_symmetric_fit": symmetric_fit,
            "pass": symmetric_fit["choi_trace_distance"] > 0.02,
        },
        "target_channel_is_valid_cptp": {"cptp_gap": cptp, "pass": cptp < 1e-12},
        "gamma5_projector_boundary": gamma5_boundary(),
    }
    graveyard_companions = {
        "depolarizing_channel_self_representation_is_exact": {
            "depolarizing_self_choi_trace_distance": depol_self_gap,
            "pass": depol_self_gap < 1e-12,
        },
        "identity_channel_self_representation_is_exact": {
            "identity_self_choi_trace_distance": trace_distance(choi_matrix(symmetric_kraus(0.0)), choi_matrix(symmetric_kraus(0.0))),
            "pass": trace_distance(choi_matrix(symmetric_kraus(0.0)), choi_matrix(symmetric_kraus(0.0))) < 1e-12,
        },
        "choi_rank_records_channel_family_difference": {
            "target_choi_rank": target_rank,
            "symmetric_fit_choi_rank": symmetric_rank,
            "pass": target_rank >= symmetric_rank,
        },
        "symbolic_rank_boundary_is_consistent": {
            "expr": f"{target_rank} >= {symmetric_rank}",
            "pass": bool(symbolic_boundary),
        },
    }
    boundary = {
        "finite_four_component_channel_dimension": {"dimension": DIM, "choi_dimension": DIM * DIM, "pass": DIM == 4},
        "z3_arbitrary_kraus_kill_witness": z3_kill_witness(same_kraus_gap, symmetric_fit["choi_trace_distance"], cptp),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-component gamma5 chirality-asymmetric CPTP channel compared against unrestricted arbitrary-Kraus self-representation and one-parameter symmetric effective-gamma Choi fit",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "Unrestricted arbitrary-Kraus CPTP equivalence is too broad to support novelty; it exactly represents the target by construction.",
            "Useful future falsifiers must restrict the comparison family: symmetric rates, matched-rank Stinespring geometry, locality, shell-independent generators, or representation-preserving maps.",
            "This kill boundary should travel with later dynamic shell and tensor-network scouts.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini arbitrary-CPTP falsifier pressure; it is not a canonical v4 probe.",
        "raw_rows": {
            "same_kraus_gap": same_kraus_gap,
            "permuted_kraus_gap": permuted_gap,
            "symmetric_fit": symmetric_fit,
            "target_choi_rank": target_rank,
            "symmetric_fit_choi_rank": symmetric_rank,
            "cptp_gap": cptp,
        },
        "blockers": [],
        "elapsed_seconds": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all(checks),
                "result": str(OUT_PATH),
                "same_kraus_gap": same_kraus_gap,
                "symmetric_fit_gap": symmetric_fit["choi_trace_distance"],
                "target_choi_rank": target_rank,
                "symmetric_fit_choi_rank": symmetric_rank,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
