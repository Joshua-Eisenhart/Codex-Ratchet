import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from pipeline import A0BSimPipeline
from state import KernelState


def _wrap_export(content_lines: list[str], export_id: str = "BATCH_POS_FAIL") -> str:
    lines = [
        "BEGIN EXPORT_BLOCK v1",
        f"EXPORT_ID: {export_id}",
        "TARGET: THREAD_B_ENFORCEMENT_KERNEL",
        "PROPOSAL_TYPE: TEST",
        "CONTENT:",
    ]
    lines.extend([f"  {line}" for line in content_lines])
    lines.append("END EXPORT_BLOCK v1")
    return "\n".join(lines) + "\n"


class TestPositiveProbeFailKills(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = A0BSimPipeline()
        self.state = KernelState()

    def test_positive_probe_fail_emits_sim_fail_kill_and_no_evidence(self) -> None:
        """
        Positive (non-negative) SIM specs must not canonize on failed/default probes.

        Mechanically:
        - SimEngine must NOT emit EVIDENCE_SIGNAL when probe_pass=false.
        - It MUST emit KILL_SIGNAL ... SIM_FAIL so the kernel clears evidence_pending
          and the spec enters the graveyard (status=KILLED).
        """
        spec_id = "S_POS_UNKNOWN_TERM"
        evidence = "E_POS_UNKNOWN_TERM"
        probe_id = "P_POS_UNKNOWN_TERM"
        export = _wrap_export(
            [
                f"PROBE_HYP {probe_id}",
                f"PROBE_KIND {probe_id} CORR POS_TEST",
                f"ASSERT {probe_id} CORR EXISTS PROBE_TOKEN PT_{probe_id}",
                f"SPEC_HYP {spec_id}",
                f"SPEC_KIND {spec_id} CORR SIM_SPEC",
                f"REQUIRES {spec_id} CORR {probe_id}",
                f"DEF_FIELD {spec_id} CORR REQUIRES_EVIDENCE {evidence}",
                f"DEF_FIELD {spec_id} CORR SIM_ID {spec_id}",
                f"DEF_FIELD {spec_id} CORR TIER T0_ATOM",
                f"DEF_FIELD {spec_id} CORR FAMILY BASELINE",
                f"DEF_FIELD {spec_id} CORR TARGET_CLASS TC_POS_TEST",
                f"ASSERT {spec_id} CORR EXISTS EVIDENCE_TOKEN {evidence}",
                f"KILL_IF {spec_id} CORR SIM_FAIL",
            ],
            export_id="BATCH_POS_FAIL_001",
        )
        self.pipeline.ingest_export_block(export, self.state, batch_id="POS_BOOT")
        self.assertIn(spec_id, self.state.evidence_pending)
        self.assertEqual("PENDING_EVIDENCE", self.state.survivor_ledger[spec_id]["status"])

        cycle = self.pipeline.run_sim_cycle(self.state, batch_id="POS_RUN")
        self.assertEqual(1, cycle["planned_task_count"])

        self.assertNotIn(evidence, self.state.evidence_tokens)
        self.assertNotIn(spec_id, self.state.survivor_ledger)
        self.assertIn(spec_id, self.state.graveyard)
        self.assertEqual("KILL_SIGNAL", self.state.graveyard[spec_id]["tag"])
        self.assertNotIn(spec_id, self.state.evidence_pending)
        killed_ids = {row.get("id") for row in self.state.kill_log if row.get("tag") == "KILL_SIGNAL"}
        self.assertIn(spec_id, killed_ids)


if __name__ == "__main__":
    unittest.main()
