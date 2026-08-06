"""Independent, fixed receipt replay for every external capability profile.

The generic Mini-LevOS replay proves the controller state transition.  It does
not by itself re-evaluate an external capability's typed receipt.  This module
is the second deterministic layer: the capability ID selects one source-owned
parser and validator below; no receipt, request, or caller can select either.

The replay never invokes an engine operation.  It checks a retained receipt
against the current controller/source/runtime pins and its original binding.
It is therefore suitable for the ConstraintBox suite and non-executing repair
planner, while keeping the simulation estate outside the CB kernel.
"""

from __future__ import annotations

from typing import Any, Callable


class CapabilityReceiptReplayError(ValueError):
    """A retained external-capability receipt did not independently replay."""


ReceiptValidator = Callable[[dict[str, Any], bool], tuple[str, ...]]


def _binding(receipt: dict[str, Any]) -> object:
    binding = receipt.get("binding")
    if not isinstance(binding, dict):
        raise CapabilityReceiptReplayError("capability receipt binding is missing")
    return binding


def _expected_digest(receipt: dict[str, Any], expected_receipt_sha256: str) -> str:
    supplied = receipt.get("receipt_sha256")
    if supplied != expected_receipt_sha256:
        raise CapabilityReceiptReplayError("capability receipt digest differs from result")
    return expected_receipt_sha256


def _pytorch(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_capability import (
        capability_binding_from_dict,
        validate_pytorch_capability_receipt,
    )

    binding = capability_binding_from_dict(_binding(receipt))
    return validate_pytorch_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _jax(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_jax_capability import (
        jax_capability_binding_from_dict,
        validate_jax_capability_receipt,
    )

    binding = jax_capability_binding_from_dict(_binding(receipt))
    return validate_jax_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _pysindy(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_pysindy_capability import (
        capability_binding_from_dict,
        validate_pysindy_capability_receipt,
    )

    binding = capability_binding_from_dict(_binding(receipt))
    return validate_pysindy_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _julia(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_julia_capability import (
        julia_capability_binding_from_dict,
        validate_julia_capability_receipt,
    )

    binding = julia_capability_binding_from_dict(_binding(receipt))
    return validate_julia_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _scipy(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_bounded_numerics import bounded_numerics_binding_from_dict
    from .external_scipy_capability import (
        SCIPY_EXPM_PROFILE,
        validate_scipy_expm_receipt,
    )

    binding = bounded_numerics_binding_from_dict(SCIPY_EXPM_PROFILE, _binding(receipt))
    return validate_scipy_expm_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _diffrax(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_bounded_numerics import bounded_numerics_binding_from_dict
    from .external_diffrax_capability import (
        DIFFRAX_TSIT5_PROFILE,
        validate_diffrax_tsit5_receipt,
    )

    binding = bounded_numerics_binding_from_dict(
        DIFFRAX_TSIT5_PROFILE, _binding(receipt)
    )
    return validate_diffrax_tsit5_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _graph_topology(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_graph_topology_capability import (
        graph_topology_binding_from_dict,
        validate_graph_topology_receipt,
    )

    binding = graph_topology_binding_from_dict(_binding(receipt))
    return validate_graph_topology_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _s3(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_s3_capability import (
        PYDMD_PROFILE,
        PYMDP_PROFILE,
        s3_capability_binding_from_dict,
        validate_s3_capability_receipt,
    )

    profiles = {
        "pydmd-discrete-rate-v1": PYDMD_PROFILE,
        "pymdp-two-state-inference-v1": PYMDP_PROFILE,
    }
    profile = profiles.get(receipt.get("capability_id"))
    if profile is None:
        raise CapabilityReceiptReplayError("S3 capability profile is not registered")
    binding = s3_capability_binding_from_dict(profile, _binding(receipt))
    return validate_s3_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _pykoopman(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_pykoopman_capability import (
        capability_binding_from_dict,
        validate_pykoopman_capability_receipt,
    )

    binding = capability_binding_from_dict(_binding(receipt))
    return validate_pykoopman_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _quimb_cotengra(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_quimb_cotengra_capability import (
        capability_binding_from_dict,
        validate_quimb_cotengra_capability_receipt,
    )

    binding = capability_binding_from_dict(_binding(receipt))
    return validate_quimb_cotengra_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _multiengine(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_multiengine_capability import (
        multiengine_binding_from_dict,
        validate_multiengine_capability_receipt,
    )

    binding = multiengine_binding_from_dict(_binding(receipt))
    return validate_multiengine_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _packet_integration(
    receipt: dict[str, Any], require_pass: bool
) -> tuple[str, ...]:
    from .external_packet_integration_capability import (
        packet_integration_binding_from_dict,
        validate_packet_integration_capability_receipt,
    )

    binding = packet_integration_binding_from_dict(_binding(receipt))
    return validate_packet_integration_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


def _e3nn(receipt: dict[str, Any], require_pass: bool) -> tuple[str, ...]:
    from .external_e3nn_capability import (
        e3nn_capability_binding_from_dict,
        validate_e3nn_capability_receipt,
    )

    binding = e3nn_capability_binding_from_dict(_binding(receipt))
    return validate_e3nn_capability_receipt(
        receipt,
        expected_binding=binding,
        expected_receipt_sha256=_expected_digest(receipt, receipt["receipt_sha256"]),
        require_pass=require_pass,
    )


_VALIDATORS: dict[str, ReceiptValidator] = {
    "pytorch-jacobian-v1": _pytorch,
    "jax-autodiff-v1": _jax,
    "pysindy-affine-generator-v1": _pysindy,
    "julia-diffeq-v1": _julia,
    "scipy-expm-rotation-v1": _scipy,
    "diffrax-tsit5-affine-flow-v1": _diffrax,
    "graph-topology-crosscheck-v1": _graph_topology,
    "pydmd-discrete-rate-v1": _s3,
    "pymdp-two-state-inference-v1": _s3,
    "pykoopman-identity-edmd-v1": _pykoopman,
    "quimb-cotengra-bounded-suite-v1": _quimb_cotengra,
    "multiengine-dlpack-diffeq-v1": _multiengine,
    "basic-packet-cross-engine-v1": _packet_integration,
    "e3nn-wigner-crosscheck-v1": _e3nn,
}


def verify_external_capability_receipt(
    *,
    capability_id: str,
    receipt: dict[str, Any],
    expected_receipt_sha256: str,
    require_pass: bool,
) -> None:
    """Run the fixed receipt validator selected only by capability ID."""

    validator = _VALIDATORS.get(capability_id)
    if validator is None:
        raise CapabilityReceiptReplayError("capability receipt validator is not registered")
    if not isinstance(receipt, dict):
        raise CapabilityReceiptReplayError("capability receipt must be an object")
    if receipt.get("receipt_sha256") != expected_receipt_sha256:
        raise CapabilityReceiptReplayError("capability receipt digest differs from result")
    try:
        errors = validator(receipt, require_pass)
    except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        raise CapabilityReceiptReplayError(
            f"capability receipt validator could not replay: {exc}"
        ) from exc
    if not isinstance(errors, tuple) or any(not isinstance(error, str) for error in errors):
        raise CapabilityReceiptReplayError("capability receipt validator returned invalid errors")
    if errors:
        raise CapabilityReceiptReplayError(
            "capability receipt validation failed: " + "; ".join(errors[:8])
        )
