#!/usr/bin/env python3
"""Finite contextuality/no-global-section event gate.

Formal scout only.

This row tests a finite contextual event surface as an alternative or companion
to SIC/POVM probes. It avoids treating one global classical sample space as
primitive: local finite contexts are satisfiable, but the full parity system has
no global section. This is a root-compatible candidate because it is finite,
probe/context native, and noncommuting-context sensitive.
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "finite_contextuality_sheaf_event_gate_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SIM_ID = NAME
VERSION = "1.0.1"
TIER = "1 finite probe/effect quotient"
PURPOSE = (
    "Reissue the Phase 1 finite contextuality/no-global-section row against "
    "the current LEGO receipt contract without opening downstream consumers."
)
SCIENTIFIC_QUESTION = (
    "Do finite local contexts remain satisfiable while the full finite event "
    "surface has no global section, and do classical global-sample-space and "
    "missing-context controls fail?"
)
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "constraint_probe"
SOURCE_ALIGNMENT_CATEGORY = "finite_contextual_event_no_global_section_candidate"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests finite contextual event/context constraints as a "
    "candidate root-adjacent probe surface. It does not admit final contextual "
    "ontology, final manifold foundation, Axis0, Xi, flux, IGT, FEP, physics, "
    "or mathematics claims."
)

BLOCKED_CONSUMERS = [
    "PEPS3D seed implementation",
    "spinor/Hopf/Weyl enforcement",
    "terrain generator placement",
    "operator substage cells",
    "PEPS/PEPS3D closure",
    "flux",
    "Xi/Phi0",
    "Axis0",
    "Holodeck/FEP",
    "physics",
    "IGT/game theory",
    "axes 7-12",
]

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing finite assignment enumeration and parity violation counts"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing no-global-section satisfiability checks"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

CONTEXTS = [
    ("row_0", (0, 1, 2), 1),
    ("row_1", (3, 4, 5), 1),
    ("row_2", (6, 7, 8), 1),
    ("col_0", (0, 3, 6), 1),
    ("col_1", (1, 4, 7), 1),
    ("col_2", (2, 5, 8), -1),
]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def torch_assignment_violation_stats(contexts: list[tuple[str, tuple[int, int, int], int]]) -> dict[str, Any]:
    raw = torch.arange(2**9, dtype=torch.int64)
    bits = ((raw[:, None] >> torch.arange(9, dtype=torch.int64)) & 1).to(torch.int64)
    signs = 1 - 2 * bits
    violations = []
    for _, ids, target in contexts:
        product = torch.prod(signs[:, list(ids)], dim=1)
        violations.append(product != int(target))
    violation_count = torch.stack(violations, dim=1).sum(dim=1)
    min_violations = int(torch.min(violation_count).item())
    best_count = int(torch.sum(violation_count == min_violations).item())
    return {
        "assignment_count": int(signs.shape[0]),
        "min_violations": min_violations,
        "best_assignment_count": best_count,
    }


def z3_context_status(contexts: list[tuple[str, tuple[int, int, int], int]]) -> dict[str, Any]:
    vars_ = [z3.Bool(f"e_{idx}") for idx in range(9)]

    def sign_bool(flag: z3.BoolRef) -> z3.ArithRef:
        return z3.If(flag, z3.IntVal(-1), z3.IntVal(1))

    solver = z3.Solver()
    for _, ids, target in contexts:
        product = sign_bool(vars_[ids[0]]) * sign_bool(vars_[ids[1]]) * sign_bool(vars_[ids[2]])
        solver.add(product == target)

    local_statuses = {}
    for name, ids, target in contexts:
        local = z3.Solver()
        product = sign_bool(vars_[ids[0]]) * sign_bool(vars_[ids[1]]) * sign_bool(vars_[ids[2]])
        local.add(product == target)
        local_statuses[name] = str(local.check())

    relaxed = z3.Solver()
    for name, ids, target in contexts:
        if name == "col_2":
            continue
        product = sign_bool(vars_[ids[0]]) * sign_bool(vars_[ids[1]]) * sign_bool(vars_[ids[2]])
        relaxed.add(product == target)
    return {
        "global_status": str(solver.check()),
        "local_statuses": local_statuses,
        "relaxed_status": str(relaxed.check()),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    z3_status = z3_context_status(CONTEXTS)
    torch_stats = torch_assignment_violation_stats(CONTEXTS)
    positive = {
        "finite_contexts_are_declared": {
            "pass": len(CONTEXTS) == 6 and all(len(ids) == 3 for _, ids, _ in CONTEXTS),
            "context_count": len(CONTEXTS),
            "event_count": 9,
        },
        "local_contexts_are_satisfiable": {
            "pass": all(status == "sat" for status in z3_status["local_statuses"].values()),
            "local_statuses": z3_status["local_statuses"],
        },
        "global_section_is_rejected": {
            "pass": z3_status["global_status"] == "unsat" and torch_stats["min_violations"] >= 1,
            "z3_global_status": z3_status["global_status"],
            "torch_min_violations": torch_stats["min_violations"],
            "torch_assignment_count": torch_stats["assignment_count"],
        },
    }
    graveyard_companions = {
        "GC1_classical_global_sample_space_rejected": {
            "pass": z3_status["global_status"] == "unsat",
            "why_rejected": "no single global +/- assignment satisfies all finite contexts",
        },
        "GC2_relaxed_missing_context_becomes_classical": {
            "pass": z3_status["relaxed_status"] == "sat",
            "why_rejected": "dropping the negative context hides contextuality",
            "relaxed_status": z3_status["relaxed_status"],
        },
    }
    boundary = {
        "B1_formal_scout_only": {"pass": PROMOTION_ALLOWED is False, "promotion_allowed": PROMOTION_ALLOWED},
        "B2_not_axis0_or_physics": {"pass": "does not admit" in CLAIM_CEILING and "Axis0" in CLAIM_CEILING},
    }
    checks = [row["pass"] for row in positive.values()] + [row["pass"] for row in graveyard_companions.values()] + [
        row["pass"] for row in boundary.values()
    ]
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": TIER,
        "purpose": PURPOSE,
        "scientific_question": SCIENTIFIC_QUESTION,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "finite_map": [
            "finite context/event parity system -> local satisfiability and global-section satisfiability readouts"
        ],
        "domain": "six finite three-event contexts over nine finite +/- events with one negative parity context",
        "codomain_or_output": "finite local-context SAT map, global-section UNSAT invariant, torch enumeration violation count, and relaxed-context control",
        "root_constraints_in_force": {
            "F01": {
                "finite_event_count": 9,
                "finite_context_count": len(CONTEXTS),
                "finite_contexts": [name for name, _, _ in CONTEXTS],
                "finite_assignment_count": torch_stats["assignment_count"],
            },
            "N01": {
                "witness": "all local contexts are satisfiable while the full finite context family has no global section",
                "global_status": z3_status["global_status"],
                "min_global_violations": torch_stats["min_violations"],
                "order_or_context_erased_control": "dropping the negative context makes the relaxed system satisfiable",
                "relaxed_status": z3_status["relaxed_status"],
            },
        },
        "carrier_layer": "phase_1_finite_contextual_event_surface",
        "geometry_layer": "none",
        "carrier_realization": "finite torch-native enumeration of +/- assignments plus z3 finite satisfiability constraints",
        "peps3d_embedding": "blocked downstream next step only; not implemented here",
        "spinor_state": "not_applicable_for_this_phase_1_contextual_event_result",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "finite contextual event no-global-section witness",
        "branch_status_before_run": "phase_1_frontier_reissue",
        "allowed_claims": ["Phase 1 finite contextual no-global-section scout only"],
        "promotion_blockers": ["remaining Phase 1 frontier rows still need reissue or blocker classification"],
        "required_tools": ["pytorch", "z3"],
        "actual_tools_used": ["pytorch", "z3"],
        "proof_surfaces_used": ["z3"],
        "graph_surfaces_used": ["not_relevant_for_this_phase1_contextuality_packet"],
        "topology_surfaces_used": ["not_relevant_for_this_phase1_contextuality_packet"],
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_inputs": ["finite contexts and finite parity targets defined in this source"],
        "data_or_artifact_dependencies": [
            "system_v5/ops/formal_scouts/results/finite_effect_algebra_laws_probe_results.json",
            "system_v5/ops/formal_scouts/results/finite_effect_sic_weyl_substrate_admission_probe_results.json",
        ],
        "required_negatives": [
            "classical_global_sample_space_rejected",
            "relaxed_missing_context_becomes_classical",
        ],
        "negatives_run": list(graveyard_companions.keys()),
        "kill_conditions": [
            "global classical sample space satisfies all contexts",
            "relaxed missing-context control remains unsatisfiable",
            "any downstream consumer admitted",
        ],
        "required_artifacts": [str(OUT_PATH.relative_to(ROOT))],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": "phase1_finite_contextuality_no_global_section_reissue_v1",
        "result_summary": {
            "context_count": len(CONTEXTS),
            "event_count": 9,
            "global_status": z3_status["global_status"],
            "min_global_violations": torch_stats["min_violations"],
            "relaxed_status": z3_status["relaxed_status"],
        },
        "pass_rule": "all finite local contexts are satisfiable, the full context family has no global section, and relaxed/classical controls fail",
        "fail_rule": "any unsatisfied local context, admitted global section, relaxed control remains unsat, or downstream consumer admission",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["phase1_frontier_matrix_only"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "controls": {
            "positive": positive,
            "negative": graveyard_companions,
            "boundary": boundary,
        },
        "nearby_variants": {"passed": sum(1 for item in checks if item), "total": len(checks)},
        "all_pass": all(checks),
        "blockers": [],
        "summary": {
            "candidate": "contextuality_sheaf_or_presheaf_events",
            "global_section": z3_status["global_status"],
            "min_global_violations": torch_stats["min_violations"],
            "elapsed_seconds": time.time() - started,
        },
        "why_not_v4_probes": "This is a v5 finite contextual event formal scout, not a v4 probe promotion.",
        "next_required_work": [
            "Reissue the next Phase 1 frontier row or write an explicit Phase 1 blocker.",
            "Keep all listed downstream consumers blocked.",
        ],
        "next_admissible_step": "Continue Phase 1 bounded frontier repair or write a Phase 1 blocker; do not open downstream consumers from this receipt.",
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(OUT_PATH), "all_pass": result["all_pass"], "summary": result["summary"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
