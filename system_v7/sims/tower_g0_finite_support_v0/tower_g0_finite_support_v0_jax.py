#!/usr/bin/env python3
"""JAX leg for G0 finite support."""

from __future__ import annotations

import hashlib
import json
import pathlib
from datetime import datetime, timezone

from jax import config

config.update("jax_enable_x64", True)
import jax.numpy as jnp
import z3

SIM_ID = "tower_g0_finite_support_v0"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / f"{SIM_ID}_jax_results.json"


class TypedRefusal(Exception):
    pass


def construct_carrier(spec: dict) -> jnp.ndarray:
    if spec.get("family") == "unbounded":
        raise TypedRefusal("F01 refuses completed unbounded family construction; only finite support carriers are admissible.")
    return jnp.arange(int(spec["carrier_size"]), dtype=jnp.int64)


def z3_completed_infinity_control(carrier_ids: list[int]) -> dict:
    k = len(carrier_ids)
    images = [z3.Int(f"carrier_image_{i}") for i in range(k + 1)]
    solver = z3.Solver()
    for image in images:
        solver.add(z3.Or([image == class_id for class_id in carrier_ids]))
    solver.add(z3.Distinct(images))
    injective = str(solver.check()).lower()
    erased = z3.Solver()
    for image in images:
        erased.add(z3.Or([image == class_id for class_id in carrier_ids]))
    return {
        "solver_backend": "z3",
        "carrier_class_ids": carrier_ids,
        "carrier_size": k,
        "index_set_size": k + 1,
        "injective_pigeonhole_verdict": injective,
        "erased_injectivity_verdict": str(erased.check()).lower(),
        "claim": "No injective map exists from k+1 indices into the run's actual size-k carrier.",
    }


def main() -> None:
    carrier = construct_carrier({"family": "finite", "carrier_size": 4})
    support = carrier[:3]
    labels = jnp.array([20, 10, 30])
    shuffled = labels[jnp.array([1, 0, 2])]
    growth_counts = [int(n) for n in range(1, 6)]
    witnesses = {
        "carrier_size": int(carrier.size),
        "support_size": int(support.size),
        "supported_class_sum": int(jnp.sum(support)),
        "growth_counts": growth_counts,
        "growth_all_finite": all(n < 10**6 for n in growth_counts),
        "label_shuffle_signature": sorted(int(x) for x in shuffled.tolist()),
    }
    try:
        construct_carrier({"family": "unbounded"})
        caught_refusal = {"receipt_type": "NOT_CAUGHT", "caught": False}
    except TypedRefusal as exc:
        caught_refusal = {"receipt_type": "TYPED_REFUSAL", "caught": True, "caught_type": type(exc).__name__, "message": str(exc)}
    pigeonhole = z3_completed_infinity_control([int(x) for x in carrier.tolist()])
    refusals = {
        "unbounded_family_construction": caught_refusal,
        "completed_infinity_pigeonhole": pigeonhole,
    }
    all_pass = witnesses["support_size"] == 3 and witnesses["growth_all_finite"] and caught_refusal["caught"] and pigeonhole["injective_pigeonhole_verdict"] == "unsat" and pigeonhole["erased_injectivity_verdict"] == "sat"
    source = pathlib.Path(__file__).resolve()
    result = {
        "schema": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "source_path": str(source),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packages_used": ["jax", "jax.numpy", "z3", "json"],
        "aligned_packages_load_bearing": ["z3"],
        "reads_peer_result": False,
        "witnesses": witnesses,
        "refusal_receipts": refusals,
        "negative_controls": {"completed_infinity_pigeonhole_unsat": pigeonhole["injective_pigeonhole_verdict"] == "unsat", "erased_injectivity_control_sat": pigeonhole["erased_injectivity_verdict"] == "sat", "label_shuffle_preserves_signature": witnesses["label_shuffle_signature"] == [10, 20, 30]},
        "TOOL_MANIFEST": {"jax.numpy": {"tried": True, "used": True, "reason": "finite carrier/support arithmetic"}, "z3": {"tried": True, "used": True, "reason": "pigeonhole unsat over the actual constructed carrier"}},
        "TOOL_INTEGRATION_DEPTH": {"jax.numpy": "supportive", "z3": "load_bearing"},
        "all_pass": all_pass,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"engine": "jax", "all_pass": all_pass, "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
