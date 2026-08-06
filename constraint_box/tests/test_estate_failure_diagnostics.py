from __future__ import annotations

import hashlib
import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path

import constraintbox.estate as estate_module
from constraintbox.estate import CapabilityState, EstateRunner

# Must match STREAM_CAPTURE_BYTE_BUDGET in estate.py. Kept local so this module
# still imports against an unmodified estate.py (where the constant is absent)
# and fails on assertions rather than on import.
STREAM_CAPTURE_BYTE_BUDGET = 8192


PACK_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_ROOT = PACK_ROOT.parent / "external_sim_estate" / "legacy_estate_v2"
WORKER = EXTERNAL_ROOT / "workers" / "capability_worker.py"
BLOCKER = EXTERNAL_ROOT / "workers" / "import_blocker.py"
FIXTURE = EXTERNAL_ROOT / "fixtures" / "manifold_fixture_v1.json"

# Distinctive marker that must appear in retained stderr after a forced failure.
FAIL_MARKER = "CONSTRAINTBOX_ESTATE_DIAG_MARKER_7f3a9c2e"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EstateFailureDiagnosticsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def manifest(self) -> Path:
        path = self.root / "estate.json"
        body = {
            "schema": "constraintbox.sim-estate.v1",
            "status": "PROPOSED",
            "promotion_allowed": False,
            "python": "3.11",
            "controller_sha256": digest(Path(estate_module.__file__)),
            "worker_sha256": digest(WORKER),
            "import_blocker_sha256": digest(BLOCKER),
            "tiers": [
                {
                    "tier_id": "S1",
                    "name": "test-finite",
                    "boot_budget_seconds": 10,
                    "capabilities": [
                        {
                            "id": "stdlib_finite",
                            "required": True,
                            "locked_version": "builtin",
                        }
                    ],
                }
            ],
        }
        path.write_text(json.dumps(body), encoding="utf-8")
        return path

    def _write_failing_python(self, script_body: str) -> Path:
        """Install a stand-in interpreter that emits controlled stderr and exits 1."""
        path = self.root / "fake-python"
        path.write_text(script_body, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return path

    def test_failed_capability_retains_readable_stderr_text(self) -> None:
        fake_python = self._write_failing_python(
            "#!/bin/sh\n"
            f'printf "%s\\n" "{FAIL_MARKER}: positive witness refused" >&2\n'
            "exit 1\n"
        )
        runner = EstateRunner(
            PACK_ROOT,
            self.manifest(),
            FIXTURE,
            fake_python,
        )
        receipt = runner.run_capability(
            {
                "id": "stdlib_finite",
                "required": True,
                "locked_version": "builtin",
            },
            "boot",
            10.0,
        )
        self.assertEqual(receipt.state, CapabilityState.FAILED)
        self.assertEqual(receipt.reason, "positive_witness_failed")
        stderr_text = receipt.evidence.get("stderr")
        self.assertIsInstance(
            stderr_text,
            str,
            msg=(
                "failure receipt must retain readable stderr text, not only a "
                f"digest; evidence keys were {sorted(receipt.evidence)}"
            ),
        )
        self.assertIn(
            FAIL_MARKER,
            stderr_text,
            msg=(
                "failure receipt must retain readable stderr text explaining "
                f"the failure; evidence keys were {sorted(receipt.evidence)}"
            ),
        )
        # Digests remain and cover the full original streams.
        self.assertIn("stderr_sha256", receipt.evidence)
        self.assertIn("stdout_sha256", receipt.evidence)
        expected_digest = hashlib.sha256(
            f"{FAIL_MARKER}: positive witness refused\n".encode("utf-8")
        ).hexdigest()
        self.assertEqual(receipt.evidence["stderr_sha256"], expected_digest)

    def test_retained_stream_text_is_bounded_with_explicit_drop_marker(self) -> None:
        # Oversized payload: well above the module budget so truncation is forced.
        oversize = STREAM_CAPTURE_BYTE_BUDGET + 4096
        emitter = (
            "#!/bin/sh\n"
            f"exec {sys.executable} -c "
            f"\"import sys; sys.stderr.buffer.write(b'Z'*{oversize}); sys.exit(1)\"\n"
        )
        fake_python = self._write_failing_python(emitter)
        runner = EstateRunner(
            PACK_ROOT,
            self.manifest(),
            FIXTURE,
            fake_python,
        )
        receipt = runner.run_capability(
            {
                "id": "stdlib_finite",
                "required": True,
                "locked_version": "builtin",
            },
            "boot",
            10.0,
        )
        self.assertEqual(receipt.state, CapabilityState.FAILED)
        stderr_text = receipt.evidence.get("stderr")
        self.assertIsInstance(stderr_text, str)
        dropped = oversize - STREAM_CAPTURE_BYTE_BUDGET
        marker = f"...[truncated: {dropped} bytes dropped]"
        self.assertIn(
            marker,
            stderr_text,
            msg=f"truncation marker missing; got {stderr_text[-120:]!r}",
        )
        # Retained body before the marker must not exceed the byte budget.
        body, _sep, _tail = stderr_text.partition("\n...[truncated:")
        self.assertLessEqual(len(body.encode("utf-8")), STREAM_CAPTURE_BYTE_BUDGET)
        # Full-stream digest is preserved (hash of the untruncated payload).
        self.assertEqual(
            receipt.evidence["stderr_sha256"],
            hashlib.sha256(b"Z" * oversize).hexdigest(),
        )

    def test_ready_receipt_does_not_embed_stream_text(self) -> None:
        runner = EstateRunner(PACK_ROOT, self.manifest(), FIXTURE)
        receipt = runner.run_capability(
            {
                "id": "stdlib_finite",
                "required": True,
                "locked_version": "builtin",
            },
            "boot",
            10.0,
        )
        self.assertEqual(receipt.state, CapabilityState.READY)
        self.assertNotIn("stderr", receipt.evidence)
        self.assertNotIn("stdout", receipt.evidence)


if __name__ == "__main__":
    unittest.main()
