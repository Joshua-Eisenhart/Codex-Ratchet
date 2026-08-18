from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest


CANDIDATE = Path(__file__).resolve().parents[1]
ROOT = CANDIDATE.parents[3]
RUNNER = CANDIDATE / "scripts" / "run_probe_map.py"
spec = importlib.util.spec_from_file_location("capability_probe_map_runner", RUNNER)
assert spec is not None and spec.loader is not None
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def _jax_interpreter() -> Path | None:
    candidates = []
    if os.environ.get("CB_JAX_PYTHON"):
        candidates.append(Path(os.environ["CB_JAX_PYTHON"]))
    candidates.extend(
        [
            Path.home() / ".local/share/jax-qit-stack/bin/python3",
        ]
    )
    for candidate in candidates:
        if candidate.is_absolute() and candidate.is_file():
            return candidate
    return None


def test_wave_definition_and_registry_are_inactive_and_explicit() -> None:
    wave = json.loads((CANDIDATE / "wave.json").read_text(encoding="utf-8"))
    registry = json.loads((CANDIDATE / "registry.json").read_text(encoding="utf-8"))
    assert wave["schema"] == "constraintbox.wave-definition.v1"
    assert wave["candidate_state"] == "NEW_CANDIDATE"
    assert wave["activated"] is False
    assert wave["promotion_allowed"] is False
    assert registry["candidate_state"] == "NEW_CANDIDATE"
    assert registry["promotion_allowed"] is False
    assert {
        "structured_probe_exact",
        "structured_probe_dual",
        "path_mass",
        "path_mass_replay",
        "external_jax_identity",
    } <= set(registry["capabilities"])
    assert wave["tool_bindings"]["z3_controller"]["registry"].endswith("controller_z3_runtime")
    assert wave["tool_bindings"]["cvc5_controller"]["registry"].endswith("controller_cvc5_runtime")
    assert wave["runtime_bindings"]["controller_runtime"]["libraries"] == [
        "controller_z3_runtime",
        "controller_cvc5_runtime",
    ]
    assert "sys.prefix" in wave["runtime_bindings"]["external_jax_runtime"]["prefix_rule"]


def test_candidate_has_no_forbidden_runtime_binding_fragments() -> None:
    # Keep the negative's needles split so this test can scan its own source.
    forbidden = (
        "".join(("code", "x", "-", "ratchet")),
        "".join(("system", "_", "v")),
        "".join(("super", "powers")),
        "".join(("Arch", "ive")),
    )
    for path in CANDIDATE.rglob("*"):
        if not path.is_file() or path.suffix in {".pyc", ".pyo"}:
            continue
        text = path.read_text(encoding="utf-8")
        lowered = text.casefold()
        assert all(term.casefold() not in lowered for term in forbidden), path


def test_local_fixtures_are_byte_identical_to_public_inputs() -> None:
    pairs = (
        (
            CANDIDATE / "fixtures" / "structured_open_bind_v1.json",
            ROOT / "constraint_box/integrated_system/fixtures/structured_open_bind_v1.json",
        ),
        (
            CANDIDATE / "fixtures" / "proposal_reference_policy_v1.json",
            ROOT / "constraint_box/fixtures/minilev/proposal_reference_policy_v1.json",
        ),
    )
    for candidate, public in pairs:
        assert hashlib.sha256(candidate.read_bytes()).digest() == hashlib.sha256(public.read_bytes()).digest()


@pytest.mark.skipif(_jax_interpreter() is None, reason="no declared external JAX interpreter")
def test_runtime_bindings_include_prefix_versions_digests_and_invocations() -> None:
    binding = runner.bind_capabilities(ROOT, _jax_interpreter())
    assert binding["status"] == "BOUND"
    runtime = binding["runtime_bindings"]
    assert runtime["environment_projection"]["credentials_passed"] is False
    controller = runtime["controller"]
    external = runtime["external_jax"]
    for identity in (controller, external):
        assert identity["status"] == "BOUND"
        assert identity["interpreter"]["sha256"]
        assert identity["runtime"]["sys_prefix"]
        assert identity["runtime"]["sys_base_prefix"]
        assert identity["invocation"]["argv"]
        assert identity["invocation"]["process"]["environment"]["sha256"] == runtime["environment_projection"]["sha256"]
    assert controller["runtime"]["libraries"]["z3"]["version"]
    assert controller["runtime"]["libraries"]["cvc5"]["version"]
    assert external["runtime"]["libraries"]["jax"]["version"]
    assert external["runtime"]["libraries"]["z3"]["version"]
    assert external["runtime"]["libraries"]["cvc5"]["version"]
    assert external["prefix_comparison"]["separate"] is True


def test_source_fixture_binding_and_non_null_structured_agreement_are_strict() -> None:
    binding = runner.bind_capabilities(ROOT, None)
    structured_fixture = CANDIDATE / "fixtures" / "structured_open_bind_v1.json"
    path_fixture = CANDIDATE / "fixtures" / "proposal_reference_policy_v1.json"
    exact_source = runner._bound_source_sha256(binding, "structured_probe_exact")
    dual_source = runner._bound_source_sha256(binding, "structured_probe_dual")
    path_source = runner._bound_source_sha256(binding, "path_mass")
    path_wrapper = runner._bound_wrapper_sha256(binding, "path_mass")
    replay_wrapper = runner._bound_wrapper_sha256(binding, "path_mass_replay")
    exact_fixture = runner.canonical_json_file_digest(structured_fixture)
    path_fixture_digest = runner.file_digest(path_fixture)
    exact = {"result": {"source_sha256": exact_source, "fixture_sha256": exact_fixture, "structured": {"ok": True}}}
    dual = {"result": {"source_sha256": dual_source, "fixture_sha256": exact_fixture, "structured": {"ok": True}}}
    path = {
        "source_sha256": path_source,
        "fixture_sha256": path_fixture_digest,
        "wrapper_sha256": path_wrapper,
        "replay_wrapper_sha256": replay_wrapper,
        "receipt": {},
    }
    assert runner.check_source_fixture_bindings(binding, exact, dual, path, structured_fixture, path_fixture)["all_pass"] is True
    bad = copy.deepcopy(exact)
    bad["result"]["source_sha256"] = "0" * 64
    assert runner.check_source_fixture_bindings(binding, bad, dual, path, structured_fixture, path_fixture)["all_pass"] is False
    bad_path = copy.deepcopy(path)
    bad_path["fixture_sha256"] = "0" * 64
    assert runner.check_source_fixture_bindings(binding, exact, dual, bad_path, structured_fixture, path_fixture)["all_pass"] is False
    bad_wrapper = copy.deepcopy(path)
    bad_wrapper["wrapper_sha256"] = "0" * 64
    assert runner.check_source_fixture_bindings(binding, exact, dual, bad_wrapper, structured_fixture, path_fixture)["all_pass"] is False
    assert runner.structured_results_agree({"result": {}}, {"result": {}}) is False
    assert runner.structured_results_agree({"result": {"structured": None}}, {"result": {"structured": None}}) is False


def test_negative_control_matrix_holds_or_refuses_incomplete_sets() -> None:
    good = [{"id": ident, "passed": True} for ident in runner.REQUIRED_NEGATIVE_CONTROL_IDS]
    assert runner.validate_negative_control_matrix(good)["status"] == "PASS"
    assert runner.validate_negative_control_matrix(good[:-1])["status"] == "HOLD"
    assert runner.validate_negative_control_matrix(good + [good[0]])["status"] == "HOLD"
    assert runner.validate_negative_control_matrix(good + [{"id": "unexpected", "passed": True}])["status"] == "REFUSE"


def test_replay_pass_requires_zero_process_and_three_way_hash_equality() -> None:
    good = {
        "receipt_sha256": "a" * 64,
        "replay": {
            "status": "PASS",
            "stored_receipt_sha256": "a" * 64,
            "replayed_receipt_sha256": "a" * 64,
            "process": {"returncode": 0},
        },
    }
    assert runner.replay_result_passes(good) is True
    nonzero = copy.deepcopy(good)
    nonzero["replay"]["process"]["returncode"] = 1
    assert runner.replay_result_passes(nonzero) is False
    mismatch = copy.deepcopy(good)
    mismatch["replay"]["replayed_receipt_sha256"] = "b" * 64
    assert runner.replay_result_passes(mismatch) is False
    original_mismatch = copy.deepcopy(good)
    original_mismatch["receipt_sha256"] = "c" * 64
    assert runner.replay_result_passes(original_mismatch) is False


def test_malformed_path_mass_request_is_typed_hold(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(command: list[str], **kwargs: object) -> dict[str, object]:
        output = Path(command[command.index("--out") + 1])
        output.write_text(json.dumps({"status": "PASS", "request": None}), encoding="utf-8")
        return {
            "returncode": 0,
            "stdout": "",
            "stderr": "",
            "timed_out": False,
            "environment": runner.environment_projection(),
            "stdout_sha256": runner.sha256_bytes(b""),
            "stderr_sha256": runner.sha256_bytes(b""),
        }

    monkeypatch.setattr(runner, "_run", fake_run)
    interpreter = _jax_interpreter() or Path(sys.executable)
    result = runner._run_path_mass(
        ROOT,
        CANDIDATE / "fixtures" / "proposal_reference_policy_v1.json",
        interpreter,
        tmp_path,
    )
    assert result["status"] == "HOLD"
    assert result["reason"] == "HOLD_PATH_MASS_RECEIPT_REQUEST_INVALID"
    assert result["request_mapping_valid"] is False


def test_drifted_public_wrapper_refuses_binding(monkeypatch: pytest.MonkeyPatch) -> None:
    real_digest = runner.file_digest
    wrapper_name = "run_constraint_path_mass.py"

    def drifted_digest(path: Path) -> str:
        if path.name == wrapper_name:
            return "0" * 64
        return real_digest(path)

    monkeypatch.setattr(runner, "file_digest", drifted_digest)
    binding = runner.bind_capabilities(ROOT, None)
    path_row = next(item for item in binding["capabilities"] if item["capability"] == "path_mass")
    replay_row = next(item for item in binding["capabilities"] if item["capability"] == "path_mass_replay")
    assert path_row["status"] == "REFUSE"
    assert replay_row["status"] == "REFUSE"
    assert path_row["reason"] == "REFUSE_PUBLIC_WRAPPER_DIGEST_MISMATCH"


def test_subprocess_environment_is_minimal_and_credential_free(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(command: list[str], **kwargs: object) -> Completed:
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return Completed()

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    observed = runner._run(["controller", "-I"], cwd=ROOT)
    assert set(captured["env"] or {}) == set(runner._SUBPROCESS_ENV)
    assert observed["environment"] == runner.environment_projection()
    assert observed["environment"]["credentials_passed"] is False


def test_external_alias_with_same_prefix_is_refused(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    alias = tmp_path / "external-alias-python"
    alias.symlink_to(Path(sys.executable))
    body = {
        "python_version": "3.13.6",
        "python_implementation": "cpython",
        "python_executable": str(alias),
        "sys_prefix": sys.prefix,
        "sys_base_prefix": sys.base_prefix,
        "libraries": {
            "jax": {"status": "BOUND", "version": "0.10.1", "jaxlib_version": "0.10.1", "device_count": 1},
            "z3": {"status": "BOUND", "version": "4.16.0"},
            "cvc5": {"status": "BOUND", "version": "1.3.3"},
        },
    }

    class Completed:
        returncode = 0
        stdout = json.dumps(body, sort_keys=True)
        stderr = ""

    monkeypatch.setattr(
        runner,
        "_run",
        lambda command, **kwargs: {
            "returncode": Completed.returncode,
            "stdout": Completed.stdout,
            "stderr": Completed.stderr,
            "timed_out": False,
            "environment": runner.environment_projection(),
            "stdout_sha256": runner.sha256_bytes(Completed.stdout.encode()),
            "stderr_sha256": runner.sha256_bytes(b""),
        },
    )
    result = runner.external_jax_identity(alias, ROOT)
    assert result["status"] == "HOLD"
    assert result["reason"] == "REFUSE_JAX_RUNTIME_SAME_PREFIX"


@pytest.mark.skipif(_jax_interpreter() is None, reason="no declared external JAX interpreter")
def test_candidate_runs_exact_dual_path_mass_and_replay() -> None:
    receipt = runner.run_candidate(ROOT, _jax_interpreter())
    assert receipt["status"] == "PASS"
    assert receipt["candidate_state"] == "NEW_CANDIDATE"
    assert receipt["activated"] is False
    assert receipt["promotion_allowed"] is False
    assert runner.verify_receipt(receipt)
    assert receipt["runtime_bindings"]["requirements"]["external_jax_runtime"] == "BOUND"
    assert receipt["environment_projection"]["credentials_passed"] is False
    assert [child["status"] for child in receipt["children"]] == ["PASS", "PASS", "PASS"]
    assert receipt["structured_crosscheck"]["exact_dual_structured_metrics_agree"] is True
    assert receipt["children"][2]["replay"]["status"] == "PASS"
    assert receipt["children"][2]["replay"]["stored_receipt_sha256"] == receipt["children"][2]["replay"]["replayed_receipt_sha256"]
    assert receipt["negative_controls"]["all_pass"] is True
    assert receipt["negative_control_matrix_exact"]["status"] == "PASS"
    assert receipt["source_fixture_binding"]["all_pass"] is True
    assert receipt["source_fixture_binding"]["checks"]["path_mass_wrapper"] is True
    assert receipt["children"][2]["wrapper_sha256"]
    assert receipt["capability_map"]["schema"] == "constraintbox.capability-map.v1"
    assert {entry["capability"] for entry in receipt["capability_map"]["entries"]} == {
        "structured_probe_exact",
        "structured_probe_dual",
        "path_mass",
        "path_mass_replay",
    }
    assert receipt["optional_manifold_6144_scratch"]["status"] == "NOT_CONSUMED"
    assert receipt["preload_receipts"] == []
    assert receipt["provider_call_receipt"] is None
    assert isinstance(receipt["output_digest"], str)
    assert all(value is False for value in receipt["writes"].values())


@pytest.mark.skipif(_jax_interpreter() is None, reason="no declared external JAX interpreter")
def test_candidate_receipt_is_deterministic_for_same_inputs() -> None:
    first = runner.run_candidate(ROOT, _jax_interpreter())
    second = runner.run_candidate(ROOT, _jax_interpreter())
    assert first == second
    assert first["receipt_sha256"] == second["receipt_sha256"]


def test_missing_external_runtime_holds_without_activation() -> None:
    receipt = runner.run_candidate(ROOT, None)
    assert receipt["status"] == "HOLD"
    assert receipt["candidate_state"] == "NEW_CANDIDATE"
    assert receipt["activated"] is False
    assert receipt["promotion_allowed"] is False
    assert receipt["capability_binding"]["status"] == "HOLD"
    assert runner.verify_receipt(receipt)


def test_controller_path_is_not_accepted_as_external_runtime() -> None:
    result = runner.external_jax_identity(Path(sys.executable), ROOT)
    assert result["status"] == "HOLD"
    assert result["reason"] == "REFUSE_JAX_INTERPRETER_NOT_EXTERNAL"


def test_receipt_digest_tampering_is_detected() -> None:
    receipt = runner.run_candidate(ROOT, None)
    tampered = copy.deepcopy(receipt)
    tampered["claim_ceiling"] = "promotion"
    assert runner.verify_receipt(receipt)
    assert not runner.verify_receipt(tampered)
