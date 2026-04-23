#!/usr/bin/env python3
"""
pi_mono_claude_batch_launcher.py

Ratchet-side Pi-Mono Claude batch launcher.

Modes
-----
dry-run  (default / original)
    Reads a Hermes-authored launch plan, validates it, checks filesystem
    state, and writes status files.  Does NOT launch Claude or spawn any
    process.

live  (added: up to three terminals)
    Validates the plan, fails closed if >3 terminals, then launches up to
    three Claude Code subprocesses via `claude -p "<launcher_text>"`, one at
    a time in order.  Polls for repo evidence (review note + required output
    files) after each launch and writes status after every terminal update.

Rules  (PI_MONO_BATCH_AUTOMATION_CONTRACT__CURRENT.md)
------------------------------------------------------
- One handoff per terminal; no stacked prompts.
- launcher_text is sent as-is; never modified here.
- Completion = repo evidence, not terminal text.
- Fail closed if >LIVE_TERMINAL_LIMIT terminals in live mode (currently 3).
- No retries, no queue inference, no scientific interpretation.

Usage
-----
  dry-run:
    python3 system_v4/skills/pi_mono_claude_batch_launcher.py \\
        --plan .agent/state/pi_mono_claude_launch_plan__pilot_live.json \\
        --mode dry-run

  live (up to 3 terminals):
    python3 system_v4/skills/pi_mono_claude_batch_launcher.py \\
        --plan .agent/state/pi_mono_claude_launch_plan__pilot_live.json \\
        --mode live

  legacy positional (dry-run only, backward-compat):
    python3 system_v4/skills/pi_mono_claude_batch_launcher.py \\
        .agent/state/pi_mono_claude_launch_plan__current.json

Outputs (dry-run):
    .agent/state/pi_mono_batch_status__current.json
    .agent/state/pi_mono_batch_status__current.md

Outputs (live):
    .agent/state/pi_mono_batch_status__<batch_id>.json

Exit 0: clean completion (dry-run: plan valid; live: repo evidence confirmed)
Exit 1: plan error, validation failure, launch failure, timeout, or CLI not found
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

STATUS_JSON_REL = ".agent/state/pi_mono_batch_status__current.json"
STATUS_MD_REL   = ".agent/state/pi_mono_batch_status__current.md"

REQUIRED_TOP_LEVEL = ["batch_id", "repo_root", "created_at", "completion_rule", "do_not_do", "terminals"]
REQUIRED_TERMINAL  = ["terminal_id", "handoff_file", "launcher_text", "expected_review_note"]

# Live-mode constants
LIVE_TERMINAL_LIMIT = 3    # Fail closed if plan has more terminals than this.
DEFAULT_TIMEOUT_SEC = 600  # 10-minute default; override via plan "timeout_sec".
POLL_INTERVAL_SEC   = 10   # Seconds between repo-evidence checks while waiting.
CLAUDE_CMD          = "claude"  # Located via shutil.which at runtime.

# Fallback absolute paths tried when shutil.which cannot find CLAUDE_CMD.
# Claude Code CLI may be installed outside normal PATH (e.g. as a shell alias).
CLAUDE_CMD_FALLBACKS = [
    "/Users/joshuaeisenhart/.claude/local/claude",
    str(Path.home() / ".claude" / "local" / "claude"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Plan validation
# ---------------------------------------------------------------------------

def _validate_plan(plan: dict[str, Any]) -> list[str]:
    """Return a list of plan-level error strings. Empty means valid."""
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL:
        if field not in plan:
            errors.append(f"missing required top-level field: {field}")
    if errors:
        return errors

    repo_root = Path(str(plan["repo_root"]))
    if not repo_root.is_dir():
        errors.append(f"repo_root does not exist or is not a directory: {repo_root}")

    batch_id = str(plan.get("batch_id", "")).strip()
    if not batch_id:
        errors.append("batch_id is empty")

    completion_rule = str(plan.get("completion_rule", "")).strip()
    if not completion_rule:
        errors.append("completion_rule is empty")

    do_not_do = plan.get("do_not_do")
    if not isinstance(do_not_do, list) or len(do_not_do) == 0:
        errors.append("do_not_do must be a non-empty list")

    terminals = plan.get("terminals")
    if not isinstance(terminals, list) or len(terminals) == 0:
        errors.append("terminals must be a non-empty list")
    elif len(terminals) > 5:
        errors.append(f"terminals list exceeds maximum of 5 (got {len(terminals)})")

    return errors


# ---------------------------------------------------------------------------
# Per-terminal evaluation
# ---------------------------------------------------------------------------

def _eval_terminal(entry: Any, repo_root: Path, seen_ids: set[str]) -> dict[str, Any]:
    """Evaluate one terminal entry and return a status dict."""
    if not isinstance(entry, dict):
        return {
            "terminal_id": "<invalid>",
            "handoff_file": "",
            "expected_review_note": "",
            "handoff_file_exists": False,
            "review_note_present": False,
            "status": "plan_error",
            "notes": "terminal entry is not a JSON object",
        }

    tid = str(entry.get("terminal_id", "")).strip()
    handoff_rel = str(entry.get("handoff_file", "")).strip()
    launcher_text = str(entry.get("launcher_text", "")).strip()
    review_rel = str(entry.get("expected_review_note", "")).strip()

    # Plan-error checks (evaluated first, in order)
    if not tid:
        return {
            "terminal_id": "<missing>",
            "handoff_file": handoff_rel,
            "expected_review_note": review_rel,
            "handoff_file_exists": False,
            "review_note_present": False,
            "status": "plan_error",
            "notes": "terminal_id is missing or empty",
        }
    if tid in seen_ids:
        return {
            "terminal_id": tid,
            "handoff_file": handoff_rel,
            "expected_review_note": review_rel,
            "handoff_file_exists": False,
            "review_note_present": False,
            "status": "plan_error",
            "notes": f"duplicate terminal_id: {tid}",
        }
    if not launcher_text:
        seen_ids.add(tid)
        return {
            "terminal_id": tid,
            "handoff_file": handoff_rel,
            "expected_review_note": review_rel,
            "handoff_file_exists": False,
            "review_note_present": False,
            "status": "plan_error",
            "notes": "launcher_text is empty",
        }

    seen_ids.add(tid)

    handoff_path = repo_root / handoff_rel
    review_path = repo_root / review_rel
    handoff_exists = handoff_path.is_file()
    review_present = review_path.is_file()

    if not handoff_exists:
        return {
            "terminal_id": tid,
            "handoff_file": handoff_rel,
            "expected_review_note": review_rel,
            "handoff_file_exists": False,
            "review_note_present": review_present,
            "status": "handoff_missing",
            "notes": f"handoff file not found: {handoff_rel}",
        }

    if review_present:
        return {
            "terminal_id": tid,
            "handoff_file": handoff_rel,
            "expected_review_note": review_rel,
            "handoff_file_exists": True,
            "review_note_present": True,
            "status": "already_complete",
            "notes": "review note already present; task was completed in a prior session",
        }

    return {
        "terminal_id": tid,
        "handoff_file": handoff_rel,
        "expected_review_note": review_rel,
        "handoff_file_exists": True,
        "review_note_present": False,
        "status": "not_started",
        "notes": "handoff file present; review note absent; ready for launch when live mode is added",
    }


# ---------------------------------------------------------------------------
# Overall status
# ---------------------------------------------------------------------------

def _overall_status(plan_errors: list[str], terminal_results: list[dict[str, Any]]) -> str:
    if plan_errors:
        return "plan_invalid"
    statuses = [t["status"] for t in terminal_results]
    if "plan_error" in statuses:
        return "has_plan_errors"
    if "handoff_missing" in statuses:
        return "has_handoff_missing"
    if all(s == "already_complete" for s in statuses):
        return "all_already_complete"
    return "ready_to_launch"


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------

def _render_markdown(
    batch_id: str,
    checked_at: str,
    overall: str,
    plan_errors: list[str],
    terminals: list[dict[str, Any]],
) -> str:
    lines = [
        "# Pi-Mono Batch Status (dry-run)",
        "",
        f"- **batch_id**: `{batch_id}`",
        f"- **checked_at**: `{checked_at}`",
        f"- **overall_status**: `{overall}`",
        f"- **dry_run**: `true`",
        "",
    ]
    if plan_errors:
        lines += ["## Plan Errors", ""]
        for e in plan_errors:
            lines.append(f"- {e}")
        lines.append("")

    lines += [
        "## Terminals",
        "",
        "| terminal_id | handoff_exists | review_present | status | notes |",
        "|---|---|---|---|---|",
    ]
    for t in terminals:
        lines.append(
            f"| {t['terminal_id']} "
            f"| {t['handoff_file_exists']} "
            f"| {t['review_note_present']} "
            f"| {t['status']} "
            f"| {t['notes']} |"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(plan_path_arg: str) -> int:
    plan_path = Path(plan_path_arg)
    if not plan_path.is_absolute():
        plan_path = Path.cwd() / plan_path

    try:
        raw = plan_path.read_text(encoding="utf-8")
        plan: dict[str, Any] = json.loads(raw)
    except Exception as exc:
        print(f"ERROR: could not read/parse plan file {plan_path_arg}: {exc}", file=sys.stderr)
        return 1

    checked_at = _utc_iso()
    batch_id = str(plan.get("batch_id", "<unknown>")).strip() or "<unknown>"

    plan_errors = _validate_plan(plan)

    terminal_results: list[dict[str, Any]] = []
    if not plan_errors:
        repo_root = Path(str(plan["repo_root"]))
        seen_ids: set[str] = set()
        for entry in plan.get("terminals", []):
            terminal_results.append(_eval_terminal(entry, repo_root, seen_ids))

    overall = _overall_status(plan_errors, terminal_results)

    status_payload: dict[str, Any] = {
        "batch_id": batch_id,
        "checked_at": checked_at,
        "dry_run": True,
        "overall_status": overall,
        "plan_errors": plan_errors,
        "terminals": terminal_results,
    }

    # Resolve output paths relative to repo_root when available, else plan file's dir
    if not plan_errors:
        output_root = Path(str(plan["repo_root"]))
    else:
        output_root = plan_path.parent.parent.parent  # best guess: repo root from plan location
        # fallback: write next to plan
        if not (output_root / ".agent").is_dir():
            output_root = plan_path.parent

    status_json_path = output_root / STATUS_JSON_REL
    status_md_path = output_root / STATUS_MD_REL

    _write_json(status_json_path, status_payload)
    _write_text(
        status_md_path,
        _render_markdown(batch_id, checked_at, overall, plan_errors, terminal_results),
    )

    n = len(terminal_results)
    print(f"{batch_id} | {overall} | {n} terminal(s)")
    print(f"  status JSON: {status_json_path}")
    print(f"  status MD:   {status_md_path}")

    return 0


# ---------------------------------------------------------------------------
# Live mode — single-terminal subprocess launch
# ---------------------------------------------------------------------------

def _live_evidence(t: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    """Check current repo evidence for one terminal.  Returns a status dict."""
    review_path = repo_root / str(t.get("expected_review_note", ""))
    required    = [repo_root / p for p in t.get("required_output_files", [])]

    review_present   = review_path.is_file() if t.get("expected_review_note") else False
    outputs_present  = all(p.is_file() for p in required) if required else True
    complete         = review_present and outputs_present

    return {
        "terminal_id":              t.get("terminal_id"),
        "status":                   "complete" if complete else "not_started",
        "handoff_file":             t.get("handoff_file"),
        "expected_review_note":     t.get("expected_review_note"),
        "review_note_present":      review_present,
        "required_outputs_present": outputs_present,
        "notes":                    "",
    }


def _live_overall(ts_list: list[dict[str, Any]]) -> str:
    statuses = {ts["status"] for ts in ts_list}
    if all(s == "complete" for s in statuses):   return "complete"
    if "error"    in statuses:                   return "error"
    if "blocked"  in statuses:                   return "blocked"
    if "launched" in statuses:                   return "launched"
    return "not_started"


def _write_live_status(plan: dict, ts_list: list[dict], out_path: Path) -> None:
    payload = {
        "batch_id":       plan.get("batch_id"),
        "checked_at":     _utc_iso(),
        "dry_run":        False,
        "overall_status": _live_overall(ts_list),
        "terminals":      ts_list,
    }
    _write_json(out_path, payload)


def run_live(plan_path_arg: str) -> int:
    """
    Live mode: launch up to LIVE_TERMINAL_LIMIT terminals sequentially via Claude Code
    subprocess.  Fail closed if the plan contains more than LIVE_TERMINAL_LIMIT terminals.
    Poll for repo evidence after each launch; write status after every terminal update.
    """
    plan_path = Path(plan_path_arg)
    if not plan_path.is_absolute():
        plan_path = Path.cwd() / plan_path

    try:
        plan: dict[str, Any] = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: could not read/parse plan: {exc}", file=sys.stderr)
        return 1

    repo_root = Path(str(plan.get("repo_root", ""))).resolve()
    batch_id  = str(plan.get("batch_id", "unknown")).strip() or "unknown"
    terminals = plan.get("terminals", [])

    status_out = repo_root / ".agent" / "state" / f"pi_mono_batch_status__{batch_id}.json"

    # ── Fail closed above terminal limit ─────────────────────────────────────
    if len(terminals) > LIVE_TERMINAL_LIMIT:
        msg = (
            f"live mode supports at most {LIVE_TERMINAL_LIMIT} terminal(s); "
            f"plan has {len(terminals)}. Aborting without launch."
        )
        print(f"[live] FAIL CLOSED: {msg}", file=sys.stderr)
        ts_list = []
        for t in terminals:
            s = _live_evidence(t, repo_root)
            s["status"] = "error"
            s["notes"]  = msg
            ts_list.append(s)
        _write_live_status(plan, ts_list, status_out)
        print(f"[live] Status written to: {status_out}", file=sys.stderr)
        return 1

    # ── Basic validation ──────────────────────────────────────────────────────
    plan_errors = _validate_plan(plan)
    if plan_errors:
        print("[live] VALIDATION ERRORS — aborting before launch:", file=sys.stderr)
        for e in plan_errors:
            print(f"  - {e}", file=sys.stderr)
        ts_list = []
        for t in terminals:
            s = _live_evidence(t, repo_root)
            s["status"] = "error"
            s["notes"]  = "live validation failed"
            ts_list.append(s)
        _write_live_status(plan, ts_list, status_out)
        return 1

    # ── Locate claude CLI ─────────────────────────────────────────────────────
    # Try shutil.which first; fall back to known absolute paths if not on PATH.
    claude_bin = shutil.which(CLAUDE_CMD)
    if not claude_bin:
        for fallback in CLAUDE_CMD_FALLBACKS:
            if Path(fallback).is_file() and Path(fallback).stat().st_mode & 0o111:
                claude_bin = fallback
                print(f"[live] claude not on PATH; using fallback: {fallback}")
                break
    if not claude_bin:
        msg = (
            f"'{CLAUDE_CMD}' not found on PATH or known fallback paths. "
            f"Tried fallbacks: {CLAUDE_CMD_FALLBACKS}. "
            "Ensure Claude Code CLI is installed. Verify: which claude"
        )
        print(f"[live] BLOCKER: {msg}", file=sys.stderr)
        ts_list = [_live_evidence(t, repo_root) for t in terminals]
        for s in ts_list:
            s["status"] = "error"
            s["notes"]  = f"claude CLI not found (CLAUDE_CMD='{CLAUDE_CMD}', fallbacks checked)"
        _write_live_status(plan, ts_list, status_out)
        print(f"[live] Status written to: {status_out}", file=sys.stderr)
        return 1

    timeout = int(plan.get("timeout_sec", DEFAULT_TIMEOUT_SEC))

    # ── Initialize status list with current repo evidence ─────────────────────
    ts_list: list[dict[str, Any]] = [_live_evidence(t, repo_root) for t in terminals]
    _write_live_status(plan, ts_list, status_out)

    # ── Launch terminals sequentially ─────────────────────────────────────────
    for i, t in enumerate(terminals):
        tid      = t.get("terminal_id", f"<unknown-{i}>")
        launcher = t.get("launcher_text", "").strip()

        # ── Skip if already complete ──────────────────────────────────────────
        ts_entry = _live_evidence(t, repo_root)
        if ts_entry["status"] == "complete":
            print(f"[live] '{tid}': repo evidence already present — skipping launch.")
            ts_list[i] = ts_entry
            _write_live_status(plan, ts_list, status_out)
            continue

        # ── Verify handoff file exists before launch ──────────────────────────
        handoff_path = repo_root / str(t.get("handoff_file", ""))
        if not handoff_path.is_file():
            msg = f"handoff_file not found before launch: {t.get('handoff_file')}"
            print(f"[live] ABORT terminal '{tid}': {msg}", file=sys.stderr)
            ts_entry["status"] = "error"
            ts_entry["notes"]  = msg
            ts_list[i] = ts_entry
            _write_live_status(plan, ts_list, status_out)
            continue

        print(f"[live] Launching terminal '{tid}' ({i + 1}/{len(terminals)})")
        print(f"[live]   handoff_file  : {t.get('handoff_file')}")
        print(f"[live]   launcher_text : {launcher}")
        print(f"[live]   claude_bin    : {claude_bin}")
        print(f"[live]   cwd           : {repo_root}")
        print(f"[live]   timeout       : {timeout}s")

        # ── Subprocess launch via claude -p ───────────────────────────────────
        # `claude -p "<prompt>"` runs Claude Code non-interactively (print mode)
        # and exits when the task completes.
        cmd = [claude_bin, "-p", launcher]
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except OSError as exc:
            msg = f"subprocess launch failed: {exc}"
            print(f"[live] ERROR: {msg}", file=sys.stderr)
            ts_entry["status"] = "error"
            ts_entry["notes"]  = msg
            ts_list[i] = ts_entry
            _write_live_status(plan, ts_list, status_out)
            continue

        ts_entry["status"] = "launched"
        ts_list[i] = ts_entry
        _write_live_status(plan, ts_list, status_out)
        print(f"[live] Launched (pid={proc.pid}). "
              f"Polling every {POLL_INTERVAL_SEC}s (timeout={timeout}s)...")

        # ── Poll for repo evidence ────────────────────────────────────────────
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(POLL_INTERVAL_SEC)
            if _live_evidence(t, repo_root)["status"] == "complete":
                break

        # ── Collect subprocess output ─────────────────────────────────────────
        try:
            _stdout, stderr_text = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            _stdout, stderr_text = proc.communicate()
        returncode = proc.returncode

        # ── Final evidence check ──────────────────────────────────────────────
        ts_entry = _live_evidence(t, repo_root)

        if ts_entry["status"] == "complete":
            print(f"[live] '{tid}' COMPLETE — repo evidence confirmed.")
        elif time.monotonic() >= deadline:
            ts_entry["status"] = "blocked"
            ts_entry["notes"]  = f"timed out after {timeout}s; repo evidence not confirmed"
            print(f"[live] '{tid}' BLOCKED — timed out.", file=sys.stderr)
        elif returncode != 0:
            ts_entry["status"] = "error"
            ts_entry["notes"]  = (
                f"claude exited {returncode}; "
                + (f"stderr: {stderr_text[:400]}" if stderr_text else "no stderr")
            )
            print(f"[live] '{tid}' ERROR — exit code {returncode}.", file=sys.stderr)
        else:
            ts_entry["status"] = "launched"
            ts_entry["notes"]  = (
                "process exited 0 but repo evidence not confirmed; "
                "Hermes should inspect expected_review_note path manually"
            )
            print(f"[live] '{tid}' — exit 0 but repo evidence not confirmed.", file=sys.stderr)

        ts_list[i] = ts_entry
        _write_live_status(plan, ts_list, status_out)

    print(f"[live] Status written to: {status_out}")
    overall = _live_overall(ts_list)
    return 0 if overall == "complete" else 1


# ---------------------------------------------------------------------------
# Entry point (argparse + legacy positional compat)
# ---------------------------------------------------------------------------

def main() -> int:
    # Legacy positional invocation: script.py <plan.json>
    # Detect by checking whether first non-script arg looks like a flag.
    args_raw = sys.argv[1:]
    if args_raw and not args_raw[0].startswith("-"):
        # Legacy dry-run positional call.
        return run(args_raw[0])

    ap = argparse.ArgumentParser(
        description="Bounded Pi-Mono Claude Code batch launcher.",
    )
    ap.add_argument("--plan", required=True,
                    help="Path to launch plan JSON.")
    ap.add_argument("--mode", required=True, choices=["dry-run", "live"],
                    help=(
                        "'dry-run': validate and write status without launching. "
                        "'live': launch one terminal via subprocess "
                        f"(fail closed if >{LIVE_TERMINAL_LIMIT} terminal)."
                    ))
    parsed = ap.parse_args()

    if parsed.mode == "dry-run":
        return run(parsed.plan)
    else:
        return run_live(parsed.plan)


if __name__ == "__main__":
    sys.exit(main())
