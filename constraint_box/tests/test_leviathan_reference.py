from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from constraintbox.leviathan_reference import (
    normalize_leviathan_dry_run_seal,
    observe_lev_exec_validate_flow,
    run_reference_conformance,
    run_leviathan_seal_boundary_controls,
)


def _valid_lev_seal() -> dict[str, object]:
    return {
        "type": "execution.sealed",
        "timestamp": "2026-07-31T00:00:00.000Z",
        "execution_id": "reference-run-1",
        "invocation_id": "reference-run-1",
        "receipt_id": "reference-receipt-1",
        "seal": {
            "schema": "lev.run_seal.v1",
            "execution_id": "reference-run-1",
            "intent_ref": {
                "uri": "urn:lev:source-intent:sha256:abc123",
                "adapter": "lev.input-adapter.source-intent.v1",
                "content_hash": "sha256:abc123",
            },
            "outcome": "dry_run_success",
            "evidence_refs": [
                {
                    "kind": "receipt",
                    "dry_run": True,
                    "proof_backed_execution": False,
                    "passed": False,
                },
                {"kind": "trace"},
            ],
        },
    }


def _valid_lev_flow_source() -> str:
    return """name: sdlc-exec-validate
entry: exec
nodes:
  exec:
    type: action
    op: lev.exec
    next: validate
  validate:
    op: lev.exec
    branches:
      pass: emit
      fail: exec
    max_iterations: \"{{knobs.max_verify_retries}}\"
    on_timeout: escalate
  escalate:
    next: done
  emit:
    type: action
    next: done
  done:
    terminal: true
"""


class LeviathanReferenceTests(unittest.TestCase):
    def test_reference_flow_has_eligible_and_hold_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_reference_conformance(
                run_root=Path(temporary) / "reference",
                request_id="lev-reference-test",
            )

        self.assertEqual(result["disposition"], "ELIGIBLE")
        self.assertEqual(result["success_after_retry"]["terminal"], "ELIGIBLE")
        self.assertEqual(result["success_after_retry"]["retries"], 1)
        self.assertEqual(result["retry_exhausted"]["terminal"], "HOLD")
        self.assertEqual(result["retry_exhausted"]["retries"], 2)
        self.assertFalse(result["llm_decision_authority"])
        self.assertFalse(result["leviathan_decision_authority"])
        self.assertFalse(result["promotion_allowed"])
        self.assertTrue(result["cb_reference_structure"]["valid"])

    def test_real_seal_shape_normalizes_to_non_authoritative_dry_run(self) -> None:
        valid, reason, normalized = normalize_leviathan_dry_run_seal(_valid_lev_seal())

        self.assertTrue(valid, reason)
        self.assertEqual(reason, "valid_leviathan_dry_run_seal")
        self.assertTrue(normalized["dry_run"])
        self.assertFalse(normalized["proof_backed_execution"])
        self.assertFalse(normalized["receipt_passed"])

    def test_non_dry_run_seal_is_refused(self) -> None:
        forged = copy.deepcopy(_valid_lev_seal())
        forged["seal"]["outcome"] = "execution_success"

        valid, reason, _normalized = normalize_leviathan_dry_run_seal(forged)

        self.assertFalse(valid)
        self.assertEqual(reason, "reference run was not a successful dry run")

    def test_proof_bearing_receipt_cannot_be_relabeled_as_dry_run(self) -> None:
        forged = copy.deepcopy(_valid_lev_seal())
        forged["seal"]["evidence_refs"][0]["proof_backed_execution"] = True

        valid, reason, _normalized = normalize_leviathan_dry_run_seal(forged)

        self.assertFalse(valid)
        self.assertEqual(reason, "reference receipt is not an unexecuted dry-run receipt")

    def test_seal_boundary_controls_reject_real_execution_variants(self) -> None:
        controls = run_leviathan_seal_boundary_controls(_valid_lev_seal())

        self.assertTrue(controls["valid"])
        self.assertTrue(controls["checks"]["baseline_dry_run"])
        self.assertTrue(controls["checks"]["execution_outcome_refused"])
        self.assertTrue(controls["checks"]["proof_bearing_receipt_refused"])

    def test_narrow_lev_flow_observer_binds_the_actual_control_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "exec-validate.flow.yaml"
            path.write_text(_valid_lev_flow_source(), encoding="utf-8")
            observed = observe_lev_exec_validate_flow(path)
            path.write_text(
                _valid_lev_flow_source().replace("on_timeout: escalate", "on_timeout: park"),
                encoding="utf-8",
            )
            mismatched = observe_lev_exec_validate_flow(path)

        self.assertTrue(observed["valid"], observed)
        self.assertEqual(observed["observed_structure"]["retry_edge"], ["validate", "exec"])
        self.assertFalse(mismatched["valid"])
        self.assertFalse(mismatched["checks"]["validate_timeout_to_escalate"])
