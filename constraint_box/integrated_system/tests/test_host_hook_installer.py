from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


SYSTEM = Path(__file__).resolve().parents[1]
HOOKS = SYSTEM / "hooks"
SPEC = importlib.util.spec_from_file_location("host_hook_installer_fixture", HOOKS / "host_hook_installer.py")
assert SPEC is not None and SPEC.loader is not None
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path, dict[str, Path]]:
    product = tmp_path / "product"
    hooks = product / "integrated_system" / "hooks"
    hooks.mkdir(parents=True)
    for name in ("portable_host_hook.py", "cb_hook.sh", "codex.sh", "claude.sh", "grok.sh", "hermes.sh"):
        shutil.copy2(HOOKS / name, hooks / name)
    for name in ("cb_hook.sh", "codex.sh", "claude.sh", "grok.sh", "hermes.sh"):
        (hooks / name).chmod(0o755)
    venv = product / ".venv"
    (venv / "bin").mkdir(parents=True)
    (venv / "bin" / "python3").symlink_to(Path(sys.executable).resolve())
    (venv / "pyvenv.cfg").write_text("home = /usr/bin\nversion = fixture\n", encoding="utf-8")

    home = tmp_path / "staged-home"
    configs = {
        "codex": home / ".codex" / "hooks.json",
        "claude": home / ".claude" / "settings.json",
        "grok": home / ".grok" / "hooks.json",
        "hermes": home / ".hermes" / "config.yaml",
    }
    for path in configs.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    configs["codex"].write_text('{"keep": {"value": 1}}\n', encoding="utf-8")
    configs["claude"].write_text('{"keep": {"value": 2}, "hooks": {}}\n', encoding="utf-8")
    configs["grok"].write_text('{"keep": {"value": 3}, "hooks": {}}\n', encoding="utf-8")
    configs["hermes"].write_text("hooks:\n  pre_tool_call:\n    - matcher: terminal\n      command: echo unrelated\nkeep: true\n", encoding="utf-8")
    (home / ".grok" / "config.toml").write_text(
        "[compat.claude]\nhooks = true\n", encoding="utf-8"
    )
    return product, venv / "bin" / "python3", home, configs


def _args(product: Path, interpreter: Path, home: Path, configs: dict[str, Path]) -> dict[str, object]:
    return {
        "product_root": product,
        "light_interpreter": interpreter,
        "host_roots": {host: home for host in configs},
        "config_paths": configs,
        "grok_compat_config": home / ".grok" / "config.toml",
    }


def _plan(args: dict[str, object], run_id: str) -> dict[str, object]:
    return installer.plan_install(**args, run_id=run_id)


def _authority(plan: dict[str, object], receipt: dict[str, object]) -> dict[str, object]:
    return {
        "plan": plan,
        "expected_plan_sha256": plan["plan_sha256"],
        "expected_receipt_sha256": receipt["receipt_sha256"],
    }


def _legacy_source_args(host: str, source: Path) -> dict[str, object]:
    return {
        "legacy_hook_sources": {host: source},
        "legacy_hook_source_hashes": {host: installer._hash_file(source)},
        "legacy_hook_source_modes": {host: installer.stat.S_IMODE(source.stat().st_mode)},
    }


def _shared_git_fixture(product: Path, source: Path, root: Path) -> None:
    common = root / "shared-common.git"
    (common / "worktrees" / "product").mkdir(parents=True)
    (common / "main").mkdir()
    (common / "config").write_text("[core]\nrepositoryformatversion = 0\n", encoding="utf-8")
    (common / "worktrees" / "product" / "commondir").write_text("../..\n", encoding="utf-8")
    (common / "main" / "commondir").write_text("..\n", encoding="utf-8")
    (product / ".git").write_text(
        f"gitdir: {common / 'worktrees' / 'product'}\n", encoding="utf-8"
    )
    legacy_checkout = source.parents[3]
    (legacy_checkout / ".git").write_text(f"gitdir: {common / 'main'}\n", encoding="utf-8")


def test_plan_is_default_shape_and_does_not_mutate_staged_home(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    before = {host: path.read_bytes() for host, path in configs.items()}
    result = installer.plan_install(**_args(product, interpreter, home, configs))
    assert result["status"] == "PLAN"
    assert result["mutates"] is False
    assert result["promotion_allowed"] is False
    assert result["runtime_binding"]["hook_source_sha256"]
    assert all(path.read_bytes() == before[host] for host, path in configs.items())
    assert not (product / "integrated_system" / "runs" / "host-hook-installer").exists()


def test_apply_is_backup_first_preserves_unrelated_values_and_replays_idempotently(
    tmp_path: Path,
) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    before = {host: path.read_bytes() for host, path in configs.items()}
    first_plan = _plan(args, "first")
    first = installer.apply_install(**args, plan=first_plan)
    assert first["status"] == "APPLIED"
    assert first["runtime_binding"]["hook_source_sha256"]
    assert first["targets"][2]["route"] == "direct"
    assert first["targets"][-1]["host"] == "grok_compat"
    assert json.loads(configs["claude"].read_text(encoding="utf-8"))["keep"] == {"value": 2}
    assert "CB_PRODUCT_ROOT=" in configs["claude"].read_text(encoding="utf-8")
    assert "command: echo unrelated" in configs["hermes"].read_text(encoding="utf-8")
    backup_dir = product / "integrated_system" / "runs" / "host-hook-installer" / "first" / "backups"
    assert {path.name for path in backup_dir.iterdir()} == {"codex.config.before", "claude.config.before", "hermes.config.before", "grok.config.before", "grok_compat.config.before"}

    after = {host: path.read_bytes() for host, path in configs.items()}
    second = installer.apply_install(**args, plan=first_plan)
    assert second["status"] == "APPLIED"
    assert second["replayed"] is True
    assert second["receipt_path"] == first["receipt_path"]
    assert {host: path.read_bytes() for host, path in configs.items()} == after
    assert [record.get("backup_path") for record in second["targets"]] == [record.get("backup_path") for record in first["targets"]]
    assert json.loads(configs["grok"].read_text(encoding="utf-8"))["keep"] == {"value": 3}


def test_interrupted_apply_restores_every_changed_target(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    before = {host: path.read_bytes() for host, path in configs.items()}
    with pytest.raises(installer.InstallerError) as raised:
        installer.apply_install(**args, plan=_plan(args, "interrupted"), fail_after_host="codex")
    assert raised.value.code == "HOLD_APPLY_INTERRUPTED"
    assert {host: path.read_bytes() for host, path in configs.items()} == before
    assert not (product / "integrated_system" / "runs" / "host-hook-installer" / "interrupted" / "receipt.json").exists()


def test_verify_and_rollback_refuse_external_tamper(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    plan = _plan(args, "tamper")
    receipt = installer.apply_install(**args, plan=plan)
    receipt_path = Path(product / "integrated_system" / "runs" / "host-hook-installer" / "tamper" / "receipt.json")
    verified = installer.verify_install(receipt_path=receipt_path, product_root=product, light_interpreter=interpreter, **_authority(plan, receipt))
    assert verified["status"] == "VERIFIED"
    configs["codex"].write_bytes(configs["codex"].read_bytes() + b"\n")
    with pytest.raises(installer.InstallerError) as raised:
        installer.rollback_install(receipt_path=receipt_path, **_authority(plan, receipt))
    assert raised.value.code == "HOLD_TARGET_TAMPERED"
    assert configs["codex"].read_bytes().endswith(b"\n\n")


def test_rollback_restores_missing_config_and_backup_hashes(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    configs["codex"].unlink()
    args = _args(product, interpreter, home, configs)
    plan = _plan(args, "rollback")
    receipt = installer.apply_install(**args, plan=plan)
    codex_record = next(row for row in receipt["targets"] if row["host"] == "codex")
    assert codex_record["existed_before"] is False
    assert codex_record["backup_sha256"] != installer.ABSENT_SHA256
    receipt_path = product / "integrated_system" / "runs" / "host-hook-installer" / "rollback" / "receipt.json"
    result = installer.rollback_install(receipt_path=receipt_path, **_authority(plan, receipt))
    assert result["status"] == "ROLLED_BACK"
    assert not configs["codex"].exists()


def test_source_drift_and_credential_targets_hold_before_read_or_write(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    planned = installer.plan_install(**args)
    source = product / "integrated_system" / "hooks" / "portable_host_hook.py"
    source.write_bytes(source.read_bytes() + b"\n# staged drift\n")
    held = installer.plan_install(**args, expected_source_sha256=planned["runtime_binding"]["hook_source_sha256"])
    assert held["status"] == "HOLD"
    assert held["reason_code"] == "HOLD_SOURCE_DRIFT"
    credential = home / ".hermes" / "credentials.json"
    credential.write_text('{"do_not_read": true}\n', encoding="utf-8")
    bad = dict(args)
    bad["config_paths"] = {"hermes": credential}
    bad["host_roots"] = {"hermes": home}
    bad.pop("grok_compat_config", None)
    result = installer.plan_install(**bad)
    assert result["status"] == "HOLD"
    assert result["reason_code"] == "HOLD_CREDENTIAL_PATH"


def test_installer_never_launches_provider_or_model_processes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("provider/model launch is outside installer scope")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    args = _args(product, interpreter, home, configs)
    result = installer.apply_install(**args, plan=_plan(args, "no-provider"))
    assert result["status"] == "APPLIED"


def test_apply_requires_a_sealed_plan_and_refuses_forged_or_stale_plan(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    with pytest.raises(installer.InstallerError) as missing:
        installer.apply_install(**args)
    assert missing.value.code == "HOLD_PLAN_REQUIRED"

    plan = _plan(args, "authority")
    forged = dict(plan)
    forged["status"] = "HOLD"
    with pytest.raises(installer.InstallerError) as forged_error:
        installer.apply_install(**args, plan=forged)
    assert forged_error.value.code == "HOLD_PLAN_NOT_APPLICABLE"
    assert not (product / "integrated_system" / "runs").exists()

    configs["codex"].write_bytes(configs["codex"].read_bytes() + b"\n")
    with pytest.raises(installer.InstallerError) as stale:
        installer.apply_install(**args, plan=plan)
    assert stale.value.code == "HOLD_PLAN_STALE"


def test_sealed_receipt_replay_does_not_overwrite_original_authority(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    plan = _plan(args, "sealed")
    first = installer.apply_install(**args, plan=plan)
    receipt_path = Path(first["receipt_path"])
    original = receipt_path.read_bytes()
    replay = installer.apply_install(**args, plan=plan)
    assert replay["replayed"] is True
    assert receipt_path.read_bytes() == original

    tampered = json.loads(original.decode("utf-8"))
    tampered["plan_sha256"] = "0" * 64
    receipt_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(installer.InstallerError) as refused:
        installer.rollback_install(receipt_path=receipt_path, **_authority(plan, first))
    assert refused.value.code == "HOLD_RECEIPT_SELF_DIGEST"


def test_config_and_hook_mode_tamper_is_detected_by_verify_and_rollback(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    configs["codex"].chmod(0o600)
    plan = _plan(args, "modes")
    receipt = installer.apply_install(**args, plan=plan)
    receipt_path = Path(receipt["receipt_path"])
    configs["codex"].chmod(0o644)
    result = installer.verify_install(receipt_path=receipt_path, product_root=product, light_interpreter=interpreter, **_authority(plan, receipt))
    assert result["status"] == "HOLD"
    assert any(row.get("reason_code") == "HOLD_CONFIG_MODE_TAMPERED" for row in result["targets"])
    with pytest.raises(installer.InstallerError) as rollback_error:
        installer.rollback_install(receipt_path=receipt_path, **_authority(plan, receipt))
    assert rollback_error.value.code == "HOLD_CONFIG_MODE_TAMPERED"

    configs["codex"].chmod(0o600)
    (product / "integrated_system" / "hooks" / "claude.sh").chmod(0o644)
    drift = installer.verify_install(receipt_path=receipt_path, product_root=product, light_interpreter=interpreter, **_authority(plan, receipt))
    assert drift["status"] == "HOLD"
    assert drift["reason_code"] in {"HOLD_RUNTIME_BINDING_DRIFT", "HOLD_HOOK_SCRIPT_NOT_EXECUTABLE"}


def test_receipt_write_failure_restores_configs_but_retains_backup_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    before = {host: path.read_bytes() for host, path in configs.items()}

    def fail_receipt(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise OSError("injected receipt failure")

    monkeypatch.setattr(installer, "_write_receipt", fail_receipt)
    with pytest.raises(installer.InstallerError) as raised:
        installer.apply_install(**args, plan=_plan(args, "receipt-failure"))
    assert raised.value.code == "HOLD_RECEIPT_WRITE_FAILED"
    assert {host: path.read_bytes() for host, path in configs.items()} == before
    backups = product / "integrated_system" / "runs" / "host-hook-installer" / "receipt-failure" / "backups"
    assert backups.is_dir()
    assert (backups / "codex.config.before").is_file()


def test_backup_custody_and_symlink_ancestor_attacks_hold(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    plan = _plan(args, "custody")
    receipt = installer.apply_install(**args, plan=plan)
    receipt_path = Path(receipt["receipt_path"])
    backup = Path(next(row["backup_path"] for row in receipt["targets"] if row["host"] == "codex"))
    backup_bytes = backup.read_bytes()
    backup.unlink()
    outside = tmp_path / "outside-backup"
    outside.write_bytes(backup_bytes)
    backup.symlink_to(outside)
    result = installer.verify_install(receipt_path=receipt_path, product_root=product, light_interpreter=interpreter, **_authority(plan, receipt))
    assert result["status"] == "HOLD"
    assert any(row.get("reason_code") == "HOLD_BACKUP_SYMLINK" for row in result["targets"])
    with pytest.raises(installer.InstallerError) as rollback_error:
        installer.rollback_install(receipt_path=receipt_path, **_authority(plan, receipt))
    assert rollback_error.value.code == "HOLD_BACKUP_SYMLINK"

    escaped_home = tmp_path / "escaped-home"
    escaped_home.mkdir()
    (home / ".claude").rename(home / ".claude-real")
    (home / ".claude").symlink_to(escaped_home, target_is_directory=True)
    held = installer.plan_install(**args)
    assert held["status"] == "HOLD"
    assert held["reason_code"] in {"HOLD_SYMLINK_ANCESTOR", "HOLD_TARGET_SYMLINK"}


def test_config_kind_duplicate_keys_yaml_errors_and_grok_compatibility_are_bounded(
    tmp_path: Path,
) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    configs["hermes"].with_suffix(".json").write_text("{}", encoding="utf-8")
    bad_kind = dict(args)
    bad_kind["config_paths"] = {"hermes": configs["hermes"].with_suffix(".json")}
    result = installer.plan_install(**bad_kind)
    assert result["status"] == "HOLD"
    assert result["reason_code"] == "HOLD_CONFIG_KIND_MISMATCH"

    configs["hermes"].write_text("hooks:\n  pre_tool_call: []\nhooks:\n  pre_tool_call: []\n", encoding="utf-8")
    duplicate_yaml = installer.plan_install(**args)
    assert duplicate_yaml["status"] == "HOLD"
    assert any(row.get("reason_code") == "HOLD_CONFIG_DUPLICATE_KEY" for row in duplicate_yaml["targets"])

    configs["hermes"].write_text("hooks: [\n", encoding="utf-8")
    parse_error = installer.plan_install(**args)
    assert parse_error["status"] == "HOLD"
    assert any(row.get("reason_code") == "HOLD_CONFIG_PARSE_FAILURE" for row in parse_error["targets"])

    # Put Claude and Grok entries in different events: a per-event first-
    # foreign check must not miss this direct+compatibility collision.
    product_root = str(product)
    command_claude = f"/usr/bin/env CB_PRODUCT_ROOT={product_root} {product_root}/integrated_system/hooks/claude.sh claude"
    command_grok = f"/usr/bin/env CB_PRODUCT_ROOT={product_root} {product_root}/integrated_system/hooks/grok.sh grok"
    configs["hermes"].write_text("hooks:\n  pre_tool_call: []\n", encoding="utf-8")
    configs["claude"].write_text(json.dumps({"hooks": {"SessionStart": [{"hooks": [{"command": command_claude}]}]}}), encoding="utf-8")
    configs["grok"].write_text(json.dumps({"hooks": {"PostToolUse": [{"hooks": [{"command": command_grok}]}]}}), encoding="utf-8")
    no_compat_args = dict(args)
    no_compat_args.pop("grok_compat_config", None)
    collision = installer.plan_install(**no_compat_args)
    assert collision["status"] == "HOLD"
    assert collision["reason_code"] == "HOLD_GROK_DOUBLE_EXECUTION"


def test_inline_empty_yaml_hooks_mapping_round_trips_and_rolls_back(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    configs["hermes"].write_text("hooks: {}\nkeep: true\n", encoding="utf-8")
    args = _args(product, interpreter, home, configs)
    plan = _plan(args, "inline-yaml")
    receipt = installer.apply_install(**args, plan=plan)
    assert "hooks: {}" not in configs["hermes"].read_text(encoding="utf-8")
    assert "keep: true" in configs["hermes"].read_text(encoding="utf-8")
    verified = installer.verify_install(
        receipt_path=receipt["receipt_path"],
        plan=plan,
        expected_plan_sha256=plan["plan_sha256"],
        expected_receipt_sha256=receipt["receipt_sha256"],
        product_root=product,
        light_interpreter=interpreter,
    )
    assert verified["status"] == "VERIFIED"
    rolled = installer.rollback_install(
        receipt_path=receipt["receipt_path"],
        plan=plan,
        expected_plan_sha256=plan["plan_sha256"],
        expected_receipt_sha256=receipt["receipt_sha256"],
        product_root=product,
        light_interpreter=interpreter,
    )
    assert rolled["status"] == "ROLLED_BACK"
    assert configs["hermes"].read_text(encoding="utf-8") == "hooks: {}\nkeep: true\n"


def test_grok_compat_replay_checks_toml_content_backup_and_mode(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    compat = home / ".grok" / "config.toml"
    args = _args(product, interpreter, home, configs)
    plan = _plan(args, "compat-replay")
    receipt = installer.apply_install(**args, plan=plan)
    compat.write_text("[compat.claude]\nhooks = true\n", encoding="utf-8")
    with pytest.raises(installer.InstallerError) as content_error:
        installer.apply_install(**args, plan=plan)
    assert content_error.value.code == "HOLD_REPLAY_TARGET_DRIFT"

    compat.write_text("[compat.claude]\nhooks = false\n", encoding="utf-8")
    compat.chmod(0o600)
    with pytest.raises(installer.InstallerError) as mode_error:
        installer.apply_install(**args, plan=plan)
    assert mode_error.value.code == "HOLD_REPLAY_TARGET_DRIFT"


def test_verify_and_rollback_require_caller_hashes_and_explicit_plan(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    plan = _plan(args, "expected-hashes")
    receipt = installer.apply_install(**args, plan=plan)
    with pytest.raises(installer.InstallerError) as missing:
        installer.verify_install(receipt_path=receipt["receipt_path"])
    assert missing.value.code == "HOLD_EXPECTED_RECEIPT_SHA256_REQUIRED"
    with pytest.raises(installer.InstallerError) as mismatch:
        installer.verify_install(
            receipt_path=receipt["receipt_path"],
            plan=plan,
            expected_plan_sha256="0" * 64,
            expected_receipt_sha256=receipt["receipt_sha256"],
        )
    assert mismatch.value.code == "HOLD_PLAN_EXPECTED_SHA256_MISMATCH"
    with pytest.raises(installer.InstallerError) as rollback_missing:
        installer.rollback_install(
            receipt_path=receipt["receipt_path"],
            plan=plan,
            expected_plan_sha256=plan["plan_sha256"],
        )
    assert rollback_missing.value.code == "HOLD_EXPECTED_RECEIPT_SHA256_REQUIRED"


def test_receipt_recomputed_with_malicious_paths_cannot_authorize_them(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    plan = _plan(args, "receipt-path-binding")
    receipt = installer.apply_install(**args, plan=plan)
    receipt_path = Path(receipt["receipt_path"])
    loaded = json.loads(receipt_path.read_text(encoding="utf-8"))
    target = next(row for row in loaded["targets"] if row["host"] == "codex")
    target["config_path"] = str(tmp_path / "outside.json")
    loaded["receipt_sha256"] = installer._self_digest(loaded, "receipt_sha256")
    receipt_path.write_text(json.dumps(loaded), encoding="utf-8")
    with pytest.raises(installer.InstallerError) as verify_error:
        installer.verify_install(
            receipt_path=receipt_path,
            plan=plan,
            expected_plan_sha256=plan["plan_sha256"],
            expected_receipt_sha256=loaded["receipt_sha256"],
            product_root=product,
            light_interpreter=interpreter,
        )
    assert verify_error.value.code == "HOLD_RECEIPT_TARGET_BINDING_MISMATCH"
    with pytest.raises(installer.InstallerError) as rollback_error:
        installer.rollback_install(
            receipt_path=receipt_path,
            plan=plan,
            expected_plan_sha256=plan["plan_sha256"],
            expected_receipt_sha256=loaded["receipt_sha256"],
            product_root=product,
            light_interpreter=interpreter,
        )
    assert rollback_error.value.code == "HOLD_RECEIPT_TARGET_BINDING_MISMATCH"


def test_plan_receipt_cross_run_pairing_is_refused(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    plan_a = _plan(args, "cross-a")
    plan_b = _plan(args, "cross-b")
    receipt_a = installer.apply_install(**args, plan=plan_a)
    with pytest.raises(installer.InstallerError) as refused:
        installer.verify_install(
            receipt_path=receipt_a["receipt_path"],
            plan=plan_b,
            expected_plan_sha256=plan_b["plan_sha256"],
            expected_receipt_sha256=receipt_a["receipt_sha256"],
            product_root=product,
            light_interpreter=interpreter,
        )
    assert refused.value.code == "HOLD_RECEIPT_PATH_MISMATCH"


def test_macos_var_private_var_aliases_bind_one_canonical_plan_and_receipt(tmp_path: Path) -> None:
    if not Path("/var").is_symlink() or not Path("/private/var").is_dir():
        pytest.skip("macOS /var alias unavailable")
    product, interpreter, home, configs = _fixture(tmp_path)
    if not str(product).startswith("/private/var/"):
        pytest.skip("fixture is not under /private/var")

    def alias(path: Path) -> Path:
        return Path(str(path).replace("/private/var", "/var", 1))

    alias_configs = {host: alias(path) for host, path in configs.items()}
    alias_args = {
        "product_root": alias(product),
        "light_interpreter": alias(interpreter),
        "host_roots": {host: alias(home) for host in configs},
        "config_paths": alias_configs,
        "grok_compat_config": alias(home / ".grok" / "config.toml"),
    }
    plan = _plan(alias_args, "var-alias")
    assert plan["product_root"] == str(product)
    assert all(row.get("config_path", "").startswith("/private/var/") for row in plan["targets"])
    receipt = installer.apply_install(**alias_args, plan=plan)
    verified = installer.verify_install(
        receipt_path=alias(Path(receipt["receipt_path"])),
        plan=plan,
        expected_plan_sha256=plan["plan_sha256"],
        expected_receipt_sha256=receipt["receipt_sha256"],
        product_root=alias(product),
        light_interpreter=alias(interpreter),
    )
    assert verified["status"] == "VERIFIED"


def test_direct_grok_requires_explicit_canonical_compatibility_target(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    args = _args(product, interpreter, home, configs)
    args.pop("grok_compat_config", None)
    held = installer.plan_install(**args, run_id="grok-missing-compat")
    assert held["status"] == "HOLD"
    assert held["reason_code"] == "HOLD_GROK_DOUBLE_EXECUTION"

    bad = dict(_args(product, interpreter, home, configs))
    bad["grok_compat_config"] = home / ".grok" / "other.toml"
    refused = installer.plan_install(**bad, run_id="grok-noncanonical")
    assert refused["status"] == "HOLD"
    assert refused["reason_code"] == "HOLD_GROK_COMPAT_CONFIG_NONCANONICAL"

    missing_legacy = installer.plan_install(
        **_args(product, interpreter, home, configs),
        run_id="missing-legacy-binding",
        force_migration=True,
    )
    assert missing_legacy["status"] == "HOLD"
    assert missing_legacy["reason_code"] == "HOLD_LEGACY_SOURCE_REQUIRED"


def test_force_migrates_only_recognized_legacy_universal_commands_and_preserves_foreign(
    tmp_path: Path,
) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    legacy_root = tmp_path / "Codex-Ratchet" / "constraint_box" / "hooks" / "universal"
    legacy_root.mkdir(parents=True)
    legacy = legacy_root / "cb_hook.sh"
    legacy.write_text("#!/bin/sh\n", encoding="utf-8")
    _shared_git_fixture(product, legacy, tmp_path)
    old = f'bash "{legacy}" codex'
    configs["codex"].write_text(
        json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": old}]}]}}),
        encoding="utf-8",
    )
    args = _args(product, interpreter, home, configs)
    no_force = installer.plan_install(**args, run_id="migration-no-force")
    assert no_force["status"] == "HOLD"
    assert any(row.get("reason_code") == "HOLD_MANAGED_ENTRY_MIGRATION_REQUIRED" for row in no_force["targets"])
    args.update(_legacy_source_args("codex", legacy))
    forced = installer.plan_install(**args, run_id="migration-force", force_migration=True)
    assert forced["status"] == "PLAN"
    assert forced["legacy_sources"]["codex"]["path"] == str(legacy)
    assert forced["legacy_sources"]["codex"]["sha256"] == installer._hash_file(legacy)
    receipt = installer.apply_install(**args, plan=forced)
    assert old not in configs["codex"].read_text(encoding="utf-8")
    assert receipt["force_migration"] is True

    foreign = tmp_path / "foreign" / "constraint_box" / "hooks" / "universal"
    foreign.mkdir(parents=True)
    foreign_cmd = f'bash "{foreign / "cb_hook.sh"}" codex'
    configs["codex"].write_text(
        json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": foreign_cmd}]}]}}),
        encoding="utf-8",
    )
    refused = installer.plan_install(**args, run_id="migration-foreign", force_migration=True)
    assert refused["status"] == "HOLD"
    assert any(row.get("reason_code") == "HOLD_MANAGED_ENTRY_MIGRATION_REQUIRED" for row in refused["targets"])
    assert foreign_cmd == json.loads(configs["codex"].read_text(encoding="utf-8"))["hooks"]["PreToolUse"][0]["hooks"][0]["command"]


def test_force_migrates_hermes_legacy_command_and_rejects_toml_duplicates_or_symlinks(
    tmp_path: Path,
) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    legacy = tmp_path / "Codex-Ratchet" / "constraint_box" / "hooks" / "universal" / "cb_hook.sh"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("#!/bin/sh\n", encoding="utf-8")
    _shared_git_fixture(product, legacy, tmp_path)
    configs["hermes"].write_text(
        f"hooks:\n  pre_tool_call:\n    - matcher: terminal|execute_code|delegate_task\n      command: bash\n        {legacy}\n        hermes\n      timeout: 30\n      fail_closed: true\n",
        encoding="utf-8",
    )
    args = _args(product, interpreter, home, configs)
    args.update(_legacy_source_args("hermes", legacy))
    forced = installer.plan_install(**args, run_id="hermes-migration", force_migration=True)
    assert forced["status"] == "PLAN"
    installer.apply_install(**args, plan=forced)
    assert str(product / "integrated_system" / "hooks" / "hermes.sh") in configs["hermes"].read_text(encoding="utf-8")

    compat = home / ".grok" / "config.toml"
    compat.write_text("[compat.claude]\nhooks = true\n[compat.claude]\nhooks = false\n", encoding="utf-8")
    bad = dict(args)
    bad["grok_compat_config"] = compat
    for key in ("legacy_hook_sources", "legacy_hook_source_hashes", "legacy_hook_source_modes"):
        bad.pop(key, None)
    duplicate = installer.plan_install(**bad, run_id="toml-duplicate")
    assert duplicate["status"] == "HOLD"
    assert duplicate["reason_code"] == "HOLD_CONFIG_PARSE_FAILURE"

    compat.unlink()
    outside = tmp_path / "outside-config.toml"
    outside.write_text("[compat.claude]\nhooks = true\n", encoding="utf-8")
    compat.symlink_to(outside)
    symlink = installer.plan_install(**bad, run_id="toml-symlink")
    assert symlink["status"] == "HOLD"
    assert symlink["reason_code"] in {"HOLD_CONFIG_SYMLINK", "HOLD_SYMLINK_ANCESTOR"}


@pytest.mark.parametrize("host", ["codex", "claude", "grok", "hermes"])
def test_all_hosts_require_exact_explicit_legacy_source_for_force_migration(
    tmp_path: Path, host: str
) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    source = tmp_path / "Codex-Ratchet" / "constraint_box" / "hooks" / "universal" / "cb_hook.sh"
    source.parent.mkdir(parents=True)
    source.write_text("#!/bin/sh\n", encoding="utf-8")
    _shared_git_fixture(product, source, tmp_path)
    old = f'bash "{source}" {host}'
    if host == "hermes":
        configs[host].write_text(
            f"hooks:\n  pre_tool_call:\n    - matcher: terminal\n      command: {old}\n",
            encoding="utf-8",
        )
    else:
        event = installer.HOST_SPECS[host].events[0]
        configs[host].write_text(
            json.dumps({"hooks": {event: [{"hooks": [{"type": "command", "command": old}]}]}}),
            encoding="utf-8",
        )
    args = _args(product, interpreter, home, configs)
    args.update(_legacy_source_args(host, source))
    forced = installer.plan_install(**args, run_id=f"migrate-{host}", force_migration=True)
    assert forced["status"] == "PLAN", forced
    receipt = installer.apply_install(**args, plan=forced)
    assert receipt["status"] == "APPLIED"

    lookalike = tmp_path / "Codex-Ratchet-fake" / "constraint_box" / "hooks" / "universal" / "cb_hook.sh"
    lookalike.parent.mkdir(parents=True)
    lookalike.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    bad_args = _args(product, interpreter, home, configs)
    bad_args.update(_legacy_source_args(host, lookalike))
    refused = installer.plan_install(**bad_args, run_id=f"lookalike-{host}", force_migration=True)
    assert refused["status"] == "HOLD"
    assert refused["reason_code"] == "HOLD_LEGACY_SOURCE_NONCANONICAL"

    symlink = tmp_path / "Codex-Ratchet" / "constraint_box" / "hooks" / "universal" / "symlink.sh"
    symlink.symlink_to(source)
    symlink_args = _args(product, interpreter, home, configs)
    symlink_args.update(_legacy_source_args(host, symlink))
    symlink_result = installer.plan_install(**symlink_args, run_id=f"symlink-{host}", force_migration=True)
    assert symlink_result["status"] == "HOLD"
    assert symlink_result["reason_code"] in {"HOLD_LEGACY_SOURCE_NONCANONICAL", "HOLD_LEGACY_SOURCE_SYMLINK"}

    foreign_root = tmp_path / "foreign-repo" / "Codex-Ratchet" / "constraint_box" / "hooks" / "universal"
    foreign_root.mkdir(parents=True)
    foreign_source = foreign_root / "cb_hook.sh"
    foreign_source.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    foreign_common = tmp_path / "foreign-common.git"
    (foreign_common / "main").mkdir(parents=True)
    (foreign_common / "config").write_text("[core]\nrepositoryformatversion = 0\n", encoding="utf-8")
    (foreign_common / "main" / "commondir").write_text("..\n", encoding="utf-8")
    (foreign_root.parent.parent.parent / ".git").write_text(
        f"gitdir: {foreign_common / 'main'}\n", encoding="utf-8"
    )
    foreign_args = _args(product, interpreter, home, configs)
    foreign_args.update(_legacy_source_args(host, foreign_source))
    foreign_result = installer.plan_install(
        **foreign_args, run_id=f"foreign-repo-{host}", force_migration=True
    )
    assert foreign_result["status"] == "HOLD"
    assert foreign_result["reason_code"] == "HOLD_LEGACY_REPOSITORY_MISMATCH"


def test_legacy_common_identity_drift_holds_apply_and_replay(tmp_path: Path) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    source = tmp_path / "Codex-Ratchet" / "constraint_box" / "hooks" / "universal" / "cb_hook.sh"
    source.parent.mkdir(parents=True)
    source.write_text("#!/bin/sh\n", encoding="utf-8")
    _shared_git_fixture(product, source, tmp_path)
    old = f'bash "{source}" codex'
    configs["codex"].write_text(json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"command": old}]}]}}), encoding="utf-8")
    args = _args(product, interpreter, home, configs)
    args.update(_legacy_source_args("codex", source))
    plan = installer.plan_install(**args, run_id="identity-drift", force_migration=True)
    foreign_common = tmp_path / "drift-common.git"
    (foreign_common / "main").mkdir(parents=True)
    (foreign_common / "config").write_text("[core]\nrepositoryformatversion = 0\n", encoding="utf-8")
    (foreign_common / "main" / "commondir").write_text("..\n", encoding="utf-8")
    (source.parents[3] / ".git").write_text(f"gitdir: {foreign_common / 'main'}\n", encoding="utf-8")
    with pytest.raises(installer.InstallerError) as apply_error:
        installer.apply_install(**args, plan=plan)
    assert apply_error.value.code == "HOLD_LEGACY_REPOSITORY_MISMATCH"


@pytest.mark.parametrize(
    "command,accepted",
    [
        ("{source} hermes", True),
        ("bash {source} hermes", True),
        ("/bin/bash {source} hermes", True),
        ("bash -c {source} hermes", False),
        ("bash {source} hermes extra", False),
        ("/bin/sh {source} hermes", False),
        ("bash {source} codex", False),
        ("bash {source}.bak hermes", False),
    ],
)
def test_hermes_legacy_command_grammar_accepts_current_shape_only(
    tmp_path: Path, command: str, accepted: bool
) -> None:
    product, interpreter, home, configs = _fixture(tmp_path)
    source = tmp_path / "Codex-Ratchet" / "constraint_box" / "hooks" / "universal" / "cb_hook.sh"
    source.parent.mkdir(parents=True)
    source.write_text("#!/bin/sh\n", encoding="utf-8")
    _shared_git_fixture(product, source, tmp_path)
    rendered = command.format(source=source)
    configs["hermes"].write_text(
        f"hooks:\n  pre_tool_call:\n    - matcher: terminal\n      command: {rendered}\n",
        encoding="utf-8",
    )
    args = _args(product, interpreter, home, configs)
    args.update(_legacy_source_args("hermes", source))
    result = installer.plan_install(**args, run_id="hermes-grammar", force_migration=True)
    if accepted:
        assert result["status"] == "PLAN"
    else:
        assert result["status"] == "HOLD"
        assert any(
            row.get("reason_code") == "HOLD_LEGACY_COMMAND_NOT_EXACT"
            for row in result["targets"]
        )
