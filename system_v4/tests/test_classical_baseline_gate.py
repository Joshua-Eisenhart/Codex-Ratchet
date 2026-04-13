"""CI gate: classical_baseline sims must not be promoted to canonical.

A probe tagged classification = "classical_baseline" is evidence for classical
behavior only. It MUST NOT simultaneously claim canonical status, and MUST NOT
appear in any canonical-registry row. This test enforces the first half
(probe-local invariant) cheaply; registry-level cross-checks can layer on top.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBES_DIR = REPO_ROOT / "system_v4" / "probes"

CLASSIFICATION_RE = re.compile(r"""classification\s*=\s*["']([^"']+)["']""")


def _probe_files() -> list[Path]:
    return sorted(p for p in PROBES_DIR.rglob("*.py") if p.name != "SIM_TEMPLATE.py")


def test_classical_baseline_probes_do_not_claim_canonical():
    offenders: list[tuple[Path, list[str]]] = []
    for path in _probe_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        classes = CLASSIFICATION_RE.findall(text)
        if "classical_baseline" not in classes:
            continue
        if "canonical" in classes:
            offenders.append((path, classes))
    assert not offenders, (
        "Probes tagged classical_baseline must not also claim canonical:\n"
        + "\n".join(f"  {p.relative_to(REPO_ROOT)}: {c}" for p, c in offenders)
    )


def test_classical_baseline_probes_do_not_declare_load_bearing_tool():
    """Classical baselines cannot have a load_bearing tool — that's canonical territory."""
    offenders: list[Path] = []
    for path in _probe_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "classical_baseline" not in text:
            continue
        if not CLASSIFICATION_RE.search(text):
            continue
        if CLASSIFICATION_RE.search(text).group(1) != "classical_baseline":
            continue
        if '"load_bearing"' in text or "'load_bearing'" in text:
            offenders.append(path)
    assert not offenders, (
        "Classical-baseline probes must not declare load_bearing tools:\n"
        + "\n".join(f"  {p.relative_to(REPO_ROOT)}" for p in offenders)
    )
