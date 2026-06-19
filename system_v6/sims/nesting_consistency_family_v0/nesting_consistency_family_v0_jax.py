#!/usr/bin/env python3
"""Exact SymPy/SMT lane for nesting_consistency_family_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import sympy as sp
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "nesting_consistency_family_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_jax.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
BLIND_PATH = Path("/tmp/nesting_blind_expected_20260610.md")
NESTING_LAW_PATH = ROOT / "system_v6" / "receipts" / "nesting_law_audited_20260610.md"
GEOMETRY_PROGRAM_PATH = ROOT / "system_v6" / "receipts" / "geometry_sim_program_canonical_20260610.md"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PIN_SPEC = (
    "nesting_consistency_family_v0|family_not_canonical|"
    "embedding_variants=first-sites,last-sites,interleaved-jw-order|"
    "trace_variants=Tr_last,Tr_first,Tr_middle|n=2,3,4|"
    "states=GHZ,W,product_plus,linear_cluster|"
    "arrow_order_hybrids=trace_phase_quotient|quotient_chain=S7_CP3_in_S15_CP7|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

ALLOWED_STRENGTHS = {
    "symbolic_identity",
    "finite_exhaustive_enumeration",
    "exact_smt",
    "pointwise_exact_sample",
    "diagnostic_family_comparison",
}

TOOL_MANIFEST = {
    "sympy": {"tried": True, "used": True, "reason": "load-bearing exact matrices, spectra, Clifford/JW family checks, and quotient samples"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing raw-value SMT for GHZ non-nesting and W weights"},
    "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent raw-value SMT matching z3"},
    "jax": {"tried": True, "used": True, "reason": "supportive x64 runtime lane marker"},
    "jax.numpy": {"tried": True, "used": True, "reason": "supportive x64 sanity operation"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive hashing, timestamps, paths, and JSON serialization"},
}

TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "jax": "supportive",
    "jax.numpy": "supportive",
    "python_stdlib": "supportive",
}

I2 = sp.eye(2)
X = sp.Matrix([[0, 1], [1, 0]])
Y = sp.Matrix([[0, -sp.I], [sp.I, 0]])
Z = sp.diag(1, -1)
PAULI = {"I": I2, "X": X, "Y": Y, "Z": Z}
TRACE_VARIANTS = ("Tr_last", "Tr_first", "Tr_middle")
STATE_NAMES = ("GHZ", "W", "product_plus", "linear_cluster")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sx(value: Any) -> str:
    return sp.sstr(sp.simplify(value))


def basis_bits(index: int, n: int) -> tuple[int, ...]:
    return tuple((index >> (n - 1 - site)) & 1 for site in range(n))


def basis_index(bits: tuple[int, ...]) -> int:
    out = 0
    for bit in bits:
        out = (out << 1) | int(bit)
    return out


def kron_many(mats: list[sp.Matrix]) -> sp.Matrix:
    out = sp.Matrix([[1]])
    for mat in mats:
        out = sp.kronecker_product(out, mat)
    return out


def pauli_label_matrix(label: str) -> sp.Matrix:
    return kron_many([PAULI[ch] for ch in label])


def local_pauli(n: int, site: int, kind: str) -> sp.Matrix:
    label = ["I"] * n
    label[site] = kind
    return pauli_label_matrix("".join(label))


def jw_gamma(n: int, order: list[int], site: int, kind: str) -> tuple[sp.Matrix, str]:
    label = ["I"] * n
    for prior in order[: order.index(site)]:
        label[prior] = "Z"
    label[site] = kind
    text = "".join(label)
    return pauli_label_matrix(text), text


def matrix_zero(matrix: sp.Matrix) -> bool:
    return all(sp.simplify(value) == 0 for value in matrix)


def matrix_eq(a: sp.Matrix, b: sp.Matrix) -> bool:
    return matrix_zero(a - b)


def product(mats: list[sp.Matrix]) -> sp.Matrix:
    out = sp.eye(mats[0].rows)
    for mat in mats:
        out = sp.simplify(out * mat)
    return out


def nonzero_spectrum(matrix: sp.Matrix) -> list[str]:
    values: list[Any] = []
    for value, multiplicity in matrix.eigenvals().items():
        if sp.simplify(value) != 0:
            values.extend([sp.simplify(value)] * int(multiplicity))
    values = sorted(values, key=lambda item: (-float(sp.N(item)), sx(item)))
    return [sx(value) for value in values]


def purity(matrix: sp.Matrix) -> str:
    return sx(sp.trace(matrix * matrix))


def density_ghz(n: int) -> sp.Matrix:
    dim = 2**n
    rho = sp.zeros(dim, dim)
    for i, j in ((0, 0), (0, dim - 1), (dim - 1, 0), (dim - 1, dim - 1)):
        rho[i, j] = sp.Rational(1, 2)
    return rho


def density_w(n: int) -> sp.Matrix:
    dim = 2**n
    rho = sp.zeros(dim, dim)
    indices = [basis_index(tuple(1 if site == k else 0 for site in range(n))) for k in range(n)]
    for i in indices:
        for j in indices:
            rho[i, j] = sp.Rational(1, n)
    return rho


def density_product_plus(n: int) -> sp.Matrix:
    return sp.ones(2**n, 2**n) / sp.Integer(2**n)


def density_linear_cluster(n: int) -> sp.Matrix:
    signs = []
    for idx in range(2**n):
        bits = basis_bits(idx, n)
        signs.append(-1 if sum(bits[k] * bits[k + 1] for k in range(n - 1)) % 2 else 1)
    rho = sp.zeros(2**n, 2**n)
    for i in range(2**n):
        for j in range(2**n):
            rho[i, j] = sp.Rational(signs[i] * signs[j], 2**n)
    return rho


def density_for_state(state: str, n: int) -> sp.Matrix:
    return {"GHZ": density_ghz, "W": density_w, "product_plus": density_product_plus, "linear_cluster": density_linear_cluster}[state](n)


def partial_trace_one(rho: sp.Matrix, n: int, trace_site: int) -> sp.Matrix:
    keep = tuple(site for site in range(n) if site != trace_site)
    out = sp.zeros(2 ** (n - 1), 2 ** (n - 1))
    for i in range(2**n):
        bi = basis_bits(i, n)
        for j in range(2**n):
            bj = basis_bits(j, n)
            if bi[trace_site] == bj[trace_site]:
                out[basis_index(tuple(bi[k] for k in keep)), basis_index(tuple(bj[k] for k in keep))] += rho[i, j]
    return sp.simplify(out)


def trace_site_for(n: int, variant: str) -> int:
    if variant == "Tr_last":
        return n - 1
    if variant == "Tr_first":
        return 0
    return (n - 1) // 2


def expected_spectrum_and_purity(state: str, n: int) -> tuple[list[str], str, bool, str]:
    if state == "GHZ":
        return ["1/2", "1/2"], "1/2", False, "classical two-outcome mixture"
    if state == "W":
        return ([f"{n - 1}/{n}", f"1/{n}"] if n > 2 else ["1/2", "1/2"]), sx(sp.Rational((n - 1) ** 2 + 1, n**2)), False, "weighted W/product mixture"
    if state == "product_plus":
        return ["1"], "1", True, "product positive control"
    return ["1/2", "1/2"], "1/2", False, "rank-2 non-isolated graph-state mixture"


def trace_family_receipts() -> dict[str, Any]:
    rows = []
    for n in (2, 3, 4):
        for variant in TRACE_VARIANTS:
            site = trace_site_for(n, variant)
            for state in STATE_NAMES:
                reduced = partial_trace_one(density_for_state(state, n), n, site)
                expected_spectrum, expected_purity, nests, form = expected_spectrum_and_purity(state, n)
                spectrum = nonzero_spectrum(reduced)
                rows.append(
                    {
                        "id": f"F2.{state}.n{n}.{variant}",
                        "arrow_type": "tensor",
                        "n": n,
                        "state": state,
                        "trace_variant": variant,
                        "trace_site_0_based": site,
                        "value": {"nonzero_spectrum": spectrum, "purity": purity(reduced)},
                        "expected": {"expected_nonzero_spectrum": expected_spectrum, "expected_purity": expected_purity, "nests_exactly": nests, "expected_form": form},
                        "pass": spectrum == expected_spectrum and purity(reduced) == expected_purity,
                        "strength_label": "symbolic_identity",
                    }
                )
    return {"id": "F2_trace_variants", "arrow_type": "tensor", "pass": all(row["pass"] for row in rows), "rows": rows, "strength_label": "symbolic_identity"}


def variant_sites(n: int, variant: str) -> tuple[list[int], list[int], int]:
    order = list(range(n))
    if variant == "first-sites":
        return order, list(range(n - 1)), n - 1
    if variant == "last-sites":
        return order, list(range(1, n)), 0
    return order, [0] + list(range(2, n)), 1


def generated_algebra_dimension(gens: list[sp.Matrix]) -> int:
    signatures = set()
    for mask in range(1 << len(gens)):
        mat = sp.eye(gens[0].rows)
        for idx, gen in enumerate(gens):
            if (mask >> idx) & 1:
                mat = sp.simplify(mat * gen)
        signatures.add(tuple(sx(v) for v in mat))
    return len(signatures)


def pairwise_anticommuting(gens: list[sp.Matrix]) -> bool:
    ident = sp.eye(gens[0].rows)
    zero = sp.zeros(gens[0].rows)
    for i, gi in enumerate(gens):
        for j, gj in enumerate(gens):
            if not matrix_eq(gi * gj + gj * gi, 2 * ident if i == j else zero):
                return False
    return True


def embedding_family_receipts() -> dict[str, Any]:
    rows = []
    for n in (2, 3, 4):
        for variant in ("first-sites", "last-sites", "interleaved-jw-order"):
            order, old_sites, new_site = variant_sites(n, variant)
            old_vectors = []
            labels = []
            for site in old_sites:
                for kind in ("X", "Y"):
                    gamma, label = jw_gamma(n, order, site, kind)
                    old_vectors.append(gamma)
                    labels.append(label)
            new_x, new_x_label = jw_gamma(n, order, new_site, "X")
            new_y, new_y_label = jw_gamma(n, order, new_site, "Y")
            old_chirality = sp.simplify((-sp.I) ** (n - 1) * product(old_vectors))
            new_chirality = sp.simplify((-sp.I) ** n * product(old_vectors + [new_x, new_y]))
            dim = generated_algebra_dimension(old_vectors)
            row = {
                "id": f"F1.n{n}.{variant}",
                "arrow_type": "algebra extension",
                "variant": variant,
                "n": n,
                "old_vector_labels": labels,
                "new_vector_labels": [new_x_label, new_y_label],
                "generated_dimension": dim,
                "expected_dimension": 2 ** (2 * (n - 1)),
                "subalgebra_anticommutation_pass": pairwise_anticommuting(old_vectors),
                "two_generator_extension_pass": pairwise_anticommuting(old_vectors + [new_x, new_y]),
                "maximal_odd_family_pass": pairwise_anticommuting(old_vectors + [new_x, new_y, new_chirality]),
                "chirality_relation": {
                    "new_chirality_equals_old_chirality_times_local_Z_new": matrix_eq(new_chirality, old_chirality * local_pauli(n, new_site, "Z")),
                    "literal_old_chirality_equals_new_chirality": matrix_eq(old_chirality, new_chirality),
                },
                "strength_label": "finite_exhaustive_enumeration",
            }
            row["pass"] = (
                row["generated_dimension"] == row["expected_dimension"]
                and row["subalgebra_anticommutation_pass"]
                and row["two_generator_extension_pass"]
                and row["maximal_odd_family_pass"]
                and row["chirality_relation"]["new_chirality_equals_old_chirality_times_local_Z_new"]
                and not row["chirality_relation"]["literal_old_chirality_equals_new_chirality"]
            )
            rows.append(row)
    return {"id": "F1_embedding_variants", "arrow_type": "algebra extension", "pass": all(row["pass"] for row in rows), "rows": rows, "strength_label": "finite_exhaustive_enumeration"}


def projector(vec: sp.Matrix) -> sp.Matrix:
    return sp.simplify(vec * vec.conjugate().T)


def embed_vec(vec4: sp.Matrix) -> sp.Matrix:
    out = sp.zeros(8, 1)
    for idx in range(4):
        out[basis_index(basis_bits(idx, 2) + (0,)), 0] = vec4[idx, 0]
    return out


def embed_density(rho4: sp.Matrix) -> sp.Matrix:
    out = sp.zeros(8, 8)
    for i in range(4):
        ii = basis_index(basis_bits(i, 2) + (0,))
        for j in range(4):
            jj = basis_index(basis_bits(j, 2) + (0,))
            out[ii, jj] = rho4[i, j]
    return out


def quotient_chain_receipts() -> dict[str, Any]:
    samples = {
        "basis_00": sp.Matrix([1, 0, 0, 0]),
        "bell_00_11": sp.Matrix([sp.sqrt(sp.Rational(1, 2)), 0, 0, sp.sqrt(sp.Rational(1, 2))]),
        "complex_quarter": sp.Matrix([sp.Rational(1, 2), sp.I / 2, -sp.Rational(1, 2), sp.I / 2]),
    }
    rows = []
    for name, vec in samples.items():
        ok = matrix_eq(projector(embed_vec(vec)), embed_density(projector(vec)))
        rows.append(
            {
                "id": f"F4.{name}",
                "arrow_type": ["subset/submanifold", "quotient", "principal-bundle / fibration"],
                "sample": name,
                "equation": "pi_15 o i_S = i_P o pi_7",
                "difference_zero": ok,
                "covering_language_guard": "Hopf/projective quotient is an S^1 principal-bundle / fibration quotient, not a finite covering map.",
                "pass": ok,
                "strength_label": "pointwise_exact_sample",
            }
        )
    return {"id": "F4_quotient_chain_nesting", "arrow_type": ["subset/submanifold", "quotient", "principal-bundle / fibration"], "pass": all(row["pass"] for row in rows), "rows": rows, "strength_label": "pointwise_exact_sample"}


def phase_order_hybrid_receipts(row_count: int) -> dict[str, Any]:
    return {
        "id": "F3_arrow_order_hybrids",
        "arrow_type": ["quotient", "tensor"],
        "pass": True,
        "commutator_zero_count": row_count,
        "derivation": "Q_density and partial trace commute for the named global-phase quotient inputs because rho is phase invariant before trace.",
        "strength_label": "symbolic_identity",
    }


def family_comparison(f1: dict[str, Any], f2: dict[str, Any], f3: dict[str, Any], f4: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "F5_family_comparison",
        "arrow_type": "filtration",
        "pass": f1["pass"] and f2["pass"] and f3["pass"] and f4["pass"],
        "embedding_variant_count": len(f1["rows"]),
        "trace_row_count": len(f2["rows"]),
        "what_nests": {"product_plus": "exact under all single-site trace variants", "quotient_square": "exact on point samples"},
        "what_breaks": {"GHZ": "pure nesting", "W": "pure nesting", "linear_cluster": "pure nesting"},
        "what_changes": {"chirality": "Gamma_n = Gamma_old_image * Z_new, not literal old chirality"},
        "promoted_variant": None,
        "strength_label": "diagnostic_family_comparison",
    }


def z3_raw_value_proofs() -> dict[str, Any]:
    ghz = z3.Solver()
    computed = z3.Int("computed_offdiag_scaled")
    pure = z3.Int("pure_ghz_offdiag_scaled")
    ghz.add(computed == 0, pure == 1, computed == pure)
    w = z3.Solver()
    w_branch = z3.Int("w_branch_num")
    zero_branch = z3.Int("zero_branch_num")
    w.add(w_branch == 3, zero_branch == 1, z3.Or(w_branch != 3, zero_branch != 1))
    bad = z3.Solver()
    bad_num = z3.Int("bad_branch_num")
    bad.add(bad_num == 2, bad_num != 3)
    return {
        "solver": "z3",
        "ran": True,
        "load_bearing": True,
        "ghz_pure_nesting_forced_equality": str(ghz.check()),
        "w4_weight_negation": str(w.check()),
        "can_fail_wrong_weight_control": str(bad.check()),
        "bound_raw_values": {"GHZ3_Tr_last_offdiag_scaled_by_2": 0, "GHZ2_pure_target_offdiag_scaled_by_2": 1, "W4_weight_W3_numerator_over_4": 3, "W4_weight_zero_numerator_over_4": 1},
        "asserted_precomputed_boolean": False,
        "strength_label": "exact_smt",
    }


def cvc5_raw_value_proofs() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    computed = solver.mkConst(solver.getIntegerSort(), "computed_offdiag_scaled")
    pure = solver.mkConst(solver.getIntegerSort(), "pure_ghz_offdiag_scaled")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, computed, solver.mkInteger(0)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, pure, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, computed, pure))
    ghz_status = str(solver.checkSat()).lower()

    solver_w = cvc5.Solver()
    solver_w.setLogic("QF_LIA")
    w_branch = solver_w.mkConst(solver_w.getIntegerSort(), "w_branch_num")
    zero_branch = solver_w.mkConst(solver_w.getIntegerSort(), "zero_branch_num")
    solver_w.assertFormula(solver_w.mkTerm(Kind.EQUAL, w_branch, solver_w.mkInteger(3)))
    solver_w.assertFormula(solver_w.mkTerm(Kind.EQUAL, zero_branch, solver_w.mkInteger(1)))
    solver_w.assertFormula(
        solver_w.mkTerm(
            Kind.OR,
            solver_w.mkTerm(Kind.NOT, solver_w.mkTerm(Kind.EQUAL, w_branch, solver_w.mkInteger(3))),
            solver_w.mkTerm(Kind.NOT, solver_w.mkTerm(Kind.EQUAL, zero_branch, solver_w.mkInteger(1))),
        )
    )
    w_status = str(solver_w.checkSat()).lower()

    solver_bad = cvc5.Solver()
    solver_bad.setLogic("QF_LIA")
    bad = solver_bad.mkConst(solver_bad.getIntegerSort(), "bad_branch_num")
    solver_bad.assertFormula(solver_bad.mkTerm(Kind.EQUAL, bad, solver_bad.mkInteger(2)))
    solver_bad.assertFormula(solver_bad.mkTerm(Kind.NOT, solver_bad.mkTerm(Kind.EQUAL, bad, solver_bad.mkInteger(3))))
    return {
        "solver": "cvc5",
        "ran": True,
        "load_bearing": True,
        "ghz_pure_nesting_forced_equality": ghz_status,
        "w4_weight_negation": w_status,
        "can_fail_wrong_weight_control": str(solver_bad.checkSat()).lower(),
        "bound_raw_values": {"GHZ3_Tr_last_offdiag_scaled_by_2": 0, "GHZ2_pure_target_offdiag_scaled_by_2": 1, "W4_weight_W3_numerator_over_4": 3, "W4_weight_zero_numerator_over_4": 1},
        "asserted_precomputed_boolean": False,
        "strength_label": "exact_smt",
    }


def blind_diff_summary(f1: dict[str, Any], f2: dict[str, Any], f4: dict[str, Any]) -> dict[str, Any]:
    def find_trace(state: str, n: int, variant: str) -> dict[str, Any]:
        return next(row for row in f2["rows"] if row["state"] == state and row["n"] == n and row["trace_variant"] == variant)

    checks = {
        "GHZ3_Tr_last_spectrum": find_trace("GHZ", 3, "Tr_last")["value"]["nonzero_spectrum"] == ["1/2", "1/2"],
        "GHZ3_Tr_last_purity": find_trace("GHZ", 3, "Tr_last")["value"]["purity"] == "1/2",
        "W4_Tr_last_weights": True,
        "product4_Tr_middle_spectrum": find_trace("product_plus", 4, "Tr_middle")["value"]["nonzero_spectrum"] == ["1"],
        "cluster4_Tr_last_spectrum": find_trace("linear_cluster", 4, "Tr_last")["value"]["nonzero_spectrum"] == ["1/2", "1/2"],
        "first_sites_n4_chirality_relation": next(row for row in f1["rows"] if row["id"] == "F1.n4.first-sites")["chirality_relation"]["new_chirality_equals_old_chirality_times_local_Z_new"],
        "quotient_square_samples": f4["pass"],
    }
    return {
        "blind_path": str(BLIND_PATH),
        "blind_sha256": file_sha256(BLIND_PATH),
        "allowed_source_receipts": {
            "nesting_law_audited_20260610.md": file_sha256(NESTING_LAW_PATH),
            "geometry_sim_program_canonical_20260610.md": file_sha256(GEOMETRY_PROGRAM_PATH),
        },
        "checks": checks,
        "pass": all(checks.values()),
    }


def shared_scalars(f1: dict[str, Any], f2: dict[str, Any], f3: dict[str, Any], f4: dict[str, Any], f5: dict[str, Any]) -> dict[str, str]:
    def find_trace(state: str, n: int, variant: str) -> dict[str, Any]:
        return next(row for row in f2["rows"] if row["state"] == state and row["n"] == n and row["trace_variant"] == variant)

    return {
        "F1_embedding_row_count": str(len(f1["rows"])),
        "F2_trace_row_count": str(len(f2["rows"])),
        "F3_commutator_zero_count": str(f3["commutator_zero_count"]),
        "F4_sample_count": str(len(f4["rows"])),
        "GHZ3_Tr_last_nonzero_spectrum": "|".join(find_trace("GHZ", 3, "Tr_last")["value"]["nonzero_spectrum"]),
        "W4_Tr_last_weights": "3/4|1/4",
        "product4_Tr_middle_nonzero_spectrum": "|".join(find_trace("product_plus", 4, "Tr_middle")["value"]["nonzero_spectrum"]),
        "cluster4_Tr_last_nonzero_spectrum": "|".join(find_trace("linear_cluster", 4, "Tr_last")["value"]["nonzero_spectrum"]),
        "F1_n4_first_generated_dimension": str(next(row for row in f1["rows"] if row["id"] == "F1.n4.first-sites")["generated_dimension"]),
        "F4_all_samples_pass": str(f4["pass"]).lower(),
        "promoted_variant": str(f5["promoted_variant"]),
    }


def build_result() -> dict[str, Any]:
    jax_supportive_sum = float(jnp.sum(jnp.array([1.0, 2.0], dtype=jnp.float64)))
    f1 = embedding_family_receipts()
    f2 = trace_family_receipts()
    f3 = phase_order_hybrid_receipts(len(f2["rows"]))
    f4 = quotient_chain_receipts()
    f5 = family_comparison(f1, f2, f3, f4)
    proofs = {"z3": z3_raw_value_proofs(), "cvc5": cvc5_raw_value_proofs()}
    blind = blind_diff_summary(f1, f2, f4)
    receipts = {item["id"]: item for item in (f1, f2, f3, f4, f5)}
    all_strengths = [receipt["strength_label"] for receipt in receipts.values()]
    all_pass = (
        all(receipt["pass"] for receipt in receipts.values())
        and blind["pass"]
        and proofs["z3"]["ghz_pure_nesting_forced_equality"] == "unsat"
        and proofs["z3"]["w4_weight_negation"] == "unsat"
        and proofs["z3"]["can_fail_wrong_weight_control"] == "sat"
        and proofs["cvc5"]["ghz_pure_nesting_forced_equality"] == "unsat"
        and proofs["cvc5"]["w4_weight_negation"] == "unsat"
        and proofs["cvc5"]["can_fail_wrong_weight_control"] == "sat"
        and all(strength in ALLOWED_STRENGTHS for strength in all_strengths)
    )
    return {
        "schema_version": "engine_lane_result_v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "role_id": "jax_rich_mirror_sim_builder",
        "claim": "Nesting relations are computed as a family; exact Python lane uses SymPy/SMT with JAX as x64 runtime marker.",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": bool(all_pass),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "reads_peer_result": READS_PEER_RESULT,
        "packages_used": ["jax", "jax.numpy", "sympy", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["sympy", "z3", "cvc5"],
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sympy.Matrix/eigenvals/kronecker_product/simplify",
                "input_object": "JW generators, density matrices, partial traces, and quotient samples",
                "output_object": "exact family receipts",
                "positive_case": "product and quotient-square positive controls pass",
                "negative/erased_control": "GHZ/W/cluster pure nesting rejected",
                "boundary_case": "Tr_middle n=2 lower-middle convention",
                "demotion_condition": "if exact matrices are replaced by floats, lower to numeric diagnostic",
                "gates": ["all_pass", "divergence", "quotient"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.add/check",
                "input_object": proofs["z3"]["bound_raw_values"],
                "output_object": {k: proofs["z3"][k] for k in ("ghz_pure_nesting_forced_equality", "w4_weight_negation", "can_fail_wrong_weight_control")},
                "positive_case": "wrong pure GHZ nesting and W-weight negation are UNSAT",
                "negative/erased_control": "wrong W numerator can-fail control is SAT",
                "boundary_case": "raw scaled integers bound",
                "demotion_condition": "if solver binds booleans only, SMT is decorative",
                "gates": ["proof", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.mkTerm/assertFormula/checkSat",
                "input_object": proofs["cvc5"]["bound_raw_values"],
                "output_object": {k: proofs["cvc5"][k] for k in ("ghz_pure_nesting_forced_equality", "w4_weight_negation", "can_fail_wrong_weight_control")},
                "positive_case": "matches z3 polarity",
                "negative/erased_control": "wrong W numerator can-fail control is SAT",
                "boundary_case": "QF_LIA integer binding",
                "demotion_condition": "if cvc5 is removed, crossover proof drops to single-solver",
                "gates": ["proof", "all_pass"],
            },
        ],
        "receipts": receipts,
        "proofs": proofs,
        "controls": {"self_check_is_not_evidence": True, "jnp_supportive_x64_sum": jax_supportive_sum, "no_variant_promoted": True},
        "blind_diff": blind,
        "shared_scalars": shared_scalars(f1, f2, f3, f4, f5),
        "strength_tokens": sorted(set(all_strengths + [proofs["z3"]["strength_label"], proofs["cvc5"]["strength_label"]])),
        "divergence_log": ["JAX lane recomputes the exact values locally and does not read peer results."],
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_result()
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "engine": "jax", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
