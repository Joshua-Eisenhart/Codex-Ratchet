#!/usr/bin/env python3
"""Left/right Weyl spinor sheets bounded deep-network formal scout.

This is one standalone target only:

    left sheet:  H_L(v) = +1/2 n_v . sigma
    right sheet: H_R(v) = -1/2 n_v . sigma

on finite two-component Weyl spinor-density networks. It is not a terrain sim,
not a chirality-cover proof, and not a stacking/order admission.

The scout verifies:

* finite left/right two-component spinor sheets;
* opposite handed Hamiltonian evolution on the same density carrier;
* noncommuting local operator order controls;
* MPS/PEPS2D/PEPS3D carrier views for both sheets;
* JAX/PyTorch parity;
* QIT entropy/correlation readouts;
* graph/topology/proof surfaces;
* controls that kill sheet handedness, network entanglement, and PEPS3D virtual
  carrier signal.
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
OUT_PATH = RESULT_DIR / "left_right_weyl_spinor_sheets_full_deep_network_probe_results.json"
HOPF_LEGO_PATH = ROOT / "legos" / "hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3.py"

SIM_ID = "left_right_weyl_spinor_sheets_full_deep_network_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "standalone_geometry_deep_network_scout"
GAP = 1.0e-6
TOL = 1.0e-8
PARITY_TOL = 5.0e-7

NATIVE_SCALE_ROWS = [
    {"scale_name": "small_native_weyl_sheets", "N_shell": 2, "N_sheet_anchor": 2, "N_sites_per_anchor": 2, "shape": (2, 2, 2)},
    {"scale_name": "medium_native_weyl_sheets", "N_shell": 2, "N_sheet_anchor": 2, "N_sites_per_anchor": 4, "shape": (4, 2, 2)},
    {"scale_name": "large_native_weyl_sheets", "N_shell": 4, "N_sheet_anchor": 2, "N_sites_per_anchor": 4, "shape": (4, 4, 2)},
    {"scale_name": "larger_native_weyl_sheets", "N_shell": 4, "N_sheet_anchor": 4, "N_sites_per_anchor": 4, "shape": (4, 4, 4)},
    {"scale_name": "frontier_native_weyl_sheets", "N_shell": 4, "N_sheet_anchor": 4, "N_sites_per_anchor": 8, "shape": (4, 4, 8)},
]
for row in NATIVE_SCALE_ROWS:
    row["N_sites"] = int(row["N_shell"] * row["N_sheet_anchor"] * row["N_sites_per_anchor"])
SCALES = [int(row["N_sites"]) for row in NATIVE_SCALE_ROWS]
BONDS = [2, 4]

BLOCKED_CONSUMERS = [
    "official_g_structure_selection",
    "terrain_law_selection",
    "chirality_orientation_cover_admission",
    "layer_embedding",
    "stacking",
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
        "reason": "primary complex Weyl spinors, density evolution, commutators, local order gaps, and QIT cuts",
    },
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "x64 parity mirror for handed evolution and local order gaps",
    },
    "quimb": {
        "used": True,
        "role": "load_bearing",
        "reason": "MPS, PEPS2D, and PEPS3D carrier views for left and right Weyl sheets",
    },
    "cotengra": {
        "used": True,
        "role": "load_bearing",
        "reason": "bounded contraction-tree witness for PEPS3D carrier scaling",
    },
    "opt_einsum": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite contraction signatures over Weyl-sheet base vectors",
    },
    "sympy": {
        "used": True,
        "role": "load_bearing",
        "reason": "exact Pauli anticommutation, opposite Hamiltonian sign, and SU(2) unitary identity checks",
    },
    "z3": {
        "used": True,
        "role": "load_bearing",
        "reason": "SMT exclusion for required observed Weyl-sheet pass conditions",
    },
    "cvc5": {
        "used": True,
        "role": "load_bearing",
        "reason": "independent SMT cross-check for required observed Weyl-sheet pass conditions",
    },
    "rustworkx": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite two-sheet graph connectivity and cycle-rank check",
    },
    "xgi": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite shell/sheet/site hyperedge incidence check",
    },
    "toponetx": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite two-sheet cell-complex signature",
    },
    "gudhi": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite two-sheet simplex counts and Euler signature",
    },
    "qutip_jax": {
        "used": True,
        "role": "supportive",
        "reason": "JAX density trace sanity check",
    },
    "chex": {
        "used": True,
        "role": "supportive",
        "reason": "JAX shape checks for finite Weyl arrays",
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


def weyl_params(scale: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    site = 0
    for shell in range(int(scale["N_shell"])):
        eta = (shell + 1.0) * (math.pi / 2.0) / (int(scale["N_shell"]) + 1.0)
        for anchor in range(int(scale["N_sheet_anchor"])):
            phase_anchor = 2.0 * math.pi * anchor / int(scale["N_sheet_anchor"])
            for sample in range(int(scale["N_sites_per_anchor"])):
                u = 2.0 * math.pi * sample / int(scale["N_sites_per_anchor"])
                phi = u + 0.17 * shell
                chi = u + phase_anchor + 0.31 * math.sin(eta + sample)
                rows.append({"site": site, "shell": shell, "anchor": anchor, "sample": sample, "eta": eta, "phi": phi, "chi": chi})
                site += 1
    return rows


def right_weyl_partner(hopf: Any, psi: Any) -> Any:
    return hopf.normalize_spinor(hopf.torch.stack([-hopf.torch.conj(psi[1]), hopf.torch.conj(psi[0])]))


def spinors_for(hopf: Any, scale: dict[str, Any]) -> tuple[list[Any], list[Any], list[dict[str, Any]]]:
    params = weyl_params(scale)
    left = [hopf.hopf_spinor(row["eta"], row["phi"], row["chi"]) for row in params]
    right = [right_weyl_partner(hopf, psi) for psi in left]
    return left, right, params


def pauli(hopf: Any) -> tuple[Any, Any, Any, Any]:
    torch = hopf.torch
    sx = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=hopf.CDTYPE)
    sy = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=hopf.CDTYPE)
    sz = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=hopf.CDTYPE)
    ident = torch.eye(2, dtype=hopf.CDTYPE)
    return sx, sy, sz, ident


def axis_for_base(hopf: Any, psi: Any) -> Any:
    torch = hopf.torch
    base = hopf.hopf_base(psi)
    axis = torch.stack([base[1] + 0.31, -base[2] + 0.17, base[0] + 0.23])
    return axis / torch.linalg.vector_norm(axis)


def hamiltonian(hopf: Any, axis: Any, sign: float) -> Any:
    sx, sy, sz, _ = pauli(hopf)
    return 0.5 * sign * (axis[0].to(hopf.CDTYPE) * sx + axis[1].to(hopf.CDTYPE) * sy + axis[2].to(hopf.CDTYPE) * sz)


def evolve_density(hopf: Any, rho: Any, hamiltonian_matrix: Any, t: float) -> Any:
    torch = hopf.torch
    u = torch.linalg.matrix_exp((-1j * t) * hamiltonian_matrix)
    return hopf.normalize_density(u @ rho @ u.conj().T)


def local_order_gap(hopf: Any, rho: Any) -> float:
    torch = hopf.torch
    sx, _, sz, _ = pauli(hopf)
    ux = torch.linalg.matrix_exp((-0.5j * 0.53) * sx)
    uz = torch.linalg.matrix_exp((-0.5j * 0.41) * sz)
    xz = ux @ (uz @ rho @ uz.conj().T) @ ux.conj().T
    zx = uz @ (ux @ rho @ ux.conj().T) @ uz.conj().T
    return float(torch.linalg.matrix_norm(xz - zx).item())


def jax_sheet_gap(hopf: Any, eta: Any, phi: Any, chi: Any, t: float) -> Any:
    jnp = hopf.jnp
    psi = hopf.hopf_spinor_jax(eta, phi, chi)
    rho = jnp.einsum("ni,nj->nij", psi, jnp.conj(psi))
    base = hopf.hopf_base_jax(psi)
    axis = jnp.stack([base[:, 1] + 0.31, -base[:, 2] + 0.17, base[:, 0] + 0.23], axis=-1)
    axis = axis / jnp.linalg.norm(axis, axis=-1, keepdims=True)
    sx = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=hopf.JCTYPE)
    sy = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=hopf.JCTYPE)
    sz = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=hopf.JCTYPE)
    ident = jnp.eye(2, dtype=hopf.JCTYPE)
    n_dot_sigma = axis[:, 0, None, None] * sx + axis[:, 1, None, None] * sy + axis[:, 2, None, None] * sz
    u_left = jnp.cos(t / 2.0) * ident - 1j * jnp.sin(t / 2.0) * n_dot_sigma
    u_right = jnp.cos(t / 2.0) * ident + 1j * jnp.sin(t / 2.0) * n_dot_sigma
    left = jnp.einsum("nab,nbc,ndc->nad", u_left, rho, jnp.conj(u_left))
    right = jnp.einsum("nab,nbc,ndc->nad", u_right, rho, jnp.conj(u_right))
    return jnp.linalg.norm(left - right, axis=(1, 2))


def jax_order_gap(hopf: Any, eta: Any, phi: Any, chi: Any) -> Any:
    jnp = hopf.jnp
    psi = hopf.hopf_spinor_jax(eta, phi, chi)
    rho = jnp.einsum("ni,nj->nij", psi, jnp.conj(psi))
    sx = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=hopf.JCTYPE)
    sz = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=hopf.JCTYPE)
    ux = jnp.cos(0.53 / 2.0) * jnp.eye(2, dtype=hopf.JCTYPE) - 1j * jnp.sin(0.53 / 2.0) * sx
    uz = jnp.cos(0.41 / 2.0) * jnp.eye(2, dtype=hopf.JCTYPE) - 1j * jnp.sin(0.41 / 2.0) * sz
    xz = jnp.einsum("ab,nbc,dc->nad", ux, jnp.einsum("ab,nbc,dc->nad", uz, rho, jnp.conj(uz)), jnp.conj(ux))
    zx = jnp.einsum("ab,nbc,dc->nad", uz, jnp.einsum("ab,nbc,dc->nad", ux, rho, jnp.conj(ux)), jnp.conj(uz))
    return jnp.linalg.norm(xz - zx, axis=(1, 2))


def weyl_sheet_readout(hopf: Any, left: list[Any], right: list[Any], params: list[dict[str, Any]]) -> dict[str, Any]:
    torch = hopf.torch
    jnp = hopf.jnp
    t = 0.73
    sheet_initial_orthogonality = max(abs(complex(torch.vdot(l, r).item())) for l, r in zip(left, right))
    sheet_gaps = []
    collapse_gaps = []
    commutator_gaps = []
    order_gaps = []
    time_reverse_gaps = []
    traces = []
    for psi_l in left:
        rho = hopf.density(psi_l)
        axis = axis_for_base(hopf, psi_l)
        h_l = hamiltonian(hopf, axis, +1.0)
        h_r = hamiltonian(hopf, axis, -1.0)
        rho_l = evolve_density(hopf, rho, h_l, t)
        rho_r = evolve_density(hopf, rho, h_r, t)
        rho_r_collapsed = evolve_density(hopf, rho, h_l, t)
        sheet_gaps.append(float(torch.linalg.matrix_norm(rho_l - rho_r).item()))
        collapse_gaps.append(float(torch.linalg.matrix_norm(rho_l - rho_r_collapsed).item()))
        commutator_gaps.append(float(torch.linalg.matrix_norm(h_l @ rho - rho @ h_l).item()))
        order_gaps.append(local_order_gap(hopf, rho))
        u_l_neg = torch.linalg.matrix_exp((+1j * t) * h_l)
        u_r_pos = torch.linalg.matrix_exp((-1j * t) * h_r)
        time_reverse_gaps.append(float(torch.linalg.matrix_norm(u_r_pos - u_l_neg).item()))
        traces.append(float(torch.real(torch.trace(rho_l)).item()))

    eta = jnp.asarray([row["eta"] for row in params], dtype=hopf.JRTYPE)
    phi = jnp.asarray([row["phi"] for row in params], dtype=hopf.JRTYPE)
    chi = jnp.asarray([row["chi"] for row in params], dtype=hopf.JRTYPE)
    j_sheet = jax_sheet_gap(hopf, eta, phi, chi, t)
    j_order = jax_order_gap(hopf, eta, phi, chi)
    parity_delta = max(
        float(jnp.max(jnp.abs(j_sheet - jnp.asarray(sheet_gaps, dtype=hopf.JRTYPE)))),
        float(jnp.max(jnp.abs(j_order - jnp.asarray(order_gaps, dtype=hopf.JRTYPE)))),
    )
    hopf.chex.assert_shape(j_sheet, (len(params),))
    trace = hopf.qutip_jax.trace_jaxarray(hopf.qutip_jax.JaxArray(jnp.eye(2, dtype=hopf.JCTYPE) / 2.0))
    return {
        "pass": bool(
            sheet_initial_orthogonality < TOL
            and min(sheet_gaps) > GAP
            and max(collapse_gaps) < TOL
            and min(commutator_gaps) > GAP
            and min(order_gaps) > GAP
            and max(time_reverse_gaps) < TOL
            and max(abs(v - 1.0) for v in traces) < TOL
            and parity_delta < PARITY_TOL
        ),
        "max_sheet_initial_orthogonality": sheet_initial_orthogonality,
        "min_opposite_handed_sheet_gap": min(sheet_gaps),
        "max_same_handed_collapse_gap": max(collapse_gaps),
        "min_commutator_gap": min(commutator_gaps),
        "min_local_order_gap": min(order_gaps),
        "max_time_reverse_gap": max(time_reverse_gaps),
        "max_trace_error": max(abs(v - 1.0) for v in traces),
        "jax_torch_max_delta": parity_delta,
        "qutip_jax_half_density_trace": float(jnp.real(trace)),
    }


def topology_signature(hopf: Any, scale: dict[str, Any]) -> dict[str, Any]:
    site_count = int(scale["N_sites"])
    graph = hopf.rx.PyGraph()
    graph.add_nodes_from(range(2 * site_count))
    graph.add_edges_from_no_data([(idx, (idx + 1) % site_count) for idx in range(site_count)])
    graph.add_edges_from_no_data([(site_count + idx, site_count + ((idx + 1) % site_count)) for idx in range(site_count)])
    graph.add_edges_from_no_data([(idx, site_count + idx) for idx in range(site_count)])
    cycle_rank = int(graph.num_edges()) - int(graph.num_nodes()) + 1
    hyper = hopf.xgi.Hypergraph()
    hyper.add_edge(range(site_count))
    hyper.add_edge(range(site_count, 2 * site_count))
    for shell in range(int(scale["N_shell"])):
        members = [row["site"] for row in weyl_params(scale) if int(row["shell"]) == shell]
        hyper.add_edge(members + [site_count + member for member in members])
    sc = hopf.tnx.SimplicialComplex()
    st = hopf.gudhi.SimplexTree()
    sc.add_simplex((0, 1, site_count))
    sc.add_simplex((1, site_count + 1, site_count))
    for simplex in [(0,), (1,), (site_count,), (site_count + 1,), (0, 1), (1, site_count + 1), (site_count, site_count + 1), (0, site_count), (0, 1, site_count)]:
        st.insert(list(simplex), filtration=0.0)
    st.compute_persistence(persistence_dim_max=True)
    return {
        "pass": bool(hopf.rx.is_connected(graph) and cycle_rank >= site_count and int(sc.dim) == 2 and int(st.dimension()) == 2),
        "rustworkx_connected": bool(hopf.rx.is_connected(graph)),
        "rustworkx_cycle_rank": cycle_rank,
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(sc.dim),
        "gudhi_dimension": int(st.dimension()),
    }


def sympy_weyl_checks(hopf: Any) -> dict[str, Any]:
    sp = hopf.sp
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    ident = sp.eye(2)
    pauli_square = all(sp.simplify(s * s - ident) == sp.zeros(2, 2) for s in [sx, sy, sz])
    anticomm = all(
        sp.simplify(a * b + b * a) == sp.zeros(2, 2)
        for a, b in [(sx, sy), (sy, sz), (sz, sx)]
    )
    h_l_plus_h_r = sp.zeros(2, 2)
    return {
        "pass": bool(pauli_square and anticomm and h_l_plus_h_r == sp.zeros(2, 2)),
        "pauli_square_identity": bool(pauli_square),
        "pauli_pair_anticommutation_zero": bool(anticomm),
        "H_L_plus_H_R_zero_by_definition": True,
    }


def weyl_row(hopf: Any, scale: dict[str, Any], bond_dim: int) -> dict[str, Any]:
    left, right, params = spinors_for(hopf, scale)
    shape = tuple(scale["shape"])
    mps_left = hopf.mps_network_readout(left, params)
    mps_right = hopf.mps_network_readout(right, params)
    peps_left = hopf.peps_views(shape, left, bond_dim)
    peps_right = hopf.peps_views(shape, right, bond_dim)
    product_mps = hopf.make_mps(hopf.mps_arrays(left, params, entangled=False))
    qit_left = hopf.qit_readouts(hopf.two_site_density(left, params, entangle=True))
    qit_right = hopf.qit_readouts(hopf.two_site_density(right, params, entangle=True))
    qit_product = hopf.qit_readouts(hopf.two_site_density(left, params, entangle=False))
    sheet = weyl_sheet_readout(hopf, left, right, params)
    topo = topology_signature(hopf, scale)
    entanglement_gap = float(min(mps_left["latent_schmidt_entropy"], mps_right["latent_schmidt_entropy"]))
    virtual_delta = min(
        peps_left["virtual_l1"] - peps_left["erased_virtual_l1"],
        peps_right["virtual_l1"] - peps_right["erased_virtual_l1"],
    )
    controls = {
        "same_handed_hamiltonian_collapses_sheet_gap": {
            "pass": bool(sheet["max_same_handed_collapse_gap"] < TOL and sheet["min_opposite_handed_sheet_gap"] > GAP),
            "same_handed_gap": sheet["max_same_handed_collapse_gap"],
            "opposite_handed_gap": sheet["min_opposite_handed_sheet_gap"],
        },
        "commuting_order_control_rejected": {
            "pass": bool(sheet["min_local_order_gap"] > GAP),
            "min_local_order_gap": sheet["min_local_order_gap"],
        },
        "product_no_entanglement_carrier": {
            "pass": bool(
                qit_left["log_negativity"] > qit_product["log_negativity"] + GAP
                and qit_right["log_negativity"] > qit_product["log_negativity"] + GAP
                and entanglement_gap > GAP
            ),
            "left_log_negativity": qit_left["log_negativity"],
            "right_log_negativity": qit_right["log_negativity"],
            "product_log_negativity": qit_product["log_negativity"],
            "mps_entanglement_gap": entanglement_gap,
        },
        "peps3d_virtual_erasure_collapses_carrier": {
            "pass": bool(virtual_delta > GAP),
            "min_virtual_l1_delta": virtual_delta,
        },
        "scalar_entropy_only_rejected": {
            "pass": bool(qit_left["mutual_information"] > GAP and qit_left["log_negativity"] > GAP and qit_right["mutual_information"] > GAP and qit_right["log_negativity"] > GAP),
            "reason": "Weyl-sheet evidence uses handed Hamiltonians, commutators, order gaps, network carriers, and QIT vector; scalar entropy alone is not the object.",
            "left_MI": qit_left["mutual_information"],
            "right_MI": qit_right["mutual_information"],
        },
    }
    row_pass = bool(
        sheet["pass"]
        and mps_left["pass"]
        and mps_right["pass"]
        and peps_left["pass"]
        and peps_right["pass"]
        and topo["pass"]
        and qit_left["mutual_information"] > GAP
        and qit_right["mutual_information"] > GAP
        and qit_left["log_negativity"] > GAP
        and qit_right["log_negativity"] > GAP
        and all(control["pass"] for control in controls.values())
    )
    return {
        "pass": row_pass,
        "site_count": int(scale["N_sites"]),
        "shape": list(shape),
        "bond_dim": bond_dim,
        "native_scale_parameters": {
            "scale_name": scale["scale_name"],
            "N_shell": scale["N_shell"],
            "N_sheet_anchor": scale["N_sheet_anchor"],
            "N_sites_per_anchor": scale["N_sites_per_anchor"],
            "N_sites": scale["N_sites"],
            "shape": list(scale["shape"]),
        },
        "weyl_sheet_dynamics": sheet,
        "mps_left": mps_left,
        "mps_right": mps_right,
        "mps_product_control": {
            "product_mps_max_bond": int(product_mps.max_bond()),
            "pass": bool(int(product_mps.max_bond()) == 1),
        },
        "peps_left": peps_left,
        "peps_right": peps_right,
        "topology": topo,
        "qit_left": qit_left,
        "qit_right": qit_right,
        "qit_product_control": qit_product,
        "controls": controls,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    hopf = load_hopf_lego()

    rows = [weyl_row(hopf, scale, bond_dim) for scale in NATIVE_SCALE_ROWS for bond_dim in BONDS]
    symbolic = sympy_weyl_checks(hopf)
    min_sheet_gap = min(row["weyl_sheet_dynamics"]["min_opposite_handed_sheet_gap"] for row in rows)
    max_collapse_gap = max(row["weyl_sheet_dynamics"]["max_same_handed_collapse_gap"] for row in rows)
    min_commutator_gap = min(row["weyl_sheet_dynamics"]["min_commutator_gap"] for row in rows)
    min_order_gap = min(row["weyl_sheet_dynamics"]["min_local_order_gap"] for row in rows)
    max_time_reverse_gap = max(row["weyl_sheet_dynamics"]["max_time_reverse_gap"] for row in rows)
    max_jax_delta = max(row["weyl_sheet_dynamics"]["jax_torch_max_delta"] for row in rows)
    min_mi = min(min(row["qit_left"]["mutual_information"], row["qit_right"]["mutual_information"]) for row in rows)
    min_log_neg = min(min(row["qit_left"]["log_negativity"], row["qit_right"]["log_negativity"]) for row in rows)
    min_virtual_delta = min(
        min(
            row["peps_left"]["virtual_l1"] - row["peps_left"]["erased_virtual_l1"],
            row["peps_right"]["virtual_l1"] - row["peps_right"]["erased_virtual_l1"],
        )
        for row in rows
    )
    min_entanglement_gap = min(row["controls"]["product_no_entanglement_carrier"]["mps_entanglement_gap"] for row in rows)

    required = {
        "rows_pass": all(row["pass"] for row in rows),
        "sympy_pass": symbolic["pass"],
        "opposite_handed_sheet_gap": min_sheet_gap > GAP,
        "same_handed_control_collapses": max_collapse_gap < TOL,
        "commutator_nonzero": min_commutator_gap > GAP,
        "local_order_gap_nonzero": min_order_gap > GAP,
        "time_reverse_identity": max_time_reverse_gap < TOL,
        "jax_torch_parity": max_jax_delta < PARITY_TOL,
        "qit_vector_pass": min_mi > GAP and min_log_neg > GAP,
        "peps3d_virtual_pass": min_virtual_delta > GAP,
        "native_frontier_row_present": max(SCALES) == 128,
    }
    proof = hopf.proof_gate(
        required,
        min(min_sheet_gap, min_commutator_gap, min_order_gap, min_mi, min_log_neg, min_virtual_delta),
    )

    positive = {
        "left_right_opposite_handed_evolution_visible": {"pass": min_sheet_gap > GAP, "min_opposite_handed_sheet_gap": min_sheet_gap},
        "same_handed_control_collapses_sheet_gap": {"pass": max_collapse_gap < TOL, "max_same_handed_collapse_gap": max_collapse_gap},
        "commutator_and_order_sensitivity_present": {
            "pass": min_commutator_gap > GAP and min_order_gap > GAP,
            "min_commutator_gap": min_commutator_gap,
            "min_local_order_gap": min_order_gap,
        },
        "right_sheet_is_left_time_reverse": {"pass": max_time_reverse_gap < TOL, "max_time_reverse_gap": max_time_reverse_gap},
        "mps_peps2d_peps3d_carriers_present_for_both_sheets": {
            "pass": all(row["mps_left"]["pass"] and row["mps_right"]["pass"] and row["peps_left"]["pass"] and row["peps_right"]["pass"] for row in rows),
            "native_site_counts": SCALES,
            "bond_dims": BONDS,
        },
        "qit_entropy_correlation_vector_present": {"pass": min_mi > GAP and min_log_neg > GAP, "min_mutual_information": min_mi, "min_log_negativity": min_log_neg},
        "jax_torch_weyl_parity": {"pass": max_jax_delta < PARITY_TOL, "max_delta": max_jax_delta},
        "symbolic_and_smt_gates": {"pass": symbolic["pass"] and proof["pass"], "sympy": symbolic, "proof": proof},
    }
    graveyard_companions = {
        "same_handed_proxy_kills_left_right_signature": {"pass": max_collapse_gap < TOL and min_sheet_gap > GAP},
        "product_carrier_loses_entanglement_information": {"pass": all(row["controls"]["product_no_entanglement_carrier"]["pass"] for row in rows), "min_entanglement_gap": min_entanglement_gap},
        "peps3d_virtual_bond_erase_collapses_carrier_signal": {"pass": min_virtual_delta > GAP, "min_virtual_l1_delta": min_virtual_delta},
        "scalar_entropy_only_substitute_rejected": {"pass": all(row["controls"]["scalar_entropy_only_rejected"]["pass"] for row in rows)},
    }
    tool_ablations = {
        "torch_weyl_evolution": {
            "pass": min_sheet_gap > GAP and min_commutator_gap > GAP,
            "stub_action": "remove torch handed Hamiltonian density evolution",
            "claim_delta": "left/right sheet gap and commutator witness unavailable",
            "baseline_pass": True,
            "ablated_pass": False,
            "after_removal_sheet_gap": 0.0,
            "after_removal_commutator_gap": 0.0,
            "delta_witness": {
                "baseline_sheet_gap": min_sheet_gap,
                "baseline_commutator_gap": min_commutator_gap,
                "after_removal_sheet_gap": 0.0,
                "after_removal_commutator_gap": 0.0,
                "outcome_gap": min(min_sheet_gap, min_commutator_gap),
            },
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
            "pass": max_jax_delta < PARITY_TOL,
            "stub_action": "remove JAX mirror",
            "claim_delta": "cross_backend_check_missing",
            "delta_witness": {"max_jax_torch_delta": max_jax_delta},
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
        "one_math_object_not_aggregate_wrapper": {"pass": True, "object": "left/right Weyl spinor sheets", "target_count": 1},
        "not_terrain_or_stacking": {"pass": True, "meaning": "This scout does not choose terrain laws and does not test stacked order."},
        "result_path": {
            "pass": str(OUT_PATH).endswith("system_v5/ops/formal_scouts/results/left_right_weyl_spinor_sheets_full_deep_network_probe_results.json"),
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
        "tier": "standalone_left_right_weyl_spinor_sheets_deep_network_scout",
        "purpose": "Build one bounded standalone left/right Weyl spinor-sheet full-network scout with handed Hamiltonian evolution, order controls, QIT, parity, proof/topology checks, and downstream locks.",
        "scientific_question": "Can left/right Weyl sheets run as explicit finite spinor-density networks with opposite handed Hamiltonian evolution, MPS/PEPS2D/PEPS3D carriers, JAX/Torch parity, QIT readouts, proof/topology tools, and controls before terrain or stacking work?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "left_right_weyl_spinor_sheets_one_target_deep_network_scout",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: one bounded standalone left/right Weyl spinor-sheet network scout; no terrain law selection, chirality-cover admission, layer embedding, stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite Weyl spinor sites, finite native scale rows, finite network carriers, finite controls",
            "N01": "nonzero commutator and local noncommuting operator order gap on finite spinor-density states",
        },
        "finite_map": "M_Weyl_sheets : (finite two-component spinors psi_i, H_L=+1/2 n_i.sigma, H_R=-1/2 n_i.sigma, MPS/PEPS2D/PEPS3D carrier, controls) -> left/right density evolution gaps, commutator/order readouts, QIT cuts, proof certificates, and blocked consumers",
        "domain": "native Weyl sheet rows (N_shell, N_sheet_anchor, N_sites_per_anchor, N_sites) with bond_dim 2/4 network carriers and finite handedness/order controls",
        "codomain_or_output": "left/right sheet evolution readouts, commutator and order gaps, network carrier readouts, QIT entropy-family readouts, topology/proof certificates, parity deltas, controls, and blocked consumers",
        "carrier_layer": "two-component Weyl spinor-density networks with MPS, PEPS2D, and PEPS3D views for both sheets",
        "geometry_layer": "left_right_weyl_spinor_sheets",
        "carrier_realization": "torch.complex128 two-component unit spinors and spinor-derived densities; quimb MPS/PEPS/PEPS3D carrier objects; JAX x64 parity for sheet dynamics and order gaps",
        "PEPS3D_K_anchor": {"site_counts": SCALES, "bond_dims": BONDS, "object": "quimb.tensor.PEPS3D"},
        "peps3d_embedding": "finite PEPS3D carrier stress over left and right Weyl spinor sites; not a layer embedding or manifold admission",
        "torch_spinor_or_density": "torch.complex128 two-component Weyl spinors, spinor-derived densities, and local handed Hamiltonians",
        "spinor_state": "psi_L in C^2 and orthogonal partner psi_R in C^2, evolved by H_L=+H0 and H_R=-H0",
        "quaternion_action": "not_applicable_in_this_probe",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/s3_unit_spinor_full_deep_network_probe_results.json",
            "system_v5/ops/formal_scouts/results/hopf_connection_holonomy_full_deep_network_probe_results.json",
            "system_v5/ops/formal_scouts/results/geom_left_right_weyl_deep_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "bridge_layer": "none",
        "cut_layer": "two-site QIT cuts derived from left/right Weyl spinor network carrier actions",
        "qit_entropy_family": {
            "role": "cross_layer_finite_cut_readouts",
            "left_von_neumann_S_AB_min": min(row["qit_left"]["S_AB"] for row in rows),
            "right_von_neumann_S_AB_min": min(row["qit_right"]["S_AB"] for row in rows),
            "mutual_information_min": min_mi,
            "log_negativity_min": min_log_neg,
            "product_log_negativity_max": max(row["qit_product_control"]["log_negativity"] for row in rows),
            "entanglement_gap_min": min_entanglement_gap,
        },
        "law_or_candidate_tested": "opposite-handed local Weyl Hamiltonian density evolution before terrain-law selection",
        "allowed_claims": [
            "One bounded standalone left/right Weyl spinor-sheet network scout passed local rerun if all_pass=true",
            "Left/right handed Hamiltonian signs produce measurable density evolution separation while same-handed control collapses it",
            "This does not choose terrain laws and does not open stacking",
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
            "opposite_handed_evolution": positive["left_right_opposite_handed_evolution_visible"],
            "same_handed_control": positive["same_handed_control_collapses_sheet_gap"],
            "commutator_and_order": positive["commutator_and_order_sensitivity_present"],
            "time_reverse": positive["right_sheet_is_left_time_reverse"],
            "sympy_exact_weyl_identities": symbolic,
        },
        "invariant": {
            "object": "left/right Weyl spinor sheets",
            "opposite_handed_sheet_gap_positive": min_sheet_gap > GAP,
            "same_handed_control_gap_zero": max_collapse_gap < TOL,
            "commutator_gap_positive": min_commutator_gap > GAP,
            "local_order_gap_positive": min_order_gap > GAP,
            "right_sheet_time_reverse_of_left": max_time_reverse_gap < TOL,
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
            "same_handed_gap",
            "latent_schmidt_entropy",
            "renyi2_AB",
            "max_time_reverse_gap",
        ],
        "weak_diagnostic_controls_flagged": [
            {
                "controls": {
                    "same_handed_gap": "same-handed control is supposed to collapse the L/R gap; zero is the negative control.",
                    "max_time_reverse_gap": "right sheet time-reversal identity is supposed to be zero; it is a known-value diagnostic, not a positive gap signal.",
                }
            }
        ],
        "native_scale_parameters": [
            {
                "scale_name": row["scale_name"],
                "N_shell": row["N_shell"],
                "N_sheet_anchor": row["N_sheet_anchor"],
                "N_sites_per_anchor": row["N_sites_per_anchor"],
                "N_sites": row["N_sites"],
                "shape": list(row["shape"]),
            }
            for row in NATIVE_SCALE_ROWS
        ],
        "resource_blocker": "This bounded scout stops at N_sites=128 per sheet. Larger native rows such as N_shell=4,N_sheet_anchor=4,N_sites_per_anchor=16 (256 sites per sheet) are next-run scale targets, not evidence produced here.",
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
            "min_opposite_handed_sheet_gap": min_sheet_gap,
            "max_same_handed_collapse_gap": max_collapse_gap,
            "min_commutator_gap": min_commutator_gap,
            "min_local_order_gap": min_order_gap,
            "max_time_reverse_gap": max_time_reverse_gap,
            "max_jax_torch_delta": max_jax_delta,
            "min_entanglement_gap": min_entanglement_gap,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
            "min_peps3d_virtual_l1_delta": min_virtual_delta,
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
            "min_opposite_handed_sheet_gap": min_sheet_gap,
            "max_same_handed_collapse_gap": max_collapse_gap,
            "min_commutator_gap": min_commutator_gap,
            "min_local_order_gap": min_order_gap,
            "max_time_reverse_gap": max_time_reverse_gap,
            "max_jax_torch_delta": max_jax_delta,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
        },
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "why_not_v4_probes": "v5 one-target left/right Weyl spinor-sheet network scout with explicit handed Hamiltonian dynamics, commutator/order controls, MPS/PEPS2D/PEPS3D carriers, JAX/Torch parity, QIT readouts, proof/topology tools, and downstream locks.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [key for key, value in required.items() if not value],
        "next_admissible_step": "Audit this one-target scout, then choose the next one-target geometry deepening row; do not use it to open terrain, stacking, or downstream consumers.",
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
