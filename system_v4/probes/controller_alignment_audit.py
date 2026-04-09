#!/usr/bin/env python3
"""
Controller alignment audit.

Builds one machine-readable report that compares:
  - execution authority (Makefile / iMessage bot interpreter path)
  - dependency floors from requirements-sim-stack.txt
  - live package truth under the current interpreter
  - stale controller-doc markers
  - Phase 7 C2 result semantics vs the dedicated C2 remaining pass

This is intentionally stdlib-only so it can run in the active env without
bringing in more dependencies.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
import argparse
from datetime import datetime, UTC
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version as pkg_version
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "controller_alignment_audit_results.json"
TRUTH_AUDIT_PATH = RESULTS_DIR / "probe_truth_audit_results.json"
DOC_DRIFT_INVENTORY_PATH = RESULTS_DIR / "controller_doc_drift_inventory.json"
RUNTIME_CACHE_ROOT = Path(
    os.environ.get("CODEX_RUNTIME_CACHE_ROOT", "/tmp/codex-ratchet-controller-audit")
)
for cache_dir in (
    RUNTIME_CACHE_ROOT,
    RUNTIME_CACHE_ROOT / "matplotlib",
    RUNTIME_CACHE_ROOT / "numba",
    RUNTIME_CACHE_ROOT / "xdg",
):
    cache_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME_CACHE_ROOT / "matplotlib"))
os.environ.setdefault("NUMBA_CACHE_DIR", str(RUNTIME_CACHE_ROOT / "numba"))
os.environ.setdefault("XDG_CACHE_HOME", str(RUNTIME_CACHE_ROOT / "xdg"))

MAKEFILE_PATH = PROJECT_DIR / "Makefile"
BOT_PATH = PROJECT_DIR / "imessage_bot.py"
CLAUDE_PATH = PROJECT_DIR / "CLAUDE.md"
TOOLING_STATUS_PATH = PROJECT_DIR / "new docs" / "TOOLING_STATUS.md"
BUILD_PLAN_PATH = PROJECT_DIR / "new docs" / "PYTORCH_RATCHET_BUILD_PLAN.md"
CONTROLLER_PATH = PROJECT_DIR / "new docs" / "LLM_CONTROLLER_CONTRACT.md"
MIGRATION_PATH = PROJECT_DIR / "new docs" / "MIGRATION_REGISTRY.md"
REQ_SIM_STACK_PATH = PROJECT_DIR / "requirements-sim-stack.txt"
PHASE7_SOURCE_PATH = SCRIPT_DIR / "sim_phase7_baseline_validation.py"
PHASE7_RESULT_PATH = RESULTS_DIR / "phase7_baseline_validation_results.json"
C2_REMAINING_PATH = RESULTS_DIR / "c2_topology_remaining_results.json"
LIVE_ANCHOR_SPINE_PATH = RESULTS_DIR / "live_anchor_spine.json"
XGI_AUTOGRAD_SOURCE_PATH = SCRIPT_DIR / "sim_xgi_torch_autograd.py"
XGI_AUTOGRAD_RESULT_PATH = RESULTS_DIR / "xgi_torch_autograd_results.json"
XGI_ASCENT_SOURCE_PATH = SCRIPT_DIR / "sim_xgi_gradient_ascent.py"
XGI_ASCENT_RESULT_PATH = RESULTS_DIR / "xgi_gradient_ascent_results.json"


PACKAGE_MAP = {
    "torch": ("torch", "torch"),
    "torch-geometric": ("torch_geometric", "torch-geometric"),
    "z3-solver": ("z3", "z3-solver"),
    "cvc5": ("cvc5", "cvc5"),
    "sympy": ("sympy", "sympy"),
    "clifford": ("clifford", "clifford"),
    "geomstats": ("geomstats", "geomstats"),
    "e3nn": ("e3nn", "e3nn"),
    "rustworkx": ("rustworkx", "rustworkx"),
    "xgi": ("xgi", "xgi"),
    "TopoNetX": ("toponetx", "TopoNetX"),
    "gudhi": ("gudhi", "gudhi"),
    "pandas": ("pandas", "pandas"),
    "networkx": ("networkx", "networkx"),
}

TRUSTED_SPINE = {
    "boundary": [
        "bridge_extended_proofs_results.json",
        "bridge_z3_kernel_ordering_results.json",
    ],
    "lego": [
        "foundation_channel_constraints_hardway_results.json",
        "foundation_hopf_torus_geomstats_clifford_results.json",
        "bridge_to_rhoab_construction_results.json",
        "torch_hopf_connection_results.json",
    ],
    "coupling": [
        "integrated_dependency_chain_results.json",
        "layer_coupling_matrix_v3_results.json",
        "xgi_indirect_pathway_results.json",
    ],
    "coexistence": [
        "weyl_nested_shell_results.json",
        "xgi_l7_marginal_results.json",
        "layer_stacking_nonprefix_results.json",
    ],
    "topology": [
        "xgi_shell_hypergraph_results.json",
        "toponetx_hopf_crosscheck_results.json",
        "toponetx_state_class_binding_results.json",
        "gudhi_cascade_persistence_results.json",
        "gudhi_wasserstein_significance_results.json",
        "c2_topology_remaining_results.json",
    ],
    "assembly": [
        "rustworkx_bridge_dag_results.json",
        "rustworkx_dag_reduction_results.json",
        "xgi_bridge_hyperedges_results.json",
        "pyg_dynamic_edge_werner_results.json",
        "torch_graph_integrated_pipeline_results.json",
    ],
}

EXPLORATORY_BRANCH = [
    "xgi_torch_autograd_results.json",
    "xgi_gradient_ascent_results.json",
    "rustworkx_3qubit_dag_results.json",
]

TOOL_FORCING_TARGETS = {
    "pyg": [
        "pyg_dynamic_edge_werner_results.json",
        "foundation_equivariant_graph_backprop_results.json",
        "torch_gnn_axis0_seeded_results.json",
    ],
    "cvc5": [
        "bridge_phi0_proof_integration_results.json",
        "bridge_cvc5_crosscheck_results.json",
        "cvc5_shells_crosscheck_results.json",
    ],
    "e3nn": [
        "axis6_e3nn_fe_bridge_results.json",
        "e3nn_ic_invariance_results.json",
        "weyl_nested_shell_results.json",
    ],
    "toponetx": [
        "toponetx_bridge_seam_results.json",
        "toponetx_constraint_shells_results.json",
        "toponetx_state_class_binding_results.json",
    ],
    "xgi": [
        "xgi_shell_hypergraph_results.json",
        "xgi_bridge_hyperedges_results.json",
        "xgi_indirect_pathway_results.json",
    ],
}

TOOL_ORDER = [
    "pytorch",
    "pyg",
    "z3",
    "cvc5",
    "sympy",
    "clifford",
    "geomstats",
    "e3nn",
    "rustworkx",
    "xgi",
    "toponetx",
    "gudhi",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_python_from_makefile(text: str) -> str | None:
    match = re.search(r"^PYTHON\s*:=\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def parse_python_bin_from_bot(text: str) -> str | None:
    match = re.search(r'^PYTHON_BIN\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    return match.group(1) if match else None


def parse_requirement_floors(path: Path) -> dict[str, str]:
    floors: dict[str, str] = {}
    for raw_line in read_text(path).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or line.startswith("-r "):
            continue
        if ">=" in line:
            name, floor = line.split(">=", 1)
            floors[name.strip()] = floor.strip()
        else:
            floors[line] = ""
    return floors


def major_minor_patch_tuple(ver: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", ver)
    return tuple(int(n) for n in nums[:3])


def compare_floor(installed: str, floor: str) -> bool | None:
    if not installed or not floor:
        return None
    return major_minor_patch_tuple(installed) >= major_minor_patch_tuple(floor)


def package_status() -> dict[str, dict]:
    statuses: dict[str, dict] = {}
    for req_name, (import_name, dist_name) in PACKAGE_MAP.items():
        info = {
            "distribution": dist_name,
            "import_name": import_name,
            "installed_version": None,
            "import_ok": False,
            "import_error": None,
        }
        try:
            info["installed_version"] = pkg_version(dist_name)
        except PackageNotFoundError:
            info["installed_version"] = None
        try:
            import_module(import_name)
            info["import_ok"] = True
        except Exception as exc:  # noqa: BLE001
            info["import_error"] = f"{exc.__class__.__name__}: {exc}"
        statuses[req_name] = info
    return statuses


def collect_stale_doc_hits() -> list[dict]:
    hits: list[dict] = []
    checks = [
        (CLAUDE_PATH, r"24/28 not tested", "stale_c2_not_tested_claim"),
        (CONTROLLER_PATH, r"24/28 not tested", "stale_c2_not_tested_claim"),
        (MIGRATION_PATH, r"24/28 not tested", "stale_c2_not_tested_claim"),
        (BUILD_PLAN_PATH, r"24/28 not tested", "stale_c2_not_tested_claim"),
        (CLAUDE_PATH, r"/opt/homebrew/bin/python3", "stale_interpreter_claim"),
        (TOOLING_STATUS_PATH, r"/opt/homebrew/bin/python3", "stale_interpreter_claim"),
        (BUILD_PLAN_PATH, r"The PyTorch computational graph IS the ratchet\.", "strong_architectural_claim"),
    ]
    for path, pattern, kind in checks:
        if not path.exists():
            continue
        text = read_text(path)
        for match in re.finditer(pattern, text):
            line = text[: match.start()].count("\n") + 1
            hits.append({
                "file": str(path),
                "line": line,
                "kind": kind,
                "match": match.group(0),
            })
    return hits


def summarize_stale_doc_hits(hits: list[dict]) -> dict:
    by_kind: dict[str, int] = {}
    by_file: dict[str, int] = {}
    for hit in hits:
        kind = hit.get("kind")
        file_path = hit.get("file")
        if isinstance(kind, str):
            by_kind[kind] = by_kind.get(kind, 0) + 1
        if isinstance(file_path, str):
            by_file[file_path] = by_file.get(file_path, 0) + 1

    severity = "none"
    if hits:
        severity = "medium"
    if by_kind.get("strong_architectural_claim", 0) > 0:
        severity = "high"

    return {
        "count": len(hits),
        "by_kind": by_kind,
        "by_file": by_file,
        "markdown_edit_required_count": sum(
            1 for path in by_file if path.endswith(".md")
        ),
        "highest_severity": severity,
    }


def enrich_stale_doc_hits(
    hits: list[dict],
    *,
    sys_executable: str,
    makefile_python: str | None,
    bot_python: str | None,
    c2_crosscheck: dict,
    truth_audit: dict,
    code_process_green: bool,
) -> list[dict]:
    enriched: list[dict] = []
    phase7_summary = c2_crosscheck.get("phase7_summary", {})
    c2_remaining_counts = c2_crosscheck.get("c2_remaining_counts", {})
    mismatch_count = c2_crosscheck.get("mismatch_count")
    interpreter_truth = {
        "sys_executable": sys_executable,
        "makefile_python": makefile_python,
        "imessage_bot_python": bot_python,
        "makefile_and_bot_agree": makefile_python == bot_python,
    }
    for hit in hits:
        row = dict(hit)
        kind = row.get("kind")
        file_path = row.get("file")
        row["requires_markdown_edit"] = isinstance(file_path, str) and file_path.endswith(".md")

        if kind == "stale_c2_not_tested_claim":
            row["severity"] = "medium"
            row["current_truth"] = {
                "phase7_c2_summary": phase7_summary,
                "c2_remaining_counts": c2_remaining_counts,
                "mismatch_count": mismatch_count,
            }
            row["recommended_action"] = (
                "Replace the stale '24/28 not tested' claim with the current "
                "Phase7 C2 summary or remove the numeric claim entirely."
            )
            row["replacement_hint"] = (
                "Current Phase7 C2 summary: "
                f"{phase7_summary.get('non_null_count', '?')} non-null, "
                f"{phase7_summary.get('null_count', '?')} null, "
                f"{phase7_summary.get('not_tested', '?')} not tested, "
                f"total {phase7_summary.get('total', '?')}; "
                f"mismatch_count={mismatch_count}."
            )
        elif kind == "stale_interpreter_claim":
            row["severity"] = "medium"
            row["current_truth"] = interpreter_truth
            row["recommended_action"] = (
                "Replace the hardcoded interpreter path claim with the current "
                "authority surface, or reference Makefile/BOT authority instead "
                "of a literal path."
            )
            row["replacement_hint"] = (
                "Current interpreter authority: "
                f"sys_executable={sys_executable}, "
                f"makefile_python={makefile_python}, "
                f"imessage_bot_python={bot_python}, "
                f"makefile_and_bot_agree={makefile_python == bot_python}."
            )
        elif kind == "strong_architectural_claim":
            row["severity"] = "high"
            row["current_truth"] = {
                "code_process_green": code_process_green,
                "truth_audit_ok": truth_audit.get("ok"),
                "hard_finding_count": truth_audit.get("hard_finding_count"),
                "warning_finding_count": truth_audit.get("warning_finding_count"),
                "c2_mismatch_count": mismatch_count,
            }
            row["recommended_action"] = (
                "Downgrade this sentence to a scoped implementation direction or "
                "explicit hypothesis. The audits support process alignment, not "
                "an identity claim about the architecture."
            )
            row["replacement_hint"] = (
                "Prefer wording like 'the PyTorch computational graph is one "
                "execution carrier for the ratchet build' unless a stronger "
                "claim is explicitly proven."
            )
        else:
            row["severity"] = "medium"
            row["current_truth"] = {}
            row["recommended_action"] = "Review and update the stale claim."
            row["replacement_hint"] = None

        enriched.append(row)
    return enriched


def build_doc_drift_inventory(
    hits: list[dict],
    *,
    summary: dict,
    code_process_green: bool,
    docs_current: bool,
    controller_contract_current: bool,
) -> dict:
    by_severity: dict[str, int] = {}
    grouped_rows: dict[str, list[dict]] = {}
    for hit in hits:
        severity = hit.get("severity")
        if isinstance(severity, str):
            by_severity[severity] = by_severity.get(severity, 0) + 1
        file_path = hit.get("file")
        if isinstance(file_path, str):
            grouped_rows.setdefault(file_path, []).append(hit)

    return {
        "name": "controller_doc_drift_inventory",
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": {
            **summary,
            "by_severity": by_severity,
            "code_process_green": code_process_green,
            "docs_current": docs_current,
            "controller_contract_current": controller_contract_current,
        },
        "rows": hits,
        "by_file": grouped_rows,
    }


def get_phase7_source_flags() -> dict:
    text = read_text(PHASE7_SOURCE_PATH)
    return {
        "mentions_full_c2_coverage": "C1/C2/C3/C4 full coverage" in text,
        "uses_topology_subset_gate": "if fname in TOPOLOGY_FAMILIES:" in text,
        "still_has_not_tested_branch": '"NOT_TESTED"' in text and "not in topology subset" in text,
        "topology_family_count": _phase7_topology_family_count(text),
    }


def _phase7_topology_family_count(text: str) -> int | None:
    match = re.search(r"TOPOLOGY_FAMILIES\s*=\s*(\[[\s\S]*?\])\s*\n\s*\n", text)
    if not match:
        return None
    try:
        value = ast.literal_eval(match.group(1))
    except Exception:  # noqa: BLE001
        return None
    return len(value) if isinstance(value, list) else None


def normalize_c2_phase7(verdict: str) -> str:
    if verdict == "NON_NULL_topology":
        return "NON_NULL_topology"
    if verdict == "NULL_topology":
        return "NULL_topology"
    return verdict


def normalize_c2_remaining(verdict: str) -> str:
    if verdict == "LOAD_BEARING":
        return "NON_NULL_topology"
    if verdict == "TOPOLOGY_INDEPENDENT":
        return "NULL_topology"
    return verdict


def compare_c2_surfaces() -> dict:
    phase7 = read_json(PHASE7_RESULT_PATH)
    c2_remaining = read_json(C2_REMAINING_PATH)

    phase7_family = phase7.get("family_verdicts", {})
    phase7_family_norm = {k.lower(): v for k, v in phase7_family.items()}
    remaining_positive = c2_remaining.get("positive", {})

    mismatches = []
    compared = []
    for family, payload in sorted(remaining_positive.items()):
        p7 = normalize_c2_phase7(
            phase7_family_norm.get(family.lower(), {}).get("C2_graph_topology", "MISSING")
        )
        c2 = normalize_c2_remaining(payload.get("verdict", "MISSING"))
        compared.append({"family": family, "phase7": p7, "c2_remaining": c2})
        if p7 != c2:
            mismatches.append({"family": family, "phase7": p7, "c2_remaining": c2})

    summary = phase7.get("criterion_summary", {}).get("C2_graph_topology", {})
    return {
        "phase7_summary": summary,
        "c2_remaining_counts": {
            "load_bearing": sum(1 for p in remaining_positive.values() if p.get("verdict") == "LOAD_BEARING"),
            "topology_independent": sum(1 for p in remaining_positive.values() if p.get("verdict") == "TOPOLOGY_INDEPENDENT"),
        },
        "compared_families": len(compared),
        "mismatch_count": len(mismatches),
        "mismatches": mismatches,
        "sample": compared[:8],
    }


def summarize_result_file(path: Path) -> dict:
    info = {
        "file": path.name,
        "exists": path.exists(),
        "classification": None,
        "signal": None,
    }
    if not path.exists():
        return info

    data = read_json(path)
    info["classification"] = data.get("classification")

    if isinstance(data.get("summary"), dict):
        summary = data["summary"]
        for key in ("all_pass", "all_tests_passed", "passed", "pass", "tests_passed"):
            if key in summary:
                info["signal"] = {key: summary[key]}
                break

    if info["signal"] is None:
        for key in ("all_pass", "all_tests_passed", "promoted_final_winner", "promoted_winner"):
            if key in data:
                info["signal"] = {key: data[key]}
                break

    if info["signal"] is None and "classification_note" in data:
        info["signal"] = {"classification_note": data["classification_note"]}

    return info


def load_truth_audit_summary() -> dict:
    if not TRUTH_AUDIT_PATH.exists():
        return {
            "available": False,
            "ok": None,
            "hard_finding_count": None,
            "warning_finding_count": None,
            "blocked_results": {},
        }
    try:
        data = read_json(TRUTH_AUDIT_PATH)
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "ok": False,
            "read_error": f"{exc.__class__.__name__}: {exc}",
            "hard_finding_count": None,
            "warning_finding_count": None,
            "blocked_results": {},
        }

    blocked_results: dict[str, list[str]] = {}
    for finding in data.get("hard_findings", []):
        if not isinstance(finding, dict):
            continue
        result_json = finding.get("result_json")
        kind = finding.get("kind", "unknown")
        if isinstance(result_json, str) and result_json:
            blocked_results.setdefault(result_json, []).append(str(kind))
    return {
        "available": True,
        "ok": data.get("summary", {}).get("ok"),
        "hard_finding_count": data.get("summary", {}).get("hard_finding_count"),
        "warning_finding_count": data.get("summary", {}).get("warning_finding_count"),
        "blocked_results": blocked_results,
    }


def analyze_spine_risks(path: Path, truth_blockers: dict[str, list[str]] | None = None) -> list[str]:
    if not path.exists():
        return ["missing_result"]

    data = read_json(path)
    risks: list[str] = []
    classification = data.get("classification")
    note = str(data.get("classification_note", "")).lower()

    if classification not in (None, "canonical"):
        risks.append("non_canonical_classification")
    if classification == "exploratory_signal":
        risks.append("exploratory_classification")
    if "not full" in note or "not a full" in note:
        risks.append("scope_limited_by_note")
    if "not" in note and "closure" in note:
        risks.append("not_closure_grade")
    if "not" in note and "winner" in note:
        risks.append("no_final_winner")
    if classification is None:
        risks.append("missing_classification")

    raw = json.dumps(data)
    if re.search(r'"all_pass"\s*:\s*false', raw):
        risks.append("all_pass_false")
    if re.search(r'"all_tests_passed"\s*:\s*false', raw):
        risks.append("all_tests_passed_false")
    if re.search(r'"status"\s*:\s*"FAIL"', raw):
        risks.append("contains_fail_status")

    if truth_blockers:
        for kind in truth_blockers.get(path.name, []):
            risks.append(f"truth_audit_blocked:{kind}")

    return risks


def build_spine_report(live_anchor_spine: list[dict]) -> dict:
    by_stage = {stage: [] for stage in TRUSTED_SPINE}
    for row in live_anchor_spine:
        stage = row.get("stage")
        if stage not in by_stage:
            continue
        by_stage[stage].append({
            "file": row.get("result_json"),
            "exists": row.get("exists"),
            "classification": row.get("classification"),
            "signal": row.get("signal"),
        })
    return by_stage


def build_live_anchor_spine(truth_blockers: dict[str, list[str]] | None = None) -> list[dict]:
    rows = []
    for stage, names in TRUSTED_SPINE.items():
        for name in names:
            path = RESULTS_DIR / name
            summary = summarize_result_file(path)
            data = read_json(path) if path.exists() else {}
            tool_depth = data.get("tool_integration_depth", {})
            dominant_tools = sorted([k for k, v in tool_depth.items() if v == "load_bearing"])
            risks = analyze_spine_risks(path, truth_blockers)
            rows.append({
                "stage": stage,
                "result_json": name,
                "exists": summary.get("exists"),
                "classification": summary.get("classification"),
                "dominant_tools": dominant_tools,
                "signal": summary.get("signal"),
                "promotion_ready": len(risks) == 0,
                "blockers": risks,
                "last_verified": datetime.now(UTC).date().isoformat(),
            })
    return rows


def check_xgi_source_result_drift() -> list[dict]:
    checks = []

    autograd_source = read_text(XGI_AUTOGRAD_SOURCE_PATH)
    autograd_result = read_json(XGI_AUTOGRAD_RESULT_PATH)
    autograd_note = str(autograd_result.get("classification_note", ""))
    checks.append({
        "source": str(XGI_AUTOGRAD_SOURCE_PATH),
        "result": str(XGI_AUTOGRAD_RESULT_PATH),
        "kind": "source_expectation_vs_result",
        "source_mentions_expected_largest": "Expected:" in autograd_source,
        "result_is_exploratory": autograd_result.get("classification") == "exploratory_signal",
        "result_joint_kill_top2_false": autograd_result.get("summary", {}).get("joint_kill_edges_in_top2_for_L4") is False,
        "result_note_mentions_top_2_claim_failure": "top-2 attribution claim does not hold" in autograd_note,
    })

    ascent_source = read_text(XGI_ASCENT_SOURCE_PATH)
    ascent_result = read_json(XGI_ASCENT_RESULT_PATH)
    ascent_note = str(ascent_result.get("classification_note", ""))
    checks.append({
        "source": str(XGI_ASCENT_SOURCE_PATH),
        "result": str(XGI_ASCENT_RESULT_PATH),
        "kind": "source_question_vs_result",
        "source_mentions_direct_edges_dominate": "direct L4 edges" in ascent_source,
        "result_is_exploratory": ascent_result.get("classification") == "exploratory_signal",
        "objective_alignment_false": ascent_result.get("summary", {}).get("objective_alignment_with_joint_kill_claim") is False,
        "result_note_mentions_objective_mismatch": "claimed joint-kill dominance pattern does not follow" in ascent_note,
    })

    return checks


def _iter_result_payloads():
    for path in sorted(RESULTS_DIR.glob("*.json")):
        try:
            data = read_json(path)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(data, dict):
            yield path, data


def build_tool_stack_summary(live_anchor_spine: list[dict] | None = None) -> dict:
    counts = {
        tool: {
            "tried_count": 0,
            "used_count": 0,
            "load_bearing_count": 0,
            "depth_present_count": 0,
            "anchor_stage_coverage": [],
            "anchor_result_files": [],
        }
        for tool in TOOL_ORDER
    }

    files_with_manifest_or_depth = 0
    for path, data in _iter_result_payloads():
        tool_manifest = data.get("tool_manifest")
        tool_depth = data.get("tool_integration_depth")
        if not isinstance(tool_manifest, dict) and not isinstance(tool_depth, dict):
            continue
        files_with_manifest_or_depth += 1
        for tool in TOOL_ORDER:
            manifest_info = tool_manifest.get(tool, {}) if isinstance(tool_manifest, dict) else {}
            depth_value = tool_depth.get(tool) if isinstance(tool_depth, dict) else None
            if not isinstance(manifest_info, dict):
                manifest_info = {}
            bucket = counts[tool]
            if manifest_info.get("tried") is True:
                bucket["tried_count"] += 1
            if manifest_info.get("used") is True:
                bucket["used_count"] += 1
            if depth_value is not None:
                bucket["depth_present_count"] += 1
            if isinstance(depth_value, str) and "load" in depth_value.lower():
                bucket["load_bearing_count"] += 1

    stage_map = {}
    for row in live_anchor_spine or []:
        stage_map.setdefault(row["result_json"], set()).add(row["stage"])

    for path, data in _iter_result_payloads():
        tool_depth = data.get("tool_integration_depth")
        if not isinstance(tool_depth, dict):
            continue
        stages = sorted(stage_map.get(path.name, set()))
        for tool, depth_value in tool_depth.items():
            if tool not in counts:
                continue
            if isinstance(depth_value, str) and "load" in depth_value.lower():
                bucket = counts[tool]
                if path.name not in bucket["anchor_result_files"]:
                    bucket["anchor_result_files"].append(path.name)
                for stage in stages:
                    if stage not in bucket["anchor_stage_coverage"]:
                        bucket["anchor_stage_coverage"].append(stage)

    shallow_tools = [
        tool
        for tool, info in counts.items()
        if info["tried_count"] > 0 and info["load_bearing_count"] < 10
    ]
    missing_anchor_tools = [
        tool for tool, info in counts.items() if len(info["anchor_result_files"]) == 0
    ]
    return {
        "files_with_manifest_or_depth": files_with_manifest_or_depth,
        "per_tool": counts,
        "shallow_tools": shallow_tools,
        "missing_anchor_tools": missing_anchor_tools,
        "forcing_targets": {
            tool: TOOL_FORCING_TARGETS.get(tool, [])
            for tool in shallow_tools
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build controller alignment audit surfaces.")
    parser.add_argument(
        "--require-docs-current",
        action="store_true",
        help="Fail closed if documentation drift remains.",
    )
    parser.add_argument(
        "--require-current-contract",
        action="store_true",
        help="Fail closed unless both code/process and docs are current.",
    )
    args = parser.parse_args()

    makefile_text = read_text(MAKEFILE_PATH)
    bot_text = read_text(BOT_PATH)
    makefile_python = parse_python_from_makefile(makefile_text)
    bot_python = parse_python_bin_from_bot(bot_text)
    floors = parse_requirement_floors(REQ_SIM_STACK_PATH)
    packages = package_status()

    env_report = {}
    for req_name, floor in floors.items():
        import_name, dist_name = PACKAGE_MAP.get(req_name, (req_name, req_name))
        pkg = packages.get(req_name, {
            "distribution": dist_name,
            "import_name": import_name,
            "installed_version": None,
            "import_ok": False,
            "import_error": "not checked",
        })
        env_report[req_name] = {
            **pkg,
            "required_floor": floor,
            "meets_floor": compare_floor(pkg.get("installed_version"), floor),
        }

    truth_audit = load_truth_audit_summary()
    truth_blockers = truth_audit.get("blocked_results", {})

    raw_stale_doc_hits = collect_stale_doc_hits()
    c2_crosscheck = compare_c2_surfaces()
    live_anchor_spine = build_live_anchor_spine(truth_blockers)
    tool_stack_summary = build_tool_stack_summary(live_anchor_spine)
    trusted_spine_risky_entries = sum(1 for row in live_anchor_spine if not row["promotion_ready"])
    code_process_green = all([
        makefile_python == bot_python,
        c2_crosscheck["mismatch_count"] == 0,
        not (
            get_phase7_source_flags()["uses_topology_subset_gate"]
            and get_phase7_source_flags()["still_has_not_tested_branch"]
        ),
        truth_audit.get("ok") is True,
        len(tool_stack_summary["shallow_tools"]) == 0,
        trusted_spine_risky_entries == 0,
    ])
    stale_doc_hits = enrich_stale_doc_hits(
        raw_stale_doc_hits,
        sys_executable=sys.executable,
        makefile_python=makefile_python,
        bot_python=bot_python,
        c2_crosscheck=c2_crosscheck,
        truth_audit=truth_audit,
        code_process_green=code_process_green,
    )
    stale_doc_summary = summarize_stale_doc_hits(stale_doc_hits)
    docs_current = len(stale_doc_hits) == 0
    controller_contract_current = code_process_green and docs_current
    report = {
        "name": "controller_alignment_audit",
        "generated_at": datetime.now(UTC).isoformat(),
        "classification": "audit",
        "interpreter_authority": {
            "sys_executable": sys.executable,
            "makefile_python": makefile_python,
            "imessage_bot_python": bot_python,
            "makefile_and_bot_agree": makefile_python == bot_python,
        },
        "env_requirements": env_report,
        "known_env_risks": {
            "clifford_import_ok": env_report.get("clifford", {}).get("import_ok"),
            "clifford_import_error": env_report.get("clifford", {}).get("import_error"),
        },
        "probe_truth_audit": truth_audit,
        "stale_doc_hits": stale_doc_hits,
        "stale_doc_summary": stale_doc_summary,
        "phase7_source_flags": get_phase7_source_flags(),
        "c2_crosscheck": c2_crosscheck,
        "tool_stack_summary": tool_stack_summary,
        "xgi_source_result_drift": check_xgi_source_result_drift(),
        "trusted_spine": build_spine_report(live_anchor_spine),
        "exploratory_branch": [summarize_result_file(RESULTS_DIR / name) for name in EXPLORATORY_BRANCH],
        "summary": {},
    }

    report["summary"] = {
        "doc_drift_count": len(report["stale_doc_hits"]),
        "interpreter_aligned": report["interpreter_authority"]["makefile_and_bot_agree"],
        "phase7_c2_surface_consistent": report["c2_crosscheck"]["mismatch_count"] == 0,
        "phase7_source_has_legacy_subset_branch": report["phase7_source_flags"]["uses_topology_subset_gate"]
        and report["phase7_source_flags"]["still_has_not_tested_branch"],
        "trusted_spine_risky_entries": trusted_spine_risky_entries,
        "truth_audit_ok": truth_audit.get("ok"),
        "shallow_tool_count": len(report["tool_stack_summary"]["shallow_tools"]),
        "code_process_green": code_process_green,
        "docs_current": docs_current,
        "controller_contract_current": controller_contract_current,
    }
    # Compatibility mirrors for older controller readers that still expect these
    # fields at the top level instead of under summary/tool_stack_summary.
    report["doc_drift_count"] = report["summary"]["doc_drift_count"]
    report["phase7_c2_surface_consistent"] = report["summary"]["phase7_c2_surface_consistent"]
    report["phase7_source_has_legacy_subset_branch"] = report["summary"]["phase7_source_has_legacy_subset_branch"]
    report["trusted_spine_risky_entries"] = report["summary"]["trusted_spine_risky_entries"]
    report["shallow_tools"] = report["tool_stack_summary"]["shallow_tools"]
    report["shallow_tool_count"] = report["summary"]["shallow_tool_count"]
    report["doc_drift_by_kind"] = report["stale_doc_summary"]["by_kind"]
    report["code_process_green"] = report["summary"]["code_process_green"]
    report["docs_current"] = report["summary"]["docs_current"]
    report["controller_contract_current"] = report["summary"]["controller_contract_current"]

    doc_drift_inventory = build_doc_drift_inventory(
        stale_doc_hits,
        summary=stale_doc_summary,
        code_process_green=code_process_green,
        docs_current=docs_current,
        controller_contract_current=controller_contract_current,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    with DOC_DRIFT_INVENTORY_PATH.open("w", encoding="utf-8") as fh:
        json.dump(doc_drift_inventory, fh, indent=2)
    with LIVE_ANCHOR_SPINE_PATH.open("w", encoding="utf-8") as fh:
        json.dump({
            "name": "live_anchor_spine",
            "generated_at": datetime.now(UTC).isoformat(),
            "rows": live_anchor_spine,
        }, fh, indent=2)

    print(f"Wrote {OUT_PATH}")
    print(f"Wrote {DOC_DRIFT_INVENTORY_PATH}")
    print(f"Wrote {LIVE_ANCHOR_SPINE_PATH}")
    print(f"doc_drift_count={report['summary']['doc_drift_count']}")
    print(f"phase7_c2_surface_consistent={report['summary']['phase7_c2_surface_consistent']}")
    print(f"phase7_source_has_legacy_subset_branch={report['summary']['phase7_source_has_legacy_subset_branch']}")
    print(f"trusted_spine_risky_entries={report['summary']['trusted_spine_risky_entries']}")
    print(f"shallow_tool_count={report['summary']['shallow_tool_count']}")
    print(f"code_process_green={report['summary']['code_process_green']}")
    print(f"docs_current={report['summary']['docs_current']}")
    print(f"controller_contract_current={report['summary']['controller_contract_current']}")

    if args.require_current_contract and not controller_contract_current:
        print("CONTROLLER ALIGNMENT AUDIT FAILED: current contract not satisfied")
        return 1
    if args.require_docs_current and not docs_current:
        print("CONTROLLER ALIGNMENT AUDIT FAILED: documentation drift remains")
        return 1

    print("CONTROLLER ALIGNMENT AUDIT PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
