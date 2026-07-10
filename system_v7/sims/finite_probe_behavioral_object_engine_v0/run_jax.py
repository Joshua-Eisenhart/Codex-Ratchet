#!/usr/bin/env python3
"""JAX x64 exhaustive lane for the finite behavioral-object fixture.

This lane is a bounded scratch diagnostic. It reads only the frozen local spec
and preregistration receipt; it does not read Julia, PyTorch, or prior results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jax import config

config.update("jax_enable_x64", True)

import jax
import jax.numpy as jnp
from jax import lax, vmap


SIM_ID = "finite_probe_behavioral_object_engine_v0"
SCHEMA = "codex_ratchet.finite_probe_behavioral_object_engine.jax_result.v1"
CLASSIFICATION = "scratch_diagnostic"
SOURCE_PATH = Path(__file__).resolve()
SIM_DIR = SOURCE_PATH.parent
SPEC_PATH = SIM_DIR / "spec.json"
PREREG_PATH = SIM_DIR / "preregistration_receipt.json"
DEFAULT_OUTPUT_PATH = SIM_DIR / "results" / f"{SIM_ID}_jax_results.json"

RING_SIZE = 6
STATE_COUNT = 1 << RING_SIZE
MAX_DEPTH = 6
HISTORY_WIDTH = (1 << (MAX_DEPTH + 1)) - 1
RULE_A = 30
RULE_B = 110

EXPECTED_TWO_PROBE_COUNTS = [11, 14, 14, 14, 14, 14, 14]
EXPECTED_WEIGHT_ONLY_COUNTS = [7, 13, 14, 14, 14, 14, 14]
EXPECTED_DISAGREEMENT_COUNT = 56
EXPECTED_A_AFTER_B_BASINS = [3, 7, 18, 18, 18]
EXPECTED_B_AFTER_A_BASINS = [3, 13, 16, 16, 16]

TOOL_MANIFEST = {
    "jax": {
        "tried": True,
        "used": True,
        "reason": "Required x64 batched-exhaustive runtime for every bounded claim in this lane.",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "Exact int64 bit, equality, indexing, and reduction substrate on the 64-state carrier.",
    },
    "jax.vmap": {
        "tried": True,
        "used": True,
        "reason": "Vectorizes ECA transitions, all-state histories, rotations, and functional-graph traces.",
    },
    "jax.lax": {
        "tried": True,
        "used": True,
        "reason": "fori_loop constructs depth-six histories and scan certifies exact composite orbits.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Receipt-only JSON, path, timestamp, and SHA-256 plumbing outside the claim computation.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "Peer runtime is excluded from this independently implemented JAX lane.",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "Learned-perception controls belong to the separately scoped PyTorch lane.",
    },
    "smt": {
        "tried": False,
        "used": False,
        "reason": "No unbounded proof is claimed; exact exhaustive enumeration is the preregistered JAX surface.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "jax": "load_bearing",
    "jax.numpy": "supportive",
    "jax.vmap": "supportive",
    "jax.lax": "supportive",
    "python_stdlib": "supportive",
    "julia": None,
    "pytorch": None,
    "smt": None,
}

TOOL_CALLS = [
    {
        "tool": "jax",
        "qualified_api/function": "jax.vmap",
        "input_object": "all 64 int64 six-bit states and scalar ECA/history/rotation functions",
        "output_object": "rule tables, 64x127 history states, relabelings, and orbit traces",
        "positive_case": "two-probe histories stabilize at the preregistered 14-class quotient",
        "negative/erased_control": "weight-only observation begins strictly coarser",
        "boundary_case": "depth-zero two-probe observation has successor conflicts",
        "demotion_condition": "demote bounded-history claims if any state is omitted or vmap output disagrees with scalar indexing",
        "gates": ["all_pass", "quotient", "divergence"],
    },
    {
        "tool": "jax",
        "qualified_api/function": "jax.lax.fori_loop",
        "input_object": "binary action tree indices 1..126 and exact transition tables",
        "output_object": "breadth-first A/B successor histories through depth six",
        "positive_case": "stable depth-six fingerprint equivalence is a semiconjugacy for A and B",
        "negative/erased_control": "one altered A transition breaks the original stable quotient",
        "boundary_case": "history prefix of width one is the unrefined probe partition",
        "demotion_condition": "demote quotient claims if the history tree is incomplete or mutation remains well-defined",
        "gates": ["all_pass", "quotient"],
    },
    {
        "tool": "jax",
        "qualified_api/function": "jax.lax.scan",
        "input_object": "each of 64 states and each exact composite transition table",
        "output_object": "64-step attractor-entry iterates and 64-step cycle traces",
        "positive_case": "five exact attractors and preregistered sorted basin sizes for each action order",
        "negative/erased_control": "reversed action order has a distinct basin-size signature",
        "boundary_case": "fixed points are represented as period-one cycles",
        "demotion_condition": "demote attractor claims if any period, basin total, or transition closure check fails",
        "gates": ["all_pass", "divergence"],
    },
]


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256_bytes(payload)


def as_list(value: jax.Array) -> Any:
    return value.tolist()


def eca_step(state: jax.Array, rule: int) -> jax.Array:
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    bits = (state >> sites) & jnp.int64(1)
    left = jnp.roll(bits, 1)
    right = jnp.roll(bits, -1)
    neighborhood = (left << 2) | (bits << 1) | right
    next_bits = (jnp.int64(rule) >> neighborhood) & jnp.int64(1)
    return jnp.sum(next_bits << sites, dtype=jnp.int64)


def transition_table(states: jax.Array, rule: int) -> jax.Array:
    return vmap(lambda state: eca_step(state, rule))(states)


def history_for_state(initial: jax.Array, actions: jax.Array) -> jax.Array:
    history = jnp.zeros((HISTORY_WIDTH,), dtype=jnp.int64).at[0].set(initial)

    def add_node(index: int, values: jax.Array) -> jax.Array:
        parent_index = (index - 1) // 2
        action_index = (index - 1) & 1
        parent_state = values[parent_index]
        child_state = actions[action_index, parent_state]
        return values.at[index].set(child_state)

    return lax.fori_loop(1, HISTORY_WIDTH, add_node, history)


def all_histories(states: jax.Array, actions: jax.Array) -> jax.Array:
    return vmap(lambda state: history_for_state(state, actions))(states)


def probe_values(values: jax.Array) -> tuple[jax.Array, jax.Array]:
    sites = jnp.arange(RING_SIZE, dtype=jnp.int64)
    bits = (values[..., None] >> sites) & jnp.int64(1)
    weight = jnp.sum(bits, axis=-1, dtype=jnp.int64)
    walls = jnp.sum(bits != jnp.roll(bits, -1, axis=-1), axis=-1, dtype=jnp.int64)
    return weight, walls


def canonical_labels(rows: jax.Array) -> tuple[jax.Array, jax.Array]:
    flat_rows = rows.reshape((STATE_COUNT, -1))
    equal_rows = jnp.all(
        flat_rows[:, None, :] == flat_rows[None, :, :], axis=-1
    )
    indices = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    labels = jnp.min(jnp.where(equal_rows, indices[None, :], STATE_COUNT), axis=1)
    class_count = jnp.sum(labels == indices, dtype=jnp.int64)
    return labels, class_count


def partitions_through_depth(
    observations: jax.Array,
) -> tuple[list[jax.Array], list[jax.Array]]:
    labels_by_depth: list[jax.Array] = []
    counts_by_depth: list[jax.Array] = []
    for depth in range(MAX_DEPTH + 1):
        width = (1 << (depth + 1)) - 1
        labels, count = canonical_labels(observations[:, :width])
        labels_by_depth.append(labels)
        counts_by_depth.append(count)
    return labels_by_depth, counts_by_depth


def equivalence_matrix(labels: jax.Array) -> jax.Array:
    return labels[:, None] == labels[None, :]


def semiconjugacy_check(labels: jax.Array, transition: jax.Array) -> dict[str, jax.Array]:
    successor_labels = labels[transition]
    same_class = equivalence_matrix(labels)
    successor_disagreement = successor_labels[:, None] != successor_labels[None, :]
    conflicts = same_class & successor_disagreement
    state_has_conflict = jnp.any(conflicts, axis=1)
    indices = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    representative = labels == indices
    class_has_conflict = vmap(
        lambda rep: jnp.any(state_has_conflict & (labels == rep))
    )(indices)
    flat_index = jnp.argmax(conflicts.reshape(-1))
    any_conflict = jnp.any(conflicts)
    witness = jnp.where(
        any_conflict,
        jnp.array([flat_index // STATE_COUNT, flat_index % STATE_COUNT]),
        jnp.array([-1, -1], dtype=jnp.int64),
    )
    return {
        "well_defined": ~any_conflict,
        "conflicting_pair_count": jnp.sum(conflicts, dtype=jnp.int64),
        "conflicting_class_count": jnp.sum(
            representative & class_has_conflict, dtype=jnp.int64
        ),
        "first_conflict": witness,
        "successor_labels": successor_labels,
    }


def rotate_state(state: jax.Array, amount: jax.Array | int) -> jax.Array:
    shift = jnp.asarray(amount, dtype=jnp.int64) % RING_SIZE
    inverse_shift = (RING_SIZE - shift) % RING_SIZE
    return ((state << shift) | (state >> inverse_shift)) & (STATE_COUNT - 1)


def rotation_orbit_labels(states: jax.Array) -> jax.Array:
    rotations = vmap(
        lambda amount: vmap(lambda state: rotate_state(state, amount))(states)
    )(jnp.arange(RING_SIZE, dtype=jnp.int64))
    return jnp.min(rotations, axis=0)


def advance_and_trace(start: jax.Array, transition: jax.Array) -> tuple[jax.Array, jax.Array]:
    def step(current: jax.Array, _: None) -> tuple[jax.Array, jax.Array]:
        next_state = transition[current]
        return next_state, next_state

    return lax.scan(step, start, xs=None, length=STATE_COUNT)


def functional_graph(transition: jax.Array, states: jax.Array) -> dict[str, jax.Array]:
    entry_states, _ = vmap(lambda state: advance_and_trace(state, transition))(states)

    def cycle_data(entry: jax.Array) -> tuple[jax.Array, jax.Array, jax.Array]:
        _, trace = advance_and_trace(entry, transition)
        returns = trace == entry
        period = jnp.argmax(returns) + 1
        positions = jnp.arange(STATE_COUNT, dtype=jnp.int64)
        cycle_id = jnp.min(jnp.where(positions < period, trace, STATE_COUNT))
        return period, cycle_id, trace

    periods, basin_ids, traces = vmap(cycle_data)(entry_states)
    basin_sizes = vmap(lambda basin: jnp.sum(basin_ids == basin, dtype=jnp.int64))(states)
    active_basins = basin_sizes > 0
    attractor_count = jnp.sum(active_basins, dtype=jnp.int64)
    return {
        "period_by_state": periods,
        "basin_id_by_state": basin_ids,
        "cycle_trace_by_state": traces,
        "basin_size_by_id": basin_sizes,
        "active_basin_mask": active_basins,
        "attractor_count": attractor_count,
        "basin_total": jnp.sum(basin_sizes, dtype=jnp.int64),
    }


def graph_receipt(graph: dict[str, jax.Array], transition: jax.Array) -> dict[str, Any]:
    basin_sizes = as_list(graph["basin_size_by_id"])
    active_ids = [index for index, size in enumerate(basin_sizes) if size > 0]
    periods = as_list(graph["period_by_state"])
    traces = as_list(graph["cycle_trace_by_state"])
    attractors = []
    for basin_id in active_ids:
        period = int(periods[basin_id])
        cycle = [basin_id]
        current = basin_id
        for _ in range(1, period):
            current = int(transition[current])
            cycle.append(current)
        attractors.append(
            {
                "canonical_cycle_id": basin_id,
                "period": period,
                "cycle_states_from_minimum": cycle,
                "basin_size": int(basin_sizes[basin_id]),
                "scan_trace_prefix": [int(value) for value in traces[basin_id][:period]],
            }
        )
    signature = sorted((item["basin_size"], item["period"]) for item in attractors)
    return {
        "attractor_count": len(attractors),
        "sorted_basin_sizes": sorted(item["basin_size"] for item in attractors),
        "sorted_basin_period_signature": [list(item) for item in signature],
        "basin_total": int(graph["basin_total"]),
        "attractors": attractors,
    }


def conjugate_transition(
    transition: jax.Array, states: jax.Array, amount: int
) -> jax.Array:
    inverse_states = vmap(lambda state: rotate_state(state, -amount))(states)
    return vmap(lambda state: rotate_state(state, amount))(transition[inverse_states])


def relabel_checks(
    states: jax.Array,
    stable_labels: jax.Array,
    action_a: jax.Array,
    action_b: jax.Array,
    a_after_b: jax.Array,
    b_after_a: jax.Array,
    base_a_graph: dict[str, jax.Array],
    base_b_graph: dict[str, jax.Array],
) -> list[dict[str, Any]]:
    base_equivalence = equivalence_matrix(stable_labels)
    base_a_sizes = jnp.sort(base_a_graph["basin_size_by_id"])
    base_b_sizes = jnp.sort(base_b_graph["basin_size_by_id"])
    base_a_signature = jnp.sort(
        jnp.where(
            base_a_graph["active_basin_mask"],
            base_a_graph["basin_size_by_id"] * (STATE_COUNT + 1)
            + base_a_graph["period_by_state"],
            0,
        )
    )
    base_b_signature = jnp.sort(
        jnp.where(
            base_b_graph["active_basin_mask"],
            base_b_graph["basin_size_by_id"] * (STATE_COUNT + 1)
            + base_b_graph["period_by_state"],
            0,
        )
    )
    checks = []
    for amount in range(RING_SIZE):
        rotated_states = vmap(lambda state: rotate_state(state, amount))(states)
        rotated_equivalence = base_equivalence[
            rotated_states[:, None], rotated_states[None, :]
        ]
        conjugate_a = conjugate_transition(action_a, states, amount)
        conjugate_b = conjugate_transition(action_b, states, amount)
        conjugate_ab = conjugate_transition(a_after_b, states, amount)
        conjugate_ba = conjugate_transition(b_after_a, states, amount)
        graph_ab = functional_graph(conjugate_ab, states)
        graph_ba = functional_graph(conjugate_ba, states)
        graph_ab_signature = jnp.sort(
            jnp.where(
                graph_ab["active_basin_mask"],
                graph_ab["basin_size_by_id"] * (STATE_COUNT + 1)
                + graph_ab["period_by_state"],
                0,
            )
        )
        graph_ba_signature = jnp.sort(
            jnp.where(
                graph_ba["active_basin_mask"],
                graph_ba["basin_size_by_id"] * (STATE_COUNT + 1)
                + graph_ba["period_by_state"],
                0,
            )
        )
        checks.append(
            {
                "rotation": amount,
                "partition_equivalence_preserved": bool(
                    jnp.all(rotated_equivalence == base_equivalence)
                ),
                "A_conjugacy_preserved": bool(jnp.all(conjugate_a == action_a)),
                "B_conjugacy_preserved": bool(jnp.all(conjugate_b == action_b)),
                "quotient_transition_preserved": bool(
                    jnp.all(rotated_equivalence == base_equivalence)
                    & jnp.all(conjugate_a == action_a)
                    & jnp.all(conjugate_b == action_b)
                ),
                "A_after_B_basin_signature_preserved": bool(
                    jnp.all(graph_ab_signature == base_a_signature)
                ),
                "B_after_A_basin_signature_preserved": bool(
                    jnp.all(graph_ba_signature == base_b_signature)
                ),
                "A_after_B_basin_sizes_preserved": bool(
                    jnp.all(jnp.sort(graph_ab["basin_size_by_id"]) == base_a_sizes)
                ),
                "B_after_A_basin_sizes_preserved": bool(
                    jnp.all(jnp.sort(graph_ba["basin_size_by_id"]) == base_b_sizes)
                ),
                "A_after_B_attractor_count_preserved": bool(
                    graph_ab["attractor_count"] == base_a_graph["attractor_count"]
                ),
                "B_after_A_attractor_count_preserved": bool(
                    graph_ba["attractor_count"] == base_b_graph["attractor_count"]
                ),
            }
        )
    return checks


def quotient_receipt(labels: jax.Array, action_a: jax.Array, action_b: jax.Array) -> dict[str, Any]:
    label_values = as_list(labels)
    successor_a = as_list(labels[action_a])
    successor_b = as_list(labels[action_b])
    representatives = [index for index, label in enumerate(label_values) if index == label]
    return {
        "class_count": len(representatives),
        "class_representatives": representatives,
        "state_to_class_representative": label_values,
        "induced_A": {str(rep): int(successor_a[rep]) for rep in representatives},
        "induced_B": {str(rep): int(successor_b[rep]) for rep in representatives},
    }


def scalar_semiconjugacy_receipt(check: dict[str, jax.Array]) -> dict[str, Any]:
    return {
        "well_defined": bool(check["well_defined"]),
        "conflicting_pair_count": int(check["conflicting_pair_count"]),
        "conflicting_class_count": int(check["conflicting_class_count"]),
        "first_conflict": as_list(check["first_conflict"]),
    }


def build_receipt(output_path: Path) -> dict[str, Any]:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
    spec_sha256 = sha256_file(SPEC_PATH)
    prereg_sha256 = sha256_file(PREREG_PATH)

    states = jnp.arange(STATE_COUNT, dtype=jnp.int64)
    action_a = transition_table(states, RULE_A)
    action_b = transition_table(states, RULE_B)
    actions = jnp.stack([action_a, action_b])
    histories = all_histories(states, actions)
    weights, walls = probe_values(histories)
    two_probe_observations = jnp.stack([weights, walls], axis=-1).reshape(
        STATE_COUNT, HISTORY_WIDTH * 2
    )

    # Interleave probe pairs by history node so each depth uses an exact prefix.
    two_probe_by_node = jnp.stack([weights, walls], axis=-1)
    two_labels, two_counts = partitions_through_depth(two_probe_by_node)
    weight_labels, weight_counts = partitions_through_depth(weights[..., None])
    two_count_values = [int(value) for value in two_counts]
    weight_count_values = [int(value) for value in weight_counts]
    stable_labels = two_labels[MAX_DEPTH]

    stable_a = semiconjugacy_check(stable_labels, action_a)
    stable_b = semiconjugacy_check(stable_labels, action_b)
    depth_zero_a = semiconjugacy_check(two_labels[0], action_a)
    depth_zero_b = semiconjugacy_check(two_labels[0], action_b)

    mutation_source = jnp.int64(1)
    original_target = action_a[mutation_source]
    original_target_label = stable_labels[original_target]
    mutation_target = jnp.argmax(stable_labels != original_target_label).astype(jnp.int64)
    mutated_a = action_a.at[mutation_source].set(mutation_target)
    mutation_check = semiconjugacy_check(stable_labels, mutated_a)

    a_after_b = action_a[action_b]
    b_after_a = action_b[action_a]
    disagreement_mask = a_after_b != b_after_a
    disagreement_count = int(jnp.sum(disagreement_mask, dtype=jnp.int64))
    graph_ab = functional_graph(a_after_b, states)
    graph_ba = functional_graph(b_after_a, states)
    graph_ab_receipt = graph_receipt(graph_ab, a_after_b)
    graph_ba_receipt = graph_receipt(graph_ba, b_after_a)

    orbit_labels = rotation_orbit_labels(states)
    orbit_equivalence = equivalence_matrix(orbit_labels)
    stable_equivalence = equivalence_matrix(stable_labels)
    relabel = relabel_checks(
        states,
        stable_labels,
        action_a,
        action_b,
        a_after_b,
        b_after_a,
        graph_ab,
        graph_ba,
    )

    two_zero_equivalence = equivalence_matrix(two_labels[0])
    weight_zero_equivalence = equivalence_matrix(weight_labels[0])
    weight_zero_coarser = bool(
        jnp.all((~two_zero_equivalence) | weight_zero_equivalence)
        & jnp.any(two_zero_equivalence != weight_zero_equivalence)
    )
    relabel_all_pass = all(
        all(value for key, value in row.items() if key != "rotation") for row in relabel
    )

    tests = {
        "T1_behavioral_objects": {
            "pass": two_count_values == EXPECTED_TWO_PROBE_COUNTS,
            "observed_class_count_by_depth": two_count_values,
            "expected_class_count_by_depth": EXPECTED_TWO_PROBE_COUNTS,
        },
        "T2_rotation_identity": {
            "pass": bool(jnp.all(stable_equivalence == orbit_equivalence))
            and int(jnp.sum(orbit_labels == states)) == 14,
            "behavioral_class_count": two_count_values[-1],
            "rotation_orbit_count": int(jnp.sum(orbit_labels == states)),
        },
        "T3_semiconjugacy": {
            "pass": bool(stable_a["well_defined"])
            and bool(stable_b["well_defined"])
            and not bool(depth_zero_a["well_defined"])
            and not bool(depth_zero_b["well_defined"]),
            "stable_A": scalar_semiconjugacy_receipt(stable_a),
            "stable_B": scalar_semiconjugacy_receipt(stable_b),
            "depth_zero_A": scalar_semiconjugacy_receipt(depth_zero_a),
            "depth_zero_B": scalar_semiconjugacy_receipt(depth_zero_b),
        },
        "T4_order_teeth": {
            "pass": disagreement_count == EXPECTED_DISAGREEMENT_COUNT
            and graph_ab_receipt["sorted_basin_sizes"] == EXPECTED_A_AFTER_B_BASINS
            and graph_ba_receipt["sorted_basin_sizes"] == EXPECTED_B_AFTER_A_BASINS,
            "disagreement_state_count": disagreement_count,
            "disagreement_states": [
                index for index, differs in enumerate(as_list(disagreement_mask)) if differs
            ],
        },
        "T5_attractor_structure": {
            "pass": graph_ab_receipt["attractor_count"] == 5
            and graph_ba_receipt["attractor_count"] == 5
            and graph_ab_receipt["basin_total"] == STATE_COUNT
            and graph_ba_receipt["basin_total"] == STATE_COUNT,
            "A_after_B_attractor_count": graph_ab_receipt["attractor_count"],
            "B_after_A_attractor_count": graph_ba_receipt["attractor_count"],
        },
        "T6_probe_ablation": {
            "pass": weight_count_values == EXPECTED_WEIGHT_ONLY_COUNTS
            and weight_zero_coarser
            and weight_count_values[1] < two_count_values[1],
            "weight_only_class_count_by_depth": weight_count_values,
            "expected_weight_only_class_count_by_depth": EXPECTED_WEIGHT_ONLY_COUNTS,
            "weight_depth_zero_strictly_coarser": weight_zero_coarser,
        },
        "T7_relabel_control": {
            "pass": relabel_all_pass,
            "rotations": relabel,
        },
        "C_transition_mutation": {
            "pass": bool(stable_a["well_defined"])
            and not bool(mutation_check["well_defined"]),
            "source_state": int(mutation_source),
            "original_target": int(original_target),
            "mutated_target": int(mutation_target),
            "original_quotient_well_defined": bool(stable_a["well_defined"]),
            "mutated_quotient": scalar_semiconjugacy_receipt(mutation_check),
        },
        "C_input_integrity": {
            "pass": spec_sha256 == prereg["spec_sha256"]
            and prereg["registered_before_builder_source"] is True
            and spec["sim_id"] == SIM_ID
            and prereg["sim_id"] == SIM_ID,
            "spec_hash_matches_preregistration": spec_sha256
            == prereg["spec_sha256"],
            "registered_before_builder_source": prereg[
                "registered_before_builder_source"
            ],
        },
        "C_jax_x64": {
            "pass": bool(jax.config.read("jax_enable_x64")),
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        },
        "T9_engine_removal_boundary": {
            "pass": False,
            "jax_claims_gated": [
                "bounded history fingerprints",
                "probe ablations",
                "action-order comparison",
                "cyclic relabel control",
                "false-quotient transition mutation",
            ],
            "claims_not_gated_by_jax": [
                "Julia semantic ownership",
                "learned reidentification",
            ],
            "reason": "role declarations are present but no executable engine-removal ablation was run; nonredundancy remains unearned",
        },
    }
    all_pass = all(test["pass"] for test in tests.values())

    history_payload = {
        "states": as_list(states),
        "A": as_list(action_a),
        "B": as_list(action_b),
        "histories": as_list(histories),
    }
    partition_payload = {
        "two_probe": [as_list(labels) for labels in two_labels],
        "weight_only": [as_list(labels) for labels in weight_labels],
    }
    composite_payload = {
        "A_after_B": as_list(a_after_b),
        "B_after_A": as_list(b_after_a),
        "A_after_B_graph": graph_ab_receipt,
        "B_after_A_graph": graph_ba_receipt,
    }

    return {
        "schema": SCHEMA,
        "schema_version": "three_engine_sim_lane_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "engine_role": "batched_exhaustive_workhorse",
        "source_path": str(SOURCE_PATH.relative_to(SOURCE_PATH.parents[3])),
        "source_sha256": sha256_file(SOURCE_PATH),
        "output_path": str(output_path),
        "classification": CLASSIFICATION,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "stage_movement_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "classical",
        "sim_class": "finite_behavioral_quotient_probe",
        "tier": 1,
        "purpose": "Exhaustively pressure finite probe-relative object identity and order-sensitive controls.",
        "scientific_question": "Which six-site states remain indistinguishable under the frozen probes and both ECA actions through depth six?",
        "root_constraints_in_force": [
            "finite bounded carrier",
            "probe-relative distinguishability",
            "action-order sensitivity",
        ],
        "carrier_layer": "all 64 binary states on a periodic six-site ring",
        "geometry_layer": "cyclic six-site presentation symmetry only",
        "bridge_layer": "none",
        "cut_layer": "finite action-history depth six",
        "law_or_candidate_tested": "behavioral partition refinement under ECA rules 30 and 110",
        "branch_status_before_run": "preregistered scratch diagnostic",
        "required_inputs": [str(SPEC_PATH), str(PREREG_PATH)],
        "data_or_artifact_dependencies": [],
        "reads_peer_result": False,
        "peer_result_paths_read": [],
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "jax_version": jax.__version__,
        "packages_used": ["jax", "jax.numpy", "jax.lax", "jax.vmap"],
        "aligned_packages_load_bearing": ["jax.lax", "jax.vmap"],
        "required_tools": ["jax", "jax.numpy", "jax.lax", "jax.vmap"],
        "actual_tools_used": ["jax", "jax.numpy", "jax.lax", "jax.vmap"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_calls": TOOL_CALLS,
        "proof_surfaces_used": ["exact exhaustive finite equality"],
        "graph_surfaces_used": ["exact JAX functional transition arrays"],
        "topology_surfaces_used": [],
        "foreign_runtime_manifest": {
            "jax": {
                "role": "batched_exhaustive_workhorse",
                "packages": ["jax", "jax.numpy", "jax.lax", "jax.vmap"],
                "x64": True,
            },
            "julia": {"used": False, "reason": "peer read prohibited"},
            "pytorch": {"used": False, "reason": "peer read prohibited"},
            "tensor_exchange": "none",
        },
        "input_integrity": {
            "spec_path": str(SPEC_PATH),
            "spec_sha256": spec_sha256,
            "preregistered_spec_sha256": prereg["spec_sha256"],
            "spec_hash_matches_preregistration": spec_sha256 == prereg["spec_sha256"],
            "preregistration_path": str(PREREG_PATH),
            "preregistration_sha256": prereg_sha256,
            "registered_before_builder_source": prereg["registered_before_builder_source"],
            "spec_schema": spec["schema"],
        },
        "fixture": {
            "state_count": STATE_COUNT,
            "ring_size": RING_SIZE,
            "history_depth": MAX_DEPTH,
            "history_node_count": HISTORY_WIDTH,
            "state_encoding": spec["fixture"]["state_encoding"],
            "A_rule": RULE_A,
            "B_rule": RULE_B,
            "A_transition": as_list(action_a),
            "B_transition": as_list(action_b),
        },
        "history_fingerprints": {
            "layout": "breadth-first action words; root then A-child/B-child recursively",
            "probe_pair_order": ["weight", "domain_walls"],
            "two_probe_class_count_by_depth": two_count_values,
            "weight_only_class_count_by_depth": weight_count_values,
            "two_probe_depth_six_fingerprints": as_list(two_probe_observations),
        },
        "quotient": quotient_receipt(stable_labels, action_a, action_b),
        "semiconjugacy": {
            "stable_A": scalar_semiconjugacy_receipt(stable_a),
            "stable_B": scalar_semiconjugacy_receipt(stable_b),
            "depth_zero_A": scalar_semiconjugacy_receipt(depth_zero_a),
            "depth_zero_B": scalar_semiconjugacy_receipt(depth_zero_b),
            "mutated_A": scalar_semiconjugacy_receipt(mutation_check),
        },
        "action_order": {
            "composition_convention": "A_after_B[s] = A[B[s]]; B_after_A[s] = B[A[s]]",
            "disagreement_state_count": disagreement_count,
            "A_after_B_transition": as_list(a_after_b),
            "B_after_A_transition": as_list(b_after_a),
            "A_after_B_functional_graph": graph_ab_receipt,
            "B_after_A_functional_graph": graph_ba_receipt,
        },
        "controls": {
            "depth_zero_false_quotient": {
                "A": scalar_semiconjugacy_receipt(depth_zero_a),
                "B": scalar_semiconjugacy_receipt(depth_zero_b),
            },
            "weight_only_probe_ablation": {
                "class_count_by_depth": weight_count_values,
                "depth_zero_strictly_coarser": weight_zero_coarser,
            },
            "cyclic_relabeling": relabel,
            "action_reversal": {
                "disagreement_state_count": disagreement_count,
                "basin_signatures_differ": graph_ab_receipt["sorted_basin_sizes"]
                != graph_ba_receipt["sorted_basin_sizes"],
            },
            "single_transition_mutation": tests["C_transition_mutation"],
        },
        "tests": tests,
        "all_pass": all_pass,
        "divergence_log": {
            "preregistered_fixture_comparison": {
                "two_probe_counts_match": two_count_values == EXPECTED_TWO_PROBE_COUNTS,
                "weight_only_counts_match": weight_count_values == EXPECTED_WEIGHT_ONLY_COUNTS,
                "order_disagreement_matches": disagreement_count == EXPECTED_DISAGREEMENT_COUNT,
                "A_after_B_basin_sizes_match": graph_ab_receipt["sorted_basin_sizes"]
                == EXPECTED_A_AFTER_B_BASINS,
                "B_after_A_basin_sizes_match": graph_ba_receipt["sorted_basin_sizes"]
                == EXPECTED_B_AFTER_A_BASINS,
            },
            "peer_engine_comparison": "not_performed",
        },
        "artifact_hashes": {
            "history_payload_sha256": canonical_hash(history_payload),
            "partition_payload_sha256": canonical_hash(partition_payload),
            "composite_payload_sha256": canonical_hash(composite_payload),
        },
        "required_negatives": [
            "depth-zero false quotient",
            "weight-only probe ablation",
            "cyclic state relabeling",
            "action reversal",
            "one mutated transition that breaks the original quotient",
        ],
        "negatives_run": [
            "depth-zero false quotient",
            "weight-only probe ablation",
            "cyclic state relabeling",
            "action reversal",
            "one mutated transition that breaks the original quotient",
        ],
        "kill_conditions": [
            "any preregistered exact count differs",
            "stable quotient has an A or B successor conflict",
            "depth-zero quotient lacks either required conflict",
            "transition mutation fails to break the original quotient",
            "any cyclic relabel invariant changes",
            "functional-graph basin totals differ from 64",
        ],
        "required_artifacts": ["structured JAX lane result JSON"],
        "artifacts_emitted": [str(output_path)],
        "witness_trace_id": canonical_hash(history_payload),
        "result_summary": "bounded JAX exhaustive checks pass" if all_pass else "one or more bounded JAX checks fail",
        "pass_rule": "all preregistered JAX-scoped exact values and required controls agree",
        "fail_rule": "any exact value, quotient gate, mutation control, relabel control, or basin closure check differs",
        "allowed_claims": [
            "finite six-site behavioral partition fingerprints through depth six",
            "finite action-order disagreement",
            "finite quotient and false-quotient controls",
            "finite exact composite attractor and basin signatures",
        ],
        "claim_ceiling": spec["claim_ceiling"],
        "promotion_blockers": [
            "scratch diagnostic classification",
            "Julia exact receipt remains semantic owner for object and basin claims",
            "PyTorch learned-perception receipt is independent and absent from this lane",
            "promotion, formal admission, and stage movement are preregistered false",
        ],
        "eligible_consumers": ["bounded controller comparison only"],
        "blocked_consumers": spec["blocked_consumers"],
        "out_of_scope": spec["blocked_consumers"],
        "demotion_condition": "demote every JAX-scoped claim if all_pass is false or input integrity fails",
        "surviving_alternatives": [
            "other finite action/probe fixtures remain untested",
            "learned object reidentification remains a separate empirical question",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    receipt = build_receipt(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
