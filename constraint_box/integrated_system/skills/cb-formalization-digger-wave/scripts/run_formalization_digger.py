#!/usr/bin/env python3
"""Run the source-bound, inactive formalization/digger candidate.

This runner consumes the repository's real v2 epoch verifier and the real
capability/probe-map producer receipt.  The four child rows are fixture-backed
proposal objects; no provider or authority operation is called here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping


SCHEMA = "constraintbox.formalization-digger-receipt.v2"
WAVE_ID = "cb-formalization-digger-wave-v1"
BUNDLE_SCHEMA = "constraintbox.formalization-digger-proposal-bundle.v2"
PROPOSAL_SCHEMA = "constraintbox.formalization-digger-proposal.v2"
FRONTIER_SCHEMA = "constraintbox.formalization-digger-frontier.v2"
EPOCH_SCHEMA = "constraintbox.context-epoch.v2"
CAPABILITY_RECEIPT_SCHEMA = "constraintbox.capability-probe-map-receipt.v1"
CAPABILITY_MAP_SCHEMA = "constraintbox.capability-map.v1"
CAPABILITY_WAVE_ID = "cb-capability-probe-map-wave-v1"
CAPABILITY_CANDIDATE_STATE = "NEW_CANDIDATE"
CAPABILITY_STATUS = "HOLD"
CLAIM_CEILING = (
    "Source-bound proposal validation and non-voting frontier compilation only; "
    "no observations, truth decision, gate activation, basin claim, provider "
    "route, or promotion."
)
CHILD_IDS = (
    "axiom_digger",
    "constraint_digger",
    "gate_digger",
    "basin_digger",
)
CHILD_KINDS = {
    "axiom_digger": "assumptions_and_non_objectives",
    "constraint_digger": "finite_candidate_predicates",
    "gate_digger": "candidate_gate_obligations",
    "basin_digger": "probe_relative_interpretations",
}
CHILD_COMMON_KEYS = {
    "schema", "child_id", "proposal_kind", "input_epoch_digest",
    "capability_receipt_sha256", "proposal_only", "observations", "decisions",
    "activation_requested", "source_refs", "claim_ceiling",
}
CHILD_KEYS = {
    "axiom_digger": CHILD_COMMON_KEYS | {"assumptions", "non_objectives"},
    "constraint_digger": CHILD_COMMON_KEYS | {"predicates"},
    "gate_digger": CHILD_COMMON_KEYS | {"obligations", "negatives"},
    "basin_digger": CHILD_COMMON_KEYS | {"interpretations"},
}
BUNDLE_KEYS = {
    "schema", "bundle_id", "epoch_digest", "capability_receipt_sha256",
    "children", "proposal_only", "promotion_allowed", "proposal_bundle_digest",
    "claim_ceiling",
}
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

_CANDIDATE_DIR = Path(__file__).resolve().parents[1]
_DEFAULT_CONTEXT = "constraint_box/integrated_system/skills/cb-formalization-digger-wave/fixtures/context_epoch_v2.json"
_DEFAULT_CAPABILITY = "constraint_box/integrated_system/skills/cb-formalization-digger-wave/fixtures/capability_probe_map_v1.json"
_DEFAULT_PROPOSALS = "constraint_box/integrated_system/skills/cb-formalization-digger-wave/fixtures/digger_proposals_v2.json"
EPOCH_VERIFIER = "constraint_box/integrated_system/scripts/seal_context_epoch.py"
EPOCH_SOURCE = "constraint_box/integrated_system/state/epochs/epoch-00000002.json"
CAPABILITY_PRODUCER = "constraint_box/integrated_system/skills/cb-capability-probe-map-wave/scripts/run_probe_map.py"
CAPABILITY_DEFINITION = "constraint_box/integrated_system/skills/cb-capability-probe-map-wave/wave.json"
CAPABILITY_REGISTRY = "constraint_box/integrated_system/skills/cb-capability-probe-map-wave/registry.json"
CAPABILITY_INTERPRETER = "constraint_box/.venv/bin/python"
_SOURCE_LOCATION_VARIANTS = {
    "constraint_box/src/constraintbox/constraint_path_mass.py": "constraint_box/constraint_path_mass.py",
    "constraint_box/integrated_system/runtime/controller_src/constraintbox/constraint_path_mass.py": "constraint_box/constraint_path_mass.py",
}
_SOURCE_LOCATION_ALTERNATE = {
    left: right
    for left, right in (
        ("constraint_box/src/constraintbox/constraint_path_mass.py", "constraint_box/integrated_system/runtime/controller_src/constraintbox/constraint_path_mass.py"),
        ("constraint_box/integrated_system/runtime/controller_src/constraintbox/constraint_path_mass.py", "constraint_box/src/constraintbox/constraint_path_mass.py"),
    )
}


class CandidateRefusal(ValueError):
    """A root, path, source, schema, or receipt boundary is invalid."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def digest(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def file_digest(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CandidateRefusal(f"REFUSE_JSON_OBJECT:{path}")
    return value


def _capability_projection(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return the producer receipt projection used for currentness binding.

    The producer's receipt and result digests cover the complete receipt.  The
    formalization candidate also records a semantic projection so the input is
    bound to a freshly reproduced producer result rather than accepted merely
    because a caller recomputed the producer's self-digest. Runtime identity
    and process evidence are intentionally excluded from this projection:
    those fields contain extracted-root paths and interpreter-specific details.
    Source, capability-map, child status, and control fields remain bound.
    """

    volatile = {
        "receipt_sha256", "result_sha256", "output_digest", "runtime_bindings",
        "tool_api_evidence", "environment_projection", "subprocess_environment",
        "process", "invocation", "runtime", "interpreter", "runtime_label",
        "runtime_sha256", "python_executable", "sys_prefix", "sys_base_prefix",
    }

    def project(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {
                str(key): project(child)
                for key, child in sorted(item.items(), key=lambda pair: str(pair[0]))
                if key not in volatile
            }
        if isinstance(item, list):
            return [project(child) for child in item]
        if isinstance(item, str):
            return _SOURCE_LOCATION_VARIANTS.get(item, item)
        return copy.deepcopy(item)

    projected = project(value)
    if not isinstance(projected, dict):
        raise CandidateRefusal("REFUSE_CAPABILITY_PROJECTION_OBJECT")
    return projected


def _logical_source_id(relative: str) -> str:
    """Collapse only the two shipped path-mass source locations."""

    return _SOURCE_LOCATION_VARIANTS.get(relative, relative)


def _capability_expectation(value: Mapping[str, Any], label: str) -> None:
    """Require the exact inactive producer identity expected by this wave."""

    if value.get("schema") != CAPABILITY_RECEIPT_SCHEMA:
        raise CandidateRefusal(f"REFUSE_CAPABILITY_{label}_SCHEMA")
    if value.get("wave_id") != CAPABILITY_WAVE_ID:
        raise CandidateRefusal(f"REFUSE_CAPABILITY_{label}_WAVE_ID")
    if value.get("candidate_state") != CAPABILITY_CANDIDATE_STATE:
        raise CandidateRefusal(f"REFUSE_CAPABILITY_{label}_CANDIDATE_STATE")
    if value.get("status") != CAPABILITY_STATUS:
        raise CandidateRefusal(f"REFUSE_CAPABILITY_{label}_STATUS")
    if value.get("activated") is not False or value.get("promotion_allowed") is not False:
        raise CandidateRefusal(f"REFUSE_CAPABILITY_{label}_AUTHORITY_FLAGS")


def _declared_capability_interpreter(root: Path) -> tuple[Path, Path]:
    """Resolve the repository-declared Light interpreter, ignoring ambient env."""

    declared = root / CAPABILITY_INTERPRETER
    if not declared.is_file():
        raise CandidateRefusal("REFUSE_CAPABILITY_INTERPRETER_MISSING")
    try:
        resolved = declared.resolve(strict=True)
    except OSError as exc:
        raise CandidateRefusal("REFUSE_CAPABILITY_INTERPRETER_RESOLVE") from exc
    if not resolved.is_file():
        raise CandidateRefusal("REFUSE_CAPABILITY_INTERPRETER_NOT_FILE")
    return declared, resolved


def _capability_reproduction(
    producer: Any,
    root: Path,
    capability: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Re-run the model-free producer and bind both receipt and projection."""

    declared_interpreter, resolved_interpreter = _declared_capability_interpreter(root)
    prior_executable = sys.executable
    try:
        # The producer uses sys.executable for its controller subprocesses.
        # Bind that choice to the repository's declared Light interpreter for
        # this finite fixture; CB_* environment variables cannot redirect it.
        sys.executable = str(declared_interpreter)
        fresh = producer.run_candidate(root, None)
    except Exception as exc:  # fail closed at the producer custody boundary
        raise CandidateRefusal(f"REFUSE_CAPABILITY_REPRODUCTION:{type(exc).__name__}") from exc
    finally:
        sys.executable = prior_executable
    if not isinstance(fresh, dict) or not producer.verify_receipt(fresh):
        raise CandidateRefusal("REFUSE_CAPABILITY_REPRODUCTION_RECEIPT")
    _capability_expectation(capability, "INPUT")
    _capability_expectation(fresh, "FRESH")
    input_projection = _capability_projection(capability)
    fresh_projection = _capability_projection(fresh)
    if input_projection != fresh_projection:
        raise CandidateRefusal("REFUSE_CAPABILITY_PROJECTION_DRIFT")
    summary = {
        "producer": "run_candidate(root, jax_interpreter=None)",
        "declared_interpreter": CAPABILITY_INTERPRETER,
        "declared_interpreter_sha256": file_digest(resolved_interpreter),
        "expected_wave_id": CAPABILITY_WAVE_ID,
        "expected_candidate_state": CAPABILITY_CANDIDATE_STATE,
        "expected_status": CAPABILITY_STATUS,
        "input_receipt_sha256": capability.get("receipt_sha256"),
        "fresh_receipt_sha256": fresh.get("receipt_sha256"),
        "input_result_sha256": capability.get("result_sha256"),
        "fresh_result_sha256": fresh.get("result_sha256"),
        "input_projection_sha256": digest(input_projection),
        "fresh_projection_sha256": digest(fresh_projection),
        "projection_match": True,
        "receipt_match": capability == fresh,
    }
    return summary, fresh


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _is_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(DIGEST_RE.fullmatch(value))


def _root(root: Path) -> Path:
    root = Path(root).expanduser()
    if root.is_symlink():
        raise CandidateRefusal("REFUSE_ROOT_SYMLINK")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise CandidateRefusal(f"REFUSE_ROOT:{root}:{exc}") from exc
    if not resolved.is_dir():
        raise CandidateRefusal("REFUSE_ROOT_NOT_DIRECTORY")
    return resolved


def _confined(root: Path, value: str | Path, label: str, *, must_exist: bool) -> Path:
    """Resolve a path while refusing escapes, `..`, and every symlink component."""

    raw = value.as_posix() if isinstance(value, Path) else str(value)
    if not raw or "\x00" in raw or "\\" in raw:
        raise CandidateRefusal(f"REFUSE_INVALID_PATH:{label}")
    candidate = Path(raw)
    # Check lexical traversal before any absolute-path normalization.  A path
    # such as /root/dir/../file may resolve inside root, but its declaration is
    # still an escape attempt and must be refused.
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
            raise CandidateRefusal(f"REFUSE_SYMLINK_PATH:{label}:{relative.as_posix()}")
    try:
        resolved = target.resolve(strict=must_exist)
    except OSError as exc:
        raise CandidateRefusal(f"REFUSE_PATH_RESOLVE:{label}:{exc}") from exc
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise CandidateRefusal(f"REFUSE_PATH_ESCAPE:{label}") from exc
    if must_exist and (not resolved.is_file() or resolved.is_symlink()):
        raise CandidateRefusal(f"REFUSE_FILE_MISSING:{label}")
    if not must_exist and target.exists():
        raise CandidateRefusal(f"REFUSE_OUTPUT_EXISTS:{label}")
    if not must_exist and not target.parent.is_dir():
        raise CandidateRefusal(f"REFUSE_OUTPUT_PARENT:{label}")
    return resolved


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root).as_posix()
    except ValueError as exc:
        raise CandidateRefusal(f"REFUSE_PATH_ESCAPE:{path}") from exc


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise CandidateRefusal(f"REFUSE_VERIFIER_LOAD:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bound_source_map(root: Path, epoch: dict[str, Any], capability: dict[str, Any]) -> dict[str, str]:
    """Return root-relative source rows allowed by the two input receipts."""

    allowed: dict[str, str] = {}
    bound = epoch.get("bound_files")
    if not isinstance(bound, Mapping):
        raise CandidateRefusal("REFUSE_EPOCH_BOUND_FILES")
    for row in bound.values():
        rows = row.values() if isinstance(row, Mapping) and "path" not in row else (row,)
        for nested in rows:
            if not isinstance(nested, Mapping) or "path" not in nested or "sha256" not in nested:
                continue
            path = _confined(root, str(nested["path"]), "epoch_bound_file", must_exist=True)
            observed = file_digest(path)
            if observed != nested["sha256"]:
                raise CandidateRefusal("REFUSE_EPOCH_BOUND_FILE_SHA256")
            allowed[_logical_source_id(_relative(root, path))] = observed
    binding = capability.get("capability_binding")
    if not isinstance(binding, Mapping):
        raise CandidateRefusal("REFUSE_CAPABILITY_BINDING")
    for capability_row in binding.get("capabilities", []):
        if not isinstance(capability_row, Mapping):
            continue
        for key in ("source", "wrapper"):
            row = capability_row.get(key)
            if not isinstance(row, Mapping) or "path" not in row or "sha256" not in row:
                continue
            path = _confined(root, str(row["path"]), "capability_source", must_exist=True)
            observed = file_digest(path)
            if observed != row["sha256"]:
                raise CandidateRefusal("REFUSE_CAPABILITY_SOURCE_SHA256")
            allowed[_logical_source_id(_relative(root, path))] = observed
    row = binding.get("registry")
    if isinstance(row, Mapping) and "path" in row and "sha256" in row:
        path = _confined(root, str(row["path"]), "capability_registry", must_exist=True)
        observed = file_digest(path)
        if observed != row["sha256"]:
            raise CandidateRefusal("REFUSE_CAPABILITY_REGISTRY_SHA256")
        allowed[_logical_source_id(_relative(root, path))] = observed
    return allowed


def _prepare_inputs(root: Path, context_path: str | Path, capability_path: str | Path, proposals_path: str | Path) -> dict[str, Any]:
    root_path = _root(root)
    epoch_file = _confined(root_path, context_path, "context_epoch", must_exist=True)
    capability_file = _confined(root_path, capability_path, "capability_receipt", must_exist=True)
    proposals_file = _confined(root_path, proposals_path, "proposal_bundle", must_exist=True)
    epoch_verifier = _confined(root_path, EPOCH_VERIFIER, "epoch_verifier", must_exist=True)
    epoch_source = _confined(root_path, EPOCH_SOURCE, "epoch_source", must_exist=True)
    capability_producer = _confined(root_path, CAPABILITY_PRODUCER, "capability_producer", must_exist=True)
    definition_file = _confined(root_path, CAPABILITY_DEFINITION, "capability_definition", must_exist=True)
    registry_file = _confined(root_path, CAPABILITY_REGISTRY, "capability_registry", must_exist=True)
    epoch_raw = epoch_file.read_bytes()
    capability_raw = capability_file.read_bytes()
    proposals_raw = proposals_file.read_bytes()
    epoch = read_json(epoch_file)
    capability = read_json(capability_file)
    proposals = read_json(proposals_file)
    epoch_source_sha = file_digest(epoch_source)
    if sha256_bytes(epoch_raw) != epoch_source_sha:
        raise CandidateRefusal("REFUSE_STALE_EPOCH_FIXTURE")
    sealer = _load_module(epoch_verifier, "formalization_epoch_verifier")
    producer = _load_module(capability_producer, "formalization_capability_producer")
    if epoch.get("schema") != EPOCH_SCHEMA:
        raise CandidateRefusal("REFUSE_EPOCH_SCHEMA")
    if capability.get("schema") != CAPABILITY_RECEIPT_SCHEMA:
        raise CandidateRefusal("REFUSE_CAPABILITY_RECEIPT_SCHEMA")
    if not producer.verify_receipt(capability):
        raise CandidateRefusal("REFUSE_CAPABILITY_RECEIPT_SELF_DIGEST")
    epoch_result = sealer.verify_epoch(root_path, _relative(root_path, epoch_file), expected_sha256=sha256_bytes(epoch_raw))
    current_producer_sha = file_digest(capability_producer)
    current_definition_sha = file_digest(definition_file)
    current_registry_sha = file_digest(registry_file)
    root_binding = capability.get("root")
    if not isinstance(root_binding, Mapping):
        raise CandidateRefusal("REFUSE_CAPABILITY_ROOT_BINDING")
    if root_binding.get("runner_sha256") != current_producer_sha:
        raise CandidateRefusal("REFUSE_STALE_CAPABILITY_PRODUCER")
    if root_binding.get("definition_sha256") != current_definition_sha:
        raise CandidateRefusal("REFUSE_STALE_CAPABILITY_DEFINITION")
    if root_binding.get("registry_sha256") != current_registry_sha:
        raise CandidateRefusal("REFUSE_STALE_CAPABILITY_REGISTRY")
    if capability.get("promotion_allowed") is not False or capability.get("activated") is not False:
        raise CandidateRefusal("REFUSE_CAPABILITY_AUTHORITY_FLAGS")
    capability_reproduction, fresh_capability = _capability_reproduction(producer, root_path, capability)
    # Source custody follows the fresh producer receipt. The supplied fixture
    # remains the proposal's identity input, but its source paths may name the
    # source-checkout location while an extracted root exposes only the
    # merged controller location.
    allowed_sources = _bound_source_map(root_path, epoch, fresh_capability)
    semantic = {
        "epoch_id": epoch.get("epoch_id"), "epoch_sequence": epoch.get("epoch_sequence"),
        "epoch_digest": epoch.get("epoch_digest"), "capability_wave_id": capability.get("wave_id"),
        "capability_status": capability.get("status"), "capability_receipt_sha256": capability.get("receipt_sha256"),
        "capability_map_digest": digest(capability.get("capability_map")),
        "capability_fresh_receipt_sha256": capability_reproduction["fresh_receipt_sha256"],
        "capability_fresh_projection_sha256": capability_reproduction["fresh_projection_sha256"],
    }
    return {
        "root": root_path, "epoch_file": epoch_file, "capability_file": capability_file,
        "proposals_file": proposals_file, "epoch_verifier": epoch_verifier, "epoch_source": epoch_source,
        "capability_producer": capability_producer, "definition_file": definition_file,
        "registry_file": registry_file, "epoch": epoch, "capability": capability,
        "fresh_capability": fresh_capability,
        "proposals": proposals, "epoch_raw_sha256": sha256_bytes(epoch_raw),
        "capability_raw_sha256": sha256_bytes(capability_raw), "proposals_raw_sha256": sha256_bytes(proposals_raw),
        "epoch_result": epoch_result, "producer_sha256": current_producer_sha,
        "definition_sha256": current_definition_sha, "registry_sha256": current_registry_sha,
        "epoch_verifier_sha256": file_digest(epoch_verifier), "epoch_source_sha256": epoch_source_sha, "semantic": semantic,
        "capability_reproduction": capability_reproduction,
        "allowed_sources": allowed_sources,
    }


def _strict_records(records: Any, required: set[str], label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(records, list) or not records:
        return [f"{label}:nonempty_list_required"]
    ids: set[str] = set()
    for index, row in enumerate(records):
        name = f"{label}[{index}]"
        if not isinstance(row, dict) or set(row) != required:
            errors.append(f"{name}:strict_fields")
            continue
        key = next((key for key in row if key.endswith("_id")), None)
        value = row.get(key) if key else None
        if not isinstance(value, str) or not value:
            errors.append(f"{name}:named_id_required")
        elif value in ids:
            errors.append(f"{name}:duplicate_identifier")
        ids.add(str(value))
    return errors


def _resolve_source_ref(root: Path, declared: str, label: str) -> Path:
    """Resolve a declared source, allowing only the known merged-path twin."""

    try:
        return _confined(root, declared, label, must_exist=True)
    except CandidateRefusal as original:
        alternate = _SOURCE_LOCATION_ALTERNATE.get(declared)
        if alternate is None or not str(original).startswith(("REFUSE_FILE_MISSING", "REFUSE_PATH_RESOLVE")):
            raise
        try:
            return _confined(root, alternate, f"{label}:alternate", must_exist=True)
        except CandidateRefusal:
            raise original


def _validate_source_refs(refs: Any, root: Path, allowed: Mapping[str, str], label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(refs, list) or not refs:
        return [f"{label}:nonempty_list_required"]
    for index, ref in enumerate(refs):
        name = f"{label}[{index}]"
        if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
            errors.append(f"{name}:strict_fields")
            continue
        try:
            declared = str(ref["path"])
            path = _resolve_source_ref(root, declared, name)
        except CandidateRefusal as exc:
            errors.append(str(exc))
            continue
        relative, observed = _relative(root, path), file_digest(path)
        if observed != ref.get("sha256"):
            errors.append(f"{name}:sha256_mismatch")
        if allowed.get(_logical_source_id(relative)) != observed:
            errors.append(f"{name}:not_epoch_or_capability_bound")
    return errors


def validate_proposal(proposal: dict[str, Any], epoch_digest: str, capability_receipt_sha256: str, root: Path, allowed_sources: Mapping[str, str], probe_ids: set[str]) -> list[str]:
    errors: list[str] = []
    child_id = str(proposal.get("child_id", ""))
    if child_id not in CHILD_IDS:
        return [f"{child_id}:unknown_child"]
    if proposal.get("schema") != PROPOSAL_SCHEMA:
        errors.append(f"{child_id}:schema")
    if set(proposal) != CHILD_KEYS[child_id]:
        errors.append(f"{child_id}:strict_fields")
    if proposal.get("proposal_kind") != CHILD_KINDS[child_id]:
        errors.append(f"{child_id}:proposal_kind")
    if proposal.get("input_epoch_digest") != epoch_digest:
        errors.append(f"{child_id}:epoch_digest_binding")
    if proposal.get("capability_receipt_sha256") != capability_receipt_sha256:
        errors.append(f"{child_id}:capability_receipt_binding")
    if proposal.get("proposal_only") is not True or proposal.get("observations") != [] or proposal.get("decisions") != [] or proposal.get("activation_requested") is not False:
        errors.append(f"{child_id}:proposal_only_contract")
    errors.extend(_validate_source_refs(proposal.get("source_refs"), root, allowed_sources, f"{child_id}:source_refs"))
    if not isinstance(proposal.get("claim_ceiling"), str) or not proposal["claim_ceiling"].strip():
        errors.append(f"{child_id}:claim_ceiling")
    if child_id == "axiom_digger":
        errors.extend(_strict_records(proposal.get("assumptions"), {"assumption_id", "statement", "polarity", "status"}, f"{child_id}:assumptions"))
        errors.extend(_strict_records(proposal.get("non_objectives"), {"objective_id", "statement", "polarity", "status"}, f"{child_id}:non_objectives"))
        for row in proposal.get("assumptions", []) if isinstance(proposal.get("assumptions"), list) else []:
            if not isinstance(row, dict):
                continue
            if row.get("polarity") != "positive" or row.get("status") != "ASSUMPTION":
                errors.append(f"{child_id}:assumption_status")
        for row in proposal.get("non_objectives", []) if isinstance(proposal.get("non_objectives"), list) else []:
            if not isinstance(row, dict):
                continue
            if row.get("polarity") != "negative" or row.get("status") != "NON_OBJECTIVE":
                errors.append(f"{child_id}:non_objective_status")
    elif child_id == "constraint_digger":
        errors.extend(_strict_records(proposal.get("predicates"), {"predicate_id", "expression", "domain", "status"}, f"{child_id}:predicates"))
        for row in proposal.get("predicates", []) if isinstance(proposal.get("predicates"), list) else []:
            if not isinstance(row, dict):
                continue
            if row.get("status") != "CANDIDATE" or not isinstance(row.get("expression"), str) or not row["expression"].strip():
                errors.append(f"{child_id}:predicate_status_or_expression")
            if not isinstance(row.get("domain"), list) or not row["domain"]:
                errors.append(f"{child_id}:predicate_domain")
    elif child_id == "gate_digger":
        errors.extend(_strict_records(proposal.get("obligations"), {"obligation_id", "requirement", "negative_id", "status"}, f"{child_id}:obligations"))
        errors.extend(_strict_records(proposal.get("negatives"), {"negative_id", "description", "expected_disposition"}, f"{child_id}:negatives"))
        negatives = {row.get("negative_id") for row in proposal.get("negatives", []) if isinstance(row, dict)}
        for row in proposal.get("obligations", []) if isinstance(proposal.get("obligations"), list) else []:
            if not isinstance(row, dict):
                continue
            if row.get("status") != "CANDIDATE" or row.get("negative_id") not in negatives:
                errors.append(f"{child_id}:obligation_status_or_negative")
        for row in proposal.get("negatives", []) if isinstance(proposal.get("negatives"), list) else []:
            if not isinstance(row, dict):
                continue
            if row.get("expected_disposition") not in {"REFUSE", "HOLD"}:
                errors.append(f"{child_id}:negative_disposition")
    else:
        errors.extend(_strict_records(proposal.get("interpretations"), {"interpretation_id", "probe_ids", "quotient", "mass", "topology", "status"}, f"{child_id}:interpretations"))
        for row in proposal.get("interpretations", []) if isinstance(proposal.get("interpretations"), list) else []:
            if not isinstance(row, dict):
                continue
            if row.get("status") != "PROPOSAL" or not isinstance(row.get("probe_ids"), list) or not row["probe_ids"]:
                errors.append(f"{child_id}:interpretation_status_or_probes")
            elif not set(row["probe_ids"]).issubset(probe_ids):
                errors.append(f"{child_id}:unknown_probe")
            for field in ("quotient", "mass", "topology"):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(f"{child_id}:{field}")
    return sorted(set(errors))


def _semantic_token(text: str) -> tuple[str, int]:
    normalized = " ".join(text.casefold().strip().split())
    negative = 0
    for prefix in ("not ", "!", "does not ", "must not "):
        if normalized.startswith(prefix):
            negative = 1
            normalized = normalized[len(prefix):].strip()
            break
    return normalized, negative


def detect_contradictions(proposals: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Find semantic oppositions; preserve them instead of selecting a side."""

    rows: list[dict[str, Any]] = []
    seen: dict[str, dict[str, Any]] = {}
    for proposal in proposals:
        if not isinstance(proposal, dict):
            continue
        child_id = str(proposal.get("child_id", ""))
        for section in ("assumptions", "non_objectives", "predicates", "obligations", "negatives", "interpretations"):
            records = proposal.get(section, [])
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue
                text = record.get("expression", record.get("statement", record.get("requirement", record.get("description"))))
                if not isinstance(text, str) or not text.strip():
                    continue
                base, polarity = _semantic_token(text)
                key = f"{section}:{base}"
                current = {"child_id": child_id, "section": section, "identifier": next((record[k] for k in record if k.endswith("_id")), ""), "polarity": polarity, "text": text}
                previous = seen.get(key)
                if previous is not None and previous["polarity"] != polarity:
                    rows.append({"kind": "SEMANTIC_CONTRADICTION", "key": key, "left": previous, "right": current, "resolution": "UNRESOLVED"})
                else:
                    seen[key] = current
    return sorted(rows, key=lambda row: (row["key"], row["left"]["identifier"], row["right"]["identifier"]))


def _child_receipts(proposals: list[dict[str, Any]], terminal_state: str) -> list[dict[str, Any]]:
    return [
        {
            "child_id": row.get("child_id") if isinstance(row, dict) else None,
            "terminal_state": terminal_state,
            "skill_execution_claimed": False,
            "proposal_digest": digest(row) if isinstance(row, dict) else None,
            "proposal_kind": row.get("proposal_kind") if isinstance(row, dict) else None,
        }
        for row in proposals
    ]


def compile_frontier(proposals: list[dict[str, Any]], epoch_digest: str, capability_receipt_sha256: str, contradictions: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {str(row["child_id"]): row for row in proposals}
    return {
        "schema": FRONTIER_SCHEMA, "wave_id": WAVE_ID, "status": "PROPOSAL_FRONTIER",
        "voting": False, "truth_decided": False, "gate_activated": False, "promotion_allowed": False,
        "epoch_digest": epoch_digest, "capability_receipt_sha256": capability_receipt_sha256,
        "children": [{"child_id": child_id, "proposal_digest": digest(by_id[child_id]), "proposal_kind": by_id[child_id]["proposal_kind"]} for child_id in CHILD_IDS],
        "candidate_sets": {
            "assumptions": copy.deepcopy(by_id["axiom_digger"]["assumptions"]),
            "non_objectives": copy.deepcopy(by_id["axiom_digger"]["non_objectives"]),
            "predicates": copy.deepcopy(by_id["constraint_digger"]["predicates"]),
            "gate_obligations": copy.deepcopy(by_id["gate_digger"]["obligations"]),
            "gate_negatives": copy.deepcopy(by_id["gate_digger"]["negatives"]),
            "quotient_mass_topology": copy.deepcopy(by_id["basin_digger"]["interpretations"]),
        },
        "unresolved_contradictions": copy.deepcopy(contradictions), "claim_ceiling": CLAIM_CEILING,
    }


def _seal_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    unsigned = copy.deepcopy(receipt)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    value = digest(unsigned)
    receipt["receipt_sha256"] = value
    receipt["receipt_self_sha256"] = value
    return receipt


def _identity(prepared: dict[str, Any], root: Path) -> dict[str, Any]:
    return {
        "declared_root": {"path": ".", "resolved_path": str(root), "symlink": False},
        "input_paths": {"context_epoch": _relative(root, prepared["epoch_file"]), "capability_receipt": _relative(root, prepared["capability_file"]), "proposal_bundle": _relative(root, prepared["proposals_file"])},
        "raw_input_sha256": {"context_epoch": prepared["epoch_raw_sha256"], "capability_receipt": prepared["capability_raw_sha256"], "proposal_bundle": prepared["proposals_raw_sha256"]},
        "semantic_inputs": copy.deepcopy(prepared["semantic"]),
        "capability_reproduction": copy.deepcopy(prepared["capability_reproduction"]),
        "epoch_source_binding": {"path": EPOCH_SOURCE, "sha256": prepared["epoch_source_sha256"]},
        "runner_binding": {"path": _relative(root, Path(__file__).resolve()), "sha256": file_digest(Path(__file__).resolve())},
        "verifier_bindings": {
            "epoch_sealer": {"path": EPOCH_VERIFIER, "sha256": prepared["epoch_verifier_sha256"]},
            "capability_producer": {"path": CAPABILITY_PRODUCER, "sha256": prepared["producer_sha256"]},
            "capability_definition": {"path": CAPABILITY_DEFINITION, "sha256": prepared["definition_sha256"]},
            "capability_registry": {"path": CAPABILITY_REGISTRY, "sha256": prepared["registry_sha256"]},
        },
    }


def _base_receipt(identity: dict[str, Any], *, status: str, reason: str, cancellation_state: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA, "wave_id": WAVE_ID, "status": status, "reason": reason,
        "candidate_state": "NEW_CANDIDATE", "activated": False, "promotion_allowed": False,
        **identity, "child_receipts": [], "child_outputs": [], "preload_receipts": [], "provider_call_receipt": None,
        "cancellation_state": cancellation_state, "disagreement_state": "NOT_APPLICABLE", "frontier": None,
        "frontier_digest": None, "contradiction_digest": digest([]), "output_digest": None,
        "error_digest": digest([]),
        "frontier_output_path": None, "output_artifact_write": False, "skill_execution_claimed": False,
        "no_provider_route": True, "no_heavy_route": True, "truth_not_decided": True,
        "gate_not_activated": True, "epoch_digest": None, "capability_receipt_sha256": None,
        "proposal_digests": {}, "source_ref_bindings": [], "claim_ceiling": CLAIM_CEILING,
    }


def _write_receipt_if_allowed(root: Path, out_path: str | Path | None, receipt: dict[str, Any]) -> None:
    if out_path is None:
        return
    output = _confined(root, out_path, "out", must_exist=False)
    write_json(output, receipt)


def run_wave(root: Path, context_epoch_path: str | Path = _DEFAULT_CONTEXT, capability_probe_map_path: str | Path = _DEFAULT_CAPABILITY, proposals_path: str | Path = _DEFAULT_PROPOSALS, *, out_path: str | Path | None = None, cancel_requested: bool = False) -> dict[str, Any]:
    """Validate real inputs and compile one proposal-only frontier."""

    try:
        prepared = _prepare_inputs(root, context_epoch_path, capability_probe_map_path, proposals_path)
        root_path = prepared["root"]
        identity = _identity(prepared, root_path)
        if cancel_requested:
            receipt = _base_receipt(identity, status="CANCELLED", reason="CANCELLED_BEFORE_FRONTIER", cancellation_state="CANCELLED")
            receipt["epoch_digest"] = prepared["epoch"]["epoch_digest"]
            receipt["capability_receipt_sha256"] = prepared["capability"]["receipt_sha256"]
            receipt["semantic_input_digest"] = digest(receipt["semantic_inputs"])
            receipt["errors"] = []
            receipt["error_digest"] = digest([])
            _seal_receipt(receipt)
            _write_receipt_if_allowed(root_path, out_path, receipt)
            return receipt
        epoch, capability, bundle = prepared["epoch"], prepared["capability"], prepared["proposals"]
        errors: list[str] = []
        if bundle.get("schema") != BUNDLE_SCHEMA:
            errors.append("bundle:schema")
        if set(bundle) != BUNDLE_KEYS:
            errors.append("bundle:strict_fields")
        expected_bundle_digest = digest({key: value for key, value in bundle.items() if key != "proposal_bundle_digest"})
        if bundle.get("proposal_bundle_digest") != expected_bundle_digest:
            errors.append("bundle:proposal_bundle_digest")
        if bundle.get("epoch_digest") != epoch.get("epoch_digest"):
            errors.append("bundle:epoch_digest_binding")
        if bundle.get("capability_receipt_sha256") != capability.get("receipt_sha256"):
            errors.append("bundle:capability_receipt_binding")
        if bundle.get("proposal_only") is not True or bundle.get("promotion_allowed") is not False:
            errors.append("bundle:authority_flags")
        rows = bundle.get("children") if isinstance(bundle.get("children"), list) else []
        if [str(row.get("child_id")) for row in rows if isinstance(row, dict)] != list(CHILD_IDS):
            errors.append("bundle:child_set_or_order")
        capability_children = prepared["fresh_capability"].get("children") if isinstance(prepared["fresh_capability"].get("children"), list) else []
        probe_ids: set[str] = set()
        for child in capability_children:
            if not isinstance(child, dict) or not isinstance(child.get("result"), dict):
                continue
            structured = child["result"].get("structured")
            if not isinstance(structured, dict) or not isinstance(structured.get("rows"), list):
                continue
            for row in structured["rows"]:
                if isinstance(row, dict) and row.get("probe"):
                    probe_ids.add(str(row["probe"]))
        missing_probe_declarations = not probe_ids
        if missing_probe_declarations:
            errors.append("REFUSE_CAPABILITY_PROBE_DECLARATIONS")
        child_errors: dict[str, list[str]] = {}
        for row in rows:
            if not isinstance(row, dict):
                errors.append("bundle:child_object")
                continue
            child_id = str(row.get("child_id", ""))
            row_errors = validate_proposal(row, str(epoch["epoch_digest"]), str(capability["receipt_sha256"]), root_path, prepared["allowed_sources"], probe_ids)
            if row_errors:
                child_errors[child_id] = row_errors
                errors.extend(row_errors)
        contradictions = detect_contradictions(rows)
        receipt_reason = "FRONTIER_COMPILED" if not errors else ("REFUSE_CAPABILITY_PROBE_DECLARATIONS" if missing_probe_declarations else "REFUSE_FORMALIZATION_INPUT")
        receipt = _base_receipt(identity, status="PASS" if not errors else "REFUSE", reason=receipt_reason, cancellation_state="NOT_REQUESTED")
        receipt["semantic_input_digest"] = digest(receipt["semantic_inputs"])
        receipt["child_outputs"] = copy.deepcopy(rows)
        receipt["child_receipts"] = _child_receipts(rows, terminal_state="PROPOSAL_VALIDATED" if not errors else "REFUSED")
        receipt["epoch_digest"] = epoch["epoch_digest"]
        receipt["capability_receipt_sha256"] = capability["receipt_sha256"]
        receipt["proposal_digests"] = {str(row.get("child_id")): digest(row) for row in rows if isinstance(row, dict)}
        receipt["source_ref_bindings"] = [{"path": path, "sha256": sha} for path, sha in sorted({(ref["path"], ref["sha256"]) for row in rows if isinstance(row, dict) for ref in row.get("source_refs", []) if isinstance(ref, dict) and "path" in ref and "sha256" in ref})]
        receipt["contradiction_scan"] = {"status": "CLEAR" if not contradictions else "SEMANTIC_CONTRADICTIONS_UNRESOLVED", "rows": contradictions}
        receipt["contradiction_digest"] = digest(contradictions)
        receipt["errors"] = sorted(set(errors))
        receipt["error_digest"] = digest(receipt["errors"])
        if not errors:
            frontier = compile_frontier(rows, str(epoch["epoch_digest"]), str(capability["receipt_sha256"]), contradictions)
            receipt["frontier"] = frontier
            receipt["frontier_digest"] = digest(frontier)
            receipt["output_digest"] = receipt["frontier_digest"]
            receipt["disagreement_state"] = "SEMANTIC_CONTRADICTIONS_PRESERVED" if contradictions else "NONE"
        _seal_receipt(receipt)
        _write_receipt_if_allowed(root_path, out_path, receipt)
        return receipt
    except (CandidateRefusal, OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        try:
            root_path = _root(root)
            identity = {"declared_root": {"path": ".", "resolved_path": str(root_path), "symlink": False}}
        except Exception:
            root_path = None
            identity = {"declared_root": {"path": str(root), "resolved_path": None, "symlink": False}}
        receipt = _base_receipt(identity, status="REFUSE", reason=str(exc).split(":", 1)[0], cancellation_state="NOT_REQUESTED")
        receipt["errors"] = [str(exc)]
        receipt["error_digest"] = digest(receipt["errors"])
        _seal_receipt(receipt)
        if root_path is not None and out_path is not None:
            try:
                _write_receipt_if_allowed(root_path, out_path, receipt)
            except CandidateRefusal:
                pass
        return receipt


def verify_receipt(receipt: dict[str, Any], root: Path | None = None) -> bool:
    """Verify self identity and, when root is supplied, every live summary."""

    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        return False
    expected = receipt.get("receipt_sha256")
    if not _is_digest(expected) or expected != receipt.get("receipt_self_sha256"):
        return False
    unsigned = copy.deepcopy(receipt)
    unsigned.pop("receipt_sha256", None)
    unsigned.pop("receipt_self_sha256", None)
    if digest(unsigned) != expected:
        return False
    if receipt.get("candidate_state") != "NEW_CANDIDATE" or receipt.get("activated") is not False or receipt.get("promotion_allowed") is not False:
        return False
    if receipt.get("provider_call_receipt") is not None or receipt.get("preload_receipts") != [] or receipt.get("skill_execution_claimed") is not False:
        return False
    if receipt.get("no_provider_route") is not True or receipt.get("no_heavy_route") is not True or receipt.get("truth_not_decided") is not True or receipt.get("gate_not_activated") is not True or receipt.get("output_artifact_write") is not False or receipt.get("frontier_output_path") is not None:
        return False
    if receipt.get("semantic_input_digest") != digest(receipt.get("semantic_inputs")):
        return False
    if receipt.get("error_digest") != digest(receipt.get("errors", [])):
        return False
    status = receipt.get("status")
    if status == "CANCELLED":
        if receipt.get("frontier") is not None or receipt.get("output_digest") is not None or receipt.get("cancellation_state") != "CANCELLED":
            return False
    elif status not in {"PASS", "REFUSE"}:
        return False
    elif status == "REFUSE":
        # A self-resealed refusal is not evidence.  Re-run the exact bound
        # inputs and require byte-for-byte receipt equality (apart from the
        # self-digest fields) before accepting its reason or error list.
        input_paths = receipt.get("input_paths")
        if not isinstance(input_paths, Mapping):
            return False
        if not all(isinstance(input_paths.get(key), str) for key in ("context_epoch", "capability_receipt", "proposal_bundle")):
            return False
        if root is None:
            try:
                root = _root(_CANDIDATE_DIR.parents[3])
            except Exception:
                return False
        try:
            replayed = run_wave(
                root,
                input_paths["context_epoch"],
                input_paths["capability_receipt"],
                input_paths["proposal_bundle"],
            )
        except Exception:
            return False
        if replayed.get("status") != "REFUSE":
            return False
        original_without_self = copy.deepcopy(receipt)
        replayed_without_self = copy.deepcopy(replayed)
        for value in (original_without_self, replayed_without_self):
            value.pop("receipt_sha256", None)
            value.pop("receipt_self_sha256", None)
        return original_without_self == replayed_without_self
    elif status != "PASS":
        return receipt.get("frontier") is None and receipt.get("output_digest") is None
    contradictions = receipt.get("contradiction_scan", {}).get("rows", [])
    if receipt.get("contradiction_digest") != digest(contradictions):
        return False
    frontier = receipt.get("frontier")
    if status == "PASS":
        if not isinstance(frontier, dict) or receipt.get("frontier_digest") != digest(frontier) or receipt.get("output_digest") != receipt.get("frontier_digest"):
            return False
        if frontier.get("voting") is not False or frontier.get("truth_decided") is not False or frontier.get("gate_activated") is not False:
            return False
    if root is None:
        try:
            root = _root(_CANDIDATE_DIR.parents[3])
        except Exception:
            return False
    try:
        prepared = _prepare_inputs(root, receipt["input_paths"]["context_epoch"], receipt["input_paths"]["capability_receipt"], receipt["input_paths"]["proposal_bundle"])
        identity = _identity(prepared, prepared["root"])
        for key in ("declared_root", "input_paths", "raw_input_sha256", "semantic_inputs", "capability_reproduction", "epoch_source_binding", "runner_binding", "verifier_bindings"):
            if receipt.get(key) != identity.get(key):
                return False
        if receipt.get("epoch_digest") != prepared["epoch"]["epoch_digest"] or receipt.get("capability_receipt_sha256") != prepared["capability"]["receipt_sha256"]:
            return False
        if status == "CANCELLED":
            return (
                receipt.get("reason") == "CANCELLED_BEFORE_FRONTIER"
                and receipt.get("claim_ceiling") == CLAIM_CEILING
                and receipt.get("child_outputs") == []
                and receipt.get("child_receipts") == []
                and receipt.get("disagreement_state") == "NOT_APPLICABLE"
            )
        rows = prepared["proposals"].get("children")
        expected_proposal_digests = {str(row.get("child_id")): digest(row) for row in rows if isinstance(row, dict)}
        expected_source_refs = [{"path": path, "sha256": sha} for path, sha in sorted({(ref["path"], ref["sha256"]) for row in rows if isinstance(row, dict) for ref in row.get("source_refs", []) if isinstance(ref, dict) and "path" in ref and "sha256" in ref})]
        if receipt.get("proposal_digests") != expected_proposal_digests or receipt.get("source_ref_bindings") != expected_source_refs:
            return False
        if receipt.get("child_outputs") != rows or receipt.get("child_receipts") != _child_receipts(rows, terminal_state="PROPOSAL_VALIDATED"):
            return False
        contradictions_now = detect_contradictions(rows)
        if contradictions_now != contradictions:
            return False
        expected_scan = {"status": "CLEAR" if not contradictions_now else "SEMANTIC_CONTRADICTIONS_UNRESOLVED", "rows": contradictions_now}
        if receipt.get("contradiction_scan") != expected_scan:
            return False
        expected_frontier = compile_frontier(rows, prepared["epoch"]["epoch_digest"], prepared["capability"]["receipt_sha256"], contradictions_now)
        expected_disagreement = "SEMANTIC_CONTRADICTIONS_PRESERVED" if contradictions_now else "NONE"
        return (
            frontier == expected_frontier
            and receipt.get("errors") == []
            and receipt.get("reason") == "FRONTIER_COMPILED"
            and receipt.get("disagreement_state") == expected_disagreement
            and receipt.get("claim_ceiling") == CLAIM_CEILING
        )
    except Exception:
        return False


def replay_receipt(receipt: dict[str, Any] | Path, root: Path, context_epoch_path: str | Path = _DEFAULT_CONTEXT, capability_probe_map_path: str | Path = _DEFAULT_CAPABILITY, proposals_path: str | Path = _DEFAULT_PROPOSALS) -> dict[str, Any]:
    try:
        root_path = _root(root)
        if isinstance(receipt, (str, Path)):
            # Confine before reading: lexical `..`, symlink, and outside-root
            # receipt paths must not become an input read through normalization.
            receipt_path = _confined(root_path, receipt, "receipt", must_exist=True)
            original = read_json(receipt_path)
        else:
            original = receipt
    except (CandidateRefusal, OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "REFUSE", "reason": str(exc).split(":", 1)[0], "detail": str(exc)}
    if not verify_receipt(original, root_path):
        return {"status": "REFUSE", "reason": "REFUSE_ORIGINAL_RECEIPT_TAMPER"}
    replayed = run_wave(root_path, context_epoch_path, capability_probe_map_path, proposals_path, cancel_requested=original.get("status") == "CANCELLED")
    equal = copy.deepcopy(original)
    fresh = copy.deepcopy(replayed)
    for field in ("receipt_sha256", "receipt_self_sha256"):
        equal.pop(field, None)
        fresh.pop(field, None)
    return {"status": "PASS" if replayed.get("status") == original.get("status") and equal == fresh else "REFUSE", "original_receipt_sha256": original.get("receipt_sha256"), "replayed_receipt_sha256": replayed.get("receipt_sha256"), "digest_match": original.get("receipt_sha256") == replayed.get("receipt_sha256"), "summary_match": equal == fresh}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="inactive CB formalization/digger candidate")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--context-epoch", default=_DEFAULT_CONTEXT)
    parser.add_argument("--capability-probe-map", default=_DEFAULT_CAPABILITY)
    parser.add_argument("--proposals", default=_DEFAULT_PROPOSALS)
    parser.add_argument("--out", default=None)
    parser.add_argument("--cancel", action="store_true")
    args = parser.parse_args(argv)
    receipt = run_wave(args.root, args.context_epoch, args.capability_probe_map, args.proposals, out_path=args.out, cancel_requested=args.cancel)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if receipt.get("status") == "PASS" else (3 if receipt.get("status") == "REFUSE" else 2)


if __name__ == "__main__":
    raise SystemExit(main())
