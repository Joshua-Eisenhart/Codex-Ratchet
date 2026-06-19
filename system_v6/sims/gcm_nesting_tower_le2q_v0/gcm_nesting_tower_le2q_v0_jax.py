#!/usr/bin/env python3
"""JAX/Python lane for gcm_nesting_tower_le2q_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp

import gcm_nesting_tower_le2q_v0_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def sign_array(values: jnp.ndarray) -> jnp.ndarray:
    return jnp.where(values < 0, -1, jnp.where(values > 0, 1, 0))


def probe_signature_matrix(coords: jnp.ndarray) -> jnp.ndarray:
    return jnp.stack([sign_array(coords[:, 0]), sign_array(coords[:, 2])], axis=1)


def registry_arrays(one_q: dict[str, Any], two_q: dict[str, Any]) -> dict[str, Any]:
    one_coords = jnp.array([row["coord_scaled"] for row in one_q["frozen_registry"]["survivors"]], dtype=jnp.int64)
    two_rows = two_q["frozen_2q_registry"]["survivors"]
    a_coords = jnp.array([row["first_bloch_scaled"] for row in two_rows], dtype=jnp.int64)
    b_coords = jnp.array([row["second_bloch_scaled"] for row in two_rows], dtype=jnp.int64)
    product_mask = jnp.array([row["family"] == "product_grid" for row in two_rows], dtype=bool)
    entangled_mask = jnp.array([bool(row["entangled"]) for row in two_rows], dtype=bool)
    return {
        "one_coords": one_coords,
        "one_sig": probe_signature_matrix(one_coords),
        "a_coords": a_coords,
        "b_coords": b_coords,
        "a_sig": probe_signature_matrix(a_coords),
        "b_sig": probe_signature_matrix(b_coords),
        "product_mask": product_mask,
        "entangled_mask": entangled_mask,
    }


def compatibility_counts(one_q: dict[str, Any], two_q: dict[str, Any]) -> dict[str, int]:
    arrays = registry_arrays(one_q, two_q)
    one_coords = arrays["one_coords"]
    one_sig = arrays["one_sig"]
    a_exact_matrix = jnp.all(arrays["a_coords"][:, None, :] == one_coords[None, :, :], axis=2)
    b_exact_matrix = jnp.all(arrays["b_coords"][:, None, :] == one_coords[None, :, :], axis=2)
    a_probe_matrix = jnp.all(arrays["a_sig"][:, None, :] == one_sig[None, :, :], axis=2)
    b_probe_matrix = jnp.all(arrays["b_sig"][:, None, :] == one_sig[None, :, :], axis=2)
    a_exact_count = jnp.sum(a_exact_matrix, axis=1)
    b_exact_count = jnp.sum(b_exact_matrix, axis=1)
    a_probe_count = jnp.sum(a_probe_matrix, axis=1)
    b_probe_count = jnp.sum(b_probe_matrix, axis=1)
    exact_mask = (a_exact_count > 0) & (b_exact_count > 0)
    probe_mask = (a_probe_count > 0) & (b_probe_count > 0)
    probe_triples_per_row = a_probe_count * b_probe_count * probe_mask
    product_exact = exact_mask & arrays["product_mask"]
    entangled_probe = probe_mask & arrays["entangled_mask"]
    return {
        "two_q_survivor_count": int(two_q["counts"]["survivor_count"]),
        "exact_tower_cardinality": int(jax.device_get(jnp.sum(exact_mask))),
        "exact_orphan_2q_count": int(jax.device_get(jnp.sum(~exact_mask))),
        "probe_compatible_2q_count": int(jax.device_get(jnp.sum(probe_mask))),
        "probe_orphan_2q_count": int(jax.device_get(jnp.sum(~probe_mask))),
        "probe_tower_cardinality": int(jax.device_get(jnp.sum(probe_triples_per_row))),
        "product_exact_subtower_count": int(jax.device_get(jnp.sum(product_exact))),
        "entangled_probe_compatible_2q_count": int(jax.device_get(jnp.sum(entangled_probe))),
        "max_probe_triples_per_row": int(jax.device_get(jnp.max(probe_triples_per_row))),
        "x64_enabled": bool(jax.config.jax_enable_x64),
    }


def sympy_guard(counts: dict[str, int]) -> dict[str, Any]:
    n2 = sp.Rational(counts["two_q_survivor_count"], 1)
    exact = sp.Rational(counts["exact_tower_cardinality"], 1)
    exact_orphans = sp.Rational(counts["exact_orphan_2q_count"], 1)
    probe = sp.Rational(counts["probe_compatible_2q_count"], 1)
    probe_orphans = sp.Rational(counts["probe_orphan_2q_count"], 1)
    product_exact = sp.Rational(counts["product_exact_subtower_count"], 1)
    return {
        "counts": {
            "two_q": str(n2),
            "exact": str(exact),
            "exact_orphans": str(exact_orphans),
            "probe": str(probe),
            "probe_orphans": str(probe_orphans),
            "product_exact": str(product_exact),
        },
        "pass": bool(
            n2 == common.EXPECTED_2Q_SURVIVOR_COUNT
            and exact == common.EXPECTED_EXACT_COMPATIBLE_2Q_COUNT
            and sp.simplify(exact + exact_orphans - n2) == 0
            and sp.simplify(probe + probe_orphans - n2) == 0
            and product_exact == common.EXPECTED_1Q_SURVIVOR_COUNT * common.EXPECTED_1Q_SURVIVOR_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    one_q = common.load_json(common.ONE_Q_REGISTRY_PATH)
    two_q = common.load_json(common.TWO_Q_REGISTRY_PATH)
    counts = compatibility_counts(one_q, two_q)
    exact = sympy_guard(counts)
    all_pass = bool(
        exact["pass"]
        and counts["entangled_probe_compatible_2q_count"] == common.EXPECTED_2Q_ENTANGLED_COUNT
        and counts["max_probe_triples_per_row"] == 4
        and counts["x64_enabled"]
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
        "aligned_packages_load_bearing": ["sympy"],
        "package_versions": {"jax": jax.__version__, "sympy": package_version("sympy")},
        "package_observables": {
            "sympy": "sp.Rational exact guard for exact/probe compatible counts and orphan partitions",
        },
        "reads_peer_result": False,
        "jax_mask_receipt": counts,
        "sympy_guard": exact,
        "exact_tower_cardinality": counts["exact_tower_cardinality"],
        "probe_tower_cardinality": counts["probe_tower_cardinality"],
        "probe_orphan_2q_count": counts["probe_orphan_2q_count"],
        "exact_orphan_2q_count": counts["exact_orphan_2q_count"],
        "product_exact_subtower_count": counts["product_exact_subtower_count"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact tower count identities"},
            "jax": {"tried": True, "used": True, "reason": "supportive vectorized compatibility mask computation"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive integer coordinate/signature arrays"},
        },
        "TOOL_INTEGRATION_DEPTH": {"sympy": "load_bearing", "jax": "supportive", "jax.numpy": "supportive"},
    }
    common.write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
