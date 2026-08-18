from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Keep the tests runnable from either the skill directory or an arbitrary
# repository cwd.  The skill's scripts are intentionally not installed as a
# package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_maintenance_wave import declared_digest, run_wave
from scripts.validate_receipt import validate


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return completed.stdout


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


def test_git_inventory_exposes_dirty_linked_worktree(tmp_path: Path) -> None:
    root, package = _layout(tmp_path)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "cb-test@example.invalid")
    _git(root, "config", "user.name", "ConstraintBox Test")
    (root / "README.md").write_text("canonical\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "initial")
    canonical_head = _git(root, "rev-parse", "HEAD").strip()

    old_desktop = tmp_path / "Desktop" / "Codex Ratchet"
    old_desktop.parent.mkdir()
    _git(root, "worktree", "add", "-q", "-b", "old-desktop", str(old_desktop))
    (old_desktop / "README.md").write_text("old dirty\n", encoding="utf-8")

    receipt = _run(root, package)
    assert receipt["status"] == "READY"
    git = receipt["diagnostics"]["git"]
    assert git["available"] is True
    assert git["worktrees_available"] is True
    inventory = git["worktree_inventory"]
    assert inventory["source"] == "git worktree list --porcelain"
    assert inventory["count"] == 2

    states = {Path(item["resolved_path"]): item for item in inventory["worktrees"]}
    canonical = states[root.resolve()]
    sibling = states[old_desktop.resolve()]
    assert canonical["head"] == canonical_head
    assert canonical["branch"] is not None
    assert sibling["branch"] == "old-desktop"
    assert sibling["head"] == canonical_head
    assert sibling["status"]["available"] is True
    assert sibling["status"]["changed_count"] >= 1
    assert any("README.md" in line for line in sibling["status"]["entries"])


def test_non_git_root_reports_unavailable_without_blocking_portability(tmp_path: Path) -> None:
    root, package = _layout(tmp_path)
    receipt = _run(root, package)

    assert receipt["status"] == "READY"
    git = receipt["diagnostics"]["git"]
    assert git["available"] is False
    assert git["worktrees"] == []
    assert git["worktree_inventory"]["available"] is False
    assert git["worktree_inventory"]["worktrees"] == []
