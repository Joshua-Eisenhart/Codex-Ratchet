#!/usr/bin/env python3
"""PyTorch lane for gcm_constraint_carve_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import gcm_constraint_carve_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_func_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    coords = torch.tensor([row["coord"] for row in payload["survivors"]], dtype=torch.float64)

    def observables(coord: torch.Tensor) -> torch.Tensor:
        radius = torch.sum(coord * coord)
        probe_norm = torch.abs(coord[0]) + torch.abs(coord[2])
        order_gap = torch.abs(coord[1])
        return torch.stack([radius, probe_norm, order_gap])

    values = vmap(observables)(coords)
    return {
        "coord_shape": list(coords.shape),
        "observable_shape": list(values.shape),
        "max_radius_squared": round(float(torch.max(values[:, 0]).item()), 12),
        "min_active_probe_norm": round(float(torch.min(values[:, 1]).item()), 12),
        "min_order_gap_proxy": round(float(torch.min(values[:, 2]).item()), 12),
        "all_density_valid": bool(torch.all(values[:, 0] <= 1.0 + 1.0e-12).item()),
        "all_probe_active": bool(torch.all(values[:, 1] > 0.0).item()),
        "all_order_gap_active": bool(torch.all(values[:, 2] >= 0.5 - 1.0e-12).item()),
        "finite": bool(torch.isfinite(values).all().item()),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    counts = {
        "candidate": sp.Rational(payload["candidate_space"]["candidate_count"], 1),
        "density": sp.Rational(payload["candidate_space"]["density_subcarrier_count"], 1),
        "survivor": sp.Rational(payload["survivor_count"], 1),
        "quotient": sp.Rational(payload["quotient"]["class_count"], 1),
    }
    return {
        "counts": {key: str(value) for key, value in counts.items()},
        "pass": bool(
            counts["candidate"] == common.EXPECTED_CANDIDATE_COUNT
            and counts["density"] == common.EXPECTED_DENSITY_COUNT
            and counts["survivor"] == common.EXPECTED_SURVIVOR_COUNT
            and counts["quotient"] == common.EXPECTED_QUOTIENT_CLASS_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    torch_receipt = torch_func_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and torch_receipt["all_density_valid"]
        and torch_receipt["all_probe_active"]
        and torch_receipt["all_order_gap_active"]
        and torch_receipt["finite"]
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
            "torch.func": "vmap(observables)(coords) checks density radius, active probes, and order-gap proxy",
            "sympy": "sp.Rational exact candidate/density/survivor/quotient count guard",
        },
        "reads_peer_result": False,
        "torch_func_receipt": torch_receipt,
        "sympy_guard": exact,
        "survivor_count": payload["survivor_count"],
        "quotient_class_count": payload["quotient"]["class_count"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched finite survivor observable"},
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
