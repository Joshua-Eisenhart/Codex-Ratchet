#!/usr/bin/env python3
"""Run the contained, model-free objective-integrity candidate.

The nine children are existing deterministic leaf cells.  This module is a
small parent controller: it validates one strict packet, resolves only the
contained child sources, invokes the children in definition order, verifies
each result against the exact child input, and seals a non-authoritative
parent receipt.  It never starts a provider, loads an MMM, or decides a
winner.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Mapping


SCHEMA = "constraintbox.objective-integrity-wave-receipt.v1"
INPUT_SCHEMA = "constraintbox.objective-integrity-wave-input.v1"
OBJECT_CARD_SCHEMA = "constraintbox.object-card.v1"
CONTEXT_SCHEMA = "constraintbox.objective-integrity-context.v1"
WAVE_ID = "cb-objective-integrity-wave-v1"
PARENT_OPERATION = "attack_goodhart_and_paperclip"
CLAIM_CEILING = (
    "Model-free objective-integrity attack composition only; preserves child "
    "findings and contradictions; no truth verdict, winner, provider route, "
    "MMM/preload execution, activation, or promotion."
)
ROUTE_TRUTH = "NOT_FULL"
ROUTE_TRUTH_LABEL = "NOT_FULL/model_free"
NOT_APPLICABLE_ITEMS = ("mmm_preload_receipts", "provider_call_receipts")
NOT_APPLICABLE_LABELS = {
    "mmm_preload_receipts": "NOT_APPLICABLE_MODEL_FREE",
    "provider_call_receipts": "NOT_APPLICABLE_MODEL_FREE",
}
CHILD_IDS = (
    "proxy_map",
    "regimes",
    "severance",
    "adversary",
    "expansion",
    "externalities",
    "termination",
    "amendment",
    "impact",
)

# The function names are part of the reviewed leaf surfaces.  They are kept
# here as a deterministic dispatch table, not as executable code in wave.json.
CHILD_FUNCTIONS: dict[str, str] = {
    "proxy_map": "map_proxy",
    "regimes": "split_regimes",
    "severance": "sever",
    "adversary": "attack",
    "expansion": "check_expansion",
    "externalities": "map_horizon",
    "termination": "check_budget",
    "amendment": "guard",
    "impact": "classify",
}
CHILD_TARGET_FIELDS = {
    "proxy_map": ("target_id", "target"),
    "regimes": ("target_id", "target"),
    "severance": ("target_id", "target"),
    "adversary": ("target_id", "target"),
    "expansion": ("target_id", "target"),
    "externalities": ("target",),
    "termination": ("target",),
    "amendment": ("target",),
    "impact": ("target",),
}
CHILD_OPERATION_FIELDS = {
    child_id: "operation_id" for child_id in CHILD_IDS[:5]
} | {child_id: "operation" for child_id in CHILD_IDS[5:]}
CHILD_INPUT_KEYS = {
    "proxy_map": frozenset({"operation_id", "target", "target_id", "object", "proxy", "measurement", "consumer", "allowed_inference", "preserves", "loses", "cancel_requested"}),
    "regimes": frozenset({"operation_id", "target", "target_id", "regressional", "extremal", "causal", "adversarial", "cancel_requested"}),
    "severance": frozenset({"operation_id", "target", "target_id", "intervention", "proxy_before", "proxy_after", "object_before", "object_after", "cancel_requested"}),
    "adversary": frozenset({"operation_id", "target", "target_id", "attempts", "cancel_requested"}),
    "expansion": frozenset({"operation_id", "target", "target_id", "authorized", "used", "cancel_requested"}),
    "externalities": frozenset({"schema", "operation", "target", "future_runs", "maintainers", "absent_stakeholders", "evidence_quality", "rival_branches", "wider_system", "cancelled", "receipt"}),
    "termination": frozenset({"schema", "operation", "target", "satisfice", "diminishing_return", "stop", "cancellation_obeys", "time_budget", "compute_budget", "resource_budget", "retry_budget", "cancelled", "receipt"}),
    "amendment": frozenset({"schema", "operation", "target", "object_changed", "success_condition_changed", "hard_constraints_changed", "owner_amendment_receipt", "discovered_better_objective", "cancelled", "receipt"}),
    "impact": frozenset({"schema", "operation", "target", "claim", "evidence", "cancelled", "receipt"}),
}
NORMAL_CHILD_STATUSES = frozenset(
    {
        "MAPPED",
        "REGIMES_SPLIT",
        "NOT_FOUND",
        "BLOCKED",
        "INSIDE",
        "BOUNDED",
        "UNCHANGED",
        "CLASSIFIED",
    }
)
TOP_KEYS = frozenset(
    {
        "schema",
        "wave_id",
        "object_card",
        "target",
        "context",
        "operation",
        "child_inputs",
        "expected_source_set_sha256",
        "cancel_requested",
    }
)
OBJECT_CARD_KEYS = frozenset(
    {
        "schema",
        "object",
        "success_condition",
        "hard_constraints",
        "non_objectives",
        "target",
    }
)
CONTEXT_KEYS = frozenset(
    {
        "schema",
        "epoch",
        "contradictions",
        "disagreements",
    }
)
CHILD_ROW_KEYS = frozenset(
    {
        "child_id",
        "skill",
        "operation",
        "leaf_operation",
        "parent_operation_id",
        "operation_id",
        "source",
        "source_sha256",
        "skill_sha256",
        "input_sha256",
        "receipt_sha256",
        "receipt_self_sha256",
        "status",
        "terminal_state",
        "receipt",
    }
)
FAILED_CHILD_ROW_KEYS = CHILD_ROW_KEYS | {"failure_reason"}
PARENT_RECEIPT_KEYS = frozenset(
    {
        "schema",
        "wave_id",
        "status",
        "reason",
        "operation",
        "operation_id",
        "target",
        "object_card",
        "context",
        "object_card_sha256",
        "context_sha256",
        "input_sha256",
        "expected_source_set_sha256",
        "source_set_sha256",
        "parent_cancellation_requested",
        "definition_sha256",
        "source_hashes",
        "child_order",
        "child_inputs",
        "children",
        "child_receipts",
        "findings",
        "contradictions",
        "disagreements",
        "launched_child_order",
        "not_launched_child_ids",
        "cancellation_state",
        "route_truth",
        "route_truth_label",
        "model_free",
        "provider_dispatch_proved",
        "mmm_preload_applicable",
        "provider_receipt_applicable",
        "not_applicable",
        "not_applicable_labels",
        "activated",
        "promotion_allowed",
        "winner_selected",
        "writes_performed",
        "receipt_written",
        "claim_ceiling",
        "integrity_disposition",
        "output_digest",
        "receipt_sha256",
        "receipt_self_sha256",
    }
)
HEX64 = set("0123456789abcdef")

# Filled after wave.json is authored.  It makes a fresh run refuse a changed
# definition, while the receipt verifier also checks the recorded definition
# digest on later replay.
EXPECTED_DEFINITION_SHA256 = "a48253f61c64bf8fcd5b5c970dd8160a52f23e0be25ab251d829f34c84111fcd"


class CandidateRefusal(ValueError):
    """A structural, custody, input, or receipt boundary was crossed."""


class CandidateCancellation(CandidateRefusal):
    """Cancellation is terminal and cannot be rewritten as success."""


class DuplicateJSONKey(ValueError):
    """JSON object keys must not silently overwrite an earlier child."""


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJSONKey(key)
        result[key] = value
    return result


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_digest(value: Any) -> str | None:
    try:
        return digest(value)
    except (TypeError, ValueError, RecursionError, OverflowError):
        return None


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX64


def _bounded(value: Any, *, depth: int = 0, state: list[int] | None = None) -> bool:
    """Keep malformed JSON from becoming a recursion or memory escape."""

    if state is None:
        state = [0]
    state[0] += 1
    if state[0] > 4096 or depth > 16:
        return False
    if value is None or isinstance(value, (bool, int, float, str)):
        if isinstance(value, float):
            return value == value and value not in (float("inf"), float("-inf"))
        return True
    if isinstance(value, list):
        return len(value) <= 512 and all(_bounded(item, depth=depth + 1, state=state) for item in value)
    if isinstance(value, dict):
        return len(value) <= 256 and all(
            isinstance(key, str) and _bounded(item, depth=depth + 1, state=state)
            for key, item in value.items()
        )
    return False


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJSONKey) as exc:
        raise CandidateRefusal(f"REFUSE_JSON:{path.name}") from exc
    if not isinstance(value, dict) or not _bounded(value):
        raise CandidateRefusal(f"REFUSE_JSON_OBJECT:{path.name}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _skills_root(explicit: Path | None = None) -> Path:
    raw = explicit if explicit is not None else os.environ.get("CB_SKILLS_ROOT")
    root = Path(raw) if raw else Path(__file__).resolve().parents[2]
    if root.is_symlink():
        raise CandidateRefusal("REFUSE_SKILLS_ROOT_SYMLINK")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise CandidateRefusal("REFUSE_SKILLS_ROOT") from exc
    if not resolved.is_dir():
        raise CandidateRefusal("REFUSE_SKILLS_ROOT_DIRECTORY")
    return resolved


def _confined(root: Path, raw: str | Path, label: str, *, must_exist: bool = True) -> Path:
    """Resolve a declared path under the contained skills root.

    Lexical ``..`` and symlink components are rejected even if the final
    resolved path happens to land back inside the root.  This prevents a
    source binding from changing meaning between receipt and replay.
    """

    text = raw.as_posix() if isinstance(raw, Path) else str(raw)
    if not text or "\x00" in text or "\\" in text:
        raise CandidateRefusal(f"REFUSE_INVALID_PATH:{label}")
    candidate = Path(text)
    if any(part == ".." for part in candidate.parts):
        raise CandidateRefusal(f"REFUSE_PATH_ESCAPE:{label}")
    if candidate.is_absolute():
        target = candidate
        try:
            relative = target.relative_to(root)
        except ValueError as exc:
            raise CandidateRefusal(f"REFUSE_PATH_ESCAPE:{label}") from exc
    else:
        relative = candidate
        target = root / candidate
    if not relative.parts or relative.as_posix() in {"", "."}:
        raise CandidateRefusal(f"REFUSE_INVALID_PATH:{label}")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise CandidateRefusal(f"REFUSE_SYMLINK_PATH:{label}")
    try:
        resolved = target.resolve(strict=must_exist)
    except OSError as exc:
        raise CandidateRefusal(f"REFUSE_PATH_RESOLVE:{label}") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CandidateRefusal(f"REFUSE_PATH_ESCAPE:{label}") from exc
    if must_exist and (not resolved.is_file() or resolved.is_symlink()):
        raise CandidateRefusal(f"REFUSE_FILE_MISSING:{label}")
    return resolved


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CandidateRefusal(f"REFUSE_CHILD_LOAD:{name}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # pragma: no cover - exercised by source-drift tests
        raise CandidateRefusal(f"REFUSE_CHILD_LOAD:{name}") from exc
    return module


def _validator(root: Path) -> tuple[Any, Path]:
    path = _confined(root, "cb-wave-author/scripts/validate_wave.py", "trusted_validator")
    return _load_module(path, "cb_objective_integrity_trusted_validator"), path


def _definition(root: Path) -> tuple[dict[str, Any], Path, dict[str, Any], Path]:
    definition_path = _confined(root, "cb-objective-integrity-wave/wave.json", "definition")
    definition = _read_json(definition_path)
    current_definition_sha = file_digest(definition_path)
    if EXPECTED_DEFINITION_SHA256 and current_definition_sha != EXPECTED_DEFINITION_SHA256:
        raise CandidateRefusal("REFUSE_DEFINITION_SOURCE_DRIFT")
    validator, validator_path = _validator(root)
    try:
        errors = list(validator.validate(definition)) + list(
            validator.validate_tree(definition, root)
        )
    except Exception as exc:
        raise CandidateRefusal("REFUSE_TRUSTED_VALIDATOR") from exc
    if errors:
        raise CandidateRefusal("REFUSE_WAVE_DEFINITION:" + ",".join(sorted(set(errors))))
    if definition.get("wave_id") != WAVE_ID:
        raise CandidateRefusal("REFUSE_WAVE_ID")
    children = definition.get("children")
    if not isinstance(children, list) or [row.get("id") for row in children if isinstance(row, dict)] != list(CHILD_IDS):
        raise CandidateRefusal("REFUSE_CHILD_ORDER")
    rows: dict[str, Any] = {}
    for row in children:
        if not isinstance(row, dict):
            raise CandidateRefusal("REFUSE_CHILD_SHAPE")
        child_id = str(row.get("id"))
        if child_id in rows:
            raise CandidateRefusal("REFUSE_DUPLICATE_CHILD_DEFINITION")
        composition_operation = row.get("operation")
        leaf_operation = row.get("leaf_operation")
        if not isinstance(composition_operation, str) or not composition_operation:
            raise CandidateRefusal(f"REFUSE_CHILD_OPERATION:{child_id}")
        if not isinstance(leaf_operation, str) or not leaf_operation:
            raise CandidateRefusal(f"REFUSE_CHILD_LEAF_OPERATION:{child_id}")
        source = row.get("source")
        skill = row.get("skill")
        if not isinstance(source, str) or not isinstance(skill, str):
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_BINDING:{child_id}")
        if not _is_digest(row.get("source_sha256")) or not _is_digest(row.get("skill_sha256")):
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_DIGEST:{child_id}")
        script_path = _confined(root, source, f"child_source:{child_id}")
        skill_path = _confined(root, f"{skill}/SKILL.md", f"child_skill:{child_id}")
        if source != f"{skill}/scripts/{_script_name(child_id)}":
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_BINDING:{child_id}")
        if file_digest(script_path) != row["source_sha256"]:
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_DRIFT:{child_id}")
        if file_digest(skill_path) != row["skill_sha256"]:
            raise CandidateRefusal(f"REFUSE_CHILD_SKILL_DRIFT:{child_id}")
        module = _load_module(script_path, f"cb_objective_integrity_{child_id}")
        if getattr(module, "OPERATION", None) != leaf_operation:
            raise CandidateRefusal(f"REFUSE_CHILD_OPERATION_BINDING:{child_id}")
        function_name = CHILD_FUNCTIONS[child_id]
        function = getattr(module, function_name, None)
        verifier = getattr(module, "verify_receipt", None)
        if not callable(function) or not callable(verifier):
            raise CandidateRefusal(f"REFUSE_CHILD_CALLABLE:{child_id}")
        rows[child_id] = {
            "definition": row,
            "composition_operation": composition_operation,
            "leaf_operation": leaf_operation,
            "script_path": script_path,
            "skill_path": skill_path,
            "module": module,
            "function": function,
            "verifier": verifier,
        }
    return definition, definition_path, rows, validator_path


def _script_name(child_id: str) -> str:
    return {
        "proxy_map": "map_proxy.py",
        "regimes": "split_regimes.py",
        "severance": "sever.py",
        "adversary": "attack.py",
        "expansion": "check_expansion.py",
        "externalities": "map_horizon.py",
        "termination": "check_budget.py",
        "amendment": "guard.py",
        "impact": "classify.py",
    }[child_id]


def _input_identity(child_id: str, child_input: Mapping[str, Any], expected_operation: str, target: str) -> None:
    if not isinstance(child_input, dict) or not _bounded(child_input):
        raise CandidateRefusal(f"REFUSE_CHILD_INPUT_SHAPE:{child_id}")
    unknown = set(child_input) - CHILD_INPUT_KEYS[child_id]
    if unknown:
        raise CandidateRefusal(f"REFUSE_CHILD_INPUT_UNKNOWN:{child_id}:" + ",".join(sorted(map(str, unknown))))
    operation_key = CHILD_OPERATION_FIELDS[child_id]
    if child_input.get(operation_key) != expected_operation:
        raise CandidateRefusal(f"REFUSE_CHILD_OPERATION:{child_id}")
    target_fields = CHILD_TARGET_FIELDS[child_id]
    present = [key for key in target_fields if key in child_input]
    if not present:
        raise CandidateRefusal(f"REFUSE_CHILD_TARGET:{child_id}")
    values = [child_input[key] for key in present]
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise CandidateRefusal(f"REFUSE_CHILD_TARGET:{child_id}")
    if any(value != target for value in values):
        raise CandidateRefusal(f"REFUSE_CHILD_TARGET_REBOUND:{child_id}")
    if len(set(values)) != 1:
        raise CandidateRefusal(f"REFUSE_CHILD_TARGET_REBOUND:{child_id}")
    # A child cancellation is valid input, but it is a terminal stop and may
    # not be allowed to launch any later sibling.
    cancel_key = "cancel_requested" if child_id in CHILD_IDS[:5] else "cancelled"
    if cancel_key in child_input and not isinstance(child_input[cancel_key], bool):
        raise CandidateRefusal(f"REFUSE_CHILD_CANCEL_TYPE:{child_id}")


def _string_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise CandidateRefusal(f"REFUSE_{label}_TYPE")


def _validate_object_card(value: Any, target: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CandidateRefusal("REFUSE_OBJECT_CARD_TYPE")
    unknown = set(value) - OBJECT_CARD_KEYS
    missing = OBJECT_CARD_KEYS - set(value)
    if unknown:
        raise CandidateRefusal("REFUSE_OBJECT_CARD_UNKNOWN:" + ",".join(sorted(map(str, unknown))))
    if missing:
        raise CandidateRefusal("REFUSE_OBJECT_CARD_MISSING:" + ",".join(sorted(missing)))
    if value.get("schema") != OBJECT_CARD_SCHEMA:
        raise CandidateRefusal("REFUSE_OBJECT_CARD_SCHEMA")
    for key in ("object", "success_condition", "target"):
        if not isinstance(value.get(key), str) or not value[key].strip():
            raise CandidateRefusal(f"REFUSE_OBJECT_CARD_{key.upper()}_TYPE")
    if value["target"] != target:
        raise CandidateRefusal("REFUSE_OBJECT_CARD_TARGET_REBOUND")
    _string_list(value.get("hard_constraints"), "OBJECT_CARD_HARD_CONSTRAINTS")
    _string_list(value.get("non_objectives"), "OBJECT_CARD_NON_OBJECTIVES")
    return copy.deepcopy(value)


def _validate_context(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CandidateRefusal("REFUSE_CONTEXT_TYPE")
    unknown = set(value) - CONTEXT_KEYS
    missing = CONTEXT_KEYS - set(value)
    if unknown:
        raise CandidateRefusal("REFUSE_CONTEXT_UNKNOWN:" + ",".join(sorted(map(str, unknown))))
    if missing:
        raise CandidateRefusal("REFUSE_CONTEXT_MISSING:" + ",".join(sorted(missing)))
    if value.get("schema") != CONTEXT_SCHEMA:
        raise CandidateRefusal("REFUSE_CONTEXT_SCHEMA")
    if not isinstance(value.get("epoch"), str) or not value["epoch"].strip():
        raise CandidateRefusal("REFUSE_CONTEXT_EPOCH_TYPE")
    _string_list(value.get("contradictions"), "CONTEXT_CONTRADICTIONS")
    _string_list(value.get("disagreements"), "CONTEXT_DISAGREEMENTS")
    return copy.deepcopy(value)


def _packet(packet: Any, definition: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, dict) or not _bounded(packet):
        raise CandidateRefusal("REFUSE_PACKET_SHAPE")
    unknown = set(packet) - TOP_KEYS
    if unknown:
        raise CandidateRefusal("REFUSE_PACKET_EXTRA:" + ",".join(sorted(map(str, unknown))))
    required = TOP_KEYS - {"cancel_requested"}
    missing = required - set(packet)
    if missing:
        raise CandidateRefusal("REFUSE_PACKET_MISSING:" + ",".join(sorted(missing)))
    if packet.get("schema") != INPUT_SCHEMA:
        raise CandidateRefusal("REFUSE_PACKET_SCHEMA")
    if packet.get("wave_id") != WAVE_ID:
        raise CandidateRefusal("REFUSE_PACKET_WAVE")
    if packet.get("operation") != PARENT_OPERATION:
        raise CandidateRefusal("REFUSE_PARENT_OPERATION")
    if not _is_digest(packet.get("expected_source_set_sha256")):
        raise CandidateRefusal("REFUSE_SOURCE_SET_EXPECTATION")
    target = packet.get("target")
    if not isinstance(target, str) or not target.strip() or target != target.strip():
        raise CandidateRefusal("REFUSE_PACKET_TARGET")
    _validate_object_card(packet.get("object_card"), target)
    _validate_context(packet.get("context"))
    if "cancel_requested" in packet and not isinstance(packet["cancel_requested"], bool):
        raise CandidateRefusal("REFUSE_PACKET_CANCEL_TYPE")
    child_inputs = packet.get("child_inputs")
    if not isinstance(child_inputs, dict):
        raise CandidateRefusal("REFUSE_CHILD_INPUTS_SHAPE")
    actual = list(child_inputs)
    if set(actual) != set(CHILD_IDS) or len(actual) != len(set(actual)):
        raise CandidateRefusal("REFUSE_CHILD_SET")
    for child_id in CHILD_IDS:
        row = definition["children"][CHILD_IDS.index(child_id)]
        _input_identity(child_id, child_inputs[child_id], str(row["leaf_operation"]), target)
    return copy.deepcopy(packet)


def _verify_child(module: Any, receipt: dict[str, Any], child_input: dict[str, Any], target: str, operation: str) -> bool:
    if not isinstance(receipt, dict):
        return False
    # The four newer strict leaves expose a candidate-specific verifier, while
    # the older five accept the same exact input through verify_receipt's
    # keyword bindings.  Prefer the stricter payload verifier when present.
    payload_verifier = getattr(module, "verify_payload_receipt", None)
    try:
        if callable(payload_verifier):
            return bool(payload_verifier(child_input, receipt))
        verifier = module.verify_receipt
        return bool(
            verifier(
                receipt,
                child_input,
                input_sha256=digest(child_input),
                current_input_sha256=digest(child_input),
                target=target,
                operation=operation,
            )
        )
    except Exception:
        return False


def _child_receipt_hash(receipt: Any) -> str | None:
    """Hash the actual child receipt object, including no-write receipts."""

    return _safe_digest(receipt) if isinstance(receipt, dict) else None


def _verify_child_cancellation_with_function(
    function: Callable[[Any], dict[str, Any]],
    module: Any,
    receipt: Any,
    child_input: dict[str, Any],
    target: str,
    operation: str,
    *,
    source_path: Path | None = None,
    child_id: str | None = None,
) -> bool:
    """Cancellation verifier with an explicit reviewed leaf callable."""

    if not isinstance(receipt, dict) or receipt.get("status") not in {"CANCELLED", "CANCELLED_NO_AUTHORITY"}:
        return False
    if receipt.get("cancellation_state") != "CANCELLED":
        return False
    if receipt.get("writes_performed") is not False or receipt.get("provider_call_receipt") is not None:
        return False
    if receipt.get("promotion_allowed") is not False or receipt.get("activated") is not False:
        return False
    if receipt.get("model_free") is not True or receipt.get("input_sha256") != _safe_digest(child_input):
        return False
    if "receipt_written" in receipt and receipt.get("receipt_written") is not False:
        return False
    if receipt.get("status") == "CANCELLED" and (
        "receipt_sha256" in receipt or "receipt_self_sha256" in receipt
    ):
        return False
    try:
        verifier_module = module
        replay_function = function
        if source_path is not None and child_id is not None:
            # Re-load the pinned source for cancellation verification.  A
            # caller cannot replace the in-memory callable with a
            # status=CANCELLED dictionary and call that a leaf receipt.
            verifier_module = _load_module(source_path, f"cb_objective_integrity_cancel_verify_{child_id}")
            replay_function = getattr(verifier_module, CHILD_FUNCTIONS[child_id])
        if _verify_child(verifier_module, receipt, child_input, target, operation):
            return True
        replay = replay_function(copy.deepcopy(child_input))
    except Exception:
        return False
    return replay == receipt


def _attest_sources(
    root: Path,
    definition_path: Path,
    configs: Mapping[str, Mapping[str, Any]],
    validator_path: Path,
    pinned: Mapping[str, Any],
    expected_source_set_sha256: str,
) -> dict[str, Any]:
    """Re-attest every pinned file and return its current hash set."""

    runner_path = _confined(root, "cb-objective-integrity-wave/scripts/run_integrity.py", "runner")
    current = _source_hashes(root, definition_path, configs, validator_path, runner_path)
    if current != dict(pinned):
        raise CandidateRefusal("REFUSE_SOURCE_DRIFT")
    if _source_set_sha256(current) != expected_source_set_sha256:
        raise CandidateRefusal("REFUSE_SOURCE_SET_DRIFT")
    if EXPECTED_DEFINITION_SHA256 and current["definition"] != EXPECTED_DEFINITION_SHA256:
        raise CandidateRefusal("REFUSE_DEFINITION_SOURCE_DRIFT")
    for child_id, config in configs.items():
        declaration = config["definition"]
        observed = current["children"].get(child_id, {})
        if observed.get("script") != declaration.get("source_sha256"):
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_DRIFT:{child_id}")
        if observed.get("skill") != declaration.get("skill_sha256"):
            raise CandidateRefusal(f"REFUSE_CHILD_SKILL_DRIFT:{child_id}")
    return current


def _failed_child_row(
    child_id: str,
    config: Mapping[str, Any],
    child_input: dict[str, Any],
    reason: str,
) -> dict[str, Any]:
    definition = config["definition"]
    return {
        "child_id": child_id,
        "skill": definition["skill"],
        "operation": definition["operation"],
        "leaf_operation": definition["leaf_operation"],
        "parent_operation_id": PARENT_OPERATION,
        "operation_id": child_input.get(CHILD_OPERATION_FIELDS[child_id]),
        "source": definition["source"],
        "source_sha256": definition["source_sha256"],
        "skill_sha256": definition["skill_sha256"],
        "input_sha256": _safe_digest(child_input),
        "receipt_sha256": None,
        "receipt_self_sha256": None,
        "status": "FAILED",
        "terminal_state": "FAILED",
        "failure_reason": reason,
        "receipt": None,
    }


def _refuse_existing(receipt: dict[str, Any], reason: str, *, cancelled: bool = False) -> dict[str, Any]:
    """Seal a refusal while retaining the exact launched prefix."""

    launched = list(receipt.get("launched_child_order") or [])
    prefix = list(CHILD_IDS[: len(launched)])
    # A controller bug must not turn a malformed launch trace into success.
    if launched != prefix:
        launched = prefix
        receipt["launched_child_order"] = launched
    receipt["status"] = "CANCELLED" if cancelled else "REFUSE"
    receipt["reason"] = reason
    receipt["cancellation_state"] = "CANCELLED" if cancelled else "NOT_REQUESTED"
    receipt["not_launched_child_ids"] = list(CHILD_IDS[len(launched):])
    rows = receipt.get("children") if isinstance(receipt.get("children"), list) else []
    context = receipt.get("context") if isinstance(receipt.get("context"), dict) else {}
    receipt["contradictions"] = _contradictions(context, rows)
    receipt["disagreements"] = _disagreements(context, rows)
    receipt["integrity_disposition"] = "CANCELLED" if cancelled else _integrity_disposition(rows)
    receipt["output_digest"] = digest(_output_view(receipt))
    return _seal(receipt)


def _child_row(
    child_id: str,
    config: Mapping[str, Any],
    child_input: dict[str, Any],
    receipt: dict[str, Any],
    *,
    terminal_state: str = "COMPLETED",
) -> dict[str, Any]:
    child_definition = config["definition"]
    return {
        "child_id": child_id,
        "skill": child_definition["skill"],
        "operation": child_definition["operation"],
        "leaf_operation": child_definition["leaf_operation"],
        "parent_operation_id": PARENT_OPERATION,
        "operation_id": child_input.get(CHILD_OPERATION_FIELDS[child_id]),
        "source": child_definition["source"],
        "source_sha256": child_definition["source_sha256"],
        "skill_sha256": child_definition["skill_sha256"],
        "input_sha256": digest(child_input),
        "receipt_sha256": _child_receipt_hash(receipt),
        "receipt_self_sha256": receipt.get("receipt_sha256"),
        "status": receipt.get("status"),
        "terminal_state": terminal_state,
        "receipt": copy.deepcopy(receipt),
    }


def _output_view(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "child_order": receipt.get("child_order"),
        "children": receipt.get("children"),
        "child_receipts": receipt.get("child_receipts"),
        "findings": receipt.get("findings"),
        "contradictions": receipt.get("contradictions"),
        "disagreements": receipt.get("disagreements"),
        "launched_child_order": receipt.get("launched_child_order"),
        "not_launched_child_ids": receipt.get("not_launched_child_ids"),
        "integrity_disposition": receipt.get("integrity_disposition"),
    }


def _seal(base: dict[str, Any]) -> dict[str, Any]:
    unsigned = copy.deepcopy(base)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    value = digest(unsigned)
    sealed = copy.deepcopy(unsigned)
    sealed["receipt_sha256"] = value
    sealed["receipt_self_sha256"] = value
    return sealed


def _base_receipt(packet: Any, *, definition_sha: str | None = None) -> dict[str, Any]:
    input_sha: str | None = None
    if isinstance(packet, dict):
        input_sha = _safe_digest(packet)
    return {
        "schema": SCHEMA,
        "wave_id": WAVE_ID,
        "status": "REFUSE",
        "reason": None,
        "operation": PARENT_OPERATION,
        "operation_id": PARENT_OPERATION,
        "target": packet.get("target") if isinstance(packet, dict) else None,
        "object_card": copy.deepcopy(packet.get("object_card")) if isinstance(packet, dict) and isinstance(packet.get("object_card"), dict) else None,
        "context": copy.deepcopy(packet.get("context")) if isinstance(packet, dict) and isinstance(packet.get("context"), dict) else None,
        "object_card_sha256": _safe_digest(packet["object_card"]) if isinstance(packet, dict) and isinstance(packet.get("object_card"), dict) else None,
        "context_sha256": _safe_digest(packet["context"]) if isinstance(packet, dict) and isinstance(packet.get("context"), dict) else None,
        "input_sha256": input_sha,
        "expected_source_set_sha256": packet.get("expected_source_set_sha256") if isinstance(packet, dict) else None,
        "source_set_sha256": None,
        "parent_cancellation_requested": packet.get("cancel_requested") if isinstance(packet, dict) and "cancel_requested" in packet else None,
        "definition_sha256": definition_sha,
        "source_hashes": {},
        "child_order": list(CHILD_IDS),
        "child_inputs": copy.deepcopy(packet.get("child_inputs", {})) if isinstance(packet, dict) and isinstance(packet.get("child_inputs", {}), dict) else {},
        "children": [],
        "child_receipts": {},
        "findings": {},
        "contradictions": [],
        "disagreements": [],
        "launched_child_order": [],
        "not_launched_child_ids": list(CHILD_IDS),
        "cancellation_state": "NOT_REQUESTED",
        "route_truth": ROUTE_TRUTH,
        "route_truth_label": ROUTE_TRUTH_LABEL,
        "model_free": True,
        "provider_dispatch_proved": False,
        "mmm_preload_applicable": False,
        "provider_receipt_applicable": False,
        "not_applicable": list(NOT_APPLICABLE_ITEMS),
        "not_applicable_labels": copy.deepcopy(NOT_APPLICABLE_LABELS),
        "activated": False,
        "promotion_allowed": False,
        "winner_selected": False,
        "writes_performed": False,
        "receipt_written": False,
        "claim_ceiling": CLAIM_CEILING,
        "integrity_disposition": "INTEGRITY_CLEAN",
        "output_digest": None,
    }


def _source_hashes(root: Path, definition_path: Path, child_configs: Mapping[str, Mapping[str, Any]], validator_path: Path, runner_path: Path) -> dict[str, Any]:
    parent_skill_path = _confined(root, "cb-objective-integrity-wave/SKILL.md", "parent_skill")
    return {
        "parent_skill": file_digest(parent_skill_path),
        "runner": file_digest(runner_path),
        "trusted_validator": file_digest(validator_path),
        "definition": file_digest(definition_path),
        "children": {
            child_id: {
                "skill": file_digest(config["skill_path"]),
                "script": file_digest(config["script_path"]),
            }
            for child_id, config in child_configs.items()
        },
    }


def _source_set_sha256(source_hashes: Mapping[str, Any]) -> str:
    """Canonical digest used for caller-bound source-set attestation."""

    return digest(source_hashes)


def source_set_sha256(skills_root: Path | None = None) -> str:
    """Compute the caller's expected digest from the current contained tree."""

    root = _skills_root(skills_root)
    _definition_data, definition_path, configs, validator_path = _definition(root)
    source_hashes = _source_hashes(
        root,
        definition_path,
        configs,
        validator_path,
        _confined(root, "cb-objective-integrity-wave/scripts/run_integrity.py", "runner"),
    )
    return _source_set_sha256(source_hashes)


def _contradictions(context: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    supplied = context.get("contradictions")
    if isinstance(supplied, list):
        out.extend({"source": "context", "value": copy.deepcopy(item)} for item in supplied)
    for row in rows:
        status = row.get("status")
        child_receipt = row.get("receipt")
        reason = (
            child_receipt.get("reason")
            if isinstance(child_receipt, dict)
            else row.get("failure_reason")
        )
        if status not in NORMAL_CHILD_STATUSES or reason:
            out.append(
                {
                    "source": "child",
                    "child_id": row.get("child_id"),
                    "status": status,
                    "reason": reason,
                }
            )
    return out


def _disagreements(context: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        status = str(row.get("status"))
        groups.setdefault(status, []).append(str(row.get("child_id")))
    out: list[dict[str, Any]] = []
    if len(groups) > 1:
        out.append({"kind": "child_status_disagreement", "status_groups": groups})
    supplied = context.get("disagreements")
    if isinstance(supplied, list):
        out.extend({"source": "context", "value": copy.deepcopy(item)} for item in supplied)
    return out


def _integrity_disposition(rows: list[dict[str, Any]]) -> str:
    statuses = {str(row.get("status")) for row in rows}
    if "SEVERED" in statuses:
        return "OBJECT_SEVERED"
    if any(
        isinstance(row.get("receipt"), dict)
        and row["receipt"].get("reason") == "REFUSE_ADVERSARY_SUCCESS"
        for row in rows
    ):
        return "ADVERSARY_SUCCESS"
    if statuses.intersection({"REFUSE", "HOLD", "PROPOSAL_ONLY"}):
        return "INTEGRITY_REFUSE"
    return "INTEGRITY_CLEAN"


def run_packet(packet: Any, *, skills_root: Path | None = None) -> dict[str, Any]:
    """Run one packet and return a sealed parent receipt.

    The returned object is deterministic for a given packet and source tree,
    except for no timestamps or provider data.  It is safe to replay without
    writing files; the CLI writes only the explicitly requested parent output.
    """

    root: Path | None = None
    definition: dict[str, Any] | None = None
    definition_path: Path | None = None
    configs: dict[str, Any] = {}
    validator_path: Path | None = None
    receipt: dict[str, Any] | None = None
    try:
        root = _skills_root(skills_root)
        definition, definition_path, configs, validator_path = _definition(root)
        normalized = _packet(packet, definition)
        definition_sha = file_digest(definition_path)
        receipt = _base_receipt(normalized, definition_sha=definition_sha)
        receipt["object_card"] = copy.deepcopy(normalized["object_card"])
        receipt["context"] = copy.deepcopy(normalized["context"])
        receipt["source_hashes"] = _source_hashes(
            root,
            definition_path,
            configs,
            validator_path,
            _confined(root, "cb-objective-integrity-wave/scripts/run_integrity.py", "runner"),
        )
        receipt["source_set_sha256"] = _source_set_sha256(receipt["source_hashes"])
        _attest_sources(
            root,
            definition_path,
            configs,
            validator_path,
            receipt["source_hashes"],
            normalized["expected_source_set_sha256"],
        )
        receipt["child_inputs"] = copy.deepcopy(normalized["child_inputs"])
        receipt["integrity_disposition"] = "INTEGRITY_CLEAN"
        if normalized.get("cancel_requested") is True:
            receipt["status"] = "CANCELLED"
            receipt["reason"] = "CANCELLED_PARENT_REQUEST"
            receipt["cancellation_state"] = "CANCELLED"
            receipt["integrity_disposition"] = "CANCELLED"
            receipt["contradictions"] = _contradictions(normalized["context"], [])
            receipt["disagreements"] = _disagreements(normalized["context"], [])
            _attest_sources(
                root,
                definition_path,
                configs,
                validator_path,
                receipt["source_hashes"],
                normalized["expected_source_set_sha256"],
            )
            receipt["output_digest"] = digest(_output_view(receipt))
            return _seal(receipt)
        for child_id in CHILD_IDS:
            child_input = normalized["child_inputs"][child_id]
            config = configs[child_id]
            # Re-attest immediately before every child.  A source edit after a
            # prior child therefore stops the run before the next launch.
            _attest_sources(
                root,
                definition_path,
                configs,
                validator_path,
                receipt["source_hashes"],
                normalized["expected_source_set_sha256"],
            )
            target = normalized["target"]
            operation = config["leaf_operation"]
            function: Callable[[Any], dict[str, Any]] = config["function"]
            receipt["launched_child_order"].append(child_id)
            receipt["not_launched_child_ids"] = list(CHILD_IDS[len(receipt["launched_child_order"]):])
            try:
                child_receipt = function(copy.deepcopy(child_input))
            except Exception as exc:
                receipt["children"].append(_failed_child_row(child_id, config, child_input, f"REFUSE_CHILD_EXCEPTION:{child_id}"))
                receipt["child_receipts"][child_id] = None
                receipt["findings"][child_id] = {"status": "FAILED", "reason": f"REFUSE_CHILD_EXCEPTION:{child_id}"}
                raise CandidateRefusal(f"REFUSE_CHILD_EXCEPTION:{child_id}") from exc
            if not isinstance(child_receipt, dict):
                receipt["children"].append(_failed_child_row(child_id, config, child_input, f"REFUSE_CHILD_RECEIPT_SHAPE:{child_id}"))
                receipt["child_receipts"][child_id] = None
                receipt["findings"][child_id] = {"status": "FAILED", "reason": f"REFUSE_CHILD_RECEIPT_SHAPE:{child_id}"}
                raise CandidateRefusal(f"REFUSE_CHILD_RECEIPT_SHAPE:{child_id}")
            status = child_receipt.get("status")
            if child_receipt.get("cancellation_state") == "CANCELLED" or status in {"CANCELLED", "CANCELLED_NO_AUTHORITY"}:
                if not _verify_child_cancellation_with_function(
                    function,
                    config["module"],
                    child_receipt,
                    child_input,
                    target,
                    operation,
                    source_path=config["script_path"],
                    child_id=child_id,
                ):
                    receipt["children"].append(_failed_child_row(child_id, config, child_input, f"REFUSE_CHILD_CANCELLATION_BINDING:{child_id}"))
                    receipt["child_receipts"][child_id] = None
                    receipt["findings"][child_id] = {"status": "FAILED", "reason": f"REFUSE_CHILD_CANCELLATION_BINDING:{child_id}"}
                    raise CandidateRefusal(f"REFUSE_CHILD_CANCELLATION_BINDING:{child_id}")
                receipt["status"] = "CANCELLED"
                receipt["reason"] = f"CANCELLED_CHILD:{child_id}"
                receipt["cancellation_state"] = "CANCELLED"
                row = _child_row(child_id, config, child_input, child_receipt, terminal_state="CANCELLED")
                receipt["children"].append(row)
                receipt["child_receipts"][child_id] = copy.deepcopy(child_receipt)
                receipt["findings"][child_id] = copy.deepcopy(child_receipt)
                receipt["contradictions"] = _contradictions(normalized["context"], receipt["children"])
                receipt["disagreements"] = _disagreements(normalized["context"], receipt["children"])
                receipt["integrity_disposition"] = "CANCELLED"
                _attest_sources(
                    root,
                    definition_path,
                    configs,
                    validator_path,
                    receipt["source_hashes"],
                    normalized["expected_source_set_sha256"],
                )
                receipt["output_digest"] = digest(_output_view(receipt))
                return _seal(receipt)
            if not _verify_child(config["module"], child_receipt, child_input, target, operation):
                receipt["children"].append(_failed_child_row(child_id, config, child_input, f"REFUSE_CHILD_RECEIPT_BINDING:{child_id}"))
                receipt["child_receipts"][child_id] = None
                receipt["findings"][child_id] = {"status": "FAILED", "reason": f"REFUSE_CHILD_RECEIPT_BINDING:{child_id}"}
                raise CandidateRefusal(f"REFUSE_CHILD_RECEIPT_BINDING:{child_id}")
            row = _child_row(child_id, config, child_input, child_receipt)
            receipt["children"].append(row)
            receipt["child_receipts"][child_id] = copy.deepcopy(child_receipt)
            receipt["findings"][child_id] = copy.deepcopy(child_receipt)
            # Re-attest after the child as well; this catches a child/test
            # hook that mutates a pinned source during its own invocation.
            _attest_sources(
                root,
                definition_path,
                configs,
                validator_path,
                receipt["source_hashes"],
                normalized["expected_source_set_sha256"],
            )
        # Final attestation is immediately before the parent receipt is sealed
        # (and therefore before any caller writes it).
        _attest_sources(
            root,
            definition_path,
            configs,
            validator_path,
            receipt["source_hashes"],
            normalized["expected_source_set_sha256"],
        )
        receipt["status"] = "COMPLETE"
        receipt["reason"] = None
        receipt["contradictions"] = _contradictions(normalized["context"], receipt["children"])
        receipt["disagreements"] = _disagreements(normalized["context"], receipt["children"])
        receipt["integrity_disposition"] = _integrity_disposition(receipt["children"])
        receipt["output_digest"] = digest(_output_view(receipt))
        return _seal(receipt)
    except CandidateCancellation as exc:
        if receipt is not None:
            return _refuse_existing(receipt, str(exc), cancelled=True)
        fresh = _base_receipt(packet, definition_sha=file_digest(definition_path) if definition_path and definition_path.is_file() else None)
        return _refuse_existing(fresh, str(exc), cancelled=True)
    except CandidateRefusal as exc:
        if receipt is not None:
            return _refuse_existing(receipt, str(exc), cancelled=False)
        fresh = _base_receipt(packet, definition_sha=file_digest(definition_path) if definition_path and definition_path.is_file() else None)
        if isinstance(packet, dict) and packet.get("cancel_requested") is True:
            return _refuse_existing(fresh, str(exc), cancelled=True)
        return _refuse_existing(fresh, str(exc), cancelled=False)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        if receipt is not None:
            return _refuse_existing(receipt, f"REFUSE_INTERNAL:{type(exc).__name__}")
        fresh = _base_receipt(packet, definition_sha=file_digest(definition_path) if definition_path and definition_path.is_file() else None)
        return _refuse_existing(fresh, f"REFUSE_INTERNAL:{type(exc).__name__}")


def _verify_source_bindings(receipt: Mapping[str, Any], root: Path, definition_path: Path, configs: Mapping[str, Any], validator_path: Path) -> bool:
    source_hashes = receipt.get("source_hashes")
    if not isinstance(source_hashes, dict):
        return False
    expected = _source_hashes(
        root,
        definition_path,
        configs,
        validator_path,
        _confined(root, "cb-objective-integrity-wave/scripts/run_integrity.py", "runner"),
    )
    return source_hashes == expected and receipt.get("definition_sha256") == expected["definition"]


def verify_receipt(receipt: Any, packet: Any | None = None, *, skills_root: Path | None = None) -> bool:
    """Verify parent and all child bindings, including current source custody."""

    if (
        not isinstance(receipt, dict)
        or set(receipt) != PARENT_RECEIPT_KEYS
        or receipt.get("schema") != SCHEMA
        or receipt.get("wave_id") != WAVE_ID
        or not _bounded(receipt)
    ):
        return False
    try:
        root = _skills_root(skills_root)
        definition, definition_path, configs, validator_path = _definition(root)
    except (CandidateRefusal, OSError, ValueError):
        return False
    try:
        if not _verify_source_bindings(receipt, root, definition_path, configs, validator_path):
            return False
    except (CandidateRefusal, OSError, ValueError):
        return False
    if receipt.get("route_truth") != ROUTE_TRUTH or receipt.get("route_truth_label") != ROUTE_TRUTH_LABEL:
        return False
    if receipt.get("model_free") is not True or receipt.get("provider_dispatch_proved") is not False:
        return False
    if receipt.get("mmm_preload_applicable") is not False or receipt.get("provider_receipt_applicable") is not False:
        return False
    if receipt.get("not_applicable") != list(NOT_APPLICABLE_ITEMS) or receipt.get("not_applicable_labels") != NOT_APPLICABLE_LABELS:
        return False
    if receipt.get("activated") is not False or receipt.get("promotion_allowed") is not False or receipt.get("winner_selected") is not False:
        return False
    if (
        receipt.get("claim_ceiling") != CLAIM_CEILING
        or receipt.get("operation") != PARENT_OPERATION
        or receipt.get("operation_id") != PARENT_OPERATION
    ):
        return False
    if receipt.get("writes_performed") is not False or receipt.get("receipt_written") is not False:
        return False
    if receipt.get("child_order") != list(CHILD_IDS):
        return False
    if not isinstance(receipt.get("children"), list) or not isinstance(receipt.get("child_receipts"), dict):
        return False
    rows = receipt["children"]
    ids = [row.get("child_id") for row in rows if isinstance(row, dict)]
    launched = receipt.get("launched_child_order")
    if (
        not isinstance(launched, list)
        or launched != list(CHILD_IDS[: len(launched)])
        or len(launched) != len(set(launched))
        or ids != launched
        or len(ids) != len(rows)
    ):
        return False
    if set(receipt["child_receipts"]) != set(ids):
        return False
    embedded_inputs = receipt.get("child_inputs")
    if not isinstance(embedded_inputs, dict) or set(embedded_inputs) != set(CHILD_IDS):
        return False
    target = receipt.get("target")
    try:
        embedded_packet: dict[str, Any] = {
            "schema": INPUT_SCHEMA,
            "wave_id": WAVE_ID,
            "expected_source_set_sha256": receipt.get("expected_source_set_sha256"),
            "object_card": receipt.get("object_card"),
            "target": target,
            "context": receipt.get("context"),
            "operation": PARENT_OPERATION,
            "child_inputs": embedded_inputs,
        }
        if receipt.get("parent_cancellation_requested") is not None:
            embedded_packet["cancel_requested"] = receipt.get("parent_cancellation_requested")
        normalized_embedded = _packet(embedded_packet, definition)
    except CandidateRefusal:
        return False
    if receipt.get("object_card_sha256") != digest(normalized_embedded["object_card"]):
        return False
    if receipt.get("context_sha256") != digest(normalized_embedded["context"]):
        return False
    if (
        not _is_digest(receipt.get("expected_source_set_sha256"))
        or receipt.get("source_set_sha256") != _source_set_sha256(receipt.get("source_hashes", {}))
        or receipt.get("source_set_sha256") != receipt.get("expected_source_set_sha256")
    ):
        return False
    if packet is not None:
        try:
            normalized = _packet(packet, definition)
        except CandidateRefusal:
            return False
        if (
            receipt.get("input_sha256") != digest(normalized)
            or receipt.get("child_inputs") != normalized["child_inputs"]
            or receipt.get("object_card") != normalized["object_card"]
            or receipt.get("context") != normalized["context"]
            or receipt.get("expected_source_set_sha256") != normalized["expected_source_set_sha256"]
            or receipt.get("parent_cancellation_requested") != normalized.get("cancel_requested")
        ):
            return False
        if receipt.get("target") != normalized["target"]:
            return False
    elif receipt.get("input_sha256") != digest(normalized_embedded):
        return False
    if receipt.get("status") == "COMPLETE":
        if (
            ids != list(CHILD_IDS)
            or receipt.get("not_launched_child_ids") != []
            or receipt.get("cancellation_state") != "NOT_REQUESTED"
            or receipt.get("parent_cancellation_requested") is True
        ):
            return False
    elif receipt.get("status") == "CANCELLED":
        if receipt.get("cancellation_state") != "CANCELLED":
            return False
        if receipt.get("not_launched_child_ids") != list(CHILD_IDS[len(launched):]):
            return False
        if receipt.get("parent_cancellation_requested") not in {True, False}:
            return False
        if receipt.get("parent_cancellation_requested") is True and ids:
            return False
        if receipt.get("parent_cancellation_requested") is False and (
            not ids or rows[-1].get("terminal_state") != "CANCELLED"
        ):
            return False
    elif receipt.get("status") == "REFUSE":
        if receipt.get("cancellation_state") not in {"NOT_REQUESTED", "CANCELLED"}:
            return False
    else:
        return False
    for row in rows:
        if not isinstance(row, dict):
            return False
        child_id = row.get("child_id")
        if child_id not in configs:
            return False
        expected_row_keys = FAILED_CHILD_ROW_KEYS if row.get("terminal_state") == "FAILED" else CHILD_ROW_KEYS
        if set(row) != expected_row_keys:
            return False
        child_input = embedded_inputs[child_id]
        config = configs[child_id]
        expected_operation = config["leaf_operation"]
        try:
            _input_identity(child_id, child_input, expected_operation, str(receipt.get("target")))
        except CandidateRefusal:
            return False
        definition_row = config["definition"]
        if (
            row.get("skill") != definition_row["skill"]
            or row.get("operation") != config["composition_operation"]
            or row.get("leaf_operation") != expected_operation
            or row.get("parent_operation_id") != PARENT_OPERATION
            or row.get("operation_id") != child_input.get(CHILD_OPERATION_FIELDS[child_id])
            or row.get("source") != definition_row["source"]
            or row.get("source_sha256") != definition_row["source_sha256"]
            or row.get("skill_sha256") != definition_row["skill_sha256"]
            or row.get("input_sha256") != digest(child_input)
        ):
            return False
        child_receipt = row.get("receipt")
        if receipt["child_receipts"].get(child_id) != child_receipt:
            return False
        if row.get("terminal_state") == "FAILED":
            if (
                child_receipt is not None
                or row.get("status") != "FAILED"
                or not isinstance(row.get("failure_reason"), str)
                or row.get("receipt_sha256") is not None
                or row.get("receipt_self_sha256") is not None
            ):
                return False
            continue
        if not isinstance(child_receipt, dict):
            return False
        if (
            row.get("receipt_sha256") != _child_receipt_hash(child_receipt)
            or row.get("receipt_self_sha256") != child_receipt.get("receipt_sha256")
            or row.get("status") != child_receipt.get("status")
        ):
            return False
        if row.get("terminal_state") == "CANCELLED":
            if not _verify_child_cancellation_with_function(
                config["function"],
                config["module"],
                child_receipt,
                child_input,
                str(receipt.get("target")),
                expected_operation,
                source_path=config["script_path"],
                child_id=child_id,
            ):
                return False
        elif row.get("terminal_state") == "COMPLETED":
            if not _verify_child(config["module"], child_receipt, child_input, str(receipt.get("target")), expected_operation):
                return False
        else:
            return False
    expected_findings = {
        str(row["child_id"]): (
            row["receipt"]
            if row.get("receipt") is not None
            else {"status": "FAILED", "reason": row.get("failure_reason")}
        )
        for row in rows
    }
    if receipt.get("findings") != expected_findings:
        return False
    verification_context = normalized_embedded["context"]
    if receipt.get("contradictions") != _contradictions(verification_context, rows):
        return False
    if receipt.get("disagreements") != _disagreements(verification_context, rows):
        return False
    expected_integrity = "CANCELLED" if receipt.get("status") == "CANCELLED" else _integrity_disposition(rows)
    if receipt.get("integrity_disposition") != expected_integrity:
        return False
    if receipt.get("output_digest") != digest(_output_view(receipt)):
        return False
    unsigned = copy.deepcopy(receipt)
    expected_self = unsigned.pop("receipt_sha256", None)
    expected_self_2 = unsigned.pop("receipt_self_sha256", None)
    return isinstance(expected_self, str) and expected_self == expected_self_2 and digest(unsigned) == expected_self


def run(packet: Any, *, skills_root: Path | None = None) -> dict[str, Any]:
    """Compatibility alias used by focused tests and contained callers."""

    return run_packet(packet, skills_root=skills_root)


def _prewrite_attest(receipt: Mapping[str, Any], *, skills_root: Path | None = None) -> None:
    """Final source attestation used by the CLI immediately before writing."""

    root = _skills_root(skills_root)
    _definition_data, definition_path, configs, validator_path = _definition(root)
    pinned = receipt.get("source_hashes")
    expected = receipt.get("expected_source_set_sha256")
    if not isinstance(pinned, dict) or not _is_digest(expected):
        raise CandidateRefusal("REFUSE_PREWRITE_SOURCE_BINDING")
    _attest_sources(root, definition_path, configs, validator_path, pinned, expected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--verify", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        packet = _read_json(args.packet)
        if args.verify is not None:
            receipt = _read_json(args.verify)
            ok = verify_receipt(receipt, packet, skills_root=args.root)
            print(json.dumps({"status": "VERIFIED" if ok else "REFUSE_RECEIPT"}, sort_keys=True))
            return 0 if ok else 2
        receipt = run_packet(packet, skills_root=args.root)
        if args.out is not None:
            try:
                _prewrite_attest(receipt, skills_root=args.root)
            except CandidateRefusal as exc:
                receipt = _refuse_existing(copy.deepcopy(receipt), str(exc))
            _write_json(args.out, receipt)
        print(json.dumps({"status": receipt.get("status"), "reason": receipt.get("reason")}, sort_keys=True))
        return 0 if receipt.get("status") == "COMPLETE" else 2
    except (CandidateRefusal, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REFUSE", "reason": f"REFUSE_CLI:{type(exc).__name__}"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
