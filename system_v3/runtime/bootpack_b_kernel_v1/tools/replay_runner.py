from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

THIS_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = THIS_DIR.parent
if str(RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(RUNTIME_DIR))

from zip_protocol_v2_validator import validate_zip_protocol_v2  # noqa: E402


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_bytes(obj: Any) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _load_zip_paths(path_or_paths: list[str] | None, list_file: str | None) -> list[Path]:
    paths: list[str] = []
    if list_file:
        raw = Path(list_file).read_text(encoding="utf-8")
        trimmed = raw.strip()
        if trimmed.startswith("["):
            parsed = json.loads(trimmed)
            if not isinstance(parsed, list):
                raise ValueError("zip list json must be an array")
            paths.extend(str(x) for x in parsed)
        else:
            for line in raw.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    paths.append(line)
    if path_or_paths:
        paths.extend(path_or_paths)
    if not paths:
        raise ValueError("no zip paths provided")
    return [Path(p).expanduser().resolve() for p in paths]


def _canonical_zip_digest(zip_path: Path) -> str:
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = sorted(name for name in zf.namelist() if not name.endswith("/"))
        h = hashlib.sha256()
        for name in names:
            h.update(name.encode("utf-8"))
            h.update(b"\0")
            h.update(zf.read(name))
            h.update(b"\0")
        return h.hexdigest()


def _read_zip_header(zip_path: Path) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            data = zf.read("ZIP_HEADER.json")
        header = json.loads(data.decode("utf-8"))
        if isinstance(header, dict):
            return header
    except Exception:
        return None
    return None


def _forward_prereq_met(
    run_id: str,
    sequence: int,
    forward_terminal: dict[str, set[int]],
) -> bool:
    seqs = forward_terminal.get(run_id, set())
    for s in range(1, sequence + 1):
        if s not in seqs:
            return False
    return True


def run_replay(
    zip_paths: list[Path],
    initial_state_bytes: bytes,
    compiler_version: str,
    *,
    enforce_backward_prereq: bool = True,
) -> dict[str, Any]:
    seq_state: dict[tuple[str, str], int] = {}
    forward_terminal: dict[str, set[int]] = {}

    state_hash = _sha256_bytes(initial_state_bytes)
    artifacts_emitted: list[str] = []
    events: list[dict[str, Any]] = []

    for idx, zip_path in enumerate(zip_paths, start=1):
        header = _read_zip_header(zip_path)
        zip_digest = _canonical_zip_digest(zip_path)
        state_before = state_hash

        temp_seq_state = dict(seq_state)
        result = validate_zip_protocol_v2(str(zip_path), temp_seq_state)
        outcome = str(result.get("outcome", "REJECT"))

        run_id = str(header.get("run_id", "")) if header else ""
        direction = str(header.get("direction", "")) if header else ""
        sequence = int(header.get("sequence", 0)) if header and str(header.get("sequence", "")).isdigit() else 0
        source_layer = str(header.get("source_layer", "")) if header else ""
        zip_type = str(header.get("zip_type", "")) if header else ""

        if outcome == "OK" and enforce_backward_prereq and direction == "BACKWARD":
            if not _forward_prereq_met(run_id, sequence, forward_terminal):
                outcome = "PARK"
                result = {
                    "outcome": "PARK",
                    "reason": "REPLAY_PREREQ_MISSING_FORWARD",
                }

        if outcome == "OK":
            seq_state = temp_seq_state
            if direction == "FORWARD" and run_id and sequence > 0:
                forward_terminal.setdefault(run_id, set()).add(sequence)
            state_hash = _sha256_bytes((state_hash + zip_digest + compiler_version).encode("utf-8"))
            artifacts_emitted.append(zip_digest)
        elif outcome == "PARK":
            if direction == "FORWARD" and run_id and sequence > 0:
                forward_terminal.setdefault(run_id, set()).add(sequence)
        else:
            # REJECT: stop replay immediately.
            pass

        event = {
            "index": idx,
            "zip_path": str(zip_path),
            "zip_digest": zip_digest,
            "zip_type": zip_type,
            "direction": direction,
            "source_layer": source_layer,
            "run_id": run_id,
            "sequence": sequence,
            "outcome": outcome,
            "tag": result.get("tag", ""),
            "reason": result.get("reason", ""),
            "state_hash_before": state_before,
            "state_hash_after": state_hash,
        }
        events.append(event)

        if outcome == "REJECT":
            break

    decision_trace_hash = _sha256_bytes(_canonical_json_bytes(events))
    emitted_artifacts_hash = _sha256_bytes(_canonical_json_bytes(artifacts_emitted))

    return {
        "compiler_version": compiler_version,
        "zip_sequence": [str(p) for p in zip_paths],
        "initial_state_hash": _sha256_bytes(initial_state_bytes),
        "final_state_hash": state_hash,
        "decision_trace_hash": decision_trace_hash,
        "emitted_artifacts_hash": emitted_artifacts_hash,
        "events": events,
    }


def _load_initial_state_bytes(initial_state_file: str | None, initial_state_hex: str | None) -> bytes:
    if initial_state_file:
        return Path(initial_state_file).read_bytes()
    if initial_state_hex:
        return bytes.fromhex(initial_state_hex)
    return b""


def main() -> None:
    parser = argparse.ArgumentParser(description="Deterministic ZIP replay runner")
    parser.add_argument("--zip", action="append", default=[], help="ZIP path (repeatable)")
    parser.add_argument("--zip-list", default=None, help="Path to newline list or JSON array of ZIP paths")
    parser.add_argument("--initial-state-file", default=None, help="Path to initial state snapshot bytes")
    parser.add_argument("--initial-state-hex", default=None, help="Initial state bytes as hex")
    parser.add_argument("--compiler-version", required=True, help="Compiler version pin")
    parser.add_argument("--out", required=True, help="Output JSON report path")
    parser.add_argument("--verify-determinism", action="store_true", help="Run replay twice and compare hashes")
    args = parser.parse_args()

    zip_paths = _load_zip_paths(args.zip, args.zip_list)
    initial_state = _load_initial_state_bytes(args.initial_state_file, args.initial_state_hex)

    first = run_replay(zip_paths, initial_state, args.compiler_version)
    report: dict[str, Any] = {"replay": first, "determinism_check": None}

    if args.verify_determinism:
        second = run_replay(zip_paths, initial_state, args.compiler_version)
        ok = (
            first["final_state_hash"] == second["final_state_hash"]
            and first["decision_trace_hash"] == second["decision_trace_hash"]
            and first["emitted_artifacts_hash"] == second["emitted_artifacts_hash"]
        )
        report["determinism_check"] = {
            "pass": ok,
            "first": {
                "final_state_hash": first["final_state_hash"],
                "decision_trace_hash": first["decision_trace_hash"],
                "emitted_artifacts_hash": first["emitted_artifacts_hash"],
            },
            "second": {
                "final_state_hash": second["final_state_hash"],
                "decision_trace_hash": second["decision_trace_hash"],
                "emitted_artifacts_hash": second["emitted_artifacts_hash"],
            },
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(_canonical_json_bytes(report))
    print(str(out_path))


if __name__ == "__main__":
    main()
