from __future__ import annotations

import json
from pathlib import Path

from spinor_network_surface_v0_common import core_surface_result


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "spinor_network_surface_v0"
RESULT_DIR = SIM_DIR / "results"


def test_core_surface_contract_nontrivial_chart_and_basin() -> None:
    core = core_surface_result()
    assert core["all_pass"] is True
    assert core["carrier"]["dimension"] == 16
    assert core["coupling"]["hermitian_residual"] <= 1.0e-10
    assert core["basin_contract"]["stored_patterns_all_trapping"] is True
    assert core["basin_contract"]["spurious_attractors_found"]
    assert core["chart_recoverability"]["verdict"] == "partial_recovery_nontrivial"
    assert core["chart_recoverability"]["recovered_cell_count"] > 1
    assert core["typed_information"]["bipartition_declared"] == {"A": [0], "B": [1, 2, 3]}
    assert core["lr_hook"]["distinguishable_under_probe"] is True


def test_envelope_result_has_required_builder_gates() -> None:
    path = RESULT_DIR / "spinor_network_surface_v0_envelope_results.json"
    assert path.is_file()
    env = json.loads(path.read_text(encoding="utf-8"))
    assert env["classification"] == "scratch_diagnostic"
    assert env["promotion_allowed"] is False
    assert env["formal_admission_allowed"] is False
    assert env["no_builder_audit_verdict"] is True
    assert env["all_pass"] is True
    assert set(env["engines"]) == {"julia", "jax", "pytorch"}
    assert env["tool_intent"]["claim_classes"]
    assert env["controls"]["non_hermitian_coupling_control"]["lyapunov_row_breaks"] is True
    assert env["controls"]["pattern_overload_boundary"]["retrieval_degrades"] is True

