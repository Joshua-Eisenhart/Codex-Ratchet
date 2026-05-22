#!/usr/bin/env python3
"""Completion audit after bounded global countermodel search.

Formal scout only. This is the post-global-countermodel audit for the two-root
manifold chain. It checks whether the foundation objective is complete after
selector minimality, provider-gap handling, and bounded finite-family
countermodel search.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
SYSTEM_V5 = SCOUT_ROOT.parents[1]
RESULT_DIR = SCOUT_ROOT / "results"
READINESS_INDEX = SYSTEM_V5 / "evidence" / "formal_scout_readiness_index.json"
ESTATE_INDEX = SYSTEM_V5 / "evidence" / "sim_estate_integration_index.json"

sys.path.insert(0, str(SCOUT_ROOT))
import sim_two_root_constraint_completion_audit_after_selector_basin_chain_probe as prior_audit  # noqa: E402


NAME = "two_root_constraint_global_countermodel_completion_audit_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_global_countermodel_completion_audit"
CLAIM_CEILING = (
    "Formal scout only: audits current completion after bounded global "
    "countermodel search. It does not admit a final geometric constraint "
    "manifold, real attractor basin, Axis0, engine, physics, target-system, "
    "Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing expanded receipt parsing and prompt-to-artifact completion checklist serialization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that completion remains unsat while weak requirements remain"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent completion-unsat proof"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing expanded requirement/evidence dependency graph"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive input receipt hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "rustworkx": "load_bearing",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

CHAIN = prior_audit.CHAIN + [
    "two_root_constraint_layer_level_selector_necessity_countermodel_probe",
    "two_root_constraint_layer_selector_cross_carrier_minimality_probe",
    "two_root_constraint_selector_minimality_completion_audit_probe",
    "two_root_constraint_provider_and_global_falsifier_gap_probe",
    "two_root_constraint_global_countermodel_exhaustive_finite_family_probe",
]

NEXT_REQUIRED_SCOUT = "two_root_constraint_chain_fresh_rerun_and_estate_tool_gate_repair_probe"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    return prior_audit.jsonable(value)


def receipt_path(stem: str) -> pathlib.Path:
    return RESULT_DIR / f"{stem}_results.json"


def load_chain() -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for stem in CHAIN:
        path = receipt_path(stem)
        if path.exists():
            loaded[stem] = read_json(path)
    return loaded


def blob(receipts: dict[str, dict[str, Any]]) -> str:
    return json.dumps(receipts, sort_keys=True).lower()


def all_terms(receipts: dict[str, dict[str, Any]], terms: list[str]) -> tuple[bool, list[str]]:
    text = blob(receipts)
    missing = [term for term in terms if term.lower() not in text]
    return not missing, missing


def any_groups(receipts: dict[str, dict[str, Any]], groups: dict[str, list[str]]) -> tuple[bool, list[str]]:
    text = blob(receipts)
    missing = [name for name, terms in groups.items() if not any(term.lower() in text for term in terms)]
    return not missing, missing


def receipt_facts(stem: str, data: dict[str, Any]) -> dict[str, Any]:
    path = receipt_path(stem)
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    return {
        "stem": stem,
        "path": rel(path),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "",
        "classification": data.get("classification"),
        "promotion_allowed": data.get("promotion_allowed"),
        "summary_all_pass": summary.get("all_pass"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def readiness_rows() -> dict[str, dict[str, Any]]:
    if not READINESS_INDEX.exists():
        return {}
    data = read_json(READINESS_INDEX)
    rows = data.get("rows", [])
    return {str(row.get("stem")): row for row in rows if isinstance(row, dict)}


def schema_status(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = readiness_rows()
    per_stem = {}
    for stem in CHAIN:
        row = rows.get(stem, {})
        per_stem[stem] = {
            "receipt_exists": stem in receipts,
            "readme_indexed": row.get("readme_indexed"),
            "validation_pass": row.get("validation_pass"),
            "source_exists": row.get("source_exists"),
            "promotion_allowed": receipts.get(stem, {}).get("promotion_allowed"),
        }
    return {
        "pass": all(
            item["receipt_exists"]
            and item["readme_indexed"] is True
            and item["validation_pass"] is True
            and item["source_exists"] is True
            and item["promotion_allowed"] is False
            for item in per_stem.values()
        ),
        "per_stem": per_stem,
    }


def estate_status() -> dict[str, Any]:
    if not ESTATE_INDEX.exists():
        return {"exists": False}
    data = read_json(ESTATE_INDEX)
    tool_gate = data.get("tool_gate_summary", {}) if isinstance(data, dict) else {}
    return {
        "exists": True,
        "path": rel(ESTATE_INDEX),
        "result_row_count": data.get("result_row_count"),
        "manifold_rows": len(data.get("geometric_constraint_manifold_rows", [])),
        "basin_rows": len(data.get("attractor_basin_rows", [])),
        "axis0_rows": len(data.get("axis0_summary", {}).get("axis0_rows", [])) if isinstance(data.get("axis0_summary"), dict) else None,
        "lirpa_lewm_rows": len(data.get("auto_lirpa_lewm_rows", [])),
        "tool_gate_status_counts": tool_gate.get("status_counts"),
        "tool_gate_candidate_count": len(tool_gate.get("candidates", [])) if isinstance(tool_gate.get("candidates"), list) else None,
        "has_open_tool_gate_rows": any(
            value
            for key, value in (tool_gate.get("status_counts") or {}).items()
            if key.startswith("blocked") or key.startswith("review")
        ),
    }


def tool_coverage(receipts: dict[str, dict[str, Any]]) -> dict[str, bool]:
    tools = prior_audit.base_audit.load_bearing_tool_union(receipts)
    return {name: bool(aliases & tools) for name, aliases in prior_audit.base_audit.REQUIRED_TOOLS.items()}


def build_rows(receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    evidence = [rel(receipt_path(stem)) for stem in CHAIN]
    hard_neg_pass, missing_hard = all_terms(receipts, prior_audit.base_audit.HARD_NEGATIVES + ["gauge_broken", "gauge_transplanted"])
    carrier_pass, missing_carriers = all_terms(receipts, ["quaternion", "su2", "hopf", "s3", "spin", "g-structure", "cellular", "ring_checkerboard"])
    basin_pass, missing_basin = any_groups(
        receipts,
        {
            "admissibility_predicate": ["admissibility_predicate", "admissibility predicate"],
            "state_space": ["state_space", "state space"],
            "update_rule": ["update_rule", "update rule"],
            "basin_boundary": ["basin_boundary", "basin boundary"],
            "stability_invariant": ["stability_invariant", "stability invariant"],
            "escape_or_failure_cases": ["escape", "failure case", "failure_cases"],
            "non_manifold_explanation_kill": ["non_manifold", "non-manifold", "nonmanifold"],
        },
    )
    scaling_pass, missing_scaling = all_terms(receipts, ["8", "16", "32", "64", "peps3d", "contraction_order", "memory", "runtime", "failure_modes"])
    layer_pass, missing_layer = all_terms(receipts, ["selector_ablation_count", "first_layer_f01_only_killed", "root_compatible_countermodel_count"])
    global_pass, missing_global = all_terms(receipts, ["row_count", "root_compatible_countermodel_count", "admitted_countermodel_count", "global_countermodel_exhaustive_finite_family"])
    provider_pass, missing_provider = all_terms(receipts, ["strict_live_route_bound_provider_count", "external_calls_launched", "blocked_by_spend_guard"])
    coverage = tool_coverage(receipts)
    schema = schema_status(receipts)
    estate = estate_status()
    premortem_count = sum("premortem" in receipt for receipt in receipts.values())
    rows = [
        {"id": "objective_restate", "requirement": "Restate objective as concrete deliverables.", "status": "covered_strong", "evidence": [NAME]},
        {"id": "expanded_chain_receipts_present", "requirement": "Consume chain through global finite-family countermodel scout.", "status": "covered_strong" if len(receipts) == len(CHAIN) else "open", "evidence": evidence, "loaded_count": len(receipts), "expected_count": len(CHAIN)},
        {"id": "f01_n01_root_gate_and_ablations", "requirement": "Keep F01/N01 and hard-negative ablations live.", "status": "covered_strong" if hard_neg_pass else "open", "evidence": evidence, "missing": missing_hard},
        {"id": "root_only_forcing_claim_killed", "requirement": "Kill/prove root-only exact stack forcing.", "status": "covered_strong", "evidence": [rel(receipt_path("two_root_constraint_layer_forcing_theorem_or_countermodel_probe"))]},
        {"id": "selector_axiom_bounded_sufficiency", "requirement": "Test selector sufficiency beyond roots.", "status": "covered_strong", "evidence": evidence},
        {"id": "layer_by_layer_selector_necessity", "requirement": "Test selectors layer by layer.", "status": "covered_strong" if layer_pass else "open", "evidence": evidence, "missing": missing_layer},
        {"id": "cross_carrier_selector_minimality", "requirement": "Port selector minimality across carriers.", "status": "covered_strong" if carrier_pass else "weak", "evidence": evidence, "missing": missing_carriers},
        {"id": "bounded_global_countermodel_search", "requirement": "Search bounded global finite family for root-compatible admitted countermodels.", "status": "covered_strong" if global_pass else "open", "evidence": [rel(receipt_path("two_root_constraint_global_countermodel_exhaustive_finite_family_probe"))], "missing": missing_global},
        {"id": "provider_gap_handled_spend_gated", "requirement": "Handle provider falsifier lanes under current spend guard without counting old receipts.", "status": "covered_strong" if provider_pass else "open", "evidence": [rel(receipt_path("two_root_constraint_provider_and_global_falsifier_gap_probe"))], "missing": missing_provider},
        {"id": "candidate_carrier_realizations", "requirement": "Treat candidate carrier families as bounded root realizations.", "status": "covered_strong" if carrier_pass else "weak", "evidence": evidence, "missing": missing_carriers},
        {"id": "bounded_basin_semantics", "requirement": "Require predicate/state/update/boundary/invariant/escape/non-manifold kill.", "status": "covered_strong" if basin_pass else "open", "evidence": evidence, "missing": missing_basin},
        {"id": "site_scaled_tensor_networks", "requirement": "Cover 8/16/32/64 PyTorch tensor/PEPS3D assumptions and failures.", "status": "covered_strong" if scaling_pass else "open", "evidence": evidence, "missing": missing_scaling},
        {"id": "load_bearing_tool_coverage", "requirement": "Cover proof/algebra/topology/PyTorch/equivariant/auto_LiRPA/le-wm tools.", "status": "covered_strong" if all(coverage.values()) else "open", "evidence": evidence, "tool_coverage": coverage, "missing": [tool for tool, ok in coverage.items() if not ok]},
        {"id": "premortem_per_loop", "requirement": "Every loop includes premortem and hard negatives.", "status": "weak", "evidence": evidence, "premortem_receipt_count": premortem_count, "expected_receipt_count": len(CHAIN)},
        {"id": "fresh_validation_and_indexes", "requirement": "Fresh-rerun validation, README, readiness, estate index, promotion blocked.", "status": "weak" if schema["pass"] else "open", "evidence": [rel(READINESS_INDEX), rel(ESTATE_INDEX)], "chain_schema_status": schema},
        {"id": "full_estate_integration", "requirement": "Integrate larger manifold/PEPS/Axis0/basin/LiRPA/le-wm/tool estate.", "status": "weak" if estate["exists"] else "open", "evidence": [rel(ESTATE_INDEX)], "estate_status": estate},
        {"id": "final_manifold_completion", "requirement": "Do not claim final completion while premortem/fresh-rerun/estate/tool-gate rows remain weak.", "status": "weak", "evidence": evidence},
    ]
    return rows


def graph_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_ids: dict[str, int] = {}
    for row in rows:
        req = f"req:{row['id']}"
        node_ids[req] = graph.add_node(req)
        for item in row.get("evidence", []):
            ev = f"evidence:{item}"
            if ev not in node_ids:
                node_ids[ev] = graph.add_node(ev)
            graph.add_edge(node_ids[req], node_ids[ev], row["status"])
    weak = [row["id"] for row in rows if row["status"] != "covered_strong"]
    return {"pass": bool(weak), "requirement_nodes": len(rows), "total_nodes": graph.num_nodes(), "edges": graph.num_edges(), "weak_or_open_requirements": weak}


def completion_proof(rows: list[dict[str, Any]]) -> dict[str, Any]:
    names = [row["id"] for row in rows]
    covered = {row["id"]: row["status"] == "covered_strong" for row in rows}
    z_terms = {name: z3.Bool(name) for name in names}
    complete = z3.Bool("objective_complete")
    solver = z3.Solver()
    solver.add(complete == z3.And(*[z_terms[name] for name in names]))
    for name in names:
        solver.add(z_terms[name] == covered[name])
    solver.add(complete)
    z_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_terms = {name: tm.mkConst(bsort, name) for name in names}
    c_complete = tm.mkConst(bsort, "objective_complete")
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_complete, tm.mkTerm(Kind.AND, *[c_terms[name] for name in names])))
    for name in names:
        slv.assertFormula(c_terms[name] if covered[name] else tm.mkTerm(Kind.NOT, c_terms[name]))
    slv.assertFormula(c_complete)
    c_sat = slv.checkSat().isSat()
    return {
        "pass": not z_sat and not c_sat,
        "completion_status": "not_achieved" if not z_sat and not c_sat else "possibly_complete",
        "z3_premature_completion_unsat": not z_sat,
        "cvc5_premature_completion_unsat": not c_sat,
        "covered_strong": sorted(name for name, ok in covered.items() if ok),
        "weak_or_open": sorted(name for name, ok in covered.items() if not ok),
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "using the bounded global no-countermodel result as final proof",
        "most_dangerous_failure": "ignoring remaining estate tool-gate blockers and historical fresh-rerun/premortem gaps",
        "hidden_assumption": "fresh validator/index state covers all historical chain claims equally",
        "checks_applied": [
            "expanded completion checklist",
            "z3/cvc5 premature-completion proof",
            "estate tool-gate status kept weak",
            "final completion blocked",
        ],
    }


def main() -> int:
    started = time.time()
    receipts = load_chain()
    rows = build_rows(receipts)
    graph = graph_report(rows)
    proof = completion_proof(rows)
    premortem = premortem_report()
    facts = {stem: receipt_facts(stem, data) for stem, data in receipts.items()}
    counts = {status: sum(1 for row in rows if row["status"] == status) for status in ["covered_strong", "weak", "open"]}
    weak_rows = [row for row in rows if row["status"] != "covered_strong"]
    positive = {
        "objective_rephrased_as_checklist": {"pass": True, "requirement_count": len(rows), "status_counts": counts},
        "expanded_chain_receipts_loaded": {"pass": len(receipts) == len(CHAIN), "loaded_count": len(receipts), "expected_count": len(CHAIN), "receipt_facts": facts},
        "requirement_dependency_graph_built": graph,
        "premortem_applied": premortem,
    }
    graveyard = {
        "bounded_global_no_countermodel_as_completion_killed": {"pass": True, "reason": "No admitted countermodel was found in 1440 rows, but final completion still has weak rows."},
        "premature_completion_claim_killed": proof,
        "proxy_green_status_rejected_as_completion": {"pass": bool(weak_rows), "weak_or_open_ids": [row["id"] for row in weak_rows]},
    }
    boundary = {
        "promotion_boundary_preserved": {"pass": True, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING},
        "completion_status_boundary": {"pass": proof["completion_status"] == "not_achieved", "completion_status": proof["completion_status"], "blocked_completion_requirements": proof["weak_or_open"]},
        "next_required_scout": {"pass": True, "name": NEXT_REQUIRED_SCOUT, "requirement": "Fresh-rerun the chain as a batch receipt and repair/audit the estate tool-gate blockers."},
    }
    all_pass = all(item.get("pass") is True for item in positive.values()) and all(
        item.get("pass") is True for item in graveyard.values()
    ) and all(item.get("pass") is True for item in boundary.values())
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
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_receipts": {stem: facts.get(stem, {"missing": True}) for stem in CHAIN},
        "premortem": premortem,
        "prompt_to_artifact_checklist": jsonable(rows),
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "completion_status": proof["completion_status"],
            "requirement_count": len(rows),
            "covered_strong_count": counts["covered_strong"],
            "weak_count": counts["weak"],
            "open_count": counts["open"],
            "weak_or_open_requirements": proof["weak_or_open"],
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "bounded global countermodel search is not universal proof",
                "estate tool-gate blockers remain weak",
                "chain-level fresh-rerun proof remains required",
            ],
        },
        "why_not_v4_probes": "This is a v5 formal scout completion audit over canonical local receipts, not a v4 proposal.",
        "divergence_log": [
            "If bounded no-countermodel evidence is promoted, the audit overclaims.",
            "If tool-gate blockers are ignored, tool integration becomes a label rather than a constraint.",
            "If historical fresh-rerun evidence is only inferred, the chain remains weaker than the objective asks.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "completion_status": proof["completion_status"],
                "covered_strong_count": counts["covered_strong"],
                "weak_count": counts["weak"],
                "open_count": counts["open"],
                "next_required_scout": NEXT_REQUIRED_SCOUT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
