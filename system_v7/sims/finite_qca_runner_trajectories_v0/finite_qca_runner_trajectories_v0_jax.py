#!/usr/bin/env python3
"""JAX leg for finite_qca_runner_trajectories_v0.

Vectorized finite transition-table and conjugated-support mirror. This leg does
not read the exact result; agreement is checked only by check_agreement.py.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

SIM_ID = "finite_qca_runner_trajectories_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_jax_results.json"

N = 6
Q = 2
NSTATES = Q**N
LEFT_CELL = 2
RIGHT_CELL = 3
LEFT_SIDE = [0, 1, 2]
RIGHT_SIDE = [3, 4, 5]
RULES = ["identity", "right_shift", "left_shift", "finite_depth_local_circuit"]
EXPECTED_INDEX = {
    "identity": 0,
    "right_shift": 1,
    "left_shift": -1,
    "finite_depth_local_circuit": 0,
}
RIGHT_SHIFT_SWAPS = [(4, 5), (3, 4), (2, 3), (1, 2), (0, 1)]
LEFT_SHIFT_SWAPS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]


def unpack(states: jnp.ndarray) -> jnp.ndarray:
    shifts = jnp.arange(N, dtype=jnp.uint32)
    return ((states[:, None].astype(jnp.uint32) >> shifts[None, :]) & 1).astype(jnp.uint8)


def pack(values: jnp.ndarray) -> jnp.ndarray:
    shifts = (jnp.array(1, dtype=jnp.uint32) << jnp.arange(N, dtype=jnp.uint32))
    return jnp.sum(values.astype(jnp.uint32) * shifts[None, :], axis=1)


def transition_array(rule: str, states: jnp.ndarray) -> jnp.ndarray:
    values = unpack(states)
    if rule == "identity":
        out = values
    elif rule in ("right_shift", "left_shift"):
        out = values
        for a, b in (RIGHT_SHIFT_SWAPS if rule == "right_shift" else LEFT_SHIFT_SWAPS):
            aa = out[:, a]
            bb = out[:, b]
            out = out.at[:, a].set(bb)
            out = out.at[:, b].set(aa)
    elif rule == "finite_depth_local_circuit":
        out = values
        for a, b in [(0, 1), (2, 3), (4, 5), (1, 2), (3, 4), (5, 0)]:
            aa = out[:, a]
            bb = out[:, b]
            out = out.at[:, a].set(bb)
            out = out.at[:, b].set(aa)
    else:
        raise ValueError(rule)
    return pack(out)


def inverse_array(rule: str, states: jnp.ndarray) -> jnp.ndarray:
    values = unpack(states)
    if rule == "identity":
        out = values
    elif rule in ("right_shift", "left_shift"):
        out = values
        schedule = RIGHT_SHIFT_SWAPS if rule == "right_shift" else LEFT_SHIFT_SWAPS
        for a, b in reversed(schedule):
            aa = out[:, a]
            bb = out[:, b]
            out = out.at[:, a].set(bb)
            out = out.at[:, b].set(aa)
    elif rule == "finite_depth_local_circuit":
        out = values
        for a, b in [(5, 0), (3, 4), (1, 2), (4, 5), (2, 3), (0, 1)]:
            aa = out[:, a]
            bb = out[:, b]
            out = out.at[:, a].set(bb)
            out = out.at[:, b].set(aa)
    else:
        raise ValueError(rule)
    return pack(out)


def gf2_rank(rows: list[list[int]]) -> int:
    rows = [row[:] for row in rows if any(row)]
    if not rows:
        return 0
    rank = 0
    col = 0
    while rank < len(rows) and col < len(rows[0]):
        pivot = next((r for r in range(rank, len(rows)) if rows[r][col]), None)
        if pivot is not None:
            rows[rank], rows[pivot] = rows[pivot], rows[rank]
            for r in range(len(rows)):
                if r != rank and rows[r][col]:
                    rows[r] = [a ^ b for a, b in zip(rows[r], rows[rank])]
            rank += 1
        col += 1
    return rank


def dependency_row(rule: str, source_cell: int) -> list[int]:
    states = jnp.arange(NSTATES, dtype=jnp.uint32)
    inv = inverse_array(rule, states)
    row = []
    for output_cell in range(N):
        flipped = states ^ jnp.uint32(1 << output_cell)
        inv_flipped = inverse_array(rule, flipped)
        a = (inv >> jnp.uint32(source_cell)) & jnp.uint32(1)
        b = (inv_flipped >> jnp.uint32(source_cell)) & jnp.uint32(1)
        row.append(int(jnp.any(a != b)))
    return row


def support_index(rule: str) -> dict:
    left_source = dependency_row(rule, LEFT_CELL)
    right_source = dependency_row(rule, RIGHT_CELL)
    right_row = [left_source[i] for i in RIGHT_SIDE]
    left_row = [right_source[i] for i in LEFT_SIDE]
    r_right = gf2_rank([right_row])
    r_left = gf2_rank([left_row])
    units = r_right - r_left
    return {
        "index_units_log_q": units,
        "index_log_value": units * math.log(Q),
        "right_flow_rank": r_right,
        "left_flow_rank": r_left,
        "left_cut_source_conjugated_support": [i for i, v in enumerate(left_source) if v],
        "right_cut_source_conjugated_support": [i for i, v in enumerate(right_source) if v],
        "right_restricted_row_from_source_2": right_row,
        "left_restricted_row_from_source_3": left_row,
        "computed_from": "JAX-vectorized finite differences of explicit inverse transition table",
    }


def transition_table(rule: str) -> list[int]:
    states = jnp.arange(NSTATES, dtype=jnp.uint32)
    table = jax.jit(lambda xs: transition_array(rule, xs))(states)
    return [int(x) for x in table.tolist()]


def inverse_table(rule: str) -> list[int]:
    states = jnp.arange(NSTATES, dtype=jnp.uint32)
    table = jax.jit(lambda xs: inverse_array(rule, xs))(states)
    return [int(x) for x in table.tolist()]


def reversibility_receipt(rule: str) -> dict:
    forward = transition_table(rule)
    inverse = inverse_table(rule)
    bijective = len(set(forward)) == NSTATES and len(set(inverse)) == NSTATES
    left_inverse = all(inverse[forward[s]] == s for s in range(NSTATES))
    right_inverse = all(forward[inverse[s]] == s for s in range(NSTATES))
    return {
        "bijective_transition_table": bijective,
        "explicit_inverse_left_composes_to_identity": left_inverse,
        "explicit_inverse_right_composes_to_identity": right_inverse,
        "reversibility_ok": bool(bijective and left_inverse and right_inverse),
    }


def cycles_for(table: list[int]) -> list[list[int]]:
    seen: set[int] = set()
    cycles = []
    for start in range(len(table)):
        if start in seen:
            continue
        path = []
        loc = {}
        state = start
        while state not in loc and state not in seen:
            loc[state] = len(path)
            path.append(state)
            state = table[state]
        if state in loc:
            cycles.append(path[loc[state]:])
        seen.update(path)
    return cycles


def recurrent_states(table: list[int]) -> set[int]:
    """Compute the recurrent set of the functional graph state -> table[state].

    A node is recurrent iff it lies on a cycle. Transient (tail) nodes are
    peeled off iteratively by removing nodes with in-degree 0: every removal
    decrements the in-degree of its successor, exposing the next tail node.
    What remains is exactly the union of cycles. This is computed from the
    table; a graph with a non-cycle terminal leaves that terminal transient.
    """
    n = len(table)
    indeg = [0] * n
    for s in range(n):
        indeg[table[s]] += 1
    transient: set[int] = set()
    frontier = [s for s in range(n) if indeg[s] == 0]
    while frontier:
        s = frontier.pop()
        transient.add(s)
        nxt = table[s]
        indeg[nxt] -= 1
        if indeg[nxt] == 0 and nxt not in transient:
            frontier.append(nxt)
    return set(range(n)) - transient


def absorbing_sets_only_cycles(table: list[int]) -> bool:
    """True iff every state is recurrent (the graph decomposes into cycles with
    no transient tails). Computed from the transition table, so a graph with a
    non-cycle terminal node returns False."""
    return len(recurrent_states(table)) == len(table)


def trajectory(table: list[int], seed: int, steps: int = 12) -> list[int]:
    out = [seed]
    state = seed
    for _ in range(steps):
        state = table[state]
        out.append(state)
    return out


def cycle_digest(rule: str) -> dict:
    table = transition_table(rule)
    cycles = cycles_for(table)
    lengths = [len(c) for c in cycles]
    fixed_points = [c[0] for c in cycles if len(c) == 1]
    recurrent = recurrent_states(table)
    only_cycles = len(recurrent) == NSTATES
    return {
        "num_cycles": len(cycles),
        "cycle_length_histogram": {str(k): v for k, v in sorted(Counter(lengths).items())},
        "fixed_points": fixed_points,
        "absorbing_sets_are_cycles": only_cycles,
        "recurrent_state_count": len(recurrent),
        "transient_state_count": NSTATES - len(recurrent),
        "states_in_cycles": sum(lengths),
        "absorbing_set_count": len(cycles),
        "absorbing_sets_check": "computed: every state recurrent (no transient tail) via in-degree peeling of the transition graph",
        "sample_absorbing_sets": [c for c in cycles[:8]],
        "sample_trajectories": {str(seed): trajectory(table, seed) for seed in [0, 1, 3, 21, 42, 63]},
    }


def main() -> int:
    rules = {}
    failures = []
    for rule in RULES:
        idx = support_index(rule)
        rev = reversibility_receipt(rule)
        cycles = cycle_digest(rule)
        tests = {
            "index_matches_expected_could_fail": idx["index_units_log_q"] == EXPECTED_INDEX[rule],
            "explicit_inverse_proves_reversibility": rev["reversibility_ok"],
            "transition_graph_has_only_cycle_absorbing_sets": cycles["absorbing_sets_are_cycles"],
        }
        if not all(tests.values()):
            failures.append(rule)
        rules[rule] = {
            "support_index": idx,
            "reversibility": rev,
            "finite_transition_graph": cycles,
            "tests": tests,
        }

    result = {
        "schema": "codex_ratchet.sim_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax_x64_vectorized",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "ring": {"N": N, "alphabet": [0, 1], "oriented_cut": "2|3"},
        "equivalence_relation": (
            "tau ~_support tau' iff ind_q(tau)=r_R-r_L from conjugated coordinate-observable "
            "support across cut 2|3 is equal; tau ~_cycle tau' iff cycle-length multisets match"
        ),
        "rules": rules,
        "gnvw_index_units_log_q": {rule: rules[rule]["support_index"]["index_units_log_q"] for rule in RULES},
        "all_tests_pass": not failures,
        "all_controls_pass": not failures,
        "failures": failures,
        "jax": {
            "ran": True,
            "source_path": str(Path(__file__).as_posix()),
            "packages_used": ["jax", "jax.numpy"],
            "aligned_packages_load_bearing": ["jax"],
            "reads_peer_result": False,
            "x64_enabled": bool(jax.config.jax_enable_x64),
            "tool_calls": [
                {
                    "tool": "jax",
                    "qualified_api/function": "jax.jit",
                    "input_object": "all 2^6 finite ring states per rule",
                    "output_object": "transition and inverse tables used by support-index and cycle checks",
                    "positive_case": "right_shift index +1 and left_shift index -1",
                    "negative/erased_control": "identity and finite_depth_local_circuit index 0",
                    "boundary_case": "fixed states 0 and 63 remain singleton absorbing cycles",
                    "demotion_condition": "if tables are non-bijective, read peer results, or indices are not derived from inverse-table support",
                    "gates": ["all_tests_pass", "all_controls_pass", "agreement_ok"],
                }
            ],
        },
        "TOOL_MANIFEST": {
            "jax": {
                "used": True,
                "tried": True,
                "reason": "x64 vectorized finite transition/inverse tables and dependency extraction gate the JAX leg indices, reversibility, and cycles",
            },
            "python_stdlib": {
                "used": True,
                "tried": True,
                "reason": "JSON emission, GF(2) row reduction, and cycle digest formatting",
            },
        },
        "TOOL_INTEGRATION_DEPTH": "load_bearing",
        "honest_scope": {
            "earns": "JAX-vectorized scratch mirror that derives the same support-flow index and transition graph from the finite inverse table without reading exact results",
            "does_not_earn": "infinite-chain GNVW theorem, canonical QCA classification, or promotion beyond scratch_diagnostic",
        },
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"engine": result["engine"], "all_tests_pass": result["all_tests_pass"], "indices": result["gnvw_index_units_log_q"], "failures": failures}, indent=2))
    return 0 if result["all_tests_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
