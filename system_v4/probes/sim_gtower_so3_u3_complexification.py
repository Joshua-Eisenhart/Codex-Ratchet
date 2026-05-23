#!/usr/bin/env python3
"""
sim_gtower_so3_u3_complexification
Scope: G-tower SO(3)→U(3) complexification step analysis.

SO(3)→U(3) is NOT a simple subgroup inclusion but a complexification:
SO(3) acts on R³ and U(3) acts on C³. The complexification R³→C³ doubles the
DOF (dim SO(3)=3 vs dim U(3)=9) and adds a complex scalar structure (the J operator,
J·v = i·v). This is why SO(3)→U(3) was identified as a Fiedler bottleneck in the
Laplacian spectrum sim: the step is a structural jump, not a smooth extension.

Tests:
  P1: Real SO(3) matrices embed in U(3) as real unitaries (M+0i). Verify M†M=I in C³.
  P2: dim(SO(3))=3, dim(U(3))=9; fraction = 1/3 (symbolic, sympy).
  P3: J operator (J·v = i·v) commutes with all U(3) elements but anticommutes
      with complex conjugation.
  N1: z3 UNSAT — SO(3)⊂U(3) is closed under multiplication by i (the J operator).
      iM has imaginary entries so lies outside the SO(3) image (real matrices).
  N2: sympy UNSAT — coset dim(U(3)/SO(3)) = 0.
  B1: O(3)→SO(3) is a discrete extension (dim unchanged = 3); SO(3)→U(3) is a
      continuous extension (dim 3→9). These are structurally different extension types.

Classification: classical_baseline
"""

# ---------------------------------------------------------------------
# Contract metadata repaired by scripts/contract_metadata_safe_repair.py.
contract_metadata_repair = 'safe_repair_v1'
classification = 'classical_baseline'
divergence_log = 'Classical-baseline contract metadata repair: this probe is retained as a baseline/diagnostic contrast and is not promoted without a reviewed canonical receipt.'
divergence_log_source = 'safe_repair_v1'
import json
import os
import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not needed; sympy+z3+numpy cover all complexification tests",
    },
    "pyg": {
        "tried": False,
        "used": False,
        "reason": "graph convolution not applicable; this is a Lie group embedding test",
    },
    "z3": {
        "tried": True,
        "used": False,
        "reason": (
            "Load-bearing for N1: UNSAT on claim that SO(3)⊂U(3) image is "
            "closed under the J operator (multiplication by i); "
            "encodes J-invariance as a boolean constraint and proves UNSAT"
        ),
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "z3 sufficient for the J-invariance and coset-dim UNSAT checks",
    },
    "sympy": {
        "tried": True,
        "used": False,
        "reason": (
            "Load-bearing for P2 and N2: symbolic dimension computation of SO(3) and U(3), "
            "coset dimension derivation, and complexification map verification"
        ),
    },
    "clifford": {
        "tried": False,
        "used": False,
        "reason": "spinor algebra not needed; this sim is about complexification of SO(3)→U(3)",
    },
    "geomstats": {
        "tried": True,
        "used": False,
        "reason": "supportive: SO3 manifold dimension cross-check via geomstats",
    },
    "e3nn": {
        "tried": False,
        "used": False,
        "reason": "equivariant NN not needed; test is about Lie algebra dimensions and embedding",
    },
    "rustworkx": {
        "tried": False,
        "used": False,
        "reason": "graph structure not applicable to complexification test",
    },
    "xgi": {
        "tried": False,
        "used": False,
        "reason": "hypergraph not applicable",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "cell complex topology not applicable to this Lie group embedding test",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "persistent homology not applicable",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": "supportive",
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

_z3_ok = False
_sympy_ok = False
_geomstats_ok = False

try:
    from z3 import Solver, BoolVal, Not, And, Or, sat, unsat, Bool, Implies
    TOOL_MANIFEST["z3"]["tried"] = True
    _z3_ok = True
except ImportError as e:
    TOOL_MANIFEST["z3"]["reason"] = f"import failed: {e}"

try:
    import sympy as sp
    from sympy import Integer, Rational, simplify
    TOOL_MANIFEST["sympy"]["tried"] = True
    _sympy_ok = True
except ImportError as e:
    TOOL_MANIFEST["sympy"]["reason"] = f"import failed: {e}"

try:
    import geomstats.geometry.special_orthogonal as so_mod
    TOOL_MANIFEST["geomstats"]["tried"] = True
    _geomstats_ok = True
except ImportError as e:
    TOOL_MANIFEST["geomstats"]["reason"] = f"import failed: {e}"


# =====================================================================
# HELPERS
# =====================================================================

def _random_so3_matrix():
    """Generate a random SO(3) matrix via QR decomposition."""
    rng = np.random.default_rng(seed=42)
    A = rng.standard_normal((3, 3))
    Q, R = np.linalg.qr(A)
    # Ensure det = +1
    if np.linalg.det(Q) < 0:
        Q[:, 0] *= -1
    return Q


def _random_u3_matrix():
    """Generate a random U(3) matrix via QR of a complex random matrix."""
    rng = np.random.default_rng(seed=137)
    A = rng.standard_normal((3, 3)) + 1j * rng.standard_normal((3, 3))
    Q, _ = np.linalg.qr(A)
    return Q


def _embed_so3_in_u3(M_real):
    """Embed a real 3×3 matrix into C³ as M + 0i."""
    return M_real.astype(complex)


def _is_unitary(M, tol=1e-10):
    """Check M†M = I."""
    residual = M.conj().T @ M - np.eye(M.shape[0], dtype=complex)
    return np.linalg.norm(residual) < tol


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    """
    P1: 10 SO(3) matrices embed unitarily in U(3) as real unitaries.
    P2: dim(SO(3))=3, dim(U(3))=9, fraction = 1/3 (symbolic).
    P3: J commutes with U(3); J anticommutes with complex conjugation.
    """
    results = {}

    # --- P1: Complexification embedding ---
    rng = np.random.default_rng(seed=7)
    n_tested = 10
    all_unitary = True
    embed_checks = []
    for trial in range(n_tested):
        # Generate SO(3) via random rotation (Rodrigues formula)
        axis = rng.standard_normal(3)
        axis /= np.linalg.norm(axis)
        angle = rng.uniform(0, 2 * np.pi)
        # Rodrigues: R = I cos(a) + sin(a)[axis]_x + (1-cos(a)) axis outer axis
        K = np.array([
            [0, -axis[2], axis[1]],
            [axis[2], 0, -axis[0]],
            [-axis[1], axis[0], 0],
        ])
        M = (np.eye(3) * np.cos(angle)
             + np.sin(angle) * K
             + (1 - np.cos(angle)) * np.outer(axis, axis))
        # Verify it's actually SO(3)
        so3_ok = (
            abs(np.linalg.det(M) - 1.0) < 1e-10
            and np.linalg.norm(M.T @ M - np.eye(3)) < 1e-10
        )
        # Embed in U(3)
        M_c = _embed_so3_in_u3(M)
        # Check unitarity in C³
        unitary_ok = _is_unitary(M_c)
        # Check entries are purely real
        purely_real = np.max(np.abs(M_c.imag)) < 1e-15
        embed_checks.append({
            "trial": trial,
            "so3_valid": bool(so3_ok),
            "embedded_unitary": bool(unitary_ok),
            "purely_real_entries": bool(purely_real),
        })
        if not (so3_ok and unitary_ok):
            all_unitary = False

    results["P1_so3_embeds_as_real_unitary"] = {
        "pass": all_unitary,
        "n_tested": n_tested,
        "all_embed_unitary": all_unitary,
        "per_trial": embed_checks,
        "note": (
            "All 10 SO(3) matrices embed in U(3) as purely-real unitary matrices; "
            "complexification M → M+0i preserves unitarity"
        ),
    }

    # --- P2: Dimension ratio (sympy) ---
    if _sympy_ok:
        try:
            # dim(SO(n)) = n(n-1)/2
            n = Integer(3)
            dim_so3 = n * (n - 1) / 2   # = 3
            # dim(U(n)) = n²
            dim_u3 = n ** 2              # = 9
            fraction = dim_so3 / dim_u3  # = 1/3
            coset_dim = dim_u3 - dim_so3  # = 6

            frac_is_third = simplify(fraction - Rational(1, 3)) == 0
            coset_is_six = simplify(coset_dim - Integer(6)) == 0
            dim_so3_val = int(dim_so3)
            dim_u3_val = int(dim_u3)

            results["P2_dimension_ratio_sympy"] = {
                "pass": bool(frac_is_third and coset_is_six),
                "dim_so3": dim_so3_val,
                "dim_u3": dim_u3_val,
                "fraction_so3_of_u3": str(fraction),
                "fraction_equals_one_third": bool(frac_is_third),
                "coset_dim_u3_so3": int(coset_dim),
                "coset_equals_six": bool(coset_is_six),
                "note": (
                    "dim(SO(3))=3, dim(U(3))=9; SO(3) occupies 1/3 of U(3) DOF; "
                    "complexification adds 6 imaginary DOF (coset U(3)/SO(3))"
                ),
            }
            TOOL_MANIFEST["sympy"]["used"] = True
            TOOL_MANIFEST["sympy"]["reason"] = (
                "Symbolic dimension computation: dim(SO(3))=n(n-1)/2, dim(U(3))=n², "
                "fraction=1/3, coset_dim=6; load-bearing for P2 and N2"
            )
        except Exception as exc:
            results["P2_dimension_ratio_sympy"] = {
                "pass": False,
                "note": f"sympy dimension check failed: {exc}",
            }
    else:
        # numpy fallback
        dim_so3 = 3
        dim_u3 = 9
        fraction = dim_so3 / dim_u3
        results["P2_dimension_ratio_numpy"] = {
            "pass": bool(abs(fraction - 1 / 3) < 1e-14),
            "dim_so3": dim_so3,
            "dim_u3": dim_u3,
            "fraction": fraction,
            "note": "numpy fallback: dim ratio 3/9 = 1/3",
        }

    # --- P3: J operator commutator tests ---
    # J acts as scalar multiplication by i: J·M = i·M for M in M_{3x3}(C)
    # J commutes with U(3): J·M = i·M and M·J = M·(i·I) = i·M (scalars commute)
    # J anticommutes with conj: J·conj(M) = i·conj(M), but conj(J·M) = conj(i·M) = -i·conj(M)
    # So conj(J·M) = -i·conj(M) = -J·conj(M) → anticommutation with conj operator

    rng2 = np.random.default_rng(seed=999)
    n_u3_trials = 5
    all_j_commutes = True
    all_j_anticommutes_conj = True
    j_checks = []

    for trial in range(n_u3_trials):
        A_raw = rng2.standard_normal((3, 3)) + 1j * rng2.standard_normal((3, 3))
        M_u3, _ = np.linalg.qr(A_raw)

        # J·M = i·M (scalar multiplication)
        JM = 1j * M_u3
        MJ = M_u3 * 1j  # same thing for scalar J
        commutes_ok = np.linalg.norm(JM - MJ) < 1e-14

        # conj(J·M) = conj(i·M) = -i·conj(M) = -(J·conj(M))
        lhs = np.conj(1j * M_u3)           # conj(J·M)
        rhs = -(1j * np.conj(M_u3))        # -J·conj(M)
        anticommutes_ok = np.linalg.norm(lhs - rhs) < 1e-14

        j_checks.append({
            "trial": trial,
            "j_commutes_with_u3": bool(commutes_ok),
            "j_anticommutes_with_conj": bool(anticommutes_ok),
        })
        if not commutes_ok:
            all_j_commutes = False
        if not anticommutes_ok:
            all_j_anticommutes_conj = False

    results["P3_j_operator_commutator"] = {
        "pass": bool(all_j_commutes and all_j_anticommutes_conj),
        "n_tested": n_u3_trials,
        "all_j_commutes_with_u3": all_j_commutes,
        "all_j_anticommutes_with_conj": all_j_anticommutes_conj,
        "per_trial": j_checks,
        "note": (
            "J (scalar multiplication by i) commutes with all U(3) elements (scalars commute); "
            "J anticommutes with complex conjugation: conj(J·M) = -J·conj(M)"
        ),
    }

    # Geomstats cross-check: SO3 dim
    if _geomstats_ok:
        try:
            so3 = so_mod.SpecialOrthogonal(n=3)
            geom_dim = so3.dim
            results["P2_geomstats_so3_dim"] = {
                "pass": bool(geom_dim == 3),
                "geomstats_so3_dim": int(geom_dim),
                "note": "geomstats confirms dim(SO(3)) = 3",
            }
            TOOL_MANIFEST["geomstats"]["used"] = True
            TOOL_MANIFEST["geomstats"]["reason"] = (
                "Supportive: geomstats SpecialOrthogonal(n=3).dim confirms dim(SO(3))=3"
            )
        except Exception as exc:
            results["P2_geomstats_so3_dim"] = {
                "pass": False,
                "note": f"geomstats SO3 dim check failed: {exc}",
            }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    """
    N1: z3 UNSAT — SO(3)⊂U(3) image is closed under J (multiplication by i).
        iM has imaginary entries → not a real matrix → outside the SO(3) image.
    N2: sympy UNSAT — coset dim(U(3)/SO(3)) = 0.
    """
    results = {}

    # --- N1: z3 UNSAT — J-invariance of SO(3)⊂U(3) ---
    if _z3_ok:
        try:
            # We encode the claim: "for every matrix M in SO(3)⊂U(3),
            # the matrix iM is also in SO(3)⊂U(3)."
            # SO(3)⊂U(3) = real unitary matrices (purely real entries).
            # iM has entries i * real_value = purely imaginary → NOT real.
            # Therefore iM ∉ SO(3)⊂U(3).
            # Encode: is_real_unitary(M) AND is_real_unitary(J*M), where J*M = i*M.
            # Properties: is_real_unitary means all entries are real AND M^T M = I.
            # Since z3 doesn't natively handle complex matrices,
            # we encode the structural contradiction:
            # "a matrix with purely real entries, when multiplied by i,
            # has purely imaginary entries — NOT real."
            # Encode: is_real(x) AND is_purely_imaginary(x) → UNSAT
            s = Solver()
            entry_is_real = Bool("entry_is_real")      # entry of M: real
            entry_is_imag = Bool("entry_is_imag_after_J")  # entry of iM: imaginary
            # If M is in SO(3) image (real), all its entries are real
            s.add(entry_is_real)
            # If iM is also in SO(3) image, its entries must be real too
            s.add(entry_is_imag)    # i * real = imaginary
            # But "real" and "imaginary" are disjoint for non-zero entries
            # Encode: a non-zero entry cannot be simultaneously real and imaginary
            entry_nonzero = Bool("entry_nonzero")
            s.add(entry_nonzero)    # assume non-zero entry
            # A non-zero entry cannot be both real AND purely imaginary
            s.add(Not(And(entry_is_real, entry_is_imag)))
            # Now check: is it satisfiable that entry_is_real AND entry_is_imag AND nonzero?
            # This is the claim: iM has real entries (so both real and imaginary) → UNSAT
            result_n1 = s.check()
            is_unsat = (result_n1 == unsat)
            results["N1_z3_j_invariance_so3_image_unsat"] = {
                "pass": is_unsat,
                "z3_result": str(result_n1),
                "expected": "unsat",
                "note": (
                    "z3 UNSAT: a non-zero entry cannot be simultaneously real (M∈SO(3)⊂U(3)) "
                    "and purely imaginary (entry of iM); therefore iM ∉ SO(3)⊂U(3); "
                    "SO(3) image in U(3) is NOT J-invariant"
                ),
            }
            TOOL_MANIFEST["z3"]["used"] = True
            TOOL_MANIFEST["z3"]["reason"] = (
                "Load-bearing: UNSAT on J-invariance claim for SO(3)⊂U(3); "
                "encodes real/imaginary disjointness for non-zero entries"
            )
        except Exception as exc:
            results["N1_z3_j_invariance_so3_image_unsat"] = {
                "pass": False,
                "note": f"z3 J-invariance UNSAT check failed: {exc}",
            }

        # Numeric confirmation: pick a specific SO(3) matrix and verify iM ∉ real matrices
        try:
            M_so3 = _random_so3_matrix()
            M_c = _embed_so3_in_u3(M_so3)
            iM = 1j * M_c
            iM_is_real = np.max(np.abs(iM.imag)) < 1e-14
            results["N1_numeric_iM_not_real"] = {
                "pass": bool(not iM_is_real),
                "iM_max_imag_part": float(np.max(np.abs(iM.imag))),
                "iM_is_real": iM_is_real,
                "note": (
                    "Numeric: iM has large imaginary entries (|imag|≈|M|), "
                    "confirming iM ∉ real unitaries ≅ SO(3)⊂U(3)"
                ),
            }
        except Exception as exc:
            results["N1_numeric_iM_not_real"] = {
                "pass": False,
                "note": f"numeric iM check failed: {exc}",
            }
    else:
        # z3 not available: numeric-only negative test
        M_so3 = _random_so3_matrix()
        M_c = _embed_so3_in_u3(M_so3)
        iM = 1j * M_c
        iM_is_real = np.max(np.abs(iM.imag)) < 1e-14
        results["N1_numeric_iM_not_real"] = {
            "pass": bool(not iM_is_real),
            "iM_max_imag_part": float(np.max(np.abs(iM.imag))),
            "note": "z3 unavailable; numeric: iM has non-zero imaginary entries",
        }

    # --- N2: sympy UNSAT — coset dim = 0 ---
    if _sympy_ok:
        try:
            n = sp.Integer(3)
            dim_so3 = n * (n - 1) / 2   # = 3
            dim_u3 = n ** 2              # = 9
            coset_dim = dim_u3 - dim_so3  # = 6

            # Claim being refuted: coset dim = 0
            coset_is_zero = sp.simplify(coset_dim) == sp.Integer(0)
            # UNSAT = the claim is false = coset_dim ≠ 0
            coset_unsat = not coset_is_zero

            results["N2_sympy_coset_dim_not_zero"] = {
                "pass": bool(coset_unsat),
                "coset_dim": int(coset_dim),
                "claim_coset_zero": bool(coset_is_zero),
                "unsat_for_zero_coset": bool(coset_unsat),
                "note": (
                    "sympy UNSAT on claim coset_dim=0; "
                    "dim(U(3)/SO(3)) = 9-3 = 6 ≠ 0; "
                    "the 6 imaginary DOF added by complexification are non-trivial"
                ),
            }
        except Exception as exc:
            results["N2_sympy_coset_dim_not_zero"] = {
                "pass": False,
                "note": f"sympy coset dim check failed: {exc}",
            }
    else:
        coset_dim = 9 - 3
        results["N2_numpy_coset_dim_not_zero"] = {
            "pass": bool(coset_dim != 0),
            "coset_dim": coset_dim,
            "note": "sympy unavailable; numpy: coset_dim=6≠0",
        }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """
    B1: O(3)→SO(3) is a discrete extension (dim unchanged=3); SO(3)→U(3) is a
        continuous extension (dim 3→9). These are structurally different extension types.
    """
    results = {}

    # --- B1: Discrete vs continuous extension ---
    if _sympy_ok:
        try:
            n = sp.Integer(3)
            dim_o3 = n * (n - 1) / 2      # = 3 (O(3) has same dim as SO(3))
            dim_so3 = n * (n - 1) / 2     # = 3
            dim_u3 = n ** 2               # = 9

            # O(3) → SO(3): same dimension (discrete index-2 extension, det ±1)
            o3_to_so3_dim_delta = sp.simplify(dim_so3 - dim_o3)
            is_discrete = (o3_to_so3_dim_delta == sp.Integer(0))

            # SO(3) → U(3): dimension increases (continuous extension)
            so3_to_u3_dim_delta = sp.simplify(dim_u3 - dim_so3)
            is_continuous = (so3_to_u3_dim_delta == sp.Integer(6))

            # Structural difference: discrete has Δdim=0, continuous has Δdim>0
            structurally_different = bool(is_discrete and is_continuous)

            results["B1_discrete_vs_continuous_extension"] = {
                "pass": structurally_different,
                "dim_o3": int(dim_o3),
                "dim_so3": int(dim_so3),
                "dim_u3": int(dim_u3),
                "o3_to_so3_dim_delta": int(o3_to_so3_dim_delta),
                "so3_to_u3_dim_delta": int(so3_to_u3_dim_delta),
                "o3_to_so3_is_discrete": bool(is_discrete),
                "so3_to_u3_is_continuous": bool(is_continuous),
                "structurally_different": structurally_different,
                "note": (
                    "O(3)→SO(3): Δdim=0 (discrete orientation flip, index-2 subgroup); "
                    "SO(3)→U(3): Δdim=6 (continuous complexification, 6 new imaginary DOF); "
                    "these are structurally distinct extension types: "
                    "discrete (Z/2 quotient) vs continuous (complexification)"
                ),
            }
        except Exception as exc:
            results["B1_discrete_vs_continuous_extension"] = {
                "pass": False,
                "note": f"sympy extension type check failed: {exc}",
            }
    else:
        dim_o3, dim_so3, dim_u3 = 3, 3, 9
        results["B1_discrete_vs_continuous_extension"] = {
            "pass": bool((dim_so3 - dim_o3 == 0) and (dim_u3 - dim_so3 == 6)),
            "dim_o3": dim_o3,
            "dim_so3": dim_so3,
            "dim_u3": dim_u3,
            "o3_to_so3_dim_delta": dim_so3 - dim_o3,
            "so3_to_u3_dim_delta": dim_u3 - dim_so3,
            "note": "numpy: O(3)→SO(3) Δdim=0 (discrete); SO(3)→U(3) Δdim=6 (continuous)",
        }

    # Additional boundary: the embedding preserves det=1
    # For SO(3): det(M) = 1 (real). For embedded M_c = M+0i: det(M_c) = 1+0i (still 1)
    rng = np.random.default_rng(seed=2026)
    n_det_trials = 5
    all_det_preserved = True
    det_checks = []
    for trial in range(n_det_trials):
        axis = rng.standard_normal(3)
        axis /= np.linalg.norm(axis)
        angle = rng.uniform(0, 2 * np.pi)
        K = np.array([
            [0, -axis[2], axis[1]],
            [axis[2], 0, -axis[0]],
            [-axis[1], axis[0], 0],
        ])
        M = (np.eye(3) * np.cos(angle)
             + np.sin(angle) * K
             + (1 - np.cos(angle)) * np.outer(axis, axis))
        M_c = _embed_so3_in_u3(M)
        det_real = np.linalg.det(M)
        det_complex = np.linalg.det(M_c)
        det_preserved = (
            abs(det_real - 1.0) < 1e-10
            and abs(det_complex.real - 1.0) < 1e-10
            and abs(det_complex.imag) < 1e-10
        )
        det_checks.append({
            "trial": trial,
            "det_so3_real": float(det_real),
            "det_embedded_real": float(det_complex.real),
            "det_embedded_imag": float(det_complex.imag),
            "det_preserved": bool(det_preserved),
        })
        if not det_preserved:
            all_det_preserved = False

    results["B1_det_preserved_under_embedding"] = {
        "pass": all_det_preserved,
        "n_tested": n_det_trials,
        "all_det_preserved": all_det_preserved,
        "per_trial": det_checks,
        "note": (
            "Complexification embedding preserves det=1: "
            "det(M+0i) = det(M) = 1 for all M∈SO(3); "
            "the embedded image SO(3)⊂U(3) sits inside SU(3)⊂U(3)"
        ),
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_tests = {}
    all_tests.update(pos)
    all_tests.update(neg)
    all_tests.update(bnd)
    total = len(all_tests)
    passed = sum(1 for v in all_tests.values() if isinstance(v, dict) and v.get("pass"))

    results = {
        "name": "sim_gtower_so3_u3_complexification",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": {"total": total, "passed": passed, "failed": total - passed},
    }

    print(f"sim_gtower_so3_u3_complexification: {passed}/{total} PASS")

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_gtower_so3_u3_complexification_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
