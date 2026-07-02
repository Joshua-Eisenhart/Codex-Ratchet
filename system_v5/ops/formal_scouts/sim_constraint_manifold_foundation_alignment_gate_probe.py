#!/usr/bin/env python3
"""Strict foundation-alignment gate for the constraint manifold.

Formal scout only.

This row exists because a green bottom-up suite can still hide a wrong work
order: Axis0 scouts may execute downstream, and flux-layer scouts may execute
before the lower manifold layers are correct. This gate does not add another
flux or Axis0 candidate. It asks whether the layers that must precede the flux
layer are actually aligned with the two roots, spinor/quaternion substrate, and
PEPS3D depth.

Passing this row means the audit ran and preserved the blocker. It does not
mean the foundation is closed.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "constraint_manifold_foundation_alignment_gate_probe_results.json"
SUITE_MODULE_PATH = ROOT / "run_probe_effect_spinor_bottom_up_manifold_suite_20260524.py"
SUITE_RESULT_PATH = RESULT_DIR / "probe_effect_spinor_bottom_up_manifold_suite_20260524_results.json"
LAYER_AUDIT_PATH = RESULT_DIR / "constraint_manifold_layer_tool_matrix_audit_20260524_results.json"
ROOT_CLASSIFIER_PATH = RESULT_DIR / "root_substrate_violation_classifier_probe_results.json"

NAME = "constraint_manifold_foundation_alignment_gate_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "foundation_alignment_gate"
SOURCE_ALIGNMENT_CATEGORY = "constraint_manifold_foundation_alignment_gate"
PROMOTION_ALLOWED = False
ADMISSION_STATUS = "blocked"
EXPECTED_NONPROMOTION = True
CLAIM_CEILING = (
    "Formal scout only: audits whether lower constraint-manifold layers are "
    "actually foundation-aligned before flux-layer and downstream Axis0 work. It does "
    "not admit final manifold foundation, full PEPS3D closure, final flux, "
    "final Axis0, Xi/Phi0, physics, gravity, Standard Model, Yang-Mills, or "
    "Riemann claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt parsing and blocker matrix serialization",
    },
    "python_importlib": {
        "tried": True,
        "used": True,
        "reason": "supportive suite registry loading",
    },
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "python_importlib": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

FOUNDATION_STAGES = [
    "L0_finite_effect_probe_substrate",
    "L1_spinor_quaternion_networks",
    "L2_mps_peps_peps3d_carriers",
    "L3_engine_runtime",
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_suite_module() -> Any:
    spec = importlib.util.spec_from_file_location("bottom_up_suite_20260524", SUITE_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import suite registry: {SUITE_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lower_text(receipt: dict[str, Any]) -> str:
    return json.dumps(receipt, sort_keys=True, default=str).lower()


def receipt_flags(receipt: dict[str, Any]) -> dict[str, bool]:
    text = lower_text(receipt)
    return {
        "formal_scout_only": receipt.get("classification") == "formal_scout",
        "promotion_disabled": receipt.get("promotion_allowed") is False,
        "final_claim_blocked": "does not admit final" in text or "not admit final" in text,
        "finite_probe_or_effect": any(item in text for item in ["finite effect", "finite probe", "povm", "sic"]),
        "two_root_or_noncommuting": any(item in text for item in ["two_root", "noncommut", "weyl-heisenberg", "order"]),
        "spinor_or_quaternion": any(item in text for item in ["spinor", "quaternion", "hopf", "ijk", "weyl split"]),
        "peps3d_marker": "peps3d" in text,
        "full_peps3d_closure_blocked": any(
            item in text
            for item in [
                "does not perform full peps3d",
                "full_network_contraction\": false",
                "full peps3d closure",
                "not final peps3d closure",
                "does not admit final peps3d",
            ]
        ),
        "dense_or_density_adapter": any(
            item in text
            for item in [
                "dense pure-state",
                "density-matrix",
                "density matrix",
                "full density carrier",
                "one-qubit",
                "2x2",
            ]
        ),
        "engine_runtime": any(item in text for item in ["engine", "runtime", "terrain", "igt", "schedule"]),
    }


def stage_receipts(suite_module: Any) -> dict[str, list[dict[str, Any]]]:
    by_stage: dict[str, list[dict[str, Any]]] = {}
    for stage, scripts in suite_module.STAGED_SCRIPTS:
        if stage not in FOUNDATION_STAGES:
            continue
        rows: list[dict[str, Any]] = []
        for script in scripts:
            path = suite_module.expected_result_path(script)
            receipt = load_json(path)
            rows.append(
                {
                    "script": script,
                    "result_path": path,
                    "receipt": receipt,
                    "flags": receipt_flags(receipt) if receipt else {},
                }
            )
        by_stage[stage] = rows
    return by_stage


def summarize_stage(stage: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    flags = [row["flags"] for row in rows if row["receipt"]]
    missing = [row["script"] for row in rows if not row["receipt"]]
    raw_failures = [row["script"] for row in rows if row["receipt"] and row["receipt"].get("all_pass") is False]
    all_formal_nonpromotional = bool(flags) and all(
        flag.get("formal_scout_only") and flag.get("promotion_disabled") for flag in flags
    )
    final_claims_blocked = bool(flags) and all(flag.get("final_claim_blocked") for flag in flags)
    if stage == "L0_finite_effect_probe_substrate":
        supported = any(flag.get("finite_probe_or_effect") for flag in flags) and any(
            flag.get("two_root_or_noncommuting") for flag in flags
        )
        status = "partial_supported_not_final"
        blockers = [
            "foundation rows prove bounded finite-effect/probe and Weyl-Heisenberg witnesses, not final manifold ontology",
        ]
    elif stage == "L1_spinor_quaternion_networks":
        supported = any(flag.get("spinor_or_quaternion") for flag in flags) and any(
            flag.get("engine_runtime") for flag in flags
        )
        density_adapter_rows = [row["script"] for row in rows if row["flags"].get("dense_or_density_adapter")]
        status = "partial_supported_adapter_bound"
        blockers = [
            "spinor/quaternion rows exist, but several engine/network receipts still use density carriers as admitted adapters",
            f"density_adapter_rows={density_adapter_rows}",
        ]
    elif stage == "L2_mps_peps_peps3d_carriers":
        supported = any(flag.get("peps3d_marker") for flag in flags)
        full_closure_blockers = [row["script"] for row in rows if row["flags"].get("full_peps3d_closure_blocked")]
        status = "blocked_sampled_or_local_peps3d"
        blockers = [
            "PEPS3D rows are local/sampled/scaling receipts, not full PEPS3D environment closure",
            f"raw_expected_blocked_or_failed_rows={raw_failures}",
            f"full_closure_blocker_rows={full_closure_blockers}",
        ]
    elif stage == "L3_engine_runtime":
        supported = any(flag.get("engine_runtime") for flag in flags)
        adapter_rows = [row["script"] for row in rows if row["flags"].get("dense_or_density_adapter")]
        status = "blocked_until_runtime_is_peps3d_spinor_native"
        blockers = [
            "engine runtime is source-aligned enough for bounded controls, but not proven as full spinor/quaternion PEPS3D runtime",
            f"adapter_or_density_rows={adapter_rows}",
        ]
    else:
        supported = False
        status = "unknown_stage"
        blockers = ["stage not recognized by strict foundation gate"]
    return {
        "stage": stage,
        "script_count": len(rows),
        "missing_receipts": missing,
        "raw_all_pass_false_rows": raw_failures,
        "all_formal_nonpromotional": all_formal_nonpromotional,
        "final_claims_blocked": final_claims_blocked,
        "local_support_present": supported,
        "foundation_status": status,
        "foundation_closed": False,
        "blockers": blockers,
    }


def main() -> int:
    started = time.time()
    suite_module = load_suite_module()
    suite_result = load_json(SUITE_RESULT_PATH)
    layer_audit = load_json(LAYER_AUDIT_PATH)
    root_classifier = load_json(ROOT_CLASSIFIER_PATH)
    rows_by_stage = stage_receipts(suite_module)
    stage_matrix = [summarize_stage(stage, rows_by_stage.get(stage, [])) for stage in FOUNDATION_STAGES]

    suite_fresh_enough_for_gate = bool(suite_result.get("all_pass")) and (
        (suite_result.get("summary") or {}).get("script_count") == sum(len(s) for _, s in suite_module.STAGED_SCRIPTS)
    )
    layer_audit_green = bool(layer_audit.get("all_pass"))
    root_classifier_green = bool(root_classifier.get("all_pass"))

    foundation_closed = all(row["foundation_closed"] for row in stage_matrix)
    flux_layer_allowed = foundation_closed
    downstream_axis0_allowed = foundation_closed and flux_layer_allowed
    downstream_work_policy = (
        "freeze_axis0_and_block_flux_layer_until_lower_manifold_layers_are_correct"
        if not foundation_closed
        else "flux_layer_may_be_reintroduced_before_downstream_axis0"
    )

    positive = {
        "fresh_suite_available_for_audit": {
            "pass": suite_fresh_enough_for_gate,
            "suite_all_pass": suite_result.get("all_pass"),
            "suite_script_count": (suite_result.get("summary") or {}).get("script_count"),
        },
        "layer_audit_available": {"pass": layer_audit_green},
        "root_classifier_available": {"pass": root_classifier_green},
        "foundation_layers_have_local_support_but_not_closure": {
            "pass": all(row["local_support_present"] and not row["foundation_closed"] for row in stage_matrix),
            "stage_statuses": {row["stage"]: row["foundation_status"] for row in stage_matrix},
        },
    }
    boundary = {
        "formal_scout_only": {"pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False},
        "flux_layer_and_downstream_axis0_blocked_until_foundation_closure": {
            "pass": flux_layer_allowed is False and downstream_axis0_allowed is False,
            "flux_layer_allowed": flux_layer_allowed,
            "downstream_axis0_allowed": downstream_axis0_allowed,
            "policy": downstream_work_policy,
        },
        "all_pass_is_not_science_closed": {
            "pass": True,
            "meaning": (
                "all_pass means this blocker receipt executed. It does not "
                "close the foundation or authorize flux-layer or downstream Axis0 claims."
            ),
        },
    }
    graveyard_companions = {
        "GC1_suite_green_means_foundation_closed_rejected": {
            "pass": suite_fresh_enough_for_gate and foundation_closed is False,
            "control": "54/54 suite receipt",
            "reading": "fresh suite execution is not foundation closure",
        },
        "GC2_axis0_as_primary_lane_rejected": {
            "pass": downstream_axis0_allowed is False,
            "control": "downstream Axis0 rows",
            "reading": "Axis0 remains downstream blocker instrumentation until the flux layer and lower manifold layers are correct",
        },
        "GC3_flux_without_lower_layer_closure_rejected": {
            "pass": flux_layer_allowed is False,
            "control": "flux-layer rows before lower-layer closure",
            "reading": "flux is a constraint-manifold layer, but it cannot be cited before the lower layer object is correct",
        },
        "GC4_local_sampled_peps3d_as_full_closure_rejected": {
            "pass": any(row["stage"] == "L2_mps_peps_peps3d_carriers" and "sampled" in row["foundation_status"] for row in stage_matrix),
            "control": "L2 PEPS3D local/sampled receipts",
            "reading": "local/sampled PEPS3D support cannot be cited as full PEPS3D environment closure",
        },
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard_companions.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "admission_status": ADMISSION_STATUS,
        "expected_nonpromotion": EXPECTED_NONPROMOTION,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "foundation_closed": foundation_closed,
        "flux_layer_allowed": flux_layer_allowed,
        "downstream_axis0_allowed": downstream_axis0_allowed,
        "downstream_work_policy": downstream_work_policy,
        "stage_matrix": stage_matrix,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "all_pass": all_pass,
        "nearby_variants": {
            "passed": sum(
                1
                for item in list(positive.values()) + list(boundary.values()) + list(graveyard_companions.values())
                if item["pass"]
            ),
            "total": len(positive) + len(boundary) + len(graveyard_companions),
            "failed_checks": [
                name
                for name, item in {**positive, **boundary, **graveyard_companions}.items()
                if not item["pass"]
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 formal-scout foundation gate over the current "
            "probe/effect -> spinor/quaternion -> PEPS3D -> engine suite, "
            "not a legacy v4 probe and not a promotion surface."
        ),
        "why_not_final": [
            "L0 has bounded finite-effect/Weyl support but no final manifold ontology.",
            "L1 has explicit spinor/quaternion support but still consumes admitted density adapters.",
            "L2 has local/sampled/scaling PEPS3D receipts, not full PEPS3D environment closure.",
            "L3 has source-aligned runtime receipts, not a full spinor/quaternion PEPS3D runtime.",
            "Flux is a constraint-manifold layer, but the current flux-layer receipts cannot be cited until lower layers are correct.",
            "Axis0 remains a downstream readout and cannot be cited until flux-layer and lower-layer receipts are correct.",
        ],
        "divergence_log": [
            "The gate distinguishes local support from foundation closure.",
            "The gate distinguishes receipt all_pass from scientific admission.",
            "The gate separates flux-layer blocking from downstream Axis0 blocking.",
            "The gate blocks flux-layer claims until lower-layer closure exists and blocks Axis0 until the flux layer exists.",
        ],
        "next_required_work": [
            "Build L0-L1 handoff receipts that keep finite probe/effect identity primary while admitting spinor/quaternion carriers.",
            "Build L2 full-closure target or a stricter proof that the current PEPS3D fixture only has local/sampled authority.",
            "Port L3 engine runtime onto the strongest admitted spinor/quaternion PEPS3D carrier before renewing flux-layer work.",
            "Keep Axis0 frozen until the flux layer is correctly represented as a constraint-manifold layer.",
        ],
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "foundation_closed": foundation_closed,
                "flux_layer_allowed": flux_layer_allowed,
                "downstream_axis0_allowed": downstream_axis0_allowed,
                "wrote": str(OUT_PATH),
            },
            indent=2,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
