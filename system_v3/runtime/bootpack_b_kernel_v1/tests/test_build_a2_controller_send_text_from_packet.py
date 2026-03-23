from __future__ import annotations

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"
sys.path.insert(0, str(TOOLS))

from build_a2_controller_send_text_from_packet import build_send_text  # noqa: E402


class TestBuildA2ControllerSendTextFromPacket(unittest.TestCase):
    def test_queue_helper_guidance_is_present_for_a1_queue_scope(self) -> None:
        packet = {
            "model": "GPT-5.4 Medium",
            "thread_class": "A2_CONTROLLER",
            "mode": "CONTROLLER_ONLY",
            "primary_corpus": str(BASE.parent / "core_docs" / "a1_refined_Ratchet Fuel"),
            "state_record": str(BASE / "a2_state" / "A2_CONTROLLER_STATE_RECORD__CURRENT__v1.md"),
            "current_primary_lane": "test primary lane",
            "current_a1_queue_status": "A1_QUEUE_STATUS: NO_WORK",
            "go_on_count": 0,
            "go_on_budget": 2,
            "stop_rule": "stop after one bounded controller action",
            "dispatch_rule": "dispatch bounded workers whenever possible",
            "initial_bounded_scope": "one bounded a1? queue answer",
        }

        send_text = build_send_text(packet)
        self.assertIn("You are a fresh A2 controller thread.", send_text)
        self.assertIn("build_a1_queue_status_packet.py", send_text)
        self.assertIn("validate_a1_queue_status_packet.py", send_text)


if __name__ == "__main__":
    unittest.main()
