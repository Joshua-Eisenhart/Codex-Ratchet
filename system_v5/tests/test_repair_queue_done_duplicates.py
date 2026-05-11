from __future__ import annotations

import json
import os
import subprocess
import time
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "repair_queue_done_duplicates.py"


def _write_done_file(done_dir: Path, stem: str, suffix: str, contents: str) -> Path:
    path = done_dir / f"{stem}.json.{suffix}"
    path.write_text(contents, encoding="utf-8")
    return path


def _run_repair(argv: list[str], env: dict[str, str] | None = None) -> str:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)] + argv,
        check=False,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    assert proc.returncode == 0, proc.stdout
    return proc.stdout


def test_repair_duplicates_dry_run_does_not_move(tmp_path: Path) -> None:
    done_dir = tmp_path / "done"
    dup_dir = tmp_path / "done" / ".duplicates"
    done_dir.mkdir(parents=True)
    base = "sim_dupe_case"
    old = _write_done_file(done_dir, base, "111.host.old", "first")
    time.sleep(0.01)
    new = _write_done_file(done_dir, base, "222.host.new", "second")

    _run_repair(
        [
            "--done-dir",
            str(done_dir),
            "--duplicates-dir",
            str(dup_dir),
            "--keep-newest",
            "--report-path",
            str(tmp_path / "dry_report.json"),
        ]
    )

    assert len(list(done_dir.glob("*.json.*"))) == 2
    assert not dup_dir.exists() or len(list(dup_dir.glob("*.json.*"))) == 0
    report = json.loads((tmp_path / "dry_report.json").read_text(encoding="utf-8"))
    assert report["apply"] is False
    assert report["moved_file_count"] == 0
    assert report["total_duplicate_files"] == 1


def test_repair_duplicates_apply_moves_oldest_and_keeps_newest(tmp_path: Path) -> None:
    done_dir = tmp_path / "done"
    dup_dir = tmp_path / "done" / ".duplicates"
    done_dir.mkdir(parents=True)
    base = "sim_apply_case"
    old = _write_done_file(done_dir, base, "100.host.old", "first")
    time.sleep(0.01)
    new = _write_done_file(done_dir, base, "200.host.new", "second")
    os.utime(str(new), (time.time() + 10, time.time() + 10))

    report_path = tmp_path / "apply_report.json"
    _run_repair(
        [
            "--done-dir",
            str(done_dir),
            "--duplicates-dir",
            str(dup_dir),
            "--keep-newest",
            "--apply",
            "--report-path",
            str(report_path),
        ]
    )

    remaining = sorted(done_dir.glob("*.json.*"))
    archived = sorted(dup_dir.glob("*.json.*"))
    assert len(remaining) == 1
    assert len(archived) == 1
    assert remaining[0].name == new.name
    assert new.exists()
    assert not old.exists()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["apply"] is True
    assert report["moved_file_count"] == 1
    assert report["moved_files"] == [old.name]
    assert report["post_repair_duplicate_files"] == 0
    assert report["pre_archive_duplicate_count"] == 0
    assert report["post_archive_duplicate_count"] == 1
    assert report["post_repair_archive_files"] == 1
    assert report["archive_duplicate_added"] == [old.name]
    assert report["archive_duplicate_removed"] == []
    assert report["forensic_manifest"] == [
        {
            "base_id": base,
            "keeper": new.name,
            "keeper_path": str(new),
            "keeper_sha256": report["forensic_manifest"][0]["keeper_sha256"],
            "moved": [old.name],
            "moved_records": report["forensic_manifest"][0]["moved_records"],
        }
    ]
    assert len(report["forensic_manifest"][0]["keeper_sha256"]) == 64
    assert report["forensic_manifest"][0]["moved_records"][0]["name"] == old.name
    assert len(report["forensic_manifest"][0]["moved_records"][0]["sha256"]) == 64


def test_repair_duplicate_report_tracks_existing_and_new_archive_entries(tmp_path: Path) -> None:
    done_dir = tmp_path / "done"
    dup_dir = tmp_path / "done" / ".duplicates"
    done_dir.mkdir(parents=True)
    dup_dir.mkdir(parents=True)
    pre_archived = _write_done_file(done_dir, "pre_archived", "000.a.host.seed", "seed")
    os.rename(pre_archived, dup_dir / pre_archived.name)

    base = "sim_archive_case"
    old = _write_done_file(done_dir, base, "111.host.old", "first")
    time.sleep(0.01)
    new = _write_done_file(done_dir, base, "222.host.new", "second")
    os.utime(str(new), (time.time() + 10, time.time() + 10))

    report_path = tmp_path / "apply_report.json"
    _run_repair(
        [
            "--done-dir",
            str(done_dir),
            "--duplicates-dir",
            str(dup_dir),
            "--keep-newest",
            "--apply",
            "--report-path",
            str(report_path),
        ]
    )

    assert (dup_dir / old.name).exists()
    assert not old.exists()
    assert new.exists()

    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["apply"] is True
    assert report["pre_archive_duplicate_count"] == 1
    assert report["post_archive_duplicate_count"] == 2
    assert report["post_repair_archive_files"] == 2
    assert report["archive_duplicate_added"] == [old.name]
    assert report["archive_duplicate_removed"] == []
    archive_rows = {
        row["base_id"]: row for row in report["archive_duplicate_manifest"]
    }
    assert archive_rows[base]["records"][0]["name"] == old.name
    assert len(archive_rows[base]["records"][0]["sha256"]) == 64
