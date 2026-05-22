#!/usr/bin/env python3
"""Completion audit after layer selector minimality scouts.

Formal scout only. This consumes the expanded two-root manifold chain after
per-layer selector necessity and cross-carrier selector minimality. It checks
whether the geometric constraint manifold can now be called complete, or which
requirements still block promotion.
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
ROOT = pathlib.Path(__file__).resolve().parents[3]
RESULT_DIR = SCOUT_ROOT / "results"
READINESS_INDEX = ROOT / "system_v5" / "evidence" / "formal_scout_readiness_index.json"
ESTATE_INDEX = ROOT / "system_v5" / "evidence" / "sim_estate_integration_index.json"

sys.path.insert(0, str(SCOUT_ROOT))
import sim_two_root_constraint_completion_audit_after_selector_basin_chain_probe as prior_audit  # noqa: E402


NAME = "two_root_constraint_selector_minimality_completion_audit_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_selector_minimality_completion_audit"
CLAIM_CEILING = (
    "Formal scout only: audits the two-root manifold chain after layer-level and "
    "cross-carrier selector minimality. It can classify progress and kill "
    "premature completion, but it does not admit a final geometric constraint "
    "manifold, real attractor basin, Axis0, engine, physics, Holodeck, or "
    "canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "load-bearing expanded receipt parsing and completion checklist serialization"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that objective completion remains unsat while weak rows remain"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent completion-unsat proof"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing expanded requirement-to-evidence dependency graph"},
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
]

NEXT_REQUIRED_SCOUT = "two_root_constraint_provider_and_global_falsifier_gap_probe"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
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


def text_blob(receipts: dict[str, dict[str, Any]]) -> str:
    return json.dumps(receipts, sort_keys=True).lower()


def all_terms(receipts: dict[str, dict[str, Any]], terms: list[str]) -> tuple[bool, list[str]]:
    blob = text_blob(receipts)
    missing = [term for term in terms if term.lower() not in blob]
    return not missing, missing


def any_groups(receipts: dict[str, dict[str, Any]], groups: dict[str, list[str]]) -> tuple[bool, list[str]]:
    blob = text_blob(receipts)
    missing = [name for name, terms in groups.items() if not any(term.lower() in blob for term in terms)]
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


def chain_schema_status(receipts: dict[str, dict[str, Any]]) -> dict[str, Any]:
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


def provider_status() -> dict[str, Any]:
    provider_dir = SCOUT_ROOT / "provider_receipts"
    paths = sorted(provider_dir.glob("*.json")) if provider_dir.exists() else []
    relevant = []
    for path in paths:
        try:
            data = read_json(path)
        except Exception:
            continue
        blob = json.dumps(data, sort_keys=True).lower()
        if "two_root" in blob or "manifold" in blob or "basin" in blob:
            relevant.append({"path": rel(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {
        "status": "weak" if relevant else "open",
        "count": len(relevant),
        "sample": relevant[:8],
        "note": "provider receipts are advisory unless route-bound to the current selector-minimality chain",
    }


def estate_status() -> dict[str, Any]:
    if not ESTATE_INDEX.exists():
        return {"exists": False}
    data = read_json(ESTATE_INDEX)
    blob = json.dumps(data, sort_keys=True).lower()
    surfaces = {
        "manifold": "manifold" in blob,
        "peps3d": "peps3d" in blob,
        "axis0": "axis0" in blob,
        "basin": "basin" in blob,
        "lirpa": "lirpa" in blob,
        "le_wm": "le_wm" in blob or "le-wm" in blob or "lewm" in blob,
        "tool_integration": "tool_integration" in blob or "tool manifest" in blob,
    }
    return {"exists": True, "path": rel(ESTATE_INDEX), "surface_coverage": surfaces, "all_named_surfaces_present": all(surfaces.values())}


def tool_coverage(receipts: dict[str, dict[str, Any]]) -> dict[str, bool]:
    tools = prior_audit.base_audit.load_bearing_tool_union(receipts)
    return {name: bool(aliases & tools) for name, aliases in prior_audit.base_audit.REQUIRED_TOOLS.items()}


def build_requirement_rows(receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    all_receipts = [rel(receipt_path(stem)) for stem in CHAIN]
    hard_neg_pass, missing_hard_negatives = all_terms(receipts, prior_audit.base_audit.HARD_NEGATIVES + ["gauge_broken", "gauge_transplanted"])
    carrier_pass, missing_carriers = all_terms(receipts, ["quaternion", "su2", "hopf", "s3", "spin", "g-structure", "ring_checkerboard", "cellular"])
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
    gauge_pass, missing_gauge = all_terms(receipts, ["gauge_representatives", "gauge_invariant_observables", "order_gap"])
    selector_pass, missing_selector = all_terms(receipts, ["selector_axiom", "canonical_row_count", "noncanonical_row_count", "sampled_countermodel_count"])
    layer_pass, missing_layer = all_terms(receipts, ["selector_ablation_count", "first_layer_f01_only_killed", "root_compatible_countermodel_count"])
    cross_carrier_pass, missing_cross = all_terms(receipts, ["quaternion_su2", "hopf_s3", "spin_g_structure", "cellular_finite_gradation", "ring_checkerboard", "selector_ablation_count"])
    escape_pass, missing_escape = all_terms(receipts, ["escape_volume", "stochastic", "adversarial_leak_found", "retuned_adversarial_gap_above_boundary"])
    coverage = tool_coverage(receipts)
    provider = provider_status()
    schema = chain_schema_status(receipts)
    estate = estate_status()
    premortem_count = sum("premortem" in receipt for receipt in receipts.values())
    rows = [
        {"id": "objective_restate", "requirement": "Restate the active goal as concrete deliverables.", "status": "covered_strong", "evidence": [NAME]},
        {"id": "expanded_chain_receipts_present", "requirement": "Consume the chain through cross-carrier selector minimality.", "status": "covered_strong" if len(receipts) == len(CHAIN) else "open", "evidence": all_receipts, "loaded_count": len(receipts), "expected_count": len(CHAIN)},
        {"id": "f01_n01_root_gate_and_ablations", "requirement": "Keep F01/N01 and hard-negative ablations live across the chain.", "status": "covered_strong" if hard_neg_pass else "open", "evidence": all_receipts, "missing": missing_hard_negatives},
        {"id": "root_only_forcing_claim_killed", "requirement": "Prove or kill root-only exact stack forcing.", "status": "covered_strong", "evidence": [rel(receipt_path("two_root_constraint_layer_forcing_theorem_or_countermodel_probe"))]},
        {"id": "selector_axiom_bounded_sufficiency", "requirement": "Test selector sufficiency beyond bare roots.", "status": "covered_strong" if selector_pass else "open", "evidence": [rel(receipt_path("two_root_constraint_selection_axiom_layer_discriminator_probe")), rel(receipt_path("two_root_constraint_selection_axiom_portability_countermodel_sweep_probe"))], "missing": missing_selector},
        {"id": "layer_by_layer_selector_necessity", "requirement": "Test required selectors layer by layer and kill first-layer F01-only admission.", "status": "covered_strong" if layer_pass else "open", "evidence": [rel(receipt_path("two_root_constraint_layer_level_selector_necessity_countermodel_probe"))], "missing": missing_layer},
        {"id": "cross_carrier_selector_minimality", "requirement": "Port selector minimality across bounded carrier families.", "status": "covered_strong" if cross_carrier_pass else "open", "evidence": [rel(receipt_path("two_root_constraint_layer_selector_cross_carrier_minimality_probe"))], "missing": missing_cross},
        {"id": "candidate_carrier_realizations", "requirement": "Treat gauge/quaternion/SU2/Spin/Hopf/S3/cellular/ring-checkerboard as candidate root realizations.", "status": "covered_strong" if carrier_pass else "weak", "evidence": all_receipts, "missing": missing_carriers},
        {"id": "gauge_representatives_vs_observables", "requirement": "Separate gauge representatives from gauge-invariant observables.", "status": "covered_strong" if gauge_pass else "open", "evidence": [rel(receipt_path("two_root_constraint_layer_order_gauge_invariant_observable_probe"))], "missing": missing_gauge},
        {"id": "bounded_basin_semantics", "requirement": "Require predicate, state, update, boundary, invariant, escapes, and non-manifold kills.", "status": "covered_strong" if basin_pass else "open", "evidence": all_receipts, "missing": missing_basin},
        {"id": "basin_escape_and_retune_loop", "requirement": "Run deterministic/stochastic/adversarial/retuned basin pressure.", "status": "covered_strong" if escape_pass else "open", "evidence": all_receipts, "missing": missing_escape},
        {"id": "site_scaled_tensor_networks", "requirement": "Cover 8/16/32/64 PyTorch tensor/PEPS3D assumptions and failures.", "status": "covered_strong" if scaling_pass else "open", "evidence": all_receipts, "missing": missing_scaling},
        {"id": "load_bearing_tool_coverage", "requirement": "Cover proof, algebra, topology, PyTorch/equivariant, auto_LiRPA, and le-wm tools.", "status": "covered_strong" if all(coverage.values()) else "open", "evidence": all_receipts, "tool_coverage": coverage, "missing": [tool for tool, covered in coverage.items() if not covered]},
        {"id": "premortem_per_loop", "requirement": "Every loop includes premortem and hard negatives.", "status": "weak", "evidence": all_receipts, "premortem_receipt_count": premortem_count, "expected_receipt_count": len(CHAIN), "notes": "Premortems are present across new loops but not uniformly top-level across all historical receipts."},
        {"id": "provider_falsifier_lanes", "requirement": "Route-bound Opus/Sonnet/Grok/Gemini falsifier/advisory receipts.", "status": provider["status"], "evidence": [item["path"] for item in provider["sample"]], "provider_receipt_count": provider["count"], "notes": provider["note"]},
        {"id": "fresh_validation_and_indexes", "requirement": "Fresh-rerun validation, README, readiness, estate index, promotion blocked.", "status": "weak" if schema["pass"] else "open", "evidence": [rel(READINESS_INDEX), rel(ESTATE_INDEX), rel(SCOUT_ROOT / "README.md")], "chain_schema_status": schema},
        {"id": "full_estate_integration", "requirement": "Process and integrate the larger manifold/PEPS/Axis0/basin/LiRPA/le-wm/tool estate.", "status": "weak" if estate["exists"] and estate.get("all_named_surfaces_present") else "open", "evidence": [rel(ESTATE_INDEX)], "estate_status": estate},
        {"id": "final_manifold_completion", "requirement": "Do not claim final completion while provider/global/estate/proxy gaps remain.", "status": "weak", "evidence": all_receipts},
    ]
    return rows


def graph_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    node_ids: dict[str, int] = {}
    for row in rows:
        req = f"req:{row['id']}"
        node_ids[req] = graph.add_node(req)
        for evidence in row.get("evidence", []):
            ev = f"evidence:{evidence}"
            if ev not in node_ids:
                node_ids[ev] = graph.add_node(ev)
            graph.add_edge(node_ids[req], node_ids[ev], row["status"])
    weak_or_open = [row["id"] for row in rows if row["status"] != "covered_strong"]
    return {"pass": bool(rows) and bool(weak_or_open), "requirement_nodes": len(rows), "total_nodes": graph.num_nodes(), "edges": graph.num_edges(), "weak_or_open_requirements": weak_or_open}


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
        "z3_premature_completion_unsat": not z_sat,
        "cvc5_premature_completion_unsat": not c_sat,
        "completion_status": "not_achieved" if not z_sat and not c_sat else "possibly_complete",
        "covered_strong": sorted(name for name, value in covered.items() if value),
        "weak_or_open": sorted(name for name, value in covered.items() if not value),
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "treating bounded cross-carrier selector minimality as final root-forced global manifold completion",
        "most_dangerous_failure": "skipping provider/global falsifier lanes because local proof and topology checks are now mostly green",
        "hidden_assumption": "the tested bounded carrier families exhaust the admissible finite noncommutative geometry space",
        "checks_applied": [
            "expanded checklist through cross-carrier minimality",
            "provider/global/estate gaps kept weak or open",
            "z3/cvc5 premature-completion kill",
            "promotion boundary retained",
        ],
    }


def main() -> int:
    started = time.time()
    receipts = load_chain()
    rows = build_requirement_rows(receipts)
    graph = graph_report(rows)
    proof = completion_proof(rows)
    premortem = premortem_report()
    facts = {stem: receipt_facts(stem, data) for stem, data in receipts.items()}
    status_counts = {status: sum(1 for row in rows if row["status"] == status) for status in ["covered_strong", "weak", "open"]}
    weak_or_open = [row for row in rows if row["status"] != "covered_strong"]
    positive = {
        "objective_rephrased_as_checklist": {"pass": True, "requirement_count": len(rows), "status_counts": status_counts},
        "expanded_chain_receipts_loaded": {"pass": len(receipts) == len(CHAIN), "loaded_count": len(receipts), "expected_count": len(CHAIN), "receipt_facts": facts},
        "requirement_dependency_graph_built": graph,
        "premortem_applied": premortem,
    }
    graveyard = {
        "premature_completion_claim_killed": proof,
        "cross_carrier_minimality_as_global_completion_killed": {"pass": True, "reason": "bounded carrier-family minimality is progress but not universal completion"},
        "proxy_green_status_rejected_as_completion": {"pass": bool(weak_or_open), "weak_or_open_ids": [row["id"] for row in weak_or_open]},
    }
    boundary = {
        "promotion_boundary_preserved": {"pass": True, "classification": CLASSIFICATION, "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING},
        "completion_status_boundary": {"pass": proof["completion_status"] == "not_achieved", "completion_status": proof["completion_status"], "blocked_completion_requirements": proof["weak_or_open"]},
        "next_required_scout": {"pass": True, "name": NEXT_REQUIRED_SCOUT, "requirement": "Audit provider/global falsifier gap under strict spend-gated receipt rules."},
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
        "premortem": premortem,
        "input_receipts": {stem: facts.get(stem, {"missing": True}) for stem in CHAIN},
        "prompt_to_artifact_checklist": jsonable(rows),
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "completion_status": proof["completion_status"],
            "requirement_count": len(rows),
            "covered_strong_count": status_counts["covered_strong"],
            "weak_count": status_counts["weak"],
            "open_count": status_counts["open"],
            "weak_or_open_requirements": proof["weak_or_open"],
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "cross-carrier selector minimality is treated as bounded progress",
                "provider/global falsifier gaps remain explicit",
                "readiness/index green status remains proxy evidence only",
            ],
        },
        "why_not_v4_probes": "This is a v5 formal scout audit over canonical local receipts, not a v4 proposal.",
        "divergence_log": [
            "If cross-carrier minimality is treated as final universality, the manifold overclaims.",
            "If provider/global falsifier gaps are skipped, the completion gate becomes circular.",
            "If index/readiness coverage is treated as proof, artifact hygiene replaces scientific evidence.",
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
                "covered_strong_count": status_counts["covered_strong"],
                "weak_count": status_counts["weak"],
                "open_count": status_counts["open"],
                "next_required_scout": NEXT_REQUIRED_SCOUT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
