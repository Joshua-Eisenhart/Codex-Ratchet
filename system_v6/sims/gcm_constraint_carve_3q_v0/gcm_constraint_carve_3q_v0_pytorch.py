#!/usr/bin/env python3
"""PyTorch lane for gcm_constraint_carve_3q_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import gcm_constraint_carve_3q_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)

CLASSIFICATION = common.CLASSIFICATION
TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive tensor storage and reductions"},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched finite survivor predicate observables"},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact count/CKW rational guard"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "supportive", "torch.func": "load_bearing", "sympy": "load_bearing"}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_func_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    coords = torch.tensor([row["first_bloch"] for row in payload["survivors"]], dtype=torch.float64)

    def observables(coord: torch.Tensor) -> torch.Tensor:
        active_probe_norm = torch.abs(coord[0]) + torch.abs(coord[2])
        order_gap_proxy = torch.abs(coord[1]) * 2.0
        return torch.stack([active_probe_norm, order_gap_proxy])

    values = vmap(observables)(coords)
    return {
        "coord_shape": list(coords.shape),
        "observable_shape": list(values.shape),
        "min_active_probe_norm": round(float(torch.min(values[:, 0]).item()), 12),
        "min_order_gap_proxy": round(float(torch.min(values[:, 1]).item()), 12),
        "finite": bool(torch.isfinite(values).all().item()),
        "all_probe_active": bool(torch.all(values[:, 0] > 0.0).item()),
        "all_order_gap_active": bool(torch.all(values[:, 1] >= 0.5 - 1.0e-12).item()),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    ckw = payload["monogamy_ckw_row"]["rows"][0]
    margin = sp.Rational(str(ckw["ckw_margin"]))
    return {
        "survivor_count": str(sp.Rational(payload["survivor_count"], 1)),
        "quotient_class_count": str(sp.Rational(payload["quotient"]["class_count"], 1)),
        "ckw_margin": str(margin),
        "pass": bool(margin == sp.Rational(3, 16)),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    torch_receipt = torch_func_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(payload["all_pass"] and torch_receipt["all_probe_active"] and torch_receipt["all_order_gap_active"] and torch_receipt["finite"] and exact["pass"])
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
            "torch.func": "vmap(observables)(first_bloch_coords) checks active probes and order-gap proxy over survivors",
            "sympy": "sp.Rational exact survivor/quotient/CKW margin guard",
        },
        "reads_peer_result": False,
        "torch_func_receipt": torch_receipt,
        "sympy_guard": exact,
        "survivor_count": payload["survivor_count"],
        "quotient_class_count": payload["quotient"]["class_count"],
        "ckw_survivor_count": payload["monogamy_ckw_row"]["survivor_count_checked"],
        "floor_carrier": payload["floor_rows"]["cl6_structure_carried_by_survivors"]["carrier"],
        "all_pass": all_pass,
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
