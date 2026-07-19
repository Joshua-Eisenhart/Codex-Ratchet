#!/usr/bin/env python3
"""EXACT leg for finite_qca_runner_trajectories_v0.

Finite reversible binary-ring QCA diagnostic. The support-flow index is derived
from Heisenberg-conjugated coordinate observables e_i -> e_i o F^{-1}; it is not
read from a stored shift label.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

SIM_ID = "finite_qca_runner_trajectories_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_exact_results.json"

N = 6
Q = 2
NSTATES = Q**N
LEFT_CELL = 2
RIGHT_CELL = 3
LEFT_SIDE = [0, 1, 2]
RIGHT_SIDE = [3, 4, 5]
EVEN_BONDS = [(0, 1), (2, 3), (4, 5)]
ODD_BONDS = [(1, 2), (3, 4), (5, 0)]
RIGHT_SHIFT_SWAPS = [(4, 5), (3, 4), (2, 3), (1, 2), (0, 1)]
LEFT_SHIFT_SWAPS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5)]
RULES = ["identity", "right_shift", "left_shift", "finite_depth_local_circuit"]
EXPECTED_INDEX = {
    "identity": 0,
    "right_shift": 1,
    "left_shift": -1,
    "finite_depth_local_circuit": 0,
}


def bits(state: int) -> list[int]:
    return [(state >> i) & 1 for i in range(N)]


def pack(values: list[int]) -> int:
    out = 0
    for i, bit in enumerate(values):
        out |= (bit & 1) << i
    return out


def swap_cells(state: int, a: int, b: int) -> int:
    values = bits(state)
    values[a], values[b] = values[b], values[a]
    return pack(values)


def apply_swap_schedule(state: int, schedule: list[tuple[int, int]]) -> int:
    for a, b in schedule:
        state = swap_cells(state, a, b)
    return state


def brickwork_swap(state: int) -> int:
    for a, b in EVEN_BONDS:
        state = swap_cells(state, a, b)
    for a, b in ODD_BONDS:
        state = swap_cells(state, a, b)
    return state


def brickwork_swap_inverse(state: int) -> int:
    for a, b in reversed(ODD_BONDS):
        state = swap_cells(state, a, b)
    for a, b in reversed(EVEN_BONDS):
        state = swap_cells(state, a, b)
    return state


def transition(rule: str, state: int) -> int:
    if rule == "identity":
        return state
    if rule == "right_shift":
        return apply_swap_schedule(state, RIGHT_SHIFT_SWAPS)
    if rule == "left_shift":
        return apply_swap_schedule(state, LEFT_SHIFT_SWAPS)
    if rule == "finite_depth_local_circuit":
        return brickwork_swap(state)
    raise ValueError(rule)


def inverse_transition(rule: str, state: int) -> int:
    if rule == "identity":
        return state
    if rule == "right_shift":
        return apply_swap_schedule(state, list(reversed(RIGHT_SHIFT_SWAPS)))
    if rule == "left_shift":
        return apply_swap_schedule(state, list(reversed(LEFT_SHIFT_SWAPS)))
    if rule == "finite_depth_local_circuit":
        return brickwork_swap_inverse(state)
    raise ValueError(rule)


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
    row = []
    for output_cell in range(N):
        depends = False
        for y in range(NSTATES):
            a = (inverse_transition(rule, y) >> source_cell) & 1
            b = (inverse_transition(rule, y ^ (1 << output_cell)) >> source_cell) & 1
            if a != b:
                depends = True
                break
        row.append(1 if depends else 0)
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
        "computed_from": "finite differences of explicit inverse transition table",
    }


def transition_table(rule: str) -> list[int]:
    return [transition(rule, s) for s in range(NSTATES)]


def inverse_table(rule: str) -> list[int]:
    return [inverse_transition(rule, s) for s in range(NSTATES)]


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


def trajectory(rule: str, seed: int, steps: int = 12) -> list[int]:
    out = [seed]
    state = seed
    for _ in range(steps):
        state = transition(rule, state)
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
        "sample_trajectories": {str(seed): trajectory(rule, seed) for seed in [0, 1, 3, 21, 42, 63]},
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
        "engine": "exact_stdlib_exhaustive",
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
        "TOOL_MANIFEST": {
            "python_stdlib": {
                "used": True,
                "tried": True,
                "reason": "exhaustive finite transition tables, explicit inverse composition checks, cycle decomposition, and finite-difference support extraction",
            }
        },
        "TOOL_INTEGRATION_DEPTH": "load_bearing",
        "honest_scope": {
            "earns": "finite scratch witness that the support-flow index is computed from conjugated operator support and separates identity/right shift/left shift/finite-depth controls as 0/+1/-1/0 on this ring",
            "does_not_earn": "infinite-chain GNVW theorem, canonical QCA classification, or promotion beyond scratch_diagnostic",
        },
    }
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"engine": result["engine"], "all_tests_pass": result["all_tests_pass"], "indices": result["gnvw_index_units_log_q"], "failures": failures}, indent=2))
    return 0 if result["all_tests_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
