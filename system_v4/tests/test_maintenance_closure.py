from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "system_v4" / "probes" / "maintenance_closure.py"


def load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"missing maintenance closure script: {SCRIPT_PATH}")
    spec = importlib.util.spec_from_file_location("maintenance_closure", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("unable to load maintenance_closure module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_payload(*, classification: str = "canonical", blank_reason: bool = False):
    return {
        "classification": classification,
        "tool_manifest": {
            "pytorch": {"tried": True, "used": True, "reason": "core tensor computation"},
            "z3": {"tried": True, "used": True, "reason": "UNSAT structural fence"},
            "sympy": {
                "tried": True,
                "used": False,
                "reason": "" if blank_reason else "not needed for this bounded packet",
            },
        },
        "tool_integration_depth": {
            "pytorch": "load_bearing",
            "z3": "load_bearing",
            "sympy": None,
        },
        "summary": {
            "all_pass": True,
            "total_tests": 4,
            "total_pass": 4,
        },
    }


def test_derive_truth_label_promotes_clean_canonical_payload_with_green_audits():
    mc = load_module()

    decision = mc.derive_truth_label(
        canonical_payload(),
        truth_audit_ok=True,
        controller_audit_ok=True,
    )

    assert decision["truth_label"] == "canonical by process"
    assert decision["blocked"] is False


def test_derive_truth_label_keeps_classical_baseline_below_canonical_even_when_audits_are_green():
    mc = load_module()

    decision = mc.derive_truth_label(
        canonical_payload(classification="classical_baseline"),
        truth_audit_ok=True,
        controller_audit_ok=True,
    )

    assert decision["truth_label"] == "passes local rerun"
    assert decision["blocked"] is False


def test_derive_truth_label_refuses_canonical_promotion_when_any_manifest_reason_is_blank():
    mc = load_module()

    decision = mc.derive_truth_label(
        canonical_payload(blank_reason=True),
        truth_audit_ok=True,
        controller_audit_ok=True,
    )

    assert decision["truth_label"] == "passes local rerun"
    assert decision["blocked"] is False


def test_derive_truth_label_blocks_promotion_when_fresh_audits_are_not_green():
    mc = load_module()

    decision = mc.derive_truth_label(
        canonical_payload(),
        truth_audit_ok=False,
        controller_audit_ok=True,
    )

    assert decision["truth_label"] == "runs"
    assert decision["blocked"] is True
    assert "audit" in decision["reason"].lower()


def test_validate_cli_args_requires_explicit_target_selector():
    mc = load_module()

    with pytest.raises(ValueError, match="target"):
        mc.validate_cli_args(
            result_json="system_v4/probes/a2_state/sim_results/density_hopf_geometry_results.json",
            truth_row=None,
            backlog_row=None,
            registry_row=None,
            tool_row=None,
            dry_run=True,
            write=False,
        )


def test_validate_cli_args_rejects_dry_run_and_write_together():
    mc = load_module()

    with pytest.raises(ValueError, match="dry-run"):
        mc.validate_cli_args(
            result_json="system_v4/probes/a2_state/sim_results/density_hopf_geometry_results.json",
            truth_row="explicit Hopf-map packet (`hopf_map_s3_to_s2`)",
            backlog_row=None,
            registry_row=None,
            tool_row=None,
            dry_run=True,
            write=True,
        )


def test_replace_markdown_table_row_updates_only_targeted_row():
    mc = load_module()

    original = "".join(
        [
            "| surface a | result_a.json | yes | yes | yes | no | note a |\n",
            "| target surface | result_b.json | yes | yes | yes | no | old note |\n",
            "| surface c | result_c.json | yes | yes | yes | no | note c |\n",
        ]
    )

    updated = mc.replace_markdown_table_row(
        original,
        "target surface",
        "| target surface | result_b.json | yes | yes, fresh local rerun | yes, fresh local rerun | `canonical by process` | new note |",
    )

    assert "surface a | result_a.json" in updated
    assert "surface c | result_c.json" in updated
    assert "old note" not in updated
    assert "new note" in updated
    assert updated.count("target surface") == 1



def test_replace_markdown_table_row_raises_when_target_row_missing():
    mc = load_module()

    with pytest.raises(ValueError, match="not found"):
        mc.replace_markdown_table_row(
            "| surface a | result_a.json | yes | yes | yes | no | note a |\n",
            "missing surface",
            "| missing surface | result_a.json | yes | yes | yes | no | note |",
        )



def test_update_truth_row_for_canonical_by_process_sets_expected_columns():
    mc = load_module()

    existing = (
        "| g-structure compatibility coupling follow-on | `system_v4/probes/a2_state/sim_results/gstructure_compatibility_coupling_results.json` "
        "| yes | yes, fresh local rerun | yes, fresh local rerun | no | stale note |"
    )

    updated = mc.update_truth_row(
        existing,
        truth_label="canonical by process",
        canonical_note="`canonical by process` for the bounded local follow-on",
        notes_note="fresh local bounded coupling proof stays narrow",
    )

    assert "| yes | yes, fresh local rerun | yes, fresh local rerun | `canonical by process` for the bounded local follow-on |" in updated
    assert updated.endswith("fresh local bounded coupling proof stays narrow |")



def test_update_truth_row_for_passes_local_rerun_keeps_canonical_column_negative():
    mc = load_module()

    existing = (
        "| g-structure support-manifold anchor | `system_v4/probes/a2_state/sim_results/g_structure_tower_results.json` "
        "| yes | yes, fresh local rerun | no | no | stale note |"
    )

    updated = mc.update_truth_row(
        existing,
        truth_label="passes local rerun",
        canonical_note="no — baseline artifact remains below canonical",
        notes_note="fresh rerun confirms a strong classical_baseline anchor",
    )

    assert "| yes | yes, fresh local rerun | yes, fresh local rerun | no — baseline artifact remains below canonical |" in updated
    assert updated.endswith("fresh rerun confirms a strong classical_baseline anchor |")



def test_prepare_truth_surface_update_returns_old_and_new_rows():
    mc = load_module()

    markdown = "".join(
        [
            "| surface a | `a.json` | yes | yes | yes | no | note a |\n",
            "| g-structure support-manifold anchor | `g.json` | yes | yes, fresh local rerun | no | no | stale note |\n",
        ]
    )

    plan = mc.prepare_truth_surface_update(
        markdown,
        row_match_fragment="g-structure support-manifold anchor",
        truth_label="passes local rerun",
        canonical_note="no — baseline artifact remains below canonical",
        notes_note="fresh rerun confirms a strong classical_baseline anchor",
    )

    assert "stale note" in plan["old_row"]
    assert "fresh rerun confirms a strong classical_baseline anchor" in plan["new_row"]
    assert "surface a" in plan["updated_text"]



def test_apply_surface_update_dry_run_does_not_write_file(tmp_path):
    mc = load_module()

    surface_path = tmp_path / "sim_truth_audit.md"
    original = "| row | `a.json` | yes | yes | yes | no | note |\n"
    surface_path.write_text(original, encoding="utf-8")

    changed = mc.apply_surface_update(surface_path, "| row | `a.json` | yes | yes | yes | no | updated |\n", write=False)

    assert changed is False
    assert surface_path.read_text(encoding="utf-8") == original



def test_apply_surface_update_write_mode_updates_file(tmp_path):
    mc = load_module()

    surface_path = tmp_path / "sim_truth_audit.md"
    original = "| row | `a.json` | yes | yes | yes | no | note |\n"
    updated = "| row | `a.json` | yes | yes | yes | `canonical by process` | updated |\n"
    surface_path.write_text(original, encoding="utf-8")

    changed = mc.apply_surface_update(surface_path, updated, write=True)

    assert changed is True
    assert surface_path.read_text(encoding="utf-8") == updated



def test_build_truth_notes_for_canonical_by_process_returns_positive_canonical_column():
    mc = load_module()

    canonical_note, notes_note = mc.build_truth_notes(
        truth_label="canonical by process",
        reason="artifact and fresh audits satisfy canonical process gates",
        result_json_name="density_hopf_geometry_results.json",
    )

    assert canonical_note.startswith("`canonical by process`")
    assert "density_hopf_geometry_results.json" in notes_note



def test_build_truth_notes_for_passes_local_rerun_returns_negative_canonical_column():
    mc = load_module()

    canonical_note, notes_note = mc.build_truth_notes(
        truth_label="passes local rerun",
        reason="bounded packet passes locally but does not satisfy every canonical process gate",
        result_json_name="g_structure_tower_results.json",
    )

    assert canonical_note.startswith("no —")
    assert "g_structure_tower_results.json" in notes_note



def test_execute_truth_surface_update_dry_run_returns_plan_without_writing(tmp_path):
    mc = load_module()

    surface_path = tmp_path / "sim_truth_audit.md"
    original = "".join(
        [
            "| surface a | `a.json` | yes | yes | yes | no | note a |\n",
            "| g-structure support-manifold anchor | `g.json` | yes | yes, fresh local rerun | no | no | stale note |\n",
        ]
    )
    surface_path.write_text(original, encoding="utf-8")

    report = mc.execute_truth_surface_update(
        surface_path=surface_path,
        row_match_fragment="g-structure support-manifold anchor",
        truth_label="passes local rerun",
        reason="bounded packet passes locally but does not satisfy every canonical process gate",
        result_json_name="g_structure_tower_results.json",
        write=False,
    )

    assert report["changed"] is False
    assert "stale note" in report["old_row"]
    assert "g_structure_tower_results.json" in report["new_row"]
    assert surface_path.read_text(encoding="utf-8") == original
