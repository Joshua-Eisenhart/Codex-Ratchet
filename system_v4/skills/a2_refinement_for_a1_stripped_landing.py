"""
a2_refinement_for_a1_stripped_landing.py

Run one bounded A2 correction pass for a stalled direct-structure target whose
A1 stripped landing has failed closed. This pass is A2-only: it writes an audit
artifact that either names a current source-anchored exact landing candidate or
preserves the blocker explicitly.
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
    "nested_graph_build_a2_refinement_for_a1_stripped_landing/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A2_REFINEMENT_FOR_A1_STRIPPED_LANDING__"
    "CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.json"
)
A1_STRIPPED_GRAPH = "system_v4/a1_state/a1_stripped_graph_v1.json"
A1_STRIPPED_AUDIT = "system_v4/a2_state/audit_logs/A1_STRIPPED_GRAPH_AUDIT__2026_03_20__v1.md"
A1_TERM_PLAN_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_STRIPPED_TERM_PLAN_ALIGNMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
)
A2_UPDATE_NOTE = (
    "system_v3/a2_state/A2_UPDATE_NOTE__STAGE1_OPERATORIZED_ENTROPY_HEAD_GROUNDING__2026_03_17__v1.md"
)
A2_IMPACT_NOTE = (
    "system_v3/a2_state/A2_TO_A1_IMPACT_NOTE__STAGE1_OPERATORIZED_ENTROPY_HEAD_GROUNDING__2026_03_17__v1.md"
)
A2_DISTILLATION_INPUTS = "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md"
OPEN_UNRESOLVED = "system_v3/a2_state/OPEN_UNRESOLVED__v1.md"
NEXT_VALIDATION = "system_v3/a2_state/NEXT_VALIDATION_TARGETS__v1.md"
A1_TARGET_MODEL = "system_v3/a1_state/A1_TARGET_FAMILY_MODEL__v1.md"
LIVE_HINTS = "system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md"
ALIAS_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A2_REFINEMENT_FOR_A1_STRIPPED_LANDING__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
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


def _derive_refinement_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "strong_candidate_still_blocked": _find_first_evidence(root, "strong_candidate_still_blocked", [
            {
                "path": A2_IMPACT_NOTE,
                "regex_all": [r"\bcorrelation_diversity_functional\b"],
                "contains_any": [
                    "strongest direct-structure candidate",
                    "still blocked above stripped landing",
                ],
            },
            {
                "path": A2_UPDATE_NOTE,
                "regex_all": [r"\bcorrelation_diversity_functional\b"],
                "contains_any": [
                    "stronger direct-structure candidate",
                    "still does not land",
                    "still blocked",
                ],
            },
        ]),
        "exact_landing_absent": _find_first_evidence(root, "exact_landing_absent", [
            {
                "path": A2_DISTILLATION_INPUTS,
                "regex_all": [r"\bcorrelation_diversity_functional\b"],
                "contains_any": [
                    "still does not land",
                    "direct structure-side executable admission remains blocked",
                ],
            },
            {
                "path": A1_TARGET_MODEL,
                "regex_all": [r"\bcorrelation_diversity_functional\b"],
                "contains_any": [
                    "final executable landing is still not earned",
                    "readiness: fail",
                    "does not land",
                ],
            },
        ]),
        "alias_witness_floor": _find_first_evidence(root, "alias_witness_floor", [
            {
                "path": LIVE_HINTS,
                "regex_all": [r"\bpairwise_correlation_spread_functional\b", r"\bWITNESS_ONLY\b"],
            },
            {
                "path": ALIAS_LIFT,
                "contains_all": ["pairwise_correlation_spread_functional", "WITNESS_ONLY"],
            },
            {
                "path": A1_TERM_PLAN_AUDIT,
                "regex_all": [r"\bpairwise_correlation_spread_functional\b", r"\bWITNESS_ONLY\b"],
            },
            {
                "path": A1_STRIPPED_AUDIT,
                "contains_all": ["pairwise_correlation_spread_functional", "witness-side only"],
            },
        ]),
        "next_work_helper_decomposition": _find_first_evidence(root, "next_work_helper_decomposition", [
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
                "path": OPEN_UNRESOLVED,
                "contains_any": ["helper decomposition", "term-surface"],
            },
        ]),
    }
    missing = [label for label, item in evidence.items() if not item]
    return evidence, missing


def run_a2_refinement_for_a1_stripped_landing(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff = _load_json(_resolve(root, HANDOFF_PACKET))
    stripped_graph = _load_json(_resolve(root, A1_STRIPPED_GRAPH))
    evidence, missing_evidence = _derive_refinement_evidence(root)

    result_value = "NO_CURRENT_SOURCE_ANCHORED_EXACT_LANDING"
    decision = (
        "Keep correlation_diversity_functional blocked above A1_STRIPPED. "
        "Current repo-held A2 doctrine still treats it as the strongest "
        "direct-structure candidate, but does not provide a current "
        "source-anchored exact landing that could honestly support stripped-layer "
        "materialization."
    )
    next_required_lane = "A2_STAGE1_OPERATORIZED_ENTROPY_HEAD_REFINEMENT__CORRELATION_DIVERSITY_FUNCTIONAL"
    if missing_evidence:
        result_value = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep the blocker explicit because the cited repo-held A2 doctrine does "
            "not currently provide enough machine-checked evidence to derive the next landing call."
        )
        next_required_lane = "MANUAL_A2_REFINEMENT_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL"
    result = {
        "schema": "A2_REFINEMENT_FOR_A1_STRIPPED_LANDING_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "term": "correlation_diversity_functional",
        "result": result_value,
        "decision": decision,
        "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
        "source_surfaces": [
            str(_resolve(root, A1_STRIPPED_GRAPH)),
            str(_resolve(root, A1_STRIPPED_AUDIT)),
            str(_resolve(root, A1_TERM_PLAN_AUDIT)),
            str(_resolve(root, A2_UPDATE_NOTE)),
            str(_resolve(root, A2_IMPACT_NOTE)),
            str(_resolve(root, A2_DISTILLATION_INPUTS)),
            str(_resolve(root, OPEN_UNRESOLVED)),
            str(_resolve(root, NEXT_VALIDATION)),
            str(_resolve(root, A1_TARGET_MODEL)),
            str(_resolve(root, LIVE_HINTS)),
            str(_resolve(root, ALIAS_LIFT)),
        ],
        "input_state": {
            "a1_stripped_build_status": stripped_graph.get("build_status", ""),
            "a1_stripped_materialized": stripped_graph.get("materialized", False),
            "a1_stripped_blocked_terms": stripped_graph.get("blocked_terms", []),
        },
        "evidence": evidence,
        "missing_evidence": missing_evidence,
        "grounded_read": {
            "family_status": "PASSENGER_ONLY_DIRECT_STRUCTURE_TARGET",
            "exact_landing_status": "NOT_CURRENTLY_JUSTIFIED",
            "witness_floor": [
                "pairwise_correlation_spread_functional",
            ],
            "active_blocker": (
                "lower-loop compound-math / term-surface semantics remain unresolved "
                "for the direct structure target"
            ),
        },
        "blockers": [
            "family-level passenger survival does not supply an exact stripped landing",
            "colder alias pairwise_correlation_spread_functional remains witness-side only",
            "current A2 doctrine preserves contradiction between strong target status and failed landing",
        ],
        "next_required_lane": next_required_lane,
        "non_claims": [
            "This pass does not reopen A1_JARGONED scope.",
            "This pass does not materialize A1_STRIPPED or A1_CARTRIDGE.",
            "This pass does not upgrade witness-floor terms into direct landing.",
            "This pass does not claim the blocker is resolved merely because the family remains interesting.",
        ],
        "handoff_snapshot": {
            "dispatch_id": handoff.get("dispatch_id", ""),
            "queue_status": handoff.get("queue_status", ""),
            "role_type": handoff.get("role_type", ""),
        },
    }

    audit_path = _resolve(root, OUTPUT_AUDIT)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# A2_REFINEMENT_FOR_A1_STRIPPED_LANDING__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1",
        "",
        f"generated_utc: {result['generated_utc']}",
        f"result: {result['result']}",
        f"decision: {result['decision']}",
        f"next_required_lane: {result['next_required_lane']}",
        "",
        "## Source Surfaces",
    ]
    for item in result["source_surfaces"]:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "## Derived Evidence",
    ])
    for label, item in result["evidence"].items():
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
        "## Input State",
        f"- a1_stripped_build_status: {result['input_state']['a1_stripped_build_status']}",
        f"- a1_stripped_materialized: {result['input_state']['a1_stripped_materialized']}",
        "- a1_stripped_blocked_terms:",
    ])
    for item in result["input_state"]["a1_stripped_blocked_terms"]:
        lines.append(f"  - {item['term']}: {item['reason']}")
    lines.extend([
        "",
        "## Grounded Read",
        f"- family_status: {result['grounded_read']['family_status']}",
        f"- exact_landing_status: {result['grounded_read']['exact_landing_status']}",
        f"- active_blocker: {result['grounded_read']['active_blocker']}",
        "- witness_floor:",
    ])
    for item in result["grounded_read"]["witness_floor"]:
        lines.append(f"  - {item}")
    lines.extend([
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
    output = run_a2_refinement_for_a1_stripped_landing(str(REPO_ROOT))
    print(json.dumps(output, indent=2, sort_keys=True))
