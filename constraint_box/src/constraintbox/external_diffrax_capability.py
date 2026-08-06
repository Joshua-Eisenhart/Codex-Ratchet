"""One fixed Diffrax Tsit5 capability outside the CB kernel."""

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


CAPABILITY_ID = "diffrax-tsit5-affine-flow-v1"
STEP_ID = "diffrax-tsit5-tool"
DIFFRAX_RUNTIME_REQUIREMENTS = (
    ("diffrax", ("diffrax",), (0, 7, 0), (0, 8, 0)),
    ("jax", ("jax",), (0, 10, 0), (0, 11, 0)),
    ("jaxlib", ("jaxlib",), (0, 10, 0), (0, 11, 0)),
)
CAPABILITY_CLAIM_CEILING = (
    "one fresh controller-challenged diffrax.ODETerm + diffrax.Tsit5 + "
    "diffrax.PIDController + diffrax.diffeqsolve affine-flow operation with "
    "positive, wrong-value, boundary, replay, and operation-severance controls "
    "on the controller-selected compatible CPU runtime; not Diffrax readiness, JAX readiness, "
    "sim-stack readiness, CR truth, scientific proof, hostile-code containment, "
    "or canonical promotion"
)

DIFFRAX_TSIT5_PROFILE = BoundedNumericsProfile(
    capability_id=CAPABILITY_ID,
    step_id=STEP_ID,
    worker_selector="diffrax_tsit5_affine",
    exact_api=(
        "diffrax.ODETerm",
        "diffrax.Tsit5",
        "diffrax.PIDController",
        "diffrax.diffeqsolve",
    ),
    python_distribution_requirements=DIFFRAX_RUNTIME_REQUIREMENTS,
    profile_source_path=Path(__file__).resolve(),
    claim_ceiling=CAPABILITY_CLAIM_CEILING,
)


def derive_diffrax_tsit5_challenge_case(challenge_seed_hex: str) -> dict[str, float]:
    return derive_bounded_numerics_case(DIFFRAX_TSIT5_PROFILE, challenge_seed_hex)


def validate_diffrax_tsit5_binding(
    binding: BoundedNumericsBinding,
) -> dict[str, str]:
    return validate_bounded_numerics_binding(DIFFRAX_TSIT5_PROFILE, binding)


def run_diffrax_tsit5_capability(
    binding: BoundedNumericsBinding,
) -> dict[str, object]:
    return BoundedNumericsCapabilityBroker(DIFFRAX_TSIT5_PROFILE).run(binding)


def validate_diffrax_tsit5_receipt(
    receipt: dict[str, object],
    *,
    expected_binding: BoundedNumericsBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    return validate_bounded_numerics_receipt(
        DIFFRAX_TSIT5_PROFILE,
        receipt,
        expected_binding=expected_binding,
        expected_receipt_sha256=expected_receipt_sha256,
        require_pass=require_pass,
    )
