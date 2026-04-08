#!/usr/bin/env python3
"""
PARTIAL TRACE EINSUM AUDIT
==========================
Sweeps all probe files for einsum-based partial trace patterns.
Tests each pattern against a known Bell state: Tr_B(|Bell><Bell|) = I/2.

Bug origin: sim_torch_axis0_gradient.py had 'aibj->ij' (wrong, sums a,b
independently) vs 'aiaj->ij' (correct, traces subsystem A).

Classification: audit
Output: system_v4/probes/a2_state/sim_results/partial_trace_audit_results.json
"""

import json
import os
import sys
import re
import numpy as np
from pathlib import Path
from datetime import datetime

# =====================================================================
# CONSTANTS
# =====================================================================

PROBES_DIR = Path(__file__).parent
RESULTS_DIR = PROBES_DIR / "a2_state" / "sim_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Bell state |Phi+> = (|00> + |11>) / sqrt(2)
BELL_KET = np.array([1, 0, 0, 1], dtype=np.complex128) / np.sqrt(2)
BELL_RHO = np.outer(BELL_KET, BELL_KET.conj())  # 4x4

# Correct answer: Tr_B(|Bell><Bell|) = I/2
EXPECTED_PARTIAL_TRACE = np.eye(2, dtype=np.complex128) / 2.0

# GHZ state |000> + |111> / sqrt(2) for 3-qubit tests
GHZ_KET = np.zeros(8, dtype=np.complex128)
GHZ_KET[0] = 1.0 / np.sqrt(2)
GHZ_KET[7] = 1.0 / np.sqrt(2)
GHZ_RHO = np.outer(GHZ_KET, GHZ_KET.conj())  # 8x8

# Expected: Tr_BC(|GHZ><GHZ|) = diag(1/2, 0, 0, 0, 0, 0, 0, 1/2) -> 2x2: diag(1/2, 1/2) = I/2
# Tr_A(|GHZ><GHZ|) = 4x4 with [0,0]=1/2, [0,7]=1/2... actually:
# Tr_A: reshape (2,4,2,4), contract A -> 4x4
# |GHZ> = |0>|00> + |1>|11>, so Tr_A = |00><00|/2 + |11><11|/2
EXPECTED_GHZ_TRA = np.zeros((4, 4), dtype=np.complex128)
EXPECTED_GHZ_TRA[0, 0] = 0.5
EXPECTED_GHZ_TRA[3, 3] = 0.5

TOL = 1e-10


# =====================================================================
# EINSUM PATTERN REGISTRY -- all patterns found in codebase
# =====================================================================

def test_einsum_pattern_2qubit(pattern_str, reshape_order, label):
    """
    Test a 2-qubit einsum partial trace pattern against Bell state.

    Args:
        pattern_str: e.g. 'aiaj->ij', 'ijik->jk', 'aibj->ij'
        reshape_order: tuple of dims, e.g. (2,2,2,2)
        label: human-readable label

    Returns:
        dict with test results
    """
    rho_r = BELL_RHO.reshape(reshape_order)
    try:
        result = np.einsum(pattern_str, rho_r)
    except Exception as e:
        return {
            "pattern": pattern_str,
            "reshape": list(reshape_order),
            "label": label,
            "error": str(e),
            "pass": False,
            "bug_type": "einsum_error"
        }

    # For Bell state, BOTH Tr_A and Tr_B should give I/2
    # So any correct partial trace of a Bell state gives I/2
    diff = np.max(np.abs(result - EXPECTED_PARTIAL_TRACE))
    trace_val = np.real(np.trace(result))
    is_hermitian = np.allclose(result, result.conj().T, atol=TOL)
    is_psd = np.all(np.linalg.eigvalsh(result) >= -TOL)
    trace_one = abs(trace_val - 1.0) < TOL
    matches_half_I = diff < TOL

    return {
        "pattern": pattern_str,
        "reshape": list(reshape_order),
        "label": label,
        "result_shape": list(result.shape),
        "trace": float(trace_val),
        "hermitian": bool(is_hermitian),
        "psd": bool(is_psd),
        "trace_one": bool(trace_one),
        "matches_I_over_2": bool(matches_half_I),
        "max_diff_from_I_over_2": float(diff),
        "pass": bool(matches_half_I and trace_one and is_hermitian and is_psd),
        "bug_type": None if matches_half_I else "wrong_contraction"
    }


def test_einsum_pattern_3qubit(pattern_str, reshape_order, expected, label):
    """Test a 3-qubit einsum partial trace pattern against GHZ state."""
    rho_r = GHZ_RHO.reshape(reshape_order)
    try:
        result = np.einsum(pattern_str, rho_r)
    except Exception as e:
        return {
            "pattern": pattern_str,
            "reshape": list(reshape_order),
            "label": label,
            "error": str(e),
            "pass": False,
            "bug_type": "einsum_error"
        }

    diff = np.max(np.abs(result - expected))
    trace_val = np.real(np.trace(result))
    is_hermitian = np.allclose(result, result.conj().T, atol=TOL)
    expected_trace = np.real(np.trace(expected))

    return {
        "pattern": pattern_str,
        "reshape": list(reshape_order),
        "label": label,
        "result_shape": list(result.shape),
        "trace": float(trace_val),
        "expected_trace": float(expected_trace),
        "hermitian": bool(is_hermitian),
        "max_diff": float(diff),
        "pass": bool(diff < TOL),
        "bug_type": None if diff < TOL else "wrong_contraction"
    }


# =====================================================================
# FILE SCANNER
# =====================================================================

def scan_file_for_einsum_patterns(filepath):
    """Extract all einsum calls from a Python file."""
    patterns_found = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
    except Exception:
        return patterns_found

    # Match einsum('pattern', ...) or einsum("pattern", ...)
    einsum_re = re.compile(r"""einsum\s*\(\s*['"]([\w>-]+)['"]\s*,""")

    for i, line in enumerate(lines, 1):
        for m in einsum_re.finditer(line):
            pat = m.group(1)
            # Only care about partial-trace-like patterns (4-index input, 2-index output)
            if '->' in pat:
                inp, out = pat.split('->')
                if len(inp) == 4 and len(out) == 2:
                    patterns_found.append({
                        "file": str(filepath.relative_to(PROBES_DIR)),
                        "line": i,
                        "pattern": pat,
                        "line_text": line.strip()
                    })
    return patterns_found


def classify_einsum_pattern(pattern):
    """
    Classify a 4->2 einsum pattern as correct or buggy for partial trace.

    For reshape (d_A, d_B, d_A, d_B) with indices (0,1,2,3):
    Correct patterns contract SAME letter at positions (0,2) or (1,3).

    Bug pattern: 'aibj->ij' contracts a(0) and b(2) as DIFFERENT indices.
    """
    inp, out = pattern.split('->')

    # Build index map: which positions share the same letter
    idx_map = {}
    for pos, ch in enumerate(inp):
        if ch not in idx_map:
            idx_map[ch] = []
        idx_map[ch].append(pos)

    # Contracted indices: appear in input but not output
    contracted = [ch for ch in idx_map if ch not in out]
    kept = [ch for ch in idx_map if ch in out]

    # For valid partial trace: each contracted index should appear exactly
    # at positions (0,2) or (1,3) [i.e., same row/col subsystem]
    valid_contraction_pairs = [{0, 2}, {1, 3}]

    issues = []
    for ch in contracted:
        positions = set(idx_map[ch])
        if len(idx_map[ch]) != 2:
            issues.append(f"index '{ch}' appears {len(idx_map[ch])} times (need exactly 2)")
        elif positions not in valid_contraction_pairs:
            issues.append(
                f"index '{ch}' at positions {sorted(positions)} -- "
                f"must be (0,2) or (1,3) for valid partial trace"
            )

    # Also check: only one contracted index letter (partial trace sums ONE subsystem)
    if len(contracted) != 1:
        # Could be valid if two letters both map to same subsystem pair
        # e.g., 'aibj->ij' has a->pos0, b->pos2, i->pos1, j->pos3
        # a and b are different letters at positions 0,2 -- this means they're
        # summed INDEPENDENTLY, which is WRONG for partial trace
        if len(contracted) == 2:
            all_contracted_positions = set()
            for ch in contracted:
                all_contracted_positions.update(idx_map[ch])
            if all_contracted_positions == {0, 2} or all_contracted_positions == {1, 3}:
                issues.append(
                    f"TWO different contracted indices {contracted} at positions "
                    f"{sorted(all_contracted_positions)} -- sums independently, "
                    f"not a valid trace (must use SAME index letter)"
                )

    return {
        "pattern": pattern,
        "contracted": contracted,
        "kept": kept,
        "is_valid_partial_trace": len(issues) == 0,
        "issues": issues
    }


# =====================================================================
# TARGETED FILE AUDITS
# =====================================================================

PRIORITY_FILES = [
    "sim_torch_mutual_info.py",
    "sim_torch_quantum_discord.py",
    "sim_torch_axis0_gradient.py",
    "sim_torch_axis0_3qubit.py",
    "sim_torch_cnot.py",
]

KNOWN_EINSUM_PATTERNS_2Q = [
    # (pattern, reshape, label, expected_correct)
    ("aiaj->ij", (2, 2, 2, 2), "trace_A_correct", True),
    ("aibj->ij", (2, 2, 2, 2), "trace_A_WRONG_independent_sum", False),
    ("ijik->jk", (2, 2, 2, 2), "trace_A_alt_correct", True),
    ("ijkj->ik", (2, 2, 2, 2), "trace_B_correct", True),
    ("iaja->ij", (2, 2, 2, 2), "trace_B_alt_correct", True),
    ("jiki->jk", (2, 2, 2, 2), "trace_B_via_jiki_correct", True),
]

KNOWN_EINSUM_PATTERNS_3Q = [
    # (pattern, reshape, expected_result, label)
    ("aiaj->ij", (2, 4, 2, 4), EXPECTED_GHZ_TRA, "3q_trace_A_correct"),
    ("iaja->ij", (4, 2, 4, 2),
     np.diag([0.5, 0.5]).astype(np.complex128),  # Tr_C of GHZ = |00><00|/2 + |11><11|/2...
     "3q_trace_C_to_rhoAB"),
]


def audit_np_trace_implementations():
    """
    Also verify np.trace(axis1=..., axis2=...) patterns which are the OTHER
    common partial trace implementation.

    np.trace(rho.reshape(dA,dB,dA,dB), axis1=1, axis2=3) traces out B (keeps A)
    np.trace(rho.reshape(dA,dB,dA,dB), axis1=0, axis2=2) traces out A (keeps B)
    """
    rho_r = BELL_RHO.reshape(2, 2, 2, 2)

    results = {}

    # Trace out B: np.trace(axis1=1, axis2=3)
    trB = np.trace(rho_r, axis1=1, axis2=3)
    results["np_trace_axis1_3_traceB"] = {
        "operation": "np.trace(rho.reshape(2,2,2,2), axis1=1, axis2=3)",
        "meaning": "trace out B, keep A",
        "matches_I_over_2": bool(np.allclose(trB, EXPECTED_PARTIAL_TRACE, atol=TOL)),
        "pass": bool(np.allclose(trB, EXPECTED_PARTIAL_TRACE, atol=TOL))
    }

    # Trace out A: np.trace(axis1=0, axis2=2)
    trA = np.trace(rho_r, axis1=0, axis2=2)
    results["np_trace_axis0_2_traceA"] = {
        "operation": "np.trace(rho.reshape(2,2,2,2), axis1=0, axis2=2)",
        "meaning": "trace out A, keep B",
        "matches_I_over_2": bool(np.allclose(trA, EXPECTED_PARTIAL_TRACE, atol=TOL)),
        "pass": bool(np.allclose(trA, EXPECTED_PARTIAL_TRACE, atol=TOL))
    }

    return results


def audit_naming_consistency():
    """
    Check files where function NAME vs actual OPERATION mismatch.
    This catches cases like partial_trace_b using einsum that actually traces A.
    """
    mismatches = []

    # sim_torch_ratchet_gnn.py: partial_trace_b uses "ijik->jk" which traces A
    mismatches.append({
        "file": "sim_torch_ratchet_gnn.py",
        "function": "partial_trace_b",
        "docstring": "Trace out subsystem B from rho_AB. Returns rho_A.",
        "einsum": "ijik->jk",
        "actual_operation": "traces out A (contracts positions 0,2 = dim_a), returns rho_B",
        "bug": "NAME MISMATCH: function says 'trace B, return rho_A' but einsum traces A, returns rho_B",
        "severity": "HIGH -- callers get rho_B labeled as rho_A"
    })

    mismatches.append({
        "file": "sim_torch_ratchet_gnn.py",
        "function": "partial_trace_a",
        "docstring": "Trace out subsystem A from rho_AB. Returns rho_B.",
        "einsum": "ijkj->ik",
        "actual_operation": "traces out B (contracts positions 1,3 = dim_b), returns rho_A",
        "bug": "NAME MISMATCH: function says 'trace A, return rho_B' but einsum traces B, returns rho_A",
        "severity": "HIGH -- callers get rho_A labeled as rho_B"
    })

    # holodeck_fep_engine.py: partial_trace_A with docstring "Trace out system B"
    mismatches.append({
        "file": "holodeck_fep_engine.py",
        "function": "partial_trace_A",
        "docstring": "Trace out system B from a composite rho_{AB}.",
        "einsum": "jiki->jk",
        "actual_operation": "contracts i at positions 1,3 = dim_B, keeps j,k at 0,2 = dim_A -> returns rho_A",
        "bug": "NAME MISLEADING: function named 'partial_trace_A' but traces B. Name convention inconsistent (other files: partial_trace_A means 'trace OUT A').",
        "severity": "MEDIUM -- math is correct (returns rho_A), but naming convention opposite to rest of codebase"
    })

    return mismatches


# =====================================================================
# MAIN AUDIT
# =====================================================================

def main():
    results = {
        "audit_type": "partial_trace_einsum",
        "timestamp": datetime.now().isoformat(),
        "classification": "audit",
        "description": "Sweep all probe .py files for einsum partial trace patterns, test against Bell/GHZ states",
        "bell_state_ground_truth": "Tr_A(|Bell><Bell|) = Tr_B(|Bell><Bell|) = I/2",
    }

    # ── 1. Test all known 2-qubit einsum patterns ──
    print("=" * 70)
    print("PHASE 1: Test known 2-qubit einsum patterns against Bell state")
    print("=" * 70)

    pattern_tests = {}
    for pat, reshape, label, expected_correct in KNOWN_EINSUM_PATTERNS_2Q:
        test = test_einsum_pattern_2qubit(pat, reshape, label)
        classification = classify_einsum_pattern(pat)
        test["classification"] = classification
        pattern_tests[label] = test

        status = "PASS" if test["pass"] else "FAIL"
        expected_str = "expected_correct" if expected_correct else "expected_WRONG"
        match = "OK" if test["pass"] == expected_correct else "UNEXPECTED"
        print(f"  {pat:15s} [{label:35s}] -> {status:4s} ({expected_str}) {match}")

    results["known_pattern_tests"] = pattern_tests

    # ── 2. Test 3-qubit patterns ──
    print()
    print("=" * 70)
    print("PHASE 2: Test 3-qubit einsum patterns against GHZ state")
    print("=" * 70)

    pattern_3q_tests = {}

    # Tr_A of GHZ: reshape (2,4,2,4), 'aiaj->ij'
    test_3q_trA = test_einsum_pattern_3qubit(
        "aiaj->ij", (2, 4, 2, 4), EXPECTED_GHZ_TRA, "3q_trace_A")
    pattern_3q_tests["3q_trace_A"] = test_3q_trA
    print(f"  aiaj->ij (2,4,2,4) [trace_A] -> {'PASS' if test_3q_trA['pass'] else 'FAIL'}")

    # Tr_C of GHZ: reshape (4,2,4,2), 'iaja->ij'
    expected_trC = np.zeros((4, 4), dtype=np.complex128)
    expected_trC[0, 0] = 0.5
    expected_trC[3, 3] = 0.5
    test_3q_trC = test_einsum_pattern_3qubit(
        "iaja->ij", (4, 2, 4, 2), expected_trC, "3q_trace_C")
    pattern_3q_tests["3q_trace_C"] = test_3q_trC
    print(f"  iaja->ij (4,2,4,2) [trace_C] -> {'PASS' if test_3q_trC['pass'] else 'FAIL'}")

    # Tr_AB of GHZ: reshape (4,2,4,2), 'aiaj->ij' -> Tr out AB, get rho_C
    expected_trAB = np.diag([0.5, 0.5]).astype(np.complex128)
    test_3q_trAB = test_einsum_pattern_3qubit(
        "aiaj->ij", (4, 2, 4, 2), expected_trAB, "3q_trace_AB")
    pattern_3q_tests["3q_trace_AB"] = test_3q_trAB
    print(f"  aiaj->ij (4,2,4,2) [trace_AB] -> {'PASS' if test_3q_trAB['pass'] else 'FAIL'}")

    # Tr_BC of GHZ: reshape (2,4,2,4), 'iaja->ij' -> Tr out BC, get rho_A
    expected_trBC = np.diag([0.5, 0.5]).astype(np.complex128)
    test_3q_trBC = test_einsum_pattern_3qubit(
        "iaja->ij", (2, 4, 2, 4), expected_trBC, "3q_trace_BC")
    pattern_3q_tests["3q_trace_BC"] = test_3q_trBC
    print(f"  iaja->ij (2,4,2,4) [trace_BC] -> {'PASS' if test_3q_trBC['pass'] else 'FAIL'}")

    results["3qubit_pattern_tests"] = pattern_3q_tests

    # ── 3. Scan ALL .py files for einsum partial trace patterns ──
    print()
    print("=" * 70)
    print("PHASE 3: Scan all probe files for einsum patterns")
    print("=" * 70)

    all_file_patterns = []
    for py_file in sorted(PROBES_DIR.glob("*.py")):
        if py_file.name == Path(__file__).name:
            continue  # skip self
        found = scan_file_for_einsum_patterns(py_file)
        all_file_patterns.extend(found)

    print(f"  Found {len(all_file_patterns)} einsum partial-trace-shaped patterns across probe files")

    file_audit = {}
    bugs_found = []

    for entry in all_file_patterns:
        pat = entry["pattern"]
        classification = classify_einsum_pattern(pat)
        entry["classification"] = classification

        # Test against Bell state
        test = test_einsum_pattern_2qubit(pat, (2, 2, 2, 2), entry["file"])
        entry["bell_test"] = {
            "pass": test["pass"],
            "matches_I_over_2": test.get("matches_I_over_2"),
            "trace": test.get("trace"),
        }

        fname = entry["file"]
        if fname not in file_audit:
            file_audit[fname] = {"patterns": [], "has_bug": False}
        file_audit[fname]["patterns"].append(entry)

        if not classification["is_valid_partial_trace"] or not test["pass"]:
            file_audit[fname]["has_bug"] = True
            bugs_found.append(entry)
            print(f"  BUG: {fname}:{entry['line']} -- {pat} -- {classification['issues']}")

    results["file_scan"] = file_audit
    results["bugs_found"] = bugs_found

    # ── 4. Verify np.trace implementations ──
    print()
    print("=" * 70)
    print("PHASE 4: Verify np.trace(axis1=..., axis2=...) implementations")
    print("=" * 70)

    np_trace_results = audit_np_trace_implementations()
    for k, v in np_trace_results.items():
        print(f"  {v['operation']} -> {'PASS' if v['pass'] else 'FAIL'}")
    results["np_trace_tests"] = np_trace_results

    # ── 5. Naming consistency audit ──
    print()
    print("=" * 70)
    print("PHASE 5: Naming consistency audit (function name vs actual operation)")
    print("=" * 70)

    naming_issues = audit_naming_consistency()
    for issue in naming_issues:
        print(f"  {issue['severity']}: {issue['file']}::{issue['function']} -- {issue['bug']}")
    results["naming_mismatches"] = naming_issues

    # ── 6. Priority file audit ──
    print()
    print("=" * 70)
    print("PHASE 6: Priority file deep audit")
    print("=" * 70)

    priority_audit = {}

    # sim_torch_mutual_info.py
    priority_audit["sim_torch_mutual_info.py"] = {
        "torch_partial_trace_A": {"einsum": "ijik->jk", "correct": True,
            "note": "Traces A (contracts 0,2), returns rho_B. Correctly named."},
        "torch_partial_trace_B": {"einsum": "ijkj->ik", "correct": True,
            "note": "Traces B (contracts 1,3), returns rho_A. Correctly named."},
        "numpy_partial_trace_A": {"einsum": "ijik->jk", "correct": True,
            "note": "Same correct pattern as torch version."},
        "numpy_partial_trace_B": {"einsum": "ijkj->ik", "correct": True,
            "note": "Same correct pattern as torch version."},
        "N1_random_trace_C": {"einsum": "ijkj->ik", "correct": True,
            "note": "Traces qubit C from 3-qubit via reshape (4,2,4,2). Correct."},
        "status": "CLEAN",
    }
    print(f"  sim_torch_mutual_info.py: CLEAN")

    # sim_torch_quantum_discord.py
    priority_audit["sim_torch_quantum_discord.py"] = {
        "torch_partial_trace_A": {"einsum": "ijik->jk", "correct": True,
            "note": "Traces A, returns rho_B. Correctly named."},
        "torch_partial_trace_B": {"einsum": "ijkj->ik", "correct": True,
            "note": "Traces B, returns rho_A. Correctly named."},
        "numpy_partial_trace_A": {"einsum": "ijik->jk", "correct": True,
            "note": "Same correct pattern."},
        "numpy_partial_trace_B": {"einsum": "ijkj->ik", "correct": True,
            "note": "Same correct pattern."},
        "status": "CLEAN",
    }
    print(f"  sim_torch_quantum_discord.py: CLEAN")

    # sim_torch_axis0_gradient.py
    priority_audit["sim_torch_axis0_gradient.py"] = {
        "partial_trace_A_line210": {"einsum": "aibj->ij", "correct": False,
            "note": "DEAD CODE BUG: line 210 has wrong pattern 'aibj->ij' that sums a,b independently. "
                    "Line 213 overwrites with correct 'aiaj->ij'. The wrong line executes but result is discarded."},
        "partial_trace_A_line213": {"einsum": "aiaj->ij", "correct": True,
            "note": "Correct pattern, overwrites the buggy line 210 result."},
        "numpy_partial_trace_A": {"einsum": "aiaj->ij", "correct": True,
            "note": "Correct pattern."},
        "status": "HAS_DEAD_CODE_BUG",
        "severity": "LOW -- dead code, overwritten by correct line. But should be removed to prevent copy-paste propagation.",
    }
    print(f"  sim_torch_axis0_gradient.py: DEAD CODE BUG (line 210 'aibj->ij' overwritten by correct line 213)")

    # sim_torch_axis0_3qubit.py
    priority_audit["sim_torch_axis0_3qubit.py"] = {
        "partial_trace_A": {"einsum": "aiaj->ij", "reshape": "(2,4,2,4)", "correct": True,
            "note": "Traces A from 8x8, returns 4x4 rho_BC. Correct."},
        "partial_trace_C": {"einsum": "iaja->ij", "reshape": "(4,2,4,2)", "correct": True,
            "note": "Traces C from 8x8, returns 4x4 rho_AB. Correct."},
        "partial_trace_AB": {"einsum": "aiaj->ij", "reshape": "(4,2,4,2)", "correct": True,
            "note": "Traces AB from 8x8, returns 2x2 rho_C. Correct."},
        "partial_trace_BC": {"einsum": "iaja->ij", "reshape": "(2,4,2,4)", "correct": True,
            "note": "Traces BC from 8x8, returns 2x2 rho_A. Correct."},
        "numpy_Ic_A_BC_line404": {"einsum": "aiaj->ij", "reshape": "(2,4,2,4)", "correct": True,
            "note": "Traces out A, returns rho_BC. Correct."},
        "numpy_Ic_AB_C_line411": {"einsum": "aiaj->ij", "reshape": "(4,2,4,2)", "correct": True,
            "note": "Traces out AB, returns rho_C. Correct."},
        "status": "CLEAN",
        "note": "This file was the one that CAUGHT the 'aibj' bug. All patterns here are correct.",
    }
    print(f"  sim_torch_axis0_3qubit.py: CLEAN (this file caught the original bug)")

    # sim_axis0_through_shells.py -- LIVE BUG (found by file scan)
    priority_audit["sim_axis0_through_shells.py"] = {
        "partial_trace_B_line108": {"einsum": "iaja->ij", "correct": True,
            "note": "Traces B (contracts 1,3), returns rho_A. Correct."},
        "partial_trace_A_line115": {"einsum": "aibj->ij", "correct": False,
            "note": "LIVE BUG: 'aibj->ij' sums a,b independently. Should be 'aiaj->ij'. "
                    "Called by coherent_info_A_to_B() -- coherent information values are WRONG."},
        "numpy_rho_A_line472": {"einsum": "iaja->ij", "correct": True,
            "note": "Numpy version traces B. Correct."},
        "numpy_rho_B_line473": {"einsum": "aibj->ij", "correct": False,
            "note": "LIVE BUG: same 'aibj->ij' error. Bloch vector for B will be wrong."},
        "status": "LIVE_BUG",
        "severity": "CRITICAL -- coherent information and Bloch vectors computed with wrong partial trace. "
                    "All results from this file are suspect.",
    }
    print(f"  sim_axis0_through_shells.py: CRITICAL LIVE BUG ('aibj->ij' at lines 115 and 473)")

    # sim_torch_cnot.py
    priority_audit["sim_torch_cnot.py"] = {
        "partial_trace_B_numpy": {"method": "explicit_loop", "correct": True,
            "note": "Manual loop: rho_A[i,j] = sum_k rho[2*i+k, 2*j+k]. Correct for trace B."},
        "partial_trace_A_numpy": {"method": "explicit_loop", "correct": True,
            "note": "Manual loop: rho_B[k,l] = sum_i rho[2*i+k, 2*i+l]. Correct for trace A."},
        "torch_partial_trace_B": {"method": "explicit_loop", "correct": True,
            "note": "Same manual loop as numpy version, differentiable. Correct."},
        "status": "CLEAN",
        "note": "Uses explicit loops, no einsum. All implementations correct.",
    }
    print(f"  sim_torch_cnot.py: CLEAN (uses explicit loops, no einsum)")

    results["priority_file_audit"] = priority_audit

    # ── 7. Additional files with einsum-based partial traces ──
    print()
    print("=" * 70)
    print("PHASE 7: Additional einsum file audit")
    print("=" * 70)

    additional_audit = {}

    # sim_torch_ratchet_gnn.py -- NAMING BUG
    additional_audit["sim_torch_ratchet_gnn.py"] = {
        "partial_trace_b": {"einsum": "ijik->jk", "math_correct": True,
            "naming_bug": True,
            "note": "Einsum traces A (correct math), but function named 'trace_b' and docstring says 'returns rho_A'. "
                    "Actually returns rho_B. Callers get SWAPPED subsystems."},
        "partial_trace_a": {"einsum": "ijkj->ik", "math_correct": True,
            "naming_bug": True,
            "note": "Einsum traces B (correct math), but function named 'trace_a' and docstring says 'returns rho_B'. "
                    "Actually returns rho_A. Callers get SWAPPED subsystems."},
        "caller_impact": "Line 549-550: rho_a_out = partial_trace_b(rho_ab) actually gets rho_B. SWAPPED.",
        "status": "NAMING_BUG",
        "severity": "HIGH -- subsystem labels swapped at call sites",
    }
    print(f"  sim_torch_ratchet_gnn.py: NAMING BUG (partial_trace_a/b swapped)")

    # sim_layered_foundation.py
    additional_audit["sim_layered_foundation.py"] = {
        "partial_trace_A": {"einsum": "ijik->jk", "correct": True,
            "note": "Traces A, returns rho_B. Correctly named."},
        "partial_trace_B": {"einsum": "ijkj->ik", "correct": True,
            "note": "Traces B, returns rho_A. Correctly named."},
        "status": "CLEAN",
    }
    print(f"  sim_layered_foundation.py: CLEAN")

    # sim_phase7_divergence_analysis.py
    additional_audit["sim_phase7_divergence_analysis.py"] = {
        "torch_partial_trace_B": {"einsum": "ijik->jk", "correct": True,
            "note": "Traces A when which='B'... wait. Let me check."},
        "status": "NEEDS_REVIEW",
    }
    # Re-examine: torch_partial_trace(which="B") uses 'ijik->jk'.
    # "which='B'" means "trace out B". But 'ijik->jk' traces out A.
    # Also: np_partial_trace(which="B") uses np.trace(axis1=1, axis2=3) which traces B.
    # INCONSISTENCY between numpy and torch versions!
    additional_audit["sim_phase7_divergence_analysis.py"] = {
        "np_partial_trace_B": {
            "method": "np.trace(axis1=1, axis2=3)",
            "correct": True,
            "note": "Traces out B (contracts dim_b at positions 1,3). Returns rho_A. Correct."
        },
        "np_partial_trace_A": {
            "method": "np.trace(axis1=0, axis2=2)",
            "correct": True,
            "note": "Traces out A (contracts dim_a at positions 0,2). Returns rho_B. Correct."
        },
        "torch_partial_trace_B": {
            "einsum": "ijik->jk",
            "correct": False,
            "note": "MISMATCH: when which='B' (trace out B), uses 'ijik->jk' which traces OUT A. "
                    "Returns rho_B instead of rho_A. Torch and numpy disagree!"
        },
        "torch_partial_trace_A": {
            "einsum": "ijkj->ik",
            "correct": False,
            "note": "MISMATCH: when which='A' (trace out A), uses 'ijkj->ik' which traces OUT B. "
                    "Returns rho_A instead of rho_B. Torch and numpy disagree!"
        },
        "status": "BUG",
        "severity": "HIGH -- torch version swaps which subsystem is traced vs numpy version. "
                    "If results are compared torch-vs-numpy, divergence analysis is comparing wrong subsystems.",
    }
    print(f"  sim_phase7_divergence_analysis.py: BUG (torch version swaps A/B vs numpy version)")

    # holodeck_fep_engine.py
    additional_audit["holodeck_fep_engine.py"] = {
        "partial_trace_A": {
            "einsum": "jiki->jk",
            "math_correct": True,
            "naming_convention": "OPPOSITE to rest of codebase",
            "note": "Function 'partial_trace_A' with doc 'trace out B' -- returns rho_A. "
                    "Math is correct but naming convention is opposite (elsewhere partial_trace_A means 'trace OUT A')."
        },
        "status": "NAMING_INCONSISTENCY",
        "severity": "MEDIUM",
    }
    print(f"  holodeck_fep_engine.py: NAMING INCONSISTENCY (partial_trace_A means 'get rho_A' not 'trace out A')")

    results["additional_file_audit"] = additional_audit

    # ── SUMMARY ──
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_files_scanned = len(file_audit)
    clean_files = sum(1 for f in file_audit.values() if not f["has_bug"])
    buggy_files = total_files_scanned - clean_files

    summary = {
        "total_files_with_einsum_ptrace": total_files_scanned,
        "clean_files": clean_files,
        "files_with_einsum_bugs": buggy_files,
        "live_einsum_bugs": 1,  # sim_axis0_through_shells.py
        "dead_code_bugs": 1,  # sim_torch_axis0_gradient.py line 210
        "naming_swap_bugs": 2,  # sim_torch_ratchet_gnn.py, sim_phase7_divergence_analysis.py
        "naming_inconsistencies": 1,  # holodeck_fep_engine.py
        "critical_bugs": [
            {
                "file": "sim_axis0_through_shells.py",
                "lines": "115, 473",
                "pattern": "aibj->ij",
                "type": "LIVE_wrong_einsum",
                "severity": "CRITICAL",
                "fix": "Replace 'aibj->ij' with 'aiaj->ij' at both lines. All results from this file are invalid."
            },
            {
                "file": "sim_torch_axis0_gradient.py",
                "line": 210,
                "pattern": "aibj->ij",
                "type": "dead_code_wrong_einsum",
                "severity": "LOW",
                "fix": "Remove line 210 (dead code, overwritten by correct line 213)"
            },
            {
                "file": "sim_torch_ratchet_gnn.py",
                "lines": "253-262",
                "pattern": "partial_trace_a/b naming swapped",
                "type": "naming_swap",
                "severity": "HIGH",
                "fix": "Swap function names: partial_trace_b should use 'ijkj->ik' (trace B), "
                       "partial_trace_a should use 'ijik->jk' (trace A)"
            },
            {
                "file": "sim_phase7_divergence_analysis.py",
                "lines": "126-131",
                "pattern": "torch vs numpy disagreement on which subsystem traced",
                "type": "torch_numpy_mismatch",
                "severity": "HIGH",
                "fix": "Swap einsum patterns in torch_partial_trace to match numpy: "
                       "which='B' should use 'ijkj->ik', which='A' should use 'ijik->jk'"
            },
            {
                "file": "holodeck_fep_engine.py",
                "line": 21,
                "pattern": "naming convention opposite",
                "type": "naming_inconsistency",
                "severity": "MEDIUM",
                "fix": "Rename to partial_trace_B or trace_out_B to match codebase convention"
            },
        ],
        "all_priority_files_status": {
            "sim_torch_mutual_info.py": "CLEAN",
            "sim_torch_quantum_discord.py": "CLEAN",
            "sim_torch_axis0_gradient.py": "DEAD_CODE_BUG",
            "sim_torch_axis0_3qubit.py": "CLEAN",
            "sim_torch_cnot.py": "CLEAN",
        },
        "verdict": "4 files need fixes. 1 CRITICAL live bug (sim_axis0_through_shells.py), 1 dead code removal, 2 naming/swap bugs that affect correctness.",
    }

    results["summary"] = summary

    print(f"  Files scanned: {total_files_scanned}")
    print(f"  Clean: {clean_files}")
    print(f"  With einsum pattern bugs: {buggy_files}")
    print(f"  Naming/swap bugs: 2")
    print(f"  Dead code bugs: 1")
    print()
    for bug in summary["critical_bugs"]:
        print(f"  [{bug['severity']}] {bug['file']}:{bug.get('line', bug.get('lines'))} -- {bug['type']}")
        print(f"         FIX: {bug['fix']}")

    # ── Write results ──
    output_path = RESULTS_DIR / "partial_trace_audit_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults written to: {output_path}")

    # Return exit code based on findings
    return 0 if buggy_files == 0 and len(naming_issues) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
