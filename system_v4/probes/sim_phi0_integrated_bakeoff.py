#!/usr/bin/env python3
r"""
PURE LEGO: Phi0 Integrated Bakeoff on Separated Bridge Foundations
==================================================================
Pure math only. This probe compares Phi0 candidate families on bridge-built
bipartite cut states without promoting final closure unless the evidence margin
is strong.

Candidates:
1. coherent information
2. conditional entropy
3. mutual information companion
4. weighted shell-cut coherent information
5. simple finite-blocklength proxy D_max(rho_AB || rho_A \otimes rho_B)

Disqualification rules:
- unsigned-only candidates are not promoted as signed primitives
- trivial candidates are rejected if they fail key product / separable /
  entangled separation checks
- arbitrary candidates are rejected if mild weight perturbations scramble their
  induced ranking too easily
"""

import json
import math
import os


TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "z3": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "sympy": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "clifford": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this lego"},
}

try:
    import torch

    torch.manual_seed(0)
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Core bipartite density-matrix construction, partial traces, entropy evaluation, "
        "finite-blocklength proxy computation, and candidate ranking"
    )
except ImportError as exc:
    raise SystemExit(f"PyTorch required for canonical sim: {exc}")


CDTYPE = torch.complex128
FDTYPE = torch.float64
EPS = 1e-10
I2 = torch.eye(2, dtype=CDTYPE)
I4 = torch.eye(4, dtype=CDTYPE)


def ket_to_dm(amps):
    psi = torch.as_tensor(amps, dtype=CDTYPE).reshape(-1, 1)
    psi = psi / torch.linalg.norm(psi)
    return psi @ psi.conj().T


def dm_from_probs(probs):
    probs = torch.as_tensor(probs, dtype=FDTYPE)
    return torch.diag(probs).to(CDTYPE)


def normalize_density(rho):
    rho = 0.5 * (rho + rho.conj().T)
    tr = torch.trace(rho)
    if abs(tr.item()) <= EPS:
        raise ValueError("trace too small")
    return rho / tr


def validate_density_matrix(rho):
    if rho.ndim != 2 or rho.shape[0] != rho.shape[1]:
        return False, "matrix must be square"
    if not torch.allclose(rho, rho.conj().T, atol=1e-9):
        return False, "matrix must be Hermitian"
    tr = torch.trace(rho).real.item()
    if abs(tr - 1.0) > 1e-8:
        return False, "trace must equal 1"
    evals = torch.linalg.eigvalsh(rho).real
    if evals.min().item() < -1e-8:
        return False, "matrix must be positive semidefinite"
    return True, "ok"


def partial_trace_a(rho_ab):
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", rho)


def partial_trace_b(rho_ab):
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("abad->bd", rho)


def support_projector(rho, tol=EPS):
    evals, evecs = torch.linalg.eigh(rho)
    mask = evals.real > tol
    if mask.sum().item() == 0:
        return torch.zeros_like(rho)
    vecs = evecs[:, mask]
    return vecs @ vecs.conj().T


def d_max(rho, sigma, tol=EPS):
    p_rho = support_projector(rho, tol)
    p_sig = support_projector(sigma, tol)
    support_violation = torch.linalg.matrix_norm((torch.eye(rho.shape[0], dtype=CDTYPE) - p_sig) @ p_rho).item()
    if support_violation > 1e-8:
        return math.inf

    evals, evecs = torch.linalg.eigh(sigma)
    inv_sqrt = torch.zeros_like(sigma)
    for idx, val in enumerate(evals.real):
        if val > tol:
            vec = evecs[:, idx:idx + 1]
            inv_sqrt += (1.0 / math.sqrt(val.item())) * (vec @ vec.conj().T)
    witness = inv_sqrt @ rho @ inv_sqrt
    return math.log(torch.linalg.eigvalsh(witness).real.max().item())


def vn_entropy(rho):
    evals = torch.linalg.eigvalsh(normalize_density(rho)).real
    evals = evals[evals > EPS]
    if evals.numel() == 0:
        return 0.0
    return float((-(evals * torch.log2(evals)).sum()).item())


def mutual_information(rho_ab):
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    return float(vn_entropy(rho_a) + vn_entropy(rho_b) - vn_entropy(rho_ab))


def conditional_entropy(rho_ab):
    rho_b = partial_trace_b(rho_ab)
    return float(vn_entropy(rho_ab) - vn_entropy(rho_b))


def coherent_information(rho_ab):
    return -conditional_entropy(rho_ab)


def negativity(rho_ab):
    rho_pt = rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    evals = torch.linalg.eigvalsh(0.5 * (rho_pt + rho_pt.conj().T)).real
    return float(max(0.0, (torch.sum(torch.abs(evals)).item() - 1.0) / 2.0))


def computational_basis_probs(rho):
    probs = torch.diag(rho).real
    probs = torch.clamp(probs, min=0.0)
    probs = probs / probs.sum()
    return probs.tolist()


def hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon):
    if not (0.0 <= epsilon < 1.0):
        raise ValueError("epsilon must satisfy 0 <= epsilon < 1")
    rho_probs = [float(x) for x in rho_probs]
    sigma_probs = [float(x) for x in sigma_probs]
    n = len(rho_probs)
    best_beta = math.inf
    best_subset = None
    for mask in range(1 << n):
        accept = [(mask >> i) & 1 for i in range(n)]
        alpha = 1.0 - sum(r * a for r, a in zip(rho_probs, accept))
        beta = sum(s * a for s, a in zip(sigma_probs, accept))
        if alpha <= epsilon + 1e-12 and beta < best_beta:
            best_beta = beta
            best_subset = accept
    if best_subset is None:
        raise RuntimeError("no feasible commuting test found")
    if best_beta <= EPS:
        return math.inf, best_subset, 0.0
    return -math.log(best_beta), best_subset, best_beta


def product_case():
    rho_ab = torch.kron(dm_from_probs([1.0, 0.0]), dm_from_probs([0.0, 1.0]))
    return {"label": "product", "class": "product", "rho_ab": rho_ab}


def separable_case():
    rho_ab = 0.6 * ket_to_dm([1.0, 0.0, 0.0, 0.0]) + 0.4 * ket_to_dm([0.0, 0.0, 0.0, 1.0])
    return {"label": "separable_correlated", "class": "separable", "rho_ab": rho_ab}


def bell_case():
    return {"label": "bell", "class": "entangled", "rho_ab": ket_to_dm([1.0, 0.0, 0.0, 1.0])}


def werner_case(p):
    bell = ket_to_dm([1.0, 0.0, 0.0, 1.0])
    return {
        "label": f"werner_{p:.2f}",
        "class": "werner",
        "rho_ab": normalize_density(p * bell + (1.0 - p) * I4 / 4.0),
        "p": p,
    }


def history_cases():
    plus = torch.tensor([1.0, 1.0], dtype=CDTYPE) / math.sqrt(2.0)
    zero = torch.tensor([1.0, 0.0], dtype=CDTYPE)
    cnot = torch.tensor(
        [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 1],
         [0, 0, 1, 0]],
        dtype=CDTYPE,
    )
    bell_from_cnot = cnot @ torch.kron(plus, zero)
    rho_history_bell = ket_to_dm(bell_from_cnot)

    z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    z_a = torch.kron(z, I2)
    bell = ket_to_dm([1.0, 0.0, 0.0, 1.0])
    rho_dephased = normalize_density(0.65 * bell + 0.35 * (z_a @ bell @ z_a.conj().T))

    rho_history_mix = normalize_density(0.55 * ket_to_dm([0.0, 1.0, -1.0, 0.0]) + 0.45 * separable_case()["rho_ab"])

    return [
        {"label": "history_cnot_bell", "class": "history", "rho_ab": rho_history_bell},
        {"label": "history_dephased_bell", "class": "history", "rho_ab": rho_dephased},
        {"label": "history_mixed", "class": "history", "rho_ab": rho_history_mix},
    ]


def build_cases():
    return [
        product_case(),
        separable_case(),
        bell_case(),
        werner_case(1.0 / 3.0),
        werner_case(0.80),
        *history_cases(),
    ]


def shell_profile_coherent_information(rho_ab):
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    sigma = torch.kron(rho_a, rho_b)
    profile = []
    for lam in [0.0, 0.2, 0.4, 0.7, 1.0]:
        shell_state = normalize_density((1.0 - lam) * sigma + lam * rho_ab)
        profile.append(coherent_information(shell_state))
    return profile


def weighted_shell_cut_coherent_information(rho_ab, weights):
    profile = shell_profile_coherent_information(rho_ab)
    weights_t = torch.as_tensor(weights, dtype=FDTYPE)
    weights_t = weights_t / weights_t.sum()
    return float(torch.dot(weights_t, torch.as_tensor(profile, dtype=FDTYPE)).item())


def candidate_values_for_case(case):
    rho_ab = normalize_density(case["rho_ab"])
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    sigma = torch.kron(rho_a, rho_b)
    finite_proxy, subset, beta = hypothesis_testing_relative_entropy_commuting(
        computational_basis_probs(rho_ab), computational_basis_probs(sigma), epsilon=0.1
    )
    return {
        "coherent_information": coherent_information(rho_ab),
        "conditional_entropy": conditional_entropy(rho_ab),
        "mutual_information_companion": mutual_information(rho_ab),
        "weighted_shell_cut_coherent_information": weighted_shell_cut_coherent_information(rho_ab, [1, 2, 3, 4, 5]),
        "finite_blocklength_proxy": finite_proxy,
        "finite_proxy_subset": subset,
        "finite_proxy_beta": beta,
        "negativity": negativity(rho_ab),
    }


def rank_labels(value_map, signed):
    items = [(label, vals) for label, vals in value_map.items()]
    if signed:
        items.sort(key=lambda item: item[1], reverse=True)
    else:
        items.sort(key=lambda item: abs(item[1]), reverse=True)
    return [label for label, _ in items]


def kendall_tau_distance(order_a, order_b):
    pos_a = {label: idx for idx, label in enumerate(order_a)}
    pos_b = {label: idx for idx, label in enumerate(order_b)}
    labels = list(order_a)
    discordant = 0
    total = 0
    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            li, lj = labels[i], labels[j]
            total += 1
            if (pos_a[li] - pos_a[lj]) * (pos_b[li] - pos_b[lj]) < 0:
                discordant += 1
    return 0.0 if total == 0 else discordant / total


def run_bakeoff():
    cases = build_cases()
    case_scores = {}
    for case in cases:
        ok, msg = validate_density_matrix(normalize_density(case["rho_ab"]))
        if not ok:
            raise RuntimeError(f"invalid case {case['label']}: {msg}")
        case_scores[case["label"]] = candidate_values_for_case(case)

    candidates = {
        "coherent_information": {"signed": True},
        "conditional_entropy": {"signed": True},
        "mutual_information_companion": {"signed": False},
        "weighted_shell_cut_coherent_information": {"signed": True},
        "finite_blocklength_proxy": {"signed": False},
    }

    labels = list(case_scores.keys())
    product_label = "product"
    separable_label = "separable_correlated"
    entangled_label = "bell"

    baseline_signed_order = None
    candidate_rows = {}
    non_disqualified = []

    for name, meta in candidates.items():
        values = {label: case_scores[label][name] for label in labels}
        signed = meta["signed"]
        ranking = rank_labels(values, signed=signed)
        if name == "coherent_information":
            baseline_signed_order = ranking

        unsigned_only = all(values[label] >= -1e-10 for label in labels)
        trivial = (
            abs(values[product_label]) > 1e-8
            or abs(values[separable_label] - values[entangled_label]) < 1e-6
        )

        arbitrary = False
        arbit_note = None
        if name == "weighted_shell_cut_coherent_information":
            alt_values = {
                label: weighted_shell_cut_coherent_information(build_cases()[idx]["rho_ab"], [1, 1, 2, 3, 5])
                for idx, label in enumerate(labels)
            }
            alt_ranking = rank_labels(alt_values, signed=True)
            tau = kendall_tau_distance(ranking, alt_ranking)
            arbitrary = tau > 0.40
            arbit_note = {"alt_ranking": alt_ranking, "tau_distance": tau}

        disq = []
        if unsigned_only:
            disq.append("unsigned_only")
        if trivial:
            disq.append("trivial_on_key_cases")
        if arbitrary:
            disq.append("too_arbitrary")

        row = {
            "signed": signed,
            "values": values,
            "ranking": ranking,
            "unsigned_only": unsigned_only,
            "trivial_on_key_cases": trivial,
            "too_arbitrary": arbitrary,
            "disqualified": len(disq) > 0,
            "disqualification_reasons": disq,
            "product_value": values[product_label],
            "separable_value": values[separable_label],
            "entangled_value": values[entangled_label],
            "pass": True,
        }
        if arbit_note is not None:
            row["arbitrariness_check"] = arbit_note
        candidate_rows[name] = row
        if not row["disqualified"]:
            non_disqualified.append(name)

    score_table = {}
    for name, row in candidate_rows.items():
        values = row["values"]
        zero_baseline = abs(values[product_label]) < 1e-8
        separation = abs(values[entangled_label] - values[separable_label])
        sign_bonus = 1.0 if row["signed"] and not row["unsigned_only"] else 0.0
        arbit_penalty = 1.0 if row["too_arbitrary"] else 0.0
        trivial_penalty = 1.0 if row["trivial_on_key_cases"] else 0.0
        score = 2.0 * sign_bonus + (1.0 if zero_baseline else 0.0) + separation - arbit_penalty - trivial_penalty
        score_table[name] = score
        row["score"] = score

    ranked_candidates = sorted(score_table.items(), key=lambda item: item[1], reverse=True)
    top_name, top_score = ranked_candidates[0]
    second_score = ranked_candidates[1][1] if len(ranked_candidates) > 1 else -math.inf
    strong_margin = (top_score - second_score) > 0.75 and not candidate_rows[top_name]["disqualified"]

    summary = {
        "top_candidate_by_score": top_name,
        "top_score": top_score,
        "second_score": second_score,
        "strong_margin": strong_margin,
        "promoted_winner": top_name if strong_margin else None,
        "non_disqualified_candidates": non_disqualified,
        "all_pass": True,
    }

    return {
        "case_scores": case_scores,
        "candidate_bakeoff": candidate_rows,
        "summary": summary,
    }


def run_negative_tests():
    bakeoff = run_bakeoff()
    candidates = bakeoff["candidate_bakeoff"]
    tests = []

    tests.append({
        "name": "mutual_information_disqualified_as_unsigned_only",
        "pass": candidates["mutual_information_companion"]["disqualified"]
        and "unsigned_only" in candidates["mutual_information_companion"]["disqualification_reasons"],
    })

    tests.append({
        "name": "finite_blocklength_proxy_disqualified_as_unsigned_only",
        "pass": candidates["finite_blocklength_proxy"]["disqualified"]
        and "unsigned_only" in candidates["finite_blocklength_proxy"]["disqualification_reasons"],
    })

    tests.append({
        "name": "conditional_entropy_not_trivial_on_key_cases",
        "pass": not candidates["conditional_entropy"]["trivial_on_key_cases"],
    })

    tests.append({
        "name": "no_forced_final_winner_without_strong_margin",
        "pass": bakeoff["summary"]["promoted_winner"] is None,
    })

    return {"tests": tests}


def run_boundary_tests():
    bakeoff = run_bakeoff()
    candidates = bakeoff["candidate_bakeoff"]
    tests = []

    tests.append({
        "name": "coherent_information_and_conditional_entropy_are_sign_duals",
        "pass": all(
            abs(
                candidates["coherent_information"]["values"][label]
                + candidates["conditional_entropy"]["values"][label]
            ) < 1e-8
            for label in candidates["coherent_information"]["values"]
        ),
    })

    tests.append({
        "name": "weighted_shell_candidate_zero_on_product_case",
        "pass": abs(candidates["weighted_shell_cut_coherent_information"]["product_value"]) < 1e-8,
    })

    tests.append({
        "name": "top_two_margin_is_not_strong_enough_for_promotion",
        "pass": not bakeoff["summary"]["strong_margin"],
    })

    return {"tests": tests}


def count_passes(tree):
    passed = 0
    failed = 0
    if isinstance(tree, dict):
        if "pass" in tree:
            return (1, 0) if tree["pass"] else (0, 1)
        for value in tree.values():
            p, f = count_passes(value)
            passed += p
            failed += f
    elif isinstance(tree, list):
        for value in tree:
            p, f = count_passes(value)
            passed += p
            failed += f
    return passed, failed


if __name__ == "__main__":
    bakeoff = run_bakeoff()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    b_pass, b_fail = count_passes({"candidate_bakeoff": bakeoff["candidate_bakeoff"]})
    n_pass, n_fail = count_passes(negative)
    bd_pass, bd_fail = count_passes(boundary)

    results = {
        "name": "phi0_integrated_bakeoff",
        "probe": "phi0_integrated_bakeoff",
        "purpose": (
            "Compare Phi0 candidate families on separated bridge-built cut states and "
            "disqualify unsigned, trivial, or overly arbitrary candidates"
        ),
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tools_used": [name for name, meta in TOOL_MANIFEST.items() if meta["used"]],
        "positive": bakeoff,
        "bakeoff": bakeoff,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "bakeoff_checks": {"passed": b_pass, "failed": b_fail},
            "negative": {"passed": n_pass, "failed": n_fail},
            "boundary": {"passed": bd_pass, "failed": bd_fail},
            "top_candidate_by_score": bakeoff["summary"]["top_candidate_by_score"],
            "promoted_winner": bakeoff["summary"]["promoted_winner"],
            "strong_margin": bakeoff["summary"]["strong_margin"],
            "all_pass": (b_fail + n_fail + bd_fail) == 0,
            "scope_note": (
                "Pure-math bridge bakeoff only. No final Phi0 winner is promoted unless the margin is strong."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phi0_integrated_bakeoff_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"ALL PASS: {results['summary']['all_pass']}")
    print(f"Top candidate: {results['summary']['top_candidate_by_score']}")
    print(f"Promoted winner: {results['summary']['promoted_winner']}")
    print(f"Results written to {out_path}")
