"""Quarantine-only ingress for typed external probe proposals.

This is intentionally not a model dispatcher or a host hook.  An outside
worker may submit one declared header plus a bounded text probe.  The local
gate verifies the current field, parses the text deterministically, runs the
same local coupling check, and returns a quarantine observation.  It cannot
spawn a child, execute arbitrary argv, write SQLite, or decide promotion.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal

import jsonschema
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import basin_field
from .basin_field_gate import FieldGateRequest, verify_ensemble


SUBMISSION_SCHEMA = "constraintbox.probe-submission.v1"
RESULT_SCHEMA = "constraintbox.probe-submission-result.v1"


class ProducerHeader(BaseModel):
    """Declared run provenance; values are data, not trusted execution proof."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str = Field(min_length=1, max_length=128)
    model: str = Field(min_length=1, max_length=256)
    parent_invocation_id: str = Field(min_length=1, max_length=256)
    depth: int = Field(ge=0, le=32)
    spawned_children: int = Field(ge=0, le=10_000)


class MmmHeader(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    mmm_id: str = Field(min_length=1, max_length=256)
    content_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    form: Literal["full", "compact"]


class ProbeSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema: Literal[SUBMISSION_SCHEMA]
    submission_id: str = Field(min_length=1, max_length=256)
    producer: ProducerHeader
    mmm: MmmHeader
    field_gate: FieldGateRequest
    probe_text: str = Field(min_length=1, max_length=4096)


def _result(
    disposition: str,
    reason_codes: list[str],
    *,
    submission: ProbeSubmission | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": RESULT_SCHEMA,
        "profile": "cb_light",
        "disposition": disposition,
        "reason_codes": sorted(set(reason_codes)),
        "submission_id": submission.submission_id if submission else None,
        "declared_producer": submission.producer.model_dump(mode="json") if submission else None,
        "declared_mmm": submission.mmm.model_dump(mode="json") if submission else None,
        "provenance_status": "declared_unverified",
        "quarantine_only": True,
        "detail": detail or {},
        "promotion_allowed": False,
        "claim_ceiling": (
            "quarantined typed local observation only; no child spawn, arbitrary execution, SQLite write, "
            "selection, adoption, host-hook, provider, model, CB Heavy, promotion, or release claim"
        ),
    }


def evaluate_submission(submission: ProbeSubmission) -> dict[str, Any]:
    field_result = verify_ensemble(submission.field_gate)
    if field_result["disposition"] != "FIELD_MAP_READY_LOCAL":
        return _result(
            "HOLD",
            ["HOLD_SUBMISSION_FIELD_MAP_NOT_READY"],
            submission=submission,
            detail={"field_gate": field_result},
        )

    parsed_result = basin_field.parse_probe_dsl(submission.probe_text)
    if parsed_result["status"] == "unavailable":
        return _result(
            "HOLD",
            ["HOLD_SUBMISSION_PARSER_UNAVAILABLE"],
            submission=submission,
            detail={"parser": parsed_result},
        )
    if parsed_result["status"] == "refused":
        if parsed_result.get("reference") is None:
            return _result(
                "REFUSE",
                ["REFUSE_SUBMISSION_GRAMMAR"],
                submission=submission,
                detail={"parser": parsed_result},
            )
        return _result(
            "HOLD",
            ["HOLD_SUBMISSION_PARSER_REFERENCE_DISAGREEMENT"],
            submission=submission,
            detail={"parser": parsed_result},
        )

    parsed = parsed_result["parsed"]
    if parsed != parsed_result["reference"] or not parsed_result["replay_equal"]:
        return _result(
            "HOLD",
            ["HOLD_SUBMISSION_PARSER_REPLAY_OR_REFERENCE_DRIFT"],
            submission=submission,
            detail={"parser": parsed_result},
        )
    schema_errors = tuple(
        sorted(
            error.message
            for error in jsonschema.Draft202012Validator(basin_field.ParsedProbeDsl.model_json_schema()).iter_errors(parsed)
        )
    )
    try:
        typed = basin_field.ParsedProbeDsl.model_validate(parsed)
        pydantic_error = None
    except ValidationError as exc:
        typed = None
        pydantic_error = exc.errors(include_url=False)
    if (typed is not None) != (not schema_errors):
        return _result(
            "HOLD",
            ["HOLD_SUBMISSION_TYPED_SCHEMA_DISAGREEMENT"],
            submission=submission,
            detail={"parsed": parsed, "pydantic_error": pydantic_error, "jsonschema_errors": schema_errors},
        )
    if typed is None:
        return _result(
            "REFUSE",
            ["REFUSE_SUBMISSION_TYPED_BOUNDARY"],
            submission=submission,
            detail={"parsed": parsed, "pydantic_error": pydantic_error, "jsonschema_errors": schema_errors},
        )

    local = basin_field._coupling_probe(
        basin_field.ProbePoint(
            family="coupling",
            round_index=0,
            index=0,
            coordinates={
                "payload_mode": "valid",
                "degree": typed.degree,
                "limit": typed.limit,
                "coefficient": typed.budget - 1,
                "events": ("start", "finish"),
                "mutation": "baseline",
                "branch": 0,
                "variant": "submission",
            },
        )
    )
    detail = {
        "typed_probe": typed.model_dump(mode="json"),
        "local_coupling_outcome": local.outcome,
        "local_coupling_reasons": local.reason_codes,
        "field_gate": field_result,
    }
    if local.outcome == "ACCEPT":
        return _result(
            "QUARANTINED_TYPED_PROBE",
            ["SUBMISSION_FIELD_AND_LOCAL_CONSTRAINTS_SAT"],
            submission=submission,
            detail=detail,
        )
    if local.outcome == "REFUSE":
        return _result(
            "REFUSE",
            ["REFUSE_SUBMISSION_LOCAL_CONSTRAINT"],
            submission=submission,
            detail=detail,
        )
    return _result(
        "HOLD",
        ["HOLD_SUBMISSION_LOCAL_CONSTRAINT_UNCERTAIN"],
        submission=submission,
        detail=detail,
    )


def evaluate_submission_file(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _result(
            "REFUSE",
            ["REFUSE_SUBMISSION_INVALID_JSON"],
            detail={"path": str(path), "exception_type": type(exc).__name__},
        )
    try:
        submission = ProbeSubmission.model_validate(payload)
    except ValidationError as exc:
        return _result(
            "REFUSE",
            ["REFUSE_SUBMISSION_SCHEMA"],
            detail={"errors": exc.errors(include_url=False)},
        )
    return evaluate_submission(submission)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Quarantine one typed external probe proposal.")
    parser.add_argument("--submission", type=Path, required=True)
    args = parser.parse_args(argv)
    result = evaluate_submission_file(args.submission)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["disposition"] == "QUARANTINED_TYPED_PROBE" else 2


if __name__ == "__main__":  # pragma: no cover - exercised through module invocation.
    raise SystemExit(main())
