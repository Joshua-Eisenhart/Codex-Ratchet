#!/usr/bin/env python3
"""Focused audit for the current JAX G-structure, entropy, and operator lanes.

This reads receipt JSONs only. It does not run Julia, PyTorch, or promote any
layer. The point is to bind three focused families into one fenced receipt:
G-structure candidates, finite QIT/entropy readouts, and noncommuting operator
order readouts.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


RESULT_DIR = Path("system_v5/ops/formal_scouts/results")
OUT_DIR = Path("system_v5/ops/wizard_admissions")

REQUIRED_BLOCKS = {
    "full_layer_completion",
    "official_g_structure_selection",
    "layer_stacking",
    "flux",
    "Axis0",
    "FEP",
    "final_manifold_admission",
}

ALIASES = {
    "full layer completion": "full_layer_completion",
    "layer_completion": "full_layer_completion",
    "official G-structure selection": "official_g_structure_selection",
    "layer_stacking_readiness": "layer_stacking",
    "layer stacking readiness": "layer_stacking",
    "layer_embedding": "layer_stacking",
    "stacking": "layer_stacking",
    "Holodeck/FEP": "FEP",
    "physics": "physics_gravity",
    "physics/gravity": "physics_gravity",
    "final_manifold": "final_manifold_admission",
    "final manifold": "final_manifold_admission",
    "final manifold admission": "final_manifold_admission",
}

FOCUS_RECEIPTS = {
    "g_structure": [
        "jax_native_geometry_su2_spin3_unit_quaternion_double_cover_probe_results.json",
        "jax_native_geometry_so3_orientation_frame_reduction_probe_results.json",
        "jax_native_geometry_pin3_spin3_chirality_split_probe_results.json",
        "jax_native_geometry_clifford_geometries_cl3_cl6_probe_results.json",
        "jax_native_geometry_spin_c_structure_probe_results.json",
    ],
    "entropy_qit": [
        "jax_native_l6_entropy_cut_communication_layer_probe_results.json",
        "jax_weyl_terrain_joint_rho_ab_qit_diagnostic_results.json",
    ],
    "operators_order": [
        "jax_native_l5_operator_substage_cell_layer_probe_results.json",
        "jax_l4_l5_order_commutator_finitude_ratchet_probe_results.json",
        "jax_density_operator_terrain_signed_commutator_probe_results.json",
        "jax_density_operator_integrated_layer_nesting_order_probe_results.json",
    ],
}

REQUIRED_FAMILY_TOKENS = {
    "g_structure": ["su2", "so3", "pin3", "clifford", "spin_c"],
    "entropy_qit": ["l6_entropy", "joint_rho_ab"],
    "operators_order": ["l5_operator", "l4_l5_order", "density_operator_terrain", "integrated_layer_nesting_order"],
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_ok(d: dict[str, Any]) -> bool:
    if "AUDIT_PASS" in d:
        return bool(d["AUDIT_PASS"])
    if "all_pass" in d:
        return bool(d["all_pass"])
    if d.get("status") in {"pass", "passed", "passes"}:
        return True
    return False


def normalize_blocks(value: Any) -> set[str]:
    out: set[str] = set()
    for raw in value or []:
        s = str(raw)
        out.add(ALIASES.get(s, s))
    return out


def receipt_blocks(d: dict[str, Any]) -> set[str]:
    blocks = normalize_blocks(d.get("blocked_consumers") or d.get("blocked_claims"))
    summary = d.get("summary")
    if isinstance(summary, dict):
        blocks |= normalize_blocks(summary.get("blocked_consumers"))
    boundary = d.get("boundary")
    if isinstance(boundary, dict):
        locked = boundary.get("downstream_consumers_locked")
        if isinstance(locked, dict):
            blocks |= normalize_blocks(locked.get("blocked_consumers"))
    return blocks


def token_for(name: str) -> str:
    if "su2_spin3" in name:
        return "su2"
    if "so3_orientation" in name:
        return "so3"
    if "pin3_spin3" in name:
        return "pin3"
    if "clifford_geometries" in name:
        return "clifford"
    if "spin_c_structure" in name:
        return "spin_c"
    if "l6_entropy" in name:
        return "l6_entropy"
    if "joint_rho_ab" in name:
        return "joint_rho_ab"
    if "l5_operator" in name:
        return "l5_operator"
    if "l4_l5_order" in name:
        return "l4_l5_order"
    if "density_operator_terrain" in name:
        return "density_operator_terrain"
    if "integrated_layer_nesting_order" in name:
        return "integrated_layer_nesting_order"
    return "unknown"


def main() -> int:
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    tokens_by_family: dict[str, set[str]] = {family: set() for family in FOCUS_RECEIPTS}

    for family, names in FOCUS_RECEIPTS.items():
        for name in names:
            path = RESULT_DIR / name
            row: dict[str, Any] = {
                "family": family,
                "receipt": str(path),
                "exists": path.exists(),
                "token": token_for(name),
            }
            if not path.exists():
                rows.append(row)
                failures.append({"receipt": str(path), "reason": "missing_receipt"})
                continue

            d = load(path)
            blocks = receipt_blocks(d)
            row.update(
                {
                    "classification": d.get("classification"),
                    "sim_id": d.get("sim_id"),
                    "result_ok": result_ok(d),
                    "promotion_allowed": d.get("promotion_allowed"),
                    "formal_admission_allowed": d.get("formal_admission_allowed"),
                    "ran_julia": d.get("ran_julia"),
                    "ran_pytorch": d.get("ran_pytorch"),
                    "required_blocks_present": REQUIRED_BLOCKS <= blocks,
                    "normalized_blocked_consumers": sorted(blocks),
                }
            )
            rows.append(row)
            tokens_by_family[family].add(str(row["token"]))

            if not row["result_ok"]:
                failures.append({"receipt": str(path), "reason": "result_not_green"})
            if row["promotion_allowed"] is not False:
                failures.append({"receipt": str(path), "reason": "promotion_not_false"})
            if row["formal_admission_allowed"] is not False:
                failures.append({"receipt": str(path), "reason": "formal_admission_not_false"})
            if row["ran_julia"] is not False:
                failures.append({"receipt": str(path), "reason": "ran_julia_not_false"})
            if row["ran_pytorch"] is not False:
                failures.append({"receipt": str(path), "reason": "ran_pytorch_not_false"})
            if not row["required_blocks_present"]:
                failures.append(
                    {
                        "receipt": str(path),
                        "reason": "missing_required_blocks",
                        "have": row["normalized_blocked_consumers"],
                    }
                )

    family_checks: dict[str, dict[str, Any]] = {}
    for family, required in REQUIRED_FAMILY_TOKENS.items():
        have = tokens_by_family.get(family, set())
        missing = sorted(set(required) - have)
        family_checks[family] = {
            "required_tokens": required,
            "observed_tokens": sorted(have),
            "missing_tokens": missing,
            "pass": not missing,
        }
        if missing:
            failures.append({"family": family, "reason": "missing_required_family_tokens", "missing": missing})

    out = {
        "kind": "jax_gstructure_entropy_operator_focus_audit",
        "classification": "admission_boundary_audit",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "Focused JAX-only receipt audit for G-structure, finite QIT/entropy, and operator/order lanes.",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "allowed_claim": "Focused families have green JAX diagnostic/formal-scout receipts and remain fenced below admission.",
        "not_claimed": [
            "full layer completion",
            "official G-structure selection",
            "layer stacking readiness",
            "noncommutative ordering admission",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "physics/gravity",
            "final manifold admission",
        ],
        "blocked_consumers": [
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking",
            "layer_stacking_readiness",
            "noncommutative_layer_order_claim",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "checks": {
            "all_receipts_green_or_passed": all(bool(row.get("result_ok")) for row in rows),
            "all_promotion_blocked": all(row.get("promotion_allowed") is False for row in rows),
            "all_formal_admission_blocked": all(row.get("formal_admission_allowed") is False for row in rows),
            "all_julia_false": all(row.get("ran_julia") is False for row in rows),
            "all_pytorch_false": all(row.get("ran_pytorch") is False for row in rows),
            "all_required_blocks_present": all(bool(row.get("required_blocks_present")) for row in rows),
            "family_tokens_complete": all(check["pass"] for check in family_checks.values()),
            "no_completion_claim_made": True,
        },
        "family_checks": family_checks,
        "rows": rows,
        "failures": failures,
        "AUDIT_PASS": not failures,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"jax_gstructure_entropy_operator_focus_audit_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"gstructure_entropy_operator_focus AUDIT_PASS={out['AUDIT_PASS']} rows={len(rows)} failures={len(failures)} path={out_path}")
    return 0 if out["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
