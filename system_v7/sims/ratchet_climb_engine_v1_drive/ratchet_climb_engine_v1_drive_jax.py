#!/usr/bin/env python3
"""JAX + SMT leg for ratchet_climb_engine_v1_drive."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import json
from pathlib import Path

import jax
import jax.numpy as jnp

import ratchet_climb_core as core

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite pvec checks and Axis-0 drive variant parity over the reused 40-state C^8 carrier",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vectorized equality matrix and class-count measurements for distinction-loss detectors",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing non-definitional contextuality UNSAT/SAT bias-check flip",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent second solver for the same contextuality flip",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive run orchestration and receipt JSON emission",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"


def jax_observables() -> dict[str, object]:
    formal = core.load_formal_result("jax")
    carrier = core.source_carrier(formal)
    matrix = jnp.asarray([row["pvec"] for row in carrier["states"]], dtype=jnp.float64)
    eq = jnp.all(jnp.isclose(matrix[:, None, :], matrix[None, :, :], atol=1e-12, rtol=0.0), axis=2)
    coarse_idx = carrier["pauli_labels"].index("ZII")
    coarse = jnp.rint(matrix[:, coarse_idx])
    coarse_eq = coarse[:, None] == coarse[None, :]
    return {
        "jax_backend": jax.default_backend(),
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "full_equality_true_count": int(jnp.sum(eq)),
        "coarse_equality_true_count": int(jnp.sum(coarse_eq)),
        "full_singleton_classes_measured": int(jnp.sum(eq)) == matrix.shape[0],
        "coarse_merges_measured": int(jnp.sum(coarse_eq)) > matrix.shape[0],
    }


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    spec = core.load_spec()
    obs = jax_observables()
    runs = [core.run_climb("jax", cfg, {"jax_distinction_observables": obs}) for cfg in spec["drive_variants"]]
    payload = core.result_envelope(
        "jax",
        runs,
        {
            "source_path": core.rel(Path(__file__)),
            "source_sha256": core.sha256_file(Path(__file__)),
            "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "python_stdlib"],
            "aligned_packages_load_bearing": ["jax", "z3", "cvc5"],
            "package_observables": {
                "jax": "vectorized full/coarse equality matrix distinction-loss checks",
                "z3": "Peres-Mermin non-definitional UNSAT/SAT flip",
                "cvc5": "second-solver Peres-Mermin non-definitional UNSAT/SAT flip",
            },
            "tool_calls": [
                {
                    "tool": "jax",
                    "qualified_api/function": "jax.numpy.isclose / jax.numpy.sum",
                    "input_object": "40x63 finite Pauli expectation matrix from ratchet_formal_gates_v1",
                    "output_object": "full singleton and coarse merge equality counts",
                    "positive_case": "full probe equality is singleton on all 40 states",
                    "negative/erased_control": "coarse ZII equality merges states",
                    "boundary_case": "probe-order permutations preserve class count",
                    "demotion_condition": "demote if full singleton or coarse merge measurement disagrees with formal R4 result",
                    "gates": ["distinction_loss_detector", "projection_residual"],
                },
                {
                    "tool": "z3/cvc5",
                    "qualified_api/function": "Solver.check / Solver.checkSat",
                    "input_object": "Peres-Mermin contextual and noncontextual-control sign systems",
                    "output_object": "UNSAT contextual, SAT control",
                    "positive_case": "contextual assignment infeasible",
                    "negative/erased_control": "frustrating sign removed is feasible",
                    "boundary_case": "same variable/context shape in both systems",
                    "demotion_condition": "demote if flip does not occur in both solvers",
                    "gates": ["non_definitional_bias_check"],
                },
            ],
            "TOOL_MANIFEST": TOOL_MANIFEST,
            "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        },
    )
    out = RESULTS / "ratchet_climb_engine_v1_drive_jax_results.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"result_path": str(out), "all_pass": payload["all_pass"], "frontier": payload["frontier_reached"]}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
