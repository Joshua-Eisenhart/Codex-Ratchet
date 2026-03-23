from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

import run_real_loop  # noqa: E402


class TestRunRealLoop(unittest.TestCase):
    def test_dedicated_recovery_entrypoint_is_not_treated_as_compatibility_path(self) -> None:
        source = run_real_loop._effective_recovery_invocation_source(
            allow_reconstructed_artifacts=True,
            recovery_invocation_source="dedicated_recovery_entrypoint",
        )
        self.assertEqual("dedicated_recovery_entrypoint", source)
        self.assertEqual([], run_real_loop._compatibility_warnings(recovery_invocation_source=source))
        self.assertEqual(
            {
                "required": False,
                "decision": None,
                "reason": None,
            },
            run_real_loop._controller_review_metadata(recovery_invocation_source=source),
        )

    def test_extract_export_records_preserves_split_file_sequences(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir)
            outbox = run_dir / "outbox"
            outbox.mkdir(parents=True, exist_ok=True)
            (outbox / "export_blocks.000.txt").write_text(
                "\n".join(
                    [
                        "BEGIN EXPORT_RECORD 00000001",
                        "BEGIN EXPORT_BLOCK v1",
                        "TARGET: THREAD_B_ENFORCEMENT_KERNEL",
                        "END EXPORT_BLOCK v1",
                        "END EXPORT_RECORD 00000001",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (outbox / "export_block_0002.txt").write_text(
                "\n".join(
                    [
                        "BEGIN EXPORT_BLOCK v1",
                        "TARGET: THREAD_B_ENFORCEMENT_KERNEL",
                        "END EXPORT_BLOCK v1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            records = run_real_loop._extract_export_records(run_dir)

            self.assertEqual([1, 2], [int(row["seq"]) for row in records])
            self.assertEqual(
                str(outbox / "export_block_0002.txt"),
                str(records[1]["source_path"]),
            )

    def test_main_fails_closed_when_required_runtime_artifacts_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_repo_root = Path(tmpdir)
            fake_tool_path = fake_repo_root / "system_v3" / "tools" / "run_real_loop.py"
            fake_tool_path.parent.mkdir(parents=True, exist_ok=True)
            fake_tool_path.write_text("# stub\n", encoding="utf-8")

            run_id = "RUN_REAL_LOOP_STRICT_TEST"
            run_dir = fake_repo_root / "system_v3" / "runs" / run_id

            def fake_init_run_surface(
                target_run_dir: Path,
                repo_root: Path,
                bootpack_a_hash: str,
                bootpack_b_hash: str,
            ) -> None:
                del repo_root, bootpack_a_hash, bootpack_b_hash
                (target_run_dir / "reports").mkdir(parents=True, exist_ok=True)
                (target_run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
                (target_run_dir / "state.json").write_text("{}", encoding="utf-8")

            run_calls: list[list[str]] = []

            def fake_run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
                del cwd
                run_calls.append(cmd)
                return subprocess.CompletedProcess(cmd, 0, stdout="AUTORATCHET_OK", stderr="")

            stdout = io.StringIO()
            argv = ["run_real_loop.py", "--run-id", run_id]
            with (
                mock.patch.object(run_real_loop, "__file__", str(fake_tool_path)),
                mock.patch.object(run_real_loop, "_init_run_surface_if_needed", side_effect=fake_init_run_surface),
                mock.patch.object(run_real_loop, "_run", side_effect=fake_run),
                mock.patch.object(sys, "argv", argv),
                contextlib.redirect_stdout(stdout),
            ):
                rc = run_real_loop.main()

            payload = json.loads(stdout.getvalue().strip())
            self.assertEqual(2, rc)
            self.assertEqual("FAIL", payload["status"])
            self.assertEqual("MISSING_REQUIRED_RUNTIME_ARTIFACTS", payload["stage"])
            self.assertEqual(
                ["canonical_events", "graveyard_records"],
                payload["missing_required_runtime_artifacts"],
            )
            self.assertFalse(payload["allow_reconstructed_artifacts"])
            self.assertEqual(1, len(run_calls))
            self.assertIn("autoratchet.py", run_calls[0][1])
            self.assertEqual(run_id, run_dir.name)

    def test_main_enters_explicit_recovery_mode_when_reconstruction_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_repo_root = Path(tmpdir)
            fake_tool_path = fake_repo_root / "system_v3" / "tools" / "run_real_loop.py"
            fake_tool_path.parent.mkdir(parents=True, exist_ok=True)
            fake_tool_path.write_text("# stub\n", encoding="utf-8")

            run_id = "RUN_REAL_LOOP_RECOVERY_TEST"

            def fake_init_run_surface(
                target_run_dir: Path,
                repo_root: Path,
                bootpack_a_hash: str,
                bootpack_b_hash: str,
            ) -> None:
                del repo_root, bootpack_a_hash, bootpack_b_hash
                (target_run_dir / "reports").mkdir(parents=True, exist_ok=True)
                (target_run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
                (target_run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "graveyard": [
                                {
                                    "id": "ALT_01",
                                    "reason": "NEG_COLLAPSE",
                                    "item_text": "line_a\nline_b",
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )

            run_calls: list[list[str]] = []

            def fake_run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
                del cwd
                run_calls.append(cmd)
                return subprocess.CompletedProcess(cmd, 0, stdout="OK", stderr="")

            stdout = io.StringIO()
            argv = [
                "run_real_loop.py",
                "--run-id",
                run_id,
                "--allow-reconstructed-artifacts",
            ]
            with (
                mock.patch.object(run_real_loop, "__file__", str(fake_tool_path)),
                mock.patch.object(run_real_loop, "_init_run_surface_if_needed", side_effect=fake_init_run_surface),
                mock.patch.object(run_real_loop, "_run", side_effect=fake_run),
                mock.patch.object(sys, "argv", argv),
                contextlib.redirect_stdout(stdout),
            ):
                rc = run_real_loop.main()

            payload = json.loads(stdout.getvalue().strip())
            self.assertEqual(0, rc)
            self.assertEqual("PASS", payload["status"])
            self.assertTrue(payload["recovery_mode_active"])
            self.assertEqual(
                [
                    "events",
                    "export_reports",
                    "graveyard_records",
                    "tapes",
                ],
                payload["reconstructed_artifact_classes"],
            )
            self.assertEqual(
                "MISSING_CANONICAL_SIM_EVIDENCE",
                payload["evidence_summary"]["evidence_mode"],
            )
            self.assertEqual(["COMPATIBILITY_RECOVERY_PATH_USED"], payload["warnings"])
            self.assertEqual(
                "compatibility_flag",
                payload["recovery_invocation"]["recovery_invocation_mode"],
            )
            self.assertTrue(payload["recovery_invocation"]["compatibility_recovery_flag_used"])
            self.assertTrue(payload["controller_review_required"])
            self.assertEqual("MANUAL_REVIEW_REQUIRED", payload["controller_review_decision"])
            self.assertEqual(
                "compatibility_recovery_path_used",
                payload["controller_review_reason"],
            )
            self.assertTrue(
                str(payload["recovery_invocation"]["preferred_recovery_entrypoint"]).endswith(
                    "system_v3/tools/run_real_loop_recovery_cycle.py"
                )
            )
            self.assertEqual([], payload.get("missing_required_runtime_artifacts", []))
            self.assertEqual(3, len(run_calls))
            self.assertIn("autoratchet.py", run_calls[0][1])
            self.assertIn("run_phase_gate_pipeline.py", run_calls[1][1])
            self.assertIn("sprawl_guard.py", run_calls[2][1])

    def test_main_dedicated_recovery_entrypoint_does_not_emit_legacy_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_repo_root = Path(tmpdir)
            fake_tool_path = fake_repo_root / "system_v3" / "tools" / "run_real_loop.py"
            fake_tool_path.parent.mkdir(parents=True, exist_ok=True)
            fake_tool_path.write_text("# stub\n", encoding="utf-8")

            run_id = "RUN_REAL_LOOP_DEDICATED_RECOVERY_TEST"

            def fake_init_run_surface(
                target_run_dir: Path,
                repo_root: Path,
                bootpack_a_hash: str,
                bootpack_b_hash: str,
            ) -> None:
                del repo_root, bootpack_a_hash, bootpack_b_hash
                (target_run_dir / "reports").mkdir(parents=True, exist_ok=True)
                (target_run_dir / "zip_packets").mkdir(parents=True, exist_ok=True)
                (target_run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "graveyard": [
                                {
                                    "id": "ALT_01",
                                    "reason": "NEG_COLLAPSE",
                                    "item_text": "line_a\nline_b",
                                }
                            ]
                        }
                    ),
                    encoding="utf-8",
                )

            run_calls: list[list[str]] = []

            def fake_run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
                del cwd
                run_calls.append(cmd)
                return subprocess.CompletedProcess(cmd, 0, stdout="OK", stderr="")

            stdout = io.StringIO()
            argv = [
                "run_real_loop.py",
                "--run-id",
                run_id,
                "--allow-reconstructed-artifacts",
                "--recovery-invocation-source",
                "dedicated_recovery_entrypoint",
            ]
            with (
                mock.patch.object(run_real_loop, "__file__", str(fake_tool_path)),
                mock.patch.object(run_real_loop, "_init_run_surface_if_needed", side_effect=fake_init_run_surface),
                mock.patch.object(run_real_loop, "_run", side_effect=fake_run),
                mock.patch.object(sys, "argv", argv),
                contextlib.redirect_stdout(stdout),
            ):
                rc = run_real_loop.main()

            payload = json.loads(stdout.getvalue().strip())
            self.assertEqual(0, rc)
            self.assertEqual("PASS", payload["status"])
            self.assertTrue(payload["recovery_mode_active"])
            self.assertEqual([], payload["warnings"])
            self.assertEqual(
                "dedicated_recovery_entrypoint",
                payload["recovery_invocation"]["recovery_invocation_mode"],
            )
            self.assertFalse(payload["recovery_invocation"]["compatibility_recovery_flag_used"])
            self.assertFalse(payload["controller_review_required"])
            self.assertIsNone(payload["controller_review_decision"])
            self.assertIsNone(payload["controller_review_reason"])
            self.assertEqual(3, len(run_calls))
            self.assertIn("autoratchet.py", run_calls[0][1])
            self.assertIn("run_phase_gate_pipeline.py", run_calls[1][1])
            self.assertIn("sprawl_guard.py", run_calls[2][1])


if __name__ == "__main__":
    unittest.main()
