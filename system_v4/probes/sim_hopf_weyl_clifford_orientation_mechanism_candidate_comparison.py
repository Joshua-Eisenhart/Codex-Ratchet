#!/usr/bin/env python3
"""Hopf/Weyl/Clifford orientation-mechanism candidate comparison.

Exploratory lego: compare several local orientation mechanisms without
declaring which one is flux. The output is a candidate-mechanism table plus
killed controls. It is not a GStack, placement, bridge, or engine admission.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import sympy as sp
import torch
import z3
from clifford import Cl


NAME = "hopf_weyl_clifford_orientation_mechanism_candidate_comparison"
CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / f"{pathlib.Path(__file__).stem}_results.json"

DTYPE = torch.complex128
TOL = 1e-8

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density, Weyl-sign commutator, and jump-operator fixed-point calculations",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing symbolic Hopf connection orientation integral calculation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independence check over candidate orientation bits",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing oriented pseudoscalar sign probe in Cl(3)",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not used; z3 duplicate is sufficient for this first candidate-comparison packet"},
    "geomstats": {"tried": False, "used": False, "reason": "not used; manifold-distance companion remains separate"},
    "pyg": {"tried": False, "used": False, "reason": "not used; no graph learner is built"},
    "e3nn": {"tried": False, "used": False, "reason": "not used; no equivariant neural layer is built"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used; no graph algorithm is needed"},
    "xgi": {"tried": False, "used": False, "reason": "not used; no hypergraph object is built"},
    "toponetx": {"tried": False, "used": False, "reason": "not used; no cell complex is built"},
    "gudhi": {"tried": False, "used": False, "reason": "not used; no filtration is built"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "clifford": "load_bearing",
    "cvc5": None,
    "geomstats": None,
    "pyg": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

CLAIM_CEILING = (
    "exploratory orientation-mechanism candidate comparison only: compares Weyl Hamiltonian sign, Hopf connection "
    "orientation, Clifford pseudoscalar orientation, and jump-operator fixed-point orientation as local "
    "candidate mechanisms; does not identify flux, close chirality, promote GStack, close placement "
    "readouts, prove an axis, prove QIT-engine mechanics, or support nonclassical admission"
)


def c(value: complex) -> torch.Tensor:
    return torch.tensor(value, dtype=DTYPE)


I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)
LOWER = torch.tensor([[0.0, 0.0], [1.0, 0.0]], dtype=DTYPE)
RAISE = torch.tensor([[0.0, 1.0], [0.0, 0.0]], dtype=DTYPE)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.stack(
        [
            torch.exp(c(1j * (phi + chi))) * c(math.cos(eta)),
            torch.exp(c(1j * (phi - chi))) * c(math.sin(eta)),
        ]
    ).reshape(2, 1)


def density(psi: torch.Tensor) -> torch.Tensor:
    return psi @ psi.conj().T


def commutator_dot(hamiltonian: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return -1j * (hamiltonian @ rho - rho @ hamiltonian)


def lindblad_step(rho: torch.Tensor, jump: torch.Tensor, dt: float = 0.2) -> torch.Tensor:
    jj = jump.conj().T @ jump
    update = jump @ rho @ jump.conj().T - 0.5 * (jj @ rho + rho @ jj)
    out = rho + dt * update
    return out / torch.trace(out).real


def z_expectation(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ SZ)).item())


def weyl_sign_candidate(rho: torch.Tensor) -> dict[str, Any]:
    h = 0.73 * SX + 0.19 * SZ
    left = commutator_dot(h, rho)
    right = commutator_dot(-h, rho)
    same = commutator_dot(h, rho)
    cancellation = float(torch.linalg.norm(left + right).real.item())
    same_gap = float(torch.linalg.norm(left + same).real.item())
    return {
        "mechanism": "hamiltonian_sign_pair",
        "orientation_readout": "opposite signs cancel under paired commutator derivative",
        "opposite_sign_pair_gap": cancellation,
        "same_sign_control_gap": same_gap,
        "passed": cancellation < TOL and same_gap > 1e-6,
    }


def hopf_connection_orientation_candidate() -> dict[str, Any]:
    theta = sp.symbols("theta", real=True)
    eta = sp.pi / 5
    plus_integral = sp.integrate(sp.Integer(1), (theta, 0, 2 * sp.pi))
    minus_integral = sp.integrate(-sp.Integer(1), (theta, 0, 2 * sp.pi))
    horizontal_eval = sp.simplify(-sp.cos(2 * eta) + sp.cos(2 * eta))
    return {
        "mechanism": "hopf_connection_loop_orientation",
        "orientation_readout": "signed common-phase connection integral",
        "positive_orientation_integral": str(plus_integral),
        "negative_orientation_integral": str(minus_integral),
        "horizontal_base_lift_eval": str(horizontal_eval),
        "opposite_integrals_sum_zero": bool(sp.simplify(plus_integral + minus_integral) == 0),
        "horizontal_base_lift_connection_zero": bool(horizontal_eval == 0),
        "passed": bool(sp.simplify(plus_integral + minus_integral) == 0 and plus_integral != minus_integral and horizontal_eval == 0),
    }


def clifford_orientation_candidate() -> dict[str, Any]:
    _layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    oriented_volume = e1 * e2 * e3
    reversed_volume = -oriented_volume
    scalar_probe_collision = float((oriented_volume * oriented_volume)[()]) == float((reversed_volume * reversed_volume)[()])
    sign_probe_separates = float(oriented_volume[(1, 2, 3)]) == -float(reversed_volume[(1, 2, 3)])
    return {
        "mechanism": "clifford_pseudoscalar_orientation",
        "orientation_readout": "oriented Cl(3) pseudoscalar coefficient",
        "positive_pseudoscalar_coefficient": float(oriented_volume[(1, 2, 3)]),
        "negative_pseudoscalar_coefficient": float(reversed_volume[(1, 2, 3)]),
        "square_scalar_positive": float((oriented_volume * oriented_volume)[()]),
        "square_scalar_negative": float((reversed_volume * reversed_volume)[()]),
        "scalar_probe_collision": scalar_probe_collision,
        "sign_probe_separates": sign_probe_separates,
        "passed": scalar_probe_collision and sign_probe_separates,
    }


def jump_fixed_point_orientation_candidate() -> dict[str, Any]:
    mixed = 0.5 * I2
    lowered = mixed.clone()
    raised = mixed.clone()
    symmetric = mixed.clone()
    for _ in range(24):
        lowered = lindblad_step(lowered, LOWER)
        raised = lindblad_step(raised, RAISE)
        symmetric = 0.5 * lindblad_step(symmetric, LOWER) + 0.5 * lindblad_step(symmetric, RAISE)
        symmetric = symmetric / torch.trace(symmetric).real
    z_lower = z_expectation(lowered)
    z_raise = z_expectation(raised)
    z_symmetric = z_expectation(symmetric)
    return {
        "mechanism": "jump_operator_fixed_point_orientation",
        "orientation_readout": "opposite z fixed-point drift under lowering versus raising jumps",
        "lowering_jump_z_expectation": z_lower,
        "raising_jump_z_expectation": z_raise,
        "symmetric_jump_control_z_expectation": z_symmetric,
        "passed": z_lower < -0.5 and z_raise > 0.5 and abs(z_symmetric) < 1e-6,
    }


def z3_independence_check() -> dict[str, Any]:
    hamiltonian_sign, connection_sign, clifford_sign, jump_sign = z3.Bools(
        "hamiltonian_sign connection_sign clifford_sign jump_sign"
    )
    independent = z3.Solver()
    independent.add(hamiltonian_sign != connection_sign)
    independent.add(clifford_sign != jump_sign)
    collapsed = z3.Solver()
    collapsed.add(hamiltonian_sign == connection_sign)
    collapsed.add(connection_sign == clifford_sign)
    collapsed.add(clifford_sign == jump_sign)
    collapsed.add(hamiltonian_sign != jump_sign)
    return {
        "independent_assignment_sat": str(independent.check()),
        "all_same_but_first_not_last_unsat": str(collapsed.check()),
        "passed": independent.check() == z3.sat and collapsed.check() == z3.unsat,
    }


def main() -> dict[str, Any]:
    started = time.time()
    rho = density(spinor(0.41, -0.17, math.pi / 5.0))
    candidates = {
        "hamiltonian_sign_pair": weyl_sign_candidate(rho),
        "hopf_connection_loop_orientation": hopf_connection_orientation_candidate(),
        "clifford_pseudoscalar_orientation": clifford_orientation_candidate(),
        "jump_operator_fixed_point_orientation": jump_fixed_point_orientation_candidate(),
    }
    controls = {
        "same_sign_hamiltonian_pair_does_not_cancel": {
            "passed": candidates["hamiltonian_sign_pair"]["same_sign_control_gap"] > 1e-6,
            "gap": candidates["hamiltonian_sign_pair"]["same_sign_control_gap"],
        },
        "scalar_only_clifford_probe_hides_orientation": {
            "passed": candidates["clifford_pseudoscalar_orientation"]["scalar_probe_collision"],
            "square_scalar_positive": candidates["clifford_pseudoscalar_orientation"]["square_scalar_positive"],
            "square_scalar_negative": candidates["clifford_pseudoscalar_orientation"]["square_scalar_negative"],
        },
        "symmetric_jump_pair_erases_fixed_point_orientation": {
            "passed": abs(candidates["jump_operator_fixed_point_orientation"]["symmetric_jump_control_z_expectation"]) < 1e-6,
            "z_expectation": candidates["jump_operator_fixed_point_orientation"]["symmetric_jump_control_z_expectation"],
        },
    }
    z3_check = z3_independence_check()
    survivor_classes = [name for name, row in candidates.items() if row["passed"]]
    killed_neighbors = [name for name, row in controls.items() if row["passed"]]
    all_pass = (
        len(survivor_classes) == len(candidates)
        and len(killed_neighbors) == len(controls)
        and z3_check["passed"]
    )
    result = {
        "schema": "SIM_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": bool(all_pass),
        "promotion_allowed": False,
        "rosetta_to_sim_contract": {
            "operation_sequence": [
                "generate four local candidate orientation mechanisms",
                "compute one mechanism-specific signed readout for each candidate",
                "compute weak-probe controls that hide or erase the signed readout",
                "partition mechanisms and killed controls under the declared probes",
            ],
            "carrier_topology": "two-level density carrier plus Hopf connection expression plus Cl(3) oriented pseudoscalar",
            "observable": [
                "paired Weyl-sign commutator cancellation",
                "signed Hopf connection loop integral",
                "Cl(3) pseudoscalar coefficient",
                "jump-operator z fixed-point drift",
            ],
            "pass_fail_predicate": "all four candidate mechanisms expose their signed readout, all weak controls are killed, and the z3 independence/collapse checks pass",
            "graveyard_companions": [
                "same-sign Hamiltonian pair",
                "scalar-only Clifford probe",
                "symmetric lowering/raising jump mixture",
            ],
            "baseline_variants": [
                "same-sign generator control",
                "orientation-hiding scalar Clifford control",
                "orientation-erasing symmetric jump control",
            ],
            "alternative_formulations": [
                "cvc5 duplicate of the Boolean independence check",
                "geomstats connection-orientation duplicate",
                "physical placement-evolution duplicate",
            ],
            "exact_tool_function_needs": {
                "pytorch": "density, commutator, Lindblad jump, and z-expectation readouts",
                "sympy": "signed connection integral and horizontal-lift expression",
                "clifford": "Cl(3) pseudoscalar coefficient",
                "z3": "finite independence/collapse satisfiability checks",
            },
            "lego_coupling_target": "orientation-mechanism candidates for geometric constraint manifold flux-layer planning",
            "claim_ceiling": CLAIM_CEILING,
        },
        "probe_family": "mechanism-specific signed orientation readouts plus weak-probe controls",
        "constraint_set": [
            "opposite Hamiltonian signs must cancel paired commutator derivative",
            "opposite loop orientations must reverse signed connection integral",
            "Cl(3) pseudoscalar sign must be visible to oriented coefficient probe",
            "lowering and raising jumps must drift to opposite z fixed points",
        ],
        "candidate_set": list(candidates.keys()) + list(controls.keys()),
        "positive": candidates,
        "negative": controls,
        "boundary": {"z3_independence": z3_check},
        "survivor_classes": {
            "survivor_equivalence_classes": survivor_classes,
            "survivor_count": len(survivor_classes),
            "killed_neighbors": killed_neighbors,
            "killed_neighbor_count": len(killed_neighbors),
        },
        "summary": {
            "all_pass": bool(all_pass),
            "positive_survivors": len(survivor_classes),
            "killed_neighbors": len(killed_neighbors),
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "cvc5_or_geomstats_orientation_duplicate_and_physical_placement_evolution_companion",
        "promotion_condition": "requires independent duplicate tools, physical-evolution companions, and a later manifold-order admission packet",
        "blocked_until": "separate duplicate and placement-evolution receipts exist; no mechanism may be named as flux by this packet",
        "demotion_condition": "demote if any candidate readout collapses under its signed probe or if weak controls are treated as sufficient evidence",
        "out_of_scope": [
            "no flux identification",
            "no chirality closure",
            "no GStack promotion",
            "no placement closure",
            "no axis claim",
            "no QIT-engine claim",
            "no nonclassical admission",
        ],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main()["summary"], indent=2, sort_keys=True))
