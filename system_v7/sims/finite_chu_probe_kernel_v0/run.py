#!/usr/bin/env python3
"""Finite response-matrix kernel for Build Card 3.

The module deliberately implements a finite table and its literal operations.
It does not install Chu-category laws, an action transition system, or an
online history update semantics.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.util
import itertools
import json
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Hashable, Iterable, Mapping

import rustworkx as rx


sys.dont_write_bytecode = True

SIM_ID = "finite_chu_probe_kernel_v0"
VERSION = "0.1.0"
RESULT_SCHEMA = "codex_ratchet.finite_chu_probe_kernel.results.v1"
RESULT_PATH = Path(__file__).resolve().with_name("results_v1.json")
REPO_ROOT = Path(__file__).resolve().parents[3]
RESULT_RELATIVE_PATH = "system_v7/sims/finite_chu_probe_kernel_v0/results_v1.json"
REQUIRED_INTERPRETER = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
APPEND_COMMAND = (
    "PYTHONDONTWRITEBYTECODE=1 "
    f"{REQUIRED_INTERPRETER} "
    "system_v7/sims/finite_chu_probe_kernel_v0/run.py --append"
)

# These module-level literals intentionally satisfy the local sim-contract
# linter while fencing this finite table below any admission claim.
classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
sim_execution_kind = "classical"
TOOL_MANIFEST = {
    "python_stdlib": {
        "reason": "Exact finite enumeration, canonical JSON encoding, source packet loading, and append-only receipt checks use only the standard library."
    },
    "rustworkx": {
        "reason": "Connected components independently cross-check each exact fingerprint quotient and are consumed by the pass rule."
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "load_bearing",
    "rustworkx": "supportive",
}


class KernelError(RuntimeError):
    """Raised when a finite-carrier or receipt invariant is violated."""


@dataclass(frozen=True)
class ResponseMatrix:
    """A total finite response matrix with explicit state and probe orders."""

    name: str
    states: tuple[str, ...]
    probes: tuple[str, ...]
    outcomes: tuple[Hashable, ...]
    responses: tuple[tuple[Hashable, ...], ...]

    def __post_init__(self) -> None:
        if not self.name:
            raise KernelError("response matrix name must be non-empty")
        if not self.states or not self.probes or not self.outcomes:
            raise KernelError("response matrix needs non-empty states, probes, and outcomes")
        if len(set(self.states)) != len(self.states):
            raise KernelError(f"{self.name}: state labels must be unique")
        if len(set(self.probes)) != len(self.probes):
            raise KernelError(f"{self.name}: probe labels must be unique")
        if len(self.responses) != len(self.states):
            raise KernelError(f"{self.name}: response row count does not match state count")
        if any(len(row) != len(self.probes) for row in self.responses):
            raise KernelError(f"{self.name}: response width does not match probe count")
        allowed = set(self.outcomes)
        if any(value not in allowed for row in self.responses for value in row):
            raise KernelError(f"{self.name}: response value falls outside declared outcomes")

    def probe_index(self, probe: str) -> int:
        try:
            return self.probes.index(probe)
        except ValueError as error:
            raise KernelError(f"{self.name}: unknown probe {probe!r}") from error


def canonical_json(value: Any) -> str:
    """Canonical encoding used for payload equality and append-only digests."""
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def partition_from_keys(labels: Iterable[str], keys: Iterable[Hashable]) -> tuple[tuple[str, ...], ...]:
    groups: dict[Hashable, list[str]] = defaultdict(list)
    for label, key in zip(labels, keys, strict=True):
        groups[key].append(label)
    return tuple(sorted((tuple(sorted(group)) for group in groups.values()), key=lambda group: group))


def partition_signature(partition: tuple[tuple[str, ...], ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(sorted((tuple(sorted(group)) for group in partition), key=lambda group: group))


def partition_refines(
    finer: tuple[tuple[str, ...], ...],
    coarser: tuple[tuple[str, ...], ...],
) -> bool:
    """Return whether every class of ``finer`` lies in one class of ``coarser``."""
    coarser_membership = {
        member: class_index
        for class_index, group in enumerate(coarser)
        for member in group
    }
    finer_members = {member for group in finer for member in group}
    coarser_members = set(coarser_membership)
    if finer_members != coarser_members:
        return False
    return all(len({coarser_membership[member] for member in group}) == 1 for group in finer)


def json_partition(partition: tuple[tuple[str, ...], ...]) -> list[list[str]]:
    return [list(group) for group in partition]


def row_quotient(matrix: ResponseMatrix, selected_probes: Iterable[str]) -> tuple[tuple[str, ...], ...]:
    selected = tuple(selected_probes)
    indices = tuple(matrix.probe_index(probe) for probe in selected)
    keys = (tuple(row[index] for index in indices) for row in matrix.responses)
    return partition_from_keys(matrix.states, keys)


def strict_column_quotient(matrix: ResponseMatrix) -> tuple[tuple[str, ...], ...]:
    keys = (
        tuple(matrix.responses[state_index][probe_index] for state_index in range(len(matrix.states)))
        for probe_index in range(len(matrix.probes))
    )
    return partition_from_keys(matrix.probes, keys)


def column_power_quotient(matrix: ResponseMatrix) -> tuple[tuple[str, ...], ...]:
    keys = (
        row_quotient(matrix, (probe,))
        for probe in matrix.probes
    )
    return partition_from_keys(matrix.probes, keys)


def all_probe_subsets(probes: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple(
        subset
        for size in range(len(probes) + 1)
        for subset in itertools.combinations(probes, size)
    )


def subset_partition_map(matrix: ResponseMatrix) -> dict[tuple[str, ...], tuple[tuple[str, ...], ...]]:
    return {subset: row_quotient(matrix, subset) for subset in all_probe_subsets(matrix.probes)}


def exhaustive_refinement_check(matrix: ResponseMatrix) -> dict[str, Any]:
    """Check every A subset B relation on a finite table, by construction."""
    partitions = subset_partition_map(matrix)
    failures: list[dict[str, Any]] = []
    checked = 0
    for smaller, smaller_partition in partitions.items():
        smaller_set = set(smaller)
        for larger, larger_partition in partitions.items():
            if smaller_set <= set(larger):
                checked += 1
                if not partition_refines(larger_partition, smaller_partition):
                    failures.append(
                        {
                            "smaller_subset": list(smaller),
                            "larger_subset": list(larger),
                            "smaller_partition": json_partition(smaller_partition),
                            "larger_partition": json_partition(larger_partition),
                        }
                    )
    return {
        "probe_count": len(matrix.probes),
        "subset_count": len(partitions),
        "ordered_inclusion_checks": checked,
        "monotone": not failures,
        "failures": failures,
        "subset_class_counts": [
            {"subset": list(subset), "class_count": len(partition)}
            for subset, partition in partitions.items()
        ],
    }


def minimal_separating_families(matrix: ResponseMatrix) -> dict[str, Any]:
    partitions = subset_partition_map(matrix)
    full_subset = matrix.probes
    full_partition = partitions[full_subset]
    matching = [subset for subset, partition in partitions.items() if partition == full_partition]
    minimum_size = min(len(subset) for subset in matching)
    minimum = [subset for subset in matching if len(subset) == minimum_size]
    return {
        "full_probe_family": list(full_subset),
        "full_row_quotient": json_partition(full_partition),
        "full_class_count": len(full_partition),
        "minimal_cardinality": minimum_size,
        "minimal_families": [list(subset) for subset in minimum],
        "all_matching_families": [list(subset) for subset in matching],
    }


def dualize(matrix: ResponseMatrix) -> ResponseMatrix:
    """Swap state and probe axes without adding categorical structure."""
    transposed = tuple(
        tuple(matrix.responses[state_index][probe_index] for state_index in range(len(matrix.states)))
        for probe_index in range(len(matrix.probes))
    )
    return ResponseMatrix(
        name=f"{matrix.name}__transpose",
        states=matrix.probes,
        probes=matrix.states,
        outcomes=matrix.outcomes,
        responses=transposed,
    )


def matrix_equal(left: ResponseMatrix, right: ResponseMatrix) -> bool:
    return (
        left.states == right.states
        and left.probes == right.probes
        and left.outcomes == right.outcomes
        and left.responses == right.responses
    )


def rustworkx_component_partition(
    matrix: ResponseMatrix,
    selected_probes: Iterable[str],
) -> tuple[tuple[str, ...], ...]:
    """Build a quotient graph from raw response equality, then cross-check it.

    The graph is deliberately not seeded from ``row_quotient``.  Edges are
    formed pairwise from raw selected response vectors, so rustworkx consumes a
    separate equality-relation construction before its components are compared
    to the ordinary fingerprint quotient.
    """
    selected = tuple(selected_probes)
    indices = tuple(matrix.probe_index(probe) for probe in selected)
    raw_fingerprints = tuple(
        tuple(row[index] for index in indices)
        for row in matrix.responses
    )
    graph = rx.PyGraph(multigraph=False)
    node_indices = graph.add_nodes_from(list(matrix.states))
    index_for_state = dict(zip(matrix.states, node_indices, strict=True))
    for left_index, right_index in itertools.combinations(range(len(matrix.states)), 2):
        if raw_fingerprints[left_index] == raw_fingerprints[right_index]:
            graph.add_edge(
                index_for_state[matrix.states[left_index]],
                index_for_state[matrix.states[right_index]],
                None,
            )
    components = rx.connected_components(graph)
    component_partition = tuple(
        sorted(
            tuple(sorted(matrix.states[node_index] for node_index in component))
            for component in components
        )
    )
    fingerprint_partition = partition_from_keys(matrix.states, raw_fingerprints)
    if partition_signature(component_partition) != partition_signature(fingerprint_partition):
        raise KernelError(f"{matrix.name}: rustworkx components disagree with response quotient")
    return partition_signature(component_partition)


def table_receipt(matrix: ResponseMatrix) -> dict[str, Any]:
    return {
        "name": matrix.name,
        "state_count": len(matrix.states),
        "probe_count": len(matrix.probes),
        "states": list(matrix.states),
        "probes": list(matrix.probes),
        "outcomes": list(matrix.outcomes),
        "response_rows": [list(row) for row in matrix.responses],
    }


def sequential_extension(
    matrix: ResponseMatrix,
    *,
    first_probe: str,
    next_probe_for_outcome: Mapping[Hashable, str],
) -> ResponseMatrix:
    """Return a one-column table of ordered, outcome-adaptive transcripts.

    The second probe is selected by the first outcome.  No state mutation is
    assumed: both answers are evaluated against the same finite response row.
    """
    if set(next_probe_for_outcome) != set(matrix.outcomes):
        raise KernelError("sequential policy must define exactly one branch for every declared outcome")
    if any(probe not in matrix.probes for probe in next_probe_for_outcome.values()):
        raise KernelError("sequential policy selects an undeclared probe")
    first_index = matrix.probe_index(first_probe)
    transcripts: list[tuple[Hashable, str, Hashable]] = []
    for row in matrix.responses:
        first_outcome = row[first_index]
        second_probe = next_probe_for_outcome[first_outcome]
        second_outcome = row[matrix.probe_index(second_probe)]
        transcripts.append((first_outcome, second_probe, second_outcome))
    declared_transcripts = tuple(sorted(set(transcripts), key=repr))
    return ResponseMatrix(
        name=f"{matrix.name}__sequential_{first_probe}",
        states=matrix.states,
        probes=("ordered_outcome_adaptive_transcript",),
        outcomes=declared_transcripts,
        responses=tuple((transcript,) for transcript in transcripts),
    )


def ordered_transcript_witness(matrix: ResponseMatrix) -> dict[str, Any] | None:
    for first_probe, second_probe in itertools.permutations(matrix.probes, 2):
        first_index = matrix.probe_index(first_probe)
        second_index = matrix.probe_index(second_probe)
        for state, row in zip(matrix.states, matrix.responses, strict=True):
            forward = (row[first_index], row[second_index])
            reverse = (row[second_index], row[first_index])
            if forward != reverse:
                return {
                    "state": state,
                    "forward_order": [first_probe, second_probe],
                    "forward_transcript": list(forward),
                    "reverse_order": [second_probe, first_probe],
                    "reverse_transcript": list(reverse),
                    "interpretation": "ordered transcript difference only; this finite table supplies no state update law",
                }
    return None


def synthetic_matrix() -> ResponseMatrix:
    """A 6-state, 5-probe table with known row and probe-power structure."""
    return ResponseMatrix(
        name="synthetic_six_state_five_probe",
        states=("s0", "s1", "s2", "s3", "s4", "s5"),
        probes=("a", "b", "c", "d", "e"),
        outcomes=(0, 1),
        responses=(
            (0, 0, 0, 1, 1),
            (0, 0, 1, 1, 1),
            (0, 1, 0, 0, 1),
            (0, 1, 1, 0, 1),
            (1, 0, 0, 1, 0),
            (1, 0, 1, 1, 0),
        ),
    )


def load_ratchet_module(engine_path: Path) -> tuple[Any, str]:
    if not engine_path.is_file():
        raise KernelError(f"missing ratchet source: {engine_path}")
    before_import_hash = file_sha256(engine_path)
    module_name = "finite_chu_probe_kernel_readonly_ratchet_engine"
    module_spec = importlib.util.spec_from_file_location(module_name, engine_path)
    if module_spec is None or module_spec.loader is None:
        raise KernelError("could not construct read-only ratchet module spec")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    try:
        module_spec.loader.exec_module(module)
    finally:
        sys.modules.pop(module_name, None)
    after_import_hash = file_sha256(engine_path)
    if after_import_hash != before_import_hash:
        raise KernelError("read-only ratchet source changed while it was imported")
    return module, before_import_hash


def load_real_matrix() -> tuple[ResponseMatrix, list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    engine_path = REPO_ROOT / "system_v7/constraint_core/ratchet/ratchet_engine.py"
    packet_path = REPO_ROOT / "system_v7/constraint_core/ratchet/examples/root_history_packet_v0_4.json"
    module, engine_hash = load_ratchet_module(engine_path)
    packet_hash = file_sha256(packet_path)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if file_sha256(packet_path) != packet_hash:
        raise KernelError("read-only ratchet packet changed while it was loaded")
    gate = next(gate for gate in packet["gates"] if gate["id"] == "G1_two_step_order")
    probes = tuple(packet["exploration"]["probe_symbols"])
    outcomes = tuple(gate["outcomes"])
    source_rows = module.generate_observations(list(probes), gate)
    if len(source_rows) != 81:
        raise KernelError(f"expected exactly 81 G1 source rows, found {len(source_rows)}")
    source_lookup = {
        (tuple(row["history"]), row["probe"]): row["outcome"]
        for row in source_rows
    }
    if len(source_lookup) != len(source_rows):
        raise KernelError("G1 source has duplicate history/probe cells")
    states = tuple(f"source_row_{index:03d}" for index in range(len(source_rows)))
    response_rows = tuple(
        tuple(source_lookup[(tuple(source_row["history"]), probe)] for probe in probes)
        for source_row in source_rows
    )
    matrix = ResponseMatrix(
        name="ratchet_g1_81_source_rows_by_3_direct_probes",
        states=states,
        probes=probes,
        outcomes=outcomes,
        responses=response_rows,
    )
    source_records = [
        {
            "state": state,
            "history": list(source_row["history"]),
            "recorded_probe": source_row["probe"],
            "recorded_outcome": source_row["outcome"],
        }
        for state, source_row in zip(states, source_rows, strict=True)
    ]
    if any(
        matrix.responses[index][matrix.probe_index(record["recorded_probe"])] != record["recorded_outcome"]
        for index, record in enumerate(source_records)
    ):
        raise KernelError("derived direct table does not reproduce every recorded source cell")
    source_meta = {
        "engine_path": str(engine_path.relative_to(REPO_ROOT)),
        "engine_sha256": engine_hash,
        "packet_path": str(packet_path.relative_to(REPO_ROOT)),
        "packet_sha256": packet_hash,
        "gate_id": gate["id"],
        "history_length": gate["history_length"],
        "dependency_depth": gate["dependency_depth"],
        "source_row_count": len(source_rows),
        "direct_probe_symbols": list(probes),
        "outcome_labels": list(outcomes),
        "derivation_rule": "R(source_row, x) is regenerated with source_row.history and direct probe x",
    }
    return matrix, source_records, gate, source_meta


def derived_outcome_membership_view(
    direct_matrix: ResponseMatrix,
    source_records: list[dict[str, Any]],
    outcomes: tuple[str, ...],
) -> ResponseMatrix:
    """A derived one-hot rendering of source outcomes, not a native probe table."""
    source_outcomes = tuple(record["recorded_outcome"] for record in source_records)
    return ResponseMatrix(
        name="derived_source_outcome_membership_view",
        states=direct_matrix.states,
        probes=outcomes,
        outcomes=(False, True),
        responses=tuple(
            tuple(source_outcome == outcome for outcome in outcomes)
            for source_outcome in source_outcomes
        ),
    )


def source_memory_tooth() -> dict[str, Any]:
    run_path = REPO_ROOT / "system_v7/constraint_core/ratchet/runs/root_history_run_v0_4.json"
    packet_path = REPO_ROOT / "system_v7/constraint_core/ratchet/examples/root_history_packet_v0_4.json"
    run_hash = file_sha256(run_path)
    packet_hash = file_sha256(packet_path)
    run = json.loads(run_path.read_text(encoding="utf-8"))
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if file_sha256(run_path) != run_hash or file_sha256(packet_path) != packet_hash:
        raise KernelError("upstream G1 run or packet changed while it was loaded")
    if run.get("source_packet") != packet.get("packet_id"):
        raise KernelError("G1 run receipt does not identify the selected source packet")
    if run.get("run_id") != packet.get("run_id"):
        raise KernelError("G1 run receipt run_id does not match the selected source packet")
    g1 = next(gate for gate in run["gates"] if gate["gate_id"] == "G1_two_step_order")
    expected_frontier = ["partial_relation__memory_2__partial4"]
    expected_projection = "erase the oldest load-bearing history coordinate"
    expected_residual = "previously distinct ordered observations merge"
    if g1.get("finite_observation_count") != 81:
        raise KernelError("upstream G1 receipt no longer reports 81 observations")
    if g1["gate"].get("baseline_candidate") != "partial_relation__memory_1__partial4":
        raise KernelError("upstream G1 baseline candidate is not the declared memory-1 relation")
    if g1["gate"].get("baseline_errors") != 54:
        raise KernelError("upstream G1 baseline error count is not 54")
    if g1["gate"].get("target_candidate") != "partial_relation__memory_2__partial4":
        raise KernelError("upstream G1 target candidate is not the declared memory-2 relation")
    if g1["gate"].get("target_errors") != 0:
        raise KernelError("upstream G1 target error count is not zero")
    if g1["gate"].get("minimal_survivor_frontier") != expected_frontier:
        raise KernelError("upstream G1 minimal survivor frontier has drifted")
    if g1["receipt"].get("projection_back_down") != expected_projection:
        raise KernelError("upstream G1 projection wording has drifted")
    if g1["receipt"].get("residual_exposed_by_projection") != expected_residual:
        raise KernelError("upstream G1 projection residual has drifted")
    return {
        "run_path": str(run_path.relative_to(REPO_ROOT)),
        "run_sha256": run_hash,
        "packet_sha256": packet_hash,
        "source_packet_id": run["source_packet"],
        "source_packet_matches_selected_packet": True,
        "run_id": run["run_id"],
        "run_id_matches_selected_packet": True,
        "gate_id": g1["gate_id"],
        "finite_observation_count": g1["finite_observation_count"],
        "baseline_candidate": g1["gate"]["baseline_candidate"],
        "baseline_errors": g1["gate"]["baseline_errors"],
        "target_candidate": g1["gate"]["target_candidate"],
        "target_errors": g1["gate"]["target_errors"],
        "minimal_survivor_frontier": g1["gate"]["minimal_survivor_frontier"],
        "projection_back_down": g1["receipt"]["projection_back_down"],
        "residual_exposed_by_projection": g1["receipt"]["residual_exposed_by_projection"],
        "claim_ceiling": g1["receipt"]["claim_ceiling"],
        "expected_tooth_fields_verified": True,
        "boundary": "This is a source-model frontier under assumption inclusion, not a minimal separating probe-family result.",
    }


def lower_depth_demand_separation(
    direct_matrix: ResponseMatrix,
    source_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Measure whether direct requery separates every source G1 depth-1 conflict."""
    grouped: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, record in enumerate(source_records):
        grouped[(record["history"][-1], record["recorded_probe"])].append(index)
    conflicting_pairs = 0
    separated_by_full_static = 0
    unseparated: list[dict[str, Any]] = []
    for group_key, indices in sorted(grouped.items()):
        for left, right in itertools.combinations(indices, 2):
            if source_records[left]["recorded_outcome"] == source_records[right]["recorded_outcome"]:
                continue
            conflicting_pairs += 1
            if direct_matrix.responses[left] != direct_matrix.responses[right]:
                separated_by_full_static += 1
            else:
                unseparated.append(
                    {
                        "depth_one_key": list(group_key),
                        "left_state": direct_matrix.states[left],
                        "right_state": direct_matrix.states[right],
                        "left_outcome": source_records[left]["recorded_outcome"],
                        "right_outcome": source_records[right]["recorded_outcome"],
                    }
                )
    return {
        "depth_one_group_count": len(grouped),
        "conflicting_source_row_pairs": conflicting_pairs,
        "separated_by_full_static_direct_table": separated_by_full_static,
        "static_table_separates_all_depth_one_conflicts": not unseparated,
        "unseparated_pairs": unseparated,
        "interpretation": "The frozen full-history response table exposes every source depth-1 outcome conflict; this does not add an online update law to the source.",
    }


def sequential_policy_enumeration(matrix: ResponseMatrix) -> dict[str, Any]:
    """Enumerate every finite two-step outcome-adaptive policy on a table."""
    full_partition = row_quotient(matrix, matrix.probes)
    policy_records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    matching_full = 0
    for first_probe in matrix.probes:
        for chosen_probes in itertools.product(matrix.probes, repeat=len(matrix.outcomes)):
            policy = dict(zip(matrix.outcomes, chosen_probes, strict=True))
            extension = sequential_extension(
                matrix,
                first_probe=first_probe,
                next_probe_for_outcome=policy,
            )
            partition = row_quotient(extension, extension.probes)
            non_splitting = partition_refines(full_partition, partition)
            matches_full = partition == full_partition
            matching_full += int(matches_full)
            record = {
                "first_probe": first_probe,
                "second_probe_by_first_outcome": {
                    str(outcome): policy[outcome] for outcome in matrix.outcomes
                },
                "class_count": len(partition),
                "full_static_refines_transcript": non_splitting,
                "transcript_matches_full_static_quotient": matches_full,
            }
            policy_records.append(record)
            if not non_splitting:
                failures.append(record)
    representative_policy = {
        outcome: matrix.probes[index % len(matrix.probes)]
        for index, outcome in enumerate(matrix.outcomes)
    }
    representative_extension = sequential_extension(
        matrix,
        first_probe=matrix.probes[0],
        next_probe_for_outcome=representative_policy,
    )
    return {
        "policy_count": len(policy_records),
        "expected_policy_count": len(matrix.probes) * (len(matrix.probes) ** len(matrix.outcomes)),
        "all_policies_preserve_full_static_equivalence": not failures,
        "policies_matching_full_static_quotient": matching_full,
        "policy_records": policy_records,
        "representative_policy": {
            "first_probe": matrix.probes[0],
            "second_probe_by_first_outcome": {
                str(outcome): representative_policy[outcome] for outcome in matrix.outcomes
            },
            "extension_table": table_receipt(representative_extension),
            "row_quotient": json_partition(row_quotient(representative_extension, representative_extension.probes)),
        },
        "order_sensitive_transcript_witness": ordered_transcript_witness(matrix),
        "interpretation": "An outcome-adaptive transcript over a fixed total table cannot split a pair already equal under every static probe; it can only encode ordered query syntax unless a separate update map is supplied.",
    }


def synthetic_analysis() -> dict[str, Any]:
    matrix = synthetic_matrix()
    minimal = minimal_separating_families(matrix)
    refinement = exhaustive_refinement_check(matrix)
    strict_columns = strict_column_quotient(matrix)
    power_columns = column_power_quotient(matrix)
    dual = dualize(matrix)
    if not matrix_equal(dualize(dual), matrix):
        raise KernelError("synthetic double transpose failed")
    if len(minimal["full_row_quotient"]) != 6:
        raise KernelError("synthetic full table should separate all six states")
    if minimal["minimal_cardinality"] != 3:
        raise KernelError("synthetic minimum separating family should have cardinality three")
    if len(power_columns) != 3:
        raise KernelError("synthetic probe-power quotient should have three classes")
    rustworkx_partition = rustworkx_component_partition(matrix, matrix.probes)
    return {
        "table": table_receipt(matrix),
        "row_quotient_full": minimal["full_row_quotient"],
        "minimal_separating_search": minimal,
        "column_response_quotient": json_partition(strict_columns),
        "column_power_quotient": json_partition(power_columns),
        "refinement_under_added_probes": refinement,
        "dualization": {
            "transpose_table": table_receipt(dual),
            "double_transpose_equals_original": True,
            "transpose_row_quotient_equals_original_strict_column_quotient": (
                row_quotient(dual, dual.probes) == strict_columns
            ),
        },
        "sequential_extension_example": {
            "first_probe": "a",
            "second_probe_by_first_outcome": {"0": "b", "1": "c"},
            "row_quotient": json_partition(
                row_quotient(
                    sequential_extension(matrix, first_probe="a", next_probe_for_outcome={0: "b", 1: "c"}),
                    ("ordered_outcome_adaptive_transcript",),
                )
            ),
            "order_sensitive_transcript_witness": ordered_transcript_witness(matrix),
        },
        "rustworkx_component_cross_check": {
            "selected_probes": list(matrix.probes),
            "partition": json_partition(rustworkx_partition),
            "matches_fingerprint_row_quotient": True,
        },
    }


def real_analysis() -> dict[str, Any]:
    direct_matrix, source_records, gate, source_meta = load_real_matrix()
    minimal = minimal_separating_families(direct_matrix)
    strict_columns = strict_column_quotient(direct_matrix)
    power_columns = column_power_quotient(direct_matrix)
    dual = dualize(direct_matrix)
    if not matrix_equal(dualize(dual), direct_matrix):
        raise KernelError("real-table double transpose failed")
    if minimal["full_class_count"] != 4:
        raise KernelError("real direct table should have exactly four full row classes")
    if minimal["minimal_cardinality"] != 1:
        raise KernelError("real direct table should have a singleton separating family")
    if set(tuple(family) for family in minimal["minimal_families"]) != {("p",), ("q",), ("r",)}:
        raise KernelError("real direct table should have p, q, and r singleton minimal families")
    membership = derived_outcome_membership_view(direct_matrix, source_records, tuple(gate["outcomes"]))
    membership_minimal = minimal_separating_families(membership)
    if membership_minimal["full_class_count"] != 4 or membership_minimal["minimal_cardinality"] != 3:
        raise KernelError("derived outcome-membership view should need three of four indicators")
    rustworkx_partition = rustworkx_component_partition(direct_matrix, direct_matrix.probes)
    sequential = sequential_policy_enumeration(direct_matrix)
    if sequential["policy_count"] != sequential["expected_policy_count"]:
        raise KernelError("real sequential policy enumeration was incomplete")
    if not sequential["all_policies_preserve_full_static_equivalence"]:
        raise KernelError("a static-equivalent pair was split by a fixed-table sequential extension")
    demand_check = lower_depth_demand_separation(direct_matrix, source_records)
    if not demand_check["static_table_separates_all_depth_one_conflicts"]:
        raise KernelError("static direct table failed to separate a source depth-one conflict")
    return {
        "source": source_meta,
        "source_records": source_records,
        "primary_direct_table": table_receipt(direct_matrix),
        "recorded_cell_reconstruction": {
            "checked_source_rows": len(source_records),
            "all_recorded_cells_match_regenerated_direct_table": True,
        },
        "row_quotient_full": minimal["full_row_quotient"],
        "minimal_separating_search": minimal,
        "column_response_quotient": json_partition(strict_columns),
        "column_power_quotient": json_partition(power_columns),
        "dualization": {
            "transpose_table": table_receipt(dual),
            "double_transpose_equals_original": True,
            "transpose_row_quotient_equals_original_strict_column_quotient": (
                row_quotient(dual, dual.probes) == strict_columns
            ),
        },
        "rustworkx_component_cross_check": {
            "selected_probes": list(direct_matrix.probes),
            "partition": json_partition(rustworkx_partition),
            "matches_fingerprint_row_quotient": True,
        },
        "derived_four_outcome_membership_view": {
            "boundary": "Derived one-hot outcome membership by each source row's recorded outcome; not four native ratchet probe columns or source-defined pair-demand families.",
            "table": table_receipt(membership),
            "full_row_quotient": membership_minimal["full_row_quotient"],
            "minimal_separating_search": membership_minimal,
        },
        "upstream_memory_two_tooth": source_memory_tooth(),
        "depth_one_demand_separation": demand_check,
        "sequential_extension_measure": sequential,
        "memory_two_interpretation": {
            "static_direct_probes_suffice_for_the_derived_full_table_quotient": True,
            "sequential_extension_required_for_that_static_quotient": False,
            "why": "Each singleton direct probe already induces the four-class full quotient, and exhaustive fixed-table outcome-adaptive policies never split a full-static-equivalent pair.",
            "source_boundary": "G1's 54-versus-0 memory comparison remains a requirement on the source history representation. It becomes a sequential/update requirement only if a separate online transition semantics is supplied and validated."
        },
    }


def build_payload() -> dict[str, Any]:
    if Path(sys.executable).resolve() != REQUIRED_INTERPRETER.resolve():
        raise KernelError("this lane must run with the user-specified sim-stack interpreter")
    synthetic = synthetic_analysis()
    real = real_analysis()
    checks = {
        "synthetic_full_row_class_count_is_six": len(synthetic["row_quotient_full"]) == 6,
        "synthetic_refinement_is_exhaustively_monotone": synthetic["refinement_under_added_probes"]["monotone"],
        "synthetic_double_transpose": synthetic["dualization"]["double_transpose_equals_original"],
        "synthetic_rustworkx_cross_check": synthetic["rustworkx_component_cross_check"]["matches_fingerprint_row_quotient"],
        "real_source_cell_reconstruction": real["recorded_cell_reconstruction"]["all_recorded_cells_match_regenerated_direct_table"],
        "real_full_row_class_count_is_four": len(real["row_quotient_full"]) == 4,
        "real_singleton_direct_probe_families_match_full": real["minimal_separating_search"]["minimal_cardinality"] == 1,
        "real_double_transpose": real["dualization"]["double_transpose_equals_original"],
        "real_rustworkx_cross_check": real["rustworkx_component_cross_check"]["matches_fingerprint_row_quotient"],
        "real_static_table_separates_depth_one_demand_conflicts": real["depth_one_demand_separation"]["static_table_separates_all_depth_one_conflicts"],
        "real_all_sequential_policies_non_splitting": real["sequential_extension_measure"]["all_policies_preserve_full_static_equivalence"],
        "real_sequential_policy_enumeration_complete": (
            real["sequential_extension_measure"]["policy_count"]
            == real["sequential_extension_measure"]["expected_policy_count"]
        ),
        "upstream_g1_tooth_fields_verified": real["upstream_memory_two_tooth"]["expected_tooth_fields_verified"],
        "upstream_g1_observation_count_is_81": real["upstream_memory_two_tooth"]["finite_observation_count"] == 81,
        "upstream_g1_memory_one_errors_are_54": real["upstream_memory_two_tooth"]["baseline_errors"] == 54,
        "upstream_g1_memory_two_errors_are_zero": real["upstream_memory_two_tooth"]["target_errors"] == 0,
        "upstream_g1_packet_and_run_ids_match": (
            real["upstream_memory_two_tooth"]["source_packet_matches_selected_packet"]
            and real["upstream_memory_two_tooth"]["run_id_matches_selected_packet"]
        ),
    }
    if not all(checks.values()):
        failed = sorted(name for name, passed in checks.items() if not passed)
        raise KernelError("kernel checks failed: " + ", ".join(failed))
    witness_seed = {
        "synthetic_full_row_quotient": synthetic["row_quotient_full"],
        "real_full_row_quotient": real["row_quotient_full"],
        "real_source_sha256": real["source"]["engine_sha256"],
        "real_packet_sha256": real["source"]["packet_sha256"],
    }
    return {
        "schema": RESULT_SCHEMA,
        "schema_version": RESULT_SCHEMA,
        "sim_id": SIM_ID,
        "name": "FINITE CHU/PROBE KERNEL v0",
        "version": VERSION,
        "command": APPEND_COMMAND,
        "runner_identity": {
            "interpreter_path": str(REQUIRED_INTERPRETER),
            "implementation": sys.implementation.name,
            "version": list(sys.version_info[:3]),
        },
        "result_path": RESULT_RELATIVE_PATH,
        "tier": 1,
        "purpose": "Implement an exact finite pre-categorical response matrix and its requested quotient/probe operations.",
        "scientific_question": "What finite distinguishability partitions are induced by explicit response tables, without installing categorical or physical structure?",
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "carrier_probe",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "root_constraints_in_force": [
            "finite explicitly enumerated carrier",
            "probe-relative exact distinguishability",
            "no hidden transition or Chu-category structure"
        ],
        "carrier_layer": "finite response matrix R: S x P -> O",
        "geometry_layer": "not applicable to this finite table diagnostic",
        "bridge_layer": "not applicable",
        "cut_layer": "declared source history records only; no online cut/update law",
        "law_or_candidate_tested": "row/column quotient, monotone refinement, sequential transcript, transpose, and exact separating subset operations on finite response matrices",
        "branch_status_before_run": "new bounded Build Card 3 diagnostic",
        "allowed_claims": [
            "exact finite-table operation receipts",
            "source-specific static quotient measurements",
            "bounded static-versus-sequential interpretation"
        ],
        "promotion_blockers": [
            "no Chu-category laws",
            "no source transition/update semantics",
            "generated ratchet observation surface only",
            "no scientific or ratchet-frontier admission"
        ],
        "required_tools": ["python_stdlib", "rustworkx"],
        "actual_tools_used": ["python_stdlib", "rustworkx"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": ["rustworkx.connected_components exact quotient cross-check"],
        "topology_surfaces_used": [],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [
            "This is a finite static-table diagnostic, not an online history-update model.",
            "The four outcome labels are not recast as four native direct probes."
        ],
        "required_inputs": [
            "synthetic six-state five-probe fixture",
            "read-only ratchet engine",
            "read-only root history packet",
            "read-only executed G1 receipt"
        ],
        "data_or_artifact_dependencies": [
            "system_v7/constraint_core/ratchet/ratchet_engine.py",
            "system_v7/constraint_core/ratchet/examples/root_history_packet_v0_4.json",
            "system_v7/constraint_core/ratchet/runs/root_history_run_v0_4.json"
        ],
        "required_negatives": [
            "all-subset refinement counterexample search",
            "source recorded-cell mismatch check",
            "static-equivalent pair split search over all outcome-adaptive policies",
            "four-outcome membership view separation from native direct probes"
        ],
        "negatives_run": [
            "no monotonicity counterexample among all 243 synthetic subset-inclusion checks",
            "no source cell mismatch among 81 regenerated records",
            "no full-static-equivalent pair split among all 243 real two-step policies",
            "derived four-outcome membership view remains explicitly non-native"
        ],
        "kill_conditions": [
            "any response outside declared outcome set",
            "any added-probe monotonicity counterexample",
            "any source recorded-cell mismatch",
            "any fixed-table sequential policy splitting a full-static-equivalent pair",
            "any append-only payload digest mismatch"
        ],
        "required_artifacts": ["CARD.md", "wizard_v4_3_object_card.json", "run.py", "results_v1.json"],
        "artifacts_emitted": ["deterministic canonical payload ready for append-only run record"],
        "witness_trace_id": "finite-chu-probe-kernel/" + sha256_text(canonical_json(witness_seed)),
        "result_summary": {
            "synthetic_full_class_count": len(synthetic["row_quotient_full"]),
            "real_full_class_count": len(real["row_quotient_full"]),
            "real_minimal_direct_probe_cardinality": real["minimal_separating_search"]["minimal_cardinality"],
            "static_probes_suffice_for_real_derived_quotient": True,
            "sequential_extension_required_for_real_derived_quotient": False,
            "claim_ceiling": "deterministic finite-kernel receipt only"
        },
        "pass_rule": "All finite invariants, exact source reconstruction checks, rustworkx component checks, and policy-enumeration non-splitting checks pass; two appended canonical payloads must have identical digests before freeze.",
        "fail_rule": "Any literal table, source, quotient, refinement, sequential-boundary, component, or deterministic-payload check fails.",
        "promotion_status": "diagnostic_only",
        "eligible_consumers": ["future finite-table or probe-design diagnostics that preserve this exact claim ceiling"],
        "blocked_consumers": [
            "Chu-category formalization",
            "online transition-system claims",
            "ratchet frontier promotion",
            "scientific, entropy, manifold, Axis0, physics, or ontology claims"
        ],
        "checks": checks,
        "all_pass": True,
        "synthetic_instance": synthetic,
        "real_instance": real,
    }


def header_record() -> dict[str, Any]:
    return {
        "kind": "header",
        "schema_version": RESULT_SCHEMA,
        "sim_id": SIM_ID,
        "format": "json_lines_append_only",
        "expected_deterministic_run_count": 2,
    }


@contextmanager
def receipt_lock(path: Path, *, exclusive: bool, create: bool) -> Iterable[None]:
    """Serialize the whole receipt state transition without a sidecar lock file."""
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_RDWR | (os.O_CREAT if create else 0)
    try:
        descriptor = os.open(path, flags, 0o644)
    except FileNotFoundError as error:
        raise KernelError("results file does not exist yet") from error
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def append_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise KernelError("append-only receipt write made no progress")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def append_record(path: Path, record: dict[str, Any]) -> None:
    append_bytes(path, (canonical_json(record) + "\n").encode("utf-8"))


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            raise KernelError(f"results contains a blank non-record line at {line_number}")
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise KernelError(f"results has invalid JSON at line {line_number}") from error
        if not isinstance(record, dict):
            raise KernelError(f"results record at line {line_number} is not an object")
        records.append(record)
    return records


def validate_payload_contract(payload: dict[str, Any]) -> None:
    """Bind stored run records to this lane rather than accepting any hash."""
    if payload.get("schema") != RESULT_SCHEMA or payload.get("schema_version") != RESULT_SCHEMA:
        raise KernelError("run payload schema does not identify this finite-kernel lane")
    if payload.get("sim_id") != SIM_ID:
        raise KernelError("run payload sim_id does not identify this lane")
    if payload.get("result_path") != RESULT_RELATIVE_PATH:
        raise KernelError("run payload result_path does not identify this lane")
    if payload.get("command") != APPEND_COMMAND:
        raise KernelError("run payload command does not identify the required interpreter invocation")
    if payload.get("classification") != classification:
        raise KernelError("run payload classification has drifted")
    if payload.get("promotion_allowed") is not False or payload.get("formal_admission_allowed") is not False:
        raise KernelError("run payload attempts promotion outside the diagnostic fence")
    if payload.get("all_pass") is not True:
        raise KernelError("run payload does not carry an explicit all_pass=true")
    identity = payload.get("runner_identity")
    if not isinstance(identity, dict):
        raise KernelError("run payload has no runner identity")
    if identity.get("interpreter_path") != str(REQUIRED_INTERPRETER):
        raise KernelError("run payload runner identity does not name the required interpreter")
    if identity.get("implementation") != "cpython" or not isinstance(identity.get("version"), list):
        raise KernelError("run payload runner identity is incomplete")
    checks = payload.get("checks")
    required_checks = {
        "synthetic_full_row_class_count_is_six",
        "synthetic_refinement_is_exhaustively_monotone",
        "synthetic_double_transpose",
        "synthetic_rustworkx_cross_check",
        "real_source_cell_reconstruction",
        "real_full_row_class_count_is_four",
        "real_singleton_direct_probe_families_match_full",
        "real_double_transpose",
        "real_rustworkx_cross_check",
        "real_static_table_separates_depth_one_demand_conflicts",
        "real_all_sequential_policies_non_splitting",
        "real_sequential_policy_enumeration_complete",
        "upstream_g1_tooth_fields_verified",
        "upstream_g1_observation_count_is_81",
        "upstream_g1_memory_one_errors_are_54",
        "upstream_g1_memory_two_errors_are_zero",
        "upstream_g1_packet_and_run_ids_match",
    }
    if not isinstance(checks, dict) or any(checks.get(name) is not True for name in required_checks):
        raise KernelError("run payload lacks a required passing finite-kernel check")


def verify_records(records: list[dict[str, Any]], *, require_frozen: bool) -> dict[str, Any]:
    if not records or records[0] != header_record():
        raise KernelError("results header is missing or does not match the append-only schema")
    kinds = [record.get("kind") for record in records]
    freeze_records = [record for record in records if record.get("kind") == "freeze"]
    run_records = [record for record in records if record.get("kind") == "run"]
    expected_kinds = ["header"] + ["run"] * len(run_records) + (["freeze"] if freeze_records else [])
    if kinds != expected_kinds:
        raise KernelError("results records are not ordered as header, runs, optional freeze")
    if len(freeze_records) > 1:
        raise KernelError("results has more than one freeze record")
    for ordinal, record in enumerate(run_records, start=1):
        if record.get("ordinal") != ordinal:
            raise KernelError("run ordinals are not append-only consecutive integers")
        payload = record.get("payload")
        digest = record.get("payload_sha256")
        if not isinstance(payload, dict) or digest != sha256_text(canonical_json(payload)):
            raise KernelError(f"run {ordinal} payload digest is invalid")
        validate_payload_contract(payload)
    if require_frozen:
        if len(run_records) != 2 or len(freeze_records) != 1:
            raise KernelError("frozen results require exactly two run records and one freeze record")
        digests = [record["payload_sha256"] for record in run_records]
        if len(set(digests)) != 1:
            raise KernelError("frozen results do not contain two identical payloads")
        freeze = freeze_records[0]
        expected_freeze = {
            "kind": "freeze",
            "schema_version": RESULT_SCHEMA,
            "sim_id": SIM_ID,
            "verified_run_count": 2,
            "identical_payloads": True,
            "payload_sha256": digests[0],
        }
        if freeze != expected_freeze:
            raise KernelError("freeze record does not certify the exact two-run payload")
    return {
        "run_count": len(run_records),
        "frozen": bool(freeze_records),
        "payload_sha256": run_records[0]["payload_sha256"] if run_records else None,
    }


def ensure_header(path: Path) -> list[dict[str, Any]]:
    records = read_records(path)
    if not records:
        append_record(path, header_record())
        return [header_record()]
    verify_records(records, require_frozen=False)
    return records


def append_deterministic_run(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    validate_payload_contract(payload)
    with receipt_lock(path, exclusive=True, create=True):
        records = ensure_header(path)
        status = verify_records(records, require_frozen=False)
        if status["frozen"]:
            raise KernelError("results are frozen; refusing to append a new run")
        if status["run_count"] >= 2:
            raise KernelError("two run records already exist; use --freeze rather than appending")
        payload_digest = sha256_text(canonical_json(payload))
        prior_runs = [record for record in records if record.get("kind") == "run"]
        if prior_runs and prior_runs[0]["payload_sha256"] != payload_digest:
            raise KernelError("new canonical payload differs from the first appended run")
        ordinal = len(prior_runs) + 1
        append_record(
            path,
            {
                "kind": "run",
                "ordinal": ordinal,
                "payload_sha256": payload_digest,
                "payload": payload,
            },
        )
        return {"ordinal": ordinal, "payload_sha256": payload_digest}


def freeze_results(path: Path) -> dict[str, Any]:
    with receipt_lock(path, exclusive=True, create=False):
        records = read_records(path)
        status = verify_records(records, require_frozen=False)
        if status["frozen"]:
            raise KernelError("results are already frozen")
        if status["run_count"] != 2:
            raise KernelError("freeze requires exactly two appended deterministic runs")
        run_records = [record for record in records if record.get("kind") == "run"]
        digests = [record["payload_sha256"] for record in run_records]
        if len(set(digests)) != 1:
            raise KernelError("cannot freeze non-identical deterministic runs")
        freeze = {
            "kind": "freeze",
            "schema_version": RESULT_SCHEMA,
            "sim_id": SIM_ID,
            "verified_run_count": 2,
            "identical_payloads": True,
            "payload_sha256": digests[0],
        }
        append_record(path, freeze)
        return freeze


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true", help="compute and print a canonical payload hash without writing")
    action.add_argument("--append", action="store_true", help="append one deterministic run record")
    action.add_argument("--freeze", action="store_true", help="append the freeze record after exactly two matching runs")
    action.add_argument("--verify", action="store_true", help="verify frozen JSON Lines without writing")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.dry_run:
            payload = build_payload()
            print(canonical_json({"action": "dry_run", "ok": True, "payload_sha256": sha256_text(canonical_json(payload))}))
            return 0
        if args.append:
            payload = build_payload()
            appended = append_deterministic_run(RESULT_PATH, payload)
            print(canonical_json({"action": "append", "ok": True, **appended}))
            return 0
        if args.freeze:
            frozen = freeze_results(RESULT_PATH)
            print(canonical_json({"action": "freeze", "ok": True, **frozen}))
            return 0
        with receipt_lock(RESULT_PATH, exclusive=False, create=False):
            status = verify_records(read_records(RESULT_PATH), require_frozen=True)
        print(canonical_json({"action": "verify", "ok": True, **status}))
        return 0
    except (KernelError, ImportError, OSError, SyntaxError, AttributeError, KeyError, StopIteration, TypeError, ValueError) as error:
        print(canonical_json({"ok": False, "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
