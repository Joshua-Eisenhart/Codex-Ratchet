from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[3]
TOOLS = BASE / "tools"


class TestAuditA1CurrentQueueNoteAlignment(unittest.TestCase):
    def test_matching_note_and_packet_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            packet_json = tmp_path / "packet.json"
            note_text = tmp_path / "note.md"
            packet_json.write_text(
                json.dumps(
                    {
                        "schema": "A1_QUEUE_STATUS_PACKET_v1",
                        "queue_status": "NO_WORK",
                        "reason": "no bounded A1 family slice is currently prepared",
                    }
                ),
                encoding="utf-8",
            )
            note_text.write_text(
                "# Test\n\n```text\nA1_QUEUE_STATUS: NO_WORK\nreason: no bounded A1 family slice is currently prepared\n```\n",
                encoding="utf-8",
            )

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "audit_a1_current_queue_note_alignment.py"),
                    "--packet-json",
                    str(packet_json),
                    "--note-text",
                    str(note_text),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertTrue(payload["valid"])

    def test_missing_reason_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            packet_json = tmp_path / "packet.json"
            note_text = tmp_path / "note.md"
            packet_json.write_text(
                json.dumps(
                    {
                        "schema": "A1_QUEUE_STATUS_PACKET_v1",
                        "queue_status": "NO_WORK",
                        "reason": "no bounded A1 family slice is currently prepared",
                    }
                ),
                encoding="utf-8",
            )
            note_text.write_text("# Test\n\n```text\nA1_QUEUE_STATUS: NO_WORK\n```\n", encoding="utf-8")

            proc = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "audit_a1_current_queue_note_alignment.py"),
                    "--packet-json",
                    str(packet_json),
                    "--note-text",
                    str(note_text),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, proc.returncode)
            payload = json.loads(proc.stdout)
            self.assertIn("note_missing_reason", payload["errors"])


if __name__ == "__main__":
    unittest.main()
