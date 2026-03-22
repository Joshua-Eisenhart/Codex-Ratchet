"""
a1_distiller.py
A2 Skill: S2 — A1-from-A2 Distillation

Purpose:
    Derive proposal-only A1 outputs from a refreshed A2 input surface.
    Enforces the A2->A1 lean handoff rules from A2_TO_A1_DISTILLATION_INPUTS__v1.md:
      - A1 inputs must be sourced from the refreshed A2 distillation surface only.
      - No direct source-corpus -> A1 shortcuts.
      - Output is PROPOSAL_A1 class only — never EARNED_STATE or SOURCE_CORPUS.
      - Traceability to the A2 source surface is mandatory.

Usage:
    python3 a1_distiller.py --a2_input PATH --output PATH [--dry-run]

Output:
    A1_DISTILLED_INPUT__<date>__v1.md — a bounded A1 launch fuel package (PROPOSAL_A1 class).
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# A1 target family names from A2_TO_A1_DISTILLATION_INPUTS__v1
# ---------------------------------------------------------------------------

A1_TARGET_FAMILIES = [
    "loop geometry and layer-boundary candidates",
    "entropy-language formalization candidates",
    "entropy-processing machine families",
    "classical engine residue families",
    "sim-capable substrate families",
    "geometric constraint manifold families",
    "attractor families",
    "axis candidates inside candidate substrates",
    "graveyard rescue operators",
    "overlay-to-kernel translation surfaces",
    "anti-classical boundary candidates",
]

# Keywords that signal direct-source bypass (forbidden in A1 inputs)
FORBIDDEN_BYPASS_SIGNALS = [
    "directly from source",
    "taken from source corpus",
    "copied from docs",
    "ingested directly",
    "raw source content",
]

# Required sections in a valid A2->A1 handoff fuel package
REQUIRED_SECTIONS = [
    "A1 Role Reminder",
    "Target Families",
    "Negative Classes",
    "Rescue / Graveyard Focus",
    "SIM Hooks",
]


def validate_a2_input(a2_input_path: Path) -> tuple[bool, list[str]]:
    """Validate that the A2 input surface is a proper DERIVED_A2 class document."""
    issues = []
    if not a2_input_path.exists():
        return False, [f"A2 input file not found: {a2_input_path}"]

    content = a2_input_path.read_text(encoding="utf-8", errors="replace")

    # Must declare DERIVED_A2 class
    if "DERIVED_A2" not in content and "NONCANONICAL" not in content:
        issues.append(
            "A2 input does not declare DERIVED_A2 or NONCANONICAL status. "
            "Direct source corpus documents cannot feed A1 without A2 distillation."
        )

    # Check for forbidden bypass signals
    for signal in FORBIDDEN_BYPASS_SIGNALS:
        if signal.lower() in content.lower():
            issues.append(f"Forbidden bypass signal detected: '{signal}'")

    return len(issues) == 0, issues


def extract_target_families(content: str) -> list[str]:
    """Extract any explicitly named target family concepts from the A2 input."""
    found = []
    for family in A1_TARGET_FAMILIES:
        if family.lower() in content.lower():
            found.append(family)
    return found


def extract_negative_classes(content: str) -> list[str]:
    """Extract negative class markers (CLASSICAL_TIME, PRIMITIVE_PROBABILITY, etc.)."""
    pattern = r'\b(PRIMITIVE_\w+|CLASSICAL_\w+|EUCLIDEAN_\w+|COMMUTATIVE_\w+|CONTINUOUS_\w+|INFINITE_\w+|NARRATIVE_\w+|KERNEL_VALID_BUT_\w+)\b'
    hits = list(set(re.findall(pattern, content)))
    return sorted(hits)


def build_a1_package(a2_input_path: Path, target_families: list[str],
                     negative_classes: list[str], output_dir: Path,
                     dry_run: bool) -> str:
    """Emit the A1 distilled input package as a PROPOSAL_A1 surface."""
    date_str = datetime.now().strftime("%Y_%m_%d")
    filename = f"A1_DISTILLED_INPUT__{date_str}__v1.md"
    filepath = output_dir / filename

    lines = [
        f"# A1_DISTILLED_INPUT__{date_str}__v1",
        "Surface Class: PROPOSAL_A1",
        f"Date: {datetime.now().strftime('%Y-%m-%d')}",
        f"Source: {a2_input_path.name} (DERIVED_A2 — A2 distillation pass)",
        "Role: Proposal-only A1 fuel. Not canon. Not earned state.",
        "",
        "## A1 Role Reminder",
        "A1 is the executable proposal layer.",
        "A1 emits proposals only — never canon, never earned state.",
        "All content below is sourced from a validated A2 distillation surface.",
        "Traceability to the A2 source is required before any lower-loop forwarding.",
        "",
        "## Target Families (extracted from A2 input)",
        *([f"- {f}" for f in target_families] if target_families else ["- (none extracted — manual review required)"]),
        "",
        "## Negative Classes (extracted from A2 input)",
        *([f"- {nc}" for nc in negative_classes] if negative_classes else ["- (none extracted)"]),
        "",
        "## Rescue / Graveyard Focus",
        "A1 must explicitly target:",
        "- rescue from killed branch families",
        "- rescue from classical-smuggling failure classes",
        "- rescue from model-empty but kernel-valid families",
        "- rescue with graveyard-cluster awareness",
        "",
        "## SIM Hooks",
        "Each family should anticipate: BASELINE, BOUNDARY_SWEEP, PERTURBATION, ADVERSARIAL_NEG, COMPOSITION_STRESS",
        "",
        "## Required Campaign Shape",
        "Each concept family must include:",
        "- primary branch",
        "- explicit negative branch",
        "- rescue branch",
        "- expected failure modes",
        "- lineage back to this A1_DISTILLED_INPUT surface",
        "",
        "## Lean Handoff Rule (from A2_TO_A1_DISTILLATION_INPUTS__v1)",
        "A1 inherits from this package only.",
        "A1 does NOT inherit: broad same-scope A2 note stacks, raw thread residues, or helper ingest packs.",
        "",
    ]

    content = "\n".join(lines)
    if not dry_run:
        filepath.write_text(content, encoding="utf-8")
        print(f"[EMITTED] {filepath}")
    else:
        print(f"[DRY-RUN] Would emit: {filepath}")
        print(content)

    return filename


def main():
    parser = argparse.ArgumentParser(
        description="A1 Distiller — derive bounded A1 fuel from a validated A2 input surface."
    )
    parser.add_argument("--a2_input", required=True,
                        help="Path to the A2 distillation input file (must be DERIVED_A2 class).")
    parser.add_argument("--output", default="system_v3/a2_state",
                        help="Output directory for the A1 distilled package.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print output to stdout without writing files.")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent
    a2_input_path = Path(args.a2_input).resolve()
    output_path = (repo_root / args.output).resolve()

    print(f"[A1 DISTILLER] Validating A2 input: {a2_input_path}")

    valid, issues = validate_a2_input(a2_input_path)
    if not valid:
        print("\n[REJECTED] A2 input validation failed:", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)
        sys.exit(1)

    print("[OK] A2 input validated.")

    content = a2_input_path.read_text(encoding="utf-8", errors="replace")
    target_families = extract_target_families(content)
    negative_classes = extract_negative_classes(content)

    print(f"  Target families extracted: {len(target_families)}")
    print(f"  Negative classes extracted: {len(negative_classes)}")

    build_a1_package(a2_input_path, target_families, negative_classes, output_path, args.dry_run)

    print("\n[RESULT] A1 distilled package emitted. A1 may now load this surface as bounded fuel.")
    sys.exit(0)


if __name__ == "__main__":
    main()
