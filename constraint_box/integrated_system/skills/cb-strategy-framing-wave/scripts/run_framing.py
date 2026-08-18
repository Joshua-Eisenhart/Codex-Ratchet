#!/usr/bin/env python3
"""Run the contained, model-free strategy-framing wave candidate.

The six children are existing deterministic proposal cells.  This runner is
the parent custody boundary: it validates one exact packet, resolves only
reviewed sources below the contained skills root, invokes children in the
definition order, verifies each receipt against the exact current child
input, and seals a non-authoritative parent receipt.  It never calls a model,
provider, scheduler, or activation gate, and it never chooses a strategy.
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


SCHEMA = "constraintbox.strategy-framing-wave-receipt.v1"
INPUT_SCHEMA = "constraintbox.strategy-framing-wave-input.v1"
OBJECT_CARD_SCHEMA = "constraintbox.object-card.v1"
CONTEXT_SCHEMA = "constraintbox.strategy-framing-context.v1"
WAVE_ID = "cb-strategy-framing-wave-v1"
PARENT_OPERATION = "frame_before_decision"
CLAIM_CEILING = (
    "Model-free strategy framing composition only; preserves the portfolio "
    "antichain and tensions; no winner, decision, implementation, provider "
    "route, MMM/preload execution, activation, or promotion."
)
ROUTE_TRUTH = "NOT_FULL"
ROUTE_TRUTH_LABEL = "NOT_FULL/model_free"
CHILD_IDS = (
    "boundary",
    "portfolio",
    "horizons",
    "retreat",
    "sequence",
    "discriminator",
)

# Function names and leaf operation identifiers are reviewed leaf surfaces.
# They are kept here as a dispatch table, not executable code in wave.json.
CHILD_FUNCTIONS: dict[str, str] = {
    "boundary": "restate",
    "portfolio": "portfolio",
    "horizons": "horizons",
    "retreat": "retreat",
    "sequence": "sequence",
    "discriminator": "discriminate",
}
CHILD_OPERATION_FIELDS = {child_id: "operation_id" for child_id in CHILD_IDS}
CHILD_INPUT_KEYS = {
    "boundary": frozenset({
        "schema", "operation", "operation_id", "target", "target_id", "cancelled", "receipt",
        "object", "invariants", "non_objectives", "forbidden_substitutions", "amendment_authority",
    }),
    "portfolio": frozenset({
        "schema", "operation", "operation_id", "target", "target_id", "cancelled", "receipt",
        "direct", "alternative", "reframe", "back", "wildcard", "stop",
    }),
    "horizons": frozenset({
        "schema", "operation", "operation_id", "target", "target_id", "cancelled", "receipt",
        "immediate", "downstream", "maintenance", "long_horizon",
    }),
    "retreat": frozenset({
        "schema", "operation", "operation_id", "target", "target_id", "cancelled", "receipt",
        "reversible_probes", "irreversible_commitments", "hold_conditions", "retreat_conditions",
        "preserved_options",
    }),
    "sequence": frozenset({
        "schema", "operation", "operation_id", "target", "target_id", "cancelled", "receipt",
        "ordered_by", "steps",
    }),
    "discriminator": frozenset({
        "schema", "operation", "operation_id", "target", "target_id", "cancelled", "receipt",
        "strategies", "disagreement", "probe", "probe_candidates",
    }),
}
CHILD_EXPECTED_STATUSES = {
    "boundary": "RESTATED",
    "portfolio": "PORTED",
    "horizons": "SCANNED",
    "retreat": "MAPPED",
    "sequence": "SEQUENCED",
    "discriminator": "DESIGNED",
}
CHILD_HOLD_STATUSES = frozenset({"HOLD"})
TOP_KEYS = frozenset(
    {
        "schema",
        "wave_id",
        "target",
        "object_card",
        "context",
        "operation",
        "child_inputs",
        "cancel_requested",
    }
)
OBJECT_CARD_KEYS = frozenset({
    "schema", "object", "success_condition", "hard_constraints", "non_objectives", "target",
})
CONTEXT_KEYS = frozenset({"schema", "epoch", "contradictions", "disagreements"})
CHILD_ROW_KEYS = frozenset({
    "child_id", "skill", "operation", "leaf_operation", "parent_operation_id", "operation_id",
    "source", "source_sha256", "skill_sha256", "input_sha256", "receipt_sha256",
    "receipt_self_sha256", "status", "terminal_state", "receipt",
})
FAILED_CHILD_ROW_KEYS = CHILD_ROW_KEYS | {"failure_reason"}
PARENT_RECEIPT_KEYS = frozenset({
    "schema", "wave_id", "status", "reason", "operation", "operation_id", "target",
    "object_card", "context", "object_card_sha256", "context_sha256", "input_sha256",
    "parent_cancellation_requested", "definition_sha256", "source_hashes", "child_order",
    "child_inputs", "child_input_hashes", "children", "child_receipts", "child_receipt_hashes",
    "findings", "contradictions", "disagreements", "tensions", "portfolio_antichain",
    "launched_child_order", "not_launched_child_ids", "cancellation_state", "route_truth",
    "route_truth_label", "model_free", "provider_dispatch_proved", "mmm_preload_applicable",
    "provider_receipt_applicable", "provider_call_receipt", "mmm_preload_receipts", "not_applicable",
    "activated", "promotion_allowed", "winner_selected", "writes_performed", "receipt_written",
    "claim_ceiling", "integrity_disposition", "output_digest", "replay_identity",
    "receipt_sha256", "receipt_self_sha256",
})
HEX64 = set("0123456789abcdef")

# Filled after wave.json is authored.  A fresh run refuses a changed
# definition; verify_receipt also checks the recorded current definition.
EXPECTED_DEFINITION_SHA256 = "1e4a477fd27e150b82d3ebb1479721cb1e7b3e6118ee39daa1853f5b187961f5"
EXPECTED_TRUSTED_VALIDATOR_SHA256 = "166b4938b52ac7f3ce8b9a3a8ca4923b07f6874899d328864e53ab63dfe5e11d"
EXPECTED_PARENT_SKILL_SHA256 = "53d9c18d901ff1c77609703b6fdb16cb5c9668a6663b1c8e8dd33936e6d574e0"


class CandidateRefusal(ValueError):
    """A structural, custody, input, or receipt boundary was crossed."""


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
        return len(value) <= 512 and all(
            _bounded(item, depth=depth + 1, state=state) for item in value
        )
    if isinstance(value, dict):
        return len(value) <= 256 and all(
            isinstance(key, str)
            and _bounded(item, depth=depth + 1, state=state)
            for key, item in value.items()
        )
    return False


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJSONKey, ValueError) as exc:
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

    Lexical ``..`` and symlink components are rejected even when resolution
    would happen to land back under the root.  This binds a source to the
    same bytes at run and replay time.
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
    except Exception as exc:  # pragma: no cover - source drift boundary
        raise CandidateRefusal(f"REFUSE_CHILD_LOAD:{name}") from exc
    return module


def _validator(root: Path) -> tuple[Any, Path]:
    path = _confined(root, "cb-wave-author/scripts/validate_wave.py", "trusted_validator")
    if file_digest(path) != EXPECTED_TRUSTED_VALIDATOR_SHA256:
        raise CandidateRefusal("REFUSE_TRUSTED_VALIDATOR_SOURCE_DRIFT")
    return _load_module(path, "cb_strategy_framing_trusted_validator"), path


def _script_name(child_id: str) -> str:
    return {
        "boundary": "restate.py",
        "portfolio": "portfolio.py",
        "horizons": "horizons.py",
        "retreat": "retreat.py",
        "sequence": "sequence.py",
        "discriminator": "discriminate.py",
    }[child_id]


def _definition(root: Path) -> tuple[dict[str, Any], Path, dict[str, Any], Path]:
    definition_path = _confined(root, "cb-strategy-framing-wave/wave.json", "definition")
    definition = _read_json(definition_path)
    current_definition_sha = file_digest(definition_path)
    if EXPECTED_DEFINITION_SHA256 and current_definition_sha != EXPECTED_DEFINITION_SHA256:
        raise CandidateRefusal("REFUSE_DEFINITION_SOURCE_DRIFT")
    parent_skill_path = _confined(root, "cb-strategy-framing-wave/SKILL.md", "parent_skill")
    if EXPECTED_PARENT_SKILL_SHA256 and file_digest(parent_skill_path) != EXPECTED_PARENT_SKILL_SHA256:
        raise CandidateRefusal("REFUSE_PARENT_SKILL_SOURCE_DRIFT")
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
    if (
        definition.get("candidate_state") != "NEW_CANDIDATE"
        or definition.get("activated") is not False
        or definition.get("promotion_allowed") is not False
    ):
        raise CandidateRefusal("REFUSE_CANDIDATE_STATE")
    children = definition.get("children")
    if not isinstance(children, list) or [
        row.get("id") for row in children if isinstance(row, dict)
    ] != list(CHILD_IDS):
        raise CandidateRefusal("REFUSE_CHILD_ORDER")
    rows: dict[str, Any] = {}
    leaf_operations: set[str] = set()
    for row in children:
        if not isinstance(row, dict):
            raise CandidateRefusal("REFUSE_CHILD_SHAPE")
        child_id = str(row.get("id"))
        if child_id in rows:
            raise CandidateRefusal("REFUSE_DUPLICATE_CHILD_DEFINITION")
        composition_operation = row.get("operation")
        leaf_operation = row.get("leaf_operation")
        source = row.get("source")
        skill = row.get("skill")
        if not isinstance(composition_operation, str) or not composition_operation:
            raise CandidateRefusal(f"REFUSE_CHILD_OPERATION:{child_id}")
        if not isinstance(leaf_operation, str) or not leaf_operation:
            raise CandidateRefusal(f"REFUSE_CHILD_LEAF_OPERATION:{child_id}")
        if leaf_operation in leaf_operations:
            raise CandidateRefusal("REFUSE_DUPLICATE_LEAF_OPERATION")
        leaf_operations.add(leaf_operation)
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
        module = _load_module(script_path, f"cb_strategy_framing_{child_id}")
        if getattr(module, "OPERATION", None) != leaf_operation:
            raise CandidateRefusal(f"REFUSE_CHILD_OPERATION_BINDING:{child_id}")
        function_name = CHILD_FUNCTIONS[child_id]
        function = getattr(module, function_name, None)
        verifier = getattr(module, "verify_receipt", None)
        payload_verifier = getattr(module, "verify_payload_receipt", None)
        if not callable(function) or not callable(verifier) or not callable(payload_verifier):
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
            "payload_verifier": payload_verifier,
        }
    return definition, definition_path, rows, validator_path


def _input_identity(
    child_id: str,
    child_input: Mapping[str, Any],
    expected_operation: str,
    target: str,
) -> None:
    if not isinstance(child_input, dict) or not _bounded(child_input):
        raise CandidateRefusal(f"REFUSE_CHILD_INPUT_SHAPE:{child_id}")
    unknown = set(child_input) - CHILD_INPUT_KEYS[child_id]
    if unknown:
        raise CandidateRefusal(
            f"REFUSE_CHILD_INPUT_UNKNOWN:{child_id}:" + ",".join(sorted(map(str, unknown)))
        )
    if child_input.get("operation") != expected_operation or child_input.get("operation_id") != expected_operation:
        raise CandidateRefusal(f"REFUSE_CHILD_OPERATION:{child_id}")
    present = [key for key in ("target", "target_id") if key in child_input]
    if not present:
        raise CandidateRefusal(f"REFUSE_CHILD_TARGET:{child_id}")
    if len(present) > 1:
        raise CandidateRefusal(f"REFUSE_CHILD_TARGET_CONFLICT:{child_id}")
    value = child_input[present[0]]
    if not isinstance(value, str) or not value.strip() or value != target:
        raise CandidateRefusal(f"REFUSE_CHILD_TARGET_REBOUND:{child_id}")
    if "cancelled" in child_input and not isinstance(child_input["cancelled"], bool):
        raise CandidateRefusal(f"REFUSE_CHILD_CANCEL_TYPE:{child_id}")
    if "cancel_requested" in child_input:
        raise CandidateRefusal(f"REFUSE_CHILD_CANCEL_ALIAS:{child_id}")


CHILD_REQUIRED_FIELDS = {
    "boundary": ("object", "invariants", "non_objectives", "forbidden_substitutions", "amendment_authority"),
    "portfolio": ("direct", "alternative", "reframe", "back", "wildcard", "stop"),
    "horizons": ("immediate", "downstream", "maintenance", "long_horizon"),
    "retreat": ("reversible_probes", "irreversible_commitments", "hold_conditions", "retreat_conditions", "preserved_options"),
    "sequence": ("steps",),
    "discriminator": ("strategies", "disagreement"),
}


def _preflight_child_input(
    child_id: str,
    child_input: dict[str, Any],
    config: Mapping[str, Any],
    target: str,
) -> None:
    """Run the reviewed leaf's pure request validator before any launch."""

    if child_input.get("cancelled") is not True:
        missing = [key for key in CHILD_REQUIRED_FIELDS[child_id] if key not in child_input]
        if missing:
            raise CandidateRefusal(
                f"REFUSE_CHILD_INPUT_MISSING:{child_id}:" + ",".join(missing)
            )
    validator = getattr(config["module"], "_request_reason", None)
    if not callable(validator):
        raise CandidateRefusal(f"REFUSE_CHILD_VALIDATOR:{child_id}")
    try:
        result = validator(copy.deepcopy(child_input))
    except Exception as exc:
        raise CandidateRefusal(f"REFUSE_CHILD_VALIDATOR_EXCEPTION:{child_id}") from exc
    reason = result[0] if isinstance(result, tuple) and result else None
    if reason:
        # The leaf may legitimately return a semantic HOLD/REFUSE finding
        # (collapsed portfolio, no disagreement, reversibility link, etc.).
        # Structural shape/identity failures must be stopped before launch.
        allowed_semantic = {
            "REFUSE_PORTFOLIO_COLLAPSED",
            "HOLD_REVERSIBILITY",
            "REFUSE_RETREAT_LINK",
            "REFUSE_HIDDEN_IRREVERSIBILITY",
            "HOLD_NO_DISAGREEMENT",
            "HOLD_NO_PROBE",
            "REFUSE_DEPENDENCY_CYCLE",
        }
        if reason not in allowed_semantic:
            raise CandidateRefusal(f"REFUSE_CHILD_INPUT_INVALID:{child_id}:{reason}")
    embedded = child_input.get("receipt")
    if embedded is not None and not config["payload_verifier"](child_input, embedded):
        raise CandidateRefusal(f"REFUSE_CHILD_INPUT_RECEIPT_TAMPER:{child_id}")


def _string_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise CandidateRefusal(f"REFUSE_{label}_TYPE")


def _validate_object_card(value: Any, target: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CandidateRefusal("REFUSE_OBJECT_CARD_TYPE")
    unknown = set(value) - OBJECT_CARD_KEYS
    missing = OBJECT_CARD_KEYS - set(value)
    if unknown:
        raise CandidateRefusal(
            "REFUSE_OBJECT_CARD_UNKNOWN:" + ",".join(sorted(map(str, unknown)))
        )
    if missing:
        raise CandidateRefusal(
            "REFUSE_OBJECT_CARD_MISSING:" + ",".join(sorted(missing))
        )
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
        raise CandidateRefusal(
            "REFUSE_CONTEXT_UNKNOWN:" + ",".join(sorted(map(str, unknown)))
        )
    if missing:
        raise CandidateRefusal("REFUSE_CONTEXT_MISSING:" + ",".join(sorted(missing)))
    if value.get("schema") != CONTEXT_SCHEMA:
        raise CandidateRefusal("REFUSE_CONTEXT_SCHEMA")
    if not isinstance(value.get("epoch"), str) or not value["epoch"].strip():
        raise CandidateRefusal("REFUSE_CONTEXT_EPOCH_TYPE")
    _string_list(value.get("contradictions"), "CONTEXT_CONTRADICTIONS")
    _string_list(value.get("disagreements"), "CONTEXT_DISAGREEMENTS")
    return copy.deepcopy(value)


def _packet(
    packet: Any,
    definition: Mapping[str, Any],
    configs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
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
    if set(child_inputs) != set(CHILD_IDS) or len(child_inputs) != len(set(child_inputs)):
        raise CandidateRefusal("REFUSE_CHILD_SET")
    for child_id in CHILD_IDS:
        row = definition["children"][CHILD_IDS.index(child_id)]
        child_input = child_inputs[child_id]
        _input_identity(child_id, child_input, str(row["leaf_operation"]), target)
        # Exact schema/type preflight is complete for every child before the
        # first child can be invoked.
        if configs is not None:
            _preflight_child_input(child_id, child_input, configs[child_id], target)
    return copy.deepcopy(packet)


def _verify_child(config: Mapping[str, Any], receipt: dict[str, Any], child_input: dict[str, Any]) -> bool:
    if not isinstance(receipt, dict):
        return False
    try:
        # All six contained leaves expose the exact payload-bound verifier.
        return bool(config["payload_verifier"](child_input, receipt))
    except (TypeError, ValueError, KeyError, AttributeError):
        return False


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
        "tensions": receipt.get("tensions"),
        "portfolio_antichain": receipt.get("portfolio_antichain"),
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
        "object_card_sha256": _safe_digest(packet.get("object_card")) if isinstance(packet, dict) else None,
        "context_sha256": _safe_digest(packet.get("context")) if isinstance(packet, dict) else None,
        "input_sha256": _safe_digest(packet),
        "parent_cancellation_requested": packet.get("cancel_requested") if isinstance(packet, dict) and "cancel_requested" in packet else None,
        "definition_sha256": definition_sha,
        "source_hashes": {},
        "child_order": list(CHILD_IDS),
        "child_inputs": copy.deepcopy(packet.get("child_inputs", {})) if isinstance(packet, dict) and isinstance(packet.get("child_inputs", {}), dict) else {},
        "child_input_hashes": {},
        "children": [],
        "child_receipts": {},
        "child_receipt_hashes": {},
        "findings": {},
        "contradictions": [],
        "disagreements": [],
        "tensions": [],
        "portfolio_antichain": None,
        "launched_child_order": [],
        "not_launched_child_ids": list(CHILD_IDS),
        "cancellation_state": "NOT_REQUESTED",
        "route_truth": ROUTE_TRUTH,
        "route_truth_label": ROUTE_TRUTH_LABEL,
        "model_free": True,
        "provider_dispatch_proved": False,
        "mmm_preload_applicable": False,
        "provider_receipt_applicable": False,
        "provider_call_receipt": None,
        "mmm_preload_receipts": [],
        "not_applicable": {
            "mmm_preload_receipts": "model_free_candidate",
            "provider_call_receipts": "model_free_candidate",
        },
        "activated": False,
        "promotion_allowed": False,
        "winner_selected": False,
        "writes_performed": False,
        "receipt_written": False,
        "claim_ceiling": CLAIM_CEILING,
        "integrity_disposition": "INTEGRITY_CLEAN",
        "output_digest": None,
        "replay_identity": {},
    }


def _source_hashes(
    root: Path,
    definition_path: Path,
    child_configs: Mapping[str, Mapping[str, Any]],
    validator_path: Path,
    runner_path: Path,
) -> dict[str, Any]:
    parent_skill_path = _confined(root, "cb-strategy-framing-wave/SKILL.md", "parent_skill")
    runner_bound = _confined(root, "cb-strategy-framing-wave/scripts/run_framing.py", "runner")
    return {
        "parent_skill": file_digest(parent_skill_path),
        "runner": file_digest(runner_bound),
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


def _child_receipt_hash(receipt: Any) -> str | None:
    """Hash the actual child receipt object, including cancellation receipts."""

    return _safe_digest(receipt) if isinstance(receipt, dict) else None


def _attest_paths(
    root: Path,
    definition_path: Path,
    configs: Mapping[str, Mapping[str, Any]],
    validator_path: Path,
) -> None:
    """Re-check lexical, symlink, and resolved custody for every pinned path."""

    expected_paths = {
        "parent_skill": _confined(root, "cb-strategy-framing-wave/SKILL.md", "parent_skill"),
        "definition": _confined(root, "cb-strategy-framing-wave/wave.json", "definition"),
        "trusted_validator": _confined(root, "cb-wave-author/scripts/validate_wave.py", "trusted_validator"),
        "runner": _confined(root, "cb-strategy-framing-wave/scripts/run_framing.py", "runner"),
    }
    if expected_paths["definition"] != definition_path.resolve(strict=True):
        raise CandidateRefusal("REFUSE_PATH_CUSTODY:definition")
    if expected_paths["trusted_validator"] != validator_path.resolve(strict=True):
        raise CandidateRefusal("REFUSE_PATH_CUSTODY:trusted_validator")
    for child_id, config in configs.items():
        declaration = config["definition"]
        source = _confined(root, declaration["source"], f"child_source:{child_id}")
        skill = _confined(root, f"{declaration['skill']}/SKILL.md", f"child_skill:{child_id}")
        if source != Path(config["script_path"]).resolve(strict=True):
            raise CandidateRefusal(f"REFUSE_PATH_CUSTODY:child_source:{child_id}")
        if skill != Path(config["skill_path"]).resolve(strict=True):
            raise CandidateRefusal(f"REFUSE_PATH_CUSTODY:child_skill:{child_id}")


def _attest_sources(
    root: Path,
    definition_path: Path,
    configs: Mapping[str, Mapping[str, Any]],
    validator_path: Path,
    pinned: Mapping[str, Any],
) -> dict[str, Any]:
    """Re-attest every parent and child source against the initial binding."""

    _attest_paths(root, definition_path, configs, validator_path)
    current = _source_hashes(
        root,
        definition_path,
        configs,
        validator_path,
        Path(__file__).resolve(),
    )
    if current != dict(pinned):
        raise CandidateRefusal("REFUSE_SOURCE_DRIFT")
    if EXPECTED_DEFINITION_SHA256 and current["definition"] != EXPECTED_DEFINITION_SHA256:
        raise CandidateRefusal("REFUSE_DEFINITION_SOURCE_DRIFT")
    if EXPECTED_TRUSTED_VALIDATOR_SHA256 and current["trusted_validator"] != EXPECTED_TRUSTED_VALIDATOR_SHA256:
        raise CandidateRefusal("REFUSE_TRUSTED_VALIDATOR_SOURCE_DRIFT")
    if EXPECTED_PARENT_SKILL_SHA256 and current["parent_skill"] != EXPECTED_PARENT_SKILL_SHA256:
        raise CandidateRefusal("REFUSE_PARENT_SKILL_SOURCE_DRIFT")
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


def _verify_child_cancellation_with_function(
    function: Callable[[Any], dict[str, Any]],
    module: Any,
    receipt: Any,
    child_input: dict[str, Any],
    *,
    root: Path,
    source_path: Path,
    declared_source: str,
    child_id: str,
) -> bool:
    """Require a real current-input cancellation receipt and exact replay."""

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
    if receipt.get("receipt_written") is not False:
        return False
    try:
        # Re-check path custody before loading the replay verifier.  A source
        # path swapped to a symlink must never be loaded as cancellation proof.
        source_path = _confined(root, declared_source, f"child_source:{child_id}")
        if source_path != Path(source_path).resolve(strict=True):
            return False
        verifier_module = _load_module(source_path, f"cb_strategy_framing_cancel_verify_{child_id}")
        verifier = getattr(verifier_module, "verify_payload_receipt", None)
        replay_function = getattr(verifier_module, CHILD_FUNCTIONS[child_id])
        if not callable(verifier) or not callable(replay_function):
            return False
        if not verifier(child_input, receipt):
            return False
        replayed = replay_function(copy.deepcopy(child_input))
    except Exception:
        return False
    return replayed == receipt


def _refuse_existing(
    receipt: dict[str, Any],
    reason: str,
    *,
    cancelled: bool = False,
    held: bool = False,
) -> dict[str, Any]:
    """Seal refusal/cancellation while retaining the truthful launched prefix."""

    rows = receipt.get("children") if isinstance(receipt.get("children"), list) else []
    row_ids = [row.get("child_id") for row in rows if isinstance(row, dict)]
    prefix = list(CHILD_IDS[: len(row_ids)])
    if row_ids != prefix:
        reason = f"REFUSE_LAUNCH_TRACE:{reason}"
        row_ids = prefix
        receipt["children"] = [row for row in rows if isinstance(row, dict)][: len(prefix)]
    receipt["launched_child_order"] = list(row_ids)
    derived_status, derived_reason = _derive_terminal(
        receipt,
        requested_reason=reason,
        force_cancelled=cancelled,
    )
    if held and derived_status == "REFUSE":
        derived_status = "HOLD"
    receipt["status"] = derived_status
    receipt["reason"] = derived_reason
    receipt["cancellation_state"] = "CANCELLED" if derived_status == "CANCELLED" else "NOT_REQUESTED"
    receipt["not_launched_child_ids"] = list(CHILD_IDS[len(row_ids):])
    context = receipt.get("context") if isinstance(receipt.get("context"), dict) else {}
    receipt["contradictions"] = _contradictions(context, receipt["children"])
    receipt["tensions"] = _tensions(context, receipt["children"])
    receipt["disagreements"] = _disagreements(context, receipt["children"])
    receipt["integrity_disposition"] = "CANCELLED" if derived_status == "CANCELLED" else _integrity_disposition(receipt["children"])
    _set_replay_identity(receipt)
    return _seal(receipt)


def _status_groups(rows: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        groups.setdefault(str(row.get("status")), []).append(str(row.get("child_id")))
    return groups


def _disagreements(context: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    groups = _status_groups(rows)
    if len(groups) > 1:
        out.append({"kind": "child_status_disagreement", "status_groups": groups})
    supplied = context.get("disagreements")
    if isinstance(supplied, list):
        out.extend({"source": "context", "value": copy.deepcopy(item)} for item in supplied)
    discriminator = next(
        (row.get("receipt", {}).get("disagreement") for row in rows if row.get("child_id") == "discriminator" and isinstance(row.get("receipt"), dict)),
        None,
    )
    if isinstance(discriminator, str) and discriminator.strip():
        out.append({"source": "child", "child_id": "discriminator", "value": discriminator})
    return out


def _tensions(context: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    supplied = context.get("tensions")
    if isinstance(supplied, list):
        out.extend({"source": "context", "value": copy.deepcopy(item)} for item in supplied)
    disagreements = context.get("disagreements")
    if isinstance(disagreements, list):
        out.extend({"source": "context_disagreement", "value": copy.deepcopy(item)} for item in disagreements)
    for row in rows:
        receipt = row.get("receipt")
        status = row.get("status")
        if status != CHILD_EXPECTED_STATUSES.get(str(row.get("child_id"))) or (
            isinstance(receipt, dict) and receipt.get("reason")
        ):
            out.append(
                {
                    "source": "child",
                    "child_id": row.get("child_id"),
                    "status": status,
                    "reason": receipt.get("reason") if isinstance(receipt, dict) else None,
                }
            )
    return out


def _contradictions(context: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    supplied = context.get("contradictions")
    if isinstance(supplied, list):
        out.extend({"source": "context", "value": copy.deepcopy(item)} for item in supplied)
    for row in rows:
        receipt = row.get("receipt")
        status = row.get("status")
        if status != CHILD_EXPECTED_STATUSES.get(str(row.get("child_id"))) or (
            isinstance(receipt, dict) and receipt.get("reason")
        ):
            out.append(
                {
                    "source": "child",
                    "child_id": row.get("child_id"),
                    "status": status,
                    "reason": receipt.get("reason") if isinstance(receipt, dict) else None,
                }
            )
    return out


def _integrity_disposition(rows: list[dict[str, Any]]) -> str:
    statuses = {str(row.get("status")) for row in rows}
    if "HOLD" in statuses:
        return "CHILD_HOLD"
    if statuses.intersection({"REFUSE", "FAILED"}):
        return "CHILD_REFUSE"
    if any(status in {"CANCELLED", "CANCELLED_NO_AUTHORITY"} for status in statuses):
        # A cancellation row inside a parent REFUSE (for example, source
        # drift discovered after the leaf cancellation) is evidence of a
        # stopped child, not a successful parent cancellation terminal.
        return "CHILD_REFUSE"
    return "INTEGRITY_CLEAN"


def _prefix_marker(rows: list[dict[str, Any]]) -> str:
    count = len(rows)
    if count == 0:
        return "before_children"
    if count >= len(CHILD_IDS):
        return "after_all_children"
    return CHILD_IDS[count]


def _derive_terminal(
    receipt: Mapping[str, Any],
    *,
    requested_reason: str | None = None,
    force_cancelled: bool = False,
) -> tuple[str, str | None]:
    """Derive terminal status/reason from the packet cancellation and rows."""

    rows = receipt.get("children") if isinstance(receipt.get("children"), list) else []
    parent_cancel = receipt.get("parent_cancellation_requested") is True
    marker = _prefix_marker(rows)
    if not force_cancelled and requested_reason:
        if requested_reason.startswith("REFUSE_SOURCE_DRIFT"):
            return "REFUSE", f"REFUSE_SOURCE_DRIFT:{marker}"
        if requested_reason.startswith("REFUSE_PATH_CUSTODY"):
            return "REFUSE", f"REFUSE_PATH_CUSTODY:{marker}"
        if requested_reason.startswith((
            "REFUSE_DEFINITION", "REFUSE_TRUSTED_VALIDATOR", "REFUSE_PARENT_SKILL",
            "REFUSE_CHILD_SOURCE_DRIFT", "REFUSE_CHILD_SKILL_DRIFT", "REFUSE_INTERNAL",
        )):
            return "REFUSE", f"{requested_reason}:{marker}"
    if parent_cancel and not rows:
        return "CANCELLED", "CANCELLED_PARENT_REQUEST"
    if parent_cancel:
        return "REFUSE", "REFUSE_PARENT_CANCEL_PREFIX"
    if rows:
        last = rows[-1] if isinstance(rows[-1], dict) else {}
        child_id = str(last.get("child_id"))
        terminal_state = last.get("terminal_state")
        status = last.get("status")
        if terminal_state == "CANCELLED" and status in {"CANCELLED", "CANCELLED_NO_AUTHORITY"}:
            if force_cancelled:
                return "CANCELLED", f"CANCELLED_CHILD:{child_id}"
            if requested_reason and requested_reason.startswith("REFUSE_SOURCE_DRIFT"):
                return "REFUSE", f"REFUSE_SOURCE_DRIFT:{_prefix_marker(rows)}"
            return "CANCELLED", f"CANCELLED_CHILD:{child_id}"
        if terminal_state == "FAILED":
            failure = last.get("failure_reason")
            return "REFUSE", failure if isinstance(failure, str) and failure else f"REFUSE_CHILD_FAILURE:{child_id}"
        if status == "HOLD":
            child_reason = last.get("receipt", {}).get("reason") if isinstance(last.get("receipt"), dict) else None
            return "HOLD", f"HOLD_CHILD_STATUS:{child_id}:HOLD:{child_reason}"
        if status == "REFUSE":
            child_reason = last.get("receipt", {}).get("reason") if isinstance(last.get("receipt"), dict) else None
            return "REFUSE", f"REFUSE_CHILD_STATUS:{child_id}:REFUSE:{child_reason}"
        if (
            len(rows) == len(CHILD_IDS)
            and all(
                isinstance(row, dict)
                and row.get("terminal_state") == "COMPLETED"
                and row.get("status") == CHILD_EXPECTED_STATUSES.get(str(row.get("child_id")))
                for row in rows
            )
        ):
            return "COMPLETE", None
    if requested_reason is None:
        # A bare incomplete prefix has no failed/held/cancelled terminal and
        # is not a causally valid parent refusal.  This makes a resealed
        # COMPLETE -> REFUSE/HOLD prefix fail verification.
        return "INVALID", None
    if requested_reason and requested_reason.startswith("REFUSE_SOURCE_DRIFT"):
        return "REFUSE", f"REFUSE_SOURCE_DRIFT:{marker}"
    if not rows and requested_reason and requested_reason.startswith("REFUSE_"):
        return "REFUSE", requested_reason
    return "REFUSE", f"REFUSE_PREFIX_INCOMPLETE:{marker}"


def _set_replay_identity(receipt: dict[str, Any]) -> None:
    receipt["output_digest"] = digest(_output_view(receipt))
    receipt["replay_identity"] = {
        "input_sha256": receipt.get("input_sha256"),
        "definition_sha256": receipt.get("definition_sha256"),
        "source_hashes": copy.deepcopy(receipt.get("source_hashes")),
        "child_input_hashes": copy.deepcopy(receipt.get("child_input_hashes")),
        "child_receipt_hashes": copy.deepcopy(receipt.get("child_receipt_hashes")),
        "output_digest": receipt.get("output_digest"),
    }


def _append_child(
    receipt: dict[str, Any],
    child_id: str,
    config: Mapping[str, Any],
    child_input: dict[str, Any],
    child_receipt: dict[str, Any],
    *,
    terminal_state: str = "COMPLETED",
) -> dict[str, Any]:
    row = _child_row(
        child_id,
        config,
        child_input,
        child_receipt,
        terminal_state=terminal_state,
    )
    receipt["children"].append(row)
    receipt["child_receipts"][child_id] = copy.deepcopy(child_receipt)
    receipt["child_receipt_hashes"][child_id] = _child_receipt_hash(child_receipt)
    receipt["findings"][child_id] = copy.deepcopy(child_receipt)
    receipt["child_input_hashes"][child_id] = digest(child_input)
    return row


def _finish_child_stop(
    receipt: dict[str, Any],
    context: Mapping[str, Any],
    *,
    status: str,
    reason: str,
    cancellation: bool = False,
) -> dict[str, Any]:
    receipt["status"] = status
    receipt["reason"] = reason
    receipt["cancellation_state"] = "CANCELLED" if cancellation else "NOT_REQUESTED"
    receipt["contradictions"] = _contradictions(context, receipt["children"])
    receipt["tensions"] = _tensions(context, receipt["children"])
    receipt["disagreements"] = _disagreements(context, receipt["children"])
    receipt["integrity_disposition"] = _integrity_disposition(receipt["children"])
    _set_replay_identity(receipt)
    return _seal(receipt)


def run_packet(packet: Any, *, skills_root: Path | None = None) -> dict[str, Any]:
    """Run one exact packet and return a sealed parent receipt."""

    root: Path | None = None
    definition_path: Path | None = None
    configs: dict[str, Any] = {}
    validator_path: Path | None = None
    receipt: dict[str, Any] | None = None
    try:
        root = _skills_root(skills_root)
        definition, definition_path, configs, validator_path = _definition(root)
        normalized = _packet(packet, definition, configs)
        receipt = _base_receipt(
            normalized,
            definition_sha=file_digest(definition_path),
        )
        receipt["source_hashes"] = _source_hashes(
            root,
            definition_path,
            configs,
            validator_path,
            Path(__file__).resolve(),
        )
        _attest_sources(root, definition_path, configs, validator_path, receipt["source_hashes"])
        receipt["child_inputs"] = copy.deepcopy(normalized["child_inputs"])
        receipt["child_input_hashes"] = {
            child_id: digest(normalized["child_inputs"][child_id])
            for child_id in CHILD_IDS
        }
        context = normalized["context"]
        if normalized.get("cancel_requested") is True:
            _attest_sources(root, definition_path, configs, validator_path, receipt["source_hashes"])
            return _refuse_existing(receipt, "CANCELLED_PARENT_REQUEST", cancelled=True)
        for child_id in CHILD_IDS:
            child_input = normalized["child_inputs"][child_id]
            config = configs[child_id]
            # Re-attest the parent skill, definition, trusted validator,
            # runner, and every leaf before every child launch.
            _attest_sources(root, definition_path, configs, validator_path, receipt["source_hashes"])
            function: Callable[[Any], dict[str, Any]] = config["function"]
            receipt["launched_child_order"].append(child_id)
            receipt["not_launched_child_ids"] = list(CHILD_IDS[len(receipt["launched_child_order"]):])
            try:
                child_receipt = function(copy.deepcopy(child_input))
            except Exception as exc:
                reason = f"REFUSE_CHILD_EXCEPTION:{child_id}"
                row = _failed_child_row(child_id, config, child_input, reason)
                receipt["children"].append(row)
                receipt["child_receipts"][child_id] = None
                receipt["child_receipt_hashes"][child_id] = None
                receipt["findings"][child_id] = {"status": "FAILED", "reason": reason}
                return _refuse_existing(receipt, reason)
            if not isinstance(child_receipt, dict):
                reason = f"REFUSE_CHILD_RECEIPT_SHAPE:{child_id}"
                row = _failed_child_row(child_id, config, child_input, reason)
                receipt["children"].append(row)
                receipt["child_receipts"][child_id] = None
                receipt["child_receipt_hashes"][child_id] = None
                receipt["findings"][child_id] = {"status": "FAILED", "reason": reason}
                return _refuse_existing(receipt, reason)
            status = child_receipt.get("status")
            if status in {"CANCELLED", "CANCELLED_NO_AUTHORITY"} or child_receipt.get("cancellation_state") == "CANCELLED":
                if not _verify_child_cancellation_with_function(
                    function,
                    config["module"],
                    child_receipt,
                    child_input,
                    root=root,
                    source_path=config["script_path"],
                    declared_source=config["definition"]["source"],
                    child_id=child_id,
                ):
                    reason = f"REFUSE_CHILD_CANCELLATION_BINDING:{child_id}"
                    row = _failed_child_row(child_id, config, child_input, reason)
                    receipt["children"].append(row)
                    receipt["child_receipts"][child_id] = None
                    receipt["child_receipt_hashes"][child_id] = None
                    receipt["findings"][child_id] = {"status": "FAILED", "reason": reason}
                    return _refuse_existing(receipt, reason)
                _append_child(
                    receipt, child_id, config, child_input, child_receipt, terminal_state="CANCELLED"
                )
                # Cancellation is only terminal after the same full source
                # and path custody attestation required for success.  If a
                # child or hook mutated a pinned file, the outer refusal path
                # preserves this row but changes the parent to REFUSE.
                _attest_sources(root, definition_path, configs, validator_path, receipt["source_hashes"])
                return _refuse_existing(receipt, f"CANCELLED_CHILD:{child_id}", cancelled=True)
            if not _verify_child(config, child_receipt, child_input):
                reason = f"REFUSE_CHILD_RECEIPT_BINDING:{child_id}"
                row = _failed_child_row(child_id, config, child_input, reason)
                receipt["children"].append(row)
                receipt["child_receipts"][child_id] = None
                receipt["child_receipt_hashes"][child_id] = None
                receipt["findings"][child_id] = {"status": "FAILED", "reason": reason}
                return _refuse_existing(receipt, reason)
            _append_child(receipt, child_id, config, child_input, child_receipt)
            expected = CHILD_EXPECTED_STATUSES[child_id]
            if (
                child_id == "portfolio"
                and status == expected
                and isinstance(child_receipt.get("strategies"), dict)
            ):
                # Preserve the antichain as soon as its exact child receipt
                # is verified, including a later cancellation prefix.
                receipt["portfolio_antichain"] = copy.deepcopy(
                    child_receipt["strategies"]
                )
            # Catch a leaf or test hook that mutates any pinned source while
            # its own invocation is running.
            _attest_sources(root, definition_path, configs, validator_path, receipt["source_hashes"])
            if status != expected:
                # A collapsed portfolio, missing disagreement, reversibility
                # hold, or any other leaf stop is retained but cannot be
                # promoted to a completed parent framing run.
                stop_status = "HOLD" if status in CHILD_HOLD_STATUSES else "REFUSE"
                return _refuse_existing(
                    receipt,
                    f"{stop_status}_CHILD_STATUS:{child_id}:{status}:{child_receipt.get('reason')}",
                    held=(status in CHILD_HOLD_STATUSES),
                )
        portfolio_receipt = receipt["child_receipts"].get("portfolio")
        if not isinstance(portfolio_receipt, dict) or not isinstance(portfolio_receipt.get("strategies"), dict):
            raise CandidateRefusal("REFUSE_PORTFOLIO_ANTICHAIN_MISSING")
        receipt["portfolio_antichain"] = copy.deepcopy(portfolio_receipt["strategies"])
        _attest_sources(root, definition_path, configs, validator_path, receipt["source_hashes"])
        receipt["status"] = "COMPLETE"
        receipt["reason"] = None
        receipt["contradictions"] = _contradictions(context, receipt["children"])
        receipt["tensions"] = _tensions(context, receipt["children"])
        receipt["disagreements"] = _disagreements(context, receipt["children"])
        receipt["integrity_disposition"] = _integrity_disposition(receipt["children"])
        _set_replay_identity(receipt)
        return _seal(receipt)
    except CandidateRefusal as exc:
        if receipt is not None:
            return _refuse_existing(receipt, str(exc))
        fresh = _base_receipt(
            packet,
            definition_sha=(
                file_digest(definition_path)
                if definition_path is not None and definition_path.is_file()
                else None
            ),
        )
        if root is not None and definition_path is not None and validator_path is not None and configs:
            try:
                fresh["source_hashes"] = _source_hashes(
                    root, definition_path, configs, validator_path, Path(__file__).resolve()
                )
            except (OSError, TypeError, ValueError):
                fresh["source_hashes"] = {}
        return _refuse_existing(fresh, str(exc))
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        reason = f"REFUSE_INTERNAL:{type(exc).__name__}"
        if receipt is not None:
            return _refuse_existing(receipt, reason)
        fresh = _base_receipt(
            packet,
            definition_sha=(
                file_digest(definition_path)
                if definition_path is not None and definition_path.is_file()
                else None
            ),
        )
        return _refuse_existing(fresh, reason)


def _verify_source_bindings(
    receipt: Mapping[str, Any],
    root: Path,
    definition_path: Path,
    configs: Mapping[str, Any],
    validator_path: Path,
) -> bool:
    source_hashes = receipt.get("source_hashes")
    if not isinstance(source_hashes, dict):
        return False
    try:
        expected = _source_hashes(
            root,
            definition_path,
            configs,
            validator_path,
            Path(__file__).resolve(),
        )
    except (OSError, TypeError, ValueError):
        return False
    return source_hashes == expected and receipt.get("definition_sha256") == expected["definition"]


def _no_authority_keys(value: Any) -> bool:
    if isinstance(value, dict):
        if any(key in value for key in {"winner", "selected_strategy", "decision", "implementation"}):
            return False
        return all(_no_authority_keys(item) for item in value.values())
    if isinstance(value, list):
        return all(_no_authority_keys(item) for item in value)
    return True


def verify_receipt(
    receipt: Any,
    packet: Any | None = None,
    *,
    skills_root: Path | None = None,
) -> bool:
    """Verify parent custody, child bindings, source hashes, and replay seal."""

    if (
        not isinstance(receipt, dict)
        or set(receipt) != PARENT_RECEIPT_KEYS
        or receipt.get("schema") != SCHEMA
        or receipt.get("wave_id") != WAVE_ID
        or not _bounded(receipt)
    ):
        return False
    if not _no_authority_keys(receipt):
        return False
    try:
        root = _skills_root(skills_root)
        definition, definition_path, configs, validator_path = _definition(root)
    except (CandidateRefusal, OSError, ValueError):
        return False
    if not _verify_source_bindings(receipt, root, definition_path, configs, validator_path):
        return False
    if receipt.get("route_truth") != ROUTE_TRUTH or receipt.get("route_truth_label") != ROUTE_TRUTH_LABEL:
        return False
    if receipt.get("model_free") is not True or receipt.get("provider_dispatch_proved") is not False:
        return False
    if receipt.get("mmm_preload_applicable") is not False or receipt.get("provider_receipt_applicable") is not False:
        return False
    if receipt.get("provider_call_receipt") is not None or receipt.get("mmm_preload_receipts") != []:
        return False
    if receipt.get("activated") is not False or receipt.get("promotion_allowed") is not False or receipt.get("winner_selected") is not False:
        return False
    if receipt.get("writes_performed") is not False or receipt.get("receipt_written") is not False:
        return False
    if (
        receipt.get("claim_ceiling") != CLAIM_CEILING
        or receipt.get("operation") != PARENT_OPERATION
        or receipt.get("operation_id") != PARENT_OPERATION
    ):
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
    input_hashes = receipt.get("child_input_hashes")
    receipt_hashes = receipt.get("child_receipt_hashes")
    if not isinstance(embedded_inputs, dict) or set(embedded_inputs) != set(CHILD_IDS):
        return False
    if not isinstance(input_hashes, dict) or set(input_hashes) != set(CHILD_IDS):
        return False
    if not isinstance(receipt_hashes, dict) or set(receipt_hashes) != set(ids):
        return False
    target = receipt.get("target")
    try:
        embedded_packet: dict[str, Any] = {
            "schema": INPUT_SCHEMA,
            "wave_id": WAVE_ID,
            "object_card": receipt.get("object_card"),
            "target": target,
            "context": receipt.get("context"),
            "operation": PARENT_OPERATION,
            "child_inputs": embedded_inputs,
        }
        if receipt.get("parent_cancellation_requested") is not None:
            embedded_packet["cancel_requested"] = receipt.get("parent_cancellation_requested")
        normalized_embedded = _packet(embedded_packet, definition, configs)
    except CandidateRefusal:
        return False
    if receipt.get("object_card_sha256") != digest(normalized_embedded["object_card"]):
        return False
    if receipt.get("context_sha256") != digest(normalized_embedded["context"]):
        return False
    if packet is not None:
        try:
            normalized = _packet(packet, definition, configs)
        except CandidateRefusal:
            return False
        if (
            receipt.get("input_sha256") != digest(normalized)
            or receipt.get("child_inputs") != normalized["child_inputs"]
            or receipt.get("object_card") != normalized["object_card"]
            or receipt.get("context") != normalized["context"]
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
        if receipt.get("not_launched_child_ids") != list(CHILD_IDS[len(ids):]):
            return False
        if receipt.get("parent_cancellation_requested") not in {True, False, None}:
            return False
        if receipt.get("parent_cancellation_requested") is True and ids:
            return False
        if receipt.get("parent_cancellation_requested") is not True and (
            not ids or rows[-1].get("terminal_state") != "CANCELLED"
        ):
            return False
    elif receipt.get("status") == "REFUSE":
        if receipt.get("cancellation_state") not in {"NOT_REQUESTED", "CANCELLED"}:
            return False
        if receipt.get("not_launched_child_ids") != list(CHILD_IDS[len(ids):]):
            return False
    elif receipt.get("status") == "HOLD":
        if receipt.get("cancellation_state") != "NOT_REQUESTED":
            return False
        if receipt.get("not_launched_child_ids") != list(CHILD_IDS[len(ids):]):
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
        expected_operation = configs[child_id]["leaf_operation"]
        try:
            _input_identity(child_id, child_input, expected_operation, str(receipt.get("target")))
        except CandidateRefusal:
            return False
        if input_hashes.get(child_id) != digest(child_input):
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
        ):
            return False
        if row.get("input_sha256") != digest(child_input):
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
            if receipt_hashes.get(child_id) is not None:
                return False
            continue
        if not isinstance(child_receipt, dict):
            return False
        if receipt_hashes.get(child_id) != _child_receipt_hash(child_receipt):
            return False
        if row.get("receipt_sha256") != _child_receipt_hash(child_receipt):
            return False
        if row.get("receipt_self_sha256") != child_receipt.get("receipt_sha256"):
            return False
        if row.get("status") != child_receipt.get("status"):
            return False
        if row.get("terminal_state") == "CANCELLED":
            if not _verify_child_cancellation_with_function(
                config["function"],
                config["module"],
                child_receipt,
                child_input,
                root=root,
                source_path=config["script_path"],
                declared_source=config["definition"]["source"],
                child_id=child_id,
            ):
                return False
        elif row.get("terminal_state") == "COMPLETED":
            if not _verify_child(config, child_receipt, child_input):
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
    if receipt.get("tensions") != _tensions(verification_context, rows):
        return False
    if receipt.get("contradictions") != _contradictions(verification_context, rows):
        return False
    if receipt.get("disagreements") != _disagreements(verification_context, rows):
        return False
    expected_integrity = "CANCELLED" if receipt.get("status") == "CANCELLED" else _integrity_disposition(rows)
    if receipt.get("integrity_disposition") != expected_integrity:
        return False
    expected_status, expected_reason = _derive_terminal(receipt)
    if receipt.get("status") != expected_status or receipt.get("reason") != expected_reason:
        return False
    if "portfolio" in receipt["child_receipts"]:
        portfolio = receipt["child_receipts"]["portfolio"]
        if receipt.get("portfolio_antichain") != portfolio.get("strategies"):
            return False
    elif receipt.get("portfolio_antichain") is not None:
        return False
    if receipt.get("output_digest") != digest(_output_view(receipt)):
        return False
    expected_replay = {
        "input_sha256": receipt.get("input_sha256"),
        "definition_sha256": receipt.get("definition_sha256"),
        "source_hashes": copy.deepcopy(receipt.get("source_hashes")),
        "child_input_hashes": copy.deepcopy(receipt.get("child_input_hashes")),
        "child_receipt_hashes": copy.deepcopy(receipt.get("child_receipt_hashes")),
        "output_digest": receipt.get("output_digest"),
    }
    if receipt.get("replay_identity") != expected_replay:
        return False
    unsigned = copy.deepcopy(receipt)
    expected_self = unsigned.pop("receipt_sha256", None)
    expected_self_2 = unsigned.pop("receipt_self_sha256", None)
    return isinstance(expected_self, str) and expected_self == expected_self_2 and digest(unsigned) == expected_self


def replay(
    packet: Any,
    prior: Mapping[str, Any] | None = None,
    *,
    skills_root: Path | None = None,
) -> dict[str, Any]:
    """Re-run the exact packet and report deterministic parent identity."""

    if prior is not None and not verify_receipt(prior, packet, skills_root=skills_root):
        return {
            "schema": SCHEMA,
            "status": "REFUSE",
            "reason": "REFUSE_RECEIPT_TAMPER",
            "digest_match": False,
            "promotion_allowed": False,
            "writes_performed": False,
        }
    current = run_packet(packet, skills_root=skills_root)
    if prior is None:
        return {
            "schema": SCHEMA,
            "status": "REPLAYED",
            "digest_match": True,
            "receipt_sha256": current.get("receipt_sha256"),
            "promotion_allowed": False,
            "writes_performed": False,
        }
    match = current.get("receipt_sha256") == prior.get("receipt_sha256")
    return {
        "schema": SCHEMA,
        "status": "REPLAY_MATCH" if match else "REPLAY_MISMATCH",
        "digest_match": match,
        "receipt_sha256": current.get("receipt_sha256"),
        "promotion_allowed": False,
        "writes_performed": False,
    }


def run(packet: Any, *, skills_root: Path | None = None) -> dict[str, Any]:
    """Compatibility alias for contained callers and focused tests."""

    return run_packet(packet, skills_root=skills_root)


def _prewrite_attest(receipt: Mapping[str, Any], *, skills_root: Path | None = None) -> None:
    """Verify the exact receipt, then re-attest custody immediately prewrite."""

    root = _skills_root(skills_root)
    _definition_data, definition_path, configs, validator_path = _definition(root)
    pinned = receipt.get("source_hashes")
    if not isinstance(pinned, dict):
        raise CandidateRefusal("REFUSE_PREWRITE_SOURCE_BINDING")
    _attest_sources(root, definition_path, configs, validator_path, pinned)
    if not isinstance(receipt, dict) or not verify_receipt(receipt, skills_root=skills_root):
        raise CandidateRefusal("REFUSE_PREWRITE_RECEIPT")


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
            _prewrite_attest(receipt, skills_root=args.root)
            _write_json(args.out, receipt)
        print(json.dumps({"status": receipt.get("status"), "reason": receipt.get("reason")}, sort_keys=True))
        return 0 if receipt.get("status") == "COMPLETE" else 2
    except (CandidateRefusal, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REFUSE", "reason": f"REFUSE_CLI:{type(exc).__name__}"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
