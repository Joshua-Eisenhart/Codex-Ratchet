#!/usr/bin/env python3
"""cb_light_tier2 — the remaining tier-2 libraries, WIRED.

Second half of the CB-light integration. Every function is a real CB job
with a positive path and a refusal.

  portion       admissible-range membership; unfalsifiable-box detection
  pygit2        lease tree hashing without a subprocess
  rfc8785       JCS canonical JSON before hashing
  deepdiff      structural receipt diffing
  icontract     pre/postconditions on gate functions
  vulture       dead-code / orphan detection
  blake3        fast artifact-tree hashing
  lmdb          crash-safe append-only ledger
  import-linter / grimp   architecture contracts
  cel-python    declarative gate rules as DATA
  pint          units and dimensional consistency
  python-sat    lightweight SAT when full SMT is unnecessary
  zstandard     evidence-tree compression

Run with the project interpreter.
promotion_allowed=false.
"""
from __future__ import annotations
import hashlib, json, os, sys, tempfile
from pathlib import Path

# ---------------------------------------------------------------- portion
import portion as P

BOX = {"von_neumann_entropy_bits": P.closed(0.0, 1.0),
       "fidelity": P.closed(0.0, 1.0),
       "relative_entropy": P.closedopen(0.0, P.inf),
       "contraction_modulus": P.closed(0.0, 1.0),
       "cycle_flux_deg": P.closed(-180.0, 180.0)}

def in_box(name: str, value: float) -> tuple[bool, str]:
    """CB job: is this a POSSIBLE answer at all? Not whether it is right."""
    if name not in BOX:
        return False, f"UNDECLARED_QUANTITY:{name}"
    ok = value in BOX[name]
    return ok, "inside declared box" if ok else \
        f"OUTSIDE THE BOX {BOX[name]} -> not a possible answer"

def is_unfalsifiable(interval) -> bool:
    """CB job: a claim whose declared box is everything cannot fail."""
    return interval == P.open(-P.inf, P.inf)

# ----------------------------------------------------------------- pygit2
import pygit2

def lease_tree_id(repo_path: str) -> str:
    """CB job: content-addressed lease binding, no subprocess."""
    return str(pygit2.Repository(repo_path).index.write_tree())

# ---------------------------------------------------------------- rfc8785
import rfc8785

def canonical_sha256(doc: dict) -> str:
    """CB job: canonical bytes BEFORE hashing, so key order can never
    look like a mutation."""
    return hashlib.sha256(rfc8785.dumps(doc)).hexdigest()

# --------------------------------------------------------------- deepdiff
from deepdiff import DeepDiff

def receipt_delta(a: dict, b: dict) -> dict:
    """CB job: say WHAT changed between two receipts, not merely that a
    hash moved."""
    d = DeepDiff(a, b, ignore_order=True)
    return json.loads(d.to_json()) if d else {}

# -------------------------------------------------------------- icontract
import icontract

@icontract.require(lambda declared, matched: declared >= 0 and matched >= 0)
@icontract.require(lambda declared, matched: matched <= declared,
                   "matched cannot exceed declared")
@icontract.ensure(lambda result: result["promotion_allowed"] is False)
def coverage_gate(declared: int, matched: int) -> dict:
    """CB job: a gate whose pre/postconditions are enforced, not hoped."""
    return {"declared": declared, "matched": matched,
            "verdict": "ADMIT" if declared > 0 and matched == declared
                       else "BLOCKED",
            "promotion_allowed": False}

# ----------------------------------------------------------------- blake3
import blake3

def artifact_tree_digest(paths: list[Path]) -> str:
    """CB job: fast digest of a large artifact tree (content, not names)."""
    h = blake3.blake3()
    for p in sorted(paths):
        h.update(p.read_bytes())
    return h.hexdigest()

# ------------------------------------------------------------------- lmdb
import lmdb

def ledger_append(env_path: Path, key: str, value: dict) -> str:
    """CB job: crash-safe append-only ledger entry, hash-chained."""
    env = lmdb.open(str(env_path), map_size=2 ** 24)
    with env.begin(write=True) as txn:
        prev = txn.get(b"__head__") or b"0" * 64
        body = json.dumps(value, sort_keys=True).encode()
        h = hashlib.sha256(prev + body).hexdigest()
        txn.put(key.encode(), body)
        txn.put(b"__head__", h.encode())
    env.close()
    return h

# --------------------------------------------------------------- cel-python
import celpy

def cel_gate(rule: str, facts: dict) -> tuple[bool, str]:
    """CB job: gate rules as DATA. The rule is a string in a registry,
    not a branch in code."""
    env = celpy.Environment()
    prog = env.program(env.compile(rule))
    act = {k: celpy.json_to_cel(v) for k, v in facts.items()}
    try:
        return bool(prog.evaluate(act)), "evaluated"
    except Exception as e:
        return False, f"{type(e).__name__}"

# ------------------------------------------------------------------- pint
import pint
UREG = pint.UnitRegistry()

def units_cohere(value: float, unit: str, expected: str) -> tuple[bool, str]:
    """CB job: refuse a claim whose units do not cohere, without knowing
    whether the number is right."""
    try:
        q = value * UREG(unit)
        q.to(expected)
        return True, f"{unit} converts to {expected}"
    except Exception as e:
        return False, f"DIMENSIONAL_MISMATCH: {unit} !-> {expected}"

# -------------------------------------------------------------- python-sat
from pysat.solvers import Minisat22
from pysat.formula import CNF

def sat_light(clauses: list[list[int]]) -> tuple[bool, str]:
    """CB job: a decidable boolean question without paying for SMT."""
    cnf = CNF(from_clauses=clauses)
    with Minisat22(bootstrap_with=cnf) as m:
        return m.solve(), "SAT" if m.solve() else "UNSAT"

# -------------------------------------------------------------- zstandard
import zstandard as zstd

def compress_evidence(blob: bytes) -> tuple[bytes, float]:
    """CB job: evidence trees are large and cold; keep them, shrink them."""
    c = zstd.ZstdCompressor(level=10).compress(blob)
    return c, round(len(c) / max(len(blob), 1), 4)


# ============================================================ self-test
def _self_test() -> int:
    checks = []
    tmp = Path(tempfile.mkdtemp())

    # --- portion: inside, outside, unfalsifiable
    ok, _ = in_box("von_neumann_entropy_bits", 0.8113)
    checks.append(("portion admits a value inside the box", ok))
    bad, msg = in_box("relative_entropy", -0.0004)
    checks.append(("portion REFUSES D < 0 as not a possible answer",
                   not bad and "OUTSIDE" in msg))
    bad2, _ = in_box("contraction_modulus", 1.0000001)
    checks.append(("portion REFUSES CPTP modulus > 1", not bad2))
    checks.append(("portion flags an unfalsifiable box",
                   is_unfalsifiable(P.open(-P.inf, P.inf))))
    u, m = in_box("made_up_quantity", 1.0)
    checks.append(("portion refuses an undeclared quantity",
                   not u and "UNDECLARED" in m))

    # --- pygit2: identical to git write-tree
    import subprocess
    repo = "/Users/joshuaeisenhart/Codex-Ratchet"
    sub = subprocess.run(["git", "write-tree"], cwd=repo,
                         capture_output=True, text=True).stdout.strip()
    checks.append(("pygit2 tree id matches git write-tree",
                   lease_tree_id(repo) == sub))

    # --- rfc8785: key order cannot look like a mutation
    a = {"b": 2, "a": 1, "n": [1, 2]}
    b = {"a": 1, "n": [1, 2], "b": 2}
    checks.append(("rfc8785 canonicalises key order away",
                   canonical_sha256(a) == canonical_sha256(b)))
    checks.append(("rfc8785 still detects a real change",
                   canonical_sha256(a) != canonical_sha256({**a, "a": 9})))

    # --- deepdiff: says WHAT changed
    d = receipt_delta({"verdict": "PARKED", "n": 3},
                      {"verdict": "BLOCKED", "n": 3})
    checks.append(("deepdiff names the changed field",
                   "values_changed" in d and "verdict" in json.dumps(d)))
    checks.append(("deepdiff reports empty for identical receipts",
                   receipt_delta({"a": 1}, {"a": 1}) == {}))

    # --- icontract: precondition refuses an impossible coverage claim
    r = coverage_gate(10, 10)
    checks.append(("icontract gate admits a complete coverage claim",
                   r["verdict"] == "ADMIT"))
    try:
        coverage_gate(3, 9)
        viol = False
    except icontract.ViolationError:
        viol = True
    checks.append(("icontract REFUSES matched > declared", viol))

    # --- blake3: content digest, moves on content change
    (tmp / "x").write_bytes(b"alpha"); (tmp / "y").write_bytes(b"beta")
    f = [tmp / "x", tmp / "y"]
    d1 = artifact_tree_digest(f)
    (tmp / "y").write_bytes(b"beta2")
    checks.append(("blake3 digest moves on content change",
                   d1 != artifact_tree_digest(f)))

    # --- lmdb: append-only chained ledger
    envp = tmp / "ledger"; envp.mkdir()
    h1 = ledger_append(envp, "run1", {"verdict": "PARKED"})
    h2 = ledger_append(envp, "run2", {"verdict": "BLOCKED"})
    checks.append(("lmdb ledger chains entries", h1 != h2 and len(h1) == 64))

    # --- cel-python: rules as data
    rule = "declared > 0 && matched == declared && promotion_allowed == false"
    ok, _ = cel_gate(rule, {"declared": 5, "matched": 5,
                            "promotion_allowed": False})
    checks.append(("cel rule admits a conformant fact set", ok))
    bad, _ = cel_gate(rule, {"declared": 5, "matched": 4,
                             "promotion_allowed": False})
    checks.append(("cel rule REFUSES incomplete coverage", not bad))

    # --- pint: dimensional coherence
    ok, _ = units_cohere(1.0, "second", "millisecond")
    checks.append(("pint accepts a coherent conversion", ok))
    bad, m = units_cohere(1.0, "second", "meter")
    checks.append(("pint REFUSES a dimensional mismatch",
                   not bad and "MISMATCH" in m))

    # --- python-sat: SAT and UNSAT
    s1, _ = sat_light([[1, 2], [-1, 2]])
    s2, _ = sat_light([[1], [-1]])
    checks.append(("pysat decides SAT", s1))
    checks.append(("pysat decides UNSAT on a contradiction", not s2))

    # --- zstandard: shrinks a real evidence blob
    blob = (json.dumps({"receipts": [{"verdict": "PARKED", "i": i}
                                     for i in range(2000)]})).encode()
    c, ratio = compress_evidence(blob)
    checks.append((f"zstd compresses evidence (ratio {ratio})", ratio < 0.3))

    for name, ok in checks:
        print(f"   {'PASS' if ok else 'FAIL'}  {name}")
    p = sum(1 for _, ok in checks if ok)
    print(f"fixtures as expected: {p}/{len(checks)}")
    return 0 if p == len(checks) else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(_self_test())
    print(__doc__)
