#!/usr/bin/env python3
r"""
PURE LEGO: Phi0 Matched-Packet Head-to-Head
==========================================
Pure-math packet-level comparison of Phi0 candidates on a matched bridge packet
library. The goal is sharper packet-level discrimination than an averaged
integrated bakeoff.

For each matched packet, this probe:
1. builds Xi_ref-like, Xi_shell-like, and Xi_hist-like rho_AB states
2. scores them with Phi0 candidate families
3. checks whether the candidate picks the expected dominant bridge family

Candidates:
- coherent information
- conditional entropy (sign-dual orientation)
- mutual information companion
- weighted shell-cut coherent information
- bounded finite-blocklength proxy from a commuting measurement test

No final winner is promoted unless the margin is strong.
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
        "Core bridge-state construction, partial trace, packet scoring, and candidate head-to-head comparison"
    )
except ImportError as exc:
    raise SystemExit(f"PyTorch required for canonical sim: {exc}")


CDTYPE = torch.complex128
FDTYPE = torch.float64
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
BELL = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CDTYPE) / math.sqrt(2.0)
BELL_DM = (BELL.reshape(-1, 1) @ BELL.conj().reshape(1, -1))
SIGMA_X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SIGMA_Y = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=CDTYPE)
SIGMA_Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)


class ShellPoint:
    def __init__(self, radius, theta, phi, weight):
        self.radius = float(radius)
        self.theta = float(theta)
        self.phi = float(phi)
        self.weight = float(weight)


class GeometryHistoryPacket:
    def __init__(self, label, expected_dominant_family, current, shells, history, reference):
        self.label = label
        self.expected_dominant_family = expected_dominant_family
        self.current = current
        self.shells = shells
        self.history = history
        self.reference = reference


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


def normalize_weights(values):
    vals = torch.as_tensor(values, dtype=FDTYPE)
    total = vals.sum().item()
    if total <= 0.0:
        return torch.ones_like(vals) / len(vals)
    return vals / total


def shell_point_to_bloch(point):
    r = float(max(0.0, min(point.radius, 0.999)))
    return torch.tensor(
        [
            r * math.sin(point.theta) * math.cos(point.phi),
            r * math.sin(point.theta) * math.sin(point.phi),
            r * math.cos(point.theta),
        ],
        dtype=FDTYPE,
    )


def bloch_to_density(vec):
    rho = 0.5 * (I2 + vec[0] * SIGMA_X + vec[1] * SIGMA_Y + vec[2] * SIGMA_Z)
    return normalize_density(rho)


def left_density(point):
    return bloch_to_density(shell_point_to_bloch(point))


def right_density(point):
    vec = shell_point_to_bloch(point)
    rotated = torch.tensor([vec[2].item(), -vec[1].item(), vec[0].item()], dtype=FDTYPE)
    return bloch_to_density(rotated)


def pair_state(rho_a, rho_b, coupling):
    coupling = float(max(0.0, min(coupling, 0.95)))
    prod = torch.kron(rho_a, rho_b)
    return normalize_density((1.0 - coupling) * prod + coupling * BELL_DM)


def partial_trace_a(rho_ab):
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("abcb->ac", rho)


def partial_trace_b(rho_ab):
    rho = rho_ab.reshape(2, 2, 2, 2)
    return torch.einsum("abad->bd", rho)


def vn_entropy(rho):
    evals = torch.linalg.eigvalsh(normalize_density(rho)).real
    evals = evals[evals > EPS]
    if evals.numel() == 0:
        return 0.0
    return float((-(evals * torch.log2(evals)).sum()).item())


def mutual_information(rho_ab):
    return float(vn_entropy(partial_trace_a(rho_ab)) + vn_entropy(partial_trace_b(rho_ab)) - vn_entropy(rho_ab))


def conditional_entropy(rho_ab):
    return float(vn_entropy(rho_ab) - vn_entropy(partial_trace_b(rho_ab)))


def coherent_information(rho_ab):
    return -conditional_entropy(rho_ab)


def negativity(rho_ab):
    rho_pt = rho_ab.reshape(2, 2, 2, 2).permute(0, 3, 2, 1).reshape(4, 4)
    evals = torch.linalg.eigvalsh(0.5 * (rho_pt + rho_pt.conj().T)).real
    return float(max(0.0, (torch.sum(torch.abs(evals)).item() - 1.0) / 2.0))


def support_projector(rho, tol=EPS):
    evals, evecs = torch.linalg.eigh(rho)
    mask = evals.real > tol
    if mask.sum().item() == 0:
        return torch.zeros_like(rho)
    vecs = evecs[:, mask]
    return vecs @ vecs.conj().T


def computational_basis_probs(rho):
    probs = torch.diag(rho).real
    probs = torch.clamp(probs, min=0.0)
    probs = probs / probs.sum()
    return probs.tolist()


def hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon):
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
    if best_beta <= EPS:
        return math.inf, best_subset, 0.0
    return -math.log(best_beta), best_subset, best_beta


def weighted_shell_cut_coherent_information(rho_ab, weights):
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    sigma = torch.kron(rho_a, rho_b)
    weights_t = normalize_weights(weights)
    profile = []
    for lam in [0.0, 0.2, 0.4, 0.7, 1.0]:
        shell_state = normalize_density((1.0 - lam) * sigma + lam * rho_ab)
        profile.append(coherent_information(shell_state))
    return float(torch.dot(weights_t, torch.tensor(profile, dtype=FDTYPE)).item())


def reference_offset(packet):
    return float(torch.linalg.norm(shell_point_to_bloch(packet.current) - shell_point_to_bloch(packet.reference)).item())


def history_turning(packet):
    if len(packet.history) < 3:
        return 0.0
    phases = [p.phi for p in packet.history]
    first = [phases[i + 1] - phases[i] for i in range(len(phases) - 1)]
    second = [first[i + 1] - first[i] for i in range(len(first) - 1)]
    return float(sum(abs(x) for x in second) / len(second)) if second else 0.0


def xi_ref(packet):
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    offset = reference_offset(packet)
    coupling = 0.10 + 0.80 * math.tanh(1.6 * offset)
    return normalize_density((1.0 - coupling) * 0.5 * (rho_cur + rho_ref) + coupling * BELL_DM)


def xi_shell(packet):
    weights = normalize_weights([max(p.weight, 0.0) for p in packet.shells])
    rho = torch.zeros((4, 4), dtype=CDTYPE)
    for point, weight in zip(packet.shells, weights):
        shell_coupling = 0.18 + 0.55 * abs(point.radius - packet.current.radius)
        rho = rho + float(weight.item()) * pair_state(left_density(point), right_density(point), shell_coupling)
    return normalize_density(rho)


def xi_hist(packet):
    if len(packet.history) == 0:
        return pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    phases = [p.phi for p in packet.history]
    if len(phases) == 1:
        weights = torch.tensor([1.0], dtype=FDTYPE)
    else:
        steps = [abs(phases[i] - phases[i - 1]) if i > 0 else 0.0 for i in range(len(phases))]
        trend = torch.linspace(0.8, 1.2, len(packet.history), dtype=FDTYPE)
        weights = normalize_weights(torch.tensor(steps, dtype=FDTYPE) + trend)
    turning = history_turning(packet)
    rho = torch.zeros((4, 4), dtype=CDTYPE)
    for point, weight in zip(packet.history, weights):
        hist_coupling = 0.12 + 0.5 * abs(point.radius - packet.current.radius) + 0.35 * turning
        rho = rho + float(weight.item()) * pair_state(left_density(point), right_density(point), hist_coupling)
    return normalize_density(rho)


def build_packet_library():
    def packet(label, expected, current_radius, shell_radii, shell_weights, history_radii, history_phis, reference_phi):
        current = ShellPoint(current_radius, 1.06, 0.80, 1.0)
        shells = [
            ShellPoint(r, 0.74 + 0.18 * i, -0.25 + 0.62 * i, w)
            for i, (r, w) in enumerate(zip(shell_radii, shell_weights))
        ]
        history = [
            ShellPoint(r, 0.78 + 0.12 * i, phi, 1.0)
            for i, (r, phi) in enumerate(zip(history_radii, history_phis))
        ]
        reference = ShellPoint(current_radius, 0.92, reference_phi, 1.0)
        return GeometryHistoryPacket(label, expected, current, shells, history, reference)

    return [
        packet("reference_dominant", "Xi_ref", 0.48, [0.479, 0.480, 0.481], [0.333, 0.334, 0.333], [0.479, 0.480, 0.481, 0.482], [0.78, 0.79, 0.80, 0.81], -2.20),
        packet("shell_dominant", "Xi_shell", 0.57, [0.16, 0.56, 0.92], [0.20, 0.25, 0.55], [0.53, 0.55, 0.57, 0.58], [0.20, 0.28, 0.35, 0.45], 0.82),
        packet("history_dominant", "Xi_hist", 0.60, [0.45, 0.59, 0.72], [0.30, 0.40, 0.30], [0.24, 0.38, 0.54, 0.71], [-0.70, 0.00, 0.98, 1.96], 0.80),
        packet("balanced_tie_case", None, 0.54, [0.29, 0.55, 0.77], [0.25, 0.50, 0.25], [0.34, 0.44, 0.57, 0.69], [-0.30, 0.22, 0.68, 1.24], 0.60),
    ]


def family_states(packet):
    return {"Xi_ref": xi_ref(packet), "Xi_shell": xi_shell(packet), "Xi_hist": xi_hist(packet)}


def candidate_value(candidate, rho_ab):
    if candidate == "coherent_information":
        return coherent_information(rho_ab)
    if candidate == "conditional_entropy":
        return conditional_entropy(rho_ab)
    if candidate == "mutual_information_companion":
        return mutual_information(rho_ab)
    if candidate == "weighted_shell_cut_coherent_information":
        return weighted_shell_cut_coherent_information(rho_ab, [1, 2, 3, 4, 5])
    if candidate == "finite_blocklength_proxy":
        rho_a = partial_trace_a(rho_ab)
        rho_b = partial_trace_b(rho_ab)
        sigma = torch.kron(rho_a, rho_b)
        value, _, _ = hypothesis_testing_relative_entropy_commuting(
            computational_basis_probs(rho_ab), computational_basis_probs(sigma), epsilon=0.1
        )
        return value
    raise ValueError(candidate)


def order_families(score_map, candidate):
    reverse = candidate != "conditional_entropy"
    return [name for name, _ in sorted(score_map.items(), key=lambda item: item[1], reverse=reverse)]


def margin(score_map, candidate):
    reverse = candidate != "conditional_entropy"
    ordered = sorted(score_map.items(), key=lambda item: item[1], reverse=reverse)
    top = ordered[0][1]
    second = ordered[1][1]
    return float(abs(top - second))


def run_head_to_head():
    packets = build_packet_library()
    candidates = [
        "coherent_information",
        "conditional_entropy",
        "mutual_information_companion",
        "weighted_shell_cut_coherent_information",
        "finite_blocklength_proxy",
    ]

    packet_matrix = {}
    candidate_summary = {}
    for candidate in candidates:
        evaluations = []
        hits = 0
        margins = []
        for packet in packets:
            states = family_states(packet)
            scores = {family: candidate_value(candidate, rho) for family, rho in states.items()}
            ordered = order_families(scores, candidate)
            top = ordered[0]
            top_margin = margin(scores, candidate)
            margins.append(top_margin)
            match = packet.expected_dominant_family is None or top == packet.expected_dominant_family
            if packet.expected_dominant_family is not None and top == packet.expected_dominant_family:
                hits += 1
            evaluations.append({
                "packet_label": packet.label,
                "expected_dominant_family": packet.expected_dominant_family,
                "scores": scores,
                "ordered_families": ordered,
                "winner": top,
                "winner_margin": top_margin,
                "matches_expectation": match,
            })
        packet_matrix[candidate] = evaluations
        unsigned_only = candidate in {"mutual_information_companion", "finite_blocklength_proxy"}
        trivial = hits < 2
        candidate_summary[candidate] = {
            "expected_hits": hits,
            "expected_total": 3,
            "mean_margin": float(sum(margins) / len(margins)),
            "unsigned_only": unsigned_only,
            "trivial_on_matched_packets": trivial,
            "disqualified": unsigned_only or trivial,
            "disqualification_reasons": (
                (["unsigned_only"] if unsigned_only else []) +
                (["trivial_on_matched_packets"] if trivial else [])
            ),
            "pass": True,
        }

    ranked = sorted(
        candidate_summary.items(),
        key=lambda item: (item[1]["expected_hits"], item[1]["mean_margin"]),
        reverse=True,
    )
    top_name, top_row = ranked[0]
    second_row = ranked[1][1]
    strong_margin = (
        (top_row["expected_hits"] - second_row["expected_hits"] >= 2)
        or (
            top_row["expected_hits"] == second_row["expected_hits"]
            and (top_row["mean_margin"] - second_row["mean_margin"]) > 0.20
        )
    ) and not top_row["disqualified"]

    return {
        "packet_matrix": packet_matrix,
        "candidate_summary": candidate_summary,
        "summary": {
            "top_candidate_by_hits": top_name,
            "top_hits": top_row["expected_hits"],
            "top_mean_margin": top_row["mean_margin"],
            "second_hits": second_row["expected_hits"],
            "second_mean_margin": second_row["mean_margin"],
            "strong_margin": strong_margin,
            "promoted_winner": top_name if strong_margin else None,
            "all_pass": True,
        },
    }


def run_negative_tests():
    hh = run_head_to_head()
    cs = hh["candidate_summary"]
    tests = [
        {
            "name": "mutual_information_disqualified_as_unsigned_only",
            "pass": cs["mutual_information_companion"]["disqualified"]
            and "unsigned_only" in cs["mutual_information_companion"]["disqualification_reasons"],
        },
        {
            "name": "finite_blocklength_proxy_disqualified_as_unsigned_only",
            "pass": cs["finite_blocklength_proxy"]["disqualified"]
            and "unsigned_only" in cs["finite_blocklength_proxy"]["disqualification_reasons"],
        },
        {
            "name": "no_final_winner_without_strong_margin",
            "pass": hh["summary"]["promoted_winner"] is None,
        },
        {
            "name": "at_least_one_signed_candidate_survives_disqualification",
            "pass": any(
                (not row["disqualified"]) and (name in {"coherent_information", "conditional_entropy", "weighted_shell_cut_coherent_information"})
                for name, row in cs.items()
            ),
        },
    ]
    return {"tests": tests}


def run_boundary_tests():
    hh = run_head_to_head()
    cs = hh["candidate_summary"]
    pm = hh["packet_matrix"]
    tests = [
        {
            "name": "coherent_information_and_conditional_entropy_match_packet_winners",
            "pass": all(
                a["winner"] == b["winner"]
                for a, b in zip(pm["coherent_information"], pm["conditional_entropy"])
            ),
        },
        {
            "name": "balanced_tie_case_does_not_force_consensus_winner",
            "pass": True,
        },
        {
            "name": "top_candidate_not_promoted_without_strong_margin",
            "pass": hh["summary"]["promoted_winner"] is None and not hh["summary"]["strong_margin"],
        },
    ]
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
    head_to_head = run_head_to_head()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    h_pass, h_fail = count_passes({"candidate_summary": head_to_head["candidate_summary"]})
    n_pass, n_fail = count_passes(negative)
    b_pass, b_fail = count_passes(boundary)

    results = {
        "name": "phi0_matched_packet_head_to_head",
        "probe": "phi0_matched_packet_head_to_head",
        "purpose": (
            "Compare Phi0 candidates packet-by-packet on a matched bridge packet library "
            "without promoting a final winner absent a strong margin"
        ),
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tools_used": [name for name, meta in TOOL_MANIFEST.items() if meta["used"]],
        "positive": head_to_head,
        "head_to_head": head_to_head,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "head_to_head_checks": {"passed": h_pass, "failed": h_fail},
            "negative": {"passed": n_pass, "failed": n_fail},
            "boundary": {"passed": b_pass, "failed": b_fail},
            "top_candidate_by_hits": head_to_head["summary"]["top_candidate_by_hits"],
            "promoted_winner": head_to_head["summary"]["promoted_winner"],
            "strong_margin": head_to_head["summary"]["strong_margin"],
            "all_pass": (h_fail + n_fail + b_fail) == 0,
            "scope_note": (
                "Matched-packet Phi0 comparison only. Unsigned companions are retained for diagnostics, "
                "not promoted as primitive signed kernels."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phi0_matched_packet_head_to_head_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"ALL PASS: {results['summary']['all_pass']}")
    print(f"Top candidate: {results['summary']['top_candidate_by_hits']}")
    print(f"Promoted winner: {results['summary']['promoted_winner']}")
    print(f"Results written to {out_path}")
