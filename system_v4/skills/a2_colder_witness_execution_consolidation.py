"""
a2_colder_witness_execution_consolidation.py

Run one bounded A2 correction pass that consolidates the current colder-witness
executable branch around correlation_polarity. This pass does not reopen A1
materialization. It writes one audit note grounded in repo-held doctrine that
confirms the broad executable head/floor split while preserving the narrow
standalone failure.
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
    "nested_graph_build_a2_colder_witness_execution_consolidation/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__COLDER_WITNESS_EXECUTION_"
    "CONSOLIDATION__CORRELATION_POLARITY__2026_03_20__v1.json"
)
HELPER_CONTROL_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A2_ENTROPY_BRIDGE_HELPER_DECOMPOSITION_CONTROL__CORRELATION_DIVERSITY_FUNCTIONAL__2026_03_20__v1.md"
)
A1_EXEC_ENTRYPOINT = "system_v3/a1_state/A1_ENTROPY_EXECUTABLE_ENTRYPOINT__v1.md"
A1_CORRELATION_EXEC_PACK = "system_v3/a1_state/A1_ENTROPY_CORRELATION_EXECUTABLE_PACK__v1.md"
LIVE_HINTS = "system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md"
A2_DISTILLATION_INPUTS = "system_v3/a2_state/A2_TO_A1_DISTILLATION_INPUTS__v1.md"
NEXT_VALIDATION = "system_v3/a2_state/NEXT_VALIDATION_TARGETS__v1.md"
BRANCH_BUDGET_PACK = "system_v3/a1_state/A1_ENTROPY_BRANCH_BUDGET_AND_MERGE_PACK__v1.md"
HELPER_LIFT_PACK = "system_v3/a1_state/A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "COLDER_WITNESS_EXECUTION_CONSOLIDATION__CORRELATION_POLARITY__2026_03_20__v1.md"
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


def _derive_colder_witness_evidence(root: Path) -> tuple[dict[str, Any], list[str]]:
    evidence = {
        "prior_helper_control_boundary": _find_first_evidence(
            root,
            "prior_helper_control_boundary",
            [
                {
                    "path": HELPER_CONTROL_AUDIT,
                    "contains_any": [
                        "result: HELPER_DECOMPOSITION_CONTROL_CONFIRMED__COMPOUND_TERMS_STAY_PROPOSAL_SIDE",
                        "next_required_lane: COLDER_WITNESS_EXECUTION_CONSOLIDATION__CORRELATION_POLARITY",
                    ],
                },
            ],
        ),
        "broad_executable_head": _find_first_evidence(
            root,
            "broad_executable_head",
            [
                {
                    "path": LIVE_HINTS,
                    "contains_any": [
                        "correlation_polarity = HEAD_READY",
                    ],
                },
                {
                    "path": A1_CORRELATION_EXEC_PACK,
                    "contains_any": [
                        "correlation_polarity remains the honest active entropy-adjacent executable head",
                    ],
                },
                {
                    "path": A1_EXEC_ENTRYPOINT,
                    "contains_any": [
                        "executable head:",
                    ],
                },
            ],
        ),
        "companion_floor": _find_first_evidence(
            root,
            "companion_floor",
            [
                {
                    "path": LIVE_HINTS,
                    "contains_any": [
                        "active companion executable floor:",
                    ],
                },
                {
                    "path": A1_CORRELATION_EXEC_PACK,
                    "contains_any": [
                        "active companion executable floor:",
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
        "narrow_single_term_too_thin": _find_first_evidence(
            root,
            "narrow_single_term_too_thin",
            [
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "single-term `correlation_polarity` local pressure also remains too thin under the current exchange/memo path",
                    ],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "do not currently treat `correlation_polarity` as a narrow executable survivor",
                    ],
                },
                {
                    "path": A1_CORRELATION_EXEC_PACK,
                    "contains_any": [
                        "neither narrower route justifies replacing the current broad executable baseline",
                    ],
                },
            ],
        ),
        "broad_route_real": _find_first_evidence(
            root,
            "broad_route_real",
            [
                {
                    "path": A1_CORRELATION_EXEC_PACK,
                    "contains_any": [
                        "wrapper_status = PASS__EXECUTED_CYCLE",
                    ],
                },
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "shows the correlation-side executable branch is real:",
                    ],
                },
            ],
        ),
        "helper_lift_next_move": _find_first_evidence(
            root,
            "helper_lift_next_move",
            [
                {
                    "path": A2_DISTILLATION_INPUTS,
                    "contains_any": [
                        "the next usable entropy move must lift colder witnesses into a stronger bridge composition instead of collapsing into `density_entropy` alone",
                    ],
                },
                {
                    "path": HELPER_LIFT_PACK,
                    "contains_any": [
                        "The next entropy bridge move should not just make helpers colder.",
                        "It should force helpers to lift into a bridge-capable composition.",
                    ],
                },
                {
                    "path": HELPER_LIFT_PACK,
                    "contains_any": [
                        "Required Lift Composition",
                    ],
                },
            ],
        ),
        "non_claim_structure_heads": _find_first_evidence(
            root,
            "non_claim_structure_heads",
            [
                {
                    "path": A1_EXEC_ENTRYPOINT,
                    "contains_any": [
                        "claim direct admission for `correlation_diversity_functional` or `probe_induced_partition_boundary`,",
                    ],
                },
                {
                    "path": LIVE_HINTS,
                    "contains_any": [
                        "Keep as a late passenger / witness-seeking target while correlation_polarity carries executable pressure.",
                    ],
                },
            ],
        ),
    }
    required = [
        "prior_helper_control_boundary",
        "broad_executable_head",
        "companion_floor",
        "narrow_single_term_too_thin",
        "broad_route_real",
        "helper_lift_next_move",
    ]
    missing = [label for label in required if not evidence[label]]
    return evidence, missing


def run_a2_colder_witness_execution_consolidation(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff = _load_json(_resolve(root, HANDOFF_PACKET))
    prior_audit = _load_text(_resolve(root, HELPER_CONTROL_AUDIT))
    evidence, missing_evidence = _derive_colder_witness_evidence(root)

    result_value = "CORRELATION_POLARITY_BROAD_EXECUTABLE_HEAD_CONFIRMED"
    decision = (
        "Keep the entropy executable branch anchored on the broad correlation-side "
        "route. Current repo-held doctrine confirms correlation_polarity as the "
        "honest executable head with correlation as companion floor, while narrow "
        "single-term pressure remains too thin to replace the broad executable baseline. "
        "The next usable move is helper-lift into stronger bridge composition, not "
        "another narrow standalone pass."
    )
    next_required_lane = "A1_ENTROPY_BRIDGE_HELPER_LIFT_PACK__CORRELATION_POLARITY"
    next_control_surface = str(_resolve(root, HELPER_LIFT_PACK))
    if missing_evidence:
        result_value = "INSUFFICIENT_DOCTRINE_EVIDENCE"
        decision = (
            "Keep the colder-witness executable branch explicit because the cited "
            "repo-held doctrine does not currently provide enough machine-checked "
            "evidence to consolidate the correlation_polarity lane honestly."
        )
        next_required_lane = "MANUAL_COLDER_WITNESS_EXECUTION_REVIEW__CORRELATION_POLARITY"
        next_control_surface = str(_resolve(root, A1_EXEC_ENTRYPOINT))

    result = {
        "schema": "COLDER_WITNESS_EXECUTION_CONSOLIDATION_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "unit_id": str(handoff.get("unit_id", "")),
        "dispatch_id": str(handoff.get("dispatch_id", "")),
        "term": "correlation_polarity",
        "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
        "result": result_value,
        "decision": decision,
        "source_surfaces": [
            str(_resolve(root, HELPER_CONTROL_AUDIT)),
            str(_resolve(root, A1_EXEC_ENTRYPOINT)),
            str(_resolve(root, A1_CORRELATION_EXEC_PACK)),
            str(_resolve(root, LIVE_HINTS)),
            str(_resolve(root, A2_DISTILLATION_INPUTS)),
            str(_resolve(root, NEXT_VALIDATION)),
            str(_resolve(root, HELPER_LIFT_PACK)),
            str(_resolve(root, BRANCH_BUDGET_PACK)),
        ],
        "derived_evidence": evidence,
        "missing_evidence": missing_evidence,
        "prior_boundary_summary": {
            "has_helper_control_audit": bool(prior_audit.strip()),
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
            "executable_head": "correlation_polarity",
            "active_companion_floor": ["correlation"],
            "accepted_bridge_witnesses": ["polarity", "density_entropy"],
            "route_status": "BROAD_EXECUTABLE_BRANCH_ACTIVE",
            "narrow_profile_status": "TOO_THIN_FOR_STANDALONE_HEAD",
        },
        "blockers": [
            "single-term or narrow packet-only correlation_polarity routes remain too thin to replace the broad executable baseline",
            "colder-witness-only pressure remains a boundary probe and should not become the default entropy route by itself",
            "the next usable entropy move must lift colder witnesses into stronger bridge composition before broader control tightening matters",
            "direct structure-side heads remain passenger or witness-side; this pass does not lift them into executable-head status",
        ],
        "next_required_lane": next_required_lane,
        "next_control_surface": next_control_surface,
        "non_claims": [
            "This pass does not materialize A1_STRIPPED or A1_CARTRIDGE.",
            "This pass does not treat correlation_polarity as a narrow standalone executable survivor.",
            "This pass does not claim correlation_diversity_functional has landed as a direct executable head.",
            "This pass does not reopen alias-first or route-invention work as the active next move.",
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
        "# COLDER_WITNESS_EXECUTION_CONSOLIDATION__CORRELATION_POLARITY__2026_03_20__v1",
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
        f"- executable_head: {result['grounded_read']['executable_head']}",
        "- active_companion_floor:",
    ])
    for item in result["grounded_read"]["active_companion_floor"]:
        lines.append(f"  - {item}")
    lines.append("- accepted_bridge_witnesses:")
    for item in result["grounded_read"]["accepted_bridge_witnesses"]:
        lines.append(f"  - {item}")
    lines.extend([
        f"- route_status: {result['grounded_read']['route_status']}",
        f"- narrow_profile_status: {result['grounded_read']['narrow_profile_status']}",
        "",
        "## Prior Boundary",
        f"- has_helper_control_audit: {result['prior_boundary_summary']['has_helper_control_audit']}",
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
    output = run_a2_colder_witness_execution_consolidation(str(REPO_ROOT))
    print(json.dumps(output, indent=2, sort_keys=True))
