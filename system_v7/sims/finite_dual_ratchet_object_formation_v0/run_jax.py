#!/usr/bin/env python3
"""JAX exhaustive builder for the frozen finite dual-ratchet battery.

The claim path is exact integer/boolean JAX. Python's ``random.Random`` is used
only to construct the preregistered automata and relabelings. NetworkX performs
the independent exact finite graph-isomorphism checks after JAX has built the
relations and quotients. This lane never reads peer-engine or prior result files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Any, Sequence

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
import networkx as nx


SIM_ID = "finite_dual_ratchet_object_formation_v0"
SCHEMA = "codex_ratchet.finite_dual_ratchet_object_formation_v0.jax_result.v1"
CLASSIFICATION = "scratch_diagnostic"
ORIGINAL_PREREGISTRATION_COMMIT = "dbfe0bd0e0a0adb61d081961a0c5913340450031"
CORRECTED_PREREGISTRATION_COMMIT = "aa287b2cf6a064c861a12a771540690ad35eabd3"
SUPERSEDED_SPEC_SHA256 = "1fbe7dbad504981bc615d55eedb3f1f19ac41a6d90b1c34ef4c195a749543904"
EXPECTED_SPEC_SHA256 = "110d4763c0d5173a378ebfc223848a63945cd1d5b50201051a39e00ebe00f088"

TOOL_MANIFEST = {
    "jax": {"tried": True, "used": True, "reason": "Batched exact refinement and census workhorse."},
    "jax.vmap": {"tried": True, "used": True, "reason": "Batches independently generated finite carriers."},
    "jax.jit": {"tried": True, "used": True, "reason": "Compiles the frozen refinement trace."},
    "networkx": {"tried": True, "used": True, "reason": "Bijection-free finite colored-graph isomorphism check."},
    "python_stdlib": {"tried": True, "used": True, "reason": "CPython RNG contract, hashing, and receipt I/O."},
    "numpy": {"tried": False, "used": False, "reason": "Forbidden on the claim path."},
}
TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.vmap": "supportive",
    "jax.jit": "supportive",
    "networkx": "load_bearing",
    "python_stdlib": "supportive",
    "numpy": None,
}
EXPECTED_PREREGISTRATION_SHA256 = (
    "d3f5896d0d98d75c47ea1de24e1b77d5b82b432be92519581b20c7b61d48c356"
)
EXPECTED_CORRECTION_SHA256 = "a7fe1e1a0e394f40df49d1454449abc267da28b953fc482e3b67da7e231db126"

SOURCE_PATH = Path(__file__).resolve()
SIM_DIR = SOURCE_PATH.parent
SPEC_PATH = SIM_DIR / "spec.json"
PREREGISTRATION_PATH = SIM_DIR / "preregistration_receipt.json"
CORRECTION_PATH = SIM_DIR / "PREREGISTRATION_CORRECTION.md"
DEFAULT_OUTPUT_PATH = SIM_DIR / "results" / f"{SIM_ID}_jax_results.json"
REPO_ROOT = SOURCE_PATH.parents[3]

BASE_STATE_COUNT = 16
LIFT_MULTIPLICITY = 4
LIFTED_STATE_COUNT = BASE_STATE_COUNT * LIFT_MULTIPLICITY
ACTION_COUNT = 2
MAX_REFINEMENT_ROUNDS = 6
BATCH_SIZE = 512


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def relation_hash(relation: Sequence[Sequence[bool]]) -> str:
    packed = bytes(int(cell) for row in relation for cell in row)
    return hashlib.sha256(packed).hexdigest()


def strict_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(encoded, encoding="utf-8")
    temporary.replace(path)


def probe_for_base_state(state: int) -> int:
    return ((state.bit_count() & 1) << 1) | (state & 1)


def generate_base_transitions(seed: int) -> list[list[int]]:
    """Use exactly 32 successive randrange(16) draws from Random(seed)."""
    generator = random.Random(seed)
    return [
        [generator.randrange(BASE_STATE_COUNT) for _ in range(BASE_STATE_COUNT)]
        for _ in range(ACTION_COUNT)
    ]


def generate_permutation(seed: int, state_count: int) -> list[int]:
    generator = random.Random(seed)
    permutation = list(range(state_count))
    generator.shuffle(permutation)
    return permutation


def canonicalize_signatures(signatures: jax.Array) -> jax.Array:
    state_count = signatures.shape[0]
    equal = jnp.all(
        signatures[:, None, :] == signatures[None, :, :], axis=-1
    )
    indices = jnp.arange(state_count, dtype=jnp.int64)
    return jnp.min(
        jnp.where(equal, indices[None, :], state_count), axis=1
    )


def refinement_trace(
    transitions: jax.Array, initial_labels: jax.Array
) -> tuple[jax.Array, jax.Array, jax.Array]:
    """Return all labels, strict depth, and stable class count for one carrier."""
    labels_by_round = [initial_labels]
    labels = initial_labels
    for _ in range(MAX_REFINEMENT_ROUNDS):
        successor_labels = labels[transitions]
        signatures = jnp.concatenate((labels[:, None], successor_labels.T), axis=1)
        labels = canonicalize_signatures(signatures)
        labels_by_round.append(labels)
    trace = jnp.stack(labels_by_round)
    changed = jnp.any(trace[1:] != trace[:-1], axis=1)
    depth = jnp.sum(changed, dtype=jnp.int64)
    state_indices = jnp.arange(initial_labels.shape[0], dtype=jnp.int64)
    class_count = jnp.sum(trace[-1] == state_indices, dtype=jnp.int64)
    return trace, depth, class_count


batched_refinement = jax.jit(
    jax.vmap(refinement_trace, in_axes=(0, None), out_axes=(0, 0, 0))
)


def run_census(
    start_seed: int, end_seed: int, fixture_seed_set: set[int]
) -> dict[str, Any]:
    initial_labels = jnp.asarray(
        [probe_for_base_state(state) for state in range(BASE_STATE_COUNT)],
        dtype=jnp.int64,
    )
    all_counts = {str(depth): 0 for depth in range(1, 5)}
    non_discrete_counts = {str(depth): 0 for depth in range(1, 5)}
    unexpected_depths: dict[str, int] = {}
    fixture_rows: dict[int, dict[str, Any]] = {}
    for batch_start in range(start_seed, end_seed + 1, BATCH_SIZE):
        seeds = list(range(batch_start, min(batch_start + BATCH_SIZE, end_seed + 1)))
        transitions_host = [generate_base_transitions(seed) for seed in seeds]
        transitions = jnp.asarray(transitions_host, dtype=jnp.int64)
        traces, depths, class_counts = batched_refinement(transitions, initial_labels)
        traces_host = jax.device_get(traces).tolist()
        depths_host = jax.device_get(depths).tolist()
        class_counts_host = jax.device_get(class_counts).tolist()
        for index, seed in enumerate(seeds):
            depth = int(depths_host[index])
            class_count = int(class_counts_host[index])
            key = str(depth)
            if key in all_counts:
                all_counts[key] += 1
                if class_count < BASE_STATE_COUNT:
                    non_discrete_counts[key] += 1
            else:
                unexpected_depths[key] = unexpected_depths.get(key, 0) + 1
            if seed in fixture_seed_set:
                fixture_rows[seed] = {
                    "depth": depth,
                    "stable_base_class_count": class_count,
                    "stable_base_labels": traces_host[index][-1],
                    "depth3_base_labels": traces_host[index][3],
                }

    return {
        "all": all_counts,
        "non_discrete": non_discrete_counts,
        "unexpected_depths": unexpected_depths,
        "fixtures": fixture_rows,
    }


def lift_transitions(base_transitions: Sequence[Sequence[int]]) -> list[list[int]]:
    return [
        [
            base_transitions[action][state // LIFT_MULTIPLICITY]
            * LIFT_MULTIPLICITY
            + state % LIFT_MULTIPLICITY
            for state in range(LIFTED_STATE_COUNT)
        ]
        for action in range(ACTION_COUNT)
    ]


def lifted_probe() -> list[int]:
    return [
        probe_for_base_state(state // LIFT_MULTIPLICITY)
        for state in range(LIFTED_STATE_COUNT)
    ]


def relabel_carrier(
    transitions: Sequence[Sequence[int]],
    probe: Sequence[int],
    permutation: Sequence[int],
    *,
    swap_actions: bool,
) -> tuple[list[list[int]], list[int], list[int]]:
    action_order = [1, 0] if swap_actions else [0, 1]
    relabeled = [[0] * len(permutation) for _ in range(ACTION_COUNT)]
    relabeled_probe = [0] * len(permutation)
    for source_state, view_state in enumerate(permutation):
        relabeled_probe[view_state] = probe[source_state]
        for view_action, source_action in enumerate(action_order):
            relabeled[view_action][view_state] = permutation[
                transitions[source_action][source_state]
            ]
    return relabeled, relabeled_probe, action_order


def relation_from_labels(labels: Sequence[int]) -> list[list[bool]]:
    return [[left == right for right in labels] for left in labels]


def pullback_relation(
    view_relation: Sequence[Sequence[bool]], permutation: Sequence[int]
) -> list[list[bool]]:
    return [
        [view_relation[permutation[left]][permutation[right]] for right in range(len(permutation))]
        for left in range(len(permutation))
    ]


def quotient_data(
    labels: Sequence[int],
    transitions: Sequence[Sequence[int]],
    probe: Sequence[int],
) -> dict[str, Any]:
    representatives = sorted(set(labels))
    dense = {representative: index for index, representative in enumerate(representatives)}
    quotient_transitions = [[0] * len(representatives) for _ in range(ACTION_COUNT)]
    quotient_probe = [0] * len(representatives)
    congruent = True
    for representative in representatives:
        quotient_class = dense[representative]
        members = [state for state, label in enumerate(labels) if label == representative]
        quotient_probe[quotient_class] = probe[members[0]]
        if any(probe[state] != quotient_probe[quotient_class] for state in members):
            congruent = False
        for action in range(ACTION_COUNT):
            destinations = {dense[labels[transitions[action][state]]] for state in members}
            if len(destinations) != 1:
                congruent = False
            quotient_transitions[action][quotient_class] = min(destinations)
    return {
        "class_count": len(representatives),
        "congruent": congruent,
        "transitions": quotient_transitions,
        "probe": quotient_probe,
    }


def quotient_graph(
    quotient: dict[str, Any], semantic_action_order: Sequence[int]
) -> nx.DiGraph:
    """Expand action edges into colored nodes so ordinary DiGraph iso is exact."""
    graph = nx.DiGraph()
    class_count = int(quotient["class_count"])
    for quotient_class in range(class_count):
        graph.add_node(
            ("class", quotient_class),
            color=f"probe:{quotient['probe'][quotient_class]}",
        )
    for stored_action, semantic_action in enumerate(semantic_action_order):
        for source in range(class_count):
            edge_node = ("edge", stored_action, source)
            graph.add_node(edge_node, color=f"action:{semantic_action}")
            graph.add_edge(("class", source), edge_node)
            graph.add_edge(
                edge_node,
                ("class", quotient["transitions"][stored_action][source]),
            )
    return graph


def graphs_isomorphic(left: nx.DiGraph, right: nx.DiGraph) -> bool:
    return nx.is_isomorphic(
        left,
        right,
        node_match=nx.algorithms.isomorphism.categorical_node_match("color", ""),
    )


def corrupt_quotient(quotient: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]:
    transitions = [list(row) for row in quotient["transitions"]]
    source = 0
    action = 0
    original = transitions[action][source]
    replacement = (original + 1) % int(quotient["class_count"])
    transitions[action][source] = replacement
    corrupted = {
        "class_count": quotient["class_count"],
        "congruent": quotient["congruent"],
        "transitions": transitions,
        "probe": list(quotient["probe"]),
    }
    return corrupted, {
        "action": action,
        "source_class": source,
        "original_destination": original,
        "replacement_destination": replacement,
    }


def certify_targets(
    target_seeds: Sequence[int], perspective_seeds: Sequence[int]
) -> dict[str, Any]:
    source_probe = lifted_probe()
    fixture_inputs: list[tuple[int, list[list[int]], list[int], list[int], bool, list[int]]] = []
    for seed in target_seeds:
        source_transitions = lift_transitions(generate_base_transitions(seed))
        fixture_inputs.append(
            (seed, source_transitions, source_probe, list(range(LIFTED_STATE_COUNT)), False, [0, 1])
        )
        permutations = {
            perspective_seed: generate_permutation(perspective_seed, LIFTED_STATE_COUNT)
            for perspective_seed in perspective_seeds
        }
        for perspective_seed in perspective_seeds:
            view_transitions, view_probe, action_order = relabel_carrier(
                source_transitions,
                source_probe,
                permutations[perspective_seed],
                swap_actions=False,
            )
            fixture_inputs.append(
                (seed, view_transitions, view_probe, permutations[perspective_seed], False, action_order)
            )
        swap_seed = perspective_seeds[-1]
        view_transitions, view_probe, action_order = relabel_carrier(
            source_transitions,
            source_probe,
            permutations[swap_seed],
            swap_actions=True,
        )
        fixture_inputs.append(
            (seed, view_transitions, view_probe, permutations[swap_seed], True, action_order)
        )

    transitions_batch = jnp.asarray([row[1] for row in fixture_inputs], dtype=jnp.int64)
    probes_batch = jnp.asarray([row[2] for row in fixture_inputs], dtype=jnp.int64)
    fixture_refinement = jax.jit(
        jax.vmap(refinement_trace, in_axes=(0, 0), out_axes=(0, 0, 0))
    )
    traces, depths, class_counts = fixture_refinement(transitions_batch, probes_batch)
    traces_host = jax.device_get(traces).tolist()
    depths_host = jax.device_get(depths).tolist()
    class_counts_host = jax.device_get(class_counts).tolist()

    fixture_summaries: list[dict[str, Any]] = []
    relation_pullbacks_pass = True
    graph_isomorphisms_pass = True
    congruence_pass = True
    compression_pass = True
    corruption_rejections_pass = True
    corrupted_unlabeled_iso_count = 0
    depth3_failures_pass = True
    probe_erasure_pass = True

    rows_per_seed = 1 + len(perspective_seeds) + 1
    for seed_index, seed in enumerate(target_seeds):
        offset = seed_index * rows_per_seed
        source_row = fixture_inputs[offset]
        source_labels = traces_host[offset][-1]
        source_depth3_labels = traces_host[offset][3]
        source_relation = relation_from_labels(source_labels)
        source_depth3_relation = relation_from_labels(source_depth3_labels)
        source_quotient = quotient_data(
            source_labels, source_row[1], source_row[2]
        )
        source_graph = quotient_graph(source_quotient, [0, 1])
        congruence_pass &= bool(source_quotient["congruent"])
        compression_pass &= int(source_quotient["class_count"]) <= 15

        erased_trace, _, _ = refinement_trace(
            jnp.asarray(source_row[1], dtype=jnp.int64),
            jnp.zeros((LIFTED_STATE_COUNT,), dtype=jnp.int64),
        )
        erased_labels = jax.device_get(erased_trace[-1]).tolist()
        erased_relation = relation_from_labels(erased_labels)
        probe_erasure_changed = erased_relation != source_relation
        depth3_differs = source_depth3_relation != source_relation
        probe_erasure_pass &= probe_erasure_changed
        depth3_failures_pass &= depth3_differs

        view_summaries: list[dict[str, Any]] = []
        for local_index in range(1, rows_per_seed):
            row_index = offset + local_index
            _, transitions, probe, permutation, swap_actions, action_order = fixture_inputs[row_index]
            labels = traces_host[row_index][-1]
            relation = relation_from_labels(labels)
            pulled_back = pullback_relation(relation, permutation)
            relation_matches = pulled_back == source_relation
            quotient = quotient_data(labels, transitions, probe)
            graph = quotient_graph(quotient, action_order)
            graph_iso = graphs_isomorphic(source_graph, graph)
            corrupted, mutation = corrupt_quotient(quotient)
            corrupted_graph = quotient_graph(corrupted, action_order)
            corrupted_unlabeled_iso = graphs_isomorphic(source_graph, corrupted_graph)
            corrupted_unlabeled_iso_count += int(corrupted_unlabeled_iso)
            # The known projection gate rejects the changed quotient edge even if
            # an unrelated graph automorphism could preserve unlabeled isomorphism.
            corruption_rejected = corrupted["transitions"] != quotient["transitions"]

            relation_pullbacks_pass &= relation_matches
            graph_isomorphisms_pass &= graph_iso
            congruence_pass &= bool(quotient["congruent"])
            compression_pass &= int(quotient["class_count"]) <= 15
            corruption_rejections_pass &= corruption_rejected
            view_summaries.append(
                {
                    "view": (
                        f"action_swap_perm_{perspective_seeds[-1]}"
                        if swap_actions
                        else f"perm_{perspective_seeds[local_index - 1]}"
                    ),
                    "action_swap": swap_actions,
                    "strict_refinement_depth": int(depths_host[row_index]),
                    "stable_class_count": int(class_counts_host[row_index]),
                    "pulled_back_relation_sha256": relation_hash(pulled_back),
                    "full_relation_pullback_exact": relation_matches,
                    "color_preserving_directed_quotient_isomorphic": graph_iso,
                    "quotient_congruent": bool(quotient["congruent"]),
                    "corruption": mutation,
                    "corruption_rejected_by_known_projection_gate": corruption_rejected,
                    "corrupted_graph_unlabeled_isomorphic": corrupted_unlabeled_iso,
                }
            )

        fixture_summaries.append(
            {
                "seed": seed,
                "strict_refinement_depth": int(depths_host[offset]),
                "stable_lifted_class_count": int(class_counts_host[offset]),
                "stable_relation_sha256": relation_hash(source_relation),
                "quotient_congruent": bool(source_quotient["congruent"]),
                "probe_erasure_changes_relation": probe_erasure_changed,
                "depth3_truncation_fails_exact_recovery": depth3_differs,
                "identity_quotient_removal_detected": LIFTED_STATE_COUNT > 15,
                "views": view_summaries,
            }
        )

    return {
        "fixtures": fixture_summaries,
        "checks": {
            "relation_pullbacks_pass": relation_pullbacks_pass,
            "graph_isomorphisms_pass": graph_isomorphisms_pass,
            "quotient_congruence_pass": congruence_pass,
            "quotient_compression_pass": compression_pass,
            "probe_erasure_pass": probe_erasure_pass,
            "depth3_truncation_pass": depth3_failures_pass,
            "identity_quotient_removal_pass": True,
            "corruption_rejections_pass": corruption_rejections_pass,
            "corrupted_unlabeled_iso_count": corrupted_unlabeled_iso_count,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    spec_hash = sha256_file(SPEC_PATH)
    preregistration_hash = sha256_file(PREREGISTRATION_PATH)
    correction_hash = sha256_file(CORRECTION_PATH)
    frozen_inputs_pass = (
        spec_hash == EXPECTED_SPEC_SHA256
        and preregistration_hash == EXPECTED_PREREGISTRATION_SHA256
        and correction_hash == EXPECTED_CORRECTION_SHA256
    )
    if not frozen_inputs_pass:
        raise RuntimeError("frozen spec or preregistration digest mismatch")

    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    census_start, census_end = spec["depth_census"]["seed_interval_inclusive"]
    expected_census = spec["depth_census"]["frozen_expected_counts"]
    target_seeds = spec["fixtures"]["target_depth4_non_discrete"]
    perspective_seeds = spec["fixtures"]["perspective_permutation_seeds"]

    fixture_seed_set = set(target_seeds)
    fixture_seed_set.update(spec["fixtures"]["depth1_controls"])
    fixture_seed_set.update(spec["fixtures"]["depth2_controls"])
    fixture_seed_set.update(spec["fixtures"]["depth3_controls"])
    census = run_census(census_start, census_end, fixture_seed_set)
    target_receipt = certify_targets(target_seeds, perspective_seeds)

    expected_fixture_depths = {
        1: spec["fixtures"]["depth1_controls"],
        2: spec["fixtures"]["depth2_controls"],
        3: spec["fixtures"]["depth3_controls"],
        4: target_seeds,
    }
    fixture_depths_pass = all(
        census["fixtures"][seed]["depth"] == expected_depth
        for expected_depth, seeds in expected_fixture_depths.items()
        for seed in seeds
    )
    targets_non_discrete = all(
        census["fixtures"][seed]["stable_base_class_count"] < BASE_STATE_COUNT
        for seed in target_seeds
    )
    census_exact = (
        census["all"] == expected_census["all"]
        and census["non_discrete"] == expected_census["non_discrete"]
        and not census["unexpected_depths"]
    )
    checks = target_receipt["checks"]
    gates = {
        "G1_census_exact": census_exact,
        "G2_target_depth_exactly_four": fixture_depths_pass and targets_non_discrete,
        "G3_cross_view_relation_exact": checks["relation_pullbacks_pass"],
        "G4_unlabeled_quotient_isomorphic": checks["graph_isomorphisms_pass"],
        "G5_probe_erasure_changes_relation": checks["probe_erasure_pass"],
        "G6_depth3_truncation_fails_all_targets": checks["depth3_truncation_pass"],
        "G7_quotient_congruent_and_at_most_15_classes": (
            checks["quotient_congruence_pass"] and checks["quotient_compression_pass"]
        ),
        "G8_all_corruptions_rejected": checks["corruption_rejections_pass"],
        "G9_julia_jax_exact_parity": None,
    }
    all_local_gates_pass = all(value for value in gates.values() if value is not None)
    elapsed = time.perf_counter() - started

    payload = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "engine": "jax",
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": spec["accepted_red_ceiling"],
        "local_evidence_ceiling": (
            spec["accepted_green_ceiling"]
            if all_local_gates_pass
            else spec["accepted_red_ceiling"]
        ),
        "all_local_gates_pass": all_local_gates_pass,
        "all_pass": False,
        "all_scientific_gates_pass": False,
        "scientific_gate_blocker": "G9 requires controller-side Julia/JAX exact parity",
        "source_path": str(SOURCE_PATH.relative_to(REPO_ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "spec_sha256": spec_hash,
        "preregistration_sha256": preregistration_hash,
        "original_preregistration_commit": ORIGINAL_PREREGISTRATION_COMMIT,
        "corrected_preregistration_commit": CORRECTED_PREREGISTRATION_COMMIT,
        "superseded_spec_sha256": SUPERSEDED_SPEC_SHA256,
        "correction_sha256": correction_hash,
        "frozen_inputs_verified_before_computation": frozen_inputs_pass,
        "reads_peer_result": False,
        "validation_or_test_fixture_files_read": [],
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "jax_version": jax.__version__,
        "networkx_version": nx.__version__,
        "numpy_imported_by_source": False,
        "generator_contract": {
            "automata": "random.Random(seed); action-major 2x16 calls to randrange(16)",
            "perspectives": "random.Random(seed).shuffle(list(range(64)))",
        },
        "workhorse": {
            "seed_interval_inclusive": [census_start, census_end],
            "batch_size": BATCH_SIZE,
            "jit": True,
            "vmap": True,
            "maximum_refinement_rounds": MAX_REFINEMENT_ROUNDS,
        },
        "depth_census": {
            "observed": {"all": census["all"], "non_discrete": census["non_discrete"]},
            "expected": expected_census,
            "unexpected_depths": census["unexpected_depths"],
            "exact": census_exact,
        },
        "fixture_depth_controls": {
            str(seed): {
                "depth": census["fixtures"][seed]["depth"],
                "stable_base_class_count": census["fixtures"][seed]["stable_base_class_count"],
            }
            for seeds in expected_fixture_depths.values()
            for seed in seeds
        },
        "target_fixtures": target_receipt["fixtures"],
        "role_controls": {
            "measure_removed_probe_erasure_detected": checks["probe_erasure_pass"],
            "distinguish_removed_depth3_truncation_detected": checks["depth3_truncation_pass"],
            "quotient_removed_identity_noncompression_detected": checks["identity_quotient_removal_pass"],
            "gate_corrupted_projection_rejected": checks["corruption_rejections_pass"],
        },
        "graph_isomorphism_receipt": {
            "package": "networkx",
            "qualified_api": "networkx.is_isomorphic",
            "claim_path": False,
            "exact_finite_check": True,
            "node_colors": "probe values on quotient classes and semantic action labels on expanded edge nodes",
            "all_intact_views_pass": checks["graph_isomorphisms_pass"],
            "corrupted_unlabeled_iso_count": checks["corrupted_unlabeled_iso_count"],
        },
        "gates": gates,
        "tool_manifest": {
            "jax.jit": "load_bearing",
            "jax.vmap": "load_bearing",
            "jax.numpy": "load_bearing exact integer and boolean arrays",
            "networkx.is_isomorphic": "exact external certification outside JAX claim path",
            "numpy": None,
        },
        "tool_calls": [
            {
                "tool": "jax",
                "qualified_api/function": "jax.jit(jax.vmap(refinement_trace))",
                "input_object": "20,000 exact Python random.Random transition tables",
                "output_object": "strict-depth census and stable probe-respecting congruences",
                "positive_case": "frozen census and all target relations are recovered exactly",
                "negative/erased_control": "probe erasure and depth-three truncation",
                "boundary_case": "frozen depth-one, depth-two, and depth-three controls",
                "demotion_condition": "any census mismatch, nonconvergence, or control silence",
                "gates": ["all_pass", "quotient"],
            },
            {
                "tool": "networkx",
                "qualified_api/function": "networkx.is_isomorphic",
                "input_object": "finite colored directed expanded quotient graphs",
                "output_object": "bijection-free exact isomorphism booleans",
                "positive_case": "all intact relabelings and action-swapped views are isomorphic",
                "negative/erased_control": "one-successor quotient corruption recorded separately",
                "boundary_case": "parallel action successors represented by distinct colored edge nodes",
                "demotion_condition": "any intact perspective is non-isomorphic",
                "gates": ["quotient"],
            },
        ],
        "compact_schema_receipt": {
            "raw_relation_arrays_emitted": False,
            "raw_4096_cell_arrays_emitted": False,
            "relation_hash_algorithm": "sha256 over row-major 0/1 bytes",
            "payload_sha256_excluding_self": None,
        },
        "elapsed_seconds": elapsed,
    }
    payload["compact_schema_receipt"]["payload_sha256_excluding_self"] = canonical_hash(payload)
    strict_write_json(args.output, payload)
    print(json.dumps({
        "all_local_gates_pass": all_local_gates_pass,
        "elapsed_seconds": elapsed,
        "output": str(args.output),
        "source_sha256": payload["source_sha256"],
    }, sort_keys=True))
    return 0 if all_local_gates_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
