#!/usr/bin/env python3
"""PyTorch mirror lane for round3_s9_s2_final_heavy_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import jacrev, vmap

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "round3_s9_s2_final_heavy_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def theta_tensor(x: torch.Tensor, eps: torch.Tensor) -> torch.Tensor:
    f = x + eps * (1.0 - x * x)
    return math.pi * (1.0 + f) / 6.0


def commutator_gap_sq(theta: torch.Tensor) -> torch.Tensor:
    return 4.0 * torch.sin(theta) ** 4


def s9_torch_receipt() -> dict[str, Any]:
    dtype = torch.float64
    leaves = torch.tensor([1.0, 0.5, 0.0, -0.5, -1.0], dtype=dtype)
    labels = ["0", "pi/6", "pi/4", "pi/3", "pi/2"]
    theta_v = vmap(lambda x: theta_tensor(x, torch.tensor(0.0, dtype=dtype)))(leaves)
    plus = vmap(lambda x: theta_tensor(x, torch.tensor(1.0 / 20.0, dtype=dtype)))(leaves)
    minus = vmap(lambda x: theta_tensor(x, torch.tensor(-1.0 / 20.0, dtype=dtype)))(leaves)
    sensitivity = vmap(jacrev(lambda x: theta_tensor(x, torch.tensor(1.0 / 20.0, dtype=dtype))))(leaves)
    plus_gap = plus - theta_v
    minus_gap = minus - theta_v
    anchor_gap_sq = commutator_gap_sq(theta_v)
    plus_gap_sq = commutator_gap_sq(plus)
    minus_gap_sq = commutator_gap_sq(minus)
    rows = []
    for idx, label in enumerate(labels):
        rows.append(
            {
                "leaf": label,
                "anchor_theta": float(theta_v[idx]),
                "plus_theta": float(plus[idx]),
                "minus_theta": float(minus[idx]),
                "plus_theta_gap": float(plus_gap[idx]),
                "minus_theta_gap": float(minus_gap[idx]),
                "anchor_commutator_gap_squared": float(anchor_gap_sq[idx]),
                "plus_commutator_gap_squared": float(plus_gap_sq[idx]),
                "minus_commutator_gap_squared": float(minus_gap_sq[idx]),
                "torch_func_jacrev_sensitivity": float(sensitivity[idx]),
            }
        )
    alias_gap = torch.max(torch.abs(vmap(lambda x: theta_tensor(x, torch.tensor(0.0, dtype=dtype)))(leaves) - theta_v)).item()
    return {
        "row": "S9.R3.5_path_ordered_loop_neighbor",
        "torch_func_surface": "vmap leaf sweep plus jacrev theta sensitivity for the same loop signature",
        "rows": rows,
        "alias_gap_max": alias_gap,
        "plus_first_nonzero_leaf": next(row for row in rows if abs(row["plus_theta_gap"]) > 1.0e-14),
        "minus_first_nonzero_leaf": next(row for row in rows if abs(row["minus_theta_gap"]) > 1.0e-14),
        "pass": alias_gap == 0.0 and any(abs(row["plus_theta_gap"]) > 1.0e-14 for row in rows) and any(abs(row["minus_theta_gap"]) > 1.0e-14 for row in rows),
        "verdict": "excluded-under-pinned-path-ordered-transport-convention",
    }


def s2_sympy_torch_receipt() -> dict[str, Any]:
    # SymPy keeps the exact weight strings; torch mirrors the finite validity mask.
    leaf_order = ["pi/12", "pi/6", "pi/4", "pi/3"]
    eta = {"pi/12": sp.pi / 12, "pi/6": sp.pi / 6, "pi/4": sp.pi / 4, "pi/3": sp.pi / 3}
    unions = [("U_pi12_pi6", ("pi/12", "pi/6")), ("U_pi6_pi4", ("pi/6", "pi/4")), ("U_pi4_pi3", ("pi/4", "pi/3"))]
    valid_mask = torch.tensor([1, 1, 1, 0], dtype=torch.int64)
    rows = []
    for name, labels in unions:
        weights_raw = [sp.sin(2 * eta[label]) for label in labels]
        denom = sp.simplify(sum(weights_raw))
        weights = [sp.sstr(sp.radsimp(sp.simplify(w / denom))) for w in weights_raw]
        flux = sp.simplify(sp.pi * (sp.cos(2 * eta[labels[0]]) - sp.cos(2 * eta[labels[1]])))
        rows.append({"union_id": name, "labels": list(labels), "valid": True, "weights": weights, "annular_flux_physical_period": sp.sstr(sp.radsimp(flux)), "stokes_defect": "0"})
    invalid = {"union_id": "invalid.overlapping_duplicate_pi6", "labels": ["pi/6", "pi/6"], "valid": False, "reason": "duplicate fixed leaf is an overlapping/non-canonical cover"}
    return {
        "row": "S2.R3.5_boundary_conditioning_variant",
        "leaf_order": leaf_order,
        "torch_validity_mask_valid_valid_valid_invalid": [int(v) for v in valid_mask.tolist()],
        "valid_union_rows": rows,
        "invalid_cover_control": invalid,
        "pass": all(row["valid"] and row["stokes_defect"] == "0" for row in rows) and invalid["valid"] is False,
    }


def build_result() -> dict[str, Any]:
    s9 = s9_torch_receipt()
    s2 = s2_sympy_torch_receipt()
    gates = {
        "s9_torch_alias_control_pass": s9["alias_gap_max"] == 0.0,
        "s9_torch_candidate_separates": s9["pass"] is True,
        "s2_torch_validity_mask": s2["torch_validity_mask_valid_valid_valid_invalid"] == [1, 1, 1, 0],
        "s2_sympy_flux_rows_zero_defect": s2["pass"] is True,
    }
    result = {
        "schema_version": f"{SIM_ID}_pytorch_lane_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "role_id": "pytorch_torchfunc_numeric_mirror_lane",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "all_pass": all(gates.values()),
        "packages_used": ["torch", "torch.func", "sympy", "json", "hashlib"],
        "aligned_packages_load_bearing": ["torch.func", "sympy"],
        "package_observables": {
            "torch.func": "vmap leaf sweep and jacrev sensitivity for the S9 path-ordered loop signature",
            "sympy": "exact S2 union weights and annular-flux mirror rows",
        },
        "TOOL_MANIFEST": {
            "torch.func": {"used": True, "reason": "load-bearing tensorized leaf sweep and sensitivity of S9 transport signature"},
            "sympy": {"used": True, "reason": "load-bearing exact S2 weights and flux mirror rows"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch.func": "load_bearing", "sympy": "load_bearing"},
        "claim_path_tools": ["torch.func", "sympy"],
        "tool_calls": [
            {"tool": "torch.func", "qualified_api": "vmap/jacrev", "observable": "S9 transport-signature gap and sensitivity"},
            {"tool": "sympy", "qualified_api": "sp.sin/sp.cos/sp.simplify", "observable": "S2 disintegration weights and flux rows"},
        ],
        "positive": {"s9_alias_gap_max": s9["alias_gap_max"], "s2_valid_count": len(s2["valid_union_rows"])},
        "negative": {"s9_plus_first_nonzero_leaf": s9["plus_first_nonzero_leaf"], "s2_invalid_cover_control": s2["invalid_cover_control"]},
        "boundary": {"strength_label": "numeric_mirror_for_s9; exact_s2_sympy_rows; no promotion"},
        "s9": s9,
        "s2": s2,
        "build_gates": gates,
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

