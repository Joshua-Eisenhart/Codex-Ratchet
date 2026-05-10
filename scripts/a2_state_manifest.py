#!/usr/bin/env python3
"""Refresh the tracked integrity manifest for ignored a2_state receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "system_v5" / "evidence" / "a2_state_manifest_2026-05-10.json"
NORMALIZATION_QUEUE_PATH = ROOT / "system_v4" / "probes" / "a2_state" / "sim_results" / "actual_lego_normalization_queue.json"
WORK_MATRIX_PATH = ROOT / "system_v4" / "probes" / "a2_state" / "sim_results" / "actual_lego_work_matrix.json"
DEFAULT_EXTRA_PATHS = (
    "system_v4/probes/a2_state/sim_results/actual_lego_work_matrix.json",
    "system_v4/probes/a2_state/sim_results/actual_lego_source_label_normalization_ledger.json",
    "system_v4/probes/a2_state/sim_results/actual_lego_process_receipt_audit.json",
    "system_v4/probes/a2_state/sim_results/actual_lego_indexed_receipt_audit.json",
    "system_v4/probes/a2_state/sim_results/actual_lego_coupling_receipt_audit.json",
    "system_v4/probes/a2_state/sim_results/operator_geometry_closure_ablation_results.json",
    "system_v4/probes/a2_state/sim_results/operator_geometry_single_pair_exclusion_results.json",
    "system_v4/probes/a2_state/sim_results/operator_geometry_multi_pair_exclusions_results.json",
    "system_v4/probes/a2_state/sim_results/operator_geometry_exclusion_assembly_audit_results.json",
    "system_v4/probes/a2_state/sim_results/operator_geometry_shared_state_coexistence_results.json",
    "system_v4/probes/a2_state/sim_results/graph_cell_complex_coexistence_results.json",
    "system_v4/probes/a2_state/sim_results/constraint_manifold_L0_L1_results.json",
    "system_v4/probes/a2_state/sim_results/commutative_geometry_collapse_results.json",
    "system_v4/probes/a2_state/sim_results/gauge_group_correspondence_results.json",
    "system_v4/probes/a2_state/sim_results/viability_vs_attractor_results.json",
)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def item(path: Path) -> dict:
    raw = path.read_bytes()
    stat = path.stat()
    return {
        "bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
        "path": rel(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def read_queue_row_count() -> int:
    if not NORMALIZATION_QUEUE_PATH.exists():
        return 0
    payload = json.loads(NORMALIZATION_QUEUE_PATH.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])
    return len(rows) if isinstance(rows, list) else 0


def read_work_matrix_result_paths() -> list[str]:
    if not WORK_MATRIX_PATH.exists():
        return []
    payload = json.loads(WORK_MATRIX_PATH.read_text(encoding="utf-8"))
    paths = []
    for row in payload.get("rows", []):
        result_path = row.get("result_path")
        if result_path:
            path = Path(result_path)
            paths.append(rel(path if path.is_absolute() else ROOT / path))
    return paths


def is_frontier_receipt(row: dict) -> bool:
    path = row["path"]
    return path.startswith("system_v4/probes/a2_state/sim_results/") and path.endswith(
        ("_results.json", "_result.json")
    )


def is_a2_state_sim_result_item(row: dict) -> bool:
    return row["path"].startswith("system_v4/probes/a2_state/sim_results/")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--extra-path", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_path = args.out if args.out.is_absolute() else ROOT / args.out
    manifest = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    previous_paths = [row.get("path") for row in manifest.get("items", []) if row.get("path")]
    requested_paths = list(
        dict.fromkeys([*previous_paths, *DEFAULT_EXTRA_PATHS, *read_work_matrix_result_paths(), *args.extra_path])
    )

    items = []
    missing = []
    for requested in requested_paths:
        path = ROOT / requested
        if not path.exists():
            missing.append(requested)
            continue
        items.append(item(path))

    manifest.update(
        {
            "schema": "codex_ratchet.a2_state_manifest.v1",
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "purpose": (
                "Tracked integrity anchor for ignored local a2_state lego frontier receipts generated "
                "during the mass-parallel lego frontier run. Receipt JSONs remain ignored by "
                ".gitignore:a2_state/; tracked visualizer payloads are included when refreshed from "
                "ignored receipts. Regenerate matrix/result receipts before this manifest so hashes "
                "reflect current disk state."
            ),
            "source_registry": "system_v4/probes/a2_state/sim_results/actual_lego_registry.json",
            "source_queue": "system_v4/probes/a2_state/sim_results/actual_lego_normalization_queue.json",
            "frontier_receipt_count": sum(1 for row in items if is_frontier_receipt(row)),
            "a2_state_sim_results_item_count": sum(1 for row in items if is_a2_state_sim_result_item(row)),
            "queue_row_count": read_queue_row_count(),
            "manifest_item_count": len(items),
            "missing_count": len(missing),
            "missing_paths": missing,
            "items": items,
        }
    )
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {rel(out_path)}")
    print(json.dumps({k: manifest[k] for k in ("frontier_receipt_count", "manifest_item_count", "missing_count")}, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
