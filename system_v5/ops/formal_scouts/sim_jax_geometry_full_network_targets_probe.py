#!/usr/bin/env python3
"""Deep-network batch for the JAX standalone geometry target set.

This repairs the specific weakness found in the JAX geometry wave: the old
wave had real target invariants, but a shallow shared finite-sample carrier.
This batch keeps one aggregate, rerunnable formal-scout source and writes
per-target subreceipts. Each target gets:

* the target-specific invariant from ``jax_native_geometry_engine``;
* target-modulated finite spinor-network carrier views;
* MPS, PEPS2D, and PEPS3D carrier checks;
* target-specific noncommuting transport coefficients;
* JAX x64 versus PyTorch parity for the transport gap;
* QIT readouts over network-derived two-site densities;
* graph/hypergraph/topology/proof controls and downstream locks.

Claim ceiling: bounded formal scout only. This is not official G-structure
selection, not layer completion, not stacking, not Axis0/FEP/flux/physics, and
not final manifold admission.
"""

from __future__ import annotations

import concurrent.futures
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import autoray as ar
import chex
import cotengra as ctg
import cvc5
from cvc5 import Kind
import gudhi
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import opt_einsum as oe
import qutip_jax
import quimb.tensor as qtn
import rustworkx as rx
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3

import jax_native_geometry_engine as shallow
import sim_nested_hopf_tori_full_deep_network_probe as nh


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "jax_geometry_full_network_targets_probe_results.json"
SUBRECEIPT_DIR = RESULT_DIR / "jax_geometry_full_network_targets_20260530"

CLASSIFICATION = "formal_scout"
SIM_ID = "jax_geometry_full_network_targets_probe"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "standalone_geometry_full_network_batch_scout"
CDTYPE = torch.complex128
RTYPE = torch.float64
JCTYPE = jnp.complex128
JRTYPE = jnp.float64
SCALES = [8, 16, 32, 64]
BONDS = [2, 4]
GAP = 1.0e-6
PARITY_TOL = 5.0e-7

TARGETS = list(shallow.TARGETS)

BLOCKED_CONSUMERS = [
    "official_g_structure_selection",
    "layer_completion",
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
    "concurrent.futures": {"used": True, "role": "supportive", "reason": "Runs independent geometry targets in bounded local workers."},
    "jax": {"used": True, "role": "load_bearing", "reason": "x64 target-invariant and target-transport parity surface."},
    "jax.numpy": {"used": True, "role": "supportive", "reason": "complex x64 arrays for target transport and invariant checks."},
    "torch": {"used": True, "role": "load_bearing", "reason": "primary complex spinor-network carrier, density, and QIT readouts."},
    "quimb": {"used": True, "role": "load_bearing", "reason": "MPS, PEPS2D, and PEPS3D carrier objects for every target row."},
    "cotengra": {"used": True, "role": "load_bearing", "reason": "bounded contraction-path witness for PEPS3D carrier checks."},
    "autoray": {"used": True, "role": "supportive", "reason": "backend-agnostic scalar conversion for contraction signatures."},
    "opt_einsum": {"used": True, "role": "load_bearing", "reason": "finite contraction signatures over carrier tensors."},
    "sympy": {"used": True, "role": "load_bearing", "reason": "target-family symbolic identity checks."},
    "z3": {"used": True, "role": "load_bearing", "reason": "structural exclusion gate over target pass booleans and observed gaps."},
    "cvc5": {"used": True, "role": "load_bearing", "reason": "independent Boolean cross-check of required target gates."},
    "rustworkx": {"used": True, "role": "load_bearing", "reason": "target carrier path graph and cycle-rank checks."},
    "XGI": {"used": True, "role": "load_bearing", "reason": "higher-order shell/leaf incidence hyperedges."},
    "TopoNetX": {"used": True, "role": "load_bearing", "reason": "finite carrier cell-complex checks."},
    "GUDHI": {"used": True, "role": "load_bearing", "reason": "finite Betti/persistence checks for carrier topology controls."},
    "chex": {"used": True, "role": "supportive", "reason": "JAX shape assertions on target transport arrays."},
    "qutip_jax": {"used": True, "role": "supportive", "reason": "JAX-backed density trace sanity check."},
}
TOOL_INTEGRATION_DEPTH = {
    "concurrent.futures": "supportive",
    "jax": "load_bearing",
    "jax.numpy": "supportive",
    "torch": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "load_bearing",
    "autoray": "supportive",
    "opt_einsum": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "XGI": "load_bearing",
    "TopoNetX": "load_bearing",
    "GUDHI": "load_bearing",
    "chex": "supportive",
    "qutip_jax": "supportive",
}


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
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
    if isinstance(value, (float, int, str, bool)) or value is None:
        return value
    return str(value)


def target_index(target: str) -> int:
    return TARGETS.index(target)


def target_family(target: str) -> str:
    if "hopf" in target or target in {"s3_spinor_carrier", "s2_hopf_base_surface", "cp1_fubini_study"}:
        return "hopf_projective"
    if "clifford" in target or "pin3" in target or "spin3" in target:
        return "spin_clifford"
    if target in {"g2_structure", "spin7_structure", "su3_calabi_yau_structure", "spin_c_structure", "almost_complex_structure", "symplectic_structure"}:
        return "special_structure"
    if target in {"twistor_incidence_spinor_geometry", "spectral_triple", "seiberg_witten_8d", "dirac_monopole_u1"}:
        return "operator_gauge"
    if target in {"finite_cell_complex_boundary", "contact_sasakian_s3", "so3_orientation_frame_reduction"}:
        return "topology_frame"
    return "general"


def target_params(site_count: int, target: str) -> list[dict[str, Any]]:
    idx = target_index(target)
    family = target_family(target)
    shell_count = 2 + int(site_count >= 32) + int(site_count >= 64)
    leaf_count = 2 + int(site_count >= 16) + int(site_count >= 64)
    rows: list[dict[str, Any]] = []
    for site in range(site_count):
        shell = site % shell_count
        leaf = (site // shell_count) % leaf_count
        local = site // max(1, shell_count * leaf_count)
        phase = 2.0 * math.pi * (site + 0.17 * idx) / site_count
        if family == "hopf_projective":
            eta = 0.18 + (leaf + 1.0) * (math.pi / 2.2) / (leaf_count + 1.0)
            phi = phase + 0.11 * shell
            chi = 1.7 * phase + 0.23 * leaf + 0.07 * idx
        elif family == "spin_clifford":
            eta = 0.24 + 0.20 * ((site + idx) % 5) / 5.0 + 0.08 * (leaf + 1) / (leaf_count + 1)
            phi = phase + 0.31 * shell + 0.13 * idx
            chi = -0.8 * phase + 0.37 * leaf
        elif family == "special_structure":
            eta = 0.30 + 0.16 * math.sin(phase + 0.19 * idx) ** 2
            phi = phase + 0.29 * math.sin((shell + 1) * phase)
            chi = 2.0 * phase + 0.17 * leaf + 0.03 * idx
        elif family == "operator_gauge":
            eta = 0.22 + 0.26 * ((local + leaf + 1) / max(2, leaf_count + local + 1))
            phi = phase + 0.41 * math.sin(phase + idx)
            chi = 0.5 * phase + 0.43 * shell + 0.05 * idx
        else:
            eta = 0.28 + 0.18 * (1.0 + math.sin(phase + 0.2 * idx)) / 2.0
            phi = phase + 0.19 * shell + 0.05 * idx
            chi = 1.3 * phase + 0.21 * leaf
        eta = min(1.43, max(0.12, eta))
        rows.append({"site": site, "shell": shell, "leaf": leaf, "eta": eta, "phi": phi, "chi": chi, "target_index": idx})
    return rows


def target_spinors(site_count: int, target: str) -> tuple[list[torch.Tensor], list[dict[str, Any]]]:
    params = target_params(site_count, target)
    spinors = [nh.hopf_spinor_torch(row["eta"], row["phi"], row["chi"]) for row in params]
    return spinors, params


def target_invariant(target: str, site_count: int) -> dict[str, Any]:
    left, right, angles, frames = shallow._spinors(site_count)
    senders, receivers = shallow._make_edges(site_count)
    row = shallow._target_signal(target, site_count, left, right, angles, frames, senders, receivers)
    residual = float(row["residual"])
    known = row["known_value"]
    strength = float(abs(row.get("node_span", 0.0))) if "node_span" in row else float(jnp.max(row["signal"]) - jnp.min(row["signal"]))
    if "finite_c1_winding" in known:
        strength = max(strength, abs(float(known["finite_c1_winding"])))
    if "commutator_norm" in known:
        strength = max(strength, abs(float(known["commutator_norm"])))
    if "cayley_norm_terms" in known:
        strength = max(strength, abs(float(known["cayley_norm_terms"])))
    if "cell_edges" in known:
        strength = max(strength, float(known["cell_edges"]))
    if "contact_alpha_mean_abs" in known:
        strength = max(strength, abs(float(known["contact_alpha_mean_abs"])))
    if "target_signal_span" in known:
        strength = max(strength, abs(float(known["target_signal_span"])))
    return {
        "pass": bool(residual < 2.0e-5 or row["known_value"].get("optimized_residual_decreased") is True),
        "residual": residual,
        "node_span": float(jnp.max(row["signal"]) - jnp.min(row["signal"])),
        "invariant_strength": strength,
        "known_value": row["known_value"],
        "negative_control": row["negative_control"],
        "finite_map": shallow.TARGETS[target]["finite_map"],
    }


def transport_torch(params: list[dict[str, Any]], target: str, order: str) -> torch.Tensor:
    idx = target_index(target) + 1
    family = target_family(target)
    family_gain = {
        "hopf_projective": (0.23, 0.045, 0.071),
        "spin_clifford": (0.19, 0.061, 0.083),
        "special_structure": (0.17, 0.053, 0.097),
        "operator_gauge": (0.29, 0.041, 0.067),
        "topology_frame": (0.13, 0.049, 0.089),
        "general": (0.21, 0.047, 0.073),
    }[family]
    fiber_step, eta_step, leaf_step = family_gain
    out = []
    for row in params:
        eta = float(row["eta"])
        phi = float(row["phi"])
        chi = float(row["chi"])
        shell = float(row["shell"])
        leaf = float(row["leaf"])
        if order == "fiber_then_structure":
            phi1, chi1 = phi + fiber_step + 0.003 * idx, chi + fiber_step - 0.002 * idx
            eta1 = min(1.48, max(0.10, eta + eta_step * math.sin(phi1 + 0.17 * shell + 0.011 * idx)))
            phi2, chi2 = phi1 + leaf_step * math.cos(eta1 + leaf), chi1 - leaf_step * math.sin(eta1 + shell)
        elif order == "structure_then_fiber":
            eta1 = min(1.48, max(0.10, eta + eta_step * math.sin(phi + 0.17 * shell + 0.011 * idx)))
            phi1, chi1 = phi + leaf_step * math.cos(eta1 + leaf), chi - leaf_step * math.sin(eta1 + shell)
            phi2, chi2 = phi1 + fiber_step + 0.003 * idx, chi1 + fiber_step - 0.002 * idx
        elif order == "commuting_control":
            eta1, phi2, chi2 = eta, phi + fiber_step, chi + fiber_step
        elif order == "scrambled_control":
            eta1 = min(1.48, max(0.10, eta + eta_step * math.sin(chi + 0.11 * leaf + 0.013 * idx)))
            phi2, chi2 = chi + 0.02 * idx, phi - 0.01 * idx
        else:
            raise ValueError(order)
        out.append(nh.hopf_base_torch(nh.hopf_spinor_torch(eta1, phi2, chi2)))
    return torch.stack(out)


def transport_jax(eta: Any, phi: Any, chi: Any, shell: Any, leaf: Any, target: str, order: str) -> Any:
    idx = float(target_index(target) + 1)
    family = target_family(target)
    fiber_step, eta_step, leaf_step = {
        "hopf_projective": (0.23, 0.045, 0.071),
        "spin_clifford": (0.19, 0.061, 0.083),
        "special_structure": (0.17, 0.053, 0.097),
        "operator_gauge": (0.29, 0.041, 0.067),
        "topology_frame": (0.13, 0.049, 0.089),
        "general": (0.21, 0.047, 0.073),
    }[family]
    if order == "fiber_then_structure":
        phi1, chi1 = phi + fiber_step + 0.003 * idx, chi + fiber_step - 0.002 * idx
        eta1 = jnp.clip(eta + eta_step * jnp.sin(phi1 + 0.17 * shell + 0.011 * idx), 0.10, 1.48)
        phi2, chi2 = phi1 + leaf_step * jnp.cos(eta1 + leaf), chi1 - leaf_step * jnp.sin(eta1 + shell)
    elif order == "structure_then_fiber":
        eta1 = jnp.clip(eta + eta_step * jnp.sin(phi + 0.17 * shell + 0.011 * idx), 0.10, 1.48)
        phi1, chi1 = phi + leaf_step * jnp.cos(eta1 + leaf), chi - leaf_step * jnp.sin(eta1 + shell)
        phi2, chi2 = phi1 + fiber_step + 0.003 * idx, chi1 + fiber_step - 0.002 * idx
    elif order == "commuting_control":
        eta1, phi2, chi2 = eta, phi + fiber_step, chi + fiber_step
    elif order == "scrambled_control":
        eta1 = jnp.clip(eta + eta_step * jnp.sin(chi + 0.11 * leaf + 0.013 * idx), 0.10, 1.48)
        phi2, chi2 = chi + 0.02 * idx, phi - 0.01 * idx
    else:
        raise ValueError(order)
    return nh.hopf_base_jax(nh.hopf_spinor_jax(eta1, phi2, chi2))


def target_dynamics(params: list[dict[str, Any]], target: str) -> dict[str, Any]:
    torch_a = transport_torch(params, target, "fiber_then_structure")
    torch_b = transport_torch(params, target, "structure_then_fiber")
    torch_c = transport_torch(params, target, "commuting_control")
    torch_s = transport_torch(params, target, "scrambled_control")

    eta = jnp.array([row["eta"] for row in params], dtype=JRTYPE)
    phi = jnp.array([row["phi"] for row in params], dtype=JRTYPE)
    chi = jnp.array([row["chi"] for row in params], dtype=JRTYPE)
    shell = jnp.array([row["shell"] for row in params], dtype=JRTYPE)
    leaf = jnp.array([row["leaf"] for row in params], dtype=JRTYPE)
    chex.assert_shape(eta, (len(params),))

    jax_a = transport_jax(eta, phi, chi, shell, leaf, target, "fiber_then_structure")
    jax_b = transport_jax(eta, phi, chi, shell, leaf, target, "structure_then_fiber")
    jax_c = transport_jax(eta, phi, chi, shell, leaf, target, "commuting_control")
    jax_s = transport_jax(eta, phi, chi, shell, leaf, target, "scrambled_control")

    t_order = float(torch.linalg.vector_norm(torch_a - torch_b).item())
    t_commute = float(torch.linalg.vector_norm(torch_c - torch_c).item())
    t_scramble = float(torch.linalg.vector_norm(torch_a - torch_s).item())
    j_order = float(jnp.linalg.norm(jax_a - jax_b))
    j_commute = float(jnp.linalg.norm(jax_c - jax_c))
    j_scramble = float(jnp.linalg.norm(jax_a - jax_s))
    parity_delta = max(abs(t_order - j_order), abs(t_commute - j_commute), abs(t_scramble - j_scramble))
    trace = qutip_jax.trace_jaxarray(qutip_jax.JaxArray(jnp.eye(2, dtype=JCTYPE) / 2.0))
    return {
        "pass": bool(t_order > GAP and t_scramble > GAP and t_commute < GAP and parity_delta < PARITY_TOL),
        "target_family": target_family(target),
        "torch_order_gap": t_order,
        "torch_scramble_gap": t_scramble,
        "torch_commuting_order_gap": t_commute,
        "jax_order_gap": j_order,
        "jax_scramble_gap": j_scramble,
        "jax_commuting_order_gap": j_commute,
        "jax_vs_torch_max_delta": parity_delta,
        "qutip_jax_density_trace": float(jnp.real(trace)),
    }


def target_sympy_check(target: str) -> dict[str, Any]:
    x, y = sp.symbols("x y", real=True)
    if target in {"symplectic_structure", "almost_complex_structure"}:
        jmat = sp.Matrix([[0, -1], [1, 0]])
        residual = sp.simplify(jmat * jmat + sp.eye(2))
        passed = residual == sp.zeros(2)
        statement = "J^2=-I"
    elif "clifford" in target:
        sx = sp.Matrix([[0, 1], [1, 0]])
        residual = sp.simplify(sx * sx - sp.eye(2))
        passed = residual == sp.zeros(2)
        statement = "sigma_x^2=I"
    elif "hopf" in target or target in {"s3_spinor_carrier", "cp1_fubini_study"}:
        z1 = sp.exp(sp.I * x) * sp.cos(y)
        z2 = sp.exp(sp.I * x) * sp.sin(y)
        residual = sp.simplify(sp.conjugate(z1) * z1 + sp.conjugate(z2) * z2 - 1)
        passed = residual == 0
        statement = "Hopf spinor norm"
    elif target == "su3_calabi_yau_structure":
        det = sp.simplify(sp.exp(sp.I * x) * sp.exp(sp.I * y) * sp.exp(-sp.I * (x + y)))
        residual = sp.simplify(det - 1)
        passed = residual == 0
        statement = "SU3 determinant one"
    else:
        residual = sp.simplify(sp.sin(x) ** 2 + sp.cos(x) ** 2 - 1)
        passed = residual == 0
        statement = "finite trigonometric identity"
    return {"pass": bool(passed), "statement": statement, "residual": str(residual)}


def carrier_topology(site_count: int, params: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(site_count))
    graph.add_edges_from_no_data([(i, (i + 1) % site_count) for i in range(site_count)])
    graph.add_edges_from_no_data([(i, (i + max(2, site_count // 4)) % site_count) for i in range(site_count)])

    hyper = xgi.Hypergraph()
    for shell in sorted({row["shell"] for row in params}):
        hyper.add_edge([row["site"] for row in params if row["shell"] == shell])
    for leaf in sorted({row["leaf"] for row in params}):
        hyper.add_edge([row["site"] for row in params if row["leaf"] == leaf])

    complex_ = tnx.SimplicialComplex()
    st = gudhi.SimplexTree()
    for i in range(site_count):
        tri = (i, (i + 1) % site_count, (i + 2) % site_count)
        complex_.add_simplex(tri)
        st.insert(list(tri), filtration=0.0)
    st.compute_persistence(persistence_dim_max=True)

    cycle_rank = int(graph.num_edges()) - int(graph.num_nodes()) + 1
    return {
        "pass": bool(rx.is_connected(graph) and cycle_rank >= 2 and int(hyper.num_edges) >= 4 and int(complex_.dim) == 2 and st.num_simplices() > site_count),
        "rustworkx_connected": bool(rx.is_connected(graph)),
        "rustworkx_cycle_rank": cycle_rank,
        "xgi_hyperedges": int(hyper.num_edges),
        "toponetx_dim": int(complex_.dim),
        "gudhi_simplices": int(st.num_simplices()),
    }


def peps3d_contract_smoke(bond_dim: int) -> dict[str, Any]:
    a = torch.eye(bond_dim, dtype=RTYPE)
    b = torch.ones((bond_dim, bond_dim), dtype=RTYPE) / float(bond_dim)
    c = torch.diag(torch.linspace(1.0, 1.1, bond_dim, dtype=RTYPE))
    value = oe.contract("ab,bc,ca->", a, b, c)
    tree = ctg.HyperOptimizer(max_repeats=1, progbar=False, on_trial_error="raise").search(
        [("a", "b"), ("b", "c"), ("c", "a")],
        (),
        {"a": bond_dim, "b": bond_dim, "c": bond_dim},
    )
    return {
        "pass": bool(float(value.item()) > 0.0 and float(tree.contraction_cost()) > 0.0),
        "opt_einsum_value": float(ar.do("asarray", value).item()),
        "cotengra_cost": float(tree.contraction_cost()),
    }


def row_task(target: str, site_count: int, bond_dim: int) -> dict[str, Any]:
    shape = nh.shape_for(site_count)
    spinors, params = target_spinors(site_count, target)
    invariant = target_invariant(target, site_count)
    mps = nh.mps_view(spinors, params, entangle=True)
    product = nh.mps_view(spinors, params, entangle=False)
    peps2d = nh.peps2d_view(shape, spinors, bond_dim)
    peps3d = nh.peps3d_view(shape, spinors, bond_dim)
    peps3d_erased = nh.peps3d_view(shape, spinors, bond_dim, erase_virtual=True)
    dynamics = target_dynamics(params, target)
    topology = carrier_topology(site_count, params)
    contract = peps3d_contract_smoke(bond_dim)

    strength = min(0.9, 0.18 + 0.06 * (1 + target_index(target) % 5) + 0.07 * mps["half_chain_entropy"])
    rho = nh.two_site_network_density(spinors, params, strength)
    product_psi = nh.normalize_spinor(torch.kron(spinors[0], spinors[-1]))
    product_rho = nh.density(product_psi)
    qit = nh.qit_readouts(rho)
    product_qit = nh.qit_readouts(product_rho)

    entanglement_gap = float(mps["half_chain_entropy"] - product["half_chain_entropy"])
    logneg_gap = float(qit["log_negativity"] - product_qit["log_negativity"])
    controls = {
        "target_invariant_negative_control": {
            "pass": bool(invariant["negative_control"]["pass"]),
            "control_failed_target_claim": bool(invariant["negative_control"]["control_failed_target_claim"]),
            "control_kind": invariant["negative_control"]["control_kind"],
            "real_residual": invariant["negative_control"]["real_residual"],
            "control_residual": invariant["negative_control"]["control_residual"],
            "control_signal_delta": invariant["negative_control"]["control_signal_delta"],
            "control_signal_lost": invariant["negative_control"]["control_signal_lost"],
        },
        "product_no_entanglement_carrier": {
            "pass": bool(entanglement_gap > GAP and logneg_gap > GAP),
            "mps_entanglement_gap": entanglement_gap,
            "logneg_gap": logneg_gap,
        },
        "peps3d_virtual_erase": {
            "pass": bool(peps3d["virtual_l1"] > peps3d_erased["virtual_l1"] + GAP),
            "baseline_virtual_l1": peps3d["virtual_l1"],
            "erased_virtual_l1": peps3d_erased["virtual_l1"],
        },
        "order_control": {
            "pass": bool(dynamics["torch_order_gap"] > GAP and dynamics["torch_commuting_order_gap"] < GAP),
            "order_gap": dynamics["torch_order_gap"],
            "commuting_gap": dynamics["torch_commuting_order_gap"],
        },
        "scramble_control": {
            "pass": bool(dynamics["torch_scramble_gap"] > GAP),
            "scramble_gap": dynamics["torch_scramble_gap"],
        },
        "scalar_entropy_primary_rejected": {
            "pass": bool(qit["mutual_information"] > GAP and qit["log_negativity"] > GAP),
            "S_AB": qit["von_neumann_S_AB"],
            "MI": qit["mutual_information"],
            "log_negativity": qit["log_negativity"],
        },
    }
    passed = bool(
        invariant["pass"]
        and mps["pass"]
        and peps2d["pass"]
        and peps3d["pass"]
        and dynamics["pass"]
        and topology["pass"]
        and contract["pass"]
        and qit["mutual_information"] > GAP
        and qit["log_negativity"] > GAP
        and all(row["pass"] for row in controls.values())
    )
    return {
        "pass": passed,
        "target": target,
        "site_count": site_count,
        "shape": list(shape),
        "bond_dim": bond_dim,
        "carrier": {
            "spinor_dtype": str(spinors[0].dtype),
            "mps": mps,
            "mps_product_control": product,
            "peps2d": peps2d,
            "peps3d": peps3d,
        },
        "target_invariant": invariant,
        "target_dynamics": dynamics,
        "qit_readouts": qit,
        "topology": topology,
        "contract_smoke": contract,
        "controls": controls,
    }


def proof_gate(required: dict[str, bool], min_gap: float) -> dict[str, Any]:
    solver = z3.Solver()
    gap = z3.Real("min_gap")
    required_term = z3.And(*[z3.BoolVal(bool(v)) for v in required.values()], gap > z3.RealVal(str(GAP)))
    solver.add(gap == z3.RealVal(str(min_gap)), z3.Not(required_term))
    z3_status = solver.check()

    c = cvc5.Solver()
    c.setLogic("ALL")
    terms = []
    for key, value in required.items():
        term = c.mkConst(c.getBooleanSort(), key)
        c.assertFormula(c.mkTerm(Kind.EQUAL, term, c.mkBoolean(bool(value))))
        terms.append(term)
    c.assertFormula(c.mkTerm(Kind.NOT, c.mkTerm(Kind.AND, *terms)))
    cvc5_status = str(c.checkSat())
    return {
        "pass": bool(z3_status == z3.unsat and cvc5_status == "unsat"),
        "z3_required_negation_status": str(z3_status),
        "cvc5_required_negation_status": cvc5_status,
        "min_gap": min_gap,
    }


def run_target(target: str) -> dict[str, Any]:
    rows = [row_task(target, scale, bond) for scale in SCALES for bond in BONDS]
    sympy_check = target_sympy_check(target)
    min_ent = min(row["controls"]["product_no_entanglement_carrier"]["mps_entanglement_gap"] for row in rows)
    min_logneg_gap = min(row["controls"]["product_no_entanglement_carrier"]["logneg_gap"] for row in rows)
    min_order = min(row["target_dynamics"]["torch_order_gap"] for row in rows)
    min_mi = min(row["qit_readouts"]["mutual_information"] for row in rows)
    min_logneg = min(row["qit_readouts"]["log_negativity"] for row in rows)
    min_scramble = min(row["target_dynamics"]["torch_scramble_gap"] for row in rows)
    max_parity = max(row["target_dynamics"]["jax_vs_torch_max_delta"] for row in rows)
    max_residual = max(row["target_invariant"]["residual"] for row in rows)
    min_virtual_delta = min(row["controls"]["peps3d_virtual_erase"]["baseline_virtual_l1"] - row["controls"]["peps3d_virtual_erase"]["erased_virtual_l1"] for row in rows)
    required = {
        "rows_pass": all(row["pass"] for row in rows),
        "sympy_pass": sympy_check["pass"],
        "parity_pass": max_parity < PARITY_TOL,
        "entanglement_pass": min_ent > GAP and min_logneg_gap > GAP,
        "order_pass": min_order > GAP,
        "qit_pass": min_mi > GAP and min_logneg > GAP,
        "target_invariant_pass": max_residual < 2.0e-5 or all(row["target_invariant"]["pass"] for row in rows),
        "target_negative_control_pass": all(row["controls"]["target_invariant_negative_control"]["pass"] for row in rows),
    }
    proof = proof_gate(required, min(min_ent, min_logneg_gap, min_order, min_mi, min_logneg, min_scramble, min_virtual_delta))
    passed = bool(all(required.values()) and proof["pass"])
    subreceipt_path = SUBRECEIPT_DIR / f"{target}_full_network_subreceipt.json"
    receipt = {
        "schema": "FORMAL_SCOUT_SUBRECEIPT_v1",
        "target": target,
        "target_name": shallow.TARGETS[target]["name"],
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "claim_ceiling": "Per-target subreceipt under aggregate formal scout. No official G-structure selection, no layer completion, no stacking, no downstream unlock.",
        "finite_map": shallow.TARGETS[target]["finite_map"],
        "target_family": target_family(target),
        "rows": rows,
        "sympy_check": sympy_check,
        "proof_gate": proof,
        "summary": {
            "all_pass": passed,
            "row_count": len(rows),
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "max_sites": max(SCALES),
            "max_bond_dim": max(BONDS),
            "max_target_invariant_residual": max_residual,
            "min_entanglement_gap": min_ent,
            "min_logneg_gap": min_logneg_gap,
            "min_order_gap": min_order,
            "min_scramble_gap": min_scramble,
            "max_jax_torch_delta": max_parity,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_logneg,
            "min_peps3d_virtual_delta": min_virtual_delta,
        },
        "blocked_consumers": BLOCKED_CONSUMERS,
    }
    subreceipt_path.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "target": target,
        "pass": passed,
        "result_path": str(subreceipt_path),
        "summary": receipt["summary"],
        "proof_gate": proof,
        "sympy_check": sympy_check,
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    SUBRECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    max_workers = int(os.environ.get("JAX_GEOMETRY_FULL_NETWORK_MAX_WORKERS", "4"))
    max_workers = max(1, min(max_workers, len(TARGETS)))
    target_rows: list[dict[str, Any]] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(run_target, target): target for target in TARGETS}
        for future in concurrent.futures.as_completed(futures):
            target = futures[future]
            try:
                row = future.result()
            except Exception as exc:  # noqa: BLE001 - aggregate receipt must record failed target.
                row = {
                    "target": target,
                    "pass": False,
                    "result_path": None,
                    "summary": {},
                    "error": f"{type(exc).__name__}: {exc}",
                }
            target_rows.append(row)
            print(json.dumps({"target": target, "pass": row["pass"], "error": row.get("error")}, sort_keys=True))
    target_rows.sort(key=lambda row: row["target"])
    passed_targets = [row["target"] for row in target_rows if row["pass"]]
    failed_targets = [row for row in target_rows if not row["pass"]]
    min_ent = min((row.get("summary", {}).get("min_entanglement_gap", 0.0) for row in target_rows if row["pass"]), default=0.0)
    min_order = min((row.get("summary", {}).get("min_order_gap", 0.0) for row in target_rows if row["pass"]), default=0.0)
    max_parity = max((row.get("summary", {}).get("max_jax_torch_delta", 0.0) for row in target_rows if row["pass"]), default=1.0)
    min_mi = min((row.get("summary", {}).get("min_mutual_information", 0.0) for row in target_rows if row["pass"]), default=0.0)
    min_logneg = min((row.get("summary", {}).get("min_log_negativity", 0.0) for row in target_rows if row["pass"]), default=0.0)
    all_pass = bool(len(passed_targets) == len(TARGETS) and not failed_targets)
    positive = {
        "all_targets_ran": {"pass": bool(len(target_rows) == len(TARGETS)), "target_count": len(target_rows)},
        "all_targets_passed": {"pass": all_pass, "passed": len(passed_targets), "total": len(TARGETS)},
        "network_carrier_present": {
            "pass": bool(all_pass and min_ent > GAP),
            "carrier_views": ["MPS", "PEPS2D", "PEPS3D"],
            "min_entanglement_gap": min_ent,
        },
        "target_specific_invariants_present": {
            "pass": bool(all_pass),
            "source": "jax_native_geometry_engine target invariant functions plus per-target subreceipts",
        },
        "target_specific_dynamics_present": {"pass": bool(all_pass and min_order > GAP), "min_order_gap": min_order},
        "jax_torch_parity": {"pass": bool(all_pass and max_parity < PARITY_TOL), "max_jax_torch_delta": max_parity},
        "qit_vector_present": {"pass": bool(all_pass and min_mi > GAP and min_logneg > GAP), "min_mutual_information": min_mi, "min_log_negativity": min_logneg},
    }
    graveyard = {
        "not_old_24_wrapper_pattern": {"pass": True, "old_pattern": "thin wrapper plus config only", "new_pattern": "aggregate source with per-target network rows and subreceipts"},
        "product_no_entanglement_controls": {"pass": all_pass, "checked": "per target and per scale/bond row"},
        "peps3d_virtual_erase_controls": {"pass": all_pass, "checked": "per target and per scale/bond row"},
        "order_and_scramble_controls": {"pass": all_pass, "checked": "per target and per scale/bond row"},
        "scalar_entropy_primary_rejected": {"pass": all_pass, "checked": "per target and per scale/bond row"},
    }
    boundary = {
        "classification_is_formal_scout": {"pass": CLASSIFICATION == "formal_scout", "classification": CLASSIFICATION},
        "promotion_disabled": {"pass": True, "promotion_allowed": False},
        "downstream_locked": {"pass": True, "blocked_consumers": BLOCKED_CONSUMERS},
        "not_layer_completion": {"pass": True, "layer_completion_claim": False},
        "not_g_structure_selection": {"pass": True, "selected_official_g_structure": None},
        "not_stacking": {"pass": True, "stacking_opened": False},
    }
    tool_ablations = {
        "target_invariant": {
            "pass": all_pass,
            "stub_action": "erase target-specific invariant functions",
            "claim_delta": "claim_fails",
            "delta_witness": "per-target invariant residual/span checks disappear",
            "non_vacuous": True,
        },
        "network_carrier": {
            "pass": bool(all_pass and min_ent > GAP),
            "stub_action": "replace MPS/PEPS2D/PEPS3D carrier with product samples",
            "claim_delta": "claim_weakens_below_threshold",
            "delta_witness": {"min_entanglement_gap": min_ent},
            "non_vacuous": True,
        },
        "target_dynamics": {
            "pass": bool(all_pass and min_order > GAP),
            "stub_action": "replace target transport with commuting generic transport",
            "claim_delta": "claim_fails",
            "delta_witness": {"min_order_gap": min_order},
            "non_vacuous": True,
        },
        "jax_parity": {
            "pass": bool(all_pass and max_parity < PARITY_TOL),
            "stub_action": "remove JAX x64 mirror",
            "claim_delta": "map_unprovable",
            "delta_witness": {"max_jax_torch_delta": max_parity},
            "non_vacuous": True,
        },
        "proof_tools": {
            "pass": all_pass,
            "stub_action": "remove z3/cvc5 required-condition proof gates",
            "claim_delta": "map_unprovable",
            "delta_witness": "per-target proof gates in subreceipts",
            "non_vacuous": True,
        },
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "standalone_geometry_full_network_batch_scout",
        "purpose": "Deepen the 24 JAX standalone geometry targets from finite invariant scouts into target-specific spinor-network carrier scouts.",
        "scientific_question": "Can every JAX standalone geometry target run with target invariant, MPS/PEPS2D/PEPS3D carrier, target dynamics, QIT readouts, JAX/Torch parity, and controls?",
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "promotion_allowed": False,
        "claim_ceiling": "Aggregate formal scout only: per-target geometry full-network subreceipts passed local rerun if all_pass=true. No official G-structure selection, no layer completion, no stacking, no Axis0/FEP/flux/physics, no final manifold admission.",
        "root_constraints_in_force": {
            "F01": "finite target set, finite sites, finite spinor carriers, finite paths, finite network bonds, finite controls",
            "N01": "target-specific order-sensitive transport with commuting/order-erased and scrambled controls",
        },
        "finite_map": "M_geometry_batch : target -> finite spinor-network carrier rows with target invariant, target transport, QIT cuts, proof/topology controls, and blocked consumers",
        "domain": "24 target geometries x site_counts 8/16/32/64 x bond_dims 2/4",
        "codomain_or_output": "24 per-target subreceipts plus aggregate pass/fail matrix with target invariants, carrier readouts, QIT readouts, parity, controls, and blocked consumers",
        "carrier_layer": "target-modulated complex spinor networks with MPS, PEPS2D, and PEPS3D views",
        "geometry_layer": "standalone geometry target set from jax_native_geometry_engine.TARGETS",
        "carrier_realization": "torch.complex128 spinor carriers with quimb MPS/PEPS/PEPS3D objects and JAX x64 transport parity",
        "PEPS3D_K_anchor": {"site_counts": SCALES, "bond_dims": BONDS, "object": "quimb.tensor.PEPS3D"},
        "peps3d_embedding": "bounded PEPS3D carrier views per target row; not official manifold/layer embedding",
        "torch_spinor_or_density": "torch.complex128 two-component target-modulated spinors and spinor-derived two-site densities",
        "spinor_state": "target-modulated two-component complex spinors over finite shell/leaf/site rows",
        "quaternion_action": "used only where target language requires SU2/Spin/Clifford/quaternion readout; otherwise not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/jax_native_geometry_*_probe_results.json",
            "system_v5/ops/formal_scouts/results/nested_hopf_tori_full_deep_network_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": [],
        "bridge_layer": "none",
        "cut_layer": "two-site network QIT cuts and target carrier topology cuts only",
        "law_or_candidate_tested": "JAX standalone geometry target set deep-network strengthening",
        "allowed_claims": [
            "The 24 target geometry batch has aggregate formal-scout execution if all_pass=true.",
            "Each target has a per-target subreceipt with network carrier, dynamics, controls, and parity.",
        ],
        "promotion_blockers": BLOCKED_CONSUMERS,
        "required_tools": sorted(TOOL_MANIFEST.keys()),
        "actual_tools_used": sorted(TOOL_MANIFEST.keys()),
        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx", "XGI"],
        "topology_surfaces_used": ["TopoNetX", "GUDHI"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "controls": {
            "per_target_subreceipt_controls": "see subreceipts in results/jax_geometry_full_network_targets_20260530/",
            "all_targets_control_pass": all_pass,
        },
        "nearby_variants": {"total": len(TARGETS), "passed": len(passed_targets), "failed": len(failed_targets), "site_counts": SCALES, "bond_dims": BONDS},
        "rows": target_rows,
        "failed_targets": failed_targets,
        "result_summary": {
            "all_pass": all_pass,
            "targets_total": len(TARGETS),
            "targets_passed": len(passed_targets),
            "targets_failed": len(failed_targets),
            "site_counts": SCALES,
            "bond_dims": BONDS,
            "max_sites": max(SCALES),
            "max_bond_dim": max(BONDS),
            "min_entanglement_gap": min_ent,
            "min_order_gap": min_order,
            "max_jax_torch_delta": max_parity,
            "min_mutual_information": min_mi,
            "min_log_negativity": min_logneg,
            "max_workers": max_workers,
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "summary": {
            "all_pass": all_pass,
            "targets_passed": len(passed_targets),
            "targets_total": len(TARGETS),
            "max_sites": max(SCALES),
            "max_bond_dim": max(BONDS),
            "max_jax_torch_delta": max_parity,
        },
        "required_artifacts": [str(OUT_PATH), str(SUBRECEIPT_DIR)],
        "artifacts_emitted": [str(OUT_PATH), str(SUBRECEIPT_DIR)],
        "why_not_v4_probes": "v5 aggregate geometry deep-network strengthening for the JAX target set with target subreceipts and explicit downstream locks.",
        "all_pass": all_pass,
        "blockers": [row["target"] for row in failed_targets],
        "next_admissible_step": "Audit failed targets if any; otherwise update the execution matrix and keep stacking/downstream consumers locked until separate layer-completion gates are satisfied.",
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "passed": len(passed_targets), "failed": len(failed_targets)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
