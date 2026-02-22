import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from kernel import BootpackBKernel
from snapshot import build_snapshot_v2
from state import KernelState


def _wrap_export(content_lines: list[str], export_id: str = "BATCH_001") -> str:
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


def _math_def_block(spec_id: str = "S_MATH_ALPHA", objects_value: str = "density matrix operator") -> str:
    probe_id = f"P_{spec_id}"
    content = [
        f"PROBE_HYP {probe_id}",
        f"PROBE_KIND {probe_id} CORR MATH_VALIDATION",
        f"ASSERT {probe_id} CORR EXISTS PROBE_TOKEN PT_{probe_id}",
        f"SPEC_HYP {spec_id}",
        f"SPEC_KIND {spec_id} CORR MATH_DEF",
        f"REQUIRES {spec_id} CORR {probe_id}",
        f"DEF_FIELD {spec_id} CORR OBJECTS {objects_value}",
        f"DEF_FIELD {spec_id} CORR OPERATIONS trace",
        f"DEF_FIELD {spec_id} CORR INVARIANTS finite dimensional",
        f"DEF_FIELD {spec_id} CORR DOMAIN hilbert space",
        f"DEF_FIELD {spec_id} CORR CODOMAIN density matrix",
        f"DEF_FIELD {spec_id} CORR SIM_CODE_HASH_SHA256 {'a'*64}",
        f"ASSERT {spec_id} CORR EXISTS MATH_TOKEN MT_{spec_id}",
    ]
    return _wrap_export(content, export_id=f"BATCH_{spec_id}")


class TestBootpackConformance(unittest.TestCase):
    def setUp(self):
        self.kernel = BootpackBKernel()
        self.state = KernelState()

    def test_pass_math_and_term_def(self):
        result_math = self.kernel.evaluate_export_block(_math_def_block(), self.state, batch_id="PASS_1")
        self.assertEqual([], result_math["rejected"])
        self.assertEqual([], result_math["parked"])
        self.assertEqual(2, len(result_math["accepted"]))

        term_block = _wrap_export(
            [
                "PROBE_HYP P_TERM_DENSITY_MATRIX",
                "PROBE_KIND P_TERM_DENSITY_MATRIX CORR TERM_VALIDATION",
                "ASSERT P_TERM_DENSITY_MATRIX CORR EXISTS PROBE_TOKEN PT_P_TERM_DENSITY_MATRIX",
                "SPEC_HYP S_TERM_DENSITY_MATRIX",
                "SPEC_KIND S_TERM_DENSITY_MATRIX CORR TERM_DEF",
                "REQUIRES S_TERM_DENSITY_MATRIX CORR S_MATH_ALPHA",
                'DEF_FIELD S_TERM_DENSITY_MATRIX CORR TERM "density_matrix"',
                "DEF_FIELD S_TERM_DENSITY_MATRIX CORR BINDS S_MATH_ALPHA",
                "ASSERT S_TERM_DENSITY_MATRIX CORR EXISTS TERM_TOKEN TT_DENSITY_MATRIX",
            ],
            export_id="PASS_2",
        )
        result_term = self.kernel.evaluate_export_block(term_block, self.state, batch_id="PASS_2")
        self.assertEqual([], result_term["rejected"])
        self.assertEqual([], result_term["parked"])
        self.assertEqual(2, len(result_term["accepted"]))
        self.assertIn("density_matrix", self.state.term_registry)

    def test_park_unknown_lexeme_component(self):
        self.kernel.evaluate_export_block(_math_def_block(), self.state, batch_id="PARK_BOOT")
        park_block = _wrap_export(
            [
                "SPEC_HYP S_TERM_DENSITY_UNKNOWN",
                "SPEC_KIND S_TERM_DENSITY_UNKNOWN CORR TERM_DEF",
                "REQUIRES S_TERM_DENSITY_UNKNOWN CORR S_MATH_ALPHA",
                'DEF_FIELD S_TERM_DENSITY_UNKNOWN CORR TERM "density_unknown"',
                "DEF_FIELD S_TERM_DENSITY_UNKNOWN CORR BINDS S_MATH_ALPHA",
                "ASSERT S_TERM_DENSITY_UNKNOWN CORR EXISTS TERM_TOKEN TT_DENSITY_UNKNOWN",
            ],
            export_id="PARK_1",
        )
        result = self.kernel.evaluate_export_block(park_block, self.state, batch_id="PARK_1")
        self.assertEqual([], result["rejected"])
        self.assertEqual(1, len(result["parked"]))
        self.assertEqual("UNDEFINED_TERM_USE", result["parked"][0]["reason"])

    def test_reject_unquoted_equal(self):
        reject_block = _math_def_block(spec_id="S_MATH_BAD_EQUAL", objects_value="a=b")
        result = self.kernel.evaluate_export_block(reject_block, self.state, batch_id="REJECT_EQ")
        self.assertEqual(1, len(result["rejected"]))
        self.assertEqual("UNQUOTED_EQUAL", result["rejected"][0]["reason"])

    def test_reject_derived_only_primitive(self):
        reject_block = _math_def_block(spec_id="S_MATH_BAD_DERIVED", objects_value="map")
        result = self.kernel.evaluate_export_block(reject_block, self.state, batch_id="REJECT_DERIVED")
        self.assertEqual(1, len(result["rejected"]))
        self.assertEqual("DERIVED_ONLY_PRIMITIVE_USE", result["rejected"][0]["reason"])

    def test_sim_spec_evidence_flow(self):
        sim_block = _wrap_export(
            [
                "PROBE_HYP P94_FULL16X4_ENGINE_PROBE",
                "PROBE_KIND P94_FULL16X4_ENGINE_PROBE CORR FULL16X4_ENGINE",
                "ASSERT P94_FULL16X4_ENGINE_PROBE CORR EXISTS PROBE_TOKEN PT_P94_FULL16X4_ENGINE",
                "SPEC_HYP S_BIND_MS_A_FULL16X4",
                "SPEC_KIND S_BIND_MS_A_FULL16X4 CORR SIM_SPEC",
                "REQUIRES S_BIND_MS_A_FULL16X4 CORR P94_FULL16X4_ENGINE_PROBE",
                "DEF_FIELD S_BIND_MS_A_FULL16X4 CORR REQUIRES_EVIDENCE E_MS_A_FULL16X4",
                "ASSERT S_BIND_MS_A_FULL16X4 CORR EXISTS EVIDENCE_TOKEN E_MS_A_FULL16X4",
            ],
            export_id="SIM_PASS",
        )
        result = self.kernel.evaluate_export_block(sim_block, self.state, batch_id="SIM_PASS")
        self.assertEqual([], result["rejected"])
        self.assertEqual([], result["parked"])
        self.assertIn("S_BIND_MS_A_FULL16X4", self.state.evidence_pending)

        evidence = "\n".join(
            [
                "BEGIN SIM_EVIDENCE v1",
                "SIM_ID: S_BIND_MS_A_FULL16X4",
                f"CODE_HASH_SHA256: {'b'*64}",
                f"INPUT_HASH_SHA256: {'d'*64}",
                f"OUTPUT_HASH_SHA256: {'c'*64}",
                f"RUN_MANIFEST_SHA256: {'e'*64}",
                "EVIDENCE_SIGNAL S_BIND_MS_A_FULL16X4 CORR E_MS_A_FULL16X4",
                "END SIM_EVIDENCE v1",
                "",
            ]
        )
        evidence_result = self.kernel.ingest_sim_evidence_pack(evidence, self.state, batch_id="SIM_EVIDENCE")
        self.assertEqual("OK", evidence_result["status"])
        self.assertIn("S_BIND_MS_A_FULL16X4", evidence_result["satisfied"])
        self.assertNotIn("S_BIND_MS_A_FULL16X4", self.state.evidence_pending)
        self.assertEqual("ACTIVE", self.state.survivor_ledger["S_BIND_MS_A_FULL16X4"]["status"])

    def test_snapshot_export(self):
        self.kernel.evaluate_export_block(_math_def_block(), self.state, batch_id="SNAP")
        snapshot = build_snapshot_v2(self.state)
        self.assertIn("BEGIN THREAD_S_SAVE_SNAPSHOT v2", snapshot)
        self.assertIn("SURVIVOR_LEDGER:", snapshot)
        self.assertIn("END THREAD_S_SAVE_SNAPSHOT v2", snapshot)


if __name__ == "__main__":
    unittest.main()
