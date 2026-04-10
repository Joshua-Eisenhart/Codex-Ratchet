#!/usr/bin/env python3
"""
Bounded doc -> lego audit.

Builds one machine-readable surface that:
  - extracts the core math/sim families explicitly named in the execution docs
  - checks whether matching sim/result surfaces already exist
  - separates lego-first families from later integration work
  - keeps root-constraint-killed candidates as useful evidence, not dead ends
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
OUT_PATH = RESULTS_DIR / "lego_stack_audit_results.json"
LIVE_SPINE_PATH = RESULTS_DIR / "live_anchor_spine.json"
PROBES_DIR = SCRIPT_DIR

CORE_DOCS = [
    PROJECT_DIR / "new docs" / "07_model_math_geometry_sim_plan.md",
    PROJECT_DIR / "new docs" / "08_aligned_sim_backlog_and_build_order.md",
    PROJECT_DIR / "new docs" / "LEGO_SIM_CONTRACT.md",
    PROJECT_DIR / "new docs" / "FALSIFICATION_SIM_DESIGNS.md",
]

BACKLOG = [
    {
        "id": "constraint_probe_admissibility",
        "family": "Constraint and probe admissibility",
        "assembly_stage": "lego",
        "doc_stage": "Layer 0 / L1 upward fence",
        "match_tokens": ["constraint", "probe", "guard", "fence", "admissibility"],
        "useful_if_rejected": True,
        "why": "Root-constraint kills are useful because they map the admissible boundary early.",
        "source_docs": [
            "new docs/07_model_math_geometry_sim_plan.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
            "new docs/LEGO_SIM_CONTRACT.md",
        ],
    },
    {
        "id": "carrier_admission_density_matrix",
        "family": "Carrier admission and density-matrix representability",
        "assembly_stage": "lego",
        "doc_stage": "Layer 1",
        "match_tokens": ["carrier", "density", "positivity", "trace", "normalization", "rhoab"],
        "useful_if_rejected": True,
        "why": "Rejected carrier families still show what the root constraints refuse to admit.",
        "source_docs": [
            "new docs/07_model_math_geometry_sim_plan.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
        ],
    },
    {
        "id": "geometry_crosschecks_same_carrier",
        "family": "Geometry cross-checks on the same carrier",
        "assembly_stage": "lego",
        "doc_stage": "Layer 2",
        "match_tokens": ["hopf", "torus", "geometry", "fubini", "bures", "berry", "qfi", "qgt", "holonomy"],
        "useful_if_rejected": True,
        "why": "Geometry failures are useful because they kill metric smuggling and flat-only shortcuts.",
        "source_docs": [
            "new docs/07_model_math_geometry_sim_plan.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
        ],
    },
    {
        "id": "graph_cell_complex_geometry",
        "family": "Graph and cell-complex carrier geometry",
        "assembly_stage": "lego",
        "doc_stage": "Layer 2",
        "match_tokens": ["graph", "cell", "toponetx", "xgi", "gudhi", "hypergraph"],
        "useful_if_rejected": True,
        "why": "Topology-sensitive failures are still evidence about which carrier views survive.",
        "source_docs": [
            "new docs/07_model_math_geometry_sim_plan.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
        ],
    },
    {
        "id": "operator_family_admission",
        "family": "Operator family admission",
        "assembly_stage": "lego",
        "doc_stage": "Layer 3",
        "match_tokens": ["operator", "pauli", "clifford", "commutator", "channel", "left_right", "chirality"],
        "useful_if_rejected": True,
        "why": "Operator families that collapse under commutative or symmetric reductions are useful kills.",
        "source_docs": [
            "new docs/07_model_math_geometry_sim_plan.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
            "new docs/FALSIFICATION_SIM_DESIGNS.md",
        ],
    },
    {
        "id": "bipartite_structure_local",
        "family": "Bipartite structure lego set",
        "assembly_stage": "lego",
        "doc_stage": "Layer 4",
        "match_tokens": ["bipartite", "partial_trace", "concurrence", "negativity", "werner", "schmidt", "discord"],
        "useful_if_rejected": True,
        "why": "False bipartite or witness candidates are still useful because they clarify which summaries are lossy.",
        "source_docs": [
            "new docs/07_model_math_geometry_sim_plan.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
        ],
    },
    {
        "id": "entropy_family_crosschecks",
        "family": "Entropy family cross-checks",
        "assembly_stage": "lego",
        "doc_stage": "Layer 5",
        "match_tokens": ["entropy", "mutual_information", "coherent_information", "renyi", "tsallis", "min_entropy"],
        "useful_if_rejected": True,
        "why": "Rejected entropy candidates are useful because entropy is later-layer and should lose if underpowered.",
        "source_docs": [
            "new docs/07_model_math_geometry_sim_plan.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
        ],
    },
    {
        "id": "dependency_dag_and_collapse",
        "family": "Collapse analysis and dependency DAG",
        "assembly_stage": "coupling",
        "doc_stage": "Build-order analysis",
        "match_tokens": ["dependency", "dag", "collapse", "family", "derived", "basis"],
        "useful_if_rejected": True,
        "why": "Collapse failures show which families are genuinely distinct rather than renamed summaries.",
        "source_docs": [
            "new docs/08_aligned_sim_backlog_and_build_order.md",
        ],
    },
    {
        "id": "axis_entry_after_admission",
        "family": "Axis entry only after lower-layer admission",
        "assembly_stage": "assembly",
        "doc_stage": "Layer 6",
        "match_tokens": ["axis0", "axis6", "signed", "left_right", "bridge", "phi0"],
        "useful_if_rejected": True,
        "why": "Axis candidates that fail lower-layer admission are useful because they prevent premature promotion.",
        "source_docs": [
            "new docs/07_model_math_geometry_sim_plan.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
        ],
    },
    {
        "id": "gauge_group_falsifier",
        "family": "Gauge-group correspondence falsifier",
        "assembly_stage": "lego",
        "doc_stage": "Falsification sim",
        "match_tokens": ["gauge", "lie", "commutator", "su2", "su3", "u1"],
        "useful_if_rejected": True,
        "why": "A kill here is more informative than a vague positive mapping claim.",
        "source_docs": [
            "new docs/FALSIFICATION_SIM_DESIGNS.md",
        ],
    },
    {
        "id": "viability_vs_attractor_falsifier",
        "family": "Viability vs attractor falsifier",
        "assembly_stage": "coupling",
        "doc_stage": "Falsification sim",
        "match_tokens": ["viability", "attractor", "trajectory", "perturb", "cycle"],
        "useful_if_rejected": True,
        "why": "If viability fails, that changes the framing cleanly and usefully.",
        "source_docs": [
            "new docs/FALSIFICATION_SIM_DESIGNS.md",
        ],
    },
    {
        "id": "quantum_metric_nonuniqueness",
        "family": "Quantum metric non-uniqueness cross-check",
        "assembly_stage": "lego",
        "doc_stage": "Falsification sim",
        "match_tokens": ["bures", "wigner", "kubo", "metric", "distance", "rho_ab"],
        "useful_if_rejected": True,
        "why": "If the metrics disagree qualitatively, that is useful structure pressure, not failure noise.",
        "source_docs": [
            "new docs/FALSIFICATION_SIM_DESIGNS.md",
            "new docs/08_aligned_sim_backlog_and_build_order.md",
        ],
    },
]

LATE_STAGE_NOISE_TOKENS = [
    "axis0",
    "phi0",
    "xi_",
    "history",
    "integrated",
    "pipeline",
    "master_engine",
    "full_cascade",
    "prototype",
    "stress",
    "bakeoff",
    "dynamic_shell",
    "attractor",
]

RESULT_SUSPICIOUS_TOKENS = [
    "phi0",
    "bridge",
    "history",
    "kernel",
    "bakeoff",
    "axis6",
    "integrated",
    "pipeline",
]

DEFAULT_LEGO_EXCLUDE_TOKENS = [
    "bridge",
    "phi0",
    "xi_",
    "kernel",
    "cut",
    "axis",
    "history",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_live_spine() -> list[dict]:
    if not LIVE_SPINE_PATH.exists():
        return []
    data = json.loads(LIVE_SPINE_PATH.read_text())
    return data.get("rows", [])


def probe_index() -> list[dict]:
    rows = []
    for path in sorted(PROBES_DIR.glob("sim_*.py")):
        stem = path.stem.lower()
        rows.append({"path": str(path), "stem": stem})
    return rows


def result_index() -> list[dict]:
    rows = []
    for path in sorted(RESULTS_DIR.glob("*_results.json")):
        try:
            data = json.loads(path.read_text())
        except Exception:
            data = {}
        rows.append({"path": str(path), "stem": path.stem.lower(), "data": data})
    return rows


def is_late_stage_noise(stem: str) -> bool:
    return any(token in stem for token in LATE_STAGE_NOISE_TOKENS)


def score_match(tokens: list[str], stem: str) -> int:
    return sum(1 for tok in tokens if tok.lower() in stem)


def match_paths(tokens: list[str], rows: list[dict], *, lego_only: bool) -> list[str]:
    hits = []
    lowered = [t.lower() for t in tokens]
    for row in rows:
        hay = row["stem"]
        if not any(tok in hay for tok in lowered):
            continue
        if lego_only and is_late_stage_noise(hay):
            continue
        hits.append((score_match(lowered, hay), Path(row["path"]).name))
    hits.sort(key=lambda item: (-item[0], item[1]))
    return [name for _, name in hits]


def classify_result_strength(result_row: dict) -> tuple[int, str]:
    stem = result_row["stem"]
    data = result_row.get("data", {})
    classification = data.get("classification")
    note = str(data.get("classification_note", "")).lower()
    summary = data.get("summary", {})
    score = 0
    reason = "weak"

    if any(tok in stem for tok in RESULT_SUSPICIOUS_TOKENS):
        score -= 2
        reason = "late_stage_name"

    if classification == "canonical":
        score += 3
        reason = "canonical"
    elif classification == "supporting":
        score += 1
        reason = "supporting"
    elif classification in ("candidate_discriminator", "exploratory_signal"):
        score -= 2
        reason = classification

    if isinstance(summary, dict):
        if summary.get("all_pass") is True or summary.get("all_tests_passed") is True:
            score += 2
        if summary.get("all_pass") is False or summary.get("all_tests_passed") is False:
            score -= 3
            reason = "failed_summary"

    if "not a full" in note or "not full" in note or "not a closure" in note:
        score -= 2
        reason = "scoped_only"

    return score, reason


def result_name_to_probe_name(result_name: str) -> str:
    stem = result_name.removesuffix("_results.json")
    return f"sim_{stem}.py"


def default_lego_allowed(probe_name: str) -> bool:
    stem = probe_name.removeprefix("sim_").removesuffix(".py").lower()
    return not any(tok in stem for tok in DEFAULT_LEGO_EXCLUDE_TOKENS)


def choose_recommended_probes(item: dict, result_rows: list[dict]) -> tuple[list[str], list[dict]]:
    result_by_name = {Path(row["path"]).name: row for row in result_rows}
    ranked = []
    for result_name in item["matching_result_files"]:
        row = result_by_name.get(result_name)
        if row is None:
            continue
        score, reason = classify_result_strength(row)
        probe_name = result_name_to_probe_name(result_name)
        ranked.append({
            "probe_file": probe_name,
            "result_file": result_name,
            "score": score,
            "reason": reason,
        })
    ranked.sort(key=lambda row: (-row["score"], row["probe_file"]))
    recommended = [
        row["probe_file"]
        for row in ranked
        if row["score"] >= 2 and default_lego_allowed(row["probe_file"])
    ][:6]
    return recommended, ranked[:10]


def stage_bias_summary(live_spine: list[dict]) -> dict:
    counts = {}
    for row in live_spine:
        stage = row.get("stage", "unknown")
        counts[stage] = counts.get(stage, 0) + 1
    lego_count = counts.get("lego", 0)
    post_lego = (
        counts.get("coupling", 0)
        + counts.get("coexistence", 0)
        + counts.get("topology", 0)
        + counts.get("assembly", 0)
    )
    return {
        "stage_counts": counts,
        "lego_anchor_count": lego_count,
        "post_lego_anchor_count": post_lego,
        "post_lego_overweight": post_lego > lego_count,
    }


def build_candidates() -> list[dict]:
    probes = probe_index()
    results = result_index()
    rows = []
    for item in BACKLOG:
        lego_only = item["assembly_stage"] == "lego"
        probe_hits = match_paths(item["match_tokens"], probes, lego_only=lego_only)
        result_hits = match_paths(item["match_tokens"], results, lego_only=lego_only)
        recommended_probe_files, result_rankings = choose_recommended_probes(
            {
                **item,
                "matching_result_files": result_hits[:6],
            },
            results,
        )
        rows.append({
            **item,
            "matching_probe_files": probe_hits[:6],
            "matching_result_files": result_hits[:6],
            "recommended_probe_files": recommended_probe_files,
            "result_rankings": result_rankings,
            "already_simulated": bool(result_hits),
            "needs_deeper_lego_work": item["assembly_stage"] == "lego" and len(recommended_probe_files) < 2,
        })
    return rows


def main() -> int:
    live_spine = load_live_spine()
    report = {
        "name": "lego_stack_audit",
        "generated_at": datetime.now(UTC).isoformat(),
        "docs_scanned": [str(path.relative_to(PROJECT_DIR)) for path in CORE_DOCS if path.exists()],
        "doc_supports_lego_first": True,
        "source_notes": {
            "07_model_math_geometry_sim_plan": "simulate families early; promote only after survival",
            "08_aligned_sim_backlog_and_build_order": "carrier -> geometry -> operators -> correlations -> entropy -> axes",
            "lego_contract": "small sims must be rich enough to compose upward",
            "falsification_designs": "kills are useful boundary evidence",
        },
        "stage_bias": stage_bias_summary(live_spine),
        "candidates": build_candidates(),
    }
    report["recommended_lego_probes"] = [
        probe
        for row in report["candidates"]
        if row["assembly_stage"] == "lego"
        for probe in row.get("recommended_probe_files", [])
    ]
    report["summary"] = {
        "candidate_count": len(report["candidates"]),
        "lego_candidate_count": sum(1 for row in report["candidates"] if row["assembly_stage"] == "lego"),
        "already_simulated_count": sum(1 for row in report["candidates"] if row["already_simulated"]),
        "needs_deeper_lego_work_count": sum(1 for row in report["candidates"] if row["needs_deeper_lego_work"]),
        "useful_if_rejected_count": sum(1 for row in report["candidates"] if row["useful_if_rejected"]),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")
    print(f"candidate_count={report['summary']['candidate_count']}")
    print(f"lego_candidate_count={report['summary']['lego_candidate_count']}")
    print(f"needs_deeper_lego_work_count={report['summary']['needs_deeper_lego_work_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
