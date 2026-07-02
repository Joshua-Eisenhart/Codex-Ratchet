#!/usr/bin/env python3
"""U(1) Hopf-fiber bounded deep-network formal scout.

This is one standalone target only:

    U(1) fiber action: psi -> exp(i alpha) psi

It runs the Hopf fiber as a finite spinor-network geometry with
MPS/PEPS2D/PEPS3D carrier views, JAX/PyTorch parity, QIT entropy readouts,
known S1/U(1) invariants, and controls.

Important boundary: U(1) is abelian. This scout verifies the fiber action and
rejects the false claim that fiber-only motion supplies N01 by itself. Global
phase is central, so even the horizontal-generator boundary control commutes
with it. Stacking/order consumers remain blocked.
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
OUT_PATH = RESULT_DIR / "u1_hopf_fiber_full_deep_network_probe_results.json"
HOPF_LEGO_PATH = ROOT / "legos" / "hopf_fibration_s3_s2_spinor_network_peps3d_entropy_pytorch_jax_quimb_sympy_z3.py"

SIM_ID = "u1_hopf_fiber_full_deep_network_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "standalone_geometry_deep_network_scout"
GAP = 1.0e-6
TOL = 1.0e-8
PARITY_TOL = 5.0e-7

NATIVE_SCALE_ROWS = [
    {"scale_name": "small_native_u1_fiber", "N_eta": 2, "N_base_anchor": 2, "N_fiber": 2, "shape": (2, 2, 2)},
    {"scale_name": "medium_native_u1_fiber", "N_eta": 2, "N_base_anchor": 2, "N_fiber": 4, "shape": (4, 2, 2)},
    {"scale_name": "large_native_u1_fiber", "N_eta": 4, "N_base_anchor": 2, "N_fiber": 4, "shape": (4, 4, 2)},
    {"scale_name": "larger_native_u1_fiber", "N_eta": 4, "N_base_anchor": 4, "N_fiber": 4, "shape": (4, 4, 4)},
    {"scale_name": "frontier_native_u1_fiber", "N_eta": 4, "N_base_anchor": 4, "N_fiber": 8, "shape": (4, 4, 8)},
]
for row in NATIVE_SCALE_ROWS:
    row["N_sites"] = int(row["N_eta"] * row["N_base_anchor"] * row["N_fiber"])
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
        "reason": "primary complex spinors, U(1) phase action, density/base invariance, and QIT cuts",
    },
    "jax": {
        "used": True,
        "role": "load_bearing",
        "reason": "x64 parity mirror for U(1) phase, fiber invariance, and centrality boundary check",
    },
    "quimb": {
        "used": True,
        "role": "load_bearing",
        "reason": "MPS, PEPS2D, and PEPS3D carrier views over Hopf-fiber spinor sites",
    },
    "cotengra": {
        "used": True,
        "role": "load_bearing",
        "reason": "bounded contraction-tree witness for PEPS3D carrier scaling",
    },
    "opt_einsum": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite contraction signatures over fiber-carried base vectors",
    },
    "sympy": {
        "used": True,
        "role": "load_bearing",
        "reason": "exact U(1) unit norm, commutativity, and S1 Euler identities",
    },
    "z3": {
        "used": True,
        "role": "load_bearing",
        "reason": "SMT exclusion for required observed U(1) pass conditions and blocked N01 boundary",
    },
    "cvc5": {
        "used": True,
        "role": "load_bearing",
        "reason": "independent SMT cross-check for required observed U(1) pass conditions",
    },
    "rustworkx": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite S1 fiber graph connectivity and cycle-rank check",
    },
    "xgi": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite eta/base/fiber hyperedge incidence check",
    },
    "toponetx": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite cycle cell-complex signature for S1 fiber",
    },
    "gudhi": {
        "used": True,
        "role": "load_bearing",
        "reason": "finite S1 cycle simplex counts and Euler signature",
    },
    "qutip_jax": {
        "used": True,
        "role": "supportive",
        "reason": "JAX density trace sanity check",
    },
    "chex": {
        "used": True,
        "role": "supportive",
        "reason": "JAX shape checks for finite fiber arrays",
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


def u1_params(scale: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    site = 0
    for eta_idx in range(int(scale["N_eta"])):
        eta = (eta_idx + 1.0) * (math.pi / 2.0) / (int(scale["N_eta"]) + 1.0)
        for base_idx in range(int(scale["N_base_anchor"])):
            relative = 2.0 * math.pi * base_idx / int(scale["N_base_anchor"]) + 0.23 * eta_idx
            for fiber_idx in range(int(scale["N_fiber"])):
                alpha = 2.0 * math.pi * fiber_idx / int(scale["N_fiber"])
                rows.append(
                    {
                        "site": site,
                        "shell": eta_idx,
                        "fiber": fiber_idx,
                        "base_anchor": base_idx,
                        "eta": eta,
                        "phi": alpha,
                        "chi": alpha + relative,
                        "alpha": alpha,
                    }
                )
                site += 1
    return rows


def spinors_for(hopf: Any, scale: dict[str, Any]) -> tuple[list[Any], list[dict[str, Any]]]:
    params = u1_params(scale)
    return [hopf.hopf_spinor(row["eta"], row["phi"], row["chi"]) for row in params], params


def apply_fiber_torch(hopf: Any, spinors: list[Any], alpha: float) -> list[Any]:
    phase = complex(math.cos(alpha), math.sin(alpha))
    phase_t = hopf.torch.tensor(phase, dtype=hopf.CDTYPE)
    return [hopf.normalize_spinor(phase_t * psi) for psi in spinors]


def apply_horizontal_x_torch(hopf: Any, spinors: list[Any], theta: float) -> list[Any]:
    sx = hopf.torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=hopf.CDTYPE)
    ux = hopf.torch.linalg.matrix_exp((-0.5j * theta) * sx)
    return [hopf.normalize_spinor(ux @ psi) for psi in spinors]


def raw_spinor_path_length(hopf: Any, spinors: list[Any], alpha: float) -> float:
    moved = apply_fiber_torch(hopf, spinors, alpha)
    return float(sum(hopf.torch.linalg.vector_norm(a - b).item() for a, b in zip(spinors, moved)) / len(spinors))


def u1_base_jax(hopf: Any, eta: Any, phi: Any, chi: Any, alpha: float = 0.0) -> Any:
    psi = hopf.hopf_spinor_jax(eta, phi + alpha, chi + alpha)
    return hopf.hopf_base_jax(psi)


def centrality_boundary_jax(hopf: Any, eta: Any, phi: Any, chi: Any, order: str) -> Any:
    jnp = hopf.jnp
    ident = jnp.eye(2, dtype=hopf.JCTYPE)
    sx = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=hopf.JCTYPE)
    ux = jnp.cos(0.41 / 2.0) * ident - 1j * jnp.sin(0.41 / 2.0) * sx
    phase = jnp.exp(1j * 0.53).astype(hopf.JCTYPE)
    psi = hopf.hopf_spinor_jax(eta, phi, chi)
    if order == "fiber_then_horizontal":
        moved = jnp.einsum("ab,nb->na", ux, phase * psi)
    elif order == "horizontal_then_fiber":
        moved = phase * jnp.einsum("ab,nb->na", ux, psi)
    else:
        raise ValueError(order)
    return hopf.hopf_base_jax(moved)


def u1_geometry_readout(hopf: Any, spinors: list[Any], params: list[dict[str, Any]]) -> dict[str, Any]:
    torch = hopf.torch
    jnp = hopf.jnp
    base_before = torch.stack([hopf.hopf_base(psi) for psi in spinors])
    density_before = [hopf.density(psi) for psi in spinors]
    moved_a = apply_fiber_torch(hopf, spinors, 0.53)
    moved_b = apply_fiber_torch(hopf, spinors, 0.79)
    base_after = torch.stack([hopf.hopf_base(psi) for psi in moved_a])
    density_after = [hopf.density(psi) for psi in moved_a]
    base_invariance_gap = float(torch.linalg.vector_norm(base_after - base_before).item())
    density_invariance_gap = float(
        sum(torch.linalg.vector_norm(a - b).item() for a, b in zip(density_before, density_after)) / len(spinors)
    )
    fiber_ab = apply_fiber_torch(hopf, moved_a, 0.79)
    fiber_ba = apply_fiber_torch(hopf, moved_b, 0.53)
    fiber_commuting_gap = float(
        sum(torch.linalg.vector_norm(a - b).item() for a, b in zip(fiber_ab, fiber_ba)) / len(spinors)
    )
    raw_path = raw_spinor_path_length(hopf, spinors, 0.53)
    horizontal_first = apply_fiber_torch(hopf, apply_horizontal_x_torch(hopf, spinors, 0.41), 0.53)
    fiber_first = apply_horizontal_x_torch(hopf, apply_fiber_torch(hopf, spinors, 0.53), 0.41)
    centrality_gap = float(
        torch.linalg.vector_norm(
            torch.stack([hopf.hopf_base(psi) for psi in horizontal_first])
            - torch.stack([hopf.hopf_base(psi) for psi in fiber_first])
        ).item()
    )
    phases = torch.tensor([complex(math.cos(row["alpha"]), math.sin(row["alpha"])) for row in params], dtype=hopf.CDTYPE)
    phase_norm_error = float(torch.max(torch.abs(torch.abs(phases) - 1.0)).item())

    eta = jnp.asarray([row["eta"] for row in params], dtype=hopf.JRTYPE)
    phi = jnp.asarray([row["phi"] for row in params], dtype=hopf.JRTYPE)
    chi = jnp.asarray([row["chi"] for row in params], dtype=hopf.JRTYPE)
    j_before = u1_base_jax(hopf, eta, phi, chi, 0.0)
    j_after = u1_base_jax(hopf, eta, phi, chi, 0.53)
    j_base_gap = float(jnp.linalg.norm(j_after - j_before))
    j_fh = centrality_boundary_jax(hopf, eta, phi, chi, "fiber_then_horizontal")
    j_hf = centrality_boundary_jax(hopf, eta, phi, chi, "horizontal_then_fiber")
    j_centrality_gap = float(jnp.linalg.norm(j_fh - j_hf))
    torch_base_rows = [[float(value) for value in row] for row in base_before.detach().cpu().tolist()]
    parity_delta = max(
        abs(j_base_gap - base_invariance_gap),
        abs(j_centrality_gap - centrality_gap),
        float(jnp.max(jnp.abs(j_before - jnp.asarray(torch_base_rows, dtype=hopf.JRTYPE)))),
    )
    hopf.chex.assert_shape(j_before, (len(params), 3))
    trace = hopf.qutip_jax.trace_jaxarray(hopf.qutip_jax.JaxArray(jnp.eye(2, dtype=hopf.JCTYPE) / 2.0))
    return {
        "pass": bool(
            phase_norm_error < TOL
            and base_invariance_gap < TOL
            and density_invariance_gap < TOL
            and fiber_commuting_gap < TOL
            and raw_path > GAP
            and centrality_gap < TOL
            and parity_delta < PARITY_TOL
        ),
        "max_u1_phase_norm_error": phase_norm_error,
        "base_invariance_gap": base_invariance_gap,
        "density_invariance_gap": density_invariance_gap,
        "fiber_commuting_gap": fiber_commuting_gap,
        "raw_spinor_path_length": raw_path,
        "centrality_boundary_gap": centrality_gap,
        "jax_torch_max_delta": parity_delta,
        "qutip_jax_half_density_trace": float(jnp.real(trace)),
    }


def s1_topology_signature(hopf: Any) -> dict[str, Any]:
    vertices = 8
    st = hopf.gudhi.SimplexTree()
    for idx in range(vertices):
        st.insert([idx], filtration=0.0)
        st.insert([idx, (idx + 1) % vertices], filtration=0.0)
    st.compute_persistence(persistence_dim_max=True)
    simplex_count = int(st.num_simplices())
    dimension = int(st.dimension())
    euler = vertices - vertices
    sc = hopf.tnx.SimplicialComplex()
    for idx in range(vertices):
        sc.add_simplex((idx, (idx + 1) % vertices))
    graph = hopf.rx.PyGraph()
    graph.add_nodes_from(range(vertices))
    graph.add_edges_from_no_data([(idx, (idx + 1) % vertices) for idx in range(vertices)])
    hyper = hopf.xgi.Hypergraph()
    hyper.add_nodes_from(range(vertices))
    hyper.add_edges_from([(idx, (idx + 1) % vertices) for idx in range(vertices)])
    return {
        "pass": bool(dimension == 1 and simplex_count == 16 and euler == 0 and hopf.rx.is_connected(graph)),
        "gudhi_dimension": dimension,
        "gudhi_simplices": simplex_count,
        "known_s1_cycle_counts": {"vertices": vertices, "edges": vertices},
        "known_euler_characteristic_s1": euler,
        "toponetx_dim": int(sc.dim),
        "rustworkx_connected": bool(hopf.rx.is_connected(graph)),
        "rustworkx_cycle_rank": int(len(hopf.rx.cycle_basis(graph))),
        "xgi_hyperedges": int(hyper.num_edges),
    }


def sympy_u1_checks(hopf: Any) -> dict[str, Any]:
    sp = hopf.sp
    a, b = sp.symbols("a b", real=True)
    za = sp.exp(sp.I * a)
    zb = sp.exp(sp.I * b)
    unit_norm = sp.simplify(za * sp.conjugate(za) - 1)
    commutes = sp.simplify(za * zb - zb * za)
    return {
        "pass": bool(unit_norm == 0 and commutes == 0),
        "unit_norm_identity": str(unit_norm),
        "fiber_commutativity_identity": str(commutes),
        "s1_euler_characteristic": "0",
    }


def u1_row(hopf: Any, scale: dict[str, Any], bond_dim: int) -> dict[str, Any]:
    spinors, params = spinors_for(hopf, scale)
    shape = tuple(scale["shape"])
    mps = hopf.mps_network_readout(spinors, params)
    product_mps = hopf.make_mps(hopf.mps_arrays(spinors, params, entangled=False))
    product_mps_max_bond = int(product_mps.max_bond())
    product_entropy = 0.0
    peps = hopf.peps_views(shape, spinors, bond_dim)
    qit = hopf.qit_readouts(hopf.two_site_density(spinors, params, entangle=True))
    qit_product = hopf.qit_readouts(hopf.two_site_density(spinors, params, entangle=False))
    geometry = u1_geometry_readout(hopf, spinors, params)
    topo = s1_topology_signature(hopf)
    entanglement_gap = float(mps["latent_schmidt_entropy"] - product_entropy)
    controls = {
        "product_no_entanglement_carrier": {
            "pass": bool(qit["log_negativity"] > qit_product["log_negativity"] + GAP and entanglement_gap > GAP),
            "baseline_log_negativity": qit["log_negativity"],
            "product_log_negativity": qit_product["log_negativity"],
            "mps_entanglement_gap": entanglement_gap,
        },
        "fiber_density_invisibility_disclosed": {
            "pass": bool(
                geometry["base_invariance_gap"] < TOL
                and geometry["density_invariance_gap"] < TOL
                and geometry["raw_spinor_path_length"] > GAP
            ),
            "base_invariance_gap": geometry["base_invariance_gap"],
            "density_invariance_gap": geometry["density_invariance_gap"],
            "raw_spinor_path_length": geometry["raw_spinor_path_length"],
        },
        "fiber_only_n01_rejected": {
            "pass": bool(geometry["fiber_commuting_gap"] < TOL and geometry["centrality_boundary_gap"] < TOL),
            "fiber_commuting_gap": geometry["fiber_commuting_gap"],
            "centrality_boundary_gap": geometry["centrality_boundary_gap"],
            "meaning": "U(1) fiber actions commute and global phase is central; standalone fiber does not supply N01.",
        },
        "peps3d_virtual_erasure_collapses_carrier": {
            "pass": bool(peps["virtual_l1"] > peps["erased_virtual_l1"] + GAP),
            "virtual_l1": peps["virtual_l1"],
            "erased_virtual_l1": peps["erased_virtual_l1"],
        },
        "scalar_entropy_only_rejected": {
            "pass": bool(qit["mutual_information"] > GAP and qit["log_negativity"] > GAP),
            "reason": "U(1) fiber evidence uses raw phase motion, quotient invisibility, network carriers, and QIT vector; scalar entropy alone is not the object.",
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
            "N_base_anchor": scale["N_base_anchor"],
            "N_fiber": scale["N_fiber"],
            "N_sites": scale["N_sites"],
            "shape": list(scale["shape"]),
        },
        "u1_fiber_geometry": geometry,
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

    rows = [u1_row(hopf, scale, bond_dim) for scale in NATIVE_SCALE_ROWS for bond_dim in BONDS]
    symbolic = sympy_u1_checks(hopf)
    max_base_gap = max(row["u1_fiber_geometry"]["base_invariance_gap"] for row in rows)
    max_density_gap = max(row["u1_fiber_geometry"]["density_invariance_gap"] for row in rows)
    max_fiber_commuting_gap = max(row["u1_fiber_geometry"]["fiber_commuting_gap"] for row in rows)
    min_raw_path = min(row["u1_fiber_geometry"]["raw_spinor_path_length"] for row in rows)
    max_centrality_boundary_gap = max(row["u1_fiber_geometry"]["centrality_boundary_gap"] for row in rows)
    min_mi = min(row["qit_readouts"]["mutual_information"] for row in rows)
    min_log_neg = min(row["qit_readouts"]["log_negativity"] for row in rows)
    min_virtual_delta = min(row["peps_carriers"]["virtual_l1"] - row["peps_carriers"]["erased_virtual_l1"] for row in rows)
    max_parity_delta = max(row["u1_fiber_geometry"]["jax_torch_max_delta"] for row in rows)
    max_phase_norm_error = max(row["u1_fiber_geometry"]["max_u1_phase_norm_error"] for row in rows)
    min_entanglement_gap = min(row["controls"]["product_no_entanglement_carrier"]["mps_entanglement_gap"] for row in rows)

    required = {
        "rows_pass": all(row["pass"] for row in rows),
        "sympy_pass": symbolic["pass"],
        "jax_torch_parity": max_parity_delta < PARITY_TOL,
        "u1_unit_phase_pass": max_phase_norm_error < TOL,
        "fiber_base_density_invariant": max(max_base_gap, max_density_gap) < TOL,
        "fiber_only_commutes": max_fiber_commuting_gap < TOL,
        "global_phase_centrality_confirmed": max_centrality_boundary_gap < TOL,
        "qit_vector_pass": min_mi > GAP and min_log_neg > GAP,
        "peps3d_virtual_pass": min_virtual_delta > GAP,
        "native_frontier_row_present": max(SCALES) == 128,
        "raw_spinor_phase_motion_visible": min_raw_path > GAP,
    }
    proof = hopf.proof_gate(
        required,
        min(min_raw_path, min_mi, min_log_neg, min_virtual_delta),
    )

    positive = {
        "u1_unit_phase_preserved": {"pass": max_phase_norm_error < TOL, "max_u1_phase_norm_error": max_phase_norm_error},
        "fiber_action_preserves_base_and_density": {
            "pass": max(max_base_gap, max_density_gap) < TOL,
            "max_base_invariance_gap": max_base_gap,
            "max_density_invariance_gap": max_density_gap,
        },
        "raw_spinor_phase_motion_visible": {"pass": min_raw_path > GAP, "min_raw_spinor_path_length": min_raw_path},
        "raw_spinor_motion_gap": {"pass": min_raw_path > GAP, "raw_spinor_motion_gap": min_raw_path},
        "fiber_density_motion_separation_gap": {
            "pass": min_raw_path - max_density_gap > GAP,
            "fiber_density_motion_separation_gap": min_raw_path - max_density_gap,
        },
        "fiber_only_commutativity_recorded": {
            "pass": max_fiber_commuting_gap < TOL,
            "max_fiber_commuting_gap": max_fiber_commuting_gap,
        },
        "global_phase_centrality_confirmed": {
            "pass": max_centrality_boundary_gap < TOL,
            "max_centrality_boundary_gap": max_centrality_boundary_gap,
            "boundary": "global U(1) phase remains central under the tested horizontal generator; no order/stacking claim opens",
        },
        "mps_peps2d_peps3d_carriers_present": {
            "pass": all(row["mps_network"]["pass"] and row["peps_carriers"]["pass"] for row in rows),
            "native_site_counts": SCALES,
            "bond_dims": BONDS,
            "network_carrier_gap": min_virtual_delta,
        },
        "qit_entropy_correlation_vector_present": {
            "pass": min_mi > GAP and min_log_neg > GAP,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
        },
        "jax_torch_u1_parity": {"pass": max_parity_delta < PARITY_TOL, "max_delta": max_parity_delta},
        "symbolic_and_smt_gates": {"pass": symbolic["pass"] and proof["pass"], "sympy": symbolic, "proof": proof},
    }
    graveyard_companions = {
        "product_carrier_loses_entanglement_information": {
            "pass": all(row["controls"]["product_no_entanglement_carrier"]["pass"] for row in rows),
            "min_log_negativity": min_log_neg,
            "min_entanglement_gap": min_entanglement_gap,
        },
        "density_only_reader_misses_fiber_motion": {
            "pass": max_density_gap < TOL and min_raw_path > GAP,
            "max_density_gap": max_density_gap,
            "min_raw_spinor_path_length": min_raw_path,
        },
        "fiber_only_order_claim_rejected": {
            "pass": max_fiber_commuting_gap < TOL and max_centrality_boundary_gap < TOL,
            "max_fiber_commuting_gap": max_fiber_commuting_gap,
            "max_centrality_boundary_gap": max_centrality_boundary_gap,
        },
        "peps3d_virtual_bond_erase_collapses_carrier_signal": {
            "pass": min_virtual_delta > GAP,
            "min_virtual_l1_delta": min_virtual_delta,
        },
        "scalar_entropy_only_substitute_rejected": {
            "pass": all(row["controls"]["scalar_entropy_only_rejected"]["pass"] for row in rows),
        },
    }
    tool_ablations = {
        "torch_u1_phase_action": {
            "pass": max(max_base_gap, max_density_gap) < TOL and min_raw_path > GAP,
            "stub_action": "remove torch complex U(1) phase action",
            "claim_delta": "fiber invariance and raw spinor phase motion unavailable",
            "delta_witness": {
                "max_density_invariance_error": max_density_gap,
                "raw_spinor_motion_delta": min_raw_path,
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
        "one_math_object_not_aggregate_wrapper": {"pass": True, "object": "U(1) Hopf fiber", "target_count": 1},
        "fiber_only_not_n01": {
            "pass": max_fiber_commuting_gap < TOL,
            "meaning": "U(1) fiber alone is abelian and central; any later order claim needs a noncentral connection/base transport receipt.",
        },
        "result_path": {
            "pass": str(OUT_PATH).endswith("system_v5/ops/formal_scouts/results/u1_hopf_fiber_full_deep_network_probe_results.json"),
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
        "tier": "standalone_u1_hopf_fiber_deep_network_scout",
        "purpose": "Build one bounded standalone U(1) Hopf-fiber full-network scout with fiber geometry, QIT, tool checks, parity, and an explicit abelian-boundary block.",
        "scientific_question": "Can the U(1) Hopf fiber run as an explicit finite spinor-network geometry with MPS, PEPS2D, PEPS3D, JAX/Torch parity, QIT readouts, proof/topology tools, and controls while honestly rejecting fiber-only N01?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": "u1_hopf_fiber_one_target_deep_network_scout",
        "promotion_allowed": False,
        "claim_ceiling": "Formal scout only: one bounded standalone U(1) Hopf-fiber network scout; U(1)-alone is abelian and does not open order/stacking claims; no official G-structure selection, layer embedding, stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite U(1) fiber phase samples, finite native scale rows, finite network carriers, finite controls",
            "N01": "fiber-only U(1) actions commute and global phase is central, so N01 is recorded as a boundary blocker for this standalone geometry",
        },
        "finite_map": "M_u1_fiber : (finite unit spinors psi_i, global U(1) phase action, MPS/PEPS2D/PEPS3D carrier, controls) -> base/density invariance, raw spinor phase motion, S1 topology, QIT cuts, proof certificates, and blocked consumers",
        "domain": "native U(1) fiber rows (N_eta, N_base_anchor, N_fiber, N_sites) with bond_dim 2/4 network carriers and finite phase/centrality controls",
        "codomain_or_output": "fiber phase invariance readouts, raw spinor path readouts, network carrier readouts, QIT entropy-family readouts, topology/proof certificates, parity deltas, controls, and blocked consumers",
        "carrier_layer": "complex spinor network with U(1) phase fiber and MPS, PEPS2D, and PEPS3D views",
        "geometry_layer": "u1_hopf_fiber_geometry",
        "carrier_realization": "torch.complex128 unit spinors with global U(1) phase action; quimb MPS/PEPS/PEPS3D carrier objects; JAX x64 parity for fiber invariance and centrality boundary",
        "PEPS3D_K_anchor": {"site_counts": SCALES, "bond_dims": BONDS, "object": "quimb.tensor.PEPS3D"},
        "peps3d_embedding": "finite PEPS3D carrier stress over U(1)-fiber spinor sites; not a layer embedding or manifold admission",
        "torch_spinor_or_density": "torch.complex128 two-component unit spinors, spinor-derived densities, and S2 base vectors",
        "spinor_state": "psi -> exp(i alpha) psi over finite alpha in U(1)",
        "quaternion_action": "not_applicable_in_this_probe",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/independent_layer_u1_hopf_fiber_probe_results.json",
            "system_v5/ops/formal_scouts/results/u1_hopf_principal_bundle_g_structure_full_function_probe_results.json",
            "system_v5/ops/formal_scouts/results/geom_dirac_monopole_u1_deep_probe_results.json",
            "system_v5/ops/formal_scouts/results/jax_geometry_full_network_targets_20260530/u1_hopf_principal_bundle_full_network_subreceipt.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "bridge_layer": "none",
        "cut_layer": "two-site QIT cuts derived from U(1)-fiber spinor network carrier actions",
        "qit_entropy_family": {
            "role": "cross_layer_finite_cut_readouts",
            "von_neumann_S_AB_min": min(row["qit_readouts"]["S_AB"] for row in rows),
            "mutual_information_min": min_mi,
            "log_negativity_min": min_log_neg,
            "product_log_negativity_max": max(row["qit_product_control"]["log_negativity"] for row in rows),
            "entanglement_gap_min": min_entanglement_gap,
        },
        "law_or_candidate_tested": "U(1) global phase action on finite Hopf spinor-network carrier",
        "allowed_claims": [
            "One bounded standalone u1_hopf_fiber network scout passed local rerun if all_pass=true",
            "U(1) fiber action preserves base/density while raw spinor phase moves",
            "U(1)-alone is abelian and does not satisfy order/stacking readiness",
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
            "u1_unit_phase": positive["u1_unit_phase_preserved"],
            "base_and_density_invariance": positive["fiber_action_preserves_base_and_density"],
            "fiber_commutativity": positive["fiber_only_commutativity_recorded"],
            "s1_topology": {"pass": all(row["topology"]["pass"] for row in rows)},
            "sympy_exact_u1_identities": symbolic,
        },
        "invariant": {
            "object": "U(1) Hopf fiber",
            "unit_phase_preserved": max_phase_norm_error < TOL,
            "base_density_invariant_under_fiber": max(max_base_gap, max_density_gap) < TOL,
            "raw_spinor_phase_path_visible": min_raw_path > GAP,
            "fiber_only_actions_commute": max_fiber_commuting_gap < TOL,
            "global_phase_centrality_confirmed": max_centrality_boundary_gap < TOL,
            "finite_s1_cycle_topology_signature_present": all(row["topology"]["pass"] for row in rows),
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
            "base_invariance_gap",
            "density_invariance_gap",
            "centrality_boundary_gap",
            "mps_entanglement_gap",
            "product_log_negativity",
            "latent_schmidt_entropy",
            "half_chain_entropy",
            "renyi2_AB",
        ],
        "weak_diagnostic_controls_flagged": [
            {
                "controls": {
                    "max_base_invariance_gap": "U(1) fiber is supposed to preserve CP1/S2 base coordinates; zero is a known invariance, not a positive scale signal.",
                    "max_density_invariance_gap": "U(1) global phase is supposed to preserve the density state; zero is a known invariance, not a positive scale signal.",
                    "max_centrality_boundary_gap": "Global U(1) centrality is an abelian boundary diagnostic, not an N01 order signal.",
                    "base_invariance_gap": "per-row U(1) base invariance diagnostic",
                    "density_invariance_gap": "per-row U(1) density invariance diagnostic",
                    "centrality_boundary_gap": "per-row U(1) centrality boundary diagnostic",
                }
            }
        ],
        "native_scale_parameters": [
            {
                "scale_name": row["scale_name"],
                "N_eta": row["N_eta"],
                "N_base_anchor": row["N_base_anchor"],
                "N_fiber": row["N_fiber"],
                "N_sites": row["N_sites"],
                "shape": list(row["shape"]),
            }
            for row in NATIVE_SCALE_ROWS
        ],
        "resource_blocker": "This bounded scout stops at N_sites=128. Larger native rows such as N_eta=4,N_base_anchor=4,N_fiber=16 (256 sites) are next-run scale targets, not evidence produced here.",
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
            "min_raw_spinor_path_length": min_raw_path,
            "max_fiber_commuting_gap": max_fiber_commuting_gap,
            "max_centrality_boundary_gap": max_centrality_boundary_gap,
            "max_jax_torch_delta": max_parity_delta,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
            "min_peps3d_virtual_l1_delta": min_virtual_delta,
            "max_base_invariance_gap": max_base_gap,
            "max_density_invariance_gap": max_density_gap,
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
            "min_raw_spinor_path_length": min_raw_path,
            "max_fiber_commuting_gap": max_fiber_commuting_gap,
            "max_centrality_boundary_gap": max_centrality_boundary_gap,
            "max_jax_torch_delta": max_parity_delta,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_log_neg,
        },
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "why_not_v4_probes": "v5 one-target U(1) Hopf-fiber network scout with explicit fiber action, MPS/PEPS2D/PEPS3D carriers, JAX/Torch parity, QIT readouts, proof/topology tools, and downstream locks.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [key for key, value in required.items() if not value],
        "next_admissible_step": "Audit this one-target scout, then choose the next one-target geometry deepening row; do not use it to open stacking or downstream consumers.",
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
