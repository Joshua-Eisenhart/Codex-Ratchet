"""One fixed, receipt-bound external capability for the CB mini-LevOS.

The simulation estate remains outside the ConstraintBox kernel.  This module
lets the controller invoke exactly one external function surface with a fresh
controller-owned challenge, then re-derive the expected result and controls.
Neither a request nor an LLM selects the executable, worker, function,
fixture, tolerance, challenge, transition, or disposition.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .external_engine_packet import (
    CASE_KEYS,
    EXACT_APIS,
    EXTERNAL_BOUNDARY,
    FIXTURE_SHA256,
    INPUT_SCHEMA,
    ROW_SCHEMA,
    WORKER_SHA256,
    ExternalEnginePacketBroker,
    ExternalPacketError,
    _runtime_pin_dict,
    evaluate_worker_output,
)
from .external_runtime_profiles import (
    inspect_external_runtime,
    inspect_python_distributions,
)
from .intake import IntakeError, canonical_json, parse_json_object


CAPABILITY_ID = "pytorch-jacobian-v1"
CAPABILITY_SCHEMA = "constraintbox.external-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-capability-binding.v1"
STEP_ID = "pytorch-jacobian-tool"
CAPABILITY_CLAIM_CEILING = (
    "one fresh controller-challenged torch.func.jacrev CPU float64 operation "
    "with positive, wrong-value, and boundary controls on a controller-selected "
    "compatible runtime; not PyTorch readiness, sim-stack readiness, CR truth, scientific "
    "proof, hostile-code containment, or canonical promotion"
)
TORCH_VERSION_MINIMUM = (2, 11, 0)
TORCH_VERSION_MAXIMUM_EXCLUSIVE = (2, 12, 0)
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_EMPTY_SHA256 = _SHA256(b"").hexdigest()


class ExternalCapabilityError(RuntimeError):
    """The fixed capability could not be constructed, run, or verified."""


@dataclass(frozen=True)
class CapabilityBinding:
    capability_id: str
    run_id: str
    flow_policy_sha256: str
    request_sha256: str
    step_id: str
    challenge_seed_hex: str

    def to_dict(self) -> dict[str, str]:
        return {
            "schema": BINDING_SCHEMA,
            "capability_id": self.capability_id,
            "run_id": self.run_id,
            "flow_policy_sha256": self.flow_policy_sha256,
            "request_sha256": self.request_sha256,
            "step_id": self.step_id,
            "challenge_seed_hex": self.challenge_seed_hex,
        }


TORCH_RUNTIME_REQUIREMENTS = (
    (
        "torch",
        ("torch",),
        TORCH_VERSION_MINIMUM,
        TORCH_VERSION_MAXIMUM_EXCLUSIVE,
    ),
)


def _sha256_file(path: Path) -> str:
    return _SHA256(path.read_bytes()).hexdigest()


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _LOWER_SHA256.fullmatch(value) is not None


def _torch_version_supported(value: object) -> bool:
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:\D.*)?", value)
    if match is None:
        return False
    version = tuple(int(match.group(index)) for index in (1, 2, 3))
    return TORCH_VERSION_MINIMUM <= version < TORCH_VERSION_MAXIMUM_EXCLUSIVE


def validate_capability_binding(binding: CapabilityBinding) -> dict[str, str]:
    if type(binding) is not CapabilityBinding:
        raise ExternalCapabilityError(
            "capability binding must be one frozen CapabilityBinding"
        )
    if binding.capability_id != CAPABILITY_ID:
        raise ExternalCapabilityError("capability binding id mismatch")
    if binding.step_id != STEP_ID:
        raise ExternalCapabilityError("capability binding step mismatch")
    for key, value in (
        ("run_id", binding.run_id),
        ("capability_id", binding.capability_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalCapabilityError(f"capability binding {key} is invalid")
    for key, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
        ("challenge_seed_hex", binding.challenge_seed_hex),
    ):
        if not _valid_sha256(value):
            raise ExternalCapabilityError(f"capability binding {key} is invalid")
    return binding.to_dict()


def capability_binding_from_dict(value: object) -> CapabilityBinding:
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
        "challenge_seed_hex",
    }:
        raise ExternalCapabilityError("capability binding keys mismatch")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalCapabilityError("capability binding schema mismatch")
    try:
        binding = CapabilityBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
            challenge_seed_hex=value["challenge_seed_hex"],
        )
    except (KeyError, TypeError) as exc:
        raise ExternalCapabilityError("capability binding is malformed") from exc
    validate_capability_binding(binding)
    return binding


def _challenge_unit(seed: bytes, index: int) -> float:
    digest = _SHA256(seed + index.to_bytes(2, "big")).digest()
    integer = int.from_bytes(digest[:8], "big")
    return integer / float((1 << 64) - 1)


def derive_pytorch_challenge_case(challenge_seed_hex: str) -> dict[str, Any]:
    """Derive one bounded case from a controller-owned per-run seed."""

    if not _valid_sha256(challenge_seed_hex):
        raise ExternalCapabilityError("challenge seed must be 32 lowercase hex bytes")
    seed = bytes.fromhex(challenge_seed_hex)
    alpha = round(0.35 + 0.55 * _challenge_unit(seed, 0), 12)
    beta = round(-1.50 + 0.50 * _challenge_unit(seed, 1), 12)
    point_x = round(0.50 + 1.50 * _challenge_unit(seed, 2), 12)
    point_y = round(-0.90 + 1.80 * _challenge_unit(seed, 3), 12)
    return {
        "alpha": alpha,
        "beta": beta,
        "point": [point_x, point_y],
        "wrong_jacobian": [[1.0, 0.0], [0.0, 1.0]],
        "boundary_point": [0.0, 0.0],
    }


def _inspect_torch_artifacts() -> dict[str, Any]:
    """Verify distribution ownership/version; hashes are observations only."""

    return inspect_python_distributions(TORCH_RUNTIME_REQUIREMENTS)


def _receipt_body(
    *,
    binding: dict[str, str],
    challenge_case: dict[str, Any],
    fixture_path: Path,
    fixture_sha256: str,
    capability_source_sha256: str,
    packet_controller_source_sha256: str,
    worker_source_sha256: str,
    artifacts_before: dict[str, Any],
    artifacts_after: dict[str, Any],
    row: dict[str, Any] | None,
    status: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "schema": CAPABILITY_SCHEMA,
        "capability_id": CAPABILITY_ID,
        "status": status,
        "reason": reason,
        "external_system": True,
        "kernel_membership": "EXTERNAL_NOT_CB_KERNEL",
        "binding": binding,
        "binding_sha256": _SHA256(canonical_json(binding)).hexdigest(),
        "challenge_case": challenge_case,
        "challenge_case_sha256": _SHA256(
            canonical_json(challenge_case)
        ).hexdigest(),
        "fixture_path": str(fixture_path),
        "fixture_sha256": fixture_sha256,
        "capability_source_sha256": capability_source_sha256,
        "packet_controller_source_sha256": packet_controller_source_sha256,
        "worker_source_sha256": worker_source_sha256,
        "worker_source_sha256_expected": WORKER_SHA256["python"],
        "torch_artifacts_before": artifacts_before,
        "torch_artifacts_after": artifacts_after,
        "row": row,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }


class PytorchJacobianCapabilityBroker:
    """Controller-owned broker for exactly one PyTorch operation."""

    def __init__(
        self,
        packet_broker: ExternalEnginePacketBroker | None = None,
    ) -> None:
        self.packet_broker = packet_broker or ExternalEnginePacketBroker()
        self.source_path = Path(__file__).resolve()

    def run(self, binding: CapabilityBinding) -> dict[str, Any]:
        binding_body = validate_capability_binding(binding)
        try:
            fixture, _canonical_fixture, fixture_sha256 = (
                self.packet_broker._load_fixture()
            )
            capability_source_sha256 = _sha256_file(self.source_path)
            packet_source_sha256 = _sha256_file(
                self.packet_broker.controller_path
            )
            worker_source_sha256 = _sha256_file(
                self.packet_broker.python_worker
            )
        except (OSError, ExternalPacketError) as exc:
            raise ExternalCapabilityError(
                f"capability source or fixture integrity failed: {exc}"
            ) from exc
        if fixture_sha256 != FIXTURE_SHA256:
            raise ExternalCapabilityError("base fixture pin mismatch")
        challenge_case = derive_pytorch_challenge_case(
            binding.challenge_seed_hex
        )
        challenge_fixture = {**fixture, CASE_KEYS["pytorch_jacobian"]: challenge_case}
        artifacts_before = _inspect_torch_artifacts()
        row: dict[str, Any] | None = None
        status = artifacts_before["status"]
        reason = artifacts_before["reason"]
        if status == "PASS":
            row = self.packet_broker._run_row(
                "pytorch_jacobian",
                challenge_fixture,
                fixture_sha256,
                execution_binding=binding_body,
            )
            status = row["status"]
            reason = row["reason"]
        artifacts_after = _inspect_torch_artifacts()
        if artifacts_after != artifacts_before:
            status = "FAIL"
            reason = "torch_artifacts_changed_during_operation"
        elif artifacts_after["status"] != "PASS":
            status = artifacts_after["status"]
            reason = artifacts_after["reason"]
        body = _receipt_body(
            binding=binding_body,
            challenge_case=challenge_case,
            fixture_path=self.packet_broker.fixture_path,
            fixture_sha256=fixture_sha256,
            capability_source_sha256=capability_source_sha256,
            packet_controller_source_sha256=packet_source_sha256,
            worker_source_sha256=worker_source_sha256,
            artifacts_before=artifacts_before,
            artifacts_after=artifacts_after,
            row=row,
            status=status,
            reason=reason,
        )
        receipt = {
            **body,
            "receipt_sha256": _SHA256(canonical_json(body)).hexdigest(),
        }
        errors = validate_pytorch_capability_receipt(
            receipt,
            expected_binding=binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=status == "PASS",
        )
        if errors:
            raise ExternalCapabilityError(
                "capability self-verification failed: " + "; ".join(errors)
            )
        return receipt


def validate_pytorch_capability_receipt(
    receipt: dict[str, Any],
    *,
    expected_binding: CapabilityBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Revalidate one capability receipt against current controller pins."""

    errors: list[str] = []

    def error(path: str, reason: str) -> None:
        errors.append(f"{path}:{reason}")

    def expect(observed: object, expected: object, path: str) -> None:
        if observed != expected:
            error(path, "mismatch")

    def digest(value: object, path: str) -> None:
        if not _valid_sha256(value):
            error(path, "invalid_sha256")

    try:
        body = parse_json_object(canonical_json(receipt))
    except (IntakeError, TypeError, ValueError) as exc:
        return (f"$:noncanonical={exc}",)
    expected_keys = {
        "schema",
        "capability_id",
        "status",
        "reason",
        "external_system",
        "kernel_membership",
        "binding",
        "binding_sha256",
        "challenge_case",
        "challenge_case_sha256",
        "fixture_path",
        "fixture_sha256",
        "capability_source_sha256",
        "packet_controller_source_sha256",
        "worker_source_sha256",
        "worker_source_sha256_expected",
        "torch_artifacts_before",
        "torch_artifacts_after",
        "row",
        "engine_readiness_claim",
        "cr_truth_claim",
        "promotion_allowed",
        "claim_ceiling",
        "receipt_sha256",
    }
    if set(body) != expected_keys:
        return ("$:receipt_keys_mismatch",)
    supplied_digest = body["receipt_sha256"]
    digest(supplied_digest, "$.receipt_sha256")
    expect(supplied_digest, expected_receipt_sha256, "$.receipt_root")
    digest_body = dict(body)
    digest_body.pop("receipt_sha256")
    expect(
        supplied_digest,
        _SHA256(canonical_json(digest_body)).hexdigest(),
        "$.receipt_sha256",
    )
    expect(body["schema"], CAPABILITY_SCHEMA, "$.schema")
    expect(body["capability_id"], CAPABILITY_ID, "$.capability_id")
    expect(body["external_system"], True, "$.external_system")
    expect(
        body["kernel_membership"],
        "EXTERNAL_NOT_CB_KERNEL",
        "$.kernel_membership",
    )
    expect(body["engine_readiness_claim"], False, "$.engine_readiness_claim")
    expect(body["cr_truth_claim"], False, "$.cr_truth_claim")
    expect(body["promotion_allowed"], False, "$.promotion_allowed")
    expect(body["claim_ceiling"], CAPABILITY_CLAIM_CEILING, "$.claim_ceiling")

    expected_binding_body = validate_capability_binding(expected_binding)
    try:
        observed_binding = capability_binding_from_dict(body["binding"])
    except ExternalCapabilityError as exc:
        error("$.binding", str(exc))
        observed_binding = None
    if observed_binding is not None:
        expect(observed_binding, expected_binding, "$.binding")
    expect(
        body["binding_sha256"],
        _SHA256(canonical_json(expected_binding_body)).hexdigest(),
        "$.binding_sha256",
    )

    broker = ExternalEnginePacketBroker()
    try:
        fixture, _canonical_fixture, fixture_sha256 = broker._load_fixture()
        current_capability_source = _sha256_file(Path(__file__).resolve())
        current_packet_source = _sha256_file(broker.controller_path)
        current_worker_source = _sha256_file(broker.python_worker)
    except (OSError, ExternalPacketError) as exc:
        error("$.current_sources", f"unavailable={exc}")
        return tuple(errors)
    expect(body["fixture_path"], str(broker.fixture_path), "$.fixture_path")
    expect(body["fixture_sha256"], fixture_sha256, "$.fixture_sha256")
    expect(body["fixture_sha256"], FIXTURE_SHA256, "$.fixture_pin")
    expect(
        body["capability_source_sha256"],
        current_capability_source,
        "$.capability_source_sha256",
    )
    expect(
        body["packet_controller_source_sha256"],
        current_packet_source,
        "$.packet_controller_source_sha256",
    )
    expect(
        body["worker_source_sha256"],
        current_worker_source,
        "$.worker_source_sha256",
    )
    expect(
        body["worker_source_sha256"],
        WORKER_SHA256["python"],
        "$.worker_source_pin",
    )
    expect(
        body["worker_source_sha256_expected"],
        WORKER_SHA256["python"],
        "$.worker_source_sha256_expected",
    )

    expected_case = derive_pytorch_challenge_case(
        expected_binding.challenge_seed_hex
    )
    expect(body["challenge_case"], expected_case, "$.challenge_case")
    expect(
        body["challenge_case_sha256"],
        _SHA256(canonical_json(expected_case)).hexdigest(),
        "$.challenge_case_sha256",
    )
    current_artifacts = _inspect_torch_artifacts()
    expect(
        body["torch_artifacts_before"],
        body["torch_artifacts_after"],
        "$.torch_artifacts_stability",
    )
    expect(
        body["torch_artifacts_after"],
        current_artifacts,
        "$.torch_artifacts_current",
    )

    status = body["status"]
    if status not in {"PASS", "PARKED", "FAIL"}:
        error("$.status", "invalid")
    if require_pass and status != "PASS":
        error("$.status", "pass_required")
    row = body["row"]
    if status != "PASS":
        if row is not None:
            if not isinstance(row, dict):
                error("$.row", "not_object_or_null")
            elif row.get("status") != status or row.get("reason") != body["reason"]:
                error("$.row", "nonpass_status_mismatch")
        elif body["reason"] != current_artifacts["reason"]:
            error("$.reason", "nonpass_artifact_reason_mismatch")
        return tuple(errors)

    expected_row_keys = {
        "schema",
        "engine_id",
        "external_system",
        "kernel_membership",
        "exact_api",
        "fixture_sha256",
        "input_sha256",
        "controller_sha256",
        "promotion_allowed",
        "engine_readiness_claim",
        "cr_truth_claim",
        "claim_ceiling",
        "runtime_pin",
        "command",
        "execution_binding",
        "worker_source_sha256",
        "worker_source_sha256_expected",
        "executable_path",
        "executable_resolved_path",
        "executable_sha256",
        "executable_sha256_is_policy_input",
        "runtime_version",
        "runtime_implementation",
        "elapsed_seconds",
        "returncode",
        "stdout_sha256",
        "stderr_sha256",
        "output_sha256",
        "worker_pid",
        "status",
        "reason",
        "controls",
        "controller_evaluation",
        "observed",
        "runtime",
    }
    if not isinstance(row, dict) or set(row) != expected_row_keys:
        error("$.row", "pass_row_keys_mismatch")
        return tuple(errors)
    expect(row["schema"], ROW_SCHEMA, "$.row.schema")
    expect(row["engine_id"], "pytorch_jacobian", "$.row.engine_id")
    expect(row["external_system"], True, "$.row.external_system")
    expect(
        row["kernel_membership"],
        "EXTERNAL_NOT_CB_KERNEL",
        "$.row.kernel_membership",
    )
    expect(row["exact_api"], EXACT_APIS["pytorch_jacobian"], "$.row.exact_api")
    expect(row["fixture_sha256"], fixture_sha256, "$.row.fixture_sha256")
    expect(
        row["controller_sha256"],
        current_packet_source,
        "$.row.controller_sha256",
    )
    expect(row["promotion_allowed"], False, "$.row.promotion_allowed")
    expect(
        row["engine_readiness_claim"],
        False,
        "$.row.engine_readiness_claim",
    )
    expect(row["cr_truth_claim"], False, "$.row.cr_truth_claim")
    expect(row["claim_ceiling"], EXTERNAL_BOUNDARY, "$.row.claim_ceiling")
    expect(
        row["runtime_pin"],
        _runtime_pin_dict("python"),
        "$.row.runtime_pin",
    )
    expect(
        row["command"],
        broker._command("pytorch_jacobian")[0],
        "$.row.command",
    )
    expect(
        row["execution_binding"],
        expected_binding_body,
        "$.row.execution_binding",
    )
    expect(
        row["worker_source_sha256"],
        current_worker_source,
        "$.row.worker_source_sha256",
    )
    expect(
        row["worker_source_sha256_expected"],
        WORKER_SHA256["python"],
        "$.row.worker_source_sha256_expected",
    )
    runtime_identity = inspect_external_runtime("python")
    expect(
        row["executable_path"],
        runtime_identity["executable_path"],
        "$.row.executable_path",
    )
    expect(
        row["executable_resolved_path"],
        runtime_identity["executable_resolved_path"],
        "$.row.executable_resolved_path",
    )
    expect(
        row["executable_sha256"],
        runtime_identity["executable_sha256"],
        "$.row.executable_sha256",
    )
    expect(
        row["executable_sha256_is_policy_input"],
        False,
        "$.row.executable_sha256_is_policy_input",
    )
    expect(
        row["runtime_version"],
        runtime_identity["runtime_version"],
        "$.row.runtime_version",
    )
    expect(
        row["runtime_implementation"],
        runtime_identity["runtime_implementation"],
        "$.row.runtime_implementation",
    )
    expect(row["returncode"], 0, "$.row.returncode")
    expect(row["status"], "PASS", "$.row.status")
    expect(row["reason"], "exact_operation_controls_passed", "$.row.reason")
    expect(body["reason"], row["reason"], "$.reason")
    elapsed = row["elapsed_seconds"]
    if isinstance(elapsed, bool) or not isinstance(elapsed, (int, float)) or elapsed < 0:
        error("$.row.elapsed_seconds", "invalid")
    for field in ("input_sha256", "stdout_sha256", "stderr_sha256", "output_sha256"):
        digest(row[field], f"$.row.{field}")
    worker_pid = row["worker_pid"]
    if (
        isinstance(worker_pid, bool)
        or not isinstance(worker_pid, int)
        or worker_pid <= 0
        or worker_pid == os.getpid()
    ):
        error("$.row.worker_pid", "invalid_or_not_separate")
    observed = row["observed"]
    runtime = row["runtime"]
    if not isinstance(observed, dict) or set(observed) != {
        "jacobian",
        "boundary_jacobian",
    }:
        error("$.row.observed", "keys_mismatch")
    if not isinstance(runtime, dict) or set(runtime) != {
        "package_version",
        "dtype",
        "device",
    }:
        error("$.row.runtime", "keys_mismatch")
    if errors:
        return tuple(errors)
    if not _torch_version_supported(runtime["package_version"]):
        error("$.row.runtime.package_version", "unsupported")
    expect(runtime["dtype"], "torch.float64", "$.row.runtime.dtype")
    expect(runtime["device"], "cpu", "$.row.runtime.device")
    challenge_fixture = {**fixture, CASE_KEYS["pytorch_jacobian"]: expected_case}
    transport = {
        "schema": INPUT_SCHEMA,
        "engine_id": "pytorch_jacobian",
        "case": expected_case,
        "execution_binding": expected_binding_body,
    }
    expect(
        row["input_sha256"],
        _SHA256(canonical_json(transport)).hexdigest(),
        "$.row.input_sha256",
    )
    witness = {
        "schema": "constraintbox.external-engine-witness.v1",
        "engine_id": "pytorch_jacobian",
        "exact_api": EXACT_APIS["pytorch_jacobian"],
        "observed": observed,
        "runtime": runtime,
        "pid": worker_pid,
        "execution_binding": expected_binding_body,
    }
    witness_bytes = canonical_json(witness)
    expect(
        row["output_sha256"],
        _SHA256(witness_bytes).hexdigest(),
        "$.row.output_sha256",
    )
    expect(
        row["stdout_sha256"],
        _SHA256(witness_bytes + b"\n").hexdigest(),
        "$.row.stdout_sha256",
    )
    expect(row["stderr_sha256"], _EMPTY_SHA256, "$.row.stderr_sha256")
    evaluation = evaluate_worker_output(
        "pytorch_jacobian",
        challenge_fixture,
        witness,
        expected_execution_binding=expected_binding_body,
    )
    expect(
        row["controller_evaluation"],
        evaluation,
        "$.row.controller_evaluation",
    )
    expect(row["controls"], evaluation["controls"], "$.row.controls")
    controls = row["controls"]
    if (
        not isinstance(controls, dict)
        or set(controls) != {"positive", "targeted_negative", "boundary"}
        or not all(value is True for value in controls.values())
        or evaluation.get("errors")
    ):
        error("$.row.controls", "not_all_required_controls_true")
    return tuple(errors)
