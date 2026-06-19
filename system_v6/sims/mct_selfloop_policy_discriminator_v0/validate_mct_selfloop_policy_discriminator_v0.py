#!/usr/bin/env python3
"""Packet-local validator for mct_selfloop_policy_discriminator_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "mct_selfloop_policy_discriminator_v0"
EXPECTED_G0_SHA256 = "bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0"
ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_results.json"
TABLE = ROOT / "system_v6" / "sims" / SIM_ID / "results" / f"{SIM_ID}_table.md"


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    require(errors, RESULT.exists(), f"missing result {RESULT}")
    require(errors, TABLE.exists(), f"missing table {TABLE}")
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2, sort_keys=True))
        return 1

    obj: dict[str, Any] = json.loads(RESULT.read_text(encoding="utf-8"))
    require(errors, obj.get("schema_version") == "policy_discriminator_table_v0", "bad schema_version")
    require(errors, obj.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
    require(errors, obj.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(errors, obj.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(errors, obj.get("claim_ceiling") == "policy_discriminator_table_only", "bad claim ceiling")
    require(errors, obj.get("decision_status") == "owner_gated", "decision must remain owner_gated")
    require(errors, obj.get("recommendation_emitted") is False, "recommendation must not be emitted")
    require(
        errors,
        obj.get("authority_receipts", {}).get("g0_transition_graph_sha256_observed") == EXPECTED_G0_SHA256,
        "G0 graph hash not pinned",
    )

    branches = obj.get("branches", {})
    erase = branches.get("erase", {})
    retain = branches.get("retain", {})
    require(errors, bool(erase) and bool(retain), "both erase and retain branches required")
    require(errors, erase.get("relation_edge_count_unique") == 1, "erase unique folded edge count must be 1")
    require(errors, retain.get("relation_edge_count_unique") == 3, "retain unique folded edge count must be 3")
    require(errors, erase.get("erased_transport_edge_count") == 196, "erase must ledger 196 erased transport rows")
    require(errors, retain.get("self_loop_transport_edge_count") == 196, "retain must keep 196 self-loop transport rows")
    require(errors, erase.get("terminal_structure", {}).get("terminal_nodes") == [1], "erase terminal node mismatch")
    require(errors, retain.get("terminal_structure", {}).get("terminal_nodes") == [1], "retain terminal node mismatch")

    erase_must = erase.get("may_must_semantics", {}).get("sure_basin_omega_containment_must", {})
    retain_must = retain.get("may_must_semantics", {}).get("sure_basin_omega_containment_must", {})
    require(errors, erase_must.get("folded_nodes") == [0, 1], "erase must semantics should force both folded nodes")
    require(errors, retain_must.get("folded_nodes") == [1], "retain must semantics should keep only terminal folded node")
    require(errors, obj.get("vacuity_control", {}).get("branches_differ_somewhere_computable") is True, "branches must differ")

    consumers = obj.get("downstream_consumer_impact", [])
    packets = {row.get("packet") for row in consumers}
    require(errors, "mct_dynamic_admissibility_packet_v0" in packets, "missing dynamic packet consumer row")
    require(errors, "mct_nonassoc_weld_packet_v0" in packets, "missing nonassoc weld consumer row")

    table_text = TABLE.read_text(encoding="utf-8")
    require(errors, "Decision status: owner-gated" in table_text, "table must state owner-gated status")
    require(errors, "recommendation" in table_text.lower(), "table must mention no recommendation")

    output = {
        "ok": not errors,
        "errors": errors,
        "checked": {
            "result": RESULT.relative_to(ROOT).as_posix(),
            "table": TABLE.relative_to(ROOT).as_posix(),
            "g0_hash": EXPECTED_G0_SHA256,
            "branch_edge_counts": {
                "erase": erase.get("relation_edge_count_unique"),
                "retain": retain.get("relation_edge_count_unique"),
            },
            "branch_must_sizes": {
                "erase": erase_must.get("size"),
                "retain": retain_must.get("size"),
            },
        },
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
