#!/usr/bin/env python3
"""cb_light_integrations — the eight present-but-unwired libraries, WIRED.

Each function is a real CB job, not a demo. Each has a positive path and
a negative control, because a gate that has only ever passed has not been
exemplified.

  msgspec       strict receipt decode with typed errors
  jsonschema    receipt contract validated at write time
  cryptography  ed25519 receipt signing — the authority seam
  filelock      lease mutual exclusion
  xxhash        manifest-scale digest (NEVER for receipts)
  orjson        fast serialize where canonical form is not required
  beartype      type enforcement at CB boundaries
  mpmath        arbitrary precision, CONTROL_ONLY by the seal

Run with the project interpreter:
  ~/.local/share/codex-ratchet/envs/main/bin/python3 cb_light_integrations.py --self-test
promotion_allowed=false.
"""
from __future__ import annotations
import hashlib, json, os, sys, tempfile, time
from pathlib import Path

CONTROL_ONLY = {"numpy", "scipy", "mpmath"}      # mirrors three_engine_seal

# ---------------------------------------------------------------- msgspec
import msgspec

class Lease(msgspec.Struct, forbid_unknown_fields=True):
    schema: str
    tree_id: str
    lease_sha256: str
    ttl_seconds: float
    issued_at_utc: str
    expires_at_utc: str
    workspace: str
    runners: list
    freshness_rule: str

def decode_lease(raw: bytes) -> tuple[bool, str]:
    """CB job: refuse a lease that is not exactly the declared shape."""
    try:
        msgspec.json.decode(raw, type=Lease)
        return True, "decoded"
    except msgspec.ValidationError as e:
        return False, str(e)

# ------------------------------------------------------------- jsonschema
import jsonschema

RECEIPT_SCHEMA = {
    "type": "object",
    "required": ["schema", "verdict", "promotion_allowed", "claim_ceiling"],
    "additionalProperties": True,
    "properties": {
        "schema": {"type": "string", "pattern": "^cb\\."},
        "verdict": {"enum": ["ADMIT_FOR_TESTING", "PARKED", "BLOCKED",
                             "RELEASED", "HOLD", "UNRESOLVED",
                             "UNVERIFIED_PRODUCER_STATUS"]},
        "promotion_allowed": {"const": False},
        "claim_ceiling": {"type": "string", "minLength": 10},
    },
}

def validate_receipt(doc: dict) -> tuple[bool, str]:
    """CB job: a receipt must declare ONE verdict from the ladder, and
    promotion_allowed must be false. Contract enforced at write time."""
    try:
        jsonschema.validate(doc, RECEIPT_SCHEMA)
        return True, "valid"
    except jsonschema.ValidationError as e:
        return False, e.message

# ----------------------------------------------------------- cryptography
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)
from cryptography.exceptions import InvalidSignature

def sign_receipt(doc: dict, sk: Ed25519PrivateKey) -> dict:
    """CB job: bind a receipt to a key. Canonical bytes, then sign."""
    body = json.dumps({k: v for k, v in doc.items() if k != "signature"},
                      sort_keys=True, separators=(",", ":")).encode()
    return {**doc, "signature": sk.sign(body).hex(),
            "signed_body_sha256": hashlib.sha256(body).hexdigest()}

def verify_receipt(doc: dict, pk: Ed25519PublicKey) -> tuple[bool, str]:
    body = json.dumps({k: v for k, v in doc.items()
                       if k not in ("signature", "signed_body_sha256")},
                      sort_keys=True, separators=(",", ":")).encode()
    try:
        pk.verify(bytes.fromhex(doc["signature"]), body)
        return True, "signature valid"
    except (InvalidSignature, KeyError, ValueError) as e:
        return False, f"{type(e).__name__}"

# --------------------------------------------------------------- filelock
from filelock import FileLock, Timeout

def acquire_lease_lock(tree_id: str, root: Path, timeout: float = 0.2):
    """CB job: one runner per tree. A second holder must be refused."""
    lock = FileLock(str(root / f"{tree_id}.lease.lock"))
    try:
        lock.acquire(timeout=timeout)
        return lock, None
    except Timeout:
        return None, "LEASE_HELD_BY_ANOTHER_RUNNER"

# ----------------------------------------------------------------- xxhash
import xxhash

def manifest_digest(paths: list[Path]) -> str:
    """CB job: fast digest over a manifest. NON-CRYPTOGRAPHIC — manifests
    only. Receipts and artifacts always use sha256."""
    h = xxhash.xxh3_128()
    for p in sorted(paths):
        h.update(str(p).encode())
        h.update(str(p.stat().st_size).encode())
    return h.hexdigest()

# ----------------------------------------------------------------- orjson
import orjson

def fast_dump(doc: dict) -> bytes:
    """CB job: serialize where canonical form is NOT required (logs,
    indexes, caches). Canonical hashing paths must not use this."""
    return orjson.dumps(doc, option=orjson.OPT_SORT_KEYS)

# --------------------------------------------------------------- beartype
from beartype import beartype
from beartype.roar import BeartypeCallHintParamViolation

@beartype
def gate_boundary(verdict: str, evidence_count: int,
                  promotion_allowed: bool) -> dict:
    """CB job: types enforced at the boundary, so a malformed call is a
    typed refusal rather than a silent wrong answer."""
    if promotion_allowed:
        raise ValueError("promotion_allowed must be False at this boundary")
    return {"verdict": verdict, "evidence_count": evidence_count,
            "promotion_allowed": False}

# ----------------------------------------------------------------- mpmath
import mpmath

def control_only_precision(x: str, dps: int = 50) -> dict:
    """CB job: arbitrary precision available, but CONTROL_ONLY. The seal
    refuses it as load_bearing; this function marks itself accordingly."""
    mpmath.mp.dps = dps
    v = mpmath.mpf(x)
    return {"value": str(v), "dps": dps, "library": "mpmath",
            "load_bearing": False,
            "seal_class": "CONTROL_ONLY",
            "note": "computes; may never seal (three_engine_seal)"}

def seal_check(claim: dict) -> tuple[bool, str]:
    """The rule itself: a claim naming a control-only library as
    load_bearing is hard-rejected."""
    lib = claim.get("library", "")
    if claim.get("load_bearing") and lib in CONTROL_ONLY:
        return False, f"BLOCKED: {lib} is CONTROL_ONLY, cannot be load_bearing"
    return True, "ADMIT"


# ============================================================ self-test
def _self_test() -> int:
    checks = []
    tmp = Path(tempfile.mkdtemp())

    # --- msgspec: positive + three refusals
    lease = {"schema": "constraintbox.tree-lease.v1", "tree_id": "056813e7",
             "lease_sha256": "6cc16ccb", "ttl_seconds": 600.0,
             "issued_at_utc": "2026-08-06T21:27:32Z",
             "expires_at_utc": "2026-08-06T21:37:32Z",
             "workspace": "staged-tree-checkout", "runners": ["python3 task.py"],
             "freshness_rule": "fresh iff issued <= now < issued + ttl"}
    ok, _ = decode_lease(json.dumps(lease).encode())
    checks.append(("msgspec accepts a valid lease", ok))
    bad = dict(lease); bad["promotion_allowed"] = True
    r1, m1 = decode_lease(json.dumps(bad).encode())
    checks.append(("msgspec refuses unknown field", not r1 and "unknown field" in m1))
    bad2 = dict(lease); bad2["ttl_seconds"] = "600"
    r2, m2 = decode_lease(json.dumps(bad2).encode())
    checks.append(("msgspec refuses wrong type", not r2 and "float" in m2))
    bad3 = {k: v for k, v in lease.items() if k != "tree_id"}
    r3, m3 = decode_lease(json.dumps(bad3).encode())
    checks.append(("msgspec refuses missing field", not r3 and "tree_id" in m3))

    # --- jsonschema: positive + two refusals
    good = {"schema": "cb.integrated-run.v1", "verdict": "PARKED",
            "promotion_allowed": False,
            "claim_ceiling": "machinery coverage only"}
    ok, _ = validate_receipt(good)
    checks.append(("jsonschema accepts a conformant receipt", ok))
    r, _ = validate_receipt({**good, "promotion_allowed": True})
    checks.append(("jsonschema refuses promotion_allowed=true", not r))
    r, _ = validate_receipt({**good, "verdict": "LOOKS_FINE"})
    checks.append(("jsonschema refuses a verdict off the ladder", not r))

    # --- cryptography: sign, verify, tamper
    sk = Ed25519PrivateKey.generate(); pk = sk.public_key()
    signed = sign_receipt(good, sk)
    ok, _ = verify_receipt(signed, pk)
    checks.append(("cryptography verifies its own signature", ok))
    tampered = {**signed, "verdict": "RELEASED"}
    bad_ok, _ = verify_receipt(tampered, pk)
    checks.append(("cryptography DETECTS a tampered receipt", not bad_ok))

    # --- filelock: hold, then refuse a second holder
    l1, err1 = acquire_lease_lock("056813e7", tmp)
    l2, err2 = acquire_lease_lock("056813e7", tmp)
    checks.append(("filelock grants the first lease holder", l1 is not None))
    checks.append(("filelock REFUSES the second holder",
                   l2 is None and err2 == "LEASE_HELD_BY_ANOTHER_RUNNER"))
    if l1: l1.release()

    # --- xxhash: stable, and changes when the manifest changes
    (tmp / "a.txt").write_text("one"); (tmp / "b.txt").write_text("two")
    files = [tmp / "a.txt", tmp / "b.txt"]
    d1 = manifest_digest(files); d2 = manifest_digest(files)
    (tmp / "b.txt").write_text("two-longer")
    d3 = manifest_digest(files)
    checks.append(("xxhash manifest digest is stable", d1 == d2))
    checks.append(("xxhash digest moves when the manifest moves", d1 != d3))

    # --- orjson: round-trips and sorts
    blob = fast_dump({"b": 2, "a": 1})
    checks.append(("orjson serializes with sorted keys",
                   blob == b'{"a":1,"b":2}'))

    # --- beartype: accepts, then refuses a wrong type
    out = gate_boundary("PARKED", 3, False)
    checks.append(("beartype accepts a well-typed boundary call",
                   out["verdict"] == "PARKED"))
    try:
        gate_boundary("PARKED", "three", False)
        typed = False
    except BeartypeCallHintParamViolation:
        typed = True
    checks.append(("beartype REFUSES a wrong-typed boundary call", typed))

    # --- mpmath: computes, and the seal refuses it as load_bearing
    v = control_only_precision("1/3")
    checks.append(("mpmath computes at declared precision",
                   v["dps"] == 50 and v["seal_class"] == "CONTROL_ONLY"))
    ok, _ = seal_check({**v, "load_bearing": False})
    checks.append(("seal admits mpmath as control", ok))
    bad_ok, msg = seal_check({**v, "load_bearing": True})
    checks.append(("seal BLOCKS mpmath declared load_bearing",
                   not bad_ok and "CONTROL_ONLY" in msg))

    for name, ok in checks:
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
    p = sum(1 for _, ok in checks if ok)
    print(f"fixtures as expected: {p}/{len(checks)}")
    return 0 if p == len(checks) else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    print(__doc__)
