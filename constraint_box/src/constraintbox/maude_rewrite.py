from __future__ import annotations

import hashlib
import importlib.metadata
import math
import os
import re
import selectors
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .contracts import Disposition, ProfileOutcome
from .intake import IntakeError, canonical_json, parse_json_object

try:  # POSIX-only boundary; absence is an admission failure, not a fallback.
    import resource
except ImportError:  # pragma: no cover - exercised through the boundary guard.
    resource = None  # type: ignore[assignment]


_PROFILE_ID = "constraintbox.formal.maude-transition.v1"
_REQUIRED_MAUDE_VERSION = "1.6.0"
_REQUIRED_MAUDE_CORE_VERSION = "3.5.1+smc"
_WORKER_SCHEMA = "constraintbox.maude-worker.request.v1"
_OBSERVATION_SCHEMA = "constraintbox.maude-worker.observation.v1"
_REQUEST_KEYS = {"from_state", "action", "to_state"}
_OBSERVATION_KEYS = {
    "schema",
    "status",
    "operation",
    "error_type",
    "error",
    "exact_api",
    "maude_version",
    "maude_core_version",
    "runtime_identity",
    "resource_limits",
    "module_name",
    "module_source_sha256",
    "module_loaded",
    "rule_inventory",
    "rule_inventory_overflow",
    "equation_count",
    "equation_inventory_overflow",
    "parsed_term",
    "applications",
    "application_count",
}
_RULE_INVENTORY_KEYS = {
    "label",
    "metadata",
    "lhs",
    "rhs",
    "has_condition",
}
_APPLICATION_KEYS = {
    "term",
    "rule_label",
    "rule_metadata",
    "substitution_size",
    "matched_portion",
    "context_callable",
}
_RUNTIME_IDENTITY_KEYS = {
    "wrapper",
    "native_extension",
    "core_library",
}
_ARTIFACT_IDENTITY_KEYS = {"path", "sha256"}
_EXACT_API = (
    "maude.init(loadPrelude=False, randomSeed=0, advise=False, "
    "handleInterrupts=False)",
    "maude.input(controller_rendered_module)",
    "maude.getModule(module_name)",
    "Module.getRules()",
    "Module.getEquations()",
    "Rule.getLabel()",
    "Rule.getMetadata()",
    "Rule.getLhs()",
    "Rule.getRhs()",
    "Rule.hasCondition()",
    "Module.parseTerm(encoded_state)",
    "Term.apply(rule_label, minDepth=0, maxDepth=0)",
    "Substitution.size()",
    "Substitution.matchedPortion()",
)
_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9._:-]{0,127}")
_HASH_RE = re.compile(r"[0-9a-f]{64}")
_HARD_MAX_STATES = 256
_HARD_MAX_RULES = 4_096
_HARD_MAX_APPLICATIONS = 16
_HARD_MAX_TIMEOUT_SECONDS = 30.0
_MAX_REQUEST_BYTES = 4_096
_MAX_WORKER_STDOUT_BYTES = 1_048_576
_MAX_WORKER_STDERR_BYTES = 65_536
_WORKER_CPU_GRACE_SECONDS = 1
_WORKER_TERMINATION_GRACE_SECONDS = 1.0
_WORKER_BOOTSTRAP_FAILURE_EXIT_CODE = 86
_WORKER_BOOTSTRAP_FAILURE_SIGNAL = b"\x01"
_HARD_MAX_WORKER_CPU_SECONDS = 31
_WORKER_MEMORY_LIMIT_BYTES = 1_073_741_824
_MIN_WORKER_MEMORY_LIMIT_BYTES = 134_217_728
_DARWIN_TASKPOLICY_PATH = Path("/usr/sbin/taskpolicy")
_RESOURCE_LIMIT_KEYS = {
    "cpu_seconds",
    "memory_limit_bytes",
    "memory_limit_mebibytes",
    "memory_limit_mechanism",
}
_EXPECTED_WORKER_SOURCE_SHA256 = (
    "34be7b60eca20d5c6eff1f45c21560de73d496eb8e7e8b678cc9f8f6470825a4"
)


class _ObservationError(ValueError):
    pass


class _RuntimePinMissing(FileNotFoundError):
    pass


class _RuntimePinDrift(RuntimeError):
    pass


class _WorkerResourceLimitUnavailable(OSError):
    """The host cannot enforce the required POSIX worker limits."""


@dataclass(frozen=True)
class _WorkerProcessResult:
    returncode: int
    stdout: bytes
    stderr: bytes
    stdout_overflow: bool
    stderr_overflow: bool


@dataclass(frozen=True)
class _WorkerResourceLimits:
    """Controller-selected OS limits for one isolated worker process."""

    cpu_seconds: int
    memory_limit_bytes: int
    memory_limit_mebibytes: int
    memory_limit_mechanism: str

    def as_dict(self) -> dict[str, int | str]:
        return {
            "cpu_seconds": self.cpu_seconds,
            "memory_limit_bytes": self.memory_limit_bytes,
            "memory_limit_mebibytes": self.memory_limit_mebibytes,
            "memory_limit_mechanism": self.memory_limit_mechanism,
        }


def _is_plain_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _valid_name(value: object) -> bool:
    return isinstance(value, str) and _NAME_RE.fullmatch(value) is not None


def _worker_path() -> Path:
    return Path(__file__).with_name("_maude_worker.py")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _maude_runtime_policy() -> dict[str, str]:
    """Return the portable compatibility contract, never local artifact pins."""

    return {
        "distribution": "maude",
        "required_version": _REQUIRED_MAUDE_VERSION,
        "required_core_version": _REQUIRED_MAUDE_CORE_VERSION,
    }


def _artifact_identity(path: Path, *, label: str) -> dict[str, str]:
    try:
        resolved = path.resolve(strict=True)
        if not resolved.is_file():
            raise FileNotFoundError(str(resolved))
        return {"path": str(resolved), "sha256": _file_sha256(resolved)}
    except (FileNotFoundError, OSError) as exc:
        raise _RuntimePinMissing(
            f"active Maude {label} artifact is unavailable"
        ) from exc


def _distribution_owns_artifact(
    distribution: importlib.metadata.Distribution,
    artifact: Path,
) -> bool:
    """Require the live module artifact to be listed by ``maude``'s wheel."""

    files = distribution.files
    if not files:
        raise _RuntimePinDrift("Maude distribution file inventory is unavailable")
    try:
        resolved = artifact.resolve(strict=True)
        return any(
            Path(distribution.locate_file(entry)).resolve(strict=True) == resolved
            for entry in files
        )
    except (FileNotFoundError, OSError) as exc:
        raise _RuntimePinMissing("Maude distribution artifact is unavailable") from exc


def _controller_runtime_identity() -> dict[str, dict[str, str]]:
    """Bind this run to the active interpreter's compatible Maude package.

    The wrapper, native extension, and core-library hashes are observations
    carried into the fresh worker so it cannot silently import another copy.
    They are deliberately *not* acceptance inputs for a particular machine or
    wheel build.  Version/API compatibility is the portable policy.
    """

    try:
        import maude  # type: ignore
    except (ImportError, ModuleNotFoundError) as exc:
        raise _RuntimePinMissing("Maude package is unavailable") from exc
    try:
        distribution = importlib.metadata.distribution("maude")
    except importlib.metadata.PackageNotFoundError as exc:
        raise _RuntimePinMissing("Maude distribution metadata is unavailable") from exc
    except Exception as exc:
        raise _RuntimePinDrift("Maude distribution metadata is unreadable") from exc

    version = getattr(maude, "__version__", None)
    core_version = getattr(maude, "MAUDE_VERSION", None)
    if (
        not isinstance(version, str)
        or version != _REQUIRED_MAUDE_VERSION
        or str(distribution.version) != version
        or not isinstance(core_version, str)
        or core_version != _REQUIRED_MAUDE_CORE_VERSION
    ):
        raise _RuntimePinDrift("active Maude runtime is outside the compatibility policy")

    wrapper_file = getattr(maude, "__file__", None)
    native_module = getattr(maude, "_maude", None)
    native_file = getattr(native_module, "__file__", None)
    if not isinstance(wrapper_file, str) or not isinstance(native_file, str):
        raise _RuntimePinDrift("active Maude module file metadata is unavailable")
    wrapper = Path(wrapper_file)
    native_extension = Path(native_file)
    core_candidates = tuple(
        native_extension.with_name(name)
        for name in ("libmaude.dylib", "libmaude.so", "libmaude.dll")
    )
    core_library = next((candidate for candidate in core_candidates if candidate.is_file()), None)
    if core_library is None:
        raise _RuntimePinMissing("active Maude core library is unavailable")
    artifacts = {
        "wrapper": wrapper,
        "native_extension": native_extension,
        "core_library": core_library,
    }
    if not all(_distribution_owns_artifact(distribution, path) for path in artifacts.values()):
        raise _RuntimePinDrift("active Maude module is not owned by its distribution")
    return {
        name: _artifact_identity(path, label=name)
        for name, path in artifacts.items()
    }


def _resource_limit_value(
    resource_name: str,
    *,
    requested: int,
    minimum: int,
) -> int:
    if resource is None:
        raise _WorkerResourceLimitUnavailable(
            "POSIX resource module is unavailable"
        )
    resource_id = getattr(resource, resource_name, None)
    if isinstance(resource_id, bool) or not isinstance(resource_id, int):
        raise _WorkerResourceLimitUnavailable(
            f"{resource_name} is unavailable on this POSIX host"
        )
    try:
        _soft, hard = resource.getrlimit(resource_id)
    except (OSError, ValueError) as exc:
        raise _WorkerResourceLimitUnavailable(
            f"cannot inspect {resource_name}"
        ) from exc
    if isinstance(hard, bool) or not isinstance(hard, int):
        raise _WorkerResourceLimitUnavailable(
            f"{resource_name} hard limit is invalid"
        )
    if hard == getattr(resource, "RLIM_INFINITY", None):
        return requested
    if hard < minimum:
        raise _WorkerResourceLimitUnavailable(
            f"{resource_name} hard limit is below the safe minimum"
        )
    return min(requested, hard)


def _worker_resource_limits(
    timeout_seconds: float,
) -> _WorkerResourceLimits:
    """Choose host-enforceable limits without an unbounded fallback.

    CPU uses a POSIX hard limit on every supported host.  Linux and other
    non-Darwin POSIX hosts must also support `RLIMIT_AS`.  Darwin exposes that
    constant but rejects it at runtime, so its native `taskpolicy -m` mechanism
    supplies the worker memory limit instead.  If either mechanism is missing,
    the controller parks the request before Maude starts.
    """

    if (
        resource is None
        or os.name != "posix"
        or not callable(getattr(os, "killpg", None))
        or not callable(getattr(resource, "getrlimit", None))
        or not callable(getattr(resource, "setrlimit", None))
    ):
        raise _WorkerResourceLimitUnavailable(
            "POSIX process-group and resource-limit support is unavailable"
        )
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise _WorkerResourceLimitUnavailable(
            "worker timeout cannot be converted to a CPU resource limit"
        )

    cpu_floor = max(1, int(math.ceil(timeout_seconds)))
    cpu_seconds = _resource_limit_value(
        "RLIMIT_CPU",
        requested=min(
            _HARD_MAX_WORKER_CPU_SECONDS,
            cpu_floor + _WORKER_CPU_GRACE_SECONDS,
        ),
        minimum=cpu_floor,
    )
    if sys.platform == "darwin":
        if (
            not _DARWIN_TASKPOLICY_PATH.is_file()
            or not os.access(_DARWIN_TASKPOLICY_PATH, os.X_OK)
        ):
            raise _WorkerResourceLimitUnavailable(
                "Darwin taskpolicy memory-limit support is unavailable"
            )
        memory_limit_bytes = _WORKER_MEMORY_LIMIT_BYTES
        mechanism = "darwin_taskpolicy"
    else:
        memory_limit_bytes = _resource_limit_value(
            "RLIMIT_AS",
            requested=_WORKER_MEMORY_LIMIT_BYTES,
            minimum=_MIN_WORKER_MEMORY_LIMIT_BYTES,
        )
        mechanism = "rlimit_as"
    return _WorkerResourceLimits(
        cpu_seconds=cpu_seconds,
        memory_limit_bytes=memory_limit_bytes,
        memory_limit_mebibytes=memory_limit_bytes // (1024 * 1024),
        memory_limit_mechanism=mechanism,
    )


def _worker_bootstrap_source(
    worker_source: bytes,
    limits: _WorkerResourceLimits,
    *,
    status_fd: int,
) -> str:
    """Build isolated child code that applies controller-owned limits first.

    `preexec_fn` would run after a multi-threaded controller has forked, which
    is unsafe once JAX or another native runtime has started threads.  This
    bootstrap instead runs in the fresh `-I` Python child before the pinned
    worker source (and therefore before Maude imports).  A dedicated inherited
    status descriptor is closed before the worker starts, so only bootstrap
    failures can signal the controller.  The worker still verifies the exact
    limits after the bootstrap transfers control.
    """

    if resource is None:
        raise _WorkerResourceLimitUnavailable(
            "POSIX resource module is unavailable for worker bootstrap"
        )
    resource_names: list[tuple[str, int]] = [
        ("RLIMIT_CPU", limits.cpu_seconds)
    ]
    if limits.memory_limit_mechanism == "rlimit_as":
        resource_names.append(("RLIMIT_AS", limits.memory_limit_bytes))
    elif limits.memory_limit_mechanism != "darwin_taskpolicy":
        raise _WorkerResourceLimitUnavailable(
            "worker memory-limit mechanism is invalid"
        )
    try:
        worker_text = worker_source.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _WorkerResourceLimitUnavailable(
            "worker source cannot be decoded for limit bootstrap"
        ) from exc
    return (
        "import os as _constraintbox_os\n"
        "try:\n"
        "    import resource as _constraintbox_resource\n"
        f"    _constraintbox_limits = {tuple(resource_names)!r}\n"
        "    for _constraintbox_name, _constraintbox_desired in "
        "_constraintbox_limits:\n"
        "        _constraintbox_id = getattr(\n"
        "            _constraintbox_resource, _constraintbox_name\n"
        "        )\n"
        "        _constraintbox_soft, _constraintbox_hard = "
        "_constraintbox_resource.getrlimit(_constraintbox_id)\n"
        "        _constraintbox_resource.setrlimit(\n"
        "            _constraintbox_id,\n"
        "            (_constraintbox_desired, _constraintbox_hard),\n"
        "        )\n"
        "        _constraintbox_resource.setrlimit(\n"
        "            _constraintbox_id,\n"
        "            (_constraintbox_desired, _constraintbox_desired),\n"
        "        )\n"
        f"    _constraintbox_os.close({status_fd})\n"
        "except BaseException as _constraintbox_error:\n"
        "    try:\n"
        f"        _constraintbox_os.write({status_fd}, "
        f"{_WORKER_BOOTSTRAP_FAILURE_SIGNAL!r})\n"
        "    except OSError:\n"
        "        pass\n"
        "    try:\n"
        f"        _constraintbox_os.close({status_fd})\n"
        "    except OSError:\n"
        "        pass\n"
        f"    raise SystemExit({_WORKER_BOOTSTRAP_FAILURE_EXIT_CODE})\n"
        f"exec(compile({worker_text!r}, '<pinned-maude-worker>', 'exec'))\n"
    )


def _bounded_append(
    buffer: bytearray,
    chunk: bytes,
    limit: int,
) -> bool:
    """Append a stream chunk without retaining a probe byte over ``limit``."""

    remaining = max(0, limit - len(buffer))
    if remaining:
        buffer.extend(chunk[:remaining])
    return len(chunk) > remaining


def _kill_worker_process_group(
    process: subprocess.Popen[bytes],
) -> None:
    """Kill the isolated worker session, including any descendants."""

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except (PermissionError, OSError):
        try:
            process.kill()
        except ProcessLookupError:
            return


def _run_worker(
    worker_source: bytes,
    job_bytes: bytes,
    timeout_seconds: float,
    *,
    resource_limits: _WorkerResourceLimits | None = None,
) -> _WorkerProcessResult:
    def close_fd(fd: int) -> None:
        try:
            os.close(fd)
        except OSError:
            pass

    limits = resource_limits or _worker_resource_limits(timeout_seconds)
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": os.defpath,
        "PYTHONHASHSEED": "0",
        "CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MEBIBYTES": str(
            limits.memory_limit_mebibytes
        ),
        "CONSTRAINTBOX_MAUDE_MEMORY_LIMIT_MECHANISM": (
            limits.memory_limit_mechanism
        ),
    }
    status_read, status_write = os.pipe()
    try:
        os.set_inheritable(status_write, True)
        bootstrap_source = _worker_bootstrap_source(
            worker_source,
            limits,
            status_fd=status_write,
        )
        command = [
            sys.executable,
            "-I",
            "-c",
            bootstrap_source,
        ]
        if limits.memory_limit_mechanism == "darwin_taskpolicy":
            command = [
                str(_DARWIN_TASKPOLICY_PATH),
                "-m",
                str(limits.memory_limit_mebibytes),
                *command,
            ]
        elif limits.memory_limit_mechanism != "rlimit_as":
            raise _WorkerResourceLimitUnavailable(
                "worker memory-limit mechanism is invalid"
            )
        started_at = time.monotonic()
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            # The session is deliberately separate before either timeout or
            # output-overflow cleanup can occur.
            start_new_session=True,
            pass_fds=(status_write,),
        )
    except BaseException:
        close_fd(status_read)
        close_fd(status_write)
        raise
    close_fd(status_write)
    selector = selectors.DefaultSelector()
    streams: dict[str, tuple[Any, bytearray, int]] = {}
    try:
        if process.stdin is None or process.stdout is None or process.stderr is None:
            _kill_worker_process_group(process)
            try:
                process.wait(timeout=_WORKER_TERMINATION_GRACE_SECONDS)
            except subprocess.TimeoutExpired as exc:
                raise OSError("worker subprocess did not exit after cleanup") from exc
            raise OSError("worker subprocess pipes are unavailable")
        streams = {
            "stdout": (
                process.stdout,
                bytearray(),
                _MAX_WORKER_STDOUT_BYTES,
            ),
            "stderr": (
                process.stderr,
                bytearray(),
                _MAX_WORKER_STDERR_BYTES,
            ),
        }
        for name, (stream, _buffer, _limit) in streams.items():
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, data=name)

        # Feeding the controller-authored job is part of the wall-clock
        # boundary.  A worker that never reads stdin must not prevent the
        # controller from reaching its deadline before it starts producing
        # output.
        os.set_blocking(process.stdin.fileno(), False)
        pending_input = memoryview(job_bytes)
        if pending_input:
            selector.register(
                process.stdin,
                selectors.EVENT_WRITE,
                data="stdin",
            )
        else:
            process.stdin.close()

        overflows = {"stdout": False, "stderr": False}
        deadline = started_at + timeout_seconds
        timed_out = False
        terminated = False
        termination_deadline: float | None = None

        def close_input() -> None:
            if process.stdin is None or process.stdin.closed:
                return
            try:
                selector.unregister(process.stdin)
            except KeyError:
                pass
            process.stdin.close()

        def terminate_worker(*, timeout: bool) -> None:
            nonlocal terminated, timed_out, termination_deadline
            timed_out = timed_out or timeout
            if terminated:
                return
            terminated = True
            close_input()
            _kill_worker_process_group(process)
            termination_deadline = (
                time.monotonic() + _WORKER_TERMINATION_GRACE_SECONDS
            )

        while selector.get_map():
            now = time.monotonic()
            active_deadline = termination_deadline or deadline
            if now >= active_deadline:
                if termination_deadline is not None:
                    # A descendant can deliberately retain a pipe after the
                    # process group is killed.  Close our pipe ends after a
                    # bounded grace period instead of waiting forever.
                    break
                terminate_worker(timeout=True)
                continue
            events = selector.select(
                timeout=min(max(active_deadline - now, 0.0), 0.1)
            )
            if not events and process.poll() is not None:
                events = [
                    (key, selectors.EVENT_READ)
                    for key in list(selector.get_map().values())
                ]
            for key, _mask in events:
                name = key.data
                if name == "stdin":
                    try:
                        written = os.write(process.stdin.fileno(), pending_input)
                    except BlockingIOError:
                        continue
                    except BrokenPipeError:
                        close_input()
                        continue
                    if written <= 0:
                        raise OSError("worker stdin write made no progress")
                    pending_input = pending_input[written:]
                    if not pending_input:
                        close_input()
                    continue
                stream, buffer, limit = streams[name]
                try:
                    chunk = os.read(stream.fileno(), 65_536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(stream)
                    stream.close()
                    continue
                if _bounded_append(buffer, chunk, limit):
                    overflows[name] = True
                    terminate_worker(timeout=False)

        for key in list(selector.get_map().values()):
            stream = key.fileobj
            try:
                selector.unregister(stream)
            except KeyError:
                pass
            stream.close()
        if terminated:
            _kill_worker_process_group(process)
        wait_timeout = _WORKER_TERMINATION_GRACE_SECONDS
        if not terminated:
            wait_timeout = max(0.001, deadline - time.monotonic())
        try:
            returncode = process.wait(timeout=wait_timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_worker_process_group(process)
            try:
                returncode = process.wait(
                    timeout=_WORKER_TERMINATION_GRACE_SECONDS
                )
            except subprocess.TimeoutExpired as exc:
                raise OSError(
                    "worker subprocess did not exit after process-group kill"
                ) from exc
        if process.returncode is not None:
            # The leader has exited. Remove any descendant that kept the
            # isolated process group alive.
            _kill_worker_process_group(process)
        bootstrap_status = os.read(status_read, 1)
        close_fd(status_read)
        status_read = -1
        if (
            returncode == _WORKER_BOOTSTRAP_FAILURE_EXIT_CODE
            and bootstrap_status == _WORKER_BOOTSTRAP_FAILURE_SIGNAL
        ):
            raise _WorkerResourceLimitUnavailable(
                "worker resource-limit bootstrap failed"
            )
        if timed_out:
            raise subprocess.TimeoutExpired(
                cmd=[sys.executable, "-I", "-c", "<pinned-maude-worker>"],
                timeout=timeout_seconds,
            )
        return _WorkerProcessResult(
            returncode=returncode,
            stdout=bytes(streams["stdout"][1]),
            stderr=bytes(streams["stderr"][1]),
            stdout_overflow=overflows["stdout"],
            stderr_overflow=overflows["stderr"],
        )
    except BaseException:
        _kill_worker_process_group(process)
        try:
            process.wait(timeout=_WORKER_TERMINATION_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            pass
        raise
    finally:
        if status_read >= 0:
            close_fd(status_read)
        selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None and not stream.closed:
                stream.close()


def _validate_observation_shape(observation: object) -> dict[str, Any]:
    if not isinstance(observation, dict):
        raise _ObservationError("worker observation must be an object")
    if set(observation) != _OBSERVATION_KEYS:
        raise _ObservationError("worker observation keys mismatch")
    if observation["schema"] != _OBSERVATION_SCHEMA:
        raise _ObservationError("worker observation schema mismatch")
    if observation["status"] not in {
        "ok",
        "dependency_unavailable",
        "runtime_unavailable",
        "operation_error",
        "invalid_job",
    }:
        raise _ObservationError("worker observation status is invalid")
    if not isinstance(observation["operation"], str):
        raise _ObservationError("worker operation must be a string")
    for key in (
        "error_type",
        "error",
        "maude_version",
        "maude_core_version",
        "module_name",
    ):
        if observation[key] is not None and not isinstance(
            observation[key], str
        ):
            raise _ObservationError(f"worker {key} has the wrong type")
    runtime_identity = observation["runtime_identity"]
    if not isinstance(runtime_identity, dict) or set(
        runtime_identity
    ) != _RUNTIME_IDENTITY_KEYS:
        raise _ObservationError("worker runtime identity is invalid")
    for artifact in runtime_identity.values():
        if (
            not isinstance(artifact, dict)
            or set(artifact) != _ARTIFACT_IDENTITY_KEYS
            or not isinstance(artifact["path"], str)
            or not isinstance(artifact["sha256"], str)
            or (
                artifact["sha256"]
                and _HASH_RE.fullmatch(artifact["sha256"]) is None
            )
        ):
            raise _ObservationError(
                "worker runtime artifact identity is invalid"
            )
    resource_limits = observation["resource_limits"]
    if (
        not isinstance(resource_limits, dict)
        or set(resource_limits) != _RESOURCE_LIMIT_KEYS
        or not _is_plain_int(resource_limits["cpu_seconds"])
        or resource_limits["cpu_seconds"] < 0
        or not _is_plain_int(resource_limits["memory_limit_bytes"])
        or resource_limits["memory_limit_bytes"] < 0
        or not _is_plain_int(resource_limits["memory_limit_mebibytes"])
        or resource_limits["memory_limit_mebibytes"] < 0
        or resource_limits["memory_limit_mechanism"]
        not in {"", "rlimit_as", "darwin_taskpolicy"}
    ):
        raise _ObservationError("worker resource limits are invalid")
    module_hash = observation["module_source_sha256"]
    if module_hash is not None and (
        not isinstance(module_hash, str)
        or _HASH_RE.fullmatch(module_hash) is None
    ):
        raise _ObservationError("worker module hash is invalid")
    if observation["exact_api"] != list(_EXACT_API):
        raise _ObservationError("worker exact API inventory mismatch")
    if not isinstance(observation["module_loaded"], bool):
        raise _ObservationError("worker module_loaded must be boolean")
    if (
        not isinstance(observation["rule_inventory_overflow"], bool)
        or not isinstance(observation["equation_inventory_overflow"], bool)
    ):
        raise _ObservationError("worker inventory overflow flag is invalid")
    if (
        not _is_plain_int(observation["equation_count"])
        or observation["equation_count"] < 0
    ):
        raise _ObservationError("worker equation_count is invalid")
    parsed_term = observation["parsed_term"]
    if parsed_term is not None and not isinstance(parsed_term, str):
        raise _ObservationError("worker parsed_term has the wrong type")

    inventory = observation["rule_inventory"]
    if not isinstance(inventory, list):
        raise _ObservationError("worker rule inventory must be a list")
    for item in inventory:
        if not isinstance(item, dict) or set(item) != _RULE_INVENTORY_KEYS:
            raise _ObservationError("worker rule inventory item is invalid")
        if any(
            not isinstance(item[key], str)
            for key in ("label", "metadata", "lhs", "rhs")
        ) or not isinstance(item["has_condition"], bool):
            raise _ObservationError(
                "worker rule inventory value has the wrong type"
            )

    applications = observation["applications"]
    if not isinstance(applications, list):
        raise _ObservationError("worker applications must be a list")
    for item in applications:
        if not isinstance(item, dict) or set(item) != _APPLICATION_KEYS:
            raise _ObservationError("worker application item is invalid")
        if any(
            not isinstance(item[key], str)
            for key in ("term", "rule_label", "rule_metadata")
        ):
            raise _ObservationError(
                "worker application value has the wrong type"
            )
        if (
            not _is_plain_int(item["substitution_size"])
            or item["substitution_size"] < 0
            or (
                item["matched_portion"] is not None
                and not isinstance(item["matched_portion"], str)
            )
            or not isinstance(item["context_callable"], bool)
        ):
            raise _ObservationError(
                "worker application match evidence is invalid"
            )
    application_count = observation["application_count"]
    if (
        not _is_plain_int(application_count)
        or application_count < 0
        or application_count != len(applications)
    ):
        raise _ObservationError("worker application count is invalid")
    return observation


@dataclass(frozen=True)
class MaudeTransitionProfile:
    """Check one controller-defined transition with one Maude rule application."""

    states: tuple[str, ...] = ("received", "validated")
    transitions: tuple[tuple[str, str, str], ...] = (
        ("received", "validate", "validated"),
    )
    max_states: int = 32
    max_rules: int = 128
    max_applications: int = 1
    timeout_seconds: float = 5.0
    required_maude_version: str = field(
        default=_REQUIRED_MAUDE_VERSION,
        init=False,
    )
    required_maude_core_version: str = field(
        default=_REQUIRED_MAUDE_CORE_VERSION,
        init=False,
    )
    worker_source_sha256: str = field(
        default=_EXPECTED_WORKER_SOURCE_SHA256,
        init=False,
    )
    profile_id: str = field(default=_PROFILE_ID, init=False)
    claim_ceiling: str = field(
        default=(
            "one bounded controller-defined transition was table-checked "
            "and separately observed on a ground nullary state term as "
            "exactly one root Maude rule application; no truth, confluence, "
            "termination, or liveness claim"
        ),
        init=False,
    )

    def __post_init__(self) -> None:
        if self.profile_id != _PROFILE_ID:
            raise ValueError(f"profile_id must be {_PROFILE_ID!r}")
        if self.required_maude_version != _REQUIRED_MAUDE_VERSION:
            raise ValueError(
                "required_maude_version must remain pinned to "
                f"{_REQUIRED_MAUDE_VERSION}"
            )
        if self.required_maude_core_version != _REQUIRED_MAUDE_CORE_VERSION:
            raise ValueError(
                "required_maude_core_version must remain pinned to "
                f"{_REQUIRED_MAUDE_CORE_VERSION}"
            )
        if (
            not isinstance(self.worker_source_sha256, str)
            or _HASH_RE.fullmatch(self.worker_source_sha256) is None
        ):
            raise ValueError("worker_source_sha256 must be a SHA-256 digest")
        if not isinstance(self.states, tuple) or not self.states:
            raise ValueError("states must be a non-empty tuple")
        if (
            any(not _valid_name(state) for state in self.states)
            or len(set(self.states)) != len(self.states)
            or self.states != tuple(sorted(self.states))
        ):
            raise ValueError(
                "states must be unique, canonically sorted bounded ASCII names"
            )
        if (
            not _is_plain_int(self.max_states)
            or not 1 <= self.max_states <= _HARD_MAX_STATES
        ):
            raise ValueError(
                f"max_states must be an integer from 1 through "
                f"{_HARD_MAX_STATES}"
            )
        if len(self.states) > self.max_states:
            raise ValueError("states exceed max_states")

        if not isinstance(self.transitions, tuple) or not self.transitions:
            raise ValueError("transitions must be a non-empty tuple")
        normalized: list[tuple[str, str, str]] = []
        for transition in self.transitions:
            if (
                not isinstance(transition, tuple)
                or len(transition) != 3
                or any(not _valid_name(part) for part in transition)
            ):
                raise ValueError(
                    "each transition must be a three-name tuple"
                )
            normalized.append(transition)
        if (
            len(set(normalized)) != len(normalized)
            or tuple(normalized) != tuple(sorted(normalized))
        ):
            raise ValueError(
                "transitions must be unique and canonically sorted"
            )
        state_set = set(self.states)
        if any(
            source not in state_set or target not in state_set
            for source, _action, target in normalized
        ):
            raise ValueError("transition endpoints must be declared states")
        transition_keys = [
            (source, action) for source, action, _target in normalized
        ]
        if len(set(transition_keys)) != len(transition_keys):
            raise ValueError(
                "transitions must be deterministic for each state/action pair"
            )
        if (
            not _is_plain_int(self.max_rules)
            or not 1 <= self.max_rules <= _HARD_MAX_RULES
        ):
            raise ValueError(
                f"max_rules must be an integer from 1 through "
                f"{_HARD_MAX_RULES}"
            )
        if len(normalized) > self.max_rules:
            raise ValueError("transitions exceed max_rules")
        if (
            not _is_plain_int(self.max_applications)
            or not 1 <= self.max_applications <= _HARD_MAX_APPLICATIONS
        ):
            raise ValueError(
                f"max_applications must be an integer from 1 through "
                f"{_HARD_MAX_APPLICATIONS}"
            )
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or not 0.05
            <= float(self.timeout_seconds)
            <= _HARD_MAX_TIMEOUT_SECONDS
        ):
            raise ValueError(
                "timeout_seconds must be finite and between 0.05 and "
                f"{_HARD_MAX_TIMEOUT_SECONDS}"
            )

    def _render(self) -> dict[str, Any]:
        state_tokens = {
            state: f"s{index}" for index, state in enumerate(self.states)
        }
        transition_rows: list[dict[str, str]] = []
        semantic_table: list[dict[str, str]] = []
        for index, (source, action, target) in enumerate(self.transitions):
            label = f"r{index}"
            metadata = f"constraintbox-transition-v1:{label}"
            transition_rows.append(
                {
                    "label": label,
                    "metadata": metadata,
                    "lhs": state_tokens[source],
                    "rhs": state_tokens[target],
                    "has_condition": False,
                }
            )
            semantic_table.append(
                {
                    "from_state": source,
                    "action": action,
                    "to_state": target,
                    "encoded_from": state_tokens[source],
                    "encoded_to": state_tokens[target],
                    "rule_label": label,
                    "rule_metadata": metadata,
                }
            )

        module_identity = {
            "profile_id": self.profile_id,
            "states": list(self.states),
            "transitions": [list(row) for row in self.transitions],
        }
        identity_hash = hashlib.sha256(
            canonical_json(module_identity)
        ).hexdigest()
        module_name = f"CBM_{identity_hash[:16].upper()}"
        operator_tokens = " ".join(state_tokens[state] for state in self.states)
        lines = [
            f"mod {module_name} is",
            "  sort State .",
            f"  ops {operator_tokens} : -> State [ctor] .",
        ]
        lines.extend(
            "  rl [{label}] : {lhs} => {rhs} "
            '[metadata "{metadata}"] .'.format(**row)
            for row in transition_rows
        )
        lines.append("endm")
        module_source = "\n".join(lines) + "\n"
        module_hash = hashlib.sha256(
            module_source.encode("utf-8")
        ).hexdigest()
        return {
            "module_name": module_name,
            "module_source": module_source,
            "module_source_sha256": module_hash,
            "state_tokens": state_tokens,
            "semantic_table": semantic_table,
            "expected_rule_inventory": transition_rows,
            "module_identity_sha256": identity_hash,
        }

    def _base_evidence(
        self,
        *,
        request: dict[str, str],
        rendered: dict[str, Any],
        worker_hash: str,
        runtime_identity: dict[str, dict[str, str]],
        resource_limits: _WorkerResourceLimits,
    ) -> dict[str, Any]:
        return {
            "schema": "constraintbox.maude-transition.evidence.v1",
            "tool": {
                "name": "maude",
                "required_version": self.required_maude_version,
                "required_core_version": self.required_maude_core_version,
                "runtime_policy": _maude_runtime_policy(),
                "controller_runtime_identity": runtime_identity,
                "artifact_sha256_is_policy_input": False,
                "worker_binding": (
                    "the fresh worker must import the same active-interpreter "
                    "Maude artifacts observed by the controller for this run"
                ),
                "exact_api": list(_EXACT_API),
                "worker_process_boundary": (
                    "fresh_python_isolated_mode_subprocess"
                ),
                "worker_os_sandboxed": False,
                "worker_has_disposition_authority": False,
                "worker_resource_limits": resource_limits.as_dict(),
            },
            "canonical_request": request,
            "canonical_request_sha256": hashlib.sha256(
                canonical_json(request)
            ).hexdigest(),
            "controller_transition_table": rendered["semantic_table"],
            "module_name": rendered["module_name"],
            "module_source_sha256": rendered["module_source_sha256"],
            "module_identity_sha256": rendered["module_identity_sha256"],
            "profile_source_sha256": _file_sha256(Path(__file__)),
            "worker_source_sha256": worker_hash,
            "expected_worker_source_sha256": self.worker_source_sha256,
            "limits": {
                "max_states": self.max_states,
                "max_rules": self.max_rules,
                "max_applications": self.max_applications,
                "timeout_seconds": float(self.timeout_seconds),
                "hard_max_states": _HARD_MAX_STATES,
                "hard_max_rules": _HARD_MAX_RULES,
                "hard_max_applications": _HARD_MAX_APPLICATIONS,
                "hard_max_timeout_seconds": _HARD_MAX_TIMEOUT_SECONDS,
                "max_request_bytes": _MAX_REQUEST_BYTES,
                "worker_cpu_grace_seconds": _WORKER_CPU_GRACE_SECONDS,
                "hard_max_worker_cpu_seconds": (
                    _HARD_MAX_WORKER_CPU_SECONDS
                ),
                "worker_memory_limit_bytes": (
                    resource_limits.memory_limit_bytes
                ),
                "worker_memory_limit_mechanism": (
                    resource_limits.memory_limit_mechanism
                ),
                "minimum_worker_memory_limit_bytes": (
                    _MIN_WORKER_MEMORY_LIMIT_BYTES
                ),
            },
            "claim_ceiling": self.claim_ceiling,
        }

    def evaluate(self, payload: bytes, run_dir: Path) -> ProfileOutcome:
        del run_dir
        if len(payload) > _MAX_REQUEST_BYTES:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_transition_request_too_large",
                {
                    "observed_bytes": len(payload),
                    "max_request_bytes": _MAX_REQUEST_BYTES,
                },
            )
        try:
            body = parse_json_object(payload)
        except IntakeError as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "strict_intake_failed",
                {"error": str(exc)},
            )
        if set(body) != _REQUEST_KEYS:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_transition_contract_keys_mismatch",
                {
                    "expected_keys": sorted(_REQUEST_KEYS),
                    "observed_keys": sorted(body),
                },
            )
        if any(not isinstance(body[key], str) for key in _REQUEST_KEYS):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_transition_contract_type_mismatch",
            )
        request = {
            "from_state": body["from_state"],
            "action": body["action"],
            "to_state": body["to_state"],
        }
        state_set = set(self.states)
        unknown_states = sorted(
            {
                request[key]
                for key in ("from_state", "to_state")
                if request[key] not in state_set
            }
        )
        if unknown_states:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_transition_state_unknown",
                {"unknown_states": unknown_states},
            )
        action_set = {action for _source, action, _target in self.transitions}
        if request["action"] not in action_set:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_transition_action_unavailable",
                {"action": request["action"]},
            )
        by_key = {
            (source, action): target
            for source, action, target in self.transitions
        }
        expected_target = by_key.get(
            (request["from_state"], request["action"])
        )
        if expected_target is None:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_transition_unavailable",
                {
                    "from_state": request["from_state"],
                    "action": request["action"],
                },
            )
        if request["to_state"] != expected_target:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_transition_target_mismatch",
                {
                    "expected_to_state": expected_target,
                    "claimed_to_state": request["to_state"],
                },
            )

        rendered = self._render()
        semantic_by_key = {
            (row["from_state"], row["action"]): row
            for row in rendered["semantic_table"]
        }
        expected_row = semantic_by_key[
            (request["from_state"], request["action"])
        ]
        runtime_policy = _maude_runtime_policy()
        try:
            runtime_identity = _controller_runtime_identity()
        except _RuntimePinMissing as exc:
            return ProfileOutcome(
                Disposition.PARKED,
                "maude_runtime_unavailable",
                {
                    "runtime_policy": runtime_policy,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        except _RuntimePinDrift as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_runtime_identity_drift",
                {
                    "runtime_policy": runtime_policy,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        try:
            resource_limits = _worker_resource_limits(
                float(self.timeout_seconds)
            )
        except _WorkerResourceLimitUnavailable as exc:
            return ProfileOutcome(
                Disposition.PARKED,
                "maude_worker_resource_limits_unavailable",
                {
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                    "requires": [
                        "POSIX process group",
                        "RLIMIT_CPU",
                        "RLIMIT_AS or Darwin taskpolicy -m",
                    ],
                },
            )
        worker = _worker_path()
        try:
            worker_source = worker.read_bytes()
            worker_hash = hashlib.sha256(worker_source).hexdigest()
        except OSError as exc:
            return ProfileOutcome(
                Disposition.PARKED,
                "maude_worker_unavailable",
                {
                    "worker_path": str(worker),
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        evidence = self._base_evidence(
            request=request,
            rendered=rendered,
            worker_hash=worker_hash,
            runtime_identity=runtime_identity,
            resource_limits=resource_limits,
        )
        if worker_hash != self.worker_source_sha256:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_source_drift",
                evidence,
            )

        worker_job = {
            "schema": _WORKER_SCHEMA,
            "module_name": rendered["module_name"],
            "module_source": rendered["module_source"],
            "module_source_sha256": rendered["module_source_sha256"],
            "source_term": expected_row["encoded_from"],
            "rule_label": expected_row["rule_label"],
            "max_applications": self.max_applications,
            # The worker's collection limit is the controller-rendered
            # inventory for this specific module, not the broader profile
            # capacity used while configuring the controller.
            "max_rules": len(rendered["expected_rule_inventory"]),
            "max_equations": 0,
            "cpu_limit_seconds": resource_limits.cpu_seconds,
            "memory_limit_bytes": resource_limits.memory_limit_bytes,
            "memory_limit_mebibytes": resource_limits.memory_limit_mebibytes,
            "memory_limit_mechanism": (
                resource_limits.memory_limit_mechanism
            ),
            "required_maude_version": self.required_maude_version,
            "required_maude_core_version": self.required_maude_core_version,
            "expected_maude_wrapper_path": runtime_identity["wrapper"]["path"],
            "expected_maude_wrapper_sha256": (
                runtime_identity["wrapper"]["sha256"]
            ),
            "expected_maude_native_extension_path": (
                runtime_identity["native_extension"]["path"]
            ),
            "expected_maude_native_extension_sha256": (
                runtime_identity["native_extension"]["sha256"]
            ),
            "expected_maude_core_library_path": (
                runtime_identity["core_library"]["path"]
            ),
            "expected_maude_core_library_sha256": (
                runtime_identity["core_library"]["sha256"]
            ),
        }
        job_bytes = canonical_json(worker_job)
        evidence["worker_job_sha256"] = hashlib.sha256(job_bytes).hexdigest()
        try:
            completed = _run_worker(
                worker_source,
                job_bytes,
                float(self.timeout_seconds),
                resource_limits=resource_limits,
            )
        except _WorkerResourceLimitUnavailable as exc:
            return ProfileOutcome(
                Disposition.PARKED,
                "maude_worker_resource_limits_unavailable",
                {
                    **evidence,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        except subprocess.TimeoutExpired as exc:
            return ProfileOutcome(
                Disposition.PARKED,
                "maude_worker_timeout",
                {
                    **evidence,
                    "timeout_seconds": float(self.timeout_seconds),
                    "exception_type": type(exc).__name__,
                },
            )
        except OSError as exc:
            return ProfileOutcome(
                Disposition.PARKED,
                "maude_runtime_unavailable",
                {
                    **evidence,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        except Exception as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_execution_error",
                {
                    **evidence,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )

        evidence["worker_returncode"] = completed.returncode
        evidence["worker_stdout_sha256"] = hashlib.sha256(
            completed.stdout
        ).hexdigest()
        evidence["worker_stderr_sha256"] = hashlib.sha256(
            completed.stderr
        ).hexdigest()
        if completed.stdout_overflow or completed.stderr_overflow:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_output_overflow",
                {
                    **evidence,
                    "stdout_overflow": completed.stdout_overflow,
                    "stderr_overflow": completed.stderr_overflow,
                    "max_stdout_bytes": _MAX_WORKER_STDOUT_BYTES,
                    "max_stderr_bytes": _MAX_WORKER_STDERR_BYTES,
                },
            )
        if (
            completed.returncode != 0
            or completed.stderr
        ):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_process_anomaly",
                {
                    **evidence,
                    "stderr": completed.stderr.decode(
                        "utf-8", errors="replace"
                    )[:4_096],
                },
            )
        try:
            parsed_observation = parse_json_object(completed.stdout)
            observation = _validate_observation_shape(parsed_observation)
        except (IntakeError, _ObservationError) as exc:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_observation_invalid",
                {
                    **evidence,
                    "exception_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        evidence["worker_observation"] = observation
        evidence["worker_observation_sha256"] = hashlib.sha256(
            canonical_json(observation)
        ).hexdigest()

        if (
            observation["module_name"] != rendered["module_name"]
            or observation["module_source_sha256"]
            != rendered["module_source_sha256"]
        ):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_module_binding_mismatch",
                evidence,
            )
        if observation["status"] == "dependency_unavailable":
            return ProfileOutcome(
                Disposition.PARKED,
                "maude_runtime_unavailable",
                evidence,
            )
        if observation["status"] == "operation_error":
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_operation_error",
                evidence,
            )
        if observation["status"] != "ok":
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_observation_anomalous",
                evidence,
            )
        if observation["runtime_identity"] != runtime_identity:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_runtime_identity_mismatch",
                evidence,
            )
        if observation["resource_limits"] != resource_limits.as_dict():
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_resource_limits_mismatch",
                evidence,
            )
        if (
            observation["operation"] != "complete"
            or observation["error_type"] is not None
            or observation["error"] is not None
            or observation["maude_version"] != self.required_maude_version
            or observation["maude_core_version"]
            != self.required_maude_core_version
            or observation["module_loaded"] is not True
            or observation["rule_inventory_overflow"] is not False
            or observation["equation_inventory_overflow"] is not False
            or len(observation["rule_inventory"]) > self.max_rules
            or observation["equation_count"] > 1
            or observation["equation_count"] != 0
            or observation["parsed_term"] != expected_row["encoded_from"]
            or observation["rule_inventory"]
            != rendered["expected_rule_inventory"]
        ):
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_inventory_disagreement",
                evidence,
            )

        applications = observation["applications"]
        if len(applications) != 1:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_application_cardinality_mismatch",
                evidence,
            )
        expected_application = {
            "term": expected_row["encoded_to"],
            "rule_label": expected_row["rule_label"],
            "rule_metadata": expected_row["rule_metadata"],
            "substitution_size": 0,
            "matched_portion": None,
            "context_callable": True,
        }
        if applications[0] != expected_application:
            return ProfileOutcome(
                Disposition.BLOCKED,
                "maude_worker_table_disagreement",
                {
                    **evidence,
                    "expected_application": expected_application,
                },
            )
        return ProfileOutcome(
            Disposition.ELIGIBLE,
            "maude_transition_observed",
            {
                **evidence,
                "expected_application": expected_application,
                "controller_table_agrees": True,
            },
        )
