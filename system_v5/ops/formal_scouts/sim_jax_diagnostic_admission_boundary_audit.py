#!/usr/bin/env python3
"""Admission-boundary audit for the current JAX diagnostic/formal-scout lane.

This audit does not run sims. It reads current JAX receipt JSONs and checks that
green scout evidence remains fenced below manifold/layer/flux/Axis0/FEP/physics
admission. Julia is read-only reference for this lane; PyTorch is retired here.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


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
    "layer_stacking_readiness": "layer_stacking",
    "layer_completion": "full_layer_completion",
    "full layer completion": "full_layer_completion",
    "official G-structure selection": "official_g_structure_selection",
    "stacking": "layer_stacking",
    "layer stacking readiness": "layer_stacking",
    "layer_embedding": "layer_stacking",
    "final_manifold": "final_manifold_admission",
    "final manifold": "final_manifold_admission",
    "final manifold admission": "final_manifold_admission",
    "physics": "physics_gravity",
    "physics/gravity": "physics_gravity",
    "Holodeck/FEP": "FEP",
}

RECEIPTS = [
    "jax_independent_layer_source_jax_rebuild_results.json",
    "jax_weyl_terrain_16_placements_lindblad_audit_results.json",
    "jax_weyl_terrain_64_microstep_diagnostic_results.json",
    "jax_gstructure_16_placement_spin3_audit_results.json",
    "jax_noncommutative_finitude_ratchet_basin_hierarchy_results.json",
    "jax_noncommutative_finitude_ratchet_deepening_falsifier_results.json",
    "jax_post_nesting_nonflux_batch_refresh_results.json",
    "jax_foundation_reference_coverage_refresh_results.json",
    "system_v5/ops/formal_scouts/results/jax_weyl_terrain_joint_rho_ab_qit_diagnostic_results.json",
    "system_v5/ops/formal_scouts/results/jaxlie_so3_order_micro_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_l4_l5_order_commutator_finitude_ratchet_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_nested_hopf_leaf_area_order_ratchet_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_radial_dirac_interleaf_coupling_probe_results.json",
    "system_v5/ops/formal_scouts/results/jax_emergent_basin_nested_terrains_probe_results.json",
]
LATEST_RECEIPT_GLOBS = [
    "system_v5/ops/wizard_admissions/jax_geometry_layer_receipt_estate_fence_audit_*.json",
    "system_v5/ops/wizard_admissions/jax_gstructure_entropy_operator_focus_audit_*.json",
]


def load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_blocks(blocks: Any) -> set[str]:
    out: set[str] = set()
    for raw in blocks or []:
        s = str(raw)
        out.add(ALIASES.get(s, s))
    return out


def result_ok(d: dict[str, Any]) -> bool:
    if "AUDIT_PASS" in d:
        return bool(d["AUDIT_PASS"])
    if "all_pass" in d:
        return bool(d["all_pass"])
    if d.get("status") in {"passes", "pass", "passed"}:
        return True
    return False


def main() -> int:
    rows = []
    failures = []
    paths = list(RECEIPTS)
    for pattern in LATEST_RECEIPT_GLOBS:
        matches = sorted(Path().glob(pattern))
        if matches:
            paths.append(str(matches[-1]))
        else:
            paths.append(pattern)
    for path in paths:
        p = Path(path)
        if not p.exists():
            row = {"path": path, "exists": False, "result_ok": False}
            rows.append(row)
            failures.append({"path": path, "reason": "missing"})
            continue
        d = load(path)
        blocks = normalize_blocks(d.get("blocked_consumers") or d.get("blocked_claims"))
        if "summary" in d and isinstance(d["summary"], dict):
            blocks |= normalize_blocks(d["summary"].get("blocked_consumers"))
        row = {
            "path": path,
            "exists": True,
            "classification": d.get("classification"),
            "AUDIT_PASS": d.get("AUDIT_PASS"),
            "all_pass": d.get("all_pass"),
            "result_ok": result_ok(d),
            "promotion_allowed": d.get("promotion_allowed"),
            "formal_admission_allowed": d.get("formal_admission_allowed"),
            "ran_julia": d.get("ran_julia"),
            "ran_pytorch": d.get("ran_pytorch"),
            "normalized_blocked_consumers": sorted(blocks),
            "required_blocks_present": REQUIRED_BLOCKS <= blocks,
        }
        rows.append(row)
        if not row["result_ok"]:
            failures.append({"path": path, "reason": "result_not_green"})
        if row["promotion_allowed"] is not False:
            failures.append({"path": path, "reason": "promotion_not_false"})
        if row["formal_admission_allowed"] is True:
            failures.append({"path": path, "reason": "formal_admission_true"})
        if row["ran_julia"] is not False:
            failures.append({"path": path, "reason": "ran_julia_not_false"})
        if row["ran_pytorch"] is not False:
            failures.append({"path": path, "reason": "ran_pytorch_not_false"})
        if not row["required_blocks_present"]:
            failures.append({"path": path, "reason": "missing_required_blocks", "have": sorted(blocks)})
    out = {
        "kind": "jax_diagnostic_admission_boundary_audit",
        "classification": "admission_boundary_audit",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "current JAX diagnostic/formal-scout receipts plus nested Hopf leaf-area order ratchet scout",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "ran_julia": False,
        "ran_pytorch": False,
        "allowed_claim": "JAX diagnostic/audit receipts passed local checks and remain fenced below promotion/admission.",
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
        "checks": {
            "all_receipts_green_or_passed": all(row["result_ok"] for row in rows),
            "all_promotion_blocked": all(row.get("promotion_allowed") is False for row in rows),
            "no_formal_admission_true": all(row.get("formal_admission_allowed") is not True for row in rows),
            "all_julia_false": all(row.get("ran_julia") is False for row in rows),
            "all_pytorch_false": all(row.get("ran_pytorch") is False for row in rows),
            "all_required_blocks_present": all(row.get("required_blocks_present") for row in rows),
            "no_completion_claim_made": True,
        },
        "rows": rows,
        "failures": failures,
        "AUDIT_PASS": not failures,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"jax_diagnostic_admission_boundary_audit_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"admission_boundary_audit AUDIT_PASS={out['AUDIT_PASS']} rows={len(rows)} failures={len(failures)} path={out_path}")
    return 0 if out["AUDIT_PASS"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
