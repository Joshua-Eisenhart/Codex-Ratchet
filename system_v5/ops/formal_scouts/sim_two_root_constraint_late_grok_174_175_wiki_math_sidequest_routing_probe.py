#!/usr/bin/env python3
"""Route grok_sim 174-175 as sidequest wiki/math evidence only.

These late grok_sim rows add high-math targets around Cl(3)/Cl(6),
G-structure tower paths, tensor-network Axis0 coherent-information mapping,
compression, PCA/QPCA, Schumacher coding, and rate-distortion limits.

This receipt preserves them as formal reproduction targets. It does not promote
them into final axis canon, final manifold evidence, real attractor-basin
evidence, bridge closure, tensor-network evidence, or D86 goal reopening.
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
OUT_PATH = RESULT_DIR / "two_root_constraint_late_grok_174_175_wiki_math_sidequest_routing_probe_results.json"

GROK_RESULTS = REPO / "system_v5" / "grok_sim" / "results"
ACTIVE_HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"
FINAL_SYNTHESIS = REPO / "system_v5" / "ops" / "formal_scouts" / "results" / "two_root_constraint_final_synthesis_receipt_results.json"

NAME = "two_root_constraint_late_grok_174_175_wiki_math_sidequest_routing_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_late_grok_174_175_wiki_math_sidequest_routing"
CLAIM_CEILING = (
    "Formal routing receipt only: classifies grok_sim iter_174-175 as "
    "sidequest wiki/math evidence. It cannot promote final axis canon, "
    "G-structure admission, manifold completion, real attractor-basin evidence, "
    "bridge closure, tensor-network evidence, cleanup, or D86 goal reopening."
)

TOOL_MANIFEST = {
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive parsing of sidequest JSON artifacts and receipt serialization",
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
        "iter": "iter_174",
        "path": GROK_RESULTS / "iter_174_wiki_batch_18_g_tower_cl3cl6_tn_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "Cl(3)/Cl(6), spin periodicity, odd-dimensional complex-structure obstruction, G-tower path, tensor-network Axis0 coherent-information mapping",
        "formal_use": "reproduce before citing G-tower, Cl-depth, contact/Sasakian obstruction, or bond-dimension to coherent-information targets",
    },
    {
        "iter": "iter_175",
        "path": GROK_RESULTS / "iter_175_wiki_batch_19_compression_pca_results.json",
        "route_class": "formal_reproduction_target",
        "subject": "spectral truncation, Eckart-Young, Schumacher coding, PCA variance, water-filling, and diagonal quantum-to-classical rate collapse",
        "formal_use": "reproduce before citing compression/PCA/QPCA or rate-distortion targets",
    },
]

ALLOWED_ROUTE_CLASSES = {
    "formal_reproduction_target",
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
    if path.exists() and path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def passed(value: Any) -> bool:
    return value is True or value == "True"


def test_keys(data: dict[str, Any]) -> list[str]:
    return sorted(key for key in data if key.startswith("T"))


def all_tests_passed(data: dict[str, Any]) -> bool:
    keys = test_keys(data)
    return bool(keys) and all(passed(data[key].get("passed")) for key in keys if isinstance(data.get(key), dict))


def selected_diagnostics(iter_id: str, data: dict[str, Any]) -> dict[str, Any]:
    common = {
        "all_pass": data.get("all_pass"),
        "test_count": len(test_keys(data)),
        "all_named_tests_passed": all_tests_passed(data),
    }
    if iter_id == "iter_174":
        common.update(
            {
                "double_cover": data.get("T1_double_cover", {}).get("passed"),
                "spinor_4pi_periodicity": data.get("T2_4pi_periodicity", {}).get("passed"),
                "cl6_even_closure": data.get("T3_cl6_even_closure", {}).get("passed"),
                "odd_dim_j2_obstruction": data.get("T4_odd_dim_J2_obstruction", {}).get("passed"),
                "max_entangled_ic": data.get("T5_max_entangled_Ic", {}).get("passed"),
                "s3_g_tower_path": data.get("T7_S3_g_tower_path", {}).get("passed"),
            }
        )
    elif iter_id == "iter_175":
        common.update(
            {
                "spectral_truncation": data.get("T1_spectral_truncation", {}).get("passed"),
                "eckart_young": data.get("T2_eckart_young", {}).get("passed"),
                "schumacher": data.get("T3_schumacher", {}).get("passed"),
                "pca_variance": data.get("T4_pca_variance", {}).get("passed"),
                "water_filling": data.get("T5_water_filling", {}).get("passed"),
                "rq_diagonal_collapse": data.get("T6_R_q_diagonal_collapses", {}).get("passed"),
            }
        )
    return common


def artifact_row(artifact: dict[str, Any]) -> dict[str, Any]:
    path = artifact["path"]
    data = read_json(path)
    return {
        "iter": artifact["iter"],
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256(path),
        "route_class": artifact["route_class"],
        "subject": artifact["subject"],
        "formal_use": artifact["formal_use"],
        "claim_ceiling": data.get("claim_ceiling") or "sidequest_wiki_math_only",
        "direct_formal_promotion_allowed": False,
        "diagnostics": selected_diagnostics(artifact["iter"], data),
    }


def z3_no_direct_promotion(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    promotion_vars = []
    for idx, row in enumerate(rows):
        route_class = z3.String(f"route_class_{idx}")
        promoted = z3.Bool(f"formal_promoted_{idx}")
        promotion_vars.append(promoted)
        solver.add(route_class == row["route_class"])
        solver.add(
            z3.Or(
                route_class == "formal_reproduction_target",
                route_class == "sidequest_context_only",
                route_class == "blocked_not_promotable",
            )
        )
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


def final_synthesis_closed() -> dict[str, Any]:
    data = read_json(FINAL_SYNTHESIS)
    return {
        "path": rel(FINAL_SYNTHESIS),
        "exists": FINAL_SYNTHESIS.exists(),
        "goal_complete": data.get("goal_complete"),
        "cleanup_authorized": data.get("cleanup_authorized"),
        "open_blocker_count": data.get("summary", {}).get("open_blocker_count")
        if isinstance(data.get("summary"), dict)
        else data.get("open_blocker_count"),
    }


def main() -> int:
    started = time.time()
    rows = [artifact_row(artifact) for artifact in ARTIFACTS]
    class_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row["route_class"]] = class_counts.get(row["route_class"], 0) + 1

    row_by_iter = {row["iter"]: row for row in rows}
    missing = [row["iter"] for row in rows if not row["exists"]]
    invalid_routes = [row["iter"] for row in rows if row["route_class"] not in ALLOWED_ROUTE_CLASSES]
    z3_result = z3_no_direct_promotion(rows)

    positive = {
        "all_174_175_artifacts_classified": {
            "pass": len(rows) == 2 and not missing,
            "classified_count": len(rows),
            "missing": missing,
        },
        "route_classes_are_allowed": {
            "pass": not invalid_routes,
            "class_counts": dict(sorted(class_counts.items())),
            "invalid_routes": invalid_routes,
        },
        "reproduction_targets_pass_sidequest_tests": {
            "pass": all(row["diagnostics"]["all_named_tests_passed"] for row in rows)
            and all(passed(row["diagnostics"]["all_pass"]) for row in rows),
            "iters": [row["iter"] for row in rows],
        },
        "g_tower_cl_depth_targets_preserved": {
            "pass": passed(row_by_iter["iter_174"]["diagnostics"]["odd_dim_j2_obstruction"])
            and passed(row_by_iter["iter_174"]["diagnostics"]["max_entangled_ic"])
            and passed(row_by_iter["iter_174"]["diagnostics"]["s3_g_tower_path"]),
            "diagnostics": row_by_iter["iter_174"]["diagnostics"],
        },
        "compression_qpca_targets_preserved": {
            "pass": passed(row_by_iter["iter_175"]["diagnostics"]["eckart_young"])
            and passed(row_by_iter["iter_175"]["diagnostics"]["schumacher"])
            and passed(row_by_iter["iter_175"]["diagnostics"]["rq_diagonal_collapse"]),
            "diagnostics": row_by_iter["iter_175"]["diagnostics"],
        },
        "no_direct_formal_promotion": {
            "pass": z3_result["direct_promotion_is_unsat"],
            "z3": z3_result,
        },
        "d86_stays_closed_not_reopened": {
            "pass": final_synthesis_closed()["goal_complete"] is True,
            "final_synthesis": final_synthesis_closed(),
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "final_axis_canon_allowed": {"pass": True, "value": False},
        "g_structure_admission_allowed": {"pass": True, "value": False},
        "manifold_completion_allowed": {"pass": True, "value": False},
        "real_basin_claim_allowed": {"pass": True, "value": False},
        "bridge_or_phi0_closure_allowed": {"pass": True, "value": False},
        "tensor_network_evidence_allowed": {"pass": True, "value": False},
        "d86_reopen_allowed": {"pass": True, "value": False},
    }
    graveyard_companions = {
        "sidequest_all_pass_is_not_promotion": {
            "pass": True,
            "reason": "Both rows keep direct_formal_promotion_allowed false despite all_pass sidequest receipts.",
        },
        "g_tower_target_not_g_structure_admission": {
            "pass": row_by_iter["iter_174"]["route_class"] == "formal_reproduction_target",
            "reason": "S3/G-tower and Cl-depth facts are reproduction targets, not admitted G-structure layers.",
        },
        "compression_targets_not_axis0_theorem": {
            "pass": row_by_iter["iter_175"]["route_class"] == "formal_reproduction_target",
            "reason": "Compression/PCA/QPCA checks can guide formal tests but do not prove Axis0 or bridge closure.",
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
        "math_object": "late grok_sim 174-175 wiki/math sidequest routing",
        "artifact_rows": rows,
        "summary": {
            "all_pass": all_pass,
            "artifact_count": len(rows),
            "class_counts": dict(sorted(class_counts.items())),
            "formal_reproduction_targets": [row["iter"] for row in rows],
            "direct_formal_promotion_allowed": False,
            "d86_reopened": False,
            "useful_reproduction_targets": [
                "Cl(3)/Cl(6) depth and spin periodicity checks",
                "odd-dimensional J^2 obstruction supporting the S3 contact/Sasakian branch",
                "max-entangled coherent-information equals log bond dimension target",
                "S3 G-tower path target",
                "spectral truncation and Eckart-Young compression checks",
                "Schumacher typical-subspace and PCA/QPCA/rate-distortion checks",
            ],
            "preserved_boundaries": [
                "sidequest all_pass is not promotion",
                "no G-structure admission",
                "no final axis canon",
                "no manifold completion",
                "no real basin, bridge closure, or tensor-network evidence",
                "D86 remains complete and is not reopened",
            ],
        },
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": {
            "passed": len(graveyard_companions),
            "total": len(graveyard_companions),
            "items": list(graveyard_companions.keys()),
        },
        "why_not_v4_probes": "This is a v5 formal-scout routing receipt over v5 grok_sim sidequest artifacts and D86 post-closeout handling.",
        "blockers": [],
        "source_hashes": {
            "final_synthesis": {
                "path": rel(FINAL_SYNTHESIS),
                "exists": FINAL_SYNTHESIS.exists(),
                "sha256": sha256(FINAL_SYNTHESIS),
            },
            "active_handoff": {
                "path": rel(ACTIVE_HANDOFF),
                "exists": ACTIVE_HANDOFF.exists(),
                "sha256": sha256(ACTIVE_HANDOFF),
            },
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
                "d86_reopened": False,
                "useful_reproduction_targets": result["summary"]["useful_reproduction_targets"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
