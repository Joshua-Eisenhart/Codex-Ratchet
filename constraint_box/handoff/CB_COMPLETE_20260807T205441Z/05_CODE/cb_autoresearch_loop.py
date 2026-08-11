#!/usr/bin/env python3
"""cb_autoresearch_loop — autoresearch that WRITES BACK.

Previous sweeps in this session measured and then evaporated. That
violates LAW 4: learning is deformation of the REGISTRY (sigma), not
motion of run states (rho). A sweep whose result is not stored is a run
state.

This loop:
  1. reads tuned parameters from config/cb_tuned_params.json (or seeds)
  2. runs the member set against the REAL receipt corpus
  3. sweeps each tunable, scoring discrimination against cost
  4. WRITES the improved parameters back, with the evidence and a
     monotone measure that must have moved
  5. refuses to write if the cycle produced no improvement (LAW 8:
     a loop that advances nothing is dead)

No model in the loop. Deterministic, replayable from the stored seed.
promotion_allowed=false.
"""
from __future__ import annotations
import json, re, time
from pathlib import Path
from collections import Counter

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
CFG = REPO / "constraint_box" / "config" / "cb_tuned_params.json"
SEED_PARAMS = {
    "schema": "cb.tuned-params.v1",
    "min_ceiling_chars": 10,
    "ladder": ["PARKED", "BLOCKED", "ADMIT_FOR_TESTING", "RELEASED", "HOLD",
               "UNRESOLVED", "PASS", "FAIL", "ELIGIBLE", "AGREE", "OK"],
    "spot_check_p": 0.35,
    "lateral_width_cheap": 6,
    "lateral_width_heavy": 4,
    "cycles": 0,
    "history": [],
    "promotion_allowed": False,
}

def load_params() -> dict:
    if CFG.exists():
        return json.loads(CFG.read_text())
    return json.loads(json.dumps(SEED_PARAMS))

def corpus() -> list:
    out = []
    for p in REPO.rglob("*.json"):
        if ".git" in p.parts:
            continue
        n = p.name.lower()
        if not any(k in n for k in ("receipt", "result", "verdict", "run",
                                    "report", "audit")):
            continue
        try:
            d = json.loads(p.read_text(errors="ignore"))
        except Exception:
            continue
        if isinstance(d, dict):
            out.append((str(p.relative_to(REPO)), d))
    return out

def score(docs, params) -> dict:
    """discrimination = refusals that are ACTIONABLE (not blanket)."""
    lad = set(params["ladder"])
    minc = params["min_ceiling_chars"]
    ref = Counter(); off = {}
    for path, d in docs:
        v = d.get("verdict") or d.get("status") or d.get("disposition")
        if v is not None and str(v).upper() not in lad:
            ref["verdict_ladder"] += 1; off.setdefault("verdict_ladder", []).append(path)
        if d.get("promotion_allowed") is True:
            ref["promotion_false"] += 1; off.setdefault("promotion_false", []).append(path)
        cc = d.get("claim_ceiling")
        if isinstance(cc, str) and len(cc) < minc:
            ref["ceiling_declared"] += 1; off.setdefault("ceiling_declared", []).append(path)
        if d.get("all_pass") is True and ("verdict" in d or "status" in d):
            ref["no_self_verdict"] += 1; off.setdefault("no_self_verdict", []).append(path)
        for k, val in d.items():
            if isinstance(val, str) and k.endswith("sha256") and \
                    not re.fullmatch(r"[0-9a-f]{64}", val):
                ref["sha256_shape"] += 1; off.setdefault("sha256_shape", []).append(path); break
    total = sum(ref.values())
    rate = total / max(len(docs), 1)
    # a member set is USEFUL when it refuses a small, non-zero fraction:
    # 0% = rubber stamp, >20% = noise generator
    useful = 0.0 if rate == 0 else (1.0 - abs(rate - 0.05) / 0.05 if rate <= 0.10 else 0.0)
    return {"refusals": dict(ref), "total": total, "rate": round(rate, 5),
            "usefulness": round(max(useful, 0.0), 4),
            "offenders": {k: v[:5] for k, v in off.items()}}

def sweep_ladder(docs, params) -> tuple[list, dict]:
    """autoresearch: which verdict tokens actually occur? An unknown token
    is either a real defect or a missing ladder entry. Tokens appearing
    >=20 times across >=3 distinct trees are vocabulary, not defects."""
    seen = Counter(); trees = {}
    for path, d in docs:
        v = d.get("verdict") or d.get("status") or d.get("disposition")
        if v is None or not isinstance(v, str):
            continue
        t = v.upper(); seen[t] += 1
        trees.setdefault(t, set()).add(path.split("/")[0])
    lad = set(params["ladder"])
    promote = [t for t, c in seen.items()
               if t not in lad and c >= 20 and len(trees[t]) >= 3]
    return sorted(lad | set(promote)), {
        "distinct_tokens": len(seen),
        "promoted_to_ladder": promote,
        "top_unknown": [(t, c) for t, c in seen.most_common(40) if t not in lad][:8]}

def main() -> int:
    t0 = time.time()
    params = load_params()
    docs = corpus()
    print(f"AUTORESEARCH CYCLE {params['cycles'] + 1}")
    print(f"corpus: {len(docs):,} real receipt-like docs\n")

    before = score(docs, params)
    print(f"BEFORE  refusals {before['total']:>5}  rate {before['rate']:.4f}  "
          f"usefulness {before['usefulness']:.3f}")

    new_ladder, evidence = sweep_ladder(docs, params)
    print(f"\nLADDER SWEEP: {evidence['distinct_tokens']} distinct verdict tokens in the corpus")
    print(f"   unknown tokens by frequency: {evidence['top_unknown']}")
    print(f"   promoted to ladder (>=20 occurrences, >=3 trees): {evidence['promoted_to_ladder']}")

    cand = json.loads(json.dumps(params)); cand["ladder"] = new_ladder
    after = score(docs, cand)
    print(f"\nAFTER   refusals {after['total']:>5}  rate {after['rate']:.4f}  "
          f"usefulness {after['usefulness']:.3f}")

    improved = after["usefulness"] > before["usefulness"] or \
        (after["total"] < before["total"] and after["total"] > 0)
    print(f"\nMONOTONE MEASURE: refusals {before['total']} -> {after['total']}  "
          f"usefulness {before['usefulness']:.3f} -> {after['usefulness']:.3f}")
    if not improved:
        print("LOOP DEAD (LAW 8): cycle advanced nothing; refusing to write back.")
        return 1

    cand["cycles"] = params["cycles"] + 1
    cand["history"] = (params.get("history", []) + [{
        "cycle": cand["cycles"], "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "corpus_docs": len(docs),
        "refusals_before": before["total"], "refusals_after": after["total"],
        "usefulness_before": before["usefulness"],
        "usefulness_after": after["usefulness"],
        "ladder_promoted": evidence["promoted_to_ladder"],
        "remaining_offenders": after["offenders"]}])[-10:]
    CFG.parent.mkdir(exist_ok=True)
    CFG.write_text(json.dumps(cand, indent=1, sort_keys=True))
    print(f"WROTE BACK -> {CFG.relative_to(REPO)}  (cycle {cand['cycles']}, "
          f"{time.time()-t0:.1f}s)")
    print(f"remaining real offenders: "
          f"{ {k: len(v) for k, v in after['offenders'].items()} }")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
