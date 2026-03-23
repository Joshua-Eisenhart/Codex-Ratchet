#!/usr/bin/env python3
"""
Conservative packet-journal compaction pilot for one run.

Design:
- Dry-run by default.
- Only targets packet classes that have already been audited as checkpoint-like:
  - B_TO_A0_STATE_UPDATE_ZIP
  - A0_TO_A1_SAVE_ZIP
- Keeps:
  - earliest packet
  - latest packet
  - every Nth checkpoint
  - the most recent tail window
- Leaves all other packet classes untouched.

This is intentionally narrower than thin_run_dir.py. It is a pilot for proving
class-specific packet retention rules before broader rollout.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNS_ROOT = REPO_ROOT / "system_v3" / "runs"

STATE_UPDATE_CLASS = "B_TO_A0_STATE_UPDATE_ZIP.zip"
DEFAULT_TARGET_CLASSES = (
    STATE_UPDATE_CLASS,
    "A0_TO_A1_SAVE_ZIP.zip",
)

OPTIONAL_TARGET_CLASSES = {
    "A0_TO_B_EXPORT_BATCH_ZIP.zip",
}
STRATEGY_CLASS = "A1_TO_A0_STRATEGY_ZIP.zip"


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


def _bytes(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        proc = subprocess.run(
            ["du", "-sk", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return int(proc.stdout.strip().split()[0]) * 1024
    except Exception:
        if path.is_file():
            try:
                return path.stat().st_size
            except Exception:
                return 0
        total = 0
        for p in path.rglob("*"):
            if p.is_file() and not p.is_symlink():
                try:
                    total += p.stat().st_size
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


def _packet_files(zip_dir: Path, suffix: str) -> list[Path]:
    return sorted(zip_dir.glob(f"*_{suffix}"))


def _retain_set(files: list[Path], checkpoint_every: int, tail_count: int) -> set[Path]:
    keep: set[Path] = set()
    if not files:
        return keep
    keep.add(files[0])
    keep.add(files[-1])
    for idx, path in enumerate(files, start=1):
        if checkpoint_every > 0 and idx % checkpoint_every == 0:
            keep.add(path)
    if tail_count > 0:
        keep.update(files[-tail_count:])
    return keep


def _strategy_shape(path: Path) -> tuple[int, int]:
    try:
        with zipfile.ZipFile(path) as zf:
            target = next(name for name in zf.namelist() if name.endswith("A1_STRATEGY_v1.json"))
            data = json.loads(zf.read(target))
        return len(data.get("targets", [])), len(data.get("alternatives", []))
    except Exception:
        return (-1, -1)


def _strategy_retain_set(files: list[Path], checkpoint_every: int, tail_count: int) -> set[Path]:
    keep = _retain_set(files, checkpoint_every=checkpoint_every, tail_count=tail_count)
    last_shape: tuple[int, int] | None = None
    for path in files:
        shape = _strategy_shape(path)
        if shape != last_shape:
            keep.add(path)
            last_shape = shape
    return keep


def plan_actions(
    run_dir: Path,
    checkpoint_every: int,
    tail_count: int,
    state_checkpoint_every: int,
    state_tail_count: int,
    strategy_checkpoint_every: int,
    strategy_tail_count: int,
    target_classes: tuple[str, ...],
) -> list[Action]:
    zip_dir = run_dir / "zip_packets"
    if not zip_dir.is_dir():
        return []

    actions: list[Action] = []
    for suffix in target_classes:
        files = _packet_files(zip_dir, suffix)
        if suffix == STRATEGY_CLASS:
            cls_checkpoint_every = strategy_checkpoint_every
            cls_tail_count = strategy_tail_count
            keep = _strategy_retain_set(files, checkpoint_every=cls_checkpoint_every, tail_count=cls_tail_count)
        elif suffix == STATE_UPDATE_CLASS:
            cls_checkpoint_every = state_checkpoint_every
            cls_tail_count = state_tail_count
            keep = _retain_set(files, checkpoint_every=cls_checkpoint_every, tail_count=cls_tail_count)
        else:
            cls_checkpoint_every = checkpoint_every
            cls_tail_count = tail_count
            keep = _retain_set(files, checkpoint_every=cls_checkpoint_every, tail_count=cls_tail_count)
        for path in files:
            if path not in keep:
                actions.append(
                    Action(
                        "delete_file",
                        path,
                        (
                            "drop superseded checkpoint-like packet; retained earliest/latest/"
                            f"every-{cls_checkpoint_every} checkpoint/tail-{cls_tail_count}"
                        ),
                    )
                )
    return actions


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True, help="Run directory name under system_v3/runs")
    ap.add_argument("--apply", action="store_true", help="Apply deletions. Default is dry-run.")
    ap.add_argument("--checkpoint-every", type=int, default=100, help="Retain every Nth packet in targeted classes.")
    ap.add_argument("--tail-count", type=int, default=50, help="Retain the most recent N packets in targeted classes.")
    ap.add_argument(
        "--state-checkpoint-every",
        type=int,
        default=200,
        help="Retain every Nth B_TO_A0_STATE_UPDATE_ZIP packet.",
    )
    ap.add_argument(
        "--state-tail-count",
        type=int,
        default=25,
        help="Retain the most recent N B_TO_A0_STATE_UPDATE_ZIP packets.",
    )
    ap.add_argument(
        "--include-export-batches",
        action="store_true",
        help="Also compact A0_TO_B_EXPORT_BATCH_ZIP using the same checkpoint/tail retention rule.",
    )
    ap.add_argument(
        "--include-strategy-history",
        action="store_true",
        help="Dry-run or apply a conservative A1_TO_A0_STRATEGY_ZIP retention rule.",
    )
    ap.add_argument(
        "--strategy-checkpoint-every",
        type=int,
        default=50,
        help="Retain every Nth A1_TO_A0_STRATEGY_ZIP packet.",
    )
    ap.add_argument(
        "--strategy-tail-count",
        type=int,
        default=50,
        help="Retain the most recent N A1_TO_A0_STRATEGY_ZIP packets.",
    )
    ap.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = ap.parse_args()

    run_dir = RUNS_ROOT / args.run_id
    if not run_dir.is_dir():
        raise SystemExit(f"run_dir not found: {_rel(run_dir)}")

    target_classes = list(DEFAULT_TARGET_CLASSES)
    if args.include_export_batches:
        target_classes.extend(sorted(OPTIONAL_TARGET_CLASSES))
    if args.include_strategy_history:
        target_classes.append(STRATEGY_CLASS)

    before = _bytes(run_dir / "zip_packets")
    actions = plan_actions(
        run_dir,
        checkpoint_every=args.checkpoint_every,
        tail_count=args.tail_count,
        state_checkpoint_every=args.state_checkpoint_every,
        state_tail_count=args.state_tail_count,
        strategy_checkpoint_every=args.strategy_checkpoint_every,
        strategy_tail_count=args.strategy_tail_count,
        target_classes=tuple(target_classes),
    )

    report = {
        "schema": "COMPACT_RUN_PACKETS_REPORT_v1",
        "run_id": args.run_id,
        "run_dir": _rel(run_dir),
        "apply": bool(args.apply),
        "target_classes": list(target_classes),
        "checkpoint_every": args.checkpoint_every,
        "tail_count": args.tail_count,
        "state_checkpoint_every": args.state_checkpoint_every,
        "state_tail_count": args.state_tail_count,
        "strategy_checkpoint_every": args.strategy_checkpoint_every,
        "strategy_tail_count": args.strategy_tail_count,
        "before_zip_packets_bytes": before,
        "before_zip_packets_human": _fmt(before),
        "action_count": len(actions),
        "actions": [{"kind": a.kind, "path": _rel(a.path), "detail": a.detail} for a in actions],
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"run={_rel(run_dir)} apply={args.apply} "
            f"zip_packets_before={_fmt(before)} actions={len(actions)}"
        )
        for a in actions[:60]:
            print(f"- {a.kind}: {_rel(a.path)} :: {a.detail}")
        if len(actions) > 60:
            print(f"... ({len(actions)-60} more)")

    if not args.apply:
        return 0

    for a in actions:
        if not _is_under(a.path, run_dir):
            raise SystemExit(f"Refusing to touch outside run_dir: {_rel(a.path)}")
        if a.kind != "delete_file":
            raise SystemExit(f"Unknown action kind: {a.kind}")
        a.path.unlink(missing_ok=True)

    after = _bytes(run_dir / "zip_packets")
    if not args.json:
        print(f"zip_packets_after={_fmt(after)} saved={_fmt(before - after)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
