#!/usr/bin/env python3
"""PyTorch lane for gcm_constraint_carve_2q_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import gcm_constraint_carve_2q_v0_common as common


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
    first = torch.tensor([row["first_bloch"] for row in payload["survivors"]], dtype=torch.float64)

    def observables(coord: torch.Tensor) -> torch.Tensor:
        active_probe_norm = torch.abs(coord[0]) + torch.abs(coord[2])
        left_z = coord[1]
        right_z = 0.5 * coord[1]
        order_gap_proxy = torch.abs(left_z - right_z) * 2.0
        first_active_positive = torch.where(coord[0] != 0.0, coord[0] > 0.0, coord[2] > 0.0).to(torch.float64)
        return torch.stack([active_probe_norm, order_gap_proxy, first_active_positive])

    values = vmap(observables)(first)
    entangled = torch.tensor([1 if row["entangled"] else 0 for row in payload["survivors"]], dtype=torch.int64)
    return {
        "coord_shape": list(first.shape),
        "observable_shape": list(values.shape),
        "min_active_probe_norm": round(float(torch.min(values[:, 0]).item()), 12),
        "min_order_gap_proxy": round(float(torch.min(values[:, 1]).item()), 12),
        "mct_positive_active_count": int(torch.sum(values[:, 2]).item()),
        "entangled_survivor_count": int(torch.sum(entangled).item()),
        "all_probe_active": bool(torch.all(values[:, 0] > 0.0).item()),
        "all_order_gap_active": bool(torch.all(values[:, 1] >= 0.5 - 1.0e-12).item()),
        "finite": bool(torch.isfinite(values).all().item()),
    }


def sympy_guard(payload: dict[str, Any]) -> dict[str, Any]:
    counts = {
        "candidate": sp.Rational(payload["candidate_space"]["candidate_count"], 1),
        "density": sp.Rational(payload["candidate_space"]["density_subcarrier_count"], 1),
        "survivor": sp.Rational(payload["survivor_count"], 1),
        "quotient": sp.Rational(payload["quotient"]["class_count"], 1),
        "embedded_1q": sp.Rational(payload["cross_rung_lineage_row"]["product_control_embedding_count"], 1),
        "entangled_survivor": sp.Rational(payload["entangled_survivor_count"], 1),
    }
    return {
        "counts": {key: str(value) for key, value in counts.items()},
        "pass": bool(
            counts["candidate"] == common.EXPECTED_CANDIDATE_COUNT
            and counts["density"] == common.EXPECTED_DENSITY_COUNT
            and counts["survivor"] == common.EXPECTED_SURVIVOR_COUNT
            and counts["quotient"] == common.EXPECTED_QUOTIENT_CLASS_COUNT
            and counts["embedded_1q"] == common.EXPECTED_ONE_Q_SURVIVOR_COUNT
            and counts["entangled_survivor"] == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    payload = common.build_packet()
    torch_receipt = torch_func_receipt(payload)
    exact = sympy_guard(payload)
    all_pass = bool(
        payload["all_pass"]
        and torch_receipt["all_probe_active"]
        and torch_receipt["all_order_gap_active"]
        and torch_receipt["finite"]
        and torch_receipt["mct_positive_active_count"] == common.EXPECTED_MCT_SURVIVOR_COUNT
        and torch_receipt["entangled_survivor_count"] == common.EXPECTED_ENTANGLED_SURVIVOR_COUNT
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
            "torch.func": "vmap(observables)(first_marginal_coords) checks active probes, order-gap proxy, M(C,t), and entangled survivor count",
            "sympy": "sp.Rational exact 2Q candidate/density/survivor/quotient/cross-rung count guard",
        },
        "reads_peer_result": False,
        "torch_func_receipt": torch_receipt,
        "sympy_guard": exact,
        "survivor_count": payload["survivor_count"],
        "quotient_class_count": payload["quotient"]["class_count"],
        "component_count": len(payload["adjacency_connectivity"]["survivor_components"]),
        "entangled_survivor_count": payload["entangled_survivor_count"],
        "embedded_1q_count": payload["cross_rung_lineage_row"]["product_control_embedding_count"],
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
