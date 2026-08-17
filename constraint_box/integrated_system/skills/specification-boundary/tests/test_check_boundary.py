from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_boundary import check


def test_fence_and_forbidden() -> None:
    spec = {
        "objective": "honest Light verbs",
        "non_objectives": ["Heavy engines"],
        "forbidden": ["git rebase"],
        "irreversible": ["push to origin"],
        "unlicensed_claims": ["canonical"],
    }
    assert check(spec)["status"] == "INSIDE"
    assert check(spec, {"text": "git rebase then call it canonical"})["status"] == "REFUSE"
