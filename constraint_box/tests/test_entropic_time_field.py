from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


BOX = Path(__file__).resolve().parents[1]
SCRIPT = BOX / "scripts" / "contained_light" / "entropic_time_field.py"
FIXTURE = (
    BOX
    / "scripts"
    / "contained_light"
    / "fixtures"
    / "entropic_time_field_v1.json"
)
WRAPPER = BOX / "scripts" / "contained_light" / "seed-check"


def _module():
    spec = importlib.util.spec_from_file_location("cb_entropic_time_field", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load entropic_time_field.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EntropicTimeFieldTests(unittest.TestCase):
    def payload(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_exact_operation_produces_one_gradient_and_all_controls(self) -> None:
        body = _module().evaluate(self.payload(), engine="exact")
        self.assertEqual(body["status"], "PASS", body)
        self.assertEqual(body["field"]["one_gradient"]["support_K"], [1.0, 2.0, 3.0])
        self.assertEqual(body["field"]["one_gradient"]["delta_K"], [1.0, 1.0])
        self.assertEqual(body["field"]["one_gradient"]["time_coordinate_count"], 1)
        self.assertEqual(body["field"]["one_gradient"]["orientation_count"], 2)
        self.assertEqual(
            body["field"]["slices"][1]["capacities"]["record"]["distinct_response_tuples"],
            3,
        )
        self.assertIn(2, [row["size"] for row in body["field"]["slices"][1]["classes"]])
        self.assertTrue(body["field"]["order_witness"]["gap_states"])
        self.assertTrue(body["controls"]["all_pass"], body["controls"])
        self.assertFalse(body["promotion_allowed"])

    def test_exact_replay_is_byte_identity_after_parse(self) -> None:
        module = _module()
        first = module.evaluate(self.payload(), engine="exact")
        second = module.evaluate(self.payload(), engine="exact")
        self.assertEqual(first, second)
        self.assertEqual(first["result_sha256"], second["result_sha256"])

    def test_collapsed_order_refuses(self) -> None:
        payload = self.payload()
        payload["order_witness"]["bind_map"] = {
            state: state for state in payload["order_witness"]["carrier"]
        }
        body = _module().evaluate(payload)
        self.assertEqual(body["status"], "REFUSE")
        self.assertIn("REFUSE_ORDER_GAP_COLLAPSED", body["reason_codes"])

    def test_hidden_relation_cannot_be_quotiented_away(self) -> None:
        payload = self.payload()
        tick_one = payload["slices"][1]
        values = {
            item["probe"]: item["value"]
            for item in tick_one["observations"]
            if item["state"] == "a"
        }
        for item in tick_one["observations"]:
            if item["state"] == "c":
                item["value"] = values[item["probe"]]
        body = _module().evaluate(payload)
        self.assertEqual(body["status"], "REFUSE")
        self.assertIn("REFUSE_RELATION_INCOMPATIBLE_QUOTIENT", body["reason_codes"])

    @unittest.skipUnless(importlib.util.find_spec("jax") is not None, "JAX profile unavailable")
    def test_jax_is_load_bearing_and_agrees_with_exact_reference(self) -> None:
        body = _module().evaluate(self.payload(), engine="dual")
        self.assertEqual(body["status"], "PASS", body)
        self.assertTrue(body["jax"]["ran"])
        self.assertTrue(body["jax"]["x64_enabled"])
        self.assertTrue(body["jax"]["load_bearing"], body["jax"])
        self.assertEqual(body["runtime_binding"]["jax_version"], body["jax"]["jax_version"])
        self.assertEqual(body["runtime_binding"]["jaxlib_version"], body["jax"]["jaxlib_version"])
        self.assertTrue(all(body["jax"]["exact_reference_agreement"]))
        self.assertTrue(body["jax"]["negative_observation_mutation_detected"])
        self.assertTrue(body["jax"]["single_state_boundary_K_zero"])

    def test_public_seed_wrapper_runs_from_repo_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "seed.json"
            env = dict(os.environ)
            env["PYTHON"] = sys.executable
            proc = subprocess.run(
                ["sh", str(WRAPPER), "--out", str(output)],
                cwd=BOX.parent,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            body = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(body["disposition"], "ADMIT")
            self.assertEqual(body["delta_K"], [1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
