"""Deterministic Hypothesis probe families for two live ConstraintBox gates.

This module deliberately keeps generation separate from gate ownership.  It
only constructs typed inputs, applies one-field mutations, and records the
observed gate boundary.  The receipt has no wall-clock material.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from hypothesis import HealthCheck, given, settings, strategies as st

from .gate_operations import gate_sympy_flow_budgets
from .mini_levos import (
    FlowNode,
    FlowPolicy,
    FlowTransition,
    HookKind,
    HookRegistration,
    HookSignal,
    MiniLevError,
    _build_policy_material,
    handler_code_sha256,
)


def _stable_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def _scalar() -> st.SearchStrategy[Any]:
    return st.one_of(st.booleans(), st.integers(-2, 2), st.sampled_from(["a", "b"]))


def finite_problem_strategy() -> st.SearchStrategy[dict[str, Any]]:
    """Generate valid finite, typed constraint specs accepted by CB."""

    domains = st.lists(_scalar(), min_size=1, max_size=3, unique=True).map(lambda d: {"x": d})
    constraints = st.one_of(
        st.just([]),
        st.builds(
            lambda value: [{"op": "eq", "left": {"var": "x"}, "right": {"const": value}}],
            _scalar(),
        ),
    )
    return st.builds(lambda variables, clauses: {"variables": variables, "constraints": clauses}, domains, constraints)


def _probe_handler(_: dict[str, Any]):
    return None


def _registration(hook_id: str) -> HookRegistration:
    source = Path(__file__).resolve()
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    return HookRegistration(
        hook_id=hook_id,
        kind=HookKind.GATE,
        handler=_probe_handler,
        source_path=source,
        source_sha256=digest,
        code_sha256=handler_code_sha256(_probe_handler),
        allowed_signals=(HookSignal.PASS, HookSignal.BLOCKED, HookSignal.PARKED),
    )


def flow_policy_strategy() -> st.SearchStrategy[FlowPolicy]:
    """Generate a small valid policy with a positive terminal path."""

    nodes = tuple(FlowNode(name, f"hook-{name}") for name in ("a", "b"))
    transitions = (
        FlowTransition("a", HookSignal.PASS, "b"),
        FlowTransition("a", HookSignal.BLOCKED, "BLOCKED"),
        FlowTransition("a", HookSignal.PARKED, "PARKED"),
        FlowTransition("a", HookSignal.HOLD, "HOLD"),
        FlowTransition("b", HookSignal.PASS, "RELEASED"),
        FlowTransition("b", HookSignal.BLOCKED, "BLOCKED"),
        FlowTransition("b", HookSignal.PARKED, "PARKED"),
        FlowTransition("b", HookSignal.HOLD, "HOLD"),
    )
    policy = FlowPolicy(
        flow_id="generated-probe-flow.v1",
        entry_node="a",
        nodes=nodes,
        transitions=transitions,
        terminal_nodes=("RELEASED", "BLOCKED", "PARKED", "HOLD"),
        required_nodes=("a", "b"),
        max_steps=2,
        max_visits_per_node=2,
        max_retries=0,
        max_context_bytes=8192,
        max_event_bytes=65536,
        max_receipt_bytes=524288,
        claim_ceiling="generated probe only",
    )
    return st.just(policy)


def mutate_one_field(policy: FlowPolicy) -> list[tuple[str, FlowPolicy]]:
    """Return minimal policy mutations; each changes one dataclass field."""

    transitions = list(policy.transitions)
    transitions[0] = replace(transitions[0], to_node="a")
    return [
        ("max_steps", replace(policy, max_steps=0)),
        ("entry_node", replace(policy, entry_node="missing")),
        ("transitions[0].to_node", replace(policy, transitions=tuple(transitions))),
    ]


def _construction_probe(policy: FlowPolicy) -> tuple[str, str]:
    registrations = tuple(_registration(node.hook_id) for node in policy.nodes)
    try:
        _build_policy_material(policy, registrations)
    except Exception as exc:  # gate boundary is the tested output
        return "REFUSED", type(exc).__name__ + ":" + str(exc)
    return "ADMITTED", "construction_material_built"


def _sympy_probe(policy: FlowPolicy) -> tuple[str, str]:
    try:
        execution = gate_sympy_flow_budgets(policy)
    except Exception as exc:  # probe records a gate escape, never hides it
        return "UNCAUGHT_EXCEPTION", f"uncaught:{type(exc).__name__}:{exc}"
    return execution.verdict, execution.reason


def _collect(strategy: st.SearchStrategy[Any], count: int, fn: Callable[[Any], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    @settings(
        max_examples=count,
        derandomize=True,
        database=None,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )
    @given(strategy)
    def run(value: Any) -> None:
        if len(rows) < count:
            rows.append(fn(value))

    run()
    return rows


def generate_receipt() -> dict[str, Any]:
    policy = next(iter(_collect(flow_policy_strategy(), 1, lambda p: {"policy": p}))) ["policy"]
    families: dict[str, Any] = {}
    sympy_rows = []
    construction_rows = []
    parent_verdict, parent_reason = _sympy_probe(policy)
    parent_construction, parent_construction_reason = _construction_probe(policy)
    for field, mutant in mutate_one_field(policy):
        verdict, reason = _sympy_probe(mutant)
        sympy_rows.append({"field": field, "parent": [parent_verdict, parent_reason], "mutant": [verdict, reason], "flipped": verdict != parent_verdict})
        c_verdict, c_reason = _construction_probe(mutant)
        construction_rows.append({"field": field, "parent": [parent_construction, parent_construction_reason], "mutant": [c_verdict, c_reason], "flipped": c_verdict != parent_construction})
    families["cb:sympy-exact-gate"] = {"parent": [parent_verdict, parent_reason], "boundary_pairs": sympy_rows}
    families["mini_levos.construction"] = {"parent": [parent_construction, parent_construction_reason], "boundary_pairs": construction_rows}
    return {
        "schema": "constraintbox.generated-probe-coverage.v1",
        "determinism": {"derandomize": True, "database": None, "wall_clock_fields": []},
        "families": families,
        "reason_codes_reached": sorted({row["mutant"][1] for row in sympy_rows + construction_rows} | {parent_reason, parent_construction_reason}),
        "reason_codes_unreached": ["sympy_stdlib_crosscheck_disagreement"],
        "blind_fields": [row["field"] for row in sympy_rows + construction_rows if not row["flipped"]],
        "claim_ceiling": "bounded generated probes over two live validation paths; not exhaustive gate coverage",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-receipt", type=Path, required=True)
    args = parser.parse_args()
    receipt = generate_receipt()
    args.write_receipt.parent.mkdir(parents=True, exist_ok=True)
    args.write_receipt.write_bytes(_stable_json(receipt) + b"\n")
    fixture_path = Path(__file__).resolve().parents[2] / "fixtures" / "generated_probes" / "probe_cases_v1.json"
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    fixture_path.write_bytes(_stable_json(receipt["families"]) + b"\n")


if __name__ == "__main__":
    main()
