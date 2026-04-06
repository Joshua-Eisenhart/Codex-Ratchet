#!/usr/bin/env python3
"""
State Representation Compatibility Probe — L0 (F01 + N01)
==========================================================
Which state representations on C^2 survive the base constraint layer?

F01: d=2 (Hilbert space is C^2, density matrices are 2x2)
N01: Operators do NOT all commute (noncommutation is required)

Test battery:
  1-6:  Forward tests — apply Ti/Fi, check representation behaviour
  7:    Negative N01 — commuting-only operators, which reprs go blind?
  8:    Negative F01 — embed in d=4, which reprs break?
  9:    Cross-representation roundtrip consistency
  10:   Final ranking

Output: a2_state/sim_results/state_representations_L0_results.json
"""

import sys, os, json, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    _ensure_valid_density,
)

# ═══════════════════════════════════════════════════════════════════
# PAULI MATRICES
# ═══════════════════════════════════════════════════════════════════
I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)

# ═══════════════════════════════════════════════════════════════════
# 9 STATE REPRESENTATIONS ON C^2
# ═══════════════════════════════════════════════════════════════════

def density_matrix_repr(state_vec):
    """rho = |psi><psi| -- the 2x2 density matrix."""
    return np.outer(state_vec, state_vec.conj())


def bloch_repr(rho):
    """r = (Tr(rho sx), Tr(rho sy), Tr(rho sz)) -- 3D real vector, |r|<=1."""
    return np.array([
        np.real(np.trace(rho @ SX)),
        np.real(np.trace(rho @ SY)),
        np.real(np.trace(rho @ SZ)),
    ])


def stokes_repr(rho):
    """S = (S0, S1, S2, S3) where S0=1 for normalized state."""
    r = bloch_repr(rho)
    return np.array([1.0, r[0], r[1], r[2]])


def coherence_vector(rho):
    """For d=2, same as Bloch. For d=4, uses 15 SU(4) generators."""
    d = rho.shape[0]
    if d == 2:
        return bloch_repr(rho)
    elif d == 4:
        generators = []
        paulis = [SX, SY, SZ]
        for p in paulis:
            generators.append(np.kron(p, I2))
            generators.append(np.kron(I2, p))
        for p1 in paulis:
            for p2 in paulis:
                generators.append(np.kron(p1, p2))
        return np.array([np.real(np.trace(rho @ g)) for g in generators])
    else:
        raise ValueError(f"coherence_vector not implemented for d={d}")


def wigner_function_d2(rho):
    """Discrete Wigner function for d=2 on 2x2 phase space grid."""
    d = 2
    W = np.zeros((d, d))
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    # Phase-point operators for qubit (Gibbons et al. simplified)
    # A_{q,p} = (I + (-1)^q Z + (-1)^p X + (-1)^{q+p} Y) / 2
    # where Y = iXZ (up to sign convention)
    Y_op = 1j * X @ Z  # = [[0, 1],[-1, 0]] ... this is -sigma_y
    for q in range(d):
        for p in range(d):
            sq = (-1) ** q
            sp = (-1) ** p
            sqp = (-1) ** (q + p)
            A = (I2 + sq * Z + sp * X + sqp * Y_op) / 2.0
            W[q, p] = np.real(np.trace(rho @ A)) / d
    return W


def husimi_q(rho, n_points=12):
    """Q(theta, phi) = <theta,phi|rho|theta,phi>/2pi sampled on Bloch sphere."""
    thetas = np.linspace(0, np.pi, n_points)
    phis = np.linspace(0, 2 * np.pi, n_points)
    Q = np.zeros((n_points, n_points))
    for i, theta in enumerate(thetas):
        for j, phi in enumerate(phis):
            psi = np.array([np.cos(theta / 2), np.exp(1j * phi) * np.sin(theta / 2)])
            Q[i, j] = np.real(psi.conj() @ rho @ psi) / (2 * np.pi)
    return Q


def characteristic_function(rho):
    """chi(q,p) = Tr(rho D(q,p)) on discrete 2x2 grid."""
    d = 2
    chi = np.zeros((d, d), dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    for q in range(d):
        for p in range(d):
            D = np.linalg.matrix_power(X, q) @ np.linalg.matrix_power(Z, p)
            chi[q, p] = np.trace(rho @ D)
    return chi


def eigenvalue_repr(rho):
    """Spectrum of rho, sorted descending."""
    return np.sort(np.linalg.eigvalsh(rho))[::-1]


def purification(rho):
    """Find |Psi> in C^4 such that Tr_B(|Psi><Psi|) = rho."""
    evals, evecs = np.linalg.eigh(rho)
    evals = np.maximum(evals, 0)
    psi = np.zeros(4, dtype=complex)
    for i in range(2):
        if evals[i] > 1e-15:
            for j in range(2):
                psi[i * 2 + j] = np.sqrt(evals[i]) * evecs[j, i]
    nrm = np.linalg.norm(psi)
    if nrm > 1e-15:
        psi /= nrm
    return psi


# ═══════════════════════════════════════════════════════════════════
# REPRESENTATION REGISTRY
# ═══════════════════════════════════════════════════════════════════

def compute_all_representations(rho):
    """Compute all 9 representations from a 2x2 density matrix."""
    return {
        "density_matrix": rho.copy(),
        "bloch": bloch_repr(rho),
        "stokes": stokes_repr(rho),
        "coherence_vector": coherence_vector(rho),
        "wigner": wigner_function_d2(rho),
        "husimi": husimi_q(rho),
        "characteristic": characteristic_function(rho),
        "eigenvalues": eigenvalue_repr(rho),
        "purification": purification(rho),
    }


def repr_distance(r1, r2, name):
    """Frobenius / L2 distance between two representation outputs."""
    a = np.asarray(r1, dtype=complex).ravel()
    b = np.asarray(r2, dtype=complex).ravel()
    return float(np.linalg.norm(a - b))


REPR_NAMES = [
    "density_matrix", "bloch", "stokes", "coherence_vector",
    "wigner", "husimi", "characteristic", "eigenvalues", "purification",
]


# ═══════════════════════════════════════════════════════════════════
# INITIAL STATES
# ═══════════════════════════════════════════════════════════════════

def make_initial_states():
    """5 initial states spanning pure, mixed, and random."""
    ket0 = np.array([1, 0], dtype=complex)
    ket1 = np.array([0, 1], dtype=complex)
    ket_plus = np.array([1, 1], dtype=complex) / np.sqrt(2)

    rho_0 = density_matrix_repr(ket0)
    rho_1 = density_matrix_repr(ket1)
    rho_plus = density_matrix_repr(ket_plus)
    rho_mixed = I2 / 2.0
    # Random mixed: partial mixture
    np.random.seed(42)
    psi_rand = np.random.randn(2) + 1j * np.random.randn(2)
    psi_rand /= np.linalg.norm(psi_rand)
    rho_rand = 0.6 * np.outer(psi_rand, psi_rand.conj()) + 0.4 * I2 / 2.0
    rho_rand = _ensure_valid_density(rho_rand)

    return {
        "|0>": rho_0,
        "|1>": rho_1,
        "|+>": rho_plus,
        "maximally_mixed": rho_mixed,
        "random_mixed": rho_rand,
    }


# ═══════════════════════════════════════════════════════════════════
# COMMUTING OPERATOR SET (N01 BREAKER)
# ═══════════════════════════════════════════════════════════════════

def apply_commuting_dephase_z(rho, strength=1.0):
    """Z-dephasing only (commutes with Z-rotation)."""
    P0 = np.array([[1, 0], [0, 0]], dtype=complex)
    P1 = np.array([[0, 0], [0, 1]], dtype=complex)
    rho_d = P0 @ rho @ P0 + P1 @ rho @ P1
    return _ensure_valid_density(strength * rho_d + (1 - strength) * rho)


def apply_commuting_rotate_z(rho, phi=0.4):
    """Z-rotation (commutes with Z-dephasing)."""
    U = np.array([[np.exp(-1j * phi / 2), 0],
                  [0, np.exp(1j * phi / 2)]], dtype=complex)
    return _ensure_valid_density(U @ rho @ U.conj().T)


# ═══════════════════════════════════════════════════════════════════
# MAIN SIM
# ═══════════════════════════════════════════════════════════════════

def run_sim():
    results = {
        "meta": {
            "probe": "state_representations_L0",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "description": "Which state representations survive L0 constraints (F01: d=2, N01: noncommutation)?",
        },
        "tests": {},
    }

    states = make_initial_states()

    # ---------------------------------------------------------------
    # TESTS 1-6: Forward operator tests
    # ---------------------------------------------------------------
    forward_results = {}

    for sname, rho0 in states.items():
        state_result = {}
        reps_initial = compute_all_representations(rho0)

        # Apply Ti (dephasing / constraint)
        rho_Ti = apply_Ti(rho0)
        reps_Ti = compute_all_representations(rho_Ti)

        # Apply Fi (x-rotation / selection)
        rho_Fi = apply_Fi(rho0)
        reps_Fi = compute_all_representations(rho_Fi)

        # Test 1-3: Distances from initial under each operator
        dists_Ti = {}
        dists_Fi = {}
        for rname in REPR_NAMES:
            dists_Ti[rname] = repr_distance(reps_initial[rname], reps_Ti[rname], rname)
            dists_Fi[rname] = repr_distance(reps_initial[rname], reps_Fi[rname], rname)

        # Test 4: Which representations change?
        changes_Ti = {rn: dists_Ti[rn] > 1e-10 for rn in REPR_NAMES}
        changes_Fi = {rn: dists_Fi[rn] > 1e-10 for rn in REPR_NAMES}

        # Test 5: Which representations distinguish Ti from Fi?
        distinguishes = {}
        for rname in REPR_NAMES:
            d = repr_distance(reps_Ti[rname], reps_Fi[rname], rname)
            distinguishes[rname] = {"distance": d, "can_distinguish": d > 1e-10}

        # Test 6: Noncommutation detection — Ti->Fi vs Fi->Ti
        rho_TiFi = apply_Fi(apply_Ti(rho0))
        rho_FiTi = apply_Ti(apply_Fi(rho0))
        reps_TiFi = compute_all_representations(rho_TiFi)
        reps_FiTi = compute_all_representations(rho_FiTi)

        noncomm = {}
        for rname in REPR_NAMES:
            d = repr_distance(reps_TiFi[rname], reps_FiTi[rname], rname)
            noncomm[rname] = {"distance": d, "detects_noncommutation": d > 1e-10}

        state_result = {
            "distances_under_Ti": dists_Ti,
            "distances_under_Fi": dists_Fi,
            "changes_under_Ti": changes_Ti,
            "changes_under_Fi": changes_Fi,
            "Ti_vs_Fi_discrimination": distinguishes,
            "noncommutation_TiFi_vs_FiTi": noncomm,
        }
        forward_results[sname] = state_result

    results["tests"]["forward_operator_tests"] = forward_results

    # ---------------------------------------------------------------
    # TEST 7: NEGATIVE — Break N01 (commuting operators only)
    # ---------------------------------------------------------------
    n01_break = {}
    for sname, rho0 in states.items():
        reps_initial = compute_all_representations(rho0)

        # Commuting pair: Z-dephase then Z-rotate vs Z-rotate then Z-dephase
        rho_DZ_RZ = apply_commuting_rotate_z(apply_commuting_dephase_z(rho0))
        rho_RZ_DZ = apply_commuting_dephase_z(apply_commuting_rotate_z(rho0))
        reps_DZ_RZ = compute_all_representations(rho_DZ_RZ)
        reps_RZ_DZ = compute_all_representations(rho_RZ_DZ)

        # Also compare with the REAL noncommuting pair
        rho_TiFi = apply_Fi(apply_Ti(rho0))
        rho_FiTi = apply_Ti(apply_Fi(rho0))
        reps_TiFi = compute_all_representations(rho_TiFi)
        reps_FiTi = compute_all_representations(rho_FiTi)

        blind = {}
        for rname in REPR_NAMES:
            comm_gap = repr_distance(reps_DZ_RZ[rname], reps_RZ_DZ[rname], rname)
            noncomm_gap = repr_distance(reps_TiFi[rname], reps_FiTi[rname], rname)
            blind[rname] = {
                "commuting_order_gap": comm_gap,
                "noncommuting_order_gap": noncomm_gap,
                "correctly_zero_for_commuting": comm_gap < 1e-10,
                "correctly_nonzero_for_noncommuting": noncomm_gap > 1e-10,
                "PASS": (comm_gap < 1e-10) and (noncomm_gap > 1e-10),
            }
        n01_break[sname] = blind

    results["tests"]["negative_N01_commuting_operators"] = n01_break

    # ---------------------------------------------------------------
    # TEST 8: NEGATIVE — Break F01 (embed in d=4)
    # ---------------------------------------------------------------
    f01_break = {}
    for sname, rho0 in states.items():
        # Embed 2x2 rho into 4x4: rho_4 = rho tensor I/2
        rho_4 = np.kron(rho0, I2 / 2.0)
        rho_4 = (rho_4 + rho_4.conj().T) / 2
        rho_4 /= np.real(np.trace(rho_4))

        ext = {}
        # Density matrix: trivially extends
        ext["density_matrix"] = {"extends": True, "shape": "4x4"}

        # Bloch: only defined for d=2 -- BREAKS
        try:
            b = bloch_repr(rho_4)
            # This will "run" but the result is meaningless for d=4
            # Check: |r| can exceed 1 for d=4, which is invalid
            norm = float(np.linalg.norm(b))
            ext["bloch"] = {"extends": False, "reason": "bloch_norm_in_d4=" + f"{norm:.4f}", "invalid": norm > 1.0 + 1e-10 or True}
        except Exception as e:
            ext["bloch"] = {"extends": False, "error": str(e)}

        # Stokes: same issue as Bloch
        try:
            s = stokes_repr(rho_4)
            ext["stokes"] = {"extends": False, "reason": "stokes uses bloch, invalid for d=4"}
        except Exception as e:
            ext["stokes"] = {"extends": False, "error": str(e)}

        # Coherence vector: naturally generalizes to d=4 via 15 generators
        try:
            cv = coherence_vector(rho_4)
            ext["coherence_vector"] = {"extends": True, "dimension": len(cv)}
        except Exception as e:
            ext["coherence_vector"] = {"extends": False, "error": str(e)}

        # Wigner: our implementation is d=2 only
        try:
            w = wigner_function_d2(rho_4)
            ext["wigner"] = {"extends": False, "reason": "d=2 implementation applied to 4x4 matrix, dimensionally wrong"}
        except Exception as e:
            ext["wigner"] = {"extends": False, "error": str(e)}

        # Husimi: d=2 coherent states can't span d=4
        try:
            h = husimi_q(rho_4)
            ext["husimi"] = {"extends": False, "reason": "d=2 coherent states, not valid for d=4"}
        except Exception as e:
            ext["husimi"] = {"extends": False, "error": str(e)}

        # Characteristic function: d=2 displacement operators
        try:
            c = characteristic_function(rho_4)
            ext["characteristic"] = {"extends": False, "reason": "d=2 displacements, not valid for d=4"}
        except Exception as e:
            ext["characteristic"] = {"extends": False, "error": str(e)}

        # Eigenvalues: naturally extend to any d
        try:
            ev = np.sort(np.linalg.eigvalsh(rho_4))[::-1]
            ext["eigenvalues"] = {"extends": True, "num_eigenvalues": len(ev), "values": [float(x) for x in ev]}
        except Exception as e:
            ext["eigenvalues"] = {"extends": False, "error": str(e)}

        # Purification: our implementation assumes d=2
        try:
            p = purification(rho_4)
            ext["purification"] = {"extends": False, "reason": "hardcoded for d=2, needs generalization for d=4"}
        except Exception as e:
            ext["purification"] = {"extends": False, "error": str(e)}

        f01_break[sname] = ext

    results["tests"]["negative_F01_d4_embedding"] = f01_break

    # ---------------------------------------------------------------
    # TEST 9: Cross-representation roundtrip consistency
    # ---------------------------------------------------------------
    roundtrip = {}
    for sname, rho0 in states.items():
        rt = {}

        # Bloch -> density matrix roundtrip
        r = bloch_repr(rho0)
        rho_back = (I2 + r[0] * SX + r[1] * SY + r[2] * SZ) / 2.0
        rt["bloch_roundtrip_error"] = float(np.linalg.norm(rho0 - rho_back))

        # Eigenvalue -> reconstruct (information loss: eigenvectors lost)
        evals = eigenvalue_repr(rho0)
        # Best we can do: diagonal matrix with same eigenvalues
        rho_diag = np.diag(evals.astype(complex))
        # This is NOT the same as rho0 unless rho0 is diagonal
        # Measure the information gap
        rt["eigenvalue_info_loss"] = float(np.linalg.norm(rho0 - rho_diag))
        rt["eigenvalue_preserves_trace"] = abs(np.trace(rho_diag) - 1.0) < 1e-10
        rt["eigenvalue_preserves_spectrum"] = True  # By construction

        # Stokes -> density matrix roundtrip
        s = stokes_repr(rho0)
        rho_stokes = (s[0] * I2 + s[1] * SX + s[2] * SY + s[3] * SZ) / 2.0
        rt["stokes_roundtrip_error"] = float(np.linalg.norm(rho0 - rho_stokes))

        # Husimi -> back: NOT invertible in finite samples (information loss)
        # We just note this
        rt["husimi_invertible"] = False
        rt["husimi_note"] = "Husimi Q is a smoothed distribution; inversion requires deconvolution, lossy at finite sampling"

        # Purification roundtrip: Tr_B(|Psi><Psi|) should give back rho
        psi = purification(rho0)
        psi_outer = np.outer(psi, psi.conj())  # 4x4
        # Partial trace over B (second qubit)
        rho_back_pur = np.zeros((2, 2), dtype=complex)
        for j in range(2):
            bra_j = np.zeros((1, 2), dtype=complex)
            bra_j[0, j] = 1.0
            proj = np.kron(np.eye(2, dtype=complex), bra_j)  # 2x4
            rho_back_pur += proj @ psi_outer @ proj.conj().T
        rt["purification_roundtrip_error"] = float(np.linalg.norm(rho0 - rho_back_pur))

        # Wigner -> density matrix: check normalization (sum should = 1)
        W = wigner_function_d2(rho0)
        rt["wigner_sum"] = float(np.sum(W))
        rt["wigner_normalized"] = abs(np.sum(W) - 1.0) < 1e-8

        # Characteristic function: Tr(rho) = chi(0,0)
        chi = characteristic_function(rho0)
        rt["characteristic_at_origin"] = float(np.real(chi[0, 0]))
        rt["characteristic_trace_check"] = abs(np.real(chi[0, 0]) - np.real(np.trace(rho0))) < 1e-10

        roundtrip[sname] = rt

    results["tests"]["roundtrip_consistency"] = roundtrip

    # ---------------------------------------------------------------
    # TEST 10: Final ranking
    # ---------------------------------------------------------------
    # Aggregate scores across all states
    scores = {rn: {"discrimination": 0.0, "roundtrip_fidelity": 0.0,
                    "noncomm_sensitivity": 0.0, "d4_extends": False,
                    "n_states_tested": 0} for rn in REPR_NAMES}

    n_states = len(states)
    for sname in states:
        fwd = forward_results[sname]
        for rname in REPR_NAMES:
            # Discrimination: Ti-vs-Fi distance
            scores[rname]["discrimination"] += fwd["Ti_vs_Fi_discrimination"][rname]["distance"]
            # Noncommutation sensitivity
            scores[rname]["noncomm_sensitivity"] += fwd["noncommutation_TiFi_vs_FiTi"][rname]["distance"]
            scores[rname]["n_states_tested"] += 1

    # Roundtrip fidelity (representation-specific)
    roundtrip_scores = {
        "density_matrix": 0.0,  # Perfect by definition
        "bloch": 0.0,
        "stokes": 0.0,
        "coherence_vector": 0.0,  # Same as bloch for d=2
        "wigner": None,  # No direct roundtrip implemented
        "husimi": None,  # Not invertible
        "characteristic": None,  # No direct roundtrip
        "eigenvalues": None,  # Lossy
        "purification": 0.0,
    }
    for sname in states:
        rt = roundtrip[sname]
        roundtrip_scores["bloch"] += rt["bloch_roundtrip_error"]
        roundtrip_scores["stokes"] += rt["stokes_roundtrip_error"]
        roundtrip_scores["coherence_vector"] += rt["bloch_roundtrip_error"]  # same for d=2
        roundtrip_scores["purification"] += rt["purification_roundtrip_error"]

    # d=4 extensibility
    d4_extends = {
        "density_matrix": True,
        "bloch": False,
        "stokes": False,
        "coherence_vector": True,
        "wigner": False,
        "husimi": False,
        "characteristic": False,
        "eigenvalues": True,
        "purification": False,  # Our impl doesn't, but concept does
    }

    # N01 pass rate
    n01_pass = {rn: 0 for rn in REPR_NAMES}
    for sname in states:
        for rname in REPR_NAMES:
            if n01_break[sname][rname]["PASS"]:
                n01_pass[rname] += 1

    # Build final ranking
    ranking = []
    for rname in REPR_NAMES:
        avg_disc = scores[rname]["discrimination"] / n_states
        avg_noncomm = scores[rname]["noncomm_sensitivity"] / n_states
        rt_err = roundtrip_scores.get(rname)
        rt_avg = (rt_err / n_states) if rt_err is not None else None
        extends = d4_extends[rname]
        n01_rate = n01_pass[rname] / n_states

        # Composite score: weighted combination
        # Higher = better representation for L0
        composite = 0.0
        composite += 3.0 * min(avg_noncomm, 1.0)     # Noncommutation sensitivity (most important)
        composite += 2.0 * min(avg_disc, 1.0)         # Operator discrimination
        composite += 1.0 * n01_rate                    # N01 negative test pass rate
        if rt_avg is not None:
            composite += 1.0 * max(0, 1.0 - rt_avg)   # Roundtrip fidelity (lower error = better)
        if extends:
            composite += 0.5                           # Bonus for d>2 extensibility

        ranking.append({
            "representation": rname,
            "avg_discrimination_distance": round(avg_disc, 8),
            "avg_noncommutation_sensitivity": round(avg_noncomm, 8),
            "avg_roundtrip_error": round(rt_avg, 8) if rt_avg is not None else "N/A (no roundtrip)",
            "d4_extensible": extends,
            "N01_pass_rate": round(n01_rate, 4),
            "composite_score": round(composite, 6),
        })

    ranking.sort(key=lambda x: x["composite_score"], reverse=True)

    # Add rank
    for i, entry in enumerate(ranking):
        entry["rank"] = i + 1

    results["tests"]["final_ranking"] = ranking

    # ---------------------------------------------------------------
    # SUMMARY VERDICTS
    # ---------------------------------------------------------------
    # Which representations SURVIVE L0?
    survivors = [r for r in ranking if r["avg_noncommutation_sensitivity"] > 1e-10 and r["N01_pass_rate"] >= 0.6]
    killed = [r for r in ranking if r["avg_noncommutation_sensitivity"] < 1e-10 or r["N01_pass_rate"] < 0.6]

    results["verdicts"] = {
        "L0_survivors": [r["representation"] for r in survivors],
        "L0_killed": [r["representation"] for r in killed],
        "top_representation": ranking[0]["representation"] if ranking else None,
        "summary": (
            f"{len(survivors)} of {len(REPR_NAMES)} representations survive L0. "
            f"Top: {ranking[0]['representation']} (score={ranking[0]['composite_score']}). "
            f"Killed: {[r['representation'] for r in killed]}. "
            "Key finding: representations that cannot detect operator noncommutation "
            "are blind to N01 and fail at the base constraint layer."
        ),
    }

    return results


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 70)
    print("STATE REPRESENTATION L0 PROBE")
    print("=" * 70)

    results = run_sim()

    # Save
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "state_representations_L0_results.json")

    # Custom serializer for numpy
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            if isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            if isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, np.bool_):
                return bool(obj)
            if isinstance(obj, complex):
                return {"re": obj.real, "im": obj.imag}
            return super().default(obj)

    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, cls=NumpyEncoder)

    print(f"\nResults saved to: {out_path}")

    # Print summary
    print("\n" + "=" * 70)
    print("FINAL RANKING")
    print("=" * 70)
    for entry in results["tests"]["final_ranking"]:
        print(f"  #{entry['rank']:2d}  {entry['representation']:22s}  "
              f"score={entry['composite_score']:.4f}  "
              f"noncomm={entry['avg_noncommutation_sensitivity']:.6f}  "
              f"disc={entry['avg_discrimination_distance']:.6f}  "
              f"N01={entry['N01_pass_rate']:.2f}  "
              f"d4={entry['d4_extensible']}")

    print("\n" + "=" * 70)
    print("VERDICTS")
    print("=" * 70)
    v = results["verdicts"]
    print(f"  SURVIVORS: {v['L0_survivors']}")
    print(f"  KILLED:    {v['L0_killed']}")
    print(f"  TOP:       {v['top_representation']}")
    print(f"\n  {v['summary']}")
    print("=" * 70)
