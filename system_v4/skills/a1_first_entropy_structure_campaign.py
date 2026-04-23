"""
a1_first_entropy_structure_campaign.py

Run one bounded A1 correction pass over the first entropy structure campaign for
correlation_diversity_functional. This pass preserves the direct
entropy-structure lane as execution-real but helper-only evidence, and hands
off to decomposition control instead of pretending A1_STRIPPED is ready.
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
    "nested_graph_build_a1_first_entropy_structure_campaign/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__"
    "CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.json"
)
PRIOR_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__CORRELATION_POLARITY__2026_03_20__v1.md"
)
STRUCTURE_CAMPAIGN = "system_v3/a1_state/A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__v1.md"
STRUCTURE_ANCHOR = "system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_STRUCTURE_FAMILY__v1.md"
STRUCTURE_WITNESS = (
    "system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_STRUCTURE_FAMILY__v1.md"
)
DECOMPOSITION_CONTROL = "system_v3/a1_state/A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md"
POST_UPDATE_AUDIT = "system_v3/a2_state/POST_UPDATE_CONSOLIDATION_AUDIT__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
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


def _derive_structure_campaign_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "prior_helper_lift_boundary": _find_first_evidence(
            root,
            "prior_helper_lift_boundary",
            [
                {
                    "path": PRIOR_AUDIT,
                    "contains_any": [
                        "result: HELPER_LIFT_BOUNDARY_CONFIRMED__FIRST_STRUCTURE_CAMPAIGN_NEXT",
                        "next_required_lane: A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__CORRELATION_DIVERSITY_FUNCTIONAL",
                    ],
                },
            ],
        ),
        "direct_targets_declared": _find_first_evidence(
            root,
            "direct_targets_declared",
            [
                {
                    "path": STRUCTURE_CAMPAIGN,
                    "contains_any": [
                        "Direct unresolved targets:",
                    ],
                },
            ],
        ),
        "route_execution_real": _find_first_evidence(
            root,
            "route_execution_real",
            [
                {
                    "path": STRUCTURE_ANCHOR,
                    "contains_any": [
                        "first direct local structure-side executed-cycle proof",
                    ],
                },
                {
                    "path": STRUCTURE_CAMPAIGN,
                    "contains_any": [
                        "one real lower-loop cycle executed",
                    ],
                },
            ],
        ),
        "targets_still_do_not_land": _find_first_evidence(
            root,
            "targets_still_do_not_land",
            [
                {
                    "path": STRUCTURE_CAMPAIGN,
                    "contains_any": [
                        "direct structure targets still did not land",
                    ],
                },
                {
                    "path": POST_UPDATE_AUDIT,
                    "contains_any": [
                        "direct targets still do not land",
                    ],
                },
            ],
        ),
        "helper_only_read": _find_first_evidence(
            root,
            "helper_only_read",
            [
                {
                    "path": STRUCTURE_ANCHOR,
                    "contains_any": [
                        "the local structure route is execution-real, but still helper-side only",
                    ],
                },
                {
                    "path": STRUCTURE_CAMPAIGN,
                    "contains_any": [
                        "The local direct-structure route is now useful as helper/cold-side evidence only.",
                    ],
                },
            ],
        ),
        "decomposition_blocker": _find_first_evidence(
            root,
            "decomposition_blocker",
            [
                {
                    "path": STRUCTURE_CAMPAIGN,
                    "contains_any": [
                        "the live blocker is helper decomposition / term-surface control",
                    ],
                },
                {
                    "path": DECOMPOSITION_CONTROL,
                    "contains_any": [
                        "The current blocker is:",
                        "lower-loop compound decomposition / helper bootstrap on the direct structure targets.",
                    ],
                },
            ],
        ),
        "next_control_surface": _find_first_evidence(
            root,
            "next_control_surface",
            [
                {
                    "path": STRUCTURE_CAMPAIGN,
                    "contains_any": [
                        "use:",
                    ],
                    "regex_any": [r"A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1\.md"],
                },
                {
                    "path": DECOMPOSITION_CONTROL,
                    "contains_any": [
                        "The correct near-term move is:",
                    ],
                },
            ],
        ),
    }
    required = [
        "prior_helper_lift_boundary",
        "direct_targets_declared",
        "route_execution_real",
        "targets_still_do_not_land",
        "helper_only_read",
        "decomposition_blocker",
        "next_control_surface",
    ]
    missing = [label for label in required if not evidence[label]]
    return evidence, missing


def run_a1_first_entropy_structure_campaign(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff_path = _resolve(root, HANDOFF_PACKET)
    handoff = _load_json(handoff_path)
    handoff_errors = _validate_handoff(
        handoff_path,
        handoff,
        expected_unit_id="A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__CORRELATION_DIVERSITY_FUNCTIONAL",
        expected_layer_id="A1_JARGONED",
    )
    prior_audit = _load_text(_resolve(root, PRIOR_AUDIT))
    evidence, missing_evidence = _derive_structure_campaign_evidence(root)

    result_value = "STRUCTURE_CAMPAIGN_CONFIRMED__DECOMPOSITION_CONTROL_NEXT"
    decision = (
        "Keep the first entropy structure campaign as the correct direct "
        "entropy-structure follow-up after helper-lift, but read it honestly as "
        "execution-real helper-only evidence under current lower-loop semantics. "
        "The next justified control move is decomposition control, not A1_STRIPPED "
        "materialization and not another bridge-route reinvention."
    )
    next_required_lane = "A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL"
    next_control_surface = str(_resolve(root, DECOMPOSITION_CONTROL))
    if handoff_errors:
        result_value = "MISSING_OR_INVALID_HANDOFF_PACKET"
        decision = (
            "Fail closed. The structure-campaign lane cannot claim a completed "
            "handoff if the current launch packet is missing or structurally invalid."
        )
        next_required_lane = "REPAIR_CURRENT_HANDOFF_PACKET"
        next_control_surface = str(handoff_path)
    elif missing_evidence:
        result_value = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep the structure campaign boundary explicit because the cited "
            "repo-held doctrine does not currently provide enough machine-checked "
            "evidence to name the next decomposition-control handoff honestly."
        )
        next_required_lane = "MANUAL_STRUCTURE_CAMPAIGN_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL"
        next_control_surface = str(_resolve(root, STRUCTURE_CAMPAIGN))

    result = {
        "schema": "A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "term": "correlation_diversity_functional",
        "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
        "result": result_value,
        "decision": decision,
        "source_surfaces": [
            str(_resolve(root, PRIOR_AUDIT)),
            str(_resolve(root, STRUCTURE_CAMPAIGN)),
            str(_resolve(root, STRUCTURE_ANCHOR)),
            str(_resolve(root, STRUCTURE_WITNESS)),
            str(_resolve(root, DECOMPOSITION_CONTROL)),
            str(_resolve(root, POST_UPDATE_AUDIT)),
        ],
        "derived_evidence": evidence,
        "missing_evidence": handoff_errors + missing_evidence,
        "prior_boundary_summary": {
            "has_helper_lift_audit": bool(prior_audit.strip()),
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
            "structure_route_status": "EXECUTION_REAL_HELPER_ONLY",
            "direct_structure_priority": "correlation_diversity_functional",
            "deferred_second_target": "probe_induced_partition_boundary",
            "active_blocker": "LOWER_LOOP_DECOMPOSITION_CONTROL",
        },
        "blockers": [
            "direct structure targets still do not land under the current local route",
            "current local survivors remain helper-side terms rather than direct structure heads",
            "the live blocker is lower-loop compound decomposition / term-surface control",
        ],
        "next_required_lane": next_required_lane,
        "next_control_surface": next_control_surface,
        "non_claims": [
            "This pass does not materialize A1_STRIPPED or A1_CARTRIDGE.",
            "This pass does not promote correlation_diversity_functional to executable-head status.",
            "This pass does not reopen bridge-floor tuning as the active blocker.",
            "This pass does not claim probe_induced_partition_boundary is the first executable direct target.",
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
        "# A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1",
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
        f"- structure_route_status: {result['grounded_read']['structure_route_status']}",
        f"- direct_structure_priority: {result['grounded_read']['direct_structure_priority']}",
        f"- deferred_second_target: {result['grounded_read']['deferred_second_target']}",
        f"- active_blocker: {result['grounded_read']['active_blocker']}",
        "",
        "## Prior Boundary",
        f"- has_helper_lift_audit: {result['prior_boundary_summary']['has_helper_lift_audit']}",
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
    output = run_a1_first_entropy_structure_campaign(str(REPO_ROOT))
    print(json.dumps(output, indent=2, sort_keys=True))
