from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


CANDIDATE = Path(__file__).resolve().parents[1]
ROOT = CANDIDATE.parents[3]
RUNNER_PATH = CANDIDATE / "scripts" / "run_formalization_digger.py"
spec = importlib.util.spec_from_file_location("formalization_digger_runner", RUNNER_PATH)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def fixture(name: str) -> Path:
    return CANDIDATE / "fixtures" / name


def run_fixture(**kwargs: object) -> dict[str, object]:
    return runner.run_wave(ROOT, **kwargs)


def _inside_copy(name: str, source: Path) -> Path:
    path = CANDIDATE / "fixtures" / f".test-{name}"
    shutil.copy2(source, path)
    return path


def _remove(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()


def _reseal_capability(capability: dict[str, object]) -> dict[str, object]:
    unsigned = {
        key: value
        for key, value in capability.items()
        if key not in {"receipt_sha256", "result_sha256"}
    }
    receipt_sha256 = runner.digest(unsigned)
    capability["receipt_sha256"] = receipt_sha256
    capability["result_sha256"] = receipt_sha256
    return capability


def _rebind_bundle(bundle: dict[str, object], capability_sha256: str) -> dict[str, object]:
    bundle["capability_receipt_sha256"] = capability_sha256
    for child in bundle.get("children", []):
        if isinstance(child, dict):
            child["capability_receipt_sha256"] = capability_sha256
    bundle["proposal_bundle_digest"] = runner.digest(
        {key: value for key, value in bundle.items() if key != "proposal_bundle_digest"}
    )
    return bundle


def test_wave_and_registry_are_explicitly_inactive_with_four_children() -> None:
    wave = json.loads((CANDIDATE / "wave.json").read_text(encoding="utf-8"))
    registry = json.loads((CANDIDATE / "registry.json").read_text(encoding="utf-8"))
    assert wave["schema"] == "constraintbox.wave-definition.v1"
    assert wave["candidate_state"] == "NEW_CANDIDATE"
    assert wave["activated"] is False
    assert wave["promotion_allowed"] is False
    assert [row["id"] for row in wave["children"]] == list(runner.CHILD_IDS)
    assert registry["candidate_state"] == "NEW_CANDIDATE"
    assert registry["activated"] is False
    assert registry["promotion_allowed"] is False
    assert registry["inputs"]["context_epoch"]["schema"] == "constraintbox.context-epoch.v2"
    assert registry["inputs"]["capability_probe_map"]["digest_field"] == "receipt_sha256"


def test_wave_definition_passes_shared_wave_validator() -> None:
    validator = ROOT / "constraint_box/integrated_system/skills/cb-wave-author/scripts/validate_wave.py"
    proc = subprocess.run([sys.executable, str(validator), str(CANDIDATE / "wave.json")], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["disposition"] == "WAVE_DEFINITION_VALID"


def test_real_epoch_and_capability_receipt_compile_frontier() -> None:
    receipt = run_fixture()
    assert receipt["status"] == "PASS"
    assert receipt["reason"] == "FRONTIER_COMPILED"
    assert receipt["semantic_inputs"]["epoch_id"] == "epoch-00000002"
    assert receipt["semantic_inputs"]["epoch_digest"] == "2142b80f0223812dcb4071a5178a85ff980062c831873a14d211cc64896942db"
    assert receipt["semantic_inputs"]["capability_wave_id"] == "cb-capability-probe-map-wave-v1"
    assert receipt["verifier_bindings"]["epoch_sealer"]["sha256"] == runner.file_digest(ROOT / runner.EPOCH_VERIFIER)
    assert receipt["verifier_bindings"]["capability_producer"]["sha256"] == runner.file_digest(ROOT / runner.CAPABILITY_PRODUCER)
    assert receipt["provider_call_receipt"] is None
    assert receipt["preload_receipts"] == []
    assert receipt["capability_reproduction"]["expected_wave_id"] == "cb-capability-probe-map-wave-v1"
    assert receipt["capability_reproduction"]["expected_candidate_state"] == "NEW_CANDIDATE"
    assert receipt["capability_reproduction"]["expected_status"] == "HOLD"
    assert isinstance(receipt["capability_reproduction"]["receipt_match"], bool)
    assert receipt["capability_reproduction"]["projection_match"] is True
    assert receipt["candidate_state"] == "NEW_CANDIDATE"
    assert receipt["activated"] is False
    assert receipt["promotion_allowed"] is False
    assert runner.verify_receipt(receipt, ROOT)
    assert all(row["terminal_state"] == "PROPOSAL_VALIDATED" for row in receipt["child_receipts"])
    assert all(row["skill_execution_claimed"] is False for row in receipt["child_receipts"])
    assert receipt["frontier"]["voting"] is False
    assert receipt["frontier"]["truth_decided"] is False
    assert receipt["frontier"]["gate_activated"] is False


def test_capability_reproduction_ignores_ambient_interpreter_overrides(monkeypatch) -> None:
    monkeypatch.setenv("CB_LIGHT_PYTHON", "/tmp/forged-light-python")
    monkeypatch.setenv("CB_LIGHT_INTERPRETER", "/tmp/forged-light-interpreter")
    receipt = run_fixture()
    assert receipt["status"] == "PASS"
    assert receipt["capability_reproduction"]["declared_interpreter"] == "constraint_box/.venv/bin/python"


def test_capability_receipt_is_actual_producer_schema_and_verifies() -> None:
    capability = runner.read_json(fixture("capability_probe_map_v1.json"))
    producer = runner._load_module(ROOT / runner.CAPABILITY_PRODUCER, "test_capability_producer")
    assert capability["schema"] == "constraintbox.capability-probe-map-receipt.v1"
    assert capability["capability_map"]["schema"] == "constraintbox.capability-map.v1"
    assert producer.verify_receipt(capability)
    assert capability["root"]["runner_sha256"] == runner.file_digest(ROOT / runner.CAPABILITY_PRODUCER)


def test_stale_epoch_fixture_refuses_against_current_epoch_source(monkeypatch) -> None:
    real_digest = runner.file_digest
    epoch_source = (ROOT / runner.EPOCH_SOURCE).resolve()

    def stale(path: Path) -> str:
        if Path(path).resolve() == epoch_source:
            return "0" * 64
        return real_digest(path)

    monkeypatch.setattr(runner, "file_digest", stale)
    receipt = run_fixture()
    assert receipt["status"] == "REFUSE"
    assert any("REFUSE_STALE_EPOCH_FIXTURE" in error for error in receipt["errors"])


def test_stale_capability_producer_refuses_before_proposal_use(monkeypatch) -> None:
    real_digest = runner.file_digest
    producer_path = (ROOT / runner.CAPABILITY_PRODUCER).resolve()

    def stale(path: Path) -> str:
        if Path(path).resolve() == producer_path:
            return "0" * 64
        return real_digest(path)

    monkeypatch.setattr(runner, "file_digest", stale)
    receipt = run_fixture()
    assert receipt["status"] == "REFUSE"
    assert any("REFUSE_STALE_CAPABILITY_PRODUCER" in error for error in receipt["errors"])


def test_stale_producer_receipt_fixture_refuses_after_valid_self_reseal() -> None:
    capability = runner.read_json(fixture("capability_probe_map_v1.json"))
    capability["root"]["runner_sha256"] = "0" * 64
    unsigned = {key: value for key, value in capability.items() if key not in {"receipt_sha256", "result_sha256"}}
    capability["receipt_sha256"] = runner.digest(unsigned)
    capability["result_sha256"] = capability["receipt_sha256"]
    path = _inside_copy("stale-capability.json", fixture("capability_probe_map_v1.json"))
    try:
        path.write_text(json.dumps(capability), encoding="utf-8")
        producer = runner._load_module(ROOT / runner.CAPABILITY_PRODUCER, "test_stale_producer")
        assert producer.verify_receipt(capability)
        receipt = runner.run_wave(ROOT, capability_probe_map_path=path.relative_to(ROOT))
        assert receipt["status"] == "REFUSE"
        assert any("REFUSE_STALE_CAPABILITY_PRODUCER" in error for error in receipt["errors"])
    finally:
        _remove(path)


@pytest.mark.parametrize(
    ("field", "value", "expected_reason"),
    [
        ("wave_id", "forged-capability-wave", "REFUSE_CAPABILITY_INPUT_WAVE_ID"),
        ("status", "PASS", "REFUSE_CAPABILITY_INPUT_STATUS"),
    ],
)
def test_resealed_capability_identity_refuses_even_when_proposals_rebound(
    field: str,
    value: str,
    expected_reason: str,
) -> None:
    capability = runner.read_json(fixture("capability_probe_map_v1.json"))
    capability[field] = value
    _reseal_capability(capability)
    capability_path = _inside_copy(f"resealed-{field}.json", fixture("capability_probe_map_v1.json"))
    proposals_path = _inside_copy(f"rebound-{field}.json", fixture("digger_proposals_v2.json"))
    try:
        capability_path.write_text(json.dumps(capability), encoding="utf-8")
        bundle = runner.read_json(proposals_path)
        _rebind_bundle(bundle, str(capability["receipt_sha256"]))
        proposals_path.write_text(json.dumps(bundle), encoding="utf-8")
        producer = runner._load_module(ROOT / runner.CAPABILITY_PRODUCER, f"test_resealed_{field}")
        assert producer.verify_receipt(capability)
        refusal = runner.run_wave(
            ROOT,
            capability_probe_map_path=capability_path.relative_to(ROOT),
            proposals_path=proposals_path.relative_to(ROOT),
        )
        assert refusal["status"] == "REFUSE"
        assert refusal["reason"] == expected_reason
        assert refusal["frontier"] is None
        assert runner.verify_receipt(refusal, ROOT) is False
    finally:
        _remove(capability_path)
        _remove(proposals_path)


def test_resealed_capability_map_refuses_even_when_proposals_rebound() -> None:
    capability = runner.read_json(fixture("capability_probe_map_v1.json"))
    capability["capability_map"]["entries"].append(
        {
            "capability": "forged_capability",
            "operation": "forged.v1",
            "status": "BOUND",
        }
    )
    _reseal_capability(capability)
    capability_path = _inside_copy("resealed-capability-map.json", fixture("capability_probe_map_v1.json"))
    proposals_path = _inside_copy("rebound-capability-map.json", fixture("digger_proposals_v2.json"))
    try:
        capability_path.write_text(json.dumps(capability), encoding="utf-8")
        bundle = runner.read_json(proposals_path)
        _rebind_bundle(bundle, str(capability["receipt_sha256"]))
        proposals_path.write_text(json.dumps(bundle), encoding="utf-8")
        producer = runner._load_module(ROOT / runner.CAPABILITY_PRODUCER, "test_resealed_capability_map")
        assert producer.verify_receipt(capability)
        refusal = runner.run_wave(
            ROOT,
            capability_probe_map_path=capability_path.relative_to(ROOT),
            proposals_path=proposals_path.relative_to(ROOT),
        )
        assert refusal["status"] == "REFUSE"
        assert refusal["reason"] == "REFUSE_CAPABILITY_PROJECTION_DRIFT"
        assert refusal["frontier"] is None
        assert runner.verify_receipt(refusal, ROOT) is False
    finally:
        _remove(capability_path)
        _remove(proposals_path)


def test_source_ref_tamper_refuses_even_when_bundle_digest_is_rebound() -> None:
    bundle = runner.read_json(fixture("digger_proposals_v2.json"))
    bundle["children"][0]["source_refs"][0]["sha256"] = "0" * 64
    bundle["proposal_bundle_digest"] = runner.digest({key: value for key, value in bundle.items() if key != "proposal_bundle_digest"})
    path = _inside_copy("source-tamper.json", fixture("digger_proposals_v2.json"))
    try:
        path.write_text(json.dumps(bundle), encoding="utf-8")
        receipt = runner.run_wave(ROOT, proposals_path=path.relative_to(ROOT))
        assert receipt["status"] == "REFUSE"
        assert any("sha256_mismatch" in error for error in receipt["errors"])
    finally:
        _remove(path)


def test_merged_controller_source_variant_is_logically_bound_only_for_same_sha(tmp_path: Path) -> None:
    source_path = "constraint_box/src/constraintbox/constraint_path_mass.py"
    merged_path = "constraint_box/integrated_system/runtime/controller_src/constraintbox/constraint_path_mass.py"
    source_bytes = (ROOT / source_path if (ROOT / source_path).is_file() else ROOT / merged_path).read_bytes()
    physical = tmp_path / merged_path
    physical.parent.mkdir(parents=True)
    physical.write_bytes(source_bytes)
    source_sha = runner.sha256_bytes(source_bytes)
    allowed = {runner._logical_source_id(merged_path): source_sha}

    accepted = runner._validate_source_refs(
        [{"path": source_path, "sha256": source_sha}],
        tmp_path,
        allowed,
        "variant",
    )
    assert accepted == []
    assert runner._logical_source_id(source_path) == runner._logical_source_id(merged_path)
    assert runner._logical_source_id(merged_path + ".suffix") == merged_path + ".suffix"

    wrong_sha = runner._validate_source_refs(
        [{"path": source_path, "sha256": "0" * 64}],
        tmp_path,
        allowed,
        "wrong_sha",
    )
    assert any("sha256_mismatch" in error for error in wrong_sha)

    wrong_path = runner._validate_source_refs(
        [{"path": merged_path + ".suffix", "sha256": source_sha}],
        tmp_path,
        allowed,
        "wrong_path",
    )
    assert wrong_path
    assert any(error.startswith("REFUSE_PATH_RESOLVE:wrong_path") for error in wrong_path)

    source_projection = runner._capability_projection(
        {"declared_source": source_path, "source": {"path": source_path, "sha256": source_sha}}
    )
    merged_projection = runner._capability_projection(
        {"declared_source": merged_path, "source": {"path": merged_path, "sha256": source_sha}}
    )
    assert source_projection == merged_projection


def test_path_escape_and_symlink_inputs_are_refused(tmp_path: Path) -> None:
    escape = run_fixture(context_epoch_path="../outside.json")
    assert escape["status"] == "REFUSE"
    assert any("REFUSE_PATH_ESCAPE" in error for error in escape["errors"])
    link = CANDIDATE / "fixtures" / ".test-epoch-link.json"
    link.symlink_to(fixture("context_epoch_v2.json"))
    try:
        symlink = run_fixture(context_epoch_path=link.relative_to(ROOT))
        assert symlink["status"] == "REFUSE"
        assert any("REFUSE_SYMLINK_PATH" in error for error in symlink["errors"])
    finally:
        _remove(link)
    outside = tmp_path / "outside.receipt.json"
    refusal = run_fixture(out_path=outside)
    assert refusal["status"] == "REFUSE"
    assert not outside.exists()


def test_absolute_path_with_parent_component_is_refused_before_normalization() -> None:
    lexical_escape = f"{ROOT}/constraint_box/integrated_system/skills/cb-formalization-digger-wave/fixtures/../fixtures/context_epoch_v2.json"
    refusal = run_fixture(context_epoch_path=lexical_escape)
    assert refusal["status"] == "REFUSE"
    assert refusal["errors"] == ["REFUSE_PATH_ESCAPE:context_epoch"]


def test_replay_receipt_path_is_confined_before_reading() -> None:
    receipt = run_fixture()
    receipt_path = CANDIDATE / "fixtures" / ".test-replay-receipt.json"
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    lexical_escape = CANDIDATE / "fixtures" / ".." / "fixtures" / ".test-replay-receipt.json"
    try:
        replay = runner.replay_receipt(lexical_escape, ROOT)
        assert replay["status"] == "REFUSE"
        assert replay["reason"] == "REFUSE_PATH_ESCAPE"
    finally:
        _remove(receipt_path)


@pytest.mark.parametrize("bad_row", [None, "scalar", [], ["nested"]])
def test_scalar_list_and_null_child_rows_refuse_deterministically(bad_row: object) -> None:
    bundle = runner.read_json(fixture("digger_proposals_v2.json"))
    bundle["children"][1] = bad_row
    bundle["proposal_bundle_digest"] = runner.digest({key: value for key, value in bundle.items() if key != "proposal_bundle_digest"})
    path = _inside_copy(f"malformed-child-{type(bad_row).__name__}.json", fixture("digger_proposals_v2.json"))
    try:
        path.write_text(json.dumps(bundle), encoding="utf-8")
        refusal = runner.run_wave(ROOT, proposals_path=path.relative_to(ROOT))
        assert refusal["status"] == "REFUSE"
        assert refusal["reason"] == "REFUSE_FORMALIZATION_INPUT"
        assert refusal["frontier"] is None
    finally:
        _remove(path)


def test_verified_capability_receipt_without_probe_rows_refuses_exactly() -> None:
    capability = runner.read_json(fixture("capability_probe_map_v1.json"))
    capability["children"] = []
    unsigned = {key: value for key, value in capability.items() if key not in {"receipt_sha256", "result_sha256"}}
    capability["receipt_sha256"] = runner.digest(unsigned)
    capability["result_sha256"] = capability["receipt_sha256"]
    path = _inside_copy("no-probes.json", fixture("capability_probe_map_v1.json"))
    try:
        path.write_text(json.dumps(capability), encoding="utf-8")
        producer = runner._load_module(ROOT / runner.CAPABILITY_PRODUCER, "test_no_probe_capability")
        assert producer.verify_receipt(capability)
        refusal = runner.run_wave(ROOT, capability_probe_map_path=path.relative_to(ROOT))
        assert refusal["status"] == "REFUSE"
        assert refusal["reason"] == "REFUSE_CAPABILITY_PROJECTION_DRIFT"
        assert refusal["frontier"] is None
    finally:
        _remove(path)


def test_replay_is_exact_and_rejects_summary_or_digest_tamper() -> None:
    receipt = run_fixture()
    assert runner.verify_receipt(receipt, ROOT)
    replay = runner.replay_receipt(receipt, ROOT)
    assert replay["status"] == "PASS"
    assert replay["digest_match"] is True
    tampered = copy.deepcopy(receipt)
    tampered["semantic_inputs"]["capability_status"] = "PASS"
    assert not runner.verify_receipt(tampered, ROOT)
    assert runner.replay_receipt(tampered, ROOT)["status"] == "REFUSE"
    tampered_frontier = copy.deepcopy(receipt)
    tampered_frontier["frontier_digest"] = "0" * 64
    assert not runner.verify_receipt(tampered_frontier, ROOT)


def test_self_resealed_refusal_requires_exact_live_replay() -> None:
    bundle = runner.read_json(fixture("digger_proposals_v2.json"))
    bundle["children"][1] = None
    bundle["proposal_bundle_digest"] = runner.digest(
        {key: value for key, value in bundle.items() if key != "proposal_bundle_digest"}
    )
    path = _inside_copy("self-resealed-refusal.json", fixture("digger_proposals_v2.json"))
    try:
        path.write_text(json.dumps(bundle), encoding="utf-8")
        refusal = runner.run_wave(ROOT, proposals_path=path.relative_to(ROOT))
        assert refusal["status"] == "REFUSE"
        assert refusal["reason"] == "REFUSE_FORMALIZATION_INPUT"
        assert runner.verify_receipt(refusal, ROOT)

        forged = copy.deepcopy(refusal)
        forged["reason"] = "FRONTIER_COMPILED"
        forged["errors"] = []
        forged["error_digest"] = runner.digest([])
        runner._seal_receipt(forged)
        assert runner.verify_receipt(forged, ROOT) is False
    finally:
        _remove(path)


def test_cancellation_receipt_is_self_bound_and_has_no_frontier_write() -> None:
    receipt = run_fixture(cancel_requested=True)
    assert receipt["status"] == "CANCELLED"
    assert receipt["cancellation_state"] == "CANCELLED"
    assert receipt["frontier"] is None
    assert receipt["output_digest"] is None
    assert receipt["frontier_output_path"] is None
    assert receipt["output_artifact_write"] is False
    assert runner.verify_receipt(receipt, ROOT)


def test_semantic_contradiction_is_preserved_unresolved() -> None:
    bundle = runner.read_json(fixture("digger_proposals_v2.json"))
    bundle["children"][1]["predicates"].append({"predicate_id": "non_finite_probe_domain", "expression": "not finite(domain(probe_id))", "domain": ["side"], "status": "CANDIDATE"})
    bundle["proposal_bundle_digest"] = runner.digest({key: value for key, value in bundle.items() if key != "proposal_bundle_digest"})
    path = _inside_copy("contradiction.json", fixture("digger_proposals_v2.json"))
    try:
        path.write_text(json.dumps(bundle), encoding="utf-8")
        receipt = runner.run_wave(ROOT, proposals_path=path.relative_to(ROOT))
        assert receipt["status"] == "PASS"
        assert receipt["contradiction_scan"]["status"] == "SEMANTIC_CONTRADICTIONS_UNRESOLVED"
        assert receipt["frontier"]["unresolved_contradictions"]
        assert all(row["resolution"] == "UNRESOLVED" for row in receipt["frontier"]["unresolved_contradictions"])
        assert receipt["frontier"]["voting"] is False
        assert runner.verify_receipt(receipt, ROOT)
    finally:
        _remove(path)


def test_structural_duplicate_child_refuses() -> None:
    bundle = runner.read_json(fixture("digger_proposals_v2.json"))
    bundle["children"].append(copy.deepcopy(bundle["children"][0]))
    bundle["proposal_bundle_digest"] = runner.digest({key: value for key, value in bundle.items() if key != "proposal_bundle_digest"})
    path = _inside_copy("structural-duplicate.json", fixture("digger_proposals_v2.json"))
    try:
        path.write_text(json.dumps(bundle), encoding="utf-8")
        receipt = runner.run_wave(ROOT, proposals_path=path.relative_to(ROOT))
        assert receipt["status"] == "REFUSE"
        assert any("child_set_or_order" in error for error in receipt["errors"])
        assert receipt["frontier"] is None
    finally:
        _remove(path)
