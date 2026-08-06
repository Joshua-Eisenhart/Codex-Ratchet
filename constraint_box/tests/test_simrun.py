from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from constraintbox import cli, simrun


INTERPRETER = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


class SimRunTests(unittest.TestCase):
    def invoke(
        self,
        sim_path: Path,
        receipt_path: Path,
        *,
        timeout: float = 5.0,
        interpreter: Path | str = INTERPRETER,
    ) -> tuple[int, dict, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        arguments = [
            "constraintbox",
            "sim",
            "run",
            str(sim_path),
            "--receipt",
            str(receipt_path),
            "--timeout",
            str(timeout),
            "--python",
            str(interpreter),
        ]
        exit_code = 0
        with (
            patch.object(sys, "argv", arguments),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            try:
                cli.main()
            except SystemExit as exc:
                exit_code = int(exc.code)
        return exit_code, json.loads(stdout.getvalue()), stderr.getvalue()

    def test_clean_sim_exit_zero_and_source_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "clean.py"
            receipt_path = root / "receipt.json"
            sim.write_text('print("clean")\n', encoding="utf-8")

            exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 0)
            self.assertTrue(receipt_path.is_file())
            self.assertEqual(
                receipt["sim_sha256"],
                hashlib.sha256(sim.read_bytes()).hexdigest(),
            )
            self.assertEqual(receipt["exit_code"], 0)
            self.assertFalse(receipt["timed_out"])

    def test_failing_sim_returns_one_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "fail.py"
            receipt_path = root / "receipt.json"
            sim.write_text("raise SystemExit(7)\n", encoding="utf-8")

            exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 1)
            self.assertTrue(receipt_path.is_file())
            self.assertEqual(receipt["exit_code"], 7)
            self.assertFalse(receipt["timed_out"])

    def test_timeout_returns_three_and_writes_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "timeout.py"
            receipt_path = root / "receipt.json"
            sim.write_text("import time\ntime.sleep(10)\n", encoding="utf-8")

            exit_code, receipt, _stderr = self.invoke(
                sim,
                receipt_path,
                timeout=0.05,
            )

            self.assertEqual(exit_code, 3)
            self.assertTrue(receipt_path.is_file())
            self.assertIsNone(receipt["exit_code"])
            self.assertTrue(receipt["timed_out"])
            self.assertEqual(receipt["timeout_seconds"], 0.05)

    def test_created_artifact_has_correct_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "create.py"
            receipt_path = root / "receipt.json"
            artifact = root / "artifact.json"
            sim.write_text(
                "from pathlib import Path\n"
                "Path('artifact.json').write_bytes(b'{\"value\": 7}\\n')\n",
                encoding="utf-8",
            )

            exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 0)
            created = next(
                row
                for row in receipt["artifacts"]["created"]
                if row["path"].endswith("artifact.json")
            )
            self.assertIsNone(created["sha256_before"])
            self.assertEqual(
                created["sha256_after"],
                hashlib.sha256(artifact.read_bytes()).hexdigest(),
            )

    def test_overwritten_artifact_marks_replay_unstable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "overwrite.py"
            receipt_path = root / "receipt.json"
            artifact = root / "artifact.txt"
            artifact.write_text("before\n", encoding="utf-8")
            before_digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
            sim.write_text(
                "from pathlib import Path\n"
                "Path('artifact.txt').write_text('after\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )

            exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 0)
            overwritten = next(
                row
                for row in receipt["artifacts"]["overwritten"]
                if row["path"].endswith("artifact.txt")
            )
            self.assertEqual(overwritten["sha256_before"], before_digest)
            self.assertEqual(
                overwritten["sha256_after"],
                hashlib.sha256(artifact.read_bytes()).hexdigest(),
            )
            self.assertFalse(receipt["replay_stable"])

    def test_identical_rewrite_is_reported_and_replay_unstable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "rewrite_identical.py"
            receipt_path = root / "receipt.json"
            artifact = root / "artifact.txt"
            artifact.write_bytes(b"identical\n")
            older_mtime_ns = artifact.stat().st_mtime_ns - 10_000_000_000
            os.utime(artifact, ns=(older_mtime_ns, older_mtime_ns))
            mtime_ns_before = artifact.stat().st_mtime_ns
            sha256_before = hashlib.sha256(artifact.read_bytes()).hexdigest()
            sim.write_text(
                "from pathlib import Path\n"
                "Path('artifact.txt').write_bytes(b'identical\\n')\n",
                encoding="utf-8",
            )

            exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 0)
            rewritten = next(
                row
                for row in receipt["artifacts"]["rewritten_identical"]
                if row["path"].endswith("artifact.txt")
            )
            sha256_after = hashlib.sha256(artifact.read_bytes()).hexdigest()
            self.assertEqual(rewritten["sha256"], sha256_before)
            self.assertEqual(sha256_before, sha256_after)
            self.assertEqual(rewritten["mtime_ns_before"], mtime_ns_before)
            self.assertGreater(
                rewritten["mtime_ns_after"],
                rewritten["mtime_ns_before"],
            )
            self.assertFalse(receipt["replay_stable"])
            self.assertEqual(
                receipt["replay_stable_reason"],
                "rewritten with identical bytes",
            )
            created_paths = {
                row["path"] for row in receipt["artifacts"]["created"]
            }
            overwritten_paths = {
                row["path"] for row in receipt["artifacts"]["overwritten"]
            }
            self.assertNotIn(rewritten["path"], created_paths)
            self.assertNotIn(rewritten["path"], overwritten_paths)

    def test_no_writes_observed_is_replay_stable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "no_writes.py"
            receipt_path = root / "receipt.json"
            sim.write_text("pass\n", encoding="utf-8")

            exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 0)
            self.assertTrue(receipt["replay_stable"])
            self.assertEqual(
                receipt["replay_stable_reason"],
                "no writes observed",
            )
            self.assertEqual(
                receipt["artifacts"]["rewritten_identical"],
                [],
            )

    def test_sim_cannot_select_controller_claim_kind(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            sim_directory = root / "system_v8" / "probe"
            sim_directory.mkdir(parents=True)
            sim = sim_directory / "assert_kind.py"
            receipt_path = root / "receipt.json"
            sim.write_text(
                "import json\n"
                "print(json.dumps({'claim_kind': 'field_only'}))\n",
                encoding="utf-8",
            )

            with patch.object(simrun, "REPO_ROOT", root):
                exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 0)
            self.assertEqual(receipt["claim_kind"], "manifold_sim")
            self.assertEqual(receipt["claim_kind_rule"], "system_v8/")
            self.assertEqual(
                receipt["claim_kind_source"],
                "constraintbox.simrun policy table",
            )
            self.assertEqual(
                receipt["sim_asserted_claim_kind"],
                "field_only",
            )
            self.assertTrue(receipt["claim_kind_conflict"])

    def test_stderr_last_line_has_real_exception_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "exception.py"
            receipt_path = root / "receipt.json"
            sim.write_text(
                "raise RuntimeError('real exception text')\n",
                encoding="utf-8",
            )

            exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 1)
            self.assertEqual(
                receipt["stderr_first_line"],
                "Traceback (most recent call last):",
            )
            self.assertEqual(
                receipt["stderr_last_line"],
                "RuntimeError: real exception text",
            )

    def test_symlink_interpreter_preserves_invoked_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "clean.py"
            receipt_path = root / "receipt.json"
            interpreter = root / "python-symlink"
            interpreter_realpath = Path(INTERPRETER).resolve()
            interpreter.symlink_to(interpreter_realpath)
            sim.write_text("pass\n", encoding="utf-8")

            exit_code, receipt, _stderr = self.invoke(
                sim,
                receipt_path,
                interpreter=interpreter,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(receipt["interpreter"], str(interpreter))
            self.assertEqual(
                receipt["interpreter_requested"],
                str(interpreter),
            )
            self.assertEqual(
                receipt["interpreter_realpath"],
                str(interpreter_realpath),
            )
            self.assertEqual(receipt["command"][0], receipt["interpreter"])

    def test_interpreter_environment_fields_are_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sim = root / "clean.py"
            receipt_path = root / "receipt.json"
            sim.write_text("pass\n", encoding="utf-8")

            exit_code, receipt, _stderr = self.invoke(sim, receipt_path)

            self.assertEqual(exit_code, 0)
            prefix = receipt["interpreter_prefix"]
            base_prefix = receipt["interpreter_base_prefix"]
            self.assertIsInstance(prefix, str)
            self.assertTrue(prefix)
            self.assertIsInstance(base_prefix, str)
            self.assertTrue(base_prefix)
            self.assertEqual(
                receipt["interpreter_is_venv"],
                prefix != base_prefix,
            )


if __name__ == "__main__":
    unittest.main()
