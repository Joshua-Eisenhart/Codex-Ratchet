#!/usr/bin/env python3
"""Fail-closed structural validator for Ratchet Card v1.

A green result validates process honesty only. It never admits the card's
scientific claim.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_ID = "codex_ratchet.ratchet_card.v1"
ROOT_PRIMITIVE = "constrained_distinction_records"
DELTA_CODOMAIN = {
    "DISTINGUISHABLE",
    "INDISTINGUISHABLE",
    "UNRESOLVED",
}
CONTROL_CLASSES = {
    "lower_structure",
    "representation",
    "order_erasure",
    "history_erasure",
    "wrong_structure",
    "anti_tautology",
    "held_out",
    "boundary",
    "alternate_attempt_family",
    "integrity",
    "preorder_variant",
    "update_family_variant",
    "generator_variant",
}
CLASSIFICATIONS = {
    "process_proposal",
    "scratch_diagnostic",
    "ratchet_survivor",
    "rejected",
    "superseded",
}
DECISIONS = {
    "UNRUN",
    "ACCEPT_PROVISIONAL",
    "PARK",
    "REJECT",
    "GRAVEYARD_KEEP",
    "SUPERSEDED_BY_WEAKER",
}
TOP_LEVEL_FIELDS = {
    "schema",
    "card_id",
    "classification",
    "promotion_allowed",
    "formal_admission_allowed",
    "source_manifest",
    "claim",
    "root_record",
    "constraints",
    "predecessor_receipts",
    "candidate_search",
    "mss",
    "earned_structures",
    "co_views",
    "recursive_loop",
    "controls",
    "independent_recomputation",
    "fabrication_audit",
    "decision",
    "blocked_consumers",
    "next_obligation",
    "ca_hypothesis",
    "receipts",
}
REPO = Path(__file__).resolve().parents[3]


def _require(mapping: dict[str, Any], keys: set[str], path: str, errors: list[str]) -> None:
    missing = keys - set(mapping)
    if missing:
        errors.append(f"{path}: missing fields {sorted(missing)}")


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def validate_card(card: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(card) != TOP_LEVEL_FIELDS:
        missing = TOP_LEVEL_FIELDS - set(card)
        extra = set(card) - TOP_LEVEL_FIELDS
        errors.append(f"card: closed schema mismatch missing={sorted(missing)} extra={sorted(extra)}")
        return errors

    if card["schema"] != SCHEMA_ID:
        errors.append("schema: wrong schema id")
    if not isinstance(card["card_id"], str) or not card["card_id"]:
        errors.append("card_id: non-empty string required")
    if card["classification"] not in CLASSIFICATIONS:
        errors.append("classification: unknown classification")

    manifests = card["source_manifest"]
    if not isinstance(manifests, list) or not manifests:
        errors.append("source_manifest: at least one source is required")
    else:
        for index, item in enumerate(manifests):
            if not isinstance(item, dict):
                errors.append(f"source_manifest[{index}]: object required")
                continue
            _require(item, {"path", "sha256", "role"}, f"source_manifest[{index}]", errors)
            if "sha256" in item and not _is_sha256(item["sha256"]):
                errors.append(f"source_manifest[{index}].sha256: invalid sha256")
            source_path = item.get("path")
            if isinstance(source_path, str) and source_path:
                path = Path(source_path)
                resolved = path if path.is_absolute() else REPO / path
                if not resolved.is_file():
                    errors.append(f"source_manifest[{index}].path: file not found")
                elif _is_sha256(item.get("sha256")):
                    actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
                    if actual != item["sha256"]:
                        errors.append(f"source_manifest[{index}].sha256: source hash mismatch")

    receipt_hashes: set[str] = set()
    receipt_paths_by_hash: dict[str, Path] = {}
    receipts = card["receipts"]
    if not isinstance(receipts, list):
        errors.append("receipts: array required")
        receipts = []
    for index, item in enumerate(receipts):
        if not isinstance(item, dict):
            errors.append(f"receipts[{index}]: object required")
            continue
        _require(item, {"path", "sha256", "kind"}, f"receipts[{index}]", errors)
        receipt_hash = item.get("sha256")
        receipt_path = item.get("path")
        if not _is_sha256(receipt_hash):
            errors.append(f"receipts[{index}].sha256: invalid sha256")
            continue
        if not isinstance(receipt_path, str) or not receipt_path:
            errors.append(f"receipts[{index}].path: non-empty path required")
            continue
        resolved = Path(receipt_path)
        resolved = resolved if resolved.is_absolute() else REPO / resolved
        if not resolved.is_file():
            errors.append(f"receipts[{index}].path: file not found")
            continue
        actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
        if actual != receipt_hash:
            errors.append(f"receipts[{index}].sha256: receipt hash mismatch")
            continue
        if receipt_hash in receipt_paths_by_hash and receipt_paths_by_hash[receipt_hash] != resolved:
            errors.append(f"receipts[{index}].sha256: duplicate hash bound to different paths")
            continue
        receipt_hashes.add(receipt_hash)
        receipt_paths_by_hash[receipt_hash] = resolved

    source_hashes = {
        item.get("sha256")
        for item in manifests
        if isinstance(item, dict) and _is_sha256(item.get("sha256"))
    }

    predecessors = card["predecessor_receipts"]
    if not isinstance(predecessors, list):
        errors.append("predecessor_receipts: array required")
        predecessors = []
    for index, item in enumerate(predecessors):
        if not isinstance(item, dict):
            errors.append(f"predecessor_receipts[{index}]: object required")
            continue
        _require(item, {"path", "sha256", "role"}, f"predecessor_receipts[{index}]", errors)
        path_value = item.get("path")
        hash_value = item.get("sha256")
        if not isinstance(path_value, str) or not path_value:
            errors.append(f"predecessor_receipts[{index}].path: non-empty path required")
            continue
        resolved = Path(path_value)
        resolved = resolved if resolved.is_absolute() else REPO / resolved
        if not resolved.is_file():
            errors.append(f"predecessor_receipts[{index}].path: file not found")
        elif not _is_sha256(hash_value):
            errors.append(f"predecessor_receipts[{index}].sha256: invalid sha256")
        elif hashlib.sha256(resolved.read_bytes()).hexdigest() != hash_value:
            errors.append(f"predecessor_receipts[{index}].sha256: receipt hash mismatch")

    claim = card["claim"]
    _require(
        claim,
        {"exact_text", "scope", "ceiling", "demotion_conditions", "required_earned_structures"},
        "claim",
        errors,
    )
    if not claim.get("demotion_conditions"):
        errors.append("claim.demotion_conditions: at least one condition required")
    required_structures = claim.get("required_earned_structures", [])
    if not isinstance(required_structures, list):
        errors.append("claim.required_earned_structures: array required")
        required_structures = []

    root = card["root_record"]
    _require(
        root,
        {
            "primitive",
            "marks_are_objects",
            "finite_marks",
            "finite_distinction_attempts",
            "finite_history_prefix",
            "delta_codomain",
            "probe_family_earned",
            "equivalence_relation_earned",
        },
        "root_record",
        errors,
    )
    if root.get("primitive") != ROOT_PRIMITIVE:
        errors.append("root_record.primitive: must be constrained_distinction_records")
    if root.get("marks_are_objects") is not False:
        errors.append("root_record.marks_are_objects: root marks cannot be primitive objects")
    if set(root.get("delta_codomain", [])) != DELTA_CODOMAIN:
        errors.append("root_record.delta_codomain: exact trivalent codomain required")
    if root.get("probe_family_earned") not in {True, False}:
        errors.append("root_record.probe_family_earned: boolean required")
    if root.get("equivalence_relation_earned") not in {True, False}:
        errors.append("root_record.equivalence_relation_earned: boolean required")
    for key in ("finite_marks", "finite_distinction_attempts", "finite_history_prefix"):
        if root.get(key) is not True:
            errors.append(f"root_record.{key}: must be true")

    constraints = card["constraints"]
    _require(constraints, {"F01", "N01", "supplied_structures"}, "constraints", errors)
    if not constraints.get("F01", {}).get("finite_realization"):
        errors.append("constraints.F01.finite_realization: must be true")
    n01 = constraints.get("N01", {})
    if not n01.get("typed_same_start_required") or not n01.get("future_effect_required"):
        errors.append("constraints.N01: typed same-start and future-effect requirements must be true")

    search = card["candidate_search"]
    _require(
        search,
        {
            "universe_model",
            "generator",
            "generator_variants",
            "candidate_families",
            "breadth_justification",
            "coverage_claim",
            "stop_rule",
            "sealed_target_suite_sha256",
            "unsearched_region",
        },
        "candidate_search",
        errors,
    )
    if not isinstance(search.get("candidate_families"), list) or len(search["candidate_families"]) < 3:
        errors.append("candidate_search.candidate_families: at least three rival families required")
    if not isinstance(search.get("generator_variants"), list) or len(search["generator_variants"]) < 2:
        errors.append("candidate_search.generator_variants: at least two variants required")
    for field in ("universe_model", "generator", "breadth_justification", "coverage_claim", "stop_rule"):
        if not isinstance(search.get(field), str) or not search[field].strip():
            errors.append(f"candidate_search.{field}: non-empty string required")
    if not _is_sha256(search.get("sealed_target_suite_sha256")):
        errors.append("candidate_search.sealed_target_suite_sha256: valid sha256 required")
    elif search.get("sealed_target_suite_sha256") not in source_hashes | receipt_hashes:
        errors.append("candidate_search.sealed_target_suite_sha256: hash must resolve to a source or receipt")
    if not search.get("unsearched_region"):
        errors.append("candidate_search.unsearched_region: uncertainty must be explicit")

    mss = card["mss"]
    _require(
        mss,
        {
            "weakness_preorder",
            "preorder_variants",
            "update_family_variants",
            "plural_minima_allowed",
            "frontier",
            "robust_core",
            "sensitivity_union",
            "empty_frontier_outcome",
            "frontier_execution_rule",
            "defeasible",
            "weaker_candidate_demotion",
        },
        "mss",
        errors,
    )
    preorder = mss.get("weakness_preorder", {})
    _require(preorder, {"definition", "status", "version"}, "mss.weakness_preorder", errors)
    if preorder.get("status") != "installed_and_defeasible":
        errors.append("mss.weakness_preorder.status: must be installed_and_defeasible")
    if mss.get("plural_minima_allowed") is not True:
        errors.append("mss.plural_minima_allowed: must be true")
    if mss.get("defeasible") is not True or mss.get("weaker_candidate_demotion") is not True:
        errors.append("mss: defeasibility and weaker-candidate demotion are mandatory")
    if not isinstance(mss.get("preorder_variants"), list) or len(mss["preorder_variants"]) < 2:
        errors.append("mss.preorder_variants: at least two variants required")
    if not isinstance(mss.get("update_family_variants"), list) or len(mss["update_family_variants"]) < 2:
        errors.append("mss.update_family_variants: at least two variants required")
    if mss.get("empty_frontier_outcome") != "NO_SURVIVOR_BLOCKS_ADMISSION":
        errors.append("mss.empty_frontier_outcome: fail-closed value required")
    if mss.get("frontier_execution_rule") != "FAN_OUT_ALL_UNLESS_REMOVED_BY_RECEIPT":
        errors.append("mss.frontier_execution_rule: plural fanout rule required")

    structures = card["earned_structures"]
    _require(
        structures,
        {"probe_family", "equivalence_relation", "quotient", "objects", "measure", "updates"},
        "earned_structures",
        errors,
    )
    for name, item in structures.items():
        if not isinstance(item, dict) or "status" not in item or "evidence" not in item:
            errors.append(f"earned_structures.{name}: status and evidence required")
            continue
        if item.get("status") not in {"UNRUN", "UNLICENSED", "PLANNED", "SUPPLIED"} and not item.get("evidence"):
            errors.append(f"earned_structures.{name}: non-empty evidence required for status {item.get('status')}")
        if item.get("status") == "EARNED":
            for evidence_hash in item.get("evidence", []):
                if evidence_hash not in receipt_hashes:
                    errors.append(f"earned_structures.{name}.evidence: unregistered receipt hash")
    unknown_required = set(required_structures) - set(structures)
    if unknown_required:
        errors.append(f"claim.required_earned_structures: unknown structures {sorted(unknown_required)}")
    if root.get("probe_family_earned") is True:
        item = structures.get("probe_family", {})
        if item.get("status") != "EARNED" or not item.get("evidence"):
            errors.append("root_record.probe_family_earned: true requires EARNED status with evidence")
    if root.get("equivalence_relation_earned") is True:
        item = structures.get("equivalence_relation", {})
        if item.get("status") != "EARNED" or not item.get("evidence"):
            errors.append("root_record.equivalence_relation_earned: true requires EARNED status with evidence")
        if root.get("probe_family_earned") is not True:
            errors.append("root_record.equivalence_relation_earned: requires an earned probe family")
    if structures.get("quotient", {}).get("status") == "EARNED" and root.get("equivalence_relation_earned") is not True:
        errors.append("earned_structures.quotient: requires earned equivalence relation")

    views = card["co_views"]
    _require(
        views,
        {"shared_boundary_id", "neither_view_prior", "geometry", "entropy", "admission_driven_by_views"},
        "co_views",
        errors,
    )
    if views.get("neither_view_prior") is not True:
        errors.append("co_views.neither_view_prior: must be true")
    if views.get("admission_driven_by_views") is not False:
        errors.append("co_views.admission_driven_by_views: views cannot self-admit")
    for name in ("geometry", "entropy"):
        view = views.get(name, {})
        _require(view, {"boundary_id", "type", "license", "recomputed", "receipt"}, f"co_views.{name}", errors)
        if view.get("boundary_id") != views.get("shared_boundary_id"):
            errors.append(f"co_views.{name}.boundary_id: must equal shared boundary")
        if view.get("recomputed") is not True:
            errors.append(f"co_views.{name}.recomputed: must be true")
        if view.get("receipt") is not None:
            if not _is_sha256(view.get("receipt")) or view.get("receipt") not in receipt_hashes:
                errors.append(f"co_views.{name}.receipt: must resolve through receipt registry")

    loop = card["recursive_loop"]
    _require(
        loop,
        {
            "passes_required",
            "passes_run",
            "raw_recomputation_required",
            "residual_returns_as_new_obligation",
            "obligation_generation_rule_sha256",
            "raw_record_sha256",
            "derived_cache_forbidden",
            "branch_rule",
        },
        "recursive_loop",
        errors,
    )
    if loop.get("passes_required", 0) < 2:
        errors.append("recursive_loop.passes_required: at least two passes required")
    if loop.get("raw_recomputation_required") is not True:
        errors.append("recursive_loop.raw_recomputation_required: must be true")
    if loop.get("residual_returns_as_new_obligation") is not True:
        errors.append("recursive_loop.residual_returns_as_new_obligation: must be true")
    if loop.get("derived_cache_forbidden") is not True:
        errors.append("recursive_loop.derived_cache_forbidden: must be true")
    if loop.get("branch_rule") != "RULE_CHANGE_OPENS_NEW_BRANCH":
        errors.append("recursive_loop.branch_rule: fail-closed branch rule required")
    for field in ("obligation_generation_rule_sha256", "raw_record_sha256"):
        if not _is_sha256(loop.get(field)):
            errors.append(f"recursive_loop.{field}: valid sha256 required")
        elif loop.get(field) not in source_hashes | receipt_hashes:
            errors.append(f"recursive_loop.{field}: hash must resolve to a source or receipt")

    controls = card["controls"]
    if not isinstance(controls, list):
        errors.append("controls: array required")
        controls = []
    seen = {item.get("class") for item in controls if isinstance(item, dict)}
    if seen != CONTROL_CLASSES:
        errors.append(f"controls: required classes mismatch missing={sorted(CONTROL_CLASSES-seen)} extra={sorted(seen-CONTROL_CLASSES)}")
    for index, item in enumerate(controls):
        if not isinstance(item, dict):
            errors.append(f"controls[{index}]: object required")
            continue
        _require(item, {"class", "status", "flip_expected", "receipt"}, f"controls[{index}]", errors)
        if item.get("status") == "PASS":
            receipt = item.get("receipt")
            if not isinstance(receipt, dict):
                errors.append(f"controls[{index}].receipt: structured receipt required for PASS")
            else:
                _require(receipt, {"sha256", "flip_observed"}, f"controls[{index}].receipt", errors)
                if not _is_sha256(receipt.get("sha256")):
                    errors.append(f"controls[{index}].receipt.sha256: invalid sha256")
                elif receipt.get("sha256") not in receipt_hashes:
                    errors.append(f"controls[{index}].receipt.sha256: unregistered receipt hash")
                if receipt.get("flip_observed") is not item.get("flip_expected"):
                    errors.append(f"controls[{index}].receipt.flip_observed: does not match expectation")
        elif item.get("status") == "PLANNED" and item.get("receipt") is not None:
            errors.append(f"controls[{index}].receipt: planned control cannot carry a result receipt")

    independent = card["independent_recomputation"]
    _require(independent, {"required_lanes", "completed_lanes", "agreement_receipt"}, "independent_recomputation", errors)
    required_lanes = independent.get("required_lanes", [])
    if not isinstance(required_lanes, list) or len(required_lanes) < 4:
        errors.append("independent_recomputation.required_lanes: Julia, JAX, PyTorch, and controller lanes required")
    else:
        for token in ("Julia", "JAX", "PyTorch", "controller"):
            if not any(token.lower() in str(lane).lower() for lane in required_lanes):
                errors.append(f"independent_recomputation.required_lanes: missing {token} lane")
    audit = card["fabrication_audit"]
    _require(audit, {"status", "fresh_context", "receipt"}, "fabrication_audit", errors)
    if independent.get("agreement_receipt") is not None:
        if not _is_sha256(independent.get("agreement_receipt")) or independent.get("agreement_receipt") not in receipt_hashes:
            errors.append("independent_recomputation.agreement_receipt: must resolve through receipt registry")
    if audit.get("receipt") is not None:
        if not _is_sha256(audit.get("receipt")) or audit.get("receipt") not in receipt_hashes:
            errors.append("fabrication_audit.receipt: must resolve through receipt registry")

    decision = card["decision"]
    _require(
        decision,
        {
            "status",
            "claim_ceiling",
            "receipt",
            "receipt_parent_hash",
            "mss_frontier_hash",
            "status_index_path",
            "status_index_sha256",
        },
        "decision",
        errors,
    )
    if decision.get("status") not in DECISIONS:
        errors.append("decision.status: unknown decision")
    if decision.get("receipt") is not None:
        if not _is_sha256(decision.get("receipt")) or decision.get("receipt") not in receipt_hashes:
            errors.append("decision.receipt: must resolve through receipt registry")

    if decision.get("status") == "ACCEPT_PROVISIONAL":
        if card.get("promotion_allowed") is not True or card.get("formal_admission_allowed") is not True:
            errors.append("decision: ACCEPT_PROVISIONAL requires both admission flags true")
        if not _is_sha256(decision.get("receipt")) or not _is_sha256(decision.get("receipt_parent_hash")):
            errors.append("decision: ACCEPT_PROVISIONAL requires receipt and parent sha256")
        if decision.get("receipt") not in receipt_hashes:
            errors.append("decision: ACCEPT_PROVISIONAL receipt must be registered and content-addressed")
        parent_hash = decision.get("receipt_parent_hash")
        if parent_hash != "0" * 64 and parent_hash not in receipt_hashes:
            errors.append("decision: ACCEPT_PROVISIONAL parent must be genesis or a registered receipt")
        frontier_hash = hashlib.sha256(
            json.dumps(mss.get("frontier"), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if not mss.get("frontier") or decision.get("mss_frontier_hash") != frontier_hash:
            errors.append("decision: ACCEPT_PROVISIONAL requires receipt and MSS frontier hash")
        status_index_hash = decision.get("status_index_sha256")
        if not decision.get("status_index_path") or status_index_hash not in receipt_hashes:
            errors.append("decision: ACCEPT_PROVISIONAL requires registered current-status index path and hash")
        elif receipt_paths_by_hash.get(status_index_hash) != (
            Path(decision["status_index_path"])
            if Path(decision["status_index_path"]).is_absolute()
            else REPO / decision["status_index_path"]
        ):
            errors.append("decision: current-status index path does not match registered receipt")
        if audit.get("status") != "PASS" or audit.get("fresh_context") is not True or not _is_sha256(audit.get("receipt")):
            errors.append("decision: ACCEPT_PROVISIONAL requires fresh fabrication audit PASS")
        elif audit.get("receipt") not in receipt_hashes:
            errors.append("decision: fabrication audit receipt must be registered")
        if set(independent.get("required_lanes", [])) - set(independent.get("completed_lanes", [])):
            errors.append("decision: ACCEPT_PROVISIONAL requires every independent lane")
        if not _is_sha256(independent.get("agreement_receipt")):
            errors.append("decision: ACCEPT_PROVISIONAL requires agreement receipt sha256")
        elif independent.get("agreement_receipt") not in receipt_hashes:
            errors.append("decision: independent agreement receipt must be registered")
        if loop.get("passes_run", 0) < loop.get("passes_required", 2):
            errors.append("decision: ACCEPT_PROVISIONAL requires all recursive passes")
        if card.get("classification") != "ratchet_survivor":
            errors.append("decision: ACCEPT_PROVISIONAL requires ratchet_survivor classification")
        if not required_structures:
            errors.append("decision: ACCEPT_PROVISIONAL requires explicit earned-structure dependencies")
        for name in required_structures:
            item = structures.get(name, {})
            if item.get("status") != "EARNED" or not item.get("evidence"):
                errors.append(f"decision: required structure {name} is not EARNED with evidence")
        for name in ("geometry", "entropy"):
            view = views.get(name, {})
            if str(view.get("license", "")).upper().startswith("UNLICENSED"):
                errors.append(f"decision: {name} view remains unlicensed")
            if view.get("receipt") not in receipt_hashes:
                errors.append(f"decision: {name} view requires a registered receipt")
        for item in controls:
            if item.get("status") != "PASS" or not item.get("receipt"):
                errors.append("decision: ACCEPT_PROVISIONAL requires every control PASS with receipt")
                break
    elif card.get("promotion_allowed") or card.get("formal_admission_allowed"):
        errors.append("decision: non-accepted cards cannot allow promotion or formal admission")

    ca = card["ca_hypothesis"]
    _require(ca, {"status", "alternatives", "required_gates"}, "ca_hypothesis", errors)
    if ca.get("status") not in {"candidate", "rejected", "accept_provisional"}:
        errors.append("ca_hypothesis.status: invalid status")
    if ca.get("status") == "candidate" and len(ca.get("alternatives", [])) < 3:
        errors.append("ca_hypothesis.alternatives: candidate CA requires at least three rival carriers")
    if ca.get("status") == "accept_provisional":
        if decision.get("status") != "ACCEPT_PROVISIONAL":
            errors.append("ca_hypothesis: accept_provisional requires card acceptance")
        if not ca.get("required_gates"):
            errors.append("ca_hypothesis: accept_provisional requires gates")

    if not isinstance(card["blocked_consumers"], list) or not card["blocked_consumers"]:
        errors.append("blocked_consumers: at least one blocked consumer required")
    if not isinstance(card["next_obligation"], str) or not card["next_obligation"]:
        errors.append("next_obligation: non-empty string required")
    return errors


def validate_file(path: Path) -> tuple[dict[str, Any], list[str]]:
    card = json.loads(path.read_text(encoding="utf-8"))
    return card, validate_card(card)


def mutation_selftest(card: dict[str, Any]) -> dict[str, bool]:
    mutations: dict[str, dict[str, Any]] = {}

    m = copy.deepcopy(card)
    m["root_record"]["marks_are_objects"] = True
    mutations["primitive_object_smuggle"] = m

    m = copy.deepcopy(card)
    m["co_views"]["entropy"]["boundary_id"] = "different_boundary"
    mutations["split_entropy_geometry_source"] = m

    m = copy.deepcopy(card)
    m["co_views"]["admission_driven_by_views"] = True
    mutations["entropy_or_geometry_self_admission"] = m

    m = copy.deepcopy(card)
    m["mss"]["weakness_preorder"]["status"] = "forced"
    mutations["forced_weakness_order"] = m

    m = copy.deepcopy(card)
    m["controls"] = [c for c in m["controls"] if c["class"] != "lower_structure"]
    mutations["missing_lower_structure_control"] = m

    m = copy.deepcopy(card)
    m["decision"]["status"] = "ACCEPT_PROVISIONAL"
    m["promotion_allowed"] = True
    m["formal_admission_allowed"] = True
    mutations["unreceipted_acceptance"] = m

    m = copy.deepcopy(card)
    m["root_record"]["probe_family_earned"] = True
    mutations["probe_earned_without_evidence"] = m

    m = copy.deepcopy(card)
    m["independent_recomputation"]["required_lanes"] = []
    mutations["empty_independent_lanes"] = m

    m = copy.deepcopy(card)
    m["candidate_search"]["candidate_families"] = ["one", "two"]
    mutations["narrow_candidate_search"] = m

    m = copy.deepcopy(card)
    m["ca_hypothesis"]["status"] = "accept_provisional"
    mutations["ca_self_promotion"] = m

    m = copy.deepcopy(card)
    m["source_manifest"][0]["sha256"] = "0" * 64
    mutations["source_hash_substitution"] = m

    m = copy.deepcopy(card)
    m["decision"]["status"] = "ACCEPT_PROVISIONAL"
    m["promotion_allowed"] = True
    m["formal_admission_allowed"] = True
    m["classification"] = "ratchet_survivor"
    m["claim"]["required_earned_structures"] = []
    mutations["acceptance_without_earned_dependencies"] = m

    return {name: bool(validate_card(mutated)) for name, mutated in mutations.items()}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("card", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()

    card, errors = validate_file(args.card)
    selftests = mutation_selftest(card) if args.selftest else {}
    all_pass = not errors and all(selftests.values())
    result = {
        "schema": "codex_ratchet.ratchet_card.validation.v1",
        "card": str(args.card),
        "card_sha256": hashlib.sha256(args.card.read_bytes()).hexdigest(),
        "classification": "controller_audit",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "errors": errors,
        "mutation_selftests": selftests,
        "all_pass": all_pass,
        "claim_ceiling": "closed-card process validation only; no scientific admission",
    }
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
