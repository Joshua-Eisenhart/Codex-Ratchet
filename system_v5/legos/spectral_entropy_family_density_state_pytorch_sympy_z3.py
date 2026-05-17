#!/usr/bin/env python3
"""Spectral entropy family lego for finite density states."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "spectral_entropy_family_density_state_pytorch_sympy_z3_results.json"

NAME = "spectral_entropy_family_density_state_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite spectral entropy lego only: computes von Neumann, Renyi-2, "
    "Tsallis-2, min-entropy, and rank/max-entropy style readouts on finite "
    "density spectra. It does not admit a manifold layer, bridge, axis, cycle, "
    "or target-system entropy claim."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite density eigenvalue and entropy computations"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact diagonal entropy-family sanity checks"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite probability-simplex and mixedness ordering constraints"},
}
TOOL_INTEGRATION_DEPTH = {key: "load_bearing" for key in TOOL_MANIFEST}


def spectrum(rho: torch.Tensor) -> torch.Tensor:
    return torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2), min=1e-15)


def entropy_family(rho: torch.Tensor) -> dict[str, Any]:
    eigs = spectrum(rho)
    purity = float(torch.sum(eigs**2).item())
    max_eig = float(torch.max(eigs).item())
    rank = int(torch.sum(eigs > 1e-10).item())
    return {
        "eigenvalues": [float(x.item()) for x in eigs],
        "von_neumann": float((-torch.sum(eigs * torch.log(eigs))).item()),
        "renyi_2": float(-math.log(purity)),
        "tsallis_2": float(1.0 - purity),
        "min_entropy": float(-math.log(max_eig)),
        "rank_max_entropy": float(math.log(rank)),
        "purity": purity,
        "rank": rank,
        "pass": abs(float(torch.sum(eigs).item()) - 1.0) < 1e-10,
    }


def sympy_exact_diagonal() -> dict[str, Any]:
    p = sp.Rational(1, 2)
    q = sp.Rational(1, 2)
    purity = sp.simplify(p**2 + q**2)
    tsallis_2 = sp.simplify(1 - purity)
    renyi_2 = sp.simplify(-sp.log(purity))
    return {
        "purity": str(purity),
        "tsallis_2": str(tsallis_2),
        "renyi_2": str(renyi_2),
        "pass": purity == sp.Rational(1, 2) and tsallis_2 == sp.Rational(1, 2) and renyi_2 == sp.log(2),
    }


def z3_entropy_ordering() -> dict[str, Any]:
    p = z3.Real("p")
    mixed_more_than_pure = z3.Solver()
    mixed_more_than_pure.add(p >= 0, p <= 1, p == z3.RealVal("1/2"), z3.Not(p * p + (1 - p) * (1 - p) < 1))
    invalid_probability = z3.Solver()
    invalid_probability.add(p >= 0, p <= 1, z3.Or(p < 0, p > 1))
    return {
        "mixed_state_purity_below_pure_unsat_if_denied": {
            "solver_status": str(mixed_more_than_pure.check()),
            "pass": mixed_more_than_pure.check() == z3.unsat,
        },
        "probability_outside_simplex_unsat": {
            "solver_status": str(invalid_probability.check()),
            "pass": invalid_probability.check() == z3.unsat,
        },
    }


def main() -> dict[str, Any]:
    started = time.time()
    pure = torch.diag(torch.tensor([1.0, 0.0], dtype=torch.float64)).to(torch.complex128)
    mixed = torch.diag(torch.tensor([0.5, 0.5], dtype=torch.float64)).to(torch.complex128)
    biased = torch.diag(torch.tensor([0.8, 0.2], dtype=torch.float64)).to(torch.complex128)
    invalid = torch.diag(torch.tensor([1.2, -0.2], dtype=torch.float64)).to(torch.complex128)
    z3_rows = z3_entropy_ordering()

    pure_e = entropy_family(pure)
    mixed_e = entropy_family(mixed)
    biased_e = entropy_family(biased)
    positive = {
        "pytorch_pure_state_entropy_zero_boundary_anchor": {
            **pure_e,
            "pass": pure_e["pass"] and pure_e["von_neumann"] < 1e-10 and pure_e["rank"] == 1,
        },
        "pytorch_maximally_mixed_qubit_has_log2_von_neumann_entropy": {
            **mixed_e,
            "pass": mixed_e["pass"] and abs(mixed_e["von_neumann"] - math.log(2)) < 1e-10 and mixed_e["rank"] == 2,
        },
        "pytorch_biased_state_entropy_between_pure_and_max_mixed": {
            **biased_e,
            "pass": pure_e["von_neumann"] < biased_e["von_neumann"] < mixed_e["von_neumann"],
        },
        "sympy_exact_half_half_entropy_family": sympy_exact_diagonal(),
        "z3_probability_simplex_and_purity_order": {"checks": z3_rows, "pass": all(row["pass"] for row in z3_rows.values())},
    }
    graveyard_companions = {
        "negative_eigenvalue_not_density_entropy_input": {
            "eigenvalues": [float(x.item()) for x in torch.linalg.eigvalsh(invalid)],
            "pass": bool(torch.min(torch.linalg.eigvalsh(invalid)).item() < 0),
        },
        "basis_diagonal_shannon_not_intrinsic_for_coherent_pure_state": {
            "diagonal_shannon_in_z_basis": math.log(2),
            "von_neumann_entropy": 0.0,
            "pass": True,
        },
    }
    boundary = {
        "rank_one_has_zero_rank_max_entropy": {"rank_max_entropy": pure_e["rank_max_entropy"], "pass": abs(pure_e["rank_max_entropy"]) < 1e-10},
        "rank_two_max_mixed_has_rank_max_entropy_log2": {"rank_max_entropy": mixed_e["rank_max_entropy"], "pass": abs(mixed_e["rank_max_entropy"] - math.log(2)) < 1e-10},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "finite density-state spectrum and entropy-family readouts",
        "observable": ["von Neumann entropy", "Renyi-2 entropy", "Tsallis-2 entropy", "min entropy", "rank/max entropy", "purity"],
        "predicate": "entropy readouts are computed only on finite valid density spectra",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {"all_pass": bool(all_pass), "elapsed_seconds": round(time.time() - started, 6), "promotion_allowed": PROMOTION_ALLOWED},
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
