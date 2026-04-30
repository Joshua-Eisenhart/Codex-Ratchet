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
    assert "Hume" in validation["visible_lanes"]
    assert "LLM Council" in validation["visible_lanes"]

    final_answer = Path(result["final_answer_path"]).read_text(encoding="utf-8")
    assert final_answer.startswith("🧙 Wizard ")
    assert "local receipts" in final_answer
    assert "Subagents:" in final_answer.splitlines()[0]
    assert "Claude Agent" not in final_answer.splitlines()[0]
    assert "OMX workers" not in final_answer.splitlines()[0]
    assert "140+" not in final_answer.splitlines()[0]
    assert "🧙 Main Answer" in final_answer
    assert "🗣️ Voices" in final_answer
    assert "📊 Quality Audit" in final_answer
    assert "Quality Audit Score:" in final_answer
    assert "Quality Audit Findings: 0" in final_answer
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
