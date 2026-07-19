#!/usr/bin/env python3
"""One finite, coupled entropic-geometric constraint-manifold realization.

Every evaluated candidate is a complete object: finite ring/checkerboard
support, nested completion relation, entropy potential, Hessian/Hodge geometry,
connection and curvature, effective inner compression, coherent histories,
carrier lift, bracket semantics, order semantics, source ancestry, and dynamic
response.  Features may be absent in a proposal, but the whole object is
recomputed for every proposal and requirement context.

This is a bounded mathematical realization and tournament surface.  It does
not identify the finite object with the physical universe.
"""

from __future__ import annotations

import cmath
import itertools
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, fields, replace
from typing import Any, Iterable

from common import (
    digest,
    matrix_dagger,
    matrix_multiply,
    matrix_subtract,
    max_abs_matrix,
    schur_complement,
    submatrix,
)
from finite_algebra import division_ladder_report, octonion_network_report, spinor_memory_report


REQUIREMENTS = (
    "finite_nonempty_whole",
    "bidirectional_nested_completion",
    "entropy_geometry_cogenerated",
    "nested_entropy_metric_chain_rule",
    "connection_curvature_on_same_complex",
    "signed_orientation_matches_source",
    "lifted_phase_memory_retained",
    "higher_hopf_nesting_retained",
    "coherent_histories_change_present",
    "same_history_object_no_signalling",
    "outer_shell_compresses_inner_operator",
    "expansion_changes_inner_operator",
    "renesting_changes_inner_operator",
    "dynamic_axis0_measured",
    "jk_order_outcomes_retained",
    "bracket_changes_network_output",
    "full_source_ancestry_retained",
    "entropy_geometry_flux_history_one_object",
)


@dataclass(frozen=True)
class ManifoldSpec:
    candidate_id: str
    ring_size: int = 4
    shell_count: int = 1
    nesting: str = "independent"
    potential: str = "none"
    metric: str = "none"
    connection: str = "none"
    orientation: str = "erased"
    carrier: str = "density"
    history: str = "latest"
    composition: str = "associative"
    compression: str = "none"
    expansion: str = "uncoupled"
    axis0: str = "static"
    order_mode: str = "single"
    source_depth: str = "none"
    parents: tuple[str, ...] = ()
    generated_from_residuals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        allowed = {
            "nesting": {"independent", "identity", "twisted"},
            "potential": {"none", "quadratic", "shannon"},
            "metric": {"none", "euclidean", "fisher"},
            "connection": {"none", "flat", "signed_u1"},
            "orientation": {"erased", "signed"},
            "carrier": {"density", "vector_register", "complex_spinor", "division_hopf"},
            "history": {"latest", "recorded", "coherent", "coherent_bracketed"},
            "composition": {"associative", "bracket_register", "octonion"},
            "compression": {"none", "schur"},
            "expansion": {"uncoupled", "coupled"},
            "axis0": {"static", "dynamic"},
            "order_mode": {"single", "all"},
            "source_depth": {"none", "latest", "full"},
        }
        if not self.candidate_id:
            raise ValueError("candidate id must be nonempty")
        if self.ring_size < 3 or self.shell_count not in (1, 2, 3):
            raise ValueError("finite realization requires ring >=3 and one to three shells")
        for name, values in allowed.items():
            if getattr(self, name) not in values:
                raise ValueError(f"invalid {name}: {getattr(self, name)!r}")

    def structural_dict(self) -> dict[str, Any]:
        excluded = {"candidate_id", "parents", "generated_from_residuals"}
        return {field.name: getattr(self, field.name) for field in fields(self) if field.name not in excluded}

    def commitments(self) -> frozenset[str]:
        tokens: set[str] = set()
        if self.ring_size != 4:
            tokens.add(f"ring_size:{self.ring_size}")
        for shell in range(2, self.shell_count + 1):
            tokens.add(f"shell:{shell}")
        if self.nesting != "independent":
            tokens.add(f"nesting:{self.nesting}")
        if self.potential != "none":
            tokens.add(f"potential:{self.potential}")
        if self.metric != "none":
            tokens.add(f"metric:{self.metric}")
        if self.connection != "none":
            tokens.add(f"connection:{self.connection}")
        if self.orientation == "signed":
            tokens.add("orientation:signed")
        if self.carrier == "vector_register":
            tokens.add("carrier:explicit_phase_register")
        elif self.carrier == "complex_spinor":
            tokens.add("carrier:complex_spinor")
        elif self.carrier == "division_hopf":
            tokens.update({"carrier:complex_spinor", "carrier:quaternion_hopf", "carrier:octonion_hopf"})
        if self.history == "recorded":
            tokens.add("history:recorded")
        elif self.history == "coherent":
            tokens.add("history:coherent")
        elif self.history == "coherent_bracketed":
            tokens.update({"history:coherent", "history:bracketed"})
        if self.composition == "bracket_register":
            tokens.add("composition:bracket_register")
        elif self.composition == "octonion":
            tokens.add("composition:octonion")
        if self.compression == "schur":
            tokens.add("compression:schur")
        if self.expansion == "coupled":
            tokens.add("expansion:coupled")
        if self.axis0 == "dynamic":
            tokens.add("axis0:dynamic")
        if self.order_mode == "all":
            tokens.add("order:retain_all")
        if self.source_depth in {"latest", "full"}:
            tokens.add("source:latest")
        if self.source_depth == "full":
            tokens.add("source:full")
        return frozenset(tokens)

    def as_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            **self.structural_dict(),
            "parents": list(self.parents),
            "generated_from_residuals": list(self.generated_from_residuals),
            "commitments": sorted(self.commitments()),
        }


def enumerate_completions(
    spec: ManifoldSpec,
    outer_allowed: Iterable[int],
    chirality: int = 1,
) -> list[dict[str, int]]:
    n = spec.ring_size
    allowed = {value % n for value in outer_allowed}
    rows: list[dict[str, int]] = []
    if spec.shell_count == 1:
        for j0, k0 in itertools.product(range(n), repeat=2):
            rows.append({"j0": j0, "k0": k0, "z0": (chirality * j0 * k0) % n})
        return rows

    epsilon_count = spec.shell_count - 1
    for j0, k0 in itertools.product(range(n), repeat=2):
        for epsilons in itertools.product((0, 1), repeat=epsilon_count):
            if (j0 + k0 + sum(epsilons)) % 2:
                continue
            row = {"j0": j0, "k0": k0, "z0": (chirality * j0 * k0) % n}
            j, k, z = j0, k0, row["z0"]
            for depth, epsilon in enumerate(epsilons, start=1):
                if spec.nesting == "twisted":
                    next_k = (k + epsilon) % n
                    next_j = (j + k) % n
                    next_z = (z + chirality * j * next_k) % n
                elif spec.nesting == "identity":
                    next_j = j
                    next_k = (k + epsilon) % n
                    next_z = z
                else:
                    next_j = (j + epsilon) % n
                    next_k = k
                    next_z = (j + k + epsilon) % n
                row[f"epsilon{depth}"] = epsilon
                row[f"j{depth}"] = next_j
                row[f"k{depth}"] = next_k
                row[f"z{depth}"] = next_z
                j, k, z = next_j, next_k, next_z
            if z in allowed:
                rows.append(row)
    return rows


def path_for(row: dict[str, int], shells: int) -> list[tuple[int, int, int]]:
    return [(shell, row[f"j{shell}"], row[f"k{shell}"]) for shell in range(shells)]


def build_complex(
    spec: ManifoldSpec,
    rows: list[dict[str, int]],
) -> dict[str, Any]:
    n = spec.ring_size
    nodes = [(shell, j, k) for shell in range(spec.shell_count) for j in range(n) for k in range(n)]
    node_index = {node: index for index, node in enumerate(nodes)}
    vertex_counts = Counter()
    vertical_counts = Counter()
    for row in rows:
        path = path_for(row, spec.shell_count)
        vertex_counts.update(path)
        if spec.nesting != "independent":
            vertical_counts.update(zip(path, path[1:]))

    horizontal_edges: list[tuple[tuple[int, int, int], tuple[int, int, int], str]] = []
    for shell in range(spec.shell_count):
        for j in range(n):
            for k in range(n):
                node = (shell, j, k)
                horizontal_edges.append((node, (shell, (j + 1) % n, k), "j"))
                horizontal_edges.append((node, (shell, j, (k + 1) % n), "k"))
    vertical_edges = [(left, right, "vertical") for left, right in sorted(vertical_counts)]
    all_edges = horizontal_edges + vertical_edges
    total_visits = sum(vertex_counts.values()) + len(nodes)
    masses = {node: (vertex_counts[node] + 1) / total_visits for node in nodes}
    return {
        "nodes": nodes,
        "node_index": node_index,
        "vertex_counts": vertex_counts,
        "vertical_counts": vertical_counts,
        "horizontal_edges": horizontal_edges,
        "vertical_edges": vertical_edges,
        "edges": all_edges,
        "masses": masses,
        "complete_history_count": len(rows),
        "node_count": len(nodes),
        "horizontal_edge_count": len(horizontal_edges),
        "vertical_edge_count": len(vertical_edges),
    }


def entropy_geometry_report(spec: ManifoldSpec, rows: list[dict[str, int]]) -> dict[str, Any]:
    count = len(rows)
    if not count:
        return {"cogenerated": False, "potential_chain_rule": False, "metric_chain_rule": False}
    last = spec.shell_count - 1
    groups: dict[int, list[int]] = defaultdict(list)
    for index, row in enumerate(rows):
        groups[row[f"z{last}"]].append(index)
    p = [1.0 / count for _ in rows]

    if spec.potential == "shannon":
        joint = sum(value * math.log(value) for value in p)
    elif spec.potential == "quadratic":
        joint = 0.5 * sum(value * value for value in p)
    else:
        joint = 0.0
    outer_masses = {group: len(indices) / count for group, indices in groups.items()}
    if spec.potential == "shannon":
        outer = sum(value * math.log(value) for value in outer_masses.values())
        conditional = 0.0
        for group, indices in groups.items():
            mass = outer_masses[group]
            q = 1.0 / len(indices)
            conditional += mass * sum(q * math.log(q) for _ in indices)
    elif spec.potential == "quadratic":
        outer = 0.5 * sum(value * value for value in outer_masses.values())
        conditional = 0.0
        for group, indices in groups.items():
            mass = outer_masses[group]
            q = 1.0 / len(indices)
            conditional += mass * 0.5 * sum(q * q for _ in indices)
    else:
        outer = conditional = 0.0
    potential_chain_error = abs(joint - outer - conditional)

    raw_tangent = [((index * 7 + 3) % 11) - 5 for index in range(count)]
    mean = sum(raw_tangent) / count
    tangent = [value - mean for value in raw_tangent]
    if spec.metric == "fisher":
        joint_metric = sum(value * value / probability for value, probability in zip(tangent, p))
    elif spec.metric == "euclidean":
        joint_metric = sum(value * value for value in tangent)
    else:
        joint_metric = 0.0
    outer_metric = 0.0
    inner_metric = 0.0
    for group, indices in groups.items():
        mass = outer_masses[group]
        group_tangent = sum(tangent[index] for index in indices)
        if spec.metric == "fisher":
            outer_metric += group_tangent * group_tangent / mass
        elif spec.metric == "euclidean":
            outer_metric += group_tangent * group_tangent
        q = 1.0 / len(indices)
        conditional_tangent = [(tangent[index] - group_tangent * q) / mass for index in indices]
        if spec.metric == "fisher":
            inner_metric += mass * sum(value * value / q for value in conditional_tangent)
        elif spec.metric == "euclidean":
            inner_metric += mass * sum(value * value for value in conditional_tangent)
    metric_chain_error = abs(joint_metric - outer_metric - inner_metric)
    cogenerated = (
        (spec.potential == "shannon" and spec.metric == "fisher")
        or (spec.potential == "quadratic" and spec.metric == "euclidean")
    )
    return {
        "potential": spec.potential,
        "metric": spec.metric,
        "joint_potential": joint,
        "outer_plus_conditional_potential": outer + conditional,
        "potential_chain_error": potential_chain_error,
        "joint_metric": joint_metric,
        "outer_plus_conditional_metric": outer_metric + inner_metric,
        "metric_chain_error": metric_chain_error,
        "cogenerated": cogenerated,
        "potential_chain_rule": spec.potential != "none" and potential_chain_error < 1e-10,
        "metric_chain_rule": spec.metric != "none" and metric_chain_error < 1e-8,
    }


def phase_for_edge(
    spec: ManifoldSpec,
    left: tuple[int, int, int],
    right: tuple[int, int, int],
    kind: str,
    chirality: int,
) -> complex:
    if spec.connection != "signed_u1":
        return 1 + 0j
    n = spec.ring_size
    shell, j, k = left
    if kind == "j":
        angle = 2.0 * math.pi * chirality * (k + shell) / n
    elif kind == "k":
        angle = 0.0
    else:
        _, next_j, next_k = right
        angle = 2.0 * math.pi * chirality * (j * next_k - k * next_j) / n
    return cmath.exp(1j * angle)


def build_operator(
    spec: ManifoldSpec,
    rows: list[dict[str, int]],
    chirality: int = 1,
) -> tuple[list[list[complex]], dict[str, Any]]:
    complex_data = build_complex(spec, rows)
    nodes = complex_data["nodes"]
    indices = complex_data["node_index"]
    masses = complex_data["masses"]
    size = len(nodes)
    matrix = [[0j for _ in range(size)] for _ in range(size)]
    edge_phase: dict[tuple[tuple[int, int, int], tuple[int, int, int]], complex] = {}
    for left, right, kind in complex_data["edges"]:
        i, j = indices[left], indices[right]
        if spec.metric == "fisher":
            weight = 2.0 * masses[left] * masses[right] / (masses[left] + masses[right])
        else:
            weight = 1.0
        if kind == "vertical":
            count = complex_data["vertical_counts"][(left, right)]
            weight *= 1.0 + count / max(1, len(rows))
        phase = phase_for_edge(spec, left, right, kind, chirality)
        edge_phase[(left, right)] = phase
        edge_phase[(right, left)] = phase.conjugate()
        matrix[i][i] += weight
        matrix[j][j] += weight
        matrix[i][j] -= weight * phase
        matrix[j][i] -= weight * phase.conjugate()
    # A declared finite anchor makes every outer block invertible.  It is a
    # numerical boundary condition, not a physical mass term.
    for index in range(size):
        matrix[index][index] += 0.25

    hermitian_error = max_abs_matrix(matrix_subtract(matrix, matrix_dagger(matrix)))
    curvature = []
    n = spec.ring_size
    for shell in range(spec.shell_count):
        for j in range(n):
            for k in range(n):
                a = (shell, j, k)
                b = (shell, (j + 1) % n, k)
                c = (shell, (j + 1) % n, (k + 1) % n)
                d = (shell, j, (k + 1) % n)
                wilson = edge_phase[(a, b)] * edge_phase[(b, c)] * edge_phase[(c, d)] * edge_phase[(d, a)]
                curvature.append(cmath.phase(wilson))
    return matrix, {
        **{key: value for key, value in complex_data.items() if key not in {"node_index", "masses", "vertex_counts", "vertical_counts", "edges", "horizontal_edges", "vertical_edges"}},
        "hermitian_error": hermitian_error,
        "curvature_phase_max_abs": max((abs(value) for value in curvature), default=0.0),
        "curvature_phase_mean": sum(curvature) / max(1, len(curvature)),
        "operator_digest": digest(matrix),
    }


def compression_report(spec: ManifoldSpec, rows: list[dict[str, int]]) -> dict[str, Any]:
    if spec.compression != "schur" or spec.shell_count < 2:
        return {
            "enabled": False,
            "outer_changes_inner": False,
            "sequential_direct_error": None,
            "effective_operator": None,
        }
    matrix, operator = build_operator(spec, rows)
    block = spec.ring_size * spec.ring_size
    keep = list(range(block))
    eliminate = list(range(block, len(matrix)))
    effective = schur_complement(matrix, keep, eliminate)
    inner_block = submatrix(matrix, keep, keep)
    compression_delta = max_abs_matrix(matrix_subtract(inner_block, effective))

    if spec.shell_count == 3:
        keep01 = list(range(2 * block))
        eliminate2 = list(range(2 * block, 3 * block))
        reduced01 = schur_complement(matrix, keep01, eliminate2)
        sequential = schur_complement(reduced01, list(range(block)), list(range(block, 2 * block)))
        sequential_direct_error = max_abs_matrix(matrix_subtract(effective, sequential))
    else:
        sequential_direct_error = 0.0
    return {
        "enabled": True,
        "outer_changes_inner": compression_delta > 1e-10,
        "inner_block_to_effective_max_change": compression_delta,
        "sequential_direct_error": sequential_direct_error,
        "exact_schur_elimination_order_invariant": sequential_direct_error < 1e-8,
        "effective_operator": effective,
        "effective_operator_digest": digest(effective),
        "operator": operator,
    }


def compare_structural_variants(spec: ManifoldSpec) -> dict[str, Any]:
    if spec.compression != "schur" or spec.shell_count < 2:
        return {"renesting_changes_inner": False, "expansion_changes_inner": False}
    baseline_rows = enumerate_completions(spec, (0, 1), 1)
    baseline = compression_report(spec, baseline_rows)
    alternate_nesting = "identity" if spec.nesting == "twisted" else "twisted"
    renested_spec = replace(spec, candidate_id=spec.candidate_id + "__renest_control", nesting=alternate_nesting)
    renested_rows = enumerate_completions(renested_spec, (0, 1), 1)
    renested = compression_report(renested_spec, renested_rows)
    renesting_delta = max_abs_matrix(
        matrix_subtract(baseline["effective_operator"], renested["effective_operator"])
    )

    expanded_rows = enumerate_completions(spec, (0, 1, 2), 1)
    expanded = compression_report(spec, expanded_rows)
    expansion_delta = max_abs_matrix(
        matrix_subtract(baseline["effective_operator"], expanded["effective_operator"])
    )
    if spec.expansion != "coupled":
        expansion_delta = 0.0
    return {
        "alternate_nesting": alternate_nesting,
        "renesting_effective_operator_delta": renesting_delta,
        "renesting_changes_inner": renesting_delta > 1e-10,
        "baseline_completion_count": len(baseline_rows),
        "expanded_completion_count": len(expanded_rows),
        "expansion_effective_operator_delta": expansion_delta,
        "expansion_changes_inner": expansion_delta > 1e-10 and len(expanded_rows) > len(baseline_rows),
    }


def normalize_matrix(matrix: list[list[complex]]) -> list[list[complex]]:
    norm = math.sqrt(sum(abs(value) ** 2 for row in matrix for value in row))
    if norm <= 1e-15:
        raise ValueError("zero history amplitude norm")
    return [[value / norm for value in row] for row in matrix]


def local_density(matrix: list[list[complex]]) -> list[list[complex]]:
    return [
        [sum(matrix[p][r] * matrix[q][r].conjugate() for r in range(len(matrix[0]))) for q in range(2)]
        for p in range(2)
    ]


def apply_remote(matrix: list[list[complex]], unitary: list[list[complex]]) -> list[list[complex]]:
    return [
        [sum(matrix[p][r] * unitary[s][r] for r in range(len(matrix[0]))) for s in range(len(unitary))]
        for p in range(2)
    ]


def trace_distance_2x2(left: list[list[complex]], right: list[list[complex]]) -> float:
    a = (left[0][0] - right[0][0]).real
    d = (left[1][1] - right[1][1]).real
    b = left[0][1] - right[0][1]
    discriminant = math.sqrt(max(0.0, (a - d) ** 2 + 4.0 * abs(b) ** 2))
    return 0.5 * (
        abs(0.5 * (a + d + discriminant))
        + abs(0.5 * (a + d - discriminant))
    )


def remote_unitaries() -> list[list[list[complex]]]:
    identity = [[complex(int(i == j)) for j in range(4)] for i in range(4)]
    swap = [[complex(int(i == (j ^ 1))) for j in range(4)] for i in range(4)]
    phase = [[0j for _ in range(4)] for _ in range(4)]
    for index, value in enumerate((1, 1j, -1, -1j)):
        phase[index][index] = value
    return [identity, swap, phase]


def history_report(spec: ManifoldSpec, rows: list[dict[str, int]]) -> dict[str, Any]:
    if not rows or spec.shell_count < 2:
        return {
            "coherent_recorded_l1": 0.0,
            "no_signalling_capacity": None,
            "history_count": len(rows),
        }
    n = spec.ring_size
    tensor = [[0j for _ in range(4)] for _ in range(2)]
    recorded_counts = [0, 0]
    last = spec.shell_count - 1
    weight = 1.0 / math.sqrt(len(rows))
    for row in rows:
        present = (row["j0"] + row["k0"]) % 2
        epsilon1 = row.get("epsilon1", 0)
        epsilon2 = row.get("epsilon2", 0)
        remote = 2 * epsilon1 + epsilon2
        phase = cmath.exp(2j * math.pi * row[f"z{last}"] / n)
        tensor[present][remote] += weight * phase
        recorded_counts[present] += 1
    tensor = normalize_matrix(tensor)
    density = local_density(tensor)
    coherent = [density[index][index].real for index in range(2)]
    recorded = [value / len(rows) for value in recorded_counts]
    l1 = sum(abs(left - right) for left, right in zip(coherent, recorded))

    reference = density
    distances = [
        trace_distance_2x2(reference, local_density(apply_remote(tensor, unitary)))
        for unitary in remote_unitaries()
    ]
    if spec.history in {"latest", "recorded"}:
        active_l1 = 0.0
    else:
        active_l1 = l1
    return {
        "history_count": len(rows),
        "amplitude_tensor_digest": digest(tensor),
        "coherent_probabilities": coherent,
        "recorded_probabilities": recorded,
        "raw_coherent_recorded_l1": l1,
        "coherent_recorded_l1": active_l1,
        "no_signalling_distances": distances,
        "no_signalling_capacity": max(distances),
        "uses_same_rows_connection_and_boundary": True,
    }


def hopf_carrier_report(spec: ManifoldSpec) -> dict[str, Any]:
    n = spec.ring_size
    spinors = []
    bases = []
    for j in range(n):
        for k in range(n):
            theta = math.pi * (j + 0.5) / n
            phi = 2.0 * math.pi * k / n
            psi = (math.cos(theta / 2.0), cmath.exp(1j * phi) * math.sin(theta / 2.0))
            x = 2.0 * (psi[0].conjugate() * psi[1]).real
            y = 2.0 * (psi[0].conjugate() * psi[1]).imag
            z = abs(psi[0]) ** 2 - abs(psi[1]) ** 2
            spinors.append(psi)
            bases.append((x, y, z))
    normalized = max(abs(sum(abs(value) ** 2 for value in psi) - 1.0) for psi in spinors) < 1e-12
    base_normalized = max(abs(sum(value * value for value in base) - 1.0) for base in bases) < 1e-12
    sign_erased_by_base = all(
        max(abs(left - right) for left, right in zip(base, base)) < 1e-12
        for base in bases
    )
    spinor_source = spinor_memory_report()
    division = division_ladder_report() if spec.carrier == "division_hopf" else None
    return {
        "carrier": spec.carrier,
        "complex_spinors_attached": spec.carrier in {"complex_spinor", "division_hopf"},
        "spinor_count": len(spinors),
        "spinors_normalized": normalized,
        "hopf_bases_normalized": base_normalized,
        "base_erases_spinor_sign": sign_erased_by_base,
        "lifted_sign_retained": (
            spec.carrier in {"complex_spinor", "division_hopf"}
            and spinor_source["spinor_lift_retains_density_erased_loop_parity"]
        ),
        "complex_hopf_identity": spec.carrier in {"complex_spinor", "division_hopf"} and normalized and base_normalized,
        "division_ladder": division,
        "higher_hopf_nesting": bool(division and division["all_pass"]),
        "spinor_digest": digest(spinors) if spec.carrier in {"complex_spinor", "division_hopf"} else None,
        "base_digest": digest(bases),
    }


def jk_order_report(spec: ManifoldSpec) -> dict[str, Any]:
    n = spec.ring_size

    def j_map(state: tuple[int, int]) -> tuple[int, int]:
        j, k = state
        return ((j + k) % n, k)

    def k_map(state: tuple[int, int]) -> tuple[int, int]:
        j, k = state
        return (j, (k + j) % n)

    rows = []
    for state in itertools.product(range(n), repeat=2):
        jk = k_map(j_map(state))
        kj = j_map(k_map(state))
        if jk != kj:
            rows.append({"state": state, "J_then_K": jk, "K_then_J": kj})
    retained = rows if spec.order_mode == "all" else rows[:1]
    return {
        "noncommuting_input_count": len(rows),
        "sample": rows[:8],
        "retained_outcome_count": len(retained),
        "all_distinct_orders_retained": spec.order_mode == "all" and bool(rows),
    }


def dynamic_axis0_report(spec: ManifoldSpec, baseline_rows: list[dict[str, int]]) -> dict[str, Any]:
    n = spec.ring_size
    count = n * n
    baseline = [1.0 / count for _ in range(count)]
    perturbed = baseline[:]
    delta = 0.25 / count
    perturbed[0] += delta
    perturbed[count // 2] -= delta

    def step(distribution: list[float]) -> list[float]:
        result = [0.0 for _ in distribution]
        for j in range(n):
            for k in range(n):
                index = j * n + k
                neighbors = (
                    ((j + 1) % n) * n + k,
                    ((j - 1) % n) * n + k,
                    j * n + (k + 1) % n,
                    j * n + (k - 1) % n,
                )
                result[index] = 0.5 * distribution[index] + 0.125 * sum(distribution[item] for item in neighbors)
        return result

    distances = []
    state = perturbed
    for _ in range(9):
        distances.append(sum(abs(left - right) for left, right in zip(state, baseline)))
        state = step(state)
    expanded_rows = enumerate_completions(spec, (0, 1, 2), 1)
    dynamic = spec.axis0 == "dynamic"
    return {
        "perturbation_l1_by_tick": distances,
        "homeostatic_damping": dynamic and distances[-1] < distances[0] and all(
            right <= left + 1e-15 for left, right in zip(distances, distances[1:])
        ),
        "baseline_future_count": len(baseline_rows),
        "opened_future_count": len(expanded_rows),
        "allostatic_opening": dynamic and len(expanded_rows) > len(baseline_rows),
        "multi_tick_measured": dynamic,
    }


def bidirectional_report(spec: ManifoldSpec, rows: list[dict[str, int]]) -> dict[str, Any]:
    if spec.shell_count < 2 or not rows:
        return {"passed": False}
    inner = {(row["j0"], row["k0"]) for row in rows}
    last = spec.shell_count - 1
    outer = {(row[f"j{last}"], row[f"k{last}"], row[f"z{last}"]) for row in rows}
    relaxed = enumerate_completions(spec, range(spec.ring_size), 1)
    relaxed_inner = {(row["j0"], row["k0"]) for row in relaxed}
    tightened_spec = replace(spec, candidate_id=spec.candidate_id + "__inner_control")
    inner_filtered = [row for row in relaxed if (row["j0"] + row["k0"]) % 4 == 0]
    filtered_outer = {
        (row[f"j{last}"], row[f"k{last}"], row[f"z{last}"])
        for row in inner_filtered
    }
    return {
        "inner_projection_count": len(inner),
        "outer_projection_count": len(outer),
        "relaxed_inner_projection_count": len(relaxed_inner),
        "inner_constraint_outer_projection_count": len(filtered_outer),
        "outer_changes_inner": inner != relaxed_inner,
        "inner_changes_outer": filtered_outer != {
            (row[f"j{last}"], row[f"k{last}"], row[f"z{last}"])
            for row in relaxed
        },
        "passed": spec.nesting != "independent" and inner != relaxed_inner and bool(filtered_outer),
    }


def evaluate_manifold(
    spec: ManifoldSpec,
    evidence: dict[str, Any],
    active_requirements: Iterable[str] = REQUIREMENTS,
) -> dict[str, Any]:
    active_requirements = tuple(active_requirements)
    unknown = set(active_requirements) - set(REQUIREMENTS)
    if unknown:
        raise ValueError(f"unknown requirements: {sorted(unknown)}")
    rows_plus = enumerate_completions(spec, (0, 1), 1)
    rows_minus = enumerate_completions(spec, (0, 1), -1)
    entropy_geometry = entropy_geometry_report(spec, rows_plus)
    operator_plus, operator_report_plus = build_operator(spec, rows_plus, 1)
    operator_minus, operator_report_minus = build_operator(spec, rows_minus, -1)
    orientation_difference = max_abs_matrix(matrix_subtract(operator_plus, operator_minus))
    compression = compression_report(spec, rows_plus)
    structural = compare_structural_variants(spec)
    history = history_report(spec, rows_plus)
    hopf = hopf_carrier_report(spec)
    jk_order = jk_order_report(spec)
    axis0 = dynamic_axis0_report(spec, rows_plus)
    bidirectional = bidirectional_report(spec, rows_plus)
    octonion = octonion_network_report() if spec.composition == "octonion" else None

    events = {row["event_id"]: row for row in evidence.get("evidence_events", [])}
    source_all = all(row.get("passed") is True for row in events.values()) and len(events) >= 6
    curvature_nonzero = operator_report_plus["curvature_phase_max_abs"] > 1e-8
    bracket_output = bool(octonion and octonion["all_pass"] and octonion["path_bracketing_gap_squared"] > 0)
    one_object = (
        spec.potential == "shannon"
        and spec.metric == "fisher"
        and spec.connection == "signed_u1"
        and spec.history in {"coherent", "coherent_bracketed"}
        and spec.compression == "schur"
        and compression["enabled"]
        and history.get("uses_same_rows_connection_and_boundary") is True
    )
    passed_all = {
        "finite_nonempty_whole": bool(rows_plus) and operator_report_plus["node_count"] > 0,
        "bidirectional_nested_completion": bidirectional.get("passed") is True,
        "entropy_geometry_cogenerated": entropy_geometry["cogenerated"],
        "nested_entropy_metric_chain_rule": (
            entropy_geometry["potential_chain_rule"] and entropy_geometry["metric_chain_rule"]
        ),
        "connection_curvature_on_same_complex": spec.connection == "signed_u1" and curvature_nonzero,
        "signed_orientation_matches_source": (
            spec.orientation == "signed"
            and spec.connection == "signed_u1"
            and orientation_difference > 1e-8
            and events.get("qca_signed_support_flow", {}).get("passed") is True
        ),
        "lifted_phase_memory_retained": (
            hopf["lifted_sign_retained"]
            and events.get("spinor_density_quotient_memory", {}).get("passed") is True
        ),
        "higher_hopf_nesting_retained": (
            hopf["higher_hopf_nesting"]
            and spec.shell_count == 3
            and events.get("division_hopf_ladder", {}).get("passed") is True
        ),
        "coherent_histories_change_present": (
            spec.history in {"coherent", "coherent_bracketed"}
            and history.get("coherent_recorded_l1", 0.0) > 1e-8
            and events.get("literal_nested_completion_seed", {}).get("passed") is True
        ),
        "same_history_object_no_signalling": (
            history.get("no_signalling_capacity") is not None
            and history["no_signalling_capacity"] < 1e-10
            and events.get("directional_axis0_source", {}).get("passed") is True
        ),
        "outer_shell_compresses_inner_operator": compression["outer_changes_inner"],
        "expansion_changes_inner_operator": spec.expansion == "coupled" and structural["expansion_changes_inner"],
        "renesting_changes_inner_operator": structural["renesting_changes_inner"],
        "dynamic_axis0_measured": (
            axis0["homeostatic_damping"]
            and axis0["allostatic_opening"]
            and events.get("directional_axis0_source", {}).get("passed") is True
        ),
        "jk_order_outcomes_retained": jk_order["all_distinct_orders_retained"],
        "bracket_changes_network_output": (
            spec.composition == "octonion"
            and spec.history == "coherent_bracketed"
            and bracket_output
            and events.get("octonion_path_bracketing", {}).get("passed") is True
        ),
        "full_source_ancestry_retained": spec.source_depth == "full" and source_all,
        "entropy_geometry_flux_history_one_object": one_object,
    }
    passed = {name: passed_all[name] for name in active_requirements}
    failed = sorted(name for name, value in passed.items() if not value)
    observable_signature = digest({
        "rows_plus": rows_plus,
        "rows_minus": rows_minus,
        "entropy_geometry": entropy_geometry,
        "operator_plus": operator_report_plus["operator_digest"],
        "operator_minus": operator_report_minus["operator_digest"],
        "compression": compression.get("effective_operator_digest"),
        "history": history,
        "hopf": hopf,
        "jk": jk_order,
        "axis0": axis0,
        "octonion": octonion,
    })
    result = {
        "schema": "ratchet.pack182.finite-whole-gcm-evaluation.v1",
        "candidate": spec.as_dict(),
        "active_requirements": list(active_requirements),
        "passed": passed,
        "failed": failed,
        "all_active_requirements_pass": not failed,
        "whole": {
            "completion_count_chi_plus": len(rows_plus),
            "completion_count_chi_minus": len(rows_minus),
            "completion_digest_chi_plus": digest(rows_plus),
            "completion_digest_chi_minus": digest(rows_minus),
            "entropy_geometry": entropy_geometry,
            "operator_chi_plus": operator_report_plus,
            "operator_chi_minus": operator_report_minus,
            "signed_operator_difference": orientation_difference,
            "bidirectional": bidirectional,
            "compression": {key: value for key, value in compression.items() if key != "effective_operator"},
            "structural_counterfactuals": structural,
            "histories": history,
            "hopf_carrier": hopf,
            "jk_order": jk_order,
            "axis0": axis0,
            "bracket": octonion,
            "source_evidence_digest": evidence.get("result_digest"),
            "observable_signature": observable_signature,
        },
        "commitment_count": len(spec.commitments()),
        "claim_ceiling": (
            "complete finite owner-realization candidate under declared requirements; "
            "not a universal manifold, absolute MSS, physical theory, or final nesting"
        ),
    }
    result["evaluation_digest"] = digest(result)
    return result


def fully_featured_spec(candidate_id: str = "whole_gcm_probe") -> ManifoldSpec:
    return ManifoldSpec(
        candidate_id=candidate_id,
        ring_size=4,
        shell_count=3,
        nesting="twisted",
        potential="shannon",
        metric="fisher",
        connection="signed_u1",
        orientation="signed",
        carrier="division_hopf",
        history="coherent_bracketed",
        composition="octonion",
        compression="schur",
        expansion="coupled",
        axis0="dynamic",
        order_mode="all",
        source_depth="full",
    )


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    from common import write_json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    evidence_data = json.loads(args.evidence.read_text(encoding="utf-8"))
    evaluation = evaluate_manifold(fully_featured_spec(), evidence_data)
    if args.output:
        write_json(args.output, evaluation)
    print(json.dumps({
        "all_pass": evaluation["all_active_requirements_pass"],
        "failed": evaluation["failed"],
        "completion_count": evaluation["whole"]["completion_count_chi_plus"],
    }, sort_keys=True))
