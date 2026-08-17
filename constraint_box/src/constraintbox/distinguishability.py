"""Stage 1: compile a distinguishability packet into FiniteConstraintProblem.

Identity is not primitive.  The primitive is probe-relative
indistinguishability under a finite family M:

    a ~_M b  :=  ∀ p ∈ M. obs(p, a) = obs(p, b)
    Distinguish(a, b, M) := ∃ p ∈ M. obs(p, a) ≠ obs(p, b)

This module compiles that relation into the existing finite constraint
language and asks dual_solve (z3 + cvc5 + enumeration) to decide it.
It does not install packages, touch CB Heavy, or promote a claim ceiling.

Unsat cores are extracted three ways and compared:
- deletion MUS on the existing enumeration/dualsolve surface
- Z3 assert_and_track / unsat_core
- cvc5 checkSatAssuming / getUnsatAssumptions
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from constraintbox.constraints import (
    ConstraintSpecError,
    FiniteConstraintProblem,
    SolverStatus,
    evaluate_constraint,
)
from constraintbox.dualsolve import dual_solve

PACKET_SCHEMA = "constraintbox.distinguishability.packet.v1"
RECEIPT_SCHEMA = "constraintbox.distinguishability.receipt.v1"
QUERY = Literal["distinguish", "demand_thick", "admissible", "encoding_control"]
CEILING = Literal["exists", "runs", "passes_local_rerun", "canonical_by_process"]
_NAME_OK = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")


class DistinguishabilityError(ValueError):
    """The packet is malformed or not a finite Stage-1 encoding."""


class DemandEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    left: str
    right: str
    id: str
    why_demanded: str = ""


class NamedConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    constraint: dict[str, Any]


class DistinguishabilityPacket(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    schema_name: Literal["constraintbox.distinguishability.packet.v1"] = Field(
        alias="schema"
    )
    claim: str
    claim_ceiling: CEILING
    candidates: list[str] = Field(min_length=2)
    probes: list[str] = Field(min_length=1)
    probe_domains: dict[str, list[Any]]
    demand_D: list[DemandEdge] = Field(default_factory=list)
    constraints_C: list[NamedConstraint] = Field(default_factory=list)
    query: QUERY
    theory: str
    authority: Literal["none"]
    negative_control: dict[str, Any] | None = None

    @field_validator("candidates", "probes")
    @classmethod
    def _unique_names(cls, values: list[str]) -> list[str]:
        if any(not value or set(value) - _NAME_OK for value in values):
            raise ValueError("names must be nonempty [A-Za-z0-9_-]+")
        if len(set(values)) != len(values):
            raise ValueError("names must be unique")
        return values


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def obs_var(probe: str, candidate: str) -> str:
    return f"obs__{probe}__{candidate}"


def _distinguish_constraint(probes: list[str], left: str, right: str) -> dict[str, Any]:
    return {
        "op": "or",
        "constraints": [
            {
                "op": "neq",
                "left": {"var": obs_var(probe, left)},
                "right": {"var": obs_var(probe, right)},
            }
            for probe in probes
        ],
    }


def compile_packet(
    raw: dict[str, Any],
) -> tuple[DistinguishabilityPacket, dict[str, Any], list[tuple[str, dict[str, Any]]]]:
    """Validate a packet and compile it to a finite spec plus named assumptions."""

    try:
        packet = DistinguishabilityPacket.model_validate(raw)
    except ValidationError as exc:
        raise DistinguishabilityError(f"packet_invalid:{exc}") from exc
    if packet.theory != "finite":
        raise DistinguishabilityError("theory_not_finite")
    if set(packet.probe_domains) != set(packet.probes):
        raise DistinguishabilityError("probe_domains_mismatch")
    for probe, domain in packet.probe_domains.items():
        if not isinstance(domain, list) or len(domain) < 2:
            raise DistinguishabilityError(f"probe_domain_too_small:{probe}")

    variables = {
        obs_var(probe, candidate): list(domain)
        for probe, domain in packet.probe_domains.items()
        for candidate in packet.candidates
    }
    named: list[tuple[str, dict[str, Any]]] = []
    if packet.query in {"distinguish", "demand_thick"}:
        if not packet.demand_D:
            raise DistinguishabilityError("demand_required")
        for edge in packet.demand_D:
            if edge.left not in packet.candidates or edge.right not in packet.candidates:
                raise DistinguishabilityError(f"demand_unknown_candidate:{edge.id}")
            if edge.left == edge.right:
                raise DistinguishabilityError(f"demand_not_a_pair:{edge.id}")
            named.append(
                (f"demand:{edge.id}", _distinguish_constraint(packet.probes, edge.left, edge.right))
            )
    elif packet.query in {"admissible", "encoding_control"}:
        if not packet.constraints_C:
            raise DistinguishabilityError("constraints_C_required")
    for item in packet.constraints_C:
        named.append((f"C:{item.id}", item.constraint))

    spec = {
        "variables": variables,
        "constraints": [constraint for _name, constraint in named],
    }
    try:
        FiniteConstraintProblem.from_spec(spec)
    except ConstraintSpecError as exc:
        raise DistinguishabilityError(f"compiled_spec_invalid:{exc}") from exc
    return packet, spec, named


def _deletion_mus(spec: dict[str, Any], named: list[tuple[str, dict[str, Any]]]) -> list[str]:
    """Greedy deletion core using the same evaluate_constraint path as enumeration."""

    active = list(named)
    variables = spec["variables"]

    def unsat(items: list[tuple[str, dict[str, Any]]]) -> bool:
        problem = FiniteConstraintProblem.from_spec(
            {"variables": variables, "constraints": [item[1] for item in items]}
        )
        return problem.solve_enumerated().status is SolverStatus.BOUNDED_UNSAT

    if not unsat(active):
        return []
    changed = True
    while changed:
        changed = False
        for index, item in enumerate(list(active)):
            trial = active[:index] + active[index + 1 :]
            if trial and unsat(trial):
                active = trial
                changed = True
                break
    return [name for name, _constraint in active]


def _z3_tracked_core(
    spec: dict[str, Any], named: list[tuple[str, dict[str, Any]]]
) -> dict[str, Any]:
    try:
        import z3
    except ModuleNotFoundError:
        return {"status": "UNAVAILABLE", "core": [], "reason": "z3_unavailable"}

    problem = FiniteConstraintProblem.from_spec(spec)
    domains = {name: domain for name, domain in problem.variables}
    vars_z3 = {name: z3.Int(name) for name, _domain in problem.variables}

    def address_of(name: str, value: Any) -> int | None:
        for position, candidate in enumerate(domains[name]):
            if candidate == value:
                return position
        return None

    def compile_equality(left: Any, right: Any) -> Any:
        if set(left) == {"var"} and set(right) == {"const"}:
            address = address_of(left["var"], right["const"])
            return z3.BoolVal(False) if address is None else vars_z3[left["var"]] == address
        if set(left) == {"const"} and set(right) == {"var"}:
            return compile_equality(right, left)
        if set(left) == {"var"} and set(right) == {"var"}:
            shared = [
                (i, j)
                for i, left_value in enumerate(domains[left["var"]])
                for j, right_value in enumerate(domains[right["var"]])
                if left_value == right_value
            ]
            if not shared:
                return z3.BoolVal(False)
            return z3.Or(
                [
                    z3.And(vars_z3[left["var"]] == i, vars_z3[right["var"]] == j)
                    for i, j in shared
                ]
            )
        return z3.BoolVal(left["const"] == right["const"])

    def compile_one(item: dict[str, Any]) -> Any:
        op = item["op"]
        if op in {"eq", "neq"}:
            equality = compile_equality(item["left"], item["right"])
            return equality if op == "eq" else z3.Not(equality)
        if op in {"and", "or"}:
            terms = [compile_one(child) for child in item["constraints"]]
            return z3.And(terms) if op == "and" else z3.Or(terms)
        if op == "not":
            return z3.Not(compile_one(item["constraint"]))
        raise DistinguishabilityError(f"z3_core_unsupported_op:{op}")

    solver = z3.Solver()
    solver.set(unsat_core=True)
    solver.set("core.minimize", True)
    for name, domain in problem.variables:
        solver.add(z3.Or([vars_z3[name] == i for i in range(len(domain))]))
    for assumption_id, constraint in named:
        solver.assert_and_track(compile_one(constraint), assumption_id)
    status = solver.check()
    if status == z3.sat:
        return {"status": "BOUNDED_SAT", "core": [], "reason": "expected_unsat"}
    if status != z3.unsat:
        return {"status": "UNKNOWN", "core": [], "reason": str(status)}
    return {
        "status": "BOUNDED_UNSAT",
        "core": sorted(str(item) for item in solver.unsat_core()),
        "reason": "z3_unsat_core",
    }


def _cvc5_assumption_core(
    spec: dict[str, Any], named: list[tuple[str, dict[str, Any]]]
) -> dict[str, Any]:
    try:
        import cvc5
        from cvc5 import Kind
    except ModuleNotFoundError:
        return {"status": "UNAVAILABLE", "core": [], "reason": "cvc5_unavailable"}

    from constraintbox.dualsolve import _cvc5_compile_constraint, _or

    problem = FiniteConstraintProblem.from_spec(spec)
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    solver.setOption("produce-models", "true")
    solver.setOption("produce-unsat-cores", "true")
    solver.setOption("produce-unsat-assumptions", "true")
    domains = {name: domain for name, domain in problem.variables}
    selectors: dict[str, list[Any]] = {}
    for variable_index, (variable, domain) in enumerate(problem.variables):
        choices = [
            solver.mkConst(
                solver.getBooleanSort(),
                f"core_sel_{variable_index}_{value_index}",
            )
            for value_index in range(len(domain))
        ]
        selectors[variable] = choices
        solver.assertFormula(_or(solver, Kind, choices))
        for left in range(len(choices)):
            for right in range(left + 1, len(choices)):
                solver.assertFormula(
                    solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.AND, choices[left], choices[right]))
                )
    flags = []
    for assumption_id, constraint in named:
        flag = solver.mkConst(solver.getBooleanSort(), assumption_id)
        flags.append(flag)
        compiled = _cvc5_compile_constraint(
            solver, Kind, selectors, domains, constraint
        )
        solver.assertFormula(solver.mkTerm(Kind.IMPLIES, flag, compiled))
    result = solver.checkSatAssuming(*flags)
    if result.isSat():
        return {"status": "BOUNDED_SAT", "core": [], "reason": "expected_unsat"}
    if not result.isUnsat():
        return {"status": "UNKNOWN", "core": [], "reason": "cvc5_unknown"}
    core = []
    for term in solver.getUnsatAssumptions():
        name = term.getSymbol() if term.hasSymbol() else str(term)
        core.append(name)
    return {
        "status": "BOUNDED_UNSAT",
        "core": sorted(core),
        "reason": "cvc5_unsat_assumptions",
    }


def _solver_versions() -> dict[str, str]:
    versions = {"python": platform.python_version(), "interpreter": sys.executable}
    try:
        import z3

        versions["z3"] = z3.get_version_string()
    except Exception as exc:  # noqa: BLE001 — version probe only
        versions["z3"] = f"unavailable:{type(exc).__name__}"
    try:
        import cvc5

        versions["cvc5"] = getattr(cvc5, "__version__", str(cvc5))
    except Exception as exc:  # noqa: BLE001 — version probe only
        versions["cvc5"] = f"unavailable:{type(exc).__name__}"
    return versions


def decide_packet(raw: dict[str, Any]) -> dict[str, Any]:
    """Compile, dual-solve, and receipt one distinguishability packet."""

    payload = {
        "schema": RECEIPT_SCHEMA,
        "operation": "finite_probe_assignment_feasibility.v1",
        "interpreter": sys.executable,
        "packet_sha256": _sha256(raw),
        "authority": "none",
        "solver_versions": _solver_versions(),
    }
    try:
        packet, spec, named = compile_packet(raw)
    except DistinguishabilityError as exc:
        payload.update(
            {
                "status": "HOLD",
                "reason": str(exc),
                "claim_ceiling": "exists",
                "caller_claim_ceiling_ignored": raw.get("claim_ceiling"),
                "witness_kind": None,
                "quotient_admitted": False,
                "quotient_reason": "no bound observation rows; solver was not asked",
            }
        )
        payload["receipt_sha256"] = _sha256(payload)
        return payload

    dual = dual_solve(spec)
    named_ids = [name for name, _constraint in named]
    cores: dict[str, Any] = {}
    if dual.get("agree") and dual.get("z3") == SolverStatus.BOUNDED_UNSAT.value:
        cores = {
            "deletion": _deletion_mus(spec, named),
            "z3": _z3_tracked_core(spec, named),
            "cvc5": _cvc5_assumption_core(spec, named),
        }
    payload.update(
        {
            "status": dual["z3"] if dual.get("agree") else "UNKNOWN",
            "reason": "dual_solve_agree" if dual.get("agree") else dual.get(
                "disagreement", {}
            ).get("reason", "dual_solve_disagreement"),
            "claim": packet.claim,
            "claim_ceiling": "exists",
            "caller_claim_ceiling_ignored": packet.claim_ceiling,
            "witness_kind": "solver_chosen",
            "quotient_admitted": False,
            "quotient_reason": "solver-chosen obs__* are not bound observation rows",
            "query": packet.query,
            "theory": packet.theory,
            "named_assumptions": named_ids,
            "compiled_spec": spec,
            "dual_solve": {
                "z3": dual.get("z3"),
                "cvc5": dual.get("cvc5"),
                "enumeration": dual.get("enumeration"),
                "agree": dual.get("agree"),
                "witnesses": dual.get("witnesses"),
                "disagreement": dual.get("disagreement"),
            },
            "cores": cores,
        }
    )
    if dual.get("agree") and dual.get("z3") == SolverStatus.BOUNDED_SAT.value:
        witness = (dual.get("witnesses") or {}).get("enumeration") or (
            dual.get("witnesses") or {}
        ).get("z3")
        if witness is not None:
            payload["witness_checks"] = [
                {
                    "id": name,
                    "holds": evaluate_constraint(constraint, witness),
                }
                for name, constraint in named
            ]
    payload["receipt_sha256"] = _sha256(
        {key: value for key, value in payload.items() if key != "receipt_sha256"}
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(prog="python -m constraintbox.distinguishability")
    parser.add_argument("packet", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    raw = json.loads(args.packet.read_text(encoding="utf-8"))
    receipt = decide_packet(raw)
    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if args.out is not None:
        args.out.write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if receipt.get("status") != "HOLD" else 5


if __name__ == "__main__":
    raise SystemExit(main())
