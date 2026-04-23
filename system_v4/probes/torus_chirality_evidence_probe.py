#!/usr/bin/env python3
"""
Torus/Chirality Evidence Loop Probe
=====================================
Runs the actual engine at different torus placements and both engine types
to answer:
  1. Does torus placement actually matter?
  2. Does the Type-1/Type-2 split produce geometrically distinct dynamics?
  3. Which negatives support that?

This is ENGINE-DRIVEN evidence, not graph assertions. It runs the real
GeometricEngine from engine_core.py at different torus η values and
measures axis trajectory divergence.

Outputs to a2_state/audit_logs/ as a bounded evidence packet.

Usage:
    python3 system_v4/probes/torus_chirality_evidence_probe.py
"""

import json
import os
import sys
import time
from pathlib import Path
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_core import GeometricEngine, StageControls, TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER
from hopf_manifold import torus_radii, von_neumann_entropy_2x2
from geometric_operators import trace_distance_2x2, negentropy

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_DIR = REPO_ROOT / "system_v4" / "a2_state" / "audit_logs"
OUTPUT_JSON = AUDIT_DIR / "TORUS_CHIRALITY_EVIDENCE__CURRENT__v1.json"
OUTPUT_MD = AUDIT_DIR / "TORUS_CHIRALITY_EVIDENCE__CURRENT__v1.md"


def _utc_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def run_engine_at_torus(engine_type: int, torus_eta: float, label: str, rng=None):
    """Run full 8-macro-stage cycle with all stages pinned to one torus."""
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(eta=torus_eta, rng=rng or np.random.default_rng(42))
    axes_before = engine.read_axes(state)

    # Pin all 8 stages to this torus
    controls = {i: StageControls(torus=torus_eta) for i in range(8)}
    state = engine.run_cycle(state, controls=controls)
    axes_after = engine.read_axes(state)

    # Per-step analysis
    dphi_L_total = sum(h["dphi_L"] for h in state.history)
    dphi_R_total = sum(h["dphi_R"] for h in state.history)

    # Chirality: trace distance between L and R at end
    chirality = float(trace_distance_2x2(state.rho_L, state.rho_R))

    # Entropy at end
    rho_avg = (state.rho_L + state.rho_R) / 2
    S_end = von_neumann_entropy_2x2(rho_avg)

    return {
        "engine_type": engine_type,
        "torus_label": label,
        "torus_eta": round(float(torus_eta), 6),
        "R_major": round(float(np.cos(torus_eta)), 6),
        "R_minor": round(float(np.sin(torus_eta)), 6),
        "stages_run": len(state.history),
        "dphi_L_total": round(dphi_L_total, 6),
        "dphi_R_total": round(dphi_R_total, 6),
        "chirality_end": round(chirality, 6),
        "entropy_end": round(S_end, 6),
        "axes_before": {k: round(v, 6) for k, v in axes_before.items()},
        "axes_after": {k: round(v, 6) for k, v in axes_after.items()},
        "axis_deltas": {k: round(axes_after[k] - axes_before[k], 6) for k in axes_before},
    }


def run_default_engine(engine_type: int, rng=None):
    """Run full cycle with default controls (Clifford start, no pinning)."""
    engine = GeometricEngine(engine_type=engine_type)
    state = engine.init_state(rng=rng or np.random.default_rng(42))
    axes_before = engine.read_axes(state)
    state = engine.run_cycle(state)
    axes_after = engine.read_axes(state)

    dphi_L_total = sum(h["dphi_L"] for h in state.history)
    dphi_R_total = sum(h["dphi_R"] for h in state.history)
    chirality = float(trace_distance_2x2(state.rho_L, state.rho_R))
    S_end = von_neumann_entropy_2x2((state.rho_L + state.rho_R) / 2)

    return {
        "engine_type": engine_type,
        "torus_label": "default",
        "torus_eta": round(float(TORUS_CLIFFORD), 6),
        "stages_run": len(state.history),
        "dphi_L_total": round(dphi_L_total, 6),
        "dphi_R_total": round(dphi_R_total, 6),
        "chirality_end": round(chirality, 6),
        "entropy_end": round(S_end, 6),
        "axes_before": {k: round(v, 6) for k, v in axes_before.items()},
        "axes_after": {k: round(v, 6) for k, v in axes_after.items()},
        "axis_deltas": {k: round(axes_after[k] - axes_before[k], 6) for k in axes_before},
    }


def compute_evidence(runs):
    """Derive evidence from the run results."""
    evidence = {}

    # 1. Does torus placement matter?
    # Compare axis deltas across torus placements for same engine type
    for et in [1, 2]:
        et_runs = [r for r in runs if r["engine_type"] == et and r["torus_label"] != "default"]
        if len(et_runs) >= 2:
            # Max axis delta spread across torus placements
            axis_keys = list(et_runs[0]["axis_deltas"].keys())
            spreads = {}
            for ax in axis_keys:
                vals = [r["axis_deltas"][ax] for r in et_runs]
                spreads[ax] = round(max(vals) - min(vals), 6)
            evidence[f"type{et}_torus_axis_spread"] = spreads
            evidence[f"type{et}_torus_max_spread"] = max(spreads.values())

            # Chirality spread
            chir_vals = [r["chirality_end"] for r in et_runs]
            evidence[f"type{et}_chirality_spread"] = round(max(chir_vals) - min(chir_vals), 6)

            # Entropy spread
            ent_vals = [r["entropy_end"] for r in et_runs]
            evidence[f"type{et}_entropy_spread"] = round(max(ent_vals) - min(ent_vals), 6)

    # 2. Does engine type matter?
    # Compare same torus placement across engine types
    for torus_label in ["inner", "clifford", "outer", "default"]:
        t_runs = [r for r in runs if r["torus_label"] == torus_label]
        if len(t_runs) == 2:
            r1, r2 = t_runs
            axis_keys = list(r1["axis_deltas"].keys())
            type_diffs = {ax: round(abs(r1["axis_deltas"][ax] - r2["axis_deltas"][ax]), 6) for ax in axis_keys}
            evidence[f"{torus_label}_engine_type_diff"] = type_diffs
            evidence[f"{torus_label}_chirality_diff"] = round(abs(r1["chirality_end"] - r2["chirality_end"]), 6)

    # 3. Verdicts
    torus_matters = any(
        evidence.get(f"type{et}_torus_max_spread", 0) > 0.01
        for et in [1, 2]
    )
    chirality_matters = any(
        evidence.get(f"{t}_chirality_diff", 0) > 0.01
        for t in ["inner", "clifford", "outer", "default"]
    )
    evidence["verdict_torus_placement_matters"] = torus_matters
    evidence["verdict_chirality_split_matters"] = chirality_matters

    return evidence


def main():
    print(f"\n{'='*60}")
    print("TORUS/CHIRALITY EVIDENCE LOOP PROBE")
    print(f"{'='*60}")

    rng = np.random.default_rng(42)
    runs = []

    torus_configs = [
        (TORUS_INNER, "inner"),
        (TORUS_CLIFFORD, "clifford"),
        (TORUS_OUTER, "outer"),
    ]

    for engine_type in [1, 2]:
        # Default run (no torus pinning)
        result = run_default_engine(engine_type, rng=np.random.default_rng(42))
        runs.append(result)
        print(f"  Type-{engine_type} default:  ΔΦ_L={result['dphi_L_total']:+.4f}  "
              f"ΔΦ_R={result['dphi_R_total']:+.4f}  chir={result['chirality_end']:.4f}  "
              f"S={result['entropy_end']:.4f}")

        # Torus-pinned runs
        for eta, label in torus_configs:
            result = run_engine_at_torus(engine_type, eta, label, rng=np.random.default_rng(42))
            runs.append(result)
            print(f"  Type-{engine_type} {label:8s}: ΔΦ_L={result['dphi_L_total']:+.4f}  "
                  f"ΔΦ_R={result['dphi_R_total']:+.4f}  chir={result['chirality_end']:.4f}  "
                  f"S={result['entropy_end']:.4f}")
        print()

    evidence = compute_evidence(runs)

    print(f"  EVIDENCE:")
    print(f"    Torus placement matters: {evidence['verdict_torus_placement_matters']}")
    print(f"    Chirality split matters: {evidence['verdict_chirality_split_matters']}")
    for et in [1, 2]:
        spread = evidence.get(f"type{et}_torus_max_spread", 0)
        print(f"    Type-{et} max torus axis spread: {spread:.6f}")
    for t in ["inner", "clifford", "outer"]:
        diff = evidence.get(f"{t}_chirality_diff", 0)
        print(f"    {t} T1↔T2 chirality diff: {diff:.6f}")

    # Build output
    output = {
        "schema": "TORUS_CHIRALITY_EVIDENCE_v1",
        "generated_utc": _utc_iso(),
        "sidecar_boundary": {
            "mode": "bounded_read_only",
            "do_not_promote": True,
            "audit_only": True,
            "nonoperative": True,
            "purpose": "Engine-driven evidence about torus placement and chirality split effects",
        },
        "runs": runs,
        "evidence": evidence,
    }

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(output, indent=2, default=str) + "\n", encoding="utf-8")

    # Markdown report
    md_lines = [
        "# Torus/Chirality Evidence Loop Results",
        "",
        f"- generated_utc: `{output['generated_utc']}`",
        f"- do_not_promote: `True`",
        "",
        "## Verdicts",
        f"- **Torus placement matters**: `{evidence['verdict_torus_placement_matters']}`",
        f"- **Chirality split matters**: `{evidence['verdict_chirality_split_matters']}`",
        "",
        "## Per-Run Summary",
        "",
        "| Engine | Torus | ΔΦ_L | ΔΦ_R | Chirality | Entropy |",
        "|--------|-------|------|------|-----------|---------|",
    ]
    for r in runs:
        md_lines.append(
            f"| Type-{r['engine_type']} | {r['torus_label']:8s} | "
            f"{r['dphi_L_total']:+.4f} | {r['dphi_R_total']:+.4f} | "
            f"{r['chirality_end']:.4f} | {r['entropy_end']:.4f} |"
        )
    md_lines.extend([
        "",
        "## Axis Spread (Torus Effect)",
    ])
    for et in [1, 2]:
        spreads = evidence.get(f"type{et}_torus_axis_spread", {})
        md_lines.append(f"\n### Type-{et}")
        for ax, s in sorted(spreads.items()):
            md_lines.append(f"- `{ax}`: {s:.6f}")
        md_lines.append(f"- Max spread: `{evidence.get(f'type{et}_torus_max_spread', 0):.6f}`")

    md_lines.extend([
        "",
        "## Engine Type Differences (at same torus)",
    ])
    for t in ["inner", "clifford", "outer", "default"]:
        diffs = evidence.get(f"{t}_engine_type_diff", {})
        if diffs:
            md_lines.append(f"\n### {t}")
            for ax, d in sorted(diffs.items()):
                md_lines.append(f"- `{ax}`: {d:.6f}")
            md_lines.append(f"- Chirality diff: `{evidence.get(f'{t}_chirality_diff', 0):.6f}`")

    md_lines.append("")
    OUTPUT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"\n  JSON: {OUTPUT_JSON}")
    print(f"  MD:   {OUTPUT_MD}")


if __name__ == "__main__":
    main()
