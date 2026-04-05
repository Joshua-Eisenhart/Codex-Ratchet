"""
Roundtrip smoke test for pi_mono_run.py.

Exercises status-file writing and evidence-based completion logic using
a fake repo root.  No real Claude subprocesses are launched.

  Case 1 — _write_status: all_complete when every terminal is "complete"
  Case 2 — _write_status: has_errors when any terminal is "error"
  Case 3 — _write_status: has_timeouts when any terminal is "timeout"
  Case 4 — _write_status: launched when any terminal is "launched" (no error/timeout)
  Case 5 — _write_status: not_started when all terminals are "not_started"
  Case 6 — _evidence_complete: True when review + required outputs exist
  Case 7 — _evidence_complete: False when review missing
  Case 8 — _evidence_complete: False when required output missing
  Case 9 — roundtrip: status JSON on disk is valid and re-readable
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import system_v4.skills.pi_mono_run as runner  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _patch_paths(tmp: Path):
    """Temporarily redirect module-level paths to a temp directory."""
    saved = (runner.REPO_ROOT, runner.STATE_DIR, runner.LIVE_NOTE_PATH)
    runner.REPO_ROOT = tmp
    runner.STATE_DIR = tmp / ".agent" / "state"
    runner.LIVE_NOTE_PATH = tmp / ".agent" / "state" / "PI_MONO_LIVE_STATUS_NOTE__CURRENT.md"
    return saved


def _restore_paths(saved):
    runner.REPO_ROOT, runner.STATE_DIR, runner.LIVE_NOTE_PATH = saved


def _make_terminals(statuses: list[str]) -> list[dict]:
    return [
        {
            "terminal_id": f"Claude-{i}",
            "status": s,
            "handoff_file": f".agent/handoffs/active/task{i}.md",
            "expected_review_note": f".agent/reviews/active/task{i}__review.md",
            "review_note_present": False,
            "required_outputs_present": False,
            "notes": "",
        }
        for i, s in enumerate(statuses, 1)
    ]


# ---------------------------------------------------------------------------
# Case 1 — all_complete
# ---------------------------------------------------------------------------

def test_write_status_all_complete() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            terminals = _make_terminals(["complete", "complete"])
            out = runner._write_status("smoke-01", terminals)
            data = json.loads(out.read_text())
            _assert(data["overall_status"] == "all_complete",
                    f"expected all_complete, got {data['overall_status']}")
            _assert(data["batch_id"] == "smoke-01", "batch_id mismatch")
            _assert(len(data["terminals"]) == 2, "terminal count mismatch")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 2 — has_errors
# ---------------------------------------------------------------------------

def test_write_status_has_errors() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            terminals = _make_terminals(["complete", "error"])
            out = runner._write_status("smoke-02", terminals)
            data = json.loads(out.read_text())
            _assert(data["overall_status"] == "has_errors",
                    f"expected has_errors, got {data['overall_status']}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 3 — has_timeouts
# ---------------------------------------------------------------------------

def test_write_status_has_timeouts() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            terminals = _make_terminals(["complete", "timeout"])
            out = runner._write_status("smoke-03", terminals)
            data = json.loads(out.read_text())
            _assert(data["overall_status"] == "has_timeouts",
                    f"expected has_timeouts, got {data['overall_status']}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 4 — launched
# ---------------------------------------------------------------------------

def test_write_status_launched() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            terminals = _make_terminals(["launched", "not_started"])
            out = runner._write_status("smoke-04", terminals)
            data = json.loads(out.read_text())
            _assert(data["overall_status"] == "launched",
                    f"expected launched, got {data['overall_status']}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 5 — not_started
# ---------------------------------------------------------------------------

def test_write_status_not_started() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            terminals = _make_terminals(["not_started", "not_started"])
            out = runner._write_status("smoke-05", terminals)
            data = json.loads(out.read_text())
            _assert(data["overall_status"] == "not_started",
                    f"expected not_started, got {data['overall_status']}")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 6 — _evidence_complete: True
# ---------------------------------------------------------------------------

def test_evidence_complete_true() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            review = tmp / ".agent" / "reviews" / "active" / "task1__review.md"
            review.parent.mkdir(parents=True, exist_ok=True)
            review.write_text("# Review")

            output = tmp / "system_v4" / "tests" / "artifact.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text("{}")

            task = {
                "expected_review_note": ".agent/reviews/active/task1__review.md",
                "required_output_files": ["system_v4/tests/artifact.json"],
            }
            _assert(runner._evidence_complete(task) is True,
                    "expected evidence_complete=True when all files exist")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 7 — _evidence_complete: False (review missing)
# ---------------------------------------------------------------------------

def test_evidence_complete_review_missing() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            task = {
                "expected_review_note": ".agent/reviews/active/missing__review.md",
                "required_output_files": [],
            }
            _assert(runner._evidence_complete(task) is False,
                    "expected evidence_complete=False when review missing")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 8 — _evidence_complete: False (required output missing)
# ---------------------------------------------------------------------------

def test_evidence_complete_output_missing() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            review = tmp / ".agent" / "reviews" / "active" / "task2__review.md"
            review.parent.mkdir(parents=True, exist_ok=True)
            review.write_text("# Review")

            task = {
                "expected_review_note": ".agent/reviews/active/task2__review.md",
                "required_output_files": ["nonexistent/file.json"],
            }
            _assert(runner._evidence_complete(task) is False,
                    "expected evidence_complete=False when required output missing")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Case 9 — roundtrip: write then read status JSON
# ---------------------------------------------------------------------------

def test_status_roundtrip_readable() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        saved = _patch_paths(tmp)
        try:
            terminals = _make_terminals(["complete", "error", "timeout"])
            out = runner._write_status("smoke-09", terminals)

            _assert(out.is_file(), "status file not created")
            data = json.loads(out.read_text())

            # Verify structure
            for key in ("batch_id", "updated_at", "overall_status", "terminals"):
                _assert(key in data, f"missing key: {key}")

            _assert(len(data["terminals"]) == 3, "terminal count mismatch")

            # Verify live note was also written
            live_note = tmp / ".agent" / "state" / "PI_MONO_LIVE_STATUS_NOTE__CURRENT.md"
            _assert(live_note.is_file(), "live note not written")
            content = live_note.read_text()
            _assert("smoke-09" in content, "batch_id not in live note")
        finally:
            _restore_paths(saved)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    test_write_status_all_complete()
    test_write_status_has_errors()
    test_write_status_has_timeouts()
    test_write_status_launched()
    test_write_status_not_started()
    test_evidence_complete_true()
    test_evidence_complete_review_missing()
    test_evidence_complete_output_missing()
    test_status_roundtrip_readable()
    print("PASS: pimono runner roundtrip smoke (9/9)")


if __name__ == "__main__":
    main()
