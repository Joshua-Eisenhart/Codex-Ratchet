#!/usr/bin/env python3
"""PyTorch lane for gcm_connection_flux_attach_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import gcm_connection_flux_attach_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_flux_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["connection_flux_attachment"]["shell_rows"]
    eta = torch.tensor([row["T_eta_rad"] for row in rows], dtype=torch.float64)

    def observables(value: torch.Tensor) -> torch.Tensor:
        return torch.stack(
            [
                -2.0 * torch.pi * torch.cos(2.0 * value),
                -2.0 * torch.sin(2.0 * value),
                torch.cos(2.0 * value),
            ]
        )

    values = vmap(observables)(eta)
    expected_h = torch.tensor([row["holonomy_lifted_cycle"]["value"] for row in rows], dtype=torch.float64)
    expected_f = torch.tensor([row["curvature"]["F_eta_chi"] for row in rows], dtype=torch.float64)
    return {
        "eta_shape": list(eta.shape),
        "observable_shape": list(values.shape),
        "max_holonomy_error": float(torch.max(torch.abs(values[:, 0] - expected_h)).item()),
        "max_curvature_error": float(torch.max(torch.abs(values[:, 1] - expected_f)).item()),
        "finite": bool(torch.isfinite(values).all().item()),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["connection_flux_attachment"]["shell_rows"]
    shell_count = sp.Rational(len(rows), 1)
    survivor_count = sp.Rational(sum(row["occupied_survivor_count"] for row in rows), 1)
    return {
        "shell_count": str(shell_count),
        "survivor_count": str(survivor_count),
        "signature": common.shell_signature(rows),
        "pass": bool(
            shell_count == common.EXPECTED_SHELL_COUNT
            and survivor_count == common.EXPECTED_SURVIVOR_COUNT
            and common.shell_signature(rows) == common.EXPECTED_SHELL_SIGNATURE
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    flux = torch_flux_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and flux["finite"]
        and flux["max_holonomy_error"] <= 1e-12
        and flux["max_curvature_error"] <= 1e-12
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
            "torch.func": "vmap(observables)(eta) recomputes h(eta), F_eta_chi, and A_chi for occupied shells",
            "sympy": "sp.Rational guards exact shell count, survivor total, and shell occupation signature",
        },
        "reads_peer_result": False,
        "torch_flux_receipt": flux,
        "sympy_guard": exact,
        "survivor_count": payload["counts"]["survivor_count"],
        "shell_count": payload["counts"]["occupied_shell_count"],
        "shell_occupation_signature": payload["connection_flux_attachment"]["shell_occupation_signature"],
        "leakage_status": payload["leakage_analysis"]["status"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched shell flux observables"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact shell signature guard"},
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
