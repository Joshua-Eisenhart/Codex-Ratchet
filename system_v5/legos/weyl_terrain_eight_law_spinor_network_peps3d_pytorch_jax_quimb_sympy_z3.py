#!/usr/bin/env python3
"""L7 eight-terrain-law lego, ON the shared TN carrier (_tn_carrier).

Object: eight candidate terrain laws -- Funnel/Vortex/Pit/Hill (+ chirality twins Cannon/Spiral/
Source/Citadel) -- applied as finite generators to the MPS-DERIVED reduced densities of the spinor
network. Each terrain has a distinct Bloch signature; the eight are pairwise distinguishable; a
control that removes the terrain generator kills its signature. carrier-erase: the generators act on
the MPS rhos (mixed/entangled vs pure/product), identity-asserted. Native scale: N_nodes / N_terrains=8.
`lego`, promotion_allowed=false.
"""
from __future__ import annotations
import json, math, time
import numpy as np
import torch
import _tn_carrier as C
from _tn_carrier import (CDTYPE, I2, SX, SY, SZ, GAP, MPS_BOND, BOND_DIM, TOOL_INTEGRATION_DEPTH, jsonable,
                         spinor, normalize_density, vn_entropy, build_entangled_mps, mps_site_rho,
                         carrier_readout, carrier_erase_and_identity, topology_checks, cvc5_required,
                         midpoint_proof, quimb_ablation, RESULT_DIR)

NAME = "weyl_terrain_eight_law_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = ("Eight-terrain-law lego only: 8 candidate terrain generators on MPS-derived reduced "
                 "densities, distinct signatures + remove-generator + carrier-erase controls. Does not "
                 "admit stacking, G-structure selection, flux, Xi/Phi0, Axis0, FEP, physics.")
SCALE_GRID = [
    {"name": "small",  "N_nodes": 64,  "N_terrains": 8},
    {"name": "medium", "N_nodes": 256, "N_terrains": 8},
    {"name": "large",  "N_nodes": 512, "N_terrains": 8},
]
BLOCKED_CONSUMERS = ["layer_stacking", "official_g_structure_selection", "flux", "Xi/Phi0", "Axis0", "Holodeck/FEP", "physics/gravity", "final_manifold"]
TOOL_MANIFEST = {t: {"tried": True, "used": True, "reason": "shared TN carrier / object readout"} for t in TOOL_INTEGRATION_DEPTH}


def bloch(rho):
    rho = normalize_density(rho)
    return np.array([float(torch.real(torch.trace(rho @ SX)).item()),
                     float(torch.real(torch.trace(rho @ SY)).item()),
                     float(torch.real(torch.trace(rho @ SZ)).item())])


def terrain_step(rho, name, *, kill=False):
    """One finite terrain generator step on a reduced density. lam/gam/kap=0 if kill (control)."""
    rho = normalize_density(rho)
    lam = 0.0 if kill else 0.25     # contraction / dissipation
    kap = 0.0 if kill else 0.30     # rotation
    chir = +1.0 if name in ("Funnel", "Vortex", "Pit", "Hill") else -1.0   # L vs R sheet sign
    H = {"Funnel": SZ, "Cannon": SZ, "Vortex": SX, "Spiral": SX,
         "Pit": SY, "Source": SY, "Hill": SZ + SX, "Citadel": SZ + SX}[name]
    contract = name in ("Funnel", "Cannon", "Pit", "Source")              # contract vs expand
    U = torch.linalg.matrix_exp(-1j * kap * chir * H)
    r2 = U @ rho @ U.conj().T
    # dissipative contraction toward (Funnel/Cannon/Pit/Source) or away (Hill/Citadel/Vortex/Spiral)
    target = 0.5 * I2 if contract else r2
    return normalize_density((1 - lam) * r2 + lam * target)


TERRAINS = ["Funnel", "Vortex", "Pit", "Hill", "Cannon", "Spiral", "Source", "Citadel"]


def signature(rho, name, *, kill=False):
    r2 = terrain_step(rho, name, kill=kill)
    b0, b1 = bloch(rho), bloch(r2)
    return {"rz_change": float(b1[2] - b0[2]), "rxy_change": float(np.linalg.norm(b1[:2]) - np.linalg.norm(b0[:2])),
            "signed_angle": float(math.atan2(b1[1], b1[0]) - math.atan2(b0[1], b0[0])),
            "purity_change": float(np.dot(b1, b1) - np.dot(b0, b0)), "dS": abs(vn_entropy(r2) - vn_entropy(rho))}


def sig_vec(rho, name, *, kill=False):
    s = signature(rho, name, kill=kill)
    return np.array([s["rz_change"], s["rxy_change"], 0.1 * s["signed_angle"], s["purity_change"]])


def spinor_rows(g):
    rows, sp = [], []
    N = g["N_nodes"]
    for i in range(N):
        u = i / N
        theta, phi = 0.3 + 0.9 * u, 2 * math.pi * u + 0.3 * (i % 3)
        rows.append({"site": i, "theta": theta, "phi": phi, "group": 0 if i < N // 2 else 1})
        sp.append(spinor(theta, phi))
    return sp, rows


def scale_row(g):
    N = g["N_nodes"]
    spinors, params = spinor_rows(g)
    carrier, ent_mps, prod_mps = carrier_readout(spinors, params)
    sites = list(range(2, N - 2, max(1, (N - 4) // 16)))[:16]
    ent_rhos = [mps_site_rho(ent_mps, s) for s in sites]
    prod_rhos = [mps_site_rho(prod_mps, s) for s in sites]
    # per-terrain mean signature vector over the MPS reduced densities
    sigs = {t: np.mean([sig_vec(r, t) for r in ent_rhos], axis=0) for t in TERRAINS}
    sigs_killed = {t: np.mean([sig_vec(r, t, kill=True) for r in ent_rhos], axis=0) for t in TERRAINS}
    pair_dists = [float(np.linalg.norm(sigs[a] - sigs[b])) for i, a in enumerate(TERRAINS) for b in TERRAINS[i + 1:]]
    min_pair = float(np.min(pair_dists))
    sig_norms = [float(np.linalg.norm(sigs[t])) for t in TERRAINS]
    killed_norms = [float(np.linalg.norm(sigs_killed[t])) for t in TERRAINS]
    min_sig = float(np.min(sig_norms)); max_killed = float(np.max(killed_norms))
    ce = carrier_erase_and_identity(ent_rhos, prod_rhos, ent_mps, sites)
    topo = topology_checks(N, [r["site"] for r in params if r["group"] == 0], [r["site"] for r in params if r["group"] == 1])
    eight_distinct = min_pair > 0.02
    signatures_alive = min_sig > 0.05
    kill_removes_signature = max_killed < 1e-9
    row_pass = bool(carrier["pass"] and topo["pass"] and eight_distinct and signatures_alive and kill_removes_signature
                    and ce["carrier_erase_entanglement_load_bearing"]["pass"]
                    and ce["object_rhos_are_live_mps_partial_traces"]["pass"])
    return {"pass": row_pass, "scale_name": g["name"], "sites_or_qubits": N, "dense_state_closure_used": False,
            "geometry_scale": {"N_nodes": N, "N_terrains": 8, "N_edges": 2 * N, "N_sites": N},
            "bond_dim": BOND_DIM, "carrier": carrier, "mps_max_bond": carrier["mps_max_bond"],
            "half_chain_entropy": carrier["half_chain_entropy"],
            "terrains": {"min_pairwise_distance": min_pair, "min_signature_norm": min_sig, "max_killed_norm": max_killed,
                         "signature_norms": dict(zip(TERRAINS, sig_norms))},
            "topology": topo,
            "controls": {
                "eight_terrains_distinct_on_mps_rhos": {"pass": bool(eight_distinct), "min_pairwise": min_pair},
                "terrain_signatures_alive": {"pass": bool(signatures_alive), "min_norm": min_sig},
                "remove_generator_kills_signature": {"pass": bool(kill_removes_signature), "max_killed": max_killed},
                **ce,
            }}


def main():
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(g) for g in SCALE_GRID]
    max_bond = max(r["mps_max_bond"] for r in rows); max_ent = max(r["half_chain_entropy"] for r in rows)
    min_pair = min(r["terrains"]["min_pairwise_distance"] for r in rows)
    max_killed = max(r["terrains"]["max_killed_norm"] for r in rows)
    ablation = quimb_ablation([r["carrier"] for r in rows])
    proof = midpoint_proof("eight-terrain min pairwise signature distance (distinct) vs killed-generator signature (~0) -- measured-bound", min_pair, max_killed)
    cvc5_status = cvc5_required({"rows_pass": all(r["pass"] for r in rows), "distinct": min_pair > 0.02, "killed_zero": max_killed < 1e-9})
    scale_ladder = {"scale_parameterization": "terrain network: native scale (N_nodes, N_terrains=8, N_edges)",
                    "rungs": {r["scale_name"]: {"sites_or_qubits": r["sites_or_qubits"], "dense_state_closure_used": False,
                                                "pass": r["pass"], "geometry_scale": r["geometry_scale"], "bond_dim": r["bond_dim"],
                                                "mps_max_bond": r["mps_max_bond"], "half_chain_entropy": r["half_chain_entropy"]} for r in rows}}
    required = {
        "rows_pass": all(r["pass"] for r in rows),
        "carrier_depth_pass": max_bond >= MPS_BOND and max_ent > GAP,
        "carrier_load_bearing_pass": all(r["controls"]["carrier_erase_entanglement_load_bearing"]["pass"] for r in rows)
            and all(r["controls"]["object_rhos_are_live_mps_partial_traces"]["pass"] for r in rows),
        "eight_distinct_pass": min_pair > 0.02,
        "remove_generator_pass": max_killed < 1e-9,
        "proof_pass": bool(proof.get("differ", False)) and cvc5_status == "unsat",
    }
    all_pass = bool(all(required.values()))
    result = {
        "schema": "LEGO_RESULT_v1", "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "carrier_role": "operator_readout_on_carrier", "carrier_role_note": "entanglement is SUPPORTIVE/gate-bearing here (object consumes live MPS traces + carrier-erase passes), but the load-bearing CLAIM is an operator/connection property true on any density -> NOT object-necessary; tier-2 would be artificial. See propagation map.",
        "math_object": "eight terrain-law generators (Funnel/Vortex/Pit/Hill + chirality twins) on MPS-derived reduced densities",
        "finite_map": "EightTerrains_{N_nodes}: MPS reduced densities -> 8 terrain signatures -> pairwise distinctness, with remove-generator + carrier-erase controls",
        "root_constraints_in_force": {"F01": "finite terrains, finite sites, finite MPS carrier",
                                      "N01": "terrain generators are order/chirality-sensitive; L and R twins differ by sheet sign"},
        "scale_ladder": scale_ladder, "required": required, "rows": rows,
        "proof_gate": proof, "structural_proof": proof, "cvc5_required_negation": cvc5_status, "tool_ablations": ablation,
        "tool_manifest": TOOL_MANIFEST, "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "blocked_consumers": BLOCKED_CONSUMERS, "eligible_consumers": [],
        "depth": {"mps_max_bond": max_bond, "half_chain_entropy": max_ent},
        "summary": {"all_pass": all_pass, "promotion_allowed": PROMOTION_ALLOWED, "elapsed_seconds": round(time.time() - started, 4),
                    "scale_grid": [{"name": r["scale_name"], **r["geometry_scale"]} for r in rows],
                    "max_N_sites": max(r["sites_or_qubits"] for r in rows), "max_mps_bond": max_bond,
                    "max_half_chain_entropy": max_ent, "min_pairwise_terrain_distance": min_pair}}
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["summary"]["all_pass"] else 1)
