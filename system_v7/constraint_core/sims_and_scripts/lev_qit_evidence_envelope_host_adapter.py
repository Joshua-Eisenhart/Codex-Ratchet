#!/usr/bin/env python3
"""lev_qit_evidence_envelope_host_adapter -- lift the UP-93 emitter envelope
(constraint_core.lev_qit_engine_perception_evidence.v1) into the schema the live
Lev host consumer accepts (three_engine_sim_result_v1, qit-evidence-consumer.ts
0.1.0). Additive: the emitter and the Lev consumer are both left untouched; this
closes the measured seam between them (live dry-run 2026-07-07: 11 boundary
findings, error_code QIT_EVIDENCE_BLOCKED).

The adapter changes NAMES AND SHAPE ONLY. Every ceiling in the source envelope
is preserved verbatim; blocked_consumers becomes the union of the source list
and the host's five required names; nothing is promoted.

Falsifiable control (same discipline as the emitter): a promoting twin
(truth_state=canon, graph_mutation_allowed=true, promotion_allowed=true) must
FAIL the local host-rule validator that the honest output passes.

classification="scratch_diagnostic". promotion_allowed=False.
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "lev_qit_engine_perception_evidence_v56.json")
OUT = os.path.join(HERE, "lev_qit_engine_perception_evidence_v56_host_adapted.json")

# Mirrors qit-evidence-consumer.ts (0.1.0) -- keep in sync with the Lev host.
REQUIRED_BLOCKED_CONSUMERS = [
    "QIT_engine_admission",
    "Axis0",
    "FEP",
    "Lev_mesh_runtime",
    "production_perception",
]
REQUIRED_CONTRACT_FALSE = [
    "graph_mutation_allowed",
    "mesh_projection_allowed",
    "compositor_apply_allowed",
    "source_boundary_mutated",
    "cr_object_id_is_lev_entity_id",
]


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def host_rules_ok(env):
    """Local rendering of the Lev host boundary checks. Returns (ok, problems)."""
    problems = []
    if env.get("schema_version") != "three_engine_sim_result_v1":
        problems.append("schema_version")
    if not env.get("sim_id"):
        problems.append("sim_id")
    if env.get("classification") != "scratch_diagnostic":
        problems.append("classification")
    if env.get("promotion_allowed") is not False:
        problems.append("promotion_allowed")
    if env.get("formal_admission_allowed") is not False:
        problems.append("formal_admission_allowed")
    if not isinstance(env.get("all_pass"), bool):
        problems.append("all_pass")
    blocked = env.get("blocked_consumers") or []
    for name in REQUIRED_BLOCKED_CONSUMERS:
        if name not in blocked:
            problems.append(f"blocked_consumers.{name}")
    contract = env.get("lev_host_consumer_contract") or {}
    if contract.get("truth_state") != "proposed":
        problems.append("contract.truth_state")
    if contract.get("evidence_kind") != "measurement":
        problems.append("contract.evidence_kind")
    if contract.get("decision_ceiling") != "accepted_as_evidence_only":
        problems.append("contract.decision_ceiling")
    for field in REQUIRED_CONTRACT_FALSE:
        if contract.get(field) is not False:
            problems.append(f"contract.{field}")
    return (not problems), problems


def build(source, source_path):
    contract = dict(source["lev_host_consumer_contract"])
    contract.setdefault("evidence_kind", "measurement")
    # all_pass is computed, not asserted: the source must carry a green
    # mechanical run, a passing source-fidelity linter, scratch promotion
    # status, and forbidden outputs absent.
    all_pass = (
        "GREEN" in str(source.get("mechanical_run_status", ""))
        and "PASS" in str(source.get("source_fidelity_status", ""))
        and source.get("promotion_status") == "scratch_diagnostic"
        and source.get("forbidden_outputs_absent") is True
    )
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": "lev_qit_engine_perception_evidence_v56_host_adapted",
        "object_id": "lev_qit_engine_perception_evidence_v56_host_adapted",
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine": "host_schema_adapter",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "all_pass": all_pass,
        "lifecycle_status": "SCRATCH_DIAGNOSTIC",
        "evidence_grade": "scratch_diagnostic_measurement",
        "claim_ceiling": source["claim_ceiling"],
        "claim": (
            "Shape-lift of the UP-93 perception-evidence envelope into the Lev "
            "host consumer schema; measurement evidence only, no new claims."
        ),
        "blocked_consumers": sorted(
            set(source["blocked_consumers"]) | set(REQUIRED_BLOCKED_CONSUMERS)
        ),
        "lev_host_consumer_contract": contract,
        "tool_intent": source.get("tool_intent"),
        "world_entry_payload": source.get("world_entry_payload"),
        "source_envelope_schema": source["schema_version"],
        "source_envelope_path": os.path.basename(source_path),
        "source_envelope_sha256": sha256_file(source_path),
        "source_bundle": source["source_bundle"],
        "adapter_note": "names/shape lifted only; all source ceilings preserved verbatim",
    }


def main():
    source = json.load(open(SOURCE))
    adapted = build(source, SOURCE)

    ok, problems = host_rules_ok(adapted)
    print(f"  adapted envelope passes local host rules: {ok} {problems if problems else ''}")

    # Falsifiable control: the promoting twin must FAIL the same validator.
    twin = json.loads(json.dumps(adapted))
    twin["lev_host_consumer_contract"]["truth_state"] = "canon"
    twin["lev_host_consumer_contract"]["graph_mutation_allowed"] = True
    twin["promotion_allowed"] = True
    twin_ok, twin_problems = host_rules_ok(twin)
    print(f"  CONTROL promoting twin rejected: {not twin_ok} ({len(twin_problems)} problems)")

    gates = ok and not twin_ok and adapted["all_pass"]
    if gates:
        with open(OUT, "w") as fh:
            json.dump(adapted, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print("PASS lev_qit_evidence_envelope_host_adapter")
        print(f"ALL_GATES: PASS -> {OUT}")
        return 0
    print("FAIL lev_qit_evidence_envelope_host_adapter")
    return 1


if __name__ == "__main__":
    sys.exit(main())
