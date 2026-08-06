from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "index_external_validation_receipt.py"
SPEC = importlib.util.spec_from_file_location("external_validation_index", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, body: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")


class ExternalValidationIndexTests(unittest.TestCase):
    def test_index_keeps_receipts_under_the_declared_run_root(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "run"
            root.mkdir()
            workload_root = root / "01_integrated_workload"
            receipt_path = workload_root / "capability.json"
            _write(
                receipt_path,
                {
                    "reason": "exact_operation_controls_passed",
                    "row": {"exact_api": ["torch.func.jacrev"]},
                },
            )
            _write(
                workload_root / "suite.json",
                {
                    "components": [
                        {
                            "capability_id": "pytorch-jacobian-v1",
                            "state": "ELIGIBLE",
                            "independent_replay_artifact": "01_pytorch/capability_independent_replay.json",
                            "result": {
                                "artifacts": {
                                    "capability_receipt": "01_integrated_workload/capability.json"
                                }
                            },
                        }
                    ]
                },
            )
            _write(
                root / "01_integrated_workload_result.json",
                {
                    "stages": [
                        {
                            "stage": "external_capability_suite",
                            "disposition": "ELIGIBLE",
                            "reason": "all_fixed_capability_flows_eligible",
                        }
                    ],
                    "external_workload": {"receipt": {"path": "suite.json"}},
                },
            )
            _write(
                root / "external_validation_result.json",
                {
                    "request_id": "external-validation-test",
                    "disposition": "ELIGIBLE",
                    "claim_ceiling": "bounded test receipt",
                    "components": {
                        "integrated_workload": {
                            "run_root": "01_integrated_workload",
                            "artifact": {"path": "01_integrated_workload_result.json"},
                        },
                        "leviathan_reference": {
                            "requested": False,
                            "disposition": "NOT_REQUESTED",
                            "reason": "not_requested",
                        },
                    },
                },
            )

            index = MODULE.build_index(run_root=root)

            self.assertIn("pytorch-jacobian-v1", index)
            self.assertIn("torch.func.jacrev", index)
            self.assertIn("external_capability_suite", index)


if __name__ == "__main__":
    unittest.main()
