#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_mmm(skills_root: Path):
    path = skills_root / "mmm-preload/scripts/mmm_preload.py"
    spec = importlib.util.spec_from_file_location("mmm_preload_for_wave", path)
    if spec is None or spec.loader is None:
        raise OSError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify(definition_path: Path, execution_path: Path, seen: set[Path] | None = None) -> list[str]:
    definition_path = definition_path.resolve()
    execution_path = execution_path.resolve()
    seen = set() if seen is None else seen
    if execution_path in seen:
        return ["recursive_execution_cycle"]
    seen.add(execution_path)
    skills_root = definition_path.parent.parent
    definition = read_json(definition_path)
    execution = read_json(execution_path)
    errors: list[str] = []
    if execution.get("schema") != "constraintbox.wave-execution.v1":
        errors.append("execution_schema")
    if execution.get("wave_id") != definition.get("wave_id"):
        errors.append("wave_id")
    if execution.get("state") not in {"COMPLETE", "PARTIAL", "CANCELLED", "MAX_ROUNDS"}:
        errors.append("state")
    run_id = execution.get("run_id")
    controller_id = execution.get("controller_agent_id")
    depth = execution.get("depth")
    if not run_id or not controller_id or not isinstance(depth, int) or depth < 0:
        errors.append("execution_context")
    round_value = execution.get("round")
    if not isinstance(round_value, int) or not 0 <= round_value <= definition["loop"]["max_rounds"]:
        errors.append("round")
    target = execution.get("target_sha256")
    if not isinstance(target, str) or len(target) != 64:
        errors.append("target_sha256")
    mmm_root = Path(str(execution.get("mmm_root", "")))
    if not mmm_root.is_dir():
        errors.append("mmm_root")
    expected = {str(row["id"]): row for row in definition["children"]}
    rows = execution.get("children", [])
    if not isinstance(rows, list):
        rows = []
        errors.append("children_shape")
    actual_ids = [str(row.get("child_id")) for row in rows if isinstance(row, dict)]
    if set(actual_ids) != set(expected) or len(actual_ids) != len(set(actual_ids)):
        errors.append("child_set")
    resolved_sets: list[tuple[str, ...]] = []
    mmm = load_mmm(skills_root)
    for row in rows:
        if not isinstance(row, dict):
            errors.append("child_row")
        else:
            child_id = str(row.get("child_id"))
            child_agent_id = row.get("agent_id")
            if child_id not in expected:
                errors.append(f"unknown_child:{child_id}")
            else:
                terminal = row.get("terminal_state")
                if terminal not in {"COMPLETED", "REFUSED", "CANCELLED", "FAILED"}:
                    errors.append(f"terminal:{child_id}")
                preload_path = Path(str(row.get("preload_receipt", "")))
                call_path = Path(str(row.get("provider_call_receipt", "")))
                output_path = Path(str(row.get("output_path", "")))
                if not preload_path.is_file() or not call_path.is_file():
                    errors.append(f"missing_call_chain:{child_id}")
                else:
                    preload_bytes = preload_path.read_bytes()
                    preload, preload_errors = mmm.receipt_errors(preload_path, mmm_root)
                    errors.extend(f"preload:{child_id}:{item}" for item in preload_errors)
                    resolved_sets.append(tuple(sorted(preload.get("selection", {}).get("resolved_primary_ids", []))))
                    context = {
                        "run_id": run_id,
                        "agent_id": child_agent_id,
                        "parent_id": controller_id,
                        "wave_id": definition.get("wave_id"),
                        "round": round_value,
                        "depth": depth + 1 if isinstance(depth, int) else None,
                    }
                    for key, value in context.items():
                        if preload.get(key) != value:
                            errors.append(f"preload_context:{child_id}:{key}")
                    call = read_json(call_path)
                    if call.get("schema") != "constraintbox.provider-call.v1" or not call.get("provider_request_id"):
                        errors.append(f"call_envelope:{child_id}")
                    if call.get("preload_receipt_sha256") != sha(preload_bytes):
                        errors.append(f"call_preload_binding:{child_id}")
                    if call.get("composed_prompt_sha256") != preload.get("composed_prompt_sha256"):
                        errors.append(f"call_prompt_binding:{child_id}")
                    for key, value in context.items():
                        if call.get(key) != value:
                            errors.append(f"call_context:{child_id}:{key}")
                    if call.get("terminal_state") != terminal:
                        errors.append(f"call_terminal_binding:{child_id}")
                    if not output_path.is_file() or sha(output_path.read_bytes()) != row.get("output_sha256"):
                        errors.append(f"output_binding:{child_id}")
                    if call.get("output_sha256") != row.get("output_sha256"):
                        errors.append(f"call_output_binding:{child_id}")
                observations = row.get("tool_observations", [])
                observed: set[str] = set()
                if not isinstance(observations, list):
                    errors.append(f"tool_evidence:{child_id}")
                else:
                    for observation in observations:
                        if not isinstance(observation, dict):
                            errors.append(f"tool_receipt_shape:{child_id}")
                        else:
                            capability = str(observation.get("capability", ""))
                            receipt_path = Path(str(observation.get("receipt_path", "")))
                            if not receipt_path.is_file() or sha(receipt_path.read_bytes()) != observation.get("receipt_sha256"):
                                errors.append(f"tool_receipt_binding:{child_id}:{capability}")
                            else:
                                tool_receipt = read_json(receipt_path)
                                if tool_receipt.get("schema") != "constraintbox.tool-observation.v1" or tool_receipt.get("capability") != capability or tool_receipt.get("target_sha256") != target:
                                    errors.append(f"tool_receipt_envelope:{child_id}:{capability}")
                                observed.add(capability)
                required_tools = set(expected[child_id].get("tools", []))
                if not required_tools.issubset(observed):
                    errors.append(f"tool_evidence:{child_id}")
                if str(expected[child_id].get("skill", "")).endswith("-wave"):
                    nested = Path(str(row.get("child_wave_receipt", "")))
                    child_definition = skills_root / str(expected[child_id]["skill"]) / "wave.json"
                    if not nested.is_file() or not child_definition.is_file():
                        errors.append(f"nested_wave_receipt:{child_id}")
                    else:
                        try:
                            nested_errors = verify(child_definition, nested, seen)
                        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
                            nested_errors = [f"invalid_execution:{type(exc).__name__}"]
                        errors.extend(f"nested:{child_id}:{item}" for item in nested_errors)
                        try:
                            if read_json(nested).get("target_sha256") != target:
                                errors.append(f"nested_target:{child_id}")
                        except (OSError, json.JSONDecodeError):
                            errors.append(f"nested_target:{child_id}")
    if len(resolved_sets) != len(set(resolved_sets)):
        errors.append("duplicate_resolved_mmm_sets")
    if execution.get("state") == "COMPLETE" and any(row.get("terminal_state") != "COMPLETED" for row in rows if isinstance(row, dict)):
        errors.append("complete_with_noncomplete_child")
    if "cancellation_state" not in execution or "disagreement_state" not in execution:
        errors.append("wave_terminal_evidence")
    wave_output = Path(str(execution.get("output_path", "")))
    if not wave_output.is_file() or sha(wave_output.read_bytes()) != execution.get("output_sha256"):
        errors.append("wave_output_binding")
    for item in definition.get("completion", {}).get("required_evidence", []):
        if item in {"repair_digest", "rerun_delta"} and item not in execution:
            errors.append(f"completion_missing:{item}")
    return sorted(set(errors))


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: verify_wave_execution.py WAVE.json EXECUTION.json", file=sys.stderr)
        return 2
    try:
        errors = verify(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        errors = [f"read:{type(exc).__name__}:{exc}"]
    print(json.dumps({"disposition": "WAVE_EXECUTION_VERIFIED" if not errors else "REFUSE_WAVE_EXECUTION", "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
