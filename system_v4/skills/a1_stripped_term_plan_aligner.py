"""
a1_stripped_term_plan_aligner.py

Correction-first pass for family-level stripped landing doctrine. This pass
decides whether a warmer passenger family term has any honest exact stripped
landing under current repo-held doctrine, writes an explicit audit artifact,
and then re-materializes the blocked stripped/cartridge owner surfaces from
that result.
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

from system_v4.skills.a1_cartridge_graph_builder import write_a1_cartridge_graph
from system_v4.skills.a1_stripped_graph_builder import write_a1_stripped_graph


HANDOFF_PACKET = (
    "system_v4/a2_state/launch_bundles/"
    "nested_graph_build_a1_stripped_term_plan_alignment/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_STRIPPED_TERM_PLAN_ALIGNMENT__"
    "CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.json"
)
STRIPPED_GRAPH = "system_v4/a1_state/a1_stripped_graph_v1.json"
CARTRIDGE_GRAPH = "system_v4/a1_state/a1_cartridge_graph_v1.json"
LIVE_HINTS = "system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md"
ROSETTA_BATCH = "system_v3/a1_state/A1_ROSETTA_BATCH__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md"
TARGET_FAMILY_MODEL = "system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md"
STRUCTURE_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_STRUCTURE_LIFT_PACK__v1.md"
ALIAS_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md"
CARTRIDGE_REVIEW = (
    "system_v3/a1_state/A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md"
)
CONTROL_SURFACE = "system_v3/a1_state/A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md"
EXEC_ENTRYPOINT = "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md"
A2_ROLE_SPLIT = "system_v3/specs/33_A2_VS_A1_ROLE_SPLIT__v1.md"
A2_UPDATE_NOTE = (
    "system_v3/a2_state/A2_UPDATE_NOTE__STAGE1_OPERATORIZED_ENTROPY_HEAD_GROUNDING__2026_03_17__v1.md"
)
A2_DISTILLATION_INPUTS = "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md"
NEXT_VALIDATION = "system_v3/a2_state/NEXT_VALIDATION_TARGETS__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_STRIPPED_TERM_PLAN_ALIGNMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
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


def _derive_term_plan_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "family_passenger_only": _find_first_evidence(root, "family_passenger_only", [
            {
                "path": LIVE_HINTS,
                "regex_all": [r"\bcorrelation_diversity_functional\b", r"\bPASSENGER_ONLY\b"],
            },
            {
                "path": ALIAS_LIFT,
                "contains_all": ["correlation_diversity_functional", "PASSENGER_ONLY"],
            },
            {
                "path": CARTRIDGE_REVIEW,
                "contains_all": ["correlation_diversity_functional", "PASSENGER_ONLY"],
            },
        ]),
        "alias_witness_only": _find_first_evidence(root, "alias_witness_only", [
            {
                "path": LIVE_HINTS,
                "regex_all": [r"\bpairwise_correlation_spread_functional\b", r"\bWITNESS_ONLY\b"],
            },
            {
                "path": ALIAS_LIFT,
                "contains_all": ["pairwise_correlation_spread_functional", "WITNESS_ONLY"],
            },
        ]),
        "no_exact_landing": _find_first_evidence(root, "no_exact_landing", [
            {
                "path": ROSETTA_BATCH,
                "contains_any": [
                    "the term still does not land cleanly under executed-cycle pressure",
                ],
            },
            {
                "path": A2_UPDATE_NOTE,
                "contains_any": [
                    "this is the stronger of the two direct structure candidates, but it still does not land",
                    "the direct target still does not land in executed-cycle broad pressure",
                ],
            },
            {
                "path": TARGET_FAMILY_MODEL,
                "contains_any": [
                    "final executable landing is still not earned",
                    "does not land in executed-cycle broad pressure",
                ],
            },
        ]),
        "blocker_control": _find_first_evidence(root, "blocker_control", [
            {
                "path": NEXT_VALIDATION,
                "contains_any": ["current blocker is helper decomposition / term-surface control"],
            },
            {
                "path": A2_DISTILLATION_INPUTS,
                "contains_any": [
                    "the next entropy engineering step should target helper decomposition control",
                    "direct structure-side executable admission remains blocked by current lower-loop term-surface semantics",
                ],
            },
            {
                "path": CONTROL_SURFACE,
                "contains_any": ["lower-loop compound decomposition / helper bootstrap", "helper decomposition"],
            },
        ]),
        "next_work_belongs_to_a2": _find_first_evidence(root, "next_work_belongs_to_a2", [
            {
                "path": A2_DISTILLATION_INPUTS,
                "contains_any": [
                    "`a1` remains dormant",
                    "`a1` still remains `no_work`",
                    "the immediate next move is additional a2 grounding on the warmer surviving passenger-side target correlation_diversity_functional",
                ],
            },
            {
                "path": A2_ROLE_SPLIT,
                "contains_any": ["broad refinery belongs to `a2`", "full-stack refinery is `a2`"],
            },
        ]),
    }
    missing = [label for label, item in evidence.items() if not item]
    return evidence, missing


def run_a1_stripped_term_plan_alignment(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff = _load_json(_resolve(root, HANDOFF_PACKET))
    stripped_before = _load_json(_resolve(root, STRIPPED_GRAPH))
    cartridge_before = _load_json(_resolve(root, CARTRIDGE_GRAPH))
    evidence, missing_evidence = _derive_term_plan_evidence(root)

    stripped_write = write_a1_stripped_graph(str(root))
    cartridge_write = write_a1_cartridge_graph(str(root))

    stripped_after = _load_json(_resolve(root, STRIPPED_GRAPH))
    cartridge_after = _load_json(_resolve(root, CARTRIDGE_GRAPH))

    result = "NO_CURRENT_STRIPPED_LANDING"
    decision = (
        "Keep A1_STRIPPED blocked for correlation_diversity_functional. Current "
        "repo-held doctrine preserves the family as PASSENGER_ONLY but does not "
        "name any honest exact stripped landing; the colder alias "
        "pairwise_correlation_spread_functional remains WITNESS_ONLY."
    )
    next_required_lane = "A2_REFINEMENT_FOR_A1_STRIPPED_LANDING__CORRELATION_DIVERSITY_FUNCTIONAL"
    if missing_evidence:
        result = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep A1_STRIPPED fail-closed because the required doctrine evidence "
            "for a derived term-plan decision is incomplete in the cited repo-held surfaces."
        )
        next_required_lane = "MANUAL_A1_STRIPPED_TERM_PLAN_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL"
    report = {
        "schema": "A1_STRIPPED_TERM_PLAN_ALIGNMENT_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "term": "correlation_diversity_functional",
        "result": result,
        "decision": decision,
        "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
        "source_surfaces": [
            str(_resolve(root, LIVE_HINTS)),
            str(_resolve(root, ROSETTA_BATCH)),
            str(_resolve(root, TARGET_FAMILY_MODEL)),
            str(_resolve(root, STRUCTURE_LIFT)),
            str(_resolve(root, ALIAS_LIFT)),
            str(_resolve(root, CARTRIDGE_REVIEW)),
            str(_resolve(root, CONTROL_SURFACE)),
            str(_resolve(root, EXEC_ENTRYPOINT)),
            str(_resolve(root, A2_ROLE_SPLIT)),
            str(_resolve(root, A2_UPDATE_NOTE)),
            str(_resolve(root, A2_DISTILLATION_INPUTS)),
            str(_resolve(root, NEXT_VALIDATION)),
        ],
        "evidence": evidence,
        "missing_evidence": missing_evidence,
        "before": {
            "stripped_build_status": stripped_before.get("build_status", ""),
            "stripped_materialized": stripped_before.get("materialized", False),
            "stripped_node_ids": sorted(list(stripped_before.get("nodes", {}).keys())),
            "cartridge_build_status": cartridge_before.get("build_status", ""),
            "cartridge_materialized": cartridge_before.get("materialized", False),
        },
        "after": {
            "stripped_build_status": stripped_after.get("build_status", ""),
            "stripped_materialized": stripped_after.get("materialized", False),
            "stripped_node_ids": sorted(list(stripped_after.get("nodes", {}).keys())),
            "stripped_blocked_terms": stripped_after.get("blocked_terms", []),
            "cartridge_build_status": cartridge_after.get("build_status", ""),
            "cartridge_materialized": cartridge_after.get("materialized", False),
            "cartridge_blockers": cartridge_after.get("blockers", []),
        },
        "write_result": {
            "stripped": stripped_write,
            "cartridge": cartridge_write,
        },
        "non_claims": [
            "This pass does not reopen A1_JARGONED scope.",
            "This pass does not upgrade correlation_diversity_functional into an executable or stripped head.",
            "This pass does not claim a new A2 landing already exists.",
            "This pass does not materialize A1_CARTRIDGE.",
        ],
        "next_required_lane": next_required_lane,
    }

    audit_path = _resolve(root, OUTPUT_AUDIT)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# A1_STRIPPED_TERM_PLAN_ALIGNMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"result: {report['result']}",
        f"decision: {report['decision']}",
        f"handoff_packet: {report['handoff_packet']}",
        f"next_required_lane: {report['next_required_lane']}",
        "",
        "## Source Surfaces",
    ]
    for item in report["source_surfaces"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Derived Evidence",
    ])
    for label, item in report["evidence"].items():
        if item:
            lines.append(
                f"- {label}: {item['path']}:{item['line']} :: {item['text']}"
            )
        else:
            lines.append(f"- {label}: missing")
    lines.extend([
        "",
        "## Missing Evidence",
    ])
    if report["missing_evidence"]:
        for item in report["missing_evidence"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Before",
        f"- stripped_build_status: {report['before']['stripped_build_status']}",
        f"- stripped_materialized: {report['before']['stripped_materialized']}",
        f"- stripped_node_ids: {report['before']['stripped_node_ids']}",
        f"- cartridge_build_status: {report['before']['cartridge_build_status']}",
        f"- cartridge_materialized: {report['before']['cartridge_materialized']}",
        "",
        "## After",
        f"- stripped_build_status: {report['after']['stripped_build_status']}",
        f"- stripped_materialized: {report['after']['stripped_materialized']}",
        f"- stripped_node_ids: {report['after']['stripped_node_ids']}",
        "- stripped_blocked_terms:",
    ])
    for item in report["after"]["stripped_blocked_terms"]:
        lines.append(f"  - {item['term']}: {item['reason']}")
    lines.extend([
        f"- cartridge_build_status: {report['after']['cartridge_build_status']}",
        f"- cartridge_materialized: {report['after']['cartridge_materialized']}",
        "- cartridge_blockers:",
    ])
    for item in report["after"]["cartridge_blockers"]:
        lines.append(f"  - {item}")
    lines.extend([
        "",
        "## Non-Claims",
    ])
    for item in report["non_claims"]:
        lines.append(f"- {item}")
    lines.append("")
    audit_path.write_text("\n".join(lines), encoding="utf-8")
    report["audit_note_path"] = str(audit_path)
    return report


if __name__ == "__main__":
    result = run_a1_stripped_term_plan_alignment(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
