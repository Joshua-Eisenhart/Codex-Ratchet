"""
Fail-closed edge-case tests for pi_mono_run.py.

Exercises launch/validation paths that must fail safely without
launching any real scientific subprocesses.

  Case 1 — main() returns 1 when plan file does not exist
  Case 2 — main() returns 1 when plan JSON is malformed
  Case 3 — main() returns 1 when plan has zero terminals
  Case 4 — main() returns 1 when claude CLI is not found
  Case 5 — _run_task marks error when handoff file is missing
  Case 6 — _run_task skips (complete) when evidence already present
  Case 7 — main() returns 1 when batch has mixed errors (overall != all_complete)
"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import system_v4.skills.pi_mono_run as runner  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _patch_paths(tmp: Path):
    """Temporarily redirect module-level paths to a temp directory."""
    saved = (
        runner.REPO_ROOT, runner.STATE_DIR,
        runner.LIVE_NOTE_PATH, runner.CURRENT_STATUS_JSON, runner.CURRENT_STATUS_MD,
    )
    runner.REPO_ROOT = tmp
    runner.STATE_DIR = tmp / ".agent" / "state"
    runner.LIVE_NOTE_PATH = tmp / ".agent" / "state" / "PI_MONO_LIVE_STATUS_NOTE__CURRENT.md"
    runner.CURRENT_STATUS_JSON = tmp / ".agent" / "state" / "pi_mono_batch_status__current.json"
    runner.CURRENT_STATUS_MD = tmp / ".agent" / "state" / "pi_mono_batch_status__current.md"
    return saved


def _restore_paths(saved):
    (runner.REPO_ROOT, runner.STATE_DIR,
     runner.LIVE_NOTE_PATH, runner.CURRENT_STATUS_JSON, runner.CURRENT_STATUS_MD) = saved


# ---------------------------------------------------------------------------
# Case 1 — plan file does not exist → main() returns 1
# ---------------------------------------------------------------------------

def test_plan_not_found() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        fake_plan = tmp / "nonexistent_plan.json"
        with mock.patch("sys.argv", ["pi_mono_run.py", "--plan", str(fake_plan), "--no-view"]):
            rc = runner.main()
        _assert(rc == 1, f"expected exit 1 for missing plan, got {rc}")


# ---------------------------------------------------------------------------
# Case 2 — plan file contains invalid JSON → main() returns 1
# ---------------------------------------------------------------------------

def test_plan_malformed_json() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        bad_plan = tmp / "bad_plan.json"
        bad_plan.write_text("{not valid json!!!")
        with mock.patch("sys.argv", ["pi_mono_run.py", "--plan", str(bad_plan), "--no-view"]):
            rc = runner.main()
        _assert(rc == 1, f"expected exit 1 for malformed JSON, got {rc}")


# ---------------------------------------------------------------------------
# Case 3 — plan has zero terminals → main() returns 1
# ---------------------------------------------------------------------------

def test_plan_empty_terminals() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            plan = {"batch_id": "empty-test", "terminals": []}
            plan_path = tmp / "empty_plan.json"
            plan_path.write_text(json.dumps(plan))
            with mock.patch("sys.argv", ["pi_mono_run.py", "--plan", str(plan_path), "--no-view"]):
                rc = runner.main()
            _assert(rc == 1, f"expected exit 1 for empty terminals, got {rc}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 4 — claude CLI not found → main() returns 1
# ---------------------------------------------------------------------------

def test_claude_not_found() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            plan = {
                "batch_id": "no-claude-test",
                "terminals": [{
                    "terminal_id": "Claude-X",
                    "handoff_file": ".agent/handoffs/active/x.md",
                    "launcher_text": "test",
                    "expected_review_note": ".agent/reviews/active/x__review.md",
                }],
            }
            # Create handoff so we get past the terminals check
            handoff = tmp / ".agent" / "handoffs" / "active" / "x.md"
            handoff.parent.mkdir(parents=True, exist_ok=True)
            handoff.write_text("# handoff")

            plan_path = tmp / "plan.json"
            plan_path.write_text(json.dumps(plan))

            with mock.patch("sys.argv", ["pi_mono_run.py", "--plan", str(plan_path), "--no-view"]):
                with mock.patch.object(runner, "_find_claude", return_value=None):
                    rc = runner.main()
            _assert(rc == 1, f"expected exit 1 when claude not found, got {rc}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 5 — _run_task marks error when handoff file is missing
# ---------------------------------------------------------------------------

def test_run_task_missing_handoff() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            (tmp / ".agent" / "state").mkdir(parents=True, exist_ok=True)

            task = {
                "terminal_id": "Claude-MH",
                "handoff_file": ".agent/handoffs/active/missing.md",
                "launcher_text": "test",
                "expected_review_note": ".agent/reviews/active/missing__review.md",
                "required_output_files": [],
            }
            lock = threading.Lock()
            terminals = [{
                "terminal_id": "Claude-MH",
                "status": "not_started",
                "handoff_file": task["handoff_file"],
                "expected_review_note": task["expected_review_note"],
                "review_note_present": False,
                "required_outputs_present": False,
                "notes": "",
            }]

            runner._run_task(task, "/usr/bin/false", 10, terminals, lock, "fc-test-05")

            t = terminals[0]
            _assert(t["status"] == "error",
                    f"expected status=error for missing handoff, got {t['status']}")
            _assert("handoff not found" in t["notes"],
                    f"expected 'handoff not found' in notes, got: {t['notes']}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 6 — _run_task skips when evidence already present
# ---------------------------------------------------------------------------

def test_run_task_already_complete() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            (tmp / ".agent" / "state").mkdir(parents=True, exist_ok=True)

            # Create evidence files
            review = tmp / ".agent" / "reviews" / "active" / "done__review.md"
            review.parent.mkdir(parents=True, exist_ok=True)
            review.write_text("# Review present")

            output = tmp / "system_v4" / "output.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("{}")

            task = {
                "terminal_id": "Claude-AC",
                "handoff_file": ".agent/handoffs/active/done.md",
                "launcher_text": "test",
                "expected_review_note": ".agent/reviews/active/done__review.md",
                "required_output_files": ["system_v4/output.json"],
            }
            lock = threading.Lock()
            terminals = [{
                "terminal_id": "Claude-AC",
                "status": "not_started",
                "handoff_file": task["handoff_file"],
                "expected_review_note": task["expected_review_note"],
                "review_note_present": False,
                "required_outputs_present": False,
                "notes": "",
            }]

            # Should skip without launching — no real claude binary needed
            runner._run_task(task, "/nonexistent/claude", 10, terminals, lock, "fc-test-06")

            t = terminals[0]
            _assert(t["status"] == "complete",
                    f"expected status=complete for pre-existing evidence, got {t['status']}")
            _assert("before launch" in t["notes"],
                    f"expected 'before launch' in notes, got: {t['notes']}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 7 — main() returns 1 when batch has mixed errors
# ---------------------------------------------------------------------------

def test_main_returns_nonzero_on_partial_failure() -> None:
    """Confirm main() exit code is 1 when not all tasks succeed."""
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            (tmp / ".agent" / "state").mkdir(parents=True, exist_ok=True)

            # Task 1: handoff missing → will error
            # Task 2: evidence present → will complete
            review = tmp / ".agent" / "reviews" / "active" / "ok__review.md"
            review.parent.mkdir(parents=True, exist_ok=True)
            review.write_text("# ok")

            plan = {
                "batch_id": "mixed-test",
                "terminals": [
                    {
                        "terminal_id": "Claude-Fail",
                        "handoff_file": ".agent/handoffs/active/missing.md",
                        "launcher_text": "test",
                        "expected_review_note": ".agent/reviews/active/missing__review.md",
                    },
                    {
                        "terminal_id": "Claude-Ok",
                        "handoff_file": ".agent/handoffs/active/ok.md",
                        "launcher_text": "test",
                        "expected_review_note": ".agent/reviews/active/ok__review.md",
                    },
                ],
            }
            plan_path = tmp / "mixed_plan.json"
            plan_path.write_text(json.dumps(plan))

            # Provide a fake claude binary that won't actually be called
            # (task 1 errors on missing handoff, task 2 completes on evidence)
            with mock.patch("sys.argv", ["pi_mono_run.py", "--plan", str(plan_path), "--no-view"]):
                with mock.patch.object(runner, "_find_claude", return_value="/usr/bin/false"):
                    rc = runner.main()

            _assert(rc == 1, f"expected exit 1 for partial failure, got {rc}")

            # Verify status file reflects the mixed state
            status_file = tmp / ".agent" / "state" / "pi_mono_batch_status__mixed-test.json"
            _assert(status_file.is_file(), "batch status file not written")
            data = json.loads(status_file.read_text())
            _assert(data["overall_status"] == "has_errors",
                    f"expected has_errors, got {data['overall_status']}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    test_plan_not_found()
    test_plan_malformed_json()
    test_plan_empty_terminals()
    test_claude_not_found()
    test_run_task_missing_handoff()
    test_run_task_already_complete()
    test_main_returns_nonzero_on_partial_failure()
    print("PASS: pimono fail-closed edge cases (7/7)")


if __name__ == "__main__":
    main()
