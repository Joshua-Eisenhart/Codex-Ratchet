#!/usr/bin/env python3
"""DURABLE GATE LEDGER — the append-only, hash-chained record of every gate run.

WHY THIS EXISTS
    Before this file, claimgate_plugin/orphan_receipt_detector.py measured
    2876 claim-bearing receipts and 0 durable gate-ledger records: 2876/2876
    orphans.  The gate ran, printed to stderr, and returned an exit code that
    nothing outlived.  A receipt in the tree was therefore indistinguishable
    from a receipt that had never been near the gate.  That is the cause the
    ledger closes: one chained line per gate run, written by the fired chain
    (claimgate_plugin/hooks/post_receipt_gate.sh) from an EXIT trap.

WHAT IT RECORDS — EVERY run, not only the passes
    A gate that logs only its successes cannot tell "never ran" from "ran and
    refused", so BLOCKED / PARKED / INFRA_ERROR / INCOMPLETE runs are written
    with the same standing as PASS.  disposition is set per-stage by the shell
    because the exit code alone is ambiguous: intake exit 3 is PARK (blocks
    admission) while claim_verify exit 3 is ADMITTED_PENDING_DEPTH (does not).

TAMPER EVIDENCE, AND ITS HONEST CEILING
    prev_line_sha256 chains each line to the exact bytes of the line before it,
    so an EDITED line breaks the next line's pointer and a DELETED interior line
    breaks the chain at the deletion.  A truncated TAIL is not detectable from
    the chain alone, so a sidecar head anchor (gate_ledger.head.json) records the
    count and the last line hash; truncation then requires editing two files
    consistently.  It raises the bar; it does not close it.  Both files live in
    the same repo as the gate, which is the same E2 ceiling as CI-config-in-repo:
    this is DETECTION, never prevention.

    NEVER rewrite history here.  Ungated historical receipts must stay counted
    as ungated; a backfilled line would be a fabricated gate run.

stdlib only.  Nonzero exit is a policy/infra disposition, never a scientific
verdict.

CLI
    gate_ledger.py append <receipt> --exit N --disposition D
                          [--blocking-stage S] [--stages "intake=0,tier0=1"]
    gate_ledger.py verify [ledger.jsonl]
    gate_ledger.py source
"""
from __future__ import annotations

import argparse
import datetime
import fcntl
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

SCHEMA = "claimgate_gate_ledger_v1"

# First line's prev pointer. A fixed constant, so "someone started the ledger
# over" is distinguishable from a legitimate first line.
GENESIS = hashlib.sha256(f"{SCHEMA}/genesis".encode()).hexdigest()

PLUGIN_DIR = Path(__file__).resolve().parent
LEDGER_PATH = PLUGIN_DIR / "results" / "gate_ledger.jsonl"

# ---------------------------------------------------------------- AUTHORSHIP
# An unkeyed SHA-256 chain proves CONSISTENCY, not AUTHORSHIP: anyone who can
# write the file can regenerate a wholly self-consistent chain from scratch,
# head anchor included, and verify() would accept it. The chain answers "were
# these lines edited after the fact"; it cannot answer "did the gate write them".
#
# So each record also carries an HMAC-SHA256 over its own canonical bytes, keyed
# by a secret that must live OUTSIDE writable repo content. A key committed
# beside the ledger would be forgeable by exactly the people the MAC excludes,
# so a key path inside the repo is REFUSED rather than trusted.
#
# HONEST CEILING. This raises forgery from "edit a file" to "hold the key". It
# does not stop someone who can read the key, and it is still detection, not
# prevention. Absent key => records are written UNKEYED and verify() reports
# CONSISTENT_UNATTRIBUTED. That is never upgraded to "verified".
KEY_ENV = "CLAIMGATE_LEDGER_KEY_FILE"
DEFAULT_KEY_PATH = Path.home() / ".config" / "claimgate" / "ledger.key"
REPO_ROOT = PLUGIN_DIR.parent


# TEST vs PRODUCTION authentication must be distinguishable IN THE RECORD, not in
# prose next to it. A dogfood run with an ephemeral scratchpad key wrote a record
# reading `mac_status: KEYED` while no production key existed anywhere; that record
# is durable, and later readers would take it for production authentication. So:
#
#   PRODUCTION_KEYED  key at DEFAULT_KEY_PATH, or CLAIMGATE_LEDGER_KEY_MODE=production
#   TEST_KEYED        any other key location — the FAIL-SAFE default, because an
#                     unlabelled key must never inherit production authority
#   UNKEYED           no usable key; consistency only, no authorship
#
# key_fingerprint is sha256(key)[:16] — enough to tell two keys apart across runs
# without carrying the secret. Never log the key itself.
MODE_ENV = "CLAIMGATE_LEDGER_KEY_MODE"
TEMP_PREFIXES = ("/tmp", "/private/tmp", "/var/folders", "/private/var/folders")


def classify_key(resolved: Path, key: bytes) -> tuple[str, str]:
    """(key_mode, key_fingerprint). Production is OPT-IN and explicit."""
    fp = hashlib.sha256(key).hexdigest()[:16]
    declared = (os.environ.get(MODE_ENV) or "").strip().lower()
    if declared == "production" and not str(resolved).startswith(TEMP_PREFIXES):
        return "PRODUCTION_KEYED", fp
    if resolved == DEFAULT_KEY_PATH.resolve() if DEFAULT_KEY_PATH.exists() else False:
        return "PRODUCTION_KEYED", fp
    return "TEST_KEYED", fp


def resolve_key() -> tuple[bytes | None, str]:
    """Return (key, status). Never returns a key that lives inside the repo."""
    raw = os.environ.get(KEY_ENV)
    path = Path(raw).expanduser() if raw else DEFAULT_KEY_PATH
    try:
        resolved = path.resolve()
    except OSError:
        return None, f"UNKEYED: key path unresolvable ({path})"
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError:
        pass          # outside the repo, which is what we require
    else:
        return None, (f"REFUSED: key {resolved} is inside the repo. A key stored in "
                      f"writable repo content is forgeable by anyone who can forge the "
                      f"ledger, so it certifies nothing.")
    if not resolved.is_file():
        return None, f"UNKEYED: no key at {resolved} (set {KEY_ENV} or create it)"
    key = resolved.read_bytes().strip()
    if len(key) < 32:
        return None, f"REFUSED: key at {resolved} is shorter than 32 bytes"
    mode, fp = classify_key(resolved, key)
    return key, f"{mode}:{fp}"


def record_mac(record: dict, key: bytes) -> str:
    """HMAC over the canonical record bytes, mac field itself excluded."""
    body = {k: v for k, v in record.items() if k != "mac"}
    return hmac.new(key, serialize(body), hashlib.sha256).hexdigest()
HEAD_PATH = PLUGIN_DIR / "results" / "gate_ledger.head.json"

# The fired chain's own source. Digesting these is what makes a NEUTERED gate
# visible: a commit that guts a checker keeps writing ledger lines, but they
# carry a different gate_source_digest than the reviewed gate did.
GATE_SOURCES = (
    "hooks/post_receipt_gate.sh",
    "intake_supervisor.py",
    "recompute_veto.py",
    "claimgate.mjs",
    "rules_ratchet.json",
    "three_engine_seal.py",
    "claim_verify.py",
    "ratchet_floor.py",
    "gate_ledger.py",
)

# Kept distinct on purpose. PARKED (blocks admission) and ADMITTED_FLOOR_PARKED
# (admitted, one floor key parked) are different states and must not collapse.
DISPOSITIONS = (
    "PASS",                    # exit 0, every stage clean
    "ADMITTED_PENDING_DEPTH",  # claim_verify exit 3 — admitted, deeper audit owed
    "ADMITTED_FLOOR_PARKED",   # admitted, but ratchet_floor parked an unknown key
    "BLOCKED",                 # exit 1 at any stage
    "PARKED",                  # intake exit 3 — blocks admission, not a rejection
    "INFRA_ERROR",             # exit 2 — the gate's own tooling broke
    "INCOMPLETE",              # trap fired before any stage reported (killed run)
)
ADMITTING = ("PASS", "ADMITTED_PENDING_DEPTH", "ADMITTED_FLOOR_PARKED")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gate_source_manifest() -> tuple[str, dict[str, str]]:
    """(aggregate digest, {relpath: short digest}). An absent file digests as
    MISSING rather than being skipped, so deleting a checker moves the digest."""
    per_file: dict[str, str] = {}
    lines = []
    for rel in GATE_SOURCES:
        path = PLUGIN_DIR / rel
        try:
            full = sha256_bytes(path.read_bytes())
        except OSError:
            full = "MISSING"
        per_file[rel] = full if full == "MISSING" else full[:12]
        lines.append(f"{rel}:{full}")
    return sha256_bytes("\n".join(lines).encode()), per_file


def serialize(record: dict) -> bytes:
    """Canonical one-line encoding. Deterministic, so the chain hash of a line is
    reproducible from the parsed record."""
    return json.dumps(record, sort_keys=True, separators=(",", ":")).encode()


def read_lines(path: Path) -> list[bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        return []
    return [ln for ln in raw.split(b"\n") if ln.strip()]


def _parse_stages(spec: str) -> list[dict]:
    """"intake=0,tier0=1" -> [{"stage":"intake","exit":0},{"stage":"tier0","exit":1}]"""
    out = []
    for chunk in (spec or "").split(","):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        name, _, value = chunk.rpartition("=")
        try:
            out.append({"stage": name, "exit": int(value)})
        except ValueError:
            out.append({"stage": name, "exit": None})
    return out


def append(receipt: str, gate_exit: int, disposition: str,
           blocking_stage: str = "", stages: str = "",
           ledger_path: Path = LEDGER_PATH, head_path: Path = HEAD_PATH) -> dict:
    """Append exactly one chained line. Returns the written record.

    Holds an exclusive flock across read-tail -> append -> head-write, so two
    concurrent gate runs cannot both chain onto the same predecessor and fork
    the ledger.
    """
    if disposition not in DISPOSITIONS:
        raise ValueError(f"unknown disposition {disposition!r}; allowed {DISPOSITIONS}")
    ledger_path.parent.mkdir(parents=True, exist_ok=True)

    receipt_path = Path(receipt) if receipt else None
    present = bool(receipt_path and receipt_path.is_file())
    # A receipt that could not be read is still a real gate run and is recorded
    # with an empty digest: it binds nothing, so it can never certify anything.
    receipt_digest = sha256_bytes(receipt_path.read_bytes()) if present else ""

    try:
        rel = str(receipt_path.resolve().relative_to(PLUGIN_DIR.parent)) if receipt_path else ""
    except (ValueError, OSError):
        rel = str(receipt_path) if receipt_path else ""

    source_digest, per_file = gate_source_manifest()

    with open(ledger_path, "a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            existing = read_lines(ledger_path)
            prev = sha256_bytes(existing[-1]) if existing else GENESIS
            record = {
                "schema": SCHEMA,
                "seq": len(existing),
                "timestamp": _now(),
                "receipt_path": rel,
                "receipt_sha256": receipt_digest,
                "receipt_present": present,
                "gate_exit": int(gate_exit),
                "disposition": disposition,
                "blocking_stage": blocking_stage or None,
                "stages": _parse_stages(stages),
                "gate_source_digest": source_digest,
                "gate_source": per_file,
                "prev_line_sha256": prev,
            }
            key, key_status = resolve_key()
            # key_mode is written VERBATIM, so TEST_KEYED can never be read as
            # production. mac_status is kept for back-compatibility but is no
            # longer the authority on authentication mode.
            mode, _, fp = key_status.partition(":")
            record["key_mode"] = mode
            record["key_fingerprint"] = fp or None
            record["mac_status"] = mode
            record["mac"] = record_mac(record, key) if key else None
            line = serialize(record)
            handle.seek(0, 2)
            handle.write(line + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
            head_path.write_text(json.dumps({
                "schema": SCHEMA + "/head",
                "count": record["seq"] + 1,
                "last_line_sha256": sha256_bytes(line),
                "updated": record["timestamp"],
                "note": "tail anchor: truncating the ledger now requires editing this file too.",
            }, indent=1) + "\n", encoding="utf-8")
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return record


def verify(ledger_path: Path = LEDGER_PATH,
           head_path: Path | None = None) -> tuple[bool, list[str], list[dict]]:
    """Re-walk the chain. Returns (ok, problems, parsed records).

    PATH ALLOWLIST. There is exactly ONE authoritative ledger, LEDGER_PATH. The
    CLI used to accept any path, so "the ledger verifies" could be produced by
    pointing verify at a clean file written anywhere. Any other path is still
    inspectable, but the result is labelled NON-AUTHORITATIVE and can never stand
    as the gate's record.
    """
    if head_path is None:
        head_path = ledger_path.with_name(ledger_path.stem + ".head.json")
    problems: list[str] = []
    if ledger_path.resolve() != LEDGER_PATH.resolve():
        problems.append(
            f"NON-AUTHORITATIVE PATH — {ledger_path} is not the single allowlisted "
            f"ledger ({LEDGER_PATH}). Inspection only; this cannot certify any run.")
    # A DELETED ledger used to verify clean: read_lines() turns any read error
    # into [], zero records skip every per-record check, and the head anchor is
    # optional, so `rm gate_ledger.jsonl` produced "chain: OK", exit 0. Deleting
    # the evidence is the loudest possible tamper, not the quietest.
    if not ledger_path.exists() and head_path.exists():
        problems.append(
            f"LEDGER DELETED — {ledger_path} is gone but its head anchor survives, and the "
            f"anchor records {head_path.name} appends. Every run it held is unrecoverable.")
    elif not ledger_path.exists():
        # Ledger AND anchor both absent: a virgin checkout and a thorough deletion
        # look identical from inside the repo, so this is stated, not scored. It is
        # the honest floor of an in-repo tamper record: the witness can be deleted
        # with the evidence. An external anchor is what would close it.
        print(f"gate_ledger: no ledger at {ledger_path} and no head anchor — either "
              f"nothing has been gated yet, or both were deleted together. These are "
              f"indistinguishable from inside the repo.", file=sys.stderr)
    elif head_path.exists() and not read_lines(ledger_path):
        problems.append(
            "LEDGER EMPTY but a head anchor exists — the anchor records prior appends, "
            "so the ledger body was truncated to zero lines.")
    lines = read_lines(ledger_path)
    records: list[dict] = []
    for index, raw in enumerate(lines):
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as exc:
            problems.append(f"line {index}: unparseable ({exc})")
            return False, problems, records
        if not isinstance(record, dict):
            problems.append(f"line {index}: not an object")
            return False, problems, records
        expected_prev = GENESIS if index == 0 else sha256_bytes(lines[index - 1])
        if record.get("prev_line_sha256") != expected_prev:
            problems.append(
                f"line {index}: CHAIN BREAK — prev_line_sha256={record.get('prev_line_sha256')} "
                f"but the preceding line's bytes hash to {expected_prev} "
                f"(line {index - 1} was edited, or a line was deleted/inserted)")
        if record.get("seq") != index:
            problems.append(f"line {index}: seq={record.get('seq')} out of order")
        records.append(record)

    # AUTHORSHIP. Walked separately from the chain because they answer different
    # questions: the chain says "unedited since written", the MAC says "written by
    # a holder of the key". A wholly regenerated file passes the first and fails
    # the second, which is exactly the forgery the chain alone cannot see.
    key, key_status = resolve_key()
    # A TEST-keyed record carries a real MAC but NO production authority. Report it
    # as its own state so it is never counted as authenticated provenance.
    test_keyed = [r.get("seq") for r in records if r.get("key_mode") == "TEST_KEYED"]
    legacy = [r.get("seq") for r in records if r.get("mac") and "key_mode" not in r]
    if test_keyed:
        problems.append(f"TEST_KEYED line(s) {test_keyed} — written with an ephemeral/"
                        f"non-default key. The MAC is valid but proves only that the same "
                        f"test key signed it; this is NOT production authentication.")
    if legacy:
        problems.append(f"UNLABELLED-MODE line(s) {legacy} — carry a MAC but predate the "
                        f"key_mode field, so test and production cannot be told apart for "
                        f"them. Treat as TEST_KEYED (fail-safe), never as production.")
    unkeyed = [r.get("seq") for r in records if not r.get("mac")]
    if key:
        bad = [r.get("seq") for r in records
               if r.get("mac") and not hmac.compare_digest(r["mac"], record_mac(r, key))]
        if bad:
            problems.append(f"MAC MISMATCH on line(s) {bad} — these records were not "
                            f"written by a holder of the ledger key (forged or re-keyed)")
        if unkeyed:
            problems.append(f"UNATTRIBUTED line(s) {unkeyed} — no MAC, so consistency is "
                            f"all that can be checked; a key is present, so these predate "
                            f"it or were written without it")
    elif records:
        problems.append(f"CONSISTENT_UNATTRIBUTED — {key_status}. The chain shows the "
                        f"lines are unedited, but NOT that the gate wrote them: anyone "
                        f"who can write the file can regenerate a valid chain and head "
                        f"anchor. This is not 'verified'.")

    if head_path.exists():
        try:
            head = json.loads(head_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"head anchor unreadable ({exc})")
            head = None
        if isinstance(head, dict):
            if head.get("count") != len(lines):
                problems.append(
                    f"head anchor says count={head.get('count')} but the ledger holds "
                    f"{len(lines)} line(s) — TAIL TRUNCATION or an unrecorded append")
            if lines and head.get("last_line_sha256") != sha256_bytes(lines[-1]):
                problems.append("head anchor last_line_sha256 does not match the final line")
    return not problems, problems, records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ClaimGate durable gate ledger")
    sub = parser.add_subparsers(dest="cmd", required=True)

    ap = sub.add_parser("append", help="append one chained gate-run line")
    ap.add_argument("receipt")
    ap.add_argument("--exit", dest="gate_exit", type=int, required=True)
    ap.add_argument("--disposition", required=True)
    ap.add_argument("--blocking-stage", default="")
    ap.add_argument("--stages", default="")

    vp = sub.add_parser("verify", help="re-walk the hash chain")
    vp.add_argument("ledger", nargs="?", type=Path, default=LEDGER_PATH)

    sub.add_parser("source", help="print the gate source manifest and its digest")

    args = parser.parse_args(argv)

    if args.cmd == "source":
        digest, per_file = gate_source_manifest()
        for rel, short in per_file.items():
            print(f"{short:14s} {rel}")
        print(f"gate_source_digest {digest}")
        return 0

    if args.cmd == "verify":
        ok, problems, records = verify(args.ledger)
        print(f"ledger: {args.ledger}")
        print(f"lines: {len(records)}")
        for problem in problems:
            print(f"TAMPER {problem}")
        print("chain: OK" if ok else "chain: BROKEN")
        return 0 if ok else 1

    try:
        record = append(args.receipt, args.gate_exit, args.disposition,
                        args.blocking_stage, args.stages)
    except Exception as exc:  # noqa: BLE001
        print(f"gate_ledger: APPEND FAILED ({exc}) — no durable record written",
              file=sys.stderr)
        return 2
    print(f"gate_ledger: seq={record['seq']} {record['disposition']} "
          f"exit={record['gate_exit']} receipt={record['receipt_sha256'][:12] or 'ABSENT'} "
          f"gate_src={record['gate_source_digest'][:12]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
