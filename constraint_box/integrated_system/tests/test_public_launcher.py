from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import json


LAUNCHER = Path(__file__).resolve().parents[1] / "bin" / "cb"
SPEC = importlib.util.spec_from_loader(
    "integrated_cb_launcher", SourceFileLoader("integrated_cb_launcher", str(LAUNCHER))
)
assert SPEC is not None and SPEC.loader is not None
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


def test_bootstrap_refuses_incomplete_box_before_install(tmp_path: Path) -> None:
    assert launcher.bootstrap_light(tmp_path) == 2


def test_launcher_exposes_bootstrap_before_light_resolution() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert 'sub.add_parser("bootstrap-light")' in source
    assert source.index('if args.command == "bootstrap-light"') < source.index(
        "light = declared_python"
    )
    assert '"jax-profile"' in source
    assert source.index('if args.command == "jax-profile"') < source.index(
        "light = declared_python"
    )
    assert '"PYTHONPATH": str(box / "light_runtime" / "src")' in source
    assert '"CB_LIGHT_BUILD_INTERPRETER": str(builder_python)' in source


def test_source_runtime_never_places_mixed_root_package_on_pythonpath(tmp_path: Path) -> None:
    box = tmp_path / "constraint_box"
    system = box / "integrated_system"
    light = box / ".venv" / "bin" / "python"
    env = launcher.runtime_env(box, system, light)
    roots = env["PYTHONPATH"].split(launcher.os.pathsep)
    assert str(box / "src") not in roots
    assert roots == [str(box / "zip_agent" / "src"), str(box / "light_runtime" / "src")]
    assert env["CB_MMM_PACKS_ROOT"] == str(box / "mmm" / "packs")


def test_bundle_runtime_uses_merged_controller_and_zip_agent_roots(tmp_path: Path) -> None:
    box = tmp_path / "PROJECT" / "constraint_box"
    system = box / "integrated_system"
    controller = system / "runtime" / "controller_src"
    zip_runtime = system / "runtime" / "zip_agent_src"
    controller.mkdir(parents=True)
    zip_runtime.mkdir(parents=True)
    light = box / ".venv" / "bin" / "python"
    roots = launcher.runtime_env(box, system, light)["PYTHONPATH"].split(launcher.os.pathsep)
    assert roots == [str(zip_runtime), str(controller)]


def test_runtime_binds_separate_build_interpreter_when_present(tmp_path: Path) -> None:
    box = tmp_path / "constraint_box"
    system = box / "integrated_system"
    build_python = box / ".bootstrap-light-build" / "bin" / "python"
    build_python.parent.mkdir(parents=True)
    build_python.write_text("", encoding="utf-8")
    env = launcher.runtime_env(box, system, box / ".venv/bin/python")
    assert env["CB_LIGHT_BUILD_INTERPRETER"] == str(build_python)


def test_jax_version_profile_is_explicit() -> None:
    assert launcher.supported_jax_version("0.10.1") is True
    assert launcher.supported_jax_version("0.10.9") is True
    assert launcher.supported_jax_version("0.11.0") is False
    assert launcher.supported_jax_version("unknown") is False


def test_default_jax_route_is_project_neutral(tmp_path: Path, monkeypatch) -> None:
    data = tmp_path / "data"
    python = data / "jax-qit-stack" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o755)
    monkeypatch.setenv("XDG_DATA_HOME", str(data))
    monkeypatch.delenv("CB_JAX_QIT_ROOT", raising=False)
    assert launcher.default_jax_python() == python


def test_public_wave_surface_is_exposed_without_provider_policy() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert 'sub.add_parser("wave"' in source
    assert 'scripts/run_wave.py' in source
    assert "grok-4" not in source
    assert "claude-" not in source


def test_public_path_mass_surface_binds_contained_fixture() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"path-mass"' in source
    assert "scripts/run_constraint_path_mass.py" in source
    assert "fixtures/minilev/proposal_reference_policy_v1.json" in source


def test_jax_profile_attestation_binds_product_lock(tmp_path: Path) -> None:
    system = tmp_path / "integrated_system"
    lock = system / "runtime_profiles" / "jax_qit" / "requirements.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("jax==0.10.1\n", encoding="utf-8")
    runtime = tmp_path / "jax-qit-stack"
    python = runtime / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    manifest = {
        "schema": "constraintbox.jax-qit-stack-manifest.v1",
        "profile": "jax_qit",
        "status": "VERIFIED_LOCAL",
        "requirements": {"lock_sha256": launcher.sha256_file(lock)},
    }
    (runtime / "STACK_MANIFEST.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    observed = launcher.jax_profile_attestation(system, python)
    assert observed["status"] == "PASS"
    lock.write_text("jax==0.10.2\n", encoding="utf-8")
    drifted = launcher.jax_profile_attestation(system, python)
    assert drifted["status"] == "HOLD"
    assert drifted["reason"] == "HOLD_JAX_PROFILE_ATTESTATION_DRIFT"
