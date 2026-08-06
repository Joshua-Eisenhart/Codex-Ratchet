"""Public fixed PyDMD capability surface; implementation remains external."""

from __future__ import annotations

from typing import Any

from .external_s3_capability import (
    BINDING_SCHEMA,
    CAPABILITY_SCHEMA,
    CONTROL_TOLERANCE,
    PYDMD_PROFILE,
    ROW_SCHEMA,
    S3CapabilityBinding,
    ExternalS3CapabilityError,
    PyDMDCapabilityBroker,
    derive_pydmd_challenge_case,
    evaluate_s3_output,
    s3_capability_binding_from_dict,
    validate_s3_capability_binding,
    validate_s3_capability_receipt,
)
from .external_runtime_profiles import runtime_profile_dict


CAPABILITY_ID = PYDMD_PROFILE.capability_id
STEP_ID = PYDMD_PROFILE.step_id
FLOW_ID = PYDMD_PROFILE.flow_id
EXACT_APIS = PYDMD_PROFILE.exact_apis
CAPABILITY_CLAIM_CEILING = PYDMD_PROFILE.claim_ceiling
RUNTIME_POLICY = runtime_profile_dict("python")
PyDMDCapabilityBinding = S3CapabilityBinding
ExternalPyDMDCapabilityError = ExternalS3CapabilityError


def validate_pydmd_capability_binding(binding: S3CapabilityBinding) -> dict[str, str]:
    return validate_s3_capability_binding(PYDMD_PROFILE, binding)


def pydmd_capability_binding_from_dict(value: object) -> S3CapabilityBinding:
    return s3_capability_binding_from_dict(PYDMD_PROFILE, value)


def evaluate_pydmd_output(
    challenge_case: dict[str, Any], observed: object
) -> dict[str, Any]:
    return evaluate_s3_output(PYDMD_PROFILE, challenge_case, observed)


def validate_pydmd_capability_receipt(
    receipt: dict[str, Any],
    *,
    expected_binding: S3CapabilityBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    return validate_s3_capability_receipt(
        receipt,
        expected_binding=expected_binding,
        expected_receipt_sha256=expected_receipt_sha256,
        require_pass=require_pass,
    )
