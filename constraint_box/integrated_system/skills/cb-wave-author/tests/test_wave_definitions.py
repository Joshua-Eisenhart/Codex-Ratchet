from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path


ROOT = Path(__file__).parents[2]
SYSTEM = ROOT.parent
VALIDATOR = ROOT / "cb-wave-author/scripts/validate_wave.py"
spec = importlib.util.spec_from_file_location("validate_wave", VALIDATOR)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
LAUNCHER = SYSTEM / "bin" / "cb"
# Custody ceiling: this pins the checked-in Git worktree bytes only.  It is
# not an external trust anchor or proof that a remote copy is immutable.
EXPECTED_ACTIVE_MANIFEST_SHA256 = (
    "211931849d0c0c1fa64507c6b505d17570d597058358675d020ecae26d5c1e77"
)
launcher_spec = importlib.util.spec_from_loader(
    "integrated_cb_launcher_for_wave_inventory",
    SourceFileLoader("integrated_cb_launcher_for_wave_inventory", str(LAUNCHER)),
)
assert launcher_spec is not None and launcher_spec.loader is not None
launcher = importlib.util.module_from_spec(launcher_spec)
launcher_spec.loader.exec_module(launcher)
EXEC_VALIDATOR = ROOT / "cb-wave-author/scripts/verify_wave_execution.py"
exec_spec = importlib.util.spec_from_file_location("verify_wave_execution", EXEC_VALIDATOR)
exec_module = importlib.util.module_from_spec(exec_spec)
assert exec_spec.loader is not None
exec_spec.loader.exec_module(exec_module)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    files = [
        item
        for item in path.rglob("*")
        if item.is_file()
        and "__pycache__" not in item.relative_to(path).parts
        and ".pytest_cache" not in item.relative_to(path).parts
        and item.suffix not in {".pyc", ".pyo"}
    ]
    for item in sorted(files, key=lambda value: value.relative_to(path).as_posix()):
        relative = item.relative_to(path).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(_sha256(item).encode("ascii"))
    return digest.hexdigest()


def _non_symlink_product_definition(path: Path) -> bool:
    """Return true only for a regular, product-confined definition file."""

    try:
        if path.is_symlink() or not path.is_file():
            return False
        root = ROOT.resolve(strict=True)
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
        # The immediate product path must not rely on a symlinked ancestor.
        current = path.absolute()
        relative = current.relative_to(ROOT.absolute())
        ancestor = ROOT.absolute()
        for component in relative.parts:
            ancestor /= component
            if ancestor.is_symlink():
                return False
        return True
    except (OSError, ValueError):
        return False


def definitions() -> list[Path]:
    """Discover every confined product ``skills/*/wave.json`` definition."""

    return sorted(
        path
        for path in ROOT.glob("*/wave.json")
        if _non_symlink_product_definition(path)
    )


def test_every_wave_definition_is_valid_and_independent() -> None:
    paths = definitions()
    catalog = launcher.discover_wave_catalog(SYSTEM)
    expected = {
        path.relative_to(SYSTEM).as_posix(): path
        for path in paths
    }
    rows = catalog["waves"]
    by_definition = {row["definition"]: row for row in rows}

    # The public catalog is the trusted inventory.  Every confined product
    # definition must appear once, while symlinked/outside entries are omitted
    # rather than silently followed.
    assert catalog["catalog_state"] == "READY"
    assert catalog["catalog_errors"] == []
    assert catalog["claim_ceiling"] == (
        "Checked-in product bytes and trusted manifest bindings only; "
        "Git custody and external immutability are unproved."
    )
    assert catalog["duplicate_definition_wave_ids"] == []
    assert catalog["omitted"] == []
    assert len(paths) == len(rows) == len(by_definition)
    assert set(expected) == set(by_definition)
    assert len({row["wave_id"] for row in rows}) == len(rows)
    assert len({row["definition_wave_id"] for row in rows}) == len(rows)

    # These are the current candidate surfaces called out by the product
    # contract; keeping the check ID-based avoids a frozen whole-estate list.
    current_candidates = {
        "cb-capability-probe-map-wave",
        "cb-formalization-digger-wave",
        "cb-context-wave",
        "cb-objective-integrity-wave",
        "cb-strategy-framing-wave",
        "cb-strategy-checkpoint-wave",
        "cb-strategy-discriminator-wave",
    }
    candidate_ids = {
        row["wave_id"] for row in catalog["unregistered_candidates"]
    }
    assert current_candidates <= candidate_ids

    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        definition_errors = list(module.validate(data))
        tree_errors = list(module.validate_tree(data, ROOT))
        key = path.relative_to(SYSTEM).as_posix()
        row = by_definition[key]
        assert row["definition"] == key
        assert row["definition_wave_id"] == data["wave_id"]
        assert _sha256(path) == row["definition_sha256"]
        tree_key = path.parent.relative_to(SYSTEM).as_posix()
        tree_sha256 = _tree_sha256(path.parent)
        assert row["tree_path"] == tree_key
        assert row["source_path"] == tree_key
        assert row["source_sha256"] == tree_sha256
        assert row["tree_sha256"] == tree_sha256
        skill = path.parent / "SKILL.md"
        skill_key = skill.relative_to(SYSTEM).as_posix()
        assert row["skill"] == skill_key
        assert row["skill_sha256"] == _sha256(skill)
        if row["classification"] != "ACTIVE":
            assert row["source"] == [
                {"path": tree_key, "sha256": tree_sha256}
            ]

        # The catalog must use this fixed validator and report exactly its
        # definition/tree findings.  Authored inactive composites may retain
        # missing-child findings; active and unregistered candidates must be
        # clean.  ZIP-native validation remains covered by its own test below,
        # but its generic trusted-validator findings are still observed here.
        assert row["validation"]["validator"] == (
            "skills/cb-wave-author/scripts/validate_wave.py"
        )
        assert row["validation"]["validator_available"] is True
        assert row["validation"]["definition_errors"] == definition_errors
        assert row["validation"]["tree_errors"] == tree_errors
        assert row["validation"]["errors"] == definition_errors + tree_errors
        if row["classification"] in {"ACTIVE", "UNREGISTERED_CANDIDATE"}:
            assert definition_errors == [], path
            assert tree_errors == [], path

        assert _sha256(path) == row["definition_sha256"]
        assert isinstance(row["source_sha256"], str)
        assert len(row["source_sha256"]) == 64
        assert (path.parent / "SKILL.md").is_file()

    manifest = json.loads(
        (ROOT / "ACTIVE_WAVES.json").read_text(encoding="utf-8")
    )
    assert _sha256(ROOT / "ACTIVE_WAVES.json") == EXPECTED_ACTIVE_MANIFEST_SHA256
    manifest_rows = manifest["runnable_cohort"]
    active_rows = [row for row in rows if row["classification"] == "ACTIVE"]
    assert {row["wave_id"] for row in manifest_rows} == launcher.REQUIRED_ACTIVE_WAVE_IDS
    assert {row["wave_id"] for row in active_rows} == launcher.REQUIRED_ACTIVE_WAVE_IDS
    assert {row["wave_id"] for row in catalog["active"]} == launcher.REQUIRED_ACTIVE_WAVE_IDS
    assert {row["definition"] for row in catalog["active"]} == {
        row["definition"] for row in manifest_rows
    }
    manifest_by_definition = {row["definition"]: row for row in manifest_rows}
    active_by_definition = {row["definition"]: row for row in active_rows}
    assert len(manifest_rows) == len(manifest_by_definition)
    assert set(manifest_by_definition) == set(active_by_definition)

    for definition_key, manifest_row in manifest_by_definition.items():
        catalog_row = active_by_definition[definition_key]
        definition = SYSTEM / definition_key
        script_key = manifest_row["script"]
        script = SYSTEM / script_key
        assert catalog_row["wave_id"] == manifest_row["wave_id"]
        assert manifest_row["skill"] == (
            f"skills/{manifest_row['wave_id']}/SKILL.md"
        )
        skill = SYSTEM / manifest_row["skill"]
        assert skill.is_file() and not skill.is_symlink()
        assert manifest_row["skill_sha256"] == _sha256(skill)
        assert catalog_row["skill"] == manifest_row["skill"]
        assert catalog_row["skill_sha256"] == manifest_row["skill_sha256"]
        assert catalog_row["runnable"] is True
        assert catalog_row["promotion_allowed"] is False
        assert manifest_row["definition_sha256"] == _sha256(definition)
        assert manifest_row["definition_sha256"] == catalog_row["definition_sha256"]
        assert script.is_file() and not script.is_symlink()
        assert manifest_row["script_sha256"] == _sha256(script)
        source_hashes = {
            entry["path"]: entry["sha256"]
            for entry in catalog_row["source"]
        }
        assert set(source_hashes) == {
            definition_key,
            script_key,
            manifest_row["skill"],
        }
        assert source_hashes[definition_key] == manifest_row["definition_sha256"]
        assert source_hashes[script_key] == manifest_row["script_sha256"]
        assert source_hashes[manifest_row["skill"]] == manifest_row["skill_sha256"]

    for row in rows:
        assert row["promotion_allowed"] is False
        if row["definition"] not in active_by_definition:
            assert row["runnable"] is False


def test_checked_in_manifest_contract_rejects_co_tamper(tmp_path: Path) -> None:
    source = ROOT / "ACTIVE_WAVES.json"
    tampered = tmp_path / "ACTIVE_WAVES.json"
    raw = source.read_text(encoding="utf-8")
    tampered.write_text(
        raw.replace(
            "8df4a17780f4cd65c4c19118f4cfb71b2f8f9bc18623a59fa839ef141aa23be9",
            "f" * 64,
            1,
        ),
        encoding="utf-8",
    )
    assert _sha256(source) == EXPECTED_ACTIVE_MANIFEST_SHA256
    assert _sha256(tampered) != EXPECTED_ACTIVE_MANIFEST_SHA256
    # The contract detects checked-in-byte drift; it is not an external
    # signature and does not claim Git or a deployed copy is immutable.


def test_runtime_assignments_in_definition_are_refused() -> None:
    data = json.loads((ROOT / "cb-failure-wave/wave.json").read_text(encoding="utf-8"))
    bad = copy.deepcopy(data)
    bad["models"] = ["temporary-name"]
    assert "embedded_runtime_assignments" in module.validate(bad)
    bad2 = copy.deepcopy(data)
    bad2["routing"] = {"preferred_models": ["temporary-name"]}
    assert "embedded_runtime_assignments" in module.validate(bad2)


def test_unknown_child_skill_is_refused_by_tree_validation() -> None:
    data = json.loads((ROOT / "cb-failure-wave/wave.json").read_text(encoding="utf-8"))
    data["children"][0]["skill"] = "does-not-exist"
    assert "missing_child_skill:does-not-exist" in module.validate_tree(data, ROOT)


def test_missing_cancellation_evidence_is_refused() -> None:
    data = json.loads((ROOT / "cb-failure-wave/wave.json").read_text(encoding="utf-8"))
    data["completion"]["required_evidence"].remove("cancellation_state")
    assert "completion_missing:cancellation_state" in module.validate(data)


def test_empty_stop_reasons_and_zero_mmm_range_are_refused() -> None:
    data = json.loads((ROOT / "cb-failure-wave/wave.json").read_text(encoding="utf-8"))
    data["loop"]["stop_reasons"] = []
    data["mmm_profile"]["voice_count_range"] = [0, 0]
    errors = module.validate(data)
    assert "loop_contract" in errors
    assert "mmm_count_range" in errors


def test_zip_failure_wave_is_valid_under_its_own_contract() -> None:
    path = ROOT / "zip-failure-wave" / "wave.json"
    validator = ROOT / "zip-failure-wave" / "scripts" / "validate_wave.py"
    proc = subprocess.run(
        [sys.executable, str(validator), str(path)],
        check=False,
        capture_output=True,
        text=True,
    )
    body = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert body["disposition"] == "ZIP_WAVE_DEFINITION_VALID"


def test_main_mmms_are_not_in_operational_wave_definitions() -> None:
    for path in definitions():
        text = path.read_text(encoding="utf-8")
        assert "FULL_MMM_v4_3" not in text
        assert "COMPACT_MMM_v4_3" not in text
        assert json.loads(text)["mmm_profile"]["mini_voices_only"] is True


def test_execution_requires_exact_child_call_and_output_chain(tmp_path: Path) -> None:
    definition_path = ROOT / "cb-premortem-wave/wave.json"
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    mmm_root = tmp_path / "mmm"
    (mmm_root / "mini/full/voices/md").mkdir(parents=True)
    (mmm_root / "mini/compact/voices/md").mkdir(parents=True)
    for voice in ("FACTORY", "FEYNMAN", "HUME", "ORWELL", "POPPER", "PUSHBACK", "STRATEGY", "SYSTEMS", "ZHUANGZI"):
        for variant in ("full", "compact"):
            path = mmm_root / "mini" / variant / "voices" / "md" / f"MMM_VOICE_{voice}_{variant.upper()}_v4_1.md"
            path.write_text(f"{voice} {variant}\n", encoding="utf-8")
    children = []
    for index, child in enumerate(definition["children"]):
        cell = tmp_path / child["id"]
        cell.mkdir()
        task = cell / "task.md"
        task.write_text(child["operation"], encoding="utf-8")
        prepared = subprocess.run([
            sys.executable, str(ROOT / "mmm-preload/scripts/mmm_preload.py"), "prepare",
            "--task-file", str(task), "--output-dir", str(cell), "--run-id", "run-1",
            "--agent-id", child["id"], "--parent-id", "controller-1", "--wave-id", definition["wave_id"],
            "--round", "1", "--depth", "1", "--seed", str(21 + index), "--voice-count", "2",
            "--mmm-root", str(mmm_root),
        ], capture_output=True, text=True, check=False)
        assert prepared.returncode == 0, prepared.stdout
        preload = cell / "preload_receipt.json"
        preload_data = json.loads(preload.read_text(encoding="utf-8"))
        output = cell / "output.md"
        output.write_text("observed", encoding="utf-8")
        output_hash = exec_module.sha(output.read_bytes())
        call = cell / "call.json"
        call.write_text(json.dumps({
            "schema": "constraintbox.provider-call.v1",
            "preload_receipt_sha256": exec_module.sha(preload.read_bytes()),
            "composed_prompt_sha256": preload_data["composed_prompt_sha256"],
            "run_id": "run-1", "agent_id": child["id"], "parent_id": "controller-1",
            "wave_id": definition["wave_id"], "round": 1, "depth": 1,
            "provider_request_id": f"request-{index}",
            "terminal_state": "COMPLETED",
            "output_sha256": output_hash,
        }), encoding="utf-8")
        tool_rows = []
        for capability in child["tools"]:
            tool_path = cell / f"tool-{capability}.json"
            tool_path.write_text(json.dumps({"schema": "constraintbox.tool-observation.v1", "capability": capability, "target_sha256": "b" * 64}), encoding="utf-8")
            tool_rows.append({"capability": capability, "receipt_path": str(tool_path), "receipt_sha256": exec_module.sha(tool_path.read_bytes())})
        children.append({
            "child_id": child["id"],
            "agent_id": child["id"],
            "terminal_state": "COMPLETED",
            "preload_receipt": str(preload),
            "provider_call_receipt": str(call),
            "output_path": str(output),
            "output_sha256": output_hash,
            "tool_observations": tool_rows,
        })
    wave_output = tmp_path / "wave-output.md"
    wave_output.write_text("wave result", encoding="utf-8")
    execution = tmp_path / "execution.json"
    execution.write_text(json.dumps({
        "schema": "constraintbox.wave-execution.v1",
        "wave_id": definition["wave_id"],
        "state": "COMPLETE",
        "run_id": "run-1",
        "controller_agent_id": "controller-1",
        "depth": 0,
        "round": 1,
        "target_sha256": "b" * 64,
        "mmm_root": str(mmm_root),
        "children": children,
        "cancellation_state": "NOT_CANCELLED",
        "disagreement_state": [],
        "repair_digest": "c" * 64,
        "rerun_delta": {},
        "output_path": str(wave_output),
        "output_sha256": exec_module.sha(wave_output.read_bytes()),
    }), encoding="utf-8")
    assert exec_module.verify(definition_path, execution) == []
    broken = json.loads(execution.read_text(encoding="utf-8"))
    broken["children"][0]["tool_observations"] = []
    execution.write_text(json.dumps(broken), encoding="utf-8")
    assert f"tool_evidence:{children[0]['child_id']}" in exec_module.verify(definition_path, execution)
    execution.write_text(json.dumps({**broken, "children": children}), encoding="utf-8")
    Path(children[0]["provider_call_receipt"]).unlink()
    assert f"missing_call_chain:{children[0]['child_id']}" in exec_module.verify(definition_path, execution)


def test_nested_wave_placeholder_is_refused(tmp_path: Path) -> None:
    definition_path = ROOT / "cb-failure-wave/wave.json"
    definition = json.loads(definition_path.read_text(encoding="utf-8"))
    placeholder = tmp_path / "placeholder.json"
    placeholder.write_text("not a wave receipt", encoding="utf-8")
    execution = tmp_path / "execution.json"
    execution.write_text(json.dumps({
        "schema": "constraintbox.wave-execution.v1", "wave_id": definition["wave_id"],
        "state": "PARTIAL", "run_id": "r", "controller_agent_id": "c", "depth": 0,
        "round": 1, "target_sha256": "a" * 64, "mmm_root": str(tmp_path),
        "children": [{"child_id": row["id"], "agent_id": row["id"], "terminal_state": "FAILED", "child_wave_receipt": str(placeholder)} for row in definition["children"]],
        "cancellation_state": "NOT_CANCELLED", "disagreement_state": [],
        "output_path": str(placeholder), "output_sha256": exec_module.sha(placeholder.read_bytes()),
        "repair_digest": "b" * 64, "rerun_delta": {},
    }), encoding="utf-8")
    errors = exec_module.verify(definition_path, execution)
    assert any("invalid_execution:JSONDecodeError" in error for error in errors)
