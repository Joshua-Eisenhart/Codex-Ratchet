#!/usr/bin/env python3
"""Packet-local validator for manifold_entropy_ledger_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "manifold_entropy_ledger_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = PACKET / "results" / f"{SIM_ID}_envelope_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def as_dict(value: Any, errors: list[str], name: str) -> dict[str, Any]:
    require(isinstance(value, dict), errors, f"{name} must be an object")
    return value if isinstance(value, dict) else {}


def no_forbidden_word(errors: list[str]) -> None:
    forbidden = "".join(["fix", "ture"])
    for path in PACKET.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".jl", ".md", ".json"}:
            text = path.read_text(errors="ignore").lower()
            require(forbidden not in text, errors, f"forbidden word appears in {path.relative_to(ROOT)}")


def main() -> int:
    result_path = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULT
    payload = json.loads(result_path.read_text())
    errors: list[str] = []

    require(payload.get("schema_version") == "three_engine_sim_result_v1", errors, "schema version mismatch")
    require(payload.get("sim_id") == SIM_ID, errors, "sim_id mismatch")
    require(payload.get("classification") == "scratch_diagnostic", errors, "classification ceiling mismatch")
    require(payload.get("promotion_allowed") is False, errors, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, errors, "formal_admission_allowed must be false")
    require(payload.get("all_pass") is True, errors, "all_pass must be true")
    require(payload.get("tool_calls_one_to_one") is True, errors, "tool_calls_one_to_one must be true")
    errors.extend(builder_audit_boundary_errors(payload, PACKET / "audit_verdict.md"))

    ledger = as_dict(payload.get("ledger"), errors, "ledger")
    measure = as_dict(ledger.get("measure_level"), errors, "ledger.measure_level")
    chain = as_dict(measure.get("chain_rule_check"), errors, "chain_rule_check")
    require(chain.get("pass") is True, errors, "chain rule must pass")
    require(chain.get("defect_exact") == "0", errors, "chain defect must be exact zero")

    controls = as_dict(payload.get("controls"), errors, "controls")
    for key in ["wrong_log_base", "wrong_flat_eta_marginal", "wrong_lens_group_order"]:
        row = as_dict(controls.get(key), errors, f"controls.{key}")
        require(row.get("detected") is True, errors, f"{key} must be detected")

    free_to_leaf = as_dict(ledger.get("conditioning_deltas"), errors, "conditioning_deltas").get("free_to_leaf", {})
    require(free_to_leaf.get("honest_drop") == "infinite", errors, "free-to-leaf drop must be infinite")

    proofs = as_dict(payload.get("crossover_proofs"), errors, "crossover_proofs")
    for key in ["z3", "cvc5", "julia_z3"]:
        row = as_dict(proofs.get(key), errors, f"crossover_proofs.{key}")
        require(row.get("ran") is True, errors, f"{key} must run")
        require(row.get("load_bearing") is True, errors, f"{key} must be load-bearing")
        require(row.get("verdict") == "unsat", errors, f"{key} verdict must be unsat")
        require(row.get("erased_flip_control_can_fail") is True, errors, f"{key} erased control must fail")

    anchors = payload.get("carrier_level_anchors")
    require(isinstance(anchors, list) and len(anchors) >= 6, errors, "carrier anchors n=3..8 are required")
    if isinstance(anchors, list):
        ns = {str(row.get("n")) for row in anchors if isinstance(row, dict)}
        for n in range(3, 9):
            require(str(n) in ns, errors, f"missing carrier anchor n={n}")

    parent_lineage = as_dict(payload.get("parent_lineage"), errors, "parent_lineage")
    for required in [
        "geo_disintegration_machinery_v0",
        "geo_nested_disintegration_v0",
        "geo_union_rule_k_leaves_v0",
        "compression_flow_radiated_record_v0",
        "ratchet_s2_three_shell_chain_v0",
        "ratchet_s6_terrain_operator_shell_v0",
    ]:
        row = as_dict(parent_lineage.get(required), errors, f"parent_lineage.{required}")
        require(bool(row.get("result_blob")) and bool(row.get("result_sha256")), errors, f"{required} must be hash-bound")

    declared = payload.get("claim_path_tools")
    called = [row.get("tool") for row in payload.get("tool_calls", []) if isinstance(row, dict)]
    require(isinstance(declared, list) and set(declared) == set(called) and len(declared) == len(called), errors, "claim_path_tools/tool_calls one-to-one mismatch")

    no_forbidden_word(errors)

    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "result_json": str(result_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
