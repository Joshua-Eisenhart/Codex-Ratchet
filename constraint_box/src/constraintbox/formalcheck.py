from __future__ import annotations

import hashlib
import json
import os
import re
import selectors
import signal
import stat
import subprocess
import tempfile
import time
import zipfile
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .contracts import Disposition


_EXPECTATIONS_SCHEMA = "constraintbox.formalcheck.expectations.v1"
_RECEIPT_SCHEMA = "constraintbox.formalcheck.receipt.v1"
_SUPPORTED_BACKENDS = frozenset({"tlc", "apalache"})
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_JAVA_VERSION_RE = re.compile(r'version "([^"]+)"')
_TLC_VERSION_RE = re.compile(r"\bTLC2 Version ([^\s]+)")
_TLC_STATE_RE = re.compile(
    r"(\d+) states generated, (\d+) distinct states found, "
    r"(\d+) states left on queue\."
)
_TLC_DEPTH_RE = re.compile(
    r"The depth of the complete state graph search is (\d+)\."
)
_TLC_INVARIANT_RE = re.compile(r"Invariant ([A-Za-z][A-Za-z0-9_]*) is violated")
_APALACHE_VERSION_RE = re.compile(r"# APALACHE version: ([^ |]+)")
_APALACHE_LENGTH_RE = re.compile(
    r"Checker reports no error up to computation length (\d+)"
)
_SOCKET_DENIAL_MARKERS = (
    "java.rmi.server.exportexception: listen failed on port",
    "java.net.socketexception: operation not permitted",
)
_MAX_TIMEOUT_SECONDS = 120.0
_MAX_FAILURE_EXCERPT = 2_000
_MAX_STDOUT_BYTES = 2 * 1024 * 1024
_MAX_STDERR_BYTES = 2 * 1024 * 1024


class FormalCheckStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    DRIFT = "DRIFT"


@dataclass(frozen=True)
class TemporalCheckProfile:
    """Controller-owned paths and bounds for one offline formal checker run."""

    backend: str
    java_executable: Path
    checker_artifact: Path
    profile_dir: Path
    expected_expectations_sha256: str
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if self.backend not in _SUPPORTED_BACKENDS:
            raise ValueError(
                f"backend must be one of {sorted(_SUPPORTED_BACKENDS)}"
            )
        for name in ("java_executable", "checker_artifact", "profile_dir"):
            value = getattr(self, name)
            if not isinstance(value, Path) or not value.is_absolute():
                raise ValueError(f"{name} must be an absolute pathlib.Path")
        if _SHA256_RE.fullmatch(self.expected_expectations_sha256) is None:
            raise ValueError(
                "expected_expectations_sha256 must be a lowercase SHA-256"
            )
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not 0.1 <= float(self.timeout_seconds) <= _MAX_TIMEOUT_SECONDS
        ):
            raise ValueError(
                f"timeout_seconds must be from 0.1 to {_MAX_TIMEOUT_SECONDS}"
            )


@dataclass(frozen=True)
class FormalCheckReceipt:
    schema: str
    profile_id: str
    backend: str
    status: FormalCheckStatus
    disposition: Disposition
    reason: str
    controls: dict[str, bool]
    evidence: dict[str, Any]
    claim_ceiling: str
    blocked_consumers: tuple[str, ...]
    promotion_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["disposition"] = self.disposition.value
        value["blocked_consumers"] = list(self.blocked_consumers)
        return value


@dataclass(frozen=True)
class ProcessResult:
    returncode: int | None
    stdout: bytes
    stderr: bytes
    elapsed_seconds: float
    timed_out: bool = False
    output_overflow: bool = False


@dataclass(frozen=True)
class ParsedCheck:
    status: str
    version: str | None
    generated_states: int | None = None
    distinct_states: int | None = None
    queue_states: int | None = None
    depth: int | None = None
    computation_length: int | None = None
    invariant_results: dict[str, str] = field(default_factory=dict)

    def semantic_key(self) -> dict[str, Any]:
        """Replay identity with seed, PID, time, path, and log noise excluded."""

        return {
            "status": self.status,
            "version": self.version,
            "generated_states": self.generated_states,
            "distinct_states": self.distinct_states,
            "queue_states": self.queue_states,
            "depth": self.depth,
            "computation_length": self.computation_length,
            "invariant_results": dict(sorted(self.invariant_results.items())),
        }


class _ExpectationsError(ValueError):
    pass


class _ToolUnavailable(RuntimeError):
    def __init__(self, reason: str, evidence: dict[str, Any] | None = None):
        super().__init__(reason)
        self.reason = reason
        self.evidence = evidence or {}


class _ToolExecutionFailed(RuntimeError):
    def __init__(self, reason: str, evidence: dict[str, Any] | None = None):
        super().__init__(reason)
        self.reason = reason
        self.evidence = evidence or {}


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while True:
            block = stream.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _ExpectationsError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _read_expectations_bytes(raw: bytes) -> dict[str, Any]:
    try:
        decoded = raw.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=_strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _ExpectationsError(f"expectations unreadable: {exc}") from exc
    if not isinstance(value, dict):
        raise _ExpectationsError("expectations root must be an object")
    return value


def _plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _required_text(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise _ExpectationsError(f"{key} must be a nonempty string")
    return value


def _required_sha(mapping: dict[str, Any], key: str) -> str:
    value = _required_text(mapping, key)
    if _SHA256_RE.fullmatch(value) is None:
        raise _ExpectationsError(f"{key} must be a lowercase SHA-256")
    return value


def _required_nonnegative_int(mapping: dict[str, Any], key: str) -> int:
    value = mapping.get(key)
    if not _plain_int(value) or value < 0:
        raise _ExpectationsError(f"{key} must be a nonnegative integer")
    return value


def _validate_expectations(value: dict[str, Any], backend: str) -> dict[str, Any]:
    if value.get("schema") != _EXPECTATIONS_SCHEMA:
        raise _ExpectationsError("expectations schema mismatch")
    for key in (
        "profile_id",
        "model_file",
        "config_file",
        "claim_ceiling",
    ):
        _required_text(value, key)
    _required_sha(value, "model_sha256")
    _required_sha(value, "config_sha256")

    for file_key in ("model_file", "config_file"):
        name = value[file_key]
        if Path(name).name != name or name in {".", ".."}:
            raise _ExpectationsError(f"{file_key} must be one plain file name")

    invariants = value.get("invariants")
    if (
        not isinstance(invariants, list)
        or not invariants
        or any(
            not isinstance(item, str)
            or re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", item) is None
            for item in invariants
        )
        or len(set(invariants)) != len(invariants)
    ):
        raise _ExpectationsError(
            "invariants must be a nonempty unique identifier list"
        )

    blocked_consumers = value.get("blocked_consumers")
    if (
        not isinstance(blocked_consumers, list)
        or not blocked_consumers
        or any(not isinstance(item, str) or not item for item in blocked_consumers)
        or len(set(blocked_consumers)) != len(blocked_consumers)
    ):
        raise _ExpectationsError(
            "blocked_consumers must be a nonempty unique string list"
        )

    bounds = value.get("bounds")
    if not isinstance(bounds, dict):
        raise _ExpectationsError("bounds must be an object")
    if set(bounds) != {"max_generation", "apalache_computation_length"}:
        raise _ExpectationsError(
            "bounds must contain only max_generation and "
            "apalache_computation_length"
        )
    for key in (
        "max_generation",
        "apalache_computation_length",
    ):
        _required_nonnegative_int(bounds, key)

    mutation = value.get("mutation")
    if not isinstance(mutation, dict):
        raise _ExpectationsError("mutation must be an object")
    for key in ("name", "target", "replacement", "expected_invariant"):
        _required_text(mutation, key)
    if mutation["target"] == mutation["replacement"]:
        raise _ExpectationsError("mutation target and replacement must differ")
    if mutation["expected_invariant"] not in invariants:
        raise _ExpectationsError(
            "mutation expected_invariant must be a named invariant"
        )

    backends = value.get("backends")
    if not isinstance(backends, dict) or any(
        name not in backends for name in _SUPPORTED_BACKENDS
    ):
        raise _ExpectationsError(
            "backends must contain tlc and apalache expectations"
        )
    for name in sorted(_SUPPORTED_BACKENDS):
        backend_value = backends[name]
        if not isinstance(backend_value, dict):
            raise _ExpectationsError(f"{name} expectations must be an object")
        _required_sha(backend_value, "artifact_sha256")
        _required_text(backend_value, "expected_version")
        _required_text(backend_value, "expected_java_version")
        if name == "tlc":
            _required_text(backend_value, "expected_release")
            for key in (
                "expected_generated_states",
                "expected_distinct_states",
                "expected_queue_states",
                "expected_depth",
            ):
                _required_nonnegative_int(backend_value, key)
        else:
            _required_nonnegative_int(backend_value, "check_length")

    if (
        bounds["apalache_computation_length"]
        != backends["apalache"]["check_length"]
    ):
        raise _ExpectationsError(
            "bounds.apalache_computation_length must equal "
            "backends.apalache.check_length"
        )
    if backend not in backends:
        raise _ExpectationsError(f"missing backend expectations for {backend}")
    return value


def _parse_max_generation_config(raw: bytes) -> int:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _ExpectationsError("config must be UTF-8") from exc

    assignments: list[int] = []
    assignment_re = re.compile(
        r"^CONSTANT[ \t]+MaxGeneration[ \t]*=[ \t]*(-?[0-9]+)[ \t]*$"
    )
    for line in text.splitlines():
        code = line.split("\\*", 1)[0].strip()
        if not code or re.search(r"\bMaxGeneration\b", code) is None:
            continue
        match = assignment_re.fullmatch(code)
        if match is None:
            raise _ExpectationsError(
                "config MaxGeneration binding must be exactly one integer "
                "CONSTANT assignment"
            )
        assignments.append(int(match.group(1)))
    if len(assignments) != 1:
        raise _ExpectationsError(
            "config must contain exactly one MaxGeneration integer assignment"
        )
    return assignments[0]


def _jar_manifest(path: Path) -> dict[str, str]:
    try:
        with zipfile.ZipFile(path) as archive:
            raw = archive.read("META-INF/MANIFEST.MF").decode(
                "utf-8", errors="strict"
            )
    except (OSError, KeyError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
        raise _ToolUnavailable(
            "checker_artifact_unusable",
            {"exception_type": type(exc).__name__, "error": str(exc)},
        ) from exc

    unfolded: list[str] = []
    for line in raw.replace("\r\n", "\n").split("\n"):
        if line.startswith(" ") and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line)
    manifest: dict[str, str] = {}
    for line in unfolded:
        if ": " in line:
            key, item = line.split(": ", 1)
            manifest[key] = item
    return manifest


def _run_process(
    command: tuple[str, ...],
    *,
    cwd: Path,
    timeout_seconds: float,
    stdout_limit: int = _MAX_STDOUT_BYTES,
    stderr_limit: int = _MAX_STDERR_BYTES,
) -> ProcessResult:
    started = time.monotonic()
    env = {
        key: value
        for key, value in os.environ.items()
        if key in {"HOME", "LANG", "LC_ALL", "PATH", "TMPDIR"}
    }
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=True,
        )
    except (FileNotFoundError, PermissionError, OSError) as exc:
        raise _ToolUnavailable(
            "process_unavailable",
            {
                "exception_type": type(exc).__name__,
                "error": str(exc),
                "executable": command[0],
            },
        ) from exc

    if process.stdout is None or process.stderr is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            process.kill()
        raise _ToolExecutionFailed("process_pipe_setup_failed")

    selector = selectors.DefaultSelector()
    streams = {
        process.stdout.fileno(): ("stdout", process.stdout),
        process.stderr.fileno(): ("stderr", process.stderr),
    }
    for descriptor, (_, stream) in streams.items():
        os.set_blocking(descriptor, False)
        selector.register(stream, selectors.EVENT_READ, descriptor)

    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    limits = {"stdout": stdout_limit, "stderr": stderr_limit}
    timed_out = False
    output_overflow = False
    deadline = started + timeout_seconds
    try:
        while selector.get_map():
            remaining_time = deadline - time.monotonic()
            if remaining_time <= 0:
                timed_out = True
                break
            events = selector.select(min(0.1, remaining_time))
            for key, _ in events:
                descriptor = key.data
                stream_name, stream = streams[descriptor]
                try:
                    chunk = os.read(descriptor, 64 * 1024)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(stream)
                    continue
                remaining_bytes = limits[stream_name] - len(buffers[stream_name])
                if len(chunk) > remaining_bytes:
                    if remaining_bytes > 0:
                        buffers[stream_name].extend(chunk[:remaining_bytes])
                    output_overflow = True
                    break
                buffers[stream_name].extend(chunk)
            if output_overflow:
                break
    finally:
        selector.close()

    if timed_out or output_overflow:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except (PermissionError, OSError):
            try:
                process.kill()
            except ProcessLookupError:
                pass
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            try:
                process.kill()
            except ProcessLookupError:
                pass
        process.wait(timeout=1.0)
    finally:
        process.stdout.close()
        process.stderr.close()

    return ProcessResult(
        process.returncode,
        bytes(buffers["stdout"]),
        bytes(buffers["stderr"]),
        time.monotonic() - started,
        timed_out,
        output_overflow,
    )


def _combined_text(result: ProcessResult) -> str:
    raw = result.stdout + b"\n" + result.stderr
    return _ANSI_RE.sub("", raw.decode("utf-8", errors="replace"))


def _socket_denied(result: ProcessResult) -> bool:
    lowered = _combined_text(result).lower()
    return any(marker in lowered for marker in _SOCKET_DENIAL_MARKERS)


def _stream_evidence(result: ProcessResult, *, include_excerpt: bool) -> dict[str, Any]:
    value: dict[str, Any] = {
        "returncode": result.returncode,
        "timed_out": result.timed_out,
        "output_overflow": result.output_overflow,
        "elapsed_seconds": round(result.elapsed_seconds, 6),
        "stdout_bytes": len(result.stdout),
        "stderr_bytes": len(result.stderr),
        "stdout_sha256": _sha256_bytes(result.stdout),
        "stderr_sha256": _sha256_bytes(result.stderr),
    }
    if include_excerpt:
        text = _combined_text(result)
        value["failure_excerpt"] = text[-_MAX_FAILURE_EXCERPT:]
    return value


def _parse_tlc_output(
    output: bytes | str,
    invariants: tuple[str, ...],
) -> ParsedCheck:
    text = (
        output.decode("utf-8", errors="replace")
        if isinstance(output, bytes)
        else output
    )
    version_match = _TLC_VERSION_RE.search(text)
    state_match = _TLC_STATE_RE.search(text)
    depth_match = _TLC_DEPTH_RE.search(text)
    violation_match = _TLC_INVARIANT_RE.search(text)
    if violation_match is not None:
        violated = violation_match.group(1)
        results = {
            invariant: "FAIL" if invariant == violated else "NOT_COMPLETED"
            for invariant in invariants
        }
        status = "INVARIANT_VIOLATION"
    elif "Model checking completed. No error has been found." in text:
        results = {invariant: "PASS" for invariant in invariants}
        status = "PASS"
    else:
        results = {invariant: "NOT_COMPLETED" for invariant in invariants}
        status = "ERROR"
    return ParsedCheck(
        status=status,
        version=version_match.group(1) if version_match else None,
        generated_states=int(state_match.group(1)) if state_match else None,
        distinct_states=int(state_match.group(2)) if state_match else None,
        queue_states=int(state_match.group(3)) if state_match else None,
        depth=int(depth_match.group(1)) if depth_match else None,
        invariant_results=results,
    )


def _parse_apalache_output(
    output: bytes | str,
    invariants: tuple[str, ...],
    *,
    expected_violation: str | None = None,
) -> ParsedCheck:
    raw_text = (
        output.decode("utf-8", errors="replace")
        if isinstance(output, bytes)
        else output
    )
    text = _ANSI_RE.sub("", raw_text)
    version_match = _APALACHE_VERSION_RE.search(text)
    length_match = _APALACHE_LENGTH_RE.search(text)
    no_error = "The outcome is: NoError" in text and "EXITCODE: OK" in text
    counterexample = (
        "The outcome is: Error" in text
        and re.search(r"State \d+: state invariant \d+ violated\.", text)
        is not None
        and re.search(r"Found \d+ error\(s\)", text) is not None
        and "Checker has found an error" in text
        and "EXITCODE: ERROR" in text
    )
    if no_error:
        status = "PASS"
        results = {invariant: "PASS" for invariant in invariants}
    elif counterexample and expected_violation is not None:
        status = "INVARIANT_VIOLATION"
        results = {
            invariant: (
                "FAIL" if invariant == expected_violation else "NOT_COMPLETED"
            )
            for invariant in invariants
        }
    else:
        status = "ERROR"
        results = {invariant: "NOT_COMPLETED" for invariant in invariants}
    return ParsedCheck(
        status=status,
        version=version_match.group(1) if version_match else None,
        computation_length=int(length_match.group(1)) if length_match else None,
        invariant_results=results,
    )


def _status_disposition(status: FormalCheckStatus) -> Disposition:
    if status == FormalCheckStatus.PASSED:
        return Disposition.ELIGIBLE
    if status == FormalCheckStatus.UNAVAILABLE:
        return Disposition.PARKED
    return Disposition.BLOCKED


def _base_evidence(profile: TemporalCheckProfile) -> dict[str, Any]:
    source = Path(__file__)
    return {
        "controller_owned_paths": {
            "java_executable": str(profile.java_executable),
            "checker_artifact": str(profile.checker_artifact),
            "profile_dir": str(profile.profile_dir),
            "expectations": str(profile.profile_dir / "expectations.json"),
        },
        "runner_source_sha256": _sha256_file(source),
        "timeout_seconds_per_process": float(profile.timeout_seconds),
        "subprocess_controls": {
            "stdout_limit_bytes": _MAX_STDOUT_BYTES,
            "stderr_limit_bytes": _MAX_STDERR_BYTES,
            "new_process_group": True,
            "kill_process_group_on_timeout_or_output_overflow": True,
            "os_resource_sandbox": False,
        },
    }


def _receipt(
    profile: TemporalCheckProfile,
    *,
    status: FormalCheckStatus,
    reason: str,
    controls: dict[str, bool],
    evidence: dict[str, Any],
    expectations: dict[str, Any] | None,
) -> FormalCheckReceipt:
    return FormalCheckReceipt(
        schema=_RECEIPT_SCHEMA,
        profile_id=(
            str(expectations.get("profile_id"))
            if expectations is not None
            else profile.profile_dir.name
        ),
        backend=profile.backend,
        status=status,
        disposition=_status_disposition(status),
        reason=reason,
        controls=controls,
        evidence={**_base_evidence(profile), **evidence},
        claim_ceiling=(
            str(expectations.get("claim_ceiling"))
            if expectations is not None
            else "no formal-check claim; profile expectations were not admitted"
        ),
        blocked_consumers=(
            tuple(str(item) for item in expectations["blocked_consumers"])
            if expectations is not None
            and isinstance(expectations.get("blocked_consumers"), list)
            else ("all_formal_check_consumers",)
        ),
    )


def _prepare(
    profile: TemporalCheckProfile,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    Path,
    Path,
    bytes,
    bytes,
]:
    if not profile.profile_dir.is_dir():
        raise _ToolUnavailable("formal_profile_directory_absent")
    expectations_path = profile.profile_dir / "expectations.json"
    if not expectations_path.is_file():
        raise _ToolUnavailable("expectations_file_absent")
    try:
        expectations_bytes = expectations_path.read_bytes()
    except OSError as exc:
        raise _ToolUnavailable(
            "expectations_file_unreadable",
            {"exception_type": type(exc).__name__, "error": str(exc)},
        ) from exc
    observed_expectations_sha = _sha256_bytes(expectations_bytes)
    if observed_expectations_sha != profile.expected_expectations_sha256:
        raise _ExpectationsError("expectations digest mismatch")
    expectations = _validate_expectations(
        _read_expectations_bytes(expectations_bytes), profile.backend
    )
    model_path = profile.profile_dir / expectations["model_file"]
    config_path = profile.profile_dir / expectations["config_file"]
    if not model_path.is_file() or not config_path.is_file():
        raise _ToolUnavailable(
            "model_or_config_absent",
            {
                "model_present": model_path.is_file(),
                "config_present": config_path.is_file(),
            },
        )
    try:
        model_bytes = model_path.read_bytes()
        config_bytes = config_path.read_bytes()
    except OSError as exc:
        raise _ToolUnavailable(
            "model_or_config_unreadable",
            {"exception_type": type(exc).__name__, "error": str(exc)},
        ) from exc

    hashes = {
        "expectations_sha256": observed_expectations_sha,
        "model_sha256": _sha256_bytes(model_bytes),
        "config_sha256": _sha256_bytes(config_bytes),
    }
    expected_source_hashes = {
        "model_sha256": expectations["model_sha256"],
        "config_sha256": expectations["config_sha256"],
    }
    source_drift = {
        key: {
            "expected": expected,
            "observed": hashes[key],
        }
        for key, expected in expected_source_hashes.items()
        if hashes[key] != expected
    }
    if source_drift:
        raise _ExpectationsError(json.dumps(source_drift, sort_keys=True))

    configured_max_generation = _parse_max_generation_config(config_bytes)
    if configured_max_generation != expectations["bounds"]["max_generation"]:
        raise _ExpectationsError(
            "bounds.max_generation must equal the config MaxGeneration binding"
        )

    if not profile.checker_artifact.is_file():
        raise _ToolUnavailable("checker_artifact_absent")
    if not profile.java_executable.is_file():
        raise _ToolUnavailable("java_executable_absent")
    try:
        java_mode = profile.java_executable.stat().st_mode
    except OSError as exc:
        raise _ToolUnavailable(
            "java_executable_unusable",
            {"exception_type": type(exc).__name__, "error": str(exc)},
        ) from exc
    if not java_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
        raise _ToolUnavailable("java_executable_not_executable")

    hashes["checker_artifact_sha256"] = _sha256_file(
        profile.checker_artifact
    )
    hashes["java_executable_sha256"] = _sha256_file(
        profile.java_executable.resolve()
    )
    backend_expectations = expectations["backends"][profile.backend]
    if (
        hashes["checker_artifact_sha256"]
        != backend_expectations["artifact_sha256"]
    ):
        raise _ExpectationsError(
            json.dumps(
                {
                    "checker_artifact_sha256": {
                        "expected": backend_expectations["artifact_sha256"],
                        "observed": hashes["checker_artifact_sha256"],
                    }
                },
                sort_keys=True,
            )
        )
    return (
        expectations,
        hashes,
        model_path,
        config_path,
        model_bytes,
        config_bytes,
    )


def _validate_java(
    profile: TemporalCheckProfile,
    expected_version: str,
) -> tuple[str, ProcessResult]:
    result = _run_process(
        (str(profile.java_executable), "-version"),
        cwd=profile.profile_dir,
        timeout_seconds=min(float(profile.timeout_seconds), 10.0),
    )
    text = _combined_text(result)
    match = _JAVA_VERSION_RE.search(text)
    if result.output_overflow:
        raise _ToolExecutionFailed(
            "java_validation_output_overflow",
            _stream_evidence(result, include_excerpt=True),
        )
    if result.timed_out:
        raise _ToolExecutionFailed(
            "java_validation_timed_out",
            _stream_evidence(result, include_excerpt=True),
        )
    if result.returncode != 0 or match is None:
        raise _ToolUnavailable(
            "java_executable_unusable",
            _stream_evidence(result, include_excerpt=True),
        )
    version = match.group(1)
    if version != expected_version:
        raise _ExpectationsError(
            json.dumps(
                {"java_version": {"expected": expected_version, "observed": version}},
                sort_keys=True,
            )
        )
    return version, result


def _write_profile_snapshots(
    model_name: str,
    config_name: str,
    model_bytes: bytes,
    config_bytes: bytes,
    target: Path,
    *,
    expected_model_sha256: str,
    expected_config_sha256: str,
) -> None:
    target.mkdir(parents=True, exist_ok=False)
    model_copy = target / model_name
    config_copy = target / config_name
    model_copy.write_bytes(model_bytes)
    config_copy.write_bytes(config_bytes)
    if _sha256_file(model_copy) != expected_model_sha256:
        raise _ExpectationsError("written model snapshot digest mismatch")
    if _sha256_file(config_copy) != expected_config_sha256:
        raise _ExpectationsError("written config snapshot digest mismatch")


def _mutate_model_snapshot(
    model_bytes: bytes,
    model_target: Path,
    mutation: dict[str, Any],
    *,
    expected_preimage_sha256: str,
) -> str:
    if _sha256_bytes(model_bytes) != expected_preimage_sha256:
        raise _ExpectationsError("behavior mutation preimage digest mismatch")
    try:
        source = model_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _ExpectationsError("model snapshot must be UTF-8") from exc
    target = mutation["target"]
    replacement = mutation["replacement"]
    if source.count(target) != 1:
        raise _ExpectationsError(
            "behavior mutation target must occur exactly once in the model"
        )
    mutant_bytes = source.replace(target, replacement, 1).encode("utf-8")
    model_target.write_bytes(mutant_bytes)
    observed = _sha256_file(model_target)
    if observed != _sha256_bytes(mutant_bytes):
        raise _ExpectationsError("written mutant model digest mismatch")
    return observed


def _copy_checker_artifact(
    source: Path,
    target_root: Path,
    *,
    expected_sha256: str,
) -> tuple[Path, str]:
    target = target_root / "checker-artifact.jar"
    digest = hashlib.sha256()
    try:
        with source.open("rb") as input_stream, target.open("xb") as output_stream:
            while True:
                block = input_stream.read(1024 * 1024)
                if not block:
                    break
                output_stream.write(block)
                digest.update(block)
    except OSError as exc:
        raise _ExpectationsError(
            f"checker artifact changed while snapshotting: {exc}"
        ) from exc
    observed = digest.hexdigest()
    if observed != expected_sha256 or _sha256_file(target) != expected_sha256:
        raise _ExpectationsError("checker artifact snapshot digest mismatch")
    return target, observed


def _post_run_hashes(
    profile: TemporalCheckProfile,
    model_path: Path,
    config_path: Path,
) -> dict[str, str | None]:
    paths = {
        "expectations_sha256": profile.profile_dir / "expectations.json",
        "model_sha256": model_path,
        "config_sha256": config_path,
        "checker_artifact_sha256": profile.checker_artifact,
        "java_executable_sha256": profile.java_executable.resolve(),
    }
    observed: dict[str, str | None] = {}
    for key, path in paths.items():
        try:
            observed[key] = _sha256_file(path) if path.is_file() else None
        except OSError:
            observed[key] = None
    return observed


def _tlc_command(
    profile: TemporalCheckProfile,
    checker_artifact: Path,
    model_name: str,
    config_name: str,
) -> tuple[str, ...]:
    return (
        str(profile.java_executable),
        "-XX:+UseParallelGC",
        "-jar",
        str(checker_artifact),
        "-workers",
        "1",
        "-config",
        config_name,
        model_name,
    )


def _run_tlc(
    profile: TemporalCheckProfile,
    expectations: dict[str, Any],
    hashes: dict[str, Any],
    model_path: Path,
    config_path: Path,
    model_bytes: bytes,
    config_bytes: bytes,
    java_version: str,
    java_result: ProcessResult,
) -> FormalCheckReceipt:
    invariants = tuple(expectations["invariants"])
    expected = expectations["backends"]["tlc"]
    controls = {
        "expectations_hash": True,
        "model_hash": True,
        "config_hash": True,
        "artifact_hash": True,
        "artifact_copy_hash": False,
        "java_usable": True,
        "checker_version": False,
        "positive": False,
        "behavior_mutation": False,
        "semantic_replay": False,
        "post_run_hashes": False,
    }
    evidence: dict[str, Any] = {
        "hashes": hashes,
        "java": {
            "path": str(profile.java_executable.resolve()),
            "version": java_version,
            **_stream_evidence(java_result, include_excerpt=False),
        },
        "bounds": expectations["bounds"],
        "expected_tlc_result_signature": {
            "generated_states": expected["expected_generated_states"],
            "distinct_states": expected["expected_distinct_states"],
            "queue_states": expected["expected_queue_states"],
            "derived_complete_state_graph_depth": expected["expected_depth"],
        },
        "named_invariants": list(invariants),
        "mutation": expectations["mutation"]["name"],
    }

    with tempfile.TemporaryDirectory(prefix="constraintbox-formal-tlc-") as raw:
        root = Path(raw)
        checker_copy, checker_copy_sha = _copy_checker_artifact(
            profile.checker_artifact,
            root,
            expected_sha256=hashes["checker_artifact_sha256"],
        )
        controls["artifact_copy_hash"] = True
        manifest = _jar_manifest(checker_copy)
        evidence["checker_artifact_copy"] = {
            "prepared_sha256": checker_copy_sha,
        }
        evidence["checker_manifest"] = {
            "implementation_title": manifest.get("Implementation-Title"),
            "implementation_version": manifest.get("Implementation-Version"),
            "release": manifest.get("X-Git-Tag"),
            "revision": manifest.get("X-Git-Revision"),
        }
        if manifest.get("X-Git-Tag") != expected["expected_release"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_release_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )

        positive_dir = root / "positive"
        mutation_dir = root / "mutation"
        replay_dir = root / "replay"
        copy_args = {
            "expected_model_sha256": hashes["model_sha256"],
            "expected_config_sha256": hashes["config_sha256"],
        }
        _write_profile_snapshots(
            model_path.name,
            config_path.name,
            model_bytes,
            config_bytes,
            positive_dir,
            **copy_args,
        )
        _write_profile_snapshots(
            model_path.name,
            config_path.name,
            model_bytes,
            config_bytes,
            mutation_dir,
            **copy_args,
        )
        _write_profile_snapshots(
            model_path.name,
            config_path.name,
            model_bytes,
            config_bytes,
            replay_dir,
            **copy_args,
        )
        evidence["mutant_model_sha256"] = _mutate_model_snapshot(
            model_bytes,
            mutation_dir / model_path.name,
            expectations["mutation"],
            expected_preimage_sha256=hashes["model_sha256"],
        )

        command = _tlc_command(
            profile, checker_copy, model_path.name, config_path.name
        )
        positive = _run_process(
            command,
            cwd=positive_dir,
            timeout_seconds=float(profile.timeout_seconds),
        )
        if positive.output_overflow:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="positive_check_output_overflow",
                controls=controls,
                evidence={
                    **evidence,
                    "positive_process": _stream_evidence(
                        positive, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if positive.timed_out:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="positive_check_timed_out",
                controls=controls,
                evidence={
                    **evidence,
                    "positive_process": _stream_evidence(
                        positive, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if _socket_denied(positive):
            return _receipt(
                profile,
                status=FormalCheckStatus.UNAVAILABLE,
                reason="sandbox_socket_denied",
                controls=controls,
                evidence={
                    **evidence,
                    "positive_process": _stream_evidence(
                        positive, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        parsed_positive = _parse_tlc_output(
            positive.stdout + b"\n" + positive.stderr, invariants
        )
        evidence["positive_process"] = _stream_evidence(
            positive, include_excerpt=parsed_positive.status != "PASS"
        )
        evidence["positive_semantics"] = parsed_positive.semantic_key()
        if positive.returncode != 0 or parsed_positive.status != "PASS":
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="positive_model_check_failed",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_positive.version is None:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="checker_version_unparseable",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_positive.version != expected["expected_version"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_version_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        controls["checker_version"] = True
        expected_semantics = {
            "generated_states": expected["expected_generated_states"],
            "distinct_states": expected["expected_distinct_states"],
            "queue_states": expected["expected_queue_states"],
            "depth": expected["expected_depth"],
        }
        observed_semantics = {
            key: getattr(parsed_positive, key) for key in expected_semantics
        }
        if observed_semantics != expected_semantics:
            evidence["expected_positive_semantics"] = expected_semantics
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="positive_semantic_output_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        controls["positive"] = True

        mutation = _run_process(
            command,
            cwd=mutation_dir,
            timeout_seconds=float(profile.timeout_seconds),
        )
        if mutation.output_overflow:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="behavior_mutation_output_overflow",
                controls=controls,
                evidence={
                    **evidence,
                    "mutation_process": _stream_evidence(
                        mutation, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if mutation.timed_out:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="behavior_mutation_timed_out",
                controls=controls,
                evidence={
                    **evidence,
                    "mutation_process": _stream_evidence(
                        mutation, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if _socket_denied(mutation):
            return _receipt(
                profile,
                status=FormalCheckStatus.UNAVAILABLE,
                reason="sandbox_socket_denied",
                controls=controls,
                evidence={
                    **evidence,
                    "mutation_process": _stream_evidence(
                        mutation, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        parsed_mutation = _parse_tlc_output(
            mutation.stdout + b"\n" + mutation.stderr, invariants
        )
        evidence["mutation_process"] = _stream_evidence(
            mutation,
            include_excerpt=parsed_mutation.status != "INVARIANT_VIOLATION",
        )
        evidence["mutation_semantics"] = parsed_mutation.semantic_key()
        expected_invariant = expectations["mutation"]["expected_invariant"]
        mutation_detected = (
            mutation.returncode not in {None, 0}
            and parsed_mutation.status == "INVARIANT_VIOLATION"
            and parsed_mutation.invariant_results.get(expected_invariant)
            == "FAIL"
        )
        if not mutation_detected:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="behavior_mutation_not_detected",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_mutation.version is None:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="behavior_mutation_version_unparseable",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_mutation.version != expected["expected_version"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_version_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        controls["behavior_mutation"] = True

        replay = _run_process(
            command,
            cwd=replay_dir,
            timeout_seconds=float(profile.timeout_seconds),
        )
        if replay.output_overflow:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_output_overflow",
                controls=controls,
                evidence={
                    **evidence,
                    "replay_process": _stream_evidence(
                        replay, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if replay.timed_out:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_timed_out",
                controls=controls,
                evidence={
                    **evidence,
                    "replay_process": _stream_evidence(
                        replay, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if _socket_denied(replay):
            return _receipt(
                profile,
                status=FormalCheckStatus.UNAVAILABLE,
                reason="sandbox_socket_denied",
                controls=controls,
                evidence={
                    **evidence,
                    "replay_process": _stream_evidence(
                        replay, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        parsed_replay = _parse_tlc_output(
            replay.stdout + b"\n" + replay.stderr, invariants
        )
        evidence["replay_process"] = _stream_evidence(
            replay, include_excerpt=parsed_replay.status != "PASS"
        )
        evidence["replay_semantics"] = parsed_replay.semantic_key()
        if replay.returncode != 0 or parsed_replay.status != "PASS":
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_disagreement",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_replay.version is None:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_version_unparseable",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_replay.version != expected["expected_version"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_version_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        controls["semantic_replay"] = (
            parsed_replay.semantic_key() == parsed_positive.semantic_key()
        )
        if not controls["semantic_replay"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_disagreement",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        copy_post_sha = _sha256_file(checker_copy)
        evidence["checker_artifact_copy"]["post_run_sha256"] = copy_post_sha
        controls["artifact_copy_hash"] = (
            copy_post_sha == hashes["checker_artifact_sha256"]
        )
        if not controls["artifact_copy_hash"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_artifact_copy_changed_during_run",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )

    evidence["post_run_hashes"] = _post_run_hashes(
        profile, model_path, config_path
    )
    controls["post_run_hashes"] = evidence["post_run_hashes"] == hashes
    if not controls["post_run_hashes"]:
        return _receipt(
            profile,
            status=FormalCheckStatus.DRIFT,
            reason="formal_inputs_changed_during_run",
            controls=controls,
            evidence=evidence,
            expectations=expectations,
        )

    return _receipt(
        profile,
        status=FormalCheckStatus.PASSED,
        reason="bounded_tlc_controls_passed",
        controls=controls,
        evidence=evidence,
        expectations=expectations,
    )


def _apalache_command(
    profile: TemporalCheckProfile,
    *,
    checker_artifact: Path,
    output_dir: Path,
    operation: str,
    model_name: str,
    config_name: str,
    invariants: tuple[str, ...],
    length: int,
) -> tuple[str, ...]:
    base = (
        str(profile.java_executable),
        "-jar",
        str(checker_artifact),
        f"--out-dir={output_dir}",
    )
    if operation == "typecheck":
        return (*base, "typecheck", model_name)
    return (
        *base,
        "check",
        f"--config={config_name}",
        f"--length={length}",
        "--no-deadlock",
        f"--inv={','.join(invariants)}",
        model_name,
    )


def _run_apalache(
    profile: TemporalCheckProfile,
    expectations: dict[str, Any],
    hashes: dict[str, Any],
    model_path: Path,
    config_path: Path,
    model_bytes: bytes,
    config_bytes: bytes,
    java_version: str,
    java_result: ProcessResult,
) -> FormalCheckReceipt:
    invariants = tuple(expectations["invariants"])
    expected = expectations["backends"]["apalache"]
    length = expected["check_length"]
    controls = {
        "expectations_hash": True,
        "model_hash": True,
        "config_hash": True,
        "artifact_hash": True,
        "artifact_copy_hash": False,
        "java_usable": True,
        "checker_version": False,
        "typecheck": False,
        "positive": False,
        "behavior_mutation": False,
        "semantic_replay": False,
        "post_run_hashes": False,
    }
    evidence: dict[str, Any] = {
        "hashes": hashes,
        "java": {
            "path": str(profile.java_executable.resolve()),
            "version": java_version,
            **_stream_evidence(java_result, include_excerpt=False),
        },
        "bounds": expectations["bounds"],
        "named_invariants": list(invariants),
        "mutation": expectations["mutation"]["name"],
    }

    with tempfile.TemporaryDirectory(prefix="constraintbox-formal-apalache-") as raw:
        root = Path(raw)
        checker_copy, checker_copy_sha = _copy_checker_artifact(
            profile.checker_artifact,
            root,
            expected_sha256=hashes["checker_artifact_sha256"],
        )
        controls["artifact_copy_hash"] = True
        manifest = _jar_manifest(checker_copy)
        evidence["checker_artifact_copy"] = {
            "prepared_sha256": checker_copy_sha,
        }
        evidence["checker_manifest"] = {
            "specification_title": manifest.get("Specification-Title"),
            "specification_version": manifest.get("Specification-Version"),
            "implementation_version": manifest.get("Implementation-Version"),
        }
        manifest_version = manifest.get("Implementation-Version")
        if manifest_version != expected["expected_version"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_manifest_version_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )

        positive_dir = root / "positive"
        mutation_dir = root / "mutation"
        replay_dir = root / "replay"
        copy_args = {
            "expected_model_sha256": hashes["model_sha256"],
            "expected_config_sha256": hashes["config_sha256"],
        }
        _write_profile_snapshots(
            model_path.name,
            config_path.name,
            model_bytes,
            config_bytes,
            positive_dir,
            **copy_args,
        )
        _write_profile_snapshots(
            model_path.name,
            config_path.name,
            model_bytes,
            config_bytes,
            mutation_dir,
            **copy_args,
        )
        _write_profile_snapshots(
            model_path.name,
            config_path.name,
            model_bytes,
            config_bytes,
            replay_dir,
            **copy_args,
        )
        evidence["mutant_model_sha256"] = _mutate_model_snapshot(
            model_bytes,
            mutation_dir / model_path.name,
            expectations["mutation"],
            expected_preimage_sha256=hashes["model_sha256"],
        )

        typecheck = _run_process(
            _apalache_command(
                profile,
                checker_artifact=checker_copy,
                output_dir=positive_dir / "typecheck-output",
                operation="typecheck",
                model_name=model_path.name,
                config_name=config_path.name,
                invariants=invariants,
                length=length,
            ),
            cwd=positive_dir,
            timeout_seconds=float(profile.timeout_seconds),
        )
        if typecheck.output_overflow:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="apalache_typecheck_output_overflow",
                controls=controls,
                evidence={
                    **evidence,
                    "typecheck_process": _stream_evidence(
                        typecheck, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if typecheck.timed_out:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="apalache_typecheck_timed_out",
                controls=controls,
                evidence={
                    **evidence,
                    "typecheck_process": _stream_evidence(
                        typecheck, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if _socket_denied(typecheck):
            return _receipt(
                profile,
                status=FormalCheckStatus.UNAVAILABLE,
                reason="sandbox_socket_denied",
                controls=controls,
                evidence={
                    **evidence,
                    "typecheck_process": _stream_evidence(
                        typecheck, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        typecheck_text = _combined_text(typecheck)
        typecheck_version = _APALACHE_VERSION_RE.search(typecheck_text)
        evidence["typecheck_process"] = _stream_evidence(
            typecheck,
            include_excerpt=(
                typecheck.returncode != 0
                or "Type checker [OK]" not in typecheck_text
            ),
        )
        typecheck_passed = (
            typecheck.returncode == 0
            and "Type checker [OK]" in typecheck_text
            and "All expressions are typed" in typecheck_text
        )
        if not typecheck_passed:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="apalache_typecheck_failed",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if typecheck_version is None:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="checker_version_unparseable",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if typecheck_version.group(1) != expected["expected_version"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_version_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        controls["checker_version"] = True
        controls["typecheck"] = True

        positive = _run_process(
            _apalache_command(
                profile,
                checker_artifact=checker_copy,
                output_dir=positive_dir / "check-output",
                operation="check",
                model_name=model_path.name,
                config_name=config_path.name,
                invariants=invariants,
                length=length,
            ),
            cwd=positive_dir,
            timeout_seconds=float(profile.timeout_seconds),
        )
        if positive.output_overflow:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="positive_check_output_overflow",
                controls=controls,
                evidence={
                    **evidence,
                    "positive_process": _stream_evidence(
                        positive, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if positive.timed_out:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="positive_check_timed_out",
                controls=controls,
                evidence={
                    **evidence,
                    "positive_process": _stream_evidence(
                        positive, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if _socket_denied(positive):
            return _receipt(
                profile,
                status=FormalCheckStatus.UNAVAILABLE,
                reason="sandbox_socket_denied",
                controls=controls,
                evidence={
                    **evidence,
                    "positive_process": _stream_evidence(
                        positive, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        parsed_positive = _parse_apalache_output(
            positive.stdout + b"\n" + positive.stderr, invariants
        )
        evidence["positive_process"] = _stream_evidence(
            positive, include_excerpt=parsed_positive.status != "PASS"
        )
        evidence["positive_semantics"] = parsed_positive.semantic_key()
        positive_passed = (
            positive.returncode == 0
            and parsed_positive.status == "PASS"
            and parsed_positive.computation_length == length
        )
        if not positive_passed:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="positive_model_check_failed",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_positive.version is None:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="checker_version_unparseable",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_positive.version != expected["expected_version"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_version_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        controls["positive"] = True

        expected_invariant = expectations["mutation"]["expected_invariant"]
        mutation_invariants = (expected_invariant,)
        mutation = _run_process(
            _apalache_command(
                profile,
                checker_artifact=checker_copy,
                output_dir=mutation_dir / "check-output",
                operation="check",
                model_name=model_path.name,
                config_name=config_path.name,
                invariants=mutation_invariants,
                length=length,
            ),
            cwd=mutation_dir,
            timeout_seconds=float(profile.timeout_seconds),
        )
        if mutation.output_overflow:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="behavior_mutation_output_overflow",
                controls=controls,
                evidence={
                    **evidence,
                    "mutation_process": _stream_evidence(
                        mutation, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if mutation.timed_out:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="behavior_mutation_timed_out",
                controls=controls,
                evidence={
                    **evidence,
                    "mutation_process": _stream_evidence(
                        mutation, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if _socket_denied(mutation):
            return _receipt(
                profile,
                status=FormalCheckStatus.UNAVAILABLE,
                reason="sandbox_socket_denied",
                controls=controls,
                evidence={
                    **evidence,
                    "mutation_process": _stream_evidence(
                        mutation, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        parsed_mutation = _parse_apalache_output(
            mutation.stdout + b"\n" + mutation.stderr,
            mutation_invariants,
            expected_violation=expected_invariant,
        )
        evidence["mutation_process"] = _stream_evidence(
            mutation,
            include_excerpt=parsed_mutation.status != "INVARIANT_VIOLATION",
        )
        evidence["mutation_semantics"] = parsed_mutation.semantic_key()
        mutation_detected = (
            mutation.returncode not in {None, 0}
            and parsed_mutation.status == "INVARIANT_VIOLATION"
            and parsed_mutation.invariant_results.get(expected_invariant)
            == "FAIL"
        )
        if not mutation_detected:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="behavior_mutation_not_detected",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_mutation.version is None:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="behavior_mutation_version_unparseable",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_mutation.version != expected["expected_version"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_version_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        controls["behavior_mutation"] = True

        replay = _run_process(
            _apalache_command(
                profile,
                checker_artifact=checker_copy,
                output_dir=replay_dir / "check-output",
                operation="check",
                model_name=model_path.name,
                config_name=config_path.name,
                invariants=invariants,
                length=length,
            ),
            cwd=replay_dir,
            timeout_seconds=float(profile.timeout_seconds),
        )
        if replay.output_overflow:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_output_overflow",
                controls=controls,
                evidence={
                    **evidence,
                    "replay_process": _stream_evidence(
                        replay, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if replay.timed_out:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_timed_out",
                controls=controls,
                evidence={
                    **evidence,
                    "replay_process": _stream_evidence(
                        replay, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        if _socket_denied(replay):
            return _receipt(
                profile,
                status=FormalCheckStatus.UNAVAILABLE,
                reason="sandbox_socket_denied",
                controls=controls,
                evidence={
                    **evidence,
                    "replay_process": _stream_evidence(
                        replay, include_excerpt=True
                    ),
                },
                expectations=expectations,
            )
        parsed_replay = _parse_apalache_output(
            replay.stdout + b"\n" + replay.stderr, invariants
        )
        evidence["replay_process"] = _stream_evidence(
            replay, include_excerpt=parsed_replay.status != "PASS"
        )
        evidence["replay_semantics"] = parsed_replay.semantic_key()
        if replay.returncode != 0 or parsed_replay.status != "PASS":
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_disagreement",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_replay.version is None:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_version_unparseable",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        if parsed_replay.version != expected["expected_version"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_version_drift",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        controls["semantic_replay"] = (
            parsed_replay.semantic_key() == parsed_positive.semantic_key()
        )
        if not controls["semantic_replay"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.FAILED,
                reason="semantic_replay_disagreement",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )
        copy_post_sha = _sha256_file(checker_copy)
        evidence["checker_artifact_copy"]["post_run_sha256"] = copy_post_sha
        controls["artifact_copy_hash"] = (
            copy_post_sha == hashes["checker_artifact_sha256"]
        )
        if not controls["artifact_copy_hash"]:
            return _receipt(
                profile,
                status=FormalCheckStatus.DRIFT,
                reason="checker_artifact_copy_changed_during_run",
                controls=controls,
                evidence=evidence,
                expectations=expectations,
            )

    evidence["post_run_hashes"] = _post_run_hashes(
        profile, model_path, config_path
    )
    controls["post_run_hashes"] = evidence["post_run_hashes"] == hashes
    if not controls["post_run_hashes"]:
        return _receipt(
            profile,
            status=FormalCheckStatus.DRIFT,
            reason="formal_inputs_changed_during_run",
            controls=controls,
            evidence=evidence,
            expectations=expectations,
        )

    return _receipt(
        profile,
        status=FormalCheckStatus.PASSED,
        reason="bounded_apalache_controls_passed",
        controls=controls,
        evidence=evidence,
        expectations=expectations,
    )


def run_temporal_check(profile: TemporalCheckProfile) -> FormalCheckReceipt:
    """Run a hash-pinned offline checker under one controller-owned profile.

    This is an instrument receipt, not a truth oracle.  The checked model is a
    bounded safety abstraction of the current lifecycle only.
    """

    expectations: dict[str, Any] | None = None
    try:
        (
            expectations,
            hashes,
            model_path,
            config_path,
            model_bytes,
            config_bytes,
        ) = _prepare(profile)
        backend_expectations = expectations["backends"][profile.backend]
        java_version, java_result = _validate_java(
            profile, backend_expectations["expected_java_version"]
        )
        if profile.backend == "tlc":
            return _run_tlc(
                profile,
                expectations,
                hashes,
                model_path,
                config_path,
                model_bytes,
                config_bytes,
                java_version,
                java_result,
            )
        return _run_apalache(
            profile,
            expectations,
            hashes,
            model_path,
            config_path,
            model_bytes,
            config_bytes,
            java_version,
            java_result,
        )
    except _ToolUnavailable as exc:
        return _receipt(
            profile,
            status=FormalCheckStatus.UNAVAILABLE,
            reason=exc.reason,
            controls={},
            evidence=exc.evidence,
            expectations=expectations,
        )
    except _ToolExecutionFailed as exc:
        return _receipt(
            profile,
            status=FormalCheckStatus.FAILED,
            reason=exc.reason,
            controls={},
            evidence=exc.evidence,
            expectations=expectations,
        )
    except _ExpectationsError as exc:
        return _receipt(
            profile,
            status=FormalCheckStatus.DRIFT,
            reason="formal_profile_drift",
            controls={},
            evidence={"error": str(exc)},
            expectations=expectations,
        )
    except Exception as exc:
        return _receipt(
            profile,
            status=FormalCheckStatus.FAILED,
            reason="formal_checker_internal_error",
            controls={},
            evidence={
                "exception_type": type(exc).__name__,
                "error": str(exc),
            },
            expectations=expectations,
        )
