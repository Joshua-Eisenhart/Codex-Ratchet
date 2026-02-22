import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

"""Adversarial batch generator: intentionally triggers each B rejection rule.

Run after a populated state to verify B's enforcement surface.
Each test sends a batch that MUST produce specific rejections.
Reports which rules fired and which didn't.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from b_kernel import BKernel
from state import KernelState
from containers import build_export_block

BOOTPACK = Path(__file__).resolve().parents[3] / "core_docs" / "BOOTPACK_THREAD_B_v3.9.13.md"


def make_kernel():
    return BKernel(str(BOOTPACK))


def make_state_with_term(term="density"):
    """State that has the base MATH_DEF and one admitted term."""
    k = make_kernel()
    s = KernelState()
    s.add_axiom("F01_FINITUDE", "AXIOM_HYP", ["AXIOM_HYP F01_FINITUDE"])
    s.add_axiom("N01_NONCOMMUTATION", "AXIOM_HYP", ["AXIOM_HYP N01_NONCOMMUTATION"])

    block1 = build_export_block("SETUP_001", "A0_BATCH", [
        "PROBE_HYP P001",
        "PROBE_KIND P001 CORR PROBE_HYP",
        "ASSERT P001 CORR EXISTS PROBE_TOKEN PT_P001",
        "SPEC_HYP S_L0_MATH",
        "SPEC_KIND S_L0_MATH CORR MATH_DEF",
        "DEF_FIELD S_L0_MATH CORR OBJECTS finite space",
        "DEF_FIELD S_L0_MATH CORR OPERATIONS operator",
        "DEF_FIELD S_L0_MATH CORR INVARIANTS trace",
        "DEF_FIELD S_L0_MATH CORR DOMAIN hilbert space",
        "DEF_FIELD S_L0_MATH CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_L0_MATH CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_L0_MATH CORR EXISTS MATH_TOKEN MT_S_L0_MATH",
        f'SPEC_HYP S_TERM_{term.upper()}',
        f'SPEC_KIND S_TERM_{term.upper()} CORR TERM_DEF',
        f'REQUIRES S_TERM_{term.upper()} CORR S_L0_MATH',
        f'DEF_FIELD S_TERM_{term.upper()} CORR TERM "{term}"',
        f'DEF_FIELD S_TERM_{term.upper()} CORR BINDS S_L0_MATH',
        f'ASSERT S_TERM_{term.upper()} CORR EXISTS TERM_TOKEN TT_S_TERM_{term.upper()}',
    ])
    k.evaluate_export_block(block1, s)
    return k, s


def run_test(name, block_lines, state, kernel, expected_reason):
    """Send a batch and check that expected_reason appears in rejections."""
    s = KernelState.from_json(state.to_json())
    events = []
    def log_fn(ev):
        events.append(ev)

    block = build_export_block(f"ADV_{name}", "A0_BATCH", block_lines)
    kernel.evaluate_export_block(block, s, log_fn=log_fn)

    reasons = [e.get("reason") for e in events if e.get("event") in ("reject", "park")]
    fired = expected_reason in reasons
    return fired, reasons


def main():
    results = {}

    # --- OVERWRITE: re-propose an already-accepted spec ---
    k, s = make_state_with_term("density")
    fired, reasons = run_test("OVERWRITE", [
        "PROBE_HYP P999",
        "PROBE_KIND P999 CORR PROBE_HYP",
        "ASSERT P999 CORR EXISTS PROBE_TOKEN PT_P999",
        "SPEC_HYP S_L0_MATH",
        "SPEC_KIND S_L0_MATH CORR MATH_DEF",
        "DEF_FIELD S_L0_MATH CORR OBJECTS finite space",
        "DEF_FIELD S_L0_MATH CORR OPERATIONS operator",
        "DEF_FIELD S_L0_MATH CORR INVARIANTS trace",
        "DEF_FIELD S_L0_MATH CORR DOMAIN hilbert space",
        "DEF_FIELD S_L0_MATH CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_L0_MATH CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_L0_MATH CORR EXISTS MATH_TOKEN MT_S_L0_MATH",
    ], s, k, "OVERWRITE")
    results["OVERWRITE"] = fired

    # --- SPEC_KIND_UNSUPPORTED: unsupported spec kind ---
    k2, s2 = make_state_with_term("density")
    fired, reasons = run_test("SPEC_KIND_UNSUPPORTED", [
        "PROBE_HYP P998",
        "PROBE_KIND P998 CORR PROBE_HYP",
        "ASSERT P998 CORR EXISTS PROBE_TOKEN PT_P998",
        "SPEC_HYP S_BAD_KIND",
        "SPEC_KIND S_BAD_KIND CORR CONSTRAINT_DEF",
        "DEF_FIELD S_BAD_KIND CORR OBJECTS finite space",
        "ASSERT S_BAD_KIND CORR EXISTS MATH_TOKEN MT_BAD",
    ], s2, k2, "SPEC_KIND_UNSUPPORTED")
    results["SPEC_KIND_UNSUPPORTED"] = fired

    # --- UNDEFINED_TERM_USE: use a word not in lexeme set ---
    k3, s3 = make_state_with_term("density")
    fired, reasons = run_test("UNDEFINED_TERM_USE", [
        "PROBE_HYP P997",
        "PROBE_KIND P997 CORR PROBE_HYP",
        "ASSERT P997 CORR EXISTS PROBE_TOKEN PT_P997",
        "SPEC_HYP S_BAD_WORD",
        "SPEC_KIND S_BAD_WORD CORR MATH_DEF",
        "REQUIRES S_BAD_WORD CORR S_L0_MATH",
        "DEF_FIELD S_BAD_WORD CORR OBJECTS quasicrystal lattice foobar",
        "DEF_FIELD S_BAD_WORD CORR OPERATIONS operator",
        "DEF_FIELD S_BAD_WORD CORR INVARIANTS trace",
        "DEF_FIELD S_BAD_WORD CORR DOMAIN hilbert space",
        "DEF_FIELD S_BAD_WORD CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_BAD_WORD CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_BAD_WORD CORR EXISTS MATH_TOKEN MT_BAD_WORD",
    ], s3, k3, "UNDEFINED_TERM_USE")
    results["UNDEFINED_TERM_USE"] = fired

    # --- UNDEFINED_LEXEME: compound term with unadmitted component ---
    k4, s4 = make_state_with_term("density")
    fired, reasons = run_test("UNDEFINED_LEXEME", [
        "PROBE_HYP P996",
        "PROBE_KIND P996 CORR PROBE_HYP",
        "ASSERT P996 CORR EXISTS PROBE_TOKEN PT_P996",
        "SPEC_HYP S_TERM_DENSITY_UNKNOWN",
        "SPEC_KIND S_TERM_DENSITY_UNKNOWN CORR TERM_DEF",
        "REQUIRES S_TERM_DENSITY_UNKNOWN CORR S_L0_MATH",
        'DEF_FIELD S_TERM_DENSITY_UNKNOWN CORR TERM "density_unknown"',
        "DEF_FIELD S_TERM_DENSITY_UNKNOWN CORR BINDS S_L0_MATH",
        "ASSERT S_TERM_DENSITY_UNKNOWN CORR EXISTS TERM_TOKEN TT_DENSITY_UNKNOWN",
    ], s4, k4, "UNDEFINED_LEXEME")
    results["UNDEFINED_LEXEME"] = fired

    # --- MISSING_DEPENDENCY: REQUIRES a spec that doesn't exist yet ---
    k5, s5 = make_state_with_term("density")
    fired, reasons = run_test("MISSING_DEPENDENCY", [
        "PROBE_HYP P995",
        "PROBE_KIND P995 CORR PROBE_HYP",
        "ASSERT P995 CORR EXISTS PROBE_TOKEN PT_P995",
        "SPEC_HYP S_DEPENDS_MISSING",
        "SPEC_KIND S_DEPENDS_MISSING CORR MATH_DEF",
        "REQUIRES S_DEPENDS_MISSING CORR S_NONEXISTENT_SPEC",
        "DEF_FIELD S_DEPENDS_MISSING CORR OBJECTS finite space",
        "DEF_FIELD S_DEPENDS_MISSING CORR OPERATIONS operator",
        "DEF_FIELD S_DEPENDS_MISSING CORR INVARIANTS trace",
        "DEF_FIELD S_DEPENDS_MISSING CORR DOMAIN hilbert space",
        "DEF_FIELD S_DEPENDS_MISSING CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_DEPENDS_MISSING CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_DEPENDS_MISSING CORR EXISTS MATH_TOKEN MT_MISSING",
    ], s5, k5, "MISSING_DEPENDENCY")
    results["MISSING_DEPENDENCY"] = fired

    # --- SCHEMA_FAIL: SIM_SPEC with no REQUIRES_EVIDENCE (B enforces this) ---
    k6, s6 = make_state_with_term("density")
    fired, reasons = run_test("SCHEMA_FAIL_SIM_SPEC", [
        "PROBE_HYP P994",
        "PROBE_KIND P994 CORR PROBE_HYP",
        "ASSERT P994 CORR EXISTS PROBE_TOKEN PT_P994",
        "SPEC_HYP S_SIM_NO_EV",
        "SPEC_KIND S_SIM_NO_EV CORR SIM_SPEC",
        "REQUIRES S_SIM_NO_EV CORR S_L0_MATH",
        "ASSERT S_SIM_NO_EV CORR EXISTS EVIDENCE_TOKEN EV_MISSING",
    ], s6, k6, "SCHEMA_FAIL")
    results["SCHEMA_FAIL"] = fired

    # --- PROBE_PRESSURE: too many specs per probe (use unique OBJECTS so no NEAR_REDUNDANT first) ---
    _UNIQUE_OBJECTS = [
        "finite space", "hilbert space", "operator trace", "commutator space",
        "channel operator", "unitary space", "tensor trace", "density operator",
        "generator space", "cptp channel", "lindblad operator", "hamiltonian space",
        "partial trace", "superoperator channel", "anticommutator operator",
        "dimensional space", "finite operator", "hilbert operator", "trace channel",
        "density channel", "space operator", "finite channel", "hilbert trace",
        "unitary trace", "tensor space",
    ]
    k7, s7 = make_state_with_term("density")
    many_specs = []
    for i in range(25):
        obj = _UNIQUE_OBJECTS[i % len(_UNIQUE_OBJECTS)] if i < len(_UNIQUE_OBJECTS) else f"finite space operator {i}"
        many_specs += [
            f"SPEC_HYP S_PRESSURE_{i:03d}",
            f"SPEC_KIND S_PRESSURE_{i:03d} CORR MATH_DEF",
            f"REQUIRES S_PRESSURE_{i:03d} CORR S_L0_MATH",
            f"DEF_FIELD S_PRESSURE_{i:03d} CORR OBJECTS {obj}",
            f"DEF_FIELD S_PRESSURE_{i:03d} CORR OPERATIONS operator",
            f"DEF_FIELD S_PRESSURE_{i:03d} CORR INVARIANTS trace",
            f"DEF_FIELD S_PRESSURE_{i:03d} CORR DOMAIN hilbert space",
            f"DEF_FIELD S_PRESSURE_{i:03d} CORR CODOMAIN hilbert space",
            f"DEF_FIELD S_PRESSURE_{i:03d} CORR SIM_CODE_HASH_SHA256 {'0'*64}",
            f"ASSERT S_PRESSURE_{i:03d} CORR EXISTS MATH_TOKEN MT_{i:03d}",
        ]
    probe_lines = [
        "PROBE_HYP P993",
        "PROBE_KIND P993 CORR PROBE_HYP",
        "ASSERT P993 CORR EXISTS PROBE_TOKEN PT_P993",
    ]
    fired, reasons = run_test("PROBE_PRESSURE", probe_lines + many_specs, s7, k7, "PROBE_PRESSURE")
    results["PROBE_PRESSURE"] = fired

    # --- TERM_DRIFT: redefine existing term with different binds (binds must resolve) ---
    # First add a second MATH_DEF so binds resolves, but binds to wrong spec -> TERM_DRIFT
    k8, s8 = make_state_with_term("density")
    # Add a second valid MATH_DEF to bind to (different from original)
    setup_block = build_export_block("SETUP_DRIFT", "A0_BATCH", [
        "PROBE_HYP P993D",
        "PROBE_KIND P993D CORR PROBE_HYP",
        "ASSERT P993D CORR EXISTS PROBE_TOKEN PT_P993D",
        "SPEC_HYP S_MATH_ALT",
        "SPEC_KIND S_MATH_ALT CORR MATH_DEF",
        "DEF_FIELD S_MATH_ALT CORR OBJECTS hilbert space",
        "DEF_FIELD S_MATH_ALT CORR OPERATIONS operator",
        "DEF_FIELD S_MATH_ALT CORR INVARIANTS trace",
        "DEF_FIELD S_MATH_ALT CORR DOMAIN hilbert space",
        "DEF_FIELD S_MATH_ALT CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_MATH_ALT CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_MATH_ALT CORR EXISTS MATH_TOKEN MT_S_MATH_ALT",
    ])
    k8.evaluate_export_block(setup_block, s8)
    fired, reasons = run_test("TERM_DRIFT", [
        "PROBE_HYP P992",
        "PROBE_KIND P992 CORR PROBE_HYP",
        "ASSERT P992 CORR EXISTS PROBE_TOKEN PT_P992",
        "SPEC_HYP S_TERM_DENSITY_DRIFT",
        "SPEC_KIND S_TERM_DENSITY_DRIFT CORR TERM_DEF",
        "REQUIRES S_TERM_DENSITY_DRIFT CORR S_L0_MATH",
        'DEF_FIELD S_TERM_DENSITY_DRIFT CORR TERM "density"',
        "DEF_FIELD S_TERM_DENSITY_DRIFT CORR BINDS S_MATH_ALT",
        "ASSERT S_TERM_DENSITY_DRIFT CORR EXISTS TERM_TOKEN TT_DRIFT",
    ], s8, k8, "TERM_DRIFT")
    results["TERM_DRIFT"] = fired

    # --- DERIVED_ONLY_PRIMITIVE_USE: use a derived-only word outside quoted context ---
    k9, s9 = make_state_with_term("density")
    fired, reasons = run_test("DERIVED_ONLY", [
        "PROBE_HYP P991",
        "PROBE_KIND P991 CORR PROBE_HYP",
        "ASSERT P991 CORR EXISTS PROBE_TOKEN PT_P991",
        "SPEC_HYP S_DERIVED_FAIL",
        "SPEC_KIND S_DERIVED_FAIL CORR MATH_DEF",
        "REQUIRES S_DERIVED_FAIL CORR S_L0_MATH",
        "DEF_FIELD S_DERIVED_FAIL CORR OBJECTS finite optimize maximize",
        "DEF_FIELD S_DERIVED_FAIL CORR OPERATIONS operator",
        "DEF_FIELD S_DERIVED_FAIL CORR INVARIANTS trace",
        "DEF_FIELD S_DERIVED_FAIL CORR DOMAIN hilbert space",
        "DEF_FIELD S_DERIVED_FAIL CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_DERIVED_FAIL CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_DERIVED_FAIL CORR EXISTS MATH_TOKEN MT_DERIVED",
    ], s9, k9, "DERIVED_ONLY_PRIMITIVE_USE")
    results["DERIVED_ONLY_PRIMITIVE_USE"] = fired

    # --- CIRCULAR_DEPENDENCY: spec requires itself ---
    k10, s10 = make_state_with_term("density")
    fired, reasons = run_test("CIRCULAR_DEPENDENCY", [
        "PROBE_HYP P990",
        "PROBE_KIND P990 CORR PROBE_HYP",
        "ASSERT P990 CORR EXISTS PROBE_TOKEN PT_P990",
        "SPEC_HYP S_CIRCULAR",
        "SPEC_KIND S_CIRCULAR CORR MATH_DEF",
        "REQUIRES S_CIRCULAR CORR S_CIRCULAR",
        "DEF_FIELD S_CIRCULAR CORR OBJECTS finite space",
        "DEF_FIELD S_CIRCULAR CORR OPERATIONS operator",
        "DEF_FIELD S_CIRCULAR CORR INVARIANTS trace",
        "DEF_FIELD S_CIRCULAR CORR DOMAIN hilbert space",
        "DEF_FIELD S_CIRCULAR CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_CIRCULAR CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_CIRCULAR CORR EXISTS MATH_TOKEN MT_CIRCULAR",
    ], s10, k10, "CIRCULAR_DEPENDENCY")
    results["CIRCULAR_DEPENDENCY"] = fired

    # --- UNQUOTED_EQUAL: = sign outside FORMULA field ---
    k11, s11 = make_state_with_term("density")
    fired, reasons = run_test("UNQUOTED_EQUAL", [
        "PROBE_HYP P989",
        "PROBE_KIND P989 CORR PROBE_HYP",
        "ASSERT P989 CORR EXISTS PROBE_TOKEN PT_P989",
        "SPEC_HYP S_EQUAL_FAIL",
        "SPEC_KIND S_EQUAL_FAIL CORR MATH_DEF",
        "REQUIRES S_EQUAL_FAIL CORR S_L0_MATH",
        "DEF_FIELD S_EQUAL_FAIL CORR OBJECTS finite space = hilbert",
        "DEF_FIELD S_EQUAL_FAIL CORR OPERATIONS operator",
        "DEF_FIELD S_EQUAL_FAIL CORR INVARIANTS trace",
        "DEF_FIELD S_EQUAL_FAIL CORR DOMAIN hilbert space",
        "DEF_FIELD S_EQUAL_FAIL CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_EQUAL_FAIL CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_EQUAL_FAIL CORR EXISTS MATH_TOKEN MT_EQUAL_FAIL",
    ], s11, k11, "UNQUOTED_EQUAL")
    results["UNQUOTED_EQUAL"] = fired

    # --- NEAR_REDUNDANT: Jaccard > 0.80 with existing spec ---
    k12, s12 = make_state_with_term("density")
    fired, reasons = run_test("NEAR_REDUNDANT", [
        "PROBE_HYP P988",
        "PROBE_KIND P988 CORR PROBE_HYP",
        "ASSERT P988 CORR EXISTS PROBE_TOKEN PT_P988",
        # S_L0_MATH is already in state — this is nearly identical
        "SPEC_HYP S_L0_MATH_NEAR",
        "SPEC_KIND S_L0_MATH_NEAR CORR MATH_DEF",
        "DEF_FIELD S_L0_MATH_NEAR CORR OBJECTS finite space",
        "DEF_FIELD S_L0_MATH_NEAR CORR OPERATIONS operator",
        "DEF_FIELD S_L0_MATH_NEAR CORR INVARIANTS trace",
        "DEF_FIELD S_L0_MATH_NEAR CORR DOMAIN hilbert space",
        "DEF_FIELD S_L0_MATH_NEAR CORR CODOMAIN hilbert space",
        f"DEF_FIELD S_L0_MATH_NEAR CORR SIM_CODE_HASH_SHA256 {'0'*64}",
        "ASSERT S_L0_MATH_NEAR CORR EXISTS MATH_TOKEN MT_NEAR",
    ], s12, k12, "NEAR_REDUNDANT")
    results["NEAR_REDUNDANT"] = fired

    # --- SHADOW_ATTEMPT: re-propose axiom with different content ---
    k13, s13 = make_state_with_term("density")
    fired, reasons = run_test("SHADOW_ATTEMPT", [
        "PROBE_HYP P987",
        "PROBE_KIND P987 CORR PROBE_HYP",
        "ASSERT P987 CORR EXISTS PROBE_TOKEN PT_P987",
        # F01_FINITUDE is in state.axioms; propose it with different lines
        "AXIOM_HYP F01_FINITUDE",
        "AXIOM_FIELD F01_FINITUDE CORR STATEMENT modified content here",
    ], s13, k13, "SHADOW_ATTEMPT")
    results["SHADOW_ATTEMPT"] = fired

    # --- COMMENT_BAN: comment line in export block ---
    k14, s14 = make_state_with_term("density")
    events_cb = []
    block_cb = build_export_block("ADV_COMMENT", "A0_BATCH", [
        "# this is a comment and should be banned",
        "PROBE_HYP P986",
        "PROBE_KIND P986 CORR PROBE_HYP",
        "ASSERT P986 CORR EXISTS PROBE_TOKEN PT_P986",
    ])
    try:
        k14.evaluate_message(block_cb, s14, log_fn=lambda e: events_cb.append(e))
    except Exception:
        pass
    comment_fired = any(e.get("reason") == "COMMENT_BAN" for e in events_cb)
    results["COMMENT_BAN"] = comment_fired

    # Summary
    print("\n=== ADVERSARIAL TEST RESULTS ===")
    fired_count = sum(1 for v in results.values() if v)
    for rule, fired in sorted(results.items()):
        status = "FIRED ✓" if fired else "DID NOT FIRE ✗"
        print(f"  {rule:35s} {status}")
    print(f"\n{fired_count}/{len(results)} rules verified")
    return 0 if fired_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
