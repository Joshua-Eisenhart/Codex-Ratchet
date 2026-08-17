from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path


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
