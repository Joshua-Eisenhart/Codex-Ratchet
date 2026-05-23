#!/usr/bin/env python3
"""Flux-recovery runtime/tensor bridge classifier.

Formal scout only. This consumes the stress-survived flux-coherent recovery
candidate together with coupled-E16 Phi0 stress and tensor-scaling status. Its
job is to prevent a false promotion: the candidate survived its bounded local
stress surface, but it has not yet been embedded into the full coupled runtime
or tensor-scaling surfaces.
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
NAME = "two_root_constraint_flux_recovery_runtime_tensor_bridge_classifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "flux_recovery_runtime_tensor_bridge_classifier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: classifies whether the stress-survived flux-coherent "
    "recovery candidate is admitted by coupled runtime and tensor-scaling "
    "evidence. It does not admit final Xi, final Phi0, final Axis0, full "
    "runtime, full tensor scaling, holography, ER=EPR, or physics."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bridge gap vector over flux stress, coupled runtime stress, tensor scaling, and final admission rows",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive nonpromotion fence separating local stress survival from runtime/tensor admission",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt ingestion and result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local receipt path handling"},
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
    "flux_coherent_stress": "two_root_constraint_flux_coherent_recovery_stress_probe_results.json",
    "coupled_e16_phi0_stress": "two_root_constraint_coupled_e16_phi0_stress_controls_probe_results.json",
    "tensor_scaling_status": "two_root_constraint_tensor_scaling_status_classifier_probe_results.json",
    "full_trace_after_stress": "two_root_constraint_full_manifold_trace_after_phi0_stress_probe_results.json",
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


def section_keys(receipt: dict[str, Any], section: str) -> set[str]:
    value = receipt.get(section, {})
    if isinstance(value, dict):
        return set(value)
    if isinstance(value, list):
        return {str(row.get("id", idx)) for idx, row in enumerate(value) if isinstance(row, dict)}
    return set()


def section_passes(section: Any) -> bool:
    if isinstance(section, dict):
        return all(not isinstance(row, dict) or bool(row.get("pass", True)) for row in section.values())
    return False


def classify(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    flux = receipts["flux_coherent_stress"]
    coupled = receipts["coupled_e16_phi0_stress"]
    tensor = receipts["tensor_scaling_status"]
    trace = receipts["full_trace_after_stress"]

    flux_class = flux["candidate_classification"]
    coupled_summary = coupled["summary"]
    tensor_positive = tensor["positive"]
    tensor_boundary = tensor["boundary"]
    tensor_graveyard = tensor["graveyard_companions"]
    trace_summary = trace["summary"]

    local_stress_survived = bool(
        flux.get("all_pass")
        and flux_class["bounded_stress_survives"]
        and flux_class["survive_count"] == flux_class["row_count"]
        and flux_class["min_margin"] > 0.001
    )
    coupled_runtime_robust = bool(
        coupled.get("all_pass")
        and coupled_summary["stress_status"] != "open_nonrobust_internal_controls"
        and coupled_summary["min_canonical_minus_max_internal_control"] > 0.0
    )
    coupled_runtime_nonrobust_blocker = bool(
        coupled.get("all_pass")
        and coupled_summary["stress_status"] == "open_nonrobust_internal_controls"
        and coupled_summary["min_canonical_minus_max_internal_control"] < 0.0
        and "stress_may_demote_weak_bridge" in section_keys(coupled, "graveyard_companions")
    )
    tensor_status_green = bool(tensor.get("all_pass") and tensor_positive["tensor_scaling_receipts_loaded"]["pass"])
    tensor_final_blocked = bool(
        tensor_status_green
        and tensor_boundary["final_tensor_scaling_not_admitted"]["pass"]
        and tensor_graveyard["robust_phi0_and_scale_basin_still_missing"]["pass"]
    )
    final_trace_blocks_admission = bool(
        trace.get("all_pass")
        and trace_summary["final_manifold_admission_allowed"] is False
        and trace_summary["final_goal_complete"] is False
        and trace_summary["phi0_current_status"] == "open_nonrobust_internal_controls"
    )

    scores = torch.tensor(
        [
            1.0 if local_stress_survived else 0.0,
            1.0 if coupled_runtime_robust else 0.0,
            0.58 if tensor_status_green else 0.0,
            0.0 if final_trace_blocks_admission else 1.0,
        ],
        dtype=torch.float64,
    )
    labels = [
        "local_flux_coherent_stress",
        "coupled_runtime_phi0_stress",
        "tensor_scaling_status",
        "final_manifold_trace",
    ]
    status = (
        "runtime_tensor_admitted_not_final"
        if local_stress_survived and coupled_runtime_robust and not tensor_final_blocked and not final_trace_blocks_admission
        else "local_stress_survived_runtime_tensor_open"
        if local_stress_survived and coupled_runtime_nonrobust_blocker and tensor_final_blocked and final_trace_blocks_admission
        else "stress_demoted_or_inconsistent"
    )
    return {
        "status": status,
        "local_stress_survived": local_stress_survived,
        "coupled_runtime_robust": coupled_runtime_robust,
        "coupled_runtime_nonrobust_blocker": coupled_runtime_nonrobust_blocker,
        "tensor_status_green": tensor_status_green,
        "tensor_final_blocked": tensor_final_blocked,
        "final_trace_blocks_admission": final_trace_blocks_admission,
        "labels": labels,
        "scores": scores,
        "min_score": torch.min(scores),
        "mean_score": torch.mean(scores),
        "local_min_margin": flux_class["min_margin"],
        "coupled_min_margin": coupled_summary["min_canonical_minus_max_internal_control"],
        "tensor_final_gap": tensor_positive["torch_gap_vector_preserves_final_tensor_gap"]["final_gap"],
    }


def z3_nonpromotion(classification_row: dict[str, Any]) -> dict[str, Any]:
    local = z3.Bool("local_flux_stress_survived")
    coupled = z3.Bool("coupled_runtime_robust")
    tensor = z3.Bool("tensor_final_closed")
    trace = z3.Bool("final_trace_admits")
    promoted = z3.Bool("promoted")

    s = z3.Solver()
    s.add(local == bool(classification_row["local_stress_survived"]))
    s.add(coupled == bool(classification_row["coupled_runtime_robust"]))
    s.add(tensor == (not bool(classification_row["tensor_final_blocked"])))
    s.add(trace == (not bool(classification_row["final_trace_blocks_admission"])))
    s.add(promoted == z3.And(local, coupled, tensor, trace))

    premature = z3.Solver()
    for assertion in s.assertions():
        premature.add(assertion)
    premature.add(promoted)

    progress = z3.Solver()
    for assertion in s.assertions():
        progress.add(assertion)
    progress.add(local)

    return {
        "pass": premature.check() == z3.unsat and progress.check() == z3.sat,
        "premature_runtime_tensor_promotion_status": str(premature.check()),
        "bounded_local_progress_status": str(progress.check()),
    }


def main() -> int:
    start = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipts = {key: load_receipt(filename) for key, filename in RECEIPTS.items()}
    classification_row = classify(receipts)
    nonpromotion = z3_nonpromotion(classification_row)

    positive = {
        "upstream_receipts_loaded": {
            "pass": all(receipt.get("all_pass") for receipt in receipts.values()),
            "loaded": RECEIPTS,
        },
        "local_flux_recovery_stress_survived": {
            "pass": classification_row["local_stress_survived"],
            "local_min_margin": classification_row["local_min_margin"],
        },
        "runtime_tensor_bridge_status_classified": {
            "pass": classification_row["status"] == "local_stress_survived_runtime_tensor_open",
            "classification": classification_row,
        },
        "z3_nonpromotion_guard": nonpromotion,
    }
    graveyard_companions = {
        "coupled_runtime_phi0_stress_not_robust": {
            "pass": classification_row["coupled_runtime_nonrobust_blocker"],
            "coupled_min_margin": classification_row["coupled_min_margin"],
        },
        "tensor_scaling_still_blocks_admission": {
            "pass": classification_row["tensor_final_blocked"],
            "tensor_final_gap": classification_row["tensor_final_gap"],
        },
        "final_trace_still_blocks_admission": {
            "pass": classification_row["final_trace_blocks_admission"],
        },
    }
    boundary = {
        "final_xi_phi0_not_admitted": {
            "pass": True,
            "summary": "Local flux-coherent stress survival does not admit final Xi/Phi0 without coupled-runtime and tensor-scale closure.",
        },
        "formal_scout_only": {
            "pass": not PROMOTION_ALLOWED and CLASSIFICATION == "formal_scout",
            "claim_ceiling": CLAIM_CEILING,
        },
        "full_runtime_and_tensor_scaling_not_admitted": {
            "pass": True,
            "summary": "The consumed runtime and tensor receipts are still bounded/nonpromotional.",
        },
    }
    nearby_variants = {
        "total": 3,
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }
    why_not_v4_probes = {
        "pass": True,
        "reason": "This is a v5 receipt classifier over formal-scout evidence, not a v4 promoted probe.",
    }
    open_gaps = [
        "embed flux-coherent recovery directly into coupled runtime stress rows",
        "close or strengthen tensor-scaling/environment contraction evidence",
        "final Xi/Phi0 and final manifold admission remain open",
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
        "candidate_classification": classification_row,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": why_not_v4_probes,
        "open_gaps": open_gaps,
        "blockers": [],
        "all_pass": all(section_passes(section) for section in (positive, graveyard_companions, boundary))
        and nearby_variants["passed"] == nearby_variants["total"],
        "runtime_seconds": time.time() - start,
        "generated_at": time.time(),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "status": classification_row["status"],
                "local_min_margin": classification_row["local_min_margin"],
                "coupled_min_margin": classification_row["coupled_min_margin"],
                "out": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
