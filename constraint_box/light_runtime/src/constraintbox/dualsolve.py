"""Independent finite-domain differential solving with cvc5, z3, and enumeration."""

from __future__ import annotations

import copy
import json
import random
import threading
from typing import Any, Callable

from constraintbox.constraints import (
    ConstraintSpecError,
    FiniteConstraintProblem,
    SolverResult,
    SolverStatus,
    evaluate_constraint,
)

DEFAULT_Z3_TIMEOUT_MS = 5_000
DEFAULT_CVC5_TIMEOUT_MS = 5_000
_MANDATORY_DECIDERS = ("z3", "cvc5", "enumeration")
_Z3_CONFIGURATION_LOCK = threading.Lock()


def _or(solver: Any, kind: Any, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(False)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(kind.OR, *terms)


def _and(solver: Any, kind: Any, terms: list[Any]) -> Any:
    if not terms:
        return solver.mkBoolean(True)
    if len(terms) == 1:
        return terms[0]
    return solver.mkTerm(kind.AND, *terms)


def _cvc5_operand_cases(
    solver: Any,
    selectors: dict[str, list[Any]],
    domains: dict[str, tuple[Any, ...]],
    operand: Any,
) -> list[tuple[Any, Any]]:
    """Translate one finite operand without retaining a solver closure.

    Keeping the cvc5 compiler helpers at module scope is intentional.  The
    Python cvc5 binding can segfault during cyclic garbage collection when
    nested recursive helper closures retain solver-owned terms.  These helpers
    carry the same explicit compiler inputs without a closure cycle.
    """

    if not isinstance(operand, dict):
        raise ConstraintSpecError("bad cvc5 operand")
    if set(operand) == {"const"}:
        return [(solver.mkBoolean(True), operand["const"])]
    if set(operand) == {"var"}:
        name = operand["var"]
        return list(zip(selectors[name], domains[name], strict=True))
    raise ConstraintSpecError("bad cvc5 operand")


def _cvc5_compile_relation(
    solver: Any,
    kind: Any,
    selectors: dict[str, list[Any]],
    domains: dict[str, tuple[Any, ...]],
    left: Any,
    right: Any,
    predicate: Callable[[Any, Any], bool],
) -> Any:
    satisfying: list[Any] = []
    for left_selector, left_value in _cvc5_operand_cases(
        solver, selectors, domains, left
    ):
        for right_selector, right_value in _cvc5_operand_cases(
            solver, selectors, domains, right
        ):
            if predicate(left_value, right_value):
                satisfying.append(
                    _and(solver, kind, [left_selector, right_selector])
                )
    return _or(solver, kind, satisfying)


def _cvc5_compile_constraint(
    solver: Any,
    kind: Any,
    selectors: dict[str, list[Any]],
    domains: dict[str, tuple[Any, ...]],
    constraint: dict[str, Any],
) -> Any:
    """Compile the supported finite relation language without solver cycles."""

    op = constraint["op"]
    if op == "eq":
        return _cvc5_compile_relation(
            solver,
            kind,
            selectors,
            domains,
            constraint.get("left"),
            constraint.get("right"),
            lambda left, right: left == right,
        )
    if op == "neq":
        equality = _cvc5_compile_relation(
            solver,
            kind,
            selectors,
            domains,
            constraint.get("left"),
            constraint.get("right"),
            lambda left, right: left == right,
        )
        return solver.mkTerm(kind.NOT, equality)
    if op == "lt":
        return _cvc5_compile_relation(
            solver,
            kind,
            selectors,
            domains,
            constraint.get("left"),
            constraint.get("right"),
            lambda left, right: left < right,
        )
    if op == "le":
        return _cvc5_compile_relation(
            solver,
            kind,
            selectors,
            domains,
            constraint.get("left"),
            constraint.get("right"),
            lambda left, right: left <= right,
        )
    if op == "gt":
        return _cvc5_compile_relation(
            solver,
            kind,
            selectors,
            domains,
            constraint.get("left"),
            constraint.get("right"),
            lambda left, right: left > right,
        )
    if op == "ge":
        return _cvc5_compile_relation(
            solver,
            kind,
            selectors,
            domains,
            constraint.get("left"),
            constraint.get("right"),
            lambda left, right: left >= right,
        )
    if op == "all_different":
        names = constraint.get("vars")
        if not isinstance(names, list) or not names:
            raise ConstraintSpecError("all_different requires nonempty vars")
        pairwise_different: list[Any] = []
        for left in range(len(names)):
            for right in range(left + 1, len(names)):
                equality = _cvc5_compile_relation(
                    solver,
                    kind,
                    selectors,
                    domains,
                    {"var": names[left]},
                    {"var": names[right]},
                    lambda left_value, right_value: left_value == right_value,
                )
                pairwise_different.append(solver.mkTerm(kind.NOT, equality))
        return _and(solver, kind, pairwise_different)
    if op in {"and", "or"}:
        children = constraint.get("constraints")
        if not isinstance(children, list) or not children:
            raise ConstraintSpecError(f"{op} requires nonempty constraints")
        compiled = [
            _cvc5_compile_constraint(
                solver, kind, selectors, domains, child
            )
            for child in children
        ]
        return (
            _and(solver, kind, compiled)
            if op == "and"
            else _or(solver, kind, compiled)
        )
    if op == "not":
        child = constraint.get("constraint")
        if not isinstance(child, dict):
            raise ConstraintSpecError("not requires one constraint")
        return solver.mkTerm(
            kind.NOT,
            _cvc5_compile_constraint(
                solver, kind, selectors, domains, child
            ),
        )
    raise ConstraintSpecError(f"cvc5 profile does not support {op}")


def _solve_cvc5(
    problem: FiniteConstraintProblem,
    *,
    timeout_ms: int | None = DEFAULT_CVC5_TIMEOUT_MS,
) -> SolverResult:
    """Compile the finite problem into independent one-hot cvc5 Booleans."""
    try:
        import cvc5  # type: ignore
    except ModuleNotFoundError as exc:
        if exc.name == "cvc5":
            return SolverResult(
                SolverStatus.UNKNOWN,
                None,
                0,
                "cvc5_unavailable",
                "cvc5",
            )
        raise

    kind = cvc5.Kind
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    solver.setOption("produce-models", "true")
    if timeout_ms is not None:
        solver.setOption("tlimit-per", str(timeout_ms))

    domains = {name: domain for name, domain in problem.variables}
    selectors: dict[str, list[Any]] = {}
    for variable_index, (variable, domain) in enumerate(problem.variables):
        choices = [
            solver.mkConst(
                solver.getBooleanSort(),
                f"dual_sel_{variable_index}_{value_index}",
            )
            for value_index in range(len(domain))
        ]
        selectors[variable] = choices
        solver.assertFormula(_or(solver, kind, choices))
        for left in range(len(choices)):
            for right in range(left + 1, len(choices)):
                solver.assertFormula(
                    solver.mkTerm(
                        kind.NOT,
                        solver.mkTerm(
                            kind.AND, choices[left], choices[right]
                        ),
                    )
                )

    try:
        for constraint in problem.constraints:
            solver.assertFormula(
                _cvc5_compile_constraint(
                    solver,
                    kind,
                    selectors,
                    domains,
                    constraint,
                )
            )
    except (ConstraintSpecError, KeyError, TypeError, ValueError):
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "constraint_not_supported_by_cvc5_profile",
            "cvc5",
        )

    result = solver.checkSat()
    if result.isUnsat():
        return SolverResult(
            SolverStatus.BOUNDED_UNSAT,
            None,
            problem.state_count,
            "bounded_one_hot_encoding_unsat",
            "cvc5",
        )
    if not result.isSat():
        return SolverResult(
            SolverStatus.UNKNOWN, None, 0, "cvc5_unknown", "cvc5"
        )
    witness: dict[str, Any] = {}
    for name, domain in problem.variables:
        selected = [
            index
            for index, selector in enumerate(selectors[name])
            if solver.getValue(selector).getBooleanValue()
        ]
        if len(selected) != 1:
            return SolverResult(
                SolverStatus.UNKNOWN,
                None,
                0,
                "cvc5_model_not_exactly_one",
                "cvc5",
            )
        witness[name] = domain[selected[0]]
    return SolverResult(
        SolverStatus.BOUNDED_SAT,
        witness,
        0,
        "bounded_one_hot_model_found",
        "cvc5",
    )


def _solve_z3(
    problem: FiniteConstraintProblem,
    *,
    timeout_ms: int | None,
) -> SolverResult:
    """Run the existing Z3 compiler with a scoped native timeout default."""
    if timeout_ms is None:
        return problem.solve_z3(max_states=problem.state_count)

    try:
        import z3  # type: ignore
    except ModuleNotFoundError as exc:
        if exc.name == "z3":
            return SolverResult(
                SolverStatus.UNKNOWN, None, 0, "z3_unavailable", "z3"
            )
        raise

    # FiniteConstraintProblem.solve_z3 does not expose Solver.set(timeout=...).
    # Z3's process-global default applies to Solver instances constructed while
    # it is set. Serialize the narrow mutation and restore the prior value so a
    # dual solve cannot silently alter another caller's solver configuration.
    with _Z3_CONFIGURATION_LOCK:
        previous_timeout = z3.get_param("timeout")
        z3.set_param("timeout", timeout_ms)
        try:
            return problem.solve_z3(max_states=problem.state_count)
        finally:
            z3.set_param("timeout", previous_timeout)


def _validated_timeout(name: str, timeout_ms: int | None) -> int | None:
    if timeout_ms is None:
        return None
    if isinstance(timeout_ms, bool) or not isinstance(timeout_ms, int):
        raise TypeError(f"{name} must be a positive integer or None")
    if timeout_ms <= 0:
        raise ValueError(f"{name} must be a positive integer or None")
    return timeout_ms


def _run_backend(
    name: str,
    operation: Callable[[], SolverResult],
) -> SolverResult:
    """Normalize backend returns without treating execution faults as abstention.

    The legacy status key remains ``UNKNOWN`` for schema compatibility.  The
    caller must also inspect the execution-integrity metadata emitted by
    :func:`dual_solve`: a genuine bounded abstention or unavailable dependency
    is not the same state as an invoked backend that raised or broke contract.
    """
    try:
        result = operation()
    except Exception as error:
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            f"backend_exception:{type(error).__name__}",
            name,
        )
    if not isinstance(result, SolverResult):
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            f"backend_contract_error:{type(result).__name__}",
            name,
        )
    if result.backend != name:
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            f"backend_identity_mismatch:{result.backend}",
            name,
        )
    if not isinstance(result.status, SolverStatus):
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            f"backend_status_invalid:{type(result.status).__name__}",
            name,
        )
    if (
        isinstance(result.explored, bool)
        or not isinstance(result.explored, int)
        or result.explored < 0
    ):
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "backend_contract_error:invalid_explored",
            name,
        )
    if not isinstance(result.reason, str) or not result.reason:
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "backend_contract_error:invalid_reason",
            name,
        )
    if (
        result.status is SolverStatus.BOUNDED_SAT
        and not isinstance(result.witness, dict)
    ):
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "backend_contract_error:invalid_sat_witness",
            name,
        )
    if (
        result.status is not SolverStatus.BOUNDED_SAT
        and result.witness is not None
    ):
        return SolverResult(
            SolverStatus.UNKNOWN,
            None,
            0,
            "backend_contract_error:unexpected_witness",
            name,
        )
    return result


def _backend_execution_state(result: SolverResult) -> str:
    """Classify an UNKNOWN without collapsing failure into unavailability."""

    if result.reason.startswith("backend_unavailable:") or result.reason in {
        "z3_unavailable",
        "cvc5_unavailable",
    }:
        return "UNAVAILABLE"
    if result.reason.startswith(
        (
            "backend_exception:",
            "backend_contract_error:",
            "backend_identity_mismatch:",
            "backend_status_invalid:",
        )
    ):
        return "EXECUTION_ERROR"
    if result.status is SolverStatus.UNKNOWN:
        return "ABSTAINED"
    return "EXECUTED_DEFINITE"


def _validate_witness(
    problem: FiniteConstraintProblem, result: SolverResult
) -> str | None:
    if result.status is not SolverStatus.BOUNDED_SAT:
        return None
    if result.witness is None:
        return "missing_sat_witness"
    try:
        expected_variables = {name for name, _domain in problem.variables}
        if set(result.witness) != expected_variables:
            return "witness_variable_keys_mismatch"
        for name, domain in problem.variables:
            matches = sum(
                1
                for candidate in domain
                if result.witness[name] == candidate
            )
            if matches != 1:
                return f"witness_value_outside_domain:{name}"
        for index, constraint in enumerate(problem.constraints):
            if not evaluate_constraint(constraint, result.witness):
                return f"constraint_{index}_failed"
    except (ConstraintSpecError, KeyError, TypeError, ValueError) as error:
        return f"witness_evaluation_error:{type(error).__name__}"
    return None


def dual_solve(
    spec: dict[str, Any],
    max_states: int = 100_000,
    *,
    z3_timeout_ms: int | None = DEFAULT_Z3_TIMEOUT_MS,
    cvc5_timeout_ms: int | None = DEFAULT_CVC5_TIMEOUT_MS,
) -> dict[str, Any]:
    """Run two symbolic deciders plus one internal bounded reference checker.

    The existing ``enumeration`` result key is retained for receipt
    compatibility. ``backend_roles`` states explicitly that enumeration is an
    internal reference method, not an external tool or installed instrument.
    Agreement still requires three definite, execution-valid votes.
    """
    z3_timeout_ms = _validated_timeout("z3_timeout_ms", z3_timeout_ms)
    cvc5_timeout_ms = _validated_timeout(
        "cvc5_timeout_ms", cvc5_timeout_ms
    )
    problem = FiniteConstraintProblem.from_spec(spec)
    results = {
        # The caller's bound governs exhaustive enumeration. The two symbolic
        # deciders still decide when enumeration abstains.
        "z3": _run_backend(
            "z3",
            lambda: _solve_z3(problem, timeout_ms=z3_timeout_ms),
        ),
        "cvc5": _run_backend(
            "cvc5",
            lambda: _solve_cvc5(problem, timeout_ms=cvc5_timeout_ms),
        ),
        "enumeration": _run_backend(
            "enumeration",
            lambda: problem.solve_enumerated(max_states=max_states),
        ),
    }
    output: dict[str, Any] = {
        name: result.status.value for name, result in results.items()
    }
    output["backend_results"] = {
        name: {
            "status": result.status.value,
            "reason": result.reason,
            "explored": result.explored,
        }
        for name, result in results.items()
    }
    output["backend_roles"] = {
        "z3": "external_symbolic_decider",
        "cvc5": "external_symbolic_decider",
        "enumeration": "internal_bounded_reference_checker",
    }
    backend_execution = {
        name: {
            "state": _backend_execution_state(result),
            "reason": result.reason,
        }
        for name, result in results.items()
    }
    output["backend_settings"] = {
        "z3": {
            "timeout_ms": z3_timeout_ms,
            "max_states": problem.state_count,
        },
        "cvc5": {
            "timeout_ms": cvc5_timeout_ms,
            "state_count": problem.state_count,
        },
        "enumeration": {
            "timeout_ms": None,
            "max_states": max_states,
        },
    }
    definite = {
        name: result.status.value
        for name, result in results.items()
        if result.status
        in (SolverStatus.BOUNDED_SAT, SolverStatus.BOUNDED_UNSAT)
    }
    invalid_witnesses = {
        name: reason
        for name, result in results.items()
        if (reason := _validate_witness(problem, result)) is not None
    }
    for name, reason in invalid_witnesses.items():
        backend_execution[name] = {
            "state": "EXECUTION_ERROR",
            "reason": f"invalid_sat_witness:{reason}",
        }
    execution_errors = {
        name: metadata["reason"]
        for name, metadata in backend_execution.items()
        if metadata["state"] == "EXECUTION_ERROR"
    }
    output["backend_execution"] = backend_execution
    output["execution_errors"] = execution_errors
    output["has_execution_error"] = bool(execution_errors)
    nondefinite = [
        name for name in _MANDATORY_DECIDERS if name not in definite
    ]
    definite_status_conflict = len(set(definite.values())) > 1
    output["all_definite"] = not nondefinite
    output["definite_status_conflict"] = definite_status_conflict
    output["agree"] = (
        output["all_definite"]
        and not definite_status_conflict
        and not invalid_witnesses
        and not execution_errors
    )

    witnesses = {
        name: result.witness
        for name, result in results.items()
        if result.status is SolverStatus.BOUNDED_SAT
    }
    if witnesses:
        output["witnesses"] = witnesses
    abstentions = {
        name: result.reason
        for name, result in results.items()
        if result.status is SolverStatus.UNKNOWN
    }
    if abstentions:
        output["abstentions"] = abstentions
    if not output["agree"]:
        if definite_status_conflict:
            reason = "definite_status_disagreement"
        elif execution_errors:
            reason = "backend_execution_error"
        elif nondefinite:
            reason = "mandatory_decider_not_definite"
        elif invalid_witnesses:
            reason = "invalid_sat_witness"
        else:
            reason = "definite_status_disagreement"
        output["disagreement"] = {
            "reason": reason,
            "definite_status_conflict": definite_status_conflict,
            "mandatory_deciders": list(_MANDATORY_DECIDERS),
            "nondefinite_deciders": nondefinite,
            "definite_statuses": definite,
            "invalid_witnesses": invalid_witnesses,
        }
    return output


_DIFFERENTIAL_POOL = [
    True,
    False,
    1,
    0,
    1.0,
    0.0,
    2,
    2.0,
    3,
    4,
    "plain",
    "other",
    [1],
    [1, 2],
]
_COLLISION_PAIRS = [
    (True, 1),
    (False, 0),
    (1, 1.0),
    (0, 0.0),
    (2, 2.0),
]


def _domain_with_required(
    rng: random.Random, required: list[Any], size: int
) -> list[Any]:
    domain = [copy.deepcopy(value) for value in required]
    candidates = [copy.deepcopy(value) for value in _DIFFERENTIAL_POOL]
    rng.shuffle(candidates)
    for candidate in candidates:
        if len(domain) >= size:
            break
        if all(candidate != existing for existing in domain):
            domain.append(candidate)
    if len(domain) != size:
        raise RuntimeError("could not construct an equality-distinct domain")
    return domain


def _random_spec(rng: random.Random, case_index: int) -> dict[str, Any]:
    names = ["p", "q", "r"][: rng.randint(2, 3)]
    required = {name: [] for name in names}
    if case_index % 3 == 0:
        left, right = _COLLISION_PAIRS[
            (case_index // 3) % len(_COLLISION_PAIRS)
        ]
        required["p"].append(left)
        required["q"].append(right)
    if case_index % 5 == 0:
        required["p"].append([1])
        required["q"].append([1, 2])
    variables = {
        name: _domain_with_required(
            rng,
            required[name],
            max(len(required[name]), rng.randint(2, 3)),
        )
        for name in names
    }

    def leaf() -> dict[str, Any]:
        if rng.random() < 0.18:
            selected = rng.sample(names, rng.randint(2, len(names)))
            return {"op": "all_different", "vars": selected}
        op = rng.choice(("eq", "neq"))
        left = {"var": rng.choice(names)}
        if rng.random() < 0.58:
            right: dict[str, Any] = {"var": rng.choice(names)}
        else:
            right = {"const": copy.deepcopy(rng.choice(_DIFFERENTIAL_POOL))}
        return {"op": op, "left": left, "right": right}

    def node(depth: int) -> dict[str, Any]:
        if depth == 0 or rng.random() < 0.48:
            return leaf()
        op = rng.choice(("and", "or", "not"))
        if op == "not":
            return {"op": "not", "constraint": node(depth - 1)}
        return {
            "op": op,
            "constraints": [
                node(depth - 1) for _ in range(rng.randint(2, 3))
            ],
        }

    return {
        "variables": variables,
        "constraints": [node(2) for _ in range(rng.randint(1, 3))],
    }


def _collision_families(spec: dict[str, Any]) -> set[str]:
    domains = list(spec["variables"].values())
    found: set[str] = set()
    for left_index, left_domain in enumerate(domains):
        for right_domain in domains[left_index + 1 :]:
            for left in left_domain:
                for right in right_domain:
                    if left is right or left != right:
                        continue
                    pair = (left, right)
                    reverse = (right, left)
                    typed_pairs = [
                        ("true_vs_1", True, bool, 1, int),
                        ("false_vs_0", False, bool, 0, int),
                        ("1_vs_1.0", 1, int, 1.0, float),
                        ("0_vs_0.0", 0, int, 0.0, float),
                        ("2_vs_2.0", 2, int, 2.0, float),
                    ]
                    for label, first, first_type, second, second_type in typed_pairs:
                        direct = (
                            type(pair[0]) is first_type
                            and pair[0] == first
                            and type(pair[1]) is second_type
                            and pair[1] == second
                        )
                        backward = (
                            type(reverse[0]) is first_type
                            and reverse[0] == first
                            and type(reverse[1]) is second_type
                            and reverse[1] == second
                        )
                        if direct or backward:
                            found.add(label)
    return found


def run_differential(
    cases: int = 600, seed: int = 20260727
) -> dict[str, Any]:
    """Run a seeded differential and retain every disagreement spec in full."""
    rng = random.Random(seed)
    disagreements: list[dict[str, Any]] = []
    collision_specs = 0
    collision_sample: dict[str, Any] | None = None
    family_counts = {label: 0 for label, *_ in [
        ("true_vs_1",),
        ("false_vs_0",),
        ("1_vs_1.0",),
        ("0_vs_0.0",),
        ("2_vs_2.0",),
    ]}
    unhashable_specs = 0
    for case_index in range(cases):
        spec = _random_spec(rng, case_index)
        families = _collision_families(spec)
        if families:
            collision_specs += 1
            collision_sample = collision_sample or copy.deepcopy(spec)
            for family in families:
                family_counts[family] += 1
        if any(
            isinstance(value, list)
            for domain in spec["variables"].values()
            for value in domain
        ):
            unhashable_specs += 1
        result = dual_solve(spec)
        if not result["agree"]:
            disagreements.append({"spec": spec, "result": result})
    return {
        "seed": seed,
        "specs_run": cases,
        "disagreements": disagreements,
        "cross_variable_collision_specs": collision_specs,
        "collision_family_counts": family_counts,
        "collision_sample": collision_sample,
        "unhashable_value_specs": unhashable_specs,
    }


def _print_differential(report: dict[str, Any]) -> None:
    print(f"DIFFERENTIAL_SEED={report['seed']}")
    print(f"DIFFERENTIAL_SPECS_RUN={report['specs_run']}")
    print(f"DIFFERENTIAL_DISAGREEMENTS={len(report['disagreements'])}")
    for index, disagreement in enumerate(report["disagreements"], start=1):
        print(
            f"DISAGREEMENT_{index}_SPEC="
            + json.dumps(disagreement["spec"], sort_keys=True)
        )
        print(
            f"DISAGREEMENT_{index}_DETAIL="
            + json.dumps(disagreement["result"], sort_keys=True)
        )
    print(
        "CROSS_VARIABLE_EQ_COLLISION_SPECS="
        f"{report['cross_variable_collision_specs']}"
    )
    print(
        "CROSS_VARIABLE_EQ_COLLISION_FAMILIES="
        + json.dumps(report["collision_family_counts"], sort_keys=True)
    )
    print(
        "CROSS_VARIABLE_EQ_COLLISION_SAMPLE="
        + json.dumps(report["collision_sample"], sort_keys=True)
    )
    print(f"UNHASHABLE_VALUE_SPECS={report['unhashable_value_specs']}")


if __name__ == "__main__":
    _print_differential(run_differential())
