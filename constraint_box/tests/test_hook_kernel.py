import ast
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from constraint_box.hookkernel import kernel
from constraint_box.hookkernel.receipts import canonical, verify_chain


ROOT = Path(__file__).resolve().parents[1] / "hookkernel"
PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"


def make_root(tmp_path):
    root = tmp_path / "hookkernel"
    root.mkdir(parents=True)
    for name in ("kernel.py", "receipts.py", "registry.json"):
        shutil.copy(ROOT / name, root / name)
    manifest = {"files": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ("kernel.py", "receipts.py", "registry.json")}}
    (root / "manifest.json").write_text(canonical(manifest), encoding="utf-8")
    (root.parent / "config").mkdir(exist_ok=True)
    shutil.copy(Path(__file__).resolve().parents[1] / "config" / "cb_light_library_candidates.json", root.parent / "config" / "cb_light_library_candidates.json")
    return root


def run(root, event, payload=None):
    env = dict(os.environ, CB_HOOKKERNEL_ROOT=str(root), PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    args = [PYTHON, "-m", "constraint_box.hookkernel.kernel", event]
    if payload is not None:
        args += ["--payload-json", payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)]
    return subprocess.run(args, cwd=Path(__file__).resolve().parents[2], env=env, text=True, capture_output=True)


def last(root):
    return json.loads((root / "receipts.jsonl").read_text().splitlines()[-1])


def test_valid_event_admits_and_chain_verifies(tmp_path):
    root = make_root(tmp_path)
    result = run(root, "dependency_file_changed", {"lock_covers_declared_set": True})
    assert result.returncode == 0
    assert last(root)["payload"]["reason_code"] == "LOCK_VALID"
    assert verify_chain(root / "receipts.jsonl") == (True, None)


def test_wrong_interpreter_refuses_specific_reason(tmp_path):
    root = make_root(tmp_path)
    result = run(root, "pip_command_observed", {"command": "python -m pip install x"})
    assert result.returncode == 2
    assert last(root)["payload"]["reason_code"] == "ENV_INTERPRETER_MISMATCH"


def test_expired_fixture_is_currentness_negative(tmp_path):
    root = make_root(tmp_path)
    result = run(root, "session_start", {"today": "2026-08-09", "stale_days_max": 548, "estate_rows": [{"id": "tabulate", "date": "2024-12-01"}]})
    assert result.returncode == 2
    body = last(root)["payload"]
    assert body["reason_code"] == "CURRENTNESS_EXPIRED"
    assert body["details"]["stale"][0]["age_days"] == 616


def test_completion_refuses_open_hold(tmp_path):
    root = make_root(tmp_path)
    assert run(root, "cb_source_changed", {"modules": ["constraintbox.constraints"]}).returncode == 2
    result = run(root, "task_completion_claimed", {})
    assert result.returncode == 2
    assert last(root)["payload"]["reason_code"] == "COMPLETION_UNEARNED"


def test_kernel_byte_flip_is_detected(tmp_path):
    root = make_root(tmp_path)
    path = root / "kernel.py"
    path.write_bytes(path.read_bytes() + b"\n# byte flip\n")
    result = run(root, "dependency_file_changed", {"lock_covers_declared_set": True})
    assert result.returncode == 2
    assert last(root)["payload"]["reason_code"] == "KERNEL_TAMPERED"


def test_malformed_payload_is_hold_not_traceback(tmp_path):
    root = make_root(tmp_path)
    result = run(root, "session_start", "{")
    assert result.returncode == 2
    assert last(root)["payload"]["reason_code"] == "HOOK_RESULT_INVALID"
    assert "Traceback" not in result.stdout


def test_missing_registry_is_unavailable(tmp_path):
    root = make_root(tmp_path)
    (root / "registry.json").unlink()
    result = run(root, "dependency_file_changed", {"lock_covers_declared_set": True})
    assert result.returncode == 2
    assert last(root)["payload"]["reason_code"] == "HOOK_UNAVAILABLE"


def test_replay_payload_is_byte_identical_in_fresh_stores(tmp_path):
    first = make_root(tmp_path / "one")
    second = make_root(tmp_path / "two")
    payload = {"lock_covers_declared_set": True}
    assert run(first, "dependency_file_changed", payload).returncode == 0
    assert run(second, "dependency_file_changed", payload).returncode == 0
    a = last(first)["payload"]
    b = last(second)["payload"]
    assert canonical(a) == canonical(b)
    assert hashlib.sha256(canonical(a).encode()).hexdigest() == hashlib.sha256(canonical(b).encode()).hexdigest()


def test_tampered_middle_receipt_names_sequence(tmp_path):
    root = make_root(tmp_path)
    for event, payload in [("dependency_file_changed", {"lock_covers_declared_set": True}), ("post_tool_use_observed", {"command": "echo x"}), ("dependency_file_changed", {"lock_covers_declared_set": True})]:
        run(root, event, payload)
    lines = (root / "receipts.jsonl").read_text().splitlines()
    middle = json.loads(lines[1])
    middle["payload"]["details"] = {"tampered": True}
    lines[1] = canonical(middle)
    (root / "receipts.jsonl").write_text("\n".join(lines) + "\n")
    assert verify_chain(root / "receipts.jsonl") == (False, "hash mismatch at seq 2")


def test_kernel_ast_imports_stdlib_only():
    allowed = set(__import__("sys").stdlib_module_names) | {"receipts"}
    tree = ast.parse((ROOT / "kernel.py").read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module.split(".")[0])
    assert set(imports) <= allowed


def test_real_registry_has_tabulate_negative(tmp_path):
    root = make_root(tmp_path)
    result = run(root, "session_start", {"today": "2026-08-09"})
    assert result.returncode == 2
    body = last(root)["payload"]
    assert body["reason_code"] == "CURRENTNESS_EXPIRED"
    assert any(row["id"] == "tabulate" and row["age_days"] == 616 for row in body["details"]["stale"])
