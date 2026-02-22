import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from gateway import BootpackBGateway
from kernel import BootpackBKernel
from state import KernelState


def _wrap_export(content_lines: list[str], export_id: str = "EDGE") -> str:
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


class TestKernelEdgeCases(unittest.TestCase):
    def setUp(self):
        self.state = KernelState()
        self.kernel = BootpackBKernel()
        self.gateway = BootpackBGateway(kernel=self.kernel, now_utc_fn=lambda: "2026-02-21T00:00:00Z")

    def test_reject_unsupported_spec_kind(self):
        block = _wrap_export(
            [
                "SPEC_HYP S_BAD_KIND",
                "SPEC_KIND S_BAD_KIND CORR UNKNOWN_KIND",
            ],
            export_id="EDGE_BAD_KIND",
        )
        result = self.kernel.evaluate_export_block(block, self.state, batch_id="EDGE_BAD_KIND")
        self.assertEqual(1, len(result["rejected"]))
        self.assertEqual("SCHEMA_FAIL", result["rejected"][0]["reason"])

    def test_park_forward_dependency(self):
        block = _wrap_export(
            [
                "PROBE_HYP P_DEP",
                "PROBE_KIND P_DEP CORR X",
                "ASSERT P_DEP CORR EXISTS PROBE_TOKEN PT_P_DEP",
                "SPEC_HYP S_DEP",
                "SPEC_KIND S_DEP CORR SIM_SPEC",
                "REQUIRES S_DEP CORR P_MISSING",
                "DEF_FIELD S_DEP CORR REQUIRES_EVIDENCE E_DEP",
                "ASSERT S_DEP CORR EXISTS EVIDENCE_TOKEN E_DEP",
            ],
            export_id="EDGE_FORWARD_DEP",
        )
        result = self.kernel.evaluate_export_block(block, self.state, batch_id="EDGE_FORWARD_DEP")
        self.assertEqual(1, len(result["parked"]))
        self.assertEqual("FORWARD_DEPEND", result["parked"][0]["reason"])

    def test_park_sim_spec_missing_evidence(self):
        block = _wrap_export(
            [
                "PROBE_HYP P_SIM",
                "PROBE_KIND P_SIM CORR X",
                "ASSERT P_SIM CORR EXISTS PROBE_TOKEN PT_P_SIM",
                "SPEC_HYP S_SIM",
                "SPEC_KIND S_SIM CORR SIM_SPEC",
                "REQUIRES S_SIM CORR P_SIM",
            ],
            export_id="EDGE_SIM_MISSING_EVIDENCE",
        )
        result = self.kernel.evaluate_export_block(block, self.state, batch_id="EDGE_SIM_MISSING_EVIDENCE")
        self.assertEqual(1, len(result["parked"]))
        self.assertEqual("SCHEMA_FAIL", result["parked"][0]["reason"])

    def test_reject_comment_in_artifact(self):
        block = _wrap_export(
            [
                "# bad comment",
                "SPEC_HYP S_X",
                "SPEC_KIND S_X CORR SIM_SPEC",
                "DEF_FIELD S_X CORR REQUIRES_EVIDENCE E_X",
                "ASSERT S_X CORR EXISTS EVIDENCE_TOKEN E_X",
            ],
            export_id="EDGE_COMMENT",
        )
        result = self.kernel.evaluate_export_block(block, self.state, batch_id="EDGE_COMMENT")
        self.assertEqual(1, len(result["rejected"]))
        self.assertEqual("COMMENT_BAN", result["rejected"][0]["reason"])

    def test_gateway_rejects_multi_artifact_message(self):
        text = "\n".join(
            [
                _wrap_export(["SPEC_HYP S_A", "SPEC_KIND S_A CORR SIM_SPEC", "DEF_FIELD S_A CORR REQUIRES_EVIDENCE E_A", "ASSERT S_A CORR EXISTS EVIDENCE_TOKEN E_A"], export_id="A").strip(),
                _wrap_export(["SPEC_HYP S_B", "SPEC_KIND S_B CORR SIM_SPEC", "DEF_FIELD S_B CORR REQUIRES_EVIDENCE E_B", "ASSERT S_B CORR EXISTS EVIDENCE_TOKEN E_B"], export_id="B").strip(),
                "",
            ]
        )
        out = self.gateway.handle_message(text, self.state, batch_id="EDGE_MULTI")
        self.assertEqual("REJECT", out["status"])
        self.assertEqual("MULTI_ARTIFACT_OR_PROSE", out["tag"])


if __name__ == "__main__":
    unittest.main()
