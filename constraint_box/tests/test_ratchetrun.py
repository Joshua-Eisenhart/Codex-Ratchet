from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

from constraintbox import cli, ratchetrun


MAIN_REASON = (
    "main() calls attach_supplemental_gate_verdicts for tick0, tick1 and junk_run"
)
MAIN_V2_REASON = (
    "main_v2() never calls attach_supplemental_gate_verdicts; the four "
    "supplemental gates do not run under --v2"
)
PINNED_NOTE = (
    "PYTHONHASHSEED=0 was pinned in the child environment. Byte-stability of "
    "the tick's result JSONs across runs is NOT established by this receipt: "
    "a single run cannot establish it, and unpinned reruns were previously "
    "observed to differ in partition digests and label ordering."
)
UNPINNED_NOTE = (
    "PYTHONHASHSEED was not pinned. The tick's result JSON digests are NOT "
    "stable across runs; unpinned reruns were observed to differ in partition "
    "digests and label ordering."
)


class RatchetRunTests(unittest.TestCase):
    def run_stub(
        self,
        root: Path,
        body: str,
        **kwargs,
    ) -> tuple[dict, int, Path, Path]:
        tick_path = root / "tick.py"
        results_dir = root / "results"
        tick_path.write_text(body, encoding="utf-8")
        receipt, exit_code = ratchetrun.run_ratchet_tick(
            tick_path=tick_path,
            results_dir=results_dir,
            interpreter=sys.executable,
            timeout_seconds=kwargs.pop("timeout_seconds", 5.0),
            **kwargs,
        )
        return receipt, exit_code, tick_path, results_dir

    def test_stub_exit_codes_and_missing_results_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt, exit_code, _tick, results = self.run_stub(
                root,
                "raise SystemExit(0)\n",
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(receipt["exit_code"], 0)
            self.assertFalse(results.exists())

        with tempfile.TemporaryDirectory() as directory:
            receipt, exit_code, _tick, _results = self.run_stub(
                Path(directory),
                "raise SystemExit(7)\n",
            )
            self.assertEqual(exit_code, 1)
            self.assertEqual(receipt["exit_code"], 7)

    def test_created_result_artifact_has_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            receipt, exit_code, _tick, results = self.run_stub(
                root,
                "from pathlib import Path\n"
                "path = Path('results/foo.json')\n"
                "path.parent.mkdir(parents=True, exist_ok=True)\n"
                "path.write_bytes(b'{\"value\": 7}\\n')\n",
            )
            artifact = results / "foo.json"

            self.assertEqual(exit_code, 0)
            created = next(
                row
                for row in receipt["artifacts"]["created"]
                if row["path"].endswith("results/foo.json")
            )
            self.assertIsNone(created["sha256_before"])
            self.assertEqual(
                created["sha256_after"],
                hashlib.sha256(artifact.read_bytes()).hexdigest(),
            )

    def test_overwritten_result_artifact_has_before_and_after_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            results = root / "results"
            results.mkdir()
            artifact = results / "foo.json"
            artifact.write_bytes(b'{"value": "before"}\n')
            before = hashlib.sha256(artifact.read_bytes()).hexdigest()

            receipt, exit_code, _tick, _results = self.run_stub(
                root,
                "from pathlib import Path\n"
                "Path('results/foo.json').write_bytes(b'{\"value\": \"after\"}\\n')\n",
            )

            self.assertEqual(exit_code, 0)
            overwritten = next(
                row
                for row in receipt["artifacts"]["overwritten"]
                if row["path"].endswith("results/foo.json")
            )
            self.assertEqual(overwritten["sha256_before"], before)
            self.assertEqual(
                overwritten["sha256_after"],
                hashlib.sha256(artifact.read_bytes()).hexdigest(),
            )

    def test_entry_path_and_supplemental_gate_reachability(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            main_receipt, exit_code, _tick, _results = self.run_stub(
                Path(directory),
                "pass\n",
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(main_receipt["entry_path"], "main")
        self.assertFalse(main_receipt["v2"])
        self.assertTrue(main_receipt["supplemental_gates_reachable"])
        self.assertEqual(
            main_receipt["supplemental_gates_reachable_reason"],
            MAIN_REASON,
        )

        with tempfile.TemporaryDirectory() as directory:
            v2_receipt, exit_code, _tick, _results = self.run_stub(
                Path(directory),
                "pass\n",
                v2=True,
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(v2_receipt["entry_path"], "main_v2")
        self.assertTrue(v2_receipt["v2"])
        self.assertFalse(v2_receipt["supplemental_gates_reachable"])
        self.assertEqual(
            v2_receipt["supplemental_gates_reachable_reason"],
            MAIN_V2_REASON,
        )

    def test_hashseed_is_pinned_only_in_child_and_stability_stays_unknown(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pinned, exit_code, _tick, _results = self.run_stub(
                Path(directory),
                "import os\nprint(os.environ.get('PYTHONHASHSEED'))\n",
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(pinned["stdout_first_line"], "0")
        self.assertEqual(
            pinned["determinism"],
            {
                "pythonhashseed_pinned": True,
                "pythonhashseed_value": "0",
                "artifact_digests_stable_across_runs": None,
                "note": PINNED_NOTE,
            },
        )

        with tempfile.TemporaryDirectory() as directory:
            unpinned, exit_code, _tick, _results = self.run_stub(
                Path(directory),
                "pass\n",
                pin_hashseed=False,
            )
        self.assertEqual(exit_code, 0)
        self.assertEqual(
            unpinned["determinism"],
            {
                "pythonhashseed_pinned": False,
                "pythonhashseed_value": None,
                "artifact_digests_stable_across_runs": None,
                "note": UNPINNED_NOTE,
            },
        )

    def test_tick_claim_kind_is_quarantined_and_verdict_fields_are_absent(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt, exit_code, _tick, _results = self.run_stub(
                Path(directory),
                "import json\n"
                "print(json.dumps({'claim_kind': 'manifold_sim'}))\n",
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(receipt["claim_kind"], "field_only")
        self.assertEqual(receipt["claim_kind_rule"], "default")
        self.assertEqual(receipt["sim_asserted_claim_kind"], "manifold_sim")
        self.assertTrue(receipt["claim_kind_conflict"])
        self.assertTrue(
            {
                "verdict",
                "ratchet_verdict",
                "frontier_moved",
                "anti_stall_control",
            }.isdisjoint(receipt)
        )

    def test_missing_tick_path_raises_runner_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ratchetrun.RatchetRunError):
                ratchetrun.run_ratchet_tick(
                    tick_path=Path(directory) / "missing.py",
                    interpreter=sys.executable,
                )

    def test_runner_timeout_returns_three(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            receipt, exit_code, _tick, _results = self.run_stub(
                Path(directory),
                "import time\ntime.sleep(10)\n",
                timeout_seconds=0.05,
            )

        self.assertEqual(exit_code, 3)
        self.assertIsNone(receipt["exit_code"])
        self.assertTrue(receipt["timed_out"])

    def test_default_tick_path_exists_and_is_a_file(self) -> None:
        self.assertTrue(ratchetrun.DEFAULT_TICK_PATH.exists())
        self.assertTrue(ratchetrun.DEFAULT_TICK_PATH.is_file())

    def test_cli_parses_ratchet_tick_without_clobbering_sim_run(self) -> None:
        parser = cli.build_parser()
        ratchet_args = parser.parse_args(
            [
                "ratchet",
                "tick",
                "--receipt",
                "/tmp/ratchet.json",
                "--v2",
                "--timeout",
                "4",
                "--python",
                sys.executable,
                "--no-pin-hashseed",
            ]
        )
        self.assertEqual(ratchet_args.command, "ratchet")
        self.assertEqual(ratchet_args.ratchet_command, "tick")
        self.assertTrue(ratchet_args.v2)
        self.assertTrue(ratchet_args.no_pin_hashseed)

        sim_args = parser.parse_args(["sim", "run", "/tmp/sim.py"])
        self.assertEqual(sim_args.command, "sim")
        self.assertEqual(sim_args.sim_command, "run")
        self.assertEqual(sim_args.sim_path, Path("/tmp/sim.py"))


if __name__ == "__main__":
    unittest.main()
