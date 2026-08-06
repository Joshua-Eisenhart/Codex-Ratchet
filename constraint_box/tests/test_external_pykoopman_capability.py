from __future__ import annotations

import copy
import hashlib
import inspect
import os
import stat
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest import mock

import constraintbox.external_pykoopman_capability as capability_module
from constraintbox.external_pykoopman_capability import (
    BINDING_SCHEMA,
    CAPABILITY_CLAIM_CEILING,
    CAPABILITY_ID,
    CAPABILITY_RECEIPT_NAME,
    CAPABILITY_SCHEMA,
    EXACT_APIS,
    FLOW_LEDGER_NAME,
    FLOW_RECEIPT_NAME,
    PYKOOPMAN_ARTIFACT_PINS,
    PYKOOPMAN_VERSION,
    RUNTIME_PIN,
    CapabilityBinding,
    ExternalPyKoopmanCapabilityFlowError,
    capability_binding_from_dict,
    derive_pykoopman_challenge_case,
    run_pykoopman_capability_flow,
    validate_pykoopman_capability_receipt,
)
from constraintbox.intake import canonical_json, parse_json_object


def _recompute_receipt_root(receipt: dict[str, object]) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    digest = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = digest
    return digest


def _binding(receipt: dict[str, object]) -> CapabilityBinding:
    return capability_binding_from_dict(receipt["binding"])


class ExternalPyKoopmanCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory(dir="/private/tmp")
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.first_result = run_pykoopman_capability_flow(
            request_id="pykoopman-fresh-a",
            run_root=cls.root / "pykoopman-fresh-a",
        )
        cls.second_result = run_pykoopman_capability_flow(
            request_id="pykoopman-fresh-b",
            run_root=cls.root / "pykoopman-fresh-b",
        )
        cls.first_receipt = parse_json_object(
            Path(cls.first_result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.second_receipt = parse_json_object(
            Path(cls.second_result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.first_flow = parse_json_object(
            Path(cls.first_result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.first_binding = _binding(cls.first_receipt)
        cls.second_binding = _binding(cls.second_receipt)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def _validate(
        self,
        receipt: dict[str, object],
        *,
        binding: CapabilityBinding | None = None,
        receipt_sha256: str | None = None,
    ) -> tuple[str, ...]:
        return validate_pykoopman_capability_receipt(
            receipt,
            expected_binding=binding or self.first_binding,
            expected_receipt_sha256=(
                receipt_sha256
                if receipt_sha256 is not None
                else receipt["receipt_sha256"]
            ),
        )

    def test_challenge_derivation_is_fixed_per_seed_and_has_distinct_wrong_value(self) -> None:
        first = derive_pykoopman_challenge_case("00" * 32)

        self.assertEqual(first, derive_pykoopman_challenge_case("00" * 32))
        self.assertNotEqual(first, derive_pykoopman_challenge_case("01" * 32))
        self.assertEqual(len(first["train_states"]), 7)
        self.assertEqual(first["boundary_state"], 0.0)
        self.assertNotEqual(first["wrong_operator"], [[first["rate"]]])

    def test_fresh_real_flow_runs_isolated_identity_edmd_operation(self) -> None:
        receipt = self.first_receipt
        row = receipt["row"]
        flow = self.first_flow

        self.assertEqual(self.first_result["disposition"], "ELIGIBLE")
        self.assertEqual(receipt["schema"], CAPABILITY_SCHEMA)
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["reason"], "exact_operation_controls_passed")
        self.assertEqual(self._validate(receipt), ())
        self.assertEqual(flow["terminal"], "ELIGIBLE")
        self.assertEqual(flow["steps"], 2)
        self.assertEqual(
            flow["completed_nodes"],
            ["pykoopman-capability-gate", "pykoopman-capability-tool"],
        )
        self.assertEqual(row["exact_api"], list(EXACT_APIS))
        self.assertEqual(
            row["controls"],
            {"positive": True, "targeted_negative": True, "boundary": True},
        )
        self.assertNotEqual(row["worker_pid"], os.getpid())
        self.assertEqual(row["runtime"]["pykoopman_version"], PYKOOPMAN_VERSION)
        self.assertEqual(row["command"][0], RUNTIME_PIN.invoked_path)
        self.assertEqual(row["command"][1:4], ["-I", "-B", "-c"])
        self.assertEqual(row["runtime"]["cache_environment"], row["cache_environment"])
        cache_root = Path(receipt["binding"]["cache_root"])
        run_root = Path(self.first_result["artifacts"]["capability_receipt"]).parent
        self.assertEqual(cache_root, run_root / ".constraintbox-pykoopman-cache")
        self.assertEqual(stat.S_IMODE(cache_root.stat().st_mode) & 0o077, 0)
        self.assertEqual(
            row["cache_environment"]["MPLCONFIGDIR"],
            str(cache_root / "matplotlib"),
        )

    def test_host_cache_variables_cannot_influence_new_private_worker_cache(self) -> None:
        poisoned = {
            "MPLCONFIGDIR": str(self.root / "host-selected-matplotlib"),
            "XDG_CACHE_HOME": str(self.root / "host-selected-xdg"),
            "NUMBA_CACHE_DIR": str(self.root / "host-selected-numba"),
            "MPLBACKEND": "TkAgg",
        }
        run_root = self.root / "host-environment-regression"
        with mock.patch.dict(os.environ, poisoned, clear=False):
            result = run_pykoopman_capability_flow(
                request_id="host-environment-regression",
                run_root=run_root,
            )
        receipt = parse_json_object(
            Path(result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cache_root = Path(receipt["binding"]["cache_root"])
        environment = receipt["row"]["cache_environment"]

        self.assertEqual(result["disposition"], "ELIGIBLE")
        self.assertEqual(cache_root, run_root / ".constraintbox-pykoopman-cache")
        self.assertEqual(environment["MPLCONFIGDIR"], str(cache_root / "matplotlib"))
        self.assertEqual(environment["XDG_CACHE_HOME"], str(cache_root / "xdg-cache"))
        self.assertEqual(environment["NUMBA_CACHE_DIR"], str(cache_root / "numba-cache"))
        self.assertEqual(environment["MPLBACKEND"], "Agg")
        self.assertTrue(all(environment[key] != value for key, value in poisoned.items()))
        self.assertEqual(receipt["row"]["runtime"]["cache_environment"], environment)
        self.assertEqual(self._validate(receipt, binding=_binding(receipt)), ())

    def test_fresh_controller_challenge_and_binding_cannot_be_reused(self) -> None:
        self.assertNotEqual(
            self.first_receipt["binding"]["challenge_seed_hex"],
            self.second_receipt["binding"]["challenge_seed_hex"],
        )
        self.assertNotEqual(
            self.first_receipt["challenge_case_sha256"],
            self.second_receipt["challenge_case_sha256"],
        )
        errors = self._validate(
            self.first_receipt,
            binding=self.second_binding,
            receipt_sha256=self.first_receipt["receipt_sha256"],
        )

        self.assertTrue(errors)
        self.assertTrue(any("$.binding" in error for error in errors))
        self.assertTrue(any("$.challenge_case" in error for error in errors))

    def test_source_runtime_pins_and_claim_ceiling_remain_external(self) -> None:
        receipt = self.first_receipt
        row = receipt["row"]

        self.assertEqual(receipt["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")
        self.assertTrue(receipt["external_system"])
        self.assertEqual(receipt["runtime_pin"], RUNTIME_PIN.to_dict())
        self.assertEqual(row["runtime_pin"], RUNTIME_PIN.to_dict())
        self.assertEqual(row["worker_source_sha256"], receipt["capability_source_sha256"])
        self.assertEqual(
            receipt["capability_source_sha256"],
            hashlib.sha256(Path(capability_module.__file__).read_bytes()).hexdigest(),
        )
        observed_labels = {
            artifact["label"]
            for artifact in receipt["pykoopman_sources_after"]["artifacts"]
        }
        self.assertEqual(observed_labels, {pin.label for pin in PYKOOPMAN_ARTIFACT_PINS})
        for field in (
            "release_allowed",
            "engine_readiness_claim",
            "cr_truth_claim",
            "promotion_allowed",
        ):
            self.assertIs(self.first_result[field], False)
            self.assertIs(receipt[field], False)
            self.assertIs(row[field], False)
        self.assertIn("not PyKoopman readiness", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not sim-stack readiness", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not CR truth", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not scientific proof", CAPABILITY_CLAIM_CEILING)
        self.assertIn("not canonical promotion", CAPABILITY_CLAIM_CEILING)
        self.assertEqual(
            Path(self.first_result["artifacts"]["capability_receipt"]).name,
            CAPABILITY_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(self.first_result["artifacts"]["flow_receipt"]).name,
            FLOW_RECEIPT_NAME,
        )
        self.assertEqual(
            Path(self.first_result["artifacts"]["flow_ledger"]).name,
            FLOW_LEDGER_NAME,
        )

    def test_forged_observed_values_fail_controller_recomputation(self) -> None:
        tampered = copy.deepcopy(self.first_receipt)
        row = tampered["row"]
        row["observed"]["operator"] = tampered["challenge_case"]["wrong_operator"]
        witness = {
            "schema": "constraintbox.external-pykoopman-worker-witness.v1",
            "capability_id": CAPABILITY_ID,
            "exact_api": row["exact_api"],
            "execution_binding": row["execution_binding"],
            "capability_source_sha256": row["worker_source_sha256"],
            "runtime_pin": row["runtime_pin"],
            "observed": row["observed"],
            "runtime": row["runtime"],
            "pid": row["worker_pid"],
        }
        witness_bytes = canonical_json(witness)
        row["output_sha256"] = hashlib.sha256(witness_bytes).hexdigest()
        row["stdout_sha256"] = hashlib.sha256(witness_bytes + b"\n").hexdigest()
        root = _recompute_receipt_root(tampered)

        errors = self._validate(tampered, receipt_sha256=root)

        self.assertTrue(errors)
        self.assertTrue(
            any(
                "$.row.controller_evaluation" in error or "$.row.controls" in error
                for error in errors
            )
        )

    def test_actual_operation_is_severed_when_fit_predict_or_edmd_is_poisoned(self) -> None:
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message=r"pkg_resources is deprecated as an API.*",
                category=UserWarning,
            )
            warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"pydmd\..*")
            from pykoopman import Koopman
            from pykoopman.regression import EDMD

        binding_body = self.first_binding.to_dict()
        transport = capability_module._worker_transport(
            binding=binding_body,
            challenge_case=derive_pykoopman_challenge_case(
                self.first_binding.challenge_seed_hex
            ),
            capability_source_sha256=hashlib.sha256(
                Path(capability_module.__file__).read_bytes()
            ).hexdigest(),
        )
        cache_environment = transport["cache_environment"]
        with mock.patch.dict(os.environ, cache_environment, clear=False):
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=SyntaxWarning)
                for owner, method in (
                    (Koopman, "fit"),
                    (Koopman, "predict"),
                    (EDMD, "fit"),
                ):
                    with self.subTest(method=f"{owner.__name__}.{method}"):
                        with mock.patch.object(
                            owner,
                            method,
                            side_effect=RuntimeError(
                                f"poisoned-{owner.__name__}-{method}"
                            ),
                        ):
                            with self.assertRaisesRegex(RuntimeError, "poisoned"):
                                capability_module._worker_witness(transport)

    def test_request_cannot_select_controller_owned_mechanism(self) -> None:
        signature = inspect.signature(run_pykoopman_capability_flow)
        self.assertEqual(list(signature.parameters), ["request_id", "run_root"])
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        forbidden = {
            "executable": "/usr/bin/python3",
            "source": "/tmp/pykoopman.py",
            "tolerance": 1.0,
            "seed": "0" * 64,
            "observable": "Polynomial(8)",
            "regressor": "DMD",
            "transition": "RELEASED",
        }
        for field, value in forbidden.items():
            with self.subTest(field=field), self.assertRaises(TypeError):
                run_pykoopman_capability_flow(
                    request_id="request-authority",
                    run_root=self.root / f"forbidden-{field}",
                    **{field: value},
                )

    def test_existing_run_directory_is_rejected_before_operation(self) -> None:
        existing = self.root / "already-exists"
        existing.mkdir()

        with self.assertRaisesRegex(
            ExternalPyKoopmanCapabilityFlowError,
            "run directory must be new",
        ):
            run_pykoopman_capability_flow(
                request_id="existing-run",
                run_root=existing,
            )

    def test_binding_schema_is_pinned(self) -> None:
        self.assertEqual(self.first_receipt["binding"]["schema"], BINDING_SCHEMA)


if __name__ == "__main__":
    unittest.main()
