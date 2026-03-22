"""
memory_admission_guard.py
A2 Skill: S3 — Memory Admission Guard

Purpose:
    Audit a candidate file/artifact before it is appended to A2 or A1 active memory surfaces.
    Enforces the rules in SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md.

Usage:
    python3 memory_admission_guard.py --file path/to/artifact.md [--layer A2|A1]

Exit codes:
    0 = ADMITTED
    1 = REJECTED (prints reason)
    2 = NEEDS_REVIEW (demote to RUNTIME_ONLY or ARCHIVE_ONLY)
"""

import argparse
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Surface class definitions (from SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES)
# ---------------------------------------------------------------------------

SURFACE_CLASSES = {
    "SOURCE_CORPUS",
    "DERIVED_A2",
    "PROPOSAL_A1",
    "PACKAGED_A0",
    "EVIDENCE_SIM",
    "EARNED_STATE",
    "RUNTIME_ONLY",
    "ARCHIVE_ONLY",
}

# Write permissions per layer
LAYER_WRITE_PERMISSIONS = {
    "A2": {"DERIVED_A2"},
    "A1": {"PROPOSAL_A1"},
    "A0": {"PACKAGED_A0"},
    "B":  {"EARNED_STATE"},
    "SIM": {"EVIDENCE_SIM"},
}

# Fake canon labels that are NOT equivalent to lower-loop EARNED_STATE
FAKE_CANON_LABELS = [
    "CANON",
    "CANONICAL",
    "SOLE_SOURCE_OF_TRUTH",
    "Canon-Installed",
    "CANONICAL_TRUTH",
    "GROUND_TRUTH",
]

# Narrative smoothing signals (LLM drift markers)
NARRATIVE_SMOOTHING_SIGNALS = [
    "therefore we can conclude",
    "it is now proven",
    "this confirms definitively",
    "no contradictions remain",
    "this resolves the tension",
    "we have now established",
    "the system now knows",
]


@dataclass
class AdmissionResult:
    admitted: bool
    needs_review: bool
    reasons: list[str]
    surface_class_found: Optional[str]

    @property
    def exit_code(self) -> int:
        if self.admitted:
            return 0
        if self.needs_review:
            return 2
        return 1

    def report(self):
        status = "ADMITTED" if self.admitted else ("NEEDS_REVIEW" if self.needs_review else "REJECTED")
        print(f"\n=== MEMORY ADMISSION GUARD RESULT: {status} ===")
        if self.surface_class_found:
            print(f"Surface class detected: {self.surface_class_found}")
        else:
            print("Surface class: NOT FOUND")
        if self.reasons:
            print("\nFindings:")
            for r in self.reasons:
                print(f"  - {r}")
        print()


def detect_surface_class(content: str) -> Optional[str]:
    """Scan for a declared surface class in the file content."""
    # Matches patterns like: Status: DERIVED_A2, Surface Class: PROPOSAL_A1, etc.
    for cls in SURFACE_CLASSES:
        pattern = rf'\b{re.escape(cls)}\b'
        if re.search(pattern, content):
            return cls
    return None


def check_fake_canon(content: str) -> list[str]:
    """Flag any fake canon labels that could elevate the surface above its class."""
    hits = []
    for label in FAKE_CANON_LABELS:
        if label.lower() in content.lower():
            hits.append(f"Fake canon label detected: '{label}' — document-local authority does not confer EARNED_STATE.")
    return hits


def check_narrative_smoothing(content: str) -> list[str]:
    """Detect narrative smoothing / contradiction collapse language."""
    hits = []
    content_lower = content.lower()
    for signal in NARRATIVE_SMOOTHING_SIGNALS:
        if signal in content_lower:
            hits.append(f"Narrative smoothing signal: '{signal}'")
    return hits


def check_unverified_claims(content: str) -> list[str]:
    """Warn if there are factual claims without UNVERIFIED or source locator."""
    # Look for assertion language without source tags
    assertion_patterns = [
        r'\bproven\b',
        r'\bestablished\b',
        r'\bconfirmed\b',
        r'\bconcluded\b',
    ]
    hits = []
    for pat in assertion_patterns:
        matches = re.findall(pat, content, re.IGNORECASE)
        if matches:
            hits.append(
                f"Unsourced assertion pattern '{pat}' found {len(matches)}x — "
                "verify each is labeled UNVERIFIED or carries a source locator."
            )
    return hits


def audit_file(filepath: str, target_layer: str = "A2") -> AdmissionResult:
    path = Path(filepath)
    if not path.exists():
        return AdmissionResult(
            admitted=False,
            needs_review=False,
            reasons=[f"File not found: {filepath}"],
            surface_class_found=None,
        )

    content = path.read_text(encoding="utf-8", errors="replace")
    reasons: list[str] = []
    needs_review = False

    # 1. Surface class check
    surface_class = detect_surface_class(content)
    if surface_class is None:
        reasons.append("No explicit surface class declared. Admission requires an explicit class label.")
        needs_review = True

    # 2. Write permission check
    if surface_class and target_layer in LAYER_WRITE_PERMISSIONS:
        allowed = LAYER_WRITE_PERMISSIONS[target_layer]
        if surface_class not in allowed:
            reasons.append(
                f"Layer '{target_layer}' may NOT write surface class '{surface_class}'. "
                f"Allowed: {allowed}."
            )
            return AdmissionResult(admitted=False, needs_review=False, reasons=reasons, surface_class_found=surface_class)

    # 3. Fake canon label check
    fake_canon_hits = check_fake_canon(content)
    if fake_canon_hits:
        reasons.extend(fake_canon_hits)
        needs_review = True

    # 4. Narrative smoothing check
    smoothing_hits = check_narrative_smoothing(content)
    if smoothing_hits:
        reasons.extend(smoothing_hits)
        needs_review = True

    # 5. Unverified claim check (advisory only)
    unverified_hits = check_unverified_claims(content)
    if unverified_hits:
        reasons.extend(unverified_hits)
        # Advisory — does not block admission, but flags for review

    admitted = not needs_review and not any(
        "may NOT write" in r or "not found" in r.lower() for r in reasons
    )

    return AdmissionResult(
        admitted=admitted,
        needs_review=needs_review,
        reasons=reasons,
        surface_class_found=surface_class,
    )


def main():
    parser = argparse.ArgumentParser(
        description="A2 Memory Admission Guard — audit a file before appending to A2/A1 brain surfaces."
    )
    parser.add_argument("--file", required=True, help="Path to the candidate artifact file.")
    parser.add_argument("--layer", default="A2", choices=["A2", "A1", "A0", "B", "SIM"],
                        help="Target layer to write to (default: A2).")
    args = parser.parse_args()

    result = audit_file(args.file, args.layer)
    result.report()
    sys.exit(result.exit_code)


if __name__ == "__main__":
    main()
