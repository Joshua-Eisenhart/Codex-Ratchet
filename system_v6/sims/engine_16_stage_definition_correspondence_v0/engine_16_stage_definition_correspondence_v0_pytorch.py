#!/usr/bin/env python3
"""PyTorch lane for engine_16_stage_definition_correspondence_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import engine_16_stage_definition_correspondence_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "supportive tensor materialization for explicit stage matrices."},
    "torch.func": {"tried": True, "used": True, "reason": "load-bearing vmap application of all 16 maps to the carrier vector."},
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact 16x16 matrix dimension and discovered-count guard."},
}
TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
}


def torch_func_receipt(payload: dict[str, Any]) -> dict[str, Any]:
    matrices = torch.tensor([row["matrix_bloch_3x3"] for row in payload["defined_stage_rows"]], dtype=torch.float64)
    bloch = torch.tensor(payload["defined_stage_rows"][0]["bloch_input"], dtype=torch.float64)

    def apply_one(matrix: torch.Tensor) -> torch.Tensor:
        return matrix @ bloch

    outputs = vmap(apply_one)(matrices)
    expected = torch.tensor([row["bloch_output"] for row in payload["defined_stage_rows"]], dtype=torch.float64)
    max_delta = torch.max(torch.abs(outputs - expected)).item()
    return {
        "matrix_tensor_shape": list(matrices.shape),
        "output_tensor_shape": list(outputs.shape),
        "max_abs_delta_vs_common": round(float(max_delta), 12),
        "pass": bool(max_delta <= 1.0e-10),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    matrix = payload["correspondence"]["match_matrix_16x16"]
    rows = sp.Rational(len(matrix), 1)
    cols = sp.Rational(len(matrix[0]), 1)
    discovered = sp.Rational(payload["correspondence"]["discovered_component_count"], 1)
    stage_count = sp.Rational(len(payload["defined_stage_rows"]), 1)
    return {
        "stage_count": str(stage_count),
        "match_rows": str(rows),
        "match_cols": str(cols),
        "discovered_count": str(discovered),
        "pass": bool(stage_count == 16 and rows == 16 and cols == 16 and discovered == 16),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    torch_receipt = torch_func_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(payload["all_pass"] and torch_receipt["pass"] and exact["pass"])
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
        "package_versions": {"torch": torch.__version__, "sympy": common.package_version("sympy")},
        "package_observables": {
            "torch.func": "vmap over the 16 explicit 3x3 stage matrices applied to the representative Bloch vector",
            "sympy": "sp.Rational exact guard for 16 stage rows, 16 discovered rows, and 16x16 matrix shape",
        },
        "reads_peer_result": False,
        "torch_func_receipt": torch_receipt,
        "sympy_guard": exact,
        "computed_values": {
            "stage_count": len(payload["defined_stage_rows"]),
            "defined_distinct_component_count": payload["summary"]["defined_distinct_component_count"],
            "discovered_component_count": payload["summary"]["discovered_component_count"],
            "exact_matched_component_count": payload["summary"]["exact_matched_component_count"],
            "perfect_bijection": payload["summary"]["perfect_bijection"],
            "normal_component_ids": [row["component_id"] for row in payload["defined_stage_rows"]],
            "match_matrix_sha256": common.stable_sha256(payload["correspondence"]["match_matrix_16x16"]),
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
