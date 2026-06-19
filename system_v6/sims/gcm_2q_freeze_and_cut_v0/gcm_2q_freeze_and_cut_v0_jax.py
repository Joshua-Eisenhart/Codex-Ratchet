#!/usr/bin/env python3
"""JAX/Python lane for gcm_2q_freeze_and_cut_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from qutip import Qobj, basis, entropy_vn, tensor
import sympy as sp

import gcm_2q_freeze_and_cut_v0_common as common


ENGINE = "jax"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def complex_from_cell(cell: dict[str, float]) -> complex:
    return complex(float(cell["re"]), float(cell["im"]))


def matrix_from_json(row: list[list[dict[str, float]]]) -> list[list[complex]]:
    return [[complex_from_cell(cell) for cell in line] for line in row]


def as_jax_matrix(row: dict[str, Any]) -> jnp.ndarray:
    return jnp.array(matrix_from_json(row["rho_AB"]), dtype=jnp.complex128)


def entropy_from_eigs(eigs: jnp.ndarray) -> jnp.ndarray:
    probs = jnp.clip(jnp.real(eigs), 0.0, 1.0)
    probs = probs / jnp.maximum(jnp.sum(probs), 1.0e-30)
    terms = jnp.where(probs > common.TOL, -probs * jnp.log(probs), 0.0)
    return jnp.sum(terms)


def partial_trace_a(rho: jnp.ndarray) -> jnp.ndarray:
    shaped = jnp.reshape(rho, (2, 2, 2, 2))
    return jnp.einsum("abcb->ac", shaped)


def partial_trace_b(rho: jnp.ndarray) -> jnp.ndarray:
    shaped = jnp.reshape(rho, (2, 2, 2, 2))
    return jnp.einsum("abad->bd", shaped)


def partial_transpose_b(rho: jnp.ndarray) -> jnp.ndarray:
    shaped = jnp.reshape(rho, (2, 2, 2, 2))
    return jnp.reshape(jnp.transpose(shaped, (0, 3, 2, 1)), (4, 4))


def cut_metrics(rho: jnp.ndarray) -> jnp.ndarray:
    rho_a = partial_trace_a(rho)
    rho_b = partial_trace_b(rho)
    s_a = entropy_from_eigs(jnp.linalg.eigvalsh(rho_a))
    s_b = entropy_from_eigs(jnp.linalg.eigvalsh(rho_b))
    s_ab = entropy_from_eigs(jnp.linalg.eigvalsh(rho))
    pt = partial_transpose_b(rho)
    pt_eigs = jnp.linalg.eigvalsh(pt)
    negativity = jnp.sum(jnp.where(pt_eigs < -common.TOL, -pt_eigs, 0.0))
    return jnp.stack([s_a, s_b, s_ab, s_ab - s_b, s_a + s_b - s_ab, s_b - s_ab, negativity])


def jax_cut_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["entropy_tables"]["survivor_cut_entropy_rows"]
    matrices = jnp.stack([as_jax_matrix(row) for row in rows])
    metrics = jax.vmap(cut_metrics)(matrices)
    metrics_host = jax.device_get(metrics)
    expected = jnp.array(
        [
            [
                row["entropy_values"]["S_rho_A"],
                row["entropy_values"]["S_rho_B"],
                row["entropy_values"]["S_rho_AB"],
                row["entropy_values"]["conditional_S_A_given_B"],
                row["entropy_values"]["mutual_I_A_B"],
                row["entropy_values"]["coherent_I_c_A_to_B"],
                row["entropy_values"]["negativity"],
            ]
            for row in rows
        ],
        dtype=jnp.float64,
    )
    deltas = jnp.abs(metrics - expected)
    product_mask = jnp.array([row["family"] == "product_grid" for row in rows])
    entangled_mask = jnp.array([bool(row["entangled"]) for row in rows])
    return {
        "matrix_shape": list(matrices.shape),
        "metric_shape": list(metrics.shape),
        "max_abs_delta_vs_packet": common.q(float(jax.device_get(jnp.max(deltas)))),
        "product_count": int(jax.device_get(jnp.sum(product_mask))),
        "entangled_count": int(jax.device_get(jnp.sum(entangled_mask))),
        "max_product_negativity": common.q(float(jax.device_get(jnp.max(metrics[product_mask, 6])))),
        "min_entangled_negativity": common.q(float(jax.device_get(jnp.min(metrics[entangled_mask, 6])))),
        "max_entangled_conditional": common.q(float(jax.device_get(jnp.max(metrics[entangled_mask, 3])))),
        "all_product_negativity_zero": bool(jax.device_get(jnp.all(metrics[product_mask, 6] <= common.TOL))),
        "all_entangled_negativity_positive": bool(jax.device_get(jnp.all(metrics[entangled_mask, 6] > common.TOL))),
        "all_entangled_conditional_negative": bool(jax.device_get(jnp.all(metrics[entangled_mask, 3] < -common.TOL))),
        "x64_enabled": bool(jax.config.jax_enable_x64),
    }


def qutip_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["entropy_tables"]["survivor_cut_entropy_rows"]
    representatives = [rows[0], next(row for row in rows if row["entangled"])]
    _basis_probe = tensor(basis(2, 0), basis(2, 0))
    checks = []
    for row in representatives:
        qobj = Qobj(matrix_from_json(row["rho_AB"]), dims=[[2, 2], [2, 2]])
        rho_a = qobj.ptrace(0)
        rho_b = qobj.ptrace(1)
        checks.append(
            {
                "gcm_2q_survivor_id": row["gcm_2q_survivor_id"],
                "S_rho_A_qutip": common.q(float(entropy_vn(rho_a, base=math_e()))),
                "S_rho_B_qutip": common.q(float(entropy_vn(rho_b, base=math_e()))),
                "S_rho_AB_qutip": common.q(float(entropy_vn(qobj, base=math_e()))),
                "S_rho_A_packet": row["entropy_values"]["S_rho_A"],
                "S_rho_B_packet": row["entropy_values"]["S_rho_B"],
                "S_rho_AB_packet": row["entropy_values"]["S_rho_AB"],
            }
        )
    return {
        "representative_count": len(checks),
        "basis_tensor_dims": str(_basis_probe.dims),
        "checks": checks,
        "max_abs_entropy_delta": max(
            abs(check["S_rho_A_qutip"] - check["S_rho_A_packet"])
            + abs(check["S_rho_B_qutip"] - check["S_rho_B_packet"])
            + abs(check["S_rho_AB_qutip"] - check["S_rho_AB_packet"])
            for check in checks
        ),
    }


def math_e() -> float:
    return float(jnp.e)


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    counts = payload["counts"]
    two_q = sp.Rational(counts["two_q_survivor_count"], 1)
    product = sp.Rational(counts["product_survivor_count"], 1)
    entangled = sp.Rational(counts["entangled_survivor_count"], 1)
    classes = sp.Rational(counts["two_q_class_count"], 1)
    embedded = sp.Rational(counts["one_q_product_embedding_count"], 1)
    return {
        "counts": {
            "two_q": str(two_q),
            "product": str(product),
            "entangled": str(entangled),
            "classes": str(classes),
            "embedded": str(embedded),
        },
        "pass": bool(
            two_q == common.EXPECTED_TWO_Q_SURVIVOR_COUNT
            and product == common.EXPECTED_PRODUCT_SURVIVOR_COUNT
            and entangled == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT
            and classes == common.EXPECTED_TWO_Q_CLASS_COUNT
            and embedded == common.EXPECTED_ONE_Q_SURVIVOR_COUNT
            and sp.simplify(two_q - product - entangled) == 0
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet(write=False)
    jax_receipt = jax_cut_receipt(payload)
    qutip_check = qutip_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and jax_receipt["max_abs_delta_vs_packet"] <= 1.0e-10
        and jax_receipt["all_product_negativity_zero"]
        and jax_receipt["all_entangled_negativity_positive"]
        and jax_receipt["all_entangled_conditional_negative"]
        and qutip_check["max_abs_entropy_delta"] <= 1.0e-10
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
        "packages_used": ["jax", "jax.numpy", "qutip", "sympy"],
        "aligned_packages_load_bearing": ["qutip", "sympy"],
        "package_versions": {
            "jax": jax.__version__,
            "qutip": package_version("qutip"),
            "sympy": package_version("sympy"),
        },
        "package_observables": {
            "qutip": "Qobj(...).ptrace plus entropy_vn representative checks on the pinned A|B cut",
            "sympy": "sp.Rational exact finite count guard for product/entangled/embedding counts",
        },
        "reads_peer_result": False,
        "jax_cut_receipt": jax_receipt,
        "qutip_receipt": qutip_check,
        "sympy_guard": exact,
        "survivor_count": payload["counts"]["two_q_survivor_count"],
        "quotient_class_count": payload["counts"]["two_q_class_count"],
        "candidate_region_count": payload["counts"]["candidate_region_count"],
        "product_survivor_count": payload["counts"]["product_survivor_count"],
        "entangled_survivor_count": payload["counts"]["entangled_survivor_count"],
        "embedded_1q_count": payload["counts"]["one_q_product_embedding_count"],
        "metric_summary": {
            "max_product_negativity": jax_receipt["max_product_negativity"],
            "min_entangled_negativity": jax_receipt["min_entangled_negativity"],
            "max_entangled_conditional": jax_receipt["max_entangled_conditional"],
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "qutip": {"tried": True, "used": True, "reason": "load-bearing representative partial-trace entropy checks"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count guard"},
            "jax": {"tried": True, "used": True, "reason": "supportive batched cut metric recomputation"},
            "jax.numpy": {"tried": True, "used": True, "reason": "supportive matrix and eigenspectrum arrays"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "qutip": "load_bearing",
            "sympy": "load_bearing",
            "jax": "supportive",
            "jax.numpy": "supportive",
        },
    }
    common.write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
