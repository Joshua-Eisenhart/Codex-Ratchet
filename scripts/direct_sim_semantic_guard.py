#!/usr/bin/env python3
"""Fail closed on direct sim names that contain claim-layer labels."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROBES_DIR = REPO_ROOT / "system_v4" / "probes"
BYPASS_SENTINEL = REPO_ROOT / "system_v5" / "ops" / "wizard_admissions" / "direct_sim_semantic_guard_bypass.ok"

CLAIM_LABEL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("axis", re.compile(r"^axis\d*$")),
    ("axes", re.compile(r"^axes$")),
    ("ax", re.compile(r"^ax\d+$")),
    ("bridge", re.compile(r"^bridge$")),
    ("qit", re.compile(r"^qit$")),
    ("gstack", re.compile(r"^gstack$")),
    ("engine", re.compile(r"^engine$")),
    ("type1", re.compile(r"^type1$")),
    ("type2", re.compile(r"^type2$")),
    ("rosetta", re.compile(r"^rosetta$")),
    ("nonclassical", re.compile(r"^nonclassical$")),
    ("holodeck", re.compile(r"^holodeck$")),
    ("leviathan", re.compile(r"^leviathan$")),
    ("iching", re.compile(r"^iching$")),
    ("igt", re.compile(r"^igt$")),
    ("fep", re.compile(r"^fep$")),
)

CLAIM_PHRASE_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("flux_to_pauli", ("flux", "to", "pauli")),
)


def split_tokens(name: str) -> list[str]:
    return [token for token in re.split(r"[^A-Za-z0-9]+", name.lower()) if token]


def matched_claim_labels(name: str) -> list[str]:
    tokens = split_tokens(name)
    matches: list[str] = []
    for label, pattern in CLAIM_LABEL_PATTERNS:
        if any(pattern.match(token) for token in tokens):
            matches.append(label)
    for label, phrase in CLAIM_PHRASE_PATTERNS:
        for idx in range(0, len(tokens) - len(phrase) + 1):
            if tuple(tokens[idx : idx + len(phrase)]) == phrase:
                matches.append(label)
                break
    return matches


def bypass_allowed() -> bool:
    return os.environ.get("ALLOW_DIRECT_SIM_CLAIM_LABELS") == "1" and BYPASS_SENTINEL.exists()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Sim basename without .py")
    parser.add_argument(
        "--probes-dir",
        default=str(DEFAULT_PROBES_DIR),
        help="Directory containing direct executable sim files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    name = args.name

    if any(part in name for part in ("/", "\\", "..")):
        print(f"DIRECT SIM SEMANTIC GUARD FAILED name={name}")
        print("invalid sim basename")
        return 2

    sim_path = Path(args.probes_dir) / f"{name}.py"
    if not sim_path.exists():
        print(f"DIRECT SIM SEMANTIC GUARD FAILED name={name}")
        print(f"missing sim: {sim_path}")
        return 2

    matches = matched_claim_labels(name)
    if not matches:
        print(f"DIRECT SIM SEMANTIC GUARD PASSED name={name}")
        return 0

    if bypass_allowed():
        print(f"DIRECT SIM SEMANTIC GUARD BYPASSED name={name}")
        print(f"matched_claim_labels={','.join(matches)}")
        print(f"sentinel={BYPASS_SENTINEL.relative_to(REPO_ROOT)}")
        return 0

    print(f"DIRECT SIM SEMANTIC GUARD FAILED name={name}")
    print(f"matched_claim_labels={','.join(matches)}")
    print("direct executable sim names must describe the concrete math object or calibration cycle")
    print("rename or quarantine before use; do not encode claim-layer labels in executable sim basenames")
    print(
        "recovery bypass requires ALLOW_DIRECT_SIM_CLAIM_LABELS=1 and "
        f"{BYPASS_SENTINEL.relative_to(REPO_ROOT)}"
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
