"""
a2_stage1_operatorized_entropy_head_refinement.py

Run one bounded A2-only Stage-1 operatorized entropy-head refinement pass for
correlation_diversity_functional. This pass does not reopen A1. It writes one
audit note that either finds a thinner admissible source-anchored landing or
preserves the helper-decomposition blocker explicitly.
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
    "nested_graph_build_a2_stage1_operatorized_entropy_head_refinement/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A2_STAGE1_OPERATORIZED_ENTROPY_HEAD_"
    "REFINEMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.json"
)
A2_REFINEMENT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A2_REFINEMENT_FOR_A1_STRIPPED_LANDING__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
)
A2_PRIOR_HANDOFF = (
    "system_v3/a2_state/A2_WORKER_LAUNCH_HANDOFF__STAGE1_OPERATORIZED_ENTROPY_HEAD__2026_03_13__v1.json"
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
A1_STRUCTURE_CONTROL = "system_v3/a1_state/A1_ENTROPY_STRUCTURE_DECOMPOSITION_CONTROL__v1.md"
A1_EXEC_ENTRYPOINT = "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md"
LIVE_HINTS = "system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md"
A2_ROLE_SPLIT = "system_v3/specs/33_A2_VS_A1_ROLE_SPLIT__v1.md"
A1_HELPER_CONTROL = "system_v3/a1_state/A1_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A2_STAGE1_OPERATORIZED_ENTROPY_HEAD_REFINEMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
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


def _derive_stage1_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "thinnest_admissible_read": _find_first_evidence(
            root,
            "thinnest_admissible_read",
            [
                {
                    "path": A2_UPDATE_NOTE,
                    "contains_any": [
                        "a proposal-side diversity measure over correlation-side distinctions",
                    ],
                },
            ],
        ),
        "candidate_viable": _find_first_evidence(
            root,
            "candidate_viable",
            [
                {
                    "path": A2_IMPACT_NOTE,
                    "regex_all": [r"\bcorrelation_diversity_functional\b"],
                    "contains_any": ["strongest direct-structure candidate"],
                },
                {
                    "path": A2_UPDATE_NOTE,
                    "regex_all": [r"\bcorrelation_diversity_functional\b"],
                    "contains_any": ["stronger direct-structure candidate"],
                },
            ],
        ),
        "landing_absent_or_present": _find_first_evidence(
            root,
            "landing_absent_or_present",
            [
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "regex_all": [r"\bcorrelation_diversity_functional\b"],
                    "contains_any": ["still does not land"],
                },
                {
                    "path": A2_UPDATE_NOTE,
                    "contains_any": [
                        "this is the stronger of the two direct structure candidates, but it still does not land",
                    ],
                },
                {
                    "path": A1_TARGET_MODEL,
                    "contains_any": ["the direct target still does not land in executed-cycle broad pressure"],
                },
            ],
        ),
        "active_blocker": _find_first_evidence(
            root,
            "active_blocker",
            [
                {
                    "path": NEXT_VALIDATION,
                    "contains_any": ["current blocker is helper decomposition / term-surface control"],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "direct structure-side executable admission remains blocked by current lower-loop term-surface semantics",
                        "the next entropy engineering step should target helper decomposition control",
                    ],
                },
                {
                    "path": A1_STRUCTURE_CONTROL,
                    "contains_any": [
                        "direct structure-side executable admission remains blocked by lower-loop decomposition",
                    ],
                },
            ],
        ),
        "a2_not_a1_guard": _find_first_evidence(
            root,
            "a2_not_a1_guard",
            [
                {
                    "path": A2_ROLE_SPLIT,
                    "contains_any": ["broad refinery belongs to `a2`", "full-stack refinery is `a2`"],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": ["`A1` remains dormant until a bounded ready state exists"],
                },
            ],
        ),
        "route_budget_guard": _find_first_evidence(
            root,
            "route_budget_guard",
            [
                {
                    "path": NEXT_VALIDATION,
                    "contains_any": ["do not spend the next budget increment on more route-proving here"],
                },
                {
                    "path": A1_EXEC_ENTRYPOINT,
                    "contains_any": ["burn more budget on pretending this is still a path-build ordering problem"],
                },
            ],
        ),
        "colder_executable_floor": _find_first_evidence(
            root,
            "colder_executable_floor",
            [
                {
                    "path": A2_IMPACT_NOTE,
                    "contains_any": ["executable witness pressure remains on `correlation` and `correlation_polarity`"],
                },
                {
                    "path": NEXT_VALIDATION,
                    "contains_any": ["Entropy Correlation Executable Branch"],
                },
                {
                    "path": A1_EXEC_ENTRYPOINT,
                    "contains_any": ["correlation-side helper floor = current executable entropy-adjacent entrypoint"],
                },
            ],
        ),
    }
    required = [
        "thinnest_admissible_read",
        "candidate_viable",
        "landing_absent_or_present",
        "active_blocker",
        "a2_not_a1_guard",
        "route_budget_guard",
    ]
    missing = [label for label in required if not evidence[label]]
    return evidence, missing


def run_a2_stage1_operatorized_entropy_head_refinement(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff = _load_json(_resolve(root, HANDOFF_PACKET))
    prior_audit = _load_text(_resolve(root, A2_REFINEMENT_AUDIT))
    evidence, missing_evidence = _derive_stage1_evidence(root)

    result_value = "NO_CURRENT_THINNER_SOURCE_ANCHORED_LANDING"
    decision = (
        "Preserve the Stage-1 entropy head as a valid A2 routing head, but keep "
        "correlation_diversity_functional blocked above A1. Current doctrine names "
        "a thinner admissible proposal-side read, yet still preserves helper-"
        "decomposition / term-surface control as the active blocker."
    )
    next_required_lane = "A2_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL"
    if missing_evidence:
        result_value = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep the Stage-1 blocker explicit because the cited repo-held surfaces "
            "do not currently provide enough machine-checked evidence to derive the "
            "bounded Stage-1 refinement result."
        )
        next_required_lane = "MANUAL_A2_STAGE1_REFINEMENT_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL"

    result = {
        "schema": "A2_STAGE1_OPERATORIZED_ENTROPY_HEAD_REFINEMENT_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "term": "correlation_diversity_functional",
        "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
        "result": result_value,
        "decision": decision,
        "source_surfaces": [
            str(_resolve(root, A2_REFINEMENT_AUDIT)),
            str(_resolve(root, A2_PRIOR_HANDOFF)),
            str(_resolve(root, A2_UPDATE_NOTE)),
            str(_resolve(root, A2_IMPACT_NOTE)),
            str(_resolve(root, A2_DISTILLATION_INPUTS)),
            str(_resolve(root, OPEN_UNRESOLVED)),
            str(_resolve(root, NEXT_VALIDATION)),
            str(_resolve(root, A1_TARGET_MODEL)),
            str(_resolve(root, A1_STRUCTURE_CONTROL)),
            str(_resolve(root, A1_EXEC_ENTRYPOINT)),
            str(_resolve(root, LIVE_HINTS)),
            str(_resolve(root, A2_ROLE_SPLIT)),
            str(_resolve(root, A1_HELPER_CONTROL)),
        ],
        "derived_evidence": evidence,
        "missing_evidence": missing_evidence,
        "prior_boundary_summary": {
            "has_prior_a2_refinement_audit": bool(prior_audit.strip()),
            "prior_result_line": next(
                (line for line in prior_audit.splitlines() if line.startswith("result: ")),
                "",
            ),
        },
        "grounded_read": {
            "stage1_family_status": "VALID_A2_ROUTING_HEAD",
            "thinnest_admissible_read": (
                "proposal-side diversity measure over correlation-side distinctions, "
                "colder than engine language and still needing alias/decomposition help"
            ),
            "candidate_status": "strongest_direct_structure_candidate_but_still_blocked",
            "active_blocker": "helper decomposition / term-surface control",
            "executable_floor": [
                "correlation",
                "correlation_polarity",
            ],
            "current_default": "compound proposal + colder witness execution",
        },
        "blockers": [
            "direct structure target still does not land under current lower-loop semantics",
            "helper decomposition / term-surface control remains the actual active blocker",
            "direct compound admission remains blocked, so no A1 landing is justified from this pass",
        ],
        "next_required_lane": next_required_lane,
        "next_control_surface": str(_resolve(root, A1_HELPER_CONTROL)),
        "non_claims": [
            "This pass does not perform A1 proposal, stripped translation, or cartridge packaging.",
            "This pass does not claim a current A1-ready exact landing exists.",
            "This pass does not reopen alias-first or path-build tuning as the main route.",
            "This pass does not treat compound bridge interest as executable success.",
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
        "# A2_STAGE1_OPERATORIZED_ENTROPY_HEAD_REFINEMENT__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1",
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
        f"- stage1_family_status: {result['grounded_read']['stage1_family_status']}",
        f"- thinnest_admissible_read: {result['grounded_read']['thinnest_admissible_read']}",
        f"- candidate_status: {result['grounded_read']['candidate_status']}",
        f"- active_blocker: {result['grounded_read']['active_blocker']}",
        f"- current_default: {result['grounded_read']['current_default']}",
        "- executable_floor:",
    ])
    for item in result["grounded_read"]["executable_floor"]:
        lines.append(f"  - {item}")
    lines.extend([
        "",
        "## Prior Boundary",
        f"- has_prior_a2_refinement_audit: {result['prior_boundary_summary']['has_prior_a2_refinement_audit']}",
        f"- prior_result_line: {result['prior_boundary_summary']['prior_result_line']}",
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
    output = run_a2_stage1_operatorized_entropy_head_refinement(str(REPO_ROOT))
    print(json.dumps(output, indent=2, sort_keys=True))
