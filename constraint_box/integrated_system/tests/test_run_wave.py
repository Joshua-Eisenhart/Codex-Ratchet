from __future__ import annotations

import json
import importlib.util
import os
import shutil
import sys
from pathlib import Path

SYSTEM = Path(__file__).resolve().parents[1]
SCRIPT = SYSTEM / "scripts" / "run_wave.py"
SPEC = importlib.util.spec_from_file_location("integrated_run_wave", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def _copy_tree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def _fixture(tmp_path: Path) -> Path:
    """Create a small extracted product with the pinned runnable cohort."""

    system = tmp_path / "integrated_system"
    skills = system / "skills"
    skills.mkdir(parents=True)
    shutil.copy2(SYSTEM / "skills" / "ACTIVE_WAVES.json", skills / "ACTIVE_WAVES.json")
    for name in (
        "cb-maintenance-wave",
        "cb-context-strategy-wave",
        "cb-exploration-wave",
    ):
        _copy_tree(SYSTEM / "skills" / name, skills / name)

    (system / "context" / "current").mkdir(parents=True)
    (system / "context" / "current" / "prompt.md").write_text(
        "> owner prompt: preserve the finite object\n", encoding="utf-8"
    )
    (system / "context" / "full").mkdir(parents=True)
    (system / "context" / "full" / "prompt_plan_progress_corpus.jsonl").write_text(
        "{\"event\":\"owner prompt\"}\n", encoding="utf-8"
    )
    (system / "fixtures").mkdir(parents=True)
    (system / "fixtures" / "structured_open_bind_v1.json").write_text("{}\n", encoding="utf-8")
    (system / "state").mkdir(parents=True)
    (system / "state" / "GENESIS.json").write_text(
        '{"status":"HOLD_TEST"}\n', encoding="utf-8"
    )
    (system / "WHAT_IS_PROVEN.md").write_text(
        "# Verified output vocabulary\n\nREFUSE_TEST and HOLD_TEST remain visible.\n",
        encoding="utf-8",
    )
    (system / "runs").mkdir(parents=True)
    for path in (
        system / "scripts",
        system / "mmms" / "primary" / "mini",
        system / "light_runtime" / "src",
        system.parent / "light_runtime" / "src",
        system.parent / "zip_agent" / "src",
    ):
        path.mkdir(parents=True, exist_ok=True)
    (system.parent / "zip_agent").mkdir(exist_ok=True)
    return system


def test_list_distinguishes_runnable_cohort_from_inactive_specs(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    listing = runner.list_waves(system_root=system)
    assert [row["wave_id"] for row in listing["runnable_cohort"]] == [
        "cb-context-strategy-wave",
        "cb-exploration-wave",
        "cb-maintenance-wave",
    ]
    inactive = {row["wave_id"] for row in listing["inactive"]}
    assert "cb-failure-wave" in inactive
    assert all(row["runnable"] for row in listing["runnable_cohort"])


def test_positive_exploration_run_has_receipted_child_and_source_hashes(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    output = system / "runs" / "public" / "positive"
    receipt = runner.run_wave(
        "cb-exploration-wave",
        system_root=system,
        output_dir=output,
        run_id="positive",
    )
    assert receipt["status"] == "PASS", receipt
    assert receipt["child_status"] == "ANTICHAIN_OPEN"
    assert receipt["subprocess"]["returncode"] == 0
    assert len(receipt["source"]) >= 2
    assert all(row.get("sha256") for row in receipt["source"])
    assert (output / "receipt.json").is_file()
    assert (output / "child.json").is_file()


def test_missing_dependency_is_hold_and_does_not_spawn(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    (system / "skills" / "cb-exploration-wave" / "scripts" / "run_exploration.py").unlink()
    inspection = runner.inspect_wave("cb-exploration-wave", system_root=system)
    assert inspection["status"] == "HOLD"
    assert inspection["reason_code"] == "MISSING_DEPENDENCY"
    receipt = runner.run_wave(
        "cb-exploration-wave",
        system_root=system,
        output_dir=system / "runs" / "public" / "missing",
    )
    assert receipt["status"] == "HOLD"
    assert receipt["subprocess"] is None


def test_tampered_source_is_held(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    script = system / "skills" / "cb-exploration-wave" / "scripts" / "run_exploration.py"
    script.write_text(script.read_text(encoding="utf-8") + "\n# tampered\n", encoding="utf-8")
    inspection = runner.inspect_wave("cb-exploration-wave", system_root=system)
    assert inspection["status"] == "HOLD"
    assert inspection["reason_code"] == "SOURCE_TAMPERED"


def test_manifest_path_escape_is_refused(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    manifest_path = system / "skills" / "ACTIVE_WAVES.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    row = next(item for item in manifest["runnable_cohort"] if item["wave_id"] == "cb-exploration-wave")
    row["script"] = "../outside.py"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    inspection = runner.inspect_wave("cb-exploration-wave", system_root=system)
    assert inspection["status"] == "HOLD"
    assert "OUTSIDE_PRODUCT" in inspection["reason_code"]


def test_preexisting_cancel_file_is_recorded_without_child_spawn(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    cancel = system / "runs" / "cancel.flag"
    cancel.write_text("cancel\n", encoding="utf-8")
    receipt = runner.run_wave(
        "cb-exploration-wave",
        system_root=system,
        output_dir=system / "runs" / "public" / "cancelled",
        cancel_file=cancel,
    )
    assert receipt["status"] == "CANCELLED"
    assert receipt["reason_code"] == "CANCELLED_BEFORE_SPAWN"
    assert receipt["subprocess"] is None


def test_subprocess_timeout_and_return_code_are_not_masked(tmp_path: Path) -> None:
    timed = runner._run_process(
        [sys.executable, "-c", "import time; time.sleep(1)"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONNOUSERSITE": "1"},
        timeout_seconds=0.03,
        cancel_file=None,
    )
    assert timed["timed_out"] is True
    assert timed["returncode"] != 0

    failed = runner._run_process(
        [sys.executable, "-c", "raise SystemExit(7)"],
        cwd=tmp_path,
        env={**os.environ, "PYTHONNOUSERSITE": "1"},
        timeout_seconds=2,
        cancel_file=None,
    )
    assert failed["timed_out"] is False
    assert failed["returncode"] == 7
