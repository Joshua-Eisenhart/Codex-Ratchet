from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "package_wizard_candidate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("package_wizard_candidate", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("unable to load package_wizard_candidate module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_package_excludes_ds_store_and_legacy_v26_manifests(tmp_path: Path) -> None:
    candidate = tmp_path / "mmm_wizard_complete_system_packet_v2_7_candidate"
    (candidate / "current").mkdir(parents=True)
    (candidate / "legacy").mkdir()
    (candidate / ".DS_Store").write_text("finder metadata", encoding="utf-8")
    (candidate / "current" / ".DS_Store").write_text("nested finder metadata", encoding="utf-8")
    (candidate / "current" / "WIZARD_GENERAL_STANDARD_v2_7.md").write_text("keep", encoding="utf-8")
    (candidate / "tools" / "__pycache__").mkdir(parents=True)
    (candidate / "tools" / "__pycache__" / "runner.cpython-313.pyc").write_bytes(b"cache")
    (candidate / "MMM_PACKET_MANIFEST_v2_7.json").write_text("{}", encoding="utf-8")
    (candidate / "legacy" / "MMM_PACKET_MANIFEST_v2_6.json").write_text("old", encoding="utf-8")
    (candidate / "legacy" / "MMM_PACKET_MANIFEST_SOURCE_RENAMED_v2.6.md").write_text(
        "old renamed", encoding="utf-8"
    )
    (candidate / "audit" / "MMM_V2_6_VALIDATION_REPORT.md").parent.mkdir()
    (candidate / "audit" / "MMM_V2_6_VALIDATION_REPORT.md").write_text("not a manifest", encoding="utf-8")

    module = load_module()
    receipt = module.package_candidate(candidate, zip_path=tmp_path / "candidate.zip")

    assert receipt["input_path"] == str(candidate.resolve())
    assert receipt["zip_path"] == str((tmp_path / "candidate.zip").resolve())
    assert receipt["file_count"] == 3
    assert len(receipt["sha256"]) == 64
    assert receipt["generated_at"].endswith("Z")

    sidecar = tmp_path / "candidate.zip.sha256"
    assert sidecar.read_text(encoding="utf-8") == f"{receipt['sha256']}  candidate.zip\n"
    assert hashlib.sha256((tmp_path / "candidate.zip").read_bytes()).hexdigest() == receipt["sha256"]

    with zipfile.ZipFile(tmp_path / "candidate.zip") as archive:
        assert archive.namelist() == [
            "mmm_wizard_complete_system_packet_v2_7_candidate/MMM_PACKET_MANIFEST_v2_7.json",
            "mmm_wizard_complete_system_packet_v2_7_candidate/audit/MMM_V2_6_VALIDATION_REPORT.md",
            "mmm_wizard_complete_system_packet_v2_7_candidate/current/WIZARD_GENERAL_STANDARD_v2_7.md",
        ]


def test_cli_prints_json_receipt_and_can_write_receipt_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    (candidate / "README_FIRST_v2_7.md").write_text("read me", encoding="utf-8")

    module = load_module()
    rc = module.main(
        [
            str(candidate),
            "--zip-path",
            str(tmp_path / "candidate.zip"),
            "--receipt-path",
            str(tmp_path / "receipt.json"),
        ]
    )

    assert rc == 0
    stdout_receipt = json.loads(capsys.readouterr().out)
    file_receipt = json.loads((tmp_path / "receipt.json").read_text(encoding="utf-8"))
    assert stdout_receipt == file_receipt
    assert stdout_receipt["file_count"] == 1


def test_package_preserves_multiple_size_variants(tmp_path: Path) -> None:
    candidate = tmp_path / "mmm_wizard_complete_system_packet_v2_7_candidate"
    for size in ("compact", "standard", "full"):
        path = candidate / "mini_mmms" / size / "voices" / "md" / f"MMM_VOICE_HUME_{size.upper()}_v2_7.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# Hume {size}\n", encoding="utf-8")

    module = load_module()
    receipt = module.package_candidate(candidate, zip_path=tmp_path / "candidate.zip")

    assert receipt["file_count"] == 3
    with zipfile.ZipFile(tmp_path / "candidate.zip") as archive:
        names = set(archive.namelist())

    assert (
        "mmm_wizard_complete_system_packet_v2_7_candidate/mini_mmms/compact/voices/md/"
        "MMM_VOICE_HUME_COMPACT_v2_7.md"
    ) in names
    assert (
        "mmm_wizard_complete_system_packet_v2_7_candidate/mini_mmms/standard/voices/md/"
        "MMM_VOICE_HUME_STANDARD_v2_7.md"
    ) in names
    assert (
        "mmm_wizard_complete_system_packet_v2_7_candidate/mini_mmms/full/voices/md/"
        "MMM_VOICE_HUME_FULL_v2_7.md"
    ) in names
