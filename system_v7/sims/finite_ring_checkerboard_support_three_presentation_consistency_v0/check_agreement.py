#!/usr/bin/env python3
"""Agreement adjudicator for finite_ring_checkerboard_support_three_presentation_consistency_v0.

Compares the exact Python finite-dictionary/table leg and the JAX vectorized-array leg on the
load-bearing invariants for the Levos target. It does not self-upgrade the sim; it only checks
cross-leg agreement.
"""

from __future__ import annotations

import json
import pathlib
import sys

SIM_ID = "finite_ring_checkerboard_support_three_presentation_consistency_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"

EXACT = RESULTS / f"{SIM_ID}_exact_results.json"
JAX = RESULTS / f"{SIM_ID}_jax_results.json"


def load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def get_q(obj: dict) -> dict:
    return obj["tests"]["quotient_classes_density_vs_phase"]


def main() -> int:
    exact = load(EXACT)
    jax = load(JAX)
    failures = []

    # Both legs must pass their own test/control suites.
    for name, obj in [("exact", exact), ("jax", jax)]:
        if not obj.get("all_tests_pass"):
            failures.append(f"{name}: all_tests_pass is false")
        if not obj.get("all_controls_pass"):
            failures.append(f"{name}: all_controls_pass is false")
        if obj.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: wrong classification {obj.get('classification')}")
        if obj.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed not false")

    # Core numeric invariants.
    pairs = [
        ("support_count", exact["support_parameters"]["support_count"], jax["support_parameters"]["support_count"]),
        ("density_class_count", get_q(exact)["density_class_count"], get_q(jax)["density_class_count"]),
        ("phase_sensitive_class_count", get_q(exact)["phase_sensitive_class_count"], get_q(jax)["phase_sensitive_class_count"]),
        ("flat_edges", exact["tests"]["folding_reindexing_invariants_valid"]["flat_edges"], jax["tests"]["folding_reindexing_invariants_valid"]["flat_edges"]),
        ("ring_edges", exact["tests"]["folding_reindexing_invariants_valid"]["ring_edges"], jax["tests"]["folding_reindexing_invariants_valid"]["ring_edges"]),
        ("full_components", exact["tests"]["folding_reindexing_invariants_valid"]["full_components"], jax["tests"]["folding_reindexing_invariants_valid"]["full_components"]),
    ]
    for key, a, b in pairs:
        if a != b:
            failures.append(f"{key}: exact={a} jax={b}")

    expected = {
        "support_count": 96,
        "density_class_count": 24,
        "phase_sensitive_class_count": 96,
        "flat_edges": 256,
        "ring_edges": 256,
        "full_components": 2,
    }
    got = {k: a for k, a, _ in pairs}
    for k, v in expected.items():
        if got[k] != v:
            failures.append(f"expected {k}={v}, got {got[k]}")

    agreement_ok = not failures
    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "agreement_ok": agreement_ok,
        "legs": {
            "exact": "dictionary/table finite enumeration",
            "jax": "integer-array/vectorized density and quotient recomputation",
        },
        "invariants": got,
        "failures": failures,
        "honest_scope": {
            "earns": "two-engine agreement on support count, quotient counts, phi-blind density split, adjacency counts, and component count",
            "does_not_earn": "final M(C), full Hopf/Weyl dynamics, Axis0 closure, QIT engine, or canonical admission; still needs PyTorch/Julia before full three-engine path",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if agreement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
