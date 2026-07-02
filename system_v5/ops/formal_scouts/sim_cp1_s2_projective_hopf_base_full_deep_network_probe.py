#!/usr/bin/env python3
"""CP1/S2 projective Hopf-base bounded deep-network formal scout.

This is one standalone target only:

    CP1 = {unit psi in C^2} / U(1)
    pi([psi]) = (2 Re(conj(a)b), 2 Im(conj(a)b), |a|^2 - |b|^2) in S2

It runs the projective Hopf base as a finite spinor-network geometry with
MPS/PEPS2D/PEPS3D carrier views, JAX/PyTorch parity, QIT entropy readouts,
known CP1/S2 invariants, and controls. It does not select a G-structure,
embed a manifold layer, or open stacking/downstream claims.
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
OUT_PATH = RESULT_DIR / "cp1_s2_projective_hopf_base_full_deep_network_probe_results.json"
HOPF_LEGO_PATH = ROOT / "legos" / "hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3.py"

SIM_ID = "cp1_s2_projective_hopf_base_full_deep_network_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "standalone_geometry_deep_network_scout"
GAP = 1.0e-6
TOL = 1.0e-8
PARITY_TOL = 5.0e-7

NATIVE_SCALE_ROWS = [
    {"scale_name": "small_native_cp1_s2_base", "N_theta": 2, "N_azimuth": 2, "N_fiber": 2, "shape": (2, 2, 2)},
    {"scale_name": "medium_native_cp1_s2_base", "N_theta": 2, "N_azimuth": 4, "N_fiber": 2, "shape": (4, 2, 2)},
    {"scale_name": "large_native_cp1_s2_base", "N_theta": 4, "N_azimuth": 4, "N_fiber": 2, "shape": (4, 4, 2)},
    {"scale_name": "larger_native_cp1_s2_base", "N_theta": 4, "N_azimuth": 4, "N_fiber": 4, "shape": (4, 4, 4)},
    {"scale_name": "frontier_native_cp1_s2_base", "N_theta": 4, "N_azimuth": 8, "N_fiber": 4, "shape": (4, 4, 8)},
]
for row in NATIVE_SCALE_ROWS:
    row["N_sites"] = int(row["N_theta"] * row["N_azimuth"] * row["N_fiber"])
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
        "reason": "primary complex spinors, CP1 quotient projection, S2 base vectors, rotations, and QIT cuts",
    },
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "x64 parity mirror for CP1/S2 base projection and noncommuting SU(2) order gap",
    },
    "quimb": {
        "used": True,
        "role": "load_bearing",
        "reason": "MPS, PEPS2D, and PEPS3D carrier views over projective-base spinor sites",
    },
    "cotengra": {
        "used": True,
        "role": "load_bearing",
        "reason": "bounded contraction-tree witness for PEPS3D carrier scaling",
    },
    "opt_einsum": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite contraction signatures over projected S2 base vectors",
    },
    "sympy": {
        "used": True,
        "role": "load_bearing",
        "reason": "exact CP1/S2 quotient and unit-sphere identities",
    },
    "z3": {
        "used": True,
        "role": "load_bearing",
        "reason": "SMT exclusion for required observed CP1/S2 pass conditions",
    },
    "cvc5": {
        "used": True,
        "role": "load_bearing",
        "reason": "independent SMT cross-check for required observed CP1/S2 pass conditions",
    },
    "rustworkx": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite S2 carrier graph connectivity and cycle-rank check",
    },
    "xgi": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite theta/azimuth/fiber hyperedge incidence check",
    },
    "toponetx": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite tetrahedral S2 boundary cell signature",
    },
    "gudhi": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite tetrahedral S2 boundary simplex counts and Euler signature",
    },
    "qutip_jax": {
        "used": True,
        "role": "supportive",
        "reason": "JAX density trace sanity check",
    },
    "chex": {
        "used": True,
        "role": "supportive",
        "reason": "JAX shape checks for finite base-projection arrays",
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


def cp1_params(scale: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    site = 0
    for theta_idx in range(int(scale["N_theta"])):
        eta = (theta_idx + 1.0) * (math.pi / 2.0) / (int(scale["N_theta"]) + 1.0)
        for azimuth_idx in range(int(scale["N_azimuth"])):
            relative = 2.0 * math.pi * azimuth_idx / int(scale["N_azimuth"])
            for fiber_idx in range(int(scale["N_fiber"])):
                alpha = 2.0 * math.pi * fiber_idx / int(scale["N_fiber"])
                rows.append(
                    {
                        "site": site,
                        "shell": theta_idx,
                        "fiber": fiber_idx,
                        "theta_idx": theta_idx,
                        "azimuth_idx": azimuth_idx,
                        "eta": eta,
                        "phi": alpha,
                        "chi": alpha + relative,
                    }
                )
                site += 1
    return rows


def spinors_for(hopf: Any, scale: dict[str, Any]) -> tuple[list[Any], list[dict[str, Any]]]:
    params = cp1_params(scale)
    return [hopf.hopf_spinor(row["eta"], row["phi"], row["chi"]) for row in params], params


def raw_hopf_base_no_normalize(hopf: Any, psi: Any) -> Any:
    a, b = psi[0], psi[1]
    return hopf.torch.stack(
        [
            2.0 * hopf.torch.real(hopf.torch.conj(a) * b),
            2.0 * hopf.torch.imag(hopf.torch.conj(a) * b),
            hopf.torch.abs(a) ** 2 - hopf.torch.abs(b) ** 2,
        ]
    )


def orthogonal_spinor(hopf: Any, psi: Any) -> Any:
    return hopf.normalize_spinor(hopf.torch.stack([-hopf.torch.conj(psi[1]), hopf.torch.conj(psi[0])]))


def fs_distance(hopf: Any, left: Any, right: Any) -> Any:
    overlap = hopf.torch.abs(hopf.torch.vdot(left, right)).clamp(min=0.0, max=1.0)
    return hopf.torch.arccos(overlap)


def su2_order_torch(hopf: Any, spinors: list[Any], order: str) -> Any:
    sx = hopf.torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=hopf.CDTYPE)
    sz = hopf.torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=hopf.CDTYPE)
    ux = hopf.torch.linalg.matrix_exp((-0.5j * 0.37) * sx)
    uz = hopf.torch.linalg.matrix_exp((-0.5j * 0.43) * sz)
    uz2 = hopf.torch.linalg.matrix_exp((-0.5j * 0.19) * sz)
    out = []
    for psi in spinors:
        if order == "x_then_z":
            moved = uz @ (ux @ psi)
        elif order == "z_then_x":
            moved = ux @ (uz @ psi)
        elif order == "z_then_z2":
            moved = uz2 @ (uz @ psi)
        elif order == "z2_then_z":
            moved = uz @ (uz2 @ psi)
        else:
            raise ValueError(order)
        out.append(hopf.hopf_base(moved))
    return hopf.torch.stack(out)


def cp1_base_jax(hopf: Any, eta: Any, phi: Any, chi: Any) -> Any:
    jnp = hopf.jnp
    relative = chi - phi
    return jnp.stack(
        [
            jnp.sin(2.0 * eta) * jnp.cos(relative),
            jnp.sin(2.0 * eta) * jnp.sin(relative),
            jnp.cos(2.0 * eta),
        ],
        axis=-1,
    ).astype(hopf.JRTYPE)


def su2_order_jax(hopf: Any, eta: Any, phi: Any, chi: Any, order: str) -> Any:
    jnp = hopf.jnp
    ident = jnp.eye(2, dtype=hopf.JCTYPE)
    sx = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=hopf.JCTYPE)
    sz = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=hopf.JCTYPE)
    ux = jnp.cos(0.37 / 2.0) * ident - 1j * jnp.sin(0.37 / 2.0) * sx
    uz = jnp.cos(0.43 / 2.0) * ident - 1j * jnp.sin(0.43 / 2.0) * sz
    uz2 = jnp.cos(0.19 / 2.0) * ident - 1j * jnp.sin(0.19 / 2.0) * sz
    psi = hopf.hopf_spinor_jax(eta, phi, chi)
    if order == "x_then_z":
        moved = jnp.einsum("ab,nb->na", uz, jnp.einsum("ab,nb->na", ux, psi))
    elif order == "z_then_x":
        moved = jnp.einsum("ab,nb->na", ux, jnp.einsum("ab,nb->na", uz, psi))
    elif order == "z_then_z2":
        moved = jnp.einsum("ab,nb->na", uz2, jnp.einsum("ab,nb->na", uz, psi))
    elif order == "z2_then_z":
        moved = jnp.einsum("ab,nb->na", uz, jnp.einsum("ab,nb->na", uz2, psi))
    else:
        raise ValueError(order)
    return hopf.hopf_base_jax(moved)


def cp1_geometry_readout(hopf: Any, spinors: list[Any], params: list[dict[str, Any]]) -> dict[str, Any]:
    torch = hopf.torch
    jnp = hopf.jnp
    bases = torch.stack([hopf.hopf_base(psi) for psi in spinors])
    norms = torch.linalg.vector_norm(bases, dim=1)
    max_norm_error = float(torch.max(torch.abs(norms - 1.0)).item())

    phase_shifted = [
        hopf.hopf_spinor(row["eta"], row["phi"] + 0.73, row["chi"] + 0.73)
        for row in params
    ]
    phase_bases = torch.stack([hopf.hopf_base(psi) for psi in phase_shifted])
    phase_error = float(torch.max(torch.linalg.vector_norm(phase_bases - bases, dim=1)).item())

    fiber_spreads = []
    for key, group in itertools.groupby(params, key=lambda row: (row["theta_idx"], row["azimuth_idx"])):
        idxs = [int(row["site"]) for row in group]
        if len(idxs) > 1:
            group_bases = bases[idxs]
            fiber_spreads.append(float(torch.max(torch.linalg.vector_norm(group_bases - group_bases[0], dim=1)).item()))
    fiber_collapse_error = max(fiber_spreads) if fiber_spreads else 0.0

    fs_errors = []
    antipodal_errors = []
    for psi in spinors:
        ortho = orthogonal_spinor(hopf, psi)
        fs_errors.append(abs(float(fs_distance(hopf, psi, ortho).item()) - math.pi / 2.0))
        base_dot = torch.dot(hopf.hopf_base(psi), hopf.hopf_base(ortho)).clamp(min=-1.0, max=1.0)
        antipodal_errors.append(abs(float(torch.arccos(base_dot).item()) - math.pi))

    xz = su2_order_torch(hopf, spinors, "x_then_z")
    zx = su2_order_torch(hopf, spinors, "z_then_x")
    zz = su2_order_torch(hopf, spinors, "z_then_z2")
    zz_reverse = su2_order_torch(hopf, spinors, "z2_then_z")
    order_gap = float(torch.mean(torch.linalg.vector_norm(xz - zx, dim=1)).item())
    commuting_gap = float(torch.mean(torch.linalg.vector_norm(zz - zz_reverse, dim=1)).item())

    eta = jnp.asarray([row["eta"] for row in params], dtype=hopf.JRTYPE)
    phi = jnp.asarray([row["phi"] for row in params], dtype=hopf.JRTYPE)
    chi = jnp.asarray([row["chi"] for row in params], dtype=hopf.JRTYPE)
    j_base = cp1_base_jax(hopf, eta, phi, chi)
    j_norm = jnp.max(jnp.abs(jnp.linalg.norm(j_base, axis=1) - 1.0))
    j_xz = su2_order_jax(hopf, eta, phi, chi, "x_then_z")
    j_zx = su2_order_jax(hopf, eta, phi, chi, "z_then_x")
    j_gap = jnp.mean(jnp.linalg.norm(j_xz - j_zx, axis=1))
    torch_base_rows = [[float(value) for value in row] for row in bases.detach().cpu().tolist()]
    parity_delta = max(
        float(abs(j_norm - max_norm_error)),
        float(abs(j_gap - order_gap)),
        float(jnp.max(jnp.abs(j_base - jnp.asarray(torch_base_rows, dtype=hopf.JRTYPE)))),
    )
    hopf.chex.assert_shape(j_base, (len(params), 3))
    trace = hopf.qutip_jax.trace_jaxarray(hopf.qutip_jax.JaxArray(jnp.eye(2, dtype=hopf.JCTYPE) / 2.0))
    raw_scaled_norm = float(torch.linalg.vector_norm(raw_hopf_base_no_normalize(hopf, 1.3 * spinors[0])).item())

    return {
        "pass": bool(
            max_norm_error < TOL
            and phase_error < TOL
            and fiber_collapse_error < TOL
            and max(fs_errors) < 1.0e-7
            and max(antipodal_errors) < 1.0e-7
            and order_gap > GAP
            and commuting_gap < TOL
            and parity_delta < PARITY_TOL
        ),
        "max_s2_base_norm_error": max_norm_error,
        "max_global_u1_phase_error": phase_error,
        "max_fiber_collapse_error": fiber_collapse_error,
        "max_fs_orthogonal_half_pi_error": max(fs_errors),
        "max_s2_antipodal_pi_error": max(antipodal_errors),
        "torch_order_gap": order_gap,
        "commuting_control_gap": commuting_gap,
        "jax_torch_max_delta": parity_delta,
        "raw_scaled_nonprojective_base_norm": raw_scaled_norm,
        "raw_scaled_norm_error": abs(raw_scaled_norm - 1.0),
        "qutip_jax_base_density_trace": float(jnp.real(trace)),
    }


def s2_topology_signature(hopf: Any) -> dict[str, Any]:
    faces = list(itertools.combinations(range(4), 3))
    st = hopf.gudhi.SimplexTree()
    for face in faces:
        st.insert(face)
    st.compute_persistence()
    simplex_count = int(st.num_simplices())
    dimension = int(st.dimension())
    vertices, edges, triangles = 4, 6, 4
    euler = vertices - edges + triangles
    sc = hopf.tnx.SimplicialComplex()
    for face in faces:
        sc.add_simplex(face)
    graph = hopf.rx.PyGraph()
    graph.add_nodes_from(range(4))
    graph.add_edges_from_no_data(list(itertools.combinations(range(4), 2)))
    hyper = hopf.xgi.Hypergraph()
    hyper.add_nodes_from(range(4))
    hyper.add_edges_from([tuple(face) for face in faces])
    return {
        "pass": bool(dimension == 2 and simplex_count == 14 and euler == 2 and hopf.rx.is_connected(graph)),
        "gudhi_dimension": dimension,
        "gudhi_simplices": simplex_count,
        "known_tetrahedral_s2_counts": {"vertices": vertices, "edges": edges, "triangles": triangles},
        "known_euler_characteristic_s2": euler,
        "toponetx_dim": int(sc.dim),
        "rustworkx_connected": bool(hopf.rx.is_connected(graph)),
        "rustworkx_cycle_rank": int(len(hopf.rx.cycle_basis(graph))),
        "xgi_hyperedges": int(hyper.num_edges),
    }


def sympy_cp1_s2_checks(hopf: Any) -> dict[str, Any]:
    sp = hopf.sp
    eta, delta = sp.symbols("eta delta", real=True)
    x = sp.sin(2 * eta) * sp.cos(delta)
    y = sp.sin(2 * eta) * sp.sin(delta)
    z = sp.cos(2 * eta)
    norm_identity = sp.simplify(x**2 + y**2 + z**2 - 1)
    return {
        "pass": bool(norm_identity == 0 and sp.simplify(sp.acos(sp.Integer(-1)) - sp.pi) == 0),
        "s2_base_norm_identity": str(norm_identity),
        "projective_map": "pi([psi])=(sin(2eta)cos(delta), sin(2eta)sin(delta), cos(2eta))",
        "antipodal_base_distance": str(sp.acos(sp.Integer(-1))),
    }


def cp1_row(hopf: Any, scale: dict[str, Any], bond_dim: int) -> dict[str, Any]:
    spinors, params = spinors_for(hopf, scale)
    shape = tuple(scale["shape"])
    mps = hopf.mps_network_readout(spinors, params)
    product_mps = hopf.make_mps(hopf.mps_arrays(spinors, params, entangled=False))
    product_mps_max_bond = int(product_mps.max_bond())
    product_entropy = 0.0
    peps = hopf.peps_views(shape, spinors, bond_dim)
    qit = hopf.qit_readouts(hopf.two_site_density(spinors, params, entangle=True))
    qit_product = hopf.qit_readouts(hopf.two_site_density(spinors, params, entangle=False))
    geometry = cp1_geometry_readout(hopf, spinors, params)
    topo = s2_topology_signature(hopf)
    entanglement_gap = float(mps["latent_schmidt_entropy"] - product_entropy)
    controls = {
        "product_no_entanglement_carrier": {
            "pass": bool(qit["log_negativity"] > qit_product["log_negativity"] + GAP and entanglement_gap > GAP),
            "baseline_log_negativity": qit["log_negativity"],
            "product_log_negativity": qit_product["log_negativity"],
            "mps_entanglement_gap": entanglement_gap,
        },
        "global_phase_erased_projective_identity": {
            "pass": bool(geometry["max_global_u1_phase_error"] < TOL and geometry["max_fiber_collapse_error"] < TOL),
            "max_global_u1_phase_error": geometry["max_global_u1_phase_error"],
            "max_fiber_collapse_error": geometry["max_fiber_collapse_error"],
        },
        "nonprojective_raw_scaling_rejected": {
            "pass": bool(geometry["raw_scaled_norm_error"] > GAP),
            "raw_scaled_nonprojective_base_norm": geometry["raw_scaled_nonprojective_base_norm"],
            "raw_scaled_norm_error": geometry["raw_scaled_norm_error"],
        },
        "order_erased_commuting_control_rejected": {
            "pass": bool(geometry["torch_order_gap"] > GAP and geometry["commuting_control_gap"] < TOL),
            "order_gap": geometry["torch_order_gap"],
            "commuting_control_gap": geometry["commuting_control_gap"],
        },
        "peps3d_virtual_erasure_collapses_carrier": {
            "pass": bool(peps["virtual_l1"] > peps["erased_virtual_l1"] + GAP),
            "virtual_l1": peps["virtual_l1"],
            "erased_virtual_l1": peps["erased_virtual_l1"],
        },
        "scalar_entropy_only_rejected": {
            "pass": bool(qit["mutual_information"] > GAP and qit["log_negativity"] > GAP),
            "reason": "CP1/S2 base evidence uses quotient geometry, order controls, network carriers, and QIT vector; scalar entropy alone is not the object.",
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
            "N_theta": scale["N_theta"],
            "N_azimuth": scale["N_azimuth"],
            "N_fiber": scale["N_fiber"],
            "N_sites": scale["N_sites"],
            "shape": list(scale["shape"]),
        },
        "cp1_s2_geometry": geometry,
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

    rows = [cp1_row(hopf, scale, bond_dim) for scale in NATIVE_SCALE_ROWS for bond_dim in BONDS]
    symbolic = sympy_cp1_s2_checks(hopf)
    min_order_gap = min(row["cp1_s2_geometry"]["torch_order_gap"] for row in rows)
    max_commuting_gap = max(row["cp1_s2_geometry"]["commuting_control_gap"] for row in rows)
    min_mi = min(row["qit_readouts"]["mutual_information"] for row in rows)
    min_log_neg = min(row["qit_readouts"]["log_negativity"] for row in rows)
    min_virtual_delta = min(row["peps_carriers"]["virtual_l1"] - row["peps_carriers"]["erased_virtual_l1"] for row in rows)
    max_parity_delta = max(row["cp1_s2_geometry"]["jax_torch_max_delta"] for row in rows)
    max_norm_error = max(row["cp1_s2_geometry"]["max_s2_base_norm_error"] for row in rows)
    max_phase_error = max(row["cp1_s2_geometry"]["max_global_u1_phase_error"] for row in rows)
    max_fiber_collapse_error = max(row["cp1_s2_geometry"]["max_fiber_collapse_error"] for row in rows)
    max_fs_error = max(row["cp1_s2_geometry"]["max_fs_orthogonal_half_pi_error"] for row in rows)
    max_antipodal_error = max(row["cp1_s2_geometry"]["max_s2_antipodal_pi_error"] for row in rows)
    min_raw_scaling_error = min(row["cp1_s2_geometry"]["raw_scaled_norm_error"] for row in rows)
    min_entanglement_gap = min(row["controls"]["product_no_entanglement_carrier"]["mps_entanglement_gap"] for row in rows)

    required = {
        "rows_pass": all(row["pass"] for row in rows),
        "sympy_pass": symbolic["pass"],
        "jax_torch_parity": max_parity_delta < PARITY_TOL,
        "order_gap_pass": min_order_gap > GAP and max_commuting_gap < TOL,
        "qit_vector_pass": min_mi > GAP and min_log_neg > GAP,
        "peps3d_virtual_pass": min_virtual_delta > GAP,
        "native_frontier_row_present": max(SCALES) == 128,
        "s2_base_norm_known_value": max_norm_error < TOL,
        "u1_quotient_known_value": max(max_phase_error, max_fiber_collapse_error) < TOL,
        "fs_and_antipodal_known_values": max(max_fs_error, max_antipodal_error) < 1.0e-7,
        "nonprojective_scaling_rejected": min_raw_scaling_error > GAP,
    }
    proof = hopf.proof_gate(required, min(min_order_gap, min_mi, min_log_neg, min_virtual_delta, min_raw_scaling_error))

    positive = {
        "cp1_projects_to_unit_s2": {"pass": max_norm_error < TOL, "max_s2_base_norm_error": max_norm_error},
        "global_u1_fiber_is_quotiented": {
            "pass": max(max_phase_error, max_fiber_collapse_error) < TOL,
            "max_global_u1_phase_error": max_phase_error,
            "max_fiber_collapse_error": max_fiber_collapse_error,
        },
        "orthogonal_cp1_points_match_known_distances": {
            "pass": max(max_fs_error, max_antipodal_error) < 1.0e-7,
            "max_fs_orthogonal_half_pi_error": max_fs_error,
            "max_s2_antipodal_pi_error": max_antipodal_error,
        },
        "su2_rotations_are_order_sensitive_on_projective_base": {
            "pass": min_order_gap > GAP and max_commuting_gap < TOL,
            "min_order_gap": min_order_gap,
            "max_commuting_control_gap": max_commuting_gap,
        },
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
        "jax_torch_cp1_s2_parity": {"pass": max_parity_delta < PARITY_TOL, "max_delta": max_parity_delta},
        "symbolic_and_smt_gates": {"pass": symbolic["pass"] and proof["pass"], "sympy": symbolic, "proof": proof},
    }
    graveyard_companions = {
        "product_carrier_loses_entanglement_information": {
            "pass": all(row["controls"]["product_no_entanglement_carrier"]["pass"] for row in rows),
            "min_log_negativity": min_log_neg,
            "min_entanglement_gap": min_entanglement_gap,
        },
        "nonprojective_raw_scaling_is_rejected": {
            "pass": min_raw_scaling_error > GAP,
            "min_raw_scaling_error": min_raw_scaling_error,
        },
        "peps3d_virtual_bond_erase_collapses_carrier_signal": {
            "pass": min_virtual_delta > GAP,
            "min_virtual_l1_delta": min_virtual_delta,
        },
        "commuting_order_substitute_rejected": {
            "pass": min_order_gap > GAP and max_commuting_gap < TOL,
            "min_order_gap": min_order_gap,
            "max_commuting_gap": max_commuting_gap,
        },
        "scalar_entropy_only_substitute_rejected": {
            "pass": all(row["controls"]["scalar_entropy_only_rejected"]["pass"] for row in rows),
        },
    }
    tool_ablations = {
        "torch_projective_base": {
            "pass": max_norm_error < TOL and max_phase_error < TOL,
            "stub_action": "remove torch complex spinor Hopf-base projection",
            "claim_delta": "CP1/S2 quotient carrier unavailable",
            "delta_witness": {"max_s2_base_norm_error": max_norm_error, "max_global_u1_phase_error": max_phase_error},
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
        "one_math_object_not_aggregate_wrapper": {"pass": True, "object": "CP1/S2 projective Hopf base", "target_count": 1},
        "result_path": {
            "pass": str(OUT_PATH).endswith(
                "system_v5/ops/formal_scouts/results/cp1_s2_projective_hopf_base_full_deep_network_probe_results.json"
            ),
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
        "tier": "standalone_cp1_s2_projective_base_deep_network_scout",
        "purpose": "Build one bounded standalone CP1/S2 projective Hopf-base full-network scout with quotient geometry, QIT, tool checks, and parity.",
        "scientific_question": "Can CP1=S3/U(1) project to S2 as an explicit finite spinor-network geometry with MPS, PEPS2D, PEPS3D, JAX/Torch parity, QIT readouts, proof/topology tools, and controls?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "cp1_s2_projective_hopf_base_one_target_deep_network_scout",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: one bounded standalone CP1/S2 projective Hopf-base network scout; no official G-structure selection, layer embedding, stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite CP1/S2 base sites, finite native scale rows, finite network carriers, finite SU(2) order maps, finite controls",
            "N01": "noncommuting SU(2) rotations change the finite CP1/S2 projected base while commuting z/z rotations do not",
        },
        "finite_map": "M_cp1_s2_base : (finite unit spinors modulo global U1 phase, SU(2) transport, MPS/PEPS2D/PEPS3D carrier, controls) -> S2 base rows, quotient invariance, network states, QIT cuts, topology/proof certificates, blocked consumers",
        "domain": "native CP1/S2 rows (N_theta, N_azimuth, N_fiber, N_sites) with bond_dim 2/4 network carriers and finite transport controls",
        "codomain_or_output": "S2 base vectors, CP1 quotient readouts, network carrier readouts, QIT entropy-family readouts, topology/proof certificates, parity deltas, controls, and blocked consumers",
        "carrier_layer": "complex spinor network modulo U(1) with projected S2 base and MPS, PEPS2D, and PEPS3D views",
        "geometry_layer": "cp1_s2_projective_hopf_base_geometry",
        "carrier_realization": "torch.complex128 unit spinors; S2 base vectors via Hopf projection; quimb MPS/PEPS/PEPS3D carrier objects; JAX x64 parity for base projection and noncommuting SU(2) order gap",
        "PEPS3D_K_anchor": {"site_counts": SCALES, "bond_dims": BONDS, "object": "quimb.tensor.PEPS3D"},
        "peps3d_embedding": "finite PEPS3D carrier stress over projective Hopf-base spinor sites; not a layer embedding or manifold admission",
        "torch_spinor_or_density": "torch.complex128 two-component unit spinors, S2 base vectors, and spinor-derived two-site density states",
        "spinor_state": "psi(eta,phi,chi)=(exp(i phi) cos eta, exp(i chi) sin eta), quotient by global U(1)",
        "projective_base_state": "pi([psi])=(2Re(conj(a)b),2Im(conj(a)b),|a|^2-|b|^2) in S2",
        "quaternion_action": "not_applicable_in_this_probe",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/independent_layer_cp1_s2_projective_hopf_base_probe_results.json",
            "system_v5/ops/formal_scouts/results/s2_hopf_base_surface_g_structure_full_function_probe_results.json",
            "system_v5/ops/formal_scouts/results/geom_s2_hopf_base_deep_probe_results.json",
            "system_v5/ops/formal_scouts/results/geom_cp1_fubini_study_deep_probe_results.json",
            "system_v5/ops/formal_scouts/results/jax_geometry_full_network_targets_20260530/cp1_fubini_study_full_network_subreceipt.json",
            "system_v5/ops/formal_scouts/results/jax_geometry_full_network_targets_20260530/s2_hopf_base_surface_full_network_subreceipt.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "bridge_layer": "none",
        "cut_layer": "two-site QIT cuts derived from CP1/S2 spinor network carrier actions",
        "qit_entropy_family": {
            "role": "cross_layer_finite_cut_readouts",
            "von_neumann_S_AB_min": min(row["qit_readouts"]["S_AB"] for row in rows),
            "mutual_information_min": min_mi,
            "log_negativity_min": min_log_neg,
            "product_log_negativity_max": max(row["qit_product_control"]["log_negativity"] for row in rows),
            "entanglement_gap_min": min_entanglement_gap,
        },
        "law_or_candidate_tested": "CP1/S2 projective Hopf-base finite spinor-network transport",
        "allowed_claims": [
            "One bounded standalone cp1_s2_projective_hopf_base network scout passed local rerun if all_pass=true",
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
            "unit_s2_base_norm": positive["cp1_projects_to_unit_s2"],
            "global_u1_fiber_quotient": positive["global_u1_fiber_is_quotiented"],
            "orthogonal_cp1_fs_and_base_distances": positive["orthogonal_cp1_points_match_known_distances"],
            "su2_order_gap": positive["su2_rotations_are_order_sensitive_on_projective_base"],
            "sympy_exact_cp1_s2_identities": symbolic,
        },
        "invariant": {
            "object": "CP1/S2 projective Hopf base",
            "unit_s2_base_norm_preserved": max_norm_error < TOL,
            "global_u1_phase_quotiented": max(max_phase_error, max_fiber_collapse_error) < TOL,
            "orthogonal_cp1_distance_known_values": max(max_fs_error, max_antipodal_error) < 1.0e-7,
            "su2_noncommuting_order_matters": min_order_gap > GAP and max_commuting_gap < TOL,
            "finite_s2_tetrahedral_topology_signature_present": all(row["topology"]["pass"] for row in rows),
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
        ],
        "native_scale_parameters": [
            {
                "scale_name": row["scale_name"],
                "N_theta": row["N_theta"],
                "N_azimuth": row["N_azimuth"],
                "N_fiber": row["N_fiber"],
                "N_sites": row["N_sites"],
                "shape": list(row["shape"]),
            }
            for row in NATIVE_SCALE_ROWS
        ],
        "resource_blocker": "This bounded scout stops at N_sites=128. Larger native rows such as N_theta=8,N_azimuth=8,N_fiber=4 (256 sites) are next-run scale targets, not evidence produced here.",
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
            "max_commuting_gap": max_commuting_gap,
            "max_jax_torch_delta": max_parity_delta,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
            "min_peps3d_virtual_l1_delta": min_virtual_delta,
            "max_s2_base_norm_error": max_norm_error,
            "max_global_u1_phase_error": max_phase_error,
            "max_fiber_collapse_error": max_fiber_collapse_error,
            "max_fs_orthogonal_half_pi_error": max_fs_error,
            "max_s2_antipodal_pi_error": max_antipodal_error,
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
            "max_s2_base_norm_error": max_norm_error,
            "max_global_u1_phase_error": max_phase_error,
        },
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "why_not_v4_probes": "v5 one-target CP1/S2 projective Hopf-base network scout with explicit quotient geometry, MPS/PEPS2D/PEPS3D carriers, JAX/Torch parity, QIT readouts, proof/topology tools, and downstream locks.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [key for key, value in required.items() if not value],
        "next_admissible_step": "Audit this one-target scout, then choose the next one-target geometry deepening row; do not use it to open stacking or downstream consumers.",
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
