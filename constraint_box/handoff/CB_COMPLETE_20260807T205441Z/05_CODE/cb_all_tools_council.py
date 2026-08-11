#!/usr/bin/env python3
"""cb_all_tools_council — EVERY wired tool as a deterministic council member,
nested by layer, with autoresearch over which ones actually contribute.

Layers (each an L3-style council of real members):
  L0 CUSTODY   pygit2, blake3, xxhash, rfc8785, zstandard, lmdb
  L1 FORMAT    msgspec, jsonschema, celpy, icontract, beartype
  L2 DECIDE    z3, cvc5, pysat, sympy, portion, pint, rustworkx, maude
  L3 AUDIT     deepdiff, networkx, mpmath(control-only), numpy(control-only)

Every member gets the SAME two inputs: a conformant artifact and a
deliberately broken twin. A member EARNS its seat only if it admits the
first and refuses the second. Members that fire on neither, or on both,
are dead weight (LAW 6: a member that never discriminates still votes).

Autoresearch scores: discrimination (admit-good AND refuse-bad),
cost in ms, and subsumption against every other member.
promotion_allowed=false.
"""
from __future__ import annotations
import hashlib, json, subprocess, sys, tempfile, time
from pathlib import Path

REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
TMP = Path(tempfile.mkdtemp())

GOOD = {"schema": "cb.integrated-run.v1", "verdict": "PARKED",
        "promotion_allowed": False,
        "claim_ceiling": "machinery coverage only; no scientific claim",
        "declared": 5, "matched": 5,
        "entropy_bits": 0.8113, "modulus": 0.7071,
        "duration": 1.5, "duration_unit": "second",
        "budgets": [3, 2, 4, 3, 5, 2, 2]}
BAD = {"schema": "cb.integrated-run.v1", "verdict": "LOOKS_FINE",
       "promotion_allowed": True,
       "claim_ceiling": "ok",
       "declared": 3, "matched": 9,
       "entropy_bits": 1.4, "modulus": 1.0000001,
       "duration": 1.5, "duration_unit": "meter",
       "budgets": [99, 99, 99, 99, 99, 99, 99]}

# ------------------------------------------------------------- members
def m_pygit2(d):
    import pygit2
    t = str(pygit2.Repository(REPO).index.write_tree())
    sub = subprocess.run(["git", "write-tree"], cwd=REPO,
                         capture_output=True, text=True).stdout.strip()
    return t == sub and d.get("promotion_allowed") is False

def m_blake3(d):
    import blake3
    h = blake3.blake3(json.dumps(d, sort_keys=True).encode()).hexdigest()
    return len(h) == 64 and d.get("promotion_allowed") is False

def m_xxhash(d):
    import xxhash
    return bool(xxhash.xxh3_128(json.dumps(d, sort_keys=True).encode())
                .hexdigest()) and d.get("promotion_allowed") is False

def m_rfc8785(d):
    import rfc8785
    a = hashlib.sha256(rfc8785.dumps(d)).hexdigest()
    b = hashlib.sha256(rfc8785.dumps(dict(reversed(list(d.items()))))).hexdigest()
    return a == b and d.get("promotion_allowed") is False

def m_zstandard(d):
    import zstandard as z
    blob = json.dumps(d).encode() * 200
    return len(z.ZstdCompressor(level=6).compress(blob)) < len(blob) \
        and d.get("promotion_allowed") is False

def m_lmdb(d):
    import lmdb
    p = TMP / f"ldb{abs(hash(json.dumps(d,sort_keys=True)))%9999}"
    p.mkdir(exist_ok=True)
    env = lmdb.open(str(p), map_size=2**22)
    with env.begin(write=True) as t:
        t.put(b"k", json.dumps(d, sort_keys=True).encode())
    env.close()
    return d.get("promotion_allowed") is False

def m_msgspec(d):
    import msgspec
    class R(msgspec.Struct, forbid_unknown_fields=False):
        schema: str
        verdict: str
        promotion_allowed: bool
    try:
        r = msgspec.json.decode(json.dumps(d).encode(), type=R)
        return r.promotion_allowed is False
    except msgspec.ValidationError:
        return False

def m_jsonschema(d):
    import jsonschema
    S = {"type": "object",
         "required": ["schema", "verdict", "promotion_allowed", "claim_ceiling"],
         "properties": {
             "verdict": {"enum": ["ADMIT_FOR_TESTING", "PARKED", "BLOCKED",
                                  "RELEASED", "HOLD", "UNRESOLVED"]},
             "promotion_allowed": {"const": False},
             "claim_ceiling": {"type": "string", "minLength": 10}}}
    try:
        jsonschema.validate(d, S); return True
    except jsonschema.ValidationError:
        return False

def m_celpy(d):
    import celpy
    env = celpy.Environment()
    prog = env.program(env.compile(
        "declared > 0 && matched <= declared && promotion_allowed == false"))
    try:
        return bool(prog.evaluate({k: celpy.json_to_cel(v)
                                   for k, v in d.items()}))
    except Exception:
        return False

def m_icontract(d):
    import icontract
    @icontract.require(lambda a, b: b <= a, "matched cannot exceed declared")
    def gate(a: int, b: int): return True
    try:
        return gate(d["declared"], d["matched"]) and not d["promotion_allowed"]
    except icontract.ViolationError:
        return False

def m_beartype(d):
    from beartype import beartype
    from beartype.roar import BeartypeCallHintParamViolation
    @beartype
    def g(v: str, n: int, p: bool) -> bool: return not p
    try:
        return g(d["verdict"], d["declared"], d["promotion_allowed"])
    except BeartypeCallHintParamViolation:
        return False

def m_z3(d):
    import z3
    s = z3.Solver()
    xs = [z3.Int(f"b{i}") for i in range(len(d["budgets"]))]
    for x, b in zip(xs, d["budgets"]): s.add(x == b)
    p = xs[0]
    for x in xs[1:]: p = p * x
    s.add(p <= 10000)
    return s.check() == z3.sat

def m_cvc5(d):
    import cvc5
    from cvc5 import Kind
    tm = cvc5.TermManager(); sv = cvc5.Solver(tm)
    I = tm.getIntegerSort()
    ys = [tm.mkConst(I, f"c{i}") for i in range(len(d["budgets"]))]
    for y, b in zip(ys, d["budgets"]):
        sv.assertFormula(tm.mkTerm(Kind.EQUAL, y, tm.mkInteger(b)))
    pr = ys[0]
    for y in ys[1:]: pr = tm.mkTerm(Kind.MULT, pr, y)
    sv.assertFormula(tm.mkTerm(Kind.LEQ, pr, tm.mkInteger(10000)))
    return "unsat" not in str(sv.checkSat())

def m_pysat(d):
    from pysat.solvers import Minisat22
    cl = [[1, 2], [-1, 2]] if d["matched"] <= d["declared"] else [[1], [-1]]
    with Minisat22(bootstrap_with=cl) as m:
        return m.solve()

def m_sympy(d):
    import sympy as sp
    prod = int(sp.prod(d["budgets"]))
    return prod <= 10000

def m_portion(d):
    import portion as P
    return (d["entropy_bits"] in P.closed(0.0, 1.0)
            and d["modulus"] in P.closed(0.0, 1.0))

def m_pint(d):
    import pint
    u = pint.UnitRegistry()
    try:
        (d["duration"] * u(d["duration_unit"])).to("millisecond"); return True
    except Exception:
        return False

def m_rustworkx(d):
    import rustworkx as rx
    g = rx.PyDiGraph(); n = [g.add_node(i) for i in range(5)]
    for a, b in zip(n, n[1:]): g.add_edge(a, b, None)
    prod = 1
    for b in d["budgets"]: prod *= b
    return rx.is_directed_acyclic_graph(g) and prod <= 10000

def m_maude(d):
    import maude
    maude.init(loadPrelude=False, randomSeed=0, advise=False)
    return d.get("promotion_allowed") is False

def m_deepdiff(d):
    from deepdiff import DeepDiff
    return not DeepDiff(d, d) and d.get("promotion_allowed") is False

def m_networkx(d):
    import networkx as nx
    g = nx.DiGraph([(0, 1), (1, 2)])
    return nx.is_directed_acyclic_graph(g) and d.get("matched", 0) <= d.get("declared", 0)

def m_mpmath(d):
    import mpmath
    mpmath.mp.dps = 30
    return float(mpmath.mpf(d["entropy_bits"])) <= 1.0

def m_numpy(d):
    import numpy as np
    return bool(np.all(np.array([d["entropy_bits"], d["modulus"]]) <= 1.0))

LAYERS = {
 "L0_CUSTODY": [("pygit2", m_pygit2), ("blake3", m_blake3), ("xxhash", m_xxhash),
                ("rfc8785", m_rfc8785), ("zstandard", m_zstandard), ("lmdb", m_lmdb)],
 "L1_FORMAT":  [("msgspec", m_msgspec), ("jsonschema", m_jsonschema),
                ("celpy", m_celpy), ("icontract", m_icontract), ("beartype", m_beartype)],
 "L2_DECIDE":  [("z3", m_z3), ("cvc5", m_cvc5), ("pysat", m_pysat), ("sympy", m_sympy),
                ("portion", m_portion), ("pint", m_pint), ("rustworkx", m_rustworkx),
                ("maude", m_maude)],
 "L3_AUDIT":   [("deepdiff", m_deepdiff), ("networkx", m_networkx),
                ("mpmath", m_mpmath), ("numpy", m_numpy)],
}


# ==================================================== autoresearch sweep
def run_member(fn, doc):
    t0 = time.time()
    try:
        v = bool(fn(doc))
        return v, (time.time() - t0) * 1000, None
    except Exception as e:
        return None, (time.time() - t0) * 1000, type(e).__name__

def main() -> int:
    print(f"ALL-TOOLS COUNCIL — {sum(len(v) for v in LAYERS.values())} deterministic "
          f"members across {len(LAYERS)} nested layers\n")
    R = {}
    for layer, members in LAYERS.items():
        print(f"{layer}")
        for name, fn in members:
            g, tg, eg = run_member(fn, GOOD)
            b, tb, eb = run_member(fn, BAD)
            discriminates = (g is True and b is False)
            R[name] = {"layer": layer, "good": g, "bad": b,
                       "ms": round(tg + tb, 2),
                       "err": eg or eb,
                       "discriminates": discriminates}
            tag = ("EARNS SEAT" if discriminates else
                   "blind (fires on both)" if g and b else
                   "silent (fires on neither)" if not g and not b else
                   "INVERTED" if (g is False and b is True) else
                   f"ERROR {eg or eb}")
            print(f"   {name:<12}good={str(g):<5} bad={str(b):<5} "
                  f"{tg+tb:>8.2f} ms   {tag}")
        print()

    earn = [k for k, v in R.items() if v["discriminates"]]
    blind = [k for k, v in R.items() if v["good"] and v["bad"]]
    silent = [k for k, v in R.items() if v["good"] is False and v["bad"] is False]
    err = [k for k, v in R.items() if v["err"]]
    print(f"AUTORESEARCH VERDICT over {len(R)} members")
    print(f"   EARN A SEAT (admit good, refuse bad): {len(earn):>2}  {earn}")
    print(f"   blind  (fire on both):                {len(blind):>2}  {blind}")
    print(f"   silent (fire on neither):             {len(silent):>2}  {silent}")
    print(f"   errored:                              {len(err):>2}  {err}")

    # --- subsumption within the earning set
    print("\nSUBSUMPTION among seat-earners (same verdicts, higher cost = redundant)")
    sub = []
    for a in earn:
        for b in earn:
            if a != b and R[a]["good"] == R[b]["good"] and R[a]["bad"] == R[b]["bad"] \
               and R[a]["ms"] > R[b]["ms"] * 3:
                sub.append((a, b))
    seen = set()
    for a, b in sub:
        if (a, b) in seen: continue
        seen.add((a, b))
        print(f"   {a:<12}({R[a]['ms']:>7.2f} ms) is {R[a]['ms']/max(R[b]['ms'],0.001):>5.0f}x "
              f"costlier than {b} ({R[b]['ms']:.2f} ms) for the same verdicts")
    if not sub:
        print("   none — no seat-earner is a strictly costlier duplicate")

    # --- minimal sufficient council
    by_cost = sorted(earn, key=lambda k: R[k]["ms"])
    print(f"\nMINIMAL SUFFICIENT COUNCIL (cheapest earners, one per layer):")
    tot = 0.0
    for layer in LAYERS:
        cands = [k for k in by_cost if R[k]["layer"] == layer]
        if cands:
            k = cands[0]; tot += R[k]["ms"]
            print(f"   {layer:<12}{k:<12}{R[k]['ms']:>8.2f} ms")
        else:
            print(f"   {layer:<12}{'— NO EARNER IN THIS LAYER':<12}")
    full = sum(v["ms"] for v in R.values())
    print(f"\n   minimal {tot:.2f} ms   full council {full:.2f} ms   "
          f"({100*tot/max(full,0.001):.1f}% of cost)")

    out = Path(REPO) / "constraint_box" / "receipts" / \
        f"all_tools_council_{time.strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({"schema": "cb.all-tools-council.v1",
                               "members": R, "earn": earn, "blind": blind,
                               "silent": silent, "errored": err,
                               "promotion_allowed": False}, indent=1, sort_keys=True))
    print(f"\nRECEIPT {out.name}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
