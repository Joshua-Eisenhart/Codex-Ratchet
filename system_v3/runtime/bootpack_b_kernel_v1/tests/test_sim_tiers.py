import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from kernel import BootpackBKernel
from pipeline import A0BSimPipeline
from sim_dispatcher import A0SimDispatcher
from sim_engine import SimEngine
from state import KernelState


def _wrap_export(content_lines: list[str], export_id: str = "BATCH_SIM") -> str:
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


def _sim_spec_block(spec_id: str, probe_id: str, evidence_token: str, tier: str, family: str, target_class: str, negative_class: str = "") -> str:
    lines = [
        f"PROBE_HYP {probe_id}",
        f"PROBE_KIND {probe_id} CORR TIER_TEST",
        f"ASSERT {probe_id} CORR EXISTS PROBE_TOKEN PT_{probe_id}",
        f"SPEC_HYP {spec_id}",
        f"SPEC_KIND {spec_id} CORR SIM_SPEC",
        f"REQUIRES {spec_id} CORR {probe_id}",
        f"DEF_FIELD {spec_id} CORR REQUIRES_EVIDENCE {evidence_token}",
        f"DEF_FIELD {spec_id} CORR SIM_ID {spec_id}",
        f"DEF_FIELD {spec_id} CORR TIER {tier}",
        f"DEF_FIELD {spec_id} CORR FAMILY {family}",
        f"DEF_FIELD {spec_id} CORR TARGET_CLASS {target_class}",
        f"ASSERT {spec_id} CORR EXISTS EVIDENCE_TOKEN {evidence_token}",
    ]
    if negative_class:
        lines.insert(-1, f"DEF_FIELD {spec_id} CORR NEGATIVE_CLASS {negative_class}")
    return _wrap_export(lines, export_id=f"BATCH_{spec_id}")


class TestSimTierFlow(unittest.TestCase):
    def setUp(self):
        self.kernel = BootpackBKernel()
        self.state = KernelState()

    def test_dispatch_orders_by_tier(self):
        block_t1 = _sim_spec_block(
            spec_id="S_SIM_T1",
            probe_id="P_SIM_T1",
            evidence_token="E_SIM_T1",
            tier="T1_COMPOUND",
            family="BASELINE",
            target_class="TC_ALPHA",
        )
        block_t0 = _sim_spec_block(
            spec_id="S_SIM_T0",
            probe_id="P_SIM_T0",
            evidence_token="E_SIM_T0",
            tier="T0_ATOM",
            family="BASELINE",
            target_class="TC_ALPHA",
        )
        self.kernel.evaluate_export_block(block_t1, self.state, batch_id="T1")
        self.kernel.evaluate_export_block(block_t0, self.state, batch_id="T0")
        tasks = A0SimDispatcher().plan_tasks(self.state)
        self.assertEqual(2, len(tasks))
        self.assertEqual("T0_ATOM", tasks[0].tier)
        self.assertEqual("T1_COMPOUND", tasks[1].tier)

    def test_pipeline_cycle_emits_and_ingests_evidence(self):
        block = _sim_spec_block(
            spec_id="S_SIM_PIPE",
            probe_id="P_SIM_PIPE",
            evidence_token="E_SIM_PIPE",
            tier="T0_ATOM",
            family="BASELINE",
            target_class="TC_PIPE",
        )
        self.kernel.evaluate_export_block(block, self.state, batch_id="PIPE_BOOT")
        pipeline = A0BSimPipeline()
        pipeline.kernel = self.kernel
        cycle = pipeline.run_sim_cycle(self.state, batch_id="PIPE_RUN")
        self.assertEqual(1, cycle["planned_task_count"])
        self.assertIn("S_SIM_PIPE", cycle["satisfied_spec_ids"])
        self.assertNotIn("S_SIM_PIPE", self.state.evidence_pending)
        self.assertIn("S_SIM_PIPE", self.state.sim_results)

    def test_kill_signal_changes_status(self):
        block = _wrap_export(
            [
                "PROBE_HYP P_KILL_TARGET",
                "PROBE_KIND P_KILL_TARGET CORR MATH_VALIDATION",
                "ASSERT P_KILL_TARGET CORR EXISTS PROBE_TOKEN PT_P_KILL_TARGET",
                "SPEC_HYP S_KILL_TARGET",
                "SPEC_KIND S_KILL_TARGET CORR MATH_DEF",
                "REQUIRES S_KILL_TARGET CORR P_KILL_TARGET",
                "DEF_FIELD S_KILL_TARGET CORR OBJECTS density matrix",
                "DEF_FIELD S_KILL_TARGET CORR OPERATIONS trace",
                "DEF_FIELD S_KILL_TARGET CORR INVARIANTS finite dimensional",
                "DEF_FIELD S_KILL_TARGET CORR DOMAIN hilbert space",
                "DEF_FIELD S_KILL_TARGET CORR CODOMAIN density matrix",
                f"DEF_FIELD S_KILL_TARGET CORR SIM_CODE_HASH_SHA256 {'d'*64}",
                "ASSERT S_KILL_TARGET CORR EXISTS MATH_TOKEN MT_KILL",
                "KILL_IF S_KILL_TARGET CORR NEG_BREAK",
            ],
            export_id="KILL_BOOT",
        )
        result = self.kernel.evaluate_export_block(block, self.state, batch_id="KILL_BOOT")
        self.assertEqual([], result["rejected"])
        evidence = "\n".join(
            [
                "BEGIN SIM_EVIDENCE v1",
                "SIM_ID: S_KILL_TARGET",
                f"CODE_HASH_SHA256: {'e'*64}",
                f"INPUT_HASH_SHA256: {'1'*64}",
                f"OUTPUT_HASH_SHA256: {'f'*64}",
                f"RUN_MANIFEST_SHA256: {'2'*64}",
                "KILL_SIGNAL S_KILL_TARGET CORR NEG_BREAK",
                "END SIM_EVIDENCE v1",
                "",
            ]
        )
        self.kernel.ingest_sim_evidence_pack(evidence, self.state, batch_id="KILL_EVIDENCE")
        self.assertEqual("KILLED", self.state.survivor_ledger["S_KILL_TARGET"]["status"])

    def test_ruleset_hash_activation_gate(self):
        evidence = "\n".join(
            [
                "BEGIN SIM_EVIDENCE v1",
                "SIM_ID: S_RULESET_HASH",
                f"CODE_HASH_SHA256: {'1'*64}",
                f"INPUT_HASH_SHA256: {'4'*64}",
                f"OUTPUT_HASH_SHA256: {'2'*64}",
                f"RUN_MANIFEST_SHA256: {'5'*64}",
                f"METRIC: ruleset_sha256={'3'*64}",
                "EVIDENCE_SIGNAL S_RULESET_HASH CORR E_RULESET_HASH",
                "END SIM_EVIDENCE v1",
                "",
            ]
        )
        self.kernel.ingest_sim_evidence_pack(evidence, self.state, batch_id="RULESET_ACTIVATE")
        self.assertEqual("3" * 64, self.state.active_ruleset_sha256)

        no_header = _wrap_export(
            [
                "SPEC_HYP S_RULESET_TEST",
                "SPEC_KIND S_RULESET_TEST CORR MATH_DEF",
                "DEF_FIELD S_RULESET_TEST CORR OBJECTS density matrix",
                "DEF_FIELD S_RULESET_TEST CORR OPERATIONS trace",
                "DEF_FIELD S_RULESET_TEST CORR INVARIANTS finite dimensional",
                "DEF_FIELD S_RULESET_TEST CORR DOMAIN hilbert space",
                "DEF_FIELD S_RULESET_TEST CORR CODOMAIN density matrix",
                f"DEF_FIELD S_RULESET_TEST CORR SIM_CODE_HASH_SHA256 {'4'*64}",
                "ASSERT S_RULESET_TEST CORR EXISTS MATH_TOKEN MT_RULESET_TEST",
            ],
            export_id="RULESET_FAIL",
        )
        fail_result = self.kernel.evaluate_export_block(no_header, self.state, batch_id="RULESET_FAIL")
        self.assertEqual("SCHEMA_FAIL", fail_result["rejected"][0]["reason"])

        with_header_lines = [
            "BEGIN EXPORT_BLOCK v1",
            "EXPORT_ID: RULESET_PASS",
            "TARGET: THREAD_B_ENFORCEMENT_KERNEL",
            "PROPOSAL_TYPE: TEST",
            f"RULESET_SHA256: {'3'*64}",
            "CONTENT:",
            "  SPEC_HYP S_RULESET_TEST_PASS",
            "  SPEC_KIND S_RULESET_TEST_PASS CORR MATH_DEF",
            "  DEF_FIELD S_RULESET_TEST_PASS CORR OBJECTS density matrix",
            "  DEF_FIELD S_RULESET_TEST_PASS CORR OPERATIONS trace",
            "  DEF_FIELD S_RULESET_TEST_PASS CORR INVARIANTS finite dimensional",
            "  DEF_FIELD S_RULESET_TEST_PASS CORR DOMAIN hilbert space",
            "  DEF_FIELD S_RULESET_TEST_PASS CORR CODOMAIN density matrix",
            f"  DEF_FIELD S_RULESET_TEST_PASS CORR SIM_CODE_HASH_SHA256 {'5'*64}",
            "  ASSERT S_RULESET_TEST_PASS CORR EXISTS MATH_TOKEN MT_RULESET_TEST_PASS",
            "END EXPORT_BLOCK v1",
            "",
        ]
        pass_result = self.kernel.evaluate_export_block("\n".join(with_header_lines), self.state, batch_id="RULESET_PASS")
        self.assertEqual([], pass_result["rejected"])

    def test_promotion_report_gate_blockers(self):
        engine = SimEngine()
        block = _sim_spec_block(
            spec_id="S_PROMOTE_T1",
            probe_id="P_PROMOTE_T1",
            evidence_token="E_PROMOTE_T1",
            tier="T1_COMPOUND",
            family="BASELINE",
            target_class="TC_PROMOTE",
        )
        self.kernel.evaluate_export_block(block, self.state, batch_id="PROMOTE_BOOT")
        report = engine.coverage_report(self.state, graveyard_by_target_class={})
        self.assertEqual("NOT_READY", report["master_sim_status"])
        self.assertTrue(any(row["sim_id"] == "S_PROMOTE_T1" for row in report["unresolved_promotion_blockers"]))


if __name__ == "__main__":
    unittest.main()
