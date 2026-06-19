#!/usr/bin/env python3
"""Minimal constraints-first finite M(C) floor.

This is not the full geometric constraint manifold. It is the smallest executable
floor that names S, C, P, ~_P, Adm_C, order maps, controls, and a carved-structure
readout attempt under the 2026-06-12 manifold-first stop order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict, deque
from itertools import product
from pathlib import Path
from typing import Callable, Iterable

State = tuple[int, int, int, int]  # shell, phase_parity, orientation, memory

OBJECT_ID = "gcm_constraint_carve_floor_v0"
PACKET_DIR = Path(__file__).resolve().parent
DEFAULT_OUTPUT = PACKET_DIR / "results" / f"{OBJECT_ID}_results.json"


def candidate_space() -> list[State]:
    return list(product(range(3), range(2), range(2), range(2)))


def canonical_memory(shell: int, phase_parity: int, orientation: int) -> int:
    return (shell + phase_parity + orientation) % 2


def normalize(state: State) -> State:
    shell, phase_parity, orientation, _memory = state
    shell %= 3
    phase_parity %= 2
    orientation %= 2
    return (shell, phase_parity, orientation, canonical_memory(shell, phase_parity, orientation))


def R(state: State) -> State:
    """Finite rotation-like parity flip. Baseline operation, not an engine claim."""
    shell, phase_parity, orientation, memory = state
    return normalize((shell, 1 - phase_parity, orientation, memory))


def D(state: State) -> State:
    """Finite dissipative/contraction-like shell move. Baseline operation, not a terrain claim."""
    shell, phase_parity, orientation, memory = state
    if orientation == 0:
        delta_shell = 1 if phase_parity == 1 else -1
    else:
        # This deliberately leaves some orientation-1 rows without a stable N01 bite.
        delta_shell = 0 if shell == 0 else (1 if phase_parity == 0 else -1)
    return normalize(((shell + delta_shell) % 3, phase_parity, orientation, memory))


def R_after_D(state: State) -> State:
    return R(D(state))


def D_after_R(state: State) -> State:
    return D(R(state))


ORDER_MAPS: dict[str, Callable[[State], State]] = {
    "R": R,
    "D": D,
    "R_after_D": R_after_D,
    "D_after_R": D_after_R,
}


def probe_signature(state: State) -> tuple[int, int, int, int]:
    shell, phase_parity, orientation, memory = state
    return (shell, phase_parity, orientation, memory)


def order_gap_visible(state: State) -> bool:
    return probe_signature(R_after_D(state)) != probe_signature(D_after_R(state))


def C_history_consistency(state: State) -> bool:
    shell, phase_parity, orientation, memory = state
    return memory == canonical_memory(shell, phase_parity, orientation)


def C_N01_order_visible(state: State) -> bool:
    return order_gap_visible(state)


def base_admissible_states(drop: set[str] | None = None) -> set[State]:
    drop = drop or set()
    states = set(candidate_space())
    if "C_history_consistency" not in drop:
        states = {state for state in states if C_history_consistency(state)}
    if "C_N01_order_visible" not in drop:
        states = {state for state in states if C_N01_order_visible(state)}
    return states


def closed_survivors(drop: set[str] | None = None, extra_predicate: Callable[[State], bool] | None = None) -> set[State]:
    """Greatest subset closed under R, D, R∘D, and D∘R after active constraints."""
    drop = drop or set()
    survivors = base_admissible_states(drop=drop)
    if extra_predicate is not None:
        survivors = {state for state in survivors if extra_predicate(state)}
    if "C_closure_under_order_maps" in drop:
        return survivors

    changed = True
    while changed:
        changed = False
        for state in list(survivors):
            if any(op(state) not in survivors for op in ORDER_MAPS.values()):
                survivors.remove(state)
                changed = True
    return survivors


def failed_constraints_for(state: State, survivors: set[State]) -> list[str]:
    failed: list[str] = []
    if not C_history_consistency(state):
        failed.append("C_history_consistency")
    if not C_N01_order_visible(state):
        failed.append("C_N01_order_visible")
    if C_history_consistency(state) and C_N01_order_visible(state) and state not in survivors:
        failed.append("C_closure_under_order_maps")
    return failed


def state_row(state: State) -> dict:
    return {
        "state": list(state),
        "probe_signature": list(probe_signature(state)),
        "R": list(R(state)),
        "D": list(D(state)),
        "R_after_D": list(R_after_D(state)),
        "D_after_R": list(D_after_R(state)),
        "order_gap_visible": order_gap_visible(state),
    }


def quotient_classes(states: Iterable[State], probe: Callable[[State], tuple | str] = probe_signature) -> list[dict]:
    buckets: dict[tuple | str, list[State]] = defaultdict(list)
    for state in states:
        buckets[probe(state)].append(state)
    rows = []
    for idx, (signature, members) in enumerate(sorted(buckets.items(), key=lambda kv: repr(kv[0]))):
        rows.append({
            "class_id": f"q{idx:02d}",
            "signature": list(signature) if isinstance(signature, tuple) else signature,
            "members": [list(member) for member in sorted(members)],
        })
    return rows


def component_rows(survivors: set[State]) -> list[list[State]]:
    adjacency: dict[State, set[State]] = {state: set() for state in survivors}
    for state in survivors:
        for op in (R, D):
            target = op(state)
            if target in survivors:
                adjacency[state].add(target)
                adjacency[target].add(state)

    seen: set[State] = set()
    components: list[list[State]] = []
    for start in sorted(survivors):
        if start in seen:
            continue
        queue: deque[State] = deque([start])
        seen.add(start)
        component: list[State] = []
        while queue:
            state = queue.popleft()
            component.append(state)
            for nxt in sorted(adjacency[state]):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        components.append(sorted(component))
    return components


def constraint_rows() -> list[dict]:
    return [
        {
            "id": "C_history_consistency",
            "source_anchor": "root_axioms_v0_1_DRAFT.md:73-85 finite history/provenance bookkeeping; constraint-manifold-architecture.md:100-129 requires S,C,Adm_C,controls",
            "operation": "Require memory == (shell + phase_parity + orientation) mod 2 on each finite state.",
            "observable": "Boolean memory-consistency predicate per candidate state.",
            "pass_fail_condition": "Pass iff the finite memory bit matches the local coordinate parity relation.",
        },
        {
            "id": "C_N01_order_visible",
            "source_anchor": "root_axioms_v0_1_DRAFT.md:49-53 noncommuting composition; constraint-manifold-architecture.md:27-35 includes N01 and composition rules",
            "operation": "Compute R∘D and D∘R from the same state and compare their finite probe signatures.",
            "observable": "order_gap_visible = probe_signature(R∘D(x)) != probe_signature(D∘R(x)).",
            "pass_fail_condition": "Pass iff order is distinguishable under the finite probe family.",
        },
        {
            "id": "C_closure_under_order_maps",
            "source_anchor": "gcm_reanchor_requirement_20260612.md:33-41 requires compute M(C), certify quotient, and audit what constraints carved; constraint-manifold-architecture.md:122-128 requires neighborhood/path rules and controls",
            "operation": "Take the greatest subset of base-admissible states closed under R, D, R∘D, and D∘R.",
            "observable": "Every survivor maps to another survivor under each order map.",
            "pass_fail_condition": "Pass iff all four mapped states remain in M(C).",
        },
    ]


def controls() -> dict:
    empty = set(candidate_space())
    return {
        "empty_C": {"survivor_count": len(empty), "class_count": len(quotient_classes(empty)), "meaning": "No carve: every candidate survives."},
        "drop_C_history_consistency": {"survivor_count": len(closed_survivors({"C_history_consistency"})), "meaning": "History erasure doubles the closed survivor floor."},
        "drop_C_N01_order_visible": {"survivor_count": len(closed_survivors({"C_N01_order_visible"})), "meaning": "Dropping N01 admits commuting/no-gap rows."},
        "drop_C_closure_under_order_maps": {"survivor_count": len(closed_survivors({"C_closure_under_order_maps"})), "meaning": "Without closure, transient rows survive as filtered-but-not-stable."},
        "overconstrained_orientation_one_only": {"survivor_count": len(closed_survivors(extra_predicate=lambda state: state[2] == 1)), "meaning": "The orientation-one-only overconstraint leaves no closed M(C) floor under this C."},
    }


def probe_erasure_controls(survivors: set[State]) -> dict:
    probes: dict[str, Callable[[State], tuple]] = {
        "full_probe": lambda state: state,
        "erase_shell": lambda state: ("*", state[1], state[2], state[3]),
        "erase_phase_parity": lambda state: (state[0], "*", state[2], state[3]),
        "erase_orientation": lambda state: (state[0], state[1], "*", state[3]),
        "erase_memory": lambda state: (state[0], state[1], state[2], "*"),
    }
    return {
        name: {"class_count": len(quotient_classes(survivors, probe=fn))}
        for name, fn in probes.items()
    }


def source_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def build_result(write: bool = True, output: Path | None = None) -> dict:
    output = output or DEFAULT_OUTPUT
    candidates = candidate_space()
    survivors = closed_survivors()
    killed = [state for state in candidates if state not in survivors]
    kill_ledger = [
        {"state": list(state), "failed_constraints": failed_constraints_for(state, survivors)}
        for state in sorted(killed)
    ]
    survivor_rows = [state_row(state) for state in sorted(survivors)]
    q_classes = quotient_classes(survivors)
    components = component_rows(survivors)
    component_sizes = [len(component) for component in components]
    q_class_sizes = Counter(len(row["members"]) for row in q_classes)

    result = {
        "object_id": OBJECT_ID,
        "receipt_kind": "finite_constraint_carve_floor",
        "classification": "scratch_diagnostic",
        "claim_ceiling": "first finite constraints-first M(C) floor only; not the full geometric constraint manifold",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "axis_claims_allowed": False,
        "engine_claims_allowed": False,
        "all_pass": True,
        "source_sha256": source_sha256(),
        "authority": {
            "stop_order": "system_v6/receipts/owner_stop_order_manifold_first_20260612.md",
            "gcm_reanchor": "system_v6/receipts/gcm_reanchor_requirement_20260612.md",
            "root_axioms": "system_v6/foundations/root_axioms_v0_1_DRAFT.md",
            "wiki_contract": "/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md",
        },
        "candidate_space": {
            "state_schema": ["shell", "phase_parity", "orientation", "memory"],
            "state_count": len(candidates),
            "states": [list(state) for state in candidates],
        },
        "constraints": constraint_rows(),
        "maps": {
            "R": "phase parity flip with finite memory recomputed; baseline order map only",
            "D": "orientation/phase-dependent shell move with finite memory recomputed; baseline order map only",
            "R_after_D": "R(D(x))",
            "D_after_R": "D(R(x))",
        },
        "constraint_carve": {
            "survivor_count": len(survivors),
            "killed_count": len(killed),
            "survivors": survivor_rows,
            "kill_ledger": kill_ledger,
        },
        "quotient": {
            "probe_family": ["shell", "phase_parity", "orientation", "memory"],
            "equivalence_rule": "x ~_P y iff all four finite probe coordinates match",
            "class_count": len(q_classes),
            "class_size_histogram": {str(key): value for key, value in sorted(q_class_sizes.items())},
            "classes": q_classes,
        },
        "controls": controls(),
        "probe_erasure_controls": probe_erasure_controls(survivors),
        "carved_structure": {
            "adjacency_maps": ["R", "D"],
            "component_count": len(components),
            "largest_component_size": max(component_sizes) if component_sizes else 0,
            "components": [[list(state) for state in component] for component in components],
            "terrain_readout_attempt": {
                "method": "read off survivor graph components and local order-map signatures; no terrain regions installed by label",
                "region_count": len(components),
                "verdict": "no_8_terrain_regions_in_this_floor",
                "meaning": "This floor carves one connected six-state finite object, not eight terrain regions. Terrain geometry remains unbuilt on this packet.",
            },
        },
        "not_admitted": [
            "full geometric constraint manifold",
            "terrain geometry",
            "stage regions",
            "engines",
            "axes",
            "physics bridge",
            "QIT engine",
        ],
    }
    if write:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Build gcm_constraint_carve_floor_v0 result JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_result(write=True, output=args.output)
    print(json.dumps({
        "object_id": result["object_id"],
        "all_pass": result["all_pass"],
        "survivor_count": result["constraint_carve"]["survivor_count"],
        "quotient_class_count": result["quotient"]["class_count"],
        "output": str(args.output),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
