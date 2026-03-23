#!/usr/bin/env python3
"""
Thin a run directory without destroying authoritative replay lineage.

Design:
- Dry-run by default.
- Only operates inside system_v3/runs/<RUN_ID>/ (or system_v3/runs/_CURRENT_STATE).
- Targets duplicate plaintext/helper surfaces first: outbox/, snapshots/, oversized
  jsonl logs, and optional plaintext sim evidence caches.

Operational rule:
- `zip_packets/`, `tapes/`, lean `state.json`, and `state.heavy.json` are the
  authoritative local replay/resume surfaces and must not be treated as scratch.
- `outbox/` and plaintext `snapshots/` are fallback/diagnostic duplicates.
- `sim/` plaintext is duplicate helper material when equivalent SIM packet lineage exists.
- legacy `a1_sandbox/` helper churn may be thinned when authoritative packet/state/report
  lineage already exists for the run.

This is NOT a "save". Runs are local operational surfaces; authoritative save lives
in the repo-held system plus explicit save artifacts.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = REPO_ROOT / "system_v3" / "runs"


@dataclass(frozen=True)
class Action:
    kind: str
    path: Path
    detail: str


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO_ROOT))
    except Exception:
        return str(p)


def _bytes(p: Path) -> int:
    if not p.exists():
        return 0
    try:
        proc = subprocess.run(
            ["du", "-sk", str(p)],
            check=True,
            capture_output=True,
            text=True,
        )
        first = proc.stdout.strip().split()[0]
        return int(first) * 1024
    except Exception:
        if p.is_symlink() or p.is_file():
            try:
                return p.lstat().st_size
            except Exception:
                return 0
        total = 0
        for f in p.rglob("*"):
            if f.is_file() and not f.is_symlink():
                try:
                    total += f.stat().st_size
                except Exception:
                    pass
        return total


def _fmt(n: int) -> str:
    x = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if x < 1024 or unit == "TB":
            return f"{x:.1f}{unit}" if unit != "B" else f"{int(x)}B"
        x /= 1024
    return f"{x:.1f}TB"


def _is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def _truncate_tail_bytes(path: Path, keep_bytes: int) -> None:
    if keep_bytes <= 0:
        path.unlink(missing_ok=True)
        return
    size = path.stat().st_size
    if size <= keep_bytes:
        return
    with path.open("rb") as f:
        f.seek(-keep_bytes, os.SEEK_END)
        tail = f.read()
    with path.open("wb") as f:
        f.write(tail)


def _iter_jsonl_candidates(run_dir: Path) -> Iterable[Path]:
    for p in run_dir.rglob("*.jsonl"):
        if p.is_file() and not p.is_symlink():
            yield p


def _has_sim_packet_lineage(run_dir: Path) -> bool:
    zip_packets = run_dir / "zip_packets"
    if not zip_packets.is_dir():
        return False
    return any(zip_packets.glob("*_SIM_TO_A0_SIM_RESULT_ZIP.zip"))


def _has_authoritative_run_lineage(run_dir: Path) -> bool:
    state_json = run_dir / "state.json"
    zip_packets = run_dir / "zip_packets"
    reports = run_dir / "reports"
    return state_json.is_file() and zip_packets.is_dir() and reports.is_dir()


def _legacy_a1_sandbox_duplicate_dirs(run_dir: Path) -> list[Path]:
    a1_sandbox = run_dir / "a1_sandbox"
    if not a1_sandbox.is_dir():
        return []
    return [
        a1_sandbox / "lawyer_memos",
        a1_sandbox / "prepack_reports",
        a1_sandbox / "prompt_queue",
        a1_sandbox / "external_memo_exchange",
        a1_sandbox / "incoming",
        a1_sandbox / "incoming_consumed",
        a1_sandbox / "incoming_drop",
    ]


def _current_state_history_files(run_dir: Path) -> list[Path]:
    if run_dir.name != "_CURRENT_STATE":
        return []
    keep = {"state.json", "sequence_state.json"}
    out: list[Path] = []
    for p in run_dir.iterdir():
        if not p.is_file() or p.name in keep:
            continue
        if p.name.startswith("state ") and p.suffix == ".json":
            out.append(p)
        elif p.name.startswith("sequence_state ") and p.suffix == ".json":
            out.append(p)
    return out


def plan_actions(
    run_dir: Path,
    keep_jsonl_bytes: int,
    delete_sim_evidence: bool,
) -> list[Action]:
    actions: list[Action] = []

    # 0) special case: _CURRENT_STATE should be a lean pointer/cache surface only
    for stale in _current_state_history_files(run_dir):
        actions.append(
            Action(
                "delete_file",
                stale,
                "drop numbered _CURRENT_STATE history file; keep only live pointer/cache files",
            )
        )

    # 1) duplicate plaintext helper surfaces
    outbox = run_dir / "outbox"
    if outbox.exists() and outbox.is_dir():
        actions.append(Action("delete_dir", outbox, "drop duplicate outbox export cache surface"))

    snapshots = run_dir / "snapshots"
    if snapshots.exists() and snapshots.is_dir():
        actions.append(Action("delete_dir", snapshots, "drop duplicate plaintext snapshot surface"))

    # 1b) legacy a1_sandbox helper churn
    if _has_authoritative_run_lineage(run_dir):
        for dup in _legacy_a1_sandbox_duplicate_dirs(run_dir):
            if dup.exists() and dup.is_dir():
                actions.append(
                    Action(
                        "delete_dir",
                        dup,
                        "drop legacy a1_sandbox helper surface now duplicated by packet/state/report lineage",
                    )
                )

    # 2) jsonl logs: keep tail bytes
    for log in _iter_jsonl_candidates(run_dir):
        size = log.stat().st_size
        if size > keep_jsonl_bytes:
            actions.append(Action("truncate_tail", log, f"truncate to last {_fmt(keep_jsonl_bytes)} (was {_fmt(size)})"))

    # 3) plaintext sim evidence can be huge; only delete when packet lineage exists
    if delete_sim_evidence:
        sim_dir = run_dir / "sim"
        if sim_dir.exists() and sim_dir.is_dir():
            if _has_sim_packet_lineage(run_dir):
                actions.append(Action("delete_dir", sim_dir, "drop duplicate sim/ plaintext evidence cache"))
            else:
                actions.append(
                    Action(
                        "noop",
                        sim_dir,
                        "retain sim/ because no authoritative SIM packet lineage was found",
                    )
                )

    return actions


def apply_actions(actions: list[Action], run_dir: Path) -> None:
    for a in actions:
        if not _is_under(a.path, run_dir):
            raise SystemExit(f"Refusing to touch outside run_dir: {_rel(a.path)}")
        if a.kind == "delete_dir":
            shutil.rmtree(a.path)
        elif a.kind == "delete_file":
            a.path.unlink(missing_ok=True)
        elif a.kind == "truncate_tail":
            _truncate_tail_bytes(a.path, keep_bytes=_truncate_bytes_from_detail(a.detail))
        else:
            raise SystemExit(f"Unknown action kind: {a.kind}")


def _truncate_bytes_from_detail(detail: str) -> int:
    # detail is informational; do not parse. Caller should not depend on this.
    raise SystemExit("Internal error: truncate bytes must be passed directly")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True, help="Run directory name under system_v3/runs (e.g. TEST_INIT_0001 or _CURRENT_STATE)")
    ap.add_argument("--apply", action="store_true", help="Apply changes. Default is dry-run.")
    ap.add_argument("--keep-jsonl-bytes", type=int, default=200_000, help="Keep only last N bytes of any *.jsonl (default 200KB).")
    ap.add_argument(
        "--delete-sim-evidence",
        action="store_true",
        help="Delete plaintext run_dir/sim/ only when SIM packet lineage already exists.",
    )
    ap.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = ap.parse_args()

    run_dir = RUNS_ROOT / args.run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise SystemExit(f"run_dir not found: {_rel(run_dir)}")

    before = _bytes(run_dir)
    actions = plan_actions(
        run_dir=run_dir,
        keep_jsonl_bytes=args.keep_jsonl_bytes,
        delete_sim_evidence=args.delete_sim_evidence,
    )

    # We can't reuse apply_actions() for truncate (needs bytes). So apply inline.
    report = {
        "schema": "THIN_RUN_DIR_REPORT_v1",
        "run_id": args.run_id,
        "run_dir": _rel(run_dir),
        "apply": bool(args.apply),
        "before_bytes": before,
        "before_bytes_human": _fmt(before),
        "keep_jsonl_bytes": args.keep_jsonl_bytes,
        "delete_sim_evidence": bool(args.delete_sim_evidence),
        "action_count": len(actions),
        "actions": [{"kind": a.kind, "path": _rel(a.path), "detail": a.detail} for a in actions],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"run={_rel(run_dir)} apply={args.apply} before={_fmt(before)} actions={len(actions)}")
        for a in actions[:60]:
            print(f"- {a.kind}: {_rel(a.path)} :: {a.detail}")
        if len(actions) > 60:
            print(f"... ({len(actions)-60} more)")

    if not args.apply:
        return 0

    for a in actions:
        if not _is_under(a.path, run_dir):
            raise SystemExit(f"Refusing to touch outside run_dir: {_rel(a.path)}")
        if a.kind == "delete_dir":
            shutil.rmtree(a.path)
        elif a.kind == "delete_file":
            a.path.unlink(missing_ok=True)
        elif a.kind == "truncate_tail":
            _truncate_tail_bytes(a.path, keep_bytes=args.keep_jsonl_bytes)
        elif a.kind == "noop":
            continue
        else:
            raise SystemExit(f"Unknown action kind: {a.kind}")

    after = _bytes(run_dir)
    if not args.json:
        print(f"after={_fmt(after)} saved={_fmt(before-after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
