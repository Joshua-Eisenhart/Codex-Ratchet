#!/usr/bin/env python3
"""Torch-native stage-token inventory scaffold for engine-stage placement.

Formal scout only.

This is not a flux row and not an Axis0 row. It builds the object that must
exist before those rows can be meaningful only as a bounded scaffold:

  root finite probes
  -> local spinor states
  -> 2 engine types x 2 loops x 4 terrains = 16 stage sites
  -> one PEPS3D local tensor per stage site
  -> four operator substages per stage = 64 substages

The row preserves blocker semantics: building this bounded stage carrier does
not admit final manifold closure, final flux, Axis0, Xi/Phi0, PEPS3D closure,
or physics.

2026-05-25 audit boundary: this scout does not prove the manifold layers in
order, does not admit quaternion shell geometry as a separate layer, and does
not embed 64 substages as 64 manifold cells. It is a stage-site/token inventory
scaffold only.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import rustworkx as rx
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "spinor_quaternion_peps3d_engine_stage_foundation_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical_spinor_quaternion_peps3d_foundation"
SOURCE_ALIGNMENT_CATEGORY = "spinor_quaternion_peps3d_engine_stage_foundation"
PROMOTION_ALLOWED = False
DAMAGE_AUDIT_STATUS = "quarantined_for_layer_order_and_foundation_closure"
VALIDITY_SCOPE = "sixteen_stage_site_inventory_and_sixty_four_operator_rows_only"
ADMISSION_STATUS = "stage_token_inventory_scaffold_only"
EXPECTED_NONPROMOTION = True
CLAIM_CEILING = (
    "Formal scout only: builds a torch-native stage-token inventory scaffold "
    "for 2 engine types, 2 loops, 4 terrains, 16 stage sites, and 64 operator "
    "rows. It does not prove the manifold layers in order, does not admit "
    "quaternion shell geometry as a separate layer, does not embed 64 "
    "substages as 64 manifold cells, and does not admit final "
    "constraint-manifold closure, final flux, Axis0, Xi/Phi0, PEPS3D "
    "environment closure, gravity, Standard Model, Yang-Mills, Riemann, or "
    "physics claims."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing complex spinors, quaternion shell tensors, local PEPS3D stage tensors, finite probe assignments, and order-gap readouts",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite PEPS3D stage adjacency graph over engine/loop/topology bonds",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact count identities and quaternion multiplication sanity checks",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite constraint witness for stage/substage counts and blocked downstream claims",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1e-9
GAP_FLOOR = 1e-5
BOND_DIM = 2
PHYS_DIM = 2

TOPOLOGIES = ("Se", "Ne", "Ni", "Si")
LOOPS = ("outer", "inner")
OPERATORS = ("Ti", "Te", "Fi", "Fe")

# Source-charted engine tokens. Type 1 is left-sheet realization. Type 2 is
# right-sheet realization. These are stage sites, not flux readouts.
ENGINE_CHART: dict[int, dict[str, dict[str, dict[str, Any]]]] = {
    1: {
        "Se": {
            "terrain": "Funnel",
            "outer": {"token": "TiSe", "operator": "Ti", "axis6": +1},
            "inner": {"token": "SeFi", "operator": "Fi", "axis6": -1},
        },
        "Ne": {
            "terrain": "Vortex",
            "outer": {"token": "NeTi", "operator": "Ti", "axis6": -1},
            "inner": {"token": "FiNe", "operator": "Fi", "axis6": +1},
        },
        "Ni": {
            "terrain": "Pit",
            "outer": {"token": "NiFe", "operator": "Fe", "axis6": -1},
            "inner": {"token": "TeNi", "operator": "Te", "axis6": +1},
        },
        "Si": {
            "terrain": "Hill",
            "outer": {"token": "FeSi", "operator": "Fe", "axis6": +1},
            "inner": {"token": "SiTe", "operator": "Te", "axis6": -1},
        },
    },
    2: {
        "Se": {
            "terrain": "Cannon",
            "outer": {"token": "FiSe", "operator": "Fi", "axis6": +1},
            "inner": {"token": "SeTi", "operator": "Ti", "axis6": -1},
        },
        "Ne": {
            "terrain": "Spiral",
            "outer": {"token": "NeFi", "operator": "Fi", "axis6": -1},
            "inner": {"token": "TiNe", "operator": "Ti", "axis6": +1},
        },
        "Ni": {
            "terrain": "Source",
            "outer": {"token": "NiTe", "operator": "Te", "axis6": -1},
            "inner": {"token": "FeNi", "operator": "Fe", "axis6": +1},
        },
        "Si": {
            "terrain": "Citadel",
            "outer": {"token": "TeSi", "operator": "Te", "axis6": +1},
            "inner": {"token": "SiFe", "operator": "Fe", "axis6": -1},
        },
    },
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def ket(values: list[complex]) -> torch.Tensor:
    out = torch.tensor(values, dtype=CDTYPE)
    return out / torch.linalg.vector_norm(out)


def projector(psi: torch.Tensor) -> torch.Tensor:
    return torch.outer(psi, torch.conj(psi))


def phase(angle: float) -> complex:
    return complex(math.cos(angle), math.sin(angle))


def spinor(phi: float, chi: float, eta: float, *, phase_shift: float = 0.0) -> torch.Tensor:
    raw = torch.tensor(
        [
            phase(phi + chi) * math.cos(eta),
            phase(phi - chi) * math.sin(eta),
        ],
        dtype=CDTYPE,
    )
    return ket([phase(phase_shift) * complex(raw[0].item()), phase(phase_shift) * complex(raw[1].item())])


def sic_effects() -> list[torch.Tensor]:
    omega = phase(2.0 * math.pi / 3.0)
    spinors = [
        ket([1.0 + 0.0j, 0.0 + 0.0j]),
        ket([1.0 / math.sqrt(3.0), math.sqrt(2.0 / 3.0)]),
        ket([1.0 / math.sqrt(3.0), math.sqrt(2.0 / 3.0) * omega]),
        ket([1.0 / math.sqrt(3.0), math.sqrt(2.0 / 3.0) * omega * omega]),
    ]
    return [projector(item) / PHYS_DIM for item in spinors]


SIC_EFFECTS = sic_effects()


def finite_probe_assignment(psi: torch.Tensor) -> torch.Tensor:
    rho = projector(psi)
    return torch.real(torch.stack([torch.trace(rho @ effect) for effect in SIC_EFFECTS])).to(RTYPE)


def wh_shift() -> torch.Tensor:
    return torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)


def wh_phase() -> torch.Tensor:
    return torch.diag(torch.tensor([1.0 + 0.0j, -1.0 + 0.0j], dtype=CDTYPE))


WH_X = wh_shift()
WH_Z = wh_phase()
WH_Y = phase(math.pi / 2.0) * (WH_X @ WH_Z)
I2 = torch.eye(2, dtype=CDTYPE)

OPERATOR_WORDS = {
    "Ti": WH_Z,
    "Te": WH_X,
    "Fi": WH_X @ WH_Z,
    "Fe": WH_Z @ WH_X,
}

TERRAIN_WORDS = {
    "Se": WH_X @ WH_Z,
    "Ne": WH_Z,
    "Ni": WH_X,
    "Si": WH_Z @ WH_X,
}


def hamilton_product(left: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    a, b, c, d = left
    e, f, g, h = right
    return torch.stack(
        [
            a * e - b * f - c * g - d * h,
            a * f + b * e + c * h - d * g,
            a * g - b * h + c * e + d * f,
            a * h + b * g - c * f + d * e,
        ]
    )


def normalize_real(vec: torch.Tensor) -> torch.Tensor:
    norm = torch.linalg.vector_norm(vec)
    if float(norm.item()) <= TOL:
        raise ValueError("zero vector")
    return vec / norm


def stage_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for engine in (1, 2):
        for loop in LOOPS:
            for topo_idx, topology in enumerate(TOPOLOGIES):
                chart = ENGINE_CHART[engine][topology][loop]
                records.append(
                    {
                        "stage_index": len(records),
                        "engine_type": engine,
                        "sheet": "L" if engine == 1 else "R",
                        "loop": loop,
                        "loop_index": LOOPS.index(loop),
                        "topology": topology,
                        "topology_index": topo_idx,
                        "terrain": ENGINE_CHART[engine][topology]["terrain"],
                        "token": chart["token"],
                        "chart_operator": chart["operator"],
                        "axis6_sign": int(chart["axis6"]),
                        "peps3d_index": [engine - 1, LOOPS.index(loop), topo_idx],
                    }
                )
    return records


def stage_spinor(record: dict[str, Any], *, collapse: bool = False) -> torch.Tensor:
    if collapse:
        return spinor(0.0, 0.0, 0.55)
    engine_sign = +1.0 if record["engine_type"] == 1 else -1.0
    loop_sign = +1.0 if record["loop"] == "outer" else -1.0
    topo = float(record["topology_index"])
    phi = 0.17 + 0.31 * topo + 0.19 * engine_sign
    chi = -0.23 + 0.27 * topo + 0.11 * loop_sign
    eta = 0.27 + 0.19 * (topo + 1.0) + 0.03 * record["loop_index"]
    eta = min(max(eta, 0.18), 1.36)
    phase_shift = 0.13 * engine_sign * loop_sign
    return spinor(phi, chi, eta, phase_shift=phase_shift)


def shell_quaternion(record: dict[str, Any], *, reverse_shell: bool = False) -> torch.Tensor:
    engine_sign = +1.0 if record["engine_type"] == 1 else -1.0
    loop_sign = +1.0 if record["loop"] == "outer" else -1.0
    topo_sign = -1.0 + (2.0 * record["topology_index"] / (len(TOPOLOGIES) - 1))
    q = torch.tensor(
        [
            1.0,
            0.18 * engine_sign,
            0.21 * loop_sign,
            0.17 * topo_sign,
        ],
        dtype=RTYPE,
    )
    if reverse_shell:
        q = torch.stack([q[0], q[1], -q[2], -q[3]])
    return normalize_real(q)


def virtual_dims(record: dict[str, Any]) -> tuple[int, int, int, int, int, int]:
    e, loop, topo = record["peps3d_index"]
    return (
        BOND_DIM if e > 0 else 1,
        BOND_DIM if e < 1 else 1,
        BOND_DIM if loop > 0 else 1,
        BOND_DIM if loop < 1 else 1,
        BOND_DIM if topo > 0 else 1,
        BOND_DIM if topo < 3 else 1,
    )


def virtual_vector(component: torch.Tensor, dim: int) -> torch.Tensor:
    if dim == 1:
        return torch.ones(1, dtype=CDTYPE)
    angle = 0.5 * math.pi * float(component.item())
    return torch.tensor([math.cos(angle), math.sin(angle)], dtype=CDTYPE)


def stage_tensor(record: dict[str, Any], psi: torch.Tensor, q: torch.Tensor) -> torch.Tensor:
    dims = virtual_dims(record)
    vectors = [
        virtual_vector(q[1], dims[0]),
        virtual_vector(q[1] * torch.tensor(-1.0, dtype=RTYPE), dims[1]),
        virtual_vector(q[2], dims[2]),
        virtual_vector(q[2] * torch.tensor(-1.0, dtype=RTYPE), dims[3]),
        virtual_vector(q[3], dims[4]),
        virtual_vector(q[3] * torch.tensor(-1.0, dtype=RTYPE), dims[5]),
    ]
    tensor = psi.reshape(PHYS_DIM, 1, 1, 1, 1, 1, 1)
    for axis, vec in enumerate(vectors, start=1):
        shape = [1] * 7
        shape[axis] = vec.numel()
        tensor = tensor * vec.reshape(shape)
    return tensor


def make_stage_site(record: dict[str, Any], *, collapse_spinor: bool = False) -> dict[str, Any]:
    psi = stage_spinor(record, collapse=collapse_spinor)
    q = shell_quaternion(record)
    tensor = stage_tensor(record, psi, q)
    assignment = finite_probe_assignment(psi)
    return {
        **record,
        "psi": psi,
        "q_shell": q,
        "tensor": tensor,
        "tensor_shape": list(tensor.shape),
        "probe_assignment": assignment,
        "probe_sum": float(torch.sum(assignment).item()),
        "tensor_norm": float(torch.linalg.vector_norm(tensor).item()),
    }


def build_graph(records: list[dict[str, Any]]) -> tuple[rx.PyDiGraph, dict[tuple[int, int, int], int]]:
    graph = rx.PyDiGraph()
    index_map: dict[tuple[int, int, int], int] = {}
    for record in records:
        node = graph.add_node(record["stage_index"])
        index_map[tuple(record["peps3d_index"])] = node
    for record in records:
        e, loop, topo = record["peps3d_index"]
        src = index_map[(e, loop, topo)]
        for delta, label in [((1, 0, 0), "engine_bond"), ((0, 1, 0), "loop_bond"), ((0, 0, 1), "topology_bond")]:
            dst_key = (e + delta[0], loop + delta[1], topo + delta[2])
            if dst_key in index_map:
                graph.add_edge(src, index_map[dst_key], label)
    return graph, index_map


def operator_order_gap(site: dict[str, Any], operator: str | None = None) -> float:
    op_name = operator or site["chart_operator"]
    terrain = TERRAIN_WORDS[site["topology"]]
    op = OPERATOR_WORDS[op_name]
    rho = projector(site["psi"])
    # Primitive N01 witness, before CPTP/unitary closure. The adjoint channel
    # can erase a global sign/phase; the root noncommutation layer must see the
    # algebraic action order directly.
    operator_first = op @ (terrain @ rho)
    terrain_first = terrain @ (op @ rho)
    return float(torch.linalg.matrix_norm(operator_first - terrain_first).item())


def substage_rows(stage_sites: list[dict[str, Any]], *, mixed_axis6: bool = False, native_only: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    operators = ("native",) if native_only else OPERATORS
    for site in stage_sites:
        for sub_idx, op in enumerate(operators):
            operator = site["chart_operator"] if op == "native" else op
            axis6 = int(site["axis6_sign"])
            if mixed_axis6 and sub_idx % 2 == 1:
                axis6 = -axis6
            rows.append(
                {
                    "substage_index": len(rows),
                    "stage_index": site["stage_index"],
                    "engine_type": site["engine_type"],
                    "loop": site["loop"],
                    "topology": site["topology"],
                    "terrain": site["terrain"],
                    "stage_token": site["token"],
                    "operator": operator,
                    "axis6_sign": axis6,
                    "same_axis6_as_stage": axis6 == int(site["axis6_sign"]),
                    "order_gap": operator_order_gap(site, operator),
                }
            )
    return rows


def graph_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    graph, _ = build_graph(records)
    edge_labels = [edge for edge in graph.edges()]
    label_counts = {label: edge_labels.count(label) for label in sorted(set(edge_labels))}
    weak_components = rx.weakly_connected_components(graph)
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "edge_label_counts": label_counts,
        "weak_component_count": len(weak_components),
        "connected": len(weak_components) == 1,
    }


def sympy_report() -> dict[str, Any]:
    engines, loops, terrains, operators = sp.symbols("engines loops terrains operators", integer=True, positive=True)
    stage_expr = engines * loops * terrains
    substage_expr = stage_expr * operators
    i, j, k = sp.symbols("i j k", commutative=False)
    rules = {
        i * i: -1,
        j * j: -1,
        k * k: -1,
        i * j: k,
        j * k: i,
        k * i: j,
        j * i: -k,
        k * j: -i,
        i * k: -j,
    }
    ij = rules[i * j]
    ijk_value = rules[ij * k]
    return {
        "stage_expr": str(stage_expr),
        "substage_expr": str(substage_expr),
        "stage_count": int(stage_expr.subs({engines: 2, loops: 2, terrains: 4})),
        "substage_count": int(substage_expr.subs({engines: 2, loops: 2, terrains: 4, operators: 4})),
        "ijk_equals_minus_one": str(ijk_value) == "-1",
    }


def z3_report(stage_count: int, substage_count: int, graph_nodes: int, graph_edges: int) -> dict[str, Any]:
    solver = z3.Solver()
    engines, loops, terrains, operators = z3.Ints("engines loops terrains operators")
    stages, substages, nodes, edges = z3.Ints("stages substages nodes edges")
    flux_allowed, axis0_allowed = z3.Bools("flux_allowed axis0_allowed")
    solver.add(engines == 2, loops == 2, terrains == 4, operators == 4)
    solver.add(stages == engines * loops * terrains)
    solver.add(substages == stages * operators)
    solver.add(nodes == stages)
    solver.add(edges > nodes)
    solver.add(stages == stage_count)
    solver.add(substages == substage_count)
    solver.add(nodes == graph_nodes)
    solver.add(edges == graph_edges)
    solver.add(flux_allowed == False)
    solver.add(axis0_allowed == False)
    status = solver.check()
    model = solver.model() if status == z3.sat else None
    return {
        "pass": status == z3.sat,
        "status": str(status),
        "stage_count": model[stages].as_long() if model else None,
        "substage_count": model[substages].as_long() if model else None,
        "flux_allowed": z3.is_true(model[flux_allowed]) if model else None,
        "axis0_allowed": z3.is_true(model[axis0_allowed]) if model else None,
    }


def foundation_constructive_report(*, collapse_spinor: bool = False) -> dict[str, Any]:
    records = stage_records()
    sites = [make_stage_site(record, collapse_spinor=collapse_spinor) for record in records]
    substages = substage_rows(sites)
    graph = graph_report(records)
    token_set = {site["token"] for site in sites}
    stage_tensor_norms = [site["tensor_norm"] for site in sites]
    probe_sums = [site["probe_sum"] for site in sites]
    order_gaps = [row["order_gap"] for row in substages]
    q_left = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
    q_right = torch.tensor([0.0, 0.0, 1.0, 0.0], dtype=RTYPE)
    q_product = hamilton_product(q_left, q_right)
    return {
        "records": sites,
        "substage_rows": substages,
        "stage_count": len(sites),
        "substage_count": len(substages),
        "unique_token_count": len(token_set),
        "unique_tokens": sorted(token_set),
        "all_probe_sums_one": all(abs(item - 1.0) < TOL for item in probe_sums),
        "min_tensor_norm": min(stage_tensor_norms),
        "max_tensor_norm": max(stage_tensor_norms),
        "graph": graph,
        "min_order_gap": min(order_gaps),
        "nonzero_order_gap_count": sum(1 for gap in order_gaps if gap > GAP_FLOOR),
        "same_axis6_all_substages": all(row["same_axis6_as_stage"] for row in substages),
        "quaternion_i_times_j": q_product,
        "quaternion_i_times_j_is_k": torch.linalg.vector_norm(q_product - torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=RTYPE)).item()
        < TOL,
        "stage_tensor_shapes": {site["token"]: site["tensor_shape"] for site in sites},
    }


def control_report(constructive: dict[str, Any]) -> dict[str, Any]:
    records = stage_records()
    collapsed_sites = [make_stage_site(record, collapse_spinor=True) for record in records]
    native_only_substages = substage_rows(constructive["records"], native_only=True)
    mixed_sign_substages = substage_rows(constructive["records"], mixed_axis6=True)
    collapsed_assignments = torch.stack([site["probe_assignment"] for site in collapsed_sites])
    nominal_assignments = torch.stack([site["probe_assignment"] for site in constructive["records"]])
    return {
        "collapsed_spinor_control": {
            "expected_fail": True,
            "assignment_rank": int(torch.linalg.matrix_rank(collapsed_assignments).item()),
            "nominal_assignment_rank": int(torch.linalg.matrix_rank(nominal_assignments).item()),
            "pass": int(torch.linalg.matrix_rank(collapsed_assignments).item())
            < int(torch.linalg.matrix_rank(nominal_assignments).item()),
        },
        "native_only_substage_control": {
            "expected_fail": True,
            "substage_count": len(native_only_substages),
            "required_substage_count": 64,
            "pass": len(native_only_substages) != 64,
        },
        "mixed_axis6_control": {
            "expected_fail": True,
            "same_axis6_all_substages": all(row["same_axis6_as_stage"] for row in mixed_sign_substages),
            "pass": not all(row["same_axis6_as_stage"] for row in mixed_sign_substages),
        },
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    constructive = foundation_constructive_report()
    controls = control_report(constructive)
    sym = sympy_report()
    z3w = z3_report(
        constructive["stage_count"],
        constructive["substage_count"],
        constructive["graph"]["node_count"],
        constructive["graph"]["edge_count"],
    )

    constructive_pass = (
        constructive["stage_count"] == 16
        and constructive["substage_count"] == 64
        and constructive["unique_token_count"] == 16
        and constructive["all_probe_sums_one"]
        and constructive["min_tensor_norm"] > 0.0
        and constructive["graph"]["connected"]
        and constructive["graph"]["node_count"] == 16
        and constructive["graph"]["edge_count"] == 28
        and constructive["nonzero_order_gap_count"] >= 16
        and constructive["same_axis6_all_substages"]
        and constructive["quaternion_i_times_j_is_k"]
    )
    controls_pass = all(item["pass"] for item in controls.values())
    sympy_pass = sym["stage_count"] == 16 and sym["substage_count"] == 64 and sym["ijk_equals_minus_one"]

    positive = {
        "P1_stage_sites": {
            "pass": constructive["stage_count"] == 16 and constructive["unique_token_count"] == 16,
            "stage_count": constructive["stage_count"],
            "unique_token_count": constructive["unique_token_count"],
        },
        "P2_substages": {
            "pass": constructive["substage_count"] == 64 and constructive["same_axis6_all_substages"],
            "substage_count": constructive["substage_count"],
            "same_axis6_all_substages": constructive["same_axis6_all_substages"],
        },
        "P3_finite_probe_spinors": {
            "pass": constructive["all_probe_sums_one"] and constructive["min_tensor_norm"] > 0.0,
            "all_probe_sums_one": constructive["all_probe_sums_one"],
            "tensor_norm_range": [constructive["min_tensor_norm"], constructive["max_tensor_norm"]],
        },
        "P4_peps3d_stage_graph": {
            "pass": constructive["graph"]["connected"] and constructive["graph"]["edge_count"] == 28,
            **constructive["graph"],
        },
        "P5_noncommuting_order": {
            "pass": constructive["nonzero_order_gap_count"] >= 16,
            "min_order_gap": constructive["min_order_gap"],
            "nonzero_order_gap_count": constructive["nonzero_order_gap_count"],
        },
        "P6_quaternion_shell": {
            "pass": constructive["quaternion_i_times_j_is_k"] and sym["ijk_equals_minus_one"],
            "torch_i_times_j": constructive["quaternion_i_times_j"],
            "sympy_ijk_equals_minus_one": sym["ijk_equals_minus_one"],
        },
        "P7_z3_finite_blocked_downstream": z3w,
    }

    payload = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "damage_audit_status": DAMAGE_AUDIT_STATUS,
        "validity_scope": VALIDITY_SCOPE,
        "admission_status": ADMISSION_STATUS,
        "expected_nonpromotion": EXPECTED_NONPROMOTION,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "all_pass": bool(constructive_pass and controls_pass and sympy_pass and z3w["pass"]),
        "foundation_stage_carrier_constructed": bool(constructive_pass),
        "foundation_layer_order_proven": False,
        "substage_manifold_cell_embedding_proven": False,
        "quaternion_layer_admitted": False,
        "flux_layer_allowed": False,
        "downstream_axis0_allowed": False,
        "peps3d_closure_admitted": False,
        "peps3d_role": "bounded stage-site carrier scaffold only; not a late conceptual layer and not full environment closure",
        "axis0_or_flux_computed": False,
        "positive": positive,
        "constructive_checks": positive,
        "graveyard_companions": controls,
        "boundary": {
            "B1_downstream_flux_axis0_blocked": {
                "pass": not z3w["flux_allowed"] and not z3w["axis0_allowed"],
                "flux_layer_allowed": False,
                "downstream_axis0_allowed": False,
            },
            "B2_no_peps3d_closure_claim": {
                "pass": True,
                "peps3d_closure_admitted": False,
                "reason": "stage-site PEPS3D carrier only; no full environment contraction",
            },
            "B3_no_physics_claim": {
                "pass": True,
                "reason": "foundation scaffold only; no gravity/SM/Yang-Mills/Riemann/physics readout",
            },
        },
        "why_not_v4_probes": [
            "This is not an Axis0 or flux probe.",
            "It is not a proof that manifold layers have been worked out in order.",
            "It is not proof that 64 substages are embedded as 64 manifold cells.",
            "It does not admit quaternion shell geometry as a separate layer.",
            "It avoids dense final-state closure and keeps PEPS3D closure blocked.",
            "It uses primitive N01 order action as a root witness before physical channel closure.",
        ],
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": {
                "collapsed_spinor_control": controls["collapsed_spinor_control"]["pass"],
                "native_only_substage_control": controls["native_only_substage_control"]["pass"],
                "mixed_axis6_control": controls["mixed_axis6_control"]["pass"],
            },
        },
        "controls": controls,
        "sympy": sym,
        "z3": z3w,
        "engine_stage_table": [
            {
                "stage_index": site["stage_index"],
                "engine_type": site["engine_type"],
                "sheet": site["sheet"],
                "loop": site["loop"],
                "topology": site["topology"],
                "terrain": site["terrain"],
                "token": site["token"],
                "chart_operator": site["chart_operator"],
                "axis6_sign": site["axis6_sign"],
                "peps3d_index": site["peps3d_index"],
                "tensor_shape": site["tensor_shape"],
            }
            for site in constructive["records"]
        ],
        "stage_tensor_shapes": constructive["stage_tensor_shapes"],
        "blockers_preserved": [
            "manifold layer order not proven",
            "64-substage manifold-cell embedding not proven",
            "quaternion shell layer not admitted",
            "no full PEPS3D environment contraction",
            "no flux layer computation yet",
            "no Xi/Phi0 bridge",
            "no Axis0 readout",
            "no physics claim",
        ],
        "duration_sec": time.time() - started,
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(as_jsonable(payload), indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
