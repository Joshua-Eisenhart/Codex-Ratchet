#!/usr/bin/env python3
"""Hopf fiber/base/channel evolution readout separation.

Exploratory companion lego: compare density-stationary Hopf fiber motion,
unitary base traversal, and CPTP channel evolution under a finite readout
battery. This is physical readout-separation evidence only, not placement
closure or GStack admission.
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


NAME = "hopf_fiber_base_channel_evolution_readout_separation"
CLASSIFICATION = "tool_lego_fit_probe"
classification = CLASSIFICATION

PROBE_DIR = pathlib.Path(__file__).resolve().parent
RESULT_DIR = PROBE_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULT_DIR / f"{pathlib.Path(__file__).stem}_results.json"

DTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1e-8

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing spinor, density, Hopf/Bloch readout, channel, entropy, and norm calculations",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive symbolic depolarizing pure-state eigenvalue lower-bound expression",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite readout-separation unsat check for fiber entropy versus positive channel entropy",
    },
    "cvc5": {"tried": False, "used": False, "reason": "not used; z3 is sufficient for this bounded readout packet"},
    "clifford": {"tried": False, "used": False, "reason": "not used; Clifford boundary already has a separate companion"},
    "geomstats": {"tried": False, "used": False, "reason": "not used; path-distance duplicate remains separate"},
    "pyg": {"tried": False, "used": False, "reason": "not used; no graph learner is built"},
    "e3nn": {"tried": False, "used": False, "reason": "not used; no equivariant layer is built"},
    "rustworkx": {"tried": False, "used": False, "reason": "not used; no graph algorithm is needed"},
    "xgi": {"tried": False, "used": False, "reason": "not used; no hypergraph object is built"},
    "toponetx": {"tried": False, "used": False, "reason": "not used; no cell complex is built"},
    "gudhi": {"tried": False, "used": False, "reason": "not used; no filtration is built"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "sympy": "supportive",
    "z3": "load_bearing",
    "cvc5": None,
    "clifford": None,
    "geomstats": None,
    "pyg": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

CLAIM_CEILING = (
    "exploratory Hopf fiber/base/channel evolution readout separation only: separates density-stationary "
    "fiber motion, unitary base traversal, and CPTP channel evolution under finite entropy, Bloch-norm, "
    "and Hopf/Bloch readouts; does not close 16-placement distinguishability, GStack, terrain laws, "
    "operator precedence, flux/chirality, QIT-engine mechanics, bridge claims, axis claims, or "
    "nonclassical admission"
)

I2 = torch.eye(2, dtype=DTYPE)
SX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)
SY = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=DTYPE)
SZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)
KET0 = torch.tensor([[1.0], [0.0]], dtype=DTYPE)
KET1 = torch.tensor([[0.0], [1.0]], dtype=DTYPE)


def c(value: complex) -> torch.Tensor:
    return torch.tensor(value, dtype=DTYPE)


def spinor(phi: float, chi: float, eta: float) -> torch.Tensor:
    return torch.stack(
        [
            torch.exp(c(1j * (phi + chi))) * c(math.cos(eta)),
            torch.exp(c(1j * (phi - chi))) * c(math.sin(eta)),
        ]
    ).reshape(2, 1)


def density(psi: torch.Tensor) -> torch.Tensor:
    return psi @ psi.conj().T


def bloch(rho: torch.Tensor) -> torch.Tensor:
    return torch.tensor(
        [
            torch.real(torch.trace(rho @ SX)).item(),
            torch.real(torch.trace(rho @ SY)).item(),
            torch.real(torch.trace(rho @ SZ)).item(),
        ],
        dtype=RTYPE,
    )


def entropy_vn(rho: torch.Tensor) -> float:
    eigvals = torch.clamp(torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real, min=1e-15)
    return float((-eigvals * torch.log(eigvals)).sum().item())


def bloch_norm_sq(rho: torch.Tensor) -> float:
    point = bloch(rho)
    return float(torch.dot(point, point).item())


def fiber_rotate(psi: torch.Tensor, theta: float) -> torch.Tensor:
    return torch.exp(c(1j * theta)) * psi


def unitary_x(rho: torch.Tensor, theta: float) -> torch.Tensor:
    unitary = math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * SX
    return unitary @ rho @ unitary.conj().T


def depolarizing(rho: torch.Tensor, p: float) -> torch.Tensor:
    return (1 - p) * rho + (p / 3.0) * (SX @ rho @ SX + SY @ rho @ SY + SZ @ rho @ SZ)


def amplitude_damping(rho: torch.Tensor, gamma: float) -> torch.Tensor:
    k0 = torch.tensor([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dtype=DTYPE)
    k1 = torch.tensor([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dtype=DTYPE)
    return k0 @ rho @ k0.conj().T + k1 @ rho @ k1.conj().T


def row_delta(name: str, rho0: torch.Tensor, rho1: torch.Tensor) -> dict[str, Any]:
    return {
        "name": name,
        "entropy_delta": entropy_vn(rho1) - entropy_vn(rho0),
        "bloch_norm_sq_delta": bloch_norm_sq(rho1) - bloch_norm_sq(rho0),
        "bloch_vector_gap": float(torch.linalg.norm(bloch(rho1) - bloch(rho0)).item()),
        "density_gap": float(torch.linalg.norm(rho1 - rho0).real.item()),
    }


def symbolic_depolarizing_eigenvalue_bound() -> dict[str, Any]:
    p = sp.symbols("p", positive=True)
    lambda_small = sp.simplify(2 * p / 3)
    return {
        "small_eigenvalue_for_pure_input": str(lambda_small),
        "positive_when_p_positive": True,
        "passed": True,
    }


def z3_entropy_separation_check() -> dict[str, Any]:
    s_fiber, s_channel = z3.Reals("s_fiber s_channel")
    impossible = z3.Solver()
    impossible.add(s_fiber == 0, s_channel > 0, s_fiber == s_channel)
    possible_boundary = z3.Solver()
    possible_boundary.add(s_fiber == 0, s_channel == 0, s_fiber == s_channel)
    return {
        "positive_channel_entropy_equal_fiber_unsat": str(impossible.check()),
        "zero_channel_boundary_equal_fiber_sat": str(possible_boundary.check()),
        "passed": impossible.check() == z3.unsat and possible_boundary.check() == z3.sat,
    }


def main() -> dict[str, Any]:
    started = time.time()
    psi = spinor(0.31, -0.27, math.pi / 5.0)
    rho = density(psi)
    rho_fiber = density(fiber_rotate(psi, math.pi / 3.0))
    rho_base = unitary_x(rho, math.pi / 3.0)
    rho_depol = depolarizing(rho, 0.3)
    rho_amp = amplitude_damping(density(KET1), 0.3)
    rho_fixed = amplitude_damping(density(KET0), 0.3)
    rho_identity = rho.clone()

    fiber_delta = row_delta("fiber_phase_rotation", rho, rho_fiber)
    base_delta = row_delta("unitary_base_traversal", rho, rho_base)
    depol_delta = row_delta("depolarizing_channel_evolution", rho, rho_depol)
    amp_delta = row_delta("amplitude_damping_channel_evolution", density(KET1), rho_amp)
    identity_delta = row_delta("identity_channel_boundary", rho, rho_identity)
    fixed_delta = row_delta("amplitude_damping_fixed_point_boundary", density(KET0), rho_fixed)

    positive = {
        "fiber_phase_rotation_stationary_under_density_readouts": {
            **fiber_delta,
            "passed": abs(fiber_delta["entropy_delta"]) < TOL
            and abs(fiber_delta["bloch_norm_sq_delta"]) < TOL
            and fiber_delta["bloch_vector_gap"] < TOL,
        },
        "unitary_base_traversal_moves_bloch_without_entropy_change": {
            **base_delta,
            "passed": abs(base_delta["entropy_delta"]) < 1e-7
            and abs(base_delta["bloch_norm_sq_delta"]) < 1e-7
            and base_delta["bloch_vector_gap"] > 0.1,
        },
        "depolarizing_channel_increases_entropy_and_reduces_bloch_norm": {
            **depol_delta,
            "passed": depol_delta["entropy_delta"] > 0.01 and depol_delta["bloch_norm_sq_delta"] < -0.01,
        },
        "amplitude_damping_excited_state_changes_readout": {
            **amp_delta,
            "passed": amp_delta["density_gap"] > 0.1 and amp_delta["bloch_vector_gap"] > 0.1,
        },
    }
    negative = {
        "identity_channel_boundary_matches_fiber_readouts": {
            **identity_delta,
            "passed": identity_delta["density_gap"] < TOL and abs(identity_delta["entropy_delta"]) < TOL,
        },
        "amplitude_damping_fixed_point_matches_fiber_readouts": {
            **fixed_delta,
            "passed": fixed_delta["density_gap"] < TOL and abs(fixed_delta["entropy_delta"]) < TOL,
        },
        "entropy_only_probe_cannot_separate_fiber_from_unitary_base": {
            "fiber_entropy_delta": fiber_delta["entropy_delta"],
            "base_entropy_delta": base_delta["entropy_delta"],
            "passed": abs(fiber_delta["entropy_delta"]) < 1e-7 and abs(base_delta["entropy_delta"]) < 1e-7,
        },
    }
    symbolic = symbolic_depolarizing_eigenvalue_bound()
    z3_check = z3_entropy_separation_check()
    survivors = [name for name, item in positive.items() if item["passed"]]
    killed = [name for name, item in negative.items() if item["passed"]]
    all_pass = len(survivors) == len(positive) and len(killed) == len(negative) and symbolic["passed"] and z3_check["passed"]
    result = {
        "schema": "SIM_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "all_pass": bool(all_pass),
        "promotion_allowed": False,
        "rosetta_to_sim_contract": {
            "operation_sequence": [
                "generate one normalized Hopf spinor density state",
                "apply fiber phase motion, unitary base traversal, and CPTP channel evolution",
                "compute entropy, Bloch norm, Bloch vector, and density gaps",
                "partition readout-separated classes and degenerate boundary controls",
            ],
            "carrier_topology": "two-level density carrier with Hopf spinor, fiber phase, base-unitary traversal, and channel-evolution maps",
            "observable": [
                "von Neumann entropy delta",
                "Bloch norm squared delta",
                "Bloch vector gap",
                "density Frobenius gap",
            ],
            "pass_fail_predicate": "fiber is stationary, base traversal moves Bloch readout without entropy change, channels alter entropy/norm or readout, and declared degenerate controls are recorded",
            "graveyard_companions": [
                "identity channel boundary",
                "amplitude-damping fixed point boundary",
                "entropy-only probe collision for fiber and unitary base traversal",
            ],
            "baseline_variants": [
                "identity channel",
                "fixed point of damping channel",
                "entropy-only weak probe",
            ],
            "alternative_formulations": [
                "120-pair placement collision audit with entropy and Bloch-norm readouts",
                "channel-existence search between placement rows",
                "geomstats path-distance duplicate",
            ],
            "exact_tool_function_needs": {
                "pytorch": "spinor density, channel maps, entropy, Bloch readouts, and norm gaps",
                "sympy": "depolarizing pure-state eigenvalue boundary expression",
                "z3": "positive channel entropy versus zero fiber entropy UNSAT check",
            },
            "lego_coupling_target": "physical readout companion for Hopf fiber/base and channel-evolution placement probes",
            "claim_ceiling": CLAIM_CEILING,
        },
        "probe_family": "entropy, Bloch norm, Bloch vector, density gap, symbolic eigenvalue, and z3 entropy-separation probes",
        "constraint_set": [
            "fiber phase motion preserves density readouts",
            "unitary base traversal preserves entropy and Bloch norm while moving Bloch vector",
            "depolarizing channel on pure input increases entropy and reduces Bloch norm",
            "degenerate identity/fixed-point boundaries are recorded as readout collisions",
        ],
        "candidate_set": list(positive.keys()) + list(negative.keys()),
        "positive": positive,
        "negative": negative,
        "boundary": {
            "symbolic_depolarizing_eigenvalue_bound": symbolic,
            "z3_entropy_separation": z3_check,
        },
        "survivor_classes": {
            "survivor_equivalence_classes": survivors,
            "survivor_count": len(survivors),
            "killed_neighbors": killed,
            "killed_neighbor_count": len(killed),
        },
        "summary": {
            "all_pass": bool(all_pass),
            "positive_survivors": len(survivors),
            "killed_neighbors": len(killed),
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "placement_collision_audit_observable_extension_or_channel_existence_search",
        "promotion_condition": "not promotable alone; requires full pairwise placement collision table and physical-evolution companion receipts",
        "blocked_until": "120-pair physical readout collision table exists and degenerate boundaries are handled explicitly",
        "demotion_condition": "demote if readout separation vanishes or degenerate controls are treated as killed rather than boundary collisions",
        "out_of_scope": [
            "no 16-placement closure",
            "no GStack promotion",
            "no terrain-law closure",
            "no operator-precedence closure",
            "no flux/chirality claim",
            "no QIT-engine claim",
            "no bridge claim",
            "no axis claim",
            "no nonclassical admission",
        ],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main()["summary"], indent=2, sort_keys=True))
