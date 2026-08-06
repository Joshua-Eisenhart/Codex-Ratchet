"""External-only wrapper for the fixed legacy cross-engine packet.

The underlying packet broker is the sole executor of the JAX, PyTorch,
PySINDy, and Julia workloads and of the PySINDy-to-Julia JSON handoff.  This
module adds a narrow, source-bound capability receipt around that broker so a
two-node Mini-LevOS flow can bind the observation to one controller run.  It
does not add a ConstraintBox kernel capability, engine-readiness result,
release path, promotion path, or scientific bridge claim.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import external_engine_packet as packet_module
from .external_engine_packet import (
    EXTERNAL_BOUNDARY,
    PACKET_SCHEMA,
    ExternalEnginePacketBroker,
    validate_pass_receipt,
)
from .intake import canonical_json


CAPABILITY_ID = "basic-packet-cross-engine-v1"
STEP_ID = "basic-packet-cross-engine-tool"
CAPABILITY_SCHEMA = "constraintbox.external-packet-integration-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-packet-integration-binding.v1"
CAPABILITY_CLAIM_CEILING = (
    "one local execution of the legacy fixed-fixture external packet through "
    "a two-node controller-owned Mini-LevOS observation/gate flow; its "
    "PySINDy-to-Julia JSON handoff is a legacy diagnostic, not a scientific "
    "DLPack bridge, engine readiness result, full sim-stack result, CR truth, "
    "scientific proof, release, or canonical promotion"
)

_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_HEX = re.compile(r"[0-9a-f]{64}")
_ARTIFACT_NAMES = (
    "capability_source",
    "packet_controller",
    "packet_fixture",
    "python_worker",
    "julia_worker",
    "julia_project",
)


class ExternalPacketIntegrationCapabilityError(ValueError):
    """The fixed external packet cannot be represented as a capability receipt."""


@dataclass(frozen=True)
class PacketIntegrationBinding:
    """Controller-owned identity material for one fixed-fixture packet run."""

    capability_id: str
    run_id: str
    flow_policy_sha256: str
    request_sha256: str
    step_id: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": BINDING_SCHEMA,
            "capability_id": self.capability_id,
            "run_id": self.run_id,
            "flow_policy_sha256": self.flow_policy_sha256,
            "request_sha256": self.request_sha256,
            "step_id": self.step_id,
        }


def _sha256_file(path: Path) -> str:
    return _SHA256(path.read_bytes()).hexdigest()


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _HEX.fullmatch(value) is not None


def validate_packet_integration_binding(binding: PacketIntegrationBinding) -> dict[str, str]:
    """Refuse caller-selected identity material before the broker can run."""

    if type(binding) is not PacketIntegrationBinding:
        raise ExternalPacketIntegrationCapabilityError(
            "packet integration binding must be frozen"
        )
    if binding.capability_id != CAPABILITY_ID:
        raise ExternalPacketIntegrationCapabilityError(
            "packet integration binding capability id mismatch"
        )
    if binding.step_id != STEP_ID:
        raise ExternalPacketIntegrationCapabilityError(
            "packet integration binding step id mismatch"
        )
    for key, value in (
        ("run_id", binding.run_id),
        ("capability_id", binding.capability_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalPacketIntegrationCapabilityError(
                f"packet integration binding {key} is invalid"
            )
    for key, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
    ):
        if not _valid_sha256(value):
            raise ExternalPacketIntegrationCapabilityError(
                f"packet integration binding {key} is invalid"
            )
    return binding.to_dict()


def packet_integration_binding_from_dict(value: object) -> PacketIntegrationBinding:
    """Parse only the controller-owned binding representation."""

    expected = {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise ExternalPacketIntegrationCapabilityError(
            "packet integration binding keys mismatch"
        )
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalPacketIntegrationCapabilityError(
            "packet integration binding schema mismatch"
        )
    try:
        binding = PacketIntegrationBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
        )
    except (KeyError, TypeError) as exc:
        raise ExternalPacketIntegrationCapabilityError(
            "packet integration binding is malformed"
        ) from exc
    validate_packet_integration_binding(binding)
    return binding


def _artifact(path: Path) -> dict[str, str]:
    resolved = path.resolve(strict=True)
    return {"path": str(resolved), "sha256": _sha256_file(resolved)}


def immutable_artifacts_for(
    broker: ExternalEnginePacketBroker,
) -> dict[str, dict[str, str]]:
    """Capture the exact local files the fixed packet is permitted to use."""

    source = Path(__file__).resolve()
    project = broker.julia_project / "Project.toml"
    return {
        "capability_source": _artifact(source),
        "packet_controller": _artifact(Path(packet_module.__file__).resolve()),
        "packet_fixture": _artifact(broker.fixture_path),
        "python_worker": _artifact(broker.python_worker),
        "julia_worker": _artifact(broker.julia_worker),
        "julia_project": _artifact(project),
    }


def _receipt_root(receipt: dict[str, Any]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    return _SHA256(canonical_json(body)).hexdigest()


def _packet_status(packet: object) -> str:
    if not isinstance(packet, dict):
        return "FAIL"
    state = packet.get("status")
    return state if state in {"PASS", "PARKED", "FAIL"} else "FAIL"


class PacketIntegrationCapabilityBroker:
    """Run the existing packet broker and bind its result without widening it."""

    def run(self, binding: PacketIntegrationBinding) -> dict[str, Any]:
        validate_packet_integration_binding(binding)
        broker = ExternalEnginePacketBroker()
        artifacts = immutable_artifacts_for(broker)
        packet = broker.run()
        state = _packet_status(packet)
        packet_errors: tuple[str, ...] = ()
        if state == "PASS" and isinstance(packet, dict):
            packet_errors = validate_pass_receipt(packet)

        if state == "PASS" and not packet_errors:
            status = "PASS"
            reason = "legacy_packet_pass_receipt_validated"
        elif state == "PARKED":
            status = "PARKED"
            reason = "legacy_packet_parked"
        elif state == "PASS":
            status = "FAIL"
            reason = "legacy_packet_pass_receipt_validation_failed"
        else:
            status = "FAIL"
            reason = "legacy_packet_failed"

        packet_digest = _SHA256(canonical_json(packet)).hexdigest()
        receipt: dict[str, Any] = {
            "schema": CAPABILITY_SCHEMA,
            "status": status,
            "reason": reason,
            "binding": binding.to_dict(),
            "binding_sha256": _SHA256(canonical_json(binding.to_dict())).hexdigest(),
            "immutable_artifacts": artifacts,
            "packet_receipt": packet,
            "packet_receipt_sha256": packet_digest,
            "external_system": True,
            "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
            "release_allowed": False,
            "engine_readiness_claim": False,
            "cr_truth_claim": False,
            "promotion_allowed": False,
            "claim_ceiling": CAPABILITY_CLAIM_CEILING,
        }
        receipt["receipt_sha256"] = _receipt_root(receipt)
        return receipt


def validate_packet_integration_capability_receipt(
    receipt: object,
    *,
    expected_binding: PacketIntegrationBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Strictly verify the wrapper and its embedded legacy PASS packet.

    A PASS wrapper is valid only when :func:`validate_pass_receipt` accepts the
    embedded packet against the current source, fixture, runtime, and artifact
    pins.  PARKED/FAIL are retained solely as non-promotable observations.
    """

    errors: list[str] = []

    def error(path: str, reason: str) -> None:
        errors.append(f"{path}:{reason}")

    expected_keys = {
        "schema",
        "status",
        "reason",
        "binding",
        "binding_sha256",
        "immutable_artifacts",
        "packet_receipt",
        "packet_receipt_sha256",
        "external_system",
        "kernel_membership",
        "release_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
        "receipt_sha256",
    }
    if not isinstance(receipt, dict):
        return ("$:not_object",)
    if set(receipt) != expected_keys:
        return ("$:keys_mismatch",)
    if receipt.get("schema") != CAPABILITY_SCHEMA:
        error("$.schema", "mismatch")
    status = receipt.get("status")
    if status not in {"PASS", "PARKED", "FAIL"}:
        error("$.status", "invalid")
    if require_pass and status != "PASS":
        error("$.status", "pass_required")
    if not isinstance(receipt.get("reason"), str) or not receipt["reason"]:
        error("$.reason", "invalid")
    if receipt.get("binding_sha256") != _SHA256(
        canonical_json(receipt.get("binding"))
    ).hexdigest():
        error("$.binding_sha256", "mismatch")
    try:
        actual_binding = packet_integration_binding_from_dict(receipt.get("binding"))
    except ExternalPacketIntegrationCapabilityError as exc:
        error("$.binding", str(exc))
    else:
        if actual_binding != expected_binding:
            error("$.binding", "differs_from_expected")

    for key, expected in {
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "release_allowed": False,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }.items():
        if receipt.get(key) != expected:
            error(f"$.{key}", "mismatch")

    artifacts = receipt.get("immutable_artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(_ARTIFACT_NAMES):
        error("$.immutable_artifacts", "keys_mismatch")
    else:
        try:
            expected_artifacts = immutable_artifacts_for(ExternalEnginePacketBroker())
        except OSError as exc:
            error("$.immutable_artifacts", f"unavailable:{exc}")
        else:
            if artifacts != expected_artifacts:
                error("$.immutable_artifacts", "source_or_artifact_drift")

    packet = receipt.get("packet_receipt")
    if not isinstance(packet, dict) or packet.get("schema") != PACKET_SCHEMA:
        error("$.packet_receipt", "malformed")
    else:
        observed_packet_sha256 = _SHA256(canonical_json(packet)).hexdigest()
        if receipt.get("packet_receipt_sha256") != observed_packet_sha256:
            error("$.packet_receipt_sha256", "mismatch")
        state = _packet_status(packet)
        expected_status = {
            "PASS": "PASS",
            "PARKED": "PARKED",
            "FAIL": "FAIL",
        }[state]
        if status != expected_status:
            error("$.status", "does_not_match_packet")
        if status == "PASS":
            for packet_error in validate_pass_receipt(packet):
                error("$.packet_receipt", packet_error)

    if not _valid_sha256(expected_receipt_sha256):
        error("$.expected_receipt_sha256", "invalid")
    if receipt.get("receipt_sha256") != _receipt_root(receipt):
        error("$.receipt_sha256", "mismatch")
    if receipt.get("receipt_sha256") != expected_receipt_sha256:
        error("$.receipt_sha256", "differs_from_expected")
    return tuple(errors)
