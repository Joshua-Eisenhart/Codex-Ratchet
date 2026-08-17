from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.judge_rederivation import judge


def test_llm_only_and_dualsolve() -> None:
    assert judge({"verifiers": ["grok", "claude", "luna"]})["reason"] == "REFUSE_LAUNDERED_CONSENSUS"
    assert judge({"verifiers": ["z3", "cvc5"]})["status"] == "REPLAYED"
