import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gcm_constraint_carve_floor_v0 as carve


def test_candidate_space_and_constraints_are_explicit_and_biting():
    result = carve.build_result(write=False)

    assert result["object_id"] == "gcm_constraint_carve_floor_v0"
    assert result["classification"] == "scratch_diagnostic"
    assert result["promotion_allowed"] is False
    assert result["formal_admission_allowed"] is False
    assert result["axis_claims_allowed"] is False
    assert result["engine_claims_allowed"] is False

    assert result["candidate_space"]["state_count"] == 24
    assert result["constraint_carve"]["survivor_count"] == 6
    assert result["constraint_carve"]["killed_count"] == 18
    assert result["quotient"]["class_count"] == 6

    constraints = {row["id"]: row for row in result["constraints"]}
    assert set(constraints) == {
        "C_history_consistency",
        "C_N01_order_visible",
        "C_closure_under_order_maps",
    }
    for row in constraints.values():
        assert row["source_anchor"]
        assert row["operation"]
        assert row["observable"]
        assert row["pass_fail_condition"]

    controls = result["controls"]
    assert controls["empty_C"]["survivor_count"] == 24
    assert controls["drop_C_history_consistency"]["survivor_count"] == 12
    assert controls["drop_C_N01_order_visible"]["survivor_count"] == 12
    assert controls["drop_C_closure_under_order_maps"]["survivor_count"] == 10
    assert controls["overconstrained_orientation_one_only"]["survivor_count"] == 0


def test_survivors_are_closed_under_order_sensitive_maps_and_have_kill_ledger():
    result = carve.build_result(write=False)
    survivors = {tuple(row["state"]) for row in result["constraint_carve"]["survivors"]}

    assert survivors == {
        (0, 0, 0, 0),
        (0, 1, 0, 1),
        (1, 0, 0, 1),
        (1, 1, 0, 0),
        (2, 0, 0, 0),
        (2, 1, 0, 1),
    }

    for row in result["constraint_carve"]["survivors"]:
        assert tuple(row["R"] ) in survivors
        assert tuple(row["D"] ) in survivors
        assert tuple(row["R_after_D"] ) in survivors
        assert tuple(row["D_after_R"] ) in survivors
        assert row["order_gap_visible"] is True

    kill_rows = result["constraint_carve"]["kill_ledger"]
    assert len(kill_rows) == 18
    assert all(row["failed_constraints"] for row in kill_rows)
    assert any("C_history_consistency" in row["failed_constraints"] for row in kill_rows)
    assert any("C_closure_under_order_maps" in row["failed_constraints"] for row in kill_rows)


def test_probe_quotient_and_carved_structure_are_read_off_not_installed():
    result = carve.build_result(write=False)

    quotient = result["quotient"]
    assert quotient["probe_family"] == ["shell", "phase_parity", "orientation", "memory"]
    assert quotient["class_count"] == 6
    assert all(len(row["members"]) == 1 for row in quotient["classes"])

    erasure = result["probe_erasure_controls"]
    assert erasure["full_probe"]["class_count"] == 6
    assert erasure["erase_shell"]["class_count"] == 4
    assert erasure["erase_phase_parity"]["class_count"] == 6

    structure = result["carved_structure"]
    assert structure["component_count"] == 1
    assert structure["largest_component_size"] == 6
    assert structure["terrain_readout_attempt"]["verdict"] == "no_8_terrain_regions_in_this_floor"
    assert structure["terrain_readout_attempt"]["region_count"] == 1
    assert "read off survivor graph" in structure["terrain_readout_attempt"]["method"]


def test_script_writes_result_and_validator_accepts_it(tmp_path):
    out = tmp_path / "result.json"
    subprocess.run([sys.executable, str(ROOT / "gcm_constraint_carve_floor_v0.py"), "--output", str(out)], check=True)
    data = json.loads(out.read_text())
    assert data["all_pass"] is True

    validator = ROOT / "validate_gcm_constraint_carve_floor_v0.py"
    subprocess.run([sys.executable, str(validator), str(out)], check=True)
