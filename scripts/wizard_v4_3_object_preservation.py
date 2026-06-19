#!/usr/bin/env python3
"""Wizard v4.3 object-preservation validator and self-test loop.

This is an additive guard for Wizard v4.2. It does not replace the v4.2
council runner. It validates whether a task packet preserves a hard primary
object while still allowing typed lateral exploration through adapters, probes,
analogies, and proxies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "wizard_v4_3_primary_object_card_v1"
ALLOWED_MAPPING_TYPES = {"adapter", "probe", "analogy", "proxy"}
PROMOTABLE_MAPPING_TYPES = {"adapter", "probe"}
REQUIRED_CARD_FIELDS = {
    "object_name",
    "object_type",
    "object_statement",
    "object_statement_sha256",
    "source_anchors",
    "plain_language_definition",
    "native_terms",
    "weirdness_signature",
    "first_class_fields",
    "domain",
    "codomain_or_output",
    "allowed_operations",
    "required_invariants",
    "forbidden_substitutions",
    "negative_controls",
    "adapter_policy",
    "promotion_locks",
    "blocked_downstream_consumers",
    "artifact_surface",
}
REQUIRED_MAPPING_FIELDS = {
    "label",
    "use_type",
    "target",
    "preserves",
    "loses",
    "preconditions",
    "kill_control",
    "promotion_allowed",
}
REQUIRED_LOOP_PHASES = {"build", "premortem", "repair", "selftest"}
REQUIRED_EVIDENCE_SPINE_FIELDS = {
    "wizard_runtime",
    "source_math_locks",
    "sim_audit_receipts",
    "claude_pattern_cards",
    "claim_ceiling",
    "blocked_consumers",
}
REQUIRED_EVIDENCE_LOCK_FIELDS = {"path", "preserves", "status"}
REQUIRED_AUDIT_RECEIPT_FIELDS = {"path", "claim_ceiling", "blocked_consumers"}
REQUIRED_PATTERN_CARD_FIELDS = {
    "source_path",
    "pattern_name",
    "port_as",
    "target_path",
    "authority_reason",
    "minimal_test",
}
REQUIRED_METHOD_CONTRACT_FIELDS = {
    "question_is_not_authorization",
    "order_check_separate",
    "baseline_preservation",
    "falsifier_first",
    "feynman_testability",
    "synthesis_refusal",
    "human_offload",
}
RETROCAUSAL_REQUIRED_FIELDS = {
    "branch_states",
    "event_x",
    "shells",
    "shell_radius_r",
    "shell_orientation",
    "future_continuations",
    "compatibility_weights",
    "compression_map",
    "present_survivor",
    "outward_record",
}
RETROCAUSAL_REQUIRED_INVARIANT_TERMS = {
    "future",
    "inward",
    "past",
    "outward",
    "compatibility",
    "survivor",
}
GATED_V42_SCHEMA_VERSION = "wizard_v4_3_gated_v4_2_receipt_v1"
V42_PACKET_ROOT = Path.home() / "wiki/wizard/packet-v4-2-current"
V42_BOOT_REQUIREMENTS = [
    ("packet_manifest", V42_PACKET_ROOT / "PACKET_MANIFEST_v4_2.md", "canonical-runtime-pointer"),
    ("compact_mmm", V42_PACKET_ROOT / "mmm/COMPACT_MMM_v4_2.md", "canonical-runtime"),
    (
        "mini_mmm_registry",
        V42_PACKET_ROOT / "mmm/mini/MEMBER_MINI_MMM_REGISTRY_v4_2.md",
        "canonical-runtime",
    ),
    ("runtime", V42_PACKET_ROOT / "WIZARD_v4_2.md", "canonical-runtime"),
    ("skills_manifest", V42_PACKET_ROOT / "skills/SKILLS_MANIFEST_v4_2.md", "canonical-skill"),
    (
        "v4_3_overlay",
        V42_PACKET_ROOT / "mmm/SALIENCY_TRANCHE_02_V4_3_OBJECT_PRESERVATION_MAINTENANCE_CANDIDATE.md",
        "reference-only",
    ),
]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    message: str


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _as_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_as_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {_as_text(val)}" for key, val in value.items())
    return str(value)


def _is_nonempty_sequence(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _contains_any(text: str, terms: set[str]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def _contains_all(text: str, terms: set[str]) -> set[str]:
    lowered = text.lower()
    return {term for term in terms if term.lower() not in lowered}


def _append(errors: list[Finding], severity: str, code: str, message: str) -> None:
    errors.append(Finding(severity=severity, code=code, message=message))


def validate_primary_object_card(card: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    missing = sorted(REQUIRED_CARD_FIELDS - card.keys())
    if missing:
        _append(findings, "error", "card.missing_fields", "missing primary_object_card fields: " + ", ".join(missing))
        return findings

    for field in (
        "object_name",
        "object_type",
        "object_statement",
        "object_statement_sha256",
        "plain_language_definition",
        "domain",
        "codomain_or_output",
        "adapter_policy",
        "artifact_surface",
    ):
        if not _is_nonempty_string(card.get(field)):
            _append(findings, "error", f"card.empty_{field}", f"{field} must be a non-empty string")

    if _is_nonempty_string(card.get("object_statement")) and _is_nonempty_string(card.get("object_statement_sha256")):
        actual_hash = hashlib.sha256(str(card["object_statement"]).encode("utf-8")).hexdigest()
        if card["object_statement_sha256"] != actual_hash:
            _append(
                findings,
                "error",
                "card.object_statement_hash_mismatch",
                "object_statement_sha256 must match object_statement",
            )

    if len(str(card.get("plain_language_definition", "")).split()) < 35:
        _append(
            findings,
            "error",
            "card.definition_too_short",
            "plain_language_definition must explain the object, not only name it",
        )

    native_terms = card.get("native_terms")
    if not isinstance(native_terms, dict) or not native_terms:
        _append(findings, "error", "card.native_terms_empty", "native_terms must define project-native terms")
    else:
        for term, definition in native_terms.items():
            if not _is_nonempty_string(term) or len(str(definition).split()) < 8:
                _append(findings, "error", "card.native_term_underdefined", f"native term {term!r} is underdefined")
        jk_key = next((key for key in native_terms if "jk" in key.lower() and "fuzz" in key.lower()), None)
        if jk_key and not _contains_any(_as_text(native_terms[jk_key]), {"future", "possibil", "continuation"}):
            _append(
                findings,
                "error",
                "card.jk_fuzz_not_explained",
                "jk fuzz must be explained as future possibilities or continuations, not left as a label",
            )

    source_anchors = card.get("source_anchors")
    if not isinstance(source_anchors, list) or not source_anchors:
        _append(findings, "error", "card.source_anchors_empty", "source_anchors must be a non-empty list")
    else:
        for index, anchor in enumerate(source_anchors):
            if not isinstance(anchor, dict):
                _append(findings, "error", "card.source_anchor_not_object", f"source_anchors[{index}] must be an object")
                continue
            for field in ("surface", "reference", "quote_or_summary"):
                if not _is_nonempty_string(anchor.get(field)):
                    _append(
                        findings,
                        "error",
                        "card.source_anchor_underdefined",
                        f"source_anchors[{index}].{field} must be non-empty",
                    )

    weirdness_signature = card.get("weirdness_signature")
    if not isinstance(weirdness_signature, list) or len(weirdness_signature) < 3:
        _append(
            findings,
            "error",
            "card.weirdness_signature_too_small",
            "weirdness_signature must name at least three hard-to-preserve features",
        )
    else:
        for index, feature in enumerate(weirdness_signature):
            if len(str(feature).split()) < 3:
                _append(
                    findings,
                    "error",
                    "card.weirdness_feature_underdefined",
                    f"weirdness_signature[{index}] must explain a feature, not just name it",
                )

    for field in (
        "first_class_fields",
        "allowed_operations",
        "required_invariants",
        "forbidden_substitutions",
        "negative_controls",
        "promotion_locks",
        "blocked_downstream_consumers",
    ):
        if not _is_nonempty_sequence(card.get(field)):
            _append(findings, "error", f"card.empty_{field}", f"{field} must be a non-empty list")

    object_type = str(card.get("object_type", "")).lower()
    if object_type == "retrocausal_possibility_field":
        fields_text = _as_text(card.get("first_class_fields"))
        missing_fields = {field for field in RETROCAUSAL_REQUIRED_FIELDS if field.lower() not in fields_text.lower()}
        if missing_fields:
            _append(
                findings,
                "error",
                "card.retrocausal_missing_fields",
                "retrocausal_possibility_field is missing first-class fields: " + ", ".join(sorted(missing_fields)),
            )
        invariant_text = _as_text(card.get("required_invariants"))
        missing_terms = _contains_all(invariant_text, RETROCAUSAL_REQUIRED_INVARIANT_TERMS)
        if missing_terms:
            _append(
                findings,
                "error",
                "card.retrocausal_missing_invariants",
                "retrocausal invariants must preserve: " + ", ".join(sorted(missing_terms)),
            )

    forbidden_text = _as_text(card.get("forbidden_substitutions"))
    if not _contains_any(forbidden_text, {"proxy", "analogy", "scalar", "label"}):
        _append(
            findings,
            "warning",
            "card.weak_forbidden_substitutions",
            "forbidden_substitutions should explicitly block proxy or label replacement",
        )
    return findings


def validate_lateral_mappings(
    mappings: Any,
    *,
    forbidden_substitutions: list[Any],
) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(mappings, list) or not mappings:
        return [Finding("error", "mappings.empty", "lateral_mappings must be a non-empty list")]

    forbidden_texts = [str(item).lower() for item in forbidden_substitutions]
    for index, mapping in enumerate(mappings):
        label = f"lateral_mappings[{index}]"
        if not isinstance(mapping, dict):
            _append(findings, "error", "mapping.not_object", f"{label} must be an object")
            continue
        missing = sorted(REQUIRED_MAPPING_FIELDS - mapping.keys())
        if missing:
            _append(findings, "error", "mapping.missing_fields", f"{label} missing fields: " + ", ".join(missing))
            continue

        use_type = mapping.get("use_type")
        if use_type not in ALLOWED_MAPPING_TYPES:
            _append(
                findings,
                "error",
                "mapping.bad_use_type",
                f"{label}.use_type must be one of {', '.join(sorted(ALLOWED_MAPPING_TYPES))}",
            )
            continue

        if not isinstance(mapping.get("promotion_allowed"), bool):
            _append(findings, "error", "mapping.bad_promotion_flag", f"{label}.promotion_allowed must be boolean")

        for field in ("label", "target", "kill_control"):
            if not _is_nonempty_string(mapping.get(field)):
                _append(findings, "error", f"mapping.empty_{field}", f"{label}.{field} must be non-empty")
        for field in ("preserves", "loses", "preconditions"):
            if not _is_nonempty_sequence(mapping.get(field)):
                _append(findings, "error", f"mapping.empty_{field}", f"{label}.{field} must be a non-empty list")

        if mapping.get("promotion_allowed") is True and use_type not in PROMOTABLE_MAPPING_TYPES:
            article = "an" if str(use_type)[0].lower() in {"a", "e", "i", "o", "u"} else "a"
            _append(
                findings,
                "error",
                "mapping.unpromotable_type_promoted",
                f"{label} is {article} {use_type}; proxies and analogies cannot be promoted into object claims",
            )

        target_text = (str(mapping.get("label", "")) + " " + str(mapping.get("target", ""))).lower()
        if mapping.get("promotion_allowed") is True:
            for forbidden in forbidden_texts:
                if forbidden and forbidden in target_text:
                    _append(
                        findings,
                        "error",
                        "mapping.promotes_forbidden_substitution",
                        f"{label} promotes forbidden substitution {forbidden!r}",
                    )

        if use_type in {"analogy", "proxy"} and not _as_text(mapping.get("loses")).strip():
            _append(
                findings,
                "error",
                "mapping.proxy_without_loss",
                f"{label} must say what the {use_type} loses",
            )
    return findings


def validate_constraint_bands(value: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(value, dict):
        return [Finding("error", "constraint_bands.missing", "constraint_bands must be an object")]
    root = value.get("root_constraints")
    extended = value.get("extended_constraints")
    if not _is_nonempty_sequence(root):
        _append(findings, "error", "constraint_bands.empty_root", "root_constraints must be a non-empty list")
    if not _is_nonempty_sequence(extended):
        _append(findings, "error", "constraint_bands.empty_extended", "extended_constraints must be a non-empty list")
    if _is_nonempty_sequence(root) and _is_nonempty_sequence(extended):
        overlap = {str(item).lower() for item in root} & {str(item).lower() for item in extended}
        if overlap:
            _append(
                findings,
                "error",
                "constraint_bands.root_extended_overlap",
                "root and extended constraints must not be collapsed together: " + ", ".join(sorted(overlap)),
            )
    return findings


def validate_exploration_contract(value: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(value, dict):
        return [Finding("error", "exploration_contract.missing", "exploration_contract must be an object")]
    wildcard_lanes_min = value.get("wildcard_lanes_min")
    if not isinstance(wildcard_lanes_min, int) or wildcard_lanes_min < 1:
        _append(
            findings,
            "error",
            "exploration_contract.no_wildcard_lane",
            "wild exploration requires wildcard_lanes_min >= 1",
        )
    if not _is_nonempty_sequence(value.get("fixation_breakers")):
        _append(
            findings,
            "error",
            "exploration_contract.no_fixation_breakers",
            "fixation_breakers must name how the loop escapes one proxy or one mild suggestion",
        )
    if not _is_nonempty_sequence(value.get("lateral_lane_types")):
        _append(
            findings,
            "error",
            "exploration_contract.no_lateral_lane_types",
            "lateral_lane_types must name allowed lateral modes",
        )
    return findings


def validate_loop_contract(value: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(value, dict):
        return [Finding("error", "loop_contract.missing", "loop_contract must be an object")]
    phases = value.get("phases")
    if not _is_nonempty_sequence(phases):
        _append(findings, "error", "loop_contract.empty_phases", "loop_contract.phases must be a non-empty list")
    else:
        missing = REQUIRED_LOOP_PHASES - {str(phase) for phase in phases}
        if missing:
            _append(
                findings,
                "error",
                "loop_contract.missing_required_phase",
                "loop_contract.phases missing: " + ", ".join(sorted(missing)),
            )
    max_loops = value.get("max_loops")
    if not isinstance(max_loops, int) or max_loops < 1:
        _append(findings, "error", "loop_contract.bad_max_loops", "loop_contract.max_loops must be an integer >= 1")
    if not _is_nonempty_string(value.get("stop_condition")):
        _append(findings, "error", "loop_contract.empty_stop_condition", "loop_contract.stop_condition must be non-empty")
    if not _is_nonempty_string(value.get("repair_rule")):
        _append(findings, "error", "loop_contract.empty_repair_rule", "loop_contract.repair_rule must be non-empty")
    return findings


def validate_method_contracts(value: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(value, dict):
        return [Finding("error", "method_contracts.missing", "method_contracts must be an object")]

    missing = sorted(REQUIRED_METHOD_CONTRACT_FIELDS - value.keys())
    if missing:
        _append(findings, "error", "method_contracts.missing_fields", "missing method_contracts fields: " + ", ".join(missing))
        return findings

    for field in sorted(REQUIRED_METHOD_CONTRACT_FIELDS):
        if not _is_nonempty_string(value.get(field)):
            _append(findings, "error", f"method_contracts.empty_{field}", f"method_contracts.{field} must be a non-empty string")

    contract_text = {field: str(value.get(field, "")).lower() for field in REQUIRED_METHOD_CONTRACT_FIELDS}
    if not all(term in contract_text["question_is_not_authorization"] for term in ("question", "authorization")):
        _append(
            findings,
            "error",
            "method_contracts.question_authorization_unclear",
            "question_is_not_authorization must say questions do not authorize implementation",
        )
    if not all(term in contract_text["order_check_separate"] for term in ("order", "separate")):
        _append(
            findings,
            "error",
            "method_contracts.order_check_unclear",
            "order_check_separate must require order to be checked separately from content",
        )
    if not all(term in contract_text["baseline_preservation"] for term in ("baseline", "preserve")):
        _append(
            findings,
            "error",
            "method_contracts.baseline_preservation_unclear",
            "baseline_preservation must preserve the visible/output baseline while runtime is debugged",
        )
    if not all(term in contract_text["falsifier_first"] for term in ("target", "falsifier", "check")) or not _contains_any(
        contract_text["falsifier_first"], {"killed", "open", "survived"}
    ):
        _append(
            findings,
            "error",
            "method_contracts.falsifier_first_incomplete",
            "falsifier_first must name target, falsifier, check, and killed/open/survived classification",
        )
    if not all(term in contract_text["feynman_testability"] for term in ("operation", "observable", "pass/fail")):
        _append(
            findings,
            "error",
            "method_contracts.feynman_testability_incomplete",
            "feynman_testability must name operation, observable, and pass/fail condition",
        )
    if not all(term in contract_text["synthesis_refusal"] for term in ("refuse", "merge")):
        _append(
            findings,
            "error",
            "method_contracts.synthesis_refusal_incomplete",
            "synthesis_refusal must name the merge it refuses",
        )
    if not all(term in contract_text["human_offload"] for term in ("resolve", "ask")):
        _append(
            findings,
            "error",
            "method_contracts.human_offload_incomplete",
            "human_offload must say resolvable work is resolved before asking the human",
        )
    return findings


def _validate_object_list(
    findings: list[Finding],
    items: Any,
    *,
    field: str,
    required_fields: set[str],
) -> None:
    if not isinstance(items, list):
        _append(findings, "error", f"evidence_spine.{field}_not_list", f"evidence_spine.{field} must be a list")
        return
    for index, item in enumerate(items):
        label = f"evidence_spine.{field}[{index}]"
        if not isinstance(item, dict):
            _append(findings, "error", f"evidence_spine.{field}_item_not_object", f"{label} must be an object")
            continue
        missing = sorted(required_fields - item.keys())
        if missing:
            _append(findings, "error", f"evidence_spine.{field}_missing_fields", f"{label} missing fields: " + ", ".join(missing))
            continue
        for required in sorted(required_fields):
            value = item.get(required)
            if isinstance(value, list):
                if not value:
                    _append(findings, "error", f"evidence_spine.{field}_empty_{required}", f"{label}.{required} must be non-empty")
            elif not _is_nonempty_string(value):
                _append(findings, "error", f"evidence_spine.{field}_empty_{required}", f"{label}.{required} must be non-empty")


def validate_evidence_spine(value: Any) -> list[Finding]:
    findings: list[Finding] = []
    if not isinstance(value, dict):
        return [Finding("error", "evidence_spine.missing", "evidence_spine must be an object")]

    missing = sorted(REQUIRED_EVIDENCE_SPINE_FIELDS - value.keys())
    if missing:
        _append(findings, "error", "evidence_spine.missing_fields", "missing evidence_spine fields: " + ", ".join(missing))
        return findings

    for field in ("wizard_runtime", "claim_ceiling"):
        if not _is_nonempty_string(value.get(field)):
            _append(findings, "error", f"evidence_spine.empty_{field}", f"evidence_spine.{field} must be a non-empty string")

    blocked = value.get("blocked_consumers")
    if not _is_nonempty_sequence(blocked):
        _append(
            findings,
            "error",
            "evidence_spine.empty_blocked_consumers",
            "evidence_spine.blocked_consumers must name consumers blocked by this packet",
        )

    source_locks = value.get("source_math_locks")
    audit_receipts = value.get("sim_audit_receipts")
    pattern_cards = value.get("claude_pattern_cards")
    _validate_object_list(findings, source_locks, field="source_math_locks", required_fields=REQUIRED_EVIDENCE_LOCK_FIELDS)
    _validate_object_list(findings, audit_receipts, field="sim_audit_receipts", required_fields=REQUIRED_AUDIT_RECEIPT_FIELDS)
    _validate_object_list(findings, pattern_cards, field="claude_pattern_cards", required_fields=REQUIRED_PATTERN_CARD_FIELDS)

    evidence_lists = [items for items in (source_locks, audit_receipts, pattern_cards) if isinstance(items, list)]
    if evidence_lists and not any(items for items in evidence_lists):
        _append(
            findings,
            "error",
            "evidence_spine.no_evidence_items",
            "at least one source lock, audit receipt, or Claude pattern card must be attached",
        )

    if isinstance(pattern_cards, list):
        for index, card in enumerate(pattern_cards):
            if not isinstance(card, dict):
                continue
            source_path = str(card.get("source_path", "")).lower()
            authority_reason = str(card.get("authority_reason", "")).lower()
            if ".claude" in source_path and not (
                "not authority" in authority_reason or "reference" in authority_reason
            ):
                _append(
                    findings,
                    "error",
                    "evidence_spine.claude_card_authority_unclear",
                    f"evidence_spine.claude_pattern_cards[{index}] must state Claude material is reference/not authority",
                )
    return findings


def validate_packet(packet: dict[str, Any]) -> dict[str, Any]:
    findings: list[Finding] = []
    if packet.get("schema_version") != SCHEMA_VERSION:
        _append(
            findings,
            "error",
            "packet.bad_schema_version",
            f"schema_version must be {SCHEMA_VERSION}",
        )

    card = packet.get("primary_object_card")
    if not isinstance(card, dict):
        _append(findings, "error", "packet.missing_primary_object_card", "primary_object_card must be an object")
        card = {}
    else:
        findings.extend(validate_primary_object_card(card))

    findings.extend(
        validate_lateral_mappings(
            packet.get("lateral_mappings"),
            forbidden_substitutions=card.get("forbidden_substitutions") if isinstance(card.get("forbidden_substitutions"), list) else [],
        )
    )
    findings.extend(validate_constraint_bands(packet.get("constraint_bands")))
    findings.extend(validate_exploration_contract(packet.get("exploration_contract")))
    findings.extend(validate_loop_contract(packet.get("loop_contract")))
    findings.extend(validate_method_contracts(packet.get("method_contracts")))
    findings.extend(validate_evidence_spine(packet.get("evidence_spine")))

    errors = [finding for finding in findings if finding.severity == "error"]
    warnings = [finding for finding in findings if finding.severity == "warning"]
    return {
        "ok": not errors,
        "schema_version": SCHEMA_VERSION,
        "errors": [asdict(finding) for finding in errors],
        "warnings": [asdict(finding) for finding in warnings],
        "checked": {
            "primary_object_card": isinstance(packet.get("primary_object_card"), dict),
            "lateral_mappings": len(packet.get("lateral_mappings") or []) if isinstance(packet.get("lateral_mappings"), list) else 0,
            "method_contracts": sorted(packet.get("method_contracts", {}).keys()) if isinstance(packet.get("method_contracts"), dict) else [],
            "evidence_spine": isinstance(packet.get("evidence_spine"), dict),
            "source_math_locks": len(packet.get("evidence_spine", {}).get("source_math_locks") or []) if isinstance(packet.get("evidence_spine"), dict) else 0,
            "sim_audit_receipts": len(packet.get("evidence_spine", {}).get("sim_audit_receipts") or []) if isinstance(packet.get("evidence_spine"), dict) else 0,
            "claude_pattern_cards": len(packet.get("evidence_spine", {}).get("claude_pattern_cards") or []) if isinstance(packet.get("evidence_spine"), dict) else 0,
        },
    }


def retrocausal_valid_packet() -> dict[str, Any]:
    object_statement = (
        "A finite shell-indexed field of possible futures compresses inward through compatibility into a present survivor, "
        "while the past-facing outward record preserves what survived."
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "primary_object_card": {
            "object_name": "RetrocausalPossibilityField",
            "object_type": "retrocausal_possibility_field",
            "object_statement": object_statement,
            "object_statement_sha256": hashlib.sha256(object_statement.encode("utf-8")).hexdigest(),
            "source_anchors": [
                {
                    "surface": "repo_doc",
                    "reference": "system_v5/docs/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md",
                    "quote_or_summary": "Literal shells carry possible futures inward; past records move outward.",
                }
            ],
            "plain_language_definition": (
                "A finite field of literal shell-indexed possible futures around event_x. "
                "Future continuations on Sigma_r compress inward through compatibility weights into a present survivor, "
                "while the past-facing outward_record preserves what survived. Entropy, Axis0, FEP, PEPS3D, and QIT cuts "
                "are readouts or carriers derived from this object, not replacements for it."
            ),
            "weirdness_signature": [
                "future possibilities are represented as first-class shell contents",
                "future compression is inward while past record is outward",
                "present survivor is derived from compatibility-weighted possible futures",
            ],
            "native_terms": {
                "shell": "Sigma_r is the finite spherical shell or stratum at radius/order r around event_x.",
                "jk fuzz": "The finite set of admissible future possibilities or continuations carried on the shell.",
                "present survivor": "The compressed state produced by compatibility-weighting possible futures.",
            },
            "first_class_fields": [
                "event_x",
                "shells",
                "shell_radius_r",
                "shell_orientation",
                "future_continuations",
                "branch_states",
                "compatibility_weights",
                "compression_map",
                "present_survivor",
                "outward_record",
            ],
            "domain": "finite shell stack, admissible continuation set, finite carrier state, active constraints",
            "codomain_or_output": "present survivor state, outward record, and derived readout bundle",
            "allowed_operations": [
                "compute compatibility weights",
                "compress future continuations into present survivor",
                "emit outward record",
                "derive entropy and QIT readouts after compression",
            ],
            "required_invariants": [
                "future continuations remain future-indexed",
                "future flow has inward orientation",
                "past record has outward orientation",
                "compatibility witnesses precede survivor compression",
                "survivor is derived from weighted futures",
            ],
            "forbidden_substitutions": [
                "Axis0 scalar proxy",
                "scalar entropy label",
                "FEP analogy",
                "PEPS3D carrier label",
            ],
            "negative_controls": [
                "remove shell orientation",
                "scramble future_continuations",
                "replace compatibility weights with uniform labels",
                "promote scalar entropy directly to Axis0",
            ],
            "adapter_policy": "Adapters may expose the object to QIT, PEPS3D, FEP, or graph tools only after naming what they preserve and lose.",
            "promotion_locks": [
                "Axis0 cannot be primary",
                "FEP cannot be primary",
                "entropy scalar cannot be primary",
            ],
            "blocked_downstream_consumers": [
                "Axis0 claim",
                "flux claim",
                "physics claim",
                "formal manifold admission",
            ],
            "artifact_surface": "repo receipt or JSON packet that records object card plus mappings plus validation output",
        },
        "lateral_mappings": [
            {
                "label": "PEPS3D spinor carrier",
                "use_type": "adapter",
                "target": "finite spinor/tensor carrier for shell branch states",
                "preserves": ["finite carrier", "cut readouts", "local boundary structure"],
                "loses": ["literal global shell unless shell metadata is carried"],
                "preconditions": ["shell metadata remains attached", "adapter output cannot become object"],
                "kill_control": "drop shell metadata; any Axis0 or gravity-model claim must fail",
                "promotion_allowed": True,
            },
            {
                "label": "Axis0 scalar",
                "use_type": "proxy",
                "target": "opening-vs-binding readout",
                "preserves": ["one polarity projection"],
                "loses": ["future possibility field", "compression map", "outward record"],
                "preconditions": ["Xi-like bridge already preserves shell field"],
                "kill_control": "if scalar passes after shell direction is removed, it is only a proxy",
                "promotion_allowed": False,
            },
            {
                "label": "FEP",
                "use_type": "analogy",
                "target": "prediction evidence posterior update pattern",
                "preserves": ["projection then correction pattern"],
                "loses": ["literal shell possibility ontology", "global possibility syncing"],
                "preconditions": ["must be derived as local expression after object is instantiated"],
                "kill_control": "if FEP update exists without possible future set, it cannot claim object preservation",
                "promotion_allowed": False,
            },
        ],
        "constraint_bands": {
            "root_constraints": ["finite carrier/probe/path set", "noncommuting or order-sensitive operation/control"],
            "extended_constraints": ["PEPS3D carrier anchor", "torch-native density", "chirality", "entropy readouts"],
        },
        "exploration_contract": {
            "wildcard_lanes_min": 1,
            "lateral_lane_types": ["adapter", "probe", "analogy", "proxy"],
            "fixation_breakers": ["demote repeated target to proxy unless primary fields are preserved"],
        },
        "loop_contract": {
            "phases": ["build", "premortem", "repair", "selftest"],
            "max_loops": 3,
            "repair_rule": "repair the first object-preservation error before adding new exploration lanes",
            "stop_condition": "all object-preservation errors pass or a named primary object field is impossible to instantiate",
        },
        "method_contracts": {
            "question_is_not_authorization": "A question asks for an answer; it is not authorization to implement unless the user explicitly says to do it.",
            "order_check_separate": "Any sequence or ordering claim must be checked separately from content correctness, with the order witness named.",
            "baseline_preservation": "When debugging runtime behavior, preserve the tuned visible/output baseline and debug the execution path underneath.",
            "falsifier_first": "A Popper pass names the target claim, strongest live falsifier, decisive check, and killed/open/survived classification before agreement.",
            "feynman_testability": "A Feynman pass names the operation, the observable measured, and the pass/fail condition.",
            "synthesis_refusal": "Synthesis must name distinct receipts and explicitly refuse the merge, sequence, or reframe it is not performing.",
            "human_offload": "Resolve with tools before asking; ask the human only for private, preference-bound, or unrecoverable information.",
        },
        "evidence_spine": {
            "wizard_runtime": "Wizard v4.3 object-preservation guard over Wizard v4.2 packet-current; v4.3 does not replace the v4.2 council runtime.",
            "source_math_locks": [
                {
                    "path": "system_v5/docs/WIZARD_V4_3_PRIMARY_OBJECT_PRESERVATION_SPEC_20260526.md",
                    "preserves": "primary object card before councils, sims, or follow-up loops claim object progress",
                    "status": "repo authority surface",
                }
            ],
            "sim_audit_receipts": [],
            "claude_pattern_cards": [
                {
                    "source_path": ".claude/skills/wizard-v43/SKILL.md",
                    "pattern_name": "object-preservation preflight before councils",
                    "port_as": "skill",
                    "target_path": "/Users/joshuaeisenhart/.codex/skills/three-council-wizard-v4-3/SKILL.md",
                    "authority_reason": "Claude material is reference only, not authority; Codex gates through AGENTS.md, CODEX.md, and this validator.",
                    "minimal_test": "python3 scripts/wizard_v4_3_object_preservation.py selftest",
                },
                {
                    "source_path": "/Users/joshuaeisenhart/.claude/CLAUDE.md",
                    "pattern_name": "question is not authorization",
                    "port_as": "validator_contract",
                    "target_path": "scripts/wizard_v4_3_object_preservation.py:method_contracts.question_is_not_authorization",
                    "authority_reason": "Claude material is reference only, not authority; Codex imports the mechanic through AGENTS.md/CODEX.md boundaries and this validator.",
                    "minimal_test": "python3 scripts/wizard_v4_3_object_preservation.py selftest",
                },
                {
                    "source_path": "/Users/joshuaeisenhart/.claude/CLAUDE.md",
                    "pattern_name": "order checked separately from content",
                    "port_as": "validator_contract",
                    "target_path": "scripts/wizard_v4_3_object_preservation.py:method_contracts.order_check_separate",
                    "authority_reason": "Claude material is reference only, not authority; Codex imports the mechanic through AGENTS.md/CODEX.md boundaries and this validator.",
                    "minimal_test": "python3 scripts/wizard_v4_3_object_preservation.py selftest",
                },
                {
                    "source_path": "/Users/joshuaeisenhart/.claude/CLAUDE.md",
                    "pattern_name": "baseline preservation while debugging runtime",
                    "port_as": "validator_contract",
                    "target_path": "scripts/wizard_v4_3_object_preservation.py:method_contracts.baseline_preservation",
                    "authority_reason": "Claude material is reference only, not authority; Codex imports the mechanic through AGENTS.md/CODEX.md boundaries and this validator.",
                    "minimal_test": "python3 scripts/wizard_v4_3_object_preservation.py selftest",
                },
                {
                    "source_path": "/Users/joshuaeisenhart/.claude/CLAUDE.md",
                    "pattern_name": "falsifier-first and testability method contracts",
                    "port_as": "validator_contract",
                    "target_path": "scripts/wizard_v4_3_object_preservation.py:method_contracts.falsifier_first+feynman_testability",
                    "authority_reason": "Claude material is reference only, not authority; Codex imports the mechanic through AGENTS.md/CODEX.md boundaries and this validator.",
                    "minimal_test": "python3 scripts/wizard_v4_3_object_preservation.py selftest",
                },
                {
                    "source_path": "/Users/joshuaeisenhart/.claude/CLAUDE.md",
                    "pattern_name": "synthesis names refused merge",
                    "port_as": "validator_contract",
                    "target_path": "scripts/wizard_v4_3_object_preservation.py:method_contracts.synthesis_refusal",
                    "authority_reason": "Claude material is reference only, not authority; Codex imports the mechanic through AGENTS.md/CODEX.md boundaries and this validator.",
                    "minimal_test": "python3 scripts/wizard_v4_3_object_preservation.py selftest",
                }
            ],
            "claim_ceiling": "object-preservation preflight only; no sim, physics, Axis0, flux, or formal admission claim",
            "blocked_consumers": [
                "v4.2 council progress claim without a passing object card",
                "sim/proof promotion without source lock and audit spine receipts",
            ],
        },
    }


def selftest_cases() -> list[tuple[str, dict[str, Any], bool]]:
    valid = retrocausal_valid_packet()

    axis_proxy_promoted = json.loads(json.dumps(valid))
    axis_proxy_promoted["lateral_mappings"][1]["promotion_allowed"] = True

    no_shell_fields = json.loads(json.dumps(valid))
    no_shell_fields["primary_object_card"]["first_class_fields"] = ["state", "entropy", "Axis0"]

    fep_promoted = json.loads(json.dumps(valid))
    fep_promoted["lateral_mappings"][2]["promotion_allowed"] = True

    no_wildcard = json.loads(json.dumps(valid))
    no_wildcard["exploration_contract"]["wildcard_lanes_min"] = 0

    root_extended_collapsed = json.loads(json.dumps(valid))
    root_extended_collapsed["constraint_bands"]["extended_constraints"].append("finite carrier/probe/path set")

    underdefined_jk = json.loads(json.dumps(valid))
    underdefined_jk["primary_object_card"]["native_terms"]["jk fuzz"] = "A project label."

    no_evidence_spine = json.loads(json.dumps(valid))
    no_evidence_spine.pop("evidence_spine")

    no_method_contracts = json.loads(json.dumps(valid))
    no_method_contracts.pop("method_contracts")

    weak_order_contract = json.loads(json.dumps(valid))
    weak_order_contract["method_contracts"]["order_check_separate"] = "Check the content."

    claude_authority_unclear = json.loads(json.dumps(valid))
    claude_authority_unclear["evidence_spine"]["claude_pattern_cards"][0]["authority_reason"] = (
        "Claude skill is the canonical behavior law for this workflow."
    )

    return [
        ("valid_retrocausal_packet", valid, True),
        ("reject_axis0_proxy_promotion", axis_proxy_promoted, False),
        ("reject_missing_shell_fields", no_shell_fields, False),
        ("reject_fep_analogy_promotion", fep_promoted, False),
        ("reject_no_wildcard_lateral_lane", no_wildcard, False),
        ("reject_root_extended_constraint_collapse", root_extended_collapsed, False),
        ("reject_underdefined_jk_fuzz", underdefined_jk, False),
        ("reject_missing_evidence_spine", no_evidence_spine, False),
        ("reject_missing_method_contracts", no_method_contracts, False),
        ("reject_weak_order_contract", weak_order_contract, False),
        ("reject_unclear_claude_authority", claude_authority_unclear, False),
    ]


def run_selftest() -> dict[str, Any]:
    cases = []
    all_passed = True
    for name, packet, expected_ok in selftest_cases():
        result = validate_packet(packet)
        passed = result["ok"] is expected_ok
        all_passed = all_passed and passed
        cases.append(
            {
                "name": name,
                "expected_ok": expected_ok,
                "actual_ok": result["ok"],
                "passed": passed,
                "errors": result["errors"],
                "warnings": result["warnings"],
            }
        )
    return {"ok": all_passed, "schema_version": SCHEMA_VERSION, "cases": cases}


def run_selftest_loop(max_loops: int) -> dict[str, Any]:
    loops: list[dict[str, Any]] = []
    final: dict[str, Any] | None = None
    for loop_index in range(1, max_loops + 1):
        result = run_selftest()
        loops.append(
            {
                "loop": loop_index,
                "ok": result["ok"],
                "failed_cases": [case["name"] for case in result["cases"] if not case["passed"]],
            }
        )
        final = result
        if result["ok"]:
            break
    return {
        "ok": bool(final and final["ok"]),
        "schema_version": SCHEMA_VERSION,
        "loops_completed": len(loops),
        "loops": loops,
        "final_selftest": final,
    }


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected JSON object")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _authority_status(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[:20]:
        if line.strip().startswith("authority_status:"):
            return line.split(":", 1)[1].strip().strip("`")
    return None


def check_v42_boot_surface() -> dict[str, Any]:
    files = []
    for label, path, expected_authority in V42_BOOT_REQUIREMENTS:
        authority = _authority_status(path)
        exists = path.exists() and path.is_file()
        files.append(
            {
                "label": label,
                "path": str(path),
                "exists": exists,
                "sha256": _file_sha256(path),
                "authority_status": authority,
                "expected_authority_status": expected_authority,
                "ok": exists and authority == expected_authority,
            }
        )
    return {
        "ok": all(item["ok"] for item in files),
        "packet_root": str(V42_PACKET_ROOT),
        "boot_order": [
            "PACKET_MANIFEST_v4_2.md",
            "mmm/COMPACT_MMM_v4_2.md",
            "mmm/mini/MEMBER_MINI_MMM_REGISTRY_v4_2.md",
            "WIZARD_v4_2.md",
            "skills/SKILLS_MANIFEST_v4_2.md",
            "mmm/SALIENCY_TRANCHE_02_V4_3_OBJECT_PRESERVATION_MAINTENANCE_CANDIDATE.md",
        ],
        "files": files,
    }


def run_v42_conformance(*, cwd: Path) -> dict[str, Any]:
    script = V42_PACKET_ROOT / "conformance/validate_v4_2_packet.py"
    if not script.exists():
        return {
            "ok": False,
            "command": ["python3", str(script)],
            "returncode": None,
            "stdout": "",
            "stderr": "missing v4.2 conformance validator",
        }
    command = [sys.executable, str(script)]
    proc = subprocess.run(command, cwd=str(cwd), text=True, capture_output=True, check=False)
    return {
        "ok": proc.returncode == 0,
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def _newest_child_dir(path: Path) -> Path | None:
    if not path.exists():
        return None
    candidates = [child for child in path.iterdir() if child.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda child: child.stat().st_mtime)


def _first_nonblank_line(path: Path) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            return line.strip()
    return ""


def run_v42_from_gate(
    *,
    task: str,
    cwd: Path,
    out_dir: Path,
    level: str,
    loop: str,
    dry_run: bool,
    codex_local_children: bool,
    no_capacity_preflight: bool,
) -> dict[str, Any]:
    v42_out_dir = out_dir / "v4_2_runs"
    v42_out_dir.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).with_name("wizard_v4_2.py")
    command = [
        sys.executable,
        str(script),
        "--task",
        task,
        "--cwd",
        str(cwd),
        "--out-dir",
        str(v42_out_dir),
        "--level",
        level,
        "--loop",
        loop,
    ]
    if dry_run:
        command.append("--dry-run")
    if codex_local_children:
        command.append("--codex-local-children")
    if no_capacity_preflight:
        command.append("--no-capacity-preflight")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = out_dir / f"v4_2_runner_stdout_{stamp}.log"
    proc = subprocess.run(command, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    log_path.write_text(proc.stdout, encoding="utf-8")

    run_root = _newest_child_dir(v42_out_dir)
    manifest_path = run_root / "wizard_loop_manifest.json" if run_root else None
    latest_output_path = run_root / "latest_wizard_output.md" if run_root else None
    return {
        "status": "completed" if proc.returncode == 0 else "failed",
        "returncode": proc.returncode,
        "command": command,
        "stdout_log": str(log_path),
        "run_root": str(run_root) if run_root else None,
        "manifest": str(manifest_path) if manifest_path and manifest_path.exists() else None,
        "latest_wizard_output": str(latest_output_path) if latest_output_path and latest_output_path.exists() else None,
        "compiled_header": _first_nonblank_line(latest_output_path) if latest_output_path else "",
        "dry_run": dry_run,
        "claim_boundary": (
            "v4.2 dry-run topology rehearsal; never a FULL council or object-proof claim"
            if dry_run
            else "read the v4.2 compiled header and receipts for council completion; v4.3 only guarded object preservation"
        ),
    }


def gated_v42_receipt(
    *,
    packet_path: Path,
    task: str,
    cwd: Path,
    out_dir: Path,
    level: str,
    loop: str,
    launch_v42: bool,
    dry_run_v42: bool,
    codex_local_children: bool,
    no_capacity_preflight: bool,
) -> dict[str, Any]:
    packet = read_json(packet_path)
    v43 = validate_packet(packet)
    boot = check_v42_boot_surface()
    conformance = run_v42_conformance(cwd=cwd)
    can_launch = bool(v43["ok"] and boot["ok"] and conformance["ok"])
    launch: dict[str, Any]
    if not launch_v42:
        launch = {
            "status": "not_requested",
            "claim_boundary": "v4.3 object-card validation plus v4.2 boot/conformance preflight only; no council run claim",
        }
    elif not can_launch:
        launch = {
            "status": "blocked",
            "claim_boundary": "v4.2 not launched because a prerequisite gate failed",
            "blocked_by": {
                "v4_3_validation": not v43["ok"],
                "v4_2_boot_surface": not boot["ok"],
                "v4_2_conformance": not conformance["ok"],
            },
        }
    else:
        launch = run_v42_from_gate(
            task=task,
            cwd=cwd,
            out_dir=out_dir,
            level=level,
            loop=loop,
            dry_run=dry_run_v42,
            codex_local_children=codex_local_children,
            no_capacity_preflight=no_capacity_preflight,
        )

    launch_ok = launch["status"] in {"not_requested", "completed"}
    object_card = packet.get("primary_object_card") if isinstance(packet.get("primary_object_card"), dict) else {}
    return {
        "ok": bool(v43["ok"] and boot["ok"] and conformance["ok"] and launch_ok),
        "schema_version": GATED_V42_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input_packet": str(packet_path),
        "task": task,
        "primary_object": {
            "object_name": object_card.get("object_name"),
            "object_type": object_card.get("object_type"),
            "object_statement_sha256": object_card.get("object_statement_sha256"),
        },
        "claim_ceiling": (
            "v4.3-gated v4.2 run receipt; object-card preservation and v4.2 boot/conformance were checked, "
            "but object truth, sim/proof admission, and FULL council status still require their own receipts"
            if launch_v42
            else "v4.3 object-card validation plus v4.2 boot/conformance preflight only; no council completion claim"
        ),
        "v4_3_validation": v43,
        "v4_2_boot_surface": boot,
        "v4_2_conformance": conformance,
        "v4_2_launch": launch,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate", help="Validate a v4.3 primary-object packet")
    validate_parser.add_argument("--input", required=True, type=Path)
    validate_parser.add_argument("--out", type=Path)

    selftest_parser = sub.add_parser("selftest", help="Run built-in object-preservation self-tests")
    selftest_parser.add_argument("--out", type=Path)

    loop_parser = sub.add_parser("loop", help="Run self-tests until clean or max loop count is reached")
    loop_parser.add_argument("--max-loops", type=int, default=3)
    loop_parser.add_argument("--out", type=Path)

    example_parser = sub.add_parser("example", help="Print a valid example packet")
    example_parser.add_argument("--out", type=Path)

    gate_parser = sub.add_parser("gate-v42", help="Validate v4.3 object preservation before a v4.2 Wizard run")
    gate_parser.add_argument("--input", required=True, type=Path)
    gate_parser.add_argument("--task", required=True)
    gate_parser.add_argument("--cwd", default=Path.cwd(), type=Path)
    gate_parser.add_argument("--out-dir", default=Path("/tmp/codex_ratchet_wizard_v4_3_gated_v4_2"), type=Path)
    gate_parser.add_argument("--out", type=Path)
    gate_parser.add_argument("--level", choices=["low", "medium", "high", "auto"], default="low")
    gate_parser.add_argument("--loop", default="1")
    gate_parser.add_argument("--launch-v42", action="store_true")
    gate_parser.add_argument("--dry-run-v42", action="store_true")
    gate_parser.add_argument("--codex-local-children", action="store_true")
    gate_parser.add_argument("--no-capacity-preflight", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "validate":
        payload = validate_packet(read_json(args.input))
        if args.out:
            write_json(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1

    if args.command == "selftest":
        payload = run_selftest()
        if args.out:
            write_json(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1

    if args.command == "loop":
        if args.max_loops < 1:
            raise SystemExit("--max-loops must be at least 1")
        payload = run_selftest_loop(args.max_loops)
        if args.out:
            write_json(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1

    if args.command == "example":
        payload = retrocausal_valid_packet()
        if args.out:
            write_json(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    if args.command == "gate-v42":
        payload = gated_v42_receipt(
            packet_path=args.input,
            task=args.task,
            cwd=args.cwd,
            out_dir=args.out_dir,
            level=args.level,
            loop=args.loop,
            launch_v42=args.launch_v42,
            dry_run_v42=args.dry_run_v42,
            codex_local_children=args.codex_local_children,
            no_capacity_preflight=args.no_capacity_preflight,
        )
        if args.out:
            write_json(args.out, payload)
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if payload["ok"] else 1

    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
