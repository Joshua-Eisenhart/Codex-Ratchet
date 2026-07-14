from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
DEEP_STACK = ROOT / "system_v5/ops/tooling/deep_stack_stress_20260714"
REGISTRY = DEEP_STACK / "registry/tool_roster_v1.json"
EDGES = DEEP_STACK / "registry/integration_edges_v1.json"
SCHEMA_DIR = DEEP_STACK / "schemas"
FINAL_ESTATE = DEEP_STACK / "results/deep_stack_estate_lev.json"
FINAL_VERDICT = DEEP_STACK / "results/deep_stack_estate_lev_verdict.json"
VALIDATOR = (
    ROOT
    / "system_v5/codex_skills/codex-ratchet-deep-stack-stress/scripts/validate_deep_stack_receipt.py"
)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), path
    return value


def load_validator_module():
    spec = importlib.util.spec_from_file_location("deep_stack_receipt_validator_tested", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR_MODULE = load_validator_module()


def materialize_minimal_fixture(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    estate, registry, edges = VALIDATOR_MODULE.minimal_selftest_fixture()
    source_bytes = estate.pop("_selftest_source_bytes")
    for name, content in source_bytes.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    return estate, registry, edges


def materialize_production_shape_fixture(
    tmp_path: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Make the minimal fixture exercise production-only raw-evidence gates."""
    estate, registry, edges = materialize_minimal_fixture(tmp_path)
    estate["_exercise_production_gates"] = True
    registry["tools"][0]["representative_sim"] = {"path": "probe.py"}

    receipt = estate["tool_receipts"][0]
    executable = str(Path(sys.executable).resolve())
    version_result = subprocess.run(
        [executable, "--version"],
        text=True,
        capture_output=True,
        check=True,
    )
    runtime_version = (version_result.stdout + version_result.stderr).strip()
    receipt["runtime_binding"].update(
        {
            "executable": executable,
            "executable_realpath": executable,
            "probe_executable": executable,
            "probe_executable_realpath": executable,
            "executable_sha256": VALIDATOR_MODULE.sha256_file(Path(executable)),
            "executable_realpath_sha256": VALIDATOR_MODULE.sha256_file(Path(executable)),
            "probe_executable_sha256": VALIDATOR_MODULE.sha256_file(Path(executable)),
            "probe_executable_realpath_sha256": VALIDATOR_MODULE.sha256_file(Path(executable)),
            "executable_matches_probe": True,
            "executable_hash_matches_probe": True,
            "runtime_version": runtime_version,
            "probe_runtime_version": runtime_version,
            "runtime_version_matches_probe": True,
        }
    )

    raw_roles = (
        "python_core",
        "julia_core",
        "jl_tensorkit",
        "jl_pepskit",
        "jl_intervalarithmetic",
        "cross_tensor",
        "cross_dynamics",
    )
    raw_root = tmp_path / "raw" / estate["run_id"]
    raw_root.mkdir(parents=True)
    raw_receipts: dict[str, str] = {}
    raw_bindings: list[dict[str, Any]] = []
    producer_commands: list[dict[str, Any]] = []
    probe_path = tmp_path / "probe.py"
    probe_argument = str(probe_path)
    for role in raw_roles:
        raw_path = raw_root / f"{role}.json"
        if role == "python_core":
            raw_call = {
                "qualified_api": "fixture.api",
                "input_object": "x",
                "output_object": "y",
                "gates": ["positive"],
                "executed": True,
                "load_bearing": True,
                "raw_probe_recorded": True,
            }
            raw_cases = {
                name: {
                    "passed": True,
                    "observed": f"{name} ok",
                    "expected": f"{name} expected",
                }
                for name in VALIDATOR_MODULE.REQUIRED_CASES
            }
            raw_demotion = {
                "passed": True,
                "method": "erase fixture API call",
                "observed": "control failed as required",
            }
            raw_payload = {
                "rows": [
                    {
                        "tool": "fixture",
                        "tool_calls": [raw_call],
                        "cases": raw_cases,
                        "demotion": raw_demotion,
                    }
                ]
            }
            normalized_cases = {
                name: VALIDATOR_MODULE.normalized_case_from_raw(
                    raw_cases[name], name, "fixture.api"
                )
                for name in VALIDATOR_MODULE.REQUIRED_CASES
            }
            receipt["cases"] = normalized_cases
            receipt["demotion"] = {
                "passed": True,
                "method": raw_demotion["method"],
                "observed": raw_demotion,
                "raw_demotion_sha256": VALIDATOR_MODULE.canonical_json_sha256(raw_demotion),
            }
            receipt["tool_calls"] = [
                VALIDATOR_MODULE.expected_normalized_tool_call(
                    raw_call,
                    cases=normalized_cases,
                    probe_source_sha256=receipt["source_binding"]["probe_sha256"],
                )
            ]
        else:
            raw_payload = {"role": role}
        raw_path.write_text(json.dumps(raw_payload) + "\n", encoding="utf-8")
        relative_path = raw_path.relative_to(tmp_path).as_posix()
        raw_receipts[role] = relative_path
        raw_hash = VALIDATOR_MODULE.sha256_file(raw_path)
        producer_command = {
            "role": "raw_producer",
            "raw_role": role,
            "command": [executable, probe_argument],
            "command_line": f"{executable} {probe_argument}",
            "exit_code": 0,
            "timed_out": False,
            "process_launcher_path": executable,
            "process_launcher_realpath": executable,
            "process_launcher_sha256": VALIDATOR_MODULE.sha256_file(Path(executable)),
            "process_launcher_realpath_sha256": VALIDATOR_MODULE.sha256_file(Path(executable)),
            "output_path": relative_path,
            "output_exists": True,
            "output_sha256": raw_hash,
            "output_created_after_explicit_unlink": True,
            "output_boundary_cleared_before_execution": True,
            "preexisting_output_removed": False,
            "invoked_source_path": "probe.py",
            "invoked_source_argument": probe_argument,
            "invoked_source_sha256": VALIDATOR_MODULE.sha256_file(probe_path),
            "invoked_source_argument_present": True,
        }
        producer_commands.append(producer_command)
        raw_bindings.append(
            {
                "role": role,
                "path": relative_path,
                "exists": True,
                "sha256": raw_hash,
                "producer_command_count": 1,
                "producer_bound": True,
                "producer_exit_code": 0,
                "producer_timed_out": False,
                "producer_output_path": relative_path,
                "producer_output_sha256": raw_hash,
                "producer_output_created_after_explicit_unlink": True,
                "producer_output_boundary_cleared_before_execution": True,
                "producer_invoked_source_path": "probe.py",
                "producer_invoked_source_sha256": VALIDATOR_MODULE.sha256_file(probe_path),
                "producer_invoked_source_argument_present": True,
            }
        )

    representative = receipt["representative_sim"]
    python_binding = next(item for item in raw_bindings if item["role"] == "python_core")
    python_path = tmp_path / python_binding["path"]
    representative["emitted_artifacts"] = [
        {
            "path": python_binding["path"],
            "exists": True,
            "changed_or_created": True,
            "created_after_explicit_unlink": True,
            "sha256": VALIDATOR_MODULE.sha256_file(python_path),
            "size": python_path.stat().st_size,
            "json_object_parsed": True,
        }
    ]
    representative["output_contract_paths"] = [python_binding["path"]]
    representative["emitted_output_contract_paths"] = [python_binding["path"]]
    representative["output_contract_exact"] = True
    representative["mapped_tool_evidence"] = {
        "mode": "registry_single_tool_source_contract",
        "registry_tool_ids_for_source": ["fixture"],
        "registry_aliases": ["fixture"],
        "structured_artifact_identities": ["fixture"],
        "matched_structured_identities": ["fixture"],
        "passed": True,
        "claim_ceiling": VALIDATOR_MODULE.MAPPED_TOOL_CLAIM_CEILING,
    }
    representative_command = copy.deepcopy(estate["commands"][0])
    estate["commands"] = [
        *producer_commands,
        representative_command,
        copy.deepcopy(representative_command),
        copy.deepcopy(representative_command),
    ]
    estate["raw_receipts"] = raw_receipts
    estate["raw_receipt_bindings"] = raw_bindings
    estate["representative_execution_receipts"] = [copy.deepcopy(representative)]
    return estate, registry, edges


def run_estate_validator(
    tmp_path: Path,
    estate: dict[str, Any],
    registry: dict[str, Any],
    edges: dict[str, Any],
    *,
    require_operational_pass: bool = False,
) -> tuple[subprocess.CompletedProcess[str], dict[str, Any]]:
    verdict = VALIDATOR_MODULE.validate_estate(
        estate,
        registry,
        edges,
        repo_root=tmp_path,
        selftest_mode=True,
    )
    returncode = 0
    if not verdict["receipt_valid"]:
        returncode = 2
    elif require_operational_pass and not verdict["operational_pass"]:
        returncode = 1
    result = subprocess.CompletedProcess(
        args=[str(VALIDATOR)],
        returncode=returncode,
        stdout=json.dumps(verdict),
        stderr="",
    )
    return result, verdict


def test_registry_ids_and_declared_counts_are_exactly_unique() -> None:
    registry = load_json(REGISTRY)
    rows = registry["tools"]
    tool_ids = [row["tool_id"] for row in rows]
    bucket_counts = Counter(row["bucket"] for row in rows)

    assert len(tool_ids) == len(set(tool_ids))
    assert sum(registry["counts"].values()) == len(rows)
    assert dict(bucket_counts) == registry["counts"]
    assert all(tool_id and tool_id.strip() == tool_id for tool_id in tool_ids)


def test_edge_registry_and_current_estate_preserve_exact_membership_order() -> None:
    registry = load_json(REGISTRY)
    edges = load_json(EDGES)
    estate = load_json(FINAL_ESTATE) if FINAL_ESTATE.is_file() else None
    tool_rows = {row["tool_id"]: row for row in registry["tools"]}
    edge_rows = edges["edges"]
    edge_ids = [row["id"] for row in edge_rows]

    assert len(edge_ids) == len(set(edge_ids))
    for edge in edge_rows:
        assert edge["members"]
        assert len(edge["members"]) == len(set(edge["members"]))
        assert all(member in tool_rows for member in edge["members"])

    edge_by_id = {row["id"]: row for row in edge_rows}
    for tool_id, row in tool_rows.items():
        for edge_id in row.get("integration_edge_ids", []):
            assert edge_id in edge_by_id
            assert tool_id in edge_by_id[edge_id]["members"]

    if estate is None:
        pytest.skip("final Lev estate is not present yet")
    receipt_by_id = {row["tool_id"]: row for row in estate["tool_receipts"]}
    edge_receipt_by_id = {
        row["edge_id"]: row for row in estate["integration_edge_receipts"]
    }
    assert set(edge_receipt_by_id) == set(edge_ids)
    for edge in edge_rows:
        receipt = edge_receipt_by_id[edge["id"]]
        assert receipt["members"] == edge["members"]
        assert receipt["family"] == edge["family"]
        assert receipt["case_id"] == edge["case_id"]
        for member in edge["members"]:
            observed = [
                item["edge_id"]
                for item in receipt_by_id[member].get("adjacent_integrations", [])
            ]
            assert observed.count(edge["id"]) == 1


def test_all_deep_stack_schemas_are_valid_draft_2020_12() -> None:
    schema_paths = sorted(SCHEMA_DIR.glob("*.schema.json"))
    assert schema_paths, SCHEMA_DIR
    for path in schema_paths:
        schema = load_json(path)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        Draft202012Validator.check_schema(schema)


def test_validator_selftest_exercises_all_fail_closed_mutations(tmp_path: Path) -> None:
    output = tmp_path / "selftest.json"
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), "selftest", "--out", str(output)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    stdout_verdict = json.loads(result.stdout)
    assert stdout_verdict == load_json(output)
    assert stdout_verdict["all_pass"] is True
    assert stdout_verdict["passed_count"] == stdout_verdict["case_count"]
    assert {case["id"] for case in stdout_verdict["cases"]} == {
        "baseline_valid",
        "missing_negative",
        "import_only",
        "false_demotion",
        "unknown_edge",
        "stale_hash",
        "science_promotion",
        "claude_bridge",
        "duplicate_tool",
        "missing_edge_receipt",
        "invented_tool_call",
        "hidden_raw_reuse",
        "representative_without_execution_receipt",
        "raw_tool_call_hash_missing",
    }


def test_honest_red_receipt_is_valid_but_strict_operational_gate_is_red(
    tmp_path: Path,
) -> None:
    estate, registry, edges = materialize_minimal_fixture(tmp_path)
    receipt = estate["tool_receipts"][0]
    receipt["cases"]["stress"]["passed"] = False
    receipt["cases"]["stress"]["observed"] = "bounded stress exposed a real red"
    receipt["tool_calls"][0]["case_bindings"]["stress"]["passed"] = False
    receipt["verdict"].update(
        {"receipt_valid": True, "operational_status": "red", "operational_pass": False}
    )

    permissive, permissive_verdict = run_estate_validator(
        tmp_path, estate, registry, edges
    )
    strict, strict_verdict = run_estate_validator(
        tmp_path,
        estate,
        registry,
        edges,
        require_operational_pass=True,
    )

    assert permissive.returncode == 0, permissive.stdout + permissive.stderr
    assert permissive_verdict["receipt_valid"] is True
    assert permissive_verdict["operational_pass"] is False
    assert permissive_verdict["operational_red_tools"] == ["fixture"]
    assert permissive_verdict["findings"] == []
    assert strict.returncode == 1, strict.stdout + strict.stderr
    assert strict_verdict == permissive_verdict


def test_validator_rejects_invented_tool_call_not_bound_to_raw_probe(
    tmp_path: Path,
) -> None:
    estate, registry, edges = materialize_minimal_fixture(tmp_path)
    invented_call = copy.deepcopy(estate["tool_receipts"][0]["tool_calls"][0])
    invented_call.update(
        {
            "qualified_api": "invented.module.fabricated_api",
            "input_object": "fabricated input",
            "output_object": "fabricated output",
            "gates": ["fabricated gate"],
        }
    )
    estate["tool_receipts"][0]["tool_calls"].append(invented_call)

    result, verdict = run_estate_validator(tmp_path, estate, registry, edges)

    assert result.returncode == 2, result.stdout + result.stderr
    assert verdict["receipt_valid"] is False
    assert verdict["operational_pass"] is False


def test_validator_rejects_raw_reuse_hidden_in_nested_command_metadata(
    tmp_path: Path,
) -> None:
    estate, registry, edges = materialize_production_shape_fixture(tmp_path)
    baseline, baseline_verdict = run_estate_validator(
        tmp_path, estate, registry, edges, require_operational_pass=True
    )
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    assert baseline_verdict["operational_pass"] is True

    estate["commands"][0]["provenance"] = {
        "reused_raw": estate["raw_receipts"]["python_core"]
    }
    result, verdict = run_estate_validator(tmp_path, estate, registry, edges)

    assert result.returncode == 2, result.stdout + result.stderr
    assert verdict["receipt_valid"] is False
    assert verdict["operational_pass"] is False


def test_validator_rejects_tool_call_probe_source_hash_mismatch(
    tmp_path: Path,
) -> None:
    estate, registry, edges = materialize_minimal_fixture(tmp_path)
    estate["tool_receipts"][0]["tool_calls"][0]["probe_source_sha256"] = "0" * 64

    result, verdict = run_estate_validator(tmp_path, estate, registry, edges)

    assert result.returncode == 2, result.stdout + result.stderr
    assert verdict["receipt_valid"] is False
    assert any(
        "tool_calls[0].probe_source_sha256 must match source binding" in finding
        for finding in verdict["findings"]
    )


def test_policy_red_receipt_blocks_strict_operational_gate(
    tmp_path: Path,
) -> None:
    estate, registry, edges = materialize_minimal_fixture(tmp_path)
    policy_row = {
        "tool_id": "policy-fixture",
        "package": "policy-fixture",
        "bucket": "candidate_missing",
        "family": "fixture-policy",
        "runtime_id": "python_canonical",
        "requires_deep_stress": False,
        "integration_edge_ids": [],
        "_selftest_fixture": True,
    }
    registry["tools"].append(policy_row)
    policy_receipt = copy.deepcopy(estate["tool_receipts"][0])
    policy_receipt.update(
        {
            "receipt_id": "fixture-run:policy-fixture",
            "tool_id": "policy-fixture",
            "package": "policy-fixture",
            "bucket": "candidate_missing",
            "family": "fixture-policy",
            "policy_check": {
                "passed": False,
                "policy": "candidate remains unavailable and non-operational",
                "observed": "policy red preserved",
            },
        }
    )
    policy_receipt["verdict"].update(
        {
            "receipt_valid": True,
            "operational_status": "policy_red",
            "operational_pass": False,
        }
    )
    estate["tool_receipts"].append(policy_receipt)
    estate["producer_summary"] = {
        "operational_red_count": 0,
        "policy_red_count": 0,
    }

    permissive, permissive_verdict = run_estate_validator(
        tmp_path, estate, registry, edges
    )
    strict, strict_verdict = run_estate_validator(
        tmp_path,
        estate,
        registry,
        edges,
        require_operational_pass=True,
    )

    assert permissive.returncode == 0, permissive.stdout + permissive.stderr
    assert permissive_verdict["receipt_valid"] is True
    assert permissive_verdict["operational_pass"] is False
    assert permissive_verdict["policy_red_tools"] == ["policy-fixture"]
    assert strict.returncode == 1, strict.stdout + strict.stderr
    assert strict_verdict == permissive_verdict


def test_validator_rejects_missing_raw_receipt_binding(
    tmp_path: Path,
) -> None:
    estate, registry, edges = materialize_production_shape_fixture(tmp_path)
    baseline, baseline_verdict = run_estate_validator(
        tmp_path, estate, registry, edges, require_operational_pass=True
    )
    assert baseline.returncode == 0, baseline.stdout + baseline.stderr
    assert baseline_verdict["operational_pass"] is True

    estate["raw_receipt_bindings"] = [
        binding
        for binding in estate["raw_receipt_bindings"]
        if binding["role"] != "cross_dynamics"
    ]
    result, verdict = run_estate_validator(tmp_path, estate, registry, edges)

    assert result.returncode == 2, result.stdout + result.stderr
    assert verdict["receipt_valid"] is False
    assert any(
        "raw_receipt_bindings must exactly cover seven execution roles" in finding
        for finding in verdict["findings"]
    )


def test_validator_rejects_representative_sim_marked_executed_without_receipt_fields(
    tmp_path: Path,
) -> None:
    estate, registry, edges = materialize_minimal_fixture(tmp_path)
    representative = estate["tool_receipts"][0]["representative_sim"]
    representative.update(
        {
            "executed": True,
            "operational_execution_pass": True,
        }
    )
    for key in (
        "command",
        "exit_code",
        "execution_source_sha256",
        "emitted_artifacts",
    ):
        representative.pop(key, None)

    result, verdict = run_estate_validator(tmp_path, estate, registry, edges)

    assert result.returncode == 2, result.stdout + result.stderr
    assert verdict["receipt_valid"] is False
    assert verdict["operational_pass"] is False


Mutation = Callable[[dict[str, Any]], None]


def remove_tool_receipt(estate: dict[str, Any]) -> None:
    estate["tool_receipts"] = []


def remove_required_case(estate: dict[str, Any]) -> None:
    estate["tool_receipts"][0]["cases"].pop("negative")


def stale_probe_hash(estate: dict[str, Any]) -> None:
    estate["tool_receipts"][0]["source_binding"]["probe_sha256"] = "0" * 64


def duplicate_tool_receipt(estate: dict[str, Any]) -> None:
    estate["tool_receipts"].append(copy.deepcopy(estate["tool_receipts"][0]))


def enable_claude_bridge(estate: dict[str, Any]) -> None:
    estate["claude_bridge_used"] = True


def promote_science_claim(estate: dict[str, Any]) -> None:
    estate["scientific_claim_proven"] = True


def enable_promotion(estate: dict[str, Any]) -> None:
    estate["promotion_allowed"] = True


@pytest.mark.parametrize(
    ("mutation", "finding"),
    [
        (remove_tool_receipt, "missing registry rows"),
        (remove_required_case, "cases.negative.passed must be boolean"),
        (stale_probe_hash, "bound source hash mismatch"),
        (duplicate_tool_receipt, "duplicate tool ids"),
        (enable_claude_bridge, "claude_bridge_used must be false"),
        (promote_science_claim, "scientific_claim_proven must be false"),
        (enable_promotion, "promotion_allowed must be false"),
    ],
    ids=[
        "missing-tool",
        "missing-case",
        "stale-source",
        "duplicate-tool",
        "claude-bridge",
        "science-claim",
        "promotion",
    ],
)
def test_validator_rejects_integrity_and_promotion_mutations(
    tmp_path: Path,
    mutation: Mutation,
    finding: str,
) -> None:
    estate, registry, edges = materialize_minimal_fixture(tmp_path)
    mutation(estate)

    result, verdict = run_estate_validator(tmp_path, estate, registry, edges)

    assert result.returncode == 2, result.stdout + result.stderr
    assert verdict["receipt_valid"] is False
    assert verdict["operational_pass"] is False
    assert any(finding in item for item in verdict["findings"]), verdict["findings"]


def test_final_lev_estate_is_the_reviewed_139_95_29_green_golden() -> None:
    if not FINAL_ESTATE.is_file() or not FINAL_VERDICT.is_file():
        pytest.skip("final Lev estate and validation golden are not present yet")
    estate = load_json(FINAL_ESTATE)
    saved_verdict = load_json(FINAL_VERDICT)

    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "estate",
            "--receipt",
            str(FINAL_ESTATE),
            "--registry",
            str(REGISTRY),
            "--edges",
            str(EDGES),
            "--repo-root",
            str(ROOT),
            "--require-operational-pass",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    live_verdict = json.loads(result.stdout)
    assert live_verdict == saved_verdict
    assert live_verdict["receipt_valid"] is True
    assert live_verdict["operational_pass"] is True
    assert live_verdict["findings"] == []
    assert len(estate["tool_receipts"]) == 139
    assert sum(
        row["verdict"]["operational_pass"] is True
        for row in estate["tool_receipts"]
    ) == 95
    assert len(estate["integration_edge_receipts"]) == 29
    assert estate["producer_summary"]["registry_tool_count"] == 139
    assert estate["producer_summary"]["deep_stress_tool_count"] == 95
    assert estate["producer_summary"]["integration_edge_count"] == 29
    assert estate["producer_summary"]["operational_red_count"] == 0
    assert estate["producer_summary"]["operational_red_edge_count"] == 0
