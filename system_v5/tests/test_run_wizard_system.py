from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_wizard_system.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_wizard_system", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def make_candidate(mod, candidate: Path, sizes: tuple[str, ...] = ("standard",)) -> None:
    for size in sizes:
        general = candidate / mod.GENERAL_FILES[size]
        general.parent.mkdir(parents=True, exist_ok=True)
        general.write_text(
            "# Wizard General\n\n"
            "Positive MMM before task. Output shape uses receipts. "
            "Follow-up options are not evidence. Minimal receipt includes unit_id wave status evidence output open.\n",
            encoding="utf-8",
        )
        for spec in mod.LANES:
            path = candidate / spec["path_template"].format(size=size, upper=size.upper())
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# fixture\n\n## terms\n\n"
                "- receipt truth\n"
                "- local run\n"
                "- live hold\n",
                encoding="utf-8",
            )


def test_run_wizard_system_writes_valid_receipt_spine(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    result = mod.run_wizard(candidate, tmp_path / "out", "test the local wizard", general_size="standard")

    assert result["ok"], result["findings"]
    assert Path(result["lane_resolution_path"]).exists()
    assert Path(result["final_answer_path"]).exists()
    assert Path(result["final_validation_path"]).exists()

    validation = json.loads(Path(result["final_validation_path"]).read_text(encoding="utf-8"))
    assert validation["ok"] is True
    assert validation["findings"] == []
    assert "Hume" not in validation["visible_lanes"]
    assert "LLM Council" in validation["visible_lanes"]

    final_answer = Path(result["final_answer_path"]).read_text(encoding="utf-8")
    assert final_answer.startswith("Wizard: ")
    assert "Pools:" in final_answer.splitlines()[1]
    assert "Routes:" in final_answer.splitlines()[2]
    assert "local receipts" in final_answer
    assert "subagents:" in final_answer.splitlines()[0]
    assert "Claude Agent" not in final_answer.splitlines()[0]
    assert "OMX workers" not in final_answer.splitlines()[0]
    assert "140+" not in final_answer.splitlines()[0]
    assert "🧙 Main Answer" in final_answer
    assert "🌊 Wave Results" in final_answer
    assert "Voice wave did not run as live spawned voice subagents" in final_answer
    assert "📊 Quality Audit" not in final_answer
    assert "\n🔎 Audit\n" not in final_answer
    assert "q:" in final_answer.splitlines()[-1]
    assert "🪄 Follow-up" in final_answer
    assert "Lane follow-ups" in final_answer
    assert "Composition follow-ups" in final_answer
    assert not re.search(r"(?m)^\s*19\.\s", final_answer)
    assert not re.search(r"(?m)^\s*C(?:19|20|21|22|23|24|25)\.", final_answer)
    assert "| W |" not in final_answer
    assert "**🔗 Compositions**" not in final_answer
    assert "Prompt-local" not in final_answer
    assert "Guard compositions" not in final_answer
    assert "L1. 🎯 Direct\n   🪄 Follow-up:" in final_answer
    assert "L5. 🧼 Hygiene\n   🪄 Follow-up:" in final_answer
    assert "L6. 🛡️ Security\n   🪄 Follow-up:" in final_answer
    assert "C5. 🧼 Clean closeout\n   🪄 Follow-up:" in final_answer
    assert "C9. 🧙 Full Wizard pass\n   🪄 Follow-up:" in final_answer
    assert "Use as much of C5, C6, C7, and C8 as the next input warrants" in final_answer


def test_run_wizard_system_strict_live_validation_rejects_local_receipts(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    result = mod.run_wizard(
        candidate,
        tmp_path / "out",
        "test strict live validation",
        general_size="standard",
        require_live_execution=True,
    )

    assert result["ok"] is False
    assert result["require_live_execution"] is True
    validation = json.loads(Path(result["final_validation_path"]).read_text(encoding="utf-8"))
    assert validation["require_live_execution"] is True
    finding_codes = {finding["code"] for finding in validation["findings"]}
    assert "live_execution_requires_spawned" in finding_codes
    assert "visible_lane_not_live" in finding_codes


def test_run_wizard_system_source_lift_gate_strict_mode_accepts_local_gates(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    result = mod.run_wizard(
        candidate,
        tmp_path / "out",
        "test strict source lift gate validation",
        general_size="standard",
        require_source_and_lift_gate=True,
    )

    assert result["ok"], result["findings"]
    assert result["require_source_and_lift_gate"] is True
    validation = json.loads(Path(result["final_validation_path"]).read_text(encoding="utf-8"))
    assert validation["require_source_and_lift_gate"] is True
    assert validation["findings"] == []
    receipt = json.loads((Path(result["receipts_dir"]) / "direct.json").read_text(encoding="utf-8"))
    gate = receipt["source_and_lift_receipt_gate"]
    assert gate["terminal_status"] == "simulated"
    assert gate["expansion_permission"] is False


def test_run_wizard_system_strict_live_validation_accepts_spawn_receipt_overlay(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)
    live_receipts = []
    for index, spec in enumerate(
        [spec for spec in mod.LANES if mod._category(spec["lane"]) != "composition"],
        start=1,
    ):
        mini_mmm_path = spec["path_template"].format(size="standard", upper="STANDARD")
        live_receipts.append(
            {
                "lane": spec["lane"],
                "status": "spawned_completed",
                "agent_id": f"019-live-{index:02d}",
                "worker_id": f"codex-live-{index:02d}",
                "mini_mmm_path": mini_mmm_path,
                "mini_mmm_scope": "voice_local" if mod._category(spec["lane"]) == "voice" else "lane_local",
                "runtime_registry": "codex native subagent spawned with route-local mini-MMM",
                "source_tool": "codex_app_spawn_agent",
                "spawn_timestamp": "2026-04-30T00:00:00+00:00",
                "checked": f"spawned {spec['lane']} with {mini_mmm_path}",
                "concluded": f"{spec['lane']} returned a usable live receipt",
                "open": "none for strict live overlay test",
                "evidence": f"spawn_agent receipt 019-live-{index:02d}",
                "output": f"{spec['lane']} live worker output",
            }
        )
    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    for offset, option_id in enumerate(("L1", "L2", "L3", "L4", "L5", "L6", "C5", "C6", "C7", "C8", "C9"), start=100):
        live_receipts.append(
            {
                "lane": f"Follow-up Scout {option_id}",
                "status": "spawned_completed",
                "agent_id": f"019-live-{offset}",
                "worker_id": f"codex-live-{offset}",
                "mini_mmm_path": direct_mini,
                "mini_mmm_scope": "lane_local",
                "runtime_registry": "codex native subagent spawned with route-local mini-MMM",
                "source_tool": "codex_app_spawn_agent",
                "spawn_timestamp": "2026-04-30T00:00:00+00:00",
                "checked": f"spawned follow-up scout {option_id}",
                "concluded": f"{option_id} returned a usable live scout receipt",
                "open": "none for strict live overlay test",
                "evidence": f"spawn_agent receipt 019-live-{offset}",
                "output": f"{option_id} live scout worker output",
            }
        )
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(json.dumps(live_receipts), encoding="utf-8")

    result = mod.run_wizard(
        candidate,
        tmp_path / "out",
        "test strict live overlay",
        general_size="standard",
        live_receipts_path=live_receipts_path,
        require_live_execution=True,
    )

    assert result["ok"], result["findings"]
    assert "Direct" in result["live_routes"]
    assert "All-D" not in result["live_routes"]
    assert "Follow-up Scout C9" in result["live_routes"]
    validation = json.loads(Path(result["final_validation_path"]).read_text(encoding="utf-8"))
    assert validation["ok"] is True
    assert validation["findings"] == []
    first_row = json.loads(Path(result["lane_resolution_path"]).read_text(encoding="utf-8").splitlines()[0])
    assert first_row["status"] == "spawned_completed"
    assert first_row["agent_id"] == "019-live-01"
    assert "not spawned" not in first_row["runtime_registry"]


def test_run_wizard_system_live_overlay_requires_worker_identity(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(
        json.dumps(
            [
                {
                    "lane": "Direct",
                    "status": "spawned_completed",
                    "mini_mmm_path": "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md",
                    "checked": "spawn attempted",
                    "concluded": "missing identity should fail",
                    "open": "identity missing",
                    "evidence": "no agent id",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires agent_id or worker_id"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "test invalid live overlay",
            general_size="standard",
            live_receipts_path=live_receipts_path,
            require_live_execution=True,
        )


def test_run_wizard_system_live_overlay_requires_provenance(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(
        json.dumps(
            [
                {
                    "lane": "Direct",
                    "status": "spawned_completed",
                    "agent_id": "019-live-direct",
                    "mini_mmm_path": "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md",
                    "checked": "spawn attempted",
                    "concluded": "missing provenance should fail",
                    "open": "provenance missing",
                    "evidence": "no source tool",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires source_tool"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "test missing live provenance",
            general_size="standard",
            live_receipts_path=live_receipts_path,
            require_live_execution=True,
        )


def full_scale_receipts(count: int = 154) -> list[dict]:
    receipts = []
    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    remaining = count
    for wave in range(1, 12):
        slots = min(14, remaining)
        for slot in range(1, slots + 1):
            receipts.append(
                {
                    "lane": f"Wizard Wave {wave:02d} Slot {slot:02d}",
                    "status": "spawned_completed",
                    "agent_id": f"019-live-wave-{wave:02d}-{slot:02d}",
                    "worker_id": f"codex-live-wave-{wave:02d}-{slot:02d}",
                    "mini_mmm_path": direct_mini,
                    "mini_mmm_scope": "lane_local",
                    "runtime_registry": "codex native subagent spawned with route-local mini-MMM",
                    "source_tool": "codex_app_spawn_agent",
                    "spawn_timestamp": "2026-04-30T00:00:00+00:00",
                    "wizard_wave": wave,
                    "wave_slot": slot,
                    "checked": f"spawned wave {wave} slot {slot}",
                    "concluded": f"wave {wave} slot {slot} returned usable live receipt",
                    "open": "none for full-scale validation fixture",
                    "evidence": f"spawn_agent receipt 019-live-wave-{wave:02d}-{slot:02d}",
                    "output": f"wave {wave} slot {slot} live worker output",
                }
            )
        remaining -= slots
        if remaining <= 0:
            break
    return receipts


def test_run_wizard_system_full_scale_requires_each_wave_not_magic_number(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(json.dumps(full_scale_receipts()), encoding="utf-8")

    result = mod.run_wizard(
        candidate,
        tmp_path / "out",
        "test full wizard scale",
        general_size="standard",
        live_receipts_path=live_receipts_path,
        require_live_execution=True,
        require_full_wizard_scale=True,
    )

    assert result["ok"], result["findings"]
    assert result["full_wizard_scale"]["required_waves"] == 11
    assert result["full_wizard_scale"]["design_max_subagents_per_wave"] == 14
    assert result["full_wizard_scale"]["runtime_max_concurrent_subagents"] >= 1
    assert result["full_wizard_scale"]["min_live_subagents"] == 1
    assert result["full_wizard_scale"]["live_subagents"] == 154
    assert result["full_wizard_scale"]["wave_counts"][1] == 14
    assert result["full_wizard_scale"]["wave_counts"][11] == 14
    assert result["full_wizard_scale"]["planned_batches_by_wave"][1] >= 1


def test_run_wizard_system_full_scale_uses_runtime_plan_for_batches(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(json.dumps(full_scale_receipts()), encoding="utf-8")
    runtime_plan_path = tmp_path / "runtime_plan.json"
    runtime_plan_path.write_text(
        json.dumps(
            {
                "runtime": "codex-app",
                "pool": "codex-native",
                "max_concurrent_subagents": 13,
                "batching": "rolling-reset",
                "reroute_policy": "use receipts from other pools only when accepted by route truth",
            }
        ),
        encoding="utf-8",
    )

    result = mod.run_wizard(
        candidate,
        tmp_path / "out",
        "test adaptive runtime plan",
        general_size="standard",
        live_receipts_path=live_receipts_path,
        runtime_plan_path=runtime_plan_path,
        require_live_execution=True,
        require_full_wizard_scale=True,
    )

    assert result["ok"], result["findings"]
    assert result["runtime_plan"]["max_concurrent_subagents"] == 13
    assert result["runtime_plan"]["release_completed_agents"] is True
    assert result["runtime_plan"]["child_spawn_retry_policy"] == "close_completed_then_retry_smaller"
    assert result["full_wizard_scale"]["runtime_max_concurrent_subagents"] == 13
    assert result["full_wizard_scale"]["release_completed_agents"] is True
    assert result["full_wizard_scale"]["planned_batches_by_wave"][1] == 2
    assert result["full_wizard_scale"]["planned_batches_by_wave"][11] == 2


def test_run_wizard_system_rejects_terminal_thread_limit_plan(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(json.dumps(full_scale_receipts()), encoding="utf-8")
    runtime_plan_path = tmp_path / "runtime_plan.json"
    runtime_plan_path.write_text(
        json.dumps(
            {
                "runtime": "codex-app",
                "pool": "codex-native",
                "max_concurrent_subagents": 1,
                "batching": "rolling",
                "release_completed_agents": False,
                "child_spawn_retry_policy": "mark_blocked",
                "thread_limit_is_terminal_blocker": True,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="release_completed_agents must be true"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "thread limit cannot be terminal child blocker",
            general_size="standard",
            live_receipts_path=live_receipts_path,
            runtime_plan_path=runtime_plan_path,
            require_live_execution=True,
            require_full_wizard_scale=True,
        )


def test_run_wizard_system_rejects_non_rolling_child_batching(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(json.dumps(full_scale_receipts()), encoding="utf-8")
    runtime_plan_path = tmp_path / "runtime_plan.json"
    runtime_plan_path.write_text(
        json.dumps(
            {
                "runtime": "codex-app",
                "pool": "codex-native",
                "max_concurrent_subagents": 10,
                "batching": "parallel",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="batching must be rolling"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "non-rolling batching hides child capacity failure",
            general_size="standard",
            live_receipts_path=live_receipts_path,
            runtime_plan_path=runtime_plan_path,
            require_live_execution=True,
            require_full_wizard_scale=True,
        )


def test_run_wizard_system_full_scale_can_require_plan_specific_minimum(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(json.dumps(full_scale_receipts(153)), encoding="utf-8")

    with pytest.raises(ValueError, match="at least 154 live receipts"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "test full wizard under scale",
            general_size="standard",
            live_receipts_path=live_receipts_path,
            require_live_execution=True,
            require_full_wizard_scale=True,
            full_wizard_min_live_subagents=154,
        )


def test_run_wizard_system_supports_selected_size_without_lane_collapse(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate, ("compact", "standard", "full"))

    expected_lanes = None
    for size in ("compact", "standard", "full"):
        result = mod.run_wizard(
            candidate,
            tmp_path / f"out-{size}",
            "test size routing",
            general_size=size,
        )

        assert result["ok"], result["findings"]
        if expected_lanes is None:
            expected_lanes = result["lanes"]
        assert result["lanes"] == expected_lanes

        lane_rows = Path(result["lane_resolution_path"]).read_text(encoding="utf-8").splitlines()
        assert lane_rows
        for raw in lane_rows:
            row = json.loads(raw)
            assert f"mini_mmms/{size}/" in row["checked"]

        validation = json.loads(Path(result["final_validation_path"]).read_text(encoding="utf-8"))
        assert validation["ok"] is True
        assert validation["findings"] == []


def test_run_wizard_system_fails_when_selected_size_body_is_missing(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate, ("standard",))

    with pytest.raises(FileNotFoundError):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "missing compact should not silently fallback",
            general_size="compact",
        )


def test_output_feedback_changes_final_answer_only_not_receipts(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    first = mod.run_wizard(
        candidate,
        tmp_path / "out-a",
        "test feedback tuning",
        general_size="standard",
        feedback=["first surface"],
    )
    second = mod.run_wizard(
        candidate,
        tmp_path / "out-b",
        "test feedback tuning",
        general_size="standard",
        feedback=["second surface"],
    )

    assert first["ok"], first["findings"]
    assert second["ok"], second["findings"]
    assert first["lanes"] == second["lanes"]

    first_rows = [
        json.loads(raw)["lane"]
        for raw in Path(first["lane_resolution_path"]).read_text(encoding="utf-8").splitlines()
    ]
    second_rows = [
        json.loads(raw)["lane"]
        for raw in Path(second["lane_resolution_path"]).read_text(encoding="utf-8").splitlines()
    ]
    assert first_rows == second_rows

    first_final = Path(first["final_answer_path"]).read_text(encoding="utf-8")
    second_final = Path(second["final_answer_path"]).read_text(encoding="utf-8")
    assert "first surface" in first_final
    assert "second surface" in second_final
    assert first_final != second_final


def _all_d_live_receipt(mini_mmm_path: str) -> dict:
    return {
        "lane": "All-D",
        "status": "spawned_completed",
        "agent_id": "019-live-all-d",
        "worker_id": "codex-live-all-d",
        "mini_mmm_path": mini_mmm_path,
        "mini_mmm_scope": "lane_local",
        "runtime_registry": "codex native subagent spawned with route-local mini-MMM",
        "source_tool": "codex_app_spawn_agent",
        "spawn_timestamp": "2026-04-30T00:00:00+00:00",
        "checked": "spawned All-D",
        "concluded": "All-D returned a usable live receipt",
        "open": "none",
        "evidence": "spawn_agent receipt 019-live-all-d",
        "output": "All-D live worker output",
    }


def _child_live_receipt(lane: str, mini_mmm_path: str, index: int, family: str = "codex") -> dict:
    return {
        "lane": lane,
        "status": "spawned_completed",
        "agent_id": f"019-live-child-{index:02d}",
        "worker_id": f"{family}-live-child-{index:02d}",
        "model_family": family,
        "mini_mmm_path": mini_mmm_path,
        "mini_mmm_scope": "lane_local",
        "runtime_registry": f"{family} child spawned with route-local mini-MMM",
        "source_tool": "codex_app_spawn_agent" if family == "codex" else f"{family}_child_runtime",
        "spawn_timestamp": "2026-04-30T00:00:00+00:00",
        "checked": f"spawned child {lane}",
        "concluded": f"{lane} returned a usable live receipt",
        "open": "none",
        "evidence": f"spawn_agent receipt 019-live-child-{index:02d}",
        "output": f"{lane} live child worker output",
    }


def test_child_quorum_all_d_live_with_no_children_is_rejected(tmp_path: Path):
    """Falsifier: All-D live + zero child receipts must raise ValueError.

    Before hardening, _overlay_live_receipts accepted this silently.
    The parent claimed 'completed' with no child execution evidence.
    """
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(
        json.dumps([_all_d_live_receipt(direct_mini)]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="All-D has a live receipt but only 0 child receipts"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "child-quorum falsifier: All-D live, no children",
            general_size="standard",
            live_receipts_path=live_receipts_path,
        )


def test_child_quorum_all_d_live_with_one_child_is_rejected(tmp_path: Path):
    """Falsifier: All-D live + one child is below the v4.1 quorum."""
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(
        json.dumps([
            _all_d_live_receipt(direct_mini),
            _child_live_receipt("Follow-up 1", direct_mini, 1),
        ]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="only 1 child receipts"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "child-quorum falsifier: All-D live with one child",
            general_size="standard",
            live_receipts_path=live_receipts_path,
        )


def test_child_quorum_all_d_live_with_model_matrix_is_accepted(tmp_path: Path):
    """Hardened path: All-D live needs 5-10 child receipts with v4.1 family spread."""
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    families = ("codex", "opus", "sonnet", "haiku", "gemini")
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(
        json.dumps([
            _all_d_live_receipt(direct_mini),
            *[
                _child_live_receipt(f"Follow-up {index}", direct_mini, index, family)
                for index, family in enumerate(families, start=1)
            ],
        ]),
        encoding="utf-8",
    )

    result = mod.run_wizard(
        candidate,
        tmp_path / "out",
        "child-quorum hardened: All-D live with model matrix",
        general_size="standard",
        live_receipts_path=live_receipts_path,
    )

    assert "All-D" in result["live_routes"]
    assert "Follow-up 5" in result["live_routes"]


def test_child_quorum_meta_row_alone_does_not_satisfy_quorum(tmp_path: Path):
    """Falsifier: All-D live + only a meta-row receipt (self-check) must be rejected.

    Before hardening, ALL_D_META_ROWS was not excluded from the quorum count.
    A parent could claim completion by supplying only 'All-D self-check', which
    records verification work, not child execution evidence.
    """
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(
        json.dumps([
            _all_d_live_receipt(direct_mini),
            _child_live_receipt("All-D self-check", direct_mini, 99),
        ]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="meta-rows.*do not count"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "child-quorum falsifier: All-D live, self-check-only",
            general_size="standard",
            live_receipts_path=live_receipts_path,
        )


def test_child_quorum_meta_row_plus_model_matrix_is_accepted(tmp_path: Path):
    """Hardened path: meta rows are allowed but do not count toward the v4.1 quorum."""
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    live_receipts_path = tmp_path / "live_receipts.json"
    families = ("codex", "opus", "sonnet", "haiku", "gemini")
    live_receipts_path.write_text(
        json.dumps([
            _all_d_live_receipt(direct_mini),
            _child_live_receipt("All-D self-check", direct_mini, 99),
            *[
                _child_live_receipt(f"Follow-up {index}", direct_mini, index, family)
                for index, family in enumerate(families, start=1)
            ],
        ]),
        encoding="utf-8",
    )

    result = mod.run_wizard(
        candidate,
        tmp_path / "out",
        "child-quorum hardened: All-D live with meta-row and real child",
        general_size="standard",
        live_receipts_path=live_receipts_path,
    )

    assert "All-D" in result["live_routes"]
    assert "All-D self-check" in result["live_routes"]
    assert "Follow-up 5" in result["live_routes"]


def test_child_quorum_all_d_live_missing_model_family_is_rejected(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    families = ("codex", "opus", "sonnet", "haiku", "codex")
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(
        json.dumps([
            _all_d_live_receipt(direct_mini),
            *[
                _child_live_receipt(f"Follow-up {index}", direct_mini, index, family)
                for index, family in enumerate(families, start=1)
            ],
        ]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required families: gemini"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "child-quorum falsifier: All-D live missing Gemini",
            general_size="standard",
            live_receipts_path=live_receipts_path,
        )


def test_child_quorum_all_d_live_above_normal_quorum_is_rejected(tmp_path: Path):
    mod = load_module()
    candidate = tmp_path / "candidate"
    make_candidate(mod, candidate)

    direct_mini = "mini_mmms/standard/lanes/md/MMM_LANE_DIRECT_STANDARD_v2_7.md"
    families = ("codex", "opus", "sonnet", "haiku", "gemini", "codex", "opus", "sonnet", "haiku", "gemini", "codex")
    live_receipts_path = tmp_path / "live_receipts.json"
    live_receipts_path.write_text(
        json.dumps([
            _all_d_live_receipt(direct_mini),
            *[
                _child_live_receipt(f"Follow-up {index}", direct_mini, index, family)
                for index, family in enumerate(families, start=1)
            ],
        ]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="normal quorum is 5-10"):
        mod.run_wizard(
            candidate,
            tmp_path / "out",
            "child-quorum falsifier: All-D stress run without audit",
            general_size="standard",
            live_receipts_path=live_receipts_path,
        )
