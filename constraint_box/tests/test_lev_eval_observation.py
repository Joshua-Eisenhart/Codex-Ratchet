from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from constraintbox.lev_eval_observation import (
    LevEvalObservationError,
    LevEvalObservationHoldError,
    build_lev_eval_observation_binding,
    observe_lev_eval_bundle,
    verify_lev_eval_observation_snapshot,
)
from constraintbox.intake import canonical_json


def js_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(js_bytes(value)).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def build_current_lev_bundle(root: Path) -> dict[str, object]:
    """Create the exact five-artifact shape emitted by the current Lev writer."""

    root.mkdir(parents=True)
    execution_id = "cb-observe-fixture-v1"
    suite_id = "constraintbox-foreign-eval-fixture"
    decided_at = "2026-07-30T06:13:15.818Z"
    evidence_refs = [
        {
            "kind": "suite",
            "label": "suite",
            "path": "plugins/sim-witness/evals/fixture.eval.js",
            "exists": True,
        },
        {
            "kind": "target",
            "label": "target",
            "path": "plugins/sim-witness/evals/sensor.mjs",
            "exists": True,
        },
        {
            "kind": "flowmind",
            "label": "flowmind",
            "path": "plugins/sim-witness/evals/flow.yaml",
            "exists": True,
        },
        {
            "kind": "fixture",
            "label": "trace",
            "path": "plugins/sim-witness/evals/trace.json",
            "exists": True,
        },
    ]
    diagnostics: list[object] = []
    decision_id = "decision:" + execution_id + ":" + hashlib.sha256(
        suite_id.encode("utf-8")
    ).hexdigest()[:16]
    input_digests = {
        "trace_cases_digest": "a" * 64,
        "command_cases_digest": "b" * 64,
        "diagnostics_digest": digest(diagnostics),
        "evidence_refs_digest": digest(evidence_refs),
    }
    decision = {
        "schema": "lev.eval_decision.v1",
        "decision_id": decision_id,
        "execution_id": execution_id,
        "suite_id": suite_id,
        "input_digests": input_digests,
        "decided_at": decided_at,
        "status": "decided",
        "verdict": "pass",
        "reason_code": "all_cases_passed",
    }
    case_id = "trace-fixture"
    measurement_id = "measurement:eval_suite_runner:" + execution_id + ":trace:" + digest(case_id)[:16]
    measurement = {
        "schema": "lev.measurement.v1",
        "measurement_id": measurement_id,
        "evaluator_id": "eval_suite_runner",
        "evaluator_version": "1",
        "subject_ref": "eval-suite:" + suite_id,
        "generation": 1,
        "variables": {
            "case_id": {"value": case_id, "confidence": 1, "evidence_count": 1},
            "case_kind": {"value": "trace", "confidence": 1, "evidence_count": 1},
            "case_status": {"value": "passed", "confidence": 1, "evidence_count": 1},
            "passed": {"value": True, "confidence": 1, "evidence_count": 1},
            "diagnostic_count": {"value": 0, "confidence": 1, "evidence_count": 1},
        },
        "provenance": "runtime_fact",
        "evidence_refs": [
            {"kind": "measurement", "ref": measurement_id, "exists": True}
        ],
        "status": "measured",
        "measured_at": decided_at,
    }
    projection = {
        "schema": "lev.telemetry.measurement_series_projection.v1",
        "projection_name": "MeasurementSeries",
        "projection_ref": None,
        "deferred": True,
        "reason": "measurement_stream_not_materialized",
        "measurements": [],
        "forward_obligation": {
            "owner_package": "core/execution-ledger",
            "missing_contract": "append_only_measurement_stream_read_contract",
            "required_shape": "materialized Measurement stream reader over ledger Measurement facts",
        },
    }
    run = {
        "execution_id": execution_id,
        "status": "passed",
        "suite_id": suite_id,
        "suite_path": "plugins/sim-witness/evals/fixture.eval.js",
        "output_root": str(root.parent),
        "run_dir": str(root),
        "decision_ref": str(root / "decision.json"),
        "measurements_ref": str(root / "measurements.jsonl"),
        "measurement_series_ref": str(root / "measurement-series" / "projection.json"),
        "diagnostics": diagnostics,
        "evidence_refs": evidence_refs,
    }
    seal = {
        "schema": "lev.run_seal.v1",
        "execution_id": execution_id,
        "intent_ref": {
            "uri": "eval-decision:" + decision_id,
            "adapter": "core/eval",
            "content_hash": digest(input_digests),
        },
        "sealed_at": decided_at,
        "action_ids": [],
        "outcome": "dry_run_success",
        "obligations": [
            {
                "obligation_id": suite_id,
                "declared_at": decided_at,
                "verdict_ref": decision_id,
            }
        ],
        "verdict_refs": [decision_id],
        "evidence_refs": [
            {"kind": "artifact", "ref": str(root / "run.json"), "exists": True},
            {"kind": "measurement", "ref": str(root / "measurements.jsonl"), "exists": True},
            {"kind": "verdict", "ref": str(root / "decision.json"), "exists": True},
        ],
        "measurement_stream_ref": str(root / "measurements.jsonl"),
        "policy_refs": [],
    }
    write_json(root / "run.json", run)
    write_json(root / "decision.json", decision)
    write_json(root / "measurement-series" / "projection.json", projection)
    write_json(root / "seal.json", seal)
    (root / "measurements.jsonl").write_bytes(js_bytes(measurement) + b"\n")
    return {
        "run": run,
        "decision": decision,
        "projection": projection,
        "seal": seal,
        "measurement": measurement,
    }


class LevEvalObservationTests(unittest.TestCase):
    def test_controller_binding_identifier_mismatch_is_a_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            binding = build_lev_eval_observation_binding(
                request_id="historical-lev-eval-wrong-identifiers",
                source_run_dir=source,
                expected_execution_id="another-selected-run",
                expected_suite_id="constraintbox-foreign-eval-fixture",
            )

            with self.assertRaises(LevEvalObservationHoldError):
                observe_lev_eval_bundle(
                    source_run_dir=source,
                    observation_run_dir=root / "cb-observation",
                    binding=binding,
                )
            self.assertFalse((root / "cb-observation").exists())

    def test_symlinked_foreign_artifact_parent_is_a_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            series = source / "measurement-series"
            retained_series = source / "real-measurement-series"
            series.rename(retained_series)
            os.symlink(retained_series, series, target_is_directory=True)

            with self.assertRaises(LevEvalObservationHoldError):
                observe_lev_eval_bundle(
                    source_run_dir=source,
                    observation_run_dir=root / "cb-observation",
                )
            self.assertFalse((root / "cb-observation").exists())

    def test_source_directory_replaced_by_a_symlink_after_binding_is_a_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            binding = build_lev_eval_observation_binding(
                request_id="historical-lev-eval-source-swap",
                source_run_dir=source,
                expected_execution_id="cb-observe-fixture-v1",
                expected_suite_id="constraintbox-foreign-eval-fixture",
            )
            replacement = root / "foreign-run-replacement"
            source.rename(replacement)
            os.symlink(replacement, source, target_is_directory=True)

            with self.assertRaises(LevEvalObservationHoldError):
                observe_lev_eval_bundle(
                    source_run_dir=binding.source_run_dir,
                    observation_run_dir=root / "cb-observation",
                    binding=binding,
                )
            self.assertFalse((root / "cb-observation").exists())

    def test_bound_snapshot_replays_after_the_foreign_directory_is_gone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            binding = build_lev_eval_observation_binding(
                request_id="historical-lev-eval-1",
                source_run_dir=source,
                expected_execution_id="cb-observe-fixture-v1",
                expected_suite_id="constraintbox-foreign-eval-fixture",
            )
            captured = observe_lev_eval_bundle(
                source_run_dir=source,
                observation_run_dir=root / "cb-observation",
                binding=binding,
            )
            self.assertNotIn(
                str(source),
                json.dumps(captured.receipt, sort_keys=True),
            )
            self.assertEqual(
                captured.receipt["controller_binding"]["request_sha256"],
                binding.request_sha256,
            )
            self.assertEqual(
                captured.receipt["foreign_observation"]["snapshot_sha256"],
                hashlib.sha256(
                    canonical_json(captured.receipt["foreign_observation"]["files"])
                ).hexdigest(),
            )
            shutil.rmtree(source)
            recovered_binding = type(binding).from_dict(binding.as_dict())
            self.assertIsNone(recovered_binding.source_run_dir)
            replayed = verify_lev_eval_observation_snapshot(
                observation_run_dir=captured.observation_run_dir,
                expected_binding=recovered_binding,
                expected_receipt_sha256=captured.receipt_sha256,
            )
            self.assertEqual(replayed.receipt, captured.receipt)

    def test_retained_snapshot_tampering_is_a_hold_not_a_foreign_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            binding = build_lev_eval_observation_binding(
                request_id="historical-lev-eval-tamper",
                source_run_dir=source,
                expected_execution_id="cb-observe-fixture-v1",
                expected_suite_id="constraintbox-foreign-eval-fixture",
            )
            captured = observe_lev_eval_bundle(
                source_run_dir=source,
                observation_run_dir=root / "cb-observation",
                binding=binding,
            )
            retained = (
                captured.observation_run_dir
                / "foreign_lev_eval_bundle"
                / "measurements.jsonl"
            )
            retained.write_bytes(b"{}\n")
            with self.assertRaises(LevEvalObservationHoldError):
                verify_lev_eval_observation_snapshot(
                    observation_run_dir=captured.observation_run_dir,
                    expected_binding=binding,
                    expected_receipt_sha256=captured.receipt_sha256,
                )

    def test_retained_snapshot_directory_replaced_by_symlink_is_a_hold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            binding = build_lev_eval_observation_binding(
                request_id="historical-lev-eval-retained-swap",
                source_run_dir=source,
                expected_execution_id="cb-observe-fixture-v1",
                expected_suite_id="constraintbox-foreign-eval-fixture",
            )
            captured = observe_lev_eval_bundle(
                source_run_dir=source,
                observation_run_dir=root / "cb-observation",
                binding=binding,
            )
            replacement = root / "cb-observation-replacement"
            captured.observation_run_dir.rename(replacement)
            os.symlink(replacement, captured.observation_run_dir, target_is_directory=True)

            with self.assertRaises(LevEvalObservationHoldError):
                verify_lev_eval_observation_snapshot(
                    observation_run_dir=captured.observation_run_dir,
                    expected_binding=binding,
                    expected_receipt_sha256=captured.receipt_sha256,
                )

    def test_current_five_file_bundle_is_retained_without_authority_transfer(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            build_current_lev_bundle(source)
            result = observe_lev_eval_bundle(
                source_run_dir=source,
                observation_run_dir=root / "cb-observation",
            )

            self.assertTrue(result.receipt_path.is_file())
            self.assertEqual(
                result.receipt["receipt_sha256"],
                result.receipt_sha256,
            )
            self.assertFalse(
                result.receipt["foreign_observation"]["producer_authenticated"]
            )
            self.assertFalse(
                result.receipt["foreign_observation"]["foreign_decision_authority"]
            )
            self.assertEqual(
                result.receipt["unrecomputed_foreign_digests"],
                ["trace_cases_digest", "command_cases_digest"],
            )
            self.assertEqual(
                result.receipt["observed"]["decision_verdict"],
                "pass",
            )
            self.assertFalse(result.receipt["promotion_allowed"])
            for relative_name in (
                "run.json",
                "decision.json",
                "measurements.jsonl",
                "measurement-series/projection.json",
                "seal.json",
            ):
                self.assertEqual(
                    (source / relative_name).read_bytes(),
                    (
                        result.observation_run_dir
                        / "foreign_lev_eval_bundle"
                        / relative_name
                    ).read_bytes(),
                )

    def test_tampered_recomputable_decision_digest_is_rejected_before_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            bundle = build_current_lev_bundle(source)
            bundle["decision"]["input_digests"]["diagnostics_digest"] = "0" * 64
            write_json(source / "decision.json", bundle["decision"])
            destination = root / "cb-observation"

            with self.assertRaisesRegex(LevEvalObservationError, "diagnostics_digest"):
                observe_lev_eval_bundle(
                    source_run_dir=source,
                    observation_run_dir=destination,
                )
            self.assertFalse(destination.exists())

    def test_escaped_run_reference_is_rejected_before_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            bundle = build_current_lev_bundle(source)
            bundle["run"]["decision_ref"] = str(root / "outside.json")
            write_json(source / "run.json", bundle["run"])
            destination = root / "cb-observation"

            with self.assertRaisesRegex(LevEvalObservationError, "decision_ref"):
                observe_lev_eval_bundle(
                    source_run_dir=source,
                    observation_run_dir=destination,
                )
            self.assertFalse(destination.exists())

    def test_tampered_seal_cannot_turn_foreign_verdict_into_an_observation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source = root / "foreign-run"
            bundle = build_current_lev_bundle(source)
            bundle["seal"]["intent_ref"]["content_hash"] = "f" * 64
            write_json(source / "seal.json", bundle["seal"])

            with self.assertRaisesRegex(LevEvalObservationError, "intent_ref"):
                observe_lev_eval_bundle(
                    source_run_dir=source,
                    observation_run_dir=root / "cb-observation",
                )


if __name__ == "__main__":
    unittest.main()
