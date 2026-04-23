"""
a1_entropy_bridge_helper_lift_pack.py

Run one bounded correction pass over the repo-held A1 helper-lift control pack
for the entropy bridge around correlation_polarity. This pass writes one audit
note that preserves the helper-lift boundary and names the next direct
structure-side lane only if the current doctrine supports it explicitly.
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


HANDOFF_PACKET = (
    "system_v4/a2_state/launch_bundles/"
    "nested_graph_build_a1_entropy_bridge_helper_lift_pack/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__"
    "CORRELATION_POLARITY__2026_03_20__v1.json"
)
PRIOR_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "COLDER_WITNESS_EXECUTION_CONSOLIDATION__CORRELATION_POLARITY__2026_03_20__v1.md"
)
HELPER_LIFT_PACK = "system_v3/a1_state/A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__v1.md"
FIRST_BRIDGE_CAMPAIGN = "system_v3/a1_state/A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md"
A2_DISTILLATION_INPUTS = "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md"
FIRST_STRUCTURE_CAMPAIGN = "system_v3/a1_state/A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__v1.md"
DIVERSITY_STRUCTURE_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_STRUCTURE_LIFT_PACK__v1.md"
DIVERSITY_ALIAS_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md"
CARTRIDGE_REVIEW = "system_v3/a1_state/A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__CORRELATION_POLARITY__2026_03_20__v1.md"
)


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve(root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (root / path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_handoff(
    handoff_path: Path,
    handoff: dict[str, Any],
    *,
    expected_unit_id: str,
    expected_layer_id: str,
) -> list[str]:
    errors: list[str] = []
    if not handoff_path.exists():
        errors.append("handoff_packet_missing")
    if not handoff:
        errors.append("handoff_packet_unreadable_or_empty")
        return errors
    for key in ["unit_id", "dispatch_id", "layer_id", "queue_status", "role_type", "thread_class", "mode"]:
        if not str(handoff.get(key, "")).strip():
            errors.append(f"missing_handoff_field:{key}")
    for key in ["required_boot", "source_artifacts", "expected_outputs", "write_scope"]:
        value = handoff.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"missing_handoff_list:{key}")
    if str(handoff.get("unit_id", "")) and str(handoff.get("unit_id", "")) != expected_unit_id:
        errors.append("handoff_unit_id_mismatch")
    if str(handoff.get("layer_id", "")) and str(handoff.get("layer_id", "")) != expected_layer_id:
        errors.append("handoff_layer_id_mismatch")
    return errors


def _load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _find_first_evidence(
    root: Path,
    label: str,
    search_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    for spec in search_specs:
        path = _resolve(root, str(spec["path"]))
        text = _load_text(path)
        if not text:
            continue
        contains_all = [item.lower() for item in spec.get("contains_all", [])]
        contains_any = [item.lower() for item in spec.get("contains_any", [])]
        regex_all = [str(item) for item in spec.get("regex_all", [])]
        regex_any = [str(item) for item in spec.get("regex_any", [])]
        for lineno, raw_line in enumerate(text.splitlines(), start=1):
            line = raw_line.strip()
            lowered = line.lower()
            if contains_all and not all(token in lowered for token in contains_all):
                continue
            if contains_any and not any(token in lowered for token in contains_any):
                continue
            if regex_all and not all(re.search(pattern, line) for pattern in regex_all):
                continue
            if regex_any and not any(re.search(pattern, line) for pattern in regex_any):
                continue
            return {
                "label": label,
                "path": str(path),
                "line": lineno,
                "text": line,
            }
    return {}


def _derive_helper_lift_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "prior_boundary": _find_first_evidence(
            root,
            "prior_boundary",
            [
                {
                    "path": PRIOR_AUDIT,
                    "contains_any": [
                        "result: CORRELATION_POLARITY_BROAD_EXECUTABLE_HEAD_CONFIRMED",
                        "next_required_lane: A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__CORRELATION_POLARITY",
                    ],
                },
            ],
        ),
        "required_lift_composition": _find_first_evidence(
            root,
            "required_lift_composition",
            [
                {
                    "path": HELPER_LIFT_PACK,
                    "contains_any": [
                        "Every primary branch must include:",
                    ],
                },
                {
                    "path": HELPER_LIFT_PACK,
                    "contains_any": [
                        "At least one colder helper must be paired with:",
                    ],
                },
            ],
        ),
        "helper_lift_as_composition_rule": _find_first_evidence(
            root,
            "helper_lift_as_composition_rule",
            [
                {
                    "path": FIRST_BRIDGE_CAMPAIGN,
                    "contains_any": [
                        "the next entropy move must force colder helpers into a bridge-capable composition instead of letting them lead alone",
                    ],
                },
                {
                    "path": FIRST_BRIDGE_CAMPAIGN,
                    "contains_any": [
                        "simply making the branch colder is not enough",
                    ],
                },
            ],
        ),
        "no_lone_helpers": _find_first_evidence(
            root,
            "no_lone_helpers",
            [
                {
                    "path": HELPER_LIFT_PACK,
                    "contains_any": [
                        "Do not allow:",
                        "to appear as isolated leading helpers.",
                    ],
                },
                {
                    "path": HELPER_LIFT_PACK,
                    "contains_any": [
                        "no lone helper branches",
                    ],
                },
            ],
        ),
        "helper_lift_not_selector_bug": _find_first_evidence(
            root,
            "helper_lift_not_selector_bug",
            [
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "therefore helper-lift broad is not exposing a selector defect",
                    ],
                },
                {
                    "path": FIRST_STRUCTURE_CAMPAIGN,
                    "contains_any": [
                        "helper-lift broad collapse is therefore not a selector bug",
                    ],
                },
            ],
        ),
        "next_direct_structure_move": _find_first_evidence(
            root,
            "next_direct_structure_move",
            [
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "the correct next move is direct entropy-structure pressure with bridge support demoted to witness status",
                    ],
                },
                {
                    "path": FIRST_STRUCTURE_CAMPAIGN,
                    "contains_any": [
                        "the next structure-side executable move should favor:",
                    ],
                },
            ],
        ),
        "diversity_structure_priority": _find_first_evidence(
            root,
            "diversity_structure_priority",
            [
                {
                    "path": DIVERSITY_STRUCTURE_LIFT,
                    "contains_any": [
                        "the first executable structure-side lift should favor:",
                    ],
                },
                {
                    "path": DIVERSITY_STRUCTURE_LIFT,
                    "contains_any": [
                        "executable-first target:",
                    ],
                },
            ],
        ),
        "diversity_still_not_landed": _find_first_evidence(
            root,
            "diversity_still_not_landed",
            [
                {
                    "path": DIVERSITY_STRUCTURE_LIFT,
                    "contains_any": [
                        "correlation_diversity_functional still does not land",
                    ],
                },
                {
                    "path": CARTRIDGE_REVIEW,
                    "contains_any": [
                        "The honest executable head remains `correlation_polarity`",
                    ],
                },
            ],
        ),
        "alias_lift_deferred": _find_first_evidence(
            root,
            "alias_lift_deferred",
            [
                {
                    "path": DIVERSITY_STRUCTURE_LIFT,
                    "contains_any": [
                        "the next move should be a colder executable alias/decomposition for the diversity side",
                    ],
                },
                {
                    "path": DIVERSITY_ALIAS_LIFT,
                    "contains_any": [
                        "the alias is not yet a justified executable lead term",
                    ],
                },
            ],
        ),
    }
    required = [
        "prior_boundary",
        "required_lift_composition",
        "helper_lift_as_composition_rule",
        "no_lone_helpers",
        "helper_lift_not_selector_bug",
        "next_direct_structure_move",
        "diversity_structure_priority",
    ]
    missing = [label for label in required if not evidence[label]]
    return evidence, missing


def run_a1_entropy_bridge_helper_lift_pack(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff_path = _resolve(root, HANDOFF_PACKET)
    handoff = _load_json(handoff_path)
    handoff_errors = _validate_handoff(
        handoff_path,
        handoff,
        expected_unit_id="A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__CORRELATION_POLARITY",
        expected_layer_id="A1_JARGONED",
    )
    prior_audit = _load_text(_resolve(root, PRIOR_AUDIT))
    evidence, missing_evidence = _derive_helper_lift_evidence(root)

    result_value = "HELPER_LIFT_BOUNDARY_CONFIRMED__FIRST_STRUCTURE_CAMPAIGN_NEXT"
    decision = (
        "Keep helper-lift as a valid composition-rule boundary probe, not the new "
        "default executable route. Current repo-held doctrine says helper-lift broad "
        "is not exposing a selector defect, so the next justified move is direct "
        "entropy-structure pressure through the first entropy structure campaign, "
        "with the diversity-side lift on correlation_diversity_functional favored "
        "inside that campaign and bridge support demoted to witness status."
    )
    next_required_lane = "A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__CORRELATION_DIVERSITY_FUNCTIONAL"
    next_control_surface = str(_resolve(root, FIRST_STRUCTURE_CAMPAIGN))
    if handoff_errors:
        result_value = "MISSING_OR_INVALID_HANDOFF_PACKET"
        decision = (
            "Fail closed. The helper-lift lane cannot claim a confirmed boundary or "
            "handoff if the current launch packet is missing or structurally invalid."
        )
        next_required_lane = "REPAIR_CURRENT_HANDOFF_PACKET"
        next_control_surface = str(handoff_path)
    elif missing_evidence:
        result_value = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep the helper-lift boundary explicit because the cited repo-held "
            "doctrine does not currently provide enough machine-checked evidence "
            "to name the next structure-side lift honestly."
        )
        next_required_lane = "MANUAL_ENTROPY_HELPER_LIFT_REVIEW__CORRELATION_POLARITY"
        next_control_surface = str(_resolve(root, HELPER_LIFT_PACK))

    result = {
        "schema": "A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "term": "correlation_polarity",
        "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
        "result": result_value,
        "decision": decision,
        "source_surfaces": [
            str(_resolve(root, PRIOR_AUDIT)),
            str(_resolve(root, HELPER_LIFT_PACK)),
            str(_resolve(root, FIRST_BRIDGE_CAMPAIGN)),
            str(_resolve(root, A2_DISTILLATION_INPUTS)),
            str(_resolve(root, FIRST_STRUCTURE_CAMPAIGN)),
            str(_resolve(root, DIVERSITY_STRUCTURE_LIFT)),
            str(_resolve(root, DIVERSITY_ALIAS_LIFT)),
            str(_resolve(root, CARTRIDGE_REVIEW)),
        ],
        "derived_evidence": evidence,
        "missing_evidence": handoff_errors + missing_evidence,
        "prior_boundary_summary": {
            "has_colder_witness_audit": bool(prior_audit.strip()),
            "prior_result_line": next(
                (line for line in prior_audit.splitlines() if line.startswith("result: ")),
                "",
            ),
            "prior_next_required_lane": next(
                (line for line in prior_audit.splitlines() if line.startswith("next_required_lane: ")),
                "",
            ),
        },
        "grounded_read": {
            "helper_lift_status": "BOUNDARY_PROBE_ONLY",
            "campaign_handoff": "A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__CORRELATION_DIVERSITY_FUNCTIONAL",
            "direct_structure_priority": "correlation_diversity_functional",
            "deferred_second_target": "probe_induced_partition_boundary",
            "bridge_support_status": "DEMOTED_TO_WITNESS_SUPPORT",
        },
        "blockers": [
            "helper-lift broad does not justify replacing the broad executable branch as the active entropy route",
            "first entropy structure remains execution-real but helper-only under current lower-loop semantics",
            "correlation_diversity_functional still does not land and remains proposal-side inside the structure campaign",
            "pairwise_correlation_spread_functional remains a witness-side alias candidate, not a clean executable head",
        ],
        "next_required_lane": next_required_lane,
        "next_control_surface": next_control_surface,
        "non_claims": [
            "This pass does not materialize A1_STRIPPED or A1_CARTRIDGE.",
            "This pass does not claim helper-lift broad is the new executable entropy route.",
            "This pass does not promote correlation_diversity_functional to executable-head status.",
            "This pass does not promote pairwise_correlation_spread_functional above witness-side alias status.",
            "This pass does not reopen probe_induced_partition_boundary as an equal first structure target.",
        ],
        "handoff_snapshot": {
            "unit_id": str(handoff.get("unit_id", "")),
            "dispatch_id": str(handoff.get("dispatch_id", "")),
            "queue_status": str(handoff.get("queue_status", "")),
            "role_type": str(handoff.get("role_type", "")),
            "thread_class": str(handoff.get("thread_class", "")),
            "mode": str(handoff.get("mode", "")),
        },
    }

    audit_path = _resolve(root, OUTPUT_AUDIT)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__CORRELATION_POLARITY__2026_03_20__v1",
        "",
        f"generated_utc: {result['generated_utc']}",
        f"result: {result['result']}",
        f"decision: {result['decision']}",
        f"handoff_packet: {result['handoff_packet']}",
        f"next_required_lane: {result['next_required_lane']}",
        f"next_control_surface: {result['next_control_surface']}",
        "",
        "## Source Surfaces",
    ]
    for item in result["source_surfaces"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Derived Evidence",
    ])
    for label, item in result["derived_evidence"].items():
        if item:
            lines.append(f"- {label}: {item['path']}:{item['line']} :: {item['text']}")
        else:
            lines.append(f"- {label}: missing")
    lines.extend([
        "",
        "## Missing Evidence",
    ])
    if result["missing_evidence"]:
        for item in result["missing_evidence"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Grounded Read",
        f"- helper_lift_status: {result['grounded_read']['helper_lift_status']}",
        f"- campaign_handoff: {result['grounded_read']['campaign_handoff']}",
        f"- direct_structure_priority: {result['grounded_read']['direct_structure_priority']}",
        f"- deferred_second_target: {result['grounded_read']['deferred_second_target']}",
        f"- bridge_support_status: {result['grounded_read']['bridge_support_status']}",
        "",
        "## Prior Boundary",
        f"- has_colder_witness_audit: {result['prior_boundary_summary']['has_colder_witness_audit']}",
        f"- prior_result_line: {result['prior_boundary_summary']['prior_result_line']}",
        f"- prior_next_required_lane: {result['prior_boundary_summary']['prior_next_required_lane']}",
        "",
        "## Blockers",
    ])
    for item in result["blockers"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Non-Claims",
    ])
    for item in result["non_claims"]:
        lines.append(f"- {item}")
    lines.append("")
    audit_path.write_text("\n".join(lines), encoding="utf-8")
    result["audit_note_path"] = str(audit_path)
    return result


if __name__ == "__main__":
    output = run_a1_entropy_bridge_helper_lift_pack(str(REPO_ROOT))
    print(json.dumps(output, indent=2, sort_keys=True))
