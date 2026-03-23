import hashlib
import json
from pathlib import Path


SCHEMA_V1 = "A1_STRATEGY_v1"
SCHEMA_V2 = "A1_STRATEGY_v2"
SUPPORTED_SCHEMAS = {SCHEMA_V1, SCHEMA_V2}
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

ALLOWED_SIM_FAMILIES = {"BASELINE", "BOUNDARY_SWEEP", "PERTURBATION", "ADVERSARIAL_NEG", "COMPOSITION_STRESS"}
ALLOWED_SIM_TIERS = {
    "T0_ATOM",
    "T1_COMPOUND",
    "T2_OPERATOR",
    "T3_STRUCTURE",
    "T4_SYSTEM_SEGMENT",
    "T5_ENGINE",
    "T6_WHOLE_SYSTEM",
}
ALLOWED_SUITE_KINDS = {
    "micro_suite",
    "mid_suite",
    "segment_suite",
    "engine_suite",
    "mega_suite",
    "failure_isolation",
    "graveyard_rescue",
    "replay_from_tape",
}
ALLOWED_FAILURE_POLICIES = {"stop_on_fail", "bisect_on_fail", "continue_collect"}

REQUIRED_ROOT_FIELDS_V1 = {
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
REQUIRED_ROOT_FIELDS_V2 = REQUIRED_ROOT_FIELDS_V1 | {"sim_program"}
OPTIONAL_ROOT_FIELDS = {"target_terms", "family_terms", "admissibility"}

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
REQUIRED_SIM_PROGRAM_FIELDS = {"program_id", "mode", "replay_source", "mega_gate_policy", "stages"}
REQUIRED_SIM_STAGE_FIELDS = {
    "stage_id",
    "tier",
    "suite_kind",
    "families",
    "depends_on",
    "target_classes",
    "max_sims",
    "failure_policy",
}
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
REQUIRED_SIM_PLAN_FIELDS_V1 = {"sim_id", "binds_to"}
REQUIRED_SIM_PLAN_FIELDS_V2 = {"sim_id", "binds_to", "stage_id"}
_TIER_ORDER = {tier: index for index, tier in enumerate(sorted(ALLOWED_SIM_TIERS))}


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


def _candidate_def_field_map(candidate: dict) -> dict[str, str]:
    field_map: dict[str, str] = {}
    for row in candidate.get("def_fields", []):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).upper().strip()
        if not name:
            continue
        field_map[name] = str(row.get("value", "")).strip()
    return field_map


def _validate_sim_program(sim_program: object, errors: list[str]) -> dict[str, dict]:
    if not isinstance(sim_program, dict):
        errors.append("sim_program must be object")
        return {}

    for key in sorted(REQUIRED_SIM_PROGRAM_FIELDS - set(sim_program.keys())):
        errors.append(f"sim_program missing field: {key}")

    if sim_program.get("mode") != "staged":
        errors.append("sim_program.mode must be staged")
    if not isinstance(sim_program.get("program_id"), str) or not sim_program.get("program_id", "").strip():
        errors.append("sim_program.program_id must be non-empty string")
    if not isinstance(sim_program.get("replay_source"), str):
        errors.append("sim_program.replay_source must be string")
    if not isinstance(sim_program.get("mega_gate_policy"), str) or not sim_program.get("mega_gate_policy", "").strip():
        errors.append("sim_program.mega_gate_policy must be non-empty string")

    stages = sim_program.get("stages")
    if not isinstance(stages, list) or len(stages) < 1:
        errors.append("sim_program.stages must be non-empty list")
        return {}

    stage_map: dict[str, dict] = {}
    for index, stage in enumerate(stages):
        prefix = f"sim_program.stages[{index}]"
        if not isinstance(stage, dict):
            errors.append(f"{prefix} must be object")
            continue
        for key in sorted(REQUIRED_SIM_STAGE_FIELDS - set(stage.keys())):
            errors.append(f"{prefix} missing field: {key}")

        stage_id = str(stage.get("stage_id", "")).strip()
        if not stage_id:
            errors.append(f"{prefix}.stage_id must be non-empty string")
            continue
        if stage_id in stage_map:
            errors.append(f"{prefix}.stage_id must be unique")
            continue

        tier = str(stage.get("tier", "")).strip()
        suite_kind = str(stage.get("suite_kind", "")).strip()
        families = stage.get("families")
        depends_on = stage.get("depends_on")
        target_classes = stage.get("target_classes")
        max_sims = stage.get("max_sims")
        failure_policy = str(stage.get("failure_policy", "")).strip()

        if tier not in ALLOWED_SIM_TIERS:
            errors.append(f"{prefix}.tier must be one of {sorted(ALLOWED_SIM_TIERS)}")
        if suite_kind not in ALLOWED_SUITE_KINDS:
            errors.append(f"{prefix}.suite_kind must be one of {sorted(ALLOWED_SUITE_KINDS)}")
        if not isinstance(families, list) or not families:
            errors.append(f"{prefix}.families must be non-empty list")
        else:
            invalid = sorted({str(x) for x in families} - ALLOWED_SIM_FAMILIES)
            if invalid:
                errors.append(f"{prefix}.families has invalid values: {invalid}")
        if not isinstance(depends_on, list):
            errors.append(f"{prefix}.depends_on must be list")
        if not isinstance(target_classes, list) or not target_classes:
            errors.append(f"{prefix}.target_classes must be non-empty list")
        if not isinstance(max_sims, int) or max_sims < 0:
            errors.append(f"{prefix}.max_sims must be integer >= 0")
        if failure_policy not in ALLOWED_FAILURE_POLICIES:
            errors.append(f"{prefix}.failure_policy must be one of {sorted(ALLOWED_FAILURE_POLICIES)}")
        if tier == "T6_WHOLE_SYSTEM" and suite_kind != "mega_suite":
            errors.append(f"{prefix}.suite_kind must be mega_suite for T6_WHOLE_SYSTEM")
        if suite_kind == "mega_suite" and tier != "T6_WHOLE_SYSTEM":
            errors.append(f"{prefix}.tier must be T6_WHOLE_SYSTEM for mega_suite")

        stage_map[stage_id] = stage

    visiting: set[str] = set()
    visited: set[str] = set()

    def _visit(stage_id: str) -> None:
        if stage_id in visited or stage_id not in stage_map:
            return
        if stage_id in visiting:
            errors.append("sim_program.stages dependency graph must be acyclic")
            return
        visiting.add(stage_id)
        stage = stage_map[stage_id]
        deps = stage.get("depends_on", [])
        if not isinstance(deps, list):
            deps = []
        for dep in deps:
            dep_id = str(dep).strip()
            if not dep_id:
                continue
            dep_stage = stage_map.get(dep_id)
            if dep_stage is None:
                errors.append(f"sim_program.stages dependency missing stage: {dep_id}")
                continue
            if _TIER_ORDER.get(str(dep_stage.get("tier", "")).strip(), -1) >= _TIER_ORDER.get(
                str(stage.get("tier", "")).strip(), -1
            ):
                errors.append(f"sim_program.stages dependency must point to lower tier: {dep_id}->{stage_id}")
            _visit(dep_id)
        visiting.remove(stage_id)
        visited.add(stage_id)

    for stage_id in sorted(stage_map.keys()):
        _visit(stage_id)

    return stage_map


def validate_strategy(strategy: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(strategy, dict):
        return ["strategy must be object"]

    schema = strategy.get("schema")
    required_root_fields = REQUIRED_ROOT_FIELDS_V2 if schema == SCHEMA_V2 else REQUIRED_ROOT_FIELDS_V1
    known_root_keys = REQUIRED_ROOT_FIELDS_V1 | REQUIRED_ROOT_FIELDS_V2 | OPTIONAL_ROOT_FIELDS
    unknown_root_keys = sorted(set(strategy.keys()) - known_root_keys)
    for key in unknown_root_keys:
        errors.append(f"unknown root field: {key}")
    for key in sorted(required_root_fields - set(strategy.keys())):
        errors.append(f"missing root field: {key}")
    if schema not in SUPPORTED_SCHEMAS:
        errors.append(f"schema must be one of {sorted(SUPPORTED_SCHEMAS)}")

    if "target_terms" in strategy and not isinstance(strategy.get("target_terms"), list):
        errors.append("target_terms must be list when present")
    if "family_terms" in strategy and not isinstance(strategy.get("family_terms"), list):
        errors.append("family_terms must be list when present")
    if "admissibility" in strategy and not isinstance(strategy.get("admissibility"), dict):
        errors.append("admissibility must be object when present")

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

    stage_map: dict[str, dict] = {}
    if schema == SCHEMA_V2:
        stage_map = _validate_sim_program(strategy.get("sim_program"), errors)

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
                required_sim_plan_fields = REQUIRED_SIM_PLAN_FIELDS_V2 if schema == SCHEMA_V2 else REQUIRED_SIM_PLAN_FIELDS_V1
                for key in sorted(required_sim_plan_fields - set(row.keys())):
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

    if schema == SCHEMA_V2:
        candidate_map: dict[str, dict] = {}
        for candidate in (targets if isinstance(targets, list) else []):
            if isinstance(candidate, dict) and isinstance(candidate.get("id"), str):
                candidate_map[candidate["id"]] = candidate
        for candidate in (alternatives if isinstance(alternatives, list) else []):
            if isinstance(candidate, dict) and isinstance(candidate.get("id"), str):
                candidate_map[candidate["id"]] = candidate

        for lane in ["positive", "negative"]:
            plan = sims.get(lane, []) if isinstance(sims, dict) else []
            if not isinstance(plan, list):
                continue
            for i, row in enumerate(plan):
                if not isinstance(row, dict):
                    continue
                bind_id = str(row.get("binds_to", "")).strip()
                stage_id = str(row.get("stage_id", "")).strip()
                if bind_id and bind_id not in candidate_map:
                    errors.append(f"sims.{lane}[{i}].binds_to must reference a target/alternative id")
                    continue
                if stage_id and stage_id not in stage_map:
                    errors.append(f"sims.{lane}[{i}].stage_id must reference sim_program.stages")
                    continue
                candidate = candidate_map.get(bind_id)
                if not isinstance(candidate, dict):
                    continue
                if str(candidate.get("kind", "")).upper() != "SIM_SPEC":
                    errors.append(f"sims.{lane}[{i}].binds_to must reference SIM_SPEC candidate")
                    continue
                field_map = _candidate_def_field_map(candidate)
                for required_name in ["TIER", "FAMILY", "TARGET_CLASS", "PROBE_TERM"]:
                    if not field_map.get(required_name, "").strip():
                        errors.append(f"{lane} candidate {bind_id} missing SIM_SPEC def_field {required_name}")
                stage = stage_map.get(stage_id)
                if not isinstance(stage, dict):
                    continue
                candidate_tier = field_map.get("TIER", "").strip()
                candidate_family = field_map.get("FAMILY", "").strip()
                candidate_target_class = field_map.get("TARGET_CLASS", "").strip()
                if candidate_tier and candidate_tier != str(stage.get("tier", "")).strip():
                    errors.append(f"{lane} candidate {bind_id} tier must match stage {stage_id}")
                stage_families = {str(x).strip() for x in stage.get("families", []) if str(x).strip()}
                if candidate_family and candidate_family not in stage_families:
                    errors.append(f"{lane} candidate {bind_id} family must be allowed by stage {stage_id}")
                stage_target_classes = {str(x).strip() for x in stage.get("target_classes", []) if str(x).strip()}
                if candidate_target_class and stage_target_classes and candidate_target_class not in stage_target_classes:
                    errors.append(f"{lane} candidate {bind_id} target class must be allowed by stage {stage_id}")
                if lane == "negative" and "ADVERSARIAL_NEG" not in stage_families:
                    errors.append(f"sims.{lane}[{i}].stage_id must allow ADVERSARIAL_NEG")

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
