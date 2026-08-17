#!/usr/bin/env python3
"""Compile operational mini-voice MMM bytes and verify preload/call receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_ROOT = Path(
    os.environ.get(
        "CB_MMM_ROOT",
        Path(__file__).resolve().parents[3] / "mmms" / "primary",
    )
)
VOICES = ("FACTORY", "FEYNMAN", "HUME", "ORWELL", "POPPER", "PUSHBACK", "STRATEGY", "SYSTEMS", "ZHUANGZI")
ALGORITHM = "cb-mini-mmm-selection-v2"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def primary_paths(root: Path) -> dict[str, Path]:
    """Return only operational mini voices; main MMMs are reference material."""
    result: dict[str, Path] = {}
    for variant in ("full", "compact"):
        for voice in VOICES:
            result[f"voice:{voice.lower()}:{variant}"] = (
                root / "mini" / variant / "voices" / "md" / f"MMM_VOICE_{voice}_{variant.upper()}_v4_1.md"
            )
    return result


def choose(args: argparse.Namespace, paths: dict[str, Path]) -> tuple[int, list[tuple[str, Path]]]:
    seed = args.seed if args.seed is not None else secrets.randbits(64)
    selected: list[tuple[str, Path]] = []
    if not 2 <= args.voice_count <= len(VOICES):
        raise ValueError("voice-count must be between 2 and 9")
    ranked = sorted(VOICES, key=lambda voice: sha(f"{seed}:voice:{voice}".encode("ascii")))
    for voice in ranked[: args.voice_count]:
        variant = args.voice_variant
        if variant in ("mixed", "random"):
            variant = ("full", "compact")[int(sha(f"{seed}:variant:{voice}".encode("ascii")), 16) & 1]
        key = f"voice:{voice.lower()}:{variant}"
        selected.append((key, paths[key]))
    return seed, selected


def pool_digest(paths: dict[str, Path]) -> str:
    rows = {key: {"path": str(path.resolve()), "sha256": sha(path.read_bytes())} for key, path in sorted(paths.items())}
    return sha(canonical(rows))


def source_row(key: str, path: Path) -> tuple[dict[str, object], bytes]:
    data = path.read_bytes()
    row = {
        "primary_id": key,
        "path": str(path.resolve()),
        "sha256": sha(data),
        "source_bytes": len(data),
        "included_bytes": len(data),
        "line_count": len(data.splitlines()),
    }
    return row, data


def prepare(args: argparse.Namespace) -> int:
    root = Path(args.mmm_root).resolve()
    paths = primary_paths(root)
    missing = [str(p) for p in paths.values() if not p.is_file()]
    if missing:
        print(json.dumps({"disposition": "REFUSE_MMM_SOURCE_MISSING", "missing": missing}, sort_keys=True))
        return 2
    seed, selected = choose(args, paths)
    rows: list[dict[str, object]] = []
    blocks: list[bytes] = []
    for key, path in selected:
        row, data = source_row(key, path)
        rows.append(row)
        blocks.append(b"\n\n<!-- MMM " + key.encode("ascii") + b" -->\n" + data)
    task_path = Path(args.task_file).resolve()
    task = task_path.read_bytes()
    bundle = b"".join(blocks)
    composed = b"# MMM SALIENCE PRELOAD\n" + bundle + b"\n\n# TASK\n" + task
    if len(composed) > args.max_bytes:
        print(json.dumps({
            "disposition": "REFUSE_MMM_BUDGET_EXCEEDED",
            "selected_bytes": len(bundle),
            "composed_bytes": len(composed),
            "max_bytes": args.max_bytes,
            "seed": seed,
            "resolved_primary_ids": [r["primary_id"] for r in rows],
        }, sort_keys=True))
        return 2
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / "mmm_bundle.md"
    prompt_path = output_dir / "composed_prompt.md"
    receipt_path = output_dir / "preload_receipt.json"
    bundle_path.write_bytes(bundle)
    prompt_path.write_bytes(composed)
    receipt: dict[str, object] = {
        "schema": "constraintbox.mmm-preload.v2",
        "disposition": "CONTENT_BOUND",
        "claim_ceiling": "selected mini-voice MMM bytes compiled into prompt; provider delivery and cognition unproved",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "run_id": args.run_id,
        "agent_id": args.agent_id,
        "parent_id": args.parent_id,
        "wave_id": args.wave_id,
        "round": args.round,
        "depth": args.depth,
        "selection": {
            "algorithm": ALGORITHM,
            "python": sys.version.split()[0],
            "seed": seed,
            "voice_variant_request": args.voice_variant,
            "voice_count": args.voice_count,
            "resolved_primary_ids": [r["primary_id"] for r in rows],
        },
        "sources": rows,
        "pool_sha256": pool_digest(paths),
        "bundle_path": str(bundle_path),
        "bundle_sha256": sha(bundle),
        "bundle_bytes": len(bundle),
        "task_path": str(task_path),
        "task_sha256": sha(task),
        "composed_prompt_path": str(prompt_path),
        "composed_prompt_sha256": sha(composed),
        "composed_prompt_bytes": len(composed),
        "max_bytes": args.max_bytes,
        "provider_dispatch_proved": False,
        "behavioral_effect_claimed": False,
    }
    receipt["receipt_self_checksum"] = sha(canonical(receipt))
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"disposition": "CONTENT_BOUND", "receipt": str(receipt_path), "prompt": str(prompt_path), "prompt_sha256": sha(composed)}, sort_keys=True))
    return 0


def receipt_errors(path: Path, mmm_root: Path) -> tuple[dict[str, object], list[str]]:
    receipt = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    checksum = receipt.pop("receipt_self_checksum", None)
    if sha(canonical(receipt)) != checksum:
        errors.append("receipt_self_checksum")
    if receipt.get("schema") != "constraintbox.mmm-preload.v2" or receipt.get("disposition") != "CONTENT_BOUND":
        errors.append("envelope")
    current_paths = primary_paths(mmm_root.resolve())
    allowed = {str(p.resolve()): key for key, p in current_paths.items()}
    if receipt.get("pool_sha256") != pool_digest(current_paths):
        errors.append("pool_drift")
    rebuilt_blocks: list[bytes] = []
    for row in receipt.get("sources", []):
        p = Path(row["path"])
        data = p.read_bytes() if p.is_file() else b""
        if allowed.get(str(p.resolve())) != row.get("primary_id"):
            errors.append(f"non_primary:{p}")
        if sha(data) != row.get("sha256") or len(data) != row.get("source_bytes"):
            errors.append(f"source_drift:{p}")
        if len(data.splitlines()) != row.get("line_count"):
            errors.append(f"line_count:{p}")
        if row.get("included_bytes") != row.get("source_bytes"):
            errors.append(f"truncated:{p}")
        rebuilt_blocks.append(b"\n\n<!-- MMM " + str(row.get("primary_id", "")).encode("ascii", "replace") + b" -->\n" + data)
    ids = [row.get("primary_id") for row in receipt.get("sources", [])]
    selection = receipt.get("selection", {})
    if not isinstance(selection, dict) or ids != selection.get("resolved_primary_ids") or len(ids) != len(set(ids)):
        errors.append("selection_rows")
    elif selection.get("algorithm") != ALGORITHM or selection.get("voice_count") != len(ids):
        errors.append("selection_metadata")
    else:
        replay_args = argparse.Namespace(seed=selection.get("seed"), voice_count=selection.get("voice_count"), voice_variant=selection.get("voice_variant_request"))
        _, replayed = choose(replay_args, current_paths)
        if [key for key, _ in replayed] != ids:
            errors.append("selection_replay")
    rebuilt_bundle = b"".join(rebuilt_blocks)
    for label in ("bundle", "composed_prompt"):
        p = Path(receipt[f"{label}_path"])
        data = p.read_bytes() if p.is_file() else b""
        if sha(data) != receipt.get(f"{label}_sha256") or len(data) != receipt.get(f"{label}_bytes"):
            errors.append(f"{label}_drift")
    task = Path(receipt["task_path"])
    if not task.is_file() or sha(task.read_bytes()) != receipt.get("task_sha256"):
        errors.append("task_drift")
    if sha(rebuilt_bundle) != receipt.get("bundle_sha256") or len(rebuilt_bundle) != receipt.get("bundle_bytes"):
        errors.append("bundle_source_binding")
    if task.is_file():
        rebuilt_prompt = b"# MMM SALIENCE PRELOAD\n" + rebuilt_bundle + b"\n\n# TASK\n" + task.read_bytes()
        if sha(rebuilt_prompt) != receipt.get("composed_prompt_sha256") or len(rebuilt_prompt) != receipt.get("composed_prompt_bytes"):
            errors.append("prompt_source_binding")
    if not isinstance(receipt.get("max_bytes"), int) or receipt.get("composed_prompt_bytes", 0) > receipt.get("max_bytes", -1):
        errors.append("budget")
    receipt["receipt_self_checksum"] = checksum
    return receipt, sorted(set(errors))


def verify_content(args: argparse.Namespace) -> int:
    receipt, errors = receipt_errors(Path(args.receipt).resolve(), Path(args.mmm_root))
    disposition = "MMM_CONTENT_VERIFIED" if not errors else "REFUSE_MMM_SOURCE_DRIFT"
    print(json.dumps({"disposition": disposition, "errors": errors, "provider_dispatch_proved": False}, sort_keys=True))
    return 0 if not errors else 2


def expected(value: str) -> object:
    return None if value == "-" else value


def verify_call(args: argparse.Namespace) -> int:
    receipt_path = Path(args.receipt).resolve()
    receipt, errors = receipt_errors(receipt_path, Path(args.mmm_root))
    context = {
        "run_id": args.expect_run_id,
        "agent_id": args.expect_agent_id,
        "parent_id": expected(args.expect_parent_id),
        "wave_id": expected(args.expect_wave_id),
        "round": args.expect_round,
        "depth": args.expect_depth,
    }
    for key, value in context.items():
        if receipt.get(key) != value:
            errors.append(f"context:{key}")
    call_path = Path(args.call_receipt).resolve()
    call = json.loads(call_path.read_text(encoding="utf-8"))
    if call.get("schema") != "constraintbox.provider-call.v1":
        errors.append("call_envelope")
    if call.get("preload_receipt_sha256") != sha(receipt_path.read_bytes()):
        errors.append("call_preload_binding")
    if call.get("composed_prompt_sha256") != receipt.get("composed_prompt_sha256"):
        errors.append("call_prompt_binding")
    for key, value in context.items():
        if call.get(key) != value:
            errors.append(f"call_context:{key}")
    if not call.get("provider_request_id") or call.get("terminal_state") not in {"COMPLETED", "REFUSED", "CANCELLED", "FAILED"}:
        errors.append("call_terminal")
    disposition = "MMM_CALL_VERIFIED" if not errors else "REFUSE_MMM_CALL"
    print(json.dumps({"disposition": disposition, "errors": sorted(set(errors)), "provider_dispatch_proved": not errors}, sort_keys=True))
    return 0 if not errors else 2


def verify_round(args: argparse.Namespace) -> int:
    errors: list[str] = []
    sets: list[tuple[str, ...]] = []
    coherence: list[tuple[object, ...]] = []
    for raw in args.receipts:
        receipt, row_errors = receipt_errors(Path(raw).resolve(), Path(args.mmm_root))
        errors.extend(f"{raw}:{item}" for item in row_errors)
        selection = receipt.get("selection", {})
        sets.append(tuple(sorted(selection.get("resolved_primary_ids", []))))
        coherence.append(tuple(receipt.get(key) for key in ("run_id", "wave_id", "round", "parent_id")))
    if len(sets) != len(set(sets)):
        errors.append("duplicate_resolved_mmm_sets")
    if coherence and len(set(coherence)) != 1:
        errors.append("round_coherence")
    disposition = "MMM_ROUND_VERIFIED" if not errors else "REFUSE_MMM_ROUND"
    print(json.dumps({"disposition": disposition, "errors": sorted(set(errors)), "cells": len(sets)}, sort_keys=True))
    return 0 if not errors else 2


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--task-file", required=True)
    prep.add_argument("--output-dir", required=True)
    prep.add_argument("--run-id", required=True)
    prep.add_argument("--agent-id", required=True)
    prep.add_argument("--parent-id", default=None)
    prep.add_argument("--wave-id", default=None)
    prep.add_argument("--round", type=int, default=0)
    prep.add_argument("--depth", type=int, default=0)
    prep.add_argument("--seed", type=int)
    prep.add_argument("--voice-count", type=int, default=2)
    prep.add_argument("--voice-variant", choices=("full", "compact", "mixed", "random"), default="mixed")
    prep.add_argument("--max-bytes", type=int, default=240000)
    prep.add_argument("--mmm-root", default=str(DEFAULT_ROOT))
    prep.set_defaults(func=prepare)
    check = sub.add_parser("verify-content")
    check.add_argument("--receipt", required=True)
    check.add_argument("--mmm-root", default=str(DEFAULT_ROOT))
    check.set_defaults(func=verify_content)
    call_check = sub.add_parser("verify")
    call_check.add_argument("--receipt", required=True)
    call_check.add_argument("--call-receipt", required=True)
    call_check.add_argument("--expect-run-id", required=True)
    call_check.add_argument("--expect-agent-id", required=True)
    call_check.add_argument("--expect-parent-id", required=True, help="Use - for null")
    call_check.add_argument("--expect-wave-id", required=True, help="Use - for null")
    call_check.add_argument("--expect-round", required=True, type=int)
    call_check.add_argument("--expect-depth", required=True, type=int)
    call_check.add_argument("--mmm-root", default=str(DEFAULT_ROOT))
    call_check.set_defaults(func=verify_call)
    round_check = sub.add_parser("verify-round")
    round_check.add_argument("--receipts", nargs="+", required=True)
    round_check.add_argument("--mmm-root", default=str(DEFAULT_ROOT))
    round_check.set_defaults(func=verify_round)
    return p


if __name__ == "__main__":
    ns = parser().parse_args()
    try:
        raise SystemExit(ns.func(ns))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"disposition": "REFUSE_MMM_PRELOAD_ERROR", "detail": f"{type(exc).__name__}:{exc}"}, sort_keys=True))
        raise SystemExit(2)
