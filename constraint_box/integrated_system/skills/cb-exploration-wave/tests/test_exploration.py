from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_exploration import run_wave


def _seed(tmp_path: Path) -> Path:
    root = tmp_path / "box"
    seed = root / "fixtures" / "cr" / "manifold_time_first_seed_v1.json"
    seed.parent.mkdir(parents=True)
    seed.write_text(json.dumps({"foundation_id": "time-first-dual-opening-v1"}), encoding="utf-8")
    return root


def test_open_antichain_keeps_more_than_one_family(tmp_path: Path) -> None:
    root = _seed(tmp_path)
    receipt = run_wave(
        root=root,
        seed=Path("fixtures/cr/manifold_time_first_seed_v1.json"),
        out=tmp_path / "out" / "receipt.json",
    )
    assert receipt["status"] == "ANTICHAIN_OPEN"
    assert receipt["winner_selected"] is False
    assert receipt["reading_count"] >= 2
    assert receipt["family_count"] >= 2
    antichain = json.loads(Path(receipt["antichain_draft"]).read_text(encoding="utf-8"))
    assert antichain["winner_selected"] is False
    assert "R-lr-two-manifolds" in receipt["antichain_ids"]
    packet = json.loads(Path(receipt["distinguish_packet"]).read_text(encoding="utf-8"))
    assert packet["schema"] == "constraintbox.distinguishability.packet.v1"
    assert packet["authority"] == "none"
    assert len(packet["candidates"]) == 2


def test_pick_winner_and_falsify_refuse(tmp_path: Path) -> None:
    root = _seed(tmp_path)
    seed = Path("fixtures/cr/manifold_time_first_seed_v1.json")
    winner = run_wave(
        root=root,
        seed=seed,
        out=tmp_path / "winner.json",
        pick_winner=True,
    )
    assert winner["status"] == "REFUSE"
    assert winner["reason"] == "REFUSE_WINNER"
    killed = run_wave(
        root=root,
        seed=seed,
        out=tmp_path / "kill.json",
        falsify=True,
    )
    assert killed["status"] == "REFUSE"
    assert killed["reason"] == "REFUSE_DEDUCTION_ON_INDUCTION"


def test_single_family_holds(tmp_path: Path) -> None:
    root = _seed(tmp_path)
    readings = tmp_path / "one.json"
    readings.write_text(
        json.dumps(
            [
                {"id": "R1", "family": "only", "text": "one future"},
                {"id": "R2", "family": "only", "text": "same family"},
            ]
        ),
        encoding="utf-8",
    )
    receipt = run_wave(
        root=root,
        seed=Path("fixtures/cr/manifold_time_first_seed_v1.json"),
        out=tmp_path / "hold.json",
        readings_path=readings,
    )
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_COLLAPSED_DIVERSITY"
