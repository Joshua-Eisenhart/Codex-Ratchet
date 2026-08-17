from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "mmm_preload.py"


def build_root(root: Path) -> None:
    (root / "mini/full/voices/md").mkdir(parents=True)
    (root / "mini/compact/voices/md").mkdir(parents=True)
    (root / "FULL_MMM_v4_3.md").write_text("main full\n", encoding="utf-8")
    (root / "COMPACT_MMM_v4_3.md").write_text("main compact\n", encoding="utf-8")
    for voice in ("FACTORY", "FEYNMAN", "HUME", "ORWELL", "POPPER", "PUSHBACK", "STRATEGY", "SYSTEMS", "ZHUANGZI"):
        for variant in ("full", "compact"):
            p = root / "mini" / variant / "voices" / "md" / f"MMM_VOICE_{voice}_{variant.upper()}_v4_1.md"
            p.write_text(f"{voice} {variant}\n", encoding="utf-8")


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True, check=False)


def test_prepare_and_verify_bind_complete_bytes(tmp_path: Path) -> None:
    root = tmp_path / "mmm"
    build_root(root)
    task = tmp_path / "task.md"
    task.write_text("test the gate\n", encoding="utf-8")
    out = tmp_path / "out"
    prepared = run("prepare", "--task-file", str(task), "--output-dir", str(out), "--run-id", "r1", "--agent-id", "a1", "--seed", "42", "--voice-count", "3", "--mmm-root", str(root))
    assert prepared.returncode == 0, prepared.stderr + prepared.stdout
    receipt = json.loads((out / "preload_receipt.json").read_text())
    assert receipt["disposition"] == "CONTENT_BOUND"
    assert receipt["provider_dispatch_proved"] is False
    assert len(receipt["sources"]) == 3
    assert all(str(row["primary_id"]).startswith("voice:") for row in receipt["sources"])
    assert all(row["included_bytes"] == row["source_bytes"] for row in receipt["sources"])
    verified = run("verify-content", "--receipt", str(out / "preload_receipt.json"), "--mmm-root", str(root))
    assert verified.returncode == 0
    assert json.loads(verified.stdout)["disposition"] == "MMM_CONTENT_VERIFIED"


def test_budget_refuses_without_silent_variant_substitution(tmp_path: Path) -> None:
    root = tmp_path / "mmm"
    build_root(root)
    task = tmp_path / "task.md"
    task.write_text("x", encoding="utf-8")
    result = run("prepare", "--task-file", str(task), "--output-dir", str(tmp_path / "out"), "--run-id", "r", "--agent-id", "a", "--seed", "1", "--voice-count", "2", "--voice-variant", "full", "--max-bytes", "10", "--mmm-root", str(root))
    assert result.returncode == 2
    data = json.loads(result.stdout)
    assert data["disposition"] == "REFUSE_MMM_BUDGET_EXCEEDED"
    assert not (tmp_path / "out/preload_receipt.json").exists()


def test_zero_voice_preload_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "mmm"
    build_root(root)
    task = tmp_path / "task.md"
    task.write_text("x", encoding="utf-8")
    result = run("prepare", "--task-file", str(task), "--output-dir", str(tmp_path / "out"), "--run-id", "r", "--agent-id", "a", "--seed", "1", "--voice-count", "0", "--mmm-root", str(root))
    assert result.returncode == 2
    assert json.loads(result.stdout)["disposition"] == "REFUSE_MMM_PRELOAD_ERROR"


def test_source_drift_is_refused(tmp_path: Path) -> None:
    root = tmp_path / "mmm"
    build_root(root)
    task = tmp_path / "task.md"
    task.write_text("x", encoding="utf-8")
    out = tmp_path / "out"
    assert run("prepare", "--task-file", str(task), "--output-dir", str(out), "--run-id", "r", "--agent-id", "a", "--seed", "9", "--voice-count", "2", "--mmm-root", str(root)).returncode == 0
    receipt = json.loads((out / "preload_receipt.json").read_text())
    Path(receipt["sources"][0]["path"]).write_text("changed\n", encoding="utf-8")
    checked = run("verify-content", "--receipt", str(out / "preload_receipt.json"), "--mmm-root", str(root))
    assert checked.returncode == 2
    assert json.loads(checked.stdout)["disposition"] == "REFUSE_MMM_SOURCE_DRIFT"


def test_round_rejects_duplicate_resolved_sets(tmp_path: Path) -> None:
    root = tmp_path / "mmm"
    build_root(root)
    task = tmp_path / "task.md"
    task.write_text("x", encoding="utf-8")
    receipts = []
    for name in ("a", "b"):
        out = tmp_path / name
        assert run("prepare", "--task-file", str(task), "--output-dir", str(out), "--run-id", "r", "--agent-id", name, "--seed", "55", "--voice-count", "2", "--mmm-root", str(root)).returncode == 0
        receipts.append(str(out / "preload_receipt.json"))
    checked = run("verify-round", "--receipts", *receipts, "--mmm-root", str(root))
    assert checked.returncode == 2
    assert "duplicate_resolved_mmm_sets" in json.loads(checked.stdout)["errors"]


def test_call_verification_binds_expected_child_identity(tmp_path: Path) -> None:
    root = tmp_path / "mmm"
    build_root(root)
    task = tmp_path / "task.md"
    task.write_text("x", encoding="utf-8")
    out = tmp_path / "out"
    prepared = run("prepare", "--task-file", str(task), "--output-dir", str(out), "--run-id", "run", "--agent-id", "child", "--parent-id", "parent", "--wave-id", "wave", "--round", "1", "--depth", "2", "--seed", "12", "--voice-count", "2", "--mmm-root", str(root))
    assert prepared.returncode == 0
    receipt_path = out / "preload_receipt.json"
    receipt = json.loads(receipt_path.read_text())
    import hashlib
    call_path = out / "call.json"
    call_path.write_text(json.dumps({
        "schema": "constraintbox.provider-call.v1",
        "preload_receipt_sha256": hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
        "composed_prompt_sha256": receipt["composed_prompt_sha256"],
        "run_id": "run", "agent_id": "child", "parent_id": "parent", "wave_id": "wave",
        "round": 1, "depth": 2, "provider_request_id": "request-1", "terminal_state": "COMPLETED",
    }), encoding="utf-8")
    base = ("verify", "--receipt", str(receipt_path), "--call-receipt", str(call_path), "--expect-run-id", "run", "--expect-agent-id", "child", "--expect-parent-id", "parent", "--expect-wave-id", "wave", "--expect-round", "1", "--expect-depth", "2", "--mmm-root", str(root))
    checked = run(*base)
    assert checked.returncode == 0
    assert json.loads(checked.stdout)["disposition"] == "MMM_CALL_VERIFIED"
    rebound = list(base)
    rebound[rebound.index("child")] = "other-child"
    refused = run(*rebound)
    assert refused.returncode == 2
    assert "context:agent_id" in json.loads(refused.stdout)["errors"]

    missing = run(*base[:3], *base[5:])
    assert missing.returncode == 2
