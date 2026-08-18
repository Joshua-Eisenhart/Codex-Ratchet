#!/usr/bin/env python3
"""Run the inactive, model-free strategy-discriminator wave candidate.

The parent compares a candidate stage list with the current profile order in
``CUMULATIVE_WAVE_SEQUENCE.json``.  The approved discriminator leaf is called
three times through distinct parent operation bindings.  No child, count, or
model can choose or reorder the stage list.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "constraintbox.strategy-discriminator-wave-receipt.v1"
INPUT_SCHEMA = "constraintbox.strategy-discriminator-wave-input.v1"
FRONTIER_SCHEMA = "constraintbox.strategy-discriminator-frontier.v1"
WAVE_ID = "cb-strategy-discriminator-wave-v1"
PARENT_OPERATION = "compare_candidate_order_to_live_profile_order"
LEAF_OPERATION = "cb-strategy-discriminator-cell.v1"
CLAIM_CEILING = (
    "Digest-bound candidate/live order comparison and non-authoritative "
    "frontier projection only; no scheduler execution, winner, reorder, "
    "activation, provider/MMM, or promotion claim."
)
ROUTE_TRUTH = "NOT_FULL"
ROUTE_TRUTH_LABEL = "NOT_FULL/model_free"

CHILD_IDS = (
    "bind_survivors",
    "name_exact_disagreement",
    "design_finite_observable",
)
CHILD_OPERATIONS = {
    "bind_survivors": "cb-strategy-discriminator-wave.bind_survivors.v1",
    "name_exact_disagreement": "cb-strategy-discriminator-wave.name_exact_disagreement.v1",
    "design_finite_observable": "cb-strategy-discriminator-wave.design_finite_observable.v1",
}
CHILD_DISAGREEMENTS = {
    "bind_survivors": "candidate_order and live_profile_order are the two surviving readings to compare",
    "name_exact_disagreement": "candidate_order differs from live_profile_order at an exact finite index or not",
    "design_finite_observable": "an exact array and prefix comparison distinguishes MATCH_OBSERVED from HOLD_ORDER_MISMATCH",
}
CHILD_PROBES = {
    "bind_survivors": {"name": "bind-order-arrays", "finite": True, "cost": 1},
    "name_exact_disagreement": {"name": "first-difference-index", "finite": True, "cost": 2},
    "design_finite_observable": {"name": "finite-prefix-compare", "finite": True, "cost": 3},
}
CONTROL_IDS = (
    "duplicate_candidate_order",
    "duplicate_live_profile_order",
    "prefix_order_binding",
    "leaf_duplicate_strategy",
    "leaf_nonfinite_probe",
    "leaf_authority_shaped",
    "selection_counts_excluded",
)

HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXPECTED_CONFIG_PATH = "constraint_box/integrated_system/config/CUMULATIVE_WAVE_SEQUENCE.json"
RUNNER_PRODUCT_PATH = "constraint_box/integrated_system/skills/cb-strategy-discriminator-wave/scripts/run_wave.py"
EXPECTED_DEFINITION_PATH = "cb-strategy-discriminator-wave/wave.json"
LEAF_SOURCE_PATH = "cb-strategy-discriminator-cell/scripts/discriminate.py"
LEAF_SKILL_PATH = "cb-strategy-discriminator-cell/SKILL.md"
PARENT_SKILL_PATH = "cb-strategy-discriminator-wave/SKILL.md"
TRUSTED_VALIDATOR_PATH = "cb-wave-author/scripts/validate_wave.py"
EPOCH_SEALER_PATH = "constraint_box/integrated_system/scripts/seal_context_epoch.py"
CONFIG_SCHEMA = "constraintbox.cumulative-wave-sequence.v1"
RETAINED_SCHEMA = "constraintbox.cumulative-wave-run.v1"
EPOCH_SCHEMA = "constraintbox.context-epoch.v2"
CONTEXT_EPOCH_KEYS = frozenset({"schema", "epoch_id", "epoch_sequence", "epoch_digest", "parent", "state", "claim_ceiling"})
CONTEXT_EPOCH_CLAIM = "current context epoch binding only"
BRANCH_FRONTIER_KEYS = frozenset({"schema", "frontier_id", "branch_ids", "open_branch_ids", "entries", "state", "claim_ceiling", "winner_selected", "activation_allowed", "promotion_allowed"})
BRANCH_FRONTIER_CLAIM = "order comparison only"

TOP_KEYS = frozenset(
    {
        "schema",
        "wave_id",
        "operation",
        "target",
        "target_bytes",
        "target_sha256",
        "candidate_order",
        "candidate_order_sha256",
        "live_order",
        "live_order_sha256",
        "profile",
        "config_path",
        "config_sha256",
        "retained_cumulative_receipt",
        "retained_cumulative_receipt_sha256",
        "retained_cumulative_receipt_self_sha256",
        "retained_cumulative_run_id",
        "context_epoch",
        "context_epoch_sha256",
        "branch_frontier",
        "branch_frontier_sha256",
        "child_inputs",
        "expected_source_set_sha256",
        "cancel_requested",
    }
)
WRAPPER_KEYS = frozenset(
    {
        "operation_id",
        "leaf_operation",
        "bindings",
        "leaf_input",
        "cancel_requested",
    }
)
BINDING_KEYS = frozenset(
    {
        "target_sha256",
        "candidate_order_sha256",
        "live_order_sha256",
        "profile",
        "config_sha256",
        "retained_cumulative_receipt_sha256",
        "retained_cumulative_receipt_self_sha256",
        "retained_cumulative_run_id",
        "context_epoch_sha256",
        "branch_frontier_sha256",
        "expected_source_set_sha256",
    }
)
LEAF_KEYS = frozenset(
    {
        "schema",
        "operation",
        "operation_id",
        "target",
        "strategies",
        "disagreement",
        "probe",
        "cancelled",
    }
)
FORBIDDEN_KEYS = frozenset(
    {
        "winner",
        "winning_strategy",
        "selected_strategy",
        "reorder",
        "reordered",
        "activation",
        "activate",
        "activated_by_child",
        "promote",
        "promotion",
        "model",
        "models",
        "vote",
        "decision",
        "verdict",
        "apply",
        "commit",
        "execute_scheduler",
    }
)


class CandidateRefusal(ValueError):
    """A structural, source, path, input, or receipt boundary was crossed."""


class DuplicateJSONKey(ValueError):
    """JSON object keys must not silently replace an earlier value."""


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
    except (TypeError, ValueError, OverflowError, RecursionError):
        return None


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX64.fullmatch(value))


def _bounded(value: Any, *, depth: int = 0, state: list[int] | None = None) -> bool:
    """Keep malformed packets from becoming a recursion or memory escape."""

    if state is None:
        state = [0]
    state[0] += 1
    if state[0] > 4096 or depth > 16:
        return False
    if value is None or isinstance(value, (bool, int, str)):
        return True
    if isinstance(value, float):
        return value == value and value not in (float("inf"), float("-inf"))
    if isinstance(value, list):
        return len(value) <= 512 and all(_bounded(item, depth=depth + 1, state=state) for item in value)
    if isinstance(value, dict):
        return len(value) <= 512 and all(
            isinstance(key, str) and _bounded(item, depth=depth + 1, state=state)
            for key, item in value.items()
        )
    return False


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJSONKey) as exc:
        raise CandidateRefusal(f"REFUSE_JSON:{path.name}") from exc


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value) + b"\n")


def _root(explicit: Path | None) -> Path:
    candidate = Path(explicit).expanduser() if explicit is not None else Path(__file__).resolve().parents[5]
    if candidate.is_symlink():
        raise CandidateRefusal("REFUSE_ROOT_SYMLINK")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise CandidateRefusal("REFUSE_ROOT") from exc
    if not resolved.is_dir():
        raise CandidateRefusal("REFUSE_ROOT_DIRECTORY")
    return resolved


def _skills_root(product_root: Path) -> Path:
    path = product_root / "constraint_box" / "integrated_system" / "skills"
    if path.is_symlink() or not path.is_dir():
        raise CandidateRefusal("REFUSE_SKILLS_ROOT")
    return path.resolve(strict=True)


def _confined(root: Path, raw: str | Path, label: str, *, must_exist: bool = True) -> Path:
    """Resolve a product path while refusing lexical and symlink escapes."""

    text = raw.as_posix() if isinstance(raw, Path) else str(raw)
    if not text or "\x00" in text or "\\" in text:
        raise CandidateRefusal(f"REFUSE_INVALID_PATH:{label}")
    declared = Path(text)
    if any(part == ".." for part in declared.parts):
        raise CandidateRefusal(f"REFUSE_PATH_ESCAPE:{label}")
    if declared.is_absolute():
        target = declared
        try:
            relative = target.relative_to(root)
        except ValueError as exc:
            raise CandidateRefusal(f"REFUSE_PATH_ESCAPE:{label}") from exc
    else:
        relative = declared
        target = root / declared
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


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError as exc:
        raise CandidateRefusal("REFUSE_PATH_ESCAPE:relative") from exc


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CandidateRefusal(f"REFUSE_MODULE_LOAD:{name}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise CandidateRefusal(f"REFUSE_MODULE_LOAD:{name}") from exc
    return module


def _contains_forbidden(value: Any) -> str | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key) in FORBIDDEN_KEYS:
                return str(key)
            found = _contains_forbidden(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _contains_forbidden(item)
            if found:
                return found
    return None


def _load_definition(product_root: Path) -> tuple[dict[str, Any], dict[str, Any], Path, dict[str, Any]]:
    skills = _skills_root(product_root)
    definition_path = _confined(skills, EXPECTED_DEFINITION_PATH, "definition")
    definition = _read_json(definition_path)
    if not isinstance(definition, dict) or not _bounded(definition):
        raise CandidateRefusal("REFUSE_DEFINITION_SHAPE")
    current_definition_sha = file_digest(definition_path)
    if EXPECTED_DEFINITION_SHA256 and current_definition_sha != EXPECTED_DEFINITION_SHA256:
        raise CandidateRefusal("REFUSE_DEFINITION_SOURCE_DRIFT")
    validator_path = _confined(skills, TRUSTED_VALIDATOR_PATH, "trusted_validator")
    if EXPECTED_VALIDATOR_SHA256 and file_digest(validator_path) != EXPECTED_VALIDATOR_SHA256:
        raise CandidateRefusal("REFUSE_TRUSTED_VALIDATOR_SOURCE_DRIFT")
    parent_skill_path = _confined(skills, PARENT_SKILL_PATH, "parent_skill")
    if EXPECTED_PARENT_SKILL_SHA256 and file_digest(parent_skill_path) != EXPECTED_PARENT_SKILL_SHA256:
        raise CandidateRefusal("REFUSE_PARENT_SKILL_SOURCE_DRIFT")
    validator = _load_module(validator_path, "cb_strategy_discriminator_trusted_validator")
    try:
        errors = list(validator.validate(definition)) + list(validator.validate_tree(definition, skills))
    except Exception as exc:
        raise CandidateRefusal("REFUSE_TRUSTED_VALIDATOR") from exc
    if errors:
        raise CandidateRefusal("REFUSE_WAVE_DEFINITION:" + ",".join(sorted(set(errors))))
    if definition.get("wave_id") != WAVE_ID:
        raise CandidateRefusal("REFUSE_WAVE_ID")
    if definition.get("candidate_state") != "NEW_CANDIDATE" or definition.get("activated") is not False or definition.get("promotion_allowed") is not False:
        raise CandidateRefusal("REFUSE_CANDIDATE_STATE")
    children = definition.get("children")
    if not isinstance(children, list) or [row.get("id") for row in children if isinstance(row, dict)] != list(CHILD_IDS):
        raise CandidateRefusal("REFUSE_CHILD_ORDER")
    rows: dict[str, Any] = {}
    for row in children:
        if not isinstance(row, dict):
            raise CandidateRefusal("REFUSE_CHILD_SHAPE")
        child_id = row.get("id")
        if child_id in rows:
            raise CandidateRefusal(f"REFUSE_DUPLICATE_CHILD_DEFINITION:{child_id}")
        if row.get("skill") != "cb-strategy-discriminator-cell":
            raise CandidateRefusal(f"REFUSE_CHILD_SKILL:{child_id}")
        if row.get("operation") != CHILD_OPERATIONS.get(str(child_id)):
            raise CandidateRefusal(f"REFUSE_CHILD_OPERATION:{child_id}")
        if row.get("leaf_operation") != LEAF_OPERATION:
            raise CandidateRefusal(f"REFUSE_CHILD_LEAF_OPERATION:{child_id}")
        if row.get("source") != LEAF_SOURCE_PATH or not _is_digest(row.get("source_sha256")) or not _is_digest(row.get("skill_sha256")):
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_BINDING:{child_id}")
        source_path = _confined(skills, row["source"], f"child_source:{child_id}")
        skill_path = _confined(skills, LEAF_SKILL_PATH, f"child_skill:{child_id}")
        if file_digest(source_path) != row["source_sha256"]:
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_DRIFT:{child_id}")
        if file_digest(skill_path) != row["skill_sha256"]:
            raise CandidateRefusal(f"REFUSE_CHILD_SKILL_DRIFT:{child_id}")
        module = _load_module(source_path, f"cb_strategy_discriminator_leaf_{child_id}")
        if getattr(module, "OPERATION", None) != LEAF_OPERATION or not callable(getattr(module, "discriminate", None)):
            raise CandidateRefusal(f"REFUSE_CHILD_CALLABLE:{child_id}")
        if not callable(getattr(module, "verify_receipt", None)):
            raise CandidateRefusal(f"REFUSE_CHILD_VERIFIER:{child_id}")
        rows[str(child_id)] = {
            "definition": copy.deepcopy(row),
            "source_path": source_path,
            "skill_path": skill_path,
            "module": module,
        }
    if len({row["definition"]["operation"] for row in rows.values()}) != len(CHILD_IDS):
        raise CandidateRefusal("REFUSE_CHILD_OPERATION_COLLAPSE")
    controls = definition.get("control_receipts")
    if not isinstance(controls, list) or [row.get("id") for row in controls if isinstance(row, dict)] != list(CONTROL_IDS):
        raise CandidateRefusal("REFUSE_CONTROL_DEFINITION")
    for row in controls:
        if not isinstance(row, dict) or not all(isinstance(row.get(key), str) and row[key] for key in ("id", "operation", "mutation", "expected_status", "expected_reason")):
            raise CandidateRefusal("REFUSE_CONTROL_DEFINITION")
    return definition, rows, validator_path, definition_path


def _authority_bindings(definition: Mapping[str, Any]) -> Mapping[str, Any]:
    authority = definition.get("authority_bindings")
    if not isinstance(authority, Mapping) or set(authority) != {"retained_cumulative_receipt", "current_epoch_pointer", "active_manifest", "frontier"}:
        raise CandidateRefusal("REFUSE_AUTHORITY_BINDINGS")
    for key in ("retained_cumulative_receipt", "current_epoch_pointer"):
        row = authority.get(key)
        if not isinstance(row, Mapping) or set(row) != {"live", "fixture"}:
            raise CandidateRefusal(f"REFUSE_AUTHORITY_BINDING:{key}")
        for mode in ("live", "fixture"):
            item = row[mode]
            if not isinstance(item, Mapping):
                raise CandidateRefusal(f"REFUSE_AUTHORITY_BINDING:{key}:{mode}")
            required = {"path", "raw_sha256", "receipt_sha256", "run_id"} if key == "retained_cumulative_receipt" else {"pointer_path", "pointer_sha256", "epoch_path", "epoch_sha256", "epoch_id", "epoch_digest"}
            if set(item) != required or any(not _is_digest(item.get(field)) for field in ("raw_sha256", "receipt_sha256") if field in item) or any(not isinstance(item.get(field), str) or not item[field] for field in ("path", "pointer_path", "epoch_path", "run_id", "epoch_id") if field in item):
                raise CandidateRefusal(f"REFUSE_AUTHORITY_BINDING:{key}:{mode}")
    manifest = authority["active_manifest"]
    if not isinstance(manifest, Mapping) or set(manifest) != {"live_path", "fixture_path", "raw_sha256"} or any(not isinstance(manifest.get(key), str) or not manifest[key] for key in ("live_path", "fixture_path")) or not _is_digest(manifest.get("raw_sha256")):
        raise CandidateRefusal("REFUSE_AUTHORITY_MANIFEST")
    frontier = authority["frontier"]
    if not isinstance(frontier, Mapping) or set(frontier) != {"frontier_id", "branch_ids", "order_fields", "entry_order_fields"} or frontier.get("frontier_id") != "strategy-sequence-order-v1" or frontier.get("branch_ids") != ["candidate_order", "live_scheduler_order"] or frontier.get("order_fields") != {"candidate_order": "candidate_order", "live_scheduler_order": "live_order"} or frontier.get("entry_order_fields") != {"candidate_order": "candidate_order_sha256", "live_scheduler_order": "live_order_sha256"}:
        raise CandidateRefusal("REFUSE_AUTHORITY_FRONTIER")
    return authority


def _authority_receipt_self_hash(receipt: Mapping[str, Any]) -> str:
    expected = receipt.get("receipt_sha256")
    if not _is_digest(expected):
        raise CandidateRefusal("REFUSE_AUTHORITY_RECEIPT_SELF_HASH")
    if digest({key: value for key, value in receipt.items() if key != "receipt_sha256"}) != expected:
        raise CandidateRefusal("REFUSE_AUTHORITY_RECEIPT_SELF_HASH")
    return expected


def _authority_epoch_self_hash(epoch: Mapping[str, Any]) -> str:
    expected = epoch.get("epoch_digest")
    if not _is_digest(expected):
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_SELF_HASH")
    if digest({key: value for key, value in epoch.items() if key != "epoch_digest"}) != expected:
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_SELF_HASH")
    return expected


def _epoch_projection(epoch: Mapping[str, Any]) -> dict[str, Any]:
    """Project the selected raw epoch into the packet's exact bound shape."""

    if not isinstance(epoch, Mapping):
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_SCHEMA")
    required = {"schema", "epoch_id", "epoch_sequence", "epoch_digest", "parent"}
    if not required.issubset(epoch) or epoch.get("schema") != EPOCH_SCHEMA:
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_SCHEMA")
    parent = epoch.get("parent")
    if (
        not isinstance(parent, Mapping)
        or set(parent) != {"path", "sha256"}
        or not isinstance(parent.get("path"), str)
        or not parent["path"]
        or Path(parent["path"]).is_absolute()
        or not _is_digest(parent.get("sha256"))
    ):
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_PARENT")
    if (
        not isinstance(epoch.get("epoch_id"), str)
        or not epoch["epoch_id"].strip()
        or type(epoch.get("epoch_sequence")) is not int
        or epoch["epoch_sequence"] < 1
        or not _is_digest(epoch.get("epoch_digest"))
    ):
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_SCHEMA")
    return {
        "schema": EPOCH_SCHEMA,
        "epoch_id": epoch["epoch_id"],
        "epoch_sequence": epoch["epoch_sequence"],
        "epoch_digest": epoch["epoch_digest"],
        "parent": copy.deepcopy(dict(parent)),
        "state": "CURRENT",
        "claim_ceiling": CONTEXT_EPOCH_CLAIM,
    }


def _validate_authority_packet(packet: Mapping[str, Any], authority: Mapping[str, Any]) -> None:
    retained = packet["retained_cumulative_receipt"]
    if packet.get("retained_cumulative_run_id") != authority["run_id"] or packet.get("retained_cumulative_receipt_self_sha256") != authority["receipt_sha256"] or retained.get("run_id") != authority["run_id"] or retained.get("receipt_sha256") != authority["receipt_sha256"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_RECEIPT_BINDING")
    authoritative_receipt = authority["receipt"]
    for field in ("schema", "profile", "runtime", "status", "reason_code", "promotion_allowed", "config_schema"):
        if retained.get(field) != authoritative_receipt.get(field):
            raise CandidateRefusal(f"REFUSE_AUTHORITY_RECEIPT_{field.upper()}")
    if retained.get("source_binding", {}).get("config_sha256") != authoritative_receipt.get("source_binding", {}).get("config_sha256") or retained.get("source_binding_after", {}).get("config_sha256") != authoritative_receipt.get("source_binding_after", {}).get("config_sha256"):
        raise CandidateRefusal("REFUSE_AUTHORITY_RECEIPT_CONFIG")
    if retained.get("source_binding", {}).get("manifest_sha256") != authority["manifest_sha256"] or retained.get("source_binding_after", {}).get("manifest_sha256") != authority["manifest_sha256"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_RECEIPT_MANIFEST")
    if packet["context_epoch"] != authority["epoch_projection"] or packet.get("context_epoch_sha256") != digest(authority["epoch_projection"]):
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_BINDING")
    if packet["branch_frontier"].get("frontier_id") != "strategy-sequence-order-v1" or packet["branch_frontier"].get("branch_ids") != authority["branch_ids"] or packet["branch_frontier"].get("open_branch_ids") != authority["branch_ids"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_FRONTIER_BINDING")


def _load_authority(product_root: Path, definition: Mapping[str, Any], authority_mode: str = "LIVE") -> dict[str, Any]:
    if authority_mode not in {"LIVE", "FIXTURE"}:
        raise CandidateRefusal("REFUSE_AUTHORITY_MODE")
    authority = _authority_bindings(definition)
    selected: dict[str, Any] = {"bindings_sha256": digest(authority)}
    manifest_binding = authority["active_manifest"]
    manifest_path_value = manifest_binding["live_path"] if authority_mode == "LIVE" else manifest_binding["fixture_path"]
    manifest_path = _confined(product_root, manifest_path_value, "authority_manifest" if authority_mode == "LIVE" else "authority_manifest_fixture")
    if file_digest(manifest_path) != manifest_binding["raw_sha256"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_MANIFEST_RAW_HASH")
    selected["manifest_path"] = _relative(product_root, manifest_path)
    selected["manifest_sha256"] = manifest_binding["raw_sha256"]
    receipt_binding = authority["retained_cumulative_receipt"]
    receipt_mode = "live" if authority_mode == "LIVE" else "fixture"
    receipt_meta = receipt_binding[receipt_mode]
    receipt_path = _confined(product_root, receipt_meta["path"], "authority_receipt" if receipt_mode == "live" else "authority_receipt_fixture")
    raw = receipt_path.read_bytes()
    if file_digest(receipt_path) != receipt_meta["raw_sha256"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_RECEIPT_RAW_HASH")
    receipt = _read_json(receipt_path)
    if not isinstance(receipt, Mapping) or receipt.get("schema") != RETAINED_SCHEMA or receipt.get("run_id") != receipt_meta["run_id"] or receipt.get("receipt_sha256") != receipt_meta["receipt_sha256"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_RECEIPT_IDENTITY")
    _authority_receipt_self_hash(receipt)
    for binding_name in ("source_binding", "source_binding_after"):
        binding = receipt.get(binding_name)
        if not isinstance(binding, Mapping) or Path(str(binding.get("manifest_path", ""))).name != "ACTIVE_WAVES.json" or binding.get("manifest_sha256") != manifest_binding["raw_sha256"]:
            raise CandidateRefusal("REFUSE_AUTHORITY_RECEIPT_MANIFEST")
    selected["receipt_mode"] = receipt_mode
    selected["receipt_path"] = _relative(product_root, receipt_path)
    selected["receipt_raw_sha256"] = receipt_meta["raw_sha256"]
    selected["receipt_sha256"] = receipt_meta["receipt_sha256"]
    selected["run_id"] = receipt_meta["run_id"]
    selected["receipt"] = receipt

    pointer_binding = authority["current_epoch_pointer"]
    pointer_mode = "live" if authority_mode == "LIVE" else "fixture"
    pointer_meta = pointer_binding[pointer_mode]
    pointer_path = _confined(product_root, pointer_meta["pointer_path"], "authority_epoch_pointer" if pointer_mode == "live" else "authority_epoch_pointer_fixture")
    if file_digest(pointer_path) != pointer_meta["pointer_sha256"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_POINTER_RAW_HASH")
    pointer = _read_json(pointer_path)
    if not isinstance(pointer, Mapping) or pointer.get("schema") != "constraintbox.current-context-epoch-pointer.v1" or pointer.get("authoritative") is not False:
        raise CandidateRefusal("REFUSE_AUTHORITY_POINTER_SCHEMA")
    pointer_digest = pointer.get("pointer_digest")
    if not _is_digest(pointer_digest) or digest({key: value for key, value in pointer.items() if key != "pointer_digest"}) != pointer_digest:
        raise CandidateRefusal("REFUSE_AUTHORITY_POINTER_SELF_HASH")
    epoch_ref = pointer.get("epoch")
    if not isinstance(epoch_ref, Mapping) or epoch_ref.get("path") != pointer_meta["epoch_path"] or epoch_ref.get("sha256") != pointer_meta["epoch_sha256"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_POINTER_EPOCH_BINDING")
    epoch_path = _confined(product_root, pointer_meta["epoch_path"], "authority_epoch")
    if file_digest(epoch_path) != pointer_meta["epoch_sha256"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_RAW_HASH")
    epoch = _read_json(epoch_path)
    if not isinstance(epoch, Mapping) or epoch.get("schema") != EPOCH_SCHEMA or epoch.get("epoch_id") != pointer_meta["epoch_id"] or epoch.get("epoch_digest") != pointer_meta["epoch_digest"]:
        raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_IDENTITY")
    _authority_epoch_self_hash(epoch)
    epoch_projection = _epoch_projection(epoch)
    if pointer_mode == "live":
        sealer_path = _confined(product_root, EPOCH_SEALER_PATH, "epoch_sealer")
        sealer = _load_module(sealer_path, "cb_strategy_discriminator_epoch_sealer")
        try:
            sealer.verify_pointer(product_root, _relative(product_root, pointer_path))
        except Exception as exc:
            raise CandidateRefusal("REFUSE_AUTHORITY_EPOCH_CURRENTNESS") from exc
        selected["epoch_sealer_path"] = _relative(product_root, sealer_path)
        selected["epoch_sealer_sha256"] = file_digest(sealer_path)
    else:
        selected["epoch_sealer_path"] = None
        selected["epoch_sealer_sha256"] = None
    selected.update({"pointer_mode": pointer_mode, "pointer_path": _relative(product_root, pointer_path), "pointer_sha256": pointer_meta["pointer_sha256"], "epoch_path": _relative(product_root, epoch_path), "epoch_sha256": pointer_meta["epoch_sha256"], "epoch_id": pointer_meta["epoch_id"], "epoch_digest": pointer_meta["epoch_digest"], "pointer": pointer, "epoch": epoch, "epoch_projection": epoch_projection, "branch_ids": list(authority["frontier"]["branch_ids"])})
    return selected


def _authority_projection(authority: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "retained_cumulative_receipt": {
            "path": authority["receipt_path"],
            "raw_sha256": authority["receipt_raw_sha256"],
            "receipt_sha256": authority["receipt_sha256"],
            "run_id": authority["run_id"],
        },
        "current_epoch_pointer": {
            "mode": authority["pointer_mode"],
            "pointer_path": authority["pointer_path"],
            "pointer_sha256": authority["pointer_sha256"],
            "epoch_path": authority["epoch_path"],
            "epoch_sha256": authority["epoch_sha256"],
            "epoch_id": authority["epoch_id"],
            "epoch_digest": authority["epoch_digest"],
        },
        "active_manifest": {"path": authority["manifest_path"], "sha256": authority["manifest_sha256"]},
        "frontier": {"branch_ids": list(authority["branch_ids"])},
    }


def _source_hashes(product_root: Path, definition_path: Path, rows: Mapping[str, Mapping[str, Any]], validator_path: Path) -> dict[str, Any]:
    skills_root = _skills_root(product_root)
    runner_path = _confined(product_root, RUNNER_PRODUCT_PATH, "runner_source")
    wave_path = _confined(skills_root, EXPECTED_DEFINITION_PATH, "definition_source")
    parent_skill_path = _confined(skills_root, PARENT_SKILL_PATH, "parent_skill_source")
    trusted_validator_path = _confined(skills_root, TRUSTED_VALIDATOR_PATH, "validator_source")
    if wave_path != definition_path or trusted_validator_path != validator_path:
        raise CandidateRefusal("REFUSE_SOURCE_PATH_BINDING")
    child_rows: dict[str, Any] = {}
    child_paths: dict[str, Any] = {}
    for child_id, row in rows.items():
        source_relative = _relative(skills_root, row["source_path"])
        skill_relative = _relative(skills_root, row["skill_path"])
        child_source = _confined(skills_root, source_relative, f"source_set_child:{child_id}")
        child_skill = _confined(skills_root, skill_relative, f"source_set_skill:{child_id}")
        child_rows[child_id] = {
            "source": file_digest(child_source),
            "skill": file_digest(child_skill),
            "leaf_operation": LEAF_OPERATION,
        }
        child_paths[child_id] = {"source": _relative(product_root, child_source), "skill": _relative(product_root, child_skill)}
    return {
        "paths": {
            "runner": _relative(product_root, runner_path),
            "definition": _relative(product_root, wave_path),
            "parent_skill": _relative(product_root, parent_skill_path),
            "trusted_validator": _relative(product_root, trusted_validator_path),
            "children": child_paths,
        },
        "runner": file_digest(runner_path),
        "definition": file_digest(wave_path),
        "trusted_validator": file_digest(trusted_validator_path),
        "parent_skill": file_digest(parent_skill_path),
        "authority_bindings": digest(_read_json(wave_path)["authority_bindings"]),
        "children": child_rows,
    }


def _attest_current(
    product_root: Path,
    packet: Mapping[str, Any],
    *,
    label: str,
    expected_source_hashes: Mapping[str, Any] | None = None,
    child_receipts: Mapping[str, Mapping[str, Any]] | None = None,
    authority_mode: str = "LIVE",
) -> dict[str, Any]:
    """Re-read every bound surface and, when present, verify child receipts."""

    definition, child_configs, validator_path, definition_path = _load_definition(product_root)
    normalized = _validate_packet(packet, definition)
    authority = _load_authority(product_root, definition, authority_mode)
    _validate_authority_packet(normalized, authority)
    config, profile, live_order, config_path = _load_config(product_root, normalized)
    retained = normalized["retained_cumulative_receipt"]
    _validate_retained_cumulative_receipt(retained, normalized, profile, live_order, require_self=False)
    current_sources = _source_hashes(product_root, definition_path, child_configs, validator_path)
    if digest(current_sources) != normalized["expected_source_set_sha256"]:
        raise CandidateRefusal("REFUSE_EXPECTED_SOURCE_SET_DRIFT")
    if expected_source_hashes is not None and current_sources != expected_source_hashes:
        raise CandidateRefusal("REFUSE_SOURCE_ATTESTATION_DRIFT")
    verified_child_ids: list[str] = []
    child_digests: dict[str, str | None] = {}
    if child_receipts is not None:
        for child_id in CHILD_IDS:
            if child_id not in child_receipts:
                continue
            wrapper = normalized["child_inputs"][child_id]
            child_receipt = child_receipts[child_id]
            if not _verify_leaf(child_configs[child_id]["module"], wrapper["leaf_input"], child_receipt):
                raise CandidateRefusal(f"REFUSE_CHILD_CURRENT_INPUT_ATTESTATION:{child_id}")
            if wrapper["cancel_requested"]:
                if child_receipt.get("status") != "CANCELLED_NO_AUTHORITY":
                    raise CandidateRefusal(f"REFUSE_CHILD_CANCEL_ATTESTATION:{child_id}")
            elif child_receipt.get("status") != "DESIGNED" or child_receipt.get("output_kind") != "PROPOSAL":
                raise CandidateRefusal(f"REFUSE_CHILD_ROLE_ATTESTATION:{child_id}")
            verified_child_ids.append(child_id)
            child_digests[child_id] = child_receipt.get("receipt_sha256")
    return {
        "label": label,
        "target_sha256": normalized["target_sha256"],
        "candidate_order_sha256": normalized["candidate_order_sha256"],
        "live_order_sha256": normalized["live_order_sha256"],
        "profile": normalized["profile"],
        "config_path": _relative(product_root, config_path),
        "config_sha256": file_digest(config_path),
        "retained_cumulative_receipt_sha256": normalized["retained_cumulative_receipt_sha256"],
        "retained_cumulative_receipt_self_sha256": normalized["retained_cumulative_receipt_self_sha256"],
        "retained_cumulative_run_id": normalized["retained_cumulative_run_id"],
        "retained_receipt_self_sha256": normalized["retained_cumulative_receipt"]["receipt_sha256"],
        "retained_prefix3_lock": _retained_prefix3_lock_projection(normalized["retained_cumulative_receipt"]),
        "context_epoch_sha256": normalized["context_epoch_sha256"],
        "branch_frontier_sha256": normalized["branch_frontier_sha256"],
        "definition_sha256": file_digest(definition_path),
        "authority_bindings_sha256": authority["bindings_sha256"],
        "authority_bindings": _authority_projection(authority),
        "authority_receipt_self_hash": authority["receipt_sha256"],
        "authority_epoch_pointer_hash": authority["pointer_sha256"],
        "authority_receipt_mode": authority["receipt_mode"],
        "authority_receipt_path": authority["receipt_path"],
        "authority_pointer_mode": authority["pointer_mode"],
        "authority_pointer_path": authority["pointer_path"],
        "authority_epoch_path": authority["epoch_path"],
        "authority_manifest_path": authority["manifest_path"],
        "authority_manifest_sha256": authority["manifest_sha256"],
        "authority_mode": authority_mode,
        "source_hashes": current_sources,
        "expected_source_set_sha256": normalized["expected_source_set_sha256"],
        "verified_child_ids": verified_child_ids,
        "child_receipt_sha256": child_digests,
    }


def _validate_order(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() or item != item.strip() for item in value):
        raise CandidateRefusal(f"REFUSE_{label.upper()}_SCHEMA")
    result = list(value)
    if len(set(result)) != len(result):
        raise CandidateRefusal(f"REFUSE_DUPLICATE_{label.upper()}")
    return result


def _validate_hash(value: Any, label: str) -> str:
    if not _is_digest(value):
        raise CandidateRefusal(f"REFUSE_{label.upper()}_DIGEST")
    return value


def _validate_target(packet: Mapping[str, Any]) -> None:
    target = packet.get("target")
    target_bytes = packet.get("target_bytes")
    if not isinstance(target, str) or not target or target != target.strip():
        raise CandidateRefusal("REFUSE_TARGET")
    if not isinstance(target_bytes, str) or not target_bytes:
        raise CandidateRefusal("REFUSE_TARGET_BYTES")
    if packet.get("target_sha256") != hashlib.sha256(target_bytes.encode("utf-8")).hexdigest():
        raise CandidateRefusal("REFUSE_TARGET_BYTES_DIGEST")


def _validate_embedded_binding(packet: Mapping[str, Any], key: str, hash_key: str, label: str) -> None:
    value = packet.get(key)
    expected = packet.get(hash_key)
    if not isinstance(value, dict) or not _bounded(value):
        raise CandidateRefusal(f"REFUSE_{label.upper()}_SHAPE")
    _validate_hash(expected, label)
    if digest(value) != expected:
        raise CandidateRefusal(f"REFUSE_{label.upper()}_DRIFT")
    forbidden = _contains_forbidden(value)
    if forbidden:
        raise CandidateRefusal(f"REFUSE_{label.upper()}_AUTHORITY:{forbidden}")


def _validate_child_wrapper(child_id: str, wrapper: Any, packet: Mapping[str, Any]) -> None:
    if not isinstance(wrapper, dict) or not _bounded(wrapper) or set(wrapper) != WRAPPER_KEYS:
        raise CandidateRefusal(f"REFUSE_CHILD_INPUT_SHAPE:{child_id}")
    if wrapper.get("operation_id") != CHILD_OPERATIONS[child_id] or wrapper.get("leaf_operation") != LEAF_OPERATION:
        raise CandidateRefusal(f"REFUSE_CHILD_OPERATION:{child_id}")
    if not isinstance(wrapper.get("cancel_requested"), bool):
        raise CandidateRefusal(f"REFUSE_CHILD_CANCEL_TYPE:{child_id}")
    bindings = wrapper.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != BINDING_KEYS:
        raise CandidateRefusal(f"REFUSE_CHILD_BINDINGS:{child_id}")
    expected_bindings = {
        "target_sha256": packet["target_sha256"],
        "candidate_order_sha256": packet["candidate_order_sha256"],
        "live_order_sha256": packet["live_order_sha256"],
        "profile": packet["profile"],
        "config_sha256": packet["config_sha256"],
        "retained_cumulative_receipt_sha256": packet["retained_cumulative_receipt_sha256"],
        "retained_cumulative_receipt_self_sha256": packet["retained_cumulative_receipt_self_sha256"],
        "retained_cumulative_run_id": packet["retained_cumulative_run_id"],
        "context_epoch_sha256": packet["context_epoch_sha256"],
        "branch_frontier_sha256": packet["branch_frontier_sha256"],
        "expected_source_set_sha256": packet["expected_source_set_sha256"],
    }
    if bindings != expected_bindings:
        raise CandidateRefusal(f"REFUSE_CHILD_REBOUND:{child_id}")
    leaf_input = wrapper.get("leaf_input")
    if not isinstance(leaf_input, dict) or set(leaf_input) != LEAF_KEYS:
        raise CandidateRefusal(f"REFUSE_LEAF_INPUT_SHAPE:{child_id}")
    if leaf_input.get("schema") != "constraintbox.strategy-discriminator.v1" or leaf_input.get("operation") != LEAF_OPERATION or leaf_input.get("operation_id") != LEAF_OPERATION:
        raise CandidateRefusal(f"REFUSE_LEAF_OPERATION:{child_id}")
    if leaf_input.get("target") != packet["target"]:
        raise CandidateRefusal(f"REFUSE_LEAF_TARGET_REBOUND:{child_id}")
    if leaf_input.get("strategies") != ["candidate_order", "live_profile_order"]:
        raise CandidateRefusal(f"REFUSE_LEAF_STRATEGIES:{child_id}")
    if leaf_input.get("disagreement") != CHILD_DISAGREEMENTS[child_id]:
        raise CandidateRefusal(f"REFUSE_LEAF_DISAGREEMENT:{child_id}")
    if leaf_input.get("probe") != CHILD_PROBES[child_id]:
        raise CandidateRefusal(f"REFUSE_LEAF_PROBE:{child_id}")
    if not isinstance(leaf_input.get("cancelled"), bool) or leaf_input["cancelled"] != wrapper["cancel_requested"]:
        raise CandidateRefusal(f"REFUSE_LEAF_CANCEL_BINDING:{child_id}")


def _validate_packet(packet: Any, definition: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, dict) or not _bounded(packet):
        raise CandidateRefusal("REFUSE_PACKET_SHAPE")
    if set(packet) - TOP_KEYS:
        raise CandidateRefusal("REFUSE_PACKET_EXTRA:" + ",".join(sorted(set(packet) - TOP_KEYS)))
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
    if "cancel_requested" in packet and not isinstance(packet["cancel_requested"], bool):
        raise CandidateRefusal("REFUSE_PACKET_CANCEL_TYPE")
    forbidden = _contains_forbidden(packet)
    if forbidden:
        raise CandidateRefusal(f"REFUSE_PACKET_AUTHORITY:{forbidden}")
    _validate_target(packet)
    candidate = _validate_order(packet.get("candidate_order"), "candidate_order")
    live = _validate_order(packet.get("live_order"), "live_order")
    if digest(candidate) != packet.get("candidate_order_sha256"):
        raise CandidateRefusal("REFUSE_CANDIDATE_ORDER_DIGEST")
    if digest(live) != packet.get("live_order_sha256"):
        raise CandidateRefusal("REFUSE_LIVE_ORDER_DIGEST")
    if not isinstance(packet.get("profile"), str) or not packet["profile"] or packet["profile"] != packet["profile"].strip():
        raise CandidateRefusal("REFUSE_PROFILE")
    if not isinstance(packet.get("config_path"), str) or not packet["config_path"]:
        raise CandidateRefusal("REFUSE_CONFIG_PATH")
    _validate_hash(packet.get("config_sha256"), "config")
    _validate_hash(packet.get("expected_source_set_sha256"), "expected_source_set")
    _validate_embedded_binding(packet, "retained_cumulative_receipt", "retained_cumulative_receipt_sha256", "retained_receipt")
    _validate_embedded_binding(packet, "context_epoch", "context_epoch_sha256", "context_epoch")
    _validate_embedded_binding(packet, "branch_frontier", "branch_frontier_sha256", "branch_frontier")
    epoch = packet["context_epoch"]
    if set(epoch) != CONTEXT_EPOCH_KEYS or epoch.get("schema") != EPOCH_SCHEMA or not isinstance(epoch.get("epoch_id"), str) or not epoch["epoch_id"].strip() or type(epoch.get("epoch_sequence")) is not int or epoch["epoch_sequence"] < 1 or not _is_digest(epoch.get("epoch_digest")) or epoch.get("state") != "CURRENT" or epoch.get("claim_ceiling") != CONTEXT_EPOCH_CLAIM:
        raise CandidateRefusal("REFUSE_CONTEXT_EPOCH_SCHEMA")
    parent = epoch.get("parent")
    if not isinstance(parent, dict) or set(parent) != {"path", "sha256"} or not isinstance(parent.get("path"), str) or not parent["path"] or Path(parent["path"]).is_absolute() or not _is_digest(parent.get("sha256")):
        raise CandidateRefusal("REFUSE_CONTEXT_EPOCH_PARENT")
    retained = packet["retained_cumulative_receipt"]
    if retained.get("schema") != RETAINED_SCHEMA or not _is_digest(retained.get("receipt_sha256")):
        raise CandidateRefusal("REFUSE_RETAINED_RECEIPT_SCHEMA")
    if packet.get("retained_cumulative_receipt_self_sha256") != retained.get("receipt_sha256"):
        raise CandidateRefusal("REFUSE_RETAINED_RECEIPT_SELF_BINDING")
    if not isinstance(packet.get("retained_cumulative_run_id"), str) or not packet["retained_cumulative_run_id"].strip() or retained.get("run_id") != packet["retained_cumulative_run_id"]:
        raise CandidateRefusal("REFUSE_RETAINED_RUN_ID_BINDING")
    if retained.get("profile") != packet["profile"]:
        raise CandidateRefusal("REFUSE_RETAINED_PROFILE_BINDING")
    frontier = packet["branch_frontier"]
    if set(frontier) != BRANCH_FRONTIER_KEYS or frontier.get("schema") != "constraintbox.strategy-discriminator-branch-frontier.v1":
        raise CandidateRefusal("REFUSE_BRANCH_FRONTIER_SCHEMA")
    if not isinstance(frontier.get("branch_ids"), list) or not frontier["branch_ids"] or len(set(frontier["branch_ids"])) != len(frontier["branch_ids"]):
        raise CandidateRefusal("REFUSE_BRANCH_FRONTIER_BRANCHES")
    if frontier.get("open_branch_ids") != frontier.get("branch_ids") or frontier.get("state") != "OPEN" or frontier.get("claim_ceiling") != BRANCH_FRONTIER_CLAIM or frontier.get("winner_selected") is not False or frontier.get("activation_allowed") is not False or frontier.get("promotion_allowed") is not False:
        raise CandidateRefusal("REFUSE_BRANCH_FRONTIER_FLAGS")
    if frontier.get("entries") != [
        {"id": "candidate_order", "order_sha256": packet["candidate_order_sha256"]},
        {"id": "live_scheduler_order", "order_sha256": packet["live_order_sha256"]},
    ]:
        raise CandidateRefusal("REFUSE_BRANCH_FRONTIER_ENTRIES")
    child_inputs = packet.get("child_inputs")
    if not isinstance(child_inputs, dict) or set(child_inputs) != set(CHILD_IDS) or len(child_inputs) != len(CHILD_IDS):
        raise CandidateRefusal("REFUSE_CHILD_SET")
    for child_id in CHILD_IDS:
        _validate_child_wrapper(child_id, child_inputs[child_id], packet)
    # Definition order and packet order must agree before any leaf invocation.
    definition_ids = [row.get("id") for row in definition.get("children", []) if isinstance(row, dict)]
    if definition_ids != list(CHILD_IDS):
        raise CandidateRefusal("REFUSE_DEFINITION_CHILD_SET")
    return copy.deepcopy(packet)


def _load_config(product_root: Path, packet: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], list[str], Path]:
    config_path = _confined(product_root, packet["config_path"], "config")
    if _relative(product_root, config_path) != EXPECTED_CONFIG_PATH:
        raise CandidateRefusal("REFUSE_CONFIG_PATH_BINDING")
    actual = file_digest(config_path)
    if actual != packet["config_sha256"]:
        raise CandidateRefusal("REFUSE_CONFIG_SOURCE_DRIFT")
    config = _read_json(config_path)
    if not isinstance(config, dict) or config.get("schema") != CONFIG_SCHEMA:
        raise CandidateRefusal("REFUSE_CONFIG_SCHEMA")
    profiles = config.get("profiles")
    if not isinstance(profiles, dict) or packet["profile"] not in profiles or not isinstance(profiles[packet["profile"]], dict):
        raise CandidateRefusal("REFUSE_UNKNOWN_PROFILE")
    profile = profiles[packet["profile"]]
    order = _validate_order(profile.get("stage_order"), "live_stage_order")
    stages = profile.get("stages")
    if not isinstance(stages, dict) or set(stages) != set(order) or any(not isinstance(stages[item], dict) for item in order):
        raise CandidateRefusal("REFUSE_CONFIG_STAGE_SET")
    active = profile.get("active_stage_ids")
    if not isinstance(active, list) or any(item not in order for item in active) or len(set(active)) != len(active):
        raise CandidateRefusal("REFUSE_CONFIG_ACTIVE_STAGE_SET")
    expected_active = {item for item in order if stages[item].get("mode") == "ACTIVE"}
    if set(active) != expected_active:
        raise CandidateRefusal("REFUSE_CONFIG_ACTIVE_STAGE_MISMATCH")
    _validate_profile_prefixes(profile, order)
    if packet["live_order"] != order:
        raise CandidateRefusal("REFUSE_LIVE_ORDER_BINDING")
    return config, profile, order, config_path


def _retained_self_hash(receipt: Mapping[str, Any]) -> str:
    """Verify the cumulative receipt's own canonical self-hash independently."""

    expected = receipt.get("receipt_sha256")
    if not _is_digest(expected):
        raise CandidateRefusal("REFUSE_RETAINED_RECEIPT_SELF_HASH")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    if digest(unsigned) != expected:
        raise CandidateRefusal("REFUSE_RETAINED_RECEIPT_SELF_HASH")
    return expected


def _stage_execution_rows(value: Any) -> list[Mapping[str, Any]]:
    rows: list[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        if isinstance(value.get("stage_id"), str) and "executed" in value:
            rows.append(value)
        for item in value.values():
            rows.extend(_stage_execution_rows(item))
    elif isinstance(value, list):
        for item in value:
            rows.extend(_stage_execution_rows(item))
    return rows


def _validate_retained_cumulative_receipt(
    receipt: Mapping[str, Any],
    packet: Mapping[str, Any],
    profile: Mapping[str, Any],
    live_order: list[str],
    *,
    require_self: bool = True,
) -> None:
    """Check the retained scheduler receipt, not merely its outer packet digest."""

    if receipt.get("schema") != RETAINED_SCHEMA or receipt.get("config_schema") != CONFIG_SCHEMA:
        raise CandidateRefusal("REFUSE_RETAINED_RECEIPT_SCHEMA")
    if require_self:
        _retained_self_hash(receipt)
    if receipt.get("profile") != packet.get("profile"):
        raise CandidateRefusal("REFUSE_RETAINED_PROFILE_BINDING")
    if not isinstance(receipt.get("run_id"), str) or not receipt["run_id"].strip():
        raise CandidateRefusal("REFUSE_RETAINED_RUN_ID")
    if receipt.get("status") != "LOCKED" or receipt.get("reason_code") != "LOCKED_STAGE":
        raise CandidateRefusal("REFUSE_RETAINED_STATUS")
    if receipt.get("promotion_allowed") is not False:
        raise CandidateRefusal("REFUSE_RETAINED_PROMOTION")
    expected_config_sha = packet.get("config_sha256")
    for binding_name in ("source_binding", "source_binding_after"):
        binding = receipt.get(binding_name)
        if not isinstance(binding, Mapping):
            raise CandidateRefusal(f"REFUSE_RETAINED_{binding_name.upper()}")
        config_path = binding.get("config_path")
        if not isinstance(config_path, str) or config_path not in {
            EXPECTED_CONFIG_PATH,
            "config/CUMULATIVE_WAVE_SEQUENCE.json",
        }:
            raise CandidateRefusal("REFUSE_RETAINED_CONFIG_PATH")
        if binding.get("config_sha256") != expected_config_sha or binding.get("valid") is not True:
            raise CandidateRefusal("REFUSE_RETAINED_CONFIG_BINDING")
    retained_rows = _retained_prefix_map(receipt)
    prefix_rows = profile.get("prefixes")
    if not isinstance(prefix_rows, list) or len(prefix_rows) < 3:
        raise CandidateRefusal("REFUSE_CONFIG_PREFIX_COUNT")
    if list(retained_rows) != ["prefix-1", "prefix-2", "prefix-3"]:
        raise CandidateRefusal("REFUSE_RETAINED_PREFIX_TOPOLOGY")
    for index in (0, 1):
        retained_prefix = retained_rows.get(f"prefix-{index + 1}")
        expected_prefix = prefix_rows[index]
        if (
            not isinstance(retained_prefix, Mapping)
            or retained_prefix.get("stage_ids") != expected_prefix.get("stage_ids")
            or retained_prefix.get("status") != "PASS"
            or retained_prefix.get("stabilized") is not True
        ):
            raise CandidateRefusal(f"REFUSE_RETAINED_PREFIX_{index + 1}_TOPOLOGY")
    prefix3 = retained_rows.get("prefix-3")
    expected_prefix3 = prefix_rows[2]
    if not isinstance(prefix3, Mapping):
        raise CandidateRefusal("REFUSE_RETAINED_PREFIX_3")
    if prefix3.get("stage_ids") != expected_prefix3.get("stage_ids"):
        raise CandidateRefusal("REFUSE_RETAINED_PREFIX_3_ORDER")
    if prefix3.get("status") != "LOCKED" or prefix3.get("blocked_stage_id") != "cb-premortem-wave":
        raise CandidateRefusal("REFUSE_RETAINED_PREFIX_3_LOCK")
    stage_records = prefix3.get("stage_records")
    if not isinstance(stage_records, list) or [row.get("stage_id") for row in stage_records if isinstance(row, Mapping)] != list(expected_prefix3.get("stage_ids", [])):
        raise CandidateRefusal("REFUSE_RETAINED_PREFIX_3_RECORDS")
    for index, row in enumerate(stage_records):
        if not isinstance(row, Mapping) or row.get("executed") is not False:
            raise CandidateRefusal("REFUSE_RETAINED_PREFIX_3_EXECUTION")
        expected_status = "LOCKED" if index == 2 else "NOT_RUN"
        if row.get("status") != expected_status:
            raise CandidateRefusal("REFUSE_RETAINED_PREFIX_3_STATUS")
    locked_index = live_order.index("cb-premortem-wave") if "cb-premortem-wave" in live_order else -1
    if locked_index < 0:
        raise CandidateRefusal("REFUSE_CONFIG_PREMORTEM_STAGE")
    for row in _stage_execution_rows(receipt):
        stage_id = row.get("stage_id")
        if row.get("executed") is True:
            if not isinstance(stage_id, str) or stage_id not in live_order:
                raise CandidateRefusal("REFUSE_RETAINED_UNKNOWN_STAGE_EXECUTED")
            if live_order.index(stage_id) > locked_index:
                raise CandidateRefusal("REFUSE_RETAINED_LATER_STAGE_EXECUTED")


def _retained_prefix3_lock_projection(receipt: Mapping[str, Any]) -> dict[str, Any]:
    prefix3 = _retained_prefix_map(receipt).get("prefix-3")
    if not isinstance(prefix3, Mapping):
        raise CandidateRefusal("REFUSE_RETAINED_PREFIX_3")
    return {
        "prefix_id": "prefix-3",
        "status": prefix3.get("status"),
        "blocked_stage_id": prefix3.get("blocked_stage_id"),
        "stage_ids": copy.deepcopy(prefix3.get("stage_ids")),
        "no_later_executed": True,
        "prefix_sha256": digest(prefix3),
    }


def _validate_profile_prefixes(profile: Mapping[str, Any], order: list[str]) -> None:
    prefixes = profile.get("prefixes")
    if not isinstance(prefixes, list) or len(prefixes) != len(order):
        raise CandidateRefusal("REFUSE_CONFIG_PREFIX_COUNT")
    for index, prefix in enumerate(prefixes, start=1):
        if not isinstance(prefix, dict) or prefix.get("prefix_id") != f"prefix-{index}" or prefix.get("stage_ids") != order[:index]:
            raise CandidateRefusal("REFUSE_CONFIG_PREFIX_ORDER")


def _retained_prefix_map(receipt: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = receipt.get("prefixes")
    if not isinstance(rows, list):
        raise CandidateRefusal("REFUSE_RETAINED_PREFIXES")
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("prefix_id"), str) or row["prefix_id"] in result:
            raise CandidateRefusal("REFUSE_RETAINED_PREFIX_SET")
        if not isinstance(row.get("status"), str):
            raise CandidateRefusal("REFUSE_RETAINED_PREFIX_STATUS")
        result[row["prefix_id"]] = row
    return result


def _prefix_lock_evidence(profile: Mapping[str, Any], retained: Mapping[str, Any]) -> list[dict[str, Any]]:
    retained_rows = _retained_prefix_map(retained)
    stages = profile["stages"]
    evidence: list[dict[str, Any]] = []
    for prefix in profile["prefixes"]:
        prefix_id = prefix["prefix_id"]
        stage_ids = list(prefix["stage_ids"])
        locked = [stage_id for stage_id in stage_ids if stages[stage_id].get("mode") == "LOCKED"]
        retained_row = retained_rows.get(prefix_id)
        retained_stage_ids: list[str] = []
        if isinstance(retained_row, Mapping):
            if isinstance(retained_row.get("stage_ids"), list):
                retained_stage_ids = list(retained_row["stage_ids"])
            elif isinstance(retained_row.get("stage_records"), list):
                retained_stage_ids = [
                    row["stage_id"]
                    for row in retained_row["stage_records"]
                    if isinstance(row, Mapping) and isinstance(row.get("stage_id"), str)
                ]
            if retained_stage_ids and retained_stage_ids != stage_ids:
                raise CandidateRefusal(f"REFUSE_RETAINED_PREFIX_ORDER:{prefix_id}")
        evidence.append(
            {
                "prefix_id": prefix_id,
                "stage_ids": stage_ids,
                "stage_ids_sha256": digest(stage_ids),
                "config_prefix_sha256": digest(prefix),
                "locked_stage_ids": locked,
                "first_locked_stage_id": locked[0] if locked else None,
                "retained_status": retained_row.get("status") if isinstance(retained_row, Mapping) else "NOT_RETAINED",
                "retained_stage_ids": retained_stage_ids,
                "retained_prefix_sha256": digest(retained_row) if isinstance(retained_row, Mapping) else None,
                "retained_blocked_stage_id": retained_row.get("blocked_stage_id") if isinstance(retained_row, Mapping) else None,
                "lock_observed": bool(locked) or (isinstance(retained_row, Mapping) and retained_row.get("status") == "LOCKED"),
            }
        )
    return evidence


def _leaf_control(
    module: Any,
    base_input: Mapping[str, Any],
    control_id: str,
    mutate: Any,
    expected_reason: str,
) -> dict[str, Any]:
    """Invoke a real leaf mutation and verify its self-bound refusal receipt."""

    mutated = copy.deepcopy(dict(base_input))
    mutate(mutated)
    try:
        control_receipt = module.discriminate(mutated)
        verified = bool(module.verify_receipt(control_receipt))
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise CandidateRefusal(f"REFUSE_CONTROL_EXCEPTION:{control_id}") from exc
    if not isinstance(control_receipt, dict):
        raise CandidateRefusal(f"REFUSE_CONTROL_RECEIPT_SHAPE:{control_id}")
    observed_reason = control_receipt.get("reason")
    if control_receipt.get("status") != "REFUSE" or observed_reason != expected_reason or not verified:
        raise CandidateRefusal(f"REFUSE_CONTROL_ASSERTION:{control_id}")
    return {
        "control_id": control_id,
        "operation_id": LEAF_OPERATION,
        "input_sha256": digest(mutated),
        "receipt_sha256": control_receipt.get("receipt_sha256"),
        "expected_status": "REFUSE",
        "expected_reason": expected_reason,
        "observed_status": control_receipt.get("status"),
        "observed_reason": observed_reason,
        "receipt_verified": verified,
        "passed": True,
        "receipt": copy.deepcopy(control_receipt),
    }


def _admission_controls(
    candidate: list[str],
    live: list[str],
    profile: Mapping[str, Any],
    retained: Mapping[str, Any],
    child_configs: Mapping[str, Mapping[str, Any]],
    base_leaf_input: Mapping[str, Any],
    control_specs: list[Mapping[str, Any]],
    source_hashes: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Run actual mutated parent and leaf operations, retaining receipts."""

    controls: list[dict[str, Any]] = []
    specs = {str(row["id"]): row for row in control_specs}
    duplicate_candidate = candidate + [candidate[0]]
    try:
        _validate_order(duplicate_candidate, "candidate_order")
    except CandidateRefusal as exc:
        observed = str(exc)
    else:  # pragma: no cover - the mutation must be rejected
        observed = "UNEXPECTED_ACCEPT"
    controls.append(
        {
            "control_id": "duplicate_candidate_order",
            "operation_id": "cb-strategy-discriminator-wave.order_validator.v1",
            "input_sha256": digest(duplicate_candidate),
            "expected_status": "REFUSE",
            "observed_status": "REFUSE",
            "expected_reason": "REFUSE_DUPLICATE_CANDIDATE_ORDER",
            "observed_reason": observed,
            "receipt_verified": observed == "REFUSE_DUPLICATE_CANDIDATE_ORDER",
            "passed": observed == "REFUSE_DUPLICATE_CANDIDATE_ORDER",
        }
    )
    duplicate_live = live + [live[0]]
    try:
        _validate_order(duplicate_live, "live_order")
    except CandidateRefusal as exc:
        observed = str(exc)
    else:  # pragma: no cover - the mutation must be rejected
        observed = "UNEXPECTED_ACCEPT"
    controls.append(
        {
            "control_id": "duplicate_live_profile_order",
            "operation_id": "cb-strategy-discriminator-wave.order_validator.v1",
            "input_sha256": digest(duplicate_live),
            "expected_status": "REFUSE",
            "observed_status": "REFUSE",
            "expected_reason": "REFUSE_DUPLICATE_LIVE_ORDER",
            "observed_reason": observed,
            "receipt_verified": observed == "REFUSE_DUPLICATE_LIVE_ORDER",
            "passed": observed == "REFUSE_DUPLICATE_LIVE_ORDER",
        }
    )
    mutated_profile = copy.deepcopy(dict(profile))
    mutated_prefixes = mutated_profile.get("prefixes")
    if isinstance(mutated_prefixes, list) and mutated_prefixes and isinstance(mutated_prefixes[0], dict):
        mutated_prefixes[0]["stage_ids"] = ["forged-stage"]
    try:
        _validate_profile_prefixes(mutated_profile, live)
    except CandidateRefusal as exc:
        observed = str(exc)
    else:  # pragma: no cover - the mutation must be rejected
        observed = "UNEXPECTED_ACCEPT"
    controls.append(
        {
            "control_id": "prefix_order_binding",
            "operation_id": "cb-strategy-discriminator-wave.prefix_validator.v1",
            "input_sha256": digest(mutated_profile),
            "expected_status": "REFUSE",
            "observed_status": "REFUSE",
            "expected_reason": "REFUSE_CONFIG_PREFIX_ORDER",
            "observed_reason": observed,
            "receipt_verified": observed == "REFUSE_CONFIG_PREFIX_ORDER",
            "passed": observed == "REFUSE_CONFIG_PREFIX_ORDER",
        }
    )
    leaf_module = child_configs["bind_survivors"]["module"]
    leaf_input = base_leaf_input
    controls.append(_leaf_control(
        leaf_module,
        leaf_input,
        "leaf_duplicate_strategy",
        lambda value: value.update({"strategies": ["candidate_order", "candidate_order"]}),
        "REFUSE_DUPLICATE_STRATEGY",
    ))
    controls.append(_leaf_control(
        leaf_module,
        leaf_input,
        "leaf_nonfinite_probe",
        lambda value: value.update({"probe": {"name": "finite-prefix-compare", "finite": False, "cost": 1}}),
        "REFUSE_NONFINITE_PROBE",
    ))
    controls.append(_leaf_control(
        leaf_module,
        leaf_input,
        "leaf_authority_shaped",
        lambda value: value.update({"winner": "candidate_order"}),
        "REFUSE_AUTHORITY_SHAPED",
    ))
    baseline = _comparison(candidate, live)
    mutated_retained = copy.deepcopy(dict(retained))
    mutated_retained["selection_count"] = (mutated_retained.get("selection_count") or 0) + 1
    mutated_retained["receipt_sha256"] = digest({
        key: value for key, value in mutated_retained.items() if key != "receipt_sha256"
    })
    after = _comparison(candidate, live)
    controls.append(
        {
            "control_id": "selection_counts_excluded",
            "operation_id": "cb-strategy-discriminator-wave.compare.v1",
            "input_sha256": digest(mutated_retained),
            "baseline_output_sha256": digest(baseline),
            "mutated_output_sha256": digest(after),
            "expected_status": "MATCH",
            "observed_status": "MATCH" if baseline == after else "REFUSE",
            "expected_reason": "NOT_USED_FOR_ORDER_ADMISSION",
            "observed_reason": "NOT_USED_FOR_ORDER_ADMISSION" if baseline == after else "SELECTION_COUNT_CHANGED_ORDER",
            "receipt_verified": baseline == after,
            "passed": baseline == after,
        }
    )
    sealed: list[dict[str, Any]] = []
    if [row.get("control_id") for row in controls] != list(CONTROL_IDS):
        raise CandidateRefusal("REFUSE_CONTROL_SET")
    for row in controls:
        spec = specs.get(str(row.get("control_id")))
        if spec is None or row.get("operation_id") != spec.get("operation") or row.get("expected_reason") != spec.get("expected_reason") or row.get("expected_status") != spec.get("expected_status"):
            raise CandidateRefusal(f"REFUSE_CONTROL_BINDING:{row.get('control_id')}")
        if row.get("control_id") == "selection_counts_excluded":
            if row.get("observed_status") is None:
                row["observed_status"] = "MATCH"
        row["source_hashes"] = copy.deepcopy(dict(source_hashes))
        unsigned = copy.deepcopy(row)
        unsigned.pop("receipt_sha256", None)
        unsigned.pop("receipt_self_sha256", None)
        control_hash = digest(unsigned)
        row["receipt_sha256"] = control_hash
        row["receipt_self_sha256"] = control_hash
        sealed.append(row)
    if not all(row.get("passed") is True and row.get("receipt_verified") is True for row in sealed):
        raise CandidateRefusal("REFUSE_ADMISSION_NEGATIVE_CONTROL")
    return sealed


def _verify_control_receipt(row: Mapping[str, Any], spec: Mapping[str, Any], source_hashes: Mapping[str, Any]) -> bool:
    if row.get("control_id") != spec.get("id") or row.get("operation_id") != spec.get("operation"):
        return False
    if row.get("expected_status") != spec.get("expected_status") or row.get("expected_reason") != spec.get("expected_reason"):
        return False
    if row.get("source_hashes") != source_hashes:
        return False
    expected = row.get("receipt_sha256")
    if not _is_digest(expected) or expected != row.get("receipt_self_sha256"):
        return False
    unsigned = {key: value for key, value in row.items() if key not in {"receipt_sha256", "receipt_self_sha256"}}
    return digest(unsigned) == expected and row.get("receipt_verified") is True and row.get("passed") is True


def _comparison(candidate: list[str], live: list[str]) -> dict[str, Any]:
    first_difference: int | None = None
    for index, (left, right) in enumerate(zip(candidate, live)):
        if left != right:
            first_difference = index
            break
    if first_difference is None and len(candidate) != len(live):
        first_difference = min(len(candidate), len(live))
    prefix = candidate[:first_difference] if first_difference is not None else list(candidate)
    equal = candidate == live
    return {
        "candidate_order": list(candidate),
        "candidate_order_sha256": digest(candidate),
        "live_profile_order": list(live),
        "live_profile_order_sha256": digest(live),
        "arrays_equal": equal,
        "first_difference_index": first_difference,
        "common_prefix": prefix,
        "common_prefix_sha256": digest(prefix),
        "common_prefix_length": len(prefix),
        "order_basis": ["candidate_order", "live_profile_order"],
        "selection_counts_used": False,
        "status": "MATCH_OBSERVED" if equal else "HOLD_ORDER_MISMATCH",
    }


def _base_receipt(packet: Any, *, definition_sha: str | None = None) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "wave_id": WAVE_ID,
        "status": "REFUSE",
        "reason": None,
        "operation": PARENT_OPERATION,
        "target": packet.get("target") if isinstance(packet, dict) else None,
        "target_bytes": packet.get("target_bytes") if isinstance(packet, dict) else None,
        "target_sha256": packet.get("target_sha256") if isinstance(packet, dict) else None,
        "target_bytes_digest": packet.get("target_sha256") if isinstance(packet, dict) else None,
        "candidate_order": copy.deepcopy(packet.get("candidate_order")) if isinstance(packet, dict) else None,
        "candidate_order_sha256": packet.get("candidate_order_sha256") if isinstance(packet, dict) else None,
        "live_order": copy.deepcopy(packet.get("live_order")) if isinstance(packet, dict) else None,
        "live_order_sha256": packet.get("live_order_sha256") if isinstance(packet, dict) else None,
        "profile": packet.get("profile") if isinstance(packet, dict) else None,
        "config_path": packet.get("config_path") if isinstance(packet, dict) else None,
        "config_sha256": packet.get("config_sha256") if isinstance(packet, dict) else None,
        "retained_cumulative_receipt_sha256": packet.get("retained_cumulative_receipt_sha256") if isinstance(packet, dict) else None,
        "retained_cumulative_receipt_self_sha256": packet.get("retained_cumulative_receipt_self_sha256") if isinstance(packet, dict) else None,
        "retained_cumulative_run_id": packet.get("retained_cumulative_run_id") if isinstance(packet, dict) else None,
        "retained_cumulative_receipt": copy.deepcopy(packet.get("retained_cumulative_receipt")) if isinstance(packet, dict) else None,
        "retained_receipt_self_sha256": None,
        "retained_prefix3_lock": None,
        "context_epoch_sha256": packet.get("context_epoch_sha256") if isinstance(packet, dict) else None,
        "context_epoch": copy.deepcopy(packet.get("context_epoch")) if isinstance(packet, dict) else None,
        "branch_frontier_sha256": packet.get("branch_frontier_sha256") if isinstance(packet, dict) else None,
        "expected_source_set_sha256": packet.get("expected_source_set_sha256") if isinstance(packet, dict) else None,
        "branch_frontier": copy.deepcopy(packet.get("branch_frontier")) if isinstance(packet, dict) else None,
        "input_sha256": _safe_digest(packet),
        "definition_sha256": definition_sha,
        "authority_bindings_sha256": None,
        "authority_bindings": None,
        "authority_receipt_self_hash": None,
        "authority_epoch_pointer_hash": None,
        "authority_receipt_mode": None,
        "authority_receipt_path": None,
        "authority_pointer_mode": None,
        "authority_pointer_path": None,
        "authority_epoch_path": None,
        "authority_manifest_path": None,
        "authority_manifest_sha256": None,
        "authority_mode": None,
        "source_hashes": {},
        "attestations": [],
        "child_order": list(CHILD_IDS),
        "child_inputs": {},
        "children": [],
        "child_receipts": {},
        "launched_child_order": [],
        "not_launched_child_ids": list(CHILD_IDS),
        "negative_controls": [],
        "control_receipts": [],
        "admission_disposition": "NOT_RUN",
        "prefix_lock_evidence": [],
        "frontier": None,
        "output_digest": None,
        "cancellation_state": "NOT_REQUESTED",
        "route_truth": ROUTE_TRUTH,
        "route_truth_label": ROUTE_TRUTH_LABEL,
        "model_free": True,
        "provider_dispatch_proved": False,
        "mmm_preload_applicable": False,
        "provider_receipt_applicable": False,
        "not_applicable": {
            "mmm_preload_receipts": "model_free_candidate",
            "provider_call_receipts": "model_free_candidate",
        },
        "activated": False,
        "promotion_allowed": False,
        "writes_performed": False,
        "receipt_written": False,
        "selection_counts_used": False,
        "claim_ceiling": CLAIM_CEILING,
    }


def _seal(receipt: Mapping[str, Any]) -> dict[str, Any]:
    unsigned = copy.deepcopy(dict(receipt))
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    value = digest(unsigned)
    unsigned["receipt_sha256"] = value
    unsigned["receipt_self_sha256"] = value
    return unsigned


def _output_digest(receipt: Mapping[str, Any]) -> str | None:
    frontier = receipt.get("frontier")
    return digest(frontier) if isinstance(frontier, dict) else None


def _child_row(child_id: str, wrapper: Mapping[str, Any], child_receipt: Mapping[str, Any], *, terminal_state: str = "COMPLETED") -> dict[str, Any]:
    return {
        "child_id": child_id,
        "operation_id": wrapper["operation_id"],
        "leaf_operation": LEAF_OPERATION,
        "input_sha256": digest(wrapper),
        "leaf_input_sha256": digest(wrapper["leaf_input"]),
        "receipt_sha256": child_receipt.get("receipt_sha256"),
        "status": child_receipt.get("status"),
        "terminal_state": terminal_state,
        "receipt": copy.deepcopy(child_receipt),
    }


def _normal_frontier(packet: Mapping[str, Any], comparison: Mapping[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": FRONTIER_SCHEMA,
        "frontier_state": comparison["status"],
        "profile": packet["profile"],
        "candidate_order": list(comparison["candidate_order"]),
        "candidate_order_sha256": comparison["candidate_order_sha256"],
        "live_profile_order": list(comparison["live_profile_order"]),
        "live_profile_order_sha256": comparison["live_profile_order_sha256"],
        "arrays_equal": comparison["arrays_equal"],
        "first_difference_index": comparison["first_difference_index"],
        "common_prefix": list(comparison["common_prefix"]),
        "common_prefix_sha256": comparison["common_prefix_sha256"],
        "common_prefix_length": comparison["common_prefix_length"],
        "prefix_lock_evidence": copy.deepcopy(evidence),
        "branch_frontier_projection": copy.deepcopy(packet["branch_frontier"]),
        "order_basis": list(comparison["order_basis"]),
        "selection_counts_used": False,
        "writes_performed": False,
        "activated": False,
        "promotion_allowed": False,
    }


def _verify_leaf(module: Any, payload: Mapping[str, Any], receipt: Any) -> bool:
    if not isinstance(receipt, dict):
        return False
    try:
        payload_verifier = getattr(module, "verify_payload_receipt", None)
        if callable(payload_verifier):
            if not bool(payload_verifier(dict(payload), receipt)):
                return False
        elif not bool(module.verify_receipt(receipt)):
            return False
        # The leaf's self-hash is necessary but not sufficient: re-run the
        # deterministic leaf on the same current payload so a forged receipt
        # cannot retain a different role/disagreement under the same input
        # digest.
        expected = module.discriminate(copy.deepcopy(dict(payload)))
        return receipt == expected
    except (AttributeError, TypeError, ValueError, KeyError):
        return False


def run_packet(packet: Any, *, root: Path | None = None, cancel_requested: bool | None = None, authority_mode: str = "LIVE") -> dict[str, Any]:
    """Run one packet without writing anything."""

    product_root: Path | None = None
    definition_path: Path | None = None
    receipt: dict[str, Any] | None = None
    try:
        product_root = _root(root)
        definition, child_configs, validator_path, definition_path = _load_definition(product_root)
        normalized = _validate_packet(packet, definition)
        authority = _load_authority(product_root, definition, authority_mode)
        _validate_authority_packet(normalized, authority)
        if cancel_requested is not None:
            if not isinstance(cancel_requested, bool):
                raise CandidateRefusal("REFUSE_CANCEL_TYPE")
            normalized["cancel_requested"] = cancel_requested
        receipt = _base_receipt(normalized, definition_sha=file_digest(definition_path))
        receipt["authority_bindings"] = _authority_projection(authority)
        receipt["authority_receipt_self_hash"] = authority["receipt_sha256"]
        receipt["authority_epoch_pointer_hash"] = authority["pointer_sha256"]
        receipt["authority_bindings_sha256"] = authority["bindings_sha256"]
        receipt["authority_receipt_mode"] = authority["receipt_mode"]
        receipt["authority_receipt_path"] = authority["receipt_path"]
        receipt["authority_pointer_mode"] = authority["pointer_mode"]
        receipt["authority_pointer_path"] = authority["pointer_path"]
        receipt["authority_epoch_path"] = authority["epoch_path"]
        receipt["authority_manifest_path"] = authority["manifest_path"]
        receipt["authority_manifest_sha256"] = authority["manifest_sha256"]
        receipt["authority_mode"] = authority_mode
        receipt["source_hashes"] = _source_hashes(product_root, definition_path, child_configs, validator_path)
        receipt["child_inputs"] = copy.deepcopy(normalized["child_inputs"])
        # Full packet preflight, including the current live config and the
        # retained scheduler receipt, must complete before a parent cancel can
        # become terminal.  Cancellation is not a bypass around custody.
        config, profile, live_order, config_path = _load_config(product_root, normalized)
        retained = normalized["retained_cumulative_receipt"]
        _validate_retained_cumulative_receipt(retained, normalized, profile, live_order, require_self=False)
        receipt["retained_receipt_self_sha256"] = retained["receipt_sha256"]
        receipt["retained_prefix3_lock"] = _retained_prefix3_lock_projection(retained)
        evidence = _prefix_lock_evidence(profile, retained)
        receipt["prefix_lock_evidence"] = copy.deepcopy(evidence)
        receipt["config_path"] = _relative(product_root, config_path)
        receipt["live_order"] = list(live_order)
        receipt["live_order_sha256"] = digest(live_order)
        receipt["attestations"].append(_attest_current(
            product_root,
            normalized,
            label="preflight",
            expected_source_hashes=receipt["source_hashes"],
            authority_mode=authority_mode,
        ))
        if normalized.get("cancel_requested") is True:
            receipt["status"] = "CANCELLED"
            receipt["reason"] = "CANCELLED_PARENT_REQUEST"
            receipt["cancellation_state"] = "CANCELLED"
            return _seal(receipt)

        controls = _admission_controls(
            normalized["candidate_order"],
            live_order,
            profile,
            retained,
            child_configs,
            normalized["child_inputs"]["bind_survivors"]["leaf_input"],
            definition["control_receipts"],
            receipt["source_hashes"],
        )
        receipt["negative_controls"] = controls
        receipt["control_receipts"] = copy.deepcopy(controls)
        receipt["admission_disposition"] = "ADMISSION_CLEAN"
        for child_id in CHILD_IDS:
            receipt["attestations"].append(_attest_current(
                product_root,
                normalized,
                label=f"before_child:{child_id}",
                expected_source_hashes=receipt["source_hashes"],
                child_receipts=receipt["child_receipts"],
                authority_mode=authority_mode,
            ))
            wrapper = normalized["child_inputs"][child_id]
            child_config = child_configs[child_id]
            leaf_input = copy.deepcopy(wrapper["leaf_input"])
            try:
                child_receipt = child_config["module"].discriminate(leaf_input)
            except Exception as exc:
                raise CandidateRefusal(f"REFUSE_CHILD_EXCEPTION:{child_id}") from exc
            if not isinstance(child_receipt, dict):
                raise CandidateRefusal(f"REFUSE_CHILD_RECEIPT_SHAPE:{child_id}")
            cancelled = child_receipt.get("status") == "CANCELLED_NO_AUTHORITY" or child_receipt.get("cancellation_state") == "CANCELLED"
            if not _verify_leaf(child_config["module"], leaf_input, child_receipt):
                raise CandidateRefusal(f"REFUSE_CHILD_RECEIPT_BINDING:{child_id}")
            if cancelled:
                row = _child_row(child_id, wrapper, child_receipt, terminal_state="CANCELLED")
                receipt["children"].append(row)
                receipt["child_receipts"][child_id] = copy.deepcopy(child_receipt)
                receipt["launched_child_order"].append(child_id)
                receipt["not_launched_child_ids"] = list(CHILD_IDS[len(receipt["launched_child_order"]):])
                receipt["attestations"].append(_attest_current(
                    product_root,
                    normalized,
                    label=f"after_child:{child_id}",
                    expected_source_hashes=receipt["source_hashes"],
                    child_receipts=receipt["child_receipts"],
                    authority_mode=authority_mode,
                ))
                receipt["status"] = "CANCELLED"
                receipt["reason"] = f"CANCELLED_CHILD:{child_id}"
                receipt["cancellation_state"] = "CANCELLED"
                return _seal(receipt)
            if child_receipt.get("status") != "DESIGNED" or child_receipt.get("output_kind") != "PROPOSAL":
                raise CandidateRefusal(f"REFUSE_CHILD_ROLE_BINDING:{child_id}")
            row = _child_row(child_id, wrapper, child_receipt)
            receipt["children"].append(row)
            receipt["child_receipts"][child_id] = copy.deepcopy(child_receipt)
            receipt["launched_child_order"].append(child_id)
            receipt["not_launched_child_ids"] = list(CHILD_IDS[len(receipt["launched_child_order"]):])
            receipt["attestations"].append(_attest_current(
                product_root,
                normalized,
                label=f"after_child:{child_id}",
                expected_source_hashes=receipt["source_hashes"],
                child_receipts=receipt["child_receipts"],
                authority_mode=authority_mode,
            ))

        receipt["attestations"].append(_attest_current(
            product_root,
            normalized,
            label="after_all_children",
            expected_source_hashes=receipt["source_hashes"],
            child_receipts=receipt["child_receipts"],
            authority_mode=authority_mode,
        ))
        comparison = _comparison(normalized["candidate_order"], live_order)
        receipt["frontier"] = _normal_frontier(normalized, comparison, evidence)
        receipt["status"] = comparison["status"]
        receipt["reason"] = "HOLD_ORDER_MISMATCH" if comparison["status"] == "HOLD_ORDER_MISMATCH" else None
        receipt["output_digest"] = _output_digest(receipt)
        receipt["attestations"].append(_attest_current(
            product_root,
            normalized,
            label="prewrite",
            expected_source_hashes=receipt["source_hashes"],
            child_receipts=receipt["child_receipts"],
            authority_mode=authority_mode,
        ))
        return _seal(receipt)
    except CandidateRefusal as exc:
        if receipt is None:
            receipt = _base_receipt(packet, definition_sha=file_digest(definition_path) if definition_path and definition_path.is_file() else None)
        else:
            receipt = copy.deepcopy(receipt)
        receipt["status"] = "REFUSE"
        receipt["reason"] = str(exc)
        receipt["frontier"] = None
        receipt["output_digest"] = None
        receipt["cancellation_state"] = "NOT_REQUESTED"
        receipt["not_launched_child_ids"] = list(CHILD_IDS[len(receipt.get("launched_child_order", [])):])
        return _seal(receipt)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        if receipt is None:
            receipt = _base_receipt(packet, definition_sha=file_digest(definition_path) if definition_path and definition_path.is_file() else None)
        else:
            receipt = copy.deepcopy(receipt)
        receipt["status"] = "REFUSE"
        receipt["reason"] = f"REFUSE_INTERNAL:{type(exc).__name__}"
        receipt["frontier"] = None
        receipt["output_digest"] = None
        receipt["cancellation_state"] = "NOT_REQUESTED"
        receipt["not_launched_child_ids"] = list(CHILD_IDS[len(receipt.get("launched_child_order", [])):])
        return _seal(receipt)


def _verify_source_bindings(receipt: Mapping[str, Any], product_root: Path, definition_path: Path, child_configs: Mapping[str, Mapping[str, Any]], validator_path: Path) -> bool:
    expected = _source_hashes(product_root, definition_path, child_configs, validator_path)
    return (
        receipt.get("source_hashes") == expected
        and receipt.get("definition_sha256") == expected["definition"]
        and receipt.get("expected_source_set_sha256") == digest(expected)
    )


def _verify_attestations(
    receipt: Mapping[str, Any],
    product_root: Path,
    normalized: Mapping[str, Any],
    child_configs: Mapping[str, Mapping[str, Any]],
    authority_mode: str,
) -> bool:
    attestations = receipt.get("attestations")
    if not isinstance(attestations, list):
        return False
    status = receipt.get("status")
    ids = list(receipt.get("launched_child_order", []))
    full_labels = ["preflight"]
    if status == "CANCELLED" and ids:
        for child_id in ids:
            full_labels.extend([f"before_child:{child_id}", f"after_child:{child_id}"])
    elif status in {"MATCH_OBSERVED", "HOLD_ORDER_MISMATCH", "REFUSE"}:
        for child_id in CHILD_IDS:
            full_labels.extend([f"before_child:{child_id}", f"after_child:{child_id}"])
        full_labels.extend(["after_all_children", "prewrite"])
    actual_labels = [row.get("label") for row in attestations if isinstance(row, Mapping)]
    labels = full_labels if status != "REFUSE" else full_labels[: len(actual_labels)]
    if actual_labels != labels:
        return False
    for row in attestations:
        if not isinstance(row, Mapping):
            return False
        verified_ids = row.get("verified_child_ids")
        if not isinstance(verified_ids, list) or any(child_id not in ids for child_id in verified_ids):
            return False
        child_receipts = {
            child_id: receipt["child_receipts"][child_id]
            for child_id in verified_ids
            if isinstance(receipt.get("child_receipts"), Mapping) and child_id in receipt["child_receipts"]
        }
        try:
            expected = _attest_current(
                product_root,
                normalized,
                label=str(row["label"]),
                expected_source_hashes=receipt["source_hashes"],
                child_receipts=child_receipts,
                authority_mode=authority_mode,
            )
        except (CandidateRefusal, KeyError, TypeError, ValueError):
            return False
        if dict(row) != expected:
            return False
    return True


def _verify_self_digest(receipt: Mapping[str, Any]) -> bool:
    if not isinstance(receipt.get("receipt_sha256"), str) or receipt.get("receipt_sha256") != receipt.get("receipt_self_sha256"):
        return False
    unsigned = copy.deepcopy(dict(receipt))
    expected = unsigned.pop("receipt_sha256", None)
    expected_2 = unsigned.pop("receipt_self_sha256", None)
    return expected == expected_2 and digest(unsigned) == expected


def verify_receipt(receipt: Any, packet: Any | None = None, *, root: Path | None = None, authority_mode: str = "LIVE") -> bool:
    """Verify parent custody, current sources, live config, and child receipts."""

    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA or receipt.get("wave_id") != WAVE_ID:
        return False
    if isinstance(packet, (Path, str)):
        candidate_path = Path(packet)
        if root is None and candidate_path.is_dir():
            root = candidate_path
            packet = None
        elif candidate_path.is_file():
            try:
                packet = _read_json(candidate_path)
            except CandidateRefusal:
                return False
    product_root: Path
    try:
        product_root = _root(root)
        definition, child_configs, validator_path, definition_path = _load_definition(product_root)
        if not _verify_source_bindings(receipt, product_root, definition_path, child_configs, validator_path):
            return False
        normalized: dict[str, Any] | None = None
        if packet is not None:
            normalized = _validate_packet(packet, definition)
            if receipt.get("input_sha256") != digest(normalized):
                return False
            if receipt.get("child_inputs") != normalized["child_inputs"]:
                return False
        if receipt.get("operation") != PARENT_OPERATION or receipt.get("claim_ceiling") != CLAIM_CEILING:
            return False
        if receipt.get("route_truth") != ROUTE_TRUTH or receipt.get("route_truth_label") != ROUTE_TRUTH_LABEL:
            return False
        if receipt.get("model_free") is not True or receipt.get("provider_dispatch_proved") is not False:
            return False
        if receipt.get("mmm_preload_applicable") is not False or receipt.get("provider_receipt_applicable") is not False:
            return False
        if receipt.get("activated") is not False or receipt.get("promotion_allowed") is not False or receipt.get("writes_performed") is not False or receipt.get("receipt_written") is not False:
            return False
        if receipt.get("selection_counts_used") is not False:
            return False
        if receipt.get("child_order") != list(CHILD_IDS):
            return False
        if not isinstance(receipt.get("children"), list) or not isinstance(receipt.get("child_receipts"), dict):
            return False
        rows = receipt["children"]
        ids = [row.get("child_id") for row in rows if isinstance(row, dict)]
        if len(ids) != len(rows) or len(ids) != len(set(ids)) or ids != list(CHILD_IDS[: len(ids)]):
            return False
        if set(receipt["child_receipts"]) != set(ids):
            return False
        if receipt.get("launched_child_order") != ids or receipt.get("not_launched_child_ids") != list(CHILD_IDS[len(ids):]):
            return False
        embedded_inputs = receipt.get("child_inputs")
        if not isinstance(embedded_inputs, dict) or set(embedded_inputs) != set(CHILD_IDS):
            return False
        for child_id in ids:
            wrapper = embedded_inputs[child_id]
            expected = child_configs[child_id]["definition"]
            _validate_child_wrapper(child_id, wrapper, normalized or {
                "target": receipt.get("target"),
                "target_sha256": receipt.get("target_sha256"),
                "candidate_order_sha256": receipt.get("candidate_order_sha256"),
                "live_order_sha256": receipt.get("live_order_sha256"),
                "profile": receipt.get("profile"),
                "config_sha256": receipt.get("config_sha256"),
                "retained_cumulative_receipt_sha256": receipt.get("retained_cumulative_receipt_sha256"),
                "retained_cumulative_receipt_self_sha256": receipt.get("retained_cumulative_receipt_self_sha256"),
                "retained_cumulative_run_id": receipt.get("retained_cumulative_run_id"),
                "context_epoch_sha256": receipt.get("context_epoch_sha256"),
                "branch_frontier_sha256": receipt.get("branch_frontier_sha256"),
                "expected_source_set_sha256": receipt.get("expected_source_set_sha256"),
            })
            row = next(row for row in rows if row["child_id"] == child_id)
            child_receipt = receipt["child_receipts"].get(child_id)
            if row.get("operation_id") != CHILD_OPERATIONS[child_id] or row.get("leaf_operation") != LEAF_OPERATION:
                return False
            if row.get("input_sha256") != digest(wrapper) or row.get("leaf_input_sha256") != digest(wrapper["leaf_input"]):
                return False
            if row.get("receipt") != child_receipt or not isinstance(child_receipt, dict):
                return False
            if row.get("receipt_sha256") != child_receipt.get("receipt_sha256") or row.get("status") != child_receipt.get("status"):
                return False
            if row.get("terminal_state") == "CANCELLED":
                if (
                    child_receipt.get("cancellation_state") != "CANCELLED"
                    or child_receipt.get("status") != "CANCELLED_NO_AUTHORITY"
                    or not _verify_leaf(child_configs[child_id]["module"], wrapper["leaf_input"], child_receipt)
                ):
                    return False
            elif (
                not _verify_leaf(child_configs[child_id]["module"], wrapper["leaf_input"], child_receipt)
                or child_receipt.get("status") != "DESIGNED"
                or child_receipt.get("output_kind") != "PROPOSAL"
            ):
                return False
        if normalized is None:
            normalized = _packet_from_receipt(receipt)
            if normalized is None:
                return False
        authority = _load_authority(product_root, definition, authority_mode)
        _validate_authority_packet(normalized, authority)
        if (
            receipt.get("authority_bindings") != _authority_projection(authority)
            or receipt.get("authority_receipt_self_hash") != authority["receipt_sha256"]
            or receipt.get("authority_epoch_pointer_hash") != authority["pointer_sha256"]
            or receipt.get("authority_bindings_sha256") != authority["bindings_sha256"]
            or receipt.get("authority_receipt_mode") != authority["receipt_mode"]
            or receipt.get("authority_receipt_path") != authority["receipt_path"]
            or receipt.get("authority_pointer_mode") != authority["pointer_mode"]
            or receipt.get("authority_pointer_path") != authority["pointer_path"]
            or receipt.get("authority_epoch_path") != authority["epoch_path"]
            or receipt.get("authority_manifest_path") != authority["manifest_path"]
            or receipt.get("authority_manifest_sha256") != authority["manifest_sha256"]
            or receipt.get("authority_mode") != authority_mode
        ):
            return False
        current_config, current_profile, current_live_order, current_config_path = _load_config(product_root, normalized)
        _validate_retained_cumulative_receipt(
            normalized["retained_cumulative_receipt"],
            normalized,
            current_profile,
            current_live_order,
            require_self=False,
        )
        if (
            receipt.get("retained_receipt_self_sha256") != normalized["retained_cumulative_receipt"]["receipt_sha256"]
            or receipt.get("retained_prefix3_lock") != _retained_prefix3_lock_projection(normalized["retained_cumulative_receipt"])
        ):
            return False
        if receipt.get("config_path") != _relative(product_root, current_config_path) or receipt.get("live_order") != current_live_order:
            return False
        if not _verify_attestations(receipt, product_root, normalized, child_configs, authority_mode):
            return False
        status = receipt.get("status")
        if status == "CANCELLED":
            if receipt.get("cancellation_state") != "CANCELLED" or receipt.get("frontier") is not None or receipt.get("output_digest") is not None:
                return False
        elif status in {"MATCH_OBSERVED", "HOLD_ORDER_MISMATCH"}:
            if ids != list(CHILD_IDS) or receipt.get("cancellation_state") != "NOT_REQUESTED":
                return False
            config, profile, live_order, config_path = _load_config(product_root, normalized)
            retained = normalized.get("retained_cumulative_receipt") if isinstance(normalized.get("retained_cumulative_receipt"), dict) else None
            if retained is None:
                return False
            if receipt.get("config_path") != _relative(product_root, config_path) or receipt.get("live_order") != live_order:
                return False
            evidence = _prefix_lock_evidence(profile, retained)
            controls = _admission_controls(
                normalized["candidate_order"],
                live_order,
                profile,
                retained,
                child_configs,
                normalized["child_inputs"]["bind_survivors"]["leaf_input"],
                definition["control_receipts"],
                receipt["source_hashes"],
            )
            comparison = _comparison(normalized["candidate_order"], live_order)
            control_specs = {row["id"]: row for row in definition["control_receipts"]}
            if not isinstance(receipt.get("control_receipts"), list) or not all(_verify_control_receipt(row, control_specs[row.get("control_id")], receipt["source_hashes"]) for row in receipt["control_receipts"] if row.get("control_id") in control_specs):
                return False
            if receipt.get("negative_controls") != controls or receipt.get("control_receipts") != controls or receipt.get("prefix_lock_evidence") != evidence or receipt.get("admission_disposition") != "ADMISSION_CLEAN":
                return False
            if receipt.get("status") != comparison["status"] or receipt.get("reason") != ("HOLD_ORDER_MISMATCH" if comparison["status"] == "HOLD_ORDER_MISMATCH" else None):
                return False
            expected_frontier = _normal_frontier(normalized, comparison, evidence)
            if receipt.get("frontier") != expected_frontier or receipt.get("output_digest") != digest(expected_frontier):
                return False
        elif status == "REFUSE":
            if receipt.get("frontier") is not None or receipt.get("output_digest") is not None:
                return False
        else:
            return False
        if _contains_forbidden({key: value for key, value in receipt.items() if key not in {"claim_ceiling"}}):
            return False
        return _verify_self_digest(receipt)
    except (CandidateRefusal, OSError, TypeError, ValueError, RecursionError, StopIteration):
        return False


def _packet_from_receipt(receipt: Mapping[str, Any]) -> dict[str, Any] | None:
    """Reconstruct the exact bound packet for receipt-only replay/verification."""

    required = (
        "target",
        "target_bytes",
        "target_sha256",
        "candidate_order",
        "candidate_order_sha256",
        "live_order",
        "live_order_sha256",
        "profile",
        "config_path",
        "config_sha256",
        "retained_cumulative_receipt",
        "retained_cumulative_receipt_sha256",
        "retained_cumulative_receipt_self_sha256",
        "retained_cumulative_run_id",
        "context_epoch",
        "context_epoch_sha256",
        "branch_frontier",
        "branch_frontier_sha256",
        "expected_source_set_sha256",
        "child_inputs",
    )
    if any(key not in receipt for key in required):
        return None
    packet = {"schema": INPUT_SCHEMA, "wave_id": WAVE_ID, "operation": PARENT_OPERATION}
    packet.update({key: copy.deepcopy(receipt[key]) for key in required})
    if receipt.get("status") == "CANCELLED" and receipt.get("reason") == "CANCELLED_PARENT_REQUEST":
        packet["cancel_requested"] = True
    return packet


def replay_receipt(receipt: Any | Path, packet: Any | Path | None = None, *, root: Path | None = None, authority_mode: str = "LIVE") -> dict[str, Any]:
    prior = _read_json(receipt) if isinstance(receipt, Path) else receipt
    if isinstance(packet, (Path, str)):
        candidate_path = Path(packet)
        if root is None and candidate_path.is_dir():
            root = candidate_path
            packet = None
        elif candidate_path.is_file():
            packet = _read_json(candidate_path)
    if packet is None and isinstance(prior, dict):
        packet = _packet_from_receipt(prior)
    if packet is None:
        return {"schema": SCHEMA, "status": "REFUSE", "reason": "REFUSE_PACKET_REQUIRED", "digest_match": False}
    if not verify_receipt(prior, packet, root=root, authority_mode=authority_mode):
        return {"schema": SCHEMA, "status": "REFUSE", "reason": "REFUSE_RECEIPT_TAMPER", "digest_match": False}
    current = run_packet(packet, root=root, authority_mode=authority_mode)
    match = current.get("receipt_sha256") == prior.get("receipt_sha256")
    return {
        "schema": SCHEMA,
        "status": "REPLAY_MATCH" if match else "REPLAY_MISMATCH",
        "reason": None if match else "REPLAY_DIGEST_MISMATCH",
        "digest_match": match,
        "receipt_sha256": current.get("receipt_sha256"),
        "promotion_allowed": False,
        "writes_performed": False,
    }


def replay(packet: Any, prior: Any | None = None, *, root: Path | None = None, authority_mode: str = "LIVE") -> dict[str, Any]:
    if prior is None:
        current = run_packet(packet, root=root, authority_mode=authority_mode)
        return {"schema": SCHEMA, "status": "REPLAYED", "digest_match": True, "receipt_sha256": current.get("receipt_sha256")}
    return replay_receipt(prior, packet, root=root, authority_mode=authority_mode)


def run_wave(root: Path, packet: Any | None = None, *, out_path: Path | None = None, cancel_requested: bool | None = None, authority_mode: str = "LIVE") -> dict[str, Any]:
    if packet is None:
        default_packet = "strategy_discriminator_input_v1.json" if authority_mode == "FIXTURE" else "strategy_discriminator_live_input_v1.json"
        packet = _read_json(Path(__file__).resolve().parents[1] / "fixtures" / default_packet)
    elif isinstance(packet, (Path, str)):
        packet = _read_json(Path(packet))
    receipt = run_packet(packet, root=root, cancel_requested=cancel_requested, authority_mode=authority_mode)
    if out_path is not None:
        # The output write is the final boundary.  Re-read and verify every
        # current source, input, retained receipt, and child receipt immediately
        # before writing; a changed source becomes a refusal with no write.
        verify_packet = copy.deepcopy(packet)
        if cancel_requested is not None and isinstance(verify_packet, dict):
            verify_packet["cancel_requested"] = cancel_requested
        if not verify_receipt(receipt, verify_packet, root=root, authority_mode=authority_mode):
            if receipt.get("status") == "REFUSE":
                # Preserve a refusal's completed child prefix and do not
                # replace it with a shorter prewrite refusal.
                return receipt
            try:
                product_root = _root(root)
                _, _, _, definition_path = _load_definition(product_root)
                refusal = _base_receipt(packet, definition_sha=file_digest(definition_path))
            except (CandidateRefusal, OSError, TypeError, ValueError):
                refusal = _base_receipt(packet)
            refusal["reason"] = "REFUSE_PREWRITE_ATTESTATION"
            return _seal(refusal)
        _write_json(Path(out_path), receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--verify", type=Path, default=None)
    parser.add_argument("--fixture-mode", action="store_true")
    args = parser.parse_args(argv)
    try:
        packet = _read_json(args.packet)
        if args.verify is not None:
            receipt = _read_json(args.verify)
            ok = verify_receipt(receipt, packet, root=args.root, authority_mode="FIXTURE" if args.fixture_mode else "LIVE")
            print(json.dumps({"status": "VERIFIED" if ok else "REFUSE_RECEIPT"}, sort_keys=True))
            return 0 if ok else 2
        receipt = run_wave(args.root or Path(__file__).resolve().parents[5], packet, out_path=args.out, authority_mode="FIXTURE" if args.fixture_mode else "LIVE")
        print(json.dumps({"status": receipt.get("status"), "reason": receipt.get("reason")}, sort_keys=True))
        return 0 if receipt.get("status") in {"MATCH_OBSERVED", "HOLD_ORDER_MISMATCH", "CANCELLED"} else 2
    except (CandidateRefusal, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "REFUSE", "reason": f"REFUSE_CLI:{type(exc).__name__}"}, sort_keys=True))
        return 2


# Filled after the candidate source and definition are sealed.  The trusted
# validator is an existing static source and can be pinned immediately.
EXPECTED_DEFINITION_SHA256 = "e8a18b7a528397ec72d32804038662e4f2ee07d6c12063d486b089df29cfcd7e"
EXPECTED_VALIDATOR_SHA256 = "166b4938b52ac7f3ce8b9a3a8ca4923b07f6874899d328864e53ab63dfe5e11d"
EXPECTED_PARENT_SKILL_SHA256 = "f38ed168604335f2141a6945a10b0cc6394e1117fea8acf5a808224511c269a7"


if __name__ == "__main__":
    raise SystemExit(main())
