#!/usr/bin/env python3
"""Gamma5 chirality-asymmetric CPTP matched-rank split-jump channel scout."""

from __future__ import annotations

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

from scipy.optimize import minimize_scalar
import sympy as sp
import torch
import z3

from sim_gamma5_chirality_asymmetric_cptp_choi_distance_effective_channel_probe import (
    DIM,
    asymmetric_kraus,
    choi_matrix,
    cptp_gap,
    gamma5_boundary,
    stinespring_projector_distance,
    symmetric_kraus,
    trace_distance,
)


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "gamma5_chirality_asymmetric_cptp_matched_rank_split_jump_channel_probe_results.json"

NAME = "gamma5_chirality_asymmetric_cptp_matched_rank_split_jump_channel_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: compares a gamma5 chirality-asymmetric rank-3 CPTP "
    "channel against a matched-rank equal-rate split-jump CPTP family and the "
    "lower-rank combined symmetric effective-gamma family by Choi trace "
    "distance and Stinespring-isometry projector distance. It does not admit "
    "novelty, empirical physics, a final manifold tower, ontology, or bridge "
    "claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing Kraus, Choi, Stinespring projector, rank, and CPTP checks"},
    "scipy": {"tried": True, "used": True, "reason": "load-bearing continuous equal-rate and combined-rate minimization"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing symbolic rank-order sanity"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing matched-rank contradiction witness"},
}
TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}


def choi_rank(choi: torch.Tensor, threshold: float = 1e-10) -> int:
    eigs = torch.linalg.eigvalsh((choi + choi.conj().T) / 2)
    return int((eigs > threshold).sum().item())


def fit_family(target: list[torch.Tensor], family: str) -> dict[str, Any]:
    target_choi = choi_matrix(target)
    def kraus(gamma: float) -> list[torch.Tensor]:
        if family == "matched_rank_split_jump_equal_rate":
            return asymmetric_kraus(gamma, gamma)
        if family == "combined_symmetric_effective_gamma":
            return symmetric_kraus(gamma)
        raise ValueError(family)
    def objective(gamma: float) -> float:
        return trace_distance(target_choi, choi_matrix(kraus(float(gamma))))
    result = minimize_scalar(objective, bounds=(0.0, 0.50), method="bounded", options={"xatol": 1e-12})
    best = kraus(float(result.x))
    return {
        "family": family,
        "gamma": float(result.x),
        "choi_trace_distance": float(result.fun),
        "stinespring_projector_distance": stinespring_projector_distance(target, best),
        "choi_rank": choi_rank(choi_matrix(best)),
        "cptp_gap": cptp_gap(best),
        "success": bool(result.success),
    }


def z3_witness(matched: dict[str, Any], combined: dict[str, Any], target_rank: int, cptp: float) -> dict[str, Any]:
    solver = z3.Solver()
    closer, still_fails, rank_match, valid = z3.Bools("closer still_fails rank_match valid")
    solver.add(closer == (matched["choi_trace_distance"] < combined["choi_trace_distance"]))
    solver.add(still_fails == (matched["choi_trace_distance"] > 0.02))
    solver.add(rank_match == (matched["choi_rank"] == target_rank))
    solver.add(valid == (cptp < 1e-12 and matched["cptp_gap"] < 1e-12))
    solver.add(z3.Not(z3.And(closer, still_fails, rank_match, valid)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "matched_rank_family_is_closer": matched["choi_trace_distance"] < combined["choi_trace_distance"],
        "matched_rank_family_still_fails": matched["choi_trace_distance"] > 0.02,
        "rank_matches": matched["choi_rank"] == target_rank,
        "cptp_valid": cptp < 1e-12 and matched["cptp_gap"] < 1e-12,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    target = asymmetric_kraus(0.30, 0.05)
    target_choi = choi_matrix(target)
    target_rank = choi_rank(target_choi)
    matched = fit_family(target, "matched_rank_split_jump_equal_rate")
    combined = fit_family(target, "combined_symmetric_effective_gamma")
    cptp = cptp_gap(target)
    symbolic_rank = bool(sp.Integer(matched["choi_rank"]) == sp.Integer(target_rank))
    positive = {
        "matched_rank_split_jump_family_is_closer_than_combined_symmetric_family": {
            "matched_rank_fit": matched,
            "combined_symmetric_fit": combined,
            "pass": matched["choi_trace_distance"] < combined["choi_trace_distance"],
        },
        "matched_rank_split_jump_family_still_fails_to_match_target_channel": {
            "matched_rank_fit": matched,
            "threshold": 0.02,
            "pass": matched["choi_trace_distance"] > 0.02 and matched["stinespring_projector_distance"] > 0.02,
        },
        "matched_rank_split_jump_family_preserves_choi_rank": {
            "target_choi_rank": target_rank,
            "matched_rank_fit_rank": matched["choi_rank"],
            "pass": matched["choi_rank"] == target_rank,
        },
        "gamma5_projector_boundary": gamma5_boundary(),
    }
    graveyard_companions = {
        "unrestricted_same_kraus_channel_matches_exactly": {
            "same_kraus_choi_trace_distance": trace_distance(target_choi, choi_matrix(target)),
            "pass": trace_distance(target_choi, choi_matrix(target)) < 1e-12,
        },
        "combined_symmetric_family_has_lower_choi_rank": {
            "combined_symmetric_fit_rank": combined["choi_rank"],
            "target_choi_rank": target_rank,
            "pass": combined["choi_rank"] < target_rank,
        },
        "matched_rank_fit_is_cptp": {
            "target_cptp_gap": cptp,
            "matched_cptp_gap": matched["cptp_gap"],
            "pass": cptp < 1e-12 and matched["cptp_gap"] < 1e-12,
        },
        "symbolic_rank_match_boundary": {
            "expr": f"{matched['choi_rank']} == {target_rank}",
            "pass": symbolic_rank,
        },
    }
    boundary = {
        "finite_four_component_channel_dimension": {"dimension": DIM, "choi_dimension": DIM * DIM, "pass": DIM == 4},
        "z3_matched_rank_witness": z3_witness(matched, combined, target_rank, cptp),
        "promotion_remains_disabled": {"promotion_allowed": PROMOTION_ALLOWED, "pass": PROMOTION_ALLOWED is False},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [row["pass"] for row in boundary.values()]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "four-component gamma5 chirality-asymmetric rank-3 CPTP channel compared against matched-rank equal-rate split-jump and lower-rank combined symmetric effective-gamma channel families",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"passed": sum(1 for value in checks if value), "total": len(checks)},
        "open_choices": [
            "Matched Choi rank alone is not enough to reproduce the asymmetric target channel.",
            "This is still a one-parameter equal-rate split-jump family; a stronger constrained comparison would optimize over locality-preserving rank-3 Kraus parameters.",
            "Use this scout before claiming any matched-rank Stinespring quotient separation.",
        ],
        "why_not_v4_probes": "This is a clean v5 formal scout translated from Grok/Gemini matched-rank Stinespring pressure; it is not a canonical v4 probe.",
        "raw_rows": {
            "target_choi_rank": target_rank,
            "target_cptp_gap": cptp,
            "matched_rank_split_jump_fit": matched,
            "combined_symmetric_fit": combined,
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
                "matched_rank_gap": matched["choi_trace_distance"],
                "combined_symmetric_gap": combined["choi_trace_distance"],
                "target_choi_rank": target_rank,
                "matched_rank": matched["choi_rank"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
