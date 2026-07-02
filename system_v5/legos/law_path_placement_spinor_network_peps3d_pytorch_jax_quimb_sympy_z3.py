#!/usr/bin/env python3
"""L8 placement-of-laws-on-paths lego, ON the shared TN carrier (_tn_carrier).

Object: placing terrain/transport laws at different positions along a path and applying them to the
MPS-DERIVED reduced densities. The placement ORDER is sensitive (two laws in opposite order give a
gap); a conservative (unitary) law REMEMBERS the transport while a contractive (dissipative) law
ERASES it. carrier-erase: the placements act on MPS rhos (mixed/entangled vs pure/product),
identity-asserted. Native scale: N_nodes / N_placements. `lego`, promotion_allowed=false.
"""
from __future__ import annotations
import json, math, time
import numpy as np
import torch
import _tn_carrier as C
from _tn_carrier import (CDTYPE, I2, SX, SY, SZ, GAP, MPS_BOND, BOND_DIM, TOOL_INTEGRATION_DEPTH, jsonable,
                         spinor, normalize_density, vn_entropy, build_entangled_mps, mps_site_rho,
                         mps_joint_rho, separable_surrogate, carrier_readout, carrier_erase_and_identity,
                         topology_checks, cvc5_required, midpoint_proof, quimb_ablation, RESULT_DIR)

NAME = "law_path_placement_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = ("Placement-of-laws-on-paths lego only. TIER-2 object = placement-order RESIDUAL, "
                 "entanglement-NECESSARY ON THE SPINOR-NETWORK MPS CARRIER (flips on carrier-erase by the exact "
                 "identity R_AB == kron(marginals) on the product path) -- NOT a universal entanglement monotone "
                 "(nonzero on abstract separable-correlated 4x4 states). The single-site placement order gap / "
                 "conservative-vs-contractive are operator-property gate controls, not load-bearing. Does not admit "
                 "stacking, G-structure selection, flux, Xi/Phi0, Axis0, FEP, physics.")
SCALE_GRID = [
    {"name": "small",  "N_nodes": 64,  "N_placements": 16},
    {"name": "medium", "N_nodes": 256, "N_placements": 16},
    {"name": "large",  "N_nodes": 512, "N_placements": 16},
]
BLOCKED_CONSUMERS = ["layer_stacking", "official_g_structure_selection", "flux", "Xi/Phi0", "Axis0", "Holodeck/FEP", "physics/gravity", "final_manifold"]
TOOL_MANIFEST = {t: {"tried": True, "used": True, "reason": "shared TN carrier / object readout"} for t in TOOL_INTEGRATION_DEPTH}


def frob(a, b):
    return float(torch.linalg.matrix_norm(normalize_density(a) - normalize_density(b)).item())


def conservative(rho, k=0.7):    # unitary rotation -- REMEMBERS
    U = torch.linalg.matrix_exp(-1j * k * SX)
    return U @ normalize_density(rho) @ U.conj().T


def transport(rho, k=0.5):       # unitary z-rotation
    U = torch.linalg.matrix_exp(-1j * k * SZ)
    return U @ normalize_density(rho) @ U.conj().T


def contractive(rho, lam=0.6):   # dissipative pull to I/2 -- ERASES
    rho = normalize_density(rho)
    return normalize_density((1 - lam) * rho + lam * 0.5 * I2)


# --- TIER-2 entanglement-NECESSARY object: placement-order RESIDUAL on the live MPS joint pairs ---
# the two non-commuting placement laws (conservative=SX-rotation, transport=SZ-rotation) lifted to A.
CON_A = torch.kron(torch.linalg.matrix_exp(-1j * 0.7 * SX), I2)
TRANS_A = torch.kron(torch.linalg.matrix_exp(-1j * 0.5 * SZ), I2)


def dag2(A):
    return A.conj().T


def placement_order_gap(R):
    """Order gap of two non-commuting placement laws on subsystem A of a 2-site joint density:
    conservative-then-transport vs transport-then-conservative. Operator property (nonzero on ANY
    4x4 density) -- kept only as the anti-revert negative witness."""
    R = normalize_density(R)
    ab = TRANS_A @ (CON_A @ R @ dag2(CON_A)) @ dag2(TRANS_A)
    ba = CON_A @ (TRANS_A @ R @ dag2(TRANS_A)) @ dag2(CON_A)
    return float(torch.linalg.matrix_norm(ab - ba).item())


def placement_order_residual(R):
    """TIER-2 object: placement-order gap on the JOINT rho MINUS the same on its separable surrogate
    kron(rho_A, rho_B). Exactly 0 on a product carrier (R == surrogate -> gaps cancel), positive only
    when the path's two sites are entangled. Entanglement-necessary ON the MPS carrier; non-commuting."""
    return abs(placement_order_gap(R) - placement_order_gap(separable_surrogate(R)))


def separable_correlated_boundary():
    """DISCLOSURE (not gated): a classically-correlated SEPARABLE 2-site state (log-negativity ~ 0) still
    has a NONZERO placement-order residual -> the residual reads joint NON-FACTORIZATION (== entanglement on
    the exactly-factorizing MPS carrier), NOT a universal entanglement monotone. Marks the claim boundary."""
    z0 = torch.tensor([1, 0], dtype=CDTYPE); zp = torch.tensor([1, 1], dtype=CDTYPE) / math.sqrt(2)
    pr = lambda v: torch.outer(v, v.conj())
    rho = normalize_density(0.5 * torch.kron(pr(z0), pr(z0)) + 0.5 * torch.kron(pr(zp), pr(zp)))
    from _tn_carrier import qit_readouts
    return {"separable_correlated_residual": placement_order_residual(rho),
            "log_negativity": qit_readouts(rho)["log_negativity"],
            "note": "separable (LN~0) yet residual>0 => reads joint NON-FACTORIZATION; entanglement-necessary "
                    "ON the MPS carrier (factorizes exactly on erase), NOT a universal monotone"}


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
    order_gaps, fiber_gaps, cons_mem, contr_mem = [], [], [], []
    for rho in ent_rhos:
        rho = normalize_density(rho)
        # placement order: conservative-then-transport vs transport-then-conservative
        ab = transport(conservative(rho)); ba = conservative(transport(rho))
        order_gaps.append(frob(ab, ba))
        # commuting placement (two transports) -> no gap
        fiber_gaps.append(frob(transport(transport(rho, 0.3), 0.2), transport(transport(rho, 0.2), 0.3)))
        # conservative REMEMBERS (reversible) vs contractive ERASES (irreversible): how much of the
        # original survives a forward-then-inverse placement
        Uc = torch.linalg.matrix_exp(-1j * 0.7 * SX)
        cons_round = Uc.conj().T @ (Uc @ rho @ Uc.conj().T) @ Uc
        cons_mem.append(frob(cons_round, rho))                       # ~0 (remembers)
        contr_mem.append(frob(contractive(rho), rho))               # >0 (erases)
    mean_order = float(np.mean(order_gaps)); max_fiber = float(np.max(fiber_gaps))
    max_cons = float(np.max(cons_mem)); min_contr = float(np.min(contr_mem))
    # --- TIER-2 placement-order RESIDUAL on the live MPS joint pairs (both carriers -> the flip) ---
    pairs = [(a, a + 1) for a in range(2, N - 3, max(1, (N - 4) // 12))][:12]
    resid_ent, resid_prod, bare_prod, bare_ent = [], [], [], []
    for (a, b) in pairs:
        Rent = mps_joint_rho(ent_mps, a, b); Rprod = mps_joint_rho(prod_mps, a, b)
        resid_ent.append(placement_order_residual(Rent)); resid_prod.append(placement_order_residual(Rprod))
        bare_ent.append(placement_order_gap(Rent)); bare_prod.append(placement_order_gap(Rprod))
    mean_resid_ent = float(np.mean(resid_ent)); max_resid_prod = float(np.max(resid_prod))
    mean_bare_prod = float(np.mean(bare_prod))
    ce = carrier_erase_and_identity(ent_rhos, prod_rhos, ent_mps, sites)
    topo = topology_checks(N, [r["site"] for r in params if r["group"] == 0], [r["site"] for r in params if r["group"] == 1])
    placement_order_sensitive = mean_order > 0.02
    commuting_no_gap = max_fiber < 1e-9
    conservative_remembers = max_cons < 1e-9
    contractive_erases = min_contr > 0.05
    residual_flips = mean_resid_ent > 0.005 and max_resid_prod < 1e-9
    bare_gap_does_not_flip = mean_bare_prod > 0.02
    row_pass = bool(carrier["pass"] and topo["pass"] and placement_order_sensitive and commuting_no_gap
                    and conservative_remembers and contractive_erases and residual_flips and bare_gap_does_not_flip
                    and ce["carrier_erase_entanglement_load_bearing"]["pass"]
                    and ce["object_rhos_are_live_mps_partial_traces"]["pass"])
    return {"pass": row_pass, "scale_name": g["name"], "sites_or_qubits": N, "dense_state_closure_used": False,
            "geometry_scale": {"N_nodes": N, "N_placements": g["N_placements"], "N_edges": 2 * N, "N_sites": N},
            "bond_dim": BOND_DIM, "carrier": carrier, "mps_max_bond": carrier["mps_max_bond"],
            "half_chain_entropy": carrier["half_chain_entropy"], "carrier_role": "object_load_bearing",
            "placement": {"mean_order_gap": mean_order, "max_commuting_gap": max_fiber,
                          "max_conservative_memory_loss": max_cons, "min_contractive_erasure": min_contr},
            "tier2_residual": {"mean_residual_entangled": mean_resid_ent, "max_residual_product": max_resid_prod,
                               "mean_bare_gap_entangled": float(np.mean(bare_ent)), "mean_bare_gap_product": mean_bare_prod,
                               "n_pairs": len(pairs)},
            "topology": topo,
            "controls": {
                "placement_order_residual_flips_on_carrier_erase": {"pass": bool(residual_flips),
                    "mean_residual_entangled": mean_resid_ent, "max_residual_product": max_resid_prod},
                "bare_placement_gap_is_operator_property_does_not_flip": {"pass": bool(bare_gap_does_not_flip),
                    "mean_bare_gap_product": mean_bare_prod, "note": "placement order gap survives carrier-erase; tier-2 content lives in the residual"},
                "placement_order_sensitive_on_mps_rhos": {"pass": bool(placement_order_sensitive), "mean_gap": mean_order, "role": "operator_property_gate"},
                "commuting_placement_no_gap": {"pass": bool(commuting_no_gap), "max_gap": max_fiber},
                "conservative_remembers": {"pass": bool(conservative_remembers), "max_loss": max_cons},
                "contractive_erases": {"pass": bool(contractive_erases), "min_erasure": min_contr},
                **ce,
            }}


def main():
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(g) for g in SCALE_GRID]
    max_bond = max(r["mps_max_bond"] for r in rows); max_ent = max(r["half_chain_entropy"] for r in rows)
    min_order = min(r["placement"]["mean_order_gap"] for r in rows)
    max_comm = max(r["placement"]["max_commuting_gap"] for r in rows)
    min_resid_ent = min(r["tier2_residual"]["mean_residual_entangled"] for r in rows)
    max_resid_prod = max(r["tier2_residual"]["max_residual_product"] for r in rows)
    ablation = quimb_ablation([r["carrier"] for r in rows])
    # HEADLINE proof binds the TIER-2 placement-order RESIDUAL flip (entangled vs product), NOT the bare gap.
    proof = midpoint_proof("TIER-2 placement-order RESIDUAL: entangled path (>0) vs product path (~0, exact) -- measured-bound", min_resid_ent, max_resid_prod)
    order_proof = midpoint_proof("tier-1 operator-property gate: placement order gap vs commuting placement gap (~0) -- measured-bound", min_order, max_comm)
    cvc5_status = cvc5_required({"rows_pass": all(r["pass"] for r in rows), "residual_flip_ent": min_resid_ent > 0.005, "residual_flip_prod": max_resid_prod < 1e-9})
    scale_ladder = {"scale_parameterization": "law-path-placement network: native scale (N_nodes, N_placements, N_edges)",
                    "rungs": {r["scale_name"]: {"sites_or_qubits": r["sites_or_qubits"], "dense_state_closure_used": False,
                                                "pass": r["pass"], "geometry_scale": r["geometry_scale"], "bond_dim": r["bond_dim"],
                                                "mps_max_bond": r["mps_max_bond"], "half_chain_entropy": r["half_chain_entropy"]} for r in rows}}
    required = {
        "rows_pass": all(r["pass"] for r in rows),
        "carrier_depth_pass": max_bond >= MPS_BOND and max_ent > GAP,
        "carrier_load_bearing_pass": all(r["controls"]["carrier_erase_entanglement_load_bearing"]["pass"] for r in rows)
            and all(r["controls"]["object_rhos_are_live_mps_partial_traces"]["pass"] for r in rows),
        "placement_order_pass": min_order > 0.02,
        "conservative_vs_contractive_pass": all(r["controls"]["conservative_remembers"]["pass"] and r["controls"]["contractive_erases"]["pass"] for r in rows),
        "tier2_residual_flips_pass": min_resid_ent > 0.005 and max_resid_prod < 1e-9,
        "tier2_bare_gap_does_not_flip_pass": all(r["controls"]["bare_placement_gap_is_operator_property_does_not_flip"]["pass"] for r in rows),
        "proof_pass": bool(proof.get("differ", False)) and bool(order_proof.get("differ", False)) and cvc5_status == "unsat",
    }
    all_pass = bool(all(required.values()))
    result = {
        "schema": "LEGO_RESULT_v1", "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "math_object": "TIER-2 entanglement-necessary: placement-order RESIDUAL (joint-rho placement-order gap minus separable-surrogate gap) on the live MPS path; flips on carrier-erase. Single-site placement order gap / conservative-vs-contractive kept as operator-property gate controls.",
        "finite_map": "LawPathPlacement_{N_nodes}: live entangled MPS -> joint 2-site path rhos -> |placement_gap(R_AB) - gap(rho_A(x)rho_B)| residual (>0 entangled, 0 product), with bare-gap witness + commuting + conservative/contractive + carrier-erase controls",
        "root_constraints_in_force": {"F01": "finite placements, finite sites, finite MPS carrier",
                                      "N01": "placing two non-commuting laws across an ENTANGLED path is order-sensitive in a way the separable surrogate cannot reproduce; product path factorizes -> residual exactly 0"},
        "carrier_role": "object_load_bearing",
        "tier2_claim_boundary": separable_correlated_boundary(),
        "scale_ladder": scale_ladder, "required": required, "rows": rows,
        "proof_gate": proof, "structural_proof": proof, "tier1_order_gate_proof": order_proof, "cvc5_required_negation": cvc5_status, "tool_ablations": ablation,
        "tool_manifest": TOOL_MANIFEST, "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "blocked_consumers": BLOCKED_CONSUMERS, "eligible_consumers": [],
        "depth": {"mps_max_bond": max_bond, "half_chain_entropy": max_ent},
        "summary": {"all_pass": all_pass, "promotion_allowed": PROMOTION_ALLOWED, "elapsed_seconds": round(time.time() - started, 4),
                    "scale_grid": [{"name": r["scale_name"], **r["geometry_scale"]} for r in rows],
                    "max_N_sites": max(r["sites_or_qubits"] for r in rows), "max_mps_bond": max_bond,
                    "max_half_chain_entropy": max_ent, "min_placement_order_gap": min_order,
                    "carrier_role": "object_load_bearing", "tier2_min_residual_entangled": min_resid_ent,
                    "tier2_max_residual_product": max_resid_prod}}
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["summary"]["all_pass"] else 1)
