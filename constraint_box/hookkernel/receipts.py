"""Append-only, deterministic receipt storage for the hook kernel."""

import hashlib
import json
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def verify_chain(path):
    previous = "0" * 64
    expected_seq = 1
    if not path.exists():
        return True, None
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                return False, "invalid JSON at seq %s" % expected_seq
            payload = record.get("payload")
            if not isinstance(payload, dict):
                return False, "missing payload at seq %s" % expected_seq
            if payload.get("seq") != expected_seq:
                return False, "expected seq %s, found %s" % (expected_seq, payload.get("seq"))
            if payload.get("prev_sha256") != previous:
                return False, "prev hash mismatch at seq %s" % expected_seq
            digest = hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()
            if record.get("sha256") != digest:
                return False, "hash mismatch at seq %s" % expected_seq
            previous = digest
            expected_seq += 1
    return True, None


def append_receipt(path, event, verdict, reason_code, facts=None, details=None, error=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    valid, problem = verify_chain(path)
    if not valid:
        raise ValueError("receipt chain invalid: %s" % problem)
    last = None
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                if line.strip():
                    last = json.loads(line)
    previous = last.get("sha256", "0" * 64) if last else "0" * 64
    seq = last["payload"]["seq"] + 1 if last else 1
    payload = {
        "seq": seq,
        "prev_sha256": previous,
        "event": event,
        "verdict": verdict,
        "reason_code": reason_code,
        "facts": facts or {},
        "details": details or {},
    }
    digest = hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()
    record = {"payload": payload, "sha256": digest}
    if error:
        record["error"] = error
    with path.open("a", encoding="utf-8") as stream:
        stream.write(canonical(record) + "\n")
    return record
