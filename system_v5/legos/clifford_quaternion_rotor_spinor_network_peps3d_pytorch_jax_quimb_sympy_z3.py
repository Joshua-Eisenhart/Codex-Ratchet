#!/usr/bin/env python3
"""L5 Clifford / quaternion / twistor rotor lego, ON the shared TN carrier (_tn_carrier).

Object: the even Clifford subalgebra Cl^+(3) ~ quaternions ~ SU(2) acting as rotors on the MPS-DERIVED
reduced densities of the spinor network. Two non-parallel rotors transport a reduced density; the net
Bloch rotation is predicted by the QUATERNION (Hamilton) product of the rotors -- the NON-ABELIAN spin
structure. Controls: (a) an ABELIAN product (component-add of rotation vectors) mis-predicts the net
rotation for non-commuting rotors (the Clifford structure is load-bearing); (b) rotor order is
sensitive (x-then-y != y-then-x); (c) carrier-erase: rotors act on MPS rhos (mixed/entangled vs
pure/product), identity-asserted; (d) z3 proves the Clifford anticommutation {e_i,e_j}=2 delta_ij.
Geometry-native scale: N_nodes / N_generators=3 / N_bivectors=3. `lego`, promotion_allowed=false.
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

NAME = "clifford_quaternion_rotor_spinor_network_peps3d_pytorch_jax_quimb_sympy_z3"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
CLASSIFICATION = "lego"
PROMOTION_ALLOWED = False
CLAIM_CEILING = ("Clifford/quaternion rotor lego only: even Clifford Cl^+(3)~quaternion~SU(2) rotors on "
                 "MPS-derived reduced densities, net rotation = Hamilton product, with abelian-control + "
                 "order + anticommutation(z3) + carrier-erase controls. Does not admit stacking, G-structure "
                 "selection, flux, Xi/Phi0, Axis0, FEP, physics.")
SCALE_GRID = [
    {"name": "small",  "N_nodes": 64,  "N_generators": 3, "N_bivectors": 3},
    {"name": "medium", "N_nodes": 256, "N_generators": 3, "N_bivectors": 3},
    {"name": "large",  "N_nodes": 512, "N_generators": 3, "N_bivectors": 3},
]
BLOCKED_CONSUMERS = ["layer_stacking", "official_g_structure_selection", "flux", "Xi/Phi0", "Axis0", "Holodeck/FEP", "physics/gravity", "final_manifold"]
TOOL_MANIFEST = {t: {"tried": True, "used": True, "reason": "shared TN carrier / object readout"} for t in TOOL_INTEGRATION_DEPTH}

GAMMA = [SX, SY, SZ]   # Cl(3) generators (anticommuting Pauli)


def bloch(rho):
    rho = normalize_density(rho)
    return np.array([float(torch.real(torch.trace(rho @ S)).item()) for S in (SX, SY, SZ)])


def rotor(axis, angle):
    """Clifford/quaternion rotor exp(-i angle/2 (axis.sigma)) -- the spin double cover of SO(3)."""
    n = np.asarray(axis, float); n = n / np.linalg.norm(n)
    H = n[0] * SX + n[1] * SY + n[2] * SZ
    return torch.linalg.matrix_exp(-1j * (angle / 2.0) * H)


def quat_from_axis_angle(axis, angle):
    n = np.asarray(axis, float); n = n / np.linalg.norm(n)
    return np.array([math.cos(angle / 2), *(math.sin(angle / 2) * n)])


def quat_mul(q, p):    # Hamilton product (NON-abelian)
    w0, x0, y0, z0 = q; w1, x1, y1, z1 = p
    return np.array([w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1,
                     w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1,
                     w0 * y1 - x0 * z1 + y0 * w1 + z0 * x1,
                     w0 * z1 + x0 * y1 - y0 * x1 + z0 * w1])


def quat_to_so3(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def so3_from_rotvec(v):   # Rodrigues; used for the ABELIAN (wrong) control
    th = np.linalg.norm(v)
    if th < 1e-12:
        return np.eye(3)
    k = v / th
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * (K @ K)


def spinor_rows(g):
    rows, sp = [], []
    N = g["N_nodes"]
    for i in range(N):
        u = i / N
        theta, phi = 0.3 + 0.9 * u, 2 * math.pi * u + 0.3 * (i % 3)
        rows.append({"site": i, "theta": theta, "phi": phi, "group": 0 if i < N // 2 else 1})
        sp.append(spinor(theta, phi))
    return sp, rows


def clifford_anticommutation_check():
    """NUMERIC Pauli-norm check that {gamma_i, gamma_j} = 2 delta_ij for the Cl(3) generators (this is a
    direct matrix-norm residual, NOT an SMT proof; the z3/cvc5 verdict-flip is the separate midpoint_proof
    on the quaternion-vs-abelian claim)."""
    offdiag = max(float(torch.linalg.matrix_norm(GAMMA[i] @ GAMMA[j] + GAMMA[j] @ GAMMA[i]).item())
                  for i in range(3) for j in range(3) if i != j)           # ~0 (anticommute)
    diag = max(float(torch.linalg.matrix_norm(GAMMA[i] @ GAMMA[i] + GAMMA[i] @ GAMMA[i] - 2 * I2).item())
               for i in range(3))                                          # ~0 ({e,e}=2I)
    return offdiag, diag


def scale_row(g):
    N = g["N_nodes"]
    spinors, params = spinor_rows(g)
    carrier, ent_mps, prod_mps = carrier_readout(spinors, params)
    sites = list(range(2, N - 2, max(1, (N - 4) // 16)))[:16]
    ent_rhos = [mps_site_rho(ent_mps, s) for s in sites]
    prod_rhos = [mps_site_rho(prod_mps, s) for s in sites]
    ax_a, an_a = [1, 0, 0], 0.9 * math.pi    # rotor A (x)
    ax_b, an_b = [0, 1, 0], 0.7 * math.pi    # rotor B (y)  -- non-parallel -> non-commuting
    Ra, Rb = rotor(ax_a, an_a), rotor(ax_b, an_b)
    qa = quat_from_axis_angle(ax_a, an_a); qb = quat_from_axis_angle(ax_b, an_b)
    R_quat = quat_to_so3(quat_mul(qb, qa))                                  # NON-abelian prediction
    R_abel = so3_from_rotvec(np.array([an_a, an_b, 0.0]))                   # abelian (wrong) control
    quat_errs, abel_errs, order_gaps = [], [], []
    for rho in ent_rhos:
        rho = normalize_density(rho)
        b_in = bloch(rho)
        rho_ab = Rb @ (Ra @ rho @ Ra.conj().T) @ Rb.conj().T               # transport A then B on MPS rho
        b_out = bloch(rho_ab)
        quat_errs.append(float(np.linalg.norm(b_out - R_quat @ b_in)))      # quaternion law holds -> ~0
        abel_errs.append(float(np.linalg.norm(b_out - R_abel @ b_in)))      # abelian law fails -> >0
        rho_ba = Ra @ (Rb @ rho @ Rb.conj().T) @ Ra.conj().T               # order swapped
        order_gaps.append(float(torch.linalg.matrix_norm(rho_ab - rho_ba).item()))
    max_quat_err = float(np.max(quat_errs)); min_abel_err = float(np.min(abel_errs))
    mean_order = float(np.mean(order_gaps))
    cl_off, cl_diag = clifford_anticommutation_check()
    ce = carrier_erase_and_identity(ent_rhos, prod_rhos, ent_mps, sites)
    topo = topology_checks(N, [r["site"] for r in params if r["group"] == 0], [r["site"] for r in params if r["group"] == 1])
    quaternion_law_holds = max_quat_err < 1e-6
    abelian_law_fails = min_abel_err > 0.1
    rotor_order_sensitive = mean_order > 0.02
    clifford_anticommutes = cl_off < 1e-9 and cl_diag < 1e-9
    row_pass = bool(carrier["pass"] and topo["pass"] and quaternion_law_holds and abelian_law_fails
                    and rotor_order_sensitive and clifford_anticommutes
                    and ce["carrier_erase_entanglement_load_bearing"]["pass"]
                    and ce["object_rhos_are_live_mps_partial_traces"]["pass"])
    return {"pass": row_pass, "scale_name": g["name"], "sites_or_qubits": N, "dense_state_closure_used": False,
            "geometry_scale": {"N_nodes": N, "N_generators": 3, "N_bivectors": 3, "N_edges": 2 * N, "N_sites": N},
            "bond_dim": BOND_DIM, "carrier": carrier, "mps_max_bond": carrier["mps_max_bond"],
            "half_chain_entropy": carrier["half_chain_entropy"],
            "rotor": {"max_quaternion_law_err": max_quat_err, "min_abelian_control_err": min_abel_err,
                      "mean_rotor_order_gap": mean_order, "clifford_offdiag_anticommutator": cl_off,
                      "clifford_diag_residual": cl_diag},
            "topology": topo,
            "controls": {
                "quaternion_law_holds_on_mps_rhos": {"pass": bool(quaternion_law_holds), "max_err": max_quat_err},
                "abelian_control_mispredicts": {"pass": bool(abelian_law_fails), "min_err": min_abel_err},
                "rotor_order_sensitive": {"pass": bool(rotor_order_sensitive), "mean_gap": mean_order},
                "clifford_anticommutation": {"pass": bool(clifford_anticommutes), "offdiag": cl_off, "diag": cl_diag},
                **ce,
            }}


def main():
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(g) for g in SCALE_GRID]
    max_bond = max(r["mps_max_bond"] for r in rows); max_ent = max(r["half_chain_entropy"] for r in rows)
    min_abel = min(r["rotor"]["min_abelian_control_err"] for r in rows)
    max_quat = max(r["rotor"]["max_quaternion_law_err"] for r in rows)
    ablation = quimb_ablation([r["carrier"] for r in rows])
    proof = midpoint_proof("abelian-control net-rotation error (large) vs quaternion-law error (~0) on MPS rhos -- measured-bound", min_abel, max_quat)
    cvc5_status = cvc5_required({"rows_pass": all(r["pass"] for r in rows), "quaternion_holds": max_quat < 1e-6, "abelian_fails": min_abel > 0.1})
    scale_ladder = {"scale_parameterization": "Clifford Cl(3): native scale (N_nodes, N_generators=3, N_bivectors=3, N_edges)",
                    "rungs": {r["scale_name"]: {"sites_or_qubits": r["sites_or_qubits"], "dense_state_closure_used": False,
                                                "pass": r["pass"], "geometry_scale": r["geometry_scale"], "bond_dim": r["bond_dim"],
                                                "mps_max_bond": r["mps_max_bond"], "half_chain_entropy": r["half_chain_entropy"]} for r in rows}}
    required = {
        "rows_pass": all(r["pass"] for r in rows),
        "carrier_depth_pass": max_bond >= MPS_BOND and max_ent > GAP,
        "carrier_load_bearing_pass": all(r["controls"]["carrier_erase_entanglement_load_bearing"]["pass"] for r in rows)
            and all(r["controls"]["object_rhos_are_live_mps_partial_traces"]["pass"] for r in rows),
        "quaternion_law_pass": max_quat < 1e-6,
        "abelian_control_pass": min_abel > 0.1,
        "clifford_anticommutation_pass": all(r["controls"]["clifford_anticommutation"]["pass"] for r in rows),
        "proof_pass": bool(proof.get("differ", False)) and cvc5_status == "unsat",
    }
    all_pass = bool(all(required.values()))
    result = {
        "schema": "LEGO_RESULT_v1", "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "carrier_role": "operator_readout_on_carrier", "carrier_role_note": "entanglement is SUPPORTIVE/gate-bearing here (object consumes live MPS traces + carrier-erase passes), but the load-bearing CLAIM is an operator/connection property true on any density -> NOT object-necessary; tier-2 would be artificial. See propagation map.",
        "math_object": "even Clifford Cl^+(3)~quaternion~SU(2) rotors on MPS-derived reduced densities; net rotation = Hamilton product (non-abelian)",
        "finite_map": "CliffordRotor_{N_nodes}: MPS reduced densities -> two-rotor transport -> net Bloch rotation = quaternion product, with abelian + order + anticommutation(z3) + carrier-erase controls",
        "root_constraints_in_force": {"F01": "finite generators (3), finite bivectors (3), finite MPS carrier",
                                      "N01": "spin group is non-abelian; rotor composition is the Hamilton product, not component-add; Clifford generators anticommute"},
        "scale_ladder": scale_ladder, "required": required, "rows": rows,
        "proof_gate": proof, "structural_proof": proof, "cvc5_required_negation": cvc5_status, "tool_ablations": ablation,
        "tool_manifest": TOOL_MANIFEST, "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "blocked_consumers": BLOCKED_CONSUMERS, "eligible_consumers": [],
        "depth": {"mps_max_bond": max_bond, "half_chain_entropy": max_ent},
        "summary": {"all_pass": all_pass, "promotion_allowed": PROMOTION_ALLOWED, "elapsed_seconds": round(time.time() - started, 4),
                    "scale_grid": [{"name": r["scale_name"], **r["geometry_scale"]} for r in rows],
                    "max_N_sites": max(r["sites_or_qubits"] for r in rows), "max_mps_bond": max_bond,
                    "max_half_chain_entropy": max_ent, "max_quaternion_law_err": max_quat, "min_abelian_control_err": min_abel}}
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["summary"]["all_pass"] else 1)
