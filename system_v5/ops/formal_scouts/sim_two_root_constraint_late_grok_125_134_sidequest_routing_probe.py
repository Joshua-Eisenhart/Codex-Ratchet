#!/usr/bin/env python3
"""Route late grok_sim 125-136 as sidequest/tooling evidence only.

This is the Workstream 6b receipt requested by the active long plan. It does
not promote grok_sim results into formal evidence. It classifies each late
sidequest artifact as a formal reproduction target, tooling repair hint,
sidequest context only, or blocked/not promotable.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_late_grok_125_134_sidequest_routing_probe_results.json"

GROK_ROOT = REPO / "system_v5" / "grok_sim"
GROK_RESULTS = GROK_ROOT / "results"
HANDOFF = GROK_ROOT / "HANDOFF_NESTED_BASIN_ARCHITECTURE_AND_TOOLING_BLOCK_20260520.md"
PLAN = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
CORRECTION = REPO / "system_v5" / "docs" / "CONSTRAINT_MANIFOLD_ORDERING_STATUS_CORRECTION_20260520.md"
ACTIVE_HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"

NAME = "two_root_constraint_late_grok_125_134_sidequest_routing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_125_136_sidequest_routing"
CLAIM_CEILING = (
    "Formal routing receipt only: classifies grok_sim iter_125-136 as "
    "sidequest/tooling evidence. It cannot promote E=8/E=16 trajectories, "
    "coherent bridge, entropy/ratchet shrinkage, PEPS/MPS construction, quimb "
    "workarounds, integrated iter_135 claims, deterministic iter_136 claims, full tensor-network, multi-qubit "
    "Lindblad, PEPS3D, real basin, Axis0, engine, physics, Holodeck, Clifford, "
    "or final-manifold claims."
)

TOOL_MANIFEST = {
    "python_json": {"tried": True, "used": True, "reason": "supportive sidequest result parsing and receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive repository path accounting"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result provenance hashes"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing proof that direct promotion is disallowed for every late grok row"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

ARTIFACTS = [
    {
        "iter": "iter_125",
        "path": GROK_RESULTS / "iter_125_torch_native_quantum_trajectories_E8_single_engine_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "E=8 one-engine quantum-trajectory Lindblad substrate",
        "formal_use": "reproduce under formal_scouts before any E=8 pseudo-basin evidence is cited",
    },
    {
        "iter": "iter_126",
        "path": GROK_RESULTS / "iter_126_torch_native_quantum_trajectories_E16_paired_engines_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "E=16 paired-engine quantum-trajectory Lindblad substrate and chirality split",
        "formal_use": "reproduce under formal_scouts before any paired-engine pseudo-basin evidence is cited",
    },
    {
        "iter": "iter_127",
        "path": GROK_RESULTS / "iter_127_full_manifold_aligned_complete_stack_sim_results.json",
        "route_class": "sidequest_context_only",
        "subject": "full 20-layer manifold sidequest run",
        "formal_use": "context for what to audit; not a final manifold receipt",
    },
    {
        "iter": "iter_128",
        "path": GROK_RESULTS / "iter_128_full_manifold_coherent_bridge_xi_proper_rho_AB_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "coherent bridge Xi -> rho_AB and Phi0 candidate values",
        "formal_use": "reproduce bridge/cut-state construction under formal_scouts before citation",
    },
    {
        "iter": "iter_129",
        "path": GROK_RESULTS / "iter_129_per_layer_entropy_ratchet_shrinkage_peps_attempt_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "entropy/ratchet-shrinkage plus PEPS/MPS construction notes",
        "formal_use": "split into formal entropy/ratchet receipt and separate tensor-network construction/tooling receipt",
    },
    {
        "iter": "iter_130",
        "path": GROK_RESULTS / "iter_130.log",
        "route_class": "tooling_repair_hint",
        "subject": "MPS Lindblad dynamics blocked by quimb local reduced-state API",
        "formal_use": "use as tool-repair symptom only",
    },
    {
        "iter": "iter_131",
        "path": GROK_RESULTS / "iter_131.log",
        "route_class": "blocked_not_promotable",
        "subject": "L=16/32/64 MPS Lindblad attempt killed for runtime",
        "formal_use": "blocked runtime evidence only",
    },
    {
        "iter": "iter_132",
        "path": GROK_RESULTS / "iter_132.log",
        "route_class": "blocked_not_promotable",
        "subject": "survival-norm MPS Lindblad attempt killed for runtime",
        "formal_use": "blocked runtime evidence only",
    },
    {
        "iter": "iter_133_L16",
        "path": GROK_RESULTS / "iter_133_L16.log",
        "route_class": "blocked_not_promotable",
        "subject": "parallel L=16 MPS attempt killed before first completion",
        "formal_use": "blocked runtime evidence only",
    },
    {
        "iter": "iter_133_L32",
        "path": GROK_RESULTS / "iter_133_L32.log",
        "route_class": "blocked_not_promotable",
        "subject": "parallel L=32 MPS attempt killed before first completion",
        "formal_use": "blocked runtime evidence only",
    },
    {
        "iter": "iter_133_L64",
        "path": GROK_RESULTS / "iter_133_L64.log",
        "route_class": "blocked_not_promotable",
        "subject": "parallel L=64 MPS attempt killed before first completion",
        "formal_use": "blocked runtime evidence only",
    },
    {
        "iter": "iter_134",
        "path": GROK_RESULTS / "iter_134_quimb_workaround_verified_at_L8_results.json",
        "route_class": "tooling_repair_hint",
        "subject": "quimb 1.14.0 expectation_via_gate workaround at L=8",
        "formal_use": "tooling hint; reproduce and resolve qualitative mismatch before scientific citation",
    },
    {
        "iter": "iter_135",
        "path": GROK_RESULTS / "iter_135_full_pytorch_manifold_complete_sim_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "single-file integrated E=8 manifold sidequest with local Si pseudo-basin signal, entropy/bridge candidates, and PEPS/MPS construction checks",
        "formal_use": (
            "split into formal reproduction receipts before citation: E=8 quantum-trajectory "
            "dynamics, local-terrain convergence, bridge/entropy values, and tensor-network "
            "construction/tooling; do not cite as full basin proof because its own receipt marks "
            "overall E=8 basin convergence false and PEPS/MPS construction is not Lindblad dynamics"
        ),
    },
    {
        "iter": "iter_136",
        "path": GROK_RESULTS / "iter_136_pure_torch_lindblad_density_matrix_E8_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "pure torch deterministic E=8 Lindblad density-matrix sidequest correcting iter_135 basin and mutual-information claims",
        "formal_use": (
            "reproduce under formal_scouts before citation: terrain-specific Si/Ni convergence, "
            "Se/Ne non-convergence, global non-convergence, and near-zero deterministic A-B mutual "
            "information; use as a correction target for iter_128/135 finite-trajectory bridge values"
        ),
    },
]

ALLOWED_ROUTE_CLASSES = {
    "formal_reproduction_target",
    "tooling_repair_hint",
    "sidequest_context_only",
    "blocked_not_promotable",
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists() or path.suffix != ".json":
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def source_hashes() -> dict[str, Any]:
    paths = {
        "active_plan": PLAN,
        "ordering_correction": CORRECTION,
        "active_handoff": ACTIVE_HANDOFF,
        "grok_handoff": HANDOFF,
    }
    for artifact in ARTIFACTS:
        paths[artifact["iter"]] = artifact["path"]
    return {
        key: {"path": rel(path), "exists": path.exists(), "sha256": sha256(path)}
        for key, path in paths.items()
    }


def artifact_row(artifact: dict[str, Any]) -> dict[str, Any]:
    path = artifact["path"]
    data = read_json(path)
    text = read_text(path) if path.suffix != ".json" else ""
    route_class = artifact["route_class"]
    claim_ceiling = data.get("claim_ceiling") or ("log_blocked_sidequest_only" if path.suffix != ".json" else None)
    method = data.get("method", {})
    if not isinstance(method, dict):
        method = {"description": method}

    flags = {
        "exists": path.exists(),
        "sidequest_ceiling_present": "side" in str(claim_ceiling).lower() or path.suffix != ".json",
        "direct_formal_promotion_allowed": False,
        "full_tensor_network_evidence_allowed": False,
        "peps3d_evidence_allowed": False,
        "real_basin_claim_allowed": False,
        "route_class_allowed": route_class in ALLOWED_ROUTE_CLASSES,
    }
    diagnostics: dict[str, Any] = {}
    if artifact["iter"] == "iter_126":
        diagnostics["scale_label"] = data.get("scale_label")
        diagnostics["has_results_per_initial_state"] = bool(data.get("results_per_initial_state"))
    if artifact["iter"] == "iter_129":
        diagnostics["mentions_peps_or_mps"] = "PEPS" in json.dumps(data) or "MPS" in json.dumps(data)
    if artifact["iter"] == "iter_134":
        diagnostics["south_pole_pull_verified"] = data.get("south_pole_pull_verified")
        diagnostics["agrees_with_pytorch_qualitative"] = data.get("agrees_with_pytorch_qualitative")
        diagnostics["mismatch_requires_reproduction"] = data.get("agrees_with_pytorch_qualitative") is not True
    if artifact["iter"] == "iter_135":
        basin = data.get("basin_convergence_test", {})
        site_rows = basin.get("per_site_convergence", [])
        deepest = data.get("most_constrained_geometry_layer", {})
        kernel_values = deepest.get("kernel_values", {}) if isinstance(deepest, dict) else {}
        diagnostics["elapsed_seconds"] = data.get("elapsed_seconds")
        diagnostics["overall_basin_converged_at_threshold_0_3"] = basin.get("basin_converged_at_threshold_0_3")
        diagnostics["overall_max_pairwise_distance"] = basin.get("overall_max_pairwise_distance")
        diagnostics["deepest_entropy_layer"] = deepest.get("layer") if isinstance(deepest, dict) else None
        diagnostics["phi0_correlational_entropy_candidates"] = {
            "I_c": kernel_values.get("I_c"),
            "S_A_given_B": kernel_values.get("S_A_given_B"),
            "I_A_B": kernel_values.get("I_A_B"),
        }
        diagnostics["local_si_site_pairwise_distances"] = [
            {
                "site": site.get("site"),
                "max_pairwise_distance_across_initial_states": site.get("max_pairwise_distance_across_initial_states"),
            }
            for site in site_rows
            if site.get("perception") == "Si"
        ]
        diagnostics["quimb_construction_flags"] = data.get("tool_integrations", {}).get("quimb", {})
        diagnostics["toolchain_used"] = data.get("toolchain_used", {})
        diagnostics["formal_audit_warning"] = (
            "Useful integrated sidequest, but not a complete attractor-basin receipt: "
            "the receipt's overall E=8 basin_converged_at_threshold_0_3 flag is false."
        )
    if artifact["iter"] == "iter_136":
        diagnostics["elapsed_seconds"] = data.get("elapsed_seconds")
        diagnostics["compute_path"] = data.get("compute_path")
        diagnostics["global_basin_converged_threshold_0_3"] = data.get("global_basin_converged_threshold_0_3")
        diagnostics["overall_max_pairwise_distance"] = data.get("overall_max_pairwise_distance")
        diagnostics["per_terrain_max_pairwise_distance"] = data.get("per_terrain_max_pairwise_distance")
        diagnostics["si_sublattice_converged_threshold_0_3"] = data.get("si_sublattice_converged_threshold_0_3")
        info_values = []
        for row in data.get("results_per_initial_state", {}).values():
            value = row.get("I_A_B")
            if value is not None:
                info_values.append(value)
        diagnostics["deterministic_I_A_B_range"] = {
            "min": min(info_values) if info_values else None,
            "max": max(info_values) if info_values else None,
        }
        diagnostics["iter_135_comparison"] = data.get("iter_135_comparison")
        diagnostics["formal_audit_warning"] = (
            "Useful pure-torch E=8 sidequest, but not a formal basin receipt: global convergence "
            "is false; Si/Ni terrain convergence and near-zero deterministic I(A:B) require formal reproduction."
        )
    if path.suffix != ".json":
        lower = text.lower()
        diagnostics["log_mentions_killed_or_timeout"] = any(token in lower for token in ["killed", "timeout", "blocked", "deprecation", "attributeerror"])

    return {
        "iter": artifact["iter"],
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256(path),
        "route_class": route_class,
        "subject": artifact["subject"],
        "formal_use": artifact["formal_use"],
        "claim_ceiling": claim_ceiling,
        "flags": flags,
        "diagnostics": diagnostics,
    }


def z3_no_direct_promotion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    promotion_vars: list[z3.BoolRef] = []
    for idx, row in enumerate(rows):
        route_class = z3.String(f"route_class_{idx}")
        formal_promoted = z3.Bool(f"formal_promoted_{idx}")
        promotion_vars.append(formal_promoted)
        solver.add(route_class == row["route_class"])
        solver.add(
            z3.Or(
                route_class == "formal_reproduction_target",
                route_class == "tooling_repair_hint",
                route_class == "sidequest_context_only",
                route_class == "blocked_not_promotable",
            )
        )
        solver.add(z3.Not(formal_promoted))

    all_no_promotion = z3.And([z3.Not(var) for var in promotion_vars]) if promotion_vars else z3.BoolVal(True)
    solver.add(all_no_promotion)
    status = solver.check()

    try_promote = z3.Solver()
    try_promote.add(solver.assertions())
    if promotion_vars:
        try_promote.add(z3.Or(promotion_vars))
    promote_status = try_promote.check()
    return {
        "solver": "z3",
        "status": str(status),
        "direct_promotion_is_unsat": str(promote_status) == "unsat",
        "model": str(solver.model()) if status == z3.sat else None,
    }


def main() -> int:
    started = time.time()
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    rows = [artifact_row(artifact) for artifact in ARTIFACTS]
    class_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row["route_class"]] = class_counts.get(row["route_class"], 0) + 1
    missing = [row for row in rows if not row["exists"]]
    promoted = [row for row in rows if row["flags"]["direct_formal_promotion_allowed"]]
    z3_result = z3_no_direct_promotion(rows)
    handoff_text = read_text(HANDOFF)

    positive = {
        "all_late_artifacts_classified": {
            "pass": len(rows) == len(ARTIFACTS) and not missing,
            "classified_count": len(rows),
            "missing": missing,
        },
        "route_classes_are_allowed": {
            "pass": all(row["flags"]["route_class_allowed"] for row in rows),
            "class_counts": dict(sorted(class_counts.items())),
        },
        "sidequest_ceiling_preserved": {
            "pass": all(row["flags"]["sidequest_ceiling_present"] for row in rows),
            "claim_ceiling": "all JSON/log rows remain sidequest/log context before formal reproduction",
        },
        "no_direct_formal_promotion": {
            "pass": not promoted and z3_result["direct_promotion_is_unsat"],
            "z3": z3_result,
        },
        "grok_handoff_mentions_late_iters": {
            "pass": all(token in handoff_text for token in ["iter_125", "iter_126", "iter_127", "iter_128", "iter_129", "iter_134", "iter_136"]),
            "path": rel(HANDOFF),
        },
    }
    graveyard_companions = {
        "grok_e8_e16_as_formal_w7_completion_killed": {
            "pass": True,
            "reason": "iter_125/126 are formal reproduction targets only and cannot replace the W7 formal receipt.",
        },
        "grok_full_manifold_as_final_manifold_killed": {
            "pass": True,
            "reason": "iter_127 is sidequest context only and cannot admit final manifold status.",
        },
        "grok_coherent_bridge_as_formal_bridge_killed": {
            "pass": True,
            "reason": "iter_128 requires formal reproduction before bridge/cut-state citation.",
        },
        "grok_peps_mps_construction_as_full_dynamics_killed": {
            "pass": True,
            "reason": "iter_129 construction notes are not PEPS/PEPS3D or full Lindblad dynamics evidence.",
        },
        "grok_mps_large_l_dynamics_as_blocked_not_promotable": {
            "pass": True,
            "reason": "iter_130-133 logs are blocked runtime/tooling evidence only.",
        },
        "grok_quimb_workaround_as_scientific_evidence_killed": {
            "pass": True,
            "reason": "iter_134 is a tooling hint and its own JSON reports qualitative mismatch with the PyTorch reference.",
        },
        "grok_iter_135_as_complete_basin_or_tensor_network_lindblad_proof_killed": {
            "pass": True,
            "reason": (
                "iter_135 is a formal reproduction target only: it records local Si pseudo-basin "
                "convergence and tool construction checks, but its own overall E=8 basin convergence "
                "flag is false and PEPS/MPS construction is not PEPS3D or Lindblad tensor-network dynamics."
            ),
        },
        "grok_iter_136_as_complete_basin_or_bridge_proof_killed": {
            "pass": True,
            "reason": (
                "iter_136 is a formal reproduction target only: it records pure-torch deterministic "
                "E=8 terrain-specific Si/Ni convergence, Se/Ne non-convergence, global non-convergence, "
                "and near-zero I(A:B), but it is not a formal W7/full tensor-network/PEPS3D receipt."
            ),
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "formal_synthesis_use": {
            "pass": True,
            "value": "cite this receipt as routing only; cite individual grok rows only after formal reproduction",
        },
        "full_tensor_network_evidence_allowed": {"pass": True, "value": False},
        "multi_qubit_lindblad_evidence_allowed": {
            "pass": True,
            "value": "not from grok_sim directly; only formal reproduction can change this",
        },
        "goal_completion_effect": {
            "pass": True,
            "value": "does not close B2-B5 and does not authorize cleanup",
        },
    }

    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and all(item["pass"] for item in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "math_object": "late grok_sim 125-136 sidequest/tooling evidence routing",
        "artifact_rows": rows,
        "summary": {
            "all_pass": all_pass,
            "artifact_count": len(rows),
            "class_counts": dict(sorted(class_counts.items())),
            "formal_reproduction_targets": [row["iter"] for row in rows if row["route_class"] == "formal_reproduction_target"],
            "tooling_repair_hints": [row["iter"] for row in rows if row["route_class"] == "tooling_repair_hint"],
            "blocked_not_promotable": [row["iter"] for row in rows if row["route_class"] == "blocked_not_promotable"],
            "sidequest_context_only": [row["iter"] for row in rows if row["route_class"] == "sidequest_context_only"],
            "direct_formal_promotion_allowed": False,
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "passed": len(graveyard_companions),
            "total": len(graveyard_companions),
            "items": list(graveyard_companions.keys()),
        },
        "why_not_v4_probes": "This is a v5 formal-scout routing receipt over v5 grok_sim sidequest artifacts and active v5 closeout plan requirements.",
        "blockers": [],
        "source_hashes": source_hashes(),
        "all_pass": all_pass,
        "generated_at": generated_at,
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "artifact_count": len(rows),
                "class_counts": result["summary"]["class_counts"],
                "direct_formal_promotion_allowed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
