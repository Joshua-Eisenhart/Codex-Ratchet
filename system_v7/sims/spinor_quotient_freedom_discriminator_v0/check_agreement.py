#!/usr/bin/env python3
"""Agreement adjudicator for spinor_quotient_freedom_discriminator_v0."""

from __future__ import annotations

import json
import pathlib
import sys

SIM_ID = "spinor_quotient_freedom_discriminator_v0"
HERE = pathlib.Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"
EXACT = RESULTS / f"{SIM_ID}_exact_results.json"
JAX = RESULTS / f"{SIM_ID}_jax_results.json"


def load(path: pathlib.Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def main() -> int:
    exact = load(EXACT)
    jax = load(JAX)
    failures = []
    for name, obj in [("exact", exact), ("jax", jax)]:
        if not obj.get("all_tests_pass"):
            failures.append(f"{name}: all_tests_pass false")
        if obj.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification {obj.get('classification')}")
        if obj.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed not false")

    pairs = [
        ("state_count", exact["carrier"]["state_count"], jax["carrier"]["state_count"]),
        ("base_count", exact["carrier"]["base_count"], jax["carrier"]["base_count"]),
        ("fiber_phase_count", exact["carrier"]["fiber_phase_count"], jax["carrier"]["fiber_phase_count"]),
        ("public_class_count", exact["quotients"]["public_class_count"], jax["quotients"]["public_class_count"]),
        ("public_class_size", exact["quotients"]["public_class_size"], jax["quotients"]["public_class_size"]),
    ]
    for k, a, b in pairs:
        if a != b:
            failures.append(f"{k}: exact={a} jax={b}")
    for k, v in exact["tests"].items():
        if jax["tests"].get(k) != v:
            failures.append(f"test {k}: exact={v} jax={jax['tests'].get(k)}")

    agreement_ok = not failures
    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "scratch_discriminator_only; not spinor admission; not physical freedom; not density-matrix necessity",
        "TOOL_INTEGRATION_DEPTH": "cross_leg_agreement_only",
        "agreement_ok": agreement_ok,
        "legs": {
            "exact": "python finite quotient table",
            "jax": "integer-array vectorized phase-bin recomputation",
        },
        "invariants": {k: a for k, a, _b in pairs},
        "failures": failures,
        "honest_scope": {
            "earns": "two-engine agreement on conditional discriminator: public quotient erases fiber phase; frame probe splits; no-frame control blocks",
            "does_not_earn": "general spinor admission, physical freedom, final Hopf/Weyl layer, density-matrix necessity, or social translation claims",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if agreement_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
