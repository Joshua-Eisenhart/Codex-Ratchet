from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .intake import parse_json_object


TRUST_MANIFEST_SCHEMA = "constraintbox.trusted-receipt-set.v1"
SIM_TIER_RECEIPT_SCHEMA = "constraintbox.sim-tier-receipt.v2"
CAPABILITY_STATES = {
    "READY",
    "DEGRADED",
    "UNAVAILABLE",
    "DRIFT",
    "FAILED",
    "UNTESTED",
}
_TRUST_MANIFEST_FIELDS = {
    "schema",
    "trust_set_id",
    "receipt_bindings",
    "promotion_allowed",
}
_TRUST_BINDING_FIELDS = {"receipt_sha256", "receipt_schema", "layer_id"}
_RECEIPT_FIELDS = {
    "schema",
    "layer_id",
    "layer_name",
    "mode",
    "state",
    "manifest_sha256",
    "fixture_sha256",
    "controller_sha256",
    "python_executable",
    "python_version",
    "environment",
    "elapsed_seconds",
    "capabilities",
    "generated_at_utc",
    "promotion_allowed",
}
_CAPABILITY_FIELDS = {
    "capability_id",
    "required",
    "state",
    "reason",
    "expected_version",
    "observed_version",
    "elapsed_seconds",
    "worker_sha256",
    "fixture_sha256",
    "controls",
    "evidence",
}


class ReceiptTrustError(ValueError):
    """The controller-owned receipt trust root is malformed or does not match."""


@dataclass(frozen=True)
class TrustedReceiptBinding:
    receipt_sha256: str
    receipt_schema: str
    layer_id: str


@dataclass(frozen=True)
class TrustedReceiptSet:
    """Externally pinned receipt digests supplied by the trusted controller.

    ``manifest_sha256`` must come from a controller-owned configuration or
    equivalent trust root.  Reading a digest from the same untrusted receipt
    (or calculating it on demand from caller-provided receipt paths) does not
    establish this type of binding.
    """

    trust_set_id: str
    manifest_sha256: str
    bindings: tuple[TrustedReceiptBinding, ...]

    def by_digest(self) -> dict[str, TrustedReceiptBinding]:
        return {row.receipt_sha256: row for row in self.bindings}


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_nonnegative_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def _timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def load_trusted_receipt_set(
    manifest_path: Path,
    *,
    expected_manifest_sha256: str,
) -> TrustedReceiptSet:
    """Load a trust set only when its bytes match an external digest pin."""
    if not _is_sha256(expected_manifest_sha256):
        raise ReceiptTrustError("expected trust-manifest sha256 is malformed")
    raw = manifest_path.read_bytes()
    observed_manifest_sha256 = hashlib.sha256(raw).hexdigest()
    if observed_manifest_sha256 != expected_manifest_sha256:
        raise ReceiptTrustError("trust-manifest sha256 does not match external pin")
    body = parse_json_object(raw)
    if set(body) != _TRUST_MANIFEST_FIELDS:
        raise ReceiptTrustError("trust manifest fields do not match schema")
    if body.get("schema") != TRUST_MANIFEST_SCHEMA:
        raise ReceiptTrustError("unsupported trust manifest schema")
    trust_set_id = body.get("trust_set_id")
    if (
        not isinstance(trust_set_id, str)
        or not trust_set_id.strip()
        or len(trust_set_id) > 128
    ):
        raise ReceiptTrustError("trust_set_id is missing or malformed")
    if body.get("promotion_allowed") is not False:
        raise ReceiptTrustError("trust manifest must keep promotion_allowed false")
    raw_bindings = body.get("receipt_bindings")
    if not isinstance(raw_bindings, list) or not raw_bindings:
        raise ReceiptTrustError("trust manifest must bind at least one receipt")

    bindings: list[TrustedReceiptBinding] = []
    seen_digests: set[str] = set()
    for raw_binding in raw_bindings:
        if (
            not isinstance(raw_binding, dict)
            or set(raw_binding) != _TRUST_BINDING_FIELDS
        ):
            raise ReceiptTrustError("receipt binding fields do not match schema")
        receipt_sha256 = raw_binding.get("receipt_sha256")
        receipt_schema = raw_binding.get("receipt_schema")
        layer_id = raw_binding.get("layer_id")
        if not _is_sha256(receipt_sha256):
            raise ReceiptTrustError("receipt binding sha256 is malformed")
        if receipt_sha256 in seen_digests:
            raise ReceiptTrustError("receipt binding sha256 is duplicated")
        if receipt_schema != SIM_TIER_RECEIPT_SCHEMA:
            raise ReceiptTrustError("receipt binding schema is not a sim-tier receipt")
        if (
            not isinstance(layer_id, str)
            or not layer_id.strip()
            or len(layer_id) > 128
        ):
            raise ReceiptTrustError("receipt binding layer_id is malformed")
        seen_digests.add(receipt_sha256)
        bindings.append(
            TrustedReceiptBinding(
                receipt_sha256=receipt_sha256,
                receipt_schema=receipt_schema,
                layer_id=layer_id,
            )
        )

    return TrustedReceiptSet(
        trust_set_id=trust_set_id,
        manifest_sha256=observed_manifest_sha256,
        bindings=tuple(bindings),
    )


def _validate_sim_tier_receipt(body: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(body) != _RECEIPT_FIELDS:
        errors.append("receipt_fields_invalid")
        return errors
    if body.get("schema") != SIM_TIER_RECEIPT_SCHEMA:
        errors.append("receipt_schema_invalid")
    for field in ("layer_id", "layer_name", "python_executable", "python_version"):
        value = body.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field}_invalid")
    if body.get("mode") not in {"boot", "acceptance"}:
        errors.append("mode_invalid")
    if body.get("state") not in CAPABILITY_STATES:
        errors.append("state_invalid")
    for field in ("manifest_sha256", "fixture_sha256", "controller_sha256"):
        if not _is_sha256(body.get(field)):
            errors.append(f"{field}_invalid")
    if not isinstance(body.get("environment"), dict):
        errors.append("environment_invalid")
    if not _is_nonnegative_number(body.get("elapsed_seconds")):
        errors.append("elapsed_seconds_invalid")
    if body.get("promotion_allowed") is not False:
        errors.append("promotion_allowed_invalid")
    generated_at = body.get("generated_at_utc")
    if not isinstance(generated_at, str):
        errors.append("generated_at_utc_invalid")
    else:
        try:
            _timestamp(generated_at)
        except (TypeError, ValueError):
            errors.append("generated_at_utc_invalid")

    capabilities = body.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("capabilities_invalid")
        return errors
    seen_capabilities: set[str] = set()
    receipt_fixture_sha = body.get("fixture_sha256")
    for row in capabilities:
        if not isinstance(row, dict) or set(row) != _CAPABILITY_FIELDS:
            errors.append("capability_fields_invalid")
            continue
        capability_id = row.get("capability_id")
        if (
            not isinstance(capability_id, str)
            or not capability_id.strip()
            or capability_id in seen_capabilities
        ):
            errors.append("capability_id_invalid_or_duplicate")
        else:
            seen_capabilities.add(capability_id)
        if not isinstance(row.get("required"), bool):
            errors.append(f"capability_required_invalid:{capability_id}")
        if row.get("state") not in CAPABILITY_STATES:
            errors.append(f"capability_state_invalid:{capability_id}")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            errors.append(f"capability_reason_invalid:{capability_id}")
        for field in ("expected_version", "observed_version"):
            if row.get(field) is not None and not isinstance(row.get(field), str):
                errors.append(f"capability_{field}_invalid:{capability_id}")
        if not _is_nonnegative_number(row.get("elapsed_seconds")):
            errors.append(f"capability_elapsed_seconds_invalid:{capability_id}")
        worker_sha = row.get("worker_sha256")
        if worker_sha is not None and not _is_sha256(worker_sha):
            errors.append(f"capability_worker_sha256_invalid:{capability_id}")
        if (
            not _is_sha256(row.get("fixture_sha256"))
            or row.get("fixture_sha256") != receipt_fixture_sha
        ):
            errors.append(f"capability_fixture_sha256_invalid:{capability_id}")
        controls = row.get("controls")
        if (
            not isinstance(controls, dict)
            or not all(
                isinstance(key, str) and isinstance(value, bool)
                for key, value in controls.items()
            )
        ):
            errors.append(f"capability_controls_invalid:{capability_id}")
        if not isinstance(row.get("evidence"), dict):
            errors.append(f"capability_evidence_invalid:{capability_id}")
    return errors


def bind_trusted_receipts(
    receipt_paths: list[Path],
    trusted_receipts: TrustedReceiptSet | None,
) -> tuple[
    list[tuple[Path, dict[str, Any], str]],
    list[dict[str, str]],
    dict[str, Any],
]:
    """Bind and type-check receipts before callers inspect claimed states."""
    if trusted_receipts is None:
        return (
            [],
            [{"reason": "trusted_receipt_set_missing"}],
            {
                "status": "UNBOUND",
                "trust_set_id": None,
                "trust_manifest_sha256": None,
                "provided_receipt_count": len(receipt_paths),
                "bound_receipt_count": 0,
            },
        )
    if not receipt_paths:
        return (
            [],
            [{"reason": "receipt_paths_empty"}],
            {
                "status": "INVALID",
                "trust_set_id": trusted_receipts.trust_set_id,
                "trust_manifest_sha256": trusted_receipts.manifest_sha256,
                "provided_receipt_count": 0,
                "bound_receipt_count": 0,
            },
        )

    bindings = trusted_receipts.by_digest()
    validated: list[tuple[Path, dict[str, Any], str]] = []
    problems: list[dict[str, str]] = []
    seen_receipt_digests: set[str] = set()
    for path in receipt_paths:
        try:
            raw = path.read_bytes()
        except OSError:
            problems.append({"path": str(path), "reason": "receipt_unreadable"})
            continue
        receipt_sha256 = hashlib.sha256(raw).hexdigest()
        if receipt_sha256 in seen_receipt_digests:
            problems.append(
                {"path": str(path), "reason": "duplicate_receipt_digest"}
            )
            continue
        seen_receipt_digests.add(receipt_sha256)
        binding = bindings.get(receipt_sha256)
        if binding is None:
            problems.append(
                {"path": str(path), "reason": "receipt_digest_not_trusted"}
            )
            continue
        try:
            body = parse_json_object(raw)
        except (TypeError, ValueError):
            problems.append(
                {"path": str(path), "reason": "receipt_json_invalid"}
            )
            continue
        receipt_errors = _validate_sim_tier_receipt(body)
        if receipt_errors:
            problems.append(
                {
                    "path": str(path),
                    "reason": "receipt_type_invalid",
                    "details": ",".join(receipt_errors),
                }
            )
            continue
        if (
            body["schema"] != binding.receipt_schema
            or body["layer_id"] != binding.layer_id
        ):
            problems.append(
                {
                    "path": str(path),
                    "reason": "receipt_identity_does_not_match_trust_binding",
                }
            )
            continue
        validated.append((path, body, receipt_sha256))

    trust_status = "BOUND" if not problems else "INVALID"
    return (
        validated,
        problems,
        {
            "status": trust_status,
            "trust_set_id": trusted_receipts.trust_set_id,
            "trust_manifest_sha256": trusted_receipts.manifest_sha256,
            "provided_receipt_count": len(receipt_paths),
            "bound_receipt_count": len(validated),
        },
    )


def major_run_preflight(
    receipt_paths: list[Path],
    required_tiers: list[str],
    max_age_hours: float,
    *,
    trusted_receipts: TrustedReceiptSet | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Check controller-bound sim-tier receipts before a major run.

    The receipt's own ``READY`` string is never a trust root.  Every receipt
    must first match a byte digest in an externally pinned
    :class:`TrustedReceiptSet` and pass the exact v2 receipt shape.
    """
    if max_age_hours <= 0:
        raise ValueError("max_age_hours must be positive")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    validated, trust_problems, trust_binding = bind_trusted_receipts(
        receipt_paths, trusted_receipts
    )
    if trust_problems:
        return {
            "schema": "constraintbox.major-run-preflight.v2",
            "required_tiers": required_tiers,
            "max_age_hours": max_age_hours,
            "trust_binding": trust_binding,
            "receipt_checks_performed": False,
            "problems": trust_problems,
            "disposition": "PARKED",
            "promotion_allowed": False,
        }

    by_tier: dict[str, dict[str, Any]] = {}
    problems: list[dict[str, str]] = []
    for path, body, _receipt_sha256 in validated:
        tier_id = body["layer_id"]
        if tier_id in by_tier:
            problems.append({"path": str(path), "reason": f"duplicate_tier:{tier_id}"})
            continue
        by_tier[tier_id] = body

    for tier_id in required_tiers:
        body = by_tier.get(tier_id)
        if body is None:
            problems.append({"tier_id": tier_id, "reason": "receipt_missing"})
            continue
        required_unready = [
            str(row["capability_id"])
            for row in body["capabilities"]
            if row["required"] is True and row["state"] != "READY"
        ]
        if body["state"] not in {"READY", "DEGRADED"} or required_unready:
            problems.append(
                {
                    "tier_id": tier_id,
                    "reason": f"tier_not_ready:{body['state']}",
                    "required_unready": ",".join(required_unready),
                }
            )
        generated = body["generated_at_utc"]
        age_hours = (current - _timestamp(generated)).total_seconds() / 3600.0
        if age_hours < 0 or age_hours > max_age_hours:
            problems.append(
                {
                    "tier_id": tier_id,
                    "reason": "receipt_stale",
                    "age_hours": f"{age_hours:.6f}",
                }
            )

    return {
        "schema": "constraintbox.major-run-preflight.v2",
        "required_tiers": required_tiers,
        "max_age_hours": max_age_hours,
        "trust_binding": trust_binding,
        "receipt_checks_performed": True,
        "problems": problems,
        "disposition": "READY" if not problems else "PARKED",
        "promotion_allowed": False,
    }
