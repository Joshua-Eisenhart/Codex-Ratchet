#!/usr/bin/env python3
"""
Thin a run directory so it stays readable and doesn't melt context windows.

Design:
- Dry-run by default.
- Only operates inside system_v3/runs/<RUN_ID>/ (or system_v3/runs/_CURRENT_STATE).
- Targets common bloat: zip_packets/, large jsonl logs, large state.json copies.

This is NOT a "save". Runs are scratch caches. The save is the system folder + brains.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
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


def plan_actions(
    run_dir: Path,
    keep_zip_packets: int,
    keep_jsonl_bytes: int,
    delete_sim_evidence: bool,
) -> list[Action]:
    actions: list[Action] = []

    # 1) zip_packets bloat
    zip_packets = run_dir / "zip_packets"
    if zip_packets.exists() and zip_packets.is_dir():
        packets = sorted([p for p in zip_packets.iterdir() if p.is_file()])
        if keep_zip_packets <= 0:
            actions.append(Action("delete_dir", zip_packets, "drop all zip_packets (scratch only)"))
        elif len(packets) > keep_zip_packets:
            to_delete = packets[: max(0, len(packets) - keep_zip_packets)]
            for p in to_delete:
                actions.append(Action("delete_file", p, f"keep last {keep_zip_packets} packets"))

    # 2) jsonl logs: keep tail bytes
    for log in _iter_jsonl_candidates(run_dir):
        size = log.stat().st_size
        if size > keep_jsonl_bytes:
            actions.append(Action("truncate_tail", log, f"truncate to last {_fmt(keep_jsonl_bytes)} (was {_fmt(size)})"))

    # 3) sim evidence can be huge; delete by default when thinning
    if delete_sim_evidence:
        sim_dir = run_dir / "sim"
        if sim_dir.exists() and sim_dir.is_dir():
            actions.append(Action("delete_dir", sim_dir, "drop sim/ outputs (regen or promote elsewhere)"))

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
    ap.add_argument("--keep-zip-packets", type=int, default=0, help="How many newest zip_packets to keep (default 0).")
    ap.add_argument("--keep-jsonl-bytes", type=int, default=200_000, help="Keep only last N bytes of any *.jsonl (default 200KB).")
    ap.add_argument("--delete-sim-evidence", action="store_true", help="Delete run_dir/sim/ entirely.")
    ap.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = ap.parse_args()

    run_dir = RUNS_ROOT / args.run_id
    if not run_dir.exists() or not run_dir.is_dir():
        raise SystemExit(f"run_dir not found: {_rel(run_dir)}")

    before = _bytes(run_dir)
    actions = plan_actions(
        run_dir=run_dir,
        keep_zip_packets=args.keep_zip_packets,
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
        "keep_zip_packets": args.keep_zip_packets,
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
        else:
            raise SystemExit(f"Unknown action kind: {a.kind}")

    after = _bytes(run_dir)
    if not args.json:
        print(f"after={_fmt(after)} saved={_fmt(before-after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

