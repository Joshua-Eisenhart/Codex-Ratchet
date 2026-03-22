"""
a1_stripped_exact_term_aligner.py

Correction-first pass for exact stripped-term admissibility. This pass resolves
whether a single stripped alias term is actually supported by current repo-held
doctrine, writes an explicit audit artifact, and then re-materializes the
bounded stripped owner graph from that corrected doctrine.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.a1_stripped_graph_builder import write_a1_stripped_graph


HANDOFF_PACKET = (
    "system_v4/a2_state/launch_bundles/"
    "nested_graph_build_a1_stripped_exact_term_pairwise_correlation_spread_functional/"
    "NESTED_GRAPH_BUILD_WORKER_LAUNCH_HANDOFF__A1_STRIPPED_EXACT_TERM__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL__2026_03_20__v1.json"
)
STRIPPED_GRAPH = "system_v4/a1_state/a1_stripped_graph_v1.json"
CARTRIDGE_GRAPH = "system_v4/a1_state/a1_cartridge_graph_v1.json"
LIVE_HINTS = "system_v3/a1_state/A1_INTEGRATION_BATCH__LIVE_FAMILY_HINT_COVERAGE__v1.md"
ALIAS_LIFT = "system_v3/a1_state/A1_ENTROPY_DIVERSITY_ALIAS_LIFT_PACK__v1.md"
CARTRIDGE_REVIEW = "system_v3/a1_state/A1_CARTRIDGE_REVIEW__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md"
CROSS_JUDGMENT = "system_v3/a1_state/A1_CARTRIDGE_REVIEW__ACTIVE_FAMILY_CROSS_JUDGMENT__v1.md"
ROSETTA_BATCH = "system_v3/a1_state/A1_ROSETTA_BATCH__CORRELATION_DIVERSITY_FUNCTIONAL__v1.md"
ANCHOR = "system_v3/run_anchor_surface/RUN_ANCHOR__ENTROPY_DIVERSITY_FAMILY__v1.md"
REGEN = "system_v3/run_anchor_surface/RUN_REGENERATION_WITNESS__ENTROPY_DIVERSITY_FAMILY__v1.md"
OUTPUT_AUDIT = (
    "system_v4/a2_state/audit_logs/"
    "A1_STRIPPED_EXACT_TERM_ALIGNMENT__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL__2026_03_20__v1.md"
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


def run_a1_stripped_exact_term_alignment(workspace_root: str) -> dict[str, Any]:
    root = Path(workspace_root).resolve()
    handoff = _load_json(_resolve(root, HANDOFF_PACKET))
    stripped_before = _load_json(_resolve(root, STRIPPED_GRAPH))
    cartridge_before = _load_json(_resolve(root, CARTRIDGE_GRAPH))

    write_result = write_a1_stripped_graph(str(root))
    stripped_after = _load_json(_resolve(root, STRIPPED_GRAPH))

    report = {
        "schema": "A1_STRIPPED_EXACT_TERM_ALIGNMENT_AUDIT_v1",
        "generated_utc": _utc_iso(),
        "term": "pairwise_correlation_spread_functional",
        "result": "CONFIRMED_WITNESS_ONLY",
        "decision": (
            "Do not materialize A1_STRIPPED::pairwise_correlation_spread_functional. "
            "The exact stripped alias remains witness-side only under current doctrine."
        ),
        "handoff_packet": str(_resolve(root, HANDOFF_PACKET)),
        "source_surfaces": [
            str(_resolve(root, LIVE_HINTS)),
            str(_resolve(root, ALIAS_LIFT)),
            str(_resolve(root, CARTRIDGE_REVIEW)),
            str(_resolve(root, CROSS_JUDGMENT)),
            str(_resolve(root, ROSETTA_BATCH)),
            str(_resolve(root, ANCHOR)),
            str(_resolve(root, REGEN)),
        ],
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
            "blocked_terms": stripped_after.get("blocked_terms", []),
        },
        "write_result": write_result,
        "non_claims": [
            "This pass does not upgrade the alias term into PASSENGER_ONLY.",
            "This pass does not claim a replacement stripped landing already exists.",
            "This pass does not materialize A1_CARTRIDGE.",
        ],
    }

    audit_path = _resolve(root, OUTPUT_AUDIT)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# A1_STRIPPED_EXACT_TERM_ALIGNMENT__PAIRWISE_CORRELATION_SPREAD_FUNCTIONAL__2026_03_20__v1",
        "",
        f"generated_utc: {report['generated_utc']}",
        f"result: {report['result']}",
        f"decision: {report['decision']}",
        "",
        "## Source Surfaces",
    ]
    for item in report["source_surfaces"]:
        lines.append(f"- {item}")
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
        "- blocked_terms:",
    ])
    for item in report["after"]["blocked_terms"]:
        lines.append(f"  - {item['term']}: {item['reason']}")
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
    result = run_a1_stripped_exact_term_alignment(str(REPO_ROOT))
    print(json.dumps(result, indent=2, sort_keys=True))
