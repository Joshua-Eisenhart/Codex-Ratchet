#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_DIR = REPO_ROOT / "system_v3" / "runs"
ARCHIVE_HEAT_DUMPS_DIR = REPO_ROOT.parent / "Codex_Ratchet__archive" / "HEAT_DUMPS"


ENTROPY_CLUSTER_MAP = {
    "NEG_CLASSICAL_TEMPERATURE": "Cluster A — Thermal Scalar Import",
    "NEG_CLASSICAL_TIME": "Cluster B — Time / Bath Leakage",
    "NEG_CONTINUOUS_BATH": "Cluster B — Time / Bath Leakage",
    "NEG_COMMUTATIVE_ASSUMPTION": "Cluster C — Cross-Basin Structural Defaults",
    "NEG_EUCLIDEAN_METRIC": "Cluster C — Cross-Basin Structural Defaults",
    "NEG_INFINITE_SET": "Cluster C — Cross-Basin Structural Defaults",
    "NEG_INFINITE_RESOLUTION": "Cluster C — Cross-Basin Structural Defaults",
    "NEG_PRIMITIVE_EQUALS": "Cluster C — Cross-Basin Structural Defaults",
}


@dataclass
class ReportRow:
    run_id: str
    report_path: Path
    status: str
    kill_tokens: dict[str, int]
    graveyard_count: int
    kill_log_count: int
    sim_registry_count: int


@dataclass(frozen=True)
class SnapshotDescriptor:
    snapshot_label: str
    source_surface: str | None = None


ENTROPY_SNAPSHOT_RULES: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_REFORMULATION_BROAD_\d+$"),
        "entropy-bridge reformulation broad profile",
        str(REPO_ROOT / "system_v3" / "run_anchor_surface" / "RUN_ANCHOR__ENTROPY_BRIDGE_REFINEMENT_BROAD_CLUSTER__v1.md"),
    ),
    (
        re.compile(r"RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_RESIDUE_BROAD_\d+$"),
        "entropy-bridge residue broad profile",
        str(REPO_ROOT / "system_v3" / "run_anchor_surface" / "RUN_ANCHOR__ENTROPY_BRIDGE_RESIDUE_BROAD_CLUSTER__v1.md"),
    ),
    (
        re.compile(r"RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_THERMAL_TIME_BROAD_\d+$"),
        "entropy-bridge thermal/time broad profile",
        str(REPO_ROOT / "system_v3" / "run_anchor_surface" / "RUN_ANCHOR__ENTROPY_BRIDGE_REFINEMENT_BROAD_CLUSTER__v1.md"),
    ),
    (
        re.compile(r"RUN_GRAVEYARD_VALIDITY_ENTROPY_STRUCTURE_LOCAL_\d+$"),
        "entropy-structure narrowed local rerun profile",
        str(REPO_ROOT / "system_v3" / "run_anchor_surface" / "RUN_ANCHOR__ENTROPY_STRUCTURE_FAMILY__v1.md"),
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a graveyard failure-topology summary from run audit reports."
    )
    parser.add_argument(
        "--run-regex",
        required=True,
        help="Regex matched against run directory names under system_v3/runs.",
    )
    parser.add_argument(
        "--output-md",
        required=True,
        help="Workspace-relative or absolute markdown output path.",
    )
    parser.add_argument(
        "--output-json",
        help="Optional JSON output path for machine-readable topology data.",
    )
    parser.add_argument(
        "--profile",
        choices=["generic", "entropy"],
        default="generic",
        help="Optional cluster projection profile.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=12,
        help="Number of top kill tokens to retain in summaries.",
    )
    return parser.parse_args()


def iter_report_paths(run_regex: str) -> Iterable[Path]:
    pattern = re.compile(run_regex)
    candidates: dict[str, Path] = {}

    for report_path in sorted(RUNS_DIR.glob("*/reports/a1_operational_integrity_audit_report.json")):
        run_id = report_path.parents[1].name
        if pattern.search(run_id):
            candidates.setdefault(run_id, report_path)

    if ARCHIVE_HEAT_DUMPS_DIR.exists():
        for report_path in sorted(ARCHIVE_HEAT_DUMPS_DIR.glob("**/reports/a1_operational_integrity_audit_report.json")):
            run_id = report_path.parents[1].name
            if pattern.search(run_id):
                candidates.setdefault(run_id, report_path)

    for run_id in sorted(candidates):
        yield candidates[run_id]


def load_report(report_path: Path) -> ReportRow:
    payload = json.loads(report_path.read_text())
    metrics = payload.get("metrics", {})
    return ReportRow(
        run_id=report_path.parents[1].name,
        report_path=report_path,
        status=payload.get("status", "UNKNOWN"),
        kill_tokens=metrics.get("kill_tokens", {}) or {},
        graveyard_count=int(metrics.get("graveyard_count", 0) or 0),
        kill_log_count=int(metrics.get("kill_log_count", 0) or 0),
        sim_registry_count=int(metrics.get("sim_registry_count", 0) or 0),
    )


def build_cluster_rows(counter: Counter[str], profile: str) -> list[tuple[str, list[tuple[str, int]], int]]:
    if profile != "entropy":
        return []

    grouped: dict[str, list[tuple[str, int]]] = {}
    for token, count in counter.most_common():
        cluster_name = ENTROPY_CLUSTER_MAP.get(token)
        if cluster_name:
            grouped.setdefault(cluster_name, []).append((token, count))

    rows = []
    for cluster_name, items in grouped.items():
        cluster_total = sum(count for _, count in items)
        rows.append((cluster_name, items, cluster_total))
    rows.sort(key=lambda item: item[2], reverse=True)
    return rows


def to_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return REPO_ROOT / value


def describe_row(row: ReportRow, profile: str) -> SnapshotDescriptor:
    if profile == "entropy":
        for pattern, snapshot_label, source_surface in ENTROPY_SNAPSHOT_RULES:
            if pattern.search(row.run_id):
                return SnapshotDescriptor(snapshot_label=snapshot_label, source_surface=source_surface)
    return SnapshotDescriptor(snapshot_label=row.run_id)


def build_source_surfaces(rows: list[ReportRow], profile: str) -> list[str]:
    surfaces: list[str] = []
    seen: set[str] = set()
    for row in rows:
        descriptor = describe_row(row, profile)
        source_surface = descriptor.source_surface or str(row.report_path)
        if source_surface not in seen:
            seen.add(source_surface)
            surfaces.append(source_surface)
    return surfaces


def render_markdown(
    rows: list[ReportRow],
    counter: Counter[str],
    top_n: int,
    profile: str,
) -> str:
    stable_tokens = [
        token
        for token, _ in counter.most_common(top_n)
        if all(token in row.kill_tokens for row in rows)
    ]
    cluster_rows = build_cluster_rows(counter, profile)
    source_surfaces = build_source_surfaces(rows, profile)

    lines: list[str] = []
    lines.append("# GRAVEYARD_FAILURE_TOPOLOGY__AUTO__v1")
    lines.append("")
    lines.append("STATUS: GENERATED / NONCANONICAL / ACTIVE CONTROL SURFACE")
    lines.append("")
    lines.append("## 1) Source Surfaces")
    for source_surface in source_surfaces:
        lines.append(f"- `{source_surface}`")
    lines.append("")
    lines.append("## 2) Aggregate Kill Tokens")
    for token, count in counter.most_common(top_n):
        lines.append(f"- `{token}` = {count}")
    lines.append("")
    lines.append("## 3) Stable Frontier Tokens")
    if stable_tokens:
        for token in stable_tokens:
            lines.append(f"- `{token}`")
    else:
        lines.append("- none")
    lines.append("")

    if cluster_rows:
        lines.append("## 4) Cluster Projection")
        for cluster_name, items, cluster_total in cluster_rows:
            lines.append(f"### {cluster_name}")
            lines.append(f"- cluster_total = {cluster_total}")
            for token, count in items:
                lines.append(f"- `{token}` = {count}")
            lines.append("")

    lines.append("## 5) Per-Snapshot Projection")
    for row in rows:
        descriptor = describe_row(row, profile)
        lines.append(f"### {descriptor.snapshot_label}")
        if descriptor.source_surface:
            lines.append(f"- normalized source surface = `{descriptor.source_surface}`")
        lines.append(f"- status = `{row.status}`")
        lines.append(f"- graveyard_count = {row.graveyard_count}")
        lines.append(f"- kill_log_count = {row.kill_log_count}")
        lines.append(f"- sim_registry_count = {row.sim_registry_count}")
        for token, count in Counter(row.kill_tokens).most_common(min(top_n, len(row.kill_tokens))):
            lines.append(f"- `{token}` = {count}")
        lines.append("")

    lines.append("## 6) Interpretation Rule")
    lines.append("- This file is a generated control surface.")
    lines.append("- It may steer A2/A1 rescue, pruning, and negative pressure.")
    lines.append("- It does not promote earned state or override lower-loop evidence.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    report_paths = list(iter_report_paths(args.run_regex))
    if not report_paths:
        raise SystemExit(f"No audit reports matched run regex: {args.run_regex}")

    rows = [load_report(path) for path in report_paths]
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.kill_tokens)

    md_path = to_path(args.output_md)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_markdown(rows, counter, args.top_n, args.profile))

    if args.output_json:
        json_path = to_path(args.output_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        source_surfaces = build_source_surfaces(rows, args.profile)
        per_snapshot = []
        for row in rows:
            descriptor = describe_row(row, args.profile)
            per_snapshot.append(
                {
                    "snapshot_label": descriptor.snapshot_label,
                    "source_surface": descriptor.source_surface or str(row.report_path),
                    "status": row.status,
                    "graveyard_count": row.graveyard_count,
                    "kill_log_count": row.kill_log_count,
                    "sim_registry_count": row.sim_registry_count,
                    "kill_tokens": row.kill_tokens,
                }
            )
        payload = {
            "schema": "graveyard_failure_topology_auto_v1",
            "profile": args.profile,
            "selection_mode": "generator_cli_run_regex_internal",
            "provenance_mode": "normalized_anchor_surface",
            "source_runs": source_surfaces,
            "source_surfaces": source_surfaces,
            "aggregate_kill_tokens": dict(counter.most_common()),
            "stable_frontier_tokens": [
                token for token, _ in counter.most_common(args.top_n) if all(token in row.kill_tokens for row in rows)
            ],
            "cluster_projection": [
                {
                    "cluster_name": cluster_name,
                    "cluster_total": cluster_total,
                    "tokens": [{"token": token, "count": count} for token, count in items],
                }
                for cluster_name, items, cluster_total in build_cluster_rows(counter, args.profile)
            ],
            "per_run": per_snapshot,
            "per_snapshot": per_snapshot,
        }
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
