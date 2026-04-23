#!/usr/bin/env python3
"""
Lane B coverage matrix generator.

Crawls `system_v4/probes/sim_*_classical*.py` and their result JSONs in
`system_v4/probes/a2_state/sim_results/*_classical_results.json`, groups
them by lego family, and emits a markdown table.

Status labels (per CLAUDE.md) are NOT inflated: we only report what the
result JSON itself says (`all_pass`) and whether `divergence_log` is
non-empty. We do not claim "canonical by process" or "passes local rerun"
on behalf of any sim.

Output: stdout AND docs/plans/lane_b_coverage_matrix.md
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
PROBES_DIR = REPO_ROOT / "system_v4" / "probes"
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"
OUTPUT_MD = REPO_ROOT / "docs" / "plans" / "lane_b_coverage_matrix.md"

SIM_GLOB = "sim_*_classical*.py"
RESULT_SUFFIX = "_classical_results.json"


# -------- family classification --------
# Keywords are matched against the sim stem (after stripping "sim_" and
# "_classical*"). First match wins, order matters.
FAMILY_RULES: list[tuple[str, list[str]]] = [
    ("entropy/information", [
        "shannon_entropy", "renyi_entropy", "min_max_entropy",
        "relative_entropy", "mutual_information", "conditional_entropy",
        "holevo_bound", "fisher_information", "quantum_fisher_information",
        "quantum_discord", "helstrom_guess_bound", "coherence_measure",
        "entanglement_of_formation",
    ]),
    ("compression/spectral", [
        "qpca", "spectral_decomposition", "spectral_truncation",
        "svd_factorization", "eigenvalue_spectrum", "principal_subspace",
        "low_rank_psd", "operator_low_rank", "schmidt_decomposition",
        "schmidt_mode_truncation", "correlation_tensor_principal",
        "covariance_operator",
    ]),
    ("state-representation", [
        "joint_density_matrix", "purification", "characteristic_representation",
        "husimi_phase_space", "operator_coordinate_representation",
        "signed_operator_variant", "coarse_grained_operator_algebra",
        "stabilizer_formalism", "magic_state",
    ]),
    ("geometry", [
        "channel_space_geometry", "trace_distance_geometry",
        "geometry_preserving_basis_change", "loop_vector_fields",
        "placement_law", "terrain_family_fourfold",
    ]),
    ("probe/measurement", [
        "povm_measurement", "measurement_instrument",
        "probe_object", "probe_identity_preservation",
        "carrier_probe_support", "distinguishability_relation",
        "witness_operator", "contextuality_witness",
        "constraint_probe_admissibility", "blackwell_comparison",
        "syndrome_decoding",
    ]),
    ("dynamics/evolution", [
        "lindbladian_evolution", "trace_norm_dynamics",
        "unitary_channel", "branch_weight",
    ]),
    ("channel", [
        "channel_cptp", "choi_matrix", "kraus_operator_sum",
        "petz_recovery",
    ]),
    ("bipartite", [
        "partial_trace",
    ]),
    ("g-tower/manifold", [
        "g_structure_tower", "admissibility_manifold",
        "constraint_manifold", "f01_finitude_constraint",
    ]),
    ("resource", [
        # intentionally empty of specific matches; resource-theoretic
        # items currently land in state-rep or entropy. Leaving the family
        # declared for completeness per task spec.
    ]),
    ("coupling", [
        "pairwise_coupling",
    ]),
]

FAMILY_ORDER = [fam for fam, _ in FAMILY_RULES] + ["unclassified"]


def classify(stem: str) -> str:
    key = stem
    if key.startswith("sim_"):
        key = key[4:]
    key = re.sub(r"_classical.*$", "", key)
    for fam, keywords in FAMILY_RULES:
        for kw in keywords:
            if kw in key:
                return fam
    return "unclassified"


def sim_to_result_path(sim_path: Path) -> Path:
    stem = sim_path.stem  # sim_foo_classical
    if stem.startswith("sim_"):
        stem = stem[4:]
    return RESULTS_DIR / f"{stem}_results.json"


def load_json(path: Path) -> dict | None:
    try:
        with path.open() as fh:
            return json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def summarize_sim(sim_path: Path) -> dict:
    result_path = sim_to_result_path(sim_path)
    data = load_json(result_path) if result_path.exists() else None

    all_pass = None
    div_nonempty = None
    if isinstance(data, dict):
        if "all_pass" in data:
            all_pass = bool(data.get("all_pass"))
        elif isinstance(data.get("summary"), dict) and "all_pass" in data["summary"]:
            all_pass = bool(data["summary"]["all_pass"])
        div = data.get("divergence_log")
        div_nonempty = bool(div) if isinstance(div, list) else (div is not None)

    return {
        "sim_path": str(sim_path.relative_to(REPO_ROOT)),
        "sim_name": sim_path.stem,
        "result_exists": result_path.exists(),
        "result_path": str(result_path.relative_to(REPO_ROOT)) if result_path.exists() else "",
        "all_pass": all_pass,
        "divergence_log_nonempty": div_nonempty,
        "family": classify(sim_path.stem),
    }


def fmt_bool(v: bool | None) -> str:
    if v is True:
        return "yes"
    if v is False:
        return "no"
    return "n/a"


def build_markdown(sims: list[dict]) -> str:
    by_family: dict[str, list[dict]] = {fam: [] for fam in FAMILY_ORDER}
    for s in sims:
        by_family.setdefault(s["family"], []).append(s)

    lines: list[str] = []
    lines.append("# Lane B Classical Baseline Coverage Matrix")
    lines.append("")
    lines.append(f"- Total classical sim files: **{len(sims)}**")
    lines.append(f"- Generated by `scripts/lane_b_coverage_matrix.py`")
    lines.append("")
    lines.append("Status note: `all_pass` and `divergence_log_nonempty` are read")
    lines.append("directly from each result JSON. No inflation to `passes local rerun`")
    lines.append("or `canonical by process` — those require re-execution this session.")
    lines.append("")

    # Family rollup
    lines.append("## Family rollup")
    lines.append("")
    lines.append("| family | count | all_pass (yes/no/n/a) | divergence_log non-empty (yes/no/n/a) |")
    lines.append("|---|---|---|---|")
    for fam in FAMILY_ORDER:
        entries = by_family.get(fam, [])
        if not entries:
            continue
        yes_pass = sum(1 for e in entries if e["all_pass"] is True)
        no_pass = sum(1 for e in entries if e["all_pass"] is False)
        na_pass = sum(1 for e in entries if e["all_pass"] is None)
        yes_div = sum(1 for e in entries if e["divergence_log_nonempty"] is True)
        no_div = sum(1 for e in entries if e["divergence_log_nonempty"] is False)
        na_div = sum(1 for e in entries if e["divergence_log_nonempty"] is None)
        lines.append(
            f"| {fam} | {len(entries)} | {yes_pass}/{no_pass}/{na_pass} | {yes_div}/{no_div}/{na_div} |"
        )
    lines.append("")

    # Per-sim detail
    lines.append("## Per-sim detail")
    lines.append("")
    for fam in FAMILY_ORDER:
        entries = sorted(by_family.get(fam, []), key=lambda e: e["sim_name"])
        if not entries:
            continue
        lines.append(f"### {fam} ({len(entries)})")
        lines.append("")
        lines.append("| sim | all_pass | divergence_log non-empty | result JSON |")
        lines.append("|---|---|---|---|")
        for e in entries:
            result_cell = f"`{e['result_path']}`" if e["result_path"] else "_missing_"
            lines.append(
                f"| `{e['sim_path']}` | {fmt_bool(e['all_pass'])} | "
                f"{fmt_bool(e['divergence_log_nonempty'])} | {result_cell} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def find_sims() -> list[Path]:
    return sorted(PROBES_DIR.glob(SIM_GLOB))


def main() -> int:
    sims = find_sims()
    summaries = [summarize_sim(s) for s in sims]
    md = build_markdown(summaries)
    print(md)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
