from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_integrated_system.py"
SPEC = importlib.util.spec_from_file_location("verify_integrated_system", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
verifier = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verifier)


def _env(tmp_path: Path) -> dict[str, str]:
    return {"PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"}


def test_canonical_json_and_digest_are_stable() -> None:
    value = {"b": 2, "a": [True, "x"]}
    assert verifier.canonical_json_bytes(value) == b'{"a":[true,"x"],"b":2}'
    assert verifier.sha256_bytes(verifier.canonical_json_bytes(value)) == verifier.sha256_bytes(
        verifier.canonical_json_bytes({"a": [True, "x"], "b": 2})
    )


def test_run_command_records_exact_invocation_and_expected_nonzero(tmp_path: Path) -> None:
    env = _env(tmp_path)
    record = verifier.run_command(
        "expected-refusal",
        [sys.executable, "-c", "print('refused'); raise SystemExit(2)"],
        cwd=tmp_path,
        env=env,
        timeout_seconds=5,
        expected_returncodes=(2,),
    )
    assert record["status"] == "PASS"
    assert record["returncode"] == 2
    assert record["argv"][0] == sys.executable
    assert record["stdout_sha256"]
    assert record["stdout_tail"] == "refused\n"


def test_run_command_timeout_is_hold_and_bounded(tmp_path: Path) -> None:
    record = verifier.run_command(
        "timeout",
        [sys.executable, "-c", "import time; time.sleep(5)"],
        cwd=tmp_path,
        env=_env(tmp_path),
        timeout_seconds=0.01,
    )
    assert record["status"] == "HOLD"
    assert record["reason_code"] == "HOLD_COMMAND_TIMEOUT"


def test_pytest_summary_is_observational() -> None:
    summary = verifier.parse_pytest_summary("71 passed, 2 skipped in 0.4s")
    assert summary == {"passed": 71, "skipped": 2}
    assert verifier.parse_pytest_summary("no tests ran") == {"no_tests_ran": 1}


def test_context_and_skill_receipts_recompute_from_current_files() -> None:
    box = Path(__file__).resolve().parents[2]
    system = box / "integrated_system"
    context = verifier.check_context(system)
    skills = verifier.check_skill_estate(system)
    assert context["status"] == "PASS", context
    assert context["event_count"] == context["manifest_event_count"]
    assert skills["status"] == "PASS", skills
    assert skills["active_wave_count"] == 5


def test_retained_structured_and_bridge_receipts_are_checked_without_promotion() -> None:
    box = Path(__file__).resolve().parents[2]
    system = box / "integrated_system"
    structured = verifier.check_structured_receipt(system)
    bridge = verifier.check_bridge_receipt(system)
    assert structured["status"] == "PASS", structured
    assert structured["exact_jax_agreement"] is True
    assert structured["crosscheck_projection_recomputed"] is False
    assert bridge["status"] == "PASS", bridge
    assert bridge["semantic_replay_identical"] is True


def test_structured_projection_excludes_engine_specific_fields() -> None:
    exact = {"schema": "s", "status": "PASS", "engine": "exact", "jax": {"ran": False}, "controls": {"x": True}}
    dual = {"schema": "s", "status": "PASS", "engine": "dual", "jax": {"ran": True}, "controls": {"x": True}}
    assert verifier.structured_projection(exact) == verifier.structured_projection(dual)


def test_test_groups_name_two_estate_wide_exclusions() -> None:
    ignores = verifier.test_groups()["curated_skills"]
    assert any("cb-wave-author/tests/test_wave_definitions.py" in value for value in ignores)
    assert any("cb-wave-admission-gate/tests/test_admit.py" in value for value in ignores)
    assert not any("cb-wave-self-loop/tests/test_score_estate.py" in value for value in ignores)


TOP_LEVEL_NAME = "constraintbox-integrated-system-v1"


def _write_json(path: Path, value: dict) -> bytes:
    rendered = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.write_bytes(rendered)
    return rendered


def _build_bundle(root: Path, payloads: dict[str, bytes]) -> Path:
    """Write a minimal, schema-correct extracted bundle envelope under ``root``."""

    bundle_root = root / TOP_LEVEL_NAME
    bundle_root.mkdir(parents=True)
    rows = []
    for relative in sorted(payloads):
        data = payloads[relative]
        destination = bundle_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        rows.append(
            {
                "path": relative,
                "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
                "mode": "0644",
            }
        )
    manifest = {
        "schema": "constraintbox.integrated-system-manifest.v1",
        "top_level": TOP_LEVEL_NAME,
        "file_count": len(rows),
        "payload_bytes": sum(row["bytes"] for row in rows),
        "files": rows,
        "promotion_allowed": False,
    }
    manifest_bytes = _write_json(bundle_root / "SYSTEM_MANIFEST.json", manifest)
    metadata = {
        "schema": "constraintbox.integrated-system-metadata.v1",
        "top_level": TOP_LEVEL_NAME,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "payload_file_count": len(rows),
        "payload_bytes": manifest["payload_bytes"],
        "promotion_allowed": False,
    }
    metadata_bytes = _write_json(bundle_root / "BUNDLE_METADATA.json", metadata)
    checksum_rows = [(f"{TOP_LEVEL_NAME}/{row['path']}", row["sha256"]) for row in rows]
    checksum_rows.append((f"{TOP_LEVEL_NAME}/SYSTEM_MANIFEST.json", hashlib.sha256(manifest_bytes).hexdigest()))
    checksum_rows.append((f"{TOP_LEVEL_NAME}/BUNDLE_METADATA.json", hashlib.sha256(metadata_bytes).hexdigest()))
    checksum_text = "".join(f"{digest}  {path}\n" for path, digest in sorted(checksum_rows))
    (bundle_root / "SHA256SUMS").write_text(checksum_text, encoding="utf-8")
    return bundle_root


def test_bundle_envelope_not_applicable_for_plain_source_checkout(tmp_path: Path) -> None:
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "NOT_APPLICABLE"
    assert result["reason_codes"] == ["NOT_APPLICABLE_NO_BUNDLE_ENVELOPE"]


def test_bundle_envelope_passes_for_a_well_formed_bundle(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n", "sub/dir/file.bin": b"\x00\x01\x02"})
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "PASS", result
    assert result["reason_codes"] == []
    assert result["manifest_file_count"] == 2

    # Also works when box_root is handed in as the bundle root directly,
    # matching an extraction tool that returns the top-level directory.
    direct = verifier.check_bundle_envelope(tmp_path / TOP_LEVEL_NAME)
    assert direct["status"] == "PASS", direct
    nested_box = bundle_root / "PROJECT" / "constraint_box"
    nested_box.mkdir(parents=True)
    nested = verifier.check_bundle_envelope(nested_box)
    assert nested["status"] == "PASS", nested


def test_bundle_envelope_detects_tampered_payload(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    (bundle_root / "hello.txt").write_bytes(b"tampered\n")
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_BUNDLE_PAYLOAD_DIGEST_MISMATCH") for code in result["reason_codes"])


def test_bundle_envelope_detects_path_traversal(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    manifest_path = bundle_root / "SYSTEM_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = "../escape.txt"
    manifest_bytes = _write_json(manifest_path, manifest)
    metadata_path = bundle_root / "BUNDLE_METADATA.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    _write_json(metadata_path, metadata)
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_BUNDLE_MANIFEST_PATH_UNSAFE") for code in result["reason_codes"])


def test_bundle_envelope_detects_missing_checksum_entry(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n", "second.txt": b"second\n"})
    checksums_path = bundle_root / "SHA256SUMS"
    kept = [line for line in checksums_path.read_text(encoding="utf-8").splitlines() if "second.txt" not in line]
    checksums_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_BUNDLE_CHECKSUMS_MISSING") for code in result["reason_codes"])


def test_bundle_envelope_detects_duplicate_checksum_entry(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    checksums_path = bundle_root / "SHA256SUMS"
    text = checksums_path.read_text(encoding="utf-8")
    duplicated_line = next(line for line in text.splitlines() if "hello.txt" in line)
    checksums_path.write_text(text + duplicated_line + "\n", encoding="utf-8")
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_BUNDLE_CHECKSUMS_DUPLICATE") for code in result["reason_codes"])


def test_bundle_envelope_detects_manifest_metadata_digest_mismatch(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    metadata_path = bundle_root / "BUNDLE_METADATA.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["manifest_sha256"] = "0" * 64
    _write_json(metadata_path, metadata)
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL"
    assert "FAIL_BUNDLE_MANIFEST_DIGEST_MISMATCH" in result["reason_codes"]


def test_bundle_envelope_check_is_wired_into_the_report(tmp_path: Path) -> None:
    _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    args = argparse.Namespace(
        box_root=tmp_path,
        light_python=tmp_path / "does-not-exist-python",
        jax_python=None,
        contained_root=None,
        output=None,
        timeout_seconds=1.0,
        require_jax=False,
        skip_tests=True,
    )
    report = verifier.verify(args)
    assert "bundle_envelope" in report["checks"]
    assert report["checks"]["bundle_envelope"]["status"] == "PASS", report["checks"]["bundle_envelope"]


def test_bundle_envelope_not_applicable_for_this_source_checkout() -> None:
    box = Path(__file__).resolve().parents[2]
    result = verifier.check_bundle_envelope(box)
    expected = "PASS" if verifier.find_bundle_root(box) is not None else "NOT_APPLICABLE"
    assert result["status"] == expected


def test_bundle_envelope_is_found_from_extracted_box_root(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    box_root = bundle_root / "PROJECT" / "constraint_box"
    box_root.mkdir(parents=True)
    result = verifier.check_bundle_envelope(box_root)
    assert result["status"] == "PASS", result
    assert Path(result["bundle_root"]) == bundle_root


def test_bundle_envelope_detects_checksum_path_traversal(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    checksums_path = bundle_root / "SHA256SUMS"
    checksums_path.write_text(
        checksums_path.read_text(encoding="utf-8") + ("0" * 64) + f"  {TOP_LEVEL_NAME}/../escape.txt\n",
        encoding="utf-8",
    )
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_BUNDLE_CHECKSUMS_PATH_UNSAFE") for code in result["reason_codes"])


def test_check_context_rejects_unsafe_current_context_paths(tmp_path: Path) -> None:
    system_root = tmp_path / "integrated_system"
    (system_root / "context" / "full").mkdir(parents=True)
    (system_root / "context" / "current").mkdir(parents=True)
    (system_root / "state").mkdir(parents=True)
    _write_json(system_root / "context" / "full" / "CORPUS_MANIFEST.json", {"output_sha256": None, "output_bytes": None, "selected_event_count": 0})
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    genesis = {"context_projection": {"sha256": None}, "promotion_allowed": False, "current_context": {str(outside): "0" * 64}}
    _write_json(system_root / "state" / "GENESIS.json", genesis)
    result = verifier.check_context(system_root)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_CONTEXT_CURRENT_PATH_ABSOLUTE") for code in result["reason_codes"])

    genesis["current_context"] = {"../outside.txt": "0" * 64}
    _write_json(system_root / "state" / "GENESIS.json", genesis)
    result2 = verifier.check_context(system_root)
    assert result2["status"] == "FAIL"
    assert any(code.startswith("FAIL_CONTEXT_CURRENT_PATH_PARENT_TRAVERSAL") for code in result2["reason_codes"])


def test_check_skill_estate_rejects_unsafe_wave_definition_paths(tmp_path: Path) -> None:
    system_root = tmp_path / "integrated_system"
    skills_root = system_root / "skills"
    skills_root.mkdir(parents=True)
    (skills_root / "MANIFEST.txt").write_text("ok\n", encoding="utf-8")
    outside = tmp_path / "outside.json"
    _write_json(outside, {"promotion_allowed": False})
    active = {"wave_definitions": [str(outside)], "zip_wave_definition": "zip/definition.json"}
    _write_json(skills_root / "ACTIVE_WAVES.json", active)
    result = verifier.check_skill_estate(system_root)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_WAVE_DEFINITION_PATH_ABSOLUTE") for code in result["reason_codes"])

    active["wave_definitions"] = ["../outside.json"]
    _write_json(skills_root / "ACTIVE_WAVES.json", active)
    result2 = verifier.check_skill_estate(system_root)
    assert result2["status"] == "FAIL"
    assert any(code.startswith("FAIL_WAVE_DEFINITION_PATH_PARENT_TRAVERSAL") for code in result2["reason_codes"])


def test_check_structured_receipt_rejects_unsafe_paths(tmp_path: Path) -> None:
    system_root = tmp_path / "integrated_system"
    runs = system_root / "runs"
    runs.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    _write_json(outside, {"status": "PASS"})
    _write_json(runs / "dual.json", {"status": "PASS"})
    crosscheck = {"status": "PASS", "exact_jax_agreement": True, "exact": {"path": str(outside)}, "dual": {"path": "dual.json"}}
    _write_json(runs / "STRUCTURED_OPEN_BIND_CROSSCHECK.json", crosscheck)
    result = verifier.check_structured_receipt(system_root)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_STRUCTURED_RECEIPT_PATH_ABSOLUTE") for code in result["reason_codes"])

    crosscheck["exact"] = {"path": "../outside.json"}
    _write_json(runs / "STRUCTURED_OPEN_BIND_CROSSCHECK.json", crosscheck)
    result2 = verifier.check_structured_receipt(system_root)
    assert result2["status"] == "FAIL"
    assert any(code.startswith("FAIL_STRUCTURED_RECEIPT_PATH_PARENT_TRAVERSAL") for code in result2["reason_codes"])


def test_check_bridge_receipt_rejects_unsafe_paths(tmp_path: Path) -> None:
    system_root = tmp_path / "integrated_system"
    runs = system_root / "runs"
    runs.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    _write_json(outside, {"status": "PASS"})
    _write_json(runs / "b.json", {"status": "PASS"})
    replay = {"status": "PASS", "semantic_replay_identical": True, "runs": [{"path": str(outside)}, {"path": "b.json"}]}
    _write_json(runs / "LIGHT_JAX_WAVE_REPLAY.json", replay)
    result = verifier.check_bridge_receipt(system_root)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_BRIDGE_RECEIPT_PATH_ABSOLUTE") for code in result["reason_codes"])

    replay["runs"] = [{"path": "../outside.json"}, {"path": "b.json"}]
    _write_json(runs / "LIGHT_JAX_WAVE_REPLAY.json", replay)
    result2 = verifier.check_bridge_receipt(system_root)
    assert result2["status"] == "FAIL"
    assert any(code.startswith("FAIL_BRIDGE_RECEIPT_PATH_PARENT_TRAVERSAL") for code in result2["reason_codes"])


def test_live_operations_and_separation_flag_reflect_a_failed_doctor(tmp_path: Path) -> None:
    args = argparse.Namespace(
        box_root=tmp_path,
        light_python=Path(sys.executable),
        jax_python=None,
        contained_root=None,
        output=None,
        timeout_seconds=10.0,
        require_jax=False,
        skip_tests=True,
    )
    report = verifier.verify(args)
    doctor_record = next(row for row in report["commands"] if row["id"] == "doctor")
    assert doctor_record["status"] != "PASS"
    assert report["checks"]["live_operations"]["status"] != "PASS"
    assert report["interpreters"]["light_jax_separation_checked"] is False


def test_bundle_envelope_detects_checksum_digest_mismatch(tmp_path: Path) -> None:
    _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    checksums_path = tmp_path / TOP_LEVEL_NAME / "SHA256SUMS"
    rewritten = []
    for line in checksums_path.read_text(encoding="utf-8").splitlines():
        if line.endswith("hello.txt"):
            rewritten.append(("0" * 64) + line[64:])
        else:
            rewritten.append(line)
    checksums_path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL"
    assert any(code.startswith("FAIL_BUNDLE_CHECKSUMS_DIGEST_MISMATCH") for code in result["reason_codes"])
