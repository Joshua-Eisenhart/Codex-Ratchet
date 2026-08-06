"""Strict execution-ownership leases for the future Mini-Lev runtime.

This module is deliberately separate from :mod:`constraintbox.lease`.
``constraintbox.lease`` binds evidence to a staged Git tree.  An execution
lease only establishes temporary, exclusive ownership of one controller-bound
run/node operation.  It never authorizes an output, claim, transition, or
release from ConstraintBox.

The semantic clock is supplied by the controller as ``ClockSample``.  Its
``tick_ns`` must come from one monotonic clock domain named by ``clock_id``.
Wall-clock time is neither read nor stored here.  A different clock domain or
a tick below the last state-changing observation fails closed.  Exact expiry
is expired: ``tick_ns < expires_tick_ns`` is required.

The store serializes read/modify/write operations with a POSIX advisory lock.
It retains a permanent initialized-slot marker and a high-water head beside
the canonical state.  State and head are each atomically replaced after their
temporary files are fsynced; interruption between the two replacements
produces a mismatch that fails closed.  The current token is rotated by every
heartbeat.  This detects deleted state, stale-token use, and state/token
rollback while the high-water head is retained.  It is not a signature or an
external trust root, and cannot defeat an attacker who can roll back the
slot marker, state, retained head, and controller token together.  The
canonical parent directory is part of the trusted controller substrate:
non-cooperating processes with permission to replace that directory or ignore
its advisory lock are outside this primitive's containment boundary.
"""

from __future__ import annotations

import errno
import fcntl
import hashlib
import hmac
import math
import os
import re
import secrets
import stat
import tempfile
import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterator

from .intake import IntakeError, canonical_json, parse_json_object


EXECUTION_LEASE_SCHEMA = "constraintbox.execution-lease-state.v1"
EXECUTION_LEASE_TOKEN_SCHEMA = "constraintbox.execution-lease-token.v1"
EXECUTION_LEASE_SLOT_SCHEMA = "constraintbox.execution-lease-slot.v1"
EXECUTION_LEASE_HEAD_SCHEMA = "constraintbox.execution-lease-head.v1"
GENESIS_SHA256 = "0" * 64

MAX_STATE_BYTES = 16 * 1024
MAX_CONTROL_BYTES = 4 * 1024
MAX_IDENTIFIER_BYTES = 160
MAX_TTL_NS = 24 * 60 * 60 * 1_000_000_000
MAX_TICK_NS = (1 << 63) - 1
DEFAULT_LOCK_TIMEOUT_SECONDS = 5.0

CLOCK_CONTRACT = (
    "The controller supplies a non-negative monotonic tick_ns and a stable "
    "clock_id for one clock domain. Wall time is not consulted. A sample from "
    "another clock_id, a tick below the last state-changing sample, or a tick "
    "at/after expires_tick_ns fails closed."
)

_AUTHORITY = {
    "purpose": "execution_ownership_only",
    "authorizes_output_release": False,
    "authorizes_transition": False,
}
_AUTHORITY_KEYS = frozenset(_AUTHORITY)
_IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]*\Z")
_HEX64_RE = re.compile(r"[0-9a-f]{64}\Z")
_RECORD_KEYS = frozenset(
    {
        "schema",
        "authority",
        "event",
        "status",
        "lease_id",
        "binding",
        "binding_sha256",
        "clock_id",
        "acquired_tick_ns",
        "observed_tick_ns",
        "expires_tick_ns",
        "ttl_ns",
        "generation",
        "nonce_sha256",
        "previous_record_sha256",
        "release_cause",
        "record_sha256",
    }
)
_BINDING_KEYS = frozenset(
    {
        "owner_id",
        "run_id",
        "node_id",
        "visit",
        "slot_sha256",
        "flow_sha256",
        "policy_sha256",
        "runtime_sha256",
        "instruction_sha256",
    }
)
_SLOT_KEYS = frozenset(
    {
        "schema",
        "authority",
        "slot_sha256",
        "slot_record_sha256",
    }
)
_HEAD_KEYS = frozenset(
    {
        "schema",
        "slot_sha256",
        "generation",
        "record_sha256",
        "head_sha256",
    }
)
_TOKEN_KEYS = frozenset(
    {
        "schema",
        "lease_id",
        "binding_sha256",
        "generation",
        "record_sha256",
        "nonce",
    }
)
_ACTIVE_EVENTS = frozenset(
    {"ACQUIRED", "ACQUIRED_AFTER_EXPIRY", "ACQUIRED_AFTER_RELEASE", "HEARTBEAT"}
)


class ExecutionLeaseError(RuntimeError):
    """Base error for an execution-lease operation."""


class ExecutionLeaseConflict(ExecutionLeaseError):
    """A new owner cannot acquire the currently active state."""


class ExecutionLeaseRejected(ExecutionLeaseError):
    """A heartbeat or release did not present a currently valid token."""

    def __init__(self, verdict: "LeaseVerdict"):
        super().__init__(f"{verdict.status.value}: {verdict.reason}")
        self.verdict = verdict


class ExecutionLeaseStateError(ExecutionLeaseError):
    """The durable state is malformed, ambiguous, or unsafe to read."""


class ExecutionLeaseLockError(ExecutionLeaseError):
    """The controller could not obtain the store transaction lock."""


class ExecutionLeasePersistenceError(ExecutionLeaseError):
    """A durable state replacement failed.

    ``state_may_have_changed`` is true only when ``os.replace`` completed and
    a later durability operation failed.  In that case the caller must not
    reuse its prior token without a fresh verification.
    """

    def __init__(self, message: str, *, state_may_have_changed: bool):
        super().__init__(message)
        self.state_may_have_changed = state_may_have_changed


class VerificationStatus(str, Enum):
    VALID = "VALID"
    ABSENT = "ABSENT"
    MALFORMED = "MALFORMED"
    IDENTITY_MISMATCH = "IDENTITY_MISMATCH"
    TOKEN_MISMATCH = "TOKEN_MISMATCH"
    CLOCK_MISMATCH = "CLOCK_MISMATCH"
    CLOCK_ROLLBACK = "CLOCK_ROLLBACK"
    EXPIRED = "EXPIRED"
    RELEASED = "RELEASED"


class ReleaseCause(str, Enum):
    """Why execution ownership ended, not an output disposition."""

    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PARKED = "PARKED"


@dataclass(frozen=True)
class LeaseVerdict:
    status: VerificationStatus
    reason: str
    record_sha256: str | None = None

    def __bool__(self) -> bool:
        raise TypeError(
            "LeaseVerdict is not a boolean; compare .status explicitly "
            f"(got {self.status.value})"
        )


def _require_identifier(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    try:
        encoded = value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be ASCII") from exc
    if not encoded or len(encoded) > MAX_IDENTIFIER_BYTES:
        raise ValueError(
            f"{name} must contain 1..{MAX_IDENTIFIER_BYTES} ASCII bytes"
        )
    if _IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{name} contains a disallowed character")
    return value


def _require_sha256(name: str, value: Any) -> str:
    if not isinstance(value, str) or _HEX64_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be 64 lowercase hexadecimal characters")
    return value


def _require_plain_int(name: str, value: Any, *, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be in [{minimum}, {maximum}]")
    return value


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], name: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(f"{name} keys differ: missing={missing}, extra={extra}")


@dataclass(frozen=True)
class ExecutionLeaseBinding:
    """Controller-owned identity for exactly one executable node."""

    owner_id: str
    run_id: str
    node_id: str
    visit: int
    slot_sha256: str
    flow_sha256: str
    policy_sha256: str
    runtime_sha256: str
    instruction_sha256: str

    def __post_init__(self) -> None:
        _require_identifier("owner_id", self.owner_id)
        _require_identifier("run_id", self.run_id)
        _require_identifier("node_id", self.node_id)
        _require_plain_int(
            "visit", self.visit, minimum=1, maximum=MAX_TICK_NS
        )
        _require_sha256("slot_sha256", self.slot_sha256)
        _require_sha256("flow_sha256", self.flow_sha256)
        _require_sha256("policy_sha256", self.policy_sha256)
        _require_sha256("runtime_sha256", self.runtime_sha256)
        _require_sha256("instruction_sha256", self.instruction_sha256)

    def as_dict(self) -> dict[str, Any]:
        return {
            "owner_id": self.owner_id,
            "run_id": self.run_id,
            "node_id": self.node_id,
            "visit": self.visit,
            "slot_sha256": self.slot_sha256,
            "flow_sha256": self.flow_sha256,
            "policy_sha256": self.policy_sha256,
            "runtime_sha256": self.runtime_sha256,
            "instruction_sha256": self.instruction_sha256,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "ExecutionLeaseBinding":
        if not isinstance(value, dict):
            raise ValueError("binding must be an object")
        _require_exact_keys(value, _BINDING_KEYS, "binding")
        return cls(
            owner_id=value["owner_id"],
            run_id=value["run_id"],
            node_id=value["node_id"],
            visit=value["visit"],
            slot_sha256=value["slot_sha256"],
            flow_sha256=value["flow_sha256"],
            policy_sha256=value["policy_sha256"],
            runtime_sha256=value["runtime_sha256"],
            instruction_sha256=value["instruction_sha256"],
        )

    @property
    def sha256(self) -> str:
        return hashlib.sha256(canonical_json(self.as_dict())).hexdigest()


@dataclass(frozen=True)
class ClockSample:
    clock_id: str
    tick_ns: int

    def __post_init__(self) -> None:
        _require_identifier("clock_id", self.clock_id)
        _require_plain_int(
            "tick_ns", self.tick_ns, minimum=0, maximum=MAX_TICK_NS
        )


@dataclass(frozen=True)
class ExecutionLeaseToken:
    """Secret controller capability for the current lease generation."""

    lease_id: str
    binding_sha256: str
    generation: int
    record_sha256: str
    nonce: str

    def __post_init__(self) -> None:
        _require_sha256("lease_id", self.lease_id)
        _require_sha256("binding_sha256", self.binding_sha256)
        _require_plain_int(
            "generation", self.generation, minimum=1, maximum=MAX_TICK_NS
        )
        _require_sha256("record_sha256", self.record_sha256)
        _require_sha256("nonce", self.nonce)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": EXECUTION_LEASE_TOKEN_SCHEMA,
            "lease_id": self.lease_id,
            "binding_sha256": self.binding_sha256,
            "generation": self.generation,
            "record_sha256": self.record_sha256,
            "nonce": self.nonce,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "ExecutionLeaseToken":
        if not isinstance(value, dict):
            raise ValueError("token must be an object")
        _require_exact_keys(value, _TOKEN_KEYS, "token")
        if value["schema"] != EXECUTION_LEASE_TOKEN_SCHEMA:
            raise ValueError("token schema mismatch")
        return cls(
            lease_id=value["lease_id"],
            binding_sha256=value["binding_sha256"],
            generation=value["generation"],
            record_sha256=value["record_sha256"],
            nonce=value["nonce"],
        )


@dataclass(frozen=True)
class LeaseGrant:
    token: ExecutionLeaseToken
    receipt: dict[str, Any]


def _record_digest(record: dict[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    return hashlib.sha256(canonical_json(body)).hexdigest()


def _slot_record_digest(record: dict[str, Any]) -> str:
    body = {
        key: value for key, value in record.items() if key != "slot_record_sha256"
    }
    return hashlib.sha256(canonical_json(body)).hexdigest()


def _head_digest(record: dict[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "head_sha256"}
    return hashlib.sha256(canonical_json(body)).hexdigest()


def _constant_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(left.encode("ascii"), right.encode("ascii"))


def _validate_authority(value: Any) -> None:
    if not isinstance(value, dict):
        raise ValueError("lease authority boundary must be an object")
    _require_exact_keys(value, _AUTHORITY_KEYS, "lease authority")
    if (
        value["purpose"] != "execution_ownership_only"
        or value["authorizes_output_release"] is not False
        or value["authorizes_transition"] is not False
    ):
        raise ValueError("lease authority boundary mismatch")


def _validate_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("lease state must be an object")
    _require_exact_keys(value, _RECORD_KEYS, "lease state")
    if value["schema"] != EXECUTION_LEASE_SCHEMA:
        raise ValueError("lease state schema mismatch")
    _validate_authority(value["authority"])

    event = value["event"]
    status = value["status"]
    release_cause = value["release_cause"]
    nonce_sha256 = value["nonce_sha256"]
    if not isinstance(event, str) or not isinstance(status, str):
        raise ValueError("event and status must be strings")
    if release_cause is not None and not isinstance(release_cause, str):
        raise ValueError("release_cause must be a string or null")
    if event in _ACTIVE_EVENTS:
        if status != "ACTIVE" or release_cause is not None:
            raise ValueError("active event has inconsistent status")
        _require_sha256("nonce_sha256", nonce_sha256)
    elif event == "RELEASED":
        if status != "RELEASED" or release_cause not in {
            cause.value for cause in ReleaseCause
        }:
            raise ValueError("release event has inconsistent status or cause")
        if nonce_sha256 is not None:
            raise ValueError("released state must not retain a nonce digest")
    else:
        raise ValueError("unknown execution-lease event")

    binding = ExecutionLeaseBinding.from_dict(value["binding"])
    _require_sha256("binding_sha256", value["binding_sha256"])
    if not _constant_equal(binding.sha256, value["binding_sha256"]):
        raise ValueError("binding digest mismatch")
    _require_sha256("lease_id", value["lease_id"])
    _require_identifier("clock_id", value["clock_id"])
    acquired = _require_plain_int(
        "acquired_tick_ns", value["acquired_tick_ns"], minimum=0, maximum=MAX_TICK_NS
    )
    observed = _require_plain_int(
        "observed_tick_ns", value["observed_tick_ns"], minimum=0, maximum=MAX_TICK_NS
    )
    expires = _require_plain_int(
        "expires_tick_ns", value["expires_tick_ns"], minimum=1, maximum=MAX_TICK_NS
    )
    ttl_ns = _require_plain_int(
        "ttl_ns", value["ttl_ns"], minimum=1, maximum=MAX_TTL_NS
    )
    _require_plain_int(
        "generation", value["generation"], minimum=1, maximum=MAX_TICK_NS
    )
    _require_sha256("previous_record_sha256", value["previous_record_sha256"])
    _require_sha256("record_sha256", value["record_sha256"])
    if observed < acquired:
        raise ValueError("observed tick precedes acquisition")
    if status == "ACTIVE" and expires != observed + ttl_ns:
        raise ValueError("active expiry does not equal observed tick plus fixed TTL")
    if status == "RELEASED" and observed >= expires:
        raise ValueError("released state was closed at or after expiry")
    actual_digest = _record_digest(value)
    if not _constant_equal(actual_digest, value["record_sha256"]):
        raise ValueError("record digest mismatch")
    return value


def validate_execution_lease_receipt(value: Any) -> dict[str, Any]:
    """Validate and copy one nonce-free public lease record.

    Mini-Lev receipts retain the acquire/release records that were current at
    hook execution time.  The durable slot necessarily advances on later
    executions, so replay must validate those retained records rather than
    trust the store's *current* state.  This public helper deliberately
    accepts only the state-record schema; it cannot deserialize or expose an
    :class:`ExecutionLeaseToken` or its nonce.
    """

    if not isinstance(value, dict):
        raise ValueError("execution-lease receipt must be an object")
    record = dict(value)
    _validate_record(record)
    return record


def _validate_slot_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("slot marker must be an object")
    _require_exact_keys(value, _SLOT_KEYS, "slot marker")
    if value["schema"] != EXECUTION_LEASE_SLOT_SCHEMA:
        raise ValueError("slot marker schema mismatch")
    _validate_authority(value["authority"])
    _require_sha256("slot_sha256", value["slot_sha256"])
    _require_sha256("slot_record_sha256", value["slot_record_sha256"])
    if not _constant_equal(_slot_record_digest(value), value["slot_record_sha256"]):
        raise ValueError("slot marker digest mismatch")
    return value


def _validate_head(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("retained head must be an object")
    _require_exact_keys(value, _HEAD_KEYS, "retained head")
    if value["schema"] != EXECUTION_LEASE_HEAD_SCHEMA:
        raise ValueError("retained head schema mismatch")
    _require_sha256("slot_sha256", value["slot_sha256"])
    _require_plain_int(
        "generation", value["generation"], minimum=1, maximum=MAX_TICK_NS
    )
    _require_sha256("record_sha256", value["record_sha256"])
    _require_sha256("head_sha256", value["head_sha256"])
    if not _constant_equal(_head_digest(value), value["head_sha256"]):
        raise ValueError("retained head digest mismatch")
    return value


class ExecutionLeaseStore:
    """A single-slot durable execution-ownership store.

    Use one controller-selected path per dynamic execution slot.  The
    canonical path is hashed as ``slot_sha256`` and must appear in the binding,
    preventing one binding from validating in two different stores.  All
    mutation methods take an advisory lock on the canonical parent directory,
    avoiding a replaceable sidecar-lock inode.  ``<state>.slot`` is a
    permanent initialized marker and ``<state>.head`` retains high water.
    The nonce is returned only in ``ExecutionLeaseToken`` and is never written
    to a public receipt.
    """

    def __init__(
        self,
        state_path: Path,
        *,
        lock_timeout_seconds: float = DEFAULT_LOCK_TIMEOUT_SECONDS,
    ):
        expanded = Path(state_path).expanduser()
        if not expanded.name or expanded.name in {".", ".."}:
            raise ValueError("state_path must name a file")
        canonical_parent = Path(
            os.path.realpath(os.path.abspath(os.fspath(expanded.parent)))
        )
        self.state_path = canonical_parent / expanded.name
        self.slot_path = self.state_path.with_name(self.state_path.name + ".slot")
        self.head_path = self.state_path.with_name(self.state_path.name + ".head")
        self.slot_sha256 = hashlib.sha256(
            canonical_json(
                {
                    "schema": EXECUTION_LEASE_SLOT_SCHEMA,
                    "state_path": os.fspath(self.state_path),
                }
            )
        ).hexdigest()
        if (
            isinstance(lock_timeout_seconds, bool)
            or not isinstance(lock_timeout_seconds, (int, float))
            or not math.isfinite(lock_timeout_seconds)
            or lock_timeout_seconds < 0
            or lock_timeout_seconds > 60
        ):
            raise ValueError("lock_timeout_seconds must be in [0, 60]")
        self.lock_timeout_seconds = float(lock_timeout_seconds)

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_RDONLY
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_DIRECTORY", 0)
        try:
            descriptor = os.open(self.state_path.parent, flags)
        except OSError as exc:
            raise ExecutionLeaseLockError(
                f"cannot open execution-lease directory lock: {exc}"
            ) from exc
        deadline = time.monotonic() + self.lock_timeout_seconds
        try:
            while True:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as exc:
                    if exc.errno not in (errno.EACCES, errno.EAGAIN):
                        raise ExecutionLeaseLockError(
                            f"cannot lock execution-lease store: {exc}"
                        ) from exc
                    if time.monotonic() >= deadline:
                        raise ExecutionLeaseLockError(
                            "timed out acquiring execution-lease lock"
                        ) from exc
                    time.sleep(0.005)
            yield
        finally:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    def _read_component_unlocked(
        self,
        path: Path,
        *,
        maximum_bytes: int,
        name: str,
        validator: Callable[[Any], dict[str, Any]],
    ) -> dict[str, Any] | None:
        flags = os.O_RDONLY
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise ExecutionLeaseStateError(
                f"cannot open execution-lease {name}: {exc}"
            ) from exc
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise ExecutionLeaseStateError(
                    f"execution-lease {name} is not a regular file"
                )
            if metadata.st_size > maximum_bytes:
                raise ExecutionLeaseStateError(
                    f"execution-lease {name} exceeds {maximum_bytes} bytes"
                )
            with os.fdopen(descriptor, "rb", closefd=False) as handle:
                raw = handle.read(maximum_bytes + 1)
            if len(raw) > maximum_bytes:
                raise ExecutionLeaseStateError(
                    f"execution-lease {name} exceeds {maximum_bytes} bytes"
                )
        finally:
            os.close(descriptor)
        try:
            parsed = parse_json_object(raw)
            validated = validator(parsed)
        except (IntakeError, TypeError, ValueError, RecursionError) as exc:
            raise ExecutionLeaseStateError(
                f"malformed execution-lease {name}: {exc}"
            ) from exc
        if raw != canonical_json(validated):
            raise ExecutionLeaseStateError(
                f"execution-lease {name} is not canonical JSON"
            )
        return validated

    def _read_unlocked(self) -> dict[str, Any] | None:
        slot = self._read_component_unlocked(
            self.slot_path,
            maximum_bytes=MAX_CONTROL_BYTES,
            name="slot marker",
            validator=_validate_slot_record,
        )
        state = self._read_component_unlocked(
            self.state_path,
            maximum_bytes=MAX_STATE_BYTES,
            name="state",
            validator=_validate_record,
        )
        head = self._read_component_unlocked(
            self.head_path,
            maximum_bytes=MAX_CONTROL_BYTES,
            name="retained head",
            validator=_validate_head,
        )
        components = (slot, state, head)
        if all(component is None for component in components):
            return None
        if any(component is None for component in components):
            raise ExecutionLeaseStateError(
                "initialized execution slot is missing marker, state, or retained head"
            )
        if slot is None or state is None or head is None:
            raise ExecutionLeaseStateError(
                "internal slot component narrowing failed"
            )
        if not _constant_equal(slot["slot_sha256"], self.slot_sha256):
            raise ExecutionLeaseStateError("slot marker belongs to another path")
        if not _constant_equal(
            state["binding"]["slot_sha256"], self.slot_sha256
        ):
            raise ExecutionLeaseStateError("lease state belongs to another slot")
        if not _constant_equal(head["slot_sha256"], self.slot_sha256):
            raise ExecutionLeaseStateError("retained head belongs to another slot")
        if (
            head["generation"] != state["generation"]
            or not _constant_equal(
                head["record_sha256"], state["record_sha256"]
            )
        ):
            raise ExecutionLeaseStateError(
                "lease state does not match retained high-water head"
            )
        return state

    def _fsync_directory_unlocked(self) -> None:
        descriptor = os.open(
            self.state_path.parent,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0),
        )
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _create_slot_marker_unlocked(self) -> None:
        marker = {
            "schema": EXECUTION_LEASE_SLOT_SCHEMA,
            "authority": dict(_AUTHORITY),
            "slot_sha256": self.slot_sha256,
            "slot_record_sha256": "",
        }
        marker["slot_record_sha256"] = _slot_record_digest(marker)
        _validate_slot_record(marker)
        payload = canonical_json(marker)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        created = False
        try:
            descriptor = os.open(self.slot_path, flags, 0o600)
            created = True
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            self._fsync_directory_unlocked()
        except OSError as exc:
            raise ExecutionLeasePersistenceError(
                f"cannot initialize execution slot marker: {exc}",
                state_may_have_changed=created,
            ) from exc

    def _stage_payload_unlocked(self, path: Path, payload: bytes) -> Path:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary = Path(temporary_name)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            try:
                os.close(descriptor)
            except OSError:
                pass
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return temporary

    def _write_unlocked(self, record: dict[str, Any]) -> None:
        _validate_record(record)
        payload = canonical_json(record)
        if len(payload) > MAX_STATE_BYTES:
            raise ExecutionLeasePersistenceError(
                "execution-lease state exceeds the configured byte limit",
                state_may_have_changed=False,
            )

        head = {
            "schema": EXECUTION_LEASE_HEAD_SCHEMA,
            "slot_sha256": self.slot_sha256,
            "generation": record["generation"],
            "record_sha256": record["record_sha256"],
            "head_sha256": "",
        }
        head["head_sha256"] = _head_digest(head)
        _validate_head(head)
        head_payload = canonical_json(head)
        if len(head_payload) > MAX_CONTROL_BYTES:
            raise ExecutionLeasePersistenceError(
                "execution-lease retained head exceeds the byte limit",
                state_may_have_changed=False,
            )

        state_temporary: Path | None = None
        head_temporary: Path | None = None
        replaced = False
        try:
            state_temporary = self._stage_payload_unlocked(
                self.state_path, payload
            )
            head_temporary = self._stage_payload_unlocked(
                self.head_path, head_payload
            )
            os.replace(state_temporary, self.state_path)
            replaced = True
            state_temporary = None
            os.replace(head_temporary, self.head_path)
            head_temporary = None
            self._fsync_directory_unlocked()
        except OSError as exc:
            for temporary in (state_temporary, head_temporary):
                if temporary is None:
                    continue
                try:
                    temporary.unlink(missing_ok=True)
                except OSError:
                    pass
            raise ExecutionLeasePersistenceError(
                f"cannot persist execution-lease state/head transaction: {exc}",
                state_may_have_changed=replaced,
            ) from exc

    @staticmethod
    def _new_nonce() -> str:
        nonce = secrets.token_hex(32)
        return _require_sha256("generated nonce", nonce)

    @staticmethod
    def _new_lease_id(
        *,
        binding: ExecutionLeaseBinding,
        clock: ClockSample,
        generation: int,
        nonce_sha256: str,
        previous_record_sha256: str,
    ) -> str:
        material = {
            "schema": EXECUTION_LEASE_SCHEMA,
            "binding": binding.as_dict(),
            "clock_id": clock.clock_id,
            "acquired_tick_ns": clock.tick_ns,
            "generation": generation,
            "nonce_sha256": nonce_sha256,
            "previous_record_sha256": previous_record_sha256,
        }
        return hashlib.sha256(canonical_json(material)).hexdigest()

    @staticmethod
    def _finish_record(body: dict[str, Any]) -> dict[str, Any]:
        record = {**body, "record_sha256": ""}
        record["record_sha256"] = _record_digest(record)
        _validate_record(record)
        return record

    @staticmethod
    def _token(record: dict[str, Any], nonce: str) -> ExecutionLeaseToken:
        return ExecutionLeaseToken(
            lease_id=record["lease_id"],
            binding_sha256=record["binding_sha256"],
            generation=record["generation"],
            record_sha256=record["record_sha256"],
            nonce=nonce,
        )

    def acquire(
        self,
        binding: ExecutionLeaseBinding,
        *,
        ttl_ns: int,
        clock: ClockSample,
    ) -> LeaseGrant:
        """Acquire an absent, released, or provably expired execution slot."""

        if not isinstance(binding, ExecutionLeaseBinding):
            raise TypeError("binding must be ExecutionLeaseBinding")
        if not isinstance(clock, ClockSample):
            raise TypeError("clock must be ClockSample")
        if not _constant_equal(binding.slot_sha256, self.slot_sha256):
            raise ValueError("binding slot_sha256 does not identify this store")
        ttl = _require_plain_int(
            "ttl_ns", ttl_ns, minimum=1, maximum=MAX_TTL_NS
        )
        if clock.tick_ns > MAX_TICK_NS - ttl:
            raise ValueError("tick_ns plus ttl_ns exceeds the supported clock range")

        with self._locked():
            current = self._read_unlocked()
            initialize_slot = current is None
            previous_sha256 = GENESIS_SHA256
            generation = 1
            event = "ACQUIRED"
            if current is not None:
                previous_sha256 = current["record_sha256"]
                generation = current["generation"] + 1
                if generation > MAX_TICK_NS:
                    raise ExecutionLeaseConflict("lease generation exhausted")
                if current["status"] == "ACTIVE":
                    if current["clock_id"] != clock.clock_id:
                        raise ExecutionLeaseConflict(
                            "active lease belongs to another clock domain"
                        )
                    if clock.tick_ns < current["observed_tick_ns"]:
                        raise ExecutionLeaseConflict(
                            "clock rollback cannot establish lease expiry"
                        )
                    if clock.tick_ns < current["expires_tick_ns"]:
                        raise ExecutionLeaseConflict(
                            "execution slot already has an unexpired owner"
                        )
                    event = "ACQUIRED_AFTER_EXPIRY"
                else:
                    if (
                        current["clock_id"] == clock.clock_id
                        and clock.tick_ns < current["observed_tick_ns"]
                    ):
                        raise ExecutionLeaseConflict(
                            "clock rollback cannot start a later lease generation"
                        )
                    event = "ACQUIRED_AFTER_RELEASE"

            nonce = self._new_nonce()
            nonce_sha256 = hashlib.sha256(nonce.encode("ascii")).hexdigest()
            lease_id = self._new_lease_id(
                binding=binding,
                clock=clock,
                generation=generation,
                nonce_sha256=nonce_sha256,
                previous_record_sha256=previous_sha256,
            )
            record = self._finish_record(
                {
                    "schema": EXECUTION_LEASE_SCHEMA,
                    "authority": dict(_AUTHORITY),
                    "event": event,
                    "status": "ACTIVE",
                    "lease_id": lease_id,
                    "binding": binding.as_dict(),
                    "binding_sha256": binding.sha256,
                    "clock_id": clock.clock_id,
                    "acquired_tick_ns": clock.tick_ns,
                    "observed_tick_ns": clock.tick_ns,
                    "expires_tick_ns": clock.tick_ns + ttl,
                    "ttl_ns": ttl,
                    "generation": generation,
                    "nonce_sha256": nonce_sha256,
                    "previous_record_sha256": previous_sha256,
                    "release_cause": None,
                }
            )
            if initialize_slot:
                self._create_slot_marker_unlocked()
            self._write_unlocked(record)
            return LeaseGrant(token=self._token(record, nonce), receipt=dict(record))

    def _verify_loaded(
        self,
        current: dict[str, Any] | None,
        *,
        binding: ExecutionLeaseBinding,
        token: ExecutionLeaseToken,
        clock: ClockSample,
    ) -> LeaseVerdict:
        if current is None:
            return LeaseVerdict(VerificationStatus.ABSENT, "lease state is absent")
        record_sha256 = current["record_sha256"]
        if not _constant_equal(binding.slot_sha256, self.slot_sha256):
            return LeaseVerdict(
                VerificationStatus.IDENTITY_MISMATCH,
                "binding names another execution slot",
                record_sha256,
            )
        if not _constant_equal(current["binding_sha256"], binding.sha256):
            return LeaseVerdict(
                VerificationStatus.IDENTITY_MISMATCH,
                "owner/run/node/visit/slot/flow/policy/runtime/instruction binding differs",
                record_sha256,
            )
        if not _constant_equal(token.binding_sha256, binding.sha256):
            return LeaseVerdict(
                VerificationStatus.TOKEN_MISMATCH,
                "token binding differs",
                record_sha256,
            )
        if current["status"] == "RELEASED":
            released_token_matches = (
                _constant_equal(token.lease_id, current["lease_id"])
                and token.generation + 1 == current["generation"]
                and _constant_equal(
                    token.record_sha256, current["previous_record_sha256"]
                )
            )
            if released_token_matches:
                return LeaseVerdict(
                    VerificationStatus.RELEASED,
                    "execution ownership has already been released",
                    record_sha256,
                )
            return LeaseVerdict(
                VerificationStatus.TOKEN_MISMATCH,
                "token does not identify the released lease generation",
                record_sha256,
            )
        token_matches = (
            _constant_equal(token.lease_id, current["lease_id"])
            and token.generation == current["generation"]
            and _constant_equal(token.record_sha256, record_sha256)
            and current["nonce_sha256"] is not None
            and _constant_equal(
                hashlib.sha256(token.nonce.encode("ascii")).hexdigest(),
                current["nonce_sha256"],
            )
        )
        if not token_matches:
            return LeaseVerdict(
                VerificationStatus.TOKEN_MISMATCH,
                "token is stale, replayed, or not current",
                record_sha256,
            )
        if clock.clock_id != current["clock_id"]:
            return LeaseVerdict(
                VerificationStatus.CLOCK_MISMATCH,
                "clock domain differs",
                record_sha256,
            )
        if clock.tick_ns < current["observed_tick_ns"]:
            return LeaseVerdict(
                VerificationStatus.CLOCK_ROLLBACK,
                "clock tick precedes the last state-changing observation",
                record_sha256,
            )
        if clock.tick_ns >= current["expires_tick_ns"]:
            return LeaseVerdict(
                VerificationStatus.EXPIRED,
                "execution ownership is expired",
                record_sha256,
            )
        return LeaseVerdict(
            VerificationStatus.VALID,
            "identity, current token, clock, and half-open TTL all match",
            record_sha256,
        )

    def verify(
        self,
        binding: ExecutionLeaseBinding,
        token: ExecutionLeaseToken,
        *,
        clock: ClockSample,
    ) -> LeaseVerdict:
        if not isinstance(binding, ExecutionLeaseBinding):
            raise TypeError("binding must be ExecutionLeaseBinding")
        if not isinstance(token, ExecutionLeaseToken):
            raise TypeError("token must be ExecutionLeaseToken")
        if not isinstance(clock, ClockSample):
            raise TypeError("clock must be ClockSample")
        try:
            with self._locked():
                current = self._read_unlocked()
        except ExecutionLeaseStateError as exc:
            return LeaseVerdict(VerificationStatus.MALFORMED, str(exc))
        return self._verify_loaded(
            current, binding=binding, token=token, clock=clock
        )

    def heartbeat(
        self,
        binding: ExecutionLeaseBinding,
        token: ExecutionLeaseToken,
        *,
        clock: ClockSample,
    ) -> LeaseGrant:
        """Renew the fixed TTL and rotate the controller token."""

        if not isinstance(binding, ExecutionLeaseBinding):
            raise TypeError("binding must be ExecutionLeaseBinding")
        if not isinstance(token, ExecutionLeaseToken):
            raise TypeError("token must be ExecutionLeaseToken")
        if not isinstance(clock, ClockSample):
            raise TypeError("clock must be ClockSample")
        with self._locked():
            current = self._read_unlocked()
            verdict = self._verify_loaded(
                current, binding=binding, token=token, clock=clock
            )
            if verdict.status is not VerificationStatus.VALID:
                raise ExecutionLeaseRejected(verdict)
            if current is None:
                raise ExecutionLeaseStateError(
                    "internal lease verification returned VALID for absent state"
                )
            if clock.tick_ns > MAX_TICK_NS - current["ttl_ns"]:
                raise ExecutionLeaseRejected(
                    LeaseVerdict(
                        VerificationStatus.EXPIRED,
                        "heartbeat expiry exceeds the supported clock range",
                        current["record_sha256"],
                    )
                )
            generation = current["generation"] + 1
            if generation > MAX_TICK_NS:
                raise ExecutionLeaseRejected(
                    LeaseVerdict(
                        VerificationStatus.EXPIRED,
                        "lease generation exhausted",
                        current["record_sha256"],
                    )
                )
            nonce = self._new_nonce()
            nonce_sha256 = hashlib.sha256(nonce.encode("ascii")).hexdigest()
            record = self._finish_record(
                {
                    **{
                        key: value
                        for key, value in current.items()
                        if key != "record_sha256"
                    },
                    "event": "HEARTBEAT",
                    "observed_tick_ns": clock.tick_ns,
                    "expires_tick_ns": clock.tick_ns + current["ttl_ns"],
                    "generation": generation,
                    "nonce_sha256": nonce_sha256,
                    "previous_record_sha256": current["record_sha256"],
                }
            )
            self._write_unlocked(record)
            return LeaseGrant(token=self._token(record, nonce), receipt=dict(record))

    def release(
        self,
        binding: ExecutionLeaseBinding,
        token: ExecutionLeaseToken,
        *,
        clock: ClockSample,
        cause: ReleaseCause,
    ) -> dict[str, Any]:
        """End execution ownership without authorizing any output release."""

        if not isinstance(binding, ExecutionLeaseBinding):
            raise TypeError("binding must be ExecutionLeaseBinding")
        if not isinstance(token, ExecutionLeaseToken):
            raise TypeError("token must be ExecutionLeaseToken")
        if not isinstance(clock, ClockSample):
            raise TypeError("clock must be ClockSample")
        if not isinstance(cause, ReleaseCause):
            raise TypeError("cause must be ReleaseCause")
        with self._locked():
            current = self._read_unlocked()
            verdict = self._verify_loaded(
                current, binding=binding, token=token, clock=clock
            )
            if verdict.status is not VerificationStatus.VALID:
                raise ExecutionLeaseRejected(verdict)
            if current is None:
                raise ExecutionLeaseStateError(
                    "internal lease verification returned VALID for absent state"
                )
            generation = current["generation"] + 1
            if generation > MAX_TICK_NS:
                raise ExecutionLeaseRejected(
                    LeaseVerdict(
                        VerificationStatus.EXPIRED,
                        "lease generation exhausted",
                        current["record_sha256"],
                    )
                )
            record = self._finish_record(
                {
                    **{
                        key: value
                        for key, value in current.items()
                        if key != "record_sha256"
                    },
                    "event": "RELEASED",
                    "status": "RELEASED",
                    "observed_tick_ns": clock.tick_ns,
                    "generation": generation,
                    "nonce_sha256": None,
                    "previous_record_sha256": current["record_sha256"],
                    "release_cause": cause.value,
                }
            )
            self._write_unlocked(record)
            return dict(record)

    def read_receipt(self) -> dict[str, Any] | None:
        """Return the current public receipt; it never contains the nonce."""

        with self._locked():
            current = self._read_unlocked()
            return None if current is None else dict(current)
