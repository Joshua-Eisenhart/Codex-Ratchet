"""
frontier_search_operator.py

Cached frontier search with abstract state keys, budgets, and
heuristic scores.

Design doc: §AlphaGeometry-style Search — search-control over
structured state.  Also incorporates §DreamCoder Abstraction
Learning (motif mining from traces) and §Algorithmic Information
Theory (trace compression).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from system_v4.skills.runtime_state_kernel import (
    RuntimeState, Transform, FnTransform, StepEvent, BoundaryTag,
    utc_iso, guard_transition,
)


@dataclass
class FrontierNode:
    state: RuntimeState
    score: float
    trace: list[StepEvent] = field(default_factory=list)


@dataclass
class SearchResult:
    found: bool = False
    winning_node: FrontierNode | None = None
    states_explored: int = 0
    frontier_peak: int = 0
    seen_keys: int = 0


def abstract_frontier_key(state: RuntimeState) -> str:
    """Coarse key for dedup — region + phase band + sorted boundaries."""
    import json
    return json.dumps({
        "region": state.region,
        "phase_band": state.phase_band(4),
        "boundaries": sorted(b.value for b in state.boundaries),
    }, sort_keys=True)


def default_heuristic(state: RuntimeState) -> float:
    """Score states by how close they are to 'admissible'."""
    score = 0.0
    if BoundaryTag.ADMISSIBLE in state.boundaries:
        score += 100.0
    if BoundaryTag.FRONTIER in state.boundaries:
        score += 10.0
    if BoundaryTag.BLOCKED in state.boundaries:
        score -= 50.0
    if BoundaryTag.DEGENERATE in state.boundaries:
        score -= 100.0
    return score


def frontier_search(
    seed: RuntimeState,
    ops: list[Transform],
    budget: int = 200,
    heuristic: Callable[[RuntimeState], float] | None = None,
    goal: Callable[[RuntimeState], bool] | None = None,
) -> SearchResult:
    """Best-first search over structured state-space."""
    if heuristic is None:
        heuristic = default_heuristic
    if goal is None:
        goal = lambda s: BoundaryTag.ADMISSIBLE in s.boundaries

    frontier: list[FrontierNode] = [
        FrontierNode(state=seed, score=heuristic(seed)),
    ]
    seen: set[str] = set()
    explored = 0
    peak = 1

    while frontier and budget > 0:
        frontier.sort(key=lambda n: -n.score)
        current = frontier.pop(0)
        budget -= 1
        explored += 1

        key = abstract_frontier_key(current.state)
        if key in seen:
            continue
        seen.add(key)

        if goal(current.state):
            return SearchResult(
                found=True, winning_node=current,
                states_explored=explored, frontier_peak=peak,
                seen_keys=len(seen),
            )

        for op in ops:
            try:
                next_state = op.apply(current.state)
            except Exception:
                continue

            violations = guard_transition(current.state, next_state)
            if violations:
                continue

            event = StepEvent(
                at=utc_iso(), op=op.transform_id,
                before_hash=current.state.hash(),
                after_hash=next_state.hash(),
            )
            new_node = FrontierNode(
                state=next_state,
                score=heuristic(next_state),
                trace=[*current.trace, event],
            )
            frontier.append(new_node)

        if len(frontier) > peak:
            peak = len(frontier)

    return SearchResult(
        found=False, states_explored=explored,
        frontier_peak=peak, seen_keys=len(seen),
    )


# ── Motif mining (from §DreamCoder / §AIT) ──────────────────────────────

def trace_signature(trace: list[StepEvent]) -> str:
    """Compress a trace to its op sequence."""
    return " -> ".join(e.op for e in trace)


def mine_motifs(traces: list[list[StepEvent]]) -> dict[str, int]:
    """Extract recurring op-sequence motifs from traces."""
    counts: dict[str, int] = {}
    for trace in traces:
        sig = trace_signature(trace)
        counts[sig] = counts.get(sig, 0) + 1
    return counts


def rank_by_compression(traces: list[list[StepEvent]]) -> list[tuple[str, int]]:
    """Rank motifs by frequency (compression potential)."""
    motifs = mine_motifs(traces)
    return sorted(motifs.items(), key=lambda kv: -kv[1])


# ── Self-test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seed = RuntimeState(region="start", phase_index=0, phase_period=8)

    ops = [
        FnTransform("advance", lambda s: s.advance_phase(1)),
        FnTransform("mark_admissible",
                     lambda s: s.add_boundary(BoundaryTag.ADMISSIBLE)),
        FnTransform("add_frontier",
                     lambda s: s.add_boundary(BoundaryTag.FRONTIER)),
    ]

    r = frontier_search(seed, ops, budget=50)
    assert r.found, "Should find admissible state"
    assert r.winning_node is not None
    assert BoundaryTag.ADMISSIBLE in r.winning_node.state.boundaries

    # Motif mining
    traces = [r.winning_node.trace] * 3  # repeat to create motif
    motifs = rank_by_compression(traces)
    assert len(motifs) >= 1

    print(f"PASS: frontier_search_operator self-test "
          f"(explored={r.states_explored}, peak={r.frontier_peak}, "
          f"trace_len={len(r.winning_node.trace)}, motifs={len(motifs)})")
