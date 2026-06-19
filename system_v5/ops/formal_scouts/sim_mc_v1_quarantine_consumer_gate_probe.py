#!/usr/bin/env python3
"""Consumer gate for the quarantined M(C) v1 scratch receipt."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from receipt_schema import validate_result_path  # noqa: E402


OBJECT_ID = "mc_v1_quarantine_consumer_gate_probe"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/sim_mc_v1_quarantine_consumer_gate_probe.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/mc_v1_quarantine_consumer_gate_probe_results.json"
MC_V1_RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json"
MC_V1_SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_mc_v1_admissibility_object_envelope.py"

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "classical"
SIM_EXECUTION_KIND = sim_execution_kind
evidence_level = "consumer_gate"
EVIDENCE_LEVEL = evidence_level

CLAIM_CEILING = (
    "Consumer gate only: M(C) v1 remains quarantined scratch_diagnostic fuel. "
    "Passing this probe does not admit M(C), Stage 4, same-carrier geometry, "
    "topology readout, AI/GNN readout, bridge, Axis0, physics, manifold, or "
    "any stronger consumer."
)
NEXT_LEGO_TARGET = (
    "Only quarantined_scratch_fuel or one exact_tool_lego_fit_probe_after_consumer_gate "
    "may cite this receipt; no stage movement is allowed."
)
PROMOTION_CONDITION = (
    "No direct promotion path. A later consumer must pass its own exact field, "
    "control, tool-lego, receipt-schema, and stage gates before any stronger claim."
)
BLOCKED_UNTIL = (
    "A dedicated future admission packet names the exact consumer, exact M(C) field, "
    "negative controls, source/result receipts, and stage-gate evidence."
)
DEMOTION_CONDITION = (
    "Demote this gate if the v1 receipt stops validating, loses scratch quarantine "
    "flags, loses current-schema field coverage, allows stage movement, or exposes "
    "any strong downstream consumer."
)

STRONG_CONSUMERS = [
    "M(C)_system_fit",
    "same_carrier_geometry",
    "topology_readout_promotion",
    "AI_GNN_readout_promotion",
    "bridge",
    "Axis0",
    "physics",
    "manifold_admission",
]
ALLOWED_CONSUMERS = [
    "quarantined_scratch_fuel",
    "exact_tool_lego_fit_probe_after_consumer_gate",
]
REQUIRED_FIELD_COVERAGE = [
    "S",
    "C",
    "M/P",
    "~_M",
    "Adm_C",
    "composition",
    "bracketing",
    "local_path_rules",
    "carrier_readout_map",
    "axes_A_i",
    "controls",
    "receipts",
    "ceiling",
]
OUT_OF_SCOPE = STRONG_CONSUMERS

TOOL_MANIFEST = {
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing and writing of the consumed M(C) v1 receipt and this gate receipt",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic repo path binding for source and result receipts",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive sha256 pinning for gate source and consumed M(C) v1 source/result",
    },
    "time": {
        "tried": True,
        "used": True,
        "reason": "supportive run timing for the executable consumer gate receipt",
    },
    "receipt_schema": {
        "tried": True,
        "used": True,
        "reason": "supportive in-process validation against the current repo receipt schema",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "time": "supportive",
    "receipt_schema": "supportive",
}


def sha256_file(path: pathlib.Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: pathlib.Path) -> tuple[dict[str, Any], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"{exc.__class__.__name__}: {exc}"
    if not isinstance(payload, dict):
        return {}, f"non-object JSON payload: {type(payload).__name__}"
    return payload, None


def check(name: str, passed: bool, *, expected: Any, observed: Any, reason: str) -> dict[str, Any]:
    return {
        "name": name,
        "pass": bool(passed),
        "expected": expected,
        "observed": observed,
        "reason": reason,
    }


def section_pass(section: dict[str, dict[str, Any]]) -> bool:
    return all(row["pass"] is True for row in section.values())


def build_result() -> dict[str, Any]:
    started_ns = time.perf_counter_ns()
    mc_payload, load_error = load_json(MC_V1_RESULT_PATH)
    default_validation = validate_result_path(MC_V1_RESULT_PATH, root=ROOT)
    strict_validation = validate_result_path(
        MC_V1_RESULT_PATH,
        root=ROOT,
        strict_scope=True,
        require_run_boundary=True,
    )

    out_of_scope = set(mc_payload.get("out_of_scope") or [])
    coverage_summary = mc_payload.get("M_C_v1_field_coverage_summary") or {}
    present_fields = set(coverage_summary.get("present_in_object") or [])
    missing_fields = sorted(set(REQUIRED_FIELD_COVERAGE) - present_fields)
    extra_external = list(coverage_summary.get("still_external") or [])
    mc_source_path = pathlib.Path(str(mc_payload.get("source_path") or MC_V1_SOURCE_PATH))
    claimed_mc_source_sha = mc_payload.get("source_sha256")
    current_mc_source_sha = sha256_file(mc_source_path)

    consumer_policy = {
        "eligible_consumers": ALLOWED_CONSUMERS,
        "allowed_next_uses": ALLOWED_CONSUMERS,
        "blocked_consumers": STRONG_CONSUMERS,
        "blocked_downstream_consumers": STRONG_CONSUMERS,
        "stage_movement_allowed": False,
        "stage_after_gate": "unchanged",
        "stage4_unlock_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
    }

    positive = {
        "mc_v1_receipt_exists": check(
            "mc_v1_receipt_exists",
            MC_V1_RESULT_PATH.exists(),
            expected=True,
            observed=MC_V1_RESULT_PATH.exists(),
            reason="A consumer gate can only consume an on-disk v1 result receipt.",
        ),
        "mc_v1_receipt_json_loaded": check(
            "mc_v1_receipt_json_loaded",
            load_error is None,
            expected=None,
            observed=load_error,
            reason="The consumed receipt must be parseable JSON.",
        ),
        "receipt_schema_default_validation": check(
            "receipt_schema_default_validation",
            default_validation.get("ok") is True,
            expected=True,
            observed=default_validation.get("hard_findings"),
            reason="The v1 receipt must pass the current default receipt schema.",
        ),
        "receipt_schema_strict_boundary_validation": check(
            "receipt_schema_strict_boundary_validation",
            strict_validation.get("ok") is True,
            expected=True,
            observed=strict_validation.get("hard_findings"),
            reason="The v1 receipt must expose strict scope and run-boundary metadata.",
        ),
        "classification_scratch_diagnostic": check(
            "classification_scratch_diagnostic",
            mc_payload.get("classification") == "scratch_diagnostic",
            expected="scratch_diagnostic",
            observed=mc_payload.get("classification"),
            reason="The consumed object remains scratch fuel only.",
        ),
        "mc_v1_all_pass_true": check(
            "mc_v1_all_pass_true",
            mc_payload.get("all_pass") is True,
            expected=True,
            observed=mc_payload.get("all_pass"),
            reason="The consumed receipt must have passed its own bounded checks.",
        ),
        "promotion_allowed_false": check(
            "promotion_allowed_false",
            mc_payload.get("promotion_allowed") is False,
            expected=False,
            observed=mc_payload.get("promotion_allowed"),
            reason="The consumed receipt must not authorize promotion.",
        ),
        "formal_admission_allowed_false": check(
            "formal_admission_allowed_false",
            mc_payload.get("formal_admission_allowed") is False,
            expected=False,
            observed=mc_payload.get("formal_admission_allowed"),
            reason="The consumed receipt must not authorize formal admission.",
        ),
        "current_schema_field_coverage_present": check(
            "current_schema_field_coverage_present",
            not missing_fields,
            expected=[],
            observed=missing_fields,
            reason="The current-schema M(C) fields must be present in the v1 object.",
        ),
        "current_schema_still_external_empty": check(
            "current_schema_still_external_empty",
            extra_external == [],
            expected=[],
            observed=extra_external,
            reason="Current-schema field coverage must not leave externalized fields.",
        ),
        "source_sha256_matches_current": check(
            "source_sha256_matches_current",
            bool(claimed_mc_source_sha) and current_mc_source_sha == claimed_mc_source_sha,
            expected=claimed_mc_source_sha,
            observed=current_mc_source_sha,
            reason="The consumed source hash must still pin the on-disk v1 source.",
        ),
    }

    negative = {
        "all_strong_consumers_in_v1_out_of_scope": check(
            "all_strong_consumers_in_v1_out_of_scope",
            set(STRONG_CONSUMERS) <= out_of_scope,
            expected=STRONG_CONSUMERS,
            observed=sorted(out_of_scope),
            reason="The consumed v1 receipt must already fence every strong consumer.",
        ),
        "all_strong_consumers_blocked_by_gate_policy": check(
            "all_strong_consumers_blocked_by_gate_policy",
            set(STRONG_CONSUMERS) <= set(consumer_policy["blocked_consumers"]),
            expected=STRONG_CONSUMERS,
            observed=consumer_policy["blocked_consumers"],
            reason="This gate must explicitly block every strong consumer.",
        ),
        "no_strong_consumer_is_eligible": check(
            "no_strong_consumer_is_eligible",
            set(STRONG_CONSUMERS).isdisjoint(set(consumer_policy["eligible_consumers"])),
            expected=[],
            observed=sorted(set(STRONG_CONSUMERS) & set(consumer_policy["eligible_consumers"])),
            reason="No strong consumer can be listed as eligible after this gate.",
        ),
        "no_admission_flags_reintroduced": check(
            "no_admission_flags_reintroduced",
            promotion_allowed is False and formal_admission_allowed is False,
            expected={"promotion_allowed": False, "formal_admission_allowed": False},
            observed={
                "promotion_allowed": promotion_allowed,
                "formal_admission_allowed": formal_admission_allowed,
            },
            reason="The consumer gate itself must remain non-promotional.",
        ),
    }

    boundary = {
        "eligible_consumers_exactly_narrow": check(
            "eligible_consumers_exactly_narrow",
            consumer_policy["eligible_consumers"] == ALLOWED_CONSUMERS,
            expected=ALLOWED_CONSUMERS,
            observed=consumer_policy["eligible_consumers"],
            reason="Only quarantined scratch use and one exact future tool-lego fit shape are allowed.",
        ),
        "allowed_next_uses_exactly_narrow": check(
            "allowed_next_uses_exactly_narrow",
            consumer_policy["allowed_next_uses"] == ALLOWED_CONSUMERS,
            expected=ALLOWED_CONSUMERS,
            observed=consumer_policy["allowed_next_uses"],
            reason="The allowed future uses must not widen beyond the consumer gate.",
        ),
        "stage_movement_forbidden": check(
            "stage_movement_forbidden",
            consumer_policy["stage_movement_allowed"] is False,
            expected=False,
            observed=consumer_policy["stage_movement_allowed"],
            reason="Passing this gate cannot move the ladder stage.",
        ),
        "stage4_unlock_forbidden": check(
            "stage4_unlock_forbidden",
            consumer_policy["stage4_unlock_allowed"] is False,
            expected=False,
            observed=consumer_policy["stage4_unlock_allowed"],
            reason="Passing this gate cannot unlock Stage 4 or any adjacent promotion.",
        ),
        "claim_ceiling_names_no_promotion": check(
            "claim_ceiling_names_no_promotion",
            "does not admit M(C), Stage 4" in CLAIM_CEILING and "manifold" in CLAIM_CEILING,
            expected="no admission and no Stage 4/manifold language",
            observed=CLAIM_CEILING,
            reason="The gate ceiling must be visible to downstream consumers.",
        ),
    }

    elapsed_ns = time.perf_counter_ns() - started_ns
    all_pass = section_pass(positive) and section_pass(negative) and section_pass(boundary)
    result: dict[str, Any] = {
        "schema_version": "formal_scout_result_v1",
        "name": OBJECT_ID,
        "object_id": OBJECT_ID,
        "classification": classification,
        "sim_execution_kind": sim_execution_kind,
        "evidence_level": evidence_level,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "all_pass": all_pass,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "elapsed_ns": elapsed_ns,
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": NEXT_LEGO_TARGET,
        "promotion_condition": PROMOTION_CONDITION,
        "blocked_until": BLOCKED_UNTIL,
        "demotion_condition": DEMOTION_CONDITION,
        "out_of_scope": OUT_OF_SCOPE,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "consumer_policy": consumer_policy,
        "eligible_consumers": consumer_policy["eligible_consumers"],
        "allowed_next_uses": consumer_policy["allowed_next_uses"],
        "blocked_consumers": consumer_policy["blocked_consumers"],
        "blocked_downstream_consumers": consumer_policy["blocked_downstream_consumers"],
        "stage_movement_allowed": consumer_policy["stage_movement_allowed"],
        "stage_after_gate": consumer_policy["stage_after_gate"],
        "stage4_unlock_allowed": consumer_policy["stage4_unlock_allowed"],
        "M_C_v1_field_coverage_summary": {
            "required": REQUIRED_FIELD_COVERAGE,
            "present_in_consumed_object": sorted(present_fields),
            "missing": missing_fields,
            "still_external": extra_external,
        },
        "source_result_sha256s": {
            "gate_source_sha256": sha256_file(SOURCE_PATH),
            "consumed_mc_v1_source_path": str(mc_source_path),
            "consumed_mc_v1_source_sha256_claimed": claimed_mc_source_sha,
            "consumed_mc_v1_source_sha256_current": current_mc_source_sha,
            "consumed_mc_v1_result_path": str(MC_V1_RESULT_PATH),
            "consumed_mc_v1_result_sha256": sha256_file(MC_V1_RESULT_PATH),
            "consumed_mc_v1_result_payload_sha256": stable_sha256(mc_payload) if mc_payload else None,
        },
        "receipt_schema_validation": {
            "default": default_validation,
            "strict_scope_and_run_boundary": strict_validation,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }
    result["result_payload_sha256_excluding_this_field"] = stable_sha256(result)
    return result


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"positive={sum(1 for row in result['positive'].values() if row['pass'])}/{len(result['positive'])} "
        f"negative={sum(1 for row in result['negative'].values() if row['pass'])}/{len(result['negative'])} "
        f"boundary={sum(1 for row in result['boundary'].values() if row['pass'])}/{len(result['boundary'])} "
        f"blocked_consumers={len(result['blocked_consumers'])} "
        f"allowed_consumers={len(result['eligible_consumers'])} "
        f"stage_movement_allowed={str(result['stage_movement_allowed']).lower()}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
