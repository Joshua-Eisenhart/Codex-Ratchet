from __future__ import annotations

import json
import pathlib
import subprocess


CB = pathlib.Path(__file__).resolve().parents[1]


def test_light_executable_surface_has_no_heavy_dependency(
    tmp_path: pathlib.Path,
) -> None:
    output = tmp_path / "light-heavy-audit.json"
    completed = subprocess.run(
        [
            str(CB / ".venv/bin/python"),
            "-I",
            str(CB / "scripts/audit_cb_light_heavy_separation.py"),
            "--output",
            str(output),
        ],
        cwd=CB,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    body = json.loads(output.read_text(encoding="utf-8"))
    assert body["disposition"] == "ADMIT"
    assert body["reason_code"] == "LIGHT_PACKAGE_AND_FRESH_INTERPRETER_HAVE_NO_HEAVY_SURFACE"
    failures = body["failures"]
    assert failures["forbidden_candidate_names"] == []
    assert failures["forbidden_python_imports"] == {}
    assert failures["forbidden_shell_or_config_references"] == {}
    assert failures["forbidden_direct_dependencies"] == []
    assert failures["manifest_sim_engine_members"] == 0
    assert failures["audit_source_bound"] is True
    fresh = failures["fresh_wheel_probe"]
    assert fresh["passed"] is True
    assert fresh["reason_code"] == "LIGHT_WHEEL_FRESH_IMPORT_SEPARATION_VERIFIED"
    assert fresh["build_source"] == "VERIFIER_OWNED_TEMPORARY_COPY"
    assert fresh["package_under_fresh_prefix"] is True
    assert fresh["hookkernel_under_fresh_prefix"] is True
    assert fresh["fresh_observation"]["legacy_entrypoint_present"] is False
    assert set(fresh["fresh_observation"]["attempts"].values()) == {"MISSING"}
    assert not any(fresh["fresh_observation"]["find_spec"].values())
    assert fresh["fresh_observation"]["wheel_forbidden_paths"] == []
    assert fresh["fresh_observation"]["unexpected_hookkernel_python_paths"] == []
    assert fresh["fresh_observation"]["missing_hookkernel_python_paths"] == []
    assert fresh["fresh_observation"]["domain_compiled"] is True
    contained = failures["contained_runtime_probe"]
    assert contained["passed"] is True
    assert contained["reason_code"] == "CONTAINED_LIGHT_RUNTIME_SEPARATION_VERIFIED"
    assert contained["package_under_contained_prefix"] is True
    assert contained["hookkernel_under_contained_prefix"] is True
    assert contained["contained_observation"]["unexpected_hookkernel_python_paths"] == []
    assert contained["contained_observation"]["missing_hookkernel_python_paths"] == []
    assert not (CB / "light_runtime" / "build").exists()
    assert not (CB / "light_runtime" / "constraintbox.egg-info").exists()


def test_two_fresh_boundary_audits_do_not_share_build_state(
    tmp_path: pathlib.Path,
) -> None:
    """Live read gates must not mutate or race the Light source directory."""

    command = [
        str(CB / ".venv/bin/python"),
        "-I",
        str(CB / "scripts/audit_cb_light_heavy_separation.py"),
    ]
    first = subprocess.Popen(
        [*command, "--output", str(tmp_path / "first.json")],
        cwd=CB,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    second = subprocess.Popen(
        [*command, "--output", str(tmp_path / "second.json")],
        cwd=CB,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    first_stdout, first_stderr = first.communicate(timeout=180)
    second_stdout, second_stderr = second.communicate(timeout=180)
    assert first.returncode == 0, first_stdout + first_stderr
    assert second.returncode == 0, second_stdout + second_stderr
    for name in ("first.json", "second.json"):
        body = json.loads((tmp_path / name).read_text(encoding="utf-8"))
        assert body["disposition"] == "ADMIT"
        assert body["failures"]["fresh_wheel_probe"]["build_source"] == (
            "VERIFIER_OWNED_TEMPORARY_COPY"
        )
    assert not (CB / "light_runtime" / "build").exists()
    assert not (CB / "light_runtime" / "constraintbox.egg-info").exists()


def test_audit_recognizes_a_literal_dynamic_heavy_import(tmp_path: pathlib.Path) -> None:
    """The static half does not overlook the lazy-import bypass we rejected."""

    source = tmp_path / "dynamic_import.py"
    source.write_text("module = __import__('torch')\n", encoding="utf-8")
    script = CB / "scripts/audit_cb_light_heavy_separation.py"
    namespace: dict[str, object] = {"__file__": str(script), "__name__": "audit_probe"}
    exec(compile(script.read_text(encoding="utf-8"), str(script), "exec"), namespace)
    assert "torch" in namespace["python_imports"](source)
