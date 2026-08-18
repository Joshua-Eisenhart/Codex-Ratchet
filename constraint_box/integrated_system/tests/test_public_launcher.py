from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path
import json
import shutil


LAUNCHER = Path(__file__).resolve().parents[1] / "bin" / "cb"
SPEC = importlib.util.spec_from_loader(
    "integrated_cb_launcher", SourceFileLoader("integrated_cb_launcher", str(LAUNCHER))
)
assert SPEC is not None and SPEC.loader is not None
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


def _catalog_fixture(tmp_path: Path) -> tuple[Path, Path]:
    source_system = LAUNCHER.parents[1]
    system = tmp_path / "integrated_system"
    skills = system / "skills"
    trusted = skills / "cb-wave-author" / "scripts"
    trusted.mkdir(parents=True)
    shutil.copy2(
        source_system / "skills" / "cb-wave-author" / "scripts" / "validate_wave.py",
        trusted / "validate_wave.py",
    )
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps(
            {
                "schema": "constraintbox.active-wave-set.v1",
                "wave_definitions": [],
                "runnable_cohort": [],
            }
        ),
        encoding="utf-8",
    )
    return system, skills


def _copy_candidate(skills: Path, name: str) -> Path:
    source_system = LAUNCHER.parents[1]
    destination = skills / name
    shutil.copytree(
        source_system / "skills" / "cb-capability-probe-map-wave", destination
    )
    return destination


def _three_active_fixture(tmp_path: Path) -> tuple[Path, Path, dict]:
    source_system = LAUNCHER.parents[1]
    system, skills = _catalog_fixture(tmp_path)
    source_manifest = json.loads(
        (source_system / "skills" / "ACTIVE_WAVES.json").read_text(encoding="utf-8")
    )
    rows = []
    for source_row in source_manifest["runnable_cohort"]:
        wave_id = source_row["wave_id"]
        source_dir = source_system / "skills" / wave_id
        shutil.copytree(source_dir, skills / wave_id)
        definition = skills / wave_id / "wave.json"
        script_key = source_row["script"]
        script = system / script_key
        skill = skills / wave_id / "SKILL.md"
        row = dict(source_row)
        row["definition"] = f"skills/{wave_id}/wave.json"
        row["script"] = script_key
        row["skill"] = f"skills/{wave_id}/SKILL.md"
        row["definition_sha256"] = launcher.sha256_file(definition)
        row["script_sha256"] = launcher.sha256_file(script)
        row["skill_sha256"] = launcher.sha256_file(skill)
        rows.append(row)
    manifest = {
        "schema": "constraintbox.active-wave-set.v1",
        "wave_definitions": [
            f"skills/{row['wave_id']}/wave.json" for row in rows
        ],
        "runnable_cohort": rows,
    }
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    return system, skills, manifest


def test_bootstrap_refuses_incomplete_box_before_install(tmp_path: Path) -> None:
    assert launcher.bootstrap_light(tmp_path) == 2


def test_launcher_exposes_bootstrap_before_light_resolution() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert 'sub.add_parser("bootstrap-light")' in source
    assert source.index('if args.command == "bootstrap-light"') < source.index(
        "light = declared_python"
    )
    assert '"jax-profile"' in source
    assert source.index('if args.command == "jax-profile"') < source.index(
        "light = declared_python"
    )
    assert '"PYTHONPATH": str(box / "light_runtime" / "src")' in source
    assert '"CB_LIGHT_BUILD_INTERPRETER": str(builder_python)' in source


def test_source_runtime_never_places_mixed_root_package_on_pythonpath(tmp_path: Path) -> None:
    box = tmp_path / "constraint_box"
    system = box / "integrated_system"
    light = box / ".venv" / "bin" / "python"
    env = launcher.runtime_env(box, system, light)
    roots = env["PYTHONPATH"].split(launcher.os.pathsep)
    assert str(box / "src") not in roots
    assert roots == [str(box / "zip_agent" / "src"), str(box / "light_runtime" / "src")]
    assert env["CB_MMM_PACKS_ROOT"] == str(box / "mmm" / "packs")


def test_bundle_runtime_uses_merged_controller_and_zip_agent_roots(tmp_path: Path) -> None:
    box = tmp_path / "PROJECT" / "constraint_box"
    system = box / "integrated_system"
    controller = system / "runtime" / "controller_src"
    zip_runtime = system / "runtime" / "zip_agent_src"
    controller.mkdir(parents=True)
    zip_runtime.mkdir(parents=True)
    light = box / ".venv" / "bin" / "python"
    roots = launcher.runtime_env(box, system, light)["PYTHONPATH"].split(launcher.os.pathsep)
    assert roots == [str(zip_runtime), str(controller)]


def test_runtime_binds_separate_build_interpreter_when_present(tmp_path: Path) -> None:
    box = tmp_path / "constraint_box"
    system = box / "integrated_system"
    build_python = box / ".bootstrap-light-build" / "bin" / "python"
    build_python.parent.mkdir(parents=True)
    build_python.write_text("", encoding="utf-8")
    env = launcher.runtime_env(box, system, box / ".venv/bin/python")
    assert env["CB_LIGHT_BUILD_INTERPRETER"] == str(build_python)


def test_jax_version_profile_is_explicit() -> None:
    assert launcher.supported_jax_version("0.10.1") is True
    assert launcher.supported_jax_version("0.10.9") is True
    assert launcher.supported_jax_version("0.11.0") is False
    assert launcher.supported_jax_version("unknown") is False


def test_default_jax_route_is_project_neutral(tmp_path: Path, monkeypatch) -> None:
    data = tmp_path / "data"
    python = data / "jax-qit-stack" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("#!/bin/sh\n", encoding="utf-8")
    python.chmod(0o755)
    monkeypatch.setenv("XDG_DATA_HOME", str(data))
    monkeypatch.delenv("CB_JAX_QIT_ROOT", raising=False)
    assert launcher.default_jax_python() == python


def test_public_wave_surface_is_exposed_without_provider_policy() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert 'sub.add_parser("wave"' in source
    assert 'scripts/run_wave.py' in source
    assert "grok-4" not in source
    assert "claude-" not in source


def test_wave_catalog_exposes_reviewed_candidates_without_activation() -> None:
    system = LAUNCHER.parents[1]
    listing = launcher.discover_wave_catalog(system)
    rows = {row["wave_id"]: row for row in listing["waves"]}
    inactive_ids = {row["wave_id"] for row in listing["inactive"]}
    for wave_id in (
        "cb-capability-probe-map-wave",
        "cb-formalization-digger-wave",
    ):
        row = rows[wave_id]
        assert wave_id in inactive_ids
        assert row["classification"] == "UNREGISTERED_CANDIDATE"
        assert row["disposition"] == "UNREGISTERED_CANDIDATE"
        assert row["runnable"] is False
        assert row["promotion_allowed"] is False
        assert row["definition_sha256"]
        assert row["source_sha256"]
        assert row["validation"]["validator_available"] is True
        assert row["validation"]["errors"] == []


def test_candidate_source_and_flags_are_recomputed_not_admitted_from_definition(
    tmp_path: Path,
) -> None:
    system, skills = _catalog_fixture(tmp_path)
    candidate = _copy_candidate(skills, "forged-candidate")
    definition = json.loads((candidate / "wave.json").read_text(encoding="utf-8"))
    definition["source_sha256"] = "f" * 64
    definition["activated"] = True
    definition["promotion_allowed"] = True
    (candidate / "wave.json").write_text(json.dumps(definition), encoding="utf-8")

    listing = launcher.discover_wave_catalog(system)
    row = next(row for row in listing["waves"] if row["wave_id"] == "forged-candidate")
    assert row["definition_wave_id"] == definition["wave_id"]
    assert row["definition_sha256"] == launcher.sha256_file(candidate / "wave.json")
    assert row["source_sha256"] == launcher._sha256_tree(candidate)
    assert row["source_sha256"] != "f" * 64
    assert row["skill"] == "skills/forged-candidate/SKILL.md"
    assert row["skill_sha256"] == launcher.sha256_file(candidate / "SKILL.md")
    assert row["activated"] is False
    assert row["activation_observed"] is True
    assert row["promotion_allowed"] is False
    assert row["runnable"] is False


def test_wave_catalog_keeps_missing_child_and_invalid_json_findings_distinct(
    tmp_path: Path,
) -> None:
    source_system = LAUNCHER.parents[1]
    system = tmp_path / "integrated_system"
    skills = system / "skills"
    (skills / "cb-wave-author" / "scripts").mkdir(parents=True)
    shutil.copy2(
        source_system / "skills" / "cb-wave-author" / "scripts" / "validate_wave.py",
        skills / "cb-wave-author" / "scripts" / "validate_wave.py",
    )
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps(
            {
                "schema": "constraintbox.active-wave-set.v1",
                "wave_definitions": [],
                "runnable_cohort": [],
            }
        ),
        encoding="utf-8",
    )
    missing = skills / "reviewed-missing-wave"
    missing.mkdir()
    definition = json.loads(
        (
            source_system
            / "skills"
            / "cb-authority-collapse-wave"
            / "wave.json"
        ).read_text(encoding="utf-8")
    )
    definition["wave_id"] = "reviewed-missing-wave-v1"
    definition["children"][0]["skill"] = "does-not-exist"
    (missing / "wave.json").write_text(json.dumps(definition), encoding="utf-8")
    invalid = skills / "reviewed-invalid-wave"
    invalid.mkdir()
    (invalid / "wave.json").write_text("{not-json\n", encoding="utf-8")

    listing = launcher.discover_wave_catalog(system)
    rows = {row["wave_id"]: row for row in listing["waves"]}
    assert rows["reviewed-missing-wave"]["reason_code"] == "MISSING_CHILD_SKILL"
    assert any(
        value == "missing_child_skill:does-not-exist"
        for value in rows["reviewed-missing-wave"]["validation_findings"]
    )
    assert rows["reviewed-invalid-wave"]["reason_code"] == "INVALID_JSON"
    assert rows["reviewed-invalid-wave"]["validation"]["parse_error"]["code"] == (
        "INVALID_JSON"
    )
    assert not any(
        value.startswith("missing_child_skill:")
        for value in rows["reviewed-invalid-wave"]["validation_findings"]
    )


def test_wave_catalog_rejects_symlinked_skill_paths_without_emitting_outside_paths(
    tmp_path: Path,
) -> None:
    system, skills = _catalog_fixture(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "wave.json").write_text("{}\n", encoding="utf-8")
    (outside / "run.py").write_text("raise SystemExit(99)\n", encoding="utf-8")

    symlink_dir = skills / "symlinked-skill-dir"
    symlink_dir.symlink_to(outside, target_is_directory=True)
    symlink_file_dir = skills / "symlinked-definition"
    symlink_file_dir.mkdir()
    (symlink_file_dir / "wave.json").symlink_to(outside / "wave.json")
    symlink_scripts = _copy_candidate(skills, "symlinked-scripts")
    shutil.rmtree(symlink_scripts / "scripts")
    (symlink_scripts / "scripts").symlink_to(outside, target_is_directory=True)

    listing = launcher.discover_wave_catalog(system)
    serialized = json.dumps(listing, sort_keys=True)
    assert str(outside) not in serialized
    omitted = {row["wave_id"] for row in listing["omitted"]}
    assert "symlinked-skill-dir" in omitted
    assert "symlinked-definition" in omitted
    row = next(row for row in listing["waves"] if row["wave_id"] == "symlinked-scripts")
    assert row["runnable"] is False
    assert row["reason_code"] == "SYMLINKED_OR_OUTSIDE_SKILL_TREE"
    assert any(
        value == "SYMLINKED_PATH:scripts" for value in row["validation_findings"]
    )


def test_wave_catalog_fails_closed_on_duplicate_definition_wave_ids(
    tmp_path: Path,
) -> None:
    system, skills = _catalog_fixture(tmp_path)
    first = _copy_candidate(skills, "duplicate-definition-a")
    second = _copy_candidate(skills, "duplicate-definition-b")
    first_data = json.loads((first / "wave.json").read_text(encoding="utf-8"))
    second_data = json.loads((second / "wave.json").read_text(encoding="utf-8"))
    second_data["wave_id"] = first_data["wave_id"]
    (second / "wave.json").write_text(json.dumps(second_data), encoding="utf-8")

    listing = launcher.discover_wave_catalog(system)
    duplicate = f"duplicate_definition_wave_id:{first_data['wave_id']}"
    assert listing["catalog_state"] == "REFUSE"
    assert duplicate in listing["catalog_errors"]
    assert listing["duplicate_definition_wave_ids"] == [first_data["wave_id"]]
    assert listing["runnable_cohort"] == []
    assert all(row["runnable"] is False for row in listing["waves"])


def test_required_v1_active_cohort_cannot_be_co_omitted_or_empty(
    tmp_path: Path,
) -> None:
    system, skills = _catalog_fixture(tmp_path)
    _copy_candidate(skills, "unregistered-only")

    listing = launcher.discover_wave_catalog(system)
    errors = set(listing["catalog_errors"])
    assert listing["required_active_wave_ids"] == sorted(
        launcher.REQUIRED_ACTIVE_WAVE_IDS
    )
    assert "required_active_manifest_ids_mismatch" in errors
    for wave_id in launcher.REQUIRED_ACTIVE_WAVE_IDS:
        assert f"required_active_definition_missing:{wave_id}" in errors
        assert f"required_active_manifest_definition_missing:{wave_id}" in errors
    assert listing["runnable_cohort"] == []
    assert all(row["runnable"] is False for row in listing["waves"])


def test_wave_catalog_fails_closed_on_duplicate_active_manifest_ids(
    tmp_path: Path,
) -> None:
    system, skills = _catalog_fixture(tmp_path)
    wave = _copy_candidate(skills, "manifest-duplicate")
    script = wave / "scripts" / "run.py"
    script.write_text("raise SystemExit(0)\n", encoding="utf-8")
    definition = wave / "wave.json"
    row = {
        "wave_id": "manifest-duplicate",
        "definition": "skills/manifest-duplicate/wave.json",
        "script": "skills/manifest-duplicate/scripts/run.py",
        "definition_sha256": launcher.sha256_file(definition),
        "script_sha256": launcher.sha256_file(script),
    }
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps(
            {
                "schema": "constraintbox.active-wave-set.v1",
                "wave_definitions": ["skills/manifest-duplicate/wave.json"],
                "runnable_cohort": [row, dict(row)],
            }
        ),
        encoding="utf-8",
    )

    listing = launcher.discover_wave_catalog(system)
    assert listing["catalog_state"] == "REFUSE"
    assert "duplicate_active_manifest_wave_id:manifest-duplicate" in listing[
        "catalog_errors"
    ]
    assert listing["runnable_cohort"] == []
    assert all(row["runnable"] is False for row in listing["waves"])


def test_active_manifest_requires_exact_definition_path_and_hash_bindings(
    tmp_path: Path,
) -> None:
    system, skills = _catalog_fixture(tmp_path)
    active = _copy_candidate(skills, "path-bound-active")
    other = _copy_candidate(skills, "path-bound-other")
    script = active / "scripts" / "run.py"
    script.write_text("raise SystemExit(0)\n", encoding="utf-8")
    active_definition = active / "wave.json"
    other_definition = other / "wave.json"

    path_mismatch = {
        "wave_id": "path-bound-active",
        "definition": "skills/path-bound-other/wave.json",
        "script": "skills/path-bound-active/scripts/run.py",
        "skill": "skills/path-bound-other/SKILL.md",
        "definition_sha256": launcher.sha256_file(other_definition),
        "script_sha256": launcher.sha256_file(script),
        "skill_sha256": launcher.sha256_file(other / "SKILL.md"),
    }
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps(
            {
                "schema": "constraintbox.active-wave-set.v1",
                "wave_definitions": [
                    "skills/path-bound-active/wave.json",
                    "skills/path-bound-other/wave.json",
                ],
                "runnable_cohort": [path_mismatch],
            }
        ),
        encoding="utf-8",
    )
    listing = launcher.discover_wave_catalog(system)
    row = next(row for row in listing["waves"] if row["wave_id"] == "path-bound-active")
    assert row["classification"] != "ACTIVE"
    assert row["runnable"] is False
    assert row["reason_code"] == "active_manifest_definition_path_mismatch"

    exact_but_tampered = dict(path_mismatch)
    exact_but_tampered["definition"] = "skills/path-bound-active/wave.json"
    exact_but_tampered["definition_sha256"] = "0" * 64
    exact_but_tampered["skill"] = "skills/path-bound-active/SKILL.md"
    exact_but_tampered["skill_sha256"] = launcher.sha256_file(active / "SKILL.md")
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps(
            {
                "schema": "constraintbox.active-wave-set.v1",
                "wave_definitions": ["skills/path-bound-active/wave.json"],
                "runnable_cohort": [exact_but_tampered],
            }
        ),
        encoding="utf-8",
    )
    listing = launcher.discover_wave_catalog(system)
    row = next(row for row in listing["waves"] if row["wave_id"] == "path-bound-active")
    assert row["classification"] != "ACTIVE"
    assert row["runnable"] is False
    assert row["reason_code"] == "active_manifest_definition_hash_mismatch"
    assert active_definition.is_file()


def test_active_manifest_rejects_skill_tamper_and_forged_hashes(
    tmp_path: Path,
) -> None:
    system, skills, manifest = _three_active_fixture(tmp_path)
    maintenance = skills / "cb-maintenance-wave"
    original_skill = maintenance / "SKILL.md"
    original_bytes = original_skill.read_bytes()
    original_skill.write_bytes(original_bytes + b"\n# tampered\n")

    listing = launcher.discover_wave_catalog(system)
    row = next(
        row for row in listing["waves"] if row["wave_id"] == "cb-maintenance-wave"
    )
    assert row["runnable"] is False
    assert row["reason_code"] == "active_manifest_skill_hash_mismatch"

    original_skill.write_bytes(original_bytes)
    active_row = next(
        row for row in manifest["runnable_cohort"]
        if row["wave_id"] == "cb-maintenance-wave"
    )
    active_row["script_sha256"] = "f" * 64
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    listing = launcher.discover_wave_catalog(system)
    row = next(
        row for row in listing["waves"] if row["wave_id"] == "cb-maintenance-wave"
    )
    assert row["runnable"] is False
    assert row["reason_code"] == "active_manifest_script_hash_mismatch"


def test_active_definition_id_forgery_cannot_be_co_tampered_into_activation(
    tmp_path: Path,
) -> None:
    system, skills, manifest = _three_active_fixture(tmp_path)
    maintenance = skills / "cb-maintenance-wave" / "wave.json"
    definition = json.loads(maintenance.read_text(encoding="utf-8"))
    definition["wave_id"] = "cb-exploration-wave-v1"
    maintenance.write_text(json.dumps(definition), encoding="utf-8")
    row = next(
        row for row in manifest["runnable_cohort"]
        if row["wave_id"] == "cb-maintenance-wave"
    )
    row["definition_sha256"] = launcher.sha256_file(maintenance)
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    listing = launcher.discover_wave_catalog(system)
    catalog_row = next(
        row for row in listing["waves"] if row["wave_id"] == "cb-maintenance-wave"
    )
    assert listing["catalog_state"] == "REFUSE"
    assert catalog_row["runnable"] is False
    assert catalog_row["reason_code"] == "active_definition_wave_id_mismatch"
    assert "required_active_catalog_missing:cb-maintenance-wave" in listing[
        "catalog_errors"
    ]


def test_candidate_local_validator_is_never_imported_and_trusted_validator_must_be_regular(
    tmp_path: Path,
) -> None:
    system, skills = _catalog_fixture(tmp_path)
    candidate = _copy_candidate(skills, "validator-boundary")
    scripts = candidate / "scripts"
    marker = tmp_path / "candidate-validator-imported"
    (scripts / "validate_wave.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('imported')\n",
        encoding="utf-8",
    )
    listing = launcher.discover_wave_catalog(system)
    row = next(row for row in listing["waves"] if row["wave_id"] == "validator-boundary")
    assert not marker.exists()
    assert row["validation"]["validator"] == (
        "skills/cb-wave-author/scripts/validate_wave.py"
    )

    trusted = skills / "cb-wave-author" / "scripts" / "validate_wave.py"
    outside = tmp_path / "trusted-validator-outside.py"
    outside.write_text("raise SystemExit(99)\n", encoding="utf-8")
    trusted.unlink()
    trusted.symlink_to(outside)
    listing = launcher.discover_wave_catalog(system)
    row = next(row for row in listing["waves"] if row["wave_id"] == "validator-boundary")
    assert row["validation"]["validator_available"] is False
    assert "trusted_validator_not_confined" in row["validation_findings"]
    assert not marker.exists()


def test_unknown_public_wave_id_still_refuses(capsys) -> None:
    returncode = launcher.main(
        ["wave", "inspect", "cb-wave-id-that-is-not-present"]
    )
    assert returncode == 2
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "REFUSE"
    assert result["reason_code"] == "UNKNOWN_WAVE"
    assert result["runnable"] is False
    assert result["promotion_allowed"] is False


def test_public_wave_inspect_candidate_is_read_only_and_non_runnable(capsys) -> None:
    returncode = launcher.main(
        ["wave", "inspect", "cb-capability-probe-map-wave"]
    )
    assert returncode == 2
    result = json.loads(capsys.readouterr().out)
    assert result["classification"] == "UNREGISTERED_CANDIDATE"
    assert result["runnable"] is False
    assert result["promotion_allowed"] is False


def test_public_campaign_surface_uses_the_contained_deterministic_scheduler() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"campaign"' in source
    assert "scripts/run_cumulative_waves.py" in source
    assert 'choices=("light", "heavy")' in source
    assert "--profile" in source


def test_public_context_refresh_uses_the_contained_compact_refresher() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"--refresh-source"' in source
    assert "scripts/refresh_context_corpus.py" in source
    assert "context/full/CORPUS_REFRESH_LEDGER.jsonl" in source
    assert '"--dry-run"' in source


def test_public_path_mass_surface_binds_contained_fixture() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"path-mass"' in source
    assert "scripts/run_constraint_path_mass.py" in source
    assert "fixtures/minilev/proposal_reference_policy_v1.json" in source


def test_public_provider_zip_surface_delegates_to_zip_runtime() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"provider-zip"' in source
    assert "constraintbox_zip_agent.single_provider_child" in source
    assert "issue_dispatch_lease" in source
    assert '"constraintbox_zip_agent", *args' in source


def test_premortem_candidate_is_lease_bound_and_not_the_active_wave() -> None:
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"premortem-candidate"' in source
    assert "skills/cb-premortem-wave/scripts/run_premortem_zip_wave.py" in source
    assert "issue_dispatch_lease(identity)" in source
    assert '"premortem-wave"' not in source


def test_jax_profile_attestation_binds_product_lock(tmp_path: Path) -> None:
    system = tmp_path / "integrated_system"
    lock = system / "runtime_profiles" / "jax_qit" / "requirements.lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("jax==0.10.1\n", encoding="utf-8")
    runtime = tmp_path / "jax-qit-stack"
    python = runtime / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    manifest = {
        "schema": "constraintbox.jax-qit-stack-manifest.v1",
        "profile": "jax_qit",
        "status": "VERIFIED_LOCAL",
        "requirements": {"lock_sha256": launcher.sha256_file(lock)},
    }
    (runtime / "STACK_MANIFEST.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    observed = launcher.jax_profile_attestation(system, python)
    assert observed["status"] == "PASS"
    lock.write_text("jax==0.10.2\n", encoding="utf-8")
    drifted = launcher.jax_profile_attestation(system, python)
    assert drifted["status"] == "HOLD"
    assert drifted["reason"] == "HOLD_JAX_PROFILE_ATTESTATION_DRIFT"
