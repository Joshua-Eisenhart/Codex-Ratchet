"""Solver-backed can-fail classification for z3-expressible checks.

This module complements :mod:`claimgate_plugin.canfail_probe`.  The mutation
probe remains the empirical decider for runnable simulations.  This decider is
only for checks already represented as z3 constraints over an explicit set of
declared variables.

Three conclusive verdicts require two logical polarities:

* ``check`` is unsatisfiable: ``CONTRADICTION`` (the check can never pass).
* ``check`` is satisfiable and ``Not(check)`` is satisfiable: ``CAN_FAIL``.
* ``check`` is satisfiable and ``Not(check)`` is unsatisfiable: ``TAUTOLOGY``.

If z3 returns ``unknown`` for either required polarity, the result is
``UNKNOWN``.  Timing is reported as observation data and never affects the
verdict.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Sequence

import z3


CAN_FAIL = "CAN_FAIL"
TAUTOLOGY = "TAUTOLOGY"
CONTRADICTION = "CONTRADICTION"
UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CanFailResult:
    """Result of classifying one z3-expressible check."""

    verdict: str
    model: z3.ModelRef | None
    witness: dict[str, str] | None
    elapsed_seconds: float
    unknown_reason: str | None = None


def _same_expr(left: z3.ExprRef, right: z3.ExprRef) -> bool:
    return left.ctx == right.ctx and left.eq(right)


def _free_constants(check: z3.BoolRef) -> tuple[z3.ExprRef, ...]:
    """Collect distinct uninterpreted constants without name-based collapse."""

    constants: list[z3.ExprRef] = []
    pending = [check]
    while pending:
        expression = pending.pop()
        if (
            z3.is_const(expression)
            and expression.decl().kind() == z3.Z3_OP_UNINTERPRETED
        ):
            if not any(_same_expr(expression, known) for known in constants):
                constants.append(expression)
            continue
        pending.extend(expression.children())
    return tuple(constants)


def _validate_inputs(
    check: z3.BoolRef,
    declared_variables: Sequence[z3.ExprRef],
) -> tuple[z3.ExprRef, ...]:
    if not isinstance(check, z3.BoolRef):
        raise TypeError("check must be a z3 Boolean constraint")

    variables = tuple(declared_variables)
    for variable in variables:
        if not isinstance(variable, z3.ExprRef):
            raise TypeError("every declared variable must be a z3 expression")
        if variable.ctx != check.ctx:
            raise ValueError("declared variables must share the check's z3 context")
        if (
            not z3.is_const(variable)
            or variable.decl().kind() != z3.Z3_OP_UNINTERPRETED
        ):
            raise ValueError(
                "declared variables must be symbolic z3 constants, not values "
                "or compound expressions"
            )

    for index, variable in enumerate(variables):
        if any(_same_expr(variable, earlier) for earlier in variables[:index]):
            raise ValueError(f"declared variable appears more than once: {variable}")

    rendered_names = [str(variable) for variable in variables]
    if len(set(rendered_names)) != len(rendered_names):
        raise ValueError(
            "declared variables must have distinct rendered names for an "
            "unambiguous witness"
        )

    missing = [
        variable
        for variable in _free_constants(check)
        if not any(_same_expr(variable, declared) for declared in variables)
    ]
    if missing:
        rendered = ", ".join(str(variable) for variable in missing)
        raise ValueError(f"check contains undeclared variables: {rendered}")

    return variables


def _solve(
    constraint: z3.BoolRef,
) -> tuple[z3.CheckSatResult, z3.ModelRef | None, str | None]:
    solver = z3.Solver(ctx=constraint.ctx)
    solver.add(constraint)
    status = solver.check()
    if status == z3.sat:
        return status, solver.model(), None
    if status == z3.unknown:
        return status, None, solver.reason_unknown()
    return status, None, None


def _witness(
    model: z3.ModelRef,
    declared_variables: Sequence[z3.ExprRef],
) -> dict[str, str]:
    return {
        str(variable): str(model.eval(variable, model_completion=True))
        for variable in declared_variables
    }


def analyze_canfail(
    check: z3.BoolRef,
    declared_variables: Sequence[z3.ExprRef],
) -> CanFailResult:
    """Classify whether ``check`` can fail over ``declared_variables``.

    Declared variables may be unused by the constraint; that makes the check
    vacuous with respect to those variables, not invalid.  Every free symbolic
    constant that *does* occur in the check must be declared.

    The elapsed time covers every solver query required for the returned
    verdict.  It is never consulted when choosing that verdict.
    """

    variables = _validate_inputs(check, declared_variables)
    started = perf_counter()

    check_status, _, check_unknown = _solve(check)
    if check_status == z3.unknown:
        return CanFailResult(
            verdict=UNKNOWN,
            model=None,
            witness=None,
            elapsed_seconds=perf_counter() - started,
            unknown_reason=f"check: {check_unknown or 'unknown'}",
        )
    if check_status == z3.unsat:
        return CanFailResult(
            verdict=CONTRADICTION,
            model=None,
            witness=None,
            elapsed_seconds=perf_counter() - started,
        )

    negated_status, negated_model, negated_unknown = _solve(z3.Not(check))
    if negated_status == z3.unknown:
        return CanFailResult(
            verdict=UNKNOWN,
            model=None,
            witness=None,
            elapsed_seconds=perf_counter() - started,
            unknown_reason=f"negated check: {negated_unknown or 'unknown'}",
        )
    if negated_status == z3.unsat:
        return CanFailResult(
            verdict=TAUTOLOGY,
            model=None,
            witness=None,
            elapsed_seconds=perf_counter() - started,
        )

    assert negated_model is not None
    return CanFailResult(
        verdict=CAN_FAIL,
        model=negated_model,
        witness=_witness(negated_model, variables),
        elapsed_seconds=perf_counter() - started,
    )
