#!/usr/bin/env python3
"""JAX/Python lane for gcm_geometry_attach_2q_v1."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp

import gcm_geometry_attach_2q_v1_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def radius_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    products = payload["geometry_packet"]["product_survivor_geometries"]
    entangled = payload["geometry_packet"]["entangled_survivor_geometries"]
    product_vectors = jnp.array(
        [
            row["joint_geometry"]["A_pure_bloch"]
            for row in products
        ]
        + [
            row["joint_geometry"]["B_pure_bloch"]
            for row in products
        ],
        dtype=jnp.float64,
    )
    entangled_radii = jnp.array(
        [
            row["reduced_states"]["radius_A"]
            for row in entangled
        ]
        + [
            row["reduced_states"]["radius_B"]
            for row in entangled
        ],
        dtype=jnp.float64,
    )
    product_norms = jnp.sqrt(jnp.sum(product_vectors * product_vectors, axis=1))
    return {
        "product_vector_shape": list(product_vectors.shape),
        "entangled_radius_shape": list(entangled_radii.shape),
        "max_product_radius_error": float(jax.device_get(jnp.max(jnp.abs(product_norms - 1.0)))),
        "min_entangled_radius": float(jax.device_get(jnp.min(entangled_radii))),
        "max_entangled_radius": float(jax.device_get(jnp.max(entangled_radii))),
        "all_entangled_subunit": bool(jax.device_get(jnp.all((entangled_radii > 0.0) & (entangled_radii < 1.0)))),
        "x64_enabled": bool(jax.config.jax_enable_x64),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    counts = payload["counts"]
    return {
        "survivors": str(sp.Rational(counts["survivor_count"], 1)),
        "products": str(sp.Rational(counts["product_survivor_count"], 1)),
        "entangled": str(sp.Rational(counts["entangled_survivor_count"], 1)),
        "fibers": str(sp.Rational(counts["entangled_fiber_count"], 1)),
        "pass": bool(
            sp.Rational(counts["survivor_count"], 1) == common.EXPECTED_SURVIVOR_COUNT
            and sp.Rational(counts["product_survivor_count"], 1) == common.EXPECTED_PRODUCT_SURVIVOR_COUNT
            and sp.Rational(counts["entangled_survivor_count"], 1) == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT
            and sp.Rational(counts["entangled_fiber_count"], 1) == common.EXPECTED_ENTANGLED_FIBER_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    radius = radius_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and radius["max_product_radius_error"] <= 1e-12
        and radius["all_entangled_subunit"]
        and exact["pass"]
    )
    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": common.SIM_ID,
        "engine": ENGINE,
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "generated_at": common.now_z(),
        "classification": common.CLASSIFICATION,
        "promotion_allowed": common.PROMOTION_ALLOWED,
        "formal_admission_allowed": common.FORMAL_ADMISSION_ALLOWED,
        "packages_used": ["jax", "jax.numpy", "sympy"],
        "aligned_packages_load_bearing": ["jax.numpy", "sympy"],
        "package_versions": {"jax": jax.__version__, "sympy": package_version("sympy")},
        "package_observables": {
            "jax.numpy": "batched product pure Bloch radii and entangled reduced radii",
            "sympy": "sp.Rational exact survivor/product/entangled/fiber count guard",
        },
        "reads_peer_result": False,
        "radius_receipt": radius,
        "sympy_guard": exact,
        "survivor_count": payload["counts"]["survivor_count"],
        "product_survivor_count": payload["counts"]["product_survivor_count"],
        "entangled_survivor_count": payload["counts"]["entangled_survivor_count"],
        "entangled_fiber_count": payload["counts"]["entangled_fiber_count"],
        "one_q_regression_ok": payload["controls"]["one_q_regression_through_partial_trace"]["image_equals_1q_attach_hopf_set"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "jax.numpy": {"tried": True, "used": True, "reason": "load-bearing batched radius checks"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count guard"},
            "jax": {"tried": True, "used": True, "reason": "supportive x64 execution"},
        },
        "TOOL_INTEGRATION_DEPTH": {"jax.numpy": "load_bearing", "sympy": "load_bearing", "jax": "supportive"},
    }
    common.write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
