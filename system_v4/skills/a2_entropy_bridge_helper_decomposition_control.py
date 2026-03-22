"""
a2_entropy_bridge_helper_decomposition_control.py

Run one bounded A2 correction pass that freezes the real helper-decomposition
barrier for correlation_diversity_functional. This pass does not reopen A1. It
writes one audit note grounded in repo-held doctrine that confirms compound
bridge terms remain proposal/control heads while colder witnesses carry the
current executable burden.
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
    "nested_graph_build_a2_entropy_bridge_helper_decomposition_control/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A2_ENTROPY_BRIDGE_HELPER_"
    "DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.json"
)
STAGE1_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A2_STAGE1_OPERATORIZED_ENTROPY_HEAD_REFINEMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
)
A2_DISTILLATION_INPUTS = "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md"
NEXT_VALIDATION = "system_v3/a2_state/NEXT_VALIDATION_TARGETS__v1.md"
A1_HELPER_CONTROL = "system_v3/a1_state/A1_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__v1.md"
A1_STRUCTURE_CONTROL = "system_v3/a1_state/A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md"
A1_EXEC_ENTRYPOINT = "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md"
A1_TARGET_MODEL = "system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A2_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
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


def _derive_helper_control_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "stage1_preserved_blocker": _find_first_evidence(
            root,
            "stage1_preserved_blocker",
            [
                {
                    "path": STAGE1_AUDIT,
                    "contains_any": [
                        "helper decomposition / term-surface control",
                        "next_required_lane: A2_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL",
                    ],
                },
            ],
        ),
        "actual_blocker": _find_first_evidence(
            root,
            "actual_blocker",
            [
                {
                    "path": A1_HELPER_CONTROL,
                    "contains_any": [
                        "downstream helper decomposition of selected multi-lexeme bridge terms under current lower-loop semantics",
                    ],
                },
                {
                    "path": A1_STRUCTURE_CONTROL,
                    "contains_any": [
                        "lower-loop compound decomposition / helper bootstrap on the direct structure targets",
                    ],
                },
                {
                    "path": NEXT_VALIDATION,
                    "contains_any": [
                        "current blocker is helper decomposition / term-surface control",
                    ],
                },
            ],
        ),
        "compound_proposal_colder_execution": _find_first_evidence(
            root,
            "compound_proposal_colder_execution",
            [
                {
                    "path": A1_HELPER_CONTROL,
                    "contains_any": [
                        "compound proposal + colder witness execution",
                        "Use colder witnesses as executable work carriers.",
                    ],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "keeping the compound terms in proposal space while colder witnesses do the executable work.",
                    ],
                },
            ],
        ),
        "direct_head_stays_proposal_side": _find_first_evidence(
            root,
            "direct_head_stays_proposal_side",
            [
                {
                    "path": A1_HELPER_CONTROL,
                    "contains_any": [
                        "keep direct compound bridge terms in proposal space for now,",
                        "compound bridge terms remain available as proposal/control surfaces,",
                        "keep compound bridge terms in proposal space,",
                    ],
                },
                {
                    "path": A1_STRUCTURE_CONTROL,
                    "contains_any": [
                        "as proposal/control targets.",
                        "keep direct targets in proposal space,",
                    ],
                },
                {
                    "path": A1_EXEC_ENTRYPOINT,
                    "contains_any": [
                        "deferred / witness-side proposal targets:",
                        "proposal/control = six-term bridge floor",
                    ],
                },
                {
                    "path": A1_TARGET_MODEL,
                    "contains_any": [
                        "keep the direct entropy-family names in proposal space while this bridge is being proven",
                    ],
                },
            ],
        ),
        "executable_floor_colder_witness": _find_first_evidence(
            root,
            "executable_floor_colder_witness",
            [
                {
                    "path": A1_EXEC_ENTRYPOINT,
                    "contains_any": [
                        "correlation-side helper floor = current executable entropy-adjacent entrypoint",
                    ],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "primary_admitted_terms = correlation, correlation_polarity",
                    ],
                },
                {
                    "path": NEXT_VALIDATION,
                    "contains_all": ["correlation", "correlation_polarity"],
                    "contains_any": ["Active executable entropy-adjacent branch"],
                },
            ],
        ),
        "next_branch_colder_consolidation": _find_first_evidence(
            root,
            "next_branch_colder_consolidation",
            [
                {
                    "path": A1_EXEC_ENTRYPOINT,
                    "contains_any": [
                        "the next executable branch should be:",
                        "correlation-side executable consolidation under current lower-loop semantics",
                    ],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "the next usable entropy move must lift colder witnesses into a stronger bridge composition instead of collapsing into `density_entropy` alone",
                    ],
                },
            ],
        ),
        "alias_or_component_deferred": _find_first_evidence(
            root,
            "alias_or_component_deferred",
            [
                {
                    "path": A1_HELPER_CONTROL,
                    "contains_any": [
                        "deferred unless colder witness movement saturates",
                    ],
                },
                {
                    "path": A1_HELPER_CONTROL,
                    "contains_any": [
                        "revisit alias or component-ladder strategies only after the colder witness lane saturates.",
                    ],
                },
                {
                    "path": A1_STRUCTURE_CONTROL,
                    "contains_any": [
                        "revisit atomic-ladder or colder-alias strategies only as explicit later work.",
                    ],
                },
            ],
        ),
    }
    required = [
        "stage1_preserved_blocker",
        "actual_blocker",
        "compound_proposal_colder_execution",
        "direct_head_stays_proposal_side",
        "executable_floor_colder_witness",
        "next_branch_colder_consolidation",
    ]
    missing = [label for label in required if not evidence[label]]
    return evidence, missing


def run_a2_entropy_bridge_helper_decomposition_control(
    workspace_root: str,
) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff = _load_json(_resolve(root, HANDOFF_PACKET))
    stage1_audit = _load_text(_resolve(root, STAGE1_AUDIT))
    evidence, missing_evidence = _derive_helper_control_evidence(root)

    result_value = "HELPER_DECOMPOSITION_CONTROL_CONFIRMED__COMPOUND_TERMS_STAY_PROPOSAL_SIDE"
    decision = (
        "Keep correlation_diversity_functional blocked above A1_STRIPPED. Current "
        "repo-held doctrine agrees that helper decomposition remains the real "
        "barrier, compound bridge heads stay proposal/control-side, and executable "
        "pressure should remain on the colder correlation-side witness floor."
    )
    next_required_lane = "COLDER_WITNESS_EXECUTION_CONSOLIDATION__CORRELATION_POLARITY"
    next_control_surface = str(_resolve(root, A1_EXEC_ENTRYPOINT))
    if missing_evidence:
        result_value = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep the helper-decomposition blocker explicit because the cited "
            "repo-held doctrine does not currently provide enough machine-checked "
            "evidence to freeze the helper-control lane."
        )
        next_required_lane = "MANUAL_HELPER_DECOMPOSITION_CONTROL_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL"
        next_control_surface = str(_resolve(root, A1_HELPER_CONTROL))

    result = {
        "schema": "A2_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "term": "correlation_diversity_functional",
        "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
        "result": result_value,
        "decision": decision,
        "source_surfaces": [
            str(_resolve(root, STAGE1_AUDIT)),
            str(_resolve(root, A2_DISTILLATION_INPUTS)),
            str(_resolve(root, NEXT_VALIDATION)),
            str(_resolve(root, A1_HELPER_CONTROL)),
            str(_resolve(root, A1_STRUCTURE_CONTROL)),
            str(_resolve(root, A1_EXEC_ENTRYPOINT)),
            str(_resolve(root, A1_TARGET_MODEL)),
        ],
        "derived_evidence": evidence,
        "missing_evidence": missing_evidence,
        "prior_boundary_summary": {
            "has_stage1_audit": bool(stage1_audit.strip()),
            "prior_result_line": next(
                (line for line in stage1_audit.splitlines() if line.startswith("result: ")),
                "",
            ),
            "prior_next_required_lane": next(
                (line for line in stage1_audit.splitlines() if line.startswith("next_required_lane: ")),
                "",
            ),
        },
        "grounded_read": {
            "structure_target_status": "PROPOSAL_CONTROL_ONLY",
            "helper_barrier_status": "CONFIRMED_ACTIVE_BLOCKER",
            "current_default": "compound proposal + colder witness execution",
            "executable_floor": [
                "correlation",
                "correlation_polarity",
            ],
            "deferred_strategies": [
                "atomic component ladder",
                "colder alias surfaces",
            ],
        },
        "blockers": [
            "selected multi-lexeme bridge terms still trigger helper decomposition under current lower-loop semantics",
            "direct compound admission remains blocked, so no stripped landing is justified from this pass",
            "alias or component-ladder work remains deferred until colder witness movement saturates",
        ],
        "next_required_lane": next_required_lane,
        "next_control_surface": next_control_surface,
        "non_claims": [
            "This pass does not materialize A1_STRIPPED or A1_CARTRIDGE.",
            "This pass does not claim correlation_diversity_functional is now a direct executable survivor.",
            "This pass does not reopen alias-first or component-ladder work as the default route.",
            "This pass does not treat helper fragments or witness survivors as direct bridge success.",
        ],
        "handoff_snapshot": {
            "queue_status": str(handoff.get("queue_status", "")),
            "role_type": str(handoff.get("role_type", "")),
            "thread_class": str(handoff.get("thread_class", "")),
            "mode": str(handoff.get("mode", "")),
        },
    }

    audit_path = _resolve(root, OUTPUT_AUDIT)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# A2_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1",
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
        f"- structure_target_status: {result['grounded_read']['structure_target_status']}",
        f"- helper_barrier_status: {result['grounded_read']['helper_barrier_status']}",
        f"- current_default: {result['grounded_read']['current_default']}",
        "- executable_floor:",
    ])
    for item in result["grounded_read"]["executable_floor"]:
        lines.append(f"  - {item}")
    lines.append("- deferred_strategies:")
    for item in result["grounded_read"]["deferred_strategies"]:
        lines.append(f"  - {item}")
    lines.extend([
        "",
        "## Prior Boundary",
        f"- has_stage1_audit: {result['prior_boundary_summary']['has_stage1_audit']}",
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
    output = run_a2_entropy_bridge_helper_decomposition_control(str(REPO_ROOT))
    print(json.dumps(output, indent=2, sort_keys=True))
