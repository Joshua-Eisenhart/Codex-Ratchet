"""
a1_entropy_structure_decomposition_control.py

Run one bounded A1 correction pass over the entropy-structure decomposition
control pack for correlation_diversity_functional. This pass freezes the real
lower-loop blocker, keeps direct structure targets proposal-side, and hands off
to a colder alias review instead of pretending A1_STRIPPED is ready.
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
    "nested_graph_build_a1_entropy_structure_decomposition_control/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_ENTROPY_STRUCTURE_"
    "DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.json"
)
PRIOR_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_FIRST_ENTROPY_STRUCTURE_CAMPAIGN__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
)
STRUCTURE_DECOMPOSITION_CONTROL = "system_v3/a1_state/A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md"
EXEC_ENTRYPOINT = "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md"
A2_DISTILLATION_INPUTS = "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md"
POST_UPDATE_AUDIT = "system_v3/a2_state/POST_UPDATE_CONSOLIDATION_AUDIT__v1.md"
ALIAS_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md"
RUN_ANCHOR = "system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_STRUCTURE_FAMILY__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
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


def _derive_decomposition_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "prior_structure_campaign": _find_first_evidence(
            root,
            "prior_structure_campaign",
            [
                {
                    "path": PRIOR_AUDIT,
                    "contains_any": [
                        "result: STRUCTURE_CAMPAIGN_CONFIRMED__DECOMPOSITION_CONTROL_NEXT",
                        "next_required_lane: A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL",
                    ],
                },
            ],
        ),
        "actual_blocker": _find_first_evidence(
            root,
            "actual_blocker",
            [
                {
                    "path": STRUCTURE_DECOMPOSITION_CONTROL,
                    "contains_any": [
                        "The current blocker is:",
                        "lower-loop compound decomposition / helper bootstrap on the direct structure targets.",
                    ],
                },
            ],
        ),
        "proposal_side_rule": _find_first_evidence(
            root,
            "proposal_side_rule",
            [
                {
                    "path": STRUCTURE_DECOMPOSITION_CONTROL,
                    "contains_any": [
                        "keep direct structure targets proposal-side,",
                    ],
                },
                {
                    "path": STRUCTURE_DECOMPOSITION_CONTROL,
                    "contains_any": [
                        "keep direct targets in proposal space,",
                    ],
                },
            ],
        ),
        "current_default": _find_first_evidence(
            root,
            "current_default",
            [
                {
                    "path": STRUCTURE_DECOMPOSITION_CONTROL,
                    "contains_any": [
                        "Proposal-only direct structure + colder executable witnesses",
                        "Status:",
                        "current default",
                    ],
                },
            ],
        ),
        "helper_only_route": _find_first_evidence(
            root,
            "helper_only_route",
            [
                {
                    "path": RUN_ANCHOR,
                    "contains_any": [
                        "the local structure route is execution-real, but still helper-side only",
                    ],
                },
                {
                    "path": PRIOR_AUDIT,
                    "contains_any": [
                        "structure_route_status: EXECUTION_REAL_HELPER_ONLY",
                    ],
                },
            ],
        ),
        "executable_floor": _find_first_evidence(
            root,
            "executable_floor",
            [
                {
                    "path": EXEC_ENTRYPOINT,
                    "contains_any": [
                        "the next executable branch should be:",
                        "correlation-side executable consolidation under current lower-loop semantics,",
                    ],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "primary_admitted_terms = correlation, correlation_polarity",
                    ],
                },
            ],
        ),
        "colder_alias_next": _find_first_evidence(
            root,
            "colder_alias_next",
            [
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "next entropy structure work should build a colder executable diversity alias/decomposition before retrying direct structure admission",
                    ],
                },
                {
                    "path": ALIAS_LIFT,
                    "contains_any": [
                        "The next entropy structure move should not keep forcing the warmer term:",
                    ],
                },
            ],
        ),
        "alias_candidate": _find_first_evidence(
            root,
            "alias_candidate",
            [
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "working candidate alias:",
                    ],
                },
                {
                    "path": ALIAS_LIFT,
                    "contains_any": [
                        "Working colder alias candidate:",
                    ],
                },
            ],
        ),
        "alias_not_head_ready": _find_first_evidence(
            root,
            "alias_not_head_ready",
            [
                {
                    "path": ALIAS_LIFT,
                    "contains_any": [
                        "the alias is not yet a justified executable lead term",
                    ],
                },
                {
                    "path": POST_UPDATE_AUDIT,
                    "contains_any": [
                        "alias work should remain a colder structure-side witness path until bootstrap debt is lower",
                    ],
                },
            ],
        ),
    }
    required = [
        "prior_structure_campaign",
        "actual_blocker",
        "proposal_side_rule",
        "current_default",
        "helper_only_route",
        "executable_floor",
        "colder_alias_next",
        "alias_candidate",
        "alias_not_head_ready",
    ]
    missing = [label for label in required if not evidence[label]]
    return evidence, missing


def run_a1_entropy_structure_decomposition_control(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff_path = _resolve(root, HANDOFF_PACKET)
    handoff = _load_json(handoff_path)
    handoff_errors = _validate_handoff(
        handoff_path,
        handoff,
        expected_unit_id="A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL",
        expected_layer_id="A1_JARGONED",
    )
    prior_audit = _load_text(_resolve(root, PRIOR_AUDIT))
    evidence, missing_evidence = _derive_decomposition_evidence(root)

    result_value = "DECOMPOSITION_CONTROL_CONFIRMED__COLDER_ALIAS_LIFT_NEXT"
    decision = (
        "Keep the local entropy-structure route honest: the live blocker remains "
        "lower-loop decomposition / helper bootstrap, so direct structure targets "
        "stay proposal-side while executable pressure remains on the colder "
        "correlation-side floor. The next explicit review lane is the colder "
        "diversity alias pack around pairwise_correlation_spread_functional."
    )
    next_required_lane = "A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL"
    next_control_surface = str(_resolve(root, ALIAS_LIFT))
    if handoff_errors:
        result_value = "MISSING_OR_INVALID_HANDOFF_PACKET"
        decision = (
            "Fail closed. The decomposition-control lane cannot claim a grounded "
            "result if its launch packet is missing or structurally invalid."
        )
        next_required_lane = "REPAIR_CURRENT_HANDOFF_PACKET"
        next_control_surface = str(handoff_path)
    elif missing_evidence:
        result_value = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep the decomposition-control boundary explicit because the cited "
            "repo-held doctrine does not currently provide enough machine-checked "
            "evidence to name the colder alias follow-on honestly."
        )
        next_required_lane = "MANUAL_ENTROPY_STRUCTURE_DECOMPOSITION_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL"
        next_control_surface = str(_resolve(root, STRUCTURE_DECOMPOSITION_CONTROL))

    result = {
        "schema": "A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "term": "correlation_diversity_functional",
        "handoff_packet": str(handoff_path),
        "result": result_value,
        "decision": decision,
        "source_surfaces": [
            str(_resolve(root, PRIOR_AUDIT)),
            str(_resolve(root, STRUCTURE_DECOMPOSITION_CONTROL)),
            str(_resolve(root, EXEC_ENTRYPOINT)),
            str(_resolve(root, A2_DISTILLATION_INPUTS)),
            str(_resolve(root, POST_UPDATE_AUDIT)),
            str(_resolve(root, ALIAS_LIFT)),
            str(_resolve(root, RUN_ANCHOR)),
        ],
        "derived_evidence": evidence,
        "missing_evidence": handoff_errors + missing_evidence,
        "prior_boundary_summary": {
            "has_structure_campaign_audit": bool(prior_audit.strip()),
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
            "active_blocker": "LOWER_LOOP_DECOMPOSITION_CONTROL",
            "direct_structure_status": "PROPOSAL_SIDE_ONLY",
            "executable_floor": "correlation_polarity / correlation",
            "next_alias_candidate": "pairwise_correlation_spread_functional",
        },
        "blockers": [
            "direct structure targets still decompose into helper/bootstrap surfaces under current lower-loop semantics",
            "the local structure route is execution-real but still helper-side only",
            "correlation_diversity_functional remains proposal-side rather than stripped-head ready",
            "pairwise_correlation_spread_functional is a real colder alias candidate but still not head-ready",
        ],
        "next_required_lane": next_required_lane,
        "next_control_surface": next_control_surface,
        "non_claims": [
            "This pass does not materialize A1_STRIPPED or A1_CARTRIDGE.",
            "This pass does not promote correlation_diversity_functional to executable-head status.",
            "This pass does not claim pairwise_correlation_spread_functional is already a clean strategy head.",
            "This pass does not reopen proposal-drift or bridge-floor wording as the active blocker.",
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
        "# A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1",
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
        f"- active_blocker: {result['grounded_read']['active_blocker']}",
        f"- direct_structure_status: {result['grounded_read']['direct_structure_status']}",
        f"- executable_floor: {result['grounded_read']['executable_floor']}",
        f"- next_alias_candidate: {result['grounded_read']['next_alias_candidate']}",
        "",
        "## Prior Boundary",
        f"- has_structure_campaign_audit: {result['prior_boundary_summary']['has_structure_campaign_audit']}",
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
    output = run_a1_entropy_structure_decomposition_control(str(REPO_ROOT))
    print(json.dumps(output, indent=2, sort_keys=True))
