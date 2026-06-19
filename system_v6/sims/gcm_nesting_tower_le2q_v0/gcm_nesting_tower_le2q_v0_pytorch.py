#!/usr/bin/env python3
"""PyTorch lane for gcm_nesting_tower_le2q_v0."""

from __future__ import annotations

import importlib.metadata
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap

import gcm_nesting_tower_le2q_v0_common as common


ENGINE = "pytorch"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_{ENGINE}_results.json"
torch.set_default_dtype(torch.float64)


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"


def sign_tensor(values: torch.Tensor) -> torch.Tensor:
    return torch.where(values < 0, torch.full_like(values, -1), torch.where(values > 0, torch.ones_like(values), torch.zeros_like(values)))


def probe_signature_tensor(coords: torch.Tensor) -> torch.Tensor:
    return torch.stack([sign_tensor(coords[:, 0]), sign_tensor(coords[:, 2])], dim=1)


def registry_tensors(one_q: dict[str, Any], two_q: dict[str, Any]) -> dict[str, torch.Tensor]:
    one_coords = torch.tensor([row["coord_scaled"] for row in one_q["frozen_registry"]["survivors"]], dtype=torch.int64)
    two_rows = two_q["frozen_2q_registry"]["survivors"]
    a_coords = torch.tensor([row["first_bloch_scaled"] for row in two_rows], dtype=torch.int64)
    b_coords = torch.tensor([row["second_bloch_scaled"] for row in two_rows], dtype=torch.int64)
    product_mask = torch.tensor([row["family"] == "product_grid" for row in two_rows], dtype=torch.bool)
    entangled_mask = torch.tensor([bool(row["entangled"]) for row in two_rows], dtype=torch.bool)
    return {
        "one_coords": one_coords,
        "one_sig": probe_signature_tensor(one_coords),
        "a_coords": a_coords,
        "b_coords": b_coords,
        "a_sig": probe_signature_tensor(a_coords),
        "b_sig": probe_signature_tensor(b_coords),
        "product_mask": product_mask,
        "entangled_mask": entangled_mask,
    }


def compatibility_counts(one_q: dict[str, Any], two_q: dict[str, Any]) -> dict[str, int]:
    tensors = registry_tensors(one_q, two_q)
    one_coords = tensors["one_coords"]
    one_sig = tensors["one_sig"]

    def row_counts(a_coord: torch.Tensor, b_coord: torch.Tensor, a_sig: torch.Tensor, b_sig: torch.Tensor) -> torch.Tensor:
        a_exact = torch.sum(torch.all(one_coords == a_coord, dim=1).to(torch.int64))
        b_exact = torch.sum(torch.all(one_coords == b_coord, dim=1).to(torch.int64))
        a_probe = torch.sum(torch.all(one_sig == a_sig, dim=1).to(torch.int64))
        b_probe = torch.sum(torch.all(one_sig == b_sig, dim=1).to(torch.int64))
        exact_ok = ((a_exact > 0) & (b_exact > 0)).to(torch.int64)
        probe_ok = ((a_probe > 0) & (b_probe > 0)).to(torch.int64)
        probe_triples = a_probe * b_probe * probe_ok
        return torch.stack([exact_ok, probe_ok, probe_triples])

    per_row = vmap(row_counts)(tensors["a_coords"], tensors["b_coords"], tensors["a_sig"], tensors["b_sig"])
    exact_mask = per_row[:, 0].to(torch.bool)
    probe_mask = per_row[:, 1].to(torch.bool)
    product_exact = exact_mask & tensors["product_mask"]
    entangled_probe = probe_mask & tensors["entangled_mask"]
    return {
        "two_q_survivor_count": int(two_q["counts"]["survivor_count"]),
        "exact_tower_cardinality": int(torch.sum(exact_mask).item()),
        "exact_orphan_2q_count": int(torch.sum(~exact_mask).item()),
        "probe_compatible_2q_count": int(torch.sum(probe_mask).item()),
        "probe_orphan_2q_count": int(torch.sum(~probe_mask).item()),
        "probe_tower_cardinality": int(torch.sum(per_row[:, 2]).item()),
        "product_exact_subtower_count": int(torch.sum(product_exact).item()),
        "entangled_probe_compatible_2q_count": int(torch.sum(entangled_probe).item()),
        "max_probe_triples_per_row": int(torch.max(per_row[:, 2]).item()),
        "finite": bool(torch.isfinite(per_row.to(torch.float64)).all().item()),
    }


def sympy_guard(counts: dict[str, int]) -> dict[str, Any]:
    n2 = sp.Rational(counts["two_q_survivor_count"], 1)
    exact = sp.Rational(counts["exact_tower_cardinality"], 1)
    exact_orphans = sp.Rational(counts["exact_orphan_2q_count"], 1)
    probe = sp.Rational(counts["probe_compatible_2q_count"], 1)
    probe_orphans = sp.Rational(counts["probe_orphan_2q_count"], 1)
    product_exact = sp.Rational(counts["product_exact_subtower_count"], 1)
    return {
        "counts": {
            "two_q": str(n2),
            "exact": str(exact),
            "exact_orphans": str(exact_orphans),
            "probe": str(probe),
            "probe_orphans": str(probe_orphans),
            "product_exact": str(product_exact),
        },
        "pass": bool(
            n2 == common.EXPECTED_2Q_SURVIVOR_COUNT
            and exact == common.EXPECTED_EXACT_COMPATIBLE_2Q_COUNT
            and sp.simplify(exact + exact_orphans - n2) == 0
            and sp.simplify(probe + probe_orphans - n2) == 0
            and product_exact == common.EXPECTED_1Q_SURVIVOR_COUNT * common.EXPECTED_1Q_SURVIVOR_COUNT
        ),
    }


def build_result() -> dict[str, Any]:
    one_q = common.load_json(common.ONE_Q_REGISTRY_PATH)
    two_q = common.load_json(common.TWO_Q_REGISTRY_PATH)
    counts = compatibility_counts(one_q, two_q)
    exact = sympy_guard(counts)
    all_pass = bool(
        counts["finite"]
        and exact["pass"]
        and counts["entangled_probe_compatible_2q_count"] == common.EXPECTED_2Q_ENTANGLED_COUNT
        and counts["max_probe_triples_per_row"] == 4
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
            "torch.func": "vmap(row_counts)(A_coords, B_coords, A_probe_sigs, B_probe_sigs) computes exact/probe compatibility masks",
            "sympy": "sp.Rational exact guard for exact/probe compatible counts and orphan partitions",
        },
        "reads_peer_result": False,
        "torch_vmap_receipt": counts,
        "sympy_guard": exact,
        "exact_tower_cardinality": counts["exact_tower_cardinality"],
        "probe_tower_cardinality": counts["probe_tower_cardinality"],
        "probe_orphan_2q_count": counts["probe_orphan_2q_count"],
        "exact_orphan_2q_count": counts["exact_orphan_2q_count"],
        "product_exact_subtower_count": counts["product_exact_subtower_count"],
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing batched exact/probe compatibility masks"},
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact tower count identities"},
            "torch": {"tried": True, "used": True, "reason": "supportive tensor storage and boolean reductions"},
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
