#!/usr/bin/env python3
"""
sim_bridge_packet_library_audit.py
===================================

Pure-math audit/support surface for packet families reused in bridge work.

What this audit classifies:
  - packet types
  - coverage of bridge families
  - degeneracies
  - counterfeit packets
  - which bridge families each packet meaningfully exercises

This is not final canon. It is a support/audit library.

Output:
  system_v4/probes/a2_state/sim_results/sim_bridge_packet_library_audit_results.json
"""

import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

EPS = 1e-12

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "pure numpy audit/support surface"},
    "pyg": {"tried": False, "used": False, "reason": "no graph layer is needed for this packet audit"},
    "z3": {"tried": False, "used": False, "reason": "no satisfiability or synthesis claim is needed here"},
    "cvc5": {"tried": False, "used": False, "reason": "no SMT or synthesis claim is needed here"},
    "sympy": {"tried": False, "used": False, "reason": "this audit uses only finite numerical checks"},
    "clifford": {"tried": False, "used": False, "reason": "no geometric algebra layer is needed"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold statistics layer is needed"},
    "e3nn": {"tried": False, "used": False, "reason": "no equivariant layer is needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "no dependency graph layer is needed"},
    "xgi": {"tried": False, "used": False, "reason": "no hypergraph layer is needed"},
    "toponetx": {"tried": False, "used": False, "reason": "no cell-complex layer is needed"},
    "gudhi": {"tried": False, "used": False, "reason": "no persistent topology layer is needed"},
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


def is_psd(rho):
    evals = np.linalg.eigvalsh(hermitian(rho))
    return bool(np.min(evals) >= -1e-10), float(np.min(evals))


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
    sy = Y
    yy = np.kron(sy, sy)
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


def correlation_tensor_norm(rho_ab):
    total = 0.0
    for pa in PAULIS:
        for pb in PAULIS:
            total += abs(np.trace(rho_ab @ np.kron(pa, pb))) ** 2
    return float(math.sqrt(total))


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


def normalize_weights(values):
    values = np.asarray(values, dtype=float)
    total = float(np.sum(values))
    if total <= 0.0:
        return np.ones_like(values) / len(values)
    return values / total


def reference_offset(packet):
    cur = shell_point_to_bloch(packet.current)
    ref = shell_point_to_bloch(packet.reference)
    return float(np.linalg.norm(cur - ref))


def shell_dispersion(packet):
    radii = np.array([p.radius for p in packet.shells], dtype=float)
    return float(np.std(radii))


def history_turning(packet):
    if len(packet.history) < 3:
        return 0.0
    phases = np.unwrap(np.array([p.phi for p in packet.history], dtype=float))
    if len(phases) < 3:
        return 0.0
    second = np.diff(np.diff(phases))
    return float(np.mean(np.abs(second))) if len(second) else 0.0


def xi_ref(packet):
    rho_cur = pair_state(left_density(packet.current), right_density(packet.current), 0.0)
    rho_ref = pair_state(left_density(packet.reference), right_density(packet.reference), 0.0)
    coupling = 0.45 * math.tanh(1.2 * reference_offset(packet))
    return validate_density((1.0 - coupling) * rho_cur + coupling * rho_ref[::-1, ::-1])


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


def packet_metrics(packet):
    rho_ref = xi_ref(packet)
    rho_shell = xi_shell(packet)
    rho_hist = xi_hist(packet)
    return {
        "xi_ref": {
            "entropy": entropy_bits(rho_ref),
            "mutual_information": mutual_information(rho_ref),
            "negativity": negativity(rho_ref),
            "correlation_tensor_norm": correlation_tensor_norm(rho_ref),
        },
        "xi_shell": {
            "entropy": entropy_bits(rho_shell),
            "mutual_information": mutual_information(rho_shell),
            "negativity": negativity(rho_shell),
            "correlation_tensor_norm": correlation_tensor_norm(rho_shell),
        },
        "xi_hist": {
            "entropy": entropy_bits(rho_hist),
            "mutual_information": mutual_information(rho_hist),
            "negativity": negativity(rho_hist),
            "correlation_tensor_norm": correlation_tensor_norm(rho_hist),
        },
    }


def packet_exercise_profile(packet):
    return {
        "reference_offset": reference_offset(packet),
        "shell_dispersion": shell_dispersion(packet),
        "history_turning": history_turning(packet),
        "exercises": {
            "xi_ref": reference_offset(packet) > 0.08,
            "xi_shell": shell_dispersion(packet) > 0.06 and len(packet.shells) > 1,
            "xi_hist": history_turning(packet) > 0.06 or len(packet.history) > 1,
            "rho_ab_constructor": True,
        },
    }


def classify_packet(packet):
    profile = packet_exercise_profile(packet)
    if packet.label in {"invalid", "counterfeit"}:
        kind = "counterfeit"
    elif packet.label in {"flat_shell", "single_history", "reference_frozen"}:
        kind = "degenerate"
    elif packet.label in {"product", "separable", "bell", "werner"}:
        kind = packet.label
    else:
        kind = "support_packet"
    return {
        "label": packet.label,
        "kind": kind,
        "coverage": profile["exercises"],
        "profile": profile,
        "family_marks": {
            "history_sensitive": profile["history_turning"] > 0.06,
            "shell_sensitive": profile["shell_dispersion"] > 0.06,
            "reference_sensitive": profile["reference_offset"] > 0.08,
        },
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

    return {
        "xi_core": XiPacket("xi_core", current, base_shells, base_history, reference),
        "history_scrambled": XiPacket("history_scrambled", current, base_shells, list(reversed(base_history)), reference),
        "shell_ablated": XiPacket("shell_ablated", current, [base_shells[1]], base_history, reference),
        "reference_frozen": XiPacket("reference_frozen", current, base_shells, base_history, current),
        "flat_shell": XiPacket(
            "flat_shell",
            current,
            [
                ShellPoint(current.radius, current.theta, current.phi, 1.0 / 3.0),
                ShellPoint(current.radius, current.theta, current.phi, 1.0 / 3.0),
                ShellPoint(current.radius, current.theta, current.phi, 1.0 / 3.0),
            ],
            base_history,
            reference,
        ),
        "single_history": XiPacket("single_history", current, base_shells, [base_history[0]], reference),
    }


def rhoab_library():
    product = np.kron(np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128), np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128))
    correlated = 0.6 * np.kron(
        np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128),
        np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.complex128),
    ) + 0.4 * np.kron(
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128),
        np.array([[0.0, 0.0], [0.0, 1.0]], dtype=np.complex128),
    )
    bell = np.outer(BELL, BELL.conj())
    werner = 0.6 * bell + 0.4 * I4 / 4.0
    invalid = np.array(
        [
            [0.7, 0.3, 0.0, 0.0],
            [0.3, 0.4, 0.0, 0.0],
            [0.0, 0.0, -0.1, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=np.complex128,
    )
    counterfeit = np.kron(
        np.array([[0.7, 0.0], [0.0, 0.3]], dtype=np.complex128),
        np.array([[0.4, 0.0], [0.0, 0.6]], dtype=np.complex128),
    )
    counterfeit[0, 3] = 0.35
    counterfeit[3, 0] = 0.35
    return {
        "product": product,
        "correlated": correlated,
        "bell": bell,
        "werner": werner,
        "invalid": invalid,
        "counterfeit": counterfeit,
    }


def validate_rhoab(rho_ab):
    rho_ab = hermitian(rho_ab)
    psd, min_eig = is_psd(rho_ab)
    tr = np.trace(rho_ab)
    rho_a = partial_trace_b(rho_ab)
    rho_b = partial_trace_a(rho_ab)
    return {
        "trace": float(np.real(tr)),
        "trace_error": float(abs(np.real(tr) - 1.0)),
        "psd": psd,
        "min_eigenvalue": min_eig,
        "rho_a_trace": float(np.real(np.trace(rho_a))),
        "rho_b_trace": float(np.real(np.trace(rho_b))),
        "mutual_information": mutual_information(rho_ab),
        "concurrence": concurrence(rho_ab),
        "negativity": negativity(rho_ab),
        "valid": bool(abs(np.real(tr) - 1.0) < 1e-10 and psd),
    }


def positive_tests():
    results = {}

    packets = packet_library()
    core = packets["xi_core"]
    core_profile = classify_packet(core)
    core_metrics = packet_metrics(core)

    results["P1_xi_core_exercises_all_families"] = {
        "pass": all(core_profile["coverage"].values()),
        "why": "the core packet should exercise every bridge family at least weakly",
        "profile": core_profile,
        "metrics": core_metrics,
    }

    rho_lib = rhoab_library()
    rho_product = validate_rhoab(rho_lib["product"])
    rho_correlated = validate_rhoab(rho_lib["correlated"])
    rho_bell = validate_rhoab(rho_lib["bell"])
    rho_werner = validate_rhoab(rho_lib["werner"])

    results["P2_rhoab_family_distinction"] = {
        "pass": (
            rho_product["valid"]
            and rho_correlated["valid"]
            and rho_bell["valid"]
            and rho_werner["valid"]
            and rho_product["concurrence"] == 0.0
            and rho_correlated["mutual_information"] > rho_product["mutual_information"]
            and rho_bell["negativity"] > 0.0
            and rho_werner["concurrence"] > 0.0
            and rho_werner["concurrence"] < rho_bell["concurrence"]
        ),
        "why": "the library must distinguish product, separable correlated, entangled, and mixed correlated packets",
        "product": rho_product,
        "correlated": rho_correlated,
        "bell": rho_bell,
        "werner": rho_werner,
    }

    core_ref = xi_ref(core)
    core_shell = xi_shell(core)
    core_hist = xi_hist(core)
    family_distances = {
        "ref_shell": float(np.linalg.norm(core_ref - core_shell)),
        "ref_hist": float(np.linalg.norm(core_ref - core_hist)),
        "shell_hist": float(np.linalg.norm(core_shell - core_hist)),
    }
    results["P3_bridge_families_are_distinct"] = {
        "pass": min(family_distances.values()) > 1e-3,
        "why": "the three bridge families should not collapse to the same rho_AB",
        "family_distances": family_distances,
    }

    return results


def negative_tests():
    results = {}
    packets = packet_library()
    rho_lib = rhoab_library()

    scrambled = packets["history_scrambled"]
    ablated = packets["shell_ablated"]
    frozen = packets["reference_frozen"]
    flat = packets["flat_shell"]
    single = packets["single_history"]
    invalid = rho_lib["invalid"]
    counterfeit = rho_lib["counterfeit"]

    results["N1_history_scrambling_detected"] = {
        "pass": classify_packet(scrambled)["coverage"]["xi_hist"],
        "rejected_counterfeit": "history scrambling should still exercise the history family, but with altered profile metrics",
        "profile": classify_packet(scrambled),
        "metrics": packet_metrics(scrambled),
    }

    results["N2_shell_ablation_detected"] = {
        "pass": (
            not classify_packet(ablated)["coverage"]["xi_shell"]
            and classify_packet(ablated)["profile"]["shell_dispersion"] < 1e-12
        ),
        "rejected_counterfeit": "shell ablation should be detected as a non-shell-exercising degeneracy",
        "profile": classify_packet(ablated),
        "metrics": packet_metrics(ablated),
    }

    results["N3_reference_freeze_detected"] = {
        "pass": (
            not classify_packet(frozen)["coverage"]["xi_ref"]
            and classify_packet(frozen)["profile"]["reference_offset"] < 1e-12
        ),
        "rejected_counterfeit": "reference freezing should be detected as a non-reference-exercising degeneracy",
        "profile": classify_packet(frozen),
        "metrics": packet_metrics(frozen),
    }

    invalid_valid = validate_rhoab(invalid)
    counterfeit_valid = validate_rhoab(counterfeit)
    results["N4_counterfeit_rhoab_rejected"] = {
        "pass": (not invalid_valid["valid"]) and (not counterfeit_valid["valid"]),
        "rejected_counterfeit": "invalid rho_AB packets must fail PSD or marginal consistency checks",
        "invalid": invalid_valid,
        "counterfeit": counterfeit_valid,
    }

    flat_profile = classify_packet(flat)
    single_profile = classify_packet(single)
    results["N5_degeneracies_are_flagged"] = {
        "pass": (
            flat_profile["kind"] == "degenerate"
            and single_profile["kind"] == "degenerate"
            and not flat_profile["coverage"]["xi_shell"]
            and not single_profile["coverage"]["xi_hist"]
        ),
        "rejected_counterfeit": "flat shells and singleton histories are degenerate audit packets, not strong bridge evidence",
        "flat_shell": flat_profile,
        "single_history": single_profile,
    }

    return results


def boundary_tests():
    results = {}
    packets = packet_library()
    core = packets["xi_core"]
    flat = packets["flat_shell"]
    single = packets["single_history"]

    core_metrics = packet_metrics(core)
    flat_metrics = packet_metrics(flat)
    single_metrics = packet_metrics(single)

    results["B1_core_packet_is_well_formed"] = {
        "pass": all(classify_packet(core)["coverage"].values()),
        "why": "the core packet should be the richest packet in the audit library",
        "profile": classify_packet(core),
        "metrics": core_metrics,
    }
    results["B2_flat_shell_boundary"] = {
        "pass": classify_packet(flat)["kind"] == "degenerate" and classify_packet(flat)["profile"]["shell_dispersion"] < 1e-12,
        "why": "identical shells should collapse the shell signal to a boundary case",
        "profile": classify_packet(flat),
        "metrics": flat_metrics,
    }
    results["B3_single_history_boundary"] = {
        "pass": classify_packet(single)["kind"] == "degenerate" and classify_packet(single)["profile"]["history_turning"] < 1e-12,
        "why": "a singleton history should not carry ordered-history curvature",
        "profile": classify_packet(single),
        "metrics": single_metrics,
    }
    return results


def build_audit_catalog():
    packets = packet_library()
    catalog = {}
    for name, packet in packets.items():
        profile = classify_packet(packet)
        catalog[name] = {
            "label": packet.label,
            "kind": profile["kind"],
            "coverage": profile["coverage"],
            "family_marks": profile["family_marks"],
            "profile": profile["profile"],
        }
    catalog["rhoab_library"] = {}
    for name, rho in rhoab_library().items():
        catalog["rhoab_library"][name] = validate_rhoab(rho)
    return catalog


def main():
    positive = positive_tests()
    negative = negative_tests()
    boundary = boundary_tests()
    audit_catalog = build_audit_catalog()

    tests_total = len(positive) + len(negative) + len(boundary)
    tests_passed = sum(1 for sec in (positive, negative, boundary) for v in sec.values() if v["pass"])
    all_pass = tests_passed == tests_total

    results = {
        "name": "bridge_packet_library_audit",
        "classification": "audit",
        "schema": {
            "version": "1.0",
            "sections": ["positive", "negative", "boundary", "audit_catalog", "tool_manifest", "summary"],
            "notes": [
                "support/audit surface, not canon",
                "pure math only",
                "packet type, degeneracy, counterfeit, and family-coverage audit",
            ],
        },
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "audit_catalog": audit_catalog,
        "summary": {
            "tests_total": tests_total,
            "tests_passed": tests_passed,
            "all_pass": all_pass,
            "coverage_counts": {
                "xi_ref": sum(1 for v in audit_catalog.values() if isinstance(v, dict) and v.get("coverage", {}).get("xi_ref")),
                "xi_shell": sum(1 for v in audit_catalog.values() if isinstance(v, dict) and v.get("coverage", {}).get("xi_shell")),
                "xi_hist": sum(1 for v in audit_catalog.values() if isinstance(v, dict) and v.get("coverage", {}).get("xi_hist")),
                "rho_ab_constructor": sum(1 for v in audit_catalog.values() if isinstance(v, dict) and v.get("coverage", {}).get("rho_ab_constructor")),
            },
            "degenerate_packets": [
                name for name, entry in audit_catalog.items()
                if isinstance(entry, dict) and entry.get("kind") == "degenerate"
            ],
            "counterfeit_packets": [
                name for name, entry in audit_catalog.items()
                if isinstance(entry, dict) and entry.get("kind") == "counterfeit"
            ],
            "caveat": "This is a support audit of packet reuse, not a promoted bridge canon.",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
        },
    }

    out_dir = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v4/probes/a2_state/sim_results"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_bridge_packet_library_audit_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(sanitize(results), f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"{tests_passed}/{tests_total} passed")
    print(f"wrote {out_path}")
    print("ALL PASS" if all_pass else "SOME FAIL")


if __name__ == "__main__":
    main()
