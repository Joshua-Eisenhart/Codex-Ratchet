import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import hashlib
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a0_compiler import compile_export_block
from a1_adapter import load_strategy_artifact


class TestA0CompilerDeterminism(unittest.TestCase):
    def test_same_inputs_identical_bytes(self):
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        artifact = load_strategy_artifact(strategy_path)
        state_hash = hashlib.sha256(b"canonical_state").hexdigest()
        compiler_version = "A0_COMPILER_v1"

        out1 = compile_export_block(state_hash, artifact["strategy"], compiler_version)
        out2 = compile_export_block(state_hash, artifact["strategy"], compiler_version)

        self.assertEqual(out1["export_block_bytes"], out2["export_block_bytes"])
        self.assertEqual(out1["report"], out2["report"])


if __name__ == "__main__":
    unittest.main()
