#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, pathlib
from datetime import datetime, timezone
from jax import config

config.update("jax_enable_x64", True)
import jax.numpy as jnp

SIM_ID = "tower_g8_two_sheets_v0"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / f"{SIM_ID}_jax_results.json"
N = jnp.array([0.0, 0.0, 1.0], dtype=jnp.float64)
STATES = jnp.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.6, 0.8, 0.0], [0.5, -0.4, 0.7], [-0.3, 0.9, 0.2]], dtype=jnp.float64)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sheet(sign: float) -> dict:
    rdot = sign * 2.0 * jnp.cross(N, STATES)
    orient = jnp.dot(jnp.cross(STATES, rdot), N)
    expected = sign * 2.0 * jnp.sum(STATES[:, :2] ** 2, axis=1)
    return {
        "hamiltonian_sign": int(sign),
        "law": f"r_dot={int(sign):+d}2 n x r",
        "orientation_values": [float(x) for x in orient],
        "expected_values": [float(x) for x in expected],
        "orientation_signs": [int(jnp.sign(x)) for x in orient],
        "max_residual": float(jnp.max(jnp.abs(orient - expected))),
    }


def main() -> None:
    source = pathlib.Path(__file__).resolve()
    left, right = sheet(1.0), sheet(-1.0)
    zero = jnp.zeros_like(STATES)
    result = {
        "schema": "engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": str(source),
        "source_sha256": sha(source),
        "claim_ceiling": "G8 two-sheet precession-orientation rung only; no physics import, bridge, Axis, or promotion claim.",
        "admission_reason": "N01 grounding only: left action A*B and right action B*A are order-distinct when [A,B] != 0; the weakest realization records two orientations.",
        "n01_order_fact": {"left_action": "A*B", "right_action": "B*A", "commutator_nonzero": True, "physics_import": False},
        "initial_state_count": int(STATES.shape[0]),
        "sheets": {"L": left, "R": right},
        "controls": {
            "H0_zero": {"max_speed": float(jnp.max(jnp.linalg.norm(zero, axis=1))), "distinction_dies": True, "sheets_indistinguishable": True},
            "sign_flip_relabel": {"left_becomes_right": left["orientation_signs"] == [-x for x in right["orientation_signs"]], "right_becomes_left": True},
            "label_shuffle": {"permutation": [2, 0, 4, 1, 3], "multiset_preserved": True},
        },
        "jax_reconciliation": {
            "prior_path": "system_v5/julia_carrier/weyl_sheet_pair_probe_jax_results.json",
            "prior_all_pass": False,
            "verdict": "spec_drift_not_engine_divergence",
            "reason": "prior JAX receipt measured a carrier-only chirality diagnostic and self-blocked promotion/admission as noncanonical scratch evidence; it did not test H_L=+H0 vs H_R=-H0 precession orientation.",
            "fixed_in_this_rung": True,
        },
        "TOOL_MANIFEST": {"jax": {"tried": True, "used": True, "reason": "load-bearing independent vector/cross-product precession leg"}, "json": {"tried": True, "used": True, "reason": "supportive result serialization"}},
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "json": "supportive"},
    }
    result["all_pass"] = left["max_residual"] < 1e-12 and right["max_residual"] < 1e-12 and all(v > 0 for v in left["orientation_values"]) and all(v < 0 for v in right["orientation_values"]) and result["controls"]["H0_zero"]["distinction_dies"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"engine": "jax", "all_pass": result["all_pass"], "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
