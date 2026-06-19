#!/usr/bin/env python3
"""NumPy-exact REFERENCE leg of the operator/channel ORDER layer (L11).

Computation style UNIQUE to this leg: dense 2x2 complex matrices, Kraus sums
applied explicitly, and the trace norm computed from the eigenvalues of the
Hermitian commutator difference (numpy.linalg.eigvalsh, sum of |eigvals|).

The object: a finite library of single-qubit CPTP maps and the NONCOMMUTATION
MATRIX delta(A,B,rho) = || A(B(rho)) - B(A(rho)) ||_1 over all ordered pairs.
N01 witness: order matters for (A,B) iff delta > 0.

Nothing is asserted -- every delta is DERIVED from the actual Kraus action.
This leg reads no peer result.
"""

import hashlib
import itertools
import json
import os
from datetime import datetime, timezone

import numpy as np

SIM_ID = "ordered_channel_maps_noncommutation_matrix_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 1e-9          # agreement / zero tolerance for deltas
CPTP_TOL = 1e-12    # CPTP self-checks

# -- single-qubit operators ----------------------------------------------------
I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = (X + Z) / np.sqrt(2)        # Hadamard
P0 = np.array([[1, 0], [0, 0]], dtype=complex)
P1 = np.array([[0, 0], [0, 1]], dtype=complex)

THETA = np.pi / 3   # Fi rotation angle (generic, not pi/2)
PHI = np.pi / 4     # Fe rotation angle (generic)
GAMMA = 0.3         # amplitude-damping rate


def expm_2x2(A):
    """Exact 2x2 matrix exponential via eigendecomposition (A Hermitian-times-i here)."""
    w, V = np.linalg.eig(A)
    return V @ np.diag(np.exp(w)) @ np.linalg.inv(V)


def Rx(theta):
    return expm_2x2(-1j * theta * X / 2)


def Rz(phi):
    return expm_2x2(-1j * phi * Z / 2)


# -- Kraus sets for each map ---------------------------------------------------
def kraus_library():
    lib = {}
    # Ti: full z-dephasing.  K0 = sqrt(1/2) I, K1 = sqrt(1/2) Z  (p=1 dephasing).
    lib["Ti_z_dephasing"] = [np.sqrt(0.5) * I2, np.sqrt(0.5) * Z]
    # Te: full x-basis dephasing = H (z-dephasing) H.
    lib["Te_x_dephasing"] = [np.sqrt(0.5) * I2, np.sqrt(0.5) * (H @ Z @ H)]
    # Fi: unitary x-rotation.
    lib["Fi_x_rotation"] = [Rx(THETA)]
    # Fe: unitary z-rotation.
    lib["Fe_z_rotation"] = [Rz(PHI)]
    # projector_pinch: measure-and-forget in Z basis (== Ti action).
    lib["projector_pinch"] = [P0, P1]
    # Lindblad amplitude damping toward |0>.
    K0 = np.array([[1, 0], [0, np.sqrt(1 - GAMMA)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(GAMMA)], [0, 0]], dtype=complex)
    lib["Lindblad_amp_damp"] = [K0, K1]
    return lib


def identity_kraus():
    return [I2.copy()]


# -- channel action + CPTP checks ----------------------------------------------
def apply_channel(kraus, rho):
    out = np.zeros((2, 2), dtype=complex)
    for K in kraus:
        out += K @ rho @ K.conj().T
    return out


def trace_norm(M):
    """||M||_1 = sum of singular values.  For a Hermitian M (our commutator
    difference is Hermitian: (AB-BA) of two Hermitian-output channel results),
    this equals sum of |eigenvalues|.  We use eigvalsh -- a DISTINCT route from
    the SVD legs."""
    Mh = 0.5 * (M + M.conj().T)
    # The difference of two physical states is Hermitian to machine precision;
    # symmetrize defensively, then sum |eigvals|.
    assert np.allclose(M, Mh, atol=1e-10), "commutator difference not Hermitian"
    ev = np.linalg.eigvalsh(Mh)
    return float(np.sum(np.abs(ev)))


def is_trace_preserving(kraus):
    s = sum(K.conj().T @ K for K in kraus)
    return float(np.max(np.abs(s - I2)))


def choi_min_eig(kraus):
    """Choi matrix C = sum_k |K_k>><<K_k| via row-major vec; PSD iff CP.

    NOTE (by-construction caveat, see by_construction_index): for any list of
    Kraus operators this outer-product sum is PSD by construction (a sum of
    rank-1 PSD terms cannot be indefinite). So this check CANNOT reject a
    non-CP map given a Kraus representation -- it is a structural sanity check,
    not a load-bearing CP discriminator. The genuine CPTP gate is the
    trace-preserving check (sum_k K^dag K == I), which DOES reject (verified:
    [I,I] gives TP error 1.0). We compute the Choi object correctly (row-major
    vec, matching the standard Choi-Jamiolkowski convention) and record its
    min eigenvalue, but do not count Choi-PSD as evidence of CP."""
    d = 2
    C = np.zeros((d * d, d * d), dtype=complex)
    for K in kraus:
        v = K.reshape(-1, 1)            # row-major vec (numpy default)
        C += v @ v.conj().T
    ev = np.linalg.eigvalsh(C)
    return float(np.min(ev.real))


# -- probe states --------------------------------------------------------------
def probe_states():
    plus = 0.5 * np.array([[1, 1], [1, 1]], dtype=complex)         # |+><+|
    mixed = 0.5 * I2
    pole = P0.astype(complex)                                       # |0><0|
    # generic Bloch-interior state: r=(0.4,0.3,0.2)
    r = np.array([0.4, 0.3, 0.2])
    generic = 0.5 * (I2 + r[0] * X + r[1] * Y + r[2] * Z)
    return {"rho0_plus": plus, "mixed": mixed, "pole0": pole, "generic": generic}


# -- noncommutation matrix -----------------------------------------------------
def noncommutation_matrix(lib, rho):
    names = list(lib.keys())
    mat = {}
    for a in names:
        mat[a] = {}
        for b in names:
            ab = apply_channel(lib[a], apply_channel(lib[b], rho))   # A(B(rho))
            ba = apply_channel(lib[b], apply_channel(lib[a], rho))   # B(A(rho))
            mat[a][b] = trace_norm(ab - ba)
    return names, mat


def commuting_noncommuting_split(names, mat):
    commuting, noncommuting = [], []
    for a in names:
        for b in names:
            if a >= b:
                continue
            d = mat[a][b]
            (commuting if d <= TOL else noncommuting).append([a, b, d])
    return commuting, noncommuting


def tomographic_basis():
    """d^2 = 4 linearly independent single-qubit probe states spanning the
    Hermitian operator space (I, X, Y, Z directions). delta(A,B,rho)=0 on a
    SINGLE probe only proves rho lies in the kernel of the commutator
    superoperator [L_A, L_B]; MAP-LEVEL commutation ([L_A,L_B]=0) requires
    delta=0 on a tomographically complete set. We use |+> (X), |+i> (Y),
    |0> (Z+), |1> (Z-): these 4 are linearly independent and span the 2x2
    Hermitian/trace-1 affine space."""
    plus = 0.5 * np.array([[1, 1], [1, 1]], dtype=complex)        # |+><+|  (+X)
    plus_i = 0.5 * np.array([[1, -1j], [1j, 1]], dtype=complex)   # |+i><+i| (+Y)
    zero = P0.astype(complex)                                      # |0><0|  (+Z)
    one = P1.astype(complex)                                       # |1><1|  (-Z)
    return {"plus_X": plus, "plus_Y": plus_i, "zero_Z": zero, "one_Z": one}


def map_level_commutation(lib):
    """For every unordered pair, the MAP-LEVEL commutation witness:
    max_delta_over_basis = max over a tomographically complete probe basis of
    delta(A,B,rho). Map-level commute iff this max is ~0. This separates:
      * structural (map-level) zeros: max ~ 0 on ALL probes,
      * probe-specific (state-null) zeros: ~0 on rho0 but > 0 on some probe
        (the maps genuinely do NOT commute as superoperators).
    Fixes the state-null conflation: classifying on a single probe (rho0) can
    label a genuinely noncommuting pair 'commuting'."""
    basis = tomographic_basis()
    names = list(lib.keys())
    rho0 = 0.5 * np.array([[1, 1], [1, 1]], dtype=complex)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d_rho0 = trace_norm(
                apply_channel(lib[a], apply_channel(lib[b], rho0))
                - apply_channel(lib[b], apply_channel(lib[a], rho0))
            )
            max_d = 0.0
            for rho in basis.values():
                d = trace_norm(
                    apply_channel(lib[a], apply_channel(lib[b], rho))
                    - apply_channel(lib[b], apply_channel(lib[a], rho))
                )
                max_d = max(max_d, d)
            map_level_commutes = bool(max_d <= TOL)
            probe_specific_zero = bool(d_rho0 <= TOL and max_d > TOL)
            rows.append({
                "pair": [a, b],
                "delta_rho0": d_rho0,
                "max_delta_over_basis": max_d,
                "map_level_commutes": map_level_commutes,
                "rho0_zero_but_map_noncommutes": probe_specific_zero,
            })
    n_map_commuting = sum(1 for r in rows if r["map_level_commutes"])
    n_probe_specific = sum(1 for r in rows if r["rho0_zero_but_map_noncommutes"])
    return {
        "basis": list(basis.keys()),
        "basis_note": "tomographically complete (d^2=4 linearly independent states)",
        "pairs": rows,
        "n_map_level_commuting": n_map_commuting,
        "n_rho0_commuting": sum(1 for r in rows if r["delta_rho0"] <= TOL),
        "n_probe_specific_zeros": n_probe_specific,
    }


def main():
    src = open(os.path.abspath(__file__), "rb").read()
    lib = kraus_library()
    names = list(lib.keys())

    # ---- CPTP validity --------------------------------------------------------
    cptp = {}
    for nm, K in lib.items():
        tp_err = is_trace_preserving(K)
        cp_min = choi_min_eig(K)
        cptp[nm] = {
            "trace_preserving_err": tp_err,
            "choi_min_eig": cp_min,
            "is_cptp": bool(tp_err < CPTP_TOL and cp_min > -CPTP_TOL),
        }
    all_cptp = all(v["is_cptp"] for v in cptp.values())

    probes = probe_states()

    # ---- headline matrix on rho0 = |+><+| ------------------------------------
    rho0 = probes["rho0_plus"]
    _, mat0 = noncommutation_matrix(lib, rho0)
    commuting0, noncommuting0 = commuting_noncommuting_split(names, mat0)

    # symmetry + diagonal structural checks (by-construction, recorded as checks)
    diag_all_zero = all(mat0[a][a] <= TOL for a in names)
    symmetric = all(abs(mat0[a][b] - mat0[b][a]) <= TOL for a in names for b in names)

    # ---- per-probe matrices ---------------------------------------------------
    per_probe = {}
    for pname, rho in probes.items():
        _, m = noncommutation_matrix(lib, rho)
        per_probe[pname] = {a: {b: m[a][b] for b in names} for a in names}

    # ---- discriminator (a): commuting pairs (DERIVED) ------------------------
    # Ti vs projector_pinch (equal action) and Fe vs Ti (z-rot commutes z-deph).
    disc_a = {
        "Ti_vs_projector_pinch": mat0["Ti_z_dephasing"]["projector_pinch"],
        "Fe_vs_Ti": mat0["Fe_z_rotation"]["Ti_z_dephasing"],
        "Fe_vs_projector_pinch": mat0["Fe_z_rotation"]["projector_pinch"],
    }
    # ---- discriminator (b): genuinely noncommuting pairs ON rho0 (DERIVED) ----
    # Lindblad_vs_Te is REMOVED from the genuine set: delta(La,Te) = GAMMA for
    # ALL rho (probe-independent, equals the parameter) -- a by-construction
    # nonzero, recorded in by_construction_index, not as a discovered effect.
    disc_b = {
        "Fe_vs_Te": mat0["Fe_z_rotation"]["Te_x_dephasing"],
        "Fe_vs_Fi": mat0["Fe_z_rotation"]["Fi_x_rotation"],
        "Lindblad_vs_Fi": mat0["Lindblad_amp_damp"]["Fi_x_rotation"],
    }
    # Lindblad_vs_Te recorded separately as a by-construction constant (= GAMMA).
    lindblad_vs_te_by_construction = mat0["Lindblad_amp_damp"]["Te_x_dephasing"]
    # ---- discriminator (b2): probe-relative Ti-Fi (DERIVED per probe) ---------
    disc_b2 = {p: per_probe[p]["Ti_z_dephasing"]["Fi_x_rotation"] for p in probes}
    # ---- discriminator (c): antisymmetric signed structure -------------------
    # signed witness on the GENERIC probe (where Ti-Fi genuinely noncommutes);
    # Tr(Y D) is real, signed, and flips sign under (a,b) swap.
    def signed_offdiag(a, b, rho):
        ab = apply_channel(lib[a], apply_channel(lib[b], rho))
        ba = apply_channel(lib[b], apply_channel(lib[a], rho))
        D = ab - ba
        return float(np.real(np.trace(Y @ D)))
    sc_ab = signed_offdiag("Ti_z_dephasing", "Fi_x_rotation", probes["generic"])
    sc_ba = signed_offdiag("Fi_x_rotation", "Ti_z_dephasing", probes["generic"])
    disc_c = {
        "signed_TiFi": sc_ab,
        "signed_FiTi": sc_ba,
        "antisymmetric": bool(abs(sc_ab + sc_ba) <= TOL and abs(sc_ab) > TOL),
    }

    # ---- discriminator (d): classical diagonal baseline collapses ------------
    # diagonal-map sub-block on a classical (diagonal) state.
    classical_maps = ["Ti_z_dephasing", "projector_pinch", "Lindblad_amp_damp", "Fe_z_rotation"]
    rho_cl = np.array([[0.7, 0], [0, 0.3]], dtype=complex)  # classical mixture
    sub = {nm: lib[nm] for nm in classical_maps}
    _, mcl = noncommutation_matrix(sub, rho_cl)
    classical_pairs = [[a, b, mcl[a][b]] for a in classical_maps for b in classical_maps if a < b]
    classical_gap_max = max((p[2] for p in classical_pairs), default=0.0)
    # contrast: re-open the gap by including a coherence map on the SAME classical state
    open_map_delta = noncommutation_matrix(
        {"Ti_z_dephasing": lib["Ti_z_dephasing"], "Fi_x_rotation": lib["Fi_x_rotation"]}, rho_cl
    )[1]["Ti_z_dephasing"]["Fi_x_rotation"]

    # ---- control: identity map commutes with everything -----------------------
    idK = identity_kraus()
    id_deltas = {}
    for nm in names:
        ab = apply_channel(idK, apply_channel(lib[nm], rho0))
        ba = apply_channel(lib[nm], apply_channel(idK, rho0))
        id_deltas[nm] = trace_norm(ab - ba)
    identity_commutes_all = all(d <= TOL for d in id_deltas.values())

    # ---- MAP-LEVEL commutation (tomographically complete basis) --------------
    # Fixes the state-null conflation (fleet glm-5.1): classify commutation by
    # the MAX delta over a d^2 probe basis, not delta on rho0 alone.
    map_commute = map_level_commutation(lib)

    # ---- by-construction index (explicit honesty labels) ----------------------
    # Every entry below is an algebraic identity / tautology that holds for ALL
    # inputs (or for ALL probe states). These are recorded as STRUCTURAL checks,
    # NOT as discovered noncommutation evidence. Confirmed by direct sweep.
    by_construction_index = {
        "choi_psd_is_tautology": {
            "statement": "Choi C = sum_k vec(K_k) vec(K_k)^dag is PSD for ANY Kraus list (sum of rank-1 PSD terms). The Choi-PSD check CANNOT reject a non-CP map. The trace-preserving check (sum K^dag K == I) is the only load-bearing CPTP gate.",
            "load_bearing_for_CP": False,
        },
        "diag_self_zero": {
            "statement": "delta[A][A] = ||A(A(rho)) - A(A(rho))||_1 = 0 (a map commutes with itself).",
            "holds_for_all": True,
        },
        "matrix_symmetric": {
            "statement": "delta[A][B] = delta[B][A] because ||M||_1 = ||-M||_1 (the commutator difference is antisymmetric in the ordering).",
            "holds_for_all": True,
        },
        "identity_commutes_all": {
            "statement": "delta[id][X] = 0 for every X (id(X(rho)) = X(id(rho)) = X(rho)).",
            "holds_for_all": True,
        },
        "Lindblad_vs_Te_equals_GAMMA_for_all_rho": {
            "statement": "delta(Lindblad_amp_damp, Te_x_dephasing, rho) = GAMMA for EVERY rho (commutator difference = diag(GAMMA/2, -GAMMA/2), probe-independent). This is a by-construction NONZERO: the value equals the damping parameter GAMMA, not a probe-discovered order effect. It is moved OUT of the genuine discriminators.",
            "value_is_parameter": GAMMA,
            "probe_independent": True,
        },
        "structural_zero_pairs_map_level": {
            "statement": "These pairs commute as SUPEROPERATORS (max delta over the d^2 basis ~ 0) for algebraic reasons predictable without simulation; they are confirmations of known algebra, not discoveries.",
            "Fe_vs_Ti": "Rz and z-dephasing are both diagonal in the Z eigenbasis -> commute for all rho.",
            "Ti_vs_projector_pinch": "identical channel action (rho -> diag(rho)) -> commute for all rho.",
            "Fe_vs_projector_pinch": "Rz (Z-diagonal) commutes with the Z-pinch for all rho.",
            "Fe_vs_Lindblad": "Rz multiplies off-diagonals by a phase; amplitude damping multiplies off-diagonals by a magnitude; scalar multiplications commute -> all rho.",
            "Fi_vs_Te": "Rx = exp(-i*theta*X/2) and x-basis dephasing are both functions of X -> commute for all rho and all theta.",
            "Ti_vs_Te": "both map |+> to I/2 on rho0; map-level they share no coherence channel that distinguishes ordering on the basis (max delta ~ 0).",
            "Te_vs_projector_pinch": "Te symmetrizes to I/2 where the Z-pinch fixes diagonal; max delta over basis ~ 0.",
        },
        "probe_specific_zeros_on_rho0": {
            "statement": "These pairs are ~0 on rho0=|+> (a state-null zero: |+> lies in the kernel of the commutator) but NONZERO on other basis probes -> they do NOT commute as maps. Reported separately from map-level commuting pairs.",
            "pairs": [r["pair"] for r in map_commute["pairs"] if r["rho0_zero_but_map_noncommutes"]],
            "reason_TiFi": "Ti(|+>) = I/2, and any unitary Fi fixes I/2, so delta=0 on |+>; on |0> (pole) Fi creates coherence that Ti dephases order-dependently -> delta = 0.866.",
        },
        "disc_b2_rho0_mixed_zeros_by_construction": {
            "statement": "Ti-Fi delta = 0 on rho0=|+> and on I/2 are by-construction fixed-point zeros (Ti(|+>)=I/2 is a fixed point of all unitaries; I/2 is a fixed point of both maps). The GENUINE probe-relativity evidence is the NONZERO on pole0 (0.866) and generic (0.312).",
            "genuine_probe_relative_evidence": ["pole0", "generic"],
        },
    }

    # ---- control: label-shuffle invariance -----------------------------------
    # relabel names -> recompute -> matrix invariant under the inverse relabel.
    perm = {names[i]: names[(i + 1) % len(names)] for i in range(len(names))}
    shuffled_lib = {perm[k]: lib[k] for k in names}
    _, mat_sh = noncommutation_matrix(shuffled_lib, rho0)
    # map shuffled value back to original label pair and compare
    label_shuffle_max_diff = 0.0
    for a in names:
        for b in names:
            v_orig = mat0[a][b]
            v_sh = mat_sh[perm[a]][perm[b]]
            label_shuffle_max_diff = max(label_shuffle_max_diff, abs(v_orig - v_sh))
    label_shuffle_invariant = label_shuffle_max_diff <= TOL

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "numpy",
        "computation_style": "dense_2x2_kraus_eigvalsh_tracenorm",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": hashlib.sha256(src).hexdigest(),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_numpy_results.json",
        "params": {"THETA": THETA, "PHI": PHI, "GAMMA": GAMMA, "TOL": TOL},
        "map_names": names,
        "cptp_validity": cptp,
        "all_maps_cptp": all_cptp,
        "delta_matrix_rho0": {a: {b: mat0[a][b] for b in names} for a in names},
        "diag_all_zero": diag_all_zero,
        "matrix_symmetric": symmetric,
        "commuting_pairs_rho0": commuting0,
        "noncommuting_pairs_rho0": noncommuting0,
        "n_commuting": len(commuting0),
        "n_noncommuting": len(noncommuting0),
        "per_probe_delta_matrix": per_probe,
        "discriminator_a_commuting": disc_a,
        "discriminator_b_noncommuting": disc_b,
        "lindblad_vs_te_by_construction_equals_gamma": lindblad_vs_te_by_construction,
        "discriminator_b2_probe_relative_TiFi": disc_b2,
        "discriminator_c_signed_antisymmetric": disc_c,
        "map_level_commutation": map_commute,
        "by_construction_index": by_construction_index,
        "discriminator_d_classical_baseline": {
            "classical_maps": classical_maps,
            "classical_state_diag": [0.7, 0.3],
            "classical_pairs": classical_pairs,
            "classical_gap_max": classical_gap_max,
            "classical_gap_collapses": bool(classical_gap_max <= TOL),
            "coherence_map_reopens_gap_on_same_state": open_map_delta,
            "gap_reopens": bool(open_map_delta > TOL),
        },
        "control_identity_map": {
            "id_deltas": id_deltas,
            "identity_commutes_all": identity_commutes_all,
        },
        "control_label_shuffle": {
            "max_diff": label_shuffle_max_diff,
            "invariant": label_shuffle_invariant,
        },
        "TOOL_MANIFEST": {
            "numpy": {"tried": True, "used": True, "reason": "dense Kraus action + eigvalsh trace norm (reference)"},
        },
        "aligned_tools_load_bearing": ["numpy"],
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_numpy_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"numpy leg wrote {out}")
    print(f"  all_maps_cptp={all_cptp}  symmetric={symmetric}  diag_all_zero={diag_all_zero}")
    print(f"  commuting={len(commuting0)} noncommuting={len(noncommuting0)}")
    print(f"  disc_a(commuting)={disc_a}")
    print(f"  disc_b(noncommuting)={disc_b}")
    print(f"  classical_gap_max={classical_gap_max:.3e}  reopens={open_map_delta:.3e}")
    print(f"  identity_commutes_all={identity_commutes_all}  label_shuffle_invariant={label_shuffle_invariant}")
    print(f"  MAP-LEVEL: rho0_commuting={map_commute['n_rho0_commuting']} "
          f"map_level_commuting={map_commute['n_map_level_commuting']} "
          f"probe_specific_zeros(rho0~0 but map-noncommute)={map_commute['n_probe_specific_zeros']}")
    print(f"  Lindblad_vs_Te (by-construction = GAMMA)={lindblad_vs_te_by_construction:.6f}")


if __name__ == "__main__":
    main()
