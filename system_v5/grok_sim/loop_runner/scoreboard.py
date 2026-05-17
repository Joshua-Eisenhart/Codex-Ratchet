#!/usr/bin/env python3
"""scoreboard.py — scan all candidates produced this session, report:
  - which phases each one passes (per latest receipts)
  - which audits flagged P0 cheats
  - which proposed legos were extracted

Useful for tracking convergence across many parallel loops.

Run: python3 scoreboard.py
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
CANDIDATES_DIR = HERE.parent / "candidates"
RECEIPTS_DIR = HERE / "receipts"
PROPOSED_DIR = HERE / "proposed_legos"


def candidates_in_play():
    """Return list of (path, mtime) for candidates produced by the loop or stored."""
    if not CANDIDATES_DIR.exists():
        return []
    cands = [p for p in CANDIDATES_DIR.glob("candidate_*.py")]
    cands.sort(key=lambda p: p.stat().st_mtime)
    return cands


def find_latest_summary(candidate_path: Path):
    """Find the most recent _summary.json that referenced this candidate."""
    if not RECEIPTS_DIR.exists():
        return None
    runs = sorted([d for d in RECEIPTS_DIR.iterdir() if d.is_dir()],
                  key=lambda d: d.name, reverse=True)
    cand_str = str(candidate_path)
    for run in runs:
        summary_path = run / "_summary.json"
        if not summary_path.exists():
            continue
        try:
            s = json.loads(summary_path.read_text())
            if s.get("candidate") == cand_str:
                return s
        except Exception:
            continue
    return None


def audit_findings_for(candidate_path: Path):
    """Read .codex_review.txt next to the candidate (if present) and return
    a tuple (has_p0, has_p1, summary_first_line)."""
    review_path = candidate_path.with_suffix(".codex_review.txt")
    if not review_path.exists():
        return None, None, None
    try:
        text = review_path.read_text()[:2000]
    except Exception:
        return None, None, None
    has_p0 = bool(re.search(r"\bP0\b|\bcritical\b", text, re.IGNORECASE))
    has_p1 = bool(re.search(r"\bP1\b|\bmajor\b", text, re.IGNORECASE))
    # First line that looks like a summary
    first = next((line for line in text.split("\n")
                  if line.strip() and not line.startswith("```") and not line.startswith("#")), "")
    return has_p0, has_p1, first[:120]


def proposed_legos_count():
    if not PROPOSED_DIR.exists():
        return 0
    return len(list(PROPOSED_DIR.glob("*.py")))


def main():
    cands = candidates_in_play()
    print(f"Candidates in play: {len(cands)}")
    print(f"{'Candidate':<60s} {'Best phase':<25s} {'P0?':<5s} {'P1?':<5s} {'audit summary':<50s}")
    print("-" * 160)
    last_phase_counts = defaultdict(int)
    for c in cands[-25:]:   # last 25 by mtime
        summary = find_latest_summary(c)
        if summary:
            phases = summary.get("phases", [])
            passed = [p["phase_id"] for p in phases if p["pass"]]
            failed = [p["phase_id"] for p in phases if not p["pass"]]
            best = failed[0] if failed else (passed[-1] if passed else "?")
            last_phase_counts[best] += 1
        else:
            best = "(no receipt)"
        p0, p1, summ = audit_findings_for(c)
        p0_s = "?" if p0 is None else ("YES" if p0 else "no")
        p1_s = "?" if p1 is None else ("YES" if p1 else "no")
        print(f"{c.name:<60s} {best:<25s} {p0_s:<5s} {p1_s:<5s} {(summ or '')[:50]}")
    print(f"\nProposed legos extracted so far: {proposed_legos_count()}")
    print(f"\nDistribution of furthest-phase reached:")
    for ph, n in sorted(last_phase_counts.items(), key=lambda kv: -kv[1])[:10]:
        print(f"  {ph}: {n} candidate(s)")


if __name__ == "__main__":
    main()
