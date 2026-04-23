#!/usr/bin/env python3
"""Crawl classical sim result JSONs and emit an innate-miss map.

Markdown report -> stdout
JSON mapping    -> system_v4/probes/a2_state/sim_results/divergence_index.json
"""
from __future__ import annotations

import glob
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RESULTS_DIR = os.path.join(ROOT, "system_v4", "probes", "a2_state", "sim_results")
OUT_JSON = os.path.join(RESULTS_DIR, "divergence_index.json")

FAMILY_KEYWORDS = [
    ("entropy", ["entropy", "renyi", "tsallis", "kl_", "relative_entropy", "mutual_info"]),
    ("compression", ["compression", "compress", "coding", "code_",
                     "principal_subspace", "qpca_spectral_extraction",
                     "spectral_decomposition", "spectral_truncation",
                     "schmidt_mode_truncation", "svd_factorization",
                     "low_rank", "operator_low_rank_factorization"]),
    ("geometry", ["geometry", "geometric", "manifold", "metric", "curvature",
                  "tensor_principal", "spectral_embedding",
                  "placement_law", "trace_distance_geometry",
                  "loop_vector_fields", "husimi_phase_space"]),
    ("dynamics", ["dynamic", "evolution", "propagat", "flow", "trajectory", "branch_weight", "history"]),
    ("probe", ["probe", "admissibility", "distinguish", "support",
               "helstrom_guess_bound"]),
    ("bipartite", ["bipartite", "entangl", "schmidt", "partial_trace"]),
    ("channel", ["channel", "cptp", "choi", "kraus", "stinespring", "blackwell"]),
    ("operator", ["operator", "algebra", "eigen", "covariance", "representation",
                  "signed_operator_variant", "operator_coordinate_representation"]),
    ("constraint", ["constraint", "manifold_mc", "spine", "fence", "ladder",
                    "terrain_family_fourfold"]),
    ("correlation", ["correl", "covarian"]),
    ("coupling", ["coupling", "pairwise_coupling"]),
    ("negation", ["neg_classical_probability", "neg_", "neg"]),
    ("sweep", ["sweep"]),
]


def infer_family(name: str) -> str:
    lo = name.lower()
    for fam, kws in FAMILY_KEYWORDS:
        for kw in kws:
            if kw in lo:
                return fam
    return "other"


def summarize_dl(dl) -> str:
    if dl is None:
        return "MISSING"
    if isinstance(dl, list):
        if not dl:
            return "(empty)"
        first = str(dl[0]).replace("\n", " ").strip()
        if len(dl) > 1:
            return f"{first} [+{len(dl)-1} more]"
        return first
    if isinstance(dl, dict):
        if not dl:
            return "(empty)"
        k = next(iter(dl))
        return f"{k}: {str(dl[k])[:80]}"
    return str(dl)[:120]


def main() -> int:
    pattern = os.path.join(RESULTS_DIR, "*_classical*_results.json")
    files = sorted(glob.glob(pattern))

    records = []
    for fp in files:
        lego = os.path.basename(fp).replace("_classical_results.json", "").replace("_classical_full_spine_results.json", "")
        try:
            with open(fp) as f:
                data = json.load(f)
        except Exception as e:
            records.append({
                "lego": lego, "file": fp, "family": "unreadable",
                "divergence_log": None, "innately_missing": None,
                "all_pass": None, "summary": f"LOAD_ERROR: {e}",
                "missing_divergence_log": True,
            })
            continue
        name = data.get("name", lego)
        dl = data.get("divergence_log", None)
        im = data.get("innately_missing", None)
        ap = data.get("all_pass", None)
        fam = infer_family(name if isinstance(name, str) else lego)
        records.append({
            "lego": lego,
            "file": os.path.relpath(fp, ROOT),
            "family": fam,
            "divergence_log": dl,
            "innately_missing": im,
            "all_pass": ap,
            "summary": summarize_dl(dl),
            "missing_divergence_log": "divergence_log" not in data,
        })

    # Group by family
    by_fam: dict[str, list] = defaultdict(list)
    for r in records:
        by_fam[r["family"]].append(r)

    # Markdown emit
    out = []
    out.append("# Innate-Miss Map (classical sim divergence_log survey)\n")
    out.append(f"Crawled: `{os.path.relpath(RESULTS_DIR, ROOT)}/*_classical*_results.json`\n")
    out.append(f"Total legos: **{len(records)}**\n")

    for fam in sorted(by_fam):
        rows = by_fam[fam]
        out.append(f"\n## Family: {fam} ({len(rows)})\n")
        out.append("| lego | divergence summary | all_pass |")
        out.append("|---|---|---|")
        for r in sorted(rows, key=lambda x: x["lego"]):
            summary = r["summary"].replace("|", "\\|")
            out.append(f"| `{r['lego']}` | {summary} | {r['all_pass']} |")

    # Tail
    missing = [r for r in records if r["summary"] == "MISSING" or r["missing_divergence_log"]]
    non_empty = [r for r in records if r["divergence_log"] and r["summary"] not in ("(empty)", "MISSING")]
    empty = [r for r in records if r["summary"] == "(empty)"]

    out.append("\n## Summary\n")
    out.append(f"- Total legos crawled: **{len(records)}**")
    out.append(f"- Families detected: **{len(by_fam)}** ({', '.join(sorted(by_fam))})")
    out.append(f"- With non-empty divergence_log: **{len(non_empty)}**")
    out.append(f"- With empty divergence_log: **{len(empty)}**")
    out.append(f"- MISSING divergence_log: **{len(missing)}**")
    if missing:
        out.append("\n### Legos missing divergence_log (need fixing):")
        for r in sorted(missing, key=lambda x: x["lego"]):
            out.append(f"- `{r['lego']}` (family: {r['family']})")

    out.append("\n### Family counts:")
    for fam in sorted(by_fam):
        out.append(f"- {fam}: {len(by_fam[fam])}")

    print("\n".join(out))

    # JSON emit
    with open(OUT_JSON, "w") as f:
        json.dump({
            "total": len(records),
            "families": {fam: len(rows) for fam, rows in by_fam.items()},
            "missing_divergence_log": [r["lego"] for r in missing],
            "records": records,
        }, f, indent=2, default=str)

    print(f"\n<!-- wrote {OUT_JSON} -->", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
