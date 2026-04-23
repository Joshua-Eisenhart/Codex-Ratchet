"""Smoke test for the hardened skill improver operator."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.skill_improver_operator import (
    WRITE_APPROVAL_TOKEN,
    run_skill_improver,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        target = Path(td) / "demo_skill.py"
        target.write_text("def value():\n    return 1\n", encoding="utf-8")
        candidate = "def value():\n    return 2\n"

        dry_run = run_skill_improver(
            {
                "target_skill_path": str(target),
                "candidate_code": candidate,
                "test_command": ["python3", "-m", "py_compile", "{candidate_path}"],
                "context_packet": {
                    "selected_witness_indices": [4, 5, 6],
                    "directive_topics": ["skill_improver_gate"],
                    "context_notes": ["first-target-only"],
                },
                "bridge_packet": {
                    "slice_id": "a2-next-state-improver-context-bridge-audit-operator",
                },
            }
        )
        _assert(dry_run["improved"] is False, "dry-run should not commit")
        _assert(dry_run["proposed_change"] is True, "candidate should count as changed")
        _assert(dry_run["compile_ok"] is True, "candidate should compile")
        _assert(dry_run["tests_state"] == "passed", "selected test command should pass")
        _assert(dry_run["write_permitted"] is False, "dry-run should not permit write")
        _assert(
            dry_run["context_contract_status"] == "metadata_only_context_loaded",
            "context contract should load as metadata only",
        )
        _assert(
            dry_run["context_summary"]["selected_witness_indices"] == [4, 5, 6],
            "selected witness indices should be preserved",
        )
        _assert(
            dry_run["context_summary"]["directive_topics"] == ["skill_improver_gate"],
            "directive topics should be preserved",
        )
        _assert(dry_run["context_summary"]["metadata_only"] is True, "context should remain metadata only")
        _assert(target.read_text(encoding="utf-8").endswith("return 1\n"), "target should remain unchanged")

        committed = run_skill_improver(
            {
                "target_skill_path": str(target),
                "candidate_code": candidate,
                "test_command": ["python3", "-m", "py_compile", "{candidate_path}"],
                "allow_write": True,
                "approval_token": WRITE_APPROVAL_TOKEN,
                "allowed_targets": [str(target)],
            }
        )
        _assert(committed["improved"] is True, "approved run should commit")
        _assert(committed["write_permitted"] is True, "approved run should permit write")
        _assert(target.read_text(encoding="utf-8").endswith("return 2\n"), "target should be updated")

    print("PASS: skill improver operator smoke")


if __name__ == "__main__":
    main()
