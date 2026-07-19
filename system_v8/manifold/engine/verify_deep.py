#!/usr/bin/env python3
"""Fail-closed semantic verification for every deep-manifold receipt."""

from __future__ import annotations

import argparse
import ast
import copy
import json
import re
from pathlib import Path
from typing import Any, Callable

from chirality_layer import compute_octonion_evidence
from common import canonical_json, digest, write_json
from connection_layer import (
    CANDIDATES as CONNECTION_CANDIDATES,
    expected_transport_tables,
    observed_inner_states,
    outer_admissible_states,
    state_key,
)
from history_layer import (
    CANDIDATES as HISTORY_CANDIDATES,
    compose_tables,
)
from persistence_layer import compute_inventories
from whole_manifold_v2 import (
    FULL_REQUIREMENTS,
    active_view,
    beats,
    candidate_id,
)


EXPECTED_SCHEMAS = {
    "connection": "ratchet.pack183.deep-connection-layer.v1",
    "history": "ratchet.pack183.deep-history-layer.v1",
    "persistence": "ratchet.pack183.deep-persistence-layer.v1",
    "chirality": "ratchet.pack183.deep-chirality-layer.v1",
    "whole_manifold_v2": "ratchet.pack183.whole-manifold-v2.v1",
    "verification": "ratchet.pack183.deep-verification.v1",
    "deterministic_replay": "ratchet.pack183.deep-deterministic-replay.v1",
}
SCHEMA = EXPECTED_SCHEMAS["verification"]
CLAIM_CEILING = (
    "packet-relative semantic and adversarial verification only; no promotion, formal admission, "
    "canonical manifold, physics, terminal state, or exhaustive-grammar claim"
)
STAGE_FILES = (
    "connection.json",
    "history.json",
    "persistence.json",
    "chirality.json",
    "whole_manifold_v2.json",
)
ENGINE_FILES = (
    "connection_layer.py",
    "history_layer.py",
    "persistence_layer.py",
    "chirality_layer.py",
    "whole_manifold_v2.py",
    "verify_deep.py",
    "deterministic_replay_deep.py",
)
BANNED_RECEIPT_WORDS = re.compile(r"\b(?:causes|creates|drives|produces)\b", re.IGNORECASE)


def result_digest_valid(value: dict[str, Any]) -> bool:
    expected = value.get("result_digest")
    body = {key: item for key, item in value.items() if key != "result_digest"}
    return expected == digest(body)


def receipt_digests_valid(value: dict[str, Any]) -> bool:
    for receipt in value.get("receipts", []):
        expected = receipt.get("receipt_digest")
        body = {key: item for key, item in receipt.items() if key != "receipt_digest"}
        if expected != digest(body):
            return False
    return True


def strict_load(path: Path) -> dict[str, Any]:
    def object_no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r} in {path}")
            result[key] = value
        return result

    def reject_constant(value: str):
        raise ValueError(f"non-finite JSON constant {value!r} in {path}")

    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=object_no_duplicates,
        parse_constant=reject_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON must be an object: {path}")
    return value


def all_claim_receipts(stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for stage in stages:
        output.append(stage)
        output.extend(receipt for receipt in stage.get("receipts", []) if isinstance(receipt, dict))
    return output


def strings_in(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from strings_in(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings_in(item)


def evaluation_receipts_consistent(stage: dict[str, Any], field: str, id_field: str) -> bool:
    evaluations = stage.get(field, {})
    listed = {receipt.get(id_field): receipt for receipt in stage.get("receipts", [])}
    return set(evaluations) == set(listed) and all(
        evaluations[name] == listed[name] for name in evaluations
    )


def branching_tree_semantics(
    structure: dict[str, Any],
    transports: dict[str, dict[str, list[int]]],
) -> bool:
    try:
        nodes = structure["nodes"]
        root = structure["root"]
        edges = structure["edges"]
        history_at_node = structure["history_at_node"]
        parent_edge = {edge["target"]: edge for edge in edges}
        if len(parent_edge) != len(edges) or root in parent_edge:
            return False
        outgoing = {node: 0 for node in nodes}
        for edge in edges:
            outgoing[edge["source"]] += 1
        if set(structure["leaves"]) != {node for node, count in outgoing.items() if count == 0}:
            return False
        expected_tables = {
            "identity": transports["identity_transport"],
            "parity_sign": transports["parity_sign_transport"],
            "qca_permutation": transports["qca_permutation_transport"],
            "parity_then_qca": compose_tables(
                transports["parity_sign_transport"], transports["qca_permutation_transport"]
            ),
            "qca_then_parity": compose_tables(
                transports["qca_permutation_transport"], transports["parity_sign_transport"]
            ),
        }
        if set(history_at_node) != set(nodes):
            return False
        restriction_tables = {
            "parity_sign_transport": transports["parity_sign_transport"],
            "qca_permutation_transport": transports["qca_permutation_transport"],
        }
        for node in nodes:
            restrictions = []
            cursor = node
            seen = set()
            while cursor != root:
                if cursor in seen or cursor not in parent_edge:
                    return False
                seen.add(cursor)
                edge = parent_edge[cursor]
                restrictions.append(edge["restriction"])
                cursor = edge["source"]
            composed = transports["identity_transport"]
            for restriction in reversed(restrictions):
                composed = compose_tables(composed, restriction_tables[restriction])
            if composed != expected_tables[history_at_node[node]]:
                return False
        return True
    except (KeyError, TypeError, ValueError):
        return False


def history_vector_from_structure(structure: dict[str, Any]) -> dict[str, int]:
    if structure.get("structure_type") == "unordered_set":
        return {"history_declared_step_edges": 0, "history_branch_points": 0}
    if structure.get("structure_type") == "sequence_family":
        return {
            "history_declared_step_edges": sum(len(steps) for steps in structure["sequences"].values()),
            "history_branch_points": 0,
        }
    if structure.get("structure_type") == "branching_tree":
        outgoing = {node: 0 for node in structure["nodes"]}
        for edge in structure["edges"]:
            outgoing[edge["source"]] += 1
        return {
            "history_declared_step_edges": len(structure["edges"]),
            "history_branch_points": sum(count > 1 for count in outgoing.values()),
        }
    raise ValueError("unknown history structure")


def connection_semantics(source: dict[str, Any], connection: dict[str, Any]) -> dict[str, bool]:
    tables, evidence = expected_transport_tables()
    observed = observed_inner_states(source)
    outer = outer_admissible_states(source)
    evaluations = connection.get("transport_evaluations", {})
    exact_tables = set(evaluations) == set(CONNECTION_CANDIDATES) and all(
        evaluations[name].get("transport_table") == tables[name] for name in CONNECTION_CANDIDATES
    )
    classifications_exact = True
    witnesses_total = True
    for name in CONNECTION_CANDIDATES:
        row = evaluations.get(name, {})
        table = row.get("transport_table", {})
        violations = []
        if set(table) == set(tables[name]):
            for state in sorted(observed):
                transported = tuple(table[state_key(state)])
                if transported not in outer:
                    violations.append({
                        "inner_state": list(state),
                        "transported_state": list(transported),
                        "transport": name,
                        "outer_admissible_states": [list(item) for item in sorted(outer)],
                    })
        else:
            classifications_exact = False
            witnesses_total = False
            continue
        classifications_exact &= row.get("admissible") == (len(violations) == 0)
        witnesses_total &= row.get("violations") == violations
    return {
        "connection_candidate_grammar_exact": tuple(connection.get("candidates", [])) == CONNECTION_CANDIDATES,
        "connection_source_tables_exact": exact_tables,
        "connection_spinor_derivation_exact": (
            connection.get("source_evidence", {}).get("spinor_density_erases_lifted_sign") is True
            and evidence["spinor_density_erases_lifted_sign"] is True
            and connection.get("source_evidence", {}).get("spinor_overlaps_0_2pi_4pi") == [1.0, -1.0, 1.0]
        ),
        "connection_qca_permutation_exact": (
            evidence["qca_transition_table_bijective"] is True
            and connection.get("source_evidence", {}).get("qca_transition_table") == evidence["qca_transition_table"]
            and len({tuple(value) for value in tables["qca_permutation_transport"].values()}) == 8
        ),
        "connection_classification_exact": classifications_exact,
        "connection_violation_witness_total": witnesses_total,
        "connection_default_admissible": connection.get("operational_default") in connection.get("frontier", []),
        "connection_evaluation_receipts_consistent": evaluation_receipts_consistent(
            connection, "transport_evaluations", "candidate_id"
        ),
    }


def history_semantics(history: dict[str, Any]) -> dict[str, bool]:
    evaluations = history.get("history_evaluations", {})
    transports = history.get("transport_tables", {})
    parity = transports.get("parity_sign_transport", {})
    qca = transports.get("qca_permutation_transport", {})
    parity_then_qca = compose_tables(parity, qca) if parity and qca else {}
    qca_then_parity = compose_tables(qca, parity) if parity and qca else {}
    witness = history.get("noncommutation_witness")
    any_difference = bool(parity_then_qca) and any(
        parity_then_qca[key] != qca_then_parity[key] for key in parity_then_qca
    )
    witness_valid = False
    if isinstance(witness, dict) and witness.get("input_state"):
        key = state_key(tuple(witness["input_state"]))
        witness_valid = (
            witness.get("T2_after_T1") == parity_then_qca.get(key)
            and witness.get("T1_after_T2") == qca_then_parity.get(key)
            and witness.get("T2_after_T1") != witness.get("T1_after_T2")
        )
    grammar_exact = tuple(history.get("candidates", [])) == HISTORY_CANDIDATES and set(evaluations) == set(HISTORY_CANDIDATES)
    tables_exact = grammar_exact and all(
        row.get("history_tables", {}).get("parity_then_qca", parity_then_qca) == parity_then_qca
        and row.get("history_tables", {}).get("qca_then_parity", qca_then_parity) == qca_then_parity
        for row in evaluations.values()
        if row.get("ordered_relation_chain") is True
    )
    expected_branching_structure = {
        "structure_type": "branching_tree",
        "root": "root",
        "nodes": ["root", "after_parity", "after_qca", "after_parity_qca", "after_qca_parity"],
        "edges": [
            {"source": "root", "target": "after_parity", "restriction": "parity_sign_transport"},
            {"source": "root", "target": "after_qca", "restriction": "qca_permutation_transport"},
            {"source": "after_parity", "target": "after_parity_qca", "restriction": "qca_permutation_transport"},
            {"source": "after_qca", "target": "after_qca_parity", "restriction": "parity_sign_transport"},
        ],
        "leaves": ["after_parity_qca", "after_qca_parity"],
        "history_at_node": {
            "root": "identity",
            "after_parity": "parity_sign",
            "after_qca": "qca_permutation",
            "after_parity_qca": "parity_then_qca",
            "after_qca_parity": "qca_then_parity",
        },
    }
    expected_sequence_structure = {
        "structure_type": "sequence_family",
        "sequences": {
            "identity": [],
            "parity_sign": ["parity_sign_transport"],
            "qca_permutation": ["qca_permutation_transport"],
            "parity_then_qca": ["parity_sign_transport", "qca_permutation_transport"],
            "qca_then_parity": ["qca_permutation_transport", "parity_sign_transport"],
        },
    }
    return {
        "history_candidate_grammar_exact": grammar_exact,
        "history_both_orders_exact": tables_exact,
        "history_noncommutation_iff_witness": (
            history.get("noncommutation_earned") is any_difference
            and ((any_difference and witness_valid) or (not any_difference and history.get("noncommutation_negative")))
        ),
        "history_order_witness_recomputes": witness_valid,
        "history_unordered_negative_explicit": (
            evaluations.get("unordered_set_baseline", {}).get("noncommutation_earned") is False
            and bool(evaluations.get("unordered_set_baseline", {}).get("noncommutation_negative"))
        ),
        "history_ordered_frontier_plural": set(history.get("frontier", [])) == {
            "sequence_histories", "branching_tree_histories"
        },
        "history_sequence_structure_exact": (
            evaluations.get("sequence_histories", {}).get("history_structure")
            == expected_sequence_structure
        ),
        "history_branching_structure_exact": (
            evaluations.get("branching_tree_histories", {}).get("history_structure")
            == expected_branching_structure
            and evaluations.get("branching_tree_histories", {}).get("branching") is True
            and branching_tree_semantics(expected_branching_structure, transports)
        ),
        "history_evaluation_receipts_consistent": evaluation_receipts_consistent(
            history, "history_evaluations", "candidate_id"
        ),
    }


def persistence_semantics(source: dict[str, Any], history: dict[str, Any], persistence: dict[str, Any]) -> dict[str, bool]:
    try:
        expected = compute_inventories(source, history)
    except (KeyError, TypeError, ValueError):
        expected = {}
    actual = persistence.get("inventories", {})
    exact = set(actual) == set(expected)
    if exact:
        for name, row in expected.items():
            for field in (
                "connection_candidate", "history_candidate", "allowed_histories",
                "allowed_history_tables", "derived_distinction_count", "surviving_distinctions",
                "excluded_distinctions", "surviving_distinction_count",
            ):
                if actual[name].get(field) != row[field]:
                    exact = False
                    break
            if not exact:
                break
    allowed_covered = set(actual) == set(expected) and all(
        set(row.get("allowed_histories", [])) == set(row.get("allowed_history_tables", {}))
        for row in actual.values()
    )
    shared = set(persistence.get("current_frontier_surviving_distinctions", []))
    frontier = persistence.get("current_frontier", [])
    recomputed_shared = set.intersection(*(
        {item["distinction_id"] for item in actual[name].get("surviving_distinctions", [])}
        for name in frontier
    )) if frontier and all(name in actual for name in frontier) else set()
    return {
        "persistence_all_candidate_manifolds_covered": set(actual) == set(expected) and len(actual) == 9,
        "persistence_inventory_exact_intersection": exact and shared == recomputed_shared,
        "persistence_all_allowed_histories_covered": allowed_covered,
        "persistence_current_frontier_inventory_eleven": len(shared) == 11,
        "persistence_evaluation_receipts_consistent": evaluation_receipts_consistent(
            persistence, "inventories", "candidate_id"
        ),
    }


def chirality_semantics(chirality: dict[str, Any]) -> dict[str, bool]:
    expected = compute_octonion_evidence()
    actual = chirality.get("octonion_evidence", {})
    evidence_exact = digest(actual) == digest(expected)
    expressible = (
        evidence_exact
        and actual.get("vendored_report_all_pass") is True
        and actual.get("left_bracket_vector") != actual.get("mixed_bracket_vector")
    )
    forced = expressible and all(
        row.get("orientation_installed") is True
        for row in chirality.get("orientation_candidates", {}).values()
        if row.get("admissible") is True
    )
    installable = expressible and not forced and any(
        row.get("orientation_installed") is True and row.get("admissible") is True
        for row in chirality.get("orientation_candidates", {}).values()
    )
    return {
        "chirality_octonion_witness_exact": evidence_exact,
        "chirality_not_forced": chirality.get("forced") is False and forced is False,
        "chirality_status_consistent": (
            chirality.get("expressible") is expressible
            and chirality.get("forced") is forced
            and chirality.get("installable") is installable
            and chirality.get("status") == "EXPRESSIBLE_INSTALLABLE_NOT_FORCED"
        ),
        "chirality_receipt_consistent": (
            len(chirality.get("receipts", [])) == 1
            and chirality["receipts"][0].get("expressible") is expressible
            and chirality["receipts"][0].get("forced") is forced
            and chirality["receipts"][0].get("installable") is installable
        ),
    }


def whole_frontier_witness_exact(whole: dict[str, Any]) -> bool:
    rows = whole.get("candidate_evaluations", {})
    frontier = whole.get("final_frontier", [])
    purgatory = whole.get("purgatory", [])
    if set(frontier) | {row.get("candidate_id") for row in purgatory} != set(rows):
        return False
    if set(frontier) & {row.get("candidate_id") for row in purgatory}:
        return False
    views = {name: active_view(row, FULL_REQUIREMENTS) for name, row in rows.items()}
    for right in frontier:
        if right not in views:
            return False
        for left in rows:
            if left != right and beats(views[left], views[right])[0]:
                return False
    for entry in purgatory:
        right = entry.get("candidate_id")
        witness = entry.get("witness", {})
        left = witness.get("beaten_by_candidate") if isinstance(witness, dict) else None
        if right not in views or left not in views:
            return False
        won, reason = beats(views[left], views[right])
        if not won or witness.get("reason") != reason:
            return False
    return True


def whole_semantics(
    source: dict[str, Any],
    chirality: dict[str, Any],
    whole: dict[str, Any],
    parent_whole: dict[str, Any],
) -> dict[str, bool]:
    expected_ids = {
        candidate_id(parent_id, connection_id, history_id)
        for parent_id in parent_whole.get("candidate_evaluations", {})
        for connection_id in chirality.get("connection_candidates", [])
        for history_id in chirality.get("history_candidates", [])
    }
    rows = whole.get("candidate_evaluations", {})
    components_exact = set(rows) == expected_ids and all(
        name == candidate_id(row.get("parent_candidate_id", ""), row.get("connection_candidate", ""), row.get("history_candidate", ""))
        and row.get("complete_whole_candidate") is True
        and row.get("settled_under_Z_plus_delta") is True
        for name, row in rows.items()
    )
    history_vectors_exact = set(rows) == expected_ids and all(
        row.get("history_structure_digest")
        == digest(chirality["history_structures"][row["history_candidate"]])
        and all(
            row.get("presumption_vector", {}).get(field) == value
            for field, value in history_vector_from_structure(
                chirality["history_structures"][row["history_candidate"]]
            ).items()
        )
        and "history_order_edges" not in row.get("presumption_vector", {})
        and "history_branch_nodes" not in row.get("presumption_vector", {})
        for row in rows.values()
    )
    receipts = whole.get("receipts", [])
    universe = set(rows)
    reoffer_exact = len(receipts) == 7 and all(
        receipt.get("candidate_count_recomputed") == len(universe)
        and set(receipt.get("frontier", [])) | set(receipt.get("purgatory_ids", [])) == universe
        and not (set(receipt.get("frontier", [])) & set(receipt.get("purgatory_ids", [])))
        for receipt in receipts[:4]
    )
    comparison_exact = len(receipts) == 7 and all(
        receipt.get("comparison_count") == len(universe) * (len(universe) - 1)
        for receipt in receipts
    )
    return {
        "whole_exact_five_way_cross_product": set(rows) == expected_ids and len(rows) == 4752,
        "whole_component_fields_exact": components_exact,
        "whole_history_vectors_recompute": history_vectors_exact,
        "whole_frontier_plural": len(whole.get("final_frontier", [])) > 1,
        "whole_frontier_and_purgatory_witnesses_recompute": whole_frontier_witness_exact(whole),
        "whole_purgatory_reoffer_rules": all(
            bool(row.get("reoffer_rule")) for row in whole.get("purgatory", [])
        ),
        "whole_full_reoffer_every_arrival": reoffer_exact,
        "whole_requirement_revision_reentry": (
            len(receipts) == 7
            and bool(receipts[4].get("reentered_from_purgatory"))
            and receipts[5].get("frontier") == receipts[3].get("frontier")
            and receipts[6].get("frontier") == receipts[5].get("frontier")
        ),
        "whole_complete_comparison_count": comparison_exact,
        "whole_open_nonterminal_nonexhaustive": (
            whole.get("global_mss_claimed") is False
            and whole.get("terminal_state") is False
            and whole.get("candidate_universe_exhausted") is False
            and all(
                receipt.get("global_mss_claimed") is False
                and receipt.get("terminal_state") is False
                and receipt.get("candidate_universe_exhausted") is False
                for receipt in receipts
            )
        ),
        "whole_lineage_exact": (
            whole.get("source_packet_digest") == source.get("result_digest")
            and whole.get("prior_whole_digest") == parent_whole.get("result_digest")
            and whole.get("prior_chirality_digest") == chirality.get("result_digest")
        ),
        "whole_late_readout_nonphysics": all(
            row.get("drive_gradient_asserted_as_physics") is False for row in rows.values()
        ),
    }


def source_files_stdlib_local() -> bool:
    engine = Path(__file__).resolve().parent
    banned = {"socket", "urllib", "http", "requests", "subprocess", "random"}
    for filename in ENGINE_FILES:
        path = engine / filename
        if not path.exists():
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".", 1)[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots = {node.module.split(".", 1)[0]}
            else:
                continue
            if roots & banned:
                return False
    return True


def validate(
    source: dict[str, Any],
    connection: dict[str, Any],
    history: dict[str, Any],
    persistence: dict[str, Any],
    chirality: dict[str, Any],
    whole: dict[str, Any],
) -> dict[str, bool]:
    parent_results = Path(__file__).resolve().parent.parent / "results"
    parent_whole = strict_load(parent_results / "whole_manifold.json")
    stages = [connection, history, persistence, chirality, whole]
    claim_receipts = all_claim_receipts(stages)
    checks = {
        "source_schema": source.get("schema") == "ratchet.v8.source-packets.v1",
        "source_result_digest": result_digest_valid(source),
        "source_packet_count_nine_unique": (
            len(source.get("base_packets", [])) == 9
            and len({row.get("packet_id") for row in source.get("base_packets", [])}) == 9
        ),
        "schema_connection": connection.get("schema") == EXPECTED_SCHEMAS["connection"],
        "schema_history": history.get("schema") == EXPECTED_SCHEMAS["history"],
        "schema_persistence": persistence.get("schema") == EXPECTED_SCHEMAS["persistence"],
        "schema_chirality": chirality.get("schema") == EXPECTED_SCHEMAS["chirality"],
        "schema_whole_v2": whole.get("schema") == EXPECTED_SCHEMAS["whole_manifold_v2"],
        "all_stage_result_digests": all(result_digest_valid(stage) for stage in stages),
        "all_nested_receipt_digests": all(receipt_digests_valid(stage) for stage in stages),
        "all_receipts_promotion_locked": all(row.get("promotion_allowed") is False for row in claim_receipts),
        "all_receipts_formal_locked": all(row.get("formal_admission_allowed") is False for row in claim_receipts),
        "packet_relative_claim_ceiling": all(
            "packet-relative" in str(row.get("claim_ceiling", "")).lower() for row in claim_receipts
        ),
        "lineage_chain_exact": (
            connection.get("source_packet_digest") == source.get("result_digest")
            and connection.get("prior_whole_digest") == parent_whole.get("result_digest")
            and history.get("source_packet_digest") == source.get("result_digest")
            and history.get("prior_connection_digest") == connection.get("result_digest")
            and persistence.get("source_packet_digest") == source.get("result_digest")
            and persistence.get("prior_history_digest") == history.get("result_digest")
            and chirality.get("source_packet_digest") == source.get("result_digest")
            and chirality.get("prior_persistence_digest") == persistence.get("result_digest")
        ),
        "history_structure_lineage_exact": (
            persistence.get("history_structures") == {
                candidate: history.get("history_evaluations", {}).get(candidate, {}).get("history_structure")
                for candidate in HISTORY_CANDIDATES
            }
            and chirality.get("history_structures") == persistence.get("history_structures")
        ),
        "all_stage_process_checks": all(
            stage.get("all_pass") is True
            and bool(stage.get("checks") or stage.get("process_checks"))
            and all((stage.get("checks") or stage.get("process_checks")).values())
            for stage in stages
        ),
        "nominalist_language_contract": not any(
            BANNED_RECEIPT_WORDS.search(text)
            for stage in stages for text in strings_in(stage.get("receipts", []))
        ),
        "new_engine_files_stdlib_local": source_files_stdlib_local(),
    }
    checks.update(connection_semantics(source, connection))
    checks.update(history_semantics(history))
    checks.update(persistence_semantics(source, history, persistence))
    checks.update(chirality_semantics(chirality))
    checks.update(whole_semantics(source, chirality, whole, parent_whole))
    return checks


def reseal_all(documents: list[dict[str, Any]]) -> None:
    for document in documents:
        for receipt in document.get("receipts", []):
            receipt.pop("receipt_digest", None)
            receipt["receipt_digest"] = digest(receipt)
        document.pop("result_digest", None)
        document["result_digest"] = digest(document)


def mutation_tests(
    source: dict[str, Any],
    connection: dict[str, Any],
    history: dict[str, Any],
    persistence: dict[str, Any],
    chirality: dict[str, Any],
    whole: dict[str, Any],
) -> list[dict[str, Any]]:
    tests = []
    templates = [
        json.loads(canonical_json(document))
        for document in (connection, history, persistence, chirality, whole)
    ]

    def run(name: str, target: int, mutate: Callable[[dict[str, Any]], None], expected_check: str) -> None:
        documents = copy.deepcopy(templates)
        mutate(documents[target])
        reseal_all(documents)
        checks = validate(source, *documents)
        mechanical_green = checks["all_stage_result_digests"] and checks["all_nested_receipt_digests"]
        tests.append({
            "mutation": name,
            "expected_failed_check": expected_check,
            "mechanical_digests_preserved": mechanical_green,
            "rejected": mechanical_green and checks.get(expected_check) is False,
            "actual_failed_checks": sorted(key for key, value in checks.items() if not value),
        })

    run("alter_connection_schema", 0, lambda d: d.__setitem__("schema", "wrong"), "schema_connection")
    run(
        "synchronized_connection_schema_drift",
        0,
        lambda d: (
            d.__setitem__("schema", "ratchet.pack183.deep-connection-layer.v2"),
            d.__setitem__("producer_schema_echo", "ratchet.pack183.deep-connection-layer.v2"),
        ),
        "schema_connection",
    )
    run("allow_promotion", 0, lambda d: d.__setitem__("promotion_allowed", True), "all_receipts_promotion_locked")
    run("allow_formal_admission", 1, lambda d: d["receipts"][0].__setitem__("formal_admission_allowed", True), "all_receipts_formal_locked")
    run("forge_parity_sign_table", 0, lambda d: d["transport_evaluations"]["parity_sign_transport"]["transport_table"].__setitem__("010", [0, 1, 1]), "connection_source_tables_exact")
    run("erase_connection_violation_witness", 0, lambda d: d["transport_evaluations"]["identity_transport"].__setitem__("violations", []), "connection_violation_witness_total")
    run("drop_branching_history", 1, lambda d: (d["history_evaluations"].pop("branching_tree_histories"), d.__setitem__("candidates", d["candidates"][:-1])), "history_candidate_grammar_exact")
    run(
        "flatten_branching_history_structure",
        1,
        lambda d: d["history_evaluations"]["branching_tree_histories"].__setitem__(
            "history_structure",
            {"structure_type": "sequence_family", "sequences": {}},
        ),
        "history_branching_structure_exact",
    )
    run("erase_noncommutation_status", 1, lambda d: d.__setitem__("noncommutation_earned", False), "history_noncommutation_iff_witness")
    run("forge_order_witness_output", 1, lambda d: d["noncommutation_witness"].__setitem__("T2_after_T1", [1, 1, 1]), "history_order_witness_recomputes")
    run("fabricate_persistent_distinction", 2, lambda d: d["inventories"][sorted(d["inventories"])[0]]["surviving_distinctions"].append({"distinction_id": "fake", "left_state": [0, 0, 0], "right_state": [0, 0, 0]}), "persistence_inventory_exact_intersection")
    run("drop_persistence_candidate", 2, lambda d: d["inventories"].pop(sorted(d["inventories"])[0]), "persistence_all_candidate_manifolds_covered")
    run("force_chirality", 3, lambda d: d.__setitem__("forced", True), "chirality_not_forced")
    run("forge_octonion_gap", 3, lambda d: d["octonion_evidence"].__setitem__("path_bracketing_gap_squared", 0), "chirality_octonion_witness_exact")
    run("remove_whole_candidate", 4, lambda d: d["candidate_evaluations"].pop(sorted(d["candidate_evaluations"])[0]), "whole_exact_five_way_cross_product")
    run("collapse_whole_frontier", 4, lambda d: d.__setitem__("final_frontier", d["final_frontier"][:1]), "whole_frontier_plural")
    run("blank_purgatory_reoffer_rule", 4, lambda d: d["purgatory"][0].__setitem__("reoffer_rule", ""), "whole_purgatory_reoffer_rules")
    run("forge_purgatory_witness", 4, lambda d: d["purgatory"][0]["witness"].__setitem__("beaten_by_candidate", d["purgatory"][0]["candidate_id"]), "whole_frontier_and_purgatory_witnesses_recompute")
    run("skip_layer_arrival_reoffer", 4, lambda d: d["receipts"][0].__setitem__("candidate_count_recomputed", 1), "whole_full_reoffer_every_arrival")
    run("claim_terminal_whole", 4, lambda d: d.__setitem__("terminal_state", True), "whole_open_nonterminal_nonexhaustive")
    run("break_lineage", 4, lambda d: d.__setitem__("prior_chirality_digest", "sha256:" + "0" * 64), "whole_lineage_exact")
    run("promote_global_ceiling", 0, lambda d: d.__setitem__("claim_ceiling", "global canonical result"), "packet_relative_claim_ceiling")
    run("insert_banned_causal_word", 4, lambda d: d["receipts"][0].__setitem__("reason", "this causes closure"), "nominalist_language_contract")
    run("forge_comparison_count", 4, lambda d: d["receipts"][0].__setitem__("comparison_count", 1), "whole_complete_comparison_count")
    run(
        "forge_history_topology_vector",
        4,
        lambda d: d["candidate_evaluations"][sorted(d["candidate_evaluations"])[0]]["presumption_vector"].__setitem__(
            "history_branch_points", 99
        ),
        "whole_history_vectors_recompute",
    )
    return tests


def run(
    source: dict[str, Any],
    connection: dict[str, Any],
    history: dict[str, Any],
    persistence: dict[str, Any],
    chirality: dict[str, Any],
    whole: dict[str, Any],
) -> dict[str, Any]:
    checks = validate(source, connection, history, persistence, chirality, whole)
    mutations = mutation_tests(source, connection, history, persistence, chirality, whole)
    result = {
        "schema": SCHEMA,
        "schema_pins": dict(EXPECTED_SCHEMAS),
        "source_packet_digest": source["result_digest"],
        "stage_result_digests": {
            "connection": connection["result_digest"],
            "history": history["result_digest"],
            "persistence": persistence["result_digest"],
            "chirality": chirality["result_digest"],
            "whole_manifold_v2": whole["result_digest"],
        },
        "checks": checks,
        "mutation_tests": mutations,
        "mutation_count": len(mutations),
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all(checks.values()) and all(row["rejected"] for row in mutations),
    }
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True, help="directory containing deep stage receipts")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = strict_load(args.source)
    documents = [strict_load(args.prior / filename) for filename in STAGE_FILES]
    result = run(source, *documents)
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "checks": len(result["checks"]),
        "failed_checks": sorted(name for name, value in result["checks"].items() if not value),
        "mutation_count": result["mutation_count"],
        "mutations_rejected": sum(row["rejected"] for row in result["mutation_tests"]),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
