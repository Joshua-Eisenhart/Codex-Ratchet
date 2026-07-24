#!/usr/bin/env python3
"""Run the engine->partition->ratchet bridge over RIVAL orders + NEGATIVE controls.

Uses the repo's real ratchet operator (ratchet_contract/mss.py frontier()), not a
reimplementation. Emits: per-candidate induced partition, basin structure, and the
ratchet's own verdict set (purgatory / branches / antichain).

Nothing here selects a loop order. OD-11 is OPEN; rivals run side by side.
classification: tool_lego_fit_probe   promotion_allowed: false
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "ratchet_contract"))

from engine_as_candidate import EngineCandidate, _GRID, rho_of, state_of  # noqa: E402
from gates import induced_partition, partition_digest, collapsed_demand_edges  # noqa: E402
from mss import frontier  # noqa: E402

# ---- the 4 chart cells of the Type-1 deductive family (FeTi = Ti,Fe operators)
#      each cell = (terrain, operator, Axis-6 arrow), taken from the 16-cell chart
CELL = {
    "Se": ("Se", "Ti", "UP"),     # TiSe  Ti^
    "Ne": ("Ne", "Ti", "DOWN"),   # NeTi  Ti_
    "Ni": ("Ni", "Fe", "DOWN"),   # NiFe  Fe_
    "Si": ("Si", "Fe", "UP"),     # FeSi  Fe^
}
# inductive family (TeFi = Te,Fi operators)
CELL_I = {
    "Se": ("Se", "Fi", "DOWN"),   # SeFi
    "Si": ("Si", "Te", "DOWN"),   # SiTe
    "Ni": ("Ni", "Te", "UP"),     # TeNi
    "Ne": ("Ne", "Fi", "UP"),     # FiNe
}


def sched(order, table=CELL):
    return [table[t] for t in order]


CANDIDATES = [
    # ---- RIVAL ORDERS (all four are live; none selected) -------------------
    EngineCandidate("T1_ded_S_to_N__doc", sched(["Se", "Ne", "Ni", "Si"]), s=+1),
    EngineCandidate("T1_ded_N_to_S__owner_hyp", sched(["Ne", "Ni", "Si", "Se"]), s=+1),
    EngineCandidate("T1_ded_AR01_pack", sched(["Ne", "Si", "Se", "Ni"]), s=+1),
    EngineCandidate("T1_ded_reversed", sched(["Si", "Ni", "Ne", "Se"]), s=+1),
    # ---- CHIRAL PARTNER -----------------------------------------------------
    EngineCandidate("T2_ded_S_to_N__doc", sched(["Se", "Ne", "Ni", "Si"]), s=-1),
    # ---- INDUCTIVE FAMILY (TeFi) -------------------------------------------
    EngineCandidate("T1_ind_S_to_N__doc", sched(["Se", "Si", "Ni", "Ne"], CELL_I), s=+1),
    # ---- NEGATIVE CONTROLS --------------------------------------------------
    # all-commuting z-family: every stage same terrain+op -> order cannot matter
    EngineCandidate("NEG_commuting_z_only", [("Si", "Fe", "UP")] * 4, s=+1),
    # pure unitary: Ne is the only entropy-preserving terrain, Id operator
    EngineCandidate("NEG_unitary_only", [("Ne", "Id", "UP")] * 4, s=+1),
    # one terrain repeated: no terrain structure at all
    EngineCandidate("NEG_single_terrain_Se", [("Se", "Ti", "UP")] * 4, s=+1),
    # terrains with no operator: strips the operator half of every cell
    EngineCandidate("NEG_no_operator", [(t, "Id", "UP") for t in ["Se", "Ne", "Ni", "Si"]], s=+1),
]

# ---- demand set D: pairs that MUST stay distinguished --------------------
# north/south and east/west extremes of the grid. If a candidate's engine merges
# these, it has destroyed a distinction the probe family was required to keep.
D = [
    ((0.6, 0.0, 0.6), (-0.6, 0.0, -0.6)),
    ((0.6, 0.0, -0.6), (-0.6, 0.0, 0.6)),
    ((0.2, 0.0, 0.6), (0.2, 0.0, -0.6)),
    ((0.6, 0.0, 0.2), (-0.6, 0.0, 0.2)),
]
X = list(_GRID)


def basin_report(c):
    """Anti-teleological readout: iterate the loop, group X by limit point."""
    basins = {}
    for x in X:
        a = c.attractor(x)
        basins.setdefault(a, []).append(x)
    return {
        "n_attractors": len(basins),
        "basin_sizes": sorted((len(v) for v in basins.values()), reverse=True),
        "attractors": [list(k) for k in basins],
    }


def rebuild(res):
    """Same roster at a different probe resolution (coarser probe = coarser
    distinguishability = the knob that decides what the ratchet can even see)."""
    out = []
    for c in CANDIDATES:
        out.append(EngineCandidate(c.name, c._schedule, c._s, probe_res=res))
    return out


def sweep():
    """The probe-resolution sweep IS the experiment: at what coarseness do the
    rival orders stop being indistinguishable? Below that, the ratchet has
    nothing to compare -- which is itself a measured negative."""
    rows = {}
    for res in (0, 1, 2):
        roster = rebuild(res)
        idx = {x: i for i, x in enumerate(X)}
        per = {}
        for c in roster:
            pi = induced_partition(c, X)
            collapsed = collapsed_demand_edges(pi, idx, D)
            per[c.name] = {
                "cells": len(set(pi)),
                "digest": partition_digest(pi)[:12],
                "collapsed_demand_edges": len(collapsed),
                "survives_D": len(collapsed) == 0,
            }
        fr = frontier(roster, X, D)
        n_distinct = len({v["digest"] for v in per.values()})
        rows[f"probe_res_{res}"] = {
            "per_candidate": per,
            "distinct_partitions": n_distinct,
            "discriminates": n_distinct > 1,
            "antichain": fr["antichain"],
            "dominated": fr["dominated"],
            "purgatory": [{"candidate": p["candidate"], "failed_at": p["failed_at"]}
                          for p in fr["purgatory"]],
            "branches": [{"members": b["members"], "cells": b["cells"]} for b in fr["branches"]],
        }
    return rows


def main():
    basins = {c.name: basin_report(c) for c in CANDIDATES}
    rows = sweep()

    out = {
        "sim_id": "engine_to_ratchet_bridge_v0",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "claim_ceiling": "engine behaviour compiled to a ratchet partition; rival orders "
                         "compared by coarsening only. No order selected. OD-11 OPEN.",
        "surface": {"X_size": len(X), "D_size": len(D), "probes": list(CANDIDATES[0].probes())},
        "basins_anti_teleological": basins,
        "probe_resolution_sweep": rows,
    }
    Path(HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "engine_to_ratchet_bridge_v0.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
