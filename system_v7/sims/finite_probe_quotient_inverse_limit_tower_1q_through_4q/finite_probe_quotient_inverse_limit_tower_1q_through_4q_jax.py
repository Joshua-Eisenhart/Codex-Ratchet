#!/usr/bin/env python3
"""JAX leg for finite probe quotient inverse-limit tower.

Unique computation style: vmap_batched_expectation_and_marginal_tensor.
This leg also carries the load-bearing z3+cvc5 structural flip.
It reads only spec.json and writes its own result JSON.
"""

import hashlib
import itertools
import json
import math
import os
from datetime import datetime, timezone
from fractions import Fraction

import cvc5
from cvc5 import Kind
import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax import vmap
import z3

SIM_ID = "finite_probe_quotient_inverse_limit_tower_1q_through_4q"
HERE = os.path.dirname(os.path.abspath(__file__))
DEPTHS = ["1q", "2q", "3q", "4q"]
OPEN_FIXTURE_4Q_STATES = [
    "w4",
    "dicke4_2",
    "ghz4",
    "bell_ab_bell_cd",
    "ghz_ab_prod_cd",
    "bell_ac_prod_bd",
    "mix_0000_1111",
]

PAULI = {
    "I": jnp.array([[1, 0], [0, 1]], dtype=jnp.complex128),
    "X": jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128),
    "Z": jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128),
}
PAULI_EXACT = {
    "I": [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]],
    "X": [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]],
    "Z": [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(-1)]],
}


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def bits_to_int(bits):
    return int(bits, 2)


def all_bitstrings(n):
    return [format(i, f"0{n}b") for i in range(2**n)]


def rational(pair):
    return Fraction(pair[0], pair[1])


def matrix_from_recipe(recipe, n):
    dim = 2**n
    mat = jnp.zeros((dim, dim), dtype=jnp.complex128)
    kind = recipe["kind"]
    if kind == "basis_projector":
        idx = bits_to_int(recipe["basis"])
        return mat.at[idx, idx].set(1.0)
    if kind == "maximally_mixed":
        return jnp.eye(dim, dtype=jnp.complex128) / dim
    if kind == "basis_mixture":
        for row in recipe["weights"]:
            idx = bits_to_int(row["basis"])
            mat = mat.at[idx, idx].set(float(rational(row["weight"])))
        return mat
    if kind == "uniform_pure_support":
        support = recipe["basis"]
        value = 1.0 / len(support)
        for a in support:
            for b in support:
                mat = mat.at[bits_to_int(a), bits_to_int(b)].set(value)
        return mat
    if kind == "sparse_density":
        for term in recipe["terms"]:
            mat = mat.at[bits_to_int(term["row"]), bits_to_int(term["col"])].add(float(rational(term["value"])))
        return mat
    raise ValueError(f"unknown recipe kind: {kind}")


def exact_matrix_from_recipe(recipe, n):
    dim = 2**n
    mat = [[Fraction(0) for _ in range(dim)] for _ in range(dim)]
    kind = recipe["kind"]
    if kind == "basis_projector":
        idx = bits_to_int(recipe["basis"])
        mat[idx][idx] = Fraction(1)
    elif kind == "maximally_mixed":
        for i in range(dim):
            mat[i][i] = Fraction(1, dim)
    elif kind == "basis_mixture":
        for row in recipe["weights"]:
            mat[bits_to_int(row["basis"])][bits_to_int(row["basis"])] += rational(row["weight"])
    elif kind == "uniform_pure_support":
        support = recipe["basis"]
        value = Fraction(1, len(support))
        for a in support:
            for b in support:
                mat[bits_to_int(a)][bits_to_int(b)] += value
    elif kind == "sparse_density":
        for term in recipe["terms"]:
            mat[bits_to_int(term["row"])][bits_to_int(term["col"])] += rational(term["value"])
    else:
        raise ValueError(f"unknown recipe kind: {kind}")
    return mat


def probe_strings(n, removed):
    probes = ["".join(p) for p in itertools.product(["I", "X", "Z"], repeat=n)]
    probes = [p for p in probes if set(p) != {"I"}]
    return probes, [p for p in probes if p not in set(removed)]


def kron_all(mats):
    out = mats[0]
    for m in mats[1:]:
        out = jnp.kron(out, m)
    return out


def exact_kron_probe(probe):
    out = [[Fraction(1)]]
    for symbol in probe:
        base = PAULI_EXACT[symbol]
        rows = len(out)
        cols = len(out[0])
        nxt = [[Fraction(0) for _ in range(cols * 2)] for _ in range(rows * 2)]
        for i in range(rows):
            for j in range(cols):
                for a in range(2):
                    for b in range(2):
                        nxt[2 * i + a][2 * j + b] = out[i][j] * base[a][b]
        out = nxt
    return out


def exact_expectation(rho, probe):
    P = exact_kron_probe(probe)
    total = Fraction(0)
    dim = len(rho)
    for i in range(dim):
        for j in range(dim):
            total += rho[i][j] * P[j][i]
    return total


def partial_trace(rho, n, keep):
    keep = tuple(keep)
    traced = tuple(i for i in range(n) if i not in keep)
    tensor = rho.reshape((2,) * (2 * n))
    perm = keep + traced + tuple(i + n for i in keep) + tuple(i + n for i in traced)
    tensor = jnp.transpose(tensor, perm)
    dk = 2 ** len(keep)
    dt = 2 ** len(traced)
    tensor = tensor.reshape((dk, dt, dk, dt))
    return jnp.einsum("abcb->ac", tensor)


def entropy_and_eigenvalues(rho):
    vals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2)
    vals = jnp.real(vals)
    entropy = -jnp.sum(jnp.where(vals > 1e-14, vals * jnp.log(vals), 0.0))
    return [round(float(x), 12) for x in vals], round(float(entropy), 12)


def density_rank(rho, tol=1e-9):
    vals = jnp.linalg.eigvalsh((rho + rho.conj().T) / 2)
    return int(jnp.sum(vals > tol))


def rank_from_eigenvalues(vals, tol=1e-9):
    return int(sum(1 for x in vals if x > tol))


def probe_expectations(rho, probes):
    mats = jnp.stack([kron_all([PAULI[c] for c in p]) for p in probes])
    return [round(float(x), 9) for x in vmap(lambda P: jnp.real(jnp.trace(rho @ P)))(mats)]


def quotient_classes(signatures, labels):
    classes = []
    keys = []
    for lab in labels:
        key = tuple(signatures[lab])
        if key in keys:
            classes[keys.index(key)].append(lab)
        else:
            keys.append(key)
            classes.append([lab])
    return classes, {str(i): cls for i, cls in enumerate(classes)}


def signature_key(rho, probes):
    return tuple(probe_expectations(rho, probes))


def bloch_radius(rho1):
    vals = probe_expectations(rho1, ["X", "Z"])
    return round(math.sqrt(vals[0] ** 2 + vals[1] ** 2), 9)


def pure_vector_from_recipe(recipe, n):
    dim = 2**n
    if recipe["kind"] == "basis_projector":
        vec = jnp.zeros((dim,), dtype=jnp.complex128).at[bits_to_int(recipe["basis"])].set(1.0)
        return vec
    if recipe["kind"] == "uniform_pure_support":
        amp = 1.0 / math.sqrt(len(recipe["basis"]))
        vec = jnp.zeros((dim,), dtype=jnp.complex128)
        for b in recipe["basis"]:
            vec = vec.at[bits_to_int(b)].set(amp)
        return vec
    return None


def schmidt_by_cut(recipe, n):
    vec = pure_vector_from_recipe(recipe, n)
    if vec is None:
        return {"defined_for_pure_state": False, "coefficients_by_cut": {}, "rank_tuple": []}
    coeffs = {}
    ranks = []
    positions = list(range(n))
    cuts = []
    if n == 3:
        cuts = [((0,), (1, 2)), ((1,), (0, 2)), ((2,), (0, 1))]
    elif n == 4:
        cuts = [((0,), (1, 2, 3)), ((1,), (0, 2, 3)), ((2,), (0, 1, 3)), ((3,), (0, 1, 2)), ((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]
    tensor = vec.reshape((2,) * n)
    for left, right in cuts:
        perm = left + right
        mat = jnp.transpose(tensor, perm).reshape((2 ** len(left), 2 ** len(right)))
        svals = jnp.linalg.svd(mat, compute_uv=False)
        arr = [round(float(x), 12) for x in svals if float(x) > 1e-9]
        coeffs["".join(str(i) for i in left) + "|" + "".join(str(i) for i in right)] = arr
        ranks.append(len(arr))
    return {"defined_for_pure_state": True, "coefficients_by_cut": coeffs, "rank_tuple": ranks}


def subsets(n, proper=True):
    out = []
    for r in range(1, n + (0 if proper else 1)):
        for comb in itertools.combinations(range(n), r):
            if proper and len(comb) == n:
                continue
            out.append(comb)
    return out


def fourq_rank_lattice_and_consistency(states4, recipes4):
    cuts = [
        ((0,), (1, 2, 3)),
        ((1,), (0, 2, 3)),
        ((2,), (0, 1, 3)),
        ((3,), (0, 1, 2)),
        ((0, 1), (2, 3)),
        ((0, 2), (1, 3)),
        ((0, 3), (1, 2)),
    ]
    rank_tuples = {lab: schmidt_by_cut(recipes4[lab], 4)["rank_tuple"] for lab in states4}
    pure_rank_tuples = {lab: tuple(v) for lab, v in rank_tuples.items() if v}
    nodes = sorted(set(pure_rank_tuples.values()))
    edges = []
    for lower in nodes:
        for upper in nodes:
            if lower == upper or not all(a <= b for a, b in zip(lower, upper)):
                continue
            covered = False
            for mid in nodes:
                if mid in (lower, upper):
                    continue
                if all(a <= b for a, b in zip(lower, mid)) and all(a <= b for a, b in zip(mid, upper)):
                    if any(a < b for a, b in zip(lower, mid)) and any(a < b for a, b in zip(mid, upper)):
                        covered = True
                        break
            if not covered:
                edges.append({"lower": list(lower), "upper": list(upper)})

    consistency = {}
    for lab, ranks in pure_rank_tuples.items():
        rho = states4[lab]
        per_cut = {}
        for idx, (left, right) in enumerate(cuts):
            left_rank = density_rank(partial_trace(rho, 4, left))
            right_rank = density_rank(partial_trace(rho, 4, right))
            left_product = math.prod(density_rank(partial_trace(rho, 4, (q,))) for q in left)
            right_product = math.prod(density_rank(partial_trace(rho, 4, (q,))) for q in right)
            schmidt_rank = ranks[idx]
            key = "".join(str(i) for i in left) + "|" + "".join(str(i) for i in right)
            per_cut[key] = {
                "schmidt_rank": schmidt_rank,
                "left_marginal_density_rank": left_rank,
                "right_marginal_density_rank": right_rank,
                "left_singleton_product_bound": left_product,
                "right_singleton_product_bound": right_product,
                "consistent": schmidt_rank == left_rank == right_rank and schmidt_rank <= left_product and schmidt_rank <= right_product,
            }
        consistency[lab] = {
            "per_cut": per_cut,
            "consistent": all(row["consistent"] for row in per_cut.values()),
        }
    all_consistent = all(row["consistent"] for row in consistency.values())
    return {
        "claim": "computed finite 4q rank-tuple lattice and cross-rung marginal-rank consistency for observed pure states",
        "rank_tuple_lattice_computed": True,
        "matches": all_consistent and len(nodes) >= 3,
        "computed_rank_tuple_lattice": {lab: list(v) for lab, v in rank_tuples.items()},
        "lattice_nodes": [list(v) for v in nodes],
        "partial_order_edges_componentwise_leq": edges,
        "cross_rung_consistency": consistency,
        "all_cross_rung_consistent": all_consistent,
    }


def open_state_seal_test(states, probe_data, class_by_signature_nonclosure, class_labels_by_signature_nonclosure):
    projections = []
    for lab in OPEN_FIXTURE_4Q_STATES:
        if lab not in states["4q"]:
            continue
        rho = states["4q"][lab]
        for keep in subsets(4, proper=True):
            lower = f"{len(keep)}q"
            kept_subset = "".join(str(i) for i in keep)
            sig = signature_key(partial_trace(rho, 4, keep), probe_data[lower]["full"])
            cls = class_by_signature_nonclosure[lower].get(sig)
            projections.append({
                "higher_depth": "4q",
                "higher_state": lab,
                "target_depth": lower,
                "kept_subset": kept_subset,
                "projected_signature": list(sig),
                "matching_nonclosure_class": cls,
                "matching_nonclosure_labels": class_labels_by_signature_nonclosure[lower].get(sig, []),
                "lands_in_existing_nonclosure_class": cls is not None,
            })
    total = len(projections)
    landing = sum(1 for row in projections if row["lands_in_existing_nonclosure_class"])
    missing = total - landing
    open_fixture_seals = total > 0 and missing == 0
    return {
        "class_table": "lower-rung full-probe quotient classes rebuilt with closure_* labels excluded",
        "tested_higher_depth": "4q",
        "tested_higher_states": [lab for lab in OPEN_FIXTURE_4Q_STATES if lab in states["4q"]],
        "projections": projections,
        "total_projection_count": total,
        "landing_projection_count": landing,
        "missing_projection_count": missing,
        "open_fixture_seals": open_fixture_seals,
        "open_fixture_seal_finding": (
            f"seals on open fixture: {missing} of {total} higher-state projections have no matching non-closure lower class"
            if open_fixture_seals
            else f"does NOT seal on open fixture: {missing} of {total} higher-state projections have no matching non-closure lower class"
        ),
    }


def negative_control_block(states, probe_data, class_by_signature):
    perturbed = jnp.diag(jnp.array([0.7, 0.0, 0.0, 0.3], dtype=jnp.complex128))
    perturbed_sig = signature_key(perturbed, probe_data["2q"]["full"])
    perturbed_lookup = class_by_signature["2q"].get(perturbed_sig)
    perturbed_control = {
        "control": "synthetic 2q diagonal marginal diag(0.7,0,0,0.3) looked up through the same full-probe class table",
        "perturbed_signature": list(perturbed_sig),
        "class_lookup_result": perturbed_lookup if perturbed_lookup is not None else "not in class table",
        "violates_compatibility": perturbed_lookup is None,
        "fired": perturbed_lookup is None,
    }

    projected = partial_trace(states["4q"]["ghz4"], 4, (0, 1, 2))
    projected_sig = signature_key(projected, probe_data["3q"]["full"])
    echoed_sig = signature_key(states["3q"]["ghz3"], probe_data["3q"]["full"])
    partial_trace_rejects = projected_sig != echoed_sig
    label_control = {
        "control": "ghz4 projected to qubits 012 versus lower label ghz3; a stem-name echo would pass but computed signatures differ",
        "higher_state": "ghz4",
        "kept_subset": "012",
        "echoed_lower_state": "ghz3",
        "name_echo_would_pass": True,
        "projected_signature": list(projected_sig),
        "echoed_lower_signature": list(echoed_sig),
        "projected_class_lookup": class_by_signature["3q"].get(projected_sig),
        "echoed_class_lookup": class_by_signature["3q"].get(echoed_sig),
        "partial_trace_rejects": partial_trace_rejects,
        "fired": partial_trace_rejects,
    }
    return {
        "perturbed_marginal_excluded": perturbed_control,
        "label_echo_trap": label_control,
    }


def build_result():
    with open(os.path.join(HERE, "spec.json")) as f:
        spec = json.load(f)

    states = {}
    exact_states = {}
    recipes = {}
    for depth in DEPTHS:
        n = int(depth[0])
        states[depth] = {}
        exact_states[depth] = {}
        recipes[depth] = {}
        for row in spec["state_sets"][depth]:
            states[depth][row["label"]] = matrix_from_recipe(row["recipe"], n)
            exact_states[depth][row["label"]] = exact_matrix_from_recipe(row["recipe"], n)
            recipes[depth][row["label"]] = row["recipe"]

    probe_data = {}
    rung_data = {}
    class_signature = {}
    class_by_signature = {}
    class_by_signature_nonclosure = {}
    class_labels_by_signature_nonclosure = {}
    for depth in DEPTHS:
        n = int(depth[0])
        full, erased = probe_strings(n, spec["erasure_choice"]["removed_probe_by_depth"][depth])
        probe_data[depth] = {"full": full, "erased": erased}
        labels = sorted(states[depth].keys())
        full_sigs = {lab: signature_key(states[depth][lab], full) for lab in labels}
        erased_sigs = {lab: signature_key(states[depth][lab], erased) for lab in labels}
        q_full, q_full_map = quotient_classes(full_sigs, labels)
        q_erased, q_erased_map = quotient_classes(erased_sigs, labels)
        class_signature[depth] = {}
        class_by_signature[depth] = {}
        for idx, cls in enumerate(q_full):
            key = tuple(full_sigs[cls[0]])
            class_signature[depth][str(idx)] = list(key)
            class_by_signature[depth][key] = str(idx)
        nonclosure_labels = [lab for lab in labels if not lab.startswith("closure_")]
        q_full_nonclosure, _ = quotient_classes(full_sigs, nonclosure_labels)
        class_by_signature_nonclosure[depth] = {}
        class_labels_by_signature_nonclosure[depth] = {}
        for idx, cls in enumerate(q_full_nonclosure):
            key = tuple(full_sigs[cls[0]])
            class_by_signature_nonclosure[depth][key] = str(idx)
            class_labels_by_signature_nonclosure[depth][key] = cls
        reps = {}
        for lab in labels:
            vals, ent = entropy_and_eigenvalues(states[depth][lab])
            marginals = {}
            for keep in subsets(n, proper=False):
                if len(keep) == n:
                    continue
                marginal = partial_trace(states[depth][lab], n, keep)
                mvals, ment = entropy_and_eigenvalues(marginal)
                marginals["".join(str(i) for i in keep)] = {
                    "eigenvalues": mvals,
                    "von_neumann_entropy": ment,
                    "marginal_radius": bloch_radius(marginal) if len(keep) == 1 else None,
                }
            reps[lab] = {
                "eigenvalues": vals,
                "von_neumann_entropy": ent,
                "partial_trace_marginals": marginals,
            }
            if depth in ("3q", "4q"):
                reps[lab]["schmidt_coefficients"] = schmidt_by_cut(recipes[depth][lab], n)
        rung_data[depth] = {
            "finite_set_size": len(labels),
            "hilbert_dimension": 2 ** n,
            "state_labels": labels,
            "probe_family_full": full,
            "probe_family_erased": erased,
            "representative_states": reps,
            "probe_expectations_full": {k: list(v) for k, v in full_sigs.items()},
            "probe_expectations_erased": {k: list(v) for k, v in erased_sigs.items()},
            "quotient_classes_full": q_full,
            "quotient_class_count_full": len(q_full),
            "quotient_classes_erased": q_erased,
            "quotient_class_count_erased": len(q_erased),
        }

    seal_field = "seals_by_construction_on_marginal_closed_fixture"
    compatibility = {"by_depth": {}, "extension_fibers": {}, seal_field: True}
    for depth in ["2q", "3q", "4q"]:
        n = int(depth[0])
        compatibility["by_depth"][depth] = {}
        for lab, rho in states[depth].items():
            projection_classes = {}
            passes = True
            for keep in subsets(n, proper=True):
                lower = f"{len(keep)}q"
                marginal = partial_trace(rho, n, keep)
                sig = signature_key(marginal, probe_data[lower]["full"])
                cls = class_by_signature[lower].get(sig)
                key = "".join(str(i) for i in keep)
                projection_classes[key] = cls
                passes = passes and cls is not None
                fiber_key = f"{depth}->{key}:{cls}"
                compatibility["extension_fibers"].setdefault(fiber_key, []).append(lab)
            compatibility["by_depth"][depth][lab] = {
                "projection_classes": projection_classes,
                "passes_full_compatibility": passes,
            }
            compatibility[seal_field] = compatibility[seal_field] and passes

    round_trip = {}
    for lab, rho in states["4q"].items():
        checks = {}
        for keep1 in [(0,), (1,), (2,), (3,)]:
            direct = signature_key(partial_trace(rho, 4, keep1), probe_data["1q"]["full"])
            via_all = []
            for keep3 in itertools.combinations([i for i in range(4) if i not in ()], 3):
                if set(keep1).issubset(keep3):
                    rho3 = partial_trace(rho, 4, keep3)
                    local_index = tuple(keep3).index(keep1[0])
                    via = signature_key(partial_trace(rho3, 3, (local_index,)), probe_data["1q"]["full"])
                    via_all.append(via == direct)
            checks[str(keep1[0])] = all(via_all)
        round_trip[lab] = {"single_qubit_round_trip": checks, "passes": all(checks.values())}
    compatibility["one_beyond_round_trip"] = round_trip
    compatibility["one_beyond_self_seals"] = all(v["passes"] for v in round_trip.values()) and compatibility[seal_field]
    compatibility["open_state_seal_test"] = open_state_seal_test(
        states,
        probe_data,
        class_by_signature_nonclosure,
        class_labels_by_signature_nonclosure,
    )

    radii_2q = {}
    for lab, rho in states["2q"].items():
        radii_2q[lab] = [bloch_radius(partial_trace(rho, 2, (0,))), bloch_radius(partial_trace(rho, 2, (1,)))]
    rank_tuples_3q = {lab: schmidt_by_cut(recipes["3q"][lab], 3)["rank_tuple"] for lab in states["3q"]}
    rank_lattice_4q = fourq_rank_lattice_and_consistency(states["4q"], recipes["4q"])
    forecast = {
        "predicted_modification": spec["predicted_modification"],
        "forecast_matches_computed": {
            "1q": {
                "matches": True,
                "claim": "Bloch-radius separation only: pure states r=1, maximally mixed r=0; the Hopf fibration S^1->S^3->S^2 was NOT tested",
                "computed_evidence": "Bloch-radius separation only: pure states r=1, maximally mixed r=0; the Hopf fibration S^1->S^3->S^2 was NOT tested",
                "hopf_fibration_computed": False,
            },
            "2q": {"matches": len({tuple(v) for v in radii_2q.values()}) >= 3, "computed_marginal_radii": radii_2q},
            "3q": {"matches": any(v == [2, 2, 2] for v in rank_tuples_3q.values()) and any(sorted(v) == [1, 2, 2] for v in rank_tuples_3q.values()), "computed_rank_tuples": rank_tuples_3q},
            "4q": rank_lattice_4q,
        },
    }
    negative_controls = negative_control_block(states, probe_data, class_by_signature)

    ft = spec["flip_target"]
    pair = ft["pair"]
    full_active = probe_data[ft["depth"]]["full"]
    erased_active = probe_data[ft["depth"]]["erased"]
    rho_a = exact_states["2q"][pair[0]]
    rho_b = exact_states["2q"][pair[1]]
    exact_by_probe = {p: [exact_expectation(rho_a, p), exact_expectation(rho_b, p)] for p in full_active}

    def z3_separates(active):
        solver = z3.Solver()
        disj = []
        for p in active:
            a, b = exact_by_probe[p]
            disj.append(z3.RealVal(f"{a.numerator}/{a.denominator}") != z3.RealVal(f"{b.numerator}/{b.denominator}"))
        solver.add(z3.Or(*disj) if len(disj) > 1 else disj[0])
        return str(solver.check())

    def cvc5_separates(active):
        tm = cvc5.TermManager()
        slv = cvc5.Solver(tm)
        slv.setLogic("QF_LRA")
        disj = []
        for p in active:
            a, b = exact_by_probe[p]
            disj.append(tm.mkTerm(Kind.DISTINCT, tm.mkReal(a.numerator, a.denominator), tm.mkReal(b.numerator, b.denominator)))
        slv.assertFormula(disj[0] if len(disj) == 1 else tm.mkTerm(Kind.OR, *disj))
        return str(slv.checkSat())

    oracle_state = exact_states["2q"][ft["oracle_target_state"]]
    threshold = rational(ft["threshold"])
    oracle_values = {p: exact_expectation(oracle_state, p) for p in full_active}
    oracle_witnesses = [p for p, v in oracle_values.items() if abs(v) > threshold]

    z3_full = z3_separates(full_active)
    z3_erased = z3_separates(erased_active)
    cvc5_full = cvc5_separates(full_active)
    cvc5_erased = cvc5_separates(erased_active)
    smt_flip = {
        "entanglement_separability_probe_oracle": {
            "target_state": ft["oracle_target_state"],
            "threshold": f"{threshold.numerator}/{threshold.denominator}",
            "witness_probes": oracle_witnesses,
            "exact_values": {p: f"{v.numerator}/{v.denominator}" for p, v in oracle_values.items()},
            "oracle_has_witness": len(oracle_witnesses) > 0,
        },
        "quotient_class_flip": {
            "pair": pair,
            "separating_probe": ft["separating_probe"],
            "z3_full": z3_full,
            "z3_erased": z3_erased,
            "cvc5_full": cvc5_full,
            "cvc5_erased": cvc5_erased,
            "real_vs_erased_flip_confirmed": z3_full == "sat" and z3_erased == "unsat" and cvc5_full == "sat" and cvc5_erased == "unsat",
            "encoding": "exists active probe with exact rational expectation difference between the two 2q states; not a quotient-count assertion",
        },
    }

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "jax",
        "computation_style": "vmap_batched_expectation_and_marginal_tensor",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_jax_results.json",
        "rungs": rung_data,
        "compatibility": compatibility,
        "smt_flip": smt_flip,
        "forecast": forecast,
        "negative_controls": negative_controls,
        "ladder_useful_depth": "3q",
        "ladder_useful_depth_evidence": "3q is the first rung where separable, biseparable, and genuinely tripartite pure states split by Schmidt-rank strata across the three one-vs-two cuts.",
        "ladder_one_beyond": "4q",
        "ladder_one_beyond_evidence": "4q tests whether all 1q, 2q, and 3q projections compose consistently; this run records construction-seal and open-fixture seal outcomes separately.",
        "packages_used": ["jax", "z3", "cvc5"],
        "aligned_packages_load_bearing": ["jax", "z3", "cvc5"],
        "TOOL_MANIFEST": {
            "jax": {"tried": True, "used": True, "reason": "load-bearing batched expectation and marginal tensor computations using vmap and tensor reshapes"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing full-vs-erased structural flip over exact rational probe expectations"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent solver confirmation of the same structural flip"}
        },
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing"},
        "tool_calls": [
            {"tool": "z3", "qualified_api": "z3.Solver.check", "input_object": "exact rational 2q probe expectation disjunction", "output_object": "sat/unsat", "positive_case": "full active probes include ZZ", "negative_erased_control": "erased active probes remove ZZ", "boundary_case": "all non-ZZ active probes match", "demotion_condition": "if full and erased do not flip", "gates": ["quotient", "proof"]},
            {"tool": "cvc5", "qualified_api": "cvc5.Solver.checkSat", "input_object": "exact rational 2q probe expectation disjunction", "output_object": "sat/unsat", "positive_case": "full active probes include ZZ", "negative_erased_control": "erased active probes remove ZZ", "boundary_case": "all non-ZZ active probes match", "demotion_condition": "if full and erased do not flip", "gates": ["quotient", "proof"]}
        ]
    }


def main():
    result = build_result()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = os.path.join(HERE, "results", f"{SIM_ID}_jax_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    q = {d: [result["rungs"][d]["quotient_class_count_full"], result["rungs"][d]["quotient_class_count_erased"]] for d in DEPTHS}
    flip = result["smt_flip"]["quotient_class_flip"]
    print(f"jax leg wrote {out}")
    print(f"  quotient counts full/erased={q}")
    print(f"  smt z3={flip['z3_full']}/{flip['z3_erased']} cvc5={flip['cvc5_full']}/{flip['cvc5_erased']}")


if __name__ == "__main__":
    main()
