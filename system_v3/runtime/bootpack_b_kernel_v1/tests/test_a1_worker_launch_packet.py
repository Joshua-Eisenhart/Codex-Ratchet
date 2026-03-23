from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

from build_a1_worker_launch_handoff import build_handoff  # noqa: E402
from build_a1_worker_send_text_from_packet import build_send_text  # noqa: E402
from run_a1_worker_launch_from_packet import build_result  # noqa: E402
from validate_a1_worker_launch_packet import validate as validate_packet  # noqa: E402
from validate_codex_thread_launch_handoff import validate as validate_handoff  # noqa: E402


class TestA1WorkerLaunchPacket(unittest.TestCase):
    def test_launch_packet_supports_a1_reload_artifacts_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_a2_artifact = tmp_path / "A2_UPDATE_NOTE__TEST.md"
            source_a2_artifact.write_text("bounded a2 fuel\n", encoding="utf-8")
            packet_json = tmp_path / "packet.json"
            send_text_path = tmp_path / "send_text.md"

            required_a1_boot = BASE / "specs" / "31_A1_THREAD_BOOT__v1.md"
            live_reload = BASE / "specs" / "77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md"
            historical_reload = BASE / "specs" / "78_A1_HISTORICAL_BRANCH_WIGGLE_EXTRACT__v1.md"
            stop_rule = "Stop after one bounded proposal pass."
            prompt = "\n".join(
                [
                    "Use the current A1 boot:",
                    f"- {required_a1_boot}",
                    "Read these A1 reload artifacts before acting:",
                    f"- {live_reload}",
                    f"- {historical_reload}",
                    "Use only these artifacts:",
                    f"- {source_a2_artifact}",
                    "Run one bounded A1_PROPOSAL pass only.",
                    f"stop_rule: {stop_rule}",
                ]
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "create_a1_worker_launch_packet.py"),
                    "--model",
                    "GPT-5.4 Medium",
                    "--queue-status",
                    "READY_FROM_NEW_A2_HANDOFF",
                    "--dispatch-id",
                    "A1_DISPATCH__TEST__v1",
                    "--target-a1-role",
                    "A1_PROPOSAL",
                    "--required-a1-boot",
                    str(required_a1_boot),
                    "--source-a2-artifact",
                    str(source_a2_artifact),
                    "--a1-reload-artifact",
                    str(live_reload),
                    "--a1-reload-artifact",
                    str(historical_reload),
                    "--bounded-scope",
                    "One bounded A1 proposal pass.",
                    "--prompt-to-send",
                    prompt,
                    "--stop-rule",
                    stop_rule,
                    "--go-on-count",
                    "0",
                    "--go-on-budget",
                    "1",
                    "--out-json",
                    str(packet_json),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)

            packet = json.loads(packet_json.read_text(encoding="utf-8"))
            self.assertEqual(
                [str(live_reload), str(historical_reload)],
                packet["a1_reload_artifacts"],
            )

            validation = validate_packet(packet)
            self.assertTrue(validation["valid"], validation["errors"])

            gate_result = build_result(packet, validation)
            self.assertEqual("LAUNCH_READY", gate_result["status"])
            self.assertEqual(
                [str(live_reload), str(historical_reload)],
                gate_result["a1_reload_artifacts"],
            )

            send_text = build_send_text(packet)
            send_text_path.write_text(send_text, encoding="utf-8")
            self.assertIn("a1_reload_artifacts:", send_text)
            self.assertIn(str(live_reload), send_text)
            self.assertIn(str(historical_reload), send_text)

            handoff = build_handoff(packet_json, packet, send_text_path)
            self.assertEqual(
                [str(live_reload), str(historical_reload)],
                handoff["a1_reload_artifacts"],
            )
            handoff_validation = validate_handoff(handoff)
            self.assertTrue(handoff_validation["valid"], handoff_validation["errors"])

    def test_launch_packet_without_reload_artifacts_remains_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            source_a2_artifact = tmp_path / "A2_UPDATE_NOTE__TEST.md"
            source_a2_artifact.write_text("bounded a2 fuel\n", encoding="utf-8")
            required_a1_boot = BASE / "specs" / "31_A1_THREAD_BOOT__v1.md"
            stop_rule = "Stop after one bounded proposal pass."

            packet = {
                "schema": "A1_WORKER_LAUNCH_PACKET_v1",
                "model": "GPT-5.4 Medium",
                "thread_class": "A1_WORKER",
                "mode": "PROPOSAL_ONLY",
                "queue_status": "READY_FROM_NEW_A2_HANDOFF",
                "dispatch_id": "A1_DISPATCH__TEST__v1",
                "target_a1_role": "A1_PROPOSAL",
                "required_a1_boot": str(required_a1_boot),
                "source_a2_artifacts": [str(source_a2_artifact)],
                "bounded_scope": "One bounded A1 proposal pass.",
                "prompt_to_send": "\n".join(
                    [
                        "Use the current A1 boot:",
                        f"- {required_a1_boot}",
                        "Use only these artifacts:",
                        f"- {source_a2_artifact}",
                        "Run one bounded A1_PROPOSAL pass only.",
                        f"stop_rule: {stop_rule}",
                    ]
                ),
                "stop_rule": stop_rule,
                "go_on_count": 0,
                "go_on_budget": 1,
            }

            validation = validate_packet(packet)
            self.assertTrue(validation["valid"], validation["errors"])

            send_text = build_send_text(packet)
            self.assertNotIn("a1_reload_artifacts:", send_text)


if __name__ == "__main__":
    unittest.main()
