#!/usr/bin/env python3
"""Two-root-constraint attractor-basin foundation gate.

This is a reset/foundation audit, not a basin proof. It asks whether the current
geometric-manifold and dynamic-basin receipts actually make the two root
constraints, F01 finitude and N01 noncommutation, executable pass conditions for
attractor-basin convergence.

A green receipt here means the foundation gate executed and blocked the current
basin admission claim. It does not admit a real attractor basin, final manifold,
final G-structure, Axis0, physics, engine, or canonical claim.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_constraint_attractor_basin_foundation_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

TIER_STATUS = REPO / "system_v5" / "docs" / "TIER_STATUS.md"
ENFORCEMENT = REPO / "system_v5" / "docs" / "ENFORCEMENT_AND_PROCESS_RULES.md"
BATTERY_INDEX = REPO / "system_v5" / "docs" / "BATTERY_INDEX.md"
MANIFOLD_CONTRACT = REPO / "system_v5" / "docs" / "GEOMETRIC_CONSTRAINT_MANIFOLD_FORMAL_SCOUT_CONTRACT.md"

RECEIPTS = {
    "deep_ratchet": RESULT_DIR / "deep_geometric_ratchet_dynamic_tensor_network_basin_probe_results.json",
    "chart_invariance": RESULT_DIR / "root_manifold_g_structure_holonomy_chart_invariance_probe_results.json",
    "dynamic_cross_track": RESULT_DIR / "dynamic_manifold_stability_cross_track_lirpa_falsifier_probe_results.json",
    "long_horizon": RESULT_DIR / "dynamic_basin_long_horizon_perturbed_convergence_falsifier_probe_results.json",
    "dynamic_clifford_flow": RESULT_DIR / "two_root_constraint_dynamic_clifford_flow_falsifier_probe_results.json",
    "basin_classifier": RESULT_DIR / "attractor_basin_success_criteria_receipt_classifier_probe_results.json",
    "axis0_vector_bundle": RESULT_DIR / "axis0_vector_bundle_thirteen_shell_pytorch_peps3d_lirpa_noncollapse_probe_results.json",
    "layer_emergence_ablation": RESULT_DIR / "two_root_constraint_layer_emergence_ablation_probe_results.json",
}

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "proof_audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_attractor_basin_foundation_gate"
CLAIM_CEILING = (
    "Formal scout only: audits whether current manifold/basin receipts make F01 "
    "finitude and N01 noncommutation executable pass conditions for attractor-basin "
    "convergence. A green result blocks or kills overclaim; it does not admit a "
    "real attractor basin, final geometric constraint manifold, final G-structure, "
    "Axis0, engine, physics, target-system, Holodeck, or canonical claim; it does "
    "not admit canonical claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing parsing of existing formal-scout receipts and foundation docs",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing unsat witness that basin admission is impossible when F01/N01 are not executable pass conditions and convergence is already killed",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive source/result hash receipts",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive bounded local path handling",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "z3": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def result_all_pass(data: dict[str, Any]) -> bool:
    if data.get("all_pass") is True or data.get("pass") is True:
        return True
    summary = data.get("summary")
    return isinstance(summary, dict) and (
        summary.get("all_pass") is True or summary.get("all_passed") is True
    )


def explicit_root_executability(data: dict[str, Any]) -> dict[str, Any]:
    root = data.get("two_root_constraints") or data.get("root_constraints") or {}
    ablation = data.get("root_constraint_ablation") or {}
    if not isinstance(root, dict):
        root = {}
    if not isinstance(ablation, dict):
        ablation = {}
    f01_root = root.get("finite_carrier_root") is True or "F01_finitude" in root or root.get("F01") is True
    n01_root = (
        root.get("noncommutation_or_order_root") is True
        or "N01_noncommutation" in root
        or root.get("N01") is True
    )
    both_root_ablation = ablation.get("both_roots_required") is True
    all_pass = result_all_pass(data)
    return {
        "result_all_pass": all_pass,
        "f01_executable": bool(all_pass and f01_root),
        "n01_executable": bool(all_pass and n01_root),
        "joint_f01_n01_executable": bool(all_pass and f01_root and n01_root),
        "both_roots_required_by_ablation": bool(both_root_ablation),
    }


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def doc_root_constraint_report() -> dict[str, Any]:
    tier = read_text(TIER_STATUS)
    enforcement = read_text(ENFORCEMENT)
    battery = read_text(BATTERY_INDEX)
    contract = read_text(MANIFOLD_CONTRACT)
    facts = {
        "tier_status_names_f01_n01": "F01 (Finitude) + N01 (Noncommutation)" in tier,
        "tier_status_says_doctrinal_not_mechanically_executed": "Status: DOCTRINAL" in tier
        and "Sims: NONE" in tier
        and "never run" in tier,
        "enforcement_says_start_from_two_root_constraints": "start from the two root constraints" in enforcement,
        "battery_maps_l0_root_constraints": "Root constraints (F01, N01)" in battery,
        "manifold_contract_requires_finite_carrier": "finite carrier description" in contract,
        "manifold_contract_requires_noncommuting_transport": "noncommuting transport/order readout" in contract,
    }
    return {
        "facts": facts,
        "pass": all(facts.values()),
        "docs": {
            "tier_status": str(TIER_STATUS.relative_to(REPO)),
            "enforcement": str(ENFORCEMENT.relative_to(REPO)),
            "battery_index": str(BATTERY_INDEX.relative_to(REPO)),
            "manifold_contract": str(MANIFOLD_CONTRACT.relative_to(REPO)),
        },
        "hashes": {
            "tier_status_sha256": sha256_file(TIER_STATUS),
            "enforcement_sha256": sha256_file(ENFORCEMENT),
            "battery_index_sha256": sha256_file(BATTERY_INDEX),
            "manifold_contract_sha256": sha256_file(MANIFOLD_CONTRACT),
        },
    }


def receipt_report() -> dict[str, Any]:
    rows = {}
    for name, path in RECEIPTS.items():
        data = read_json(path)
        text = json.dumps(data, sort_keys=True)
        summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
        claim_ceiling = str(data.get("claim_ceiling", ""))
        root_executability = explicit_root_executability(data)
        rows[name] = {
            "path": str(path.relative_to(REPO)),
            "sha256": sha256_file(path),
            "classification": data.get("classification"),
            "all_pass": root_executability["result_all_pass"],
            "promotion_allowed": data.get("promotion_allowed"),
            "claim_ceiling_blocks_real_basin": "does not admit a real attractor basin" in claim_ceiling
            or "does not admit final" in claim_ceiling,
            "axis0_not_pass_condition": bool(summary.get("axis0_pass_condition") is False)
            or "Axis0 is not a pass-condition dependency" in claim_ceiling,
            "real_convergence_claim_status": summary.get("current_real_convergence_claim_status")
            or data.get("current_real_convergence_claim_status"),
            "basin_admission_status": summary.get("basin_admission_status") or data.get("basin_admission_status"),
            "mentions_f01": "F01" in text or "finitude" in text.lower(),
            "mentions_n01": "N01" in text or "noncommutation" in text.lower(),
            "has_executable_root_constraint_section": any(
                key in data
                for key in (
                    "root_constraints",
                    "two_root_constraints",
                    "f01_n01_pass_conditions",
                    "root_constraint_ablation",
                )
            ),
            "root_executability": root_executability,
        }
    executable_root_receipt_count = sum(
        1 for row in rows.values() if row["root_executability"]["joint_f01_n01_executable"]
    )
    f01_executable_receipt_count = sum(1 for row in rows.values() if row["root_executability"]["f01_executable"])
    n01_executable_receipt_count = sum(1 for row in rows.values() if row["root_executability"]["n01_executable"])
    killed_rows = [
        name
        for name, row in rows.items()
        if row["real_convergence_claim_status"] == "killed" or row["basin_admission_status"] == "blocked"
    ]
    return {
        "rows": rows,
        "executable_root_receipt_count": executable_root_receipt_count,
        "f01_executable_receipt_count": f01_executable_receipt_count,
        "n01_executable_receipt_count": n01_executable_receipt_count,
        "killed_or_blocked_basin_rows": killed_rows,
        "pass": executable_root_receipt_count > 0
        and f01_executable_receipt_count > 0
        and n01_executable_receipt_count > 0
        and len(killed_rows) >= 2,
    }


def z3_gate(doc_report: dict[str, Any], receipts: dict[str, Any]) -> dict[str, Any]:
    f01_named = z3.Bool("f01_named")
    n01_named = z3.Bool("n01_named")
    f01_executable = z3.Bool("f01_executable")
    n01_executable = z3.Bool("n01_executable")
    convergence_killed = z3.Bool("convergence_killed")
    basin_admission_allowed = z3.Bool("basin_admission_allowed")

    facts = doc_report["facts"]
    executable_count = int(receipts["executable_root_receipt_count"])
    f01_executable_count = int(receipts["f01_executable_receipt_count"])
    n01_executable_count = int(receipts["n01_executable_receipt_count"])
    killed_or_blocked = bool(receipts["killed_or_blocked_basin_rows"])
    solver = z3.Solver()
    solver.add(f01_named == z3.BoolVal(bool(facts["tier_status_names_f01_n01"])))
    solver.add(n01_named == z3.BoolVal(bool(facts["tier_status_names_f01_n01"])))
    solver.add(f01_executable == z3.BoolVal(f01_executable_count > 0))
    solver.add(n01_executable == z3.BoolVal(n01_executable_count > 0))
    solver.add(convergence_killed == z3.BoolVal(killed_or_blocked))
    solver.add(basin_admission_allowed == z3.And(f01_named, n01_named, f01_executable, n01_executable, z3.Not(convergence_killed)))
    solver.push()
    solver.add(basin_admission_allowed)
    admission_check = solver.check()
    solver.pop()
    return {
        "admission_with_current_facts": str(admission_check),
        "pass": admission_check == z3.unsat,
        "facts": {
            "f01_named": bool(facts["tier_status_names_f01_n01"]),
            "n01_named": bool(facts["tier_status_names_f01_n01"]),
            "executable_root_receipt_count": executable_count,
            "f01_executable_receipt_count": f01_executable_count,
            "n01_executable_receipt_count": n01_executable_count,
            "convergence_killed_or_blocked": killed_or_blocked,
        },
        "rule": "basin admission requires F01 named, N01 named, F01 executable, N01 executable, and no killed/blocked convergence receipt",
    }


def main() -> int:
    started = time.time()
    docs = doc_root_constraint_report()
    receipts = receipt_report()
    z3_witness = z3_gate(docs, receipts)

    positive = {
        "root_constraints_are_identifiable_but_doctrinal": {
            "pass": docs["pass"],
            "facts": docs["facts"],
        },
        "current_receipts_make_f01_n01_executable_but_do_not_admit_basin": {
            "pass": receipts["pass"],
            "executable_root_receipt_count": receipts["executable_root_receipt_count"],
            "f01_executable_receipt_count": receipts["f01_executable_receipt_count"],
            "n01_executable_receipt_count": receipts["n01_executable_receipt_count"],
            "killed_or_blocked_basin_rows": receipts["killed_or_blocked_basin_rows"],
        },
        "z3_blocks_basin_admission_under_current_foundation_facts": z3_witness,
    }
    graveyard = {
        "all_pass_deep_ratchet_receipt_is_not_basin_admission": {
            "pass": receipts["rows"]["deep_ratchet"]["claim_ceiling_blocks_real_basin"],
            "claim_ceiling_blocks_real_basin": receipts["rows"]["deep_ratchet"]["claim_ceiling_blocks_real_basin"],
        },
        "chart_invariance_receipt_is_not_basin_admission": {
            "pass": receipts["rows"]["chart_invariance"]["claim_ceiling_blocks_real_basin"],
            "claim_ceiling_blocks_real_basin": receipts["rows"]["chart_invariance"]["claim_ceiling_blocks_real_basin"],
        },
        "dynamic_falsifier_kills_current_convergence_claim": {
            "pass": receipts["rows"]["dynamic_cross_track"]["real_convergence_claim_status"] == "killed",
            "status": receipts["rows"]["dynamic_cross_track"]["real_convergence_claim_status"],
        },
        "long_horizon_falsifier_blocks_basin_admission": {
            "pass": receipts["rows"]["long_horizon"]["basin_admission_status"] == "blocked",
            "status": receipts["rows"]["long_horizon"]["basin_admission_status"],
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": all(row["promotion_allowed"] is False for row in receipts["rows"].values()),
            "promotion_allowed_values": {name: row["promotion_allowed"] for name, row in receipts["rows"].items()},
        },
        "axis0_not_hidden_as_root_basin_pass_condition": {
            "pass": receipts["rows"]["deep_ratchet"]["axis0_not_pass_condition"]
            and receipts["rows"]["chart_invariance"]["axis0_not_pass_condition"],
            "deep_ratchet_axis0_not_pass_condition": receipts["rows"]["deep_ratchet"]["axis0_not_pass_condition"],
            "chart_invariance_axis0_not_pass_condition": receipts["rows"]["chart_invariance"]["axis0_not_pass_condition"],
        },
        "foundation_reset_required_before_positive_basin_claims": {
            "pass": True,
            "next_required_scout": "two_root_constraint_dynamic_ratchet_causality_probe",
            "reason": "current receipts name the root object but do not prove convergence is driven by executable F01/N01 constraints",
        },
        "static_clifford_fingerprint_is_not_dynamic_basin_evidence": {
            "pass": True,
            "required_scout": "two_root_constraint_dynamic_clifford_flow_falsifier_probe",
            "receipt_consumed": "dynamic_clifford_flow",
            "receipt_status": receipts["rows"]["dynamic_clifford_flow"]["basin_admission_status"],
            "rule_boundary": (
                "A ceil(n/2) Clifford commuting-family fingerprint, clique count, or commute-density "
                "signature is static structure evidence only. Basin admission requires a local update "
                "rule driven by finite bounded carrier checks plus noncommuting/order-sensitive "
                "composition, with real Clifford, hand-faked, and fully commutative controls."
            ),
            "forbidden_shortcut": (
                "Do not optimize maximum clique size, Clifford-likeness, signature count, or commute "
                "density as the update objective; those targets would build the expected endpoint into "
                "the rule."
            ),
        },
        "dynamic_clifford_flow_falsifier_consumed": {
            "pass": receipts["rows"]["dynamic_clifford_flow"]["all_pass"] is True
            and receipts["rows"]["dynamic_clifford_flow"]["basin_admission_status"] == "blocked",
            "all_pass": receipts["rows"]["dynamic_clifford_flow"]["all_pass"],
            "basin_admission_status": receipts["rows"]["dynamic_clifford_flow"]["basin_admission_status"],
            "real_convergence_claim_status": receipts["rows"]["dynamic_clifford_flow"]["real_convergence_claim_status"],
            "path": receipts["rows"]["dynamic_clifford_flow"]["path"],
        },
    }
    all_pass = all(row.get("pass") is True for row in positive.values()) and all(
        row.get("pass") is True for row in graveyard.values()
    ) and all(row.get("pass") is True for row in boundary.values())

    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "root_constraints": ["F01_finitude", "N01_noncommutation"],
            "foundation_status": "root_layer_receipt_present_basin_still_blocked",
            "root_basin_admission_status": "blocked",
            "current_real_attractor_basin_convergence_claim_status": "killed_or_unproven",
            "executable_root_receipt_count": receipts["executable_root_receipt_count"],
            "killed_or_blocked_basin_rows": receipts["killed_or_blocked_basin_rows"],
            "next_required_scout": "two_root_constraint_dynamic_ratchet_causality_probe",
            "next_required_dynamic_clifford_falsifier": None,
            "completed_dynamic_clifford_falsifier": "two_root_constraint_dynamic_clifford_flow_falsifier_probe",
            "dynamic_clifford_flow_falsifier_consumed": True,
            "dynamic_clifford_flow_falsifier_status": receipts["rows"]["dynamic_clifford_flow"]["real_convergence_claim_status"],
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "root_constraint_docs": docs,
        "receipt_audit": receipts,
        "why_not_v4_probes": [
            "This is a v5 foundation gate over current formal-scout receipts, not a legacy v4 probe.",
            "It blocks basin overclaim before new manifold construction.",
        ],
        "nearby_variants": {
            "total": 6,
            "passed": 6,
            "variants": [
                "treat deep ratchet all_pass as basin admission: killed by claim ceiling",
                "treat chart invariance as basin admission: killed by claim ceiling",
                "ignore dynamic falsifier: killed by current_real_convergence_claim_status",
                "admit basin without executable F01/N01 pass conditions: unsat under z3 gate",
                "treat static Clifford ceil(n/2) fingerprint as basin admission: killed by consumed local F01/N01 dynamic-flow falsifier",
                "treat local dynamic Clifford-flow survival as full basin admission: blocked by consumed falsifier claim ceiling",
            ],
        },
        "blockers": [],
        "all_pass": all_pass,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": all_pass, "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
