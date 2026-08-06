from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from constraintbox.contracts import Disposition
from constraintbox.formalcheck import (
    FormalCheckStatus,
    ProcessResult,
    TemporalCheckProfile,
    _parse_apalache_output,
    _parse_tlc_output,
    _run_process,
    run_temporal_check,
)


INVARIANTS = (
    "BasicStateDomains",
    "NoDispositionAtProposal",
    "NonemptyEvidenceBeforeEligible",
    "CapturedGenerationMatchesDuringRun",
)
MODEL = """\
----------------------------- MODULE ConstraintBox -----------------------------
EXTENDS Naturals
CONSTANT MaxGeneration
VARIABLES state, policyGeneration, runPolicyGeneration, evidence, disposition
Observe ==
  /\\ state = "RUNNING"
  /\\ state' = "OBSERVED"
  /\\ evidence' = {"worker_witness"}
  /\\ UNCHANGED <<policyGeneration, runPolicyGeneration, disposition>>
=============================================================================
"""
CONFIG = """\
SPECIFICATION Spec
INVARIANT BasicStateDomains
INVARIANT NoDispositionAtProposal
INVARIANT NonemptyEvidenceBeforeEligible
INVARIANT CapturedGenerationMatchesDuringRun
CONSTANT MaxGeneration = 2
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def process(
    stdout: str = "",
    *,
    returncode: int | None = 0,
    stderr: str = "",
    timed_out: bool = False,
    output_overflow: bool = False,
) -> ProcessResult:
    return ProcessResult(
        returncode,
        stdout.encode(),
        stderr.encode(),
        0.01,
        timed_out,
        output_overflow,
    )


def java_version() -> ProcessResult:
    return process(stderr='openjdk version "21.0.8" 2025-07-15\n')


def tlc_pass(*, seed: int, pid: int, finished: str) -> str:
    return f"""\
TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)
Running breadth-first search Model-Checking with fp 39 and seed {seed} with 1 worker [pid: {pid}].
Parsing file /private/tmp/noisy-{pid}/ConstraintBox.tla
Model checking completed. No error has been found.
73 states generated, 45 distinct states found, 0 states left on queue.
The depth of the complete state graph search is 10.
Finished in 00s at ({finished})
"""


def tlc_mutation() -> str:
    return """\
TLC2 Version 2.19 of 08 August 2024 (rev: 5a47802)
Error: Invariant NonemptyEvidenceBeforeEligible is violated.
23 states generated, 19 distinct states found, 2 states left on queue.
The depth of the complete state graph search is 8.
"""


def apalache_typecheck(*, ok: bool = True) -> str:
    if ok:
        return """\
# APALACHE version: 0.58.3 | build: f4ac7ff
PASS #1: TypeCheckerSnowcat
 > Your types are purrfect!
 > All expressions are typed
Type checker [OK]
EXITCODE: OK
"""
    return """\
# APALACHE version: 0.58.3 | build: f4ac7ff
Typing input error: Expected a type annotation for VARIABLE state
Type checker [ERROR]
EXITCODE: ERROR
"""


def apalache_pass(*, noise: str) -> str:
    return f"""\
# APALACHE version: 0.58.3 | build: f4ac7ff
Output directory: /tmp/{noise}/ConstraintBox.tla/timestamp
The outcome is: NoError
Checker reports no error up to computation length 10
Total time: {noise} sec
EXITCODE: OK
"""


def apalache_mutation() -> str:
    return """\
# APALACHE version: 0.58.3 | build: f4ac7ff
State 7: state invariant 0 violated.
Found 1 error(s)
The outcome is: Error
Checker has found an error
EXITCODE: ERROR (12)
"""


class FormalCheckFixture:
    def __init__(self, root: Path, backend: str):
        self.root = root
        self.backend = backend
        self.profile_dir = root / "profile"
        self.profile_dir.mkdir()
        self.model = self.profile_dir / "ConstraintBox.tla"
        self.config = self.profile_dir / "ConstraintBox.cfg"
        self.model.write_text(MODEL, encoding="utf-8")
        self.config.write_text(CONFIG, encoding="utf-8")
        self.java = root / "java"
        self.java.write_bytes(b"fake-java")
        self.java.chmod(0o755)
        self.artifact = root / f"{backend}.jar"
        manifest = (
            "Manifest-Version: 1.0\r\n"
            + (
                "Implementation-Title: TLA+ Tools\r\n"
                "Implementation-Version: 2.0 2024-08-08\r\n"
                "X-Git-Tag: v1.7.4\r\n"
                "X-Git-Revision: 5a47802\r\n"
                if backend == "tlc"
                else "Specification-Title: apalache\r\n"
                "Specification-Version: 0.58.3\r\n"
                "Implementation-Version: 0.58.3\r\n"
            )
            + "\r\n"
        )
        with zipfile.ZipFile(self.artifact, "w") as archive:
            archive.writestr("META-INF/MANIFEST.MF", manifest)
        artifact_sha = sha256(self.artifact)
        expectations = {
            "schema": "constraintbox.formalcheck.expectations.v1",
            "profile_id": "controller_lifecycle_v1",
            "model_file": self.model.name,
            "config_file": self.config.name,
            "model_sha256": sha256(self.model),
            "config_sha256": sha256(self.config),
            "invariants": list(INVARIANTS),
            "bounds": {
                "max_generation": 2,
                "apalache_computation_length": 10,
            },
            "mutation": {
                "name": "observe_without_worker_evidence",
                "target": '  /\\ evidence\' = {"worker_witness"}',
                "replacement": "  /\\ evidence' = {}",
                "expected_invariant": "NonemptyEvidenceBeforeEligible",
            },
            "backends": {
                "tlc": {
                    "artifact_sha256": artifact_sha,
                    "expected_version": "2.19",
                    "expected_release": "v1.7.4",
                    "expected_java_version": "21.0.8",
                    "expected_generated_states": 73,
                    "expected_distinct_states": 45,
                    "expected_queue_states": 0,
                    "expected_depth": 10,
                },
                "apalache": {
                    "artifact_sha256": artifact_sha,
                    "expected_version": "0.58.3",
                    "expected_java_version": "21.0.8",
                    "check_length": 10,
                },
            },
            "claim_ceiling": (
                "bounded safety checking of one abstract completed "
                "controller-run state-token lifecycle skeleton; no "
                "implementation correspondence, decision correctness, "
                "retry, lease, release, liveness, concurrency, or "
                "refinement claim"
            ),
            "blocked_consumers": [
                "implementation_correspondence_claims",
                "retry_safety_claims",
                "lease_safety_claims",
                "release_correctness_claims",
                "external_sim_estate_admission",
            ],
        }
        self.expectations = self.profile_dir / "expectations.json"
        self.expectations.write_text(
            json.dumps(expectations, sort_keys=True), encoding="utf-8"
        )
        self.profile = TemporalCheckProfile(
            backend=backend,
            java_executable=self.java,
            checker_artifact=self.artifact,
            profile_dir=self.profile_dir,
            expected_expectations_sha256=sha256(self.expectations),
            timeout_seconds=5,
        )

    def repin(self) -> TemporalCheckProfile:
        return TemporalCheckProfile(
            backend=self.backend,
            java_executable=self.java,
            checker_artifact=self.artifact,
            profile_dir=self.profile_dir,
            expected_expectations_sha256=sha256(self.expectations),
            timeout_seconds=5,
        )

    def read_expectations(self) -> dict[str, object]:
        return json.loads(self.expectations.read_text(encoding="utf-8"))

    def write_expectations(self, value: dict[str, object]) -> None:
        self.expectations.write_text(
            json.dumps(value, sort_keys=True), encoding="utf-8"
        )

    def repin_config(self, text: str) -> TemporalCheckProfile:
        self.config.write_text(text, encoding="utf-8")
        expectations = self.read_expectations()
        expectations["config_sha256"] = sha256(self.config)
        self.write_expectations(expectations)
        return self.repin()


class FormalCheckTests(unittest.TestCase):
    def test_missing_checker_artifact_is_unavailable_and_parked(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            fixture.artifact.unlink()
            receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.UNAVAILABLE)
        self.assertEqual(receipt.disposition, Disposition.PARKED)
        self.assertEqual(receipt.reason, "checker_artifact_absent")
        self.assertFalse(receipt.promotion_allowed)

    def test_dead_java_is_unavailable_not_a_checker_failure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            with patch(
                "constraintbox.formalcheck._run_process",
                return_value=process(returncode=1, stderr="dead java"),
            ):
                receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.UNAVAILABLE)
        self.assertEqual(receipt.disposition, Disposition.PARKED)
        self.assertEqual(receipt.reason, "java_executable_unusable")

    def test_artifact_digest_drift_blocks_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            fixture.artifact.write_bytes(fixture.artifact.read_bytes() + b"drift")
            with patch("constraintbox.formalcheck._run_process") as invoked:
                receipt = run_temporal_check(fixture.profile)

        invoked.assert_not_called()
        self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
        self.assertEqual(receipt.disposition, Disposition.BLOCKED)
        self.assertEqual(receipt.reason, "formal_profile_drift")

    def test_tlc_parser_extracts_only_semantic_replay_fields(self) -> None:
        left = _parse_tlc_output(
            tlc_pass(seed=1, pid=10, finished="first"), INVARIANTS
        )
        right = _parse_tlc_output(
            tlc_pass(seed=999, pid=77, finished="second"), INVARIANTS
        )
        mutant = _parse_tlc_output(tlc_mutation(), INVARIANTS)

        self.assertEqual(left.semantic_key(), right.semantic_key())
        self.assertEqual(left.status, "PASS")
        self.assertEqual(left.version, "2.19")
        self.assertEqual(left.generated_states, 73)
        self.assertEqual(left.distinct_states, 45)
        self.assertEqual(left.depth, 10)
        self.assertEqual(
            mutant.invariant_results["NonemptyEvidenceBeforeEligible"], "FAIL"
        )

    def test_tlc_replay_tolerates_seed_pid_timestamp_and_path_noise(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            mutation_seen: list[bool] = []

            def fake_run(command, *, cwd, timeout_seconds):
                del timeout_seconds
                if command[-1] == "-version":
                    return java_version()
                if cwd.name == "mutation":
                    mutated = (cwd / "ConstraintBox.tla").read_text(
                        encoding="utf-8"
                    )
                    mutation_seen.append(
                        "evidence' = {}" in mutated
                        and '{"worker_witness"}' not in mutated
                    )
                    return process(tlc_mutation(), returncode=12)
                if cwd.name == "positive":
                    return process(
                        tlc_pass(seed=1, pid=10, finished="first")
                    )
                if cwd.name == "replay":
                    return process(
                        tlc_pass(seed=999, pid=77, finished="second")
                    )
                raise AssertionError(f"unexpected cwd: {cwd}")

            with patch(
                "constraintbox.formalcheck._run_process", side_effect=fake_run
            ):
                receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.PASSED)
        self.assertEqual(receipt.disposition, Disposition.ELIGIBLE)
        self.assertTrue(receipt.controls["positive"])
        self.assertTrue(receipt.controls["behavior_mutation"])
        self.assertTrue(receipt.controls["semantic_replay"])
        self.assertEqual(mutation_seen, [True])
        self.assertIn("no implementation correspondence", receipt.claim_ceiling)
        self.assertIn("retry", receipt.claim_ceiling)

    def test_checker_executes_only_a_verified_private_artifact_copy(self) -> None:
        for backend in ("tlc", "apalache"):
            with self.subTest(backend=backend):
                with tempfile.TemporaryDirectory() as raw:
                    fixture = FormalCheckFixture(Path(raw), backend)
                    executed_artifacts: list[Path] = []

                    def fake_run(command, *, cwd, timeout_seconds):
                        del timeout_seconds
                        if command[-1] == "-version":
                            return java_version()
                        artifact = Path(command[command.index("-jar") + 1])
                        self.assertNotEqual(artifact, fixture.artifact)
                        self.assertTrue(artifact.is_file())
                        self.assertEqual(sha256(artifact), sha256(fixture.artifact))
                        executed_artifacts.append(artifact)
                        if backend == "tlc":
                            if cwd.name == "mutation":
                                return process(tlc_mutation(), returncode=12)
                            return process(
                                tlc_pass(
                                    seed=1 if cwd.name == "positive" else 2,
                                    pid=1,
                                    finished=cwd.name,
                                )
                            )
                        if "typecheck" in command:
                            return process(apalache_typecheck())
                        if cwd.name == "mutation":
                            return process(apalache_mutation(), returncode=1)
                        return process(apalache_pass(noise=cwd.name))

                    with patch(
                        "constraintbox.formalcheck._run_process",
                        side_effect=fake_run,
                    ):
                        receipt = run_temporal_check(fixture.profile)

                self.assertEqual(receipt.status, FormalCheckStatus.PASSED)
                self.assertTrue(receipt.controls["artifact_copy_hash"])
                self.assertEqual(len({str(path) for path in executed_artifacts}), 1)
                self.assertEqual(
                    len(executed_artifacts), 3 if backend == "tlc" else 4
                )

    def test_source_artifact_change_cannot_change_executed_bytes(self) -> None:
        for backend in ("tlc", "apalache"):
            with self.subTest(backend=backend):
                with tempfile.TemporaryDirectory() as raw:
                    fixture = FormalCheckFixture(Path(raw), backend)
                    original_sha = sha256(fixture.artifact)
                    executed_hashes: list[str] = []

                    def fake_run(command, *, cwd, timeout_seconds):
                        del timeout_seconds
                        if command[-1] == "-version":
                            return java_version()
                        copied_artifact = Path(
                            command[command.index("-jar") + 1]
                        )
                        executed_hashes.append(sha256(copied_artifact))
                        if len(executed_hashes) == 1:
                            fixture.artifact.write_bytes(
                                fixture.artifact.read_bytes() + b"source-drift"
                            )
                        if backend == "tlc":
                            if cwd.name == "mutation":
                                return process(tlc_mutation(), returncode=12)
                            return process(
                                tlc_pass(
                                    seed=1 if cwd.name == "positive" else 2,
                                    pid=1,
                                    finished=cwd.name,
                                )
                            )
                        if "typecheck" in command:
                            return process(apalache_typecheck())
                        if cwd.name == "mutation":
                            return process(apalache_mutation(), returncode=1)
                        return process(apalache_pass(noise=cwd.name))

                    with patch(
                        "constraintbox.formalcheck._run_process",
                        side_effect=fake_run,
                    ):
                        receipt = run_temporal_check(fixture.profile)

                self.assertTrue(executed_hashes)
                self.assertEqual(set(executed_hashes), {original_sha})
                self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
                self.assertEqual(
                    receipt.reason, "formal_inputs_changed_during_run"
                )
                self.assertTrue(receipt.controls["artifact_copy_hash"])
                self.assertFalse(receipt.controls["post_run_hashes"])

    def test_model_mutant_uses_the_admitted_byte_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            snapshots: dict[str, bytes] = {}

            def fake_run(command, *, cwd, timeout_seconds):
                del timeout_seconds
                if command[-1] == "-version":
                    fixture.model.write_text(
                        MODEL + "\\* source drift after admission\n",
                        encoding="utf-8",
                    )
                    return java_version()
                snapshots[cwd.name] = (cwd / "ConstraintBox.tla").read_bytes()
                if cwd.name == "mutation":
                    return process(tlc_mutation(), returncode=12)
                return process(
                    tlc_pass(
                        seed=1 if cwd.name == "positive" else 2,
                        pid=1,
                        finished=cwd.name,
                    )
                )

            with patch(
                "constraintbox.formalcheck._run_process", side_effect=fake_run
            ):
                receipt = run_temporal_check(fixture.profile)

        admitted = MODEL.encode()
        expected_mutant = admitted.replace(
            b'  /\\ evidence\' = {"worker_witness"}',
            b"  /\\ evidence' = {}",
            1,
        )
        self.assertEqual(snapshots["positive"], admitted)
        self.assertEqual(snapshots["replay"], admitted)
        self.assertEqual(snapshots["mutation"], expected_mutant)
        self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
        self.assertEqual(receipt.reason, "formal_inputs_changed_during_run")

    def test_expectations_are_parsed_from_the_admitted_byte_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")

            def fake_run(command, *, cwd, timeout_seconds):
                del timeout_seconds
                if command[-1] == "-version":
                    fixture.expectations.write_bytes(b"not-json-after-admission")
                    return java_version()
                if cwd.name == "mutation":
                    return process(tlc_mutation(), returncode=12)
                return process(
                    tlc_pass(
                        seed=1 if cwd.name == "positive" else 2,
                        pid=1,
                        finished=cwd.name,
                    )
                )

            with patch(
                "constraintbox.formalcheck._run_process", side_effect=fake_run
            ):
                receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
        self.assertEqual(receipt.reason, "formal_inputs_changed_during_run")
        self.assertTrue(receipt.controls["positive"])
        self.assertTrue(receipt.controls["behavior_mutation"])
        self.assertTrue(receipt.controls["semantic_replay"])

    def test_tlc_behavior_mutant_must_be_detected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            results = [
                java_version(),
                process(tlc_pass(seed=1, pid=1, finished="first")),
                process(tlc_pass(seed=2, pid=2, finished="mutant")),
            ]
            with patch(
                "constraintbox.formalcheck._run_process", side_effect=results
            ):
                receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.FAILED)
        self.assertEqual(receipt.disposition, Disposition.BLOCKED)
        self.assertEqual(receipt.reason, "behavior_mutation_not_detected")
        self.assertFalse(receipt.controls["behavior_mutation"])

    def test_model_source_mutation_is_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            fixture.model.write_text(MODEL + "\\* drift\n", encoding="utf-8")
            with patch("constraintbox.formalcheck._run_process") as invoked:
                receipt = run_temporal_check(fixture.profile)

        invoked.assert_not_called()
        self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
        self.assertEqual(receipt.reason, "formal_profile_drift")

    def test_config_max_generation_is_exactly_bound_before_execution(self) -> None:
        malformed_configs = {
            "missing": CONFIG.replace("CONSTANT MaxGeneration = 2\n", ""),
            "duplicate": CONFIG + "CONSTANT MaxGeneration = 2\n",
            "noninteger": CONFIG.replace(
                "CONSTANT MaxGeneration = 2",
                "CONSTANT MaxGeneration = two",
            ),
        }
        for backend in ("tlc", "apalache"):
            with self.subTest(backend=backend, case="mismatch"):
                with tempfile.TemporaryDirectory() as raw:
                    fixture = FormalCheckFixture(Path(raw), backend)
                    expectations = fixture.read_expectations()
                    expectations["bounds"]["max_generation"] = 1
                    fixture.write_expectations(expectations)
                    with patch(
                        "constraintbox.formalcheck._run_process"
                    ) as invoked:
                        receipt = run_temporal_check(fixture.repin())
                invoked.assert_not_called()
                self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
                self.assertEqual(receipt.disposition, Disposition.BLOCKED)
                self.assertEqual(receipt.reason, "formal_profile_drift")

            for case, config_text in malformed_configs.items():
                with self.subTest(backend=backend, case=case):
                    with tempfile.TemporaryDirectory() as raw:
                        fixture = FormalCheckFixture(Path(raw), backend)
                        profile = fixture.repin_config(config_text)
                        with patch(
                            "constraintbox.formalcheck._run_process"
                        ) as invoked:
                            receipt = run_temporal_check(profile)
                    invoked.assert_not_called()
                    self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
                    self.assertEqual(receipt.disposition, Disposition.BLOCKED)
                    self.assertEqual(receipt.reason, "formal_profile_drift")

    def test_sandbox_socket_denial_is_unavailable(self) -> None:
        denial = process(
            returncode=1,
            stderr=(
                "java.rmi.server.ExportException: Listen failed on port: 0; "
                "nested exception is: java.net.SocketException: "
                "Operation not permitted"
            ),
        )
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            with patch(
                "constraintbox.formalcheck._run_process",
                side_effect=[java_version(), denial],
            ):
                receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.UNAVAILABLE)
        self.assertEqual(receipt.reason, "sandbox_socket_denied")
        self.assertEqual(receipt.disposition, Disposition.PARKED)

    def test_no_banner_execution_failures_are_failed_not_drift(self) -> None:
        scenarios = (
            ("tlc", [java_version(), process(returncode=1)], "positive_model_check_failed"),
            (
                "apalache",
                [java_version(), process(returncode=1)],
                "apalache_typecheck_failed",
            ),
        )
        for backend, results, expected_reason in scenarios:
            with self.subTest(backend=backend):
                with tempfile.TemporaryDirectory() as raw:
                    fixture = FormalCheckFixture(Path(raw), backend)
                    with patch(
                        "constraintbox.formalcheck._run_process",
                        side_effect=results,
                    ):
                        receipt = run_temporal_check(fixture.profile)
                self.assertEqual(receipt.status, FormalCheckStatus.FAILED)
                self.assertEqual(receipt.disposition, Disposition.BLOCKED)
                self.assertEqual(receipt.reason, expected_reason)

    def test_no_banner_timeouts_are_failed_at_every_checker_stage(self) -> None:
        timeout = process(returncode=None, timed_out=True)
        scenarios = (
            (
                "java",
                "tlc",
                [timeout],
                "java_validation_timed_out",
            ),
            (
                "tlc_positive",
                "tlc",
                [java_version(), timeout],
                "positive_check_timed_out",
            ),
            (
                "tlc_mutation",
                "tlc",
                [
                    java_version(),
                    process(tlc_pass(seed=1, pid=1, finished="positive")),
                    timeout,
                ],
                "behavior_mutation_timed_out",
            ),
            (
                "tlc_replay",
                "tlc",
                [
                    java_version(),
                    process(tlc_pass(seed=1, pid=1, finished="positive")),
                    process(tlc_mutation(), returncode=12),
                    timeout,
                ],
                "semantic_replay_timed_out",
            ),
            (
                "apalache_typecheck",
                "apalache",
                [java_version(), timeout],
                "apalache_typecheck_timed_out",
            ),
            (
                "apalache_positive",
                "apalache",
                [java_version(), process(apalache_typecheck()), timeout],
                "positive_check_timed_out",
            ),
            (
                "apalache_mutation",
                "apalache",
                [
                    java_version(),
                    process(apalache_typecheck()),
                    process(apalache_pass(noise="positive")),
                    timeout,
                ],
                "behavior_mutation_timed_out",
            ),
            (
                "apalache_replay",
                "apalache",
                [
                    java_version(),
                    process(apalache_typecheck()),
                    process(apalache_pass(noise="positive")),
                    process(apalache_mutation(), returncode=12),
                    timeout,
                ],
                "semantic_replay_timed_out",
            ),
        )
        for name, backend, results, expected_reason in scenarios:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as raw:
                    fixture = FormalCheckFixture(Path(raw), backend)
                    with patch(
                        "constraintbox.formalcheck._run_process",
                        side_effect=results,
                    ):
                        receipt = run_temporal_check(fixture.profile)
                self.assertEqual(receipt.status, FormalCheckStatus.FAILED)
                self.assertEqual(receipt.disposition, Disposition.BLOCKED)
                self.assertEqual(receipt.reason, expected_reason)

    def test_output_overflow_is_failed_at_java_and_checker_stages(self) -> None:
        overflow = process(returncode=None, output_overflow=True)
        scenarios = (
            (
                "java",
                "tlc",
                [overflow],
                "java_validation_output_overflow",
            ),
            (
                "tlc_positive",
                "tlc",
                [java_version(), overflow],
                "positive_check_output_overflow",
            ),
            (
                "tlc_mutation",
                "tlc",
                [
                    java_version(),
                    process(tlc_pass(seed=1, pid=1, finished="positive")),
                    overflow,
                ],
                "behavior_mutation_output_overflow",
            ),
            (
                "tlc_replay",
                "tlc",
                [
                    java_version(),
                    process(tlc_pass(seed=1, pid=1, finished="positive")),
                    process(tlc_mutation(), returncode=12),
                    overflow,
                ],
                "semantic_replay_output_overflow",
            ),
            (
                "apalache_typecheck",
                "apalache",
                [java_version(), overflow],
                "apalache_typecheck_output_overflow",
            ),
            (
                "apalache_positive",
                "apalache",
                [java_version(), process(apalache_typecheck()), overflow],
                "positive_check_output_overflow",
            ),
            (
                "apalache_mutation",
                "apalache",
                [
                    java_version(),
                    process(apalache_typecheck()),
                    process(apalache_pass(noise="positive")),
                    overflow,
                ],
                "behavior_mutation_output_overflow",
            ),
            (
                "apalache_replay",
                "apalache",
                [
                    java_version(),
                    process(apalache_typecheck()),
                    process(apalache_pass(noise="positive")),
                    process(apalache_mutation(), returncode=12),
                    overflow,
                ],
                "semantic_replay_output_overflow",
            ),
        )
        for name, backend, results, expected_reason in scenarios:
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory() as raw:
                    fixture = FormalCheckFixture(Path(raw), backend)
                    with patch(
                        "constraintbox.formalcheck._run_process",
                        side_effect=results,
                    ):
                        receipt = run_temporal_check(fixture.profile)
                self.assertEqual(receipt.status, FormalCheckStatus.FAILED)
                self.assertEqual(receipt.disposition, Disposition.BLOCKED)
                self.assertEqual(receipt.reason, expected_reason)

    def test_process_output_is_capped_during_execution(self) -> None:
        for stream_name in ("stdout", "stderr"):
            with self.subTest(stream=stream_name):
                script = (
                    "import sys; "
                    f"sys.{stream_name}.buffer.write(b'x' * 65536); "
                    f"sys.{stream_name}.flush()"
                )
                with tempfile.TemporaryDirectory() as raw:
                    started = time.monotonic()
                    result = _run_process(
                        (sys.executable, "-c", script),
                        cwd=Path(raw),
                        timeout_seconds=2,
                        stdout_limit=128,
                        stderr_limit=128,
                    )
                    elapsed = time.monotonic() - started

                self.assertTrue(result.output_overflow)
                self.assertFalse(result.timed_out)
                self.assertLess(elapsed, 2)
                observed = (
                    result.stdout if stream_name == "stdout" else result.stderr
                )
                self.assertEqual(len(observed), 128)

    def test_process_timeout_kills_the_process_group(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            started = time.monotonic()
            result = _run_process(
                (sys.executable, "-c", "import time; time.sleep(5)"),
                cwd=Path(raw),
                timeout_seconds=0.1,
                stdout_limit=128,
                stderr_limit=128,
            )
            elapsed = time.monotonic() - started

        self.assertTrue(result.timed_out)
        self.assertFalse(result.output_overflow)
        self.assertLess(elapsed, 2)

    def test_inconsistent_declared_bounds_are_drift_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "apalache")
            expectations = fixture.read_expectations()
            expectations["bounds"]["apalache_computation_length"] = 1
            fixture.write_expectations(expectations)
            profile = fixture.repin()
            with patch("constraintbox.formalcheck._run_process") as invoked:
                receipt = run_temporal_check(profile)

        invoked.assert_not_called()
        self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
        self.assertEqual(receipt.disposition, Disposition.BLOCKED)
        self.assertEqual(receipt.reason, "formal_profile_drift")

    def test_tlc_depth_is_labeled_as_a_result_signature_not_a_bound(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            expectations = fixture.read_expectations()
            expectations["backends"]["tlc"]["expected_depth"] = 9
            fixture.write_expectations(expectations)
            with patch(
                "constraintbox.formalcheck._run_process",
                side_effect=[
                    java_version(),
                    process(tlc_pass(seed=1, pid=1, finished="positive")),
                ],
            ) as invoked:
                receipt = run_temporal_check(fixture.repin())

        self.assertEqual(invoked.call_count, 2)
        self.assertEqual(receipt.status, FormalCheckStatus.DRIFT)
        self.assertEqual(receipt.reason, "positive_semantic_output_drift")
        self.assertNotIn("complete_state_graph_depth", receipt.evidence["bounds"])
        self.assertEqual(
            receipt.evidence["expected_tlc_result_signature"][
                "derived_complete_state_graph_depth"
            ],
            9,
        )

    def test_apalache_parser_and_typed_failure(self) -> None:
        parsed = _parse_apalache_output(
            apalache_pass(noise="one"), INVARIANTS
        )
        self.assertEqual(parsed.status, "PASS")
        self.assertEqual(parsed.version, "0.58.3")
        self.assertEqual(parsed.computation_length, 10)

        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "apalache")
            with patch(
                "constraintbox.formalcheck._run_process",
                side_effect=[
                    java_version(),
                    process(apalache_typecheck(ok=False), returncode=1),
                ],
            ):
                receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.FAILED)
        self.assertEqual(receipt.disposition, Disposition.BLOCKED)
        self.assertEqual(receipt.reason, "apalache_typecheck_failed")
        self.assertFalse(receipt.controls["typecheck"])

    def test_apalache_missing_artifact_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "apalache")
            fixture.artifact.unlink()
            receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.UNAVAILABLE)
        self.assertEqual(receipt.disposition, Disposition.PARKED)
        self.assertEqual(receipt.reason, "checker_artifact_absent")

    def test_apalache_positive_mutant_and_semantic_replay(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "apalache")
            results = [
                java_version(),
                process(apalache_typecheck()),
                process(apalache_pass(noise="first")),
                process(apalache_mutation(), returncode=1),
                process(apalache_pass(noise="second")),
            ]
            with patch(
                "constraintbox.formalcheck._run_process", side_effect=results
            ):
                receipt = run_temporal_check(fixture.profile)

        self.assertEqual(receipt.status, FormalCheckStatus.PASSED)
        self.assertTrue(receipt.controls["typecheck"])
        self.assertTrue(receipt.controls["positive"])
        self.assertTrue(receipt.controls["behavior_mutation"])
        self.assertTrue(receipt.controls["semantic_replay"])

    def test_checker_removal_changes_pass_to_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            fixture = FormalCheckFixture(Path(raw), "tlc")
            results = [
                java_version(),
                process(tlc_pass(seed=1, pid=1, finished="first")),
                process(tlc_mutation(), returncode=12),
                process(tlc_pass(seed=2, pid=2, finished="second")),
            ]
            with patch(
                "constraintbox.formalcheck._run_process", side_effect=results
            ):
                before = run_temporal_check(fixture.profile)
            fixture.artifact.unlink()
            after = run_temporal_check(fixture.profile)

        self.assertEqual(before.status, FormalCheckStatus.PASSED)
        self.assertEqual(after.status, FormalCheckStatus.UNAVAILABLE)
        self.assertEqual(after.reason, "checker_artifact_absent")


if __name__ == "__main__":
    unittest.main()
