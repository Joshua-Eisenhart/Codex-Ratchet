#!/usr/bin/env python3
"""L9 local operator / channel action lego, ON the shared TN carrier (_tn_carrier).

Object: local action families (pinch / unitary / CPTP amplitude-damping / order gap) applied to the
MPS-DERIVED reduced densities of the spinor network. The order gap of non-commuting actions is the
load-bearing claim; a commuting registry collapses it. carrier-erase: the channels act on MPS rhos
(mixed on entangled, pure on product) -- identity-asserted. Native scale: N_nodes / N_actions.
`lego`, promotion_allowed=false.
"""
from __future__ import annotations
import json, math, time
import numpy as np
import torch
import _tn_carrier as C
from _tn_carrier import (CDTYPE, I2, SX, SY, SZ, GAP, MPS_BOND, BOND_DIM, TOOL_INTEGRATION_DEPTH, jsonable,
                         spinor, normalize_density, vn_entropy, build_entangled_mps, mps_site_rho,
                         mps_cut_qit, mps_joint_rho, separable_surrogate, carrier_readout,
                         carrier_erase_and_identity, topology_checks, cvc5_required, midpoint_proof,
                         quimb_ablation, RESULT_DIR)

NAME = "local_operator_channel_action_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = ("Local operator/channel action lego only. TIER-2 object = joint two-site order-gap RESIDUAL, "
                 "entanglement-NECESSARY ON THE SPINOR-NETWORK MPS CARRIER (the residual flips on carrier-erase "
                 "by the exact identity R_AB == kron(marginals) on the product carrier) -- it is NOT a universal "
                 "entanglement monotone (it is nonzero on abstract separable-correlated 4x4 states). Tier-1 "
                 "single-site order gap / CPTP are operator-property gate controls, not load-bearing. Does not "
                 "admit stacking, G-structure selection, flux, Xi/Phi0, Axis0, FEP, physics.")
SCALE_GRID = [
    {"name": "small",  "N_nodes": 64,  "N_actions": 4},
    {"name": "medium", "N_nodes": 256, "N_actions": 4},
    {"name": "large",  "N_nodes": 512, "N_actions": 4},
]
BLOCKED_CONSUMERS = ["layer_stacking", "official_g_structure_selection", "flux", "Xi/Phi0", "Axis0", "Holodeck/FEP", "physics/gravity", "final_manifold"]
TOOL_MANIFEST = {t: {"tried": True, "used": True, "reason": "shared TN carrier / object readout"} for t in TOOL_INTEGRATION_DEPTH}

P0 = torch.tensor([[1, 0], [0, 0]], dtype=CDTYPE)
P1 = torch.tensor([[0, 0], [0, 1]], dtype=CDTYPE)


def dag(A):
    return A.conj().T


def spinor_rows(g):
    rows, sp = [], []
    N = g["N_nodes"]
    for i in range(N):
        u = i / N
        theta, phi = 0.2 + 1.1 * u, 2 * math.pi * u + 0.3 * (i % 3)
        rows.append({"site": i, "theta": theta, "phi": phi, "group": 0 if i < N // 2 else 1})
        sp.append(spinor(theta, phi))
    return sp, rows


def pinch(rho):
    return P0 @ rho @ P0 + P1 @ rho @ P1


def unitary(A, t):
    U = torch.linalg.matrix_exp(-1j * t * A)
    return lambda r: U @ r @ dag(U)


def amp_damp(rho, gamma=0.3):
    K0 = torch.tensor([[1, 0], [0, math.sqrt(1 - gamma)]], dtype=CDTYPE)
    K1 = torch.tensor([[0, math.sqrt(gamma)], [0, 0]], dtype=CDTYPE)
    return K0 @ rho @ dag(K0) + K1 @ rho @ dag(K1)


def frob(a, b):
    return float(torch.linalg.matrix_norm(a - b).item())


# --- TIER-2 entanglement-NECESSARY object: joint two-site order-gap RESIDUAL ---
# Lift the single-site actions (pinch, Ux) to subsystem A of a 2-site joint density via kron(., I2).
UX_A = torch.kron(torch.linalg.matrix_exp(-1j * (math.pi / 4) * SX), I2)
P0_A = torch.kron(P0, I2)
P1_A = torch.kron(P1, I2)


def pinch_A(R):
    return P0_A @ R @ P0_A + P1_A @ R @ P1_A


def ux_A(R):
    return UX_A @ R @ dag(UX_A)


def joint_order_gap(R):
    """Bare order gap of two non-commuting local actions on subsystem A of a 2-site joint density.
    This is the TIER-1 operator property (nonzero on ANY 4x4 density, incl. product) -- NOT load-bearing
    on its own; kept only as the anti-revert negative witness."""
    R = normalize_density(R)
    return float(torch.linalg.matrix_norm(pinch_A(ux_A(R)) - ux_A(pinch_A(R))).item())


def joint_order_residual(R):
    """TIER-2 object: bare gap on the JOINT rho MINUS the same gap on its separable surrogate
    kron(rho_A, rho_B). Exactly 0 on a product carrier (there R == surrogate to machine precision, so the
    two gaps cancel), positive only when the joint rho is non-factorizable. Entanglement-necessary ON THE
    MPS CARRIER by an exact algebraic identity (the carrier-erased = product carrier factorizes exactly),
    and requires the actions to be non-commuting (commuting -> both gaps ~0)."""
    return abs(joint_order_gap(R) - joint_order_gap(separable_surrogate(R)))


def separable_correlated_boundary():
    """DISCLOSURE (not gated, per the cross-model verify): a classically-correlated SEPARABLE 2-site state
    (log-negativity ~ 0) still has a NONZERO joint-order residual. So the residual detects joint NON-
    FACTORIZATION -- which on the spinor-network MPS carrier coincides with entanglement (the product /
    carrier-erased carrier factorizes EXACTLY), but is NOT a universal entanglement-only monotone. This
    marks the exact boundary of the tier-2 claim that grok+gemini+codex flagged."""
    z0 = torch.tensor([1, 0], dtype=CDTYPE)
    zp = torch.tensor([1, 1], dtype=CDTYPE) / math.sqrt(2)
    pr = lambda v: torch.outer(v, v.conj())
    rho = normalize_density(0.5 * torch.kron(pr(z0), pr(z0)) + 0.5 * torch.kron(pr(zp), pr(zp)))  # separable, correlated
    from _tn_carrier import qit_readouts
    return {"separable_correlated_residual": joint_order_residual(rho),
            "log_negativity": qit_readouts(rho)["log_negativity"],
            "note": "separable (LN~0) yet residual>0 => the residual reads joint NON-FACTORIZATION; it is "
                    "entanglement-necessary ON the MPS carrier (which factorizes exactly on erase), NOT a "
                    "universal entanglement monotone"}


def scale_row(g):
    N = g["N_nodes"]
    spinors, params = spinor_rows(g)
    carrier, ent_mps, prod_mps = carrier_readout(spinors, params)
    sites = list(range(2, N - 2, max(1, (N - 4) // 12)))[:12]
    ent_rhos = [mps_site_rho(ent_mps, s) for s in sites]
    prod_rhos = [mps_site_rho(prod_mps, s) for s in sites]
    Ux = unitary(SX, math.pi / 4); Uz = unitary(SZ, math.pi / 3); Uz2 = unitary(SZ, math.pi / 5)
    # ACTIONS applied to the MPS reduced densities (NOT isolated spinors)
    order_gaps, commute_gaps, cptp_trace_errs, dS_pinch, dS_unit = [], [], [], [], []
    for rho in ent_rhos:
        rho = normalize_density(rho)
        order_gaps.append(frob(Ux(pinch(rho)), pinch(Ux(rho))))            # non-commuting -> gap
        commute_gaps.append(frob(Uz(Uz2(rho)), Uz2(Uz(rho))))             # commuting -> ~0
        cptp_trace_errs.append(abs(float(torch.trace(amp_damp(rho)).real.item()) - 1.0))
        dS_pinch.append(vn_entropy(pinch(rho)) - vn_entropy(rho))
        dS_unit.append(abs(vn_entropy(Ux(rho)) - vn_entropy(rho)))
    mean_order = float(np.mean(order_gaps)); max_commute = float(np.max(commute_gaps))
    max_cptp_err = float(np.max(cptp_trace_errs)); max_dS_unit = float(np.max(dS_unit))
    # non-CPTP control breaks trace (bad Kraus)
    bad = torch.tensor([[1, 0], [0, 1.4]], dtype=CDTYPE)
    noncptp_err = float(max(abs(float(torch.trace(bad @ normalize_density(r) @ dag(bad)).real.item()) - 1.0) for r in ent_rhos))
    # --- TIER-2 entanglement-NECESSARY object: joint two-site order-gap RESIDUAL on the live MPS ---
    # adjacent physical pairs carry the brick-wall entanglement; run the residual on BOTH carriers (the flip)
    pairs = [(a, a + 1) for a in range(2, N - 3, max(1, (N - 4) // 12))][:12]
    resid_ent, resid_prod, bare_ent, bare_prod = [], [], [], []
    for (a, b) in pairs:
        Rent = mps_joint_rho(ent_mps, a, b)
        Rprod = mps_joint_rho(prod_mps, a, b)
        resid_ent.append(joint_order_residual(Rent))      # >0: joint != separable surrogate (entangled)
        resid_prod.append(joint_order_residual(Rprod))    # ~0: joint == surrogate byte-for-byte (product)
        bare_ent.append(joint_order_gap(Rent))            # tier-1 operator property (nonzero on BOTH)
        bare_prod.append(joint_order_gap(Rprod))
    mean_resid_ent = float(np.mean(resid_ent)); max_resid_prod = float(np.max(resid_prod))
    mean_bare_ent = float(np.mean(bare_ent)); mean_bare_prod = float(np.mean(bare_prod))
    ce = carrier_erase_and_identity(ent_rhos, prod_rhos, ent_mps, sites)
    topo = topology_checks(N, [r["site"] for r in params if r["group"] == 0], [r["site"] for r in params if r["group"] == 1])
    order_sensitive = mean_order > 0.02
    commuting_no_gap = max_commute < 1e-9
    cptp_trace_preserving = max_cptp_err < 1e-9
    noncptp_breaks = noncptp_err > 0.1
    unitary_conserves = max_dS_unit < 1e-9
    # tier-2 gates
    residual_flips = mean_resid_ent > 0.005 and max_resid_prod < 1e-9      # passes on entangled, fails on product
    bare_gap_does_not_flip = mean_bare_prod > 0.02                          # anti-revert: bare gap survives carrier-erase
    row_pass = bool(carrier["pass"] and topo["pass"] and order_sensitive and commuting_no_gap
                    and cptp_trace_preserving and noncptp_breaks and unitary_conserves
                    and residual_flips and bare_gap_does_not_flip
                    and ce["carrier_erase_entanglement_load_bearing"]["pass"]
                    and ce["object_rhos_are_live_mps_partial_traces"]["pass"])
    return {"pass": row_pass, "scale_name": g["name"], "sites_or_qubits": N, "dense_state_closure_used": False,
            "geometry_scale": {"N_nodes": N, "N_actions": g["N_actions"], "N_edges": 2 * N, "N_sites": N},
            "bond_dim": BOND_DIM, "carrier": carrier, "mps_max_bond": carrier["mps_max_bond"],
            "half_chain_entropy": carrier["half_chain_entropy"],
            "carrier_role": "object_load_bearing",
            "action_readouts": {"mean_order_gap": mean_order, "max_commuting_gap": max_commute,
                                "max_cptp_trace_err": max_cptp_err, "noncptp_trace_err": noncptp_err},
            "tier2_residual": {"mean_residual_entangled": mean_resid_ent, "max_residual_product": max_resid_prod,
                               "mean_bare_gap_entangled": mean_bare_ent, "mean_bare_gap_product": mean_bare_prod,
                               "n_pairs": len(pairs)},
            "topology": topo,
            "controls": {
                "joint_order_residual_flips_on_carrier_erase": {"pass": bool(residual_flips),
                    "mean_residual_entangled": mean_resid_ent, "max_residual_product": max_resid_prod},
                "bare_gap_is_tier1_operator_property_does_not_flip": {"pass": bool(bare_gap_does_not_flip),
                    "mean_bare_gap_product": mean_bare_prod, "note": "operator property survives carrier-erase; tier-2 content lives in the residual, not the bare gap"},
                "order_gap_noncommuting_on_mps_rhos": {"pass": bool(order_sensitive), "mean_order_gap": mean_order, "role": "operator_property_gate"},
                "commuting_registry_no_gap": {"pass": bool(commuting_no_gap), "max_gap": max_commute},
                "cptp_trace_preserving": {"pass": bool(cptp_trace_preserving)},
                "noncptp_control_breaks_trace": {"pass": bool(noncptp_breaks), "err": noncptp_err},
                "unitary_conserves_entropy": {"pass": bool(unitary_conserves)},
                **ce,
            }}


def main():
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(g) for g in SCALE_GRID]
    max_bond = max(r["mps_max_bond"] for r in rows); max_ent = max(r["half_chain_entropy"] for r in rows)
    min_order = min(r["action_readouts"]["mean_order_gap"] for r in rows)
    max_commute = max(r["action_readouts"]["max_commuting_gap"] for r in rows)
    min_resid_ent = min(r["tier2_residual"]["mean_residual_entangled"] for r in rows)
    max_resid_prod = max(r["tier2_residual"]["max_residual_product"] for r in rows)
    ablation = quimb_ablation([r["carrier"] for r in rows])
    # HEADLINE proof binds the TIER-2 residual flip (entangled vs product), NOT the bare order gap.
    proof = midpoint_proof("TIER-2 joint two-site order-gap RESIDUAL: entangled carrier (>0) vs product carrier (~0, exact) -- measured-bound", min_resid_ent, max_resid_prod)
    order_proof = midpoint_proof("tier-1 operator-property gate: non-commuting order gap vs commuting registry gap -- measured-bound", min_order, max_commute)
    cvc5_status = cvc5_required({"rows_pass": all(r["pass"] for r in rows), "residual_flip_ent": min_resid_ent > 0.005,
                                 "residual_flip_prod": max_resid_prod < 1e-9})
    scale_ladder = {"scale_parameterization": "operator/channel network: native scale (N_nodes, N_actions, N_edges)",
                    "rungs": {r["scale_name"]: {"sites_or_qubits": r["sites_or_qubits"], "dense_state_closure_used": False,
                                                "pass": r["pass"], "geometry_scale": r["geometry_scale"], "bond_dim": r["bond_dim"],
                                                "mps_max_bond": r["mps_max_bond"], "half_chain_entropy": r["half_chain_entropy"]} for r in rows}}
    required = {
        "rows_pass": all(r["pass"] for r in rows),
        "carrier_depth_pass": max_bond >= MPS_BOND and max_ent > GAP,
        "carrier_load_bearing_pass": all(r["controls"]["carrier_erase_entanglement_load_bearing"]["pass"] for r in rows)
            and all(r["controls"]["object_rhos_are_live_mps_partial_traces"]["pass"] for r in rows),
        "order_gap_pass": min_order > 0.02,
        "commuting_control_pass": max_commute < 1e-9,
        "cptp_pass": all(r["controls"]["cptp_trace_preserving"]["pass"] and r["controls"]["noncptp_control_breaks_trace"]["pass"] for r in rows),
        "tier2_residual_flips_pass": min_resid_ent > 0.005 and max_resid_prod < 1e-9,
        "tier2_bare_gap_does_not_flip_pass": all(r["controls"]["bare_gap_is_tier1_operator_property_does_not_flip"]["pass"] for r in rows),
        "proof_pass": bool(proof.get("differ", False)) and bool(order_proof.get("differ", False)) and cvc5_status == "unsat",
    }
    all_pass = bool(all(required.values()))
    result = {
        "schema": "LEGO_RESULT_v1", "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "math_object": "TIER-2 entanglement-necessary: joint two-site order-gap RESIDUAL (joint-rho gap minus separable-surrogate gap) on the live MPS; flips on carrier-erase. Tier-1 single-site order gap / CPTP kept as operator-property gate controls.",
        "finite_map": "LocalAction_{N_nodes}: live entangled MPS -> joint 2-site rhos -> |gap(R_AB) - gap(rho_A(x)rho_B)| residual (>0 entangled, 0 product), with bare-gap anti-revert witness + commuting + CPTP + carrier-erase controls",
        "root_constraints_in_force": {"F01": "finite sites, finite action registry, finite MPS carrier",
                                      "N01": "non-commuting actions on an ENTANGLED joint rho give a residual the separable surrogate cannot reproduce; product carrier factorizes -> residual exactly 0"},
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
                    "max_half_chain_entropy": max_ent, "min_order_gap": min_order, "max_commuting_gap": max_commute,
                    "carrier_role": "object_load_bearing", "tier2_min_residual_entangled": min_resid_ent,
                    "tier2_max_residual_product": max_resid_prod}}
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["summary"]["all_pass"] else 1)
