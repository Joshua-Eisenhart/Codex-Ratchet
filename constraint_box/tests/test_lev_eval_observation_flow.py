from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from constraintbox import lev_eval_observation_flow
from constraintbox.lev_eval_observation_flow import (
    FLOW_RECEIPT_NAME,
    load_lev_eval_observation_flow,
    run_lev_eval_observation_flow,
    verify_lev_eval_observation_flow,
)

from test_lev_eval_observation import build_current_lev_bundle, write_json


class LevEvalObservationFlowTests(unittest.TestCase):
    def _run(self, root: Path, source: Path):
        return run_lev_eval_observation_flow(
            request_id="historical-observation-flow-1",
            source_run_dir=source,
            expected_execution_id="cb-observe-fixture-v1",
            expected_suite_id="constraintbox-foreign-eval-fixture",
            run_root=root / "cb-flow",
        )

    def test_valid_foreign_bundle_is_retained_replayed_and_parked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            result = self._run(root, source)

            self.assertEqual(result.terminal, "PARKED")
            self.assertEqual(result.flow_receipt["steps"], 2)
            self.assertEqual(
                result.flow_receipt["completed_nodes"],
                ["observe-foreign-eval", "replay-verify-foreign-eval"],
            )
            self.assertFalse(result.flow_receipt["promotion_allowed"])
            self.assertNotIn("ELIGIBLE", result.flow_receipt["policy"]["terminal_nodes"])
            self.assertNotIn("RELEASED", result.flow_receipt["policy"]["terminal_nodes"])
            self.assertNotIn(str(source), json.dumps(result.flow_receipt, sort_keys=True))
            self.assertNotIn(
                "decision_verdict",
                result.flow_ledger_path.read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                str(source),
                result.flow_ledger_path.read_text(encoding="utf-8"),
            )
            self.assertNotIn(
                "decision_reason_code",
                result.flow_ledger_path.read_text(encoding="utf-8"),
            )
            valid, reason = verify_lev_eval_observation_flow(result)
            self.assertTrue(valid, reason)
            shutil.rmtree(source)
            valid, reason = verify_lev_eval_observation_flow(result)
            self.assertTrue(valid, reason)
            reloaded = load_lev_eval_observation_flow(result.flow_root)
            self.assertEqual(reloaded.terminal, "PARKED")
            self.assertIsNone(reloaded.binding.source_run_dir)

    def test_foreign_fail_is_not_a_cb_terminal_selector(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            bundle = build_current_lev_bundle(source)
            bundle["decision"]["verdict"] = "fail"
            bundle["decision"]["reason_code"] = "case_failed"
            bundle["seal"]["outcome"] = "failed"
            write_json(source / "decision.json", bundle["decision"])
            write_json(source / "seal.json", bundle["seal"])

            result = self._run(root, source)

            self.assertEqual(result.terminal, "PARKED")
            self.assertEqual(
                result.flow_receipt["final_context"]["lev_eval_observation_replay_state"],
                "retained_snapshot_rechecked",
            )

    def test_tampered_retained_snapshot_holds_before_a_parked_result_can_be_kept(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            original_verify = lev_eval_observation_flow.verify_lev_eval_observation_snapshot
            calls = 0

            def tampering_verify(**kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    observation_root = kwargs["observation_run_dir"]
                    (
                        observation_root
                        / "foreign_lev_eval_bundle"
                        / "measurements.jsonl"
                    ).write_bytes(b"{}\n")
                return original_verify(**kwargs)

            with patch.object(
                lev_eval_observation_flow,
                "verify_lev_eval_observation_snapshot",
                side_effect=tampering_verify,
            ):
                result = self._run(root, source)

            self.assertEqual(result.terminal, "HOLD")
            self.assertFalse(result.flow_receipt["promotion_allowed"])

    def test_missing_selected_source_parks_without_a_capture_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            result = self._run(root, root / "missing-foreign-run")

            self.assertEqual(result.terminal, "PARKED")
            self.assertEqual(result.flow_receipt["steps"], 1)
            self.assertFalse(
                (result.flow_root / "lev_eval_observation").exists()
            )

    def test_a_valid_minilev_receipt_with_a_positive_terminal_policy_is_rejected(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            result = self._run(root, source)
            altered = json.loads(json.dumps(result.flow_receipt))
            altered["policy"]["terminal_nodes"] = ["PARKED", "HOLD", "ELIGIBLE"]

            valid, reason = verify_lev_eval_observation_flow(
                replace(result, flow_receipt=altered)
            )

            self.assertFalse(valid)
            self.assertIn("terminals", reason)

    def test_persisted_flow_receipt_tampering_fails_replay(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            result = self._run(root, source)
            result.flow_receipt_path.write_text("{}\n", encoding="utf-8")

            valid, reason = verify_lev_eval_observation_flow(result)

            self.assertFalse(valid)
            self.assertIn("persisted observation flow receipt", reason)
            self.assertTrue((result.flow_root / FLOW_RECEIPT_NAME).is_file())

    def test_persisted_flow_replays_in_a_fresh_python_process_without_source(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            result = self._run(root, source)
            shutil.rmtree(source)
            source_root = Path(__file__).resolve().parents[1] / "src"
            environment = dict(os.environ)
            environment["PYTHONPATH"] = str(source_root) + os.pathsep + environment.get(
                "PYTHONPATH", ""
            )
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            script = (
                "from pathlib import Path\n"
                "from constraintbox.lev_eval_observation_flow import load_lev_eval_observation_flow\n"
                f"result = load_lev_eval_observation_flow(Path({str(result.flow_root)!r}))\n"
                "assert result.terminal == 'PARKED'\n"
                "assert result.binding.source_run_dir is None\n"
                "print(result.terminal)\n"
            )
            child_argv = [sys.executable]
            if sys.flags.optimize:
                child_argv.append("-O")
            child_argv.extend(["-c", script])
            completed = subprocess.run(
                child_argv,
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), "PARKED")


if __name__ == "__main__":
    unittest.main()
