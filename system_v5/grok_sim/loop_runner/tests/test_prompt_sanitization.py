#!/usr/bin/env python3
"""test_prompt_sanitization.py — regression-check that Teacher prompts never leak audit internals.

Builds the Teacher prompt with a deliberately-leaky failure list (raw check ids,
"z > 2σ" thresholds, "Phase 32" mentions, etc.) and asserts none of the forbidden
tokens appear anywhere in the final prompt string.

Run: python3 test_prompt_sanitization.py
Exit code 0 = all assertions pass; 1 = any leak found.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))

import loop_driver as ld


# Tokens that must NEVER appear in a Grok-facing prompt
FORBIDDEN_TOKENS = [
    # Raw check ids (audit-internal naming)
    "factorization_persists",
    "axis_below_threshold_",
    "knn_prime_enrichment",
    "primes_cluster_significant",
    "noncomm_distinguishable",
    "stage_aggregate_uniqueness",
    "cliff_at_position_7",
    "cliff_at_7_strength",
    # Numeric thresholds the hidden harness uses
    "z ≥ 2σ",
    "z > 2σ",
    "z > 2.0σ",
    "Spearman > 0.4",
    "accuracy ≥ 65%",
    "trace_distance > 0.03",
    "L2-distance > 0.03",
    "L2 > 0.05",
    "pairwise L2 > 0.05",
    "berry_phase nonzero (≥ 0.05",
    "efficiency must be > 0.1",
    "invariance_error < 1e-2",
    "z-score = ",
    "lift +",
    "lift ≥",
    "Pearson r = ",
    "Pearson r=",
    # Audit-internal jargon
    "regex",
    "threshold (need",
    "(need ≥",
    "(need ≤",
    "audit harness",
]

# Phase number leakage — "Phase 32", "Phase 42", etc. should never appear in
# the prompt (use human-readable names instead via PHASE_HUMAN_NAMES)
PHASE_NUMBER_PATTERN = re.compile(r"\bPhase\s+\d+\w*\b")

# Common audit-internal phrasings that surface in failure msgs
AUDIT_PHRASES = [
    "fails .*_significant",
    "FAIL \\(",
    "below the .* threshold",
    "(audit observed|hidden audit)",  # we DO mention "hidden audit harness" in
                                       # the doctrine section — so this pattern
                                       # is for the diagnostic body, not the contract
]


def build_leaky_failures():
    """Construct failure dicts that mimic the worst-case audit output."""
    return [
        {
            "check": "primes_cluster_significant",
            "msg": "Prime cluster ratio = 1.0167; random-label null gives 1.0094 ± 0.0760. "
                   "Observed z-score = 0.10σ (need ≥ 2σ for statistical significance). "
                   "Failed Phase 32 threshold.",
        },
        {
            "check": "factorization_persists",
            "msg": "at n=51..200: accuracy 25.2% vs chance 21.6%, lift +0.036. Phase 41's "
                   "signal was sample-size dependent — the factorization geometry collapses "
                   "at larger scale. Threshold (need ≥ 0.05) not met.",
        },
        {
            "check": "stage_aggregate_uniqueness",
            "msg": "only 54/120 = 45.0% of stage-aggregate pairs (16 choose 2 = 120) have "
                   "td > 0.08. Two or more stages are doing semantically the same thing.",
        },
        {
            "check": "cliff_at_position_7",
            "msg": "strongest cliff is at σ_1/σ_2 = 2.325, NOT at position 7 (where ratio = "
                   "1.107). The 'seven axes' claim is a labeling, not a geometric fact about "
                   "the carrier. Spearman > 0.4 threshold also failed via audit regex.",
        },
        {
            "check": "noncomm_distinguishable",
            "msg": "trace distance 0.0001 below threshold of 1e-3; Pearson r = 0.85 with purity.",
        },
    ]


def run_checks():
    """Build a real Teacher prompt with leaky failures, assert no forbidden tokens."""
    leaky_failures = build_leaky_failures()

    # Step 1: sanitize the failure list via the production helper
    sanitized = ld._sanitize_failure_list(leaky_failures)
    print(f"[1/4] Sanitized {len(sanitized)} failures.")

    # Step 2: build the Teacher prompt for a known leaky phase
    public_contract = "## (mock public contract for test — kept minimal)"
    candidate_code = "# (mock candidate code)"
    prompt = ld.build_teacher_prompt(
        public_contract=public_contract,
        candidate_code=candidate_code,
        failures=sanitized,
        metrics={"noncommutation": {"trace_distance": 0.0001}},
        relevant_sims=[],
        iteration=1,
        phase_id="32_axis_cliff",
        phase_summary={"phases": [
            {"phase_id": "00_smoke", "pass": True},
            {"phase_id": "01_axioms", "pass": True},
            {"phase_id": "32_axis_cliff", "pass": False},
        ]},
    )
    print(f"[2/4] Built prompt: {len(prompt)} chars.")

    # Step 3: check for forbidden tokens
    leaks = []
    for tok in FORBIDDEN_TOKENS:
        if tok in prompt:
            leaks.append(tok)

    # Phase number pattern check
    phase_matches = PHASE_NUMBER_PATTERN.findall(prompt)
    if phase_matches:
        # Filter to only matches in the diagnostic body, not in legitimate
        # mentions like "Phase ids" in docs. The Teacher prompt should have NONE.
        for m in phase_matches:
            leaks.append(f"[phase_number_pattern] {m}")

    print(f"[3/4] Found {len(leaks)} leaked token(s).")

    if leaks:
        print(f"\n❌ FAIL — Teacher prompt contains forbidden tokens:")
        for L in leaks:
            print(f"  - {L!r}")
        print("\n=== Prompt body (first 4000 chars) ===")
        print(prompt[:4000])
        return 1

    # Step 4: positive checks — sanitized output STILL communicates the math problem
    must_contain_keywords = [
        "patch request",
        "Public API contract",
        "axis-cliff-structure phase",  # phase mapped to human-readable name
        "Smallest next move",
        "Modify ONLY",  # case-sensitive match against the actual prompt wording
    ]
    missing = [k for k in must_contain_keywords if k not in prompt]
    print(f"[4/4] Checking positive content...")
    if missing:
        print(f"\n❌ FAIL — Teacher prompt is missing expected content:")
        for k in missing:
            print(f"  - {k!r}")
        return 1

    print("\n✓ PASS — Teacher prompt is clean and content-complete.")
    print(f"  - {len(FORBIDDEN_TOKENS)} forbidden tokens checked: none found")
    print(f"  - {len(must_contain_keywords)} required content markers: all present")
    print(f"  - {len(phase_matches)} 'Phase NN' mentions: none (good — uses human names)")
    return 0


def check_sanitize_failure_msg_directly():
    """Direct test of the message sanitization helper."""
    print("\n=== Helper: _sanitize_failure_msg ===")
    cases = [
        ("z-score = 0.10σ (need ≥ 2σ)", ["z-score", "need ≥"]),
        ("Spearman > 0.4 threshold not met", ["Spearman > 0.4"]),
        ("Phase 32 failed", ["Phase 32"]),
        ("audit harness regex flagged this", ["regex", "harness"]),
        ("Pearson r = 0.85 with purity", ["Pearson r = "]),
    ]
    failures = []
    for raw, must_not_contain in cases:
        out = ld._sanitize_failure_msg(raw)
        bad = [t for t in must_not_contain if t in out]
        if bad:
            print(f"  ❌ {raw!r} → {out!r}  (still contains: {bad})")
            failures.append(raw)
        else:
            print(f"  ✓ {raw!r} → {out!r}")
    return 0 if not failures else 1


def test_sanitize_failure_msg_directly():
    assert check_sanitize_failure_msg_directly() == 0


def check_phase_human_name_mapping():
    """Every contract in contracts/ should have a human name, OR fall through to generic."""
    print("\n=== Helper: PHASE_HUMAN_NAMES coverage ===")
    contracts_dir = HERE.parent / "contracts"
    if not contracts_dir.exists():
        print("  (no contracts dir — skipping)")
        return 0
    missing = []
    for cf in sorted(contracts_dir.glob("phase_*.py")):
        pid = cf.stem.replace("phase_", "")
        if pid not in ld.PHASE_HUMAN_NAMES:
            missing.append(pid)
    if missing:
        print(f"  ⚠ {len(missing)} phase id(s) missing from PHASE_HUMAN_NAMES (will use generic):")
        for m in missing[:8]:
            print(f"    - {m}")
        # Not a hard fail — generic fallback is OK, just a warning
    else:
        print(f"  ✓ All {sum(1 for _ in contracts_dir.glob('phase_*.py'))} contracts have human names.")
    return 0


def test_phase_human_name_mapping():
    assert check_phase_human_name_mapping() == 0


if __name__ == "__main__":
    print("=" * 70)
    print("Prompt sanitization regression test")
    print("=" * 70)
    rc1 = run_checks()
    rc2 = check_sanitize_failure_msg_directly()
    rc3 = check_phase_human_name_mapping()
    rc = max(rc1, rc2, rc3)
    print(f"\n{'=' * 70}\nOverall: {'PASS' if rc == 0 else 'FAIL'}")
    sys.exit(rc)
