#!/usr/bin/env python3
"""Build a manifold-centered integration index across the active sim estate.

This is an evidence map, not a promotion surface. It keeps the geometric
constraint manifold as the root object and indexes carriers, Axis0, basin,
tool-role, and proposal estates against that object.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from two_root_constraints import legacy_sections_all_pass


ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "system_v5" / "ops" / "formal_scouts"
RESULTS = FORMAL / "results"
GROK_SIM = ROOT / "system_v5" / "grok_sim"
LEGOS_RESULTS = ROOT / "system_v5" / "legos" / "results"
TMP_ENGINE = Path("/tmp/engine_v2")
OUT_JSON = ROOT / "system_v5" / "evidence" / "sim_estate_integration_index.json"
OUT_MD = ROOT / "system_v5" / "docs" / "SIM_ESTATE_INTEGRATION_INDEX.md"

TOOL_ROLE_GATE = RESULTS / "constraint_admissible_tool_role_gate_probe_results.json"
NUMPY_QUARANTINE = RESULTS / "numpy_quarantine_source_native_nonclassical_gate_probe_results.json"
READINESS_INDEX = ROOT / "system_v5" / "evidence" / "formal_scout_readiness_index.json"
TOOL_FUNCTION_MATRIX = ROOT / "system_v5" / "evidence" / "tool_function_receipt_matrix.json"

EXTERNAL_REPOS = {
    "auto_LiRPA": Path("/Users/joshuaeisenhart/GitHub/auto_LiRPA"),
    "le-wm": Path("/Users/joshuaeisenhart/GitHub/le-wm"),
}

MANIFOLD_LAYERS = [
    "finite_constraint_complex",
    "complex_hilbert_carrier",
    "unit_spinor_sphere",
    "projective_base_sphere",
    "hopf_fiber_bundle",
    "hopf_torus_leaf_family",
    "connection_holonomy_geometry",
    "weyl_spinor_bundle",
    "chirality_orientation_cover",
    "clifford_module_geometry",
    "frame_bundle_structure_reduction",
    "tensor_product_coupling_geometry",
    "dynamic_transition_ratchet_geometry",
]

AXIS_OVERLAY_MAP = {
    "axis0": {
        "status": "open_partial",
        "role": "positive feedback loop vs negative feedback loop over deviation from reference/attractor/constraint target",
        "current_evidence": [
            "axis0_plural_candidate_multicarrier_drive_controls_probe",
            "macro_sim_axis0_plural_stage_candidate_router_probe",
            "axis0_fep_gradient_stage_local_adapter_closure_probe",
            "axis0_lewm_lirpa_pytorch_assembly_probe",
        ],
        "blockers": [
            "path_entropy and holographic_boundary_interior_reconstruction are blocked as downstream Axis0 candidates",
            "per-candidate controls still project through scalar-weighted carrier actuation",
        ],
    },
    "axis1": {
        "status": "overlay_solid_in_docs",
        "role": "first binary topology/stage coordinate for terrain classes",
        "current_evidence": ["AXIS_TERRAIN_MANIFOLD_CORRECTION_HANDOFF.md"],
    },
    "axis2": {
        "status": "overlay_solid_in_docs",
        "role": "second binary topology/stage coordinate; Axis1 x Axis2 yields Se, Ne, Ni, Si",
        "current_evidence": ["AXIS_TERRAIN_MANIFOLD_CORRECTION_HANDOFF.md"],
    },
    "axis3": {
        "status": "overlay_defined_but_formal_receipt_thin",
        "role": "fiber loop vs lifted-base loop / inner vs outer surface label; do not collapse chirality or flux into Axis3",
        "current_evidence": [
            "AXIS_AND_ENTROPY_REFERENCE.md token partition",
            "CLAUDE_THREAD_HANDOFF_FLUX_TERRAIN_AXIS_OPERATOR_DISCIPLINE_20260515.md",
        ],
        "blockers": [
            "current formal_scouts/results has no dedicated Axis3 formal receipt; legacy axis3 rows remain unadmitted in SIM_INVENTORY_INDEX",
        ],
    },
    "axis4": {
        "status": "overlay_solid_in_docs",
        "role": "heat-flow / ordering direction; inductive vs deductive noncommuting composition order",
        "current_evidence": ["AXIS_TERRAIN_MANIFOLD_CORRECTION_HANDOFF.md", "AXIS_AND_ENTROPY_REFERENCE.md"],
    },
    "axis5": {
        "status": "overlay_solid_in_docs",
        "role": "heat level / excitation intensity; hot vs cold, gradient/Lindblad/semigroup class vs spectral/Hamiltonian/group class",
        "current_evidence": ["AXIS_TERRAIN_MANIFOLD_CORRECTION_HANDOFF.md", "CONSTRAINT_ON_DISTINGUISHABILITY_FULL_MATH.md"],
    },
    "axis6": {
        "status": "overlay_solid_in_docs_and_specs",
        "role": "action orientation; up vs down and left/right multiplication style; operators get signed here",
        "current_evidence": [
            "AXIS_TERRAIN_MANIFOLD_CORRECTION_HANDOFF.md",
            "AXIS_AND_ENTROPY_REFERENCE.md token partition",
            "canonical_qit_engine_specs.py axis6 fields",
        ],
    },
}

CORE_MANIFOLD_RECEIPTS = {
    "nested_geometry_tower_dependency_order_probe",
    "integrated_nested_geometric_constraint_manifold_dynamic_tensor_network_probe",
    "thirteen_layer_active_nested_manifold_mps_special_holonomy_deep_graveyard_dynamic_tensor_network_probe",
    "constraint_manifold_multitool_entropy_geometry_carrier_integration_probe",
    "full_thirteen_layer_active_g_structure_both_chiral_source_native_composition_probe",
    "integrated_constraint_manifold_suite_fresh_rerun_probe",
}

MANIFOLD_RE = re.compile(
    r"manifold|thirteen[_ -]?layer|13[_ -]?layer|nested[_ -]?geometry|"
    r"g[_ -]?structure|special[_ -]?holonomy|hopf|weyl|chirality|"
    r"clifford|toponetx|xgi|simplicial|hypergraph|constraint[_ -]?complex"
)
PEPS_RE = re.compile(r"\bpeps3d\b|\bpeps\b|\bmps\b|tensor[_ -]?network|quimb")
AXIS0_RE = re.compile(r"axis0|axis_0|fep_gradient|path_entropy|holographic_boundary|plural_candidate")
BASIN_RE = re.compile(r"attractor|basin|dt018|dt_tuning|basin_radius|convergen|anti_basin")
LIRPA_LEWM_RE = re.compile(r"auto[_-]?lirpa|lirpa|lewm|le-wm")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def all_pass_status(data: dict[str, Any]) -> tuple[bool | None, str]:
    for path in (
        ("all_pass",),
        ("summary", "all_pass"),
        ("summary", "all_passed"),
        ("positive", "all_pass"),
    ):
        cur: Any = data
        for key in path:
            if not isinstance(cur, dict) or key not in cur:
                cur = None
                break
            cur = cur[key]
        if isinstance(cur, bool):
            return cur, ".".join(path)
    if data.get("classification") == "formal_scout":
        return legacy_sections_all_pass(data), "derived_formal_scout_sections"
    return None, "missing"


def all_pass(data: dict[str, Any]) -> bool | None:
    return all_pass_status(data)[0]


def load_bearing_tools(data: dict[str, Any]) -> list[str]:
    depth = data.get("TOOL_INTEGRATION_DEPTH") or data.get("tool_integration_depth") or {}
    if isinstance(depth, dict):
        tools = [
            str(tool)
            for tool, value in depth.items()
            if str(value).replace("-", "_").lower() == "load_bearing"
        ]
        if tools:
            return sorted(tools)
    manifest = data.get("TOOL_MANIFEST") or data.get("tool_manifest") or {}
    if isinstance(manifest, dict):
        tools = []
        for tool, entry in manifest.items():
            if isinstance(entry, dict) and entry.get("used") is True:
                tools.append(str(tool))
        return sorted(tools)
    return []


def supportive_tools(data: dict[str, Any]) -> list[str]:
    depth = data.get("TOOL_INTEGRATION_DEPTH") or data.get("tool_integration_depth") or {}
    if not isinstance(depth, dict):
        return []
    return sorted(
        str(tool)
        for tool, value in depth.items()
        if str(value).replace("-", "_").lower() == "supportive"
    )


def short(value: Any, limit: int = 220) -> str | None:
    if value is None:
        return None
    text = str(value).replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def compact_summary(summary: Any) -> dict[str, Any]:
    if not isinstance(summary, dict):
        return {}
    keep = {}
    for key, value in summary.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            keep[key] = value
    return keep


def positive_keys(data: dict[str, Any]) -> list[str]:
    positive = data.get("positive") or data.get("positive_predicates") or {}
    if isinstance(positive, dict):
        return sorted(positive.keys())
    return []


def compact_layers(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict):
            name = item.get("name") or item.get("layer") or item.get("id")
            out.append(str(name) if name is not None else short(item, 120) or "")
        else:
            out.append(str(item))
    return out


def blocker_names(data: dict[str, Any]) -> list[str]:
    blockers = data.get("blockers")
    if isinstance(blockers, list):
        return [short(item, 120) or "" for item in blockers]
    if isinstance(blockers, dict):
        return sorted(blockers.keys())
    return []


def maturity_all_pass(data: dict[str, Any]) -> bool:
    return data.get("promotion_allowed") is True and all_pass(data) is True


def width_metadata(data: dict[str, Any]) -> dict[str, Any]:
    positive = data.get("positive") if isinstance(data.get("positive"), dict) else {}
    policy = positive.get("minimum_width_policy_is_explicit")
    if isinstance(policy, dict) and isinstance(policy.get("minimum_nonclassical_width"), int):
        role = str(policy.get("minimum_width_role") or policy.get("width_role") or "maturity_gate")
        eligible = policy.get("pass") is True and role != "calibration_only" and maturity_all_pass(data)
        return {
            "minimum_width_qubits": policy["minimum_nonclassical_width"],
            "width_role": role,
            "maturity_eligible": eligible,
        }

    width_entries: list[dict[str, Any]] = []
    for check in positive.values():
        if not isinstance(check, dict):
            continue
        width = check.get("minimum_width_qubits")
        if not isinstance(width, int):
            width = check.get("n_qubits")
        if not isinstance(width, int):
            continue
        role = str(check.get("minimum_width_role") or check.get("width_role") or "")
        width_entries.append(
            {
                "width": width,
                "role": role,
                "pass": check.get("pass") is True,
            }
        )

    subminimum = [entry for entry in width_entries if entry["width"] < 8]
    if subminimum:
        first = sorted(subminimum, key=lambda entry: entry["width"])[0]
        return {
            "minimum_width_qubits": first["width"],
            "width_role": first["role"] or "subminimum_unlabeled",
            "maturity_eligible": False,
        }

    eligible = [entry for entry in width_entries if entry["width"] >= 8 and entry["pass"]]
    if eligible:
        first = sorted(eligible, key=lambda entry: entry["width"])[0]
        return {
            "minimum_width_qubits": first["width"],
            "width_role": first["role"] or "maturity_gate",
            "maturity_eligible": maturity_all_pass(data),
        }

    for entry in width_entries:
        width = entry["width"]
        role = entry["role"]
        if width < 8:
            role = role or "subminimum_unlabeled"
            return {
                "minimum_width_qubits": width,
                "width_role": role,
                "maturity_eligible": False,
            }
        return {
            "minimum_width_qubits": width,
            "width_role": role or "maturity_gate",
            "maturity_eligible": entry["pass"] is True and maturity_all_pass(data),
        }

    if isinstance(data.get("minimum_width_qubits"), int):
        role = str(data.get("minimum_width_role") or data.get("width_role") or "declared")
        return {
            "minimum_width_qubits": data["minimum_width_qubits"],
            "width_role": role,
            "maturity_eligible": role != "calibration_only" and maturity_all_pass(data),
        }

    return {
        "minimum_width_qubits": None,
        "width_role": "not_declared",
        "maturity_eligible": None,
    }


def result_stem(path: Path) -> str:
    stem = path.stem
    return stem.removesuffix("_results")


def source_for_result(stem: str) -> Path:
    return FORMAL / f"sim_{stem}.py"


def infer_tags(text: str, stem: str) -> list[str]:
    tags = []
    if MANIFOLD_RE.search(text) or stem in CORE_MANIFOLD_RECEIPTS:
        tags.append("geometric_constraint_manifold")
    if PEPS_RE.search(text):
        tags.append("peps_peps3d_mps_carrier")
    if AXIS0_RE.search(text):
        tags.append("axis0")
    if BASIN_RE.search(text):
        tags.append("attractor_basin")
    if LIRPA_LEWM_RE.search(text):
        tags.append("auto_lirpa_lewm")
    return tags


def build_result_rows(role_by_result: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(RESULTS.glob("*_results.json")):
        data = load_json(path)
        if not isinstance(data, dict):
            continue
        stem = result_stem(path)
        source = source_for_result(stem)
        layers = compact_layers(data.get("candidate_layers") or data.get("layers") or [])
        lb_tools = load_bearing_tools(data)
        sup_tools = supportive_tools(data)
        subject_text_bits = [
            stem,
            data.get("name", ""),
            " ".join(layers),
            " ".join(lb_tools),
            " ".join(positive_keys(data)),
        ]
        text_bits = subject_text_bits + [data.get("claim_ceiling", "")]
        subject_text = " ".join(str(bit) for bit in subject_text_bits).lower()
        text = " ".join(str(bit) for bit in text_bits).lower()
        subject_tags = infer_tags(subject_text, stem)
        tags = infer_tags(text, stem)
        role_row = role_by_result.get(f"results/{path.name}", {})
        width = width_metadata(data)
        pass_value, pass_source = all_pass_status(data)
        rows.append(
            {
                "name": data.get("name") or stem,
                "stem": stem,
                "result_path": rel(path),
                "source_path": rel(source) if source.exists() else None,
                "source_exists": source.exists(),
                "classification": data.get("classification"),
                "promotion_allowed": data.get("promotion_allowed"),
                "raw_all_pass": data.get("all_pass"),
                "all_pass": pass_value,
                "derived_all_pass": pass_value,
                "all_pass_source": pass_source,
                "minimum_width_qubits": width["minimum_width_qubits"],
                "width_role": width["width_role"],
                "maturity_eligible": width["maturity_eligible"],
                "summary": compact_summary(data.get("summary")),
                "candidate_layer_count": len(layers),
                "candidate_layers": layers,
                "load_bearing_tools": lb_tools,
                "supportive_tools": sup_tools,
                "tool_role_status": role_row.get("tool_role_status"),
                "nonclassical_basin_claim_allowed": role_row.get("nonclassical_basin_claim_allowed"),
                "blocker_count": len(blocker_names(data)),
                "blockers": blocker_names(data),
                "nearby_variants": data.get("nearby_variants"),
                "positive_keys": positive_keys(data),
                "claim_ceiling": short(data.get("claim_ceiling"), 360),
                "tags": tags,
                "subject_tags": subject_tags,
            }
        )
    return rows


def build_tool_gate_summary() -> dict[str, Any]:
    data = load_json(TOOL_ROLE_GATE)
    if not isinstance(data, dict):
        return {"present": False}
    rows = data.get("tool_role_rows")
    rows = rows if isinstance(rows, list) else []
    status_counts = Counter(str(row.get("tool_role_status")) for row in rows)
    candidates = [row for row in rows if row.get("tool_role_status") == "tool_role_candidate"]
    blocked = [row for row in rows if row.get("nonclassical_basin_claim_allowed") is not True]
    by_tool: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        status = str(row.get("tool_role_status"))
        for tool in row.get("load_bearing_tools", []) or []:
            by_tool[str(tool)][status] += 1
    return {
        "present": True,
        "path": rel(TOOL_ROLE_GATE),
        "all_pass": data.get("all_pass"),
        "positive": data.get("positive"),
        "status_counts": dict(status_counts),
        "candidate_count": len(candidates),
        "blocked_count": len(blocked),
        "candidates": [
            {
                "name": row.get("name"),
                "result_path": row.get("result_path"),
                "load_bearing_tools": row.get("load_bearing_tools", []),
                "nonclassical_basin_claim_allowed": row.get("nonclassical_basin_claim_allowed"),
            }
            for row in candidates
        ],
        "by_tool": {tool: dict(counts) for tool, counts in sorted(by_tool.items())},
        "role_by_result": {str(row.get("result_path")): row for row in rows if row.get("result_path")},
    }


def build_numpy_quarantine_summary() -> dict[str, Any]:
    data = load_json(NUMPY_QUARANTINE)
    if not isinstance(data, dict):
        return {"present": False}
    positive = data.get("positive") if isinstance(data.get("positive"), dict) else {}
    source_scan = positive.get("formal_scout_source_scan_completed", {})
    result_scan = positive.get("result_receipt_scan_completed", {})
    hard_source = positive.get("source_native_nonclassical_numpy_is_quarantined", {})
    hard_result = positive.get("receipt_level_numpy_load_bearing_without_pytorch_is_quarantined", {})
    return {
        "present": True,
        "path": rel(NUMPY_QUARANTINE),
        "all_pass": data.get("all_pass"),
        "source_scan": source_scan,
        "result_scan": result_scan,
        "hard_quarantine_source_paths": hard_source.get("hard_quarantine_paths", []),
        "hard_quarantine_result_paths": hard_result.get("hard_quarantine_result_paths", []),
    }


def build_axis0_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    path = RESULTS / "axis0_plural_candidate_multicarrier_drive_controls_probe_results.json"
    axis0_rows = [r for r in rows if "axis0" in r["tags"]]
    axis0_subject_rows = [r for r in rows if "axis0" in r["subject_tags"]]
    data = load_json(path)
    if not isinstance(data, dict):
        return {
            "present": False,
            "axis0_rows": axis0_rows,
            "axis0_row_count": len(axis0_rows),
            "axis0_subject_rows": axis0_subject_rows,
            "axis0_subject_row_count": len(axis0_subject_rows),
        }
    positive = data.get("positive") if isinstance(data.get("positive"), dict) else {}
    candidate_report = (
        positive.get("candidates_are_admitted_or_explicitly_blocked", {})
        .get("candidate_report", {})
    )
    scalar_blocker = (
        positive.get("control_family_correlation_report_is_recorded", {})
        .get("control_family_correlation_report", {})
        .get("scalar_weighted_drive_blocker", {})
    )
    carrier_checks = (
        positive.get("plural_candidate_controls_separate_on_mps_peps_peps3d", {})
        .get("checks", {})
    )
    return {
        "present": True,
        "path": rel(path),
        "all_pass": all_pass(data),
        "admitted_candidate_names": candidate_report.get("admitted_candidate_names", []),
        "blocked_candidate_names": candidate_report.get("blocked_candidate_names", []),
        "contribution_rank": candidate_report.get("contribution_rank"),
        "dominance_report": candidate_report.get("dominance_report", {}),
        "scalar_weighted_drive_blocker": scalar_blocker,
        "carrier_checks": carrier_checks,
        "axis0_rows": axis0_rows,
        "axis0_row_count": len(axis0_rows),
        "axis0_subject_rows": axis0_subject_rows,
        "axis0_subject_row_count": len(axis0_subject_rows),
        "axis0_tag_note": "axis0_rows is broad mention-tagging and can include negative claim-ceiling boilerplate; axis0_subject_rows excludes claim_ceiling text.",
    }


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def build_process_lines() -> dict[str, Any]:
    grok_counts = Counter()
    if GROK_SIM.exists():
        for item in GROK_SIM.rglob("*"):
            if item.is_file():
                try:
                    first = item.relative_to(GROK_SIM).parts[0]
                except ValueError:
                    first = "."
                grok_counts[first] += 1
    tmp_counts = Counter()
    if TMP_ENGINE.exists():
        for item in TMP_ENGINE.rglob("*"):
            if item.is_file():
                tmp_counts[item.suffix or "<none>"] += 1
    return {
        "formal_scout_index_surface": {
            "source_dir": rel(FORMAL),
            "source_count": len(list(FORMAL.glob("sim_*.py"))),
            "result_dir": rel(RESULTS),
            "result_count": len(list(RESULTS.glob("*_results.json"))),
            "provider_receipt_count": len(list((FORMAL / "provider_receipts").glob("*.json"))),
        },
        "grok_sim_proposal_process_line": {
            "path": rel(GROK_SIM),
            "exists": GROK_SIM.exists(),
            "file_count": count_files(GROK_SIM),
            "top_level_counts": dict(sorted(grok_counts.items())),
            "role": "proposal and failure-pattern mining until translated into formal scouts",
        },
        "lego_results": {
            "path": rel(LEGOS_RESULTS),
            "exists": LEGOS_RESULTS.exists(),
            "file_count": count_files(LEGOS_RESULTS),
        },
        "tmp_engine_v2_scratch": {
            "path": str(TMP_ENGINE),
            "exists": TMP_ENGINE.exists(),
            "file_count": count_files(TMP_ENGINE),
            "suffix_counts": dict(sorted(tmp_counts.items())),
            "role": "scratch/council/provider routing estate, not canonical sim evidence",
        },
    }


def build_external_repo_summary() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, path in EXTERNAL_REPOS.items():
        out[name] = {
            "path": str(path),
            "exists": path.exists(),
            "file_count": count_files(path) if path.exists() else 0,
        }
    return out


def build_readiness_summary() -> dict[str, Any]:
    data = load_json(READINESS_INDEX)
    if not isinstance(data, dict):
        return {"present": False}
    return {
        "present": True,
        "path": rel(READINESS_INDEX),
        "summary": data.get("summary", {}),
        "failures": data.get("failures", data.get("failed", [])),
    }


def rows_with_tag(rows: list[dict[str, Any]], tag: str) -> list[dict[str, Any]]:
    return [row for row in rows if tag in row["tags"]]


def prioritized_rows(rows: list[dict[str, Any]], names: set[str] | None = None) -> list[dict[str, Any]]:
    names = names or set()
    return sorted(
        rows,
        key=lambda row: (
            0 if row["stem"] in names or row["name"] in names else 1,
            0 if row.get("all_pass") is True else 1,
            row["stem"],
        ),
    )


def compact_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": row["name"],
        "stem": row["stem"],
        "result_path": row["result_path"],
        "classification": row["classification"],
        "promotion_allowed": row["promotion_allowed"],
        "raw_all_pass": row["raw_all_pass"],
        "all_pass": row["all_pass"],
        "derived_all_pass": row["derived_all_pass"],
        "all_pass_source": row["all_pass_source"],
        "minimum_width_qubits": row["minimum_width_qubits"],
        "width_role": row["width_role"],
        "maturity_eligible": row["maturity_eligible"],
        "candidate_layer_count": row["candidate_layer_count"],
        "layers": row["candidate_layer_count"],
        "load_bearing_tools": row["load_bearing_tools"],
        "tool_role_status": row["tool_role_status"],
        "nonclassical_basin_claim_allowed": row["nonclassical_basin_claim_allowed"],
        "tags": row.get("tags", []),
        "subject_tags": row.get("subject_tags", []),
        "summary": row["summary"],
        "blockers": row["blockers"],
    }


def markdown_table(rows: list[dict[str, Any]], limit: int = 14) -> str:
    if not rows:
        return "_None found._\n"
    lines = [
        "| receipt | pass | pass source | min width | width role | maturity eligible | layers | tool gate | load-bearing tools | summary |",
        "|---|---:|---|---:|---|---:|---:|---|---|---|",
    ]
    for row in rows[:limit]:
        summary = row.get("summary") or {}
        summary_bits = []
        for key in (
            "all_pass",
            "microstep_count",
            "layer_count",
            "tool_count",
            "load_bearing_count",
            "load_bearing_tool_count",
            "cross_track_divergence",
            "max_coherent_information",
            "min_conditional_entropy",
            "validator_fail_count",
            "validator_red_rows_classified",
            "cleanup_authorized",
        ):
            if key in summary:
                summary_bits.append(f"{key}={summary[key]}")
        if row["stem"] == "formal_scout_readiness_debt_classification_probe":
            summary_bits.append("classifier_debt_only_validator_red_rows_remain_preserved")
        lines.append(
            "| `{}` | {} | `{}` | {} | {} | {} | {} | {} | {} | {} |".format(
                row["stem"],
                row["all_pass"],
                row.get("all_pass_source"),
                row.get("minimum_width_qubits"),
                row.get("width_role"),
                row.get("maturity_eligible"),
                row["candidate_layer_count"],
                row.get("tool_role_status") or "",
                ", ".join(row["load_bearing_tools"][:8]),
                "; ".join(summary_bits[:5]),
            )
        )
    if len(rows) > limit:
        lines.append(f"\n_{len(rows) - limit} more rows in `{rel(OUT_JSON)}`._")
    return "\n".join(lines) + "\n"


def build_markdown(index: dict[str, Any]) -> str:
    process = index["sim_process_lines"]
    tool_gate = index["tool_gate_summary"]
    numpy_gate = index["numpy_quarantine_summary"]
    axis0 = index["axis0_summary"]
    readiness = index["readiness_summary"]
    manifold_rows = prioritized_rows(index["geometric_constraint_manifold_rows"], CORE_MANIFOLD_RECEIPTS)
    peps_rows = prioritized_rows(index["peps_peps3d_rows"])
    basin_rows = prioritized_rows(index["attractor_basin_rows"])
    lirpa_rows = prioritized_rows(index["auto_lirpa_lewm_rows"])
    integrated_candidate_rows = [
        row
        for row in index["geometric_constraint_manifold_rows"]
        if row.get("all_pass") is True
        and row.get("promotion_allowed") is False
        and row.get("candidate_layer_count") == 13
        and row.get("summary", {}).get("microstep_count") == 64
    ]
    integrated_candidate_count = len(integrated_candidate_rows)
    readiness_summary = readiness.get("summary", {}) if isinstance(readiness, dict) else {}
    validator_red_count = readiness_summary.get("validator_fail_count", "unknown")
    lines = [
        "# Sim Estate Integration Index",
        "",
        f"Generated: `{index['generated_at']}`",
        "",
        "## Root Object",
        "",
        "The current working root surface is the geometric constraint manifold candidate: 13 simultaneous constraint shells, not axis labels and not only the Weyl/chirality layer. PEPS/PEPS3D, Axis0, attractor-basin receipts, provider outputs, and graph/proof tools are indexed here only as evidence surfaces over that candidate, not as final manifold promotion.",
        "",
        "## Axis Overlay Map",
        "",
        "| axis | status | role | blockers |",
        "|---|---|---|---|",
        *[
            "| `{}` | `{}` | {} | {} |".format(
                axis,
                row.get("status"),
                row.get("role"),
                "; ".join(row.get("blockers", [])) if row.get("blockers") else "",
            )
            for axis, row in index["axis_overlay_map"].items()
        ],
        "",
        "## Current Verdict",
        "",
        f"- The active evidence estate contains {integrated_candidate_count} 13-layer integrated manifold candidates with pass evidence, `promotion_allowed=false`, and 64 microsteps.",
        "- The strongest manifold receipts are still formal scouts. They do not promote a final manifold, final G-structure, physics, bridge, axis, engine, or target-system claim.",
        f"- Tool-role gate: {tool_gate.get('candidate_count')} candidate surfaces and {tool_gate.get('blocked_count')} blocked result-not-all-pass surfaces from {tool_gate.get('positive', {}).get('result_surface_scanned', {}).get('nonclassical_surface_count')} scanned nonclassical/source-native result surfaces.",
        f"- NumPy quarantine: source scan sees {numpy_gate.get('source_scan', {}).get('numpy_tainted_file_count')} NumPy-pattern files total, hard-quarantines {numpy_gate.get('source_scan', {}).get('hard_quarantine_count')} files, marks {numpy_gate.get('source_scan', {}).get('review_required_count')} review-required surfaces, preserves {numpy_gate.get('source_scan', {}).get('reviewed_numpy_boundary_count')} reviewed NumPy-bearing boundary files as nonclassical-claim blocked, and keeps {numpy_gate.get('source_scan', {}).get('legacy_or_baseline_boundary_count')} quarantine-scanner self-hit / legacy-baseline boundary file separate; receipt scan hard-quarantines {numpy_gate.get('result_scan', {}).get('current_receipt_quarantine_count')} result receipts.",
        f"- Axis0 is partially repaired but not solid: admitted {axis0.get('admitted_candidate_names', [])}; blocked {axis0.get('blocked_candidate_names', [])}; scalar projection blocker admitted={axis0.get('scalar_weighted_drive_blocker', {}).get('admitted')}.",
        f"- Axis0 row counts are split: broad mention-tagged rows `{axis0.get('axis0_row_count')}`, subject-tagged rows `{axis0.get('axis0_subject_row_count')}`. Broad rows may include negative claim-ceiling boilerplate and should not be treated as subject evidence.",
        f"- Row summaries may preserve row-local historical flags such as `cleanup_authorized=False`; these are not the D86 final closeout state. Conversely, D86 closeout does not override the current readiness tuple or the {validator_red_count} validator-red rows preserved as nonpromotional evidence.",
        "",
        "## Sim Process Lines",
        "",
        f"- Formal-scout source/result estate: `{process['formal_scout_index_surface']['source_dir']}` has {process['formal_scout_index_surface']['source_count']} sources and {process['formal_scout_index_surface']['result_count']} result receipts.",
        f"- Independent `grok_sim` process line: `{process['grok_sim_proposal_process_line']['path']}` has {process['grok_sim_proposal_process_line']['file_count']} files; role is proposal/failure mining until translated.",
        f"- Scratch/council estate: `{process['tmp_engine_v2_scratch']['path']}` has {process['tmp_engine_v2_scratch']['file_count']} files; not canonical evidence.",
        f"- Lego result estate: `{process['lego_results']['path']}` has {process['lego_results']['file_count']} files.",
        "",
        "## Geometric Constraint Manifold Receipts",
        "",
        markdown_table(manifold_rows, limit=18),
        "## PEPS / PEPS3D / MPS Carrier-Name Receipts, Nonpromotional",
        "",
        "Rows here are indexed because their names or summaries mention these carriers. A passing row is still formal-scout evidence unless a separate promotion gate says otherwise.",
        "",
        markdown_table(peps_rows, limit=18),
        "## Tool Integration Gate",
        "",
        f"- Status counts: `{tool_gate.get('status_counts')}`",
        f"- Candidate rows: `{', '.join(row['name'] for row in tool_gate.get('candidates', []))}`",
        "",
        "## auto_LiRPA / le-wm Surface",
        "",
        f"- External repos: `{index['external_repos']}`",
        "",
        markdown_table(lirpa_rows, limit=14),
        "## Axis0 Surface",
        "",
        f"- Receipt: `{axis0.get('path')}`",
        f"- Admitted candidates: `{axis0.get('admitted_candidate_names')}`",
        f"- Blocked candidates: `{axis0.get('blocked_candidate_names')}`",
        f"- Contribution rank: `{axis0.get('contribution_rank')}`",
        f"- Scalar projection blocker: `{axis0.get('scalar_weighted_drive_blocker')}`",
        f"- Broad mention-tagged row count: `{axis0.get('axis0_row_count')}`",
        f"- Subject-tagged row count: `{axis0.get('axis0_subject_row_count')}`",
        f"- Tag note: {axis0.get('axis0_tag_note')}",
        "",
        "## Attractor Basin Surface",
        "",
        markdown_table(basin_rows, limit=16),
        "## Readiness / Red Basics",
        "",
        f"- Readiness summary: `{readiness.get('summary')}`",
        f"- Readiness red split: formal-scout validator-failed rows `{readiness.get('summary', {}).get('validator_fail_count')}`; preserved red rows `{readiness.get('summary', {}).get('preserved_validator_fail_count')}`; actionable red rows `{readiness.get('summary', {}).get('actionable_validator_fail_count')}`.",
        "- Basic open repairs: keep the manifold candidate bounded; do not count numpy-tainted source-native rows as basin evidence; keep strict-live provider provenance debt separate from normal schema validation. The current validator-red formal-scout rows are preserved negative/quarantine/overclaim-boundary evidence, not readiness-repair debt unless a revised-design rerun is explicitly requested.",
        "",
        "## Machine Index",
        "",
        f"Full row data: `{rel(OUT_JSON)}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    tool_gate = build_tool_gate_summary()
    role_by_result = tool_gate.pop("role_by_result", {})
    rows = build_result_rows(role_by_result)
    pass_source_counts = Counter(str(row.get("all_pass_source")) for row in rows)
    axis0_summary = build_axis0_summary(rows)
    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifold_layers": MANIFOLD_LAYERS,
        "axis_overlay_map": AXIS_OVERLAY_MAP,
        "sim_process_lines": build_process_lines(),
        "tool_gate_summary": tool_gate,
        "numpy_quarantine_summary": build_numpy_quarantine_summary(),
        "readiness_summary": build_readiness_summary(),
        "tool_function_matrix_present": TOOL_FUNCTION_MATRIX.exists(),
        "external_repos": build_external_repo_summary(),
        "result_row_count": len(rows),
        "all_pass_source_counts": dict(pass_source_counts),
        "geometric_constraint_manifold_rows": [compact_row(r) for r in rows_with_tag(rows, "geometric_constraint_manifold")],
        "peps_peps3d_rows": [compact_row(r) for r in rows_with_tag(rows, "peps_peps3d_mps_carrier")],
        "axis0_summary": axis0_summary,
        "axis0_rows": [compact_row(r) for r in axis0_summary.get("axis0_rows", [])],
        "axis0_subject_rows": [compact_row(r) for r in axis0_summary.get("axis0_subject_rows", [])],
        "attractor_basin_rows": [compact_row(r) for r in rows_with_tag(rows, "attractor_basin")],
        "auto_lirpa_lewm_rows": [compact_row(r) for r in rows_with_tag(rows, "auto_lirpa_lewm")],
        "all_tagged_rows": [compact_row(r) for r in rows if r["tags"]],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(build_markdown(index), encoding="utf-8")
    print(f"Wrote {rel(OUT_JSON)}")
    print(f"Wrote {rel(OUT_MD)}")
    print(
        "Rows: manifold={manifold} peps={peps} axis0={axis0} axis0_subject={axis0_subject} basin={basin} lirpa_lewm={lirpa}".format(
            manifold=len(index["geometric_constraint_manifold_rows"]),
            peps=len(index["peps_peps3d_rows"]),
            axis0=len(index["axis0_rows"]),
            axis0_subject=len(index["axis0_subject_rows"]),
            basin=len(index["attractor_basin_rows"]),
            lirpa=len(index["auto_lirpa_lewm_rows"]),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
