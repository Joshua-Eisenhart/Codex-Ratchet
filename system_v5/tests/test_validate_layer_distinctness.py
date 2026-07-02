#!/usr/bin/env python3
"""Spec-lock for scripts/validate_layer_distinctness.py.

Each test constructs a synthetic receipt exhibiting exactly one theater pattern and
asserts the gate flags it HARD, plus one clean receipt the gate must pass. Run with
the repo interpreter: ``python3 -m pytest system_v5/tests/test_validate_layer_distinctness.py``
or directly ``python3 system_v5/tests/test_validate_layer_distinctness.py``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = REPO_ROOT / "scripts" / "validate_layer_distinctness.py"

_spec = importlib.util.spec_from_file_location("layer_distinctness_gate", GATE_PATH)
gate = importlib.util.module_from_spec(_spec)
sys.modules["layer_distinctness_gate"] = gate  # let dataclass introspection resolve the module
_spec.loader.exec_module(gate)


def _write(tmp: Path, name: str, data: dict) -> Path:
    path = tmp / name
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _codes(report: dict, layer: str | None = None) -> set[str]:
    out = set()
    for v in report["violations"]:
        if layer is None or (v.get("layer") or "").startswith(layer):
            out.add(v["code"])
    return out


def _clean_fsn(layer: str, mi: float) -> dict:
    """A receipt with a distinct signature, real witnesses, varying scale, enough controls."""
    return {
        "summary": {
            "layer": layer, "elapsed_seconds": 1.0, "max_sites": 64,
            "min_entanglement_gap_vs_product_mps": 1.5 + mi,
            "min_log_negativity": 0.3 + mi, "min_mutual_information": mi,
            "min_pyg_message_gap": 4.0 + mi,
            "min_control_gaps": {"phase_erased": 0.4 + mi, "order_reversed": 0.7 + mi,
                                 "scalar_entropy_primary": 1.1 + mi, "peps3d_erased": 2.2 + mi},
        },
        "tool_ablations": {
            "torch": {"non_vacuous": True, "pass": True,
                      "delta_witness": {"after_removal_gap": 0.9123 + mi}},
        },
        "rows": [
            {"site_count": 8, "mutual_information": 0.10 + mi, "von_neumann_entropy": 0.5 + mi},
            {"site_count": 64, "mutual_information": 0.40 + mi, "von_neumann_entropy": 0.9 + mi},
        ],
    }


def test_clean_receipt_passes(tmp_path):
    paths = [
        _write(tmp_path, "l6_clean_full_spinor_network_layer_probe_results.json", _clean_fsn("L6", 0.11)),
        _write(tmp_path, "l7_clean_full_spinor_network_layer_probe_results.json", _clean_fsn("L7", 0.29)),
    ]
    report = gate.evaluate(paths)
    assert report["ok"] is True, report["violations"]
    assert report["hard_violations"] == 0


def test_cross_layer_identity_is_hard(tmp_path):
    same = _clean_fsn("L0", 0.10)
    a = _write(tmp_path, "l0_x_full_spinor_network_layer_probe_results.json", same)
    b = _write(tmp_path, "l4_x_full_spinor_network_layer_probe_results.json", json.loads(json.dumps(same)))
    report = gate.evaluate([a, b])
    assert report["ok"] is False
    assert "cross_layer_signature_identity" in _codes(report)


def test_fabricated_ablation_after_zero_is_hard(tmp_path):
    data = _clean_fsn("L2", 0.22)
    data["ablation_outcome_delta"] = {
        t: {"control_gap_after_stub": 0.0, "control_gap_before": v, "delta_magnitude": v}
        for t, v in {"GUDHI": 14.0, "torch": 0.3, "z3": 8.0}.items()
    }
    p = _write(tmp_path, "l2_y_peps3d_bond4_tool_ablation_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "fabricated_ablation_after_zero" in _codes(report)
    assert report["ok"] is False


def test_asserted_ablation_no_witness_is_hard(tmp_path):
    data = _clean_fsn("L3", 0.31)
    data["tool_ablations"]["PEPS3D"] = {"non_vacuous": True, "pass": True, "stub_action": "erase"}
    p = _write(tmp_path, "l3_z_full_spinor_network_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "asserted_ablation_no_witness" in _codes(report)


def test_delta_witness_echoes_baseline_is_hard(tmp_path):
    data = _clean_fsn("L5", 0.55)
    base = data["summary"]["min_entanglement_gap_vs_product_mps"]
    data["tool_ablations"]["MPS"] = {"non_vacuous": True, "pass": True,
                                     "delta_witness": {"min_entanglement_gap": base}}
    p = _write(tmp_path, "l5_w_full_spinor_network_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "delta_witness_echoes_baseline" in _codes(report)


def test_vacuous_scale_ladder_is_hard(tmp_path):
    data = _clean_fsn("L8", 0.81)
    # identical physics across distinct site counts -> vacuous ladder
    data["rows"] = [
        {"site_count": 8, "mutual_information": 0.744, "min_quaternion_order_gap": 0.344, "cell_count": 1},
        {"site_count": 64, "mutual_information": 0.744, "min_quaternion_order_gap": 0.344, "cell_count": 27},
    ]
    p = _write(tmp_path, "l8_v_invariant_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "vacuous_scale_ladder" in _codes(report)


def test_insufficient_controls_is_hard(tmp_path):
    data = _clean_fsn("L1", 0.13)
    data["summary"]["min_control_gaps"] = {"only_one": 0.5, "and_two": 0.7}  # < 3 distinct
    p = _write(tmp_path, "l1_u_mps_peps2d_peps3d_depth_probe_results.json", data)
    report = gate.evaluate([p])
    assert "insufficient_nonvacuous_controls" in _codes(report)


def test_honest_fencing_is_soft_not_hard(tmp_path):
    """A vacuous control honestly fenced as diagnostic must NOT hard-fail on that control."""
    data = _clean_fsn("L7", 0.29)
    data["summary"]["min_control_gaps"]["phase_erased"] = 1e-16  # vacuous...
    data["weak_controls_flagged"] = [
        {"controls": {"phase_erased": 1e-16}, "status": "diagnostic_not_claim_bearing"}
    ]
    p = _write(tmp_path, "l7_t_full_spinor_network_layer_probe_results.json", data)
    report = gate.evaluate([p])
    codes = _codes(report)
    assert "vacuous_control_fenced" in codes          # reported...
    assert "vacuous_claim_bearing_control" not in codes  # ...but not hard on the fenced one


# --------------------------------------------------------------------------- hardening
# Added after the 2026-05-28 fresh-context audit found bypasses (l457-shape receipts) and
# false-positive risks (echo vs honest full-collapse; declared topological invariants).


def _l457_shape(layer: str, loop_gap: float, mi_vary: bool = True) -> dict:
    """A receipt shaped like the layer_l4_l5_l7_individual_runner output: bookkeeping-only
    summary, real gaps parked in controls.positive + rows[].layer_gate."""
    rows = []
    for i, n in enumerate((8, 16, 32, 64)):
        mi = 0.40 + (0.05 * i if mi_vary else 0.0)
        rows.append({"site_count": n, "layer_gate": {
            "max_fiber_shell_loop_order_gap": loop_gap,
            "mutual_information": mi, "cell_count": n // 8}})
    return {
        "summary": {"all_pass": True, "elapsed_seconds": 1.0, "max_qubits": 64,
                    "shell_count": 5, "phase_grid_count": 64, "row_count": 4},
        "controls": {
            "positive": {"N01_shell_loop_order_witness": {
                "max_fiber_shell_loop_order_gap": loop_gap, "pass": True}},
            "negative": {"fiber_order_control_collapses": {
                "max_fiber_shell_loop_order_gap": 0.0, "pass": True}},
        },
        "tool_ablations_by_tool": {
            "pytorch": {"non_vacuous": True, "pass": True,
                        "delta_witness": {"order_gap": loop_gap}},
        },
        "rows": rows,
    }


def test_l457_vacuous_positive_witness_is_hard(tmp_path):
    """The exact bypass: bookkeeping-only summary + a 0.0 positive claim witness."""
    p = _write(tmp_path, "l7_b_peps3d_bond4_tool_ablation_layer_probe_results.json",
               _l457_shape("L7", loop_gap=0.0))
    report = gate.evaluate([p])
    codes = _codes(report)
    assert "vacuous_claim_bearing_control" in codes      # positive witness gap 0.0 caught
    assert "no_observable_signature" not in codes        # surface exists, just vacuous
    assert report["ok"] is False


def test_l457_with_signal_still_catches_vacuous_ablation(tmp_path):
    """A non-zero loop gap clears the control check but the witness still echoes baseline."""
    p = _write(tmp_path, "l7_c_peps3d_bond4_tool_ablation_layer_probe_results.json",
               _l457_shape("L7", loop_gap=0.4442882938))
    report = gate.evaluate([p])
    # pytorch delta_witness.order_gap == the positive baseline loop gap, no after-removal value.
    assert "delta_witness_echoes_baseline" in _codes(report)


def test_no_observable_signature_is_hard(tmp_path):
    data = {"summary": {"all_pass": True, "max_qubits": 64, "shell_count": 5, "row_count": 4}}
    p = _write(tmp_path, "l7_d_full_spinor_network_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "no_observable_signature" in _codes(report)
    assert report["ok"] is False


def test_vacuous_ablation_witness_is_hard(tmp_path):
    data = _clean_fsn("L2", 0.22)
    data["tool_ablations_by_tool"] = {
        "GUDHI": {"non_vacuous": True, "pass": True, "delta_witness": {"max_gap": 0.0}},
    }
    p = _write(tmp_path, "l2_q_peps3d_bond4_tool_ablation_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "vacuous_ablation_witness" in _codes(report)


def test_vacuous_unfenced_control_is_hard(tmp_path):
    data = _clean_fsn("L3", 0.31)
    data["summary"]["min_control_gaps"]["dead_control"] = 1e-16  # unfenced, sub-floor
    p = _write(tmp_path, "l3_p_mps_peps2d_peps3d_depth_probe_results.json", data)
    report = gate.evaluate([p])
    assert "vacuous_claim_bearing_control" in _codes(report)


def test_honest_full_collapse_ablation_not_flagged(tmp_path):
    """A real |before-after| delta that equals a baseline must NOT be flagged when the
    receipt records an explicit after-removal value."""
    data = _clean_fsn("L6", 0.17)
    base = data["summary"]["min_entanglement_gap_vs_product_mps"]
    data["tool_ablations"]["MPS"] = {
        "non_vacuous": True, "pass": True, "after_removal": 0.0,
        "delta_witness": {"collapse_gap": base},  # == before, but after_removal proves it real
    }
    p = _write(tmp_path, "l6_o_full_spinor_network_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "delta_witness_echoes_baseline" not in _codes(report)


def test_declared_topological_invariant_scale_is_soft(tmp_path):
    data = _clean_fsn("L7", 0.29)
    data["expected_N_invariant"] = ["chern_flux_invariant"]
    data["rows"] = [
        {"site_count": 8, "chern_flux_invariant": 2.0, "mutual_information": 0.30},
        {"site_count": 64, "chern_flux_invariant": 2.0, "mutual_information": 0.55},
    ]
    p = _write(tmp_path, "l7_n_full_spinor_network_layer_probe_results.json", data)
    report = gate.evaluate([p])
    codes = _codes(report)
    assert "declared_invariant_scale" in codes        # reported as SOFT
    assert "vacuous_scale_ladder" not in codes         # not HARD-killed
    assert report["ok"] is True


# --------------------------------------------------------------------------- round-2 FP fixes
# Added after the 2026-05-28 confirm-round audit found the location-agnostic rewrite introduced
# false-positives (no_observable on top-level `positive`; erasure controls flagged as dead claims).


def test_top_level_positive_counts_as_signal(tmp_path):
    """Receipt with a bookkeeping-only summary but real claims under top-level `positive`
    must NOT be flagged no_observable_signature."""
    data = {
        "summary": {"all_pass": True, "max_qubits": 64, "shell_count": 5, "row_count": 4},
        "positive": {
            "N01_projective_path_order_witness": {"order_gap": 0.2500000000001, "pass": True},
            "QIT_local_edge_cut": {"mutual_information": 1.999999, "pass": True},
            "third_witness": {"min_signature_gap": 0.61, "pass": True},
        },
    }
    p = _write(tmp_path, "l0_e_peps3d_entropy_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "no_observable_signature" not in _codes(report)


def test_erasure_control_in_positive_is_soft_not_hard(tmp_path):
    """An intended-zero erasure leg co-located in a positive witness block is SOFT, not a dead
    claim -- the confirm-round false positive on L2's sheet_erased=0.0."""
    data = {
        "summary": {"all_pass": True, "min_control_gaps": {"a_gap": 0.5, "b_gap": 0.7, "c_gap": 1.1}},
        "controls": {"positive": {"N01_sheet_action_order_witness": {
            "min_left_right_signature_gap": 0.65,
            "order_erased_sheet_erasure_gap": 0.0,   # erasure leg, intended zero
            "max_sheet_erased_gap": 0.0,
            "pass": True}}},
    }
    p = _write(tmp_path, "l2_e_peps3d_bond4_tool_ablation_layer_probe_results.json", data)
    report = gate.evaluate([p])
    codes = _codes(report)
    assert "vacuous_erasure_control" in codes
    assert "vacuous_claim_bearing_control" not in codes
    assert report["ok"] is True


def test_declared_required_erasure_vacuous_is_hard(tmp_path):
    """When the receipt declares an erasure load-bearing, a vacuous one becomes HARD -- this is
    how L2 forces chirality/sheet erasure to actually bite."""
    data = {
        "summary": {"all_pass": True, "min_control_gaps": {"a_gap": 0.5, "b_gap": 0.7, "c_gap": 1.1}},
        "required_load_bearing_erasures": ["sheet"],
        "controls": {"positive": {"N01_sheet_action_order_witness": {
            "min_left_right_signature_gap": 0.65,
            "max_sheet_erased_gap": 0.0,   # declared load-bearing, but vacuous -> theater
            "pass": True}}},
    }
    p = _write(tmp_path, "l2_r_peps3d_bond4_tool_ablation_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "vacuous_required_erasure" in _codes(report)
    assert report["ok"] is False


def test_echo_suppressed_when_before_after_pair_present(tmp_path):
    """A real ablation recording baseline_pass + ablated_pass (a before/after transition) must
    not be flagged echo even if a witness number coincides with a baseline."""
    data = _clean_fsn("L4", 0.41)
    base = data["summary"]["min_pyg_message_gap"]
    data["tool_ablations_by_tool"] = {"terrain": {
        "non_vacuous": True, "pass": True, "baseline_pass": True, "ablated_pass": False,
        "delta_witness": {"message_gap": base}}}
    p = _write(tmp_path, "l4_e_peps3d_bond4_tool_ablation_layer_probe_results.json", data)
    report = gate.evaluate([p])
    assert "delta_witness_echoes_baseline" not in _codes(report)


if __name__ == "__main__":
    import subprocess
    import sys
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "-q", __file__]))
