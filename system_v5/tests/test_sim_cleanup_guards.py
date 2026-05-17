from __future__ import annotations

import argparse
import importlib.util
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
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
        if path.name == "queue_claim.py":
            module.STRICT_WIZARD_QUEUE_ADMISSION = False
            module.CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION = False
        return module
    finally:
        sys.modules.pop(module_name, None)
        if inserted_parent:
            sys.path.remove(module_parent)


def test_repo_hygiene_classifies_visualizer_data_payloads_as_generated() -> None:
    module = _load_module(
        "repo_hygiene_visualizer_payloads_under_test",
        REPO_ROOT / "system_v4" / "probes" / "repo_hygiene_audit.py",
    )

    assert module.is_generated_artifact_path("visualizer/prime-qit-sidecar-data.js")
    assert module.is_generated_artifact_path("visualizer/cycle-invariant-correlation-data.js")
    assert not module.is_generated_artifact_path("visualizer/app.jsx")
    assert not module.is_generated_artifact_path("visualizer/engine_primitives.jsx")
    assert not module.is_generated_artifact_path("visualizer/DESIGN.md")


def test_source_dirty_plan_skips_visualizer_generated_data_payloads(monkeypatch) -> None:
    module = _load_module(
        "source_dirty_plan_visualizer_payloads_under_test",
        REPO_ROOT / "system_v4" / "probes" / "source_dirty_checkpoint_plan.py",
    )

    class Completed:
        stdout = "\n".join(
            [
                "?? visualizer/prime-qit-sidecar-data.js",
                "?? visualizer/rosetta-triad-modes-data.js",
                "?? visualizer/app.jsx",
                " M system_v4/probes/sim_prime_qit_sidecar_probe.py",
            ]
        )

    monkeypatch.setattr(module.subprocess, "run", lambda *args, **kwargs: Completed())

    entries = module.git_source_entries()

    assert entries == [
        {"path": "visualizer/app.jsx", "status_kind": "untracked"},
        {"path": "system_v4/probes/sim_prime_qit_sidecar_probe.py", "status_kind": "modified"},
    ]


def test_cleanup_first_guard_allows_maintenance_context_with_dirty_repo(
    tmp_path, monkeypatch, capsys
) -> None:
    module = _load_module(
        "cleanup_first_guard_maintenance_context_under_test",
        REPO_ROOT / "system_v4" / "probes" / "cleanup_first_guard.py",
    )

    results = tmp_path / "results"
    results.mkdir()
    supervisor = results / "system_hygiene_supervisor_results.json"
    supervisor.write_text(
        json.dumps(
            {
                "repo_hygiene_green": False,
                "overall_green": False,
                "repair_queue_count": 1,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "PROJECT_DIR", tmp_path)
    monkeypatch.setattr(module, "SUPERVISOR_PATH", supervisor)
    monkeypatch.setattr(sys, "argv", ["cleanup_first_guard.py", "--context", "hygiene"])

    assert module.main() == 0
    out = capsys.readouterr().out
    assert "CLEANUP FIRST GUARD PASSED context=hygiene" in out
    assert "blocks new sim execution" in out


def test_cleanup_first_guard_still_blocks_sim_context_with_dirty_repo(
    tmp_path, monkeypatch, capsys
) -> None:
    module = _load_module(
        "cleanup_first_guard_sim_context_under_test",
        REPO_ROOT / "system_v4" / "probes" / "cleanup_first_guard.py",
    )

    results = tmp_path / "results"
    results.mkdir()
    supervisor = results / "system_hygiene_supervisor_results.json"
    supervisor.write_text(
        json.dumps(
            {
                "repo_hygiene_green": False,
                "overall_green": False,
                "repair_queue_count": 1,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "PROJECT_DIR", tmp_path)
    monkeypatch.setattr(module, "SUPERVISOR_PATH", supervisor)
    monkeypatch.setattr(sys, "argv", ["cleanup_first_guard.py", "--context", "sim"])

    assert module.main() == 1
    out = capsys.readouterr().out
    assert "CLEANUP FIRST GUARD FAILED context=sim" in out


def test_rosetta_completion_audit_keeps_cleanup_gate_as_blocker(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "rosetta_completion_audit_cleanup_blocker_under_test",
        REPO_ROOT / "system_v4" / "probes" / "rosetta_goal_completion_audit.py",
    )

    project = tmp_path / "repo"
    results = project / "system_v4" / "probes" / "a2_state" / "sim_results"
    evidence = project / "system_v5" / "evidence"
    results.mkdir(parents=True)
    evidence.mkdir(parents=True)

    def write_result(name: str, summary: dict) -> Path:
        path = results / name
        path.write_text(json.dumps({"summary": summary}), encoding="utf-8")
        return path

    paths = {
        "probe_truth": write_result("probe_truth_audit_results.json", {"ok": True}),
        "controller_alignment": write_result(
            "controller_alignment_audit_results.json",
            {"code_process_green": True, "controller_contract_current": True},
        ),
        "migration_contract": write_result("migration_contract_audit_results.json", {"ok": True}),
        "lego_tool_reporting": write_result("lego_tool_reporting_audit_results.json", {"ok": True}),
        "repo_hygiene": write_result(
            "repo_hygiene_audit_results.json",
            {"dirty_worktree_count": 3, "source_dirty_count": 2, "generated_dirty_count": 1},
        ),
        "system_hygiene": write_result(
            "system_hygiene_supervisor_results.json",
            {
                "truth_green": True,
                "controller_green": True,
                "migration_green": True,
                "lego_tool_reporting_green": True,
                "repo_hygiene_green": False,
                "overall_green": False,
            },
        ),
        "lane_catalog": write_result(
            "source_dirty_lane_catalog.json",
            {
                "lane_count": 1,
                "ready_for_checkpoint_review_count": 1,
                "missing_companion_count": 0,
                "stage_path_count": 4,
            },
        ),
        "lane_catalog_md": results / "source_dirty_lane_catalog.md",
        "parallel_review_md": results / "source_dirty_parallel_review.md",
        "prime_sidecar": write_result(
            "prime_qit_sidecar_probe_results.json",
            {
                "all_pass": True,
                "claim_ceiling": "sidecar_probe_candidate_prior_only",
                "recommendation": "retool",
            },
        ),
        "prime_sidecar_graveyard": write_result(
            "prime_qit_sidecar_graveyard_results.json",
            {
                "all_pass": True,
                "claim_ceiling": "sidecar_graveyard_control_only",
                "recommendation": "retool",
            },
        ),
        "prime_rosetta_fit": write_result(
            "prime_rosetta_sidecar_fit_results.json",
            {
                "all_pass": True,
                "claim_ceiling": "sidecar_fit_diagnostic_only",
                "recommendation": "retool",
                "all_fits_diagnostic_only": True,
            },
        ),
        "iching_rosetta": write_result("six_bit_gray_code_single_flip_cycle_invariant_results.json", {"all_pass": True}),
        "visualizer_audit": write_result(
            "visualizer_engine_lab_receipt_audit_results.json",
            {"all_pass": True, "qit_or_axis_promotion_allowed": False},
        ),
        "z3_capability": write_result("z3_capability_results.json", {"all_pass": True}),
        "cvc5_capability": write_result("cvc5_capability_results.json", {"all_pass": True}),
        "clifford_capability": write_result("clifford_capability_results.json", {"all_pass": True}),
        "cycle_receipt_coupling_candidate_registry": write_result("cycle_receipt_coupling_candidate_registry_results.json", {"all_pass": True}),
        "rosetta_coupled_array": write_result(
            "rosetta_lego_coupled_array_results.json", {"all_pass": True}
        ),
        "rosetta_coupled_array_graveyard": write_result(
            "rosetta_lego_coupled_array_graveyard_results.json", {"all_pass": True}
        ),
    }
    inventory = evidence / "sim_inventory_index.json"
    inventory.write_text(
        json.dumps(
            {
                "summary": {
                    "admitted_count": 9,
                    "admission_repair_count": 0,
                    "unlinked_result_json_count": 0,
                },
                "admitted_stems": ["sim_z3_capability", "sim_cvc5_capability"],
            }
        ),
        encoding="utf-8",
    )
    paths["inventory"] = inventory
    paths["inventory_unlinked_audit"] = write_result(
        "inventory_unlinked_result_audit_results.json",
        {"all_pass": True, "possible_orphan_count": 0, "source_link_gap_count": 0},
    )

    monkeypatch.setattr(module, "PROJECT_DIR", project)
    monkeypatch.setattr(module, "RESULTS_DIR", results)
    monkeypatch.setattr(module, "OUT_JSON", results / "rosetta_goal_completion_audit_results.json")
    monkeypatch.setattr(module, "OUT_MD", results / "rosetta_goal_completion_audit.md")
    monkeypatch.setattr(module, "PATHS", paths)

    report = module.build_report()

    assert report["completion_status"] == "blocked"
    assert report["checklist"]["repo_cleanup_gate"]["status"] == "blocked"
    assert report["checklist"]["tracking_and_admission_truth"]["status"] == "met"
    assert report["checklist"]["rosetta_registry_and_coupling_receipts"]["status"] == "met"
    assert any(
        item["requirement"].startswith("Do not claim goal complete")
        and item["status"] == "blocked"
        for item in report["prompt_to_artifact_checklist"]
    )


def test_rosetta_completion_audit_blocks_prime_sidecar_overclaim(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "rosetta_completion_audit_prime_overclaim_under_test",
        REPO_ROOT / "system_v4" / "probes" / "rosetta_goal_completion_audit.py",
    )

    project = tmp_path / "repo"
    results = project / "system_v4" / "probes" / "a2_state" / "sim_results"
    evidence = project / "system_v5" / "evidence"
    results.mkdir(parents=True)
    evidence.mkdir(parents=True)

    def write_result(name: str, summary: dict) -> Path:
        path = results / name
        path.write_text(json.dumps({"summary": summary}), encoding="utf-8")
        return path

    passing = {"all_pass": True}
    paths = {
        "probe_truth": write_result("probe_truth_audit_results.json", {"ok": True}),
        "controller_alignment": write_result(
            "controller_alignment_audit_results.json",
            {"code_process_green": True, "controller_contract_current": True},
        ),
        "migration_contract": write_result("migration_contract_audit_results.json", {"ok": True}),
        "lego_tool_reporting": write_result("lego_tool_reporting_audit_results.json", {"ok": True}),
        "repo_hygiene": write_result(
            "repo_hygiene_audit_results.json",
            {"dirty_worktree_count": 0, "source_dirty_count": 0, "generated_dirty_count": 0},
        ),
        "system_hygiene": write_result(
            "system_hygiene_supervisor_results.json",
            {
                "truth_green": True,
                "controller_green": True,
                "migration_green": True,
                "lego_tool_reporting_green": True,
                "repo_hygiene_green": True,
                "overall_green": True,
            },
        ),
        "lane_catalog": write_result(
            "source_dirty_lane_catalog.json",
            {
                "lane_count": 1,
                "ready_for_checkpoint_review_count": 1,
                "missing_companion_count": 0,
                "stage_path_count": 4,
            },
        ),
        "lane_catalog_md": results / "source_dirty_lane_catalog.md",
        "parallel_review_md": results / "source_dirty_parallel_review.md",
        "prime_sidecar": write_result(
            "prime_qit_sidecar_probe_results.json",
            {"all_pass": True, "claim_ceiling": "riemann_solved", "recommendation": "promote"},
        ),
        "prime_sidecar_graveyard": write_result(
            "prime_qit_sidecar_graveyard_results.json",
            {
                "all_pass": True,
                "claim_ceiling": "sidecar_graveyard_control_only",
                "recommendation": "retool",
            },
        ),
        "prime_rosetta_fit": write_result(
            "prime_rosetta_sidecar_fit_results.json",
            {
                "all_pass": True,
                "claim_ceiling": "sidecar_fit_diagnostic_only",
                "recommendation": "retool",
                "all_fits_diagnostic_only": True,
            },
        ),
        "iching_rosetta": write_result("six_bit_gray_code_single_flip_cycle_invariant_results.json", passing),
        "visualizer_audit": write_result(
            "visualizer_engine_lab_receipt_audit_results.json",
            {"all_pass": True, "qit_or_axis_promotion_allowed": False},
        ),
        "z3_capability": write_result("z3_capability_results.json", passing),
        "cvc5_capability": write_result("cvc5_capability_results.json", passing),
        "clifford_capability": write_result("clifford_capability_results.json", passing),
        "cycle_receipt_coupling_candidate_registry": write_result("cycle_receipt_coupling_candidate_registry_results.json", passing),
        "rosetta_coupled_array": write_result("rosetta_lego_coupled_array_results.json", passing),
        "rosetta_coupled_array_graveyard": write_result(
            "rosetta_lego_coupled_array_graveyard_results.json", passing
        ),
    }
    inventory = evidence / "sim_inventory_index.json"
    inventory.write_text(
        json.dumps(
            {
                "summary": {
                    "admitted_count": 9,
                    "admission_repair_count": 0,
                    "unlinked_result_json_count": 0,
                },
                "admitted_stems": ["sim_z3_capability", "sim_cvc5_capability"],
            }
        ),
        encoding="utf-8",
    )
    paths["inventory"] = inventory
    paths["inventory_unlinked_audit"] = write_result(
        "inventory_unlinked_result_audit_results.json",
        {"all_pass": True, "possible_orphan_count": 0, "source_link_gap_count": 0},
    )

    monkeypatch.setattr(module, "PROJECT_DIR", project)
    monkeypatch.setattr(module, "RESULTS_DIR", results)
    monkeypatch.setattr(module, "OUT_JSON", results / "rosetta_goal_completion_audit_results.json")
    monkeypatch.setattr(module, "OUT_MD", results / "rosetta_goal_completion_audit.md")
    monkeypatch.setattr(module, "PATHS", paths)

    report = module.build_report()

    assert report["completion_status"] == "blocked"
    assert report["checklist"]["bounded_prime_sidecar"]["status"] == "blocked"
    assert any(
        item["requirement"].startswith("Run bounded prime/Riemann sidecar")
        and item["status"] == "blocked"
        for item in report["prompt_to_artifact_checklist"]
    )


def test_source_dirty_lane_manifest_can_select_manual_next_lane(
    tmp_path, monkeypatch, capsys
) -> None:
    module = _load_module(
        "source_dirty_lane_manifest_manual_next_under_test",
        REPO_ROOT / "system_v4" / "probes" / "source_dirty_lane_manifest.py",
    )

    results = tmp_path / "results"
    results.mkdir()
    plan_path = results / "source_dirty_checkpoint_plan.json"
    out_path = results / "source_dirty_lane_manifest.json"
    plan_path.write_text(
        json.dumps(
            {
                "checkpoint_groups": [],
                "recommended_checkpoint_order": [],
                "next_code_only_manual": {
                    "group_id": "probe_source__sim_family_iching",
                    "file_count": 1,
                    "untracked_count": 1,
                    "tracked_dirty_count": 0,
                    "safe_next_action": "manual_split_required",
                    "source_path": "system_v4/probes/sim_six_bit_gray_code_single_flip_cycle_invariant.py",
                    "result_path": "system_v4/probes/a2_state/sim_results/six_bit_gray_code_single_flip_cycle_invariant_results.json",
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "PROJECT_DIR", tmp_path)
    monkeypatch.setattr(module, "PLAN_PATH", plan_path)
    monkeypatch.setattr(module, "OUT_PATH", out_path)
    monkeypatch.setattr(sys, "argv", ["source_dirty_lane_manifest.py", "--allow-manual"])

    assert module.main() == 0
    out = capsys.readouterr().out
    assert "manual-only lane selected" in out
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"]["status"] == "manual_only_lane_selected"
    assert payload["summary"]["manual_review_required"] is True
    lane_manifest = results / "source_dirty_lane_manifest__probe_source__sim_family_iching.json"
    lane_payload = json.loads(lane_manifest.read_text(encoding="utf-8"))
    assert payload["lane_specific_manifest_path"].endswith(str(lane_manifest.relative_to(tmp_path)))
    assert lane_payload["selected_group_id"] == "probe_source__sim_family_iching"
    assert "last-write-wins latest pointer" in lane_payload["concurrency_note"]
    assert payload["executable_lane"]["files"] == [
        "system_v4/probes/sim_six_bit_gray_code_single_flip_cycle_invariant.py"
    ]


def test_source_dirty_lane_manifest_can_select_explicit_manual_lane(
    tmp_path, monkeypatch, capsys
) -> None:
    module = _load_module(
        "source_dirty_lane_manifest_explicit_manual_under_test",
        REPO_ROOT / "system_v4" / "probes" / "source_dirty_lane_manifest.py",
    )

    results = tmp_path / "results"
    results.mkdir()
    plan_path = results / "source_dirty_checkpoint_plan.json"
    out_path = results / "source_dirty_lane_manifest.json"
    plan_path.write_text(
        json.dumps(
            {
                "checkpoint_groups": [],
                "recommended_checkpoint_order": [],
                "recommended_code_only_order": [
                    {
                        "group_id": "probe_source__sim_family_iching",
                        "file_count": 1,
                        "safe_next_action": "manual_split_required",
                        "source_path": "system_v4/probes/sim_six_bit_gray_code_single_flip_cycle_invariant.py",
                        "result_path": "system_v4/probes/a2_state/sim_results/six_bit_gray_code_single_flip_cycle_invariant_results.json",
                    },
                    {
                        "group_id": "probe_source__sim_family_prime",
                        "file_count": 1,
                        "safe_next_action": "manual_split_required",
                        "source_path": "system_v4/probes/sim_prime_qit_sidecar_probe.py",
                        "result_path": "system_v4/probes/a2_state/sim_results/prime_qit_sidecar_probe_results.json",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "PROJECT_DIR", tmp_path)
    monkeypatch.setattr(module, "PLAN_PATH", plan_path)
    monkeypatch.setattr(module, "OUT_PATH", out_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "source_dirty_lane_manifest.py",
            "--allow-manual",
            "--group-id",
            "probe_source__sim_family_prime",
        ],
    )

    assert module.main() == 0
    out = capsys.readouterr().out
    assert "probe_source__sim_family_prime (manual-only)" in out
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"]["selected_group_id"] == "probe_source__sim_family_prime"
    assert payload["selection_mode"] == "explicit_manual"
    lane_manifest = results / "source_dirty_lane_manifest__probe_source__sim_family_prime.json"
    assert lane_manifest.exists()
    assert payload["executable_lane"]["files"] == [
        "system_v4/probes/sim_prime_qit_sidecar_probe.py"
    ]


def test_source_dirty_lane_manifest_can_select_manual_group_lane(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "source_dirty_lane_manifest_manual_group_under_test",
        REPO_ROOT / "system_v4" / "probes" / "source_dirty_lane_manifest.py",
    )

    results = tmp_path / "results"
    results.mkdir()
    plan_path = results / "source_dirty_checkpoint_plan.json"
    out_path = results / "source_dirty_lane_manifest.json"
    plan_path.write_text(
        json.dumps(
            {
                "checkpoint_groups": [
                    {
                        "group_id": "probe_source__sim_family_carnot",
                        "file_count": 2,
                        "safe_next_action": "manual_split_required",
                        "path_prefixes": [
                            "system_v4/probes/sim_carnot_alpha.py",
                            "system_v4/probes/sim_carnot_beta.py",
                        ],
                    }
                ],
                "recommended_checkpoint_order": [],
                "recommended_code_only_order": [
                    {
                        "group_id": "probe_source__sim_family_carnot",
                        "file_count": 2,
                        "safe_next_action": "manual_split_required",
                        "source_path": None,
                        "result_path": None,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "PROJECT_DIR", tmp_path)
    monkeypatch.setattr(module, "PLAN_PATH", plan_path)
    monkeypatch.setattr(module, "OUT_PATH", out_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "source_dirty_lane_manifest.py",
            "--allow-manual",
            "--group-id",
            "probe_source__sim_family_carnot",
        ],
    )

    assert module.main() == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"]["selected_group_id"] == "probe_source__sim_family_carnot"
    assert payload["executable_lane"]["files"] == [
        "system_v4/probes/sim_carnot_alpha.py",
        "system_v4/probes/sim_carnot_beta.py",
    ]
    assert payload["executable_lane"]["result_companions"] == [
        "system_v4/probes/a2_state/sim_results/carnot_alpha_results.json",
        "system_v4/probes/a2_state/sim_results/carnot_beta_results.json",
    ]


def test_source_dirty_checkpoint_packet_includes_visual_payload_companion(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "source_dirty_checkpoint_packet_visual_payload_under_test",
        REPO_ROOT / "system_v4" / "probes" / "source_dirty_checkpoint_packet.py",
    )

    repo = tmp_path / "repo"
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    visualizer = repo / "visualizer"
    results.mkdir(parents=True)
    visualizer.mkdir()
    (results / "probe_truth_audit_results.json").write_text(
        json.dumps({"summary": {"ok": True}}),
        encoding="utf-8",
    )
    (results / "repo_hygiene_audit_results.json").write_text(
        json.dumps({"summary": {"root_result_orphan_count": 0, "secondary_result_count": 0, "duplicate_result_basename_count": 0}}),
        encoding="utf-8",
    )
    (results / "prime_qit_sidecar_probe_results.json").write_text(
        json.dumps({"summary": {"visual_payload": "visualizer/prime-qit-sidecar-data.js"}}),
        encoding="utf-8",
    )
    (visualizer / "prime-qit-sidecar-data.js").write_text("window.X = {};\n", encoding="utf-8")
    manifest = results / "source_dirty_lane_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "lane_id": "source_dirty__probe_source__sim_family_prime",
                "selected_group_id": "probe_source__sim_family_prime",
                "executable_lane": {
                    "group_id": "probe_source__sim_family_prime",
                    "files": ["system_v4/probes/sim_prime_qit_sidecar_probe.py"],
                    "result_companions": [
                        "system_v4/probes/a2_state/sim_results/prime_qit_sidecar_probe_results.json"
                    ],
                    "required_git_paths_clean": [
                        "system_v4/probes/sim_prime_qit_sidecar_probe.py",
                        "system_v4/probes/a2_state/sim_results/prime_qit_sidecar_probe_results.json",
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "PROJECT_DIR", repo)
    monkeypatch.setattr(module, "RESULTS_DIR", results)
    monkeypatch.setattr(module, "LANE_MANIFEST_PATH", manifest)
    monkeypatch.setattr(module, "TRUTH_AUDIT_PATH", results / "probe_truth_audit_results.json")
    monkeypatch.setattr(module, "REPO_HYGIENE_PATH", results / "repo_hygiene_audit_results.json")
    monkeypatch.setattr(module, "OUT_PATH", results / "source_dirty_checkpoint_packet.json")
    monkeypatch.setattr(module, "git_status_for", lambda paths: [f"?? {path}" for path in paths])

    assert module.main() == 0
    payload = json.loads((results / "source_dirty_checkpoint_packet.json").read_text(encoding="utf-8"))
    lane_packet = results / "source_dirty_checkpoint_packet__probe_source__sim_family_prime.json"
    lane_payload = json.loads(lane_packet.read_text(encoding="utf-8"))
    assert "visualizer/prime-qit-sidecar-data.js" in payload["result_companions"]
    assert "visualizer/prime-qit-sidecar-data.js" in payload["required_git_paths_clean"]
    assert payload["lane_specific_packet_path"].endswith(str(lane_packet.relative_to(repo)))
    assert lane_payload["group_id"] == "probe_source__sim_family_prime"
    assert "last-write-wins latest pointer" in lane_payload["concurrency_note"]


def test_source_dirty_stage_plan_keeps_source_maintenance_scripts(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "source_dirty_stage_plan_keeps_source_scripts_under_test",
        REPO_ROOT / "system_v4" / "probes" / "source_dirty_stage_plan.py",
    )

    results = tmp_path / "results"
    results.mkdir()
    manifest_path = results / "source_dirty_lane_manifest.json"
    packet_path = results / "source_dirty_checkpoint_packet.json"
    out_path = results / "source_dirty_stage_plan.json"
    manifest_path.write_text(
        json.dumps({"lane_id": "source_dirty__probe_source__probe_misc", "selected_group_id": "probe_source__probe_misc"}),
        encoding="utf-8",
    )
    packet_path.write_text(
        json.dumps(
            {
                "group_id": "probe_source__probe_misc",
                "ready_for_checkpoint": True,
                "owned_files": [
                    "system_v4/probes/source_dirty_lane_manifest.py",
                    "system_v4/probes/source_dirty_stage_plan.py",
                ],
                "result_companions": [],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "PROJECT_DIR", tmp_path)
    monkeypatch.setattr(module, "RESULTS_DIR", results)
    monkeypatch.setattr(module, "LANE_MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(module, "CHECKPOINT_PACKET_PATH", packet_path)
    monkeypatch.setattr(module, "OUT_PATH", out_path)

    assert module.main() == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    lane_stage_plan = results / "source_dirty_stage_plan__probe_source__probe_misc.json"
    lane_payload = json.loads(lane_stage_plan.read_text(encoding="utf-8"))
    assert "system_v4/probes/source_dirty_lane_manifest.py" in payload["stage_paths"]
    assert "system_v4/probes/source_dirty_stage_plan.py" in payload["stage_paths"]
    assert payload["lane_specific_stage_plan_path"].endswith(str(lane_stage_plan.relative_to(tmp_path)))
    assert lane_payload["summary"]["ready_for_staging"] is True


def test_source_dirty_lane_catalog_expands_result_and_visual_payload(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "source_dirty_lane_catalog_under_test",
        REPO_ROOT / "system_v4" / "probes" / "source_dirty_lane_catalog.py",
    )

    repo = tmp_path / "repo"
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    visualizer = repo / "visualizer"
    results.mkdir(parents=True)
    visualizer.mkdir()
    plan_path = results / "source_dirty_checkpoint_plan.json"
    out_path = results / "source_dirty_lane_catalog.json"
    out_md = results / "source_dirty_lane_catalog.md"
    (results / "cycle_receipt_coupling_candidate_registry_results.json").write_text(
        json.dumps({"summary": {"visual_payload": "visualizer/cycle-receipt-coupling-candidate-registry-data.js"}}),
        encoding="utf-8",
    )
    (visualizer / "cycle-receipt-coupling-candidate-registry-data.js").write_text("window.X = {};\n", encoding="utf-8")
    plan_path.write_text(
        json.dumps(
            {
                "checkpoint_groups": [
                    {
                        "group_id": "probe_source__sim_family_rosetta",
                        "bucket": "probe_source",
                        "display_name": "Rosetta",
                        "safe_next_action": "manual_split_required",
                        "file_count": 1,
                        "path_prefixes": ["system_v4/probes/sim_cycle_receipt_coupling_candidate_registry.py"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "PROJECT_DIR", repo)
    monkeypatch.setattr(module, "RESULTS_DIR", results)
    monkeypatch.setattr(module, "PLAN_PATH", plan_path)
    monkeypatch.setattr(module, "TRUTH_AUDIT_PATH", results / "probe_truth_audit_results.json")
    monkeypatch.setattr(module, "REPO_HYGIENE_PATH", results / "repo_hygiene_audit_results.json")
    monkeypatch.setattr(module, "OUT_PATH", out_path)
    monkeypatch.setattr(module, "OUT_MD", out_md)
    monkeypatch.setattr(module, "git_status_for", lambda paths: [])

    assert module.main() == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    lane = payload["lanes"][0]
    assert lane["stage_paths"] == [
        "system_v4/probes/sim_cycle_receipt_coupling_candidate_registry.py",
        "system_v4/probes/a2_state/sim_results/cycle_receipt_coupling_candidate_registry_results.json",
        "visualizer/cycle-receipt-coupling-candidate-registry-data.js",
    ]
    assert lane["ready_for_checkpoint_review"] is True
    assert lane["decision_needed"] == "checkpoint_or_rework_probe_lane"
    markdown = out_md.read_text(encoding="utf-8")
    assert "Source Dirty Lane Catalog" in markdown
    assert "decision needed: checkpoint_or_rework_probe_lane" in markdown


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
    _write_allow_stage_gate(repo)
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


def test_lint_blocks_numpy_bridge_and_requires_pytorch_for_nonclassical(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "lint_sim_contract_nonclassical_tools_under_test",
        REPO_ROOT / "scripts" / "lint_sim_contract.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)

    for tool in ("numpy", "z3", "pytorch"):
        (probes / f"sim_{tool}_capability.py").write_text(
            "\n".join(
                [
                    'classification = "canonical"',
                    f'TOOL_MANIFEST = {{"{tool}": {{"used": True, "reason": "capability"}}}}',
                    f'TOOL_INTEGRATION_DEPTH = {{"{tool}": "load_bearing"}}',
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        (results / f"{tool}_capability_results.json").write_text(
            json.dumps({"summary": {"all_pass": True}}),
            encoding="utf-8",
        )

    bridge = probes / "sim_bridge_numpy_row.py"
    bridge.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'sim_execution_kind = "bridge"',
                'TOOL_MANIFEST = {"numpy": {"used": True, "reason": "bridge fixture"}}',
                'TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    nonclassical_missing_pytorch = probes / "sim_nonclassical_z3_only.py"
    nonclassical_missing_pytorch.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'sim_execution_kind = "nonclassical"',
                'TOOL_MANIFEST = {"z3": {"used": True, "reason": "symbolic fixture"}}',
                'TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    nonclassical_pytorch = probes / "sim_nonclassical_pytorch_row.py"
    nonclassical_pytorch.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'sim_execution_kind = "nonclassical"',
                'TOOL_MANIFEST = {"pytorch": {"used": True, "reason": "tensor dynamics fixture"}}',
                'TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    nonclassical_bridge_numpy = probes / "sim_nonclassical_bridge_numpy.py"
    nonclassical_bridge_numpy.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'sim_execution_kind = "nonclassical_bridge"',
                'TOOL_MANIFEST = {"numpy": {"used": True, "reason": "bridge alias fixture"}}',
                'TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    bridge_rules = {violation["rule"] for violation in module.lint_sim(bridge)}
    z3_rules = {violation["rule"] for violation in module.lint_sim(nonclassical_missing_pytorch)}
    pytorch_rules = {violation["rule"] for violation in module.lint_sim(nonclassical_pytorch)}
    bridge_alias_rules = {violation["rule"] for violation in module.lint_sim(nonclassical_bridge_numpy)}

    assert "C7_numpy_load_bearing_for_bridge_or_nonclassical" in bridge_rules
    assert "C8_nonclassical_requires_pytorch_load_bearing" in z3_rules
    assert "C7_numpy_load_bearing_for_bridge_or_nonclassical" not in pytorch_rules
    assert "C8_nonclassical_requires_pytorch_load_bearing" not in pytorch_rules
    assert "C7_numpy_load_bearing_for_bridge_or_nonclassical" in bridge_alias_rules


def test_adaptive_controller_honors_explicit_sim_execution_kind(tmp_path) -> None:
    module = _load_module(
        "adaptive_controller_execution_kind_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    classical = probes / "sim_carnot_cycle.py"
    classical.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'sim_execution_kind = "classical"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    bridge = probes / "sim_szilard_measure_feedback_cycle.py"
    bridge.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'sim_execution_kind = "bridge"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    semiclassical = probes / "sim_szilard_landauer_cycle.py"
    semiclassical.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'SIM_EXECUTION_KIND = "semiclassical_szilard"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    nonclassical = probes / "sim_pytorch_channel.py"
    nonclassical.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'sim_execution_kind = "nonclassical"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert module.runner_class_for(classical) == "classical"
    assert module.runner_class_reason(classical) == "sim_execution_kind_classical"
    assert module.runner_class_for(bridge) == "bridge"
    assert module.runner_class_reason(bridge) == "sim_execution_kind_bridge"
    assert module.runner_class_for(semiclassical) == "bridge"
    assert module.runner_class_reason(semiclassical) == "sim_execution_kind_bridge"
    assert module.runner_class_for(nonclassical) == "nonclassical"
    assert module.runner_class_reason(nonclassical) == "sim_execution_kind_nonclassical"


def test_lint_accepts_explicit_path_arguments(tmp_path, monkeypatch, capsys) -> None:
    module = _load_module(
        "lint_sim_contract_path_args_under_test",
        REPO_ROOT / "scripts" / "lint_sim_contract.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    sim_path = probes / "sim_bridge_numpy_row.py"
    sim_path.write_text(
        "\n".join(
            [
                'classification = "canonical"',
                'sim_execution_kind = "bridge"',
                'TOOL_MANIFEST = {"numpy": {"used": True, "reason": "bridge fixture"}}',
                'TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)
    monkeypatch.setattr(sys, "argv", ["lint_sim_contract.py", str(sim_path)])

    assert module.main() == 1
    report = json.loads(capsys.readouterr().out)
    assert report["checked"] == 1
    assert report["violations_by_type"]["C7_numpy_load_bearing_for_bridge_or_nonclassical"] == 1


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


def test_gate_extracts_depth_updates_after_manifest_comprehension(tmp_path) -> None:
    module = _load_module(
        "verify_load_bearing_depth_updates_under_test",
        REPO_ROOT / "scripts" / "verify_load_bearing_has_capability_probe.py",
    )
    sim = tmp_path / "sim_dynamic_depth.py"
    sim.write_text(
        "\n".join(
            [
                "TOOL_MANIFEST = {'e3nn': {'tried': True, 'used': True, 'reason': 'fixture'}}",
                "TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}",
                "TOOL_INTEGRATION_DEPTH['e3nn'] = 'load_bearing'",
                "TOOL_INTEGRATION_DEPTH['pytorch'] = 'supportive'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert module.extract_tool_integration_depth(sim) == {
        "e3nn": "load_bearing",
        "pytorch": "supportive",
    }


def test_gate_extracts_depth_when_manifest_values_are_nonliteral(tmp_path) -> None:
    module = _load_module(
        "verify_load_bearing_nonliteral_manifest_under_test",
        REPO_ROOT / "scripts" / "verify_load_bearing_has_capability_probe.py",
    )
    sim = tmp_path / "sim_nonliteral_manifest_depth.py"
    sim.write_text(
        "\n".join(
            [
                "_REASON = 'shared reason text'",
                "TOOL_MANIFEST = {'cvc5': {'tried': True, 'used': True, 'reason': _REASON}}",
                "TOOL_INTEGRATION_DEPTH = {tool: None for tool in TOOL_MANIFEST}",
                "TOOL_INTEGRATION_DEPTH['cvc5'] = 'load_bearing'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    assert module.extract_tool_integration_depth(sim) == {"cvc5": "load_bearing"}


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

    sim = probes / "sim_clifford_holo_dirac_topology_variants.py"
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

    sim = probes / "sim_weyl_chirality_core.py"
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
    assert payload["plan_stage"] == "early_core"


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

    assert claimed is None
    blocked = list((queue_root / "blocked").glob("*.json*"))
    assert len(blocked) == 1
    payload = json.loads(blocked[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_weyl_chirality_bipartite.py"
    assert payload["blocked_reason"] == "stage_gate_blocked"
    assert exploratory.exists()


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

    assert claimed is None
    blocked = list((queue_root / "blocked").glob("*.json*"))
    assert len(blocked) == 1
    payload = json.loads(blocked[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_weyl_chirality_bipartite.py"
    assert payload["blocked_reason"] == "stage_gate_blocked"
    assert exploratory.exists()


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

    assert claimed is None
    blocked = list((queue_root / "blocked").glob("*.json*"))
    assert len(blocked) == 1
    payload = json.loads(blocked[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_qit_szilard_record_translation_lane.py"
    assert payload["blocked_reason"] == "stage_gate_blocked"
    assert exploratory.exists()


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


def test_queue_claim_stage_gate_sees_engine_qit_and_nonclassical_tokens() -> None:
    module = _load_module(
        "queue_claim_stage_token_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )

    assert module._stage_gate_claim_for_sim("sim_engine_smoke.py") == "scientific_coupling"
    assert module._stage_gate_claim_for_sim("sim_qit_smoke.py") == "scientific_coupling"
    assert module._stage_gate_claim_for_sim("sim_mega_smoke.py") == "scientific_coupling"
    assert module._stage_gate_claim_for_sim("sim_nonclassical_smoke.py") == "scientific_coupling"


def test_queue_claim_does_not_stage_gate_demoted_partial_trace_baseline() -> None:
    module = _load_module(
        "queue_claim_partial_trace_demotion_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )

    sim = "system_v4/probes/sim_partial_trace_classical.py"

    assert module._plan_stage_from_sim_path(sim) == "early_core"
    assert module._stage_gate_claim_for_sim(sim) is None


def test_queue_claim_does_not_stage_gate_nonpromotable_tool_lego_fit(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "queue_claim_tool_lego_fit_bypass_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    sim = "system_v4/probes/sim_bridge_tool_fit_probe.py"
    (results / "sim_bridge_tool_fit_probe_results.json").write_text(
        json.dumps(
            {
                "classification": "tool_lego_fit_probe",
                "promotion_allowed": False,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)

    assert module._stage_gate_claim_for_sim("system_v4/probes/sim_bridge_probe.py") == "scientific_coupling"
    assert module._stage_gate_claim_for_sim(sim) is None


def test_queue_claim_does_not_late_gate_classical_baseline_gram_schmidt() -> None:
    module = _load_module(
        "queue_claim_classical_baseline_token_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )

    sim = "system_v4/probes/classical_baseline_gram_schmidt.py"

    assert module._plan_stage_from_sim_path(sim) == "early_core"
    assert module._stage_gate_claim_for_sim(sim) is None
    assert module._stage_gate_claim_for_sim("system_v4/probes/sim_schmidt_decomposition_classical.py") == "default_late_stage"


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


def test_autonomous_reseed_loop_blocks_stage_gated_enqueue() -> None:
    text = (REPO_ROOT / "scripts" / "autonomous_reseed_loop.sh").read_text(encoding="utf-8")
    assert "stage_gate_claim_for_sim()" in text
    assert "stage_gate_allows_sim" in text
    assert 'scripts/stage_gate.py --claim "$claim"' in text
    assert "stage gate blocked enqueue" in text
    assert "classical_baseline_*) echo \"early_core\"; return 0 ;;" in text
    assert "classical_baseline_*) return 1 ;;" in text


def test_overnight_two_runner_blocks_stage_gated_claims() -> None:
    text = (REPO_ROOT / "scripts" / "overnight_two_runner.sh").read_text(encoding="utf-8")
    assert "stage_gate_claim_for_sim()" in text
    assert 'scripts/stage_gate.py" --claim "$claim"' in text
    assert "stage_gate_blocked" in text
    assert "QUEUE_CLAIM\" block" in text
    assert "classical_baseline_*) return 1 ;;" in text


def test_overnight_two_runner_blocks_semantic_claim_names_before_execution() -> None:
    text = (REPO_ROOT / "scripts" / "overnight_two_runner.sh").read_text(encoding="utf-8")
    guard_idx = text.index("direct_sim_semantic_guard.py")
    admission_idx = text.index('if [ "$STRICT_WIZARD_QUEUE_ADMISSION" = "1" ]; then', guard_idx)
    run_idx = text.index('run_sim_with_timeout "$sim" "$artifact"')
    assert guard_idx < admission_idx < run_idx
    assert "semantic_name_blocked" in text
    assert '--name "$(basename "$sim" .py)"' in text


def test_parallel_runner_has_helper_and_admission_preflight() -> None:
    text = (REPO_ROOT / "scripts" / "overnight_two_runner.sh").read_text(encoding="utf-8")
    assert "helper_process_preflight()" in text
    assert "helper_process_audit.py\" --strict" in text
    assert "admission_bypass_preflight()" in text
    assert "STRICT_RECEIPT_ADMISSION" in text
    assert "STRICT_WIZARD_QUEUE_ADMISSION" in text


def test_helper_process_audit_ignores_removed_browser_mcp_config(tmp_path) -> None:
    module = _load_module(
        "helper_process_audit_removed_browser_config_under_test",
        REPO_ROOT / "scripts" / "helper_process_audit.py",
    )
    config = tmp_path / "config.toml"
    config.write_text(
        '[mcp_servers.browser]\ncommand = "npx"\nargs = ["removed-browser-mcp"]\n',
        encoding="utf-8",
    )

    report = module.audit_mcp_config(config)

    assert report["findings"] == []


def test_helper_process_audit_allows_no_browser_mcp_config(tmp_path) -> None:
    module = _load_module(
        "helper_process_audit_no_browser_config_under_test",
        REPO_ROOT / "scripts" / "helper_process_audit.py",
    )
    config = tmp_path / "config.toml"
    config.write_text(
        '[mcp_servers.omx_state]\ncommand = "node"\nargs = ["state-server.js"]\n',
        encoding="utf-8",
    )

    report = module.audit_mcp_config(config)

    assert report["findings"] == []
    assert report["parse_error"] is None


def test_qit_admission_rehearsal_rejects_non_tmp_out_dir(tmp_path) -> None:
    module = _load_module(
        "qit_admission_rehearsal_out_dir_guard_under_test",
        REPO_ROOT / "scripts" / "qit_admission_rehearsal.py",
    )

    with pytest.raises(ValueError, match="out_dir_not_under_tmp_codex_ratchet_prefix"):
        module.disposable_out_dir(tmp_path / "not_disposable")


def test_qit_admission_rehearsal_allows_tmp_codex_ratchet_out_dir() -> None:
    module = _load_module(
        "qit_admission_rehearsal_safe_out_dir_under_test",
        REPO_ROOT / "scripts" / "qit_admission_rehearsal.py",
    )

    out_dir = module.disposable_out_dir(Path("/tmp/codex_ratchet_safe_rehearsal/nested"))

    assert str(out_dir).startswith(str(Path("/tmp").resolve() / "codex_ratchet_safe_rehearsal"))


def test_makefile_exposes_parallel_runner_targets() -> None:
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "parallel-runner-dry:" in text
    assert "parallel-runner:" in text
    assert "overnight_two_runner.sh --minutes" in text
    assert "runner-preflight" in text


def test_runner_queue_preflight_blocks_live_default_queue_when_stage_gate_closed(tmp_path) -> None:
    module = _load_module(
        "runner_queue_preflight_under_test",
        REPO_ROOT / "scripts" / "runner_queue_preflight.py",
    )
    repo = tmp_path / "repo"
    ops = repo / "system_v5" / "ops"
    ops.mkdir(parents=True)
    (ops / "stage_gate.json").write_text(
        json.dumps({"active_stage": "lego", "allow_default_queue_late_stage": False}),
        encoding="utf-8",
    )
    (ops / "queue_default.txt").write_text(
        "# comment\nsim_engine_default_leak\n\n",
        encoding="utf-8",
    )

    report = module.audit(root=repo)

    assert report["all_pass"] is False
    assert report["blocked_default_queue_count"] == 1
    assert report["findings"][0]["kind"] == "default_queue_late_stage_blocked"


def test_runner_queue_preflight_blocks_late_rows_in_priority_queues(tmp_path) -> None:
    module = _load_module(
        "runner_queue_preflight_priority_under_test",
        REPO_ROOT / "scripts" / "runner_queue_preflight.py",
    )
    repo = tmp_path / "repo"
    ops = repo / "system_v5" / "ops"
    ops.mkdir(parents=True)
    (ops / "stage_gate.json").write_text(
        json.dumps({"active_stage": "lego", "allow_default_queue_late_stage": False}),
        encoding="utf-8",
    )
    (ops / "queue_tier_a.txt").write_text("sim_coupling_pairwise_probe\n", encoding="utf-8")

    report = module.audit(root=repo)

    assert report["all_pass"] is False
    assert report["blocked_stage_gate_queue_count"] == 1
    assert report["findings"][0]["queue"] == "system_v5/ops/queue_tier_a.txt"
    assert report["findings"][0]["claim"] == "scientific_coupling"


def test_runner_queue_preflight_allows_classical_baseline_gram_schmidt(tmp_path) -> None:
    module = _load_module(
        "runner_queue_preflight_classical_baseline_under_test",
        REPO_ROOT / "scripts" / "runner_queue_preflight.py",
    )
    repo = tmp_path / "repo"
    ops = repo / "system_v5" / "ops"
    ops.mkdir(parents=True)
    (ops / "stage_gate.json").write_text(
        json.dumps({"active_stage": "lego", "allow_default_queue_late_stage": False}),
        encoding="utf-8",
    )
    (ops / "queue_default.txt").write_text(
        "system_v4/probes/classical_baseline_gram_schmidt.py\n",
        encoding="utf-8",
    )
    (ops / "queue_tier_a.txt").write_text(
        "system_v4/probes/classical_baseline_gram_schmidt.py\n",
        encoding="utf-8",
    )

    report = module.audit(root=repo)

    assert report["all_pass"] is True


def test_runner_queue_preflight_blocks_nonempty_atomic_claims(tmp_path) -> None:
    module = _load_module(
        "runner_queue_preflight_atomic_claims_under_test",
        REPO_ROOT / "scripts" / "runner_queue_preflight.py",
    )
    repo = tmp_path / "repo"
    ops = repo / "system_v5" / "ops"
    ops.mkdir(parents=True)
    (ops / "stage_gate.json").write_text(
        json.dumps({"active_stage": "lego", "allow_default_queue_late_stage": False}),
        encoding="utf-8",
    )
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    claimed = queue_root / "claimed"
    blocked = queue_root / "blocked"
    done = queue_root / "done"
    claimed.mkdir(parents=True)
    blocked.mkdir(parents=True)
    done.mkdir(parents=True)
    claimed_at = 100.0
    (claimed / "abc123.json.0.host.worker").write_text(
        json.dumps({"sim_path": "system_v4/probes/sim_probe.py", "claimed_at": claimed_at}),
        encoding="utf-8",
    )
    (blocked / "blocked.json").write_text("{}", encoding="utf-8")
    (done / "done.json").write_text("{}", encoding="utf-8")
    (queue_root / ".DS_Store").write_text("junk", encoding="utf-8")
    (done / ".DS_Store").write_text("junk", encoding="utf-8")

    now = claimed_at + module.CLAIM_RECONCILE_SAFETY_SECONDS - 60.0
    report = module.audit(root=repo, now=now)

    assert report["all_pass"] is False
    assert report["atomic_queue_counts"] == {"claimed": 1, "blocked": 1, "done": 1}
    assert report["atomic_queue_junk_counts"] == {
        "root": 1,
        "lane_A": 0,
        "lane_B": 0,
        "claimed": 0,
        "blocked": 0,
        "done": 1,
    }
    assert report["findings"][0]["kind"] == "atomic_claimed_queue_not_empty"
    assert report["findings"][0]["count"] == 1
    safety = report["findings"][0]["claim_safety"]
    assert safety["count"] == 1
    assert safety["safety_window_seconds"] == 72 * 60 * 60
    assert safety["oldest_claimed_at_utc"] == "1970-01-01T00:01:40+00:00"
    assert safety["newest_claimed_at_utc"] == "1970-01-01T00:01:40+00:00"
    assert safety["safe_to_reconcile_after_utc"] == "1970-01-04T00:01:40+00:00"
    assert safety["seconds_until_safe_to_reconcile"] == 60.0
    assert safety["all_claims_past_safety_window"] is False
    assert safety["pid_summary"]["with_pid"] == 1
    assert safety["oldest_samples"][0]["timestamp_source"] == "payload.claimed_at"
    assert report["blocked_default_queue_count"] == 0
    assert report["blocked_stage_gate_queue_count"] == 0
    assert module.claim_for_row("system_v4/probes/classical_baseline_gram_schmidt.py") is None


def test_runner_preflight_runs_queue_stage_gate_audit() -> None:
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    assert "scripts/runner_queue_preflight.py" in text


def test_wizard_autoresearch_loop_preserves_sim_boundaries() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")
    assert "accepted QIT/engine evidence only from controller-read canonical artifacts" in text
    assert "runner_deferred_receipt" in text
    assert "\"authorization_status\": \"not_requested\"" in text
    assert "\"outcome_status\": \"not_executed\"" in text
    assert "authorized_deferred" in text
    assert "runner_taxonomy_disagreements_need_packet_or_taxonomy_reconcile" in text
    assert "opus_audit" in text
    assert "premortem.json" in text
    assert "helper_process_audit.py" in text


def test_wizard_autoresearch_loop_writes_real_qit_evidence_index() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_evidence_index_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")

    assert module.EVIDENCE_INDEX == REPO_ROOT / "system_v5" / "evidence" / "qit_engine_evidence_index.json"
    assert "scripts/qit_engine_evidence_index.py" in text
    assert "qit_index_write.out" in text


def test_wizard_autoresearch_make_target_routes_out_dir_qit_index_to_tmp() -> None:
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")

    assert "$(if $(OUT_DIR),--out-dir $(OUT_DIR),)" in text
    assert "$(if $(OUT_DIR),--evidence-index-out $(OUT_DIR)/qit_engine_evidence_index.json,)" in text


def test_wizard_autoresearch_dry_target_is_disposable_preflight_only() -> None:
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    dry_block = text.split("wizard-autoresearch-loop-dry:", 1)[1].split("\n\n", 1)[0]

    assert "OUT_DIR=$(or $(OUT_DIR),/tmp/codex_ratchet_wizard_autoresearch_dry)" in dry_block
    assert "SKIP_WIZARD_MATRIX=1" in dry_block
    assert "RUN_RUNNER=1" in dry_block
    assert "LANE_A_PARALLEL=$(or $(LANE_A_PARALLEL),2)" in dry_block
    assert "LANE_B_PARALLEL=$(or $(LANE_B_PARALLEL),4)" in dry_block


def test_qit_admission_rehearsal_make_target_is_tmp_only() -> None:
    text = (REPO_ROOT / "Makefile").read_text(encoding="utf-8")
    block = text.split("qit-admission-rehearsal:", 1)[1].split("\n\n", 1)[0]

    assert "scripts/qit_admission_rehearsal.py" in block
    assert "--basename $(BASENAME)" in block
    assert "--result $(RESULT)" in block
    assert "$(if $(FUNCTION_SURFACE),--function-surface $(FUNCTION_SURFACE),)" in block
    assert "$(if $(OUT_DIR),--out-dir $(OUT_DIR),)" in block
    assert "system_v4/probes/a2_state/sim_results" not in block


def test_qit_admission_rehearsal_script_accepts_temp_canonical_shape(tmp_path) -> None:
    result = tmp_path / "sim_qit_probe_results.json"
    result.write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "all_pass": True,
                "all_passed": True,
                "TOOL_MANIFEST": {"pytorch": {"tried": True, "used": True, "reason": "fixture"}},
                "TOOL_INTEGRATION_DEPTH": {"pytorch": "load_bearing"},
                "tool_manifest": {"pytorch": {"tried": True, "used": True, "reason": "fixture"}},
                "tool_integration_depth": {"pytorch": "load_bearing"},
                "positive": {"passed": True, "function_surface": "pytorch.linalg.eigvalsh"},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no bridge promotion", "no axis promotion", "no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    source = tmp_path / "sim_qit_probe.py"
    source.write_text("# fixture\n", encoding="utf-8")
    out_dir = Path("/tmp") / f"codex_ratchet_pytest_rehearsal_{tmp_path.name}_canonical"

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "qit_admission_rehearsal.py"),
            "--basename",
            "sim_qit_probe",
            "--result",
            str(result),
            "--sim-path",
            str(source),
            "--function-surface",
            "pytorch.linalg.eigvalsh",
            "--out-dir",
            str(out_dir),
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout[-4000:]
    report = json.loads(proc.stdout)
    assert report["ok"] is True
    assert report["accepted"] == 1
    assert report["admitted_micro_entries"] == 1
    assert report["operational_status"] == "has_accepted_qit_entry"
    assert report["receipt_validation"]["returncode"] == 0
    assert report["admission_validation"]["returncode"] == 0
    assert report["index_run"]["returncode"] == 0
    admission = json.loads(Path(report["admission"]).read_text(encoding="utf-8"))
    assert admission["packet_contract"]["tool_target"] == "pytorch"
    assert admission["packet_contract"]["function_surface"] == "pytorch.linalg.eigvalsh"
    assert admission["packet_contract"]["promotion_boundary"] == "no promotion beyond tool_micro without a later admitted packet"


def test_qit_admission_rehearsal_derives_nested_positive_function_surface(tmp_path) -> None:
    result = tmp_path / "sim_qit_probe_results.json"
    result.write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "all_pass": True,
                "all_passed": True,
                "tool_manifest": {"pytorch": {"tried": True, "used": True, "reason": "fixture"}},
                "tool_integration_depth": {"pytorch": "load_bearing"},
                "positive": {"P_entropy": {"passed": True, "function_surface": "torch.linalg.eigvalsh"}},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no bridge promotion", "no axis promotion", "no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    source = tmp_path / "sim_qit_probe.py"
    source.write_text("# fixture\n", encoding="utf-8")
    out_dir = Path("/tmp") / f"codex_ratchet_pytest_rehearsal_{tmp_path.name}_nested"

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "qit_admission_rehearsal.py"),
            "--basename",
            "sim_qit_probe",
            "--result",
            str(result),
            "--sim-path",
            str(source),
            "--out-dir",
            str(out_dir),
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout[-4000:]
    report = json.loads(proc.stdout)
    admission = json.loads(Path(report["admission"]).read_text(encoding="utf-8"))
    assert admission["packet_contract"]["function_surface"] == "torch.linalg.eigvalsh"
    assert report["accepted"] == 1


def test_wizard_autoresearch_dry_loop_writes_numbered_iteration_receipts(tmp_path) -> None:
    out_dir = tmp_path / "dry_loop"
    evidence_index = out_dir / "qit_engine_evidence_index.json"

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py"),
            "--iterations",
            "2",
            "--run-tag",
            "pytest-multi-iteration",
            "--out-dir",
            str(out_dir),
            "--evidence-index-out",
            str(evidence_index),
            "--run-runner",
            "--runner-minutes",
            "1",
            "--lane-a-parallel",
            "2",
            "--lane-b-parallel",
            "4",
            "--skip-wizard-matrix",
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
        timeout=60,
    )

    assert proc.returncode == 0, proc.stdout[-4000:]
    manifest = json.loads((out_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "wizard_autoresearch_run_manifest"
    assert manifest["schema_version"] == 1
    assert manifest["run_status"] == "complete"
    datetime.fromisoformat(manifest["run_started_at"])
    datetime.fromisoformat(manifest["manifest_updated_at"])
    assert manifest["iterations_requested"] == 2
    assert manifest["iterations_completed"] == 2
    assert manifest["evidence_index"] == str(evidence_index)
    assert manifest["run_mode"] == {
        "matrix_enabled": False,
        "gemini_requested": False,
        "haiku_requested": False,
        "runner_requested": True,
    }
    assert manifest["run_config"] == {
        "runner_minutes": 1,
        "lane_a_parallel": 2,
        "lane_b_parallel": 4,
        "opus_audit_requested": False,
        "external_council_receipts": "",
        "evidence_index_out": str(evidence_index),
    }
    assert "--iterations" in manifest["argv"]
    assert "--skip-wizard-matrix" in manifest["argv"]
    expected_argv_hash = hashlib.sha256(
        json.dumps(manifest["argv"], separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    assert manifest["argv_sha256"] == expected_argv_hash
    assert manifest["artifact_status"]["status"] == "complete"
    assert manifest["artifact_status"]["checked_paths"] == 12
    assert manifest["artifact_status"]["missing_paths"] == 0
    expected_next_required_step = manifest["admission_summary"]["next_required_step"]
    assert expected_next_required_step in {
        "rerun_repaired_source_under_canonical_micro_result_surface",
        "create_or_repair_wizard_sim_admission",
        "run_parallel_admitted_workers",
        "repair_decision_or_runner_blockers",
    }
    expected_next_action_by_step = {
        "rerun_repaired_source_under_canonical_micro_result_surface": "rerun_repaired_source_under_canonical_micro_result_surface",
        "create_or_repair_wizard_sim_admission": "create_or_repair_wizard_sim_admission",
        "run_parallel_admitted_workers": "runner_launch_allowed",
        "repair_decision_or_runner_blockers": "repair_runner_launch_blockers",
    }
    expected_next_action = expected_next_action_by_step[expected_next_required_step]
    assert manifest["overall_readiness"]["next_required_step"] == expected_next_required_step
    assert manifest["overall_readiness"]["components"]["artifact_status"] == "complete"
    assert manifest["overall_readiness"]["components"]["claim_boundary_status"] == "no_claims_promoted"
    assert manifest["final_blockers"] in ([], ["accepted_qit_engine_evidence_zero"])
    accepted_qit_entries = manifest["admission_summary"]["accepted_qit_entries"]
    assert manifest["run_classification"] in {"blocked", "complete_no_blockers", "runner_launch_allowed"}
    assert manifest["next_action"] == expected_next_action
    assert manifest["controller_consistency"] == {
        "next_action_matches_admission": True,
        "next_action": expected_next_action,
        "admission_next_required_step": expected_next_required_step,
        "expected_next_action": (
            None if expected_next_required_step == "repair_decision_or_runner_blockers" else expected_next_action
        ),
    }
    assert manifest["runner_summary"]["requested"] is True
    assert manifest["runner_summary"]["launch_allowed"] is manifest["admission_summary"]["runner_launch_allowed"]
    if manifest["runner_summary"]["launch_allowed"]:
        assert manifest["runner_summary"]["status"] == "allowed"
        assert manifest["runner_summary"]["next_required_step"] == "run_parallel_admitted_workers"
        assert manifest["runner_summary"]["launch_blockers"] == []
    elif accepted_qit_entries:
        assert manifest["runner_summary"]["status"] == "authorized_deferred"
        assert manifest["runner_summary"]["next_required_step"] == "repair_runner_launch_blockers"
    else:
        assert manifest["runner_summary"]["status"] == "authorized_deferred"
        assert manifest["runner_summary"]["next_required_step"] == "admit_or_repair_micro_qit_evidence"
        assert "accepted_qit_engine_evidence_zero" in manifest["runner_summary"]["launch_blockers"]
    assert manifest["admission_summary"]["status"] in {
        "blocked_no_accepted_qit_entries",
        "blocked",
        "runner_launch_allowed",
    }
    assert manifest["admission_summary"]["next_required_step"] == expected_next_required_step
    assert manifest["admission_summary"]["active_stage"] == "lego"
    assert manifest["admission_summary"]["stage_gate_all_pass"] is True
    assert "tool_micro" in manifest["admission_summary"]["allowed_claims"]
    assert "bridge" in manifest["admission_summary"]["blocked_claims"]
    assert manifest["admission_summary"]["qit_operational_status"] in {
        "blocked_no_accepted_qit_entries",
        "has_accepted_qit_entry",
    }
    assert accepted_qit_entries >= 0
    assert manifest["admission_summary"]["out_of_scope_qit_signal_result_count"] >= 1
    assert manifest["admission_summary"]["out_of_scope_qit_scan_status"] == "out_of_scope_qit_like_results_present"
    triage_counts = manifest["admission_summary"]["out_of_scope_qit_triage_bucket_counts"]
    if accepted_qit_entries:
        assert triage_counts["already_admitted_duplicate_reference"] >= 1
        assert manifest["admission_summary"]["out_of_scope_qit_provisional_target_count"] == 0
    else:
        assert triage_counts["source_bound_repaired_source_rerun_candidate"] >= 1
        assert manifest["admission_summary"]["out_of_scope_qit_provisional_target_count"] >= 1
        assert manifest["admission_summary"]["out_of_scope_qit_first_provisional_target"]["next_action"] == (
            "rerun_repaired_source_under_canonical_micro_result_surface"
        )
    if expected_next_required_step == "create_or_repair_wizard_sim_admission":
        assert manifest["admission_summary"]["next_acceptance_target_count"] >= 1
        assert manifest["admission_summary"]["first_next_acceptance_target"]["next_action"] == (
            "create_or_repair_wizard_sim_admission"
        )
    if accepted_qit_entries:
        assert manifest["admission_summary"]["canonical_micro_rerun_command"] is None
        assert manifest["admission_summary"]["tmp_admission_rehearsal_command"] is None
    else:
        assert manifest["admission_summary"]["canonical_micro_rerun_command"] == [
            "env",
            "SIM_RESULTS_DIR=system_v4/probes/a2_state/sim_results",
            "NUMBA_CACHE_DIR=/tmp/codex-numba",
            "MPLCONFIGDIR=/tmp/codex-mpl",
            "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "system_v4/probes/sim_weyl_holo_symplectic_topology_variants.py",
        ]
        assert manifest["admission_summary"]["tmp_admission_rehearsal_command"] == [
            "make",
            "qit-admission-rehearsal",
            "BASENAME=sim_weyl_holo_symplectic_topology_variants",
            "RESULT=system_v4/probes/a2_state/sim_results/sim_weyl_holo_symplectic_topology_variants_results.json",
            "SIM_PATH=system_v4/probes/sim_weyl_holo_symplectic_topology_variants.py",
            "OUT_DIR=/tmp/codex_ratchet_qit_admission_rehearsal_sim_weyl_holo_symplectic_topology_variants",
        ]
    assert manifest["admission_summary"]["runner_launch_blockers"] == manifest["runner_summary"]["launch_blockers"]
    if accepted_qit_entries:
        assert "accepted_qit_engine_evidence_zero" not in manifest["admission_summary"]["runner_launch_blockers"]
        assert manifest["admission_summary"]["decision_blockers"] == []
    else:
        assert "accepted_qit_engine_evidence_zero" in manifest["admission_summary"]["runner_launch_blockers"]
        assert manifest["admission_summary"]["decision_blockers"] == ["accepted_qit_engine_evidence_zero"]
    assert manifest["claim_boundary_summary"]["claim_boundary_status"] == "no_claims_promoted"
    assert manifest["claim_boundary_summary"]["promoted_claims"] == []
    assert manifest["claim_boundary_summary"]["promoted_count"] == 0
    assert "tool_micro" in manifest["claim_boundary_summary"]["allowed_claims"]
    assert manifest["claim_boundary_summary"]["late_stage_claims_blocked"] == [
        "bridge",
        "axis",
        "engine",
        "scientific_coupling",
        "tier_d",
    ]
    assert manifest["matrix_summary"]["latest_route_count"] == 0
    assert manifest["matrix_summary"]["status"] == "not_attempted"
    assert manifest["matrix_summary"]["latest_all_accepted"] is None
    assert manifest["matrix_summary"]["latest_routes"] == {}
    assert manifest["matrix_summary"]["completed_count"] == 2
    assert manifest["matrix_summary"]["attempted_count"] == 0
    assert manifest["matrix_summary"]["skipped_count"] == 2
    assert manifest["matrix_summary"]["failed_iterations"] == []
    assert manifest["preflight_summary"]["status"] == ("passed" if all(item["preflight_all_pass"] for item in manifest["iterations"]) else "failed")
    assert manifest["preflight_summary"]["completed_count"] == 2
    assert manifest["preflight_summary"]["latest_all_pass"] == manifest["iterations"][-1]["preflight_all_pass"]
    assert manifest["preflight_summary"]["all_completed_pass"] == all(item["preflight_all_pass"] for item in manifest["iterations"])
    assert manifest["preflight_summary"]["failed_iterations"] == [
        item["iteration"] for item in manifest["iterations"] if not item["preflight_all_pass"]
    ]
    assert manifest["latest_iteration_summary"]["iteration"] == 2
    assert manifest["latest_iteration_summary"]["blockers"] in ([], ["accepted_qit_engine_evidence_zero"])
    assert manifest["latest_iteration_summary"]["preflight_all_pass"] == manifest["iterations"][-1]["preflight_all_pass"]
    assert isinstance(manifest["latest_iteration_summary"]["goal_exit_eligible"], bool)
    assert isinstance(manifest["latest_iteration_summary"]["runner_launch_allowed"], bool)
    assert manifest["latest_iteration_summary"]["stage_gate_summary"]["active_stage"] == "lego"
    assert manifest["latest_iteration_summary"]["qit_evidence_summary"]["summary"]["accepted"] >= 0
    assert manifest["latest_stage_gate_summary"]["active_stage"] == "lego"
    assert manifest["latest_qit_evidence_summary"]["summary"]["accepted"] >= 0
    assert manifest["latest_helper_process_summary"] == manifest["latest_iteration_summary"]["helper_process_summary"]
    for iteration in (1, 2):
        goal_loop = json.loads((out_dir / f"ralph_goal_loop_{iteration:02d}.json").read_text(encoding="utf-8"))
        council = json.loads((out_dir / f"wizard_council_receipt_{iteration:02d}.json").read_text(encoding="utf-8"))
        preflight = json.loads((out_dir / f"preflight_receipts_{iteration:02d}.json").read_text(encoding="utf-8"))
        manifest_item = manifest["iterations"][iteration - 1]

        assert manifest_item["iteration"] == iteration
        datetime.fromisoformat(manifest_item["completed_at"])
        assert manifest_item["preflight_receipt"] == str(out_dir / f"preflight_receipts_{iteration:02d}.json")
        assert manifest_item["council_receipt"] == str(out_dir / f"wizard_council_receipt_{iteration:02d}.json")
        assert manifest_item["goal_loop_receipt"] == str(out_dir / f"ralph_goal_loop_{iteration:02d}.json")
        assert manifest_item["premortem"] == str(out_dir / f"premortem_{iteration:02d}.json")
        assert manifest_item["qit_index_stdout"] == str(out_dir / f"qit_index_write_{iteration:02d}.out")
        assert manifest_item["qit_evidence_summary"]["operational_status"] in {
            "blocked_no_accepted_qit_entries",
            "has_accepted_qit_entry",
        }
        assert manifest_item["qit_evidence_summary"]["status"] in {
            "blocked_no_accepted_qit_entries",
            "has_accepted_qit_entry",
        }
        assert manifest_item["qit_evidence_summary"]["status_reason"] in {
            "no_qit_signal_results_indexed",
            "qit_entries_blocked",
            "accepted_qit_entries_present",
        }
        assert manifest_item["qit_evidence_summary"]["scanned_result_count"] >= 1
        assert manifest_item["qit_evidence_summary"]["qit_signal_result_count"] >= 0
        assert "qit" in manifest_item["qit_evidence_summary"]["qit_signal_filter"]["tokens"]
        assert "claim_ceiling" in manifest_item["qit_evidence_summary"]["qit_signal_filter"]["fields"]
        assert len(manifest_item["qit_evidence_summary"]["scan_sample"]["scanned_result_files"]) >= 1
        assert isinstance(manifest_item["qit_evidence_summary"]["scan_sample"]["qit_signal_result_files"], list)
        assert manifest_item["qit_evidence_summary"]["out_of_scope_qit_result_scan"]["status"] in {
            "out_of_scope_qit_like_results_present",
            "no_out_of_scope_qit_like_results",
        }
        if manifest_item["qit_evidence_summary"]["qit_signal_result_count"] == 0:
            assert manifest_item["qit_evidence_summary"]["out_of_scope_qit_result_scan"]["external_qit_signal_count"] >= 1
        else:
            assert manifest_item["qit_evidence_summary"]["out_of_scope_qit_result_scan"]["external_qit_signal_count"] >= 0
        assert manifest_item["qit_evidence_summary"]["out_of_scope_qit_result_scan"]["admission_boundary"] == "diagnostic_only_not_accepted_evidence"
        if manifest_item["qit_evidence_summary"]["qit_signal_result_count"] == 0:
            assert manifest_item["qit_evidence_summary"]["out_of_scope_qit_triage_summary"]["bucket_counts"][
                "source_bound_repaired_source_rerun_candidate"
            ] >= 1
        else:
            assert manifest_item["qit_evidence_summary"]["next_acceptance_target_count"] >= 0
        assert manifest_item["qit_evidence_summary"]["summary"]["accepted"] >= 0
        assert manifest_item["qit_evidence_summary"]["parse_error"] is False
        assert manifest_item["stage_gate_stdout"] == str(out_dir / f"stage_gate_{iteration:02d}.out")
        assert manifest_item["stage_gate_summary"]["active_stage"] == "lego"
        assert manifest_item["stage_gate_summary"]["status"] == "passed"
        assert "tool_micro" in manifest_item["stage_gate_summary"]["allowed_claims"]
        assert "bridge" in manifest_item["stage_gate_summary"]["blocked_claims"]
        assert "axis" in manifest_item["stage_gate_summary"]["blocked_claims"]
        assert "engine" in manifest_item["stage_gate_summary"]["blocked_claims"]
        assert "tier_d" in manifest_item["stage_gate_summary"]["blocked_claims"]
        assert manifest_item["blockers"] in ([], ["accepted_qit_engine_evidence_zero"])
        assert isinstance(manifest_item["goal_exit_eligible"], bool)
        assert isinstance(manifest_item["runner_launch_allowed"], bool)
        assert manifest_item["matrix_route_count"] == 0
        assert manifest_item["matrix_route_summaries"] == {}
        assert manifest_item["matrix_all_accepted"] is None
        assert isinstance(preflight["all_pass"], bool)
        assert preflight["qit_evidence_index"] == str(evidence_index)
        assert preflight["premortem_path"] == str(out_dir / f"premortem_{iteration:02d}.json")
        assert preflight["qit_index_stdout_path"] == str(out_dir / f"qit_index_write_{iteration:02d}.out")
        assert preflight["qit_evidence_summary"]["operational_status"] in {
            "blocked_no_accepted_qit_entries",
            "has_accepted_qit_entry",
        }
        assert preflight["qit_evidence_summary"]["status"] in {
            "blocked_no_accepted_qit_entries",
            "has_accepted_qit_entry",
        }
        assert preflight["qit_evidence_summary"]["status_reason"] in {
            "no_qit_signal_results_indexed",
            "qit_entries_blocked",
            "accepted_qit_entries_present",
        }
        assert preflight["qit_evidence_summary"]["scanned_result_count"] >= 1
        assert preflight["qit_evidence_summary"]["qit_signal_result_count"] >= 0
        assert "qit" in preflight["qit_evidence_summary"]["qit_signal_filter"]["tokens"]
        assert "claim_ceiling" in preflight["qit_evidence_summary"]["qit_signal_filter"]["fields"]
        assert len(preflight["qit_evidence_summary"]["scan_sample"]["scanned_result_files"]) >= 1

        assert isinstance(preflight["qit_evidence_summary"]["scan_sample"]["qit_signal_result_files"], list)
        assert preflight["qit_evidence_summary"]["out_of_scope_qit_result_scan"]["status"] in {
            "out_of_scope_qit_like_results_present",
            "no_out_of_scope_qit_like_results",
        }
        if preflight["qit_evidence_summary"]["qit_signal_result_count"] == 0:
            assert preflight["qit_evidence_summary"]["out_of_scope_qit_result_scan"]["external_qit_signal_count"] >= 1
        else:
            assert preflight["qit_evidence_summary"]["out_of_scope_qit_result_scan"]["external_qit_signal_count"] >= 0
        if preflight["qit_evidence_summary"]["qit_signal_result_count"] == 0:
            assert preflight["qit_evidence_summary"]["out_of_scope_qit_triage_summary"]["provisional_rerun_target_count"] >= 1
        else:
            assert preflight["qit_evidence_summary"]["next_acceptance_target_count"] >= 0
        assert preflight["qit_evidence_summary"]["summary"]["accepted"] >= 0
        assert preflight["stage_gate_stdout_path"] == str(out_dir / f"stage_gate_{iteration:02d}.out")
        assert preflight["qit_index_write"]["returncode"] == 0
        assert preflight["stage_gate"]["returncode"] == 0
        assert preflight["stage_gate_summary"]["active_stage"] == "lego"
        assert preflight["stage_gate_summary"]["status"] == "passed"
        assert preflight["stage_gate_summary"]["parse_error"] is False
        assert preflight["helper_process_summary"]["returncode"] == preflight["helper_process_audit"]["returncode"]
        if preflight["helper_process_audit"]["returncode"] == 0:
            assert preflight["helper_process_summary"]["parse_error"] is False
            assert preflight["helper_process_summary"]["status"] == "passed"
            assert preflight["helper_process_summary"]["helper_process_count"] == 0
            assert preflight["helper_process_summary"]["guard"] == "non_browser_sim_preflight"
            assert manifest_item["helper_process_summary"]["helper_process_count"] == 0
        else:
            assert preflight["helper_process_summary"]["parse_error"] is True
            assert preflight["helper_process_summary"]["status"] == "parse_error"
        assert preflight["helper_process_audit"]["command"][-1] == "--strict"
        assert Path(preflight["premortem_path"]).exists()
        assert Path(preflight["qit_index_stdout_path"]).exists()
        assert Path(preflight["stage_gate_stdout_path"]).exists()
        assert goal_loop["completion_audit"]["preflight_receipt"] == str(out_dir / f"preflight_receipts_{iteration:02d}.json")
        assert isinstance(goal_loop["goal_exit_eligible"], bool)
        assert goal_loop["completion_audit"]["qit_evidence_index"] == str(evidence_index)
        assert goal_loop["completion_audit"]["blockers"] in ([], ["accepted_qit_engine_evidence_zero"])
        assert council["run_mode"] == {
            "matrix_enabled": False,
            "gemini_enabled": False,
            "haiku_enabled": False,
            "matrix_route_count": 0,
            "matrix_all_accepted": False,
        }
        assert council["parent_receipts"]["failure"]["status"] == "skipped"
        assert council["parent_receipts"]["follow_up"]["status"] == "deferred"


def test_wizard_autoresearch_manifest_prefers_admission_target_over_stale_rerun_triage() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_admission_target_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    decision = {
        "blockers": ["accepted_qit_engine_evidence_zero"],
        "runner_launch_blockers": ["accepted_qit_engine_evidence_zero"],
        "runner_launch_allowed": False,
    }
    iteration = {
        "stage_gate_summary": {
            "all_pass": True,
            "active_stage": "lego",
            "allowed_claims": ["tool_micro"],
            "blocked_claims": ["bridge", "axis", "engine", "scientific_coupling", "tier_d"],
        },
        "qit_evidence_summary": {
            "operational_status": "blocked_no_accepted_qit_entries",
            "summary": {
                "accepted": 0,
                "missing_or_invalid_admission": 1,
                "qit_signal_result_count": 1,
            },
            "next_acceptance_targets": [
                {
                    "basename": "sim_weyl_holo_symplectic_topology_variants",
                    "next_action": "create_or_repair_wizard_sim_admission",
                    "result_path": "system_v4/probes/a2_state/sim_results/sim_weyl_holo_symplectic_topology_variants_results.json",
                    "sim_path": "system_v4/probes/sim_weyl_holo_symplectic_topology_variants.py",
                }
            ],
            "first_next_acceptance_target": {
                "basename": "sim_weyl_holo_symplectic_topology_variants",
                "next_action": "create_or_repair_wizard_sim_admission",
            },
            "out_of_scope_qit_result_scan": {
                "status": "out_of_scope_qit_like_results_present",
                "external_qit_signal_count": 39,
            },
            "out_of_scope_qit_triage_summary": {
                "bucket_counts": {"source_bound_repaired_source_rerun_candidate": 1},
                "provisional_rerun_target_count": 1,
                "first_provisional_target": {
                    "name": "sim_weyl_holo_symplectic_topology_variants",
                    "next_action": "rerun_repaired_source_under_canonical_micro_result_surface",
                    "source_path": "system_v4/probes/sim_weyl_holo_symplectic_topology_variants.py",
                },
            },
        },
    }

    assert module.manifest_next_action(decision, [iteration]) == "create_or_repair_wizard_sim_admission"
    admission = module.manifest_admission_summary(decision, iteration)
    assert admission["next_required_step"] == "create_or_repair_wizard_sim_admission"
    assert admission["next_acceptance_target_count"] == 1
    consistency = module.manifest_controller_consistency("create_or_repair_wizard_sim_admission", admission)
    assert consistency["next_action_matches_admission"] is True


def test_wizard_autoresearch_accepted_evidence_without_runner_request_is_ready_not_failed() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_no_runner_ready_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    decision = module.decide_next(
        {"summary": {"runner_taxonomy_disagreement_count": 0}},
        {"accepted": 1, "admitted_micro_entries": 1, "next_acceptance_targets": []},
        [{"returncode": 0}, {"returncode": 0}, {"returncode": 0}],
        run_runner=False,
        parallel_runner_authorized=False,
        opus={"status": "skipped"},
        matrix_receipts={},
    )
    assert decision == {
        "action": "draft_or_repair_packets_parallel",
        "blockers": [],
        "runner_launch_allowed": False,
        "runner_launch_blockers": [],
        "runner_status": "not_requested",
    }

    iteration = {
        "stage_gate_summary": {
            "all_pass": True,
            "active_stage": "lego",
            "allowed_claims": ["tool_micro"],
            "blocked_claims": ["bridge", "axis", "engine", "scientific_coupling", "tier_d"],
        },
        "qit_evidence_summary": {
            "operational_status": "has_accepted_qit_entry",
            "summary": {"accepted": 1, "admitted_micro_entries": 1},
            "next_acceptance_targets": [],
            "out_of_scope_qit_result_scan": {"external_qit_signal_count": 0},
            "out_of_scope_qit_triage_summary": {"bucket_counts": {}, "provisional_rerun_target_count": 0},
        },
    }
    admission = module.manifest_admission_summary(decision, iteration)
    assert admission["status"] == "ready_for_next_micro_step"
    assert admission["next_required_step"] == "continue_next_micro_step"
    consistency = module.manifest_controller_consistency("continue_next_iteration", admission)
    assert consistency["next_action_matches_admission"] is True
    runner = module.manifest_runner_summary(False, decision)
    assert runner["next_required_step"] == "request_runner_when_admissible"


def test_wizard_autoresearch_no_runner_does_not_emit_runner_launch_blockers() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_no_runner_blocker_truth_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    decision = module.decide_next(
        {"summary": {"runner_taxonomy_disagreement_count": 0}},
        {"accepted": 0},
        [{"returncode": 1}],
        run_runner=False,
        parallel_runner_authorized=False,
        opus={"status": "blocked", "returncode": 1},
        matrix_receipts={"manager.route_truth": {"status": "failed"}},
    )

    assert decision["runner_status"] == "not_requested"
    assert decision["runner_launch_allowed"] is False
    assert decision["runner_launch_blockers"] == []
    assert "accepted_qit_engine_evidence_zero" in decision["blockers"]
    assert "opus_audit_failed" in decision["blockers"]
    assert "wizard_matrix_failed:manager.route_truth" in decision["blockers"]
    runner = module.manifest_runner_summary(False, decision)
    assert runner["launch_blockers"] == []
    assert runner["next_required_step"] == "request_runner_when_admissible"


def _run_wizard_autoresearch_receipt_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    run_runner: bool,
    runner_allowed: bool,
    dry_runner: bool = False,
    runner_returncode: int = 0,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    module = _load_module(
        f"wizard_autoresearch_receipt_fixture_{run_runner}_{runner_allowed}",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    out_dir = tmp_path / ("runner_requested" if run_runner else "no_runner")
    evidence_index = out_dir / "qit_engine_evidence_index.json"
    qit_summary = {
        "operational_status": "has_accepted_qit_entry",
        "status": "has_accepted_qit_entry",
        "status_reason": "accepted_qit_entries_present",
        "summary": {
            "accepted": 1,
            "admitted_micro_entries": 1,
            "scanned_result_count": 1,
            "qit_signal_result_count": 1,
        },
        "next_acceptance_targets": [],
        "first_next_acceptance_target": None,
        "out_of_scope_qit_result_scan": {
            "status": "no_out_of_scope_qit_like_results",
            "external_qit_signal_count": 0,
        },
        "out_of_scope_qit_triage_summary": {
            "bucket_counts": {},
            "provisional_rerun_target_count": 0,
            "first_provisional_target": None,
        },
        "qit_signal_filter": {"tokens": ["qit"], "fields": ["claim_ceiling"]},
    }
    stage_summary = {
        "all_pass": True,
        "active_stage": "lego",
        "allowed_claims": ["tool_micro", "tool_lego_fit", "tool_integration_micro", "lego"],
        "blocked_claims": ["bridge", "axis", "engine", "scientific_coupling", "tier_d"],
    }

    def fake_run(command: list[str], *, cwd: Path = module.REPO_ROOT) -> dict[str, object]:
        text = " ".join(command)
        if "qit_engine_evidence_index.py" in text:
            evidence_index.parent.mkdir(parents=True, exist_ok=True)
            evidence_index.write_text(json.dumps(qit_summary), encoding="utf-8")
            return {"command": command, "returncode": 0, "stdout": json.dumps(qit_summary)}
        if "stage_gate.py" in text:
            return {"command": command, "returncode": 0, "stdout": json.dumps(stage_summary)}
        if command[:2] == ["make", "parallel-runner-dry"]:
            return {"command": command, "returncode": runner_returncode, "stdout": "dry runner ok", "status": "allowed"}
        if command[:2] == ["make", "parallel-runner"]:
            return {"command": command, "returncode": runner_returncode, "stdout": "live runner ok", "status": "allowed"}
        return {"command": command, "returncode": 0, "stdout": "{}"}

    def fake_decide_next(*args, **kwargs):
        run_requested = bool(kwargs["run_runner"])
        allowed = bool(run_requested and runner_allowed)
        runner_status = "allowed" if allowed else ("authorized_deferred" if run_requested else "not_requested")
        return {
            "action": "run_parallel_admitted_workers" if allowed else "draft_or_repair_packets_parallel",
            "blockers": [] if allowed or not run_requested else ["fixture_runner_deferred"],
            "runner_launch_allowed": allowed,
            "runner_launch_blockers": [] if allowed or not run_requested else ["fixture_runner_deferred"],
            "runner_status": runner_status,
        }

    argv = [
        "wizard_autoresearch_sim_loop.py",
        "--iterations",
        "1",
        "--run-tag",
        "pytest-runner-receipt",
        "--out-dir",
        str(out_dir),
        "--evidence-index-out",
        str(evidence_index),
        "--skip-wizard-matrix",
    ]
    if run_runner:
        argv.append("--run-runner")
    if dry_runner:
        argv.append("--dry-runner")

    monkeypatch.setattr(module, "run", fake_run)
    monkeypatch.setattr(module, "qit_evidence_summary", lambda path: qit_summary)
    monkeypatch.setattr(module, "evidence_counts", lambda path=None: qit_summary["summary"] | {"next_acceptance_targets": []})
    monkeypatch.setattr(module, "stage_gate_summary", lambda result: stage_summary)
    monkeypatch.setattr(module, "decide_next", fake_decide_next)
    monkeypatch.setattr(sys, "argv", argv)

    assert module.main() == 0
    council = json.loads((out_dir / "wizard_council_receipt_01.json").read_text(encoding="utf-8"))
    manifest = json.loads((out_dir / "run_manifest.json").read_text(encoding="utf-8"))
    decision = council["parent_receipts"]["decision"]["decision"]
    return council, manifest, decision


def test_wizard_autoresearch_no_runner_main_loop_receipt_is_not_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _council, manifest, decision = _run_wizard_autoresearch_receipt_fixture(
        tmp_path,
        monkeypatch,
        run_runner=False,
        runner_allowed=False,
    )

    assert decision["runner_status"] == "not_requested"
    assert decision["runner"] == {
        "authorization_status": "not_requested",
        "outcome_status": "not_executed",
        "execution_mode": "none",
        "dry_run": False,
        "authorized_deferred": False,
        "launch_blockers": [],
    }
    assert manifest["runner_summary"]["requested"] is False
    assert manifest["runner_summary"]["status"] == "not_requested"


def test_wizard_autoresearch_runner_requested_main_loop_receipt_stays_consistent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _council, manifest, decision = _run_wizard_autoresearch_receipt_fixture(
        tmp_path,
        monkeypatch,
        run_runner=True,
        runner_allowed=False,
    )

    assert decision["runner_status"] == "authorized_deferred"
    assert decision["runner"]["authorization_status"] == "authorized_deferred"
    assert decision["runner"]["outcome_status"] == "not_executed"
    assert decision["runner"]["execution_mode"] == "none"
    assert decision["runner"]["dry_run"] is False
    assert decision["runner"]["authorized_deferred"] is True
    assert decision["runner"]["launch_blockers"] == ["fixture_runner_deferred"]
    assert manifest["runner_summary"]["requested"] is True
    assert manifest["runner_summary"]["status"] == "authorized_deferred"


def test_wizard_autoresearch_runner_allowed_main_loop_receipt_marks_runner_allowed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _council, manifest, decision = _run_wizard_autoresearch_receipt_fixture(
        tmp_path,
        monkeypatch,
        run_runner=True,
        runner_allowed=True,
    )

    assert decision["runner_status"] == "allowed"
    assert decision["runner_launch_allowed"] is True
    assert decision["runner"]["authorization_status"] == "permitted"
    assert decision["runner"]["outcome_status"] == "live_run_completed"
    assert decision["runner"]["execution_mode"] == "live"
    assert decision["runner"]["dry_run"] is False
    assert decision["runner"]["returncode"] == 0
    assert decision["runner"]["command"][:2] == ["make", "parallel-runner"]
    assert manifest["runner_summary"]["requested"] is True
    assert manifest["runner_summary"]["status"] == "allowed"


def test_wizard_autoresearch_runner_allowed_main_loop_can_use_dry_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _council, manifest, decision = _run_wizard_autoresearch_receipt_fixture(
        tmp_path,
        monkeypatch,
        run_runner=True,
        runner_allowed=True,
        dry_runner=True,
    )

    assert decision["runner_status"] == "allowed"
    assert decision["runner_launch_allowed"] is True
    assert decision["runner"]["authorization_status"] == "permitted"
    assert decision["runner"]["outcome_status"] == "dry_run_completed"
    assert decision["runner"]["execution_mode"] == "dry_run"
    assert decision["runner"]["dry_run"] is True
    assert decision["runner"]["command"][:2] == ["make", "parallel-runner-dry"]
    assert manifest["runner_summary"]["requested"] is True
    assert manifest["runner_summary"]["status"] == "allowed"


def test_wizard_autoresearch_runner_allowed_main_loop_marks_failed_live_runner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _council, manifest, decision = _run_wizard_autoresearch_receipt_fixture(
        tmp_path,
        monkeypatch,
        run_runner=True,
        runner_allowed=True,
        runner_returncode=2,
    )

    assert decision["runner_status"] == "allowed"
    assert decision["runner_launch_allowed"] is True
    assert decision["runner"]["authorization_status"] == "permitted"
    assert decision["runner"]["execution_mode"] == "live"
    assert decision["runner"]["dry_run"] is False
    assert decision["runner"]["outcome_status"] == "live_run_failed"
    assert decision["runner"]["returncode"] == 2
    assert manifest["runner_summary"]["status"] == "allowed"


def test_wizard_autoresearch_runner_receipt_state_machine_is_enumerated() -> None:
    valid_shapes = [
        {
            "authorization_status": "not_requested",
            "execution_mode": "none",
            "dry_run": False,
            "outcome_status": "not_executed",
        },
        {
            "authorization_status": "authorized_deferred",
            "execution_mode": "none",
            "dry_run": False,
            "outcome_status": "not_executed",
        },
        {
            "authorization_status": "permitted",
            "execution_mode": "dry_run",
            "dry_run": True,
            "outcome_status": "dry_run_completed",
        },
        {
            "authorization_status": "permitted",
            "execution_mode": "dry_run",
            "dry_run": True,
            "outcome_status": "dry_run_failed",
        },
        {
            "authorization_status": "permitted",
            "execution_mode": "live",
            "dry_run": False,
            "outcome_status": "live_run_completed",
        },
        {
            "authorization_status": "permitted",
            "execution_mode": "live",
            "dry_run": False,
            "outcome_status": "live_run_failed",
        },
    ]

    for runner in valid_shapes:
        if runner["execution_mode"] == "none":
            assert runner["dry_run"] is False
            assert runner["outcome_status"] == "not_executed"
            assert runner["authorization_status"] in {"not_requested", "authorized_deferred"}
        elif runner["execution_mode"] == "dry_run":
            assert runner["dry_run"] is True
            assert runner["authorization_status"] == "permitted"
            assert runner["outcome_status"] in {"dry_run_completed", "dry_run_failed"}
        elif runner["execution_mode"] == "live":
            assert runner["dry_run"] is False
            assert runner["authorization_status"] == "permitted"
            assert runner["outcome_status"] in {"live_run_completed", "live_run_failed"}
        else:
            raise AssertionError(f"unexpected execution mode: {runner['execution_mode']}")


def test_wizard_autoresearch_matrix_receipt_without_status_is_invalid_schema(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_matrix_status_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    monkeypatch.setattr(module, "run", lambda command: {"command": command, "returncode": 0, "stdout": ""})
    monkeypatch.setattr(
        module,
        "latest_matrix_receipt",
        lambda route_out: {"receipt_path": str(tmp_path / "matrix_receipt.json"), "counts": {}, "model_family_statuses": {}},
    )

    receipt = module.run_wizard_matrix(
        route="manager.route_truth",
        only_children="manager.lineage_audit",
        prompt="audit",
        out_dir=tmp_path,
        attempt_gemini=False,
        include_haiku=False,
    )

    assert receipt["status"] == "invalid_schema"


def test_wizard_autoresearch_run_manifest_can_checkpoint_in_progress(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_manifest_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    evidence_index = tmp_path / "qit_engine_evidence_index.json"

    path = module.write_run_manifest(
        tmp_path,
        run_tag="pytest-checkpoint",
        run_started_at="2026-05-08T00:00:00+00:00",
        iterations_requested=3,
        evidence_index=evidence_index,
        matrix_enabled=False,
        gemini_requested=False,
        haiku_requested=False,
        runner_requested=True,
        run_config={"runner_minutes": 1, "lane_a_parallel": 2, "lane_b_parallel": 4},
        argv=["wizard_autoresearch_sim_loop.py", "--iterations", "3"],
        latest_decision={"blockers": ["accepted_qit_engine_evidence_zero"], "runner_launch_allowed": False},
        iteration_manifest=[
            {
                "iteration": 1,
                "preflight_receipt": str(tmp_path / "preflight_receipts_01.json"),
                "runner_launch_allowed": False,
                "blockers": ["accepted_qit_engine_evidence_zero"],
            }
        ],
        run_status="in_progress",
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["run_status"] == "in_progress"
    assert not (tmp_path / "run_manifest.json.tmp").exists()
    assert manifest["run_started_at"] == "2026-05-08T00:00:00+00:00"
    datetime.fromisoformat(manifest["manifest_updated_at"])
    assert manifest["iterations_requested"] == 3
    assert manifest["iterations_completed"] == 1
    assert manifest["artifact_status"]["status"] == "missing_artifacts"
    assert manifest["artifact_status"]["missing_paths"] == 1
    assert manifest["artifact_status"]["missing"][0]["field"] == "preflight_receipt"
    assert manifest["overall_readiness"] == {
        "status": "blocked",
        "blockers": ["missing_artifacts", "accepted_qit_engine_evidence_zero"],
        "next_required_step": "admit_or_repair_micro_qit_evidence",
        "runner_launch_allowed": False,
        "components": {
            "artifact_status": "missing_artifacts",
            "admission_status": "blocked_no_accepted_qit_entries",
            "controller_consistent": True,
            "claim_boundary_status": "no_claims_promoted",
        },
    }
    assert manifest["run_config"]["lane_b_parallel"] == 4
    assert manifest["argv"] == ["wizard_autoresearch_sim_loop.py", "--iterations", "3"]
    assert len(manifest["argv_sha256"]) == 64
    assert manifest["final_blockers"] == ["accepted_qit_engine_evidence_zero"]
    assert manifest["run_mode"]["runner_requested"] is True
    assert manifest["iterations"][0]["iteration"] == 1
    assert manifest["controller_consistency"] == {
        "next_action_matches_admission": True,
        "next_action": "repair_or_admit_micro_qit_evidence_before_runner_launch",
        "admission_next_required_step": "admit_or_repair_micro_qit_evidence",
        "expected_next_action": "repair_or_admit_micro_qit_evidence_before_runner_launch",
    }
    assert manifest["admission_summary"] == {
        "status": "blocked_no_accepted_qit_entries",
        "next_required_step": "admit_or_repair_micro_qit_evidence",
        "active_stage": None,
        "stage_gate_all_pass": None,
        "allowed_claims": [],
        "blocked_claims": [],
        "qit_operational_status": None,
        "accepted_qit_entries": None,
        "out_of_scope_qit_signal_result_count": 0,
        "out_of_scope_qit_scan_status": None,
        "out_of_scope_qit_triage_bucket_counts": {},
        "out_of_scope_qit_provisional_target_count": 0,
        "out_of_scope_qit_first_provisional_target": None,
        "next_acceptance_target_count": 0,
        "first_next_acceptance_target": None,
        "canonical_micro_rerun_command": None,
        "tmp_admission_rehearsal_command": None,
        "runner_launch_allowed": False,
        "runner_launch_blockers": [],
        "decision_blockers": ["accepted_qit_engine_evidence_zero"],
    }
    assert manifest["claim_boundary_summary"] == {
        "promoted_claims": [],
        "promoted_count": 0,
        "allowed_claims": [],
        "blocked_claims": [],
        "late_stage_claims_blocked": [],
        "claim_boundary_status": "no_claims_promoted",
    }
    assert manifest["matrix_summary"] == {
        "status": "not_attempted",
        "latest_route_count": 0,
        "latest_all_accepted": None,
        "latest_routes": {},
        "completed_count": 1,
        "attempted_count": 0,
        "skipped_count": 1,
        "failed_iterations": [],
    }


def test_wizard_autoresearch_run_manifest_summarizes_enabled_matrix_routes(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_enabled_matrix_manifest_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    route_summary = {
        "failure.premortem": {
            "status": "accepted",
            "counts": {"accepted_children": 2},
            "model_family_statuses": {"sonnet": "completed", "opus": "completed"},
            "receipt_path": "/tmp/failure/matrix_receipt.json",
        },
        "manager.route_truth": {
            "status": "failed",
            "counts": {"accepted_children": 0},
            "model_family_statuses": {"sonnet": "blocked", "opus": "failed"},
            "receipt_path": "/tmp/manager/matrix_receipt.json",
        },
    }

    path = module.write_run_manifest(
        tmp_path,
        run_tag="pytest-matrix",
        run_started_at="2026-05-08T00:00:00+00:00",
        iterations_requested=2,
        evidence_index=tmp_path / "qit_engine_evidence_index.json",
        matrix_enabled=True,
        gemini_requested=False,
        haiku_requested=False,
        runner_requested=False,
        run_config={},
        argv=["wizard_autoresearch_sim_loop.py"],
        latest_decision={"blockers": ["wizard_matrix_failed:manager.route_truth"], "runner_launch_allowed": False},
        iteration_manifest=[
            {
                "iteration": 1,
                "matrix_route_summaries": {"failure.premortem": {"status": "accepted"}},
                "matrix_all_accepted": True,
            },
            {
                "iteration": 2,
                "matrix_route_summaries": route_summary,
                "matrix_all_accepted": False,
            },
        ],
        run_status="in_progress",
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))

    assert manifest["matrix_summary"]["latest_route_count"] == 2
    assert manifest["matrix_summary"]["status"] == "failed"
    assert manifest["matrix_summary"]["latest_all_accepted"] is False
    assert manifest["matrix_summary"]["attempted_count"] == 2
    assert manifest["matrix_summary"]["skipped_count"] == 0
    assert manifest["matrix_summary"]["failed_iterations"] == [2]
    assert manifest["matrix_summary"]["latest_routes"]["failure.premortem"]["status"] == "accepted"
    assert manifest["matrix_summary"]["latest_routes"]["manager.route_truth"]["status"] == "failed"
    assert manifest["next_action"] == "repair_wizard_matrix_route:manager.route_truth"
    assert manifest["admission_summary"]["status"] == "blocked"
    assert manifest["admission_summary"]["next_required_step"] == "repair_decision_or_runner_blockers"
    assert manifest["admission_summary"]["decision_blockers"] == ["wizard_matrix_failed:manager.route_truth"]
    assert manifest["controller_consistency"] == {
        "next_action_matches_admission": True,
        "next_action": "repair_wizard_matrix_route:manager.route_truth",
        "admission_next_required_step": "repair_decision_or_runner_blockers",
        "expected_next_action": None,
    }
    assert manifest["overall_readiness"] == {
        "status": "blocked",
        "blockers": ["wizard_matrix_failed:manager.route_truth"],
        "next_required_step": "repair_decision_or_runner_blockers",
        "runner_launch_allowed": False,
        "components": {
            "artifact_status": "not_started",
            "admission_status": "blocked",
            "controller_consistent": True,
            "claim_boundary_status": "no_claims_promoted",
        },
    }


def test_wizard_autoresearch_controller_consistency_flags_drift() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_controller_drift_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )

    result = module.manifest_controller_consistency(
        "continue_next_iteration",
        {"next_required_step": "admit_or_repair_micro_qit_evidence"},
    )

    assert result == {
        "next_action_matches_admission": False,
        "next_action": "continue_next_iteration",
        "admission_next_required_step": "admit_or_repair_micro_qit_evidence",
        "expected_next_action": "repair_or_admit_micro_qit_evidence_before_runner_launch",
    }


def test_wizard_autoresearch_run_manifest_can_exist_before_first_iteration(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_initial_manifest_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    evidence_index = tmp_path / "qit_engine_evidence_index.json"

    path = module.write_run_manifest(
        tmp_path,
        run_tag="pytest-start",
        run_started_at="2026-05-08T00:00:00+00:00",
        iterations_requested=5,
        evidence_index=evidence_index,
        matrix_enabled=True,
        gemini_requested=True,
        haiku_requested=False,
        runner_requested=False,
        run_config={},
        argv=[],
        latest_decision={},
        iteration_manifest=[],
        run_status="in_progress",
    )
    manifest = json.loads(path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["run_status"] == "in_progress"
    assert manifest["run_started_at"] == "2026-05-08T00:00:00+00:00"
    datetime.fromisoformat(manifest["manifest_updated_at"])
    assert manifest["iterations_requested"] == 5
    assert manifest["iterations_completed"] == 0
    assert manifest["run_classification"] == "initialized"
    assert manifest["next_action"] == "continue_first_iteration"
    assert manifest["controller_consistency"] == {
        "next_action_matches_admission": True,
        "next_action": "continue_first_iteration",
        "admission_next_required_step": "complete_first_preflight_iteration",
        "expected_next_action": "continue_first_iteration",
    }
    assert manifest["runner_summary"] == {
        "requested": False,
        "launch_allowed": False,
        "status": None,
        "launch_blockers": [],
        "next_required_step": "request_runner_when_admissible",
    }
    assert manifest["preflight_summary"] == {
        "status": "not_started",
        "latest_all_pass": None,
        "all_completed_pass": None,
        "completed_count": 0,
        "failed_iterations": [],
    }
    assert manifest["admission_summary"] == {
        "status": "not_started",
        "next_required_step": "complete_first_preflight_iteration",
        "active_stage": None,
        "stage_gate_all_pass": None,
        "allowed_claims": [],
        "blocked_claims": [],
        "qit_operational_status": None,
        "accepted_qit_entries": None,
        "out_of_scope_qit_signal_result_count": 0,
        "out_of_scope_qit_scan_status": None,
        "out_of_scope_qit_triage_bucket_counts": {},
        "out_of_scope_qit_provisional_target_count": 0,
        "out_of_scope_qit_first_provisional_target": None,
        "next_acceptance_target_count": 0,
        "first_next_acceptance_target": None,
        "canonical_micro_rerun_command": None,
        "tmp_admission_rehearsal_command": None,
        "runner_launch_allowed": False,
        "runner_launch_blockers": [],
        "decision_blockers": [],
    }
    assert manifest["matrix_summary"] == {
        "status": "not_started",
        "latest_route_count": 0,
        "latest_all_accepted": None,
        "latest_routes": {},
        "completed_count": 0,
        "attempted_count": 0,
        "skipped_count": 0,
        "failed_iterations": [],
    }
    assert manifest["latest_iteration_summary"]["iteration"] is None
    assert manifest["latest_iteration_summary"]["blockers"] == []
    assert manifest["latest_stage_gate_summary"] is None
    assert manifest["latest_qit_evidence_summary"] is None
    assert manifest["latest_helper_process_summary"] is None
    assert manifest["artifact_status"]["checked_paths"] == 0
    assert manifest["artifact_status"]["status"] == "not_started"
    assert manifest["artifact_status"]["missing_paths"] == 0
    assert manifest["overall_readiness"] == {
        "status": "not_started",
        "blockers": [],
        "next_required_step": "complete_first_preflight_iteration",
        "runner_launch_allowed": False,
        "components": {
            "artifact_status": "not_started",
            "admission_status": "not_started",
            "controller_consistent": True,
            "claim_boundary_status": "no_claims_promoted",
        },
    }
    assert manifest["final_blockers"] == []
    assert manifest["iterations"] == []
    assert manifest["run_mode"] == {
        "matrix_enabled": True,
        "gemini_requested": True,
        "haiku_requested": False,
        "runner_requested": False,
    }


def test_ralph_goal_loop_surfaces_next_qit_acceptance_targets() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_qit_targets_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    loop = module.build_ralph_goal_loop(
        objective_ref="test",
        objective_text="test objective",
        iteration=1,
        counts={
            "accepted": 0,
            "missing_or_invalid_admission": 1,
            "next_acceptance_targets": [
                {
                    "basename": "sim_qit_probe",
                    "next_action": "create_or_repair_wizard_sim_admission",
                }
            ],
        },
        premortem={"ok": True},
        decision={"blockers": ["accepted_qit_engine_evidence_zero"]},
    )

    strict_item = next(
        item
        for item in loop["prompt_to_artifact_checklist"]
        if item["requirement"] == "strict admission blocks promotion"
    )
    assert strict_item["evidence"]["next_acceptance_targets"][0]["basename"] == "sim_qit_probe"
    assert loop["completion_audit"]["next_acceptance_targets"][0]["next_action"] == "create_or_repair_wizard_sim_admission"


def test_ralph_goal_loop_covers_qit_canonical_artifact_requirement_with_accepted_entry() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_qit_accepted_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    loop = module.build_ralph_goal_loop(
        objective_ref="test",
        objective_text="test objective",
        iteration=1,
        counts={
            "accepted": 1,
            "missing_or_invalid_admission": 38,
            "next_acceptance_targets": [
                {
                    "basename": "sim_next_probe",
                    "next_action": "create_or_repair_wizard_sim_admission",
                }
            ],
        },
        premortem={"ok": True},
        decision={"blockers": ["runner_taxonomy_disagreements_need_packet_or_taxonomy_reconcile"]},
    )

    qit_item = next(
        item
        for item in loop["prompt_to_artifact_checklist"]
        if item["requirement"] == "QIT engine evidence is accepted only from canonical artifacts"
    )
    assert qit_item["status"] == "covered"
    assert "QIT engine evidence is accepted only from canonical artifacts" not in loop["completion_audit"]["uncovered_requirements"]


def test_wizard_autoresearch_loop_evidence_counts_reads_full_index_targets(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_counts_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    index_path = tmp_path / "qit_engine_evidence_index.json"
    index_path.write_text(
        json.dumps(
            {
                "summary": {
                    "accepted": 0,
                    "admitted_micro_entries": 1,
                    "blocked": 1,
                    "quarantine_entries": 1,
                    "candidate_entries": 0,
                    "missing_or_invalid_admission": 1,
                },
                "next_acceptance_targets": [
                    {
                        "basename": "sim_qit_probe",
                        "next_action": "create_or_repair_wizard_sim_admission",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    module.EVIDENCE_INDEX = index_path

    counts = module.evidence_counts()

    assert counts["accepted"] == 0
    assert counts["admitted_micro_entries"] == 1
    assert counts["next_acceptance_targets"][0]["basename"] == "sim_qit_probe"


def test_wizard_autoresearch_loop_runs_three_councils_with_skill_lanes() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")
    assert "write_council_receipts" in text
    assert '"decision"' in text
    assert '"failure"' in text
    assert '"follow_up"' in text
    assert "parent_skill_lanes" in text
    assert "child_skill_lanes" in text
    assert "codex-autoresearch" in text
    assert "premortem" in text
    assert "claude-bridge:opus" in text
    assert "cdo" in text


def test_wizard_autoresearch_loop_records_cdo_scheduler_state() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")
    assert "cdo_scheduler" in text
    assert "turn_count" in text
    assert "total_agents" in text
    assert "next_turn_strategy" in text
    assert "exit_eligible" in text
    assert "final synthesis is blocked until scheduler metrics are met" in text


def test_wizard_autoresearch_loop_records_goal_ralph_loop_state() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")
    assert "build_ralph_goal_loop" in text
    assert "ralph_goal_loop" in text
    assert "run_audit_learn_premortem_harden" in text
    assert "objective_ref" in text
    assert "prompt_to_artifact_checklist" in text
    assert "completion_audit" in text
    assert "goal_exit_eligible" in text


def test_wizard_autoresearch_loop_blocks_failed_opus_audit() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    decision = module.decide_next(
        {
            "summary": {
                "runner_taxonomy_disagreement_count": 0,
                "row_state_counts": {"queue_candidate": 1},
            }
        },
        {"accepted": 1},
        [{"returncode": 0}],
        run_runner=True,
        parallel_runner_authorized=True,
        opus={"status": "blocked", "returncode": 1, "reason": "opus_audit_failed"},
    )

    assert decision["action"] == "draft_or_repair_packets_parallel"
    assert "opus_audit_failed" in decision["blockers"]
    assert "opus_audit_failed" in decision["runner_launch_blockers"]


def test_wizard_autoresearch_loop_taxonomy_blocks_promotion_not_sim_execution() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_runner_gate_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    decision = module.decide_next(
        {
            "summary": {
                "runner_taxonomy_disagreement_count": 7,
                "row_state_counts": {"queue_candidate": 3},
            }
        },
        {"accepted": 1},
        [{"returncode": 0}],
        run_runner=True,
        parallel_runner_authorized=True,
        opus={"status": "skipped"},
    )

    assert "runner_taxonomy_disagreements_need_packet_or_taxonomy_reconcile" in decision["blockers"]
    assert decision["runner_launch_blockers"] == []
    assert decision["runner_launch_allowed"] is True
    assert decision["action"] == "run_parallel_admitted_workers"


def test_ralph_goal_loop_dedupes_failed_opus_blocker() -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_ralph_opus_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )

    loop = module.build_ralph_goal_loop(
        objective_ref="test",
        objective_text="test objective",
        iteration=1,
        opus={"status": "blocked", "returncode": 1},
        decision={"blockers": ["opus_audit_failed"]},
    )

    assert loop["completion_audit"]["blockers"].count("opus_audit_failed") == 1


def test_ralph_goal_loop_persists_decision_counts_and_evidence_index_path(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_ralph_audit_surface_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    evidence_index = tmp_path / "qit_engine_evidence_index.json"
    counts = {
        "accepted": 0,
        "admitted_micro_entries": 0,
        "missing_or_invalid_admission": 0,
        "next_acceptance_targets": [],
    }
    decision = {
        "runner_launch_allowed": False,
        "runner_launch_blockers": ["accepted_qit_engine_evidence_zero"],
        "blockers": ["accepted_qit_engine_evidence_zero"],
    }

    loop = module.build_ralph_goal_loop(
        objective_ref="test",
        objective_text="test objective",
        iteration=1,
        counts=counts,
        decision=decision,
        evidence_index_path=evidence_index,
    )

    audit = loop["completion_audit"]
    assert audit["decision"]["runner_launch_allowed"] is False
    assert audit["qit_evidence_counts"]["accepted"] == 0
    assert audit["qit_evidence_index"] == str(evidence_index)


def test_ralph_goal_loop_can_point_to_preflight_receipt(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_preflight_pointer_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )
    preflight = tmp_path / "preflight_receipts_01.json"

    loop = module.build_ralph_goal_loop(
        objective_ref="test",
        objective_text="test objective",
        iteration=1,
        counts={"accepted": 0},
        decision={"blockers": ["accepted_qit_engine_evidence_zero"]},
        preflight_receipt_path=preflight,
    )

    assert loop["completion_audit"]["preflight_receipt"] == str(preflight)


def test_wizard_autoresearch_loop_writes_preflight_receipt_artifact() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")
    assert "preflight_receipts_" in text
    assert "wizard_autoresearch_preflight_receipts" in text
    assert "helper_process_audit" in text
    assert "qit_index_write" in text


def test_wizard_council_receipt_separates_active_and_disabled_model_lanes(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_lane_truth_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )

    path = module.write_council_receipts(
        tmp_path,
        iteration=1,
        decision={"action": "draft_or_repair_packets_parallel"},
        premortem={"ok": True},
        external={},
        matrix_receipts={"failure.premortem": {"status": "accepted"}},
        gemini_enabled=True,
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))

    assert "claude-bridge:sonnet-high" in receipt["child_skill_lanes"]
    assert "claude-bridge:opus-audit" in receipt["child_skill_lanes"]
    assert "gemini:audit" in receipt["child_skill_lanes"]
    assert "claude-bridge:haiku" not in receipt["child_skill_lanes"]
    assert receipt["disabled_skill_lanes"] == ["claude-bridge:haiku"]
    assert "premortem" in receipt["parent_skill_lanes"]
    assert "claude-bridge" in receipt["parent_skill_lanes"]
    assert receipt["disabled_parent_skill_lanes"] == ["cdo"]
    assert receipt["parent_receipts"]["failure"]["status"] == "completed"
    assert receipt["parent_receipts"]["follow_up"]["status"] == "deferred"
    assert receipt["parent_receipts"]["follow_up"]["evidence_present"] is False
    assert "route_truth_join" in receipt["management_parents"]
    assert "premortem_follow_up_join_gate" in receipt["management_parents"]
    assert receipt["disabled_management_parents"] == []
    assert receipt["run_mode"] == {
        "matrix_enabled": True,
        "gemini_enabled": True,
        "haiku_enabled": False,
        "matrix_route_count": 1,
        "matrix_all_accepted": True,
    }


def test_wizard_council_receipt_completes_followup_only_with_followup_evidence(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_followup_evidence_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )

    path = module.write_council_receipts(
        tmp_path,
        iteration=1,
        decision={"action": "draft_or_repair_packets_parallel"},
        premortem={"ok": True},
        external={},
        matrix_receipts={
            "failure.premortem": {"status": "accepted"},
            "follow_up.compile_gate": {"status": "accepted"},
        },
        gemini_enabled=True,
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))

    assert receipt["parent_receipts"]["follow_up"]["status"] == "completed"
    assert receipt["parent_receipts"]["follow_up"]["evidence_present"] is True


def test_wizard_child_matrix_blocks_accepted_status_on_usefulness_failures() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_child_matrix.py").read_text(encoding="utf-8")

    assert "blocking_failures = blocking_usefulness_failures(groups, formal_completed, active_formal_children)" in text
    assert "launched_families_completed" in text
    assert "route_quality_ok = formal_ok and launched_families_completed and usefulness_ok" in text
    assert "matrix_ok = (route_quality_ok if v4_2_route else core_families_completed and route_quality_ok)" in text
    assert "and not rescore_stale" in text
    assert '"status": "accepted" if matrix_ok else "rescored_stale" if rescore_stale else "partial"' in text


def test_wizard_child_matrix_delegates_expensive_failure_skill_child_to_opus() -> None:
    module = _load_module(
        "wizard_child_matrix_specialist_opus_under_test",
        REPO_ROOT / "scripts" / "wizard_child_matrix.py",
    )
    roles = module.FORMAL_CHILDREN["failure.loophole_auditor"]

    specs = module.asymmetric_model_role_specs(
        route="failure.loophole_auditor",
        roles=roles,
        active_formal_children=roles,
        full_model_council=False,
        sonnet_count=4,
        opus_count=1,
        haiku_count=0,
    )

    assert specs["opus"]["roles"] == ["skill.loophole_auditor"]
    assert specs["opus"]["count"] == 1
    assert "skill.loophole_auditor" not in specs["sonnet"]["roles"]
    assert specs["sonnet"]["count"] == 3


def test_wizard_child_matrix_ignores_redundant_failure_when_formal_child_completed_elsewhere() -> None:
    module = _load_module(
        "wizard_child_matrix_redundant_failure_under_test",
        REPO_ROOT / "scripts" / "wizard_child_matrix.py",
    )
    active = module.FORMAL_CHILDREN["failure.loophole_auditor"]
    completed = list(active)
    groups = [
        {
            "model": "sonnet",
            "usefulness_failures": [
                {
                    "id": "failure.loophole_auditor-skill-loophole-auditor-sonnet-1",
                    "status": "timed_out",
                    "reason": "child_not_completed",
                }
            ],
        },
        {"model": "opus", "usefulness_failures": []},
    ]

    assert module.blocking_usefulness_failures(groups, completed, active) == []


def test_wizard_child_matrix_keeps_failure_blocking_when_formal_child_missing() -> None:
    module = _load_module(
        "wizard_child_matrix_missing_failure_under_test",
        REPO_ROOT / "scripts" / "wizard_child_matrix.py",
    )
    active = module.FORMAL_CHILDREN["failure.loophole_auditor"]
    completed = [child for child in active if child != "skill.loophole_auditor"]
    failure = {
        "id": "failure.loophole_auditor-skill-loophole-auditor-sonnet-1",
        "status": "timed_out",
        "reason": "child_not_completed",
    }
    groups = [{"model": "sonnet", "usefulness_failures": [failure]}]

    assert module.blocking_usefulness_failures(groups, completed, active) == [failure]


def test_wizard_full_matrix_launches_sibling_council_routes_before_waiting(monkeypatch, tmp_path) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_parallel_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    events: list[str] = []

    class FakeProc:
        def __init__(self, command, **_kwargs) -> None:
            route = command[command.index("--route") + 1]
            self.route = route
            events.append(f"launch:{route}")

        def wait(self) -> int:
            events.append(f"wait:{self.route}")
            return 0

    class Args:
        task = "audit v4.2 topology"
        followup_prompt = "next"
        payoff = "prove parallel council topology"
        use_when = "running v4.2"
        stop_if = "blocked"
        boundary = "tmp receipts only"
        cwd = REPO_ROOT
        run_id = "test-run"
        sonnet_timeout_sec = 1
        opus_timeout_sec = 1
        haiku_timeout_sec = 1
        sonnet_count = 0
        opus_count = 0
        haiku_count = 1
        sonnet_budget = 0.1
        opus_budget = 0.1
        haiku_budget = 0.1
        global_max_active = 4
        max_concurrency = 2
        parallel_model_groups = True
        full_model_council = True
        attempt_gemini = False
        skip_gemini = True
        repair_single_model = True
        repair_skip_gemini = True
        capacity_preflight = False
        capacity_preflight_models = "sonnet,opus,haiku"
        capacity_preflight_timeout_sec = 1
        dry_run = False

    monkeypatch.setattr(module.subprocess, "Popen", FakeProc)
    routes = [
        "decision.context_strategy",
        "decision.move_selection",
        "decision.evidence_boundary",
    ]

    results = module.run_routes_parallel(Args, routes, tmp_path)

    assert list(results) == routes
    assert events[:3] == [f"launch:{route}" for route in routes]
    assert events[3:] == [f"wait:{route}" for route in routes]


def test_wizard_full_matrix_passes_parallel_model_groups_to_child_matrix() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_parallel_groups_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    class Args:
        task = "audit v4.2 topology"
        followup_prompt = "next"
        payoff = "prove parallel model families"
        use_when = "running v4.2"
        stop_if = "blocked"
        boundary = "tmp receipts only"
        cwd = REPO_ROOT
        run_id = "test-run"
        sonnet_timeout_sec = 1
        opus_timeout_sec = 1
        haiku_timeout_sec = 1
        sonnet_count = 0
        opus_count = 0
        haiku_count = 1
        sonnet_budget = 0.1
        opus_budget = 0.1
        haiku_budget = 0.1
        global_max_active = 4
        max_concurrency = 2
        parallel_model_groups = True
        full_model_council = True
        attempt_gemini = False
        skip_gemini = True
        repair_single_model = True
        repair_skip_gemini = True
        capacity_preflight = False
        capacity_preflight_models = "sonnet,opus,haiku"
        capacity_preflight_timeout_sec = 1
        dry_run = False

    command = module.route_command(Args, "decision.context_strategy", REPO_ROOT)

    assert "--parallel-model-groups" in command
    assert "--full-model-council" in command


def test_wizard_full_matrix_can_forward_dry_run_to_child_matrix() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_dry_run_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    class Args:
        task = "local topology rehearsal"
        followup_prompt = "next"
        payoff = "prove dry run forwarding"
        use_when = "external capacity unavailable"
        stop_if = "blocked"
        boundary = "tmp receipts only"
        cwd = REPO_ROOT
        run_id = "test-run"
        sonnet_timeout_sec = 1
        opus_timeout_sec = 1
        haiku_timeout_sec = 1
        sonnet_count = 0
        opus_count = 0
        haiku_count = 1
        sonnet_budget = 0.1
        opus_budget = 0.1
        haiku_budget = 0.1
        global_max_active = 4
        max_concurrency = 2
        parallel_model_groups = True
        full_model_council = True
        attempt_gemini = False
        skip_gemini = True
        dry_run = True
        repair_single_model = True
        repair_skip_gemini = True

    command = module.route_command(Args, "decision.context_strategy", REPO_ROOT)

    assert "--dry-run" in command


def test_wizard_full_matrix_compact_caps_child_count_to_route_obligation() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_compact_count_cap_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    class Args:
        mode = "compact"
        task = "compact count cap"
        followup_prompt = "next"
        payoff = "avoid duplicate child timeouts"
        use_when = "compact audit"
        stop_if = "blocked"
        boundary = "tmp receipts only"
        cwd = REPO_ROOT
        run_id = "test-run"
        sonnet_timeout_sec = 1
        opus_timeout_sec = 1
        haiku_timeout_sec = 1
        sonnet_count = 7
        opus_count = 1
        haiku_count = 0
        sonnet_budget = 0.1
        opus_budget = 0.1
        haiku_budget = 0.1
        global_max_active = 4
        max_concurrency = 2
        parallel_model_groups = True
        full_model_council = False
        codex_local_children = False
        attempt_gemini = False
        skip_gemini = True
        repair_single_model = True
        repair_skip_gemini = True
        dry_run = False

    command = module.route_command(Args, "failure.loophole_auditor", REPO_ROOT)

    assert command[command.index("--sonnet-count") + 1] == "4"


def test_wizard_full_matrix_does_not_attempt_gemini_by_default() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py").read_text(encoding="utf-8")

    assert 'parser.add_argument("--attempt-gemini", action="store_true", default=False)' in text


def test_wizard_v42_compact_routes_are_one_parent_per_council() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_compact_routes_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    assert module.council_wave_routes("Decision", "compact") == ["decision.move_selection"]
    assert module.council_wave_routes("Failure", "compact") == ["failure.falsifier"]
    assert module.council_wave_routes("Follow-Up", "compact") == ["follow_up.compile_gate"]


def test_wizard_v42_compact_can_run_three_representatives_parallel() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_compact_parallel_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    assert module.selected_run_waves("compact", "parallel") == [
        (
            "Compact",
            ["decision.move_selection", "failure.falsifier", "follow_up.compile_gate"],
        )
    ]


def test_wizard_v42_compact_profiles_select_different_members() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_compact_profiles_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    assert module.compact_council_routes("Decision", "audit") == ["decision.evidence_boundary"]
    assert module.compact_council_routes("Failure", "strategy") == ["failure.premortem"]
    assert module.compact_council_routes("Follow-Up", "followup") == ["follow_up.next_move_selector"]
    assert module.resolve_compact_profile("auto", "audit route truth and overclaim") == "audit"
    assert module.resolve_compact_profile("auto", "give nice formatting and readable report") == "formatting"
    assert (
        module.resolve_compact_profile(
            "auto",
            "nice formatting, clean output, readable report, route truth",
        )
        == "formatting"
    )
    assert module.selected_run_waves("compact", "parallel", "auto", "audit route truth") == [
        (
            "Compact",
            ["decision.evidence_boundary", "failure.loophole_auditor", "follow_up.compile_gate"],
        )
    ]


def test_wizard_v42_level_loop_cli_normalizes_friendly_invocation() -> None:
    module = _load_module(
        "wizard_v4_2_level_loop_cli_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )

    assert module.normalize_invocation(["low", "loop", "2", "--task", "x"]) == (
        "low",
        "2",
        ["--task", "x"],
    )
    assert module.normalize_invocation(["auto", "loop", "auto", "--task", "x"]) == (
        "auto",
        "auto",
        ["--task", "x"],
    )
    assert module.loop_limit("auto") == (6, True)
    assert module.loop_limit("2") == (2, False)


def test_wizard_v42_auto_level_selects_reasoning_breadth() -> None:
    module = _load_module(
        "wizard_v4_2_auto_level_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )

    assert module.select_auto_level("give nice formatting") == "low"
    assert module.select_auto_level("audit route truth and overclaim") == "medium"
    assert module.select_auto_level("canonical sim promotion proof") == "high"


def test_wizard_v42_level_presets_build_expected_runner_commands(tmp_path) -> None:
    module = _load_module(
        "wizard_v4_2_runner_command_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )

    low_command = module.build_runner_command(
        preset=module.PRESETS["low"],
        task="audit",
        out_dir=tmp_path / "low",
        cwd=REPO_ROOT,
    )
    high_command = module.build_runner_command(
        preset=module.PRESETS["high"],
        task="proof",
        out_dir=tmp_path / "high",
        cwd=REPO_ROOT,
        attempt_gemini=True,
    )

    assert low_command[low_command.index("--mode") + 1] == "compact"
    assert low_command[low_command.index("--compact-route-mode") + 1] == "sequential"
    assert low_command[low_command.index("--compact-profile") + 1] == "auto"
    assert low_command[low_command.index("--sonnet-count") + 1] == "7"
    assert "--no-full-model-council" in low_command
    assert "--skip-gemini" in low_command
    assert high_command[high_command.index("--mode") + 1] == "full"
    assert "--full-model-council" in high_command
    assert "--parallel-model-groups" in high_command
    assert "--attempt-gemini" in high_command
    assert "--skip-gemini" not in high_command


def test_wizard_v42_level_wrapper_can_force_compact_profile(tmp_path) -> None:
    module = _load_module(
        "wizard_v4_2_runner_profile_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )

    command = module.build_runner_command(
        preset=module.PRESETS["low"],
        task="premortem audit repair",
        out_dir=tmp_path / "low",
        cwd=REPO_ROOT,
        compact_profile="strategy",
    )

    assert command[command.index("--compact-profile") + 1] == "strategy"


def test_wizard_v42_loop_extracts_next_task_from_compiled_followup(tmp_path) -> None:
    module = _load_module(
        "wizard_v4_2_next_task_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )
    compiled = tmp_path / "compiled.md"
    compiled.write_text(
        "\n".join(
            [
                "🧙 Wizard v4.2 | PARTIAL | waves:3/3 | parents:3/3 | children:1/1 | tools:2 | score:90 | runtimes:codex-controller | mode:compact",
                "## 🧭 Follow-Up Options",
                "### 1. Continue",
                "`Run Wizard Auto loop auto on the next evidence repair.`",
            ]
        ),
        encoding="utf-8",
    )

    assert module.next_task_from_compiled(compiled, "fallback") == (
        "Run Wizard Auto loop auto on the next evidence repair."
    )
    assert module.should_stop_auto_loop(
        header="🧙 Wizard v4.2 | PARTIAL",
        next_task="fallback",
        seen_tasks={"fallback"},
    ) == "repeated_next_task"
    assert module.should_stop_auto_loop(
        header="🧙 Wizard v4.2 | PARTIAL",
        next_task="repair next",
        seen_tasks=set(),
    ) is None
    assert module.should_stop_auto_loop(
        header="🧙 Wizard v4.2 | BLOCKED",
        next_task="repair next",
        seen_tasks=set(),
    ) == "blocked_header"


def test_wizard_v42_loop_stops_when_compile_fails(monkeypatch, tmp_path) -> None:
    module = _load_module(
        "wizard_v4_2_compile_fail_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )

    class Proc:
        returncode = 0

    def fake_run(command, **_kwargs):
        out_dir = Path(command[command.index("--out-dir") + 1])
        run_root = out_dir / "20260509T000000Z"
        run_root.mkdir(parents=True)
        return Proc()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "compile_run", lambda *_args, **_kwargs: (1, "compile failed"))

    args = argparse.Namespace(
        out_dir=str(tmp_path),
        requested_level="low",
        loop_value="2",
        task="test compile failure",
        cwd=REPO_ROOT,
        dry_run=False,
        codex_local_children=True,
        attempt_gemini=False,
        no_capacity_preflight=True,
    )

    assert module.run_level_loop(args, module.PRESETS["low"], loop_count=2, loop_auto=False) == 1
    manifest = json.loads(next(tmp_path.glob("wizard-low-*/wizard_loop_manifest.json")).read_text(encoding="utf-8"))
    assert manifest["stop_reason"] == "compile_failed"
    assert len(manifest["iterations"]) == 1


def test_wizard_v42_auto_loop_stops_after_repeated_pass(monkeypatch, tmp_path) -> None:
    module = _load_module(
        "wizard_v4_2_repeat_stop_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )

    class Proc:
        returncode = 0

    def fake_run(command, **_kwargs):
        out_dir = Path(command[command.index("--out-dir") + 1])
        run_root = out_dir / "20260509T000000Z"
        run_root.mkdir(parents=True)
        return Proc()

    def fake_compile(_run_root, task, _cwd, compiled_path):
        compiled_path.write_text(
            "\n".join(
                [
                    "🧙 Wizard v4.2 | PARTIAL | waves:3/3 | parents:3/3 | children:1/1 | tools:2 | score:90 | runtimes:codex-controller | mode:compact",
                    "## 🧭 Follow-Up Options",
                    f"`{task}`",
                ]
            ),
            encoding="utf-8",
        )
        return 0, str(compiled_path)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "compile_run", fake_compile)

    args = argparse.Namespace(
        out_dir=str(tmp_path),
        requested_level="medium",
        loop_value="auto",
        task="repeat me exactly",
        cwd=REPO_ROOT,
        dry_run=False,
        codex_local_children=True,
        attempt_gemini=False,
        no_capacity_preflight=True,
    )

    assert module.run_level_loop(args, module.PRESETS["medium"], loop_count=6, loop_auto=True) == 0
    manifest = json.loads(next(tmp_path.glob("wizard-medium-*/wizard_loop_manifest.json")).read_text(encoding="utf-8"))
    assert manifest["stop_reason"] == "repeated_next_task"
    assert len(manifest["iterations"]) == 1
    assert Path(manifest["iterations"][0]["wizard_output"]).name == "latest_wizard_output.md"
    assert Path(manifest["iterations"][0]["wizard_output"]).exists()


def test_wizard_v42_auto_loop_continues_after_partial_output(monkeypatch, tmp_path) -> None:
    module = _load_module(
        "wizard_v4_2_partial_continue_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )

    class Proc:
        returncode = 1

    calls = {"count": 0}

    def fake_run(command, **_kwargs):
        calls["count"] += 1
        out_dir = Path(command[command.index("--out-dir") + 1])
        run_root = out_dir / f"20260509T00000{calls['count']}Z"
        run_root.mkdir(parents=True)
        return Proc()

    def fake_compile(_run_root, task, _cwd, compiled_path):
        header = "🧙 Wizard v4.2 | PARTIAL | waves:3/3 | parents:3/3 | children:1/1 | tools:2 | score:90 | runtimes:codex-controller | mode:compact" if calls["count"] == 1 else "🧙 Wizard v4.2 | PARTIAL | waves:3/3 | parents:3/3 | children:1/1 | tools:2 | score:90 | runtimes:codex-controller | mode:compact"
        next_prompt = "repair visible Wizard output" if calls["count"] == 1 else task
        compiled_path.write_text(
            "\n".join([header, "## 🧭 Follow-Up Options", f"`{next_prompt}`"]),
            encoding="utf-8",
        )
        return 0, str(compiled_path)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "compile_run", fake_compile)

    args = argparse.Namespace(
        out_dir=str(tmp_path),
        requested_level="medium",
        loop_value="auto",
        task="audit visible Wizard output",
        cwd=REPO_ROOT,
        dry_run=False,
        codex_local_children=True,
        attempt_gemini=False,
        no_capacity_preflight=True,
    )

    assert module.run_level_loop(args, module.PRESETS["medium"], loop_count=6, loop_auto=True) == 0
    manifest = json.loads(next(tmp_path.glob("wizard-medium-*/wizard_loop_manifest.json")).read_text(encoding="utf-8"))
    assert len(manifest["iterations"]) == 2
    assert manifest["iterations"][0]["header"].startswith("🧙 Wizard v4.2 | PARTIAL")
    assert manifest["iterations"][1]["header"].startswith("🧙 Wizard v4.2 | PARTIAL")
    assert Path(manifest["iterations"][1]["wizard_output"]).read_text(encoding="utf-8").startswith(
        "🧙 Wizard v4.2 | PARTIAL"
    )


def test_wizard_v42_loop_prints_wizard_output_not_json_log(monkeypatch, capsys, tmp_path) -> None:
    module = _load_module(
        "wizard_v4_2_stdout_output_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )

    class Proc:
        returncode = 0

    def fake_run(command, **_kwargs):
        out_dir = Path(command[command.index("--out-dir") + 1])
        run_root = out_dir / "20260509T000000Z"
        run_root.mkdir(parents=True)
        return Proc()

    def fake_compile(_run_root, _task, _cwd, compiled_path):
        compiled_path.write_text(
            "\n".join(
                [
                    "🧙 Wizard v4.2 | PARTIAL | waves:3/3 | parents:3/3 | children:1/1 | tools:2 | score:90 | runtimes:codex-controller | mode:compact",
                    "",
                    "## ✨ Answer",
                    "",
                    "Wizard body, not a JSON pass record.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        return 0, str(compiled_path)

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "compile_run", fake_compile)

    args = argparse.Namespace(
        out_dir=str(tmp_path),
        requested_level="low",
        loop_value="1",
        task="print wizard body",
        cwd=REPO_ROOT,
        dry_run=False,
        codex_local_children=True,
        attempt_gemini=False,
        no_capacity_preflight=True,
    )

    assert module.run_level_loop(args, module.PRESETS["low"], loop_count=1, loop_auto=False) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("🧙 Wizard v4.2 | PARTIAL | loops:1/1 | waves:3/3")
    assert "## ✨ Answer" in captured.out
    assert not captured.out.lstrip().startswith("{")
    assert '"compile_returncode": 0' in captured.err


def test_wizard_v42_loop_output_header_aggregates_completed_loops() -> None:
    module = _load_module(
        "wizard_v4_2_aggregate_header_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )
    manifest = {
        "loop_count_limit": 4,
        "iterations": [
            {
                "header": "🧙 Wizard v4.2 | PARTIAL | waves:3/3 | parents:3/3 | children:13/13 | tools:2 | score:90 | runtimes:codex-controller, claude-bridge | mode:compact"
            },
            {
                "header": "🧙 Wizard v4.2 | PARTIAL | waves:3/3 | parents:3/3 | children:15/15 | tools:2 | score:90 | runtimes:codex-controller, claude-bridge | mode:compact"
            },
        ],
    }
    output = "\n".join(
        [
            "🧙 Wizard v4.2 | PARTIAL | waves:3/3 | parents:3/3 | children:15/15 | tools:2 | score:90 | runtimes:codex-controller, claude-bridge | mode:compact",
            "",
            "## ✨ Answer",
            "Body.",
        ]
    )
    aggregated = module.aggregate_loop_header(manifest, output)

    assert aggregated.startswith(
        "🧙 Wizard v4.2 | PARTIAL | loops:2/4 | waves:6/6 | parents:6/6 | children:28/28 | tools:4 | score:90 | runtimes:codex-controller, claude-bridge | mode:compact"
    )


def test_wizard_v42_compact_defaults_shrink_fanout(monkeypatch, tmp_path) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_compact_defaults_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    seen: dict[str, object] = {}

    def fake_external_capacity_preflight(args, root):
        seen["preflight_mode"] = args.mode
        return {"status": "skipped", "probes": []}

    def fake_run_routes_parallel(args, routes, root, repair_by_route=None):
        seen["mode"] = args.mode
        seen["sonnet_count"] = args.sonnet_count
        seen["opus_count"] = args.opus_count
        seen["haiku_count"] = args.haiku_count
        seen["full_model_council"] = args.full_model_council
        seen["attempt_gemini"] = args.attempt_gemini
        return {route: 1 for route in routes}

    monkeypatch.setattr(module, "external_capacity_preflight", fake_external_capacity_preflight)
    monkeypatch.setattr(module, "run_routes_parallel", fake_run_routes_parallel)
    monkeypatch.setattr(module, "capacity_blockers", lambda root: [])
    monkeypatch.setattr(module, "status_json", lambda root, cwd, required_routes=None: (1, {"members": []}))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wizard_full_matrix_run_v4_2.py",
            "--task",
            "compact defaults regression",
            "--cwd",
            str(REPO_ROOT),
            "--out-dir",
            str(tmp_path / "compact"),
            "--mode",
            "compact",
            "--max-repair-loops",
            "0",
            "--no-capacity-preflight",
        ],
    )

    assert module.main() == 1
    assert seen["mode"] == "compact"
    assert seen["sonnet_count"] == 1
    assert seen["opus_count"] == 1
    assert seen["haiku_count"] == 0
    assert seen["full_model_council"] is False
    assert seen["attempt_gemini"] is False


def test_wizard_full_matrix_zero_repair_loops_accepts_clean_status(monkeypatch, tmp_path) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_zero_repair_accept_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    monkeypatch.setattr(module, "external_capacity_preflight", lambda args, root: {"status": "skipped", "probes": []})
    monkeypatch.setattr(module, "run_routes_parallel", lambda args, routes, root, repair_by_route=None: {route: 0 for route in routes})
    monkeypatch.setattr(module, "capacity_blockers", lambda root: [])
    monkeypatch.setattr(
        module,
        "status_json",
        lambda root, cwd, required_routes=None: (
            0,
            {
                "members": [
                    {"status": "accepted", "first_pass_clean": True},
                    {"status": "accepted", "first_pass_clean": True},
                    {"status": "accepted", "first_pass_clean": True},
                ]
            },
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wizard_full_matrix_run_v4_2.py",
            "--task",
            "zero repair accept regression",
            "--cwd",
            str(REPO_ROOT),
            "--out-dir",
            str(tmp_path / "compact"),
            "--mode",
            "compact",
            "--compact-route-mode",
            "parallel",
            "--max-repair-loops",
            "0",
            "--no-capacity-preflight",
        ],
    )

    assert module.main() == 0


def test_wizard_child_matrix_dry_run_children_are_not_useful_or_accepted() -> None:
    module = _load_module(
        "wizard_child_matrix_dry_run_truth_under_test",
        REPO_ROOT / "scripts" / "wizard_child_matrix.py",
    )

    dry_child = {"id": "decision.context_strategy-voice.hume-sonnet-1", "status": "dry_run"}
    groups = [{"model": "sonnet", "status": "dry_run", "counts": {"completed": 0}}]
    gemini = {"model": "gemini", "status": "dry_run", "counts": {"completed": 0}}

    assert module.child_usefulness_failure_reason(dry_child) == "child_not_completed"
    assert module.child_is_useful(dry_child) is False
    assert module.accepted_child_count(groups, gemini) == 0


def test_wizard_full_matrix_repairs_partial_routes_but_not_accepted_unclean_by_default() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_partial_repair_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    repair = module.repair_children_by_route(
        {
            "members": [
                {
                    "route": "failure.premortem",
                    "status": "partial",
                    "missing_formal": [],
                    "first_pass_clean": False,
                },
                {
                    "route": "follow_up.compile_gate",
                    "status": "accepted",
                    "missing_formal": [],
                    "first_pass_clean": False,
                },
            ]
        }
    )

    assert repair["failure.premortem"] == module.FORMAL_CHILDREN["failure.premortem"]
    assert "follow_up.compile_gate" not in repair


def test_wizard_full_matrix_can_repair_accepted_unclean_when_explicit() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_unclean_repair_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    repair = module.repair_children_by_route(
        {
            "members": [
                {
                    "route": "follow_up.compile_gate",
                    "status": "accepted",
                    "missing_formal": [],
                    "first_pass_clean": False,
                },
            ]
        },
        repair_first_pass_unclean=True,
    )

    assert repair["follow_up.compile_gate"] == module.FORMAL_CHILDREN["follow_up.compile_gate"]


def test_wizard_full_matrix_caps_repair_routes() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_repair_cap_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    repair = module.repair_children_by_route(
        {
            "members": [
                {"route": "failure.premortem", "status": "partial", "missing_formal": []},
                {"route": "failure.falsifier", "status": "partial", "missing_formal": []},
                {"route": "follow_up.compile_gate", "status": "partial", "missing_formal": []},
            ]
        },
        max_repair_routes=2,
    )

    assert list(repair) == ["failure.premortem", "failure.falsifier"]


def test_wizard_full_matrix_uses_smaller_repair_fanout_by_default() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_repair_command_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    class Args:
        task = "audit v4.2 repair"
        followup_prompt = "next"
        payoff = "avoid repair storm"
        use_when = "repairing v4.2"
        stop_if = "blocked"
        boundary = "tmp receipts only"
        cwd = REPO_ROOT
        run_id = "test-run"
        sonnet_timeout_sec = 1
        opus_timeout_sec = 1
        haiku_timeout_sec = 1
        sonnet_count = 0
        opus_count = 0
        haiku_count = 1
        sonnet_budget = 0.1
        opus_budget = 0.1
        haiku_budget = 0.1
        global_max_active = 4
        max_concurrency = 2
        parallel_model_groups = True
        full_model_council = True
        attempt_gemini = True
        skip_gemini = False
        repair_single_model = True
        repair_skip_gemini = True
        capacity_preflight = False
        capacity_preflight_models = "sonnet,opus,haiku"
        capacity_preflight_timeout_sec = 1
        dry_run = False

    command = module.route_command(Args, "follow_up.compile_gate", REPO_ROOT, ["compile_gate.action"])

    assert "--parallel-model-groups" in command
    assert "--full-model-council" not in command
    assert "--attempt-gemini" not in command


def test_wizard_full_matrix_caps_repair_fanout_to_missing_children() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_repair_child_cap_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    class Args:
        mode = "compact"
        task = "audit v4.2 repair"
        followup_prompt = "next"
        payoff = "avoid repair storm"
        use_when = "repairing v4.2"
        stop_if = "blocked"
        boundary = "tmp receipts only"
        cwd = REPO_ROOT
        run_id = "test-run"
        sonnet_timeout_sec = 1
        opus_timeout_sec = 1
        haiku_timeout_sec = 1
        sonnet_count = 7
        opus_count = 1
        haiku_count = 0
        sonnet_budget = 0.1
        opus_budget = 0.1
        haiku_budget = 0.1
        global_max_active = 6
        max_concurrency = 4
        parallel_model_groups = False
        codex_local_children = False
        full_model_council = False
        attempt_gemini = False
        skip_gemini = True
        repair_single_model = True
        repair_skip_gemini = True
        capacity_preflight = False
        capacity_preflight_models = "sonnet"
        capacity_preflight_timeout_sec = 1
        dry_run = False

    command = module.route_command(Args, "failure.loophole_auditor", REPO_ROOT, ["voice.strategy"])

    assert command[command.index("--sonnet-count") + 1] == "1"
    assert command[command.index("--opus-count") + 1] == "1"
    assert command[command.index("--haiku-count") + 1] == "0"
    assert command[command.index("--only-children") + 1] == "voice.strategy"


def test_wizard_full_matrix_compact_passes_active_child_obligation() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_compact_obligation_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    class Args:
        mode = "compact"
        task = "audit v4.2 compact route truth"
        followup_prompt = "next"
        payoff = "avoid compact overclaim"
        use_when = "compact route smoke"
        stop_if = "blocked"
        boundary = "tmp receipts only"
        cwd = REPO_ROOT
        run_id = "test-run"
        sonnet_timeout_sec = 1
        opus_timeout_sec = 1
        haiku_timeout_sec = 1
        sonnet_count = 1
        opus_count = 1
        haiku_count = 0
        sonnet_budget = 0.1
        opus_budget = 0.1
        haiku_budget = 0.1
        global_max_active = 2
        max_concurrency = 2
        parallel_model_groups = False
        codex_local_children = False
        full_model_council = False
        attempt_gemini = False
        skip_gemini = True
        repair_single_model = True
        repair_skip_gemini = True
        capacity_preflight = False
        capacity_preflight_models = "sonnet"
        capacity_preflight_timeout_sec = 1
        dry_run = False

    command = module.route_command(Args, "follow_up.compile_gate", REPO_ROOT)

    assert command[command.index("--only-children") + 1] == "compile_gate.target"


def test_wizard_full_matrix_detects_external_capacity_blockers(tmp_path) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_capacity_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    receipt = tmp_path / "child.receipt.json"
    receipt.write_text(
        json.dumps({"parsed": {"result_preview": "You've hit your limit - resets later"}}),
        encoding="utf-8",
    )

    blockers = module.capacity_blockers(tmp_path)

    assert blockers
    assert blockers[0]["path"] == str(receipt)
    assert blockers[0]["pattern"] == "you've hit your limit"


def test_wizard_full_matrix_scans_matrix_and_gemini_capacity_receipts(tmp_path) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_capacity_receipts_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    matrix = tmp_path / "route" / "matrix_receipt.json"
    gemini = tmp_path / "route" / "gemini" / "gemini_group_receipt.json"
    matrix.parent.mkdir(parents=True)
    gemini.parent.mkdir(parents=True)
    matrix.write_text(json.dumps({"status": "partial", "note": "hit your limit"}), encoding="utf-8")
    gemini.write_text(json.dumps({"status": "blocked", "note": "quota will reset"}), encoding="utf-8")

    blockers = module.capacity_blockers(tmp_path)
    paths = {Path(row["path"]).name for row in blockers}

    assert "matrix_receipt.json" in paths
    assert "gemini_group_receipt.json" in paths


def test_sim_inventory_excludes_finder_duplicates_and_requires_admission_result_link(tmp_path) -> None:
    module = _load_module(
        "sim_inventory_index_duplicate_admission_under_test",
        REPO_ROOT / "scripts" / "sim_inventory_index.py",
    )
    module.ROOT = tmp_path
    module.PROBES = tmp_path / "system_v4" / "probes"
    module.PROBES.mkdir(parents=True)
    result_dir = tmp_path / "system_v4" / "probes" / "a2_state" / "sim_results"
    result_dir.mkdir(parents=True)
    admission_dir = tmp_path / "system_v5" / "ops" / "wizard_admissions"
    admission_dir.mkdir(parents=True)

    source_text = (
        'TOOL_MANIFEST = {"z3": {"used": True, "reason": "fixture"}}\n'
        'TOOL_INTEGRATION_DEPTH = {"z3": "load_bearing"}\n'
    )
    (module.PROBES / "sim_good.py").write_text(source_text, encoding="utf-8")
    (module.PROBES / "sim_good 2.py").write_text(source_text, encoding="utf-8")
    (module.PROBES / "sim_missing.py").write_text(source_text, encoding="utf-8")
    good_result = result_dir / "good_results.json"
    good_result.write_text(
        json.dumps({"tool_manifest": {"z3": {"used": True}}, "tool_integration_depth": {"z3": "load_bearing"}}),
        encoding="utf-8",
    )
    (admission_dir / "sim_good.json").write_text(
        json.dumps({"formal_sim_profile": {"expected_result_path": str(good_result)}}),
        encoding="utf-8",
    )
    (admission_dir / "sim_good 2.json").write_text(
        json.dumps({"formal_sim_profile": {"expected_result_path": str(good_result)}}),
        encoding="utf-8",
    )
    (admission_dir / "sim_missing.json").write_text(
        json.dumps({"formal_sim_profile": {"expected_result_path": str(result_dir / "missing_results.json")}}),
        encoding="utf-8",
    )

    index = module.build_index()
    rows = {row["stem"]: row for row in index["rows"]}

    assert "sim_good 2" not in rows
    assert index["admitted_stems"] == ["sim_good"]
    assert rows["sim_good"]["inventory_status"] == "admitted"
    assert rows["sim_missing"]["inventory_status"] == "admission_missing_result_link"
    assert index["summary"]["admitted_count"] == 1
    assert index["summary"]["admission_repair_count"] == 1


def test_sim_inventory_reports_unlinked_result_paths(tmp_path) -> None:
    module = _load_module(
        "sim_inventory_index_unlinked_results_under_test",
        REPO_ROOT / "scripts" / "sim_inventory_index.py",
    )
    module.ROOT = tmp_path
    module.PROBES = tmp_path / "system_v4" / "probes"
    module.PROBES.mkdir(parents=True)
    result_dir = tmp_path / "system_v4" / "probes" / "a2_state" / "sim_results"
    result_dir.mkdir(parents=True)
    (module.PROBES / "sim_linked.py").write_text(
        'TOOL_MANIFEST = {"numpy": {"used": True, "reason": "fixture"}}\n'
        'TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}\n',
        encoding="utf-8",
    )
    (result_dir / "linked_results.json").write_text(
        json.dumps({"tool_manifest": {"numpy": {"used": True}}, "tool_integration_depth": {"numpy": "load_bearing"}}),
        encoding="utf-8",
    )
    (result_dir / "orphan_results.json").write_text(json.dumps({"classification": "canonical"}), encoding="utf-8")

    index = module.build_index()

    assert index["summary"]["result_json_count"] == 2
    assert index["summary"]["linked_result_json_count"] == 1
    assert index["summary"]["unlinked_result_json_count"] == 1
    assert index["unlinked_result_samples"] == ["system_v4/probes/a2_state/sim_results/orphan_results.json"]


def test_sim_inventory_separates_execution_lanes_and_engine_roles(tmp_path) -> None:
    module = _load_module(
        "sim_inventory_index_execution_lanes_under_test",
        REPO_ROOT / "scripts" / "sim_inventory_index.py",
    )
    module.ROOT = tmp_path
    module.PROBES = tmp_path / "system_v4" / "probes"
    module.PROBES.mkdir(parents=True)
    result_dir = tmp_path / "system_v4" / "probes" / "a2_state" / "sim_results"
    result_dir.mkdir(parents=True)

    source_contract = (
        'TOOL_MANIFEST = {"numpy": {"used": True, "reason": "fixture"}}\n'
        'TOOL_INTEGRATION_DEPTH = {"numpy": "load_bearing"}\n'
    )
    (module.PROBES / "sim_classical_carnot_two_bath_cycle.py").write_text(
        'SIM_EXECUTION_KIND = "classical"\n' + source_contract,
        encoding="utf-8",
    )
    (module.PROBES / "sim_semiclassical_szilard_measure_feedback_erasure.py").write_text(
        'SIM_EXECUTION_KIND = "semiclassical_szilard"\n' + source_contract,
        encoding="utf-8",
    )
    (module.PROBES / "sim_bridge_xi_cut_boundary.py").write_text(
        'SIM_EXECUTION_KIND = "bridge"\n' + source_contract,
        encoding="utf-8",
    )
    (module.PROBES / "sim_weyl_spinor_nonclassical_probe.py").write_text(
        'SIM_EXECUTION_KIND = "nonclassical"\n' + source_contract,
        encoding="utf-8",
    )
    (module.PROBES / "sim_negative_graveyard_control.py").write_text("# no result yet\n", encoding="utf-8")

    result_payload = {
        "tool_manifest": {"np.linalg": {"used": True}},
        "tool_integration_depth": {"np.linalg": "load_bearing"},
    }
    (result_dir / "classical_carnot_two_bath_cycle_results.json").write_text(
        json.dumps({"classification": "classical_baseline", **result_payload}),
        encoding="utf-8",
    )
    (result_dir / "semiclassical_szilard_measure_feedback_erasure_results.json").write_text(
        json.dumps({"classification": "canonical", "sim_execution_kind": "semiclassical_szilard", **result_payload}),
        encoding="utf-8",
    )
    (result_dir / "bridge_xi_cut_boundary_results.json").write_text(
        json.dumps({"classification": "canonical", "sim_execution_kind": "bridge", **result_payload}),
        encoding="utf-8",
    )
    (result_dir / "weyl_spinor_nonclassical_probe_results.json").write_text(
        json.dumps({"classification": "canonical", "sim_execution_kind": "nonclassical", **result_payload}),
        encoding="utf-8",
    )

    index = module.build_index()
    rows = {row["stem"]: row for row in index["rows"]}

    assert rows["sim_classical_carnot_two_bath_cycle"]["sim_execution_lane"] == "classical"
    assert rows["sim_classical_carnot_two_bath_cycle"]["engine_types"] == ["carnot"]
    assert "full_run_signal" in rows["sim_classical_carnot_two_bath_cycle"]["engine_role_modes"]
    assert rows["sim_classical_carnot_two_bath_cycle"]["engine_roles"] == ["classical_carnot_engine_token_match"]
    assert rows["sim_semiclassical_szilard_measure_feedback_erasure"]["sim_execution_lane"] == "semiclassical_szilard"
    assert rows["sim_semiclassical_szilard_measure_feedback_erasure"]["engine_types"] == ["szilard"]
    assert "landauer_erasure_signal" in rows["sim_semiclassical_szilard_measure_feedback_erasure"]["engine_role_modes"]
    assert rows["sim_semiclassical_szilard_measure_feedback_erasure"]["engine_role_conflict"] is False
    assert rows["sim_semiclassical_szilard_measure_feedback_erasure"]["engine_roles"] == [
        "semiclassical_szilard_engine_token_match"
    ]
    assert rows["sim_bridge_xi_cut_boundary"]["sim_execution_lane"] == "semiclassical_bridge"
    assert rows["sim_bridge_xi_cut_boundary"]["engine_types"] == ["none"]
    assert rows["sim_bridge_xi_cut_boundary"]["engine_roles"] == ["nonclassical_inspiration_or_boundary_signal"]
    assert "numpy_load_bearing_blocked_for_bridge_or_nonclassical" in rows["sim_bridge_xi_cut_boundary"][
        "promotion_blockers"
    ]
    assert rows["sim_weyl_spinor_nonclassical_probe"]["sim_execution_lane"] == "nonclassical"
    assert "nonclassical_inspiration_or_boundary_signal" in rows["sim_weyl_spinor_nonclassical_probe"]["engine_roles"]
    assert "nonclassical_requires_load_bearing_pytorch" in rows["sim_weyl_spinor_nonclassical_probe"][
        "promotion_blockers"
    ]
    assert rows["sim_negative_graveyard_control"]["cleanup_bucket"] == (
        "source_only_negative_or_graveyard_manifest_before_archive_decision"
    )
    assert "source_only_negative_or_graveyard" in rows["sim_negative_graveyard_control"]["garbage_candidate_flags"]
    assert rows["sim_weyl_spinor_nonclassical_probe"]["public_status_blockers"] == [
        "inventory_only_no_execution",
        "fresh_local_rerun_not_performed",
        "canonical_process_not_evaluated",
        "wizard_admission_not_accepted",
    ]
    assert index["summary"]["public_status_counts"] == {"exists": 5}
    assert index["summary"]["sim_execution_lane_counts"] == {
        "classical": 1,
        "nonclassical": 1,
        "semiclassical_bridge": 1,
        "semiclassical_szilard": 1,
        "unknown": 1,
    }
    assert index["summary"]["runner_execution_kind_counts"] == {
        "bridge": 2,
        "classical": 1,
        "nonclassical": 1,
        "unknown": 1,
    }
    assert index["summary"]["engine_type_counts"] == {"carnot": 1, "none": 3, "szilard": 1}
    assert "canonical_result_not_execution_lane_evidence" not in rows["sim_semiclassical_szilard_measure_feedback_erasure"][
        "garbage_candidate_flags"
    ]
    assert index["summary"]["garbage_candidate_counts"]["source_only_negative_or_graveyard"] == 1


def test_formal_scout_readiness_index_keeps_noncanonical_status(tmp_path) -> None:
    module = _load_module(
        "formal_scout_readiness_index_under_test",
        REPO_ROOT / "scripts" / "formal_scout_readiness_index.py",
    )
    scout_root = tmp_path / "system_v5" / "ops" / "formal_scouts"
    results = scout_root / "results"
    results.mkdir(parents=True)
    module.ROOT = tmp_path
    module.SCOUT_ROOT = scout_root
    module.RESULTS = results
    module.README = scout_root / "README.md"
    module.VALIDATOR = scout_root / "validate_formal_scout_results.py"

    module.VALIDATOR.write_text(
        "import json\n"
        "def validate(path):\n"
        "    data = json.loads(path.read_text())\n"
        "    errors = []\n"
        "    if data.get('classification') != 'formal_scout':\n"
        "        errors.append('classification is not formal_scout')\n"
        "    if data.get('promotion_allowed') is not False:\n"
        "        errors.append('promotion_allowed is not false')\n"
        "    return {'path': str(path), 'pass': not errors, 'errors': errors}\n",
        encoding="utf-8",
    )
    module.README.write_text(
        "| Harness | Result |\n| --- | --- |\n"
        "| good | `results/good_probe_results.json` |\n",
        encoding="utf-8",
    )
    (scout_root / "sim_good_probe.py").write_text("# good scout\n", encoding="utf-8")
    (scout_root / "sim_bad_probe.py").write_text("# bad scout\n", encoding="utf-8")
    (scout_root / "sim_mapping_probe.py").write_text("# starts with sim_ stem\n", encoding="utf-8")
    (scout_root / "sim_dual_probe.py").write_text("# alternate source\n", encoding="utf-8")
    (scout_root / "sim_sim_dual_probe.py").write_text("# validator expected source\n", encoding="utf-8")
    (scout_root / "sim_orphan_source.py").write_text("# no result\n", encoding="utf-8")
    good = {"classification": "formal_scout", "promotion_allowed": False, "claim_ceiling": "formal scout only"}
    (results / "good_probe_results.json").write_text(json.dumps(good), encoding="utf-8")
    (results / "bad_probe_results.json").write_text(
        json.dumps({"classification": "canonical", "promotion_allowed": True}),
        encoding="utf-8",
    )
    (results / "sim_mapping_probe_results.json").write_text(json.dumps(good), encoding="utf-8")
    (results / "sim_dual_probe_results.json").write_text(json.dumps(good), encoding="utf-8")

    index = module.build_index()
    rows = {row["stem"]: row for row in index["rows"]}

    assert index["summary"]["result_count"] == 4
    assert index["summary"]["source_count"] == 6
    assert index["summary"]["source_without_result_count"] == 1
    assert index["summary"]["validator_pass_count"] == 3
    assert index["summary"]["validator_fail_count"] == 1
    assert index["summary"]["readme_indexed_count"] == 1
    assert index["summary"]["readme_missing_count"] == 3
    assert index["summary"]["fresh_rerun_mapping_defect_count"] == 1
    assert index["summary"]["fresh_rerun_dual_source_defect_count"] == 1
    assert rows["good_probe"]["readiness_status"] == "schema_ready"
    assert rows["good_probe"]["public_status_label"] == "exists"
    assert "formal_scout_noncanonical" in rows["good_probe"]["promotion_blockers"]
    assert rows["bad_probe"]["readiness_status"] == "validator_failed"
    assert rows["sim_mapping_probe"]["fresh_rerun_mapping_defect"] is True
    assert rows["sim_mapping_probe"]["validator_expected_source_path"].endswith("sim_sim_mapping_probe.py")
    assert rows["sim_dual_probe"]["fresh_rerun_dual_source_defect"] is True


def test_grok_sim_archive_index_maps_sidequest_buckets(tmp_path) -> None:
    module = _load_module(
        "grok_sim_archive_index_under_test",
        REPO_ROOT / "scripts" / "grok_sim_archive_index.py",
    )
    grok_root = tmp_path / "system_v5" / "grok_sim"
    loop_root = grok_root / "loop_runner"
    receipts = loop_root / "receipts"
    contracts = loop_root / "contracts"
    proposed = loop_root / "proposed_formal_sims"
    complete_run = receipts / "complete_run"
    incomplete_run = receipts / "incomplete_run"
    missing_summary_run = receipts / "missing_summary_run"
    bad_late_phase_run = receipts / "bad_late_phase_run"
    for path in (complete_run, incomplete_run, missing_summary_run, bad_late_phase_run, contracts, proposed / "_quarantine_jargon"):
        path.mkdir(parents=True)
    module.ROOT = tmp_path
    module.GROK_ROOT = grok_root
    module.LOOP_ROOT = loop_root
    module.RECEIPTS = receipts
    module.CONTRACTS = contracts
    module.PROPOSED = proposed

    for phase in ("00_smoke", "01_axioms"):
        (contracts / f"phase_{phase}.py").write_text("# contract\n", encoding="utf-8")
    summary = {
        "run_id": "complete_run",
        "candidate": "/tmp/candidate.py",
        "phases": [{"phase_id": "00_smoke", "pass": True}, {"phase_id": "01_axioms", "pass": True}],
    }
    (complete_run / "_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (complete_run / "_frozen_manifest.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    (complete_run / "_run_hash.txt").write_text("abc\n", encoding="utf-8")
    (complete_run / "phase_00_smoke_results.json").write_text(
        json.dumps({"observable": {"phase_pass": True}, "classification": "side_quest_only", "promotion_allowed": False}),
        encoding="utf-8",
    )
    (incomplete_run / "_summary.json").write_text(json.dumps(summary | {"run_id": "incomplete_run"}), encoding="utf-8")
    (incomplete_run / "phase_00_smoke_results.json").write_text(
        json.dumps({"observable": {"phase_pass": True}}),
        encoding="utf-8",
    )
    (missing_summary_run / "phase_00_smoke_results.json").write_text(
        json.dumps({"observable": {"phase_pass": False}}),
        encoding="utf-8",
    )
    (bad_late_phase_run / "_summary.json").write_text(
        json.dumps(summary | {"run_id": "bad_late_phase_run"}),
        encoding="utf-8",
    )
    (bad_late_phase_run / "_frozen_manifest.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
    (bad_late_phase_run / "_run_hash.txt").write_text("def\n", encoding="utf-8")
    (bad_late_phase_run / "phase_00_smoke_results.json").write_text(
        json.dumps({"observable": {"phase_pass": True}, "promotion_allowed": False}),
        encoding="utf-8",
    )
    (bad_late_phase_run / "phase_01_axioms_results.json").write_text(
        json.dumps({"observable": {"phase_pass": True}, "promotion_allowed": True}),
        encoding="utf-8",
    )
    (proposed / "sim_proposed_constraint_manifold_assembly_handbuilt.py").write_text(
        "promotion_allowed = False\nclassification = 'formal_scout'\n",
        encoding="utf-8",
    )
    (proposed / "sim_bad.py").write_text(
        "promotion_allowed = True\nclassification = 'nonclassical_torch'\n",
        encoding="utf-8",
    )
    (proposed / "_quarantine_jargon" / "sim_old.py").write_text(
        "promotion_allowed = False\n",
        encoding="utf-8",
    )

    index = module.build_index()
    receipt_buckets = index["summary"]["receipt_archive_bucket_counts"]
    proposal_buckets = index["summary"]["proposed_archive_bucket_counts"]

    assert index["summary"]["receipt_run_dir_count"] == 4
    assert index["summary"]["complete_bundle_count"] == 2
    assert index["summary"]["citeable_sidequest_bundle_count"] == 1
    assert index["summary"]["complete_all_pass_bundle_count"] == 1
    assert index["summary"]["phase_promotion_allowed_true_count"] == 1
    assert index["summary"]["phase_count_at_least_live_contract_count_bundle_count"] == 1
    assert receipt_buckets["phase_count_at_least_live_contract_count_hash_review"] == 1
    assert receipt_buckets["quarantine_required_phase_promotion_allowed_true"] == 1
    assert receipt_buckets["archive_only_incomplete_receipt_bundle"] == 1
    assert receipt_buckets["archive_only_missing_summary"] == 1
    assert proposal_buckets["keep_current_handbuilt_proposal_source"] == 1
    assert proposal_buckets["quarantine_required_promotion_allowed_true"] == 1
    assert proposal_buckets["keep_graveyard_quarantine"] == 1
    assert index["high_risk_proposals"][0]["path"].endswith("sim_bad.py")


def test_sim_results_archive_candidates_requires_ignored_untracked_unreferenced_old(tmp_path) -> None:
    module = _load_module(
        "sim_results_archive_candidates_under_test",
        REPO_ROOT / "scripts" / "sim_results_archive_candidates.py",
    )
    result_root = tmp_path / "system_v4" / "probes" / "a2_state" / "sim_results"
    docs = tmp_path / "system_v5" / "docs"
    result_root.mkdir(parents=True)
    docs.mkdir(parents=True)

    names = [
        "safe_results.json",
        "tracked_results.json",
        "referenced_results.json",
        "recent_results.json",
        "notignored_results.json",
    ]
    now = module.SAFETY_WINDOW_SECONDS + 100.0
    for name in names:
        path = result_root / name
        path.write_text(json.dumps({"name": name}), encoding="utf-8")
        os.utime(path, (0, 0))
    os.utime(result_root / "recent_results.json", (now - 10, now - 10))
    (docs / "INDEX.md").write_text("keep `referenced_results.json` live\n", encoding="utf-8")

    tracked = {"system_v4/probes/a2_state/sim_results/tracked_results.json"}
    ignored = {
        "system_v4/probes/a2_state/sim_results/safe_results.json",
        "system_v4/probes/a2_state/sim_results/tracked_results.json",
        "system_v4/probes/a2_state/sim_results/referenced_results.json",
        "system_v4/probes/a2_state/sim_results/recent_results.json",
    }

    manifest = module.build_manifest(
        root=tmp_path,
        now=now,
        tracked_paths=tracked,
        ignored_paths=ignored,
        include_runtime_reference_scan=True,
    )
    rows = {Path(row["path"]).name: row for row in manifest["rows"]}

    assert rows["safe_results.json"]["decision"] == "MOVE_TO_ARCHIVE_CANDIDATE"
    assert rows["tracked_results.json"]["blockers"] == ["tracked_file"]
    assert "referenced_by_current_surface" in rows["referenced_results.json"]["blockers"]
    assert "inside_72h_safety_window" in rows["recent_results.json"]["blockers"]
    assert "not_gitignored" in rows["notignored_results.json"]["blockers"]
    assert manifest["summary"]["candidate_count"] == 1


def test_lego_tool_reporting_audit_writes_fail_closed_missing_registry(tmp_path) -> None:
    module = _load_module(
        "lego_tool_reporting_audit_missing_registry_under_test",
        REPO_ROOT / "system_v4" / "probes" / "lego_tool_reporting_audit.py",
    )
    module.PROJECT_DIR = tmp_path
    module.RESULTS_DIR = tmp_path / "system_v4" / "probes" / "a2_state" / "sim_results"
    module.REGISTRY_PATH = module.RESULTS_DIR / "actual_lego_registry.json"
    module.OUT_PATH = module.RESULTS_DIR / "lego_tool_reporting_audit_results.json"

    assert module.main() == 1
    report = json.loads(module.OUT_PATH.read_text(encoding="utf-8"))

    assert report["summary"]["ok"] is False
    assert report["blockers"][0]["kind"] == "missing_registry"


def test_controller_alignment_writes_blocked_surface_when_truth_audit_red(tmp_path) -> None:
    module = _load_module(
        "controller_alignment_audit_truth_red_under_test",
        REPO_ROOT / "system_v4" / "probes" / "controller_alignment_audit.py",
    )
    module.PROJECT_DIR = tmp_path
    module.RESULTS_DIR = tmp_path / "system_v4" / "probes" / "a2_state" / "sim_results"
    module.OUT_PATH = module.RESULTS_DIR / "controller_alignment_audit_results.json"
    module.TRUTH_AUDIT_PATH = module.RESULTS_DIR / "probe_truth_audit_results.json"
    module.DOC_DRIFT_INVENTORY_PATH = module.RESULTS_DIR / "controller_doc_drift_inventory.json"
    module.LIVE_ANCHOR_SPINE_PATH = module.RESULTS_DIR / "live_anchor_spine.json"
    module.MAKEFILE_PATH = tmp_path / "Makefile"
    module.BOT_PATH = tmp_path / "imessage_bot.py"
    module.REQ_SIM_STACK_PATH = tmp_path / "requirements-sim-stack.txt"
    module.RESULTS_DIR.mkdir(parents=True)
    module.MAKEFILE_PATH.write_text("PYTHON := /tmp/python\n", encoding="utf-8")
    module.BOT_PATH.write_text('PYTHON_BIN = "/tmp/python"\n', encoding="utf-8")
    module.REQ_SIM_STACK_PATH.write_text("z3-solver>=0.0\n", encoding="utf-8")
    module.TRUTH_AUDIT_PATH.write_text(json.dumps({"ok": False, "hard_finding_count": 1}), encoding="utf-8")

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(sys, "argv", ["controller_alignment_audit.py"])
    try:
        assert module.main() == 0
    finally:
        monkeypatch.undo()
    report = json.loads(module.OUT_PATH.read_text(encoding="utf-8"))

    assert report["status"] == "blocked"
    assert report["summary"]["blocked_reason"] == "truth_audit_not_green"
    assert report["summary"]["controller_contract_current"] is False


def test_controller_alignment_c2_compare_fails_closed_missing_inputs(tmp_path) -> None:
    module = _load_module(
        "controller_alignment_audit_missing_c2_under_test",
        REPO_ROOT / "system_v4" / "probes" / "controller_alignment_audit.py",
    )
    module.RESULTS_DIR = tmp_path
    module.PHASE7_RESULT_PATH = tmp_path / "phase7_baseline_validation_results.json"
    module.C2_REMAINING_PATH = tmp_path / "c2_topology_remaining_results.json"

    report = module.compare_c2_surfaces()

    assert report["available"] is False
    assert report["mismatch_count"] == 1
    assert report["mismatches"][0]["kind"] == "missing_c2_surface_input"


def test_controller_alignment_xgi_drift_fails_closed_missing_inputs(tmp_path) -> None:
    module = _load_module(
        "controller_alignment_audit_missing_xgi_under_test",
        REPO_ROOT / "system_v4" / "probes" / "controller_alignment_audit.py",
    )
    module.XGI_AUTOGRAD_SOURCE_PATH = tmp_path / "sim_xgi_torch_autograd.py"
    module.XGI_AUTOGRAD_RESULT_PATH = tmp_path / "xgi_torch_autograd_results.json"
    module.XGI_ASCENT_SOURCE_PATH = tmp_path / "sim_xgi_gradient_ascent.py"
    module.XGI_ASCENT_RESULT_PATH = tmp_path / "xgi_gradient_ascent_results.json"

    report = module.check_xgi_source_result_drift()

    assert report == [{
        "kind": "missing_xgi_source_result_input",
        "missing_inputs": [
            str(module.XGI_AUTOGRAD_SOURCE_PATH),
            str(module.XGI_AUTOGRAD_RESULT_PATH),
            str(module.XGI_ASCENT_SOURCE_PATH),
            str(module.XGI_ASCENT_RESULT_PATH),
        ],
        "source_result_drift_check_available": False,
    }]


def test_probe_truth_audit_allows_killed_graveyard_pass_false() -> None:
    module = _load_module(
        "probe_truth_audit_graveyard_under_test",
        REPO_ROOT / "system_v4" / "probes" / "probe_truth_audit.py",
    )
    payload = {
        "rows": [
            {
                "variant_id": "negative_variant",
                "verdict": "killed",
                "metrics": {"pass": False},
                "next_allowed_action": "graveyard this claim only",
            },
            {
                "variant_id": "surviving_variant",
                "verdict": "survived",
                "metrics": {"pass": True},
                "next_allowed_action": "use as local evidence only",
            },
        ],
        "boundary": {"all_rows_have_verdicts": {"pass": True}},
    }

    assert module.false_pass_paths(payload) == []


def test_probe_truth_audit_still_blocks_non_graveyard_pass_false() -> None:
    module = _load_module(
        "probe_truth_audit_failed_check_under_test",
        REPO_ROOT / "system_v4" / "probes" / "probe_truth_audit.py",
    )
    payload = {
        "rows": [
            {
                "variant_id": "surviving_variant",
                "verdict": "survived",
                "metrics": {"pass": False},
                "next_allowed_action": "use as local evidence only",
            }
        ]
    }

    assert module.false_pass_paths(payload) == ["$.rows[0].metrics.pass"]


def test_wizard_followups_preserve_inventory_admission_audit_domain() -> None:
    compiler = _load_module(
        "wizard_compile_output_v4_2_inventory_domain_under_test",
        REPO_ROOT / "scripts" / "wizard_compile_output_v4_2.py",
    )
    loop = _load_module(
        "wizard_v4_2_inventory_domain_under_test",
        REPO_ROOT / "scripts" / "wizard_v4_2.py",
    )
    task = "Audit Wizard inventory/admission updates for duplicate stems and missing result linkage."

    prompts = [prompt for _, prompt in compiler.task_preserving_followups(task, "PARTIAL", "compact")]

    assert "Wizard inventory/admission audit" in compiler.task_domain_label(task)
    assert any("Continue the Wizard inventory/admission audit" in prompt for prompt in prompts)
    assert all("Continue bounded sim work" not in prompt for prompt in prompts)
    assert loop.preserves_task_domain(prompts[0], task)


def test_wizard_full_matrix_detects_new_premortem_report_artifacts(tmp_path) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_premortem_artifact_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    existing = tmp_path / "premortem-report-existing.html"
    existing.write_text("old artifact\n", encoding="utf-8")
    baseline = module.premortem_artifacts(tmp_path)
    new_report = tmp_path / "premortem-report-new.html"
    new_transcript = tmp_path / "premortem-transcript-new.md"
    new_report.write_text("new report\n", encoding="utf-8")
    new_transcript.write_text("new transcript\n", encoding="utf-8")

    leaked = module.new_premortem_artifacts(tmp_path, baseline)

    assert str(existing) not in leaked
    assert leaked == [str(new_report), str(new_transcript)]


def test_gitignore_excludes_generated_premortem_artifacts() -> None:
    text = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "premortem-report-*.html" in text
    assert "premortem-transcript-*.md" in text


def test_wizard_full_matrix_capacity_preflight_blocks_before_waves(
    tmp_path,
    monkeypatch,
) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_capacity_preflight_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    launched: list[str] = []
    seen_commands: list[list[str]] = []

    def fake_run(command, **_kwargs):
        seen_commands.append(command)
        class Completed:
            returncode = 1
            stdout = "You've hit your limit - resets later"

        return Completed()

    bridge = tmp_path / "claude_bridge.py"
    bridge.write_text("# fixture\n", encoding="utf-8")
    monkeypatch.setattr(module, "CANONICAL_CLAUDE_BRIDGE", bridge)
    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "run_routes_parallel", lambda *args, **kwargs: launched.append("wave") or {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wizard_full_matrix_run_v4_2.py",
            "--task",
            "capacity preflight regression",
            "--cwd",
            str(REPO_ROOT),
            "--out-dir",
            str(tmp_path / "full"),
            "--skip-gemini",
        ],
    )

    assert module.main() == 1
    assert launched == []
    preflight_files = list((tmp_path / "full").glob("*/capacity_preflight.json"))
    assert preflight_files
    preflight = json.loads(preflight_files[0].read_text(encoding="utf-8"))
    assert preflight["status"] == "blocked"
    assert preflight["reason"] == "external_model_capacity"
    assert seen_commands[0][seen_commands[0].index("--budget") + 1] == "0.5"


def test_wizard_full_matrix_capacity_preflight_skips_in_dry_run(tmp_path) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_capacity_preflight_dry_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    class Args:
        dry_run = True
        capacity_preflight = True
        capacity_preflight_only = False
        capacity_preflight_models = "sonnet"
        capacity_preflight_timeout_sec = 1
        capacity_preflight_budget = 0.5
        cwd = REPO_ROOT

    assert module.external_capacity_preflight(Args, tmp_path)["status"] == "skipped"


def test_wizard_full_matrix_capacity_preflight_skips_for_codex_local_children(tmp_path) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_capacity_preflight_codex_local_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )

    class Args:
        dry_run = False
        codex_local_children = True
        capacity_preflight = True
        capacity_preflight_only = False
        capacity_preflight_models = "sonnet"
        capacity_preflight_timeout_sec = 1
        capacity_preflight_budget = 0.5
        cwd = REPO_ROOT

    assert module.external_capacity_preflight(Args, tmp_path) == {
        "status": "skipped",
        "reason": "codex_local_children",
        "probes": [],
    }


def test_wizard_child_matrix_codex_local_children_cover_formal_obligation(tmp_path) -> None:
    module = _load_module(
        "wizard_child_matrix_codex_local_under_test",
        REPO_ROOT / "scripts" / "wizard_child_matrix.py",
    )

    class Args:
        route = "failure.falsifier"

    roles = module.FORMAL_CHILDREN["failure.falsifier"]
    group = module.run_codex_local_group(Args, tmp_path, roles)

    assert group["model"] == "codex-local"
    assert group["counts"]["completed"] == len(roles)
    assert module.completed_formal_children_any_group([group], roles) == roles
    assert not group["usefulness_failures"]


def test_wizard_full_matrix_capacity_preflight_only_exits_before_waves(
    tmp_path,
    monkeypatch,
) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_capacity_preflight_only_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    launched: list[str] = []

    bridge = tmp_path / "claude_bridge.py"
    bridge.write_text("# fixture\n", encoding="utf-8")
    monkeypatch.setattr(module, "CANONICAL_CLAUDE_BRIDGE", bridge)

    def fake_run(command, **_kwargs):
        class Completed:
            returncode = 0
            stdout = "ready"

        return Completed()

    monkeypatch.setattr(module.subprocess, "run", fake_run)
    monkeypatch.setattr(module, "run_routes_parallel", lambda *args, **kwargs: launched.append("wave") or {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wizard_full_matrix_run_v4_2.py",
            "--task",
            "capacity preflight only regression",
            "--cwd",
            str(REPO_ROOT),
            "--out-dir",
            str(tmp_path / "full"),
            "--capacity-preflight-only",
            "--capacity-preflight-models",
            "sonnet",
        ],
    )

    assert module.main() == 0
    assert launched == []


def test_wizard_full_matrix_stops_after_capacity_blocked_council_wave(
    tmp_path,
    monkeypatch,
) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_capacity_stop_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    launched_waves: list[list[str]] = []

    def fake_run_routes_parallel(args, routes, root, repair_by_route=None):
        launched_waves.append(list(routes))
        receipt = root / "decision.context_strategy" / "child.receipt.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            json.dumps({"parsed": {"result_preview": "You have exhausted your capacity. Quota will reset later."}}),
            encoding="utf-8",
        )
        return {route: (1 if route == "decision.context_strategy" else 0) for route in routes}

    monkeypatch.setattr(module, "run_routes_parallel", fake_run_routes_parallel)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wizard_full_matrix_run_v4_2.py",
            "--task",
            "capacity breaker regression",
            "--cwd",
            str(REPO_ROOT),
            "--out-dir",
            str(tmp_path / "full"),
            "--skip-gemini",
            "--no-capacity-preflight",
        ],
    )

    assert module.main() == 1
    assert launched_waves == [module.council_wave_routes("Decision")]


def test_wizard_full_matrix_stops_on_capacity_even_when_routes_return_zero(
    tmp_path,
    monkeypatch,
) -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_capacity_zero_stop_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    launched_waves: list[list[str]] = []

    def fake_run_routes_parallel(args, routes, root, repair_by_route=None):
        launched_waves.append(list(routes))
        receipt = root / "follow_up.compile_gate" / "child.receipt.json"
        receipt.parent.mkdir(parents=True, exist_ok=True)
        receipt.write_text(
            json.dumps({"parsed": {"result_preview": "hit your limit - resets 8:50pm"}}),
            encoding="utf-8",
        )
        return {route: 0 for route in routes}

    monkeypatch.setattr(module, "run_routes_parallel", fake_run_routes_parallel)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "wizard_full_matrix_run_v4_2.py",
            "--task",
            "capacity breaker regression",
            "--cwd",
            str(REPO_ROOT),
            "--out-dir",
            str(tmp_path / "full"),
            "--skip-gemini",
            "--no-capacity-preflight",
        ],
    )

    assert module.main() == 1
    assert launched_waves == [module.council_wave_routes("Decision")]


def test_wizard_child_matrix_full_model_council_expands_opus_and_haiku() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_child_matrix.py").read_text(encoding="utf-8")

    assert 'parser.add_argument("--full-model-council"' in text
    assert "opus_count = args.opus_count if args.opus_count > 0 else (full_role_count if args.full_model_council else 1)" in text
    assert "haiku_count = full_role_count if args.full_model_council and args.haiku_count > 0 else args.haiku_count" in text
    assert "roles = roles if args.full_model_council and roles else [\"outside-model contrast and sanity check\"]" in text
    assert "gemini_group_receipt.json" in text
    assert '"mode": "full_model_council" if args.full_model_council else "asymmetric_model_council"' in text


def test_wizard_full_matrix_uses_three_council_waves_with_management_side_lanes() -> None:
    module = _load_module(
        "wizard_full_matrix_run_v4_2_topology_under_test",
        REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py",
    )
    text = (REPO_ROOT / "scripts" / "wizard_full_matrix_run_v4_2.py").read_text(encoding="utf-8")

    assert module.council_wave_routes("Decision") == [
        "decision.context_strategy",
        "decision.move_selection",
        "decision.evidence_boundary",
        "manager.run_controller",
        "manager.child_health",
    ]
    assert module.council_wave_routes("Failure") == [
        "failure.premortem",
        "failure.falsifier",
        "failure.loophole_auditor",
        "manager.strategy_memory",
    ]
    assert module.council_wave_routes("Follow-Up") == [
        "follow_up.next_move_selector",
        "follow_up.lane_builder",
        "follow_up.compile_gate",
        "manager.route_truth",
        "manager.output_compiler",
    ]
    assert "Management Preflight" not in text
    assert "Management Closeout" not in text


def test_wizard_member_status_does_not_upgrade_partial_receipt_to_accepted() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_member_status.py").read_text(encoding="utf-8")

    assert 'elif status == "accepted" and formal_expected and formal_passed == formal_expected:' in text
    assert "elif formal_expected and formal_passed == formal_expected:" not in text


def test_wizard_member_status_v42_keeps_dry_run_receipt_partial(tmp_path) -> None:
    route_dir = tmp_path / "decision.context_strategy" / "20260509T000000Z"
    route_dir.mkdir(parents=True)
    (route_dir / "matrix_receipt.json").write_text(
        json.dumps(
            {
                "route": "decision.context_strategy",
                "run_id": "wizard-v4-2-dry-run-fixture",
                "status": "partial",
                "formal_child_obligation": [
                    "voice.strategy",
                    "voice.systems",
                    "voice.hume",
                    "voice.feynman",
                ],
                "formal_children_completed": [],
                "groups": [
                    {
                        "model": "sonnet",
                        "status": "dry_run",
                        "counts": {"completed": 0, "failed": 0, "timed_out": 0, "total": 4},
                    }
                ],
                "gemini": {"status": "dry_run", "counts": {"completed": 0, "total": 1}},
            }
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "wizard_member_status_v4_2.py"),
            str(tmp_path),
            "--json",
        ],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )

    assert proc.returncode == 1
    payload = json.loads(proc.stdout)
    row = next(member for member in payload["members"] if member["route"] == "decision.context_strategy")
    assert row["status"] == "partial"
    assert row["formal_passed"] == 0
    assert row["agents_passed"] == 0


def test_wizard_compile_output_v42_labels_partial_when_gates_not_clean() -> None:
    module = _load_module(
        "wizard_compile_output_v4_2_label_under_test",
        REPO_ROOT / "scripts" / "wizard_compile_output_v4_2.py",
    )
    rows = [
        {"council": "Management", "status": "accepted", "formal_passed": 1, "formal_expected": 1},
        {"council": "Decision", "status": "accepted", "formal_passed": 1, "formal_expected": 1},
    ]
    counts = module.count_by_council(rows)

    assert module.run_completion_label(rows, counts, first_pass_clean=False, failed_or_weak=1) == "PARTIAL"
    assert module.council_result_label(rows, "Management", 5) == "partial"
    assert module.council_result_label(rows, "Failure", 3) == "blocked"


def test_wizard_compile_output_v42_labels_dry_run_status_as_blocked() -> None:
    module = _load_module(
        "wizard_compile_output_v4_2_dry_label_under_test",
        REPO_ROOT / "scripts" / "wizard_compile_output_v4_2.py",
    )
    rows = [
        {
            "council": "Decision",
            "status": "partial",
            "formal_passed": 0,
            "formal_expected": 4,
        },
        {
            "council": "Management",
            "status": "partial",
            "formal_passed": 0,
            "formal_expected": 3,
        },
    ]
    counts = module.count_by_council(rows)

    assert module.run_completion_label(rows, counts, first_pass_clean=False, failed_or_weak=0) == "BLOCKED"
    assert module.council_result_label(rows, "Decision", 3) == "blocked"


def test_wizard_compile_output_v42_compact_uses_compact_parent_denominator() -> None:
    module = _load_module(
        "wizard_compile_output_v4_2_compact_label_under_test",
        REPO_ROOT / "scripts" / "wizard_compile_output_v4_2.py",
    )
    rows = [
        {
            "council": "Decision",
            "status": "accepted",
            "formal_passed": 5,
            "formal_expected": 5,
        },
        {
            "council": "Failure",
            "status": "accepted",
            "formal_passed": 4,
            "formal_expected": 4,
        },
        {
            "council": "Follow-Up",
            "status": "accepted",
            "formal_passed": 7,
            "formal_expected": 7,
        },
    ]
    counts = module.count_by_council(rows)

    assert module.required_routes_for_compile("compact", "sequential") == [
        "decision.move_selection",
        "failure.falsifier",
        "follow_up.compile_gate",
    ]
    assert module.required_routes_for_compile("compact", "parallel", "strategy") == [
        "decision.context_strategy",
        "failure.premortem",
        "follow_up.lane_builder",
    ]
    assert module.expected_parent_counts(rows) == {"Decision": 1, "Failure": 1, "Follow-Up": 1}
    assert module.weak_spots(rows, module.expected_parent_counts(rows)) == []
    assert (
        module.run_completion_label(
            rows,
            counts,
            first_pass_clean=True,
            failed_or_weak=0,
            expected_parents=module.expected_parent_counts(rows),
        )
        == "FULL"
    )
    assert module.visible_completion_label("FULL", "compact") == "PARTIAL"
    assert module.visible_completion_label("FULL", "full") == "FULL"


def test_wizard_compile_output_v42_names_usefulness_blockers(tmp_path) -> None:
    module = _load_module(
        "wizard_compile_output_v4_2_usefulness_blockers_under_test",
        REPO_ROOT / "scripts" / "wizard_compile_output_v4_2.py",
    )
    receipt_path = tmp_path / "matrix_receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "groups": [
                    {
                        "model": "sonnet",
                        "usefulness_failures": [
                            {"id": "child-1", "status": "timed_out"},
                            {"id": "child-2", "status": "failed"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    rows = [{"route": "failure.loophole_auditor", "receipt_path": str(receipt_path), "degraded": []}]

    spots = module.weak_spots(rows, {"Failure": 1})

    assert "failure.loophole_auditor had 2 usefulness-blocked child receipts, including 1 timed out." in spots


def test_wizard_compile_output_v42_exposes_exact_blockers_and_repair_command(tmp_path) -> None:
    module = _load_module(
        "wizard_compile_output_v4_2_exact_blockers_under_test",
        REPO_ROOT / "scripts" / "wizard_compile_output_v4_2.py",
    )
    receipt_path = tmp_path / "matrix_receipt.json"
    receipt_path.write_text(
        json.dumps(
            {
                "route": "failure.loophole_auditor",
                "run_id": "test-run",
                "parent_prompt": "repair this route",
                "active_formal_child_obligation": ["skill.loophole_auditor"],
                "formal_child_obligation": ["skill.loophole_auditor"],
                "followup": {
                    "prompt": "next",
                    "payoff": "restore route",
                    "use_when": "partial route",
                    "stop_if": "still blocked",
                    "boundary": "tmp only",
                },
                "child_rerouter": {
                    "quality_blockers": {
                        "blocking_usefulness_failures": [
                            {
                                "id": "failure.loophole_auditor-skill-loophole-auditor-sonnet-1",
                                "status": "timed_out",
                                "reason": "child_not_completed",
                            }
                        ]
                    }
                },
                "groups": [],
            }
        ),
        encoding="utf-8",
    )
    rows = [
        {
            "route": "failure.loophole_auditor",
            "status": "partial",
            "receipt_path": str(receipt_path),
            "missing_formal": ["skill.loophole_auditor"],
            "agents_failed_or_weak": 1,
        }
    ]

    details = module.route_blocker_details(rows, REPO_ROOT)

    assert details[0]["failures"][0]["id"] == "failure.loophole_auditor-skill-loophole-auditor-sonnet-1"
    assert "--only-children skill.loophole_auditor" in details[0]["repair_command"]
    assert "scripts/wizard_child_matrix.py" in details[0]["repair_command"]
    assert module.compact_profile_match_summary("audit", "audit route truth overclaim") == (
        "auto matched `audit` from: `audit`, `overclaim`, `route truth`"
    )


def test_wizard_compile_output_v42_parses_partial_status_json(monkeypatch, tmp_path) -> None:
    module = _load_module(
        "wizard_compile_output_v4_2_partial_status_under_test",
        REPO_ROOT / "scripts" / "wizard_compile_output_v4_2.py",
    )

    class Result:
        returncode = 1
        stdout = json.dumps({"members": [{"route": "failure.loophole_auditor", "status": "partial"}]})

    monkeypatch.setattr(module.subprocess, "run", lambda *_args, **_kwargs: Result())

    assert module.status_json(tmp_path, REPO_ROOT)["members"][0]["status"] == "partial"


def test_wizard_council_receipt_marks_matrix_lanes_disabled_when_skipped(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_skip_lane_truth_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )

    path = module.write_council_receipts(
        tmp_path,
        iteration=1,
        decision={"action": "draft_or_repair_packets_parallel"},
        premortem={"ok": True},
        external={},
        matrix_enabled=False,
        gemini_enabled=True,
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))

    assert receipt["child_skill_lanes"] == ["tool:helper_process_audit.py"]
    assert "claude-bridge:sonnet-high" in receipt["disabled_skill_lanes"]
    assert "claude-bridge:opus-audit" in receipt["disabled_skill_lanes"]
    assert "gemini:audit" in receipt["disabled_skill_lanes"]
    assert "claude-bridge:haiku" in receipt["disabled_skill_lanes"]
    assert receipt["parent_skill_lanes"] == ["codex-autoresearch", "tool:preflight"]
    assert "premortem" in receipt["disabled_parent_skill_lanes"]
    assert "claude-bridge" in receipt["disabled_parent_skill_lanes"]
    assert "cdo" in receipt["disabled_parent_skill_lanes"]
    assert receipt["parent_receipts"]["failure"]["status"] == "skipped"
    assert receipt["parent_receipts"]["follow_up"]["status"] == "deferred"
    assert receipt["management_parents"] == ["manager_rerouter", "sim_loop_state_gate"]
    assert "route_truth_join" in receipt["disabled_management_parents"]
    assert "premortem_follow_up_join_gate" in receipt["disabled_management_parents"]
    assert receipt["run_mode"] == {
        "matrix_enabled": False,
        "gemini_enabled": False,
        "haiku_enabled": False,
        "matrix_route_count": 0,
        "matrix_all_accepted": False,
    }


def test_wizard_council_receipt_summarizes_per_route_model_statuses(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_matrix_summary_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )

    path = module.write_council_receipts(
        tmp_path,
        iteration=1,
        decision={"action": "draft_or_repair_packets_parallel"},
        premortem={"ok": True},
        external={},
        matrix_receipts={
            "failure.premortem": {
                "status": "accepted",
                "counts": {"accepted_children": 2, "sonnet_completed": 0, "opus_completed": 1, "gemini_completed": 1},
                "model_family_statuses": {"sonnet": "blocked", "opus": "completed", "gemini": "completed", "haiku": "disabled"},
                "receipt_path": "/tmp/failure/matrix_receipt.json",
            }
        },
        gemini_enabled=True,
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))
    summary = receipt["matrix_route_summaries"]["failure.premortem"]

    assert summary["status"] == "accepted"
    assert summary["counts"]["accepted_children"] == 2
    assert summary["model_family_statuses"]["sonnet"] == "blocked"
    assert summary["model_family_statuses"]["opus"] == "completed"
    assert summary["receipt_path"] == "/tmp/failure/matrix_receipt.json"


def test_wizard_council_receipt_blocks_followup_when_any_matrix_route_fails(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_matrix_followup_gate_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )

    path = module.write_council_receipts(
        tmp_path,
        iteration=1,
        decision={"action": "draft_or_repair_packets_parallel"},
        premortem={"ok": True},
        external={},
        matrix_receipts={
            "failure.premortem": {"status": "accepted"},
            "manager.route_truth": {"status": "failed"},
        },
        gemini_enabled=True,
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))

    assert receipt["parent_receipts"]["failure"]["status"] == "completed"
    assert receipt["parent_receipts"]["follow_up"]["status"] == "blocked"
    assert receipt["matrix_route_summaries"]["manager.route_truth"]["status"] == "failed"


def test_wizard_council_receipt_blocks_failure_when_premortem_route_fails(tmp_path) -> None:
    module = _load_module(
        "wizard_autoresearch_sim_loop_failure_gate_under_test",
        REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py",
    )

    path = module.write_council_receipts(
        tmp_path,
        iteration=1,
        decision={"action": "draft_or_repair_packets_parallel"},
        premortem={"ok": True},
        external={},
        matrix_receipts={"failure.premortem": {"status": "failed"}},
        gemini_enabled=True,
    )
    receipt = json.loads(path.read_text(encoding="utf-8"))

    assert receipt["parent_receipts"]["failure"]["status"] == "blocked"
    assert receipt["parent_receipts"]["follow_up"]["status"] == "blocked"
    assert receipt["matrix_route_summaries"]["failure.premortem"]["status"] == "failed"


def test_wizard_autoresearch_loop_writes_v41_receipt_shape() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")
    assert "wizard_council_receipt" in text
    assert "parent_receipts" in text
    assert "child_receipts" in text
    assert "management_parents" in text
    assert "manager_rerouter" in text
    assert "sim_loop_state_gate" in text
    assert "route_truth_join" in text
    assert "premortem_follow_up_join_gate" in text


def test_wizard_autoresearch_loop_can_bind_external_native_parent_receipts() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")
    assert "--external-council-receipts" in text
    assert "load_external_council_receipts" in text
    assert "external_native_parent_receipts" in text
    assert "external_native_child_receipts" in text
    assert "native_codex_parent" in text
    assert "mass_parent_child_fanout_boundary" in text


def test_wizard_autoresearch_loop_does_not_count_artifact_proxies_as_native_children() -> None:
    text = (REPO_ROOT / "scripts" / "wizard_autoresearch_sim_loop.py").read_text(encoding="utf-8")
    assert "artifact_proxy_receipts" in text
    assert "accepted_artifact_proxy_receipt_ids" in text
    assert "validated_native_child_ids" in text
    assert "is_native_codex_receipt" in text
    assert '"children": f"{len(native_child_ids)' in text
    assert '"accepted_child_receipt_ids": native_child_ids' in text
    assert "counts_as_native_codex_child" in text


def _valid_wizard_admission_payload(
    *,
    repo: Path,
    basename: str,
    sim_path: str,
    artifact: Path,
) -> dict:
    return {
        "schema": "wizard_sim_admission_v4_2",
        "basename": basename,
        "sim_path": sim_path,
        "status": "queue_ready",
        "admitted_by": "guard.receipt_audit",
        "admission_artifact": str(artifact),
        "controller_read_artifacts": [
            str(artifact),
            str(repo / "system_v4/probes/a2_state/sim_results" / f"{basename}_results.json"),
        ],
        "bounded_work_compile_gate": {"status": "ready_for_execution"},
        "sim_packet_compile_gate": {"status": "queue_candidate"},
        "sim_admissibility_gate": {"result": "one_exact_packet"},
        "formal_sim_profile": {
            "stage": "micro",
            "claim": "one bounded claim",
            "carrier_fixture": "fixture_a",
            "exact_tool_or_function": "tool.fn",
            "positive_check": "accepts good fixture",
            "negative_or_boundary_check": "rejects boundary fixture",
            "expected_result_path": str(repo / "system_v4/probes/a2_state/sim_results" / f"{basename}_results.json"),
        },
        "management_parent_surfaces": [
            "queue_liveness",
            "runner_preflight",
            "sim_admissibility",
            "queue_readiness",
            "formal_sim_profile",
            "stage_gate",
            "expected_result_surface",
            "controller_read_artifacts",
        ],
        "packet_contract": {
            "type": "MICRO",
            "tool_target": "tool",
            "function_surface": "tool.fn",
            "micro_claim": "one bounded claim",
            "lego_target": "fixture_a",
            "function_receipt": "new",
            "prior_function_receipts": [],
            "why_this_lego": "the fixture exposes exactly one function surface",
            "positive_case": "accepts good fixture",
            "negative_case": "rejects bad fixture",
            "boundary_case": "checks the boundary fixture",
            "demotion_condition": "demote if the function fails this fixture",
            "out_of_scope": ["no lego promotion", "no coupling claim"],
            "claim_ceiling": "tool_function_micro_only",
            "next_lego_target": "none",
            "promotion_condition": "requires later admitted row",
            "blocked_until": "exact downstream packet and parent receipts are reconciled",
            "promotion_boundary": "no promotion without a later admitted packet",
        },
    }


def _write_allow_stage_gate(repo: Path) -> None:
    stage_gate = repo / "scripts" / "stage_gate.py"
    stage_gate.parent.mkdir(parents=True, exist_ok=True)
    stage_gate.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
    stage_gate.chmod(0o755)


def test_wizard_sim_admission_rejects_runner_self_promotion(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["admitted_by"] = "runner"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "admitted_by_not_independent" in findings


def test_wizard_sim_admission_accepts_exact_queue_ready_packet(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_valid_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    admission_dir = repo / "system_v5" / "ops" / "wizard_admissions"
    admission_dir.mkdir(parents=True)
    admission_path = admission_dir / "sim_probe_object.json"
    admission_path.write_text(
        json.dumps(
            _valid_wizard_admission_payload(
                repo=repo,
                basename="sim_probe_object",
                sim_path="system_v4/probes/sim_probe_object.py",
                artifact=artifact,
            )
        ),
        encoding="utf-8",
    )

    report = module.load_and_validate(
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert report["ok"] is True
    assert report["path"] == str(admission_path)


def test_wizard_sim_admission_rejects_legacy_v41_without_recovery_flag(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_legacy_schema_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["schema"] = "wizard_sim_admission_v4_1"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "schema_legacy_v4_1_requires_explicit_recovery" in findings


def test_wizard_sim_admission_accepts_legacy_v41_with_recovery_flag(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_legacy_recovery_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["schema"] = "wizard_sim_admission_v4_1"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        allow_legacy_v4_1=True,
    )

    assert "schema_legacy_v4_1_requires_explicit_recovery" not in findings
    assert findings == []


def test_wizard_sim_admission_path_only_matches_runner_call(tmp_path) -> None:
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    admission_dir = repo / "system_v5" / "ops" / "wizard_admissions"
    admission_dir.mkdir(parents=True)
    admission_path = admission_dir / "sim_probe_object.json"
    admission_path.write_text(
        json.dumps(
            _valid_wizard_admission_payload(
                repo=repo,
                basename="sim_probe_object",
                sim_path="system_v4/probes/sim_probe_object.py",
                artifact=artifact,
            )
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "wizard_sim_admission.py"),
            "--repo-root",
            str(repo),
            "--basename",
            "sim_probe_object",
            "--sim-path",
            "system_v4/probes/sim_probe_object.py",
            "--path-only",
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert proc.returncode == 0
    assert proc.stdout.strip() == str(admission_path)
    assert proc.stderr == ""


def test_wizard_sim_admission_rejects_profile_without_packet_contract(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_no_packet_contract_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload.pop("packet_contract")

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "missing_packet_contract" in findings


def test_wizard_sim_admission_rejects_coupling_without_exact_parent_results(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_parent_receipts_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["stage"] = "integration_micro"
    payload["packet_contract"]["type"] = "INTEGRATION_MICRO"
    payload["packet_contract"]["micro_claim"] = "couple two exact function surfaces"
    payload["packet_contract"]["function_receipt"] = "system_v4/probes/a2_state/sim_results/parent_a_results.json"
    payload["packet_contract"]["prior_function_receipts"] = ["parent_a"]

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "packet_contract_parent_receipts_not_exact_result_paths" in findings


def test_wizard_sim_admission_rejects_missing_parent_result_artifact(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_missing_parent_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["stage"] = "integration_micro"
    payload["packet_contract"]["type"] = "INTEGRATION_MICRO"
    payload["packet_contract"]["micro_claim"] = "couple two exact function surfaces"
    payload["packet_contract"]["function_receipt"] = "system_v4/probes/a2_state/sim_results/parent_a_results.json"
    payload["packet_contract"]["prior_function_receipts"] = [
        "system_v4/probes/a2_state/sim_results/parent_a_results.json"
    ]

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "packet_contract_parent_receipt_missing" in findings


def test_wizard_sim_admission_rejects_parent_result_hash_mismatch(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_parent_hash_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    parent = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "parent_a_results.json"
    parent.parent.mkdir(parents=True)
    parent.write_text(
        json.dumps(
            {
                "name": "parent_a",
                "classification": "canonical",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "parent function"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if parent fails",
                "out_of_scope": ["no coupling promotion"],
                "claim_ceiling": "parent_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires downstream packet",
                "blocked_until": "child cites current hash",
            }
        ),
        encoding="utf-8",
    )
    prior = "system_v4/probes/a2_state/sim_results/parent_a_results.json"
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["stage"] = "integration_micro"
    payload["packet_contract"]["type"] = "INTEGRATION_MICRO"
    payload["packet_contract"]["micro_claim"] = "couple two exact function surfaces"
    payload["packet_contract"]["function_receipt"] = prior
    payload["packet_contract"]["prior_function_receipts"] = [prior]
    payload["packet_contract"]["parent_receipt_sha256"] = {prior: "not-the-current-hash"}

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "packet_contract_parent_receipt_hash_mismatch" in findings


def test_wizard_sim_admission_rejects_noncanonical_parent_receipt(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_parent_classification_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    parent = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "parent_a_results.json"
    parent.parent.mkdir(parents=True)
    parent.write_text(
        json.dumps(
            {
                "name": "parent_a",
                "classification": "classical_baseline",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "baseline function"}},
                "tool_integration_depth": {"z3": "load_bearing"},
                "divergence_log": "classical baseline only",
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if parent fails",
                "out_of_scope": ["no coupling promotion"],
                "claim_ceiling": "parent_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires downstream packet",
                "blocked_until": "child cites current hash",
            }
        ),
        encoding="utf-8",
    )
    prior = "system_v4/probes/a2_state/sim_results/parent_a_results.json"
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["stage"] = "integration_micro"
    payload["packet_contract"]["type"] = "INTEGRATION_MICRO"
    payload["packet_contract"]["micro_claim"] = "couple two exact function surfaces"
    payload["packet_contract"]["function_receipt"] = prior
    payload["packet_contract"]["prior_function_receipts"] = [prior]
    payload["packet_contract"]["parent_receipt_sha256"] = {
        prior: __import__("hashlib").sha256(parent.read_bytes()).hexdigest()
    }

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "packet_contract_parent_receipt_not_canonical" in findings


def test_wizard_sim_admission_rejects_stage_above_stage_gate(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_stage_gate_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    stage_gate = repo / "scripts" / "stage_gate.py"
    stage_gate.parent.mkdir(parents=True)
    stage_gate.write_text("#!/usr/bin/env python3\nraise SystemExit(1)\n", encoding="utf-8")
    stage_gate.chmod(0o755)
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["stage"] = "qit"
    payload["packet_contract"] = {
        "type": "QIT",
        "tool_target": "sympy",
        "integration_question": "can this QIT engine claim advance",
        "anchor_lego": "qit_micro",
        "why_this_lego": "tests an advanced engine claim",
        "loopback_target": "qit_engine_index",
        "expected_outcome_classification": "blocked",
        "bound_exit_condition": "stage gate must allow engine",
        "out_of_scope": ["no promotion while stage gate is red"],
        "prior_function_receipts": ["system_v4/probes/a2_state/sim_results/parent_a_results.json"],
        "parent_receipt_sha256": {"system_v4/probes/a2_state/sim_results/parent_a_results.json": "abc"},
        "claim_ceiling": "qit_engine",
        "promotion_condition": "stage gate allows engine",
        "blocked_until": "active stage reaches coupling/engine",
    }

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
    )

    assert "stage_gate_rejects_engine" in findings


def test_wizard_sim_admission_rejects_micro_when_stage_gate_missing(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_missing_micro_stage_gate_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "stage_gate_missing_for_tool_micro" in findings


def test_wizard_sim_admission_rejects_advanced_stage_when_stage_gate_missing(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_missing_stage_gate_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["stage"] = "qit"
    payload["packet_contract"] = {
        "type": "QIT",
        "tool_target": "sympy",
        "integration_question": "can this QIT engine claim advance",
        "anchor_lego": "qit_micro",
        "why_this_lego": "tests an advanced engine claim",
        "loopback_target": "qit_engine_index",
        "expected_outcome_classification": "blocked",
        "bound_exit_condition": "stage gate must allow engine",
        "out_of_scope": ["no promotion while stage gate is missing"],
        "prior_function_receipts": ["system_v4/probes/a2_state/sim_results/parent_a_results.json"],
        "parent_receipt_sha256": {"system_v4/probes/a2_state/sim_results/parent_a_results.json": "abc"},
        "claim_ceiling": "qit_engine",
        "promotion_condition": "stage gate allows engine",
        "blocked_until": "active stage reaches coupling/engine",
    }

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
    )

    assert "stage_gate_missing_for_engine" in findings


def test_wizard_sim_admission_rejects_advanced_stage_without_packet_contract(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_advanced_stage_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["stage"] = "qit"
    payload.pop("packet_contract")

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "missing_packet_contract" in findings


def test_wizard_sim_admission_rejects_noncanonical_expected_result_path(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_expected_result_path_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = "tmp/result.json"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "formal_sim_profile_expected_result_path_not_canonical" in findings


def test_wizard_sim_admission_rejects_stale_result_hash_artifact(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_stale_artifact_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_probe_object_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text('{"result":"current"}\n', encoding="utf-8")
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps({"result_path": str(result_path), "result_sha256": "stale-hash"}),
        encoding="utf-8",
    )
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "admission_artifact_result_sha256_mismatch" in findings


def test_wizard_sim_admission_rejects_existing_result_without_artifact_hash(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_missing_artifact_hash_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_probe_object_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text('{"result":"current"}\n', encoding="utf-8")
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "admission_artifact_missing_result_path" in findings
    assert "admission_artifact_missing_result_sha256" in findings


def test_wizard_sim_admission_rejects_controller_read_missing_bound_artifacts(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_controller_read_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_probe_object_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text('{"result":"current"}\n', encoding="utf-8")
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps(
            {
                "result_path": str(result_path),
                "result_sha256": __import__("hashlib").sha256(result_path.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["controller_read_artifacts"] = ["other.json"]

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "controller_read_artifacts_missing_admission_artifact" in findings
    assert "controller_read_artifacts_missing_expected_result" in findings


def test_wizard_sim_admission_requires_promotion_boundary(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_promotion_boundary_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["packet_contract"].pop("promotion_boundary")

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "packet_contract_missing_promotion_boundary" in findings


def test_queue_claim_blocks_strict_wizard_admission_without_artifact(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "queue_claim_wizard_admission_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "QUEUE_ROOT", queue_root)
    monkeypatch.setattr(module, "STRICT_WIZARD_QUEUE_ADMISSION", True)

    terminal = module.enqueue("lane_A", "system_v4/probes/sim_probe_object.py")

    assert terminal.parent.name == "blocked"
    payload = json.loads(terminal.read_text(encoding="utf-8"))
    assert payload["blocked_reason"] == "wizard_admission_blocked"


def test_queue_claim_claim_rechecks_wizard_admission_even_when_enqueue_relaxed(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "queue_claim_wizard_claim_gate_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "QUEUE_ROOT", queue_root)
    monkeypatch.setattr(module, "STRICT_WIZARD_QUEUE_ADMISSION", False)
    monkeypatch.setattr(module, "CLAIM_REQUIRES_WIZARD_QUEUE_ADMISSION", True)

    queued = module.enqueue("lane_A", "system_v4/probes/sim_probe_object.py")
    assert queued.parent.name == "lane_A"

    claimed = module.claim("lane_A", "w1")

    assert claimed is None
    blocked = list((queue_root / "blocked").glob("*.json*"))
    assert len(blocked) == 1
    payload = json.loads(blocked[0].read_text(encoding="utf-8"))
    assert payload["blocked_reason"] == "wizard_admission_blocked"


def test_qit_engine_evidence_index_blocks_unadmitted_qit_results(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)
    (probes / "sim_qit_probe.py").write_text("# fixture\n", encoding="utf-8")
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    result_path = results / "sim_qit_probe_results.json"
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "exact fixture check"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "wizard admission exists",
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    assert index["summary"]["total_entries"] == 1
    assert index["summary"]["scanned_result_count"] == 1
    assert index["summary"]["qit_signal_result_count"] == 1
    assert "qit" in index["qit_signal_filter"]["tokens"]
    assert "claim_ceiling" in index["qit_signal_filter"]["fields"]
    assert index["scan_sample"]["scanned_result_files"] == ["sim_qit_probe_results.json"]
    assert index["scan_sample"]["qit_signal_result_files"] == ["sim_qit_probe_results.json"]
    assert index["summary"]["candidate_entries"] == 0
    assert index["summary"]["quarantine_entries"] == 1
    assert index["operational_status"] == "blocked_no_accepted_qit_entries"
    assert index["status_reason"] == "qit_entries_blocked"
    assert len(index["candidate_entries"]) == 0
    assert len(index["quarantine_entries"]) == 1
    entry = index["entries"][0]
    assert entry["status"] == "blocked"
    assert entry["admission_status"] == "missing_or_invalid"
    assert entry["receipt_schema_ok"] is True
    assert any(item.startswith("admission:") for item in entry["blockers"])
    assert index["next_acceptance_targets"][0]["basename"] == "sim_qit_probe"
    assert index["next_acceptance_targets"][0]["next_action"] == "create_or_repair_wizard_sim_admission"


def test_qit_engine_evidence_index_requires_source_binding_before_admission(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_source_binding_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    (results / "lego_07_results.json").write_text(
        json.dumps(
            {
                "name": "lego_07",
                "classification": "canonical",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "exact qit fixture check"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "wizard admission exists",
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    assert index["next_acceptance_targets"][0]["next_action"] == "repair_or_bind_source_probe_before_admission"


def test_qit_engine_evidence_index_blocks_bridge_numpy_and_nonclassical_without_pytorch(
    tmp_path,
) -> None:
    module = _load_module(
        "qit_engine_evidence_index_tool_policy_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    for stem in ("sim_qit_bridge_numpy", "sim_qit_bridge_numpy_dot", "sim_qit_nonclassical_z3"):
        (probes / f"{stem}.py").write_text("# fixture\n", encoding="utf-8")
    base = {
        "classification": "canonical",
        "summary": {"tests_passed": 1, "tests_total": 1},
        "positive": {"passed": True},
        "negative": {"passed": True},
        "boundary": {"passed": True},
        "demotion_condition": "demote if fixture fails",
        "out_of_scope": ["no engine promotion"],
        "claim_ceiling": "qit_micro_only",
        "next_lego_target": "none",
        "promotion_condition": "requires admitted downstream packet",
        "blocked_until": "wizard admission exists",
    }
    (results / "sim_qit_bridge_numpy_results.json").write_text(
        json.dumps(
            {
                "name": "sim_qit_bridge_numpy",
                "sim_execution_kind": "bridge",
                "tool_manifest": {"np.linalg": {"tried": True, "used": True, "reason": "blocked bridge fixture"}},
                "tool_integration_depth": {"np.linalg": "load_bearing"},
                **base,
            }
        ),
        encoding="utf-8",
    )
    (results / "sim_qit_bridge_numpy_dot_results.json").write_text(
        json.dumps(
            {
                "name": "sim_qit_bridge_numpy_dot",
                "sim_execution_kind": "bridge",
                "tool_manifest": {"numpy.linalg": {"tried": True, "used": True, "reason": "blocked bridge fixture"}},
                "tool_integration_depth": {"numpy.linalg": "load_bearing"},
                **base,
            }
        ),
        encoding="utf-8",
    )
    (results / "sim_qit_nonclassical_z3_results.json").write_text(
        json.dumps(
            {
                "name": "sim_qit_nonclassical_z3",
                "sim_execution_kind": "nonclassical",
                "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "missing pytorch fixture"}},
                "tool_integration_depth": {"z3": "load_bearing"},
                **base,
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)
    blockers = {entry["basename"]: entry["blockers"] for entry in index["entries"]}
    targets = {row["basename"]: row["next_action"] for row in index["next_acceptance_targets"]}

    assert "result:numpy_load_bearing_blocked_for_bridge_or_nonclassical" in blockers["sim_qit_bridge_numpy"]
    assert "result:numpy_load_bearing_blocked_for_bridge_or_nonclassical" in blockers["sim_qit_bridge_numpy_dot"]
    assert "result:nonclassical_requires_load_bearing_pytorch" in blockers["sim_qit_nonclassical_z3"]
    assert targets["sim_qit_bridge_numpy"] == "repair_tool_policy_before_any_admission"
    assert targets["sim_qit_bridge_numpy_dot"] == "repair_tool_policy_before_any_admission"
    assert targets["sim_qit_nonclassical_z3"] == "repair_tool_policy_before_any_admission"


def test_qit_engine_evidence_index_blocks_qit_like_canonical_missing_execution_kind(
    tmp_path,
) -> None:
    module = _load_module(
        "qit_engine_evidence_index_execution_kind_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    (probes / "sim_qit_density_numpy.py").write_text("# fixture\n", encoding="utf-8")
    (results / "sim_qit_density_numpy_results.json").write_text(
        json.dumps(
            {
                "name": "sim_qit_density_numpy",
                "classification": "canonical",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"numpy": {"tried": True, "used": True, "reason": "ambiguous qit fixture"}},
                "tool_integration_depth": {"numpy": "load_bearing"},
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_density_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)
    blockers = {entry["basename"]: entry["blockers"] for entry in index["entries"]}

    assert "result:qit_execution_kind_missing" in blockers["sim_qit_density_numpy"]


def test_qit_engine_evidence_index_can_skip_external_scan(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_skip_external_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)

    index = module.build_index(repo, include_external_scan=False)

    assert index["out_of_scope_qit_result_scan"]["status"] == "external_scan_skipped"
    assert index["out_of_scope_qit_result_scan"]["triage"]["triage_boundary"] == (
        "external_scan_skipped_run_without_skip_external_scan_for_diagnostics"
    )


def test_qit_engine_evidence_index_accepts_uppercase_tool_contract_fields(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_uppercase_contract_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    (results / "sim_qit_probe_results.json").write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "TOOL_MANIFEST": {"z3": {"tried": True, "used": True, "reason": "uppercase fixture"}},
                "TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing"},
                "claim_ceiling": "qit_micro_only",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "wizard admission exists",
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    assert index["summary"]["total_entries"] == 1
    assert index["entries"][0]["receipt_schema_ok"] is True
    assert "result:receipt_schema_incomplete" not in index["entries"][0]["blockers"]


def test_qit_engine_evidence_index_prioritizes_source_bound_admission_targets(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_target_priority_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)
    (probes / "sim_qit_probe.py").write_text("# fixture\n", encoding="utf-8")
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    base_payload = {
        "classification": "canonical",
        "summary": {"tests_passed": 1, "tests_total": 1},
        "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "exact qit fixture check"}},
        "tool_integration_depth": {"sympy": "load_bearing"},
        "positive": {"passed": True},
        "negative": {"passed": True},
        "boundary": {"passed": True},
        "demotion_condition": "demote if fixture fails",
        "out_of_scope": ["no engine promotion"],
        "claim_ceiling": "qit_micro_only",
        "next_lego_target": "none",
        "promotion_condition": "requires admitted downstream packet",
        "blocked_until": "wizard admission exists",
    }
    (results / "aaa_unbound_qit_results.json").write_text(
        json.dumps({"name": "aaa_unbound_qit", **base_payload}),
        encoding="utf-8",
    )
    (results / "sim_qit_probe_results.json").write_text(
        json.dumps({"name": "sim_qit_probe", **base_payload}),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    first_target = index["next_acceptance_targets"][0]
    assert first_target["basename"] == "sim_qit_probe"
    assert first_target["sim_path"] == "system_v4/probes/sim_qit_probe.py"
    assert first_target["next_action"] == "create_or_repair_wizard_sim_admission"
    targets_by_basename = {target["basename"]: target for target in index["next_acceptance_targets"]}
    assert targets_by_basename["aaa_unbound_qit"]["next_action"] == "repair_or_bind_source_probe_before_admission"


def test_qit_engine_evidence_index_accepts_strict_result_with_wizard_admission(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_accept_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)
    (probes / "sim_qit_probe.py").write_text("# fixture\n", encoding="utf-8")
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    result_path = results / "sim_qit_probe_results.json"
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "exact structural fixture check"}},
                "tool_integration_depth": {"z3": "load_bearing"},
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps(
            {
                "result_path": str(result_path),
                "result_sha256": __import__("hashlib").sha256(result_path.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    admission_dir = repo / "system_v5" / "ops" / "wizard_admissions"
    admission_dir.mkdir(parents=True)
    admission = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
        artifact=artifact,
    )
    admission["formal_sim_profile"]["expected_result_path"] = str(result_path)
    admission["formal_sim_profile"]["exact_tool_or_function"] = "z3.Solver.check"
    admission["packet_contract"]["tool_target"] = "z3"
    admission["packet_contract"]["function_surface"] = "z3.Solver.check"
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    payload["positive"] = {"passed": True, "function_surface": "z3.Solver.check"}
    result_path.write_text(json.dumps(payload), encoding="utf-8")
    import hashlib
    artifact.write_text(
        json.dumps({"result_path": str(result_path), "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}),
        encoding="utf-8",
    )
    admission_path = admission_dir / "sim_qit_probe.json"
    admission_path.write_text(json.dumps(admission), encoding="utf-8")

    index = module.build_index(repo)

    assert index["summary"]["accepted"] == 1
    assert index["summary"]["scanned_result_count"] == 1
    assert index["summary"]["qit_signal_result_count"] == 1
    assert index["scan_sample"]["qit_signal_result_files"] == ["sim_qit_probe_results.json"]
    assert index["summary"]["admitted_micro_entries"] == 1
    assert index["summary"]["candidate_entries"] == 1
    assert index["summary"]["quarantine_entries"] == 0
    assert index["operational_status"] == "has_accepted_qit_entry"
    assert index["status_reason"] == "accepted_qit_entries_present"
    assert index["next_acceptance_targets"] == []
    entry = index["entries"][0]
    assert entry["status"] == "accepted"
    assert entry["admission_status"] == "admitted"
    assert entry["admission_artifact"] == str(admission_path)
    assert entry["parent_receipt_sha256"] == {}
    assert entry["tool_function_ancestry"]["tool_target"] == "z3"
    assert entry["tool_function_ancestry"]["function_surface"] == "z3.Solver.check"
    assert entry["result_sha256"]


def test_qit_engine_evidence_index_accepts_payload_named_result_with_strict_admission(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_payload_named_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)
    (probes / "sim_z3_capability.py").write_text("# fixture\n", encoding="utf-8")
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    result_path = results / "z3_capability_results.json"
    result_path.write_text(
        json.dumps(
                {
                    "name": "sim_z3_capability",
                    "classification": "canonical",
                    "all_pass": True,
                    "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "capability fixture"}},
                "tool_integration_depth": {"z3": "load_bearing"},
                "positive": {"passed": True, "function_surface": "z3.Solver.check"},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "tool_micro_z3_capability_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    import hashlib

    artifact = repo / "system_v5" / "ops" / "wizard_admission_receipts" / "sim_z3_capability_admission_artifact.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps({"result_path": str(result_path), "result_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest()}),
        encoding="utf-8",
    )
    admission_dir = repo / "system_v5" / "ops" / "wizard_admissions"
    admission_dir.mkdir(parents=True)
    admission = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_z3_capability",
        sim_path="system_v4/probes/sim_z3_capability.py",
        artifact=artifact,
    )
    admission["admission_artifact"] = str(artifact.relative_to(repo))
    admission["controller_read_artifacts"] = [str(artifact.relative_to(repo)), str(result_path)]
    admission["formal_sim_profile"]["expected_result_path"] = str(result_path)
    admission["formal_sim_profile"]["claim"] = "tool_micro_z3_capability_only"
    admission["formal_sim_profile"]["exact_tool_or_function"] = "z3.Solver.check"
    admission["packet_contract"]["tool_target"] = "z3"
    admission["packet_contract"]["function_surface"] = "z3.Solver.check"
    admission["packet_contract"]["claim_ceiling"] = "tool_micro_z3_capability_only"
    admission["packet_contract"]["micro_claim"] = "tool_micro_z3_capability_only"
    admission_path = admission_dir / "sim_z3_capability.json"
    admission_path.write_text(json.dumps(admission), encoding="utf-8")

    index = module.build_index(repo)

    assert index["summary"]["accepted"] == 1
    entry = index["entries"][0]
    assert entry["basename"] == "sim_z3_capability"
    assert entry["result_path"] == str(result_path)
    assert entry["status"] == "accepted"
    assert entry["admission_artifact"] == str(admission_path)


def test_qit_engine_evidence_index_does_not_rerun_already_admitted_duplicate(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_duplicate_admitted_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)
    source = probes / "sim_qit_probe.py"
    source.write_text("# repaired source newer than duplicate result\n", encoding="utf-8")
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    canonical_result = results / "sim_qit_probe_results.json"
    payload = {
        "name": "sim_qit_probe",
        "classification": "canonical",
        "all_pass": True,
        "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "qit fixture"}},
        "tool_integration_depth": {"z3": "load_bearing"},
        "positive": {"passed": True, "function_surface": "z3.Solver.check"},
        "negative": {"passed": True},
        "boundary": {"passed": True},
        "demotion_condition": "demote if fixture fails",
        "out_of_scope": ["no engine promotion"],
        "claim_ceiling": "qit_micro_only",
        "next_lego_target": "none",
        "promotion_condition": "requires admitted downstream packet",
        "blocked_until": "controller acceptance",
    }
    canonical_result.write_text(json.dumps(payload), encoding="utf-8")
    duplicate_result = probes / "sim_qit_probe_results.json"
    duplicate_result.write_text(json.dumps(payload), encoding="utf-8")
    import hashlib

    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps(
            {
                "result_path": str(canonical_result),
                "result_sha256": hashlib.sha256(canonical_result.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    admission_dir = repo / "system_v5" / "ops" / "wizard_admissions"
    admission_dir.mkdir(parents=True)
    admission = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
        artifact=artifact,
    )
    admission["formal_sim_profile"]["expected_result_path"] = str(canonical_result)
    admission["formal_sim_profile"]["exact_tool_or_function"] = "z3.Solver.check"
    admission["packet_contract"]["tool_target"] = "z3"
    admission["packet_contract"]["function_surface"] = "z3.Solver.check"
    (admission_dir / "sim_qit_probe.json").write_text(json.dumps(admission), encoding="utf-8")

    index = module.build_index(repo)

    assert index["summary"]["accepted"] == 1
    triage = index["out_of_scope_qit_result_scan"]["triage"]
    assert triage["bucket_counts"] == {"already_admitted_duplicate_reference": 1}
    assert triage["provisional_rerun_target_count"] == 0
    duplicate = triage["bucket_samples"]["already_admitted_duplicate_reference"][0]
    assert duplicate["next_action"] == "do_not_rerun_already_accepted_canonical_evidence"


def test_wizard_sim_admission_rejects_tool_target_not_load_bearing(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_tool_binding_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_probe_object_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_probe_object",
                "classification": "canonical",
                "all_pass": True,
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "fixture"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True, "function_surface": "sympy.simplify"},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no promotion"],
                "claim_ceiling": "micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires later packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = str(result_path)
    payload["packet_contract"]["tool_target"] = "z3"
    payload["packet_contract"]["function_surface"] = "z3.Solver.check"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "admission_artifact_tool_target_not_load_bearing" in findings


def test_wizard_sim_admission_reads_uppercase_tool_integration_depth(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_uppercase_depth_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_qit_probe_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "all_passed": True,
                "TOOL_MANIFEST": {"z3": {"tried": True, "used": True, "reason": "legacy uppercase fixture"}},
                "TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing"},
                "positive": {"passed": True, "function_surface": "z3.Solver.check"},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps({"result_path": str(result_path), "result_sha256": __import__("hashlib").sha256(result_path.read_bytes()).hexdigest()}),
        encoding="utf-8",
    )
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = str(result_path)
    payload["formal_sim_profile"]["exact_tool_or_function"] = "z3.Solver.check"
    payload["packet_contract"]["tool_target"] = "z3"
    payload["packet_contract"]["function_surface"] = "z3.Solver.check"
    payload["packet_contract"]["claim_ceiling"] = "qit_micro_only"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
    )

    assert "admission_artifact_tool_target_not_load_bearing" not in findings


def test_wizard_sim_admission_rejects_qit_canonical_without_nonclassical_tool(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_nonclassical_tool_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_qit_probe_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "all_pass": True,
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "symbolic fixture only"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True, "function_surface": "sympy.simplify"},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = str(result_path)
    payload["formal_sim_profile"]["claim"] = "QIT engine micro claim"
    payload["packet_contract"]["tool_target"] = "sympy"
    payload["packet_contract"]["function_surface"] = "sympy.simplify"
    payload["packet_contract"]["claim_ceiling"] = "qit_micro_only"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
    )

    assert "nonclassical_suitable_load_bearing_tool_missing" in findings


def test_wizard_sim_admission_rejects_hidden_coupling_result_without_nonclassical_tool(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_hidden_coupling_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_probe_object_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_probe_object",
                "classification": "classical_baseline",
                "all_pass": True,
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "symbolic fixture only"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True, "function_surface": "sympy.simplify"},
                "observables": {"rho_AB": 1, "Phi0": 0, "Xi": "coupling witness"},
                "divergence_log": "classical baseline only",
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = str(result_path)
    payload["packet_contract"]["tool_target"] = "sympy"
    payload["packet_contract"]["function_surface"] = "sympy.simplify"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "nonclassical_suitable_load_bearing_tool_missing" in findings


def test_wizard_sim_admission_hidden_signal_does_not_match_substrings(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_hidden_substring_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    sim_path = repo / "system_v4" / "probes" / "sim_symbolic_exact.py"
    sim_path.parent.mkdir(parents=True)
    sim_path.write_text(
        "def explain():\n    return 'explicit matrix symbolic fixture'\n",
        encoding="utf-8",
    )

    assert not module._has_hidden_nonclassical_signal(
        repo,
        "system_v4/probes/sim_symbolic_exact.py",
        {"note": "explicit matrix symbolic fixture"},
    )


def test_wizard_sim_admission_accepts_nonclassical_tool_family_suffix(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_tool_family_suffix_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_qit_probe_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "all_pass": True,
                "tool_manifest": {"z3.solver": {"tried": True, "used": True, "reason": "exact fixture"}},
                "tool_integration_depth": {"z3.solver": "load_bearing"},
                "positive": {"passed": True, "function_surface": "z3.Solver.check"},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = str(result_path)
    payload["formal_sim_profile"]["claim"] = "QIT engine micro claim"
    payload["packet_contract"]["tool_target"] = "z3.solver"
    payload["packet_contract"]["function_surface"] = "z3.Solver.check"
    payload["packet_contract"]["claim_ceiling"] = "qit_micro_only"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
    )

    assert "nonclassical_suitable_load_bearing_tool_missing" not in findings


def test_wizard_sim_admission_rejects_nonclassical_z3_without_pytorch(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_nonclassical_pytorch_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_nonclassical_probe_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_nonclassical_probe",
                "classification": "canonical",
                "sim_execution_kind": "nonclassical",
                "all_pass": True,
                "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "formal check only"}},
                "tool_integration_depth": {"z3": "load_bearing"},
                "positive": {"passed": True, "function_surface": "z3.Solver.check"},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "nonclassical_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_nonclassical_probe",
        sim_path="system_v4/probes/sim_nonclassical_probe.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = str(result_path)
    payload["formal_sim_profile"]["claim"] = "nonclassical micro claim"
    payload["formal_sim_profile"]["exact_tool_or_function"] = "z3.Solver.check"
    payload["packet_contract"]["tool_target"] = "z3"
    payload["packet_contract"]["function_surface"] = "z3.Solver.check"
    payload["packet_contract"]["claim_ceiling"] = "nonclassical_micro_only"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_nonclassical_probe",
        sim_path="system_v4/probes/sim_nonclassical_probe.py",
    )

    assert "nonclassical_requires_load_bearing_pytorch" in findings


def test_wizard_sim_admission_rejects_hidden_coupling_baseline_without_baseline_ceiling(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_hidden_baseline_ceiling_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_probe_object_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_probe_object",
                "classification": "classical_baseline",
                "all_pass": True,
                "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "exact fixture"}},
                "tool_integration_depth": {"z3": "load_bearing"},
                "positive": {"passed": True, "function_surface": "z3.Solver.check"},
                "observables": {"rho_AB": 1, "Phi0": 0, "Xi": "coupling witness"},
                "divergence_log": "classical baseline only",
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = str(result_path)
    payload["packet_contract"]["tool_target"] = "z3"
    payload["packet_contract"]["function_surface"] = "z3.Solver.check"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "nonclassical_baseline_missing_baseline_only_ceiling" in findings


def test_wizard_sim_admission_rejects_hidden_coupling_source_without_nonclassical_tool(tmp_path) -> None:
    module = _load_module(
        "wizard_sim_admission_hidden_source_under_test",
        REPO_ROOT / "scripts" / "wizard_sim_admission.py",
    )
    repo = tmp_path / "repo"
    sim_path = repo / "system_v4" / "probes" / "sim_probe_object.py"
    sim_path.parent.mkdir(parents=True)
    sim_path.write_text("rho_AB = 'hidden coupling source signal'\n", encoding="utf-8")
    result_path = repo / "system_v4" / "probes" / "a2_state" / "sim_results" / "sim_probe_object_results.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_probe_object",
                "classification": "classical_baseline",
                "all_pass": True,
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "symbolic fixture only"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True, "function_surface": "sympy.simplify"},
                "divergence_log": "classical baseline only",
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    payload = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
        artifact=artifact,
    )
    payload["formal_sim_profile"]["expected_result_path"] = str(result_path)
    payload["packet_contract"]["tool_target"] = "sympy"
    payload["packet_contract"]["function_surface"] = "sympy.simplify"

    findings = module.validate_admission(
        payload,
        root=repo,
        basename="sim_probe_object",
        sim_path="system_v4/probes/sim_probe_object.py",
    )

    assert "nonclassical_suitable_load_bearing_tool_missing" in findings


def test_qit_engine_evidence_index_blocks_stale_admission_artifact_hash(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_stale_artifact_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)
    (probes / "sim_qit_probe.py").write_text("# fixture\n", encoding="utf-8")
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    result_path = results / "sim_qit_probe_results.json"
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "exact fixture check"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps({"result_path": str(result_path), "result_sha256": "stale-hash"}),
        encoding="utf-8",
    )
    admission_dir = repo / "system_v5" / "ops" / "wizard_admissions"
    admission_dir.mkdir(parents=True)
    admission = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_qit_probe",
        sim_path="system_v4/probes/sim_qit_probe.py",
        artifact=artifact,
    )
    admission["formal_sim_profile"]["expected_result_path"] = str(result_path)
    (admission_dir / "sim_qit_probe.json").write_text(json.dumps(admission), encoding="utf-8")

    index = module.build_index(repo)

    assert index["summary"]["accepted"] == 0
    assert index["summary"]["candidate_entries"] == 0
    assert index["summary"]["quarantine_entries"] == 1
    entry = index["entries"][0]
    assert entry["status"] == "blocked"
    assert "admission:admission_artifact_result_sha256_mismatch" in entry["blockers"]


def test_qit_engine_evidence_index_does_not_accept_admitted_baseline_as_qit_evidence(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_baseline_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    _write_allow_stage_gate(repo)
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)
    (probes / "sim_hopf_probe.py").write_text("# fixture\n", encoding="utf-8")
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    result_path = results / "sim_hopf_probe_results.json"
    result_path.write_text(
        json.dumps(
            {
                "name": "sim_hopf_probe",
                "classification": "classical_baseline",
                "all_pass": True,
                "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "exact fixture check"}},
                "tool_integration_depth": {"z3": "load_bearing"},
                "positive": {"passed": True, "function_surface": "z3.Solver.check"},
                "divergence_log": "baseline only",
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "hopf_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "controller acceptance",
            }
        ),
        encoding="utf-8",
    )
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text(
        json.dumps(
            {
                "result_path": str(result_path),
                "result_sha256": __import__("hashlib").sha256(result_path.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    admission_dir = repo / "system_v5" / "ops" / "wizard_admissions"
    admission_dir.mkdir(parents=True)
    admission = _valid_wizard_admission_payload(
        repo=repo,
        basename="sim_hopf_probe",
        sim_path="system_v4/probes/sim_hopf_probe.py",
        artifact=artifact,
    )
    admission["formal_sim_profile"]["expected_result_path"] = str(result_path)
    admission["packet_contract"]["tool_target"] = "z3"
    admission["packet_contract"]["function_surface"] = "z3.Solver.check"
    admission["packet_contract"]["nonclassical_claim_ceiling"] = "baseline_only"
    (admission_dir / "sim_hopf_probe.json").write_text(json.dumps(admission), encoding="utf-8")

    index = module.build_index(repo)

    assert index["summary"]["admitted_micro_entries"] == 1
    assert index["summary"]["accepted"] == 0
    assert index["operational_status"] == "blocked_no_accepted_qit_entries"
    assert index["next_acceptance_targets"][0]["next_action"] == "do_not_promote_reclassify_or_replace_with_canonical_qit_result"
    entry = index["entries"][0]
    assert entry["status"] == "blocked"
    assert "result:result_classification_not_canonical" in entry["blockers"]


def test_qit_engine_evidence_index_ignores_broad_filename_without_structured_qit_signal(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_scope_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    (results / "sim_coupling_micro_results.json").write_text(
        json.dumps(
            {
                "name": "sim_coupling_micro",
                "classification": "canonical",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "ordinary micro check"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no downstream promotion"],
                "claim_ceiling": "lego_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires later ordinary packet",
                "blocked_until": "ordinary micro acceptance",
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    assert index["summary"]["total_entries"] == 0
    assert index["summary"]["scanned_result_count"] == 1
    assert index["summary"]["qit_signal_result_count"] == 0
    assert len(index["scan_sample"]["scanned_result_files"]) == 1
    assert index["scan_sample"]["qit_signal_result_files"] == []
    assert index["status_reason"] == "no_qit_signal_results_indexed"
    assert index["summary"]["quarantine_entries"] == 0


def test_qit_engine_evidence_index_reports_out_of_scope_qit_like_results_without_accepting_them(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_external_scope_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    canonical_results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    canonical_results.mkdir(parents=True)
    (canonical_results / "sim_plain_micro_results.json").write_text(
        json.dumps(
            {
                "name": "sim_plain_micro",
                "classification": "canonical",
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "ordinary fixture"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "claim_ceiling": "lego_micro_only",
                "promotion_condition": "ordinary later packet",
                "blocked_until": "ordinary acceptance",
            }
        ),
        encoding="utf-8",
    )
    legacy_result = repo / "system_v4" / "probes" / "sim_weyl_legacy_results.json"
    legacy_result.parent.mkdir(parents=True, exist_ok=True)
    (legacy_result.parent / "sim_weyl_legacy.py").write_text("# legacy fixture\n", encoding="utf-8")
    legacy_result.write_text(
        json.dumps(
            {
                "name": "sim_weyl_legacy",
                "classification": "canonical",
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "legacy fixture"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "claim_ceiling": "weyl_micro_only",
                "promotion_condition": "requires canonical re-run and admission",
                "blocked_until": "canonical result exists",
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    assert index["summary"]["total_entries"] == 0
    assert index["summary"]["qit_signal_result_count"] == 0
    assert index["status_reason"] == "no_qit_signal_results_indexed"
    external_scan = index["out_of_scope_qit_result_scan"]
    assert external_scan["status"] == "out_of_scope_qit_like_results_present"
    assert external_scan["external_qit_signal_count"] == 1
    assert external_scan["admission_boundary"] == "diagnostic_only_not_accepted_evidence"
    assert external_scan["sample"][0]["path"] == "system_v4/probes/sim_weyl_legacy_results.json"
    assert external_scan["triage"]["triage_boundary"] == "diagnostic_only_targets_require_canonical_rerun_and_strict_admission"
    assert external_scan["triage"]["bucket_counts"] == {"source_bound_micro_rerun_candidate": 1}
    assert external_scan["triage"]["provisional_rerun_target_count"] == 1
    assert external_scan["triage"]["provisional_rerun_targets"][0]["next_action"] == (
        "rerun_under_canonical_micro_result_surface_then_create_strict_admission"
    )
    assert external_scan["triage"]["provisional_rerun_targets"][0]["source_path"] == (
        "system_v4/probes/sim_weyl_legacy.py"
    )


def test_qit_engine_evidence_index_triages_out_of_scope_late_stage_and_classical_without_rerun_target(
    tmp_path,
) -> None:
    module = _load_module(
        "qit_engine_evidence_index_external_triage_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    canonical_results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    canonical_results.mkdir(parents=True)
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True, exist_ok=True)
    (probes / "sim_weyl_pairwise_coupling.py").write_text("# late fixture\n", encoding="utf-8")
    (probes / "sim_weyl_pairwise_coupling_results.json").write_text(
        json.dumps(
            {
                "name": "sim_weyl_pairwise_coupling",
                "classification": "canonical",
                "tool_manifest": {"z3": {"tried": True, "used": True, "reason": "legacy"}},
                "tool_integration_depth": {"z3": "load_bearing"},
                "claim_ceiling": "weyl_coupling_only",
            }
        ),
        encoding="utf-8",
    )
    mirror = probes / "classical_doctrine_mirrors" / "sim_results"
    mirror.mkdir(parents=True)
    (mirror / "sim_classical_hopf_u1_fiber_winding_results.json").write_text(
        json.dumps(
            {
                "name": "sim_classical_hopf_u1_fiber_winding",
                "classification": "classical_baseline",
                "tool_manifest": {"numpy": {"tried": True, "used": True, "reason": "baseline"}},
                "tool_integration_depth": {"numpy": "load_bearing"},
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    triage = index["out_of_scope_qit_result_scan"]["triage"]
    assert triage["bucket_counts"] == {
        "classical_baseline_reference_only": 1,
        "late_stage_or_coupling_blocked": 1,
    }
    assert triage["provisional_rerun_target_count"] == 0
    late_sample = triage["bucket_samples"]["late_stage_or_coupling_blocked"][0]
    assert late_sample["late_stage_tokens"] == ["coupling", "pairwise"]
    assert late_sample["next_action"] == "do_not_promote_extract_smaller_tool_or_geometry_micro_probe"
    classical_sample = triage["bucket_samples"]["classical_baseline_reference_only"][0]
    assert classical_sample["next_action"] == (
        "do_not_promote_use_only_as_classical_reference_or_rerun_as_new_micro_if_needed"
    )


def test_qit_engine_evidence_index_triages_source_bound_without_load_bearing_as_contract_repair(
    tmp_path,
) -> None:
    module = _load_module(
        "qit_engine_evidence_index_external_repair_triage_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    canonical_results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    canonical_results.mkdir(parents=True)
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True, exist_ok=True)
    (probes / "sim_weyl_micro.py").write_text("# fixture\n", encoding="utf-8")
    (probes / "sim_weyl_micro_results.json").write_text(
        json.dumps(
            {
                "name": "sim_weyl_micro",
                "classification": "canonical",
                "TOOL_MANIFEST": {"z3": {"tried": True, "used": True, "reason": "legacy"}},
                "TOOL_INTEGRATION_DEPTH": {"z3": None},
                "claim_ceiling": "weyl_micro_only",
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    triage = index["out_of_scope_qit_result_scan"]["triage"]
    assert triage["bucket_counts"] == {"source_bound_contract_repair_candidate": 1}
    assert triage["provisional_rerun_target_count"] == 1
    target = triage["provisional_rerun_targets"][0]
    assert target["next_action"] == "repair_micro_contract_then_rerun_under_canonical_result_surface"
    assert target["receipt_schema_present"] is True
    assert target["load_bearing_depths"] == {}


def test_qit_engine_evidence_index_triages_newer_repaired_source_as_rerun_candidate(
    tmp_path,
) -> None:
    module = _load_module(
        "qit_engine_evidence_index_external_repaired_source_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    canonical_results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    canonical_results.mkdir(parents=True)
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True, exist_ok=True)
    source = probes / "sim_weyl_micro.py"
    source.write_text("# repaired fixture\n", encoding="utf-8")
    result = probes / "sim_weyl_micro_results.json"
    result.write_text(
        json.dumps(
            {
                "name": "sim_weyl_micro",
                "classification": "canonical",
                "TOOL_MANIFEST": {"z3": {"tried": True, "used": True, "reason": "legacy"}},
                "TOOL_INTEGRATION_DEPTH": {"z3": None},
                "claim_ceiling": "weyl_micro_only",
            }
        ),
        encoding="utf-8",
    )
    os.utime(result, (1, 1))
    os.utime(source, (2, 2))

    index = module.build_index(repo)

    triage = index["out_of_scope_qit_result_scan"]["triage"]
    assert triage["bucket_counts"] == {"source_bound_repaired_source_rerun_candidate": 1}
    target = triage["provisional_rerun_targets"][0]
    assert target["next_action"] == "rerun_repaired_source_under_canonical_micro_result_surface"
    assert target["source_newer_than_result"] is True


def test_qit_engine_evidence_index_require_accepted_fails_without_candidate(tmp_path) -> None:
    module = _load_module(
        "qit_engine_evidence_index_require_under_test",
        REPO_ROOT / "scripts" / "qit_engine_evidence_index.py",
    )
    repo = tmp_path / "repo"
    results = repo / "system_v4" / "probes" / "a2_state" / "sim_results"
    results.mkdir(parents=True)
    (results / "sim_qit_probe_results.json").write_text(
        json.dumps(
            {
                "name": "sim_qit_probe",
                "classification": "canonical",
                "summary": {"tests_passed": 1, "tests_total": 1},
                "tool_manifest": {"sympy": {"tried": True, "used": True, "reason": "exact fixture check"}},
                "tool_integration_depth": {"sympy": "load_bearing"},
                "positive": {"passed": True},
                "negative": {"passed": True},
                "boundary": {"passed": True},
                "demotion_condition": "demote if fixture fails",
                "out_of_scope": ["no engine promotion"],
                "claim_ceiling": "qit_micro_only",
                "next_lego_target": "none",
                "promotion_condition": "requires admitted downstream packet",
                "blocked_until": "wizard admission exists",
            }
        ),
        encoding="utf-8",
    )

    index = module.build_index(repo)

    assert index["summary"]["accepted"] == 0
    assert index["operational_status"] == "blocked_no_accepted_qit_entries"
    assert index["status_reason"] == "qit_entries_blocked"


def test_queue_claim_defaults_to_strict_wizard_admission() -> None:
    text = (REPO_ROOT / "scripts" / "queue_claim.py").read_text(encoding="utf-8")
    assert 'os.environ.get("STRICT_WIZARD_QUEUE_ADMISSION", "1") == "1"' in text


def test_queue_claim_accepts_strict_wizard_admission_artifact(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "queue_claim_wizard_admission_valid_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    _write_allow_stage_gate(repo)
    artifact = repo / "receipts" / "admission.json"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("{}", encoding="utf-8")
    admission = tmp_path / "admission.json"
    admission.write_text(
        json.dumps(
            _valid_wizard_admission_payload(
                repo=repo,
                basename="sim_probe_object",
                sim_path="system_v4/probes/sim_probe_object.py",
                artifact=artifact,
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "QUEUE_ROOT", queue_root)
    monkeypatch.setattr(module, "STRICT_WIZARD_QUEUE_ADMISSION", True)

    queued = module.enqueue(
        "lane_A",
        "system_v4/probes/sim_probe_object.py",
        str(admission),
    )

    assert queued.parent.name == "lane_A"
    payload = json.loads(queued.read_text(encoding="utf-8"))
    assert payload["wizard_admission_file"] == str(admission)


def test_live_sim_runner_requires_wizard_queue_admission_before_execution() -> None:
    text = (REPO_ROOT / "system_v5" / "ops" / "sim_runner.sh").read_text(encoding="utf-8")
    assert 'STRICT_WIZARD_QUEUE_ADMISSION="${STRICT_WIZARD_QUEUE_ADMISSION:-1}"' in text
    assert "wizard_queue_admitted()" in text
    assert "scripts/wizard_sim_admission.py" in text
    assert 'mark_line "$queue_file" "$basename" "INELIGIBLE" "0"' in text


def test_live_sim_runner_blocks_semantic_claim_names_before_execution() -> None:
    text = (REPO_ROOT / "system_v5" / "ops" / "sim_runner.sh").read_text(encoding="utf-8")
    guard_idx = text.index("direct_sim_semantic_guard.py")
    run_idx = text.index('if "${RUN_CMD[@]}" >/dev/null 2>&1; then')
    assert guard_idx < run_idx
    assert "INELIGIBLE (semantic name)" in text
    assert '--name "$basename"' in text


def test_live_sim_runner_requires_recovery_sentinel_for_admission_bypass() -> None:
    text = (REPO_ROOT / "system_v5" / "ops" / "sim_runner.sh").read_text(encoding="utf-8")
    assert "admission_bypass_preflight()" in text
    assert 'STRICT_RECEIPT_ADMISSION" = "1"' in text
    assert 'STRICT_WIZARD_QUEUE_ADMISSION" = "1"' in text
    assert ".allow_admission_bypass_recovery" in text
    assert "Admission bypass refused" in text


def test_tier_b_gate_poller_uses_system_v5_prompt_authority() -> None:
    text = (REPO_ROOT / "system_v5" / "ops" / "tier_b_gate_poller.py").read_text(
        encoding="utf-8"
    )
    assert "REPO / 'system_v5' / 'ops' / 'tier_b_launch_prompt.md'" in text
    assert "REPO / 'ops' / 'tier_b_launch_prompt.md'" not in text


def test_adaptive_controller_stage_gate_blocks_late_enqueue(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "adaptive_controller_stage_gate_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    queue_root = tmp_path / "queue"
    sim = tmp_path / "sim_axis0_forbidden.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    gate = tmp_path / "stage_gate.py"
    gate.write_text("#!/usr/bin/env python3\nraise SystemExit(1)\n", encoding="utf-8")
    gate.chmod(0o755)

    monkeypatch.setattr(module, "QUEUE", queue_root)
    monkeypatch.setattr(module, "STAGE_GATE_SCRIPT", gate)

    result = module.enqueue(sim, "lane_A", "high")

    assert result is None
    assert not list(queue_root.glob("lane_A/*.json"))
    blocked = list(queue_root.glob("blocked/*.json"))
    assert len(blocked) == 1
    payload = json.loads(blocked[0].read_text(encoding="utf-8"))
    assert payload["blocked_reason"] == "stage_gate_blocked"
    assert payload["blocked_stage_claim"] == "axis"


def test_adaptive_controller_does_not_stage_gate_nonpromotable_tool_lego_fit(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_tool_lego_fit_bypass_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    results = tmp_path / "results"
    results.mkdir()
    sim = tmp_path / "sim_bridge_tool_fit_probe.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    (results / "sim_bridge_tool_fit_probe_results.json").write_text(
        json.dumps(
            {
                "classification": "tool_lego_fit_probe",
                "promotion_allowed": False,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "RESULTS", results)

    assert module.stage_gate_claim_for_sim(tmp_path / "sim_bridge_probe.py") == "scientific_coupling"
    assert module.stage_gate_claim_for_sim(sim) is None


def test_queue_claim_blocks_stage_gated_enqueue_and_claim(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "queue_claim_stage_gate_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    gate = tmp_path / "stage_gate.py"
    gate.write_text("#!/usr/bin/env python3\nraise SystemExit(1)\n", encoding="utf-8")
    gate.chmod(0o755)

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "QUEUE_ROOT", queue_root)
    monkeypatch.setattr(module, "STAGE_GATE_SCRIPT", gate)

    terminal = module.enqueue("lane_A", "system_v4/probes/sim_boundary_flux_admissibility.py")

    assert terminal.parent.name == "blocked"
    payload = json.loads(terminal.read_text(encoding="utf-8"))
    assert payload["blocked_reason"] == "stage_gate_blocked"
    assert payload["blocked_stage_claim"] == "tier_d"

    allowed = tmp_path / "allow_gate.py"
    allowed.write_text("#!/usr/bin/env python3\nraise SystemExit(0)\n", encoding="utf-8")
    allowed.chmod(0o755)
    monkeypatch.setattr(module, "STAGE_GATE_SCRIPT", allowed)
    queued = module.enqueue("lane_A", "system_v4/probes/sim_axis0_forbidden.py")
    assert queued.parent.name == "lane_A"

    monkeypatch.setattr(module, "STAGE_GATE_SCRIPT", gate)
    claimed = module.claim("lane_A", "w1")

    assert claimed is None
    blocked = list((queue_root / "blocked").glob("*.json*"))
    assert any(
        json.loads(item.read_text(encoding="utf-8")).get("blocked_stage_claim") == "axis"
        for item in blocked
    )


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
