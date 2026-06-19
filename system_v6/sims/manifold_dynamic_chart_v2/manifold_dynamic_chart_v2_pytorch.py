#!/usr/bin/env python3
"""PyTorch lane for manifold_dynamic_chart_v2."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import manifold_dynamic_chart_v2_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor source for density-state coordinate checks and common entropy path.",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing batched Bloch-radius/density validity observable over all state rows.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact row-count guard for 33*(T+1) state rows.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
}


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def torch_func_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    coords = torch.tensor([row["coord"] for row in payload["state_rows"]], dtype=torch.float64)

    def radius_squared(coord: torch.Tensor) -> torch.Tensor:
        return torch.sum(coord * coord)

    radii = vmap(radius_squared)(coords)
    return {
        "state_row_count": int(coords.shape[0]),
        "coord_shape": list(coords.shape),
        "max_radius_squared": round(float(torch.max(radii).item()), 12),
        "all_inside_bloch_ball": bool(torch.all(radii <= 1.0 + 1.0e-9).item()),
        "finite": bool(torch.isfinite(radii).all().item()),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    expected = sp.Rational(common.EXPECTED_STATE_COUNT, 1) * sp.Rational(payload["trajectory"]["T"] + 1, 1)
    actual = sp.Rational(len(payload["state_rows"]), 1)
    return {
        "expected_state_rows": str(expected),
        "actual_state_rows": str(actual),
        "pass": sp.simplify(expected - actual) == 0,
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    artifact = common.write_trajectory_artifact(payload)
    arrays = common.cells_and_entropy_by_t(payload)
    torch_receipt = torch_func_receipt(payload)
    exact_guard = sympy_guard(payload)
    all_pass = bool(payload["all_pass"] and artifact["sha_verified"] and torch_receipt["all_inside_bloch_ball"] and exact_guard["pass"])
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
            "torch.func": "vmap(radius_squared)(coords) over all density-state trajectory rows",
            "sympy": "sp.Rational exact equality len(state_rows)=33*(T+1)",
        },
        "reads_peer_result": False,
        "torch_func_receipt": torch_receipt,
        "sympy_guard": exact_guard,
        "computed_values": {
            "state_count": payload["carrier"]["state_count"],
            "trajectory_T": payload["trajectory"]["T"],
            "state_row_count": len(payload["state_rows"]),
            "cells_by_t": arrays["cells_by_t"],
            "entropy_by_t": arrays["entropy_by_t"],
            "trajectory_signature_sha256": payload["trajectory"]["trajectory_signature_sha256"],
            "entropy_signature_sha256": payload["trajectory"]["entropy_signature_sha256"],
            "shell_signature_sha256": payload["trajectory"]["shell_signature_sha256"],
            "jk_signature_sha256": payload["trajectory"]["jk_signature_sha256"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "all_pass": all_pass,
    }
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"ok": all_pass, "result": common.rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return result


def main() -> int:
    result = build_result()
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
