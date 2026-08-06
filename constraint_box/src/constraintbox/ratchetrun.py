"""Run one ratchet tick and emit controller-owned execution evidence.

Exit codes:

* 0 -- the tick exited zero.
* 1 -- the tick exited non-zero.
* 2 -- runner usage or I/O failure.
* 3 -- the tick timed out.

The receipt records the tick's bytes and result-artifact changes.  It does not
adopt the tick's verdict or let the tick choose its own claim kind.
"""

from __future__ import annotations

import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .simrun import (
    CLAIM_KIND_SOURCE,
    SimRunError,
    Snapshot,
    _as_bytes,
    _claim_kind_conflicts,
    _claim_kind_for,
    _diff_snapshots,
    _display_path,
    _probe_interpreter_environment,
    _quarantined_claim_kind,
    _resolve_interpreter,
    _sha256_file,
    _snapshot,
    _stream_fields,
    render_receipt,
    write_receipt_atomic,
)


DEFAULT_TIMEOUT_SECONDS = 900.0
REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TICK_PATH = REPO_ROOT / "ratchet_contract" / "run_ratchet_tick.py"

_MAIN_SUPPLEMENTAL_REASON = (
    "main() calls attach_supplemental_gate_verdicts for tick0, tick1 and junk_run"
)
_MAIN_V2_SUPPLEMENTAL_REASON = (
    "main_v2() never calls attach_supplemental_gate_verdicts; the four "
    "supplemental gates do not run under --v2"
)
_PINNED_DETERMINISM_NOTE = (
    "PYTHONHASHSEED=0 was pinned in the child environment. Byte-stability of "
    "the tick's result JSONs across runs is NOT established by this receipt: "
    "a single run cannot establish it, and unpinned reruns were previously "
    "observed to differ in partition digests and label ordering."
)
_UNPINNED_DETERMINISM_NOTE = (
    "PYTHONHASHSEED was not pinned. The tick's result JSON digests are NOT "
    "stable across runs; unpinned reruns were observed to differ in partition "
    "digests and label ordering."
)


class RatchetRunError(RuntimeError):
    """Runner usage or I/O failure."""


def _empty_snapshot() -> Snapshot:
    return Snapshot(files={}, skipped_large=(), truncated=False)


def _snapshot_results(directory: Path) -> Snapshot:
    if not directory.exists():
        return _empty_snapshot()
    if not directory.is_dir():
        raise RatchetRunError(f"results path is not a directory: {directory}")
    try:
        return _snapshot(directory)
    except SimRunError as exc:
        raise RatchetRunError(str(exc)) from exc


def run_ratchet_tick(
    *,
    tick_path: Path = DEFAULT_TICK_PATH,
    results_dir: Path | None = None,
    v2: bool = False,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    interpreter: Path | str | None = None,
    pin_hashseed: bool = True,
) -> tuple[dict[str, Any], int]:
    """Run one ratchet tick and return its receipt and runner exit code."""

    try:
        timeout_seconds = float(timeout_seconds)
    except (TypeError, ValueError) as exc:
        raise RatchetRunError("timeout must be a number") from exc
    if timeout_seconds <= 0:
        raise RatchetRunError("timeout must be greater than zero")

    tick_path = Path(tick_path).expanduser().resolve()
    if not tick_path.is_file():
        raise RatchetRunError(f"missing tick path: {tick_path}")

    if results_dir is None:
        results_dir = tick_path.parent / "results"
    results_dir = Path(results_dir).expanduser().resolve()

    try:
        tick_sha256 = _sha256_file(tick_path)
        (
            actual_interpreter,
            interpreter_requested,
            interpreter_realpath,
            interpreter_sha256,
        ) = _resolve_interpreter(interpreter)
    except SimRunError as exc:
        raise RatchetRunError(str(exc)) from exc

    command = [actual_interpreter, str(tick_path)]
    if v2:
        command.append("--v2")
    interpreter_environment = _probe_interpreter_environment(
        actual_interpreter,
        cwd=tick_path.parent,
    )

    before = _snapshot_results(results_dir)
    child_environment = None
    if pin_hashseed:
        child_environment = os.environ.copy()
        child_environment["PYTHONHASHSEED"] = "0"

    started_at_utc = datetime.now(timezone.utc).isoformat()
    started = time.monotonic()
    timed_out = False
    exit_code: int | None
    try:
        completed = subprocess.run(
            command,
            cwd=tick_path.parent,
            capture_output=True,
            timeout=timeout_seconds,
            env=child_environment,
        )
        exit_code = completed.returncode
        stdout = _as_bytes(completed.stdout)
        stderr = _as_bytes(completed.stderr)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = _as_bytes(exc.stdout)
        stderr = _as_bytes(exc.stderr)
    except OSError as exc:
        raise RatchetRunError(f"could not execute ratchet tick: {exc}") from exc
    wall_seconds = time.monotonic() - started
    after = _snapshot_results(results_dir)

    try:
        artifacts, created_paths = _diff_snapshots(before, after, REPO_ROOT)
    except SimRunError as exc:
        raise RatchetRunError(str(exc)) from exc
    claim_kind, claim_kind_rule = _claim_kind_for(tick_path, REPO_ROOT)
    sim_asserted_claim_kind = _quarantined_claim_kind(stdout, created_paths)
    entry_path = "main_v2" if v2 else "main"
    supplemental_gates_reachable = not v2

    receipt: dict[str, Any] = {
        "schema": "constraintbox.ratchetrun.v1",
        "tick_path": _display_path(tick_path, REPO_ROOT),
        "tick_sha256": tick_sha256,
        "entry_path": entry_path,
        "v2": bool(v2),
        "supplemental_gates_reachable": supplemental_gates_reachable,
        "supplemental_gates_reachable_reason": (
            _MAIN_SUPPLEMENTAL_REASON
            if supplemental_gates_reachable
            else _MAIN_V2_SUPPLEMENTAL_REASON
        ),
        "results_dir": _display_path(results_dir, REPO_ROOT),
        "command": command,
        "interpreter": actual_interpreter,
        "interpreter_requested": interpreter_requested,
        "interpreter_realpath": interpreter_realpath,
        "interpreter_sha256": interpreter_sha256,
        **interpreter_environment,
        "cwd": str(tick_path.parent),
        "timeout_seconds": timeout_seconds,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "wall_seconds": wall_seconds,
        "started_at_utc": started_at_utc,
        **_stream_fields("stdout", stdout),
        **_stream_fields("stderr", stderr),
        "artifacts": artifacts,
        "determinism": {
            "pythonhashseed_pinned": bool(pin_hashseed),
            "pythonhashseed_value": "0" if pin_hashseed else None,
            "artifact_digests_stable_across_runs": None,
            "note": (
                _PINNED_DETERMINISM_NOTE
                if pin_hashseed
                else _UNPINNED_DETERMINISM_NOTE
            ),
        },
        "claim_kind": claim_kind,
        "claim_kind_source": CLAIM_KIND_SOURCE,
        "claim_kind_rule": claim_kind_rule,
        "sim_asserted_claim_kind": sim_asserted_claim_kind,
        "claim_kind_conflict": _claim_kind_conflicts(
            sim_asserted_claim_kind,
            claim_kind,
        ),
        "produced_by": "constraintbox.ratchetrun",
        "promotion_allowed": False,
    }

    if timed_out:
        runner_exit_code = 3
    elif exit_code == 0:
        runner_exit_code = 0
    else:
        runner_exit_code = 1
    return receipt, runner_exit_code
