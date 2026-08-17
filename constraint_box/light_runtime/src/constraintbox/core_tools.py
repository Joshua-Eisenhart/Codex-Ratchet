"""Declared CB Light tool contracts and their bounded exercises.

The registry is a current integration surface, not an official or permanent
"core": tools become usable for a given operation only when their live probes
and that operation's gate admit them.  This module intentionally contains no
optional-engine imports; missing tools are reported as observations.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
from typing import Any


# The default CLI must work from an installed wheel, where the checkout-level
# ``config/`` directory is intentionally absent.  Keep the registry beside the
# code that consumes it and include it as package data.
_REGISTRY = Path(__file__).with_name("core_tool_registry_v9.json")


def _declared_tool_contract_ids(body: dict[str, Any]) -> tuple[str, ...]:
    tools = body.get("tools")
    if not isinstance(tools, list) or not tools:
        raise RuntimeError("CB Light declared tool registry is empty")
    ids = tuple(row.get("id") for row in tools if isinstance(row, dict))
    if len(ids) != len(tools) or any(not isinstance(tool_id, str) or not tool_id for tool_id in ids):
        raise RuntimeError("CB Light declared tool registry has invalid identities")
    if len(set(ids)) != len(ids):
        raise RuntimeError("CB Light declared tool registry has duplicate identities")
    return ids


def _initial_declared_tool_contract_ids() -> tuple[str, ...]:
    return _declared_tool_contract_ids(json.loads(_REGISTRY.read_text(encoding="utf-8")))


DECLARED_TOOL_CONTRACT_IDS = _initial_declared_tool_contract_ids()
# Compatibility only for legacy callers.  It is derived from the packaged
# registry rather than a hard-coded official tool membership list.
CORE_TOOL_IDS = DECLARED_TOOL_CONTRACT_IDS


def _import_visible(import_name: str) -> bool:
    try:
        return importlib.util.find_spec(import_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def load_registry() -> dict[str, Any]:
    body = json.loads(_REGISTRY.read_text(encoding="utf-8"))
    _declared_tool_contract_ids(body)
    return body


def doctor() -> dict[str, Any]:
    registry = load_registry()
    rows: list[dict[str, Any]] = []
    for declared in registry["tools"]:
        distribution = declared["distribution"]
        import_name = declared["import"]
        present = _import_visible(import_name)
        try:
            version = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            version = None
        rows.append(
            {
                "id": declared["id"],
                "distribution": distribution,
                "import": import_name,
                "import_visible": present,
                "version": version,
                "required_apis": declared["required_apis"],
                "integration_level": declared["integration_level"],
            }
        )
    return {
        "schema": "constraintbox.core-doctor.v9",
        "product_version": registry["version"],
        "tool_contract_ids": [row["id"] for row in registry["tools"]],
        "core_tool_ids": [row["id"] for row in registry["tools"]],
        "rows": rows,
        "missing": [row["id"] for row in rows if not row["import_visible"]],
    }


def _pydantic_boundary_model() -> Any:
    """Return the strict bounded model used for hostile-input refusal probes."""
    from typing import Literal

    from pydantic import BaseModel, ConfigDict, Field

    class TypedHostileInputBoundary(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

        operation: Literal["bounded_request"]
        maximum: int = Field(ge=0, le=2)

    return TypedHostileInputBoundary


def _validate_pydantic_boundary(raw: dict[str, Any]) -> dict[str, Any]:
    """Use Pydantic's strict typed boundary for one finite request shape."""
    model = _pydantic_boundary_model()
    value = model.model_validate(dict(raw), strict=True)
    return value.model_dump(mode="json")


def _jsonschema_boundary_schema() -> dict[str, Any]:
    """Return the independent finite JSON Schema boundary used by CB Light."""
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://constraintbox.local/schema/bounded-request-v1",
        "type": "object",
        "additionalProperties": False,
        "required": ["operation", "maximum"],
        "properties": {
            "operation": {"const": "bounded_request"},
            "maximum": {"type": "integer", "minimum": 0, "maximum": 2},
        },
    }


def _validate_jsonschema_boundary(raw: dict[str, Any]) -> dict[str, Any]:
    """Use jsonschema's independent validator for the bounded request shape."""
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(_jsonschema_boundary_schema())
    validator.validate(raw)
    return {"operation": raw["operation"], "maximum": raw["maximum"]}


def _exercise_z3() -> dict[str, Any]:
    import z3

    x = z3.Int("x")
    solver = z3.Solver()
    solver.add(x >= 0, x <= 2, x != 1)
    status = solver.check()
    model_value = solver.model()[x].as_long() if status == z3.sat else None
    return {"api": ["Int", "Solver.add", "Solver.check", "ModelRef.__getitem__"], "status": str(status), "witness": model_value}


def _exercise_cvc5() -> dict[str, Any]:
    import cvc5
    from cvc5 import Kind

    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    integers = solver.getIntegerSort()
    x = solver.mkConst(integers, "x")
    solver.assertFormula(solver.mkTerm(Kind.GEQ, x, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, x, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, x, solver.mkInteger(1)))
    result = solver.checkSat()
    witness = solver.getValue(x).getIntegerValue() if result.isSat() else None
    return {
        "api": [
            "Solver",
            "mkConst",
            "assertFormula",
            "checkSat",
            "getValue",
        ],
        "status": str(result),
        "is_sat": bool(result.isSat()),
        "witness": witness,
    }


def _exercise_sympy() -> dict[str, Any]:
    import sympy

    x = sympy.symbols("x")
    expanded = sympy.expand((x - 1) * (x + 1))
    polynomial = sympy.Poly(expanded, x)
    return {"api": ["symbols", "expand", "Poly.all_coeffs"], "expanded": str(expanded), "coefficients": [int(value) for value in polynomial.all_coeffs()]}


def _exercise_rustworkx() -> dict[str, Any]:
    import rustworkx

    graph = rustworkx.PyDiGraph()
    nodes = graph.add_nodes_from(["request", "symbolic", "solve", "rewrite", "decision"])
    graph.add_edges_from_no_data([(nodes[0], nodes[1]), (nodes[1], nodes[2]), (nodes[2], nodes[3]), (nodes[3], nodes[4])])
    order = [graph[index] for index in rustworkx.topological_sort(graph)]
    return {"api": ["PyDiGraph", "add_nodes_from", "add_edges_from_no_data", "topological_sort"], "order": order, "edge_count": graph.num_edges()}


def _exercise_maude() -> dict[str, Any]:
    import maude

    initialized = maude.init(loadPrelude=False, randomSeed=0, advise=False, handleInterrupts=False)
    source = "mod CB-V9 is sorts State . ops s0 s1 : -> State . rl [advance] : s0 => s1 . endm"
    maude.input(source)
    module = maude.getModule("CB-V9")
    term = None if module is None else module.parseTerm("s0")
    applications = [] if term is None else list(term.apply("advance", minDepth=0, maxDepth=0))
    rewritten = str(applications[0][0]) if applications else None
    return {"api": ["init", "input", "getModule", "Module.parseTerm", "Term.apply"], "initialized": initialized is True, "module_loaded": module is not None, "rewritten": rewritten}


def _exercise_automaton() -> dict[str, Any]:
    """Cross-check the fixed state carrier consumed by transition_mini_lev."""
    from automaton.machines import FiniteMachine

    machine = FiniteMachine()
    for state in ("idle", "running", "done"):
        machine.add_state(state, terminal=state == "done")
    machine.add_transition("idle", "running", "start")
    machine.add_transition("running", "done", "finish")
    machine.initialize("idle")
    machine.process_event("start")
    finish_actionable = machine.is_actionable_event("finish")
    start_actionable = machine.is_actionable_event("start")
    return {
        "api": [
            "machines.FiniteMachine",
            "FiniteMachine.add_state",
            "FiniteMachine.add_transition",
            "FiniteMachine.initialize",
            "FiniteMachine.process_event",
            "FiniteMachine.is_actionable_event",
        ],
        "initial_state": "idle",
        "event": "start",
        "state": machine.current_state,
        "terminated": bool(machine.terminated),
        "finish_actionable_after_start": bool(finish_actionable),
        "start_actionable_after_start": bool(start_actionable),
    }


def _exercise_pydantic() -> dict[str, Any]:
    payload = _validate_pydantic_boundary(
        {"operation": "bounded_request", "maximum": 2}
    )
    return {
        "api": [
            "BaseModel",
            "ConfigDict",
            "Field",
            "BaseModel.model_validate",
            "BaseModel.model_dump",
        ],
        "payload": payload,
        "strict": True,
        "extra_policy": "forbid",
    }


def _exercise_jsonschema() -> dict[str, Any]:
    payload = _validate_jsonschema_boundary(
        {"operation": "bounded_request", "maximum": 2}
    )
    return {
        "api": [
            "Draft202012Validator",
            "Draft202012Validator.validate",
            "ValidationError",
        ],
        "payload": payload,
        "schema_draft": "2020-12",
        "independent_schema_boundary": True,
    }


def exercise() -> dict[str, Any]:
    registry = load_registry()
    exercises = {
        "python.z3": _exercise_z3(),
        "python.cvc5": _exercise_cvc5(),
        "python.sympy": _exercise_sympy(),
        "python.rustworkx": _exercise_rustworkx(),
        "python.maude": _exercise_maude(),
        "python.automaton": _exercise_automaton(),
        "python.pydantic": _exercise_pydantic(),
        "python.jsonschema": _exercise_jsonschema(),
    }
    declared_ids = tuple(row["id"] for row in registry["tools"])
    if set(exercises) != set(declared_ids):
        raise RuntimeError(
            "declared tool contracts and exercise adapters differ: "
            f"declared={declared_ids!r}, adapters={tuple(exercises)!r}"
        )
    observations = {tool_id: exercises[tool_id] for tool_id in declared_ids}
    canonical = json.dumps(observations, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema": "constraintbox.core-exercise.v9",
        "product_version": registry["version"],
        "fixture": "finite_two-witness_ordered-rewrite_v1",
        "observations": observations,
        "observation_sha256": hashlib.sha256(canonical).hexdigest(),
        "claim_ceiling": (
            f"{len(observations)}_declared_tool_function_exercises_only; "
            "no operation selection or adoption"
        ),
        "promotion_allowed": False,
    }
