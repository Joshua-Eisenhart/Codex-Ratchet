"""One fixed SciPy ``linalg.expm`` capability outside the CB kernel."""

from __future__ import annotations

from pathlib import Path

from .external_bounded_numerics import (
    BoundedNumericsBinding,
    BoundedNumericsCapabilityBroker,
    BoundedNumericsProfile,
    derive_bounded_numerics_case,
    validate_bounded_numerics_binding,
    validate_bounded_numerics_receipt,
)


CAPABILITY_ID = "scipy-expm-rotation-v1"
STEP_ID = "scipy-expm-tool"
SCIPY_RUNTIME_REQUIREMENTS = (
    ("scipy", ("scipy",), (1, 17, 0), (1, 18, 0)),
)
CAPABILITY_CLAIM_CEILING = (
    "one fresh controller-challenged scipy.linalg.expm rotation operation with "
    "positive, wrong-value, boundary, replay, and operation-severance controls "
    "on the controller-selected compatible CPU runtime; not SciPy readiness, sim-stack "
    "readiness, CR truth, scientific proof, hostile-code containment, or "
    "canonical promotion"
)

SCIPY_EXPM_PROFILE = BoundedNumericsProfile(
    capability_id=CAPABILITY_ID,
    step_id=STEP_ID,
    worker_selector="scipy_expm_rotation",
    exact_api=("scipy.linalg.expm",),
    python_distribution_requirements=SCIPY_RUNTIME_REQUIREMENTS,
    profile_source_path=Path(__file__).resolve(),
    claim_ceiling=CAPABILITY_CLAIM_CEILING,
)


def derive_scipy_expm_challenge_case(challenge_seed_hex: str) -> dict[str, float]:
    return derive_bounded_numerics_case(SCIPY_EXPM_PROFILE, challenge_seed_hex)


def validate_scipy_expm_binding(binding: BoundedNumericsBinding) -> dict[str, str]:
    return validate_bounded_numerics_binding(SCIPY_EXPM_PROFILE, binding)


def run_scipy_expm_capability(binding: BoundedNumericsBinding) -> dict[str, object]:
    return BoundedNumericsCapabilityBroker(SCIPY_EXPM_PROFILE).run(binding)


def run_scipy_expm_replay_severance_rehearsal(
    binding: BoundedNumericsBinding,
) -> dict[str, object]:
    """Run the one controller-owned SciPy replay-severance rehearsal.

    This is not a caller-selectable capability option.  The dedicated
    rehearsal orchestrator is the only supported caller and records the
    deliberate injection beside the resulting external receipt.  The normal
    SciPy capability above never receives this selector.
    """

    return BoundedNumericsCapabilityBroker(
        SCIPY_EXPM_PROFILE,
        controller_replay_poisoned_operation=SCIPY_EXPM_PROFILE.exact_api[-1],
    ).run(binding)


def validate_scipy_expm_receipt(
    receipt: dict[str, object],
    *,
    expected_binding: BoundedNumericsBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    return validate_bounded_numerics_receipt(
        SCIPY_EXPM_PROFILE,
        receipt,
        expected_binding=expected_binding,
        expected_receipt_sha256=expected_receipt_sha256,
        require_pass=require_pass,
    )
