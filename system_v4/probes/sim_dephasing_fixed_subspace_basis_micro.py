#!/usr/bin/env python3
"""Micro probe: dephasing generators have basis-dependent fixed subspaces."""

import json
import os

import numpy as np

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "torch complex matrices compute Lindblad residual norms for fixed-subspace predicates",
    },
    "pyg": {"tried": False, "used": False, "reason": "no graph object is needed"},
    "z3": {"tried": False, "used": False, "reason": "numeric residual predicate is the declared probe"},
    "cvc5": {"tried": False, "used": False, "reason": "numeric residual predicate is the declared probe"},
    "sympy": {"tried": False, "used": False, "reason": "no symbolic simplification is needed"},
    "clifford": {"tried": False, "used": False, "reason": "no Clifford algebra claim is made"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold metric claim is made"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariance claim is made"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph object is needed"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph object is needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex object is needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence object is needed"},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"

import torch

DTYPE = torch.complex128
EPS = 1e-10


def ket(values):
    v = torch.tensor(values, dtype=DTYPE).reshape(2, 1)
    return v / torch.linalg.norm(v)


K0 = ket([1.0, 0.0])
K1 = ket([0.0, 1.0])
KP = ket([1.0, 1.0])
KM = ket([1.0, -1.0])


def projector(v):
    return v @ v.conj().T


P0, P1, PP, PM = map(projector, (K0, K1, KP, KM))
I2 = torch.eye(2, dtype=DTYPE)


def density_from_probs(p0, p1, basis):
    a, b = basis
    return p0 * projector(a) + p1 * projector(b)


def lindblad_dephasing_residual(rho, projectors):
    residual = torch.zeros((2, 2), dtype=DTYPE)
    for p in projectors:
        residual = residual + p @ rho @ p - 0.5 * (p @ rho + rho @ p)
    return residual


def fro_norm(mat):
    return float(torch.linalg.norm(mat).real)


def matrix_distance(a, b):
    return fro_norm(a - b)


def rotated_basis(theta):
    c = torch.cos(torch.tensor(theta, dtype=torch.float64))
    s = torch.sin(torch.tensor(theta, dtype=torch.float64))
    r0 = c * K0 + s * K1
    r1 = -s * K0 + c * K1
    return r0, r1


def identity_residual(_rho):
    return torch.zeros((2, 2), dtype=DTYPE)


def run_positive_tests():
    z_fixed = density_from_probs(0.72, 0.28, (K0, K1))
    x_fixed = density_from_probs(0.72, 0.28, (KP, KM))
    return {
        "z_basis_diagonal_state_survives_z_dephasing": {
            "pass": fro_norm(lindblad_dephasing_residual(z_fixed, (P0, P1))) < EPS,
            "residual_norm": fro_norm(lindblad_dephasing_residual(z_fixed, (P0, P1))),
            "criterion": "fixed-state residual below epsilon for matching basis",
        },
        "x_basis_diagonal_state_survives_x_dephasing": {
            "pass": fro_norm(lindblad_dephasing_residual(x_fixed, (PP, PM))) < EPS,
            "residual_norm": fro_norm(lindblad_dephasing_residual(x_fixed, (PP, PM))),
            "criterion": "fixed-state residual below epsilon for matching basis",
        },
    }


def run_negative_tests():
    z_fixed = density_from_probs(0.72, 0.28, (K0, K1))
    x_fixed = density_from_probs(0.72, 0.28, (KP, KM))
    wrong_residual = fro_norm(lindblad_dephasing_residual(x_fixed, (P0, P1)))
    set_separation = matrix_distance(z_fixed, x_fixed)
    return {
        "x_basis_fixed_state_excluded_by_z_dephasing_fixed_subspace": {
            "pass": wrong_residual > 0.1,
            "residual_norm": wrong_residual,
            "criterion": "state fixed in a different basis has nonzero residual",
        },
        "fixed_subspace_representatives_are_distinct": {
            "pass": set_separation > 0.4,
            "frobenius_distance": set_separation,
            "criterion": "matching-basis fixed states are not the same density matrix",
        },
    }


def run_boundary_tests():
    maximally_mixed = 0.5 * I2
    theta_small = 0.03
    rb = rotated_basis(theta_small)
    rotated_projectors = tuple(projector(v) for v in rb)
    z_fixed = density_from_probs(0.72, 0.28, (K0, K1))
    identity_gate_residual = fro_norm(identity_residual(z_fixed))
    rotated_residual = fro_norm(lindblad_dephasing_residual(z_fixed, rotated_projectors))
    common_residual_z = fro_norm(lindblad_dephasing_residual(maximally_mixed, (P0, P1)))
    common_residual_x = fro_norm(lindblad_dephasing_residual(maximally_mixed, (PP, PM)))
    return {
        "maximally_mixed_state_is_common_boundary": {
            "pass": common_residual_z < EPS and common_residual_x < EPS,
            "z_residual_norm": common_residual_z,
            "x_residual_norm": common_residual_x,
            "criterion": "basis probe loses resolution on the scalar density matrix",
        },
        "identity_channel_graveyard_is_vacuous": {
            "pass": identity_gate_residual < EPS,
            "identity_residual_norm": identity_gate_residual,
            "promotion_allowed": False,
            "criterion": "identity generator fixes every state and cannot support the subspace claim",
        },
        "nearby_rotated_basis_changes_residual": {
            "pass": rotated_residual > EPS,
            "rotated_residual_norm": rotated_residual,
            "criterion": "small basis rotation produces measurable residual for a non-scalar fixed state",
        },
    }


def all_sections_pass(results):
    return all(
        item.get("pass", False)
        for section in ("positive", "negative", "boundary")
        for item in results[section].values()
    )


if __name__ == "__main__":
    results = {
        "name": "dephasing_fixed_subspace_basis_micro",
        "probe_family": "finite_lindblad_residual_norm_probe",
        "constraint_set": "basis_dependent_dephasing_fixed_subspace_constraint",
        "operation_sequence": [
            "construct two one-qubit density matrices diagonal in distinct orthonormal bases",
            "apply dephasing Lindblad residual for each declared basis",
            "compare residual norms and fixed-state representative separation",
            "run identity-generator and rotated-basis graveyards",
        ],
        "carrier_topology": "single finite two-dimensional complex Hilbert carrier; no Hopf, bundle, or chirality claim",
        "observable": "Frobenius norm of Lindblad residual plus Frobenius distance between fixed-state representatives",
        "pass_fail_predicate": "matching-basis residuals < EPS; wrong-basis residual and representative separation exceed thresholds; graveyards expose vacuity or basis sensitivity",
        "graveyards": [
            "identity generator fixes all states and is marked promotion_allowed false",
            "nearby rotated basis changes the residual of a non-scalar fixed state",
            "maximally mixed state is a common boundary where basis distinction is intentionally lost",
        ],
        "baselines": [
            "numpy-only dephasing baseline remains classical and does not carry this receipt",
            "identity-generator graveyard is the vacuous fixed-space baseline",
        ],
        "alternative_formulations": [
            "Kraus dephasing channel fixed points",
            "commutant algebra of projectors",
            "superoperator null-space computation",
        ],
        "tool_function_needs": {
            "pytorch": ["torch complex matrix multiplication", "torch.linalg.norm"],
        },
        "lego_coupling_target": "lindbladian_evolution; channel_cptp_map; dephasing fixed-subspace support",
        "claim_ceiling": "single-carrier dephasing fixed-subspace micro evidence only; no engine, axis, bridge, GStack, or nonclassical claim",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
        "surviving_alternatives": [
            "Kraus fixed-point proof remains admissible as a separate formulation",
            "symbolic commutant proof remains admissible as a separate formulation",
        ],
        "next_lego_target": "lindbladian_evolution",
        "promotion_condition": "requires queue/admission ledger reconciliation before reuse by later coupling sims",
        "blocked_until": "exact source/result/admission receipts and matrix loopback are reconciled",
        "demotion_condition": "demote if residual thresholds are tuned to hide basis dependence or if identity graveyard is treated as positive evidence",
        "out_of_scope": [
            "no engine mechanics claim",
            "no axis or direction claim",
            "no Hopf, Weyl, flux, GStack, bridge, emergence, or nonclassical claim",
        ],
        "criteria_checked": [
            "C1 matching-basis dephasing residual is zero within EPS",
            "C2 wrong-basis residual is nonzero for a non-scalar fixed state",
            "C3 fixed-state representatives are distinct density matrices",
            "C4 scalar density matrix is a declared boundary case",
            "C5 identity generator is a vacuous graveyard",
            "C6 small basis rotation is observable by the residual probe",
        ],
    }
    results["all_pass"] = all_sections_pass(results)
    results["summary"] = {
        "total_tests": sum(len(results[s]) for s in ("positive", "negative", "boundary")),
        "passed": sum(
            1
            for s in ("positive", "negative", "boundary")
            for item in results[s].values()
            if item.get("pass")
        ),
        "failed": sum(
            1
            for s in ("positive", "negative", "boundary")
            for item in results[s].values()
            if not item.get("pass")
        ),
        "all_pass": results["all_pass"],
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "dephasing_fixed_subspace_basis_micro_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"PASS={results['all_pass']} -> {out_path}")
