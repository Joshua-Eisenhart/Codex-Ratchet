"""
A2 -- fresh-context audit probe against the live ratchet operator.

Claim under test (owner diagram): "when demand or probes do not DISCRIMINATE
the rivals it returns HOLD or plural survivors rather than an MSS verdict."

Adversary: the TOTAL-COLLAPSE candidate. It declares one readout that maps every
state to a single token, so its induced partition has ONE cell -- the coarsest
partition that exists on the surface. Under an EMPTY demand set nothing is
demanded of it. Stage 3 of pairwise_mss compares partitions by coarsening with
no demand to constrain the comparison.

Also measured: whether the flat single-layer comparison is refused as an invalid
comparison unit, and whether requesting nest-level thickening changes anything.

This file MEASURES. Every verdict below is `MssResult.verdict.value` read off a
value the imported operator returned. Nothing here writes a literal verdict.
"""
import json, sys, pathlib, hashlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "ratchet_contract"))
sys.path.insert(0, str(HERE.parent / "probe_lane3"))

from mss import pairwise_mss, frontier, MssVerdict          # noqa: E402
from gates import induced_partition, IDENTITY_GATE          # noqa: E402
import ratchet_mechanics_cases as L3                        # reuse ONLY the scaffolding

X = L3.X
Tower = L3.Tower

# genuine rival: reads the full value -- finest honest partition
genuine  = Tower("genuine_read_value",  declared_probes=["read_value"],
                 reid_ops=["read_value"])
# coarse but still honest: reads warm/cool -- 2 cells
category = Tower("category_warm_cool",  declared_probes=["read_category"],
                 reid_ops=["read_category"])
# adversary: one cell. Everything indistinguishable.
collapse = Tower("total_collapse_one_cell", declared_probes=["read_constant"],
                 reid_ops=["read_constant"])

out = {"probe": "A2_ratchet_under_empty_demand_and_flat_comparison",
       "classification": "tool_lego_fit_probe", "promotion_allowed": False,
       "target_operator": "ratchet_contract/mss.py::pairwise_mss / frontier",
       "observation_surface_X": [list(map(repr, s)) for s in X],
       "declared_verdict_tokens": sorted(v.value for v in MssVerdict),
       "induced_partitions": {}, "cases": {}}

for c in (genuine, category, collapse):
    pi = induced_partition(c, X)
    out["induced_partitions"][c.name] = {
        "partition": list(map(str, pi)), "cells": len(set(pi)),
        "identity_gate_verdict": IDENTITY_GATE(c, X).verdict.value}

D_nonempty = L3.D                       # one demanded distinction
D_empty    = ()                         # nothing demanded

def case(tag, A, B, D, **kw):
    r = pairwise_mss(A, B, X, D, **kw)
    out["cases"][tag] = {
        "A": A.name, "B": B.name, "demand_edges": len(D),
        "kwargs": {k: (v if isinstance(v, (bool, int, str)) else str(v)) for k, v in kw.items()},
        "measured_verdict": r.verdict.value,
        "measured_stage": (r.reasons or {}).get("stage"),
        "measured_reason": (r.reasons or {}).get("reason", "")[:200],
        "cells_A": (r.reasons or {}).get("cells_A"), "cells_B": (r.reasons or {}).get("cells_B"),
    }
    return r

# 1. adversary vs genuine, EMPTY demand
case("C1_collapse_vs_genuine_EMPTY_demand", collapse, genuine, D_empty)
# 2. same pair, one real demanded distinction -- the control
case("C2_collapse_vs_genuine_ONE_demand", collapse, genuine, D_nonempty)
# 3. adversary vs a coarse-but-honest rival, empty demand
case("C3_collapse_vs_category_EMPTY_demand", collapse, category, D_empty)
# 4. empty demand with every thickening layer requested
case("C4_collapse_vs_genuine_EMPTY_demand_all_thickening", collapse, genuine, D_empty,
     thicken_persistence=True, thicken_evolvability=True, thicken_wholenest=True)
# 5. honest pair, empty demand -- does coarseness alone still decide?
case("C5_category_vs_genuine_EMPTY_demand", category, genuine, D_empty)

# 6. frontier() on the empty demand set: who survives?
fr_empty = frontier([collapse, category, genuine], X, D_empty)
fr_real  = frontier([collapse, category, genuine], X, D_nonempty)
def summarise(fr):
    if isinstance(fr, dict):
        return {k: (sorted(map(str, v)) if isinstance(v, (list, tuple, set)) else str(v))
                for k, v in fr.items()}
    return str(fr)
out["frontier_empty_demand"] = summarise(fr_empty)
out["frontier_one_demand"]   = summarise(fr_real)

out["measured_summary"] = {
    "empty_demand_verdict_collapse_vs_genuine":
        out["cases"]["C1_collapse_vs_genuine_EMPTY_demand"]["measured_verdict"],
    "one_demand_verdict_collapse_vs_genuine":
        out["cases"]["C2_collapse_vs_genuine_ONE_demand"]["measured_verdict"],
    "empty_demand_returned_HOLD_or_INCOMPARABLE":
        out["cases"]["C1_collapse_vs_genuine_EMPTY_demand"]["measured_verdict"]
        in ("HOLD", "INCOMPARABLE"),
    "all_thickening_changed_the_empty_demand_verdict":
        out["cases"]["C4_collapse_vs_genuine_EMPTY_demand_all_thickening"]["measured_verdict"]
        != out["cases"]["C1_collapse_vs_genuine_EMPTY_demand"]["measured_verdict"],
}

rp = HERE / "results" / "a2_ratchet_empty_demand.json"
rp.write_text(json.dumps(out, indent=1))
print(json.dumps(out["induced_partitions"], indent=1))
print(json.dumps(out["cases"], indent=1))
print(json.dumps(out["measured_summary"], indent=1))
print("frontier_empty:", json.dumps(out["frontier_empty_demand"])[:400])
print("frontier_one:  ", json.dumps(out["frontier_one_demand"])[:400])
print("sha256", hashlib.sha256(rp.read_bytes()).hexdigest())
