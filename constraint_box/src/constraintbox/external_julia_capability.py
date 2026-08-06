"""One fixed, receipt-bound Julia DifferentialEquations capability for CB.

The Julia workload remains outside the ConstraintBox kernel.  The controller
selects one fresh bounded ODE challenge, invokes the source-pinned Julia
worker in a separate strict-carrier process, and independently recomputes the
positive, targeted-negative, boundary, and carrier controls.  This module
does not make Julia, sim-stack, release, promotion, CR-truth, or scientific
claims.
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
from .external_runtime_profiles import inspect_external_runtime
from .intake import IntakeError, canonical_json, parse_json_object


CAPABILITY_ID = "julia-diffeq-v1"
CAPABILITY_SCHEMA = "constraintbox.external-julia-capability-receipt.v1"
BINDING_SCHEMA = "constraintbox.external-julia-capability-binding.v1"
STEP_ID = "julia-diffeq-tool"
JULIA_CARRIER_PROJECT_SHA256 = (
    "ab88d198bef1e9b1c0ca2bc065e97f71a62598cc4f8111c80e58fa689e8fbd03"
)
JULIA_VERSION_PIN = "1.12.6"
DIFFERENTIALEQUATIONS_VERSION_PIN = "8.0.2"
STRICT_LOAD_PATH = ["@", "@stdlib"]
CAPABILITY_CLAIM_CEILING = (
    "one fresh controller-challenged DifferentialEquations.ODEProblem, "
    "DifferentialEquations.solve, and DifferentialEquations.Tsit5 ODE "
    "operation with positive, wrong-rate, boundary, strict-carrier, and "
    "separate-process controls on the canonical local Julia carrier; not "
    "Julia readiness, sim-stack readiness, release, CR truth, scientific "
    "proof, hostile-code containment, or canonical promotion"
)
_SHA256 = hashlib.sha256
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_LOWER_SHA256 = re.compile(r"[0-9a-f]{64}")
_EMPTY_SHA256 = _SHA256(b"").hexdigest()


class ExternalJuliaCapabilityError(RuntimeError):
    """The fixed Julia capability could not be constructed, run, or checked."""


@dataclass(frozen=True)
class JuliaCapabilityBinding:
    """Controller-owned identity for one bounded Julia capability run."""

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


def _sha256_file(path: Path) -> str:
    return _SHA256(path.read_bytes()).hexdigest()


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _LOWER_SHA256.fullmatch(value) is not None


def validate_julia_capability_binding(
    binding: JuliaCapabilityBinding,
) -> dict[str, str]:
    """Reject caller-chosen IDs, flow identities, or challenge material."""

    if type(binding) is not JuliaCapabilityBinding:
        raise ExternalJuliaCapabilityError(
            "capability binding must be one frozen JuliaCapabilityBinding"
        )
    if binding.capability_id != CAPABILITY_ID:
        raise ExternalJuliaCapabilityError("capability binding id mismatch")
    if binding.step_id != STEP_ID:
        raise ExternalJuliaCapabilityError("capability binding step mismatch")
    for key, value in (
        ("run_id", binding.run_id),
        ("capability_id", binding.capability_id),
        ("step_id", binding.step_id),
    ):
        if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
            raise ExternalJuliaCapabilityError(
                f"capability binding {key} is invalid"
            )
    for key, value in (
        ("flow_policy_sha256", binding.flow_policy_sha256),
        ("request_sha256", binding.request_sha256),
        ("challenge_seed_hex", binding.challenge_seed_hex),
    ):
        if not _valid_sha256(value):
            raise ExternalJuliaCapabilityError(
                f"capability binding {key} is invalid"
            )
    return binding.to_dict()


def julia_capability_binding_from_dict(value: object) -> JuliaCapabilityBinding:
    """Parse only the canonical controller-owned Julia binding shape."""

    if not isinstance(value, dict) or set(value) != {
        "schema",
        "capability_id",
        "run_id",
        "flow_policy_sha256",
        "request_sha256",
        "step_id",
        "challenge_seed_hex",
    }:
        raise ExternalJuliaCapabilityError("capability binding keys mismatch")
    if value.get("schema") != BINDING_SCHEMA:
        raise ExternalJuliaCapabilityError("capability binding schema mismatch")
    try:
        binding = JuliaCapabilityBinding(
            capability_id=value["capability_id"],
            run_id=value["run_id"],
            flow_policy_sha256=value["flow_policy_sha256"],
            request_sha256=value["request_sha256"],
            step_id=value["step_id"],
            challenge_seed_hex=value["challenge_seed_hex"],
        )
    except (KeyError, TypeError) as exc:
        raise ExternalJuliaCapabilityError(
            "capability binding is malformed"
        ) from exc
    validate_julia_capability_binding(binding)
    return binding


def _challenge_unit(seed: bytes, index: int) -> float:
    digest = _SHA256(seed + index.to_bytes(2, "big")).digest()
    integer = int.from_bytes(digest[:8], "big")
    return integer / float((1 << 64) - 1)


def derive_julia_challenge_case(challenge_seed_hex: str) -> dict[str, float]:
    """Derive one finite ODE case; no request may supply these values."""

    if not _valid_sha256(challenge_seed_hex):
        raise ExternalJuliaCapabilityError(
            "challenge seed must be 32 lowercase hex bytes"
        )
    seed = bytes.fromhex(challenge_seed_hex)
    rate = round(-0.95 + 0.45 * _challenge_unit(seed, 0), 12)
    initial = round(0.55 + 1.45 * _challenge_unit(seed, 1), 12)
    duration = round(0.45 + 0.85 * _challenge_unit(seed, 2), 12)
    wrong_rate = round(rate + 0.40 + 0.35 * _challenge_unit(seed, 3), 12)
    boundary_rate = round(-1.10 + 0.65 * _challenge_unit(seed, 4), 12)
    boundary_initial = round(0.30 + 1.10 * _challenge_unit(seed, 5), 12)
    boundary_duration = round(0.20 + 0.90 * _challenge_unit(seed, 6), 12)
    return {
        "rate": rate,
        "initial": initial,
        "duration": duration,
        "wrong_rate": wrong_rate,
        "boundary_rate": boundary_rate,
        "boundary_initial": boundary_initial,
        "boundary_duration": boundary_duration,
    }


def _strict_carrier_record(
    broker: ExternalEnginePacketBroker,
) -> tuple[Path, str]:
    project_path = (broker.julia_project / "Project.toml").resolve()
    try:
        project_sha256 = _sha256_file(project_path)
    except OSError as exc:
        raise ExternalJuliaCapabilityError(
            f"strict Julia carrier project unavailable: {exc}"
        ) from exc
    if project_sha256 != JULIA_CARRIER_PROJECT_SHA256:
        raise ExternalJuliaCapabilityError(
            "strict Julia carrier project digest mismatch"
        )
    return project_path, project_sha256


def _receipt_body(
    *,
    binding: dict[str, str],
    challenge_case: dict[str, float],
    fixture_path: Path,
    fixture_sha256: str,
    capability_source_sha256: str,
    packet_controller_source_sha256: str,
    worker_source_sha256: str,
    strict_carrier_project_path: Path,
    strict_carrier_project_sha256: str,
    row: dict[str, Any],
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
        "release_allowed": False,
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
        "worker_source_sha256_expected": WORKER_SHA256["julia"],
        "strict_carrier_project_path": str(strict_carrier_project_path),
        "strict_carrier_project_sha256": strict_carrier_project_sha256,
        "strict_carrier_project_sha256_expected": JULIA_CARRIER_PROJECT_SHA256,
        "strict_load_path": STRICT_LOAD_PATH,
        "julia_runtime_pin": _runtime_pin_dict("julia"),
        "row": row,
        "engine_readiness_claim": False,
        "cr_truth_claim": False,
        "promotion_allowed": False,
        "claim_ceiling": CAPABILITY_CLAIM_CEILING,
    }


class JuliaDifferentialEquationsCapabilityBroker:
    """Controller-owned broker for one strict-carrier Julia ODE operation."""

    def __init__(
        self,
        packet_broker: ExternalEnginePacketBroker | None = None,
    ) -> None:
        self.packet_broker = packet_broker or ExternalEnginePacketBroker()
        self.source_path = Path(__file__).resolve()

    def run(self, binding: JuliaCapabilityBinding) -> dict[str, Any]:
        binding_body = validate_julia_capability_binding(binding)
        try:
            fixture, _canonical_fixture, fixture_sha256 = (
                self.packet_broker._load_fixture()
            )
            capability_source_sha256 = _sha256_file(self.source_path)
            packet_source_sha256 = _sha256_file(
                self.packet_broker.controller_path
            )
            worker_source_sha256 = _sha256_file(
                self.packet_broker.julia_worker
            )
        except (OSError, ExternalPacketError) as exc:
            raise ExternalJuliaCapabilityError(
                f"capability source or fixture integrity failed: {exc}"
            ) from exc
        if fixture_sha256 != FIXTURE_SHA256:
            raise ExternalJuliaCapabilityError("base fixture pin mismatch")
        if worker_source_sha256 != WORKER_SHA256["julia"]:
            raise ExternalJuliaCapabilityError("Julia worker source pin mismatch")
        strict_project_path, strict_project_sha256 = _strict_carrier_record(
            self.packet_broker
        )
        challenge_case = derive_julia_challenge_case(binding.challenge_seed_hex)
        challenge_fixture = {
            **fixture,
            CASE_KEYS["julia_diffeq"]: challenge_case,
        }
        row = self.packet_broker._run_row(
            "julia_diffeq",
            challenge_fixture,
            fixture_sha256,
        )
        body = _receipt_body(
            binding=binding_body,
            challenge_case=challenge_case,
            fixture_path=self.packet_broker.fixture_path,
            fixture_sha256=fixture_sha256,
            capability_source_sha256=capability_source_sha256,
            packet_controller_source_sha256=packet_source_sha256,
            worker_source_sha256=worker_source_sha256,
            strict_carrier_project_path=strict_project_path,
            strict_carrier_project_sha256=strict_project_sha256,
            row=row,
            status=row["status"],
            reason=row["reason"],
        )
        receipt = {
            **body,
            "receipt_sha256": _SHA256(canonical_json(body)).hexdigest(),
        }
        errors = validate_julia_capability_receipt(
            receipt,
            expected_binding=binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=row["status"] == "PASS",
        )
        if errors:
            raise ExternalJuliaCapabilityError(
                "capability self-verification failed: " + "; ".join(errors)
            )
        return receipt


def validate_julia_capability_receipt(
    receipt: dict[str, Any],
    *,
    expected_binding: JuliaCapabilityBinding,
    expected_receipt_sha256: str,
    require_pass: bool = True,
) -> tuple[str, ...]:
    """Revalidate one Julia receipt against current controller-owned pins."""

    errors: list[str] = []

    def error(path: str, reason: str) -> None:
        errors.append(f"{path}:{reason}")

    def expect(observed: object, expected: object, path: str) -> None:
        if observed != expected:
            error(path, "mismatch")

    def digest(value: object, path: str) -> None:
        if not _valid_sha256(value):
            error(path, "invalid_sha256")

    def exact_keys(
        value: object,
        path: str,
        expected: set[str],
    ) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            error(path, "not_object")
            return None
        if set(value) != expected:
            error(path, "keys_mismatch")
        return value

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
        "release_allowed",
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
        "strict_carrier_project_path",
        "strict_carrier_project_sha256",
        "strict_carrier_project_sha256_expected",
        "strict_load_path",
        "julia_runtime_pin",
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
    expect(body["release_allowed"], False, "$.release_allowed")
    expect(body["engine_readiness_claim"], False, "$.engine_readiness_claim")
    expect(body["cr_truth_claim"], False, "$.cr_truth_claim")
    expect(body["promotion_allowed"], False, "$.promotion_allowed")
    expect(body["claim_ceiling"], CAPABILITY_CLAIM_CEILING, "$.claim_ceiling")
    expect(body["strict_load_path"], STRICT_LOAD_PATH, "$.strict_load_path")
    expect(
        body["julia_runtime_pin"],
        _runtime_pin_dict("julia"),
        "$.julia_runtime_pin",
    )

    expected_binding_body = validate_julia_capability_binding(expected_binding)
    try:
        observed_binding = julia_capability_binding_from_dict(body["binding"])
    except ExternalJuliaCapabilityError as exc:
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
        current_worker_source = _sha256_file(broker.julia_worker)
        current_project_path, current_project_source = _strict_carrier_record(
            broker
        )
    except (OSError, ExternalPacketError, ExternalJuliaCapabilityError) as exc:
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
        WORKER_SHA256["julia"],
        "$.worker_source_pin",
    )
    expect(
        body["worker_source_sha256_expected"],
        WORKER_SHA256["julia"],
        "$.worker_source_sha256_expected",
    )
    expect(
        body["strict_carrier_project_path"],
        str(current_project_path),
        "$.strict_carrier_project_path",
    )
    expect(
        body["strict_carrier_project_sha256"],
        current_project_source,
        "$.strict_carrier_project_sha256",
    )
    expect(
        body["strict_carrier_project_sha256"],
        JULIA_CARRIER_PROJECT_SHA256,
        "$.strict_carrier_project_pin",
    )
    expect(
        body["strict_carrier_project_sha256_expected"],
        JULIA_CARRIER_PROJECT_SHA256,
        "$.strict_carrier_project_sha256_expected",
    )

    expected_case = derive_julia_challenge_case(expected_binding.challenge_seed_hex)
    expect(body["challenge_case"], expected_case, "$.challenge_case")
    expect(
        body["challenge_case_sha256"],
        _SHA256(canonical_json(expected_case)).hexdigest(),
        "$.challenge_case_sha256",
    )

    status = body["status"]
    if status not in {"PASS", "PARKED", "FAIL"}:
        error("$.status", "invalid")
    if require_pass and status != "PASS":
        error("$.status", "pass_required")
    row = body["row"]
    if not isinstance(row, dict):
        error("$.row", "not_object")
        return tuple(errors)
    if status != "PASS":
        expect(row.get("status"), status, "$.row.status")
        expect(row.get("reason"), body["reason"], "$.row.reason")
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
    if set(row) != expected_row_keys:
        error("$.row", "pass_row_keys_mismatch")
        return tuple(errors)
    expect(row["schema"], ROW_SCHEMA, "$.row.schema")
    expect(row["engine_id"], "julia_diffeq", "$.row.engine_id")
    expect(row["external_system"], True, "$.row.external_system")
    expect(
        row["kernel_membership"],
        "EXTERNAL_NOT_CB_KERNEL",
        "$.row.kernel_membership",
    )
    expect(row["exact_api"], EXACT_APIS["julia_diffeq"], "$.row.exact_api")
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
        _runtime_pin_dict("julia"),
        "$.row.runtime_pin",
    )
    expect(row["command"], broker._command("julia_diffeq")[0], "$.row.command")
    expect(
        row["worker_source_sha256"],
        current_worker_source,
        "$.row.worker_source_sha256",
    )
    expect(
        row["worker_source_sha256"],
        WORKER_SHA256["julia"],
        "$.row.worker_source_pin",
    )
    expect(
        row["worker_source_sha256_expected"],
        WORKER_SHA256["julia"],
        "$.row.worker_source_sha256_expected",
    )
    runtime_identity = inspect_external_runtime("julia")
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
    observed = exact_keys(
        row["observed"],
        "$.row.observed",
        {"terminal", "boundary_terminal"},
    )
    runtime = exact_keys(
        row["runtime"],
        "$.row.runtime",
        {"julia_version", "package_version", "active_project", "load_path"},
    )
    if errors or observed is None or runtime is None:
        return tuple(errors)
    expect(runtime["julia_version"], JULIA_VERSION_PIN, "$.row.runtime.julia_version")
    expect(
        runtime["package_version"],
        DIFFERENTIALEQUATIONS_VERSION_PIN,
        "$.row.runtime.package_version",
    )
    expect(
        runtime["active_project"],
        str(current_project_path),
        "$.row.runtime.active_project",
    )
    expect(runtime["load_path"], STRICT_LOAD_PATH, "$.row.runtime.load_path")
    challenge_fixture = {
        **fixture,
        CASE_KEYS["julia_diffeq"]: expected_case,
    }
    transport = {
        "schema": INPUT_SCHEMA,
        "engine_id": "julia_diffeq",
        "case": expected_case,
    }
    expect(
        row["input_sha256"],
        _SHA256(canonical_json(transport)).hexdigest(),
        "$.row.input_sha256",
    )
    witness = {
        "schema": "constraintbox.external-engine-witness.v1",
        "engine_id": "julia_diffeq",
        "exact_api": EXACT_APIS["julia_diffeq"],
        "observed": observed,
        "runtime": runtime,
        "pid": worker_pid,
    }
    witness_bytes = canonical_json(witness)
    expect(
        row["output_sha256"],
        _SHA256(witness_bytes).hexdigest(),
        "$.row.output_sha256",
    )
    # JSON3 emits valid strict JSON but does not promise canonical key order.
    # The broker binds the canonical parsed witness through output_sha256; the
    # raw stdout digest remains an audit pin rather than a reserialized value.
    expect(row["stderr_sha256"], _EMPTY_SHA256, "$.row.stderr_sha256")
    evaluation = evaluate_worker_output(
        "julia_diffeq",
        challenge_fixture,
        witness,
        julia_project=broker.julia_project,
        controller_pid=os.getpid(),
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
        or set(controls) != {
            "positive",
            "targeted_negative",
            "boundary",
            "strict_carrier",
        }
        or not all(value is True for value in controls.values())
        or evaluation.get("errors")
    ):
        error("$.row.controls", "not_all_required_controls_true")
    return tuple(errors)
