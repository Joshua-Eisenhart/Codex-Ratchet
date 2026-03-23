from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

BASE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE / "tools"))

from a1_external_memo_batch_driver import _compact_timeline_row
from a1_exchange_serial_runner import main as serial_main
from a1_entropy_engine_campaign_runner import _with_selector_warning_snapshot as _campaign_with_selector_warning_snapshot
from a1_selector_warning_snapshot import (
    build_selector_provenance_fields,
    build_selector_warning_snapshot,
    extract_selector_provenance_fields,
    selector_stop_summary,
)
from run_a1_consolidation_prepack_job import _with_selector_warning_snapshot as _prepack_with_selector_warning_snapshot


SUPPORT_WARNING = (
    "noncanon mining witnesses are present; keep them support-side and do not treat them as executable head authority"
)
PROVENANCE_WARNING = "selector used external cold-core path; run-local regeneration provenance is bypassed"
SCOPE_WARNING = (
    "target scope clamp is narrower than family role context; use target_terms for local selection and admissibility for surrounding family context"
)


class TestA1ExchangeWarningCompaction(unittest.TestCase):
    def test_shared_provenance_builder_supports_plain_cold_core_payloads(self) -> None:
        fields = build_selector_provenance_fields(
            cold_core_path="/tmp/cold.json",
            cold_core_source="explicit_arg",
            cold_core_path_class="transient_store",
            cold_core_sha256="abc123",
            cold_core_sequence=7,
            cold_core_sequence_mismatch_stage="selector",
            selector_prefixed=False,
        )

        self.assertEqual("/tmp/cold.json", fields["cold_core_path"])
        self.assertEqual("explicit_arg", fields["cold_core_source"])
        self.assertEqual("transient_store", fields["cold_core_path_class"])
        self.assertEqual("abc123", fields["cold_core_sha256"])
        self.assertEqual(7, fields["cold_core_sequence"])
        self.assertEqual("selector", fields["cold_core_sequence_mismatch_stage"])

    def test_shared_provenance_extractor_normalizes_selector_cold_core_fields(self) -> None:
        fields = extract_selector_provenance_fields(
            {
                "cold_core_path": "/tmp/cold.json",
                "cold_core_source": "explicit_arg",
                "cold_core_path_class": "transient_store",
                "cold_core_sha256": "abc123",
                "cold_core_sequence": 7,
                "cold_core_sequence_mismatch_stage": "selector",
            }
        )

        self.assertEqual("/tmp/cold.json", fields["selector_cold_core_path"])
        self.assertEqual("explicit_arg", fields["selector_cold_core_source"])
        self.assertEqual("transient_store", fields["selector_cold_core_path_class"])
        self.assertEqual("abc123", fields["selector_cold_core_sha256"])
        self.assertEqual(7, fields["selector_cold_core_sequence"])
        self.assertEqual("selector", fields["cold_core_sequence_mismatch_stage"])

    def test_shared_snapshot_prioritizes_structured_categories_over_message_text(self) -> None:
        support_message = "support warning phrasing drifted"
        provenance_message = "provenance warning phrasing drifted"

        snapshot = build_selector_warning_snapshot(
            [support_message, provenance_message],
            warning_codes=["noncanon_mining_support_only", "external_cold_core_path"],
            warning_categories=["support_boundary", "cold_core_provenance"],
        )

        self.assertEqual(provenance_message, snapshot["selector_warning_summary"])
        self.assertTrue(snapshot["selector_support_warning_present"])

    def test_selector_stop_summary_uses_structured_warning_priority(self) -> None:
        support_message = "support warning phrasing drifted"
        sequence_message = "sequence mismatch phrasing drifted"

        summary = selector_stop_summary(
            {
                "selector_process_warnings": [support_message, sequence_message],
                "selector_warning_codes": [
                    "noncanon_mining_support_only",
                    "pack_selector_reported_sequence_mismatch",
                ],
                "selector_warning_categories": [
                    "support_boundary",
                    "cold_core_sequence",
                ],
            }
        )

        self.assertEqual(sequence_message, summary)

    def test_prepack_result_emits_structured_selector_warning_fields(self) -> None:
        payload = _prepack_with_selector_warning_snapshot(
            {
                "schema": "A1_CONSOLIDATION_PREPACK_RESULT_v1",
                "selector_process_warnings": [SUPPORT_WARNING, PROVENANCE_WARNING, SCOPE_WARNING],
                "selector_warning_codes": [
                    "noncanon_mining_support_only",
                    "external_cold_core_path",
                    "target_scope_family_context_split",
                ],
                "selector_warning_categories": [
                    "support_boundary",
                    "cold_core_provenance",
                    "scope_boundary",
                ],
            },
            [SUPPORT_WARNING, PROVENANCE_WARNING, SCOPE_WARNING],
        )

        self.assertEqual(3, payload["selector_warning_count"])
        self.assertEqual(
            [
                "noncanon_mining_support_only",
                "external_cold_core_path",
                "target_scope_family_context_split",
            ],
            payload["selector_warning_codes"],
        )
        self.assertEqual(
            ["support_boundary", "cold_core_provenance", "scope_boundary"],
            payload["selector_warning_categories"],
        )
        self.assertTrue(payload["selector_support_warning_present"])
        self.assertEqual(
            [SUPPORT_WARNING, PROVENANCE_WARNING, SCOPE_WARNING],
            payload["selector_warning_examples"],
        )
        self.assertEqual(PROVENANCE_WARNING, payload["selector_warning_summary"])

    def test_entropy_cycle_result_emits_structured_selector_warning_fields(self) -> None:
        payload = _campaign_with_selector_warning_snapshot(
            {
                "schema": "A1_ENTROPY_ENGINE_CYCLE_RESULT_v1",
                "selector_process_warnings": [SUPPORT_WARNING, PROVENANCE_WARNING],
                "selector_warning_codes": ["noncanon_mining_support_only", "external_cold_core_path"],
                "selector_warning_categories": ["support_boundary", "cold_core_provenance"],
            },
            [SUPPORT_WARNING, PROVENANCE_WARNING],
        )

        self.assertEqual(2, payload["selector_warning_count"])
        self.assertEqual(
            ["noncanon_mining_support_only", "external_cold_core_path"],
            payload["selector_warning_codes"],
        )
        self.assertEqual(
            ["support_boundary", "cold_core_provenance"],
            payload["selector_warning_categories"],
        )
        self.assertTrue(payload["selector_support_warning_present"])
        self.assertEqual([SUPPORT_WARNING, PROVENANCE_WARNING], payload["selector_warning_examples"])
        self.assertEqual(PROVENANCE_WARNING, payload["selector_warning_summary"])

    def test_driver_compact_timeline_keeps_warning_structure(self) -> None:
        compact = _compact_timeline_row(
            {
                "sequence": 4,
                "status": "WAITING_FOR_MEMOS",
                "selector_process_warnings": [
                    SUPPORT_WARNING,
                    PROVENANCE_WARNING,
                    SCOPE_WARNING,
                ],
                "selector_warning_codes": [
                    "noncanon_mining_support_only",
                    "external_cold_core_path",
                    "target_scope_family_context_split",
                ],
                "selector_warning_categories": [
                    "support_boundary",
                    "cold_core_provenance",
                    "scope_boundary",
                ],
            }
        )

        self.assertNotIn("selector_process_warnings", compact)
        self.assertEqual(3, compact["selector_warning_count"])
        self.assertEqual(
            [
                "noncanon_mining_support_only",
                "external_cold_core_path",
                "target_scope_family_context_split",
            ],
            compact["selector_warning_codes"],
        )
        self.assertEqual(
            ["support_boundary", "cold_core_provenance", "scope_boundary"],
            compact["selector_warning_categories"],
        )
        self.assertTrue(compact["selector_support_warning_present"])
        self.assertEqual(
            [SUPPORT_WARNING, PROVENANCE_WARNING, SCOPE_WARNING],
            compact["selector_warning_examples"],
        )
        self.assertEqual(PROVENANCE_WARNING, compact["selector_warning_summary"])

    def test_serial_runner_report_preserves_compacted_selector_warning_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_root = Path(tmpdir) / "runs"
            run_dir = runs_root / "RUN_WARNING_COMPACTION_001"
            (run_dir / "reports").mkdir(parents=True, exist_ok=True)

            fake_report = {
                "timeline": [
                    {
                        "status": "STOPPED",
                        "sequence": 7,
                        "process_phase": "path_build",
                        "run_stop_reason": "STOPPED__PACK_SELECTOR_FAILED",
                        "first_failure_sequence": 7,
                        "first_failure_surface": "exchange_prepack",
                        "first_failure_summary": "",
                        "selector_warning_count": 3,
                        "selector_warning_codes": [
                            "noncanon_mining_support_only",
                            "external_cold_core_path",
                        ],
                        "selector_warning_categories": [
                            "support_boundary",
                            "cold_core_provenance",
                        ],
                        "selector_support_warning_present": True,
                        "selector_warning_examples": [SUPPORT_WARNING, PROVENANCE_WARNING],
                        "selector_warning_summary": PROVENANCE_WARNING,
                    }
                ],
                "executed_cycles": 0,
            }

            with mock.patch("a1_exchange_serial_runner._run_driver", return_value=Path("")), mock.patch(
                "a1_exchange_serial_runner._load_latest_report",
                return_value=fake_report,
            ):
                rc = serial_main(
                    [
                        "--run-id",
                        "RUN_WARNING_COMPACTION_001",
                        "--steps",
                        "1",
                        "--runs-root",
                        str(runs_root),
                    ]
                )

            self.assertEqual(0, rc)
            report = json.loads((run_dir / "reports" / "a1_exchange_serial_runner_report.json").read_text(encoding="utf-8"))
            self.assertEqual(3, report["last_selector_warning_count"])
            self.assertEqual(
                ["noncanon_mining_support_only", "external_cold_core_path"],
                report["last_selector_warning_codes"],
            )
            self.assertEqual(
                ["support_boundary", "cold_core_provenance"],
                report["last_selector_warning_categories"],
            )
            self.assertTrue(report["last_selector_support_warning_present"])
            self.assertEqual([SUPPORT_WARNING, PROVENANCE_WARNING], report["last_selector_warning_examples"])
            self.assertEqual(PROVENANCE_WARNING, report["last_first_failure_summary"])
            self.assertEqual(3, report["timeline"][0]["selector_warning_count"])
            self.assertEqual(
                ["noncanon_mining_support_only", "external_cold_core_path"],
                report["timeline"][0]["selector_warning_codes"],
            )
            self.assertEqual(
                ["support_boundary", "cold_core_provenance"],
                report["timeline"][0]["selector_warning_categories"],
            )
            self.assertTrue(report["timeline"][0]["selector_support_warning_present"])
            self.assertEqual([SUPPORT_WARNING, PROVENANCE_WARNING], report["timeline"][0]["selector_warning_examples"])


if __name__ == "__main__":
    unittest.main()
