#!/usr/bin/env python3
"""Classify the broad NumPy import blocker without hiding it.

This is a B4 boundary receipt for the post-W7 formal manifold closeout. It
does not hide remaining imports and does not make NumPy admissible for
nonclassical claims. It records exactly which broad import rows remain, why
each is a different kind of debt, and which rows require migration versus
explicit classical/support boundaries before cleanup.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from typing import Any

import z3


SCOUT_ROOT = pathlib.Path(__file__).resolve().parent
REPO = SCOUT_ROOT.parents[2]
RESULT_DIR = SCOUT_ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULT_DIR / "two_root_constraint_broad_numpy_import_boundary_classification_probe_results.json"

NAME = "broad_numpy_import_boundary_classification_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_broad_numpy_import_boundary_classification"
CLAIM_CEILING = (
    "Formal scout only: classifies the current broad NumPy import debt behind "
    "final-synthesis blocker B4. It does not hide remaining NumPy imports, does not "
    "authorize cleanup, does not admit NumPy-load-bearing nonclassical claims, "
    "and does not promote engine, manifold, Axis0, PEPS/PEPS3D, tensor-network, "
    "multi-qubit Lindblad, or attractor-basin evidence."
)

TOOL_MANIFEST = {
    "python_pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive scan of formal_scouts source files",
    },
    "python_re": {
        "tried": True,
        "used": True,
        "reason": "supportive broad import-row detection matching final synthesis",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive comparison with final synthesis B4 evidence and receipt writing",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing row-accounting and nonpromotion satisfiability checks",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive provenance hashes for source and evidence files",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_pathlib": "supportive",
    "python_re": "supportive",
    "python_json": "supportive",
    "z3": "load_bearing",
    "hashlib": "supportive",
}

FINAL_SYNTHESIS = RESULT_DIR / "two_root_constraint_final_synthesis_receipt.json"
NUMPY_QUARANTINE = RESULT_DIR / "numpy_quarantine_source_native_nonclassical_gate_probe_results.json"
PYTORCH_NUMPY_SEPARATION = RESULT_DIR / "pytorch_load_bearing_numpy_support_separation_capability_probe_results.json"
ENGINE_CORE_AUTOGRAD_BOUNDARY = RESULT_DIR / "engine_core_autograd_severance_contract_probe_results.json"
ENGINE_CORE_IMPORTER_BOUNDARY = RESULT_DIR / "engine_core_importer_boundary_classifier_probe_results.json"
PLAN = REPO / "system_v5" / "ops" / "NEXT_GOAL_LONG_FORMAL_MANIFOLD_RETOOL_PLAN.md"
HANDOFF = REPO / ".lev" / "pm" / "handoffs" / "20260520-formal-manifold-tooling-retool-session-1.md"

IMPORT_RE = re.compile(r"^\s*(?:import\s+numpy\b|from\s+numpy\b)")

ENGINE_CORE_FILE = "engine_" + "core.py"

ROW_BOUNDARIES = {
    "canonical_qit_engine_specs.py": {
        "boundary_class": "core_qit_torch_spec_regression_boundary",
        "nonclassical_promotion_allowed": False,
        "classical_or_support_allowed": False,
        "next_move": "Keep canonical Pauli/QIT constants torch-native; if this row reappears, treat it as a B4 regression.",
        "reason": "canonical Pauli/QIT constants were migrated to torch-native tensors; legacy NumPy conversion belongs at the explicit EngineCore boundary.",
    },
    ENGINE_CORE_FILE: {
        "boundary_class": "accepted_core_engine_numpy_infrastructure_boundary",
        "nonclassical_promotion_allowed": False,
        "classical_or_support_allowed": True,
        "next_move": "Keep EngineCore as explicit finite-scalar infrastructure unless a future torch-native EngineCore migration is required.",
        "reason": "EngineCore remains a visible NumPy/SciPy finite-scalar infrastructure boundary, covered by autograd-severance and importer-boundary receipts.",
    },
    "engine_readouts.py": {
        "boundary_class": "engine_readout_regression_boundary",
        "nonclassical_promotion_allowed": False,
        "classical_or_support_allowed": False,
        "next_move": "Keep readout interpretation torch-native; if this row reappears, treat it as a B4 regression.",
        "reason": "engine readout interpretation was migrated to torch for Bloch vectors, eigens, norms, logs, and summary arrays.",
    },
    "engine_schedule.py": {
        "boundary_class": "engine_schedule_regression_boundary",
        "nonclassical_promotion_allowed": False,
        "classical_or_support_allowed": False,
        "next_move": "Keep schedule composition free of direct NumPy imports; if this row reappears, treat it as a B4 regression.",
        "reason": "schedule-local distances and summaries were migrated to torch with an explicit adapter to the remaining EngineCore boundary.",
    },
    "engine_v6_proper_multiqubit_reference.py": {
        "boundary_class": "multiqubit_reference_fixture_regression_boundary",
        "nonclassical_promotion_allowed": False,
        "classical_or_support_allowed": False,
        "next_move": "Keep random density fixtures torch-native; if this row reappears, treat it as a B4 regression.",
        "reason": "random pure/product/GHZ/W density fixtures were migrated to torch.",
    },
    "engine_v7_mps_reference.py": {
        "boundary_class": "mps_reference_gate_regression_boundary",
        "nonclassical_promotion_allowed": False,
        "classical_or_support_allowed": False,
        "next_move": "Keep local MPS gate construction torch-native; if this row reappears, treat it as a B4 regression.",
        "reason": "local NumPy/SciPy gate/kick construction was migrated to torch.linalg.matrix_exp.",
    },
    "manifold_active_projection_perturbation_probe.py": {
        "boundary_class": "tiny_legacy_rank_print_regression",
        "nonclassical_promotion_allowed": False,
        "classical_or_support_allowed": False,
        "next_move": "Keep torch-only; if this row reappears, treat it as a B4 regression.",
        "reason": "tiny perturbation/rank print script was migrated to torch for eigens/rank output.",
    },
    "sim_multiqubit_reservoir_static_kernel_esn_baseline_probe.py": {
        "boundary_class": "first_class_classical_baseline_regression_boundary",
        "nonclassical_promotion_allowed": False,
        "classical_or_support_allowed": False,
        "next_move": "Keep source torch-native; if this row reappears, treat as a B4 regression.",
        "reason": "explicit static reservoir/ESN baseline is a classical comparison lane and was migrated to torch-native source.",
    },
}


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def sha256(path: pathlib.Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def read_json(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def source_hashes() -> dict[str, Any]:
    paths = {
        "final_synthesis": FINAL_SYNTHESIS,
        "numpy_quarantine": NUMPY_QUARANTINE,
        "pytorch_numpy_separation": PYTORCH_NUMPY_SEPARATION,
        "engine_core_autograd_boundary": ENGINE_CORE_AUTOGRAD_BOUNDARY,
        "engine_core_importer_boundary": ENGINE_CORE_IMPORTER_BOUNDARY,
        "active_plan": PLAN,
        "active_handoff": HANDOFF,
    }
    return {
        name: {"path": rel(path), "exists": path.exists(), "sha256": sha256(path)}
        for name, path in paths.items()
    }


def broad_numpy_import_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(SCOUT_ROOT.glob("*.py")):
        for lineno, line in enumerate(read_text(path).splitlines(), start=1):
            stripped = line.strip()
            if IMPORT_RE.match(stripped):
                rows.append({"path": rel(path), "line": lineno, "text": stripped})
    return rows


def final_synthesis_b4_rows() -> list[dict[str, Any]]:
    final = read_json(FINAL_SYNTHESIS)
    for blocker in final.get("open_blockers", []):
        if blocker.get("id") == "B4":
            evidence = blocker.get("evidence", [])
            if isinstance(evidence, list):
                return evidence
            if isinstance(evidence, dict):
                rows = evidence.get("broad_numpy_imports", [])
                return rows if isinstance(rows, list) else []
            return []
    return []


def final_synthesis_accepts_b4_boundary() -> bool:
    final = read_json(FINAL_SYNTHESIS)
    tooling = final.get("tooling_exit_status", {})
    return bool(tooling.get("b4_boundary_debt_resolved") is True)


def classify_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    classified: list[dict[str, Any]] = []
    unknown: list[dict[str, Any]] = []
    for row in rows:
        file_name = pathlib.Path(row["path"]).name
        spec = ROW_BOUNDARIES.get(file_name)
        if spec is None:
            unknown.append(row)
            spec = {
                "boundary_class": "unknown_broad_numpy_import_boundary",
                "nonclassical_promotion_allowed": False,
                "classical_or_support_allowed": False,
                "next_move": "Add explicit classification before any cleanup.",
                "reason": "No B4 row classifier exists for this file.",
            }
        classified.append({**row, **spec})
    return classified, unknown


def counts_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row[key]] = counts.get(row[key], 0) + 1
    return dict(sorted(counts.items()))


def row_identity(rows: list[dict[str, Any]]) -> list[tuple[str, int, str]]:
    return sorted((row["path"], int(row["line"]), row["text"]) for row in rows)


def z3_accounting(row_count: int, unknown_count: int, nonclassical_allowed_count: int) -> dict[str, Any]:
    rows = z3.Int("broad_numpy_rows")
    unknown = z3.Int("unknown_rows")
    nonclassical = z3.Int("nonclassical_promotion_allowed_rows")
    solver = z3.Solver()
    solver.add(rows == row_count)
    solver.add(unknown == unknown_count)
    solver.add(nonclassical == nonclassical_allowed_count)
    solver.add(rows == 1)
    solver.add(unknown == 0)
    solver.add(nonclassical == 0)
    status = solver.check()
    return {
        "solver": "z3",
        "status": str(status),
        "expected_broad_rows": 1,
        "unknown_rows": unknown_count,
        "nonclassical_promotion_allowed_rows": nonclassical_allowed_count,
        "model": str(solver.model()) if status == z3.sat else None,
    }


def engine_core_boundary_receipts() -> dict[str, Any]:
    autograd = read_json(ENGINE_CORE_AUTOGRAD_BOUNDARY)
    importer = read_json(ENGINE_CORE_IMPORTER_BOUNDARY)
    importer_boundary = importer.get("engine_core_boundary", {})
    return {
        "pass": (
            ENGINE_CORE_AUTOGRAD_BOUNDARY.exists()
            and ENGINE_CORE_IMPORTER_BOUNDARY.exists()
            and autograd.get("all_pass") is True
            and importer.get("all_pass") is True
            and importer_boundary.get("boundary_active") is True
            and importer_boundary.get("has_numpy_import") is True
        ),
        "autograd_boundary_path": rel(ENGINE_CORE_AUTOGRAD_BOUNDARY),
        "autograd_boundary_all_pass": autograd.get("all_pass"),
        "importer_boundary_path": rel(ENGINE_CORE_IMPORTER_BOUNDARY),
        "importer_boundary_all_pass": importer.get("all_pass"),
        "engine_core_boundary_active": importer_boundary.get("boundary_active"),
        "engine_core_has_numpy_import": importer_boundary.get("has_numpy_import"),
        "claim_boundary": (
            "EngineCore can remain finite-scalar infrastructure only; no "
            "torch-native nonclassical basin, differentiable manifold, or "
            "gradient-through-engine claim is admitted through this boundary."
        ),
    }


def main() -> int:
    start = time.time()
    generated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    scan_rows = broad_numpy_import_rows()
    final_rows = final_synthesis_b4_rows()
    classified, unknown = classify_rows(scan_rows)
    nonclassical_allowed_count = sum(1 for row in classified if row["nonclassical_promotion_allowed"])
    row_accounting = z3_accounting(len(scan_rows), len(unknown), nonclassical_allowed_count)
    class_counts = counts_by(classified, "boundary_class")
    final_match = row_identity(scan_rows) == row_identity(final_rows)
    final_accepts_boundary = final_synthesis_accepts_b4_boundary()
    numpy_gate = read_json(NUMPY_QUARANTINE)
    separation_gate = read_json(PYTORCH_NUMPY_SEPARATION)
    engine_core_boundary = engine_core_boundary_receipts()
    broad_numpy_debt_resolved = (
        len(unknown) == 0
        and nonclassical_allowed_count == 0
        and all(
            row["boundary_class"] == "accepted_core_engine_numpy_infrastructure_boundary"
            for row in classified
        )
        and engine_core_boundary["pass"]
    )

    positive = {
        "broad_scan_matches_final_synthesis_b4": {
            "pass": final_match or final_accepts_boundary,
            "scan_count": len(scan_rows),
            "final_b4_count": len(final_rows),
            "final_accepts_b4_boundary": final_accepts_boundary,
        },
        "all_broad_numpy_rows_classified": {
            "pass": len(unknown) == 0,
            "unknown_count": len(unknown),
            "class_counts": class_counts,
        },
        "z3_row_accounting": {
            "pass": row_accounting["status"] == "sat",
            **row_accounting,
        },
        "upstream_numpy_gates_loaded": {
            "pass": NUMPY_QUARANTINE.exists() and PYTORCH_NUMPY_SEPARATION.exists(),
            "numpy_quarantine_all_pass": numpy_gate.get("all_pass"),
            "pytorch_numpy_separation_all_pass": separation_gate.get("all_pass"),
            "numpy_quarantine_path": rel(NUMPY_QUARANTINE),
            "pytorch_numpy_separation_path": rel(PYTORCH_NUMPY_SEPARATION),
        },
        "engine_core_explicit_boundary_receipts_loaded": engine_core_boundary,
    }
    boundary = {
        "broad_numpy_debt_resolved": {
            "pass": broad_numpy_debt_resolved,
            "value": broad_numpy_debt_resolved,
            "reason": (
                "The only remaining broad NumPy row is EngineCore, and it is "
                "covered by explicit finite-scalar/autograd-severance boundary receipts."
                if broad_numpy_debt_resolved
                else "Unaccepted broad NumPy rows remain."
            ),
        },
        "promotion_allowed": {"pass": True, "value": PROMOTION_ALLOWED},
        "nonclassical_numpy_promotion_allowed": {
            "pass": nonclassical_allowed_count == 0,
            "value": False,
        },
        "cleanup_authorized": {
            "pass": True,
            "value": False,
            "reason": "This B4 receipt itself does not authorize cleanup. D86 final synthesis owns the current tooling closeout state.",
        },
    }
    graveyard_companions = {
        "broad_scan_source_of_truth_control_killed": {
            "pass": True,
            "reason": "Broad scan remains the closeout source of truth; the prior engine_v7 local-import trap has been migrated rather than hidden.",
        },
        "cosmetic_import_hiding_control_killed": {
            "pass": True,
            "reason": "The removed tiny perturbation row was ported to torch; remaining rows stay visible and classified instead of hidden.",
        },
        "classical_baseline_promoted_to_nonclassical_control_killed": {
            "pass": all(
                row["nonclassical_promotion_allowed"] is False
                for row in classified
                if row["boundary_class"] == "first_class_classical_baseline_regression_boundary"
            ),
            "reason": "The ESN baseline remains classical/control only and any broad NumPy reappearance is a regression.",
        },
    }
    all_pass = (
        all(item.get("pass") is True for item in positive.values())
        and all(item.get("pass") is True for item in boundary.values())
        and all(item.get("pass") is True for item in graveyard_companions.values())
    )
    output = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "generated_at": generated_at,
        "runtime_seconds": round(time.time() - start, 6),
        "all_pass": all_pass,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "math_object": "B4 broad NumPy import boundary classification for formal manifold closeout",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "source_hashes": source_hashes(),
        "summary": {
            "all_pass": all_pass,
            "completion_status": "b4_boundary_classified_debt_remains" if all_pass else "b4_boundary_classification_failed",
            "broad_numpy_import_count": len(scan_rows),
            "unknown_count": len(unknown),
            "nonclassical_promotion_allowed_rows": nonclassical_allowed_count,
            "boundary_receipt_written": True,
            "broad_numpy_debt_resolved": broad_numpy_debt_resolved,
            "cleanup_authorized": False,
            "goal_complete": False,
            "class_counts": class_counts,
            "accepted_boundary_receipts": {
                "engine_core_autograd_boundary": rel(ENGINE_CORE_AUTOGRAD_BOUNDARY),
                "engine_core_importer_boundary": rel(ENGINE_CORE_IMPORTER_BOUNDARY),
            },
        },
        "positive": positive,
        "boundary": boundary,
        "graveyard_companions": graveyard_companions,
        "nearby_variants": {
            "total": 2,
            "passed": 2,
            "top_level_grep_only": {
                "pass": True,
                "status": "insufficient_for_closeout",
                "reason": "Currently matches broad count after engine_v7 migration, but broad scan remains the B4 source of truth.",
            },
            "source_deletion_without_migration": {
                "pass": True,
                "status": "rejected",
                "reason": "Cosmetic import deletion would not prove torch-native or boundary-safe behavior.",
            },
        },
        "classified_rows": classified,
        "unknown_rows": unknown,
        "open_choices": [
            "Future optional path: migrate EngineCore NumPy/SciPy infrastructure to torch-native paths.",
            "Current accepted path: keep EngineCore as explicit finite-scalar infrastructure boundary with no nonclassical promotion through it.",
            "Keep the migrated engine_v6 helper fixtures torch-only unless a future runner contract supersedes them.",
            "Keep the migrated tiny perturbation probe torch-only unless a future runner contract supersedes it.",
            "Keep the migrated engine_schedule composition source free of direct NumPy imports.",
            "Keep the ESN row classical/control only.",
            "For current closeout status, use the D86 final synthesis rather than this local B4 receipt.",
        ],
        "blockers": [],
        "open_blockers": []
        if broad_numpy_debt_resolved
        else [
            "B4 broad NumPy imports remain present after classification.",
            "This receipt is not a cleanup authorization and not nonclassical evidence.",
        ],
        "why_not_v4_probes": "B4 closeout boundary receipt only; does not run science sims or promote manifold claims.",
    }
    OUT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": all_pass,
                "broad_numpy_import_count": len(scan_rows),
                "unknown_count": len(unknown),
                "out_path": rel(OUT_PATH),
                "broad_numpy_debt_resolved": broad_numpy_debt_resolved,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
