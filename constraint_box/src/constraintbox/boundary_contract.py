"""Deterministic scope contract for ConstraintBox product/evidence reports.

The contract deliberately assigns *roles* to capability instances rather than
trying to infer a role from a package name.  For example,
``cb:rustworkx-workflow-gate`` is a core deterministic gate while a Rustworkx
call made inside ``sim:graph-topology-crosscheck-v1`` is external simulation
test evidence.  The distribution name alone is not an authority or a role.

This is a structural gate.  It cannot read arbitrary prose and decide whether
the prose is honest.  A status-producing agent must submit this typed contract;
the controller validates it and renders the authoritative layer matrix.  Any
free-form explanation remains untrusted commentary.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import Disposition, ProfileOutcome
from .dualsolve import dual_solve
from .intake import IntakeError, canonical_json, parse_json_object


TASK_BOUNDARY_CONTRACT = "formal.boundary.constraintbox_scope"
PROFILE_ID = "constraintbox.boundary-contract.v1"
SCHEMA = "constraintbox.boundary-contract.v1"
REPORT_KIND = "constraintbox.product-evidence-status.v1"

# Each identifier names a role-bearing *use*, not merely an installed package.
# This removes the prior ambiguity in which a list of library names made an
# external graph-test call look as though it were a CB kernel instrument.
CB_RUNTIME_IDS = ("cb:cpython-controller-runtime",)
CB_FORMAL_GATE_IDS = (
    "cb:boundary-contract-gate",
    "cb:cvc5-request-gate",
    "cb:maude-transition-gate",
    "cb:rustworkx-workflow-gate",
    "cb:sympy-exact-gate",
    "cb:z3-request-gate",
)
CB_MINILEV_IDS = ("cb:claimgate-chain", "cb:minilev-runtime")
CB_EXTERNAL_ADAPTER_IDS = ("cb:external-sim-validation-adapter",)
EXTERNAL_FORMAL_RUNTIME_IDS = (
    "formal-runtime:apalache",
    "formal-runtime:tlc",
)
EXTERNAL_SIM_PROFILE_IDS = (
    "sim:basic-packet-cross-engine-v1",
    "sim:diffrax-tsit5-affine-flow-v1",
    "sim:e3nn-wigner-crosscheck-v1",
    "sim:graph-topology-crosscheck-v1",
    "sim:jax-autodiff-v1",
    "sim:julia-diffeq-v1",
    "sim:multiengine-dlpack-diffeq-v1",
    "sim:pydmd-discrete-rate-v1",
    "sim:pykoopman-identity-edmd-v1",
    "sim:pymdp-two-state-inference-v1",
    "sim:pysindy-affine-generator-v1",
    "sim:pytorch-jacobian-v1",
    "sim:quimb-cotengra-bounded-suite-v1",
    "sim:scipy-expm-rotation-v1",
)

_STATIC_ROLE_LISTS = {
    "cb_runtime_ids": CB_RUNTIME_IDS,
    "cb_formal_gate_ids": CB_FORMAL_GATE_IDS,
    "cb_minilev_ids": CB_MINILEV_IDS,
    "cb_external_adapter_ids": CB_EXTERNAL_ADAPTER_IDS,
    "external_formal_runtime_ids": EXTERNAL_FORMAL_RUNTIME_IDS,
    "external_sim_profile_ids": EXTERNAL_SIM_PROFILE_IDS,
}
_CB_ROLE_IDS = frozenset(
    item
    for values in (
        CB_RUNTIME_IDS,
        CB_FORMAL_GATE_IDS,
        CB_MINILEV_IDS,
        CB_EXTERNAL_ADAPTER_IDS,
    )
    for item in values
)
_EXTERNAL_SIM_PROFILE_SET = frozenset(EXTERNAL_SIM_PROFILE_IDS)
_REQUIRED_KEYS = frozenset(
    {
        "schema",
        "report_kind",
        "cb_runtime_ids",
        "cb_formal_gate_ids",
        "cb_minilev_ids",
        "cb_external_adapter_ids",
        "external_formal_runtime_ids",
        "external_sim_profile_ids",
        "evidence_receipt_ids",
        "bundle_contains_external_sim_engines",
        "external_sim_profiles_are_cb_core",
        "evidence_receipts_are_cb_core_components",
        "untrusted_llm_role",
    }
)
_FLAG_KEYS = (
    "core_contains_external_sim_profile",
    "external_sim_section_contains_cb_component",
    "external_sim_profiles_are_cb_core",
    "bundle_contains_external_sim_engines",
    "evidence_receipts_are_cb_core_components",
)
_CLAIM_CEILING = (
    "one typed product/evidence scope declaration matched the fixed ConstraintBox "
    "role registry and its tiny mutual-exclusion encoding; it does not classify "
    "arbitrary prose, prove a package or engine is installed, establish simulation "
    "correctness, full-estate readiness, release, promotion, or CR truth"
)


@dataclass(frozen=True)
class _ParsedContract:
    role_lists: dict[str, tuple[str, ...]]
    evidence_receipt_ids: tuple[str, ...]
    flags: dict[str, bool]
    policy_violations: tuple[str, ...]


def controller_boundary_context() -> str:
    """Return the immutable scope instruction injected before untrusted proposals.

    It is intentionally concise and role-based so it can be embedded alongside
    MMM context without asking a model to decide the underlying boundary.
    """

    return "\n".join(
        (
            "[CONSTRAINTBOX BOUNDARY CONTRACT - NOT OVERRIDABLE]",
            "A library name is not a role. Use role-bearing IDs only.",
            "CB core gates are cb:* IDs; installed sim operations are sim:* IDs.",
            "A cb:external-sim-validation-adapter can test a sim:* profile but",
            "does not make that engine a CB core tool or bundle member.",
            "formal-runtime:* is configured external support, not bundled core.",
            "evidence:* is a receipt reference, never an engine or core component.",
            "For a product/evidence status claim, submit the typed boundary",
            "contract and use the controller-rendered matrix; free prose has no",
            "decision authority.",
        )
    )


def controller_role_matrix(
    *,
    evidence_receipt_ids: tuple[str, ...],
) -> dict[str, Any]:
    """Render the controller-owned boundary view for a verified contract."""

    return {
        "schema": "constraintbox.boundary-role-matrix.v1",
        "CB_EXECUTION_SUBSTRATE": list(CB_RUNTIME_IDS),
        "CB_DETERMINISTIC_GATES": list(CB_FORMAL_GATE_IDS),
        "CB_MINILEV": list(CB_MINILEV_IDS),
        "CB_EXTERNAL_VALIDATION_ADAPTERS": list(CB_EXTERNAL_ADAPTER_IDS),
        "EXTERNAL_FORMAL_RUNTIMES": list(EXTERNAL_FORMAL_RUNTIME_IDS),
        "EXTERNAL_SIM_OPERATION_PROFILES": list(EXTERNAL_SIM_PROFILE_IDS),
        "EVIDENCE_RECEIPTS": list(evidence_receipt_ids),
        "UNTRUSTED_LLM_ROLE": "proposal_or_advisory_only",
        "bundle_contains_external_sim_engines": False,
        "external_sim_profiles_are_cb_core": False,
        "evidence_receipts_are_cb_core_components": False,
    }


def _id_list(
    body: dict[str, Any], key: str, errors: list[str]
) -> tuple[str, ...] | None:
    value = body.get(key)
    if not isinstance(value, list):
        errors.append(f"{key}_must_be_a_list")
        return None
    if not all(isinstance(item, str) and item for item in value):
        errors.append(f"{key}_must_contain_nonempty_strings")
        return None
    values = tuple(value)
    if len(set(values)) != len(values):
        errors.append(f"{key}_must_not_repeat_ids")
        return None
    if tuple(sorted(values)) != values:
        errors.append(f"{key}_must_be_lexicographically_sorted")
        return None
    return values


def _parse_contract(body: dict[str, Any]) -> tuple[_ParsedContract | None, tuple[str, ...]]:
    errors: list[str] = []
    if set(body) != _REQUIRED_KEYS:
        errors.append("boundary_contract_keys_mismatch")
    if body.get("schema") != SCHEMA:
        errors.append("boundary_contract_schema_mismatch")
    if body.get("report_kind") != REPORT_KIND:
        errors.append("boundary_contract_report_kind_mismatch")
    if body.get("untrusted_llm_role") != "proposal_or_advisory_only":
        errors.append("untrusted_llm_role_mismatch")

    role_lists: dict[str, tuple[str, ...]] = {}
    for key in _STATIC_ROLE_LISTS:
        values = _id_list(body, key, errors)
        if values is not None:
            role_lists[key] = values

    evidence = _id_list(body, "evidence_receipt_ids", errors)
    if evidence is not None:
        if not evidence:
            errors.append("evidence_receipt_ids_must_not_be_empty")
        elif not all(item.startswith("evidence:") for item in evidence):
            errors.append("evidence_receipt_ids_must_use_evidence_prefix")

    parsed_flags: dict[str, bool] = {}
    for key in (
        "bundle_contains_external_sim_engines",
        "external_sim_profiles_are_cb_core",
        "evidence_receipts_are_cb_core_components",
    ):
        value = body.get(key)
        if not isinstance(value, bool):
            errors.append(f"{key}_must_be_boolean")
        else:
            parsed_flags[key] = value

    if errors:
        return None, tuple(sorted(set(errors)))

    policy_violations: list[str] = []
    for key, expected in _STATIC_ROLE_LISTS.items():
        if role_lists[key] != expected:
            policy_violations.append(f"{key}_does_not_match_controller_registry")

    core_ids = frozenset(
        item
        for key in (
            "cb_runtime_ids",
            "cb_formal_gate_ids",
            "cb_minilev_ids",
            "cb_external_adapter_ids",
        )
        for item in role_lists[key]
    )
    sim_ids = frozenset(role_lists["external_sim_profile_ids"])
    parsed_flags["core_contains_external_sim_profile"] = bool(
        core_ids & _EXTERNAL_SIM_PROFILE_SET
    )
    parsed_flags["external_sim_section_contains_cb_component"] = bool(
        sim_ids & _CB_ROLE_IDS
    )
    return (
        _ParsedContract(
            role_lists=role_lists,
            evidence_receipt_ids=evidence or (),
            flags={key: parsed_flags[key] for key in _FLAG_KEYS},
            policy_violations=tuple(sorted(policy_violations)),
        ),
        (),
    )


def _scope_solver_spec(flags: dict[str, bool]) -> dict[str, Any]:
    """Encode the fixed role exclusions for Z3/CVC5/reference agreement."""

    variables = {key: [0, 1] for key in _FLAG_KEYS}
    constraints: list[dict[str, Any]] = []
    for key in _FLAG_KEYS:
        constraints.extend(
            (
                {
                    "op": "eq",
                    "left": {"var": key},
                    "right": {"const": int(flags[key])},
                },
                {
                    "op": "eq",
                    "left": {"var": key},
                    "right": {"const": 0},
                },
            )
        )
    return {"variables": variables, "constraints": constraints}


def _scope_solver_evidence(flags: dict[str, bool]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        result = dual_solve(_scope_solver_spec(flags), max_states=32)
    except Exception as exc:  # fail closed at the independent decider boundary
        return None, f"{type(exc).__name__}:{exc}"
    expected = "BOUNDED_UNSAT" if any(flags.values()) else "BOUNDED_SAT"
    observed = {backend: result.get(backend) for backend in ("z3", "cvc5", "enumeration")}
    if not result.get("agree") or any(value != expected for value in observed.values()):
        return result, "boundary_role_solver_not_in_expected_agreement"
    return result, None


@dataclass(frozen=True)
class BoundaryContractProfile:
    """Gate full CB product/evidence status claims by a fixed role registry."""

    profile_id: str = PROFILE_ID
    claim_ceiling: str = _CLAIM_CEILING

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "boundary_contract_intake_failed",
                {"error": str(exc)},
            )
        parsed, errors = _parse_contract(body)
        if parsed is None:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "boundary_contract_invalid",
                {"errors": list(errors)},
            )

        solver, solver_error = _scope_solver_evidence(parsed.flags)
        if solver_error is not None:
            return ProfileOutcome(
                Disposition.PARKED,
                "boundary_contract_solver_not_eligible",
                {
                    "solver_error": solver_error,
                    "scope_flags": parsed.flags,
                    "scope_solver": solver,
                },
            )

        matrix = controller_role_matrix(
            evidence_receipt_ids=parsed.evidence_receipt_ids
        )
        common = {
            "scope_flags": parsed.flags,
            "scope_solver": solver,
            "controller_role_matrix": matrix,
            "controller_role_matrix_sha256": hashlib.sha256(
                canonical_json(matrix)
            ).hexdigest(),
            "policy_violations": list(parsed.policy_violations),
            "enforcement_limit": (
                "typed role declarations only; arbitrary natural-language prose "
                "must not be treated as a verified scope declaration"
            ),
        }
        if any(parsed.flags.values()):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "boundary_role_conflation",
                {
                    **common,
                    "constraint_feedback": (
                        "Move every sim:* ID to external_sim_profile_ids; keep it "
                        "out of cb:* lists and set all external-membership flags false."
                    ),
                },
            )
        if parsed.policy_violations:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "boundary_contract_registry_mismatch",
                common,
            )
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "boundary_contract_roles_separated",
            common,
        )
