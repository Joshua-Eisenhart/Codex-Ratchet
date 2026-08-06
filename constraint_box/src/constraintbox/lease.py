from __future__ import annotations

import hashlib
import io
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

from .intake import IntakeError, canonical_json, parse_json_value


LEASE_SCHEMA = "constraintbox.tree-lease.v1"

VALID = "VALID"
STALE = "STALE"
TREE_MISMATCH = "TREE_MISMATCH"
ABSENT = "ABSENT"
MALFORMED = "MALFORMED"

FRESHNESS_RULE = (
    "A lease is fresh iff issued_at_utc <= now < issued_at_utc + ttl_seconds. "
    "Expiry is half-open: at expires_at_utc exactly the lease is STALE. "
    "A lease issued in the future relative to the verifying clock is STALE, "
    "not VALID. The clock is supplied by the caller; the lease never reads it."
)

DEFAULT_TIMEOUT_SECONDS = 300.0


class LeaseError(RuntimeError):
    """A lease could not be issued or the repository could not be read."""


class LeaseDenied(LeaseError):
    """A declared runner ran and did not exit 0, so no lease exists.

    ``runs`` holds the real captured runner rows up to and including the
    failure. It is evidence of denial, never a partial lease.
    """

    def __init__(self, message: str, runs: list[dict[str, Any]]):
        super().__init__(message)
        self.runs = runs


@dataclass(frozen=True)
class Verdict:
    """A named verification outcome.

    Deliberately not a bool. ``if verify_lease(...)`` raises rather than
    silently admitting, because the failure this module exists to stop is a
    check that looks like it ran and did not.
    """

    status: str
    reason: str

    def __bool__(self) -> bool:
        raise TypeError(
            f"Verdict is not a boolean; compare Verdict.status "
            f"(got {self.status}: {self.reason})"
        )


def _is_object_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) in (40, 64)
        and all(character in "0123456789abcdef" for character in value)
    )


def _utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def staged_tree_id(repo: Path) -> str:
    """Return the object id of the currently STAGED tree.

    This is the identity that survives a content swap. ``HEAD`` does not:
    restaging different content leaves HEAD byte-identical, which is the
    measured agentguard bypass. ``git write-tree`` writes tree objects only;
    it does not move HEAD, the index, or the working tree.
    """
    try:
        completed = subprocess.run(
            ["git", "write-tree"],
            cwd=str(repo),
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise LeaseError(f"cannot run git in {repo}: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise LeaseError(f"git write-tree failed ({completed.returncode}): {detail}")
    tree = completed.stdout.decode("utf-8", "replace").strip()
    if not _is_object_id(tree):
        raise LeaseError(f"git write-tree returned no object id: {tree!r}")
    return tree


def materialize_tree(repo: Path, tree_id: str, dest: Path) -> Path:
    """Write the exact contents of ``tree_id`` into ``dest``.

    Runners execute here, not in the working tree. Otherwise a runner could
    pass against worktree bytes while the index -- the thing that actually
    gets committed -- holds something else, which is the same class of failure
    as keying on HEAD. ``git archive`` reads a named tree object and touches
    nothing in the repository.
    """
    if not _is_object_id(tree_id):
        raise ValueError(f"tree_id is not an object id: {tree_id!r}")
    try:
        completed = subprocess.run(
            ["git", "archive", "--format=tar", tree_id],
            cwd=str(repo),
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise LeaseError(f"cannot run git in {repo}: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise LeaseError(f"git archive {tree_id} failed: {detail}")
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
        archive.extractall(dest, filter="data")
    return dest


def _run_one(
    argv: Sequence[str], workspace: Path, timeout_seconds: float
) -> dict[str, Any]:
    if not argv or not all(isinstance(part, str) for part in argv):
        raise LeaseError("runner must be a non-empty list of string arguments")
    try:
        completed = subprocess.run(
            list(argv),
            cwd=str(workspace),
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise LeaseError(
            f"runner {list(argv)!r} timed out after {timeout_seconds}s; "
            "no exit code, so no lease"
        ) from exc
    except OSError as exc:
        raise LeaseError(
            f"runner {list(argv)!r} could not be executed: {exc}; no lease"
        ) from exc
    return {
        "argv": list(argv),
        "exit_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr).hexdigest(),
    }


def lease_digest(lease: dict[str, Any]) -> str:
    body = {key: value for key, value in lease.items() if key != "lease_sha256"}
    return hashlib.sha256(canonical_json(body)).hexdigest()


def issue_lease(
    repo: Path,
    runners: Sequence[Sequence[str]],
    *,
    ttl_seconds: float,
    now: datetime | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run every declared command against the staged tree and bind the result.

    There is no agent-submitted-proof path into this function. The only inputs
    are a repository and argv lists; the exit codes come from
    ``subprocess.run``. A non-zero exit raises LeaseDenied and returns nothing.
    A command that cannot be run raises LeaseError and returns nothing.

    Runners execute inside a throwaway checkout of the staged tree, so the
    exit codes are earned by exactly the bytes the lease names. A runner
    therefore cannot see the working tree, untracked files, or the .git
    directory; declare commands that test content, not repository state.

    Runner output is hashed for the record and is never parsed. Exit code is
    the whole verdict: stdout saying "PASS" alongside exit 1 is a denial.
    """
    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be positive")
    if not runners:
        raise ValueError("a lease with no runners proves nothing")
    issued = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    tree = staged_tree_id(repo)

    runs: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="constraintbox-lease-") as scratch:
        workspace = materialize_tree(repo, tree, Path(scratch) / "tree")
        for argv in runners:
            row = _run_one(argv, workspace, timeout_seconds)
            runs.append(row)
            if row["exit_code"] != 0:
                raise LeaseDenied(
                    f"runner {row['argv']!r} exited {row['exit_code']}; "
                    "no lease issued",
                    runs,
                )

    lease = {
        "schema": LEASE_SCHEMA,
        "tree_id": tree,
        "runners": runs,
        "workspace": "staged-tree-checkout",
        "issued_at_utc": issued.isoformat(),
        "expires_at_utc": (issued + timedelta(seconds=ttl_seconds)).isoformat(),
        "ttl_seconds": ttl_seconds,
        "freshness_rule": FRESHNESS_RULE,
    }
    lease["lease_sha256"] = lease_digest(lease)
    return lease


def _malformed(reason: str) -> Verdict:
    return Verdict(MALFORMED, reason)


def _structure_problem(lease: Any) -> str | None:
    if not isinstance(lease, dict):
        return f"lease must be a JSON object, got {type(lease).__name__}"
    if lease.get("schema") != LEASE_SCHEMA:
        return f"schema is not {LEASE_SCHEMA}: {lease.get('schema')!r}"
    if not _is_object_id(lease.get("tree_id")):
        return f"tree_id is not an object id: {lease.get('tree_id')!r}"
    if lease.get("workspace") != "staged-tree-checkout":
        return f"unknown runner workspace: {lease.get('workspace')!r}"
    runners = lease.get("runners")
    if not isinstance(runners, list) or not runners:
        return "runners must be a non-empty list; a lease with no runs proves nothing"
    for index, row in enumerate(runners):
        if not isinstance(row, dict):
            return f"runner {index} is not an object"
        argv = row.get("argv")
        if not isinstance(argv, list) or not argv:
            return f"runner {index} has no argv"
        if any(not isinstance(part, str) for part in argv):
            return f"runner {index} argv is not all strings"
        exit_code = row.get("exit_code")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool):
            return f"runner {index} has no integer exit_code"
        if exit_code != 0:
            return (
                f"runner {index} records exit_code {exit_code}; a lease is a "
                "pass artifact and cannot carry a failing run"
            )
        for field in ("stdout_sha256", "stderr_sha256"):
            digest = row.get(field)
            if not (isinstance(digest, str) and len(digest) == 64):
                return f"runner {index} has no {field}"
    for field in ("issued_at_utc", "expires_at_utc"):
        value = lease.get(field)
        if not isinstance(value, str):
            return f"{field} missing"
        try:
            _utc(value)
        except ValueError as exc:
            return f"{field} invalid: {exc}"
    if _utc(lease["expires_at_utc"]) <= _utc(lease["issued_at_utc"]):
        return "expires_at_utc does not follow issued_at_utc"
    if not isinstance(lease.get("lease_sha256"), str):
        return "lease_sha256 missing"
    if lease["lease_sha256"] != lease_digest(lease):
        return "lease_sha256 does not match the lease body"
    return None


def verify_lease(lease: Any, staged_tree: str, now: datetime) -> Verdict:
    """Decide (lease, currently staged tree, clock) -> Verdict. Pure.

    No filesystem, no subprocess, no clock read. Check order is
    ABSENT -> MALFORMED -> TREE_MISMATCH -> STALE -> VALID: a lease earned
    against a different tree is reported as TREE_MISMATCH even when it is also
    expired, because the tree binding is the claim being enforced.

    The digest detects accidental and careless modification. It is not a
    signature: anyone who can write the lease file can recompute it. What the
    tree binding removes is transfer -- a proof earned against tree A can no
    longer admit tree B. Forgery is bounded by where the lease is stored, not
    by this function.
    """
    if lease is None:
        return Verdict(ABSENT, "no lease presented")
    if not _is_object_id(staged_tree):
        raise ValueError(f"staged_tree is not an object id: {staged_tree!r}")
    problem = _structure_problem(lease)
    if problem is not None:
        return _malformed(problem)

    if lease["tree_id"] != staged_tree:
        return Verdict(
            TREE_MISMATCH,
            f"lease binds tree {lease['tree_id']}, staged tree is {staged_tree}",
        )

    current = now.astimezone(timezone.utc)
    issued = _utc(lease["issued_at_utc"])
    expires = _utc(lease["expires_at_utc"])
    if current < issued:
        return Verdict(
            STALE, f"lease issued at {issued.isoformat()} is ahead of clock"
        )
    if current >= expires:
        return Verdict(STALE, f"lease expired at {expires.isoformat()}")
    return Verdict(
        VALID,
        f"{len(lease['runners'])} runner(s) exited 0 against tree {staged_tree}",
    )


def write_lease(path: Path, lease: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_bytes(canonical_json(lease) + b"\n")
    temp.replace(path)


class _Unparseable:
    __slots__ = ()


_UNPARSEABLE = _Unparseable()


def read_lease(path: Path) -> Any:
    """Return the parsed lease, None when absent, or the _UNPARSEABLE sentinel.

    Unparseable bytes come back as a sentinel rather than an exception, so the
    caller still reaches a named verdict instead of an error it might swallow.
    """
    if not path.exists():
        return None
    try:
        return parse_json_value(path.read_bytes())
    except (IntakeError, OSError):
        return _UNPARSEABLE


def verify_lease_file(
    path: Path, repo: Path, *, now: datetime | None = None
) -> Verdict:
    """Read a stored lease and verify it against the repository's staged tree."""
    lease = read_lease(path)
    if isinstance(lease, _Unparseable):
        return _malformed(f"lease at {path} is not parseable JSON")
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return verify_lease(lease, staged_tree_id(repo), current)
