#!/usr/bin/env python3
"""
Create long explicit alias names for system_v3 surfaces using symlinks.

This is a non-destructive compatibility layer:
- Existing short names stay in place.
- Long explicit names are added as symlink aliases.
"""

from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TOP_LEVEL_ALIASES = {
    "a2_derived_indices_noncanonical": "a2_noncanonical_derived_index_cache_surface",
    "a2_state": "a2_persistent_context_and_memory_surface",
    "conformance": "conformance_and_fixture_validation_surface",
    "control_plane_bundle_work": "control_plane_bundle_authoring_workspace_surface",
    "public_facing_docs": "public_facing_documentation_surface",
    "runs": "deterministic_campaign_run_surface",
    "runtime": "deterministic_runtime_execution_surface",
    "specs": "noncanonical_draft_specification_surface",
    "tools": "deterministic_operational_tooling_surface",
}

RUN_SUBDIR_ALIASES = {
    "a1_inbox": "a1_packet_inbox_surface",
    "a1_strategies": "optional_a1_strategy_duplicate_surface",
    "outbox": "deterministic_outbound_export_block_cache_surface",
    "reports": "deterministic_compile_and_kernel_report_surface",
    "sim": "optional_plaintext_sim_evidence_duplicate_surface",
    "snapshots": "optional_plaintext_snapshot_duplicate_surface",
    "zip_packets": "zip_protocol_v2_packet_journal_surface",
}


def _safe_symlink(target: Path, link: Path) -> tuple[str, str]:
    if not target.exists():
        return (str(link), "target_missing")
    if link.exists() or link.is_symlink():
        if link.is_symlink() and link.resolve() == target.resolve():
            return (str(link), "ok_existing")
        return (str(link), "conflict_exists")
    # Relative link keeps tree relocatable.
    rel_target = os.path.relpath(str(target), str(link.parent))
    link.symlink_to(rel_target)
    return (str(link), "created")


def main() -> int:
    rows: list[tuple[str, str]] = []
    for short_name, long_name in sorted(TOP_LEVEL_ALIASES.items()):
        target = ROOT / short_name
        link = ROOT / long_name
        rows.append(_safe_symlink(target, link))

    runs_root = ROOT / "runs"
    if runs_root.exists():
        for run_dir in sorted([p for p in runs_root.iterdir() if p.is_dir() and not p.name.startswith("_")]):
            for short_name, long_name in sorted(RUN_SUBDIR_ALIASES.items()):
                target = run_dir / short_name
                link = run_dir / long_name
                rows.append(_safe_symlink(target, link))

    created = sum(1 for _, status in rows if status == "created")
    conflicts = sum(1 for _, status in rows if status == "conflict_exists")
    missing = sum(1 for _, status in rows if status == "target_missing")
    print(
        {
            "schema": "EXPLICIT_NAME_ALIAS_SURFACE_RESULT_v1",
            "root": str(ROOT),
            "created": created,
            "conflicts": conflicts,
            "target_missing": missing,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
