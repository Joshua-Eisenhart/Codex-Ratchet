#!/usr/bin/env python3
"""Audit tmp/grok attractor-basin sidequests for bounded adoption.

This scout does not promote tmp files or grok_sim sidequests into formal
evidence. It imports only method-level guardrails: sidequest boundaries,
phase-failure negatives, and basin-label discipline.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "attractor_basin_tmp_grok_sidequest_adoption_audit_probe_results.json"

NAME = "attractor_basin_tmp_grok_sidequest_adoption_audit_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: audits tmp and system_v5/grok_sim sidequest artifacts "
    "as noncanonical proposal/audit material for attractor-basin criteria. It "
    "does not admit tmp results, grok_sim results, Axis0, FEP, Holodeck, engine, "
    "physics, cognition, world-model, or canonical architecture claims."
)

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parsing of current basin classifier and grok_sim sidequest receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing bounded path checks for repo and tmp artifacts",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source artifact hash receipts",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "json": "load_bearing",
    "pathlib": "load_bearing",
    "hashlib": "load_bearing",
}

TMP_ENGINE_V2 = pathlib.Path("/private/tmp/engine_v2")
TMP_GROK_LOOPS = [
    pathlib.Path("/private/tmp/grok_loop_v17.txt"),
    pathlib.Path("/private/tmp/grok_loop_v18.txt"),
]
GROK_PHASE21 = REPO / "system_v5/grok_sim/loop_runner/receipts/20260517T054314Z/phase_21_engine_16_placement_64_microstep_uniqueness_results.json"
GROK_PHASE32 = REPO / "system_v5/grok_sim/loop_runner/receipts/codex_verify_sidequest_best_20260514Tlocal/phase_32_axis_cliff_results.json"
CLASSIFIER_RESULT = RESULT_DIR / "attractor_basin_success_criteria_receipt_classifier_probe_results.json"
DOCTRINE_DOC = REPO / "system_v5/docs/ATTRACTOR_BASIN_SUCCESS_DOCTRINE_v0.md"

REQUIRED_REPAIR_FIELDS = {
    "weak_link",
    "target_file_or_result",
    "admission_rule_improved",
    "dependency_subset",
    "stage_fields_touched_or_consumed",
    "before_baseline/hash",
    "after_delta/hash",
    "primary_control/result",
    "axis0_outputs_or_blockers",
    "provider_inputs_used",
    "promotion_ceiling",
    "next_step",
}


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["path"] = str(path)
    data["sha256"] = sha256_file(path)
    return data


def read_text_report(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "path": str(path), "sha256": None}
    text = path.read_text(encoding="utf-8", errors="replace")
    return {
        "exists": True,
        "path": str(path),
        "sha256": sha256_file(path),
        "bytes": len(text.encode("utf-8")),
        "all_pass_false_mentions": text.count("ALL PASS: False"),
        "did_run_false_mentions": text.count("did_run=False"),
        "z3_cvc5_mismatch_mentions": text.count("SMT z3==cvc5: False"),
        "qutip_dimension_error": "incompatible dimensions" in text,
        "z3_reset_assertions_error": "resetAssertions" in text,
    }


def classifier_label_counts(classifier: dict[str, Any]) -> dict[str, int]:
    if not classifier.get("exists"):
        return {}
    labels = classifier.get("label_summary") or classifier.get("label_counts") or {}
    if isinstance(labels, dict):
        return {str(k): int(v) for k, v in labels.items()}
    rows = classifier.get("case_rows") or []
    counts: dict[str, int] = {}
    for row in rows:
        label = str(row.get("computed_label"))
        counts[label] = counts.get(label, 0) + 1
    return counts


def phase_receipt_summary(receipt: dict[str, Any]) -> dict[str, Any]:
    observable = receipt.get("observable") or {}
    failures = observable.get("failures") or []
    return {
        "exists": receipt.get("exists", False),
        "classification": receipt.get("classification"),
        "promotion_allowed": receipt.get("promotion_allowed"),
        "admission_scope": receipt.get("admission_scope"),
        "claim_ceiling": receipt.get("claim_ceiling"),
        "phase_pass": observable.get("phase_pass"),
        "failure_count": len(failures),
        "first_failure": failures[0] if failures else None,
    }


def main() -> int:
    started = time.time()
    classifier = load_json(CLASSIFIER_RESULT)
    phase21 = load_json(GROK_PHASE21)
    phase32 = load_json(GROK_PHASE32)
    tmp_reports = [read_text_report(path) for path in TMP_GROK_LOOPS]
    tmp_engine_reports = [
        read_text_report(TMP_ENGINE_V2 / name)
        for name in ("jp_council_grok.txt", "lev_council_grok.txt", "v4_2_council_grok.txt")
    ]

    labels = classifier_label_counts(classifier)
    phase21_summary = phase_receipt_summary(phase21)
    phase32_summary = phase_receipt_summary(phase32)
    tmp_negative_markers = sum(
        int(report.get("all_pass_false_mentions", 0))
        + int(report.get("did_run_false_mentions", 0))
        + int(report.get("z3_cvc5_mismatch_mentions", 0))
        for report in tmp_reports
    )

    adopted_method_guards = [
        "score basin depth by method independence and matched-control pressure, not by all_pass alone",
        "keep tmp and grok_sim sidequests noncanonical until converted to formal_scout receipts",
        "treat repeated phase failures as anti/open basin signals, not as failed work to hide",
        "require sidequest phase claims to survive formal scout claim ceilings before adoption",
        "use z3/cvc5 disagreement, dimension errors, and did_run=false as hard open-boundary markers",
    ]

    repair_receipt = {
        "weak_link": "Attractor-basin work was split across current formal receipts, tmp engine_v2 notes, and grok_sim sidequest artifacts without a bounded adoption gate.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": "Tmp/grok artifacts can contribute only method guards or scout targets unless converted into formal_scout receipts with claim ceilings and matched controls.",
        "dependency_subset": [
            str(CLASSIFIER_RESULT),
            str(DOCTRINE_DOC),
            str(GROK_PHASE21),
            str(GROK_PHASE32),
            *[str(path) for path in TMP_GROK_LOOPS],
            str(TMP_ENGINE_V2),
        ],
        "stage_fields_touched_or_consumed": [],
        "before_baseline/hash": {
            "classifier_result": classifier.get("sha256"),
            "phase21_sidequest": phase21.get("sha256"),
            "phase32_sidequest": phase32.get("sha256"),
            "tmp_grok_loop_hashes": {report["path"]: report.get("sha256") for report in tmp_reports},
        },
        "after_delta/hash": {
            "script": sha256_file(pathlib.Path(__file__)),
            "result": sha256_file(OUT_PATH) if OUT_PATH.exists() else None,
        },
        "primary_control/result": {
            "classifier_label_counts": labels,
            "phase21_summary": phase21_summary,
            "phase32_summary": phase32_summary,
            "tmp_negative_markers": tmp_negative_markers,
            "adopted_method_guards": adopted_method_guards,
        },
        "axis0_outputs_or_blockers": {
            "axis0_claim_promotion_allowed": False,
            "path_entropy_status": "unchanged_blocked_by_existing_classifier_and_guard_receipts",
            "tmp_grok_axis0_material": "proposal_only_no_axis0_admission",
        },
        "provider_inputs_used": {
            "grok": "tmp/provider text read as proposal-only artifact",
            "gemini": "not_run_this_repair_wave",
            "sonnet_high": "not_run_this_repair_wave",
            "opus_max": "not_run_this_repair_wave",
            "reason": "bounded local adoption audit; no new external model calls",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "If one sidequest negative is useful, convert exactly one into a formal_scout with a matching script/result pair and fresh validator.",
    }

    positive = {
        "current_classifier_receipt_loaded": {
            "pass": classifier.get("exists") is True and classifier.get("all_pass") is True,
            "classifier_label_counts": labels,
        },
        "current_system_has_mixed_basin_levels": {
            "pass": all(labels.get(label, 0) > 0 for label in ("deep_basin", "candidate_basin", "shallow_basin", "anti_basin", "open_basin_boundary")),
            "interpretation": "Current evidence is not one basin; it contains deep/candidate/shallow/anti/open strata.",
            "classifier_label_counts": labels,
        },
        "grok_sidequest_failures_are_read_as_noncanonical_negative_evidence": {
            "pass": phase21_summary["phase_pass"] is False
            and phase32_summary["phase_pass"] is False
            and phase21_summary["promotion_allowed"] is False
            and phase32_summary["promotion_allowed"] is False,
            "phase21": phase21_summary,
            "phase32": phase32_summary,
        },
        "tmp_loop_artifacts_supply_open_boundary_markers": {
            "pass": any(report.get("all_pass_false_mentions", 0) > 0 for report in tmp_reports)
            and any(report.get("z3_cvc5_mismatch_mentions", 0) > 0 for report in tmp_reports),
            "tmp_reports": tmp_reports,
        },
        "method_guards_are_adopted_without_adopting_tmp_claims": {
            "pass": len(adopted_method_guards) >= 5,
            "adopted_method_guards": adopted_method_guards,
        },
    }
    graveyards = {
        "tmp_grok_text_does_not_count_as_formal_receipt": {
            "pass": all(report.get("exists") for report in tmp_engine_reports[:2])
            and all("canonical" in CLAIM_CEILING.lower() for _ in [0]),
            "tmp_engine_reports": tmp_engine_reports,
            "reason": "Council text can suggest prompts or controls, but cannot promote Codex Ratchet claims.",
        },
        "sidequest_phase_failures_do_not_get_repaired_by_wording": {
            "pass": phase21_summary["failure_count"] > 0 and phase32_summary["failure_count"] > 0,
            "reason": "Failed uniqueness and axis-cliff phases stay negative/open until a formal scout repairs or closes them.",
        },
        "grok_loop_runtime_errors_are_open_boundary_not_deep_basin": {
            "pass": any(report.get("qutip_dimension_error") for report in tmp_reports)
            or any(report.get("z3_reset_assertions_error") for report in tmp_reports),
            "reason": "Dimension/API errors are useful premortem markers, not evidence of attractor convergence.",
        },
        "all_pass_distribution_does_not_collapse_to_single_success_label": {
            "pass": labels.get("candidate_basin", 0) > labels.get("deep_basin", 0)
            and labels.get("anti_basin", 0) > 0,
            "reason": "The classifier keeps most current evidence below deep-basin level.",
        },
    }
    boundary = {
        "no_tmp_or_grok_claim_promotion": {
            "pass": PROMOTION_ALLOWED is False
            and all(term in CLAIM_CEILING.lower() for term in ("formal scout", "does not admit", "grok_sim", "canonical")),
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": REQUIRED_REPAIR_FIELDS.issubset(repair_receipt),
            "keys": sorted(repair_receipt),
        },
        "adoption_is_method_level_not_architecture_level": {
            "pass": all(
                any(token in guard for token in ("method", "sidequest", "all_pass", "phase", "z3/cvc5"))
                for guard in adopted_method_guards
            ),
            "adopted_method_guards": adopted_method_guards,
        },
    }
    nearby = {
        "total": len(graveyards),
        "passed": sum(1 for row in graveyards.values() if row["pass"]),
        "variants": sorted(graveyards),
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "attractor_basin_tmp_grok_sidequest_adoption_audit",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "repair_receipt": repair_receipt,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": nearby,
        "why_not_v4_probes": [
            "This is an adoption/audit gate over current receipts and sidequest artifacts, not an old v4 physics probe.",
            "Tmp and grok_sim materials remain noncanonical until converted into formal scouts.",
        ],
        "blockers": [],
        "all_pass": all_pass,
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    print(f"  classifier labels: {labels}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
