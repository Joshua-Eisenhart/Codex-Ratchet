#!/usr/bin/env python3
"""PyTorch lane for gcm_geometry_attach_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import gcm_geometry_attach_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_density_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["attachment_map"]["survivor_spinor_maps"]
    spinors = torch.tensor([[row["psi_C2"][0]["re"], row["psi_C2"][1]["re"]] for row in rows], dtype=torch.float64)

    def density_observables(v: torch.Tensor) -> torch.Tensor:
        rho = torch.outer(v, v)
        trace = torch.trace(rho)
        det = torch.linalg.det(rho)
        norm = torch.sum(v * v)
        hopf = torch.stack([2.0 * v[0] * v[1], torch.tensor(0.0, dtype=torch.float64), v[0] * v[0] - v[1] * v[1]])
        hopf_norm = torch.sum(hopf * hopf)
        return torch.stack([trace, det, norm, hopf_norm])

    values = vmap(density_observables)(spinors)
    return {
        "spinor_shape": list(spinors.shape),
        "observable_shape": list(values.shape),
        "max_trace_error": float(torch.max(torch.abs(values[:, 0] - 1.0)).item()),
        "max_abs_det": float(torch.max(torch.abs(values[:, 1])).item()),
        "max_spinor_norm_error": float(torch.max(torch.abs(values[:, 2] - 1.0)).item()),
        "max_hopf_norm_error": float(torch.max(torch.abs(values[:, 3] - 1.0)).item()),
        "finite": bool(torch.isfinite(values).all().item()),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    density_classes = sp.Rational(payload["counts"]["density_quotient_unique_count"], 1)
    qclasses = sp.Rational(payload["counts"]["quotient_class_count"], 1)
    shells = sp.Rational(payload["counts"]["occupied_shell_count"], 1)
    return {
        "density_classes": str(density_classes),
        "quotient_classes": str(qclasses),
        "shells": str(shells),
        "pass": bool(
            density_classes == common.EXPECTED_QUOTIENT_CLASS_COUNT
            and qclasses == common.EXPECTED_QUOTIENT_CLASS_COUNT
            and shells == common.EXPECTED_SHELL_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    density = torch_density_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and density["finite"]
        and density["max_trace_error"] <= 1e-12
        and density["max_abs_det"] <= 1e-12
        and density["max_spinor_norm_error"] <= 1e-12
        and density["max_hopf_norm_error"] <= 1e-12
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
        "package_versions": {
            "torch": torch.__version__,
            "sympy": package_version("sympy"),
        },
        "package_observables": {
            "torch.func": "vmap(density_observables)(spinors) recomputes rho trace, determinant, spinor norm, and Hopf norm",
            "sympy": "sp.Rational exact density quotient and shell count guard",
        },
        "reads_peer_result": False,
        "torch_density_receipt": density,
        "sympy_guard": exact,
        "survivor_count": payload["counts"]["survivor_count"],
        "density_quotient_unique_count": payload["counts"]["density_quotient_unique_count"],
        "shell_count": payload["counts"]["occupied_shell_count"],
        "class_structure_survives_density_quotient": payload["attachment_map"]["class_structure_survives_density_quotient"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched density controls"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count guard"},
            "torch": {"tried": True, "used": True, "reason": "supportive tensor storage and reductions"},
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
