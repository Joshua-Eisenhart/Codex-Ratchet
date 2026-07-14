#!/usr/bin/env python3
"""Compare packet-native ledger integrity with an audit-only ancestry-DAG policy.

This does not patch or wrap the packet's verifier as production code.  It runs
the exact archive-pinned verifier first, then (only when native integrity
passes) applies a separately named DAG predicate to the variation graph.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import rustworkx as rx


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "results" / "lineage_contract_differential_v3_results.json"
DEFAULT_VALIDATOR = HERE / "validate_lineage_contract_differential_v3.py"
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"

EXPECTED_ARCHIVE_SHA256 = "42fc2629e076b4cd5b8015514fb1c9027aa7c751702ebc7a719a6b808141b9da"
POOL_MEMBER = "ratchet/purgatory_pool.py"
LEDGER_MEMBER = "sims_and_scripts/living_purgatory_ledger_r2_results.json"
EXPECTED_POOL_SHA256 = "73f152e646e6cd9e0e989c4b0f7ce1f6ca2c39359c951f40648b0a3909a954e8"
EXPECTED_LEDGER_SHA256 = "850e975c1d3e7aee2a78d5614a4d64e21bd0309ef61683ed150c77c209870553"

NATIVE_MODE = "packet_native_integrity_v3"
STRICT_MODE = "audit_only_strict_ancestry_dag_v1"
CLAIM_CEILING = "contract semantics only; no production integrity defect"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def receipt_content_sha256(receipt: Mapping[str, Any]) -> str:
    core = copy.deepcopy(dict(receipt))
    core.pop("receipt_content_sha256", None)
    return sha256_bytes(canonical_json(core).encode("utf-8"))


def import_packet_verifier(pool_bytes: bytes, directory: Path) -> Any:
    source_path = directory / "packet166_purgatory_pool.py"
    source_path.write_bytes(pool_bytes)
    spec = importlib.util.spec_from_file_location("packet166_purgatory_pool_v3", source_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to import packet-native PurgatoryPool")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def graph_for(entries: Mapping[str, Any], variation_log: list[Mapping[str, Any]]) -> rx.PyDiGraph:
    candidate_ids = sorted(str(candidate_id) for candidate_id in entries)
    index_by_id = {candidate_id: index for index, candidate_id in enumerate(candidate_ids)}
    graph = rx.PyDiGraph(multigraph=True)
    graph.add_nodes_from(candidate_ids)
    graph.add_edges_from_no_data(
        [
            (index_by_id[str(edge["parent_id"])], index_by_id[str(edge["child_id"])])
            for edge in variation_log
        ]
    )
    return graph


def cycle_report(graph: rx.PyDiGraph) -> dict[str, Any] | None:
    cycle_edges = list(rx.digraph_find_cycle(graph))
    if not cycle_edges:
        return None
    return {
        "nodes": [graph[cycle_edges[0][0]], *[graph[target] for _, target in cycle_edges]],
        "edges": [
            {"parent_id": graph[source], "child_id": graph[target]}
            for source, target in cycle_edges
        ],
    }


def topology_report(state: Mapping[str, Any]) -> dict[str, Any]:
    graph = graph_for(state["entries"], state.get("variation_log", []))
    is_dag = bool(rx.is_directed_acyclic_graph(graph))
    return {
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "is_dag": is_dag,
        "one_cycle": None if is_dag else cycle_report(graph),
    }


def native_verdict(module: Any, state: Mapping[str, Any], path: Path) -> dict[str, Any]:
    path.write_text(json.dumps(state, sort_keys=True), encoding="utf-8")
    try:
        pool = module.PurgatoryPool.load(path, verify=True)
        accepted, reason = pool.verify_integrity()
        return {
            "mode": NATIVE_MODE,
            "authority": "packet_native",
            "accepted": bool(accepted),
            "reason": str(reason),
            "error_type": None,
        }
    except (ValueError, KeyError, TypeError) as error:
        return {
            "mode": NATIVE_MODE,
            "authority": "packet_native",
            "accepted": False,
            "reason": str(error),
            "error_type": type(error).__name__,
        }


def strict_verdict(native: Mapping[str, Any], topology: Mapping[str, Any]) -> dict[str, Any]:
    if not native["accepted"]:
        return {
            "mode": STRICT_MODE,
            "authority": "audit_only_hypothetical_policy_not_packet_native",
            "accepted": False,
            "reason": "native_integrity_precondition_failed",
            "native_precondition_pass": False,
            "dag_predicate_evaluated_for_policy": False,
        }
    if not topology["is_dag"]:
        return {
            "mode": STRICT_MODE,
            "authority": "audit_only_hypothetical_policy_not_packet_native",
            "accepted": False,
            "reason": "ancestry_cycle_detected",
            "native_precondition_pass": True,
            "dag_predicate_evaluated_for_policy": True,
        }
    return {
        "mode": STRICT_MODE,
        "authority": "audit_only_hypothetical_policy_not_packet_native",
        "accepted": True,
        "reason": "native_integrity_and_ancestry_dag_pass",
        "native_precondition_pass": True,
        "dag_predicate_evaluated_for_policy": True,
    }


def evaluate_state(module: Any, state: Mapping[str, Any], directory: Path, name: str) -> dict[str, Any]:
    topology = topology_report(state)
    native = native_verdict(module, state, directory / f"{name}.json")
    return {
        "native_mode": native,
        "strict_ancestry_dag_mode": strict_verdict(native, topology),
        "topology_observation": topology,
    }


def build_fixture_state(module: Any, name: str) -> dict[str, Any]:
    pool = module.PurgatoryPool()
    if name == "valid_dag_positive":
        for candidate_id in ("root", "left", "right", "leaf"):
            pool.register(candidate_id, {"fixture": candidate_id})
        edges = [
            {"parent_id": "root", "child_id": "left"},
            {"parent_id": "root", "child_id": "right"},
            {"parent_id": "left", "child_id": "leaf"},
            {"parent_id": "right", "child_id": "leaf"},
        ]
    elif name == "cycle_negative":
        for candidate_id in ("a", "b", "c"):
            pool.register(candidate_id, {"fixture": candidate_id})
        edges = [
            {"parent_id": "a", "child_id": "b"},
            {"parent_id": "b", "child_id": "c"},
            {"parent_id": "c", "child_id": "a"},
        ]
    elif name == "isolated_boundary":
        pool.register("only", {"fixture": "only"})
        edges = []
    else:
        raise ValueError(f"unknown fixture: {name}")
    pool.run_rung(
        0,
        f"audit-fixture:{name}",
        lambda _candidate, _gamma: {
            "survives": True,
            "reason": "contract differential fixture",
            "evidence": {"fixture": name},
            "scope": "audit_only",
            "reopen_condition": "not applicable",
        },
        variation_edges=edges,
    )
    state = {
        "schema": module.LEDGER_SCHEMA,
        "entries": {
            candidate_id: {
                "candidate_encoded": entry["candidate_encoded"],
                "content_sha": entry["content_sha"],
                "content_hash_schema": entry.get("content_hash_schema", "v3"),
                "root_compatible_note": entry["root_compatible_note"],
                "origins": entry.get("origins", []),
                "history": entry["history"],
            }
            for candidate_id, entry in pool.entries.items()
        },
        "rung_log": copy.deepcopy(pool.rung_log),
        "variation_log": copy.deepcopy(pool.variation_log),
    }
    return state


def rehash_rung_log(module: Any, state: dict[str, Any]) -> None:
    previous_rung_hash = ""
    variation_log = state["variation_log"]
    for row in state["rung_log"]:
        if row.get("schema") != module.RUNG_SCHEMA:
            previous_rung_hash = ""
            continue
        rung_index = int(row["rung_index"])
        variation_ids = [
            edge["variation_id"]
            for edge in variation_log
            if int(edge["proposed_at_rung"]) == rung_index
        ]
        row["variation_ids"] = variation_ids
        row["purgatory_flux"]["new_variations"] = len(variation_ids)
        row["cites_prior_rung"] = previous_rung_hash
        core = {key: value for key, value in row.items() if key != "payload_hash"}
        row["payload_hash"] = module._sha_encoded(core)
        previous_rung_hash = row["payload_hash"]


def dag_projection(state: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []
    for edge in state["variation_log"]:
        candidate = copy.deepcopy(edge)
        trial_state = {"entries": state["entries"], "variation_log": [*kept, candidate]}
        if topology_report(trial_state)["is_dag"]:
            kept.append(candidate)
        else:
            removed.append(candidate)
    projected = copy.deepcopy(dict(state))
    projected["variation_log"] = kept
    return projected, removed


def inject_reverse_edge(module: Any, state: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    mutated = copy.deepcopy(dict(state))
    endpoint_pairs = {
        (str(edge["parent_id"]), str(edge["child_id"]))
        for edge in mutated["variation_log"]
    }
    source_edge = next(
        edge
        for edge in mutated["variation_log"]
        if (str(edge["child_id"]), str(edge["parent_id"])) not in endpoint_pairs
    )
    parent_id = str(source_edge["child_id"])
    child_id = str(source_edge["parent_id"])
    core = {
        "schema": module.VARIATION_SCHEMA,
        "parent_id": parent_id,
        "parent_content_sha": mutated["entries"][parent_id]["content_sha"],
        "child_id": child_id,
        "child_content_sha": mutated["entries"][child_id]["content_sha"],
        "operator": "audit_only_reverse_edge_injection",
        "proposed_at_rung": int(source_edge["proposed_at_rung"]),
        "reason": "audit-only topology mutation control; never written to the packet",
    }
    injected = dict(core, variation_id=module._variation_id(core))
    mutated["variation_log"].append(injected)
    return mutated, {
        "reversed_existing_variation_id": source_edge["variation_id"],
        "injected_edge": injected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--validator", type=Path, default=DEFAULT_VALIDATOR)
    args = parser.parse_args()

    if Path(sys.executable).resolve() != Path(PYTHON).resolve():
        raise RuntimeError(f"wrong Python runtime: {sys.executable}")

    archive = args.archive.resolve()
    archive_sha_before = sha256_file(archive)
    if archive_sha_before != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(f"unexpected packet archive sha256: {archive_sha_before}")
    with zipfile.ZipFile(archive) as bundle:
        pool_bytes = bundle.read(POOL_MEMBER)
        ledger_bytes = bundle.read(LEDGER_MEMBER)
    if sha256_bytes(pool_bytes) != EXPECTED_POOL_SHA256:
        raise ValueError("packet-native verifier member hash mismatch")
    if sha256_bytes(ledger_bytes) != EXPECTED_LEDGER_SHA256:
        raise ValueError("packet ledger member hash mismatch")
    original_state = json.loads(ledger_bytes)

    with tempfile.TemporaryDirectory(prefix="ratchet-lineage-contract-v3-") as directory_name:
        directory = Path(directory_name)
        module = import_packet_verifier(pool_bytes, directory)

        original_cycle = evaluate_state(module, original_state, directory, "original-cycle")

        fixture_results = {
            fixture: evaluate_state(
                module,
                build_fixture_state(module, fixture),
                directory,
                f"fixture-{fixture}",
            )
            for fixture in ("valid_dag_positive", "cycle_negative", "isolated_boundary")
        }

        projected_state, removed_edges = dag_projection(original_state)
        rehash_rung_log(module, projected_state)
        packet_dag_projection = evaluate_state(
            module,
            projected_state,
            directory,
            "packet-dag-projection",
        )

        injected_state, mutation_detail = inject_reverse_edge(module, projected_state)
        rehash_rung_log(module, injected_state)
        packet_cycle_injection = evaluate_state(
            module,
            injected_state,
            directory,
            "packet-cycle-injection",
        )

        tampered_state = copy.deepcopy(original_state)
        tampered_state["variation_log"][0]["child_content_sha"] = "0" * 64
        tampered_hash = evaluate_state(module, tampered_state, directory, "tampered-hash")

    archive_sha_after = sha256_file(archive)
    checks = {
        "archive_and_members_match_pinned_hashes": (
            archive_sha_before == archive_sha_after == EXPECTED_ARCHIVE_SHA256
            and sha256_bytes(pool_bytes) == EXPECTED_POOL_SHA256
            and sha256_bytes(ledger_bytes) == EXPECTED_LEDGER_SHA256
        ),
        "packet_native_verifier_was_not_modified": archive_sha_before == archive_sha_after,
        "original_cycle_native_accepts": original_cycle["native_mode"]["accepted"] is True,
        "original_cycle_strict_rejects": original_cycle["strict_ancestry_dag_mode"]["accepted"] is False,
        "original_cycle_is_observed": original_cycle["topology_observation"]["is_dag"] is False,
        "valid_dag_fixture_passes_both_modes": (
            fixture_results["valid_dag_positive"]["native_mode"]["accepted"] is True
            and fixture_results["valid_dag_positive"]["strict_ancestry_dag_mode"]["accepted"] is True
        ),
        "cycle_fixture_differentiates_modes": (
            fixture_results["cycle_negative"]["native_mode"]["accepted"] is True
            and fixture_results["cycle_negative"]["strict_ancestry_dag_mode"]["accepted"] is False
        ),
        "isolated_boundary_passes_both_modes": (
            fixture_results["isolated_boundary"]["native_mode"]["accepted"] is True
            and fixture_results["isolated_boundary"]["strict_ancestry_dag_mode"]["accepted"] is True
        ),
        "actual_packet_dag_projection_passes_both_modes": (
            bool(removed_edges)
            and packet_dag_projection["native_mode"]["accepted"] is True
            and packet_dag_projection["strict_ancestry_dag_mode"]["accepted"] is True
        ),
        "rehash_consistent_packet_cycle_mutation_differentiates_modes": (
            packet_cycle_injection["native_mode"]["accepted"] is True
            and packet_cycle_injection["strict_ancestry_dag_mode"]["accepted"] is False
            and packet_cycle_injection["topology_observation"]["is_dag"] is False
        ),
        "tampered_hash_fails_native_and_strict_precondition": (
            tampered_hash["native_mode"]["accepted"] is False
            and tampered_hash["strict_ancestry_dag_mode"]["accepted"] is False
            and tampered_hash["strict_ancestry_dag_mode"]["reason"]
            == "native_integrity_precondition_failed"
        ),
    }
    contract_differential_closed = all(checks.values())

    source_path = Path(__file__).resolve()
    validator_path = args.validator.resolve()
    command = [
        PYTHON,
        str(source_path),
        "--archive",
        str(archive),
        "--output",
        str(args.output.resolve()),
        "--validator",
        str(validator_path),
    ]
    receipt: dict[str, Any] = {
        "schema": "codex-ratchet.lineage-contract-differential-result.v3",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "runner_identity": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "rustworkx_version": rx.__version__,
        },
        "classification": "contract_semantics_audit",
        "evidence_level": "L3_bounded_contract_chain_receipt",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "native_verifier_change_attempted": False,
        "integrity_defect_admitted": False,
        "h_integrity_defect_claim_pass": False,
        "h_lane_status": "red_unadmitted_contract_difference",
        "all_pass": False,
        "contract_differential_closed": contract_differential_closed,
        "claim_ceiling": CLAIM_CEILING,
        "sources": {
            "archive_path": str(archive),
            "archive_sha256": archive_sha_before,
            "native_verifier_member": POOL_MEMBER,
            "native_verifier_sha256": sha256_bytes(pool_bytes),
            "ledger_member": LEDGER_MEMBER,
            "ledger_sha256": sha256_bytes(ledger_bytes),
            "audit_source_path": str(source_path),
            "audit_source_sha256": sha256_file(source_path),
            "validator_source_path": str(validator_path),
            "validator_source_sha256": sha256_file(validator_path),
        },
        "mode_contracts": {
            "native_mode": {
                "mode": NATIVE_MODE,
                "authority": "packet_native",
                "api": "PurgatoryPool.load(verify=True) + PurgatoryPool.verify_integrity()",
                "dag_requirement": False,
            },
            "strict_ancestry_dag_mode": {
                "mode": STRICT_MODE,
                "authority": "audit_only_hypothetical_policy_not_packet_native",
                "definition": "native integrity must pass and the variation parent-to-child graph must be acyclic",
                "production_change": False,
            },
        },
        "same_packet_cycle_ledger": original_cycle,
        "fixture_controls": fixture_results,
        "actual_packet_topology_mutations": {
            "dag_projection": {
                "method": "stable archive-order edge projection; cycle-closing edges omitted; rung hashes recomputed with the packet helper",
                "removed_edge_count": len(removed_edges),
                "removed_variation_ids": [edge["variation_id"] for edge in removed_edges],
                "result": packet_dag_projection,
            },
            "rehash_consistent_reverse_edge_injection": {
                "method": "reverse one retained packet edge; recompute variation id and affected rung hash chain with packet helpers; temporary audit copy only",
                "mutation": mutation_detail,
                "result": packet_cycle_injection,
            },
        },
        "tampered_hash_control": tampered_hash,
        "checks": checks,
        "semantic_verdict": {
            "native_contract_accepts_cycles": True,
            "audit_only_strict_contract_rejects_cycles": True,
            "contract_difference_reproduced": contract_differential_closed,
            "production_integrity_defect_admitted": False,
            "status": "contract_semantics_differential_closed_h_remains_red",
        },
        "tool_manifest": {
            "packet PurgatoryPool verifier": "claim_load_bearing for archive-defined integrity",
            "rustworkx": "claim_load_bearing only for the separately labeled DAG policy",
        },
        "blocked_consumers": [
            "packet integrity defect escalation",
            "production verifier change",
            "scientific memory-layer crack claim",
            "Ratchet promotion",
            "Lev promotion",
        ],
        "process_exit_semantics": (
            "exit 0 means the contract differential and controls closed; top-level all_pass remains false "
            "because H does not admit a production integrity defect"
        ),
    }
    receipt["receipt_content_sha256"] = receipt_content_sha256(receipt)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "contract_differential_closed": contract_differential_closed,
                "h_all_pass": False,
                "claim_ceiling": CLAIM_CEILING,
                "receipt": str(args.output.resolve()),
            },
            sort_keys=True,
        )
    )
    return 0 if contract_differential_closed else 1


if __name__ == "__main__":
    raise SystemExit(main())
