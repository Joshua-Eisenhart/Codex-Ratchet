from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).parents[2]
VALIDATOR = ROOT / "cb-wave-author/scripts/validate_wave.py"
spec = importlib.util.spec_from_file_location("validate_wave", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
EXEC_VALIDATOR = ROOT / "cb-wave-author/scripts/verify_wave_execution.py"
exec_spec = importlib.util.spec_from_file_location("verify_wave_execution", EXEC_VALIDATOR)
exec_module = importlib.util.module_from_spec(exec_spec)
assert exec_spec.loader is not None
exec_spec.loader.exec_module(exec_module)


def definitions() -> list[Path]:
    return sorted(ROOT.glob("cb-*-wave/wave.json"))


def test_every_wave_definition_is_valid_and_independent() -> None:
    paths = definitions()
    assert {p.parent.name for p in paths} == {
        "cb-premortem-wave",
        "cb-counterexample-wave",
        "cb-authority-collapse-wave",
        "cb-failure-wave",
        "cb-repair-wave",
        "cb-strategy-wave",
        "cb-build-campaign-wave",
        "cb-maintenance-wave",
        "cb-context-strategy-wave",
        "cb-exploration-wave",
        "cb-goodhart-wave",
        "cb-object-loop-wave",
        "cb-context-wave",
        "cb-objective-integrity-wave",
        "cb-strategy-framing-wave",
        "cb-strategy-checkpoint-wave",
        "cb-strategy-discriminator-wave",
    }
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert module.validate(data) == [], path
        assert module.validate_tree(data, ROOT) == [], path
        assert (path.parent / "SKILL.md").is_file()


def test_runtime_assignments_in_definition_are_refused() -> None:
    data = json.loads((ROOT / "cb-failure-wave/wave.json").read_text(encoding="utf-8"))
    bad = copy.deepcopy(data)
    bad["models"] = ["temporary-name"]
    assert "embedded_runtime_assignments" in module.validate(bad)
    bad2 = copy.deepcopy(data)
    bad2["routing"] = {"preferred_models": ["temporary-name"]}
    assert "embedded_runtime_assignments" in module.validate(bad2)


def test_unknown_child_skill_is_refused_by_tree_validation() -> None:
    data = json.loads((ROOT / "cb-failure-wave/wave.json").read_text(encoding="utf-8"))
    data["children"][0]["skill"] = "does-not-exist"
    assert "missing_child_skill:does-not-exist" in module.validate_tree(data, ROOT)


def test_missing_cancellation_evidence_is_refused() -> None:
    data = json.loads((ROOT / "cb-failure-wave/wave.json").read_text(encoding="utf-8"))
    data["completion"]["required_evidence"].remove("cancellation_state")
    assert "completion_missing:cancellation_state" in module.validate(data)


def test_empty_stop_reasons_and_zero_mmm_range_are_refused() -> None:
    data = json.loads((ROOT / "cb-failure-wave/wave.json").read_text(encoding="utf-8"))
    data["loop"]["stop_reasons"] = []
    data["mmm_profile"]["voice_count_range"] = [0, 0]
    errors = module.validate(data)
    assert "loop_contract" in errors
    assert "mmm_count_range" in errors


def test_zip_failure_wave_is_valid_under_its_own_contract() -> None:
    path = ROOT / "zip-failure-wave" / "wave.json"
    validator = ROOT / "zip-failure-wave" / "scripts" / "validate_wave.py"
    proc = subprocess.run(
        [sys.executable, str(validator), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    body = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert body["disposition"] == "ZIP_WAVE_DEFINITION_VALID"


def test_main_mmms_are_not_in_operational_wave_definitions() -> None:
    for path in definitions():
        text = path.read_text(encoding="utf-8")
        assert "FULL_MMM_v4_3" not in text
        assert "COMPACT_MMM_v4_3" not in text
        assert json.loads(text)["mmm_profile"]["mini_voices_only"] is True


def test_execution_requires_exact_child_call_and_output_chain(tmp_path: Path) -> None:
    definition_path = ROOT / "cb-premortem-wave/wave.json"
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    mmm_root = tmp_path / "mmm"
    (mmm_root / "mini/full/voices/md").mkdir(parents=True)
    (mmm_root / "mini/compact/voices/md").mkdir(parents=True)
    for voice in ("FACTORY", "FEYNMAN", "HUME", "ORWELL", "POPPER", "PUSHBACK", "STRATEGY", "SYSTEMS", "ZHUANGZI"):
        for variant in ("full", "compact"):
            path = mmm_root / "mini" / variant / "voices" / "md" / f"MMM_VOICE_{voice}_{variant.upper()}_v4_1.md"
            path.write_text(f"{voice} {variant}\n", encoding="utf-8")
    children = []
    for index, child in enumerate(definition["children"]):
        cell = tmp_path / child["id"]
        cell.mkdir()
        task = cell / "task.md"
        task.write_text(child["operation"], encoding="utf-8")
        prepared = subprocess.run([
            sys.executable, str(ROOT / "mmm-preload/scripts/mmm_preload.py"), "prepare",
            "--task-file", str(task), "--output-dir", str(cell), "--run-id", "run-1",
            "--agent-id", child["id"], "--parent-id", "controller-1", "--wave-id", definition["wave_id"],
            "--round", "1", "--depth", "1", "--seed", str(21 + index), "--voice-count", "2",
            "--mmm-root", str(mmm_root),
        ], capture_output=True, text=True, check=False)
        assert prepared.returncode == 0, prepared.stdout
        preload = cell / "preload_receipt.json"
        preload_data = json.loads(preload.read_text(encoding="utf-8"))
        output = cell / "output.md"
        output.write_text("observed", encoding="utf-8")
        output_hash = exec_module.sha(output.read_bytes())
        call = cell / "call.json"
        call.write_text(json.dumps({
            "schema": "constraintbox.provider-call.v1",
            "preload_receipt_sha256": exec_module.sha(preload.read_bytes()),
            "composed_prompt_sha256": preload_data["composed_prompt_sha256"],
            "run_id": "run-1", "agent_id": child["id"], "parent_id": "controller-1",
            "wave_id": definition["wave_id"], "round": 1, "depth": 1,
            "provider_request_id": f"request-{index}",
            "terminal_state": "COMPLETED",
            "output_sha256": output_hash,
        }), encoding="utf-8")
        tool_rows = []
        for capability in child["tools"]:
            tool_path = cell / f"tool-{capability}.json"
            tool_path.write_text(json.dumps({"schema": "constraintbox.tool-observation.v1", "capability": capability, "target_sha256": "b" * 64}), encoding="utf-8")
            tool_rows.append({"capability": capability, "receipt_path": str(tool_path), "receipt_sha256": exec_module.sha(tool_path.read_bytes())})
        children.append({
            "child_id": child["id"],
            "agent_id": child["id"],
            "terminal_state": "COMPLETED",
            "preload_receipt": str(preload),
            "provider_call_receipt": str(call),
            "output_path": str(output),
            "output_sha256": output_hash,
            "tool_observations": tool_rows,
        })
    wave_output = tmp_path / "wave-output.md"
    wave_output.write_text("wave result", encoding="utf-8")
    execution = tmp_path / "execution.json"
    execution.write_text(json.dumps({
        "schema": "constraintbox.wave-execution.v1",
        "wave_id": definition["wave_id"],
        "state": "COMPLETE",
        "run_id": "run-1",
        "controller_agent_id": "controller-1",
        "depth": 0,
        "round": 1,
        "target_sha256": "b" * 64,
        "mmm_root": str(mmm_root),
        "children": children,
        "cancellation_state": "NOT_CANCELLED",
        "disagreement_state": [],
        "repair_digest": "c" * 64,
        "rerun_delta": {},
        "output_path": str(wave_output),
        "output_sha256": exec_module.sha(wave_output.read_bytes()),
    }), encoding="utf-8")
    assert exec_module.verify(definition_path, execution) == []
    broken = json.loads(execution.read_text(encoding="utf-8"))
    broken["children"][0]["tool_observations"] = []
    execution.write_text(json.dumps(broken), encoding="utf-8")
    assert f"tool_evidence:{children[0]['child_id']}" in exec_module.verify(definition_path, execution)
    execution.write_text(json.dumps({**broken, "children": children}), encoding="utf-8")
    Path(children[0]["provider_call_receipt"]).unlink()
    assert f"missing_call_chain:{children[0]['child_id']}" in exec_module.verify(definition_path, execution)


def test_nested_wave_placeholder_is_refused(tmp_path: Path) -> None:
    definition_path = ROOT / "cb-failure-wave/wave.json"
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    placeholder = tmp_path / "placeholder.json"
    placeholder.write_text("not a wave receipt", encoding="utf-8")
    execution = tmp_path / "execution.json"
    execution.write_text(json.dumps({
        "schema": "constraintbox.wave-execution.v1", "wave_id": definition["wave_id"],
        "state": "PARTIAL", "run_id": "r", "controller_agent_id": "c", "depth": 0,
        "round": 1, "target_sha256": "a" * 64, "mmm_root": str(tmp_path),
        "children": [{"child_id": row["id"], "agent_id": row["id"], "terminal_state": "FAILED", "child_wave_receipt": str(placeholder)} for row in definition["children"]],
        "cancellation_state": "NOT_CANCELLED", "disagreement_state": [],
        "output_path": str(placeholder), "output_sha256": exec_module.sha(placeholder.read_bytes()),
        "repair_digest": "b" * 64, "rerun_delta": {},
    }), encoding="utf-8")
    errors = exec_module.verify(definition_path, execution)
    assert any("invalid_execution:JSONDecodeError" in error for error in errors)
