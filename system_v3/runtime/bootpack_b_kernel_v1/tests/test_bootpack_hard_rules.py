import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from kernel import BootpackBKernel
from state import KernelState


def _wrap_export(content_lines: list[str], export_id: str) -> str:
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


def _math_with_formula(spec_id: str, formula: str) -> str:
    probe_id = f"P_{spec_id}"
    return _wrap_export(
        [
            f"PROBE_HYP {probe_id}",
            f"PROBE_KIND {probe_id} CORR FORMULA_TEST",
            f"ASSERT {probe_id} CORR EXISTS PROBE_TOKEN PT_{probe_id}",
            f"SPEC_HYP {spec_id}",
            f"SPEC_KIND {spec_id} CORR MATH_DEF",
            f"REQUIRES {spec_id} CORR {probe_id}",
            f'DEF_FIELD {spec_id} CORR FORMULA "{formula}"',
            f"DEF_FIELD {spec_id} CORR OBJECTS density matrix",
            f"DEF_FIELD {spec_id} CORR OPERATIONS trace",
            f"DEF_FIELD {spec_id} CORR INVARIANTS finite dimensional",
            f"DEF_FIELD {spec_id} CORR DOMAIN hilbert space",
            f"DEF_FIELD {spec_id} CORR CODOMAIN density matrix",
            f"DEF_FIELD {spec_id} CORR SIM_CODE_HASH_SHA256 {'a'*64}",
            f"ASSERT {spec_id} CORR EXISTS MATH_TOKEN MT_{spec_id}",
        ],
        export_id=f"E_{spec_id}",
    )


class TestBootpackHardRules(unittest.TestCase):
    def setUp(self):
        self.kernel = BootpackBKernel()
        self.state = KernelState()

    def test_formula_unknown_glyph_reject(self):
        result = self.kernel.evaluate_export_block(_math_with_formula("S_FORMULA_UNKNOWN", "density@matrix"), self.state, batch_id="F_UNKNOWN")
        self.assertEqual(1, len(result["rejected"]))
        self.assertEqual("GLYPH_NOT_PERMITTED", result["rejected"][0]["reason"])
        self.assertEqual("BR-0F6", result["rejected"][0]["offender_rule"])

    def test_formula_known_glyph_without_term_reject(self):
        result = self.kernel.evaluate_export_block(_math_with_formula("S_FORMULA_PLUS", "density+matrix"), self.state, batch_id="F_PLUS")
        self.assertEqual(1, len(result["rejected"]))
        self.assertEqual("GLYPH_NOT_PERMITTED", result["rejected"][0]["reason"])
        self.assertEqual("BR-0F5", result["rejected"][0]["offender_rule"])

    def test_probe_utilization_parks_unused_probe_after_3_batches(self):
        probe_only = _wrap_export(
            [
                "PROBE_HYP P_UNUSED_PROBE",
                "PROBE_KIND P_UNUSED_PROBE CORR UTIL_TEST",
                "ASSERT P_UNUSED_PROBE CORR EXISTS PROBE_TOKEN PT_P_UNUSED_PROBE",
            ],
            export_id="E_PROBE_ONLY",
        )
        self.kernel.evaluate_export_block(probe_only, self.state, batch_id="B1")

        axiom_1 = _wrap_export(["AXIOM_HYP W_TEST_1", "AXIOM_KIND W_TEST_1 CORR BASE_RULE"], export_id="E_A1")
        axiom_2 = _wrap_export(["AXIOM_HYP W_TEST_2", "AXIOM_KIND W_TEST_2 CORR BASE_RULE"], export_id="E_A2")
        axiom_3 = _wrap_export(["AXIOM_HYP W_TEST_3", "AXIOM_KIND W_TEST_3 CORR BASE_RULE"], export_id="E_A3")
        self.kernel.evaluate_export_block(axiom_1, self.state, batch_id="B2")
        self.kernel.evaluate_export_block(axiom_2, self.state, batch_id="B3")
        self.kernel.evaluate_export_block(axiom_3, self.state, batch_id="B4")

        self.assertNotIn("P_UNUSED_PROBE", self.state.survivor_ledger)
        self.assertIn("P_UNUSED_PROBE", self.state.park_set)
        self.assertEqual("UNUSED_PROBE", self.state.park_set["P_UNUSED_PROBE"]["tag"])

    def test_probe_utilization_counts_same_batch_reference(self):
        batch = _wrap_export(
            [
                "PROBE_HYP P_USED_NOW",
                "PROBE_KIND P_USED_NOW CORR UTIL_TEST",
                "ASSERT P_USED_NOW CORR EXISTS PROBE_TOKEN PT_P_USED_NOW",
                "SPEC_HYP S_USED_NOW",
                "SPEC_KIND S_USED_NOW CORR SIM_SPEC",
                "REQUIRES S_USED_NOW CORR P_USED_NOW",
                "DEF_FIELD S_USED_NOW CORR REQUIRES_EVIDENCE E_USED_NOW",
                "ASSERT S_USED_NOW CORR EXISTS EVIDENCE_TOKEN E_USED_NOW",
            ],
            export_id="E_PROBE_USED_NOW",
        )
        result = self.kernel.evaluate_export_block(batch, self.state, batch_id="B1_USED")
        self.assertEqual([], result["rejected"])

        axiom_1 = _wrap_export(["AXIOM_HYP W_USED_1", "AXIOM_KIND W_USED_1 CORR BASE_RULE"], export_id="EU_A1")
        axiom_2 = _wrap_export(["AXIOM_HYP W_USED_2", "AXIOM_KIND W_USED_2 CORR BASE_RULE"], export_id="EU_A2")
        axiom_3 = _wrap_export(["AXIOM_HYP W_USED_3", "AXIOM_KIND W_USED_3 CORR BASE_RULE"], export_id="EU_A3")
        self.kernel.evaluate_export_block(axiom_1, self.state, batch_id="B2_USED")
        self.kernel.evaluate_export_block(axiom_2, self.state, batch_id="B3_USED")
        self.kernel.evaluate_export_block(axiom_3, self.state, batch_id="B4_USED")

        self.assertIn("P_USED_NOW", self.state.survivor_ledger)
        self.assertNotIn("P_USED_NOW", self.state.park_set)

    def test_defined_id_accepts_prior_header_even_if_rejected(self):
        block = _wrap_export(
            [
                "PROBE_HYP P_OK",
                "PROBE_KIND P_OK CORR X",
                "ASSERT P_OK CORR EXISTS PROBE_TOKEN PT_P_OK",
                "SPEC_HYP S_BAD",
                "SPEC_KIND S_BAD CORR UNKNOWN_KIND",
                "SPEC_HYP S_FOLLOW",
                "SPEC_KIND S_FOLLOW CORR SIM_SPEC",
                "REQUIRES S_FOLLOW CORR S_BAD",
                "REQUIRES S_FOLLOW CORR P_OK",
                "DEF_FIELD S_FOLLOW CORR REQUIRES_EVIDENCE E_FOLLOW",
                "ASSERT S_FOLLOW CORR EXISTS EVIDENCE_TOKEN E_FOLLOW",
            ],
            export_id="E_DEFINED_HEADER",
        )
        result = self.kernel.evaluate_export_block(block, self.state, batch_id="DEFINED_HEADER")
        parked_reasons = {row["reason"] for row in result["parked"]}
        self.assertNotIn("FORWARD_DEPEND", parked_reasons)
        accepted_ids = {row["id"] for row in result["accepted"]}
        self.assertIn("S_FOLLOW", accepted_ids)
        self.assertEqual("PENDING_EVIDENCE", self.state.survivor_ledger["S_FOLLOW"]["status"])

    def test_prune_stale_undefined_term_use_park_entry(self):
        parked_id = "S_PARKED_TERM"
        parked_term = "nested_hopf_torus_constraint"
        self.state.park_set[parked_id] = {
            "id": parked_id,
            "class": "SPEC_HYP",
            "tag": "UNDEFINED_TERM_USE",
            "detail": "UNDEFINED_LEXEME:nested",
            "item_text": (
                f"SPEC_HYP {parked_id}\n"
                f"SPEC_KIND {parked_id} CORR TERM_DEF\n"
                f"DEF_FIELD {parked_id} CORR TERM \"{parked_term}\"\n"
            ),
        }
        self.state.term_registry["nested"] = {"state": "CANONICAL_ALLOWED"}
        self.state.term_registry[parked_term] = {"state": "CANONICAL_ALLOWED"}

        self.kernel._prune_resolved_park_entries(self.state)

        self.assertNotIn(parked_id, self.state.park_set)

    def test_probe_term_allows_canonical_compound_term_without_segment_split(self):
        self.state.term_registry["correlation_polarity"] = {"state": "CANONICAL_ALLOWED"}
        block = _wrap_export(
            [
                "PROBE_HYP P_CORR_POL",
                "PROBE_KIND P_CORR_POL CORR UTIL_TEST",
                "ASSERT P_CORR_POL CORR EXISTS PROBE_TOKEN PT_P_CORR_POL",
                "SPEC_HYP S_CORR_POL_SIM",
                "SPEC_KIND S_CORR_POL_SIM CORR SIM_SPEC",
                "REQUIRES S_CORR_POL_SIM CORR P_CORR_POL",
                "DEF_FIELD S_CORR_POL_SIM CORR PROBE_TERM correlation_polarity",
                "DEF_FIELD S_CORR_POL_SIM CORR REQUIRES_EVIDENCE E_CORR_POL",
                "ASSERT S_CORR_POL_SIM CORR EXISTS EVIDENCE_TOKEN E_CORR_POL",
            ],
            export_id="E_CORR_POL_SIM",
        )

        result = self.kernel.evaluate_export_block(block, self.state, batch_id="B_CORR_POL")

        self.assertEqual([], result["rejected"])
        accepted_ids = {row["id"] for row in result["accepted"]}
        self.assertIn("S_CORR_POL_SIM", accepted_ids)


if __name__ == "__main__":
    unittest.main()
