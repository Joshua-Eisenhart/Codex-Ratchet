"""Detection and session-freezing spine; not a protected location.

The owner account can write every local tree. Claude snapshots hooks at session start,
the manifest detects kernel movement, the chained store detects receipt rewriting, and
server-side GitHub required checks form the outer boundary. This is detection and
session-freezing, not impossibility.
"""

import argparse
import datetime
import hashlib
import json
import os
import sys
import traceback
from pathlib import Path

from .receipts import append_receipt, canonical, verify_chain

MANDATED_INTERPRETER = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
STALE_DAYS_MAX = 548
EXIT_ADMIT = 0
EXIT_HOLD = 2


def _root():
    return Path(os.environ.get("CB_HOOKKERNEL_ROOT", Path(__file__).resolve().parent))


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _verify_manifest(root):
    manifest = root / "manifest.json"
    if not manifest.exists():
        return False, "manifest missing"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    for name, expected in data.get("files", {}).items():
        path = root / name
        if not path.exists() or expected in ("", "REPLACED_AT_BUILD") or _sha256(path) != expected:
            return False, name
    return True, None


def _load_payload(raw):
    if raw is None:
        return {}
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("payload must be a JSON object")
    return value


def _date(value):
    return datetime.date.fromisoformat(str(value)[:10])


def _estate_rows(payload, root):
    rows = payload.get("estate_rows")
    if rows is not None:
        return rows, payload.get("stale_days_max", STALE_DAYS_MAX)
    config = root.parent / "config" / "cb_light_library_candidates.json"
    if not config.exists():
        return [], STALE_DAYS_MAX
    data = json.loads(config.read_text(encoding="utf-8"))
    rows = []
    for candidate in data.get("candidates", []):
        verified = candidate.get("verified", {})
        if verified.get("release_date"):
            rows.append({"id": candidate.get("pypi_name"), "date": verified["release_date"]})
    return rows, data.get("stale_days_max", STALE_DAYS_MAX)


def _evaluate(event, payload, root, registry):
    if event not in registry.get("events", {}):
        return "HOLD", "HOOK_RESULT_INVALID", {}, {"unknown_event": event}
    if event == "session_start":
        today = _date(payload.get("today", datetime.date.today().isoformat()))
        rows, limit = _estate_rows(payload, root)
        stale = []
        for row in rows:
            age = (today - _date(row["date"])).days
            if age > int(limit):
                stale.append({"id": row.get("id", "unknown"), "age_days": age, "stale_days_max": int(limit)})
        if stale:
            return "HOLD", "CURRENTNESS_EXPIRED", {"estate_currentness": "stale"}, {"stale": stale}
        return "ADMIT", "CURRENTNESS_VALID", {"estate_currentness": "current"}, {"checked": len(rows)}
    if event == "pip_command_observed":
        tool_input = payload.get("tool_input", {})
        command = payload.get("command") or (tool_input.get("command", "") if isinstance(tool_input, dict) else "")
        command = str(command)
        if MANDATED_INTERPRETER not in command:
            return "REFUSE", "ENV_INTERPRETER_MISMATCH", {"environment_identity": "mismatch"}, {"command": command}
        return "ADMIT", "ENV_INTERPRETER_VALID", {"environment_identity": "valid"}, {}
    if event == "dependency_file_changed":
        if payload.get("lock_covers_declared_set") is True:
            return "ADMIT", "LOCK_VALID", {"lock_validity": "valid"}, {}
        return "HOLD", "LOCK_STALE", {"lock_validity": "stale"}, {}
    if event == "cb_source_changed":
        modules = payload.get("modules", [])
        return "HOLD", "PROBES_REQUIRED", {"integration_validity": "stale"}, {"modules": modules}
    if event == "task_completion_claimed":
        receipts = root / "receipts.jsonl"
        valid, problem = verify_chain(receipts)
        if not valid:
            return "REFUSE", "COMPLETION_UNEARNED", {"receipt_chain": "broken"}, {"missing": [problem]}
        required = payload.get("required_facts", [])
        missing = list(required)
        good = ("valid", "current", "fresh")
        # Replay the chain and keep the LATEST state of each constraint fact. A
        # HOLD is open only while its fact is still bad; a later receipt that
        # restores the fact to a good state closes it. Without this a HOLD is
        # write-once and the gate deadlocks permanently on the first one ever
        # written. Only HOLD and ADMIT verdicts carry ongoing constraint state;
        # a REFUSE means an action was blocked (transient), and a HOLD with no
        # fact (a transient HOOK_RESULT_INVALID) is a logged error, not a
        # constraint, so neither participates here.
        fact_state = {}  # fact -> (latest_value, reason_code)
        if receipts.exists():
            for line in receipts.read_text(encoding="utf-8").splitlines():
                body = json.loads(line)["payload"]
                if body.get("verdict") not in ("HOLD", "ADMIT"):
                    continue
                for fact, value in body.get("facts", {}).items():
                    fact_state[fact] = (value, body.get("reason_code"))
        for fact, (value, _reason) in fact_state.items():
            if fact in missing and value in good:
                missing.remove(fact)
        open_holds = sorted(
            reason for _fact, (value, reason) in fact_state.items() if value not in good
        )
        if missing or open_holds:
            return "REFUSE", "COMPLETION_UNEARNED", {"required_facts": "stale"}, {"missing": missing, "open_holds": open_holds}
        return "ADMIT", "COMPLETION_EARNED", {"required_facts": "fresh"}, {}
    return "ADMIT", "OBSERVATION_RECORDED", {}, {"observation": payload}


def dispatch(event, payload_raw=None):
    root = _root()
    receipts = root / "receipts.jsonl"
    try:
        manifest_ok, manifest_problem = _verify_manifest(root)
        if not manifest_ok:
            missing_registry = manifest_problem == "registry.json" and not (root / "registry.json").exists()
            reason = "HOOK_UNAVAILABLE" if missing_registry else "KERNEL_TAMPERED"
            record = append_receipt(receipts, event, "HOLD", reason, details={"file": manifest_problem})
            return EXIT_HOLD, record
        try:
            payload = _load_payload(payload_raw)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            record = append_receipt(receipts, event, "HOLD", "HOOK_RESULT_INVALID", details={"error": str(exc)})
            return EXIT_HOLD, record
        registry_path = root / "registry.json"
        if not registry_path.exists():
            record = append_receipt(receipts, event, "HOLD", "HOOK_UNAVAILABLE", details={"file": "registry.json"})
            return EXIT_HOLD, record
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        verdict, reason, facts, details = _evaluate(event, payload, root, registry)
        record = append_receipt(receipts, event, verdict, reason, facts, details)
        return (EXIT_ADMIT if verdict == "ADMIT" else EXIT_HOLD), record
    except Exception as exc:
        try:
            record = append_receipt(receipts, event, "HOLD", "UNHANDLED_EXCEPTION", error=traceback.format_exc())
            return EXIT_HOLD, record
        except Exception:
            return EXIT_HOLD, {"verdict": "HOLD", "reason_code": "UNHANDLED_EXCEPTION", "error": traceback.format_exc()}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("event")
    parser.add_argument("--payload-json")
    args = parser.parse_args(argv)
    code, record = dispatch(args.event, args.payload_json)
    print(canonical(record))
    if code == EXIT_HOLD:
        print("%s: %s" % (record.get("reason_code", record.get("payload", {}).get("reason_code")), canonical(record)), file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
