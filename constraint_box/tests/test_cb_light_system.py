from __future__ import annotations

import json
import hashlib
import pathlib
import subprocess
import sys


CB = pathlib.Path(__file__).resolve().parents[1]
ROOT = CB.parent


def read(relative: str) -> dict:
    return json.loads((CB / relative).read_text(encoding="utf-8"))


def test_contract_manifest_and_exclusions_are_exact() -> None:
    contract = read("config/cb_light_contract_v1.json")
    manifest = read("config/cb_light_tools_v1.json")
    names = {row["normalized_name"] for row in manifest["tools"]}
    excluded = {
        row["normalized_name"] for row in manifest["preinstall_excluded_candidates"]
    }
    assert manifest["membership_authority"] == "config/cb_light_contract_v1.json"
    assert names == set(contract["install_proposal_names"])
    assert excluded == set(contract["preinstall_excluded_names"])
    assert names.isdisjoint(excluded)
    expected = contract["expected_counts"]
    assert len(names) == expected["install_proposals"]
    assert len(excluded) == expected["preinstall_excluded"]
    assert manifest["counts"] == {
        "candidate_passing": expected["candidate_passing"],
        "core": expected["core"],
        "evaluated_candidate_domain": (
            expected["install_proposals"] + expected["preinstall_excluded"]
        ),
        "extended": expected["extended"],
        "preinstall_excluded": expected["preinstall_excluded"],
        "tools": expected["install_proposals"],
    }
    assert manifest["constraints"]["usable_now_requires"] == contract[
        "usable_now_requires"
    ]
    assert set(manifest["source_hashes"]) == set(contract["required_source_paths"])
    assert manifest["role_layers"] == {
        "controller_runtime_candidates": expected["core"],
        "supporting_probe_or_engineering_candidates": (
            expected["install_proposals"] - expected["core"]
        ),
        "rule": (
            "supporting build, test, audit, and probe tools do not become "
            "CB Light runtime identity merely by being installed or selected"
        ),
    }
    assert sum(
        row["runtime_identity_authority"] is True for row in manifest["tools"]
    ) == expected["core"]
    assert manifest["set_separation"]["sim_engine_members"] == 0
    assert manifest["runtime_environment"] == ".venv"
    assert (CB / manifest["mandated_interpreter"]).resolve() == (
        CB / ".venv/bin/python"
    ).resolve()


def test_required_source_set_covers_active_light_gate_spine() -> None:
    contract = read("config/cb_light_contract_v1.json")
    required = set(contract["required_source_paths"])
    # CB Light is packaged from the contained ``light_runtime`` project.  The
    # repository-root ``src/constraintbox`` tree is the mixed legacy estate
    # and must not substitute for these controller sources in the Light
    # source-set contract.
    active_spine = {
        "light_runtime/src/constraintbox/core_cli.py",
        "light_runtime/src/constraintbox/cb_light_probes.py",
        "light_runtime/src/constraintbox/cb_light_selection.py",
        "scripts/audit_cb_light_heavy_separation.py",
        "light_runtime/src/hookkernel/cb_light_domain.py",
        "light_runtime/src/hookkernel/cb_light_gate.py",
        "light_runtime/src/hookkernel/cb_light_runtime.py",
        "light_runtime/src/hookkernel/cb_light_state.py",
    }
    assert active_spine.issubset(required)
    assert not {
        "src/constraintbox/core_cli.py",
        "src/constraintbox/cb_light_probes.py",
        "src/constraintbox/cb_light_selection.py",
    }.intersection(required)


def test_contained_light_package_files_are_exactly_contract_bound() -> None:
    """A new importable Light module cannot evade the manifest source set."""

    contract = read("config/cb_light_contract_v1.json")
    declared = {
        path
        for path in contract["required_source_paths"]
        if path.startswith("light_runtime/src/")
    }
    observed: set[str] = set()
    for package in ("constraintbox", "hookkernel"):
        root = CB / "light_runtime" / "src" / package
        for path in root.rglob("*"):
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix not in {".pyc", ".pyo"}
            ):
                observed.add(path.relative_to(CB).as_posix())
    assert declared == observed


def test_runtime_and_clean_install_evidence_are_distinct_and_exact() -> None:
    expected_roots = read("config/cb_light_contract_v1.json")["expected_counts"][
        "install_proposals"
    ]
    runtime = read("receipts/cb_light_install_runtime_v1.json")
    clean = read("receipts/cb_light_install_clean_v1.json")
    runtime_prefix = pathlib.Path(runtime["environment"]["prefix"]).resolve()
    clean_prefix = pathlib.Path(clean["environment"]["prefix"]).resolve()
    assert runtime["environment_role"] == "runtime"
    assert clean["environment_role"] == "clean"
    assert runtime_prefix == (CB / ".venv").resolve()
    assert clean_prefix != runtime_prefix
    assert runtime_prefix.is_dir()
    # The clean environment is deliberately separate but persists so a later
    # verifier can still inspect the exact prefix named by the receipt.
    assert clean_prefix == (CB / ".venv-clean").resolve()
    assert clean_prefix.is_dir()
    assert runtime["install_report"]["path"] != clean["install_report"]["path"]
    for receipt, prefix in ((runtime, runtime_prefix), (clean, clean_prefix)):
        assert receipt["all_root_constraints_satisfied"] is True
        assert receipt["all_install_constraints_satisfied"] is True
        assert receipt["environment"]["environment_exact"] is True
        assert receipt["counts"]["distribution_present"] == expected_roots
        assert receipt["counts"]["version_matches"] == expected_roots
        assert receipt["counts"]["import_passed"] == expected_roots
        assert receipt["counts"]["provider_bound"] == expected_roots
        assert receipt["counts"]["closure_missing"] == 0
        assert receipt["counts"]["closure_requirement_violations"] == 0
        assert receipt["install_report"]["install_records"] >= expected_roots
        snapshot = receipt["site_packages_snapshot"]
        assert snapshot["file_count"] > 0
        assert snapshot["total_bytes"] > 0
        assert len(snapshot["digest"]) == 64
        assert "**/__editable__.constraintbox-*.pth" in snapshot["excluded"]
        assert "**/constraintbox-*.dist-info/**" in snapshot["excluded"]
        for row in receipt["rows"]:
            probe = row["import_probe"]
            assert probe["passed"] is True
            assert probe["origin_under_probe_prefix"] is True
            assert pathlib.Path(probe["observation"]["prefix"]).resolve() == prefix
            assert pathlib.Path(probe["observation"]["file"]).resolve().is_relative_to(
                prefix
            )
            assert row["root_install_constraints_satisfied"] is True
    runtime_versions = {
        row["distribution"]: row["version"] for row in runtime["closure"]
    }
    clean_versions = {row["distribution"]: row["version"] for row in clean["closure"]}
    assert runtime_versions == clean_versions


def test_operation_selection_and_three_solver_backends_are_rederived() -> None:
    operation = read("receipts/cb_light_tool_probes_v1.json")
    selection = read("receipts/cb_light_selection_v1.json")
    expected = read("config/cb_light_contract_v1.json")["expected_counts"]
    proposal_count = expected["install_proposals"]
    assert operation["counts"]["probed"] == proposal_count
    assert operation["counts"]["admit"] + operation["counts"]["hold"] == proposal_count
    decision = selection["finite_selection_decision"]
    assert decision["domain_size"] == proposal_count
    assert decision["agree"] is True
    assert decision["unique_assignment"] is True
    assert set(decision["deciders"]) == {"z3", "cvc5", "enumeration"}
    assert not decision["execution_errors"]
    assert "not independent fact validation" in selection[
        "finite_selection_interpretation"
    ]
    assert selection["evaluation_complete"] is True
    assert selection["runtime_ready"] is True
    assert selection["evaluation_allowed"] is True
    assert selection["completion_allowed"] is False
    assert selection["system_completion_reason"] == "SELECTION_IS_LOCAL_CB_LIGHT_EVALUATION_ONLY"
    assert selection["promotion_allowed"] is False
    counts = selection["counts"]
    assert counts["evaluated_candidate_domain"] == (
        proposal_count + expected["preinstall_excluded"]
    )
    assert counts["preinstall_excluded"] == expected["preinstall_excluded"]
    assert (
        counts["selected_for_work"]
        + counts["hold_missing_evidence"]
        + counts["hold_decider_disagreement"]
        == proposal_count
    )
    assert counts["hold_decider_disagreement"] == 0
    for row in selection["rows"]:
        expected = all(row["usable_now_facts"].values())
        assert decision["assignment"][row["normalized_name"]] is expected
        assert set(row["decider_votes"].values()) == {expected}
        assert row["adopted"] is False
        assert row["portable_adoption_disposition"] == "HOLD_NOT_ADOPTED"
        if expected:
            assert row["work_disposition"] == "SELECTED_FOR_WORK"
            assert not row["failed_usable_now_constraints"]
        else:
            assert row["work_disposition"] == "HOLD_MISSING_EVIDENCE"
            assert row["failed_usable_now_constraints"]


def test_hook_wiring_covers_install_and_completion_transitions() -> None:
    settings = json.loads((ROOT / ".claude/settings.json").read_text(encoding="utf-8"))
    hooks = settings["hooks"]
    expected = {
        "SessionStart": ".claude/hooks/session-start.sh",
        "PreToolUse": ".claude/hooks/cb_pretooluse_guard.sh",
        "PostToolUse": ".claude/hooks/cb_posttooluse_record.sh",
        "PostToolUseFailure": "constraint_box/hooks/post_tool_failure.sh",
        "PostToolBatch": "constraint_box/hooks/post_tool_batch.sh",
        "TaskCompleted": "constraint_box/hooks/task_completed.sh",
        "SubagentStop": "constraint_box/hooks/subagent_stop.sh",
        "Stop": "constraint_box/hooks/stop.sh",
        "ConfigChange": "constraint_box/hooks/config_change.sh",
        "FileChanged": "constraint_box/hooks/file_changed.sh",
    }
    for event, suffix in expected.items():
        commands = [
            hook["command"]
            for group in hooks[event]
            for hook in group.get("hooks", [])
            if hook.get("type") == "command"
        ]
        assert any(suffix in command for command in commands)
    assert hooks["ConfigChange"][0]["matcher"] == (
        "user_settings|project_settings|local_settings|policy_settings|skills"
    )
    assert hooks["PreToolUse"][0]["matcher"] == "Bash|Edit|Write|NotebookEdit"
    assert hooks["PostToolUse"][0]["matcher"] == "Bash|Edit|Write|NotebookEdit"
    adapter_targets = {
        "session_start.sh": ".claude/hooks/session-start.sh",
        "pre_tool.sh": ".claude/hooks/cb_pretooluse_guard.sh",
        "post_tool.sh": ".claude/hooks/cb_posttooluse_record.sh",
    }
    for wrapper, target in adapter_targets.items():
        text = (CB / "hooks" / wrapper).read_text(encoding="utf-8")
        assert 'exec bash "$repo/' in text
        assert target in text
        assert "cb_light_hook.py" not in text
    for wrapper in (
        "post_tool_failure.sh",
        "post_tool_batch.sh",
        "task_completed.sh",
        "subagent_stop.sh",
        "stop.sh",
        "config_change.sh",
        "file_changed.sh",
    ):
        text = (CB / "hooks" / wrapper).read_text(encoding="utf-8")
        assert '"$interpreter" -I ' in text
        assert ".venv/bin/python" in text
        assert "exit 2" in text


def test_command_guard_blocks_direct_mutation_without_blocking_normal_compounds() -> None:
    sys.path.insert(0, str(CB))
    from hooks.cb_light_command_guard import classify_command, git_transition

    broker = CB / "bin/cb-light"
    cwd = ROOT
    denied = [
        "python3 -m pip install requests",
        "python3 -mpip install requests",
        "sh -c '$CMD pip install requests'",
        f"cp module.py {CB / '.venv/lib/python3.13/site-packages/'}",
        "python3 -m ensurepip --upgrade",
    ]
    for command in denied:
        assert classify_command(command, cwd=cwd, broker=broker)["disposition"] == "DENY"
    assert classify_command("ls && echo ok", cwd=cwd, broker=broker)[
        "disposition"
    ] == "ADMIT"
    assert classify_command("grep pip README.md", cwd=cwd, broker=broker)[
        "disposition"
    ] == "ADMIT"
    assert classify_command("echo uv", cwd=cwd, broker=broker)[
        "disposition"
    ] == "ADMIT"
    admitted_broker = classify_command(str(broker) + " install", cwd=cwd, broker=broker)
    assert admitted_broker["disposition"] == "ADMIT"
    assert admitted_broker["broker"] is True
    compound_broker = classify_command(
        f"cd {ROOT} && {broker} status && echo checked", cwd=cwd, broker=broker
    )
    assert compound_broker["disposition"] == "ADMIT"
    assert compound_broker["broker"] is True
    assert git_transition("git -C /tmp commit -m test") == "commit"
    assert git_transition("bash -c 'git commit -m test'") == "commit"


def test_file_tool_guard_blocks_authority_and_runtime_writes() -> None:
    sys.path.insert(0, str(CB))
    from hooks.cb_light_hook import HookRefusal, evaluate_file_write

    for target in (
        CB / "hooks/hashlib.py",
        CB / ".venv/lib/python3.13/site-packages/shadow.py",
        CB / "receipts/forged.json",
        ROOT / ".claude/settings.json",
    ):
        payload = {
            "tool_name": "Write",
            "cwd": str(ROOT),
            "tool_input": {"file_path": str(target)},
        }
        try:
            evaluate_file_write(payload)
        except HookRefusal as exc:
            assert exc.reason_code == "PROTECTED_CB_LIGHT_WRITE_REFUSED"
        else:
            raise AssertionError(f"protected write admitted: {target}")
    admitted = evaluate_file_write(
        {
            "tool_name": "Edit",
            "cwd": str(ROOT),
            "tool_input": {"file_path": str(CB / "docs/example.md")},
        }
    )
    assert admitted["disposition"] == "ADMIT"


def test_contained_light_slice_has_no_external_runtime_authority() -> None:
    manifest = read("config/cb_light_tools_v1.json")
    forbidden_path_parts = (
        "/Archive/",
        "/Desktop/Constraint Box/",
        "/Desktop/Leviathan/",
        "/sim_engines/",
        "/system_v5/",
    )
    for relative in manifest["source_hashes"]:
        assert not any(part in relative for part in forbidden_path_parts)
    runtime_files = [
        CB / "scripts/cb_light_cli.py",
        CB / "scripts/cb_light_install_probe.py",
        CB / "scripts/cb_light_metadata_probe.py",
        CB / "scripts/cb_light_select.py",
        CB / "scripts/audit_cb_light_heavy_separation.py",
        CB / "hooks/cb_light_hook.py",
        CB / "hooks/cb_light_command_guard.py",
        CB / "light_runtime/src/hookkernel/cb_light_solver.py",
    ]
    forbidden_imports = (
        "import Archive",
        "from Archive",
        "import sim_engines",
        "from sim_engines",
        "import system_v5",
        "from system_v5",
    )
    for path in runtime_files:
        text = path.read_text(encoding="utf-8")
        assert not any(token in text for token in forbidden_imports)


def test_status_rechecks_live_runtime_inventory() -> None:
    completed = subprocess.run(
        [str(CB / "bin/cb-light"), "status"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout
    body = json.loads(completed.stdout)
    assert body["evaluation_allowed"] is True
    assert body["completion_allowed"] is False
    assert body["reason_code"].startswith("CB_LIGHT_EVALUATION_VERIFIED:")
    assert body["system_completion_reason"] == (
        "LOCAL_CB_LIGHT_EVALUATION_DOES_NOT_EARN_SYSTEM_COMPLETION"
    )


def test_complete_remains_fail_closed_after_a_current_light_evaluation() -> None:
    completed = subprocess.run(
        [str(CB / "bin/cb-light"), "complete"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 2
    body = json.loads(completed.stdout)
    assert body["evaluation_allowed"] is True
    assert body["completion_allowed"] is False
    assert body["reason_code"].startswith("SYSTEM_COMPLETION_NOT_EARNED:")


def test_selector_live_inventory_ignores_checkout_style_metadata(
    tmp_path: pathlib.Path,
) -> None:
    """A source-tree dist-info directory must not look installed in the venv."""
    code = """
import importlib.util
import pathlib
import sys

script = pathlib.Path(sys.argv[1])
fake_root = pathlib.Path(sys.argv[2])
fake = fake_root / "source_leak-1.0.0.dist-info"
fake.mkdir()
(fake / "METADATA").write_text(
    "Metadata-Version: 2.1\\nName: source-leak\\nVersion: 1.0\\n",
    encoding="utf-8",
)
spec = importlib.util.spec_from_file_location("cb_light_select_probe", script)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
sys.path.insert(0, str(fake_root))
observed, _ = module.live_runtime_inventory(pathlib.Path(sys.prefix).resolve())
raise SystemExit("source-leak" in observed)
"""
    completed = subprocess.run(
        [
            str(CB / ".venv/bin/python"),
            "-I",
            "-c",
            code,
            str(CB / "scripts/cb_light_select.py"),
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr + completed.stdout


def test_runtime_postcondition_rejects_file_snapshot_drift(monkeypatch) -> None:
    sys.path.insert(0, str(CB))
    from hooks import cb_light_hook

    runtime = read("receipts/cb_light_install_runtime_v1.json")
    expected_inventory = {
        row["distribution"]: row["version"]
        for row in runtime["closure"]
        if row["installed"] is True
    }
    monkeypatch.setattr(
        cb_light_hook,
        "runtime_inventory",
        lambda: {
            **expected_inventory,
            "pip": "test-bootstrap",
            "constraintbox": "test-controller",
        },
    )
    changed = dict(runtime["site_packages_snapshot"])
    changed["digest"] = "0" * 64
    monkeypatch.setattr(
        cb_light_hook, "runtime_site_packages_snapshot", lambda _receipt: changed
    )
    allowed, reason = cb_light_hook.verify_runtime_postcondition(runtime)
    assert allowed is False
    assert reason.startswith("RUNTIME_SITE_PACKAGES_FILE_DRIFT:")


def test_runtime_postcondition_rejects_missing_controller_package(monkeypatch) -> None:
    sys.path.insert(0, str(CB))
    from hooks import cb_light_hook

    runtime = read("receipts/cb_light_install_runtime_v1.json")
    expected_inventory = {
        row["distribution"]: row["version"]
        for row in runtime["closure"]
        if row["installed"] is True
    }
    monkeypatch.setattr(
        cb_light_hook,
        "runtime_inventory",
        lambda: {**expected_inventory, "pip": "test-bootstrap"},
    )
    monkeypatch.setattr(
        cb_light_hook,
        "runtime_site_packages_snapshot",
        lambda _receipt: runtime["site_packages_snapshot"],
    )
    allowed, reason = cb_light_hook.verify_runtime_postcondition(runtime)
    assert allowed is False
    assert reason == "CONTAINED_CONTROLLER_PACKAGE_MISSING"


def test_selector_refuses_tampered_install_aggregate(tmp_path: pathlib.Path) -> None:
    runtime = read("receipts/cb_light_install_runtime_v1.json")
    runtime["counts"]["distribution_present"] = 90
    tampered_runtime = tmp_path / "tampered-runtime.json"
    tampered_runtime.write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    completed = subprocess.run(
        [
            str(CB / ".venv/bin/python"),
            str(CB / "scripts/cb_light_select.py"),
            "--manifest",
            str(CB / "config/cb_light_tools_v1.json"),
            "--runtime-install",
            str(tampered_runtime),
            "--clean-install",
            str(CB / "receipts/cb_light_install_clean_v1.json"),
            "--operation",
            str(CB / "receipts/cb_light_tool_probes_v1.json"),
            "--metadata",
            str(CB / "receipts/cb_light_metadata_v1.json"),
            "--output",
            str(tmp_path / "selection.json"),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    assert completed.returncode != 0
    assert "runtime install aggregate mismatch" in completed.stderr


def test_selector_refuses_an_incomplete_dependency_failure_mutation(
    tmp_path: pathlib.Path,
) -> None:
    runtime = read("receipts/cb_light_install_runtime_v1.json")
    target = "annotated-types"
    row = next(item for item in runtime["rows"] if item["normalized_name"] == target)
    row.update(
        {
            "installed": False,
            "installed_version": None,
            "version_matches": False,
            "import_providers": [],
            "expected_provider_present": False,
            "installed_bytes": 0,
            "requires_dist": [],
            "root_dependency_closure": [target],
            "root_dependency_missing": [target],
            "root_dependency_requirement_issues": [],
            "root_install_constraints_satisfied": False,
        }
    )
    row["import_probe"].update(
        {
            "passed": False,
            "returncode": 1,
            "observation": None,
            "prefix_matches_probe_process": False,
            "origin_under_probe_prefix": False,
        }
    )
    closure_row = next(
        item for item in runtime["closure"] if item["distribution"] == target
    )
    closure_row.update(
        {"installed": False, "version": None, "installed_bytes": 0, "requires_dist": []}
    )
    runtime["counts"]["distribution_present"] -= 1
    runtime["counts"]["version_matches"] -= 1
    runtime["counts"]["import_passed"] -= 1
    runtime["counts"]["provider_bound"] -= 1
    runtime["counts"]["closure_missing"] = 1
    runtime["all_root_constraints_satisfied"] = False
    runtime["all_install_constraints_satisfied"] = False
    runtime["disposition"] = "HOLD"
    runtime["reason_code"] = "INSTALL_CONSTRAINTS_INCOMPLETE"
    inventory = {
        item["distribution"]: item["version"]
        for item in runtime["closure"]
        if item["installed"] is True
    }
    canonical = json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()
    runtime["runtime_inventory_sha256"] = hashlib.sha256(canonical).hexdigest()
    held_runtime = tmp_path / "held-runtime.json"
    held_runtime.write_text(
        json.dumps(runtime, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output = tmp_path / "held-selection.json"
    completed = subprocess.run(
        [
            str(CB / ".venv/bin/python"),
            str(CB / "scripts/cb_light_select.py"),
            "--runtime-install",
            str(held_runtime),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode != 0
    assert "dependency check self-report mismatch" in completed.stderr
    assert not output.exists()


def test_recursive_stop_hook_returns_without_livelock() -> None:
    completed = subprocess.run(
        [str(CB / "hooks/stop.sh")],
        input=json.dumps(
            {
                "session_id": "test",
                "hook_event_name": "Stop",
                "stop_hook_active": True,
            }
        ),
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert "without a recursive block" in completed.stderr


def test_completion_refuses_tampered_selection_without_touching_authority(
    tmp_path: pathlib.Path, monkeypatch,
) -> None:
    sys.path.insert(0, str(CB))
    from hooks import cb_light_hook

    selection = read("receipts/cb_light_selection_v1.json")
    selection["counts"]["selected_for_work"] += 1
    tampered = tmp_path / "tampered-selection.json"
    tampered.write_text(
        json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    monkeypatch.setattr(cb_light_hook, "SELECTION_RECEIPT", tampered)
    allowed, reason = cb_light_hook.verify_completion()
    assert allowed is False
    assert reason == "SELECTION_RECEIPT_TAMPERED"
