from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable


class ConstraintSpecError(ValueError):
    pass


class SolverStatus(str, Enum):
    BOUNDED_SAT = "BOUNDED_SAT"
    BOUNDED_UNSAT = "BOUNDED_UNSAT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class SolverResult:
    status: SolverStatus
    witness: dict[str, Any] | None
    explored: int
    reason: str
    backend: str


def _operand(spec: Any, assignment: dict[str, Any]) -> Any:
    if not isinstance(spec, dict) or set(spec) not in ({"var"}, {"const"}):
        raise ConstraintSpecError("operand must contain exactly one of var or const")
    if "var" in spec:
        name = spec["var"]
        if name not in assignment:
            raise ConstraintSpecError(f"unknown variable: {name}")
        return assignment[name]
    return spec["const"]


def evaluate_constraint(spec: dict[str, Any], assignment: dict[str, Any]) -> bool:
    if not isinstance(spec, dict) or "op" not in spec:
        raise ConstraintSpecError("constraint must be an object with op")
    op = spec["op"]
    if op in {"eq", "neq", "lt", "le", "gt", "ge"}:
        left = _operand(spec.get("left"), assignment)
        right = _operand(spec.get("right"), assignment)
        return {
            "eq": lambda: left == right,
            "neq": lambda: left != right,
            "lt": lambda: left < right,
            "le": lambda: left <= right,
            "gt": lambda: left > right,
            "ge": lambda: left >= right,
        }[op]()
    if op in {"in", "not_in"}:
        value = _operand(spec.get("value"), assignment)
        values = spec.get("values")
        if not isinstance(values, list):
            raise ConstraintSpecError("in/not_in requires a values list")
        return (value in values) if op == "in" else (value not in values)
    if op == "all_different":
        names = spec.get("vars")
        if not isinstance(names, list) or not names:
            raise ConstraintSpecError("all_different requires nonempty vars")
        values = [assignment[name] for name in names]
        # Pairwise ==, not set(). set() is hash-based, so it raises TypeError on
        # a legal unhashable domain value such as a JSON array, while the z3
        # backend answers happily — the same repr-vs-== split, one layer down.
        for i, left in enumerate(values):
            for right in values[i + 1 :]:
                if left == right:
                    return False
        return True
    if op == "table":
        names = spec.get("vars")
        allowed = spec.get("allowed")
        if not isinstance(names, list) or not isinstance(allowed, list):
            raise ConstraintSpecError("table requires vars and allowed")
        row = [assignment[name] for name in names]
        return row in allowed
    if op in {"and", "or"}:
        children = spec.get("constraints")
        if not isinstance(children, list) or not children:
            raise ConstraintSpecError(f"{op} requires nonempty constraints")
        results = [evaluate_constraint(child, assignment) for child in children]
        return all(results) if op == "and" else any(results)
    if op == "not":
        child = spec.get("constraint")
        if not isinstance(child, dict):
            raise ConstraintSpecError("not requires one constraint")
        return not evaluate_constraint(child, assignment)
    raise ConstraintSpecError(f"unsupported constraint op: {op}")


@dataclass(frozen=True)
class FiniteConstraintProblem:
    variables: tuple[tuple[str, tuple[Any, ...]], ...]
    constraints: tuple[dict[str, Any], ...]

    @classmethod
    def from_spec(cls, spec: dict[str, Any]) -> "FiniteConstraintProblem":
        variables = spec.get("variables")
        constraints = spec.get("constraints")
        if not isinstance(variables, dict) or not variables:
            raise ConstraintSpecError("variables must be a nonempty object")
        if not isinstance(constraints, list):
            raise ConstraintSpecError("constraints must be a list")
        parsed: list[tuple[str, tuple[Any, ...]]] = []
        for name, domain in variables.items():
            if not isinstance(name, str) or not name:
                raise ConstraintSpecError("variable names must be nonempty strings")
            if not isinstance(domain, list) or not domain:
                raise ConstraintSpecError(f"domain for {name} must be nonempty")
            canonical = tuple(domain)
            # Compare with ==, not repr. JSON true and 1 have distinct reprs but
            # are == in Python, and the enumeration backend compares with ==. A
            # repr-only check admits domains the two backends read differently.
            for i, left in enumerate(canonical):
                for right in canonical[i + 1 :]:
                    if left == right:
                        raise ConstraintSpecError(
                            f"domain for {name} contains duplicates"
                        )
            parsed.append((name, canonical))
        problem = cls(tuple(parsed), tuple(constraints))
        # Validate every expression against a representative bounded assignment.
        sample = {name: domain[0] for name, domain in problem.variables}
        for constraint in problem.constraints:
            evaluate_constraint(constraint, sample)
        return problem

    @property
    def state_count(self) -> int:
        return math.prod(len(domain) for _, domain in self.variables)

    def assignments(self) -> Iterable[dict[str, Any]]:
        names = [name for name, _ in self.variables]
        domains = [domain for _, domain in self.variables]
        for values in itertools.product(*domains):
            yield dict(zip(names, values, strict=True))

    def solve_enumerated(self, max_states: int = 100_000) -> SolverResult:
        if self.state_count > max_states:
            return SolverResult(
                SolverStatus.UNKNOWN,
                None,
                0,
                f"state_count_exceeds_bound:{self.state_count}>{max_states}",
                "enumeration",
            )
        explored = 0
        for assignment in self.assignments():
            explored += 1
            if all(evaluate_constraint(c, assignment) for c in self.constraints):
                return SolverResult(
                    SolverStatus.BOUNDED_SAT,
                    assignment,
                    explored,
                    "finite_witness_found",
                    "enumeration",
                )
        return SolverResult(
            SolverStatus.BOUNDED_UNSAT,
            None,
            explored,
            "finite_domain_exhausted",
            "enumeration",
        )

    def solve_z3(self, max_states: int = 100_000) -> SolverResult:
        """Optional Z3 backend for the finite supported subset.

        A model is returned as one bounded witness.  Z3 equality here is
        equality of finite encoding addresses, not ontological identity.
        """

        if self.state_count > max_states:
            return SolverResult(
                SolverStatus.UNKNOWN,
                None,
                0,
                f"state_count_exceeds_bound:{self.state_count}>{max_states}",
                "z3",
            )
        try:
            import z3  # type: ignore
        except ModuleNotFoundError as exc:
            if exc.name == "z3":
                return SolverResult(
                    SolverStatus.UNKNOWN,
                    None,
                    0,
                    "z3_unavailable",
                    "z3",
                )
            raise

        domains = {name: domain for name, domain in self.variables}
        reverse = {
            name: {i: value for i, value in enumerate(domain)}
            for name, domain in self.variables
        }

        def address_of(name: str, value: Any) -> int | None:
            """Resolve a value to its domain address under ==.

            The enumeration backend compares with ==, so this backend must too,
            or the two disagree on the same spec.  from_spec guarantees domains
            are pairwise distinct under ==, so at most one address matches.
            """
            for position, candidate in enumerate(domains[name]):
                if candidate == value:
                    return position
            return None
        vars_z3 = {name: z3.Int(name) for name, _ in self.variables}
        solver = z3.Solver()
        for name, domain in self.variables:
            solver.add(z3.Or([vars_z3[name] == i for i in range(len(domain))]))

        def compile_equality(left: Any, right: Any) -> Any:
            if not isinstance(left, dict) or not isinstance(right, dict):
                raise ConstraintSpecError("bad equality operand")
            if set(left) == {"const"} and set(right) == {"const"}:
                return z3.BoolVal(left["const"] == right["const"])
            if set(left) == {"var"} and set(right) == {"const"}:
                name = left["var"]
                address = address_of(name, right["const"])
                return z3.BoolVal(False) if address is None else vars_z3[name] == address
            if set(left) == {"const"} and set(right) == {"var"}:
                return compile_equality(right, left)
            if set(left) == {"var"} and set(right) == {"var"}:
                left_name = left["var"]
                right_name = right["var"]
                shared = [
                    (i, j)
                    for i, left_value in enumerate(domains[left_name])
                    for j, right_value in enumerate(domains[right_name])
                    if left_value == right_value
                ]
                if not shared:
                    return z3.BoolVal(False)
                return z3.Or(
                    [
                        z3.And(
                            vars_z3[left_name] == i,
                            vars_z3[right_name] == j,
                        )
                        for i, j in shared
                    ]
                )
            raise ConstraintSpecError("bad equality operand")

        def compile_one(spec: dict[str, Any]) -> Any:
            op = spec["op"]
            if op in {"eq", "neq"}:
                equality = compile_equality(spec.get("left"), spec.get("right"))
                return equality if op == "eq" else z3.Not(equality)
            if op == "all_different":
                names = spec["vars"]
                return z3.And(
                    [
                        z3.Not(
                            compile_equality(
                                {"var": names[i]}, {"var": names[j]}
                            )
                        )
                        for i in range(len(names))
                        for j in range(i + 1, len(names))
                    ]
                )
            if op in {"and", "or"}:
                terms = [compile_one(child) for child in spec["constraints"]]
                return z3.And(terms) if op == "and" else z3.Or(terms)
            if op == "not":
                return z3.Not(compile_one(spec["constraint"]))
            raise ConstraintSpecError(
                f"Z3 backend supports eq, neq, all_different, and/or/not; got {op}"
            )

        try:
            for constraint in self.constraints:
                solver.add(compile_one(constraint))
        except (ConstraintSpecError, KeyError):
            return SolverResult(
                SolverStatus.UNKNOWN,
                None,
                0,
                "constraint_not_supported_by_z3_profile",
                "z3",
            )
        status = solver.check()
        if status == z3.unknown:
            return SolverResult(
                SolverStatus.UNKNOWN, None, 0, f"z3_unknown:{solver.reason_unknown()}", "z3"
            )
        if status == z3.unsat:
            return SolverResult(
                SolverStatus.BOUNDED_UNSAT,
                None,
                self.state_count,
                "bounded_encoding_unsat",
                "z3",
            )
        model = solver.model()
        witness = {
            name: reverse[name][model.eval(var).as_long()]
            for name, var in vars_z3.items()
        }
        return SolverResult(
            SolverStatus.BOUNDED_SAT,
            witness,
            0,
            "bounded_model_found",
            "z3",
        )
