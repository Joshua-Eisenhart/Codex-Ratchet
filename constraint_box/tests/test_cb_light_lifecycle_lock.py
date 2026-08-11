from __future__ import annotations

from contextlib import nullcontext
import json
from pathlib import Path
import subprocess
import sys

import pytest


CB = Path(__file__).resolve().parents[1]
if str(CB) not in sys.path:
    sys.path.insert(0, str(CB))


def test_lifecycle_lock_refuses_a_second_authoritative_writer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from hooks import cb_light_hook

    lock = tmp_path / "cb-light.lock"
    monkeypatch.setattr(cb_light_hook, "LIFECYCLE_LOCK", lock)
    with cb_light_hook.lifecycle_lock():
        with pytest.raises(cb_light_hook.HookRefusal) as raised:
            with cb_light_hook.lifecycle_lock():
                pass
    assert raised.value.reason_code == "CB_LIGHT_LIFECYCLE_LOCK_HELD"
    assert not lock.exists()


def test_lifecycle_lock_refuses_a_real_second_process(tmp_path: Path) -> None:
    """O_EXCL is exercised across processes, not merely nested contexts."""

    worker = """
import json
from pathlib import Path
import sys
import time

root = Path(sys.argv[1])
lock_path = Path(sys.argv[2])
hold = sys.argv[3] == 'hold'
sys.path.insert(0, str(root))
from hooks import cb_light_hook

cb_light_hook.LIFECYCLE_LOCK = lock_path
try:
    with cb_light_hook.lifecycle_lock():
        print(json.dumps({'state': 'ACQUIRED'}), flush=True)
        if hold:
            time.sleep(5)
except cb_light_hook.HookRefusal as exc:
    print(json.dumps({'state': 'REFUSED', 'reason_code': exc.reason_code}), flush=True)
    raise SystemExit(2)
"""
    lock = tmp_path / "cross-process.lock"
    first = subprocess.Popen(
        [sys.executable, "-I", "-u", "-c", worker, str(CB), str(lock), "hold"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert first.stdout is not None
        assert json.loads(first.stdout.readline()) == {"state": "ACQUIRED"}
        second = subprocess.run(
            [sys.executable, "-I", "-u", "-c", worker, str(CB), str(lock), "once"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        assert second.returncode == 2, second.stdout + second.stderr
        assert json.loads(second.stdout) == {
            "state": "REFUSED",
            "reason_code": "CB_LIGHT_LIFECYCLE_LOCK_HELD",
        }
    finally:
        first_stdout, first_stderr = first.communicate(timeout=30)
        assert first.returncode == 0, first_stdout + first_stderr
    assert not lock.exists()


def test_installed_light_package_integrity_rejects_manifest_ahead_of_wheel() -> None:
    """A refreshed manifest alone cannot bless an older installed controller."""

    from hooks import cb_light_hook

    manifest = cb_light_hook.load_json(cb_light_hook.MANIFEST)
    current_ok, current_reason, current_evidence = (
        cb_light_hook.installed_light_package_source_integrity(manifest)
    )
    assert current_ok is True, current_reason
    assert current_evidence["missing_paths"] == []
    assert current_evidence["unexpected_paths"] == []
    assert current_evidence["hash_mismatch_paths"] == []

    ahead = json.loads(json.dumps(manifest))
    target = "light_runtime/src/constraintbox/core_cli.py"
    ahead["source_hashes"][target] = "0" * 64
    ahead_ok, ahead_reason, ahead_evidence = (
        cb_light_hook.installed_light_package_source_integrity(ahead)
    )
    assert ahead_ok is False
    assert ahead_reason.startswith("INSTALLED_LIGHT_PACKAGE_SOURCE_HASH_MISMATCH")
    assert ahead_evidence["hash_mismatch_paths"] == [target]


def test_complete_cli_reports_the_same_live_evaluation_used_for_its_hold(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import cb_light_cli

    monkeypatch.setattr(
        cb_light_cli,
        "verify_completion_state",
        lambda **_: (
            False,
            "SYSTEM_COMPLETION_NOT_EARNED:PORTABLE_ADOPTION_OWNER_APPROVAL_"
            "REAL_CONSUMER_AND_HEAVY_PROFILE_PENDING",
            True,
            "CB_LIGHT_EVALUATION_VERIFIED:selected=86,held=5,excluded_before_install=15",
        ),
    )

    assert cb_light_cli.main(["complete"]) == 2
    body = json.loads(capsys.readouterr().out)
    assert body["completion_allowed"] is False
    assert body["evaluation_allowed"] is True
    assert body["evaluation_reason_code"].startswith("CB_LIGHT_EVALUATION_VERIFIED")


def test_complete_cli_does_not_print_a_stale_evaluation_after_live_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from scripts import cb_light_cli

    monkeypatch.setattr(
        cb_light_cli,
        "verify_completion_state",
        lambda **_: (
            False,
            "LIVE_LIGHT_HEAVY_SEPARATION_AUDIT_FAILED:rc=2",
            False,
            "LIVE_LIGHT_HEAVY_SEPARATION_AUDIT_FAILED:rc=2",
        ),
    )

    assert cb_light_cli.main(["complete"]) == 2
    body = json.loads(capsys.readouterr().out)
    assert body["completion_allowed"] is False
    assert body["evaluation_allowed"] is False
    assert body["reason_code"] == body["evaluation_reason_code"]


def test_refresh_cli_renders_a_lock_refusal_as_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    from hooks.cb_light_hook import HookRefusal
    from scripts import cb_light_cli

    def refuse() -> None:
        raise HookRefusal("CB_LIGHT_LIFECYCLE_LOCK_HELD", "{\"pid\": 123}")

    monkeypatch.setattr(cb_light_cli, "refresh", refuse)
    assert cb_light_cli.main(["refresh"]) == 2
    body = json.loads(capsys.readouterr().out)
    assert body == {
        "command": "refresh",
        "completion_allowed": False,
        "detail": "{\"pid\": 123}",
        "disposition": "HOLD",
        "evaluation_allowed": False,
        "reason_code": "CB_LIGHT_LIFECYCLE_LOCK_HELD",
        "schema": "constraintbox.cb-light-command-refusal.v1",
    }


def test_explicit_manifest_rebuild_is_serialized_before_broker_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import cb_light_cli

    calls: list[str] = []
    monkeypatch.setattr(cb_light_cli, "lifecycle_lock", lambda: nullcontext())
    monkeypatch.setattr(
        cb_light_cli,
        "_rebuild_manifest_under_lifecycle_lock",
        lambda: calls.append("rebuild") or 0,
    )
    monkeypatch.setattr(cb_light_cli, "_install", lambda: calls.append("install") or 0)

    assert cb_light_cli.install(rebuild_manifest=True) == 0
    assert calls == ["rebuild", "install"]


def test_install_cli_routes_explicit_manifest_rebuild_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from scripts import cb_light_cli

    observed: dict[str, bool] = {}

    def fake_install(*, rebuild_manifest: bool) -> int:
        observed["rebuild_manifest"] = rebuild_manifest
        return 0

    monkeypatch.setattr(
        cb_light_cli,
        "install",
        fake_install,
    )

    assert cb_light_cli.main(["install", "--rebuild-manifest"]) == 0
    assert observed == {"rebuild_manifest": True}


def test_lifecycle_cli_binds_its_checkout_before_importing_installed_runtime(
    tmp_path: Path,
) -> None:
    """An external working directory cannot make the wheel use site-packages as ROOT."""

    script = CB / "scripts" / "cb_light_cli.py"
    worker = """
import importlib.util
import json
from pathlib import Path
import sys

script = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("isolated_cb_light_cli", script)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

seen = []
class Completed:
    returncode = 0
def fake_run(command, **kwargs):
    seen.append(command)
    return Completed()

module.subprocess.run = fake_run
result = module._rebuild_manifest_under_lifecycle_lock()
print(json.dumps({
    "result": result,
    "root": str(module.ROOT),
    "mandated": str(module.MANDATED_INTERPRETER),
    "build": str(module.BUILD_INTERPRETER),
    "command": seen[0],
}, sort_keys=True))
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", worker, str(script)],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    observed = json.loads(completed.stdout)
    assert observed["result"] == 0
    assert observed["root"] == str(CB)
    assert observed["mandated"].startswith(str(CB / ".venv"))
    assert observed["command"][0] == observed["build"]
    assert "site-packages/.venv" not in observed["mandated"]
    assert "site-packages/.venv" not in observed["command"][0]


def test_lifecycle_venv_creation_uses_base_builder_and_platform_layout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from scripts import cb_light_cli

    observed: list[list[str]] = []

    class Completed:
        returncode = 0

    monkeypatch.setattr(cb_light_cli, "BUILD_INTERPRETER", tmp_path / "base-python")
    monkeypatch.setattr(
        cb_light_cli,
        "subprocess",
        type(
            "Subprocess",
            (),
            {
                "run": staticmethod(
                    lambda command, **kwargs: observed.append(command) or Completed()
                )
            },
        ),
    )

    target = tmp_path / "fresh"
    assert cb_light_cli._create_venv(target) == 0
    assert observed == [
        [str(tmp_path / "base-python"), "-m", "venv", "--clear", str(target)]
    ]
    assert cb_light_cli._venv_python(target, platform_name="posix") == (
        target / "bin" / "python"
    )
    assert cb_light_cli._venv_python(target, platform_name="nt") == (
        target / "Scripts" / "python.exe"
    )
