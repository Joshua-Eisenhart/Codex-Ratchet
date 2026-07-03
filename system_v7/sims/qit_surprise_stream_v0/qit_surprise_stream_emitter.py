#!/usr/bin/env python3
"""Reference append-only QIT surprise JSONL stream emitter.

The Lev-side bridge consumes a stream shaped around belief Bloch coordinates,
surprise bits, and a free-energy-gradient scalar. This file intentionally does
not import the Lev bundle; it reimplements the minimal deterministic loop needed
to produce and verify transport ticks.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

TICK_SCHEMA = "cr.qit_surprise_tick.v1"
MANIFEST_SCHEMA = "cr.qit_surprise_segments_manifest.v1"
DEFAULT_STREAM_ID = "qit_surprise_stream_v0.reference"
DEFAULT_SEGMENT_LINES = 10_000
DEFAULT_START_TIME = "2026-07-03T00:00:00Z"


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: str) -> dt.datetime:
    if not value.endswith("Z"):
        raise ValueError("start time must be UTC and end in Z")
    return dt.datetime.fromisoformat(value[:-1] + "+00:00")


def canonical_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def line_sha256_without_hash(record: dict[str, Any]) -> str:
    material = {k: v for k, v in record.items() if k != "line_sha256"}
    return sha256_bytes(canonical_json(material).encode("utf-8"))


def encode_tick_line(record_without_hash: dict[str, Any]) -> bytes:
    digest = line_sha256_without_hash(record_without_hash)
    record = dict(record_without_hash)
    record["line_sha256"] = digest
    return (canonical_json(record) + "\n").encode("utf-8")


def fsync_path(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def segment_relpath(index: int) -> str:
    return f"segments/segment_{index:06d}.jsonl"


def init_manifest(stream_id: str, segment_lines: int) -> dict[str, Any]:
    return {
        "schema": MANIFEST_SCHEMA,
        "stream_id": stream_id,
        "tick_schema": TICK_SCHEMA,
        "segment_line_limit": segment_lines,
        "append_only": True,
        "reader_contract": "tail-follow current segment or poll manifest and verify line/segment hashes",
        "created_at": utc_now_iso(),
        "updated_at": utc_now_iso(),
        "next_tick": 0,
        "segments": [],
    }


def load_manifest(out_dir: Path, stream_id: str, segment_lines: int) -> dict[str, Any]:
    manifest_path = out_dir / "segments_manifest.json"
    if not manifest_path.exists():
        return init_manifest(stream_id, segment_lines)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError("manifest schema mismatch")
    if manifest.get("stream_id") != stream_id:
        raise ValueError("manifest stream_id mismatch")
    if int(manifest.get("segment_line_limit", -1)) != segment_lines:
        raise ValueError("manifest segment_line_limit mismatch")
    return manifest


def write_manifest(out_dir: Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = utc_now_iso()
    manifest_path = out_dir / "segments_manifest.json"
    tmp_path = out_dir / ".segments_manifest.json.tmp"
    tmp_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fsync_path(tmp_path)
    os.replace(tmp_path, manifest_path)
    fsync_path(manifest_path)
    fsync_dir(out_dir)


def segment_sha(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def choose_segment(out_dir: Path, manifest: dict[str, Any]) -> tuple[int, Path, dict[str, Any]]:
    segment_limit = int(manifest["segment_line_limit"])
    segments = manifest["segments"]
    if not segments or int(segments[-1]["line_count"]) >= segment_limit:
        index = len(segments)
        rel = segment_relpath(index)
        entry = {
            "path": rel,
            "first_tick": None,
            "last_tick": None,
            "line_count": 0,
            "segment_sha256": hashlib.sha256(b"").hexdigest(),
        }
        segments.append(entry)
        return index, out_dir / rel, entry
    entry = segments[-1]
    return len(segments) - 1, out_dir / entry["path"], entry


def normalize_bloch(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm <= 1.0:
        return vec
    return [v / norm for v in vec]


def observation_bloch(tick: int) -> list[float]:
    if tick < 50:
        base = [0.12, -0.08, 0.96]
    else:
        base = [-0.42, 0.37, 0.78]
    wobble = [
        0.015 * math.sin(tick / 9.0),
        0.012 * math.cos(tick / 11.0),
        0.006 * math.sin(tick / 7.0),
    ]
    return normalize_bloch([base[i] + wobble[i] for i in range(3)])


def lev_bridge_minimal_ticks(start_tick: int, count: int, stream_id: str, start_time: dt.datetime) -> list[dict[str, Any]]:
    """Emit the minimal Lev bridge stream pattern: low surprise, spike, relearn."""
    if count <= 0:
        return []
    belief = observation_bloch(0)
    previous_surprise = 0.0
    for prior_tick in range(start_tick):
        obs = observation_bloch(prior_tick)
        diff = [obs[i] - belief[i] for i in range(3)]
        previous_surprise = max(0.0, 5.0 * sum(d * d for d in diff) / (2.0 * math.log(2.0)))
        belief = normalize_bloch([belief[i] + 0.32 * diff[i] for i in range(3)])
    rows: list[dict[str, Any]] = []
    for tick in range(start_tick, start_tick + count):
        obs = observation_bloch(tick)
        diff = [obs[i] - belief[i] for i in range(3)]
        surprise_bits = max(0.0, 5.0 * sum(d * d for d in diff) / (2.0 * math.log(2.0)))
        fe_gradient = surprise_bits - previous_surprise
        row = {
            "tick": tick,
            "t_iso": (start_time + dt.timedelta(seconds=tick)).isoformat().replace("+00:00", "Z"),
            "belief_bloch": [round(v, 12) for v in belief],
            "surprise_bits": round(surprise_bits, 12),
            "fe_gradient": round(fe_gradient, 12),
            "stream_id": stream_id,
            "schema": TICK_SCHEMA,
        }
        rows.append(row)
        belief = normalize_bloch([belief[i] + 0.32 * diff[i] for i in range(3)])
        previous_surprise = surprise_bits
    return rows


def emit_ticks(out_dir: Path, ticks: int, stream_id: str, segment_lines: int, start_time: dt.datetime) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "segments").mkdir(exist_ok=True)
    manifest = load_manifest(out_dir, stream_id, segment_lines)
    start_tick = int(manifest["next_tick"])
    rows = lev_bridge_minimal_ticks(start_tick, ticks, stream_id, start_time)

    for row in rows:
        _, segment_path, entry = choose_segment(out_dir, manifest)
        segment_path.parent.mkdir(parents=True, exist_ok=True)
        line = encode_tick_line(row)
        with segment_path.open("ab") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        line_count = int(entry["line_count"]) + 1
        entry["line_count"] = line_count
        entry["first_tick"] = row["tick"] if entry["first_tick"] is None else entry["first_tick"]
        entry["last_tick"] = row["tick"]
        entry["segment_sha256"] = segment_sha(segment_path)
        manifest["next_tick"] = row["tick"] + 1
        write_manifest(out_dir, manifest)

    return verify_stream(out_dir)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def verify_stream(out_dir: Path) -> dict[str, Any]:
    manifest_path = out_dir / "segments_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    ticks_seen: list[int] = []
    segment_summaries = []

    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append("manifest_schema_mismatch")
    if manifest.get("tick_schema") != TICK_SCHEMA:
        errors.append("tick_schema_mismatch")

    for segment in manifest.get("segments", []):
        rel = Path(segment.get("path", ""))
        if rel.is_absolute() or ".." in rel.parts:
            errors.append(f"unsafe_segment_path:{rel}")
            continue
        path = out_dir / rel
        if not path.exists():
            errors.append(f"segment_missing:{rel}")
            continue
        actual_sha = segment_sha(path)
        if actual_sha != segment.get("segment_sha256"):
            errors.append(f"segment_sha_mismatch:{rel}")
        lines = path.read_bytes().splitlines()
        if len(lines) != int(segment.get("line_count", -1)):
            errors.append(f"segment_line_count_mismatch:{rel}")
        segment_ticks: list[int] = []
        for offset, raw in enumerate(lines):
            try:
                record = json.loads(raw.decode("utf-8"))
            except Exception as exc:  # pragma: no cover - defensive verifier path
                errors.append(f"line_json_malformed:{rel}:{offset}:{exc}")
                continue
            expected_line_hash = line_sha256_without_hash(record)
            if record.get("line_sha256") != expected_line_hash:
                errors.append(f"line_sha_mismatch:{rel}:{offset}")
            tick = record.get("tick")
            if not isinstance(tick, int) or tick < 0:
                errors.append(f"tick_malformed:{rel}:{offset}")
                continue
            if record.get("schema") != TICK_SCHEMA:
                errors.append(f"schema_mismatch:tick={tick}")
            if record.get("stream_id") != manifest.get("stream_id"):
                errors.append(f"stream_id_mismatch:tick={tick}")
            if not isinstance(record.get("belief_bloch"), list) or len(record["belief_bloch"]) != 3:
                errors.append(f"belief_bloch_malformed:tick={tick}")
            elif not all(finite_number(v) for v in record["belief_bloch"]):
                errors.append(f"belief_bloch_nonfinite:tick={tick}")
            if not finite_number(record.get("surprise_bits")) or float(record["surprise_bits"]) < 0:
                errors.append(f"surprise_bits_bad:tick={tick}")
            if not finite_number(record.get("fe_gradient")):
                errors.append(f"fe_gradient_bad:tick={tick}")
            segment_ticks.append(tick)
            ticks_seen.append(tick)
        if segment_ticks:
            if segment_ticks[0] != segment.get("first_tick"):
                errors.append(f"segment_first_tick_mismatch:{rel}")
            if segment_ticks[-1] != segment.get("last_tick"):
                errors.append(f"segment_last_tick_mismatch:{rel}")
        segment_summaries.append(
            {
                "path": str(rel),
                "line_count": len(lines),
                "first_tick": segment_ticks[0] if segment_ticks else None,
                "last_tick": segment_ticks[-1] if segment_ticks else None,
                "segment_sha256": actual_sha,
            }
        )

    expected_ticks = list(range(len(ticks_seen)))
    if sorted(ticks_seen) != expected_ticks:
        errors.append("tick_sequence_not_contiguous")
    if len(set(ticks_seen)) != len(ticks_seen):
        errors.append("duplicate_tick")
    if int(manifest.get("next_tick", -1)) != len(ticks_seen):
        errors.append("manifest_next_tick_mismatch")

    result = {
        "schema": "cr.qit_surprise_stream_verification.v1",
        "stream_id": manifest.get("stream_id"),
        "verified_at": utc_now_iso(),
        "ok": not errors,
        "ticks_verified": len(ticks_seen),
        "manifest_ok": not errors,
        "segments": segment_summaries,
        "errors": errors,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticks", type=int, default=100)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "results" / "reference_100")
    parser.add_argument("--stream-id", default=DEFAULT_STREAM_ID)
    parser.add_argument("--segment-lines", type=int, default=DEFAULT_SEGMENT_LINES)
    parser.add_argument("--start-time", default=DEFAULT_START_TIME)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    if args.segment_lines <= 0:
        raise SystemExit("--segment-lines must be positive")
    if args.verify_only:
        verification = verify_stream(args.out_dir)
    else:
        verification = emit_ticks(args.out_dir, args.ticks, args.stream_id, args.segment_lines, parse_utc(args.start_time))

    verification_path = args.out_dir / "verification.json"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    verification_path.write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0 if verification["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
