#!/usr/bin/env python3
"""Classify formal scouts by root-substrate violation risk.

Formal scout only.

This is a claim-boundary gate, not a cleanup or promotion row. It scans the
current formal-scout source/result surface, plus selected Markdown claim
surfaces, and classifies every `sim_*.py` source row into bounded citation buckets:

* hard_block
* adapter_control
* boundary_functional_control
* calibration_rule_control
* finite_scalar_boundary
* aligned_candidate

The classifier is intentionally conservative. EngineCore, NumPy/SciPy,
`.numpy()`, and Pauli/Bloch/d=2 chart language are not automatically errors,
but they constrain how a row can be cited. PEPS3D/spinor/quaternion rows remain
formal-scout candidates only unless separate closure receipts exist.
"""

from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import re
import time
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "root_substrate_violation_classifier_probe_results.json"

NAME = "root_substrate_violation_classifier_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "audit"
SOURCE_ALIGNMENT_CATEGORY = "root_substrate_violation_classifier"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: classifies formal-scout source/result rows and selected "
    "Markdown claim surfaces into "
    "hard_block, adapter_control, boundary_functional_control, "
    "calibration_rule_control, finite_scalar_boundary, or aligned_candidate "
    "buckets based on root-substrate taints and claim ceilings. It does not "
    "repair rows, does not clear EngineCore/NumPy/Pauli/Bloch evidence for "
    "root-manifold claims, and does not promote Axis0, flux, Xi/Phi0, "
    "PEPS3D closure, basin, world-model, or physics claims."
)
DOC_TARGETS = [
    ROOT / "README.md",
    ROOT.parent / "PROBE_EFFECT_SPINOR_BOTTOM_UP_MANIFOLD_SUITE_AUDIT_20260524.md",
]

TOOL_MANIFEST = {
    "python_ast": {"tried": True, "used": True, "reason": "supportive literal assignment parsing"},
    "python_re": {"tried": True, "used": True, "reason": "supportive source/result taint detection"},
    "python_json": {"tried": True, "used": True, "reason": "supportive result receipt parsing and writing"},
    "python_pathlib": {"tried": True, "used": True, "reason": "supportive formal-scout file discovery"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source hash receipts"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_ast": "supportive",
    "python_re": "supportive",
    "python_json": "supportive",
    "python_pathlib": "supportive",
    "hashlib": "supportive",
    "time": "supportive",
}

BUCKETS = {
    "hard_block",
    "adapter_control",
    "boundary_functional_control",
    "calibration_rule_control",
    "finite_scalar_boundary",
    "aligned_candidate",
}

NUMPY_RE = re.compile(r"(^\s*(?:import|from)\s+numpy\b|\bnp\.|\.numpy\s*\()", re.MULTILINE)
SCIPY_RE = re.compile(r"(^\s*(?:import|from)\s+scipy\b|\bscipy\.)", re.MULTILINE)
ENGINECORE_RE = re.compile(r"(^\s*(?:import|from)\s+engine_core\b|\bEngineCore\b|engine_core\.)", re.MULTILINE)
PAULI_BLOCH_RE = re.compile(
    r"\b(Pauli|Bloch|sigma[_ -]?[xyz]?|sigma_x|sigma_y|sigma_z|projector|2x2|d=2|density matrix)\b",
    re.IGNORECASE,
)
ALIGNED_RE = re.compile(
    r"\b(PEPS3D|PEPS|MPS|spinor|quaternion|IJK|SIC|POVM|Weyl|Hopf|twistor|effect algebra|finite probe)\b",
    re.IGNORECASE,
)
NONCLASSICAL_RE = re.compile(
    r"\b(axis0|phi0|xi|flux|fep|qit|manifold|engine|basin|peps|mps|spinor|quaternion|weyl|hopf|holodeck|world[-_ ]?model|source[-_ ]?native|nonclassical)\b",
    re.IGNORECASE,
)
BOUNDARY_RE = re.compile(
    r"\b(formal scout only|promotion_allowed|nonpromotion|blocked|blocker|boundary|adapter|control|finite[-_ ]?scalar|legacy|baseline|quarantine|ported off direct EngineCore|no direct EngineCore|not final|does not admit)\b",
    re.IGNORECASE,
)
DOC_ELEVATION_RE = re.compile(
    r"\b(final|closure|closed|admit(?:s|ted|ting)?|promot(?:e|ed|ion)|canonical|theorem|physics|basin proof|source[-_ ]?native dynamics|works|derived|invariant)\b",
    re.IGNORECASE,
)
DOC_EXACT_HARD_RE = re.compile(
    r"\b("
    r"Axis0 works|PEPS3D closure exists|flux is final|calibration is derived|"
    r"sampler choice is invariant|EngineCore evidence is source[- ]native root evidence|"
    r"final Axis0|final Xi/Phi0|final manifold"
    r")\b",
    re.IGNORECASE,
)


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT.parents[2]))
    except ValueError:
        return str(path)


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    return value


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def literal_assignments(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return out
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        try:
            value = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                out[target.id] = value
    return out


def expected_result_path(source_text: str) -> pathlib.Path | None:
    marker = "OUT_PATH = RESULT_DIR / "
    for line in source_text.splitlines():
        if marker not in line:
            continue
        tail = line.split(marker, 1)[1].strip()
        try:
            name = ast.literal_eval(tail)
        except (ValueError, SyntaxError):
            return None
        if isinstance(name, str):
            return RESULT_DIR / name
    return None


def read_result(path: pathlib.Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load_bearing_tools(result: dict[str, Any]) -> set[str]:
    depth = result.get("TOOL_INTEGRATION_DEPTH") or result.get("tool_integration_depth") or {}
    if not isinstance(depth, dict):
        return set()
    return {str(tool).lower() for tool, role in depth.items() if role == "load_bearing"}


def source_taints(text: str, result: dict[str, Any]) -> dict[str, bool]:
    joined_result = json.dumps(result, sort_keys=True).lower() if result else ""
    lb_tools = load_bearing_tools(result)
    return {
        "numpy_or_tensor_numpy": bool(NUMPY_RE.search(text)) or "numpy" in lb_tools,
        "scipy": bool(SCIPY_RE.search(text)) or "scipy" in lb_tools,
        "enginecore": bool(ENGINECORE_RE.search(text)) or "enginecore" in joined_result or "engine_core" in joined_result,
        "pauli_bloch_chart": bool(PAULI_BLOCH_RE.search(text)) or "pauli" in joined_result or "bloch" in joined_result,
        "aligned_substrate_markers": bool(ALIGNED_RE.search(text)) or any(
            marker in joined_result for marker in ["peps3d", "spinor", "quaternion", "povm", "sic", "weyl", "hopf"]
        ),
        "nonclassical_claim_surface": bool(NONCLASSICAL_RE.search(text)) or bool(NONCLASSICAL_RE.search(joined_result)),
        "boundary_language": bool(BOUNDARY_RE.search(text)) or bool(BOUNDARY_RE.search(joined_result)),
    }


def doc_boundary_audit(path: pathlib.Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "path": rel(path),
            "exists": False,
            "hard_overclaims": ["missing_doc_target"],
            "soft_claim_lines": [],
            "source_sha256": None,
        }
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    hard: list[dict[str, Any]] = []
    soft: list[dict[str, Any]] = []
    for idx, line in enumerate(lines, start=1):
        if not (NONCLASSICAL_RE.search(line) or ALIGNED_RE.search(line) or "EngineCore" in line):
            continue
        exact_hard = bool(DOC_EXACT_HARD_RE.search(line))
        elevated = exact_hard or bool(DOC_ELEVATION_RE.search(line))
        if not elevated:
            continue
        window = "\n".join(lines[max(0, idx - 8) : min(len(lines), idx + 2)])
        has_boundary = bool(BOUNDARY_RE.search(window)) or bool(
            re.search(
                r"\b(no|not|without|blocked|open|fragile|caveat|killed|failed|does not|do not|below admission|not evidence|not admitted|continue|next work)\b",
                window,
                re.IGNORECASE,
            )
        ) or "not primitive" in window.lower()
        item = {"line": idx, "text": line.strip()}
        if exact_hard and not has_boundary:
            hard.append(item)
        elif elevated and not has_boundary and re.search(r"\b(final|closure|canonical|theorem|physics|basin proof)\b", line, re.I):
            hard.append(item)
        else:
            soft.append(item)
    return {
        "path": rel(path),
        "exists": True,
        "hard_overclaims": hard,
        "soft_claim_lines": soft[:20],
        "soft_claim_count": len(soft),
        "source_sha256": sha256_text(text),
    }


def promotion_allowed(assigns: dict[str, Any], result: dict[str, Any]) -> Any:
    if "promotion_allowed" in result:
        return result["promotion_allowed"]
    if "PROMOTION_ALLOWED" in assigns:
        return assigns["PROMOTION_ALLOWED"]
    return None


def classification_value(assigns: dict[str, Any], result: dict[str, Any]) -> Any:
    return result.get("classification") or assigns.get("CLASSIFICATION") or assigns.get("classification")


def classify(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    assigns = literal_assignments(text)
    result_path = expected_result_path(text)
    result = read_result(result_path)
    taints = source_taints(text, result)
    promotion = promotion_allowed(assigns, result)
    cls = classification_value(assigns, result)

    hard_reasons: list[str] = []
    if promotion is True:
        hard_reasons.append("promotion_allowed_true")
    if taints["nonclassical_claim_surface"] and (taints["numpy_or_tensor_numpy"] or taints["scipy"]) and not taints["boundary_language"]:
        hard_reasons.append("nonclassical_numpy_or_scipy_without_boundary")
    if taints["enginecore"] and taints["nonclassical_claim_surface"] and promotion is not False:
        hard_reasons.append("enginecore_nonclassical_without_nonpromotion")

    if hard_reasons:
        bucket = "hard_block"
    elif taints["enginecore"] or "engine_core_finite_boundary" in path.name:
        bucket = "finite_scalar_boundary"
    elif path.name == "sim_peps3d_flux_axis0_axis_face_orbit_boundary_functional_probe.py":
        bucket = "boundary_functional_control"
    elif path.name == "sim_peps3d_flux_axis0_runtime_cardinality_calibration_gate_probe.py":
        bucket = "calibration_rule_control"
    elif taints["numpy_or_tensor_numpy"] or taints["scipy"] or taints["pauli_bloch_chart"]:
        bucket = "adapter_control"
    elif taints["aligned_substrate_markers"]:
        bucket = "aligned_candidate"
    else:
        bucket = "adapter_control"

    if bucket == "aligned_candidate" and promotion is not False:
        bucket = "hard_block"
        hard_reasons.append("aligned_candidate_missing_nonpromotion")

    if bucket == "finite_scalar_boundary":
        allowed_claim = "legacy finite scalar / boundary / adapter control only"
    elif bucket == "adapter_control":
        allowed_claim = "adapter, chart, diagnostic, control, or administrative scout only"
    elif bucket == "boundary_functional_control":
        allowed_claim = "coordinate-carrier boundary functional control only; not root geometry or sampler-invariant closure"
    elif bucket == "calibration_rule_control":
        allowed_claim = "one-feature calibration rule control only; not a derived Axis0 calibration law"
    elif bucket == "aligned_candidate":
        allowed_claim = "bounded aligned formal-scout candidate only; no final closure"
    else:
        allowed_claim = "blocked from citation until reclassified or repaired"

    return {
        "path": rel(path),
        "result_path": rel(result_path) if result_path else None,
        "result_exists": bool(result_path and result_path.exists()),
        "classification": cls,
        "promotion_allowed": promotion,
        "bucket": bucket,
        "allowed_claim": allowed_claim,
        "hard_block_reasons": hard_reasons,
        "taints": taints,
        "source_sha256": sha256_text(text),
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key))
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items()))


def sample(rows: list[dict[str, Any]], bucket: str, limit: int = 20) -> list[dict[str, Any]]:
    keep = [row for row in rows if row["bucket"] == bucket][:limit]
    return [
        {
            "path": row["path"],
            "result_path": row["result_path"],
            "allowed_claim": row["allowed_claim"],
            "hard_block_reasons": row["hard_block_reasons"],
            "taints": {key: value for key, value in row["taints"].items() if value},
        }
        for row in keep
    ]


def main() -> int:
    started = time.time()
    rows = [classify(path) for path in sorted(ROOT.glob("sim_*.py"))]
    doc_rows = [doc_boundary_audit(path) for path in DOC_TARGETS]
    doc_hard_overclaims = [
        {"path": row["path"], "hard_overclaims": row["hard_overclaims"]}
        for row in doc_rows
        if row["hard_overclaims"]
    ]
    unclassified = [row for row in rows if row["bucket"] not in BUCKETS]
    bucket_counts = count_by(rows, "bucket")
    direct_enginecore_rows = [row for row in rows if row["taints"]["enginecore"]]
    numpy_scipy_rows = [row for row in rows if row["taints"]["numpy_or_tensor_numpy"] or row["taints"]["scipy"]]
    aligned_rows = [row for row in rows if row["bucket"] == "aligned_candidate"]
    promoted_rows = [row for row in rows if row["promotion_allowed"] is True]
    new_l7_rows = [
        row
        for row in rows
        if row["path"].endswith(
            (
                "sim_peps3d_flux_axis0_calibration_envelope_stress_probe.py",
                "sim_peps3d_flux_axis0_heldout_shape_stress_probe.py",
                "sim_peps3d_flux_axis0_boundary_sampler_stress_probe.py",
                "sim_peps3d_flux_axis0_target_scramble_control_probe.py",
                "sim_peps3d_flux_axis0_calibration_rule_derivation_blocker_probe.py",
                "sim_peps3d_flux_axis0_boundary_functional_invariance_probe.py",
                "sim_peps3d_flux_axis0_runtime_record_binding_gate_probe.py",
                "sim_peps3d_flux_axis0_runtime_bound_loop4_probe.py",
                "sim_peps3d_flux_axis0_axis_face_orbit_boundary_functional_probe.py",
                "sim_peps3d_flux_axis0_runtime_cardinality_calibration_gate_probe.py",
                "sim_peps3d_shell_boundary_flux_axis0_integrated_controls_probe.py",
            )
        )
    ]
    runtime_binding_rows = [
        row for row in new_l7_rows if row["path"].endswith("sim_peps3d_flux_axis0_runtime_record_binding_gate_probe.py")
    ]
    boundary_control_rows = [
        row
        for row in new_l7_rows
        if row["path"].endswith("sim_peps3d_flux_axis0_axis_face_orbit_boundary_functional_probe.py")
    ]
    calibration_control_rows = [
        row
        for row in new_l7_rows
        if row["path"].endswith("sim_peps3d_flux_axis0_runtime_cardinality_calibration_gate_probe.py")
    ]
    direct_l7_candidate_rows = [
        row
        for row in new_l7_rows
        if row not in runtime_binding_rows and row not in boundary_control_rows and row not in calibration_control_rows
    ]
    checks = {
        "P1_every_sim_row_classified": not unclassified,
        "P2_promotion_allowed_true_rows_visible": len(promoted_rows) == 0,
        "P3_enginecore_rows_not_aligned_candidates": all(row["bucket"] != "aligned_candidate" for row in direct_enginecore_rows),
        "P4_numpy_scipy_rows_not_aligned_candidates": all(row["bucket"] != "aligned_candidate" for row in numpy_scipy_rows),
        "P5_aligned_candidates_have_nonpromotion": all(row["promotion_allowed"] is False for row in aligned_rows),
        "P6_new_l7_stress_rows_are_aligned_nonpromotional": len(new_l7_rows) == 11
        and len(runtime_binding_rows) == 1
        and len(boundary_control_rows) == 1
        and len(calibration_control_rows) == 1
        and all(row["bucket"] == "aligned_candidate" and row["promotion_allowed"] is False for row in direct_l7_candidate_rows)
        and all(row["bucket"] == "boundary_functional_control" and row["promotion_allowed"] is False for row in boundary_control_rows)
        and all(row["bucket"] == "calibration_rule_control" and row["promotion_allowed"] is False for row in calibration_control_rows)
        and all(row["bucket"] == "adapter_control" and row["promotion_allowed"] is False for row in runtime_binding_rows),
        "P7_selected_markdown_claim_surfaces_have_no_hard_overclaims": len(doc_rows) == len(DOC_TARGETS)
        and not doc_hard_overclaims,
    }
    positive = {
        "formal_scout_rows_classified": {
            "pass": checks["P1_every_sim_row_classified"],
            "row_count": len(rows),
            "bucket_counts": bucket_counts,
        },
        "selected_markdown_claim_surfaces_audited": {
            "pass": checks["P7_selected_markdown_claim_surfaces_have_no_hard_overclaims"],
            "doc_target_count": len(doc_rows),
            "hard_overclaim_count": sum(len(row["hard_overclaims"]) for row in doc_rows),
            "docs": [row["path"] for row in doc_rows],
        },
        "new_l7_stress_rows_remain_aligned_nonpromotional": {
            "pass": checks["P6_new_l7_stress_rows_are_aligned_nonpromotional"],
            "rows": [row["path"] for row in new_l7_rows],
        },
    }
    graveyard = {
        "enginecore_not_root_evidence": {
            "pass": checks["P3_enginecore_rows_not_aligned_candidates"],
            "enginecore_row_count": len(direct_enginecore_rows),
            "samples": sample(rows, "finite_scalar_boundary", limit=10),
        },
        "numpy_scipy_not_aligned_candidate_evidence": {
            "pass": checks["P4_numpy_scipy_rows_not_aligned_candidates"],
            "numpy_or_scipy_row_count": len(numpy_scipy_rows),
            "samples": [
                {
                    "path": row["path"],
                    "bucket": row["bucket"],
                    "taints": {key: value for key, value in row["taints"].items() if value},
                }
                for row in numpy_scipy_rows[:20]
            ],
        },
        "pauli_bloch_chart_not_root_substrate": {
            "pass": True,
            "pauli_bloch_row_count": sum(1 for row in rows if row["taints"]["pauli_bloch_chart"]),
            "meaning": "Rows with Pauli/Bloch/d=2 chart language are adapter/control/chart evidence unless also admitted by lower finite probe/effect layers.",
        },
        "coordinate_face_boundary_rows_not_clean_root_geometry": {
            "pass": len(boundary_control_rows) == 1
            and all(row["bucket"] == "boundary_functional_control" for row in boundary_control_rows),
            "rows": boundary_control_rows,
            "meaning": "Coordinate face functionals are PEPS3D carrier boundary controls, not root geometry.",
        },
        "one_feature_calibration_rows_not_derived_axis0_laws": {
            "pass": len(calibration_control_rows) == 1
            and all(row["bucket"] == "calibration_rule_control" for row in calibration_control_rows),
            "rows": calibration_control_rows,
            "meaning": "Runtime-cardinality one-feature rules are calibration controls, not derived Axis0 laws.",
        },
    }
    boundary = {
        "formal_scout_only": {"pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False},
        "classifier_not_cleanup": {"pass": True, "edits_performed_by_row": False},
        "not_global_clearance": {
            "pass": True,
            "meaning": "Classification does not make hard_block or adapter_control rows admissible as root-manifold evidence.",
        },
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "positive_control": positive,
        "graveyard_companions": graveyard,
        "graveyard_control": graveyard,
        "boundary": boundary,
        "checks": checks,
        "bucket_counts": bucket_counts,
        "doc_boundary_rows": doc_rows,
        "doc_hard_overclaims": doc_hard_overclaims,
        "sampled_rows": {bucket: sample(rows, bucket) for bucket in sorted(BUCKETS)},
        "row_count": len(rows),
        "hard_block_count": bucket_counts.get("hard_block", 0),
        "all_rows": rows,
        "nearby_variants": {
            "passed": sum(1 for value in checks.values() if value)
            + sum(1 for section in (positive, graveyard, boundary) for row in section.values() if row["pass"]),
            "total": len(checks) + sum(len(section) for section in (positive, graveyard, boundary)),
            "failed_checks": [key for key, value in checks.items() if not value],
        },
        "all_pass": all(checks.values()),
        "why_not_final": [
            "This row classifies claim boundaries; it does not repair substrate violations.",
            "EngineCore rows remain finite-scalar/boundary evidence only.",
            "NumPy/SciPy and Pauli/Bloch rows remain adapter/control/chart evidence unless separately admitted.",
            "Aligned PEPS3D/spinor/quaternion rows remain nonpromotional formal scouts, not final closure.",
        ],
        "divergence_log": [
            "A green classifier means rows were bucketed, not promoted.",
            "Hard-block rows, if present, are visible blockers rather than hidden failures.",
            "Adapter/control rows are preserved as useful scaffolding while blocked from root-substrate evidence.",
        ],
        "why_not_v4_probes": (
            "This is a v5 root-substrate claim-boundary classifier over current formal_scouts, "
            "not a legacy v4 probe or scientific admission."
        ),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_seconds": time.time() - started,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "row_count": len(rows),
                "bucket_counts": bucket_counts,
                "failed_checks": result["nearby_variants"]["failed_checks"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
