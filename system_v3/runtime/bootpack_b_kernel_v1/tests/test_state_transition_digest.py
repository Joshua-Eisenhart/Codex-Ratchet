import json
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from a0_compiler import compute_state_transition_digest
from a1_a0_b_sim_runner import run_loop


class TestStateTransitionDigest(unittest.TestCase):
    def _digest_chain(self, run_dir: Path) -> list[str]:
        payload = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        rows = payload.get("canonical_ledger", [])
        return [str(row.get("state_transition_digest", "")) for row in rows]

    def test_identical_replay_produces_identical_transition_digest_chain(self):
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        run_a, _ = run_loop(
            strategy_path=strategy_path,
            steps=3,
            run_id="TEST_STATE_TRANSITION_CHAIN_A",
            a1_source="replay",
            a1_model="",
            a1_timeout_sec=1,
            clean=True,
        )
        run_b, _ = run_loop(
            strategy_path=strategy_path,
            steps=3,
            run_id="TEST_STATE_TRANSITION_CHAIN_B",
            a1_source="replay",
            a1_model="",
            a1_timeout_sec=1,
            clean=True,
        )

        chain_a = self._digest_chain(run_a)
        chain_b = self._digest_chain(run_b)
        self.assertGreaterEqual(len(chain_a), 1)
        self.assertEqual(chain_a, chain_b)

    def test_changing_export_block_hash_changes_transition_digest(self):
        strategy_path = BASE / "a1_strategies" / "sample_strategy.json"
        run_dir, _ = run_loop(
            strategy_path=strategy_path,
            steps=1,
            run_id="TEST_STATE_TRANSITION_MUTATION",
            a1_source="replay",
            a1_model="",
            a1_timeout_sec=1,
            clean=True,
        )
        payload = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
        row = dict(payload.get("canonical_ledger", [])[0])
        export_block_hash = str(row.get("export_block_hash", ""))
        mutated_export_hash = ("0" if export_block_hash[:1] != "0" else "1") + export_block_hash[1:]
        mutated_digest = compute_state_transition_digest(
            previous_state_hash=str(row.get("previous_state_hash", "")),
            export_block_hash=mutated_export_hash,
            snapshot_hash=str(row.get("snapshot_hash", "")),
            compiler_version=str(row.get("compiler_version", "")),
        )
        self.assertNotEqual(str(row.get("state_transition_digest", "")), mutated_digest)


if __name__ == "__main__":
    unittest.main()
