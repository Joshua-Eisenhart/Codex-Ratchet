#!/usr/bin/env python3
"""PyTorch lane for gcm_geometry_attach_2q_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import gcm_geometry_attach_2q_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_geometry_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    products = payload["geometry_packet"]["product_survivor_geometries"]
    entangled = payload["geometry_packet"]["entangled_survivor_geometries"]
    product_vectors = torch.tensor(
        [row["joint_geometry"]["A_pure_bloch"] for row in products]
        + [row["joint_geometry"]["B_pure_bloch"] for row in products],
        dtype=torch.float64,
    )
    entangled_radii = torch.tensor(
        [row["reduced_states"]["radius_A"] for row in entangled]
        + [row["reduced_states"]["radius_B"] for row in entangled],
        dtype=torch.float64,
    )

    def norm(v: torch.Tensor) -> torch.Tensor:
        return torch.sqrt(torch.sum(v * v))

    product_norms = vmap(norm)(product_vectors)
    return {
        "product_vector_shape": list(product_vectors.shape),
        "max_product_radius_error": float(torch.max(torch.abs(product_norms - 1.0)).item()),
        "min_entangled_radius": float(torch.min(entangled_radii).item()),
        "max_entangled_radius": float(torch.max(entangled_radii).item()),
        "all_entangled_subunit": bool(torch.all((entangled_radii > 0.0) & (entangled_radii < 1.0)).item()),
        "finite": bool(torch.isfinite(product_norms).all().item() and torch.isfinite(entangled_radii).all().item()),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    counts = payload["counts"]
    total = sp.Rational(counts["product_survivor_count"], 1) + sp.Rational(counts["entangled_survivor_count"], 1)
    return {
        "total": str(total),
        "survivors": str(sp.Rational(counts["survivor_count"], 1)),
        "pass": bool(
            total == common.EXPECTED_SURVIVOR_COUNT
            and sp.Rational(counts["entangled_fiber_count"], 1) == common.EXPECTED_ENTANGLED_FIBER_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    geometry = torch_geometry_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and geometry["finite"]
        and geometry["max_product_radius_error"] <= 1e-12
        and geometry["all_entangled_subunit"]
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
            "torch.func": "vmap over product Bloch vectors recomputes unit-radius geometry control",
            "sympy": "sp.Rational exact count decomposition guard",
        },
        "reads_peer_result": False,
        "torch_geometry_receipt": geometry,
        "sympy_guard": exact,
        "survivor_count": payload["counts"]["survivor_count"],
        "product_survivor_count": payload["counts"]["product_survivor_count"],
        "entangled_survivor_count": payload["counts"]["entangled_survivor_count"],
        "entangled_fiber_count": payload["counts"]["entangled_fiber_count"],
        "one_q_regression_ok": payload["controls"]["one_q_regression_through_partial_trace"]["image_equals_1q_attach_hopf_set"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched radius checks"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count guard"},
            "torch": {"tried": True, "used": True, "reason": "supportive tensor storage and reductions"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch.func": "load_bearing", "sympy": "load_bearing", "torch": "supportive"},
    }
    common.write_json(RESULT_PATH, result)
    return result


def main() -> int:
    result = build_result()
    print(json.dumps({"ok": result["all_pass"], "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
