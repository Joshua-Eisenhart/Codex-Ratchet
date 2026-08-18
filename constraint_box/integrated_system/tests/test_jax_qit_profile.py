from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


PROFILE_ROOT = Path(__file__).parents[1] / "runtime_profiles" / "jax_qit"
BOOTSTRAP_PATH = PROFILE_ROOT / "bootstrap_jax_qit.py"
spec = importlib.util.spec_from_file_location("cb_jax_qit_bootstrap", BOOTSTRAP_PATH)
assert spec is not None and spec.loader is not None
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


def test_default_target_is_project_neutral_and_configurable(tmp_path: Path) -> None:
    target = bootstrap.resolve_target(environ={"XDG_DATA_HOME": str(tmp_path / "data")})
    assert target == (tmp_path / "data" / "jax-qit-stack").resolve()
    explicit = bootstrap.resolve_target(tmp_path / "explicit")
    assert explicit == (tmp_path / "explicit").resolve()


def test_plan_is_lock_bound_and_has_no_product_runtime_path(tmp_path: Path) -> None:
    plan = bootstrap.build_plan(
        target=tmp_path / "jax-qit-stack",
        python_executable="python3.13",
        installer="pip",
    )
    assert plan["installer"] == "pip"
    assert plan["inputs"]["lock"] == "requirements.lock"
    assert len(plan["inputs"]["lock_sha256"]) == 64
    rendered = json.dumps(plan, sort_keys=True)
    for forbidden in ("system_v", "Archive", "Codex-Ratchet", "constraint_box", "sim-stack"):
        assert forbidden not in rendered


def test_install_commands_use_exact_lock_and_do_not_install_into_profile(tmp_path: Path) -> None:
    target = tmp_path / "jax-qit-stack"
    commands = bootstrap.install_commands(
        target=target,
        python_executable="python3.13",
        installer="pip",
    )
    assert commands[0] == ["python3.13", "-m", "venv", str(target)]
    assert commands[1][-2:] == ["--requirement", str(PROFILE_ROOT / "requirements.lock")]
    assert all(str(PROFILE_ROOT) not in command[-1:] for command in commands[:1])


def test_uv_plan_is_inspectable_without_running_uv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bootstrap.shutil, "which", lambda name: "/fake/uv" if name == "uv" else None)
    target = tmp_path / "jax-qit-stack"
    commands = bootstrap.install_commands(
        target=target,
        python_executable="python3.13",
        installer="uv",
    )
    assert commands[0][:3] == ["/fake/uv", "venv", "--python"]
    assert commands[1][:3] == ["/fake/uv", "pip", "sync"]
    assert commands[1][-1] == str(PROFILE_ROOT / "requirements.lock")


def test_profile_refuses_target_inside_product(tmp_path: Path) -> None:
    with pytest.raises(bootstrap.BootstrapError, match="REFUSE_TARGET_INSIDE_PRODUCT_PROFILE"):
        bootstrap.build_plan(
            target=PROFILE_ROOT / "would-overwrite-product",
            python_executable="python3.13",
            installer="pip",
        )


def test_existing_unowned_target_is_refused(tmp_path: Path) -> None:
    target = tmp_path / "not-a-profile"
    target.mkdir()
    (target / "unrelated.txt").write_text("keep me", encoding="utf-8")
    with pytest.raises(bootstrap.BootstrapError, match="REFUSE_TARGET_NOT_OWNED"):
        bootstrap._target_is_safe(target)


def test_normal_probe_on_unowned_target_holds_without_writing(tmp_path: Path) -> None:
    target = tmp_path / "existing-runtime"
    target.mkdir()
    sentinel = target / "keep.txt"
    sentinel.write_text("untouched", encoding="utf-8")
    before = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
    result = bootstrap.attest_existing(target)
    after = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
    assert result == {"status": "HOLD", "reason_code": "HOLD_TARGET_NOT_OWNED", "target": str(target)}
    assert before == after
    assert sentinel.read_text(encoding="utf-8") == "untouched"


def _fake_external_target(tmp_path: Path) -> Path:
    target = tmp_path / "external-runtime"
    (target / "bin").mkdir(parents=True)
    (target / "bin" / "python").write_text("placeholder", encoding="utf-8")
    (target / "user-file.txt").write_text("preserve", encoding="utf-8")
    return target


def test_explicit_adoption_writes_metadata_only_after_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _fake_external_target(tmp_path)
    installer_called = False

    def forbidden_installer(*args, **kwargs):
        nonlocal installer_called
        installer_called = True
        raise AssertionError("adoption must not invoke an installer")

    monkeypatch.setattr(bootstrap, "_run_commands", forbidden_installer)
    monkeypatch.setattr(bootstrap, "verify_locked_distributions", lambda target: {"status": "PASS", "expected_count": 112})
    monkeypatch.setattr(
        bootstrap,
        "run_probe",
        lambda target, **kwargs: {"status": "PASS", "returncode": 0, "probe": {"passed": 12, "failed": 0}},
    )
    result = bootstrap.adopt_existing(target)
    assert result["status"] == "PASS"
    assert result["mode"] == "ADOPT_EXISTING"
    assert installer_called is False
    assert (target / bootstrap.STATE_FILE).is_file()
    assert (target / "PROBE_RECEIPT.json").is_file()
    assert (target / "STACK_MANIFEST.json").is_file()
    assert (target / "user-file.txt").read_text(encoding="utf-8") == "preserve"


def test_adoption_version_mismatch_refuses_before_any_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _fake_external_target(tmp_path)
    sentinel_before = sorted(path.relative_to(target).as_posix() for path in target.rglob("*"))
    expected = bootstrap.locked_distributions()
    observed = dict(expected)
    observed["jax"] = "0.0.0"

    def fake_metadata_runner(argv, **kwargs):
        assert argv[1:3] == ["-I", "-c"]
        return SimpleNamespace(returncode=0, stdout=json.dumps(observed), stderr="")

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_metadata_runner)
    result = bootstrap.adopt_existing(target)
    assert result["status"] == "REFUSE"
    assert result["reason_code"] == "REFUSE_LOCK_MISMATCH"
    assert "jax" in result["mismatched"]
    assert sorted(path.relative_to(target).as_posix() for path in target.rglob("*")) == sentinel_before
    assert not (target / bootstrap.STATE_FILE).exists()
    assert not (target / "PROBE_RECEIPT.json").exists()


def test_lock_verification_reads_metadata_and_does_not_mutate_packages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _fake_external_target(tmp_path)
    expected = bootstrap.locked_distributions()
    calls: list[list[str]] = []

    def fake_metadata_runner(argv, **kwargs):
        calls.append([str(item) for item in argv])
        return SimpleNamespace(returncode=0, stdout=json.dumps(expected), stderr="")

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_metadata_runner)
    before = (target / "user-file.txt").read_bytes()
    result = bootstrap.verify_locked_distributions(target)
    assert result["status"] == "PASS"
    assert len(calls) == 1
    assert calls[0][1:3] == ["-I", "-c"]
    assert "pip" not in calls[0] and "uv" not in calls[0]
    assert (target / "user-file.txt").read_bytes() == before
    assert not (target / bootstrap.STATE_FILE).exists()


def test_attestation_is_bounded_and_marks_runtime_as_external(tmp_path: Path) -> None:
    target = tmp_path / "jax-qit-stack"
    target.mkdir()
    for name in ("requirements.in", "requirements.lock", "probe_runtime.py"):
        source = PROFILE_ROOT / name
        (target / name).write_bytes(source.read_bytes())
    manifest = bootstrap.write_attestation(
        target,
        {
            "status": "PASS",
            "returncode": 0,
            "probe": {"passed": 12, "failed": 0, "results": {}},
        },
    )
    assert manifest["status"] == "VERIFIED_LOCAL"
    assert manifest["boundaries"]["cb_light_runtime"] is False
    assert manifest["boundaries"]["project_source_installed"] is False
    assert manifest["promotion_allowed"] is False
    receipt = json.loads((target / "PROBE_RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["profile"] == "jax_qit"
    assert receipt["probe"]["passed"] == 12


def test_fake_runner_can_exercise_install_command_sequence_without_installing(tmp_path: Path) -> None:
    target = tmp_path / "jax-qit-stack"
    calls: list[list[str]] = []

    def fake_runner(argv, **kwargs):
        calls.append([str(item) for item in argv])
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    bootstrap._run_commands(
        bootstrap.install_commands(
            target=target,
            python_executable="python3.13",
            installer="pip",
        ),
        runner=fake_runner,
    )
    assert len(calls) == 2
    assert not target.exists()
