#!/usr/bin/env python3
"""Direct local lego: admissibility manifold M(C).

This probe builds a finite admitted set from explicit constraints on small
density matrices and a finite probe family.  It is a row-level admissibility
surface only; it does not promote a GStack, axis model, or full QIT engine.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


classification = "canonical"

CLASSIFICATION_NOTE = (
    "Canonical direct lego for M(C) as the finite subset of candidate states "
    "that pass explicit trace, positivity, and probe-boundedness constraints."
)
LEGO_IDS = ["admissibility_manifold_mc"]
PRIMARY_LEGO_IDS = ["admissibility_manifold_mc"]
TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "constructs the finite candidate family, applies PSD/trace/probe constraints, and measures admitted-set closure",
    }
}
TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}
EPS = 1e-10


def json_safe(value):
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_safe(value.tolist())
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, complex):
        if abs(value.imag) <= EPS:
            return float(value.real)
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def projectors() -> list[np.ndarray]:
    return [
        np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex),
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex),
    ]


def candidates() -> dict[str, np.ndarray]:
    return {
        "rho0": np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex),
        "rho1": np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex),
        "mixed": np.array([[0.5, 0.0], [0.0, 0.5]], dtype=complex),
        "plus": np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex),
        "wrong_trace": np.array([[0.7, 0.0], [0.0, 0.7]], dtype=complex),
        "negative": np.array([[1.1, 0.0], [0.0, -0.1]], dtype=complex),
        "non_hermitian": np.array([[0.5, 1.0], [0.0, 0.5]], dtype=complex),
    }


def check_state(rho: np.ndarray, probes: list[np.ndarray]) -> dict:
    hermitian = bool(np.allclose(rho, rho.conj().T, atol=EPS))
    trace_one = abs(complex(np.trace(rho)).real - 1.0) <= EPS and abs(complex(np.trace(rho)).imag) <= EPS
    eigenvalues = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
    psd = bool(np.all(eigenvalues >= -EPS))
    probabilities = [float(np.real(np.trace(effect @ rho))) for effect in probes]
    probe_bounded = all(-EPS <= p <= 1.0 + EPS for p in probabilities)
    admitted = hermitian and trace_one and psd and probe_bounded
    return {
        "hermitian": hermitian,
        "trace_one": trace_one,
        "eigenvalues": [float(x) for x in eigenvalues],
        "psd": psd,
        "probe_probabilities": probabilities,
        "probe_bounded": probe_bounded,
        "admitted": admitted,
    }


def admitted_set() -> tuple[dict[str, dict], list[str]]:
    probes = projectors()
    checks = {name: check_state(rho, probes) for name, rho in candidates().items()}
    admitted = [name for name, check in checks.items() if check["admitted"]]
    return checks, admitted


def convex_average(lhs: np.ndarray, rhs: np.ndarray, weight: float) -> np.ndarray:
    return weight * lhs + (1.0 - weight) * rhs


def run_positive_tests() -> dict:
    checks, admitted = admitted_set()
    expected = {"rho0", "rho1", "mixed", "plus"}
    probe_sum = np.sum(projectors(), axis=0)
    avg = convex_average(candidates()["rho0"], candidates()["rho1"], 0.5)
    avg_check = check_state(avg, projectors())
    return {
        "finite_candidate_family_selects_expected_admitted_states": {
            "admitted": admitted,
            "expected": sorted(expected),
            "pass": set(admitted) == expected,
        },
        "finite_probe_family_resolves_identity": {
            "probe_count": len(projectors()),
            "identity_sum": probe_sum.tolist(),
            "pass": np.allclose(probe_sum, np.eye(2), atol=EPS),
        },
        "admitted_set_closed_under_sampled_convex_mixture": {
            "mixture_check": avg_check,
            "pass": avg_check["admitted"],
        },
        "admitted_states_have_bounded_probe_observables": {
            "probabilities": {name: checks[name]["probe_probabilities"] for name in admitted},
            "pass": all(checks[name]["probe_bounded"] for name in admitted),
        },
    }


def run_negative_tests() -> dict:
    checks, _ = admitted_set()
    rejected = {name: checks[name] for name in ["wrong_trace", "negative", "non_hermitian"]}
    return {
        "wrong_trace_candidate_rejected": {
            **rejected["wrong_trace"],
            "pass": not rejected["wrong_trace"]["admitted"] and not rejected["wrong_trace"]["trace_one"],
        },
        "negative_eigenvalue_candidate_rejected": {
            **rejected["negative"],
            "pass": not rejected["negative"]["admitted"] and not rejected["negative"]["psd"],
        },
        "non_hermitian_candidate_rejected": {
            **rejected["non_hermitian"],
            "pass": not rejected["non_hermitian"]["admitted"] and not rejected["non_hermitian"]["hermitian"],
        },
    }


def run_boundary_tests() -> dict:
    checks, admitted = admitted_set()
    pure_boundary = checks["rho0"]
    mixed_interior = checks["mixed"]
    return {
        "rank_one_boundary_state_admitted": {
            "eigenvalues": pure_boundary["eigenvalues"],
            "pass": pure_boundary["admitted"] and min(abs(x) for x in pure_boundary["eigenvalues"]) <= EPS,
        },
        "full_rank_interior_state_admitted": {
            "eigenvalues": mixed_interior["eigenvalues"],
            "pass": mixed_interior["admitted"] and min(mixed_interior["eigenvalues"]) > EPS,
        },
        "admitted_set_is_finite_and_nonempty": {
            "admitted_count": len(admitted),
            "pass": 0 < len(admitted) < len(candidates()),
        },
    }


def main() -> int:
    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in negative.values())
        and all(item["pass"] for item in boundary.values())
    )
    payload = {
        "name": "admissibility_manifold_mc",
        "classification": classification if all_pass else "exploratory_signal",
        "classification_note": CLASSIFICATION_NOTE,
        "claim_ceiling": "finite_admitted_set_only_not_axis_not_gstack_not_qit_promotion",
        "out_of_scope": [
            "GStack or nested manifold promotion",
            "Axis-0 field admission",
            "QIT engine admission",
            "nonclassical entropy-gradient claims",
        ],
        "promotion_condition": "requires separate topology, entropy, operator, coupling, and stage-gate receipts; this receipt alone cannot promote",
        "demotion_condition": "demote if finite candidate selection, excluded candidates, or probe-boundedness checks fail",
        "blocked_until": "separate later-stage receipts explicitly lift the coupling/axis/QIT gate",
        "next_lego_target": "n01_noncommutation_constraint",
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "probe_family": "finite_manifold_admissibility_only",
        "standalone_scope": {
            "imports_old_l0_l1_bundle": False,
            "forbidden_dependency_modules": ["sim_constraint_manifold_L0_L1", "engine_core"],
            "positive_instance": "finite candidate density states admitted by trace, PSD, Hermiticity, and bounded probe probabilities",
            "excluded_instance": "wrong-trace, negative-eigenvalue, and non-Hermitian candidates",
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "all_pass": all_pass,
            "claim_ceiling": "finite_admitted_set_only_not_axis_not_gstack_not_qit_promotion",
        },
        "all_pass": all_pass,
    }
    out = Path(__file__).resolve().parent / "a2_state" / "sim_results" / "admissibility_manifold_mc_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(json_safe(payload), indent=2), encoding="utf-8")
    print(f"ALL PASS: {all_pass} -> {out}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
