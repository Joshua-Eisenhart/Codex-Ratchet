from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


BOX = Path(__file__).resolve().parents[2]
SCRIPT = BOX / "integrated_system" / "scripts" / "run_constraint_path_mass.py"
LIGHT_SOURCE = BOX / "light_runtime" / "src" / "constraintbox"
ROOT_SOURCE = BOX / "src" / "constraintbox"
MERGED_SOURCE = BOX / "integrated_system" / "runtime" / "controller_src" / "constraintbox"
SELECTED_SOURCE = ROOT_SOURCE if ROOT_SOURCE.is_dir() else MERGED_SOURCE
SELECTED_ROOT_FILES = ("bound_quotient.py", "constraint_path_mass.py")
FIXTURE = BOX / "fixtures" / "minilev" / "proposal_reference_policy_v1.json"


def _fresh_merged_controller(tmp_path: Path) -> tuple[Path, Path]:
    """Build only the merged controller closure used by a fresh extract."""

    root = tmp_path / "PROJECT" / "constraint_box"
    controller = root / "integrated_system" / "runtime" / "controller_src"
    script = root / "integrated_system" / "scripts" / SCRIPT.name
    package = controller / "constraintbox"
    shutil.copytree(LIGHT_SOURCE, package)
    for name in SELECTED_ROOT_FILES:
        shutil.copy2(SELECTED_SOURCE / name, package / name)
    assert not (package / "proposal_minilev_flow.py").exists()
    assert not (package / "mini_levos.py").exists()
    fixture = root / "fixtures" / "minilev" / FIXTURE.name
    fixture.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(FIXTURE, fixture)
    script.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SCRIPT, script)
    return root, script


def _run(script: Path, output: Path, *extra: str) -> dict[str, object]:
    env = os.environ.copy()
    env.update({"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    completed = subprocess.run(
        [sys.executable, str(script), "--out", str(output), *extra],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    return json.loads(completed.stdout)


def test_public_wrapper_runs_from_fresh_merged_controller(tmp_path: Path) -> None:
    _root, script = _fresh_merged_controller(tmp_path)
    output = tmp_path / "runs" / "result.json"
    summary = _run(script, output)
    assert summary["status"] == "PASS"
    assert summary["n_paths"] == 14
    assert summary["smt_real"] == "BOUNDED_SAT"
    assert summary["smt_erased"] == "BOUNDED_UNSAT"
    assert output.is_file()


def test_public_wrapper_replays_fresh_receipt(tmp_path: Path) -> None:
    _root, script = _fresh_merged_controller(tmp_path)
    output = tmp_path / "runs" / "result.json"
    _run(script, output)
    replay = _run(script, output, "--replay", str(output))
    assert replay["status"] == "PASS"
    assert replay["stored_receipt_sha256"] == replay["replayed_receipt_sha256"]


def test_public_wrapper_uses_declared_external_jax_if_available(tmp_path: Path) -> None:
    interpreter = os.environ.get("CB_JAX_PYTHON")
    if not interpreter or not Path(interpreter).is_file():
        return
    _root, script = _fresh_merged_controller(tmp_path)
    output = tmp_path / "runs" / "jax-result.json"
    summary = _run(
        script,
        output,
        "--jax-python",
        interpreter,
        "--require-jax",
    )
    assert summary["status"] == "PASS"
    assert summary["jax"]["status"] == "PASS"


def test_public_source_has_no_legacy_runtime_binding() -> None:
    text = (SELECTED_SOURCE / "constraint_path_mass.py").read_text(
        encoding="utf-8"
    )
    for forbidden in ("/Users/", "/home/", "Archive", "system_v", "Codex-Ratchet"):
        assert forbidden not in text
