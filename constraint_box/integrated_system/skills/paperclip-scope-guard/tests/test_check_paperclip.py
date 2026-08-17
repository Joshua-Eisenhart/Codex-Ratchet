from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_paperclip import check


def test_nine_files_is_paperclip() -> None:
    receipt = check({"files_touched": [f"f{i}" for i in range(9)]})
    assert receipt["reason"] == "REFUSE_PAPERCLIP"


def test_untested_wave_is_paperclip() -> None:
    receipt = check({"new_waves": [{"name": "cb-fake-wave", "has_tests": False}]})
    assert receipt["status"] == "REFUSE"


def test_small_tested_mutation_is_clean() -> None:
    receipt = check(
        {
            "files_touched": ["a.py", "b.py"],
            "new_waves": [{"name": "cb-goodhart-wave", "has_tests": True}],
            "promotion_allowed": False,
            "claim_ceiling": "bounded keep/discard only; not promotion",
        }
    )
    assert receipt["status"] == "SCOPE_CLEAN"
