#!/usr/bin/env python3
"""
sim_toponetx_deep_cell_complex_boundary_consistency

Scope note: The admissibility claim being tested is B_{k-1} B_k = 0 on a 2-cell
complex (a square face glued to its 4 edges). This is the chain-complex fence
from system_v5/new docs/LADDERS_FENCES_ADMISSION_REFERENCE.md (boundary fence).
Without toponetx constructing the CellComplex and emitting incidence matrices
with the canonical orientation convention, we have no admissibility probe for
cell-complex distinguishability at all -- a hand-rolled B2 would beg the
orientation question the claim is about. Removing toponetx does not merely slow
the computation; it removes the admissibility claim's referent.

Classification: canonical (tool-integration depth sim).
"""
import json, os, sys
import numpy as np

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"] = {
        "tried": True, "used": True,
        "reason": "CellComplex + incidence_matrix(k) provide the oriented boundary "
                  "operators B1,B2; the admissibility claim B1 @ B2 == 0 is only "
                  "defined in toponetx's orientation convention. Without it, the "
                  "admissibility referent does not exist -- this is load_bearing.",
    }
    TOOL_INTEGRATION_DEPTH["toponetx"] = "load_bearing"
except ImportError as e:
    print(f"BROKEN ENV: toponetx not importable: {e}", file=sys.stderr)
    sys.exit(2)


def _build_square():
    cc = CellComplex()
    cc.add_cell([1, 2, 3, 4], rank=2)
    return cc


def run_positive_tests():
    out = {}
    cc = _build_square()
    B1 = cc.incidence_matrix(1).toarray()
    B2 = cc.incidence_matrix(2).toarray()
    prod = B1 @ B2
    out["B1B2_zero_square"] = {
        "PASS": bool(np.all(prod == 0)),
        "max_abs": float(np.max(np.abs(prod))),
        "note": "admissible: boundary-of-boundary vanishes on oriented 2-cell",
    }
    # second positive: two glued squares
    cc2 = CellComplex()
    cc2.add_cell([1, 2, 3, 4], rank=2)
    cc2.add_cell([3, 4, 5, 6], rank=2)
    B1b = cc2.incidence_matrix(1).toarray()
    B2b = cc2.incidence_matrix(2).toarray()
    prod2 = B1b @ B2b
    out["B1B2_zero_two_glued"] = {
        "PASS": bool(np.all(prod2 == 0)),
        "max_abs": float(np.max(np.abs(prod2))),
    }
    return out


def run_negative_tests():
    out = {}
    # Negative: if we scramble the B2 column signs (simulating an orientation
    # violation), admissibility must FAIL. This shows the claim is not trivial.
    cc = _build_square()
    B1 = cc.incidence_matrix(1).toarray()
    B2 = cc.incidence_matrix(2).toarray().copy()
    B2_bad = B2.copy()
    # flip exactly one edge's contribution to the face -> breaks d^2=0
    nz = np.flatnonzero(B2_bad[:, 0])
    B2_bad[nz[0], 0] = -B2_bad[nz[0], 0] * 2 + B2_bad[nz[0], 0]  # +1 -> -3-ish? ensure !=
    B2_bad[nz[0], 0] += 1
    prod_bad = B1 @ B2_bad
    out["orientation_violation_excluded"] = {
        "PASS": bool(np.any(prod_bad != 0)),
        "max_abs": float(np.max(np.abs(prod_bad))),
        "language": "excluded: orientation-violating B2 is not admissible",
    }
    # Negative 2: wrong-rank product (B2 @ B1 is shape-incompatible)
    try:
        _ = B2 @ B1
        out["rank_mismatch_caught"] = {"PASS": False, "note": "should have raised"}
    except ValueError:
        out["rank_mismatch_caught"] = {"PASS": True, "note": "excluded by shape"}
    return out


def run_boundary_tests():
    out = {}
    # Minimal (triangle) and degenerate (single edge, no 2-cell)
    cc_tri = CellComplex()
    cc_tri.add_cell([1, 2, 3], rank=2)
    B1 = cc_tri.incidence_matrix(1).toarray()
    B2 = cc_tri.incidence_matrix(2).toarray()
    out["triangle_d2_zero"] = {
        "PASS": bool(np.all(B1 @ B2 == 0)),
        "shapes": [list(B1.shape), list(B2.shape)],
    }
    cc_edge = CellComplex()
    cc_edge.add_cell([1, 2], rank=1)
    # no 2-cells: incidence_matrix(2) has zero columns; product is vacuously zero
    B2e = cc_edge.incidence_matrix(2).toarray()
    out["no_2cells_vacuous"] = {
        "PASS": B2e.shape[1] == 0,
        "shape": list(B2e.shape),
    }
    return out


if __name__ == "__main__":
    name = "sim_toponetx_deep_cell_complex_boundary_consistency"
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()
    all_pass = (
        all(v.get("PASS") for v in pos.values())
        and all(v.get("PASS") for v in neg.values())
        and all(v.get("PASS") for v in bnd.values())
    )
    results = {
        "name": name,
        "classification": "canonical",
        "scope_note": "LADDERS_FENCES_ADMISSION_REFERENCE.md (boundary fence)",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "ALL_PASS": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"{name}: ALL_PASS={all_pass} -> {out_path}")
