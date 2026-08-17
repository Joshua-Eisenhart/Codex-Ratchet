from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.score_estate import _active_wave_paths, _json_out


def test_pretty_printed_receipt_is_not_read_from_the_last_brace() -> None:
    pretty = json.dumps({"status": "BOUNDED_SAT", "witness_checks": [{"holds": True}]}, indent=2)
    proc = SimpleNamespace(stdout=pretty + "\n", stderr="")
    assert _json_out(proc)["status"] == "BOUNDED_SAT"


def test_self_loop_state_is_not_tmp_or_mutable_score_flags() -> None:
    root = Path(__file__).resolve().parents[1]
    score_source = (root / "scripts" / "score_estate.py").read_text(encoding="utf-8")
    loop_source = (root / "scripts" / "run_self_loop.py").read_text(encoding="utf-8")
    assert "/tmp/cb-wave-self-loop" not in score_source + loop_source
    assert "score_flags.json" not in score_source + loop_source
    assert "CB_WAVE_SELF_LOOP_STATE_DIR" in score_source
    assert "CB_WAVE_SELF_LOOP_STATE_DIR" in loop_source


def test_active_wave_manifest_excludes_authored_only_specs() -> None:
    paths, zip_path, digest = _active_wave_paths()
    names = {path.parent.name for path in paths}
    assert names == {
        "cb-context-strategy-wave",
        "cb-exploration-wave",
        "cb-goodhart-wave",
        "cb-object-loop-wave",
        "cb-maintenance-wave",
    }
    assert zip_path.parent.name == "zip-failure-wave"
    assert len(digest) == 64
