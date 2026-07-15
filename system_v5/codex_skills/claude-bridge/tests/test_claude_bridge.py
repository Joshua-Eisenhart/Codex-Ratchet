from __future__ import annotations

import copy
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import claude_bridge  # noqa: E402
import validate_receipt  # noqa: E402


class RoutingTests(unittest.TestCase):
    def test_fable_spellings_use_live_fable_alias(self) -> None:
        for requested in ("fable", "fable5", "fable-5", "FABLE5"):
            with self.subTest(requested=requested):
                self.assertEqual(claude_bridge.resolve_model(requested), "fable")

    def test_default_remains_distinct_from_fable(self) -> None:
        self.assertEqual(claude_bridge.resolve_model("default"), "default")
        self.assertNotEqual(
            claude_bridge.resolve_model("default"), claude_bridge.resolve_model("fable5")
        )
        self.assertEqual(
            claude_bridge.route_metadata("default")["resolution_kind"],
            "configured_default",
        )

    def test_other_moving_aliases_remain_live(self) -> None:
        for name in ("opus", "sonnet", "haiku"):
            self.assertEqual(claude_bridge.resolve_model(name), name)
            self.assertEqual(
                claude_bridge.route_metadata(name)["resolution_kind"], "moving_alias"
            )

    def test_explicit_full_identifier_passes_through_unchanged(self) -> None:
        model = "claude-sonnet-4-9-20261231"
        self.assertEqual(claude_bridge.resolve_model(model), model)
        self.assertEqual(
            claude_bridge.route_metadata(model)["resolution_kind"],
            "explicit_passthrough",
        )

    def test_empty_model_fails(self) -> None:
        with self.assertRaises(ValueError):
            claude_bridge.resolve_model("  ")


class ParsingTests(unittest.TestCase):
    def test_json_parser_uses_model_usage_as_backend_truth(self) -> None:
        raw = json.dumps(
            {
                "subtype": "success",
                "is_error": False,
                "total_cost_usd": 0.25,
                "duration_ms": 123,
                "result": "advisory text",
                "modelUsage": {
                    "claude-backend-new": {"inputTokens": 10, "outputTokens": 5}
                },
            }
        )
        parsed = claude_bridge.summarize_json_text(raw)
        self.assertTrue(parsed["parse_ok"])
        self.assertEqual(parsed["models"], ["claude-backend-new"])
        self.assertEqual(parsed["total_cost_usd"], 0.25)

    def test_json_parser_fails_closed_on_non_object(self) -> None:
        parsed = claude_bridge.summarize_json_text("[]")
        self.assertFalse(parsed["parse_ok"])
        self.assertEqual(parsed["models"], [])

    def test_stream_parser_counts_completion_not_just_start(self) -> None:
        events = [
            {"type": "system", "subtype": "task_started"},
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Agent"},
                        {"type": "tool_use", "name": "Read"},
                    ]
                },
            },
            {
                "type": "system",
                "subtype": "task_notification",
                "status": "completed",
            },
            {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "total_cost_usd": 0.4,
                "modelUsage": {"claude-backend-stream": {"costUSD": 0.4}},
            },
        ]
        raw = "noise\n" + "\n".join(json.dumps(event) for event in events)
        parsed = claude_bridge.summarize_stream_text(raw)
        self.assertTrue(parsed["parse_ok"])
        self.assertEqual(parsed["task_started"], 1)
        self.assertEqual(parsed["task_completed"], 1)
        self.assertEqual(parsed["agent_tool_calls"], 1)
        self.assertEqual(parsed["models"], ["claude-backend-stream"])

    def test_stream_without_result_fails_parse_contract(self) -> None:
        parsed = claude_bridge.summarize_stream_text(
            json.dumps({"type": "system", "subtype": "task_started"})
        )
        self.assertFalse(parsed["parse_ok"])
        self.assertIn("no result", parsed["parse_error"])


class BudgetAndCommandTests(unittest.TestCase):
    def test_budget_logic_handles_unknown_equal_and_exceeded(self) -> None:
        self.assertIsNone(claude_bridge.budget_summary(2, None)["exceeded"])
        self.assertFalse(claude_bridge.budget_summary(2, 2)["exceeded"])
        self.assertTrue(claude_bridge.budget_summary(2, 2.01)["exceeded"])

    def test_invalid_budgets_fail(self) -> None:
        for value in (0, -1, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                claude_bridge.normalize_budget(value)

    def test_command_construction_routes_alias_and_disables_tools_by_default(self) -> None:
        command = claude_bridge.build_command(
            requested_model="fable5",
            budget=2,
            stream=False,
            tools="",
            requested_cwd="/tmp",
        )
        self.assertEqual(command[command.index("--model") + 1], "fable")
        self.assertEqual(command[command.index("--max-budget-usd") + 1], "2.0")
        self.assertEqual(command[-2:], ["--tools", ""])
        self.assertNotIn("--add-dir", command)

    def test_stream_command_uses_explicit_tools_and_full_model(self) -> None:
        model = "claude-opus-4-9-20990101"
        command = claude_bridge.build_command(
            requested_model=model,
            budget=3,
            stream=True,
            tools="Task,Read",
            requested_cwd="/work/repo",
            effort="high",
            fallback_model="fable-5",
        )
        self.assertEqual(command[command.index("--model") + 1], model)
        self.assertIn("--verbose", command)
        self.assertEqual(command[command.index("--allowedTools") + 1], "Task,Read")
        self.assertEqual(command[command.index("--fallback-model") + 1], "fable")
        self.assertEqual(command[command.index("--add-dir") + 1], "/work/repo")


class ReceiptTests(unittest.TestCase):
    def _make_dry_receipt(self, directory: str) -> dict:
        args = claude_bridge.parse_args(
            [
                "--dry-run",
                "--model",
                "fable5",
                "--budget",
                "2",
                "--cwd",
                "/tmp",
                "--out-dir",
                directory,
                "--name",
                "unit",
                "--prompt",
                "bounded advisory review",
            ]
        )
        with mock.patch.object(claude_bridge.subprocess, "run") as run:
            receipt, returncode = claude_bridge.run_bridge(args)
        run.assert_not_called()
        self.assertEqual(returncode, 0)
        return receipt

    def test_dry_run_never_spawns_claude_and_receipt_validates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt = self._make_dry_receipt(directory)
            self.assertFalse(receipt["provider_invoked"])
            self.assertEqual(receipt["execution_mode"], "dry_run")
            self.assertEqual(validate_receipt.validate_receipt(receipt), [])

    def test_receipt_hashes_cover_prompt_and_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt = self._make_dry_receipt(directory)
            self.assertEqual(
                receipt["prompt_sha256"],
                claude_bridge.sha256_file(Path(receipt["prompt_path"])),
            )
            self.assertEqual(
                receipt["output_sha256"],
                claude_bridge.sha256_file(Path(receipt["output_path"])),
            )

    def test_validator_fails_closed_on_authority_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt = self._make_dry_receipt(directory)
            mutations = {
                "advisory_only": False,
                "gate_authority": True,
                "evidence_allowed": True,
                "promotion_allowed": True,
                "formal_admission_allowed": True,
                "release_eligible": True,
                "official_launch_allowed": True,
                "scientific_claim_proven": True,
                "gate_decision": "pass",
            }
            for key, value in mutations.items():
                with self.subTest(key=key):
                    changed = copy.deepcopy(receipt)
                    changed[key] = value
                    self.assertTrue(validate_receipt.validate_receipt(changed))

    def test_validator_rejects_hash_and_command_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt = self._make_dry_receipt(directory)
            changed_hash = copy.deepcopy(receipt)
            changed_hash["output_sha256"] = "0" * 64
            self.assertTrue(validate_receipt.validate_receipt(changed_hash))
            changed_command = copy.deepcopy(receipt)
            changed_command["command"].append("--dangerous-extra")
            self.assertTrue(validate_receipt.validate_receipt(changed_command))

    def test_validator_rejects_model_usage_and_returncode_drift(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt = self._make_dry_receipt(directory)
            changed_models = copy.deepcopy(receipt)
            changed_models["parsed"]["models"] = ["invented-backend"]
            changed_models["backend_models"] = ["invented-backend"]
            self.assertTrue(validate_receipt.validate_receipt(changed_models))
            changed_returncode = copy.deepcopy(receipt)
            changed_returncode["wrapper_returncode"] = 7
            self.assertTrue(validate_receipt.validate_receipt(changed_returncode))

    def test_live_invalid_json_returns_wrapper_failure_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            args = claude_bridge.parse_args(
                [
                    "--model",
                    "default",
                    "--budget",
                    "1",
                    "--cwd",
                    "/tmp",
                    "--out-dir",
                    directory,
                    "--prompt",
                    "bounded advisory review",
                ]
            )
            completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="not json")
            with mock.patch.object(
                claude_bridge.subprocess, "run", return_value=completed
            ) as run:
                receipt, returncode = claude_bridge.run_bridge(args)
            self.assertEqual(run.call_count, 1)
            self.assertEqual(returncode, 3)
            self.assertFalse(receipt["parsed"]["parse_ok"])
            self.assertEqual(validate_receipt.validate_receipt(receipt), [])

    def test_route_inspection_does_not_load_prompt_or_spawn(self) -> None:
        stdout = io.StringIO()
        with mock.patch.object(claude_bridge, "load_prompt") as load_prompt, mock.patch.object(
            claude_bridge.subprocess, "run"
        ) as run, redirect_stdout(stdout):
            returncode = claude_bridge.main(["--inspect-route", "--model", "fable-5"])
        self.assertEqual(returncode, 0)
        load_prompt.assert_not_called()
        run.assert_not_called()
        self.assertEqual(json.loads(stdout.getvalue())["routed_model"], "fable")


if __name__ == "__main__":
    unittest.main()
