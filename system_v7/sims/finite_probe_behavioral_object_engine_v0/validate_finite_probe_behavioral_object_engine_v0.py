#!/usr/bin/env python3
"""Independent fail-closed validator for the finite behavioral-object packet.

The validator uses only the Python standard library.  It reconstructs the
finite fixture instead of importing any builder, treats Julia/JAX agreement as
exact-fixture parity rather than proof, and keeps the PyTorch lane below exact
object authority.  The semantic fabrication audit is intentionally adverse:
T9 was not executed, so the packet can validate mechanically without passing
all scientific gates.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = ROOT / "system_v7/sims/finite_probe_behavioral_object_engine_v0"
RESULTS = HERE / "results"
SPEC_PATH = HERE / "spec.json"
PREREG_PATH = HERE / "preregistration_receipt.json"
JULIA_SOURCE_PATH = HERE / "run_julia.jl"
JAX_SOURCE_PATH = HERE / "run_jax.py"
PYTORCH_SOURCE_PATH = HERE / "run_pytorch.py"
JULIA_RESULT_PATH = RESULTS / "finite_probe_behavioral_object_engine_v0_julia_results.json"
JAX_RESULT_PATH = RESULTS / "finite_probe_behavioral_object_engine_v0_jax_results.json"
PYTORCH_RESULT_PATH = RESULTS / "finite_probe_behavioral_object_engine_v0_pytorch_results.json"
OUTPUT_PATH = RESULTS / "finite_probe_behavioral_object_engine_v0_validation.json"

SIM_ID = "finite_probe_behavioral_object_engine_v0"
CLASSIFICATION = "scratch_diagnostic"
ACCEPTED_LABEL = "EXACT_CORE_PLUS_TOPOLOGY_DEPENDENT_FIT_ONLY"
BLOCKED_LABEL = "BLOCKED_MECHANICAL_VALIDATION_FAILURE"
RING_SIZE = 6
STATE_COUNT = 64
MAX_DEPTH = 6
HISTORY_WIDTH = 127
RULE_A = 30
RULE_B = 110

FROZEN_HASHES = {
    SPEC_PATH: "73dfcce77e1f4001b3b2341817a449f96f898bc77c025323d1ca04ee3b3a1146",
    PREREG_PATH: "25dfea0d30479d9fb6fa20e960aebe2a6366d4521807bfa298a772944f7091b5",
    JULIA_SOURCE_PATH: "81a9b728cf19ce2df99d65f8ecb149bd3ca7bc7281f539f42ac393feae2eaf16",
    JAX_SOURCE_PATH: "b1af1342fc18034585aacfaf076d161221eaccc2845a9b929526ceb02f22fd67",
    PYTORCH_SOURCE_PATH: "5220efd437f8e34f996d04b438d1b67fa31a2e532e0d3c70d53895b969da941c",
    JULIA_RESULT_PATH: "a17aa35eb9366b4b00980b430c475de33bc18b5a597fb06cf8fb75771e796c8d",
    JAX_RESULT_PATH: "1d3620f46e59f85d9577ded8f2ba2868e0b330a15059dd43e4df03485980a356",
    PYTORCH_RESULT_PATH: "eac297c3b881c651f090f40b5d18aa7417710dc20975e73917fcc820032f0d7c",
}

SPEC_KEYS = {
    "schema", "sim_id", "created_at", "classification", "promotion_allowed",
    "formal_admission_allowed", "stage_movement_allowed", "fixture",
    "engine_contract", "preregistered_tests", "expected_controller_fixture_values",
    "required_controls", "claim_ceiling", "blocked_consumers",
}
PREREG_KEYS = {
    "schema", "sim_id", "registered_before_builder_source", "registered_at",
    "spec_path", "spec_sha256", "classification", "promotion_allowed",
    "formal_admission_allowed", "controller_note",
}
JULIA_TOP_KEYS = {
    "TOOL_INTEGRATION_DEPTH", "TOOL_MANIFEST", "aligned_packages_load_bearing",
    "all_pass", "behavioral_refinement", "blocked_consumers", "claim_ceiling",
    "classification", "closed_json_validation", "controls", "divergence_log",
    "engine", "engine_contract", "exact_quotient", "fixture",
    "foreign_runtime_manifest", "formal_admission_allowed", "functional_graphs",
    "hashes", "input_provenance", "lego_contract", "packages_used",
    "presentation_symmetry", "promotion_allowed", "ran", "reads_peer_result",
    "result_path", "schema", "scientific_pass_before_closed_json_gate",
    "semantic_role", "sim_id", "source_path", "stage_movement_allowed",
    "test_scope", "tests", "tool_calls", "tool_integration_depth",
    "tool_manifest", "witness_trace",
}
JAX_TOP_KEYS = {
    "TOOL_INTEGRATION_DEPTH", "TOOL_MANIFEST", "action_order", "actual_tools_used",
    "aligned_packages_load_bearing", "all_pass", "allowed_claims", "artifact_hashes",
    "artifacts_emitted", "blocked_consumers", "branch_status_before_run", "bridge_layer",
    "carrier_layer", "claim_ceiling", "classification", "controls", "cut_layer",
    "data_or_artifact_dependencies", "demotion_condition", "divergence_log",
    "eligible_consumers", "engine", "engine_role", "fail_rule", "fixture",
    "foreign_runtime_manifest", "formal_admission_allowed", "geometry_layer",
    "graph_surfaces_used", "history_fingerprints", "input_integrity", "jax_version",
    "kill_conditions", "law_or_candidate_tested", "negatives_run", "out_of_scope",
    "output_path", "packages_used", "pass_rule", "peer_result_paths_read",
    "promotion_allowed", "promotion_blockers", "promotion_status", "proof_surfaces_used",
    "purpose", "quotient", "reads_peer_result", "required_artifacts", "required_inputs",
    "required_negatives", "required_tools", "result_summary", "root_constraints_in_force",
    "schema", "schema_version", "scientific_question", "semiconjugacy", "sim_class",
    "sim_execution_kind", "sim_id", "source_path", "source_sha256",
    "stage_movement_allowed", "surviving_alternatives", "tests", "tier", "tool_calls",
    "tool_integration_depth", "tool_manifest", "topology_surfaces_used",
    "witness_trace_id", "x64_enabled",
}
PYTORCH_TOP_KEYS = {
    "TOOL_INTEGRATION_DEPTH", "TOOL_MANIFEST", "actual_tools_used",
    "aligned_packages_load_bearing", "all_pass", "claim_ceiling", "classification",
    "control_gaps", "engine", "engine_contract", "experiments",
    "formal_admission_allowed", "graph_surfaces_used", "hashes",
    "input_integrity_gates", "inputs", "negatives_run", "outputs", "packages_used",
    "peer_result_paths_read", "post_audit_interpretation", "preregistered_T8_gates",
    "preregistration_receipt_sha256", "promotion_allowed",
    "promotion_status", "proof_surfaces_used", "reads_peer_result", "result_path",
    "schema", "schema_version", "sim_contract", "sim_id", "source_path",
    "source_sha256", "spec_path", "spec_sha256", "split", "stage_movement_allowed",
    "target_derivation", "test_accuracy", "test_margin", "tool_calls",
    "topology_surfaces_used", "torch_func_sensitivity", "training",
}
METRIC_KEYS = {
    "accuracy", "correct", "count", "margin_max", "margin_mean", "margin_median",
    "margin_min", "margin_sha256", "positive_margin_fraction", "prediction_sha256",
}
EXPERIMENT_KEYS = {
    "bounded_epoch_limit", "directed_edge_count_per_graph", "epochs_completed",
    "erased_ring_edges", "final_loss", "held_out_against_true_targets", "initial_loss",
    "model_state_sha256", "name", "seed", "training_against_assigned_targets",
}
EXPECTED_PYTORCH_HELD = {
    "positive": {
        "accuracy": 1.0, "correct": 50, "count": 50,
        "margin_min": 8.53661343615415,
        "margin_sha256": "911c1284510b5cdcdd466eaa4cf5befa47d359710d438cf3c25cfb4b700628a6",
        "prediction_sha256": "20c3acf32ab7f8bc52f02e0e8338321cc3d97942dc94e1a4960dd072bec21fde",
        "model_state_sha256": "8cc307d8db813246def625fea44129701ad6fcdc5737541e88c4923b09feeeef",
    },
    "shuffled_target_control": {
        "accuracy": 0.0, "correct": 0, "count": 50,
        "margin_min": -38.705725232184875,
        "margin_sha256": "408c8063b443e875a46ea64dff5c63b4a44d2c3819b05d400cc49b0e88efb31e",
        "prediction_sha256": "6ea41edf6a4c276dcd251a3189baa56f32fec9aa9e1f0b27ffcfd5ce2ec6c018",
        "model_state_sha256": "442fa064dce94ab352d8655cf12a8e65558ef406980349e3800e82a1bfdceef0",
    },
    "erased_ring_edge_control": {
        "accuracy": 0.44, "correct": 22, "count": 50,
        "margin_min": -0.16061910621404252,
        "margin_sha256": "acd93b5e525c942be784289fecc1fad8210366885f7484719cf320a46fe6d0b7",
        "prediction_sha256": "52acba93e3f66487c72fcb7bb0ff98ceff18d3cc68e999d114eeeea06f1e837a",
        "model_state_sha256": "e44303062cd03783af55cf4f85bcbbaea37904422a00a2b51ce2c78362416330",
    },
}


class ValidationError(RuntimeError):
    """A fail-closed packet validation error."""


@dataclass
class Packet:
    spec: dict[str, Any]
    prereg: dict[str, Any]
    julia: dict[str, Any]
    jax: dict[str, Any]
    pytorch: dict[str, Any]


@dataclass(frozen=True)
class ExactFixture:
    action_a: list[int]
    action_b: list[int]
    histories: list[list[int]]
    fingerprints: list[list[int]]
    two_probe_partitions: list[list[list[int]]]
    weight_partitions: list[list[list[int]]]
    two_probe_labels: list[list[int]]
    weight_labels: list[list[int]]
    rotation_orbits: list[list[int]]
    rotation_labels: list[int]
    induced_a: list[int]
    induced_b: list[int]
    quotient_sccs: list[list[int]]
    a_after_b: list[int]
    b_after_a: list[int]
    graph_ab: dict[str, Any]
    graph_ba: dict[str, Any]


def reject_constant(token: str) -> None:
    raise ValidationError(f"non-finite JSON constant {token!r}")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def strict_json_load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=reject_constant,
            object_pairs_hook=reject_duplicate_pairs,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"cannot read strict JSON {relative(path)}: {exc}") from exc
    require(isinstance(value, dict), relative(path), "root must be an object")
    return value


def strict_write_json(path: Path, value: dict[str, Any]) -> None:
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def require(condition: bool, path: str, message: str) -> None:
    if not condition:
        raise ValidationError(f"{path}: {message}")


def exact_keys(value: Any, expected: set[str], path: str) -> dict[str, Any]:
    require(isinstance(value, dict), path, "must be an object")
    observed = set(value)
    require(
        observed == expected,
        path,
        f"closed schema keys differ; missing={sorted(expected - observed)}, extra={sorted(observed - expected)}",
    )
    return value


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def canonical_partition(cells: Iterable[Iterable[int]]) -> list[list[int]]:
    normalized = []
    for cell in cells:
        normalized_cell = sorted(set(cell))
        if normalized_cell:
            normalized.append(normalized_cell)
    return sorted(normalized, key=tuple)


def bit_at(state: int, site: int) -> int:
    return (state >> (site % RING_SIZE)) & 1


def eca_step(state: int, rule: int) -> int:
    result = 0
    for site in range(RING_SIZE):
        neighborhood = (
            (bit_at(state, site - 1) << 2)
            | (bit_at(state, site) << 1)
            | bit_at(state, site + 1)
        )
        result |= ((rule >> neighborhood) & 1) << site
    return result


def rotate_state(state: int, shift: int) -> int:
    result = 0
    for site in range(RING_SIZE):
        result |= bit_at(state, site) << ((site + shift) % RING_SIZE)
    return result


def probes(state: int) -> tuple[int, int]:
    weight = state.bit_count()
    walls = sum(bit_at(state, site) != bit_at(state, site + 1) for site in range(RING_SIZE))
    return weight, walls


def observation_partition(weight_only: bool) -> list[list[int]]:
    buckets: dict[Any, list[int]] = {}
    for state in range(STATE_COUNT):
        observation: Any = probes(state)[0] if weight_only else probes(state)
        buckets.setdefault(observation, []).append(state)
    return canonical_partition(buckets.values())


def class_indices(partition: list[list[int]]) -> list[int]:
    labels = [-1] * STATE_COUNT
    for class_index, cell in enumerate(partition):
        for state in cell:
            labels[state] = class_index
    require(all(label >= 0 for label in labels), "fixture.partition", "does not cover all states")
    return labels


def representative_labels(partition: list[list[int]]) -> list[int]:
    labels = [-1] * STATE_COUNT
    for cell in partition:
        representative = min(cell)
        for state in cell:
            labels[state] = representative
    return labels


def refine_partition(
    partition: list[list[int]], action_a: list[int], action_b: list[int]
) -> list[list[int]]:
    labels = class_indices(partition)
    refined: list[list[int]] = []
    for cell in partition:
        buckets: dict[tuple[int, int], list[int]] = {}
        for state in cell:
            signature = (labels[action_a[state]], labels[action_b[state]])
            buckets.setdefault(signature, []).append(state)
        refined.extend(buckets.values())
    return canonical_partition(refined)


def refinement_history(weight_only: bool, action_a: list[int], action_b: list[int]) -> list[list[list[int]]]:
    history = [observation_partition(weight_only)]
    for _ in range(MAX_DEPTH):
        history.append(refine_partition(history[-1], action_a, action_b))
    return history


def action_histories(action_a: list[int], action_b: list[int]) -> list[list[int]]:
    rows: list[list[int]] = []
    actions = (action_a, action_b)
    for initial in range(STATE_COUNT):
        row = [0] * HISTORY_WIDTH
        row[0] = initial
        for index in range(1, HISTORY_WIDTH):
            parent = (index - 1) // 2
            action = (index - 1) & 1
            row[index] = actions[action][row[parent]]
        rows.append(row)
    return rows


def labels_from_rows(rows: list[list[int]], width: int) -> list[int]:
    buckets: dict[tuple[int, ...], list[int]] = {}
    for state, row in enumerate(rows):
        buckets.setdefault(tuple(row[:width]), []).append(state)
    return representative_labels(canonical_partition(buckets.values()))


def rotation_orbits() -> list[list[int]]:
    cells: dict[int, set[int]] = {}
    for state in range(STATE_COUNT):
        orbit = {rotate_state(state, shift) for shift in range(RING_SIZE)}
        cells.setdefault(min(orbit), set()).update(orbit)
    return canonical_partition(cells.values())


def induced_maps(
    partition: list[list[int]], action_a: list[int], action_b: list[int]
) -> tuple[list[int], list[int]]:
    labels = class_indices(partition)
    maps: list[list[int]] = [[], []]
    for action_index, action in enumerate((action_a, action_b)):
        for cell in partition:
            destinations = {labels[action[state]] for state in cell}
            require(len(destinations) == 1, "fixture.stable_quotient", "is not a congruence")
            maps[action_index].append(next(iter(destinations)))
    return maps[0], maps[1]


def reachable(start: int, edges: set[tuple[int, int]], count: int) -> set[int]:
    seen = {start}
    stack = [start]
    while stack:
        source = stack.pop()
        for edge_source, destination in edges:
            if edge_source == source and destination not in seen:
                seen.add(destination)
                stack.append(destination)
    return seen


def strongly_connected_components(induced_a: list[int], induced_b: list[int]) -> list[list[int]]:
    count = len(induced_a)
    edges = {(source, destination) for source, destination in enumerate(induced_a)}
    edges |= {(source, destination) for source, destination in enumerate(induced_b)}
    reaches = [reachable(source, edges, count) for source in range(count)]
    remaining = set(range(count))
    components: list[list[int]] = []
    while remaining:
        source = min(remaining)
        component = sorted(node for node in remaining if node in reaches[source] and source in reaches[node])
        components.append(component)
        remaining.difference_update(component)
    return sorted(components, key=tuple)


def canonical_cycle(cycle: list[int]) -> list[int]:
    return min((cycle[index:] + cycle[:index] for index in range(len(cycle))), key=tuple)


def functional_graph(transition: list[int]) -> dict[str, Any]:
    basins: dict[tuple[int, ...], list[int]] = {}
    for start in range(STATE_COUNT):
        path: list[int] = []
        first_index: dict[int, int] = {}
        state = start
        while state not in first_index:
            first_index[state] = len(path)
            path.append(state)
            state = transition[state]
        cycle = tuple(canonical_cycle(path[first_index[state] :]))
        basins.setdefault(cycle, []).append(start)
    records = [
        {
            "cycle": list(cycle),
            "period": len(cycle),
            "basin_size": len(states),
            "basin_states": sorted(states),
        }
        for cycle, states in sorted(basins.items())
    ]
    return {
        "attractor_count": len(records),
        "sorted_basin_sizes": sorted(record["basin_size"] for record in records),
        "attractors": records,
        "all_states_assigned_once": sum(record["basin_size"] for record in records) == STATE_COUNT,
    }


def semiconjugacy(labels: list[int], transition: list[int]) -> dict[str, Any]:
    conflicting_pairs: list[tuple[int, int]] = []
    conflicting_classes: set[int] = set()
    for left in range(STATE_COUNT):
        for right in range(STATE_COUNT):
            if labels[left] == labels[right] and labels[transition[left]] != labels[transition[right]]:
                conflicting_pairs.append((left, right))
                conflicting_classes.add(labels[left])
    return {
        "well_defined": not conflicting_pairs,
        "conflicting_pair_count": len(conflicting_pairs),
        "conflicting_class_count": len(conflicting_classes),
        "first_conflict": list(conflicting_pairs[0]) if conflicting_pairs else [-1, -1],
    }


def build_fixture() -> ExactFixture:
    action_a = [eca_step(state, RULE_A) for state in range(STATE_COUNT)]
    action_b = [eca_step(state, RULE_B) for state in range(STATE_COUNT)]
    histories = action_histories(action_a, action_b)
    fingerprints = [[item for state in row for item in probes(state)] for row in histories]
    two_probe_partitions = refinement_history(False, action_a, action_b)
    weight_partitions = refinement_history(True, action_a, action_b)
    two_probe_labels = [representative_labels(partition) for partition in two_probe_partitions]
    weight_labels = [representative_labels(partition) for partition in weight_partitions]
    orbits = rotation_orbits()
    stable = two_probe_partitions[-1]
    induced_a, induced_b = induced_maps(stable, action_a, action_b)
    a_after_b = [action_a[action_b[state]] for state in range(STATE_COUNT)]
    b_after_a = [action_b[action_a[state]] for state in range(STATE_COUNT)]
    return ExactFixture(
        action_a=action_a,
        action_b=action_b,
        histories=histories,
        fingerprints=fingerprints,
        two_probe_partitions=two_probe_partitions,
        weight_partitions=weight_partitions,
        two_probe_labels=two_probe_labels,
        weight_labels=weight_labels,
        rotation_orbits=orbits,
        rotation_labels=representative_labels(orbits),
        induced_a=induced_a,
        induced_b=induced_b,
        quotient_sccs=strongly_connected_components(induced_a, induced_b),
        a_after_b=a_after_b,
        b_after_a=b_after_a,
        graph_ab=functional_graph(a_after_b),
        graph_ba=functional_graph(b_after_a),
    )


def load_packet() -> Packet:
    return Packet(
        spec=strict_json_load(SPEC_PATH),
        prereg=strict_json_load(PREREG_PATH),
        julia=strict_json_load(JULIA_RESULT_PATH),
        jax=strict_json_load(JAX_RESULT_PATH),
        pytorch=strict_json_load(PYTORCH_RESULT_PATH),
    )


def validate_hashes() -> dict[str, dict[str, Any]]:
    receipts: dict[str, dict[str, Any]] = {}
    for path, expected in FROZEN_HASHES.items():
        observed = sha256(path)
        require(observed == expected, f"hashes.{relative(path)}", f"expected {expected}, got {observed}")
        receipts[relative(path)] = {"expected": expected, "observed": observed, "pass": True}
    return receipts


def validate_identity_and_ceilings(packet: Packet) -> None:
    exact_keys(packet.spec, SPEC_KEYS, "spec")
    exact_keys(packet.prereg, PREREG_KEYS, "preregistration")
    exact_keys(packet.julia, JULIA_TOP_KEYS, "julia")
    exact_keys(packet.jax, JAX_TOP_KEYS, "jax")
    exact_keys(packet.pytorch, PYTORCH_TOP_KEYS, "pytorch")
    expected_lane_all_pass = {"julia": False, "jax": False, "pytorch": True}
    for name, result in (("julia", packet.julia), ("jax", packet.jax), ("pytorch", packet.pytorch)):
        require(result["sim_id"] == SIM_ID, f"{name}.sim_id", "unexpected sim id")
        require(result["engine"] == name, f"{name}.engine", "unexpected engine")
        require(result["classification"] == CLASSIFICATION, f"{name}.classification", "ceiling drift")
        require(result["promotion_allowed"] is False, f"{name}.promotion_allowed", "must be false")
        require(result["formal_admission_allowed"] is False, f"{name}.formal_admission_allowed", "must be false")
        require(result["stage_movement_allowed"] is False, f"{name}.stage_movement_allowed", "must be false")
        require(
            result["all_pass"] is expected_lane_all_pass[name],
            f"{name}.all_pass",
            f"expected post-audit value {expected_lane_all_pass[name]}",
        )
    require(packet.spec["classification"] == CLASSIFICATION, "spec.classification", "ceiling drift")
    require(packet.spec["promotion_allowed"] is False, "spec.promotion_allowed", "must be false")
    require(packet.spec["formal_admission_allowed"] is False, "spec.formal_admission_allowed", "must be false")
    require(packet.spec["stage_movement_allowed"] is False, "spec.stage_movement_allowed", "must be false")
    require(packet.prereg["spec_sha256"] == FROZEN_HASHES[SPEC_PATH], "preregistration.spec_sha256", "does not bind frozen spec")
    require(packet.prereg["registered_before_builder_source"] is True, "preregistration.registered_before_builder_source", "must be true")
    require(packet.julia["claim_ceiling"] == packet.spec["claim_ceiling"], "julia.claim_ceiling", "does not preserve spec")
    require(packet.jax["claim_ceiling"] == packet.spec["claim_ceiling"], "jax.claim_ceiling", "does not preserve spec")
    require(packet.julia["blocked_consumers"] == packet.spec["blocked_consumers"], "julia.blocked_consumers", "does not preserve spec")
    require(packet.jax["blocked_consumers"] == packet.spec["blocked_consumers"], "jax.blocked_consumers", "does not preserve spec")
    exact_keys(packet.pytorch["claim_ceiling"], {"allowed", "never_gates", "blocked_consumers", "removal_effect"}, "pytorch.claim_ceiling")
    never_gates = set(packet.pytorch["claim_ceiling"]["never_gates"])
    require(
        {"exact behavioral-object identity", "quotient semiconjugacy", "exact attractor or basin structure", "Julia semantic arbitration", "JAX exhaustive-history claims"} <= never_gates,
        "pytorch.claim_ceiling.never_gates",
        "exact-core exclusions are incomplete",
    )


def validate_source_bindings_and_peer_reads(packet: Packet) -> dict[str, Any]:
    require(packet.julia["hashes"]["run_julia_sha256"] == FROZEN_HASHES[JULIA_SOURCE_PATH], "julia.hashes.run_julia_sha256", "source binding mismatch")
    require(packet.jax["source_sha256"] == FROZEN_HASHES[JAX_SOURCE_PATH], "jax.source_sha256", "source binding mismatch")
    require(packet.pytorch["source_sha256"] == FROZEN_HASHES[PYTORCH_SOURCE_PATH], "pytorch.source_sha256", "source binding mismatch")
    require(packet.pytorch["hashes"]["source_sha256"] == FROZEN_HASHES[PYTORCH_SOURCE_PATH], "pytorch.hashes.source_sha256", "source binding mismatch")
    require(packet.julia["hashes"]["spec_sha256"] == FROZEN_HASHES[SPEC_PATH], "julia.hashes.spec_sha256", "spec binding mismatch")
    require(packet.jax["input_integrity"]["spec_sha256"] == FROZEN_HASHES[SPEC_PATH], "jax.input_integrity.spec_sha256", "spec binding mismatch")
    require(packet.pytorch["spec_sha256"] == FROZEN_HASHES[SPEC_PATH], "pytorch.spec_sha256", "spec binding mismatch")
    require(packet.pytorch["preregistration_receipt_sha256"] == FROZEN_HASHES[PREREG_PATH], "pytorch.preregistration_receipt_sha256", "preregistration binding mismatch")
    require(packet.pytorch["hashes"]["preregistration_receipt_sha256"] == FROZEN_HASHES[PREREG_PATH], "pytorch.hashes.preregistration_receipt_sha256", "preregistration binding mismatch")

    sources = {
        "julia": JULIA_SOURCE_PATH.read_text(encoding="utf-8"),
        "jax": JAX_SOURCE_PATH.read_text(encoding="utf-8"),
        "pytorch": PYTORCH_SOURCE_PATH.read_text(encoding="utf-8"),
    }
    result_names = {
        "julia": JULIA_RESULT_PATH.name,
        "jax": JAX_RESULT_PATH.name,
        "pytorch": PYTORCH_RESULT_PATH.name,
    }
    static_checks: dict[str, bool] = {}
    for engine, result in (("julia", packet.julia), ("jax", packet.jax), ("pytorch", packet.pytorch)):
        require(result["reads_peer_result"] is False, f"{engine}.reads_peer_result", "must be false")
        peer_list = result["input_provenance"]["peer_result_files_read"] if engine == "julia" else result["peer_result_paths_read"]
        require(peer_list == [], f"{engine}.peer_result_paths_read", "must be empty")
        forbidden = [name for peer, name in result_names.items() if peer != engine]
        static_checks[engine] = all(name not in sources[engine] for name in forbidden)
        require(static_checks[engine], f"sources.{engine}", "contains a peer result filename")
    return {
        "result_receipts_declare_no_peer_read": True,
        "frozen_sources_contain_no_peer_result_filename": static_checks,
        "pytorch_preregistration_runtime_read": "preregistration_receipt.json" in sources["pytorch"],
    }


def expected_state_table(fixture: ExactFixture) -> list[dict[str, Any]]:
    orbit_class = class_indices(fixture.rotation_orbits)
    return [
        {
            "state": state,
            "bits_site_5_to_0": format(state, "06b"),
            "weight": probes(state)[0],
            "domain_walls": probes(state)[1],
            "A_rule30_successor": fixture.action_a[state],
            "B_rule110_successor": fixture.action_b[state],
            "behavioral_class": orbit_class[state],
            "rotation_canonical": fixture.rotation_labels[state],
        }
        for state in range(STATE_COUNT)
    ]


def julia_graph_expected(graph: dict[str, Any]) -> dict[str, Any]:
    return graph


def jax_graph_expected(graph: dict[str, Any], transition: list[int]) -> dict[str, Any]:
    attractors = []
    for record in graph["attractors"]:
        cycle = record["cycle"]
        cycle_id = min(cycle)
        ordered = [cycle_id]
        current = cycle_id
        for _ in range(1, len(cycle)):
            current = transition[current]
            ordered.append(current)
        attractors.append(
            {
                "canonical_cycle_id": cycle_id,
                "period": len(cycle),
                "cycle_states_from_minimum": ordered,
                "basin_size": record["basin_size"],
                "scan_trace_prefix": [],
            }
        )
        entry = cycle_id
        for _ in range(STATE_COUNT):
            entry = transition[entry]
        current = entry
        for _ in range(len(cycle)):
            current = transition[current]
            attractors[-1]["scan_trace_prefix"].append(current)
    attractors.sort(key=lambda row: row["canonical_cycle_id"])
    return {
        "attractor_count": len(attractors),
        "sorted_basin_sizes": sorted(row["basin_size"] for row in attractors),
        "sorted_basin_period_signature": sorted([[row["basin_size"], row["period"]] for row in attractors]),
        "basin_total": sum(row["basin_size"] for row in attractors),
        "attractors": attractors,
    }


def validate_spec_fixture(packet: Packet, fixture: ExactFixture) -> None:
    expected = packet.spec["expected_controller_fixture_values"]
    require([len(partition) for partition in fixture.two_probe_partitions] == expected["behavioral_class_count_by_depth_two_probe"], "spec.expected.two_probe", "independent reconstruction differs")
    require([len(partition) for partition in fixture.weight_partitions] == expected["behavioral_class_count_by_depth_weight_only"], "spec.expected.weight_only", "independent reconstruction differs")
    disagreement = sum(left != right for left, right in zip(fixture.a_after_b, fixture.b_after_a))
    require(disagreement == expected["action_noncommuting_state_count"], "spec.expected.action_noncommuting_state_count", "independent reconstruction differs")
    require(fixture.graph_ab["sorted_basin_sizes"] == expected["A_after_B_sorted_basin_sizes"], "spec.expected.A_after_B_sorted_basin_sizes", "independent reconstruction differs")
    require(fixture.graph_ba["sorted_basin_sizes"] == expected["B_after_A_sorted_basin_sizes"], "spec.expected.B_after_A_sorted_basin_sizes", "independent reconstruction differs")
    require(len(fixture.rotation_orbits) == 14, "fixture.rotation_orbits", "expected 14")
    require(fixture.two_probe_partitions[-1] == fixture.rotation_orbits, "fixture.stable_partition", "does not equal rotation orbits")


def validate_julia(packet: Packet, fixture: ExactFixture) -> dict[str, Any]:
    julia = packet.julia
    require(julia["schema"] == "codex_ratchet.finite_probe_behavioral_object_engine.julia_result.v1", "julia.schema", "unexpected schema")
    require(julia["semantic_role"] == "semantic_owner", "julia.semantic_role", "role drift")
    require(julia["ran"] is True and julia["closed_json_validation"]["passed"] is True, "julia.closed_json_validation", "lane did not close")
    require(julia["fixture"]["state_table"] == expected_state_table(fixture), "julia.fixture.state_table", "does not match independent ECA/probe reconstruction")
    refinement = julia["behavioral_refinement"]
    require(refinement["two_probe_partitions_by_depth"] == fixture.two_probe_partitions, "julia.behavioral_refinement.two_probe_partitions_by_depth", "mismatch")
    require(refinement["weight_only_partitions_by_depth"] == fixture.weight_partitions, "julia.behavioral_refinement.weight_only_partitions_by_depth", "mismatch")
    require(refinement["stable_partition"] == fixture.two_probe_partitions[-1], "julia.behavioral_refinement.stable_partition", "mismatch")
    require(julia["presentation_symmetry"]["independently_computed_rotation_orbits"] == fixture.rotation_orbits, "julia.presentation_symmetry", "rotation orbit mismatch")
    quotient = julia["exact_quotient"]
    require(quotient["congruent"] is True, "julia.exact_quotient.congruent", "must be true")
    require(quotient["induced_A_rule30"] == fixture.induced_a, "julia.exact_quotient.induced_A_rule30", "mismatch")
    require(quotient["induced_B_rule110"] == fixture.induced_b, "julia.exact_quotient.induced_B_rule110", "mismatch")
    require(quotient["graph"]["strongly_connected_components"] == fixture.quotient_sccs, "julia.exact_quotient.graph.strongly_connected_components", "mismatch")
    require(quotient["graph"]["vertex_count"] == 14 and quotient["graph"]["edge_count"] == len(set(enumerate(fixture.induced_a)) | set(enumerate(fixture.induced_b))), "julia.exact_quotient.graph", "vertex or edge count mismatch")
    require(julia["functional_graphs"]["A_after_B"] == julia_graph_expected(fixture.graph_ab), "julia.functional_graphs.A_after_B", "exact cycle/basin mismatch")
    require(julia["functional_graphs"]["B_after_A"] == julia_graph_expected(fixture.graph_ba), "julia.functional_graphs.B_after_A", "exact cycle/basin mismatch")
    disagreement_states = [state for state in range(STATE_COUNT) if fixture.a_after_b[state] != fixture.b_after_a[state]]
    require(julia["functional_graphs"]["noncommuting_states"] == disagreement_states, "julia.functional_graphs.noncommuting_states", "mismatch")
    require(all(julia["tests"][name] is True for name in ("T1_behavioral_objects", "T2_rotation_identity", "T3_semiconjugacy", "T4_order_teeth", "T5_attractor_structure", "T6_probe_ablation", "T7_relabel_control")), "julia.tests", "an exact-core test is false")
    require(julia["tests"]["T9_engine_removal"] is False, "julia.tests.T9_engine_removal", "must remain red/unearned")
    require(julia["scientific_pass_before_closed_json_gate"] is False, "julia.scientific_pass_before_closed_json_gate", "must remain false on T9")
    require(julia["controls"]["mutated_transition_breaks_original_quotient"]["quotient_broken"] is True, "julia.controls.mutated_transition", "sanity check is not reported")
    return {"exact_fixture_match": True, "exact_cycle_basin_match": True, "semantic_owner_scope_preserved": True}


def validate_jax(packet: Packet, fixture: ExactFixture) -> dict[str, Any]:
    jax = packet.jax
    require(jax["schema"] == "codex_ratchet.finite_probe_behavioral_object_engine.jax_result.v1", "jax.schema", "unexpected schema")
    require(jax["engine_role"] == "batched_exhaustive_workhorse", "jax.engine_role", "role drift")
    require(jax["x64_enabled"] is True, "jax.x64_enabled", "must be true")
    expected_fixture = {
        "state_count": STATE_COUNT,
        "ring_size": RING_SIZE,
        "history_depth": MAX_DEPTH,
        "history_node_count": HISTORY_WIDTH,
        "state_encoding": packet.spec["fixture"]["state_encoding"],
        "A_rule": RULE_A,
        "B_rule": RULE_B,
        "A_transition": fixture.action_a,
        "B_transition": fixture.action_b,
    }
    require(jax["fixture"] == expected_fixture, "jax.fixture transition", "does not match independent ECA reconstruction")
    fingerprints = jax["history_fingerprints"]
    require(fingerprints["two_probe_depth_six_fingerprints"] == fixture.fingerprints, "jax.history_fingerprints.two_probe_depth_six_fingerprints", "mismatch")
    require(fingerprints["two_probe_class_count_by_depth"] == [len(item) for item in fixture.two_probe_partitions], "jax.history_fingerprints.two_probe_class_count_by_depth", "mismatch")
    require(fingerprints["weight_only_class_count_by_depth"] == [len(item) for item in fixture.weight_partitions], "jax.history_fingerprints.weight_only_class_count_by_depth", "mismatch")
    stable_labels = fixture.two_probe_labels[-1]
    representatives = [cell[0] for cell in fixture.two_probe_partitions[-1]]
    quotient = jax["quotient"]
    require(quotient["class_count"] == 14 and quotient["class_representatives"] == representatives, "jax quotient representatives", "mismatch")
    require(quotient["state_to_class_representative"] == stable_labels, "jax quotient state labels", "false or altered quotient")
    expected_induced_a = {str(rep): stable_labels[fixture.action_a[rep]] for rep in representatives}
    expected_induced_b = {str(rep): stable_labels[fixture.action_b[rep]] for rep in representatives}
    require(quotient["induced_A"] == expected_induced_a, "jax quotient induced_A", "mismatch")
    require(quotient["induced_B"] == expected_induced_b, "jax quotient induced_B", "mismatch")
    depth_zero = fixture.two_probe_labels[0]
    require(jax["semiconjugacy"]["stable_A"] == semiconjugacy(stable_labels, fixture.action_a), "jax.semiconjugacy.stable_A", "mismatch")
    require(jax["semiconjugacy"]["stable_B"] == semiconjugacy(stable_labels, fixture.action_b), "jax.semiconjugacy.stable_B", "mismatch")
    require(jax["semiconjugacy"]["depth_zero_A"] == semiconjugacy(depth_zero, fixture.action_a), "jax.semiconjugacy.depth_zero_A", "mismatch")
    require(jax["semiconjugacy"]["depth_zero_B"] == semiconjugacy(depth_zero, fixture.action_b), "jax.semiconjugacy.depth_zero_B", "mismatch")
    action_order = jax["action_order"]
    require(action_order["A_after_B_transition"] == fixture.a_after_b, "jax.action_order.A_after_B_transition", "mismatch")
    require(action_order["B_after_A_transition"] == fixture.b_after_a, "jax.action_order.B_after_A_transition", "mismatch")
    require(action_order["A_after_B_functional_graph"] == jax_graph_expected(fixture.graph_ab, fixture.a_after_b), "jax.action_order.A_after_B_functional_graph", "exact cycle/basin mismatch")
    require(action_order["B_after_A_functional_graph"] == jax_graph_expected(fixture.graph_ba, fixture.b_after_a), "jax.action_order.B_after_A_functional_graph", "exact cycle/basin mismatch")
    history_payload = {"states": list(range(STATE_COUNT)), "A": fixture.action_a, "B": fixture.action_b, "histories": fixture.histories}
    partition_payload = {"two_probe": fixture.two_probe_labels, "weight_only": fixture.weight_labels}
    composite_payload = {
        "A_after_B": fixture.a_after_b,
        "B_after_A": fixture.b_after_a,
        "A_after_B_graph": jax_graph_expected(fixture.graph_ab, fixture.a_after_b),
        "B_after_A_graph": jax_graph_expected(fixture.graph_ba, fixture.b_after_a),
    }
    require(jax["artifact_hashes"] == {
        "history_payload_sha256": canonical_hash(history_payload),
        "partition_payload_sha256": canonical_hash(partition_payload),
        "composite_payload_sha256": canonical_hash(composite_payload),
    }, "jax.artifact_hashes", "independent payload hash mismatch")
    require(all(jax["tests"][name]["pass"] is True for name in ("T1_behavioral_objects", "T2_rotation_identity", "T3_semiconjugacy", "T4_order_teeth", "T5_attractor_structure", "T6_probe_ablation", "T7_relabel_control")), "jax.tests", "an exact-core test is false")
    require(jax["tests"]["T9_engine_removal_boundary"]["pass"] is False, "jax.tests.T9_engine_removal_boundary", "must remain red/unearned")
    require("no executable engine-removal ablation" in jax["tests"]["T9_engine_removal_boundary"]["reason"], "jax.tests.T9_engine_removal_boundary.reason", "missing post-audit reason")
    return {"exact_fixture_match": True, "bounded_history_match": True, "exact_cycle_basin_match": True, "parity_scope_only": True}


def validate_metric(metric: Any, path: str) -> dict[str, Any]:
    metric = exact_keys(metric, METRIC_KEYS, path)
    require(type(metric["correct"]) is int and type(metric["count"]) is int and metric["count"] > 0, path, "invalid counts")
    require(math.isclose(metric["accuracy"], metric["correct"] / metric["count"], rel_tol=0.0, abs_tol=1e-15), f"{path}.accuracy", "does not equal correct/count")
    require(0.0 <= metric["accuracy"] <= 1.0, f"{path}.accuracy", "outside [0,1]")
    require(0.0 <= metric["positive_margin_fraction"] <= 1.0, f"{path}.positive_margin_fraction", "outside [0,1]")
    require(metric["margin_min"] <= metric["margin_median"] <= metric["margin_max"], path, "margin ordering invalid")
    require(metric["margin_min"] <= metric["margin_mean"] <= metric["margin_max"], path, "margin mean outside extrema")
    require(all(math.isfinite(metric[key]) for key in ("accuracy", "margin_min", "margin_mean", "margin_median", "margin_max", "positive_margin_fraction")), path, "contains non-finite metric")
    return metric


def validate_pytorch(packet: Packet, fixture: ExactFixture) -> dict[str, Any]:
    pytorch = packet.pytorch
    require(pytorch["schema"] == "codex_ratchet.pytorch_learned_perception_result.v1", "pytorch.schema", "unexpected schema")
    require(pytorch["engine_contract"] == {
        "mode": "pytorch_graph_network_packet",
        "role": "topology_dependent_orbit_fit_proxy",
        "semantic_owner": "julia",
        "local_gate": "topology-dependent fitting on isomorphic cyclic presentations only",
    }, "pytorch.engine_contract", "scope drift")
    require(pytorch["input_integrity_gates"]["preregistration_bound_at_runtime"] is True, "pytorch.input_integrity_gates.preregistration_bound_at_runtime", "must be true")
    require(pytorch["post_audit_interpretation"] == {
        "edge_erasure_is_the_meaningful_topology_dependence_control": True,
        "global_pooling_builds_relabel_invariance_into_the_architecture": True,
        "held_out_rotations_are_isomorphic_presentations": True,
        "shuffled_target_control_is_sanity_only": True,
        "unseen_object_generalization_earned": False,
    }, "pytorch.post_audit_interpretation", "post-audit demotion drift")
    target_table = class_indices(fixture.rotation_orbits)
    representatives = [cell[0] for cell in fixture.rotation_orbits]
    class_members = {str(index): cell for index, cell in enumerate(fixture.rotation_orbits)}
    target = pytorch["target_derivation"]
    require(target["representatives"] == representatives, "pytorch.target_derivation.representatives", "mismatch")
    require(target["class_members"] == class_members, "pytorch.target_derivation.class_members", "mismatch")
    require(target["target_table_state_0_through_63"] == target_table, "pytorch.target_derivation.target_table", "mismatch")
    require(target["target_table_sha256"] == canonical_hash(target_table), "pytorch.target_derivation.target_table_sha256", "mismatch")
    held_out = [state for state in range(STATE_COUNT) if state not in set(representatives)]
    split_manifest = {"train_states": representatives, "held_out_states": held_out}
    split = pytorch["split"]
    require(split["train_states"] == representatives and split["held_out_states"] == held_out, "pytorch.split", "is not one representative versus held rotations")
    require(split["training_count"] == 14 and split["held_out_count"] == 50 and split["state_overlap_count"] == 0, "pytorch.split", "count mismatch")
    require(split["split_sha256"] == canonical_hash(split_manifest), "pytorch.split.split_sha256", "mismatch")
    permutation = pytorch["training"]["target_permutation_for_shuffled_control"]
    require(sorted(permutation) == list(range(14)) and all(index != value for index, value in enumerate(permutation)), "pytorch.training.target_permutation", "must be a derangement")
    experiments = exact_keys(pytorch["experiments"], {"positive", "shuffled_target_control", "erased_ring_edge_control"}, "pytorch.experiments")
    for name, experiment in experiments.items():
        exact_keys(experiment, EXPERIMENT_KEYS, f"pytorch.experiments.{name}")
        held_metric = validate_metric(experiment["held_out_against_true_targets"], f"pytorch.experiments.{name}.held")
        validate_metric(experiment["training_against_assigned_targets"], f"pytorch.experiments.{name}.training")
        frozen = EXPECTED_PYTORCH_HELD[name]
        for key in ("accuracy", "correct", "count", "margin_min", "margin_sha256", "prediction_sha256"):
            require(held_metric[key] == frozen[key], f"pytorch.experiments.{name}.{key}", "frozen PyTorch metric receipt mismatch")
        require(experiment["model_state_sha256"] == frozen["model_state_sha256"], f"pytorch.experiments.{name}.model_state_sha256", "frozen PyTorch metric receipt mismatch")
    positive = experiments["positive"]["held_out_against_true_targets"]["accuracy"]
    shuffled = experiments["shuffled_target_control"]["held_out_against_true_targets"]["accuracy"]
    erased = experiments["erased_ring_edge_control"]["held_out_against_true_targets"]["accuracy"]
    require(pytorch["test_accuracy"] == positive and pytorch["test_margin"] == experiments["positive"]["held_out_against_true_targets"], "pytorch.test_accuracy", "duplicate metric mismatch")
    require(pytorch["control_gaps"] == {
        "positive_minus_shuffled_target_accuracy": positive - shuffled,
        "positive_minus_erased_ring_edge_accuracy": positive - erased,
    }, "pytorch.control_gaps", "not reconstructed from experiment metrics")
    require(pytorch["preregistered_T8_gates"] == {
        "held_out_rotation_accuracy_at_least_0_90": positive >= 0.90,
        "shuffled_target_gap_at_least_0_25": positive - shuffled >= 0.25,
        "erased_ring_edge_gap_at_least_0_25": positive - erased >= 0.25,
    }, "pytorch.preregistered_T8_gates", "not reconstructed from metrics")
    graph_manifest = {
        "ring_size": RING_SIZE,
        "positive_edge_index": [list(range(RING_SIZE)), [1, 2, 3, 4, 5, 0]],
        "erased_edge_index": [[], []],
        "state_bits": [[bit_at(state, site) for site in range(RING_SIZE)] for state in range(STATE_COUNT)],
    }
    controls_manifest = {
        "shuffled_target_permutation": permutation,
        "erased_edge_index": [[], []],
        "shared_model_seed": pytorch["training"]["model_seed"],
        "shared_epochs": pytorch["training"]["epochs"],
    }
    require(pytorch["hashes"]["target_table_sha256"] == canonical_hash(target_table), "pytorch.hashes.target_table_sha256", "mismatch")
    require(pytorch["hashes"]["split_sha256"] == canonical_hash(split_manifest), "pytorch.hashes.split_sha256", "mismatch")
    require(pytorch["hashes"]["graph_fixture_sha256"] == canonical_hash(graph_manifest), "pytorch.hashes.graph_fixture_sha256", "mismatch")
    require(pytorch["hashes"]["controls_sha256"] == canonical_hash(controls_manifest), "pytorch.hashes.controls_sha256", "mismatch")
    require(experiments["positive"]["directed_edge_count_per_graph"] == 6 and experiments["positive"]["erased_ring_edges"] is False, "pytorch.experiments.positive", "topology scope mismatch")
    require(experiments["erased_ring_edge_control"]["directed_edge_count_per_graph"] == 0 and experiments["erased_ring_edge_control"]["erased_ring_edges"] is True, "pytorch.experiments.erased_ring_edge_control", "topology control mismatch")
    return {
        "orbit_targets_reconstructed": True,
        "held_presentations_are_isomorphic_rotations": True,
        "positive_accuracy": positive,
        "shuffled_accuracy": shuffled,
        "erased_edge_accuracy": erased,
        "topology_dependence_gap": positive - erased,
        "accepted_scope": "topology-dependent orbit fitting only; not unseen-object generalization",
        "shuffled_target_control_role": "sanity_only",
        "edge_erasure_control_role": "meaningful_topology_dependence_control",
    }


def validate_payloads(packet: Packet, *, enforce_hashes: bool) -> dict[str, Any]:
    validate_identity_and_ceilings(packet)
    hashes = validate_hashes() if enforce_hashes else {}
    source_receipt = validate_source_bindings_and_peer_reads(packet)
    fixture = build_fixture()
    validate_spec_fixture(packet, fixture)
    julia = validate_julia(packet, fixture)
    jax = validate_jax(packet, fixture)
    pytorch = validate_pytorch(packet, fixture)
    require(packet.julia["behavioral_refinement"]["stable_partition"] == fixture.two_probe_partitions[-1], "parity.julia", "stable partition mismatch")
    require(packet.jax["quotient"]["state_to_class_representative"] == fixture.two_probe_labels[-1], "parity.jax", "stable partition mismatch")
    return {
        "frozen_hashes": hashes,
        "source_and_peer_read_enforcement": source_receipt,
        "independent_fixture": {
            "state_count": STATE_COUNT,
            "A_rule": RULE_A,
            "B_rule": RULE_B,
            "two_probe_class_count_by_depth": [len(item) for item in fixture.two_probe_partitions],
            "weight_only_class_count_by_depth": [len(item) for item in fixture.weight_partitions],
            "stable_partition": fixture.two_probe_partitions[-1],
            "rotation_orbits": fixture.rotation_orbits,
            "quotient_sccs": fixture.quotient_sccs,
            "A_after_B": fixture.graph_ab,
            "B_after_A": fixture.graph_ba,
        },
        "julia_exact_semantic_owner": julia,
        "jax_batched_exhaustive_parity": jax,
        "julia_jax_exact_fixture_parity": True,
        "pytorch_learned_proxy": pytorch,
    }


def run_mutation_self_tests(packet: Packet) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def rejected(name: str, mutate: Callable[[Packet], None], expected_fragment: str) -> None:
        candidate = copy.deepcopy(packet)
        mutate(candidate)
        observed = ""
        try:
            validate_payloads(candidate, enforce_hashes=False)
        except ValidationError as exc:
            observed = str(exc)
        cases.append({
            "name": name,
            "expected_error_fragment": expected_fragment,
            "observed_error": observed,
            "validator_rejected": bool(observed),
            "pass": bool(observed) and expected_fragment in observed,
        })

    rejected(
        "result_alteration",
        lambda candidate: candidate.jax["fixture"]["A_transition"].__setitem__(1, 0),
        "jax.fixture transition",
    )
    rejected(
        "ceiling_removal",
        lambda candidate: candidate.jax.pop("claim_ceiling"),
        "closed schema keys differ",
    )
    rejected(
        "false_quotient",
        lambda candidate: candidate.jax["quotient"]["state_to_class_representative"].__setitem__(2, 2),
        "jax quotient state labels",
    )

    def fabricate_accuracy(candidate: Packet) -> None:
        metric = candidate.pytorch["experiments"]["positive"]["held_out_against_true_targets"]
        metric["accuracy"] = 0.98
        metric["correct"] = 49
        candidate.pytorch["test_accuracy"] = 0.98
        candidate.pytorch["test_margin"] = copy.deepcopy(metric)
        candidate.pytorch["control_gaps"]["positive_minus_shuffled_target_accuracy"] = 0.98
        candidate.pytorch["control_gaps"]["positive_minus_erased_ring_edge_accuracy"] = 0.54

    rejected("pytorch_accuracy_fabrication", fabricate_accuracy, "frozen PyTorch metric receipt mismatch")

    def fabricate_control(candidate: Packet) -> None:
        metric = candidate.pytorch["experiments"]["erased_ring_edge_control"]["held_out_against_true_targets"]
        metric["accuracy"] = 0.0
        metric["correct"] = 0
        candidate.pytorch["control_gaps"]["positive_minus_erased_ring_edge_accuracy"] = 1.0

    rejected("pytorch_control_fabrication", fabricate_control, "frozen PyTorch metric receipt mismatch")
    return {
        "schema": f"codex_ratchet.{SIM_ID}.mutation_self_tests.v1",
        "kind": "in_memory_result_corruption",
        "cases": cases,
        "case_count": len(cases),
        "all_pass": all(case["pass"] for case in cases),
    }


def success_receipt(packet: Packet) -> dict[str, Any]:
    checks = validate_payloads(packet, enforce_hashes=True)
    mutation_tests = run_mutation_self_tests(packet)
    require(mutation_tests["all_pass"], "mutation_self_tests", "one or more corruptions escaped rejection")
    pytorch_prereg_read = checks["source_and_peer_read_enforcement"]["pytorch_preregistration_runtime_read"]
    return {
        "schema": f"codex_ratchet.{SIM_ID}.independent_validation.v1",
        "sim_id": SIM_ID,
        "validator_role": "independent_mechanical_gatekeeper_and_semantic_fabrication_auditor",
        "classification": CLASSIFICATION,
        "artifact_validation_all_pass": True,
        "validator_all_pass": True,
        "all_scientific_gates_pass": False,
        "accepted_scientific_label": ACCEPTED_LABEL,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "preregistered_test_projection": {
            "T1_behavioral_objects": True,
            "T2_rotation_identity": True,
            "T3_semiconjugacy": True,
            "T4_order_teeth": True,
            "T5_attractor_structure": True,
            "T6_probe_ablation": True,
            "T7_relabel_control": True,
            "T8_topology_dependent_orbit_fit_only": True,
            "T9_engine_removal_nonredundancy": False,
        },
        "engine_role_ceilings": {
            "julia": "exact semantic owner for this finite fixture only",
            "jax": "independent bounded-exhaustive parity and controls for this finite fixture only",
            "pytorch": "topology-dependent cyclic-orbit fitting and edge-dependence metrics only",
            "nonredundant_three_engine_claim": False,
            "removing_pytorch": "demotes topology-dependent learned-fit evidence only",
            "removing_jax": "demotes bounded-history and independent exhaustive parity evidence only",
            "removing_julia": "removes packet authority for exact object, quotient, SCC, cycle, and basin claims",
        },
        "fabrication_audit": {
            "found_fabrication": True,
            "layer": "semantic_claim_layer",
            "findings": [
                "PyTorch trains on one representative per orbit and tests only isomorphic rotations under invariant pooling; 1.0 accuracy is topology-dependent orbit fitting, not unseen-object generalization.",
                "The shuffled-target control is constructed and the transition mutation deliberately chooses a cross-class target; both are sanity_only.",
                "The edge-erasure accuracy drop from 1.0 to 0.44 is a meaningful topology-dependence control.",
                "T9 engine removal was not executed; the final Julia and JAX receipts explicitly keep T9 false, so nonredundant-engine evidence is unearned.",
                "Julia/JAX exact finite-fixture parity remains valid but does not prove nonredundant roles or admission.",
                "PyTorch does not read the preregistration receipt at runtime in the frozen source." if not pytorch_prereg_read else "PyTorch runtime preregistration receipt read is present in the frozen source.",
            ],
            "sanity_only_controls": ["shuffled PyTorch targets", "deterministic cross-class transition mutation"],
            "meaningful_controls": ["PyTorch ring-edge erasure: held accuracy 1.0 to 0.44"],
        },
        "checks": checks,
        "mutation_self_tests": mutation_tests,
        "claim_ceiling": "Exact finite ECA behavioral quotient, rotation-orbit identity, composite cycles/basins, Julia/JAX parity, and topology-dependent PyG orbit fit only; no nonredundant-engine, unseen-object, QIT, stage, Axis0, general-perception, ontology, physics, or consciousness claim.",
        "blocked_consumers": packet.spec["blocked_consumers"],
        "validator_source_sha256": sha256(Path(__file__)),
    }


def failure_receipt(error: Exception) -> dict[str, Any]:
    observed_hashes: dict[str, str | None] = {}
    for path in FROZEN_HASHES:
        try:
            observed_hashes[relative(path)] = sha256(path)
        except OSError:
            observed_hashes[relative(path)] = None
    return {
        "schema": f"codex_ratchet.{SIM_ID}.independent_validation.v1",
        "sim_id": SIM_ID,
        "validator_role": "independent_mechanical_gatekeeper_and_semantic_fabrication_auditor",
        "classification": CLASSIFICATION,
        "artifact_validation_all_pass": False,
        "validator_all_pass": False,
        "all_scientific_gates_pass": False,
        "accepted_scientific_label": BLOCKED_LABEL,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "error": f"{type(error).__name__}: {error}",
        "observed_hashes": observed_hashes,
        "mutation_self_tests": "not_accepted_after_base_validation_failure",
        "claim_ceiling": "No scientific claim is accepted after mechanical validation failure.",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        receipt = success_receipt(load_packet())
    except Exception as exc:
        receipt = failure_receipt(exc)
    strict_write_json(args.output, receipt)
    print(json.dumps({
        "validator_all_pass": receipt["validator_all_pass"],
        "all_scientific_gates_pass": receipt["all_scientific_gates_pass"],
        "accepted_scientific_label": receipt["accepted_scientific_label"],
        "output": str(args.output),
    }, sort_keys=True, allow_nan=False))
    return 0 if receipt["validator_all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
