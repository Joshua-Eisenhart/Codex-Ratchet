#!/usr/bin/env python3
"""Audit grok_sim iter substrate alignment without importing formal proof claims.

This is a sidequest-local guard. It does not promote results, and it does not
read or write formal_scout surfaces.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ITERS = ROOT / "iters"
RESULTS = ROOT / "results"
OUT_JSON = RESULTS / "grok_sim_substrate_violation_gate_20260524_results.json"
OUT_MD = ROOT / "GROK_SIM_SUBSTRATE_VIOLATION_AUDIT_20260524.md"

# Iter scope: discovery-based. Scans all iter_*.py files and extracts the
# label (e.g., "283", "306a", "306a2") so lettered/sub-suffix iters are
# detected. Originally hard-coded ITER_START=283 / ITER_END=304 — owner
# audit 2026-05-24 flagged that as blind to letter-suffixed iters.
ITER_LABEL_PATTERN = re.compile(r"^iter_(\d+[a-z]?[\d]*)(?:_.*)?\.py$")

# Kept as legacy markers for documentation only — actual scope is discovered.
ITER_START = 283
ITER_END = 304


PATTERNS = {
    "numpy_import": re.compile(r"(^|\n)\s*(import numpy|from numpy)", re.I),
    "scipy_import": re.compile(r"(^|\n)\s*(import scipy|from scipy)", re.I),
    "dot_numpy": re.compile(r"\.numpy\s*\("),
    "enginecore": re.compile(r"\bEngineCore\b|engine[_-]?core", re.I),
    "pauli_bloch_mention": re.compile(
        r"\b(PAULI|Pauli|sigma_|sigma[xyz]\b|SX\b|SY\b|SZ\b|Bloch|bloch)\b"
    ),
    "pauli_bloch_primitive": re.compile(
        r"(^|\n)\s*(PAULI|SIGMA|SX|SY|SZ)\s*=|"
        r"\b(def\s+\w*bloch|measure_bloch|bloch_to_density|quat_to_density|"
        r"to_bloch|from_bloch|pauli_basis|sigma_basis|np\.kron)\b",
        re.I,
    ),
    "kraus_dense": re.compile(r"\b(Kraus|kraus|np\.kron|np\.linalg|eigvalsh|trace_norm|expm)\b"),
    "dense_rho": re.compile(r"\b(rho|density_matrix|density matrix|partial_trace|von_neumann)\b", re.I),
    "torch": re.compile(r"\b(import torch|from torch|torch\.)\b"),
    "quimb": re.compile(r"\b(import quimb|from quimb|qtn\.|PEPS|PEPS3D)\b"),
    "quaternion": re.compile(r"\b(quaternion|qmul|qconj|Hamilton product|IJK|ijk)\b", re.I),
    "spinor": re.compile(r"\b(spinor|Weyl|left[-_ ]right|L/R|H_unit|sheet)\b", re.I),
    "mps": re.compile(r"\b(MPS|matrix product|bond_dim|left_canonical)\b", re.I),
    "peps": re.compile(r"\b(PEPS|PEPS3D|boundary contraction|surface contraction)\b", re.I),
}


def read_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        return {"_json_error": str(exc)}


def find_single(pattern: str, folder: Path) -> Path | None:
    matches = sorted(folder.glob(pattern))
    return matches[0] if matches else None


def discover_iter_labels(folder: Path) -> list[str]:
    """Discover all iter labels present as iter_*.py files in `folder`.

    Returns labels (e.g., "283", "306a", "306a2") in sorted order. Letter-
    suffixed iters are sorted alongside numeric iters.
    """
    labels = []
    for f in folder.glob("iter_*.py"):
        m = ITER_LABEL_PATTERN.match(f.name)
        if m:
            labels.append(m.group(1))
    return sorted(set(labels), key=_sort_key)


def _sort_key(label: str) -> tuple:
    """Sort key for iter labels: numeric portion first, then letter suffix."""
    m = re.match(r"^(\d+)([a-z]?)([\d]*)$", label)
    if not m:
        return (0, "", "")
    num = int(m.group(1))
    letter = m.group(2) or ""
    sub = int(m.group(3)) if m.group(3) else 0
    return (num, letter, sub)


def find_iter_files(label: str, iters_folder: Path, results_folder: Path) -> tuple[Path | None, Path | None]:
    """Find source iter_{label}_*.py and result iter_{label}_*_results.json."""
    source = None
    for f in iters_folder.glob(f"iter_{label}_*.py"):
        source = f
        break
    result = None
    for f in results_folder.glob(f"iter_{label}_*_results.json"):
        result = f
        break
    return source, result


def tool_depth_entries(data: dict[str, Any]) -> dict[str, str]:
    raw = (
        data.get("TOOL_INTEGRATION_DEPTH")
        or data.get("tool_integration_depth")
        or data.get("tool_depth")
        or {}
    )
    if not isinstance(raw, dict):
        return {}
    out: dict[str, str] = {}
    for key, value in raw.items():
        role = value
        if isinstance(value, dict):
            role = value.get("role") or value.get("depth") or value.get("integration_depth")
        if role is None:
            role = value
        out[str(key).lower()] = str(role).lower()
    return out


def find_nested_strings(obj: Any) -> list[str]:
    found: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            found.append(str(key))
            found.extend(find_nested_strings(value))
    elif isinstance(obj, list):
        for item in obj:
            found.extend(find_nested_strings(item))
    elif obj is not None:
        found.append(str(obj))
    return found


def has_load_bearing(depth: dict[str, str], *names: str) -> bool:
    for name in names:
        for key, value in depth.items():
            if name in key and "load_bearing" in value:
                return True
    return False


def has_supportive(depth: dict[str, str], *names: str) -> bool:
    for name in names:
        for key, value in depth.items():
            if name in key and "supportive" in value:
                return True
    return False


def analyze_iter(iter_label) -> dict[str, Any]:
    """Analyze a single iter by label.

    `iter_label` is a string like "283", "306a", or "306a2". Accepts int
    for backward compatibility (converts to str).
    """
    label = str(iter_label)
    source, result = find_iter_files(label, ITERS, RESULTS)
    source_text = read_text(source)
    result_data = load_json(result)
    result_text = json.dumps(result_data, sort_keys=True) if result_data else ""
    text = source_text + "\n" + result_text
    depth = tool_depth_entries(result_data)

    hits = {name: bool(pattern.search(text)) for name, pattern in PATTERNS.items()}
    source_hits = {name: bool(pattern.search(source_text)) for name, pattern in PATTERNS.items()}
    result_strings = [s.lower() for s in find_nested_strings(result_data)]

    # AST-based check for actual .numpy() calls (excludes docstring/string
    # mentions). Overrides the regex `dot_numpy` hit when source is parseable.
    if source_text:
        try:
            import ast
            tree = ast.parse(source_text)
            actual_numpy_calls = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Attribute) and func.attr == "numpy":
                        actual_numpy_calls.append(node.lineno)
            source_hits["dot_numpy"] = len(actual_numpy_calls) > 0
            if not source_hits["dot_numpy"]:
                hits["dot_numpy"] = False  # also clear combined hits
        except SyntaxError:
            pass  # fall back to regex result

    hard_reasons: list[str] = []
    adapter_reasons: list[str] = []
    aligned_reasons: list[str] = []
    boundary_issues: list[str] = []

    if source is None:
        hard_reasons.append("missing_iter_source")
    if result is None:
        adapter_reasons.append("missing_result_receipt")
    if result_data.get("_json_error"):
        hard_reasons.append("result_json_parse_error")

    if has_load_bearing(depth, "numpy", "scipy"):
        hard_reasons.append("numpy_or_scipy_declared_load_bearing")
    if source_hits["scipy_import"]:
        hard_reasons.append("scipy_import_in_iter_source")
    if source_hits["dot_numpy"]:
        hard_reasons.append("torch_autograd_severed_by_dot_numpy_conversion")
    if hits["enginecore"]:
        hard_reasons.append("EngineCore_or_engine_core_dependency_detected")

    dense_axis_stack = source_hits["numpy_import"] and (
        source_hits["kraus_dense"] or source_hits["dense_rho"]
    )
    if dense_axis_stack and not (source_hits["quimb"] or source_hits["mps"] or source_hits["peps"]):
        hard_reasons.append("dense_numpy_density_or_kraus_stack_without_tensor_carrier")

    if source_hits["pauli_bloch_primitive"]:
        adapter_reasons.append("Pauli_Bloch_or_cartesian_chart_used_as_code_primitive")
    elif source_hits["pauli_bloch_mention"]:
        adapter_reasons.append("Pauli_Bloch_mentioned_as_disclaimer_or_representation_note")
    if has_supportive(depth, "numpy", "scipy") or source_hits["numpy_import"]:
        adapter_reasons.append("numpy_present_as_support_or_fixture")
    if "formal_scout" in str(result_data.get("classification", "")).lower():
        boundary_issues.append("grok_sim_result_uses_formal_scout_classification")
    if "formal scout" in " ".join(result_strings):
        boundary_issues.append("grok_sim_result_mentions_formal_scout_claim_ceiling")
    if result_data.get("promotion_allowed") is True:
        boundary_issues.append("promotion_allowed_true_inside_grok_sim")
    if result_data.get("evidence_allowed") is True:
        boundary_issues.append("evidence_allowed_true_inside_grok_sim")

    if source_hits["torch"]:
        aligned_reasons.append("torch_present")
    if source_hits["quaternion"]:
        aligned_reasons.append("quaternion_language_or_ops_present")
    if source_hits["spinor"]:
        aligned_reasons.append("spinor_or_sheet_language_present")
    if source_hits["quimb"] or source_hits["peps"]:
        aligned_reasons.append("quimb_or_peps_surface_present")
    if source_hits["mps"]:
        aligned_reasons.append("mps_surface_present")

    quimb_depth = depth.get("quimb", "")
    if source_hits["quimb"] and "decorative" in quimb_depth:
        adapter_reasons.append("quimb_declared_decorative_or_fallback_only")
    if source_hits["peps"] and source_hits["pauli_bloch_primitive"]:
        adapter_reasons.append("PEPS_surface_is_measured_through_Pauli_Bloch_adapter")

    if hard_reasons:
        classification = "hard_block"
    elif source_hits["pauli_bloch_primitive"]:
        classification = "adapter_control"
    elif aligned_reasons:
        classification = "aligned_candidate"
    else:
        classification = "adapter_control"
        adapter_reasons.append("insufficient_root_aligned_signal_for_aligned_candidate")

    rebuild_role = {
        "hard_block": "question_generator_only",
        "adapter_control": "adapter_or_negative_control_only",
        "aligned_candidate": "candidate_source_baseline_only",
    }[classification]

    if boundary_issues and classification == "aligned_candidate":
        rebuild_role = "candidate_source_baseline_only_receipt_boundary_invalid"

    # Schema v3 introduced by iter_306a5: receipt_complete /
    # strict_scientific_pass / expected_failure_adjusted_pass replace
    # the single all_pass. Read both schemas for backward compatibility.
    schema_version = result_data.get("schema_version", "legacy")
    pass_fields = {
        "all_pass": result_data.get("all_pass"),
        "all_pass_strict": result_data.get("all_pass_strict"),
        "all_pass_excluding_expected_failures": result_data.get("all_pass_excluding_expected_failures"),
        "receipt_complete": result_data.get("receipt_complete"),
        "strict_scientific_pass": result_data.get("strict_scientific_pass"),
        "expected_failure_adjusted_pass": result_data.get("expected_failure_adjusted_pass"),
    }

    return {
        "iter": label,
        "source": str(source.relative_to(ROOT)) if source else None,
        "result": str(result.relative_to(ROOT)) if result else None,
        "substrate_classification": classification,
        "rebuild_role": rebuild_role,
        "schema_version": schema_version,
        "pass_fields": pass_fields,
        "all_pass": result_data.get("all_pass"),  # kept for backwards-compat consumers
        "claim_ceiling": result_data.get("claim_ceiling"),
        "boundary_issues": boundary_issues,
        "hard_reasons": hard_reasons,
        "adapter_reasons": adapter_reasons,
        "aligned_reasons": aligned_reasons,
        "tool_depth": depth,
        "hits": hits,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for row in rows:
        key = row["substrate_classification"]
        counts[key] = counts.get(key, 0) + 1

    aligned = [row["iter"] for row in rows if row["substrate_classification"] == "aligned_candidate"]
    adapter = [row["iter"] for row in rows if row["substrate_classification"] == "adapter_control"]
    hard = [row["iter"] for row in rows if row["substrate_classification"] == "hard_block"]
    boundary = [row["iter"] for row in rows if row["boundary_issues"]]

    return {
        "counts": counts,
        "aligned_candidate_iters": aligned,
        "adapter_control_iters": adapter,
        "hard_block_iters": hard,
        "boundary_issue_iters": boundary,
        "source_baseline_recommendation": [
            row["iter"]
            for row in rows
            if row["substrate_classification"] == "aligned_candidate"
            and not row["hits"].get("pauli_bloch_primitive")
            and not row["hits"].get("enginecore")
        ],
        "not_evidence_statement": (
            "This gate classifies grok_sim sources for sidequest rebuild planning only. "
            "It does not authorize any formal-sim claim."
        ),
    }


def render_md(payload: dict[str, Any]) -> str:
    rows = payload["iters"]
    summary = payload["summary"]
    lines: list[str] = []
    lines.append("# grok_sim Substrate Violation Audit - 2026-05-24")
    lines.append("")
    lines.append("Status: sidequest-local audit only. No formal-sim proof import or promotion.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    iters_found = [row["iter"] for row in rows]
    lines.append(f"- Scope: discovery-based scan; detected {len(iters_found)} iters.")
    lines.append(f"- Iters found: {iters_found}")
    lines.append(f"- Counts: {json.dumps(summary['counts'], sort_keys=True)}.")
    lines.append(f"- Aligned-candidate sources: {summary['aligned_candidate_iters']}.")
    lines.append(f"- Adapter/control sources: {summary['adapter_control_iters']}.")
    lines.append(f"- Hard-block sources: {summary['hard_block_iters']}.")
    lines.append(f"- Boundary-vocabulary issue iters: {summary['boundary_issue_iters']}.")
    lines.append("")
    lines.append("## Rebuild Baseline")
    lines.append("")
    lines.append(
        "Use aligned candidates only as source baselines, not as evidence receipts. "
        "Receipts using formal_scout vocabulary need boundary repair before they can "
        "serve even as grok_sim-local ledger entries."
    )
    lines.append("")
    lines.append(
        f"Recommended source baseline window after this scan: "
        f"{summary['source_baseline_recommendation']}."
    )
    lines.append("")
    lines.append("Hard-block iters may still be useful as question generators or negative controls.")
    lines.append("Adapter/control iters may be useful for chart/readout controls, not root substrate.")
    lines.append("")
    lines.append("## Iter Ledger")
    lines.append("")
    lines.append("| iter | class | rebuild role | main blockers/caveats |")
    lines.append("|---:|---|---|---|")
    for row in rows:
        caveats = row["hard_reasons"] + row["adapter_reasons"] + row["boundary_issues"]
        if not caveats:
            caveats = row["aligned_reasons"][:2]
        caveat_text = "; ".join(caveats[:4]).replace("|", "/")
        lines.append(
            f"| {row['iter']} | {row['substrate_classification']} | "
            f"{row['rebuild_role']} | {caveat_text} |"
        )
    lines.append("")
    lines.append("## Forward Rule")
    lines.append("")
    lines.append("- New grok_sim substrate rebuilds should be PyTorch-native and spinor/quaternion-first.")
    lines.append("- NumPy/SciPy may not be load-bearing for nonclassical root-manifold claims.")
    lines.append("- Pauli, Bloch, and Cartesian d=2 charts are adapter/control surfaces only.")
    lines.append("- PEPS/PEPS3D claims must state whether they perform actual tensor-network contraction or only full-state/product fixtures.")
    lines.append("- Axis0 and flux claims must stay sidequest-local until independently rebuilt by formal sims.")
    lines.append("")
    lines.append(f"Receipt: `{OUT_JSON.relative_to(ROOT)}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    # Discovery-based scan: pick up any iter_*.py file including letter-
    # suffixed iters (e.g., iter_306a, iter_306a2). Per owner audit
    # 2026-05-24, the gate was previously blind to lettered iters.
    #
    # Scope filter: only labels with sort-key >= ITER_START (excludes old
    # iter_90-iter_282 chains that are outside the active rebuild window).
    all_labels = discover_iter_labels(ITERS)
    start_key = _sort_key(str(ITER_START))
    labels = [l for l in all_labels if _sort_key(l) >= start_key]
    rows = [analyze_iter(label) for label in labels]
    payload = {
        "kind": "grok_sim_substrate_violation_gate",
        "classification": "sidequest_audit_only",
        "claim_ceiling": "side_quest_only",
        "promotion_allowed": False,
        "evidence_allowed_for_formal": False,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": {
            "root": str(ROOT),
            "iter_start": ITER_START,
            "iter_end": ITER_END,
            "discovered_labels": [row["iter"] for row in rows],
            "discovery_method": "iter_*.py glob with ITER_LABEL_PATTERN regex",
            "formal_surfaces_read": [],
            "formal_surfaces_written": [],
        },
        "rules": {
            "hard_block": [
                "numpy_or_scipy_load_bearing",
                "torch_dot_numpy_autograd_severance",
                "EngineCore_dependency",
                "dense_numpy_density_or_kraus_stack_without_tensor_carrier",
            ],
            "adapter_control": [
                "Pauli_Bloch_cartesian_chart",
                "supportive_numpy_fixture",
                "decorative_or_fallback_tensor_tool",
                "PEPS_measured_through_Pauli_Bloch_adapter",
            ],
            "aligned_candidate": [
                "torch_native",
                "spinor_or_quaternion_first",
                "no_hard_block_detected",
                "no_Pauli_Bloch_primitive_detected",
            ],
        },
        "summary": {},
        "iters": rows,
    }
    payload["summary"] = summarize(rows)
    RESULTS.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    if payload["summary"]["hard_block_iters"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
