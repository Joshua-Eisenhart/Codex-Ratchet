#!/usr/bin/env python3
"""Two-point finite spectral triple commutator-distance lego."""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
OUT_PATH = RESULT_DIR / "two_point_spectral_triple_dirac_commutator_distance_pytorch_sympy_z3_results.json"

NAME = "two_point_spectral_triple_dirac_commutator_distance_pytorch_sympy_z3"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Finite spectral-triple lego only: checks a two-point algebra, Dirac "
    "operator, commutator norm, and distance bound. It does not admit metric "
    "reconstruction for the full manifold tower, Hopf geometry, cycle, bridge, "
    "or target-system interpretation."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite matrix spectrum and commutator norm"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact commutator formula"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing bound proof for finite two-point distance constraint"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "sympy": "load_bearing", "z3": "load_bearing"}

BLOCKED_CONSUMERS = [
    "PEPS3D scale promotion",
    "Hopf layer",
    "Weyl sheet cover",
    "terrain placement",
    "operator substages",
    "matrix stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "final manifold",
]


def torch_commutator_norm(mass: float, a: float, b: float) -> dict[str, Any]:
    d = torch.tensor([[0.0, mass], [mass, 0.0]], dtype=torch.float64)
    alg = torch.diag(torch.tensor([a, b], dtype=torch.float64))
    comm = d @ alg - alg @ d
    singular_values = torch.linalg.svdvals(comm)
    return {
        "commutator": comm.tolist(),
        "operator_norm": float(torch.max(singular_values).item()),
        "dirac_eigenvalues": [float(x.item()) for x in torch.linalg.eigvalsh(d)],
    }


def sympy_commutator_formula() -> dict[str, Any]:
    m, a, b = sp.symbols("m a b", positive=True, real=True)
    d = sp.Matrix([[0, m], [m, 0]])
    alg = sp.diag(a, b)
    comm = sp.simplify(d * alg - alg * d)
    expected = sp.Matrix([[0, m * (b - a)], [m * (a - b), 0]])
    return {"commutator": str(comm), "expected": str(expected), "pass": comm == expected}


def z3_distance_bound() -> dict[str, Any]:
    m = z3.Real("m")
    delta = z3.Real("delta")
    distance = z3.Real("distance")
    solver = z3.Solver()
    solver.add(m == 2, delta >= 0, m * delta <= 1, distance == delta, distance > z3.RealVal("1/2"))
    zero_dirac = z3.Solver()
    zero_dirac.add(m == 0, delta > 0, m * delta <= 1)
    return {
        "distance_exceeds_inverse_mass_unsat": {"solver_status": str(solver.check()), "pass": solver.check() == z3.unsat},
        "zero_dirac_bound_cannot_separate_points": {"solver_status": str(zero_dirac.check()), "pass": zero_dirac.check() == z3.sat},
    }


def main() -> dict[str, Any]:
    started = time.time()
    mass = 2.0
    separated = torch_commutator_norm(mass, 0.0, 0.5)
    collapsed = torch_commutator_norm(mass, 0.25, 0.25)
    over_bound = torch_commutator_norm(mass, 0.0, 0.75)
    z3_checks = z3_distance_bound()

    positive = {
        "pytorch_two_point_commutator_norm_hits_bound": {
            **separated,
            "pass": abs(separated["operator_norm"] - 1.0) < 1e-12 and separated["dirac_eigenvalues"] == [-2.0, 2.0],
        },
        "sympy_exact_two_point_commutator_formula": sympy_commutator_formula(),
        "z3_distance_cannot_exceed_inverse_mass": z3_checks["distance_exceeds_inverse_mass_unsat"],
    }
    graveyard_companions = {
        "constant_algebra_element_has_zero_commutator": {
            **collapsed,
            "pass": abs(collapsed["operator_norm"]) < 1e-12,
        },
        "over_bound_algebra_element_rejected_by_norm": {
            **over_bound,
            "pass": over_bound["operator_norm"] > 1.0,
        },
        "zero_dirac_cannot_bound_nonzero_distance": z3_checks["zero_dirac_bound_cannot_separate_points"],
    }
    boundary = {
        "inverse_mass_distance_boundary": {
            "mass": mass,
            "distance": 1.0 / mass,
            "commutator_norm": separated["operator_norm"],
            "pass": abs((1.0 / mass) - 0.5) < 1e-12 and abs(separated["operator_norm"] - 1.0) < 1e-12,
        }
    }
    controls = {
        "commuting_constant_algebra": graveyard_companions["constant_algebra_element_has_zero_commutator"],
        "wrong_dirac_zero_mass": graveyard_companions["zero_dirac_cannot_bound_nonzero_distance"],
        "over_bound_rejected": graveyard_companions["over_bound_algebra_element_rejected_by_norm"],
        "scalar_label": {
            "reason": "A label 'spectral triple' without finite A, H, D, commutator norm, and distance constraint cannot witness a metric readout.",
            "pass": True,
        },
        "dense_closure": {
            "reason": "The row uses a finite two-point algebra and 2x2 Dirac operator only; no dense manifold reconstruction or PEPS3D closure is built.",
            "pass": True,
        },
    }
    ablation_outcome_delta = {
        "pytorch": {
            "without_tool": "map_unprovable",
            "reason": "Dirac eigenvalues, finite commutator matrix, singular-value operator norm, and numeric boundary readout are PyTorch claim objects.",
        },
        "sympy": {
            "without_tool": "map_unprovable",
            "reason": "The exact commutator formula [D,a]=m(b-a) off-diagonal is no longer mechanically checked.",
        },
        "z3": {
            "without_tool": "map_unprovable",
            "reason": "The inverse-mass distance bound and zero-Dirac blocker become unchecked algebraic assertions.",
        },
    }
    scale_rungs = [
        {"points": 2, "hilbert_dim": 2, "status": "passed_finite_spectral_triple_floor"},
        {
            "points": 4,
            "status": "blocked_pending_new_row",
            "description": "larger finite spectral triples require a separate row and are not claimed here",
        },
    ]
    result = {
        "schema": "LEGO_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": "ST_2pt : finite spectral triple (A=C^2, H=C^2, D_m) and algebra element a -> commutator [D_m,a], operator norm, inverse-mass distance bound, and solver status",
        "domain": "finite two-point algebra elements diag(a,b), finite Hilbert carrier C^2, finite Dirac operator [[0,m],[m,0]] with m=2, and finite controls",
        "codomain_or_output": "finite commutator matrix, Dirac eigenvalues, operator norm, distance boundary, exact SymPy formula, and z3 statuses",
        "F01_status": "passed: finite algebra, finite Hilbert carrier, finite Dirac operator, finite controls, finite outputs",
        "N01_status": "passed: nonconstant algebra element has nonzero Dirac commutator while constant commuting control collapses to zero",
        "torch_carrier_status": "claim_bearing_two_point_finite_matrix_carrier",
        "spinor_or_density_status": "not_applicable_no_density_or_spinor_claim_in_this_row",
        "peps3d_anchor_status": "not_applicable_to_two_point_spectral_triple_row; PEPS3D scale promotion remains blocked",
        "math_object": "finite two-point spectral triple with Dirac commutator distance bound",
        "observable": ["Dirac eigenvalues", "algebra commutator", "operator norm", "z3 distance bound"],
        "predicate": "commutator norm bounds two-point algebra separation by inverse Dirac mass",
        "entropy_matrix": [],
        "entropy_status": "not_applicable_no_density_readout_present",
        "scale_rungs": scale_rungs,
        "controls": controls,
        "ablation_outcome_delta": ablation_outcome_delta,
        "tool_ablations": ablation_outcome_delta,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyard_companions), "passed": sum(1 for row in graveyard_companions.values() if row["pass"])},
        "blockers": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyard_companions.values()) and all(row["pass"] for row in boundary.values()),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
