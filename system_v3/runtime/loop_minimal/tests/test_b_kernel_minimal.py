import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from b_kernel import BKernel
from state import KernelState


def _load_fixture(name: str) -> str:
    return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")


class TestBKernelMinimal(unittest.TestCase):
    def test_accept_sim_spec_bind(self):
        block = _load_fixture("sim_spec_bind_pass.txt")
        state = KernelState()
        kernel = BKernel()
        result = kernel.evaluate_export_block(block, state)
        self.assertIn("S_BIND_MS_A_FULL16X4", result["accepted"])
        self.assertIn("P94_FULL16X4_ENGINE_PROBE", result["accepted"])
        self.assertIn("S_BIND_MS_A_FULL16X4", state.evidence_pending)

    def test_reject_unsupported_spec_kind(self):
        block = _load_fixture("sim_spec_bad_kind.txt")
        state = KernelState()
        kernel = BKernel()
        result = kernel.evaluate_export_block(block, state)
        rejected = {r["id"] for r in result["rejected"]}
        self.assertIn("S_BIND_MS_A_FULL16X4", rejected)


if __name__ == "__main__":
    unittest.main()
