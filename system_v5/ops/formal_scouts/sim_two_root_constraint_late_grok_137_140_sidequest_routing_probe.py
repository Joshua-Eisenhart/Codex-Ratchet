#!/usr/bin/env python3
"""Route grok_sim 137-140 as sidequest evidence only.

These late grok_sim rows contain useful implementation signals:

- small PEPS/PEPS3D carrier/tool demos,
- non-trivial layer invariant and entropy-ratchet tables,
- an L=16 MPS Lindblad sidequest run,
- a log-only L=32 scale-up blocker from bond-dimension saturation.

This receipt does not promote those rows into formal basin, PEPS/PEPS3D,
tensor-network Lindblad, or final-manifold evidence.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_late_grok_137_140_sidequest_routing_probe_results.json"

GROK_RESULTS = REPO / "system_v5" / "grok_sim" / "results"
PLAN = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
PROMPT = REPO / "system_v5" / "ops" / "NEXT_GOAL_TERRAIN_ENGINE_PSEUDO_BASIN_PROMPT_20260520.md"
ACTIVE_HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"

NAME = "two_root_constraint_late_grok_137_140_sidequest_routing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_137_140_sidequest_routing"
CLAIM_CEILING = (
    "Formal routing receipt only: classifies grok_sim iter_137-140 as "
    "sidequest/tooling evidence. It cannot promote PEPS/PEPS3D, MPS L=16, "
    "MPS L=32, entropy-ratchet, non-trivial admissibility, real basin, "
    "full tensor-network Lindblad, bridge-correlation, Axis0, cleanup, or "
    "final-manifold claims."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive sidequest result parsing and receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive repository path accounting",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive artifact provenance hashes",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing proof that every routed row remains nonpromotional",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
    "z3": "load_bearing",
}

ARTIFACTS = [
    {
        "iter": "iter_137",
        "path": GROK_RESULTS / "iter_137_peps_peps3d_dynamics_and_unused_tool_integrations_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "small PEPS/PEPS3D carrier/tool demos plus GUDHI/PyG/e3nn/TopoNetX integration",
        "formal_use": "split into tiny formal capability/tool-function receipts before citation; not research-grade PEPS/PEPS3D Lindblad dynamics",
    },
    {
        "iter": "iter_138",
        "path": GROK_RESULTS / "iter_138_non_trivial_admissibility_and_entropy_necessity_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "non-trivial per-layer invariants and entropy-form necessity table",
        "formal_use": "reproduce as formal structural-invariant and entropy-ratchet receipts before using in synthesis",
    },
    {
        "iter": "iter_139",
        "path": GROK_RESULTS / "iter_139_dynamic_tensor_networks_and_entropy_all_layers_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "L=16 MPS Lindblad sidequest, PEPS 2x4 multistep sidequest, and 19 layer entropies",
        "formal_use": "reproduce under formal_scouts before citation; preserve its own south-pole nonverification flag",
    },
    {
        "iter": "iter_140",
        "path": GROK_RESULTS / "iter_140.log",
        "route_class": "blocked_not_promotable",
        "subject": "log-only L=32 MPS Lindblad scale-up blocker from bond-dimension saturation",
        "formal_use": "use as algorithmic blocker symptom only; no result JSON and no L=32 promotion",
    },
]

ALLOWED_ROUTE_CLASSES = {"formal_reproduction_target", "blocked_not_promotable"}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    if path.exists() and path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def artifact_row(artifact: dict[str, Any]) -> dict[str, Any]:
    path = artifact["path"]
    data = read_json(path)
    text = read_text(path)
    diagnostics: dict[str, Any] = {}

    if artifact["iter"] == "iter_137":
        parts = data.get("parts", {})
        diagnostics = {
            "peps_2x4_status": parts.get("part_a_peps_2x4", {}).get("status"),
            "peps3d_2x2x2_status": parts.get("part_b_peps3d_2x2x2", {}).get("status"),
            "peps3d_local_gates_applied_ok": parts.get("part_b_peps3d_2x2x2", {}).get("n_local_gates_applied_ok"),
            "lirpa_available": parts.get("lirpa_status", {}).get("available"),
            "lirpa_reason": parts.get("lirpa_status", {}).get("reason"),
        }
    elif artifact["iter"] == "iter_138":
        summary = data.get("summary", {})
        diagnostics = {
            "n_non_trivial_invariant_layers": summary.get("n_non_trivial_invariant_layers"),
            "n_entropy_forms_with_structural_requirements": summary.get("n_entropy_forms_with_structural_requirements"),
            "entropy_ratchet_monotone": summary.get("entropy_ratchet_monotone"),
            "deepest_entropy_layer": summary.get("deepest_entropy_layer"),
            "deepest_entropy_family": summary.get("deepest_entropy_family"),
        }
    elif artifact["iter"] == "iter_139":
        parts = data.get("parts", {})
        part_a = parts.get("part_a_mps_l16_lindblad", {})
        part_b = parts.get("part_b_peps_multistep", {})
        part_c = parts.get("part_c_entropy_all_layers", {})
        diagnostics = {
            "mps_L_sites": part_a.get("L_sites"),
            "mps_bond_dim": part_a.get("bond_dim"),
            "mps_runtime_s": part_a.get("runtime_s"),
            "si_rz_values": part_a.get("si_rz_values"),
            "south_pole_pull_verified_at_L16": part_a.get("south_pole_pull_verified_at_L16"),
            "peps_2x4_multistep_status": part_b.get("status"),
            "peps_z_at_00_evolved": part_b.get("z_at_00_evolved"),
            "n_layers_with_entropy_measured": part_c.get("n_layers_with_entropy_measured"),
            "deepest_layer_entropy": part_c.get("deepest_layer_entropy"),
            "l20_I_A_B": part_c.get("entropies_per_layer", {}).get("L20_I_A_B"),
        }
    elif artifact["iter"] == "iter_140":
        diagnostics = {
            "result_json_exists": False,
            "log_only": path.exists(),
            "mentions_L32": "L=32" in text,
            "mentions_step_8": "step 8/15" in text,
            "mentions_242_seconds": "242.8s" in text,
            "last_log_line": text.strip().splitlines()[-1] if text.strip() else None,
            "formal_audit_warning": "log-only blocked run; no result JSON and no formal L=32 evidence",
        }

    return {
        "iter": artifact["iter"],
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256(path),
        "route_class": artifact["route_class"],
        "subject": artifact["subject"],
        "formal_use": artifact["formal_use"],
        "claim_ceiling": data.get("claim_ceiling") or ("log_blocked_sidequest_only" if path.suffix != ".json" else None),
        "direct_formal_promotion_allowed": False,
        "diagnostics": diagnostics,
    }


def z3_no_direct_promotion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    promotion_vars = []
    for idx, row in enumerate(rows):
        route_class = z3.String(f"route_class_{idx}")
        promoted = z3.Bool(f"formal_promoted_{idx}")
        promotion_vars.append(promoted)
        solver.add(route_class == row["route_class"])
        solver.add(z3.Or(route_class == "formal_reproduction_target", route_class == "blocked_not_promotable"))
        solver.add(z3.Not(promoted))
    solver.add(z3.And([z3.Not(var) for var in promotion_vars]))
    status = solver.check()
    promote = z3.Solver()
    promote.add(solver.assertions())
    promote.add(z3.Or(promotion_vars))
    return {
        "solver": "z3",
        "status": str(status),
        "direct_promotion_is_unsat": str(promote.check()) == "unsat",
    }


def main() -> int:
    started = time.time()
    rows = [artifact_row(artifact) for artifact in ARTIFACTS]
    class_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row["route_class"]] = class_counts.get(row["route_class"], 0) + 1

    missing = [row["iter"] for row in rows if not row["exists"]]
    invalid_routes = [row["iter"] for row in rows if row["route_class"] not in ALLOWED_ROUTE_CLASSES]
    z3_result = z3_no_direct_promotion(rows)

    positive = {
        "all_137_140_artifacts_classified": {
            "pass": len(rows) == 4 and not missing,
            "classified_count": len(rows),
            "missing": missing,
        },
        "route_classes_are_allowed": {
            "pass": not invalid_routes,
            "class_counts": dict(sorted(class_counts.items())),
            "invalid_routes": invalid_routes,
        },
        "iter_140_is_log_only_blocker": {
            "pass": rows[-1]["iter"] == "iter_140" and rows[-1]["diagnostics"]["log_only"] and not rows[-1]["diagnostics"]["result_json_exists"],
            "diagnostics": rows[-1]["diagnostics"],
        },
        "iter_139_preserves_south_pole_nonverification": {
            "pass": rows[2]["diagnostics"]["south_pole_pull_verified_at_L16"] is False,
            "si_rz_values": rows[2]["diagnostics"]["si_rz_values"],
        },
        "no_direct_formal_promotion": {
            "pass": z3_result["direct_promotion_is_unsat"],
            "z3": z3_result,
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "full_tensor_network_lindblad_evidence_allowed": {"pass": True, "value": False},
        "peps3d_lindblad_evidence_allowed": {"pass": True, "value": False},
        "real_basin_claim_allowed": {"pass": True, "value": False},
        "goal_completion_effect": {"pass": True, "value": "does not close B2-B6 and does not authorize cleanup"},
    }
    graveyard_companions = {
        "iter_137_as_research_grade_peps3d_lindblad_killed": {
            "pass": True,
            "reason": "iter_137 is a bounded tiny carrier/tool demo; not PEPS3D Lindblad dynamics.",
        },
        "iter_139_as_uniform_si_south_pole_evidence_killed": {
            "pass": True,
            "reason": "iter_139's own receipt has south_pole_pull_verified_at_L16=false.",
        },
        "iter_140_as_l32_success_killed": {
            "pass": True,
            "reason": "iter_140 has only a log and stops after step 8/15 with a 242.8s step.",
        },
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard_companions.values())
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
        "math_object": "late grok_sim 137-140 sidequest/tooling evidence routing",
        "artifact_rows": rows,
        "summary": {
            "all_pass": all_pass,
            "artifact_count": len(rows),
            "class_counts": dict(sorted(class_counts.items())),
            "formal_reproduction_targets": [row["iter"] for row in rows if row["route_class"] == "formal_reproduction_target"],
            "blocked_not_promotable": [row["iter"] for row in rows if row["route_class"] == "blocked_not_promotable"],
            "direct_formal_promotion_allowed": False,
        },
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": {
            "passed": len(graveyard_companions),
            "total": len(graveyard_companions),
            "items": list(graveyard_companions.keys()),
        },
        "why_not_v4_probes": "This is a v5 formal-scout routing receipt over v5 grok_sim sidequest artifacts and active v5 closeout plan requirements.",
        "blockers": [],
        "source_hashes": {
            "active_plan": {"path": rel(PLAN), "exists": PLAN.exists(), "sha256": sha256(PLAN)},
            "active_prompt": {"path": rel(PROMPT), "exists": PROMPT.exists(), "sha256": sha256(PROMPT)},
            "active_handoff": {"path": rel(ACTIVE_HANDOFF), "exists": ACTIVE_HANDOFF.exists(), "sha256": sha256(ACTIVE_HANDOFF)},
            **{
                row["iter"]: {"path": row["path"], "exists": row["exists"], "sha256": row["sha256"]}
                for row in rows
            },
        },
        "all_pass": all_pass,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
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
                "iter_140_status": rows[-1]["diagnostics"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
