from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.bind import bind_tools, bind_wave


def test_named_only_tools_refuse() -> None:
    assert bind_tools(["context_diff"])["reason"] == "REFUSE_UNBOUND_TOOLS"


def test_sha256_binds() -> None:
    assert bind_tools(["sha256"])["status"] == "BOUND"
