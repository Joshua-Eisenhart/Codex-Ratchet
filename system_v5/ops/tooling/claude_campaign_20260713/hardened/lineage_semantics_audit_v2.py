#!/usr/bin/env python3
"""Audit packet-166 variation cycles against the packet's native verifier.

The observed two-cycle is preserved. The script refuses to call it an
integrity defect unless an authoritative contract actually requires the
variation graph to be a DAG.
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
from typing import Any

import rustworkx as rx


HERE = Path(__file__).resolve().parent
DEFAULT_OUTPUT = HERE / "results" / "lineage_semantics_audit_v2_results.json"
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
EXPECTED_ARCHIVE_SHA256 = "42fc2629e076b4cd5b8015514fb1c9027aa7c751702ebc7a719a6b808141b9da"
POOL_MEMBER = "ratchet/purgatory_pool.py"
LEDGER_MEMBER = "sims_and_scripts/living_purgatory_ledger_r2_results.json"
EXPECTED_POOL_SHA256 = "73f152e646e6cd9e0e989c4b0f7ce1f6ca2c39359c951f40648b0a3909a954e8"
EXPECTED_LEDGER_SHA256 = "850e975c1d3e7aee2a78d5614a4d64e21bd0309ef61683ed150c77c209870553"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def cycle_report(graph: rx.PyDiGraph) -> dict[str, Any] | None:
    edges = list(rx.digraph_find_cycle(graph))
    if not edges:
        return None
    return {
        "nodes": [graph[edges[0][0]], *[graph[target] for _, target in edges]],
        "edges": [
            {"parent_id": graph[source], "child_id": graph[target]}
            for source, target in edges
        ],
    }


def fixture_controls() -> dict[str, Any]:
    dag = rx.PyDiGraph()
    dag.add_nodes_from(["root", "left", "right", "leaf"])
    dag.add_edges_from_no_data([(0, 1), (0, 2), (1, 3), (2, 3)])
    cyclic = rx.PyDiGraph()
    cyclic.add_nodes_from(["a", "b", "c"])
    cyclic.add_edges_from_no_data([(0, 1), (1, 2), (2, 0)])
    isolated = rx.PyDiGraph()
    isolated.add_node("only")
    return {
        "dag_fixture_is_dag": bool(rx.is_directed_acyclic_graph(dag)),
        "cycle_fixture_is_not_dag": not bool(rx.is_directed_acyclic_graph(cyclic)),
        "cycle_fixture_is_named": cycle_report(cyclic) is not None,
        "isolated_fixture_is_dag": bool(rx.is_directed_acyclic_graph(isolated)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if Path(sys.executable).resolve() != Path(PYTHON).resolve():
        raise RuntimeError(f"wrong Python runtime: {sys.executable}")

    archive = args.archive.resolve()
    archive_sha = sha256_file(archive)
    if archive_sha != EXPECTED_ARCHIVE_SHA256:
        raise ValueError(f"unexpected packet archive sha256: {archive_sha}")
    with zipfile.ZipFile(archive) as bundle:
        pool_bytes = bundle.read(POOL_MEMBER)
        ledger_bytes = bundle.read(LEDGER_MEMBER)
    if sha256_bytes(pool_bytes) != EXPECTED_POOL_SHA256 or sha256_bytes(ledger_bytes) != EXPECTED_LEDGER_SHA256:
        raise ValueError("packet member hash mismatch")

    raw = json.loads(ledger_bytes)
    with tempfile.TemporaryDirectory(prefix="ratchet-lineage-v2-") as temporary_name:
        temporary = Path(temporary_name)
        pool_path = temporary / "purgatory_pool.py"
        ledger_path = temporary / "ledger.json"
        pool_path.write_bytes(pool_bytes)
        ledger_path.write_bytes(ledger_bytes)
        spec = importlib.util.spec_from_file_location("packet166_purgatory_pool", pool_path)
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to import packet purgatory verifier")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pool = module.PurgatoryPool.load(ledger_path, verify=True)
        native_ok, native_reason = pool.verify_integrity()

        tampered = copy.deepcopy(raw)
        tampered["variation_log"][0]["child_content_sha"] = "0" * 64
        tampered_path = temporary / "tampered-ledger.json"
        tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
        tamper_rejected = False
        tamper_error = ""
        try:
            module.PurgatoryPool.load(tampered_path, verify=True)
        except ValueError as error:
            tamper_rejected = True
            tamper_error = str(error)

    candidate_ids = sorted(raw["entries"])
    index_by_id = {candidate_id: index for index, candidate_id in enumerate(candidate_ids)}
    graph = rx.PyDiGraph(multigraph=True)
    graph.add_nodes_from(candidate_ids)
    graph.add_edges_from_no_data([
        (index_by_id[str(edge["parent_id"])], index_by_id[str(edge["child_id"])])
        for edge in raw["variation_log"]
    ])
    is_dag = bool(rx.is_directed_acyclic_graph(graph))
    cycle = None if is_dag else cycle_report(graph)
    cycle_pairs = set()
    if cycle is not None:
        cycle_pairs = {(edge["parent_id"], edge["child_id"]) for edge in cycle["edges"]}
    cycle_records = [
        {
            "variation_id": edge["variation_id"],
            "parent_id": edge["parent_id"],
            "child_id": edge["child_id"],
            "operator": edge.get("operator"),
            "proposed_at_rung": edge.get("proposed_at_rung"),
        }
        for edge in raw["variation_log"]
        if (edge["parent_id"], edge["child_id"]) in cycle_pairs
    ]
    controls = fixture_controls()
    audit_checks = {
        "archive_and_members_match_pinned_hashes": archive_sha == EXPECTED_ARCHIVE_SHA256,
        "native_packet_integrity_verifier_accepts_ledger": bool(native_ok) and native_reason == "ok",
        "rustworkx_graph_counts_match_native_namespaces": graph.num_nodes() == len(raw["entries"]) and graph.num_edges() == len(raw["variation_log"]),
        "cycle_is_reproducibly_observed": not is_dag and cycle is not None,
        "native_verifier_accepts_the_observed_cycle": bool(native_ok) and not is_dag,
        "tampered_variation_hash_is_rejected_by_native_verifier": tamper_rejected,
        "rustworkx_controls_pass": all(controls.values()),
    }
    audit_completed = all(audit_checks.values())
    ancestry_dag_claim_pass = False
    source_path = Path(__file__).resolve()
    command = [PYTHON, str(source_path), "--archive", str(archive), "--output", str(args.output.resolve())]
    result = {
        "schema": "codex-ratchet.lineage-semantics-audit-result.v2",
        "sim_id": "packet166_variation_graph_semantics",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "runner_identity": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "rustworkx_version": rx.__version__,
        },
        "classification": "contract_semantics_audit",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "source": {
            "archive_path": str(archive),
            "archive_sha256": archive_sha,
            "native_verifier_member": POOL_MEMBER,
            "native_verifier_sha256": sha256_bytes(pool_bytes),
            "ledger_member": LEDGER_MEMBER,
            "ledger_sha256": sha256_bytes(ledger_bytes),
            "audit_path": str(source_path),
            "audit_sha256": sha256_file(source_path),
        },
        "native_integrity_contract": {
            "api": "PurgatoryPool.load(verify=True) + PurgatoryPool.verify_integrity()",
            "accepted": bool(native_ok),
            "reason": native_reason,
            "variation_checks_observed": "endpoint existence, edge schema/id hash, parent/child content hashes, duplicate edge ids, rung variation-id membership",
            "dag_requirement_observed": False,
            "tampered_variation_hash_rejected": tamper_rejected,
            "tamper_error": tamper_error,
        },
        "variation_graph": {
            "interpretation_in_native_source": "mutation lineage / variation transitions",
            "node_count": graph.num_nodes(),
            "edge_count": graph.num_edges(),
            "is_dag": is_dag,
            "one_cycle": cycle,
            "one_cycle_edge_records": cycle_records,
        },
        "semantic_verdict": {
            "cycle_observed": not is_dag,
            "native_integrity_pass": bool(native_ok),
            "append_only_ancestry_contract_found": False,
            "integrity_defect_admitted": False,
            "status": "cycle_observed_but_native_contract_does_not_forbid_it",
            "required_decision": "Either retain mutation-transition semantics with cycles allowed, or explicitly add ancestry-DAG semantics to the authoritative contract and native verifier tests.",
        },
        "controls": controls,
        "audit_checks": audit_checks,
        "audit_completed": audit_completed,
        "ancestry_dag_claim_pass": ancestry_dag_claim_pass,
        "all_pass": False,
        "process_exit_semantics": "exit 0 means the semantics audit completed; top-level all_pass remains false because no ancestry-DAG claim is admitted",
        "tool_manifest": {
            "native PurgatoryPool verifier": "claim_load_bearing for packet-defined ledger integrity",
            "rustworkx": "claim_load_bearing for the bounded graph-cycle observation only",
        },
        "tool_calls": [
            {
                "tool": "packet PurgatoryPool",
                "api": "load(verify=True) and verify_integrity",
                "input": "archive-pinned r2 ledger",
                "output": "native integrity verdict",
                "negative_control": "tampered variation child hash is rejected",
                "gates": ["audit_completed"],
            },
            {
                "tool": "rustworkx",
                "api": "PyDiGraph + is_directed_acyclic_graph + digraph_find_cycle",
                "input": "variation_log parent_id to child_id transitions",
                "output": "cycle observation and named cycle",
                "negative_control": "three-node injected cycle is detected",
                "boundary_control": "isolated-node graph is a DAG",
                "gates": ["audit_completed"],
            },
        ],
        "claim_ceiling": "Packet-local observation that the variation transition graph contains a cycle while the packet's native integrity verifier accepts it. No ledger defect is admitted without an authoritative ancestry-DAG rule.",
        "blocked_consumers": ["packet integrity defect escalation", "scientific memory-layer crack claim", "Ratchet promotion", "Lev graph mutation"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"audit_completed": audit_completed, "all_pass": False, "receipt": str(args.output.resolve()), "semantic_status": result["semantic_verdict"]["status"]}, sort_keys=True))
    return 0 if audit_completed else 1


if __name__ == "__main__":
    raise SystemExit(main())
