"""
Smoke test for the Pi-Mono dry-run validator (pi_mono_claude_batch_launcher.py).

Exercises four status paths without launching any terminal or process:
  Case 1 — handoff_missing:      handoff file absent  → has_handoff_missing
  Case 2 — not_started:          handoff present, review absent → ready_to_launch
  Case 3 — already_complete:     handoff + review present → all_already_complete
  Case 4 — plan_error:           duplicate terminal_id → has_plan_errors
  Case 5 — plan_invalid:         missing required field → plan_invalid
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.pi_mono_claude_batch_launcher import run  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_plan(tmp: Path, terminals: list[dict], extra: dict | None = None) -> Path:
    """Write a minimal valid launch plan into tmp and return its path."""
    plan = {
        "batch_id": "test-batch-001",
        "created_at": "2026-04-04T00:00:00Z",
        "repo_root": str(tmp),
        "completion_rule": "review note present",
        "do_not_do": ["Do not invent prompt text."],
        "terminals": terminals,
    }
    if extra:
        plan.update(extra)
    plan_path = tmp / "test_plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    return plan_path


def _read_status(tmp: Path) -> dict:
    status_path = tmp / ".agent" / "state" / "pi_mono_batch_status__current.json"
    _assert(status_path.exists(), f"status JSON not written: {status_path}")
    return json.loads(status_path.read_text(encoding="utf-8"))


def _status_md_exists(tmp: Path) -> bool:
    return (tmp / ".agent" / "state" / "pi_mono_batch_status__current.md").exists()


# ---------------------------------------------------------------------------
# Case 1 — handoff file absent → handoff_missing / has_handoff_missing
# ---------------------------------------------------------------------------

def test_handoff_missing() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        terminals = [{
            "terminal_id": "Claude-A",
            "handoff_file": ".agent/handoffs/active/nonexistent.md",
            "launcher_text": "Read .agent/handoffs/active/nonexistent.md and execute it.",
            "expected_review_note": ".agent/reviews/active/nonexistent__review.md",
        }]
        plan_path = _write_plan(tmp, terminals)
        rc = run(str(plan_path))
        _assert(rc == 0, f"expected exit 0, got {rc}")

        status = _read_status(tmp)
        _assert(status["dry_run"] is True, "dry_run flag missing")
        _assert(status["overall_status"] == "has_handoff_missing",
                f"expected has_handoff_missing, got {status['overall_status']}")
        _assert(len(status["terminals"]) == 1, "expected 1 terminal result")
        t = status["terminals"][0]
        _assert(t["status"] == "handoff_missing", f"expected handoff_missing, got {t['status']}")
        _assert(t["handoff_file_exists"] is False, "handoff_file_exists should be False")
        _assert(t["review_note_present"] is False, "review_note_present should be False")
        _assert(_status_md_exists(tmp), "markdown not written")


# ---------------------------------------------------------------------------
# Case 2 — handoff present, review absent → not_started / ready_to_launch
# ---------------------------------------------------------------------------

def test_not_started() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        handoff_path = tmp / ".agent" / "handoffs" / "active" / "task.md"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text("# Handoff", encoding="utf-8")

        terminals = [{
            "terminal_id": "Claude-B",
            "handoff_file": ".agent/handoffs/active/task.md",
            "launcher_text": "Read .agent/handoffs/active/task.md and execute it.",
            "expected_review_note": ".agent/reviews/active/task__review.md",
        }]
        plan_path = _write_plan(tmp, terminals)
        rc = run(str(plan_path))
        _assert(rc == 0, f"expected exit 0, got {rc}")

        status = _read_status(tmp)
        _assert(status["overall_status"] == "ready_to_launch",
                f"expected ready_to_launch, got {status['overall_status']}")
        t = status["terminals"][0]
        _assert(t["status"] == "not_started", f"expected not_started, got {t['status']}")
        _assert(t["handoff_file_exists"] is True, "handoff_file_exists should be True")
        _assert(t["review_note_present"] is False, "review_note_present should be False")


# ---------------------------------------------------------------------------
# Case 3 — handoff + review present → already_complete / all_already_complete
# ---------------------------------------------------------------------------

def test_already_complete() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        handoff_path = tmp / ".agent" / "handoffs" / "active" / "done.md"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text("# Handoff", encoding="utf-8")
        review_path = tmp / ".agent" / "reviews" / "active" / "done__review.md"
        review_path.parent.mkdir(parents=True, exist_ok=True)
        review_path.write_text("# Review", encoding="utf-8")

        terminals = [{
            "terminal_id": "Claude-C",
            "handoff_file": ".agent/handoffs/active/done.md",
            "launcher_text": "Read .agent/handoffs/active/done.md and execute it.",
            "expected_review_note": ".agent/reviews/active/done__review.md",
        }]
        plan_path = _write_plan(tmp, terminals)
        rc = run(str(plan_path))
        _assert(rc == 0, f"expected exit 0, got {rc}")

        status = _read_status(tmp)
        _assert(status["overall_status"] == "all_already_complete",
                f"expected all_already_complete, got {status['overall_status']}")
        t = status["terminals"][0]
        _assert(t["status"] == "already_complete", f"expected already_complete, got {t['status']}")
        _assert(t["handoff_file_exists"] is True, "handoff_file_exists should be True")
        _assert(t["review_note_present"] is True, "review_note_present should be True")


# ---------------------------------------------------------------------------
# Case 4 — duplicate terminal_id → plan_error / has_plan_errors
# ---------------------------------------------------------------------------

def test_duplicate_terminal_id() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        handoff_path = tmp / ".agent" / "handoffs" / "active" / "x.md"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text("# Handoff", encoding="utf-8")

        terminals = [
            {
                "terminal_id": "Claude-D",
                "handoff_file": ".agent/handoffs/active/x.md",
                "launcher_text": "Read .agent/handoffs/active/x.md and execute it.",
                "expected_review_note": ".agent/reviews/active/x__review.md",
            },
            {
                "terminal_id": "Claude-D",  # duplicate
                "handoff_file": ".agent/handoffs/active/x.md",
                "launcher_text": "Read .agent/handoffs/active/x.md and execute it.",
                "expected_review_note": ".agent/reviews/active/x__review.md",
            },
        ]
        plan_path = _write_plan(tmp, terminals)
        rc = run(str(plan_path))
        _assert(rc == 0, f"expected exit 0, got {rc}")

        status = _read_status(tmp)
        _assert(status["overall_status"] == "has_plan_errors",
                f"expected has_plan_errors, got {status['overall_status']}")
        statuses = [t["status"] for t in status["terminals"]]
        _assert("plan_error" in statuses, f"expected plan_error in statuses: {statuses}")


# ---------------------------------------------------------------------------
# Case 5 — missing required plan field → plan_invalid
# ---------------------------------------------------------------------------

def test_plan_invalid_missing_field() -> None:
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        # Omit completion_rule
        plan = {
            "batch_id": "bad-plan",
            "created_at": "2026-04-04T00:00:00Z",
            "repo_root": str(tmp),
            "do_not_do": ["Do not invent."],
            "terminals": [{
                "terminal_id": "Claude-E",
                "handoff_file": ".agent/handoffs/active/e.md",
                "launcher_text": "Read it.",
                "expected_review_note": ".agent/reviews/active/e__review.md",
            }],
            # completion_rule intentionally absent
        }
        plan_path = tmp / "bad_plan.json"
        plan_path.write_text(json.dumps(plan), encoding="utf-8")

        rc = run(str(plan_path))
        _assert(rc == 0, f"expected exit 0, got {rc}")

        status = _read_status(tmp)
        _assert(status["overall_status"] == "plan_invalid",
                f"expected plan_invalid, got {status['overall_status']}")
        _assert(len(status["plan_errors"]) > 0, "expected non-empty plan_errors")
        _assert(status["terminals"] == [], "expected empty terminals on plan_invalid")


# ---------------------------------------------------------------------------
# Additional: status JSON is schema-compatible with template
# ---------------------------------------------------------------------------

def test_status_schema_superset_of_template() -> None:
    """Verify output JSON has all fields from pi_mono_batch_status__template.json."""
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        handoff_path = tmp / ".agent" / "handoffs" / "active" / "schema_test.md"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text("# Handoff", encoding="utf-8")

        terminals = [{
            "terminal_id": "Claude-F",
            "handoff_file": ".agent/handoffs/active/schema_test.md",
            "launcher_text": "Read and execute.",
            "expected_review_note": ".agent/reviews/active/schema_test__review.md",
        }]
        plan_path = _write_plan(tmp, terminals)
        run(str(plan_path))

        status = _read_status(tmp)
        # Required top-level fields (from template)
        for field in ("batch_id", "checked_at", "overall_status", "terminals"):
            _assert(field in status, f"missing template field: {field}")
        # Extra dry-run fields
        _assert("dry_run" in status, "missing dry_run field")
        _assert("plan_errors" in status, "missing plan_errors field")
        # Per-terminal fields
        t = status["terminals"][0]
        for field in ("terminal_id", "handoff_file", "expected_review_note",
                      "review_note_present", "notes"):
            _assert(field in t, f"missing template terminal field: {field}")
        # Extra per-terminal fields
        _assert("handoff_file_exists" in t, "missing handoff_file_exists field")
        _assert("status" in t, "missing per-terminal status field")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    test_handoff_missing()
    test_not_started()
    test_already_complete()
    test_duplicate_terminal_id()
    test_plan_invalid_missing_field()
    test_status_schema_superset_of_template()
    print("PASS: pimono dry-run validator smoke")


if __name__ == "__main__":
    main()
