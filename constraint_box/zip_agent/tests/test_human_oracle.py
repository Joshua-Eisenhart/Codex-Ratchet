from __future__ import annotations

import io
import importlib.metadata
import json
import zipfile
from functools import lru_cache

import pytest
from pydantic import ValidationError

from constraintbox_zip_agent.cache import cache_result
from constraintbox_zip_agent.operation_probe_field import build_operation_probe_field_packet

from constraintbox_zip_agent.human_oracle import (
    MAP_DELTA_OUTPUT_PATH,
    OUTPUT_PATH,
    UPDATED_MAP_OUTPUT_PATH,
    HumanOracleSurface,
    build_human_oracle_packet,
    build_human_oracle_map_update_packet,
    human_oracle_identity,
    render_human_oracle,
)
from constraintbox_zip_agent.protocol import (
    ZipJobRefusal,
    canonical_json_bytes,
    deterministic_zip,
    sha256_bytes,
    validate_return_zip,
)
from constraintbox_zip_agent.runtime import execute_packet
from constraintbox_zip_agent.work_cycle import build_work_cycle_packet


@lru_cache(maxsize=2)
def _map_pair(mapped_pydantic: bool = True) -> tuple[bytes, bytes, bytes]:
    def tool(distribution: str, import_name: str) -> dict[str, object]:
        return {
            "locked_distribution": distribution,
            "locked_version": importlib.metadata.version(distribution),
            "import_names": [import_name],
        }

    packet = build_work_cycle_packet(
        prompt=b"Map the exact renderer dependencies without declaring a core.",
        tool_manifest=json.dumps(
            {
                "tools": [
                    tool("jsonschema", "jsonschema"),
                    tool("pydantic", "pydantic"),
                    tool("sympy", "sympy"),
                ]
            }
        ).encode(),
        prior_field_summary=json.dumps(
            {
                "tool_projection": [
                    {
                        "tool_id": "jsonschema",
                        "observations": 11,
                        "local_centrality": 0.4,
                    },
                    *(
                        [
                            {
                                "tool_id": "pydantic",
                                "observations": 13,
                                "local_centrality": 0.5,
                            }
                        ]
                        if mapped_pydantic
                        else []
                    ),
                ]
            }
        ).encode(),
        seed=17,
        jobs=2,
        pair_samples=3,
    )
    returned = execute_packet(packet).return_zip_bytes
    with zipfile.ZipFile(io.BytesIO(returned), "r") as archive:
        quotient = archive.read("output/measured_quotient.json")
    return packet, returned, quotient


@lru_cache(maxsize=2)
def _operation_pair(mapped_pydantic: bool = True) -> tuple[bytes, bytes]:
    def tool(
        tool_id: str,
        distribution: str,
        import_name: str,
        operation_probe: dict[str, object],
    ) -> dict[str, object]:
        return {
            "tool_id": tool_id,
            "locked_distribution": distribution,
            "locked_version": importlib.metadata.version(distribution),
            "import_names": [import_name],
            "operation_probe": operation_probe,
        }

    manifest = canonical_json_bytes(
        {
            "tools": [
                tool(
                    "jsonschema",
                    "jsonschema",
                    "jsonschema",
                    {
                        "module": "jsonschema",
                        "callable": "validate",
                        "positive": {"args": [1, {"type": "integer"}]},
                        "mutations": [
                            {
                                "name": "wrong-instance",
                                "args": ["one", {"type": "integer"}],
                                "expected": "REFUSED",
                            }
                        ],
                        "boundaries": [
                            {"name": "zero", "args": [0, {"type": "integer"}]}
                        ],
                        "shared_input": {"args": [1, {"type": "integer"}]},
                    },
                ),
                tool(
                    "pydantic",
                    "pydantic",
                    "pydantic",
                    {
                        "module": "pydantic",
                        "callable": "RootModel.model_validate_json",
                        "positive": {"args": ["{\"value\":1}"]},
                        "mutations": [
                            {"name": "invalid-json", "args": ["{"], "expected": "REFUSED"}
                        ],
                        "boundaries": [{"name": "null", "args": ["null"]}],
                        "shared_input": {"args": ["{\"value\":1}"]},
                    },
                )
                if mapped_pydantic
                else {
                    "tool_id": "pydantic",
                    "locked_distribution": "pydantic",
                    "locked_version": importlib.metadata.version("pydantic"),
                    "import_names": ["pydantic"],
                },
            ]
        }
    )
    request = canonical_json_bytes(
        {
            "schema": "constraintbox.operation_probe_field_request.v1",
            "seed": 41,
            "cohort_size": 2,
            "cohort_limit": 2,
            "max_pairs": 1,
            "max_ablation_tools": 2,
        }
    )
    packet = build_operation_probe_field_packet(
        request=request,
        manifest=manifest,
        operation_catalog=b"{}",
        job_id="human-oracle-operation-evidence",
    )
    return packet, execute_packet(packet).return_zip_bytes


def _surface() -> dict[str, object]:
    return {
        "schema": "constraintbox.human-oracle-surface.v2",
        "run_id": "oracle-1",
        "state": "HUMAN_CONFIRMATION_REQUIRED",
        "headline": "Choose the next ConstraintBox work packet",
        "summary": "Three independent routes returned evidence, but one nested-agent requirement remains unmet.",
        "closing_summary": "The next accepted action must close the nesting gap and retain the raw prompt.",
        "raw_prompt_sha256": "1" * 64,
        "map_snapshot_sha256": __import__("hashlib").sha256(_map_pair()[2]).hexdigest(),
        "map_return_sha256": __import__("hashlib").sha256(_map_pair()[1]).hexdigest(),
        "required_map_tool_ids": ["jsonschema", "pydantic"],
        "execution": {
            "model_calls": 3,
            "agents": 3,
            "subagents": 0,
            "subsubagents": 0,
            "deeper_agents": 0,
            "tool_operations": 7,
            "retries": 1,
            "failures": 1,
            "source_receipt_sha256": "2" * 64,
        },
        "models": [
            {
                "route_id": f"route-{index}",
                "provider": f"fixture-provider-{index}",
                "model_requested": f"requested-{index}",
                "model_observed": f"observed-{index}",
                "call_count": 1,
                "status": "COMPLETED",
                "receipt_sha256": str(index) * 64,
            }
            for index in (3, 4, 5)
        ],
        "agent_runs": [
            {
                "agent_id": "agent-3",
                "parent_agent_id": None,
                "depth": 0,
                "status": "COMPLETED",
                "model_route_id": "route-3",
                "receipt_sha256": "6" * 64,
            },
            {
                "agent_id": "agent-4",
                "parent_agent_id": None,
                "depth": 0,
                "status": "COMPLETED",
                "model_route_id": "route-4",
                "receipt_sha256": "7" * 64,
            },
            {
                "agent_id": "agent-5",
                "parent_agent_id": None,
                "depth": 0,
                "status": "COMPLETED",
                "model_route_id": "route-5",
                "receipt_sha256": "8" * 64,
            },
        ],
        "python_tools": [
            {
                "tool_id": "python.probe-runner",
                "operation": "probe",
                "call_count": 4,
                "status": "COMPLETED",
                "receipt_sha256": "9" * 64,
            },
            {
                "tool_id": "python.form-compiler",
                "operation": "render",
                "call_count": 3,
                "status": "COMPLETED",
                "receipt_sha256": "a" * 64,
            },
        ],
        "skills": [
            {
                "skill_id": "cb-strategy-wave",
                "call_count": 1,
                "status": "COMPLETED",
                "receipt_sha256": "b" * 64,
            }
        ],
        "waves": [
            {
                "wave_id": "strategy-1",
                "profile": "LEAN",
                "status": "COMPLETED",
                "receipt_sha256": "c" * 64,
            }
        ],
        "minimums": {
            "profile_id": "lean-multimodel-v1",
            "distinct_providers": 3,
            "model_calls": 3,
            "agents": 3,
            "subagents": 0,
            "subsubagents": 0,
            "python_tool_calls": 7,
            "required_skill_ids": ["cb-strategy-wave"],
            "required_wave_ids": ["strategy-1"],
        },
        "minimums_satisfied": True,
        "what_ran": [
            "Three prompt candidates were returned as declared files.",
            "Seven deterministic checks completed.",
        ],
        "failures_and_unknowns": [
            {
                "reason_code": "MMM_EFFECT_UNPROVED",
                "plain_language": "MMM bytes were delivered, but their influence was not measured.",
                "impact": "Do not attribute a candidate's quality to its assigned MMM.",
                "next_test": "Run a registered same-model A/B comparison.",
            }
        ],
        "decision_needed": "Choose, edit, combine, reject, or request another round.",
        "next_prompt_options": [
            {
                "option_id": "broad",
                "title": "Build and test the complete narrow slice",
                "prompt_text": "Implement the operator command and its refusal tests, then run the failure council.",
                "combines_actions": ["implement operator command", "run refusal tests", "run failure council"],
                "framing_mmm_ids": ["systems", "popper"],
                "preserves_raw_prompt": True,
            },
            {
                "option_id": "audit",
                "title": "Close the authority seam first",
                "prompt_text": "Capture relay and cancellation receipts, then implement the prompt handshake.",
                "combines_actions": ["capture hook receipts", "implement prompt handshake"],
                "framing_mmm_ids": ["hume", "orwell"],
                "preserves_raw_prompt": True,
            },
        ],
        "claim_ceiling": "human selection surface only",
        "execution_authorized": False,
        "promotion_allowed": False,
    }


def test_renderer_exposes_counts_failures_and_combined_prompts() -> None:
    rendered = render_human_oracle(_surface()).decode()
    assert "3 agents · 0 subagents · 0 subsubagents" in rendered
    assert "Three independent routes returned evidence" in rendered
    assert "python.probe-runner" in rendered
    assert "cb-strategy-wave" in rendered
    assert "Proposed next actions and prompts" in rendered
    assert "MMM_EFFECT_UNPROVED" in rendered
    assert "**Combines:** implement operator command; run refusal tests; run failure council" in rendered
    assert "Execution authorized: false" in rendered
    assert "thinking" not in rendered.lower()


def test_single_action_next_prompt_is_refused() -> None:
    value = _surface()
    value["next_prompt_options"][0]["combines_actions"] = ["one action"]  # type: ignore[index]
    with pytest.raises(ValidationError):
        HumanOracleSurface.model_validate(value)


def test_unstructured_thinking_or_log_field_is_refused() -> None:
    value = _surface()
    value["thinking"] = "private narrative"
    with pytest.raises(ValidationError):
        HumanOracleSurface.model_validate(value)


def test_model_call_count_must_match_receipts() -> None:
    value = _surface()
    value["execution"]["model_calls"] = 4  # type: ignore[index]
    with pytest.raises(ValidationError):
        HumanOracleSurface.model_validate(value)


def test_agent_depth_counts_must_match_receipts() -> None:
    value = _surface()
    value["execution"]["subagents"] = 1  # type: ignore[index]
    with pytest.raises(ValidationError):
        HumanOracleSurface.model_validate(value)


def test_python_tool_call_count_must_match_receipts() -> None:
    value = _surface()
    value["execution"]["tool_operations"] = 8  # type: ignore[index]
    with pytest.raises(ValidationError):
        HumanOracleSurface.model_validate(value)


def test_process_minimums_mismatch_is_refused() -> None:
    value = _surface()
    value["minimums"]["subsubagents"] = 1  # type: ignore[index]
    with pytest.raises(ValidationError, match="minimums_satisfied"):
        HumanOracleSurface.model_validate(value)


def test_unmet_process_minimums_render_as_hold() -> None:
    value = _surface()
    value["state"] = "HOLD"
    value["minimums"]["subsubagents"] = 1  # type: ignore[index]
    value["minimums_satisfied"] = False
    rendered = render_human_oracle(value).decode()
    assert "Profile `lean-multimodel-v1` — **not met**" in rendered
    assert "1 subsubagent" in rendered


def test_complete_state_cannot_hide_unmet_minimums() -> None:
    value = _surface()
    value["state"] = "COMPLETE"
    value["minimums"]["subsubagents"] = 1  # type: ignore[index]
    value["minimums_satisfied"] = False
    with pytest.raises(ValidationError, match="complete state"):
        HumanOracleSurface.model_validate(value)


def test_identity_is_replayable() -> None:
    assert human_oracle_identity(_surface()) == human_oracle_identity(_surface())


def _returned_files(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        return {
            info.filename: archive.read(info)
            for info in archive.infolist()
            if not info.is_dir()
        }


def test_human_oracle_is_a_receipt_bound_zip_operation() -> None:
    map_packet, map_return, _ = _map_pair()
    packet = build_human_oracle_packet(
        _surface(), map_packet=map_packet, map_return=map_return
    )
    first = execute_packet(packet)
    second = execute_packet(packet)
    assert first.return_zip_bytes == second.return_zip_bytes
    returned = validate_return_zip(
        first.return_zip_bytes,
        expected_input_sha256=first.input_packet_sha256,
        input_packet_bytes=packet,
    )
    files = _returned_files(first.return_zip_bytes)
    assert returned.required_output_file_list == [OUTPUT_PATH]
    assert b"## Failures and unknowns" in files[OUTPUT_PATH]
    receipt = json.loads(files["receipts/00_render-human-oracle.json"])
    assert receipt["operation"] == "render_human_oracle_v2"


def test_human_oracle_map_update_is_current_replay_bound_and_byte_stable() -> None:
    map_packet, map_return, quotient = _map_pair()
    operation_packet, operation_return = _operation_pair()
    packet = build_human_oracle_map_update_packet(
        _surface(),
        map_packet=map_packet,
        map_return=map_return,
        operation_packet=operation_packet,
        operation_return=operation_return,
    )
    first = execute_packet(packet)
    second = execute_packet(packet)
    assert first.return_zip_bytes == second.return_zip_bytes
    returned = validate_return_zip(
        first.return_zip_bytes,
        expected_input_sha256=first.input_packet_sha256,
        input_packet_bytes=packet,
    )
    files = _returned_files(first.return_zip_bytes)
    assert returned.required_output_file_list == [
        OUTPUT_PATH,
        MAP_DELTA_OUTPUT_PATH,
        UPDATED_MAP_OUTPUT_PATH,
    ]
    delta = json.loads(files[MAP_DELTA_OUTPUT_PATH])
    updated = json.loads(files[UPDATED_MAP_OUTPUT_PATH])
    assert delta["operation_id"] == "render_human_oracle_map_update_v1"
    assert delta["operation_result"] == "OBSERVED"
    assert delta["base_map_sha256"] == sha256_bytes(quotient)
    assert updated["map_delta_count"] == 1
    assert updated["map_delta_head_sha256"] == delta["delta_sha256"]
    assert all(
        fact["tool_id"] in {"jsonschema", "pydantic"}
        for bucket in delta["observations"].values()
        for fact in bucket
    )


def test_real_map_update_cache_holds_before_any_cache_write(tmp_path) -> None:
    map_packet, map_return, _ = _map_pair()
    operation_packet, operation_return = _operation_pair()
    packet = build_human_oracle_map_update_packet(
        _surface(),
        map_packet=map_packet,
        map_return=map_return,
        operation_packet=operation_packet,
        operation_return=operation_return,
    )
    result = execute_packet(packet)
    with pytest.raises(ZipJobRefusal) as caught:
        cache_result(tmp_path, packet, result)
    assert caught.value.reason_code == "HOLD_CACHE_REPLAY_UNSUPPORTED"
    assert not (tmp_path / "objects").exists()
    assert not (tmp_path / "index.sqlite3").exists()


def test_self_consistent_forged_map_return_is_refused_by_live_replay() -> None:
    map_packet, map_return, quotient = _map_pair()
    operation_packet, operation_return = _operation_pair()
    files = _returned_files(map_return)
    manifest = json.loads(files.pop("RETURN_MANIFEST.json"))
    forged_quotient = json.loads(quotient)
    forged_quotient["forged"] = True
    files["output/measured_quotient.json"] = canonical_json_bytes(forged_quotient)
    manifest["file_sha256_registry"] = {
        path: sha256_bytes(data) for path, data in sorted(files.items())
    }
    files["RETURN_MANIFEST.json"] = canonical_json_bytes(manifest)
    forged_return = deterministic_zip(files)
    surface = _surface()
    surface["map_snapshot_sha256"] = sha256_bytes(files["output/measured_quotient.json"])
    surface["map_return_sha256"] = sha256_bytes(forged_return)
    packet = build_human_oracle_map_update_packet(
        surface,
        map_packet=map_packet,
        map_return=forged_return,
        operation_packet=operation_packet,
        operation_return=operation_return,
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_HUMAN_ORACLE_MAP_REPLAY_MISMATCH"


def test_map_update_holds_generic_only_tool_before_any_return() -> None:
    map_packet, map_return, quotient = _map_pair(False)
    operation_packet, operation_return = _operation_pair()
    surface = _surface()
    surface["map_snapshot_sha256"] = sha256_bytes(quotient)
    surface["map_return_sha256"] = sha256_bytes(map_return)
    packet = build_human_oracle_map_update_packet(
        surface,
        map_packet=map_packet,
        map_return=map_return,
        operation_packet=operation_packet,
        operation_return=operation_return,
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_HUMAN_ORACLE_TOOL_UNMAPPED"


def test_map_update_holds_when_required_operation_evidence_is_generic_only() -> None:
    map_packet, map_return, _ = _map_pair()
    operation_packet, operation_return = _operation_pair(False)
    packet = build_human_oracle_map_update_packet(
        _surface(),
        map_packet=map_packet,
        map_return=map_return,
        operation_packet=operation_packet,
        operation_return=operation_return,
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_HUMAN_ORACLE_OPERATION_TOOL_UNMAPPED"


def test_self_consistent_forged_operation_evidence_is_refused_by_live_replay() -> None:
    map_packet, map_return, _ = _map_pair()
    operation_packet, operation_return = _operation_pair()
    files = _returned_files(operation_return)
    manifest = json.loads(files.pop("RETURN_MANIFEST.json"))
    field = json.loads(files["output/operation_probe_field.json"])
    field["forged"] = True
    files["output/operation_probe_field.json"] = canonical_json_bytes(field)
    manifest["file_sha256_registry"] = {
        path: sha256_bytes(data) for path, data in sorted(files.items())
    }
    files["RETURN_MANIFEST.json"] = canonical_json_bytes(manifest)
    forged_return = deterministic_zip(files)
    packet = build_human_oracle_map_update_packet(
        _surface(),
        map_packet=map_packet,
        map_return=map_return,
        operation_packet=operation_packet,
        operation_return=forged_return,
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_HUMAN_ORACLE_OPERATION_EVIDENCE_REPLAY_MISMATCH"


def test_invalid_surface_refuses_without_a_return_zip() -> None:
    surface = _surface()
    surface["thinking"] = "narrative is not evidence"
    with pytest.raises(ValidationError):
        map_packet, map_return, _ = _map_pair()
        build_human_oracle_packet(
            surface, map_packet=map_packet, map_return=map_return
        )


def test_runtime_refuses_changed_path_contract() -> None:
    # Validation of input/output identity is also performed inside the operation;
    # a direct call proves the dispatcher cannot silently remap this interface.
    from constraintbox_zip_agent.human_oracle import run_human_oracle
    from constraintbox_zip_agent.protocol import TaskSpec, canonical_json_bytes

    task = TaskSpec.model_validate(
        {
            "schema": "constraintbox.zip_task.v1",
            "task_id": "wrong-path",
            "sequence": 0,
            "operation": "render_human_oracle_v2",
            "input_paths": ["inputs/other.json"],
            "output_paths": [OUTPUT_PATH],
            "depends_on": [],
            "parameters": {},
            "preload_files": [],
        }
    )
    with pytest.raises(ZipJobRefusal) as caught:
        run_human_oracle(task, {"inputs/other.json": canonical_json_bytes(_surface())})
    assert caught.value.reason_code == "REFUSE_HUMAN_ORACLE_PATH_CONTRACT"


def test_human_oracle_holds_when_required_tool_is_generic_only() -> None:
    map_packet, map_return, quotient = _map_pair(False)
    surface = _surface()
    surface["map_snapshot_sha256"] = __import__("hashlib").sha256(quotient).hexdigest()
    surface["map_return_sha256"] = __import__("hashlib").sha256(map_return).hexdigest()
    packet = build_human_oracle_packet(
        surface, map_packet=map_packet, map_return=map_return
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "HOLD_HUMAN_ORACLE_TOOL_UNMAPPED"
