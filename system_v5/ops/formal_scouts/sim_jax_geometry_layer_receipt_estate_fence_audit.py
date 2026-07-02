#!/usr/bin/env python3
"""Fence audit for the current JAX geometry/layer receipt estate.

This audit reads receipt JSONs only. It does not run Julia, PyTorch, or any
scientific sim. Its job is to make the current JAX geometry/layer evidence
explicitly visible as diagnostic/formal-scout evidence and to catch receipts
whose no-promotion/no-admission fence is still implicit.
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
    "layer_embedding": "layer_stacking",
    "stacking": "layer_stacking",
    "layer_stacking_readiness": "layer_stacking",
    "physics": "physics_gravity",
    "physics/gravity": "physics_gravity",
    "final_manifold": "final_manifold_admission",
    "final manifold": "final_manifold_admission",
    "official G-structure selection": "official_g_structure_selection",
    "full layer completion": "full_layer_completion",
    "Holodeck/FEP": "FEP",
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
        s = ALIASES.get(str(raw), str(raw))
        out.add(s)
    return out


def blocks_from_receipt(d: dict[str, Any]) -> set[str]:
    blocks = normalize_blocks(d.get("blocked_consumers") or d.get("blocked_claims"))
    for key in ("boundary", "controls"):
        section = d.get(key)
        if isinstance(section, dict):
            locked = section.get("downstream_consumers_locked")
            if isinstance(locked, dict):
                blocks |= normalize_blocks(locked.get("blocked_consumers"))
    if isinstance(d.get("summary"), dict):
        blocks |= normalize_blocks(d["summary"].get("blocked_consumers"))
    return blocks


def family_for(path: Path) -> str:
    name = path.name
    if name.startswith("jax_native_geometry_"):
        return "native_geometry"
    if name.startswith("jax_native_l"):
        return "native_layer"
    return "selected_diagnostic"


def main() -> int:
    receipt_paths = sorted(RESULT_DIR.glob("jax_native_geometry_*_probe_results.json"))
    receipt_paths += sorted(RESULT_DIR.glob("jax_native_l*_layer_probe_results.json"))
    receipt_paths += [
        RESULT_DIR / "jax_l4_l5_order_commutator_finitude_ratchet_probe_results.json",
        RESULT_DIR / "jax_nested_hopf_leaf_area_order_ratchet_probe_results.json",
        RESULT_DIR / "jax_radial_dirac_interleaf_coupling_probe_results.json",
        RESULT_DIR / "jax_emergent_basin_nested_terrains_probe_results.json",
        RESULT_DIR / "jax_weyl_terrain_joint_rho_ab_qit_diagnostic_results.json",
    ]
    receipt_paths = sorted(dict.fromkeys(receipt_paths))

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for path in receipt_paths:
        row: dict[str, Any] = {
            "path": str(path),
            "family": family_for(path),
            "exists": path.exists(),
        }
        if not path.exists():
            row["result_ok"] = False
            rows.append(row)
            failures.append({"path": str(path), "reason": "missing_receipt"})
            continue

        d = load(path)
        blocks = blocks_from_receipt(d)
        row.update(
            {
                "sim_id": d.get("sim_id"),
                "classification": d.get("classification"),
                "result_ok": result_ok(d),
                "promotion_allowed": d.get("promotion_allowed"),
                "formal_admission_allowed": d.get("formal_admission_allowed"),
                "ran_julia": d.get("ran_julia"),
                "ran_pytorch": d.get("ran_pytorch"),
                "required_blocks_present": REQUIRED_BLOCKS <= blocks,
                "normalized_blocked_consumers": sorted(blocks),
                "explicit_runtime_flags_present": "ran_julia" in d and "ran_pytorch" in d,
                "explicit_formal_fence_present": "formal_admission_allowed" in d,
            }
        )
        rows.append(row)

        if not row["result_ok"]:
            failures.append({"path": str(path), "reason": "result_not_green"})
        if row["promotion_allowed"] is not False:
            failures.append({"path": str(path), "reason": "promotion_not_false"})
        if row["formal_admission_allowed"] is True:
            failures.append({"path": str(path), "reason": "formal_admission_true"})
        if row["ran_julia"] is True:
            failures.append({"path": str(path), "reason": "ran_julia_true"})
        if row["ran_pytorch"] is True:
            failures.append({"path": str(path), "reason": "ran_pytorch_true"})
        if not row["required_blocks_present"]:
            failures.append(
                {
                    "path": str(path),
                    "reason": "missing_required_blocks",
                    "have": row["normalized_blocked_consumers"],
                }
            )
        if not row["explicit_formal_fence_present"]:
            failures.append({"path": str(path), "reason": "formal_admission_flag_missing"})
        if not row["explicit_runtime_flags_present"]:
            failures.append({"path": str(path), "reason": "runtime_lane_flags_missing"})

    by_family: dict[str, dict[str, int]] = {}
    for row in rows:
        fam = str(row["family"])
        bucket = by_family.setdefault(fam, {"rows": 0, "green": 0, "missing_formal_flag": 0, "missing_runtime_flags": 0})
        bucket["rows"] += 1
        bucket["green"] += int(bool(row.get("result_ok")))
        bucket["missing_formal_flag"] += int(not bool(row.get("explicit_formal_fence_present")))
        bucket["missing_runtime_flags"] += int(not bool(row.get("explicit_runtime_flags_present")))

    out = {
        "kind": "jax_geometry_layer_receipt_estate_fence_audit",
        "classification": "admission_boundary_audit",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "JAX-native geometry probes, L0-L8 layer probes, and selected post-nesting diagnostic scouts.",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "allowed_claim": "Receipt-estate fence audit only; green rows remain diagnostic/formal-scout evidence.",
        "blocked_consumers": [
            "full_layer_completion",
            "official_g_structure_selection",
            "layer_stacking",
            "layer_stacking_readiness",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "physics_gravity",
            "final_manifold_admission",
        ],
        "blocked_claims": [
            "full layer completion",
            "official G-structure selection",
            "layer stacking readiness",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "FEP",
            "physics/gravity",
            "final manifold admission",
        ],
        "families": by_family,
        "checks": {
            "all_receipts_green_or_passed": all(bool(row.get("result_ok")) for row in rows),
            "all_promotion_blocked": all(row.get("promotion_allowed") is False for row in rows),
            "no_formal_admission_true": all(row.get("formal_admission_allowed") is not True for row in rows),
            "no_runtime_lane_true": all(row.get("ran_julia") is not True and row.get("ran_pytorch") is not True for row in rows),
            "all_required_blocks_present": all(bool(row.get("required_blocks_present")) for row in rows),
            "all_formal_flags_explicit": all(bool(row.get("explicit_formal_fence_present")) for row in rows),
            "all_runtime_flags_explicit": all(bool(row.get("explicit_runtime_flags_present")) for row in rows),
            "no_completion_claim_made": True,
        },
        "rows": rows,
        "failures": failures,
        "AUDIT_PASS": not failures,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"jax_geometry_layer_receipt_estate_fence_audit_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"geometry_layer_fence_audit AUDIT_PASS={out['AUDIT_PASS']} rows={len(rows)} failures={len(failures)} path={out_path}")
    return 0 if out["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
