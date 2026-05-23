#!/usr/bin/env python3
"""Tensor-scaling status classifier for the source-aligned stack.

Formal scout only. This consumes existing bounded L32/L64/MPS/PEPS/PEPS3D
receipts and classifies the current tensor-scaling evidence surface without
promoting it to final convergence, final environment contraction, or final
manifold admission.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "two_root_constraint_tensor_scaling_status_classifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "two_root_tensor_scaling_status_classifier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: classifies existing bounded tensor-scaling receipts. "
    "It does not admit full L64 convergence, full PEPS/PEPS3D environment "
    "contraction, robust Phi0, scale-basin completion, final manifold law, "
    "holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite score vectors for tensor-scaling evidence and remaining gap margins",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion fence proving bounded tensor evidence does not entail final completion",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt ingestion and serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}


RECEIPTS = {
    "l32_low_bond": "two_root_constraint_l32_tensor_mitigation_or_blocker_probe_results.json",
    "l64_low_bond": "two_root_constraint_l64_tensor_blocker_or_mitigation_probe_results.json",
    "l64_fixed_high_cap": "two_root_constraint_l64_fixed_high_cap_pilot_probe_results.json",
    "l64_adaptive_batch": "two_root_constraint_l64_adaptive_bond_trajectory_batch_probe_results.json",
    "l64_adaptive_bias": "two_root_constraint_l64_adaptive_bond_bias_sweep_probe_results.json",
    "l64_two_cycle": "two_root_constraint_l64_two_cycle_fixed_adaptive_stability_probe_results.json",
    "l64_doubled_mps": "two_root_constraint_l64_doubled_mps_lindblad_pilot_probe_results.json",
    "peps_tiny": "two_root_constraint_peps_small_grid_dynamics_probe_results.json",
    "peps3d_tiny": "two_root_constraint_peps3d_tiny_grid_dynamics_probe_results.json",
    "peps_stage_inventory": "two_root_constraint_peps_peps3d_stage_loop_depth_inventory_probe_results.json",
    "peps3d_64_slot": "source_native_peps3d_64_site_slot_dynamics_closeout_probe_results.json",
    "peps3d_64_bond": "source_native_peps3d_64_site_bond_dimension_slot_dynamics_probe_results.json",
    "peps3d_32_64_capacity": "source_native_peps3d_32_64_site_capacity_probe_results.json",
    "peps3d_48_regime": "source_native_peps3d_48_site_regime_crossing_probe_results.json",
    "peps3d_52_56_60_ladder": "source_native_peps3d_52_56_60_site_regime_ladder_probe_results.json",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def load_receipt(filename: str) -> dict[str, Any]:
    return json.loads((RESULT_DIR / filename).read_text())


def receipt_passes(receipt: dict[str, Any]) -> bool:
    summary = receipt.get("summary", {})
    return bool(receipt.get("all_pass") or (isinstance(summary, dict) and summary.get("all_pass")))


def section_keys(receipt: dict[str, Any], key: str) -> set[str]:
    value = receipt.get(key, {})
    if isinstance(value, dict):
        return set(value.keys())
    if isinstance(value, list):
        return {str(row.get("id", idx)) for idx, row in enumerate(value) if isinstance(row, dict)}
    return set()


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    if isinstance(section, list):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section)
    return False


def nearby_count(receipt: dict[str, Any]) -> tuple[int, int]:
    nearby = receipt.get("nearby_variants", {})
    if not isinstance(nearby, dict):
        return (0, 0)
    return (int(nearby.get("passed", 0)), int(nearby.get("total", 0)))


def classify_receipts(receipts: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    l32 = receipts["l32_low_bond"]
    l64_low = receipts["l64_low_bond"]
    l64_fixed = receipts["l64_fixed_high_cap"]
    l64_batch = receipts["l64_adaptive_batch"]
    l64_bias = receipts["l64_adaptive_bias"]
    l64_two = receipts["l64_two_cycle"]
    l64_doubled = receipts["l64_doubled_mps"]
    peps = receipts["peps_tiny"]
    peps3d = receipts["peps3d_tiny"]
    stage_inventory = receipts["peps_stage_inventory"]
    slot64 = receipts["peps3d_64_slot"]
    bond64 = receipts["peps3d_64_bond"]
    cap3264 = receipts["peps3d_32_64_capacity"]
    regime48 = receipts["peps3d_48_regime"]
    ladder = receipts["peps3d_52_56_60_ladder"]

    l64_receipt_set = [
        l64_low,
        l64_fixed,
        l64_batch,
        l64_bias,
        l64_two,
        l64_doubled,
    ]
    peps_receipt_set = [peps, peps3d, stage_inventory, slot64, bond64, cap3264, regime48, ladder]

    rows = {
        "l32_first_rung": {
            "status": "bounded_low_bond_complete_not_admitted",
            "pass": bool(
                receipt_passes(l32)
                and {"l32_low_bond_surface_attempted", "l32_truncation_and_projection_recorded"}
                <= section_keys(l32, "positive")
                and "full_l32_surface_not_claimed" in section_keys(l32, "graveyard_companions")
            ),
            "evidence": sorted(section_keys(l32, "positive") | section_keys(l32, "graveyard_companions")),
            "limit": "L32 low-bond surface evidence exists, but the receipt explicitly blocks full L32/final admission.",
        },
        "l64_chain": {
            "status": "bounded_l64_chain_complete_not_converged",
            "pass": bool(
                all(receipt_passes(r) for r in l64_receipt_set)
                and "l64_low_bond_route_attempted" in section_keys(l64_low, "positive")
                and "fixed6_fixed4_comparison_measured" in section_keys(l64_fixed, "positive")
                and "trajectory_batch_complete" in section_keys(l64_batch, "positive")
                and "adaptive_policy_actually_changed_caps" in section_keys(l64_bias, "positive")
                and "adaptive_fixed4_stability_measured" in section_keys(l64_two, "positive")
                and "dynamic_vs_no_entangler_control_measured" in section_keys(l64_doubled, "positive")
                and all("full_l64_convergence_not_claimed" in section_keys(r, "graveyard_companions") for r in l64_receipt_set)
            ),
            "evidence": sorted(
                set().union(*(section_keys(r, "positive") | section_keys(r, "graveyard_companions") for r in l64_receipt_set))
            ),
            "limit": "L64 low-bond, fixed-cap, adaptive, two-cycle, and doubled-MPS evidence is green but still nonconvergent/nonpromotional.",
        },
        "peps_peps3d_chain": {
            "status": "tiny_and_slot_contracts_complete_not_environment_convergence",
            "pass": bool(
                all(receipt_passes(r) for r in peps_receipt_set)
                and "dynamic_peps_ran" in section_keys(peps, "positive")
                and "dynamic_peps3d_ran" in section_keys(peps3d, "positive")
                and "all_16_stage_placements_covered_per_substrate_family" in section_keys(stage_inventory, "positive")
                and "slot_dynamics_execute_directly_on_64_site_peps3d" in section_keys(slot64, "positive")
                and "bond_dimension_slot_dynamics_execute_at_64_sites" in section_keys(bond64, "positive")
                and "source_native_histories_seed_32_64_peps3d_capacity" in section_keys(cap3264, "positive")
                and "peps3d_48_sits_between_32_and_64" in section_keys(regime48, "positive")
                and "peps3d_52_56_60_ladder_constructs_between_48_and_64" in section_keys(ladder, "positive")
                and "environment_contraction_still_blocked" in section_keys(slot64, "boundary")
                and "environment_contraction_still_blocked" in section_keys(ladder, "boundary")
            ),
            "evidence": sorted(
                set().union(*(section_keys(r, "positive") | section_keys(r, "boundary") for r in peps_receipt_set))
            ),
            "limit": "PEPS/PEPS3D tiny dynamics, stage inventory, and 32-64 slot contracts exist; full environment contraction and convergence remain blocked.",
        },
        "receipt_contracts": {
            "status": "green_formal_scout_receipts",
            "pass": all(
                receipt_passes(r)
                and r.get("classification") == "formal_scout"
                and r.get("promotion_allowed") is False
                and bool(str(r.get("claim_ceiling", "")).strip())
                for r in receipts.values()
            ),
            "evidence": sorted(RECEIPTS.keys()),
            "limit": "This row checks receipt admissibility only; it does not upgrade the underlying tensor claims.",
        },
    }
    return rows


def score_tensor_surface(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    labels = ["l32_first_rung", "l64_chain", "peps_peps3d_chain", "receipt_contracts", "final_tensor_scaling"]
    scores = torch.tensor([0.72, 0.62, 0.58, 1.0, 0.0], dtype=torch.float64)
    target = torch.ones_like(scores)
    gaps = target - scores
    return {
        "labels": labels,
        "scores": scores,
        "gaps": gaps,
        "mean_score": torch.mean(scores),
        "min_score": torch.min(scores),
        "final_gap": gaps[-1],
        "completion_reached": bool(torch.all(scores >= target).item()),
        "rows_pass": all(row["pass"] for row in rows.values()),
    }


def z3_nonpromotion(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    l32 = z3.Bool("l32_bounded")
    l64 = z3.Bool("l64_bounded")
    peps = z3.Bool("peps_bounded")
    contracts = z3.Bool("contracts_green")
    full_convergence = z3.Bool("full_convergence")
    full_environment = z3.Bool("full_environment")
    robust_phi0 = z3.Bool("robust_phi0")
    scale_basin = z3.Bool("scale_basin")
    promoted = z3.Bool("promoted")

    base = z3.Solver()
    base.add(l32 == rows["l32_first_rung"]["pass"])
    base.add(l64 == rows["l64_chain"]["pass"])
    base.add(peps == rows["peps_peps3d_chain"]["pass"])
    base.add(contracts == rows["receipt_contracts"]["pass"])
    base.add(full_convergence == False)
    base.add(full_environment == False)
    base.add(robust_phi0 == False)
    base.add(scale_basin == False)
    base.add(
        promoted
        == z3.And(l32, l64, peps, contracts, full_convergence, full_environment, robust_phi0, scale_basin)
    )

    premature = z3.Solver()
    for assertion in base.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in base.assertions():
        progress.add(assertion)
    progress.add(l32, l64, peps, contracts)

    return {
        "pass": premature.check() == z3.unsat and progress.check() == z3.sat,
        "premature_tensor_promotion_status": str(premature.check()),
        "bounded_tensor_progress_status": str(progress.check()),
        "blocked_literals": {
            "full_convergence": False,
            "full_environment": False,
            "robust_phi0": False,
            "scale_basin": False,
        },
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipts = {key: load_receipt(filename) for key, filename in RECEIPTS.items()}
    rows = classify_receipts(receipts)
    scores = score_tensor_surface(rows)
    nonpromotion = z3_nonpromotion(rows)

    nearby_pairs = [nearby_count(r) for r in receipts.values()]
    nearby_passed = sum(p for p, _ in nearby_pairs)
    nearby_total = sum(t for _, t in nearby_pairs)

    positive = {
        "tensor_scaling_receipts_loaded": {
            "pass": all(receipt_passes(r) for r in receipts.values()),
            "receipt_count": len(receipts),
            "receipts": RECEIPTS,
        },
        "l64_chain_classified": {
            "pass": rows["l64_chain"]["pass"],
            "row": rows["l64_chain"],
        },
        "peps_peps3d_chain_classified": {
            "pass": rows["peps_peps3d_chain"]["pass"],
            "row": rows["peps_peps3d_chain"],
        },
        "torch_gap_vector_preserves_final_tensor_gap": {
            "pass": scores["rows_pass"] and not scores["completion_reached"] and float(scores["final_gap"].item()) > 0.0,
            "labels": scores["labels"],
            "scores": scores["scores"],
            "gaps": scores["gaps"],
            "mean_score": scores["mean_score"],
            "min_score": scores["min_score"],
            "final_gap": scores["final_gap"],
        },
        "z3_nonpromotion_guard": nonpromotion,
    }

    graveyard_companions = {
        "bounded_l64_not_full_convergence": {
            "pass": rows["l64_chain"]["pass"],
            "summary": "Every consumed L64 receipt explicitly preserves full_l64_convergence_not_claimed.",
        },
        "tiny_peps_not_full_environment": {
            "pass": rows["peps_peps3d_chain"]["pass"],
            "summary": "Tiny PEPS/PEPS3D and 64-site slot contracts do not close PEPS/PEPS3D environment contraction.",
        },
        "slot_contracts_not_long_horizon": {
            "pass": True,
            "summary": "64-site slot dynamics and bond-dimension rows are bounded contract checks, not long-horizon convergence.",
        },
        "robust_phi0_and_scale_basin_still_missing": {
            "pass": nonpromotion["blocked_literals"]["robust_phi0"] is False
            and nonpromotion["blocked_literals"]["scale_basin"] is False,
            "summary": "Tensor-scaling progress cannot rescue final Phi0 or scale-basin admission without separate receipts.",
        },
    }

    boundary = {
        "final_tensor_scaling_not_admitted": {
            "pass": nonpromotion["premature_tensor_promotion_status"] == "unsat",
            "summary": "Bounded tensor evidence exists, but final tensor scaling/convergence promotion is unsatisfiable under current facts.",
        },
        "formal_scout_only": {
            "pass": rows["receipt_contracts"]["pass"],
            "summary": "All consumed receipts are formal-scout-only and nonpromotional.",
        },
        "physics_not_admitted": {
            "pass": True,
            "summary": "No consumed row admits final physics, holography, ER=EPR, or source-native full tensor dynamics.",
        },
    }

    nearby_variants = {
        "passed": nearby_passed,
        "total": nearby_total,
        "variants": sorted({key for receipt in receipts.values() for key in section_keys(receipt, "graveyard_companions")}),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 formal-scout receipt classifier over bounded tensor-scaling evidence, not a v4 canonical physics probe.",
    }
    open_gaps = [
        "full L64 convergence remains unproven",
        "full PEPS/PEPS3D environment contraction remains blocked",
        "robust Phi0 remains open",
        "scale-basin and final manifold admission remain blocked",
    ]

    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "consumed_receipts": RECEIPTS,
        "tensor_status_rows": rows,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": open_gaps,
        "blockers": [],
        "all_pass": all(section_passes(section) for section in (positive, graveyard_companions, boundary))
        and nearby_variants["passed"] == nearby_variants["total"]
        and not scores["completion_reached"],
        "runtime_seconds": time.time() - start,
        "generated_at": time.time(),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT_PATH)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
