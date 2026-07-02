#!/usr/bin/env python3
"""L4 Hopf-fibration / nested-tori transport-holonomy lego, ON the shared TN carrier (_tn_carrier).

Object: parallel transport of the MPS-DERIVED reduced densities around closed loops on the Hopf base
S^2. The Hopf connection (a non-flat U(1) connection on S^3 -> S^2) accumulates a holonomy = half the
enclosed solid angle when the rho is carried around a base loop; a FLAT (trivial) connection
accumulates zero. Nested-tori leaves of different base-latitude enclose different solid angles ->
different holonomy. carrier-erase: the transport acts on MPS rhos (mixed/entangled vs pure/product),
identity-asserted. Geometry-native scale: N_fiber x N_base x N_shells (NOT a qubit ladder).
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

NAME = "hopf_transport_holonomy_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = ("Hopf transport-holonomy lego only: parallel transport of MPS-derived reduced densities "
                 "around Hopf base loops -> holonomy = half-solid-angle, with flat-connection + carrier-erase "
                 "controls. Does not admit stacking, G-structure selection, flux, Xi/Phi0, Axis0, FEP, physics.")
# native Hopf scale: fiber samples x base samples x torus leaves (shells). MPS site count derives from base x shells.
SCALE_GRID = [
    {"name": "small",  "N_fiber": 16, "N_base": 16, "N_shells": 4},
    {"name": "medium", "N_fiber": 32, "N_base": 32, "N_shells": 8},
    {"name": "large",  "N_fiber": 48, "N_base": 48, "N_shells": 12},
]
BLOCKED_CONSUMERS = ["layer_stacking", "official_g_structure_selection", "flux", "Xi/Phi0", "Axis0", "Holodeck/FEP", "physics/gravity", "final_manifold"]
TOOL_MANIFEST = {t: {"tried": True, "used": True, "reason": "shared TN carrier / object readout"} for t in TOOL_INTEGRATION_DEPTH}


def base_loop_unitaries(theta, n_seg, *, flat=False):
    """Discretized parallel-transport unitaries around a latitude-theta loop on S^2 (Hopf base).
    Non-flat: the spin-1/2 holonomy of a loop enclosing solid angle Omega is exp(-i Omega/2 * n.sigma).
    Flat control: zero connection -> identity transport (no holonomy)."""
    us = []
    for k in range(n_seg):
        phi = 2 * math.pi * k / n_seg
        # local connection 1-form A = (1-cos theta)/2 dphi about the local z axis (Berry/Hopf monopole)
        dphi = 2 * math.pi / n_seg
        ang = 0.0 if flat else (1 - math.cos(theta)) * dphi
        us.append(torch.linalg.matrix_exp(-1j * 0.5 * ang * SZ))
    return us


def transport_loop(rho, us):
    rho = normalize_density(rho)
    for U in us:
        rho = U @ rho @ U.conj().T
    return rho


def holonomy_on_rho(rho, theta, n_seg, *, flat=False):
    """Carrier-borne Berry/Hopf holonomy: transport the MPS-DERIVED reduced density rho around the
    latitude-theta base loop and READ the holonomy phase Omega/2 off the rho's off-diagonal coherence.
    Under the diagonal transport U=diag(e^{-i.5 ang}, e^{+i.5 ang}), rho_01 -> e^{-i Omega} rho_01, so
    Omega = -arg(rho'_01 / rho_01) and holonomy = Omega/2. Returns None if rho has no transverse support
    (a holonomy is only readable on a coherence). flat connection -> no phase shift -> 0. This makes the
    half-solid-angle LAW depend on the carrier rho, not on an isolated unitary."""
    r = normalize_density(rho)
    a0 = complex(r[0, 1].item())
    if abs(a0) < 1e-6:
        return None
    for U in base_loop_unitaries(theta, n_seg, flat=flat):
        r = U @ r @ U.conj().T
    a1 = complex(r[0, 1].item())
    omega = -float(np.angle(a1 / a0))             # principal value in (-pi, pi]; = Omega for our range (Omega<pi)
    return 0.5 * omega                            # = Omega/2; flat -> ~0 (no spurious 2pi wrap)


def shell_holonomy_on_rhos(rhos, theta, n_seg, *, flat=False):
    """Mean holonomy read off the transverse-supported MPS reduced densities at one shell latitude."""
    vals = [h for h in (holonomy_on_rho(r, theta, n_seg, flat=flat) for r in rhos) if h is not None]
    return float(np.mean(vals)) if vals else 0.0


def spinor_rows(g):
    rows, sp = [], []
    N = g["N_base"] * g["N_shells"]
    for i in range(N):
        u = i / N
        theta, phi = 0.25 + 0.85 * u, 2 * math.pi * u + 0.3 * (i % 3)
        rows.append({"site": i, "theta": theta, "phi": phi, "group": 0 if i < N // 2 else 1})
        sp.append(spinor(theta, phi))
    return sp, rows


def scale_row(g):
    N = g["N_base"] * g["N_shells"]
    n_seg = g["N_fiber"]
    spinors, params = spinor_rows(g)
    carrier, ent_mps, prod_mps = carrier_readout(spinors, params)
    sites = list(range(2, N - 2, max(1, (N - 4) // 16)))[:16]
    ent_rhos = [mps_site_rho(ent_mps, s) for s in sites]
    prod_rhos = [mps_site_rho(prod_mps, s) for s in sites]
    # nested-tori leaves at distinct base latitudes (shells) -> distinct enclosed solid angle -> distinct holonomy
    shell_thetas = [0.3 + 0.7 * k / max(1, g["N_shells"] - 1) for k in range(g["N_shells"])]
    # transport each MPS reduced density around each shell loop; measure post-transport Bloch rotation
    transport_rots = []
    for rho in ent_rhos[:8]:
        rho = normalize_density(rho)
        b0 = np.array([float(torch.real(torch.trace(rho @ S)).item()) for S in (SX, SY, SZ)])
        rt = transport_loop(rho, base_loop_unitaries(shell_thetas[-1], n_seg))
        b1 = np.array([float(torch.real(torch.trace(rt @ S)).item()) for S in (SX, SY, SZ)])
        transport_rots.append(float(np.linalg.norm(b1 - b0)))
    mean_transport_rot = float(np.mean(transport_rots))
    # holonomy READ OFF THE MPS REDUCED DENSITIES (carrier-borne): half solid angle, distinct across
    # shells; flat connection -> ~0. The law now depends on the carrier rho, not an isolated unitary.
    holonomies = [shell_holonomy_on_rhos(ent_rhos, th, n_seg) for th in shell_thetas]
    flat_holonomies = [shell_holonomy_on_rhos(ent_rhos, th, n_seg, flat=True) for th in shell_thetas]
    # check half-solid-angle law: Omega(theta) = 2*pi*(1-cos theta); holonomy phase = Omega/2 = pi*(1-cos theta)
    expected = [math.pi * (1 - math.cos(th)) for th in shell_thetas]
    law_err = float(max(abs(holonomies[k] - expected[k]) for k in range(len(holonomies))))
    shells_distinct = float(min(abs(holonomies[i] - holonomies[j])
                                for i in range(len(holonomies)) for j in range(i + 1, len(holonomies)))) if len(holonomies) > 1 else 1.0
    max_flat = float(max(flat_holonomies))
    min_holo = float(min(h for h in holonomies if h > 1e-6)) if any(h > 1e-6 for h in holonomies) else 0.0
    ce = carrier_erase_and_identity(ent_rhos, prod_rhos, ent_mps, sites)
    topo = topology_checks(N, [r["site"] for r in params if r["group"] == 0], [r["site"] for r in params if r["group"] == 1])
    holonomy_nonzero = min_holo > 0.02 and mean_transport_rot > 0.01
    half_solid_angle_law = law_err < 0.05
    flat_zero = max_flat < 1e-9
    shells_distinct_pass = shells_distinct > 0.01
    row_pass = bool(carrier["pass"] and topo["pass"] and holonomy_nonzero and half_solid_angle_law and flat_zero and shells_distinct_pass
                    and ce["carrier_erase_entanglement_load_bearing"]["pass"]
                    and ce["object_rhos_are_live_mps_partial_traces"]["pass"])
    return {"pass": row_pass, "scale_name": g["name"], "sites_or_qubits": N, "dense_state_closure_used": False,
            "geometry_scale": {"N_fiber": g["N_fiber"], "N_base": g["N_base"], "N_shells": g["N_shells"],
                               "N_eta": g["N_fiber"], "N_edges": 2 * N, "N_sites": N},
            "bond_dim": BOND_DIM, "carrier": carrier, "mps_max_bond": carrier["mps_max_bond"],
            "half_chain_entropy": carrier["half_chain_entropy"],
            "holonomy": {"shell_holonomies": holonomies, "half_solid_angle_law_err": law_err,
                         "shells_min_distinct": shells_distinct, "max_flat_holonomy": max_flat,
                         "min_holonomy": min_holo, "mean_transport_rotation": mean_transport_rot},
            "topology": topo,
            "controls": {
                "holonomy_nonzero_on_mps_rhos": {"pass": bool(holonomy_nonzero), "min_holonomy": min_holo, "mean_transport_rot": mean_transport_rot},
                "half_solid_angle_law": {"pass": bool(half_solid_angle_law), "law_err": law_err},
                "flat_connection_zero_holonomy": {"pass": bool(flat_zero), "max_flat": max_flat},
                "nested_tori_shells_distinct": {"pass": bool(shells_distinct_pass), "min_distinct": shells_distinct},
                **ce,
            }}


def main():
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(g) for g in SCALE_GRID]
    max_bond = max(r["mps_max_bond"] for r in rows); max_ent = max(r["half_chain_entropy"] for r in rows)
    min_holo = min(r["holonomy"]["min_holonomy"] for r in rows)
    max_flat = max(r["holonomy"]["max_flat_holonomy"] for r in rows)
    ablation = quimb_ablation([r["carrier"] for r in rows])
    proof = midpoint_proof("Hopf holonomy (nonzero half-solid-angle) vs flat-connection holonomy (~0) on MPS rhos -- measured-bound", min_holo, max_flat)
    cvc5_status = cvc5_required({"rows_pass": all(r["pass"] for r in rows), "holonomy_nonzero": min_holo > 0.02, "flat_zero": max_flat < 1e-9})
    scale_ladder = {"scale_parameterization": "Hopf fibration: native scale (N_fiber x N_base x N_shells); MPS sites = N_base x N_shells",
                    "rungs": {r["scale_name"]: {"sites_or_qubits": r["sites_or_qubits"], "dense_state_closure_used": False,
                                                "pass": r["pass"], "geometry_scale": r["geometry_scale"], "bond_dim": r["bond_dim"],
                                                "mps_max_bond": r["mps_max_bond"], "half_chain_entropy": r["half_chain_entropy"]} for r in rows}}
    required = {
        "rows_pass": all(r["pass"] for r in rows),
        "carrier_depth_pass": max_bond >= MPS_BOND and max_ent > GAP,
        "carrier_load_bearing_pass": all(r["controls"]["carrier_erase_entanglement_load_bearing"]["pass"] for r in rows)
            and all(r["controls"]["object_rhos_are_live_mps_partial_traces"]["pass"] for r in rows),
        "holonomy_nonzero_pass": min_holo > 0.02,
        "half_solid_angle_law_pass": all(r["controls"]["half_solid_angle_law"]["pass"] for r in rows),
        "flat_connection_pass": max_flat < 1e-9,
        "proof_pass": bool(proof.get("differ", False)) and cvc5_status == "unsat",
    }
    all_pass = bool(all(required.values()))
    result = {
        "schema": "LEGO_RESULT_v1", "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "carrier_role": "operator_readout_on_carrier", "carrier_role_note": "entanglement is SUPPORTIVE/gate-bearing here (object consumes live MPS traces + carrier-erase passes), but the load-bearing CLAIM is an operator/connection property true on any density -> NOT object-necessary; tier-2 would be artificial. See propagation map.",
        "math_object": "Hopf-connection parallel-transport holonomy (= half enclosed solid angle) of MPS-derived reduced densities, across nested-tori shells",
        "finite_map": "HopfHolonomy_{N_base}x{N_shells}: MPS reduced densities -> base-loop parallel transport -> holonomy = Omega/2, with flat-connection + nested-shell + carrier-erase controls",
        "root_constraints_in_force": {"F01": "finite fiber/base/shell samples, finite MPS carrier",
                                      "N01": "Hopf connection is non-flat; holonomy is path/area-sensitive; flat connection gives zero"},
        "scale_ladder": scale_ladder, "required": required, "rows": rows,
        "proof_gate": proof, "structural_proof": proof, "cvc5_required_negation": cvc5_status, "tool_ablations": ablation,
        "tool_manifest": TOOL_MANIFEST, "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "blocked_consumers": BLOCKED_CONSUMERS, "eligible_consumers": [],
        "depth": {"mps_max_bond": max_bond, "half_chain_entropy": max_ent},
        "summary": {"all_pass": all_pass, "promotion_allowed": PROMOTION_ALLOWED, "elapsed_seconds": round(time.time() - started, 4),
                    "scale_grid": [{"name": r["scale_name"], **r["geometry_scale"]} for r in rows],
                    "max_N_sites": max(r["sites_or_qubits"] for r in rows), "max_mps_bond": max_bond,
                    "max_half_chain_entropy": max_ent, "min_holonomy": min_holo, "max_flat_holonomy": max_flat}}
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["summary"]["all_pass"] else 1)
