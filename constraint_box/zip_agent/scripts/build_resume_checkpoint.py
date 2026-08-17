#!/usr/bin/env python3
"""Build the current compact ConstraintBox resume ZIP from repo-held bytes."""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from constraintbox_zip_agent.project_ledger import ProjectLedger
from constraintbox_zip_agent.protocol import sha256_bytes, validate_packet
from constraintbox_zip_agent.resume_checkpoint import build_resume_checkpoint_packet


MATERIAL_PATHS = (
    "constraint_box/CB_READ_THIS_FIRST.md",
    "constraint_box/status/CURRENT_LOCAL_ESTATE.json",
    "constraint_box/status/CURRENT_LOCAL_ESTATE.md",
    "constraint_box/receipts/maintenance/branch-consolidation-session-1-corrected.json",
    "constraint_box/receipts/handoffs/2026-08-16-grok-wave-estate-to-codex.json",
    "constraint_box/zip_agent/project_state/CURRENT.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-owner-crash-resume-directive.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-branch-consolidation-progress.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-resume-checkpoint-emitted.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-manifold-campaign-exact-recovery.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-manifold-campaign-rerun.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-resume-checkpoint-2-emitted.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-checkpoint-ratchet-hardening.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-resume-checkpoint-3-emitted.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-crash-resume-prototype-closeout.md",
    "constraint_box/zip_agent/project_state/inbox/20260817-wave-self-loop-crash-state-repair.md",
    "constraint_box/receipts/wave_self_loop/latest.json",
    "constraint_box/zip_agent/src/constraintbox_zip_agent/resume_checkpoint.py",
    "constraint_box/zip_agent/src/constraintbox_zip_agent/project_ledger.py",
    "constraint_box/zip_agent/src/constraintbox_zip_agent/protocol.py",
    "constraint_box/zip_agent/src/constraintbox_zip_agent/runtime.py",
    "constraint_box/zip_agent/scripts/build_resume_checkpoint.py",
    "constraint_box/zip_agent/tests/test_resume_checkpoint.py",
    "constraint_box/zip_agent/tests/test_project_ledger.py",
)

NEXT_ACTIONS = (
    "Verify the append-only project ledger before trusting the derived current view.",
    "Refresh CURRENT_LOCAL_ESTATE and keep Light, external JAX, and Heavy distinct.",
    "Recover the lost manifold campaign byte-exactly or rerun from repo-held source; never reconstruct it approximately.",
    "Validate, run, and verify this ZIP before handing work to another model.",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--project-state", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--captured-at")
    args = parser.parse_args()
    repo = args.repo.resolve(strict=True)
    project_state = args.project_state.resolve(strict=True)
    materials: dict[str, bytes] = {}
    for relative in MATERIAL_PATHS:
        path = (repo / relative).resolve(strict=True)
        if repo not in path.parents:
            raise SystemExit(f"material outside repo: {path}")
        materials[relative] = path.read_bytes()
    ledger_binding = ProjectLedger(project_state).verify()
    captured_at = args.captured_at or dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    packet = build_resume_checkpoint_packet(
        materials=materials,
        ledger_binding=ledger_binding,
        next_actions=NEXT_ACTIONS,
        captured_at=captured_at,
    )
    validated = validate_packet(packet)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(packet)
    print(
        json.dumps(
            {
                "disposition": "RESUME_CHECKPOINT_BUILT_LOCAL",
                "output": str(args.output.resolve()),
                "packet_sha256": sha256_bytes(packet),
                "job_id": validated.manifest.job_id,
                "material_count": len(materials),
                "ledger_event_count": ledger_binding["event_count"],
                "ledger_head_sha256": ledger_binding["head_sha256"],
                "promotion_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
