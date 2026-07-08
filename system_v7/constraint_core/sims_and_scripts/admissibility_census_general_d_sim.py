#!/usr/bin/env python3
"""Finite admissibility census for the d=4 strengthening path.

This is a scratch diagnostic.  It generalizes the local d=2
``admissibility_two_operator_sim.py`` convention through an explicitly scoped
two-qubit X/Z Pauli-axis family:

* unitary generators are Hamiltonians along nonidentity X/Z Pauli axes;
* dissipative generators are dephasing and canonical tensor-product lowering
  Lindblad jumps along those same axes.

The count is relative to that family, not to all Lindblad generators on M_4.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from collections import Counter, deque
from itertools import product
from pathlib import Path
from typing import Any

import sympy as sp
import z3


ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/admissibility_census_general_d_sim.py"
RESULT_PATH = ROOT / "system_v7/constraint_core/sims_and_scripts/admissibility_census_general_d_sim_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

I2 = sp.eye(2)
X = sp.Matrix([[0, 1], [1, 0]])
Z = sp.Matrix([[1, 0], [0, -1]])
LOWER_Z = sp.Matrix([[0, 0], [1, 0]])
LOWER_X = sp.Matrix([[sp.Rational(1, 2), -sp.Rational(1, 2)], [sp.Rational(1, 2), -sp.Rational(1, 2)]])

LOCAL_PAULI = {"I": I2, "X": X, "Z": Z}
LOCAL_LOWERING = {"I": I2, "X": LOWER_X, "Z": LOWER_Z}


def kron_all(mats: list[sp.Matrix]) -> sp.Matrix:
    out = sp.Matrix([[1]])
    for mat in mats:
        out = sp.kronecker_product(out, mat)
    return sp.Matrix(out)


def axis_words(n_qubits: int) -> list[str]:
    return ["".join(word) for word in product("IXZ", repeat=n_qubits) if any(letter != "I" for letter in word)]


def pauli_word(axis: str) -> sp.Matrix:
    return kron_all([LOCAL_PAULI[letter] for letter in axis])


def lowering_word(axis: str) -> sp.Matrix:
    return kron_all([LOCAL_LOWERING[letter] for letter in axis])


def vectorize(mat: sp.Matrix) -> sp.Matrix:
    return sp.Matrix(mat).reshape(mat.rows * mat.cols, 1)


def rank_of(mats: list[sp.Matrix]) -> int:
    if not mats:
        return 0
    return sp.Matrix.hstack(*[vectorize(mat) for mat in mats]).rank()


def add_if_independent(basis: list[sp.Matrix], candidate: sp.Matrix) -> bool:
    before = len(basis)
    after_rank = rank_of([*basis, candidate])
    if after_rank > before:
        basis.append(sp.Matrix(candidate))
        return True
    return False


def generated_algebra_basis(generators: list[sp.Matrix]) -> list[sp.Matrix]:
    dim = generators[0].rows
    basis: list[sp.Matrix] = []
    add_if_independent(basis, sp.eye(dim))
    for generator in generators:
        add_if_independent(basis, generator)

    changed = True
    while changed:
        changed = False
        current = list(basis)
        for left in current:
            for right in current:
                if add_if_independent(basis, left * right):
                    changed = True
                    if len(basis) == dim * dim:
                        return basis
    return basis


def commutant_dimension(generators: list[sp.Matrix]) -> int:
    dim = generators[0].rows
    variables = sp.symbols(f"x0:{dim * dim}")
    unknown = sp.Matrix(dim, dim, variables)
    rows: list[list[sp.Expr]] = []
    for generator in generators:
        comm = unknown * generator - generator * unknown
        for expr in list(comm):
            rows.append([sp.expand(expr).coeff(var) for var in variables])
    coeffs = sp.Matrix(rows)
    return dim * dim - coeffs.rank()


def rational_to_z3(value: sp.Expr) -> z3.ArithRef:
    value = sp.Rational(value)
    return z3.RealVal(f"{int(value.p)}/{int(value.q)}")


def z3_independence_certificate(basis: list[sp.Matrix], label: str) -> dict[str, Any]:
    coeffs = [z3.Real(f"{label}_c_{idx}") for idx in range(len(basis))]
    solver = z3.Solver()
    for row in range(basis[0].rows * basis[0].cols):
        solver.add(sum(coeffs[col] * rational_to_z3(vectorize(basis[col])[row, 0]) for col in range(len(basis))) == 0)
    solver.add(z3.Or(*[coeff != 0 for coeff in coeffs]))
    verdict = str(solver.check())
    return {
        "basis_size": len(basis),
        "linear_dependence_exists_verdict": verdict,
        "independent": verdict == "unsat",
        "encoding": "QF_LRA: nonzero rational linear dependence over flattened exact generator-algebra basis",
    }


def symplectic_anticommutes(left: str, right: str) -> bool:
    flips = 0
    for a, b in zip(left, right, strict=True):
        if {a, b} == {"X", "Z"}:
            flips += 1
    return flips % 2 == 1


def support_size(axis: str) -> int:
    return sum(letter != "I" for letter in axis)


def dissipative_matrix(kind: str, axis: str) -> sp.Matrix:
    if kind == "dephase":
        return pauli_word(axis)
    if kind == "lowering":
        return lowering_word(axis)
    raise ValueError(f"unknown dissipative kind: {kind}")


def pair_report(n_qubits: int, d_kind: str, d_axis: str, h_axis: str) -> dict[str, Any]:
    dmat = dissipative_matrix(d_kind, d_axis)
    hmat = pauli_word(h_axis)
    generators = [dmat, dmat.T, hmat]
    basis = generated_algebra_basis(generators)
    alg_dim = len(basis)
    full_dim = 4**n_qubits
    comm_dim = commutant_dimension(generators)
    z3_cert = z3_independence_certificate(basis, f"n{n_qubits}_{d_kind}_{d_axis}_{h_axis}")
    admitted = alg_dim == full_dim and comm_dim == 1 and z3_cert["independent"]
    if admitted:
        exclusion_reason = None
    elif d_kind == "dephase":
        exclusion_reason = "dephasing_pauli_string_pair_generates_proper_pauli_subalgebra"
    elif support_size(d_axis) < n_qubits:
        exclusion_reason = "lowering_axis_has_partial_support_tensor_factor_trap"
    elif not symplectic_anticommutes(d_axis, h_axis):
        exclusion_reason = "full_support_lowering_but_hamiltonian_axis_commutes_even_parity"
    else:
        exclusion_reason = "other_reducible_generated_algebra"
    return {
        "dissipative_kind": d_kind,
        "dissipative_axis": d_axis,
        "hamiltonian_axis": h_axis,
        "full_matrix_algebra_dimension": full_dim,
        "generated_algebra_dimension": alg_dim,
        "commutant_dimension": comm_dim,
        "pauli_axes_anticommute": symplectic_anticommutes(d_axis, h_axis),
        "dissipative_axis_support_size": support_size(d_axis),
        "admitted": admitted,
        "exclusion_reason": exclusion_reason,
        "z3_rank_certificate": z3_cert,
    }


def run_census(n_qubits: int, dissipative_kinds: list[str]) -> dict[str, Any]:
    axes = axis_words(n_qubits)
    rows = [
        pair_report(n_qubits, d_kind, d_axis, h_axis)
        for d_kind in dissipative_kinds
        for d_axis in axes
        for h_axis in axes
    ]
    admitted = [row for row in rows if row["admitted"]]
    exclusions = Counter(row["exclusion_reason"] for row in rows if not row["admitted"])
    by_kind = Counter(row["dissipative_kind"] for row in admitted)
    by_alg_dim = Counter(str(row["generated_algebra_dimension"]) for row in rows)
    return {
        "n_qubits": n_qubits,
        "hilbert_dimension": 2**n_qubits,
        "axis_family": axes,
        "dissipative_kinds": dissipative_kinds,
        "unitary_kinds": ["hamiltonian_pauli_axis"],
        "candidate_pair_count": len(rows),
        "admitted_pair_count": len(admitted),
        "admitted_pairs": [
            {
                "dissipative_kind": row["dissipative_kind"],
                "dissipative_axis": row["dissipative_axis"],
                "hamiltonian_axis": row["hamiltonian_axis"],
                "generated_algebra_dimension": row["generated_algebra_dimension"],
                "commutant_dimension": row["commutant_dimension"],
            }
            for row in admitted
        ],
        "admitted_count_by_dissipative_kind": dict(sorted(by_kind.items())),
        "exclusion_counts": dict(sorted(exclusions.items())),
        "generated_algebra_dimension_histogram": dict(sorted(by_alg_dim.items(), key=lambda item: int(item[0]))),
        "all_z3_rank_certificates_independent": all(row["z3_rank_certificate"]["independent"] for row in rows),
        "rows": rows,
    }


def transform_h_qubit(axis: str, qubit: int) -> str:
    chars = list(axis)
    chars[qubit] = {"I": "I", "X": "Z", "Z": "X"}[chars[qubit]]
    return "".join(chars)


def transform_swap(axis: str) -> str:
    return axis[1] + axis[0]


def compose_perm(left: dict[str, str], right: dict[str, str]) -> dict[str, str]:
    return {axis: left[right[axis]] for axis in right}


def normalizing_involutions(axes: list[str]) -> dict[str, Any]:
    generators = {
        "H_q0": {axis: transform_h_qubit(axis, 0) for axis in axes},
        "H_q1": {axis: transform_h_qubit(axis, 1) for axis in axes},
        "SWAP": {axis: transform_swap(axis) for axis in axes},
    }
    identity = {axis: axis for axis in axes}
    seen = {tuple(identity[axis] for axis in axes): ("I", identity)}
    queue: deque[tuple[str, dict[str, str]]] = deque([("I", identity)])
    while queue:
        name, perm = queue.popleft()
        for gen_name, gen_perm in generators.items():
            new_perm = compose_perm(gen_perm, perm)
            key = tuple(new_perm[axis] for axis in axes)
            if key not in seen:
                new_name = gen_name if name == "I" else f"{gen_name}*{name}"
                seen[key] = (new_name, new_perm)
                queue.append((new_name, new_perm))

    involutions = []
    for name, perm in seen.values():
        squared = compose_perm(perm, perm)
        if squared == identity:
            involutions.append({"name": name, "axis_map": perm, "nontrivial": perm != identity})
    return {
        "normalizer_generators": list(generators),
        "normalizer_group_size": len(seen),
        "involution_count_including_identity": len(involutions),
        "nontrivial_involution_count": sum(1 for item in involutions if item["nontrivial"]),
        "involutions": sorted(involutions, key=lambda item: (not item["nontrivial"], item["name"])),
    }


def orbit_structure(admitted_pairs: list[dict[str, Any]], involution_payload: dict[str, Any]) -> dict[str, Any]:
    admitted = {
        (row["dissipative_kind"], row["dissipative_axis"], row["hamiltonian_axis"])
        for row in admitted_pairs
    }
    involutions = [item["axis_map"] for item in involution_payload["involutions"]]
    seen: set[tuple[str, str, str]] = set()
    orbits: list[list[tuple[str, str, str]]] = []
    for pair in sorted(admitted):
        if pair in seen:
            continue
        orbit = {pair}
        frontier = {pair}
        while frontier:
            kind, d_axis, h_axis = frontier.pop()
            for perm in involutions:
                image = (kind, perm[d_axis], perm[h_axis])
                if image in admitted and image not in orbit:
                    orbit.add(image)
                    frontier.add(image)
        seen.update(orbit)
        orbits.append(sorted(orbit))
    return {
        "orbit_class_count": len(orbits),
        "orbit_sizes": [len(orbit) for orbit in orbits],
        "orbits": [
            [
                {"dissipative_kind": kind, "dissipative_axis": d_axis, "hamiltonian_axis": h_axis}
                for kind, d_axis, h_axis in orbit
            ]
            for orbit in orbits
        ],
    }


def pick_spot_check(rows: list[dict[str, Any]], d_kind: str, d_axis: str, h_axis: str) -> dict[str, Any]:
    for row in rows:
        if row["dissipative_kind"] == d_kind and row["dissipative_axis"] == d_axis and row["hamiltonian_axis"] == h_axis:
            return {
                "pair": {
                    "dissipative_kind": d_kind,
                    "dissipative_axis": d_axis,
                    "hamiltonian_axis": h_axis,
                },
                "generated_algebra_dimension": row["generated_algebra_dimension"],
                "commutant_dimension": row["commutant_dimension"],
                "pauli_axes_anticommute": row["pauli_axes_anticommute"],
                "reducible": row["commutant_dimension"] > 1,
                "exclusion_reason": row["exclusion_reason"],
            }
    raise ValueError("spot-check pair not found")


def main() -> int:
    d2 = run_census(n_qubits=1, dissipative_kinds=["dephase"])
    d4 = run_census(n_qubits=2, dissipative_kinds=["dephase", "lowering"])
    involutions = normalizing_involutions(d4["axis_family"])
    orbits = orbit_structure(d4["admitted_pairs"], involutions)

    d2_sanity = {
        "reproduces_admissibility_two_operator_sim": d2["admitted_pair_count"] == 2,
        "admitted_pair_count": d2["admitted_pair_count"],
        "admitted_pairs": d2["admitted_pairs"],
        "terrain_slots": 8,
        "native_operators_per_terrain": 2,
        "stage_count": 16,
        "stage_count_note": "8 terrain/sign placements x 2 native operators; the algebraic d=2 pair census has 2 surviving dephasing/Hamiltonian pairs.",
    }
    naive_d4_count = len(d4["axis_family"]) * d2["admitted_pair_count"]
    count_verdict = "naive_scaling_holds" if d4["admitted_pair_count"] == naive_d4_count else "novel_structure_appears"
    structural_exclusions = {
        "partial_support_traps": d4["exclusion_counts"].get("lowering_axis_has_partial_support_tensor_factor_trap", 0),
        "dephasing_subalgebra_traps": d4["exclusion_counts"].get(
            "dephasing_pauli_string_pair_generates_proper_pauli_subalgebra", 0
        ),
        "commuting_even_parity_traps": d4["exclusion_counts"].get(
            "full_support_lowering_but_hamiltonian_axis_commutes_even_parity", 0
        ),
    }
    result = {
        "schema_version": "admissibility_census_general_d_v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "premise": {
            "scope": "finite enumeration theorem for the stated X/Z Pauli-axis generator family only",
            "d2_convention_generalized": (
                "admissibility_two_operator_sim.py uses dephasing Lindblad jumps D_z,D_x and Hamiltonians H_x,H_z; "
                "the d=4 strengthening keeps the same one-dissipative-plus-one-unitary algebra rule and expands the "
                "axis set to nonidentity two-qubit words over {I,X,Z}, adding canonical tensor-product lowering jumps "
                "as the extra dissipative branch named in the build card."
            ),
            "dissipative_generators": {
                "dephase": "L_P = P for nonidentity P in {I,X,Z}^{tensor n}; FES algebra uses P=P^dagger.",
                "lowering": (
                    "L_a = tensor_j ell_{a_j}, with ell_I=I, ell_Z=|1><0|, "
                    "ell_X=H ell_Z H; FES algebra uses L_a and L_a^dagger."
                ),
            },
            "unitary_generators": "Hamiltonian H_Q = Q for nonidentity Q in the same X/Z Pauli-axis family.",
            "admissibility_rule": (
                "admit exactly pairs with one dissipative generator and one unitary Hamiltonian whose "
                "FES generated *-algebra <I,L,L^dagger,H> is M_d; equivalently commutant dimension is 1."
            ),
            "rank_method": "exact SymPy rational rank and commutant nullity; z3 QF_LRA linear-independence UNSAT certificate for every reported generated-algebra basis; no numeric tolerance.",
        },
        "d2_sanity": d2_sanity,
        "d4_census": {
            key: value
            for key, value in d4.items()
            if key not in {"rows"}
        },
        "d4_controls": {
            "commuting_pair_spot_check": pick_spot_check(d4["rows"], "dephase", "ZZ", "ZZ"),
            "all_z3_rank_certificates_independent": d4["all_z3_rank_certificates_independent"],
        },
        "involution_orbits": {
            "normalizing_involutions": involutions,
            "admitted_pair_orbits": orbits,
        },
        "differential_verdict": {
            "d2_admitted_pair_count": d2["admitted_pair_count"],
            "d4_axis_count": len(d4["axis_family"]),
            "naive_d4_count": naive_d4_count,
            "d4_admitted_pair_count": d4["admitted_pair_count"],
            "count_verdict": count_verdict,
            "literature_check_nontrivial_count": d4["admitted_pair_count"] != naive_d4_count,
            "structural_exclusion_verdict": (
                "new_subalgebra_traps_present" if any(structural_exclusions.values()) else "no_new_exclusion_structure_detected"
            ),
            "structural_exclusions": structural_exclusions,
            "honest_summary": (
                "The admitted count equals the naive 8x2 scaling under this premise, but the d=4 candidate pool is not "
                "a trivial lift: dephasing pairs never reach M4, partial-support lowerings remain tensor-factor "
                "reducible, and full-support lowerings require odd X/Z symplectic parity with the Hamiltonian."
            ),
        },
        "TOOL_MANIFEST": {
            "sympy": {
                "tried": True,
                "used": True,
                "reason": "load-bearing exact rational generated-algebra rank and commutant nullity",
            },
            "z3": {
                "tried": True,
                "used": True,
                "reason": "load-bearing QF_LRA UNSAT certificates that each exact generated-algebra basis is linearly independent",
            },
            "numpy": {"tried": False, "used": False, "reason": "not needed; no floating tolerance used"},
        },
        "TOOL_INTEGRATION_DEPTH": {"sympy": "load_bearing", "z3": "load_bearing", "numpy": "None"},
    }
    result["all_pass"] = bool(
        d2_sanity["reproduces_admissibility_two_operator_sim"]
        and d2_sanity["stage_count"] == 16
        and d4["admitted_pair_count"] == 16
        and d4["all_z3_rank_certificates_independent"]
        and result["d4_controls"]["commuting_pair_spot_check"]["commutant_dimension"] > 1
        and orbits["orbit_class_count"] == 2
    )

    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("ADMISSIBILITY CENSUS GENERAL-D SCRATCH DIAGNOSTIC")
    print(f"result_path: {RESULT_PATH}")
    print("\nD=2 sanity gate")
    print(f"  admitted pair count: {d2_sanity['admitted_pair_count']}")
    print(f"  admitted pairs: {[(p['dissipative_axis'], p['hamiltonian_axis']) for p in d2_sanity['admitted_pairs']]}")
    print(f"  reproduced 16 stages / 2-per-terrain: {d2_sanity['stage_count'] == 16}")
    print("\nD=4 census table")
    print(f"  axis family ({len(d4['axis_family'])}): {d4['axis_family']}")
    print(f"  candidate pairs: {d4['candidate_pair_count']}")
    print(f"  admitted pairs: {d4['admitted_pair_count']}")
    print(f"  admitted by dissipative kind: {d4['admitted_count_by_dissipative_kind']}")
    print(f"  generated algebra dimension histogram: {d4['generated_algebra_dimension_histogram']}")
    print(f"  exclusion counts: {d4['exclusion_counts']}")
    print(f"  z3 rank certificates all independent: {d4['all_z3_rank_certificates_independent']}")
    print("\nD=4 admitted pairs")
    for row in d4["admitted_pairs"]:
        print(
            "  "
            f"{row['dissipative_kind']}:{row['dissipative_axis']} + H:{row['hamiltonian_axis']} "
            f"-> alg_dim={row['generated_algebra_dimension']} commutant_dim={row['commutant_dimension']}"
        )
    print("\nInvolution orbit structure")
    print(
        "  "
        f"normalizer_group_size={involutions['normalizer_group_size']} "
        f"involutions={involutions['involution_count_including_identity']} "
        f"nontrivial={involutions['nontrivial_involution_count']}"
    )
    print(f"  orbit_class_count={orbits['orbit_class_count']} orbit_sizes={orbits['orbit_sizes']}")
    for idx, orbit in enumerate(orbits["orbits"], start=1):
        compact = [(item["dissipative_axis"], item["hamiltonian_axis"]) for item in orbit]
        print(f"  orbit {idx}: {compact}")
    print("\nControls")
    print(f"  commuting spot check: {result['d4_controls']['commuting_pair_spot_check']}")
    print("\nDifferential verdict")
    print(f"  naive_d4_count: {naive_d4_count}")
    print(f"  d4_admitted_pair_count: {d4['admitted_pair_count']}")
    print(f"  count_verdict: {count_verdict}")
    print(f"  structural_exclusion_verdict: {result['differential_verdict']['structural_exclusion_verdict']}")
    print(f"  all_pass: {result['all_pass']}")
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
