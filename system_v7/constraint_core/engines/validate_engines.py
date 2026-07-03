#!/usr/bin/env python3
"""
validate_engines.py -- cross-substrate validation against engines/targets.json.

Usage:
  python3 oracle_targets.py          # (re)generate targets from the numpy oracle
  python3 jax_engine.py              # produce jax_results.json
  julia julia_engine.jl              # produce julia_results.json
  python3 torch_engine.py            # produce torch_results.json
  python3 validate_engines.py        # compare all *_results.json to targets

Exit 0 iff every present substrate matches every target within tolerance AND
the derived invariants hold. A missing substrate file is a SKIP, not a fail.

WHY THIS EXISTS (validity): the numpy sims integrate with RK4; the JAX engine
uses exact superoperator exponentials; Julia uses its own expm; PyTorch its
own. Agreement across four independent numerical routes on the same contract
rules out method-specific artifacts. Disagreement is a FINDING -- report it,
never widen a tolerance to hide it (CLAUDE.md rule 1).
"""
import glob, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    tpath = os.path.join(HERE, "targets.json")
    if not os.path.exists(tpath):
        print("targets.json missing -- run oracle_targets.py first"); sys.exit(1)
    T = json.load(open(tpath))
    tol = T["tolerances"]
    tkey = {(s["t"], s["op"]): s for s in T["stages"]}
    tterr = {tr["t"]: tr for tr in T["terrains"]}
    any_fail, n_checked = False, 0
    for rf in sorted(glob.glob(os.path.join(HERE, "*_results.json"))):
        R = json.load(open(rf)); name = R.get("substrate", os.path.basename(rf))
        fails = []
        for s in R["stages"]:
            t = tkey[(s["t"], s["op"])]
            for k, tl in (("bloch_down", tol["bloch_abs"]), ("bloch_up", tol["bloch_abs"])):
                d = float(np.max(np.abs(np.array(s[k]) - np.array(t[k]))))
                if d > tl:
                    fails.append(f"t{s['t']}:{s['op']} {k} off by {d:.2e} (tol {tl})")
            if abs(s["order_gap"] - t["order_gap"]) > tol["order_gap_abs"]:
                fails.append(f"t{s['t']}:{s['op']} order_gap {s['order_gap']:.6f} "
                             f"vs {t['order_gap']:.6f}")
        for tr in R.get("terrains", []):
            tt = tterr[tr["t"]]
            if tr["nonunital"] != tt["nonunital"]:
                fails.append(f"t{tr['t']} nonunital bit {tr['nonunital']} != {tt['nonunital']}")
            if abs(tr["fixed_z"] - tt["fixed_z"]) > tol["fixed_z_abs"]:
                fails.append(f"t{tr['t']} fixed_z {tr['fixed_z']:.5f} vs {tt['fixed_z']:.5f}")
        # substrate-side invariants recomputed (not trusted from the file)
        M = np.array([s["bloch_down"] + s["bloch_up"] for s in R["stages"]])
        dmin = min(float(np.linalg.norm(M[i] - M[j]))
                   for i in range(len(M)) for j in range(i + 1, len(M)))
        if len(R["stages"]) != 16:
            fails.append(f"{len(R['stages'])} stages != 16")
        if dmin < 0.9 * T["invariants"]["min_pairwise_dist"]:
            fails.append(f"min pairwise dist {dmin:.4f} < oracle {T['invariants']['min_pairwise_dist']:.4f}")
        if not all(s["order_gap"] > 1e-6 for s in R["stages"]):
            fails.append("order gap collapsed (N01 violation)")
        n_checked += 1
        status = "PASS" if not fails else "FAIL"
        if fails: any_fail = True
        print(f"{status} {name}: 16 stages, min dist {dmin:.4f}"
              + ("" if not fails else "\n   " + "\n   ".join(fails[:8])))
    if n_checked == 0:
        print("no *_results.json found -- run at least one engine"); sys.exit(1)
    print(f"\n=== {'GREEN' if not any_fail else 'RED'} "
          f"({n_checked} substrate(s) validated against the oracle contract) ===")
    sys.exit(1 if any_fail else 0)

if __name__ == "__main__":
    main()
