import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from kernel import BootpackBKernel
from pipeline import A0BSimPipeline
from state import KernelState


def _wrap_export(content_lines: list[str], export_id: str = "BATCH_NEG") -> str:
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


def _neg_sim_spec(
    *,
    spec_id: str,
    probe_id: str,
    evidence_token: str,
    target_class: str,
    negative_class: str,
    extra_def_fields: list[str] | None = None,
) -> str:
    extra_def_fields = extra_def_fields or []
    lines = [
        f"PROBE_HYP {probe_id}",
        f"PROBE_KIND {probe_id} CORR NEG_TEST",
        f"ASSERT {probe_id} CORR EXISTS PROBE_TOKEN PT_{probe_id}",
        f"SPEC_HYP {spec_id}",
        f"SPEC_KIND {spec_id} CORR SIM_SPEC",
        f"REQUIRES {spec_id} CORR {probe_id}",
        f"DEF_FIELD {spec_id} CORR REQUIRES_EVIDENCE {evidence_token}",
        f"DEF_FIELD {spec_id} CORR SIM_ID {spec_id}",
        "DEF_FIELD {spec_id} CORR TIER T0_ATOM".format(spec_id=spec_id),
        "DEF_FIELD {spec_id} CORR FAMILY ADVERSARIAL_NEG".format(spec_id=spec_id),
        f"DEF_FIELD {spec_id} CORR TARGET_CLASS {target_class}",
        f"DEF_FIELD {spec_id} CORR NEGATIVE_CLASS {negative_class}",
    ]
    for row in extra_def_fields:
        lines.append(f"DEF_FIELD {spec_id} CORR {row}")
    lines.extend(
        [
            f"ASSERT {spec_id} CORR EXISTS EVIDENCE_TOKEN {evidence_token}",
            f"KILL_IF {spec_id} CORR NEG_{negative_class}",
        ]
    )
    return _wrap_export(lines, export_id=f"BATCH_{spec_id}")


class TestNegativeSimSemantics(unittest.TestCase):
    def setUp(self) -> None:
        self.kernel = BootpackBKernel()
        self.state = KernelState()

    def test_negative_sim_without_expected_marker_does_not_kill(self) -> None:
        block = _neg_sim_spec(
            spec_id="S_NEG_NO_MARKER",
            probe_id="P_NEG_NO_MARKER",
            evidence_token="E_NEG_NO_MARKER",
            target_class="TC_NEG",
            negative_class="COMMUTATIVE_ASSUMPTION",
            extra_def_fields=[],
        )
        self.kernel.evaluate_export_block(block, self.state, batch_id="NEG_BOOT")
        pipeline = A0BSimPipeline()
        pipeline.kernel = self.kernel
        pipeline.run_sim_cycle(self.state, batch_id="NEG_RUN")
        self.assertEqual("ACTIVE", self.state.survivor_ledger["S_NEG_NO_MARKER"]["status"])
        killed_ids = {row.get("id") for row in self.state.kill_log if row.get("tag") == "KILL_SIGNAL"}
        self.assertNotIn("S_NEG_NO_MARKER", killed_ids)

    def test_negative_sim_with_expected_marker_kills(self) -> None:
        block = _neg_sim_spec(
            spec_id="S_NEG_WITH_MARKER",
            probe_id="P_NEG_WITH_MARKER",
            evidence_token="E_NEG_WITH_MARKER",
            target_class="TC_NEG",
            negative_class="COMMUTATIVE_ASSUMPTION",
            extra_def_fields=["ASSUME_COMMUTATIVE TRUE"],
        )
        self.kernel.evaluate_export_block(block, self.state, batch_id="NEG_BOOT")
        pipeline = A0BSimPipeline()
        pipeline.kernel = self.kernel
        pipeline.run_sim_cycle(self.state, batch_id="NEG_RUN")
        self.assertNotIn("S_NEG_WITH_MARKER", self.state.survivor_ledger)
        self.assertIn("S_NEG_WITH_MARKER", self.state.graveyard)
        killed_ids = {row.get("id") for row in self.state.kill_log if row.get("tag") == "KILL_SIGNAL"}
        self.assertIn("S_NEG_WITH_MARKER", killed_ids)
        # Interaction counts exclude kill targets (non-kill evidence only).
        self.assertEqual(0, self.state.interaction_counts.get("S_NEG_WITH_MARKER", 0))

    def test_negative_sim_kill_target_can_kill_bound_math_artifact(self) -> None:
        block = _wrap_export(
            [
                "SPEC_HYP S_MATH_TARGET",
                "SPEC_KIND S_MATH_TARGET CORR MATH_DEF",
                "DEF_FIELD S_MATH_TARGET CORR OBJECTS density matrix operator",
                "DEF_FIELD S_MATH_TARGET CORR OPERATIONS channel cptp",
                "DEF_FIELD S_MATH_TARGET CORR INVARIANTS finite dimensional",
                "DEF_FIELD S_MATH_TARGET CORR DOMAIN hilbert space",
                "DEF_FIELD S_MATH_TARGET CORR CODOMAIN density matrix",
                f"DEF_FIELD S_MATH_TARGET CORR SIM_CODE_HASH_SHA256 {'d'*64}",
                "DEF_FIELD S_MATH_TARGET CORR KILL_BIND S_NEG_TARGETER",
                "ASSERT S_MATH_TARGET CORR EXISTS MATH_TOKEN MT_TARGET",
                "KILL_IF S_MATH_TARGET CORR NEG_COMMUTATIVE_ASSUMPTION",
                "PROBE_HYP P_NEG_TARGETER",
                "PROBE_KIND P_NEG_TARGETER CORR NEG_TEST",
                "ASSERT P_NEG_TARGETER CORR EXISTS PROBE_TOKEN PT_P_NEG_TARGETER",
                "SPEC_HYP S_NEG_TARGETER",
                "SPEC_KIND S_NEG_TARGETER CORR SIM_SPEC",
                "REQUIRES S_NEG_TARGETER CORR P_NEG_TARGETER",
                "DEF_FIELD S_NEG_TARGETER CORR REQUIRES_EVIDENCE E_NEG_TARGETER",
                "DEF_FIELD S_NEG_TARGETER CORR SIM_ID S_NEG_TARGETER",
                "DEF_FIELD S_NEG_TARGETER CORR TIER T0_ATOM",
                "DEF_FIELD S_NEG_TARGETER CORR FAMILY ADVERSARIAL_NEG",
                "DEF_FIELD S_NEG_TARGETER CORR TARGET_CLASS TC_NEG",
                "DEF_FIELD S_NEG_TARGETER CORR NEGATIVE_CLASS COMMUTATIVE_ASSUMPTION",
                "DEF_FIELD S_NEG_TARGETER CORR ASSUME_COMMUTATIVE TRUE",
                "DEF_FIELD S_NEG_TARGETER CORR KILL_TARGET S_MATH_TARGET",
                "ASSERT S_NEG_TARGETER CORR EXISTS EVIDENCE_TOKEN E_NEG_TARGETER",
                "KILL_IF S_NEG_TARGETER CORR NEG_COMMUTATIVE_ASSUMPTION",
            ],
            export_id="BATCH_NEG_TARGET",
        )
        self.kernel.evaluate_export_block(block, self.state, batch_id="NEG_TARGET_BOOT")
        pipeline = A0BSimPipeline()
        pipeline.kernel = self.kernel
        pipeline.run_sim_cycle(self.state, batch_id="NEG_TARGET_RUN")
        killed_ids = {row.get("id") for row in self.state.kill_log if row.get("tag") == "KILL_SIGNAL"}
        self.assertIn("S_NEG_TARGETER", killed_ids)
        self.assertIn("S_MATH_TARGET", killed_ids)
        self.assertNotIn("S_MATH_TARGET", self.state.survivor_ledger)
        self.assertIn("S_MATH_TARGET", self.state.graveyard)


if __name__ == "__main__":
    unittest.main()
