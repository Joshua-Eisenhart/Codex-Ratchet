"""Fail-closed evaluation of a gate policy over observed variables.

The rule is transcribed from LevOS ``core/eval/src/discharge.ts``: when a
required variable is MISSING or STALE the evaluation returns
``EVALUATION_ERROR`` with ``blocking`` set.  It never returns a pass and it
never returns a fail.

This closes the hole a bare threshold comparison over absent data leaves
open.  ``if value > threshold`` on a missing value silently becomes a pass or
a fail depending on how the absence coerces, and either way a verdict was
issued about evidence nobody had.  The same hole is open for evidence that is
present but unusable, so this module also blocks on three Python-specific
coercions that a naive comparison would swallow:

* ``True > 0.5`` is ``True`` -- a bool is not a number here.
* ``float("nan") > 0.5`` is ``False`` -- a silent fail on a non-value.
* an undated or future-dated observation, whose freshness cannot be decided.

``blocking`` means "no verdict was reached, go run the evaluator".  It is not
the admission decision: a ``FAIL`` is a real verdict and is not blocking.
"""

from __future__ import annotations

import math
import operator
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


PASS = "PASS"
FAIL = "FAIL"
EVALUATION_ERROR = "EVALUATION_ERROR"

POLICY_SATISFIED = "policy_satisfied"
POLICY_UNSATISFIED = "policy_unsatisfied"
MISSING_REQUIRED_VARIABLE = "missing_required_variable"
STALE_VARIABLE = "stale_variable"
UNDATED_VARIABLE = "undated_variable"
ILL_TYPED_VARIABLE = "ill_typed_variable"
INCOMPLETE_EVALUATION = "incomplete_evaluation"

_COMPARISONS = {
    "lt": operator.lt,
    "lte": operator.le,
    "gt": operator.gt,
    "gte": operator.ge,
    "eq": operator.eq,
    "neq": operator.ne,
    "in": lambda value, threshold: value in threshold,
    "not_in": lambda value, threshold: value not in threshold,
}
COMPARATORS = tuple(_COMPARISONS)

_ORDERING = frozenset({"lt", "lte", "gt", "gte"})
_EQUALITY = frozenset({"eq", "neq"})
_MEMBERSHIP = frozenset({"in", "not_in"})
_COLLECTIONS = (tuple, list, set, frozenset)


def _is_real_number(value: Any) -> bool:
    """True for a finite int or float.  A bool is not a number here."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def _type_class(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    return type(value).__name__


@dataclass(frozen=True)
class Observation:
    """One measured variable and the moment it was measured.

    ``observed_at`` is epoch seconds.  ``None`` means the age is unknown,
    which is not the same as fresh.
    """

    value: Any
    observed_at: float | None = None
    source: str | None = None


@dataclass(frozen=True)
class Requirement:
    """One variable, the comparator applied to it, and its threshold."""

    variable: str
    comparator: str
    threshold: Any
    optional: bool = False

    def __post_init__(self) -> None:
        if not self.variable:
            raise ValueError("requirement needs a variable name")
        if self.comparator not in _COMPARISONS:
            raise ValueError(
                f"unknown comparator {self.comparator!r}; "
                f"declared comparators are {', '.join(COMPARATORS)}"
            )
        if self.comparator in _ORDERING and not _is_real_number(self.threshold):
            raise ValueError(
                f"comparator {self.comparator!r} on {self.variable!r} needs a "
                f"finite numeric threshold, got {_type_class(self.threshold)}"
            )
        if self.comparator in _MEMBERSHIP and not isinstance(
            self.threshold, _COLLECTIONS
        ):
            raise ValueError(
                f"comparator {self.comparator!r} on {self.variable!r} needs a "
                f"collection threshold, got {_type_class(self.threshold)}"
            )


@dataclass(frozen=True)
class Policy:
    """Required variables, their comparators, and one freshness bound."""

    policy_id: str
    requirements: tuple[Requirement, ...]
    max_age_seconds: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirements", tuple(self.requirements))
        if not self.policy_id:
            raise ValueError("policy needs an id")
        if not self.requirements:
            raise ValueError("policy needs at least one requirement")
        names = [requirement.variable for requirement in self.requirements]
        if len(set(names)) != len(names):
            raise ValueError("policy declares the same variable twice")
        if not self.required_variables:
            raise ValueError("policy needs at least one non-optional variable")
        if not _is_real_number(self.max_age_seconds) or self.max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be a finite positive number")

    @property
    def required_variables(self) -> tuple[str, ...]:
        return tuple(
            requirement.variable
            for requirement in self.requirements
            if not requirement.optional
        )

    @property
    def optional_variables(self) -> tuple[str, ...]:
        return tuple(
            requirement.variable
            for requirement in self.requirements
            if requirement.optional
        )


@dataclass(frozen=True)
class Check:
    """One comparison that actually ran, with the evidence it ran on."""

    variable: str
    comparator: str
    threshold: Any
    observed: Any
    age_seconds: float
    outcome: str


@dataclass(frozen=True)
class Discharge:
    """The receipt.  ``status`` is PASS, FAIL, or EVALUATION_ERROR."""

    status: str
    policy_id: str
    reason_code: str
    blocking: bool
    decided_at: float
    checks: tuple[Check, ...] = ()
    missing: tuple[str, ...] = ()
    stale: tuple[str, ...] = ()
    undated: tuple[str, ...] = ()
    ill_typed: tuple[str, ...] = ()
    absent_optional: tuple[str, ...] = ()

    @property
    def is_verdict(self) -> bool:
        return self.status in (PASS, FAIL)

    @property
    def unusable(self) -> tuple[str, ...]:
        """Every variable that stopped the evaluation, in one list."""
        return self.missing + self.stale + self.undated + self.ill_typed


def unevaluated_variables(
    policy: Policy,
    checks: tuple[Check, ...],
    absent_optional: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Declared variables the receipt does not account for.

    Recomputed from the receipt rather than tracked during the loop, so a
    comparison that was skipped cannot be mistaken for one that ran.
    """
    accounted = {check.variable for check in checks} | set(absent_optional)
    return tuple(
        requirement.variable
        for requirement in policy.requirements
        if requirement.variable not in accounted
    )


def _type_complaint(requirement: Requirement, value: Any) -> str | None:
    """Why ``value`` cannot be compared, or None if it can."""
    if requirement.comparator in _ORDERING:
        if not _is_real_number(value):
            return (
                f"{requirement.comparator} needs a finite real number, "
                f"got {_type_class(value)}"
            )
        return None
    if requirement.comparator in _MEMBERSHIP:
        if not (isinstance(value, str) or _is_real_number(value)):
            return (
                f"{requirement.comparator} needs a string or finite number, "
                f"got {_type_class(value)}"
            )
        return None
    observed_class = _type_class(value)
    threshold_class = _type_class(requirement.threshold)
    if observed_class != threshold_class:
        return (
            f"{requirement.comparator} needs a {threshold_class}, "
            f"got {observed_class}"
        )
    return None


def _error(
    policy: Policy,
    reason_code: str,
    now: float,
    *,
    missing: tuple[str, ...] = (),
    stale: tuple[str, ...] = (),
    undated: tuple[str, ...] = (),
    ill_typed: tuple[str, ...] = (),
    absent_optional: tuple[str, ...] = (),
) -> Discharge:
    """A blocking non-verdict.  It carries no comparisons at all."""
    return Discharge(
        status=EVALUATION_ERROR,
        policy_id=policy.policy_id,
        reason_code=reason_code,
        blocking=True,
        decided_at=now,
        checks=(),
        missing=missing,
        stale=stale,
        undated=undated,
        ill_typed=ill_typed,
        absent_optional=absent_optional,
    )


def discharge(
    policy: Policy,
    observations: Mapping[str, Observation],
    *,
    now: float,
) -> Discharge:
    """Evaluate ``policy`` against ``observations`` at clock ``now``.

    Returns a PASS or FAIL verdict only when every declared variable was
    resolved to fresh, well-typed evidence and actually compared.  Otherwise
    returns a blocking EVALUATION_ERROR naming the variables at fault.

    ``now`` is required so the clock is stated by the caller and never
    smuggled in.
    """
    if not _is_real_number(now):
        raise ValueError("now must be a finite number of epoch seconds")

    missing: list[str] = []
    stale: list[str] = []
    undated: list[str] = []
    ill_typed: list[str] = []
    absent_optional: list[str] = []
    checks: list[Check] = []

    for requirement in policy.requirements:
        observation = observations.get(requirement.variable)
        if observation is None:
            target = absent_optional if requirement.optional else missing
            target.append(requirement.variable)
            continue

        # An optional variable may be absent.  Once present it is evidence,
        # and unusable evidence blocks whether or not it was optional.
        if not _is_real_number(observation.observed_at):
            undated.append(requirement.variable)
            continue
        age = now - float(observation.observed_at)
        if age < 0 or age > policy.max_age_seconds:
            stale.append(requirement.variable)
            continue

        if _type_complaint(requirement, observation.value) is not None:
            ill_typed.append(requirement.variable)
            continue

        comparison = _COMPARISONS[requirement.comparator]
        checks.append(
            Check(
                variable=requirement.variable,
                comparator=requirement.comparator,
                threshold=requirement.threshold,
                observed=observation.value,
                age_seconds=age,
                outcome=PASS if comparison(observation.value, requirement.threshold) else FAIL,
            )
        )

    if missing:
        reason_code = MISSING_REQUIRED_VARIABLE
    elif stale:
        reason_code = STALE_VARIABLE
    elif undated:
        reason_code = UNDATED_VARIABLE
    elif ill_typed:
        reason_code = ILL_TYPED_VARIABLE
    else:
        reason_code = ""
    if reason_code:
        return _error(
            policy,
            reason_code,
            now,
            missing=tuple(missing),
            stale=tuple(stale),
            undated=tuple(undated),
            ill_typed=tuple(ill_typed),
            absent_optional=tuple(absent_optional),
        )

    unevaluated = unevaluated_variables(
        policy, tuple(checks), tuple(absent_optional)
    )
    if unevaluated:
        return _error(policy, INCOMPLETE_EVALUATION, now, missing=unevaluated)

    passed = all(check.outcome == PASS for check in checks)
    return Discharge(
        status=PASS if passed else FAIL,
        policy_id=policy.policy_id,
        reason_code=POLICY_SATISFIED if passed else POLICY_UNSATISFIED,
        blocking=False,
        decided_at=now,
        checks=tuple(checks),
        absent_optional=tuple(absent_optional),
    )
