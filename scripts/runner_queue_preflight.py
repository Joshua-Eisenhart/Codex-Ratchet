#!/usr/bin/env python3
"""Fail-closed queue preflight before launching parallel sim runners."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


LATE_STAGE_RE = re.compile(
    r"(tier_d|boundary_flux|bridge|coupling|pairwise|coexistence|rho_ab|phi0|kernel|"
    r"emergence|axis|axis0|bipartite|partial_trace|entanglement|mutual_information|"
    r"mutual_info|coherent_information|coherent_info|concurrence|negativity|schmidt|"
    r"entropy|capacity|capacities|carnot|szilard|landauer|thermo|engine|qit|nonclassical)",
    re.I,
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def load_gate(root: Path) -> dict[str, Any]:
    path = root / "system_v5" / "ops" / "stage_gate.json"
    if not path.exists():
        return {"active_stage": None, "allow_default_queue_late_stage": False, "allow_tier_d_launch": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "active_stage": payload.get("active_stage"),
        "allow_default_queue_late_stage": payload.get("allow_default_queue_late_stage") is True,
        "allow_tier_d_launch": payload.get("allow_tier_d_launch") is True,
    }


def rows(path: Path) -> list[str]:
    if not path.exists():
        return []
    out: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        item = line.strip()
        if item and not item.startswith("#"):
            out.append(item)
    return out


def claim_for_row(row: str) -> str | None:
    low = row.lower()
    stem = Path(low).stem
    if stem.startswith("classical_baseline_"):
        return None
    if "tier_d" in low or "boundary_flux" in low:
        return "tier_d"
    if any(token in low for token in ("bridge", "coupling", "pairwise", "coexistence", "rho_ab", "phi0", "kernel", "emergence", "engine", "qit", "nonclassical")):
        return "scientific_coupling"
    if "axis" in low:
        return "axis"
    if LATE_STAGE_RE.search(low):
        return "default_late_stage"
    return None


def _direct_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(item for item in path.iterdir() if item.is_file())


def _queue_files(path: Path) -> list[Path]:
    return [item for item in _direct_files(path) if item.match("*.json*")]


def _junk_files(path: Path) -> list[Path]:
    return [item for item in _direct_files(path) if not item.match("*.json*")]


def atomic_queue_counts(root: Path) -> dict[str, int]:
    queue_root = root / "system_v4" / "probes" / "a2_state" / "queue"
    return {
        "claimed": len(_queue_files(queue_root / "claimed")),
        "blocked": len(_queue_files(queue_root / "blocked")),
        "done": len(_queue_files(queue_root / "done")),
    }


def atomic_queue_junk_counts(root: Path) -> dict[str, int]:
    queue_root = root / "system_v4" / "probes" / "a2_state" / "queue"
    return {
        "root": len(_junk_files(queue_root)),
        "lane_A": len(_junk_files(queue_root / "lane_A")),
        "lane_B": len(_junk_files(queue_root / "lane_B")),
        "claimed": len(_junk_files(queue_root / "claimed")),
        "blocked": len(_junk_files(queue_root / "blocked")),
        "done": len(_junk_files(queue_root / "done")),
    }


def audit(root: Path | None = None) -> dict[str, Any]:
    root = root or repo_root()
    ops = root / "system_v5" / "ops"
    gate = load_gate(root)
    atomics = atomic_queue_counts(root)
    atomic_junk = atomic_queue_junk_counts(root)
    findings: list[dict[str, Any]] = []

    if atomics["claimed"]:
        queue_root = root / "system_v4" / "probes" / "a2_state" / "queue"
        findings.append(
            {
                "kind": "atomic_claimed_queue_not_empty",
                "queue": "system_v4/probes/a2_state/queue/claimed",
                "count": atomics["claimed"],
                "sample": [
                    str(path.relative_to(root))
                    for path in _queue_files(queue_root / "claimed")[:5]
                ],
            }
        )

    blocked_default = 0
    if not gate.get("allow_default_queue_late_stage"):
        for row in rows(ops / "queue_default.txt"):
            claim = claim_for_row(row)
            if claim:
                blocked_default += 1
                findings.append(
                    {
                        "kind": "default_queue_late_stage_blocked",
                        "queue": "system_v5/ops/queue_default.txt",
                        "row": row,
                        "claim": claim,
                    }
                )

    blocked_priority = 0
    for rel in ("queue_tier_a.txt", "queue_tier_b.txt"):
        queue = ops / rel
        for row in rows(queue):
            claim = claim_for_row(row)
            if claim in {"scientific_coupling", "axis", "tier_d", "default_late_stage"}:
                blocked_priority += 1
                findings.append(
                    {
                        "kind": "priority_queue_stage_gate_blocked",
                        "queue": f"system_v5/ops/{rel}",
                        "row": row,
                        "claim": claim,
                    }
                )

    return {
        "all_pass": not findings,
        "active_stage": gate.get("active_stage"),
        "atomic_queue_counts": atomics,
        "atomic_queue_junk_counts": atomic_junk,
        "blocked_default_queue_count": blocked_default,
        "blocked_stage_gate_queue_count": blocked_priority,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(repo_root()))
    args = parser.parse_args()
    report = audit(Path(args.repo_root))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
