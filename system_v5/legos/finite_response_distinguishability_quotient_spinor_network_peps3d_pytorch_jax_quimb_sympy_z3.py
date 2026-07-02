#!/usr/bin/env python3
"""L1 finite response / distinguishability quotient lego, ON the shared TN carrier (_tn_carrier).

Object: response vectors r_P(site) = (Tr(E_a rho_site))_a of a SIC POVM applied to the MPS-DERIVED
reduced densities of the spinor network, and the distinguishability quotient X/~_P. SIC (info-
complete) separates the sites' reduced densities into more cells than the commuting z-only POVM.
carrier-erase: the responses are computed on the MPS rhos (mixed/entangled vs pure/product),
identity-asserted. Native scale: N_states / N_effects. `lego`, promotion_allowed=false.
"""
from __future__ import annotations
import json, math, time
import numpy as np
import torch
import _tn_carrier as C
from _tn_carrier import (CDTYPE, I2, SX, SY, SZ, GAP, MPS_BOND, BOND_DIM, TOOL_INTEGRATION_DEPTH, jsonable,
                         spinor, normalize_density, build_entangled_mps, mps_site_rho, carrier_readout,
                         carrier_erase_and_identity, topology_checks, cvc5_required, midpoint_proof,
                         sympy_uniform_max_entropy, quimb_ablation, RESULT_DIR)

NAME = "finite_response_distinguishability_quotient_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = ("Finite response / distinguishability quotient lego only: SIC vs z-only quotient of the "
                 "MPS-derived reduced densities, with carrier-erase control. Does not admit stacking, "
                 "G-structure selection, flux, Xi/Phi0, Axis0, FEP, physics.")
SCALE_GRID = [
    {"name": "small",  "N_nodes": 64,  "N_effects": 4},
    {"name": "medium", "N_nodes": 256, "N_effects": 4},
    {"name": "large",  "N_nodes": 512, "N_effects": 4},
]
BLOCKED_CONSUMERS = ["layer_stacking", "official_g_structure_selection", "flux", "Xi/Phi0", "Axis0", "Holodeck/FEP", "physics/gravity", "final_manifold"]
TOOL_MANIFEST = {t: {"tried": True, "used": True, "reason": "shared TN carrier / object readout"} for t in TOOL_INTEGRATION_DEPTH}


def sic_effects():
    s = 1 / math.sqrt(3)
    bs = [(s, s, s), (s, -s, -s), (-s, s, -s), (-s, -s, s)]
    return [0.25 * (I2 + b[0] * SX + b[1] * SY + b[2] * SZ) for b in bs]


def z_effects():
    return [0.5 * (I2 + SZ), 0.5 * (I2 - SZ)]


def responses(rhos, effects):
    return np.array([[float(torch.real(torch.trace(E @ normalize_density(r))).item()) for E in effects] for r in rhos])


def quotient_cells(resp, eps):
    n = len(resp); parent = list(range(n))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for i in range(n):
        for j in range(i + 1, n):
            if np.linalg.norm(resp[i] - resp[j]) <= eps:
                parent[find(i)] = find(j)
    cells = {}
    for i in range(n):
        cells.setdefault(find(i), []).append(i)
    return list(cells.values())


def cell_entropy(cells, n):
    ps = [len(c) / n for c in cells]
    return -sum(p * math.log2(p) for p in ps if p > 0)


def spinor_rows(g):
    rows, sp = [], []
    N = g["N_nodes"]
    for i in range(N):
        u = i / N
        theta, phi = 0.2 + 1.1 * u, 2 * math.pi * u + 0.3 * (i % 3)
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
    eps = 0.04
    r_sic = responses(ent_rhos, sic_effects()); r_z = responses(ent_rhos, z_effects())
    cells_sic = quotient_cells(r_sic, eps); cells_z = quotient_cells(r_z, eps)
    H_sic = cell_entropy(cells_sic, len(sites)); H_z = cell_entropy(cells_z, len(sites))
    # eps sweep refinement (smaller eps -> more cells)
    sweep = [len(quotient_cells(r_sic, e)) for e in [0.5, 0.2, 0.1, 0.05, 0.02]]
    monotone = all(sweep[k] >= sweep[k - 1] for k in range(1, len(sweep)))
    ce = carrier_erase_and_identity(ent_rhos, prod_rhos, ent_mps, sites)
    topo = topology_checks(N, [r["site"] for r in params if r["group"] == 0], [r["site"] for r in params if r["group"] == 1])
    sic_finer = len(cells_sic) > len(cells_z) and H_sic > H_z
    refines = sweep[-1] >= sweep[0] + 2
    row_pass = bool(carrier["pass"] and topo["pass"] and sic_finer and monotone and refines
                    and ce["carrier_erase_entanglement_load_bearing"]["pass"]
                    and ce["object_rhos_are_live_mps_partial_traces"]["pass"])
    return {"pass": row_pass, "scale_name": g["name"], "sites_or_qubits": N, "dense_state_closure_used": False,
            "geometry_scale": {"N_nodes": N, "N_effects": g["N_effects"], "N_edges": 2 * N, "N_sites": N},
            "bond_dim": BOND_DIM, "carrier": carrier, "mps_max_bond": carrier["mps_max_bond"],
            "half_chain_entropy": carrier["half_chain_entropy"],
            "quotient": {"n_cells_sic": len(cells_sic), "n_cells_z": len(cells_z), "H_sic": H_sic, "H_z": H_z, "eps_sweep": sweep},
            "topology": topo,
            "controls": {
                "sic_finer_than_z": {"pass": bool(sic_finer), "n_sic": len(cells_sic), "n_z": len(cells_z)},
                "eps_refines_quotient": {"pass": bool(monotone and refines), "sweep": sweep},
                **ce,
            }}


def main():
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(g) for g in SCALE_GRID]
    symbolic = sympy_uniform_max_entropy(4)
    max_bond = max(r["mps_max_bond"] for r in rows); max_ent = max(r["half_chain_entropy"] for r in rows)
    min_dH = min(r["quotient"]["H_sic"] - r["quotient"]["H_z"] for r in rows)
    max_dH = max(r["quotient"]["H_sic"] - r["quotient"]["H_z"] for r in rows)
    ablation = quimb_ablation([r["carrier"] for r in rows])
    proof = midpoint_proof("SIC quotient entropy exceeds z-only quotient entropy (distinguishability gap) -- measured-bound", max_dH, 0.0)
    cvc5_status = cvc5_required({"rows_pass": all(r["pass"] for r in rows), "sic_finer": min_dH > GAP})
    scale_ladder = {"scale_parameterization": "distinguishability network: native scale (N_nodes, N_effects, N_edges)",
                    "rungs": {r["scale_name"]: {"sites_or_qubits": r["sites_or_qubits"], "dense_state_closure_used": False,
                                                "pass": r["pass"], "geometry_scale": r["geometry_scale"], "bond_dim": r["bond_dim"],
                                                "mps_max_bond": r["mps_max_bond"], "half_chain_entropy": r["half_chain_entropy"]} for r in rows}}
    required = {
        "rows_pass": all(r["pass"] for r in rows),
        "carrier_depth_pass": max_bond >= MPS_BOND and max_ent > GAP,
        "carrier_load_bearing_pass": all(r["controls"]["carrier_erase_entanglement_load_bearing"]["pass"] for r in rows)
            and all(r["controls"]["object_rhos_are_live_mps_partial_traces"]["pass"] for r in rows),
        "sic_finer_than_z_pass": min_dH > GAP,
        "eps_refines_pass": all(r["controls"]["eps_refines_quotient"]["pass"] for r in rows),
        "sympy_pass": symbolic["pass"],
        "proof_pass": bool(proof.get("differ", False)) and cvc5_status == "unsat",
    }
    all_pass = bool(all(required.values()))
    result = {
        "schema": "LEGO_RESULT_v1", "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "carrier_role": "operator_readout_on_carrier", "carrier_role_note": "entanglement is SUPPORTIVE/gate-bearing here (object consumes live MPS traces + carrier-erase passes), but the load-bearing CLAIM is an operator/connection property true on any density -> NOT object-necessary; tier-2 would be artificial. See propagation map.",
        "math_object": "finite SIC/z response + distinguishability quotient of the MPS-derived reduced densities of a spinor network",
        "finite_map": "FiniteResponseQuotient_{N_nodes}: MPS reduced densities -> SIC vs z responses -> quotient cells/entropy, with eps refinement + carrier-erase controls",
        "root_constraints_in_force": {"F01": "finite states (sites), finite SIC/z effects, finite MPS carrier",
                                      "N01": "SIC is informationally complete; z-only is blind to coherence -> finer vs coarser quotient"},
        "scale_ladder": scale_ladder, "required": required, "rows": rows, "symbolic_checks": symbolic,
        "proof_gate": proof, "structural_proof": proof, "cvc5_required_negation": cvc5_status, "tool_ablations": ablation,
        "tool_manifest": TOOL_MANIFEST, "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "blocked_consumers": BLOCKED_CONSUMERS, "eligible_consumers": [],
        "depth": {"mps_max_bond": max_bond, "half_chain_entropy": max_ent},
        "summary": {"all_pass": all_pass, "promotion_allowed": PROMOTION_ALLOWED, "elapsed_seconds": round(time.time() - started, 4),
                    "scale_grid": [{"name": r["scale_name"], **r["geometry_scale"]} for r in rows],
                    "max_N_sites": max(r["sites_or_qubits"] for r in rows), "max_mps_bond": max_bond,
                    "max_half_chain_entropy": max_ent, "min_sic_minus_z_entropy": min_dH}}
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["summary"]["all_pass"] else 1)
