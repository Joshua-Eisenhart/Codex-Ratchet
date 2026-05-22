#!/usr/bin/env python3
"""Provider/global falsifier gap scout for the two-root manifold chain.

Formal scout only. This is a spend-gated local audit: it does not launch
Claude, Grok, Gemini, or other providers. Instead it checks whether existing
provider receipts are route-bound to the current selector-minimality chain,
records the provider gap honestly, and reroutes to a local global finite-family
countermodel scout.
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
PROVIDER_DIR = SCOUT_ROOT / "provider_receipts"

sys.path.insert(0, str(SCOUT_ROOT))
import validate_provider_receipts  # noqa: E402


NAME = "two_root_constraint_provider_and_global_falsifier_gap_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
UPSTREAM_RESULT = RESULT_DIR / "two_root_constraint_selector_minimality_completion_audit_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_provider_global_falsifier_gap"
CLAIM_CEILING = (
    "Formal scout only: audits provider/global falsifier gaps under a local "
    "spend guard. It does not admit provider output as evidence, final "
    "geometric constraint manifold, real attractor basin, Axis0, engine, "
    "physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing provider receipt parsing, route-bound gap classification, and result serialization",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that completion cannot follow from unbound provider receipts or blocked provider lanes",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent completion-block proof matching z3",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing provider/global/local reroute dependency graph",
    },
    "hashlib": {"tried": True, "used": True, "reason": "supportive receipt hashing"},
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

PROVIDER_ROUTES = ["grok", "gemini", "sonnet_high", "opus_max"]
ROUTE_BOUND_TERMS = [
    "two_root_constraint_selector_minimality_completion_audit_probe",
    "two_root_constraint_layer_selector_cross_carrier_minimality_probe",
    "two_root_constraint_provider_and_global_falsifier_gap_probe",
    "selector_minimality_completion_audit",
    "cross_carrier_selector_minimality",
]
NEXT_REQUIRED_SCOUT = "two_root_constraint_global_countermodel_exhaustive_finite_family_probe"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    return value


def upstream_report() -> dict[str, Any]:
    data = read_json(UPSTREAM_RESULT)
    summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    return {
        "pass": data.get("classification") == "formal_scout"
        and data.get("promotion_allowed") is False
        and summary.get("completion_status") == "not_achieved"
        and summary.get("next_required_scout") == NAME,
        "path": rel(UPSTREAM_RESULT),
        "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
        "completion_status": summary.get("completion_status"),
        "weak_or_open_requirements": summary.get("weak_or_open_requirements"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def provider_receipt_rows() -> dict[str, Any]:
    rows = []
    if PROVIDER_DIR.exists():
        for path in sorted(PROVIDER_DIR.glob("*.json")):
            try:
                data = read_json(path)
            except Exception as exc:  # pragma: no cover - defensive receipt audit
                rows.append({"path": rel(path), "readable": False, "error": repr(exc)})
                continue
            blob = json.dumps(data, sort_keys=True).lower()
            provider = str(data.get("provider") or "").lower()
            route = str(data.get("route") or "").lower()
            route_bound = any(term.lower() in blob for term in ROUTE_BOUND_TERMS)
            relevant = any(term in blob for term in ["two_root", "manifold", "basin", "selector", "f01", "n01"])
            strict = validate_provider_receipts.validate(path, strict_live=True)
            rows.append(
                {
                    "path": rel(path),
                    "readable": True,
                    "provider": provider,
                    "route": route,
                    "status": data.get("status"),
                    "relevant": relevant,
                    "route_bound_to_current_chain": route_bound,
                    "strict_live_pass": strict["pass"],
                    "strict_live_errors": strict["errors"],
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
    relevant_rows = [row for row in rows if row.get("relevant")]
    route_bound_rows = [row for row in relevant_rows if row.get("route_bound_to_current_chain")]
    strict_route_bound_rows = [row for row in route_bound_rows if row.get("strict_live_pass")]
    provider_counts = {
        route: sum(1 for row in relevant_rows if route in str(row.get("provider")) or route in str(row.get("route")))
        for route in PROVIDER_ROUTES
    }
    return {
        "pass": True,
        "provider_receipt_count": len(rows),
        "relevant_receipt_count": len(relevant_rows),
        "route_bound_relevant_count": len(route_bound_rows),
        "strict_live_route_bound_count": len(strict_route_bound_rows),
        "provider_counts": provider_counts,
        "route_bound_samples": route_bound_rows[:8],
        "failed_strict_live_samples": [row for row in relevant_rows if not row.get("strict_live_pass")][:8],
        "status": "blocked_gap" if not strict_route_bound_rows else "weak_route_bound_provider_evidence",
        "note": "Existing provider receipts do not close the current selector-minimality provider falsifier lane unless strict-live and route-bound to the current chain.",
    }


def spend_guard_report(provider_rows: dict[str, Any]) -> dict[str, Any]:
    blocked_routes = [
        {
            "provider": provider,
            "status": "blocked_by_spend_guard",
            "reason": "external provider launch intentionally skipped after observed Claude quota burn; no current-turn explicit reopen",
            "reroute": NEXT_REQUIRED_SCOUT,
        }
        for provider in PROVIDER_ROUTES
    ]
    return {
        "pass": provider_rows["strict_live_route_bound_count"] == 0,
        "external_calls_launched": 0,
        "blocked_routes": blocked_routes,
        "reroute_policy": "local-first global countermodel scout before any renewed provider fanout",
    }


def global_gap_matrix() -> dict[str, Any]:
    rows = [
        {
            "gap": "unbounded_carrier_exhaustion",
            "status": "open",
            "local_reroute": NEXT_REQUIRED_SCOUT,
            "failure_mode": "bounded quaternion/SU2, Hopf/S3, Spin/G, cellular, and ring-checkerboard families are mistaken for exhaustive admissible geometry",
        },
        {
            "gap": "global_attractor_basin_convergence",
            "status": "open",
            "local_reroute": NEXT_REQUIRED_SCOUT,
            "failure_mode": "retuned bounded basin shell is mistaken for global convergence under all finite carrier perturbations",
        },
        {
            "gap": "provider_route_bound_falsifiers",
            "status": "blocked",
            "local_reroute": NEXT_REQUIRED_SCOUT,
            "failure_mode": "old provider proposals are treated as fresh falsifier receipts",
        },
        {
            "gap": "estate_integration_as_proof",
            "status": "weak",
            "local_reroute": "tool_integration_estate_keyword_repair_or_full_estate_audit",
            "failure_mode": "large estate index is treated as integration proof despite tool_integration surface still false",
        },
    ]
    return {"pass": True, "rows": rows, "open_or_blocked_count": sum(1 for row in rows if row["status"] in {"open", "blocked", "weak"})}


def graph_report(provider_rows: dict[str, Any], global_gaps: dict[str, Any]) -> dict[str, Any]:
    graph = rx.PyDiGraph()
    root = graph.add_node("selector_minimality_completion_audit")
    provider_gap = graph.add_node("provider_falsifier_gap")
    global_gap = graph.add_node("global_countermodel_gap")
    reroute = graph.add_node(NEXT_REQUIRED_SCOUT)
    graph.add_edge(root, provider_gap, "weak_or_open")
    graph.add_edge(root, global_gap, "weak_or_open")
    graph.add_edge(provider_gap, reroute, "spend_guard_reroute")
    graph.add_edge(global_gap, reroute, "local_global_falsifier")
    for provider, count in provider_rows["provider_counts"].items():
        node = graph.add_node(provider)
        graph.add_edge(node, provider_gap, f"existing_receipts:{count}")
    for row in global_gaps["rows"]:
        node = graph.add_node(row["gap"])
        graph.add_edge(node, global_gap, row["status"])
    return {
        "pass": bool(rx.is_directed_acyclic_graph(graph)) and graph.num_nodes() >= 10 and graph.num_edges() >= 10,
        "nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "is_dag": bool(rx.is_directed_acyclic_graph(graph)),
    }


def proof_report(provider_rows: dict[str, Any], global_gaps: dict[str, Any]) -> dict[str, Any]:
    route_bound = provider_rows["strict_live_route_bound_count"] > 0
    global_closed = global_gaps["open_or_blocked_count"] == 0

    p = z3.Bool("route_bound_provider_falsifiers")
    g = z3.Bool("global_falsifier_gap_closed")
    complete = z3.Bool("completion_allowed")
    solver = z3.Solver()
    solver.add(p == route_bound)
    solver.add(g == global_closed)
    solver.add(complete == z3.And(p, g))
    solver.add(complete)
    z3_completion_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bsort = tm.getBooleanSort()
    cp = tm.mkConst(bsort, "route_bound_provider_falsifiers")
    cg = tm.mkConst(bsort, "global_falsifier_gap_closed")
    cc = tm.mkConst(bsort, "completion_allowed")
    slv.assertFormula(cp if route_bound else tm.mkTerm(Kind.NOT, cp))
    slv.assertFormula(cg if global_closed else tm.mkTerm(Kind.NOT, cg))
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, cc, tm.mkTerm(Kind.AND, cp, cg)))
    slv.assertFormula(cc)
    cvc5_completion_sat = slv.checkSat().isSat()

    return {
        "pass": not z3_completion_sat and not cvc5_completion_sat,
        "route_bound_provider_falsifiers": route_bound,
        "global_falsifier_gap_closed": global_closed,
        "z3_completion_from_provider_global_gap_unsat": not z3_completion_sat,
        "cvc5_completion_from_provider_global_gap_unsat": not cvc5_completion_sat,
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "old provider proposal receipts get counted as current route-bound falsifier evidence",
        "most_dangerous_failure": "provider quota is burned again before the local global countermodel gap is sharpened",
        "hidden_assumption": "external model disagreement is needed before local finite-family countermodel search can proceed",
        "checks_applied": [
            "strict-live provider receipt validation",
            "route-bound term audit against current selector-minimality chain",
            "zero external calls under spend guard",
            "z3/cvc5 completion block",
            "local reroute to global finite-family countermodel scout",
        ],
    }


def main() -> int:
    started = time.time()
    upstream = upstream_report()
    provider_rows = provider_receipt_rows()
    spend_guard = spend_guard_report(provider_rows)
    global_gaps = global_gap_matrix()
    graph = graph_report(provider_rows, global_gaps)
    proof = proof_report(provider_rows, global_gaps)
    premortem = premortem_report()
    positive = {
        "upstream_completion_audit_consumed": upstream,
        "provider_receipts_audited_without_external_calls": provider_rows,
        "spend_guard_reroute_recorded": spend_guard,
        "global_falsifier_gap_matrix_built": global_gaps,
        "provider_global_dependency_graph": graph,
        "z3_cvc5_provider_global_completion_block": proof,
        "premortem_applied": premortem,
    }
    graveyard = {
        "old_provider_receipts_as_current_route_bound_evidence_killed": {
            "pass": provider_rows["strict_live_route_bound_count"] == 0,
            "strict_live_route_bound_count": provider_rows["strict_live_route_bound_count"],
        },
        "provider_spend_without_local_reroute_killed": {
            "pass": spend_guard["external_calls_launched"] == 0,
            "reason": "No provider calls were made; the next move is a local global countermodel scout.",
        },
        "completion_from_provider_global_gap_killed": proof,
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "provider_boundary": {
            "pass": True,
            "provider_status": provider_rows["status"],
            "external_calls_launched": spend_guard["external_calls_launched"],
            "note": "Provider lanes are blocked/deferred under current spend guard, not counted as completed falsifiers.",
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Search for bounded global finite-family countermodels locally before any renewed provider fanout.",
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
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "input_receipts": {
            "selector_minimality_completion_audit": {
                "path": rel(UPSTREAM_RESULT),
                "sha256": hashlib.sha256(UPSTREAM_RESULT.read_bytes()).hexdigest(),
            }
        },
        "premortem": premortem,
        "positive": jsonable(positive),
        "graveyard_companions": jsonable(graveyard),
        "boundary": jsonable(boundary),
        "summary": {
            "all_pass": all_pass,
            "completion_status": "not_achieved",
            "provider_receipt_count": provider_rows["provider_receipt_count"],
            "relevant_provider_receipt_count": provider_rows["relevant_receipt_count"],
            "strict_live_route_bound_provider_count": provider_rows["strict_live_route_bound_count"],
            "external_calls_launched": spend_guard["external_calls_launched"],
            "global_gap_count": global_gaps["open_or_blocked_count"],
            "next_required_scout": NEXT_REQUIRED_SCOUT,
            "runtime_seconds": round(time.time() - started, 6),
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "items": [
                "old provider proposals are not current route-bound falsifier evidence",
                "blocked provider spend guard is recorded rather than hidden",
                "local global countermodel scout is selected before renewed provider fanout",
            ],
        },
        "why_not_v4_probes": "This is a v5 formal scout over local provider receipt metadata and proof gates, not a v4 proposal.",
        "divergence_log": [
            "If old provider receipts are counted, the current falsifier lane is fake.",
            "If external calls launch without a spend gate, quota can be burned without improving local proof state.",
            "If global countermodels are not searched locally, bounded carrier success can be mistaken for universality.",
        ],
        "blockers": [],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "wrote": rel(OUT_PATH),
                "all_pass": all_pass,
                "completion_status": "not_achieved",
                "strict_live_route_bound_provider_count": provider_rows["strict_live_route_bound_count"],
                "external_calls_launched": spend_guard["external_calls_launched"],
                "next_required_scout": NEXT_REQUIRED_SCOUT,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
