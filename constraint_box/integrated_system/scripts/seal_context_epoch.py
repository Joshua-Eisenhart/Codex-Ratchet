#!/usr/bin/env python3
"""Seal and verify file-backed ConstraintBox context epochs.

This module is deliberately a small provenance utility.  It does not decide
whether a context is true, useful, admitted, or promotable.  An epoch only
records the exact bytes that a later wave was allowed to see and the verified
parent from which those bytes were projected.

The authoritative object is the epoch file itself.  ``CURRENT_EPOCH.json`` is
an optional, compare-and-swap updated convenience pointer and is never needed
to verify an epoch or its chain.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping


SCHEMA = "constraintbox.context-epoch.v2"
GENESIS_SCHEMA = "constraintbox.integrated-system-genesis.v1"
POINTER_SCHEMA = "constraintbox.current-context-epoch-pointer.v1"
HISTORICAL_CHAIN_INTEGRITY = "historical_chain_integrity"
CURRENT_BINDINGS = "current_bindings"
VERIFICATION_MODES = frozenset({HISTORICAL_CHAIN_INTEGRITY, CURRENT_BINDINGS})
ZERO_SHA256 = "0" * 64
POINTER_LOCK_TIMEOUT_SECONDS = 5.0
POINTER_LOCK_POLL_SECONDS = 0.01
FORBIDDEN_POINTER_KEYS = frozenset(
    {"decision", "disposition", "promotion_allowed", "truth_disposition", "truth_status"}
)
REQUIRED_BINDINGS = frozenset(
    {
        "corpus",
        "corpus_manifest",
        "refresh_ledger",
        "current_context",
        "wave_bootstrap",
        "consolidation",
        "retained_receipt_manifest",
    }
)
FORBIDDEN_EPOCH_KEYS = frozenset(
    {
        "decision",
        "disposition",
        "promotion_allowed",
        "truth_disposition",
        "truth_status",
    }
)
_EPOCH_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


class EpochRefusal(ValueError):
    """A declared path, parent, digest, pointer, or epoch is invalid."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the v1 canonical JSON identity encoding used by CB Light."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise EpochRefusal(f"REFUSE_FILE_READ:{path}:{exc}") from exc
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _valid_sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise EpochRefusal(f"REFUSE_INVALID_SHA256:{label}")
    try:
        int(value, 16)
    except ValueError as exc:
        raise EpochRefusal(f"REFUSE_INVALID_SHA256:{label}") from exc
    return value.lower()


def _load_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise EpochRefusal(f"REFUSE_FILE_READ:{label}:{exc}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EpochRefusal(f"REFUSE_JSON:{label}:{exc}") from exc
    if not isinstance(value, dict):
        raise EpochRefusal(f"REFUSE_JSON_OBJECT:{label}")
    return value, raw


def _root(root: Path) -> Path:
    try:
        resolved = root.expanduser().resolve(strict=True)
    except OSError as exc:
        raise EpochRefusal(f"REFUSE_ROOT:{root}:{exc}") from exc
    if not resolved.is_dir():
        raise EpochRefusal(f"REFUSE_ROOT_NOT_DIRECTORY:{root}")
    return resolved


def _relative_declared_path(value: Any, label: str) -> str:
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
    if not isinstance(value, str) or not value or "\x00" in value:
        raise EpochRefusal(f"REFUSE_INVALID_PATH:{label}")
    # Epoch paths are portable, root-relative POSIX names.  Refusing backslash
    # avoids a declaration that is interpreted differently by another host.
    if "\\" in value:
        raise EpochRefusal(f"REFUSE_NON_PORTABLE_PATH:{label}")
    candidate = Path(value)
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        raise EpochRefusal(f"REFUSE_PATH_ESCAPE:{label}:{value}")
    normalized = candidate.as_posix()
    if normalized in {"", "."}:
        raise EpochRefusal(f"REFUSE_INVALID_PATH:{label}")
    return normalized


def _confined_path(root: Path, value: Any, label: str, *, must_exist: bool) -> Path:
    relative = _relative_declared_path(value, label)
    candidate = root / relative
    # Resolve existing components so symlinks cannot turn a relative claim into
    # an outside file.  A symlink is refused even when it points back inside:
    # the byte custody claim must name a stable ordinary file.
    current = root
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise EpochRefusal(f"REFUSE_SYMLINK_PATH:{label}:{relative}")
    try:
        resolved = candidate.resolve(strict=must_exist)
    except OSError as exc:
        raise EpochRefusal(f"REFUSE_PATH_RESOLVE:{label}:{relative}:{exc}") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EpochRefusal(f"REFUSE_PATH_ESCAPE:{label}:{relative}") from exc
    if must_exist and (not resolved.exists() or not resolved.is_file()):
        raise EpochRefusal(f"REFUSE_FILE_MISSING:{label}:{relative}")
    return resolved


def _relative_from_root(root: Path, path: Path, label: str) -> str:
    try:
        relative = path.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise EpochRefusal(f"REFUSE_PATH_ESCAPE:{label}:{path}") from exc
    return _relative_declared_path(relative.as_posix(), label)


def _argument_path(root: Path, value: str | Path, label: str) -> str:
    """Normalize an API path while keeping persisted declarations portable.

    String declarations are already root-relative and are never allowed to be
    absolute.  A ``Path`` supplied by a Python caller may be absolute, but it
    is accepted only when it resolves inside ``root`` and is converted to its
    portable relative spelling before confinement checks.
    """

    if isinstance(value, Path) and value.expanduser().is_absolute():
        candidate = value.expanduser()
        try:
            # Keep the lexical components here.  _confined_path must still see
            # any symlink component and refuse it rather than resolving it
            # away before the custody check.
            relative = candidate.relative_to(root)
        except ValueError as exc:
            raise EpochRefusal(f"REFUSE_PATH_ESCAPE:{label}:{candidate}") from exc
        return _relative_declared_path(relative.as_posix(), label)
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _read_file_binding(
    root: Path,
    declaration: Any,
    label: str,
) -> dict[str, Any]:
    if isinstance(declaration, str):
        declared_path = declaration
        expected_sha = None
        expected_bytes = None
    elif isinstance(declaration, Mapping):
        declared_path = declaration.get("path")
        expected_sha = declaration.get("sha256")
        expected_bytes = declaration.get("byte_length")
    else:
        raise EpochRefusal(f"REFUSE_BINDING_DECLARATION:{label}")
    path = _confined_path(root, declared_path, label, must_exist=True)
    raw_bytes = path.read_bytes()
    observed_sha = sha256_bytes(raw_bytes)
    if expected_sha is not None and _valid_sha(expected_sha, label) != observed_sha:
        raise EpochRefusal(f"REFUSE_DECLARED_SHA256_MISMATCH:{label}")
    if expected_bytes is not None and (
        isinstance(expected_bytes, bool)
        or not isinstance(expected_bytes, int)
        or expected_bytes != len(raw_bytes)
    ):
        raise EpochRefusal(f"REFUSE_DECLARED_BYTE_LENGTH_MISMATCH:{label}")
    return {
        "path": _relative_from_root(root, path, label),
        "sha256": observed_sha,
        "byte_length": len(raw_bytes),
    }


def _normalize_bindings(root: Path, declarations: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(declarations, Mapping):
        raise EpochRefusal("REFUSE_BINDINGS_NOT_OBJECT")
    keys = set(declarations)
    if keys != REQUIRED_BINDINGS:
        missing = sorted(REQUIRED_BINDINGS - keys)
        extra = sorted(keys - REQUIRED_BINDINGS)
        raise EpochRefusal(f"REFUSE_BINDING_SET:missing={missing}:extra={extra}")

    normalized: dict[str, Any] = {
        "corpus": _read_file_binding(root, declarations["corpus"], "corpus"),
        "corpus_manifest": _read_file_binding(
            root, declarations["corpus_manifest"], "corpus_manifest"
        ),
        "refresh_ledger": _read_file_binding(
            root, declarations["refresh_ledger"], "refresh_ledger"
        ),
        "wave_bootstrap": _read_file_binding(
            root, declarations["wave_bootstrap"], "wave_bootstrap"
        ),
        "consolidation": _read_file_binding(
            root, declarations["consolidation"], "consolidation"
        ),
        "retained_receipt_manifest": _read_file_binding(
            root,
            declarations["retained_receipt_manifest"],
            "retained_receipt_manifest",
        ),
    }
    current = declarations["current_context"]
    if not isinstance(current, Mapping) or not current:
        raise EpochRefusal("REFUSE_CURRENT_CONTEXT_BINDINGS")
    current_normalized: dict[str, Any] = {}
    for name in sorted(current):
        if not isinstance(name, str) or not name:
            raise EpochRefusal("REFUSE_CURRENT_CONTEXT_LABEL")
        current_normalized[name] = _read_file_binding(
            root, current[name], f"current_context:{name}"
        )
    normalized["current_context"] = current_normalized
    return normalized


def _validate_file_binding_shape(
    root: Path,
    binding: Any,
    label: str,
    *,
    must_exist: bool,
) -> tuple[Path, str, int]:
    if not isinstance(binding, Mapping):
        raise EpochRefusal(f"REFUSE_BINDING_OBJECT:{label}")
    path = _confined_path(root, binding.get("path"), label, must_exist=must_exist)
    digest = _valid_sha(binding.get("sha256"), label)
    byte_length = binding.get("byte_length")
    if isinstance(byte_length, bool) or not isinstance(byte_length, int) or byte_length < 0:
        raise EpochRefusal(f"REFUSE_BOUND_FILE_BYTE_LENGTH:{label}")
    return path, digest, byte_length


def _verify_file_binding(root: Path, binding: Any, label: str) -> None:
    path, expected_sha, expected_bytes = _validate_file_binding_shape(
        root, binding, label, must_exist=True
    )
    raw_bytes = path.read_bytes()
    if expected_sha != sha256_bytes(raw_bytes):
        raise EpochRefusal(f"REFUSE_BOUND_FILE_SHA256_MISMATCH:{label}")
    if expected_bytes != len(raw_bytes):
        raise EpochRefusal(f"REFUSE_BOUND_FILE_BYTE_LENGTH_MISMATCH:{label}")


def _verify_binding_declaration(root: Path, binding: Any, label: str) -> None:
    # Historical-chain verification checks the immutable claim shape and path
    # confinement, but deliberately does not read the old live path.  The
    # source may have legitimately moved or changed since this epoch.
    _validate_file_binding_shape(root, binding, label, must_exist=False)


def _verify_bindings(
    root: Path,
    bindings: Any,
    *,
    mode: str = CURRENT_BINDINGS,
) -> None:
    if mode not in VERIFICATION_MODES:
        raise EpochRefusal(f"REFUSE_VERIFICATION_MODE:{mode}")
    if not isinstance(bindings, Mapping) or set(bindings) != REQUIRED_BINDINGS:
        raise EpochRefusal("REFUSE_BOUND_BINDING_SET")
    verifier = (
        _verify_file_binding
        if mode == CURRENT_BINDINGS
        else _verify_binding_declaration
    )
    for label in (
        "corpus",
        "corpus_manifest",
        "refresh_ledger",
        "wave_bootstrap",
        "consolidation",
        "retained_receipt_manifest",
    ):
        verifier(root, bindings[label], label)
    current = bindings["current_context"]
    if not isinstance(current, Mapping) or not current:
        raise EpochRefusal("REFUSE_BOUND_CURRENT_CONTEXT")
    for name in sorted(current):
        if not isinstance(name, str) or not name:
            raise EpochRefusal("REFUSE_BOUND_CURRENT_CONTEXT_LABEL")
        verifier(root, current[name], f"current_context:{name}")


def _verify_genesis(root: Path, path: Path, observed_sha: str) -> int:
    value, _raw = _load_json(path, "genesis")
    if value.get("schema") != GENESIS_SCHEMA:
        raise EpochRefusal("REFUSE_PARENT_SCHEMA")
    # GENESIS is an immutable predecessor record, not a v2 epoch, and has no
    # self digest.  The child still binds its exact bytes with observed_sha.
    if "epoch_digest" in value:
        raise EpochRefusal("REFUSE_GENESIS_DISPOSITION_FIELD")
    # The historical projection predates v2 and contains this exact safe
    # field.  It is provenance, not an epoch decision: accept only the
    # literal boolean false and never copy it into a child epoch.
    if "promotion_allowed" not in value or value["promotion_allowed"] is not False:
        raise EpochRefusal("REFUSE_GENESIS_DISPOSITION_FIELD")
    if observed_sha != sha256_file(path):
        raise EpochRefusal("REFUSE_PARENT_SHA256_MISMATCH")
    return 0


def _verify_epoch_object(
    root: Path,
    epoch: Mapping[str, Any],
    raw: bytes,
    epoch_path: Path,
    expected_sha: str | None,
    seen: set[str],
    *,
    mode: str,
) -> dict[str, Any]:
    if mode not in VERIFICATION_MODES:
        raise EpochRefusal(f"REFUSE_VERIFICATION_MODE:{mode}")
    if not isinstance(epoch, Mapping):
        raise EpochRefusal("REFUSE_EPOCH_OBJECT")
    if epoch.get("schema") != SCHEMA:
        raise EpochRefusal("REFUSE_EPOCH_SCHEMA")
    if any(key in epoch for key in FORBIDDEN_EPOCH_KEYS):
        raise EpochRefusal("REFUSE_EPOCH_DISPOSITION_FIELD")
    digest = _valid_sha(epoch.get("epoch_digest"), "epoch_digest")
    body = dict(epoch)
    body.pop("epoch_digest", None)
    if digest != sha256_bytes(canonical_json_bytes(body)):
        raise EpochRefusal("REFUSE_EPOCH_SELF_DIGEST_MISMATCH")
    if raw != canonical_json_bytes(dict(epoch)) + b"\n":
        raise EpochRefusal("REFUSE_EPOCH_NON_CANONICAL_BYTES")
    if expected_sha is not None:
        digest_file = sha256_bytes(raw)
        if _valid_sha(expected_sha, "expected_epoch_sha256") != digest_file:
            raise EpochRefusal("REFUSE_EPOCH_FILE_SHA256_MISMATCH")

    sequence = epoch.get("epoch_sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise EpochRefusal("REFUSE_EPOCH_SEQUENCE")
    epoch_id = epoch.get("epoch_id")
    if not isinstance(epoch_id, str) or _EPOCH_ID_RE.fullmatch(epoch_id) is None:
        raise EpochRefusal("REFUSE_EPOCH_ID")
    if not isinstance(epoch.get("captured_at"), str) or not epoch["captured_at"]:
        raise EpochRefusal("REFUSE_CAPTURED_AT")
    parent = epoch.get("parent")
    if not isinstance(parent, Mapping):
        raise EpochRefusal("REFUSE_EPOCH_PARENT")
    parent_path = _confined_path(root, parent.get("path"), "parent", must_exist=True)
    parent_key = str(parent_path)
    if parent_key in seen:
        raise EpochRefusal("REFUSE_EPOCH_PARENT_CYCLE")
    parent_sha = _valid_sha(parent.get("sha256"), "parent")
    actual_parent_sha = sha256_file(parent_path)
    if parent_sha != actual_parent_sha:
        raise EpochRefusal("REFUSE_PARENT_SHA256_MISMATCH")
    seen.add(parent_key)
    parent_value, parent_raw = _load_json(parent_path, "parent")
    if parent_value.get("schema") == GENESIS_SCHEMA:
        parent_sequence = _verify_genesis(root, parent_path, actual_parent_sha)
    elif parent_value.get("schema") == SCHEMA:
        parent_result = _verify_epoch_object(
            root,
            parent_value,
            parent_raw,
            parent_path,
            actual_parent_sha,
            seen,
            mode=HISTORICAL_CHAIN_INTEGRITY,
        )
        parent_sequence = int(parent_result["epoch_sequence"])
    else:
        raise EpochRefusal("REFUSE_PARENT_SCHEMA")
    if sequence != parent_sequence + 1:
        raise EpochRefusal("REFUSE_EPOCH_SEQUENCE_GAP")
    _verify_bindings(root, epoch.get("bound_files"), mode=mode)
    if mode == CURRENT_BINDINGS:
        claim_ceiling = (
            "epoch-chain integrity plus this head's bound files matched current filesystem bytes"
        )
        current_bindings = "VERIFIED"
    else:
        claim_ceiling = (
            "historical epoch-chain integrity only; bound source paths were not checked "
            "for presence, bytes, or currentness"
        )
        current_bindings = "NOT_CHECKED"
    return {
        "status": "PASS",
        "mode": mode,
        "verification_mode": mode,
        "historical_chain_integrity": "VERIFIED",
        "historical_chain_integrity_status": "VERIFIED",
        "current_bindings_checked": mode == CURRENT_BINDINGS,
        "current_bindings": current_bindings,
        "current_bindings_status": current_bindings,
        "claim_ceiling": claim_ceiling,
        "path": _relative_from_root(root, epoch_path, "epoch"),
        "sha256": sha256_bytes(raw),
        "epoch_sequence": sequence,
        "parent": {
            "path": _relative_from_root(root, parent_path, "parent"),
            "sha256": parent_sha,
        },
    }


def verify_epoch(
    root: Path,
    epoch_path: str | Path,
    *,
    expected_sha256: str | None = None,
    mode: str = CURRENT_BINDINGS,
) -> dict[str, Any]:
    """Verify one epoch and its complete parent chain.

    ``current_bindings`` checks this head's bound files against the current
    filesystem and verifies ancestors in historical mode.  Explicit
    ``historical_chain_integrity`` checks only immutable epoch claims and never
    reports that old source bytes are present or current.
    """

    if mode not in VERIFICATION_MODES:
        raise EpochRefusal(f"REFUSE_VERIFICATION_MODE:{mode}")

    root_path = _root(Path(root))
    relative = _relative_declared_path(_argument_path(root_path, epoch_path, "epoch"), "epoch")
    path = _confined_path(root_path, relative, "epoch", must_exist=True)
    value, raw = _load_json(path, "epoch")
    return _verify_epoch_object(
        root_path,
        value,
        raw,
        path,
        expected_sha256,
        {str(path)},
        mode=mode,
    )


def _parent_sequence(root: Path, parent: Mapping[str, Any]) -> int:
    if not isinstance(parent, Mapping):
        raise EpochRefusal("REFUSE_PARENT_DECLARATION")
    path_value = parent.get("path")
    if isinstance(path_value, Path):
        path_value = _argument_path(root, path_value, "parent")
    path = _confined_path(root, path_value, "parent", must_exist=True)
    expected_sha = _valid_sha(parent.get("sha256"), "parent")
    actual_sha = sha256_file(path)
    if expected_sha != actual_sha:
        raise EpochRefusal("REFUSE_STALE_PARENT")
    value, raw = _load_json(path, "parent")
    if value.get("schema") == GENESIS_SCHEMA:
        return _verify_genesis(root, path, actual_sha)
    if value.get("schema") == SCHEMA:
        return int(
            _verify_epoch_object(
                root,
                value,
                raw,
                path,
                actual_sha,
                {str(path)},
                mode=HISTORICAL_CHAIN_INTEGRITY,
            )["epoch_sequence"]
        )
    raise EpochRefusal("REFUSE_PARENT_SCHEMA")


def _fsync_directory(path: Path) -> None:
    """Flush a directory after publishing a file in it."""

    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        # Directory fsync is not available on every supported filesystem.  A
        # successfully fsynced file is still a valid receipt; callers should
        # not lose the receipt merely because the optional directory flush is
        # unavailable.
        return
    try:
        os.fsync(descriptor)
    except OSError:
        # A directory flush is a durability enhancement, not part of the
        # epoch's byte identity.  Keep the complete published file usable on
        # filesystems that reject directory fsync.
        return
    finally:
        os.close(descriptor)


def _fsync_file(path: Path) -> None:
    """Flush the published file after an atomic replacement."""

    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError as exc:
        raise EpochRefusal(f"REFUSE_POINTER_FILE_READ:{path}:{exc}") from exc
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


@contextmanager
def _pointer_directory_lock(
    directory: Path,
    *,
    timeout: float = POINTER_LOCK_TIMEOUT_SECONDS,
) -> Iterator[None]:
    """Serialize pointer CAS transactions across local processes.

    The directory inode is a stable lock object, so no lock-file artifact is
    left in the repository and a crashed holder releases the advisory lock
    with its file descriptor.  Non-blocking polling gives callers a bounded,
    deterministic refusal instead of waiting forever on a dead process.
    """

    try:
        import fcntl
    except ImportError as exc:  # pragma: no cover - this estate is POSIX
        raise EpochRefusal("REFUSE_POINTER_LOCK_UNAVAILABLE") from exc
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError as exc:
        raise EpochRefusal(f"REFUSE_POINTER_LOCK_OPEN:{directory}:{exc}") from exc
    deadline = time.monotonic() + max(0.0, timeout)
    acquired = False
    try:
        while True:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise EpochRefusal(f"REFUSE_POINTER_LOCK:{directory}:{exc}") from exc
                if time.monotonic() >= deadline:
                    raise EpochRefusal("REFUSE_POINTER_LOCK_TIMEOUT") from exc
                time.sleep(min(POINTER_LOCK_POLL_SECONDS, max(0.0, deadline - time.monotonic())))
        try:
            yield
        finally:
            if acquired:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                acquired = False
    finally:
        if acquired:
            try:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            except OSError:
                pass
        os.close(descriptor)


def _write_exclusive(path: Path, raw: bytes) -> None:
    """Publish complete bytes once, leaving no partial epoch on interruption.

    A temporary file is fsynced before an atomic hard-link creates the final
    name.  ``os.link`` is intentionally used instead of ``os.replace``:
    replacing an existing epoch would violate immutability, while a failed
    link gives a clean compare-and-fail outcome under concurrent writers.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise EpochRefusal(f"REFUSE_EPOCH_OVERWRITE:{path}") from exc
        _fsync_directory(path.parent)
    except BaseException:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def seal_epoch(
    root: Path,
    output_path: str | Path,
    parent: Mapping[str, Any],
    bindings: Mapping[str, Any],
    *,
    captured_at: str | None = None,
    epoch_id: str | None = None,
) -> dict[str, Any]:
    """Create one immutable epoch file and return its parsed object.

    ``parent`` must contain a root-relative ``path`` and its caller-declared
    exact ``sha256``.  ``bindings`` must name every required context stratum.
    The output is published through an exclusive hard-link and can never
    silently overwrite an earlier epoch.
    """

    root_path = _root(Path(root))
    output_text = _argument_path(root_path, output_path, "output")
    output = _confined_path(root_path, output_text, "output", must_exist=False)
    if output.exists():
        raise EpochRefusal(f"REFUSE_EPOCH_OVERWRITE:{output_text}")
    parent_seq = _parent_sequence(root_path, parent)
    normalized = _normalize_bindings(root_path, bindings)
    sequence = parent_seq + 1
    if epoch_id is None:
        epoch_id = f"epoch-{sequence:08d}"
    if not isinstance(epoch_id, str) or _EPOCH_ID_RE.fullmatch(epoch_id) is None:
        raise EpochRefusal("REFUSE_EPOCH_ID")
    if captured_at is None:
        captured_at = _utc_now()
    if not isinstance(captured_at, str) or not captured_at:
        raise EpochRefusal("REFUSE_CAPTURED_AT")
    parent_path_value = parent.get("path")
    if isinstance(parent_path_value, Path):
        parent_path_value = _argument_path(root_path, parent_path_value, "parent")
    parent_path = _confined_path(root_path, parent_path_value, "parent", must_exist=True)
    body: dict[str, Any] = {
        "schema": SCHEMA,
        "epoch_id": epoch_id,
        "epoch_sequence": sequence,
        "captured_at": captured_at,
        "parent": {
            "path": _relative_from_root(root_path, parent_path, "parent"),
            "sha256": _valid_sha(parent.get("sha256"), "parent"),
        },
        "bound_files": normalized,
    }
    body["epoch_digest"] = sha256_bytes(canonical_json_bytes(body))
    raw = canonical_json_bytes(body) + b"\n"
    _write_exclusive(output, raw)
    result = verify_epoch(root_path, output, expected_sha256=sha256_bytes(raw))
    if result["epoch_sequence"] != sequence:
        raise EpochRefusal("REFUSE_EPOCH_REPLAY_SEQUENCE")
    return body


def _load_pointer(root: Path, pointer: Path) -> dict[str, Any]:
    value, raw = _load_json(pointer, "pointer")
    if value.get("schema") != POINTER_SCHEMA:
        raise EpochRefusal("REFUSE_POINTER_SCHEMA")
    if any(key in value for key in FORBIDDEN_POINTER_KEYS):
        raise EpochRefusal("REFUSE_POINTER_DISPOSITION_FIELD")
    if value.get("authoritative") is not False:
        raise EpochRefusal("REFUSE_POINTER_AUTHORITY")
    pointer_digest = _valid_sha(value.get("pointer_digest"), "pointer_digest")
    body = dict(value)
    body.pop("pointer_digest", None)
    if pointer_digest != sha256_bytes(canonical_json_bytes(body)):
        raise EpochRefusal("REFUSE_POINTER_SELF_DIGEST_MISMATCH")
    if raw != canonical_json_bytes(value) + b"\n":
        raise EpochRefusal("REFUSE_POINTER_NON_CANONICAL_BYTES")
    return value


def update_current_pointer(
    root: Path,
    pointer_path: str | Path,
    epoch_path: str | Path,
    expected_prior_parent: Mapping[str, Any],
    *,
    updated_at: str | None = None,
) -> dict[str, Any]:
    """CAS-update the non-authoritative current-epoch pointer.

    The caller's expected prior parent must equal the new epoch's parent.  If
    a pointer exists, its current epoch must also equal that expected parent.
    A missing pointer is only compatible with a genesis parent.
    """

    root_path = _root(Path(root))
    pointer_text = _argument_path(root_path, pointer_path, "pointer")
    pointer = _confined_path(root_path, pointer_text, "pointer", must_exist=False)
    epoch_text = _argument_path(root_path, epoch_path, "epoch")
    epoch = _confined_path(root_path, epoch_text, "epoch", must_exist=True)
    if not isinstance(expected_prior_parent, Mapping):
        raise EpochRefusal("REFUSE_EXPECTED_PRIOR_PARENT")
    expected_parent_path_value = expected_prior_parent.get("path")
    if isinstance(expected_parent_path_value, Path):
        expected_parent_path_value = _argument_path(
            root_path, expected_parent_path_value, "expected_prior_parent"
        )
    expected_parent_path = _confined_path(
        root_path, expected_parent_path_value, "expected_prior_parent", must_exist=True
    )
    expected_parent = {
        "path": _relative_from_root(root_path, expected_parent_path, "expected_prior_parent"),
        "sha256": _valid_sha(expected_prior_parent.get("sha256"), "expected_prior_parent"),
    }
    pointer.parent.mkdir(parents=True, exist_ok=True)
    # The lock spans every reread, verification, compare, replacement, and
    # post-replace fsync.  A check performed outside this critical section
    # would permit two processes to observe the same prior pointer and both
    # publish a successor.
    with _pointer_directory_lock(pointer.parent):
        verify_epoch(root_path, epoch)
        full_epoch, _ = _load_json(epoch, "epoch")
        new_parent = full_epoch["parent"]
        if new_parent != expected_parent:
            raise EpochRefusal("REFUSE_POINTER_PARENT_MISMATCH")
        if pointer.exists():
            current = _load_pointer(root_path, pointer)
            current_epoch = current.get("epoch")
            if not isinstance(current_epoch, Mapping):
                raise EpochRefusal("REFUSE_POINTER_EPOCH")
            current_epoch_path = _confined_path(
                root_path, current_epoch.get("path"), "pointer.epoch", must_exist=True
            )
            current_epoch_ref = {
                "path": _relative_from_root(root_path, current_epoch_path, "pointer.epoch"),
                "sha256": _valid_sha(current_epoch.get("sha256"), "pointer.epoch"),
            }
            actual_current_sha = sha256_file(current_epoch_path)
            if current_epoch_ref["sha256"] != actual_current_sha:
                raise EpochRefusal("REFUSE_POINTER_EPOCH_SHA256_MISMATCH")
            if current_epoch_ref != expected_parent:
                raise EpochRefusal("REFUSE_POINTER_CAS")
        else:
            parent_path = _confined_path(root_path, new_parent["path"], "parent", must_exist=True)
            parent_value, _parent_raw = _load_json(parent_path, "parent")
            if parent_value.get("schema") != GENESIS_SCHEMA:
                raise EpochRefusal("REFUSE_POINTER_MISSING_NON_GENESIS")
            _verify_genesis(root_path, parent_path, sha256_file(parent_path))
        pointer_body: dict[str, Any] = {
            "schema": POINTER_SCHEMA,
            "epoch": {
                "path": _relative_from_root(root_path, epoch, "epoch"),
                "sha256": sha256_file(epoch),
            },
            "parent": expected_parent,
            "updated_at": updated_at or _utc_now(),
            "authoritative": False,
        }
        pointer_body["pointer_digest"] = sha256_bytes(canonical_json_bytes(pointer_body))
        raw = canonical_json_bytes(pointer_body) + b"\n"
        fd, temporary = tempfile.mkstemp(prefix=".current-epoch.", dir=str(pointer.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, pointer)
            # os.replace makes the new name visible atomically, but durability
            # requires flushing that final inode and its containing directory.
            _fsync_file(pointer)
            _fsync_directory(pointer.parent)
        finally:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
        return pointer_body


def verify_pointer(root: Path, pointer_path: str | Path) -> dict[str, Any]:
    root_path = _root(Path(root))
    pointer_text = _argument_path(root_path, pointer_path, "pointer")
    pointer = _confined_path(root_path, pointer_text, "pointer", must_exist=True)
    value = _load_pointer(root_path, pointer)
    epoch_ref = value.get("epoch")
    if not isinstance(epoch_ref, Mapping):
        raise EpochRefusal("REFUSE_POINTER_EPOCH")
    epoch = _confined_path(root_path, epoch_ref.get("path"), "pointer.epoch", must_exist=True)
    expected = _valid_sha(epoch_ref.get("sha256"), "pointer.epoch")
    actual = sha256_file(epoch)
    if expected != actual:
        raise EpochRefusal("REFUSE_POINTER_EPOCH_SHA256_MISMATCH")
    verified = verify_epoch(root_path, epoch, expected_sha256=actual)
    if value.get("parent") != verified["parent"]:
        raise EpochRefusal("REFUSE_POINTER_PARENT_MISMATCH")
    return {"pointer": value, "epoch": verified}


def _load_bindings_json(path: Path) -> dict[str, Any]:
    value, _raw = _load_json(path, "bindings")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    seal_parser = subparsers.add_parser("seal")
    seal_parser.add_argument("--root", type=Path, required=True)
    seal_parser.add_argument("--output", type=str, required=True)
    seal_parser.add_argument("--parent", type=str, required=True)
    seal_parser.add_argument("--parent-sha256", required=True)
    seal_parser.add_argument("--bindings", type=Path, required=True)
    seal_parser.add_argument("--captured-at")
    seal_parser.add_argument("--epoch-id")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--root", type=Path, required=True)
    verify_parser.add_argument("--epoch", type=str, required=True)
    verify_parser.add_argument("--expected-sha256")
    verify_parser.add_argument(
        "--mode", choices=sorted(VERIFICATION_MODES), default=CURRENT_BINDINGS
    )
    pointer_parser = subparsers.add_parser("pointer")
    pointer_parser.add_argument("--root", type=Path, required=True)
    pointer_parser.add_argument("--pointer", type=str, required=True)
    pointer_parser.add_argument("--epoch", type=str, required=True)
    pointer_parser.add_argument("--prior-parent", type=str, required=True)
    pointer_parser.add_argument("--prior-parent-sha256", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "seal":
            result = seal_epoch(
                args.root,
                args.output,
                {"path": args.parent, "sha256": args.parent_sha256},
                _load_bindings_json(args.bindings),
                captured_at=args.captured_at,
                epoch_id=args.epoch_id,
            )
        elif args.command == "verify":
            result = verify_epoch(
                args.root,
                args.epoch,
                expected_sha256=args.expected_sha256,
                mode=args.mode,
            )
        else:
            result = update_current_pointer(
                args.root,
                args.pointer,
                args.epoch,
                {"path": args.prior_parent, "sha256": args.prior_parent_sha256},
            )
    except (EpochRefusal, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
