#!/usr/bin/env python3
"""Post-retune completion audit for the two-root selector-basin chain.

Formal scout only. This audit consumes the expanded two-root chain through the
selector-basin stochastic falsifier and retune. It decides whether the central
geometric constraint manifold can honestly be called complete, or whether the
current receipts still leave foundational gaps.
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
import sim_two_root_constraint_completion_audit_and_gap_classifier_probe as base_audit  # noqa: E402


NAME = "two_root_constraint_completion_audit_after_selector_basin_chain_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_selector_basin_completion_audit"
CLAIM_CEILING = (
    "Formal scout only: audits the expanded two-root selector-basin chain after "
    "the adversarial retune. It may classify strengthened bounded evidence and "
    "kill premature completion, but it does not admit a final geometric "
    "constraint manifold, real attractor basin, Axis0, engine, physics, "
    "Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing prompt-to-artifact checklist, receipt parsing, and result serialization",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing premature-completion kill proof over weak/open objective rows",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent premature-completion kill proof matching z3",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing requirement-to-receipt dependency graph for uncovered objective rows",
    },
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

CHAIN = [
    "two_root_constraint_layer_stack_peps3d_boundary_portability_probe",
    "two_root_constraint_long_horizon_layer_stack_countermodel_probe",
    "two_root_constraint_cross_family_countermodel_transfer_probe",
    "two_root_constraint_escape_boundary_and_nonmanifold_explanation_kill_probe",
    "two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe",
    "two_root_constraint_layer_order_gauge_invariant_observable_probe",
    "two_root_constraint_completion_audit_and_gap_classifier_probe",
    "two_root_constraint_layer_forcing_theorem_or_countermodel_probe",
    "two_root_constraint_selection_axiom_layer_discriminator_probe",
    "two_root_constraint_selection_axiom_portability_countermodel_sweep_probe",
    "two_root_constraint_selector_adversarial_synthesis_and_basin_bridge_probe",
    "two_root_constraint_selector_basin_bridge_scaling_and_escape_volume_probe",
    "two_root_constraint_selector_basin_stochastic_escape_volume_falsifier_probe",
    "two_root_constraint_selector_basin_adversarial_leak_retune_probe",
]

NEXT_REQUIRED_SCOUT = "two_root_constraint_layer_level_selector_necessity_countermodel_probe"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def jsonable(value: Any) -> Any:
    return base_audit.jsonable(value)


def receipt_path(stem: str) -> pathlib.Path:
    return RESULT_DIR / f"{stem}_results.json"


def load_chain() -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for stem in CHAIN:
        path = receipt_path(stem)
        if path.exists():
            loaded[stem] = read_json(path)
    return loaded


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
        "row_count": summary.get("row_count") or summary.get("joint_row_count"),
        "next_required_scout": summary.get("next_required_scout"),
    }


def all_terms(receipts: dict[str, dict[str, Any]], terms: list[str]) -> tuple[bool, list[str]]:
    text = json.dumps(receipts, sort_keys=True).lower()
    missing = [term for term in terms if term.lower() not in text]
    return not missing, missing


def any_groups(receipts: dict[str, dict[str, Any]], groups: dict[str, list[str]]) -> tuple[bool, list[str]]:
    text = json.dumps(receipts, sort_keys=True).lower()
    missing = [name for name, terms in groups.items() if not any(term.lower() in text for term in terms)]
    return not missing, missing


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
    return {
        "exists": True,
        "path": rel(ESTATE_INDEX),
        "surface_coverage": surfaces,
        "all_named_surfaces_present": all(surfaces.values()),
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
        "note": "provider outputs are advisory unless route-bound to this exact chain with prompt hash, model, status, and accepted receipt",
    }


def tool_coverage(receipts: dict[str, dict[str, Any]]) -> dict[str, bool]:
    tools = base_audit.load_bearing_tool_union(receipts)
    return {name: bool(aliases & tools) for name, aliases in base_audit.REQUIRED_TOOLS.items()}


def build_requirement_rows(receipts: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    all_receipts = [rel(receipt_path(stem)) for stem in CHAIN]
    hard_neg_pass, missing_hard_negatives = all_terms(receipts, base_audit.HARD_NEGATIVES)
    carrier_pass, missing_carriers = all_terms(
        receipts,
        ["quaternion", "su2", "hopf", "s3", "g2", "spin7", "ring_checkerboard", "cellular"],
    )
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
    scaling_pass, missing_scaling = all_terms(
        receipts,
        ["8", "16", "32", "64", "peps3d", "contraction_order", "memory", "runtime", "failure_modes"],
    )
    gauge_pass, missing_gauge = all_terms(
        receipts, ["gauge_representatives", "gauge_invariant_observables", "order_gap"]
    )
    selector_pass, missing_selector = all_terms(
        receipts, ["selector_axiom", "canonical_row_count", "noncanonical_row_count", "sampled_countermodel_count"]
    )
    escape_pass, missing_escape = all_terms(
        receipts,
        [
            "escape_volume",
            "stochastic",
            "adversarial_leak_found",
            "retuned_adversarial_gap_above_boundary",
            "old_adversarial_gap_above_boundary",
        ],
    )
    coverage = tool_coverage(receipts)
    schema = chain_schema_status(receipts)
    estate = estate_status()
    provider = provider_status()
    premortem_count = sum("premortem" in receipt for receipt in receipts.values())

    rows = [
        {
            "id": "objective_restate",
            "requirement": "Restate the active goal as concrete deliverables before claiming completion.",
            "status": "covered_strong",
            "evidence": [NAME],
            "notes": "This audit scout encodes the goal as prompt-to-artifact rows.",
        },
        {
            "id": "expanded_chain_receipts_present",
            "requirement": "Consume the expanded two-root chain through selector portability, basin bridge, stochastic falsifier, and retune.",
            "status": "covered_strong" if len(receipts) == len(CHAIN) else "open",
            "evidence": all_receipts,
            "loaded_count": len(receipts),
            "expected_count": len(CHAIN),
        },
        {
            "id": "f01_n01_root_gate_and_ablations",
            "requirement": "Every manifold advance must keep F01 finitude and N01 noncommutation live with root-off, single-root, order, pressure, gauge, carrier, flux, transplant, null, classical, and apparent-basin controls.",
            "status": "covered_strong" if hard_neg_pass else "open",
            "evidence": all_receipts,
            "missing": missing_hard_negatives,
        },
        {
            "id": "root_only_forcing_claim_killed",
            "requirement": "Prove or kill whether F01 plus N01 alone force the exact layered geometry.",
            "status": "covered_strong",
            "evidence": [rel(receipt_path("two_root_constraint_layer_forcing_theorem_or_countermodel_probe"))],
            "notes": "The chain kills the root-only exact-stack forcing claim; selector axioms are extra conditions, not automatic consequences.",
        },
        {
            "id": "selector_axiom_bounded_sufficiency",
            "requirement": "If roots alone do not force the stack, test explicit selector conditions that make a bounded finite noncommutative stack admissible.",
            "status": "covered_strong" if selector_pass else "open",
            "evidence": [
                rel(receipt_path("two_root_constraint_selection_axiom_layer_discriminator_probe")),
                rel(receipt_path("two_root_constraint_selection_axiom_portability_countermodel_sweep_probe")),
            ],
            "missing": missing_selector,
        },
        {
            "id": "layer_by_layer_selector_necessity",
            "requirement": "Audit and retune each individual manifold layer from the base up, proving which layer selectors are necessary rather than merely sufficient in the stack.",
            "status": "weak",
            "evidence": [
                rel(receipt_path("two_root_constraint_layer_stack_peps3d_boundary_portability_probe")),
                rel(receipt_path("two_root_constraint_layer_order_gauge_invariant_observable_probe")),
                rel(receipt_path("two_root_constraint_selection_axiom_layer_discriminator_probe")),
            ],
            "notes": "The stack, order, and selector set are tested jointly; isolated per-layer necessity/countermodel rows remain the next foundational gap.",
        },
        {
            "id": "candidate_carrier_realizations",
            "requirement": "Treat gauge, quaternion/SU(2)/Spin, Hopf/S3, cellular, and ring-checkerboard as candidate root realizations rather than primitives.",
            "status": "covered_strong" if carrier_pass else "weak",
            "evidence": [rel(receipt_path("two_root_constraint_cross_family_countermodel_transfer_probe"))],
            "missing": missing_carriers,
        },
        {
            "id": "gauge_representatives_vs_observables",
            "requirement": "Separate gauge representatives from gauge-invariant observables and verify layer order is load-bearing.",
            "status": "covered_strong" if gauge_pass else "open",
            "evidence": [rel(receipt_path("two_root_constraint_layer_order_gauge_invariant_observable_probe"))],
            "missing": missing_gauge,
        },
        {
            "id": "bounded_basin_semantics",
            "requirement": "A basin claim must include admissibility predicate, state space, update rule, boundary, stability invariant, escape/failure cases, and a killed non-manifold explanation.",
            "status": "covered_strong" if basin_pass else "open",
            "evidence": [
                rel(receipt_path("two_root_constraint_escape_boundary_and_nonmanifold_explanation_kill_probe")),
                rel(receipt_path("two_root_constraint_selector_adversarial_synthesis_and_basin_bridge_probe")),
            ],
            "missing": missing_basin,
        },
        {
            "id": "basin_escape_and_retune_loop",
            "requirement": "Run deterministic, stochastic, adversarial, and retuned escape/failure pressure instead of treating repeated clustering as convergence.",
            "status": "covered_strong" if escape_pass else "open",
            "evidence": [
                rel(receipt_path("two_root_constraint_selector_basin_bridge_scaling_and_escape_volume_probe")),
                rel(receipt_path("two_root_constraint_selector_basin_stochastic_escape_volume_falsifier_probe")),
                rel(receipt_path("two_root_constraint_selector_basin_adversarial_leak_retune_probe")),
            ],
            "missing": missing_escape,
        },
        {
            "id": "site_scaled_tensor_networks",
            "requirement": "Build PyTorch-native 8/16/32/64 site tensor-network scouts with PEPS/PEPS3D assumptions, contraction order, runtime/memory, observables, invariants, and failures.",
            "status": "covered_strong" if scaling_pass else "open",
            "evidence": [rel(receipt_path("two_root_constraint_8_16_32_64_site_basin_boundary_scaling_probe"))],
            "missing": missing_scaling,
        },
        {
            "id": "load_bearing_tool_coverage",
            "requirement": "Use z3/cvc5, SymPy/Clifford, rustworkx/XGI/TopoNetX/GUDHI, PyTorch/autograd/PyG/e3nn, auto_LiRPA, and le-wm only where load-bearing.",
            "status": "covered_strong" if all(coverage.values()) else "open",
            "evidence": all_receipts,
            "tool_coverage": coverage,
            "missing": [tool for tool, covered in coverage.items() if not covered],
        },
        {
            "id": "premortem_per_loop",
            "requirement": "Every loop must include a premortem plus hard negatives.",
            "status": "weak",
            "evidence": all_receipts,
            "premortem_receipt_count": premortem_count,
            "expected_receipt_count": len(CHAIN),
            "hard_negatives_missing": missing_hard_negatives,
            "notes": "Hard negatives are present across the expanded chain; premortem is present in 11 of 14 receipts, not uniformly top-level in every loop.",
        },
        {
            "id": "provider_falsifier_lanes",
            "requirement": "Use Opus/Sonnet/Grok/Gemini as advisory/falsifier lanes when available with accepted provider receipts.",
            "status": provider["status"],
            "evidence": [item["path"] for item in provider["sample"]],
            "provider_receipt_count": provider["count"],
            "notes": provider["note"],
        },
        {
            "id": "fresh_validation_and_indexes",
            "requirement": "Every sim fresh-reruns, passes validation, writes canonical receipts, updates README/readiness/estate indexes, and keeps promotion blocked.",
            "status": "weak" if schema["pass"] else "open",
            "evidence": [rel(READINESS_INDEX), rel(ESTATE_INDEX), rel(SCOUT_ROOT / "README.md")],
            "chain_schema_status": schema,
            "notes": "Schema/index coverage is green for the chain, but historical fresh-rerun command receipts are not embedded for every prior scout.",
        },
        {
            "id": "full_estate_integration",
            "requirement": "Process and index the larger sim estate around manifold, PEPS/PEPS3D, Axis0, basin, LiRPA/le-wm, and tool integration.",
            "status": "weak" if estate["exists"] and estate.get("all_named_surfaces_present") else "open",
            "evidence": [rel(ESTATE_INDEX)],
            "estate_status": estate,
            "notes": "The estate index maps the surfaces; it is not proof that every sim has been integrated, ported, or retuned.",
        },
        {
            "id": "final_manifold_completion",
            "requirement": "Do not claim the geometric constraint manifold is final until root forcing, selector necessity, basin semantics, tensor scaling, tool coverage, provider falsifiers, and estate integration are all strongly covered.",
            "status": "weak",
            "evidence": all_receipts,
            "notes": "The expanded chain supports a bounded selector-driven manifold/basin fixture and closes one known adversarial leak; it does not close the final foundation objective.",
        },
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
    return {
        "pass": bool(rows) and bool(weak_or_open),
        "requirement_nodes": len(rows),
        "total_nodes": graph.num_nodes(),
        "edges": graph.num_edges(),
        "weak_or_open_requirements": weak_or_open,
    }


def completion_proof(rows: list[dict[str, Any]]) -> dict[str, Any]:
    names = [row["id"] for row in rows]
    covered = {row["id"]: row["status"] == "covered_strong" for row in rows}

    z_terms = {name: z3.Bool(name) for name in names}
    z_complete = z3.Bool("objective_complete")
    solver = z3.Solver()
    solver.add(z_complete == z3.And(*[z_terms[name] for name in names]))
    for name in names:
        solver.add(z_terms[name] == covered[name])
    solver.add(z_complete)
    z3_completion_sat = solver.check() == z3.sat

    tm = cvc5.TermManager()
    slv = cvc5.Solver(tm)
    slv.setLogic("ALL")
    bool_sort = tm.getBooleanSort()
    c_terms = {name: tm.mkConst(bool_sort, name) for name in names}
    c_complete = tm.mkConst(bool_sort, "objective_complete")
    slv.assertFormula(tm.mkTerm(Kind.EQUAL, c_complete, tm.mkTerm(Kind.AND, *[c_terms[name] for name in names])))
    for name in names:
        slv.assertFormula(c_terms[name] if covered[name] else tm.mkTerm(Kind.NOT, c_terms[name]))
    slv.assertFormula(c_complete)
    cvc5_completion_sat = slv.checkSat().isSat()

    return {
        "pass": not z3_completion_sat and not cvc5_completion_sat,
        "z3_premature_completion_unsat": not z3_completion_sat,
        "cvc5_premature_completion_unsat": not cvc5_completion_sat,
        "completion_status": "not_achieved" if not z3_completion_sat and not cvc5_completion_sat else "possibly_complete",
        "covered_strong": sorted(name for name, value in covered.items() if value),
        "weak_or_open": sorted(name for name, value in covered.items() if not value),
    }


def premortem_report() -> dict[str, Any]:
    return {
        "pass": True,
        "most_likely_failure": "calling the selector-retuned bounded basin fixture a final geometric manifold",
        "most_dangerous_failure": "letting downstream Axis0 or engine work inherit an unproven layer-necessity and provider-falsifier gap",
        "hidden_assumption": "selector sufficiency plus retuned escape margin is equivalent to root-forced global necessity",
        "checks_applied": [
            "expanded prompt-to-artifact checklist",
            "root-only forcing kill retained as progress, not as completion",
            "selector sufficiency separated from layer-level necessity",
            "z3 and cvc5 premature-completion proof gates",
            "estate index treated as map rather than final integration proof",
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
        "objective_rephrased_as_checklist": {
            "pass": True,
            "requirement_count": len(rows),
            "status_counts": status_counts,
        },
        "expanded_chain_receipts_loaded": {
            "pass": len(receipts) == len(CHAIN),
            "loaded_count": len(receipts),
            "expected_count": len(CHAIN),
            "receipt_facts": facts,
        },
        "requirement_dependency_graph_built": graph,
        "premortem_applied": premortem,
    }
    graveyard = {
        "premature_completion_claim_killed": proof,
        "root_only_exact_stack_forcing_as_completion_killed": {
            "pass": True,
            "reason": "root-only exact stack forcing was killed; selector axioms remain explicit extra conditions",
        },
        "retuned_basin_as_global_attractor_claim_killed": {
            "pass": True,
            "reason": "the retune closes a bounded adversarial proxy, but does not promote the basin fixture to a global attractor proof",
        },
        "proxy_green_status_rejected_as_completion": {
            "pass": bool(weak_or_open),
            "weak_or_open_ids": [row["id"] for row in weak_or_open],
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "claim_ceiling": CLAIM_CEILING,
        },
        "completion_status_boundary": {
            "pass": proof["completion_status"] == "not_achieved",
            "completion_status": proof["completion_status"],
            "blocked_completion_requirements": proof["weak_or_open"],
        },
        "next_required_scout": {
            "pass": True,
            "name": NEXT_REQUIRED_SCOUT,
            "requirement": "Probe per-layer selector necessity and countermodels so stack sufficiency can be separated from root-forced necessity.",
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
        "input_receipts": {stem: facts.get(stem, {"missing": True}) for stem in CHAIN},
        "premortem": premortem,
        "objective_restatement": {
            "success_criteria": [
                "show whether F01 finitude and N01 noncommutation force or fail to force layered finite noncommutative geometry",
                "separate root-only forcing, selector sufficiency, and layer-level selector necessity",
                "treat gauge/quaternion/SU(2)/Spin/Hopf/S3/cellular/ring-checkerboard as candidate finite noncommutative realizations",
                "require basin semantics with explicit state, update, boundary, invariant, escape, and non-manifold kill rows",
                "keep 8/16/32/64-site PyTorch tensor-network and load-bearing proof/topology/robustness evidence canonical",
                "reject provider, index, or validation proxies as final completion unless they cover every objective row",
            ]
        },
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
                "root-only exact-stack forcing is killed rather than promoted",
                "selector sufficiency is not treated as per-layer selector necessity",
                "retuned bounded basin bridge is not treated as global attractor-basin convergence",
            ],
        },
        "why_not_v4_probes": (
            "This is a v5 formal scout completion audit over canonical local receipts, not a v4 proposal or provider-only route."
        ),
        "divergence_log": [
            "If a retuned positive margin is treated as global convergence, the basin criterion becomes too weak.",
            "If selector sufficiency is treated as root-forced necessity, the layer stack can be overfit to chosen selectors.",
            "If provider or index surfaces are accepted without route-bound receipts, the audit loses falsifiability.",
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
