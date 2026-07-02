#!/usr/bin/env python3
"""Validate the foundation role registry.

This is an audit helper, not a formal admission gate. It checks that the
machine-readable foundation registry keeps thesis, constraints, gates, sims,
and receipts separated.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parent
REGISTRY = ROOT / "foundation_role_registry_20260523.json"
SCHEMA = ROOT / "foundation_role_registry_schema_20260523.json"
PROCESS_SPEC = ROOT / "foundation_operational_process_spec_20260523.json"
RESULT_DIR = ROOT / "results"
OUT = RESULT_DIR / "foundation_role_registry_validation_results.json"

ALLOWED_ROLES = {"TH", "RC", "DC", "CF", "PL", "EG", "SIM", "REC", "OBJ", "REL", "MC", "GR"}
FORBIDDEN_STATUS = {"axiomatically_true", "axiom", "proved_by_axiom"}
REQUIRED_BY_ROLE = {
    "TH": {"code", "role", "name", "statement", "finite_translation", "thesis_kind", "status"},
    "RC": {"code", "role", "name", "statement", "forbidden_primitive", "cs_form", "qit_math_form", "process_form", "status"},
    "DC": {
        "code",
        "role",
        "name",
        "root_pressure",
        "forbidden_primitive",
        "cs_form",
        "qit_math_form",
        "process_form",
        "derivation_note",
        "derivation_status",
        "status",
    },
    "CF": {
        "code",
        "role",
        "name",
        "root_pressure",
        "forbidden_primitive",
        "cs_form",
        "qit_math_form",
        "process_form",
        "gate_needed",
        "required_gate",
        "gate_implemented",
        "claim_ceiling",
        "status",
    },
    "PL": {"code", "role", "name", "statement", "root_pressure", "status"},
    "EG": {
        "code",
        "role",
        "name",
        "enforces",
        "positive_case",
        "negative_case",
        "boundary_case",
        "observable",
        "pass_threshold",
        "fail_threshold",
        "claim_ceiling",
        "gate_implemented",
        "receipt_id",
    },
    "SIM": {
        "code",
        "role",
        "name",
        "enforces",
        "implementation_path",
        "uncertainty_variable",
        "status",
        "claim_ceiling",
    },
    "REC": {
        "code",
        "role",
        "name",
        "sim",
        "gate",
        "result_path",
        "claim_ceiling",
        "receipt_id",
        "status",
        "ceiling_kind",
        "ceiling_reason",
        "lift_condition",
    },
    "OBJ": {"code", "role", "name", "statement", "root_pressure", "status"},
    "REL": {"code", "role", "name", "statement", "source_role", "target_role", "semantic_smuggling_risk", "status"},
    "MC": {
        "code",
        "role",
        "display_code",
        "name",
        "statement",
        "built_from",
        "is_emergent_surface",
        "is_final_ontology",
        "derived_from_snapshot_id",
        "archived_predecessors",
        "status",
    },
    "GR": {"code", "role", "name", "killed_code", "reason", "receipt_id", "status"},
}


def load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    registry = load_registry()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    process_spec = json.loads(PROCESS_SPEC.read_text(encoding="utf-8"))
    items = registry.get("items", [])
    codes = [item.get("code") for item in items]
    duplicate_codes = sorted({code for code in codes if codes.count(code) > 1})
    violations: list[dict[str, Any]] = []

    try:
        jsonschema.validate(registry, schema)
    except jsonschema.ValidationError as exc:
        violations.append(
            {
                "code": "<registry>",
                "kind": "json_schema_validation_failed",
                "message": exc.message,
                "path": list(exc.absolute_path),
            }
        )

    for key in schema.get("required", []):
        if key not in registry:
            violations.append({"code": "<registry>", "kind": "missing_top_level_schema_field", "field": key})

    expected_schema = schema.get("properties", {}).get("schema", {}).get("const")
    if expected_schema and registry.get("schema") != expected_schema:
        violations.append(
            {
                "code": "<registry>",
                "kind": "schema_const_mismatch",
                "expected": expected_schema,
                "observed": registry.get("schema"),
            }
        )

    for item in items:
        code = item.get("code", "<missing>")
        role = item.get("role")
        if role not in ALLOWED_ROLES:
            violations.append({"code": code, "kind": "invalid_role", "role": role})
            continue

        required = REQUIRED_BY_ROLE.get(role, {"code", "role", "name"})
        missing = sorted(required - set(item))
        if missing:
            violations.append({"code": code, "kind": "missing_required_fields", "fields": missing})

        for status_field in ("status", "formal_status"):
            if status_field not in item:
                continue
            status = str(item.get(status_field, "")).lower()
            if status in FORBIDDEN_STATUS:
                violations.append({"code": code, "kind": "forbidden_axiom_status", "field": status_field, "status": status})
            elif item.get(status_field) and item.get(status_field) not in registry.get("status_ladder", []):
                violations.append(
                    {
                        "code": code,
                        "kind": "status_not_in_ladder",
                        "field": status_field,
                        "status": item.get(status_field),
                    }
                )

        if role == "TH" and item.get("status") in {"accepted_constraint", "passed_under_ceiling"}:
            violations.append({"code": code, "kind": "thesis_marked_enforced"})
        if role == "TH" and item.get("thesis_kind") not in registry.get("allowed_thesis_kinds", []):
            violations.append({"code": code, "kind": "thesis_kind_not_allowed", "thesis_kind": item.get("thesis_kind")})

        if role == "CF" and item.get("status") == "accepted_constraint":
            violations.append({"code": code, "kind": "candidate_fence_marked_accepted"})

        if role == "EG" and item.get("status") in {"receipted", "passed_under_ceiling"}:
            violations.append({"code": code, "kind": "gate_confused_with_receipt"})
        if role == "EG" and item.get("gate_implemented") is True and not item.get("receipt_id"):
            violations.append({"code": code, "kind": "implemented_gate_missing_receipt_id"})
        if role == "EG" and item.get("gate_implemented") is not True:
            if not item.get("coverage_status") or "gap" not in item:
                violations.append({"code": code, "kind": "unimplemented_gate_missing_coverage_status"})
        if role == "EG" and len(item.get("enforces", []) or []) > 1:
            mapping = item.get("enforces_observables")
            if not isinstance(mapping, dict):
                violations.append({"code": code, "kind": "aggregate_gate_missing_enforces_observables"})
            else:
                for target in item.get("enforces", []):
                    if target not in mapping:
                        violations.append(
                            {
                                "code": code,
                                "kind": "aggregate_gate_missing_target_observable",
                                "target": target,
                            }
                        )
                observable_values = list(mapping.values())
                duplicated_observables = sorted({value for value in observable_values if observable_values.count(value) > 1})
                if duplicated_observables:
                    violations.append(
                        {
                            "code": code,
                            "kind": "aggregate_gate_duplicate_target_observable",
                            "observables": duplicated_observables,
                        }
                    )
        if role == "SIM":
            for target in item.get("enforces", []) or []:
                if isinstance(target, str) and not target.startswith("EG-"):
                    violations.append({"code": code, "kind": "sim_enforces_non_gate_target", "target": target})
        if role == "MC":
            if item.get("is_emergent_surface") is not True or item.get("is_final_ontology") is not False:
                violations.append(
                    {
                        "code": code,
                        "kind": "mc_surface_flags_invalid",
                        "is_emergent_surface": item.get("is_emergent_surface"),
                        "is_final_ontology": item.get("is_final_ontology"),
                    }
                )
            if not item.get("derived_from_snapshot_id"):
                violations.append({"code": code, "kind": "mc_missing_derived_from_snapshot_id"})

    code_set = {str(code) for code in codes}
    for item in items:
        if item.get("role") != "MC":
            continue
        code = item.get("code", "<missing>")
        for target in item.get("built_from", []) or []:
            if target not in code_set:
                violations.append(
                    {
                        "code": code,
                        "kind": "mc_built_from_non_registry_code",
                        "target": target,
                    }
                )

    receipt_by_gate = {item.get("gate"): item for item in items if item.get("role") == "REC"}
    gates_by_code = {item.get("code"): item for item in items if item.get("role") == "EG"}
    for item in items:
        if item.get("role") != "CF":
            continue
        code = item.get("code", "<missing>")
        required_gate = item.get("required_gate")
        gate = gates_by_code.get(required_gate)
        if not gate:
            violations.append({"code": code, "kind": "candidate_fence_missing_required_gate", "required_gate": required_gate})
        elif code not in (gate.get("enforces") or []):
            violations.append(
                {
                    "code": code,
                    "kind": "candidate_fence_gate_does_not_enforce_candidate",
                    "required_gate": required_gate,
                }
            )

    cf_required_gates = {item.get("code"): item.get("required_gate") for item in items if item.get("role") == "CF"}
    priority_map = {
        row.get("code"): row.get("next_gate")
        for row in process_spec.get("candidate_fence_priorities", [])
        if isinstance(row, dict)
    }
    for cf_code, required_gate in cf_required_gates.items():
        if priority_map.get(cf_code) != required_gate:
            violations.append(
                {
                    "code": cf_code,
                    "kind": "candidate_fence_priority_mismatch",
                    "required_gate": required_gate,
                    "priority_next_gate": priority_map.get(cf_code),
                }
            )
    for cf_code in sorted(set(priority_map) - set(cf_required_gates)):
        violations.append({"code": cf_code, "kind": "candidate_fence_priority_unknown_code"})

    alias_owner: dict[str, str] = {}
    for item in items:
        code = str(item.get("code"))
        for alias in item.get("aliases", []) or []:
            if alias in code_set:
                violations.append({"code": code, "kind": "alias_reuses_registry_code", "alias": alias})
            if alias in alias_owner and alias_owner[alias] != code:
                violations.append(
                    {
                        "code": code,
                        "kind": "alias_reused_by_multiple_items",
                        "alias": alias,
                        "first_owner": alias_owner[alias],
                    }
                )
            alias_owner[alias] = code
    list_ref_fields = {"root_pressure", "enforces", "maps_to", "gated_by", "pending_gates"}
    scalar_ref_fields = {"sim", "gate", "required_gate", "admission_gate", "receipt_id"}
    for item in items:
        code = item.get("code", "<missing>")
        for field in list_ref_fields:
            for target in item.get(field, []) or []:
                if isinstance(target, str) and target.startswith(("TH-", "RC-", "DC-", "CF-", "PL-", "EG-", "SIM-", "REC-", "OBJ-", "REL-", "MC-")) and target not in code_set:
                    violations.append({"code": code, "kind": "dangling_reference", "field": field, "target": target})
                if field == "root_pressure" and isinstance(target, str) and target.startswith("CF-"):
                    violations.append({"code": code, "kind": "candidate_fence_used_as_root_pressure", "target": target})
        for field in scalar_ref_fields:
            target = item.get(field)
            if isinstance(target, str) and target.startswith(("TH-", "RC-", "DC-", "CF-", "PL-", "EG-", "SIM-", "REC-", "OBJ-", "REL-", "MC-")) and target not in code_set:
                violations.append({"code": code, "kind": "dangling_reference", "field": field, "target": target})
            if item.get("role") == "REL" and field == "required_gate" and isinstance(target, str):
                if target.startswith("EG-") and target not in code_set:
                    violations.append({"code": code, "kind": "rel_required_gate_missing_eg", "target": target})
                elif not target.startswith("EG-") and target not in registry.get("allowed_process_gate_placeholders", []):
                    violations.append({"code": code, "kind": "rel_required_gate_unknown_process_placeholder", "target": target})

    for item in items:
        if item.get("role") != "REC":
            continue
        result_path = item.get("result_path")
        if isinstance(result_path, str) and result_path:
            path = pathlib.Path(result_path)
            if not path.is_absolute():
                path = ROOT.parents[2] / path
            if not path.exists():
                violations.append({"code": item.get("code"), "kind": "receipt_result_path_missing", "result_path": result_path})

    for item in items:
        if item.get("role") != "EG":
            continue
        mapping = item.get("enforces_observables")
        receipt = receipt_by_gate.get(item.get("code"))
        if not isinstance(mapping, dict) or not receipt:
            continue
        result_path = receipt.get("result_path")
        if not isinstance(result_path, str):
            continue
        path = pathlib.Path(result_path)
        if not path.is_absolute():
            path = ROOT.parents[2] / path
        if not path.exists():
            continue
        try:
            result_payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            violations.append({"code": receipt.get("code"), "kind": "receipt_json_decode_failed", "message": str(exc)})
            continue
        gate_sections = result_payload.get("gates")
        if isinstance(gate_sections, dict):
            for target, observable in mapping.items():
                if observable not in gate_sections:
                    violations.append(
                        {
                            "code": item.get("code"),
                            "kind": "aggregate_gate_observable_missing_from_receipt",
                            "target": target,
                            "observable": observable,
                            "receipt": receipt.get("code"),
                        }
                    )

    enforced_targets = {
        target
        for item in items
        if item.get("role") == "EG"
        for target in item.get("enforces", [])
    }
    for item in items:
        if item.get("role") in {"RC", "DC"} and item.get("status") == "accepted_constraint":
            if item.get("code") not in enforced_targets and not item.get("gated_by"):
                violations.append({"code": item.get("code"), "kind": "accepted_constraint_without_registered_gate"})

    role_counts: dict[str, int] = {}
    for item in items:
        role = str(item.get("role"))
        role_counts[role] = role_counts.get(role, 0) + 1

    declared_counters = registry.get("counters", {})
    counter_mismatches = []
    for role, observed in sorted(role_counts.items()):
        declared = declared_counters.get(role)
        if declared != observed:
            counter_mismatches.append({"role": role, "declared": declared, "observed": observed})
    for role, declared in sorted(declared_counters.items()):
        if role not in role_counts and declared != 0:
            counter_mismatches.append({"role": role, "declared": declared, "observed": 0})
    for mismatch in counter_mismatches:
        violations.append({"code": "<registry>", "kind": "counter_mismatch", **mismatch})

    gate_coverage = registry.get("gate_coverage", {})
    observed_total_eg = sum(1 for item in items if item.get("role") == "EG")
    observed_implemented_eg = sum(1 for item in items if item.get("role") == "EG" and item.get("gate_implemented") is True)
    accepted_targets = [
        item
        for item in items
        if item.get("role") in {"RC", "DC"} and item.get("status") == "accepted_constraint"
    ]
    cf_targets = [item for item in items if item.get("role") == "CF"]
    cf_targets_receipted = sum(1 for item in cf_targets if item.get("gate_implemented") is True and item.get("receipt_id"))
    expected_gate_coverage = {
        "eg_rows": {
            "implemented": observed_implemented_eg,
            "total": observed_total_eg,
            "unimplemented": observed_total_eg - observed_implemented_eg,
        },
        "constraint_targets": {
            "accepted_rc_dc_targets": len(accepted_targets),
            "accepted_rc_dc_targets_receipted_by_aggregate": len(accepted_targets),
            "candidate_cf_targets": len(cf_targets),
            "candidate_cf_targets_with_gate_receipts": cf_targets_receipted,
        },
        "note": gate_coverage.get("note"),
        "candidate_note": gate_coverage.get("candidate_note"),
    }
    if gate_coverage != expected_gate_coverage:
        violations.append(
            {
                "code": "<registry>",
                "kind": "gate_coverage_mismatch",
                "declared": gate_coverage,
                "observed": expected_gate_coverage,
            }
        )

    result = {
        "schema": "foundation_role_registry_validation_v1",
        "registry": str(REGISTRY),
        "registry_schema": str(SCHEMA),
        "all_pass": not duplicate_codes and not violations,
        "item_count": len(items),
        "role_counts": role_counts,
        "declared_counters": declared_counters,
        "duplicate_codes": duplicate_codes,
        "violations": violations,
        "checks": {
            "roles_separated": not any(v["kind"] == "invalid_role" for v in violations),
            "forbidden_axiom_status_checked": not any(v["kind"] == "forbidden_axiom_status" for v in violations),
            "candidate_fence_not_accepted_checked": not any(v["kind"] == "candidate_fence_marked_accepted" for v in violations),
            "thesis_not_marked_enforced_checked": not any(v["kind"] == "thesis_marked_enforced" for v in violations),
            "thesis_kind_enum_checked": not any(v["kind"] == "thesis_kind_not_allowed" for v in violations),
            "gate_not_receipt_checked": not any(v["kind"] == "gate_confused_with_receipt" for v in violations),
            "implemented_gate_receipt_id_checked": not any(
                v["kind"] == "implemented_gate_missing_receipt_id" for v in violations
            ),
            "unimplemented_gate_coverage_status_checked": not any(
                v["kind"] == "unimplemented_gate_missing_coverage_status" for v in violations
            ),
            "sim_to_gate_only_checked": not any(v["kind"] == "sim_enforces_non_gate_target" for v in violations),
            "mc_surface_flags_checked": not any(v["kind"] == "mc_surface_flags_invalid" for v in violations),
            "mc_snapshot_derivation_checked": not any(v["kind"] == "mc_missing_derived_from_snapshot_id" for v in violations),
            "mc_built_from_registry_codes_checked": not any(
                v["kind"] == "mc_built_from_non_registry_code" for v in violations
            ),
            "receipt_paths_exist_checked": not any(v["kind"] == "receipt_result_path_missing" for v in violations),
            "aggregate_observables_exist_in_receipts_checked": not any(
                v["kind"] == "aggregate_gate_observable_missing_from_receipt" for v in violations
            ),
            "top_level_schema_required_fields_checked": not any(v["kind"] == "missing_top_level_schema_field" for v in violations),
            "json_schema_checked": not any(v["kind"] == "json_schema_validation_failed" for v in violations),
            "cross_references_checked": not any(v["kind"] == "dangling_reference" for v in violations),
            "root_pressure_excludes_candidate_fences_checked": not any(
                v["kind"] == "candidate_fence_used_as_root_pressure" for v in violations
            ),
            "rel_required_gate_placeholders_checked": not any(
                v["kind"].startswith("rel_required_gate_") for v in violations
            ),
            "accepted_constraints_have_registered_gates_checked": not any(
                v["kind"] == "accepted_constraint_without_registered_gate" for v in violations
            ),
            "status_ladder_checked": not any(v["kind"] == "status_not_in_ladder" for v in violations),
            "gate_coverage_checked": not any(v["kind"] == "gate_coverage_mismatch" for v in violations),
            "alias_reuse_checked": not any(v["kind"].startswith("alias_") for v in violations),
            "candidate_fence_gate_mapping_checked": not any(
                v["kind"].startswith("candidate_fence_") for v in violations
            ),
            "candidate_fence_priorities_match_required_gates_checked": not any(
                v["kind"].startswith("candidate_fence_priority_") for v in violations
            ),
            "aggregate_gate_observable_mapping_checked": not any(
                v["kind"].startswith("aggregate_gate_") for v in violations
            ),
        },
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "out": str(OUT)}, indent=2))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
