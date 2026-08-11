"""The v9 ConstraintBox core: exactly five third-party tools.

This module intentionally contains no optional-engine imports. Importing it is
safe on a CB-only installation; missing tools are reported as observations.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
from typing import Any


CORE_TOOL_IDS = ("python.z3", "python.cvc5", "python.sympy", "python.rustworkx", "python.maude")
# The default CLI must work from an installed wheel, where the checkout-level
# ``config/`` directory is intentionally absent.  Keep the registry beside the
# code that consumes it and include it as package data.
_REGISTRY = Path(__file__).with_name("core_tool_registry_v9.json")


def _import_visible(import_name: str) -> bool:
    try:
        return importlib.util.find_spec(import_name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def load_registry() -> dict[str, Any]:
    body = json.loads(_REGISTRY.read_text(encoding="utf-8"))
    ids = tuple(row["id"] for row in body["tools"])
    if ids != CORE_TOOL_IDS:
        raise RuntimeError(f"CB core registry drift: {ids!r}")
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
        "core_tool_ids": list(CORE_TOOL_IDS),
        "rows": rows,
        "missing": [row["id"] for row in rows if not row["import_visible"]],
    }


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


def exercise() -> dict[str, Any]:
    registry = load_registry()
    observations = {
        "python.z3": _exercise_z3(),
        "python.cvc5": _exercise_cvc5(),
        "python.sympy": _exercise_sympy(),
        "python.rustworkx": _exercise_rustworkx(),
        "python.maude": _exercise_maude(),
    }
    canonical = json.dumps(observations, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema": "constraintbox.core-exercise.v9",
        "product_version": registry["version"],
        "fixture": "finite_two-witness_ordered-rewrite_v1",
        "observations": observations,
        "observation_sha256": hashlib.sha256(canonical).hexdigest(),
        "claim_ceiling": "five_tool_function_exercise_only",
        "promotion_allowed": False,
    }
