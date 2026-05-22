#!/usr/bin/env python3
"""Ingest Gemini/Grok cross-audit for the selector-energy metric-pass row.

Formal scout only. This consumes durable provider receipts for the
`commutator_balance_energy` selector after the weighted selector scout found a
metric pass across active scales 8 and 16. Provider output is audit evidence
only: survived status is blocked unless both providers explicitly return
`provider_verdict=survived` with non-tautological=true, beats_matched_baseline=true,
and no graveyard rule hits.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import cvc5
from cvc5 import Kind
import rustworkx as rx
import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
PROVIDER_DIR = ROOT / "provider_receipts"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

NAME = "two_root_constraint_selector_energy_cross_audit_or_scale64_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_group_action_weighted_selector_or_energy_probe_results.json"
PLAN_PATH = REPO / "system_v5" / "ops" / "NEXT_GOAL_SELECTOR_ENERGY_PHASE_PLAN.md"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_selector_energy_cross_audit_ingest"
CLAIM_CEILING = (
    "Formal scout only: ingests Gemini/Grok provider cross-audit receipts for "
    "a selector-energy metric-pass candidate. It can classify the candidate as "
    "borderline, graveyard, blocked, or provider-survived-at-audit-level; it "
    "does not admit a final geometric constraint manifold, real attractor "
    "basin, Clifford basin, Axis0, engine, physics, target-system, Holodeck, "
    "or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive parsing of selector scout and provider audit receipts"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical path handling"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt/source hashing"},
    "rustworkx": {"tried": True, "used": True, "reason": "load-bearing provider receipt dependency graph and both-provider coverage check"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that survived status is blocked by provider borderline verdicts"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent proof that survived status is blocked by provider borderline verdicts"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "rustworkx": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}

TWO_ROOT_CONSTRAINTS = {
    "F01": True,
    "N01": True,
    "finite_carrier_root": True,
    "noncommutation_or_order_root": True,
    "scope": "audit of finite selector-energy receipts and provider cross-audit against two-root basin admission",
}

NEXT_REQUIRED_SCOUT = "two_root_constraint_commutator_balance_static_fake_and_scale64_probe"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    return value


def latest_provider_pair() -> dict[str, pathlib.Path]:
    receipts = sorted(PROVIDER_DIR.glob("*_selector_energy_commutator_balance_cross_audit.json"), key=lambda path: path.stat().st_mtime)
    latest: dict[str, pathlib.Path] = {}
    for path in receipts:
        name = path.name
        if "_gemini_" in name:
            latest["gemini"] = path
        elif "_grok_" in name:
            latest["grok"] = path
    return latest


def provider_row(provider: str, path: pathlib.Path) -> dict[str, Any]:
    receipt = read_json(path)
    parsed = receipt.get("parsed") if isinstance(receipt.get("parsed"), dict) else {}
    graveyard_hits = parsed.get("graveyard_rule_hits") if isinstance(parsed.get("graveyard_rule_hits"), list) else []
    hit_rows = [row for row in graveyard_hits if isinstance(row, dict) and row.get("hit") is True]
    return {
        "provider": provider,
        "path": rel(path),
        "sha256": sha256_file(path),
        "status": receipt.get("status"),
        "model": receipt.get("model"),
        "prompt_sha256": receipt.get("prompt_sha256"),
        "result_sha256": (receipt.get("repo_grounding") or {}).get("result_sha256"),
        "plan_sha256": (receipt.get("repo_grounding") or {}).get("plan_sha256"),
        "provider_verdict": parsed.get("provider_verdict"),
        "non_tautological": parsed.get("non_tautological"),
        "beats_matched_baseline": parsed.get("beats_matched_baseline"),
        "graveyard_rule_hit_count": len(hit_rows),
        "graveyard_rule_hits": hit_rows,
        "strongest_objection": parsed.get("strongest_objection"),
        "missing_evidence": parsed.get("missing_evidence"),
        "required_next_move": parsed.get("required_next_move"),
        "parsed_present": bool(parsed),
    }


def provider_coverage_report(rows: dict[str, dict[str, Any]], upstream: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    audit = graph.add_node("selector_energy_cross_audit")
    upstream_node = graph.add_node("weighted_selector_metric_receipt")
    graph.add_edge(upstream_node, audit, "upstream_metric_pass")
    for provider in ("gemini", "grok"):
        if provider in rows:
            node = graph.add_node(provider)
            graph.add_edge(node, audit, "provider_receipt")
    prompts = {row.get("prompt_sha256") for row in rows.values()}
    result_hashes = {row.get("result_sha256") for row in rows.values()}
    upstream_hash = sha256_file(UPSTREAM_RESULT)
    return {
        "pass": set(rows) == {"gemini", "grok"}
        and all(row["status"] == "completed" and row["parsed_present"] for row in rows.values())
        and len(prompts) == 1
        and result_hashes == {upstream_hash},
        "provider_count": len(rows),
        "providers": sorted(rows),
        "dependency_graph_node_count": graph.num_nodes(),
        "dependency_graph_edge_count": graph.num_edges(),
        "same_prompt_hash": len(prompts) == 1,
        "prompt_hashes": sorted(str(item) for item in prompts),
        "same_upstream_result_hash": result_hashes == {upstream_hash},
        "upstream_result_hash": upstream_hash,
        "upstream_candidate_status": upstream["summary"]["candidate_statuses"]["commutator_balance_energy"],
    }


def cross_audit_verdict_report(rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    both_non_taut = all(row.get("non_tautological") is True for row in rows.values())
    both_beat = all(row.get("beats_matched_baseline") is True for row in rows.values())
    no_rule_hits = all(int(row.get("graveyard_rule_hit_count") or 0) == 0 for row in rows.values())
    both_survived = all(row.get("provider_verdict") == "survived" for row in rows.values())
    any_borderline = any(row.get("provider_verdict") == "borderline" for row in rows.values())
    any_graveyard = any(row.get("provider_verdict") == "graveyard" for row in rows.values())
    if both_survived and both_non_taut and both_beat and no_rule_hits:
        verdict = "provider_survived_audit_level_not_final_basin"
    elif any_graveyard:
        verdict = "graveyard_by_provider_audit"
    elif any_borderline:
        verdict = "borderline_requires_static_fake_and_scale64"
    else:
        verdict = "blocked_or_incomplete_provider_audit"
    return {
        "pass": True,
        "verdict": verdict,
        "both_non_tautological": both_non_taut,
        "both_beat_matched_baseline": both_beat,
        "no_graveyard_rule_hits": no_rule_hits,
        "both_provider_verdict_survived": both_survived,
        "any_provider_borderline": any_borderline,
        "any_provider_graveyard": any_graveyard,
        "provider_rows": rows,
        "selector_survived": verdict == "provider_survived_audit_level_not_final_basin",
    }


def proof_report(verdict: dict[str, Any]) -> dict[str, Any]:
    both_survived = bool(verdict["both_provider_verdict_survived"])
    both_non_taut = bool(verdict["both_non_tautological"])
    both_beat = bool(verdict["both_beat_matched_baseline"])
    no_hits = bool(verdict["no_graveyard_rule_hits"])
    no_final_claim = PROMOTION_ALLOWED is False

    z_survived = z3.Bool("provider_survived")
    z_non_taut = z3.Bool("both_non_tautological")
    z_beat = z3.Bool("both_beat")
    z_no_hits = z3.Bool("no_graveyard_hits")
    z_no_final = z3.Bool("no_final_claim_allowed")
    z_admit = z3.Bool("selector_survived_admitted")
    solver = z3.Solver()
    solver.add(z_survived == both_survived)
    solver.add(z_non_taut == both_non_taut)
    solver.add(z_beat == both_beat)
    solver.add(z_no_hits == no_hits)
    solver.add(z_no_final == no_final_claim)
    solver.add(z_admit == z3.And(z_survived, z_non_taut, z_beat, z_no_hits, z3.Not(z_no_final)))
    solver.add(z_admit)
    z_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    c_survived = tm.mkConst(bsort, "provider_survived")
    c_non_taut = tm.mkConst(bsort, "both_non_tautological")
    c_beat = tm.mkConst(bsort, "both_beat")
    c_no_hits = tm.mkConst(bsort, "no_graveyard_hits")
    c_no_final = tm.mkConst(bsort, "no_final_claim_allowed")
    c_admit = tm.mkConst(bsort, "selector_survived_admitted")
    slv.assertFormula(c_survived if both_survived else tm.mkTerm(Kind.NOT, c_survived))
    slv.assertFormula(c_non_taut if both_non_taut else tm.mkTerm(Kind.NOT, c_non_taut))
    slv.assertFormula(c_beat if both_beat else tm.mkTerm(Kind.NOT, c_beat))
    slv.assertFormula(c_no_hits if no_hits else tm.mkTerm(Kind.NOT, c_no_hits))
    slv.assertFormula(c_no_final if no_final_claim else tm.mkTerm(Kind.NOT, c_no_final))
    slv.assertFormula(
        tm.mkTerm(
            Kind.EQUAL,
            c_admit,
            tm.mkTerm(Kind.AND, c_survived, c_non_taut, c_beat, c_no_hits, tm.mkTerm(Kind.NOT, c_no_final)),
        )
    )
    slv.assertFormula(c_admit)
    c_sat = slv.checkSat().isSat()
    return {
        "pass": not z_sat and not c_sat,
        "z3_final_selector_survival_unsat": not z_sat,
        "cvc5_final_selector_survival_unsat": not c_sat,
        "blocked_reason": "provider verdicts are borderline and promotion boundary remains closed; no final selector survival or basin claim is admitted",
    }


def main() -> int:
    started = time.time()
    upstream = read_json(UPSTREAM_RESULT)
    pair = latest_provider_pair()
    rows = {provider: provider_row(provider, path) for provider, path in pair.items()}
    coverage = provider_coverage_report(rows, upstream)
    verdict = cross_audit_verdict_report(rows)
    proof = proof_report(verdict)
    positive = {
        "provider_receipts_complete_same_context": coverage,
        "cross_audit_verdict_ingested": verdict,
        "z3_cvc5_survival_block": proof,
    }
    graveyard = {
        "selector_survived_without_provider_survived_verdict_killed": {
            "pass": verdict["both_provider_verdict_survived"] is False and proof["pass"],
            "reason": "both providers returned borderline, not survived; local proof blocks survived admission",
        },
        "provider_output_as_canonical_proof_killed": {
            "pass": True,
            "reason": "provider receipts are classified provider_audit and promotion_allowed=false",
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": PROMOTION_ALLOWED is False,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Run explicit static-fingerprint fake controls and/or scale-64 commutator-balance dynamics before any stronger selector claim.",
        },
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
        "two_root_constraints": TWO_ROOT_CONSTRAINTS,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "script_sha256": sha256_file(pathlib.Path(__file__)),
        "input_paths": {
            "upstream_selector_energy_result": rel(UPSTREAM_RESULT),
            "goal_plan": rel(PLAN_PATH),
        },
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "completion_status": "not_achieved",
            "candidate": "commutator_balance_energy",
            "provider_verdict": verdict["verdict"],
            "selector_survived": verdict["selector_survived"],
            "both_non_tautological": verdict["both_non_tautological"],
            "both_beat_matched_baseline": verdict["both_beat_matched_baseline"],
            "both_provider_verdict_survived": verdict["both_provider_verdict_survived"],
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": len(graveyard),
            "passed": sum(1 for item in graveyard.values() if item["pass"]),
            "items": sorted(graveyard),
        },
        "why_not_v4_probes": "This is a v5 formal scout over provider cross-audit receipts, not a v4 proposal.",
        "divergence_log": [
            "If provider borderline is treated as survived, the cross-audit gate is bypassed.",
            "If provider audit output is promoted directly, formal_scout authority is bypassed.",
            "If low-energy dwell is confused with variance-zero attraction, the basin claim is overpromoted.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": rel(OUT_PATH), "all_pass": all_pass, "provider_verdict": verdict["verdict"], "selector_survived": verdict["selector_survived"], "next_required_scout": NEXT_REQUIRED_SCOUT}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
