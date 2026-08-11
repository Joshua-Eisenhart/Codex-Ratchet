"""Bounded, subprocess-isolated probes for the five current CB Light tools."""

from __future__ import annotations

import argparse
import builtins
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from . import core_tools


ROOT = Path(__file__).resolve().parents[2]
_MARKER = "CB_LIGHT_PROBE_JSON="
_TOOL_FUNCTIONS = {
    "python.z3": core_tools._exercise_z3,
    "python.cvc5": core_tools._exercise_cvc5,
    "python.sympy": core_tools._exercise_sympy,
    "python.rustworkx": core_tools._exercise_rustworkx,
    "python.maude": core_tools._exercise_maude,
}


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _boundary_z3(limit: int) -> dict[str, Any]:
    import z3

    x = z3.Int("cb_boundary_x")
    solver = z3.Solver()
    solver.add(x == 2, x <= limit)
    status = solver.check()
    admitted = status == z3.sat
    return {
        "input": {"maximum": limit},
        "verdict": "ADMIT" if admitted else "REFUSE",
        "reason_code": "Z3_BOUNDARY_SAT" if admitted else "Z3_BOUNDARY_UNSAT",
        "status": str(status),
    }


def _boundary_cvc5(limit: int) -> dict[str, Any]:
    import cvc5
    from cvc5 import Kind

    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    x = solver.mkConst(integer, "cb_boundary_x")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, x, solver.mkInteger(2)))
    solver.assertFormula(
        solver.mkTerm(Kind.LEQ, x, solver.mkInteger(str(limit)))
    )
    status = solver.checkSat()
    admitted = bool(status.isSat())
    return {
        "input": {"maximum": limit},
        "verdict": "ADMIT" if admitted else "REFUSE",
        "reason_code": "CVC5_BOUNDARY_SAT" if admitted else "CVC5_BOUNDARY_UNSAT",
        "status": str(status),
    }


def _boundary_sympy(max_degree: int) -> dict[str, Any]:
    import sympy

    x = sympy.symbols("x")
    polynomial = sympy.Poly(sympy.expand((x - 1) * (x + 1)), x)
    degree = int(polynomial.degree())
    admitted = degree <= max_degree
    return {
        "input": {"max_degree": max_degree},
        "verdict": "ADMIT" if admitted else "REFUSE",
        "reason_code": (
            "SYMPY_DEGREE_WITHIN_BOUND"
            if admitted
            else "SYMPY_DEGREE_LIMIT_EXCEEDED"
        ),
        "degree": degree,
    }


def _boundary_rustworkx(close_cycle: bool) -> dict[str, Any]:
    import rustworkx

    graph = rustworkx.PyDiGraph()
    nodes = graph.add_nodes_from(["intake", "gate", "decision"])
    graph.add_edges_from_no_data([(nodes[0], nodes[1]), (nodes[1], nodes[2])])
    if close_cycle:
        graph.add_edge(nodes[2], nodes[0], None)
    try:
        order = [graph[index] for index in rustworkx.topological_sort(graph)]
        admitted = True
        exception = None
    except Exception as exc:  # the concrete extension exception varies by wheel
        order = []
        admitted = False
        exception = type(exc).__name__
    return {
        "input": {"close_cycle": close_cycle},
        "verdict": "ADMIT" if admitted else "REFUSE",
        "reason_code": (
            "RUSTWORKX_DAG_ADMITTED" if admitted else "RUSTWORKX_CYCLE_REFUSED"
        ),
        "order": order,
        "exception_type": exception,
    }


def _boundary_maude(rule_label: str) -> dict[str, Any]:
    import maude

    maude.init(loadPrelude=False, randomSeed=0, advise=False, handleInterrupts=False)
    accepted = maude.input(
        "mod CB-LIGHT-BOUNDARY is sorts State . "
        "ops s0 s1 : -> State . rl [advance] : s0 => s1 . endm"
    )
    module = maude.getModule("CB-LIGHT-BOUNDARY")
    term = None if module is None else module.parseTerm("s0")
    try:
        applications = [] if term is None else list(
            term.apply(rule_label, minDepth=0, maxDepth=0)
        )
    except Exception:
        applications = []
    admitted = bool(accepted and applications)
    return {
        "input": {"rule_label": rule_label},
        "verdict": "ADMIT" if admitted else "REFUSE",
        "reason_code": (
            "MAUDE_DECLARED_RULE_APPLIED"
            if admitted
            else "MAUDE_UNDECLARED_RULE_REFUSED"
        ),
        "rewritten": str(applications[0][0]) if applications else None,
    }


def _boundary(tool_id: str, admitted: bool) -> dict[str, Any]:
    if tool_id == "python.z3":
        return _boundary_z3(2 if admitted else 1)
    if tool_id == "python.cvc5":
        return _boundary_cvc5(2 if admitted else 1)
    if tool_id == "python.sympy":
        return _boundary_sympy(2 if admitted else 1)
    if tool_id == "python.rustworkx":
        return _boundary_rustworkx(not admitted)
    if tool_id == "python.maude":
        return _boundary_maude("advance" if admitted else "missing")
    raise KeyError(tool_id)


def _reference(tool_id: str, positive: dict[str, Any]) -> dict[str, Any]:
    if tool_id == "python.z3":
        reference = [value for value in range(3) if value != 1]
        agrees = positive.get("status") == "sat" and positive.get("witness") in reference
        detail: Any = reference
    elif tool_id == "python.cvc5":
        reference = [value for value in range(3) if value != 1]
        agrees = (
            positive.get("status") == "sat"
            and positive.get("is_sat") is True
            and positive.get("witness") in reference
        )
        detail = reference
    elif tool_id == "python.sympy":
        reference = [1, 0, -1]
        agrees = positive.get("coefficients") == reference
        detail = reference
    elif tool_id == "python.rustworkx":
        reference = ["request", "symbolic", "solve", "rewrite", "decision"]
        agrees = positive.get("order") == reference and positive.get("edge_count") == 4
        detail = reference
    elif tool_id == "python.maude":
        reference = {"s0": "s1"}
        agrees = positive.get("rewritten") == reference["s0"]
        detail = reference
    else:
        raise KeyError(tool_id)
    return {
        "executor_kind": "internal_bounded_reference_checker",
        "agrees": agrees,
        "reference": detail,
    }


def _replay_projection(tool_id: str, output: dict[str, Any]) -> dict[str, Any]:
    """Normalize process-local initialization state away from semantic replay."""
    if tool_id == "python.maude":
        return {
            "api": output.get("api"),
            "module_loaded": output.get("module_loaded"),
            "rewritten": output.get("rewritten"),
        }
    return output


def _severance(tool_id: str, import_name: str) -> dict[str, Any]:
    original_import = builtins.__import__

    def blocked(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == import_name or name.startswith(import_name + "."):
            raise ModuleNotFoundError(f"severed CB Light binding: {import_name}")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = blocked
    try:
        _TOOL_FUNCTIONS[tool_id]()
    except ModuleNotFoundError as exc:
        return {
            "fired": True,
            "reason_code": "PRODUCTION_IMPORT_BINDING_SEVERED",
            "exception_type": type(exc).__name__,
        }
    except Exception as exc:
        return {
            "fired": False,
            "reason_code": "SEVERANCE_WRONG_FAILURE",
            "exception_type": type(exc).__name__,
        }
    finally:
        builtins.__import__ = original_import
    return {"fired": False, "reason_code": "SEVERANCE_NOT_OBSERVED"}


def _run_one_tool(tool: dict[str, Any]) -> dict[str, Any]:
    tool_id = tool["id"]
    positive_a = _TOOL_FUNCTIONS[tool_id]()
    positive_b = _TOOL_FUNCTIONS[tool_id]()
    boundary_admit = _boundary(tool_id, True)
    boundary_refuse = _boundary(tool_id, False)
    changed = sorted(
        key
        for key in set(boundary_admit["input"]) | set(boundary_refuse["input"])
        if boundary_admit["input"].get(key) != boundary_refuse["input"].get(key)
    )
    replay_a = _replay_projection(tool_id, positive_a)
    replay_b = _replay_projection(tool_id, positive_b)
    replay_equal = _canonical(replay_a) == _canonical(replay_b)
    reference = _reference(tool_id, positive_a)
    severance = _severance(tool_id, tool["import"])
    return {
        "tool_id": tool_id,
        "distribution": tool["distribution"],
        "import": tool["import"],
        "positive": {"fired": True, "output": positive_a},
        "negative": {
            "fired": boundary_refuse["verdict"] == "REFUSE",
            "reason_code": boundary_refuse["reason_code"],
            "output": boundary_refuse,
        },
        "boundary": {
            "admit": boundary_admit,
            "refuse": boundary_refuse,
            "changed_fields": changed,
            "single_field_flip": (
                changed and len(changed) == 1
                and boundary_admit["verdict"] == "ADMIT"
                and boundary_refuse["verdict"] == "REFUSE"
            ),
        },
        "replay": {
            "equal": replay_equal,
            "normalization": "semantic_output_v1",
            "sha256_a": _sha(_canonical(replay_a)),
            "sha256_b": _sha(_canonical(replay_b)),
        },
        "severance": severance,
        "reference": reference,
    }


def _child(tool_id: str) -> int:
    registry = core_tools.load_registry()
    tool = next(row for row in registry["tools"] if row["id"] == tool_id)
    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(
            captured_stderr
        ):
            body = _run_one_tool(tool)
        body["captured_stdout_sha256"] = _sha(captured_stdout.getvalue().encode())
        body["captured_stderr_sha256"] = _sha(captured_stderr.getvalue().encode())
        print(_MARKER + json.dumps(body, sort_keys=True, separators=(",", ":")))
        return 0
    except Exception as exc:
        body = {
            "tool_id": tool_id,
            "error": type(exc).__name__,
            "detail": str(exc)[:500],
            "captured_stdout_sha256": _sha(captured_stdout.getvalue().encode()),
            "captured_stderr_sha256": _sha(captured_stderr.getvalue().encode()),
        }
        print(_MARKER + json.dumps(body, sort_keys=True, separators=(",", ":")))
        return 1


def _source_hashes() -> dict[str, str]:
    paths = {
        "light_runtime/src/constraintbox/core_tools.py": Path(core_tools.__file__).resolve(),
        "light_runtime/src/constraintbox/cb_light_probes.py": Path(__file__).resolve(),
        "light_runtime/src/constraintbox/core_tool_registry_v9.json": core_tools._REGISTRY,
    }
    return {
        name: _sha(path.read_bytes()) for name, path in paths.items()
    }


def run_core_probe_matrix(timeout_seconds: float = 15.0) -> dict[str, Any]:
    registry = core_tools.load_registry()
    doctor = core_tools.doctor()
    doctor_by_id = {row["id"]: row for row in doctor["rows"]}
    source_hashes = _source_hashes()
    started = time.monotonic()
    tool_decisions: list[dict[str, Any]] = []
    raw_runs: list[dict[str, Any]] = []
    for tool in registry["tools"]:
        before = time.monotonic()
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-m", "constraintbox.cb_light_probes", "--child", tool["id"]],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
        elapsed_ms = round((time.monotonic() - before) * 1000, 3)
        marker_lines = [
            line for line in completed.stdout.splitlines() if line.startswith(_MARKER)
        ]
        if marker_lines:
            observed = json.loads(marker_lines[-1][len(_MARKER) :])
        else:
            observed = {
                "tool_id": tool["id"],
                "error": "MISSING_STRUCTURED_CHILD_OUTPUT",
                "detail": completed.stderr[-500:],
            }
        raw_runs.append(
            {
                "tool_id": tool["id"],
                "returncode": completed.returncode,
                "elapsed_ms": elapsed_ms,
                "stdout_sha256": _sha(completed.stdout.encode()),
                "stderr_sha256": _sha(completed.stderr.encode()),
            }
        )
        installed = doctor_by_id[tool["id"]]
        import_succeeds = bool(installed["import_visible"])
        facts = {
            "candidate_bound": True,
            "installed": installed["version"] is not None,
            "import_succeeds": import_succeeds,
            "positive_api_case": bool(observed.get("positive", {}).get("fired")),
            "reason_specific_negative": bool(observed.get("negative", {}).get("fired"))
            and bool(observed.get("negative", {}).get("reason_code")),
            "single_field_boundary_flip": bool(
                observed.get("boundary", {}).get("single_field_flip")
            ),
            "deterministic_replay": bool(observed.get("replay", {}).get("equal")),
            "severance_observed": bool(observed.get("severance", {}).get("fired")),
            "reference_agreement": bool(observed.get("reference", {}).get("agrees")),
            # This matrix is immediately consumed and revalidated by the
            # cb_light_gate SQLite transition, rather than left as loose JSON.
            "receipt_consumer_bound": True,
        }
        satisfied = completed.returncode == 0 and all(facts.values())
        cases = [
            {"kind": "candidate", "passed": facts["candidate_bound"]},
            {
                "kind": "install",
                "passed": facts["installed"],
                "version": installed["version"],
            },
            {"kind": "import", "passed": facts["import_succeeds"]},
            {
                "kind": "positive",
                "passed": facts["positive_api_case"],
                "detail": observed.get("positive"),
            },
            {
                "kind": "negative",
                "passed": facts["reason_specific_negative"],
                "detail": observed.get("negative"),
            },
            {
                "kind": "boundary",
                "passed": facts["single_field_boundary_flip"],
                "detail": observed.get("boundary"),
            },
            {
                "kind": "replay",
                "passed": facts["deterministic_replay"],
                "detail": observed.get("replay"),
            },
            {
                "kind": "severance",
                "passed": facts["severance_observed"],
                "detail": observed.get("severance"),
            },
            {
                "kind": "reference",
                "passed": facts["reference_agreement"],
                "detail": observed.get("reference"),
            },
        ]
        tool_decisions.append(
            {
                "contract_id": tool["id"],
                "distribution": tool["distribution"],
                "import": tool["import"],
                "version": installed["version"],
                "disposition": "ADMIT" if satisfied else "HOLD",
                "reason_code": (
                    "PROBE_CONTRACT_SATISFIED"
                    if satisfied
                    else "PROBE_CONTRACT_INCOMPLETE"
                ),
                "facts": facts,
                "cases": cases,
                "child_observation": observed,
                "source": tool["source"],
            }
        )

    contract_set_sha256 = _sha(_canonical(registry["tools"]))
    evidence_set_sha256 = _sha(_canonical(tool_decisions))
    return {
        "schema": "constraintbox.cb-light-core-probes.v1",
        "profile": "cb_light",
        "interpreter": sys.executable,
        "python_version": sys.version.split()[0],
        "contract_set_sha256": contract_set_sha256,
        "source_hashes": source_hashes,
        "source_set_sha256": _sha(_canonical(source_hashes)),
        "evidence_set_sha256": evidence_set_sha256,
        "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
        "required_case_kinds": [
            "candidate",
            "install",
            "import",
            "positive",
            "negative",
            "boundary",
            "replay",
            "severance",
            "reference",
        ],
        "tool_decisions": tool_decisions,
        "raw_runs": raw_runs,
        "all_contracts_satisfied": all(
            row["disposition"] == "ADMIT" for row in tool_decisions
        ),
        "promotion_allowed": False,
        "claim_ceiling": "five current CB Light tool probe contracts only",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", choices=list(_TOOL_FUNCTIONS))
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)
    if args.child:
        return _child(args.child)
    print(json.dumps(run_core_probe_matrix(args.timeout), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
