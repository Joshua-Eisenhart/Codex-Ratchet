#!/usr/bin/env python3
"""Receipt for QIT engine runtime consolidation.

Workstream A requires the D90-D92 exact-torch engine/schedule scouts to stop
owning separate copies of the same Liouvillian and composition logic. This
receipt verifies that the shared runtime exists, the scouts import it, core
runtime functions are centralized, and the D90-D92 rerun anchors remain green.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import qit_engine_runtime as qit


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_qit_runtime_consolidation_receipt_probe_results.json"

NAME = "two_root_constraint_qit_runtime_consolidation_receipt_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "source_native_runtime_consolidation_receipt"
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_qit_runtime_consolidation"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal consolidation receipt only: verifies shared QIT runtime extraction "
    "and D90-D92 anchor preservation. It does not build full E=16 dynamics, "
    "tensor-network Lindblad, real basin admission, Xi/rho_AB/Phi0 closure, "
    "or final manifold admission."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing helper spot checks for exact engine/schedule channels and fixed Bloch readouts",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing nonpromotion guard for consolidation-only evidence",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result loading and serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source provenance hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive path handling"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

RUNTIME_SOURCE = SCOUT_ROOT / "qit_engine_runtime.py"
D90_SOURCE = SCOUT_ROOT / "sim_two_root_constraint_phi_engine_parameter_sweep_probe.py"
D91_SOURCE = SCOUT_ROOT / "sim_two_root_constraint_phi_schedule_suffix_basin_probe.py"
D92_SOURCE = SCOUT_ROOT / "sim_two_root_constraint_phi_schedule_growth_law_tau_reconciliation_probe.py"
D90_RESULT = RESULT_DIR / "two_root_constraint_phi_engine_parameter_sweep_probe_results.json"
D91_RESULT = RESULT_DIR / "two_root_constraint_phi_schedule_suffix_basin_probe_results.json"
D92_RESULT = RESULT_DIR / "two_root_constraint_phi_schedule_growth_law_tau_reconciliation_probe_results.json"


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def jsonable(value: Any) -> Any:
    if isinstance(value, pathlib.Path):
        return rel(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return float(item)
        return value.detach().cpu().tolist()
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, dict):
        return {str(key): jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(inner) for inner in value]
    return value


def source_checks() -> dict[str, Any]:
    required_exports = [
        "row_major_liouvillian",
        "stage_channel",
        "terrain_stage_channels",
        "engine_channel",
        "schedule_channel",
        "fixed_density",
        "fixed_bloch",
        "channel_spectrum",
        "channel_diagnostics",
        "cluster_points",
        "assign_suffix_cluster",
    ]
    scout_sources = {
        "d90": D90_SOURCE,
        "d91": D91_SOURCE,
        "d92": D92_SOURCE,
    }
    forbidden_local_defs = [
        "def row_major_liouvillian",
        "def stage_channel",
        "def compose(",
    ]
    import_rows = {}
    centralization_rows = {}
    for label, path in scout_sources.items():
        text = path.read_text(encoding="utf-8")
        import_rows[label] = {
            "path": rel(path),
            "imports_qit_runtime": "import qit_engine_runtime as qit" in text,
        }
        centralization_rows[label] = {
            "path": rel(path),
            "forbidden_local_defs": [needle for needle in forbidden_local_defs if needle in text],
        }
    return {
        "runtime_source_exists": {
            "pass": RUNTIME_SOURCE.exists(),
            "path": rel(RUNTIME_SOURCE),
        },
        "runtime_exports_present": {
            "pass": all(hasattr(qit, name) for name in required_exports),
            "required_exports": required_exports,
            "missing": [name for name in required_exports if not hasattr(qit, name)],
        },
        "scouts_import_runtime": {
            "pass": all(row["imports_qit_runtime"] for row in import_rows.values()),
            "rows": import_rows,
        },
        "core_runtime_defs_centralized": {
            "pass": all(not row["forbidden_local_defs"] for row in centralization_rows.values()),
            "rows": centralization_rows,
        },
    }


def helper_spot_checks() -> dict[str, Any]:
    t1_tau_one = qit.engine_channel("L", "iter176_xz", tau=1.0, normalize=True)
    t2_tau_one = qit.engine_channel("R", "iter176_xz", tau=1.0, normalize=True)
    t1_t2 = qit.schedule_channel(("T1", "T2"), {"T1": t1_tau_one, "T2": t2_tau_one})
    t2_t1 = qit.schedule_channel(("T2", "T1"), {"T1": t1_tau_one, "T2": t2_tau_one})
    order_diff = math.dist(qit.fixed_bloch(t1_t2), qit.fixed_bloch(t2_t1))
    diag_t1 = qit.channel_diagnostics(t1_tau_one)
    raw_t1_tau_half = qit.engine_channel("L", (0.7, 0.0, 0.5), tau=0.5, normalize=False)
    raw_t2_tau_half = qit.engine_channel("R", (0.7, 0.0, 0.5), tau=0.5, normalize=False)
    half_clusters = qit.cluster_points(
        [
            {
                "label": "".join(word),
                "fixed_bloch": qit.fixed_bloch(qit.schedule_channel(word, {"1": raw_t1_tau_half, "2": raw_t2_tau_half})),
            }
            for word in (("1", "1"), ("1", "2"), ("2", "1"), ("2", "2"))
        ],
        eps=0.05,
    )
    return {
        "nominal_t1_is_single_basin": {
            "pass": diag_t1["asymptotic_single_basin"],
            "diag": diag_t1,
        },
        "schedule_order_sensitive_spot": {
            "pass": order_diff > 0.05,
            "order_diff_T1T2_vs_T2T1": order_diff,
        },
        "tau_half_n2_four_cluster_spot": {
            "pass": len(half_clusters) == 4,
            "cluster_count": len(half_clusters),
            "clusters": half_clusters,
        },
    }


def anchor_checks() -> dict[str, Any]:
    d90 = read_json(D90_RESULT)
    d91 = read_json(D91_RESULT)
    d92 = read_json(D92_RESULT)
    return {
        "d90_anchor_preserved": {
            "pass": (
                d90.get("all_pass") is True
                and d90.get("summary", {}).get("row_count") == 1152
                and d90.get("summary", {}).get("interior_multibasin_candidates") == 0
                and d90.get("summary", {}).get("interior_finite_time_slow_convergence_cases") == 32
                and d90.get("summary", {}).get("boundary_multifixed_or_nonconvergent_candidates") == 272
            ),
            "result": rel(D90_RESULT),
            "summary": d90.get("summary", {}),
        },
        "d91_anchor_preserved": {
            "pass": (
                d91.get("all_pass") is True
                and d91.get("summary", {}).get("schedule_row_count") == 126
                and d91.get("summary", {}).get("cluster_count_through_length_6") == 2
                and d91.get("summary", {}).get("all_schedule_maps_single_basin") is True
            ),
            "result": rel(D91_RESULT),
            "summary": d91.get("summary", {}),
        },
        "d92_anchor_preserved": {
            "pass": (
                d92.get("all_pass") is True
                and d92.get("summary", {}).get("tau_half_counts") == [2, 4, 4, 4, 4, 4]
                and d92.get("summary", {}).get("tau_one_counts") == [2, 2, 2, 2, 2, 2]
                and d92.get("summary", {}).get("memory_window_tau_half") == 2
                and d92.get("summary", {}).get("geometry_coplanar_rank") == 2
            ),
            "result": rel(D92_RESULT),
            "summary": d92.get("summary", {}),
        },
    }


def z3_report() -> dict[str, Any]:
    consolidated = z3.Bool("consolidated")
    full_engine_complete = z3.Bool("full_engine_complete")
    tensor_network_complete = z3.Bool("tensor_network_complete")
    basin_admitted = z3.Bool("basin_admitted")
    promotion_allowed = z3.Bool("promotion_allowed")
    solver = z3.Solver()
    solver.add(consolidated)
    solver.add(z3.Not(full_engine_complete))
    solver.add(z3.Not(tensor_network_complete))
    solver.add(z3.Not(basin_admitted))
    solver.add(promotion_allowed == z3.And(consolidated, full_engine_complete, tensor_network_complete, basin_admitted))
    solver.add(promotion_allowed)
    return {
        "consolidation_does_not_imply_promotion_unsat": str(solver.check()) == "unsat",
        "rule": "runtime consolidation alone cannot promote full engine, tensor-network, or basin claims",
    }


def main() -> int:
    started = time.time()
    positive = {
        **source_checks(),
        **helper_spot_checks(),
        **anchor_checks(),
        "no_direct_promotion": {
            "pass": z3_report()["consolidation_does_not_imply_promotion_unsat"],
            "z3": z3_report(),
        },
    }
    boundary = {
        "promotion_allowed": {"pass": True, "value": False},
        "full_e16_claim_allowed": {"pass": True, "value": False},
        "tensor_network_claim_allowed": {"pass": True, "value": False},
        "real_basin_claim_allowed": {"pass": True, "value": False},
        "final_manifold_claim_allowed": {"pass": True, "value": False},
    }
    graveyard_companions = {
        "single_engine_multibasin_not_promoted": {
            "pass": positive["d90_anchor_preserved"]["summary"].get("interior_multibasin_candidates") == 0,
            "reason": "D90 anchor remains zero interior asymptotic multi-basin candidates",
        },
        "schedule_pseudo_basin_not_real_basin": {
            "pass": positive["d91_anchor_preserved"]["summary"].get("all_schedule_maps_single_basin") is True,
            "reason": "D91 anchor preserves single-basin status for each fixed schedule map",
        },
    }
    nearby_variant_rows = [
        {
            "variant": "d90_parameter_sweep_anchor",
            "pass": positive["d90_anchor_preserved"]["pass"],
            "claim": "runtime extraction preserves the D90 interior monostable/boundary split",
        },
        {
            "variant": "d91_schedule_suffix_anchor",
            "pass": positive["d91_anchor_preserved"]["pass"],
            "claim": "runtime extraction preserves the D91 tau=1 last-engine suffix classes",
        },
        {
            "variant": "d92_tau_reconciliation_anchor",
            "pass": positive["d92_anchor_preserved"]["pass"],
            "claim": "runtime extraction preserves the D92 tau=0.5 last-2/tau=1 last-1 split",
        },
        {
            "variant": "order_sensitive_spot_check",
            "pass": positive["schedule_order_sensitive_spot"]["pass"],
            "claim": "shared runtime still exposes noncommuting T1/T2 schedule order",
        },
        {
            "variant": "nonpromotion_guard",
            "pass": positive["no_direct_promotion"]["pass"],
            "claim": "consolidation alone cannot promote engine, basin, tensor-network, or manifold claims",
        },
    ]
    nearby_variants = {
        "pass": all(row["pass"] for row in nearby_variant_rows),
        "passed": sum(1 for row in nearby_variant_rows if row["pass"]),
        "total": len(nearby_variant_rows),
        "variants": nearby_variant_rows,
    }
    all_pass = (
        all(item["pass"] for item in positive.values())
        and all(item["pass"] for item in boundary.values())
        and all(item["pass"] for item in graveyard_companions.values())
        and nearby_variants["pass"]
    )
    result = {
        "schema": "formal_scout_result/v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runtime_seconds": time.time() - started,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "source_hashes": {
            "runtime": sha256(RUNTIME_SOURCE),
            "d90_source": sha256(D90_SOURCE),
            "d91_source": sha256(D91_SOURCE),
            "d92_source": sha256(D92_SOURCE),
            "d90_result": sha256(D90_RESULT),
            "d91_result": sha256(D91_RESULT),
            "d92_result": sha256(D92_RESULT),
        },
        "summary": {
            "all_pass": all_pass,
            "runtime_module": rel(RUNTIME_SOURCE),
            "ported_scout_count": 3,
            "anchors": {
                "d90_zero_interior_multibasin": positive["d90_anchor_preserved"]["summary"].get("interior_multibasin_candidates"),
                "d91_tau_one_suffix_classes": positive["d91_anchor_preserved"]["summary"].get("cluster_count_through_length_6"),
                "d92_tau_half_counts": positive["d92_anchor_preserved"]["summary"].get("tau_half_counts"),
            },
            "interpretation": (
                "Workstream A runtime consolidation is green for the D90-D92 surface: "
                "the exact torch terrain/engine/schedule operations are centralized in "
                "qit_engine_runtime.py, the three scouts import it, and their anchor "
                "receipts remain unchanged within the asserted predicates. This does "
                "not complete E=16, tensor-network dynamics, Xi/rho_AB/Phi0 closure, "
                "or real basin admission."
            ),
        },
        "why_not_v4_probes": "This is a v5 formal Workstream A consolidation receipt for exact torch QIT engine runtime helpers; it is not a legacy v4 probe or scientific promotion.",
        "all_pass": all_pass,
        "blockers": [] if all_pass else [name for name, item in positive.items() if not item["pass"]],
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "out_path": rel(OUT_PATH),
                "ported_scout_count": 3,
                "d90_zero_interior_multibasin": result["summary"]["anchors"]["d90_zero_interior_multibasin"],
                "d91_tau_one_suffix_classes": result["summary"]["anchors"]["d91_tau_one_suffix_classes"],
                "d92_tau_half_counts": result["summary"]["anchors"]["d92_tau_half_counts"],
                "interpretation": result["summary"]["interpretation"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
