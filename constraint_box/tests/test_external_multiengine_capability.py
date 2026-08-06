from __future__ import annotations

import copy
import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from constraintbox.capability_suite import _validate_component_result
from constraintbox.external_multiengine_capability import (
    CAPABILITY_ID,
    CAPABILITY_SCHEMA,
    CLAIM_CEILING,
    MultiEngineBinding,
    derive_multiengine_challenge,
    multiengine_binding_from_dict,
    run_multiengine_capability_flow,
    validate_multiengine_capability_receipt,
)
from constraintbox.intake import canonical_json, parse_json_object


def _refresh_row(row: dict) -> None:
    row["stdout"] = canonical_json(row["witness"]).decode("utf-8") + "\n"
    row["stdout_sha256"] = hashlib.sha256(
        row["stdout"].encode("utf-8")
    ).hexdigest()
    row["output_sha256"] = hashlib.sha256(
        canonical_json(row["witness"])
    ).hexdigest()


def _refresh_receipt(receipt: dict) -> str:
    body = dict(receipt)
    body.pop("receipt_sha256", None)
    root = hashlib.sha256(canonical_json(body)).hexdigest()
    receipt["receipt_sha256"] = root
    return root


class ExternalMultiEngineCapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls._temporary_directory.name).resolve()
        cls.result = run_multiengine_capability_flow(
            request_id="multiengine-real",
            run_root=cls.root / "multiengine-real",
        )
        cls.receipt = parse_json_object(
            Path(cls.result["artifacts"]["capability_receipt"]).read_bytes()
        )
        cls.flow = parse_json_object(
            Path(cls.result["artifacts"]["flow_receipt"]).read_bytes()
        )
        cls.binding = multiengine_binding_from_dict(cls.receipt["binding"])

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def _validate(
        self, receipt: dict, *, require_pass: bool = True
    ) -> tuple[str, ...]:
        return validate_multiengine_capability_receipt(
            receipt,
            expected_binding=self.binding,
            expected_receipt_sha256=receipt["receipt_sha256"],
            require_pass=require_pass,
        )

    def test_real_profile_is_capability_suite_compatible(self) -> None:
        self.assertEqual(self.result["capability_id"], CAPABILITY_ID)
        self.assertEqual(self.result["disposition"], "ELIGIBLE")
        self.assertEqual(self.receipt["schema"], CAPABILITY_SCHEMA)
        self.assertEqual(self.receipt["status"], "PASS")
        self.assertEqual(self.receipt["claim_ceiling"], CLAIM_CEILING)
        self.assertIn("SMT remains", CLAIM_CEILING)
        self.assertFalse(self.result["engine_readiness_claim"])
        self.assertFalse(self.result["cr_truth_claim"])
        self.assertFalse(self.result["promotion_allowed"])
        self.assertIn("not general engine readiness", CLAIM_CEILING)
        self.assertEqual(self._validate(self.receipt), ())
        self.assertEqual(
            _validate_component_result(
                self.result,
                capability_id=CAPABILITY_ID,
                request_id="multiengine-real",
                run_root=self.root / "multiengine-real",
            ),
            self.result,
        )

    def test_fixed_tool_gate_flow_and_replay_are_real(self) -> None:
        self.assertEqual(self.flow["terminal"], "ELIGIBLE")
        self.assertEqual(self.flow["steps"], 2)
        self.assertEqual(
            [node["node_id"] for node in self.flow["policy"]["nodes"]],
            ["multiengine-tool", "multiengine-gate"],
        )
        self.assertEqual(
            self.flow["completed_nodes"],
            ["multiengine-gate", "multiengine-tool"],
        )
        self.assertTrue(all(self.receipt["controls"].values()))
        lanes = self.receipt["lanes"]
        for lane_name in ("python_dlpack_jax", "julia_diffeq"):
            primary = lanes[lane_name]["primary"]
            replay = lanes[lane_name]["replay"]
            self.assertNotEqual(primary["child_pid"], os.getpid())
            self.assertNotEqual(replay["child_pid"], os.getpid())
            self.assertEqual(primary["returncode"], 0)
            self.assertEqual(replay["returncode"], 0)
            self.assertEqual(primary["witness"]["reads_peer_output"], False)
            self.assertEqual(replay["witness"]["reads_peer_output"], False)
            self.assertEqual(primary["witness"]["input_origin"], "controller-derived")
            self.assertEqual(replay["witness"]["input_origin"], "controller-derived")

    def test_named_apis_and_no_array_serialization_bridge(self) -> None:
        lanes = self.receipt["lanes"]
        self.assertEqual(
            lanes["python_dlpack_jax"]["primary"]["witness"]["exact_apis"],
            [
                "torch.func.jacrev",
                "torch.utils.dlpack.to_dlpack",
                "jax.dlpack.from_dlpack",
                "jax.jit",
                "jax.vmap",
            ],
        )
        self.assertEqual(
            lanes["julia_diffeq"]["primary"]["witness"]["exact_apis"],
            [
                "DifferentialEquations.ODEProblem",
                "DifferentialEquations.solve",
                "DifferentialEquations.Tsit5",
            ],
        )
        python_source = Path(
            lanes["python_dlpack_jax"]["primary"]["command"][-1]
        ).read_text(encoding="utf-8")
        self.assertNotIn(".numpy(", python_source)
        self.assertNotIn("np.asarray", python_source)
        self.assertIn("torch_dlpack.to_dlpack", python_source)
        self.assertIn("jax_dlpack.from_dlpack", python_source)
        julia_source = Path(
            lanes["julia_diffeq"]["primary"]["command"][-1]
        ).read_text(encoding="utf-8")
        self.assertIn("DifferentialEquations.ODEProblem", julia_source)
        self.assertIn("DifferentialEquations.solve", julia_source)
        self.assertIn("DifferentialEquations.Tsit5", julia_source)

    def test_controller_recomputation_rejects_rehashed_severance_substitution(
        self,
    ) -> None:
        tampered = copy.deepcopy(self.receipt)
        primary = tampered["lanes"]["python_dlpack_jax"]["primary"]
        primary["witness"]["observed"]["jax_output"] = list(
            primary["witness"]["observed"]["severed_jax_output"]
        )
        _refresh_row(primary)
        root = _refresh_receipt(tampered)
        errors = validate_multiengine_capability_receipt(
            tampered,
            expected_binding=self.binding,
            expected_receipt_sha256=root,
            require_pass=True,
        )
        self.assertTrue(errors)
        self.assertTrue(
            any(
                "controller_recomputed_controls" in error
                for error in errors
            )
        )

    def test_fresh_binding_challenge_is_seed_bound(self) -> None:
        first = derive_multiengine_challenge("00" * 32)
        second = derive_multiengine_challenge("01" * 32)
        self.assertNotEqual(first, second)
        forged = MultiEngineBinding(
            capability_id=self.binding.capability_id,
            run_id="forged-run",
            flow_policy_sha256=self.binding.flow_policy_sha256,
            request_sha256=self.binding.request_sha256,
            step_id=self.binding.step_id,
            challenge_seed_hex=self.binding.challenge_seed_hex,
        )
        errors = validate_multiengine_capability_receipt(
            self.receipt,
            expected_binding=forged,
            expected_receipt_sha256=self.receipt["receipt_sha256"],
            require_pass=True,
        )
        self.assertTrue(errors)
        self.assertTrue(any("binding_mismatch" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
