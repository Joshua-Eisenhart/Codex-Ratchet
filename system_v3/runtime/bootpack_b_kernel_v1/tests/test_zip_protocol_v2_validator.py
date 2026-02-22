from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from containers import build_export_block
from zip_protocol_v2_validator import _ZIP_TYPES, validate_zip_protocol_v2


def _canonical_json_bytes(obj: object) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_payload_for_type(zip_type: str) -> dict[str, bytes]:
    payload = _ZIP_TYPES[zip_type]["payload_files"][0]
    if payload.endswith(".json"):
        return {payload: _canonical_json_bytes({"schema": "test", "value": 1})}
    if payload == "EXPORT_BLOCK.txt":
        text = build_export_block(
            export_id="E_TEST_001",
            proposal_type="TEST",
            content_lines=["SPEC_HYP S_TEST", "SPEC_KIND S_TEST CORR SIM_SPEC"],
            version="v1",
        )
        return {payload: text.encode("utf-8")}
    if payload == "THREAD_S_SAVE_SNAPSHOT_v2.txt":
        text = "\n".join(
            [
                "BEGIN THREAD_S_SAVE_SNAPSHOT v2",
                "END THREAD_S_SAVE_SNAPSHOT v2",
                "",
            ]
        )
        return {payload: text.encode("utf-8")}
    if payload == "SIM_EVIDENCE.txt":
        text = "\n".join(
            [
                "BEGIN SIM_EVIDENCE v1",
                "SIM_ID: SIM_001",
                f"CODE_HASH_SHA256: {'a'*64}",
                f"INPUT_HASH_SHA256: {'b'*64}",
                f"OUTPUT_HASH_SHA256: {'c'*64}",
                f"RUN_MANIFEST_SHA256: {'d'*64}",
                "END SIM_EVIDENCE v1",
                "",
            ]
        )
        return {payload: text.encode("utf-8")}
    raise AssertionError(f"unknown payload type: {payload}")


def _make_zip(
    root: Path,
    zip_type: str,
    sequence: int,
    run_id: str = "RUN_A",
    payload_files: dict[str, bytes] | None = None,
    source_layer_override: str | None = None,
) -> Path:
    mapping = _ZIP_TYPES[zip_type]
    payload = payload_files or _build_payload_for_type(zip_type)

    manifest_entries = []
    for rel_path in sorted(payload.keys()):
        b = payload[rel_path]
        manifest_entries.append({"rel_path": rel_path, "byte_size": len(b), "sha256": _sha(b)})
    manifest_bytes = _canonical_json_bytes(manifest_entries)

    header = {
        "zip_protocol": "ZIP_PROTOCOL_v2",
        "zip_type": zip_type,
        "direction": mapping["direction"],
        "source_layer": source_layer_override if source_layer_override is not None else mapping["source_layer"],
        "target_layer": mapping["target_layer"],
        "run_id": run_id,
        "sequence": sequence,
        "created_utc": "2026-02-21T00:00:00Z",
        "compiler_version": "A0_COMPILER_v1" if mapping["source_layer"] == "A0" else "",
        "manifest_sha256": _sha(manifest_bytes),
    }
    header_bytes = _canonical_json_bytes(header)

    hash_map = {
        "ZIP_HEADER.json": _sha(header_bytes),
        "MANIFEST.json": _sha(manifest_bytes),
    }
    for rel_path, b in payload.items():
        hash_map[rel_path] = _sha(b)
    hash_lines = [f"{hash_map[path]}  {path}" for path in sorted(hash_map.keys())]
    hashes_bytes = ("\n".join(hash_lines) + "\n").encode("utf-8")

    path = root / f"{zip_type}_{sequence}.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.writestr("HASHES.sha256", hashes_bytes)
        zf.writestr("MANIFEST.json", manifest_bytes)
        zf.writestr("ZIP_HEADER.json", header_bytes)
        for rel_path in sorted(payload.keys()):
            zf.writestr(rel_path, payload[rel_path])
    return path


class TestZipProtocolV2Validator(unittest.TestCase):
    def test_valid_export_zip_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = _make_zip(Path(td), "A0_TO_B_EXPORT_BATCH_ZIP", sequence=1)
            result = validate_zip_protocol_v2(str(p), {})
            self.assertEqual("OK", result["outcome"])

    def test_sequence_gap_parks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = _make_zip(Path(td), "A0_TO_B_EXPORT_BATCH_ZIP", sequence=3)
            seq = {("RUN_A", "A0"): 1}
            result = validate_zip_protocol_v2(str(p), seq)
            self.assertEqual("PARK", result["outcome"])

    def test_invalid_run_id_is_missing_header_field(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = _make_zip(Path(td), "A0_TO_B_EXPORT_BATCH_ZIP", sequence=1, run_id="bad run id")
            result = validate_zip_protocol_v2(str(p), {})
            self.assertEqual("REJECT", result["outcome"])
            self.assertEqual("MISSING_HEADER_FIELD", result["tag"])

    def test_manifest_payload_mismatch_rejects_forbidden_file_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            payload = {"WRONG.txt": b"BEGIN EXPORT_BLOCK v1\nEND EXPORT_BLOCK v1\n"}
            p = _make_zip(Path(td), "A0_TO_B_EXPORT_BATCH_ZIP", sequence=1, payload_files=payload)
            result = validate_zip_protocol_v2(str(p), {})
            self.assertEqual("REJECT", result["outcome"])
            self.assertEqual("FORBIDDEN_FILE_PRESENT", result["tag"])

    def test_forbidden_container_exact_line_rejects(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            payload = {
                "THREAD_S_SAVE_SNAPSHOT_v2.txt": "\n".join(
                    [
                        "BEGIN THREAD_S_SAVE_SNAPSHOT v2",
                        "BEGIN SIM_EVIDENCE v1",
                        "END THREAD_S_SAVE_SNAPSHOT v2",
                        "",
                    ]
                ).encode("utf-8")
            }
            p = _make_zip(Path(td), "B_TO_A0_STATE_UPDATE_ZIP", sequence=1, payload_files=payload)
            result = validate_zip_protocol_v2(str(p), {})
            self.assertEqual("REJECT", result["outcome"])
            self.assertEqual("FORBIDDEN_CONTAINER_PRESENT", result["tag"])


if __name__ == "__main__":
    unittest.main()

