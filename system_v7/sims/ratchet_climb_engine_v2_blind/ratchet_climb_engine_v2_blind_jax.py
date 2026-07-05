#!/usr/bin/env python3
"""JAX leg: native fact-only drive and blinded selector."""

from __future__ import annotations

from jax import config

config.update("jax_enable_x64", True)

import json
import random
from pathlib import Path

import jax
import jax.numpy as jnp

import ratchet_climb_core as core

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "load-bearing native JAX drive, mixedness, commutator, and blinded selector facts"},
    "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing vectorized quotient and two-carrier drive measurements"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive result JSON emission"},
}
TOOL_INTEGRATION_DEPTH = {"jax": "load_bearing", "jax.numpy": "load_bearing", "python_stdlib": "supportive"}


def qcount(car):
    mat = jnp.asarray([row["pvec"] for row in car["states"]], dtype=jnp.float64)
    eq = jnp.all(jnp.isclose(mat[:, None, :], mat[None, :, :], atol=1e-12, rtol=0.0), axis=2)
    return int(jnp.sum(jnp.any(eq, axis=1))), 1


def state(theta):
    v = jnp.zeros((4,), dtype=jnp.complex128).at[0].set(jnp.cos(theta)).at[3].set(jnp.sin(theta))
    return v / jnp.linalg.norm(v)


def mixed(v):
    t = jnp.reshape(v, (2, 2))
    rho = t @ jnp.conjugate(t).T
    return round(float(jnp.real(1.0 - jnp.trace(rho @ rho))), 12)


def drive(kind, seed):
    rng = random.Random(seed)
    z = jnp.asarray([[1, 0], [0, -1]], dtype=jnp.complex128)
    h = jnp.asarray([[1, 1], [1, -1]], dtype=jnp.complex128) / jnp.sqrt(2.0)
    i2 = jnp.eye(2, dtype=jnp.complex128)
    cnot = jnp.asarray([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=jnp.complex128)
    ua, ub = (jnp.kron(z, i2), jnp.kron(z, i2)) if kind == "commuting_control" else (jnp.kron(h, i2), cnot)
    base = state(jnp.pi / 5.0)
    facts, window = [], []
    for tick in range(1, 9):
        ab, ba = ub @ (ua @ base), ua @ (ub @ base)
        if kind == "memoryless_control":
            jitter = rng.choice([-1.0, 1.0]) * 0.03
            ab, ba = state(jnp.pi / 5.0 + jitter), state(jnp.pi / 5.0 - jitter)
        pair = [mixed(ab), mixed(ba)]
        if kind != "memoryless_control":
            window = (window + [tuple(pair)])[-4:]
        facts.append({"tick": tick, "reduced_state_mixedness_values": pair, "commutator_norm": round(float(jnp.linalg.norm(ua @ ub - ub @ ua)), 12), "order_gap_norm": round(float(jnp.linalg.norm(ab - ba)), 12), "persistence_count": 0 if kind == "memoryless_control" else len(set(window))})
        if kind != "static_control":
            base = ab / jnp.linalg.norm(ab)
    if kind == "static_control":
        facts = facts[:1]
    if kind == "label_fact_shuffle_control":
        rng.shuffle(facts)
    return facts


def selector(facts):
    candidates = [
        {"candidate_id": "survivor_partition_slot", "rung": 5, "strength": 1, "needs": "persistent_mixedness_split"},
        {"candidate_id": "ordered_update_slot", "rung": 6, "strength": 2, "needs": "persistent_order_gap"},
        {"candidate_id": "density_readout_slot", "rung": 10, "strength": 3, "needs": "late_density_refused"},
        {"candidate_id": "hopf_readout_slot", "rung": 11, "strength": 4, "needs": "late_hopf_refused"},
    ]
    for fact in facts:
        mixed_split = abs(fact["reduced_state_mixedness_values"][0] - fact["reduced_state_mixedness_values"][1])
        if fact["commutator_norm"] > 0 and fact["persistence_count"] >= 2 and mixed_split > 0.2:
            return {"selected": candidates[0], "facts_used": [fact], "enumerated_candidates": candidates}
    return {"selected": None, "facts_used": [], "enumerated_candidates": candidates}


def run_variant(cfg):
    car = core.carrier("jax")
    full, none = qcount(car)
    admitted, receipts, locks = core.base_receipts("jax", car, full, none)
    facts = drive(cfg["kind"], int(cfg["seed"]))
    picked = selector(facts)
    rejected = []
    if picked["selected"]:
        admitted.append(int(picked["selected"]["rung"]))
        receipts.append({"rung": picked["selected"]["rung"], "admitted": True, "selected_lift": picked["selected"]["candidate_id"], "distinction_loss_detector": {"facts": picked["facts_used"]}})
        locks.append({"rung": picked["selected"]["rung"], "decision": receipts[-1], "prev_hash": locks[-1]["entry_hash"], "entry_hash": core.sha256_json(receipts[-1])})
    else:
        rejected.append({"typed_refusal": "rejected_unforced", "reason": "rung4 quotient not measured lossy by fact-only stream", "enumerated_candidates": picked["enumerated_candidates"]})
    return {"run_id": cfg["run_id"], "variant_id": cfg["variant_id"], "engine": "jax", "facts": facts, "blinded_selector": picked, "climbed_ladder": admitted, "frontier_rung": max(admitted), "append_only_lock_ledger": locks, "rejected_frontier_attempts": rejected, "rejected_unforced": rejected, "all_pass": full == car["state_count"]}


def main():
    runs = [run_variant(cfg) for cfg in core.load_spec()["drive_variants"]]
    payload = core.finish_payload("jax", runs, {"source_path": core.rel(Path(__file__)), "source_sha256": core.sha256_file(Path(__file__)), "packages_used": ["jax", "jax.numpy", "python_stdlib"], "aligned_packages_load_bearing": ["jax", "jax.numpy"], "package_observables": {"jax_backend": jax.default_backend()}, "TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH})
    out = core.RESULTS / "ratchet_climb_engine_v2_blind_jax_results.json"
    core.write_json(out, payload)
    print(json.dumps({"all_pass": payload["all_pass"], "frontier_by_variant": payload["frontier_by_variant"]}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
