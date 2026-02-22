import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from kernel import BootpackBKernel
from state import KernelState


def _evidence_block(
    sim_id: str = "S_SIM_ALPHA",
    code_hash: str = "a" * 64,
    input_hash: str = "b" * 64,
    output_hash: str = "c" * 64,
    manifest_hash: str = "d" * 64,
    extra_lines: list[str] | None = None,
) -> str:
    lines = [
        "BEGIN SIM_EVIDENCE v1",
        f"SIM_ID: {sim_id}",
        f"CODE_HASH_SHA256: {code_hash}",
        f"INPUT_HASH_SHA256: {input_hash}",
        f"OUTPUT_HASH_SHA256: {output_hash}",
        f"RUN_MANIFEST_SHA256: {manifest_hash}",
    ]
    if extra_lines:
        lines.extend(extra_lines)
    lines.append("END SIM_EVIDENCE v1")
    lines.append("")
    return "\n".join(lines)


class TestSimEvidenceContract(unittest.TestCase):
    def setUp(self):
        self.kernel = BootpackBKernel()
        self.state = KernelState()

    def test_valid_block_accepts(self):
        result = self.kernel.ingest_sim_evidence_pack(_evidence_block(), self.state, batch_id="SIM_OK")
        self.assertEqual("OK", result["status"])

    def test_missing_field_rejects(self):
        text = "\n".join(
            [
                "BEGIN SIM_EVIDENCE v1",
                "SIM_ID: S_SIM_ALPHA",
                f"CODE_HASH_SHA256: {'a' * 64}",
                f"INPUT_HASH_SHA256: {'b' * 64}",
                f"RUN_MANIFEST_SHA256: {'d' * 64}",
                "END SIM_EVIDENCE v1",
                "",
            ]
        )
        result = self.kernel.ingest_sim_evidence_pack(text, self.state, batch_id="SIM_MISSING")
        self.assertEqual("REJECT", result["status"])

    def test_invalid_hash_rejects(self):
        result = self.kernel.ingest_sim_evidence_pack(
            _evidence_block(output_hash="Z" * 64), self.state, batch_id="SIM_HASH"
        )
        self.assertEqual("REJECT", result["status"])

    def test_comment_rejects(self):
        result = self.kernel.ingest_sim_evidence_pack(
            _evidence_block(extra_lines=["# comment not allowed"]), self.state, batch_id="SIM_COMMENT"
        )
        self.assertEqual("REJECT", result["status"])

    def test_extra_text_rejects(self):
        result = self.kernel.ingest_sim_evidence_pack(
            _evidence_block(extra_lines=["EXTRA_FIELD: NOPE"]), self.state, batch_id="SIM_EXTRA"
        )
        self.assertEqual("REJECT", result["status"])

    def test_duplicate_sim_id_in_pack_rejects(self):
        pack = _evidence_block(sim_id="S_DUP") + _evidence_block(sim_id="S_DUP")
        result = self.kernel.ingest_sim_evidence_pack(pack, self.state, batch_id="SIM_DUP")
        self.assertEqual("REJECT", result["status"])

    def test_evidence_signal_sim_id_mismatch_rejects(self):
        block = _evidence_block(sim_id="S_ONE", extra_lines=["EVIDENCE_SIGNAL S_TWO CORR E_TOKEN"])
        result = self.kernel.ingest_sim_evidence_pack(block, self.state, batch_id="SIM_SIGNAL_MISMATCH")
        self.assertEqual("REJECT", result["status"])

    def test_duplicate_required_field_rejects(self):
        block = _evidence_block(extra_lines=[f"OUTPUT_HASH_SHA256: {'f' * 64}"])
        result = self.kernel.ingest_sim_evidence_pack(block, self.state, batch_id="SIM_DUP_FIELD")
        self.assertEqual("REJECT", result["status"])


if __name__ == "__main__":
    unittest.main()
