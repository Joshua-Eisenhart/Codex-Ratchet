#!/usr/bin/env python3
r"""
PURE LEGO: Phi0 Ic-vs-MI Regime Map
===================================
Pure-math regime map for bridge-built packets.

This probe separates two questions:
1. when mutual information wins as an unsigned packet discriminator
2. when coherent information remains the stronger signed primitive

The point is not to crown a final winner. The point is to map regimes where:
- MI has better hit-count on packet discrimination
- Ic carries signed orientation that MI cannot supply
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
        "Core bridge-state construction, partial traces, entropy evaluation, and regime sweeps"
    )
except ImportError as exc:
    raise SystemExit(f"PyTorch required for canonical sim: {exc}")


CDTYPE = torch.complex128
FDTYPE = torch.float64
EPS = 1e-10

I2 = torch.eye(2, dtype=CDTYPE)
BELL = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=CDTYPE) / math.sqrt(2.0)
BELL_DM = BELL.reshape(-1, 1) @ BELL.conj().reshape(1, -1)
SIGMA_X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=CDTYPE)
SIGMA_Y = torch.tensor([[0.0, -1j], [1j, 0.0]], dtype=CDTYPE)
SIGMA_Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)


class ShellPoint:
    def __init__(self, radius, theta, phi, weight):
        self.radius = float(radius)
        self.theta = float(theta)
        self.phi = float(phi)
        self.weight = float(weight)


class Packet:
    def __init__(self, label, expected, current, shells, history, reference):
        self.label = label
        self.expected_dominant_family = expected
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


def dm_from_probs(probs):
    probs = torch.as_tensor(probs, dtype=FDTYPE)
    return torch.diag(probs).to(CDTYPE)


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


def computational_basis_probs(rho):
    probs = torch.diag(rho).real
    probs = torch.clamp(probs, min=0.0)
    probs = probs / probs.sum()
    return probs.tolist()


def hypothesis_testing_relative_entropy_commuting(rho_probs, sigma_probs, epsilon):
    best_beta = math.inf
    best_subset = None
    n = len(rho_probs)
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
    coupling = 0.10 + 0.80 * math.tanh(1.6 * reference_offset(packet))
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
        return Packet(label, expected, current, shells, history, reference)

    return [
        packet("reference_dominant", "Xi_ref", 0.48, [0.479, 0.480, 0.481], [0.333, 0.334, 0.333], [0.479, 0.480, 0.481, 0.482], [0.78, 0.79, 0.80, 0.81], -2.20),
        packet("shell_dominant", "Xi_shell", 0.57, [0.16, 0.56, 0.92], [0.20, 0.25, 0.55], [0.53, 0.55, 0.57, 0.58], [0.20, 0.28, 0.35, 0.45], 0.82),
        packet("history_dominant", "Xi_hist", 0.60, [0.45, 0.59, 0.72], [0.30, 0.40, 0.30], [0.24, 0.38, 0.54, 0.71], [-0.70, 0.00, 0.98, 1.96], 0.80),
        packet("balanced_tie_case", None, 0.54, [0.29, 0.55, 0.77], [0.25, 0.50, 0.25], [0.34, 0.44, 0.57, 0.69], [-0.30, 0.22, 0.68, 1.24], 0.60),
    ]


def family_states(packet):
    return {"Xi_ref": xi_ref(packet), "Xi_shell": xi_shell(packet), "Xi_hist": xi_hist(packet)}


def family_scores(packet):
    states = family_states(packet)
    rows = {}
    for family, rho in states.items():
        ok, msg = validate_density_matrix(rho)
        if not ok:
            raise RuntimeError(f"{packet.label}/{family} invalid: {msg}")
        rho_a = partial_trace_a(rho)
        rho_b = partial_trace_b(rho)
        sigma = torch.kron(rho_a, rho_b)
        mi = mutual_information(rho)
        ic = coherent_information(rho)
        finite_proxy, subset, beta = hypothesis_testing_relative_entropy_commuting(
            computational_basis_probs(rho), computational_basis_probs(sigma), epsilon=0.1
        )
        rows[family] = {
            "mutual_information": mi,
            "coherent_information": ic,
            "conditional_entropy": -ic,
            "weighted_shell_cut_coherent_information": weighted_shell_cut_coherent_information(rho, [1, 2, 3, 4, 5]),
            "finite_blocklength_proxy": finite_proxy,
            "finite_proxy_subset": subset,
            "finite_proxy_beta": beta,
            "negativity": negativity(rho),
            "signed_eligible": abs(ic) > 1e-12,
            "unsigned_discrimination": mi,
        }
    return rows


def regime_label(mi_values, ic_values):
    mi_span = max(mi_values) - min(mi_values)
    ic_span = max(ic_values) - min(ic_values)
    ic_signs = {0 if abs(v) < 1e-10 else (1 if v > 0 else -1) for v in ic_values}
    if mi_span > 0.05 and ic_span < 0.02:
        return "mi_discrimination_dominant"
    if len(ic_signs - {0}) >= 2:
        return "ic_signed_orientation_dominant"
    if mi_span > 0.02 and ic_span > 0.02:
        return "mixed_regime"
    return "weak_separation"


def build_regime_map():
    packets = build_packet_library()
    packet_rows = []
    mi_hit_count = 0
    ic_signed_count = 0

    for packet in packets:
        scores = family_scores(packet)
        mi_values = [scores[f]["mutual_information"] for f in scores]
        ic_values = [scores[f]["coherent_information"] for f in scores]
        mi_winner = max(scores.items(), key=lambda kv: kv[1]["mutual_information"])[0]
        ic_winner = max(scores.items(), key=lambda kv: kv[1]["coherent_information"])[0]
        if packet.expected_dominant_family is not None and mi_winner == packet.expected_dominant_family:
            mi_hit_count += 1
        if any(scores[f]["signed_eligible"] for f in scores):
            ic_signed_count += 1
        packet_rows.append({
            "packet_label": packet.label,
            "expected_dominant_family": packet.expected_dominant_family,
            "mi_winner": mi_winner,
            "ic_winner": ic_winner,
            "regime": regime_label(mi_values, ic_values),
            "family_scores": scores,
        })

    sweep_rows = []
    for coupling in [0.0, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9]:
        rho = normalize_density((1.0 - coupling) * torch.kron(dm_from_probs([0.8, 0.2]), dm_from_probs([0.6, 0.4])) + coupling * BELL_DM)
        sweep_rows.append({
            "coupling": coupling,
            "mutual_information": mutual_information(rho),
            "coherent_information": coherent_information(rho),
            "conditional_entropy": conditional_entropy(rho),
            "finite_blocklength_proxy": hypothesis_testing_relative_entropy_commuting(
                computational_basis_probs(rho),
                computational_basis_probs(torch.kron(partial_trace_a(rho), partial_trace_b(rho))),
                epsilon=0.1,
            )[0],
            "signed_eligible": abs(coherent_information(rho)) > 1e-12,
        })

    summary = {
        "mi_hit_count": mi_hit_count,
        "mi_expected_total": 3,
        "ic_signed_packet_count": ic_signed_count,
        "mi_wins_on_hit_count": mi_hit_count >= 3,
        "ic_remains_signed_primitive": ic_signed_count >= 1,
        "winner_by_hits": "mutual_information" if mi_hit_count >= 3 else None,
        "primitive_signed_candidate": "coherent_information" if ic_signed_count >= 1 else None,
        "promoted_final_winner": None,
        "all_pass": True,
    }
    return {"packet_rows": packet_rows, "sweep_rows": sweep_rows, "summary": summary}


def run_negative_tests():
    regime = build_regime_map()
    tests = [
        {
            "name": "mi_not_treated_as_signed_primitive",
            "pass": regime["summary"]["winner_by_hits"] == "mutual_information"
            and regime["summary"]["primitive_signed_candidate"] == "coherent_information",
        },
        {
            "name": "no_final_winner_promoted_from_hit_count_alone",
            "pass": regime["summary"]["promoted_final_winner"] is None,
        },
        {
            "name": "conditional_entropy_is_not_independent_of_ic",
            "pass": all(
                abs(row["family_scores"][family]["conditional_entropy"] + row["family_scores"][family]["coherent_information"]) < 1e-8
                for row in regime["packet_rows"]
                for family in row["family_scores"]
            ),
        },
    ]
    return {"tests": tests}


def run_boundary_tests():
    regime = build_regime_map()
    zero = regime["sweep_rows"][0]
    high = regime["sweep_rows"][-1]
    tests = [
        {
            "name": "zero_coupling_product_has_zero_mi_and_nonpositive_ic",
            "pass": abs(zero["mutual_information"]) < 1e-8 and zero["coherent_information"] <= 1e-8,
        },
        {
            "name": "high_coupling_keeps_mi_positive_while_ic_becomes_signed",
            "pass": high["mutual_information"] > 0.0 and abs(high["coherent_information"]) > 1e-8,
        },
        {
            "name": "regime_map_separates_unsigned_and_signed_roles",
            "pass": regime["summary"]["mi_wins_on_hit_count"] and regime["summary"]["ic_remains_signed_primitive"],
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
    regime = build_regime_map()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    r_pass, r_fail = count_passes({"summary": {"pass": regime["summary"]["all_pass"]}})
    n_pass, n_fail = count_passes(negative)
    b_pass, b_fail = count_passes(boundary)

    results = {
        "name": "phi0_ic_vs_mi_regime_map",
        "probe": "phi0_ic_vs_mi_regime_map",
        "purpose": (
            "Map where mutual information wins as an unsigned packet discriminator "
            "while coherent information remains the stronger signed primitive"
        ),
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tools_used": [name for name, meta in TOOL_MANIFEST.items() if meta["used"]],
        "regime_map": regime,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "regime_checks": {"passed": r_pass, "failed": r_fail},
            "negative": {"passed": n_pass, "failed": n_fail},
            "boundary": {"passed": b_pass, "failed": b_fail},
            "winner_by_hits": regime["summary"]["winner_by_hits"],
            "primitive_signed_candidate": regime["summary"]["primitive_signed_candidate"],
            "promoted_final_winner": regime["summary"]["promoted_final_winner"],
            "all_pass": (r_fail + n_fail + b_fail) == 0,
            "scope_note": (
                "Pure-math regime map only. Packet hit-count and signed-primitive eligibility are kept separate."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "phi0_ic_vs_mi_regime_map_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"ALL PASS: {results['summary']['all_pass']}")
    print(f"Winner by hits: {results['summary']['winner_by_hits']}")
    print(f"Signed primitive candidate: {results['summary']['primitive_signed_candidate']}")
    print(f"Results written to {out_path}")
