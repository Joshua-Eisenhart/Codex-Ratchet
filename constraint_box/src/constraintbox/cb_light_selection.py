"""SMT-backed CB Light work selection over measured proposal rows.

The selector does not discover candidates and does not install anything. It
maps every proposal row into a finite constraint problem and preserves unknown
facts as open Boolean domains. A satisfiable open domain is an OPEN_BASIN, not
an admission. Adoption remains a separate owner-authority transition.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from .dualsolve import dual_solve


WORK_REQUIREMENTS = (
    "light_profile",
    "metadata_admissible",
    "role_declared",
    "declared_for_current_work",
    "installed_in_mandated_interpreter",
    "import_succeeds",
    "positive_api_case",
    "reason_specific_negative",
    "single_field_boundary_flip",
    "deterministic_replay",
    "severance_observed",
    "reference_agreement",
    "receipt_consumer_bound",
)
_STRUCTURAL = {"light_profile", "metadata_admissible"}


def _selection_source_hashes() -> dict[str, str]:
    directory = Path(__file__).resolve().parent
    paths = {
        "src/constraintbox/cb_light_selection.py": directory
        / "cb_light_selection.py",
        "src/constraintbox/constraints.py": directory / "constraints.py",
        "src/constraintbox/dualsolve.py": directory / "dualsolve.py",
    }
    return {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in paths.items()
    }


def _metadata_admissible(row: Mapping[str, Any]) -> bool | None:
    if row.get("kind") == "stdlib_module":
        return True
    metadata = row.get("registry_metadata")
    if not isinstance(metadata, Mapping):
        return None
    predicates = metadata.get("predicates")
    if not isinstance(predicates, Mapping):
        return None
    values = list(predicates.values())
    if metadata.get("registry_verdict") == "drop" or any(value is False for value in values):
        return False
    if values and all(value is True for value in values):
        return True
    return None


def measured_facts(
    row: Mapping[str, Any], probe_decision: Mapping[str, Any] | None = None
) -> dict[str, bool | None]:
    declarations = row.get("declarations") or {}
    observation = row.get("observation") or {}
    probe = (probe_decision or {}).get("facts") or {}
    installed = observation.get("installed")
    version_ok = observation.get("version_satisfies_declaration")
    if (
        row.get("kind") == "distribution"
        and declarations.get("pyproject_direct")
        and installed is True
    ):
        installed_for_work = version_ok
    else:
        installed_for_work = bool(installed) if installed is not None else None
    return {
        "light_profile": True,
        "metadata_admissible": _metadata_admissible(row),
        "role_declared": bool(row.get("role_claims")),
        "declared_for_current_work": bool(
            declarations.get("pyproject_direct") and row.get("core_contract")
        ),
        "installed_in_mandated_interpreter": installed_for_work,
        "import_succeeds": (
            bool(observation["import_visible"])
            if observation.get("import_visible") is not None
            else None
        ),
        "positive_api_case": probe.get("positive_api_case"),
        "reason_specific_negative": probe.get("reason_specific_negative"),
        "single_field_boundary_flip": probe.get("single_field_boundary_flip"),
        "deterministic_replay": probe.get("deterministic_replay"),
        "severance_observed": probe.get("severance_observed"),
        "reference_agreement": probe.get("reference_agreement"),
        "receipt_consumer_bound": probe.get("receipt_consumer_bound"),
    }


def _spec(facts: Mapping[str, bool | None]) -> dict[str, Any]:
    return {
        "variables": {
            name: [False, True] if facts[name] is None else [facts[name]]
            for name in WORK_REQUIREMENTS
        },
        "constraints": [
            {
                "op": "eq",
                "left": {"var": name},
                "right": {"const": True},
            }
            for name in WORK_REQUIREMENTS
        ],
    }


def _normal_status(result: Mapping[str, Any]) -> str | None:
    votes = [result.get(name) for name in ("z3", "cvc5", "enumeration")]
    definite = {"SAT", "UNSAT", "BOUNDED_SAT", "BOUNDED_UNSAT"}
    if any(value not in definite for value in votes):
        return None
    statuses = {value.removeprefix("BOUNDED_") for value in votes}
    return next(iter(statuses)) if len(statuses) == 1 else None


def decide_row(
    row: Mapping[str, Any],
    probe_decision: Mapping[str, Any] | None = None,
    *,
    solve: Callable[[dict[str, Any]], dict[str, Any]] = dual_solve,
    cached_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    facts = measured_facts(row, probe_decision)
    result = dict(cached_result) if cached_result is not None else solve(_spec(facts))
    normal = _normal_status(result)
    failed = [name for name, value in facts.items() if value is False]
    open_variables = [name for name, value in facts.items() if value is None]

    if not result.get("agree") or normal is None:
        disposition = "HOLD_DECIDER"
        reason = "SELECTION_DECIDER_UNRESOLVED"
    elif normal == "SAT" and not open_variables:
        disposition = "SELECTED_FOR_WORK"
        reason = "WORK_CONSTRAINTS_SATISFIED"
    elif normal == "SAT":
        disposition = "OPEN_BASIN"
        reason = "ADMISSIBLE_COMPLETION_EXISTS"
    elif any(name in _STRUCTURAL for name in failed):
        disposition = "EXCLUDED_BY_CONSTRAINT"
        reason = "STRUCTURAL_LIGHT_CONSTRAINT_FAILED"
    else:
        disposition = "HOLD_MISSING_EVIDENCE"
        reason = "WORK_EVIDENCE_INCOMPLETE"

    return {
        "candidate_id": row["candidate_id"],
        "disposition": disposition,
        "reason_code": reason,
        "facts": facts,
        "failed_observed": failed,
        "open_variables": open_variables,
        "solver": {
            "z3": result.get("z3"),
            "cvc5": result.get("cvc5"),
            "enumeration": result.get("enumeration"),
            "agree": bool(result.get("agree")),
            "disagreement": result.get("disagreement"),
            "witnesses": result.get("witnesses"),
        },
        "adoption": {
            "disposition": "HOLD",
            "reason_code": "OWNER_APPROVAL_REQUIRED",
            "protected_owner_approval": None,
        },
        "claim_ceiling": "candidate work selection only; not adoption",
    }


def decide_domain(
    domain: Mapping[str, Any], probe_matrix: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    by_distribution = {
        decision["distribution"]: decision
        for decision in (probe_matrix or {}).get("tool_decisions", [])
    }
    cache: dict[tuple[bool | None, ...], dict[str, Any]] = {}
    decisions: list[dict[str, Any]] = []
    for row in domain["rows"]:
        probe = by_distribution.get(row["normalized_name"])
        facts = measured_facts(row, probe)
        signature = tuple(facts[name] for name in WORK_REQUIREMENTS)
        result = cache.get(signature)
        if result is None:
            result = dual_solve(_spec(facts))
            cache[signature] = result
        decisions.append(decide_row(row, probe, cached_result=result))

    counts: dict[str, int] = {}
    for decision in decisions:
        disposition = decision["disposition"]
        counts[disposition] = counts.get(disposition, 0) + 1
    source_hashes = _selection_source_hashes()
    return {
        "schema": "constraintbox.cb-light-selection.v1",
        "profile": "cb_light",
        "domain_sha256": domain["domain_sha256"],
        "requirements": list(WORK_REQUIREMENTS),
        "counts": counts,
        "decisions": decisions,
        "source_hashes": source_hashes,
        "source_set_sha256": hashlib.sha256(
            json.dumps(source_hashes, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "owner_approved_adoptions": 0,
        "promotion_allowed": False,
        "claim_ceiling": "full proposal-domain selection state; no adoption authority",
    }
