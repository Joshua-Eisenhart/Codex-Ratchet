"""Deterministic failed-clause feedback from controller-built Booleans.

This module accepts no SMT text or expression language.  The controller
supplies a bounded ordered set of named Boolean obligations.  Z3 and CVC5 each
check every obligation under one assumption literal, expose the singleton
unsat core for a failed obligation, and are cross-checked against the
controller's direct Boolean reference.
"""

from __future__ import annotations

import hashlib
import importlib
import re
from pathlib import Path
from typing import Any

from .intake import canonical_json


DEFAULT_Z3_TIMEOUT_MS = 5_000
DEFAULT_CVC5_TIMEOUT_MS = 5_000
_MAX_CLAUSES = 64
_CLAUSE_NAME = re.compile(r"[a-z][a-z0-9_]{0,127}")
_OPERATION = "singleton_assumption_unsat_core"
_Z3_API = "Solver.check(assumption); Solver.unsat_core()"
_CVC5_API = (
    "Solver.checkSatAssuming(assumption); "
    "Solver.getUnsatAssumptions()"
)
_EXPECTED_Z3_VERSION = (4, 16, 0, 0)
_EXPECTED_CVC5_VERSION = "1.3.3"


class ClauseFeedbackError(RuntimeError):
    """An invoked clause-feedback operation failed or disagreed."""

    def __init__(
        self,
        reason: str,
        evidence: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(reason)
        self.reason = reason
        self.evidence = evidence or {}


class ClauseFeedbackUnavailable(ImportError):
    """A required solver module could not be acquired before invocation."""


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _import_solver(name: str, evidence: dict[str, Any]) -> Any:
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        if exc.name == name:
            raise ClauseFeedbackUnavailable(
                f"{name} unavailable: {exc}"
            ) from exc
        raise ClauseFeedbackError(
            f"{name}_import_failed",
            {
                **evidence,
                "backend": name,
                "exception_type": type(exc).__name__,
                "missing_module": exc.name,
                "error": str(exc),
            },
        ) from exc
    except Exception as exc:
        raise ClauseFeedbackError(
            f"{name}_import_failed",
            {
                **evidence,
                "backend": name,
                "exception_type": type(exc).__name__,
                "error": str(exc),
            },
        ) from exc


def _validated_timeout(name: str, value: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 60_000
    ):
        raise ClauseFeedbackError(
            "clause_feedback_controller_contract_invalid",
            {"error": f"{name} must be an integer from 1 through 60000"},
        )
    return value


def _validate_controller_inputs(
    values: dict[str, bool],
    clause_order: tuple[str, ...],
    retry_questions: dict[str, str],
    reference_failed: tuple[str, ...],
) -> tuple[str, ...]:
    if (
        not isinstance(values, dict)
        or not isinstance(clause_order, tuple)
        or not 1 <= len(clause_order) <= _MAX_CLAUSES
        or len(set(clause_order)) != len(clause_order)
        or any(
            not isinstance(name, str)
            or _CLAUSE_NAME.fullmatch(name) is None
            for name in clause_order
        )
        or set(values) != set(clause_order)
        or any(
            not isinstance(values[name], bool)
            for name in clause_order
        )
    ):
        raise ClauseFeedbackError(
            "clause_feedback_controller_contract_invalid",
            {
                "error": (
                    "values must contain exactly 1 through 64 unique, "
                    "bounded clause names with Boolean values"
                )
            },
        )
    if (
        not isinstance(retry_questions, dict)
        or set(retry_questions) != set(clause_order)
        or any(
            not isinstance(retry_questions[name], str)
            or not retry_questions[name].strip()
            or len(retry_questions[name]) > 2_000
            for name in clause_order
        )
    ):
        raise ClauseFeedbackError(
            "clause_feedback_controller_contract_invalid",
            {
                "error": (
                    "retry_questions must contain one bounded nonempty "
                    "controller-authored question per clause"
                )
            },
        )
    if (
        not isinstance(reference_failed, tuple)
        or any(name not in values for name in reference_failed)
        or len(set(reference_failed)) != len(reference_failed)
    ):
        raise ClauseFeedbackError(
            "clause_feedback_controller_contract_invalid",
            {"error": "reference_failed is not a unique clause tuple"},
        )

    derived = tuple(name for name in clause_order if not values[name])
    if reference_failed != derived:
        raise ClauseFeedbackError(
            "clause_feedback_reference_mismatch",
            {
                "reference_failed": list(reference_failed),
                "derived_failed": list(derived),
            },
        )
    return derived


def _literal_name(index: int, clause: str) -> str:
    return f"cb_requirement_{index}_{clause}"


def _run_z3_feedback(
    z3_module: Any,
    values: dict[str, bool],
    clause_order: tuple[str, ...],
    *,
    timeout_ms: int,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    failed: list[str] = []
    for index, clause in enumerate(clause_order):
        literal_name = _literal_name(index, clause)
        solver = z3_module.Solver()
        solver.set(timeout=timeout_ms)
        observed = z3_module.Bool(f"cb_observed_{index}_{clause}")
        assumption = z3_module.Bool(literal_name)
        solver.add(observed == z3_module.BoolVal(values[clause]))
        solver.add(z3_module.Implies(assumption, observed))
        status = solver.check(assumption)
        if status == z3_module.sat:
            core_names: list[str] = []
            status_name = "SAT"
        elif status == z3_module.unsat:
            core_names = [str(term) for term in solver.unsat_core()]
            if core_names != [literal_name]:
                raise ValueError(
                    "Z3 singleton unsat core did not identify its assumption"
                )
            failed.append(clause)
            status_name = "UNSAT"
        else:
            raise RuntimeError(
                f"Z3 returned a nondefinite clause result for {clause}"
            )
        checks.append(
            {
                "clause": clause,
                "assumption_literal": literal_name,
                "status": status_name,
                "unsat_core": core_names,
            }
        )
    return {
        "api": _Z3_API,
        "summary_status": (
            "FAILED_CLAUSES_IDENTIFIED"
            if failed
            else "ALL_CLAUSES_SATISFIED"
        ),
        "failed_clauses": failed,
        "checks": checks,
    }


def _new_cvc5_solver(cvc5_module: Any) -> Any:
    """Seam used to verify the exact CVC5 operation can fail closed."""

    return cvc5_module.Solver()


def _run_cvc5_feedback(
    cvc5_module: Any,
    values: dict[str, bool],
    clause_order: tuple[str, ...],
    *,
    timeout_ms: int,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    failed: list[str] = []
    for index, clause in enumerate(clause_order):
        literal_name = _literal_name(index, clause)
        solver = _new_cvc5_solver(cvc5_module)
        solver.setLogic("QF_UF")
        solver.setOption("produce-unsat-assumptions", "true")
        solver.setOption("tlimit-per", str(timeout_ms))
        boolean_sort = solver.getBooleanSort()
        observed = solver.mkConst(
            boolean_sort, f"cb_observed_{index}_{clause}"
        )
        assumption = solver.mkConst(boolean_sort, literal_name)
        solver.assertFormula(
            solver.mkTerm(
                cvc5_module.Kind.EQUAL,
                observed,
                solver.mkBoolean(values[clause]),
            )
        )
        solver.assertFormula(
            solver.mkTerm(
                cvc5_module.Kind.IMPLIES,
                assumption,
                observed,
            )
        )
        status = solver.checkSatAssuming(assumption)
        if status.isSat():
            core_names: list[str] = []
            status_name = "SAT"
        elif status.isUnsat():
            core_names = [
                str(term) for term in solver.getUnsatAssumptions()
            ]
            if core_names != [literal_name]:
                raise ValueError(
                    "CVC5 singleton unsat core did not identify its assumption"
                )
            failed.append(clause)
            status_name = "UNSAT"
        else:
            raise RuntimeError(
                f"CVC5 returned a nondefinite clause result for {clause}"
            )
        checks.append(
            {
                "clause": clause,
                "assumption_literal": literal_name,
                "status": status_name,
                "unsat_core": core_names,
            }
        )
    return {
        "api": _CVC5_API,
        "summary_status": (
            "FAILED_CLAUSES_IDENTIFIED"
            if failed
            else "ALL_CLAUSES_SATISFIED"
        ),
        "failed_clauses": failed,
        "checks": checks,
    }


def build_clause_feedback(
    values: dict[str, bool],
    *,
    clause_order: tuple[str, ...],
    retry_questions: dict[str, str],
    reference_failed: tuple[str, ...],
    z3_timeout_ms: int = DEFAULT_Z3_TIMEOUT_MS,
    cvc5_timeout_ms: int = DEFAULT_CVC5_TIMEOUT_MS,
) -> dict[str, Any]:
    """Return solver-certified retry feedback for controller-built clauses.

    Missing solver modules raise :class:`ClauseFeedbackUnavailable` so the
    request boundary can PARK an unavailable required instrument. Once a
    backend is imported and invoked, any exception, malformed core,
    nondefinite result, or cross-check mismatch raises
    :class:`ClauseFeedbackError`.
    """

    reference = _validate_controller_inputs(
        values,
        clause_order,
        retry_questions,
        reference_failed,
    )
    z3_timeout_ms = _validated_timeout("z3_timeout_ms", z3_timeout_ms)
    cvc5_timeout_ms = _validated_timeout(
        "cvc5_timeout_ms", cvc5_timeout_ms
    )
    canonical_input = [
        {
            "clause": name,
            "satisfied": values[name],
            "retry_question": retry_questions[name],
        }
        for name in clause_order
    ]
    settings = {
        "operation": _OPERATION,
        "strategy": "one_controller_built_assumption_literal_per_check",
        "maximum_clauses": _MAX_CLAUSES,
        "z3": {"timeout_ms": z3_timeout_ms, "api": _Z3_API},
        "cvc5": {
            "timeout_ms": cvc5_timeout_ms,
            "api": _CVC5_API,
            "produce_unsat_assumptions": True,
        },
    }
    base_evidence: dict[str, Any] = {
        "schema": "constraintbox.clause-feedback.v1",
        "canonical_input": canonical_input,
        "canonical_input_sha256": _sha256(canonical_input),
        "settings": settings,
        "settings_sha256": _sha256(settings),
        "profile_source_sha256": hashlib.sha256(
            Path(__file__).read_bytes()
        ).hexdigest(),
        "reference_failed_clauses": list(reference),
        "claim_ceiling": (
            "solver-certified retry feedback for this bounded request-clause "
            "encoding only; no proposal, truth, external result, or release "
            "is admitted"
        ),
    }

    # Import only after validating controller-built input. Solver acquisition
    # is the sole unavailability path; all failures after import are errors.
    z3_module = _import_solver("z3", base_evidence)
    cvc5_module = _import_solver("cvc5", base_evidence)
    expected_versions = {
        "z3": list(_EXPECTED_Z3_VERSION),
        "cvc5": _EXPECTED_CVC5_VERSION,
    }
    observed_versions: dict[str, Any] = {
        "z3": None,
        "cvc5": None,
    }
    try:
        z3_version = z3_module.get_version()
        if (
            not isinstance(z3_version, tuple)
            or len(z3_version) != 4
            or any(
                isinstance(part, bool) or not isinstance(part, int)
                for part in z3_version
            )
        ):
            raise TypeError("z3.get_version() did not return four integers")
        observed_versions["z3"] = list(z3_version)
        cvc5_version = cvc5_module.__version__
        if not isinstance(cvc5_version, str) or not cvc5_version:
            raise TypeError("cvc5.__version__ was not a nonempty string")
        observed_versions["cvc5"] = cvc5_version
    except Exception as exc:
        raise ClauseFeedbackError(
            "clause_feedback_version_probe_failed",
            {
                **base_evidence,
                "tool_versions": {
                    "expected": expected_versions,
                    "observed": observed_versions,
                },
                "exception_type": type(exc).__name__,
                "error": str(exc),
            },
        ) from exc

    tool_versions = {
        "expected": expected_versions,
        "observed": observed_versions,
    }
    bound_evidence = {
        **base_evidence,
        "tool_versions": tool_versions,
        "tool_versions_sha256": _sha256(tool_versions),
    }
    version_drift = [
        backend
        for backend in ("z3", "cvc5")
        if observed_versions[backend] != expected_versions[backend]
    ]
    if version_drift:
        raise ClauseFeedbackError(
            "clause_feedback_version_drift",
            {
                **bound_evidence,
                "drifted_backends": version_drift,
            },
        )
    try:
        z3_output = _run_z3_feedback(
            z3_module,
            values,
            clause_order,
            timeout_ms=z3_timeout_ms,
        )
    except Exception as exc:
        raise ClauseFeedbackError(
            "z3_clause_feedback_execution_failed",
            {
                **bound_evidence,
                "backend": "z3",
                "exception_type": type(exc).__name__,
                "error": str(exc),
            },
        ) from exc
    try:
        cvc5_output = _run_cvc5_feedback(
            cvc5_module,
            values,
            clause_order,
            timeout_ms=cvc5_timeout_ms,
        )
    except Exception as exc:
        raise ClauseFeedbackError(
            "cvc5_clause_feedback_execution_failed",
            {
                **bound_evidence,
                "backend": "cvc5",
                "exception_type": type(exc).__name__,
                "error": str(exc),
            },
        ) from exc

    retry_feedback = [
        {
            "clause": name,
            "question": retry_questions[name],
            "minimal_failed_assumption": _literal_name(
                clause_order.index(name), name
            ),
        }
        for name in reference
    ]
    result: dict[str, Any] = {
        **bound_evidence,
        "per_solver": {
            "z3": z3_output,
            "cvc5": cvc5_output,
        },
        "retry_feedback": retry_feedback,
        "agree": (
            z3_output["failed_clauses"]
            == cvc5_output["failed_clauses"]
            == list(reference)
        ),
    }
    if not result["agree"]:
        raise ClauseFeedbackError(
            "clause_feedback_crosscheck_disagreement",
            {
                **result,
                "mismatch": {
                    "reference": list(reference),
                    "z3": z3_output["failed_clauses"],
                    "cvc5": cvc5_output["failed_clauses"],
                },
            },
        )
    result["result_sha256"] = _sha256(result)
    return result
