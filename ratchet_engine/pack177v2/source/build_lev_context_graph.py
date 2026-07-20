#!/usr/bin/env python3
"""Project Ratchet receipts and fuel obligations into a Leviathan graph."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / "receipts"


def load(name: str):
    return json.loads((RECEIPTS / name).read_text(encoding="utf-8"))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha(value):
    return "sha256:" + hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def main() -> int:
    campaign = load("campaign_receipt.json")
    r3 = load("r3_projection_eligibility.json")
    r6 = load("r6_full_recompute.json")
    controls = load("controls.json")
    fuel = load("fuel_obligations.json")
    schedule = load("fuel_schedule_projection.json")
    proposal = load("proposal_fuel_projection.json")
    campaign_id = "lev://entity/ratchet/campaign/fuel-bearing-completion-v0-2"
    compiler_id = "lev://entity/ratchet/compiler/residual-to-obligation-v0-2"
    queue_id = "lev://entity/ratchet/queue/source-fair-fuel-v0-2"
    nodes = [
        {"id": campaign_id, "type": "campaign", "status": campaign["status"]},
        {
            "id": compiler_id,
            "type": "fuel_compiler",
            "status": fuel["status"],
            "mathematical_authority": False,
        },
        {
            "id": queue_id,
            "type": "fair_logistical_queue",
            "status": schedule["status"],
            "epistemic_score_used": False,
        },
        {
            "id": "lev://entity/ratchet/pawl/source-family-balance-v0-1",
            "type": "packet_local_pawl",
            "status": "engaged" if controls["packet_local_pawl"]["engaged"] else "held",
        },
    ]
    edges = [
        {"from": campaign_id, "to": compiler_id, "relation": "supplies_residuals"},
        {"from": compiler_id, "to": queue_id, "relation": "projects_all_obligations"},
    ]
    r6_by_handle = {row["handle"]: row for row in r6["sources"]}
    fuel_by_handle = {row["handle"]: row for row in fuel["sources"]}
    for source in r3["sources"]:
        handle = source["handle"]
        source_id = f"lev://entity/ratchet/source/{handle}"
        frontier_id = f"lev://entity/ratchet/frontier/{handle}"
        nodes.append(
            {
                "id": source_id,
                "type": "anonymous_source_projection",
                "claim_ceiling": source["claim_ceiling"],
            }
        )
        nodes.append(
            {
                "id": frontier_id,
                "type": "completion_frontier",
                "repair_split": r6_by_handle[handle]["full_recompute"]["repair_split"],
            }
        )
        edges.append({"from": source_id, "to": campaign_id, "relation": "measured_by"})
        edges.append({"from": campaign_id, "to": frontier_id, "relation": "recomputed"})
        for obligation in fuel_by_handle[handle]["obligations"]:
            obligation_id = "lev://entity/ratchet/obligation/" + hashlib.sha256(
                obligation["obligation_id"].encode("utf-8")
            ).hexdigest()[:24]
            nodes.append(
                {
                    "id": obligation_id,
                    "type": "mathematical_obligation",
                    "kind": obligation["kind"],
                    "status": obligation["mathematical_status"],
                    "epistemic_priority": None,
                }
            )
            edges.append({"from": frontier_id, "to": obligation_id, "relation": "exposes"})
            edges.append({"from": obligation_id, "to": queue_id, "relation": "scheduled_by"})
    for entry in proposal["entries"]:
        proposal_id = "lev://entity/ratchet/proposal-fuel/" + entry["id"].lower()
        nodes.append(
            {
                "id": proposal_id,
                "type": "proposal_fuel",
                "layer": entry["layer"],
                "status": entry["status"],
                "selector_access": False,
            }
        )
        edges.append({"from": proposal_id, "to": queue_id, "relation": "eligible_for_typed_routing"})
    pawl_id = "lev://entity/ratchet/pawl/source-family-balance-v0-1"
    edges.append({"from": pawl_id, "to": campaign_id, "relation": "guards_replay"})
    graph = {
        "schema_version": "ratchet.lev-context-graph/0.2",
        "native_graph_ingestion_status": "PROJECTION_READY_NOT_YET_INGESTED",
        "nodes": sorted(nodes, key=lambda row: row["id"]),
        "edges": sorted(edges, key=canonical),
        "campaign_receipt_sha256": sha(campaign),
        "fuel_obligation_receipt_sha256": sha(fuel),
        "proposal_fuel_receipt_sha256": sha(proposal),
        "mathematical_authority": False,
    }
    graph["graph_fingerprint"] = sha({"nodes": graph["nodes"], "edges": graph["edges"]})
    (RECEIPTS / "lev_context_graph.json").write_text(
        json.dumps(graph, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"PASS Lev graph projection {len(nodes)} nodes {len(edges)} edges")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
