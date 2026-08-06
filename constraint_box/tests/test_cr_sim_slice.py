from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from constraintbox.cr_sim_slice import (
    CRSimSliceError,
    MANIFEST_SCHEMA,
    run_cr_sim_slice,
)


class CRSimSliceTests(unittest.TestCase):
    def _manifest(self, root: Path) -> Path:
        source = root / "fake_sim.py"
        result = root / "fake_result.json"
        source.write_text(
            "import json\n"
            f"json.dump({{'all_pass': True, 'promotion_allowed': False}}, open({str(result)!r}, 'w'))\n",
            encoding="utf-8",
        )
        fixture = root / "manifold_time_first_seed_v1.json"
        fixture.write_text(
            (Path(__file__).parents[1] / "fixtures" / "cr" / "manifold_time_first_seed_v1.json").read_text(
                encoding="utf-8"
            ),
            encoding="utf-8",
        )
        manifest = {
            "schema": MANIFEST_SCHEMA,
            "manifest_id": "test-cr-slice",
            "claim_ceiling": "test only",
            "foundation_fixture": fixture.name,
            "profiles": {"test": ["fake"]},
            "entries": [
                {
                    "id": "fake",
                    "group": "test",
                    "engine": "python",
                    "source": source.name,
                    "result": result.name,
                    "result_mode": "json_all_pass",
                    "reads_peer_result": False,
                    "integration_level": ["source_invocation", "receipt_capture", "controller_recheck"],
                }
            ],
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        return manifest_path

    def test_registered_source_runs_and_is_rechecked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt, exit_code = run_cr_sim_slice(
                profile="test",
                run_root=root / "run",
                cr_root=root,
                manifest_path=self._manifest(root),
                timeout_seconds=20,
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(receipt["status"], "PASS")
            self.assertEqual(receipt["entries"][0]["status"], "PASS")
            self.assertFalse(receipt["promotion_allowed"])
            self.assertEqual(receipt["entries"][0]["kernel_membership"], "EXTERNAL_NOT_CB_KERNEL")

    def test_path_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = self._manifest(root)
            body = json.loads(manifest.read_text(encoding="utf-8"))
            body["entries"][0]["source"] = "../outside.py"
            manifest.write_text(json.dumps(body), encoding="utf-8")
            with self.assertRaises(CRSimSliceError):
                run_cr_sim_slice(
                    profile="test",
                    run_root=root / "run",
                    cr_root=root,
                    manifest_path=manifest,
                )

    def test_fixture_hash_mismatch_is_rejected_by_controller(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "fake_sim.py"
            result = root / "fake_result.json"
            source.write_text(
                "import json\n"
                f"json.dump({{'all_pass': True, 'promotion_allowed': False, 'fixture_sha256': 'wrong'}}, open({str(result)!r}, 'w'))\n",
                encoding="utf-8",
            )
            fixture = root / "fixture.json"
            fixture.write_text('{"fixture": "present"}\n', encoding="utf-8")
            foundation = root / "manifold_time_first_seed_v1.json"
            foundation.write_text(
                (Path(__file__).parents[1] / "fixtures" / "cr" / "manifold_time_first_seed_v1.json").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )
            manifest = {
                "schema": MANIFEST_SCHEMA,
                "manifest_id": "test-fixture-hash",
                "claim_ceiling": "test only",
                "foundation_fixture": foundation.name,
                "profiles": {"test": ["fake"]},
                "entries": [
                    {
                        "id": "fake",
                        "group": "test",
                        "engine": "python",
                        "source": source.name,
                        "result": result.name,
                        "result_mode": "json_all_pass",
                        "reads_peer_result": False,
                        "fixture": fixture.name,
                        "integration_level": ["source_invocation", "shared_fixture_hash", "controller_recheck"],
                    }
                ],
            }
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            receipt, exit_code = run_cr_sim_slice(
                profile="test",
                run_root=root / "run",
                cr_root=root,
                manifest_path=manifest_path,
                timeout_seconds=20,
            )
            self.assertEqual(exit_code, 1)
            self.assertEqual(receipt["status"], "FAIL")
            self.assertEqual(receipt["entries"][0]["reason"], "fixture_hash_mismatch")


if __name__ == "__main__":
    unittest.main()
