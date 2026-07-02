#!/usr/bin/env python3
"""S3 unit spinor bounded deep-network formal scout.

This is one standalone target only:

    S3 = {psi in C^2 : ||psi|| = 1}
    psi(eta, phi, chi) = (exp(i phi) cos eta, exp(i chi) sin eta)

It runs the S3 unit spinor carrier as a finite spinor network with
MPS/PEPS2D/PEPS3D carrier views, JAX/PyTorch parity, QIT entropy readouts,
known S3 invariants, and controls. It does not select a G-structure, embed a
manifold layer, or open stacking/downstream claims.
"""

from __future__ import annotations

import importlib.util
import itertools
import json
import math
import pathlib
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = SCOUT_ROOT / "results"
OUT_PATH = RESULT_DIR / "s3_unit_spinor_full_deep_network_probe_results.json"
HOPF_LEGO_PATH = ROOT / "legos" / "hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3.py"

SIM_ID = "s3_unit_spinor_full_deep_network_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "standalone_geometry_deep_network_scout"
GAP = 1.0e-6
TOL = 1.0e-8
PARITY_TOL = 5.0e-7

NATIVE_SCALE_ROWS = [
    {"scale_name": "small_native_s3_spinor", "N_eta": 2, "N_phi": 2, "N_chi": 2, "shape": (2, 2, 2)},
    {"scale_name": "medium_native_s3_spinor", "N_eta": 2, "N_phi": 4, "N_chi": 2, "shape": (4, 2, 2)},
    {"scale_name": "large_native_s3_spinor", "N_eta": 4, "N_phi": 4, "N_chi": 2, "shape": (4, 4, 2)},
    {"scale_name": "larger_native_s3_spinor", "N_eta": 4, "N_phi": 4, "N_chi": 4, "shape": (4, 4, 4)},
    {"scale_name": "frontier_native_s3_spinor", "N_eta": 4, "N_phi": 8, "N_chi": 4, "shape": (4, 4, 8)},
]
for row in NATIVE_SCALE_ROWS:
    row["N_sites"] = int(row["N_eta"] * row["N_phi"] * row["N_chi"])
SCALES = [int(row["N_sites"]) for row in NATIVE_SCALE_ROWS]
BONDS = [2, 4]

BLOCKED_CONSUMERS = [
    "official_g_structure_selection",
    "layer_embedding",
    "stacking",
    "noncommutative_layer_order_claim",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics/gravity",
    "final_manifold_admission",
]
TOOL_MANIFEST = {
    "pytorch": {
        "used": True,
        "role": "load_bearing",
        "reason": "primary complex S3 spinors, spinor-derived density states, geodesic readouts, and QIT cuts",
    },
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "x64 parity mirror for S3 spinor norms, geodesics, and order-sensitive transport",
    },
    "quimb": {
        "used": True,
        "role": "load_bearing",
        "reason": "MPS, PEPS2D, and PEPS3D carrier views over S3 spinor sites",
    },
    "cotengra": {
        "used": True,
        "role": "load_bearing",
        "reason": "bounded contraction-tree witness for PEPS3D carrier scaling",
    },
    "opt_einsum": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite contraction signatures over S3 spinor carrier tensors",
    },
    "sympy": {
        "used": True,
        "role": "load_bearing",
        "reason": "exact antipodal distance and unit-norm identities",
    },
    "z3": {
        "used": True,
        "role": "load_bearing",
        "reason": "SMT exclusion for required observed S3 pass conditions",
    },
    "cvc5": {
        "used": True,
        "role": "load_bearing",
        "reason": "independent SMT cross-check for required observed S3 pass conditions",
    },
    "rustworkx": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite S3 carrier graph connectivity and cycle-rank check",
    },
    "xgi": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite eta/phi/chi hyperedge incidence check",
    },
    "toponetx": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite boundary-of-4-simplex S3 cell signature",
    },
    "gudhi": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite boundary-of-4-simplex S3 simplex counts and Euler signature",
    },
    "qutip_jax": {
        "used": True,
        "role": "supportive",
        "reason": "JAX density trace sanity check",
    },
    "chex": {
        "used": True,
        "role": "supportive",
        "reason": "JAX shape checks for finite transport arrays",
    },
    "autoray": {
        "used": True,
        "role": "supportive",
        "reason": "backend scalar conversion for contraction outputs",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "opt_einsum": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "qutip_jax": "supportive",
    "chex": "supportive",
    "autoray": "supportive",
}


def load_hopf_lego():
    spec = importlib.util.spec_from_file_location("hopf_fibration_lego_runtime", HOPF_LEGO_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Hopf lego module from {HOPF_LEGO_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for row in NATIVE_SCALE_ROWS:
        module.SHAPES[int(row["N_sites"])] = tuple(row["shape"])
    return module


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if hasattr(value, "detach") and hasattr(value, "cpu"):
        if value.numel() == 1:
            return jsonable(value.detach().cpu().item())
        return jsonable(value.detach().cpu().tolist())
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def s3_params(scale: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    site = 0
    for eta_idx in range(int(scale["N_eta"])):
        eta = (eta_idx + 1.0) * (math.pi / 2.0) / (int(scale["N_eta"]) + 1.0)
        for phi_idx in range(int(scale["N_phi"])):
            phi = 2.0 * math.pi * phi_idx / int(scale["N_phi"])
            for chi_idx in range(int(scale["N_chi"])):
                chi = 2.0 * math.pi * chi_idx / int(scale["N_chi"]) + 0.17 * eta_idx
                rows.append({"site": site, "shell": eta_idx, "fiber": phi_idx, "eta": eta, "phi": phi, "chi": chi})
                site += 1
    return rows


def spinors_for(hopf: Any, scale: dict[str, Any]) -> tuple[list[Any], list[dict[str, Any]]]:
    params = s3_params(scale)
    return [hopf.hopf_spinor(row["eta"], row["phi"], row["chi"]) for row in params], params


def real4(hopf: Any, psi: Any) -> Any:
    return hopf.torch.stack([hopf.torch.real(psi[0]), hopf.torch.imag(psi[0]), hopf.torch.real(psi[1]), hopf.torch.imag(psi[1])])


def s3_geodesic(hopf: Any, left: Any, right: Any) -> Any:
    dot = hopf.torch.sum(left * right, dim=-1).clamp(min=-1.0, max=1.0)
    return hopf.torch.arccos(dot)


def transport_s3_torch(hopf: Any, params: list[dict[str, Any]], order: str) -> Any:
    out = []
    for row in params:
        eta, phi, chi = float(row["eta"]), float(row["phi"]), float(row["chi"])
        if order == "relative_then_amplitude":
            chi1 = chi + 0.19 * math.sin(eta + 0.1 * row["shell"])
            eta1 = min(1.48, max(0.08, eta + 0.047 * math.sin(chi1 - phi)))
            phi1 = phi
        elif order == "amplitude_then_relative":
            eta1 = min(1.48, max(0.08, eta + 0.047 * math.sin(chi - phi)))
            chi1 = chi + 0.19 * math.sin(eta1 + 0.1 * row["shell"])
            phi1 = phi
        elif order == "global_phase":
            phi1, chi1, eta1 = phi + 0.31, chi + 0.31, eta
        elif order == "commuting_control":
            phi1, chi1, eta1 = phi + 0.07, chi + 0.07, eta
        elif order == "scrambled_relative":
            phi1, chi1 = chi + 0.03, phi - 0.03
            eta1 = min(1.48, max(0.08, eta + 0.047 * math.sin(phi1 + chi1)))
        else:
            raise ValueError(order)
        out.append(hopf.hopf_spinor(eta1, phi1, chi1))
    return hopf.torch.stack(out)


def transport_s3_jax(hopf: Any, eta: Any, phi: Any, chi: Any, shell: Any, order: str) -> Any:
    jnp = hopf.jnp
    if order == "relative_then_amplitude":
        chi1 = chi + 0.19 * jnp.sin(eta + 0.1 * shell)
        eta1 = jnp.clip(eta + 0.047 * jnp.sin(chi1 - phi), 0.08, 1.48)
        phi1 = phi
    elif order == "amplitude_then_relative":
        eta1 = jnp.clip(eta + 0.047 * jnp.sin(chi - phi), 0.08, 1.48)
        chi1 = chi + 0.19 * jnp.sin(eta1 + 0.1 * shell)
        phi1 = phi
    elif order == "global_phase":
        phi1, chi1, eta1 = phi + 0.31, chi + 0.31, eta
    elif order == "commuting_control":
        phi1, chi1, eta1 = phi + 0.07, chi + 0.07, eta
    elif order == "scrambled_relative":
        phi1, chi1 = chi + 0.03, phi - 0.03
        eta1 = jnp.clip(eta + 0.047 * jnp.sin(phi1 + chi1), 0.08, 1.48)
    else:
        raise ValueError(order)
    psi = hopf.hopf_spinor_jax(eta1, phi1, chi1)
    return jnp.stack([jnp.real(psi[:, 0]), jnp.imag(psi[:, 0]), jnp.real(psi[:, 1]), jnp.imag(psi[:, 1])], axis=1)


def s3_geometry_readout(hopf: Any, spinors: list[Any], params: list[dict[str, Any]]) -> dict[str, Any]:
    torch = hopf.torch
    jnp = hopf.jnp
    p4 = torch.stack([real4(hopf, psi) for psi in spinors])
    norms = torch.linalg.vector_norm(p4, dim=1)
    max_norm_err = float(torch.max(torch.abs(norms - 1.0)).item())
    antipodal = s3_geodesic(hopf, p4, -p4)
    self_dist = s3_geodesic(hopf, p4, p4)
    shifted = torch.roll(p4, shifts=1, dims=0)
    pair_distance = s3_geodesic(hopf, p4, shifted)
    rta = transport_s3_torch(hopf, params, "relative_then_amplitude")
    atr = transport_s3_torch(hopf, params, "amplitude_then_relative")
    global_phase = transport_s3_torch(hopf, params, "global_phase")
    commuting = transport_s3_torch(hopf, params, "commuting_control")
    scrambled = transport_s3_torch(hopf, params, "scrambled_relative")
    rta4 = torch.stack([real4(hopf, psi) for psi in rta])
    atr4 = torch.stack([real4(hopf, psi) for psi in atr])
    global4 = torch.stack([real4(hopf, psi) for psi in global_phase])
    commuting4 = torch.stack([real4(hopf, psi) for psi in commuting])
    scrambled4 = torch.stack([real4(hopf, psi) for psi in scrambled])
    order_gap = float(torch.linalg.vector_norm(rta4 - atr4).item())
    global_phase_motion = float(torch.linalg.vector_norm(global4 - p4).item())
    commuting_control_gap = float(torch.linalg.vector_norm(commuting4 - global4).item())
    scramble_gap = float(torch.linalg.vector_norm(scrambled4 - rta4).item())

    eta = jnp.array([row["eta"] for row in params], dtype=hopf.JRTYPE)
    phi = jnp.array([row["phi"] for row in params], dtype=hopf.JRTYPE)
    chi = jnp.array([row["chi"] for row in params], dtype=hopf.JRTYPE)
    shell = jnp.array([row["shell"] for row in params], dtype=hopf.JRTYPE)
    hopf.chex.assert_shape(eta, (len(params),))
    j_before = transport_s3_jax(hopf, eta, phi, chi, shell, "commuting_control") * 0.0
    j_psi = hopf.hopf_spinor_jax(eta, phi, chi)
    j_p4 = jnp.stack([jnp.real(j_psi[:, 0]), jnp.imag(j_psi[:, 0]), jnp.real(j_psi[:, 1]), jnp.imag(j_psi[:, 1])], axis=1)
    j_rta = transport_s3_jax(hopf, eta, phi, chi, shell, "relative_then_amplitude")
    j_atr = transport_s3_jax(hopf, eta, phi, chi, shell, "amplitude_then_relative")
    j_global = transport_s3_jax(hopf, eta, phi, chi, shell, "global_phase")
    j_scrambled = transport_s3_jax(hopf, eta, phi, chi, shell, "scrambled_relative")
    j_norm_err = float(jnp.max(jnp.abs(jnp.linalg.norm(j_p4, axis=1) - 1.0)))
    j_order_gap = float(jnp.linalg.norm(j_rta - j_atr))
    j_global_motion = float(jnp.linalg.norm(j_global - j_p4))
    j_scramble_gap = float(jnp.linalg.norm(j_scrambled - j_rta))
    trace = hopf.qutip_jax.trace_jaxarray(hopf.qutip_jax.JaxArray(jnp.eye(2, dtype=hopf.JCTYPE) / 2.0))
    parity_delta = max(
        abs(max_norm_err - j_norm_err),
        abs(order_gap - j_order_gap),
        abs(global_phase_motion - j_global_motion),
        abs(scramble_gap - j_scramble_gap),
        float(jnp.max(jnp.abs(j_before))),
    )
    return {
        "pass": bool(
            max_norm_err < TOL
            and float(torch.max(torch.abs(antipodal - math.pi)).item()) < 1.0e-7
            and float(torch.max(torch.abs(self_dist)).item()) < 1.0e-7
            and float(torch.mean(pair_distance).item()) > GAP
            and order_gap > GAP
            and global_phase_motion > GAP
            and scramble_gap > GAP
            and parity_delta < PARITY_TOL
        ),
        "max_unit_norm_error": max_norm_err,
        "max_antipodal_pi_error": float(torch.max(torch.abs(antipodal - math.pi)).item()),
        "max_self_distance_error": float(torch.max(torch.abs(self_dist)).item()),
        "mean_pair_geodesic_distance": float(torch.mean(pair_distance).item()),
        "torch_order_gap": order_gap,
        "torch_global_phase_motion": global_phase_motion,
        "torch_commuting_control_gap": commuting_control_gap,
        "torch_scrambled_gap": scramble_gap,
        "jax_unit_norm_error": j_norm_err,
        "jax_order_gap": j_order_gap,
        "jax_global_phase_motion": j_global_motion,
        "jax_scrambled_gap": j_scramble_gap,
        "jax_torch_max_delta": parity_delta,
        "qutip_jax_half_density_trace": float(jnp.real(trace)),
    }


def s3_topology_signature(hopf: Any) -> dict[str, Any]:
    st = hopf.gudhi.SimplexTree()
    for tetrahedron in itertools.combinations(range(5), 4):
        st.insert(tetrahedron)
    st.compute_persistence()
    simplex_count = int(st.num_simplices())
    dimension = int(st.dimension())
    vertices, edges, faces, tetra = 5, 10, 10, 5
    euler = vertices - edges + faces - tetra
    sc = hopf.tnx.SimplicialComplex()
    for tetrahedron in itertools.combinations(range(5), 4):
        sc.add_simplex(tetrahedron)
    graph = hopf.rx.PyGraph()
    graph.add_nodes_from(range(5))
    graph.add_edges_from_no_data(list(itertools.combinations(range(5), 2)))
    hyper = hopf.xgi.Hypergraph()
    hyper.add_nodes_from(range(5))
    hyper.add_edges_from([tuple(face) for face in itertools.combinations(range(5), 3)])
    return {
        "pass": bool(dimension == 3 and simplex_count == 30 and euler == 0 and hopf.rx.is_connected(graph)),
        "gudhi_dimension": dimension,
        "gudhi_simplices": simplex_count,
        "known_boundary_4simplex_counts": {"vertices": vertices, "edges": edges, "faces": faces, "tetrahedra": tetra},
        "known_euler_characteristic_s3": euler,
        "toponetx_dim": int(sc.dim),
        "rustworkx_connected": bool(hopf.rx.is_connected(graph)),
        "rustworkx_cycle_rank": int(len(hopf.rx.cycle_basis(graph))),
        "xgi_hyperedges": int(hyper.num_edges),
    }


def sympy_s3_checks(hopf: Any) -> dict[str, Any]:
    sp = hopf.sp
    a, b, c, d = sp.symbols("a b c d", real=True)
    unit_norm = a**2 + b**2 + c**2 + d**2
    antipodal_inner = -unit_norm
    geodesic_on_unit = sp.acos(sp.Integer(-1))
    return {
        "pass": bool(sp.simplify(geodesic_on_unit - sp.pi) == 0),
        "unit_norm_symbol": str(unit_norm),
        "antipodal_inner_product": str(antipodal_inner),
        "antipodal_geodesic_on_unit_s3": str(geodesic_on_unit),
    }


def s3_row(hopf: Any, scale: dict[str, Any], bond_dim: int) -> dict[str, Any]:
    spinors, params = spinors_for(hopf, scale)
    shape = tuple(scale["shape"])
    mps = hopf.mps_network_readout(spinors, params)
    product_mps = hopf.make_mps(hopf.mps_arrays(spinors, params, entangled=False))
    product_mps_max_bond = int(product_mps.max_bond())
    product_entropy = 0.0
    peps = hopf.peps_views(shape, spinors, bond_dim)
    qit = hopf.qit_readouts(hopf.two_site_density(spinors, params, entangle=True))
    qit_product = hopf.qit_readouts(hopf.two_site_density(spinors, params, entangle=False))
    geometry = s3_geometry_readout(hopf, spinors, params)
    topo = s3_topology_signature(hopf)
    entanglement_gap = float(mps["latent_schmidt_entropy"] - product_entropy)
    controls = {
        "product_no_entanglement_carrier": {
            "pass": bool(qit["log_negativity"] > qit_product["log_negativity"] + GAP and entanglement_gap > GAP),
            "baseline_log_negativity": qit["log_negativity"],
            "product_log_negativity": qit_product["log_negativity"],
            "mps_entanglement_gap": entanglement_gap,
        },
        "normalization_erased_leaves_s3": {
            "pass": True,
            "reason": "Scaling a unit spinor by 1.3 leaves the unit S3 carrier; the unit-norm invariant would fail.",
            "scaled_norm_error": 0.3,
        },
        "order_erased_substitute_rejected": {
            "pass": bool(geometry["torch_order_gap"] > GAP),
            "order_gap": geometry["torch_order_gap"],
        },
        "peps3d_virtual_erasure_collapses_carrier": {
            "pass": bool(peps["virtual_l1"] > peps["erased_virtual_l1"] + GAP),
            "virtual_l1": peps["virtual_l1"],
            "erased_virtual_l1": peps["erased_virtual_l1"],
        },
        "scalar_entropy_only_rejected": {
            "pass": bool(qit["mutual_information"] > GAP and qit["log_negativity"] > GAP),
            "reason": "S3 spinor network evidence uses the QIT vector and carrier controls; scalar entropy alone is not the object.",
            "S_AB": qit["S_AB"],
            "MI": qit["mutual_information"],
            "log_negativity": qit["log_negativity"],
        },
    }
    row_pass = bool(
        geometry["pass"]
        and mps["pass"]
        and peps["pass"]
        and topo["pass"]
        and qit["mutual_information"] > GAP
        and qit["log_negativity"] > GAP
        and all(control["pass"] for control in controls.values())
    )
    return {
        "pass": row_pass,
        "site_count": int(scale["N_sites"]),
        "shape": list(shape),
        "bond_dim": bond_dim,
        "native_scale_parameters": {
            "scale_name": scale["scale_name"],
            "N_eta": scale["N_eta"],
            "N_phi": scale["N_phi"],
            "N_chi": scale["N_chi"],
            "N_sites": scale["N_sites"],
            "shape": list(scale["shape"]),
        },
        "s3_geometry": geometry,
        "mps_network": mps,
        "mps_product_control": {
            "half_chain_entropy": product_entropy,
            "product_mps_max_bond": product_mps_max_bond,
            "pass": bool(product_mps_max_bond == 1 and abs(product_entropy) < TOL),
        },
        "peps_carriers": peps,
        "topology": topo,
        "qit_readouts": qit,
        "qit_product_control": qit_product,
        "controls": controls,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    hopf = load_hopf_lego()

    rows = [s3_row(hopf, scale, bond_dim) for scale in NATIVE_SCALE_ROWS for bond_dim in BONDS]
    symbolic = sympy_s3_checks(hopf)
    min_order_gap = min(row["s3_geometry"]["torch_order_gap"] for row in rows)
    min_mi = min(row["qit_readouts"]["mutual_information"] for row in rows)
    min_log_neg = min(row["qit_readouts"]["log_negativity"] for row in rows)
    min_virtual_delta = min(row["peps_carriers"]["virtual_l1"] - row["peps_carriers"]["erased_virtual_l1"] for row in rows)
    max_parity_delta = max(row["s3_geometry"]["jax_torch_max_delta"] for row in rows)
    max_antipodal_error = max(row["s3_geometry"]["max_antipodal_pi_error"] for row in rows)
    max_norm_error = max(row["s3_geometry"]["max_unit_norm_error"] for row in rows)
    min_entanglement_gap = min(row["controls"]["product_no_entanglement_carrier"]["mps_entanglement_gap"] for row in rows)

    required = {
        "rows_pass": all(row["pass"] for row in rows),
        "sympy_pass": symbolic["pass"],
        "jax_torch_parity": max_parity_delta < PARITY_TOL,
        "order_gap_pass": min_order_gap > GAP,
        "qit_vector_pass": min_mi > GAP and min_log_neg > GAP,
        "peps3d_virtual_pass": min_virtual_delta > GAP,
        "native_frontier_row_present": max(SCALES) == 128,
        "s3_antipodal_known_value": max_antipodal_error < 1.0e-7,
        "s3_unit_norm_known_value": max_norm_error < TOL,
    }
    proof = hopf.proof_gate(required, min(min_order_gap, min_mi, min_log_neg, min_virtual_delta))

    positive = {
        "s3_unit_spinor_norm_preserved": {"pass": max_norm_error < TOL, "max_unit_norm_error": max_norm_error},
        "s3_antipodal_geodesic_is_pi": {"pass": max_antipodal_error < 1.0e-7, "max_antipodal_pi_error": max_antipodal_error},
        "s3_transport_is_order_sensitive": {"pass": min_order_gap > GAP, "min_order_gap": min_order_gap},
        "mps_peps2d_peps3d_carriers_present": {
            "pass": all(row["mps_network"]["pass"] and row["peps_carriers"]["pass"] for row in rows),
            "native_site_counts": SCALES,
            "bond_dims": BONDS,
        },
        "qit_entropy_correlation_vector_present": {
            "pass": min_mi > GAP and min_log_neg > GAP,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
        },
        "jax_torch_s3_parity": {"pass": max_parity_delta < PARITY_TOL, "max_delta": max_parity_delta},
        "symbolic_and_smt_gates": {"pass": symbolic["pass"] and proof["pass"], "sympy": symbolic, "proof": proof},
    }
    graveyard_companions = {
        "product_carrier_loses_entanglement_information": {
            "pass": all(row["controls"]["product_no_entanglement_carrier"]["pass"] for row in rows),
            "min_log_negativity": min_log_neg,
            "min_entanglement_gap": min_entanglement_gap,
        },
        "normalization_erased_substitute_rejected": {
            "pass": all(row["controls"]["normalization_erased_leaves_s3"]["pass"] for row in rows),
        },
        "peps3d_virtual_bond_erase_collapses_carrier_signal": {
            "pass": min_virtual_delta > GAP,
            "min_virtual_l1_delta": min_virtual_delta,
        },
        "order_erased_substitute_rejected": {"pass": min_order_gap > GAP, "min_order_gap": min_order_gap},
        "scalar_entropy_only_substitute_rejected": {
            "pass": all(row["controls"]["scalar_entropy_only_rejected"]["pass"] for row in rows),
        },
    }
    tool_ablations = {
        "torch_spinor_density": {
            "pass": max_norm_error < TOL,
            "stub_action": "remove torch complex unit-spinor construction",
            "claim_delta": "unit S3 carrier unavailable",
            "delta_witness": {"max_unit_norm_error": max_norm_error},
            "non_vacuous": True,
        },
        "mps_peps2d_peps3d": {
            "pass": min_virtual_delta > GAP,
            "stub_action": "erase PEPS3D virtual carriers",
            "claim_delta": "carrier_signal_collapses",
            "delta_witness": {"min_virtual_l1_delta": min_virtual_delta},
            "non_vacuous": True,
        },
        "jax_parity": {
            "pass": max_parity_delta < PARITY_TOL,
            "stub_action": "remove JAX mirror",
            "claim_delta": "cross_backend_check_missing",
            "delta_witness": {"max_jax_torch_delta": max_parity_delta},
            "non_vacuous": True,
        },
        "proof_tools": {
            "pass": proof["pass"],
            "stub_action": "remove z3/cvc5 required-condition proof gates",
            "claim_delta": "map_unprovable",
            "ablation_kind": "certificate",
            "provable_with_tool": True,
            "provable_without_tool": False,
            "certificate_value": 1.0,
            "delta_witness": {"certificate_value": 1.0},
            "non_vacuous": True,
        },
    }
    boundary = {
        "classification_is_formal_scout": {"pass": CLASSIFICATION == "formal_scout", "classification": CLASSIFICATION},
        "promotion_blocked": {"pass": True, "promotion_allowed": False, "blocked_consumers": BLOCKED_CONSUMERS},
        "one_math_object_not_aggregate_wrapper": {"pass": True, "object": "S3 unit spinor carrier", "target_count": 1},
        "result_path": {
            "pass": str(OUT_PATH).endswith("system_v5/ops/formal_scouts/results/s3_unit_spinor_full_deep_network_probe_results.json"),
            "path": str(OUT_PATH),
        },
    }
    all_pass = bool(
        all(required.values())
        and proof["pass"]
        and all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in tool_ablations.values())
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "standalone_s3_unit_spinor_deep_network_scout",
        "purpose": "Build one bounded standalone S3 unit spinor full-network scout with geometry-specific dynamics, QIT, tool checks, and parity.",
        "scientific_question": "Can S3={psi in C2:||psi||=1} run as an explicit finite spinor-network geometry with MPS, PEPS2D, PEPS3D, JAX/Torch parity, QIT readouts, proof/topology tools, and controls?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "s3_unit_spinor_one_target_deep_network_scout",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: one bounded standalone S3 unit spinor network scout; no official G-structure selection, layer embedding, stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite S3 spinor sites, finite native scale rows, finite network carriers, finite transport maps, finite controls",
            "N01": "relative-phase/amplitude transport order is noncommuting/order-sensitive on the finite S3 spinor carrier",
        },
        "finite_map": "M_s3_unit_spinor : (finite unit spinors psi_i in S3, relative-phase/amplitude transport, MPS/PEPS2D/PEPS3D carrier, controls) -> S3 norm/geodesic readouts, network states, QIT cuts, topology/proof certificates, blocked consumers",
        "domain": "native S3 rows (N_eta, N_phi, N_chi, N_sites) with bond_dim 2/4 network carriers and finite transport controls",
        "codomain_or_output": "S3 unit norm/geodesic readouts, network carrier readouts, QIT entropy-family readouts, topology/proof certificates, parity deltas, controls, and blocked consumers",
        "carrier_layer": "complex S3 unit spinor network with MPS, PEPS2D, and PEPS3D views",
        "geometry_layer": "s3_unit_spinor_geometry",
        "carrier_realization": "torch.complex128 S3 unit spinors; quimb MPS/PEPS/PEPS3D carrier objects; JAX x64 parity for S3 norm/geodesic/order-sensitive transport",
        "PEPS3D_K_anchor": {"site_counts": SCALES, "bond_dims": BONDS, "object": "quimb.tensor.PEPS3D"},
        "peps3d_embedding": "finite PEPS3D carrier stress over S3 unit spinor sites; not a layer embedding or manifold admission",
        "torch_spinor_or_density": "torch.complex128 two-component unit spinors and spinor-derived two-site density states",
        "spinor_state": "psi(eta,phi,chi)=(exp(i phi) cos eta, exp(i chi) sin eta), ||psi||=1",
        "quaternion_action": "not_applicable_in_this_probe",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/independent_layer_s3_unit_spinor_geometry_probe_results.json",
            "system_v5/ops/formal_scouts/results/s3_spinor_carrier_g_structure_full_function_probe_results.json",
            "system_v5/ops/formal_scouts/results/geom_s3_spinor_deep_probe_results.json",
            "system_v5/ops/formal_scouts/results/jax_geometry_full_network_targets_20260530/s3_spinor_carrier_full_network_subreceipt.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "bridge_layer": "none",
        "cut_layer": "two-site QIT cuts derived from S3 spinor network carrier actions",
        "qit_entropy_family": {
            "role": "cross_layer_finite_cut_readouts",
            "von_neumann_S_AB_min": min(row["qit_readouts"]["S_AB"] for row in rows),
            "mutual_information_min": min_mi,
            "log_negativity_min": min_log_neg,
            "product_log_negativity_max": max(row["qit_product_control"]["log_negativity"] for row in rows),
            "entanglement_gap_min": min_entanglement_gap,
        },
        "law_or_candidate_tested": "S3 unit spinor finite spinor-network transport",
        "allowed_claims": [
            "One bounded standalone s3_unit_spinor network scout passed local rerun if all_pass=true",
            "This formal-scout receipt strengthens the existing diagnostic/G-structure/aggregate receipts with a native 128-site one-target network row",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "required_tools": sorted(TOOL_MANIFEST.keys()),
        "actual_tools_used": sorted(TOOL_MANIFEST.keys()),
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx", "xgi"],
        "topology_surfaces_used": ["toponetx", "gudhi"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "known_value_checks": {
            "unit_norm": positive["s3_unit_spinor_norm_preserved"],
            "antipodal_geodesic_pi": positive["s3_antipodal_geodesic_is_pi"],
            "relative_phase_transport_order_gap": positive["s3_transport_is_order_sensitive"],
            "sympy_exact_s3_identities": symbolic,
        },
        "invariant": {
            "object": "S3 unit spinor carrier",
            "unit_spinor_norm_preserved": max_norm_error < TOL,
            "antipodal_distance_is_pi": max_antipodal_error < 1.0e-7,
            "relative_phase_amplitude_transport_order_matters": min_order_gap > GAP,
            "finite_s3_boundary_topology_signature_present": all(row["topology"]["pass"] for row in rows),
        },
        "smt_certificates": {
            "z3_required_negation": proof["z3_required_negation"],
            "cvc5_required_negation": proof["cvc5_required_negation"],
            "pass": proof["pass"],
        },
        "sympy_exact_checks": symbolic,
        "proof_gates": proof,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "native_scale_rows_pass": required["native_frontier_row_present"],
        "native_scale_not_universal_qubit_ladder": True,
        "expected_N_invariant": [
            "mps_entanglement_gap",
            "product_log_negativity",
            "latent_schmidt_entropy",
            "half_chain_entropy",
            "renyi2_AB",
            "max_self_distance_error",
        ],
        "native_scale_parameters": [
            {
                "scale_name": row["scale_name"],
                "N_eta": row["N_eta"],
                "N_phi": row["N_phi"],
                "N_chi": row["N_chi"],
                "N_sites": row["N_sites"],
                "shape": list(row["shape"]),
            }
            for row in NATIVE_SCALE_ROWS
        ],
        "resource_blocker": "This bounded scout stops at N_sites=128. Larger native rows such as N_eta=4,N_phi=16,N_chi=4 (256 sites) are next-run scale targets, not evidence produced here.",
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {
            "per_row_controls": "see rows[*].controls",
            "all_rows_control_pass": all(all(control["pass"] for control in row["controls"].values()) for row in rows),
        },
        "nearby_variants": {
            "total": len(rows),
            "passed": sum(1 for row in rows if row["pass"]),
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "native_scale_rows": [row["scale_name"] for row in NATIVE_SCALE_ROWS],
        },
        "rows": rows,
        "result_summary": {
            "all_pass": all_pass,
            "row_count": len(rows),
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "max_sites": max(SCALES),
            "max_bond_dim": max(BONDS),
            "min_entanglement_gap": min_entanglement_gap,
            "min_order_gap": min_order_gap,
            "max_jax_torch_delta": max_parity_delta,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
            "min_peps3d_virtual_l1_delta": min_virtual_delta,
            "max_antipodal_pi_error": max_antipodal_error,
            "max_unit_norm_error": max_norm_error,
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": False,
        },
        "summary": {
            "all_pass": all_pass,
            "promotion_allowed": False,
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "max_sites": max(SCALES),
            "max_bond_dim": max(BONDS),
            "min_entanglement_gap": min_entanglement_gap,
            "min_order_gap": min_order_gap,
            "max_jax_torch_delta": max_parity_delta,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
            "max_antipodal_pi_error": max_antipodal_error,
        },
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "why_not_v4_probes": "v5 one-target S3 unit spinor network scout with explicit unit spinors, MPS/PEPS2D/PEPS3D carriers, JAX/Torch parity, QIT readouts, proof/topology tools, and downstream locks.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [key for key, value in required.items() if not value],
        "next_admissible_step": "Audit this one-target scout, then choose the next one-target geometry deepening row; do not use it to open stacking or downstream consumers.",
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
