#!/usr/bin/env python3
"""PyTorch lane for gcm_2q_freeze_and_cut_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import gcm_2q_freeze_and_cut_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def complex_from_cell(cell: dict[str, float]) -> complex:
    return complex(float(cell["re"]), float(cell["im"]))


def matrix_from_json(row: list[list[dict[str, float]]]) -> list[list[complex]]:
    return [[complex_from_cell(cell) for cell in line] for line in row]


def entropy_from_eigs(eigs: torch.Tensor) -> torch.Tensor:
    probs = torch.clamp(torch.real(eigs), min=0.0, max=1.0)
    probs = probs / torch.clamp(torch.sum(probs), min=1.0e-30)
    return torch.sum(torch.where(probs > common.TOL, -probs * torch.log(probs), torch.zeros_like(probs)))


def partial_trace_a(rho: torch.Tensor) -> torch.Tensor:
    shaped = rho.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", shaped)


def partial_trace_b(rho: torch.Tensor) -> torch.Tensor:
    shaped = rho.reshape(2, 2, 2, 2)
    return torch.einsum("abad->bd", shaped)


def partial_transpose_b(rho: torch.Tensor) -> torch.Tensor:
    shaped = rho.reshape(2, 2, 2, 2)
    return shaped.permute(0, 3, 2, 1).reshape(4, 4)


def cut_metrics(rho: torch.Tensor) -> torch.Tensor:
    rho_a = partial_trace_a(rho)
    rho_b = partial_trace_b(rho)
    s_a = entropy_from_eigs(torch.linalg.eigvalsh(rho_a))
    s_b = entropy_from_eigs(torch.linalg.eigvalsh(rho_b))
    s_ab = entropy_from_eigs(torch.linalg.eigvalsh(rho))
    pt_eigs = torch.linalg.eigvalsh(partial_transpose_b(rho))
    negativity = torch.sum(torch.where(pt_eigs < -common.TOL, -pt_eigs, torch.zeros_like(pt_eigs)))
    return torch.stack([s_a, s_b, s_ab, s_ab - s_b, s_a + s_b - s_ab, s_b - s_ab, negativity])


def torch_cut_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["entropy_tables"]["survivor_cut_entropy_rows"]
    matrices = torch.tensor([matrix_from_json(row["rho_AB"]) for row in rows], dtype=torch.complex128)
    metrics = vmap(cut_metrics)(matrices)
    expected = torch.tensor(
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
        dtype=torch.float64,
    )
    deltas = torch.abs(metrics - expected)
    product_mask = torch.tensor([row["family"] == "product_grid" for row in rows], dtype=torch.bool)
    entangled_mask = torch.tensor([bool(row["entangled"]) for row in rows], dtype=torch.bool)
    return {
        "matrix_shape": list(matrices.shape),
        "metric_shape": list(metrics.shape),
        "max_abs_delta_vs_packet": common.q(float(torch.max(deltas).item())),
        "product_count": int(torch.sum(product_mask).item()),
        "entangled_count": int(torch.sum(entangled_mask).item()),
        "max_product_negativity": common.q(float(torch.max(metrics[product_mask, 6]).item())),
        "min_entangled_negativity": common.q(float(torch.min(metrics[entangled_mask, 6]).item())),
        "max_entangled_conditional": common.q(float(torch.max(metrics[entangled_mask, 3]).item())),
        "all_product_negativity_zero": bool(torch.all(metrics[product_mask, 6] <= common.TOL).item()),
        "all_entangled_negativity_positive": bool(torch.all(metrics[entangled_mask, 6] > common.TOL).item()),
        "all_entangled_conditional_negative": bool(torch.all(metrics[entangled_mask, 3] < -common.TOL).item()),
        "finite": bool(torch.isfinite(torch.real(metrics)).all().item()),
    }


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
    torch_receipt = torch_cut_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and torch_receipt["finite"]
        and torch_receipt["max_abs_delta_vs_packet"] <= 1.0e-10
        and torch_receipt["all_product_negativity_zero"]
        and torch_receipt["all_entangled_negativity_positive"]
        and torch_receipt["all_entangled_conditional_negative"]
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
        "packages_used": ["torch", "torch.func", "sympy"],
        "aligned_packages_load_bearing": ["torch.func", "sympy"],
        "package_versions": {"torch": torch.__version__, "sympy": package_version("sympy")},
        "package_observables": {
            "torch.func": "vmap(cut_metrics)(rho_AB) recomputes partial traces, entropy, partial transpose, and negativity",
            "sympy": "sp.Rational exact finite count guard for product/entangled/embedding counts",
        },
        "reads_peer_result": False,
        "torch_cut_receipt": torch_receipt,
        "sympy_guard": exact,
        "survivor_count": payload["counts"]["two_q_survivor_count"],
        "quotient_class_count": payload["counts"]["two_q_class_count"],
        "candidate_region_count": payload["counts"]["candidate_region_count"],
        "product_survivor_count": payload["counts"]["product_survivor_count"],
        "entangled_survivor_count": payload["counts"]["entangled_survivor_count"],
        "embedded_1q_count": payload["counts"]["one_q_product_embedding_count"],
        "metric_summary": {
            "max_product_negativity": torch_receipt["max_product_negativity"],
            "min_entangled_negativity": torch_receipt["min_entangled_negativity"],
            "max_entangled_conditional": torch_receipt["max_entangled_conditional"],
        },
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched cut-metric recomputation"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count guard"},
            "torch": {"tried": True, "used": True, "reason": "supportive tensor storage and eigensolver"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch.func": "load_bearing",
            "sympy": "load_bearing",
            "torch": "supportive",
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
