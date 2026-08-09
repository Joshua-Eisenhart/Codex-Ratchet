"""ClaimGate-owned finite-constraint intake contract, version 1.

This small stdlib-only parser intentionally mirrors the JSON shape accepted by
the CR/ConstraintBox bridge without importing ConstraintBox. Cross-product
agreement belongs in a bridge test; ClaimGate must remain runnable alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


CONTRACT_VERSION = "finite-constraint.v1"


class ConstraintSpecError(ValueError):
    pass


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
        operations = {
            "eq": lambda: left == right,
            "neq": lambda: left != right,
            "lt": lambda: left < right,
            "le": lambda: left <= right,
            "gt": lambda: left > right,
            "ge": lambda: left >= right,
        }
        return bool(operations[op]())
    if op in {"in", "not_in"}:
        value = _operand(spec.get("value"), assignment)
        values = spec.get("values")
        if not isinstance(values, list):
            raise ConstraintSpecError("in/not_in requires a values list")
        return value in values if op == "in" else value not in values
    if op == "all_different":
        names = spec.get("vars")
        if not isinstance(names, list) or not names:
            raise ConstraintSpecError("all_different requires nonempty vars")
        values = [assignment[name] for name in names]
        return all(left != right for index, left in enumerate(values) for right in values[index + 1 :])
    if op == "table":
        names = spec.get("vars")
        allowed = spec.get("allowed")
        if not isinstance(names, list) or not isinstance(allowed, list):
            raise ConstraintSpecError("table requires vars and allowed")
        return [assignment[name] for name in names] in allowed
    if op in {"and", "or"}:
        children = spec.get("constraints")
        if not isinstance(children, list) or not children:
            raise ConstraintSpecError(f"{op} requires nonempty constraints")
        values = [evaluate_constraint(child, assignment) for child in children]
        return all(values) if op == "and" else any(values)
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
            for index, left in enumerate(canonical):
                if any(left == right for right in canonical[index + 1 :]):
                    raise ConstraintSpecError(f"domain for {name} contains duplicates")
            parsed.append((name, canonical))
        problem = cls(tuple(parsed), tuple(constraints))
        sample = {name: domain[0] for name, domain in problem.variables}
        for constraint in problem.constraints:
            evaluate_constraint(constraint, sample)
        return problem
