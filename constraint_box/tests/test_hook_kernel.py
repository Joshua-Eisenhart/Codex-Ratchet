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


def make_root(tmp_path, *, declared=("alpha",), locked=("alpha",)):
    root = tmp_path / "hookkernel"
    root.mkdir(parents=True)
    for name in ("kernel.py", "receipts.py", "registry.json"):
        shutil.copy(ROOT / name, root / name)
    manifest = {"files": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in ("kernel.py", "receipts.py", "registry.json")}}
    (root / "manifest.json").write_text(canonical(manifest), encoding="utf-8")
    (root.parent / "config").mkdir(exist_ok=True)
    shutil.copy(Path(__file__).resolve().parents[1] / "config" / "cb_light_library_candidates.json", root.parent / "config" / "cb_light_library_candidates.json")
    # Lock coverage is RECOMPUTED from these files, never from a payload boolean
    # (a caller-supplied lock_covers_declared_set was a forgeable clear). Tests
    # therefore control the declared set and the lock, not the verdict.
    req = root.parent / "requirements" / "candidates"
    req.mkdir(parents=True, exist_ok=True)
    (req / "cb-light-extended.in").write_text("\n".join(declared) + "\n", encoding="utf-8")
    (req / "cb-candidates-passing.in").write_text("", encoding="utf-8")
    locks = root.parent / "requirements" / "locks"
    locks.mkdir(parents=True, exist_ok=True)
    (locks / "test.lock").write_text("\n".join(f"{n}==1.0.0" for n in locked) + "\n", encoding="utf-8")
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
    result = run(root, "dependency_file_changed", {})
    assert result.returncode == 0
    assert last(root)["payload"]["reason_code"] == "LOCK_VALID"
    assert verify_chain(root / "receipts.jsonl") == (True, None)


def test_wrong_interpreter_refuses_specific_reason(tmp_path):
    root = make_root(tmp_path)
    result = run(root, "pip_command_observed", {"command": "python -m pip install x"})
    assert result.returncode == 2
    assert last(root)["payload"]["reason_code"] == "ENV_INTERPRETER_MISMATCH"


def test_expired_fixture_is_currentness_negative(tmp_path):
    # Currentness is scoped to the ADOPTED estate, so the stale package must be
    # declared as adopted or it is correctly ignored as a mere candidate.
    root = make_root(tmp_path, declared=("tabulate",), locked=("tabulate",))
    # Currentness derives from the AUTHORITATIVE config, so control the config,
    # not a payload override. A payload override is correctly ignored when a
    # config exists — that binding closes the forged-fixture bypass and is
    # itself probed in test_hook_currentness_authority.py.
    config = root.parent / "config" / "cb_light_library_candidates.json"
    config.write_text(json.dumps({
        "stale_days_max": 548,
        "candidates": [{"pypi_name": "tabulate", "verified": {"release_date": "2024-12-01"}}],
    }), encoding="utf-8")
    result = run(root, "session_start", {"today": "2026-08-09"})
    assert result.returncode == 2
    body = last(root)["payload"]
    assert body["reason_code"] == "MAINTENANCE_REVIEW_REQUIRED"
    assert body["details"]["over_bar"][0]["age_days"] == 616
    assert body["details"]["resolve_with"] == "estate_metadata_refreshed"


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
    payload = {}
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


def test_real_registry_scoped_to_adopted_estate_is_current(tmp_path):
    """The real registry, scoped to what CB adopts, is current.

    This replaces an earlier test that asserted tabulate fires from the real
    registry. Two things changed, both deliberate: currentness is now scoped to
    the ADOPTED estate rather than all 139 candidates (35 of the 36 stale rows
    were packages CB never installs), and tabulate was DROPPED from the adopted
    set for being 616 days old against a 548-day bar while imported by zero CB
    source files. The bar was not moved; the failing package was removed.

    The negative for this constraint is pinned by
    test_expired_fixture_is_currentness_negative, which declares a stale package
    as adopted and shows it fire.
    """
    root = tmp_path / "hookkernel"
    root.mkdir(parents=True)
    for name in ("kernel.py", "receipts.py", "registry.json"):
        shutil.copy(ROOT / name, root / name)
    manifest = {"files": {n: hashlib.sha256((root / n).read_bytes()).hexdigest() for n in ("kernel.py", "receipts.py", "registry.json")}}
    (root / "manifest.json").write_text(canonical(manifest), encoding="utf-8")
    # real config AND real requirement files, so this exercises production data
    real = Path(__file__).resolve().parents[1]
    (root.parent / "config").mkdir(exist_ok=True)
    shutil.copy(real / "config" / "cb_light_library_candidates.json", root.parent / "config" / "cb_light_library_candidates.json")
    shutil.copytree(real / "requirements", root.parent / "requirements")

    result = run(root, "session_start", {"today": "2026-08-09"})
    body = last(root)["payload"]
    assert body["reason_code"] == "CURRENTNESS_LOCAL_OK", body
    assert result.returncode == 0
    assert body["details"]["checked"] > 50, body
