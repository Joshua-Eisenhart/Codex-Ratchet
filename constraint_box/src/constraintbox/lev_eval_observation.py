"""Strict, non-authoritative observation of one Lev eval-run bundle.

This adapter deliberately does *not* run Lev, FlowMind, a suite, a provider,
or a ClaimGate path.  It snapshots five already-produced Lev artifacts, checks
the relationships that are available in that closed bundle, and writes a
ConstraintBox-owned observation receipt.  A foreign ``pass`` is retained as an
observation only; it is never a ConstraintBox disposition or admission.

The raw snapshot is a CB-private forensic copy and deliberately preserves the
foreign bytes exactly.  Those bytes can contain the producer's absolute paths.
Only the Mini-Lev flow receipt, ledger, CLI result, and durable binding record
omit literal source paths and foreign verdict fields.

The Lev writer does not retain raw trace- and command-case result arrays in
this five-file bundle.  Their decision digests are therefore deliberately
reported as foreign and unrecomputed rather than guessed at.
"""

from __future__ import annotations

import errno
import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import intake as _intake_module
from .intake import IntakeError, canonical_json, parse_json_object


_SHA256 = hashlib.sha256
_SCHEMA = "constraintbox.lev-eval-observation.v1"
_RECEIPT_NAME = "lev_eval_observation_receipt.json"
_FOREIGN_DIRECTORY = "foreign_lev_eval_bundle"
_SOURCE_FILES = (
    "run.json",
    "decision.json",
    "measurements.jsonl",
    "measurement-series/projection.json",
    "seal.json",
)
_OBSERVATION_EXPECTED_FILES = frozenset((*_SOURCE_FILES, _RECEIPT_NAME))
_MAX_ARTIFACT_BYTES = 1_048_576
_MAX_MEASUREMENTS_BYTES = 4_194_304
_MAX_MEASUREMENTS = 256
_HEX = frozenset("0123456789abcdef")
_UNRECOMPUTED_DIGESTS = (
    "trace_cases_digest",
    "command_cases_digest",
)
_CLAIM_CEILING = (
    "one captured Lev eval artifact path was structurally cross-checked and "
    "retained by ConstraintBox; foreign decision content remains observation "
    "only, with trace and command case digests unrecomputed"
)


class LevEvalObservationError(ValueError):
    """The selected foreign bundle cannot be observed under the fixed contract."""


class LevEvalObservationHoldError(LevEvalObservationError):
    """Local capture or replay integrity failed and must not be treated as input drift."""


@dataclass(frozen=True)
class LevEvalObservationBinding:
    """One controller-selected historical foreign-bundle observation request.

    ``source_run_dir`` is deliberately controller-private.  ``as_dict`` never
    serializes it: retained artifacts bind only its canonical-text hash.  The
    fixed v1 mode is historical-only because this adapter does not run or
    authenticate Lev and therefore cannot establish freshness by itself.
    """

    request_id: str
    source_run_dir: Path | None
    source_run_dir_text_sha256: str
    expected_execution_id: str
    expected_suite_id: str
    observer_profile_sha256: str
    mode: str = "historical_only"

    def __post_init__(self) -> None:
        _require_string(self.request_id, "observation request_id")
        if self.source_run_dir is not None and (
            not isinstance(self.source_run_dir, Path)
            or not self.source_run_dir.is_absolute()
        ):
            raise LevEvalObservationError(
                "observation source_run_dir must be an absolute pathlib.Path or absent for replay"
            )
        _require_sha256(
            self.source_run_dir_text_sha256,
            "observation source_run_dir_text_sha256",
        )
        _require_string(self.expected_execution_id, "observation expected_execution_id")
        _require_string(self.expected_suite_id, "observation expected_suite_id")
        _require_sha256(
            self.observer_profile_sha256,
            "observation observer_profile_sha256",
        )
        if self.mode != "historical_only":
            raise LevEvalObservationError(
                "only the fixed historical_only observation mode is admitted"
            )

    def as_dict(self) -> dict[str, Any]:
        body = {
            "schema": "constraintbox.lev-eval-observation-binding.v1",
            "request_id": self.request_id,
            "source_run_dir_text_sha256": self.source_run_dir_text_sha256,
            "expected_execution_id": self.expected_execution_id,
            "expected_suite_id": self.expected_suite_id,
            "mode": self.mode,
            "observer_profile_sha256": self.observer_profile_sha256,
            "foreign_decision_authority": False,
            "foreign_claim_gate_authenticated": False,
            "promotion_allowed": False,
        }
        return {**body, "request_sha256": _sha256(canonical_json(body))}

    @property
    def request_sha256(self) -> str:
        return self.as_dict()["request_sha256"]

    @classmethod
    def from_dict(cls, value: object) -> "LevEvalObservationBinding":
        """Recover the durable, source-private portion of one binding.

        The source path itself is intentionally absent.  Replay derives it
        solely from the retained raw snapshot and checks its text digest before
        accepting any relationship that refers to the former foreign tree.
        """

        expected = {
            "schema",
            "request_id",
            "source_run_dir_text_sha256",
            "expected_execution_id",
            "expected_suite_id",
            "mode",
            "observer_profile_sha256",
            "foreign_decision_authority",
            "foreign_claim_gate_authenticated",
            "promotion_allowed",
            "request_sha256",
        }
        if not isinstance(value, dict) or set(value) != expected:
            raise LevEvalObservationHoldError(
                "durable observation binding keys mismatch"
            )
        body = dict(value)
        supplied_digest = body.pop("request_sha256")
        if value.get("schema") != "constraintbox.lev-eval-observation-binding.v1":
            raise LevEvalObservationHoldError("durable observation binding schema mismatch")
        if (
            value.get("foreign_decision_authority") is not False
            or value.get("foreign_claim_gate_authenticated") is not False
            or value.get("promotion_allowed") is not False
        ):
            raise LevEvalObservationHoldError(
                "durable observation binding attempted to grant foreign authority"
            )
        if not isinstance(supplied_digest, str) or supplied_digest != _sha256(
            canonical_json(body)
        ):
            raise LevEvalObservationHoldError(
                "durable observation binding digest mismatch"
            )
        try:
            return cls(
                request_id=value["request_id"],
                source_run_dir=None,
                source_run_dir_text_sha256=value["source_run_dir_text_sha256"],
                expected_execution_id=value["expected_execution_id"],
                expected_suite_id=value["expected_suite_id"],
                observer_profile_sha256=value["observer_profile_sha256"],
                mode=value["mode"],
            )
        except LevEvalObservationError as exc:
            raise LevEvalObservationHoldError(
                "durable observation binding fields are invalid"
            ) from exc

    def assert_source_binding(self, source_root: Path) -> None:
        if self.source_run_dir_text_sha256 != _sha256(
            str(source_root).encode("utf-8")
        ):
            raise LevEvalObservationHoldError(
                "selected foreign source path does not match the controller binding"
            )

    def assert_profile_current(self) -> None:
        if self.observer_profile_sha256 != lev_eval_observer_profile_sha256():
            raise LevEvalObservationHoldError(
                "foreign-eval observer implementation identity drifted"
            )


@dataclass(frozen=True)
class LevEvalObservation:
    """One retained, CB-owned observation receipt for a foreign Lev eval run."""

    observation_run_dir: Path
    receipt_path: Path
    receipt_sha256: str
    receipt: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "constraintbox.lev-eval-observation-result.v1",
            "observation_run_dir": str(self.observation_run_dir),
            "receipt": str(self.receipt_path),
            "receipt_sha256": self.receipt_sha256,
            "observed": self.receipt["observed"],
            "claim_ceiling": _CLAIM_CEILING,
            "promotion_allowed": False,
        }


def _sha256(value: bytes) -> str:
    return _SHA256(value).hexdigest()


def lev_eval_observer_profile_sha256() -> str:
    """Bind the observer and strict intake implementation used for replay."""

    source_rows: list[dict[str, str]] = []
    for label, source_path in (
        ("lev_eval_observation", Path(__file__).resolve()),
        ("intake", Path(_intake_module.__file__).resolve()),
    ):
        try:
            source_rows.append(
                {
                    "module": label,
                    "sha256": _sha256(source_path.read_bytes()),
                }
            )
        except OSError as exc:
            raise LevEvalObservationHoldError(
                f"observer implementation source is unavailable: {label}"
            ) from exc
    return _sha256(
        canonical_json(
            {
                "schema": "constraintbox.lev-eval-observer-profile.v1",
                "sources": source_rows,
            }
        )
    )


def build_lev_eval_observation_binding(
    *,
    request_id: str,
    source_run_dir: Path,
    expected_execution_id: str,
    expected_suite_id: str,
) -> LevEvalObservationBinding:
    """Build the immutable, historical-only controller binding for one run."""

    if not isinstance(source_run_dir, Path):
        raise LevEvalObservationError("observation source_run_dir must be a pathlib.Path")
    supplied_source = source_run_dir.expanduser()
    if supplied_source.is_symlink():
        raise LevEvalObservationHoldError(
            "observation source run directory must not be a symlink"
        )
    source_root = supplied_source.resolve(strict=False)
    return LevEvalObservationBinding(
        request_id=request_id,
        source_run_dir=source_root,
        source_run_dir_text_sha256=_sha256(str(source_root).encode("utf-8")),
        expected_execution_id=expected_execution_id,
        expected_suite_id=expected_suite_id,
        observer_profile_sha256=lev_eval_observer_profile_sha256(),
    )


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in _HEX for character in value)
    )


def _require_sha256(value: object, label: str) -> str:
    if not _is_sha256(value):
        raise LevEvalObservationError(f"{label} must be one lowercase SHA-256")
    return value


def _require_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise LevEvalObservationError(f"{label} must be one non-empty string")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise LevEvalObservationError(f"{label} is not UTF-8 encodable") from exc
    return value


def _require_exact_keys(
    value: object,
    *,
    keys: frozenset[str],
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise LevEvalObservationError(f"{label} keys mismatch")
    return value


def _require_list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise LevEvalObservationError(f"{label} must be a list")
    return value


def _require_nonnegative_int(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise LevEvalObservationError(f"{label} must be one non-negative integer")
    return value


def _js_json_bytes(value: object) -> bytes:
    """Match the relevant finite JSON.stringify subset while preserving order.

    The current Lev writer calls ``JSON.stringify`` on source-created records.
    ``parse_json_object`` preserves their object-pair order, and this fixed
    contract accepts only finite JSON, so compact Python serialization has the
    same bytes for the supported Lev v1 subset.
    """

    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise LevEvalObservationError(
            "foreign JSON cannot be reproduced under the Lev v1 digest subset"
        ) from exc


def _absolute_ref(
    value: object,
    *,
    expected: Path,
    label: str,
) -> None:
    resolved = _resolved_absolute_path(value, label)
    if resolved != expected:
        raise LevEvalObservationError(f"{label} does not bind the selected run")


def _resolved_absolute_path(value: object, label: str) -> Path:
    text = _require_string(value, label)
    candidate = Path(text)
    if not candidate.is_absolute():
        raise LevEvalObservationError(f"{label} must be an absolute path in v1")
    try:
        return candidate.resolve(strict=False)
    except OSError as exc:
        raise LevEvalObservationError(f"{label} cannot be resolved") from exc


def _open_real_directory(path: Path, label: str) -> int:
    """Open a fixed directory identity without following a replaced root."""

    try:
        metadata = path.lstat()
    except OSError as exc:
        raise LevEvalObservationError(f"{label} is unavailable") from exc
    if path.is_symlink() or stat.S_ISLNK(metadata.st_mode):
        raise LevEvalObservationHoldError(f"{label} must not be a symlink")
    if not stat.S_ISDIR(metadata.st_mode):
        raise LevEvalObservationError(f"{label} is not a directory")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise LevEvalObservationHoldError(
                f"{label} became a symlink while it was opened"
            ) from exc
        raise LevEvalObservationError(f"{label} could not be opened") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or opened.st_dev != metadata.st_dev
            or opened.st_ino != metadata.st_ino
        ):
            raise LevEvalObservationHoldError(
                f"{label} changed while it was opened"
            )
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _open_real_child_directory(
    parent_fd: int,
    component: str,
    relative_name: str,
) -> int:
    """Traverse one non-symlink child from an already-pinned directory."""

    try:
        metadata = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as exc:
        raise LevEvalObservationError(
            f"foreign artifact parent is unavailable: {relative_name}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise LevEvalObservationHoldError(
            f"foreign artifact parent must not be a symlink: {relative_name}"
        )
    if not stat.S_ISDIR(metadata.st_mode):
        raise LevEvalObservationError(
            f"foreign artifact parent is not a directory: {relative_name}"
        )
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(component, flags, dir_fd=parent_fd)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise LevEvalObservationHoldError(
                f"foreign artifact parent became a symlink: {relative_name}"
            ) from exc
        raise LevEvalObservationError(
            f"foreign artifact parent could not be opened: {relative_name}"
        ) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or opened.st_dev != metadata.st_dev
            or opened.st_ino != metadata.st_ino
        ):
            raise LevEvalObservationHoldError(
                f"foreign artifact parent changed while it was opened: {relative_name}"
            )
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _source_file_bytes(
    source_root: Path,
    relative_name: str,
    *,
    root_fd: int | None = None,
) -> bytes:
    """Read one bounded regular artifact under a pinned directory identity."""

    if root_fd is None:
        parent_fd = _open_real_directory(source_root, "foreign artifact root")
    else:
        try:
            root_metadata = os.fstat(root_fd)
        except OSError as exc:
            raise LevEvalObservationHoldError(
                "foreign artifact root descriptor is unavailable"
            ) from exc
        if not stat.S_ISDIR(root_metadata.st_mode):
            raise LevEvalObservationHoldError(
                "foreign artifact root descriptor is not a directory"
            )
        parent_fd = os.dup(root_fd)
    descriptor = -1
    try:
        parts = Path(relative_name).parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise LevEvalObservationHoldError("foreign artifact relative path is invalid")
        for component in parts[:-1]:
            child_fd = _open_real_child_directory(parent_fd, component, relative_name)
            os.close(parent_fd)
            parent_fd = child_fd
        leaf_name = parts[-1]
        try:
            metadata = os.stat(
                leaf_name,
                dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except OSError as exc:
            raise LevEvalObservationError(
                f"foreign artifact is unavailable: {relative_name}"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise LevEvalObservationHoldError(
                f"foreign artifact must not be a symlink: {relative_name}"
            )
        if not stat.S_ISREG(metadata.st_mode):
            raise LevEvalObservationError(
                f"foreign artifact must be one regular file: {relative_name}"
            )
        maximum = (
            _MAX_MEASUREMENTS_BYTES
            if relative_name == "measurements.jsonl"
            else _MAX_ARTIFACT_BYTES
        )
        if metadata.st_size > maximum:
            raise LevEvalObservationError(
                f"foreign artifact exceeds its controller byte bound: {relative_name}"
            )
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(leaf_name, flags, dir_fd=parent_fd)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise LevEvalObservationHoldError(
                    f"foreign artifact became a symlink: {relative_name}"
                ) from exc
            raise LevEvalObservationError(
                f"foreign artifact could not be read: {relative_name}"
            ) from exc
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != metadata.st_dev
            or opened.st_ino != metadata.st_ino
            or opened.st_size != metadata.st_size
        ):
            raise LevEvalObservationHoldError(
                f"foreign artifact changed before capture: {relative_name}"
            )
        with os.fdopen(descriptor, "rb", closefd=True) as stream:
            descriptor = -1
            value = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
        if len(value) > maximum:
            raise LevEvalObservationError(
                f"foreign artifact exceeds its controller byte bound: {relative_name}"
            )
        if (
            len(value) != opened.st_size
            or after.st_dev != opened.st_dev
            or after.st_ino != opened.st_ino
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
        ):
            raise LevEvalObservationHoldError(
                f"foreign artifact changed while it was captured: {relative_name}"
            )
        return value
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(parent_fd)


def _snapshot_directory_bytes(source_root: Path) -> dict[str, bytes]:
    """Capture all five files from the same pinned directory identity."""

    root_fd = _open_real_directory(source_root, "foreign artifact root")
    try:
        return {
            relative_name: _source_file_bytes(
                source_root,
                relative_name,
                root_fd=root_fd,
            )
            for relative_name in _SOURCE_FILES
        }
    finally:
        os.close(root_fd)


def _parse_object(raw: bytes, label: str) -> dict[str, Any]:
    try:
        return parse_json_object(raw)
    except IntakeError as exc:
        raise LevEvalObservationError(f"{label} is not strict finite JSON") from exc


def _validate_evidence_refs(
    value: object,
    *,
    label: str,
) -> list[dict[str, Any]]:
    refs = _require_list(value, label)
    checked: list[dict[str, Any]] = []
    for index, raw in enumerate(refs):
        ref = _require_exact_keys(
            raw,
            keys=frozenset({"kind", "label", "path", "exists"}),
            label=f"{label}[{index}]",
        )
        if ref["kind"] not in {"suite", "target", "flowmind", "fixture"}:
            raise LevEvalObservationError(f"{label}[{index}].kind is invalid")
        _require_string(ref["label"], f"{label}[{index}].label")
        _require_string(ref["path"], f"{label}[{index}].path")
        if type(ref["exists"]) is not bool:
            raise LevEvalObservationError(f"{label}[{index}].exists is invalid")
        checked.append(ref)
    return checked


def _validate_run(
    value: dict[str, Any],
    *,
    source_root: Path,
) -> tuple[str, str, list[dict[str, Any]], list[Any]]:
    required = frozenset(
        {
            "execution_id",
            "status",
            "suite_id",
            "suite_path",
            "output_root",
            "run_dir",
            "decision_ref",
            "measurements_ref",
            "measurement_series_ref",
            "diagnostics",
            "evidence_refs",
        }
    )
    permitted = required | {"artifact_route"}
    if set(value) not in {required, permitted}:
        raise LevEvalObservationError("run.json keys mismatch")
    execution_id = _require_string(value["execution_id"], "run execution_id")
    suite_id = _require_string(value["suite_id"], "run suite_id")
    if value["status"] not in {"passed", "blocked"}:
        raise LevEvalObservationError("run status is invalid")
    _require_string(value["suite_path"], "run suite_path")
    output_root = _require_string(value["output_root"], "run output_root")
    output_root_path = Path(output_root)
    if not output_root_path.is_absolute() or output_root_path.resolve(strict=False) != source_root.parent:
        raise LevEvalObservationError("run output_root does not bind the selected run")
    _absolute_ref(value["run_dir"], expected=source_root, label="run run_dir")
    _absolute_ref(
        value["decision_ref"],
        expected=source_root / "decision.json",
        label="run decision_ref",
    )
    _absolute_ref(
        value["measurements_ref"],
        expected=source_root / "measurements.jsonl",
        label="run measurements_ref",
    )
    _absolute_ref(
        value["measurement_series_ref"],
        expected=source_root / "measurement-series" / "projection.json",
        label="run measurement_series_ref",
    )
    diagnostics = _require_list(value["diagnostics"], "run diagnostics")
    for index, diagnostic in enumerate(diagnostics):
        if not isinstance(diagnostic, dict):
            raise LevEvalObservationError(f"run diagnostics[{index}] is invalid")
        allowed = {"code", "message", "field", "path"}
        if not {"code", "message"}.issubset(diagnostic) or not set(diagnostic).issubset(allowed):
            raise LevEvalObservationError(f"run diagnostics[{index}] keys mismatch")
        _require_string(diagnostic["code"], f"run diagnostics[{index}].code")
        _require_string(diagnostic["message"], f"run diagnostics[{index}].message")
        for optional in ("field", "path"):
            if optional in diagnostic:
                _require_string(
                    diagnostic[optional],
                    f"run diagnostics[{index}].{optional}",
                )
    return execution_id, suite_id, _validate_evidence_refs(
        value["evidence_refs"], label="run evidence_refs"
    ), diagnostics


def _validate_decision(
    value: dict[str, Any],
    *,
    execution_id: str,
    suite_id: str,
    run_evidence_refs: list[dict[str, Any]],
    run_diagnostics: list[Any],
) -> tuple[str, str | None, str, dict[str, Any]]:
    common = frozenset(
        {
            "schema",
            "decision_id",
            "execution_id",
            "suite_id",
            "input_digests",
            "decided_at",
            "status",
            "reason_code",
        }
    )
    if value.get("status") == "decided":
        required = common | {"verdict"}
    elif value.get("status") == "evaluation_error":
        required = common | {"reason"}
    else:
        raise LevEvalObservationError("decision status is invalid")
    if set(value) != required:
        raise LevEvalObservationError("decision.json keys mismatch")
    if value["schema"] != "lev.eval_decision.v1":
        raise LevEvalObservationError("decision schema is invalid")
    if value["execution_id"] != execution_id or value["suite_id"] != suite_id:
        raise LevEvalObservationError("decision identifiers do not bind run.json")
    expected_id = "decision:" + execution_id + ":" + _sha256(
        suite_id.encode("utf-8")
    )[:16]
    if value["decision_id"] != expected_id:
        raise LevEvalObservationError("decision_id does not match the Lev v1 rule")
    decided_at = _require_string(value["decided_at"], "decision decided_at")
    digests = _require_exact_keys(
        value["input_digests"],
        keys=frozenset(
            {
                "trace_cases_digest",
                "command_cases_digest",
                "diagnostics_digest",
                "evidence_refs_digest",
            }
        ),
        label="decision input_digests",
    )
    for name in (*_UNRECOMPUTED_DIGESTS, "diagnostics_digest", "evidence_refs_digest"):
        _require_sha256(digests[name], f"decision {name}")
    if digests["diagnostics_digest"] != _sha256(_js_json_bytes(run_diagnostics)):
        raise LevEvalObservationError("decision diagnostics_digest mismatch")
    if digests["evidence_refs_digest"] != _sha256(_js_json_bytes(run_evidence_refs)):
        raise LevEvalObservationError("decision evidence_refs_digest mismatch")
    if value["status"] == "decided":
        verdict = value["verdict"]
        if verdict not in {"pass", "fail"}:
            raise LevEvalObservationError("decision verdict is invalid")
        expected_reason = "all_cases_passed" if verdict == "pass" else "case_failed"
        if value["reason_code"] != expected_reason:
            raise LevEvalObservationError("decision reason_code is invalid")
        return value["decision_id"], verdict, decided_at, digests
    _require_string(value["reason"], "decision reason")
    if value["reason_code"] != "cases_unobserved" or value["reason"] != "cases_unobserved":
        raise LevEvalObservationError("decision evaluation-error variant is invalid")
    return value["decision_id"], None, decided_at, digests


def _variable(value: object, label: str) -> dict[str, Any]:
    variable = _require_exact_keys(
        value,
        keys=frozenset({"value", "confidence", "evidence_count"}),
        label=label,
    )
    if variable["confidence"] != 1 or variable["evidence_count"] != 1:
        raise LevEvalObservationError(f"{label} confidence/evidence_count is invalid")
    return variable


def _validate_measurements(
    raw: bytes,
    *,
    execution_id: str,
    suite_id: str,
    decided_at: str,
) -> int:
    if not raw:
        return 0
    lines = raw.splitlines()
    if len(lines) > _MAX_MEASUREMENTS:
        raise LevEvalObservationError("measurement line count exceeds the controller bound")
    for index, line in enumerate(lines, start=1):
        measurement = _parse_object(line, f"measurement line {index}")
        required = frozenset(
            {
                "schema",
                "measurement_id",
                "evaluator_id",
                "evaluator_version",
                "subject_ref",
                "generation",
                "variables",
                "provenance",
                "evidence_refs",
                "status",
                "measured_at",
            }
        )
        if set(measurement) != required:
            raise LevEvalObservationError(f"measurement line {index} keys mismatch")
        if (
            measurement["schema"] != "lev.measurement.v1"
            or measurement["evaluator_id"] != "eval_suite_runner"
            or measurement["evaluator_version"] != "1"
            or measurement["subject_ref"] != f"eval-suite:{suite_id}"
            or measurement["provenance"] != "runtime_fact"
            or measurement["status"] != "measured"
            or measurement["measured_at"] != decided_at
        ):
            raise LevEvalObservationError(
                f"measurement line {index} fixed fields do not bind the decision"
            )
        if measurement["generation"] != index:
            raise LevEvalObservationError("measurement generations are not contiguous")
        variables = measurement["variables"]
        if not isinstance(variables, dict):
            raise LevEvalObservationError(f"measurement line {index} variables are invalid")
        for name in ("case_id", "case_kind", "case_status", "passed", "diagnostic_count"):
            if name not in variables:
                raise LevEvalObservationError(
                    f"measurement line {index} lacks {name}"
                )
        case_id = _variable(variables["case_id"], f"measurement {index} case_id")["value"]
        case_kind = _variable(variables["case_kind"], f"measurement {index} case_kind")["value"]
        case_status = _variable(variables["case_status"], f"measurement {index} case_status")["value"]
        passed = _variable(variables["passed"], f"measurement {index} passed")["value"]
        _require_nonnegative_int(
            _variable(
                variables["diagnostic_count"],
                f"measurement {index} diagnostic_count",
            )["value"],
            f"measurement {index} diagnostic_count value",
        )
        if (
            not isinstance(case_id, str)
            or case_kind not in {"trace", "command"}
            or case_status not in {"passed", "failed", "blocked", "unavailable"}
            or type(passed) is not bool
            or passed != (case_status == "passed")
        ):
            raise LevEvalObservationError(f"measurement line {index} case variables are invalid")
        expected_measurement_id = (
            "measurement:eval_suite_runner:"
            + execution_id
            + ":"
            + case_kind
            + ":"
            + _sha256(_js_json_bytes(case_id))[:16]
        )
        if measurement["measurement_id"] != expected_measurement_id:
            raise LevEvalObservationError(f"measurement line {index} id mismatch")
        refs = _require_list(measurement["evidence_refs"], f"measurement {index} refs")
        if refs != [
            {
                "kind": "measurement",
                "ref": expected_measurement_id,
                "exists": True,
            }
        ]:
            raise LevEvalObservationError(f"measurement line {index} evidence refs mismatch")
    return len(lines)


def _validate_projection(value: dict[str, Any]) -> None:
    expected = {
        "schema": "lev.telemetry.measurement_series_projection.v1",
        "projection_name": "MeasurementSeries",
        "projection_ref": None,
        "deferred": True,
        "reason": "measurement_stream_not_materialized",
        "measurements": [],
        "forward_obligation": {
            "owner_package": "core/execution-ledger",
            "missing_contract": "append_only_measurement_stream_read_contract",
            "required_shape": "materialized Measurement stream reader over ledger Measurement facts",
        },
    }
    if value != expected:
        raise LevEvalObservationError(
            "measurement-series projection is not the fixed deferred Lev v1 shape"
        )


def _validate_seal(
    value: dict[str, Any],
    *,
    source_root: Path,
    execution_id: str,
    suite_id: str,
    decision_id: str,
    decision_digests: dict[str, Any],
    decided_at: str,
    run_status: str,
    verdict: str | None,
) -> str:
    keys = frozenset(
        {
            "schema",
            "execution_id",
            "intent_ref",
            "sealed_at",
            "action_ids",
            "outcome",
            "obligations",
            "verdict_refs",
            "evidence_refs",
            "measurement_stream_ref",
            "policy_refs",
        }
    )
    seal = _require_exact_keys(value, keys=keys, label="seal.json")
    if seal["schema"] != "lev.run_seal.v1" or seal["execution_id"] != execution_id:
        raise LevEvalObservationError("seal schema or execution_id mismatch")
    if seal["sealed_at"] != decided_at:
        raise LevEvalObservationError("seal timestamp does not bind the decision")
    intent = _require_exact_keys(
        seal["intent_ref"],
        keys=frozenset({"uri", "adapter", "content_hash"}),
        label="seal intent_ref",
    )
    if (
        intent["uri"] != f"eval-decision:{decision_id}"
        or intent["adapter"] != "core/eval"
        or intent["content_hash"] != _sha256(_js_json_bytes(decision_digests))
    ):
        raise LevEvalObservationError("seal intent_ref does not bind the decision")
    if seal["action_ids"] != [] or seal["policy_refs"] != []:
        raise LevEvalObservationError("seal action or policy refs are not the v1 eval writer shape")
    expected_outcome = (
        "close_incomplete"
        if verdict is None
        else "dry_run_success"
        if verdict == "pass" and run_status == "passed"
        else "failed"
    )
    if seal["outcome"] != expected_outcome:
        raise LevEvalObservationError("seal outcome disagrees with run and decision")
    if seal["verdict_refs"] != [decision_id]:
        raise LevEvalObservationError("seal verdict refs do not bind the decision")
    obligations = _require_list(seal["obligations"], "seal obligations")
    if obligations != [
        {
            "obligation_id": suite_id,
            "declared_at": decided_at,
            "verdict_ref": decision_id,
        }
    ]:
        raise LevEvalObservationError("seal obligations do not bind the decision")
    _absolute_ref(
        seal["measurement_stream_ref"],
        expected=source_root / "measurements.jsonl",
        label="seal measurement_stream_ref",
    )
    expected_refs = [
        {"kind": "artifact", "ref": str(source_root / "run.json"), "exists": True},
        {"kind": "measurement", "ref": str(source_root / "measurements.jsonl"), "exists": True},
        {"kind": "verdict", "ref": str(source_root / "decision.json"), "exists": True},
    ]
    if seal["evidence_refs"] != expected_refs:
        raise LevEvalObservationError("seal evidence refs do not bind the selected run")
    return expected_outcome


def _source_file_rows(snapshot: dict[str, bytes]) -> list[dict[str, Any]]:
    return [
        {
            "name": relative_name,
            "sha256": _sha256(snapshot[relative_name]),
            "bytes": len(snapshot[relative_name]),
        }
        for relative_name in _SOURCE_FILES
    ]


def _snapshot_sha256(source_files: list[dict[str, Any]]) -> str:
    return _sha256(canonical_json(source_files))


def _observation_receipt_body(
    *,
    snapshot: dict[str, bytes],
    source_root: Path,
    binding: LevEvalObservationBinding | None,
) -> dict[str, Any]:
    """Recompute every checkable relationship from retained raw bytes."""

    if set(snapshot) != set(_SOURCE_FILES):
        raise LevEvalObservationHoldError("foreign snapshot file set is invalid")
    run = _parse_object(snapshot["run.json"], "run.json")
    decision = _parse_object(snapshot["decision.json"], "decision.json")
    projection = _parse_object(
        snapshot["measurement-series/projection.json"],
        "measurement-series/projection.json",
    )
    seal = _parse_object(snapshot["seal.json"], "seal.json")
    execution_id, suite_id, evidence_refs, diagnostics = _validate_run(
        run,
        source_root=source_root,
    )
    decision_id, verdict, decided_at, decision_digests = _validate_decision(
        decision,
        execution_id=execution_id,
        suite_id=suite_id,
        run_evidence_refs=evidence_refs,
        run_diagnostics=diagnostics,
    )
    measurement_count = _validate_measurements(
        snapshot["measurements.jsonl"],
        execution_id=execution_id,
        suite_id=suite_id,
        decided_at=decided_at,
    )
    _validate_projection(projection)
    seal_outcome = _validate_seal(
        seal,
        source_root=source_root,
        execution_id=execution_id,
        suite_id=suite_id,
        decision_id=decision_id,
        decision_digests=decision_digests,
        decided_at=decided_at,
        run_status=run["status"],
        verdict=verdict,
    )
    source_files = _source_file_rows(snapshot)
    receipt: dict[str, Any] = {
        "schema": _SCHEMA,
        "foreign_observation": {
            "claimed_kind": "lev.eval.run.bundle.v1",
            "source_run_dir_text_sha256": _sha256(
                str(source_root).encode("utf-8")
            ),
            "files": source_files,
            "snapshot_sha256": _snapshot_sha256(source_files),
            "producer_authenticated": False,
            "foreign_decision_authority": False,
            "foreign_claim_gate_authenticated": False,
        },
        "observed": {
            "execution_id": execution_id,
            "suite_id": suite_id,
            "run_status": run["status"],
            "decision_status": decision["status"],
            "decision_verdict": verdict,
            "decision_reason_code": decision["reason_code"],
            "seal_outcome": seal_outcome,
            "measurement_count": measurement_count,
            "measurement_series_state": "deferred_not_materialized",
        },
        "verified_bindings": [
            "run_refs_bind_selected_directory",
            "decision_ids_and_available_input_digests",
            "measurement_generation_identity_and_timestamp",
            "deferred_projection_shape",
            "seal_intent_obligations_evidence_and_outcome",
        ],
        "unrecomputed_foreign_digests": list(_UNRECOMPUTED_DIGESTS),
        "claim_ceiling": _CLAIM_CEILING,
        "promotion_allowed": False,
    }
    if binding is not None:
        binding.assert_source_binding(source_root)
        binding.assert_profile_current()
        if (
            execution_id != binding.expected_execution_id
            or suite_id != binding.expected_suite_id
        ):
            raise LevEvalObservationHoldError(
                "foreign run identifiers do not match the controller binding"
            )
        receipt["controller_binding"] = binding.as_dict()
    return receipt


def _observation_snapshot_from_directory(
    observation_root: Path,
) -> dict[str, bytes]:
    return _snapshot_directory_bytes(observation_root / _FOREIGN_DIRECTORY)


def _retained_source_root(snapshot: dict[str, bytes]) -> Path:
    """Recover the path text needed only to recheck retained Lev references."""

    run = _parse_object(snapshot["run.json"], "retained run.json")
    return _resolved_absolute_path(run.get("run_dir"), "retained run_dir")


def _validate_observation_layout(observation_root: Path) -> None:
    """Require the exact retained snapshot tree and no link-shaped escape."""

    try:
        root_metadata = observation_root.lstat()
    except OSError as exc:
        raise LevEvalObservationHoldError(
            "observation run directory is unavailable"
        ) from exc
    if observation_root.is_symlink() or stat.S_ISLNK(root_metadata.st_mode):
        raise LevEvalObservationHoldError(
            "observation run directory must not be a symlink"
        )
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise LevEvalObservationHoldError("observation run directory is not a directory")
    discovered: set[str] = set()
    try:
        descendants = list(observation_root.rglob("*"))
    except OSError as exc:
        raise LevEvalObservationHoldError(
            "observation run directory could not be enumerated"
        ) from exc
    for candidate in descendants:
        try:
            metadata = candidate.lstat()
        except OSError as exc:
            raise LevEvalObservationHoldError(
                "observation snapshot changed during enumeration"
            ) from exc
        relative_name = candidate.relative_to(observation_root).as_posix()
        if candidate.is_symlink() or stat.S_ISLNK(metadata.st_mode):
            raise LevEvalObservationHoldError(
                f"observation snapshot contains a symlink: {relative_name}"
            )
        if stat.S_ISDIR(metadata.st_mode):
            continue
        if not stat.S_ISREG(metadata.st_mode):
            raise LevEvalObservationHoldError(
                f"observation snapshot contains a non-regular entry: {relative_name}"
            )
        discovered.add(relative_name)
    expected = {
        _RECEIPT_NAME,
        *(
            f"{_FOREIGN_DIRECTORY}/{relative_name}"
            for relative_name in _SOURCE_FILES
        ),
    }
    if discovered != expected:
        raise LevEvalObservationHoldError(
            "observation snapshot membership differs from the fixed contract"
        )


def _create_empty_child_directory(parent_fd: int, name: str, label: str) -> int:
    """Create and pin one controller-owned directory beneath a pinned parent."""

    try:
        os.mkdir(name, 0o700, dir_fd=parent_fd)
    except FileExistsError as exc:
        raise LevEvalObservationHoldError(
            f"observation directory already exists: {label}"
        ) from exc
    except OSError as exc:
        raise LevEvalObservationHoldError(
            f"observation directory could not be created: {label}"
        ) from exc
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise LevEvalObservationHoldError(
            f"observation directory could not be pinned: {label}"
        ) from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISDIR(metadata.st_mode):
            raise LevEvalObservationHoldError(
                f"observation directory is not a directory: {label}"
            )
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _persist_file_exclusive(
    *,
    parent_fd: int,
    name: str,
    value: bytes,
    label: str,
) -> None:
    """Write one exact leaf through an already-pinned output directory."""

    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(name, flags, 0o600, dir_fd=parent_fd)
    except FileExistsError as exc:
        raise LevEvalObservationHoldError(
            f"observation artifact already exists: {label}"
        ) from exc
    except OSError as exc:
        raise LevEvalObservationHoldError(
            f"observation artifact persistence failed: {label}"
        ) from exc
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            written = handle.write(value)
            if written != len(value):
                raise LevEvalObservationHoldError(
                    f"observation artifact short write: {label}"
                )
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise LevEvalObservationHoldError(
            f"observation artifact persistence failed: {label}"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _persist_observation_snapshot(
    *,
    destination: Path,
    snapshot: dict[str, bytes],
    receipt: bytes,
) -> None:
    """Persist the fixed tree using descriptor-relative writes only."""

    destination_fd = _open_real_directory(
        destination,
        "observation run directory",
    )
    foreign_fd = -1
    series_fd = -1
    try:
        foreign_fd = _create_empty_child_directory(
            destination_fd,
            _FOREIGN_DIRECTORY,
            _FOREIGN_DIRECTORY,
        )
        series_fd = _create_empty_child_directory(
            foreign_fd,
            "measurement-series",
            "measurement-series",
        )
        for relative_name in (
            "run.json",
            "decision.json",
            "measurements.jsonl",
            "seal.json",
        ):
            _persist_file_exclusive(
                parent_fd=foreign_fd,
                name=relative_name,
                value=snapshot[relative_name],
                label=relative_name,
            )
        _persist_file_exclusive(
            parent_fd=series_fd,
            name="projection.json",
            value=snapshot["measurement-series/projection.json"],
            label="measurement-series/projection.json",
        )
        _persist_file_exclusive(
            parent_fd=destination_fd,
            name=_RECEIPT_NAME,
            value=receipt,
            label=_RECEIPT_NAME,
        )
        os.fsync(series_fd)
        os.fsync(foreign_fd)
        os.fsync(destination_fd)
    except OSError as exc:
        raise LevEvalObservationHoldError(
            "observation directory fsync failed"
        ) from exc
    finally:
        if series_fd >= 0:
            os.close(series_fd)
        if foreign_fd >= 0:
            os.close(foreign_fd)
        os.close(destination_fd)


def observe_lev_eval_bundle(
    *,
    source_run_dir: Path,
    observation_run_dir: Path,
    binding: LevEvalObservationBinding | None = None,
) -> LevEvalObservation:
    """Snapshot and cross-check one current Lev v1 eval artifact bundle.

    ``source_run_dir`` is foreign input.  The caller selects it outside the
    adapter, and this function neither executes nor authenticates Lev.  v1
    requires absolute in-bundle references because that is the only safe
    resolution basis available without importing a Lev project/runtime.
    ``observation_run_dir`` must not exist, making retention non-overwriting.
    """

    if binding is not None and type(binding) is not LevEvalObservationBinding:
        raise LevEvalObservationHoldError(
            "observation binding is not the fixed controller binding type"
        )
    supplied_source = Path(source_run_dir).expanduser()
    if supplied_source.is_symlink():
        raise LevEvalObservationHoldError(
            "source run directory must not be a symlink"
        )
    try:
        source_root = supplied_source.resolve(strict=True)
    except OSError as exc:
        raise LevEvalObservationError("source run directory is unavailable") from exc
    if not source_root.is_dir():
        raise LevEvalObservationError("source run directory is not a directory")
    supplied_destination = Path(observation_run_dir).expanduser()
    if supplied_destination.is_symlink():
        raise LevEvalObservationHoldError(
            "observation run directory must not be a symlink"
        )
    destination = supplied_destination.resolve(strict=False)
    if destination == source_root or source_root in destination.parents:
        raise LevEvalObservationHoldError(
            "observation run directory must be outside the source run"
        )
    if destination.exists():
        raise LevEvalObservationHoldError("observation run directory already exists")
    if binding is not None:
        binding.assert_source_binding(source_root)
        binding.assert_profile_current()

    snapshot = _snapshot_directory_bytes(source_root)
    receipt = _observation_receipt_body(
        snapshot=snapshot,
        source_root=source_root,
        binding=binding,
    )
    receipt_sha256 = _sha256(canonical_json(receipt))
    receipt_with_digest = {**receipt, "receipt_sha256": receipt_sha256}

    try:
        destination.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise LevEvalObservationHoldError(
            "observation run directory already exists"
        ) from exc
    except OSError as exc:
        raise LevEvalObservationHoldError(
            "observation run directory could not be created"
        ) from exc
    receipt_path = destination / _RECEIPT_NAME
    _persist_observation_snapshot(
        destination=destination,
        snapshot=snapshot,
        receipt=canonical_json(receipt_with_digest),
    )
    return LevEvalObservation(
        observation_run_dir=destination,
        receipt_path=receipt_path,
        receipt_sha256=receipt_sha256,
        receipt=receipt_with_digest,
    )


def verify_lev_eval_observation_snapshot(
    *,
    observation_run_dir: Path,
    expected_binding: LevEvalObservationBinding,
    expected_receipt_sha256: str,
) -> LevEvalObservation:
    """Replay one retained CB snapshot without reading the mutable Lev source.

    The original foreign directory is intentionally not opened here.  The
    controller binding provides only its resolved-text digest and expected
    identifiers; all structural work is performed on the CB-owned raw copy.
    """

    if type(expected_binding) is not LevEvalObservationBinding:
        raise LevEvalObservationHoldError(
            "replay binding is not the fixed controller binding type"
        )
    _require_sha256(expected_receipt_sha256, "expected observation receipt_sha256")
    supplied_root = Path(observation_run_dir).expanduser()
    if supplied_root.is_symlink():
        raise LevEvalObservationHoldError(
            "replay observation run directory must not be a symlink"
        )
    try:
        observation_root = supplied_root.resolve(strict=True)
    except OSError as exc:
        raise LevEvalObservationHoldError(
            "replay observation run directory is unavailable"
        ) from exc
    _validate_observation_layout(observation_root)
    expected_binding.assert_profile_current()
    try:
        snapshot = _observation_snapshot_from_directory(observation_root)
        retained_source_root = _retained_source_root(snapshot)
        expected_receipt = _observation_receipt_body(
            snapshot=snapshot,
            source_root=retained_source_root,
            binding=expected_binding,
        )
    except LevEvalObservationHoldError:
        raise
    except LevEvalObservationError as exc:
        raise LevEvalObservationHoldError(
            "retained foreign snapshot no longer satisfies the fixed contract"
        ) from exc
    computed_sha256 = _sha256(canonical_json(expected_receipt))
    if computed_sha256 != expected_receipt_sha256:
        raise LevEvalObservationHoldError(
            "retained observation receipt digest differs from the controller binding"
        )
    receipt_path = observation_root / _RECEIPT_NAME
    try:
        raw_receipt = _source_file_bytes(observation_root, _RECEIPT_NAME)
        actual_receipt = _parse_object(raw_receipt, "retained observation receipt")
    except LevEvalObservationHoldError:
        raise
    except LevEvalObservationError as exc:
        raise LevEvalObservationHoldError(
            "retained observation receipt is unavailable or malformed"
        ) from exc
    expected_with_digest = {
        **expected_receipt,
        "receipt_sha256": computed_sha256,
    }
    if actual_receipt != expected_with_digest:
        raise LevEvalObservationHoldError(
            "retained observation receipt does not replay from its raw snapshot"
        )
    if raw_receipt != canonical_json(expected_with_digest):
        raise LevEvalObservationHoldError(
            "retained observation receipt is not exclusively canonical"
        )
    return LevEvalObservation(
        observation_run_dir=observation_root,
        receipt_path=receipt_path,
        receipt_sha256=computed_sha256,
        receipt=expected_with_digest,
    )
