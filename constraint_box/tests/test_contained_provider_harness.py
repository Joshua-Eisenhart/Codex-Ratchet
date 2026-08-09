from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox import agentrun
from constraintbox.boxrun import VerifiedBoxRun


class ContainedProviderHarnessTests(unittest.TestCase):
    @staticmethod
    def _verified_box(root: Path) -> VerifiedBoxRun:
        request = (
            b'{"allowed_actions":["invoke_llm"],'
            b'"request_id":"contained-local-provider",'
            b'"schema":"constraintbox.user-request.v1"}'
        )
        context = "[USER PROFILE test v1]\\n- output must be bounded"
        return VerifiedBoxRun(
            root=root.resolve(),
            receipt_sha256="1" * 64,
            request_id="contained-local-provider",
            request_sha256=agentrun._sha256_bytes(request),
            request_canonical=request,
            profile_sha256="2" * 64,
            context_sha256=agentrun._sha256_bytes(context.encode("utf-8")),
            context_text=context,
            external_engine_packet_sha256="3" * 64,
            artifact_sha256s=(("compiled_user_context.txt", "4" * 64),),
        )

    @staticmethod
    def _profile_inputs() -> dict:
        context = "controller-base-MMM"
        return {
            "fixture": {"path": "fixture", "sha256": "f" * 64},
            "estate_controller": {"path": "estate", "sha256": "e" * 64},
            "worker": {"path": "worker", "sha256": "w" * 64},
            "import_blocker": {"path": "blocker", "sha256": "b" * 64},
            "operation_poisoner": {"path": "poison", "sha256": "p" * 64},
            "mmm": {
                "packs": [],
                "sha256": agentrun._sha256_bytes(context.encode("utf-8")),
                "text": context,
            },
        }

    @staticmethod
    def _strong_claim_gate(path: Path) -> dict:
        receipt = path.read_text(encoding="utf-8")
        if agentrun.RELEASE_TEXT not in receipt:
            raise AssertionError("provider output reached the release receipt")
        return {
            "disposition": "ADMITTED",
            "chain_exit_code": 0,
            "chain_verdict": "VERIFIED",
            "required_tiers": ["tier0"],
            "verified_tiers": ["tier0"],
            "required_unmet": [],
            "tamper_events": [],
        }

    def test_agent_components_resolve_inside_constraintbox(self) -> None:
        components = agentrun._harness_components()
        for name, component in components.items():
            module = getattr(component, "__module__", "")
            self.assertTrue(
                module.startswith("constraintbox._provider_harness."),
                f"{name} escaped the contained provider harness: {module}",
            )
        source = Path(agentrun.__file__).read_text(encoding="utf-8")
        self.assertNotIn("scripts.llm_harness", source)

    def test_local_subprocess_is_notarized_and_gated_by_contained_harness(self) -> None:
        components = agentrun._harness_components()
        task = components["TaskSpec"](
            task_id="contained-harness-local-process",
            role="builder",
            prompt="return a bounded untrusted observation",
            classification="scratch_diagnostic",
            claim_ceiling="bounded_tool_execution",
            gate_ceiling_rung="scratch_diagnostic",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            with patch.dict(
                "os.environ",
                {"CONSTRAINTBOX_RUNTIME_DIR": str(root)},
            ):
                output_path = root / "provider-output.txt"
                job = components["ModelJob"](
                    task=task,
                    provider="local_tool",
                    model="contained-local-process",
                    output_path=str(output_path),
                    command=[sys.executable, "-c", "print('untrusted candidate bytes')"],
                    cwd=str(root),
                    produced_by="constraintbox.contained-provider-test",
                )
                receipt = components["run_job"](
                    job,
                    components["LocalToolProvider"](),
                    timeout=5,
                    started_at="2026-07-31T00:00:00+00:00",
                    completed_at="2026-07-31T00:00:01+00:00",
                    receipt_path=root / "provider-receipt.json",
                    notary=components["Notary"](),
                )
                decision = components["provider_gate"](receipt)

                self.assertEqual(receipt.status, "success")
                self.assertEqual(receipt.returncode, 0)
                self.assertTrue(receipt.signature)
                self.assertTrue(output_path.is_file())
                self.assertTrue(decision.admitted)
                self.assertEqual(decision.granted_rung, "scratch_diagnostic")

    def test_missing_runtime_key_location_fails_closed(self) -> None:
        from constraintbox._provider_harness.notary import KeyRegistry

        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "no provider-key location"):
                KeyRegistry().secret_for("contained-missing-runtime")

    def test_default_local_provider_reaches_full_minilev_with_a_real_subprocess(self) -> None:
        try:
            import z3  # noqa: F401
        except ImportError:
            self.skipTest("the Mini-Lev controller needs the pinned Z3 backend")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            box_dir = root / "box"
            box_dir.mkdir()
            run_dir = root / "agent-run"
            stub = root / "local_provider_stub.py"
            # A faithful codex stand-in: real codex emits thread.started and
            # writes a session rollout naming the model it actually ran (the
            # enforced -m argument).  The model-binding gate recomputes the
            # answering model from those rollout bytes, so a stub without them
            # would be honestly unverifiable and could never release.
            stub.write_text(
                "#!" + sys.executable + "\n"
                "import json\n"
                "import os\n"
                "import re\n"
                "import sys\n"
                "match = re.search(r'evidence_ref=([0-9a-f]{64})', sys.argv[-1])\n"
                "if match is None:\n"
                "    raise SystemExit('missing controller evidence reference')\n"
                "thread_id = 'stub-thread-local-0001'\n"
                "model = (sys.argv[sys.argv.index('-m') + 1]\n"
                "         if '-m' in sys.argv else 'stub-default')\n"
                "day = os.path.join(os.environ['CODEX_HOME'],\n"
                "                   'sessions', '2026', '01', '01')\n"
                "os.makedirs(day, exist_ok=True)\n"
                "rollout = os.path.join(\n"
                "    day, 'rollout-2026-01-01T00-00-00-' + thread_id + '.jsonl')\n"
                "with open(rollout, 'w', encoding='utf-8') as handle:\n"
                "    handle.write(json.dumps({'type': 'turn_context',\n"
                "                             'payload': {'model': model}}) + '\\n')\n"
                "print(json.dumps({'type': 'thread.started', "
                "'thread_id': thread_id}))\n"
                "proposal = {'proposal_id': 'local-subprocess-proposal', "
                "'candidate': {'requested_claim': 'bounded_tool_execution', "
                "'evidence_ref': match.group(1)}, "
                "'falsifiers': ['the operation-severance control stops flipping']}\n"
                "print(json.dumps({'type': 'item.completed', "
                "'item': {'type': 'agent_message', "
                "'text': json.dumps(proposal, sort_keys=True)}}))\n",
                encoding="utf-8",
            )
            stub.chmod(0o700)
            verified_box = self._verified_box(box_dir)
            tool_receipt = {
                "schema": "constraintbox.agent-tool-receipt.v1",
                "estate_receipt": {
                    "state": "READY",
                    "capabilities": [
                        {
                            "capability_id": "contained-local-tool",
                            "state": "READY",
                            "controls": {
                                "positive": True,
                                "operation": True,
                                "replay": True,
                                "severance": True,
                            },
                        }
                    ],
                },
                "promotion_allowed": False,
            }
            with (
                patch.object(agentrun, "verify_box_run", return_value=verified_box),
                patch.object(
                    agentrun,
                    "_load_profile_inputs",
                    return_value=(self._profile_inputs(), []),
                ),
                patch.object(
                    agentrun,
                    "_run_fixed_tool",
                    return_value=(tool_receipt, []),
                ),
                patch.dict(
                    "os.environ",
                    {
                        "CONSTRAINTBOX_RUNTIME_DIR": str(root / "runtime"),
                        "CODEX_HOME": str(root / "codex-home"),
                    },
                ),
            ):
                result, code = agentrun._run_agent_for_test(
                    box_dir,
                    run_dir,
                    provider=None,
                    codex_binary=str(stub),
                    claim_gate=self._strong_claim_gate,
                )

            self.assertEqual(code, 0, result)
            self.assertEqual(result["disposition"], "RELEASED")
            self.assertEqual(result["proposal_flow"]["terminal"], "RELEASED")
            self.assertTrue(
                result["contained_provider_harness"]["inside_constraint_box"]
            )
            provider_receipt = Path(
                result["attempts"][0]["provider_receipt"]
            ).read_text(encoding="utf-8")
            self.assertIn('"launch_surface": "local_tool"', provider_receipt)
            self.assertIn('"returncode": 0', provider_receipt)
    def test_public_runner_selects_contained_local_provider_without_override(self) -> None:
        """Public entry selects the contained provider; wrong scope stays refused."""

        try:
            import z3  # noqa: F401
        except ImportError:
            self.skipTest("the Mini-Lev controller needs the pinned Z3 backend")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            box_dir = root / "box"
            box_dir.mkdir()
            run_dir = root / "public-agent-run"
            codex_stub = root / "codex"
            # Faithful codex stand-in (thread.started + rollout naming the -m
            # model); see test_default_local_provider_reaches_full_minilev.
            codex_stub.write_text(
                "#!" + sys.executable + "\n"
                "import json\n"
                "import os\n"
                "import re\n"
                "import sys\n"
                "match = re.search(r'evidence_ref=([0-9a-f]{64})', sys.argv[-1])\n"
                "if match is None:\n"
                "    raise SystemExit('missing controller evidence reference')\n"
                "thread_id = 'stub-thread-public-0001'\n"
                "model = (sys.argv[sys.argv.index('-m') + 1]\n"
                "         if '-m' in sys.argv else 'stub-default')\n"
                "day = os.path.join(os.environ['CODEX_HOME'],\n"
                "                   'sessions', '2026', '01', '01')\n"
                "os.makedirs(day, exist_ok=True)\n"
                "rollout = os.path.join(\n"
                "    day, 'rollout-2026-01-01T00-00-00-' + thread_id + '.jsonl')\n"
                "with open(rollout, 'w', encoding='utf-8') as handle:\n"
                "    handle.write(json.dumps({'type': 'turn_context',\n"
                "                             'payload': {'model': model}}) + '\\n')\n"
                "print(json.dumps({'type': 'thread.started', "
                "'thread_id': thread_id}))\n"
                "proposal = {'proposal_id': 'public-local-provider-proposal', "
                "'candidate': {'requested_claim': 'outside_claim_ceiling', "
                "'evidence_ref': match.group(1)}, "
                "'falsifiers': ['controller should refuse the wrong claim scope']}\n"
                "print(json.dumps({'type': 'item.completed', "
                "'item': {'type': 'agent_message', "
                "'text': json.dumps(proposal, sort_keys=True)}}))\n",
                encoding="utf-8",
            )
            codex_stub.chmod(0o700)
            verified_box = self._verified_box(box_dir)
            tool_receipt = {
                "schema": "constraintbox.agent-tool-receipt.v1",
                "estate_receipt": {
                    "state": "READY",
                    "capabilities": [
                        {
                            "capability_id": "contained-public-local-tool",
                            "state": "READY",
                            "controls": {
                                "positive": True,
                                "operation": True,
                                "replay": True,
                                "severance": True,
                            },
                        }
                    ],
                },
                "promotion_allowed": False,
            }
            with (
                patch.object(agentrun, "verify_box_run", return_value=verified_box),
                patch.object(
                    agentrun,
                    "_load_profile_inputs",
                    return_value=(self._profile_inputs(), []),
                ),
                patch.object(
                    agentrun,
                    "_run_fixed_tool",
                    return_value=(tool_receipt, []),
                ),
                patch.dict(
                    "os.environ",
                    {
                        "CONSTRAINTBOX_RUNTIME_DIR": str(root / "runtime"),
                        "PATH": str(root),
                        "CODEX_HOME": str(root / "codex-home"),
                    },
                    clear=True,
                ),
            ):
                result, code = agentrun.run_agent(box_dir, run_dir)

            self.assertEqual(code, agentrun.RUN_EXIT_CODES["REFUSED"], result)
            self.assertEqual(result["disposition"], "REFUSED")
            self.assertIsNone(result["release"])
            self.assertTrue(
                result["contained_provider_harness"]["inside_constraint_box"]
            )
            self.assertEqual(len(result["attempts"]), agentrun.MAX_ATTEMPTS)
            for attempt in result["attempts"]:
                self.assertEqual(attempt["disposition"], "BLOCKED")
                provider_receipt = Path(attempt["provider_receipt"]).read_text(
                    encoding="utf-8"
                )
                self.assertIn('"launch_surface": "local_tool"', provider_receipt)
                self.assertIn('"returncode": 0', provider_receipt)
                self.assertIn(
                    "CLAIM_CEILING_EXCEEDED", attempt["reason_codes"]
                )

    def test_public_runner_parks_unconfigured_remote_route_without_local_fallback(self) -> None:
        """An explicit remote route without its key cannot spend the local route."""

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            box_dir = root / "box"
            box_dir.mkdir()
            run_dir = root / "remote-route-without-key"
            verified_box = self._verified_box(box_dir)
            tool_receipt = {
                "schema": "constraintbox.agent-tool-receipt.v1",
                "estate_receipt": {
                    "state": "READY",
                    "capabilities": [
                        {
                            "capability_id": "contained-remote-route-tool",
                            "state": "READY",
                            "controls": {
                                "positive": True,
                                "operation": True,
                                "replay": True,
                                "severance": True,
                            },
                        }
                    ],
                },
                "promotion_allowed": False,
            }
            with (
                patch.object(agentrun, "verify_box_run", return_value=verified_box),
                patch.object(
                    agentrun,
                    "_load_profile_inputs",
                    return_value=(self._profile_inputs(), []),
                ),
                patch.object(
                    agentrun,
                    "_run_fixed_tool",
                    return_value=(tool_receipt, []),
                ),
                patch.dict(
                    "os.environ",
                    {
                        "CONSTRAINTBOX_RUNTIME_DIR": str(root / "runtime"),
                        "CONSTRAINTBOX_PROPOSAL_PROVIDER": "openrouter",
                    },
                    clear=True,
                ),
            ):
                result, code = agentrun.run_agent(box_dir, run_dir)

            self.assertEqual(code, agentrun.RUN_EXIT_CODES["PARKED"], result)
            self.assertEqual(result["disposition"], "PARKED")
            self.assertEqual(result["attempts"], [])
            policy = result["proposal_provider_policy"]
            self.assertEqual(
                policy["reason"], "registered_provider_route_unavailable"
            )
            self.assertIn("OPENROUTER_API_KEY", policy["error"])
            self.assertFalse((run_dir / "attempt-1").exists())


if __name__ == "__main__":
    unittest.main()
