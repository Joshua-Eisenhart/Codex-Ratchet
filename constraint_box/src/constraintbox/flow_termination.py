"""Structural termination check for Mini-Lev FlowPolicy graphs.

The Mini-Lev kernel (``mini_levos.py``) guarantees halting by budget
exhaustion: ``max_steps`` bounds the loop, ``max_visits_per_node`` bounds
revisits, and ``max_retries`` bounds persisted RETRY transitions
(mini_levos.py:1852, 1867, 1990, 2037).  Its construction-time validation
also enforces, with a hand-rolled Kahn's algorithm (``_is_dag``,
mini_levos.py:808), that non-RETRY node-to-node edges form a DAG
(mini_levos.py:1012).

This module runs both core tools on the actual FlowPolicy. The package's
``mini_lev_topology`` module proves the graph property (acyclic, reachability)
on the REAL policy object via rustworkx and workflow_graph. This module
provides an independent termination analysis using the same graph library
and adds an SMT-based proof via z3:

* rustworkx builds the real ``PyDiGraph`` (nodes, terminals, signal-labelled
  edges) and computes what only a graph library gives: the simple-cycle
  inventory, the strongly connected components, whether every flow node
  reaches a terminal, and whether any terminal is unreachable from the entry
  node.
* z3 is asserted on the proposition "there EXISTS a directed cycle through
  the flow-node graph that can be traversed without consuming the retry
  budget".  UNSAT of that proposition is the termination proof in this
  project's preferred form: structural impossibility.

Encoding (stated precisely):

* One Bool variable ``on_cycle::<node_id>`` per flow node.  Terminals carry
  no variables: a transition source must be a flow node
  (mini_levos.py:954), so terminals are sinks and cannot lie on a cycle.
* A "budget-free" edge is a transition whose target is a flow node and whose
  signal is not RETRY.  A persisted RETRY is the only transition that
  consumes a named per-edge budget counter (``retries``,
  mini_levos.py:2037-2041) and is converted to HOLD once
  ``retries >= max_retries`` (mini_levos.py:1990-1993).  ``max_steps`` and
  ``max_visits_per_node`` are deliberately excluded from the encoding: every
  step consumes them, so including them would make the proposition
  vacuously UNSAT and the check decorative.  The question asked is whether
  the graph structure alone, with only the retry meter, excludes unbounded
  looping.
* Constraint 1: ``Or(on_cycle::n for all flow nodes n)`` — the candidate
  cycle-support set is non-empty.
* Constraint 2, per flow node ``n``:
  ``Implies(on_cycle::n, Or(on_cycle::m for m in budget_free_successors(n)))``
  — every member of the set has a budget-free successor inside the set.  A
  node with no budget-free successors gets ``Or()`` which is False, so it
  can never be in the set.

Equivalence: SAT iff a budget-free directed cycle exists.  A cycle's node
set satisfies both constraints; conversely a model gives a non-empty finite
set in which every node has a budget-free successor inside the set, so
following successors must revisit a node, which closes a budget-free cycle.

What UNSAT licenses: on the encoded (from_node, signal, to_node) graph,
every directed cycle traverses at least one edge whose only signals are
RETRY, so each traversal of any cycle consumes the retry budget and the
wave can loop at most ``max_retries`` times before RETRY is converted to
HOLD, which every node maps to the HOLD terminal (mini_levos.py:966-973,
999-1010).  The wave loops AND ratchets: termination is structural, not
merely step-counter exhaustion.

What UNSAT does NOT license: nothing about the runtime code faithfully
implementing the transition map, nothing about hook behaviour, byte
budgets, the execution lease, or wall-clock liveness, and nothing about any
policy not passed to this checker.  It is a claim about the extracted graph
under the stated reading of the retry accounting, not about the runtime.

Cross-check: the rustworkx lane classifies every simple cycle by whether it
can be traversed budget-free.  Any budget-free cycle contains a simple
budget-free cycle (its edges are a subset), so "no budget-free simple
cycle" must agree with z3 UNSAT.  Disagreement raises
``FlowTerminationError`` instead of picking a winner.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .mini_levos import (
    _TERMINALS,
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookResult,
    HookSignal,
    MiniLevError,
    MiniLevRuntime,
    handler_code_sha256,
)

SCHEMA = "constraintbox.flow-termination-check.v1"
VERDICT_RATCHETS = "RATCHETS"
VERDICT_CAN_SPIN = "CAN_SPIN"
_PROPOSITION = (
    "EXISTS a directed cycle through the flow-node graph traversable "
    "without consuming the retry budget"
)


class FlowTerminationError(RuntimeError):
    """The termination check could not run, or its two lanes disagreed."""


def extract_flow_graph(policy: FlowPolicy) -> dict[str, Any]:
    """Extract the directed graph of a FlowPolicy without judging it.

    This is deliberately a plain read of the frozen dataclass: it must work
    on policies the kernel would refuse, so the negative control can be
    analysed.  It only rejects shapes it cannot read as a graph.
    """

    if type(policy) is not FlowPolicy:
        raise FlowTerminationError("policy must be one frozen FlowPolicy")
    node_ids: list[str] = []
    for node in policy.nodes:
        if type(node) is not FlowNode:
            raise FlowTerminationError("flow nodes must be FlowNode values")
        node_ids.append(node.node_id)
    if len(set(node_ids)) != len(node_ids):
        raise FlowTerminationError("duplicate node_id in policy nodes")
    terminals = [name for name in policy.terminal_nodes]
    unknown_terminals = sorted(set(terminals) - _TERMINALS)
    if unknown_terminals:
        raise FlowTerminationError(
            f"terminal_nodes outside the kernel terminal set: {unknown_terminals}"
        )
    known = set(node_ids) | set(terminals)
    edges: list[dict[str, str]] = []
    for transition in policy.transitions:
        if type(transition) is not FlowTransition:
            raise FlowTerminationError("transitions must be FlowTransition values")
        if not isinstance(transition.signal, HookSignal):
            raise FlowTerminationError("transition signal must be a HookSignal")
        if transition.from_node not in set(node_ids):
            raise FlowTerminationError(
                f"transition source is not a flow node: {transition.from_node}"
            )
        if transition.to_node not in known:
            raise FlowTerminationError(
                f"transition target is not a node or terminal: {transition.to_node}"
            )
        edges.append(
            {
                "from_node": transition.from_node,
                "signal": transition.signal.value,
                "to_node": transition.to_node,
            }
        )
    if policy.entry_node not in set(node_ids):
        raise FlowTerminationError("entry node is not a flow node")
    return {
        "flow_id": policy.flow_id,
        "entry_node": policy.entry_node,
        "nodes": node_ids,
        "terminals": terminals,
        "edges": edges,
        "budgets": {
            "max_steps": policy.max_steps,
            "max_visits_per_node": policy.max_visits_per_node,
            "max_retries": policy.max_retries,
        },
    }


def _budget_free_successors(graph: dict[str, Any]) -> dict[str, set[str]]:
    """Flow-node successors reachable without consuming the retry budget."""

    successors: dict[str, set[str]] = {node: set() for node in graph["nodes"]}
    node_set = set(graph["nodes"])
    for edge in graph["edges"]:
        if edge["to_node"] in node_set and edge["signal"] != HookSignal.RETRY.value:
            successors[edge["from_node"]].add(edge["to_node"])
    return successors


def rustworkx_wave_analysis(graph: dict[str, Any]) -> dict[str, Any]:
    """Build the real PyDiGraph and compute cycle/SCC/reachability facts.

    Deleting this lane loses: the concrete simple-cycle witnesses, the SCC
    structure, the every-node-reaches-a-terminal audit, the
    unreachable-terminal audit, and the independent cross-check on the z3
    verdict.  None of those are produced by the z3 encoding.
    """

    import rustworkx

    digraph = rustworkx.PyDiGraph()
    names = [*graph["nodes"], *graph["terminals"]]
    indices = digraph.add_nodes_from(names)
    index_of = dict(zip(names, indices))
    name_of = dict(zip(indices, names))
    digraph.add_edges_from(
        [
            (
                index_of[edge["from_node"]],
                index_of[edge["to_node"]],
                edge["signal"],
            )
            for edge in graph["edges"]
        ]
    )

    node_set = set(graph["nodes"])
    signals_between: dict[tuple[str, str], set[str]] = {}
    for edge in graph["edges"]:
        signals_between.setdefault(
            (edge["from_node"], edge["to_node"]), set()
        ).add(edge["signal"])

    def _canonical_rotation(cycle: list[str]) -> tuple[str, ...]:
        pivot = cycle.index(min(cycle))
        return tuple(cycle[pivot:] + cycle[:pivot])

    cycles: list[dict[str, Any]] = []
    seen_rotations: set[tuple[str, ...]] = set()
    for raw_cycle in rustworkx.simple_cycles(digraph):
        named = [name_of[index] for index in raw_cycle]
        rotation = _canonical_rotation(named)
        if rotation in seen_rotations:
            continue
        seen_rotations.add(rotation)
        pairs = [
            (named[position], named[(position + 1) % len(named)])
            for position in range(len(named))
        ]
        budget_free_traversal = all(
            any(
                signal != HookSignal.RETRY.value
                for signal in signals_between.get(pair, set())
            )
            for pair in pairs
        )
        retry_metered_pairs = sorted(
            f"{source}->{target}"
            for source, target in pairs
            if signals_between.get((source, target), set())
            == {HookSignal.RETRY.value}
        )
        cycles.append(
            {
                "nodes": list(rotation),
                "budget_free_traversal": budget_free_traversal,
                "retry_metered_edges": retry_metered_pairs,
            }
        )
    cycles.sort(key=lambda row: row["nodes"])

    components = [
        sorted(name_of[index] for index in component)
        for component in rustworkx.strongly_connected_components(digraph)
    ]
    nontrivial_sccs = sorted(
        component for component in components if len(component) > 1
    )

    terminal_indices = {index_of[name] for name in graph["terminals"]}
    nodes_not_reaching_terminal = sorted(
        node
        for node in graph["nodes"]
        if not (rustworkx.descendants(digraph, index_of[node]) & terminal_indices)
    )
    entry_reach = rustworkx.descendants(digraph, index_of[graph["entry_node"]])
    entry_reach.add(index_of[graph["entry_node"]])
    terminals_unreachable_from_entry = sorted(
        name for name in graph["terminals"] if index_of[name] not in entry_reach
    )
    flow_nodes_unreachable_from_entry = sorted(
        name for name in graph["nodes"] if index_of[name] not in entry_reach
    )

    return {
        "tool": "rustworkx",
        "node_count": len(names),
        "edge_count": len(graph["edges"]),
        "simple_cycles": cycles,
        "budget_free_cycle_found": any(
            row["budget_free_traversal"] for row in cycles
        ),
        "strongly_connected_components": sorted(components),
        "nontrivial_sccs": nontrivial_sccs,
        "nodes_not_reaching_terminal": nodes_not_reaching_terminal,
        "terminals_unreachable_from_entry": terminals_unreachable_from_entry,
        "flow_nodes_unreachable_from_entry": flow_nodes_unreachable_from_entry,
        "flow_node_set_note": (
            "cycle facts concern flow nodes only; terminals have no outgoing"
            " transitions (mini_levos.py:954) so they cannot lie on a cycle"
        ),
    }


def z3_nonterminating_cycle_probe(graph: dict[str, Any]) -> dict[str, Any]:
    """Assert the budget-free-cycle proposition; UNSAT is the ratchet proof.

    Deleting this lane loses: the structural-impossibility certificate in
    the project's preferred proof form (UNSAT under the stated encoding) and
    the decision path that does not depend on cycle enumeration being
    complete.  The rustworkx lane does not produce an UNSAT certificate.
    """

    import z3

    successors = _budget_free_successors(graph)
    on_cycle = {
        node: z3.Bool(f"on_cycle::{node}") for node in graph["nodes"]
    }
    solver = z3.Solver()
    solver.add(z3.Or([on_cycle[node] for node in graph["nodes"]]))
    for node in graph["nodes"]:
        solver.add(
            z3.Implies(
                on_cycle[node],
                z3.Or([on_cycle[target] for target in sorted(successors[node])]),
            )
        )
    status = solver.check()
    if status not in (z3.sat, z3.unsat):
        raise FlowTerminationError(f"z3 returned neither sat nor unsat: {status}")
    witness_nodes: list[str] = []
    if status == z3.sat:
        model = solver.model()
        witness_nodes = sorted(
            node
            for node in graph["nodes"]
            if z3.is_true(model.eval(on_cycle[node], model_completion=True))
        )
    return {
        "tool": "z3",
        "proposition": _PROPOSITION,
        "variables": sorted(f"on_cycle::{node}" for node in graph["nodes"]),
        "constraints": [
            "the candidate cycle-support set is non-empty",
            "every member has a budget-free successor inside the set",
        ],
        "budget_free_edge_definition": (
            "a transition whose target is a flow node and whose signal is"
            " not RETRY; persisted RETRY is the only per-edge budget"
            " consumer (mini_levos.py:2037-2041) and converts to HOLD at"
            " the retry ceiling (mini_levos.py:1990-1993)"
        ),
        "status": str(status),
        "witness_support_set": witness_nodes,
        "unsat_licenses": (
            "every directed cycle in the encoded graph consumes the retry"
            " budget, so the wave loops at most max_retries times:"
            " structural termination of the encoded graph"
        ),
        "unsat_does_not_license": (
            "any claim about the runtime implementation, hook behaviour,"
            " byte budgets, the execution lease, or unencoded policies"
        ),
    }


def check_flow_termination(policy: FlowPolicy) -> dict[str, Any]:
    """Run both lanes on one FlowPolicy and cross-check their verdicts."""

    graph = extract_flow_graph(policy)
    rustworkx_report = rustworkx_wave_analysis(graph)
    z3_report = z3_nonterminating_cycle_probe(graph)

    z3_spin = z3_report["status"] == "sat"
    rustworkx_spin = rustworkx_report["budget_free_cycle_found"]
    if z3_spin != rustworkx_spin:
        raise FlowTerminationError(
            "lane disagreement: z3 says "
            f"{z3_report['status']} but rustworkx budget-free cycle"
            f" inventory says {rustworkx_spin}; refusing to pick a winner"
        )
    return {
        "schema": SCHEMA,
        "flow_id": graph["flow_id"],
        "graph": graph,
        "rustworkx": rustworkx_report,
        "z3": z3_report,
        "lanes_agree": True,
        "verdict": VERDICT_CAN_SPIN if z3_spin else VERDICT_RATCHETS,
        "claim_scope": (
            "a claim about the extracted (from_node, signal, to_node) graph"
            " under the cited retry accounting; not a runtime liveness proof"
        ),
    }


# --- negative control ------------------------------------------------------
#
# A policy that genuinely CAN spin: spin-a -> spin-b -> spin-a on OBSERVED
# signals, so the cycle consumes no retry budget.  The FlowPolicy dataclass
# is frozen but unvalidated, so this value constructs; the kernel's own
# construction-time validation is expected to refuse it at the non-RETRY DAG
# check (mini_levos.py:1012).  Both facts are reported, not assumed.


def _spin_hook_a(context: dict[str, Any]) -> HookResult:
    return HookResult(HookSignal.OBSERVED, {"spin": "a"})


def _spin_hook_b(context: dict[str, Any]) -> HookResult:
    return HookResult(HookSignal.OBSERVED, {"spin": "b"})


def spinning_control_policy() -> FlowPolicy:
    """A FlowPolicy whose only cycle is budget-free.  It must read CAN_SPIN."""

    return FlowPolicy(
        flow_id="flow-termination-negative-control",
        entry_node="spin-a",
        nodes=(
            FlowNode("spin-a", "spin-hook-a"),
            FlowNode("spin-b", "spin-hook-b"),
        ),
        transitions=(
            FlowTransition("spin-a", HookSignal.OBSERVED, "spin-b"),
            FlowTransition("spin-a", HookSignal.PARKED, "PARKED"),
            FlowTransition("spin-a", HookSignal.HOLD, "HOLD"),
            FlowTransition("spin-b", HookSignal.OBSERVED, "spin-a"),
            FlowTransition("spin-b", HookSignal.PARKED, "PARKED"),
            FlowTransition("spin-b", HookSignal.HOLD, "HOLD"),
        ),
        terminal_nodes=("PARKED", "HOLD"),
        required_nodes=(),
        max_steps=8,
        max_visits_per_node=4,
        max_retries=1,
        max_context_bytes=8_192,
        max_event_bytes=65_536,
        max_receipt_bytes=524_288,
        claim_ceiling="scratch_diagnostic",
    )


def _spin_control_registrations() -> tuple[HookRegistration, ...]:
    source_path = Path(__file__).resolve()
    from .mini_levos import _sha256_file

    source_sha256 = _sha256_file(source_path)
    return tuple(
        HookRegistration(
            hook_id=hook_id,
            kind=HookKind.HOOK,
            handler=handler,
            source_path=source_path,
            source_sha256=source_sha256,
            code_sha256=handler_code_sha256(handler),
            allowed_signals=(HookSignal.OBSERVED, HookSignal.PARKED),
        )
        for hook_id, handler in (
            ("spin-hook-a", _spin_hook_a),
            ("spin-hook-b", _spin_hook_b),
        )
    )


def kernel_admission_probe(
    policy: FlowPolicy,
    registrations: tuple[HookRegistration, ...],
    scratch_root: Path,
) -> dict[str, Any]:
    """Ask the kernel itself whether it admits the policy at construction.

    Constructs a MiniLevRuntime (which runs the kernel's own
    ``_build_policy_material`` validation) against a scratch ledger path.
    Nothing is executed and nothing durable is written by construction.
    """

    ledger_path = (
        Path(scratch_root).expanduser().resolve()
        / f"{policy.flow_id}-admission-probe-ledger.jsonl"
    )
    try:
        MiniLevRuntime(
            policy,
            registrations,
            run_id="flow-termination-admission-probe",
            ledger_path=ledger_path,
        )
    except MiniLevError as exc:
        return {"kernel_admitted": False, "kernel_error": str(exc)}
    return {"kernel_admitted": True, "kernel_error": None}


def negative_control_report(scratch_root: Path) -> dict[str, Any]:
    """Run the checker and the kernel on the spinning control policy."""

    policy = spinning_control_policy()
    check = check_flow_termination(policy)
    admission = kernel_admission_probe(
        policy, _spin_control_registrations(), scratch_root
    )
    control_caught = check["verdict"] == VERDICT_CAN_SPIN
    return {
        "policy": "spinning_control_policy",
        "checker_verdict": check["verdict"],
        "checker_caught_spin": control_caught,
        "z3_status": check["z3"]["status"],
        "z3_witness_support_set": check["z3"]["witness_support_set"],
        "rustworkx_budget_free_cycles": [
            row
            for row in check["rustworkx"]["simple_cycles"]
            if row["budget_free_traversal"]
        ],
        "kernel_admission": admission,
        "finding": (
            "the FlowPolicy dataclass constructs (it is frozen but"
            " unvalidated); the kernel's construction-time validation is the"
            " surface that refuses it, so the checker is exercised on the"
            " raw policy value"
        ),
    }


def load_real_proposal_policy(scratch_root: Path) -> FlowPolicy:
    """Build the real `constraintbox run` FlowPolicy via its own builder.

    Uses ``proposal_minilev_flow._build_runtime`` with a scratch controller
    state root, so the returned policy is the exact object the proposal flow
    validates and executes, not a re-transcription of it.
    """

    from .execution_lease import ExecutionLeaseStore
    from .mini_levos import ControllerMonotonicClock
    from .proposal_minilev_flow import (
        _build_runtime,
        _controller_lease_clock_id,
        _controller_state_root,
    )

    scratch = Path(scratch_root).expanduser().resolve()
    flow_root = scratch / "flow-termination-probe-flow"
    state_root, lease_state_path = _controller_state_root(
        scratch / "flow-termination-probe-state",
        flow_root=flow_root,
    )
    lease_store = ExecutionLeaseStore(lease_state_path)
    clock_id = _controller_lease_clock_id(state_root, lease_state_path)
    runtime = _build_runtime(
        run_id="flow-termination-real-policy-probe",
        ledger_path=flow_root / "flow-termination-probe-ledger.jsonl",
        execution_lease_store=lease_store,
        execution_lease_clock=ControllerMonotonicClock(clock_id=clock_id),
        execution_lease_clock_id=clock_id,
    )
    return runtime.policy


def main(argv: list[str] | None = None) -> int:
    """Check the real proposal policy, then the mandatory negative control.

    Exit 0 only when the real policy reads RATCHETS, the control reads
    CAN_SPIN, and the kernel refuses the control at construction.  Any other
    combination exits 1 with the full report on stdout.
    """

    import tempfile

    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        raise SystemExit("flow_termination takes no arguments")
    with tempfile.TemporaryDirectory(
        prefix="constraintbox-flow-termination-"
    ) as scratch:
        scratch_root = Path(scratch)
        real_policy = load_real_proposal_policy(scratch_root / "real")
        real_check = check_flow_termination(real_policy)
        control = negative_control_report(scratch_root / "control")
    report = {
        "schema": SCHEMA,
        "real_policy_check": real_check,
        "negative_control": control,
    }
    sys.stdout.write(json.dumps(report, indent=2, sort_keys=True))
    sys.stdout.write("\n")
    healthy = (
        real_check["verdict"] == VERDICT_RATCHETS
        and control["checker_caught_spin"]
        and control["kernel_admission"]["kernel_admitted"] is False
    )
    return 0 if healthy else 1


if __name__ == "__main__":
    raise SystemExit(main())
