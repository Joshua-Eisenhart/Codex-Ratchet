#!/usr/bin/env python3
"""
qit_torus_type_repair_gap_report.py

Bounded repair-gap report for the torus-placement and type-split carrier lane.

This reads the existing Hopf/Weyl evidence audit and turns its
carrier_evidence_summary into a concrete, non-promotional repair map.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "system_v4" / "a2_state" / "audit_logs"
SOURCE_JSON = AUDIT_DIR / "QIT_HOPF_WEYL_EVIDENCE_AUDIT__CURRENT__v1.json"
OUT_JSON = AUDIT_DIR / "QIT_TORUS_TYPE_REPAIR_GAP_REPORT__CURRENT__v1.json"
OUT_MD = AUDIT_DIR / "QIT_TORUS_TYPE_REPAIR_GAP_REPORT__CURRENT__v1.md"


def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _git_status_porcelain(paths: list[Path] | None = None) -> list[str]:
    cmd = ["git", "status", "--short"]
    if paths:
        cmd.append("--")
        cmd.extend(str(path) for path in paths)
    try:
        output = subprocess.check_output(cmd, cwd=str(REPO_ROOT), text=True)
    except Exception:
        return []
    return [line.rstrip() for line in output.splitlines() if line.strip()]


def build_qit_torus_type_repair_gap_report() -> dict[str, Any]:
    source = _load_json(SOURCE_JSON)
    summary = source.get("carrier_evidence_summary", {})
    torus = summary.get("torus_placement_evidence", {})
    type_split = summary.get("type_split_evidence", {})
    branch_nodes_present = bool(type_split.get("weyl_branch_nodes_present"))
    script_path = Path(__file__).resolve()

    payload = {
        "schema": "QIT_TORUS_TYPE_REPAIR_GAP_REPORT_v1",
        "generated_utc": _utc_iso(),
        "status": "bounded_non_promotional_gap_summary",
        "report_surface": {
            "surface_class": "tracked_current_workspace_report",
            "represents": (
                "current workspace torus/type repair-gap state at generation time; may differ from the "
                "last committed snapshot until tracked CURRENT artifacts are committed"
            ),
            "tracked_report_files": [str(OUT_JSON), str(OUT_MD)],
            "tracked_report_files_dirty_before_generation": _git_status_porcelain([OUT_JSON, OUT_MD]),
            "script_path": str(script_path),
            "script_sha256": _sha256_path(script_path),
            "git_sha": _git_sha(),
        },
        "audit_boundary": {
            "audit_only": True,
            "nonoperative": True,
            "do_not_promote": True,
            "promotion_claim": "none",
            "scope_note": "owner carrier evidence + negative witnesses + runtime alignment only",
        },
        "derived_from": {
            "carrier_evidence_summary_path": str(SOURCE_JSON),
            "owner_snapshot_hash": torus.get("owner_graph_content_hash", type_split.get("owner_graph_content_hash", "")),
        },
        "repair_gap_summary": {
            "status": "bounded_non_promotional_gap_summary",
            "promotion_claim": "none",
            "torus_placement": {
                "supported_now": [
                    "owner graph has 3 torus carrier nodes",
                    "owner graph has 2 torus-nesting edges",
                    "owner graph has 32 STAGE_ON_TORUS edges",
                    "owner graph supports stage-to-torus carrier assignment counts",
                ],
                "aligned_only": [
                    "runtime samples align to the same owner engine/stage ids",
                    "sidecar carrier summaries are hash-aligned to the current owner snapshot",
                ],
                "missing": [
                    "no direct runtime bridge packet for torus-placement witnesses",
                    "no promoted torus 2-cells in owner graph",
                    "no runtime state graph proving torus occupancy over time",
                ],
                "forbidden_to_infer": [
                    "validated Hopf geometry",
                    "promoted torus topology semantics",
                    "runtime proof that torus placement is physically realized",
                    "promotion-ready torus evidence",
                ],
                "relevant_negative_witnesses": torus.get("relevant_negative_witnesses", []),
                "torus_public_ids": torus.get("torus_public_ids", []),
            },
            "type_split": {
                "supported_now": [
                    "owner graph has 2 engine-family nodes",
                    "owner graph has 1 CHIRALITY_COUPLING edge",
                    "owner graph has stage ownership split by engine family",
                    "negative witnesses exist for no-chirality and type-flatten",
                ],
                "aligned_only": [
                    "runtime bridge resolves type-split alignment to owner engine ids",
                    "runtime bridge maps neg_type_flatten to the current engine-family ids",
                ],
                "missing": [
                    "no promoted chirality algebra payload in owner truth",
                    "no runtime/history graph proving branch-level type semantics",
                ],
                "forbidden_to_infer": [
                    "live Weyl branch semantics",
                    "promoted chirality truth beyond engine-family split",
                    "validated clifford/pseudoscalar proof in owner truth",
                    "promotion-ready type-split evidence",
                ],
                "relevant_negative_witnesses": type_split.get("relevant_negative_witnesses", []),
                "engine_public_ids": type_split.get("engine_public_ids", []),
            },
        },
        "minimal_next_repairs": {
            "torus_placement": [
                "add a bounded runtime-side torus join table keyed by existing stage ids",
                "preserve torus-targeted negatives as explicit bounded context until a faithful owner concept exists",
                "avoid promoting torus 2-cells before round-trip owner representation exists",
            ],
            "type_split": [
                "keep type split anchored at the two engine owner ids",
                "treat admitted WEYL_BRANCH owner nodes as anchor-level structure only until branch-runtime and promotion gates are satisfied",
                "treat chirality algebra as candidate sidecar evidence only until promotion gates are satisfied",
            ],
        },
    }
    if branch_nodes_present:
        payload["repair_gap_summary"]["type_split"]["supported_now"].append(
            "owner graph has 2 live WEYL_BRANCH nodes anchored to the engine families"
        )
        payload["repair_gap_summary"]["type_split"]["aligned_only"].append(
            "sidecar readiness reports materialized branch anchors, not just engine-pair-only readiness"
        )
    else:
        payload["repair_gap_summary"]["type_split"]["aligned_only"].append(
            "sidecar readiness says engine-pair-only, not branch-level"
        )
        payload["repair_gap_summary"]["type_split"]["missing"].insert(
            0, "no live WEYL_BRANCH owner nodes"
        )
    return payload


def _render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["repair_gap_summary"]
    boundary = payload["audit_boundary"]
    surface = payload["report_surface"]
    lines = [
        "# QIT Torus/Type Repair Gap Report",
        "",
        f"- status: `{payload['status']}`",
        f"- generated_utc: `{payload['generated_utc']}`",
        "",
        "## Report Surface",
        f"- surface_class: `{surface['surface_class']}`",
        f"- represents: `{surface['represents']}`",
        f"- git_sha: `{surface['git_sha']}`",
        "",
        "## Audit Boundary",
        f"- audit_only: `{boundary['audit_only']}`",
        f"- nonoperative: `{boundary['nonoperative']}`",
        f"- do_not_promote: `{boundary['do_not_promote']}`",
        f"- promotion_claim: `{boundary['promotion_claim']}`",
        "",
        "## Torus Placement",
        "- supported_now:",
        *[f"  - {item}" for item in summary["torus_placement"]["supported_now"]],
        "- aligned_only:",
        *[f"  - {item}" for item in summary["torus_placement"]["aligned_only"]],
        "- missing:",
        *[f"  - {item}" for item in summary["torus_placement"]["missing"]],
        "- forbidden_to_infer:",
        *[f"  - {item}" for item in summary["torus_placement"]["forbidden_to_infer"]],
        "",
        "## Type Split",
        "- supported_now:",
        *[f"  - {item}" for item in summary["type_split"]["supported_now"]],
        "- aligned_only:",
        *[f"  - {item}" for item in summary["type_split"]["aligned_only"]],
        "- missing:",
        *[f"  - {item}" for item in summary["type_split"]["missing"]],
        "- forbidden_to_infer:",
        *[f"  - {item}" for item in summary["type_split"]["forbidden_to_infer"]],
        "",
        "## Minimal Next Repairs",
        "- torus_placement:",
        *[f"  - {item}" for item in payload["minimal_next_repairs"]["torus_placement"]],
        "- type_split:",
        *[f"  - {item}" for item in payload["minimal_next_repairs"]["type_split"]],
        "",
    ]
    return "\n".join(lines)


def write_qit_torus_type_repair_gap_report() -> dict[str, Any]:
    payload = build_qit_torus_type_repair_gap_report()
    _write_json(OUT_JSON, payload)
    _write_text(OUT_MD, _render_markdown(payload))
    return payload


def main() -> None:
    payload = write_qit_torus_type_repair_gap_report()
    print("QIT torus/type repair-gap report written:")
    print(f"  JSON: {OUT_JSON}")
    print(f"  MD:   {OUT_MD}")
    print(f"  status: {payload['status']}")


if __name__ == "__main__":
    main()
