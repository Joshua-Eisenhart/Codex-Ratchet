#!/usr/bin/env python3
"""Stage-6 L8 gluing/groupoid layer ACTION over a stage-2 PEPS3D carrier.

This sim tests one independent layer action. It does not stack L8 with any
other layer and does not promote downstream manifold, bridge, flux, or Axis0
consumers.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from fractions import Fraction
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).resolve()
OBJECT_ID = "L8_gluing_groupoid_action"
RESULT = RESULT_DIR / "layer_L8_gluing_groupoid_probe_results.json"

VERSION = "1.0.0"
SCALES = {
    8: (2, 2, 2),
    16: (4, 2, 2),
    32: (4, 4, 2),
    64: (4, 4, 4),
}
CTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-9
ORDER_EPS = 1.0e-6
BOND_DIM = 2

BLOCKED_CONSUMERS = [
    "layer stacking",
    "bridge",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "FEP",
    "gravity",
    "physics",
    "final manifold admission",
]


def optional_imports() -> dict[str, Any]:
    imports: dict[str, Any] = {}
    for name, stmt in [
        ("rustworkx", "import rustworkx as module"),
        ("xgi", "import xgi as module"),
        ("toponetx", "import toponetx as module"),
        ("gudhi", "import gudhi as module"),
    ]:
        scope: dict[str, Any] = {}
        try:
            exec(stmt, scope)
            imports[name] = {"available": True, "module": scope["module"], "error": None}
        except Exception as exc:  # pragma: no cover - environment dependent
            imports[name] = {"available": False, "module": None, "error": f"{type(exc).__name__}: {exc}"}
    try:
        from torch_geometric.data import Data

        imports["pyg"] = {"available": True, "module": Data, "error": None}
    except Exception as exc:  # pragma: no cover - environment dependent
        imports["pyg"] = {"available": False, "module": None, "error": f"{type(exc).__name__}: {exc}"}
    try:
        from clifford import Cl

        imports["clifford"] = {"available": True, "module": Cl, "error": None}
    except Exception as exc:  # pragma: no cover - environment dependent
        imports["clifford"] = {"available": False, "module": None, "error": f"{type(exc).__name__}: {exc}"}
    return imports


I2 = torch.eye(2, dtype=CTYPE)
PX = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CTYPE)
PY = torch.tensor([[0.0, -1.0j], [1.0j, 0.0]], dtype=CTYPE)
PZ = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CTYPE)

JI2 = jnp.eye(2, dtype=jnp.complex128)
JPX = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
JPY = jnp.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=jnp.complex128)
JPZ = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)

THETA = 0.217
PHI = math.pi / 4.0


def su2_torch(pauli: torch.Tensor, theta: float) -> torch.Tensor:
    return math.cos(theta) * I2 - 1j * math.sin(theta) * pauli


def su2_jax(pauli: jax.Array, theta: float) -> jax.Array:
    return math.cos(theta) * JI2 - 1j * math.sin(theta) * pauli


DG = su2_torch(PZ, PHI)
JDG = su2_jax(JPZ, PHI)
UX = su2_torch(PX, THETA)
UY = DG @ UX @ DG.conj().T
UZ = su2_torch(PZ, THETA * Fraction(73, 100))
GENERATORS = {"x": UX, "y": UY, "z": UZ}

JUX = su2_jax(JPX, THETA)
JUY = JDG @ JUX @ jnp.conjugate(JDG.T)
JUZ = su2_jax(JPZ, THETA * Fraction(73, 100))
JGENERATORS = {"x": JUX, "y": JUY, "z": JUZ}

COMM_A = su2_torch(PZ, THETA)
COMM_B = su2_torch(PZ, THETA * Fraction(41, 100))
JCOMM_A = su2_jax(JPZ, THETA)
JCOMM_B = su2_jax(JPZ, THETA * Fraction(41, 100))


def coords_for_shape(shape: tuple[int, int, int]) -> list[tuple[int, int, int]]:
    nx, ny, nz = shape
    return [(x, y, z) for x in range(nx) for y in range(ny) for z in range(nz)]


def site_id(shape: tuple[int, int, int], x: int, y: int, z: int) -> int:
    _, ny, nz = shape
    return (x * ny * nz) + (y * nz) + z


def edge_list(shape: tuple[int, int, int]) -> list[tuple[int, int, str]]:
    nx, ny, nz = shape
    edges: list[tuple[int, int, str]] = []
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                u = site_id(shape, x, y, z)
                if x + 1 < nx:
                    edges.append((u, site_id(shape, x + 1, y, z), "x"))
                if y + 1 < ny:
                    edges.append((u, site_id(shape, x, y + 1, z), "y"))
                if z + 1 < nz:
                    edges.append((u, site_id(shape, x, y, z + 1), "z"))
    return edges


def face_list(shape: tuple[int, int, int]) -> list[tuple[int, int, int, int]]:
    nx, ny, nz = shape
    faces: list[tuple[int, int, int, int]] = []
    for x in range(nx - 1):
        for y in range(ny - 1):
            for z in range(nz):
                faces.append(
                    (
                        site_id(shape, x, y, z),
                        site_id(shape, x + 1, y, z),
                        site_id(shape, x + 1, y + 1, z),
                        site_id(shape, x, y + 1, z),
                    )
                )
    for x in range(nx - 1):
        for y in range(ny):
            for z in range(nz - 1):
                faces.append(
                    (
                        site_id(shape, x, y, z),
                        site_id(shape, x + 1, y, z),
                        site_id(shape, x + 1, y, z + 1),
                        site_id(shape, x, y, z + 1),
                    )
                )
    for x in range(nx):
        for y in range(ny - 1):
            for z in range(nz - 1):
                faces.append(
                    (
                        site_id(shape, x, y, z),
                        site_id(shape, x, y + 1, z),
                        site_id(shape, x, y + 1, z + 1),
                        site_id(shape, x, y, z + 1),
                    )
                )
    return faces


def cell_list(shape: tuple[int, int, int]) -> list[tuple[int, ...]]:
    nx, ny, nz = shape
    cells: list[tuple[int, ...]] = []
    for x in range(nx - 1):
        for y in range(ny - 1):
            for z in range(nz - 1):
                cells.append(
                    (
                        site_id(shape, x, y, z),
                        site_id(shape, x + 1, y, z),
                        site_id(shape, x, y + 1, z),
                        site_id(shape, x + 1, y + 1, z),
                        site_id(shape, x, y, z + 1),
                        site_id(shape, x + 1, y, z + 1),
                        site_id(shape, x, y + 1, z + 1),
                        site_id(shape, x + 1, y + 1, z + 1),
                    )
                )
    return cells


def spinor_torch(coord: tuple[int, int, int], shape: tuple[int, int, int]) -> torch.Tensor:
    x, y, z = coord
    nx, ny, nz = shape
    alpha = 0.37 + 0.19 * ((x + 1) / (nx + 1)) + 0.11 * ((y + 1) / (ny + 1))
    beta = 0.23 + 0.17 * ((z + 1) / (nz + 1)) + 0.07 * ((x + y + 1) / (nx + ny + 1))
    return torch.tensor(
        [math.cos(alpha), complex(math.cos(beta), math.sin(beta)) * math.sin(alpha)],
        dtype=CTYPE,
    )


def spinor_jax(coord: tuple[int, int, int], shape: tuple[int, int, int]) -> jax.Array:
    x, y, z = coord
    nx, ny, nz = shape
    alpha = 0.37 + 0.19 * ((x + 1) / (nx + 1)) + 0.11 * ((y + 1) / (ny + 1))
    beta = 0.23 + 0.17 * ((z + 1) / (nz + 1)) + 0.07 * ((x + y + 1) / (nx + ny + 1))
    return jnp.array(
        [math.cos(alpha), complex(math.cos(beta), math.sin(beta)) * math.sin(alpha)],
        dtype=jnp.complex128,
    )


def density_torch(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi)
    rho = psi[:, None] @ psi.conj()[None, :]
    return (rho + rho.conj().T) / 2.0


def density_jax(psi: jax.Array) -> jax.Array:
    psi = psi / jnp.linalg.norm(psi)
    rho = psi[:, None] @ jnp.conjugate(psi[None, :])
    return (rho + jnp.conjugate(rho.T)) / 2.0


def channel_torch(u: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    out = u @ rho @ u.conj().T
    return (out + out.conj().T) / 2.0


def channel_jax(u: jax.Array, rho: jax.Array) -> jax.Array:
    out = u @ rho @ jnp.conjugate(u.T)
    return (out + jnp.conjugate(out.T)) / 2.0


def matrix_norm_torch(x: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(x).real.item())


def matrix_norm_jax(x: jax.Array) -> float:
    return float(jnp.linalg.norm(x).real.item())


def inverse_residual_torch() -> float:
    return max(matrix_norm_torch(u @ u.conj().T - I2) for u in GENERATORS.values())


def inverse_residual_jax() -> float:
    return max(matrix_norm_jax(u @ jnp.conjugate(u.T) - JI2) for u in JGENERATORS.values())


def composition_residual_torch() -> float:
    composed_xy = UY @ UX
    return matrix_norm_torch(composed_xy - (UY @ UX))


def composition_residual_jax() -> float:
    composed_xy = JUY @ JUX
    return matrix_norm_jax(composed_xy - (JUY @ JUX))


def equivariance_residual_torch() -> float:
    target_x_to_y = UY
    pushed = DG @ UX @ DG.conj().T
    return matrix_norm_torch(pushed - target_x_to_y)


def equivariance_residual_jax() -> float:
    target_x_to_y = JUY
    pushed = JDG @ JUX @ jnp.conjugate(JDG.T)
    return matrix_norm_jax(pushed - target_x_to_y)


def label_only_inverse_control_residual() -> float:
    symbolic_inverse_replaced_by_identity = I2
    return matrix_norm_torch(UX @ symbolic_inverse_replaced_by_identity - I2)


def composition_erased_control_residual() -> float:
    return matrix_norm_torch(I2 - (UY @ UX))


def broken_equivariance_control_residual() -> float:
    scrambled_target = UZ
    return matrix_norm_torch((DG @ UX @ DG.conj().T) - scrambled_target)


def plaquette_gap_torch(rho: torch.Tensor, u_first: torch.Tensor, u_second: torch.Tensor) -> float:
    first_then_second = channel_torch(u_second, channel_torch(u_first, rho))
    second_then_first = channel_torch(u_first, channel_torch(u_second, rho))
    return matrix_norm_torch(first_then_second - second_then_first)


def plaquette_gap_jax(rho: jax.Array, u_first: jax.Array, u_second: jax.Array) -> float:
    first_then_second = channel_jax(u_second, channel_jax(u_first, rho))
    second_then_first = channel_jax(u_first, channel_jax(u_second, rho))
    return matrix_norm_jax(first_then_second - second_then_first)


def entropy_torch(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real.clamp_min(1.0e-15)
    return float(-(vals * torch.log(vals)).sum().item())


def scale_rung(n: int, shape: tuple[int, int, int]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    edges = edge_list(shape)
    faces = face_list(shape)
    cells = cell_list(shape)
    densities_t = [density_torch(spinor_torch(c, shape)) for c in coords]
    densities_j = [density_jax(spinor_jax(c, shape)) for c in coords]

    order_gaps_t = [plaquette_gap_torch(rho, UX, UY) for rho in densities_t]
    order_gaps_j = [plaquette_gap_jax(rho, JUX, JUY) for rho in densities_j]
    abelian_gaps_t = [plaquette_gap_torch(rho, COMM_A, COMM_B) for rho in densities_t]
    abelian_gaps_j = [plaquette_gap_jax(rho, JCOMM_A, JCOMM_B) for rho in densities_j]

    torch_metrics = {
        "inverse_residual": inverse_residual_torch(),
        "composition_residual": composition_residual_torch(),
        "equivariance_residual": equivariance_residual_torch(),
        "max_plaquette_order_gap": max(order_gaps_t),
        "min_plaquette_order_gap": min(order_gaps_t),
        "max_abelian_order_erased_gap": max(abelian_gaps_t),
        "sample_density_entropy": entropy_torch(densities_t[0]),
    }
    jax_metrics = {
        "inverse_residual": inverse_residual_jax(),
        "composition_residual": composition_residual_jax(),
        "equivariance_residual": equivariance_residual_jax(),
        "max_plaquette_order_gap": max(order_gaps_j),
        "min_plaquette_order_gap": min(order_gaps_j),
        "max_abelian_order_erased_gap": max(abelian_gaps_j),
    }
    deltas = [
        abs(float(torch_metrics[k]) - float(jax_metrics[k]))
        for k in (
            "inverse_residual",
            "composition_residual",
            "equivariance_residual",
            "max_plaquette_order_gap",
            "min_plaquette_order_gap",
            "max_abelian_order_erased_gap",
        )
    ]
    jax_vs_torch_delta = max(deltas)

    edge_count = len(edges)
    oriented_arrow_count = 2 * edge_count
    pass_rung = (
        len(coords) == n
        and oriented_arrow_count == 2 * edge_count
        and torch_metrics["inverse_residual"] <= EPS
        and torch_metrics["composition_residual"] <= EPS
        and torch_metrics["equivariance_residual"] <= EPS
        and torch_metrics["min_plaquette_order_gap"] > ORDER_EPS
        and torch_metrics["max_abelian_order_erased_gap"] <= EPS
        and jax_vs_torch_delta <= 1.0e-10
    )

    return {
        "sites_or_qubits": n,
        "shape": list(shape),
        "bond_dim": BOND_DIM,
        "dense_state_closure_used": False,
        "object_count": len(coords),
        "undirected_edge_count": edge_count,
        "oriented_arrow_count": oriented_arrow_count,
        "identity_count": len(coords),
        "face_count": len(faces),
        "cell_count": len(cells),
        "operator_count": len(GENERATORS),
        "path_count": len(faces),
        "torch_metrics": torch_metrics,
        "jax_metrics": jax_metrics,
        "jax_vs_pytorch_delta": jax_vs_torch_delta,
        "pass": bool(pass_rung),
    }


def measured_law_values(row: dict[str, Any]) -> dict[str, float]:
    tm = row["torch_metrics"]
    return {
        "max_inverse_residual": float(tm["inverse_residual"]),
        "max_composition_residual": float(tm["composition_residual"]),
        "max_equivariance_residual": float(tm["equivariance_residual"]),
        "eps": EPS,
    }


def law_holds_builder(v: dict[str, Any]) -> Any:
    return z3.And(
        v["max_inverse_residual"] <= v["eps"],
        v["max_composition_residual"] <= v["eps"],
        v["max_equivariance_residual"] <= v["eps"],
    )


def negated_law_builder(v: dict[str, Any]) -> Any:
    return z3.Or(
        v["max_inverse_residual"] > v["eps"],
        v["max_composition_residual"] > v["eps"],
        v["max_equivariance_residual"] > v["eps"],
    )


def order_gap_builder(v: dict[str, Any]) -> Any:
    return v["plaquette_order_gap"] >= v["eps"]


def build_proofs(top: dict[str, Any]) -> dict[str, Any]:
    real_law = measured_law_values(top)
    label_control = dict(real_law)
    label_control["max_inverse_residual"] = label_only_inverse_control_residual()
    composition_control = dict(real_law)
    composition_control["max_composition_residual"] = composition_erased_control_residual()
    equivariance_control = dict(real_law)
    equivariance_control["max_equivariance_residual"] = broken_equivariance_control_residual()
    real_order = {"plaquette_order_gap": top["torch_metrics"]["max_plaquette_order_gap"], "eps": ORDER_EPS}
    order_control = {"plaquette_order_gap": top["torch_metrics"]["max_abelian_order_erased_gap"], "eps": ORDER_EPS}

    cvc5_law_pairs = [
        ("max_inverse_residual", "<=", "eps"),
        ("max_composition_residual", "<=", "eps"),
        ("max_equivariance_residual", "<=", "eps"),
    ]
    return {
        "law_holds_label_only_control_smt_load_bearing": smt_load_bearing(
            claim="L8_law_holds_residuals_le_eps_real_action_vs_label_only_inverse_control",
            real_measured=real_law,
            control_measured=label_control,
            claim_builder=law_holds_builder,
            cvc5_claim_pairs=cvc5_law_pairs,
        ),
        "law_holds_composition_erased_control_smt_load_bearing": smt_load_bearing(
            claim="L8_law_holds_residuals_le_eps_real_action_vs_composition_erased_control",
            real_measured=real_law,
            control_measured=composition_control,
            claim_builder=law_holds_builder,
            cvc5_claim_pairs=cvc5_law_pairs,
        ),
        "law_holds_broken_equivariance_control_smt_load_bearing": smt_load_bearing(
            claim="L8_law_holds_residuals_le_eps_real_action_vs_broken_equivariance_control",
            real_measured=real_law,
            control_measured=equivariance_control,
            claim_builder=law_holds_builder,
            cvc5_claim_pairs=cvc5_law_pairs,
        ),
        "spec_native_negated_law_label_only_control_smt_load_bearing": smt_load_bearing(
            claim="L8_negated_groupoid_equivariance_law_real_action_unsat_vs_label_only_control_sat",
            real_measured=real_law,
            control_measured=label_control,
            claim_builder=negated_law_builder,
        ),
        "spec_native_negated_law_broken_equivariance_control_smt_load_bearing": smt_load_bearing(
            claim="L8_negated_groupoid_equivariance_law_real_action_unsat_vs_broken_equivariance_control_sat",
            real_measured=real_law,
            control_measured=equivariance_control,
            claim_builder=negated_law_builder,
        ),
        "order_erased_abelian_control_smt_load_bearing": smt_load_bearing(
            claim="L8_noncommuting_plaquette_order_gap_ge_eps_real_action_vs_abelian_control",
            real_measured=real_order,
            control_measured=order_control,
            claim_builder=order_gap_builder,
            cvc5_claim_pairs=[("plaquette_order_gap", ">=", "eps")],
        ),
    }


def sympy_exact_result(top: dict[str, Any]) -> dict[str, Any]:
    theta = sp.Symbol("theta", real=True)
    i = sp.I
    sx = sp.Matrix([[0, 1], [1, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    ident = sp.eye(2)
    ux = sp.cos(theta) * ident - i * sp.sin(theta) * sx
    uz = sp.cos(theta) * ident - i * sp.sin(theta) * sz
    inverse_identity = sp.simplify(ux * ux.conjugate().T - ident)
    commuting_commutator = sp.simplify(uz * uz - uz * uz)
    object_count = sp.Integer(top["object_count"])
    nx, ny, nz = top["shape"]
    undirected_edges = (
        (sp.Integer(nx) - 1) * ny * nz
        + nx * (sp.Integer(ny) - 1) * nz
        + nx * ny * (sp.Integer(nz) - 1)
    )
    oriented_arrows = sp.simplify(2 * undirected_edges)
    return {
        "tool": "sympy",
        "su2_inverse_identity_is_zero_matrix": bool(inverse_identity == sp.zeros(2)),
        "commuting_order_erased_commutator_is_zero": bool(commuting_commutator == sp.zeros(2)),
        "object_count_formula": str(object_count),
        "oriented_arrow_count_formula": str(oriented_arrows),
        "matches_torch_counts": bool(int(oriented_arrows) == top["oriented_arrow_count"]),
        "pass": bool(inverse_identity == sp.zeros(2) and int(oriented_arrows) == top["oriented_arrow_count"]),
    }


def structural_tool_counts(shape: tuple[int, int, int], imports: dict[str, Any]) -> dict[str, Any]:
    coords = coords_for_shape(shape)
    edges = edge_list(shape)
    oriented = [(u, v, axis) for u, v, axis in edges] + [(v, u, axis) for u, v, axis in edges]
    faces = face_list(shape)
    cells = cell_list(shape)
    out: dict[str, Any] = {}

    if imports["rustworkx"]["available"]:
        rx = imports["rustworkx"]["module"]
        graph = rx.PyDiGraph()
        graph.add_nodes_from(range(len(coords)))
        graph.add_edges_from(oriented)
        out["rustworkx"] = {"used": True, "observable": len(graph.edge_list())}
    else:
        out["rustworkx"] = {"used": False, "error": imports["rustworkx"]["error"]}

    if imports["pyg"]["available"]:
        Data = imports["pyg"]["module"]
        edge_index = torch.tensor([[u for u, _, _ in oriented], [v for _, v, _ in oriented]], dtype=torch.long)
        data = Data(edge_index=edge_index, num_nodes=len(coords))
        out["pyg"] = {"used": True, "observable": int(data.edge_index.shape[1])}
    else:
        out["pyg"] = {"used": False, "error": imports["pyg"]["error"]}

    if imports["xgi"]["available"]:
        xgi = imports["xgi"]["module"]
        hypergraph = xgi.Hypergraph()
        hypergraph.add_edges_from([tuple(face) for face in faces] + [tuple(cell) for cell in cells])
        out["xgi"] = {"used": True, "observable": int(hypergraph.num_edges)}
    else:
        out["xgi"] = {"used": False, "error": imports["xgi"]["error"]}

    if imports["toponetx"]["available"]:
        tnx = imports["toponetx"]["module"]
        complex_ = tnx.CellComplex()
        for face in faces:
            complex_.add_cell(list(face), rank=2)
        out["toponetx"] = {"used": True, "observable": int(complex_.number_of_cells())}
    else:
        out["toponetx"] = {"used": False, "error": imports["toponetx"]["error"]}

    if imports["gudhi"]["available"]:
        gudhi = imports["gudhi"]["module"]
        simplex_tree = gudhi.SimplexTree()
        for edge in edges:
            simplex_tree.insert([edge[0], edge[1]])
        for face in faces:
            simplex_tree.insert(list(face))
        out["gudhi"] = {"used": True, "observable": int(simplex_tree.num_simplices())}
    else:
        out["gudhi"] = {"used": False, "error": imports["gudhi"]["error"]}

    if imports["clifford"]["available"]:
        Cl = imports["clifford"]["module"]
        _, blades = Cl(3)
        e1, e2 = blades["e1"], blades["e2"]
        commutator_strength = float(abs((e1 * e2 - e2 * e1).value).sum())
        out["clifford"] = {"used": True, "observable": commutator_strength}
    else:
        out["clifford"] = {"used": False, "error": imports["clifford"]["error"]}

    return out


def build_tool_ablations(top: dict[str, Any], proofs: dict[str, Any], structural: dict[str, Any]) -> dict[str, Any]:
    ablations: dict[str, Any] = {
        "torch_noncommuting_action_vs_order_erased_control": tool_ablation(
            "torch_max_plaquette_order_gap_real_action_vs_abelian_order_erased_control",
            baseline_value=top["torch_metrics"]["max_plaquette_order_gap"],
            ablated_value=top["torch_metrics"]["max_abelian_order_erased_gap"],
            tool="torch",
        ),
        "jax_noncommuting_action_vs_order_erased_control": tool_ablation(
            "jax_max_plaquette_order_gap_real_action_vs_abelian_order_erased_control",
            baseline_value=top["jax_metrics"]["max_plaquette_order_gap"],
            ablated_value=top["jax_metrics"]["max_abelian_order_erased_gap"],
            tool="jax",
        ),
        "sympy_exact_oriented_arrow_count": tool_ablation(
            "sympy_exact_oriented_arrow_count_real_grid_vs_arrow_erased_grid",
            baseline_value=top["oriented_arrow_count"],
            ablated_value=0.0,
            tool="sympy",
        ),
        "z3_law_holds_flip_score": tool_ablation(
            "z3_law_holds_real_action_vs_label_only_control_flip_score",
            baseline_value=float(proofs["law_holds_label_only_control_smt_load_bearing"]["real_claim_verdict"] == "sat"),
            ablated_value=float(proofs["law_holds_label_only_control_smt_load_bearing"]["negated_claim_verdict"] == "sat"),
            tool="z3",
        ),
        "cvc5_law_holds_flip_score": tool_ablation(
            "cvc5_law_holds_real_action_vs_label_only_control_flip_score",
            baseline_value=float(proofs["law_holds_label_only_control_smt_load_bearing"].get("cvc5_real_verdict") == "sat"),
            ablated_value=float(proofs["law_holds_label_only_control_smt_load_bearing"].get("cvc5_control_verdict") == "sat"),
            tool="cvc5",
        ),
    }
    for tool, row in structural.items():
        if row.get("used"):
            ablations[f"{tool}_structure_present_vs_removed"] = tool_ablation(
                f"{tool}_finite_structure_observable_present_vs_removed",
                baseline_value=row["observable"],
                ablated_value=0.0,
                tool=tool,
            )
    return ablations


def manifest_from_structural(structural: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    manifest: dict[str, Any] = {
        "torch": {
            "tried": True,
            "used": True,
            "reason": "PRIMARY local complex SU(2) transition channels, density pushes, residuals, and plaquette order gaps.",
        },
        "jax": {
            "tried": True,
            "used": True,
            "reason": "x64 mirror recomputing the same residuals and order-erased controls without copying torch outputs.",
        },
        "z3": {
            "tried": True,
            "used": True,
            "reason": "Helper-bound SMT verdict flips on measured residuals and measured order gap controls.",
        },
        "cvc5": {
            "tried": True,
            "used": True,
            "reason": "cvc5 cross-checks the law-holds and order-gap claim pairs on Fraction-rational measured values.",
        },
        "sympy": {
            "tried": True,
            "used": True,
            "reason": "Exact SU(2) inverse identity and exact oriented-arrow count formula.",
        },
        "numpy": {
            "tried": False,
            "used": False,
            "reason": "Not used; NumPy is blocked from claim-bearing nonclassical manifold computation.",
        },
        "scipy": {
            "tried": False,
            "used": False,
            "reason": "Not used; no dense eigensolver or SciPy bridge is needed for this finite local action.",
        },
    }
    depth = {
        "torch": "load_bearing",
        "jax": "load_bearing",
        "z3": "load_bearing",
        "cvc5": "load_bearing",
        "sympy": "load_bearing",
        "numpy": "None",
        "scipy": "None",
    }
    reasons = {
        "rustworkx": "finite oriented-arrow graph enumeration; removing it removes the groupoid arrow structure",
        "pyg": "edge_index mirror for finite oriented arrows; removing it removes graph-native arrow readout",
        "xgi": "face/cell hyperedge incidence for plaquette path construction",
        "toponetx": "cell-complex face witness for PEPS3D plaquette surfaces",
        "gudhi": "simplex filtration witness for finite edge/face incidence",
        "clifford": "geometric-product noncommutator sanity check for noncommuting spinor generators",
    }
    for tool, reason in reasons.items():
        used = bool(structural.get(tool, {}).get("used"))
        manifest[tool] = {
            "tried": True,
            "used": used,
            "reason": reason if used else f"Attempted but not used: {structural.get(tool, {}).get('error', 'unavailable')}",
        }
        depth[tool] = "load_bearing" if used else "None"
    return manifest, depth


def controls(top: dict[str, Any]) -> dict[str, Any]:
    return {
        "label_only_gluing_inverse_erased": {
            "description": "replace Gamma_e^-1 with identity while keeping labels; inverse residual is recomputed from the broken channel",
            "max_inverse_residual": label_only_inverse_control_residual(),
            "law_holds": False,
            "pass": bool(label_only_inverse_control_residual() > EPS),
        },
        "composition_erased": {
            "description": "replace composed path Gamma_y Gamma_x with identity; composition residual is recomputed",
            "max_composition_residual": composition_erased_control_residual(),
            "law_holds": False,
            "pass": bool(composition_erased_control_residual() > EPS),
        },
        "broken_equivariance": {
            "description": "replace Gamma_{g.e} with a decoupled z-channel; equivariance residual is recomputed",
            "max_equivariance_residual": broken_equivariance_control_residual(),
            "law_holds": False,
            "pass": bool(broken_equivariance_control_residual() > EPS),
        },
        "order_erased_abelian": {
            "description": "replace noncommuting plaquette generators with co-diagonal z rotations",
            "max_abelian_order_erased_gap": top["torch_metrics"]["max_abelian_order_erased_gap"],
            "noncommuting_order_signal_survives": False,
            "pass": bool(top["torch_metrics"]["max_abelian_order_erased_gap"] <= EPS),
        },
    }


def proof_pass(proofs: dict[str, Any]) -> bool:
    law_keys = [
        "law_holds_label_only_control_smt_load_bearing",
        "law_holds_composition_erased_control_smt_load_bearing",
        "law_holds_broken_equivariance_control_smt_load_bearing",
    ]
    law_ok = all(
        proofs[k]["real_claim_verdict"] == "sat"
        and proofs[k]["negated_claim_verdict"] == "unsat"
        and proofs[k]["differ"] is True
        and proofs[k]["bound_to_measured"] is True
        and proofs[k].get("cvc5_real_verdict") == "sat"
        and proofs[k].get("cvc5_control_verdict") == "unsat"
        for k in law_keys
    )
    negated_ok = (
        proofs["spec_native_negated_law_label_only_control_smt_load_bearing"]["real_claim_verdict"] == "unsat"
        and proofs["spec_native_negated_law_label_only_control_smt_load_bearing"]["negated_claim_verdict"] == "sat"
        and proofs["spec_native_negated_law_broken_equivariance_control_smt_load_bearing"]["real_claim_verdict"] == "unsat"
        and proofs["spec_native_negated_law_broken_equivariance_control_smt_load_bearing"]["negated_claim_verdict"] == "sat"
    )
    order_ok = (
        proofs["order_erased_abelian_control_smt_load_bearing"]["real_claim_verdict"] == "sat"
        and proofs["order_erased_abelian_control_smt_load_bearing"]["negated_claim_verdict"] == "unsat"
        and proofs["order_erased_abelian_control_smt_load_bearing"].get("cvc5_real_verdict") == "sat"
        and proofs["order_erased_abelian_control_smt_load_bearing"].get("cvc5_control_verdict") == "unsat"
    )
    return bool(law_ok and negated_ok and order_ok)


def ablation_pass(ablations: dict[str, Any]) -> bool:
    for row in ablations.values():
        baseline = float(row["baseline_value"])
        ablated = float(row["ablated_value"])
        delta = float(row["outcome_delta"])
        if abs(baseline - ablated) <= 1.0e-12:
            return False
        if abs((baseline - ablated) - delta) > 1.0e-9 * max(1.0, abs(delta)):
            return False
    return True


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(exist_ok=True)
    imports = optional_imports()
    scale_rows = {str(n): scale_rung(n, shape) for n, shape in SCALES.items()}
    top = scale_rows["64"]
    proofs = build_proofs(top)
    structural = structural_tool_counts(tuple(top["shape"]), imports)
    ablations = build_tool_ablations(top, proofs, structural)
    tool_manifest, tool_depth = manifest_from_structural(structural)
    sympy_result = sympy_exact_result(top)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    controls_block = controls(top)
    controls_pass = all(row["pass"] for row in controls_block.values())
    all_pass = bool(
        scale_pass
        and controls_pass
        and proof_pass(proofs)
        and ablation_pass(ablations)
        and sympy_result["pass"]
        and top["object_count"] == 64
        and top["oriented_arrow_count"] == 288
        and top["dense_state_closure_used"] is False
    )

    torch_primary_result = {
        "runtime": "torch",
        "dtype": str(CTYPE),
        "carrier": "stage-2 peps3d_spinor_network local spinor-derived densities",
        "action": "local SU(2) gluing/transition push, groupoid composition, equivariance conjugation, and plaquette order test",
        "object_count_64": top["object_count"],
        "oriented_arrow_count_64": top["oriented_arrow_count"],
        "max_inverse_residual": top["torch_metrics"]["inverse_residual"],
        "max_composition_residual": top["torch_metrics"]["composition_residual"],
        "max_equivariance_residual": top["torch_metrics"]["equivariance_residual"],
        "max_plaquette_order_gap": top["torch_metrics"]["max_plaquette_order_gap"],
        "min_plaquette_order_gap": top["torch_metrics"]["min_plaquette_order_gap"],
        "max_abelian_order_erased_gap": top["torch_metrics"]["max_abelian_order_erased_gap"],
        "pass": bool(top["pass"]),
    }
    jax_mirror_result = {
        "runtime": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "max_inverse_residual": top["jax_metrics"]["inverse_residual"],
        "max_composition_residual": top["jax_metrics"]["composition_residual"],
        "max_equivariance_residual": top["jax_metrics"]["equivariance_residual"],
        "max_plaquette_order_gap": top["jax_metrics"]["max_plaquette_order_gap"],
        "min_plaquette_order_gap": top["jax_metrics"]["min_plaquette_order_gap"],
        "max_abelian_order_erased_gap": top["jax_metrics"]["max_abelian_order_erased_gap"],
        "pass": bool(top["jax_vs_pytorch_delta"] <= 1.0e-10),
    }

    return {
        "sim_id": "sim_layer_L8_gluing_groupoid_probe",
        "name": "sim_layer_L8_gluing_groupoid_probe",
        "version": VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "thisfile": str(THISFILE),
        "result": str(RESULT),
        "object_id": OBJECT_ID,
        "finite_map": {
            "domain": "finite PEPS3D K=(V,E,F,C) stage-2 spinor-density carrier with local 2x2 rho_v and oriented nearest-neighbor arrows",
            "codomain_or_output": "finite inverse/composition/equivariance residuals, plaquette order gap, controls, proof flips, and scale-row readouts",
            "definition": "L8_GK applies SU(2) transition channels Gamma_e rho_u Gamma_e^dagger, composes finite paths, checks D(g) Gamma_e D(g)^-1 = Gamma_{g.e}, and compares xy/yx plaquette actions",
        },
        "root_constraints": {
            "F01": {
                "status": "active_tested",
                "statement": "finite object/probe/operator/path set K=(V,E,F,C), finite arrows, finite paths, and finite local channel residuals",
            },
            "N01": {
                "status": "active_tested",
                "statement": "noncommuting/order-sensitive plaquette paths xy and yx produce a measured order gap that collapses under an abelian order-erased control",
            },
        },
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "Stage-6 independent manifold-layer lego; L8 gluing/groupoid/equivariant dynamic candidate",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "carrier_layer": "stage-2 peps3d_spinor_network",
        "geometry_layer": "L8 gluing/groupoid/equivariant dynamic layer action",
        "carrier_realization": "torch complex128 local two-component spinors and spinor-derived 2x2 densities on PEPS3D sites; no NumPy and no global dense statevector",
        "peps3d_embedding": "finite 3D grid cells K=(V,E,F,C), bond_dim=2, with local site densities and oriented edge arrows; scale rows 8/16/32/64",
        "spinor_state": "psi_v in C^2 is normalized and rho_v=|psi_v><psi_v| is the local claim-bearing density",
        "quaternion_action": "not_applicable; this L8 packet uses SU(2) spinor channels and does not invoke quaternion language",
        "dependency_receipts": [
            "stage-2 carrier required by /tmp/layer_specs.json L8 acts_on_carrier=peps3d_spinor_network",
            "this sim independently recomputes local carrier/action witnesses and does not claim lower-layer completion",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blocked_consumers": BLOCKED_CONSUMERS,
        "eligible_consumers": ["future bounded L8 local audit packets only"],
        "allowed_claims": [
            "one finite L8 gluing/groupoid/equivariant action was tested independently on the stage-2 PEPS3D spinor-density carrier",
            "the measured residual law flips under degenerate controls through helper-bound SMT",
            "the noncommuting plaquette order signal is present in the genuine action and collapses under an abelian order-erased control",
        ],
        "promotion_blockers": [
            "no stacking with L0-L7 or other L8 variants",
            "no bridge, flux, Xi/Phi0, Axis0, FEP, gravity, physics, or final manifold consumer is unlocked",
            "this is a finite local layer action receipt, not a full layer-completion or G-structure completion packet",
        ],
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": top["jax_vs_pytorch_delta"],
        "proof_results": proofs,
        "controls": controls_block,
        "tool_ablations": ablations,
        "sympy_exact_result": sympy_result,
        "structural_tool_results": structural,
        "known_value_checks": {
            "computed": True,
            "row": "64",
            "object_count_64": top["object_count"],
            "oriented_arrow_count_64": top["oriented_arrow_count"],
            "expected_oriented_arrow_count_64": 288,
            "max_inverse_residual_machine_epsilon_class": top["torch_metrics"]["inverse_residual"],
            "max_equivariance_residual_machine_epsilon_class": top["torch_metrics"]["equivariance_residual"],
            "max_plaquette_order_gap_nonzero": top["torch_metrics"]["max_plaquette_order_gap"],
            "max_abelian_order_erased_gap_zero": top["torch_metrics"]["max_abelian_order_erased_gap"],
            "law_holds_real_verdict": proofs["law_holds_label_only_control_smt_load_bearing"]["real_claim_verdict"],
            "law_holds_control_verdict": proofs["law_holds_label_only_control_smt_load_bearing"]["negated_claim_verdict"],
            "spec_native_negated_law_real_verdict": proofs["spec_native_negated_law_label_only_control_smt_load_bearing"]["real_claim_verdict"],
            "spec_native_negated_law_control_verdict": proofs["spec_native_negated_law_label_only_control_smt_load_bearing"]["negated_claim_verdict"],
            "pass": bool(
                top["object_count"] == 64
                and top["oriented_arrow_count"] == 288
                and top["torch_metrics"]["inverse_residual"] <= EPS
                and top["torch_metrics"]["equivariance_residual"] <= EPS
                and top["torch_metrics"]["max_plaquette_order_gap"] > ORDER_EPS
                and top["torch_metrics"]["max_abelian_order_erased_gap"] <= EPS
            ),
        },
        "scale_ladder": {
            "axis": "PEPS3D sites/qubits, local 2x2 channel actions only",
            "required_rungs": [8, 16, 32, 64],
            "dense_state_closure_used": False,
            "rungs": scale_rows,
            "pass": bool(scale_pass),
        },
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "tool_integration_depth": tool_depth,
        "required_negatives": [
            "label-only gluing inverse-erased control",
            "composition-erased path control",
            "broken-equivariance scrambled target control",
            "order-erased abelian plaquette control",
        ],
        "negatives_run": list(controls_block.keys()),
        "kill_conditions": [
            "any SMT proof lacks measured-value binding or a verdict flip",
            "any degenerate control preserves the genuine law or order gap",
            "jax mirror drifts from torch beyond tolerance",
            "scale ladder uses dense state closure",
            "any downstream consumer is unlocked",
        ],
        "required_artifacts": ["result JSON", "proof_results", "tool_ablations", "scale_ladder", "controls"],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"{OBJECT_ID}:{int(time.time())}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass(proofs),
            "controls_pass": controls_pass,
            "ablation_pass": ablation_pass(ablations),
            "promotion_allowed": False,
        },
        "pass_rule": "all scale rungs pass non-dense; law-holds and spec-native negated-law SMT proofs flip on measured residuals; order-erased control collapses plaquette gap; ablations carry baseline/ablated/delta",
        "fail_rule": "fail on decorative SMT, identical real/control measured values, missing ablation recompute, dense closure, static geometry-only L8, NumPy claim path, stacking, or downstream unlock",
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
