from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    module_parent = str(path.parent)
    inserted_parent = False
    if module_parent not in sys.path:
        sys.path.insert(0, module_parent)
        inserted_parent = True
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(module_name, None)
        if inserted_parent:
            sys.path.remove(module_parent)


def test_axis0_result_loader_prefers_canonical_over_legacy(tmp_path) -> None:
    module = _load_module(
        "axis0_result_loader_prefers_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_result_loader.py",
    )
    results = tmp_path / "sim_results"
    results.mkdir()
    (results / "sim_axis0_bridge_search_results.json").write_text(
        json.dumps({"source": "canonical"}),
        encoding="utf-8",
    )
    (results / "axis0_bridge_search_results.json").write_text(
        json.dumps({"source": "legacy"}),
        encoding="utf-8",
    )

    resolved = module.resolve_axis0_result_path(results, "axis0_bridge_search_results.json")
    payload = module.load_axis0_result(results, "axis0_bridge_search_results.json")

    assert resolved.name == "sim_axis0_bridge_search_results.json"
    assert payload["source"] == "canonical"


def test_axis0_result_loader_falls_back_to_legacy_when_canonical_missing(tmp_path) -> None:
    module = _load_module(
        "axis0_result_loader_fallback_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_result_loader.py",
    )
    results = tmp_path / "sim_results"
    results.mkdir()
    (results / "axis0_phase5b_results.json").write_text(
        json.dumps({"source": "legacy"}),
        encoding="utf-8",
    )

    resolved = module.resolve_axis0_result_path(results, "axis0_phase5b_results.json")
    payload = module.load_axis0_result(results, "axis0_phase5b_results.json")

    assert resolved.name == "axis0_phase5b_results.json"
    assert payload["source"] == "legacy"


def test_validate_axis0_attractor_basin_boundary_search_accepts_canonical_only_result(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.syspath_prepend(str(REPO_ROOT / "system_v4" / "probes"))
    module = _load_module(
        "validate_axis0_attractor_basin_boundary_search_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_axis0_attractor_basin_boundary_search.py",
    )
    results = tmp_path / "sim_results"
    results.mkdir()
    q1_configs = [
        {
            "constant_at_1": False,
            "lr_asym_min": 0.91,
            "lr_asym_mean": 0.92,
            "lr_asym_max": 0.995,
        }
        for _ in range(8)
    ]
    payload = {
        "q1_trajectory_lr_asym": {"configs": q1_configs},
        "q3_ti_boundary": {
            "best_lr_asym_before_threshold": 0.05,
            "threshold_accuracy": 0.95,
            "n_successes": 20,
            "n_failures": 5,
            "failure_asym_before_mean": 0.2,
            "success_asym_before_mean": 0.89,
        },
    }
    (results / "sim_axis0_attractor_basin_boundary_results.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "SIM_RESULTS", results)
    monkeypatch.setattr(
        module,
        "OUTPUT_PATH",
        results / "axis0_attractor_basin_boundary_search_validation.json",
    )
    monkeypatch.setattr(sys, "argv", ["validate_axis0_attractor_basin_boundary_search.py"])

    rc = module.main()
    written = json.loads(module.OUTPUT_PATH.read_text(encoding="utf-8"))

    assert rc == 0
    assert written["passed_gates"] == written["total_gates"] == 3


def test_validate_c1_bridge_object_support_contract_accepts_open_search_with_explicit_handoff(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "validate_c1_bridge_object_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_c1_bridge_object_packet.py",
    )
    results = tmp_path / "sim_results"
    results.mkdir()
    payload = {
        "bridge_object": {
            "name": "Xi_chiral_entangle",
            "status": "admitted_bridge_object_for_downstream_readout_not_final_owner_law",
            "scope": "downstream_readout_only",
            "consumer_status": "allowed_for_entropy_readout_not_final_owner_xi",
            "evidence": {
                "bridge_winner": "Xi_chiral_entangle",
                "winner_mean_mi": 0.82,
                "winner_mean_i_c": 0.03,
                "runner_up": "Xi_chiral_hist_entangle",
                "runner_up_mean_i_c": -0.07,
                "lr_direct_mean_mi": 0.0,
                "counterfeit_status": "counterfeit_beats_mi_but_loses_signed_honesty",
                "counterfeit_mean_live_I_c": 0.03,
                "counterfeit_mean_counterfeit_I_c": -0.06,
                "counterfeit_mean_I_c_gap": 0.09,
            },
        },
        "support_contract": {
            "c1_search_closed": False,
            "bridge_owner_alignment": {
                "pass": True,
                "status": "axis_internal_candidate_not_final_owner_law",
                "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
                "owner_dependency": "must_bind_under_xi_hist_signed_law",
                "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
                "winner": "Xi_chiral_entangle",
                "runner_up": "Xi_chiral_hist_entangle",
            },
            "carrier_handoff": {
                "candidate": "Xi_chiral_entangle",
                "status": "provisional_handoff_ready",
                "placement_contract": "downstream_axis_internal_bridge_candidate_only",
                "owner_dependency": "must_bind_under_xi_hist_signed_law",
                "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
                "consumer_status": "allowed_for_entropy_readout_not_final_owner_xi",
            },
            "carrier_selection_handoff_matches_search": True,
            "pre_entropy_mapping": "axis_internal_candidate_not_final_owner_law",
            "pre_entropy_relation": "downstream_of_xi_hist_signed_law_not_alternate_owner_law",
            "pre_entropy_placement": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
            "entropy_gate_name": "E10_current_bridge_candidate_is_explicit_and_provisional",
            "entropy_gate_status": "admitted_executable_candidate_not_final_owner_law",
        },
        "non_claims": {
            "status": "explicit_non_owner_reservation",
            "final_xi_owner_law": "reserved_for_future_owner_doctrine_not_claimed_by_c1",
            "shell_doctrine": "reserved_for_future_shell_doctrine_not_claimed_by_c1",
            "history_law_replacement": "reserved_for_future_history_law_replacement_not_claimed_by_c1",
            "entropy_family_owner_doctrine": "reserved_for_future_entropy_owner_doctrine_not_claimed_by_c1",
            "owner_dependency": "must_bind_under_xi_hist_signed_law",
            "consumer_scope": "downstream_readout_only",
        },
    }
    (results / "c1_bridge_object_packet_results.json").write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(module, "SIM_RESULTS", results)
    monkeypatch.setattr(module, "OUTPUT_PATH", results / "c1_bridge_object_packet_validation.json")
    monkeypatch.setattr(sys, "argv", ["validate_c1_bridge_object_packet.py"])

    rc = module.main()
    written = json.loads(module.OUTPUT_PATH.read_text(encoding="utf-8"))
    gate_map = {gate["name"]: gate for gate in written["gates"]}

    assert rc == 0
    assert gate_map["C1B3_bridge_object_is_bound_to_the_existing_support_contract"]["pass"] is True


def test_validate_c1_signed_bridge_candidate_search_accepts_near_live_counterfeit_pressure(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "validate_c1_signed_bridge_candidate_search_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_c1_signed_bridge_candidate_search.py",
    )
    results = tmp_path / "sim_results"
    results.mkdir()
    payload = {
        "candidate_object": {
            "status": "provisional_signed_bridge_candidate",
            "keep": True,
            "evidence": {
                "bridge_winner": "Xi_chiral_entangle",
                "winner_mean_mi": 0.82,
                "winner_mean_i_c": 0.03,
                "runner_up": "Xi_chiral_hist_entangle",
                "runner_up_mean_i_c": -0.07,
                "lr_direct_mean_mi": 0.0,
            },
        },
        "negative_family": {
            "history_mispair_counterfeit": {
                "status": "counterfeit_beats_mi_but_loses_signed_honesty",
                "keep": True,
                "evidence": {
                    "mean_live_I_AB": 0.82,
                    "mean_counterfeit_I_AB": 0.78,
                    "mean_live_I_c": 0.03,
                    "mean_counterfeit_I_c": -0.06,
                    "mean_I_c_gap": 0.09,
                },
            }
        },
        "support_chain": {
            "bridge_owner_alignment": {
                "pass": True,
                "status": "axis_internal_candidate_not_final_owner_law",
                "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
                "owner_dependency": "must_bind_under_xi_hist_signed_law",
                "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
                "winner": "Xi_chiral_entangle",
                "runner_up": "Xi_chiral_hist_entangle",
            },
            "matched_marginal_closed": True,
            "matched_marginal_contract_scope": "xi_downstream_handoff_and_honesty_layer",
            "matched_marginal_required_gates": [
                "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract",
                "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping",
            ],
            "matched_marginal_required_passes": {
                "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract": True,
                "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping": True,
            },
            "matched_marginal_excluded_failures": ["M7_fe_indexed_pairs_remain_the_only_structured_refinement_winner"],
            "pre_entropy_mapping": "axis_internal_candidate_not_final_owner_law",
            "pre_entropy_relation": "downstream_of_xi_hist_signed_law_not_alternate_owner_law",
            "pre_entropy_placement": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
            "entropy_readout_current_bridge_gate": "E10_current_bridge_candidate_is_explicit_and_provisional",
        },
        "unresolved": {
            "status": "explicit_non_owner_reservation",
            "final_xi_owner_law": "reserved_for_future_owner_doctrine_not_claimed_by_c1",
            "shell_doctrine": "reserved_for_future_shell_doctrine_not_claimed_by_c1",
            "history_law_replacement": "reserved_for_future_history_law_replacement_not_claimed_by_c1",
            "entropy_family_owner_doctrine": "reserved_for_future_entropy_owner_doctrine_not_claimed_by_c1",
            "owner_dependency": "must_bind_under_xi_hist_signed_law",
            "consumer_scope": "downstream_readout_only",
        },
        "owner_read": {
            "status": "admitted_executable_candidate_not_final_owner_law",
        },
    }
    (results / "c1_signed_bridge_candidate_search_results.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "SIM_RESULTS", results)
    monkeypatch.setattr(
        module,
        "OUTPUT_PATH",
        results / "c1_signed_bridge_candidate_search_validation.json",
    )
    monkeypatch.setattr(sys, "argv", ["validate_c1_signed_bridge_candidate_search.py"])

    rc = module.main()
    written = json.loads(module.OUTPUT_PATH.read_text(encoding="utf-8"))
    gate_map = {gate["name"]: gate for gate in written["gates"]}

    assert rc == 0
    assert gate_map["C1S2_counterfeit_pressure_keeps_signed_honesty_load_bearing"]["pass"] is True


def test_validate_c1_signed_bridge_candidate_search_keeps_support_chain_fail_closed(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "validate_c1_signed_bridge_candidate_search_fail_closed_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_c1_signed_bridge_candidate_search.py",
    )
    results = tmp_path / "sim_results"
    results.mkdir()
    payload = {
        "candidate_object": {
            "status": "provisional_signed_bridge_candidate",
            "keep": True,
            "evidence": {
                "bridge_winner": "Xi_chiral_entangle",
                "winner_mean_mi": 0.82,
                "winner_mean_i_c": 0.03,
                "runner_up": "Xi_chiral_hist_entangle",
                "runner_up_mean_i_c": -0.07,
                "lr_direct_mean_mi": 0.0,
            },
        },
        "negative_family": {
            "history_mispair_counterfeit": {
                "status": "counterfeit_beats_mi_but_loses_signed_honesty",
                "keep": True,
                "evidence": {
                    "mean_live_I_AB": 0.82,
                    "mean_counterfeit_I_AB": 0.78,
                    "mean_live_I_c": 0.03,
                    "mean_counterfeit_I_c": -0.06,
                    "mean_I_c_gap": 0.09,
                },
            }
        },
        "support_chain": {
            "bridge_owner_alignment": {
                "pass": True,
                "status": "axis_internal_candidate_not_final_owner_law",
                "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
                "owner_dependency": "must_bind_under_xi_hist_signed_law",
                "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
                "winner": "Xi_chiral_entangle",
                "runner_up": "Xi_chiral_hist_entangle",
            },
            "matched_marginal_closed": False,
            "matched_marginal_contract_scope": "xi_downstream_handoff_and_honesty_layer",
            "matched_marginal_required_gates": [
                "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract",
                "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping",
            ],
            "matched_marginal_required_passes": {
                "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract": False,
                "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping": True,
            },
            "matched_marginal_excluded_failures": ["M7_fe_indexed_pairs_remain_the_only_structured_refinement_winner"],
            "pre_entropy_mapping": "axis_internal_candidate_not_final_owner_law",
            "pre_entropy_relation": "downstream_of_xi_hist_signed_law_not_alternate_owner_law",
            "pre_entropy_placement": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
            "entropy_readout_current_bridge_gate": "E10_current_bridge_candidate_is_explicit_and_provisional",
        },
        "unresolved": {
            "status": "explicit_non_owner_reservation",
            "final_xi_owner_law": "reserved_for_future_owner_doctrine_not_claimed_by_c1",
            "shell_doctrine": "reserved_for_future_shell_doctrine_not_claimed_by_c1",
            "history_law_replacement": "reserved_for_future_history_law_replacement_not_claimed_by_c1",
            "entropy_family_owner_doctrine": "reserved_for_future_entropy_owner_doctrine_not_claimed_by_c1",
            "owner_dependency": "must_bind_under_xi_hist_signed_law",
            "consumer_scope": "downstream_readout_only",
        },
        "owner_read": {
            "status": "admitted_executable_candidate_not_final_owner_law",
        },
    }
    (results / "c1_signed_bridge_candidate_search_results.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "SIM_RESULTS", results)
    monkeypatch.setattr(
        module,
        "OUTPUT_PATH",
        results / "c1_signed_bridge_candidate_search_validation.json",
    )
    monkeypatch.setattr(sys, "argv", ["validate_c1_signed_bridge_candidate_search.py"])

    rc = module.main()
    written = json.loads(module.OUTPUT_PATH.read_text(encoding="utf-8"))
    gate_map = {gate["name"]: gate for gate in written["gates"]}

    assert rc == 1
    assert gate_map["C1S1_current_signed_bridge_candidate_is_explicit"]["pass"] is True
    assert gate_map["C1S2_counterfeit_pressure_keeps_signed_honesty_load_bearing"]["pass"] is True
    assert gate_map["C1S3_support_chain_is_closed_before_candidate_packaging"]["pass"] is False


def test_live_queue_controller_ignores_copy_sims(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "live_queue_controller_under_test",
        REPO_ROOT / "system_v4" / "probes" / "live_queue_controller.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_alpha.py").write_text("print('alpha')\n", encoding="utf-8")
    (probes / "sim_alpha 2.py").write_text("print('alpha copy')\n", encoding="utf-8")
    (probes / "sim_beta.py").write_text("print('beta')\n", encoding="utf-8")

    monkeypatch.setattr(module, "PROBES", probes)

    names = [path.name for path in module.enumerate_all_sims()]
    assert names == ["sim_alpha.py", "sim_beta.py"]


def test_check_witnesses_accepts_recent_witness_fields(tmp_path, monkeypatch, capsys) -> None:
    module = _load_module(
        "check_witnesses_under_test",
        REPO_ROOT / "scripts" / "check_witnesses.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)

    witness = probes / "sim_pyg_dynamic_edge_werner.py"
    witness.write_text(
        "TOOL_INTEGRATION_DEPTH = {'pyg': 'load_bearing'}\n",
        encoding="utf-8",
    )
    capability = probes / "sim_pyg_capability.py"
    capability.write_text(
        "\n".join(
            [
                "results = {",
                "    'witness_use_cases': ['system_v4/probes/sim_pyg_dynamic_edge_werner.py'],",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)

    rc = module.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert '"violation_count": 0' in out


def test_check_witnesses_canonicalizes_deep_capability_variants(
    tmp_path, monkeypatch, capsys
) -> None:
    module = _load_module(
        "check_witnesses_alias_under_test",
        REPO_ROOT / "scripts" / "check_witnesses.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)

    witness = probes / "sim_pyg_dynamic_edge_werner.py"
    witness.write_text(
        "TOOL_INTEGRATION_DEPTH = {'pyg': 'load_bearing'}\n",
        encoding="utf-8",
    )
    capability = probes / "sim_pyg_hopf_graph_deep_capability.py"
    capability.write_text(
        "\n".join(
            [
                "WITNESS_INFO = {",
                "    'witness_use_cases': ['system_v4/probes/sim_pyg_dynamic_edge_werner.py'],",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)

    rc = module.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert '"tool": "pyg"' in out
    assert '"violation_count": 0' in out


def test_lint_accepts_isolated_capability_probe_for_classical_integration(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "lint_sim_contract_under_test",
        REPO_ROOT / "scripts" / "lint_sim_contract.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)

    capability = probes / "sim_capability_datasketch_isolated.py"
    capability.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'divergence_log = "Classical capability baseline."',
                'TOOL_MANIFEST = {"datasketch": {"tried": True, "used": True, "reason": "load-bearing isolated capability probe"}}',
                'TOOL_INTEGRATION_DEPTH = {"datasketch": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (results / "sim_capability_datasketch_isolated_results.json").write_text(
        '{"overall_pass": true}\n',
        encoding="utf-8",
    )

    integration = probes / "sim_integration_datasketch_graph.py"
    integration.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'divergence_log = "Classical integration baseline."',
                'TOOL_MANIFEST = {"datasketch": {"tried": True, "used": True, "reason": "load-bearing graph edge construction"}}',
                'TOOL_INTEGRATION_DEPTH = {"datasketch": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    violations = module.lint_sim(integration)
    rules = {v["rule"] for v in violations}

    assert "C5_missing_probe" not in rules
    assert "C5_probe_stale" not in rules
    assert "C5_probe_failing" not in rules
    assert "C6_classical_has_load_bearing" not in rules


def test_gate_accepts_isolated_capability_probe_for_load_bearing_tool(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "verify_load_bearing_under_test",
        REPO_ROOT / "scripts" / "verify_load_bearing_has_capability_probe.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)

    capability = probes / "sim_capability_evotorch_isolated.py"
    capability.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'TOOL_MANIFEST = {"evotorch": {"tried": True, "used": True, "reason": "isolated capability probe"}}',
                'TOOL_INTEGRATION_DEPTH = {"evotorch": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (results / "sim_capability_evotorch_isolated_results.json").write_text(
        '{"overall_pass": true}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    assert module.probe_status("evotorch") is None


def test_adaptive_controller_builds_plane_snapshot_from_current_surfaces(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    skill_log = repo / "system_v4" / "a1_state" / "skill_invocation_log.jsonl"
    for lane, count in {
        "lane_A": 2,
        "lane_B": 1,
        "claimed": 3,
        "blocked": 1,
        "done": 4,
    }.items():
        lane_dir = queue_root / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            (lane_dir / f"{lane}_{i}.json").write_text("{}", encoding="utf-8")

    skill_log.parent.mkdir(parents=True, exist_ok=True)
    skill_log.write_text(
        "\n".join(
            [
                '{"timestamp":"2026-04-15T01:00:00Z","batch_id":"B1","phase":"A1_EXTRACTION","layer_id":"A1_STRIPPED","graph_family":"dependency","selected_skill_id":"a1-brain","execution_runtime":"codex"}',
                '{"timestamp":"2026-04-15T01:05:00Z","batch_id":"B2","phase":"SIM_EVIDENCE","layer_id":"SIM_EVIDENCED","graph_family":"runtime","selected_skill_id":"sim-engine","execution_runtime":"codex"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "QUEUE", queue_root)
    monkeypatch.setattr(module, "SKILL_LOG", skill_log)

    state = {
        "ts": "2026-04-15T02:00:00Z",
        "failing": ["sim_fail"],
        "schema_debt": ["sim_schema"],
        "never_run": ["sim_new"],
        "stale": [],
        "passing": ["sim_ok1", "sim_ok2"],
        "released_claims": 5,
    }
    integration = {
        "canonical_passing": 1,
        "total_passing": 2,
        "rosetta_candidate_clusters": 3,
    }

    snapshot = module.build_plane_snapshot(state, integration)

    assert snapshot["control_plane"]["queue"] == {
        "lane_A": 2,
        "lane_B": 1,
        "claimed": 3,
        "blocked": 1,
        "done": 4,
    }
    assert snapshot["control_plane"]["released_claims"] == 5
    assert len(snapshot["control_plane"]["recent_dispatch"]) == 2
    assert snapshot["state_plane"]["triage"] == {
        "failing": 1,
        "schema_debt": 1,
        "never_run": 1,
        "stale": 0,
        "passing": 2,
    }
    assert snapshot["state_plane"]["integration"]["rosetta_candidate_clusters"] == 3
    assert snapshot["state_plane"]["program"]["never_run_families"] == {"new": 1}
    assert snapshot["state_plane"]["program"]["passing_families"] == {"ok1": 1, "ok2": 1}
    assert snapshot["state_plane"]["program"]["never_run_buckets"] == {"exploratory": 1}
    assert snapshot["state_plane"]["program"]["passing_buckets"] == {"exploratory": 2}
    assert snapshot["state_plane"]["program"]["never_run_stages"] == {"early_core": 1}
    assert snapshot["state_plane"]["program"]["passing_stages"] == {"early_core": 2}
    assert snapshot["state_plane"]["program"]["queue_families"]["lane_A"] == {"other": 2}


def test_adaptive_controller_rescues_misrouted_blocked_classical_baseline(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_rescue_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    lane_b = queue_root / "lane_B"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    blocked.mkdir(parents=True)
    lane_b.mkdir(parents=True)

    sim = probes / "sim_cl3_composition.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")
    blocked_item = blocked / "dead.json.123.host.w1"
    blocked_item.write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied"}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    rescued = module.rescue_misrouted_blocked()

    queued = list(lane_b.glob("*.json"))
    resolved = list((blocked / "resolved").glob("*.json*"))
    assert rescued == 1
    assert len(queued) == 1
    assert len(resolved) == 1
    queued_payload = json.loads(queued[0].read_text(encoding="utf-8"))
    assert queued_payload["sim_path"] == str(sim)
    resolved_payload = json.loads(resolved[0].read_text(encoding="utf-8"))
    assert resolved_payload["rescued_lane"] == "lane_B"
    assert resolved_payload["rescued_priority"] == "normal"
    assert blocked_item.exists() is False


def test_adaptive_controller_resolves_blacklisted_blocked_items(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_blacklisted_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    blocked.mkdir(parents=True)

    sim = probes / "sim_timing_benchmark.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")
    blocked_item = blocked / "meta.json"
    blocked_item.write_text(
        '{"lane":"lane_B","sim_path":"%s","blocked_reason":"blacklisted_meta_sim"}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    rescued = module.rescue_misrouted_blocked()

    resolved = list((blocked / "resolved").glob("*.json*"))
    assert rescued == 1
    assert len(resolved) == 1
    payload = json.loads(resolved[0].read_text(encoding="utf-8"))
    assert payload["resolution"] == "blacklisted_meta_sim"
    assert blocked_item.exists() is False


def test_adaptive_controller_triage_skips_enqueue_for_active_blocked_sim(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_blocked_skip_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    blocked.mkdir(parents=True)

    sim = probes / "sim_clifford_holo_dirac_pairwise_coupling.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    (blocked / "gate.json.1.host.w1").write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied","blocked_at":1}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)
    monkeypatch.setattr(module, "gate_allows_sim", lambda path: False)

    state = module.triage_cycle(dry=False)

    assert "sim_clifford_holo_dirac_pairwise_coupling" in state["never_run"]
    assert state["enqueued"]["never_run"] == 0
    assert list((queue_root / "lane_A").glob("*.json")) == []


def test_adaptive_controller_dedupes_blocked_entries_and_queue_overlaps(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_blocked_dedupe_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    lane_a = queue_root / "lane_A"
    probes.mkdir(parents=True)
    blocked.mkdir(parents=True)
    lane_a.mkdir(parents=True)

    sim = probes / "sim_alpha.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    abs_sim = str(sim.resolve())
    (blocked / "dup1.json.1.host.w1").write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied","blocked_at":1}\n' % abs_sim,
        encoding="utf-8",
    )
    (blocked / "dup2.json.2.host.w2").write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied","blocked_at":2}\n' % abs_sim,
        encoding="utf-8",
    )
    (lane_a / "queued.json").write_text(
        '{"lane":"lane_A","sim_path":"%s","priority":"high"}\n' % abs_sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    removed = module.dedupe_queue_entries()

    active_blocked = list(blocked.glob("*.json.*"))
    resolved = list((blocked / "resolved").glob("*.json*"))
    assert removed == 2
    assert len(active_blocked) == 1
    assert len(resolved) == 1
    assert list(lane_a.glob("*.json")) == []
    payload = json.loads(resolved[0].read_text(encoding="utf-8"))
    assert payload["resolution"] == "deduped_duplicate_block"


def test_adaptive_controller_rescues_gate_ready_blocked_canonical(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_gate_ready_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    lane_a = queue_root / "lane_A"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    blocked.mkdir(parents=True)
    lane_a.mkdir(parents=True)

    sim = probes / "sim_clifford_holo_dirac_pairwise_coupling.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    blocked_item = blocked / "gate.json.123.host.w1"
    blocked_item.write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied"}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)
    monkeypatch.setattr(module, "gate_allows_sim", lambda path: True)

    rescued = module.rescue_misrouted_blocked()

    queued = list(lane_a.glob("*.json"))
    resolved = list((blocked / "resolved").glob("*.json*"))
    assert rescued == 1
    assert len(queued) == 1
    assert len(resolved) == 1
    payload = json.loads(resolved[0].read_text(encoding="utf-8"))
    assert payload["rescued_lane"] == "lane_A"
    assert payload["resolution"] == "requeued_lane_A"
    assert blocked_item.exists() is False


def test_adaptive_controller_dry_mode_skips_queue_mutation(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "adaptive_controller_dry_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    for lane in ("claimed", "blocked"):
        (queue_root / lane).mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_alpha.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")
    claim = queue_root / "claimed" / "dead.json.123.host.w1"
    claim.write_text(
        '{"lane":"lane_A","sim_path":"%s"}\n' % sim,
        encoding="utf-8",
    )
    blocked = queue_root / "blocked" / "gate.json.123.host.w1"
    blocked.write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied"}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    state = module.triage_cycle(dry=True)

    assert state["released_claims"] == 0
    assert state["rescued_misrouted_blocked"] == 0
    assert claim.exists()
    assert blocked.exists()


def test_adaptive_controller_is_queued_matches_relative_and_absolute_paths(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_is_queued_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    (queue_root / "lane_B").mkdir(parents=True, exist_ok=True)

    sim_rel = "system_v4/probes/sim_alpha.py"
    sim_abs = str((repo / sim_rel).resolve())
    (queue_root / "lane_B" / "item.json").write_text(
        '{"sim_path":"%s","lane":"lane_B"}\n' % sim_rel,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    assert module.is_queued(sim_abs) is True


def test_adaptive_controller_enqueue_is_idempotent(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "adaptive_controller_enqueue_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    lane_b = queue_root / "lane_B"
    probes.mkdir(parents=True, exist_ok=True)
    lane_b.mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_weyl_chirality_bipartite.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    module.enqueue(sim, "lane_B", "normal")
    module.enqueue(sim, "lane_B", "normal")

    queued = list(lane_b.glob("*.json"))
    assert len(queued) == 1
    payload = json.loads(queued[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == str(sim.resolve())
    assert payload["plan_stage"] == "late_info"


def test_adaptive_controller_dedupes_queue_entries_and_normalizes_paths(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_dedupe_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    lane_a = queue_root / "lane_A"
    lane_b = queue_root / "lane_B"
    probes.mkdir(parents=True, exist_ok=True)
    lane_a.mkdir(parents=True, exist_ok=True)
    lane_b.mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_weyl_chirality_bipartite.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")
    abs_sim = str(sim.resolve())
    rel_sim = "system_v4/probes/sim_weyl_chirality_bipartite.py"
    (lane_b / "a.json").write_text(
        '{"sim_path":"%s","lane":"lane_B","priority":"high"}\n' % rel_sim,
        encoding="utf-8",
    )
    (lane_b / "b.json").write_text(
        '{"sim_path":"%s","lane":"lane_B","priority":"normal"}\n' % abs_sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    removed = module.dedupe_queue_entries()

    remaining = list(lane_b.glob("*.json"))
    assert removed == 1
    assert len(remaining) == 1
    payload = json.loads(remaining[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == abs_sim
    assert remaining[0].name == module.queue_item_path("lane_B", abs_sim).name
    assert payload["plan_bucket"] == "core_ladder"
    assert payload["plan_stage"] == "late_info"
    assert payload["priority"] == "high"


def test_adaptive_controller_normalizes_legacy_queue_filename_without_duplicate(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_queue_normalize_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    lane_b = queue_root / "lane_B"
    probes.mkdir(parents=True, exist_ok=True)
    lane_b.mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_shannon_entropy.py"
    sim.write_text("print('ok')\n", encoding="utf-8")
    abs_sim = str(sim.resolve())
    legacy = lane_b / "legacy.json"
    legacy.write_text(
        '{"sim_path":"%s","lane":"lane_B","priority":"normal"}\n' % abs_sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    removed = module.dedupe_queue_entries()

    remaining = list(lane_b.glob("*.json"))
    assert removed == 0
    assert len(remaining) == 1
    assert remaining[0].name == module.queue_item_path("lane_B", abs_sim).name
    payload = json.loads(remaining[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == abs_sim
    assert payload["plan_stage"] == "late_info"


def test_adaptive_controller_removes_queue_entries_for_claimed_sims(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_claim_overlap_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    lane_a = queue_root / "lane_A"
    claimed = queue_root / "claimed"
    probes.mkdir(parents=True, exist_ok=True)
    lane_a.mkdir(parents=True, exist_ok=True)
    claimed.mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_gerbe_admissibility_dixmier_douady.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    abs_sim = str(sim.resolve())
    (lane_a / "legacy.json").write_text(
        '{"sim_path":"%s","lane":"lane_A","priority":"high"}\n' % abs_sim,
        encoding="utf-8",
    )
    (claimed / "claimed.json.123.host.laneA_w1").write_text(
        '{"sim_path":"%s","lane":"lane_A","claimed_at":1}\n' % abs_sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    removed = module.dedupe_queue_entries()

    assert removed == 1
    assert list(lane_a.glob("*.json")) == []


def test_adaptive_controller_accepts_all_pass_and_summary_all_passed() -> None:
    module = _load_module(
        "adaptive_controller_pass_schema_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )

    assert module.is_passing({"all_pass": True}) is True
    assert module.is_passing({"all_pass": False}) is False
    assert module.is_passing({"ALL_PASS": True}) is True
    assert module.is_passing({"ALL_PASS": False}) is False
    assert module.is_passing({"summary": {"all_passed": True}}) is True
    assert module.is_passing({"summary": {"all_pass": False}}) is False
    assert module.is_passing({"summary": {"all_checks_pass": True}}) is True
    assert module.is_passing({
        "summary": {
            "all_checks_pass": True,
            "key_findings": {"one": True, "two": True},
        }
    }) is True
    assert module.is_passing({
        "positive": {"torch": {"status": "ok"}},
        "negative": {"z3": {"status": "ok"}},
    }) is True
    assert module.is_legacy_schema({"timestamp": "x", "all_pass": True}) is False
    assert module.is_legacy_schema({"timestamp": "x", "ALL_PASS": True}) is False


def test_adaptive_controller_find_result_file_skips_oversized_candidates(tmp_path) -> None:
    module = _load_module(
        "adaptive_controller_long_filename_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )

    results_dir = tmp_path / "results"
    results_dir.mkdir()
    expected = results_dir / "normal_probe_results.json"
    expected.write_text('{"all_pass": true}\n', encoding="utf-8")

    long_stem = "sim_" + ("x" * 512)
    assert module.find_result_file(long_stem, results_dir) is None
    assert module.find_result_file("sim_normal_probe", results_dir) == expected


def test_perpetual_runner_declares_pidfile_singleton() -> None:
    text = (REPO_ROOT / "scripts" / "perpetual_runner.sh").read_text(encoding="utf-8")

    assert 'PERPETUAL_PIDFILE="/tmp/codex_ratchet_perpetual_runner.pid"' in text
    assert "acquire_perpetual_pidfile()" in text
    assert "existing perpetual pidfile is alive; exiting duplicate" in text


def test_system_surface_audit_infers_legacy_pass_shapes() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    assert module._pass_state({"all_pass": True}) == "pass"
    assert module._pass_state({"ALL_PASS": True}) == "pass"
    assert module._pass_state({"summary": {"all_passed": True}}) == "pass"
    assert module._pass_state({"summary": {"all_checks_pass": True}}) == "pass"
    assert module._pass_state({
        "summary": {"all_checks_pass": True, "key_findings": {"alpha": True, "beta": True}},
    }) == "pass"
    assert module._pass_state({
        "positive": {"torch": {"status": "ok"}},
        "negative": {"z3": {"status": "ok"}},
        "boundary": {"sympy": {"status": "passed"}},
    }) == "pass"
    assert module._pass_state({
        "evidence_ledger": [{"status": "PASS"}],
        "results": {"check_a": True},
    }) == "pass_inferred"
    assert module._pass_state({
        "positive": {"foo": {"passed": True}},
        "negative": {"bar": {"pass": True}},
        "boundary": {"baz": {"ok": True}},
    }) == "pass_inferred"
    assert module._pass_state({"summary": {"positive": "42/42", "boundary": "5/5"}}) == "pass_inferred"


def test_system_surface_audit_first_result_for_probe_skips_oversized_candidates(tmp_path) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_long_filename_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    result_root = tmp_path / "sim_results"
    result_root.mkdir()
    long_probe = tmp_path / ("sim_" + ("y" * 512) + ".py")

    module.RESULT_ROOTS = [result_root]

    assert module._first_result_for_probe(long_probe) is None


def test_system_surface_audit_pidfile_uses_ps_fallback_on_permission_error(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_pid_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    pidfile = tmp_path / "runner.pid"
    pidfile.write_text("123\n", encoding="utf-8")

    def fake_kill(pid: int, sig: int) -> None:
        raise PermissionError

    monkeypatch.setattr(module.os, "kill", fake_kill)
    monkeypatch.setattr(module, "_process_command", lambda pid: "bash scripts/perpetual_runner.sh")

    status = module._pidfile_status("perpetual_runner", pidfile)

    assert status["alive"] is True
    assert status["alive_state"] == "ps_visible_permission_limited"
    assert status["command"] == "bash scripts/perpetual_runner.sh"


def test_system_surface_audit_reports_fail_and_unknown_families(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_result_surface_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    root = probes / "a2_state" / "sim_results"
    root.mkdir(parents=True, exist_ok=True)

    (root / "sim_szilard_alpha_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )
    (root / "sim_szilard_beta_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )
    (root / "sim_weyl_gamma_results.json").write_text(
        '{"summary": {"all_checks_pass": true}}\n',
        encoding="utf-8",
    )
    (root / "sim_axis_delta_results.json").write_text(
        '{"summary": {"note": "unknown legacy shape"}}\n',
        encoding="utf-8",
    )
    (probes / "sim_szilard_alpha.py").write_text("print('alpha')\n", encoding="utf-8")
    (probes / "weyl_beta.py").write_text("print('beta')\n", encoding="utf-8")
    (root / "weyl_beta_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULT_ROOTS", [root])

    report = module.result_surface()["system_v4/probes/a2_state/sim_results"]

    assert report["status"]["fail"] == 3
    assert report["status"]["pass"] == 1
    assert report["status"]["unknown"] == 1
    assert report["fail_families"] == {"szilard": 2, "weyl": 1}
    assert report["fail_modes"] == {"summary_gate_false": 3}
    assert report["fail_source_states"] == {"source_clean_source_newer": 1, "source_missing": 1, "source_clean_result_newer": 1}
    assert report["fail_actions"] == {"missing_source_repair": 1, "rerun_candidate": 1, "noncanonical_source_repair": 1}
    assert report["unknown_families"] == {"axis": 1}


def test_system_surface_audit_classifies_fail_modes() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_fail_modes_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    assert module._result_fail_mode({"error": "ImportError", "overall_pass": False}) == "explicit_error"
    assert module._result_fail_mode({"summary": {"tests_failed": 2}, "overall_pass": False}) == "tests_failed"
    assert module._result_fail_mode({"summary": {"passed": 2, "total": 3}, "overall_pass": False}) == "partial_pass"
    assert module._result_fail_mode({"summary": {"all_pass": False}, "overall_pass": False}) == "summary_gate_false"
    assert module._result_fail_mode({"all_pass": False}) == "top_level_gate_false"
    assert module._result_fail_mode({"positive": {"foo": {"pass": False}}, "overall_pass": False}) == "section_check_failed"


def test_system_surface_audit_queue_freshness_detects_recent_activity(tmp_path) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_freshness_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    item = queue_dir / "item.json"
    item.write_text("{}", encoding="utf-8")

    freshness = module._queue_dir_freshness(queue_dir)

    assert freshness["newest_file"] == "item.json"
    assert freshness["newest_age_sec"] is not None
    assert freshness["active_within_60s"] is True
    assert freshness["active_within_300s"] is True


def test_system_surface_audit_git_layer_classifies_probe_sources() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_git_layer_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    assert module._git_layer("system_v4/probes/sim_mera_weyl_pairwise_coupling.py") == "probe_sources"
    assert (
        module._git_layer("system_v4/probes/sim_mera_weyl_pairwise_coupling_results.json")
        == "misplaced_probe_results"
    )


def test_system_surface_audit_result_surface_reports_untracked_probe_sources(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_untracked_sources_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    root = probes / "a2_state" / "sim_results"
    root.mkdir(parents=True, exist_ok=True)
    (root / "sim_mera_weyl_pairwise_coupling_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )
    (probes / "sim_mera_weyl_pairwise_coupling.py").write_text(
        "print('probe')\n",
        encoding="utf-8",
    )
    newer = time.time() + 5
    os.utime(root / "sim_mera_weyl_pairwise_coupling_results.json", (newer, newer))

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULT_ROOTS", [root])
    monkeypatch.setattr(
        module,
        "_git_status_entries",
        lambda: [{"status": "??", "path": "system_v4/probes/sim_mera_weyl_pairwise_coupling.py"}],
    )

    report = module.result_surface()["system_v4/probes/a2_state/sim_results"]

    assert report["dirty_source_results"] == 1
    assert report["untracked_source_results"] == 1
    assert report["samples"]["untracked_source_results"] == ["sim_mera_weyl_pairwise_coupling_results.json"]
    assert report["fail_source_states"] == {"source_untracked_result_newer": 1}
    assert report["fail_details"] == [{
        "result": "sim_mera_weyl_pairwise_coupling_results.json",
        "source": "system_v4/probes/sim_mera_weyl_pairwise_coupling.py",
        "fail_mode": "summary_gate_false",
        "source_state": "source_untracked_result_newer",
        "action": "source_drift_review",
    }]


def test_system_surface_audit_tool_integration_flags_missing_torch_headers(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_tool_integration_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    (probes / "sim_torch_missing_headers.py").write_text(
        "\n".join(
            [
                "import torch",
                "",
                "classification = 'canonical'",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_torch_declared_headers.py").write_text(
        "\n".join(
            [
                "import torch",
                "TOOL_MANIFEST = {'pytorch': {'tried': True, 'used': True, 'reason': 'declared'}}",
                "TOOL_INTEGRATION_DEPTH = {'pytorch': 'load_bearing'}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_pytorch_capability.py").write_text(
        "TOOL_INTEGRATION_DEPTH = {'pytorch': 'load_bearing'}\n",
        encoding="utf-8",
    )
    (results / "pytorch_capability_results.json").write_text(
        '{"summary": {"all_pass": true}}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)

    report = module.tool_integration_surface()

    assert report["audited_sims_with_tool_imports"] == 2
    assert report["missing_manifest_by_tool"] == {"pytorch": 1}
    assert report["missing_depth_by_tool"] == {"pytorch": 1}
    assert report["samples"] == [{
        "sim": "sim_torch_missing_headers.py",
        "imported_tools": ["pytorch"],
        "missing_manifest_tools": ["pytorch"],
        "missing_depth_tools": ["pytorch"],
    }]
    assert report["per_tool"]["pytorch"]["status"] == "passing"
    assert report["per_tool"]["pytorch"]["imported_in_sims"] == 2
    assert report["per_tool"]["pytorch"]["load_bearing_witnesses"] == 1
    assert report["per_tool"]["pytorch"]["missing_manifest"] == 1
    assert report["per_tool"]["pytorch"]["missing_depth"] == 1


def test_system_surface_audit_tool_integration_reports_failing_capability_probe(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_tool_probe_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    (probes / "sim_capability_cma_isolated.py").write_text(
        "TOOL_INTEGRATION_DEPTH = {'cma': 'load_bearing'}\n",
        encoding="utf-8",
    )
    (results / "sim_capability_cma_isolated_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()

    assert report["per_tool"]["cma"]["status"] == "probe_failing"
    assert report["per_tool"]["cma"]["probe_files"] == [
        "system_v4/probes/sim_capability_cma_isolated.py"
    ]


def test_system_surface_audit_tool_integration_reports_bundle_witnesses(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_bundle_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "pytorch": (
            "sim_pytorch_capability.py",
            "pytorch_capability_results.json",
        ),
        "datasketch": (
            "sim_capability_datasketch_isolated.py",
            "sim_capability_datasketch_isolated_results.json",
        ),
        "pynndescent": (
            "sim_capability_pynndescent_isolated.py",
            "sim_capability_pynndescent_isolated_results.json",
        ),
        "umap": (
            "sim_capability_umap_isolated.py",
            "sim_capability_umap_isolated_results.json",
        ),
        "hdbscan": (
            "sim_capability_hdbscan_isolated.py",
            "sim_capability_hdbscan_isolated_results.json",
        ),
        "sklearn": (
            "sim_capability_sklearn_isolated.py",
            "sim_capability_sklearn_isolated_results.json",
        ),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_manifold_cluster_stack.py").write_text(
        "\n".join(
            [
                "import torch",
                "import hdbscan",
                "import umap",
                "from datasketch import MinHash",
                "from pynndescent import NNDescent",
                "from sklearn.metrics import adjusted_rand_score",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor manifold'},",
                "    'datasketch': {'tried': True, 'used': True, 'reason': 'signature witness'},",
                "    'pynndescent': {'tried': True, 'used': True, 'reason': 'ann witness'},",
                "    'umap': {'tried': True, 'used': True, 'reason': 'embedding witness'},",
                "    'hdbscan': {'tried': True, 'used': True, 'reason': 'density witness'},",
                "    'sklearn': {'tried': True, 'used': True, 'reason': 'metric witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'datasketch': 'load_bearing',",
                "    'pynndescent': 'load_bearing',",
                "    'umap': 'load_bearing',",
                "    'hdbscan': 'load_bearing',",
                "    'sklearn': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()
    bundle = report["bundles"]["manifold_cluster_stack"]

    assert report["per_tool"]["umap"]["imported_in_sims"] == 1
    assert report["per_tool"]["hdbscan"]["imported_in_sims"] == 1
    assert report["per_tool"]["pynndescent"]["imported_in_sims"] == 1
    assert report["per_tool"]["sklearn"]["imported_in_sims"] == 1
    assert bundle["capability_gap_tools"] == []
    assert bundle["weak_tools"] == []
    assert bundle["full_bundle_witness_count"] == 1
    assert bundle["needs_reference_sim"] is False
    assert bundle["best_existing_witnesses"][0]["sim"] == "sim_integration_manifold_cluster_stack.py"
    assert bundle["best_existing_witnesses"][0]["imported_overlap_count"] == 6


def test_system_surface_audit_reports_search_archive_bundle_witness(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_search_archive_bundle_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "optuna": ("sim_capability_optuna_isolated.py", "sim_capability_optuna_isolated_results.json"),
        "pymoo": ("sim_capability_pymoo_isolated.py", "sim_capability_pymoo_isolated_results.json"),
        "ribs": ("sim_capability_ribs_isolated.py", "sim_capability_ribs_isolated_results.json"),
        "deap": ("sim_capability_deap_isolated.py", "sim_capability_deap_isolated_results.json"),
        "evotorch": ("sim_capability_evotorch_isolated.py", "sim_capability_evotorch_isolated_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_search_archive_stack.py").write_text(
        "\n".join(
            [
                "import torch",
                "import optuna",
                "from deap import base",
                "from evotorch import Problem",
                "from pymoo.algorithms.moo.nsga2 import NSGA2",
                "from ribs.archives import GridArchive",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'objective'},",
                "    'optuna': {'tried': True, 'used': True, 'reason': 'tpe'},",
                "    'pymoo': {'tried': True, 'used': True, 'reason': 'pareto'},",
                "    'ribs': {'tried': True, 'used': True, 'reason': 'archive'},",
                "    'deap': {'tried': True, 'used': True, 'reason': 'ga'},",
                "    'evotorch': {'tried': True, 'used': True, 'reason': 'snes'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'optuna': 'load_bearing',",
                "    'pymoo': 'load_bearing',",
                "    'ribs': 'load_bearing',",
                "    'deap': 'load_bearing',",
                "    'evotorch': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()
    bundle = report["bundles"]["search_archive_stack"]

    assert report["per_tool"]["optuna"]["imported_in_sims"] == 1
    assert report["per_tool"]["pymoo"]["imported_in_sims"] == 1
    assert report["per_tool"]["ribs"]["imported_in_sims"] == 1
    assert report["per_tool"]["deap"]["imported_in_sims"] == 1
    assert report["per_tool"]["evotorch"]["imported_in_sims"] == 1
    assert bundle["capability_gap_tools"] == []
    assert bundle["weak_tools"] == []
    assert bundle["full_bundle_witness_count"] == 1
    assert bundle["needs_reference_sim"] is False
    assert bundle["best_existing_witnesses"][0]["sim"] == "sim_integration_search_archive_stack.py"
    assert bundle["best_existing_witnesses"][0]["imported_overlap_count"] == 6


def test_system_surface_audit_reports_manifold_search_archive_bundle_witness(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_manifold_search_archive_bundle_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "datasketch": ("sim_capability_datasketch_isolated.py", "sim_capability_datasketch_isolated_results.json"),
        "pynndescent": ("sim_capability_pynndescent_isolated.py", "sim_capability_pynndescent_isolated_results.json"),
        "umap": ("sim_capability_umap_isolated.py", "sim_capability_umap_isolated_results.json"),
        "hdbscan": ("sim_capability_hdbscan_isolated.py", "sim_capability_hdbscan_isolated_results.json"),
        "sklearn": ("sim_capability_sklearn_isolated.py", "sim_capability_sklearn_isolated_results.json"),
        "optuna": ("sim_capability_optuna_isolated.py", "sim_capability_optuna_isolated_results.json"),
        "ribs": ("sim_capability_ribs_isolated.py", "sim_capability_ribs_isolated_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_manifold_search_archive_stack.py").write_text(
        "\n".join(
            [
                "import torch",
                "import optuna",
                "import hdbscan",
                "import umap",
                "from datasketch import MinHash",
                "from pynndescent import NNDescent",
                "from ribs.archives import GridArchive",
                "from sklearn.metrics import adjusted_rand_score",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor manifold'},",
                "    'datasketch': {'tried': True, 'used': True, 'reason': 'signature witness'},",
                "    'pynndescent': {'tried': True, 'used': True, 'reason': 'ann witness'},",
                "    'umap': {'tried': True, 'used': True, 'reason': 'embedding witness'},",
                "    'hdbscan': {'tried': True, 'used': True, 'reason': 'density witness'},",
                "    'sklearn': {'tried': True, 'used': True, 'reason': 'metric witness'},",
                "    'optuna': {'tried': True, 'used': True, 'reason': 'search witness'},",
                "    'ribs': {'tried': True, 'used': True, 'reason': 'archive witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'datasketch': 'load_bearing',",
                "    'pynndescent': 'load_bearing',",
                "    'umap': 'load_bearing',",
                "    'hdbscan': 'load_bearing',",
                "    'sklearn': 'load_bearing',",
                "    'optuna': 'load_bearing',",
                "    'ribs': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()
    bundle = report["bundles"]["manifold_search_archive_stack"]

    assert report["per_tool"]["optuna"]["imported_in_sims"] == 1
    assert report["per_tool"]["ribs"]["imported_in_sims"] == 1
    assert report["per_tool"]["umap"]["imported_in_sims"] == 1
    assert report["per_tool"]["hdbscan"]["imported_in_sims"] == 1
    assert bundle["capability_gap_tools"] == []
    assert bundle["weak_tools"] == []
    assert bundle["full_bundle_witness_count"] == 1
    assert bundle["needs_reference_sim"] is False
    assert bundle["best_existing_witnesses"][0]["sim"] == "sim_integration_manifold_search_archive_stack.py"
    assert bundle["best_existing_witnesses"][0]["imported_overlap_count"] == 8


def test_system_surface_audit_reports_symbolic_graph_topology_bundle_witness(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_symbolic_graph_topology_bundle_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "z3": ("sim_z3_capability.py", "z3_capability_results.json"),
        "cvc5": ("sim_capability_cvc5_isolated.py", "sim_capability_cvc5_isolated_results.json"),
        "sympy": ("sim_sympy_capability.py", "sympy_capability_results.json"),
        "clifford": ("sim_capability_clifford_isolated.py", "sim_capability_clifford_isolated_results.json"),
        "pyg": ("sim_capability_pyg_isolated.py", "sim_capability_pyg_isolated_results.json"),
        "rustworkx": ("sim_capability_rustworkx_isolated.py", "sim_capability_rustworkx_isolated_results.json"),
        "xgi": ("sim_capability_xgi_isolated.py", "sim_capability_xgi_isolated_results.json"),
        "toponetx": ("sim_capability_toponetx_isolated.py", "sim_capability_toponetx_isolated_results.json"),
        "gudhi": ("sim_capability_gudhi_isolated.py", "sim_capability_gudhi_isolated_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_symbolic_graph_topology_stack.py").write_text(
        "\n".join(
            [
                "import torch",
                "import cvc5",
                "import gudhi",
                "import rustworkx",
                "import sympy",
                "import xgi",
                "from clifford import Cl",
                "from toponetx.classes import SimplicialComplex",
                "from torch_geometric.data import Data",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'solver'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'solver cross-check'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'rotor'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'graph tensor'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'graph algo'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'hypergraph'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell complex'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'persistence'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()
    bundle = report["bundles"]["symbolic_graph_topology_stack"]

    assert report["per_tool"]["cvc5"]["imported_in_sims"] == 1
    assert report["per_tool"]["clifford"]["imported_in_sims"] == 1
    assert report["per_tool"]["pyg"]["imported_in_sims"] == 1
    assert report["per_tool"]["gudhi"]["imported_in_sims"] == 1
    assert bundle["capability_gap_tools"] == []
    assert bundle["weak_tools"] == []
    assert bundle["full_bundle_witness_count"] == 1
    assert bundle["needs_reference_sim"] is False
    assert bundle["best_existing_witnesses"][0]["sim"] == "sim_integration_symbolic_graph_topology_stack.py"
    assert bundle["best_existing_witnesses"][0]["imported_overlap_count"] == 10


def test_system_surface_audit_reports_symbolic_graph_manifold_bundle_witness(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_symbolic_graph_manifold_bundle_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "z3": ("sim_z3_capability.py", "z3_capability_results.json"),
        "cvc5": ("sim_cvc5_capability.py", "cvc5_capability_results.json"),
        "sympy": ("sim_sympy_capability.py", "sympy_capability_results.json"),
        "clifford": ("sim_clifford_capability.py", "clifford_capability_results.json"),
        "pyg": ("sim_pyg_capability.py", "pyg_capability_results.json"),
        "rustworkx": ("sim_rustworkx_capability.py", "rustworkx_capability_results.json"),
        "xgi": ("sim_xgi_capability.py", "xgi_capability_results.json"),
        "toponetx": ("sim_toponetx_capability.py", "toponetx_capability_results.json"),
        "gudhi": ("sim_gudhi_capability.py", "gudhi_capability_results.json"),
        "datasketch": ("sim_datasketch_capability.py", "datasketch_capability_results.json"),
        "pynndescent": ("sim_pynndescent_capability.py", "pynndescent_capability_results.json"),
        "umap": ("sim_umap_capability.py", "umap_capability_results.json"),
        "hdbscan": ("sim_hdbscan_capability.py", "hdbscan_capability_results.json"),
        "sklearn": ("sim_sklearn_capability.py", "sklearn_capability_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_symbolic_graph_manifold_stack.py").write_text(
        "\n".join(
            [
                "import cvc5",
                "import gudhi",
                "import hdbscan",
                "import rustworkx",
                "import sympy",
                "import torch",
                "import umap",
                "import xgi",
                "from clifford import Cl",
                "from datasketch import MinHash",
                "from pynndescent import NNDescent",
                "from sklearn.metrics import adjusted_rand_score",
                "from toponetx.classes import SimplicialComplex",
                "from torch_geometric.data import Data",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor lane'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'solver lane'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'solver cross-check'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic lane'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'rotor lane'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'graph lane'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'diameter lane'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'hypergraph lane'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'simplicial lane'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'persistence lane'},",
                "    'datasketch': {'tried': True, 'used': True, 'reason': 'signature lane'},",
                "    'pynndescent': {'tried': True, 'used': True, 'reason': 'ann lane'},",
                "    'umap': {'tried': True, 'used': True, 'reason': 'embedding lane'},",
                "    'hdbscan': {'tried': True, 'used': True, 'reason': 'clustering lane'},",
                "    'sklearn': {'tried': True, 'used': True, 'reason': 'metric lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'datasketch': 'load_bearing',",
                "    'pynndescent': 'load_bearing',",
                "    'umap': 'load_bearing',",
                "    'hdbscan': 'load_bearing',",
                "    'sklearn': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()
    bundle = report["bundles"]["symbolic_graph_manifold_stack"]

    assert bundle["capability_gap_tools"] == []
    assert bundle["weak_tools"] == []
    assert bundle["full_bundle_witness_count"] == 1
    assert bundle["best_existing_witnesses"][0]["sim"] == "sim_integration_symbolic_graph_manifold_stack.py"
    assert bundle["best_existing_witnesses"][0]["imported_overlap_count"] == 15


def test_system_surface_audit_reports_symbolic_graph_manifold_search_bundle_witness(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_symbolic_graph_manifold_search_bundle_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "z3": ("sim_z3_capability.py", "z3_capability_results.json"),
        "cvc5": ("sim_cvc5_capability.py", "cvc5_capability_results.json"),
        "sympy": ("sim_sympy_capability.py", "sympy_capability_results.json"),
        "clifford": ("sim_clifford_capability.py", "clifford_capability_results.json"),
        "pyg": ("sim_pyg_capability.py", "pyg_capability_results.json"),
        "rustworkx": ("sim_rustworkx_capability.py", "rustworkx_capability_results.json"),
        "xgi": ("sim_xgi_capability.py", "xgi_capability_results.json"),
        "toponetx": ("sim_toponetx_capability.py", "toponetx_capability_results.json"),
        "gudhi": ("sim_gudhi_capability.py", "gudhi_capability_results.json"),
        "datasketch": ("sim_datasketch_capability.py", "datasketch_capability_results.json"),
        "pynndescent": ("sim_pynndescent_capability.py", "pynndescent_capability_results.json"),
        "umap": ("sim_umap_capability.py", "umap_capability_results.json"),
        "hdbscan": ("sim_hdbscan_capability.py", "hdbscan_capability_results.json"),
        "sklearn": ("sim_sklearn_capability.py", "sklearn_capability_results.json"),
        "optuna": ("sim_optuna_capability.py", "optuna_capability_results.json"),
        "pymoo": ("sim_pymoo_capability.py", "pymoo_capability_results.json"),
        "ribs": ("sim_ribs_capability.py", "ribs_capability_results.json"),
        "deap": ("sim_deap_capability.py", "deap_capability_results.json"),
        "evotorch": ("sim_evotorch_capability.py", "evotorch_capability_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_symbolic_graph_manifold_search_stack.py").write_text(
        "\n".join(
            [
                "import cvc5",
                "import gudhi",
                "import hdbscan",
                "import optuna",
                "import rustworkx",
                "import sympy",
                "import torch",
                "import umap",
                "import xgi",
                "from clifford import Cl",
                "from datasketch import MinHash",
                "from deap import base",
                "from evotorch import Problem",
                "from pymoo.algorithms.moo.nsga2 import NSGA2",
                "from pynndescent import NNDescent",
                "from ribs.archives import GridArchive",
                "from sklearn.metrics import adjusted_rand_score",
                "from toponetx.classes import SimplicialComplex",
                "from torch_geometric.data import Data",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor lane'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'solver lane'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'solver cross-check'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic lane'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'rotor lane'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'graph lane'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'diameter lane'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'hypergraph lane'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'simplicial lane'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'persistence lane'},",
                "    'datasketch': {'tried': True, 'used': True, 'reason': 'signature lane'},",
                "    'pynndescent': {'tried': True, 'used': True, 'reason': 'ann lane'},",
                "    'umap': {'tried': True, 'used': True, 'reason': 'embedding lane'},",
                "    'hdbscan': {'tried': True, 'used': True, 'reason': 'cluster lane'},",
                "    'sklearn': {'tried': True, 'used': True, 'reason': 'metric lane'},",
                "    'optuna': {'tried': True, 'used': True, 'reason': 'search lane'},",
                "    'pymoo': {'tried': True, 'used': True, 'reason': 'moo lane'},",
                "    'ribs': {'tried': True, 'used': True, 'reason': 'archive lane'},",
                "    'deap': {'tried': True, 'used': True, 'reason': 'ga lane'},",
                "    'evotorch': {'tried': True, 'used': True, 'reason': 'es lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'datasketch': 'load_bearing',",
                "    'pynndescent': 'load_bearing',",
                "    'umap': 'load_bearing',",
                "    'hdbscan': 'load_bearing',",
                "    'sklearn': 'load_bearing',",
                "    'optuna': 'load_bearing',",
                "    'pymoo': 'load_bearing',",
                "    'ribs': 'load_bearing',",
                "    'deap': 'load_bearing',",
                "    'evotorch': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()
    bundle = report["bundles"]["symbolic_graph_manifold_search_stack"]

    assert bundle["capability_gap_tools"] == []
    assert bundle["weak_tools"] == []
    assert bundle["full_bundle_witness_count"] == 1
    assert bundle["best_existing_witnesses"][0]["sim"] == "sim_integration_symbolic_graph_manifold_search_stack.py"
    assert bundle["best_existing_witnesses"][0]["imported_overlap_count"] == 20


def test_system_surface_audit_reports_equivariant_symbolic_graph_manifold_search_bundle_witness(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_equivariant_symbolic_graph_manifold_search_bundle_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "z3": ("sim_z3_capability.py", "z3_capability_results.json"),
        "cvc5": ("sim_cvc5_capability.py", "cvc5_capability_results.json"),
        "sympy": ("sim_sympy_capability.py", "sympy_capability_results.json"),
        "clifford": ("sim_clifford_capability.py", "clifford_capability_results.json"),
        "e3nn": ("sim_e3nn_capability.py", "e3nn_capability_results.json"),
        "geomstats": ("sim_geomstats_capability.py", "geomstats_capability_results.json"),
        "pyg": ("sim_pyg_capability.py", "pyg_capability_results.json"),
        "rustworkx": ("sim_rustworkx_capability.py", "rustworkx_capability_results.json"),
        "xgi": ("sim_xgi_capability.py", "xgi_capability_results.json"),
        "toponetx": ("sim_toponetx_capability.py", "toponetx_capability_results.json"),
        "gudhi": ("sim_gudhi_capability.py", "gudhi_capability_results.json"),
        "datasketch": ("sim_datasketch_capability.py", "datasketch_capability_results.json"),
        "pynndescent": ("sim_pynndescent_capability.py", "pynndescent_capability_results.json"),
        "umap": ("sim_umap_capability.py", "umap_capability_results.json"),
        "hdbscan": ("sim_hdbscan_capability.py", "hdbscan_capability_results.json"),
        "sklearn": ("sim_sklearn_capability.py", "sklearn_capability_results.json"),
        "optuna": ("sim_optuna_capability.py", "optuna_capability_results.json"),
        "pymoo": ("sim_pymoo_capability.py", "pymoo_capability_results.json"),
        "ribs": ("sim_ribs_capability.py", "ribs_capability_results.json"),
        "deap": ("sim_deap_capability.py", "deap_capability_results.json"),
        "evotorch": ("sim_evotorch_capability.py", "evotorch_capability_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_equivariant_symbolic_graph_manifold_search_stack.py").write_text(
        "\n".join(
            [
                "import cvc5",
                "import gudhi",
                "import hdbscan",
                "import optuna",
                "import rustworkx",
                "import sympy",
                "import torch",
                "import umap",
                "import xgi",
                "import geomstats.backend as gs",
                "from clifford import Cl",
                "from datasketch import MinHash",
                "from deap import base",
                "from e3nn import o3",
                "from evotorch import Problem",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from pymoo.algorithms.moo.nsga2 import NSGA2",
                "from pynndescent import NNDescent",
                "from ribs.archives import GridArchive",
                "from sklearn.metrics import adjusted_rand_score",
                "from toponetx.classes import SimplicialComplex",
                "from torch_geometric.data import Data",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor lane'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'solver lane'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'solver cross-check'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic lane'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'rotor lane'},",
                "    'e3nn': {'tried': True, 'used': True, 'reason': 'equivariant lane'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'riemannian lane'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'graph lane'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'diameter lane'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'hypergraph lane'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'simplicial lane'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'persistence lane'},",
                "    'datasketch': {'tried': True, 'used': True, 'reason': 'signature lane'},",
                "    'pynndescent': {'tried': True, 'used': True, 'reason': 'ann lane'},",
                "    'umap': {'tried': True, 'used': True, 'reason': 'embedding lane'},",
                "    'hdbscan': {'tried': True, 'used': True, 'reason': 'cluster lane'},",
                "    'sklearn': {'tried': True, 'used': True, 'reason': 'metric lane'},",
                "    'optuna': {'tried': True, 'used': True, 'reason': 'search lane'},",
                "    'pymoo': {'tried': True, 'used': True, 'reason': 'moo lane'},",
                "    'ribs': {'tried': True, 'used': True, 'reason': 'archive lane'},",
                "    'deap': {'tried': True, 'used': True, 'reason': 'ga lane'},",
                "    'evotorch': {'tried': True, 'used': True, 'reason': 'es lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'e3nn': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'datasketch': 'load_bearing',",
                "    'pynndescent': 'load_bearing',",
                "    'umap': 'load_bearing',",
                "    'hdbscan': 'load_bearing',",
                "    'sklearn': 'load_bearing',",
                "    'optuna': 'load_bearing',",
                "    'pymoo': 'load_bearing',",
                "    'ribs': 'load_bearing',",
                "    'deap': 'load_bearing',",
                "    'evotorch': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()
    bundle = report["bundles"]["equivariant_symbolic_graph_manifold_search_stack"]

    assert bundle["capability_gap_tools"] == []
    assert bundle["weak_tools"] == []
    assert bundle["full_bundle_witness_count"] == 1
    assert bundle["best_existing_witnesses"][0]["sim"] == "sim_integration_equivariant_symbolic_graph_manifold_search_stack.py"
    assert bundle["best_existing_witnesses"][0]["imported_overlap_count"] == 22


def test_system_surface_audit_reports_quantum_ga_bridge_bundle_witness(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_quantum_ga_bridge_bundle_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "numpy": ("sim_numpy_capability.py", "numpy_capability_results.json"),
        "scipy": ("sim_scipy_capability.py", "scipy_capability_results.json"),
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "clifford": ("sim_clifford_capability.py", "clifford_capability_results.json"),
        "torch_ga": ("sim_torch_ga_capability.py", "torch_ga_capability_results.json"),
        "qutip": ("sim_qutip_capability.py", "qutip_capability_results.json"),
        "cirq": ("sim_cirq_capability.py", "cirq_capability_results.json"),
        "pennylane": ("sim_pennylane_capability.py", "pennylane_capability_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_quantum_ga_bridge_stack.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "import torch",
                "import torch_ga",
                "from clifford import Cl",
                "from scipy.linalg import expm",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'dense state lane'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'matrix exponential lane'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'bloch tensor lane'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'clifford embedding lane'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'torch GA lane'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'density witness lane'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'circuit witness lane'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'qnode witness lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'load_bearing',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'qutip': 'load_bearing',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()
    bundle = report["bundles"]["quantum_ga_bridge_stack"]

    assert bundle["capability_gap_tools"] == []
    assert bundle["weak_tools"] == []
    assert bundle["full_bundle_witness_count"] == 1
    assert bundle["best_existing_witnesses"][0]["sim"] == "sim_integration_quantum_ga_bridge_stack.py"
    assert bundle["best_existing_witnesses"][0]["imported_overlap_count"] == 8


def test_system_surface_audit_reports_additional_quantum_bridge_bundle_witnesses(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_additional_quantum_bridge_bundles_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "numpy": ("sim_numpy_capability.py", "numpy_capability_results.json"),
        "scipy": ("sim_scipy_capability.py", "scipy_capability_results.json"),
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "clifford": ("sim_clifford_capability.py", "clifford_capability_results.json"),
        "torch_ga": ("sim_torch_ga_capability.py", "torch_ga_capability_results.json"),
        "qutip": ("sim_qutip_capability.py", "qutip_capability_results.json"),
        "cirq": ("sim_cirq_capability.py", "cirq_capability_results.json"),
        "pennylane": ("sim_pennylane_capability.py", "pennylane_capability_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_qutip_open_system_bridge.py").write_text(
        "\n".join(
            [
                "import numpy as np",
                "import qutip",
                "from scipy.linalg import expm",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'density arithmetic'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'liouvillian witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'mesolve witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'supportive',",
                "    'qutip': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_integration_quantum_open_entanglement_stack.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "from scipy.linalg import expm",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'state arithmetic'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'matrix witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'open-system witness'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'entanglement circuit witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'entanglement qnode witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'supportive',",
                "    'qutip': 'load_bearing',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    (probes / "sim_integration_cirq_pennylane_entanglement_bridge.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import numpy as np",
                "import pennylane as qml",
                "from scipy.linalg import expm",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'state arithmetic'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'matrix witness'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'circuit witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'qnode witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'supportive',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_integration_quantum_ga_correlator_stack.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "import torch",
                "import torch_ga",
                "from clifford import Cl",
                "from scipy.linalg import expm",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'dense correlator arithmetic'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'matrix exponential witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'supportive density witness'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'circuit witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'qnode witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'correlator fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'geometric carrier witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga roundtrip witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'supportive',",
                "    'qutip': 'supportive',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    (probes / "sim_integration_torch_clifford_ga_rotor_bridge.py").write_text(
        "\n".join(
            [
                "import numpy as np",
                "import torch",
                "import torch_ga",
                "from clifford import Cl",
                "from scipy.linalg import expm",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'numeric carrier'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'matrix witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'rotor witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'supportive',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()

    qutip_bundle = report["bundles"]["qutip_open_system_stack"]
    assert qutip_bundle["capability_gap_tools"] == []
    assert qutip_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_qutip_open_system_bridge.py"
        for witness in qutip_bundle["best_existing_witnesses"]
    )

    open_ent_bundle = report["bundles"]["quantum_open_entanglement_stack"]
    assert open_ent_bundle["capability_gap_tools"] == []
    assert open_ent_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_quantum_open_entanglement_stack.py"
        for witness in open_ent_bundle["best_existing_witnesses"]
    )

    ent_bundle = report["bundles"]["cirq_pennylane_entanglement_stack"]
    assert ent_bundle["capability_gap_tools"] == []
    assert ent_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_cirq_pennylane_entanglement_bridge.py"
        for witness in ent_bundle["best_existing_witnesses"]
    )

    ga_bundle = report["bundles"]["quantum_ga_correlator_stack"]
    assert ga_bundle["capability_gap_tools"] == []
    assert ga_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_quantum_ga_correlator_stack.py"
        for witness in ga_bundle["best_existing_witnesses"]
    )

    rotor_bundle = report["bundles"]["torch_clifford_ga_rotor_stack"]
    assert rotor_bundle["capability_gap_tools"] == []
    assert rotor_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_torch_clifford_ga_rotor_bridge.py"
        for witness in rotor_bundle["best_existing_witnesses"]
    )


def test_system_surface_audit_reports_entropy_and_thermo_bridge_bundle_witnesses(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_entropy_thermo_bundles_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "numpy": ("sim_numpy_capability.py", "numpy_capability_results.json"),
        "scipy": ("sim_scipy_capability.py", "scipy_capability_results.json"),
        "torch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "pyg": ("sim_pyg_capability.py", "pyg_capability_results.json"),
        "cvc5": ("sim_cvc5_capability.py", "cvc5_capability_results.json"),
        "clifford": ("sim_clifford_capability.py", "clifford_capability_results.json"),
        "torch_ga": ("sim_torch_ga_capability.py", "torch_ga_capability_results.json"),
        "qutip": ("sim_qutip_capability.py", "qutip_capability_results.json"),
        "cirq": ("sim_cirq_capability.py", "cirq_capability_results.json"),
        "pennylane": ("sim_pennylane_capability.py", "pennylane_capability_results.json"),
        "geomstats": ("sim_geomstats_capability.py", "geomstats_capability_results.json"),
        "e3nn": ("sim_e3nn_capability.py", "e3nn_capability_results.json"),
        "rustworkx": ("sim_rustworkx_capability.py", "rustworkx_capability_results.json"),
        "xgi": ("sim_xgi_capability.py", "xgi_capability_results.json"),
        "toponetx": ("sim_toponetx_capability.py", "toponetx_capability_results.json"),
        "gudhi": ("sim_gudhi_capability.py", "gudhi_capability_results.json"),
        "sympy": ("sim_sympy_capability.py", "sympy_capability_results.json"),
        "z3": ("sim_z3_capability.py", "z3_capability_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_integration_quantum_open_entangle_correlator_mega_stack.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "import gudhi",
                "from clifford import Cl",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'state and correlator arithmetic'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'matrix exponential witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'open-system witness'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'entangling circuit witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'qnode entangling witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'correlator geometry witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'geometric carrier witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga roundtrip witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'shell dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'shell hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic shell witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'shell constraint witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'supportive',",
                "    'qutip': 'load_bearing',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_integration_classical_nonclassical_entropy_stack.py").write_text(
        "\n".join(
            [
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "import torch",
                "import torch_ga",
                "from clifford import Cl",
                "from scipy.linalg import expm",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'entropy arithmetic'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'state-preparation witness'},",
                "    'torch': {'tried': True, 'used': True, 'reason': 'entropy-gap autograd witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'bloch carrier witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'density entropy witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'statevector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga roundtrip witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'supportive',",
                "    'torch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'qutip': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_integration_thermo_open_system_bridge_stack.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "from scipy.linalg import expm",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'thermal populations and rate equations'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'thermal matrix exponential witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'master-equation witness'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'density-simulator witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'mixed-state witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'load_bearing',",
                "    'scipy': 'load_bearing',",
                "    'qutip': 'load_bearing',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_lambda_expansion_cosmology_stack.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import cvc5",
                "import e3nn",
                "import gudhi",
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from e3nn import o3",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from torch_geometric.data import Data",
                "from torch_geometric.nn import MessagePassing",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'lambda-shell arrays'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'expansion propagator witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'open-system shell witness'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'entangling source witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'qnode source witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'proxy fit witness'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'lambda-shell message-passing witness'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'lambda-shell contradiction witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'cosmology vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga vector witness'},",
                "    'e3nn': {'tried': True, 'used': True, 'reason': 'cosmology parity witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'shell dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'shell hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic shell witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'shell constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold shell witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'qutip': 'load_bearing',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'e3nn': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_lambda_crosslane_semantic_bridge.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import cvc5",
                "import e3nn",
                "import gudhi",
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from e3nn import o3",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from torch_geometric.data import Data",
                "from torch_geometric.nn import MessagePassing",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'cross-lane semantic vectors'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'semantic propagator witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'open-system source witness'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'entangling source witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'qnode source witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'cross-lane fit witness'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'cross-lane message-passing witness'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'cross-lane contradiction witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'semantic carrier witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga semantic carrier witness'},",
                "    'e3nn': {'tried': True, 'used': True, 'reason': 'cross-lane parity witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'cross-lane dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'cross-lane hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic semantic witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'cross-lane constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold semantic witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'qutip': 'load_bearing',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'e3nn': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_lambda_crosslane_result_audit.py").write_text(
        "\n".join(
            [
                "import cirq",
                "import cvc5",
                "import e3nn",
                "import gudhi",
                "import numpy as np",
                "import pennylane as qml",
                "import qutip",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from e3nn import o3",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from torch_geometric.data import Data",
                "from torch_geometric.nn import MessagePassing",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'persisted semantic vectors'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'persisted semantic propagator witness'},",
                "    'qutip': {'tried': True, 'used': True, 'reason': 'persisted open-system source witness'},",
                "    'cirq': {'tried': True, 'used': True, 'reason': 'persisted entangling source witness'},",
                "    'pennylane': {'tried': True, 'used': True, 'reason': 'persisted qnode source witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'persisted frontier fit witness'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'persisted message-passing witness'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'persisted contradiction witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'persisted semantic carrier witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'persisted ga semantic witness'},",
                "    'e3nn': {'tried': True, 'used': True, 'reason': 'persisted parity witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'persisted dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'persisted hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'persisted cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'persisted topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'persisted symbolic witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'persisted constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'persisted manifold witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'qutip': 'load_bearing',",
                "    'cirq': 'load_bearing',",
                "    'pennylane': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'e3nn': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_dynamic_shell.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'shell arrays'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'expansion propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'shell fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'shell vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga shell vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'shell dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'shell hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic shell witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'shell constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold shell witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_iscalar_sweep.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'option arrays'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'option propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'option fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'winner vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga winner vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'option dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'option hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic option witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'option constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold option witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_fep_compression_framing.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'framing aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'framing propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'framing fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'framing vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga framing vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'framing dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'framing hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic framing witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'framing constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold framing witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_fe_indexed_xi_hist.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'bridge aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'bridge propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'bridge fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'bridge vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga bridge vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'bridge dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'bridge hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic bridge witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'bridge constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold bridge witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_coarising_stress_test.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'operator aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'operator propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'operator fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'operator vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga operator vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'operator dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'operator hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic operator witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'operator constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold operator witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_bridge_search.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'candidate aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'candidate propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'candidate fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'candidate vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga candidate vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'candidate dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'candidate hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic candidate witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'candidate constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold candidate witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_phase3_composite.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'composite aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'composite propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'composite fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'composite vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga composite vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'composite dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'composite hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic composite witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'composite constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold composite witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_phase4_final_bridge.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'final-bridge aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'final-bridge propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'final-bridge fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'final-bridge vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga final-bridge vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'final-bridge dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'final-bridge hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic final-bridge witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'final-bridge constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold final-bridge witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_phase5a_marginal_preserving.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'preserving-surface aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'preserving-surface propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'preserving-surface fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'preserving-surface vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga preserving-surface vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'preserving-surface dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'preserving-surface hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic preserving-surface witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'preserving-surface constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold preserving-surface witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_phase5b_stability.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'stability-surface aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'stability-surface propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'stability-surface fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'stability-surface vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga stability-surface vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'stability-surface dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'stability-surface hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic stability-surface witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'stability-surface constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold stability-surface witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_phase5c_earned_vs_smuggled.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'honesty-surface aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'honesty-surface propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'honesty-surface fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'honesty-surface vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga honesty-surface vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'honesty-surface dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'honesty-surface hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic honesty-surface witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'honesty-surface constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold honesty-surface witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_phase6_clifford_anomaly.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'anomaly-surface aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'anomaly-surface propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'anomaly-surface fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'anomaly-surface vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga anomaly-surface vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'anomaly-surface dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'anomaly-surface hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic anomaly-surface witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'anomaly-surface constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold anomaly-surface witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_phase6_point_reference.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'point-reference aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'point-reference propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'point-reference fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'point-reference vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga point-reference vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'point-reference dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'point-reference hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic point-reference witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'point-reference constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold point-reference witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_chiral_deep_search.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'chiral-search aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'chiral-search propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'chiral-search fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'chiral-search vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga chiral-search vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'chiral-search dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'chiral-search hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic chiral-search witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'chiral-search constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold chiral-search witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_axis6_coupling_seam.py").write_text(
        "\n".join(
            [
                "import cvc5",
                "import e3nn",
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from e3nn import o3",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from torch_geometric.data import Data",
                "from torch_geometric.nn import MessagePassing",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam fit witness'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam message-passing witness'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam ranking contradiction witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga axis0-axis6 seam vector witness'},",
                "    'e3nn': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam parity witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic axis0-axis6 seam witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'axis0-axis6 seam constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold axis0-axis6 seam witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'e3nn': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_through_shells.py").write_text(
        "\n".join(
            [
                "import cvc5",
                "import e3nn",
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from e3nn import o3",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from torch_geometric.data import Data",
                "from torch_geometric.nn import MessagePassing",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'through-shells aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'through-shells propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'through-shells fit witness'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'through-shells message-passing witness'},",
                "    'cvc5': {'tried': True, 'used': True, 'reason': 'through-shells ranking contradiction witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'through-shells vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga through-shells vector witness'},",
                "    'e3nn': {'tried': True, 'used': True, 'reason': 'through-shells parity witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'through-shells dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'through-shells hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic through-shells witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'through-shells constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold through-shells witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'cvc5': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'e3nn': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_attractor_basin_boundary.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'attractor-boundary aggregates'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'attractor-boundary propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'attractor-boundary fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'attractor-boundary vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga attractor-boundary vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'attractor-boundary dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'attractor-boundary hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic attractor-boundary witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'attractor-boundary constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold attractor-boundary witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_kernel_phi0.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'kernel phi0 bridge numerics'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'kernel phi0 propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'kernel phi0 fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'kernel phi0 vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga kernel phi0 vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'kernel phi0 dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'kernel phi0 hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic kernel phi0 witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'kernel phi0 constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold kernel phi0 witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_cut_kernel_sweep.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'cut-kernel sweep numerics'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'cut-kernel sweep propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'cut-kernel sweep fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'cut-kernel sweep vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga cut-kernel sweep vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'cut-kernel sweep dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'cut-kernel sweep hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic cut-kernel witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'cut-kernel constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold cut-kernel witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_entropy_gradient_constraint_canonical.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'entropy-gradient numerics'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'entropy-gradient propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'entropy-gradient fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'entropy-gradient vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga entropy-gradient vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'entropy-gradient dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'entropy-gradient hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic entropy-gradient witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'entropy-gradient constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold entropy-gradient witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_orbit_phase_alignment.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'orbit-phase numerics'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'orbit-phase propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'orbit-phase fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'orbit-phase vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga orbit-phase vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'orbit-phase dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'orbit-phase hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic orbit-phase witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'orbit-phase constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold orbit-phase witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_gtower_gradient_cascade.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'G-tower numerics'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'G-tower propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'G-tower fit witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'G-tower vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga G-tower vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'G-tower dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'G-tower hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic G-tower witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'G-tower constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold G-tower witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (probes / "sim_axis0_pyg_proxy.py").write_text(
        "\n".join(
            [
                "import gudhi",
                "import numpy as np",
                "import rustworkx as rx",
                "import sympy as sp",
                "import torch",
                "import torch_ga",
                "import xgi",
                "from clifford import Cl",
                "from geomstats.geometry.hypersphere import Hypersphere",
                "from scipy.linalg import expm",
                "from toponetx import CellComplex",
                "from torch_geometric.data import HeteroData",
                "from torch_geometric.nn import MessagePassing",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'numpy': {'tried': True, 'used': True, 'reason': 'PyG proxy numerics'},",
                "    'scipy': {'tried': True, 'used': True, 'reason': 'PyG proxy propagator witness'},",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'PyG proxy fit witness'},",
                "    'pyg': {'tried': True, 'used': True, 'reason': 'PyG chain witness'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'PyG proxy vector witness'},",
                "    'torch_ga': {'tried': True, 'used': True, 'reason': 'ga PyG proxy vector witness'},",
                "    'rustworkx': {'tried': True, 'used': True, 'reason': 'PyG proxy dag witness'},",
                "    'xgi': {'tried': True, 'used': True, 'reason': 'PyG proxy hypergraph witness'},",
                "    'toponetx': {'tried': True, 'used': True, 'reason': 'cell-complex witness'},",
                "    'gudhi': {'tried': True, 'used': True, 'reason': 'topology witness'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic PyG proxy witness'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'PyG proxy constraint witness'},",
                "    'geomstats': {'tried': True, 'used': True, 'reason': 'manifold PyG proxy witness'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'numpy': 'supportive',",
                "    'scipy': 'load_bearing',",
                "    'pytorch': 'load_bearing',",
                "    'pyg': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "    'torch_ga': 'load_bearing',",
                "    'rustworkx': 'load_bearing',",
                "    'xgi': 'load_bearing',",
                "    'toponetx': 'load_bearing',",
                "    'gudhi': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'geomstats': 'load_bearing',",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()

    mega_bundle = report["bundles"]["quantum_open_entangle_correlator_mega_stack"]
    assert mega_bundle["capability_gap_tools"] == []
    assert mega_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_quantum_open_entangle_correlator_mega_stack.py"
        for witness in mega_bundle["best_existing_witnesses"]
    )

    entropy_bundle = report["bundles"]["classical_nonclassical_entropy_stack"]
    assert entropy_bundle["capability_gap_tools"] == []
    assert entropy_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_classical_nonclassical_entropy_stack.py"
        for witness in entropy_bundle["best_existing_witnesses"]
    )

    thermo_bundle = report["bundles"]["thermo_open_system_bridge_stack"]
    assert thermo_bundle["capability_gap_tools"] == []
    assert thermo_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_thermo_open_system_bridge_stack.py"
        for witness in thermo_bundle["best_existing_witnesses"]
    )

    axis0_bundle = report["bundles"]["axis0_dynamic_shell_stack"]
    assert axis0_bundle["capability_gap_tools"] == []
    assert axis0_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_integration_quantum_open_entangle_correlator_mega_stack.py"
        for witness in axis0_bundle["best_existing_witnesses"]
    )

    axis0_lambda_bundle = report["bundles"]["axis0_lambda_expansion_stack"]
    assert axis0_lambda_bundle["capability_gap_tools"] == []
    assert axis0_lambda_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_lambda_expansion_cosmology_stack.py"
        for witness in axis0_lambda_bundle["best_existing_witnesses"]
    )

    axis0_lambda_crosslane_bundle = report["bundles"]["axis0_lambda_crosslane_semantic_bridge_stack"]
    assert axis0_lambda_crosslane_bundle["capability_gap_tools"] == []
    assert axis0_lambda_crosslane_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_lambda_crosslane_semantic_bridge.py"
        for witness in axis0_lambda_crosslane_bundle["best_existing_witnesses"]
    )

    axis0_lambda_result_audit_bundle = report["bundles"]["axis0_lambda_crosslane_result_audit_stack"]
    assert axis0_lambda_result_audit_bundle["capability_gap_tools"] == []
    assert axis0_lambda_result_audit_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_lambda_crosslane_result_audit.py"
        for witness in axis0_lambda_result_audit_bundle["best_existing_witnesses"]
    )

    axis0_history_bundle = report["bundles"]["axis0_history_dynamic_shell_stack"]
    assert axis0_history_bundle["capability_gap_tools"] == []
    assert axis0_history_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_dynamic_shell.py"
        for witness in axis0_history_bundle["best_existing_witnesses"]
    )

    axis0_iscalar_bundle = report["bundles"]["axis0_iscalar_deep_stack"]
    assert axis0_iscalar_bundle["capability_gap_tools"] == []
    assert axis0_iscalar_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_iscalar_sweep.py"
        for witness in axis0_iscalar_bundle["best_existing_witnesses"]
    )

    axis0_fep_bundle = report["bundles"]["axis0_fep_framing_deep_stack"]
    assert axis0_fep_bundle["capability_gap_tools"] == []
    assert axis0_fep_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_fep_compression_framing.py"
        for witness in axis0_fep_bundle["best_existing_witnesses"]
    )

    axis0_fe_xi_bundle = report["bundles"]["axis0_fe_indexed_xi_hist_deep_stack"]
    assert axis0_fe_xi_bundle["capability_gap_tools"] == []
    assert axis0_fe_xi_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_fe_indexed_xi_hist.py"
        for witness in axis0_fe_xi_bundle["best_existing_witnesses"]
    )

    axis0_coarising_bundle = report["bundles"]["axis0_coarising_stress_deep_stack"]
    assert axis0_coarising_bundle["capability_gap_tools"] == []
    assert axis0_coarising_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_coarising_stress_test.py"
        for witness in axis0_coarising_bundle["best_existing_witnesses"]
    )

    axis0_bridge_bundle = report["bundles"]["axis0_bridge_search_deep_stack"]
    assert axis0_bridge_bundle["capability_gap_tools"] == []
    assert axis0_bridge_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_bridge_search.py"
        for witness in axis0_bridge_bundle["best_existing_witnesses"]
    )

    axis0_phase3_bundle = report["bundles"]["axis0_phase3_composite_deep_stack"]
    assert axis0_phase3_bundle["capability_gap_tools"] == []
    assert axis0_phase3_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_phase3_composite.py"
        for witness in axis0_phase3_bundle["best_existing_witnesses"]
    )

    axis0_phase4_bundle = report["bundles"]["axis0_phase4_final_bridge_deep_stack"]
    assert axis0_phase4_bundle["capability_gap_tools"] == []
    assert axis0_phase4_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_phase4_final_bridge.py"
        for witness in axis0_phase4_bundle["best_existing_witnesses"]
    )

    axis0_phase5a_bundle = report["bundles"]["axis0_phase5a_marginal_preserving_deep_stack"]
    assert axis0_phase5a_bundle["capability_gap_tools"] == []
    assert axis0_phase5a_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_phase5a_marginal_preserving.py"
        for witness in axis0_phase5a_bundle["best_existing_witnesses"]
    )

    axis0_phase5b_bundle = report["bundles"]["axis0_phase5b_stability_deep_stack"]
    assert axis0_phase5b_bundle["capability_gap_tools"] == []
    assert axis0_phase5b_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_phase5b_stability.py"
        for witness in axis0_phase5b_bundle["best_existing_witnesses"]
    )

    axis0_phase5c_bundle = report["bundles"]["axis0_phase5c_honesty_deep_stack"]
    assert axis0_phase5c_bundle["capability_gap_tools"] == []
    assert axis0_phase5c_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_phase5c_earned_vs_smuggled.py"
        for witness in axis0_phase5c_bundle["best_existing_witnesses"]
    )

    axis0_phase6_anomaly_bundle = report["bundles"]["axis0_phase6_clifford_anomaly_deep_stack"]
    assert axis0_phase6_anomaly_bundle["capability_gap_tools"] == []
    assert axis0_phase6_anomaly_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_phase6_clifford_anomaly.py"
        for witness in axis0_phase6_anomaly_bundle["best_existing_witnesses"]
    )

    axis0_phase6_point_reference_bundle = report["bundles"]["axis0_phase6_point_reference_deep_stack"]
    assert axis0_phase6_point_reference_bundle["capability_gap_tools"] == []
    assert axis0_phase6_point_reference_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_phase6_point_reference.py"
        for witness in axis0_phase6_point_reference_bundle["best_existing_witnesses"]
    )

    axis0_chiral_deep_search_bundle = report["bundles"]["axis0_chiral_deep_search_deep_stack"]
    assert axis0_chiral_deep_search_bundle["capability_gap_tools"] == []
    assert axis0_chiral_deep_search_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_chiral_deep_search.py"
        for witness in axis0_chiral_deep_search_bundle["best_existing_witnesses"]
    )

    axis0_axis6_seam_bundle = report["bundles"]["axis0_axis6_coupling_seam_deep_stack"]
    assert axis0_axis6_seam_bundle["capability_gap_tools"] == []
    assert axis0_axis6_seam_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_axis6_coupling_seam.py"
        for witness in axis0_axis6_seam_bundle["best_existing_witnesses"]
    )

    axis0_through_shells_bundle = report["bundles"]["axis0_through_shells_deep_stack"]
    assert axis0_through_shells_bundle["capability_gap_tools"] == []
    assert axis0_through_shells_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_through_shells.py"
        for witness in axis0_through_shells_bundle["best_existing_witnesses"]
    )

    axis0_attractor_boundary_bundle = report["bundles"]["axis0_attractor_basin_boundary_deep_stack"]
    assert axis0_attractor_boundary_bundle["capability_gap_tools"] == []
    assert axis0_attractor_boundary_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_attractor_basin_boundary.py"
        for witness in axis0_attractor_boundary_bundle["best_existing_witnesses"]
    )

    axis0_kernel_phi0_bundle = report["bundles"]["axis0_kernel_phi0_deep_stack"]
    assert axis0_kernel_phi0_bundle["capability_gap_tools"] == []
    assert axis0_kernel_phi0_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_kernel_phi0.py"
        for witness in axis0_kernel_phi0_bundle["best_existing_witnesses"]
    )

    axis0_cut_kernel_sweep_bundle = report["bundles"]["axis0_cut_kernel_sweep_deep_stack"]
    assert axis0_cut_kernel_sweep_bundle["capability_gap_tools"] == []
    assert axis0_cut_kernel_sweep_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_cut_kernel_sweep.py"
        for witness in axis0_cut_kernel_sweep_bundle["best_existing_witnesses"]
    )

    axis0_entropy_gradient_bundle = report["bundles"]["axis0_entropy_gradient_constraint_deep_stack"]
    assert axis0_entropy_gradient_bundle["capability_gap_tools"] == []
    assert axis0_entropy_gradient_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_entropy_gradient_constraint_canonical.py"
        for witness in axis0_entropy_gradient_bundle["best_existing_witnesses"]
    )

    axis0_orbit_phase_bundle = report["bundles"]["axis0_orbit_phase_alignment_deep_stack"]
    assert axis0_orbit_phase_bundle["capability_gap_tools"] == []
    assert axis0_orbit_phase_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_orbit_phase_alignment.py"
        for witness in axis0_orbit_phase_bundle["best_existing_witnesses"]
    )

    axis0_gtower_bundle = report["bundles"]["axis0_gtower_gradient_cascade_deep_stack"]
    assert axis0_gtower_bundle["capability_gap_tools"] == []
    assert axis0_gtower_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_gtower_gradient_cascade.py"
        for witness in axis0_gtower_bundle["best_existing_witnesses"]
    )

    axis0_pyg_proxy_bundle = report["bundles"]["axis0_pyg_proxy_deep_stack"]
    assert axis0_pyg_proxy_bundle["capability_gap_tools"] == []
    assert axis0_pyg_proxy_bundle["full_bundle_witness_count"] >= 1
    assert any(
        witness["sim"] == "sim_axis0_pyg_proxy.py"
        for witness in axis0_pyg_proxy_bundle["best_existing_witnesses"]
    )


def test_system_surface_audit_handles_nonliteral_manifest_and_depth_updates(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_nonliteral_headers_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    (probes / "sim_nonliteral_headers.py").write_text(
        "\n".join(
            [
                "_REASON = 'isolated tool probe'",
                "import optuna",
                "TOOL_MANIFEST = {",
                "    'optuna': {'tried': True, 'used': True, 'reason': _REASON},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}",
                "TOOL_INTEGRATION_DEPTH['optuna'] = 'load_bearing'",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_capability_optuna_isolated.py").write_text(
        "TOOL_INTEGRATION_DEPTH = {'optuna': 'load_bearing'}\n",
        encoding="utf-8",
    )
    (results / "sim_capability_optuna_isolated_results.json").write_text(
        '{"overall_pass": true}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()

    assert report["per_tool"]["optuna"]["imported_in_sims"] == 1
    assert report["per_tool"]["optuna"]["missing_manifest"] == 0
    assert report["per_tool"]["optuna"]["missing_depth"] == 0


def test_system_surface_audit_reports_top_stack_cover_and_companions(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_stack_cover_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    capability_specs = {
        "pytorch": ("sim_pytorch_capability.py", "pytorch_capability_results.json"),
        "z3": ("sim_z3_capability.py", "z3_capability_results.json"),
        "sympy": ("sim_sympy_capability.py", "sympy_capability_results.json"),
        "clifford": ("sim_clifford_capability.py", "clifford_capability_results.json"),
        "optuna": ("sim_optuna_capability.py", "optuna_capability_results.json"),
    }
    for tool, (probe_name, result_name) in capability_specs.items():
        (probes / probe_name).write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / result_name).write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    (probes / "sim_stack_anchor.py").write_text(
        "\n".join(
            [
                "import optuna",
                "import sympy",
                "import torch",
                "from clifford import Cl",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor lane'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'solver lane'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic lane'},",
                "    'clifford': {'tried': True, 'used': True, 'reason': 'rotor lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "    'clifford': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_stack_search_bridge.py").write_text(
        "\n".join(
            [
                "import optuna",
                "import torch",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor lane'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'solver lane'},",
                "    'optuna': {'tried': True, 'used': True, 'reason': 'search lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "    'optuna': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_stack_partial.py").write_text(
        "\n".join(
            [
                "import optuna",
                "import sympy",
                "import torch",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor lane'},",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'sympy': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_stack_solver_only.py").write_text(
        "\n".join(
            [
                "import torch",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor lane'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'solver lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface(limit=5)

    assert report["max_stack_sims"][0]["sim"] == "sim_stack_anchor.py"
    assert report["max_stack_sims"][0]["load_bearing_tool_count"] == 4

    greedy_cover = report["greedy_declared_cover"]
    assert greedy_cover["target_tool_count"] == 5
    assert greedy_cover["covered_tool_count"] == 5
    assert greedy_cover["uncovered_tools"] == []
    assert [row["sim"] for row in greedy_cover["selected_sims"][:2]] == [
        "sim_stack_anchor.py",
        "sim_stack_search_bridge.py",
    ]

    pytorch_companions = report["per_tool_best_companions"]["pytorch"]
    assert pytorch_companions["best_companions"][0]["tool"] == "z3"
    assert pytorch_companions["best_companions"][0]["co_load_bearing_sims"] == 3
    assert pytorch_companions["best_anchor_sims"][0]["sim"] == "sim_stack_anchor.py"


def test_system_surface_audit_reports_classical_surface(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_classical_surface_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)

    for tool in ("pytorch", "z3"):
        (probes / f"sim_{tool}_capability.py").write_text(
            f"TOOL_INTEGRATION_DEPTH = {{'{tool}': 'load_bearing'}}\n",
            encoding="utf-8",
        )
        (results / f"{tool}_capability_results.json").write_text(
            '{"overall_pass": true}\n',
            encoding="utf-8",
        )

    anchor = probes / "sim_integration_classical_anchor.py"
    anchor.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'divergence_log = "Classical integration reference."',
                "import torch",
                "from z3 import Solver",
                "TOOL_MANIFEST = {",
                "    'pytorch': {'tried': True, 'used': True, 'reason': 'tensor lane'},",
                "    'z3': {'tried': True, 'used': True, 'reason': 'solver lane'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'pytorch': 'load_bearing',",
                "    'z3': 'load_bearing',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (results / "sim_integration_classical_anchor_results.json").write_text(
        '{"overall_pass": true}\n',
        encoding="utf-8",
    )

    stale = probes / "sim_classical_stale.py"
    stale.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'divergence_log = "Classical supportive baseline."',
                "import sympy",
                "TOOL_MANIFEST = {",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic baseline'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'sympy': 'supportive',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    stale_result = results / "sim_classical_stale_results.json"
    stale_result.write_text('{"overall_pass": true}\n', encoding="utf-8")

    unknown = probes / "sim_classical_unknown.py"
    unknown.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'divergence_log = "Classical unknown-shape baseline."',
                "import sympy",
                "TOOL_MANIFEST = {",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic baseline'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'sympy': 'supportive',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (results / "sim_classical_unknown_results.json").write_text(
        '{"summary": {"note": "unknown legacy shape"}}\n',
        encoding="utf-8",
    )

    failed = probes / "sim_classical_fail.py"
    failed.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'divergence_log = "Classical failing baseline."',
                "import sympy",
                "TOOL_MANIFEST = {",
                "    'sympy': {'tried': True, 'used': True, 'reason': 'symbolic baseline'},",
                "}",
                "TOOL_INTEGRATION_DEPTH = {",
                "    'sympy': 'supportive',",
                "}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (results / "sim_classical_fail_results.json").write_text(
        '{"overall_pass": false}\n',
        encoding="utf-8",
    )

    missing = probes / "sim_classical_missing_contract.py"
    missing.write_text(
        'classification = "classical_baseline"\n',
        encoding="utf-8",
    )

    base_time = time.time()
    os.utime(stale_result, (base_time - 20, base_time - 20))
    os.utime(stale, (base_time, base_time))

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULT_ROOTS", [results])
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.classical_surface(limit=5)

    assert report["count"] == 5
    assert report["result_states"]["pass"] == 2
    assert report["result_states"]["fail"] == 1
    assert report["result_states"]["unknown"] == 1
    assert report["result_states"]["no_result"] == 1
    assert report["result_states"]["stale_source_newer"] == 1
    assert report["samples"]["stale_source_newer"] == ["sim_classical_stale.py"]
    assert report["lint"]["counts"]["clean"] == 4
    assert report["lint"]["counts"]["violating_sims"] == 1
    assert report["lint"]["counts"]["C2_manifest_missing"] == 1
    assert report["lint"]["counts"]["C3_depth_missing"] == 1
    assert report["lint"]["counts"]["C4_divergence_log_missing"] == 1
    assert report["tool_integration"]["max_stack_sims"][0]["sim"] == "sim_integration_classical_anchor.py"
    assert report["tool_integration"]["max_stack_sims"][0]["load_bearing_tool_count"] == 2


def test_system_surface_audit_runner_health_reports_draining() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_runner_health_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    health = module._runner_health(
        {"lane_A": 1, "lane_B": 2, "claimed": 3, "done": 10},
        {
            "lane_A": {"active_within_60s": False},
            "lane_B": {"active_within_60s": True},
            "claimed": {"active_within_60s": True},
            "done": {"active_within_60s": True},
        },
    )

    assert health["status"] == "draining"


def test_system_surface_audit_runner_health_reports_long_claims() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_runner_health_long_claims_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    health = module._runner_health(
        {"lane_A": 0, "lane_B": 5, "claimed": 2, "done": 10},
        {
            "lane_A": {"active_within_60s": False},
            "lane_B": {"active_within_60s": True},
            "claimed": {"active_within_60s": True},
            "done": {"active_within_60s": True},
        },
        {"over_900s": 1},
    )

    assert health["status"] == "draining_with_long_claims"


def test_system_surface_audit_runner_warnings_report_long_claims() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_runner_warnings_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    warnings = module._runner_warnings(
        {"lane_A": 1, "lane_B": 2, "claimed": 1, "done": 10},
        {
            "lane_A": {"active_within_60s": False},
            "lane_B": {"active_within_60s": True},
            "claimed": {"active_within_60s": True},
            "done": {"active_within_60s": True},
        },
        {"over_300s": 1, "over_900s": 0},
    )

    assert warnings == ["1 claim(s) over 300s"]


def test_system_surface_audit_runner_warnings_report_blocked_duplicates() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_runner_blocked_warnings_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    warnings = module._runner_warnings(
        {"lane_A": 1, "lane_B": 2, "claimed": 0, "done": 10},
        {
            "lane_A": {"active_within_60s": True},
            "lane_B": {"active_within_60s": True},
            "claimed": {"active_within_60s": False},
            "done": {"active_within_60s": True},
        },
        {"over_300s": 0, "over_900s": 0},
        {"active_count": 9, "unique_sims": 3, "duplicate_entries": 6},
    )

    assert warnings == ["9 blocked entry(s) across 3 unique sim(s)"]


def test_system_surface_audit_blocked_surface_reports_reasons_and_duplicates(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_blocked_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    queue_root = tmp_path / "queue"
    blocked = queue_root / "blocked"
    resolved = blocked / "resolved"
    blocked.mkdir(parents=True, exist_ok=True)
    resolved.mkdir(parents=True, exist_ok=True)
    for name in ("a.json.1.host.w1", "a.json.2.host.w2"):
        (blocked / name).write_text(
            json.dumps(
                {
                    "sim_path": "/tmp/sim_alpha.py",
                    "lane": "lane_A",
                    "blocked_reason": "gate_denied",
                }
            ),
            encoding="utf-8",
        )
    (blocked / "b.json.1.host.w1").write_text(
        json.dumps(
            {
                "sim_path": "/tmp/sim_beta.py",
                "lane": "lane_B",
                "blocked_reason": "blacklisted_meta_sim",
            }
        ),
        encoding="utf-8",
    )
    (resolved / "old.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(module.adaptive_controller, "QUEUE", queue_root)

    report = module._blocked_surface()

    assert report["active_count"] == 3
    assert report["resolved_count"] == 1
    assert report["reasons"] == {"gate_denied": 2, "blacklisted_meta_sim": 1}
    assert report["unique_sims"] == 2
    assert report["duplicate_entries"] == 1
    assert report["duplicate_sims"] == {"sim_alpha.py": 2}


def test_system_surface_audit_claimed_age_surface_uses_claimed_at(tmp_path) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_claimed_age_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    claimed = tmp_path / "claimed"
    claimed.mkdir()
    (claimed / "sample.json.1.host.laneB_w1").write_text(
        json.dumps({"sim_path": "/tmp/sim_alpha.py", "claimed_at": time.time() - 1200}),
        encoding="utf-8",
    )

    report = module._claimed_age_surface(claimed)

    assert report["count"] == 1
    assert report["over_900s"] == 1
    assert report["samples"][0]["sim"] == "sim_alpha.py"


def test_system_surface_audit_maintenance_queue_groups_actions() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_maintenance_queue_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    queue = module.maintenance_queue_surface(
        {
            "layers": {
                "owner_vault": 3,
                "probe_results": 4,
                "runner_logs": 1,
                "misplaced_probe_results": 2,
            },
            "cleanup_posture": {
                "owner_vault": "BLOCKED_REQUIRES_PREP",
                "probe_results": "KEEP_ACTIVE",
                "runner_logs": "KEEP_ACTIVE",
                "misplaced_probe_results": "REPAIR_TO_CANONICAL_ROOT",
            },
        },
        {
            "health": {"status": "draining"},
            "warnings": ["1 claim(s) over 300s"],
            "claimed_age": {"over_300s": 1},
            "blocked": {
                "active_count": 5,
                "reasons": {"gate_denied": 5},
                "unique_sims": 2,
                "duplicate_entries": 3,
                "samples": [{"sim": "sim_alpha.py", "reason": "gate_denied"}],
            },
        },
        {
            "system_v4/probes/a2_state/sim_results": {
                "fail_actions": {"rerun_candidate": 2, "missing_source_repair": 1},
                "fail_details": [
                    {"result": "a.json", "action": "rerun_candidate"},
                    {"result": "b.json", "action": "missing_source_repair"},
                ],
                "dirty_source_results": 1,
                "untracked_source_results": 0,
            }
        },
        {
            "count": 12,
            "result_states": {
                "pass": 7,
                "stale_source_newer": 2,
                "no_result": 2,
                "unknown": 1,
            },
            "stale_families": {"gtower": 2},
            "no_result_families": {"pure": 2},
            "unknown_families": {"fep": 1},
            "samples": {
                "stale_source_newer": ["sim_alpha.py"],
                "no_result": ["sim_beta.py"],
                "unknown": ["sim_gamma.py"],
            },
            "lint": {
                "counts": {"clean": 3, "violating_sims": 9, "C6_classical_has_load_bearing": 4},
                "samples": {"C6_classical_has_load_bearing": ["sim_alpha.py"]},
            },
            "tool_integration": {
                "missing_manifest_by_tool": {"scipy": 3},
                "missing_depth_by_tool": {"scipy": 4},
                "max_stack_sims": [{"sim": "sim_anchor.py", "load_bearing_tool_count": 5}],
                "greedy_declared_cover": {"target_tool_count": 6, "covered_tool_count": 5},
            },
        },
    )

    assert queue["git"]["blocked_entries"] == 3
    assert queue["git"]["repair_entries"] == 2
    assert queue["git"]["active_churn_entries"] == 5
    assert queue["runner"]["warnings"] == ["1 claim(s) over 300s"]
    assert queue["runner"]["blocked"]["duplicate_entries"] == 3
    assert queue["results"]["fail_actions"] == {"rerun_candidate": 2, "missing_source_repair": 1}
    assert queue["results"]["fail_action_samples"]["rerun_candidate"] == [{"result": "a.json", "action": "rerun_candidate"}]
    assert queue["classical"]["freshness_queue"] == {
        "count": 2,
        "families": {"gtower": 2},
        "samples": ["sim_alpha.py"],
    }
    assert queue["classical"]["no_result_queue"] == {
        "count": 2,
        "families": {"pure": 2},
        "samples": ["sim_beta.py"],
    }
    assert queue["classical"]["unknown_queue"] == {
        "count": 1,
        "families": {"fep": 1},
        "samples": ["sim_gamma.py"],
    }
    assert queue["classical"]["contract_queue"]["violating_sims"] == 9
    assert queue["classical"]["top_tool_manifest_gaps"] == {"scipy": 3}
    assert queue["classical"]["top_tool_depth_gaps"] == {"scipy": 4}


def test_sim_program_audit_skips_invalid_queue_candidates(tmp_path) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "sim_program_audit_invalid_queue_under_test",
            REPO_ROOT / "scripts" / "sim_program_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    queue_root = tmp_path / "queue"
    lane_b = queue_root / "lane_B"
    lane_b.mkdir(parents=True, exist_ok=True)
    (lane_b / "bad.json").write_text('{"plan_bucket":"exploratory"}\n', encoding="utf-8")
    (lane_b / "good.json").write_text(
        '{"sim_path":"system_v4/probes/sim_good_alpha.py","plan_bucket":"core_ladder","priority":"high"}\n',
        encoding="utf-8",
    )

    module.QUEUE = queue_root

    assert module.queue_invalid_entry_summary() == {"lane_A": 0, "lane_B": 1}
    assert module.next_queue_candidates("lane_B", limit=5) == [{
        "sim": "sim_good_alpha.py",
        "priority": "high",
        "plan_bucket": "core_ladder",
        "plan_stage": "early_core",
    }]


def test_queue_claim_prefers_high_priority_items(tmp_path) -> None:
    module = _load_module(
        "queue_claim_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    low = lane / "b.json"
    low.write_text(
        '{"sim_path":"sim_low.py","lane":"lane_B","priority":"low"}\n',
        encoding="utf-8",
    )
    high = lane / "a.json"
    high.write_text(
        '{"sim_path":"sim_high.py","lane":"lane_B","priority":"high"}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_high.py"


def test_queue_claim_inferrs_priority_for_legacy_items(tmp_path) -> None:
    module = _load_module(
        "queue_claim_legacy_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    exploratory = lane / "b.json"
    exploratory.write_text(
        '{"sim_path":"sim_leviathan_control_surface.py","lane":"lane_B"}\n',
        encoding="utf-8",
    )
    core = lane / "a.json"
    core.write_text(
        '{"sim_path":"sim_weyl_chirality_bipartite.py","lane":"lane_B"}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_weyl_chirality_bipartite.py"


def test_queue_claim_prefers_core_ladder_when_priority_ties(tmp_path) -> None:
    module = _load_module(
        "queue_claim_bucket_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    exploratory = lane / "a.json"
    exploratory.write_text(
        '{"sim_path":"sim_leviathan_control_surface.py","lane":"lane_B","priority":"normal","enqueued_at":1}\n',
        encoding="utf-8",
    )
    core = lane / "b.json"
    core.write_text(
        '{"sim_path":"sim_weyl_chirality_bipartite.py","lane":"lane_B","priority":"normal","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_weyl_chirality_bipartite.py"


def test_queue_claim_promotes_stale_priority_to_bucket_default(tmp_path) -> None:
    module = _load_module(
        "queue_claim_priority_upgrade_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    stale_core = lane / "a.json"
    stale_core.write_text(
        '{"sim_path":"sim_qit_szilard_record_translation_lane.py","lane":"lane_B","priority":"normal","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    exploratory = lane / "b.json"
    exploratory.write_text(
        '{"sim_path":"sim_leviathan_control_surface.py","lane":"lane_B","priority":"normal","plan_bucket":"exploratory","enqueued_at":0}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_qit_szilard_record_translation_lane.py"


def test_queue_claim_demotes_axis_stage_within_core_ladder(tmp_path) -> None:
    module = _load_module(
        "queue_claim_stage_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    axis = lane / "a.json"
    axis.write_text(
        '{"sim_path":"sim_axis0_kernel_phi0.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    early = lane / "b.json"
    early.write_text(
        '{"sim_path":"sim_z3_negative_quasiprob_exclusion.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_z3_negative_quasiprob_exclusion.py"


def test_queue_claim_demotes_late_info_stage_within_core_ladder(tmp_path) -> None:
    module = _load_module(
        "queue_claim_late_info_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    late_info = lane / "a.json"
    late_info.write_text(
        '{"sim_path":"sim_qit_carnot_finite_time_companion.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    early = lane / "b.json"
    early.write_text(
        '{"sim_path":"sim_z3_negative_quasiprob_exclusion.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_z3_negative_quasiprob_exclusion.py"


def test_queue_claim_classifies_coherent_info_as_late_info(tmp_path) -> None:
    module = _load_module(
        "queue_claim_coherent_info_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    late_info = lane / "a.json"
    late_info.write_text(
        '{"sim_path":"sim_lego_coherent_info_advanced.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    early = lane / "b.json"
    early.write_text(
        '{"sim_path":"sim_z3_negative_quasiprob_exclusion.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_z3_negative_quasiprob_exclusion.py"


def test_queue_claim_classifies_entanglement_as_late_info(tmp_path) -> None:
    module = _load_module(
        "queue_claim_entanglement_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    late_info = lane / "a.json"
    late_info.write_text(
        '{"sim_path":"sim_lego_entanglement_distillation.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    early = lane / "b.json"
    early.write_text(
        '{"sim_path":"sim_geom_cp1_u1_projective.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_geom_cp1_u1_projective.py"


def test_autonomous_reseed_loop_uses_deterministic_stage_aware_enqueue() -> None:
    text = (REPO_ROOT / "scripts" / "autonomous_reseed_loop.sh").read_text(encoding="utf-8")
    assert "plan_stage_for_sim()" in text
    assert "hashlib.sha1" in text
    assert '"plan_stage": stage' in text
    assert "secrets.token_hex" not in text


def test_queue_claim_prefers_older_items_when_rank_ties(tmp_path) -> None:
    module = _load_module(
        "queue_claim_fifo_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    newer = lane / "a.json"
    newer.write_text(
        '{"sim_path":"sim_probe_object.py","lane":"lane_B","priority":"normal","enqueued_at":20}\n',
        encoding="utf-8",
    )
    older = lane / "z.json"
    older.write_text(
        '{"sim_path":"sim_characteristic_representation.py","lane":"lane_B","priority":"normal","enqueued_at":10}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_characteristic_representation.py"


def test_controller_plane_snapshot_dry_mode_prints_snapshot(
    tmp_path, monkeypatch, capsys
) -> None:
    adaptive = _load_module(
        "adaptive_controller_for_plane_script",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    sys.modules["adaptive_controller"] = adaptive
    try:
        module = _load_module(
            "controller_plane_snapshot_under_test",
            REPO_ROOT / "scripts" / "controller_plane_snapshot.py",
        )
    finally:
        sys.modules.pop("adaptive_controller", None)

    monkeypatch.setattr(adaptive, "triage_cycle", lambda dry=True: {
        "ts": "2026-04-15T03:00:00Z",
        "failing": [],
        "schema_debt": [],
        "never_run": [],
        "stale": [],
        "passing": ["sim_ok"],
        "released_claims": 0,
    })
    monkeypatch.setattr(adaptive, "build_integration_summary", lambda state: {
        "canonical_passing": 1,
        "total_passing": 1,
        "rosetta_candidate_clusters": 0,
    })
    monkeypatch.setattr(adaptive, "build_plane_snapshot", lambda state, integration: {
        "ts": state["ts"],
        "control_plane": {"queue": {"lane_A": 0, "lane_B": 0, "claimed": 0, "blocked": 0, "done": 0}},
        "state_plane": {"triage": {"passing": 1}},
    })
    monkeypatch.setattr(sys, "argv", ["controller_plane_snapshot.py", "--dry"])

    rc = module.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert '"control_plane"' in out


def test_axis0_xi_law_fingerprint_matches_across_strict_pre_entropy_and_entropy() -> None:
    module = _load_module(
        "axis0_xi_law_fingerprint_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_xi_law_fingerprint.py",
    )
    law_summary = {
        "law_name": "Xi_hist signed law",
        "owner_read": "late-anchor equivalence plus 8_15 prefix anchor, global 8_23-over-0_3 IC dominance, and front-half signed-cut asymmetry",
        "late_anchor_equivalence": {
            "placement_8_23_equals_16_31": True,
            "placement_8_23_equals_prefix_8_15_on_mi": True,
            "placement_8_23_equals_prefix_8_15_on_ic": True,
            "placement_8_23_equals_prefix_8_15_on_signed_cut": True,
        },
        "anchor_and_width_profile": {
            "best_prefix_drop_by_ic_is_8_15": True,
            "best_early_width_by_ic_is_0_7_majority": True,
            "late_anchor_beats_0_3_globally_on_ic": True,
            "front_half_signed_cut_preference_all_seats": True,
            "clifford_mi_0_7_vs_0_15_is_tied": True,
        },
        "counts": {
            "total_rows": 6,
            "off_clifford_rows": 4,
            "clifford_rows": 2,
            "placement_8_23_beats_0_3_on_ic_count": 6,
            "placement_8_23_beats_0_3_on_ic_off_clifford_count": 4,
            "short_width_0_3_beats_8_23_on_ic_clifford_count": 0,
            "best_early_width_by_ic_counts": {"0_3": 1, "0_7": 5, "0_11": 0, "0_15": 0},
            "best_prefix_drop_by_ic_counts": {"0_15": 0, "1_15": 0, "2_15": 0, "4_15": 0, "8_15": 6},
        },
    }
    strict_payload = {"verdict": {"xi_hist_signed_law_summary": law_summary}}
    pre_entropy_payload = {
        "gates": [
            {
                "name": "P14_xi_hist_signed_law_is_explicit_in_strict_bakeoff",
                "detail": law_summary,
            }
        ]
    }
    entropy_payload = {
        "gates": [
            {
                "name": "E12_xi_hist_law_summary_binds_pre_entropy_to_readout",
                "detail": {"p14_detail": law_summary},
            }
        ]
    }

    strict_fp = module.strict_law_fingerprint(strict_payload)
    pre_fp = module.pre_entropy_law_fingerprint(pre_entropy_payload)
    entropy_fp = module.entropy_law_fingerprint(entropy_payload)

    assert strict_fp == pre_fp == entropy_fp


def test_axis0_xi_law_fingerprint_carrier_alignment_uses_global_0_7_8_23_8_15() -> None:
    module = _load_module(
        "axis0_xi_law_fingerprint_carrier_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_xi_law_fingerprint.py",
    )
    strict_law = {
        "law_name": "Xi_hist signed law",
        "owner_read": "late-anchor equivalence plus 8_15 prefix anchor, global 8_23-over-0_3 IC dominance, and front-half signed-cut asymmetry",
        "late_anchor_equivalence": {
            "placement_8_23_equals_16_31": True,
            "placement_8_23_equals_prefix_8_15_on_mi": True,
            "placement_8_23_equals_prefix_8_15_on_ic": True,
            "placement_8_23_equals_prefix_8_15_on_signed_cut": True,
        },
        "anchor_and_width_profile": {
            "best_prefix_drop_by_ic_is_8_15": True,
            "best_early_width_by_ic_is_0_7_majority": True,
            "late_anchor_beats_0_3_globally_on_ic": True,
            "front_half_signed_cut_preference_all_seats": True,
            "clifford_mi_0_7_vs_0_15_is_tied": True,
        },
        "counts": {
            "total_rows": 6,
            "off_clifford_rows": 4,
            "clifford_rows": 2,
            "placement_8_23_beats_0_3_on_ic_count": 6,
            "placement_8_23_beats_0_3_on_ic_off_clifford_count": 4,
            "short_width_0_3_beats_8_23_on_ic_clifford_count": 0,
            "best_early_width_by_ic_counts": {"0_3": 1, "0_7": 5, "0_11": 0, "0_15": 0},
            "best_prefix_drop_by_ic_counts": {"0_15": 0, "1_15": 0, "2_15": 0, "4_15": 0, "8_15": 6},
        },
    }
    carrier_payload = {
        "gates": [
            {
                "name": "C5_strict_bakeoff_confirms_structured_history_without_shell_shortcut",
                "detail": {
                    "history_nontrivial_while_shell_flat": True,
                    "point_ref_minus_shell_base_std": 0.2,
                    "best_window_by_mi_counts": {"0_3": 0, "0_7": 6, "0_11": 0, "0_15": 0},
                    "best_placement_by_mi_counts": {"0_15": 0, "8_23": 6, "16_31": 0},
                    "best_prefix_drop_by_mi_counts": {"0_15": 0, "1_15": 0, "2_15": 0, "4_15": 0, "8_15": 6},
                    "early_window_beats_shifted_count": 0,
                },
            }
        ]
    }

    law_fp = module.strict_law_fingerprint({"verdict": {"xi_hist_signed_law_summary": strict_law}})
    carrier_fp = module.carrier_law_fingerprint(carrier_payload)

    assert module.carrier_matches_law(carrier_fp, law_fp) is True
    carrier_fp["best_prefix_drop_by_mi_counts"]["8_15"] = 5
    assert module.carrier_matches_law(carrier_fp, law_fp) is False


def test_fe_indexed_xi_hist_owner_alignment_stays_subordinate_to_strict_law() -> None:
    module = _load_module(
        "axis0_fe_indexed_xi_hist_under_test",
        REPO_ROOT / "system_v4" / "probes" / "sim_axis0_fe_indexed_xi_hist.py",
    )
    strict_law = {
        "owner_read": "late-anchor equivalence plus 8_15 prefix anchor, global 8_23-over-0_3 IC dominance, and front-half signed-cut asymmetry",
        "placement_label": "8_23",
        "canonical_prefix_drop": "8_15",
        "canonical_early_width": "0_7",
    }
    summary = {
        "winner_counts": {
            "A_phase4_winner": 6,
            "B_fe_indexed": 0,
            "C_fe_pairs_only": 0,
            "D_lag7_pairs": 0,
        },
        "best_new_bridge": "C_fe_pairs_only",
        "best_gain": -0.061,
    }
    deep_contract = {"winner": "A_phase4_winner"}
    results = [
        {
            "bridges": {
                "A_phase4_winner": {"ic": 0.5},
                "C_fe_pairs_only": {"ic": 0.4},
            }
        }
        for _ in range(6)
    ]

    alignment = module._xi_hist_owner_alignment_surface(
        results,
        summary,
        deep_contract,
        strict_law,
    )

    assert alignment["pass"] is True
    assert alignment["status"] == "subordinate_refinement_only"
    assert alignment["owner_dependency"] == "must_bind_under_xi_hist_signed_law"

    results[0]["bridges"]["C_fe_pairs_only"]["ic"] = 0.6
    broken = module._xi_hist_owner_alignment_surface(
        results,
        summary,
        deep_contract,
        strict_law,
    )
    assert broken["pass"] is False


def test_bridge_search_owner_alignment_stays_downstream_of_xi_hist_signed_law() -> None:
    module = _load_module(
        "axis0_bridge_search_under_test",
        REPO_ROOT / "system_v4" / "probes" / "sim_axis0_bridge_search.py",
    )
    strict_law = {
        "owner_read": "late-anchor equivalence plus 8_15 prefix anchor, global 8_23-over-0_3 IC dominance, and front-half signed-cut asymmetry",
        "placement_label": "8_23",
        "canonical_prefix_drop": "8_15",
        "canonical_early_width": "0_7",
    }
    ranking = ["Xi_chiral_entangle", "Xi_chiral_hist_entangle"]
    candidate_mis = {
        "Xi_chiral_entangle": [0.82, 0.81],
        "Xi_chiral_hist_entangle": [0.51, 0.50],
    }
    candidate_ics = {
        "Xi_chiral_entangle": [0.03, 0.028],
        "Xi_chiral_hist_entangle": [-0.07, -0.08],
    }
    deep_contract = {"winner": "Xi_chiral_entangle"}

    alignment = module._xi_hist_owner_alignment_surface(
        ranking,
        candidate_mis,
        candidate_ics,
        deep_contract,
        strict_law,
    )

    assert alignment["pass"] is True
    assert alignment["status"] == "axis_internal_candidate_not_final_owner_law"
    assert alignment["owner_dependency"] == "must_bind_under_xi_hist_signed_law"

    candidate_ics["Xi_chiral_hist_entangle"] = [0.01, 0.02]
    broken = module._xi_hist_owner_alignment_surface(
        ranking,
        candidate_mis,
        candidate_ics,
        deep_contract,
        strict_law,
    )
    assert broken["pass"] is False


def test_entropy_readout_bridge_owner_alignment_contract_is_fail_closed() -> None:
    module = _load_module(
        "axis0_entropy_readout_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_entropy_readout_packet.py",
    )
    alignment = {
        "pass": True,
        "status": "axis_internal_candidate_not_final_owner_law",
        "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
        "owner_dependency": "must_bind_under_xi_hist_signed_law",
        "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
        "winner": "Xi_chiral_entangle",
        "runner_up": "Xi_chiral_hist_entangle",
    }

    assert module.bridge_owner_alignment_ok(alignment) is True

    broken = dict(alignment)
    broken["owner_dependency"] = "free_owner_promotion"
    assert module.bridge_owner_alignment_ok(broken) is False


def test_c1_bridge_owner_alignment_contract_is_fail_closed() -> None:
    signed_module = _load_module(
        "axis0_c1_signed_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_c1_signed_bridge_candidate_search.py",
    )
    bridge_module = _load_module(
        "axis0_c1_bridge_object_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_c1_bridge_object_packet.py",
    )
    alignment = {
        "pass": True,
        "status": "axis_internal_candidate_not_final_owner_law",
        "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
        "owner_dependency": "must_bind_under_xi_hist_signed_law",
        "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
        "winner": "Xi_chiral_entangle",
        "runner_up": "Xi_chiral_hist_entangle",
    }

    assert signed_module.bridge_owner_alignment_ok(alignment) is True
    assert bridge_module.bridge_owner_alignment_ok(alignment) is True

    broken = dict(alignment)
    broken["runner_up"] = "Xi_loop_phase"
    assert signed_module.bridge_owner_alignment_ok(broken) is False
    assert bridge_module.bridge_owner_alignment_ok(broken) is False


def test_axis0_signed_bridge_handoff_contract_is_fail_closed() -> None:
    module = _load_module(
        "axis0_bridge_contract_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_bridge_owner_alignment_contract.py",
    )
    handoff = {
        "candidate": "Xi_chiral_entangle",
        "status": "provisional_handoff_ready",
        "placement_contract": "downstream_axis_internal_bridge_candidate_only",
        "owner_dependency": "must_bind_under_xi_hist_signed_law",
        "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
        "consumer_status": "allowed_for_entropy_readout_not_final_owner_xi",
    }

    assert module.signed_bridge_handoff_ok(handoff) is True

    broken = dict(handoff)
    broken["consumer_status"] = "final_owner_law"
    assert module.signed_bridge_handoff_ok(broken) is False

    built = module.build_signed_bridge_handoff(
        bridge_owner_alignment={
            "pass": True,
            "status": "axis_internal_candidate_not_final_owner_law",
            "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
            "owner_dependency": "must_bind_under_xi_hist_signed_law",
            "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
            "winner": "Xi_chiral_entangle",
            "runner_up": "Xi_chiral_hist_entangle",
        },
        extra_fields={"object": "c1_signed_bridge_candidate_handoff"},
    )
    assert built["consumer_status"] == "allowed_for_entropy_readout_not_final_owner_xi"
    assert built["bridge_owner_alignment"]["winner"] == "Xi_chiral_entangle"
    assert module.axis_internal_candidate_status() == "axis_internal_candidate_not_final_owner_law"
    assert (
        module.axis_internal_candidate_relation()
        == "downstream_of_xi_hist_signed_law_not_alternate_owner_law"
    )
    assert (
        module.axis_internal_candidate_placement()
        == "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law"
    )
    assert module.current_bridge_gate_name() == "E10_current_bridge_candidate_is_explicit_and_provisional"
    assert module.current_bridge_object_status() == "admitted_bridge_object_for_downstream_readout_not_final_owner_law"
    assert module.axis_internal_mapping_ok({"Xi_chiral_entangle": module.axis_internal_candidate_status()}) is True
    assert (
        module.axis_internal_placement_ok(
            {"Xi_chiral_entangle": module.axis_internal_candidate_placement()}
        )
        is True
    )

    with pytest.raises(ValueError):
        module.build_signed_bridge_handoff(
            extra_fields={"consumer_status": "final_owner_law"},
        )

    reservation = module.build_non_owner_reservation()
    assert module.non_owner_reservation_ok(reservation) is True

    broken_reservation = dict(reservation)
    broken_reservation["consumer_scope"] = "final_owner_law"
    assert module.non_owner_reservation_ok(broken_reservation) is False

    with pytest.raises(ValueError):
        module.build_non_owner_reservation(
            extra_fields={"consumer_scope": "final_owner_law"},
        )

    owner_read = module.build_owner_read(note=module.c1_signed_candidate_owner_note())
    assert module.owner_read_ok(owner_read) is True
    assert "without replacing xi_hist signed law" in owner_read["note"]

    broken_owner_read = dict(owner_read)
    broken_owner_read["status"] = "final_owner_law"
    assert module.owner_read_ok(broken_owner_read) is False


def test_axis0_bridge_owner_packet_surface_is_fail_closed(tmp_path) -> None:
    module = _load_module(
        "axis0_bridge_owner_packet_surface_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_bridge_owner_packet_surface.py",
    )
    results = tmp_path / "sim_results"
    results.mkdir()

    c1_signed_result = {
        "support_chain": {
            "pre_entropy_mapping": "axis_internal_candidate_not_final_owner_law",
            "pre_entropy_relation": "downstream_of_xi_hist_signed_law_not_alternate_owner_law",
            "pre_entropy_placement": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
            "entropy_readout_current_bridge_gate": "E10_current_bridge_candidate_is_explicit_and_provisional",
        },
        "downstream_handoff": {
            "candidate": "Xi_chiral_entangle",
            "status": "provisional_handoff_ready",
            "placement_contract": "downstream_axis_internal_bridge_candidate_only",
            "owner_dependency": "must_bind_under_xi_hist_signed_law",
            "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
            "consumer_status": "allowed_for_entropy_readout_not_final_owner_xi",
        },
        "unresolved": {
            "status": "explicit_non_owner_reservation",
            "final_xi_owner_law": "reserved_for_future_owner_doctrine_not_claimed_by_c1",
            "shell_doctrine": "reserved_for_future_shell_doctrine_not_claimed_by_c1",
            "history_law_replacement": "reserved_for_future_history_law_replacement_not_claimed_by_c1",
            "entropy_family_owner_doctrine": "reserved_for_future_entropy_owner_doctrine_not_claimed_by_c1",
            "owner_dependency": "must_bind_under_xi_hist_signed_law",
            "consumer_scope": "downstream_readout_only",
        },
        "owner_read": {
            "status": "admitted_executable_candidate_not_final_owner_law",
            "note": "bounded",
        },
    }
    c1_bridge_result = {
        "bridge_object": {
            "status": "admitted_bridge_object_for_downstream_readout_not_final_owner_law",
        },
        "support_contract": {
            "bridge_owner_alignment": {
                "pass": True,
                "status": "axis_internal_candidate_not_final_owner_law",
                "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
                "owner_dependency": "must_bind_under_xi_hist_signed_law",
                "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
                "winner": "Xi_chiral_entangle",
                "runner_up": "Xi_chiral_hist_entangle",
            },
            "carrier_handoff": {
                "candidate": "Xi_chiral_entangle",
                "status": "provisional_handoff_ready",
                "placement_contract": "downstream_axis_internal_bridge_candidate_only",
                "owner_dependency": "must_bind_under_xi_hist_signed_law",
                "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
                "consumer_status": "allowed_for_entropy_readout_not_final_owner_xi",
            },
            "carrier_selection_handoff_matches_search": True,
            "pre_entropy_mapping": "axis_internal_candidate_not_final_owner_law",
            "pre_entropy_relation": "downstream_of_xi_hist_signed_law_not_alternate_owner_law",
            "pre_entropy_placement": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
            "entropy_gate_name": "E10_current_bridge_candidate_is_explicit_and_provisional",
            "entropy_gate_status": "admitted_executable_candidate_not_final_owner_law",
        },
        "non_claims": {
            "status": "explicit_non_owner_reservation",
            "final_xi_owner_law": "reserved_for_future_owner_doctrine_not_claimed_by_c1",
            "shell_doctrine": "reserved_for_future_shell_doctrine_not_claimed_by_c1",
            "history_law_replacement": "reserved_for_future_history_law_replacement_not_claimed_by_c1",
            "entropy_family_owner_doctrine": "reserved_for_future_entropy_owner_doctrine_not_claimed_by_c1",
            "owner_dependency": "must_bind_under_xi_hist_signed_law",
            "consumer_scope": "downstream_readout_only",
        },
    }
    validation_payload = lambda name: {"gates": [{"name": name, "pass": True}]}
    stack_validation = {
        "gates": [
            {"name": "S5_axis0_ladder_is_mechanically_traversable", "pass": True},
            {"name": "S6_xi_chiral_entangle_remains_axis_internal_and_not_owner_law", "pass": True},
            {"name": "S7_axis0_stack_explicitly_consumes_named_contract_gates", "pass": True},
            {"name": "S9_axis0_stack_consumes_standalone_c1_bridge_object_contract", "pass": True},
        ]
    }

    (results / "c1_signed_bridge_candidate_search_results.json").write_text(
        json.dumps(c1_signed_result),
        encoding="utf-8",
    )
    (results / "c1_signed_bridge_candidate_search_validation.json").write_text(
        json.dumps(
            {
                "gates": [
                    {"name": "C1S3_support_chain_is_closed_before_candidate_packaging", "pass": True},
                    {"name": "C1S4_candidate_stays_provisional_and_does_not_overpromote", "pass": True},
                ]
            }
        ),
        encoding="utf-8",
    )
    (results / "c1_bridge_object_packet_results.json").write_text(
        json.dumps(c1_bridge_result),
        encoding="utf-8",
    )
    (results / "c1_bridge_object_packet_validation.json").write_text(
        json.dumps(
            {
                "gates": [
                    {"name": "C1B1_bridge_object_is_explicit_and_downstream_only", "pass": True},
                    {"name": "C1B3_bridge_object_is_bound_to_the_existing_support_contract", "pass": True},
                    {"name": "C1B4_bridge_object_keeps_owner_doctrine_questions_open", "pass": True},
                ]
            }
        ),
        encoding="utf-8",
    )
    (results / "pre_entropy_packet_validation.json").write_text(
        json.dumps(
            {
                "gates": [
                    {"name": "P22_c1_signed_bridge_candidate_is_explicit_and_provisional", "pass": True},
                    {"name": "P23_xi_chiral_entangle_remains_downstream_of_xi_hist_signed_law", "pass": True},
                    {"name": "P24_carrier_handoff_matches_pre_entropy_downstream_mapping", "pass": True},
                    {"name": "P25_standalone_c1_bridge_object_matches_pre_entropy_contract", "pass": True},
                ]
            }
        ),
        encoding="utf-8",
    )
    (results / "entropy_readout_packet_validation.json").write_text(
        json.dumps(validation_payload("E10_current_bridge_candidate_is_explicit_and_provisional")),
        encoding="utf-8",
    )
    (results / "axis0_stack_packet_validation.json").write_text(
        json.dumps(stack_validation),
        encoding="utf-8",
    )

    surface = module.load_bridge_owner_packet_surface(results)
    assert surface["pass"] is True
    assert surface["gate_passes"]["S6_xi_chiral_entangle_remains_axis_internal_and_not_owner_law"] is True

    broken = dict(c1_bridge_result)
    broken["support_contract"] = dict(c1_bridge_result["support_contract"])
    broken["support_contract"]["entropy_gate_status"] = "final_owner_law"
    (results / "c1_bridge_object_packet_results.json").write_text(
        json.dumps(broken),
        encoding="utf-8",
    )

    broken_surface = module.load_bridge_owner_packet_surface(results)
    assert broken_surface["pass"] is False


def test_axis0_distinguishability_constraint_is_fail_closed() -> None:
    module = _load_module(
        "axis0_constraint_types_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_constraint_types.py",
    )

    surface = module.build_distinguishability_constraint(
        observational=True,
        admissible=True,
        stable=True,
        entropy_conditioned=True,
        topology_conditioned=True,
        note="ok",
    )
    assert surface["type"] == "distinguishability_constraint"
    assert surface["pass"] is True
    assert surface["gate_fraction"] == 1.0
    assert surface["signals"] == {}
    assert surface["constraint_profile"]["entropy_conditioned"] == 0.0

    broken = module.build_distinguishability_constraint(
        observational=True,
        admissible=False,
        stable=True,
        entropy_conditioned=True,
        topology_conditioned=True,
        note="broken",
    )
    assert broken["pass"] is False
    assert broken["gate_fraction"] < 1.0

    thresholded = module.build_distinguishability_constraint(
        observational=True,
        admissible=False,
        stable=True,
        entropy_conditioned=True,
        topology_conditioned=True,
        note="thresholded",
        pass_threshold=0.8,
        signals={"entropy_signal": 1.25},
    )
    assert thresholded["pass"] is True
    assert thresholded["gate_fraction"] == 0.8
    assert thresholded["pass_threshold"] == 0.8
    assert thresholded["signals"]["entropy_signal"] == 1.25
    assert thresholded["constraint_profile"]["entropy_conditioned"] == 1.25


def test_axis0_pyg_distinguishability_uses_lane_native_graph_operator_separation() -> None:
    module = _load_module(
        "axis0_pyg_proxy_under_test",
        REPO_ROOT / "system_v4" / "probes" / "sim_axis0_pyg_proxy.py",
    )

    strong = module._pyg_distinguishability_surface(
        {
            "P2_gradient_varies_with_theta": {"grad_std": 0.01},
            "P4_theta_star_exists": {
                "in_admissible_range": True,
                "grad_at_theta_star": 0.02,
                "grad_threshold_used": 0.01,
            },
        },
        {
            "B1_theta_near_zero_pole_behavior": {"is_finite": True},
            "B2_theta_near_halfpi_equator_behavior": {"is_finite": True},
        },
        {"A0_gradient_profile_matches_expected": {"is_nonmonotone": True}},
        {"edge_count": 9, "longest_path_length": 5},
        {"sat": True},
        {"symbolic_hubble_mid": 1.1},
        {"mean_geodesic_distance": 0.4},
        {"dynamic_vs_frozen_gap": 0.03},
        [
            {"option": "pyg_topology_surface", "composite_score": 1.3},
            {"option": "solver_formula_surface", "composite_score": 1.2},
            {"option": "chain_direction_surface", "composite_score": 0.6},
            {"option": "proxy_nonnegative_surface", "composite_score": 0.4},
        ],
    )
    assert strong["gates"]["entropy_conditioned"] is True

    weak = module._pyg_distinguishability_surface(
        {
            "P2_gradient_varies_with_theta": {"grad_std": 0.01},
            "P4_theta_star_exists": {
                "in_admissible_range": True,
                "grad_at_theta_star": 0.02,
                "grad_threshold_used": 0.01,
            },
        },
        {
            "B1_theta_near_zero_pole_behavior": {"is_finite": True},
            "B2_theta_near_halfpi_equator_behavior": {"is_finite": True},
        },
        {"A0_gradient_profile_matches_expected": {"is_nonmonotone": True}},
        {"edge_count": 9, "longest_path_length": 5},
        {"sat": True},
        {"symbolic_hubble_mid": 1.1},
        {"mean_geodesic_distance": 0.4},
        {"dynamic_vs_frozen_gap": 0.01},
        [
            {"option": "pyg_topology_surface", "composite_score": 0.8},
            {"option": "solver_formula_surface", "composite_score": 0.9},
            {"option": "chain_direction_surface", "composite_score": 0.7},
            {"option": "proxy_nonnegative_surface", "composite_score": 0.6},
        ],
    )
    assert weak["gates"]["entropy_conditioned"] is False


def test_axis0_crosslane_distinguishability_alignment_compares_gate_patterns() -> None:
    module = _load_module(
        "axis0_crosslane_core_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_lambda_crosslane_semantic_core.py",
    )

    aligned = module._pairwise_distinguishability_alignment_surface(
        [
            {
                "lane": "lhs",
                "distinguishability_gate_fraction": 1.0,
                "distinguishability_surface": {
                    "gates": {
                        "observational": True,
                        "admissible": True,
                        "stable": True,
                        "entropy_conditioned": True,
                        "topology_conditioned": True,
                    },
                    "signals": {
                        "observational_signal": 1.0,
                        "entropy_signal": 1.2,
                    },
                },
            },
            {
                "lane": "rhs",
                "distinguishability_gate_fraction": 1.0,
                "distinguishability_surface": {
                    "gates": {
                        "observational": True,
                        "admissible": True,
                        "stable": True,
                        "entropy_conditioned": True,
                        "topology_conditioned": True,
                    },
                    "signals": {
                        "observational_signal": 1.0,
                        "entropy_signal": 1.2,
                    },
                },
            },
        ]
    )
    assert aligned["min_gate_agreement"] == 1.0
    assert aligned["max_gate_disagreement"] == 0.0
    assert aligned["min_surface_cosine_similarity"] == 1.0
    assert aligned["min_constraint_profile_cosine_similarity"] == pytest.approx(1.0)
    assert aligned["min_signal_cosine_similarity"] == pytest.approx(1.0)

    drifted = module._pairwise_distinguishability_alignment_surface(
        [
            {
                "lane": "lhs",
                "distinguishability_gate_fraction": 1.0,
                "distinguishability_surface": {
                    "gates": {
                        "observational": True,
                        "admissible": True,
                        "stable": True,
                        "entropy_conditioned": True,
                        "topology_conditioned": True,
                    },
                    "signals": {
                        "observational_signal": 1.0,
                        "entropy_signal": 1.2,
                    },
                },
            },
            {
                "lane": "rhs",
                "distinguishability_gate_fraction": 0.6,
                "distinguishability_surface": {
                    "gates": {
                        "observational": True,
                        "admissible": True,
                        "stable": True,
                        "entropy_conditioned": False,
                        "topology_conditioned": False,
                    },
                    "signals": {
                        "observational_signal": 0.2,
                        "entropy_signal": 0.1,
                    },
                },
            },
        ]
    )
    assert drifted["min_gate_agreement"] < 1.0
    assert drifted["max_gate_disagreement"] == 1.0
    assert drifted["min_surface_cosine_similarity"] < 1.0
    assert drifted["min_constraint_profile_cosine_similarity"] < 1.0
    assert drifted["min_signal_cosine_similarity"] < 1.0


def test_axis0_semantic_row_exposes_constraint_family_profile() -> None:
    module = _load_module(
        "axis0_crosslane_core_rows_under_test",
        REPO_ROOT / "system_v4" / "probes" / "axis0_lambda_crosslane_semantic_core.py",
    )

    row = module.semantic_row(
        lane="test_lane",
        symbolic_hubble_mid=1.0,
        constraint_pass=True,
        cvc5_pass=True,
        graph_longest_path_length=5,
        manifold_distance=0.4,
        pyg_mean_aggregate_norm=1.2,
        distinguishability_pass=True,
        distinguishability_gate_fraction=1.0,
        distinguishability_surface={
            "constraint_profile": {
                "observational": 1.1,
                "admissible": 1.0,
                "stable": 0.9,
                "entropy_conditioned": 1.3,
                "topology_conditioned": 0.8,
            }
        },
        constraint_family_profile={
            "observational": 1.1,
            "admissible": 1.0,
            "stable": 0.9,
            "entropy_conditioned": 1.3,
            "topology_conditioned": 0.8,
        },
    )
    assert row["constraint_family_profile"]["entropy_conditioned"] == 1.3


def test_axis0_entropy_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_entropy_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_entropy_readout_packet.py",
    )

    gate_map = {
        "E1_qubit_spectral_family_is_order_equivalent": {"pass": True},
        "E2_shannon_diagonal_is_not_geometry_safe": {"pass": True},
        "E3_product_proxy_and_pure_fi_negatives_hold": {"pass": True},
        module.current_bridge_gate_name(): {"pass": True},
        "E11_xi_chiral_entangle_signed_honesty_beats_mispair_counterfeit": {"pass": False},
        "E4_bridge_family_ranking_is_separated": {"pass": True},
        "E5_raw_and_lr_controls_stay_entropy_trivial": {"pass": True},
        "E8_history_family_handoff_supports_signed_readout_on_same_objects": {"pass": False},
        "E6_shell_bridge_supports_signed_entropy_readout": {"pass": True},
        "E7_history_bridges_are_nontrivial_and_torus_sensitive": {"pass": True},
        "E9_fep_framing_shows_nonclassical_directionality": {"pass": False},
        "E12_xi_hist_law_summary_binds_pre_entropy_to_readout": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 1.0
    assert profile["admissible"] == 0.5
    assert profile["stable"] == 2.0 / 3.0
    assert profile["entropy_conditioned"] == 0.75
    assert profile["topology_conditioned"] == 1.0


def test_axis0_carrier_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_carrier_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_carrier_selection_packet.py",
    )

    gate_map = {
        "C1_search_and_bridge_surfaces_execute_cleanly": {"pass": True},
        "C2_missing_axis_search_finds_uncaptured_candidate": {"pass": False},
        "C3_live_carrier_wins_and_honesty_signal_stays_unique": {"pass": True},
        "C4_bridge_search_separates_winning_bridges_from_controls": {"pass": True},
        "C5_strict_bakeoff_confirms_structured_history_without_shell_shortcut": {"pass": False},
        "C6_direct_lr_stays_ranked_as_control_not_winner": {"pass": True},
        "C7_counterfeit_history_games_mi_but_not_coherent_info": {"pass": True},
        "C8_provisional_signed_bridge_candidate_handoff_is_explicit": {"pass": True},
        "C9_handoff_contract_freezes_downstream_only_placement": {"pass": False},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 0.5
    assert profile["admissible"] == 0.5
    assert profile["stable"] == 1.0
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 0.5


def test_axis0_pre_entropy_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_pre_entropy_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_pre_entropy_packet.py",
    )

    gate_map = {
        "P1_bridge_admission_is_fail_closed": {"pass": True},
        "P3_history_windows_currently_degenerate": {"pass": False},
        "P4_shell_flat_pointref_varies": {"pass": True},
        "P10_xi_hist_signed_handoff_uses_8_23_anchor_8_15_prefix_and_front_half_signed_cut": {"pass": True},
        "P11_xi_hist_signed_late_anchor_is_equivalent_not_free_placement": {"pass": True},
        "P22_c1_signed_bridge_candidate_is_explicit_and_provisional": {"pass": True},
        "P24_carrier_handoff_matches_pre_entropy_downstream_mapping": {"pass": False},
        "P25_standalone_c1_bridge_object_matches_pre_entropy_contract": {"pass": True},
        "P5_bridge_is_multicycle_stable_off_clifford": {"pass": True},
        "P6_clifford_is_the_edge_case_not_the_norm": {"pass": True},
        "P8_dynamic_shell_is_explicitly_unresolved": {"pass": False},
        "P2_strict_bakeoff_keeps_history_structured_without_shell_shortcut": {"pass": True},
        "P7_fe_pairs_only_is_strongest_new_candidate_but_phase4_still_wins": {"pass": True},
        "P9_xi_hist_handoff_prefers_shifted_anchor_and_8_15_prefix": {"pass": True},
        "P12_xi_hist_late_anchor_beats_0_3_globally_on_ic": {"pass": True},
        "P13_xi_hist_typing_law_8_15_vs_2_15_vs_0_7": {"pass": True},
        "P14_xi_hist_signed_law_is_explicit_in_strict_bakeoff": {"pass": True},
        "P23_xi_chiral_entangle_remains_downstream_of_xi_hist_signed_law": {"pass": True},
        "P15_owner_worthiness_map_demotes_raw_deltas_and_open_flux_labels": {"pass": True},
        "P16_transport_delta_branch_survives_but_is_not_owner_law_yet": {"pass": False},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 2.0 / 3.0
    assert profile["admissible"] == 0.8
    assert profile["stable"] == 2.0 / 3.0
    assert profile["entropy_conditioned"] == 1.0
    assert profile["topology_conditioned"] == 0.75


def test_axis0_root_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_root_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_root_emergence_packet.py",
    )

    gate_map = {
        "R1_formal_geometry_prerequisite_is_closed": {"pass": True},
        "R2_root_guards_and_ec3_execute_cleanly": {"pass": True},
        "R3_missing_axis_search_finds_uncaptured_structure": {"pass": False},
        "R4_bridge_search_rejects_direct_cartesian_carrier": {"pass": True},
        "R10_root_emergence_bridge_winner_respects_xi_handoff_contract": {"pass": False},
        "R5_small_carrier_family_selects_live_hopf_weyl": {"pass": True},
        "R6_live_carrier_keeps_unique_positive_honesty_signal": {"pass": True},
        "R7_mispair_counterfeit_games_mi_but_not_coherent_info": {"pass": False},
        "R8_coarising_is_attractor_specific_not_universal_algebra": {"pass": True},
        "R9_root_emergence_remains_open_without_smuggling": {"pass": True},
        "R10A_attractor_basin_keeps_trajectory_far_from_ti_failure_boundary": {"pass": True},
        "R10B_te_steps_stay_on_antiparallel_yz_band_on_attractor": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 2.0 / 3.0
    assert profile["admissible"] == 0.5
    assert profile["stable"] == 2.0 / 3.0
    assert profile["entropy_conditioned"] == 1.0
    assert profile["topology_conditioned"] == 1.0


def test_axis0_root_packet_requires_upstream_constraint_profiles() -> None:
    formal_profile = {
        "observational": 1.0,
        "admissible": 1.0,
        "stable": 1.0,
    }
    attractor_profile = {
        "admissible": 1.0,
        "entropy_conditioned": 1.0,
        "topology_conditioned": 1.0,
        "stable": 1.0,
    }
    c1_profile = {
        "admissible": 1.0,
        "topology_conditioned": 1.0,
    }

    assert formal_profile["observational"] >= 1.0
    assert attractor_profile["entropy_conditioned"] >= 1.0
    assert attractor_profile["topology_conditioned"] >= 1.0
    assert c1_profile["admissible"] >= 1.0
    assert c1_profile["topology_conditioned"] >= 1.0


def test_axis0_matched_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_matched_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_matched_marginal_packet.py",
    )

    gate_map = {
        "M1_phase4_and_phase5a_execute_cleanly": {"pass": True},
        "M2_phase4_winner_fails_matched_marginal_filter": {"pass": False},
        "M8_matched_marginal_layer_preserves_xi_downstream_handoff_contract": {"pass": True},
        "M9_matched_marginal_stays_subordinate_to_xi_downstream_mapping": {"pass": True},
        "M3_phase5a_certifies_marginal_preserving_family": {"pass": True},
        "M4_preserving_mi_collapses_while_chiral_mi_stays_large": {"pass": True},
        "M5_optimizer_finds_no_nonproduct_preserving_advantage": {"pass": False},
        "M6_exact_preserving_point_reference_stays_discriminator_only": {"pass": True},
        "M7_fe_indexed_pairs_remain_the_strongest_structured_refinement_candidate": {"pass": False},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 0.5
    assert profile["admissible"] == 1.0
    assert profile["stable"] == 2.0 / 3.0
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 2.0 / 3.0


def test_axis0_formal_geometry_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_formal_geometry_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_formal_geometry_packet.py",
    )

    gate_map = {
        "G1_exact_hopf_geometry_truth": {"pass": True},
        "G2_weyl_ambient_rung": {"pass": True},
        "G3_ambient_vs_engine_overlay": {"pass": False},
        "G4_live_engine_family_split": {"pass": True},
        "G5_dual_weyl_cycle_stability": {"pass": False},
        "G6_torus_negative_is_load_bearing": {"pass": True},
        "G7_no_chirality_negative_still_incomplete": {"pass": False},
        "G8_exact_loop_law_swap_negative": {"pass": True},
        "G9_owner_anchor_state_explicit": {"pass": True},
        "G10_lower_tier_carrier_admission_and_classical_leakage_guards_are_explicit": {"pass": True},
        "G11_chiral_readout_and_symmetric_bookkeeping_are_embargoed_from_law_promotion": {"pass": False},
        "G12_lower_tier_chiral_law_search_is_explicit_and_fail_closed": {"pass": True},
        "G13_lower_tier_transport_law_search_is_explicit_and_fail_closed": {"pass": False},
        "G14_lower_tier_operator_basis_search_is_explicit_and_fail_closed": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 0.75
    assert profile["admissible"] == 2.0 / 3.0
    assert profile["stable"] == 2.0 / 3.0
    assert profile["entropy_conditioned"] == 1.0 / 3.0
    assert profile["topology_conditioned"] == 2.0 / 3.0


def test_axis0_c1_bridge_object_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_c1_bridge_object_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_c1_bridge_object_packet.py",
    )

    gate_map = {
        "C1B1_bridge_object_is_explicit_and_downstream_only": {"pass": True},
        "C1B2_counterfeit_pressure_remains_bound_to_the_bridge_object": {"pass": False},
        "C1B3_bridge_object_is_bound_to_the_existing_support_contract": {"pass": True},
        "C1B4_bridge_object_keeps_owner_doctrine_questions_open": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 1.0
    assert profile["admissible"] == 1.0
    assert profile["stable"] == 2.0 / 3.0
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 1.0


def test_axis0_c1_signed_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_c1_signed_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_c1_signed_bridge_candidate_search.py",
    )

    gate_map = {
        "C1S1_current_signed_bridge_candidate_is_explicit": {"pass": True},
        "C1S2_counterfeit_pressure_keeps_signed_honesty_load_bearing": {"pass": False},
        "C1S3_support_chain_is_closed_before_candidate_packaging": {"pass": True},
        "C1S4_candidate_stays_provisional_and_does_not_overpromote": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 1.0
    assert profile["admissible"] == 1.0
    assert profile["stable"] == 2.0 / 3.0
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 1.0


def test_axis0_lower_tier_transport_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_lower_tier_transport_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_lower_tier_transport_law_search.py",
    )

    gate_map = {
        "T1_exact_same_carrier_loop_law_survives_search": {"pass": True},
        "T2_generic_transport_activity_is_not_promoted_to_law": {"pass": False},
        "T3_symmetric_motion_summary_is_killed_as_fake_transport_law": {"pass": True},
        "T4_downstream_cut_effect_is_fenced_off_from_lower_transport_law": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 1.0
    assert profile["admissible"] == 2.0 / 3.0
    assert profile["stable"] == 1.0
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 1.0


def test_axis0_weyl_delta_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_weyl_delta_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_weyl_delta_packet.py",
    )

    gate_map = {
        "W1_stagewise_raw_delta_surfaces_exist": {"pass": True},
        "W2_transport_geometry_is_mechanically_nontrivial": {"pass": True},
        "W3_chirality_differential_is_real_pre_axis_signal": {"pass": False},
        "W4_raw_lr_deltas_are_not_reducible_to_symmetric_dphi_shim": {"pass": True},
        "W5_branch_map_keeps_flux_placement_open": {"pass": False},
        "W6_flux_family_is_explicit_without_canonizing_flux": {"pass": True},
        "W7_branch_map_preserves_skeptical_flux_read": {"pass": False},
        "W8_pre_axis_object_inventory_is_explicit": {"pass": True},
        "W9_transport_embargo_boundary_is_explicit": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 2.0 / 3.0
    assert profile["admissible"] == 0.5
    assert profile["stable"] == 2.0 / 3.0
    assert profile["entropy_conditioned"] == 2.0 / 3.0
    assert profile["topology_conditioned"] == 0.75


def test_axis0_lower_tier_chiral_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_lower_tier_chiral_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_lower_tier_chiral_law_search.py",
    )

    gate_map = {
        "L1_fake_lower_tier_chiral_law_routes_are_killed": {"pass": True},
        "L2_delta_chirality_is_real_signal_but_not_owner_law": {"pass": False},
        "L3_compound_transport_chirality_branch_survives_search": {"pass": True},
        "L4_search_keeps_single_lower_tier_chiral_law_open_but_unadmitted": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 0.5
    assert profile["admissible"] == 2.0 / 3.0
    assert profile["stable"] == 1.0
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 1.0


def test_axis0_transport_embargo_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_transport_embargo_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_transport_embargo_packet.py",
    )

    gate_map = {
        "TE1_weyl_delta_transport_family_is_live_but_fail_closed": {"pass": True},
        "TE2_lower_tier_transport_law_stays_narrow_and_non_generic": {"pass": False},
        "TE3_transport_embargo_branch_is_explicitly_supported_but_not_promoted": {"pass": True},
        "TE4_nonproxy_support_and_embargo_blocker_are_bound_together": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 1.0
    assert profile["admissible"] == 0.75
    assert profile["stable"] == 0.5
    assert profile["entropy_conditioned"] == 1.0
    assert profile["topology_conditioned"] == 2.0 / 3.0


def test_axis0_no_chirality_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_no_chirality_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_no_chirality_search.py",
    )

    gate_map = {
        "N1_no_chirality_kill_is_real_but_not_total": {"pass": True},
        "N2_no_chirality_residual_is_explicitly_nontrivial": {"pass": False},
        "N3_chiral_run_keeps_stronger_sheet_split_than_flattened_run": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 2.0 / 3.0
    assert profile["admissible"] == 0.5
    assert profile["stable"] == 1.0
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 1.0


def test_axis0_attractor_boundary_packet_constraint_family_profile_is_typed() -> None:
    module = _load_module(
        "axis0_attractor_boundary_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_axis0_attractor_basin_boundary_search.py",
    )

    gate_map = {
        "AB1_trajectory_lr_asym_surface_is_explicit_and_nontrivial": {"pass": True},
        "AB2_ti_failure_boundary_is_explicit_and_predictive": {"pass": False},
        "AB3_observed_trajectory_stays_clear_of_the_ti_failure_regime": {"pass": True},
    }
    profile = module._packet_constraint_family_profile(gate_map)
    assert profile["observational"] == 0.5
    assert profile["admissible"] == 0.5
    assert profile["stable"] == 1.0
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 0.5


def test_axis0_stack_run_loads_emitted_constraint_profiles(tmp_path: Path) -> None:
    module = _load_module(
        "axis0_stack_run_under_test",
        REPO_ROOT / "system_v4" / "probes" / "run_axis0_stack_packet.py",
    )

    (tmp_path / "formal_geometry_packet_validation.json").write_text(
        json.dumps(
            {
                "constraint_family_profile": {
                    "observational": 1.0,
                    "admissible": 0.5,
                    "stable": 0.25,
                    "entropy_conditioned": 0.75,
                    "topology_conditioned": 1.0,
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "entropy_readout_packet_validation.json").write_text(
        json.dumps(
            {
                "constraint_family_profile": {
                    "observational": 0.5,
                    "admissible": 1.0,
                    "stable": 0.75,
                    "entropy_conditioned": 1.0,
                    "topology_conditioned": 0.5,
                }
            }
        ),
        encoding="utf-8",
    )

    profiles = module._load_constraint_profile_results(tmp_path)
    assert profiles["formal_geometry"]["stable"] == 0.25
    assert profiles["entropy_readout"]["entropy_conditioned"] == 1.0


def test_axis0_stack_run_constraint_family_profile_averages_emitted_sources() -> None:
    module = _load_module(
        "axis0_stack_run_profile_under_test",
        REPO_ROOT / "system_v4" / "probes" / "run_axis0_stack_packet.py",
    )

    profile = module._mean_profile(
        {
            "observational": 1.0,
            "admissible": 0.5,
            "stable": 0.5,
            "entropy_conditioned": 1.0,
            "topology_conditioned": 0.0,
        },
        {
            "observational": 0.0,
            "admissible": 1.0,
            "stable": 1.0,
            "entropy_conditioned": 0.0,
            "topology_conditioned": 1.0,
        },
    )
    assert profile["observational"] == 0.5
    assert profile["admissible"] == 0.75
    assert profile["stable"] == 0.75
    assert profile["entropy_conditioned"] == 0.5
    assert profile["topology_conditioned"] == 0.5


def test_axis0_stack_constraint_family_profile_averages_sources() -> None:
    module = _load_module(
        "axis0_stack_packet_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_axis0_stack_packet.py",
    )

    profile = module._mean_profile(
        {"observational": 1.0, "admissible": 0.5, "stable": 0.75, "entropy_conditioned": 1.0, "topology_conditioned": 0.5},
        {"observational": 0.0, "admissible": 1.0, "stable": 0.25, "entropy_conditioned": 0.5, "topology_conditioned": 1.0},
    )
    assert profile["observational"] == 0.5
    assert profile["admissible"] == 0.75
    assert profile["stable"] == 0.5
    assert profile["entropy_conditioned"] == 0.75
    assert profile["topology_conditioned"] == 0.75


def test_carrier_and_root_bridge_owner_alignment_contracts_are_fail_closed() -> None:
    carrier_module = _load_module(
        "axis0_carrier_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_carrier_selection_packet.py",
    )
    root_module = _load_module(
        "axis0_root_under_test",
        REPO_ROOT / "system_v4" / "probes" / "validate_root_emergence_packet.py",
    )
    alignment = {
        "pass": True,
        "status": "axis_internal_candidate_not_final_owner_law",
        "placement_relation": "downstream_axis_internal_bridge_candidate_derived_from_xi_hist_signed_law",
        "owner_dependency": "must_bind_under_xi_hist_signed_law",
        "forbidden_reclassification": "not_owner_derived_not_final_owner_xi",
        "winner": "Xi_chiral_entangle",
        "runner_up": "Xi_chiral_hist_entangle",
    }

    assert carrier_module.bridge_owner_alignment_ok(alignment) is True
    assert root_module.bridge_owner_alignment_ok(alignment) is True

    broken = dict(alignment)
    broken["status"] = "final_owner_law"
    assert carrier_module.bridge_owner_alignment_ok(broken) is False
    assert root_module.bridge_owner_alignment_ok(broken) is False
