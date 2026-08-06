from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from constraintbox.external_engine_packet import (
    CASE_KEYS,
    EXACT_APIS,
    EXTERNAL_BOUNDARY,
    FIXTURE_SHA256,
    WORKER_SHA256,
    ExternalEnginePacketBroker,
    build_identified_rate_artifact,
    evaluate_worker_output,
    validate_handoff_artifact,
    validate_pass_receipt,
    validate_fixture,
)
from constraintbox.external_runtime_profiles import runtime_profile_dict
from constraintbox.intake import canonical_json, parse_json_object


REPO_ROOT = Path(__file__).resolve().parents[2]
EXTERNAL_ROOT = REPO_ROOT / "external_sim_estate" / "basic_packet_v1"
FIXTURE = EXTERNAL_ROOT / "fixtures" / "exact_operations_v1.json"
PYTHON_WORKER = EXTERNAL_ROOT / "workers" / "python_engine_worker.py"
JULIA_WORKER = EXTERNAL_ROOT / "workers" / "julia_diffeq_worker.jl"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ExternalEnginePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = parse_json_object(FIXTURE.read_bytes())
        cls.broker = ExternalEnginePacketBroker(
            timeout_seconds=240.0,
        )
        cls.receipt = cls.broker.run()

    def test_fixture_and_worker_sources_are_pinned_outside_cb(self) -> None:
        validate_fixture(self.fixture)
        self.assertEqual(digest(FIXTURE), FIXTURE_SHA256)
        self.assertEqual(digest(PYTHON_WORKER), WORKER_SHA256["python"])
        self.assertEqual(digest(JULIA_WORKER), WORKER_SHA256["julia"])
        for path in (FIXTURE, PYTHON_WORKER, JULIA_WORKER):
            self.assertIn("external_sim_estate/basic_packet_v1", str(path))
            self.assertNotIn("/constraint_box/", str(path))

    def test_runtime_profiles_are_portable_controller_owned_contracts(self) -> None:
        expected = {
            "python": ("external-cpython-3.11-3.13-v1", "controller_process"),
            "julia": ("external-julia-1.12-v1", "operator_path_lookup"),
        }
        for family, (profile_id, selection) in expected.items():
            profile = runtime_profile_dict(family)
            self.assertEqual(profile["profile_id"], profile_id)
            self.assertEqual(profile["executable_selection"], selection)
            self.assertFalse(profile["artifact_sha256_is_policy_input"])
            self.assertNotIn("/Users/", repr(profile))
            self.assertNotIn("/opt/homebrew/", repr(profile))

    def test_actual_packet_runs_or_explicitly_parks_unavailable_api(self) -> None:
        self.assertEqual(self.receipt["status"], "PASS")
        self.assertEqual(len(self.receipt["rows"]), 4)
        self.assertEqual(
            {row["engine_id"] for row in self.receipt["rows"]},
            set(EXACT_APIS),
        )
        for row in self.receipt["rows"]:
            self.assertIn(row["status"], {"PASS", "PARKED"})
            self.assertTrue(row["external_system"])
            self.assertEqual(row["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
            self.assertFalse(row["engine_readiness_claim"])
            self.assertFalse(row["promotion_allowed"])
            self.assertEqual(row["claim_ceiling"], EXTERNAL_BOUNDARY)
            family = "julia" if row["engine_id"] == "julia_diffeq" else "python"
            self.assertEqual(row["runtime_pin"], runtime_profile_dict(family))
            self.assertFalse(row["executable_sha256_is_policy_input"])
            if row["status"] == "PASS":
                self.assertTrue(all(row["controls"].values()))
                self.assertEqual(row["reason"], "exact_operation_controls_passed")
            else:
                self.assertIn(
                    row["reason"],
                    {
                        "runtime_executable_unavailable",
                        "strict_julia_carrier_unavailable",
                        "exact_function_unavailable",
                    },
                )

    def test_python_launch_is_isolated_and_scrubs_inherited_python_paths(
        self,
    ) -> None:
        fixture, _canonical, fixture_sha256 = self.broker._load_fixture()
        captured: dict[str, object] = {}

        def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
            captured["command"] = command
            captured["environment"] = kwargs["env"]
            witness = {
                "schema": "constraintbox.external-engine-unavailable.v1",
                "engine_id": "jax_autodiff",
                "exact_api": EXACT_APIS["jax_autodiff"],
                "reason": "test unavailable",
                "pid": os.getpid() + 1000,
            }
            return subprocess.CompletedProcess(
                command,
                3,
                stdout=canonical_json(witness) + b"\n",
                stderr=b"",
            )

        with mock.patch(
            "constraintbox.external_engine_packet.subprocess.run",
            side_effect=fake_run,
        ):
            row = self.broker._run_row(
                "jax_autodiff", fixture, fixture_sha256
            )
        self.assertEqual(row["status"], "PARKED")
        command = captured["command"]
        self.assertIsInstance(command, list)
        self.assertEqual(command[0], str(self.broker.python_executable))
        self.assertEqual(command[1], "-I")
        environment = captured["environment"]
        self.assertIsInstance(environment, dict)
        self.assertNotIn("PYTHONPATH", environment)
        self.assertNotIn("PYTHONHOME", environment)

    def test_injected_alternate_runtime_never_passes(self) -> None:
        missing = Path("/private/tmp/constraintbox-no-such-julia-runtime")
        alternate = Path("/usr/bin/python3")
        self.assertTrue(alternate.is_file())
        broker = ExternalEnginePacketBroker(
            python_executable=alternate,
            julia_executable=missing,
            timeout_seconds=1.0,
        )
        receipt = broker.run()
        self.assertEqual(receipt["status"], "FAIL")
        python_rows = [
            row
            for row in receipt["rows"]
            if row["engine_id"] != "julia_diffeq"
        ]
        self.assertTrue(python_rows)
        for row in python_rows:
            self.assertEqual(row["status"], "FAIL")
            self.assertEqual(row["reason"], "runtime_selection_override_rejected")

    def test_pass_rows_bind_process_source_input_and_output_bytes(self) -> None:
        fixture_digest = digest(FIXTURE)
        worker_pids: list[int] = []
        for row in self.receipt["rows"]:
            if row["status"] != "PASS":
                continue
            worker_pids.append(row["worker_pid"])
            self.assertNotEqual(row["worker_pid"], os.getpid())
            self.assertEqual(row["fixture_sha256"], fixture_digest)
            self.assertEqual(
                digest(Path(row["executable_resolved_path"])),
                row["executable_sha256"],
            )
            worker = (
                JULIA_WORKER
                if row["engine_id"] == "julia_diffeq"
                else PYTHON_WORKER
            )
            self.assertEqual(digest(worker), row["worker_source_sha256"])
            transport = {
                "schema": "constraintbox.external-engine-input.v1",
                "engine_id": row["engine_id"],
                "case": self.fixture[CASE_KEYS[row["engine_id"]]],
            }
            self.assertEqual(
                hashlib.sha256(canonical_json(transport)).hexdigest(),
                row["input_sha256"],
            )
            witness = {
                "schema": "constraintbox.external-engine-witness.v1",
                "engine_id": row["engine_id"],
                "exact_api": row["exact_api"],
                "observed": row["observed"],
                "runtime": row["runtime"],
                "pid": row["worker_pid"],
            }
            self.assertEqual(
                hashlib.sha256(canonical_json(witness)).hexdigest(),
                row["output_sha256"],
            )
        self.assertEqual(len(worker_pids), len(set(worker_pids)))

    def test_targeted_wrong_claims_are_rejected_by_controller_math(self) -> None:
        wrong_observations = {
            "jax_autodiff": {
                "derivatives": self.fixture["jax"]["wrong_derivatives"],
                "boundary_derivative": self.fixture["jax"]["linear"],
            },
            "pytorch_jacobian": {
                "jacobian": self.fixture["pytorch"]["wrong_jacobian"],
                "boundary_jacobian": [
                    [0.0, self.fixture["pytorch"]["beta"]],
                    [0.0, 0.0],
                ],
            },
            "pysindy_identification": {
                "coefficient": self.fixture["pysindy"]["wrong_rate"],
                "heldout_derivatives": [
                    self.fixture["pysindy"]["rate"] * value
                    for value in self.fixture["pysindy"]["heldout_states"]
                ],
                "boundary_derivative": 0.0,
            },
            "julia_diffeq": {
                "terminal": self.fixture["julia"]["initial"]
                * math.exp(
                    self.fixture["julia"]["wrong_rate"]
                    * self.fixture["julia"]["duration"]
                ),
                "boundary_terminal": self.fixture["julia"]["boundary_initial"],
            },
        }
        for engine_id, observed in wrong_observations.items():
            runtime: dict[str, object] = {}
            if engine_id == "julia_diffeq":
                runtime = {
                    "active_project": str(
                        self.broker.julia_project / "Project.toml"
                    ),
                    "load_path": ["@", "@stdlib"],
                }
            witness = {
                "schema": "constraintbox.external-engine-witness.v1",
                "engine_id": engine_id,
                "exact_api": EXACT_APIS[engine_id],
                "observed": observed,
                "runtime": runtime,
                "pid": os.getpid() + 1000,
            }
            evaluation = evaluate_worker_output(
                engine_id,
                self.fixture,
                witness,
                julia_project=self.broker.julia_project,
                controller_pid=os.getpid(),
            )
            self.assertFalse(evaluation["controls"]["positive"], engine_id)
            self.assertFalse(
                evaluation["controls"]["targeted_negative"], engine_id
            )

    def test_real_pysindy_artifact_is_consumed_by_julia(self) -> None:
        integration = self.receipt["integration"]
        if self.receipt["status"] == "PARKED":
            self.assertEqual(integration["status"], "PARKED")
            return
        self.assertEqual(integration["status"], "PASS")
        self.assertEqual(
            integration["reason"], "pysindy_artifact_consumed_by_julia"
        )
        self.assertTrue(all(integration["controls"].values()))
        self.assertTrue(integration["external_system"])
        self.assertFalse(integration["engine_readiness_claim"])
        producer = next(
            row
            for row in self.receipt["rows"]
            if row["engine_id"] == "pysindy_identification"
        )
        identified_rate = integration["artifact"]["identified_rate"]
        self.assertEqual(
            integration["artifact"]["producer_output_sha256"],
            producer["output_sha256"],
        )
        self.assertAlmostEqual(
            identified_rate, producer["observed"]["coefficient"], places=12
        )
        expected_terminal = self.fixture["julia"]["initial"] * math.exp(
            identified_rate * self.fixture["julia"]["duration"]
        )
        self.assertAlmostEqual(
            integration["observed"]["terminal"], expected_terminal, places=7
        )
        self.assertAlmostEqual(
            integration["observed"]["consumed_rate"],
            identified_rate,
            places=12,
        )
        artifact_bytes = canonical_json(integration["artifact"])
        self.assertEqual(
            hashlib.sha256(artifact_bytes).hexdigest(),
            integration["artifact_sha256"],
        )
        self.assertEqual(
            integration["observed"]["artifact_sha256"],
            integration["artifact_sha256"],
        )
        self.assertNotEqual(integration["worker_pid"], producer["worker_pid"])
        self.assertEqual(
            digest(Path(integration["executable_resolved_path"])),
            integration["executable_sha256"],
        )
        self.assertEqual(
            digest(JULIA_WORKER), integration["worker_source_sha256"]
        )
        transport = {
            "schema": "constraintbox.external-engine-handoff-input.v1",
            "engine_id": "pysindy_to_julia_rate",
            "artifact_json": artifact_bytes.decode("utf-8"),
            "artifact_sha256": integration["artifact_sha256"],
            "case": {
                "initial": self.fixture["julia"]["initial"],
                "duration": self.fixture["julia"]["duration"],
            },
        }
        self.assertEqual(
            hashlib.sha256(canonical_json(transport)).hexdigest(),
            integration["input_sha256"],
        )
        witness = {
            "schema": "constraintbox.external-engine-integration-witness.v1",
            "integration_id": "pysindy_to_julia_rate",
            "exact_api": integration["exact_api"]["consumer"],
            "observed": integration["observed"],
            "runtime": integration["runtime"],
            "pid": integration["worker_pid"],
        }
        self.assertEqual(
            hashlib.sha256(canonical_json(witness)).hexdigest(),
            integration["output_sha256"],
        )

    def test_handoff_rejects_removal_digest_mutation_and_wrong_rate(self) -> None:
        producer = next(
            row
            for row in self.receipt["rows"]
            if row["engine_id"] == "pysindy_identification"
        )
        if producer["status"] != "PASS":
            self.assertEqual(self.receipt["integration"]["status"], "PARKED")
            return
        artifact_bytes = build_identified_rate_artifact(producer)
        artifact_sha256 = hashlib.sha256(artifact_bytes).hexdigest()
        producer_output_sha256 = producer["output_sha256"]
        accepted = validate_handoff_artifact(
            artifact_bytes,
            expected_sha256=artifact_sha256,
            expected_producer_output_sha256=producer_output_sha256,
        )
        self.assertTrue(accepted["accepted"])

        removed = validate_handoff_artifact(
            None,
            expected_sha256=artifact_sha256,
            expected_producer_output_sha256=producer_output_sha256,
        )
        self.assertEqual(removed, {"accepted": False, "reason": "artifact_missing"})

        mutated = validate_handoff_artifact(
            artifact_bytes + b" ",
            expected_sha256=artifact_sha256,
            expected_producer_output_sha256=producer_output_sha256,
        )
        self.assertFalse(mutated["accepted"])
        self.assertEqual(mutated["reason"], "artifact_digest_mismatch")

        wrong_artifact = parse_json_object(artifact_bytes)
        wrong_artifact["identified_rate"] = -float(
            wrong_artifact["identified_rate"]
        )
        substituted = validate_handoff_artifact(
            canonical_json(wrong_artifact),
            expected_sha256=artifact_sha256,
            expected_producer_output_sha256=producer_output_sha256,
        )
        self.assertFalse(substituted["accepted"])
        self.assertEqual(substituted["reason"], "artifact_digest_mismatch")

    def test_missing_runtimes_park_instead_of_fabricating_rows(self) -> None:
        with mock.patch(
            "constraintbox.external_engine_packet.selected_runtime_executable",
            return_value=None,
        ), mock.patch(
            "constraintbox.external_runtime_profiles.selected_runtime_executable",
            return_value=None,
        ):
            receipt = ExternalEnginePacketBroker(timeout_seconds=1.0).run()
        self.assertEqual(receipt["status"], "PARKED")
        for row in receipt["rows"]:
            self.assertEqual(row["status"], "PARKED")
            self.assertEqual(row["reason"], "runtime_executable_unavailable")
            self.assertNotIn("observed", row)
            self.assertNotIn("output_sha256", row)

    def test_missing_external_estate_parks_instead_of_falling_back_to_host_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            broker = ExternalEnginePacketBroker(repo_root=Path(directory))
            receipt = broker.run()
        self.assertEqual(receipt["status"], "PARKED")
        self.assertEqual(receipt["reason"], "external_fixture_unavailable")
        self.assertEqual(receipt["rows"], [])
        self.assertFalse(receipt["promotion_allowed"])

    def test_minimal_fabricated_pass_receipt_is_rejected(self) -> None:
        errors = validate_pass_receipt(
            {
                "schema": "constraintbox.external-engine-packet-receipt.v1",
                "status": "PASS",
                "rows": [],
                "integration": {"status": "PASS"},
            }
        )
        self.assertTrue(errors)
        self.assertTrue(any("missing_fields" in item for item in errors))

    def test_runtime_digest_substitution_in_receipt_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.receipt)
        tampered["rows"][0]["executable_sha256"] = "0" * 64
        errors = validate_pass_receipt(tampered)
        self.assertTrue(errors)
        self.assertTrue(
            any("rows[0].executable_sha256" in item for item in errors)
        )

    def test_real_pass_packet_revalidates_from_current_sources(self) -> None:
        self.assertEqual(self.receipt["status"], "PASS")
        self.assertEqual(validate_pass_receipt(self.receipt), ())

    def test_receipt_ceiling_forbids_engine_or_cr_claims(self) -> None:
        self.assertTrue(self.receipt["external_system"])
        self.assertEqual(
            self.receipt["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL"
        )
        self.assertFalse(self.receipt["engine_readiness_claim"])
        self.assertFalse(self.receipt["cr_truth_claim"])
        self.assertFalse(self.receipt["promotion_allowed"])
        self.assertEqual(self.receipt["claim_ceiling"], EXTERNAL_BOUNDARY)
        self.assertIn(self.receipt["integration"]["status"], {"PASS", "PARKED"})
        self.assertTrue(self.receipt["integration"]["external_system"])
        self.assertFalse(self.receipt["integration"]["engine_readiness_claim"])
        self.assertFalse(self.receipt["integration"]["cr_truth_claim"])

    def test_fixture_bytes_are_strict_json_but_transport_is_canonical(self) -> None:
        parsed = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(parsed, self.fixture)
        self.assertNotEqual(FIXTURE.read_bytes(), canonical_json(self.fixture))
        self.assertEqual(
            self.receipt["canonical_fixture_sha256"],
            hashlib.sha256(canonical_json(self.fixture)).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
