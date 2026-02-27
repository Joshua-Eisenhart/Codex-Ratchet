import hashlib
import json
from pathlib import Path


CANONICAL_SCHEMA = "A1_STRATEGY_v1"
FORBIDDEN_FIELDS = {"confidence", "probability", "embedding", "hidden_prompt", "raw_text"}
ALLOWED_SPEC_KINDS = {"MATH_DEF", "TERM_DEF", "LABEL_DEF", "CANON_PERMIT", "SIM_SPEC"}
ALLOWED_ITEM_CLASSES = {"SPEC_HYP"}
ALLOWED_TOKEN_CLASSES = {
    "STATE_TOKEN",
    "PROBE_TOKEN",
    "REGISTRY_TOKEN",
    "MATH_TOKEN",
    "TERM_TOKEN",
    "LABEL_TOKEN",
    "PERMIT_TOKEN",
    "EVIDENCE_TOKEN",
}

REQUIRED_ROOT_FIELDS = {
    "schema",
    "strategy_id",
    "inputs",
    "budget",
    "policy",
    "targets",
    "alternatives",
    "sims",
    "self_audit",
}

REQUIRED_INPUT_FIELDS = {
    "state_hash",
    "fuel_slice_hashes",
    "bootpack_rules_hash",
    "pinned_ruleset_sha256",
    "pinned_megaboot_sha256",
}

REQUIRED_BUDGET_FIELDS = {"max_items", "max_sims"}
REQUIRED_POLICY_FIELDS = {"forbid_fields", "overlay_ban_terms", "require_try_to_fail"}
REQUIRED_SIMS_FIELDS = {"positive", "negative"}
REQUIRED_SELF_AUDIT_FIELDS = {
    "strategy_hash",
    "compile_lane_digest",
    "candidate_count",
    "alternative_count",
    "operator_ids_used",
}
REQUIRED_CANDIDATE_FIELDS = {"item_class", "id", "kind", "requires", "def_fields", "asserts", "operator_id"}
REQUIRED_DEF_FIELD_FIELDS = {"field_id", "name", "value_kind", "value"}
REQUIRED_ASSERT_FIELDS = {"assert_id", "token_class", "token"}
REQUIRED_SIM_PLAN_FIELDS = {"sim_id", "binds_to"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_strategy_bytes(strategy: dict) -> bytes:
    return json.dumps(strategy, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _is_hex64(value: object) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(ch in "0123456789abcdef" for ch in value)


def _scan_forbidden_fields(payload: object, errors: list[str], path: str = "$") -> None:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key) in FORBIDDEN_FIELDS:
                errors.append(f"forbidden field present: {path}.{key}")
            _scan_forbidden_fields(value, errors, f"{path}.{key}")
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            _scan_forbidden_fields(item, errors, f"{path}[{index}]")


def _validate_candidate(candidate: object, index: int, lane: str, errors: list[str]) -> None:
    prefix = f"{lane}[{index}]"
    if not isinstance(candidate, dict):
        errors.append(f"{prefix} must be object")
        return
    unknown_keys = sorted(set(candidate.keys()) - REQUIRED_CANDIDATE_FIELDS)
    for key in unknown_keys:
        errors.append(f"{prefix} unknown field: {key}")
    for key in sorted(REQUIRED_CANDIDATE_FIELDS - set(candidate.keys())):
        errors.append(f"{prefix} missing field: {key}")
    if candidate.get("item_class") not in ALLOWED_ITEM_CLASSES:
        errors.append(f"{prefix}.item_class must be one of {sorted(ALLOWED_ITEM_CLASSES)}")
    if candidate.get("kind") not in ALLOWED_SPEC_KINDS:
        errors.append(f"{prefix}.kind must be one of {sorted(ALLOWED_SPEC_KINDS)}")
    requires = candidate.get("requires")
    if not isinstance(requires, list):
        errors.append(f"{prefix}.requires must be list")
        requires = []
    if not isinstance(candidate.get("def_fields"), list):
        errors.append(f"{prefix}.def_fields must be list")
    if not isinstance(candidate.get("asserts"), list):
        errors.append(f"{prefix}.asserts must be list")
    if candidate.get("kind") == "SIM_SPEC":
        has_probe_dep = any(isinstance(dep, str) and dep.startswith("P") for dep in requires)
        if not has_probe_dep:
            errors.append(f"{prefix}.requires must include at least one probe dependency id starting with 'P' for SIM_SPEC")

    for j, field in enumerate(candidate.get("def_fields", [])):
        if not isinstance(field, dict):
            errors.append(f"{prefix}.def_fields[{j}] must be object")
            continue
        for key in sorted(REQUIRED_DEF_FIELD_FIELDS - set(field.keys())):
            errors.append(f"{prefix}.def_fields[{j}] missing field: {key}")
    for j, assertion in enumerate(candidate.get("asserts", [])):
        if not isinstance(assertion, dict):
            errors.append(f"{prefix}.asserts[{j}] must be object")
            continue
        for key in sorted(REQUIRED_ASSERT_FIELDS - set(assertion.keys())):
            errors.append(f"{prefix}.asserts[{j}] missing field: {key}")
        if assertion.get("token_class") not in ALLOWED_TOKEN_CLASSES:
            errors.append(f"{prefix}.asserts[{j}].token_class must be one of {sorted(ALLOWED_TOKEN_CLASSES)}")


def validate_strategy(strategy: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(strategy, dict):
        return ["strategy must be object"]

    unknown_root_keys = sorted(set(strategy.keys()) - REQUIRED_ROOT_FIELDS)
    for key in unknown_root_keys:
        errors.append(f"unknown root field: {key}")
    for key in sorted(REQUIRED_ROOT_FIELDS - set(strategy.keys())):
        errors.append(f"missing root field: {key}")
    if strategy.get("schema") != CANONICAL_SCHEMA:
        errors.append(f"schema must be {CANONICAL_SCHEMA}")

    _scan_forbidden_fields(strategy, errors)

    inputs = strategy.get("inputs")
    if not isinstance(inputs, dict):
        errors.append("inputs must be object")
    else:
        for key in sorted(REQUIRED_INPUT_FIELDS - set(inputs.keys())):
            errors.append(f"inputs missing field: {key}")
        for hex_key in ["state_hash", "bootpack_rules_hash"]:
            if hex_key in inputs and not _is_hex64(inputs.get(hex_key)):
                errors.append(f"inputs.{hex_key} must be 64 lowercase hex")
        for maybe_hex in ["pinned_ruleset_sha256", "pinned_megaboot_sha256"]:
            value = inputs.get(maybe_hex)
            if value is not None and value != "" and not _is_hex64(value):
                errors.append(f"inputs.{maybe_hex} must be null/empty or 64 lowercase hex")
        if not isinstance(inputs.get("fuel_slice_hashes"), list):
            errors.append("inputs.fuel_slice_hashes must be list")
        else:
            for index, value in enumerate(inputs.get("fuel_slice_hashes", [])):
                if not _is_hex64(value):
                    errors.append(f"inputs.fuel_slice_hashes[{index}] must be 64 lowercase hex")

    budget = strategy.get("budget")
    if not isinstance(budget, dict):
        errors.append("budget must be object")
    else:
        for key in sorted(REQUIRED_BUDGET_FIELDS - set(budget.keys())):
            errors.append(f"budget missing field: {key}")
        for key in REQUIRED_BUDGET_FIELDS:
            if key in budget and (not isinstance(budget[key], int) or budget[key] < 0):
                errors.append(f"budget.{key} must be integer >= 0")

    policy = strategy.get("policy")
    if not isinstance(policy, dict):
        errors.append("policy must be object")
    else:
        for key in sorted(REQUIRED_POLICY_FIELDS - set(policy.keys())):
            errors.append(f"policy missing field: {key}")
        forbid_fields = policy.get("forbid_fields", [])
        if not isinstance(forbid_fields, list):
            errors.append("policy.forbid_fields must be list")
        else:
            present = {str(x) for x in forbid_fields}
            if not FORBIDDEN_FIELDS.issubset(present):
                errors.append(f"policy.forbid_fields must include {sorted(FORBIDDEN_FIELDS)}")
        if not isinstance(policy.get("overlay_ban_terms"), list):
            errors.append("policy.overlay_ban_terms must be list")
        if not isinstance(policy.get("require_try_to_fail"), bool):
            errors.append("policy.require_try_to_fail must be boolean")

    targets = strategy.get("targets")
    alternatives = strategy.get("alternatives")
    if not isinstance(targets, list) or len(targets) < 1:
        errors.append("targets must be non-empty list")
    else:
        for i, candidate in enumerate(targets):
            _validate_candidate(candidate, i, "targets", errors)
    if not isinstance(alternatives, list):
        errors.append("alternatives must be list")
    else:
        for i, candidate in enumerate(alternatives):
            _validate_candidate(candidate, i, "alternatives", errors)
        if isinstance(policy, dict) and policy.get("require_try_to_fail") and len(alternatives) < 1:
            errors.append("alternatives must be non-empty when require_try_to_fail is true")

    sims = strategy.get("sims")
    if not isinstance(sims, dict):
        errors.append("sims must be object")
    else:
        for key in sorted(REQUIRED_SIMS_FIELDS - set(sims.keys())):
            errors.append(f"sims missing field: {key}")
        for lane in ["positive", "negative"]:
            plan = sims.get(lane, [])
            if not isinstance(plan, list):
                errors.append(f"sims.{lane} must be list")
                continue
            for i, row in enumerate(plan):
                if not isinstance(row, dict):
                    errors.append(f"sims.{lane}[{i}] must be object")
                    continue
                for key in sorted(REQUIRED_SIM_PLAN_FIELDS - set(row.keys())):
                    errors.append(f"sims.{lane}[{i}] missing field: {key}")

    self_audit = strategy.get("self_audit")
    if not isinstance(self_audit, dict):
        errors.append("self_audit must be object")
    else:
        for key in sorted(REQUIRED_SELF_AUDIT_FIELDS - set(self_audit.keys())):
            errors.append(f"self_audit missing field: {key}")
        for key in ["strategy_hash", "compile_lane_digest"]:
            value = self_audit.get(key)
            if value is not None and value != "" and not _is_hex64(value):
                errors.append(f"self_audit.{key} must be empty or 64 lowercase hex")
        for key in ["candidate_count", "alternative_count"]:
            value = self_audit.get(key)
            if not isinstance(value, int) or value < 0:
                errors.append(f"self_audit.{key} must be integer >= 0")
        operator_ids = self_audit.get("operator_ids_used")
        if not isinstance(operator_ids, list):
            errors.append("self_audit.operator_ids_used must be list")
        if isinstance(targets, list) and isinstance(self_audit.get("candidate_count"), int):
            if self_audit.get("candidate_count") != len(targets):
                errors.append("self_audit.candidate_count must equal len(targets)")
        if isinstance(alternatives, list) and isinstance(self_audit.get("alternative_count"), int):
            if self_audit.get("alternative_count") != len(alternatives):
                errors.append("self_audit.alternative_count must equal len(alternatives)")

    ids = []
    for candidate in (targets if isinstance(targets, list) else []):
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str):
            ids.append(candidate["id"])
    for candidate in (alternatives if isinstance(alternatives, list) else []):
        if isinstance(candidate, dict) and isinstance(candidate.get("id"), str):
            ids.append(candidate["id"])
    if len(ids) != len(set(ids)):
        errors.append("candidate ids must be unique across targets+alternatives")

    return errors


def load_strategy(path: Path) -> dict:
    raw = path.read_bytes()
    strategy = json.loads(raw.decode("utf-8"))
    errors = validate_strategy(strategy)
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "path": str(path),
        "sha256": _sha256_bytes(raw),
        "strategy": strategy,
    }
