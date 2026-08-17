from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "structured_open_bind_probe.py"
FIXTURE = ROOT / "fixtures" / "structured_open_bind_v1.json"
SPEC = importlib.util.spec_from_file_location("structured_open_bind_probe", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_exact_structured_family_has_gap_and_commuting_controls() -> None:
    result = probe.evaluate(fixture(), engine="exact")
    assert result["status"] == "PASS"
    assert result["finding"] == "STRUCTURED_FAMILY_DIFFERS_FROM_RANDOM_MASKS"
    assert result["controls"]["all_pass"] is True
    assert result["structured"]["structured_noncontrol_gap_rate"] < result["structured"]["random_mask_gap_rate"]
    assert result["generic_endomap_control"]["pair_count"] == 65536
    assert result["generic_endomap_control"]["noncommuting_rate"] > 0.95
    assert "order gap is chirality" in result["forbidden_inferences"]


def test_missing_observation_refuses_before_map_construction() -> None:
    raw = fixture()
    raw["observations"] = raw["observations"][:-1]
    result = probe.evaluate(raw, engine="exact")
    assert result["status"] == "REFUSE"
    assert result["reason_code"] == "REFUSE_UNBOUND_OBSERVATION"


def test_identity_only_family_holds_missing_diversity() -> None:
    raw = fixture()
    raw["bind_candidates"] = [raw["bind_candidates"][-1]]
    result = probe.evaluate(raw, engine="exact")
    assert result["status"] == "HOLD"
    assert result["controls"]["structured_has_gap_case"] is False


def test_relabel_control_changes_names_not_metrics() -> None:
    validated = probe.validate_fixture(fixture())
    before = probe.structured_metrics(validated)
    after = probe.structured_metrics(probe.relabel_fixture(validated))
    assert before["structured_noncontrol_gap_count"] == after["structured_noncontrol_gap_count"]
    assert before["random_mask_gap_count"] == after["random_mask_gap_count"]
