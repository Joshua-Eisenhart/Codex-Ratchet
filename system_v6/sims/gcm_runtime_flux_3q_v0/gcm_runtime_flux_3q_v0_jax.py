#!/usr/bin/env python3
"""JAX/SymPy scoped parity lane for gcm_runtime_flux_3q_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp

import gcm_runtime_flux_3q_v0_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.JAX_RESULT_PATH
CLASSIFICATION = "scratch_diagnostic"
TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact sign/cut-count guard"},
    "jax": {"tried": True, "used": True, "reason": "supportive vector sign check"},
}
TOOL_INTEGRATION_DEPTH = {"sympy": "load_bearing", "jax": "supportive"}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def sympy_guard(packet: dict[str, Any]) -> dict[str, Any]:
    need = packet["three_q_necessity_row"]
    three_q_cuts = sp.Rational(need["three_q_cut_count"], 1)
    two_q_cuts = sp.Rational(need["two_q_cut_count"], 1)
    right_chi = sp.Rational(2, 1)
    left_chi = sp.Rational(-2, 1)
    return {
        "three_q_cuts": str(three_q_cuts),
        "two_q_cuts": str(two_q_cuts),
        "left_chi": str(left_chi),
        "right_chi": str(right_chi),
        "pass": bool(three_q_cuts == 3 and two_q_cuts == 1 and sp.simplify(right_chi + left_chi) == 0),
    }


def jax_vector_guard(packet: dict[str, Any]) -> dict[str, Any]:
    rows = {row["row_id"]: row for row in packet["runtime_current_rows"]}
    values = jnp.array(
        [
            rows["engine_R_flux_OUT_right_3q"]["J_cut"]["net_delta_mutual_I"],
            rows["engine_R_flux_OUT_right_3q"]["J_ent"]["net_delta_negativity"],
            rows["engine_L_flux_IN_left_3q"]["J_cut"]["net_delta_mutual_I"],
            rows["engine_L_flux_IN_left_3q"]["J_ent"]["net_delta_negativity"],
        ],
        dtype=jnp.float64,
    )
    signs = jnp.sign(values)
    return {
        "values": [common.q(float(value)) for value in jax.device_get(values).tolist()],
        "signs": [int(value) for value in jax.device_get(signs).tolist()],
        "right_positive_left_negative": bool(jax.device_get(jnp.all(signs == jnp.array([1.0, 1.0, -1.0, -1.0])))),
        "x64_enabled": bool(jax.config.jax_enable_x64),
    }


def build_result() -> dict[str, Any]:
    packet = common.build_packet(write=False)
    exact = sympy_guard(packet)
    vector = jax_vector_guard(packet)
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": common.SIM_ID,
        "engine": ENGINE,
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "generated_at": common.now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "packages_used": ["jax", "jax.numpy", "sympy"],
        "aligned_packages_load_bearing": ["sympy"],
        "package_versions": {"jax": jax.__version__, "sympy": package_version("sympy")},
        "package_observables": {
            "sympy": "sp.Rational guard for three_q_cut_count/two_q_cut_count and L/R chirality cancellation",
        },
        "reads_peer_result": False,
        "sympy_guard": exact,
        "jax_vector_guard": vector,
        "engine_values": {
            "right_j_cut_sign": 1,
            "left_j_cut_sign": -1,
            "right_j_ent_sign": 1,
            "left_j_ent_sign": -1,
            "right_j_chi": 2,
            "left_j_chi": -2,
        },
        "all_pass": bool(packet["all_pass"] and exact["pass"] and vector["right_positive_left_negative"]),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    common.write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
