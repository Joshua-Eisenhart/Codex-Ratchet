from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .constraints import FiniteConstraintProblem, SolverResult


@dataclass(frozen=True)
class DeciderOutcome:
    decider: str
    status: str
    raw_verdict: str | None
    normal_verdict: str | None
    detail: str | None


@dataclass(frozen=True)
class CrossCheckResult:
    claim_kind: str
    outcomes: tuple[DeciderOutcome, ...]
    agreement: str
    reason: str


@dataclass(frozen=True)
class _RegisteredDecider:
    name: str
    run: Callable[[dict[str, Any]], tuple[str, str | None]]
    normalise: Callable[[str], tuple[str, str | None]]


def _solver_outcome(result: SolverResult) -> tuple[str, str | None]:
    return result.status.value, result.reason


def _run_enumeration(claim: dict[str, Any]) -> tuple[str, str | None]:
    return _solver_outcome(
        FiniteConstraintProblem.from_spec(claim).solve_enumerated()
    )


def _run_z3(claim: dict[str, Any]) -> tuple[str, str | None]:
    return _solver_outcome(FiniteConstraintProblem.from_spec(claim).solve_z3())


def _run_cvc5(claim: dict[str, Any]) -> tuple[str, str | None]:
    from .dualsolve import _solve_cvc5

    problem = FiniteConstraintProblem.from_spec(claim)
    return _solver_outcome(_solve_cvc5(problem))


def _normalise_finite(raw_verdict: str) -> tuple[str, str | None]:
    if raw_verdict == "BOUNDED_SAT":
        return "DECIDED", "SAT"
    if raw_verdict == "BOUNDED_UNSAT":
        return "DECIDED", "UNSAT"
    if raw_verdict == "UNKNOWN":
        return "ABSTAINED", None
    return "UNMAPPED", None


def _ratchet_floor_smt() -> Any:
    repo_root = Path(__file__).resolve().parents[3]
    repo_root_text = str(repo_root)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
    return importlib.import_module("claimgate_plugin.ratchet_floor_smt")


def _ratchet_case(module: Any, claim: dict[str, Any]) -> Any:
    current = claim.get("current")
    next_spec = claim.get("next")
    if not isinstance(current, dict) or not isinstance(next_spec, dict):
        raise ValueError("ratchet_floor_transition requires current and next specs")

    for case in module.cross_check_cases():
        if (
            module.floor_claims_to_spec(case.domains, case.prior_floors)
            == current
            and module.floor_claims_to_spec(
                case.domains, case.candidate_claims
            )
            == next_spec
        ):
            return case
    raise ValueError(
        "ratchet floor transition is not one of lane 1 cross_check_cases()"
    )


def _run_scalar(claim: dict[str, Any]) -> tuple[str, str | None]:
    module = _ratchet_floor_smt()
    verdict, exit_code = module._run_scalar_case(_ratchet_case(module, claim))
    return verdict, f"exit_code={exit_code}"


def _run_smt(claim: dict[str, Any]) -> tuple[str, str | None]:
    module = _ratchet_floor_smt()
    current = claim.get("current")
    next_spec = claim.get("next")
    if not isinstance(current, dict) or not isinstance(next_spec, dict):
        raise ValueError("ratchet_floor_transition requires current and next specs")
    verdict = module.classify_transition(current, next_spec)
    return verdict.value, None


def _normalise_scalar(raw_verdict: str) -> tuple[str, str | None]:
    normal = {
        "ADMITTED": "FLOOR_MOVES_OR_HOLDS",
        "REJECTED": "FLOOR_BLOCKED",
    }.get(raw_verdict)
    return ("DECIDED", normal) if normal is not None else ("UNMAPPED", None)


def _normalise_smt(raw_verdict: str) -> tuple[str, str | None]:
    normal = {
        "TIGHTENED": "FLOOR_MOVES_OR_HOLDS",
        "EQUIVALENT": "FLOOR_MOVES_OR_HOLDS",
        "WEAKENED": "FLOOR_BLOCKED",
    }.get(raw_verdict)
    return ("DECIDED", normal) if normal is not None else ("UNMAPPED", None)


def _registry() -> dict[str, tuple[_RegisteredDecider, ...]]:
    return {
        "finite_constraint_satisfiability": (
            _RegisteredDecider("enumeration", _run_enumeration, _normalise_finite),
            _RegisteredDecider("z3", _run_z3, _normalise_finite),
            _RegisteredDecider("cvc5", _run_cvc5, _normalise_finite),
        ),
        "ratchet_floor_transition": (
            _RegisteredDecider("scalar", _run_scalar, _normalise_scalar),
            _RegisteredDecider("smt", _run_smt, _normalise_smt),
        ),
    }


def registered_claim_kinds() -> tuple[str, ...]:
    return tuple(_registry())


def cross_check(claim_kind: str, claim: dict[str, Any]) -> CrossCheckResult:
    try:
        deciders = _registry()[claim_kind]
    except KeyError as exc:
        raise ValueError(f"unregistered claim kind: {claim_kind}") from exc

    outcomes = []
    for decider in deciders:
        try:
            raw_verdict, detail = decider.run(claim)
            status, normal_verdict = decider.normalise(raw_verdict)
        except Exception as exc:
            outcomes.append(
                DeciderOutcome(
                    decider=decider.name,
                    status="ERRORED",
                    raw_verdict=None,
                    normal_verdict=None,
                    detail=str(exc),
                )
            )
            continue
        outcomes.append(
            DeciderOutcome(
                decider=decider.name,
                status=status,
                raw_verdict=raw_verdict,
                normal_verdict=normal_verdict,
                detail=detail,
            )
        )

    frozen_outcomes = tuple(outcomes)
    decided = [outcome for outcome in frozen_outcomes if outcome.status == "DECIDED"]
    normal_verdicts = {outcome.normal_verdict for outcome in decided}
    if (
        len(frozen_outcomes) >= 2
        and len(decided) == len(frozen_outcomes)
        and len(normal_verdicts) == 1
    ):
        return CrossCheckResult(claim_kind, frozen_outcomes, "AGREE", "")

    non_decided = [
        f"{outcome.decider}={outcome.status}"
        for outcome in frozen_outcomes
        if outcome.status != "DECIDED"
    ]
    reasons = []
    if len(frozen_outcomes) < 2:
        reasons.append("fewer than two deciders ran")
    if non_decided:
        reasons.append("not every decider decided: " + ", ".join(non_decided))
    if len(decided) >= 2 and len(normal_verdicts) > 1:
        reasons.append("normal verdicts disagree")
    return CrossCheckResult(
        claim_kind,
        frozen_outcomes,
        "UNRESOLVED",
        "; ".join(reasons),
    )
