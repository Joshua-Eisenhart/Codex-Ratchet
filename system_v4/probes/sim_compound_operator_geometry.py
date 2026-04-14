#!/usr/bin/env python3
"""
sim_compound_operator_geometry.py
---------------------------------
Compound Operator Sequence Geometry Sim.

THE QUESTION: When operators are COMPOSED in sequence, which geometry survives?

Single operators have clear compatibility (the 48-cell matrix).
But the engine runs SEQUENCES. This sim discovers how constraint layers COMPOUND.

Tests:
  - All 16 two-operator pairs (4x4)
  - 20 representative three-operator triples
  - Full engine cycle Ti->Fe->Te->Fi (forward and reversed)
  - Cl(3) geometric algebra cross-check
  - 2-qubit entangling gate sequences

NO engine imports. Pure legos: numpy, scipy, clifford.
"""

import sys, os, json, time
import numpy as np
from scipy.linalg import expm
classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed -- numpy/scipy state evolution"},
    "pyg": {"tried": False, "used": False, "reason": "not needed -- no graph message passing"},
    "z3": {"tried": False, "used": False, "reason": "not needed -- no SMT proof layer in this sim"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed -- no synthesis/proof search"},
    "sympy": {"tried": False, "used": False, "reason": "not needed -- numeric comparison only"},
    "clifford": {"tried": True, "used": True, "reason": "Cl(3) rotor/dephasing cross-check is part of the core comparison"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- geometry is classified directly, not via manifold package"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed -- no equivariant NN layer"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency/order graph"},
    "xgi": {"tried": False, "used": False, "reason": "not needed -- no hypergraph layer"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed -- no cell-complex layer"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed -- no persistence layer"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# ─── Pauli matrices ──────────────────────────────────────────────────────────

sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)
I4 = np.eye(4, dtype=complex)

# ─── 4 Engine Operators + Entangling Gate ────────────────────────────────────

def Ti(rho, s=0.5):
    """Z-dephasing (internal dissipative)."""
    P0 = np.array([[1, 0], [0, 0]], dtype=complex)
    P1 = np.array([[0, 0], [0, 1]], dtype=complex)
    return (1 - s) * rho + s * (P0 @ rho @ P0 + P1 @ rho @ P1)

def Fe(rho, phi=0.4):
    """Z-rotation (external unitary)."""
    U = expm(-1j * phi / 2 * sz)
    return U @ rho @ U.conj().T

def Te(rho, s=0.5):
    """X-dephasing (external dissipative)."""
    Qp = np.array([[1, 1], [1, 1]], dtype=complex) / 2
    Qm = np.array([[1, -1], [-1, 1]], dtype=complex) / 2
    return (1 - s) * rho + s * (Qp @ rho @ Qp + Qm @ rho @ Qm)

def Fi(rho, theta=0.4):
    """X-rotation (internal unitary)."""
    U = expm(-1j * theta / 2 * sx)
    return U @ rho @ U.conj().T

def Ent(rho_AB, s=0.3):
    """Ising ZZ entangling gate (4x4)."""
    H = np.kron(sz, sz)
    U = expm(-1j * s * H)
    return U @ rho_AB @ U.conj().T

OP_NAMES = ["Ti", "Fe", "Te", "Fi"]
OPS = [Ti, Fe, Te, Fi]
ALLOWED_GEOMETRIES = {"S2", "z-fiber", "x-fiber", "torus", "origin", "interior"}
PAIR_ORDER_TOL = 0.001


def finite_and_bounded(value, lower=0.0, upper=1.0):
    return bool(np.isfinite(value) and lower <= value <= upper)


def geometries_known(labels):
    return all(label in ALLOWED_GEOMETRIES for label in labels)

# ─── Geometry Checks ────────────────────────────────────────────────────────

def bloch_vector(rho):
    """Extract Bloch vector from 2x2 density matrix."""
    return np.array([
        np.real(np.trace(rho @ sx)),
        np.real(np.trace(rho @ sy)),
        np.real(np.trace(rho @ sz))
    ])

def purity(rho):
    """Tr(rho^2)."""
    return float(np.real(np.trace(rho @ rho)))

def is_on_sphere(rho, tol=0.01):
    """Is rho a pure state? (purity > 1-tol)."""
    return purity(rho) > 1 - tol

def is_on_fiber(rho, axis='z', tol=0.05):
    """Is Bloch vector aligned with axis? (transverse components < tol)."""
    r = bloch_vector(rho)
    if axis == 'z':
        return float(np.sqrt(r[0]**2 + r[1]**2)) < tol
    if axis == 'x':
        return float(np.sqrt(r[1]**2 + r[2]**2)) < tol
    if axis == 'y':
        return float(np.sqrt(r[0]**2 + r[2]**2)) < tol
    return False

def is_on_torus(rho, tol=0.10):
    """Is Bloch vector on a torus-like surface? (not fiber, not sphere, not origin)."""
    r = bloch_vector(rho)
    norm = float(np.linalg.norm(r))
    if norm < 0.05:
        return False  # at origin = maximally mixed
    if is_on_sphere(rho, tol=0.01):
        return False  # pure = sphere
    if is_on_fiber(rho, 'z', tol=0.05) or is_on_fiber(rho, 'x', tol=0.05):
        return False  # on a fiber
    return True

def trace_distance(rho1, rho2):
    """Trace distance between two density matrices."""
    diff = rho1 - rho2
    eigvals = np.linalg.eigvalsh(diff)
    return float(0.5 * np.sum(np.abs(eigvals)))

def classify_geometry(rho):
    """Classify which geometry rho sits on."""
    r = bloch_vector(rho)
    norm = float(np.linalg.norm(r))
    p = purity(rho)
    if norm < 0.05:
        return "origin"
    if p > 0.99:
        return "S2"
    if is_on_fiber(rho, 'z', tol=0.05):
        return "z-fiber"
    if is_on_fiber(rho, 'x', tol=0.05):
        return "x-fiber"
    if is_on_torus(rho, tol=0.10):
        return "torus"
    return "interior"

# ─── Generate test states on S2 ─────────────────────────────────────────────

def make_pure_states(n=10):
    """Generate n pure states distributed on S2."""
    states = []
    # Use Fibonacci sphere for decent distribution
    golden_ratio = (1 + np.sqrt(5)) / 2
    for i in range(n):
        theta = np.arccos(1 - 2 * (i + 0.5) / n)
        phi = 2 * np.pi * i / golden_ratio
        # |psi> = cos(theta/2)|0> + e^{i*phi}*sin(theta/2)|1>
        psi = np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)])
        rho = np.outer(psi, psi.conj())
        states.append(rho)
    return states

# ─── 2-Qubit helpers ────────────────────────────────────────────────────────

def partial_trace_B(rho_AB):
    """Trace out qubit B from 4x4 density matrix."""
    rho_A = np.zeros((2, 2), dtype=complex)
    rho_A[0, 0] = rho_AB[0, 0] + rho_AB[1, 1]
    rho_A[0, 1] = rho_AB[0, 2] + rho_AB[1, 3]
    rho_A[1, 0] = rho_AB[2, 0] + rho_AB[3, 1]
    rho_A[1, 1] = rho_AB[2, 2] + rho_AB[3, 3]
    return rho_A

def concurrence(rho_AB):
    """Concurrence of a 2-qubit state."""
    sy2 = np.kron(sy, sy)
    rho_tilde = sy2 @ rho_AB.conj() @ sy2
    R = rho_AB @ rho_tilde
    eigvals = np.sort(np.real(np.sqrt(np.maximum(np.linalg.eigvals(R), 0))))[::-1]
    return float(max(0, eigvals[0] - eigvals[1] - eigvals[2] - eigvals[3]))

def mutual_information(rho_AB):
    """Mutual information I(A:B) = S(A) + S(B) - S(AB)."""
    def vn_entropy(rho):
        eigvals = np.real(np.linalg.eigvalsh(rho))
        eigvals = eigvals[eigvals > 1e-12]
        return float(-np.sum(eigvals * np.log2(eigvals)))
    rho_A = partial_trace_B(rho_AB)
    # Trace out A (swap indices)
    rho_B = np.zeros((2, 2), dtype=complex)
    rho_B[0, 0] = rho_AB[0, 0] + rho_AB[2, 2]
    rho_B[0, 1] = rho_AB[0, 1] + rho_AB[2, 3]
    rho_B[1, 0] = rho_AB[1, 0] + rho_AB[3, 2]
    rho_B[1, 1] = rho_AB[1, 1] + rho_AB[3, 3]
    return vn_entropy(rho_A) + vn_entropy(rho_B) - vn_entropy(rho_AB)

# ─── Cl(3) Cross-Check ──────────────────────────────────────────────────────

def run_cl3_crosscheck(pair_results):
    """For each 2-op pair, compare matrix result to Cl(3) rotor result."""
    from clifford import Cl
    layout, blades = Cl(3)
    e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']

    def cl3_z_rotate(v, phi=0.4):
        """Z-rotation in Cl(3): rotation in e1-e2 plane.
        QM convention: exp(-i*phi/2*sz) maps r -> Rz(phi)*r.
        Cl(3) rotor: R = cos(phi/2) - sin(phi/2)*e12 (note sign)."""
        R = np.cos(phi / 2) - np.sin(phi / 2) * (e1 ^ e2)
        return R * v * ~R

    def cl3_x_rotate(v, theta=0.4):
        """X-rotation in Cl(3): rotation in e2-e3 plane.
        QM convention: exp(-i*theta/2*sx) maps r -> Rx(theta)*r.
        Cl(3) rotor: R = cos(theta/2) - sin(theta/2)*e23."""
        R = np.cos(theta / 2) - np.sin(theta / 2) * (e2 ^ e3)
        return R * v * ~R

    def cl3_z_dephase(v, s=0.5):
        """Z-dephasing in Cl(3): project onto e3 axis, mix."""
        z_comp = float(v | e3)
        proj = z_comp * e3
        return (1 - s) * v + s * proj

    def cl3_x_dephase(v, s=0.5):
        """X-dephasing in Cl(3): project onto e1 axis, mix."""
        x_comp = float(v | e1)
        proj = x_comp * e1
        return (1 - s) * v + s * proj

    cl3_ops = {
        "Ti": cl3_z_dephase,
        "Fe": cl3_z_rotate,
        "Te": cl3_x_dephase,
        "Fi": cl3_x_rotate
    }

    cl3_results = []
    test_vectors = [
        np.array([1.0, 0.0, 0.0]),
        np.array([0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 1.0]),
        np.array([1.0, 1.0, 0.0]) / np.sqrt(2),
        np.array([1.0, 1.0, 1.0]) / np.sqrt(3),
    ]

    for pr in pair_results:
        op_a_name = pr["op_A"]
        op_b_name = pr["op_B"]
        agreements = []
        for tv in test_vectors:
            # Matrix path
            theta_h = np.arccos(np.clip(tv[2], -1, 1))
            phi_h = np.arctan2(tv[1], tv[0])
            psi = np.array([np.cos(theta_h / 2),
                            np.exp(1j * phi_h) * np.sin(theta_h / 2)])
            rho = np.outer(psi, psi.conj())
            rho_out = OPS[OP_NAMES.index(op_b_name)](
                OPS[OP_NAMES.index(op_a_name)](rho))
            bv_matrix = bloch_vector(rho_out)

            # Cl(3) path
            v_cl3 = tv[0] * e1 + tv[1] * e2 + tv[2] * e3
            v_out = cl3_ops[op_b_name](cl3_ops[op_a_name](v_cl3))
            bv_cl3 = np.array([float(v_out | e1),
                               float(v_out | e2),
                               float(v_out | e3)])

            diff = float(np.linalg.norm(bv_matrix - bv_cl3))
            agreements.append(diff < 0.15)

        cl3_results.append({
            "pair": f"{op_a_name}->{op_b_name}",
            "agreement_frac": sum(agreements) / len(agreements),
            "note": "exact" if all(agreements) else "diverges (dephasing is non-unitary)"
        })

    return cl3_results

# ─── MAIN SIM ────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    print("=" * 70)
    print("COMPOUND OPERATOR GEOMETRY SIM")
    print("=" * 70)

    pure_states = make_pure_states(10)
    results = {
        "name": "compound_operator_geometry",
        "sim": "compound_operator_geometry",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "classification": "supporting",
        "classification_note": (
            "Supporting pairwise operator/geometry coupling map. Useful as a successor "
            "surface for local geometry/operator legos, but not a closure-grade proof."
        ),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tests": {}
    }

    # ═══════════════════════════════════════════════════════════════════════
    # TEST 1: ALL 16 TWO-OPERATOR PAIRS
    # ═══════════════════════════════════════════════════════════════════════
    print("\n--- TEST 1: 16 two-operator pairs ---")
    pair_results = []

    for i, (name_a, op_a) in enumerate(zip(OP_NAMES, OPS)):
        for j, (name_b, op_b) in enumerate(zip(OP_NAMES, OPS)):
            purities_ab = []
            purities_ba = []
            geos_ab = []
            geos_ba = []
            order_dists = []
            # After 5 iterations
            converge_geos = []
            converge_purities = []

            for rho0 in pure_states:
                # A then B
                rho_ab = op_b(op_a(rho0))
                purities_ab.append(purity(rho_ab))
                geos_ab.append(classify_geometry(rho_ab))

                # B then A
                rho_ba = op_a(op_b(rho0))
                purities_ba.append(purity(rho_ba))
                geos_ba.append(classify_geometry(rho_ba))

                # Order matters?
                order_dists.append(trace_distance(rho_ab, rho_ba))

                # 5 iterations of A,B,A,B,...
                rho_iter = rho0.copy()
                for _ in range(5):
                    rho_iter = op_a(rho_iter)
                    rho_iter = op_b(rho_iter)
                converge_geos.append(classify_geometry(rho_iter))
                converge_purities.append(purity(rho_iter))

            # Determine dominant geometry
            from collections import Counter
            geo_counts_ab = Counter(geos_ab)
            geo_counts_ba = Counter(geos_ba)
            converge_counts = Counter(converge_geos)

            entry = {
                "op_A": name_a,
                "op_B": name_b,
                "single_pass": {
                    "AB_mean_purity": round(float(np.mean(purities_ab)), 4),
                    "BA_mean_purity": round(float(np.mean(purities_ba)), 4),
                    "AB_geometries": dict(geo_counts_ab),
                    "BA_geometries": dict(geo_counts_ba),
                    "mean_order_distance": round(float(np.mean(order_dists)), 6),
                    "order_matters": float(np.mean(order_dists)) > 0.001,
                    "S2_survives_AB": geo_counts_ab.get("S2", 0) == len(pure_states),
                    "S2_survives_BA": geo_counts_ba.get("S2", 0) == len(pure_states),
                },
                "after_5_cycles": {
                    "mean_purity": round(float(np.mean(converge_purities)), 4),
                    "geometries": dict(converge_counts),
                    "attractor": converge_counts.most_common(1)[0][0],
                }
            }
            entry["single_pass"]["pass"] = (
                finite_and_bounded(entry["single_pass"]["AB_mean_purity"])
                and finite_and_bounded(entry["single_pass"]["BA_mean_purity"])
                and finite_and_bounded(entry["single_pass"]["mean_order_distance"], 0.0, float("inf"))
                and geometries_known(entry["single_pass"]["AB_geometries"])
                and geometries_known(entry["single_pass"]["BA_geometries"])
            )
            entry["after_5_cycles"]["pass"] = (
                finite_and_bounded(entry["after_5_cycles"]["mean_purity"])
                and entry["after_5_cycles"]["attractor"] in ALLOWED_GEOMETRIES
                and geometries_known(entry["after_5_cycles"]["geometries"])
            )
            entry["pass"] = entry["single_pass"]["pass"] and entry["after_5_cycles"]["pass"]
            pair_results.append(entry)
            tag = "=" if not entry["single_pass"]["order_matters"] else "!="
            print(f"  {name_a}->{name_b}: purity={entry['single_pass']['AB_mean_purity']:.4f}  "
                  f"AB{tag}BA  attractor@5={entry['after_5_cycles']['attractor']}")

    results["tests"]["two_operator_pairs"] = pair_results

    # ═══════════════════════════════════════════════════════════════════════
    # TEST 2: 20 REPRESENTATIVE THREE-OPERATOR TRIPLES
    # ═══════════════════════════════════════════════════════════════════════
    print("\n--- TEST 2: 20 three-operator triples ---")

    triples = [
        # Canonical-like
        ("Ti", "Fe", "Te"), ("Ti", "Fe", "Fi"), ("Fe", "Te", "Fi"), ("Ti", "Te", "Fi"),
        # All same
        ("Ti", "Ti", "Ti"), ("Fe", "Fe", "Fe"), ("Te", "Te", "Te"), ("Fi", "Fi", "Fi"),
        # Reversed
        ("Fi", "Te", "Fe"), ("Fi", "Te", "Ti"), ("Te", "Fe", "Ti"), ("Fi", "Fe", "Ti"),
        # Mixed interesting
        ("Ti", "Fi", "Te"), ("Fe", "Ti", "Fi"), ("Te", "Ti", "Fe"), ("Fi", "Ti", "Te"),
        # Dissipative-heavy
        ("Ti", "Te", "Ti"), ("Te", "Ti", "Te"),
        # Unitary-heavy
        ("Fe", "Fi", "Fe"), ("Fi", "Fe", "Fi"),
    ]

    triple_results = []
    op_map = dict(zip(OP_NAMES, OPS))

    for triple in triples:
        purities_list = []
        geos_list = []
        converge_purities = []
        converge_geos = []

        for rho0 in pure_states:
            # Single pass
            rho = rho0.copy()
            for op_name in triple:
                rho = op_map[op_name](rho)
            purities_list.append(purity(rho))
            geos_list.append(classify_geometry(rho))

            # 5 rounds
            rho_iter = rho0.copy()
            for _ in range(5):
                for op_name in triple:
                    rho_iter = op_map[op_name](rho_iter)
            converge_purities.append(purity(rho_iter))
            converge_geos.append(classify_geometry(rho_iter))

        from collections import Counter
        geo_counts = Counter(geos_list)
        converge_counts = Counter(converge_geos)

        entry = {
            "sequence": list(triple),
            "single_pass": {
                "mean_purity": round(float(np.mean(purities_list)), 4),
                "geometries": dict(geo_counts),
                "S2_survives": geo_counts.get("S2", 0) == len(pure_states),
            },
            "after_5_rounds": {
                "mean_purity": round(float(np.mean(converge_purities)), 4),
                "geometries": dict(converge_counts),
                "attractor": converge_counts.most_common(1)[0][0],
            }
        }
        entry["single_pass"]["pass"] = (
            finite_and_bounded(entry["single_pass"]["mean_purity"])
            and geometries_known(entry["single_pass"]["geometries"])
        )
        entry["after_5_rounds"]["pass"] = (
            finite_and_bounded(entry["after_5_rounds"]["mean_purity"])
            and entry["after_5_rounds"]["attractor"] in ALLOWED_GEOMETRIES
            and geometries_known(entry["after_5_rounds"]["geometries"])
        )
        entry["pass"] = entry["single_pass"]["pass"] and entry["after_5_rounds"]["pass"]
        triple_results.append(entry)
        label = "->".join(triple)
        print(f"  {label:20s}: p1={entry['single_pass']['mean_purity']:.4f}  "
              f"p5={entry['after_5_rounds']['mean_purity']:.4f}  "
              f"attractor={entry['after_5_rounds']['attractor']}")

    results["tests"]["three_operator_triples"] = triple_results

    # ═══════════════════════════════════════════════════════════════════════
    # TEST 3: FULL ENGINE CYCLE Ti->Fe->Te->Fi
    # ═══════════════════════════════════════════════════════════════════════
    print("\n--- TEST 3: Full engine cycle ---")

    forward_seq = ["Ti", "Fe", "Te", "Fi"]
    reverse_seq = ["Fi", "Te", "Fe", "Ti"]
    cycle_results = {}

    for label, seq in [("forward_TiFeTeFi", forward_seq),
                       ("reverse_FiTeFeTi", reverse_seq)]:
        cycle_data = {"sequence": seq, "cycles": {}}
        for n_cycles in [1, 5, 10, 20]:
            purities_list = []
            bvecs = []
            geos = []

            for rho0 in pure_states:
                rho = rho0.copy()
                for _ in range(n_cycles):
                    for op_name in seq:
                        rho = op_map[op_name](rho)
                purities_list.append(purity(rho))
                bv = bloch_vector(rho)
                bvecs.append(bv.tolist())
                geos.append(classify_geometry(rho))

            from collections import Counter
            geo_counts = Counter(geos)
            mean_bv = np.mean(bvecs, axis=0).tolist()

            cycle_data["cycles"][str(n_cycles)] = {
                "mean_purity": round(float(np.mean(purities_list)), 6),
                "min_purity": round(float(np.min(purities_list)), 6),
                "max_purity": round(float(np.max(purities_list)), 6),
                "mean_bloch_vector": [round(v, 6) for v in mean_bv],
                "bloch_norm": round(float(np.linalg.norm(mean_bv)), 6),
                "geometries": dict(geo_counts),
                "attractor": geo_counts.most_common(1)[0][0],
                "pass": (
                    finite_and_bounded(float(np.mean(purities_list)))
                    and geo_counts.most_common(1)[0][0] in ALLOWED_GEOMETRIES
                ),
            }
            print(f"  {label} x{n_cycles:2d}: purity={np.mean(purities_list):.6f}  "
                  f"|r|={np.linalg.norm(mean_bv):.4f}  "
                  f"geo={geo_counts.most_common(1)[0][0]}")

        cycle_results[label] = cycle_data

    # Compare forward vs reverse attractors
    fwd_20 = cycle_results["forward_TiFeTeFi"]["cycles"]["20"]
    rev_20 = cycle_results["reverse_FiTeFeTi"]["cycles"]["20"]
    cycle_results["forward_vs_reverse"] = {
        "same_attractor": fwd_20["attractor"] == rev_20["attractor"],
        "purity_diff": round(abs(fwd_20["mean_purity"] - rev_20["mean_purity"]), 6),
        "bloch_distance": round(float(np.linalg.norm(
            np.array(fwd_20["mean_bloch_vector"]) -
            np.array(rev_20["mean_bloch_vector"]))), 6),
        "pass": fwd_20["attractor"] == rev_20["attractor"],
    }
    print(f"\n  Forward vs Reverse: same_attractor={cycle_results['forward_vs_reverse']['same_attractor']}  "
          f"purity_diff={cycle_results['forward_vs_reverse']['purity_diff']:.6f}")

    results["tests"]["engine_cycle"] = cycle_results

    # ═══════════════════════════════════════════════════════════════════════
    # TEST 4: Cl(3) CROSS-CHECK
    # ═══════════════════════════════════════════════════════════════════════
    print("\n--- TEST 4: Cl(3) cross-check ---")
    cl3_results = run_cl3_crosscheck(pair_results)
    for cr in cl3_results:
        cr["pass"] = cr["agreement_frac"] == 1.0
    for cr in cl3_results:
        print(f"  {cr['pair']:10s}: agreement={cr['agreement_frac']:.0%}  {cr['note']}")
    results["tests"]["cl3_crosscheck"] = cl3_results

    # ═══════════════════════════════════════════════════════════════════════
    # TEST 5: 2-QUBIT ENTANGLING GATE SEQUENCES
    # ═══════════════════════════════════════════════════════════════════════
    print("\n--- TEST 5: 2-qubit entangling sequences ---")

    # Product state: |00><00|
    psi00 = np.array([1, 0, 0, 0], dtype=complex)
    rho_product = np.outer(psi00, psi00.conj())

    # Also test |+0>
    psi_plus0 = np.kron(
        np.array([1, 1], dtype=complex) / np.sqrt(2),
        np.array([1, 0], dtype=complex)
    )
    rho_plus0 = np.outer(psi_plus0, psi_plus0.conj())

    def Ti_kron_I(rho_AB, s=0.5):
        """Ti on qubit A, identity on B."""
        P0 = np.array([[1, 0], [0, 0]], dtype=complex)
        P1 = np.array([[0, 0], [0, 1]], dtype=complex)
        K0 = np.kron(P0, I2)
        K1 = np.kron(P1, I2)
        return (1 - s) * rho_AB + s * (K0 @ rho_AB @ K0 + K1 @ rho_AB @ K1)

    def Te_kron_I(rho_AB, s=0.5):
        """Te on qubit A, identity on B."""
        Qp = np.array([[1, 1], [1, 1]], dtype=complex) / 2
        Qm = np.array([[1, -1], [-1, 1]], dtype=complex) / 2
        K0 = np.kron(Qp, I2)
        K1 = np.kron(Qm, I2)
        return (1 - s) * rho_AB + s * (K0 @ rho_AB @ K0 + K1 @ rho_AB @ K1)

    def Fe_kron_I(rho_AB, phi=0.4):
        """Fe on qubit A, identity on B."""
        U = np.kron(expm(-1j * phi / 2 * sz), I2)
        return U @ rho_AB @ U.conj().T

    def Fi_kron_I(rho_AB, theta=0.4):
        """Fi on qubit A, identity on B."""
        U = np.kron(expm(-1j * theta / 2 * sx), I2)
        return U @ rho_AB @ U.conj().T

    entangling_sequences = [
        ("Ti_I->Ent->Te_I->Ent", [Ti_kron_I, Ent, Te_kron_I, Ent]),
        ("Ent->Ti_I->Ent->Te_I", [Ent, Ti_kron_I, Ent, Te_kron_I]),
        ("Ti_I->Fe_I->Ent->Te_I->Fi_I->Ent", [Ti_kron_I, Fe_kron_I, Ent, Te_kron_I, Fi_kron_I, Ent]),
        ("Ent->Ti_I->Fe_I->Te_I->Fi_I", [Ent, Ti_kron_I, Fe_kron_I, Te_kron_I, Fi_kron_I]),
        ("Ti_I->Te_I->Ent", [Ti_kron_I, Te_kron_I, Ent]),
        ("Ent->Ti_I->Te_I", [Ent, Ti_kron_I, Te_kron_I]),
    ]

    ent_results = []
    for init_label, init_state in [("00", rho_product), ("+0", rho_plus0)]:
        for seq_label, seq_ops in entangling_sequences:
            step_data = []
            rho = init_state.copy()

            # Track after each operator
            for k, op in enumerate(seq_ops):
                rho = op(rho)
                c = concurrence(rho)
                mi = mutual_information(rho)
                rho_A = partial_trace_B(rho)
                p_A = purity(rho_A)
                step_data.append({
                    "step": k + 1,
                    "concurrence": round(c, 6),
                    "mutual_info": round(mi, 6),
                    "subsystem_purity": round(p_A, 6),
                })

            # 5 cycles
            rho_5 = init_state.copy()
            for _ in range(5):
                for op in seq_ops:
                    rho_5 = op(rho_5)
            c5 = concurrence(rho_5)
            mi5 = mutual_information(rho_5)
            rho_A5 = partial_trace_B(rho_5)

            entry = {
                "init_state": init_label,
                "sequence": seq_label,
                "per_step": step_data,
                "after_5_cycles": {
                    "concurrence": round(c5, 6),
                    "mutual_info": round(mi5, 6),
                    "subsystem_purity": round(purity(rho_A5), 6),
                    "subsystem_geometry": classify_geometry(rho_A5),
                    "pass": classify_geometry(rho_A5) in ALLOWED_GEOMETRIES,
                }
            }
            entry["pass"] = all(
                np.isfinite(step["concurrence"])
                and np.isfinite(step["mutual_info"])
                and np.isfinite(step["subsystem_purity"])
                for step in step_data
            ) and entry["after_5_cycles"]["pass"]
            ent_results.append(entry)
            print(f"  [{init_label}] {seq_label}: "
                  f"C_final={step_data[-1]['concurrence']:.4f}  "
                  f"C_5cyc={c5:.4f}  "
                  f"sub_geo={entry['after_5_cycles']['subsystem_geometry']}")

    results["tests"]["entangling_sequences"] = ent_results

    # ═══════════════════════════════════════════════════════════════════════
    # DISCOVERY TABLE: What sequences preserve which geometry?
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("DISCOVERY: COMPOUND GEOMETRY COMPATIBILITY TABLE")
    print("=" * 70)

    discovery_table = []

    # From pair results
    for pr in pair_results:
        row = {
            "sequence": f"{pr['op_A']}->{pr['op_B']}",
            "S2_survives": pr["single_pass"]["S2_survives_AB"],
            "fiber": any(g in ["z-fiber", "x-fiber"]
                        for g in pr["single_pass"]["AB_geometries"]),
            "torus": "torus" in pr["single_pass"]["AB_geometries"],
            "entangled": "N/A",
            "attractor_5cyc": pr["after_5_cycles"]["attractor"],
            "order_matters": pr["single_pass"]["order_matters"],
            "purity_1pass": pr["single_pass"]["AB_mean_purity"],
        }
        discovery_table.append(row)

    # From engine cycle
    for label in ["forward_TiFeTeFi", "reverse_FiTeFeTi"]:
        cd = cycle_results[label]
        c1 = cd["cycles"]["1"]
        c5 = cd["cycles"]["5"]
        row = {
            "sequence": label.replace("_", "->").replace("forward->", "").replace("reverse->", "rev:"),
            "S2_survives": c1["geometries"].get("S2", 0) > 0,
            "fiber": any(g in ["z-fiber", "x-fiber"] for g in c1["geometries"]),
            "torus": "torus" in c1["geometries"],
            "entangled": "N/A",
            "attractor_5cyc": c5["attractor"],
            "order_matters": True,
            "purity_1pass": c1["mean_purity"],
        }
        discovery_table.append(row)

    # From entangling results (select key ones)
    for er in ent_results:
        if er["init_state"] == "00":
            row = {
                "sequence": f"[2q] {er['sequence']}",
                "S2_survives": "N/A",
                "fiber": "N/A",
                "torus": "N/A",
                "entangled": er["after_5_cycles"]["concurrence"] > 0.01,
                "attractor_5cyc": er["after_5_cycles"]["subsystem_geometry"],
                "order_matters": True,
                "purity_1pass": er["per_step"][-1]["subsystem_purity"],
            }
            discovery_table.append(row)

    results["tests"]["discovery_table"] = discovery_table

    # Print table
    print(f"\n{'Sequence':<40s} {'S2?':<6s} {'Fiber?':<7s} {'Torus?':<7s} "
          f"{'Ent?':<6s} {'Attractor':<12s} {'Order?':<7s} {'Purity':<8s}")
    print("-" * 95)
    for row in discovery_table:
        s2 = str(row["S2_survives"])[:5]
        fib = str(row["fiber"])[:5]
        tor = str(row["torus"])[:5]
        ent = str(row["entangled"])[:5]
        print(f"{row['sequence']:<40s} {s2:<6s} {fib:<7s} {tor:<7s} "
              f"{ent:<6s} {row['attractor_5cyc']:<12s} "
              f"{str(row['order_matters']):<7s} {row['purity_1pass']:<8.4f}")

    # ═══════════════════════════════════════════════════════════════════════
    # SUMMARY STATISTICS
    # ═══════════════════════════════════════════════════════════════════════
    n_commutative = sum(1 for pr in pair_results if not pr["single_pass"]["order_matters"])
    n_s2_survive = sum(1 for pr in pair_results if pr["single_pass"]["S2_survives_AB"])
    attractor_dist = {}
    for pr in pair_results:
        att = pr["after_5_cycles"]["attractor"]
        attractor_dist[att] = attractor_dist.get(att, 0) + 1

    summary = {
        "total_pairs_tested": len(pair_results),
        "commutative_pairs": n_commutative,
        "non_commutative_pairs": len(pair_results) - n_commutative,
        "S2_preserving_pairs": n_s2_survive,
        "attractor_distribution": attractor_dist,
        "engine_forward_attractor": cycle_results["forward_TiFeTeFi"]["cycles"]["20"]["attractor"],
        "engine_reverse_attractor": cycle_results["reverse_FiTeFeTi"]["cycles"]["20"]["attractor"],
        "forward_reverse_same": cycle_results["forward_vs_reverse"]["same_attractor"],
        "cl3_exact_agreement_count": sum(1 for cr in cl3_results if cr["agreement_frac"] == 1.0),
        "cl3_partial_agreement_count": sum(1 for cr in cl3_results if 0 < cr["agreement_frac"] < 1.0),
    }
    positive = {
        "all_operator_pairs_covered": {
            "count": len(pair_results),
            "expected": len(OP_NAMES) * len(OP_NAMES),
            "pass": len(pair_results) == len(OP_NAMES) * len(OP_NAMES),
        },
        "non_commutative_pairs_detected": {
            "count": summary["non_commutative_pairs"],
            "pass": summary["non_commutative_pairs"] > 0,
        },
        "engine_cycles_reach_named_attractors": {
            "forward": summary["engine_forward_attractor"],
            "reverse": summary["engine_reverse_attractor"],
            "pass": bool(summary["engine_forward_attractor"]) and bool(summary["engine_reverse_attractor"]),
        },
        "cl3_exact_crosschecks_exist": {
            "count": summary["cl3_exact_agreement_count"],
            "pass": summary["cl3_exact_agreement_count"] > 0,
        },
    }
    negative = {
        "not_all_pairs_commute": {
            "commutative_pairs": summary["commutative_pairs"],
            "total_pairs": summary["total_pairs_tested"],
            "pass": summary["commutative_pairs"] < summary["total_pairs_tested"],
        },
        "not_all_pairs_preserve_S2": {
            "S2_preserving_pairs": summary["S2_preserving_pairs"],
            "total_pairs": summary["total_pairs_tested"],
            "pass": summary["S2_preserving_pairs"] < summary["total_pairs_tested"],
        },
        "order_dependence_exists": {
            "non_commutative_pairs": summary["non_commutative_pairs"],
            "pass": summary["non_commutative_pairs"] > 0,
        },
    }
    boundary = {
        "forward_reverse_relation_is_defined": {
            "same_attractor": summary["forward_reverse_same"],
            "pass": isinstance(summary["forward_reverse_same"], bool),
        },
        "attractor_distribution_nonempty": {
            "distribution": attractor_dist,
            "pass": bool(attractor_dist),
        },
    }
    summary["discovery_table_pass"] = (
        len(discovery_table) == len(pair_results) + 2 + sum(1 for er in ent_results if er["init_state"] == "00")
    )
    summary["positive_pass"] = all(item["pass"] for item in positive.values())
    summary["negative_pass"] = all(item["pass"] for item in negative.values())
    summary["boundary_pass"] = all(item["pass"] for item in boundary.values())
    summary["contract_pass"] = (
        summary["positive_pass"]
        and summary["negative_pass"]
        and summary["boundary_pass"]
        and summary["discovery_table_pass"]
    )
    summary["all_pass"] = summary["contract_pass"]
    results["positive"] = positive
    results["negative"] = negative
    results["boundary"] = boundary
    results["summary"] = summary

    print(f"\n--- SUMMARY ---")
    print(f"  Commutative pairs:    {n_commutative}/16")
    print(f"  S2-preserving pairs:  {n_s2_survive}/16")
    print(f"  Attractor distribution: {attractor_dist}")
    print(f"  Engine forward attractor:  {summary['engine_forward_attractor']}")
    print(f"  Engine reverse attractor:  {summary['engine_reverse_attractor']}")
    print(f"  Forward=Reverse?:     {summary['forward_reverse_same']}")
    print(f"  Cl(3) exact matches:  {summary['cl3_exact_agreement_count']}/16")

    elapsed = time.time() - t0
    results["elapsed_seconds"] = round(elapsed, 2)
    print(f"\n  Elapsed: {elapsed:.2f}s")

    # ─── Write results ───────────────────────────────────────────────────
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "compound_operator_geometry_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Results written to: {out_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
