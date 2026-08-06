"""Typed, bounded simulation-evidence admission for the ClaimGate boundary.

This module deliberately admits *retained bounded evidence*, not a scientific
claim, engine readiness, release, or promotion.  The evaluator owns the
accepted receipt families and recomputes their structural/hash contracts; a
producer cannot select a command or declare itself admitted.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .capability_origin import capability_ids
from .intake import canonical_json


SCHEMA = "constraintbox.sim-admission-claim.v1"
CLAIM_KIND = "constraintbox_sim_evidence_v1"
_HEX = frozenset("0123456789abcdef")
_CLAIM_KEYS = frozenset(
    {
        "schema",
        "claim_kind",
        "produced_by",
        "capability_suite",
        "attractor_basin_envelope",
        "release_allowed",
        "promotion_allowed",
        "claim_ceiling",
    }
)
_REF_KEYS = frozenset({"path", "sha256"})


class SimAdmissionError(ValueError):
    """The bounded sim-evidence admission contract did not hold."""


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SimAdmissionError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                SimAdmissionError(f"non-finite JSON value: {value}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SimAdmissionError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SimAdmissionError(f"{path} root must be an object")
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _require_ref(value: Any, label: str) -> tuple[Path, str]:
    if not isinstance(value, dict) or frozenset(value) != _REF_KEYS:
        raise SimAdmissionError(f"{label} must be exactly {{path, sha256}}")
    path_text = value.get("path")
    digest = value.get("sha256")
    if not isinstance(path_text, str) or not path_text:
        raise SimAdmissionError(f"{label}.path must be a nonempty string")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or not set(digest).issubset(_HEX)
    ):
        raise SimAdmissionError(f"{label}.sha256 must be lowercase SHA-256")
    path = Path(path_text).expanduser().resolve(strict=True)
    if not path.is_file():
        raise SimAdmissionError(f"{label}.path is not a file")
    if _sha256_file(path) != digest:
        raise SimAdmissionError(f"{label}.sha256 does not bind the file")
    return path, digest


def build_claim(*, capability_suite: Path, attractor_basin_envelope: Path) -> dict[str, Any]:
    """Build the fixed receipt handed to ClaimGate's registered verifier."""

    suite = capability_suite.expanduser().resolve(strict=True)
    basin = attractor_basin_envelope.expanduser().resolve(strict=True)
    return {
        "schema": SCHEMA,
        "claim_kind": CLAIM_KIND,
        "produced_by": "constraintbox.sim_admission",
        "capability_suite": {"path": str(suite), "sha256": _sha256_file(suite)},
        "attractor_basin_envelope": {
            "path": str(basin),
            "sha256": _sha256_file(basin),
        },
        "release_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": (
            "retained fixed capability-suite and three-engine attractor-basin "
            "evidence passed evaluator-owned structural and hash rechecks; "
            "not an engine rerun, scientific claim, runtime-readiness claim, "
            "release, or promotion"
        ),
    }


def run_sim_admission(
    *,
    capability_suite: Path,
    attractor_basin_envelope: Path,
    claim_path: Path,
) -> tuple[dict[str, Any], int]:
    """Write one controller-built claim and pass it through ClaimGate.

    ``claim_path`` must be a new absolute path so no caller can overwrite a
    prior admission artifact.  ClaimGate remains the decision consumer; this
    helper only assembles the fixed typed input.
    """

    if not claim_path.is_absolute() or claim_path.exists():
        raise SimAdmissionError("sim-admission claim path must be new and absolute")
    claim = build_claim(
        capability_suite=capability_suite,
        attractor_basin_envelope=attractor_basin_envelope,
    )
    claim_path.parent.mkdir(parents=True, exist_ok=False)
    with claim_path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(claim, indent=2, sort_keys=True) + "\n")
    from .gate import GateError, run_gate

    try:
        gate_result = run_gate(claim_path)
    except GateError as exc:
        return {
            "schema": "constraintbox.sim-admission-result.v1",
            "disposition": "HOLD",
            "reason": "claimgate_execution_error",
            "error": str(exc),
            "claim": str(claim_path),
            "release_allowed": False,
            "promotion_allowed": False,
        }, 5
    disposition = "ELIGIBLE" if gate_result.get("disposition") == "ADMITTED" else "BLOCKED"
    return {
        "schema": "constraintbox.sim-admission-result.v1",
        "disposition": disposition,
        "reason": (
            "claimgate_recomputed_capability_and_basin_evidence"
            if disposition == "ELIGIBLE"
            else "claimgate_did_not_admit_sim_evidence"
        ),
        "claim": str(claim_path),
        "claim_sha256": _sha256_file(claim_path),
        "gate_result": gate_result,
        "release_allowed": False,
        "promotion_allowed": False,
        "claim_ceiling": claim["claim_ceiling"],
    }, 0 if disposition == "ELIGIBLE" else 1


def _verify_capability_suite(path: Path) -> None:
    suite = _read_object(path)
    if suite.get("schema") != "constraintbox.capability-suite-receipt.v1":
        raise SimAdmissionError("capability suite schema mismatch")
    if suite.get("disposition") != "ELIGIBLE":
        raise SimAdmissionError("capability suite is not ELIGIBLE")
    if suite.get("release_allowed") is not False or suite.get("promotion_allowed") is not False:
        raise SimAdmissionError("capability suite tries to grant release or promotion")
    components = suite.get("components")
    expected_ids = list(capability_ids())
    if not isinstance(components, list) or len(components) != len(expected_ids):
        raise SimAdmissionError("capability suite component count differs from policy")
    for index, (component, capability_id) in enumerate(zip(components, expected_ids)):
        if not isinstance(component, dict) or component.get("capability_id") != capability_id:
            raise SimAdmissionError(f"capability component {index} identity differs from policy")
        result = component.get("result")
        replay = component.get("independent_replay")
        if (
            component.get("state") != "ELIGIBLE"
            or not isinstance(result, dict)
            or not isinstance(replay, dict)
            or result.get("capability_id") != capability_id
            or result.get("disposition") != "ELIGIBLE"
            or result.get("release_allowed") is not False
            or result.get("promotion_allowed") is not False
            or replay.get("capability_id") != capability_id
            or replay.get("disposition") != "ELIGIBLE"
            or replay.get("independent_replay") is not True
        ):
            raise SimAdmissionError(f"capability component {capability_id} is not replay-eligible")
        if component.get("result_sha256") != hashlib.sha256(canonical_json(result)).hexdigest():
            raise SimAdmissionError(f"capability component {capability_id} result hash mismatch")
        if component.get("independent_replay_sha256") != hashlib.sha256(canonical_json(replay)).hexdigest():
            raise SimAdmissionError(f"capability component {capability_id} replay hash mismatch")


def _verify_attractor_basin(path: Path) -> None:
    # The existing verifier recursively rechecks the three engine receipts,
    # controller source, formal/SMT controls, and retained Mini-Lev evidence.
    root = Path(__file__).resolve().parents[2]
    verifier_path = root / "scripts" / "verify_attractor_basin_envelope.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("constraintbox_basin_verifier", verifier_path)
    if spec is None or spec.loader is None:
        raise SimAdmissionError("attractor-basin verifier is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify_envelope(path)
    if result.get("state") != "VERIFIED" or result.get("promotion_allowed") is not False:
        raise SimAdmissionError("attractor-basin envelope did not independently verify")


def verify_claim(claim_path: Path) -> dict[str, Any]:
    """Recompute the fixed evidence predicates for ClaimGate tier 2."""

    claim = _read_object(claim_path.expanduser().resolve(strict=True))
    if frozenset(claim) != _CLAIM_KEYS:
        raise SimAdmissionError("sim-admission claim key set differs from policy")
    if claim.get("schema") != SCHEMA or claim.get("claim_kind") != CLAIM_KIND:
        raise SimAdmissionError("sim-admission claim schema or kind differs from policy")
    if claim.get("produced_by") != "constraintbox.sim_admission":
        raise SimAdmissionError("sim-admission producer identity differs from policy")
    if claim.get("release_allowed") is not False or claim.get("promotion_allowed") is not False:
        raise SimAdmissionError("sim-admission claims must remain non-releasing and non-promoting")
    suite_path, suite_sha256 = _require_ref(claim.get("capability_suite"), "capability_suite")
    basin_path, basin_sha256 = _require_ref(
        claim.get("attractor_basin_envelope"), "attractor_basin_envelope"
    )
    _verify_capability_suite(suite_path)
    _verify_attractor_basin(basin_path)
    return {
        "schema": "constraintbox.sim-admission-verification.v1",
        "state": "ELIGIBLE",
        "claim_sha256": _sha256_file(claim_path),
        "capability_suite_sha256": suite_sha256,
        "attractor_basin_envelope_sha256": basin_sha256,
        "release_allowed": False,
        "promotion_allowed": False,
    }
