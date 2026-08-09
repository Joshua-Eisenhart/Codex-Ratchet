from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from constraintbox.ledger import HashChainLedger
from constraintbox.process_ratchet import (
    ADVANCED,
    BLOCKED,
    HOLD,
    INVARIANT_VIOLATION,
    PARKED,
    RUNG_RECEIPT_SCHEMA,
    GateExecution,
    ProcessRatchet,
    RungSpec,
)


def _gate(gate_id: str, verdict: str = "PASS") -> GateExecution:
    return GateExecution(gate_id, "a" * 64, "b" * 64, verdict)


class ProcessRatchetTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        (self.root / "e0.json").write_text('{"rung": 0}', encoding="utf-8")
        (self.root / "e1.json").write_text('{"rung": 1}', encoding="utf-8")
        (self.root / "e2.json").write_text('{"rung": 2}', encoding="utf-8")
        self.ledger = HashChainLedger(self.root / "ledger.jsonl")
        self.ladder = (
            RungSpec("r0", 0, ("e0.json",), ("cb:z3-request-gate",)),
            RungSpec("r1", 1, ("e1.json",)),
            RungSpec("r2", 2, ("e2.json",)),
        )
        self.ratchet = ProcessRatchet(self.ladder, self.ledger, self.root)

    def _ledger_lines(self) -> list[dict]:
        path = self.ledger.path
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
        ]

    def test_chain_extends_in_declared_order(self) -> None:
        first = self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),))
        self.assertEqual(first.state, ADVANCED)
        self.assertTrue(first.decision["agree"])
        for backend in ("z3", "cvc5", "enumeration"):
            self.assertEqual(first.decision[backend], "BOUNDED_SAT")
        self.assertIsNotNone(first.receipt_line_sha256)
        self.assertEqual(self.ratchet.next_rung(), "r1")

        second = self.ratchet.advance("r1")
        self.assertEqual(second.state, ADVANCED)
        third = self.ratchet.advance("r2")
        self.assertEqual(third.state, ADVANCED)
        self.assertIsNone(self.ratchet.next_rung())

        valid, reason = self.ledger.verify()
        self.assertTrue(valid, reason)
        self.assertEqual(len(self._ledger_lines()), 3)

    def test_skip_ahead_is_parked_naming_the_missing_rung(self) -> None:
        result = self.ratchet.advance("r1")
        self.assertEqual(result.state, PARKED)
        self.assertIn("r0", result.missing_rungs)
        self.assertTrue(result.reason.startswith("MISSING_RUNG_RECEIPT:"))
        self.assertIn("r0", result.reason)
        self.assertTrue(result.decision["agree"])
        self.assertEqual(result.decision["z3"], "BOUNDED_UNSAT")
        self.assertEqual(self._ledger_lines(), [])

    def test_deep_skip_names_every_missing_rung(self) -> None:
        result = self.ratchet.advance("r2")
        self.assertEqual(result.state, PARKED)
        self.assertEqual(set(result.missing_rungs), {"r0", "r1"})
        self.assertEqual(self._ledger_lines(), [])

    def test_lower_rung_byte_drift_is_invariant_violation(self) -> None:
        self.assertEqual(
            self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),)).state,
            ADVANCED,
        )
        (self.root / "e0.json").write_text('{"rung": 0, "edited": true}')
        result = self.ratchet.advance("r1")
        self.assertEqual(result.state, INVARIANT_VIOLATION)
        self.assertTrue(result.reason.startswith("RUNG_EVIDENCE_DRIFT:"))
        self.assertIn("r0", result.reason)
        drifted_rungs = {entry[0] for entry in result.drifted}
        drifted_paths = {entry[1] for entry in result.drifted}
        self.assertEqual(drifted_rungs, {"r0"})
        self.assertIn("e0.json", drifted_paths)
        self.assertEqual(result.decision["z3"], "BOUNDED_UNSAT")
        # No repair, no append: the chain still holds exactly one receipt.
        self.assertEqual(len(self._ledger_lines()), 1)

    def test_deleted_lower_evidence_is_invariant_violation(self) -> None:
        self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),))
        (self.root / "e0.json").unlink()
        result = self.ratchet.advance("r1")
        self.assertEqual(result.state, INVARIANT_VIOLATION)
        recomputed = {entry[3] for entry in result.drifted}
        self.assertIn("ABSENT", recomputed)

    def test_declared_only_gate_is_parked(self) -> None:
        result = self.ratchet.advance("r0")
        self.assertEqual(result.state, PARKED)
        self.assertIn("cb:z3-request-gate", result.missing_gates)
        self.assertTrue(result.reason.startswith("GATE_NOT_EXECUTED:"))
        self.assertEqual(self._ledger_lines(), [])

    def test_failed_gate_is_blocked(self) -> None:
        result = self.ratchet.advance(
            "r0", (_gate("cb:z3-request-gate", "FAIL"),)
        )
        self.assertEqual(result.state, BLOCKED)
        self.assertIn("cb:z3-request-gate", result.failed_gates)
        self.assertTrue(result.reason.startswith("GATE_EXECUTED_FAIL:"))
        self.assertEqual(self._ledger_lines(), [])

    def test_readvance_of_recorded_rung_is_blocked(self) -> None:
        self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),))
        result = self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),))
        self.assertEqual(result.state, BLOCKED)
        self.assertEqual(result.reason, "RUNG_ALREADY_RECORDED")
        self.assertEqual(len(self._ledger_lines()), 1)

    def test_missing_own_evidence_is_parked(self) -> None:
        self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),))
        (self.root / "e1.json").unlink()
        result = self.ratchet.advance("r1")
        self.assertEqual(result.state, PARKED)
        self.assertIn("e1.json", result.missing_evidence)
        self.assertTrue(result.reason.startswith("MISSING_EVIDENCE:"))

    def test_tampered_ledger_is_invariant_violation(self) -> None:
        self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),))
        raw = self.ledger.path.read_text(encoding="utf-8")
        self.ledger.path.write_text(
            raw.replace('"rung_id":"r0"', '"rung_id":"rX"'), encoding="utf-8"
        )
        result = self.ratchet.advance("r1")
        self.assertEqual(result.state, INVARIANT_VIOLATION)
        self.assertTrue(result.reason.startswith("LEDGER_BROKEN:"))

    def test_receipt_shape_on_chain(self) -> None:
        self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),))
        self.ratchet.advance("r1")
        rows = self._ledger_lines()
        record = rows[1]["record"]
        self.assertEqual(record["schema"], RUNG_RECEIPT_SCHEMA)
        self.assertEqual(record["rung_id"], "r1")
        self.assertEqual(record["ordinal"], 1)
        self.assertIn("e1.json", record["evidence"])
        self.assertEqual(len(record["evidence"]["e1.json"]), 64)
        self.assertEqual(record["revalidated"], {"r0": "validated"})
        self.assertIn("e0.json", record["revalidated_evidence"]["r0"])
        self.assertTrue(record["decision"]["agree"])
        self.assertIn("variables", record["decision_spec"])
        self.assertEqual(len(record["decision_spec_sha256"]), 64)
        self.assertFalse(record["promotion_allowed"])
        first_gate = record["gate_executions"]
        self.assertEqual(first_gate, [])
        r0_gates = rows[0]["record"]["gate_executions"]
        self.assertEqual(r0_gates[0]["gate_id"], "cb:z3-request-gate")
        self.assertEqual(r0_gates[0]["verdict"], "PASS")
        self.assertEqual(len(r0_gates[0]["input_sha256"]), 64)
        self.assertEqual(len(r0_gates[0]["output_sha256"]), 64)

    def test_spec_pins_enumerated_domains_only(self) -> None:
        result = self.ratchet.advance("r1")
        variables = result.spec["variables"]
        self.assertIn("ledger", variables)
        self.assertIn("chain", variables)
        self.assertIn("extension", variables)
        self.assertIn("evidence", variables)
        self.assertIn("rung::r0", variables)
        for domain in variables.values():
            self.assertTrue(all(isinstance(value, str) for value in domain))

    def test_malformed_gate_execution_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            GateExecution("g", "deadbeef", "b" * 64, "PASS")
        with self.assertRaises(ValueError):
            GateExecution("g", "a" * 64, "b" * 64, "MAYBE")
        with self.assertRaises(ValueError):
            GateExecution("", "a" * 64, "b" * 64, "PASS")

    def test_undeclared_gate_execution_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.ratchet.advance("r1", (_gate("cb:sympy-exact-gate"),))

    def test_unknown_rung_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.ratchet.advance("r9")

    def test_ladder_must_be_contiguous_from_zero(self) -> None:
        with self.assertRaises(ValueError):
            ProcessRatchet(
                (RungSpec("r0", 1, ("e0.json",)),), self.ledger, self.root
            )

    def test_rung_without_evidence_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            RungSpec("r0", 0, ())

    def test_ladder_rewrite_below_recorded_rung_is_drift(self) -> None:
        self.ratchet.advance("r0", (_gate("cb:z3-request-gate"),))
        rewritten = ProcessRatchet(
            (
                RungSpec("r0", 0, ("e0.json",)),  # gate silently dropped
                RungSpec("r1", 1, ("e1.json",)),
                RungSpec("r2", 2, ("e2.json",)),
            ),
            self.ledger,
            self.root,
        )
        result = rewritten.advance("r1")
        self.assertEqual(result.state, INVARIANT_VIOLATION)
        drifted_items = {entry[1] for entry in result.drifted}
        self.assertIn("ladder_prefix", drifted_items)


if __name__ == "__main__":
    unittest.main()
