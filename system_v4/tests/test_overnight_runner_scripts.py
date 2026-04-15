from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_RUNNER = REPO_ROOT / "system_v5" / "docs" / "plans" / "overnight_8h_run.sh"
LIVE_RUNNER = REPO_ROOT / "system_v5" / "new docs" / "plans" / "run_overnight_8h_controller.sh"


def test_canonical_overnight_runner_calls_cleanup_guard():
    text = CANONICAL_RUNNER.read_text(encoding="utf-8")
    assert "cleanup_first_guard.py" in text



def test_canonical_runner_contains_telegram_status_helper():
    text = CANONICAL_RUNNER.read_text(encoding="utf-8")
    assert "send_telegram_status" in text
    assert "load_hermes_telegram_env" in text
    assert "/Users/joshuaeisenhart/.hermes/.env" in text



def test_canonical_runner_rate_limits_telegram_heartbeats_to_five_minutes():
    text = CANONICAL_RUNNER.read_text(encoding="utf-8")
    assert 'TELEGRAM_MIN_INTERVAL=300' in text
    # Cadence is now enforced by the decoupled reporter loop, not a per-call gate.
    assert 'reporter_loop' in text
    assert 'last_periodic' in text



def test_canonical_runner_uses_live_queue_controller_for_remaining_budget():
    text = CANONICAL_RUNNER.read_text(encoding="utf-8")
    assert 'LIVE_QUEUE_CONTROLLER="$ROOT/system_v4/probes/live_queue_controller.py"' in text
    assert 'run_live_queue_for_remaining_budget' in text
    assert 'sleep_heartbeat_loop 30' not in text



def test_canonical_runner_declares_success_criteria_and_closeout_check():
    text = CANONICAL_RUNNER.read_text(encoding="utf-8")
    assert '/tmp/overnight_8h_run.lock' in text
    assert 'RUN_HEADER=' in text
    assert 'write_run_header' in text
    assert 'evaluate_success_criteria' in text
    assert 'live_queue_batches_min' in text
    assert 'new_result_jsons_min' in text
    assert 'canonical_by_process_count_delta' in text
    assert 'FAILURE' in text



def test_canonical_runner_uses_decoupled_reporter_process():
    text = CANONICAL_RUNNER.read_text(encoding="utf-8")
    assert 'start_reporter' in text
    assert 'queue_report_event' in text
    heartbeat_block = text.split('heartbeat() {', 1)[1].split('run_task() {', 1)[0]
    assert 'send_telegram_status' not in heartbeat_block



def test_live_runner_delegates_to_canonical_runner():
    text = LIVE_RUNNER.read_text(encoding="utf-8")
    assert "system_v5/docs/plans/overnight_8h_run.sh" in text
