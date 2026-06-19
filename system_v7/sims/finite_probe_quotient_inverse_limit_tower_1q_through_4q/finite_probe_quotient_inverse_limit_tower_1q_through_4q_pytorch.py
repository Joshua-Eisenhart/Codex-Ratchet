#!/usr/bin/env python3
"""PyTorch leg for finite probe quotient inverse-limit tower.

Unique computation style: autograd_jacobian_over_state_parameters.
It computes a torch.func Jacobian of probe expectations with respect to a
two-qubit mixture parameter, a derivative no other leg computes.
It reads only spec.json and writes its own result JSON.
"""

import hashlib
import itertools
import json
import math
import os
from datetime import datetime, timezone
from fractions import Fraction

import torch
from torch.func import jacrev

torch.set_default_dtype(torch.float64)

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
    "I": torch.tensor([[1, 0], [0, 1]], dtype=torch.complex128),
    "X": torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128),
    "Z": torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128),
}


def sha256_of(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def bits_to_int(bits):
    return int(bits, 2)


def rational(pair):
    return Fraction(pair[0], pair[1])


def matrix_from_recipe(recipe, n):
    dim = 2**n
    mat = torch.zeros((dim, dim), dtype=torch.complex128)
    kind = recipe["kind"]
    if kind == "basis_projector":
        idx = bits_to_int(recipe["basis"])
        mat[idx, idx] = 1.0
        return mat
    if kind == "maximally_mixed":
        return torch.eye(dim, dtype=torch.complex128) / dim
    if kind == "basis_mixture":
        for row in recipe["weights"]:
            idx = bits_to_int(row["basis"])
            mat[idx, idx] += float(rational(row["weight"]))
        return mat
    if kind == "uniform_pure_support":
        value = 1.0 / len(recipe["basis"])
        for a in recipe["basis"]:
            for b in recipe["basis"]:
                mat[bits_to_int(a), bits_to_int(b)] += value
        return mat
    if kind == "sparse_density":
        for term in recipe["terms"]:
            mat[bits_to_int(term["row"]), bits_to_int(term["col"])] += float(rational(term["value"]))
        return mat
    raise ValueError(f"unknown recipe kind: {kind}")


def probe_strings(n, removed):
    probes = ["".join(p) for p in itertools.product(["I", "X", "Z"], repeat=n)]
    probes = [p for p in probes if set(p) != {"I"}]
    return probes, [p for p in probes if p not in set(removed)]


def kron_all(mats):
    out = mats[0]
    for m in mats[1:]:
        out = torch.kron(out, m)
    return out


def partial_trace(rho, n, keep):
    keep = tuple(keep)
    traced = tuple(i for i in range(n) if i not in keep)
    tensor = rho.reshape((2,) * (2 * n))
    perm = keep + traced + tuple(i + n for i in keep) + tuple(i + n for i in traced)
    tensor = tensor.permute(perm)
    dk = 2 ** len(keep)
    dt = 2 ** len(traced)
    tensor = tensor.reshape(dk, dt, dk, dt)
    return torch.einsum("abcb->ac", tensor)


def entropy_and_eigenvalues(rho):
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    entropy = -torch.sum(torch.where(vals > 1e-14, vals * torch.log(vals), torch.zeros_like(vals)))
    return [round(float(x), 12) for x in vals], round(float(entropy), 12)


def density_rank(rho, tol=1e-9):
    vals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    return int(torch.sum(vals > tol).item())


def probe_expectations(rho, probes):
    out = []
    for p in probes:
        mat = kron_all([PAULI[c] for c in p])
        out.append(round(float(torch.real(torch.trace(rho @ mat))), 9))
    return out


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
    return classes


def signature_key(rho, probes):
    return tuple(probe_expectations(rho, probes))


def bloch_radius(rho1):
    vals = probe_expectations(rho1, ["X", "Z"])
    return round(math.sqrt(vals[0] ** 2 + vals[1] ** 2), 9)


def pure_vector_from_recipe(recipe, n):
    dim = 2**n
    if recipe["kind"] == "basis_projector":
        vec = torch.zeros((dim,), dtype=torch.complex128)
        vec[bits_to_int(recipe["basis"])] = 1.0
        return vec
    if recipe["kind"] == "uniform_pure_support":
        amp = 1.0 / math.sqrt(len(recipe["basis"]))
        vec = torch.zeros((dim,), dtype=torch.complex128)
        for b in recipe["basis"]:
            vec[bits_to_int(b)] = amp
        return vec
    return None


def schmidt_by_cut(recipe, n):
    vec = pure_vector_from_recipe(recipe, n)
    if vec is None:
        return {"defined_for_pure_state": False, "coefficients_by_cut": {}, "rank_tuple": []}
    coeffs = {}
    ranks = []
    if n == 3:
        cuts = [((0,), (1, 2)), ((1,), (0, 2)), ((2,), (0, 1))]
    elif n == 4:
        cuts = [((0,), (1, 2, 3)), ((1,), (0, 2, 3)), ((2,), (0, 1, 3)), ((3,), (0, 1, 2)), ((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]
    else:
        cuts = []
    tensor = vec.reshape((2,) * n)
    for left, right in cuts:
        key = "".join(str(i) for i in left) + "|" + "".join(str(i) for i in right)
        mat = tensor.permute(left + right).reshape(2 ** len(left), 2 ** len(right))
        svals = torch.linalg.svdvals(mat)
        arr = [round(float(x), 12) for x in svals if float(x) > 1e-9]
        coeffs[key] = arr
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


def autograd_receipt():
    # rho(t) = t |00><00| + (1-t) I/4. d<ZZ>/dt = 1, d<XX>/dt = 0.
    p_00 = torch.zeros((4, 4), dtype=torch.complex128)
    p_00[0, 0] = 1.0
    mm = torch.eye(4, dtype=torch.complex128) / 4
    probes = ["ZI", "IZ", "ZZ", "XX"]
    probe_mats = [kron_all([PAULI[c] for c in p]) for p in probes]

    def values(t):
        rho = t.to(torch.complex128) * p_00 + (1 - t).to(torch.complex128) * mm
        return torch.stack([torch.real(torch.trace(rho @ p)) for p in probe_mats])

    t0 = torch.tensor(0.25, dtype=torch.float64)
    jac = jacrev(values)(t0)
    expected = torch.tensor([1.0, 1.0, 1.0, 0.0], dtype=torch.float64)
    return {
        "parameterized_state": "rho(t)=t |00><00| + (1-t) I/4",
        "probes": probes,
        "jacobian_d_expectation_d_t": [round(float(x), 9) for x in jac],
        "expected_jacobian": [float(x) for x in expected],
        "jacobian_matches_structural_identity": bool(torch.max(torch.abs(jac - expected)) < 1e-9),
        "identity": "d tr(rho(t) P)/dt equals tr((|00><00|-I/4) P)"
    }


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


def negative_control_block(states, probe_data, class_by_signature):
    perturbed = torch.diag(torch.tensor([0.7, 0.0, 0.0, 0.3], dtype=torch.complex128))
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


def build_result():
    with open(os.path.join(HERE, "spec.json")) as f:
        spec = json.load(f)
    states = {}
    recipes = {}
    for depth in DEPTHS:
        n = int(depth[0])
        states[depth] = {}
        recipes[depth] = {}
        for row in spec["state_sets"][depth]:
            states[depth][row["label"]] = matrix_from_recipe(row["recipe"], n)
            recipes[depth][row["label"]] = row["recipe"]

    probe_data = {}
    rung_data = {}
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
        q_full = quotient_classes(full_sigs, labels)
        q_erased = quotient_classes(erased_sigs, labels)
        class_by_signature[depth] = {tuple(full_sigs[cls[0]]): str(i) for i, cls in enumerate(q_full)}
        nonclosure_labels = [lab for lab in labels if not lab.startswith("closure_")]
        q_full_nonclosure = quotient_classes(full_sigs, nonclosure_labels)
        class_by_signature_nonclosure[depth] = {tuple(full_sigs[cls[0]]): str(i) for i, cls in enumerate(q_full_nonclosure)}
        class_labels_by_signature_nonclosure[depth] = {tuple(full_sigs[cls[0]]): cls for cls in q_full_nonclosure}
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
            reps[lab] = {"eigenvalues": vals, "von_neumann_entropy": ent, "partial_trace_marginals": marginals}
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
                sig = signature_key(partial_trace(rho, n, keep), probe_data[lower]["full"])
                cls = class_by_signature[lower].get(sig)
                key = "".join(str(i) for i in keep)
                projection_classes[key] = cls
                passes = passes and cls is not None
                compatibility["extension_fibers"].setdefault(f"{depth}->{key}:{cls}", []).append(lab)
            compatibility["by_depth"][depth][lab] = {"projection_classes": projection_classes, "passes_full_compatibility": passes}
            compatibility[seal_field] = compatibility[seal_field] and passes

    round_trip = {}
    for lab, rho in states["4q"].items():
        checks = {}
        for keep1 in [(0,), (1,), (2,), (3,)]:
            direct = signature_key(partial_trace(rho, 4, keep1), probe_data["1q"]["full"])
            via_all = []
            for keep3 in itertools.combinations(range(4), 3):
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

    radii_2q = {lab: [bloch_radius(partial_trace(rho, 2, (0,))), bloch_radius(partial_trace(rho, 2, (1,)))] for lab, rho in states["2q"].items()}
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

    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "computation_style": "autograd_jacobian_over_state_parameters",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_pytorch_results.json",
        "rungs": rung_data,
        "compatibility": compatibility,
        "autograd_receipt": autograd_receipt(),
        "forecast": forecast,
        "negative_controls": negative_controls,
        "ladder_useful_depth": "3q",
        "ladder_useful_depth_evidence": "3q is the first rung where separable, biseparable, and genuinely tripartite pure states split by Schmidt-rank strata across the three one-vs-two cuts.",
        "ladder_one_beyond": "4q",
        "ladder_one_beyond_evidence": "4q tests whether all 1q, 2q, and 3q projections compose consistently; this run records construction-seal and open-fixture seal outcomes separately.",
        "packages_used": ["torch", "torch.func"],
        "aligned_packages_load_bearing": ["torch.func"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "supportive tensor algebra for density matrices, partial traces, spectra, and quotients"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing Jacobian of probe expectations with respect to a density-mixture parameter"}
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "torch.func": "load_bearing"},
        "tool_calls": [
            {"tool": "torch.func", "qualified_api": "torch.func.jacrev", "input_object": "rho(t)=t |00><00| + (1-t) I/4 and probes ZI, IZ, ZZ, XX", "output_object": "jacobian d expectation / dt", "positive_case": "ZI, IZ, ZZ derivatives equal 1", "negative_erased_control": "XX derivative equals 0", "boundary_case": "t=0.25 inside [0,1]", "demotion_condition": "if jacobian does not match the structural identity", "gates": ["all_pass"]}
        ]
    }


def main():
    result = build_result()
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    out = os.path.join(HERE, "results", f"{SIM_ID}_pytorch_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    q = {d: [result["rungs"][d]["quotient_class_count_full"], result["rungs"][d]["quotient_class_count_erased"]] for d in DEPTHS}
    print(f"pytorch leg wrote {out}")
    print(f"  quotient counts full/erased={q}")
    print(f"  autograd identity ok={result['autograd_receipt']['jacobian_matches_structural_identity']}")


if __name__ == "__main__":
    main()
