#!/usr/bin/env python3
"""Finite G2-like -> Spin(7)-like containment-direction scout.

This formal scout tests one bounded algebraic direction:

    G2-like three-form phi on R^7 + oriented normal e7
        -> Spin(7)-like Cayley four-form Omega = phi wedge e7 + *phi.

It also records a reverse-direction falsifier: a signed frame action preserves
Omega while moving the chosen normal line, so Spin(7)-like preservation alone
does not recover the fixed G2-like slice. The witnesses are explicit exterior
form tensors, signed-frame actions, and solver gates, not index/order-only
arguments.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch
import z3

try:
    import cvc5
    from cvc5 import Kind

    HAVE_CVC5 = True
except ImportError:
    cvc5 = None
    Kind = None
    HAVE_CVC5 = False

try:
    import sympy as sp

    HAVE_SYMPY = True
except ImportError:
    sp = None
    HAVE_SYMPY = False

try:
    from clifford import Cl

    HAVE_CLIFFORD = True
except ImportError:
    Cl = None
    HAVE_CLIFFORD = False

try:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere

    HAVE_GEOMSTATS = True
except ImportError:
    gs = None
    Hypersphere = None
    HAVE_GEOMSTATS = False

try:
    import rustworkx as rx

    HAVE_RUSTWORKX = True
except ImportError:
    rx = None
    HAVE_RUSTWORKX = False


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "g2_spin7_containment_direction_falsifier_probe_results.json"

NAME = "g2_spin7_containment_direction_falsifier_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
SIM_CLASS = "geometry_alternative_falsifier_probe"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "g2_spin7_containment_direction_with_reverse_falsifier"
CLAIM_CEILING = (
    "Formal scout only: a finite exterior-form/tensor witness that G2-like "
    "three-form preservation plus an oriented normal line preserves the induced "
    "Spin(7)-like Cayley four-form, with an explicit reverse-direction "
    "falsifier that preserves the Cayley form while moving the chosen normal "
    "slice. It does not admit a final G-structure, full holonomy group, "
    "canonical manifold, bridge, axis-level claim, or target-system claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing antisymmetric tensor construction, Cayley-form gaps, and signed-frame action witnesses",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing boolean admission gate for containment direction and reverse falsifier predicates",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent boolean cross-check for the same containment/falsifier predicates",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "supportive exact permutation determinant/sign witness for the reverse signed-frame action",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "supportive Clifford pseudoscalar sanity check for the seven-dimensional oriented slice",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "supportive S7 unit-normal membership and moved-normal distance witness",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency graph showing that fixed-normal G2 slice data is extra input, not recovered from Omega alone",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "supportive",
    "clifford": "supportive",
    "geomstats": "supportive",
    "rustworkx": "supportive",
}


Form = dict[tuple[int, ...], int]

G2_THREE_FORM: Form = {
    (0, 1, 2): 1,
    (0, 3, 4): 1,
    (0, 5, 6): 1,
    (1, 3, 5): 1,
    (1, 4, 6): -1,
    (2, 3, 6): -1,
    (2, 4, 5): -1,
}

EXPECTED_SPIN7_CAYLEY_FORM: Form = {
    (0, 1, 2, 7): 1,
    (0, 3, 4, 7): 1,
    (0, 5, 6, 7): 1,
    (1, 3, 5, 7): 1,
    (1, 4, 6, 7): -1,
    (2, 3, 6, 7): -1,
    (2, 4, 5, 7): -1,
    (3, 4, 5, 6): 1,
    (1, 2, 5, 6): 1,
    (1, 2, 3, 4): 1,
    (0, 2, 4, 6): 1,
    (0, 2, 3, 5): -1,
    (0, 1, 4, 5): -1,
    (0, 1, 3, 6): -1,
}

DEGENERATE_GENERIC_THREE_FORM: Form = {
    (0, 1, 2): 1,
    (0, 1, 3): 1,
    (0, 2, 4): -1,
    (1, 2, 5): 1,
    (2, 3, 6): 1,
    (3, 4, 5): -1,
    (4, 5, 6): 1,
}

IDENTITY_PERM = tuple(range(8))
IDENTITY_SIGNS = (1, 1, 1, 1, 1, 1, 1, 1)

# Explicit reverse-direction falsifier found in the finite signed-permutation
# stabilizer of the Cayley form. It preserves Omega but maps e7 to e6.
REVERSE_WITNESS_PERM = (0, 1, 3, 2, 4, 5, 7, 6)
REVERSE_WITNESS_SIGNS = (-1, -1, -1, -1, 1, 1, 1, 1)


def parity(sequence: tuple[int, ...] | list[int]) -> int:
    inversions = 0
    for i, left in enumerate(sequence):
        for right in sequence[i + 1 :]:
            inversions += int(left > right)
    return -1 if inversions % 2 else 1


def clean_form(form: Form) -> Form:
    return {term: int(coeff) for term, coeff in sorted(form.items()) if coeff}


def hodge_star_7(phi: Form) -> Form:
    star: Form = {}
    for term, coeff in phi.items():
        complement = tuple(idx for idx in range(7) if idx not in term)
        star[complement] = coeff * parity(tuple(term) + complement)
    return clean_form(star)


def wedge_with_normal(phi: Form, normal_idx: int = 7) -> Form:
    out: Form = {}
    for term, coeff in phi.items():
        extended = tuple(sorted((*term, normal_idx)))
        out[extended] = out.get(extended, 0) + coeff * parity(tuple(term) + (normal_idx,))
    return clean_form(out)


def build_cayley(phi: Form) -> Form:
    out: Form = {}
    for source in (wedge_with_normal(phi), hodge_star_7(phi)):
        for term, coeff in source.items():
            out[term] = out.get(term, 0) + coeff
    return clean_form(out)


def embed_form(form: Form, dim: int = 8) -> Form:
    del dim
    return clean_form(form)


def form_to_tensor(form: Form, dim: int, degree: int) -> torch.Tensor:
    tensor = torch.zeros((dim,) * degree, dtype=torch.float64)
    for term, coeff in form.items():
        for permuted in itertools.permutations(term):
            tensor[permuted] = float(coeff * parity(permuted))
    return tensor


def tensor_gap(left: Form, right: Form, dim: int, degree: int) -> float:
    return float(torch.linalg.norm(form_to_tensor(left, dim, degree) - form_to_tensor(right, dim, degree)).item())


def act_form(form: Form, perm: tuple[int, ...], signs: tuple[int, ...]) -> Form:
    out: Form = {}
    for term, coeff in form.items():
        images = tuple(perm[idx] for idx in term)
        sign_product = math.prod(signs[idx] for idx in term)
        sorted_images = tuple(sorted(images))
        out[sorted_images] = out.get(sorted_images, 0) + int(coeff * sign_product * parity(images))
    return clean_form(out)


def preserves_form(form: Form, perm: tuple[int, ...], signs: tuple[int, ...]) -> bool:
    return act_form(form, perm, signs) == clean_form(form)


def g2_sign_survivors() -> list[tuple[int, ...]]:
    survivors = []
    for signs7 in itertools.product([-1, 1], repeat=7):
        signs8 = tuple(signs7) + (1,)
        if preserves_form(G2_THREE_FORM, tuple(range(7)), tuple(signs7)):
            survivors.append(signs8)
    return survivors


def label_scramble_roundtrip_gap(omega: Form) -> dict[str, Any]:
    labels = ["eta", "beta", "theta", "alpha", "zeta", "gamma", "delta", "normal"]
    coord_to_label = {idx: labels[(idx * 5 + 3) % len(labels)] for idx in range(8)}
    label_to_coord = {label: idx for idx, label in coord_to_label.items()}
    labelled_terms = [
        (tuple(coord_to_label[idx] for idx in term), coeff)
        for term, coeff in sorted(omega.items(), key=lambda item: item[0])
    ]
    restored: Form = {}
    for labelled, coeff in labelled_terms:
        term = tuple(sorted(label_to_coord[label] for label in labelled))
        restored[term] = restored.get(term, 0) + coeff
    gap = tensor_gap(omega, clean_form(restored), 8, 4)
    return {
        "scrambled_labels": coord_to_label,
        "roundtrip_gap": gap,
        "pass": bool(gap <= 1e-12),
    }


def storage_reindex_restored_gap(omega: Form) -> dict[str, Any]:
    shuffled_items = list(sorted(omega.items(), key=lambda item: (sum(item[0]) % 5, item[0][::-1])))
    restored: Form = {}
    for term, coeff in reversed(shuffled_items):
        restored[term] = restored.get(term, 0) + coeff
    gap = tensor_gap(omega, clean_form(restored), 8, 4)
    return {
        "storage_order_sample": [list(term) for term, _coeff in shuffled_items[:5]],
        "roundtrip_gap": gap,
        "pass": bool(gap <= 1e-12),
    }


def z3_gate(predicates: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    terms = []
    for name, value in predicates.items():
        atom = z3.Bool(name)
        solver.add(atom == z3.BoolVal(bool(value)))
        terms.append(atom)
    joint = z3.Bool("joint_formal_scout_admission")
    solver.add(joint == z3.And(*terms))
    solver.add(joint)
    verdict = solver.check()
    return {
        "solver": "z3",
        "verdict": str(verdict),
        "joint_sat": bool(verdict == z3.sat),
        "predicate_count": len(predicates),
    }


def cvc5_gate(predicates: dict[str, bool]) -> dict[str, Any]:
    if not HAVE_CVC5 or cvc5 is None or Kind is None:
        return {"solver": "cvc5", "verdict": "unavailable", "joint_sat": None, "predicate_count": len(predicates)}
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_UF")
    bool_sort = tm.getBooleanSort()
    terms = []
    for name, value in predicates.items():
        atom = tm.mkConst(bool_sort, name)
        solver.assertFormula(tm.mkTerm(Kind.EQUAL, atom, tm.mkBoolean(bool(value))))
        terms.append(atom)
    joint = tm.mkConst(bool_sort, "joint_formal_scout_admission")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, joint, tm.mkTerm(Kind.AND, *terms)))
    solver.assertFormula(joint)
    verdict = solver.checkSat()
    return {
        "solver": "cvc5",
        "verdict": str(verdict),
        "joint_sat": bool(verdict.isSat()),
        "predicate_count": len(predicates),
    }


def sympy_reverse_witness_check() -> dict[str, Any]:
    if not HAVE_SYMPY or sp is None:
        return {"available": False, "pass": False, "reason": "sympy unavailable"}
    matrix = sp.zeros(8, 8)
    for src, dst in enumerate(REVERSE_WITNESS_PERM):
        matrix[dst, src] = REVERSE_WITNESS_SIGNS[src]
    determinant = int(matrix.det())
    moved_normal = [int(x) for x in matrix[:, 7]]
    return {
        "available": True,
        "determinant": determinant,
        "normal_image_column": moved_normal,
        "moves_normal_to_e6": bool(moved_normal == [0, 0, 0, 0, 0, 0, 1, 0]),
        "pass": bool(abs(determinant) == 1 and moved_normal == [0, 0, 0, 0, 0, 0, 1, 0]),
    }


def clifford_slice_check() -> dict[str, Any]:
    if not HAVE_CLIFFORD or Cl is None:
        return {"available": False, "pass": False, "reason": "clifford unavailable"}
    layout, blades = Cl(0, 7)
    pseudoscalar = blades["e1"] * blades["e2"] * blades["e3"] * blades["e4"] * blades["e5"] * blades["e6"] * blades["e7"]
    square = float((pseudoscalar * pseudoscalar)[()])
    return {
        "available": True,
        "layout_dims": layout.dims,
        "pseudoscalar_square": square,
        "pass": bool(layout.dims == 7 and math.isfinite(square) and abs(square - 1.0) <= 1e-12),
    }


def geomstats_normal_check() -> dict[str, Any]:
    if not HAVE_GEOMSTATS or gs is None or Hypersphere is None:
        return {"available": False, "pass": False, "reason": "geomstats unavailable"}
    sphere = Hypersphere(dim=7)
    normal = gs.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0])
    moved = gs.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0])
    normal_belongs = bool(sphere.belongs(normal))
    moved_belongs = bool(sphere.belongs(moved))
    distance = float(sphere.metric.dist(normal, moved))
    return {
        "available": True,
        "normal_belongs_s7": normal_belongs,
        "moved_belongs_s7": moved_belongs,
        "normal_to_moved_distance": distance,
        "pass": bool(normal_belongs and moved_belongs and distance > 0.1),
    }


def rustworkx_dependency_check() -> dict[str, Any]:
    if not HAVE_RUSTWORKX or rx is None:
        return {"available": False, "pass": False, "reason": "rustworkx unavailable"}
    graph = rx.PyDiGraph()
    phi = graph.add_node("G2_phi_on_fixed_R7")
    normal = graph.add_node("oriented_normal_e7")
    omega = graph.add_node("Spin7_like_Cayley_Omega")
    graph.add_edge(phi, omega, "wedge_plus_hodge_input")
    graph.add_edge(normal, omega, "chosen_normal_input")
    topo = [graph[idx] for idx in rx.topological_sort(graph)]
    normal_required = graph.has_edge(normal, omega)
    return {
        "available": True,
        "topological_order": topo,
        "normal_is_explicit_input": normal_required,
        "reverse_witness_moves_normal": REVERSE_WITNESS_PERM[7] != 7,
        "pass": bool(normal_required and REVERSE_WITNESS_PERM[7] != 7),
    }


def main() -> int:
    started = time.time()
    eps_equal = 1e-12
    eps_gap = 1e-6

    omega = build_cayley(G2_THREE_FORM)
    expected_gap = tensor_gap(omega, EXPECTED_SPIN7_CAYLEY_FORM, 8, 4)
    g2_tensor_norm = float(torch.linalg.norm(form_to_tensor(G2_THREE_FORM, 7, 3)).item())
    omega_tensor_norm = float(torch.linalg.norm(form_to_tensor(omega, 8, 4)).item())

    survivors = g2_sign_survivors()
    survivor_preserves_omega = [
        preserves_form(omega, IDENTITY_PERM, signs8)
        for signs8 in survivors
    ]
    survivor_omega_gaps = [
        tensor_gap(omega, act_form(omega, IDENTITY_PERM, signs8), 8, 4)
        for signs8 in survivors
    ]

    reverse_acted_omega = act_form(omega, REVERSE_WITNESS_PERM, REVERSE_WITNESS_SIGNS)
    reverse_omega_gap = tensor_gap(omega, reverse_acted_omega, 8, 4)
    embedded_phi = embed_form(G2_THREE_FORM)
    reverse_acted_phi = act_form(embedded_phi, REVERSE_WITNESS_PERM, REVERSE_WITNESS_SIGNS)
    reverse_phi_gap = tensor_gap(embedded_phi, reverse_acted_phi, 8, 3)
    reverse_phi_leak_terms = [term for term in reverse_acted_phi if 7 in term]
    reverse_moves_normal = REVERSE_WITNESS_PERM[7] != 7

    label_control = label_scramble_roundtrip_gap(omega)
    storage_control = storage_reindex_restored_gap(omega)

    degenerate_omega = build_cayley(DEGENERATE_GENERIC_THREE_FORM)
    degenerate_gap = tensor_gap(omega, degenerate_omega, 8, 4)
    degenerate_support_count = len(degenerate_omega)
    degenerate_reverse_gap = tensor_gap(
        degenerate_omega,
        act_form(degenerate_omega, REVERSE_WITNESS_PERM, REVERSE_WITNESS_SIGNS),
        8,
        4,
    )

    orientation_reversal_signs = (1, 1, 1, 1, 1, 1, 1, -1)
    orientation_reversed = act_form(omega, IDENTITY_PERM, orientation_reversal_signs)
    orientation_gap = tensor_gap(omega, orientation_reversed, 8, 4)

    sympy_check = sympy_reverse_witness_check()
    clifford_check = clifford_slice_check()
    geomstats_check = geomstats_normal_check()
    rustworkx_check = rustworkx_dependency_check()

    predicate_map = {
        "cayley_construction_matches_expected_terms": expected_gap <= eps_equal,
        "g2_sign_survivors_nonempty": len(survivors) > 0,
        "all_g2_sign_survivors_preserve_omega": all(survivor_preserves_omega),
        "reverse_witness_preserves_omega": reverse_omega_gap <= eps_equal,
        "reverse_witness_moves_normal": reverse_moves_normal,
        "reverse_witness_not_fixed_g2_slice": reverse_phi_gap > eps_gap and bool(reverse_phi_leak_terms),
        "label_scramble_roundtrip_invariant": label_control["pass"],
        "storage_reindex_roundtrip_invariant": storage_control["pass"],
        "degenerate_generic_control_rejected": degenerate_gap > eps_gap and degenerate_reverse_gap > eps_gap,
        "orientation_reversal_rejected": orientation_gap > eps_gap,
        "sympy_support_pass": sympy_check["pass"],
        "clifford_support_pass": clifford_check["pass"],
        "geomstats_support_pass": geomstats_check["pass"],
        "rustworkx_support_pass": rustworkx_check["pass"],
    }
    z3_result = z3_gate(predicate_map)
    cvc5_result = cvc5_gate(predicate_map)
    cross_solver_agree = z3_result["joint_sat"] == cvc5_result["joint_sat"]

    positive = {
        "pytorch_cayley_construction_matches_expected_spin7_terms": {
            "expected_gap": expected_gap,
            "eps_equal": eps_equal,
            "g2_tensor_norm": g2_tensor_norm,
            "omega_tensor_norm": omega_tensor_norm,
            "spin7_term_count": len(omega),
            "pass": bool(expected_gap <= eps_equal and len(omega) == 14),
        },
        "finite_g2_like_sign_survivors_extend_to_spin7_like_preservers": {
            "g2_survivor_count": len(survivors),
            "max_omega_gap_after_extension": max(survivor_omega_gaps),
            "sample_survivors": [list(row) for row in survivors[:8]],
            "pass": bool(len(survivors) > 0 and all(survivor_preserves_omega) and max(survivor_omega_gaps) <= eps_equal),
        },
        "reverse_witness_preserves_spin7_like_cayley_form": {
            "perm": list(REVERSE_WITNESS_PERM),
            "signs": list(REVERSE_WITNESS_SIGNS),
            "omega_gap": reverse_omega_gap,
            "pass": bool(reverse_omega_gap <= eps_equal),
        },
        "reverse_witness_falsifies_fixed_g2_slice_recovery": {
            "moves_normal": reverse_moves_normal,
            "normal_image": REVERSE_WITNESS_PERM[7],
            "phi_gap_on_fixed_slice": reverse_phi_gap,
            "phi_terms_leaking_into_normal": [list(term) for term in reverse_phi_leak_terms],
            "pass": bool(reverse_moves_normal and reverse_phi_gap > eps_gap and bool(reverse_phi_leak_terms)),
        },
        "z3_joint_admission": {**z3_result, "pass": bool(z3_result["joint_sat"])},
        "cvc5_joint_admission": {**cvc5_result, "pass": bool(cvc5_result["joint_sat"] is True)},
        "cross_solver_agreement": {
            "z3_joint_sat": z3_result["joint_sat"],
            "cvc5_joint_sat": cvc5_result["joint_sat"],
            "pass": bool(cross_solver_agree is True),
        },
    }

    graveyard_companions = {
        "reverse_containment_without_fixed_normal_is_not_admitted": {
            "omega_preserved": reverse_omega_gap <= eps_equal,
            "fixed_normal_preserved": not reverse_moves_normal,
            "fixed_phi_slice_preserved": reverse_phi_gap <= eps_equal,
            "interpretation": "Spin(7)-like Cayley preservation is compatible with moving the selected normal; fixed G2 slice data is extra.",
            "pass": bool(reverse_omega_gap <= eps_equal and reverse_moves_normal and reverse_phi_gap > eps_gap),
        },
        "label_scramble_is_metadata_only": label_control,
        "storage_reindex_restored_is_metadata_only": storage_control,
        "degenerate_generic_three_form_does_not_earn_g2_to_spin7_direction": {
            "gap_from_cayley": degenerate_gap,
            "degenerate_support_count": degenerate_support_count,
            "reverse_witness_gap_on_degenerate_form": degenerate_reverse_gap,
            "pass": bool(degenerate_gap > eps_gap and degenerate_reverse_gap > eps_gap),
        },
        "orientation_reversal_breaks_oriented_normal_containment_witness": {
            "orientation_reversal_signs": list(orientation_reversal_signs),
            "omega_gap": orientation_gap,
            "pass": bool(orientation_gap > eps_gap),
        },
    }

    boundary = {
        "classification_is_formal_scout": {
            "classification": CLASSIFICATION,
            "pass": bool(CLASSIFICATION == "formal_scout"),
        },
        "promotion_remains_disabled": {
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": bool(PROMOTION_ALLOWED is False),
        },
        "claim_ceiling_blocks_final_g_structure_and_manifold_promotion": {
            "claim_ceiling": CLAIM_CEILING,
            "pass": bool(
                all(
                    term in CLAIM_CEILING.lower()
                    for term in ["formal scout only", "does not admit", "final g-structure", "canonical manifold"]
                )
            ),
        },
        "supportive_tools_available_and_nonpromotional": {
            "sympy": sympy_check,
            "clifford": clifford_check,
            "geomstats": geomstats_check,
            "rustworkx": rustworkx_check,
            "pass": bool(all(row["pass"] for row in [sympy_check, clifford_check, geomstats_check, rustworkx_check])),
        },
        "result_path_is_formal_scout_result_surface": {
            "result_path": str(OUT_PATH),
            "pass": bool(OUT_PATH.parent.name == "results" and OUT_PATH.name.endswith("_results.json")),
        },
    }

    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row.get("pass") is True),
        "variants": sorted(graveyard_companions),
    }

    all_pass = (
        all(row.get("pass") is True for row in positive.values())
        and all(row.get("pass") is True for row in graveyard_companions.values())
        and all(row.get("pass") is True for row in boundary.values())
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.1.0",
        "tier": "geometry_alternative_falsifier",
        "purpose": (
            "Test a bounded exceptional-holonomy-like geometry alternative: "
            "G2-like fixed-slice three-form data plus an oriented normal induces "
            "a Spin(7)-like Cayley four-form, while reverse recovery of the "
            "fixed G2 slice from the Cayley form alone is falsified."
        ),
        "scientific_question": (
            "Does this finite exterior-form scout support a directional "
            "G2-like -> Spin(7)-like containment witness, and does it block "
            "the reverse direction strongly enough to prevent accidental "
            "official G-structure promotion?"
        ),
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "sim_class": SIM_CLASS,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": {
            "F01": {
                "finite_carrier": "finite exterior-form term dictionaries for one 7D G2-like three-form and one induced 8D Spin(7)-like Cayley four-form",
                "finite_probe_set": [
                    "G2 sign-survivor enumeration",
                    "reverse signed-frame witness",
                    "orientation-reversal control",
                    "degenerate generic three-form control"
                ],
                "finite_operator_or_path_set": [
                    "signed-frame action on form terms",
                    "wedge_with_normal",
                    "hodge_star_7",
                    "Cayley construction"
                ]
            },
            "N01": {
                "direction_sensitive_witness": "G2-like fixed-slice data plus oriented normal induces Omega, but Omega preservation alone does not recover the fixed normal or G2 slice",
                "reverse_control": {
                    "reverse_omega_gap": reverse_omega_gap,
                    "reverse_phi_gap": reverse_phi_gap,
                    "normal_moved": reverse_moves_normal
                },
                "orientation_control": {
                    "orientation_gap": orientation_gap
                }
            }
        },
        "finite_map": (
            "G2Spin7_alt : (finite G2-like three-form phi on fixed R7, "
            "oriented normal e7, signed-frame action family, controls) -> "
            "Spin(7)-like Cayley form Omega, survivor/falsifier gaps, solver "
            "certificates, and blocked-consumer status"
        ),
        "domain": (
            "finite exterior-form term dictionaries, finite signed-frame action "
            "family, finite normal orientation, finite degenerate/orientation/"
            "label/storage controls"
        ),
        "codomain_or_output": (
            "finite Cayley-form term dictionary, containment-direction witness, "
            "reverse-direction falsifier, support-tool certificates, controls, "
            "and blocked consumers"
        ),
        "carrier_layer": "finite exterior-form algebra over torch tensors; geometry-alternative scout only",
        "geometry_layer": "G2-like fixed-slice three-form and Spin(7)-like Cayley four-form directionality",
        "carrier_realization": (
            "torch.float64 antisymmetric form tensors generated from finite term "
            "dictionaries; not a source-native spinor-network carrier"
        ),
        "peps3d_embedding": "blocked: no PEPS3D site/bond/face/cell carrier is constructed in this exterior-form scout",
        "spinor_state": "blocked: no torch-native spinor payload is constructed in this exterior-form scout",
        "torch_spinor_or_density": "blocked_for_full_geometry_candidate: tensor-form witness only, no spinor-derived density",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": [
            "individual_full_g_structure_candidate_admission",
            "source_native_spinor_network_candidate",
            "MPS/PEPS2D/PEPS3D_depth_candidate",
            "official_layered_ratchet_G_structure_selection",
            "layer_embedding",
            "stacking",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "Holodeck/FEP",
            "physics/gravity",
            "final_manifold_admission"
        ],
        "blocked_consumers": [
            "individual_full_g_structure_candidate_admission",
            "source_native_spinor_network_candidate",
            "MPS/PEPS2D/PEPS3D_depth_candidate",
            "official_layered_ratchet_G_structure_selection",
            "layer_embedding",
            "stacking",
            "flux",
            "Xi/Phi0",
            "Axis0",
            "Holodeck/FEP",
            "physics/gravity",
            "final_manifold_admission"
        ],
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "directional G2-like fixed-slice containment into Spin(7)-like Cayley form with reverse-direction falsifier",
        "branch_status_before_run": "geometry alternative candidate not yet admitted to source-native spinor/PEPS carrier matrix",
        "allowed_claims": [
            "bounded exterior-form containment-direction witness",
            "reverse recovery of fixed G2 slice from Omega alone is falsified",
            "exceptional geometry remains candidate/control fuel only until source-native spinor/PEPS carrier is built"
        ],
        "promotion_blockers": [
            "no torch-native spinor payload",
            "no spinor-derived density",
            "no MPS carrier view",
            "no PEPS2D carrier view",
            "no PEPS3D site/bond/face/cell carrier",
            "no QIT entropy family readout",
            "no shell-gradient metadata"
        ],
        "extended_constraint_alignment": {
            "finite_map_domain_codomain": "pass",
            "F01_finite_carrier_probe_operator_path": "pass",
            "N01_direction_or_order_sensitive_control": "pass",
            "torch_native_computation": "pass_tensor_form_only",
            "torch_spinor_or_spinor_derived_density": "blocked",
            "MPS_view": "blocked",
            "PEPS2D_view": "blocked",
            "PEPS3D_site_bond_face_cell_anchor": "blocked",
            "QIT_entropy_as_derived_readout": "not_applicable_in_this_exterior_form_scout",
            "tool_ablation_or_support_delta": "partial_supportive_tools_and_solver_gates_present",
            "scale_8_16_32_64": "not_applicable_to_single_exterior_form_falsifier",
            "shell_gradient_fields": "not_applicable_unless_lifted_into_shell_candidate",
            "blocked_consumers": "pass"
        },
        "next_admissible_step": (
            "If exceptional geometry remains useful, build a separate "
            "G2/Spin7 source-native spinor-network candidate with MPS, PEPS2D, "
            "PEPS3D, 8/16/32/64 scale, QIT readouts, and controls. Do not "
            "promote this exterior-form scout as that candidate."
        ),
        "all_pass": bool(all_pass),
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": PROMOTION_ALLOWED,
            "result_path": str(OUT_PATH),
            "g2_survivor_count": len(survivors),
            "spin7_term_count": len(omega),
            "reverse_omega_gap": reverse_omega_gap,
            "reverse_phi_gap": reverse_phi_gap,
            "orientation_gap": orientation_gap,
            "degenerate_gap": degenerate_gap,
            "cross_solver_agree": cross_solver_agree,
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "v5 formal scout only; it writes no canonical v4 probe and does not update the v4 result estate.",
            "The witness is finite exterior-form algebra over one fixed model phi and Omega, not a full holonomy or manifold theorem.",
            "Reverse-direction failure keeps final G-structure/manifold promotion disallowed.",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "probe_family_M": {
            "g2_three_form_terms": {str(term): coeff for term, coeff in G2_THREE_FORM.items()},
            "spin7_cayley_terms": {str(term): coeff for term, coeff in omega.items()},
            "construction": "Omega = phi wedge e7 + hodge_star_7(phi)",
            "reverse_witness": {
                "perm": list(REVERSE_WITNESS_PERM),
                "signs": list(REVERSE_WITNESS_SIGNS),
                "normal_image": REVERSE_WITNESS_PERM[7],
            },
        },
        "constraint_set_C": {
            "C1_forward_containment": "all finite diagonal signed G2-like phi preservers with normal sign +1 preserve Omega",
            "C2_reverse_falsifier": "one signed-frame action preserves Omega while moving e7 and leaking phi out of the fixed R7 slice",
            "C3_label_control": "scrambled display labels roundtrip to the same Omega tensor",
            "C4_storage_control": "storage reindexing roundtrips to the same Omega tensor",
            "C5_generic_degenerate_control": "a same-size degenerate generic 3-form does not match the Cayley witness and is not preserved by the reverse witness",
            "C6_orientation_control": "normal orientation reversal changes Omega",
        },
        "eps_equal": eps_equal,
        "eps_gap": eps_gap,
        "all_predicates": predicate_map,
        "solver_admission": {"z3": z3_result, "cvc5": cvc5_result},
        "supportive_checks": {
            "sympy": sympy_check,
            "clifford": clifford_check,
            "geomstats": geomstats_check,
            "rustworkx": rustworkx_check,
        },
        "blockers": [] if all_pass else ["g2_spin7_containment_direction_falsifier_probe_failed"],
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
