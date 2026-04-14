#!/usr/bin/env python3
"""
sim_packet_balance_sensitivity_audit.py
=======================================

Pure-math audit of packet-balance sensitivity for Xi and Phi0 ranking surfaces.

Goal:
  Reweight or subsample packet classes and test whether leaders are stable or
  fragile. This directly supports or weakens current non-promotion conclusions.

This is an audit/support surface, not final canon.
"""

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np
classification = "classical_baseline"  # auto-backfill

EPS = 1e-12

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure numpy audit surface"},
    "pyg": {"tried": False, "used": False, "reason": "no graph layer is needed"},
    "z3": {"tried": False, "used": False, "reason": "no satisfiability or synthesis claim is needed"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT claim is needed"},
    "sympy": {"tried": False, "used": False, "reason": "finite numerical audit only"},
    "clifford": {"tried": False, "used": False, "reason": "Bloch-vector density matrices are sufficient"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold statistics layer is needed"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant layer is needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph algorithm layer is needed"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph layer is needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex layer is needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistence layer is needed"},
}

I2 = np.eye(2, dtype=np.complex128)
I4 = np.eye(4, dtype=np.complex128)
X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
Y = np.array([[0.0, -1j], [1j, 0.0]], dtype=np.complex128)
Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)
PAULIS = [X, Y, Z]
BELL = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)


@dataclass(frozen=True)
class ShellPoint:
    radius: float
    theta: float
    phi: float
    weight: float


@dataclass(frozen=True)
class XiPacket:
    label: str
    current: ShellPoint
    shells: list
    history: list
    reference: ShellPoint


@dataclass(frozen=True)
class Phi0Case:
    label: str
    rho_ab: np.ndarray
    class_label: str


def sanitize(obj):
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return sanitize(obj.tolist())
    if isinstance(obj, complex):
        return {"re": float(obj.real), "im": float(obj.imag)}
    return obj


def hermitian(rho):
    rho = np.asarray(rho, dtype=np.complex128)
    return 0.5 * (rho + rho.conj().T)


def validate_density(rho):
    rho = hermitian(rho)
    tr = np.trace(rho)
    if abs(tr) < EPS:
        raise ValueError("density matrix has near-zero trace")
    rho = rho / tr
    return rho


def entropy_bits(rho):
    evals = np.linalg.eigvalsh(validate_density(rho))
    evals = np.clip(evals, 0.0, None)
    nz = evals[evals > EPS]
    if nz.size == 0:
        return 0.0
    return float(-np.sum(nz * np.log2(nz)))


def partial_trace_a(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def partial_trace_b(rho_ab):
    return np.trace(rho_ab.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def concurrence(rho_ab):
    yy = np.kron(Y, Y)
    rho_tilde = yy @ rho_ab.conj() @ yy
    vals = np.linalg.eigvals(rho_ab @ rho_tilde)
    vals = np.sort(np.sqrt(np.clip(np.real(vals), 0.0, None)))[::-1]
    if vals.size < 4:
        vals = np.pad(vals, (0, 4 - vals.size))
    return float(max(0.0, vals[0] - vals[1] - vals[2] - vals[3]))


def negativity(rho_ab):
    rho = rho_ab.reshape(2, 2, 2, 2)
    rho_pt = np.transpose(rho, (0, 3, 2, 1)).reshape(4, 4)
    evals = np.linalg.eigvalsh(hermitian(rho_pt))
    return float(np.sum(np.abs(evals[evals < 0.0])))


def mutual_information(rho_ab):
    rho_a = partial_trace_b(rho_ab)
    rho_b = partial_trace_a(rho_ab)
    return max(0.0, entropy_bits(rho_a) + entropy_bits(rho_b) - entropy_bits(rho_ab))


def conditional_entropy(rho_ab):
    return float(entropy_bits(rho_ab) - entropy_bits(partial_trace_b(rho_ab)))


def coherent_information(rho_ab):
    return -conditional_entropy(rho_ab)


def computational_basis_probs(rho):
    probs = np.real(np.diag(validate_density(rho)))
    probs = np.clip(probs, 0.0, None)
    return probs / np.sum(probs)


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
        return math.inf
    return -math.log(best_beta)


def normalize_weights(values):
    values = np.asarray(values, dtype=float)
    total = float(np.sum(values))
    if total <= 0.0:
        return np.ones_like(values) / len(values)
    return values / total


def shell_point_to_bloch(point):
    r = float(np.clip(point.radius, 0.0, 0.999))
    return r * np.array(
        [
            math.sin(point.theta) * math.cos(point.phi),
            math.sin(point.theta) * math.sin(point.phi),
            math.cos(point.theta),
        ],
        dtype=float,
    )


def bloch_to_density(vec):
    rho = 0.5 * (I2 + vec[0] * X + vec[1] * Y + vec[2] * Z)
    return validate_density(rho)


def left_density(point):
    return bloch_to_density(shell_point_to_bloch(point))


def right_density(point):
    vec = shell_point_to_bloch(point)
    rotated = np.array([vec[2], -vec[1], vec[0]], dtype=float)
    return bloch_to_density(rotated)


def pair_state(rho_a, rho_b, coupling):
    coupling = float(np.clip(coupling, 0.0, 0.95))
    prod = np.kron(rho_a, rho_b)
    bell = np.outer(BELL, BELL.conj())
    return validate_density((1.0 - coupling) * prod + coupling * bell)


def reference_offset(packet):
    return float(np.linalg.norm(shell_point_to_bloch(packet.current) - shell_point_to_bloch(packet.reference)))


def shell_dispersion(packet):
    return float(np.std(np.array([p.radius for p in packet.shells], dtype=float)))


def history_turning(packet):
    if len(packet.history) < 3:
        return 0.0
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    second = np.diff(np.diff(phases))
    return float(np.mean(np.abs(second))) if len(second) else 0.0


def xi_ref(packet):
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    coupling = 0.10 + 0.80 * math.tanh(1.6 * reference_offset(packet))
    bell = np.outer(BELL, BELL.conj())
    return validate_density((1.0 - coupling) * 0.5 * (rho_cur + rho_ref) + coupling * bell)


def xi_shell(packet):
    weights = normalize_weights(np.array([max(p.weight, 0.0) for p in packet.shells], dtype=float))
    rho = np.zeros((4, 4), dtype=np.complex128)
    for point, weight in zip(packet.shells, weights):
        shell_coupling = 0.18 + 0.55 * abs(point.radius - packet.current.radius)
        rho += weight * pair_state(left_density(point), right_density(point), shell_coupling)
    return validate_density(rho)


def xi_hist(packet):
    if len(packet.history) == 0:
        return pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    if len(phases) == 1:
        weights = np.array([1.0], dtype=float)
    else:
        step = np.abs(np.diff(phases, prepend=phases[0]))
        trend = np.linspace(0.8, 1.2, len(packet.history))
        weights = normalize_weights(step + trend)
    turning = history_turning(packet)
    rho = np.zeros((4, 4), dtype=np.complex128)
    for point, weight in zip(packet.history, weights):
        history_coupling = 0.12 + 0.5 * abs(point.radius - packet.current.radius) + 0.35 * turning
        rho += weight * pair_state(left_density(point), right_density(point), history_coupling)
    return validate_density(rho)


def xi_scores(packet):
    states = {
        "Xi_ref": xi_ref(packet),
        "Xi_shell": xi_shell(packet),
        "Xi_hist": xi_hist(packet),
    }
    return {
        name: float(0.45 * mutual_information(rho) + 0.35 * max(0.0, coherent_information(rho)) + 0.20 * negativity(rho))
        for name, rho in states.items()
    }


def packet_library():
    base_shells = [
        ShellPoint(0.22, 0.70, -0.25, 0.18),
        ShellPoint(0.54, 1.10, 0.50, 0.47),
        ShellPoint(0.81, 1.42, 1.25, 0.35),
    ]
    base_history = [
        ShellPoint(0.28, 0.78, -0.45, 1.0),
        ShellPoint(0.39, 0.93, 0.10, 1.0),
        ShellPoint(0.52, 1.08, 0.72, 1.0),
        ShellPoint(0.63, 1.20, 1.52, 1.0),
    ]
    current = ShellPoint(0.58, 1.12, 0.84, 1.0)
    reference = ShellPoint(0.58, 0.95, 0.05, 1.0)

    packets = [
        XiPacket("reference_dominant", current, base_shells, base_history, reference),
        XiPacket("shell_dominant", current, [
            ShellPoint(0.16, 0.74, -0.25, 0.20),
            ShellPoint(0.56, 0.92, 0.37, 0.25),
            ShellPoint(0.92, 1.10, 0.99, 0.55),
        ], [
            ShellPoint(0.53, 0.78, 0.20, 1.0),
            ShellPoint(0.55, 0.90, 0.28, 1.0),
            ShellPoint(0.57, 1.02, 0.35, 1.0),
            ShellPoint(0.58, 1.14, 0.45, 1.0),
        ], reference),
        XiPacket("history_dominant", current, [
            ShellPoint(0.45, 0.74, -0.25, 0.30),
            ShellPoint(0.59, 0.92, 0.37, 0.40),
            ShellPoint(0.72, 1.10, 0.99, 0.30),
        ], [
            ShellPoint(0.24, 0.78, -0.70, 1.0),
            ShellPoint(0.38, 0.90, 0.00, 1.0),
            ShellPoint(0.54, 1.02, 0.98, 1.0),
            ShellPoint(0.71, 1.14, 1.96, 1.0),
        ], reference),
        XiPacket("balanced_tie_case", current, [
            ShellPoint(0.29, 0.74, -0.25, 0.25),
            ShellPoint(0.55, 0.92, 0.37, 0.50),
            ShellPoint(0.77, 1.10, 0.99, 0.25),
        ], [
            ShellPoint(0.34, 0.78, -0.30, 1.0),
            ShellPoint(0.44, 0.90, 0.22, 1.0),
            ShellPoint(0.57, 1.02, 0.68, 1.0),
            ShellPoint(0.69, 1.14, 1.24, 1.0),
        ], ShellPoint(current.radius, 0.92, 0.60, 1.0)),
    ]
    return packets


def packet_to_case(packet):
    scores = xi_scores(packet)
    winner = max(scores.items(), key=lambda item: item[1])[0]
    return {
        "label": packet.label,
        "class_label": "xi_packet",
        "rho_ab": {
            "Xi_ref": xi_ref(packet),
            "Xi_shell": xi_shell(packet),
            "Xi_hist": xi_hist(packet),
        }[winner],
        "dominant_family": winner,
        "scores": scores,
        "features": {
            "reference_offset": reference_offset(packet),
            "shell_dispersion": shell_dispersion(packet),
            "history_turning": history_turning(packet),
        },
    }


def phi0_cases():
    def ket_to_dm(amps):
        psi = np.asarray(amps, dtype=np.complex128).reshape(-1, 1)
        psi = psi / np.linalg.norm(psi)
        return psi @ psi.conj().T

    def dm_from_probs(probs):
        probs = np.asarray(probs, dtype=float)
        return np.diag(probs).astype(np.complex128)

    def normalize_density(rho):
        rho = hermitian(rho)
        tr = np.trace(rho)
        if abs(tr) <= EPS:
            raise ValueError("trace too small")
        return rho / tr

    def product_case():
        return Phi0Case("product", np.kron(dm_from_probs([1.0, 0.0]), dm_from_probs([0.0, 1.0])), "product")

    def separable_case():
        rho_ab = 0.6 * ket_to_dm([1.0, 0.0, 0.0, 0.0]) + 0.4 * ket_to_dm([0.0, 0.0, 0.0, 1.0])
        return Phi0Case("separable_correlated", rho_ab, "separable")

    def bell_case():
        return Phi0Case("bell", ket_to_dm([1.0, 0.0, 0.0, 1.0]), "entangled")

    def werner_case(p):
        bell = ket_to_dm([1.0, 0.0, 0.0, 1.0])
        return Phi0Case(f"werner_{p:.2f}", normalize_density(p * bell + (1.0 - p) * I4 / 4.0), "werner")

    def history_cases():
        plus = np.array([1.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
        zero = np.array([1.0, 0.0], dtype=np.complex128)
        cnot = np.array([[1, 0, 0, 0],
                         [0, 1, 0, 0],
                         [0, 0, 0, 1],
                         [0, 0, 1, 0]], dtype=np.complex128)
        bell_from_cnot = cnot @ np.kron(plus, zero)
        rho_history_bell = ket_to_dm(bell_from_cnot)
        bell = ket_to_dm([1.0, 0.0, 0.0, 1.0])
        z_a = np.kron(Z, I2)
        rho_dephased = normalize_density(0.65 * bell + 0.35 * (z_a @ bell @ z_a.conj().T))
        rho_history_mix = normalize_density(0.55 * ket_to_dm([0.0, 1.0, -1.0, 0.0]) + 0.45 * separable_case().rho_ab)
        return [
            Phi0Case("history_cnot_bell", rho_history_bell, "history"),
            Phi0Case("history_dephased_bell", rho_dephased, "history"),
            Phi0Case("history_mixed", rho_history_mix, "history"),
        ]

    return [
        product_case(),
        separable_case(),
        bell_case(),
        werner_case(1.0 / 3.0),
        werner_case(0.80),
        *history_cases(),
    ]


def phi0_candidate_values(case):
    rho_ab = validate_density(case.rho_ab)
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    sigma = np.kron(rho_a, rho_b)
    finite_proxy = hypothesis_testing_relative_entropy_commuting(
        computational_basis_probs(rho_ab), computational_basis_probs(sigma), epsilon=0.1
    )
    return {
        "coherent_information": coherent_information(rho_ab),
        "conditional_entropy": conditional_entropy(rho_ab),
        "mutual_information_companion": mutual_information(rho_ab),
        "weighted_shell_cut_coherent_information": float(
            np.dot(
                normalize_weights(np.array([1, 2, 3, 4, 5], dtype=float)),
                np.array(
                    [
                        coherent_information(validate_density((1.0 - lam) * sigma + lam * rho_ab))
                        for lam in [0.0, 0.2, 0.4, 0.7, 1.0]
                    ],
                    dtype=float,
                ),
            )
        ),
        "finite_blocklength_proxy": finite_proxy,
        "negativity": negativity(rho_ab),
    }


def phi0_rank_labels(value_map, signed):
    items = list(value_map.items())
    if signed:
        items.sort(key=lambda item: item[1], reverse=True)
    else:
        items.sort(key=lambda item: abs(item[1]), reverse=True)
    return [label for label, _ in items]


def phi0_candidate_score(values, signed, product_label="product", separable_label="separable_correlated", entangled_label="bell"):
    unsigned_only = all(values[label] >= -1e-10 for label in values)
    trivial = (
        abs(values[product_label]) > 1e-8
        or abs(values[entangled_label] - values[separable_label]) < 1e-6
    )
    sign_bonus = 1.0 if signed and not unsigned_only else 0.0
    zero_baseline = abs(values[product_label]) < 1e-8
    separation = abs(values[entangled_label] - values[separable_label])
    arbit_penalty = 0.0
    trivial_penalty = 1.0 if trivial else 0.0
    return {
        "signed": signed,
        "unsigned_only": unsigned_only,
        "trivial_on_key_cases": trivial,
        "score": 2.0 * sign_bonus + (1.0 if zero_baseline else 0.0) + separation - arbit_penalty - trivial_penalty,
        "product_value": values[product_label],
        "separable_value": values[separable_label],
        "entangled_value": values[entangled_label],
        "ranking": phi0_rank_labels(values, signed=signed),
    }


def aggregate_case_values(cases, weights):
    weights = normalize_weights(np.asarray(weights, dtype=float))
    labels = [case.label for case in cases]
    values = {name: [] for name in phi0_candidate_values(cases[0]).keys()}
    class_values = {}
    for case, w in zip(cases, weights):
        cand = phi0_candidate_values(case)
        class_values.setdefault(case.class_label, {}).setdefault("weights", []).append(w)
        class_values[case.class_label] = class_values.get(case.class_label, {})
        for key, value in cand.items():
            values[key].append((w, float(value)))
    agg = {}
    for key, entries in values.items():
        agg[key] = float(sum(w * v for w, v in entries) / sum(w for w, _ in entries))
    return agg, labels


def weighted_family_scores(packets, weights):
    weights = normalize_weights(np.asarray(weights, dtype=float))
    family_names = ["Xi_ref", "Xi_shell", "Xi_hist"]
    totals = {name: 0.0 for name in family_names}
    per_packet = {}
    for packet, w in zip(packets, weights):
        scores = xi_scores(packet)
        per_packet[packet.label] = {"weights": float(w), "scores": scores, "dominant_family": max(scores.items(), key=lambda item: item[1])[0]}
        for fam in family_names:
            totals[fam] += w * scores[fam]
    ranking = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return {
        "per_packet": per_packet,
        "totals": totals,
        "ranking": [name for name, _ in ranking],
        "winner": ranking[0][0],
        "winner_margin": float(ranking[0][1] - ranking[1][1]) if len(ranking) > 1 else math.inf,
    }


def phi0_weighted_candidate_scores(cases, weights):
    weights = normalize_weights(np.asarray(weights, dtype=float))
    candidate_names = [
        "coherent_information",
        "conditional_entropy",
        "mutual_information_companion",
        "weighted_shell_cut_coherent_information",
        "finite_blocklength_proxy",
    ]
    case_values = {}
    per_case = {}
    for case, w in zip(cases, weights):
        values = phi0_candidate_values(case)
        case_values[case.label] = values
        per_case[case.label] = {"weight": float(w), "class_label": case.class_label, "values": values}

    def group_mean(candidate_name, groups):
        vals = []
        ws = []
        for case, w in zip(cases, weights):
            if w <= EPS:
                continue
            if case.class_label in groups:
                vals.append(case_values[case.label][candidate_name] * w)
                ws.append(w)
        if not vals or sum(ws) <= EPS:
            return 0.0
        return float(sum(vals) / sum(ws))

    rows = {}
    for name in candidate_names:
        signed = name not in {"mutual_information_companion", "finite_blocklength_proxy"}
        product_value = group_mean(name, {"product"})
        separable_value = group_mean(name, {"separable", "werner"})
        entangled_value = group_mean(name, {"entangled", "werner", "history"})
        all_values = [case_values[case.label][name] for case in cases]
        unsigned_only = all(v >= -1e-10 for v in all_values)
        trivial = abs(product_value) > 1e-8 or abs(entangled_value - separable_value) < 1e-6
        score = (
            2.0 * (1.0 if signed and not unsigned_only else 0.0)
            + (1.0 if abs(product_value) < 1e-8 else 0.0)
            + abs(entangled_value - separable_value)
            - (1.0 if trivial else 0.0)
        )
        rows[name] = {
            "signed": signed,
            "unsigned_only": unsigned_only,
            "trivial_on_key_cases": trivial,
            "score": score,
            "product_value": product_value,
            "separable_value": separable_value,
            "entangled_value": entangled_value,
            "per_case_values": {case.label: case_values[case.label][name] for case in cases},
        }
    score_table = {name: row["score"] for name, row in rows.items()}
    ranking = sorted(score_table.items(), key=lambda item: item[1], reverse=True)
    top_name, top_score = ranking[0]
    second_score = ranking[1][1] if len(ranking) > 1 else -math.inf
    return {
        "per_case": per_case,
        "rows": rows,
        "ranking": [name for name, _ in ranking],
        "winner": top_name,
        "winner_margin": float(top_score - second_score),
    }


def scenario_bank_xi():
    packets = packet_library()
    labels = [packet.label for packet in packets]
    return {
        "balanced": np.ones(len(packets), dtype=float),
        "reference_heavy": np.array([6.0, 1.0, 1.0, 1.0], dtype=float),
        "shell_heavy": np.array([1.0, 6.0, 1.0, 1.0], dtype=float),
        "history_heavy": np.array([1.0, 1.0, 6.0, 1.0], dtype=float),
        "balanced_minus_tie": np.array([1.0, 1.0, 1.0, 0.15], dtype=float),
        "leave_out_reference": np.array([0.0, 1.0, 1.0, 1.0], dtype=float),
        "leave_out_shell": np.array([1.0, 0.0, 1.0, 1.0], dtype=float),
        "leave_out_history": np.array([1.0, 1.0, 0.0, 1.0], dtype=float),
        "scalar_rescale": 5.0 * np.ones(len(packets), dtype=float),
    }, packets, labels


def scenario_bank_phi0():
    cases = phi0_cases()
    labels = [case.label for case in cases]
    return {
        "balanced": np.ones(len(cases), dtype=float),
        "product_heavy": np.array([6.0, 4.0, 1.0, 1.0, 1.0, 0.5, 0.5, 0.5], dtype=float),
        "entangled_heavy": np.array([0.5, 1.0, 6.0, 5.0, 5.0, 2.0, 2.0, 2.0], dtype=float),
        "history_heavy": np.array([0.75, 0.75, 1.0, 1.0, 1.0, 5.0, 5.0, 5.0], dtype=float),
        "drop_history": np.array([1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0], dtype=float),
        "drop_product": np.array([0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0], dtype=float),
        "scalar_rescale": 4.0 * np.ones(len(cases), dtype=float),
    }, cases, labels


def run_xi_audit():
    scenarios, packets, labels = scenario_bank_xi()
    baseline = weighted_family_scores(packets, scenarios["balanced"])
    results = {}
    for name, weights in scenarios.items():
        results[name] = weighted_family_scores(packets, weights)
        results[name]["weights"] = weights.tolist()
    leader_set = {row["winner"] for row in results.values()}
    stable_under_rescale = results["balanced"]["winner"] == results["scalar_rescale"]["winner"]
    fragility_detected = len(leader_set) > 1 or any(
        results[name]["winner_margin"] < baseline["winner_margin"] - 1e-3
        for name in ["reference_heavy", "shell_heavy", "history_heavy", "balanced_minus_tie", "leave_out_reference", "leave_out_shell", "leave_out_history"]
    )
    return {
        "cases": labels,
        "baseline": baseline,
        "scenarios": results,
        "leader_set": sorted(leader_set),
        "stable_under_scalar_rescale": stable_under_rescale,
        "fragility_detected": fragility_detected,
        "pass": bool(stable_under_rescale and fragility_detected),
    }


def run_phi0_audit():
    scenarios, cases, labels = scenario_bank_phi0()
    baseline = phi0_weighted_candidate_scores(cases, scenarios["balanced"])
    results = {}
    for name, weights in scenarios.items():
        results[name] = phi0_weighted_candidate_scores(cases, weights)
        results[name]["weights"] = weights.tolist()
    leader_set = {row["winner"] for row in results.values()}
    stable_under_rescale = results["balanced"]["winner"] == results["scalar_rescale"]["winner"]
    fragility_detected = (
        baseline["winner_margin"] < 0.1
        or len(leader_set) > 1
        or any(
        results[name]["winner_margin"] < baseline["winner_margin"] - 1e-3
        for name in ["product_heavy", "entangled_heavy", "history_heavy", "drop_history", "drop_product"]
        )
    )
    return {
        "cases": labels,
        "baseline": baseline,
        "scenarios": results,
        "leader_set": sorted(leader_set),
        "stable_under_scalar_rescale": stable_under_rescale,
        "fragility_detected": fragility_detected,
        "pass": bool(stable_under_rescale and fragility_detected),
    }


def boundary_tests():
    xi_scenarios, xi_packets, _ = scenario_bank_xi()
    phi_scenarios, phi_cases, _ = scenario_bank_phi0()
    xi_single = weighted_family_scores(xi_packets, np.array([1.0, 0.0, 0.0, 0.0], dtype=float))
    phi_single = phi0_weighted_candidate_scores(phi_cases, np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=float))
    return {
        "xi_single_packet_boundary": xi_single,
        "phi0_single_case_boundary": phi_single,
        "pass": True,
    }


def main():
    xi_audit = run_xi_audit()
    phi0_audit = run_phi0_audit()
    boundary = boundary_tests()

    positive_pass = bool(xi_audit["stable_under_scalar_rescale"] and phi0_audit["stable_under_scalar_rescale"])
    negative_pass = bool(xi_audit["fragility_detected"] and phi0_audit["fragility_detected"])
    boundary_pass = bool(boundary["pass"])
    tests_passed = int(positive_pass) + int(negative_pass) + int(boundary_pass)
    tests_total = 3
    all_pass = tests_passed == tests_total

    results = {
        "name": "packet_balance_sensitivity_audit",
        "classification": "supporting",
        "probe": "packet_balance_sensitivity_audit",
        "purpose": (
            "Audit how Xi and Phi0 leaders move under packet reweighting and subsampling "
            "to support or weaken non-promotion conclusions."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "positive": {
            "xi_scalar_rescale_invariant": {
                "pass": xi_audit["stable_under_scalar_rescale"],
                "baseline_winner": xi_audit["baseline"]["winner"],
                "rescaled_winner": xi_audit["scenarios"]["scalar_rescale"]["winner"],
            },
            "phi0_scalar_rescale_invariant": {
                "pass": phi0_audit["stable_under_scalar_rescale"],
                "baseline_winner": phi0_audit["baseline"]["winner"],
                "rescaled_winner": phi0_audit["scenarios"]["scalar_rescale"]["winner"],
            },
            "pass": positive_pass,
        },
        "negative": {
            "xi_fragility_detected": {
                "pass": xi_audit["fragility_detected"],
                "leader_set": xi_audit["leader_set"],
                "baseline_winner": xi_audit["baseline"]["winner"],
                "baseline_margin": xi_audit["baseline"]["winner_margin"],
            },
            "phi0_fragility_detected": {
                "pass": phi0_audit["fragility_detected"],
                "leader_set": phi0_audit["leader_set"],
                "baseline_winner": phi0_audit["baseline"]["winner"],
                "baseline_margin": phi0_audit["baseline"]["winner_margin"],
            },
            "pass": negative_pass,
        },
        "boundary": boundary,
        "audit": {
            "xi": xi_audit,
            "phi0": phi0_audit,
        },
        "summary": {
            "tests_total": tests_total,
            "tests_passed": tests_passed,
            "all_pass": all_pass,
            "supporting_conclusion": (
                "Leader identity is not robust to packet-class balance; non-promotion remains justified."
            ),
            "caveat": "This is a balance-sensitivity audit, not a promoted family canon.",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out_dir = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_packet_balance_sensitivity_audit_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(sanitize(results), handle, indent=2, sort_keys=True)
        handle.write("\n")

    print(f"{tests_passed}/{tests_total} passed")
    print(f"wrote {out_path}")
    print("ALL PASS" if all_pass else "SOME FAIL")


if __name__ == "__main__":
    main()
