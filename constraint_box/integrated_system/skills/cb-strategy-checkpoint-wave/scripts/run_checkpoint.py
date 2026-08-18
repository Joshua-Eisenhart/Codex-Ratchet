#!/usr/bin/env python3
"""Run the contained, inactive strategy-checkpoint candidate.

The parent is deliberately model-free.  It validates exact source-bound
failure/repair/context inputs, calls four existing deterministic leaves in a
fixed order, and compiles a non-voting routing disposition.  It never writes
branch memory, applies a repair, starts a provider, loads an MMM, or promotes
an output.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Callable, Mapping


SCHEMA = "constraintbox.strategy-checkpoint-wave-receipt.v1"
INPUT_SCHEMA = "constraintbox.strategy-checkpoint-wave-input.v1"
WAVE_ID = "cb-strategy-checkpoint-wave-v1"
PARENT_OPERATION = "checkpoint_after_failure_and_repair"
CLAIM_CEILING = (
    "Source-bound checkpoint evidence and deterministic non-voting routing "
    "only; no truth verdict, strategy vote, provider route, MMM execution, "
    "repair, activation, or promotion."
)
ROUTE_TRUTH = "NOT_FULL"
ROUTE_TRUTH_LABEL = "NOT_FULL/model_free"
CHILD_IDS = ("repair_vs_object", "expansion", "rivals", "recency")
DISPOSITIONS = (
    "continue_candidate",
    "revert_repair",
    "split_target",
    "run_discriminator",
    "reopen_rival",
    "stop_satisfied",
    "reject_local_optimum",
    "request_owner_amendment",
    "cancelled",
)
# Safety and owner-boundary conditions precede local optimization signals.
# This table is emitted verbatim in every compiled receipt.
PRECEDENCE = (
    "cancelled",
    "request_owner_amendment",
    "revert_repair",
    "split_target",
    "run_discriminator",
    "reopen_rival",
    "reject_local_optimum",
    "stop_satisfied",
    "continue_candidate",
)
DISPOSITION_REASONS = {
    "continue_candidate": "NO_HIGHER_PRECEDENCE_TRIGGER",
    "revert_repair": "REPAIR_PROXY_OR_OBJECT_REGRESSION",
    "split_target": "TARGET_BOUNDARY_REQUIRES_SPLIT",
    "run_discriminator": "RECENCY_FLIP_REQUIRES_DISCRIMINATOR",
    "reopen_rival": "OLDER_RIVAL_REMAINS_LIVE",
    "stop_satisfied": "STOP_IS_BETTER_THAN_CONTINUATION",
    "reject_local_optimum": "SCOPE_EXPANSION_SUNK_COST_OR_PROXY_SEVERANCE",
    "request_owner_amendment": "OWNER_BOUNDARY_REQUIRES_AMENDMENT",
    "cancelled": "CANCELLATION_REQUESTED",
}

CHILD_FUNCTIONS: dict[str, str] = {
    "repair_vs_object": "classify",
    "expansion": "check_expansion",
    "rivals": "resurrect",
    "recency": "audit",
}
CHILD_SOURCE_NAMES = {
    "repair_vs_object": "classify.py",
    "expansion": "check_expansion.py",
    "rivals": "remember.py",
    "recency": "audit_recency.py",
}
CHILD_TARGET_KEYS = {
    "repair_vs_object": ("target",),
    "expansion": ("target_id", "target"),
    "rivals": ("target",),
    "recency": ("target",),
}
CHILD_OPERATION_KEYS = {
    "repair_vs_object": "operation",
    "expansion": "operation_id",
    "rivals": "operation",
    "recency": "operation",
}
CHILD_LEAF_OPERATIONS = {
    "repair_vs_object": "cb-impact-vs-output-auditor.v1",
    "expansion": "cb-resource-expansion-cell.v1",
    "rivals": "cb-branch-failure-memory.check.v1",
    "recency": "cb-recency-bias-auditor.v1",
}
CHILD_SCHEMAS = {
    "repair_vs_object": "constraintbox.impact-vs-output.v1",
    "expansion": "constraintbox.resource-expansion.v1",
    "rivals": "constraintbox.strategy-checkpoint-rival-input.v1",
    "recency": "constraintbox.strategy-checkpoint-recency-input.v1",
}

# This is caller-facing custody, not a baseline chosen by the runner.  Every
# path is fixed and root-relative so the caller can bind one digest before the
# first source read.  Child skill bytes and child runner bytes are both part
# of the set.
SOURCE_SET_RELATIVE_PATHS = (
    "cb-strategy-checkpoint-wave/SKILL.md",
    "cb-strategy-checkpoint-wave/scripts/run_checkpoint.py",
    "cb-strategy-checkpoint-wave/wave.json",
    "cb-wave-author/scripts/validate_wave.py",
    "cb-impact-vs-output-auditor/SKILL.md",
    "cb-impact-vs-output-auditor/scripts/classify.py",
    "cb-resource-expansion-cell/SKILL.md",
    "cb-resource-expansion-cell/scripts/check_expansion.py",
    "cb-branch-failure-memory/SKILL.md",
    "cb-branch-failure-memory/scripts/remember.py",
    "cb-recency-bias-auditor/SKILL.md",
    "cb-recency-bias-auditor/scripts/audit_recency.py",
)

PARENT_RECEIPT_KEYS = frozenset(
    {
        "schema", "wave_id", "status", "reason", "operation", "candidate_state", "target",
        "input_sha256", "expected_source_set_sha256", "source_set_sha256", "definition_sha256",
        "parent_cancellation_requested",
        "source_hashes", "artifact_bindings", "failure_receipt_sha256", "candidate_receipt_sha256",
        "context_epoch_digest", "branch_memory_snapshot_sha256", "current_projection_sha256",
        "ablated_projection_sha256", "child_order", "child_inputs", "children", "child_receipts",
        "findings", "contradictions", "minority_branches", "disagreements", "launched_child_order",
        "not_launched_child_ids", "decision_flags", "checkpoint_disposition", "disposition",
        "disposition_reason", "disposition_precedence", "cancellation_state", "route_truth",
        "route_truth_label", "model_free", "provider_dispatch_proved", "mmm_preload_applicable",
        "provider_receipt_applicable", "skill_execution_claimed", "mmm_preload_receipts",
        "provider_call_receipt", "not_applicable", "activated", "promotion_allowed", "winner_selected",
        "voting_performed", "truth_disposition", "truth_decided", "writes_performed", "receipt_written",
        "claim_ceiling", "output_digest", "receipt_sha256", "receipt_self_sha256",
    }
)
CHILD_RECEIPT_KEYS = {
    "repair_vs_object": frozenset(
        {
            "schema", "operation", "target", "status", "reason", "claim_ceiling", "promotion_allowed",
            "activated", "model_free", "provider_call_receipt", "audit_only", "proposal_only",
            "writes_performed", "cancellation_state", "input_sha256", "output_kind", "claim", "evidence",
            "class", "receipt_sha256", "receipt_self_sha256",
        }
    ),
    "expansion": frozenset(
        {
            "schema", "operation", "operation_id", "target", "target_id", "target_binding", "status",
            "reason", "claim_ceiling", "promotion_allowed", "activated", "model_free", "provider_call_receipt",
            "writes_performed", "receipt_written", "cancellation_state", "input_sha256", "output_kind",
            "expanded", "field", "missing", "unknown", "receipt_sha256", "receipt_self_sha256",
        }
    ),
    "rivals": frozenset(
        {
            "schema", "operation", "target", "status", "reason", "input_sha256", "claim_ceiling",
            "model_free", "provider_call_receipt", "promotion_allowed", "activated", "writes_performed",
            "receipt_written", "hits", "read_only", "source_check", "receipt_sha256", "receipt_self_sha256",
        }
    ),
    "recency": frozenset(
        {
            "schema", "operation", "target", "status", "reason", "input_sha256", "claim_ceiling",
            "model_free", "provider_call_receipt", "promotion_allowed", "activated", "writes_performed",
            "receipt_written", "flipped", "audit", "causal_evidence", "receipt_sha256", "receipt_self_sha256",
        }
    ),
}
DECISION_FLAG_KEYS = frozenset(
    {
        "owner_amendment_needed", "repair_addressed_proxy", "object_delta", "proxy_delta",
        "object_regressed", "object_improved", "proxy_rose", "proxy_severance", "repair_regressed",
        "repair_causality", "split_target", "recency_flip", "older_rival_dominates", "scope_expanded",
        "sunk_cost_defense", "stop_better",
    }
)

TOP_KEYS = frozenset(
    {
        "schema",
        "wave_id",
        "operation",
        "target",
        "expected_source_set_sha256",
        "before_repair",
        "after_repair",
        "failure_receipt",
        "candidate_receipt",
        "context_epoch",
        "branch_memory_snapshot",
        "current_projection",
        "ablated_projection",
        "child_inputs",
        "contradictions",
        "minority_branches",
        "disagreements",
        "cancel_requested",
    }
)
ARTIFACT_REF_KEYS = frozenset({"path", "sha256", "format", "content"})
HEX64 = set("0123456789abcdef")
MAX_BYTES = 2 * 1024 * 1024

# These constants are intentionally filled after the candidate sources are
# authored.  A fresh run therefore refuses a changed definition/validator,
# while receipt replay also checks the live source hashes.
EXPECTED_DEFINITION_SHA256 = "03f5e7ea7ecb90e30ba7c8b696b5bd134ec9733eedbcbf5c6979ffedab32fee7"
EXPECTED_VALIDATOR_SHA256 = "166b4938b52ac7f3ce8b9a3a8ca4923b07f6874899d328864e53ab63dfe5e11d"
EXPECTED_SKILL_SHA256 = "34bde294b2720f8b2b56deb054ea070bf08d20eae9b0b3cefbca17237b49d078"


class CandidateRefusal(ValueError):
    """A structural, custody, input, or receipt boundary was crossed."""


class DuplicateJSONKey(ValueError):
    """JSON object keys must not silently overwrite an earlier binding."""


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
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise CandidateRefusal(f"REFUSE_FILE_BOUNDS:{path.name}")
    return hashlib.sha256(raw).hexdigest()


def _safe_digest(value: Any) -> str | None:
    try:
        return digest(value)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return None


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX64


def _bounded(value: Any, *, depth: int = 0, state: list[int] | None = None) -> bool:
    if state is None:
        state = [0, 0]
    state[0] += 1
    if state[0] > 4096 or depth > 16:
        return False
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, str):
        try:
            size = len(value.encode("utf-8"))
        except UnicodeError:
            return False
        state[1] += size
        return size <= 64 * 1024 and state[1] <= MAX_BYTES
    if isinstance(value, int):
        return abs(value) <= 10**18
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return len(value) <= 1024 and all(_bounded(item, depth=depth + 1, state=state) for item in value)
    if isinstance(value, dict):
        return len(value) <= 512 and all(
            isinstance(key, str)
            and _bounded(key, depth=depth + 1, state=state)
            and _bounded(item, depth=depth + 1, state=state)
            for key, item in value.items()
        )
    return False


def _read_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        if len(raw) > MAX_BYTES:
            raise CandidateRefusal(f"REFUSE_FILE_BOUNDS:{path.name}")
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)),
        )
    except CandidateRefusal:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, DuplicateJSONKey, ValueError, RecursionError) as exc:
        raise CandidateRefusal(f"REFUSE_JSON:{path.name}") from exc
    if not isinstance(value, dict) or not _bounded(value):
        raise CandidateRefusal(f"REFUSE_JSON_OBJECT:{path.name}")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    try:
        raw = path.read_bytes()
        if len(raw) > MAX_BYTES:
            raise CandidateRefusal(f"REFUSE_FILE_BOUNDS:{path.name}")
        lines = raw.decode("utf-8").splitlines()
    except CandidateRefusal:
        raise
    except (OSError, UnicodeError) as exc:
        raise CandidateRefusal(f"REFUSE_JSONL:{path.name}") from exc
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(lines, start=1):
        if not line.strip():
            raise CandidateRefusal(f"REFUSE_JSONL_BLANK:{path.name}:{index}")
        try:
            value = json.loads(
                line,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=lambda item: (_ for _ in ()).throw(ValueError(item)),
            )
        except (json.JSONDecodeError, DuplicateJSONKey, ValueError, RecursionError) as exc:
            raise CandidateRefusal(f"REFUSE_JSONL:{path.name}:{index}") from exc
        if not isinstance(value, dict) or not _bounded(value):
            raise CandidateRefusal(f"REFUSE_JSONL_ROW:{path.name}:{index}")
        rows.append(value)
    return rows


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


def _source_set(root: Path) -> dict[str, Any]:
    """Attest the fixed caller-visible source set without recapturing it.

    The nested shape intentionally matches the parent ``source_hashes``
    receipt, so callers can independently recompute
    ``sha256(canonical_json(source_hashes))``.
    """

    parent_skill = _confined(root, "cb-strategy-checkpoint-wave/SKILL.md", "source_set:parent_skill")
    runner = _confined(root, "cb-strategy-checkpoint-wave/scripts/run_checkpoint.py", "source_set:runner")
    validator = _confined(root, "cb-wave-author/scripts/validate_wave.py", "source_set:trusted_validator")
    definition = _confined(root, "cb-strategy-checkpoint-wave/wave.json", "source_set:definition")
    children: dict[str, dict[str, str]] = {}
    for child_id, skill, script in (
        ("repair_vs_object", "cb-impact-vs-output-auditor/SKILL.md", "cb-impact-vs-output-auditor/scripts/classify.py"),
        ("expansion", "cb-resource-expansion-cell/SKILL.md", "cb-resource-expansion-cell/scripts/check_expansion.py"),
        ("rivals", "cb-branch-failure-memory/SKILL.md", "cb-branch-failure-memory/scripts/remember.py"),
        ("recency", "cb-recency-bias-auditor/SKILL.md", "cb-recency-bias-auditor/scripts/audit_recency.py"),
    ):
        children[child_id] = {
            "skill": file_digest(_confined(root, skill, f"source_set:{child_id}:skill")),
            "script": file_digest(_confined(root, script, f"source_set:{child_id}:script")),
        }
    source_hashes = {
        "parent_skill": file_digest(parent_skill),
        "runner": file_digest(runner),
        "trusted_validator": file_digest(validator),
        "definition": file_digest(definition),
        "children": children,
    }
    return {"source_hashes": source_hashes, "sha256": _source_set_sha256(source_hashes)}


def _source_set_sha256(source_hashes: Mapping[str, Any]) -> str:
    """Canonical caller-binding digest for a source-hash object."""

    return digest(source_hashes)


def _expected_source_set(packet: Any) -> str:
    if not isinstance(packet, dict) or not _is_digest(packet.get("expected_source_set_sha256")):
        raise CandidateRefusal("REFUSE_SOURCE_SET_EXPECTATION")
    return str(packet["expected_source_set_sha256"])


def _assert_expected_source_set(root: Path, expected: str) -> dict[str, Any]:
    current = _source_set(root)
    if current["sha256"] != expected:
        raise CandidateRefusal("REFUSE_SOURCE_SET_DRIFT")
    return current


def source_set_sha256(skills_root: Path | None = None) -> str:
    """Expose the caller-binding digest computation without running a wave."""

    return _source_set(_skills_root(skills_root))["sha256"]


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CandidateRefusal(f"REFUSE_CHILD_LOAD:{name}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except BaseException as exc:  # pragma: no cover - source drift path
        if isinstance(exc, (KeyboardInterrupt, GeneratorExit)):
            raise
        raise CandidateRefusal(f"REFUSE_CHILD_LOAD:{name}") from exc
    return module


def _runner_path(root: Path) -> Path:
    return _confined(root, "cb-strategy-checkpoint-wave/scripts/run_checkpoint.py", "runner")


def _delegate_runner(root: Path, function_name: str) -> Any | None:
    """Load the supplied-root runner when the caller uses a copied tree.

    This prevents the host-imported ``__file__`` from becoming an implicit
    source authority.  The delegated module is the exact runner whose bytes
    are included in the supplied root source set.
    """

    supplied = _runner_path(root)
    imported = Path(__file__).resolve()
    if supplied == imported:
        return None
    module_name = f"cb_strategy_checkpoint_supplied_{digest(str(supplied))[:16]}"
    module = _load_module(supplied, module_name)
    function = getattr(module, function_name, None)
    if not callable(function):
        raise CandidateRefusal(f"REFUSE_SUPPLIED_RUNNER_CALLABLE:{function_name}")
    return function


def _call_delegated(function: Callable[..., Any], function_name: str, *args: Any, **kwargs: Any) -> Any:
    """Normalize exceptions from an isolated module into local custody codes."""

    try:
        return function(*args, **kwargs)
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, GeneratorExit)):
            raise
        # Never let the delegated module's CandidateRefusal class (or an
        # arbitrary traceback/detail) cross the root boundary.  The caller
        # receives one bounded local refusal code instead.
        kind = type(exc).__name__
        if kind == "CandidateRefusal":
            raise CandidateRefusal("REFUSE_SUPPLIED_RUNNER_DELEGATED") from None
        raise CandidateRefusal(f"REFUSE_SUPPLIED_RUNNER_EXCEPTION:{function_name}:{kind}") from None


def _definition(root: Path) -> tuple[dict[str, Any], Path, dict[str, Any], Path]:
    definition_path = _confined(root, "cb-strategy-checkpoint-wave/wave.json", "definition")
    definition = _read_json(definition_path)
    current_definition_sha = file_digest(definition_path)
    if EXPECTED_DEFINITION_SHA256 and current_definition_sha != EXPECTED_DEFINITION_SHA256:
        raise CandidateRefusal("REFUSE_DEFINITION_SOURCE_DRIFT")
    validator_path = _confined(root, "cb-wave-author/scripts/validate_wave.py", "trusted_validator")
    current_validator_sha = file_digest(validator_path)
    if EXPECTED_VALIDATOR_SHA256 and current_validator_sha != EXPECTED_VALIDATOR_SHA256:
        raise CandidateRefusal("REFUSE_TRUSTED_VALIDATOR_SOURCE_DRIFT")
    candidate_skill_path = _confined(root, "cb-strategy-checkpoint-wave/SKILL.md", "candidate_skill")
    if EXPECTED_SKILL_SHA256 and file_digest(candidate_skill_path) != EXPECTED_SKILL_SHA256:
        raise CandidateRefusal("REFUSE_CANDIDATE_SKILL_SOURCE_DRIFT")
    validator = _load_module(validator_path, "cb_strategy_checkpoint_trusted_validator")
    try:
        errors = list(validator.validate(definition)) + list(validator.validate_tree(definition, root))
    except Exception as exc:
        raise CandidateRefusal("REFUSE_TRUSTED_VALIDATOR") from exc
    if errors:
        raise CandidateRefusal("REFUSE_WAVE_DEFINITION:" + ",".join(sorted(set(errors))))
    if definition.get("wave_id") != WAVE_ID:
        raise CandidateRefusal("REFUSE_WAVE_ID")
    children = definition.get("children")
    if not isinstance(children, list) or [row.get("id") for row in children if isinstance(row, dict)] != list(CHILD_IDS):
        raise CandidateRefusal("REFUSE_CHILD_ORDER")
    configs: dict[str, Any] = {}
    for row in children:
        if not isinstance(row, dict):
            raise CandidateRefusal("REFUSE_CHILD_SHAPE")
        child_id = str(row.get("id"))
        if child_id in configs:
            raise CandidateRefusal(f"REFUSE_DUPLICATE_CHILD_DEFINITION:{child_id}")
        skill = row.get("skill")
        source = row.get("source")
        leaf_operation = row.get("leaf_operation")
        if not isinstance(skill, str) or not isinstance(source, str) or not isinstance(leaf_operation, str):
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_BINDING:{child_id}")
        if source != f"{skill}/scripts/{CHILD_SOURCE_NAMES[child_id]}":
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_BINDING:{child_id}")
        source_path = _confined(root, source, f"child_source:{child_id}")
        skill_path = _confined(root, f"{skill}/SKILL.md", f"child_skill:{child_id}")
        if not _is_digest(row.get("source_sha256")) or not _is_digest(row.get("skill_sha256")):
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_DIGEST:{child_id}")
        if file_digest(source_path) != row["source_sha256"]:
            raise CandidateRefusal(f"REFUSE_CHILD_SOURCE_DRIFT:{child_id}")
        if file_digest(skill_path) != row["skill_sha256"]:
            raise CandidateRefusal(f"REFUSE_CHILD_SKILL_DRIFT:{child_id}")
        module = _load_module(source_path, f"cb_strategy_checkpoint_{child_id}")
        if child_id in {"repair_vs_object", "expansion"} and getattr(module, "OPERATION", None) != leaf_operation:
            raise CandidateRefusal(f"REFUSE_CHILD_OPERATION_BINDING:{child_id}")
        function = getattr(module, CHILD_FUNCTIONS[child_id], None)
        if not callable(function):
            raise CandidateRefusal(f"REFUSE_CHILD_CALLABLE:{child_id}")
        configs[child_id] = {
            "definition": row,
            "module": module,
            "function": function,
            "source_path": source_path,
            "skill_path": skill_path,
            "leaf_operation": leaf_operation,
        }
    return definition, definition_path, configs, validator_path


def _artifact_ref_shape(ref: Any, label: str) -> dict[str, Any]:
    if not isinstance(ref, dict) or not _bounded(ref):
        raise CandidateRefusal(f"REFUSE_ARTIFACT_REF:{label}")
    unknown = set(ref) - ARTIFACT_REF_KEYS
    if unknown:
        raise CandidateRefusal(f"REFUSE_ARTIFACT_REF_EXTRA:{label}")
    path = ref.get("path")
    if not isinstance(path, str) or not path.strip():
        raise CandidateRefusal(f"REFUSE_ARTIFACT_PATH:{label}")
    if not _is_digest(ref.get("sha256")):
        raise CandidateRefusal(f"REFUSE_ARTIFACT_SHA256:{label}")
    fmt = ref.get("format", "json")
    if fmt not in {"json", "jsonl"}:
        raise CandidateRefusal(f"REFUSE_ARTIFACT_FORMAT:{label}")
    if "content" in ref and not _bounded(ref["content"]):
        raise CandidateRefusal(f"REFUSE_ARTIFACT_CONTENT:{label}")
    return copy.deepcopy(ref)


def _read_artifact(root: Path, ref: Any, label: str) -> tuple[Any, dict[str, Any]]:
    shaped = _artifact_ref_shape(ref, label)
    path = _confined(root, shaped["path"], f"artifact:{label}")
    observed = file_digest(path)
    if observed != shaped["sha256"]:
        raise CandidateRefusal(f"REFUSE_ARTIFACT_SOURCE_DRIFT:{label}")
    if shaped.get("format", "json") == "jsonl":
        value = _read_jsonl(path)
    else:
        value = _read_json(path)
    if "content" in shaped and shaped["content"] != value:
        raise CandidateRefusal(f"REFUSE_ARTIFACT_CONTENT_TAMPER:{label}")
    observed_ref = {"path": shaped["path"], "sha256": observed, "format": shaped.get("format", "json")}
    if "content" in shaped:
        observed_ref["content"] = copy.deepcopy(shaped["content"])
    return value, observed_ref


def _verify_self(value: Mapping[str, Any], field: str) -> bool:
    expected = value.get(field)
    if not _is_digest(expected):
        return False
    aliases = {field.replace("sha256", "self_sha256")} if field.endswith("sha256") else {field.replace("_digest", "_self_digest")}
    unsigned = dict(value)
    for alias in aliases:
        if alias in value and value[alias] != expected:
            return False
        unsigned.pop(alias, None)
    unsigned.pop(field, None)
    return digest(unsigned) == expected


def _require_target(value: Any, target: str, label: str) -> None:
    if not isinstance(value, dict):
        raise CandidateRefusal(f"REFUSE_{label}_SHAPE")
    supplied = value.get("target")
    if supplied != target:
        raise CandidateRefusal(f"REFUSE_{label}_TARGET_REBOUND")


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _validate_artifacts(root: Path, packet: Mapping[str, Any]) -> dict[str, Any]:
    before, before_ref = _read_artifact(root, packet["before_repair"], "before_repair")
    after, after_ref = _read_artifact(root, packet["after_repair"], "after_repair")
    failure, failure_ref = _read_artifact(root, packet["failure_receipt"], "failure_receipt")
    candidate, candidate_ref = _read_artifact(root, packet["candidate_receipt"], "candidate_receipt")
    epoch, epoch_ref = _read_artifact(root, packet["context_epoch"], "context_epoch")
    branches, branch_ref = _read_artifact(root, packet["branch_memory_snapshot"], "branch_memory_snapshot")
    current, current_ref = _read_artifact(root, packet["current_projection"], "current_projection")
    ablated, ablated_ref = _read_artifact(root, packet["ablated_projection"], "ablated_projection")
    target = str(packet["target"])
    for value, label in ((before, "BEFORE_REPAIR"), (after, "AFTER_REPAIR"), (failure, "FAILURE_RECEIPT"), (candidate, "CANDIDATE_RECEIPT"), (current, "CURRENT_PROJECTION"), (ablated, "ABLATED_PROJECTION")):
        _require_target(value, target, label)
    if isinstance(epoch, dict) and epoch.get("target") is not None and epoch.get("target") != target:
        raise CandidateRefusal("REFUSE_CONTEXT_EPOCH_TARGET_REBOUND")
    if not isinstance(before, dict) or before.get("schema") != "constraintbox.repair-artifact.v1" or before.get("artifact_role") != "before_repair":
        raise CandidateRefusal("REFUSE_BEFORE_REPAIR_ARTIFACT")
    if not isinstance(after, dict) or after.get("schema") != "constraintbox.repair-artifact.v1" or after.get("artifact_role") != "after_repair":
        raise CandidateRefusal("REFUSE_AFTER_REPAIR_ARTIFACT")
    for value, label in ((before, "before"), (after, "after")):
        if not isinstance(value.get("artifact_id"), str) or not value["artifact_id"].strip():
            raise CandidateRefusal(f"REFUSE_{label.upper()}_ARTIFACT_ID")
        if not _finite_number(value.get("object_measure")) or not _finite_number(value.get("proxy_measure")):
            raise CandidateRefusal(f"REFUSE_{label.upper()}_MEASURE")
        if not isinstance(value.get("authorized_resources"), dict) or not isinstance(value.get("used_resources"), dict):
            raise CandidateRefusal(f"REFUSE_{label.upper()}_RESOURCES")
    if not isinstance(failure, dict) or failure.get("schema") != "constraintbox.failure-receipt.v1" or failure.get("status") != "FAILED" or failure.get("failure_verified") is not True or not _verify_self(failure, "receipt_sha256"):
        raise CandidateRefusal("REFUSE_UNVERIFIED_FAILURE")
    if not isinstance(candidate, dict) or candidate.get("schema") != "constraintbox.repair-candidate-receipt.v1" or candidate.get("repair_verified") is not True or candidate.get("status") not in {"REPAIRED", "REPAIR_VERIFIED", "CANDIDATE_VERIFIED"} or not _verify_self(candidate, "receipt_sha256"):
        raise CandidateRefusal("REFUSE_UNVERIFIED_REPAIR")
    if not isinstance(candidate.get("candidate_id"), str) or not candidate["candidate_id"].strip():
        raise CandidateRefusal("REFUSE_CANDIDATE_ID")
    if candidate.get("before_artifact_sha256") != before_ref["sha256"] or candidate.get("after_artifact_sha256") != after_ref["sha256"]:
        raise CandidateRefusal("REFUSE_REPAIR_ARTIFACT_BINDING")
    if candidate.get("failure_receipt_sha256") != failure_ref["sha256"]:
        raise CandidateRefusal("REFUSE_FAILURE_CANDIDATE_BINDING")
    epoch_sealed = isinstance(epoch, dict) and (
        epoch.get("sealed") is True
        or (
            epoch.get("schema") == "constraintbox.context-epoch.v2"
            and isinstance(epoch.get("bound_files"), dict)
            and isinstance(epoch.get("epoch_sequence"), int)
        )
    )
    if not isinstance(epoch, dict) or epoch.get("schema") not in {"constraintbox.context-epoch.v1", "constraintbox.context-epoch.v2"} or not epoch_sealed or not _verify_self(epoch, "epoch_digest"):
        raise CandidateRefusal("REFUSE_UNVERIFIED_CONTEXT_EPOCH")
    if candidate.get("context_epoch_digest") != epoch.get("epoch_digest"):
        raise CandidateRefusal("REFUSE_CONTEXT_EPOCH_BINDING")
    if not isinstance(branches, list):
        raise CandidateRefusal("REFUSE_BRANCH_SNAPSHOT_FORMAT")
    for index, row in enumerate(branches):
        if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row.get("id"):
            raise CandidateRefusal(f"REFUSE_BRANCH_SNAPSHOT_ROW:{index}")
        if row.get("target") is not None and row.get("target") != target:
            raise CandidateRefusal(f"REFUSE_BRANCH_SNAPSHOT_TARGET:{index}")
    if branch_ref.get("format") != "jsonl":
        raise CandidateRefusal("REFUSE_BRANCH_SNAPSHOT_NOT_JSONL")
    if not isinstance(current, dict) or current.get("schema") != "constraintbox.strategy-projection.v1" or not _verify_self(current, "projection_sha256"):
        raise CandidateRefusal("REFUSE_CURRENT_PROJECTION")
    if not isinstance(ablated, dict) or ablated.get("schema") != "constraintbox.strategy-projection.v1" or not _verify_self(ablated, "projection_sha256"):
        raise CandidateRefusal("REFUSE_ABLATED_PROJECTION")
    if current.get("candidate_id") != candidate.get("candidate_id") or ablated.get("candidate_id") != candidate.get("candidate_id"):
        raise CandidateRefusal("REFUSE_PROJECTION_CANDIDATE_BINDING")
    if not isinstance(current.get("decision"), str) or not isinstance(ablated.get("decision"), str):
        raise CandidateRefusal("REFUSE_PROJECTION_DECISION")
    if current.get("causal_evidence") is not None and not _bounded(current.get("causal_evidence")):
        raise CandidateRefusal("REFUSE_PROJECTION_EVIDENCE")
    for key in ("split_target", "stop_better", "owner_amendment_needed", "sunk_cost_defense", "older_rival_dominates"):
        if key in candidate and not isinstance(candidate[key], bool):
            raise CandidateRefusal(f"REFUSE_CANDIDATE_FLAG:{key}")
    if "repair_addressed" in candidate and candidate["repair_addressed"] not in {"object", "proxy", "none"}:
        raise CandidateRefusal("REFUSE_CANDIDATE_REPAIR_ENUM")
    for key in ("split_target", "stop_better", "owner_amendment_needed"):
        if key in current and not isinstance(current[key], bool):
            raise CandidateRefusal(f"REFUSE_PROJECTION_FLAG:{key}")
    return {
        "before": before,
        "after": after,
        "failure": failure,
        "candidate": candidate,
        "epoch": epoch,
        "branches": branches,
        "current": current,
        "ablated": ablated,
        "refs": {
            "before_repair": before_ref,
            "after_repair": after_ref,
            "failure_receipt": failure_ref,
            "candidate_receipt": candidate_ref,
            "context_epoch": epoch_ref,
            "branch_memory_snapshot": branch_ref,
            "current_projection": current_ref,
            "ablated_projection": ablated_ref,
        },
    }


def _validate_packet(packet: Any, definition: Mapping[str, Any], root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(packet, dict) or not _bounded(packet):
        raise CandidateRefusal("REFUSE_PACKET_SHAPE")
    unknown = set(packet) - TOP_KEYS
    if unknown:
        raise CandidateRefusal("REFUSE_PACKET_EXTRA:" + ",".join(sorted(map(str, unknown))))
    required = TOP_KEYS - {"contradictions", "minority_branches", "disagreements", "cancel_requested"}
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
    if "cancel_requested" in packet and not isinstance(packet["cancel_requested"], bool):
        raise CandidateRefusal("REFUSE_PACKET_CANCEL_TYPE")
    for key in ("contradictions", "minority_branches", "disagreements"):
        if key in packet and (not isinstance(packet[key], list) or not _bounded(packet[key])):
            raise CandidateRefusal(f"REFUSE_PACKET_{key.upper()}")
    child_inputs = packet.get("child_inputs")
    if not isinstance(child_inputs, dict) or set(child_inputs) != set(CHILD_IDS):
        raise CandidateRefusal("REFUSE_CHILD_SET")
    normalized = copy.deepcopy(packet)
    artifacts = _validate_artifacts(root, normalized)
    candidate = artifacts["candidate"]
    after = artifacts["after"]
    current = artifacts["current"]
    ablated = artifacts["ablated"]
    expected_inputs = {
        "repair_vs_object": {
            "schema": "constraintbox.impact-vs-output.v1",
            "operation": CHILD_LEAF_OPERATIONS["repair_vs_object"],
            "target": target,
            "claim": candidate.get("impact_claim"),
            "evidence": candidate.get("impact_evidence"),
        },
        "expansion": {
            "target_id": target,
            "operation_id": CHILD_LEAF_OPERATIONS["expansion"],
            "authorized": after.get("authorized_resources"),
            "used": after.get("used_resources"),
        },
        "rivals": {
            "schema": CHILD_SCHEMAS["rivals"],
            "operation": CHILD_LEAF_OPERATIONS["rivals"],
            "target": target,
            "memory_path": normalized["branch_memory_snapshot"]["path"],
            "memory_sha256": artifacts["refs"]["branch_memory_snapshot"]["sha256"],
            "candidate_id": candidate["candidate_id"],
            "new_bridge": candidate.get("new_bridge"),
            "new_evidence": candidate.get("new_evidence"),
        },
        "recency": {
            "schema": CHILD_SCHEMAS["recency"],
            "operation": CHILD_LEAF_OPERATIONS["recency"],
            "target": target,
            "current": current,
            "ablated": ablated,
            "causal_evidence": current.get("causal_evidence"),
        },
    }
    if expected_inputs["repair_vs_object"]["claim"] not in {"artifact", "metric", "external_condition"} or not isinstance(expected_inputs["repair_vs_object"]["evidence"], list) or not expected_inputs["repair_vs_object"]["evidence"]:
        raise CandidateRefusal("REFUSE_IMPACT_CHILD_INPUT")
    for child_id, expected in expected_inputs.items():
        supplied = child_inputs[child_id]
        if not isinstance(supplied, dict) or supplied != expected:
            raise CandidateRefusal(f"REFUSE_CHILD_INPUT_REBOUND:{child_id}")
        operation_key = CHILD_OPERATION_KEYS[child_id]
        if supplied.get(operation_key) != CHILD_LEAF_OPERATIONS[child_id]:
            raise CandidateRefusal(f"REFUSE_CHILD_OPERATION:{child_id}")
        for target_key in CHILD_TARGET_KEYS[child_id]:
            if target_key in supplied and supplied[target_key] != target:
                raise CandidateRefusal(f"REFUSE_CHILD_TARGET_REBOUND:{child_id}")
    normalized["child_inputs"] = copy.deepcopy(child_inputs)
    return normalized, artifacts


def _source_hashes(root: Path, definition_path: Path, configs: Mapping[str, Any], validator_path: Path) -> dict[str, Any]:
    return {
        "runner": file_digest(_runner_path(root)),
        "parent_skill": file_digest(definition_path.parent / "SKILL.md"),
        "trusted_validator": file_digest(validator_path),
        "definition": file_digest(definition_path),
        "children": {
            child_id: {
                "skill": file_digest(config["skill_path"]),
                "script": file_digest(config["source_path"]),
            }
            for child_id, config in configs.items()
        },
    }


def _assert_source_attestation(
    definition_path: Path,
    configs: Mapping[str, Any],
    validator_path: Path,
    expected: Mapping[str, Any],
    expected_source_set_sha256: str,
) -> None:
    """Re-attest every immutable parent/definition/runner/child source.

    This is intentionally repeated before each child and immediately before
    the parent receipt is sealed.  A child may not mutate the source tree and
    leave a later receipt claiming that the earlier attestation still holds.
    """

    _assert_expected_source_set(definition_path.parent.parent, expected_source_set_sha256)
    current = _source_hashes(definition_path.parent.parent, definition_path, configs, validator_path)
    if dict(current) != dict(expected):
        raise CandidateRefusal("REFUSE_SOURCE_DRIFT")


def _custom_child_base(schema: str, operation: str, target: str, input_value: Any, status: str, reason: str | None = None) -> dict[str, Any]:
    return {
        "schema": schema,
        "operation": operation,
        "target": target,
        "status": status,
        "reason": reason,
        "input_sha256": digest(input_value),
        "claim_ceiling": "Read-only child observation only; no strategy vote or promotion.",
        "model_free": True,
        "provider_call_receipt": None,
        "promotion_allowed": False,
        "activated": False,
        "writes_performed": False,
        "receipt_written": False,
    }


def _seal_child(value: dict[str, Any]) -> dict[str, Any]:
    unsigned = copy.deepcopy(value)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    sealed = copy.deepcopy(unsigned)
    sealed["receipt_sha256"] = digest(unsigned)
    sealed["receipt_self_sha256"] = sealed["receipt_sha256"]
    return sealed


def _branch_child(module: Any, child_input: dict[str, Any], branches: list[dict[str, Any]], memory_path: Path | None = None) -> dict[str, Any]:
    # The declared path remains part of the child input digest; only the
    # already-confined resolved path is handed to the read-only leaf.
    path = memory_path if memory_path is not None else Path(child_input["memory_path"])
    proposal = {
        "id": child_input["candidate_id"],
        "new_bridge": child_input.get("new_bridge"),
        "new_evidence": child_input.get("new_evidence"),
    }
    try:
        result = module.resurrect(path, proposal)
    except Exception as exc:
        raise CandidateRefusal("REFUSE_RIVAL_CHILD_EXCEPTION") from exc
    hits = [row.get("id") for row in branches if row.get("id") == proposal["id"]]
    if hits and result.get("status") == "REFUSE" and result.get("reason") == "REFUSE_RESURRECTION":
        status = "RIVAL_LIVE"
        reason = "OLDER_RIVAL_REMAINS_IN_FAILURE_MEMORY"
    elif hits:
        status = "RIVAL_REOPENABLE"
        reason = "OLDER_RIVAL_HAS_NEW_BRIDGE_OR_EVIDENCE"
    else:
        status = "NO_LIVE_RIVAL"
        reason = None
    output = _custom_child_base(CHILD_SCHEMAS["rivals"], CHILD_LEAF_OPERATIONS["rivals"], child_input["target"], child_input, status, reason)
    output.update({"hits": hits, "read_only": True, "source_check": result})
    return _seal_child(output)


def _recency_child(module: Any, child_input: dict[str, Any]) -> dict[str, Any]:
    try:
        result = module.audit(copy.deepcopy(child_input["current"]), copy.deepcopy(child_input["ablated"]))
    except Exception as exc:
        raise CandidateRefusal("REFUSE_RECENCY_CHILD_EXCEPTION") from exc
    status = str(result.get("status"))
    if status not in {"STABLE", "EXPLAINED", "REFUSE"}:
        raise CandidateRefusal("REFUSE_RECENCY_CHILD_STATUS")
    output = _custom_child_base(CHILD_SCHEMAS["recency"], CHILD_LEAF_OPERATIONS["recency"], child_input["target"], child_input, status, result.get("reason"))
    # The contained auditor omits ``flipped`` on refusal; derive that fact
    # from the exact projections so an unexplained flip cannot pass through.
    flipped = bool(result.get("flipped", False) or child_input["current"].get("decision") != child_input["ablated"].get("decision"))
    output.update({"flipped": flipped, "audit": result, "causal_evidence": child_input.get("causal_evidence")})
    return _seal_child(output)


def _verify_custom_child(receipt: Any, child_input: dict[str, Any], schema: str, operation: str) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != schema or receipt.get("operation") != operation:
        return False
    if receipt.get("target") != child_input.get("target") or receipt.get("input_sha256") != digest(child_input):
        return False
    if receipt.get("model_free") is not True or receipt.get("promotion_allowed") is not False or receipt.get("activated") is not False:
        return False
    if receipt.get("writes_performed") is not False or receipt.get("receipt_written") is not False or receipt.get("provider_call_receipt") is not None:
        return False
    expected = receipt.get("receipt_sha256")
    if not _is_digest(expected) or expected != receipt.get("receipt_self_sha256"):
        return False
    unsigned = dict(receipt)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    return digest(unsigned) == expected


def _verify_leaf(config: Mapping[str, Any], child_input: dict[str, Any], receipt: Any) -> bool:
    module = config["module"]
    try:
        if config["definition"]["id"] == "repair_vs_object":
            verifier = getattr(module, "verify_payload_receipt", None)
            return callable(verifier) and bool(verifier(child_input, receipt))
        verifier = getattr(module, "verify_receipt", None)
        if not callable(verifier):
            return False
        return bool(verifier(receipt, child_input, input_sha256=digest(child_input), current_input_sha256=digest(child_input), target=child_input.get("target") or child_input.get("target_id"), target_id=child_input.get("target_id"), operation=child_input.get("operation_id") or child_input.get("operation")))
    except (TypeError, ValueError, KeyError, AttributeError):
        return False


def _contradictions(packet: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[Any]:
    out: list[Any] = copy.deepcopy(packet.get("contradictions", [])) if isinstance(packet.get("contradictions"), list) else []
    for row in rows:
        child = row.get("receipt")
        if isinstance(child, dict) and (child.get("reason") or child.get("status") in {"REFUSE", "RIVAL_LIVE"}):
            out.append({"source": "child", "child_id": row.get("child_id"), "status": child.get("status"), "reason": child.get("reason")})
    return out


def _minority_branches(packet: Mapping[str, Any], artifacts: Mapping[str, Any]) -> list[Any]:
    out: list[Any] = copy.deepcopy(packet.get("minority_branches", [])) if isinstance(packet.get("minority_branches"), list) else []
    for branch in artifacts.get("branches", []):
        if isinstance(branch, dict) and branch.get("kind") in {"parked_branch", "unresolved_discriminator", "failed_candidate"}:
            out.append({"source": "branch_memory", "value": copy.deepcopy(branch)})
    for projection_name in ("current", "ablated"):
        values = artifacts[projection_name].get("minority_branches")
        if isinstance(values, list):
            out.extend({"source": projection_name, "value": copy.deepcopy(item)} for item in values)
    return out


def _disagreements(packet: Mapping[str, Any], rows: list[dict[str, Any]]) -> list[Any]:
    out: list[Any] = copy.deepcopy(packet.get("disagreements", [])) if isinstance(packet.get("disagreements"), list) else []
    groups: dict[str, list[str]] = {}
    for row in rows:
        groups.setdefault(str(row.get("status")), []).append(str(row.get("child_id")))
    if len(groups) > 1:
        out.append({"kind": "child_status_disagreement", "status_groups": groups})
    return out


def _decision_flags(artifacts: Mapping[str, Any], child_receipts: Mapping[str, Any]) -> dict[str, Any]:
    before = artifacts["before"]
    after = artifacts["after"]
    candidate = artifacts["candidate"]
    current = artifacts["current"]
    recency = child_receipts["recency"]
    rival = child_receipts["rivals"]
    object_delta = float(after["object_measure"]) - float(before["object_measure"])
    proxy_delta = float(after["proxy_measure"]) - float(before["proxy_measure"])
    object_regressed = object_delta < 0.0
    object_improved = object_delta > 0.0
    proxy_rose = proxy_delta > 0.0
    # A proxy rise while the protected object is unchanged or worse is the
    # decisive proxy-severance negative.  Do not trust candidate metadata such
    # as ``repair_addressed=proxy`` for this derivation.
    proxy_severance = proxy_rose and object_delta <= 0.0
    repair_regressed = object_regressed and not proxy_severance
    return {
        "owner_amendment_needed": bool(candidate.get("owner_amendment_needed", False) or current.get("owner_amendment_needed", False)),
        "repair_addressed_proxy": proxy_severance,
        "object_delta": object_delta,
        "proxy_delta": proxy_delta,
        "object_regressed": object_regressed,
        "object_improved": object_improved,
        "proxy_rose": proxy_rose,
        "proxy_severance": proxy_severance,
        "repair_regressed": repair_regressed,
        "repair_causality": (
            "proxy_severance"
            if proxy_severance
            else "object_improvement"
            if object_improved
            else "object_regression"
            if object_regressed
            else "no_numeric_change"
        ),
        "split_target": bool(candidate.get("split_target", False) or current.get("split_target", False)),
        "recency_flip": bool(recency.get("flipped", False)),
        "older_rival_dominates": bool(candidate.get("older_rival_dominates", False) or rival.get("status") == "RIVAL_LIVE"),
        "scope_expanded": bool(child_receipts["expansion"].get("status") == "REFUSE" and child_receipts["expansion"].get("reason") == "REFUSE_SCOPE_EXPANSION"),
        "sunk_cost_defense": bool(candidate.get("sunk_cost_defense", False)),
        "stop_better": bool(candidate.get("stop_better", False) or current.get("stop_better", False)),
    }


def _compile_disposition(flags: Mapping[str, bool], *, cancelled: bool = False) -> str:
    for item in PRECEDENCE:
        if item == "cancelled" and cancelled:
            return item
        if item == "request_owner_amendment" and flags.get("owner_amendment_needed"):
            return item
        if item == "revert_repair" and flags.get("repair_regressed"):
            return item
        if item == "split_target" and flags.get("split_target"):
            return item
        if item == "run_discriminator" and flags.get("recency_flip"):
            return item
        if item == "reopen_rival" and flags.get("older_rival_dominates"):
            return item
        if item == "reject_local_optimum" and (
            flags.get("scope_expanded")
            or flags.get("sunk_cost_defense")
            or flags.get("proxy_severance")
        ):
            return item
        if item == "stop_satisfied" and flags.get("stop_better"):
            return item
        if item == "continue_candidate":
            return item
    raise CandidateRefusal("REFUSE_DISPOSITION")


def _output_view(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": receipt.get("status"),
        "parent_cancellation_requested": receipt.get("parent_cancellation_requested"),
        "checkpoint_disposition": receipt.get("checkpoint_disposition"),
        "disposition": receipt.get("disposition"),
        "disposition_reason": receipt.get("disposition_reason"),
        "decision_flags": receipt.get("decision_flags"),
        "child_order": receipt.get("child_order"),
        "children": receipt.get("children"),
        "child_receipts": receipt.get("child_receipts"),
        "contradictions": receipt.get("contradictions"),
        "minority_branches": receipt.get("minority_branches"),
        "disagreements": receipt.get("disagreements"),
        "launched_child_order": receipt.get("launched_child_order"),
        "not_launched_child_ids": receipt.get("not_launched_child_ids"),
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
    target = packet.get("target") if isinstance(packet, dict) else None
    expected_source_set = packet.get("expected_source_set_sha256") if isinstance(packet, dict) else None
    return {
        "schema": SCHEMA,
        "wave_id": WAVE_ID,
        "status": "REFUSE",
        "reason": None,
        "operation": PARENT_OPERATION,
        "candidate_state": "INACTIVE",
        "target": target,
        "input_sha256": _safe_digest(packet),
        "expected_source_set_sha256": expected_source_set if _is_digest(expected_source_set) else None,
        "source_set_sha256": None,
        "definition_sha256": definition_sha,
        "parent_cancellation_requested": packet.get("cancel_requested", False) if isinstance(packet, dict) and isinstance(packet.get("cancel_requested", False), bool) else None,
        "source_hashes": {},
        "artifact_bindings": {},
        "failure_receipt_sha256": None,
        "candidate_receipt_sha256": None,
        "context_epoch_digest": None,
        "branch_memory_snapshot_sha256": None,
        "current_projection_sha256": None,
        "ablated_projection_sha256": None,
        "child_order": list(CHILD_IDS),
        "child_inputs": {},
        "children": [],
        "child_receipts": {},
        "findings": {},
        "contradictions": [],
        "minority_branches": [],
        "disagreements": [],
        "launched_child_order": [],
        "not_launched_child_ids": list(CHILD_IDS),
        "decision_flags": {},
        "checkpoint_disposition": None,
        "disposition": None,
        "disposition_reason": None,
        "disposition_precedence": list(PRECEDENCE),
        "cancellation_state": "NOT_REQUESTED",
        "route_truth": ROUTE_TRUTH,
        "route_truth_label": ROUTE_TRUTH_LABEL,
        "model_free": True,
        "provider_dispatch_proved": False,
        "mmm_preload_applicable": False,
        "provider_receipt_applicable": False,
        "skill_execution_claimed": False,
        "mmm_preload_receipts": [],
        "provider_call_receipt": None,
        "not_applicable": {"mmm_preload_receipts": "model_free_candidate", "provider_call_receipt": "model_free_candidate"},
        "activated": False,
        "promotion_allowed": False,
        "winner_selected": False,
        "voting_performed": False,
        "truth_disposition": None,
        "truth_decided": False,
        "writes_performed": False,
        "receipt_written": False,
        "claim_ceiling": CLAIM_CEILING,
        "output_digest": None,
    }


def _child_row(child_id: str, config: Mapping[str, Any], child_input: dict[str, Any], receipt: dict[str, Any], artifacts: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "child_id": child_id,
        "skill": config["definition"]["skill"],
        "operation": config["definition"]["operation"],
        "leaf_operation": config["leaf_operation"],
        "operation_id": child_input.get("operation_id") or child_input.get("operation"),
        "input_sha256": digest(child_input),
        "source_hashes": {
            "skill": file_digest(config["skill_path"]),
            "script": file_digest(config["source_path"]),
        },
        "bound_artifact_sha256": {key: value["sha256"] for key, value in artifacts["refs"].items()},
        "receipt_sha256": receipt.get("receipt_sha256"),
        "status": receipt.get("status"),
        "terminal_state": "COMPLETED",
        "receipt": copy.deepcopy(receipt),
    }


def run_packet(packet: Any, *, skills_root: Path | None = None) -> dict[str, Any]:
    root: Path | None = None
    definition_path: Path | None = None
    configs: dict[str, Any] = {}
    validator_path: Path | None = None
    receipt: dict[str, Any] | None = None
    expected_source_set_sha256: str | None = None
    try:
        root = _skills_root(skills_root)
        delegated = _delegate_runner(root, "run_packet")
        if delegated is not None:
            return _call_delegated(delegated, "run_packet", packet, skills_root=root)
        # Caller custody is checked before loading the definition or packet
        # artifacts.  The runner never establishes a substitute baseline.
        expected_source_set_sha256 = _expected_source_set(packet)
        source_set = _assert_expected_source_set(root, expected_source_set_sha256)
        definition, definition_path, configs, validator_path = _definition(root)
        normalized, artifacts = _validate_packet(packet, definition, root)
        _assert_expected_source_set(root, expected_source_set_sha256)
        receipt = _base_receipt(normalized, definition_sha=file_digest(definition_path))
        receipt["source_hashes"] = _source_hashes(root, definition_path, configs, validator_path)
        receipt["expected_source_set_sha256"] = expected_source_set_sha256
        receipt["source_set_sha256"] = source_set["sha256"]
        receipt["parent_cancellation_requested"] = bool(normalized.get("cancel_requested", False))
        receipt["artifact_bindings"] = copy.deepcopy(artifacts["refs"])
        receipt["failure_receipt_sha256"] = artifacts["refs"]["failure_receipt"]["sha256"]
        receipt["candidate_receipt_sha256"] = artifacts["refs"]["candidate_receipt"]["sha256"]
        receipt["context_epoch_digest"] = artifacts["epoch"].get("epoch_digest")
        receipt["branch_memory_snapshot_sha256"] = artifacts["refs"]["branch_memory_snapshot"]["sha256"]
        receipt["current_projection_sha256"] = artifacts["refs"]["current_projection"]["sha256"]
        receipt["ablated_projection_sha256"] = artifacts["refs"]["ablated_projection"]["sha256"]
        receipt["child_inputs"] = copy.deepcopy(normalized["child_inputs"])
        if normalized.get("cancel_requested") is True:
            receipt["status"] = "CANCELLED"
            receipt["reason"] = "CANCELLED_PARENT_REQUEST"
            receipt["checkpoint_disposition"] = "cancelled"
            receipt["disposition"] = "cancelled"
            receipt["disposition_reason"] = DISPOSITION_REASONS["cancelled"]
            receipt["cancellation_state"] = "CANCELLED"
            receipt["contradictions"] = _contradictions(normalized, [])
            receipt["minority_branches"] = _minority_branches(normalized, artifacts)
            receipt["disagreements"] = _disagreements(normalized, [])
            receipt["output_digest"] = digest(_output_view(receipt))
            _assert_source_attestation(
                definition_path,
                configs,
                validator_path,
                receipt["source_hashes"],
                expected_source_set_sha256,
            )
            return _seal(receipt)

        child_receipts: dict[str, dict[str, Any]] = {}
        rows: list[dict[str, Any]] = []
        for child_id in CHILD_IDS:
            _assert_source_attestation(
                definition_path,
                configs,
                validator_path,
                receipt["source_hashes"],
                expected_source_set_sha256,
            )
            config = configs[child_id]
            child_input = normalized["child_inputs"][child_id]
            if child_id in {"repair_vs_object", "expansion"}:
                child_receipt = config["function"](copy.deepcopy(child_input))
                if not _verify_leaf(config, child_input, child_receipt):
                    raise CandidateRefusal(f"REFUSE_CHILD_RECEIPT_BINDING:{child_id}")
            elif child_id == "rivals":
                memory_path = _confined(root, child_input["memory_path"], "rival_child_memory")
                child_receipt = _branch_child(config["module"], child_input, artifacts["branches"], memory_path)
                if not _verify_custom_child(child_receipt, child_input, CHILD_SCHEMAS[child_id], CHILD_LEAF_OPERATIONS[child_id]):
                    raise CandidateRefusal("REFUSE_RIVAL_RECEIPT_BINDING")
            else:
                child_receipt = _recency_child(config["module"], child_input)
                if not _verify_custom_child(child_receipt, child_input, CHILD_SCHEMAS[child_id], CHILD_LEAF_OPERATIONS[child_id]):
                    raise CandidateRefusal("REFUSE_RECENCY_RECEIPT_BINDING")
            child_receipts[child_id] = copy.deepcopy(child_receipt)
            row = _child_row(child_id, config, child_input, child_receipt, artifacts)
            rows.append(row)
            # Keep the prefix on the parent object as each child completes.
            # If the next attestation fails, the refusal receipt retains the
            # exact executed prefix rather than erasing it.
            receipt["children"] = copy.deepcopy(rows)
            receipt["child_receipts"] = copy.deepcopy(child_receipts)
            receipt["findings"] = copy.deepcopy(child_receipts)
            receipt["launched_child_order"] = [row["child_id"] for row in rows]
            receipt["not_launched_child_ids"] = list(CHILD_IDS[len(rows):])
            _assert_source_attestation(
                definition_path,
                configs,
                validator_path,
                receipt["source_hashes"],
                expected_source_set_sha256,
            )
        _assert_source_attestation(
            definition_path,
            configs,
            validator_path,
            receipt["source_hashes"],
            expected_source_set_sha256,
        )
        if child_receipts["recency"].get("status") == "REFUSE" and child_receipts["recency"].get("flipped"):
            raise CandidateRefusal("REFUSE_RECENCY_FLIP")
        if child_receipts["repair_vs_object"].get("status") != "CLASSIFIED":
            raise CandidateRefusal("REFUSE_UNVERIFIED_REPAIR_IMPACT")
        expansion_status = child_receipts["expansion"].get("status")
        if expansion_status not in {"INSIDE", "REFUSE"}:
            raise CandidateRefusal("REFUSE_SCOPE_CHILD_STATUS")
        if expansion_status == "REFUSE" and child_receipts["expansion"].get("reason") != "REFUSE_SCOPE_EXPANSION":
            raise CandidateRefusal("REFUSE_SCOPE_CHILD_CHECK")
        _assert_source_attestation(
            definition_path,
            configs,
            validator_path,
            receipt["source_hashes"],
            expected_source_set_sha256,
        )
        flags = _decision_flags(artifacts, child_receipts)
        receipt["children"] = rows
        receipt["child_receipts"] = child_receipts
        receipt["findings"] = copy.deepcopy(child_receipts)
        receipt["launched_child_order"] = list(CHILD_IDS)
        receipt["not_launched_child_ids"] = []
        receipt["decision_flags"] = flags
        receipt["checkpoint_disposition"] = _compile_disposition(flags)
        receipt["disposition"] = receipt["checkpoint_disposition"]
        receipt["disposition_reason"] = DISPOSITION_REASONS[receipt["checkpoint_disposition"]]
        receipt["status"] = "COMPLETE"
        receipt["reason"] = None
        receipt["contradictions"] = _contradictions(normalized, rows)
        receipt["minority_branches"] = _minority_branches(normalized, artifacts)
        receipt["disagreements"] = _disagreements(normalized, rows)
        receipt["output_digest"] = digest(_output_view(receipt))
        _assert_source_attestation(
            definition_path,
            configs,
            validator_path,
            receipt["source_hashes"],
            expected_source_set_sha256,
        )
        return _seal(receipt)
    except CandidateRefusal as exc:
        if receipt is None:
            receipt = _base_receipt(packet, definition_sha=file_digest(definition_path) if definition_path and definition_path.is_file() else None)
        receipt["status"] = "REFUSE"
        receipt["reason"] = str(exc)
        receipt["checkpoint_disposition"] = None
        receipt["disposition"] = None
        receipt["disposition_reason"] = None
        receipt["decision_flags"] = {}
        receipt["cancellation_state"] = "NOT_REQUESTED"
        launched = receipt.get("launched_child_order") or []
        receipt["not_launched_child_ids"] = list(CHILD_IDS[len(launched):])
        receipt["output_digest"] = digest(_output_view(receipt))
        return _seal(receipt)
    except (OSError, TypeError, ValueError, RecursionError) as exc:
        if receipt is None:
            receipt = _base_receipt(packet, definition_sha=file_digest(definition_path) if definition_path and definition_path.is_file() else None)
        receipt["status"] = "REFUSE"
        receipt["reason"] = f"REFUSE_INTERNAL:{type(exc).__name__}"
        receipt["checkpoint_disposition"] = None
        receipt["disposition"] = None
        receipt["disposition_reason"] = None
        receipt["decision_flags"] = {}
        launched = receipt.get("launched_child_order") or []
        receipt["not_launched_child_ids"] = list(CHILD_IDS[len(launched):])
        receipt["output_digest"] = digest(_output_view(receipt))
        return _seal(receipt)


def _verify_source_bindings(receipt: Mapping[str, Any], definition_path: Path, configs: Mapping[str, Any], validator_path: Path) -> bool:
    source_hashes = receipt.get("source_hashes")
    if not isinstance(source_hashes, dict):
        return False
    expected = _source_hashes(definition_path.parent.parent, definition_path, configs, validator_path)
    return source_hashes == expected and receipt.get("definition_sha256") == expected["definition"]


def _verify_child_again(config: Mapping[str, Any], child_input: dict[str, Any], receipt: dict[str, Any], root: Path) -> bool:
    child_id = config["definition"]["id"]
    if child_id == "rivals":
        try:
            memory_path = _confined(root, child_input["memory_path"], "rival_child_memory")
            branches = _read_jsonl(memory_path)
            expected = _branch_child(config["module"], child_input, branches, memory_path)
        except (CandidateRefusal, OSError, ValueError, TypeError):
            return False
        return expected == receipt and _verify_custom_child(receipt, child_input, CHILD_SCHEMAS[child_id], CHILD_LEAF_OPERATIONS[child_id])
    if child_id == "recency":
        try:
            expected = _recency_child(config["module"], child_input)
        except (CandidateRefusal, OSError, ValueError, TypeError):
            return False
        return expected == receipt and _verify_custom_child(receipt, child_input, CHILD_SCHEMAS[child_id], CHILD_LEAF_OPERATIONS[child_id])
    return _verify_leaf(config, child_input, receipt)


def _integrity_shape(receipt: Any, root: Path) -> bool:
    """Check receipt custody only; never derive a semantic disposition."""

    if not isinstance(receipt, dict) or set(receipt) != PARENT_RECEIPT_KEYS:
        return False
    try:
        _, definition_path, configs, validator_path = _definition(root)
        if receipt.get("schema") != SCHEMA or receipt.get("wave_id") != WAVE_ID or receipt.get("operation") != PARENT_OPERATION or receipt.get("claim_ceiling") != CLAIM_CEILING:
            return False
        if not isinstance(receipt.get("target"), str) or not receipt["target"].strip() or receipt.get("child_order") != list(CHILD_IDS):
            return False
        if not isinstance(receipt.get("parent_cancellation_requested"), bool):
            return False
        current_source_set = _source_set(root)
        receipt_artifacts = receipt.get("artifact_bindings")
        if not isinstance(receipt_artifacts, dict) or set(receipt_artifacts) != {
            "before_repair", "after_repair", "failure_receipt", "candidate_receipt",
            "context_epoch", "branch_memory_snapshot", "current_projection", "ablated_projection",
        }:
            return False
        artifact_values: dict[str, Any] = {}
        for label, ref in receipt_artifacts.items():
            artifact_values[label], observed_ref = _read_artifact(root, ref, label)
            if observed_ref != ref:
                return False
        if receipt.get("failure_receipt_sha256") != receipt_artifacts["failure_receipt"]["sha256"] or receipt.get("candidate_receipt_sha256") != receipt_artifacts["candidate_receipt"]["sha256"]:
            return False
        if receipt.get("context_epoch_digest") != artifact_values["context_epoch"].get("epoch_digest"):
            return False
        for field, label in (
            ("branch_memory_snapshot_sha256", "branch_memory_snapshot"),
            ("current_projection_sha256", "current_projection"),
            ("ablated_projection_sha256", "ablated_projection"),
        ):
            if receipt.get(field) != receipt_artifacts[label]["sha256"]:
                return False
        for label in ("before_repair", "after_repair", "failure_receipt", "candidate_receipt", "current_projection", "ablated_projection"):
            value = artifact_values[label]
            if isinstance(value, dict) and value.get("target") is not None and value.get("target") != receipt.get("target"):
                return False
        if not _is_digest(receipt.get("expected_source_set_sha256")):
            return False
        if (
            receipt.get("expected_source_set_sha256") != current_source_set["sha256"]
            or receipt.get("source_set_sha256") != current_source_set["sha256"]
            or receipt.get("source_set_sha256") != _source_set_sha256(receipt.get("source_hashes", {}))
            or receipt.get("source_set_sha256") != receipt.get("expected_source_set_sha256")
        ):
            return False
        if not _verify_source_bindings(receipt, definition_path, configs, validator_path):
            return False
        if receipt.get("candidate_state") != "INACTIVE":
            return False
        if receipt.get("route_truth") != ROUTE_TRUTH or receipt.get("route_truth_label") != ROUTE_TRUTH_LABEL:
            return False
        for key, expected in (
            ("model_free", True), ("provider_dispatch_proved", False), ("mmm_preload_applicable", False),
            ("provider_receipt_applicable", False), ("skill_execution_claimed", False), ("activated", False),
            ("promotion_allowed", False), ("winner_selected", False), ("voting_performed", False),
            ("truth_decided", False), ("writes_performed", False), ("receipt_written", False),
        ):
            if receipt.get(key) is not expected:
                return False
        if receipt.get("truth_disposition") is not None or receipt.get("provider_call_receipt") is not None or receipt.get("mmm_preload_receipts") != []:
            return False
        if receipt.get("not_applicable") != {
            "mmm_preload_receipts": "model_free_candidate",
            "provider_call_receipt": "model_free_candidate",
        }:
            return False
        if receipt.get("disposition_precedence") != list(PRECEDENCE):
            return False
        decision_flags = receipt.get("decision_flags")
        if not isinstance(decision_flags, dict) or set(decision_flags) - DECISION_FLAG_KEYS:
            return False
        unsigned = copy.deepcopy(receipt)
        expected_self = unsigned.pop("receipt_sha256", None)
        expected_self_2 = unsigned.pop("receipt_self_sha256", None)
        if not _is_digest(expected_self) or expected_self != expected_self_2 or digest(unsigned) != expected_self:
            return False
        child_inputs = receipt.get("child_inputs")
        if not isinstance(child_inputs, dict) or set(child_inputs) != set(CHILD_IDS):
            return False
        child_input_keys = {
            "repair_vs_object": {"schema", "operation", "target", "claim", "evidence"},
            "expansion": {"target_id", "operation_id", "authorized", "used"},
            "rivals": {"schema", "operation", "target", "memory_path", "memory_sha256", "candidate_id", "new_bridge", "new_evidence"},
            "recency": {"schema", "operation", "target", "current", "ablated", "causal_evidence"},
        }
        for child_id in CHILD_IDS:
            if not isinstance(child_inputs[child_id], dict) or set(child_inputs[child_id]) != child_input_keys[child_id]:
                return False
        rows = receipt.get("children")
        child_receipts = receipt.get("child_receipts")
        if not isinstance(rows, list) or not isinstance(child_receipts, dict):
            return False
        row_keys = {
            "child_id", "skill", "operation", "leaf_operation", "operation_id", "input_sha256",
            "source_hashes", "bound_artifact_sha256", "receipt_sha256", "status", "terminal_state", "receipt",
        }
        ids: list[str] = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != row_keys:
                return False
            child_id = row.get("child_id")
            if child_id not in CHILD_IDS or child_id in ids:
                return False
            ids.append(child_id)
            if not isinstance(row.get("source_hashes"), dict) or set(row["source_hashes"]) != {"skill", "script"} or not all(_is_digest(row["source_hashes"].get(key)) for key in ("skill", "script")):
                return False
            bound_artifacts = row.get("bound_artifact_sha256")
            if not isinstance(bound_artifacts, dict) or set(bound_artifacts) != set(receipt_artifacts) or not all(_is_digest(value) for value in bound_artifacts.values()):
                return False
            if bound_artifacts != {key: value["sha256"] for key, value in receipt_artifacts.items()}:
                return False
            child_receipt = row.get("receipt")
            if not isinstance(child_receipt, dict) or set(child_receipt) - CHILD_RECEIPT_KEYS[child_id]:
                return False
            if child_id == "rivals":
                source_check = child_receipt.get("source_check")
                if not isinstance(source_check, dict) or set(source_check) - {"schema", "status", "reason", "hits", "promotion_allowed"}:
                    return False
            if child_id == "recency":
                audit = child_receipt.get("audit")
                if not isinstance(audit, dict) or set(audit) - {"schema", "status", "reason", "flipped", "promotion_allowed"}:
                    return False
            expected_child = child_receipts.get(child_id)
            if expected_child != child_receipt:
                return False
            if not _is_digest(child_receipt.get("receipt_sha256")) or child_receipt.get("receipt_sha256") != child_receipt.get("receipt_self_sha256"):
                return False
            child_unsigned = dict(child_receipt)
            child_unsigned.pop("receipt_sha256", None)
            child_unsigned.pop("receipt_self_sha256", None)
            if digest(child_unsigned) != child_receipt.get("receipt_sha256"):
                return False
        if set(child_receipts) != set(ids):
            return False
        return True
    except (CandidateRefusal, OSError, ValueError, TypeError, KeyError):
        return False


def verify_integrity(receipt: Any, *, skills_root: Path | None = None) -> dict[str, Any]:
    """Return custody integrity only; it makes no status/disposition claim."""

    try:
        root = _skills_root(skills_root)
        delegated = _delegate_runner(root, "verify_integrity")
        if delegated is not None:
            return _call_delegated(delegated, "verify_integrity", receipt, skills_root=root)
        valid = _integrity_shape(receipt, root)
    except (CandidateRefusal, OSError, ValueError, TypeError, KeyError):
        valid = False
    return {
        "schema": "constraintbox.strategy-checkpoint-wave-integrity.v1",
        "integrity_valid": bool(valid),
        "semantic_verified": False,
        "decision_claim": None,
        "claim_ceiling": "Receipt custody integrity only; no status or checkpoint disposition claim.",
    }


def verify_receipt(receipt: Any, packet: Any | None = None, *, skills_root: Path | None = None) -> bool:
    # Semantic verification requires the exact caller packet.  A receipt alone
    # can only be checked through verify_integrity(), never treated as a
    # semantic routing result.
    if packet is None:
        return False
    if not isinstance(receipt, dict) or set(receipt) != PARENT_RECEIPT_KEYS or receipt.get("schema") != SCHEMA or receipt.get("wave_id") != WAVE_ID:
        return False
    try:
        root = _skills_root(skills_root)
        delegated = _delegate_runner(root, "verify_receipt")
        if delegated is not None:
            return bool(_call_delegated(delegated, "verify_receipt", receipt, packet, skills_root=root))
        definition, definition_path, configs, validator_path = _definition(root)
    except (CandidateRefusal, OSError, ValueError, TypeError):
        return False
    if receipt.get("route_truth") != ROUTE_TRUTH or receipt.get("route_truth_label") != ROUTE_TRUTH_LABEL:
        return False
    for key, expected in (("model_free", True), ("provider_dispatch_proved", False), ("mmm_preload_applicable", False), ("provider_receipt_applicable", False), ("skill_execution_claimed", False), ("activated", False), ("promotion_allowed", False), ("winner_selected", False), ("voting_performed", False), ("truth_decided", False), ("writes_performed", False), ("receipt_written", False)):
        if receipt.get(key) is not expected:
            return False
    if receipt.get("truth_disposition") is not None:
        return False
    if receipt.get("candidate_state") != "INACTIVE":
        return False
    if receipt.get("not_applicable") != {
        "mmm_preload_receipts": "model_free_candidate",
        "provider_call_receipt": "model_free_candidate",
    }:
        return False
    if receipt.get("provider_call_receipt") is not None or receipt.get("mmm_preload_receipts") != []:
        return False
    if receipt.get("claim_ceiling") != CLAIM_CEILING or receipt.get("operation") != PARENT_OPERATION or receipt.get("child_order") != list(CHILD_IDS):
        return False
    if receipt.get("disposition_precedence") != list(PRECEDENCE):
        return False
    if not isinstance(receipt.get("decision_flags"), dict) or set(receipt["decision_flags"]) - DECISION_FLAG_KEYS:
        return False
    if not _verify_source_bindings(receipt, definition_path, configs, validator_path):
        return False
    try:
        current_source_set = _source_set(root)
    except (CandidateRefusal, OSError, ValueError, TypeError):
        return False
    if (
        receipt.get("expected_source_set_sha256") != current_source_set["sha256"]
        or receipt.get("source_set_sha256") != current_source_set["sha256"]
        or receipt.get("source_set_sha256") != _source_set_sha256(receipt.get("source_hashes", {}))
        or receipt.get("source_set_sha256") != receipt.get("expected_source_set_sha256")
    ):
        return False
    receipt_artifacts = receipt.get("artifact_bindings")
    if not isinstance(receipt_artifacts, dict) or set(receipt_artifacts) != {
        "before_repair", "after_repair", "failure_receipt", "candidate_receipt",
        "context_epoch", "branch_memory_snapshot", "current_projection", "ablated_projection",
    }:
        return False
    try:
        for label, ref in receipt_artifacts.items():
            _, observed_ref = _read_artifact(root, ref, label)
            if observed_ref != ref:
                return False
    except (CandidateRefusal, OSError, ValueError, TypeError):
        return False
    if receipt.get("disposition_precedence") != list(PRECEDENCE):
        return False
    unsigned = copy.deepcopy(receipt)
    expected_self = unsigned.pop("receipt_sha256", None)
    expected_self_2 = unsigned.pop("receipt_self_sha256", None)
    if not _is_digest(expected_self) or expected_self != expected_self_2 or digest(unsigned) != expected_self:
        return False
    normalized: dict[str, Any] | None = None
    artifacts: dict[str, Any] | None = None
    if packet is not None:
        try:
            normalized, artifacts = _validate_packet(packet, definition, root)
        except (CandidateRefusal, OSError, ValueError, TypeError):
            return False
        if receipt.get("input_sha256") != digest(normalized) or receipt.get("target") != normalized.get("target") or receipt.get("child_inputs") != normalized.get("child_inputs"):
            return False
        if receipt.get("parent_cancellation_requested") != bool(normalized.get("cancel_requested", False)):
            return False
        if receipt.get("expected_source_set_sha256") != normalized.get("expected_source_set_sha256"):
            return False
        if receipt.get("artifact_bindings") != artifacts.get("refs"):
            return False
        if receipt.get("failure_receipt_sha256") != artifacts["refs"]["failure_receipt"]["sha256"] or receipt.get("candidate_receipt_sha256") != artifacts["refs"]["candidate_receipt"]["sha256"]:
            return False
        if receipt.get("context_epoch_digest") != artifacts["epoch"].get("epoch_digest"):
            return False
        if receipt.get("branch_memory_snapshot_sha256") != artifacts["refs"]["branch_memory_snapshot"]["sha256"]:
            return False
        if receipt.get("current_projection_sha256") != artifacts["refs"]["current_projection"]["sha256"]:
            return False
        if receipt.get("ablated_projection_sha256") != artifacts["refs"]["ablated_projection"]["sha256"]:
            return False
        # The packet is the authority for terminal status, child prefix, and
        # causal disposition.  Structural self-digests alone must not let a
        # caller forge REFUSE or CANCELLED around a valid packet.
        replayed = run_packet(packet, skills_root=root)
        if receipt != replayed:
            return False
    if not isinstance(receipt.get("children"), list) or not isinstance(receipt.get("child_receipts"), dict) or not isinstance(receipt.get("child_inputs"), dict):
        return False
    rows = receipt["children"]
    ids = [row.get("child_id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(rows) or len(ids) != len(set(ids)) or ids != list(CHILD_IDS[: len(ids)]):
        return False
    if set(receipt["child_receipts"]) != set(ids):
        return False
    status = receipt.get("status")
    if receipt.get("checkpoint_disposition") is not None and receipt.get("checkpoint_disposition") not in DISPOSITION_REASONS:
        return False
    if status == "COMPLETE":
        if receipt.get("parent_cancellation_requested") is not False:
            return False
        if ids != list(CHILD_IDS) or receipt.get("launched_child_order") != list(CHILD_IDS) or receipt.get("not_launched_child_ids") != [] or receipt.get("cancellation_state") != "NOT_REQUESTED":
            return False
        if not isinstance(receipt.get("checkpoint_disposition"), str) or receipt["checkpoint_disposition"] not in DISPOSITIONS[:-1]:
            return False
        if receipt.get("disposition") != receipt.get("checkpoint_disposition") or receipt.get("disposition_reason") != DISPOSITION_REASONS[receipt["checkpoint_disposition"]]:
            return False
    elif status == "CANCELLED":
        if packet is None:
            return False
        if normalized is None or normalized.get("cancel_requested") is not True:
            return False
        if receipt.get("parent_cancellation_requested") is not True:
            return False
        if receipt.get("checkpoint_disposition") != "cancelled" or receipt.get("disposition") != "cancelled" or receipt.get("disposition_reason") != DISPOSITION_REASONS["cancelled"] or receipt.get("cancellation_state") != "CANCELLED":
            return False
        if ids or receipt.get("children") != [] or receipt.get("child_receipts") != {} or receipt.get("findings") != {} or receipt.get("launched_child_order") != [] or receipt.get("not_launched_child_ids") != list(CHILD_IDS):
            return False
    elif status == "REFUSE":
        if receipt.get("checkpoint_disposition") is not None or receipt.get("disposition") is not None or receipt.get("cancellation_state") != "NOT_REQUESTED":
            return False
        if ids != list(CHILD_IDS[: len(ids)]) or receipt.get("launched_child_order") != ids or receipt.get("not_launched_child_ids") != list(CHILD_IDS[len(ids):]):
            return False
        if not isinstance(receipt.get("reason"), str) or not receipt.get("reason"):
            return False
    else:
        return False
    for row in rows:
        if not isinstance(row, dict):
            return False
        child_id = row.get("child_id")
        if child_id not in configs or child_id not in receipt["child_inputs"]:
            return False
        child_input = receipt["child_inputs"][child_id]
        child_receipt = row.get("receipt")
        if not isinstance(child_receipt, dict) or receipt["child_receipts"].get(child_id) != child_receipt:
            return False
        if row.get("input_sha256") != digest(child_input) or row.get("receipt_sha256") != child_receipt.get("receipt_sha256"):
            return False
        if row.get("operation_id") != child_input.get("operation_id") and row.get("operation_id") != child_input.get("operation"):
            return False
        if row.get("terminal_state") != "COMPLETED":
            return False
        expected_bound = {key: value["sha256"] for key, value in (artifacts or {}).get("refs", {}).items()} if artifacts is not None else {key: value["sha256"] for key, value in receipt_artifacts.items()}
        if row.get("bound_artifact_sha256") != expected_bound:
            return False
        if row.get("operation") != configs[child_id]["definition"].get("operation") or row.get("leaf_operation") != configs[child_id]["leaf_operation"]:
            return False
        if row.get("source_hashes") != {
            "skill": file_digest(configs[child_id]["skill_path"]),
            "script": file_digest(configs[child_id]["source_path"]),
        }:
            return False
        if not _verify_child_again(configs[child_id], child_input, child_receipt, root):
            return False
    if receipt.get("findings") != {str(row["child_id"]): row["receipt"] for row in rows}:
        return False
    if status == "COMPLETE":
        flags = receipt.get("decision_flags")
        if not isinstance(flags, dict) or receipt.get("checkpoint_disposition") != _compile_disposition(flags):
            return False
        if packet is not None:
            if receipt.get("contradictions") != _contradictions(normalized or {}, rows) or receipt.get("minority_branches") != _minority_branches(normalized or {}, artifacts or {}):
                return False
            if receipt.get("disagreements") != _disagreements(normalized or {}, rows):
                return False
    if receipt.get("output_digest") != digest(_output_view(receipt)):
        return False
    return True


def run(packet: Any, *, skills_root: Path | None = None) -> dict[str, Any]:
    """Compatibility alias for contained callers and focused tests."""

    return run_packet(packet, skills_root=skills_root)


def _prewrite_attest(receipt: Mapping[str, Any], *, skills_root: Path | None = None) -> None:
    """Re-attest the caller-bound source set immediately before CLI output."""

    root = _skills_root(skills_root)
    delegated = _delegate_runner(root, "_prewrite_attest")
    if delegated is not None:
        _call_delegated(delegated, "_prewrite_attest", receipt, skills_root=root)
        return
    _, definition_path, configs, validator_path = _definition(root)
    expected = receipt.get("expected_source_set_sha256")
    pinned = receipt.get("source_hashes")
    if not _is_digest(expected) or not isinstance(pinned, dict):
        raise CandidateRefusal("REFUSE_PREWRITE_SOURCE_BINDING")
    _assert_source_attestation(definition_path, configs, validator_path, pinned, str(expected))


def _prewrite_refusal(receipt: Mapping[str, Any], reason: str) -> dict[str, Any]:
    refused = copy.deepcopy(dict(receipt))
    refused["status"] = "REFUSE"
    refused["reason"] = reason
    refused["checkpoint_disposition"] = None
    refused["disposition"] = None
    refused["disposition_reason"] = None
    refused["decision_flags"] = {}
    refused["cancellation_state"] = "NOT_REQUESTED"
    launched = refused.get("launched_child_order") or []
    refused["not_launched_child_ids"] = list(CHILD_IDS[len(launched):])
    refused["output_digest"] = digest(_output_view(refused))
    return _seal(refused)


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
            result = _read_json(args.verify)
            ok = verify_receipt(result, packet, skills_root=args.root)
            print(json.dumps({"status": "VERIFIED" if ok else "REFUSE_RECEIPT"}, sort_keys=True))
            return 0 if ok else 2
        result = run_packet(packet, skills_root=args.root)
        if args.out is not None:
            try:
                _prewrite_attest(result, skills_root=args.root)
            except CandidateRefusal as exc:
                # Preserve an already-normalized delegated refusal.  A late
                # prewrite refusal must not overwrite the original custody
                # code with a second module's class/detail.
                if result.get("status") != "REFUSE":
                    result = _prewrite_refusal(result, str(exc))
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": result.get("status"), "reason": result.get("reason"), "checkpoint_disposition": result.get("checkpoint_disposition")}, sort_keys=True))
        return 0 if result.get("status") == "COMPLETE" else 2
    except (CandidateRefusal, OSError, UnicodeError, json.JSONDecodeError, DuplicateJSONKey) as exc:
        print(json.dumps({"status": "REFUSE", "reason": f"REFUSE_CLI:{type(exc).__name__}"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
