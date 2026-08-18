from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

import pytest


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


def test_bridge_output_directory_is_product_confined_and_cleaned(
    tmp_path: Path,
) -> None:
    box_root = tmp_path / "constraint_box"
    system_root = box_root / "integrated_system"
    system_root.mkdir(parents=True)
    with verifier._bridge_output_directory(
        box_root=box_root, system_root=system_root
    ) as bridge_root:
        assert bridge_root.is_relative_to(box_root.resolve())
        assert bridge_root.parent == system_root / "runs"
        (bridge_root / "bridge-1").mkdir()
        (bridge_root / "bridge-1" / "argv.json").write_text(
            json.dumps({"output_dir": str(bridge_root / "bridge-1")}),
            encoding="utf-8",
        )
        assert bridge_root.exists()
    assert not bridge_root.exists()
    assert not (system_root / "runs").exists()


def test_bridge_output_directory_preserves_preexisting_runs_files(
    tmp_path: Path,
) -> None:
    box_root = tmp_path / "constraint_box"
    system_root = box_root / "integrated_system"
    runs_root = system_root / "runs"
    runs_root.mkdir(parents=True)
    sentinel = runs_root / "sentinel.json"
    sentinel.write_text("{}\n", encoding="utf-8")
    with verifier._bridge_output_directory(
        box_root=box_root, system_root=system_root
    ) as bridge_root:
        assert bridge_root.is_relative_to(box_root.resolve())
        assert bridge_root.parent == runs_root
    assert sentinel.read_text(encoding="utf-8") == "{}\n"
    assert not bridge_root.exists()


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
    assert context["epoch"]["status"] == "PASS"
    epoch_sequence = context["epoch"]["epoch_sequence"]
    assert epoch_sequence >= 1
    assert context["epoch"]["epoch_id"] == f"epoch-{epoch_sequence:08d}"
    if epoch_sequence > 1:
        assert context["epoch"]["epoch_parent"]["path"].endswith(
            f"epoch-{epoch_sequence - 1:08d}.json"
        )
    assert context["epoch"]["bound_current_context_count"] == 6
    assert context["epoch"]["epoch_verifier_sha256"] == verifier.sha256_file(
        system / "scripts" / "seal_context_epoch.py"
    )
    assert context["epoch"]["epoch_verifier_path"] == "scripts/seal_context_epoch.py"
    assert skills["status"] == "PASS", skills
    assert skills["active_wave_count"] == 3
    assert skills["wave_definition_count"] == 20
    assert skills["authored_specs_not_active_count"] == 10
    assert skills["unregistered_candidate_count"] == 7
    assert len(skills["catalog_sha256"]) == 64
    assert skills["catalog_source_sha256"]


def test_public_wave_catalog_truth_keeps_candidates_non_runnable() -> None:
    box = Path(__file__).resolve().parents[2]
    result = verifier.check_skill_estate(box / "integrated_system")
    assert result["status"] == "PASS", result
    assert set(result["runnable_wave_ids"]) == {
        "cb-maintenance-wave",
        "cb-context-strategy-wave",
        "cb-exploration-wave",
    }
    assert set(result["unregistered_candidates"]) == {
        "cb-capability-probe-map-wave",
        "cb-context-wave",
        "cb-formalization-digger-wave",
        "cb-objective-integrity-wave",
        "cb-strategy-checkpoint-wave",
        "cb-strategy-discriminator-wave",
        "cb-strategy-framing-wave",
    }


def test_retained_structured_and_bridge_receipts_are_checked_without_promotion() -> None:
    box = Path(__file__).resolve().parents[2]
    system = box / "integrated_system"
    structured = verifier.check_structured_receipt(system)
    bridge = verifier.check_bridge_receipt(system)
    if structured["status"] == "NOT_APPLICABLE":
        assert bridge["status"] == "NOT_APPLICABLE"
        return
    assert structured["status"] == "PASS", structured
    assert structured["exact_jax_agreement"] is True
    assert structured["crosscheck_projection_recomputed"] is False
    # The retained receipt predates this verifier's source changes.  It must
    # be labeled stale rather than silently treated as a current PASS.
    assert bridge["status"] in {"PASS", "STALE"}, bridge
    assert bridge["semantic_replay_identical"] is True
    if bridge["status"] == "STALE":
        assert bridge["stale_reason_codes"]


def test_structured_projection_excludes_engine_specific_fields() -> None:
    exact = {"schema": "s", "status": "PASS", "engine": "exact", "jax": {"ran": False}, "controls": {"x": True}}
    dual = {"schema": "s", "status": "PASS", "engine": "dual", "jax": {"ran": True}, "controls": {"x": True}}
    assert verifier.structured_projection(exact) == verifier.structured_projection(dual)


def test_test_groups_name_two_estate_wide_exclusions() -> None:
    ignores = verifier.test_groups()["curated_skills"]
    assert any("cb-wave-author/tests/test_wave_definitions.py" in value for value in ignores)
    assert any("cb-wave-admission-gate/tests/test_admit.py" in value for value in ignores)
    assert not any("cb-wave-self-loop/tests/test_score_estate.py" in value for value in ignores)


def test_integrated_system_group_runs_first_for_clean_envelope_self_test() -> None:
    groups = verifier.test_groups()
    assert next(iter(groups)) == "integrated_system"
    assert groups["integrated_system"] == ["constraint_box/integrated_system/tests"]


def test_default_verification_roster_is_model_free() -> None:
    assert "provider_adapters" not in verifier.test_groups()
    assert "provider_adapters" in verifier.test_groups(include_provider_adapters=True)


def test_jax_profile_is_static_and_explicitly_external() -> None:
    box = Path(__file__).resolve().parents[2]
    profile = verifier.check_jax_profile(box / "integrated_system")
    assert profile["status"] == "PASS", profile
    assert profile["runtime_probe_is_live"] is False


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
        "source_closure_sha256": hashlib.sha256(
            verifier.canonical_json_bytes(
                [
                    {
                        "path": row["path"],
                        "bytes": row["bytes"],
                        "sha256": row["sha256"],
                        "mode": row["mode"],
                    }
                    for row in rows
                ]
            )
        ).hexdigest(),
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
        "source_closure_sha256": manifest["source_closure_sha256"],
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


@pytest.mark.parametrize(
    "raw_path",
    (
        "./hello.txt",
        "hello//txt",
        "hello\\txt",
        "hello\x00txt",
        "hello.txt/",
        "../hello.txt",
        "/tmp/hello.txt",
        ".",
        "",
    ),
)
def test_bundle_manifest_rejects_noncanonical_raw_path_spelling(
    tmp_path: Path, raw_path: str
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    manifest_path = bundle_root / "SYSTEM_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["path"] = raw_path
    manifest_bytes = _write_json(manifest_path, manifest)
    metadata_path = bundle_root / "BUNDLE_METADATA.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    _write_json(metadata_path, metadata)
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL", (raw_path, result)
    assert any(
        code.startswith("FAIL_BUNDLE_MANIFEST_PATH_UNSAFE")
        for code in result["reason_codes"]
    )


@pytest.mark.parametrize(
    "raw_entry",
    (
        f"{TOP_LEVEL_NAME}/./hello.txt",
        f"{TOP_LEVEL_NAME}//hello.txt",
        f"{TOP_LEVEL_NAME}/hello\\txt",
        f"{TOP_LEVEL_NAME}/hello\x00txt",
        f"{TOP_LEVEL_NAME}/hello.txt/",
        f"{TOP_LEVEL_NAME}/../hello.txt",
        "/tmp/hello.txt",
        f"{TOP_LEVEL_NAME}/",
    ),
)
def test_bundle_checksums_reject_noncanonical_raw_path_spelling(
    tmp_path: Path, raw_entry: str
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    checksums_path = bundle_root / "SHA256SUMS"
    checksums_path.write_text(
        checksums_path.read_text(encoding="utf-8")
        + ("0" * 64)
        + f"  {raw_entry}\n",
        encoding="utf-8",
    )
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL", (raw_entry, result)
    assert any(
        code.startswith("FAIL_BUNDLE_CHECKSUMS_PATH_UNSAFE")
        for code in result["reason_codes"]
    )


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


@pytest.mark.parametrize(
    ("filename", "reason"),
    (
        ("SYSTEM_MANIFEST.json", "FAIL_BUNDLE_MANIFEST_SYMLINK"),
        ("BUNDLE_METADATA.json", "FAIL_BUNDLE_METADATA_SYMLINK"),
        ("SHA256SUMS", "FAIL_BUNDLE_CHECKSUMS_SYMLINK"),
    ),
)
def test_bundle_envelope_rejects_symlinked_envelope_files(
    tmp_path: Path, filename: str, reason: str
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    outside = tmp_path / f"external-{filename}"
    outside.write_bytes((bundle_root / filename).read_bytes())
    (bundle_root / filename).unlink()
    (bundle_root / filename).symlink_to(outside)
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL", result
    assert reason in result["reason_codes"]


def test_bundle_envelope_rejects_unlisted_physical_file(tmp_path: Path) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    (bundle_root / "unlisted-extra.bin").write_bytes(b"not in the closure\n")
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL", result
    assert "FAIL_BUNDLE_CHECKSUMS_MISSING_PHYSICAL:unlisted-extra.bin" in result[
        "reason_codes"
    ]


def test_bundle_envelope_rejects_preexisting_source_bytecode_cache(
    tmp_path: Path,
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    cache = bundle_root / "PROJECT" / "constraint_box" / "source" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.cpython-313.pyc").write_bytes(b"preexisting\n")

    result = verifier.check_bundle_envelope(tmp_path)

    assert result["status"] == "FAIL", result
    assert any(
        code.startswith("FAIL_BUNDLE_UNLISTED_CACHE_DIRECTORY")
        for code in result["reason_codes"]
    ), result


def test_generated_pure_bytecode_is_cleaned_and_post_envelope_passes(
    tmp_path: Path,
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    initial = verifier.check_bundle_envelope(tmp_path)
    assert initial["status"] == "PASS", initial
    cache = bundle_root / "PROJECT" / "constraint_box" / "source" / "__pycache__"
    cache.mkdir(parents=True)
    bytecode = cache / "module.cpython-313.pyc"
    bytecode.write_bytes(b"generated\n")
    expected_digest = verifier.sha256_file(bytecode)

    cleanup = verifier.cleanup_generated_bytecode(tmp_path, initial)
    post = verifier.check_bundle_envelope(tmp_path)

    relative = "PROJECT/constraint_box/source/__pycache__/module.cpython-313.pyc"
    assert cleanup["status"] == "PASS", cleanup
    assert cleanup["count"] == 1
    assert cleanup["paths"] == [relative]
    assert cleanup["digests"] == {relative: expected_digest}
    assert not bytecode.exists()
    assert not cache.exists()
    assert post["status"] == "PASS", post


def test_generated_foreign_bytecode_cache_entry_refuses_cleanup(
    tmp_path: Path,
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    initial = verifier.check_bundle_envelope(tmp_path)
    assert initial["status"] == "PASS", initial
    cache = bundle_root / "PROJECT" / "constraint_box" / "source" / "__pycache__"
    cache.mkdir(parents=True)
    foreign = cache / "module.py"
    foreign.write_text("not bytecode\n", encoding="utf-8")

    cleanup = verifier.cleanup_generated_bytecode(tmp_path, initial)
    post = verifier.check_bundle_envelope(tmp_path)

    assert cleanup["status"] == "FAIL", cleanup
    assert any(
        code.startswith("FAIL_GENERATED_BYTECODE_FOREIGN_ENTRY")
        for code in cleanup["reason_codes"]
    ), cleanup
    assert foreign.exists()
    assert post["status"] == "FAIL", post


def test_generated_symlink_bytecode_cache_entry_refuses_cleanup(
    tmp_path: Path,
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    initial = verifier.check_bundle_envelope(tmp_path)
    assert initial["status"] == "PASS", initial
    cache = bundle_root / "PROJECT" / "constraint_box" / "source" / "__pycache__"
    cache.mkdir(parents=True)
    outside = tmp_path / "outside.pyc"
    outside.write_bytes(b"outside\n")
    linked = cache / "module.cpython-313.pyc"
    linked.symlink_to(outside)

    cleanup = verifier.cleanup_generated_bytecode(tmp_path, initial)
    post = verifier.check_bundle_envelope(tmp_path)

    assert cleanup["status"] == "FAIL", cleanup
    assert any(
        code.startswith("FAIL_GENERATED_BYTECODE_SYMLINK")
        for code in cleanup["reason_codes"]
    ), cleanup
    assert linked.is_symlink()
    assert post["status"] == "FAIL", post


def test_manifest_source_mutation_still_fails_post_envelope(
    tmp_path: Path,
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    initial = verifier.check_bundle_envelope(tmp_path)
    assert initial["status"] == "PASS", initial
    (bundle_root / "hello.txt").write_bytes(b"source changed\n")

    cleanup = verifier.cleanup_generated_bytecode(tmp_path, initial)
    post = verifier.check_bundle_envelope(tmp_path)

    assert cleanup["status"] == "PASS", cleanup
    assert post["status"] == "FAIL", post
    assert any(
        code.startswith("FAIL_BUNDLE_PAYLOAD_DIGEST_MISMATCH:hello.txt")
        for code in post["reason_codes"]
    ), post


def test_bundle_envelope_ignores_exact_product_runtime_roots_with_venv_symlink(
    tmp_path: Path,
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    product_root = bundle_root / "PROJECT" / "constraint_box"
    runtime_roots = (
        product_root / ".venv",
        product_root / ".venv-clean",
        product_root / ".bootstrap-light-build",
        product_root / "integrated_system" / "runs",
        product_root / "receipts",
    )
    for runtime_root in runtime_roots:
        runtime_root.mkdir(parents=True)
        (runtime_root / "generated.bin").write_bytes(b"generated\n")
    python_link = product_root / ".venv" / "bin" / "python"
    python_link.parent.mkdir()
    python_link.symlink_to(sys.executable)

    result = verifier.check_bundle_envelope(tmp_path)

    assert result["status"] == "PASS", result
    assert result["reason_codes"] == []


@pytest.mark.parametrize(
    "relative",
    verifier._GENERATED_RUNTIME_ROOTS,
)
def test_bundle_envelope_rejects_symlinked_product_runtime_root(
    tmp_path: Path, relative: str
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    runtime_root = bundle_root.joinpath(*Path(relative).parts)
    runtime_root.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / f"outside-{runtime_root.name}"
    outside.mkdir()
    runtime_root.symlink_to(outside, target_is_directory=True)

    result = verifier.check_bundle_envelope(tmp_path)

    assert result["status"] == "FAIL", result
    assert f"FAIL_BUNDLE_RUNTIME_ROOT_SYMLINK:{relative}" in result[
        "reason_codes"
    ]


@pytest.mark.parametrize(
    "relative",
    (
        *verifier._GENERATED_RUNTIME_ROOTS,
        "PROJECT/constraint_box/.venv-lookalike",
        "PROJECT/.venv",
    ),
)
def test_bundle_envelope_rejects_runtime_root_or_lookalike_file(
    tmp_path: Path, relative: str
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    candidate = bundle_root.joinpath(*Path(relative).parts)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes(b"not a generated runtime directory\n")

    result = verifier.check_bundle_envelope(tmp_path)

    assert result["status"] == "FAIL", result
    if relative in verifier._GENERATED_RUNTIME_ROOTS:
        assert f"FAIL_BUNDLE_RUNTIME_ROOT_NOT_DIRECTORY:{relative}" in result[
            "reason_codes"
        ]
    else:
        assert any(
            code.startswith("FAIL_BUNDLE_CHECKSUMS_MISSING_PHYSICAL")
            for code in result["reason_codes"]
        ), result


@pytest.mark.parametrize(
    "relative",
    (
        "PROJECT/constraint_box/.venv-lookalike",
        "PROJECT/constraint_box/integrated_system/.venv",
        "PROJECT/.venv",
    ),
)
def test_bundle_envelope_rejects_lookalike_or_elsewhere_runtime_symlink(
    tmp_path: Path, relative: str
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    candidate = bundle_root.joinpath(*Path(relative).parts)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / f"outside-{candidate.name}"
    outside.mkdir()
    candidate.symlink_to(outside, target_is_directory=True)

    result = verifier.check_bundle_envelope(tmp_path)

    assert result["status"] == "FAIL", result
    assert any(
        code.startswith("FAIL_BUNDLE_SYMLINK_DIRECTORY")
        for code in result["reason_codes"]
    ), result


def test_bundle_envelope_rejects_symlinked_payload_even_when_inside_root(
    tmp_path: Path,
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    target = bundle_root / "hello.txt"
    target.unlink()
    target.symlink_to(tmp_path / "outside-payload.txt")
    (tmp_path / "outside-payload.txt").write_bytes(b"outside\n")
    result = verifier.check_bundle_envelope(tmp_path)
    assert result["status"] == "FAIL", result
    assert any(
        code.startswith("FAIL_BUNDLE_SYMLINK_FILE:hello.txt")
        for code in result["reason_codes"]
    )


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
    assert report["checks"]["generated_bytecode_cleanup"]["status"] == "PASS", report["checks"]["generated_bytecode_cleanup"]
    assert report["checks"]["bundle_envelope_post"]["status"] == "PASS", report["checks"]["bundle_envelope_post"]


def _stub_verify_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep post-envelope report tests focused on file-custody behavior."""

    monkeypatch.setattr(
        verifier,
        "run_zip_demo",
        lambda **kwargs: {"status": "PASS", "reason_codes": []},
    )
    monkeypatch.setattr(
        verifier,
        "run_structured_probe",
        lambda **kwargs: {"status": "PASS", "reason_codes": []},
    )
    monkeypatch.setattr(
        verifier,
        "run_bridge_pair",
        lambda **kwargs: {"status": "PASS", "reason_codes": []},
    )
    monkeypatch.setattr(
        verifier,
        "run_contained_overlay",
        lambda **kwargs: {"status": "NOT_APPLICABLE", "reason_codes": []},
    )


def _verify_bundle_args(root: Path) -> argparse.Namespace:
    return argparse.Namespace(
        box_root=root,
        light_python=Path(sys.executable),
        jax_python=None,
        contained_root=None,
        output=None,
        timeout_seconds=1.0,
        require_jax=False,
        skip_tests=True,
    )


def test_verify_post_envelope_rejects_cache_or_extra_file_created_by_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    _stub_verify_commands(monkeypatch)
    monkeypatch.setattr(
        verifier,
        "find_interpreter",
        lambda value, fallback: Path(sys.executable),
    )
    mutated = False

    def fake_add_command(records, command_id, argv, **kwargs):
        nonlocal mutated
        if not mutated:
            cache = bundle_root / "PROJECT" / "constraint_box" / "postrun-cache"
            cache.mkdir(parents=True)
            (cache / "generated.pyc").write_bytes(b"cache\n")
            mutated = True
        record = {"id": command_id, "status": "PASS"}
        records.append(record)
        return record

    monkeypatch.setattr(verifier, "add_command", fake_add_command)

    report = verifier.verify(_verify_bundle_args(tmp_path))

    assert report["checks"]["bundle_envelope"]["status"] == "PASS"
    post = report["checks"]["bundle_envelope_post"]
    assert post["status"] == "FAIL", post
    assert any(
        code.startswith("FAIL_BUNDLE_CHECKSUMS_MISSING_PHYSICAL")
        for code in post["reason_codes"]
    ), post
    assert report["status"] == "FAIL"


def test_verify_records_and_cleans_generated_bytecode_before_postcheck(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    _stub_verify_commands(monkeypatch)
    monkeypatch.setattr(
        verifier,
        "find_interpreter",
        lambda value, fallback: Path(sys.executable),
    )
    created = False

    def fake_add_command(records, command_id, argv, **kwargs):
        nonlocal created
        if not created:
            cache = bundle_root / "PROJECT" / "constraint_box" / "source" / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "module.cpython-313.pyc").write_bytes(b"generated\n")
            created = True
        record = {"id": command_id, "status": "PASS"}
        records.append(record)
        return record

    monkeypatch.setattr(verifier, "add_command", fake_add_command)

    report = verifier.verify(_verify_bundle_args(tmp_path))

    cleanup = report["checks"]["generated_bytecode_cleanup"]
    assert cleanup["status"] == "PASS", cleanup
    assert cleanup["count"] == 1
    assert cleanup["paths"] == [
        "PROJECT/constraint_box/source/__pycache__/module.cpython-313.pyc"
    ]
    assert report["checks"]["bundle_envelope_post"]["status"] == "PASS", report["checks"]["bundle_envelope_post"]


def test_verify_post_envelope_allows_generated_receipts_environment_and_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle_root = _build_bundle(tmp_path, {"hello.txt": b"hello world\n"})
    _stub_verify_commands(monkeypatch)
    monkeypatch.setattr(
        verifier,
        "find_interpreter",
        lambda value, fallback: Path(sys.executable),
    )
    created = False

    def fake_add_command(records, command_id, argv, **kwargs):
        nonlocal created
        if not created:
            for relative in verifier._GENERATED_RUNTIME_ROOTS:
                root = bundle_root.joinpath(*Path(relative).parts)
                root.mkdir(parents=True)
                (root / "generated.bin").write_bytes(b"generated\n")
            created = True
        record = {"id": command_id, "status": "PASS"}
        records.append(record)
        return record

    monkeypatch.setattr(verifier, "add_command", fake_add_command)

    report = verifier.verify(_verify_bundle_args(tmp_path))

    assert report["checks"]["bundle_envelope"]["status"] == "PASS"
    assert report["checks"]["bundle_envelope_post"]["status"] == "PASS", report["checks"]["bundle_envelope_post"]


def test_light_core_pytest_isolation_disables_bytecode_and_host_imports(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    box_root = tmp_path / "constraint_box"
    test_path = box_root / "tests" / "test_light_core.py"
    test_path.parent.mkdir(parents=True)
    test_path.write_text("def test_ok(): pass\n", encoding="utf-8")
    captured: list[list[str]] = []

    def fake_add_command(records, command_id, argv, **kwargs):
        captured.append(argv)
        record = {"id": command_id, "status": "PASS"}
        records.append(record)
        return record

    monkeypatch.setattr(verifier, "add_command", fake_add_command)
    monkeypatch.setattr(
        verifier,
        "test_groups",
        lambda include_provider_adapters=False: {
            "light_core": ["constraint_box/tests/test_light_core.py"]
        },
    )

    results = verifier.run_test_groups(
        light_python=Path(sys.executable),
        repo_root=tmp_path,
        env={"CB_BOX_ROOT": str(box_root)},
        timeout_seconds=1.0,
        records=[],
    )

    assert results["light_core"]["status"] == "PASS"
    assert captured[0][1:3] == ["-B", "-I"]


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


def test_check_context_requires_current_epoch_chain(tmp_path: Path) -> None:
    system_root = tmp_path / "integrated_system"
    (system_root / "context" / "full").mkdir(parents=True)
    (system_root / "context" / "current").mkdir(parents=True)
    (system_root / "state").mkdir(parents=True)
    _write_json(system_root / "context" / "full" / "CORPUS_MANIFEST.json", {"output_sha256": None, "output_bytes": None, "selected_event_count": 0})
    result = verifier.check_context(system_root)
    assert result["status"] == "FAIL"
    assert "FAIL_CONTEXT_CURRENT_EPOCH_MISSING" in result["reason_codes"]


def test_check_context_rejects_drift_in_an_epoch_bound_file(tmp_path: Path) -> None:
    source_box = Path(__file__).resolve().parents[2]
    source_system = source_box / "integrated_system"
    copied_box = tmp_path / "constraint_box"
    copied_system = copied_box / "integrated_system"
    shutil.copytree(source_system / "context", copied_system / "context")
    shutil.copytree(source_system / "state", copied_system / "state")
    (copied_system / "scripts").mkdir(parents=True)
    shutil.copy2(
        source_system / "scripts" / "seal_context_epoch.py",
        copied_system / "scripts" / "seal_context_epoch.py",
    )
    (copied_system / "context" / "current" / "CURRENT_PLAN.md").write_text(
        "drifted after epoch capture\n", encoding="utf-8"
    )
    result = verifier.check_context(copied_system)
    assert result["status"] == "FAIL", result
    assert any(
        "FAIL_CONTEXT_EPOCH:EpochRefusal:REFUSE_BOUND_FILE_SHA256_MISMATCH" in code
        for code in result["reason_codes"]
    )


def test_check_context_rejects_symlinked_epoch_verifier_before_execution(
    tmp_path: Path,
) -> None:
    source_box = Path(__file__).resolve().parents[2]
    source_system = source_box / "integrated_system"
    copied_system = tmp_path / "constraint_box" / "integrated_system"
    shutil.copytree(source_system / "context", copied_system / "context")
    shutil.copytree(source_system / "state", copied_system / "state")
    (copied_system / "scripts").mkdir(parents=True)
    external = tmp_path / "external-seal-context-epoch.py"
    external.write_text(
        "(Path('EXECUTED').write_text('bad'))\n", encoding="utf-8"
    )
    (copied_system / "scripts" / "seal_context_epoch.py").symlink_to(external)
    result = verifier.check_context(copied_system)
    assert result["status"] == "FAIL", result
    assert any(
        "REFUSE_EPOCH_VERIFIER_SYMLINK" in code for code in result["reason_codes"]
    )
    assert not (tmp_path / "EXECUTED").exists()


def test_check_context_rejects_external_epoch_verifier_directory(
    tmp_path: Path,
) -> None:
    source_box = Path(__file__).resolve().parents[2]
    source_system = source_box / "integrated_system"
    copied_system = tmp_path / "constraint_box" / "integrated_system"
    shutil.copytree(source_system / "context", copied_system / "context")
    shutil.copytree(source_system / "state", copied_system / "state")
    external_scripts = tmp_path / "external-scripts"
    external_scripts.mkdir()
    shutil.copy2(
        source_system / "scripts" / "seal_context_epoch.py",
        external_scripts / "seal_context_epoch.py",
    )
    (copied_system / "scripts").symlink_to(external_scripts, target_is_directory=True)
    result = verifier.check_context(copied_system)
    assert result["status"] == "FAIL", result
    assert any(
        "REFUSE_EPOCH_VERIFIER_SCRIPTS_SYMLINK" in code
        for code in result["reason_codes"]
    )


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


def test_check_skill_estate_rejects_noncanonical_authority_path_spelling(
    tmp_path: Path,
) -> None:
    system_root = tmp_path / "integrated_system"
    skills_root = system_root / "skills"
    skills_root.mkdir(parents=True)
    (skills_root / "MANIFEST.txt").write_text("ok\n", encoding="utf-8")
    _write_json(skills_root / "definition.json", {"promotion_allowed": False})
    for malformed in (
        "./definition.json",
        "definition//json",
        "definition\\json",
        "",
    ):
        _write_json(
            skills_root / "ACTIVE_WAVES.json",
            {
                "wave_definitions": [malformed],
                "zip_wave_definition": "definition.json",
            },
        )
        result = verifier.check_skill_estate(system_root)
        assert result["status"] == "FAIL", (malformed, result)


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
    assert any(code.startswith("STALE_STRUCTURED_RECEIPT_PATH_ABSOLUTE") for code in result["reason_codes"])

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
    assert any(code.startswith("STALE_BRIDGE_RECEIPT_PATH_ABSOLUTE") for code in result["reason_codes"])

    replay["runs"] = [{"path": "../outside.json"}, {"path": "b.json"}]
    _write_json(runs / "LIGHT_JAX_WAVE_REPLAY.json", replay)
    result2 = verifier.check_bridge_receipt(system_root)
    assert result2["status"] == "FAIL"
    assert any(code.startswith("FAIL_BRIDGE_RECEIPT_PATH_PARENT_TRAVERSAL") for code in result2["reason_codes"])


def test_check_bridge_receipt_labels_source_binding_drift_stale(tmp_path: Path) -> None:
    system_root = tmp_path / "integrated_system"
    runs = system_root / "runs"
    source_root = system_root.parent
    runs.mkdir(parents=True)
    # The retained receipt is structurally valid but deliberately names a
    # digest that no longer matches the current source.  This is stale
    # evidence, not a fresh PASS and not a structural receipt failure.
    current = {
        "bridge_source_sha256": system_root / "scripts" / "run_light_jax_wave_bridge.py",
        "field_source_sha256": source_root / "scripts" / "contained_light" / "entropic_time_field.py",
        "seed_source_sha256": source_root / "scripts" / "contained_light" / "seed_check.py",
        "fixture_sha256": source_root / "scripts" / "contained_light" / "fixtures" / "entropic_time_field_v1.json",
        "campaign_source_sha256": source_root / "experiments" / "manifold_capability" / "v1" / "campaign.py",
        "campaign_custody_sha256": source_root / "experiments" / "manifold_capability" / "v1" / "REPLAY_CUSTODY.json",
    }
    for path in current.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("source\n", encoding="utf-8")
    children = {name: {"returncode": 0} for name in verifier.BRIDGE_CHILD_NAMES}
    receipt = {
        "status": "PASS",
        "promotion_allowed": False,
        "children": children,
        "bindings": {name: "0" * 64 for name in current},
        "replay_projection": {"stable": True},
    }
    receipt["replay_projection_sha256"] = verifier.sha256_bytes(
        verifier.canonical_json_bytes(receipt["replay_projection"])
    )
    receipt["receipt_sha256"] = verifier.digest_without(receipt, "receipt_sha256")
    receipt_path = runs / "a" / "bridge_receipt.json"
    receipt_path.parent.mkdir(parents=True)
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    replay = {
        "status": "PASS",
        "semantic_replay_identical": True,
        "runs": [
            {
                "path": "a/bridge_receipt.json",
                "file_sha256": verifier.sha256_file(receipt_path),
                "replay_projection_sha256": verifier.sha256_bytes(
                    verifier.canonical_json_bytes({"stable": True})
                ),
            },
            {
                "path": "a/bridge_receipt.json",
                "file_sha256": verifier.sha256_file(receipt_path),
                "replay_projection_sha256": verifier.sha256_bytes(
                    verifier.canonical_json_bytes({"stable": True})
                ),
            },
        ],
    }
    # Two identical rows are intentionally used only to exercise stale
    # classification; path duplication is a separate structural refusal.
    replay["runs"][1]["path"] = "a/bridge_receipt-copy.json"
    copy_path = runs / "a" / "bridge_receipt-copy.json"
    copy_path.write_text(json.dumps(receipt), encoding="utf-8")
    replay["runs"][1]["file_sha256"] = verifier.sha256_file(copy_path)
    _write_json(runs / "LIGHT_JAX_WAVE_REPLAY.json", replay)
    result = verifier.check_bridge_receipt(system_root)
    assert result["status"] == "STALE", result
    assert any(code.startswith("STALE_BRIDGE_SOURCE_BINDING") for code in result["reason_codes"])


def test_check_bridge_receipt_rejects_nonzero_child_even_when_receipt_says_pass(tmp_path: Path) -> None:
    system_root = tmp_path / "integrated_system"
    runs = system_root / "runs"
    runs.mkdir(parents=True)
    receipt = {
        "status": "PASS",
        "promotion_allowed": False,
        "children": {
            name: {"returncode": 7 if name == "etf_dual" else 0}
            for name in verifier.BRIDGE_CHILD_NAMES
        },
        "bindings": {},
        "replay_projection": {},
    }
    receipt["replay_projection_sha256"] = verifier.sha256_bytes(
        verifier.canonical_json_bytes(receipt["replay_projection"])
    )
    receipt["receipt_sha256"] = verifier.digest_without(receipt, "receipt_sha256")
    path = runs / "a.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    _write_json(
        runs / "LIGHT_JAX_WAVE_REPLAY.json",
        {
            "status": "PASS",
            "semantic_replay_identical": True,
            "runs": [
                {"path": "a.json", "file_sha256": verifier.sha256_file(path), "replay_projection_sha256": verifier.sha256_bytes(verifier.canonical_json_bytes({}))},
                {"path": "a.json.copy", "file_sha256": verifier.sha256_file(path), "replay_projection_sha256": verifier.sha256_bytes(verifier.canonical_json_bytes({}))},
            ],
        },
    )
    (runs / "a.json.copy").write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    result = verifier.check_bridge_receipt(system_root)
    assert result["status"] == "FAIL", result
    assert any(code.startswith("FAIL_BRIDGE_CHILD_RETURNCODE") for code in result["reason_codes"])


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
