from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "seal_context_epoch.py"
SPEC = importlib.util.spec_from_file_location("seal_context_epoch", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
seal = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = seal
SPEC.loader.exec_module(seal)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _fixture(tmp_path: Path) -> tuple[Path, Path, dict[str, object]]:
    root = tmp_path / "contained-root"
    root.mkdir()
    genesis = root / "state" / "GENESIS.json"
    # This is intentionally a historical, human-readable projection.  Its
    # safe false field is accepted as provenance but is not copied into v2.
    genesis_value = {
        "schema": seal.GENESIS_SCHEMA,
        "predecessor": {
            "event_count": 3,
            "head_sha256": "a" * 64,
            "ledger_sha256": "b" * 64,
            "full_object_store_included": False,
        },
        "context_projection": {
            "path": "context/full/prompt_plan_progress_corpus.jsonl",
            "sha256": "c" * 64,
            "selected_event_count": 2,
        },
        "migration_rule": "cite only",
        "claim_ceiling": "projection only",
        "promotion_allowed": False,
    }
    _write(genesis, (json.dumps(genesis_value, indent=2) + "\n").encode())

    files = {
        "corpus": ("context/full/prompt_plan_progress_corpus.jsonl", b"corpus\n"),
        "corpus_manifest": (
            "context/full/CORPUS_MANIFEST.json",
            b'{"schema":"corpus"}\n',
        ),
        "refresh_ledger": (
            "context/full/CORPUS_REFRESH_LEDGER.jsonl",
            b'{"sequence":1}\n',
        ),
        "wave_bootstrap": (
            "state/WAVE_BOOTSTRAP_20260817.json",
            b'{"schema":"bootstrap"}\n',
        ),
        "consolidation": (
            "state/CONSOLIDATION_20260817.json",
            b'{"schema":"consolidation"}\n',
        ),
        "retained_receipt_manifest": (
            "state/receipts/RETENTION_MANIFEST.json",
            b'{"schema":"retention"}\n',
        ),
    }
    bindings: dict[str, object] = {}
    for name, (relative, data) in files.items():
        _write(root / relative, data)
        bindings[name] = relative
    current: dict[str, str] = {}
    for name in (
        "OWNER_OBJECT.md",
        "PRODUCT_CONTRACT.md",
        "WORK_ASSESSMENT.md",
        "CURRENT_PLAN.md",
        "FAILURE_MEMORY.md",
        "OPEN_HYPOTHESES.md",
    ):
        relative = f"context/current/{name}"
        _write(root / relative, f"{name}\nexact bytes\n".encode())
        current[name] = relative
    bindings["current_context"] = current
    return root, genesis, bindings


def _ref(root: Path, path: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": _sha(path)}


def _seal_first(
    root: Path,
    genesis: Path,
    bindings: dict[str, object],
    name: str = "epoch-00000001.json",
    epoch_id: str | None = None,
) -> Path:
    output = root / "state" / "epochs" / name
    seal.seal_epoch(
        root,
        output,
        _ref(root, genesis),
        bindings,
        captured_at="2026-08-18T12:00:00.000Z",
        epoch_id=epoch_id,
    )
    return output


def test_creation_accepts_safe_genesis_and_binds_current_bytes(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    epoch = _seal_first(root, genesis, bindings)

    value = json.loads(epoch.read_text())
    assert value["schema"] == seal.SCHEMA
    assert value["epoch_sequence"] == 1
    assert value["parent"] == _ref(root, genesis)
    assert "promotion_allowed" not in value
    assert "truth_disposition" not in value
    assert epoch.read_bytes() == seal.canonical_json_bytes(value) + b"\n"
    assert value["epoch_digest"] == seal.sha256_bytes(
        seal.canonical_json_bytes({k: v for k, v in value.items() if k != "epoch_digest"})
    )
    result = seal.verify_epoch(root, epoch)
    assert result["epoch_sequence"] == 1
    assert result["parent"] == _ref(root, genesis)


@pytest.mark.parametrize("historical_value", [None, True])
def test_genesis_requires_literal_false_promotion_field(
    tmp_path: Path, historical_value: object
) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    value = json.loads(genesis.read_text())
    if historical_value is None:
        del value["promotion_allowed"]
    else:
        value["promotion_allowed"] = historical_value
    genesis.write_text(json.dumps(value, indent=2) + "\n")
    with pytest.raises(seal.EpochRefusal, match="REFUSE_GENESIS_DISPOSITION_FIELD"):
        _seal_first(root, genesis, bindings)


def test_full_chain_verification_requires_verified_parent(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    first = _seal_first(root, genesis, bindings)
    second = root / "state" / "epochs" / "epoch-00000002.json"
    seal.seal_epoch(
        root,
        second,
        _ref(root, first),
        bindings,
        captured_at="2026-08-18T12:01:00.000Z",
    )

    result = seal.verify_epoch(root, second)
    assert result["epoch_sequence"] == 2
    assert result["parent"] == _ref(root, first)


def test_successor_uses_historical_parent_mode_after_live_context_drift(
    tmp_path: Path,
) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    first = _seal_first(root, genesis, bindings)
    (root / "context" / "current" / "CURRENT_PLAN.md").write_bytes(
        b"new plan bytes\n"
    )
    (root / "context" / "current" / "WORK_ASSESSMENT.md").write_bytes(
        b"new assessment bytes\n"
    )

    with pytest.raises(seal.EpochRefusal, match="REFUSE_BOUND_FILE_SHA256_MISMATCH"):
        seal.verify_epoch(root, first)
    historical = seal.verify_epoch(
        root, first, mode=seal.HISTORICAL_CHAIN_INTEGRITY
    )
    assert historical["status"] == "PASS"
    assert historical["mode"] == seal.HISTORICAL_CHAIN_INTEGRITY
    assert historical["verification_mode"] == seal.HISTORICAL_CHAIN_INTEGRITY
    assert historical["historical_chain_integrity"] == "VERIFIED"
    assert historical["historical_chain_integrity_status"] == "VERIFIED"
    assert historical["current_bindings_checked"] is False
    assert historical["current_bindings"] == "NOT_CHECKED"
    assert historical["current_bindings_status"] == "NOT_CHECKED"
    assert "not checked" in historical["claim_ceiling"]

    second = root / "state" / "epochs" / "epoch-00000002.json"
    seal.seal_epoch(
        root,
        second,
        _ref(root, first),
        bindings,
        captured_at="2026-08-18T12:01:00.000Z",
    )
    successor = seal.verify_epoch(root, second)
    assert successor["mode"] == seal.CURRENT_BINDINGS
    assert successor["verification_mode"] == seal.CURRENT_BINDINGS
    assert successor["historical_chain_integrity"] == "VERIFIED"
    assert successor["current_bindings_checked"] is True
    assert successor["current_bindings"] == "VERIFIED"


def test_historical_parent_self_tamper_still_refuses_successor(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    first = _seal_first(root, genesis, bindings)
    value = json.loads(first.read_text())
    value["epoch_id"] = "tampered-parent"
    # Deliberately retain the old self digest: the parent file is now a
    # tampered but hash-rebound historical candidate.
    first.write_bytes(seal.canonical_json_bytes(value) + b"\n")
    second = root / "state" / "epochs" / "epoch-00000002.json"
    with pytest.raises(seal.EpochRefusal, match="REFUSE_EPOCH_SELF_DIGEST_MISMATCH"):
        seal.seal_epoch(root, second, _ref(root, first), bindings)


def test_current_file_drift_refuses_full_chain(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    epoch = _seal_first(root, genesis, bindings)
    current_file = root / "context" / "current" / "OWNER_OBJECT.md"
    current_file.write_bytes(b"drifted current context\n")
    with pytest.raises(seal.EpochRefusal, match="REFUSE_BOUND_FILE_SHA256_MISMATCH"):
        seal.verify_epoch(root, epoch)


def test_parent_drift_refuses_child_even_when_genesis_stays_safe(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    epoch = _seal_first(root, genesis, bindings)
    value = json.loads(genesis.read_text())
    value["claim_ceiling"] = "changed historical bytes"
    genesis.write_text(json.dumps(value, indent=2) + "\n")
    with pytest.raises(seal.EpochRefusal, match="REFUSE_PARENT_SHA256_MISMATCH"):
        seal.verify_epoch(root, epoch)


def test_path_escape_and_symlink_escape_are_refused(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    escaped = copy.deepcopy(bindings)
    escaped["corpus"] = "../outside-corpus"
    with pytest.raises(seal.EpochRefusal, match="REFUSE_PATH_ESCAPE"):
        seal.seal_epoch(root, "state/epochs/escape.json", _ref(root, genesis), escaped)

    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"outside\n")
    symlink = root / "context" / "full" / "corpus-link"
    symlink.symlink_to(outside)
    linked = copy.deepcopy(bindings)
    linked["corpus"] = "context/full/corpus-link"
    with pytest.raises(seal.EpochRefusal, match="REFUSE_SYMLINK_PATH"):
        seal.seal_epoch(root, "state/epochs/symlink.json", _ref(root, genesis), linked)

    parent_link = root / "state" / "genesis-link.json"
    parent_link.symlink_to(genesis)
    with pytest.raises(seal.EpochRefusal, match="REFUSE_SYMLINK_PATH"):
        seal.seal_epoch(
            root,
            "state/epochs/parent-link.json",
            {"path": "state/genesis-link.json", "sha256": _sha(genesis)},
            bindings,
        )


def test_noncanonical_epoch_bytes_are_refused(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    epoch = _seal_first(root, genesis, bindings)
    value = json.loads(epoch.read_text())
    epoch.write_text(json.dumps(value, indent=2) + "\n")
    with pytest.raises(seal.EpochRefusal, match="REFUSE_EPOCH_NON_CANONICAL_BYTES"):
        seal.verify_epoch(root, epoch)


def test_parent_cycle_guard_refuses_self_parent_before_hash_resolution(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    epoch = _seal_first(root, genesis, bindings)
    value = json.loads(epoch.read_text())
    value["parent"] = {
        "path": epoch.relative_to(root).as_posix(),
        "sha256": seal.ZERO_SHA256,
    }
    value["epoch_digest"] = seal.sha256_bytes(
        seal.canonical_json_bytes({k: v for k, v in value.items() if k != "epoch_digest"})
    )
    epoch.write_bytes(seal.canonical_json_bytes(value) + b"\n")
    with pytest.raises(seal.EpochRefusal, match="REFUSE_EPOCH_PARENT_CYCLE"):
        seal.verify_epoch(root, epoch)


def test_pointer_compare_and_swap_and_full_pointer_verification(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    first = _seal_first(root, genesis, bindings)
    pointer = root / "state" / "CURRENT_EPOCH.json"
    first_pointer = seal.update_current_pointer(
        root,
        pointer,
        first,
        _ref(root, genesis),
        updated_at="2026-08-18T12:00:01.000Z",
    )
    assert first_pointer["authoritative"] is False
    assert seal.verify_pointer(root, pointer)["epoch"]["epoch_sequence"] == 1

    second = root / "state" / "epochs" / "epoch-00000002.json"
    seal.seal_epoch(
        root,
        second,
        _ref(root, first),
        bindings,
        captured_at="2026-08-18T12:01:00.000Z",
    )
    seal.update_current_pointer(root, pointer, second, _ref(root, first))
    assert seal.verify_pointer(root, pointer)["epoch"]["epoch_sequence"] == 2

    # The new epoch still names first as its parent, but the pointer has
    # already advanced to second.  A stale writer must not overwrite it.
    with pytest.raises(seal.EpochRefusal, match="REFUSE_POINTER_CAS"):
        seal.update_current_pointer(root, pointer, second, _ref(root, first))


def test_pointer_flushes_replaced_file_then_containing_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    epoch = _seal_first(root, genesis, bindings)
    pointer = root / "state" / "CURRENT_EPOCH.json"
    events: list[str] = []
    original_replace = seal.os.replace
    original_file_flush = seal._fsync_file
    original_directory_flush = seal._fsync_directory

    def record_replace(source: object, destination: object) -> None:
        events.append("replace")
        original_replace(source, destination)

    def record_file_flush(path: Path) -> None:
        events.append("file")
        original_file_flush(path)

    def record_directory_flush(path: Path) -> None:
        events.append("directory")
        original_directory_flush(path)

    monkeypatch.setattr(seal.os, "replace", record_replace)
    monkeypatch.setattr(seal, "_fsync_file", record_file_flush)
    monkeypatch.setattr(seal, "_fsync_directory", record_directory_flush)
    seal.update_current_pointer(root, pointer, epoch, _ref(root, genesis))
    assert events == ["replace", "file", "directory"]
    assert seal.verify_pointer(root, pointer)["epoch"]["epoch_sequence"] == 1


def test_pointer_lock_has_bounded_timeout(tmp_path: Path) -> None:
    root, _genesis, _bindings = _fixture(tmp_path)
    state_directory = root / "state"
    with seal._pointer_directory_lock(state_directory):
        with pytest.raises(seal.EpochRefusal, match="REFUSE_POINTER_LOCK_TIMEOUT"):
            with seal._pointer_directory_lock(state_directory, timeout=0.02):
                raise AssertionError("the competing lock unexpectedly acquired")


def test_competing_pointer_writers_publish_at_most_one_successor(tmp_path: Path) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    first = _seal_first(
        root, genesis, bindings, "epoch-a.json", epoch_id="epoch-a"
    )
    second = _seal_first(
        root, genesis, bindings, "epoch-b.json", epoch_id="epoch-b"
    )
    pointer = root / "state" / "CURRENT_EPOCH.json"
    command_base = [
        sys.executable,
        str(SCRIPT),
        "pointer",
        "--root",
        str(root),
        "--pointer",
        "state/CURRENT_EPOCH.json",
        "--prior-parent",
        genesis.relative_to(root).as_posix(),
        "--prior-parent-sha256",
        _sha(genesis),
    ]
    processes = [
        subprocess.Popen(
            command_base + ["--epoch", epoch.relative_to(root).as_posix()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for epoch in (first, second)
    ]
    results = [process.communicate(timeout=10) for process in processes]
    statuses = [process.returncode for process in processes]
    assert statuses.count(0) == 1, results
    assert statuses.count(2) == 1, results
    assert "REFUSE_POINTER_CAS" in "\n".join(
        stdout + stderr for stdout, stderr in results if "REFUSE_POINTER_CAS" in stdout + stderr
    )
    verified = seal.verify_pointer(root, pointer)
    assert verified["epoch"]["path"] in {
        first.relative_to(root).as_posix(),
        second.relative_to(root).as_posix(),
    }


def test_epoch_and_pointer_crash_recovery_leave_no_partial_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, genesis, bindings = _fixture(tmp_path)
    output = root / "state" / "epochs" / "epoch-crash.json"
    original_link = seal.os.link
    state = {"fail": True}

    def fail_once(source: object, destination: object) -> None:
        if state["fail"]:
            state["fail"] = False
            raise RuntimeError("injected epoch publication crash")
        original_link(source, destination)

    monkeypatch.setattr(seal.os, "link", fail_once)
    with pytest.raises(RuntimeError, match="injected epoch publication crash"):
        seal.seal_epoch(root, output, _ref(root, genesis), bindings)
    assert not output.exists()
    assert not list(output.parent.glob(f".{output.name}.*"))

    seal.seal_epoch(root, output, _ref(root, genesis), bindings)
    assert seal.verify_epoch(root, output)["epoch_sequence"] == 1

    pointer = root / "state" / "CURRENT_EPOCH.json"
    original_replace = seal.os.replace
    replace_state = {"fail": True}

    def fail_replace_once(source: object, destination: object) -> None:
        if replace_state["fail"]:
            replace_state["fail"] = False
            raise RuntimeError("injected pointer publication crash")
        original_replace(source, destination)

    monkeypatch.setattr(seal.os, "replace", fail_replace_once)
    with pytest.raises(RuntimeError, match="injected pointer publication crash"):
        seal.update_current_pointer(root, pointer, output, _ref(root, genesis))
    assert not pointer.exists()
    assert not list(pointer.parent.glob(".current-epoch.*"))

    seal.update_current_pointer(root, pointer, output, _ref(root, genesis))
    assert seal.verify_pointer(root, pointer)["epoch"]["epoch_sequence"] == 1
