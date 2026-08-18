from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Keep the tests runnable from either the skill directory or an arbitrary
# repository cwd.  The skill's scripts are intentionally not installed as a
# package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_maintenance_wave import declared_digest, run_wave
from scripts.validate_receipt import validate


def _layout(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "constraint_box"
    package = root / "zip_agent"
    (package / "src").mkdir(parents=True)
    (package / "scripts").mkdir()
    (package / "project_state").mkdir()
    (package / "context").mkdir()
    (package / "src" / "main.py").write_text("print('ok')\n", encoding="utf-8")
    (package / "project_state" / "events.jsonl").write_text('{"event":1}\n', encoding="utf-8")
    (package / "context" / "CURRENT.md").write_text("context\n", encoding="utf-8")
    return root, package


def _run(root: Path, package: Path, **kwargs):
    return run_wave(
        root=root,
        package=package,
        source_paths=["zip_agent/src", "zip_agent/scripts"],
        context_paths=["zip_agent/project_state", "zip_agent/context"],
        ledger_path="zip_agent/project_state/events.jsonl",
        **kwargs,
    )


def test_positive_dry_run_is_ready_and_never_moves(tmp_path: Path) -> None:
    root, package = _layout(tmp_path)
    candidate = root / "integrated_system" / "runs" / "tmp__old.json"
    candidate.parent.mkdir(parents=True)
    candidate.write_text("staged\n", encoding="utf-8")
    receipt = _run(root, package, candidates=[str(candidate)])

    assert receipt["status"] == "READY"
    assert receipt["candidate_decisions"][0]["classification"] == "MOVE_TO_ARCHIVE"
    assert receipt["mutation_performed"] is False
    assert candidate.exists()
    assert validate(receipt) == []


def test_deletion_request_is_refused_without_touching_candidate(tmp_path: Path) -> None:
    root, package = _layout(tmp_path)
    candidate = package / "generated.json"
    candidate.write_text("keep\n", encoding="utf-8")
    receipt = _run(root, package, candidates=[str(candidate)], requested_action="delete")

    assert receipt["status"] == "HOLD"
    assert any(item["code"] == "REFUSE_DESTRUCTIVE_ACTION" for item in receipt["blockers"])
    assert receipt["candidate_decisions"][0]["reason_code"] == "REFUSE_DESTRUCTIVE_ACTION"
    assert candidate.read_text(encoding="utf-8") == "keep\n"
    assert receipt["mutation_performed"] is False


def test_archive_is_never_an_authoritative_source(tmp_path: Path) -> None:
    root, package = _layout(tmp_path)
    candidate = root / "archive" / "source.md"
    candidate.parent.mkdir()
    candidate.write_text("historical\n", encoding="utf-8")
    receipt = _run(root, package, candidates=[str(candidate)])

    assert receipt["status"] == "HOLD"
    assert receipt["candidate_decisions"][0]["reason_code"] == "ARCHIVE_SOURCE"


def test_fresh_and_ambiguous_owner_surfaces_block(tmp_path: Path) -> None:
    root, package = _layout(tmp_path)
    fresh = package / "project_state" / "owner" / "fresh.md"
    fresh.parent.mkdir()
    fresh.write_text("owner\n", encoding="utf-8")
    old = package / "project_state" / "owner" / "old.md"
    old.write_text("owner\n", encoding="utf-8")
    old_time = (datetime.now(timezone.utc) - timedelta(hours=100)).timestamp()
    os.utime(old, (old_time, old_time))
    receipt = _run(root, package, candidates=[str(fresh), str(old)])

    reasons = [item["reason_code"] for item in receipt["candidate_decisions"]]
    assert receipt["status"] == "HOLD"
    assert reasons == ["FRESH_OWNER_SURFACE", "AMBIGUOUS_OWNER_SURFACE"]


def test_missing_required_receipt_holds(tmp_path: Path) -> None:
    root, package = _layout(tmp_path)
    missing = package / "runs" / "provider.json"
    receipt = _run(root, package, required_receipts=[str(missing)])

    assert receipt["status"] == "HOLD"
    assert {item["code"] for item in receipt["blockers"]} >= {"REFUSE_MISSING_RECEIPT"}
    assert validate(receipt) == []


def test_source_digest_ignores_python_caches_but_tracks_source(tmp_path: Path) -> None:
    root, package = _layout(tmp_path)
    source = root / "zip_agent" / "src"
    before, _ = declared_digest(root, ["zip_agent/src"])
    cache = source / "__pycache__"
    cache.mkdir()
    (cache / "main.cpython-313.pyc").write_bytes(b"generated")
    (source / ".pytest_cache").mkdir()
    (source / ".pytest_cache" / "lastfailed").write_text("generated\n", encoding="utf-8")
    after_cache, _ = declared_digest(root, ["zip_agent/src"])
    assert before == after_cache
    (source / "main.py").write_text("print('changed')\n", encoding="utf-8")
    after_source, _ = declared_digest(root, ["zip_agent/src"])
    assert after_source != before
