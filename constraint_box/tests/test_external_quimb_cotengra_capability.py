from __future__ import annotations

import copy
import hashlib
import os
import unittest
from pathlib import Path
from unittest import mock

import constraintbox.external_quimb_cotengra_capability as capability_module
from constraintbox.external_quimb_cotengra_capability import (
    ARTIFACT_PINS,
    CAPABILITY_ID,
    CAPABILITY_SCHEMA,
    CLAIM_CEILING,
    COTENGRA_OPTIMIZER_CONFIG,
    COTENGRA_PROFILE,
    ENVIRONMENT_POLICY,
    ENVIRONMENT_POLICY_SHA256,
    EXACT_APIS,
    PACKAGE_VERSIONS,
    QUIMB_PROFILE,
    RUNTIME_INVOKED_PATH,
    RUNTIME_RESOLVED_PATH,
    RUNTIME_SHA256,
    STEP_ID,
    WORKER_SHA256,
    CapabilityBinding,
    ExternalQuimbCotengraCapabilityError,
    QuimbCotengraCapabilityBroker,
    derive_challenge_cases,
    validate_quimb_cotengra_capability_receipt,
)
from constraintbox.intake import canonical_json


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rebuild_root(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    root = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = root
    return root


class ExternalQuimbCotengraCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.binding = CapabilityBinding(
            capability_id=CAPABILITY_ID,
            run_id="fresh-quimb-cotengra-a",
            flow_policy_sha256=hashlib.sha256(b"flow-policy-a").hexdigest(),
            request_sha256=hashlib.sha256(b"request-a").hexdigest(),
            step_id=STEP_ID,
            challenge_seed_hex=hashlib.sha256(b"quimb-cotengra-seed-a").hexdigest(),
        )
        cls.broker = QuimbCotengraCapabilityBroker()
        cls.receipt = cls.broker.run(cls.binding)

    def _validate(self, receipt: dict[str, object]) -> tuple[str, ...]:
        return validate_quimb_cotengra_capability_receipt(
            receipt,
            expected_binding=self.binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
        )

    def test_fresh_real_external_quimb_and_cotengra_operations_pass(self) -> None:
        receipt = self.receipt

        self.assertEqual(receipt["schema"], CAPABILITY_SCHEMA)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["reason"], "exact_operation_controls_passed")
        self.assertEqual(self._validate(receipt), ())
        self.assertTrue(receipt["external_system"])
        self.assertEqual(receipt["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
        self.assertFalse(receipt["promotion_allowed"])
        self.assertFalse(receipt["engine_readiness_claim"])
        self.assertFalse(receipt["cr_truth_claim"])
        self.assertFalse(receipt["release_allowed"])
        self.assertEqual(receipt["claim_ceiling"], CLAIM_CEILING)

        self.assertEqual([row["profile_id"] for row in receipt["rows"]], [QUIMB_PROFILE, COTENGRA_PROFILE])
        for row in receipt["rows"]:
            self.assertEqual(row["status"], "PASS")
            self.assertEqual(row["reason"], "exact_operation_controls_passed")
            self.assertEqual(row["exact_api"], list(EXACT_APIS[row["profile_id"]]))
            self.assertTrue(all(row["controls"].values()))
            expected_runtime = {"package_version": PACKAGE_VERSIONS[row["profile_id"]]}
            if row["profile_id"] == COTENGRA_PROFILE:
                expected_runtime["optimizer_config"] = COTENGRA_OPTIMIZER_CONFIG
            self.assertEqual(row["worker_witness"]["runtime"], expected_runtime)
            self.assertNotEqual(row["worker_witness"]["pid"], os.getpid())

        quimb_row, cotengra_row = receipt["rows"]
        self.assertEqual(
            set(quimb_row["controls"]),
            {"positive", "targeted_negative", "boundary", "operation_severance"},
        )
        self.assertEqual(quimb_row["expected"]["trace"], 1.0)
        self.assertEqual(quimb_row["expected"]["boundary_trace"], 1.0)
        self.assertEqual(cotengra_row["expected"], {"contraction_cost": 12, "max_size": 4, "boundary_contraction_cost": 2, "boundary_max_size": 1})

    def test_controller_owned_cache_environment_is_bound_and_python_paths_are_scrubbed(self) -> None:
        receipt = self.receipt

        self.assertEqual(receipt["environment_policy"], ENVIRONMENT_POLICY)
        self.assertEqual(receipt["environment_policy_sha256"], ENVIRONMENT_POLICY_SHA256)
        for row in receipt["rows"]:
            environment = row["environment"]
            self.assertEqual(environment["PATH"], "/usr/bin:/bin")
            self.assertTrue(environment["HOME"].startswith("/private/tmp/constraintbox-quimb-cotengra-"))
            self.assertEqual(environment["PYTHONHASHSEED"], "0")
            self.assertIsNone(environment["PYTHONPATH"])
            self.assertIsNone(environment["PYTHONHOME"])
            self.assertTrue(environment["NUMBA_CACHE_DIR"].startswith("/private/tmp/constraintbox-quimb-cotengra-"))
            self.assertTrue(environment["MPLCONFIGDIR"].startswith("/private/tmp/constraintbox-quimb-cotengra-"))
            self.assertEqual(row["worker_witness"]["environment"], environment)
            self.assertEqual(row["runtime"]["invoked_path"], RUNTIME_INVOKED_PATH)
            self.assertEqual(row["runtime"]["resolved_path"], RUNTIME_RESOLVED_PATH)
            self.assertEqual(row["runtime"]["sha256"], RUNTIME_SHA256)
            self.assertEqual(row["worker_source_sha256"], WORKER_SHA256)
            self.assertEqual(row["worker_source_sha256_expected"], WORKER_SHA256)

    def test_package_and_worker_artifacts_are_pinned_before_real_apis_run(self) -> None:
        state = self.receipt["runtime_and_artifacts_before"]
        self.assertEqual(state["status"], "PASS")
        self.assertTrue(state["runtime"]["matches"])
        self.assertEqual(state["worker"]["sha256"], WORKER_SHA256)
        self.assertTrue(state["worker"]["matches"])
        expected_pins = {pin.label: pin for pin in ARTIFACT_PINS}
        self.assertEqual({row["label"] for row in state["artifacts"]}, set(expected_pins))
        for row in state["artifacts"]:
            pin = expected_pins[row["label"]]
            self.assertEqual(row["size_bytes"], pin.size_bytes)
            self.assertEqual(row["sha256"], pin.sha256)
            self.assertTrue(row["matches"])
            self.assertEqual(digest(Path(pin.path)), pin.sha256)
        self.assertEqual(digest(self.broker.worker_path), WORKER_SHA256)

    def test_actual_operation_severance_probes_cover_all_declared_load_bearing_apis(self) -> None:
        expected_poison_targets = {
            QUIMB_PROFILE: ("quimb.eigvalsh", "quimb.trace"),
            COTENGRA_PROFILE: ("cotengra.HyperOptimizer.search",),
        }
        for row in self.receipt["rows"]:
            poison_rows = row["operation_severance"]
            self.assertEqual(
                tuple(item["poisoned_api"] for item in poison_rows),
                expected_poison_targets[row["profile_id"]],
            )
            for item in poison_rows:
                self.assertTrue(item["accepted"])
                self.assertIsNone(item["error"])
                self.assertEqual(item["launch"]["status"], "PASS")
                self.assertEqual(
                    item["launch"]["response"]["poisoned_api"],
                    item["poisoned_api"],
                )
                self.assertNotEqual(item["launch"]["response"]["pid"], os.getpid())

    def test_wrong_value_receipt_cannot_pass_after_rehash(self) -> None:
        forged = copy.deepcopy(self.receipt)
        quimb_row = forged["rows"][0]
        wrong_values = quimb_row["challenge_case"]["wrong_eigenvalues"]
        quimb_row["worker_witness"]["observed"]["eigenvalues"] = wrong_values
        quimb_row["normal_launch"]["response"] = quimb_row["worker_witness"]
        witness_sha = hashlib.sha256(canonical_json(quimb_row["worker_witness"])).hexdigest()
        quimb_row["worker_witness_sha256"] = witness_sha
        quimb_row["normal_launch"]["response_sha256"] = witness_sha
        root = rebuild_root(forged)

        errors = validate_quimb_cotengra_capability_receipt(
            forged,
            expected_binding=self.binding,
            expected_receipt_sha256=root,
        )
        self.assertTrue(
            any("quimb-density-v1_witness_evaluation_failed" in error or "quimb-density-v1_control_replay_mismatch" in error for error in errors),
            errors,
        )

    def test_binding_or_severance_substitution_cannot_pass_after_rehash(self) -> None:
        binding_tampered = copy.deepcopy(self.receipt)
        binding_tampered["binding"]["run_id"] = "forged-quimb-cotengra-run"
        binding_tampered["binding_sha256"] = hashlib.sha256(canonical_json(binding_tampered["binding"])).hexdigest()
        root = rebuild_root(binding_tampered)
        binding_errors = validate_quimb_cotengra_capability_receipt(
            binding_tampered,
            expected_binding=self.binding,
            expected_receipt_sha256=root,
        )
        self.assertTrue(any("binding" in error for error in binding_errors), binding_errors)

        severance_tampered = copy.deepcopy(self.receipt)
        severance_tampered["rows"][1]["operation_severance"][0]["accepted"] = False
        root = rebuild_root(severance_tampered)
        severance_errors = validate_quimb_cotengra_capability_receipt(
            severance_tampered,
            expected_binding=self.binding,
            expected_receipt_sha256=root,
        )
        self.assertTrue(
            any("cotengra-triangle-path-v1_severance_replay_failed" in error for error in severance_errors),
            severance_errors,
        )

    def test_same_binding_replays_real_operations_with_the_same_challenges(self) -> None:
        replay = self.broker.run(self.binding)

        self.assertEqual(replay["status"], "PASS")
        self.assertEqual(
            validate_quimb_cotengra_capability_receipt(
                replay,
                expected_binding=self.binding,
                expected_receipt_sha256=replay["receipt_sha256"],
            ),
            (),
        )
        self.assertEqual(
            [row["challenge_case"] for row in replay["rows"]],
            [row["challenge_case"] for row in self.receipt["rows"]],
        )
        self.assertEqual(
            [row["expected"] for row in replay["rows"]],
            [row["expected"] for row in self.receipt["rows"]],
        )
        self.assertNotEqual(
            replay["rows"][0]["environment"]["NUMBA_CACHE_DIR"],
            self.receipt["rows"][0]["environment"]["NUMBA_CACHE_DIR"],
        )

    def test_invalid_binding_or_worker_source_drift_prevents_child_execution(self) -> None:
        invalid = CapabilityBinding(
            capability_id="not-a-capability",
            run_id="bad-binding",
            flow_policy_sha256="0" * 64,
            request_sha256="1" * 64,
            step_id=STEP_ID,
            challenge_seed_hex="2" * 64,
        )
        with mock.patch.object(capability_module.subprocess, "run") as launched:
            with self.assertRaises(ExternalQuimbCotengraCapabilityError):
                self.broker.run(invalid)
        launched.assert_not_called()

        with mock.patch.object(capability_module, "WORKER_SHA256", "0" * 64):
            source_drift = self.broker.run(self.binding)
        self.assertEqual(source_drift["status"], "FAIL")
        self.assertEqual(source_drift["reason"], "worker_source_digest_mismatch")
        self.assertEqual(source_drift["rows"], [])

    def test_controller_challenge_is_deterministic_and_not_model_authored(self) -> None:
        cases = derive_challenge_cases(self.binding.challenge_seed_hex)
        self.assertEqual(cases, derive_challenge_cases(self.binding.challenge_seed_hex))
        self.assertNotEqual(
            cases,
            derive_challenge_cases(hashlib.sha256(b"different-seed").hexdigest()),
        )
        self.assertEqual(cases[COTENGRA_PROFILE]["inputs"], [[0, 1], [1, 2], [2, 0]])
        self.assertEqual(cases[COTENGRA_PROFILE]["sizes"], {"0": 2, "1": 2, "2": 2})


if __name__ == "__main__":
    unittest.main()
