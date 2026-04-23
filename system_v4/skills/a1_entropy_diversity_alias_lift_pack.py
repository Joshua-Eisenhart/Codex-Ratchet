"""
a1_entropy_diversity_alias_lift_pack.py

Run one bounded A1 correction pass over the colder diversity alias pack around
pairwise_correlation_spread_functional. This pass preserves the alias as a real
but witness-only colder candidate and refuses to promote it to a clean
executable head before lower-loop bootstrap debt is lower.
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
    "nested_graph_build_a1_entropy_diversity_alias_lift_pack/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_ENTROPY_DIVERSITY_ALIAS_"
    "LIFT_PACK__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL__2026_03_20__v1.json"
)
PRIOR_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
)
ALIAS_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md"
EXEC_ENTRYPOINT = "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md"
A2_DISTILLATION_INPUTS = "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md"
POST_UPDATE_AUDIT = "system_v3/a2_state/POST_UPDATE_CONSOLIDATION_AUDIT__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL__2026_03_20__v1.md"
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


def _derive_alias_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "prior_decomposition_control": _find_first_evidence(
            root,
            "prior_decomposition_control",
            [
                {
                    "path": PRIOR_AUDIT,
                    "contains_any": [
                        "result: DECOMPOSITION_CONTROL_CONFIRMED__COLDER_ALIAS_LIFT_NEXT",
                        "next_required_lane: A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL",
                    ],
                },
            ],
        ),
        "alias_candidate_declared": _find_first_evidence(
            root,
            "alias_candidate_declared",
            [
                {
                    "path": ALIAS_LIFT,
                    "contains_any": [
                        "Working colder alias candidate:",
                    ],
                },
            ],
        ),
        "alias_should_be_tested": _find_first_evidence(
            root,
            "alias_should_be_tested",
            [
                {
                    "path": ALIAS_LIFT,
                    "contains_any": [
                        "It should first test whether a colder executable alias like:",
                    ],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "Active colder-alias next step:",
                    ],
                },
            ],
        ),
        "alias_real_but_not_head": _find_first_evidence(
            root,
            "alias_real_but_not_head",
            [
                {
                    "path": ALIAS_LIFT,
                    "contains_any": [
                        "the alias is real and worth keeping",
                    ],
                },
                {
                    "path": ALIAS_LIFT,
                    "contains_any": [
                        "the alias is not yet a justified executable lead term",
                    ],
                },
                {
                    "path": POST_UPDATE_AUDIT,
                    "contains_any": [
                        "current executable alias profiles do not justify promoting it to the active route",
                    ],
                },
            ],
        ),
        "current_readiness": _find_first_evidence(
            root,
            "current_readiness",
            [
                {
                    "path": ALIAS_LIFT,
                    "contains_all": ["pairwise_correlation_spread_functional", "WITNESS_ONLY"],
                },
            ],
        ),
        "do_not_make_active_route": _find_first_evidence(
            root,
            "do_not_make_active_route",
            [
                {
                    "path": ALIAS_LIFT,
                    "contains_any": [
                        "do not keep spending budget on alias-first executable profiles right now",
                    ],
                },
                {
                    "path": EXEC_ENTRYPOINT,
                    "contains_any": [
                        "until a cleaner colder alias or component ladder is justified",
                    ],
                },
            ],
        ),
    }
    required = [
        "prior_decomposition_control",
        "alias_candidate_declared",
        "alias_should_be_tested",
        "alias_real_but_not_head",
        "current_readiness",
        "do_not_make_active_route",
    ]
    missing = [label for label in required if not evidence[label]]
    return evidence, missing


def run_a1_entropy_diversity_alias_lift_pack(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff_path = _resolve(root, HANDOFF_PACKET)
    handoff = _load_json(handoff_path)
    handoff_errors = _validate_handoff(
        handoff_path,
        handoff,
        expected_unit_id="A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL",
        expected_layer_id="A1_JARGONED",
    )
    prior_audit = _load_text(_resolve(root, PRIOR_AUDIT))
    evidence, missing_evidence = _derive_alias_evidence(root)

    result_value = "ALIAS_LIFT_CONFIRMED__WITNESS_ONLY_KEEP_ROUTE_SMALL"
    decision = (
        "Keep pairwise_correlation_spread_functional as a real colder alias "
        "candidate, but do not promote it to executable-head status. Under "
        "current doctrine it remains witness-only, and direct entropy-executable "
        "work should stay small until a cleaner alias or deliberate component "
        "ladder is justified."
    )
    next_required_lane = "PAUSE_DIRECT_ENTROPY_EXECUTABLE_WORK__CORRELATION_DIVERSITY_FUNCTIONAL"
    next_control_surface = str(_resolve(root, EXEC_ENTRYPOINT))
    if handoff_errors:
        result_value = "MISSING_OR_INVALID_HANDOFF_PACKET"
        decision = (
            "Fail closed. The alias-lift lane cannot claim a grounded result if "
            "its launch packet is missing or structurally invalid."
        )
        next_required_lane = "REPAIR_CURRENT_HANDOFF_PACKET"
        next_control_surface = str(handoff_path)
    elif missing_evidence:
        result_value = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep the colder alias lane explicit because the cited repo-held "
            "doctrine does not currently provide enough machine-checked evidence "
            "to close it out honestly."
        )
        next_required_lane = "MANUAL_ENTROPY_ALIAS_REVIEW__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL"
        next_control_surface = str(_resolve(root, ALIAS_LIFT))

    result = {
        "schema": "A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "term": "pairwise_correlation_spread_functional",
        "handoff_packet": str(handoff_path),
        "result": result_value,
        "decision": decision,
        "source_surfaces": [
            str(_resolve(root, PRIOR_AUDIT)),
            str(_resolve(root, ALIAS_LIFT)),
            str(_resolve(root, EXEC_ENTRYPOINT)),
            str(_resolve(root, A2_DISTILLATION_INPUTS)),
            str(_resolve(root, POST_UPDATE_AUDIT)),
        ],
        "derived_evidence": evidence,
        "missing_evidence": handoff_errors + missing_evidence,
        "prior_boundary_summary": {
            "has_decomposition_control_audit": bool(prior_audit.strip()),
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
            "alias_status": "REAL_COLDER_CANDIDATE_BUT_WITNESS_ONLY",
            "strategy_head_status": "NOT_HEAD_READY",
            "active_head_remains": "correlation_polarity",
            "late_passenger_remains": "correlation_diversity_functional",
        },
        "blockers": [
            "pairwise_correlation_spread_functional still carries too much bootstrap debt for clean head promotion",
            "current executable alias profiles do not justify promoting the alias to the active route",
            "correlation_diversity_functional still remains passenger-side until alias, decomposition, and witness floors improve",
        ],
        "next_required_lane": next_required_lane,
        "next_control_surface": next_control_surface,
        "non_claims": [
            "This pass does not materialize A1_STRIPPED or A1_CARTRIDGE.",
            "This pass does not promote pairwise_correlation_spread_functional to executable-head status.",
            "This pass does not reopen alias-first executable profiles as the default route.",
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
        "# A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL__2026_03_20__v1",
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
        f"- alias_status: {result['grounded_read']['alias_status']}",
        f"- strategy_head_status: {result['grounded_read']['strategy_head_status']}",
        f"- active_head_remains: {result['grounded_read']['active_head_remains']}",
        f"- late_passenger_remains: {result['grounded_read']['late_passenger_remains']}",
        "",
        "## Prior Boundary",
        f"- has_decomposition_control_audit: {result['prior_boundary_summary']['has_decomposition_control_audit']}",
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
    output = run_a1_entropy_diversity_alias_lift_pack(str(REPO_ROOT))
    print(json.dumps(output, indent=2, sort_keys=True))
