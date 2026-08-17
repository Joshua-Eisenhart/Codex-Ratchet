#!/usr/bin/env python3
"""Bounded CB Light manifold capability campaign.

This scratch operation keeps four stages separate:

1. A deterministic Cartesian-product spawner creates finite DOF candidates.
2. JAX probes paired spinor-memory and density-channel dynamics.
3. Z3 and CVC5 independently gate quantized measured values.
4. Rustworkx maps only the surviving observation rows.

It is a functional capability diagnostic, not a physical, Axis-0, chirality,
manifold-completion, or formal-admission result.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import itertools
import json
import math
import os
import platform
import sys
from collections import Counter
from pathlib import Path
from typing import Any

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/cb-matplotlib-cache")

import cvc5
import jax
import rustworkx as rx
import sympy as sp
import z3
from cvc5 import Kind

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp


SCHEMA = "constraintbox.manifold-capability-campaign.v1"
ROWS_SCHEMA = "constraintbox.manifold-capability-probe-row.v1"
CLASSIFICATION = "scratch_diagnostic"
SCALE = 1_000_000

MEMORY_FIDELITY_MIN = 800_000
MEMORY_IMPROVEMENT_MIN = 10_000
FIXED_RESIDUAL_MAX = 1_000
TRACE_ERROR_MAX = 10
MIN_EIGENVALUE_MIN = -10
ORDER_GAP_MIN = 30_000
COMMUTING_GAP_MAX = 10


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def has_direct_numpy_import(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name == "numpy" or alias.name.startswith("numpy.")
            for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and node.module and (
            node.module == "numpy" or node.module.startswith("numpy.")
        ):
            return True
    return False


def load_light_base(repo: Path) -> dict[str, Any]:
    source = repo / "constraint_box" / "scripts" / "contained_light" / "entropic_time_field.py"
    fixture = (
        repo
        / "constraint_box"
        / "scripts"
        / "contained_light"
        / "fixtures"
        / "entropic_time_field_v1.json"
    )
    spec = importlib.util.spec_from_file_location("cb_entropic_time_field_base", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load current entropic-time field source")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    body = module.evaluate_file(fixture, engine="dual")
    if body.get("status") != "PASS":
        raise RuntimeError(f"base one-gradient operation did not pass: {body}")
    return {
        "source_path": str(source),
        "source_sha256": file_sha(source),
        "fixture_path": str(fixture),
        "fixture_sha256": file_sha(fixture),
        "operation_id": body["operation_id"],
        "result_sha256": body["result_sha256"],
        "one_gradient": body["field"]["one_gradient"],
        "claim_ceiling": body["claim_ceiling"],
    }


def memories_and_bonds():
    memory_zero = jnp.tile(
        jnp.asarray([[1.0, 0.0]], dtype=jnp.complex128), (4, 1)
    )
    phases = jnp.asarray([1.0, 1.0j, -1.0, -1.0j], dtype=jnp.complex128)
    memory_one = jnp.stack(
        [jnp.zeros(4, dtype=jnp.complex128), phases], axis=1
    )
    memories = jnp.stack([memory_zero, memory_one])

    complete = jnp.ones((4, 4), dtype=jnp.float64) - jnp.eye(
        4, dtype=jnp.float64
    )
    ring = jnp.asarray(
        [[0, 1, 0, 1], [1, 0, 1, 0], [0, 1, 0, 1], [1, 0, 1, 0]],
        dtype=jnp.float64,
    )
    matching = jnp.asarray(
        [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
        dtype=jnp.float64,
    )
    erased = jnp.zeros((4, 4), dtype=jnp.float64)
    bonds = jnp.stack([complete, ring, matching, erased])
    return memories, bonds


MEMORIES, BOND_GRAPHS = memories_and_bonds()
MIXTURE_ANGLES = jnp.asarray(
    [0.08, 0.32, 0.58, 0.74, 0.83, 0.99, 1.25, 1.49], dtype=jnp.float64
)
CORRUPTION_MASK_VALUES = (0, 1, 2, 4, 8, 3, 5, 15)
CORRUPTION_MASKS = jnp.asarray(CORRUPTION_MASK_VALUES, dtype=jnp.int32)
CORRUPTION_ANGLES = jnp.asarray([0.18, 0.50], dtype=jnp.float64)
DEPHASING = jnp.asarray([0.20, 0.55], dtype=jnp.float64)
TIME_STEPS = jnp.asarray([0.20, 0.35, 0.50], dtype=jnp.float64)


def normalize_nodes(value):
    return value / jnp.maximum(jnp.linalg.norm(value, axis=-1, keepdims=True), 1e-15)


def initial_spinors(mixture_id, corruption_mask_id, angle_id, sign_id):
    mixture = MIXTURE_ANGLES[mixture_id]
    value = normalize_nodes(
        jnp.cos(mixture) * MEMORIES[0] + jnp.sin(mixture) * MEMORIES[1]
    )
    theta = CORRUPTION_ANGLES[angle_id] * jnp.where(sign_id == 0, 1.0, -1.0)
    cosine = jnp.cos(theta / 2.0)
    sine = jnp.sin(theta / 2.0)
    rotation = jnp.asarray(
        [[cosine, -sine], [sine, cosine]], dtype=jnp.complex128
    )
    corruption_mask = CORRUPTION_MASKS[corruption_mask_id]
    selected = ((corruption_mask >> jnp.arange(4)) & 1).astype(bool)
    rotated = jax.vmap(
        lambda spinor, flag: jnp.where(flag, rotation @ spinor, spinor)
    )(value, selected)
    return normalize_nodes(rotated)


def spinor_recall(value, bond_id, steps=5):
    """Bond-weighted associative recall over stored node-spinor patterns."""

    adjacency = BOND_GRAPHS[bond_id]

    def update(_, current):
        local_fidelity = jnp.abs(
            jnp.einsum("mni,ni->mn", jnp.conj(MEMORIES), current)
        ) ** 2
        memory_scores = 0.5 * jnp.einsum(
            "ij,mi,mj->m", adjacency, local_fidelity, local_fidelity
        )
        weights = jax.nn.softmax(1.2 * (memory_scores - jnp.max(memory_scores)))
        target = jnp.einsum("m,mni->ni", weights, MEMORIES)
        return normalize_nodes(0.15 * current + 0.85 * target)

    return jax.lax.fori_loop(0, steps, update, value)


def density_of(spinors):
    return jnp.einsum("ni,nj->nij", spinors, jnp.conj(spinors))


def unitary(axis, theta):
    cosine = jnp.cos(theta / 2.0)
    sine = jnp.sin(theta / 2.0)
    if axis == "x":
        return jnp.asarray(
            [[cosine, -1.0j * sine], [-1.0j * sine, cosine]],
            dtype=jnp.complex128,
        )
    return jnp.asarray(
        [[jnp.exp(-0.5j * theta), 0.0], [0.0, jnp.exp(0.5j * theta)]],
        dtype=jnp.complex128,
    )


def apply_unitary(rho, matrix):
    return jnp.einsum("ab,nbc,dc->nad", matrix, rho, jnp.conj(matrix))


def bind_dephase(rho, strength):
    diagonal = (
        jnp.zeros_like(rho)
        .at[:, 0, 0]
        .set(rho[:, 0, 0])
        .at[:, 1, 1]
        .set(rho[:, 1, 1])
    )
    return (1.0 - strength) * rho + strength * diagonal


def paired_engine(rho, strength, axis):
    left = rho
    right = rho
    gaps = []
    for theta in TIME_STEPS:
        rotation = unitary(axis, theta)
        left = bind_dephase(apply_unitary(left, rotation), strength)
        right = apply_unitary(bind_dephase(right, strength), rotation)
        eigenvalues = jnp.linalg.eigvalsh(left - right)
        gaps.append(0.5 * jnp.mean(jnp.sum(jnp.abs(eigenvalues), axis=1)))
    return left, right, jnp.stack(gaps)


def entropy_bits(rho):
    eigenvalues = jnp.clip(jnp.linalg.eigvalsh(rho), 1e-15, 1.0)
    return -jnp.sum(eigenvalues * jnp.log2(eigenvalues), axis=-1)


def probe_candidate(dofs):
    (
        mixture_id,
        corruption_mask_id,
        angle_id,
        sign_id,
        bond_id,
        dephase_id,
        density_fault_id,
    ) = dofs
    initial = initial_spinors(mixture_id, corruption_mask_id, angle_id, sign_id)
    recalled = spinor_recall(initial, bond_id)
    initial_by_memory = jnp.mean(
        jnp.abs(jnp.einsum("mni,ni->mn", jnp.conj(MEMORIES), initial)) ** 2,
        axis=1,
    )
    final_by_memory = jnp.mean(
        jnp.abs(jnp.einsum("mni,ni->mn", jnp.conj(MEMORIES), recalled)) ** 2,
        axis=1,
    )
    initial_best = jnp.max(initial_by_memory)
    final_best = jnp.max(final_by_memory)
    recalled_again = spinor_recall(recalled, bond_id, 1)
    fixed_residual = jnp.linalg.norm(recalled_again - recalled)

    initial_density = density_of(recalled)
    strength = DEPHASING[dephase_id]
    left, right, order_gaps = paired_engine(initial_density, strength, "x")
    _, _, commuting_gaps = paired_engine(initial_density, strength, "z")
    signed_fault = jnp.asarray([[-2.0, 0.0], [0.0, 2.0]], dtype=jnp.complex128)[
        None, :, :
    ]
    left = jnp.where(density_fault_id == 1, 1.1 * left, left)
    right = jnp.where(density_fault_id == 1, 1.1 * right, right)
    left = jnp.where(density_fault_id == 2, left + signed_fault, left)
    right = jnp.where(density_fault_id == 2, right + signed_fault, right)
    left_eigenvalues = jnp.linalg.eigvalsh(left)
    right_eigenvalues = jnp.linalg.eigvalsh(right)
    trace_error = jnp.maximum(
        jnp.max(jnp.abs(jnp.trace(left, axis1=1, axis2=2) - 1.0)),
        jnp.max(jnp.abs(jnp.trace(right, axis1=1, axis2=2) - 1.0)),
    )
    minimum_eigenvalue = jnp.minimum(
        jnp.min(left_eigenvalues), jnp.min(right_eigenvalues)
    )
    return jnp.asarray(
        [
            initial_best,
            final_best,
            final_best - initial_best,
            jnp.argmax(initial_by_memory),
            jnp.argmax(final_by_memory),
            fixed_residual,
            order_gaps[-1],
            jnp.max(commuting_gaps),
            trace_error.real,
            minimum_eigenvalue.real,
            jnp.mean(entropy_bits(left)),
            jnp.mean(entropy_bits(right)),
            order_gaps[0],
            order_gaps[1],
            order_gaps[2],
        ],
        dtype=jnp.float64,
    )


PROBE_BATCH = jax.jit(jax.vmap(probe_candidate))


def candidate_dofs() -> list[tuple[int, ...]]:
    return list(
        itertools.product(
            range(8), range(8), range(2), range(2), range(4), range(2), range(3)
        )
    )


METRIC_NAMES = (
    "initial_best_fidelity",
    "final_best_fidelity",
    "best_fidelity_improvement",
    "initial_nearest_memory",
    "recall_class",
    "fixed_point_residual",
    "paired_order_gap",
    "commuting_control_gap",
    "trace_error",
    "minimum_eigenvalue",
    "mean_left_vn_entropy_bits",
    "mean_right_vn_entropy_bits",
    "order_gap_t0",
    "order_gap_t1",
    "order_gap_t2",
)


def quantize(value: float) -> int:
    return int(round(value * SCALE))


def make_probe_rows(dofs: list[tuple[int, ...]], measured) -> list[dict[str, Any]]:
    values = measured.tolist()
    rows = []
    for index, (coordinates, metrics) in enumerate(zip(dofs, values, strict=True)):
        metric_map = {name: float(value) for name, value in zip(METRIC_NAMES, metrics, strict=True)}
        quantized = {
            name: int(round(value))
            if name in {"initial_nearest_memory", "recall_class"}
            else quantize(float(value))
            for name, value in metric_map.items()
        }
        rows.append(
            {
                "schema": ROWS_SCHEMA,
                "candidate_id": f"c{index:04d}",
                "dofs": {
                    "mixture_angle_id": coordinates[0],
                    "corruption_mask_id": coordinates[1],
                    "corruption_angle_id": coordinates[2],
                    "rotation_sign_id": coordinates[3],
                    "bond_geometry_id": coordinates[4],
                    "dephasing_strength_id": coordinates[5],
                    "density_fault_id": coordinates[6],
                },
                "probes": metric_map,
                "quantized": quantized,
                "gate_dispositions": {},
            }
        )
    return rows


QIT_SPEC = (
    ("trace_error", "<=", TRACE_ERROR_MAX),
    ("minimum_eigenvalue", ">=", MIN_EIGENVALUE_MIN),
    ("commuting_control_gap", "<=", COMMUTING_GAP_MAX),
)
MEMORY_SPEC = (
    ("final_best_fidelity", ">=", MEMORY_FIDELITY_MIN),
    ("best_fidelity_improvement", ">=", MEMORY_IMPROVEMENT_MIN),
    ("fixed_point_residual", "<=", FIXED_RESIDUAL_MAX),
)
ORDER_SPEC = (
    ("paired_order_gap", ">=", ORDER_GAP_MIN),
    ("commuting_control_gap", "<=", COMMUTING_GAP_MAX),
)


def python_condition(row: dict[str, Any], spec) -> bool:
    for name, operator, threshold in spec:
        value = row["quantized"][name]
        if operator == ">=" and value < threshold:
            return False
        if operator == "<=" and value > threshold:
            return False
    return True


def z3_term(row: dict[str, Any], spec):
    terms = []
    for name, operator, threshold in spec:
        value = z3.IntVal(row["quantized"][name])
        terms.append(value >= threshold if operator == ">=" else value <= threshold)
    return z3.And(*terms)


def z3_select(rows: list[dict[str, Any]], incoming: list[int], spec):
    solver = z3.Solver()
    variables = []
    for index in incoming:
        variable = z3.Bool(f"admit_{index}")
        solver.add(variable == z3_term(rows[index], spec))
        variables.append((index, variable))
    verdict = solver.check()
    if verdict != z3.sat:
        return str(verdict), []
    model = solver.model()
    selected = [index for index, variable in variables if z3.is_true(model.eval(variable))]
    return "sat", selected


def cvc5_comparison(solver, row, spec):
    terms = []
    for name, operator, threshold in spec:
        value = solver.mkInteger(row["quantized"][name])
        bound = solver.mkInteger(threshold)
        terms.append(
            solver.mkTerm(Kind.GEQ if operator == ">=" else Kind.LEQ, value, bound)
        )
    return solver.mkTerm(Kind.AND, *terms)


def cvc5_select(rows: list[dict[str, Any]], incoming: list[int], spec):
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    variables = []
    boolean = solver.getBooleanSort()
    for index in incoming:
        variable = solver.mkConst(boolean, f"admit_{index}")
        solver.assertFormula(
            solver.mkTerm(Kind.EQUAL, variable, cvc5_comparison(solver, rows[index], spec))
        )
        variables.append((index, variable))
    verdict = solver.checkSat()
    if not verdict.isSat():
        return str(verdict), []
    selected = [
        index
        for index, variable in variables
        if str(solver.getValue(variable)) == "true"
    ]
    return "sat", selected


def z3_exists(rows: list[dict[str, Any]], indices: list[int], spec) -> str:
    solver = z3.Solver()
    solver.add(z3.Or(*[z3_term(rows[index], spec) for index in indices]) if indices else z3.BoolVal(False))
    return str(solver.check())


def cvc5_exists(rows: list[dict[str, Any]], indices: list[int], spec) -> str:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    terms = [cvc5_comparison(solver, rows[index], spec) for index in indices]
    solver.assertFormula(
        solver.mkTerm(Kind.OR, *terms) if terms else solver.mkBoolean(False)
    )
    return str(solver.checkSat())


def run_gate(
    name: str,
    rows: list[dict[str, Any]],
    incoming: list[int],
    spec,
) -> tuple[dict[str, Any], list[int]]:
    python_selected = [index for index in incoming if python_condition(rows[index], spec)]
    z3_verdict, z3_selected = z3_select(rows, incoming, spec)
    cvc5_verdict, cvc5_selected = cvc5_select(rows, incoming, spec)
    agreement = python_selected == z3_selected == cvc5_selected
    selected = python_selected if agreement else []
    selected_ids = [rows[index]["candidate_id"] for index in selected]
    for index in incoming:
        rows[index]["gate_dispositions"][name] = (
            "PASS" if index in selected else "REFUSE"
        )
    return (
        {
            "name": name,
            "incoming": len(incoming),
            "selected": len(selected),
            "held_or_refused": len(incoming) - len(selected),
            "spec": [list(item) for item in spec],
            "python_z3_cvc5_exact_set_agreement": agreement,
            "z3_verdict": z3_verdict,
            "cvc5_verdict": cvc5_verdict,
            "selected_ids_sha256": sha(selected_ids),
            "support_K_before": math.log2(len(incoming)) if incoming else None,
            "support_K_after": math.log2(len(selected)) if selected else None,
        },
        selected,
    )


def neighbor_coordinates(coordinates: tuple[int, ...]):
    mixture, mask_id, angle, sign, bond, dephase, fault = coordinates
    for delta in (-1, 1):
        changed = mixture + delta
        if 0 <= changed < 8:
            yield (changed, mask_id, angle, sign, bond, dephase, fault), "mixture_angle"
    mask = CORRUPTION_MASK_VALUES[mask_id]
    for other_id, other_mask in enumerate(CORRUPTION_MASK_VALUES):
        if (mask ^ other_mask).bit_count() == 1:
            yield (mixture, other_id, angle, sign, bond, dephase, fault), "corruption_bit"
    for delta in (-1, 1):
        changed = angle + delta
        if 0 <= changed < 2:
            yield (mixture, mask_id, changed, sign, bond, dephase, fault), "corruption_angle"
    yield (mixture, mask_id, angle, 1 - sign, bond, dephase, fault), "rotation_sign"
    for delta in (-1, 1):
        changed = bond + delta
        if 0 <= changed < 4:
            yield (mixture, mask_id, angle, sign, changed, dephase, fault), "bond_geometry"
    yield (mixture, mask_id, angle, sign, bond, 1 - dephase, fault), "dephasing"
    for changed in range(3):
        if changed != fault:
            yield (mixture, mask_id, angle, sign, bond, dephase, changed), "density_fault"


def build_map(rows: list[dict[str, Any]], selected: list[int]) -> dict[str, Any]:
    graph = rx.PyGraph(multigraph=False)
    node_indices = graph.add_nodes_from([rows[index]["candidate_id"] for index in selected])
    coordinate_to_graph = {
        tuple(rows[index]["dofs"].values()): node_index
        for index, node_index in zip(selected, node_indices, strict=True)
    }
    graph_to_row = {
        node_index: index for index, node_index in zip(selected, node_indices, strict=True)
    }
    edge_axes = Counter()
    boundary_edges = []
    edge_records: list[tuple[int, int, str]] = []
    for coordinates, node_index in coordinate_to_graph.items():
        for neighbor, axis in neighbor_coordinates(coordinates):
            other = coordinate_to_graph.get(neighbor)
            if other is None or node_index >= other:
                continue
            graph.add_edge(node_index, other, axis)
            edge_records.append((node_index, other, axis))
            edge_axes[axis] += 1
            left_label = int(round(rows[graph_to_row[node_index]]["probes"]["recall_class"]))
            right_label = int(round(rows[graph_to_row[other]]["probes"]["recall_class"]))
            if left_label != right_label:
                boundary_edges.append(
                    {
                        "left": rows[graph_to_row[node_index]]["candidate_id"],
                        "right": rows[graph_to_row[other]]["candidate_id"],
                        "axis": axis,
                        "left_recall_class": left_label,
                        "right_recall_class": right_label,
                    }
                )
    components = [
        sorted(rows[graph_to_row[node]]["candidate_id"] for node in component)
        for component in rx.connected_components(graph)
    ]
    recall_counts = Counter(
        int(round(rows[index]["probes"]["recall_class"])) for index in selected
    )
    total = len(selected)
    probabilities = [count / total for count in recall_counts.values()] if total else []
    shannon = -sum(value * math.log2(value) for value in probabilities if value > 0)

    mixture_ablated = rx.PyGraph(multigraph=False)
    mixture_ablated.add_nodes_from([rows[index]["candidate_id"] for index in selected])
    ablated_boundary_count = 0
    for left, right, axis in edge_records:
        if axis == "mixture_angle":
            continue
        mixture_ablated.add_edge(left, right, axis)
        left_label = int(round(rows[graph_to_row[left]]["probes"]["recall_class"]))
        right_label = int(round(rows[graph_to_row[right]]["probes"]["recall_class"]))
        ablated_boundary_count += int(left_label != right_label)
    mixture_ablated_components = len(rx.connected_components(mixture_ablated))

    wrong = rx.PyGraph(multigraph=False)
    wrong.add_nodes_from([rows[index]["candidate_id"] for index in selected])
    target_edges = graph.num_edges()
    wrong_pairs: set[tuple[int, int]] = set()
    node_count = len(selected)
    for offset in range(1, node_count):
        if len(wrong_pairs) >= target_edges:
            break
        for left in range(node_count):
            right = (left + offset) % node_count
            pair = tuple(sorted((left, right)))
            if left == right or pair in wrong_pairs:
                continue
            wrong_pairs.add(pair)
            if len(wrong_pairs) >= target_edges:
                break
    wrong_boundary_count = 0
    for left, right in sorted(wrong_pairs):
        wrong.add_edge(left, right, "rewired")
        left_label = int(round(rows[graph_to_row[left]]["probes"]["recall_class"]))
        right_label = int(round(rows[graph_to_row[right]]["probes"]["recall_class"]))
        wrong_boundary_count += int(left_label != right_label)
    wrong_components = len(rx.connected_components(wrong))
    wrong_structure_changes = (
        wrong.num_edges() == graph.num_edges()
        and (
            wrong_components != len(components)
            or wrong_boundary_count != len(boundary_edges)
        )
    )
    mixture_axis_load_bearing = (
        bool(boundary_edges)
        and ablated_boundary_count == 0
        and mixture_ablated_components >= len(components)
    )
    return {
        "map_kind": "one_dof_mutation_graph_over_gated_probe_rows",
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "components": len(components),
        "component_sizes": sorted([len(component) for component in components], reverse=True),
        "edge_axes": dict(sorted(edge_axes.items())),
        "recall_region_counts": {str(key): value for key, value in sorted(recall_counts.items())},
        "recall_region_renyi0_bits": math.log2(len(recall_counts)) if recall_counts else 0.0,
        "recall_region_shannon_bits": shannon,
        "boundary_edge_count": len(boundary_edges),
        "boundary_queue_sample": boundary_edges[:20],
        "mixture_axis_ablation": {
            "components": mixture_ablated_components,
            "boundary_edge_count": ablated_boundary_count,
            "removes_cross_recall_boundary": mixture_axis_load_bearing,
        },
        "same_edge_count_wrong_structure": {
            "nodes": wrong.num_nodes(),
            "edges": wrong.num_edges(),
            "components": wrong_components,
            "boundary_edge_count": wrong_boundary_count,
            "changes_map": wrong_structure_changes,
        },
        "map_sha256": sha(
            {
                "nodes": [rows[index]["candidate_id"] for index in selected],
                "edges": sorted(
                    (
                        min(rows[graph_to_row[a]]["candidate_id"], rows[graph_to_row[b]]["candidate_id"]),
                        max(rows[graph_to_row[a]]["candidate_id"], rows[graph_to_row[b]]["candidate_id"]),
                        graph.get_edge_data(a, b),
                    )
                    for a, b in graph.edge_list()
                ),
                "recall_regions": dict(recall_counts),
            }
        ),
        "tool_call": {
            "tool": "rustworkx",
            "qualified_api/function": "rustworkx.PyGraph + connected_components",
            "input_object": "gated finite candidate rows and one-DOF neighbor rules",
            "output_object": "components, boundary edges, recall-region mass",
            "positive_case": "survivor graph is constructed from selected rows",
            "negative/erased_control": "same-edge-count circulant rewiring changes components or recall boundary",
            "boundary_case": "empty survivor set maps to zero nodes",
            "demotion_condition": "rewiring is observationally identical or mixture-axis ablation leaves recall boundary",
            "gates": ["map_integrity", "wrong_structure", "mixture_axis_ablation"],
        },
    }


def sympy_channel_check() -> dict[str, Any]:
    imaginary = sp.I
    cosine = sp.Rational(3, 5)
    sine = sp.Rational(4, 5)
    strength = sp.Rational(1, 3)
    rho = sp.Matrix([[1, 0], [0, 0]])
    ux = sp.Matrix([[cosine, -imaginary * sine], [-imaginary * sine, cosine]])
    uz = sp.diag(cosine - imaginary * sine, cosine + imaginary * sine)

    def unitary_channel(matrix, unitary_matrix):
        return sp.simplify(unitary_matrix * matrix * unitary_matrix.conjugate().T)

    def dephase(matrix):
        diagonal = sp.diag(matrix[0, 0], matrix[1, 1])
        return sp.simplify((1 - strength) * matrix + strength * diagonal)

    x_gap = sp.simplify(
        dephase(unitary_channel(rho, ux)) - unitary_channel(dephase(rho), ux)
    )
    z_gap = sp.simplify(
        dephase(unitary_channel(rho, uz)) - unitary_channel(dephase(rho), uz)
    )
    noncommuting = x_gap != sp.zeros(2)
    commuting = z_gap == sp.zeros(2)
    return {
        "ran": True,
        "sympy_version": sp.__version__,
        "x_channel_nonzero_exact": noncommuting,
        "z_matched_channel_zero_exact": commuting,
        "x_gap": [[str(value) for value in row] for row in x_gap.tolist()],
        "load_bearing": noncommuting and commuting,
        "tool_call": {
            "tool": "sympy",
            "qualified_api/function": "sympy.Matrix exact channel composition",
            "input_object": "rational unitary and dephasing channel",
            "output_object": "exact ordered-channel difference matrices",
            "positive_case": "x rotation and z dephasing do not commute",
            "negative/erased_control": "matched z rotation and z dephasing commute",
            "boundary_case": "identity input density",
            "demotion_condition": "generic gap zero or matched control nonzero",
            "gates": ["order_formula_reference"],
        },
    }


def representative_density(dofs: tuple[int, ...]):
    row = jnp.asarray(dofs, dtype=jnp.int32)
    (
        mixture_id,
        corruption_mask_id,
        angle_id,
        sign_id,
        bond_id,
        dephase_id,
        _density_fault_id,
    ) = row
    initial = initial_spinors(mixture_id, corruption_mask_id, angle_id, sign_id)
    recalled = spinor_recall(initial, bond_id)
    left, right, _ = paired_engine(
        density_of(recalled), DEPHASING[dephase_id], "x"
    )
    return left, right


def qit_crosschecks(representative: tuple[int, ...]) -> dict[str, Any]:
    import dynamiqs as dq
    import qutip as qt
    import qutip_jax

    left, _ = representative_density(representative)
    sample = left[0]
    jax_entropy = float(entropy_bits(sample[None, :, :])[0])
    qobj = qt.Qobj(sample)
    qutip_entropy = float(qt.entropy_vn(qobj, base=2))
    qutip_backend = type(qobj.data).__module__ + "." + type(qobj.data).__name__
    trace_fault = 1.1 * sample
    negative_fault = sample + jnp.asarray(
        [[-2.0, 0.0], [0.0, 2.0]], dtype=jnp.complex128
    )
    trace_fault_qobj = qt.Qobj(trace_fault)
    negative_fault_qobj = qt.Qobj(negative_fault)
    trace_fault_detected = abs(complex(trace_fault_qobj.tr()).real - 1.0) > 1e-3
    negative_fault_detected = min(
        float(value.real) for value in negative_fault_qobj.eigenenergies()
    ) < -1e-3
    qutip_agree = (
        abs(jax_entropy - qutip_entropy) < 1e-9
        and "qutip_jax" in qutip_backend
        and trace_fault_detected
        and negative_fault_detected
    )

    times = jnp.linspace(0.0, 0.5, 6)
    dyn_result = dq.mesolve(
        0.5 * dq.sigmax(),
        [jnp.sqrt(0.2) * dq.sigmaz()],
        dq.asqarray(sample),
        times,
        method=dq.method.Tsit5(rtol=1e-10, atol=1e-12),
    )
    dyn_states = dyn_result.states.to_jax()
    trace_error = float(
        jnp.max(
            jnp.abs(jnp.trace(dyn_states, axis1=-2, axis2=-1) - 1.0)
        )
    )
    minimum_eigenvalue = float(jnp.min(jnp.linalg.eigvalsh(dyn_states)))
    dyn_valid = trace_error < 1e-9 and minimum_eigenvalue > -1e-9
    return {
        "qutip_jax": {
            "ran": True,
            "qutip_version": qt.__version__,
            "backend": qutip_backend,
            "jax_entropy_bits": jax_entropy,
            "qutip_entropy_bits": qutip_entropy,
            "absolute_difference": abs(jax_entropy - qutip_entropy),
            "trace_fault_detected": trace_fault_detected,
            "negative_eigenvalue_fault_detected": negative_fault_detected,
            "load_bearing": qutip_agree,
        },
        "dynamiqs": {
            "ran": True,
            "dynamiqs_version": dq.__version__,
            "trace_error": trace_error,
            "minimum_eigenvalue": minimum_eigenvalue,
            "load_bearing": dyn_valid,
        },
        "all_pass": qutip_agree and dyn_valid,
    }


def write_rows(path: Path, rows: list[dict[str, Any]]) -> str:
    with path.open("wb") as handle:
        for row in rows:
            handle.write(canonical(row) + b"\n")
    return file_sha(path)


def write_json_artifact(path: Path, value: Any) -> str:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return file_sha(path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    output_dir = args.output_dir.resolve()
    if output_dir.exists():
        raise SystemExit("REFUSE_OUTPUT_DIR_EXISTS")
    output_dir.mkdir(parents=True)

    source_path = Path(__file__).resolve()
    source_sha_before = file_sha(source_path)

    light_base = load_light_base(repo)
    dofs = candidate_dofs()
    dof_array = jnp.asarray(dofs, dtype=jnp.int32)
    measured = PROBE_BATCH(dof_array)
    measured.block_until_ready()
    rows = make_probe_rows(dofs, measured)
    probe_rows = [
        {key: value for key, value in row.items() if key != "gate_dispositions"}
        for row in rows
    ]
    probe_rows_path = output_dir / "probe_rows.jsonl"
    probe_rows_sha = write_rows(probe_rows_path, probe_rows)

    all_indices = list(range(len(rows)))
    qit_gate, qit_selected = run_gate("qit_validity", rows, all_indices, QIT_SPEC)
    memory_gate, memory_selected = run_gate(
        "spinor_memory", rows, qit_selected, MEMORY_SPEC
    )
    order_gate, final_selected = run_gate(
        "paired_order", rows, memory_selected, ORDER_SPEC
    )
    gates = [qit_gate, memory_gate, order_gate]
    solver_agreement = all(
        gate["python_z3_cvc5_exact_set_agreement"] for gate in gates
    )

    real_indices = [
        index for index in qit_selected if rows[index]["dofs"]["bond_geometry_id"] < 3
    ]
    erased_indices = [
        index for index in qit_selected if rows[index]["dofs"]["bond_geometry_id"] == 3
    ]
    solver_flip = {
        "polarity": "direct memory claim: real SAT, erased UNSAT",
        "z3_real": z3_exists(rows, real_indices, MEMORY_SPEC),
        "z3_erased": z3_exists(rows, erased_indices, MEMORY_SPEC),
        "cvc5_real": cvc5_exists(rows, real_indices, MEMORY_SPEC),
        "cvc5_erased": cvc5_exists(rows, erased_indices, MEMORY_SPEC),
    }
    solver_flip["load_bearing"] = (
        solver_flip["z3_real"] == "sat"
        and solver_flip["z3_erased"] == "unsat"
        and solver_flip["cvc5_real"] == "sat"
        and solver_flip["cvc5_erased"] == "unsat"
    )

    field_map = build_map(rows, final_selected)
    sympy_check = sympy_channel_check()
    representative = dofs[final_selected[0]] if final_selected else dofs[0]
    qit_check = qit_crosschecks(representative)
    gate_rows = [
        {
            "schema": "constraintbox.manifold-capability-gate-row.v1",
            "candidate_id": row["candidate_id"],
            "gate_dispositions": row["gate_dispositions"],
        }
        for row in rows
    ]
    gate_rows_path = output_dir / "gate_rows.jsonl"
    gate_rows_sha = write_rows(gate_rows_path, gate_rows)
    map_path = output_dir / "map.json"
    map_file_sha = write_json_artifact(map_path, field_map)

    final_rows = [rows[index] for index in final_selected]
    recall_counts = Counter(
        int(round(row["probes"]["recall_class"])) for row in final_rows
    )
    class_switches = sum(
        int(round(row["probes"]["initial_nearest_memory"]))
        != int(round(row["probes"]["recall_class"]))
        for row in final_rows
    )
    minimum_final_fidelity = min(
        (row["probes"]["final_best_fidelity"] for row in final_rows), default=0.0
    )
    maximum_fixed_residual = max(
        (row["probes"]["fixed_point_residual"] for row in final_rows), default=math.inf
    )
    left_entropies = [row["probes"]["mean_left_vn_entropy_bits"] for row in final_rows]
    right_entropies = [row["probes"]["mean_right_vn_entropy_bits"] for row in final_rows]
    no_numpy_direct = not has_direct_numpy_import(Path(__file__))
    controls = {
        "solver_sets_agree": solver_agreement,
        "real_vs_erased_smt_flip": solver_flip["load_bearing"],
        "matched_axis_commuting_control": max(
            row["probes"]["commuting_control_gap"] for row in rows
        )
        < 1e-10,
        "erased_bonds_have_no_memory_survivor": not any(
            rows[index]["dofs"]["bond_geometry_id"] == 3
            for index in memory_selected
        ),
        "same_edge_count_wrong_structure_changes_map": field_map[
            "same_edge_count_wrong_structure"
        ]["changes_map"],
        "mixture_axis_ablation_removes_boundary": field_map[
            "mixture_axis_ablation"
        ]["removes_cross_recall_boundary"],
        "sympy_exact_order_control": sympy_check["load_bearing"],
        "qit_crosschecks": qit_check["all_pass"],
        "one_gradient_base_passed": bool(light_base["one_gradient"]["global_growth_positive"]),
        "no_direct_numpy_in_campaign_source": no_numpy_direct,
        "nonempty_final_survivor_set": bool(final_selected),
        "invalid_density_rows_refused": (
            qit_gate["held_or_refused"] > 0
            and all(rows[index]["dofs"]["density_fault_id"] == 0 for index in qit_selected)
        ),
        "many_to_one_fixed_point_recall_regions": (
            len(recall_counts) == 2
            and min(recall_counts.values(), default=0) > 1
            and minimum_final_fidelity >= MEMORY_FIDELITY_MIN / SCALE
            and maximum_fixed_residual <= FIXED_RESIDUAL_MAX / SCALE
        ),
    }
    source_sha_after = file_sha(source_path)
    controls["executing_source_stable"] = source_sha_before == source_sha_after
    controls["all_pass"] = all(controls.values())

    runtime = {
        "python_version": platform.python_version(),
        "jax_version": jax.__version__,
        "jaxlib_version": jax.lib.__version__,
        "jax_x64_enabled": bool(jax.config.jax_enable_x64),
        "jax_device": str(jax.devices()[0]),
        "z3_version": z3.get_version_string(),
        "cvc5_version": cvc5.__version__,
        "rustworkx_version": getattr(rx, "__version__", "unknown"),
        "sympy_version": sp.__version__,
    }
    source_sha = source_sha_before
    result = {
        "schema": SCHEMA,
        "operation": "finite_spinor_qit_manifold_capability_campaign.v1",
        "operation_id": "mcap-"
        + sha(
            {
                "source_sha256": source_sha,
                "base_result_sha256": light_base["result_sha256"],
                "runtime": runtime,
                "thresholds": {
                    "qit": QIT_SPEC,
                    "memory": MEMORY_SPEC,
                    "order": ORDER_SPEC,
                },
            }
        )[:24],
        "status": "PASS" if controls["all_pass"] else "HOLD",
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source_path": str(source_path),
        "source_sha256": source_sha,
        "source_sha256_after": source_sha_after,
        "invocation": {
            "python_executable_realpath": str(Path(sys.executable).resolve()),
            "cwd": str(Path.cwd().resolve()),
            "repo": str(repo),
            "argv_without_output_dir": ["--repo", str(repo)],
        },
        "runtime": runtime,
        "base_one_gradient": light_base,
        "separation": {
            "spawner": "finite Cartesian product only",
            "probes": "JAX measurements; no dispositions",
            "gates": "Z3/CVC5 measured-value filters",
            "map": "Rustworkx over gated observation rows",
        },
        "spawner": {
            "candidate_count": len(rows),
            "axes": {
                "mixture_angle": 8,
                "corruption_mask": 8,
                "corruption_angle": 2,
                "rotation_sign": 2,
                "bond_geometry": 4,
                "dephasing_strength": 2,
                "density_fault": 3,
            },
            "candidate_ids_sha256": sha([row["candidate_id"] for row in rows]),
        },
        "probe_field": {
            "row_count": len(rows),
            "rows_path": "probe_rows.jsonl",
            "rows_sha256": probe_rows_sha,
            "measured_fields": list(METRIC_NAMES),
            "tool_call": {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(probe_candidate))",
                "input_object": "6,144 finite DOF configurations including two invalid-density controls",
                "output_object": "spinor recall, density validity, entropy, fixed-point and paired-order probes",
                "positive_case": "unlabelled mixtures settle into retained recall classes under non-erased bonds",
                "negative/erased_control": "zero-bond geometry has no memory survivor",
                "boundary_case": "zero corruption and maximum corruption masks are both enumerated",
                "demotion_condition": "solver disagreement, erased-memory survivor, QIT invalidity, or replay drift",
                "gates": ["qit_validity", "spinor_memory", "paired_order"],
            },
        },
        "gate_ratchet": {
            "gate_rows_path": "gate_rows.jsonl",
            "gate_rows_sha256": gate_rows_sha,
            "stages": gates,
            "final_selected": len(final_selected),
            "final_selected_ids_sha256": sha(
                [rows[index]["candidate_id"] for index in final_selected]
            ),
            "solver_flip": solver_flip,
            "note": "gate support contraction is search-space filtering, not the entropy/time gradient",
            "threshold_provenance": (
                "exploratory source constants selected before this 6,144-row run; "
                "not independently calibrated or universal"
            ),
        },
        "map": field_map,
        "map_artifact": {
            "path": "map.json",
            "file_sha256": map_file_sha,
            "semantic_sha256": field_map["map_sha256"],
        },
        "nested_readouts": {
            "support_capacity_by_gate": [
                {
                    "stage": gate["name"],
                    "K_before": gate["support_K_before"],
                    "K_after": gate["support_K_after"],
                }
                for gate in gates
            ],
            "recall_region_mass": {str(key): value for key, value in sorted(recall_counts.items())},
            "recall_region_renyi0_bits": field_map["recall_region_renyi0_bits"],
            "recall_region_shannon_bits": field_map["recall_region_shannon_bits"],
            "recall_region_evidence": {
                "initial_to_final_nearest_class_switches": class_switches,
                "minimum_final_fidelity": minimum_final_fidelity,
                "maximum_fixed_point_residual": maximum_fixed_residual,
                "ceiling": (
                    "many initial configurations contract toward two fixed prototypes; "
                    "no observed nearest-class switching, so attractor-basin admission is blocked"
                ),
            },
            "mean_left_vn_entropy_bits": (
                sum(left_entropies) / len(left_entropies) if left_entropies else None
            ),
            "mean_right_vn_entropy_bits": (
                sum(right_entropies) / len(right_entropies) if right_entropies else None
            ),
            "summed_into_one_entropy": False,
        },
        "sympy_order_reference": sympy_check,
        "qit_engine_crosschecks": qit_check,
        "controls": controls,
        "claim_ceiling": (
            "local finite functionality only: wide spinor-memory/QIT probes, paired density dynamics, "
            "SMT-gated survivor map, and finite fixed-point recall regions; no admitted attractor basin, physical spacetime, "
            "Axis0, chirality, final manifold, quantum advantage, or CB admission"
        ),
        "blocked_consumers": [
            "CB Light public CLI/SQLite",
            "manifold completion claims",
            "physical/QIT truth claims",
            "automatic Heavy promotion",
        ],
    }
    result["result_sha256"] = sha(result)
    result_path = output_dir / "result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
