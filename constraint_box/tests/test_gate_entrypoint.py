from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from constraintbox.cli import build_parser
from constraintbox.gate import GATE_EXIT_CODES, GateError, run_gate


class GateEntrypointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.constraint_box = Path(__file__).resolve().parents[1]
        cls.chain = cls.constraint_box / "claimgate_plugin" / "claim_verify.py"
        cls.fixtures = cls.constraint_box / "claimgate_plugin" / "fixtures"
        cls.admitted = cls.fixtures / "hook_clean_receipt.json"
        cls.refused = cls.fixtures / "hook_inflated_receipt.json"
        cls.insufficient = (
            cls.fixtures
            / "bypass"
            / "b7_claim_hidden_under_ignored_key.json"
        )

    def _run_chain_directly(self, receipt: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(self.chain), str(receipt)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

    def test_real_fixtures_have_three_distinct_dispositions(self):
        rows = [
            (run_gate(self.admitted), "ADMITTED", 0),
            (run_gate(self.refused), "REFUSED", 1),
            (run_gate(self.insufficient), "INSUFFICIENT_DEPTH", 3),
        ]
        self.assertEqual(
            {row[0]["disposition"] for row in rows},
            {"ADMITTED", "REFUSED", "INSUFFICIENT_DEPTH"},
        )
        for result, disposition, exit_code in rows:
            self.assertEqual(result["disposition"], disposition)
            self.assertEqual(result["chain_exit_code"], exit_code)

    def test_known_good_reports_supply_matching_structured_verdicts(self):
        rows = [
            (run_gate(self.admitted), "VERIFIED"),
            (run_gate(self.refused), "REJECTED"),
            (run_gate(self.insufficient), "INSUFFICIENT_DEPTH"),
        ]
        for result, verdict in rows:
            with self.subTest(verdict=verdict):
                self.assertEqual(result["chain_verdict"], verdict)
                self.assertNotIn("chain_report_error", result)

    def test_receipt_sha256_hashes_raw_bytes(self):
        result = run_gate(self.admitted)
        self.assertEqual(
            result["receipt_sha256"],
            hashlib.sha256(self.admitted.read_bytes()).hexdigest(),
        )

    def test_exit_code_mapping_uses_exact_integer_equality(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for code, forbidden in ((30, "INSUFFICIENT_DEPTH"), (13, "REFUSED")):
                stub = root / f"exit_{code}.py"
                stub.write_text(
                    f"import sys\nsys.exit({code})\n",
                    encoding="utf-8",
                )
                result = run_gate(self.admitted, chain=stub)
                self.assertEqual(result["disposition"], "EVALUATION_ERROR")
                self.assertEqual(result["chain_exit_code"], code)
                self.assertNotEqual(result["disposition"], forbidden)

    def test_pipeline_exit_code_table_is_authoritative(self):
        self.assertEqual(
            GATE_EXIT_CODES,
            {
                "ADMITTED": 0,
                "REFUSED": 1,
                "INSUFFICIENT_DEPTH": 3,
                "PARKED": 4,
                "EVALUATION_ERROR": 5,
            },
        )
        from constraintbox import cli

        for disposition, expected in GATE_EXIT_CODES.items():
            with self.subTest(disposition=disposition):
                argv = ["constraintbox", "gate", str(self.admitted)]
                with (
                    mock.patch.object(sys, "argv", argv),
                    mock.patch.object(
                        cli,
                        "run_gate",
                        return_value={"disposition": disposition},
                    ),
                ):
                    if expected == 0:
                        self.assertIsNone(cli.main())
                    else:
                        with self.assertRaises(SystemExit) as raised:
                            cli.main()
                        self.assertEqual(raised.exception.code, expected)

    def test_unavailable_tier0_checker_parks_without_running_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            checked = (
                root / "claimgate" / "claimgate.py",
                root / "claimgate_plugin" / "claimgate.mjs",
            )
            with (
                mock.patch(
                    "constraintbox.gate._resolve_chain_root",
                    return_value=root,
                ),
                mock.patch("constraintbox.gate.subprocess.run") as run,
            ):
                result = run_gate(self.admitted)
        run.assert_not_called()
        self.assertEqual(result["disposition"], "PARKED")
        self.assertIsNone(result["chain_exit_code"])
        self.assertEqual(result["chain_root"], str(root))
        self.assertFalse(result["chain_root_inside_box"])
        self.assertIsNone(result["tier0_checker"])
        self.assertIn(str(root), result["reason"])
        self.assertIn(str(checked[0]), result["reason"])
        self.assertIn(str(checked[1]), result["reason"])

    def test_started_chain_failures_are_evaluation_errors(self):
        for code in (2, 42):
            with self.subTest(chain_exit_code=code):
                completed = subprocess.CompletedProcess(
                    args=[],
                    returncode=code,
                    stdout="{}",
                    stderr="chain failure",
                )
                with mock.patch(
                    "constraintbox.gate.subprocess.run",
                    return_value=completed,
                ):
                    result = run_gate(self.admitted)
                self.assertEqual(result["disposition"], "EVALUATION_ERROR")
                self.assertEqual(result["chain_exit_code"], code)
                self.assertEqual(
                    GATE_EXIT_CODES[result["disposition"]],
                    5,
                )

    def test_recognized_exit_without_valid_report_is_evaluation_error(self):
        for code in (0, 1, 3):
            for stdout in ("", "{", "[]", "{}"):
                with self.subTest(chain_exit_code=code, stdout=stdout):
                    completed = subprocess.CompletedProcess(
                        args=[],
                        returncode=code,
                        stdout=stdout,
                        stderr="hostile stub",
                    )
                    with mock.patch(
                        "constraintbox.gate.subprocess.run",
                        return_value=completed,
                    ):
                        result = run_gate(self.admitted)
                    self.assertEqual(result["disposition"], "EVALUATION_ERROR")
                    self.assertIsNone(result["chain_verdict"])
                    self.assertIn("chain_report_error", result)

    def test_exit_and_structured_verdict_must_be_consistent(self):
        admitted = self._run_chain_directly(self.admitted)
        refused = self._run_chain_directly(self.refused)
        insufficient = self._run_chain_directly(self.insufficient)
        self.assertEqual(
            (admitted.returncode, refused.returncode, insufficient.returncode),
            (0, 1, 3),
        )
        hostile_pairs = [
            (self.refused, 0, refused.stdout),
            (self.insufficient, 0, insufficient.stdout),
            (self.admitted, 1, admitted.stdout),
            (self.admitted, 3, admitted.stdout),
        ]
        for receipt, code, stdout in hostile_pairs:
            with self.subTest(chain_exit_code=code):
                completed = subprocess.CompletedProcess(
                    args=[],
                    returncode=code,
                    stdout=stdout,
                    stderr="",
                )
                with mock.patch(
                    "constraintbox.gate.subprocess.run",
                    return_value=completed,
                ):
                    result = run_gate(receipt)
                self.assertEqual(result["disposition"], "EVALUATION_ERROR")
                self.assertIn(
                    "inconsistent with verdict",
                    result["chain_report_error"],
                )

    def test_duplicate_json_key_is_not_admissible(self):
        completed = self._run_chain_directly(self.admitted)
        hostile_stdout = completed.stdout.replace(
            '"verdict": "VERIFIED"',
            '"verdict": "REJECTED", "verdict": "VERIFIED"',
            1,
        )
        self.assertNotEqual(hostile_stdout, completed.stdout)
        hostile = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=hostile_stdout,
            stderr="",
        )
        with mock.patch(
            "constraintbox.gate.subprocess.run",
            return_value=hostile,
        ):
            result = run_gate(self.admitted)
        self.assertEqual(result["disposition"], "EVALUATION_ERROR")
        self.assertIn("duplicate JSON key: verdict", result["chain_report_error"])

    def test_internally_contradictory_report_is_not_admissible(self):
        completed = self._run_chain_directly(self.admitted)
        report = json.loads(completed.stdout)
        report["tier_results"][0]["status"] = "FAIL"
        hostile = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(report),
            stderr="",
        )
        with mock.patch(
            "constraintbox.gate.subprocess.run",
            return_value=hostile,
        ):
            result = run_gate(self.admitted)
        self.assertEqual(result["disposition"], "EVALUATION_ERROR")
        self.assertIn("contradicts", result["chain_report_error"])

    def test_report_is_bound_to_the_evaluated_receipt(self):
        completed = self._run_chain_directly(self.admitted)
        report = json.loads(completed.stdout)
        report["receipt"] = str(self.refused)
        hostile = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(report),
            stderr="",
        )
        with mock.patch(
            "constraintbox.gate.subprocess.run",
            return_value=hostile,
        ):
            result = run_gate(self.admitted)
        self.assertEqual(result["disposition"], "EVALUATION_ERROR")
        self.assertIn(
            "does not name the evaluated receipt",
            result["chain_report_error"],
        )

    def test_tier_is_not_producer_selectable(self):
        untouched = run_gate(self.admitted)
        with tempfile.TemporaryDirectory() as directory:
            altered = Path(directory) / "receipt.json"
            body = json.loads(self.admitted.read_text(encoding="utf-8"))
            body["required_tiers"] = ["tier4"]
            body["tier"] = "tier4"
            body["verification"] = {"tier2": {"note": "x"}}
            altered.write_text(json.dumps(body), encoding="utf-8")
            result = run_gate(altered)
        self.assertEqual(result["required_tiers"], untouched["required_tiers"])

    def test_gate_parser_exposes_only_receipt_and_output(self):
        parser = build_parser()
        subparsers = next(
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        )
        gate = subparsers.choices["gate"]
        option_strings = {
            option
            for action in gate._actions
            for option in action.option_strings
        }
        positionals = [
            action
            for action in gate._actions
            if not action.option_strings and action.dest != argparse.SUPPRESS
        ]
        self.assertEqual(option_strings, {"-h", "--help", "--output"})
        self.assertEqual(len(positionals), 1)
        self.assertEqual(positionals[0].dest, "receipt")
        for option in option_strings:
            self.assertFalse(
                any(word in option for word in ("tier", "registry", "claim", "chain"))
            )

    def test_missing_receipt_raises_gate_error(self):
        missing = self.fixtures / "does-not-exist.json"
        with self.assertRaisesRegex(GateError, str(missing.resolve())):
            run_gate(missing)


if __name__ == "__main__":
    unittest.main()
