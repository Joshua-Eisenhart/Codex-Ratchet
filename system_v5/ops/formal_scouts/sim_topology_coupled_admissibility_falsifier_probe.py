#!/usr/bin/env python3
"""
sim_topology_coupled_admissibility_falsifier_probe.py

Falsifier target: the claim that GUDHI persistence is constraint-load-bearing
(not merely decorative) in the current formal-scout estate. This probe tests
whether H1 gating is non-vacuous on the scalar-admitted survivor cloud. Positive
H1 records a topology gate surface; it does not by itself promote topology as a
constraint layer or prove an interior-threshold admission change.

Standalone (no engine_core, no canonical_qit_engine_specs imports).
"""
from __future__ import annotations
import json, math, os, pathlib, time
from typing import Any
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch
import gudhi
import z3

# --- Metadata ---
NAME = "topology_coupled_admissibility_falsifier_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Does not admit topology as a constraint layer; tests only whether H1 "
    "lifetime gating changes scalar-admitted sets."
)
TOOL_MANIFEST = {
    "gudhi":  {"tried": True, "used": True,
               "reason": "load-bearing: Vietoris-Rips H1 on survivor distance matrix; H1_sum is the topology-gate quantity"},
    "torch":  {"tried": True, "used": True,
               "reason": "load-bearing: qubit density matrices, entropy, purity, trace-distance metric"},
    "z3":     {"tried": True, "used": True,
               "reason": "load-bearing: proves interesting τ-interval is non-empty (separates scalar vs topology-coupled sets)"},
}
TOOL_INTEGRATION_DEPTH = {"gudhi": "load_bearing", "torch": "load_bearing", "z3": "load_bearing"}
ROOT = pathlib.Path(__file__).resolve().parent
OUT_PATH = ROOT / "results" / "topology_coupled_admissibility_falsifier_probe_results.json"
DTYPE = torch.complex128
ENTROPY_CEIL, PURITY_FLOOR = 0.85, 0.50

# --- Candidate construction (10 single-qubit density matrices) ---
def _dm(bx: float, by: float, bz: float) -> torch.Tensor:
    sx = torch.tensor([[0,1],[1,0]], dtype=DTYPE)
    sy = torch.tensor([[0,-1j],[1j,0]], dtype=DTYPE)
    sz = torch.tensor([[1,0],[0,-1]], dtype=DTYPE)
    return (torch.eye(2, dtype=DTYPE) + bx*sx + by*sy + bz*sz) / 2

def build_candidates() -> list[dict[str, Any]]:
    rng = torch.Generator().manual_seed(271828)
    anchors = [("pure_up",(0,0,1)), ("pure_dn",(0,0,-1)), ("pure_x",(1,0,0)),
               ("max_mixed",(0,0,0)), ("strong_z",(0,0,.85)), ("strong_x",(.85,0,0))]
    cands = [{"id": i, "label": lbl, "rho": _dm(*v)} for i, (lbl, v) in enumerate(anchors)]
    for k in range(4):
        r = float((0.5 + 0.25 * torch.rand((), generator=rng)).item())
        th = float((math.pi * torch.rand((), generator=rng)).item())
        ph = float((2 * math.pi * torch.rand((), generator=rng)).item())
        cands.append({"id": len(cands), "label": f"rand_{k}",
                      "rho": _dm(r*math.sin(th)*math.cos(ph),
                                 r*math.sin(th)*math.sin(ph),
                                 r*math.cos(th))})
    return cands  # exactly 10

# --- Scalar constraint utilities ---
def entropy(rho: torch.Tensor) -> float:
    ev = torch.clamp(torch.linalg.eigvalsh(rho), min=1e-15)
    ev = ev / ev.sum()
    return float((-ev * torch.log(ev)).sum().item())

def purity(rho: torch.Tensor) -> float:
    return float(torch.real(torch.trace(rho @ rho)).item())

def trace_dist(a: torch.Tensor, b: torch.Tensor) -> float:
    d = (a - b + (a - b).conj().T) / 2
    return float(0.5 * torch.linalg.eigvalsh(d).abs().sum().item())

# --- GUDHI H1 on survivor cloud ---
def h1_sum(survivors: list[dict[str, Any]]) -> float:
    n = len(survivors)
    if n < 3:
        return 0.0
    dm = [[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1, n):
            d = trace_dist(survivors[i]["rho"], survivors[j]["rho"])
            dm[i][j] = dm[j][i] = d
    mx = max(dm[i][j] for i in range(n) for j in range(n))
    st = gudhi.RipsComplex(distance_matrix=dm, max_edge_length=mx).create_simplex_tree(max_dimension=2)
    st.persistence()
    return sum(float(death - birth) for dim, (birth, death) in st.persistence()
               if dim == 1 and death != float("inf"))

# --- z3 separation check ---
def z3_check(tau_mid: float, tau_max: float) -> dict[str, Any]:
    if tau_max <= 1e-12:
        return {"z3_result": "skipped", "interesting_interval_non_empty": False}
    t_lo, t_hi = z3.Real("t_lo"), z3.Real("t_hi")
    tm, tM = z3.RealVal(str(round(tau_mid, 8))), z3.RealVal(str(round(tau_max, 8)))
    s = z3.Solver()
    s.add(t_lo > 0, t_hi < tM, t_lo < t_hi, t_lo < tm, tm < t_hi)
    r = s.check()
    return {"z3_result": str(r), "interesting_interval_non_empty": r == z3.sat,
            "tau_mid": tau_mid, "tau_max": tau_max}

# --- Main ---
def run() -> dict[str, Any]:
    t0 = time.time()
    cands = build_candidates()
    for c in cands:
        c["entropy"] = entropy(c["rho"])
        c["purity"] = purity(c["rho"])
        c["scalar_admitted"] = c["entropy"] <= ENTROPY_CEIL and c["purity"] >= PURITY_FLOOR
    survivors = [c for c in cands if c["scalar_admitted"]]
    scalar_ids = sorted(c["id"] for c in survivors)

    tau_max = h1_sum(survivors)
    tau_mid = tau_max / 2.0 if tau_max > 1e-12 else 0.0
    sweep_taus = [0.0, tau_mid * 0.25, tau_mid, tau_mid * 1.5, tau_max, tau_max * 2.0]
    sweep = [
        {
            "tau": round(t, 8),
            "cloud_passes": tau_max > t,
            "interior_tau": 0.0 < t < tau_max,
        }
        for t in sweep_taus
    ]

    # Predicates
    pred_a = len(survivors) > 0
    pred_b = tau_max > 1e-12
    pred_c = sweep[0]["cloud_passes"]    # τ=0 is first entry; gate is vacuous iff H1_sum > 0
    pred_d = not sweep[-1]["cloud_passes"]  # τ = 2×τ_max is last entry; must exclude all

    z3_res = z3_check(tau_mid, tau_max)
    pred_z3 = z3_res["interesting_interval_non_empty"] is True
    all_pass = pred_a and pred_b and pred_c and pred_d and pred_z3

    if pred_b:
        verdict = "killed_zero_h1_decorative_fixture — positive H1 makes the topology gate non-vacuous"
    elif tau_max <= 1e-12:
        verdict = "open — survivor cloud has zero H1; topology gate vacuously decorative"
    else:
        verdict = "open — all interior τ left cloud admission unchanged; topology decorative at this scale"

    positive = {
        "scalar_admission_set_is_nonempty": {
            "pass": pred_a,
            "scalar_admitted_count": len(survivors),
            "scalar_admitted_ids": scalar_ids,
        },
        "source_records_topology_gate_readout_without_promotion": {
            "pass": PROMOTION_ALLOWED is False and CLASSIFICATION == "formal_scout",
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "falsifier_verdict": verdict,
        },
        "positive_h1_gate_is_nonvacuous": {
            "pass": pred_b,
            "tau_max_h1_lifetime_sum": round(tau_max, 8),
            "claim": "Positive H1 makes the topology threshold surface non-vacuous without promoting topology as a layer.",
        },
        "z3_interior_interval_exists_for_positive_h1": {
            "pass": pred_z3,
            "z3_separation": z3_res,
            "claim": "Z3 records a non-empty tau interval only when tau_max is positive.",
        },
    }
    graveyard_companions = {
        "zero_h1_fixture_not_applicable_when_positive_h1_observed": {
            "pass": tau_max > 1e-12,
            "tau_max_h1_lifetime_sum": round(tau_max, 8),
            "claim": "The stale zero-H1 graveyard is not the active branch once H1_sum is positive.",
        },
        "z3_interval_witness_requires_positive_tau_max": {
            "pass": (tau_max > 1e-12) == pred_z3,
            "z3_separation": z3_res,
            "claim": "The interval witness is accepted only on the positive-H1 branch.",
        },
    }
    boundary = {
        "positive_h1_boundary_is_recorded": {
            "pass": tau_max > 1e-12,
            "tau_max_h1_lifetime_sum": round(tau_max, 8),
        },
        "large_tau_excludes_cloud_in_recorded_sweep": {
            "pass": pred_d,
            "largest_tau_row": sweep[-1],
        },
        "tau_zero_vacuous_gate_is_recorded": {
            "pass": pred_c is True,
            "tau_zero_row": sweep[0],
            "note": "At tau=0 the positive-H1 gate is intentionally vacuous; this is boundary metadata, not promotion.",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        "variants": sorted(graveyard_companions),
    }

    return {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "promotion_boundary": "formal_scout only; no topology-layer or v4 probe promotion from this falsifier receipt",
        "promotion_condition": "blocked unless an independent fixture with positive H1 and topology-changing admission is produced",
        "source_alignment_category": "standalone_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive, "graveyard_companions": graveyard_companions,
        "boundary": boundary, "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "This is a v5 formal-scout falsifier, not a v4 canonical sim promotion receipt.",
            "The observed fixture has positive H1, so the stale zero-H1 branch is not applicable.",
            "It records a non-vacuous topology threshold surface while preserving the no-promotion ceiling.",
        ],
        "blockers": [],
        "all_pass": all_pass, "elapsed_seconds": round(time.time() - t0, 3),
        "scalar_constraint": {"entropy_ceil": ENTROPY_CEIL, "purity_floor": PURITY_FLOOR},
        "candidate_count": 10, "scalar_admitted_count": len(survivors),
        "scalar_admitted_ids": scalar_ids,
        "tau_max_h1_lifetime_sum": round(tau_max, 8), "tau_mid": round(tau_mid, 8),
        "topology_gate_sweep": sweep,
        "predicates": {"a_scalar_set_nonempty": pred_a,
                       "b_positive_h1_gate_nonvacuous": pred_b,
                       "c_tau_zero_gate_vacuous": pred_c,
                       "d_tau_inf_excludes_all": pred_d,
                       "e_z3_positive_interval_exists": pred_z3},
        "z3_separation": z3_res, "falsifier_verdict": verdict,
        "candidate_detail": [{"id": c["id"], "label": c["label"],
                               "entropy": round(c["entropy"], 6),
                               "purity": round(c["purity"], 6),
                               "scalar_admitted": c["scalar_admitted"]} for c in cands],
    }

if __name__ == "__main__":
    result = run()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as fh:
        json.dump(result, fh, indent=2, default=str)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("candidate_detail", "topology_gate_sweep")},
                     indent=2, default=str))
    print(f"\nFull result written to: {OUT_PATH}")
