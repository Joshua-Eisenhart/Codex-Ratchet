from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_wizard_proof_manifest.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_wizard_proof_manifest", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_gates_are_explicit_and_nonempty():
    mod = load_module()
    gates = mod.default_gates()

    assert [gate["id"] for gate in gates] == [
        "wiki_lproof_gate",
        "wizard_receipt_gate",
        "weyl_graph_proof_gate",
    ]
    for gate in gates:
        assert gate["command"]
        assert gate["expected_exit"] == 0
        assert gate["evidence"]


def test_weyl_graph_inline_check_imports_json():
    mod = load_module()

    assert "import json" in mod.WEYL_GRAPH_CHECK
