#!/usr/bin/env python3
"""Bounded Z3/cvc5 crossover for the fixed-X_4 append-chain claims.

The two solver encoders below are deliberately separate.  They share only the
human-readable query plan; neither consumes formulas, models, or generated
manifests from the other.  Every satisfying permutation is enumerated and then
replayed by the plain-Python structure semantics in this file.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

import cvc5
import z3
from cvc5 import Kind


SCHEMA_VERSION = "finite_structure_hypothesis_tournament.smt.v1"
CLASSIFICATION = "scratch_diagnostic"
CANONICAL_PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
EXPECTED_SPEC_SHA256 = "060177cae89e23e19f05c6ed7f10fe729bb636db14e0d1caaab66770872efae3"
CARRIER = tuple(range(4))
UNIVERSAL_RELATION = tuple(tuple(True for _ in CARRIER) for _ in CARRIER)


# These data are used only by the solver-independent replay/oracle.  Each SMT
# backend encodes the structures independently in its own function below.
STRUCTURES: dict[str, dict[str, Any]] = {
    "A0": {"relation": None, "constants": {}},
    "A1": {"relation": UNIVERSAL_RELATION, "constants": {}},
    "A2": {"relation": UNIVERSAL_RELATION, "constants": {"c0": 0}},
    "A3": {
        "relation": UNIVERSAL_RELATION,
        "constants": {"c0": 0, "c1": 1},
    },
    "B2": {"relation": UNIVERSAL_RELATION, "constants": {"c0": 1}},
    # Mutation controls.  Constants remain separately named even when their
    # interpretations coincide.
    "B2_mutated_c0_0": {
        "relation": UNIVERSAL_RELATION,
        "constants": {"c0": 0},
    },
    "A3_mutated_c1_0": {
        "relation": UNIVERSAL_RELATION,
        "constants": {"c0": 0, "c1": 0},
    },
}


# Every query asks whether Aut(left) \ Aut(right) is nonempty.  Thus UNSAT is
# the append-subgroup polarity and SAT supplies a literal counterexample.
QUERY_PLAN: tuple[dict[str, str], ...] = (
    {
        "id": "append_subgroup_A0_A1",
        "category": "required_append_subgroup",
        "left": "A1",
        "right": "A0",
        "expected": "unsat",
    },
    {
        "id": "append_subgroup_A1_A2",
        "category": "required_append_subgroup",
        "left": "A2",
        "right": "A1",
        "expected": "unsat",
    },
    {
        "id": "append_subgroup_A2_A3",
        "category": "required_append_subgroup",
        "left": "A3",
        "right": "A2",
        "expected": "unsat",
    },
    {
        "id": "append_strictness_A0_A1",
        "category": "required_append_strictness",
        "left": "A0",
        "right": "A1",
        "expected": "unsat",
    },
    {
        "id": "append_strictness_A1_A2",
        "category": "required_append_strictness",
        "left": "A1",
        "right": "A2",
        "expected": "sat",
    },
    {
        "id": "append_strictness_A2_A3",
        "category": "required_append_strictness",
        "left": "A2",
        "right": "A3",
        "expected": "sat",
    },
    {
        "id": "replacement_B2_not_subset_A2",
        "category": "required_replacement_nonmonotone",
        "left": "B2",
        "right": "A2",
        "expected": "sat",
    },
    {
        "id": "control_mutated_replacement_c0_to_0",
        "category": "mutated_constant_flip_control",
        "left": "B2_mutated_c0_0",
        "right": "A2",
        "expected": "unsat",
        "flips": "replacement_B2_not_subset_A2",
    },
    {
        "id": "control_mutated_A3_c1_to_0",
        "category": "mutated_constant_flip_control",
        "left": "A2",
        "right": "A3_mutated_c1_0",
        "expected": "unsat",
        "flips": "append_strictness_A2_A3",
    },
)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def is_permutation(permutation: tuple[int, ...] | list[int]) -> bool:
    return len(permutation) == len(CARRIER) and sorted(permutation) == list(CARRIER)


def is_automorphism(structure_id: str, permutation: tuple[int, ...] | list[int]) -> bool:
    """Solver-independent fixed-carrier automorphism semantics."""

    if structure_id not in STRUCTURES or not is_permutation(permutation):
        return False
    structure = STRUCTURES[structure_id]
    relation = structure["relation"]
    if relation is not None:
        for source in CARRIER:
            for target in CARRIER:
                if relation[source][target] != relation[permutation[source]][permutation[target]]:
                    return False
    # Each named constant is preserved individually.  Coincident values in a
    # mutation control do not erase either constant symbol.
    for value in structure["constants"].values():
        if permutation[value] != value:
            return False
    return True


def replay_query(query: dict[str, str], permutation: tuple[int, ...] | list[int]) -> dict[str, bool]:
    permutation_ok = is_permutation(permutation)
    left_automorphism = is_automorphism(query["left"], permutation)
    right_automorphism = is_automorphism(query["right"], permutation)
    return {
        "permutation": permutation_ok,
        "left_automorphism": left_automorphism,
        "right_automorphism": right_automorphism,
        "query_satisfied": permutation_ok and left_automorphism and not right_automorphism,
    }


def python_oracle(query: dict[str, str]) -> list[list[int]]:
    return [
        list(permutation)
        for permutation in itertools.permutations(CARRIER)
        if replay_query(query, permutation)["query_satisfied"]
    ]


def z3_encode_automorphism(
    permutation: list[z3.ArithRef], structure_id: str
) -> z3.BoolRef:
    """Z3-native encoding; no cvc5 or generated formula input is used."""

    clauses: list[z3.BoolRef] = []
    has_relation = structure_id != "A0"
    if has_relation:
        relation = [[True for _ in CARRIER] for _ in CARRIER]
        for source in CARRIER:
            for target in CARRIER:
                image_in_relation = z3.Or(
                    *[
                        z3.And(permutation[source] == image_source, permutation[target] == image_target)
                        for image_source in CARRIER
                        for image_target in CARRIER
                        if relation[image_source][image_target]
                    ]
                )
                clauses.append(image_in_relation == z3.BoolVal(relation[source][target]))

    if structure_id in {"A2", "A3", "B2_mutated_c0_0", "A3_mutated_c1_0"}:
        clauses.append(permutation[0] == 0)  # preserve c0=0
    if structure_id == "B2":
        clauses.append(permutation[1] == 1)  # preserve c0=1
    if structure_id == "A3":
        clauses.append(permutation[1] == 1)  # preserve c1=1, separately from c0
    if structure_id == "A3_mutated_c1_0":
        clauses.append(permutation[0] == 0)  # preserve separately named c1=0

    return z3.And(*clauses) if clauses else z3.BoolVal(True)


def solve_z3(query: dict[str, str]) -> dict[str, Any]:
    """Enumerate every Z3 model permutation for one existential query."""

    solver = z3.Solver()
    solver.set(timeout=5_000)
    permutation = [z3.Int(f"z3_{query['id']}_p_{index}") for index in CARRIER]
    solver.add(*(term >= 0 for term in permutation))
    solver.add(*(term < len(CARRIER) for term in permutation))
    solver.add(z3.Distinct(*permutation))
    solver.add(z3_encode_automorphism(permutation, query["left"]))
    solver.add(z3.Not(z3_encode_automorphism(permutation, query["right"])))

    witnesses: list[dict[str, Any]] = []
    terminal_status = "unknown"
    reason_unknown: str | None = None
    while True:
        verdict = solver.check()
        if verdict == z3.sat:
            model = solver.model()
            values = [model.eval(term, model_completion=True).as_long() for term in permutation]
            replay = replay_query(query, values)
            witnesses.append({"permutation": values, "replay": replay})
            solver.add(z3.Or(*[term != value for term, value in zip(permutation, values)]))
            continue
        if verdict == z3.unsat:
            terminal_status = "unsat"
        else:
            terminal_status = "unknown"
            reason_unknown = solver.reason_unknown()
        break

    status = "sat" if witnesses and terminal_status == "unsat" else terminal_status
    return {
        "status": status,
        "enumeration_terminal_status": terminal_status,
        "enumeration_complete": terminal_status == "unsat",
        "reason_unknown": reason_unknown,
        "witness_count": len(witnesses),
        "witnesses": witnesses,
    }


def cvc5_encode_automorphism(
    solver: cvc5.Solver, permutation: list[cvc5.Term], structure_id: str
) -> cvc5.Term:
    """cvc5-native encoding; no Z3 or generated formula input is used."""

    true = solver.mkBoolean(True)
    clauses: list[cvc5.Term] = []
    has_relation = structure_id != "A0"
    if has_relation:
        relation = tuple(tuple(True for _ in CARRIER) for _ in CARRIER)
        for source in CARRIER:
            for target in CARRIER:
                image_cases = [
                    solver.mkTerm(
                        Kind.AND,
                        solver.mkTerm(Kind.EQUAL, permutation[source], solver.mkInteger(image_source)),
                        solver.mkTerm(Kind.EQUAL, permutation[target], solver.mkInteger(image_target)),
                    )
                    for image_source in CARRIER
                    for image_target in CARRIER
                    if relation[image_source][image_target]
                ]
                image_in_relation = (
                    image_cases[0]
                    if len(image_cases) == 1
                    else solver.mkTerm(Kind.OR, *image_cases)
                )
                clauses.append(
                    solver.mkTerm(
                        Kind.EQUAL,
                        image_in_relation,
                        solver.mkBoolean(relation[source][target]),
                    )
                )

    if structure_id in {"A2", "A3", "B2_mutated_c0_0", "A3_mutated_c1_0"}:
        clauses.append(solver.mkTerm(Kind.EQUAL, permutation[0], solver.mkInteger(0)))
    if structure_id == "B2":
        clauses.append(solver.mkTerm(Kind.EQUAL, permutation[1], solver.mkInteger(1)))
    if structure_id == "A3":
        clauses.append(solver.mkTerm(Kind.EQUAL, permutation[1], solver.mkInteger(1)))
    if structure_id == "A3_mutated_c1_0":
        clauses.append(solver.mkTerm(Kind.EQUAL, permutation[0], solver.mkInteger(0)))

    if not clauses:
        return true
    if len(clauses) == 1:
        return clauses[0]
    return solver.mkTerm(Kind.AND, *clauses)


def solve_cvc5(query: dict[str, str]) -> dict[str, Any]:
    """Enumerate every cvc5 model permutation for one existential query."""

    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    solver.setOption("produce-models", "true")
    solver.setOption("incremental", "true")
    solver.setOption("tlimit-per", "5000")
    integer_sort = solver.getIntegerSort()
    permutation = [solver.mkConst(integer_sort, f"cvc5_{query['id']}_p_{index}") for index in CARRIER]
    for term in permutation:
        solver.assertFormula(solver.mkTerm(Kind.GEQ, term, solver.mkInteger(0)))
        solver.assertFormula(solver.mkTerm(Kind.LT, term, solver.mkInteger(len(CARRIER))))
    solver.assertFormula(solver.mkTerm(Kind.DISTINCT, *permutation))
    solver.assertFormula(cvc5_encode_automorphism(solver, permutation, query["left"]))
    solver.assertFormula(
        solver.mkTerm(Kind.NOT, cvc5_encode_automorphism(solver, permutation, query["right"]))
    )

    witnesses: list[dict[str, Any]] = []
    terminal_status = "unknown"
    solver_result = ""
    while True:
        verdict = solver.checkSat()
        solver_result = str(verdict)
        if verdict.isSat():
            values = [int(str(solver.getValue(term))) for term in permutation]
            replay = replay_query(query, values)
            witnesses.append({"permutation": values, "replay": replay})
            blocking_terms = [
                solver.mkTerm(Kind.DISTINCT, term, solver.mkInteger(value))
                for term, value in zip(permutation, values)
            ]
            solver.assertFormula(solver.mkTerm(Kind.OR, *blocking_terms))
            continue
        if verdict.isUnsat():
            terminal_status = "unsat"
        else:
            terminal_status = "unknown"
        break

    status = "sat" if witnesses and terminal_status == "unsat" else terminal_status
    return {
        "status": status,
        "enumeration_terminal_status": terminal_status,
        "enumeration_complete": terminal_status == "unsat",
        "solver_result": solver_result,
        "witness_count": len(witnesses),
        "witnesses": witnesses,
    }


def safe_solve(solver_name: str, query: dict[str, str]) -> dict[str, Any]:
    try:
        return solve_z3(query) if solver_name == "z3" else solve_cvc5(query)
    except Exception as exc:  # pragma: no cover - retained to emit a red receipt
        return {
            "status": "error",
            "enumeration_terminal_status": "error",
            "enumeration_complete": False,
            "error": f"{type(exc).__name__}: {exc}",
            "witness_count": 0,
            "witnesses": [],
        }


def permutation_set(result: dict[str, Any]) -> set[tuple[int, ...]]:
    return {tuple(item["permutation"]) for item in result.get("witnesses", [])}


def evaluate_query(query: dict[str, str]) -> dict[str, Any]:
    oracle_witnesses = python_oracle(query)
    oracle_set = {tuple(witness) for witness in oracle_witnesses}
    oracle_status = "sat" if oracle_witnesses else "unsat"
    z3_result = safe_solve("z3", query)
    cvc5_result = safe_solve("cvc5", query)

    z3_set = permutation_set(z3_result)
    cvc5_set = permutation_set(cvc5_result)
    z3_replay_pass = all(
        item["replay"]["query_satisfied"] for item in z3_result.get("witnesses", [])
    )
    cvc5_replay_pass = all(
        item["replay"]["query_satisfied"] for item in cvc5_result.get("witnesses", [])
    )
    expected = query["expected"]
    checks = {
        "oracle_matches_expected": oracle_status == expected,
        "z3_matches_expected": z3_result["status"] == expected,
        "cvc5_matches_expected": cvc5_result["status"] == expected,
        "z3_enumeration_complete": bool(z3_result.get("enumeration_complete")),
        "cvc5_enumeration_complete": bool(cvc5_result.get("enumeration_complete")),
        "z3_every_witness_replayed": z3_replay_pass,
        "cvc5_every_witness_replayed": cvc5_replay_pass,
        "z3_witness_set_matches_python": z3_set == oracle_set,
        "cvc5_witness_set_matches_python": cvc5_set == oracle_set,
        "z3_cvc5_status_agreement": z3_result["status"] == cvc5_result["status"],
        "z3_cvc5_witness_set_agreement": z3_set == cvc5_set,
    }
    return {
        **query,
        "semantics": f"exists p in Aut({query['left']}) but not Aut({query['right']})",
        "oracle": {
            "status": oracle_status,
            "witness_count": len(oracle_witnesses),
            "witnesses": oracle_witnesses,
        },
        "z3": z3_result,
        "cvc5": cvc5_result,
        "checks": checks,
        "pass": all(checks.values()),
    }


def validate_spec_contract(spec: dict[str, Any], spec_sha256: str) -> dict[str, bool]:
    chain = spec.get("fixed_carrier_internal_append_chain", {})
    steps = chain.get("steps", [])
    return {
        "schema_is_v1": spec.get("schema_version") == "finite_structure_hypothesis_tournament.v1",
        "spec_is_frozen_amendment_1": (
            spec.get("spec_status") == "frozen_before_execution_amendment_1"
        ),
        "spec_hash_matches_frozen_amendment_1": spec_sha256 == EXPECTED_SPEC_SHA256,
        "classification_is_scratch": spec.get("classification") == CLASSIFICATION,
        "carrier_is_fixed_X4": chain.get("carrier_size") == 4,
        "append_steps_match": [step.get("id") for step in steps] == ["A0", "A1", "A2", "A3"],
        "append_orders_match": [step.get("expected_aut_order") for step in steps] == [24, 24, 6, 2],
        "solver_obligations_present": [
            item.get("id") for item in spec.get("solver_obligations", [])
        ]
        == ["append_subgroup", "append_strictness", "replacement_nonmonotone"],
    }


def build_result(source_path: Path, spec_path: Path) -> dict[str, Any]:
    spec = json.loads(spec_path.read_text())
    spec_sha256 = sha256_path(spec_path)
    spec_checks = validate_spec_contract(spec, spec_sha256)
    query_results = [evaluate_query(query) for query in QUERY_PLAN]
    by_id = {row["id"]: row for row in query_results}
    controls = {
        "replacement_constant_mutation_flips": (
            by_id["replacement_B2_not_subset_A2"]["expected"] == "sat"
            and by_id["control_mutated_replacement_c0_to_0"]["expected"] == "unsat"
            and by_id["replacement_B2_not_subset_A2"]["pass"]
            and by_id["control_mutated_replacement_c0_to_0"]["pass"]
        ),
        "A3_distinct_constant_mutation_flips": (
            by_id["append_strictness_A2_A3"]["expected"] == "sat"
            and by_id["control_mutated_A3_c1_to_0"]["expected"] == "unsat"
            and by_id["append_strictness_A2_A3"]["pass"]
            and by_id["control_mutated_A3_c1_to_0"]["pass"]
        ),
        "all_sat_permutations_replayed": all(
            all(
                item["replay"]["query_satisfied"]
                for item in row[solver_name].get("witnesses", [])
            )
            for row in query_results
            for solver_name in ("z3", "cvc5")
        ),
        "unknown_timeout_error_forces_red": all(
            row[solver_name]["status"] in {"sat", "unsat"}
            for row in query_results
            for solver_name in ("z3", "cvc5")
        ),
        "solver_disagreement_forces_red": all(
            row["checks"]["z3_cvc5_status_agreement"]
            and row["checks"]["z3_cvc5_witness_set_agreement"]
            for row in query_results
        ),
    }

    automorphism_orders = {
        structure_id: sum(
            is_automorphism(structure_id, permutation)
            for permutation in itertools.permutations(CARRIER)
        )
        for structure_id in STRUCTURES
    }
    expected_orders = {"A0": 24, "A1": 24, "A2": 6, "A3": 2, "B2": 6}
    order_check = all(automorphism_orders[name] == order for name, order in expected_orders.items())

    all_pass = (
        all(spec_checks.values())
        and all(row["pass"] for row in query_results)
        and all(controls.values())
        and order_check
    )
    errors: list[str] = []
    errors.extend(name for name, passed in spec_checks.items() if not passed)
    errors.extend(row["id"] for row in query_results if not row["pass"])
    errors.extend(name for name, passed in controls.items() if not passed)
    if not order_check:
        errors.append("automorphism_orders")

    z3_witness_total = sum(row["z3"]["witness_count"] for row in query_results)
    cvc5_witness_total = sum(row["cvc5"]["witness_count"] for row in query_results)
    cwd = str(Path.cwd().resolve())
    command = [
        CANONICAL_PYTHON,
        str(source_path.resolve()),
        "--spec",
        str(spec_path.resolve()),
        "--out",
        str((source_path.parent / "results" / "smt_result.json").resolve()),
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "all_pass": all_pass,
        "classification": CLASSIFICATION,
        "claim_ceiling": spec["claim_ceiling"],
        "command": command,
        "cwd": cwd,
        "runner_identity": {
            "executable": str(Path(sys.executable).resolve()),
            "canonical_launcher": CANONICAL_PYTHON,
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
        },
        "runtime": {
            "platform": platform.platform(),
            "packages": {
                "z3": {
                    "version": z3.get_version_string(),
                    "module_path": str(Path(z3.__file__).resolve()),
                },
                "cvc5": {
                    "version": cvc5.__version__,
                    "module_path": str(Path(cvc5.__file__).resolve()),
                },
            },
        },
        "source_path": str(source_path.resolve()),
        "source_sha256": sha256_path(source_path),
        "spec_path": str(spec_path.resolve()),
        "spec_sha256": spec_sha256,
        "expected_spec_sha256": EXPECTED_SPEC_SHA256,
        "query_plan_sha256": canonical_sha256(QUERY_PLAN),
        "structure_replay_sha256": canonical_sha256(STRUCTURES),
        "polarity": {
            "query": "exists p in Aut(left) but not Aut(right)",
            "unsat": "Aut(left) is a subset of Aut(right) on fixed X_4",
            "sat": "the replayed permutation witnesses non-subset",
        },
        "spec_contract_checks": spec_checks,
        "candidate_counts": {
            "carrier_size": len(CARRIER),
            "all_carrier_permutations": 24,
            "core_structures": 5,
            "mutation_control_structures": 2,
            "queries": len(QUERY_PLAN),
            "automorphism_orders": automorphism_orders,
        },
        "solver_independence": {
            "z3_encoder": "z3_encode_automorphism",
            "cvc5_encoder": "cvc5_encode_automorphism",
            "shared_generated_formula_manifest": False,
            "shared_solver_models": False,
            "comparison_oracle": "plain Python enumeration of all 24 permutations",
        },
        "queries": query_results,
        "tool_receipts": {
            "z3": {
                "query_count": len(QUERY_PLAN),
                "all_terminal": all(row["z3"]["enumeration_complete"] for row in query_results),
                "sat_permutations_extracted": z3_witness_total,
            },
            "cvc5": {
                "query_count": len(QUERY_PLAN),
                "all_terminal": all(row["cvc5"]["enumeration_complete"] for row in query_results),
                "sat_permutations_extracted": cvc5_witness_total,
            },
            "python_replay": {
                "oracle_permutations_per_query": 24,
                "z3_witnesses_replayed": z3_witness_total,
                "cvc5_witnesses_replayed": cvc5_witness_total,
                "all_replays_pass": controls["all_sat_permutations_replayed"],
            },
        },
        "controls": controls,
        "errors": errors,
        "blocked_consumers": spec["blocked_consumers"],
    }


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=root / "spec.json")
    parser.add_argument("--out", type=Path, default=root / "results" / "smt_result.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = Path(__file__).resolve()
    spec_path = args.spec.resolve()
    output_path = args.out.resolve()
    result = build_result(source_path, spec_path)
    # Bind the receipt to the actual requested output path even if a caller
    # uses a nondefault location for a red diagnostic run.
    result["command"][-1] = str(output_path)
    result["result_core_sha256"] = canonical_sha256(result)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "errors": result["errors"],
                "output": str(output_path),
                "query_count": len(result["queries"]),
                "z3_witnesses": result["tool_receipts"]["z3"]["sat_permutations_extracted"],
                "cvc5_witnesses": result["tool_receipts"]["cvc5"]["sat_permutations_extracted"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
