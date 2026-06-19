#!/usr/bin/env python3
"""Generate durable hash-bound receipts for foundation envelope results."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "system_v5/ops/formal_scouts/results"
RECEIPTS_DIR = ROOT / "system_v5/ops/audit_receipts"
VALIDATOR = ROOT / "scripts/validate_three_engine_sim_result.py"
PATTERNS = ("foundation_*results.json", "foundation_foundation_*results.json")


def now_utc() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def resolve_path(value: Any) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    if not path.is_absolute():
        path = ROOT / path
    return path


def foundation_results(results_dir: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in PATTERNS:
        files.update(results_dir.glob(pattern))
    return sorted(files)


def envelope_results(results_dir: Path) -> list[Path]:
    return [
        path
        for path in foundation_results(results_dir)
        if "envelope" in path.name and load_json(path).get("schema_version") == "three_engine_sim_result_v1"
    ]


def run_validator(result_path: Path) -> dict[str, Any]:
    command = [sys.executable, str(VALIDATOR), str(result_path), "--require-pytorch"]
    completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    stdout = completed.stdout.strip()
    parsed_stdout: Any | None = None
    if stdout:
        try:
            parsed_stdout = json.loads(stdout)
        except json.JSONDecodeError:
            parsed_stdout = None
    return {
        "command": command,
        "returncode": completed.returncode,
        "ok": completed.returncode == 0,
        "stdout": stdout,
        "stdout_json": parsed_stdout,
        "stderr": completed.stderr.strip(),
    }


def existing_receipts(receipts_dir: Path) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for path in sorted(receipts_dir.glob("*.json")):
        try:
            payload = load_json(path)
        except Exception:
            continue
        payload["_receipt_path"] = str(path)
        receipts.append(payload)
    return receipts


def matching_receipt(
    receipts: list[dict[str, Any]], source_path: Path, source_sha256: str
) -> dict[str, Any] | None:
    source_real = os.path.realpath(source_path)
    for receipt in receipts:
        if receipt.get("source_sha256") != source_sha256:
            continue
        receipt_file = receipt.get("file_realpath") or receipt.get("file")
        if receipt_file and os.path.realpath(str(receipt_file)) == source_real:
            return receipt
    return None


def receipt_path_for(envelope_result: Path, source_sha256: str, receipts_dir: Path) -> Path:
    stem = envelope_result.name.removesuffix("_results.json")
    return receipts_dir / f"foundation_envelope__{stem}__{source_sha256[:12]}.json"


def leg_records(payload: dict[str, Any], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    records: dict[str, Any] = {}
    engines = payload.get("engines") or {}
    for name in ("julia", "jax", "pytorch"):
        engine = engines.get(name) or {}
        source_path = resolve_path(engine.get("source_path"))
        result_path = resolve_path(engine.get("result_path"))
        record: dict[str, Any] = {
            "source_path": str(source_path) if source_path else None,
            "result_path": str(result_path) if result_path else None,
            "source_sha256": None,
            "durable_audit_receipt": {"exists": False, "path": None},
        }
        if source_path and source_path.exists():
            source_sha = sha256_file(source_path)
            record["source_sha256"] = source_sha
            receipt = matching_receipt(receipts, source_path, source_sha)
            if receipt:
                record["durable_audit_receipt"] = {
                    "exists": True,
                    "path": receipt.get("_receipt_path"),
                    "authority_verdict": (receipt.get("authority") or {}).get("verdict"),
                }
        records[name] = record
    return records


def build_receipt(envelope_result: Path, payload: dict[str, Any], receipts: list[dict[str, Any]]) -> dict[str, Any]:
    source_path = resolve_path(payload.get("source_path"))
    if source_path is None or not source_path.exists():
        raise ValueError(f"{envelope_result} has missing envelope source_path")
    source_sha = sha256_file(source_path)
    recorded_sha = payload.get("source_sha256")
    validator = run_validator(envelope_result)
    max_divergence = (payload.get("divergence") or {}).get("max_divergence")
    authority_verdict = "GENUINE" if validator["ok"] and recorded_sha == source_sha else "BLOCK"
    authority_raw = {
        "validator_ok": validator["ok"],
        "recorded_source_sha256_matches_current": recorded_sha == source_sha,
    }
    return {
        "schema_version": "foundation_envelope_audit_receipt_v1",
        "receipt_kind": "foundation_envelope_hash_pin",
        "rung": payload.get("rung_id") or envelope_result.name.removesuffix("_results.json"),
        "file": str(source_path),
        "file_realpath": os.path.realpath(source_path),
        "source_sha256": source_sha,
        "source_size_bytes": source_path.stat().st_size,
        "source_mtime": source_path.stat().st_mtime,
        "source_mtime_iso": dt.datetime.fromtimestamp(source_path.stat().st_mtime, dt.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "envelope_result_path": str(envelope_result),
        "envelope_result_source_sha256": recorded_sha,
        "audited_at": now_utc(),
        "validator": validator,
        "max_divergence": max_divergence,
        "constituent_legs": leg_records(payload, receipts),
        "authority": {
            "model": "local scripts/validate_three_engine_sim_result.py --require-pytorch",
            "returncode": validator["returncode"],
            "verdict": authority_verdict,
            "raw": json.dumps(authority_raw, sort_keys=True),
        },
        "alt_views": {},
        "classification": "infrastructure_scratch",
        "promotion_allowed": False,
    }


def write_receipts(results_dir: Path, receipts_dir: Path) -> dict[str, Any]:
    receipts_dir.mkdir(parents=True, exist_ok=True)
    existing = existing_receipts(receipts_dir)
    report: dict[str, Any] = {
        "matched_envelopes": 0,
        "written": 0,
        "skipped_existing_current": 0,
        "validator_failed": [],
        "missing_or_mismatched_source_pin": [],
        "receipts": [],
    }
    for envelope_result in envelope_results(results_dir):
        report["matched_envelopes"] += 1
        payload = load_json(envelope_result)
        receipt = build_receipt(envelope_result, payload, existing)
        out_path = receipt_path_for(envelope_result, receipt["source_sha256"], receipts_dir)

        if receipt["authority"]["verdict"] != "GENUINE":
            report["validator_failed"].append(str(envelope_result))
        if receipt["envelope_result_source_sha256"] != receipt["source_sha256"]:
            report["missing_or_mismatched_source_pin"].append(str(envelope_result))

        if out_path.exists():
            try:
                old = load_json(out_path)
            except Exception:
                old = {}
            if (
                old.get("source_sha256") == receipt["source_sha256"]
                and (old.get("validator") or {}).get("ok") == receipt["validator"]["ok"]
                and old.get("envelope_result_source_sha256") == receipt["envelope_result_source_sha256"]
            ):
                report["skipped_existing_current"] += 1
                report["receipts"].append(str(out_path))
                continue

        out_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        report["written"] += 1
        report["receipts"].append(str(out_path))
        existing.append({**receipt, "_receipt_path": str(out_path)})

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--receipts-dir", type=Path, default=RECEIPTS_DIR)
    args = parser.parse_args()

    report = write_receipts(args.results_dir, args.receipts_dir)
    print(json.dumps(report, indent=2))
    return 1 if report["validator_failed"] or report["missing_or_mismatched_source_pin"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
