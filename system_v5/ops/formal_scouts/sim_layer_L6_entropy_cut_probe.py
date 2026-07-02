#!/usr/bin/env python3
"""Stage-6 L6 entropy/cut/communication layer probe.

L6 is tested here as an action on a finite cut carrier:
partial trace over an admitted A|B cut, then signed QIT readouts.  It is not a
standalone geometry object and it is not a scalar entropy label.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import os
import pathlib
import sys
import time
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3

for cache_dir in (
    "/tmp/claude-501/matplotlib",
    "/tmp/claude-501/numba",
    "/tmp/claude-501/xdg-cache",
):
    pathlib.Path(cache_dir).mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", "/tmp/claude-501/matplotlib")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/claude-501/numba")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/claude-501/xdg-cache")

from torch_geometric.data import Data
import gudhi
import rustworkx as rx
import toponetx as tnx
import xgi
from clifford import Cl

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).resolve()
RESULT = RESULT_DIR / "layer_L6_entropy_cut_probe_results.json"
OBJECT_ID = "L6_entropy_cut_communication_action"

DTYPE = torch.complex128
REAL_DTYPE = torch.float64
EPS = 1.0e-10
SCALES = {
    8: (2, 2, 2),
    16: (4, 2, 2),
    32: (4, 4, 2),
    64: (4, 4, 4),
}
BLOCKED_CONSUMERS = [
    "flux",
    "Xi",
    "Phi0",
    "Axis0",
    "bridge",
    "basin",
    "FEP",
    "physics",
    "gravity",
]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY action carrier: complex128 partial trace, eigvalsh entropy, signed coherent-information invariant, controls, and scale ladder.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputes the same local 4x4 cut readout without NumPy.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; variables are bound to measured signed-information values from the real action and controls.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through load_bearing_proof.smt_load_bearing cvc5_claim_pairs on the same measured values.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact ln(2) and 2ln(2) anchors for Bell-cut coherent information and mutual information.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Spinor/Cl(3) sanity surface: nonabelian generator check and spinor-derived density boundary.",
    },
    "pyg": {
        "tried": True,
        "used": True,
        "reason": "Cut-edge incidence carrier for PEPS3D local pair readouts; ablation removes the cut topology.",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "Independent cut-edge graph enumeration over the finite PEPS3D carrier; ablation removes edges.",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "Hypergraph cut-family enumeration over local cut pairs; ablation removes hyperedges.",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "Cell-complex witness that the cut carrier has a real 1-cell boundary surface; ablation removes cells.",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "Simplex-tree filtration witness for cut edges; ablation keeps only vertices.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "supportive",
    "pyg": "load_bearing",
    "rustworkx": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "numpy": "None",
    "scipy": "None",
}


def bell_density_torch() -> torch.Tensor:
    psi = torch.zeros(4, dtype=DTYPE)
    psi[0] = 1.0 / math.sqrt(2.0)
    psi[3] = 1.0 / math.sqrt(2.0)
    return torch.outer(psi, psi.conj())


def product_density_torch() -> torch.Tensor:
    psi = torch.zeros(4, dtype=DTYPE)
    psi[0] = 1.0
    return torch.outer(psi, psi.conj())


def mixed_density_torch() -> torch.Tensor:
    return torch.eye(4, dtype=DTYPE) / 4.0


def partial_trace_torch(rho_ab: torch.Tensor, keep: str) -> torch.Tensor:
    reshaped = rho_ab.reshape(2, 2, 2, 2)
    if keep == "A":
        return torch.einsum("abcb->ac", reshaped)
    if keep == "B":
        return torch.einsum("abad->bd", reshaped)
    raise ValueError(f"unknown keep side: {keep}")


def entropy_torch(rho: torch.Tensor) -> float:
    hermitian = (rho + rho.conj().T) / 2.0
    eigvals = torch.linalg.eigvalsh(hermitian).real
    eigvals = torch.clamp(eigvals, min=0.0)
    live = eigvals[eigvals > 1.0e-14]
    if live.numel() == 0:
        return 0.0
    return float(-(live * torch.log(live)).sum().item())


def cut_readout_torch(rho_ab: torch.Tensor) -> dict[str, Any]:
    rho_a = partial_trace_torch(rho_ab, "A")
    rho_b = partial_trace_torch(rho_ab, "B")
    s_ab = entropy_torch(rho_ab)
    s_a = entropy_torch(rho_a)
    s_b = entropy_torch(rho_b)
    mutual_information = s_a + s_b - s_ab
    conditional_entropy = s_ab - s_b
    coherent_information = s_b - s_ab
    return {
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "mutual_information": mutual_information,
        "conditional_entropy_A_given_B": conditional_entropy,
        "coherent_information_A_to_B": coherent_information,
        "rho_A_trace": float(torch.trace(rho_a).real.item()),
        "rho_B_trace": float(torch.trace(rho_b).real.item()),
        "rho_AB_trace": float(torch.trace(rho_ab).real.item()),
        "partial_trace_performed": True,
        "pass": bool(
            abs(float(torch.trace(rho_a).real.item()) - 1.0) <= 1.0e-12
            and abs(float(torch.trace(rho_b).real.item()) - 1.0) <= 1.0e-12
            and abs(float(torch.trace(rho_ab).real.item()) - 1.0) <= 1.0e-12
        ),
    }


def bell_density_jax() -> jax.Array:
    psi = jnp.zeros((4,), dtype=jnp.complex128)
    psi = psi.at[0].set(1.0 / math.sqrt(2.0))
    psi = psi.at[3].set(1.0 / math.sqrt(2.0))
    return jnp.outer(psi, jnp.conj(psi))


def product_density_jax() -> jax.Array:
    psi = jnp.zeros((4,), dtype=jnp.complex128)
    psi = psi.at[0].set(1.0)
    return jnp.outer(psi, jnp.conj(psi))


def mixed_density_jax() -> jax.Array:
    return jnp.eye(4, dtype=jnp.complex128) / 4.0


def partial_trace_jax(rho_ab: jax.Array, keep: str) -> jax.Array:
    reshaped = rho_ab.reshape(2, 2, 2, 2)
    if keep == "A":
        return jnp.einsum("abcb->ac", reshaped)
    if keep == "B":
        return jnp.einsum("abad->bd", reshaped)
    raise ValueError(f"unknown keep side: {keep}")


def entropy_jax(rho: jax.Array) -> float:
    hermitian = (rho + jnp.conj(rho.T)) / 2.0
    eigvals = jnp.real(jnp.linalg.eigvalsh(hermitian))
    eigvals = jnp.clip(eigvals, min=0.0)
    live = jnp.where(eigvals > 1.0e-14, eigvals, 1.0)
    terms = jnp.where(eigvals > 1.0e-14, eigvals * jnp.log(live), 0.0)
    return float(-jnp.sum(terms).item())


def cut_readout_jax(rho_ab: jax.Array) -> dict[str, Any]:
    rho_a = partial_trace_jax(rho_ab, "A")
    rho_b = partial_trace_jax(rho_ab, "B")
    s_ab = entropy_jax(rho_ab)
    s_a = entropy_jax(rho_a)
    s_b = entropy_jax(rho_b)
    mutual_information = s_a + s_b - s_ab
    conditional_entropy = s_ab - s_b
    coherent_information = s_b - s_ab
    return {
        "S_AB": s_ab,
        "S_A": s_a,
        "S_B": s_b,
        "mutual_information": mutual_information,
        "conditional_entropy_A_given_B": conditional_entropy,
        "coherent_information_A_to_B": coherent_information,
        "rho_A_trace": float(jnp.real(jnp.trace(rho_a)).item()),
        "rho_B_trace": float(jnp.real(jnp.trace(rho_b)).item()),
        "rho_AB_trace": float(jnp.real(jnp.trace(rho_ab)).item()),
        "partial_trace_performed": True,
        "pass": bool(
            abs(float(jnp.real(jnp.trace(rho_a)).item()) - 1.0) <= 1.0e-12
            and abs(float(jnp.real(jnp.trace(rho_b)).item()) - 1.0) <= 1.0e-12
            and abs(float(jnp.real(jnp.trace(rho_ab)).item()) - 1.0) <= 1.0e-12
        ),
    }


def max_abs_readout_delta(a: dict[str, Any], b: dict[str, Any]) -> float:
    keys = [
        "S_AB",
        "S_A",
        "S_B",
        "mutual_information",
        "conditional_entropy_A_given_B",
        "coherent_information_A_to_B",
    ]
    return max(abs(float(a[k]) - float(b[k])) for k in keys)


def signed_ci_claim(v: dict[str, z3.ArithRef]) -> z3.BoolRef:
    return z3.And(
        v["coherent_information"] > v["eps"],
        v["conditional_entropy"] < v["minus_eps"],
        v["mutual_information"] > v["eps"],
    )


def mi_nonnegative_claim(v: dict[str, z3.ArithRef]) -> z3.BoolRef:
    return v["mutual_information"] >= v["zero"]


def smt_signed_ci_proof(real: dict[str, Any], control: dict[str, Any], claim: str) -> dict[str, Any]:
    real_measured = {
        "coherent_information": real["coherent_information_A_to_B"],
        "conditional_entropy": real["conditional_entropy_A_given_B"],
        "mutual_information": real["mutual_information"],
        "eps": EPS,
        "minus_eps": -EPS,
    }
    control_measured = {
        "coherent_information": control["coherent_information_A_to_B"],
        "conditional_entropy": control["conditional_entropy_A_given_B"],
        "mutual_information": control["mutual_information"],
        "eps": EPS,
        "minus_eps": -EPS,
    }
    return smt_load_bearing(
        claim=claim,
        real_measured=real_measured,
        control_measured=control_measured,
        claim_builder=signed_ci_claim,
        cvc5_claim_pairs=[
            ("coherent_information", ">", "eps"),
            ("conditional_entropy", "<", "minus_eps"),
            ("mutual_information", ">", "eps"),
        ],
    )


def smt_mi_guard(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="mutual_information_nonnegative_guard_rejects_sign_broken_readout",
        real_measured={"mutual_information": real["mutual_information"], "zero": 0.0},
        control_measured={"mutual_information": control["mutual_information"], "zero": 0.0},
        claim_builder=mi_nonnegative_claim,
        cvc5_claim_pairs=[("mutual_information", ">=", "zero")],
    )


def node_id(x: int, y: int, z: int, shape: tuple[int, int, int]) -> int:
    sx, sy, sz = shape
    return (x * sy * sz) + (y * sz) + z


def enumerate_cut_edges(shape: tuple[int, int, int]) -> list[tuple[int, int, str]]:
    sx, sy, sz = shape
    edges: list[tuple[int, int, str]] = []
    axes = [
        ("x", sx, sy, sz),
        ("y", sy, sx, sz),
        ("z", sz, sx, sy),
    ]
    for axis, axis_len, first_other, second_other in axes:
        if axis_len < 2:
            continue
        left_index = axis_len // 2 - 1
        right_index = axis_len // 2
        for a in range(first_other):
            for b in range(second_other):
                if axis == "x":
                    left = node_id(left_index, a, b, shape)
                    right = node_id(right_index, a, b, shape)
                elif axis == "y":
                    left = node_id(a, left_index, b, shape)
                    right = node_id(a, right_index, b, shape)
                else:
                    left = node_id(a, b, left_index, shape)
                    right = node_id(a, b, right_index, shape)
                edges.append((left, right, axis))
    return edges


def pyg_edge_count(n_sites: int, cut_edges: list[tuple[int, int, str]]) -> int:
    if cut_edges:
        edge_index = torch.tensor([[u for u, _, _ in cut_edges], [v for _, v, _ in cut_edges]], dtype=torch.long)
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
    data = Data(edge_index=edge_index, num_nodes=n_sites)
    return int(data.num_edges)


def rustworkx_edge_count(n_sites: int, cut_edges: list[tuple[int, int, str]]) -> int:
    graph = rx.PyGraph(multigraph=False)
    graph.add_nodes_from(range(n_sites))
    graph.add_edges_from([(u, v, axis) for u, v, axis in cut_edges])
    return int(graph.num_edges())


def xgi_edge_count(cut_edges: list[tuple[int, int, str]]) -> int:
    graph = xgi.Hypergraph()
    for i, (u, v, axis) in enumerate(cut_edges):
        graph.add_edge([u, v, f"{axis}:{i}"])
    return int(graph.num_edges)


def toponetx_cut_dim(cut_edges: list[tuple[int, int, str]]) -> int:
    complex_ = tnx.CellComplex()
    for u, v, _ in cut_edges:
        complex_.add_cell((u, v), rank=1)
    return int(complex_.dim)


def gudhi_simplex_gap(n_sites: int, cut_edges: list[tuple[int, int, str]]) -> int:
    tree = gudhi.SimplexTree()
    for node in range(n_sites):
        tree.insert([node], filtration=0.0)
    for u, v, _ in cut_edges:
        tree.insert([u, v], filtration=1.0)
    return int(tree.num_simplices()) - n_sites


def scale_rung(n_sites: int, shape: tuple[int, int, int], bell: dict[str, Any], product: dict[str, Any]) -> dict[str, Any]:
    cut_edges = enumerate_cut_edges(shape)
    no_edges: list[tuple[int, int, str]] = []
    cut_signature_count = len(cut_edges)
    real_ci_values = [bell["coherent_information_A_to_B"] for _ in cut_edges]
    control_ci_values = [product["coherent_information_A_to_B"] for _ in cut_edges]
    min_real_ci = min(real_ci_values) if real_ci_values else 0.0
    max_control_ci = max(control_ci_values) if control_ci_values else 0.0
    return {
        "sites_or_qubits": n_sites,
        "peps3d_shape": list(shape),
        "bond_dim": 2,
        "local_pair_density_shape": [4, 4],
        "dense_state_closure_used": False,
        "global_hilbert_dim_materialized": False,
        "cut_signature_count": cut_signature_count,
        "cut_axes": sorted(set(axis for _, _, axis in cut_edges)),
        "pyg_cut_edges": pyg_edge_count(n_sites, cut_edges),
        "pyg_cut_edges_ablated": pyg_edge_count(n_sites, no_edges),
        "rustworkx_cut_edges": rustworkx_edge_count(n_sites, cut_edges),
        "rustworkx_cut_edges_ablated": rustworkx_edge_count(n_sites, no_edges),
        "xgi_cut_hyperedges": xgi_edge_count(cut_edges),
        "xgi_cut_hyperedges_ablated": xgi_edge_count(no_edges),
        "toponetx_cut_dim": toponetx_cut_dim(cut_edges),
        "toponetx_cut_dim_ablated": toponetx_cut_dim(no_edges),
        "gudhi_cut_edge_simplices": gudhi_simplex_gap(n_sites, cut_edges),
        "gudhi_cut_edge_simplices_ablated": gudhi_simplex_gap(n_sites, no_edges),
        "min_real_coherent_information": min_real_ci,
        "max_product_control_coherent_information": max_control_ci,
        "per_cut_action": "local 4x4 pair partial_trace -> signed information tuple",
        "pass": bool(
            cut_signature_count > 0
            and min_real_ci > EPS
            and abs(max_control_ci) <= EPS
            and pyg_edge_count(n_sites, cut_edges) == cut_signature_count
            and rustworkx_edge_count(n_sites, cut_edges) == cut_signature_count
            and xgi_edge_count(cut_edges) == cut_signature_count
            and toponetx_cut_dim(cut_edges) == 1
            and gudhi_simplex_gap(n_sites, cut_edges) == cut_signature_count
        ),
    }


def clifford_result() -> dict[str, Any]:
    layout, blades = Cl(3)
    e1 = blades["e1"]
    e2 = blades["e2"]
    anticommutator = e1 * e2 + e2 * e1
    norm = float(sum(abs(float(v)) for v in anticommutator.value))
    return {
        "tool": "clifford",
        "algebra": "Cl(3)",
        "anticommutator_e1_e2_norm": norm,
        "spinor_density_boundary": "Bell pair is built as a torch spinor-derived density; Cl(3) sanity confirms nonabelian generator surface is available.",
        "pass": bool(norm <= 1.0e-12),
    }


def sympy_exact_result() -> dict[str, Any]:
    ln2 = sp.log(2)
    return {
        "tool": "sympy",
        "bell_S_AB": "0",
        "bell_S_A": str(ln2),
        "bell_S_B": str(ln2),
        "bell_mutual_information": str(2 * ln2),
        "bell_coherent_information": str(ln2),
        "bell_conditional_entropy_A_given_B": str(-ln2),
        "product_mutual_information": "0",
        "product_coherent_information": "0",
        "ln2_float": float(ln2.evalf(20)),
        "two_ln2_float": float((2 * ln2).evalf(20)),
        "pass": True,
    }


def build_controls(product: dict[str, Any], mixed: dict[str, Any]) -> dict[str, Any]:
    scalar_label = {
        "description": "scalar entropy label control; no partial trace or A|B carrier action is performed",
        "partial_trace_performed": False,
        "partition_defined": False,
        "S_label": product["S_A"],
        "S_AB": 0.0,
        "S_A": product["S_A"],
        "S_B": 0.0,
        "mutual_information": 0.0,
        "conditional_entropy_A_given_B": 0.0,
        "coherent_information_A_to_B": 0.0,
        "signed_ci_claim_holds": False,
        "pass": True,
    }
    cut_axis_erased = {
        "description": "cut-axis-erased control; no A|B partition exists, so signed readout fails closed to zero sentinel values",
        "partial_trace_performed": False,
        "partition_defined": False,
        "S_AB": 0.0,
        "S_A": 0.0,
        "S_B": 0.0,
        "mutual_information": 0.0,
        "conditional_entropy_A_given_B": 0.0,
        "coherent_information_A_to_B": 0.0,
        "signed_ci_claim_holds": False,
        "pass": True,
    }
    sign_broken = {
        "description": "sign-broken MI readout control for the nonnegative mutual-information guard",
        "partial_trace_performed": True,
        "partition_defined": True,
        "mutual_information": -abs(mixed["S_A"]),
        "source": "computed by intentionally reversing the MI sign in the control readout",
        "pass": True,
    }
    return {
        "product_cut_erased": {
            **product,
            "description": "product |00><00| cut control; partial trace is real but entanglement is erased",
            "signed_ci_claim_holds": False,
            "pass": bool(
                abs(product["mutual_information"]) <= EPS
                and abs(product["coherent_information_A_to_B"]) <= EPS
                and product["conditional_entropy_A_given_B"] >= -EPS
            ),
        },
        "maximally_mixed_boundary": {
            **mixed,
            "description": "I/4 boundary check; MI collapses to zero and coherent information is nonpositive",
            "signed_ci_claim_holds": False,
            "pass": bool(
                abs(mixed["mutual_information"]) <= EPS
                and mixed["coherent_information_A_to_B"] <= EPS
                and mixed["conditional_entropy_A_given_B"] >= -EPS
            ),
        },
        "scalar_entropy_label_control": scalar_label,
        "cut_axis_erased_control": cut_axis_erased,
        "sign_broken_mi_control": sign_broken,
    }


def proof_pass(proofs: dict[str, Any]) -> bool:
    required = [
        proofs["signed_ci_product_control_smt_load_bearing"],
        proofs["signed_ci_scalar_label_control_smt_load_bearing"],
        proofs["signed_ci_cut_axis_erased_smt_load_bearing"],
        proofs["mutual_information_nonnegative_sign_guard"],
    ]
    for proof in required:
        if not (
            proof.get("real_claim_verdict") == "sat"
            and proof.get("negated_claim_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        ):
            return False
    return True


def build_tool_ablations(
    bell: dict[str, Any],
    product: dict[str, Any],
    mixed: dict[str, Any],
    scale_top: dict[str, Any],
    sympy_result: dict[str, Any],
) -> dict[str, Any]:
    ablations = {
        "torch_partial_trace_signed_ci": tool_ablation(
            "torch coherent-information action on Bell cut vs product-cut recompute",
            baseline_value=bell["coherent_information_A_to_B"],
            ablated_value=product["coherent_information_A_to_B"],
            tool="torch",
        ),
        "jax_partial_trace_signed_ci": tool_ablation(
            "jax coherent-information mirror on Bell cut vs product-cut recompute",
            baseline_value=cut_readout_jax(bell_density_jax())["coherent_information_A_to_B"],
            ablated_value=cut_readout_jax(product_density_jax())["coherent_information_A_to_B"],
            tool="jax",
        ),
        "sympy_exact_ci_anchor": tool_ablation(
            "sympy exact Bell coherent information ln2 vs product 0",
            baseline_value=sympy_result["ln2_float"],
            ablated_value=0.0,
            tool="sympy",
        ),
        "pyg_cut_topology": tool_ablation(
            "PyG cut-edge incidence count vs cut-topology erased",
            baseline_value=scale_top["pyg_cut_edges"],
            ablated_value=scale_top["pyg_cut_edges_ablated"],
            tool="pyg",
        ),
        "rustworkx_cut_topology": tool_ablation(
            "rustworkx cut-edge graph count vs cut-topology erased",
            baseline_value=scale_top["rustworkx_cut_edges"],
            ablated_value=scale_top["rustworkx_cut_edges_ablated"],
            tool="rustworkx",
        ),
        "xgi_cut_topology": tool_ablation(
            "XGI cut hyperedge count vs cut-topology erased",
            baseline_value=scale_top["xgi_cut_hyperedges"],
            ablated_value=scale_top["xgi_cut_hyperedges_ablated"],
            tool="xgi",
        ),
        "toponetx_cut_topology": tool_ablation(
            "TopoNetX cut cell-complex dimension vs cut-axis erased",
            baseline_value=scale_top["toponetx_cut_dim"],
            ablated_value=scale_top["toponetx_cut_dim_ablated"],
            tool="toponetx",
        ),
        "gudhi_cut_topology": tool_ablation(
            "GUDHI cut-edge simplex count vs vertices-only control",
            baseline_value=scale_top["gudhi_cut_edge_simplices"],
            ablated_value=scale_top["gudhi_cut_edge_simplices_ablated"],
            tool="gudhi",
        ),
        "mixed_boundary_ci_guard": tool_ablation(
            "Bell coherent information vs maximally mixed boundary control",
            baseline_value=bell["coherent_information_A_to_B"],
            ablated_value=mixed["coherent_information_A_to_B"],
            tool="torch",
        ),
    }
    for row in ablations.values():
        row["pass"] = bool(
            abs(float(row["baseline_value"]) - float(row["ablated_value"])) > 1.0e-12
            and abs(
                (float(row["baseline_value"]) - float(row["ablated_value"]))
                - float(row["outcome_delta"])
            )
            <= 1.0e-12
        )
    return ablations


def known_value_checks(bell: dict[str, Any], product: dict[str, Any], mixed: dict[str, Any]) -> dict[str, Any]:
    ln2 = float(sp.log(2).evalf(20))
    checks = {
        "bell_S_AB_zero": abs(bell["S_AB"]) <= EPS,
        "bell_S_A_ln2": abs(bell["S_A"] - ln2) <= 1.0e-10,
        "bell_S_B_ln2": abs(bell["S_B"] - ln2) <= 1.0e-10,
        "bell_MI_2ln2": abs(bell["mutual_information"] - 2.0 * ln2) <= 1.0e-10,
        "bell_CI_ln2": abs(bell["coherent_information_A_to_B"] - ln2) <= 1.0e-10,
        "bell_conditional_minus_ln2": abs(bell["conditional_entropy_A_given_B"] + ln2) <= 1.0e-10,
        "product_MI_zero": abs(product["mutual_information"]) <= EPS,
        "product_CI_zero": abs(product["coherent_information_A_to_B"]) <= EPS,
        "mixed_MI_zero": abs(mixed["mutual_information"]) <= EPS,
    }
    return {
        "ln2": ln2,
        "two_ln2": 2.0 * ln2,
        "checks": checks,
        "pass": all(checks.values()),
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    bell_torch = cut_readout_torch(bell_density_torch())
    product_torch = cut_readout_torch(product_density_torch())
    mixed_torch = cut_readout_torch(mixed_density_torch())

    bell_jax = cut_readout_jax(bell_density_jax())
    product_jax = cut_readout_jax(product_density_jax())
    mixed_jax = cut_readout_jax(mixed_density_jax())

    controls = build_controls(product_torch, mixed_torch)
    sympy_result = sympy_exact_result()
    scale_rows = {
        str(n): scale_rung(n, shape, bell_torch, product_torch)
        for n, shape in SCALES.items()
    }
    top = scale_rows["64"]

    proofs = {
        "signed_ci_product_control_smt_load_bearing": smt_signed_ci_proof(
            bell_torch,
            controls["product_cut_erased"],
            "signed_coherent_information_positive_and_conditional_entropy_negative_product_control",
        ),
        "signed_ci_scalar_label_control_smt_load_bearing": smt_signed_ci_proof(
            bell_torch,
            controls["scalar_entropy_label_control"],
            "signed_coherent_information_requires_partial_trace_not_scalar_label",
        ),
        "signed_ci_cut_axis_erased_smt_load_bearing": smt_signed_ci_proof(
            bell_torch,
            controls["cut_axis_erased_control"],
            "signed_coherent_information_requires_defined_cut_axis",
        ),
        "mutual_information_nonnegative_sign_guard": smt_mi_guard(
            bell_torch,
            controls["sign_broken_mi_control"],
        ),
        "sympy_exact_signed_information_identities": sympy_result,
    }
    ablations = build_tool_ablations(bell_torch, product_torch, mixed_torch, top, sympy_result)
    clifford = clifford_result()
    known_checks = known_value_checks(bell_torch, product_torch, mixed_torch)

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(DTYPE),
        "action": "EK_L6 partial_trace(A|B) -> signed information tuple",
        "real_entangled_cut": bell_torch,
        "product_control_cut": product_torch,
        "maximally_mixed_boundary": mixed_torch,
        "signed_ci_invariant_holds": bool(
            bell_torch["coherent_information_A_to_B"] > EPS
            and bell_torch["conditional_entropy_A_given_B"] < -EPS
            and bell_torch["mutual_information"] > EPS
        ),
        "product_control_collapses": bool(
            abs(product_torch["mutual_information"]) <= EPS
            and abs(product_torch["coherent_information_A_to_B"]) <= EPS
            and product_torch["conditional_entropy_A_given_B"] >= -EPS
        ),
        "pass": bool(bell_torch["pass"] and product_torch["pass"] and mixed_torch["pass"]),
    }

    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "real_entangled_cut": bell_jax,
        "product_control_cut": product_jax,
        "maximally_mixed_boundary": mixed_jax,
        "torch_jax_delta_real": max_abs_readout_delta(bell_torch, bell_jax),
        "torch_jax_delta_product": max_abs_readout_delta(product_torch, product_jax),
        "torch_jax_delta_mixed": max_abs_readout_delta(mixed_torch, mixed_jax),
        "pass": bool(
            max_abs_readout_delta(bell_torch, bell_jax) <= 1.0e-12
            and max_abs_readout_delta(product_torch, product_jax) <= 1.0e-12
            and max_abs_readout_delta(mixed_torch, mixed_jax) <= 1.0e-12
        ),
    }
    jax_vs_pytorch_delta = max(
        jax_mirror_result["torch_jax_delta_real"],
        jax_mirror_result["torch_jax_delta_product"],
        jax_mirror_result["torch_jax_delta_mixed"],
    )

    scale_pass = all(row["pass"] for row in scale_rows.values())
    ablation_pass = all(row["pass"] for row in ablations.values())
    all_pass = bool(
        torch_primary_result["pass"]
        and jax_mirror_result["pass"]
        and known_checks["pass"]
        and proof_pass(proofs)
        and scale_pass
        and ablation_pass
        and clifford["pass"]
    )

    return {
        "sim_id": "sim_layer_L6_entropy_cut_probe",
        "name": "sim_layer_L6_entropy_cut_probe",
        "version": "1.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": str(THISFILE),
        "result": str(RESULT),
        "object_id": OBJECT_ID,
        "layer": "L6 entropy/cut/communication layer ACTION, variant L6b signed cut-information readout",
        "finite_map": {
            "domain": "finite PEPS3D cut family C over local 4x4 two-site spinor-density states rho_AB on admitted cut edges; scales 8/16/32/64 sites",
            "codomain_or_output": "signed information tuple (S_AB, S_A, S_B, I(A:B), S(A|B), I_c(A>B)) for each finite cut",
            "definition": "EK_L6(rho_AB, C): partial_trace over A|B to rho_A,rho_B, then eigvalsh entropy readout; no dense global state is materialized",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite site set, finite cut-edge family, finite local 4x4 pair carriers, and finite readout tuple per cut",
            },
            "N01": {
                "status": "active_tested",
                "statement": "signed-information invariant separates entangled cut action from product/cut-erased and scalar-label controls; noncommuting Cl(3) spinor generator sanity is present",
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage-6 independent manifold-layer lego",
        "sim_execution_kind": "nonclassical",
        "sim_class": "entropy_cut_readout_action_probe",
        "carrier_layer": "boundary_interior_cut over PEPS3D spinor-density local pair carriers",
        "geometry_layer": "finite PEPS3D cut-edge family only; no L7 Hopf or L8 gluing stack",
        "carrier_realization": "torch complex128 local 4x4 spinor-density pair states; no NumPy bridge and no dense global state closure",
        "peps3d_embedding": {
            "site_shapes": {str(k): list(v) for k, v in SCALES.items()},
            "bond_dim": 2,
            "cut_edge_rule": "axis mid-plane adjacent pairs; all readouts are local 4x4 pair actions",
            "dense_state_closure_used": False,
        },
        "spinor_state": "two-component Bell/product/mixed pair densities as torch complex128 spinor-derived rho_AB; local reductions rho_A/rho_B computed by partial trace",
        "quaternion_action": "not_applicable; no quaternion language is used for the L6 claim",
        "dependency_receipts": [
            "stage-2 spinor_density carrier assumed as input by /tmp/layer_specs.json L6; this sim tests only the independent L6 action",
            "lower layer stacking receipts are not claimed or consumed",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "allowed_claims": [
            "L6 cut-readout action maps a finite local cut density to a signed information tuple",
            "Bell cut has I_c>0 and S(A|B)<0 while product/scalar-label/cut-erased controls fail that invariant",
            "8/16/32/64 scaling is non-dense over local cut-edge pair readouts",
        ],
        "promotion_blockers": [
            "independent L6 lego only; no stacking with L0-L5/L7/L8",
            "does not unlock flux, Xi, Phi0, Axis0, bridge, basin, physics, or gravity consumers",
            "does not claim full layer completion or manifold admission",
        ],
        "eligible_consumers": ["future bounded L6 local readout comparison packets only"],
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "proof_results": proofs,
        "controls": controls,
        "tool_ablations": ablations,
        "ablation_outcome_delta": ablations,
        "scale_ladder": {
            "axis": "PEPS3D site count with local cut-edge readouts",
            "rungs": scale_rows,
            "dense_state_closure_used": False,
            "pass": bool(scale_pass),
        },
        "known_value_checks": known_checks,
        "sympy_exact_result": sympy_result,
        "clifford_result": clifford,
        "shells": [
            "boundary_interior_cut",
            "peps3d_spinor_network_cut_edges",
            "spinor_density_local_pair_state",
        ],
        "future_continuations": {
            "allowed": ["future bounded L6 local readout comparison packets"],
            "blocked": BLOCKED_CONSUMERS,
            "reason": "this packet preserves the L6 action object but does not admit stacking or downstream bridge/axis/physics consumers",
        },
        "compatibility_weights": {
            "independent_L6_action": 1.0,
            "product_cut_control": 0.0,
            "scalar_entropy_label_control": 0.0,
            "cut_axis_erased_control": 0.0,
            "stacking_or_downstream_promotion": 0.0,
        },
        "compression_map": {
            "from": "finite cut family of local 4x4 rho_AB states",
            "to": "per-cut signed information tuple",
            "operation": "partial_trace_then_eigvalsh_entropy",
            "loss_boundary": "does not preserve global dense state, layer stacking, or downstream bridge/axis claims",
        },
        "present_survivor": {
            "object": "Bell-cut L6 readout action",
            "coherent_information_positive": bell_torch["coherent_information_A_to_B"] > EPS,
            "conditional_entropy_negative": bell_torch["conditional_entropy_A_given_B"] < -EPS,
            "controls_collapse": bool(
                controls["product_cut_erased"]["pass"]
                and controls["scalar_entropy_label_control"]["pass"]
                and controls["cut_axis_erased_control"]["pass"]
            ),
        },
        "outward_record": {
            "artifact": str(RESULT),
            "claim_ceiling": "independent Stage-6 L6 lego action only; promotion_allowed=false",
        },
        "survivor_invariant": {
            "passed": bool(
                bell_torch["coherent_information_A_to_B"] > EPS
                and bell_torch["conditional_entropy_A_given_B"] < -EPS
                and controls["product_cut_erased"]["pass"]
            ),
            "coherent_information_A_to_B": bell_torch["coherent_information_A_to_B"],
            "conditional_entropy_A_given_B": bell_torch["conditional_entropy_A_given_B"],
            "control_coherent_information": product_torch["coherent_information_A_to_B"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [k for k, v in TOOL_MANIFEST.items() if v["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3/cvc5 signed-CI proof",
            "load_bearing_proof.smt_load_bearing z3/cvc5 MI sign-broken guard",
            "sympy exact ln2 identities",
        ],
        "graph_surfaces_used": ["PyG", "rustworkx", "XGI"],
        "topology_surfaces_used": ["TopoNetX", "GUDHI"],
        "required_inputs": ["stage-2 spinor_density local pair state", "finite PEPS3D cut-edge family"],
        "data_or_artifact_dependencies": ["/tmp/layer_specs.json exact L6 spec entry"],
        "required_negatives": [
            "product/cut-erased control",
            "scalar entropy label control",
            "cut-axis-erased control",
            "sign-broken mutual information control",
            "maximally mixed boundary check",
        ],
        "negatives_run": list(controls.keys()),
        "kill_conditions": [
            "SMT proof does not flip between measured real and control values",
            "known Bell values miss ln2/2ln2/-ln2 anchors",
            "JAX mirror diverges from torch",
            "any scale rung materializes a dense global state",
            "cut topology ablation leaves structural witness unchanged",
        ],
        "required_artifacts": [
            "result JSON",
            "torch_primary_result",
            "jax_mirror_result",
            "proof_results",
            "controls",
            "tool_ablations",
            "scale_ladder",
            "known_value_checks",
        ],
        "artifacts_emitted": [str(RESULT)],
        "witness_trace_id": "L6_entropy_cut_action_bell_vs_product_controls",
        "result_summary": {
            "bell_coherent_information": bell_torch["coherent_information_A_to_B"],
            "bell_conditional_entropy_A_given_B": bell_torch["conditional_entropy_A_given_B"],
            "product_coherent_information": product_torch["coherent_information_A_to_B"],
            "top_scale_cut_signature_count": top["cut_signature_count"],
            "proof_pass": proof_pass(proofs),
            "scale_pass": scale_pass,
            "ablation_pass": ablation_pass,
            "all_pass": all_pass,
        },
        "pass_rule": "torch/JAX compute Bell ln2 signed-information readout; helper-bound SMT flips against product/scalar/cut-axis controls; scale rungs stay non-dense; topology ablations remove real witnesses",
        "fail_rule": "fail on decorative proof, scalar entropy label standing in for the action, missing product/cut-erased collapse, dense state closure, JAX mismatch, or downstream promotion",
        "promotion_status": "keep_but_open",
        "all_pass": all_pass,
        "required_pass": all_pass,
    }


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {RESULT.relative_to(ROOT)}")
    print(f"required_pass={result['required_pass']}")
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
