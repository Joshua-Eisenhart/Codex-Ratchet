import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from gateway import BootpackBGateway
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


def _math_def_block(spec_id: str, export_id: str, objects_value: str = "density matrix operator") -> str:
    probe_id = f"P_{spec_id}"
    return _wrap_export(
        [
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
        ],
        export_id=export_id,
    )


class TestBootpackGateway(unittest.TestCase):
    def setUp(self):
        self.state = KernelState()
        self.gateway = BootpackBGateway(kernel=BootpackBKernel(), now_utc_fn=lambda: "2026-02-21T00:00:00Z")

    def test_message_type_rejects_prose(self):
        result = self.gateway.handle_message("hello world\n", self.state, batch_id="MSG_001")
        self.assertEqual("REJECT", result["status"])
        self.assertEqual("MULTI_ARTIFACT_OR_PROSE", result["tag"])
        self.assertIn("BOOT_ID: BOOTPACK_THREAD_B_v3.9.13", result["output_text"])

    def test_save_snapshot_command_has_metadata_and_lexicographic_order(self):
        block_b = _math_def_block("S_MATH_B", export_id="E_B")
        block_a = _math_def_block("S_MATH_A", export_id="E_A")
        self.gateway.handle_message(block_b, self.state, batch_id="B")
        self.gateway.handle_message(block_a, self.state, batch_id="A")

        command_result = self.gateway.handle_message("REQUEST SAVE_SNAPSHOT\n", self.state, batch_id="SNAP")
        output = command_result["output_text"]
        self.assertIn("BOOT_ID: BOOTPACK_THREAD_B_v3.9.13", output)
        self.assertIn("TIMESTAMP_UTC: 2026-02-21T00:00:00Z", output)
        self.assertLess(output.index("SPEC_HYP S_MATH_A"), output.index("SPEC_HYP S_MATH_B"))

    def test_export_report_echoes_offender_detail(self):
        bad_block = _math_def_block("S_MATH_BAD", export_id="E_BAD", objects_value="map")
        result = self.gateway.handle_message(bad_block, self.state, batch_id="BAD")
        output = result["output_text"]
        self.assertEqual("FAIL", result["status"])
        self.assertIn("EXPORT_ID: E_BAD", output)
        self.assertIn("RULESET_HEADER_MATCH UNKNOWN", output)
        self.assertIn('OFFENDER_RULE "BR-0D1"', output)
        self.assertIn('OFFENDER_LITERAL "map"', output)

    def test_snapshot_requires_verbatim_item_header(self):
        snapshot_text = "\n".join(
            [
                "BEGIN THREAD_S_SAVE_SNAPSHOT v2",
                "BOOT_ID: BOOTPACK_THREAD_B_v3.9.13",
                "TIMESTAMP_UTC: 2026-02-21T00:00:00Z",
                "SURVIVOR_LEDGER:",
                "  EMPTY",
                "PARK_SET:",
                "  EMPTY",
                "TERM_REGISTRY:",
                "EVIDENCE_PENDING:",
                "PROVENANCE:",
                "  ACCEPTED_BATCH_COUNT=0",
                "  UNCHANGED_LEDGER_STREAK=0",
                "END THREAD_S_SAVE_SNAPSHOT v2",
                "",
            ]
        )
        result = self.gateway.handle_message(snapshot_text, self.state, batch_id="SNAP_BAD")
        self.assertEqual("REJECT", result["status"])
        self.assertEqual("SNAPSHOT_NONVERBATIM", result["tag"])

    def test_dump_terms_uses_required_format(self):
        self.gateway.handle_message(_math_def_block("S_MATH_TERM", export_id="M1"), self.state, batch_id="M1")
        term_block = _wrap_export(
            [
                "PROBE_HYP P_TERM_DENSITY_MATRIX",
                "PROBE_KIND P_TERM_DENSITY_MATRIX CORR TERM_VALIDATION",
                "ASSERT P_TERM_DENSITY_MATRIX CORR EXISTS PROBE_TOKEN PT_P_TERM_DENSITY_MATRIX",
                "SPEC_HYP S_TERM_DENSITY_MATRIX",
                "SPEC_KIND S_TERM_DENSITY_MATRIX CORR TERM_DEF",
                "REQUIRES S_TERM_DENSITY_MATRIX CORR S_MATH_TERM",
                'DEF_FIELD S_TERM_DENSITY_MATRIX CORR TERM "density_matrix"',
                "DEF_FIELD S_TERM_DENSITY_MATRIX CORR BINDS S_MATH_TERM",
                "ASSERT S_TERM_DENSITY_MATRIX CORR EXISTS TERM_TOKEN TT_DENSITY_MATRIX",
            ],
            export_id="TERM_1",
        )
        self.gateway.handle_message(term_block, self.state, batch_id="TERM_1")
        output = self.gateway.handle_message("REQUEST DUMP_TERMS\n", self.state, batch_id="TERMS")["output_text"]
        self.assertIn("TERM density_matrix STATE TERM_PERMITTED BINDS S_MATH_TERM REQUIRED_EVIDENCE EMPTY", output)

    def test_header_gate_echo_false_when_ruleset_header_missing(self):
        self.state.active_ruleset_sha256 = "3" * 64
        block = _math_def_block("S_MATH_GATE", export_id="GATE_1")
        output = self.gateway.handle_message(block, self.state, batch_id="GATE")["output_text"]
        self.assertIn("RULESET_HEADER_MATCH FALSE", output)


if __name__ == "__main__":
    unittest.main()
