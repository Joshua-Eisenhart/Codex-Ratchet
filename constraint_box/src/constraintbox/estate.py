from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from .intake import canonical_json, parse_json_object


class CapabilityState(str, Enum):
    READY = "READY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"
    DRIFT = "DRIFT"
    FAILED = "FAILED"
    UNTESTED = "UNTESTED"


@dataclass(frozen=True)
class CapabilityDefinition:
    module: str | None
    distribution: str | None
    oracle: str
    block_import: str | None
    external: str | None = None
    # Severance for an engine that runs in a SUBPROCESS. block_import severs a
    # Python import, which reaches nothing when the real work happens in an
    # external process. These env vars break the external binary, and
    # the capability is then required to FAIL.
    #
    # This is the control that catches a worker claiming an engine it never ran:
    # a receipt can be forged and a dispatch list is only a string, but a fake
    # does not break when you break the dependency it claims to use. Failing to
    # fail is the tell. Kept as a tuple so the definition stays hashable.
    sever_env: tuple[tuple[str, str], ...] = ()
    # (module, function) of the operation this capability CLAIMS to perform.
    # block_import only proves the module was reachable: a worker that imports
    # scipy, touches it, then computes with stdlib math passes severance while
    # scipy.linalg.expm never runs. Poisoning the named function discriminates —
    # a worker that really calls it dies, and one that merely imported the
    # module survives. Surviving is the failure.
    sever_operation: tuple[str, str] = ()


CAPABILITIES: dict[str, CapabilityDefinition] = {
    "stdlib_finite": CapabilityDefinition(None, None, "finite", None),
    "numpy_density": CapabilityDefinition(
        "numpy",
        "numpy",
        "density",
        "numpy",
        sever_operation=("numpy.linalg", "eigvalsh"),
    ),
    "scipy_channel": CapabilityDefinition(
        "scipy",
        "scipy",
        "channel",
        "scipy",
        sever_operation=("scipy.linalg", "expm"),
    ),
    "z3_finite": CapabilityDefinition("z3", "z3-solver", "solver", "z3"),
    "cvc5_finite": CapabilityDefinition("cvc5", "cvc5", "solver", "cvc5"),
    "jax_density": CapabilityDefinition("jax", "jax", "density", "jax"),
    "diffrax_flow": CapabilityDefinition(
        "diffrax", "diffrax", "flow", "diffrax"
    ),
    "quimb_tensor": CapabilityDefinition(
        "quimb", "quimb", "density", "quimb"
    ),
    "cotengra_path": CapabilityDefinition(
        "cotengra", "cotengra", "path", "cotengra"
    ),
    "torch_density": CapabilityDefinition(
        "torch", "torch", "density", "torch"
    ),
    "pysindy_law": CapabilityDefinition(
        "pysindy", "pysindy", "law", "pysindy"
    ),
    "pydmd_rate": CapabilityDefinition("pydmd", "PyDMD", "rate", "pydmd"),
    "pymdp_fep": CapabilityDefinition(
        "pymdp", "inferactively-pymdp", "fep", "pymdp"
    ),
    "pykoopman_rate": CapabilityDefinition(
        "pykoopman", "pykoopman", "unimplemented", "pykoopman"
    ),
    "dimod_anneal": CapabilityDefinition(
        "dimod", "dimod", "unimplemented", "dimod"
    ),
    "tla_controller": CapabilityDefinition(
        None, None, "external", None, external="java"
    ),
    "nvidia_device": CapabilityDefinition(
        None, None, "external", None, external="nvidia-smi"
    ),
    "jax_cuda_parity": CapabilityDefinition("jax", "jax", "gpu", "jax"),
    "torch_cuda_parity": CapabilityDefinition("torch", "torch", "gpu", "torch"),
    "cuquantum_tensor": CapabilityDefinition(
        "cuquantum", "cuquantum-python", "unimplemented", "cuquantum"
    ),
}


@dataclass(frozen=True)
class CapabilityReceipt:
    capability_id: str
    required: bool
    state: CapabilityState
    reason: str
    expected_version: str | None
    observed_version: str | None
    elapsed_seconds: float
    worker_sha256: str | None
    fixture_sha256: str
    controls: dict[str, bool]
    evidence: dict[str, Any]


@dataclass(frozen=True)
class SimTierReceipt:
    schema: str
    layer_id: str
    layer_name: str
    mode: str
    state: CapabilityState
    manifest_sha256: str
    fixture_sha256: str
    controller_sha256: str
    python_executable: str
    python_version: str
    environment: dict[str, Any]
    elapsed_seconds: float
    capabilities: tuple[CapabilityReceipt, ...]
    generated_at_utc: str = ""
    promotion_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        if not value["generated_at_utc"]:
            value["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
        value["state"] = self.state.value
        for row in value["capabilities"]:
            row["state"] = row["state"].value
        return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Bound retained worker stream text on non-READY receipts. Digests always cover
# the full original bytes; only the human-readable copy is capped.
STREAM_CAPTURE_BYTE_BUDGET = 8192

# Some real external packages compile/cache at import time (notably Numba via
# Quimb) or attempt a user-home configuration write (notably matplotlib via
# PyKoopman).  A capability worker must never inherit either cache location
# from the controller's user environment.  Each worker invocation receives two
# fresh controller-created directories instead.  They exist only for the child
# lifetime; their absolute names are deliberately not recorded in receipts.
_EPHEMERAL_WORKER_CACHE_ENV = ("NUMBA_CACHE_DIR", "MPLCONFIGDIR")

# Public protocol emitted only when the installed poison wrapper itself is
# called.  A generic nonzero worker exit is not operation evidence.
OPERATION_SEVERED_EXIT_CODE = 86
OPERATION_SEVERED_SIGNAL_PREFIX = b"constraintbox.operation-severed.v1:"


def _operation_severance_signal(operation: tuple[str, str]) -> bytes:
    return (
        OPERATION_SEVERED_SIGNAL_PREFIX
        + ".".join(operation).encode("utf-8")
        + b"\n"
    )


def _bounded_stream_text(
    data: bytes, budget: int = STREAM_CAPTURE_BYTE_BUDGET
) -> str:
    """Decode stream bytes for a receipt, truncating to *budget* with a marker.

    Truncation is explicit: when bytes are dropped the returned string ends with
    a marker naming how many bytes were omitted. Complete text has no marker.
    """
    if len(data) <= budget:
        return data.decode("utf-8", errors="replace")
    kept = data[:budget]
    dropped = len(data) - budget
    return (
        kept.decode("utf-8", errors="replace")
        + f"\n...[truncated: {dropped} bytes dropped]"
    )


def _stream_evidence(
    *,
    stdout: bytes | None = None,
    stderr: bytes | None = None,
    include_text: bool = False,
    prefix: str = "",
) -> dict[str, Any]:
    """Build digest (+ optional bounded text) evidence for captured streams.

    Digests are always taken over the full original bytes. Text is included only
    when *include_text* is true (failing / non-READY paths) and is bounded by
    STREAM_CAPTURE_BYTE_BUDGET.
    """
    key_prefix = f"{prefix}_" if prefix else ""
    evidence: dict[str, Any] = {}
    if stdout is not None:
        evidence[f"{key_prefix}stdout_sha256"] = hashlib.sha256(stdout).hexdigest()
        if include_text:
            evidence[f"{key_prefix}stdout"] = _bounded_stream_text(stdout)
    if stderr is not None:
        evidence[f"{key_prefix}stderr_sha256"] = hashlib.sha256(stderr).hexdigest()
        if include_text:
            evidence[f"{key_prefix}stderr"] = _bounded_stream_text(stderr)
    return evidence


def _eigenvalues_2x2(matrix: list[list[float]]) -> list[float]:
    a, b = matrix[0]
    c, d = matrix[1]
    trace = a + d
    determinant = a * d - b * c
    gap = math.sqrt(max(0.0, trace * trace - 4.0 * determinant))
    return sorted(((trace - gap) / 2.0, (trace + gap) / 2.0))


def _entropy_bits(eigenvalues: list[float]) -> float:
    return -sum(value * math.log2(value) for value in eigenvalues if value > 0)


def _expected(oracle: str, fixture: dict[str, Any]) -> dict[str, Any]:
    if oracle == "finite":
        histories = fixture["finite_histories"]
        present = sorted({row["present"] for row in histories})
        fibres = sorted(
            sum(1 for row in histories if row["present"] == value)
            for value in present
        )
        return {
            "history_count": len(histories),
            "projection_count": len(present),
            "fibre_sizes": fibres,
            "hartley_bits": math.log2(len(histories)),
        }
    if oracle == "density":
        eigenvalues = _eigenvalues_2x2(fixture["rho"])
        dephased_eigenvalues = _eigenvalues_2x2(fixture["dephased"])
        return {
            "trace": sum(fixture["rho"][i][i] for i in range(2)),
            "eigenvalues": eigenvalues,
            "rank": sum(value > 1e-12 for value in eigenvalues),
            "hartley_bits": math.log2(sum(value > 1e-12 for value in eigenvalues)),
            "von_neumann_bits": _entropy_bits(eigenvalues),
            "dephased_entropy_bits": _entropy_bits(dephased_eigenvalues),
        }
    if oracle == "channel":
        gamma = fixture["channel"]["gamma"]
        duration = fixture["channel"]["duration"]
        decay = math.exp(-2.0 * gamma * duration)
        return {
            "state": [(1.0 + decay) / 2.0, (1.0 - decay) / 2.0],
            "column_sum": 1.0,
        }
    if oracle == "solver":
        return {"sat": "sat", "unsat": "unsat"}
    if oracle == "flow":
        flow = fixture["flow"]
        return {
            "terminal": flow["initial"]
            * math.exp(flow["rate"] * flow["duration"])
        }
    if oracle == "law":
        return {"coefficient": fixture["flow"]["rate"]}
    if oracle == "rate":
        return {"eigenvalue": fixture["discrete_rate"]["multiplier"]}
    if oracle == "path":
        return {"positive_cost": True, "positive_max_size": True}
    if oracle == "fep":
        return {
            "posterior_sum": 1.0,
            "policy_sum": 1.0,
            "vfe_finite": True,
            "neg_efe_finite": True,
        }
    if oracle == "gpu":
        return _expected("density", fixture)
    return {}


def _close(expected: Any, observed: Any, tolerance: float = 5e-6) -> bool:
    if isinstance(expected, dict):
        return isinstance(observed, dict) and set(expected).issubset(observed) and all(
            _close(value, observed[key], tolerance) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return (
            isinstance(observed, list)
            and len(expected) == len(observed)
            and all(_close(a, b, tolerance) for a, b in zip(expected, observed, strict=True))
        )
    if isinstance(expected, float):
        return (
            isinstance(observed, (int, float))
            and not isinstance(observed, bool)
            and math.isfinite(float(observed))
            and abs(expected - float(observed)) <= tolerance
        )
    return expected == observed


class EstateRunner:
    def __init__(
        self,
        pack_root: Path,
        manifest_path: Path,
        fixture_path: Path,
        python_executable: Path | None = None,
        external_estate_root: Path | None = None,
    ):
        self.pack_root = pack_root.resolve()
        self.manifest_path = manifest_path.resolve()
        self.fixture_path = fixture_path.resolve()
        # Never Path.resolve() a virtual-environment interpreter. Resolving the
        # symlink can replace `<venv>/bin/python` with the base interpreter and
        # silently test a different dependency estate.
        selected_python = python_executable or Path(sys.executable)
        self.python = Path(os.path.abspath(os.fspath(selected_python)))
        legacy_local_workers = self.pack_root / "workers" / "estate"
        selected_external_root = (
            Path(external_estate_root).resolve()
            if external_estate_root is not None
            else Path(__file__).resolve().parents[3]
            / "external_sim_estate"
            / "legacy_estate_v2"
        )
        legacy_worker_names = (
            "capability_worker.py",
            "import_blocker.py",
            "operation_poisoner.py",
        )
        worker_root = (
            legacy_local_workers
            if all(
                (legacy_local_workers / name).is_file()
                for name in legacy_worker_names
            )
            else selected_external_root / "workers"
        )
        self.external_estate_root = selected_external_root
        self.worker = worker_root / "capability_worker.py"
        self.blocker = worker_root / "import_blocker.py"
        self.poisoner = (
            worker_root / "operation_poisoner.py"
        )
        self.manifest = parse_json_object(self.manifest_path.read_bytes())
        self.fixture = parse_json_object(self.fixture_path.read_bytes())
        self.controller_source = Path(__file__)
        self._worker_runtime_environment: dict[str, str] | None = None

    @contextmanager
    def _worker_cache_scope(self):
        """Give a whole capability run one controller-owned cache lifetime.

        Reusing the two private directories across positive, mutation, replay,
        and severance children avoids repeated package cache/font initialization
        while keeping every cache outside the user environment and removing it
        after the controller has collected all observations.
        """

        if self._worker_runtime_environment is not None:
            yield
            return
        with tempfile.TemporaryDirectory(
            prefix="constraintbox-worker-cache-"
        ) as temporary:
            root = Path(temporary)
            numba_cache = root / "numba"
            matplotlib_config = root / "matplotlib"
            numba_cache.mkdir()
            matplotlib_config.mkdir()
            self._worker_runtime_environment = {
                "NUMBA_CACHE_DIR": str(numba_cache),
                "MPLCONFIGDIR": str(matplotlib_config),
            }
            try:
                yield
            finally:
                self._worker_runtime_environment = None

    def _python_version(self) -> str:
        proc = subprocess.run(
            [
                str(self.python),
                "-I",
                "-c",
                "import platform; print(platform.python_version())",
            ],
            capture_output=True,
            check=False,
            timeout=10,
            env={
                key: value
                for key, value in os.environ.items()
                if key in {"PATH", "HOME", "TMPDIR"}
            },
        )
        if proc.returncode != 0:
            return "unknown"
        return proc.stdout.decode("utf-8", errors="replace").strip() or "unknown"

    def _controller_integrity(self) -> tuple[bool, str, str | None]:
        observed = _sha(self.controller_source)
        expected = self.manifest.get("controller_sha256")
        return bool(expected and observed == expected), observed, expected

    @staticmethod
    def _normalize_distribution(line: str) -> str:
        name, separator, version = line.partition("==")
        if not separator:
            return line.strip()
        normalized = "".join(
            "-" if character in "._-" else character.lower() for character in name
        )
        while "--" in normalized:
            normalized = normalized.replace("--", "-")
        return f"{normalized}=={version.strip()}"

    def _environment_snapshot(self, layer: dict[str, Any]) -> dict[str, Any]:
        script = (
            "import importlib.metadata as m,json;"
            "print(json.dumps(sorted("
            "f\"{d.metadata['Name']}=={d.version}\" for d in m.distributions())))"
        )
        proc = subprocess.run(
            [str(self.python), "-I", "-c", script],
            capture_output=True,
            check=False,
            timeout=15,
            env={
                key: value
                for key, value in os.environ.items()
                if key in {"PATH", "HOME", "TMPDIR"}
            },
        )
        if proc.returncode != 0:
            return {
                "state": "FAILED",
                "reason": "cannot_inventory_selected_interpreter",
                **_stream_evidence(stderr=proc.stderr, include_text=True),
            }
        try:
            raw_rows = json.loads(proc.stdout)
            observed = sorted(
                self._normalize_distribution(row)
                for row in raw_rows
                if isinstance(row, str)
            )
        except Exception:  # noqa: BLE001
            return {"state": "FAILED", "reason": "invalid_environment_inventory"}

        observed_bytes = ("\n".join(observed) + "\n").encode("utf-8")
        lock_name = layer.get("tested_lock")
        lock_sha = layer.get("tested_lock_sha256")
        if lock_name is None:
            return {
                "state": "UNPINNED",
                "distribution_count": len(observed),
                "observed_sha256": hashlib.sha256(observed_bytes).hexdigest(),
            }
        lock_path = self.pack_root / lock_name
        if not lock_path.is_file():
            return {
                "state": "DRIFT",
                "reason": "tested_lock_absent",
                "tested_lock": lock_name,
            }
        observed_lock_sha = _sha(lock_path)
        expected_rows = sorted(
            self._normalize_distribution(row)
            for row in lock_path.read_text(encoding="utf-8").splitlines()
            if row.strip() and not row.lstrip().startswith("#")
        )
        return {
            "state": (
                "READY"
                if observed == expected_rows and observed_lock_sha == lock_sha
                else "DRIFT"
            ),
            "tested_lock": lock_name,
            "tested_lock_sha256": observed_lock_sha,
            "expected_lock_sha256": lock_sha,
            "distribution_count": len(observed),
            "missing": sorted(set(expected_rows) - set(observed)),
            "unexpected": sorted(set(observed) - set(expected_rows)),
        }

    def _run_worker(
        self,
        capability_id: str,
        fixture_path: Path,
        timeout: float,
        *,
        blocked_import: str | None = None,
        extra_env: tuple[tuple[str, str], ...] = (),
        poison_operation: tuple[str, str] = (),
    ) -> tuple[int | None, bytes, bytes, float, bool]:
        if poison_operation:
            argv = [
                str(self.python),
                "-I",
                str(self.poisoner),
                poison_operation[0],
                poison_operation[1],
                str(self.worker),
                capability_id,
                str(fixture_path),
            ]
        elif blocked_import:
            argv = [
                str(self.python),
                "-I",
                str(self.blocker),
                blocked_import,
                str(self.worker),
                capability_id,
                str(fixture_path),
            ]
        else:
            argv = [
                str(self.python),
                "-I",
                str(self.worker),
                capability_id,
                str(fixture_path),
            ]
        started = time.monotonic()
        allowed_environment = {
            key: value
            for key, value in os.environ.items()
            if key
            in {
                "PATH",
                "HOME",
                "TMPDIR",
                "LD_LIBRARY_PATH",
                "DYLD_LIBRARY_PATH",
                "CUDA_VISIBLE_DEVICES",
                "XLA_FLAGS",
                "JAX_PLATFORMS",
            }
        }
        # Do not allow a caller's cache/config paths to cross this boundary.
        # The static tuple gives a testable policy surface even though those
        # names are not inherited by the whitelist above.
        for key in _EPHEMERAL_WORKER_CACHE_ENV:
            allowed_environment.pop(key, None)
        allowed_environment.update(dict(extra_env))
        if self._worker_runtime_environment is not None:
            allowed_environment.update(self._worker_runtime_environment)
            return self._invoke_worker_process(
                argv, allowed_environment, timeout, started
            )
        # Direct private-helper tests and one-off callers still get the same
        # policy; public capability/tier calls use `_worker_cache_scope()` so
        # their controls share a single short-lived directory pair.
        with self._worker_cache_scope():
            if self._worker_runtime_environment is None:
                raise RuntimeError("controller worker-cache scope was not established")
            allowed_environment.update(self._worker_runtime_environment)
            return self._invoke_worker_process(
                argv, allowed_environment, timeout, started
            )

    @staticmethod
    def _invoke_worker_process(
        argv: list[str],
        environment: dict[str, str],
        timeout: float,
        started: float,
    ) -> tuple[int | None, bytes, bytes, float, bool]:
        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                timeout=timeout,
                check=False,
                env=environment,
            )
        except subprocess.TimeoutExpired as exc:
            return (
                None,
                exc.stdout or b"",
                exc.stderr or b"",
                time.monotonic() - started,
                True,
            )
        return (
            proc.returncode,
            proc.stdout,
            proc.stderr,
            time.monotonic() - started,
            False,
        )

    def _external_receipt(
        self,
        capability_id: str,
        required: bool,
        expected_version: str | None,
        definition: CapabilityDefinition,
    ) -> CapabilityReceipt:
        executable = shutil.which(definition.external or "")
        return CapabilityReceipt(
            capability_id,
            required,
            CapabilityState.UNAVAILABLE if executable is None else CapabilityState.UNTESTED,
            "external_executable_absent"
            if executable is None
            else "external_acceptance_profile_not_executed",
            expected_version,
            None,
            0.0,
            None,
            _sha(self.fixture_path),
            {},
            {"executable": executable},
        )

    def _tla_receipt(
        self,
        capability: dict[str, Any],
        mode: str,
        timeout: float,
    ) -> CapabilityReceipt:
        required = bool(capability["required"])
        expected_version = capability.get("locked_version")
        fixture_sha = _sha(self.fixture_path)
        java = shutil.which("java")
        jar_value = os.environ.get("TLA2TOOLS_JAR")
        if java is None or not jar_value:
            return CapabilityReceipt(
                "tla_controller",
                required,
                CapabilityState.UNAVAILABLE,
                "java_or_TLA2TOOLS_JAR_absent",
                expected_version,
                None,
                0.0,
                None,
                fixture_sha,
                {},
                {"java": java, "jar_declared": bool(jar_value)},
            )
        jar = Path(jar_value)
        if not jar.is_file():
            return CapabilityReceipt(
                "tla_controller",
                required,
                CapabilityState.UNAVAILABLE,
                "declared_tla2tools_jar_absent",
                expected_version,
                None,
                0.0,
                None,
                fixture_sha,
                {},
                {"java": java, "jar": str(jar)},
            )
        expected_sha1 = capability.get("artifact_sha1")
        observed_sha1 = hashlib.sha1(jar.read_bytes()).hexdigest()  # noqa: S324
        artifact_ok = bool(expected_sha1 and observed_sha1 == expected_sha1)
        tla_dir = self.pack_root / "config" / "tla"
        tla = tla_dir / "ConstraintBox.tla"
        cfg = tla_dir / "ConstraintBox.cfg"

        def invoke(
            directory: Path, run_timeout: float
        ) -> tuple[int | None, bytes, bytes, float, bool]:
            started = time.monotonic()
            try:
                proc = subprocess.run(
                    [
                        java,
                        "-XX:+UseParallelGC",
                        "-jar",
                        str(jar),
                        "-config",
                        "ConstraintBox.cfg",
                        "ConstraintBox.tla",
                    ],
                    cwd=directory,
                    capture_output=True,
                    check=False,
                    timeout=run_timeout,
                    env={
                        key: value
                        for key, value in os.environ.items()
                        if key in {"PATH", "HOME", "TMPDIR"}
                    },
                )
                return (
                    proc.returncode,
                    proc.stdout,
                    proc.stderr,
                    time.monotonic() - started,
                    False,
                )
            except subprocess.TimeoutExpired as exc:
                return (
                    None,
                    exc.stdout or b"",
                    exc.stderr or b"",
                    time.monotonic() - started,
                    True,
                )

        code, stdout, stderr, elapsed, positive_timed_out = invoke(tla_dir, timeout)
        controls_timed_out = ["positive"] if positive_timed_out else []
        positive = (
            not positive_timed_out
            and artifact_ok
            and code == 0
            and b"Model checking completed. No error has been found." in stdout
            and b"45 distinct states found" in stdout
        )
        controls = {
            "artifact_hash": artifact_ok,
            "positive": positive,
            "dispatch": b"TLC2 Version" in stdout,
        }
        if mode == "acceptance":
            with tempfile.TemporaryDirectory(prefix="constraintbox-tla-") as temp:
                temp_dir = Path(temp)
                mutated = tla.read_text(encoding="utf-8").replace(
                    'disposition = "ELIGIBLE" => evidence /= {}',
                    'disposition = "ELIGIBLE" => evidence = {}',
                )
                (temp_dir / tla.name).write_text(mutated, encoding="utf-8")
                (temp_dir / cfg.name).write_bytes(cfg.read_bytes())
                (
                    mutation_code,
                    mutation_out,
                    _,
                    mutation_elapsed,
                    mutation_timed_out,
                ) = invoke(
                    temp_dir, timeout
                )
            elapsed += mutation_elapsed
            if mutation_timed_out:
                controls_timed_out.append("mutation")
            controls["mutation"] = (
                not mutation_timed_out
                and mutation_code != 0
                and b"Invariant EvidenceBeforeEligibility is violated"
                in mutation_out
            )
            (
                replay_code,
                replay_out,
                _,
                replay_elapsed,
                replay_timed_out,
            ) = invoke(tla_dir, timeout)
            elapsed += replay_elapsed
            if replay_timed_out:
                controls_timed_out.append("replay")
            # The middle conjunct used to be `sha256(replay_out).hexdigest() != ""`,
            # which is true for every possible input including empty bytes — a
            # tautology dressed as a digest comparison. A replay control has to
            # compare the replay to the base run, as _nvidia_receipt does.
            controls["replay"] = (
                not replay_timed_out
                and replay_code == 0
                and replay_out == stdout
                and b"Model checking completed. No error has been found."
                in replay_out
            )
        passed = all(controls.values())
        return CapabilityReceipt(
            "tla_controller",
            required,
            CapabilityState.READY if passed else CapabilityState.FAILED,
            "all_required_controls_passed"
            if passed
            else "one_or_more_controls_failed",
            expected_version,
            expected_version if artifact_ok else None,
            elapsed,
            None,
            fixture_sha,
            controls,
            {
                "java": java,
                "jar_sha1": observed_sha1,
                "jar_sha256": hashlib.sha256(jar.read_bytes()).hexdigest(),
                "tla_sha256": _sha(tla),
                "cfg_sha256": _sha(cfg),
                **(
                    {"controls_timed_out": sorted(controls_timed_out)}
                    if controls_timed_out
                    else {}
                ),
                **_stream_evidence(
                    stdout=stdout,
                    stderr=stderr,
                    include_text=not passed,
                ),
            },
        )

    def _nvidia_receipt(
        self,
        required: bool,
        expected_version: str | None,
        mode: str,
        timeout: float,
    ) -> CapabilityReceipt:
        fixture_sha = _sha(self.fixture_path)
        executable = shutil.which("nvidia-smi")
        if executable is None:
            return CapabilityReceipt(
                "nvidia_device",
                required,
                CapabilityState.UNAVAILABLE,
                "nvidia_smi_absent",
                expected_version,
                None,
                0.0,
                None,
                fixture_sha,
                {},
                {"executable": None},
            )
        argv = [
            executable,
            "--query-gpu=uuid,name,driver_version,memory.total",
            "--format=csv,noheader,nounits",
        ]

        def invoke() -> tuple[int | None, bytes, bytes, float, bool]:
            started = time.monotonic()
            try:
                proc = subprocess.run(
                    argv,
                    capture_output=True,
                    check=False,
                    timeout=timeout,
                    env={
                        key: value
                        for key, value in os.environ.items()
                        if key in {"PATH", "HOME", "TMPDIR"}
                    },
                )
                return (
                    proc.returncode,
                    proc.stdout,
                    proc.stderr,
                    time.monotonic() - started,
                    False,
                )
            except subprocess.TimeoutExpired as exc:
                return (
                    None,
                    exc.stdout or b"",
                    exc.stderr or b"",
                    time.monotonic() - started,
                    True,
                )

        code, stdout, stderr, elapsed, positive_timed_out = invoke()
        controls_timed_out = ["positive"] if positive_timed_out else []
        rows = [
            row.strip()
            for row in stdout.decode("utf-8", errors="replace").splitlines()
            if row.strip()
        ]
        controls = {
            "positive": not positive_timed_out and code == 0 and bool(rows),
            "dispatch": True,
        }
        if mode == "acceptance":
            replay_code, replay_out, _, replay_elapsed, replay_timed_out = invoke()
            elapsed += replay_elapsed
            if replay_timed_out:
                controls_timed_out.append("replay")
            controls["replay"] = (
                not replay_timed_out
                and replay_code == 0
                and replay_out == stdout
            )
        passed = all(controls.values())
        return CapabilityReceipt(
            "nvidia_device",
            required,
            CapabilityState.READY if passed else CapabilityState.FAILED,
            "all_required_controls_passed"
            if passed
            else "one_or_more_controls_failed",
            expected_version,
            None,
            elapsed,
            None,
            fixture_sha,
            controls,
            {
                "executable": executable,
                "devices": rows,
                **(
                    {"controls_timed_out": sorted(controls_timed_out)}
                    if controls_timed_out
                    else {}
                ),
                **_stream_evidence(
                    stdout=stdout,
                    stderr=stderr,
                    include_text=not passed,
                ),
            },
        )

    def run_capability(
        self,
        capability: dict[str, Any],
        mode: str,
        timeout: float,
    ) -> CapabilityReceipt:
        """Run one capability with one private cache/config lifetime."""

        if self._worker_runtime_environment is not None:
            return self._run_capability(capability, mode, timeout)
        with self._worker_cache_scope():
            return self._run_capability(capability, mode, timeout)

    def _run_capability(
        self,
        capability: dict[str, Any],
        mode: str,
        timeout: float,
    ) -> CapabilityReceipt:
        capability_id = capability["id"]
        required = bool(capability["required"])
        expected_version = capability.get("locked_version")
        definition = CAPABILITIES.get(capability_id)
        fixture_sha = _sha(self.fixture_path)
        if definition is None:
            return CapabilityReceipt(
                capability_id,
                required,
                CapabilityState.UNTESTED,
                "capability_not_registered_by_controller",
                expected_version,
                None,
                0.0,
                None,
                fixture_sha,
                {},
                {},
            )
        if capability_id == "tla_controller":
            return self._tla_receipt(capability, mode, timeout)
        if capability_id == "nvidia_device":
            return self._nvidia_receipt(
                required, expected_version, mode, timeout
            )
        if definition.external:
            return self._external_receipt(
                capability_id, required, expected_version, definition
            )
        if definition.oracle == "unimplemented":
            return CapabilityReceipt(
                capability_id,
                required,
                CapabilityState.UNTESTED,
                "acceptance_profile_not_implemented",
                expected_version,
                None,
                0.0,
                None,
                fixture_sha,
                {},
                {},
            )
        worker_sha = _sha(self.worker)
        required_worker_sha = self.manifest.get("worker_sha256")
        blocker_sha = _sha(self.blocker)
        required_blocker_sha = self.manifest.get("import_blocker_sha256")
        poisoner_sha = _sha(self.poisoner) if self.poisoner.is_file() else None
        required_poisoner_sha = self.manifest.get(
            "operation_poisoner_sha256"
        )
        # v2 is the live, source-bound protocol.  Legacy v1 test manifests are
        # still runnable, but their receipts explicitly carry the lower
        # causality ceiling below.
        poisoner_pin_required = (
            bool(definition.sever_operation)
            and self.manifest.get("schema")
            == "constraintbox.sim-estate.v2"
        )
        if (
            not required_worker_sha
            or worker_sha != required_worker_sha
            or not required_blocker_sha
            or blocker_sha != required_blocker_sha
            or (
                poisoner_pin_required
                and (
                    not required_poisoner_sha
                    or poisoner_sha != required_poisoner_sha
                )
            )
        ):
            return CapabilityReceipt(
                capability_id,
                required,
                CapabilityState.DRIFT,
                "worker_source_digest_mismatch",
                expected_version,
                None,
                0.0,
                worker_sha,
                fixture_sha,
                {},
                {
                    "expected_worker_sha256": required_worker_sha,
                    "observed_import_blocker_sha256": blocker_sha,
                    "expected_import_blocker_sha256": required_blocker_sha,
                    "observed_operation_poisoner_sha256": poisoner_sha,
                    "expected_operation_poisoner_sha256": (
                        required_poisoner_sha
                    ),
                },
            )

        base_code, base_out, base_err, elapsed, base_timed_out = self._run_worker(
            capability_id, self.fixture_path, timeout
        )
        if base_timed_out or base_code != 0:
            unavailable = (
                not base_timed_out
                and (
                    b"ModuleNotFoundError" in base_err
                    or b"ImportError" in base_err
                )
            )
            return CapabilityReceipt(
                capability_id,
                required,
                CapabilityState.UNAVAILABLE if unavailable else CapabilityState.FAILED,
                (
                    "positive_witness_timed_out"
                    if base_timed_out
                    else "dependency_unavailable"
                    if unavailable
                    else "positive_witness_failed"
                ),
                expected_version,
                None,
                elapsed,
                worker_sha,
                fixture_sha,
                {"positive": False},
                {
                    "exit_code": base_code,
                    "controls_timed_out": ["positive"] if base_timed_out else [],
                    **_stream_evidence(
                        stdout=base_out,
                        stderr=base_err,
                        include_text=True,
                    ),
                },
            )
        try:
            base = parse_json_object(base_out)
        except Exception as exc:  # noqa: BLE001
            return CapabilityReceipt(
                capability_id,
                required,
                CapabilityState.FAILED,
                "worker_output_invalid",
                expected_version,
                None,
                elapsed,
                worker_sha,
                fixture_sha,
                {"positive": False},
                {"error": str(exc)},
            )
        observed_version = base.get("version")
        version_drift = (
            expected_version is not None and observed_version != expected_version
        )

        expected = _expected(definition.oracle, self.fixture)
        observed = base.get("observed", {})
        if definition.oracle == "path":
            positive = (
                isinstance(observed, dict)
                and observed.get("contraction_cost", 0) > 0
                and observed.get("max_size", 0) > 0
            )
        elif definition.oracle == "law":
            expected_coefficient = expected["coefficient"]
            positive = (
                isinstance(observed, dict)
                and abs(observed.get("coefficient", math.inf) - expected_coefficient)
                <= 5e-3
                and observed.get("true_residual", math.inf)
                < observed.get("wrong_residual", 0.0) * 1e-3
                and base.get("runtime", {}).get("feature_library")
                == "polynomial_degree_1_no_bias"
            )
        else:
            positive = _close(expected, observed)
        if definition.oracle == "gpu":
            positive = positive and base.get("runtime", {}).get("platform") == "gpu"
        dispatch = bool(base.get("dispatch"))
        controls = {"positive": positive, "dispatch": dispatch}
        evidence: dict[str, Any] = {
            "stdout_sha256": hashlib.sha256(base_out).hexdigest(),
            "observed": base.get("observed", {}),
            "dispatch": base.get("dispatch", []),
            "runtime": base.get("runtime", {}),
            "controller_worker_environment": {
                "ephemeral_cache_config": list(_EPHEMERAL_WORKER_CACHE_ENV),
                "host_cache_config_inherited": False,
            },
        }
        if definition.sever_operation:
            evidence.update(
                {
                    "operation_target": ".".join(
                        definition.sever_operation
                    ),
                    "operation_poisoner_sha256": poisoner_sha,
                    "operation_poisoner_source_pinned": bool(
                        required_poisoner_sha
                        and poisoner_sha == required_poisoner_sha
                    ),
                    "operation_causality_ceiling": (
                        "source-pinned adapter and exact severance protocol; "
                        "not arbitrary hostile-process containment"
                    ),
                }
            )
        if version_drift:
            evidence["version_drift"] = {
                "expected": expected_version,
                "observed": str(observed_version),
            }
        mut_out = b""
        mut_err = b""
        replay_out = b""
        replay_err = b""
        sever_out = b""
        sever_err = b""
        poison_out = b""
        poison_err = b""
        controls_timed_out: list[str] = []
        if mode == "acceptance":
            mutated = json.loads(json.dumps(self.fixture))
            mutated["rho"][0][1] = mutated["rho"][1][0] = 0.125
            mutated["flow"]["rate"] = -1.5
            mutated["discrete_rate"]["multiplier"] = 0.4
            mutated["channel"]["gamma"] = 0.5
            mutated["finite_histories"] = mutated["finite_histories"][:-1]
            with tempfile.TemporaryDirectory(prefix="constraintbox-estate-") as temp:
                mutated_path = Path(temp) / "fixture.json"
                mutated_path.write_bytes(canonical_json(mutated))
                (
                    mut_code,
                    mut_out,
                    mut_err,
                    mut_elapsed,
                    mut_timed_out,
                ) = self._run_worker(
                    capability_id, mutated_path, timeout
                )
            elapsed += mut_elapsed
            if mut_timed_out:
                controls_timed_out.append("mutation")
            try:
                mut_body = (
                    parse_json_object(mut_out)
                    if not mut_timed_out and mut_code == 0
                    else {}
                )
            except Exception:
                mut_body = {}
            if definition.oracle in {
                "finite",
                "density",
                "channel",
                "flow",
                "law",
                "rate",
                "gpu",
            }:
                mutated_expected = _expected(definition.oracle, mutated)
                if definition.oracle == "law":
                    mutated_observed = mut_body.get("observed", {})
                    mutation_matches = (
                        isinstance(mutated_observed, dict)
                        and abs(
                            mutated_observed.get("coefficient", math.inf)
                            - mutated_expected["coefficient"]
                        )
                        <= 5e-3
                        and mutated_observed.get("true_residual", math.inf)
                        < mutated_observed.get("wrong_residual", 0.0) * 1e-3
                    )
                else:
                    mutation_matches = _close(
                        mutated_expected, mut_body.get("observed", {})
                    )
                mutation = (
                    not mut_timed_out
                    and mut_code == 0
                    and mutation_matches
                    and mut_body.get("observed") != base.get("observed")
                )
                controls["mutation"] = mutation

            (
                replay_code,
                replay_out,
                replay_err,
                replay_elapsed,
                replay_timed_out,
            ) = self._run_worker(capability_id, self.fixture_path, timeout)
            elapsed += replay_elapsed
            if replay_timed_out:
                controls_timed_out.append("replay")
            try:
                replay = (
                    parse_json_object(replay_out)
                    if not replay_timed_out and replay_code == 0
                    else {}
                )
            except Exception:
                replay = {}
            replay_ok = replay.get("observed") == base.get("observed")
            controls["replay"] = not replay_timed_out and replay_ok

            if definition.block_import or definition.sever_env:
                (
                    sever_code,
                    sever_out,
                    sever_err,
                    sever_elapsed,
                    sever_timed_out,
                ) = self._run_worker(
                    capability_id,
                    self.fixture_path,
                    timeout,
                    blocked_import=definition.block_import,
                    extra_env=definition.sever_env,
                )
                elapsed += sever_elapsed
                if sever_timed_out:
                    controls_timed_out.append("severance")
                controls["severance"] = (
                    not sever_timed_out and sever_code != 0
                )

            if definition.sever_operation:
                (
                    poison_code,
                    poison_out,
                    poison_err,
                    poison_elapsed,
                    poison_timed_out,
                ) = (
                    self._run_worker(
                        capability_id,
                        self.fixture_path,
                        timeout,
                        poison_operation=definition.sever_operation,
                    )
                )
                elapsed += poison_elapsed
                if poison_timed_out:
                    controls_timed_out.append("operation")
                expected_signal = _operation_severance_signal(
                    definition.sever_operation
                )
                exact_cause = (
                    not poison_timed_out
                    and poison_code == OPERATION_SEVERED_EXIT_CODE
                    and poison_out == b""
                    and poison_err == expected_signal
                )
                controls["operation"] = exact_cause
                evidence.update(
                    {
                        "operation_expected_exit_code": (
                            OPERATION_SEVERED_EXIT_CODE
                        ),
                        "operation_observed_exit_code": poison_code,
                        "operation_expected_signal_sha256": hashlib.sha256(
                            expected_signal
                        ).hexdigest(),
                        "operation_observed_signal_sha256": hashlib.sha256(
                            poison_err
                        ).hexdigest(),
                    }
                )
                if exact_cause:
                    evidence["operation_severed"] = ".".join(
                        definition.sever_operation
                    )
                if not poison_timed_out and poison_code == 0:
                    evidence["operation_never_called"] = True
                elif not poison_timed_out and not exact_cause:
                    evidence["operation_severance_cause_unconfirmed"] = (
                        "generic_or_worker_selected_failure"
                    )

        if controls_timed_out:
            # A timeout was attempted but produced no verdict. It is neither a
            # legitimate exemption nor a measured failure of the dependency,
            # so record it separately and force the attempted control false.
            # This keeps capability state and CLI disposition fail-closed.
            evidence["controls_timed_out"] = sorted(controls_timed_out)
            for name in controls_timed_out:
                controls[name] = False
        passed = all(controls.values())
        if not passed:
            # Keep digests already present; add bounded stream text for diagnosis.
            # Base run succeeded as JSON, so attach acceptance-control streams that
            # failed (mutation / replay / severance / operation) plus base
            # stderr if any.
            evidence.update(
                _stream_evidence(
                    stdout=base_out,
                    stderr=base_err,
                    include_text=True,
                )
            )
            if mode == "acceptance":
                if controls.get("mutation") is False:
                    evidence.update(
                        _stream_evidence(
                            stdout=mut_out,
                            stderr=mut_err,
                            include_text=True,
                            prefix="mutation",
                        )
                    )
                if controls.get("replay") is False:
                    evidence.update(
                        _stream_evidence(
                            stdout=replay_out,
                            stderr=replay_err,
                            include_text=True,
                            prefix="replay",
                        )
                    )
                if controls.get("severance") is False:
                    evidence.update(
                        _stream_evidence(
                            stdout=sever_out,
                            stderr=sever_err,
                            include_text=True,
                            prefix="severance",
                        )
                    )
                if controls.get("operation") is False:
                    evidence.update(
                        _stream_evidence(
                            stdout=poison_out,
                            stderr=poison_err,
                            include_text=True,
                            prefix="operation",
                        )
                    )
        # A control that was never inserted is not a control that passed.
        # `all(controls.values())` is vacuously true over whatever keys happen to
        # exist: mutation is only set for some oracles, severance only when
        # block_import is set. Exempting a control is legitimate; claiming it ran
        # is not. Record the gap and refuse to say "all".
        expected_controls = {"positive", "dispatch"}
        if mode == "acceptance":
            expected_controls |= {"mutation", "replay", "severance"}
        not_measured = sorted(expected_controls - set(controls))
        if not_measured:
            evidence["controls_not_measured"] = not_measured
        return CapabilityReceipt(
            capability_id,
            required,
            (
                CapabilityState.DRIFT
                if version_drift
                else CapabilityState.READY
                if passed
                else CapabilityState.FAILED
            ),
            (
                (
                    "installed_version_differs_from_tested_lock"
                    if passed
                    else (
                        "installed_version_differs_from_tested_lock"
                        "_and_one_or_more_controls_failed"
                    )
                )
                if version_drift
                else (
                    "all_required_controls_passed"
                    if passed and not not_measured
                    else "measured_controls_passed_others_not_run"
                    if passed
                    else "one_or_more_controls_failed"
                )
            ),
            expected_version,
            str(observed_version),
            elapsed,
            worker_sha,
            fixture_sha,
            controls,
            evidence,
        )

    def run_tier(self, tier_id: str, mode: str = "boot") -> SimTierReceipt:
        """Run one simulation-estate installation tier.

        These tiers belong to the sim-engine setup sequence. They are not
        ConstraintBox authority levels and are not scientific manifold layers.
        """
        if mode not in {"boot", "acceptance"}:
            raise ValueError("mode must be boot or acceptance")
        tiers = self.manifest.get("tiers", self.manifest.get("layers", []))
        tier = next(
            (
                row
                for row in tiers
                if row.get("tier_id", row.get("layer_id")) == tier_id
            ),
            None,
        )
        if tier is None:
            raise ValueError(f"unknown simulation-estate tier: {tier_id}")
        started = time.monotonic()
        controller_ok, controller_sha, expected_controller_sha = (
            self._controller_integrity()
        )
        environment = self._environment_snapshot(tier)
        if not controller_ok:
            rows = tuple(
                CapabilityReceipt(
                    capability["id"],
                    bool(capability["required"]),
                    CapabilityState.DRIFT,
                    "controller_source_digest_mismatch",
                    capability.get("locked_version"),
                    None,
                    0.0,
                    None,
                    _sha(self.fixture_path),
                    {},
                    {
                        "observed_controller_sha256": controller_sha,
                        "expected_controller_sha256": expected_controller_sha,
                    },
                )
                for capability in tier["capabilities"]
            )
            return SimTierReceipt(
                "constraintbox.sim-tier-receipt.v2",
                tier_id,
                tier["name"],
                mode,
                CapabilityState.DRIFT,
                _sha(self.manifest_path),
                _sha(self.fixture_path),
                controller_sha,
                str(self.python),
                self._python_version(),
                environment,
                time.monotonic() - started,
                rows,
            )
        timeout = float(tier["boot_budget_seconds"])
        rows = tuple(
            self.run_capability(capability, mode, timeout)
            for capability in tier["capabilities"]
        )
        rows_by_id = {row.capability_id: row for row in rows}
        required_sets = tier.get("required_capability_sets", [])
        route_members = {
            capability_id
            for route in required_sets
            for capability_id in route
        }
        route_ready = (
            not required_sets
            or any(
                all(
                    capability_id in rows_by_id
                    and rows_by_id[capability_id].state is CapabilityState.READY
                    for capability_id in route
                )
                for route in required_sets
            )
        )
        required_failures = [
            row
            for row in rows
            if row.required and row.state is not CapabilityState.READY
        ]
        optional_failures = [
            row
            for row in rows
            if not row.required
            and row.capability_id not in route_members
            and row.state is not CapabilityState.READY
        ]
        route_failures = [
            rows_by_id[capability_id]
            for capability_id in route_members
            if capability_id in rows_by_id
            and rows_by_id[capability_id].state is not CapabilityState.READY
        ]
        decisive_failures = required_failures + (
            route_failures if not route_ready else []
        )
        if decisive_failures:
            if any(row.state is CapabilityState.DRIFT for row in decisive_failures):
                state = CapabilityState.DRIFT
            elif any(row.state is CapabilityState.FAILED for row in decisive_failures):
                state = CapabilityState.FAILED
            else:
                state = CapabilityState.UNAVAILABLE
        elif optional_failures:
            state = CapabilityState.DEGRADED
        else:
            state = CapabilityState.READY
        if environment.get("state") in {"DRIFT", "FAILED"}:
            state = CapabilityState.DRIFT
        return SimTierReceipt(
            "constraintbox.sim-tier-receipt.v2",
            tier_id,
            tier["name"],
            mode,
            state,
            _sha(self.manifest_path),
            _sha(self.fixture_path),
            controller_sha,
            str(self.python),
            self._python_version(),
            environment,
            time.monotonic() - started,
            rows,
        )

    def run_layer(self, layer_id: str, mode: str = "boot") -> SimTierReceipt:
        """Backward-compatible alias for the v0.2 package."""
        return self.run_tier(layer_id, mode)
