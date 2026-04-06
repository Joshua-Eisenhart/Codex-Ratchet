"""
Focused tests for the wrapper's bounded multi-terminal live logic.

Tests exercise:
  Case 1 — 2-terminal plan: validation path accepts it (no plan errors)
  Case 2 — 3-terminal plan: validation path accepts it (no plan errors)
  Case 3 — 4-terminal plan: run_live fails closed (exit 1, all terminals marked error)
  Case 4 — 5-terminal plan: run_live fails closed (exit 1, all terminals marked error)

Real Claude launches are never attempted.  4+-terminal tests rely on the
LIVE_TERMINAL_LIMIT guard in run_live, which fires before any subprocess call.
2-3 terminal acceptance is tested via _validate_plan directly (no subprocess path).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from system_v4.skills.pi_mono_claude_batch_launcher import (  # noqa: E402
    LIVE_TERMINAL_LIMIT,
    _validate_plan,
    run_live,
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _make_terminal(n: int, tmp: Path) -> dict:
    return {
        "terminal_id": f"Claude-{n}",
        "handoff_file": f".agent/handoffs/active/task{n}.md",
        "launcher_text": f"Read .agent/handoffs/active/task{n}.md and execute it.",
        "expected_review_note": f".agent/reviews/active/task{n}__review.md",
    }


def _write_plan(tmp: Path, n_terminals: int) -> Path:
    plan = {
        "batch_id": f"test-live-{n_terminals}t",
        "created_at": "2026-04-04T00:00:00Z",
        "repo_root": str(tmp),
        "completion_rule": "review note present",
        "do_not_do": ["Do not invent prompt text."],
        "terminals": [_make_terminal(i, tmp) for i in range(1, n_terminals + 1)],
    }
    plan_path = tmp / f"plan_{n_terminals}t.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    return plan_path


def _read_live_status(tmp: Path, batch_id: str) -> dict:
    status_path = tmp / ".agent" / "state" / f"pi_mono_batch_status__{batch_id}.json"
    _assert(status_path.exists(), f"live status JSON not written: {status_path}")
    return json.loads(status_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Case 1 — 2-terminal plan accepted by validation path
# ---------------------------------------------------------------------------

def test_two_terminal_plan_passes_validation() -> None:
    """_validate_plan must return no errors for a well-formed 2-terminal plan."""
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        plan_path = _write_plan(tmp, 2)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        errors = _validate_plan(plan)
        _assert(errors == [], f"expected no validation errors for 2-terminal plan, got: {errors}")
        # Also confirm terminal count is within LIVE_TERMINAL_LIMIT
        _assert(len(plan["terminals"]) <= LIVE_TERMINAL_LIMIT,
                f"2-terminal plan should be within limit ({LIVE_TERMINAL_LIMIT})")


# ---------------------------------------------------------------------------
# Case 2 — 3-terminal plan accepted by validation path
# ---------------------------------------------------------------------------

def test_three_terminal_plan_passes_validation() -> None:
    """_validate_plan must return no errors for a well-formed 3-terminal plan."""
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        plan_path = _write_plan(tmp, 3)
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        errors = _validate_plan(plan)
        _assert(errors == [], f"expected no validation errors for 3-terminal plan, got: {errors}")
        _assert(len(plan["terminals"]) <= LIVE_TERMINAL_LIMIT,
                f"3-terminal plan should be within limit ({LIVE_TERMINAL_LIMIT})")


# ---------------------------------------------------------------------------
# Case 3 — 4-terminal plan fails closed in run_live
# ---------------------------------------------------------------------------

def test_four_terminal_plan_fails_closed() -> None:
    """run_live must exit 1 and mark all terminals error when plan has 4 terminals."""
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        plan_path = _write_plan(tmp, 4)
        rc = run_live(str(plan_path))
        _assert(rc == 1, f"expected exit 1 for 4-terminal plan, got {rc}")

        status = _read_live_status(tmp, "test-live-4t")
        _assert(status["dry_run"] is False, "live mode should set dry_run=False")
        _assert(len(status["terminals"]) == 4,
                f"expected 4 terminal entries in status, got {len(status['terminals'])}")
        for t in status["terminals"]:
            _assert(t["status"] == "error",
                    f"expected status=error for terminal {t.get('terminal_id')}, got {t['status']}")


# ---------------------------------------------------------------------------
# Case 4 — 5-terminal plan also fails closed in run_live
# ---------------------------------------------------------------------------

def test_five_terminal_plan_fails_closed() -> None:
    """run_live must exit 1 and mark all terminals error when plan has 5 terminals."""
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        plan_path = _write_plan(tmp, 5)
        rc = run_live(str(plan_path))
        _assert(rc == 1, f"expected exit 1 for 5-terminal plan, got {rc}")

        status = _read_live_status(tmp, "test-live-5t")
        _assert(len(status["terminals"]) == 5,
                f"expected 5 terminal entries in status, got {len(status['terminals'])}")
        for t in status["terminals"]:
            _assert(t["status"] == "error",
                    f"expected status=error for terminal {t.get('terminal_id')}, got {t['status']}")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    test_two_terminal_plan_passes_validation()
    test_three_terminal_plan_passes_validation()
    test_four_terminal_plan_fails_closed()
    test_five_terminal_plan_fails_closed()
    print("PASS: pimono multiterminal live logic")


if __name__ == "__main__":
    main()
