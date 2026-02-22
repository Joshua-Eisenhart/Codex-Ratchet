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


class TestSimSpecBindFixture(unittest.TestCase):
    def test_fixture_passes_b_kernel(self):
        fixture = (Path(__file__).parent / "fixtures" / "sim_spec_bind_pass.txt").read_text(encoding="utf-8")
        kernel = BKernel()
        state = KernelState()
        result = kernel.evaluate_export_block(fixture, state)

        self.assertEqual([], result["rejected"])
        self.assertIn("P94_FULL16X4_ENGINE_PROBE", result["accepted"])
        self.assertIn("S_BIND_MS_A_FULL16X4", result["accepted"])
        self.assertIn("S_BIND_MS_A_FULL16X4", state.evidence_pending)


if __name__ == "__main__":
    unittest.main()
