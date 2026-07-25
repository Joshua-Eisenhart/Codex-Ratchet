#!/usr/bin/env python3
"""RECOMPUTE VETO — the gate re-derives claimed numbers instead of trusting them.

Closes the hole V2 named: the seal checks metadata and re-runs the JAX leg, but
every other accepted number is a producer assertion. The existing tier0 linter
already emits "R5-absent: receipt declares no recompute contract — numbers are
asserted, not re-derivable by this linter". This makes that actionable.

ClaimGate lane. numpy is ALLOWED here by owner rule and is independent of
Codex-Ratchet's science numpy rule: the gate's whole job is veto, and numpy
vetoes. No Julia, no PyTorch, no JAX (CPU-only on this machine, so it buys
nothing for a single recompute).

Two checks:
  1. RECOMPUTE   an explicit `recompute` block, or the implicit pattern of a raw
                 array beside a claimed aggregate, is re-derived and compared.
  2. ASSOCIATIVITY  numba runs an ORDERED sum of the same raw array. If ordered
                 and library-order results differ beyond tolerance, the array is
                 reassociation-sensitive and any parallel reduction over it is a
                 semantic hazard (the bracket-tree problem, GPU or otherwise).

Exit: 0 pass or N/A | 1 VETO | 2 usage.
Nonzero is a policy disposition, never a scientific verdict.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

# NOTE: builtin sum() is COMPENSATED (Neumaier) on py3.12+, numpy is PAIRWISE, and a
# plain loop is ORDERED. These are DIFFERENT OPERATIONS and can disagree wildly:
# [1e16, 1.0, -1e16] -> compensated 1.0, ordered/pairwise 0.0. So the gate computes
# both and refuses to guess which one the producer meant.
AGG = {
    "mean": lambda a: math.fsum(a) / len(a),
    "sum": lambda a: math.fsum(a),
    "min": lambda a: min(a),
    "max": lambda a: max(a),
    "count": lambda a: float(len(a)),
    "n": lambda a: float(len(a)),
}
DEFAULT_TOL = 1e-9


def _numeric_list(v):
    return (isinstance(v, list) and len(v) > 1
            and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in v))


def _walk(obj, path=""):
    if isinstance(obj, dict):
        yield path, obj
        for k, v in obj.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _walk(v, f"{path}[{i}]")


def explicit_contracts(receipt):
    """A receipt may declare its own recompute contract:
       "recompute": [{"raw": "metrics.raw_x", "claim": "metrics.mean_x",
                      "op": "mean", "tol": 1e-9}]"""
    out = []
    for _, node in _walk(receipt):
        rc = node.get("recompute") if isinstance(node, dict) else None
        if isinstance(rc, list):
            out.extend(x for x in rc if isinstance(x, dict))
    return out


def _resolve(receipt, dotted):
    cur = receipt
    for part in dotted.replace("[", ".").replace("]", "").split("."):
        if not part:
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        else:
            return None
    return cur


def implicit_pairs(receipt):
    """Raw array beside a claimed aggregate in the SAME object:
       {"raw_accuracies": [...], "mean_accuracies": 0.9}"""
    found = []
    for path, node in _walk(receipt):
        if not isinstance(node, dict):
            continue
        arrays = {k: v for k, v in node.items() if _numeric_list(v)}
        for akey, arr in arrays.items():
            stem = akey
            for pre in ("raw_", "all_", "values_", "series_"):
                if stem.startswith(pre):
                    stem = stem[len(pre):]
            for ckey, cval in node.items():
                if ckey == akey or not isinstance(cval, (int, float)) or isinstance(cval, bool):
                    continue
                low = ckey.lower()
                for op in AGG:
                    if low.startswith(op) and (stem.lower() in low or low.endswith(stem.lower())):
                        found.append({"raw_inline": arr, "claim_value": float(cval),
                                      "op": op, "where": f"{path}.{ckey}", "tol": DEFAULT_TOL})
                        break
    return found


def ordered_sum_check(arr):
    """COMPENSATED (math.fsum) vs ORDERED (numba plain loop). A difference means
    summation order is load-bearing for this array, so a bare 'sum' claim is
    AMBIGUOUS -- the receipt must say which one it means."""
    try:
        from numba import njit
        import numpy as np

        @njit(cache=False)
        def _ordered(a):
            t = 0.0
            for i in range(a.shape[0]):
                t += a[i]
            return t

        npa = np.asarray(arr, dtype=np.float64)
        return float(_ordered(npa)), math.fsum(arr), True
    except Exception as exc:  # noqa: BLE001
        # ran=False used to mean "no veto", so killing numba deleted this check:
        # PYTHONPATH=<dir with a numba.py that raises> made a receipt claiming
        # sum([1e16,1,-1e16])==1.0 pass, exit 0. A check that cannot run has not
        # passed, so the absence is reported and the caller vetoes.
        return None, None, f"UNAVAILABLE: {exc.__class__.__name__}: {exc}"


def main(argv):
    if len(argv) != 2:
        print("usage: recompute_veto.py <receipt.json>", file=sys.stderr)
        return 2
    p = Path(argv[1])
    if not p.exists():
        print(f"recompute_veto: VETO — artifact absent: {p}", file=sys.stderr)
        return 1
    try:
        receipt = json.loads(p.read_bytes().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"recompute_veto: VETO — unparseable ({e}); failing closed", file=sys.stderr)
        return 1
    # A top-level array returned 0 here unscanned, so wrapping a receipt in [...]
    # skipped every recompute. _walk already descends lists; only the top-level
    # contract lookup assumed a dict, and that is handled below.
    if not isinstance(receipt, (dict, list)):
        return 0

    try:
        import numpy as np  # noqa: F401
    except Exception:
        print("recompute_veto: VETO — numpy unavailable; the gate cannot recompute, "
              "so it fails CLOSED rather than trusting asserted numbers", file=sys.stderr)
        return 1

    jobs = []
    for c in explicit_contracts(receipt):
        raw = _resolve(receipt, c.get("raw", ""))
        claim = _resolve(receipt, c.get("claim", ""))
        if _numeric_list(raw) and isinstance(claim, (int, float)):
            jobs.append({"raw_inline": raw, "claim_value": float(claim),
                         "op": c.get("op", "mean"), "where": c.get("claim"),
                         "tol": float(c.get("tol", DEFAULT_TOL)), "explicit": True})
    jobs += implicit_pairs(receipt)

    if not jobs:
        print("recompute_veto: N/A — no recompute contract and no raw-array/claimed-aggregate "
              "pair found; every number in this receipt is ASSERTED, not re-derived", file=sys.stderr)
        return 0

    vetoes, hazards, checked = [], [], 0
    for j in jobs:
        op = j["op"]
        if op not in AGG:
            # `continue` here meant a receipt could declare op:"median" and get
            # "pass — 0 claimed value(s) re-derived": a PASS message covering
            # nothing. An op this gate cannot compute is unverifiable, so it
            # blocks. Adding the op is the fix; skipping it is not.
            vetoes.append(f"{j['where']}: declared aggregate op {op!r} is not one this "
                          f"gate can recompute (known: {sorted(AGG)}). An unverifiable "
                          f"claim is not a verified one.")
            continue
        arr = j["raw_inline"]
        actual = float(AGG[op](arr))
        checked += 1
        if not math.isclose(actual, j["claim_value"], rel_tol=j["tol"], abs_tol=j["tol"]):
            vetoes.append(f"{j['where']}: claimed {j['claim_value']} but {op} of raw = {actual}")
        o, c, ran = ordered_sum_check(arr)
        if ran is not True:
            vetoes.append(f"{j['where']}: the summation-order check could not run ({ran}). "
                          f"This gate cannot tell an ordered sum from a compensated one for "
                          f"this array, so the claim is unverifiable, not verified.")
        elif o is not None and not math.isclose(o, c, rel_tol=1e-12, abs_tol=1e-12):
            vetoes.append(f"{j['where']}: summation order is LOAD-BEARING for this array "
                          f"(ordered {o} vs compensated {c}); a bare '{op}' claim is ambiguous — "
                          f"the receipt must declare which summation it claims")

    for h in hazards:
        print(f"recompute_veto: HAZARD — {h}", file=sys.stderr)
    if vetoes:
        for v in vetoes:
            print(f"recompute_veto: VETO — {v}", file=sys.stderr)
        return 1
    print(f"recompute_veto: pass — {checked} claimed value(s) re-derived from raw arrays and matched"
          + (f"; {len(hazards)} reassociation hazard(s) flagged" if hazards else ""),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
