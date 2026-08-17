"""Bounded, local probe-field mapping for CB Light.

This module maps observations; it does not select tools, write CB state, launch
models, install hooks, or promote anything.  A field run is deliberately
ephemeral: it exercises a finite set of local Python APIs, records positive and
negative observations, then projects only *candidate* regions and local
ablation hypotheses.  The result is input to a later deterministic gate, not a
gate itself.

The first field deliberately covers typed/schema agreement, solver agreement,
symbolic boundaries, finite transitions, and graph topology.  It leaves
rewrite semantics and every external execution route as explicit unmapped
areas rather than fabricating coverage for them.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import importlib.metadata
import json
import os
import random
import re
import statistics
import sys
import time
from collections import Counter, defaultdict, deque
from pathlib import Path
from threading import Lock
from typing import Any, Iterable, Literal

import jsonschema
from pydantic import BaseModel, ConfigDict, Field, ValidationError


FIELD_SCHEMA = "constraintbox.basin-field.v1"
OUTCOME = Literal["ACCEPT", "REFUSE", "HOLD"]
FAMILY = Literal["packet", "solver", "symbolic", "transition", "topology", "rewrite", "parser", "coupling"]

_MAUDE_LOCK = Lock()
_MAUDE_MODULE_NAME = "CBLIGHTBASINREWRITE"
_MAUDE_SOURCE = (
    "mod CBLIGHTBASINREWRITE is sorts State . "
    "ops idle running done : -> State . "
    "rl [start] : idle => running . "
    "rl [finish] : running => done . endm"
)
_MAUDE_RULES = {
    ("start", "idle"): "running",
    ("finish", "running"): "done",
}


def canonical_bytes(value: Any) -> bytes:
    """Return the explicit, finite JSON identity used by this new field schema."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


class FieldConfig(BaseModel):
    """Bounded local work parameters, supplied per run rather than as policy."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    density: int = Field(default=8, ge=1, le=64)
    rounds: int = Field(default=3, ge=1, le=8)
    jobs: int = Field(default=max(1, min(16, os.cpu_count() or 1)), ge=1, le=64)
    seed: int = Field(default=0, ge=0)
    max_points_per_round: int | None = Field(default=None, ge=1)
    # Candidate lanes are an explicit run input.  They do not change the
    # baseline dependency set or imply that a candidate has been adopted.
    candidate_tool_ids: tuple[str, ...] = ()


class ProbePoint(BaseModel):
    """One deterministic coordinate in the local field."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    family: FAMILY
    round_index: int = Field(ge=0)
    index: int = Field(ge=0)
    coordinates: dict[str, Any]
    parent_id: str | None = None

    @property
    def point_id(self) -> str:
        # Parentage is an edge, not identity; it may be recomputed by a planner.
        material = self.model_dump(mode="json", exclude={"parent_id"})
        return f"p-{sha256_json(material)[:24]}"


class ParsedProbeDsl(BaseModel):
    """Typed target of the bounded parser-candidate grammar."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: Literal["observe", "quarantine", "read", "transition"]
    budget: int = Field(ge=0, le=3)
    degree: int = Field(ge=0, le=4)
    limit: int = Field(ge=0, le=4)


class ProbeObservation(BaseModel):
    """A real API observation, including refusal and HOLD outcomes."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    point: ProbePoint
    outcome: OUTCOME
    reason_codes: tuple[str, ...]
    tool_ids: tuple[str, ...]
    facts: dict[str, Any]
    observation_sha256: str


class FieldEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    target_id: str
    kind: Literal["mutation"]


class CandidateRegion(BaseModel):
    """A local, non-authoritative connected region of accepting observations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    region_id: str
    family: str
    point_ids: tuple[str, ...]
    boundary_edge_count: int
    hold_neighbor_count: int
    accepted_point_count: int
    interior_axis_count: int
    boundary_axis_count: int
    status: Literal["BASIN_CANDIDATE", "BOUNDARY_FRAGMENT", "OPEN_REGION"]


def _point(
    family: FAMILY,
    round_index: int,
    index: int,
    coordinates: dict[str, Any],
    previous: ProbePoint | None,
) -> ProbePoint:
    point = ProbePoint(
        family=family,
        round_index=round_index,
        index=index,
        coordinates=coordinates,
        parent_id=previous.point_id if previous else None,
    )
    return point


def _round_specs(config: FieldConfig, round_index: int) -> list[ProbePoint]:
    """Generate a dense but finite lattice of one-step mutation chains."""

    width = config.density + round_index
    specs: list[ProbePoint] = []
    index = 0

    # Typed packet and JSON Schema boundary pairs.  Every chain differs only in
    # payload mode, which makes the surrounding refusal shell explicit.
    for operation in ("observe", "quarantine", "read", "transition"):
        for budget in range(width + 2):
            previous: ProbePoint | None = None
            for payload_mode in ("valid", "missing", "extra", "wrong_type"):
                point = _point(
                    "packet",
                    round_index,
                    index,
                    {
                        "operation": operation,
                        "budget": budget,
                        "payload_mode": payload_mode,
                    },
                    previous,
                )
                specs.append(point)
                previous = point
                index += 1

    # Agreement grid.  The salt intentionally supplies repeated independent
    # solver constructions without pretending that repeats are new semantics.
    for salt in range(width + 2):
        for allow in (False, True):
            for schema_ok in (False, True):
                for route_ok in (False, True):
                    previous = None
                    for freshness in (False, True):
                        point = _point(
                            "solver",
                            round_index,
                            index,
                            {
                                "allow": allow,
                                "schema_ok": schema_ok,
                                "route_ok": route_ok,
                                "freshness": freshness,
                                "salt": salt,
                            },
                            previous,
                        )
                        specs.append(point)
                        previous = point
                        index += 1

    # A symbolic degree/limit lattice.  Coefficient perturbations make the
    # algebra real rather than a Boolean surrogate, while the degree threshold
    # gives every positive region an explicit boundary.
    for degree in range(5):
        for limit in range(5):
            previous = None
            for coefficient in range(-width, width + 1):
                point = _point(
                    "symbolic",
                    round_index,
                    index,
                    {
                        "degree": degree,
                        "limit": limit,
                        "coefficient": coefficient,
                    },
                    previous,
                )
                specs.append(point)
                previous = point
                index += 1

    # More than degree checking: symbolic identity and root cells use distinct
    # SymPy APIs and explicit false claims.  They are small stars so a wrong
    # algebraic claim remains adjacent to the exact valid construction.
    for branch in range(width * 16):
        left = branch - width
        right = left + 1 + (branch % 3)
        identity_base = _point(
            "symbolic",
            round_index,
            index,
            {
                "kind": "identity",
                "left": left,
                "right": right,
                "claim_delta": 0,
                "representation": "expanded",
                "branch": branch,
            },
            None,
        )
        specs.append(identity_base)
        index += 1
        for variant, change in (
            ("factored", {"representation": "factored"}),
            ("wrong_identity", {"claim_delta": 1}),
        ):
            point = _point(
                "symbolic",
                round_index,
                index,
                {**identity_base.coordinates, **change, "variant": variant},
                identity_base,
            )
            specs.append(point)
            index += 1

        roots_base = _point(
            "symbolic",
            round_index,
            index,
            {
                "kind": "roots",
                "left": left,
                "right": right,
                "candidate": left,
                "branch": branch,
                "variant": "root_member",
            },
            None,
        )
        specs.append(roots_base)
        index += 1
        root_refusal = _point(
            "symbolic",
            round_index,
            index,
            {**roots_base.coordinates, "candidate": right + 1, "variant": "root_nonmember"},
            roots_base,
        )
        specs.append(root_refusal)
        index += 1

    # Randomized only through an explicit seed.  It is a reproducible broad
    # transition shot, not an oracle or a model-generated test list.
    rng = random.Random((config.seed << 8) + round_index)
    for branch in range(width * 16):
        previous = None
        events: list[str] = []
        for depth in range(1, 8):
            events.append(rng.choice(("start", "finish", "repeat", "reset")))
            point = _point(
                "transition",
                round_index,
                index,
                {"events": tuple(events), "branch": branch, "depth": depth},
                previous,
            )
            specs.append(point)
            previous = point
            index += 1

    # Topology variations use a fixed carrier and vary exactly one mutation
    # class.  This is deliberately a map of a local graph operation, not a
    # claim that it contains a host, provider, or global execution perimeter.
    for group in range(width * 16):
        previous = None
        for mutation in ("baseline", "shortcut", "cycle", "remove"):
            point = _point(
                "topology",
                round_index,
                index,
                {"mutation": mutation, "group": group},
                previous,
            )
            specs.append(point)
            previous = point
            index += 1

    # Maude has a process-global runtime.  It receives a smaller, explicitly
    # serial rewrite lattice rather than being threaded beside pure-Python work.
    for branch in range(width * 8):
        base = _point(
            "rewrite",
            round_index,
            index,
            {"initial_state": "idle", "rule_label": "start", "branch": branch, "variant": "base"},
            None,
        )
        specs.append(base)
        index += 1
        for variant, change in (
            ("finish", {"initial_state": "running", "rule_label": "finish"}),
            ("wrong_label", {"rule_label": "advance"}),
            ("inapplicable", {"initial_state": "done"}),
            ("wrong_source", {"initial_state": "running"}),
        ):
            point = _point(
                "rewrite",
                round_index,
                index,
                {**base.coordinates, **change, "variant": variant},
                base,
            )
            specs.append(point)
            index += 1

    # Optional candidate lane: a bounded text probe grammar becomes a typed
    # local request and then a real coupled operation.  It is generated only
    # when this run explicitly requests the candidate; the baseline field does
    # not import or depend on it.
    if "lark" in config.candidate_tool_ids:
        for branch in range(width * 8):
            base = _point(
                "parser",
                round_index,
                index,
                {
                    "operation": ("observe", "quarantine", "read", "transition")[branch % 4],
                    "budget": branch % 4,
                    "degree": 2,
                    "limit": 2,
                    "case": "valid",
                    "branch": branch,
                },
                None,
            )
            specs.append(base)
            index += 1
            for case, change in (
                ("alternate_valid", {"operation": "read"}),
                ("typed_boundary", {"budget": 4}),
                ("coupling_refusal", {"limit": 1}),
                ("grammar_refusal", {"case": "grammar_refusal"}),
            ):
                point = _point(
                    "parser",
                    round_index,
                    index,
                    {**base.coordinates, **change, "case": case},
                    base,
                )
                specs.append(point)
                index += 1

    # Cross-tool cells are the first actual local operation coupling.  Each
    # star has one valid base and one-field mutations around it, so the map can
    # distinguish a packet, symbolic, transition, or topology shell instead of
    # simply counting isolated package exercises.
    for branch in range(width * 16):
        base = _point(
            "coupling",
            round_index,
            index,
            {
                "payload_mode": "valid",
                "degree": 2,
                "limit": 2,
                "coefficient": branch - width,
                "events": ("start", "finish"),
                "mutation": "baseline",
                "branch": branch,
                "variant": "base",
            },
            None,
        )
        specs.append(base)
        index += 1
        variants = (
            ("coefficient_shift", {"coefficient": base.coordinates["coefficient"] + 1}),
            ("shortcut", {"mutation": "shortcut"}),
            ("packet_extra", {"payload_mode": "extra"}),
            ("degree_over", {"limit": 1}),
            ("bad_transition", {"events": ("repeat",)}),
            ("cycle", {"mutation": "cycle"}),
        )
        for variant, change in variants:
            point = _point(
                "coupling",
                round_index,
                index,
                {**base.coordinates, **change, "variant": variant},
                base,
            )
            specs.append(point)
            index += 1

    if config.max_points_per_round is not None:
        return specs[: config.max_points_per_round]
    return specs


def _digest_observation(
    point: ProbePoint,
    outcome: OUTCOME,
    reason_codes: Iterable[str],
    tool_ids: Iterable[str],
    facts: dict[str, Any],
) -> str:
    return sha256_json(
        {
            "point": point.model_dump(mode="json"),
            "outcome": outcome,
            "reason_codes": list(reason_codes),
            "tool_ids": list(tool_ids),
            "facts": facts,
        }
    )


def _observation(
    point: ProbePoint,
    outcome: OUTCOME,
    reason_codes: Iterable[str],
    tool_ids: Iterable[str],
    facts: dict[str, Any],
) -> ProbeObservation:
    codes = tuple(sorted(set(reason_codes)))
    tools = tuple(sorted(set(tool_ids)))
    return ProbeObservation(
        point=point,
        outcome=outcome,
        reason_codes=codes,
        tool_ids=tools,
        facts=facts,
        observation_sha256=_digest_observation(point, outcome, codes, tools, facts),
    )


def _packet_probe(point: ProbePoint) -> ProbeObservation:
    base: dict[str, Any] = {
        "family": point.family,
        "round_index": point.round_index,
        "index": point.index,
        "coordinates": point.coordinates,
    }
    mode = point.coordinates["payload_mode"]
    if mode == "missing":
        payload = {key: value for key, value in base.items() if key != "coordinates"}
    elif mode == "extra":
        payload = {**base, "unexpected": True}
    elif mode == "wrong_type":
        payload = {**base, "index": "not-an-integer"}
    else:
        payload = base

    schema = ProbePoint.model_json_schema()
    schema_errors = tuple(
        sorted(error.message for error in jsonschema.Draft202012Validator(schema).iter_errors(payload))
    )
    try:
        ProbePoint.model_validate(payload)
        pydantic_error = None
    except ValidationError as exc:
        pydantic_error = exc.errors(include_url=False)

    pydantic_accepts = pydantic_error is None
    schema_accepts = not schema_errors
    facts = {
        "pydantic_accepts": pydantic_accepts,
        "jsonschema_accepts": schema_accepts,
        "payload_mode": mode,
    }
    if pydantic_accepts != schema_accepts:
        return _observation(
            point,
            "HOLD",
            ("HOLD_PACKET_VALIDATOR_DISAGREEMENT",),
            ("pydantic", "jsonschema"),
            facts,
        )
    if pydantic_accepts:
        return _observation(
            point,
            "ACCEPT",
            ("PACKET_TYPED_SCHEMA_AGREEMENT",),
            ("pydantic", "jsonschema"),
            facts,
        )
    return _observation(
        point,
        "REFUSE",
        ("PACKET_TYPED_SCHEMA_REFUSAL",),
        ("pydantic", "jsonschema"),
        facts,
    )


def _solver_statuses(point_id: str, expected: bool) -> tuple[str, str]:
    import cvc5
    import z3
    from cvc5 import Kind

    z3_solver = z3.Solver()
    gate = z3.Bool(f"gate_{point_id[-12:]}")
    z3_solver.add(gate == expected)
    z3_solver.add(gate)
    z3_status = str(z3_solver.check())

    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    integer = cvc5_solver.getIntegerSort()
    gate_term = cvc5_solver.mkConst(integer, f"gate_{point_id[-12:]}")
    zero = cvc5_solver.mkInteger(0)
    one = cvc5_solver.mkInteger(1)
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, gate_term, one))
    if not expected:
        cvc5_solver.assertFormula(cvc5_solver.mkTerm(Kind.EQUAL, gate_term, zero))
    cvc5_result = cvc5_solver.checkSat()
    cvc5_status = "sat" if cvc5_result.isSat() else "unsat" if cvc5_result.isUnsat() else str(cvc5_result)
    return z3_status, cvc5_status


def _solver_probe(point: ProbePoint) -> ProbeObservation:
    values = point.coordinates
    expected = bool(values["allow"] and values["schema_ok"] and values["route_ok"] and values["freshness"])
    z3_status, cvc5_status = _solver_statuses(point.point_id, expected)

    facts = {
        "expected": expected,
        "z3_status": z3_status,
        "cvc5_status": cvc5_status,
        "salt": values["salt"],
    }
    if z3_status != cvc5_status:
        return _observation(
            point,
            "HOLD",
            ("HOLD_SOLVER_DISAGREEMENT",),
            ("z3", "cvc5"),
            facts,
        )
    if expected and z3_status == "sat":
        return _observation(
            point,
            "ACCEPT",
            ("SOLVER_AGREEMENT_SAT",),
            ("z3", "cvc5"),
            facts,
        )
    if not expected and z3_status == "unsat":
        return _observation(
            point,
            "REFUSE",
            ("SOLVER_AGREEMENT_UNSAT",),
            ("z3", "cvc5"),
            facts,
        )
    return _observation(
        point,
        "HOLD",
        ("HOLD_SOLVER_UNEXPECTED_STATUS",),
        ("z3", "cvc5"),
        facts,
    )


def _symbolic_probe(point: ProbePoint) -> ProbeObservation:
    import sympy

    x = sympy.symbols("x")
    kind = str(point.coordinates.get("kind", "degree"))
    if kind == "identity":
        left = int(point.coordinates["left"])
        right = int(point.coordinates["right"])
        claim_delta = int(point.coordinates["claim_delta"])
        expression = sympy.expand((x + left) * (x - right))
        claimed = sympy.expand(x**2 + (left - right) * x - left * right + claim_delta)
        residual = sympy.simplify(expression - claimed)
        accepts = residual == 0
        facts = {
            "kind": kind,
            "expression": str(expression),
            "factored": str(sympy.factor(expression)),
            "claimed": str(claimed),
            "residual": str(residual),
            "representation": point.coordinates["representation"],
        }
        return _observation(
            point,
            "ACCEPT" if accepts else "REFUSE",
            ("SYMPY_IDENTITY_RESIDUAL_ZERO",) if accepts else ("SYMPY_IDENTITY_RESIDUAL_NONZERO",),
            ("sympy",),
            facts,
        )
    if kind == "roots":
        left = int(point.coordinates["left"])
        right = int(point.coordinates["right"])
        candidate = int(point.coordinates["candidate"])
        expression = sympy.expand((x - left) * (x - right))
        roots = {int(root) for root in sympy.solve(sympy.Eq(expression, 0), x)}
        accepts = candidate in roots
        facts = {
            "kind": kind,
            "expression": str(expression),
            "factored": str(sympy.factor(expression)),
            "roots": sorted(roots),
            "candidate": candidate,
            "candidate_value": int(sympy.Poly(expression, x).eval(candidate)),
        }
        return _observation(
            point,
            "ACCEPT" if accepts else "REFUSE",
            ("SYMPY_ROOT_MEMBER",) if accepts else ("SYMPY_ROOT_NONMEMBER",),
            ("sympy",),
            facts,
        )
    degree = int(point.coordinates["degree"])
    limit = int(point.coordinates["limit"])
    coefficient = int(point.coordinates["coefficient"])
    # The extra linear term ensures perturbations actually traverse SymPy's
    # expand/poly machinery even when the leading degree is zero.
    expression = sympy.expand(x**degree + coefficient * x + coefficient)
    observed_degree = int(sympy.Poly(expression, x).degree())
    accepts = observed_degree <= limit
    facts = {
        "expression": str(expression),
        "observed_degree": observed_degree,
        "limit": limit,
        "coefficient": coefficient,
    }
    return _observation(
        point,
        "ACCEPT" if accepts else "REFUSE",
        ("SYMPY_DEGREE_WITHIN_LIMIT",) if accepts else ("SYMPY_DEGREE_EXCEEDS_LIMIT",),
        ("sympy",),
        facts,
    )


def _transition_probe(point: ProbePoint) -> ProbeObservation:
    from automaton.machines import FiniteMachine

    transitions = {"idle": {"start": "running"}, "running": {"finish": "done"}, "done": {}}
    machine = FiniteMachine()
    for state in transitions:
        machine.add_state(state, terminal=state == "done")
    machine.add_transition("idle", "running", "start")
    machine.add_transition("running", "done", "finish")
    machine.initialize("idle")

    expected_state = "idle"
    expected_refusal = False
    actual_error: str | None = None
    for event in point.coordinates["events"]:
        next_state = transitions[expected_state].get(event)
        if next_state is None:
            expected_refusal = True
        else:
            expected_state = next_state
        try:
            machine.process_event(event)
        except Exception as exc:  # Library-specific refusal types are evidence, not policy.
            actual_error = type(exc).__name__
            break

    actual_refusal = actual_error is not None
    facts = {
        "events": list(point.coordinates["events"]),
        "expected_state": expected_state,
        "actual_state": machine.current_state,
        "expected_refusal": expected_refusal,
        "actual_refusal": actual_refusal,
        "actual_error": actual_error,
    }
    if expected_refusal != actual_refusal or (not actual_refusal and machine.current_state != expected_state):
        return _observation(
            point,
            "HOLD",
            ("HOLD_AUTOMATON_REFERENCE_DISAGREEMENT",),
            ("automaton",),
            facts,
        )
    if actual_refusal:
        return _observation(
            point,
            "REFUSE",
            ("AUTOMATON_EVENT_REFUSED",),
            ("automaton",),
            facts,
        )
    return _observation(
        point,
        "ACCEPT",
        ("AUTOMATON_TRANSITION_AGREEMENT",),
        ("automaton",),
        facts,
    )


def _has_path(edges: list[tuple[int, int]], source: int, target: int) -> bool:
    adjacency: dict[int, list[int]] = defaultdict(list)
    for left, right in edges:
        adjacency[left].append(right)
    queue: deque[int] = deque([source])
    seen = {source}
    while queue:
        current = queue.popleft()
        if current == target:
            return True
        for child in adjacency[current]:
            if child not in seen:
                seen.add(child)
                queue.append(child)
    return False


def _topology_probe(point: ProbePoint) -> ProbeObservation:
    import rustworkx

    graph = rustworkx.PyDiGraph()
    nodes = graph.add_nodes_from(["inbox", "gate", "executor", "quarantine", "receipt"])
    edges = [(nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3]), (nodes[3], nodes[4])]
    mutation = point.coordinates["mutation"]
    if mutation == "shortcut":
        edges.append((nodes[1], nodes[3]))
    elif mutation == "cycle":
        edges.append((nodes[4], nodes[0]))
    elif mutation == "remove":
        edges.pop(2)
    graph.add_edges_from_no_data(edges)
    acyclic = bool(rustworkx.is_directed_acyclic_graph(graph))
    reaches_receipt = _has_path(edges, nodes[0], nodes[4])
    order = [graph[node] for node in rustworkx.topological_sort(graph)] if acyclic else []
    accepts = acyclic and reaches_receipt
    facts = {
        "mutation": mutation,
        "acyclic": acyclic,
        "reaches_receipt": reaches_receipt,
        "edge_count": graph.num_edges(),
        "topological_order": order,
    }
    if accepts:
        return _observation(
            point,
            "ACCEPT",
            ("TOPOLOGY_ACYCLIC_PATH_EXISTS",),
            ("rustworkx",),
            facts,
        )
    reason = "TOPOLOGY_CYCLE_REFUSED" if not acyclic else "TOPOLOGY_PATH_REFUSED"
    return _observation(point, "REFUSE", (reason,), ("rustworkx",), facts)


def _maude_sequence(initial: str, labels: tuple[str, ...]) -> dict[str, Any]:
    """Apply a bounded fixed rewrite sequence under exact inventory custody."""

    import maude

    with _MAUDE_LOCK:
        initialized = maude.init(loadPrelude=False, randomSeed=0, advise=False, handleInterrupts=False)
        module = maude.getModule(_MAUDE_MODULE_NAME)
        if module is None:
            maude.input(_MAUDE_SOURCE)
            module = maude.getModule(_MAUDE_MODULE_NAME)
        if module is None:
            return {"status": "module_unavailable", "initialized": initialized is True, "module_loaded": False}
        rules = {
            (str(rule.getLabel()), str(rule.getLhs())): str(rule.getRhs())
            for rule in module.getRules()
        }
        exact_inventory = rules == _MAUDE_RULES and not list(module.getEquations())
        if not exact_inventory:
            return {
                "status": "inventory_drift",
                "initialized": initialized is True,
                "module_loaded": True,
                "exact_inventory": False,
            }
        term = module.parseTerm(initial)
        states = [initial]
        for label in labels:
            try:
                applications = list(term.apply(label, minDepth=0, maxDepth=0))
            except Exception:
                applications = []
            if len(applications) != 1:
                return {
                    "status": "rule_inapplicable",
                    "initialized": initialized is True,
                    "module_loaded": True,
                    "exact_inventory": True,
                    "states": states,
                    "failed_label": label,
                    "application_count": len(applications),
                }
            term = applications[0][0]
            states.append(str(term))
    return {
        "status": "ok",
        "initialized": initialized is True,
        "module_loaded": True,
        "exact_inventory": True,
        "states": states,
        "target": states[-1],
    }


def _rewrite_probe(point: ProbePoint) -> ProbeObservation:
    """Check one fixed local rewrite relation and explicit inapplicability."""

    initial = str(point.coordinates["initial_state"])
    rule_label = str(point.coordinates["rule_label"])
    witness = _maude_sequence(initial, (rule_label,))
    expected = _MAUDE_RULES.get((rule_label, initial))
    facts = {
        **witness,
        "initial_state": initial,
        "rule_label": rule_label,
        "expected": expected,
    }
    if witness["status"] == "module_unavailable":
        return _observation(point, "HOLD", ("HOLD_MAUDE_MODULE_UNAVAILABLE",), ("maude",), facts)
    if witness["status"] == "inventory_drift":
        return _observation(point, "HOLD", ("HOLD_MAUDE_MODULE_INVENTORY_DRIFT",), ("maude",), facts)
    if expected is not None and witness["status"] == "ok" and witness.get("target") == expected:
        return _observation(point, "ACCEPT", ("MAUDE_REWRITE_REFERENCE_AGREEMENT",), ("maude",), facts)
    if expected is None and witness["status"] == "rule_inapplicable":
        return _observation(point, "REFUSE", ("MAUDE_RULE_INAPPLICABLE",), ("maude",), facts)
    return _observation(point, "HOLD", ("HOLD_MAUDE_REWRITE_REFERENCE_DISAGREEMENT",), ("maude",), facts)


_PARSER_CANDIDATE_GRAMMAR = r"""
start: "probe" OPERATION "budget" "=" INT "degree" "=" INT "limit" "=" INT
OPERATION: "observe" | "quarantine" | "read" | "transition"
%import common.INT
%import common.WS
%ignore WS
"""
_PARSER_CANDIDATE_REFERENCE = re.compile(
    r"^probe (observe|quarantine|read|transition) budget=(\d+) degree=(\d+) limit=(\d+)$"
)


def _parser_candidate_text(point: ProbePoint) -> str:
    text = (
        f"probe {point.coordinates['operation']} budget={point.coordinates['budget']} "
        f"degree={point.coordinates['degree']} limit={point.coordinates['limit']}"
    )
    return text.replace("budget", "baddget", 1) if point.coordinates["case"] == "grammar_refusal" else text


def parse_probe_dsl(text: str) -> dict[str, Any]:
    """Parse one bounded text probe with replay and a stdlib reference check."""

    try:
        from lark import Lark
        from lark.exceptions import UnexpectedInput
    except ModuleNotFoundError as exc:
        return {"status": "unavailable", "exception_type": type(exc).__name__}
    parser = Lark(_PARSER_CANDIDATE_GRAMMAR, parser="lalr")
    reference_match = _PARSER_CANDIDATE_REFERENCE.fullmatch(text)
    reference = (
        {
            "operation": reference_match.group(1),
            "budget": int(reference_match.group(2)),
            "degree": int(reference_match.group(3)),
            "limit": int(reference_match.group(4)),
        }
        if reference_match
        else None
    )
    try:
        first = parser.parse(text)
        second = parser.parse(text)
        first_values = [str(value) for value in first.children]
        second_values = [str(value) for value in second.children]
        parsed = {
            "operation": first_values[0],
            "budget": int(first_values[1]),
            "degree": int(first_values[2]),
            "limit": int(first_values[3]),
        }
        replay = {
            "operation": second_values[0],
            "budget": int(second_values[1]),
            "degree": int(second_values[2]),
            "limit": int(second_values[3]),
        }
        return {
            "status": "parsed",
            "reference": reference,
            "parsed": parsed,
            "replay_equal": sha256_json(parsed) == sha256_json(replay),
        }
    except UnexpectedInput as exc:
        return {
            "status": "refused",
            "reference": reference,
            "parsed": None,
            "replay_equal": None,
            "parse_error": type(exc).__name__,
        }


def _parser_probe(point: ProbePoint) -> ProbeObservation:
    """Exercise the optional parser candidate into a typed coupled probe input."""

    text = _parser_candidate_text(point)
    parsed_result = parse_probe_dsl(text)
    if parsed_result["status"] == "unavailable":
        return _observation(
            point,
            "HOLD",
            ("HOLD_LARK_CANDIDATE_IMPORT_UNAVAILABLE",),
            ("lark",),
            parsed_result,
        )
    parsed = parsed_result["parsed"]
    reference = parsed_result["reference"]
    replay_equal = parsed_result["replay_equal"]
    parse_error = parsed_result.get("parse_error")

    facts: dict[str, Any] = {
        "text": text,
        "reference": reference,
        "parsed": parsed,
        "replay_equal": replay_equal,
        "parse_error": parse_error,
        "case": point.coordinates["case"],
    }
    if parsed is None:
        if reference is None:
            return _observation(point, "REFUSE", ("LARK_GRAMMAR_REFUSED",), ("lark",), facts)
        return _observation(point, "HOLD", ("HOLD_LARK_REFERENCE_DISAGREEMENT",), ("lark",), facts)
    if reference != parsed or not replay_equal:
        return _observation(point, "HOLD", ("HOLD_LARK_REFERENCE_OR_REPLAY_DRIFT",), ("lark",), facts)

    schema_errors = tuple(
        sorted(
            error.message
            for error in jsonschema.Draft202012Validator(ParsedProbeDsl.model_json_schema()).iter_errors(parsed)
        )
    )
    try:
        typed = ParsedProbeDsl.model_validate(parsed)
        pydantic_error = None
    except ValidationError as exc:
        typed = None
        pydantic_error = exc.errors(include_url=False)
    typed_accepts = typed is not None
    schema_accepts = not schema_errors
    facts.update(
        {
            "typed_accepts": typed_accepts,
            "jsonschema_accepts": schema_accepts,
            "pydantic_error": pydantic_error,
            "jsonschema_errors": schema_errors,
        }
    )
    if typed_accepts != schema_accepts:
        return _observation(
            point,
            "HOLD",
            ("HOLD_LARK_TYPED_SCHEMA_DISAGREEMENT",),
            ("lark", "pydantic", "jsonschema"),
            facts,
        )
    if not typed_accepts:
        return _observation(
            point,
            "REFUSE",
            ("LARK_TYPED_BOUNDARY_REFUSED",),
            ("lark", "pydantic", "jsonschema"),
            facts,
        )

    coupled = _coupling_probe(
        ProbePoint(
            family="coupling",
            round_index=point.round_index,
            index=point.index,
            coordinates={
                "payload_mode": "valid",
                "degree": typed.degree,
                "limit": typed.limit,
                "coefficient": typed.budget - 1,
                "events": ("start", "finish"),
                "mutation": "baseline",
                "branch": point.coordinates["branch"],
                "variant": f"parser-{point.coordinates['case']}",
            },
        )
    )
    facts["coupling_outcome"] = coupled.outcome
    facts["coupling_reasons"] = coupled.reason_codes
    tools = tuple(sorted({"lark", "pydantic", "jsonschema", *coupled.tool_ids}))
    if coupled.outcome == "ACCEPT":
        return _observation(point, "ACCEPT", ("LARK_TYPED_PROBE_CONSUMER_ACCEPT",), tools, facts)
    if coupled.outcome == "REFUSE":
        return _observation(point, "REFUSE", ("LARK_TYPED_PROBE_CONSUMER_REFUSED",), tools, facts)
    return _observation(point, "HOLD", ("HOLD_LARK_TYPED_PROBE_CONSUMER",), tools, facts)


def _coupling_probe(point: ProbePoint) -> ProbeObservation:
    """Exercise a typed local operation through all eight mapped Python APIs."""

    packet = _packet_probe(point)
    symbolic = _symbolic_probe(point)
    transition = _transition_probe(point)
    topology = _topology_probe(point)
    maude = _maude_sequence("idle", tuple(point.coordinates["events"]))
    maude_accepts = maude["status"] == "ok" and maude.get("target") == transition.facts["actual_state"]
    expected = all(
        observation.outcome == "ACCEPT" for observation in (packet, symbolic, transition, topology)
    ) and maude_accepts
    z3_status, cvc5_status = _solver_statuses(point.point_id, expected)
    facts = {
        "packet_outcome": packet.outcome,
        "symbolic_outcome": symbolic.outcome,
        "transition_outcome": transition.outcome,
        "topology_outcome": topology.outcome,
        "maude": maude,
        "maude_accepts": maude_accepts,
        "expected": expected,
        "z3_status": z3_status,
        "cvc5_status": cvc5_status,
        "variant": point.coordinates["variant"],
    }
    tools = ("pydantic", "jsonschema", "sympy", "automaton", "rustworkx", "maude", "z3", "cvc5")
    if z3_status != cvc5_status:
        return _observation(point, "HOLD", ("HOLD_COUPLING_SOLVER_DISAGREEMENT",), tools, facts)
    if expected and z3_status == "sat":
        return _observation(point, "ACCEPT", ("COUPLING_ALL_LOCAL_CONSTRAINTS_SAT",), tools, facts)
    if not expected and z3_status == "unsat":
        return _observation(point, "REFUSE", ("COUPLING_LOCAL_CONSTRAINT_REFUSED",), tools, facts)
    return _observation(point, "HOLD", ("HOLD_COUPLING_UNEXPECTED_STATUS",), tools, facts)


def _run_point(point: ProbePoint) -> ProbeObservation:
    try:
        if point.family == "packet":
            return _packet_probe(point)
        if point.family == "solver":
            return _solver_probe(point)
        if point.family == "symbolic":
            return _symbolic_probe(point)
        if point.family == "transition":
            return _transition_probe(point)
        if point.family == "topology":
            return _topology_probe(point)
        if point.family == "rewrite":
            return _rewrite_probe(point)
        if point.family == "parser":
            return _parser_probe(point)
        if point.family == "coupling":
            return _coupling_probe(point)
    except Exception as exc:  # Every unexpected local failure is a visible field hole.
        return _observation(
            point,
            "HOLD",
            ("HOLD_PROBE_EXCEPTION", type(exc).__name__),
            (),
            {"exception_type": type(exc).__name__, "exception": str(exc)},
        )
    raise AssertionError(f"unknown probe family: {point.family}")


def _mutation_edges(observations: Iterable[ProbeObservation]) -> list[FieldEdge]:
    by_id = {observation.point.point_id: observation for observation in observations}
    edges = [
        FieldEdge(source_id=observation.point.parent_id, target_id=observation.point.point_id, kind="mutation")
        for observation in observations
        if observation.point.parent_id and observation.point.parent_id in by_id
    ]
    return sorted(edges, key=lambda edge: (edge.source_id, edge.target_id))


def _candidate_regions(
    observations: list[ProbeObservation], edges: list[FieldEdge]
) -> list[CandidateRegion]:
    by_id = {observation.point.point_id: observation for observation in observations}
    accepted = {point_id for point_id, observation in by_id.items() if observation.outcome == "ACCEPT"}
    adjacency: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if edge.source_id in accepted and edge.target_id in accepted:
            adjacency[edge.source_id].add(edge.target_id)
            adjacency[edge.target_id].add(edge.source_id)

    regions: list[CandidateRegion] = []
    remaining = set(accepted)
    while remaining:
        root = min(remaining)
        component: set[str] = set()
        queue = deque([root])
        while queue:
            current = queue.popleft()
            if current in component:
                continue
            component.add(current)
            remaining.discard(current)
            queue.extend(adjacency[current] - component)
        families = {by_id[point_id].point.family for point_id in component}
        family = min(families) if len(families) == 1 else "mixed"
        boundary_edges = 0
        hold_neighbors = 0
        interior_axes: set[str] = set()
        boundary_axes: set[str] = set()
        for edge in edges:
            left, right = by_id[edge.source_id], by_id[edge.target_id]
            changed_axes = {
                key
                for key in set(left.point.coordinates) | set(right.point.coordinates)
                if left.point.coordinates.get(key) != right.point.coordinates.get(key)
            }
            if edge.source_id in component and edge.target_id in component:
                interior_axes.update(changed_axes)
            inside = (edge.source_id in component) ^ (edge.target_id in component)
            if not inside:
                continue
            outside_id = edge.target_id if edge.source_id in component else edge.source_id
            outside = by_id[outside_id]
            if outside.outcome == "REFUSE":
                boundary_edges += 1
                boundary_axes.update(changed_axes)
            elif outside.outcome == "HOLD":
                hold_neighbors += 1
        point_ids = tuple(sorted(component))
        qualifies = (
            len(point_ids) >= 3
            and boundary_edges >= 2
            and len(interior_axes) >= 2
            and len(boundary_axes) >= 2
            and not hold_neighbors
        )
        status: Literal["BASIN_CANDIDATE", "BOUNDARY_FRAGMENT", "OPEN_REGION"]
        if qualifies:
            status = "BASIN_CANDIDATE"
        elif boundary_edges:
            status = "BOUNDARY_FRAGMENT"
        else:
            status = "OPEN_REGION"
        regions.append(
            CandidateRegion(
                region_id=f"r-{sha256_json(point_ids)[:20]}",
                family=family,
                point_ids=point_ids,
                boundary_edge_count=boundary_edges,
                hold_neighbor_count=hold_neighbors,
                accepted_point_count=len(point_ids),
                interior_axis_count=len(interior_axes),
                boundary_axis_count=len(boundary_axes),
                status=status,
            )
        )
    return sorted(regions, key=lambda region: region.region_id)


def _tool_projection(observations: list[ProbeObservation], edges: list[FieldEdge]) -> list[dict[str, Any]]:
    """Derive run-local centrality hypotheses by ablation, never permanent roles."""

    by_id = {observation.point.point_id: observation for observation in observations}
    accepted_total = sum(observation.outcome == "ACCEPT" for observation in observations)
    tool_ids = sorted({tool for observation in observations for tool in observation.tool_ids})
    projection: list[dict[str, Any]] = []
    for tool_id in tool_ids:
        covered = [observation for observation in observations if tool_id in observation.tool_ids]
        accepted = sum(observation.outcome == "ACCEPT" for observation in covered)
        ablated_accepted = sum(
            observation.outcome == "ACCEPT" and tool_id not in observation.tool_ids
            for observation in observations
        )
        boundary_crossings = 0
        for edge in edges:
            left, right = by_id[edge.source_id], by_id[edge.target_id]
            if tool_id not in (*left.tool_ids, *right.tool_ids):
                continue
            if {left.outcome, right.outcome} == {"ACCEPT", "REFUSE"}:
                boundary_crossings += 1
        ablation_loss = accepted_total - ablated_accepted
        centrality = 0.0 if not accepted_total else round(
            (ablation_loss / accepted_total) + (boundary_crossings / max(1, len(edges))), 6
        )
        projection.append(
            {
                "tool_id": tool_id,
                "observations": len(covered),
                "accepted_observations": accepted,
                "ablation_accepted_loss": ablation_loss,
                "boundary_crossings": boundary_crossings,
                "local_centrality": centrality,
                "hypothesis": "field_support" if ablation_loss else "peripheral_in_this_field",
                "metric_ceiling": (
                    "sample-weighted local ablation plus observed boundary crossings; "
                    "not a global rank or a tool adoption decision"
                ),
            }
        )
    return sorted(projection, key=lambda row: (-row["local_centrality"], row["tool_id"]))


def _novelty(
    observations: Iterable[ProbeObservation], seen: set[tuple[str, str, tuple[str, ...]]]
) -> tuple[int, set[tuple[str, str, tuple[str, ...]]]]:
    signatures = {
        (observation.point.family, observation.outcome, observation.reason_codes)
        for observation in observations
    }
    return len(signatures - seen), seen | signatures


def _normalize_distribution(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _requirement_distribution(requirement: str) -> str | None:
    """Extract an unconditional PEP 508 name without making packaging a root."""

    parts = requirement.split(";", 1)
    material = parts[0]
    # Optional extras and platform-marked requirements are real metadata, but
    # not unconditional runtime edges for this local interpreter projection.
    # Omitting them is safer than accidentally promoting test/doc extras into
    # map topology; the count is retained below as an explicit blind spot.
    if len(parts) > 1:
        return None
    material = material.strip()
    match = re.match(r"^([A-Za-z0-9][A-Za-z0-9._-]*)", material)
    return _normalize_distribution(match.group(1)) if match else None


def _outer_dependency_projection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Map installed metadata topology; this intentionally makes no API claim."""

    import rustworkx

    by_name = {
        _normalize_distribution(str(row.get("distribution") or row.get("normalized_name"))): row
        for row in rows
        if isinstance(row, dict) and (row.get("distribution") or row.get("normalized_name"))
    }
    names = sorted(by_name)
    graph = rustworkx.PyDiGraph()
    node_index = {name: graph.add_node(name) for name in names}
    edges: set[tuple[str, str]] = set()
    missing_metadata: list[str] = []
    external_requirements: Counter[str] = Counter()
    conditional_requirements_ignored = 0
    for name in names:
        try:
            requirements = importlib.metadata.distribution(name).requires or []
        except importlib.metadata.PackageNotFoundError:
            missing_metadata.append(name)
            continue
        for requirement in requirements:
            if ";" in requirement:
                conditional_requirements_ignored += 1
            dependency = _requirement_distribution(requirement)
            if dependency is None:
                continue
            if dependency in node_index:
                edges.add((name, dependency))
            else:
                external_requirements[dependency] += 1
    edge_indexes = [(node_index[source], node_index[target]) for source, target in sorted(edges)]
    graph.add_edges_from_no_data(edge_indexes)
    incoming = Counter(target for _, target in edges)
    outgoing = Counter(source for source, _ in edges)
    topology = [
        {
            "distribution": name,
            "probe_disposition": by_name[name].get("disposition"),
            "candidate_in_degree": incoming[name],
            "candidate_out_degree": outgoing[name],
            "candidate_total_degree": incoming[name] + outgoing[name],
        }
        for name in names
    ]
    return {
        "kind": "installed_distribution_metadata",
        "node_count": graph.num_nodes(),
        "candidate_edge_count": graph.num_edges(),
        "acyclic": bool(rustworkx.is_directed_acyclic_graph(graph)),
        "missing_metadata": missing_metadata,
        "conditional_requirements_ignored": conditional_requirements_ignored,
        "external_requirement_frequency": dict(external_requirements.most_common()),
        "topology": sorted(
            topology,
            key=lambda row: (-row["candidate_total_degree"], row["distribution"]),
        ),
        "claim_ceiling": (
            "unconditional installed package metadata topology only; no API integration or tool role inferred"
        ),
    }


def load_outer_tool_matrix(path: Path | None) -> dict[str, Any] | None:
    """Load, but never upgrade, an independently generated 93-tool matrix."""

    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "constraintbox.cb-light-tool-probes.v1":
        raise ValueError("outer tool matrix has an unexpected schema")
    rows = payload.get("tool_decisions")
    if not isinstance(rows, list):
        raise ValueError("outer tool matrix has no tool_decisions list")
    typed_rows = [row for row in rows if isinstance(row, dict)]
    dispositions = Counter(str(row.get("disposition", "MISSING")) for row in typed_rows)
    return {
        "path": str(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "row_count": len(rows),
        "dispositions": dict(sorted(dispositions.items())),
        "dependency_projection": _outer_dependency_projection(typed_rows),
        "claim": "outer candidate evidence only; no operation integration inferred",
    }


def aggregate_campaign_summaries(paths: Iterable[Path]) -> dict[str, Any]:
    """Intersect only compatible local field runs into a seed-stability view."""

    paths = tuple(paths)
    if len(paths) < 2:
        raise ValueError("an ensemble needs at least two field summaries")
    payloads = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    if any(payload.get("schema") != FIELD_SCHEMA for payload in payloads):
        raise ValueError("ensemble input has an unexpected field schema")
    source_hashes = {payload.get("runtime", {}).get("source_sha256") for payload in payloads}
    if len(source_hashes) != 1 or None in source_hashes:
        raise ValueError("ensemble inputs do not share one field source identity")
    configs = [{key: value for key, value in payload["config"].items() if key != "seed"} for payload in payloads]
    if any(config != configs[0] for config in configs[1:]):
        raise ValueError("ensemble inputs differ outside their run seed")
    if any(payload.get("promotion_allowed") is not False for payload in payloads):
        raise ValueError("ensemble input exceeded the field claim ceiling")

    candidate_sets = [
        {
            region["region_id"]
            for region in payload.get("candidate_regions", [])
            if region.get("status") == "BASIN_CANDIDATE"
        }
        for payload in payloads
    ]
    stable_regions = set.intersection(*candidate_sets)
    union_regions = set.union(*candidate_sets)
    tool_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for payload in payloads:
        for row in payload.get("tool_projection", []):
            tool_rows[str(row["tool_id"])].append(row)
    tool_stability = []
    for tool_id, rows in sorted(tool_rows.items()):
        if len(rows) != len(payloads):
            continue
        centralities = [float(row["local_centrality"]) for row in rows]
        tool_stability.append(
            {
                "tool_id": tool_id,
                "runs": len(rows),
                "mean_local_centrality": round(statistics.fmean(centralities), 6),
                "min_local_centrality": round(min(centralities), 6),
                "max_local_centrality": round(max(centralities), 6),
                "range_local_centrality": round(max(centralities) - min(centralities), 6),
                "metric_ceiling": rows[0].get("metric_ceiling"),
            }
        )
    return {
        "schema": "constraintbox.basin-field-ensemble.v1",
        "profile": "cb_light",
        "source_sha256": next(iter(source_hashes)),
        "config_without_seed": configs[0],
        "inputs": [
            {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "seed": payload["config"]["seed"]}
            for path, payload in zip(paths, payloads, strict=True)
        ],
        "stable_candidate_region_ids": sorted(stable_regions),
        "candidate_region_stability": {
            "intersection": len(stable_regions),
            "union": len(union_regions),
            "jaccard": round(len(stable_regions) / len(union_regions), 6) if union_regions else 1.0,
        },
        "tool_stability": sorted(tool_stability, key=lambda row: (-row["mean_local_centrality"], row["tool_id"])),
        "promotion_allowed": False,
        "claim_ceiling": (
            "compatible local field-summary agreement only; no selection, adoption, host-hook, provider, "
            "model, portability, CB Heavy, promotion, or release claim"
        ),
    }


def write_ensemble(result: dict[str, Any], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "ensemble.json"
    path.write_bytes(canonical_bytes(result) + b"\n")
    return path


def run_campaign(config: FieldConfig, *, outer_tool_matrix: Path | None = None) -> dict[str, Any]:
    """Run finite local rounds until the configured budget or novelty plateau."""

    started = time.monotonic()
    all_observations: list[ProbeObservation] = []
    round_summaries: list[dict[str, Any]] = []
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    plateau_streak = 0
    stopped_reason = "ROUND_BUDGET_EXHAUSTED"

    for round_index in range(config.rounds):
        specs = _round_specs(config, round_index)
        # The local Z3 binding has a process-wide context teardown hazard when
        # many short-lived contexts are finalized on worker threads.  Keep the
        # dual-solver cells deterministic and serial; use the wide lane only
        # for independent Python calls.  This is measured runtime behavior,
        # not a permanent scheduling policy for every future tool.
        slow_specs = [point for point in specs if point.family in {"solver", "rewrite", "parser", "coupling"}]
        wide_specs = [point for point in specs if point.family not in {"solver", "rewrite", "parser", "coupling"}]
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.jobs) as pool:
            observations = list(pool.map(_run_point, wide_specs))
        observations.extend(_run_point(point) for point in slow_specs)
        observations.sort(key=lambda observation: observation.point.point_id)
        novel_signatures, seen = _novelty(observations, seen)
        if novel_signatures == 0:
            plateau_streak += 1
        else:
            plateau_streak = 0
        all_observations.extend(observations)
        round_summaries.append(
            {
                "round_index": round_index,
                "points": len(observations),
                "slow_lane_points": len(slow_specs),
                "wide_lane_points": len(wide_specs),
                "outcomes": dict(sorted(Counter(observation.outcome for observation in observations).items())),
                "new_outcome_signatures": novel_signatures,
            }
        )
        # Outcome signatures can plateau while the geometric field is still
        # gaining cells and edges.  Record that fact, but do not mislabel the
        # entire map as exhausted or terminate a configured local budget early.

    edges = _mutation_edges(all_observations)
    regions = _candidate_regions(all_observations, edges)
    outer = load_outer_tool_matrix(outer_tool_matrix)
    source_path = Path(__file__)
    return {
        "schema": FIELD_SCHEMA,
        "profile": "cb_light",
        "config": config.model_dump(mode="json"),
        "runtime": {
            "interpreter": sys.executable,
            "python_version": sys.version.split()[0],
            "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        },
        "rounds": round_summaries,
        "stopped_reason": stopped_reason,
        "outcome_signature_plateau_streak": plateau_streak,
        "counts": {
            "observations": len(all_observations),
            "edges": len(edges),
            "outcomes": dict(sorted(Counter(observation.outcome for observation in all_observations).items())),
            "candidate_regions": len(regions),
            "basin_candidates": sum(region.status == "BASIN_CANDIDATE" for region in regions),
            "boundary_fragments": sum(region.status == "BOUNDARY_FRAGMENT" for region in regions),
        },
        "observations": [observation.model_dump(mode="json") for observation in all_observations],
        "edges": [edge.model_dump(mode="json") for edge in edges],
        "candidate_regions": [region.model_dump(mode="json") for region in regions],
        "tool_projection": _tool_projection(all_observations, edges),
        "outer_tool_matrix": outer,
        "unmapped_areas": [
            "rewrite semantics: mapped inside one fixed local coupling only; broader rewrite theories remain unmapped",
            "external launch and hook behavior: intentionally outside this local field",
            "LLM proposals: deferred until this local field has a stable bounded projection",
            "JAX and Julia: deferred until a Python field gap is demonstrated",
        ],
        "promotion_allowed": False,
        "claim_ceiling": (
            "bounded local Python observations and run-local map hypotheses only; no selection, adoption, "
            "host-hook, provider, model, portability, CB Heavy, promotion, or release claim"
        ),
        "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
    }


def write_campaign(result: dict[str, Any], output_dir: Path) -> tuple[Path, Path]:
    """Persist reproducible observation rows and a summary outside authoritative CB state."""

    output_dir.mkdir(parents=True, exist_ok=True)
    field_path = output_dir / "field.jsonl"
    summary_path = output_dir / "summary.json"
    lines = [canonical_bytes(row).decode("utf-8") for row in result["observations"]]
    field_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    summary = {key: value for key, value in result.items() if key != "observations"}
    summary["field_sha256"] = hashlib.sha256(field_path.read_bytes()).hexdigest()
    summary_path.write_bytes(canonical_bytes(summary) + b"\n")
    return field_path, summary_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a bounded local CB Light basin field campaign.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--density", type=int, default=8)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=max(1, min(16, os.cpu_count() or 1)))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-points-per-round", type=int)
    parser.add_argument("--outer-tool-matrix", type=Path)
    parser.add_argument("--candidate-tool", dest="candidate_tool_ids", action="append", default=[])
    parser.add_argument(
        "--aggregate-summary",
        type=Path,
        action="append",
        help="Build a seed-stability projection from two or more compatible summaries.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.aggregate_summary:
        result = aggregate_campaign_summaries(args.aggregate_summary)
        output_path = write_ensemble(result, args.output_dir)
        print(
            json.dumps(
                {
                    "ensemble": str(output_path),
                    "candidate_region_stability": result["candidate_region_stability"],
                    "promotion_allowed": False,
                },
                sort_keys=True,
            )
        )
        return 0
    config = FieldConfig(
        density=args.density,
        rounds=args.rounds,
        jobs=args.jobs,
        seed=args.seed,
        max_points_per_round=args.max_points_per_round,
        candidate_tool_ids=tuple(sorted(set(args.candidate_tool_ids))),
    )
    result = run_campaign(config, outer_tool_matrix=args.outer_tool_matrix)
    field_path, summary_path = write_campaign(result, args.output_dir)
    print(
        json.dumps(
            {
                "field": str(field_path),
                "summary": str(summary_path),
                "counts": result["counts"],
                "stopped_reason": result["stopped_reason"],
                "promotion_allowed": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through module invocation.
    raise SystemExit(main())
