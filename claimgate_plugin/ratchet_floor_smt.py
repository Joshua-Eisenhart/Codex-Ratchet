#!/usr/bin/env python3
"""Finite SMT implication decider for ratchet-floor transitions.

The input language is the ``FiniteConstraintProblem.from_spec`` shape from
``constraintbox.constraints``.  This module supports every operation accepted
by that language: ``eq``, ``neq``, ``lt``, ``le``, ``gt``, ``ge``, ``in``,
``not_in``, ``all_different``, ``table``, ``and``, ``or``, and ``not``.
Anything else raises ``UnsupportedConstraintOpError`` before solving.

Every variable is one shared Z3 Int constrained to its finite domain-address
range.  Constants, cross-variable equality, and cross-side domain identity are
resolved under Python ``==``, never ``repr``.  Variable-name order is
irrelevant, but each named domain is order-sensitive because positions are the
encoding addresses.  Consequently ``[0, 1]`` and ``[False, True]`` count as the
same domain: this is the inherited ``==`` decision made by
``FiniteConstraintProblem``, not a new type-identity policy.

Scalar/SMT cross-check mapping:

* scalar ``ADMITTED`` agrees with SMT ``TIGHTENED`` or ``EQUIVALENT``;
* scalar ``REJECTED`` agrees with SMT ``WEAKENED`` or ``BROKEN``;
* scalar ``PARKED`` has no SMT implication counterpart and therefore cannot
  produce ``AGREE``;
* SMT ``BROKEN`` and ``INCOMPARABLE`` have no faithful scalar-floor verdict.

The mapping is intentionally partial.  Cross-check disagreements are printed
with their exact inputs and are never used to rewrite either decider.
"""

from __future__ import annotations

import argparse
import json
import operator
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from constraintbox.constraints import ConstraintSpecError, FiniteConstraintProblem


SUPPORTED_OPS = frozenset(
    {
        "eq",
        "neq",
        "lt",
        "le",
        "gt",
        "ge",
        "in",
        "not_in",
        "all_different",
        "table",
        "and",
        "or",
        "not",
    }
)


class RatchetFloorSMTError(ConstraintSpecError):
    """Base class for named intake and solver errors."""


class UndeclaredSymbolError(RatchetFloorSMTError):
    """A constraint references a symbol absent from its variable declaration."""


class VariableDomainMismatchError(RatchetFloorSMTError):
    """The two sides do not declare the same typed finite variables."""


class UnsupportedConstraintOpError(RatchetFloorSMTError):
    """A constraint operation is outside the documented supported language."""


class ConstraintEncodingError(RatchetFloorSMTError):
    """A validated constraint cannot be compiled with matching semantics."""


class SolverDecisionError(RatchetFloorSMTError):
    """Z3 returned unknown instead of a decidable bounded result."""


class RatchetVerdict(str, Enum):
    BROKEN = "BROKEN"
    EQUIVALENT = "EQUIVALENT"
    TIGHTENED = "TIGHTENED"
    WEAKENED = "WEAKENED"
    INCOMPARABLE = "INCOMPARABLE"


SCALAR_TO_SMT_AGREEMENT: Mapping[str, frozenset[RatchetVerdict]] = {
    "ADMITTED": frozenset(
        {RatchetVerdict.TIGHTENED, RatchetVerdict.EQUIVALENT}
    ),
    "REJECTED": frozenset(
        {RatchetVerdict.WEAKENED, RatchetVerdict.BROKEN}
    ),
    "PARKED": frozenset(),
}


def _constraint_nodes(constraints: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(constraints, list):
        return
    for constraint in constraints:
        if not isinstance(constraint, dict):
            continue
        yield constraint
        children = constraint.get("constraints")
        if isinstance(children, list):
            yield from _constraint_nodes(children)
        child = constraint.get("constraint")
        if isinstance(child, dict):
            yield from _constraint_nodes([child])


def _operand_symbols(operand: Any) -> Iterable[Any]:
    if not isinstance(operand, dict):
        return
    if "var" in operand:
        yield operand["var"]
    # A const payload is data, even when that data itself contains a "var" key.
    if "const" in operand:
        return
    for value in operand.values():
        if isinstance(value, dict):
            yield from _operand_symbols(value)
        elif isinstance(value, list):
            for item in value:
                yield from _operand_symbols(item)


def _referenced_symbols(constraints: Any) -> Iterable[Any]:
    for constraint in _constraint_nodes(constraints):
        names = constraint.get("vars")
        if isinstance(names, list):
            yield from names
        for key in ("left", "right", "value"):
            yield from _operand_symbols(constraint.get(key))


def _validate_declared_symbols(spec: Any, side: str) -> None:
    if not isinstance(spec, dict) or not isinstance(spec.get("variables"), dict):
        return
    declared = set(spec["variables"])
    for symbol in _referenced_symbols(spec.get("constraints")):
        if not isinstance(symbol, str) or symbol not in declared:
            raise UndeclaredSymbolError(
                f"{side} constraint set references undeclared symbol {symbol!r}"
            )


def _validate_supported_ops(spec: Any, side: str) -> None:
    if not isinstance(spec, dict):
        return
    for constraint in _constraint_nodes(spec.get("constraints")):
        op = constraint.get("op")
        if isinstance(op, str) and op not in SUPPORTED_OPS:
            supported = ", ".join(sorted(SUPPORTED_OPS))
            raise UnsupportedConstraintOpError(
                f"{side} constraint set uses unsupported op {op!r}; "
                f"supported ops: {supported}"
            )


def _parse_problem(spec: dict[str, Any], side: str) -> FiniteConstraintProblem:
    # Run the two projection-sensitive checks before from_spec: from_spec's
    # representative assignment would otherwise expose unknown all_different
    # names as a raw KeyError rather than this named intake error.
    _validate_declared_symbols(spec, side)
    _validate_supported_ops(spec, side)
    return FiniteConstraintProblem.from_spec(spec)


def _equal_under_eq(left: Any, right: Any) -> bool:
    try:
        return bool(left == right)
    except Exception:
        return False


def _validate_same_variables(
    current: FiniteConstraintProblem, next_problem: FiniteConstraintProblem
) -> None:
    current_domains = dict(current.variables)
    next_domains = dict(next_problem.variables)
    current_names = set(current_domains)
    next_names = set(next_domains)
    if current_names != next_names:
        missing_from_next = sorted(current_names - next_names)
        missing_from_current = sorted(next_names - current_names)
        raise VariableDomainMismatchError(
            "variable names differ: "
            f"missing_from_next={missing_from_next}, "
            f"missing_from_current={missing_from_current}"
        )

    for name in sorted(current_names):
        left_domain = current_domains[name]
        right_domain = next_domains[name]
        if len(left_domain) != len(right_domain):
            raise VariableDomainMismatchError(
                f"domain for {name!r} differs in length: "
                f"{len(left_domain)} != {len(right_domain)}"
            )
        for index, (left, right) in enumerate(
            zip(left_domain, right_domain, strict=True)
        ):
            if not _equal_under_eq(left, right):
                raise VariableDomainMismatchError(
                    f"domain for {name!r} differs at index {index}: "
                    f"{left!r} ({type(left).__name__}) != "
                    f"{right!r} ({type(right).__name__})"
                )


def _truth(value: Any, *, context: str) -> bool:
    try:
        return bool(value)
    except Exception as exc:
        raise ConstraintEncodingError(
            f"{context} did not produce a scalar truth value: {exc}"
        ) from exc


class _FiniteZ3Compiler:
    def __init__(self, problem: FiniteConstraintProblem):
        try:
            import z3  # type: ignore
        except ImportError as exc:
            raise SolverDecisionError("z3 is unavailable") from exc
        self.z3 = z3
        self.domains = dict(problem.variables)
        self.variables = {
            name: z3.Int(f"ratchet_floor::{name}") for name in self.domains
        }
        self.bounds = [
            z3.Or(
                [
                    self.variables[name] == address
                    for address in range(len(domain))
                ]
            )
            for name, domain in self.domains.items()
        ]

    def _operand_cases(self, operand: Any) -> list[tuple[Any, Any]]:
        if not isinstance(operand, dict) or set(operand) not in (
            {"var"},
            {"const"},
        ):
            raise ConstraintEncodingError(
                "operand must contain exactly one of var or const"
            )
        if "const" in operand:
            return [(self.z3.BoolVal(True), operand["const"])]
        name = operand["var"]
        if name not in self.domains:
            raise UndeclaredSymbolError(
                f"constraint references undeclared symbol {name!r}"
            )
        return [
            (self.variables[name] == address, value)
            for address, value in enumerate(self.domains[name])
        ]

    def _relation(
        self,
        left: Any,
        right: Any,
        predicate: Callable[[Any, Any], Any],
        *,
        op_name: str,
    ) -> Any:
        terms = []
        for left_condition, left_value in self._operand_cases(left):
            for right_condition, right_value in self._operand_cases(right):
                try:
                    keep = _truth(
                        predicate(left_value, right_value),
                        context=f"{op_name} comparison",
                    )
                except TypeError as exc:
                    raise ConstraintEncodingError(
                        f"{op_name} cannot compare "
                        f"{left_value!r} and {right_value!r}: {exc}"
                    ) from exc
                if keep:
                    terms.append(
                        self.z3.And(left_condition, right_condition)
                    )
        return self.z3.Or(terms) if terms else self.z3.BoolVal(False)

    def _membership(self, operand: Any, values: Any, *, negate: bool) -> Any:
        if not isinstance(values, list):
            raise ConstraintEncodingError("in/not_in requires a values list")

        def contained(value: Any, candidates: list[Any]) -> bool:
            return value in candidates

        expression = self._relation(
            operand,
            {"const": values},
            contained,
            op_name="not_in" if negate else "in",
        )
        return self.z3.Not(expression) if negate else expression

    def _table(self, names: Any, allowed: Any) -> Any:
        if not isinstance(names, list) or not isinstance(allowed, list):
            raise ConstraintEncodingError("table requires vars and allowed")
        rows = []
        for candidate in allowed:
            if not isinstance(candidate, list) or len(candidate) != len(names):
                continue
            cells = [
                self._relation(
                    {"var": name},
                    {"const": value},
                    operator.eq,
                    op_name="table",
                )
                for name, value in zip(names, candidate, strict=True)
            ]
            rows.append(self.z3.And(cells))
        return self.z3.Or(rows) if rows else self.z3.BoolVal(False)

    def compile_one(self, spec: dict[str, Any]) -> Any:
        op = spec["op"]
        comparisons: Mapping[str, Callable[[Any, Any], Any]] = {
            "eq": operator.eq,
            "neq": operator.ne,
            "lt": operator.lt,
            "le": operator.le,
            "gt": operator.gt,
            "ge": operator.ge,
        }
        if op in comparisons:
            return self._relation(
                spec.get("left"),
                spec.get("right"),
                comparisons[op],
                op_name=op,
            )
        if op in {"in", "not_in"}:
            return self._membership(
                spec.get("value"),
                spec.get("values"),
                negate=op == "not_in",
            )
        if op == "all_different":
            names = spec["vars"]
            terms = [
                self.z3.Not(
                    self._relation(
                        {"var": names[left_index]},
                        {"var": names[right_index]},
                        operator.eq,
                        op_name="all_different",
                    )
                )
                for left_index in range(len(names))
                for right_index in range(left_index + 1, len(names))
            ]
            return self.z3.And(terms)
        if op == "table":
            return self._table(spec.get("vars"), spec.get("allowed"))
        if op in {"and", "or"}:
            terms = [
                self.compile_one(child) for child in spec["constraints"]
            ]
            return (
                self.z3.And(terms) if op == "and" else self.z3.Or(terms)
            )
        if op == "not":
            return self.z3.Not(self.compile_one(spec["constraint"]))
        raise UnsupportedConstraintOpError(f"unsupported constraint op: {op!r}")

    def compile_problem(self, problem: FiniteConstraintProblem) -> Any:
        return self.z3.And(
            [self.compile_one(constraint) for constraint in problem.constraints]
        )

    def is_unsat(self, expression: Any, *, query: str) -> bool:
        solver = self.z3.Solver()
        solver.add(*self.bounds)
        solver.add(expression)
        status = solver.check()
        if status == self.z3.unknown:
            raise SolverDecisionError(
                f"{query} returned z3 unknown: {solver.reason_unknown()}"
            )
        return status == self.z3.unsat


def classify_transition(
    current_spec: dict[str, Any], next_spec: dict[str, Any]
) -> RatchetVerdict:
    """Classify a finite constraint-set transition with three Z3 queries."""

    current = _parse_problem(current_spec, "current")
    next_problem = _parse_problem(next_spec, "next")
    _validate_same_variables(current, next_problem)

    compiler = _FiniteZ3Compiler(current)
    current_expression = compiler.compile_problem(current)
    next_expression = compiler.compile_problem(next_problem)

    # This guard must precede implication: false implies every proposition.
    if compiler.is_unsat(next_expression, query="SAT(C_next)"):
        return RatchetVerdict.BROKEN

    next_implies_current = compiler.is_unsat(
        compiler.z3.And(next_expression, compiler.z3.Not(current_expression)),
        query="C_next AND NOT C_t",
    )
    current_implies_next = compiler.is_unsat(
        compiler.z3.And(current_expression, compiler.z3.Not(next_expression)),
        query="C_t AND NOT C_next",
    )
    if next_implies_current and current_implies_next:
        return RatchetVerdict.EQUIVALENT
    if next_implies_current:
        return RatchetVerdict.TIGHTENED
    if current_implies_next:
        return RatchetVerdict.WEAKENED
    return RatchetVerdict.INCOMPARABLE


def _comparison_constraint(
    key: str, value: Any, direction: str
) -> dict[str, Any]:
    if direction == "higher_is_better":
        op = "ge"
    elif direction == "lower_is_better":
        op = "le"
    else:
        raise ValueError(f"unknown scalar direction: {direction!r}")
    return {
        "op": op,
        "left": {"var": key},
        "right": {"const": value},
    }


def floor_claims_to_spec(
    domains: Mapping[str, Sequence[Any]],
    claims: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Encode scalar claims as finite admitted regions."""

    return {
        "variables": {name: list(domain) for name, domain in domains.items()},
        "constraints": [
            _comparison_constraint(
                str(claim["key"]), claim["value"], str(claim["direction"])
            )
            for claim in claims
        ],
    }


@dataclass(frozen=True)
class VerdictDemoRow:
    example: str
    verdict: str
    wall_ms: float


def verdict_examples() -> list[tuple[str, dict[str, Any], dict[str, Any]]]:
    domain = {"x": [0, 1, 2, 3]}

    def spec(constraints: list[dict[str, Any]]) -> dict[str, Any]:
        return {"variables": domain, "constraints": constraints}

    def ge(value: int) -> dict[str, Any]:
        return _comparison_constraint("x", value, "higher_is_better")

    def eq(value: int) -> dict[str, Any]:
        return {
            "op": "eq",
            "left": {"var": "x"},
            "right": {"const": value},
        }

    return [
        ("tightened_floor_1_to_2", spec([ge(1)]), spec([ge(2)])),
        ("equivalent_same_floor", spec([ge(1)]), spec([ge(1)])),
        ("weakened_floor_2_to_1", spec([ge(2)]), spec([ge(1)])),
        (
            "broken_unsat_next",
            spec([ge(1)]),
            spec(
                [
                    {
                        "op": "and",
                        "constraints": [eq(0), eq(1)],
                    }
                ]
            ),
        ),
        (
            "incomparable_disjoint_singletons",
            spec([eq(0)]),
            spec([eq(1)]),
        ),
    ]


def run_verdict_demo() -> list[VerdictDemoRow]:
    rows = []
    for name, current_spec, next_spec in verdict_examples():
        started = time.perf_counter()
        verdict = classify_transition(current_spec, next_spec)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        rows.append(VerdictDemoRow(name, verdict.value, elapsed_ms))
    return rows


def format_verdict_demo(rows: Sequence[VerdictDemoRow]) -> str:
    lines = [
        "FIVE VERDICT DEMONSTRATION",
        "EXAMPLE | SMT VERDICT | WALL_MS",
    ]
    lines.extend(
        f"{row.example} | {row.verdict} | {row.wall_ms:.3f}"
        for row in rows
    )
    return "\n".join(lines)


@dataclass(frozen=True)
class CrossCheckCase:
    name: str
    domains: dict[str, list[Any]]
    prior_floors: list[dict[str, Any]]
    candidate_claims: list[dict[str, Any]]


@dataclass(frozen=True)
class CrossCheckRow:
    name: str
    scalar_verdict: str
    scalar_exit_code: int
    smt_verdict: str
    agreement: str
    exact_input: dict[str, Any]


def cross_check_cases() -> list[CrossCheckCase]:
    higher = "higher_is_better"
    lower = "lower_is_better"

    def claim(key: str, value: Any, direction: str) -> dict[str, Any]:
        return {"key": key, "value": value, "direction": direction}

    return [
        CrossCheckCase(
            "higher_tightened",
            {"x": [0, 1, 2]},
            [claim("x", 1, higher)],
            [claim("x", 2, higher)],
        ),
        CrossCheckCase(
            "higher_equivalent",
            {"x": [0, 1, 2]},
            [claim("x", 1, higher)],
            [claim("x", 1, higher)],
        ),
        CrossCheckCase(
            "higher_weakened",
            {"x": [0, 1, 2]},
            [claim("x", 2, higher)],
            [claim("x", 1, higher)],
        ),
        CrossCheckCase(
            "lower_tightened",
            {"x": [0, 1, 2]},
            [claim("x", 1, lower)],
            [claim("x", 0, lower)],
        ),
        CrossCheckCase(
            "lower_equivalent",
            {"x": [0, 1, 2]},
            [claim("x", 1, lower)],
            [claim("x", 1, lower)],
        ),
        CrossCheckCase(
            "lower_weakened",
            {"x": [0, 1, 2]},
            [claim("x", 0, lower)],
            [claim("x", 1, lower)],
        ),
        CrossCheckCase(
            "epsilon_tolerance_gap",
            {"x": [0.9999999999995, 1.0, 1.5]},
            [claim("x", 1.0, higher)],
            [claim("x", 0.9999999999995, higher)],
        ),
        CrossCheckCase(
            "empty_admitted_region",
            {"x": [0, 1, 2]},
            [claim("x", 1, higher)],
            [claim("x", 3, higher)],
        ),
        CrossCheckCase(
            "direction_flip",
            {"x": [0, 1, 2]},
            [claim("x", 1, higher)],
            [claim("x", 1, lower)],
        ),
        CrossCheckCase(
            "multi_metric_tradeoff",
            {"x": [0, 1, 2], "y": [0, 1, 2]},
            [claim("x", 1, higher), claim("y", 1, higher)],
            [claim("x", 2, higher), claim("y", 0, higher)],
        ),
        CrossCheckCase(
            "unknown_new_key",
            {"x": [0, 1, 2]},
            [],
            [claim("x", 1, higher)],
        ),
    ]


def _run_scalar_case(case: CrossCheckCase) -> tuple[str, int]:
    scalar_path = Path(__file__).with_name("ratchet_floor.py")
    with tempfile.TemporaryDirectory(prefix="ratchet-floor-smt-") as temp:
        temp_path = Path(temp)
        store_path = temp_path / "store.json"
        if case.prior_floors:
            seed_path = temp_path / "seed.json"
            seed_path.write_text(
                json.dumps({"floor_claims": case.prior_floors}),
                encoding="utf-8",
            )
            seeded = subprocess.run(
                [
                    sys.executable,
                    str(scalar_path),
                    "admit",
                    str(seed_path),
                    "--store",
                    str(store_path),
                    "--allow-new-keys",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            if seeded.returncode != 0:
                raise RuntimeError(
                    "ratchet_floor.py could not seed prior floors: "
                    f"exit={seeded.returncode} stdout={seeded.stdout!r} "
                    f"stderr={seeded.stderr!r}"
                )
        receipt_path = temp_path / "receipt.json"
        receipt_path.write_text(
            json.dumps({"floor_claims": case.candidate_claims}),
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(scalar_path),
                "admit",
                str(receipt_path),
                "--store",
                str(store_path),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        try:
            report = json.loads(completed.stdout)
            verdict = str(report["verdict"])
        except (json.JSONDecodeError, KeyError) as exc:
            raise RuntimeError(
                "ratchet_floor.py returned unreadable output: "
                f"exit={completed.returncode} stdout={completed.stdout!r} "
                f"stderr={completed.stderr!r}"
            ) from exc
        expected_exit = {"ADMITTED": 0, "REJECTED": 1, "PARKED": 3}.get(
            verdict
        )
        if completed.returncode != expected_exit:
            raise RuntimeError(
                "ratchet_floor.py verdict/exit mismatch: "
                f"verdict={verdict} exit={completed.returncode}"
            )
        return verdict, completed.returncode


def run_cross_check() -> list[CrossCheckRow]:
    rows = []
    for case in cross_check_cases():
        scalar_verdict, scalar_exit = _run_scalar_case(case)
        current_spec = floor_claims_to_spec(
            case.domains, case.prior_floors
        )
        next_spec = floor_claims_to_spec(
            case.domains, case.candidate_claims
        )
        smt_verdict = classify_transition(current_spec, next_spec)
        agrees = smt_verdict in SCALAR_TO_SMT_AGREEMENT[scalar_verdict]
        exact_input = {
            "domains": case.domains,
            "prior_floors": case.prior_floors,
            "candidate_claims": case.candidate_claims,
            "allow_new_keys": False,
        }
        rows.append(
            CrossCheckRow(
                case.name,
                scalar_verdict,
                scalar_exit,
                smt_verdict.value,
                "AGREE" if agrees else "DISAGREE",
                exact_input,
            )
        )
    return rows


def format_cross_check(rows: Sequence[CrossCheckRow]) -> str:
    lines = [
        "SCALAR / SMT CROSS-CHECK",
        "INPUT | SCALAR VERDICT | SCALAR EXIT | SMT VERDICT | RESULT",
    ]
    lines.extend(
        f"{row.name} | {row.scalar_verdict} | "
        f"{row.scalar_exit_code} | {row.smt_verdict} | {row.agreement}"
        for row in rows
    )
    disagreements = [row for row in rows if row.agreement == "DISAGREE"]
    if disagreements:
        lines.append("DISAGREEMENTS (EXACT INPUTS)")
        lines.append(
            json.dumps(
                [asdict(row) for row in disagreements],
                indent=2,
                sort_keys=True,
            )
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--demo", action="store_true", help="print timed five-verdict examples"
    )
    parser.add_argument(
        "--cross-check",
        action="store_true",
        help="run scalar subprocess/SMT cross-check rows",
    )
    args = parser.parse_args(argv)
    if not args.demo and not args.cross_check:
        parser.error("select --demo and/or --cross-check")

    if args.demo:
        print(format_verdict_demo(run_verdict_demo()))
    disagreements = []
    if args.cross_check:
        rows = run_cross_check()
        print(format_cross_check(rows))
        disagreements = [row for row in rows if row.agreement == "DISAGREE"]
    return 1 if disagreements else 0


if __name__ == "__main__":
    raise SystemExit(main())
