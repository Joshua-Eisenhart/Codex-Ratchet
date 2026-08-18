from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"


def _relocated_source(tmp_path: Path) -> Path:
    destination = tmp_path / "bundle" / "src"
    shutil.copytree(SOURCE_ROOT, destination)
    return destination


def _run(source: Path, tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(source),
        "PYTHONNOUSERSITE": "1",
    }
    return subprocess.run(
        [sys.executable, "-m", "constraintbox_zip_agent", *args],
        cwd=str(tmp_path),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_relocated_zip_source_can_show_help_without_controller_or_sibling(tmp_path: Path) -> None:
    source = _relocated_source(tmp_path)
    result = _run(source, tmp_path, "--help")
    assert result.returncode == 0, result.stderr
    assert "build-demo" in result.stdout
    assert "ModuleNotFoundError" not in result.stderr


def test_relocated_zip_source_runs_model_free_demo_without_controller(tmp_path: Path) -> None:
    source = _relocated_source(tmp_path)
    packet = tmp_path / "demo.zip"
    returned = tmp_path / "return.zip"
    built = _run(source, tmp_path, "build-demo", "--out", str(packet))
    assert built.returncode == 0, built.stderr
    ran = _run(source, tmp_path, "run", str(packet), "--return-zip", str(returned))
    assert ran.returncode == 0, ran.stderr
    assert returned.is_file()


def test_relocated_zip_source_imports_provider_module_without_controller(tmp_path: Path) -> None:
    source = _relocated_source(tmp_path)
    script = (
        "import constraintbox_zip_agent.provider_task as p; "
        "print(p.REQUEST_SCHEMA)"
    )
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(source),
        "PYTHONNOUSERSITE": "1",
    }
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(tmp_path),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "constraintbox.provider-zip-task-request.v1" in result.stdout
