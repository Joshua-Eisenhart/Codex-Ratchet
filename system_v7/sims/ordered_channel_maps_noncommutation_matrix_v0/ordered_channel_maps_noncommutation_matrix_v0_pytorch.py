#!/usr/bin/env python3
"""PyTorch leg -- independent recompute via a DISTINCT trace-norm route.

Computation style UNIQUE to this leg: torch complex128 dense Kraus action and
the trace norm computed via the NUCLEAR-NORM API (torch.linalg.matrix_norm(M,
ord='nuc')), which is a different code path from numpy's eigvalsh and jax's
svdvals.  Different framework + different API route => agreement is genuine.

Recomputes delta(A,B,rho)=||A(B(rho)) - B(A(rho))||_1 over the 6-map library,
the four genuine discriminators, and the controls.  Reads no peer result.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

import torch

torch.set_default_dtype(torch.float64)
CDT = torch.complex128

SIM_ID = "ordered_channel_maps_noncommutation_matrix_v0"
HERE = os.path.dirname(os.path.abspath(__file__))
TOL = 1e-9
CPTP_TOL = 1e-12

I2 = torch.eye(2, dtype=CDT)
X = torch.tensor([[0, 1], [1, 0]], dtype=CDT)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDT)
Z = torch.tensor([[1, 0], [0, -1]], dtype=CDT)
H = (X + Z) / (2.0 ** 0.5)
P0 = torch.tensor([[1, 0], [0, 0]], dtype=CDT)
P1 = torch.tensor([[0, 0], [0, 1]], dtype=CDT)

import math
THETA = math.pi / 3
PHI = math.pi / 4
GAMMA = 0.3


def expm2(A):
    return torch.linalg.matrix_exp(A)


def Rx(theta):
    return expm2(-1j * theta * X / 2)


def Rz(phi):
    return expm2(-1j * phi * Z / 2)


def kraus_library():
    K0amp = torch.tensor([[1, 0], [0, math.sqrt(1 - GAMMA)]], dtype=CDT)
    K1amp = torch.tensor([[0, math.sqrt(GAMMA)], [0, 0]], dtype=CDT)
    return {
        "Ti_z_dephasing": [math.sqrt(0.5) * I2, math.sqrt(0.5) * Z],
        "Te_x_dephasing": [math.sqrt(0.5) * I2, math.sqrt(0.5) * (H @ Z @ H)],
        "Fi_x_rotation": [Rx(THETA)],
        "Fe_z_rotation": [Rz(PHI)],
        "projector_pinch": [P0, P1],
        "Lindblad_amp_damp": [K0amp, K1amp],
    }


def apply_channel(kraus, rho):
    out = torch.zeros((2, 2), dtype=CDT)
    for K in kraus:
        out = out + K @ rho @ K.conj().T
    return out


def trace_norm(M):
    """||M||_1 via the NUCLEAR-NORM API (distinct route from eigvalsh / svdvals)."""
    return float(torch.linalg.matrix_norm(M, ord="nuc").real)


def is_trace_preserving(kraus):
    s = sum(K.conj().T @ K for K in kraus)
    return float(torch.max(torch.abs(s - I2)))


def choi_min_eig(kraus):
    # row-major vec (standard Choi). NOTE: Choi-PSD is a tautology for any Kraus
    # list; the trace-preserving check is the load-bearing CPTP gate.
    C = torch.zeros((4, 4), dtype=CDT)
    for K in kraus:
        v = K.reshape(-1, 1)
        C = C + v @ v.conj().T
    ev = torch.linalg.eigvalsh(C)
    return float(torch.min(ev.real))


def tomographic_basis():
    """d^2 = 4 linearly independent probe states for MAP-LEVEL commutation."""
    plus = 0.5 * torch.tensor([[1, 1], [1, 1]], dtype=CDT)
    plus_i = 0.5 * torch.tensor([[1, -1j], [1j, 1]], dtype=CDT)
    zero = P0.clone()
    one = P1.clone()
    return {"plus_X": plus, "plus_Y": plus_i, "zero_Z": zero, "one_Z": one}


def map_level_commutation(lib):
    basis = tomographic_basis()
    names = list(lib.keys())
    rho0 = 0.5 * torch.tensor([[1, 1], [1, 1]], dtype=CDT)
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            d_rho0 = trace_norm(
                apply_channel(lib[a], apply_channel(lib[b], rho0))
                - apply_channel(lib[b], apply_channel(lib[a], rho0)))
            max_d = 0.0
            for rho in basis.values():
                d = trace_norm(
                    apply_channel(lib[a], apply_channel(lib[b], rho))
                    - apply_channel(lib[b], apply_channel(lib[a], rho)))
                max_d = max(max_d, d)
            rows.append({
                "pair": [a, b],
                "delta_rho0": d_rho0,
                "max_delta_over_basis": max_d,
                "map_level_commutes": bool(max_d <= TOL),
                "rho0_zero_but_map_noncommutes": bool(d_rho0 <= TOL and max_d > TOL),
            })
    return {
        "basis": list(basis.keys()),
        "basis_note": "tomographically complete (d^2=4 linearly independent states)",
        "pairs": rows,
        "n_map_level_commuting": sum(1 for r in rows if r["map_level_commutes"]),
        "n_rho0_commuting": sum(1 for r in rows if r["delta_rho0"] <= TOL),
        "n_probe_specific_zeros": sum(1 for r in rows if r["rho0_zero_but_map_noncommutes"]),
    }


def probe_states():
    plus = 0.5 * torch.tensor([[1, 1], [1, 1]], dtype=CDT)
    mixed = 0.5 * I2
    pole = P0.clone()
    r = [0.4, 0.3, 0.2]
    generic = 0.5 * (I2 + r[0] * X + r[1] * Y + r[2] * Z)
    return {"rho0_plus": plus, "mixed": mixed, "pole0": pole, "generic": generic}


def noncommutation_matrix(lib, rho):
    names = list(lib.keys())
    mat = {}
    for a in names:
        mat[a] = {}
        for b in names:
            ab = apply_channel(lib[a], apply_channel(lib[b], rho))
            ba = apply_channel(lib[b], apply_channel(lib[a], rho))
            mat[a][b] = trace_norm(ab - ba)
    return names, mat


def main():
    src = open(os.path.abspath(__file__), "rb").read()
    lib = kraus_library()
    names = list(lib.keys())

    cptp = {}
    for nm, K in lib.items():
        tp = is_trace_preserving(K)
        cp = choi_min_eig(K)
        cptp[nm] = {"trace_preserving_err": tp, "choi_min_eig": cp,
                    "is_cptp": bool(tp < CPTP_TOL and cp > -CPTP_TOL)}
    all_cptp = all(v["is_cptp"] for v in cptp.values())

    probes = probe_states()
    rho0 = probes["rho0_plus"]
    _, mat0 = noncommutation_matrix(lib, rho0)

    commuting0, noncommuting0 = [], []
    for a in names:
        for b in names:
            if a >= b:
                continue
            d = mat0[a][b]
            (commuting0 if d <= TOL else noncommuting0).append([a, b, d])

    diag_all_zero = all(mat0[a][a] <= TOL for a in names)
    symmetric = all(abs(mat0[a][b] - mat0[b][a]) <= TOL for a in names for b in names)

    per_probe = {}
    for pname, rho in probes.items():
        _, m = noncommutation_matrix(lib, rho)
        per_probe[pname] = {a: {b: m[a][b] for b in names} for a in names}

    disc_a = {
        "Ti_vs_projector_pinch": mat0["Ti_z_dephasing"]["projector_pinch"],
        "Fe_vs_Ti": mat0["Fe_z_rotation"]["Ti_z_dephasing"],
        "Fe_vs_projector_pinch": mat0["Fe_z_rotation"]["projector_pinch"],
    }
    # Lindblad_vs_Te removed from genuine set (= GAMMA for all rho, by-construction).
    disc_b = {
        "Fe_vs_Te": mat0["Fe_z_rotation"]["Te_x_dephasing"],
        "Fe_vs_Fi": mat0["Fe_z_rotation"]["Fi_x_rotation"],
        "Lindblad_vs_Fi": mat0["Lindblad_amp_damp"]["Fi_x_rotation"],
    }
    lindblad_vs_te_by_construction = mat0["Lindblad_amp_damp"]["Te_x_dephasing"]
    disc_b2 = {p: per_probe[p]["Ti_z_dephasing"]["Fi_x_rotation"] for p in probes}

    def signed_offdiag(a, b, rho):
        ab = apply_channel(lib[a], apply_channel(lib[b], rho))
        ba = apply_channel(lib[b], apply_channel(lib[a], rho))
        return float(torch.trace(Y @ (ab - ba)).real)
    sc_ab = signed_offdiag("Ti_z_dephasing", "Fi_x_rotation", probes["generic"])
    sc_ba = signed_offdiag("Fi_x_rotation", "Ti_z_dephasing", probes["generic"])
    disc_c = {"signed_TiFi": sc_ab, "signed_FiTi": sc_ba,
              "antisymmetric": bool(abs(sc_ab + sc_ba) <= TOL and abs(sc_ab) > TOL)}

    classical_maps = ["Ti_z_dephasing", "projector_pinch", "Lindblad_amp_damp", "Fe_z_rotation"]
    rho_cl = torch.tensor([[0.7, 0], [0, 0.3]], dtype=CDT)
    sub = {nm: lib[nm] for nm in classical_maps}
    _, mcl = noncommutation_matrix(sub, rho_cl)
    classical_pairs = [[a, b, mcl[a][b]] for a in classical_maps for b in classical_maps if a < b]
    classical_gap_max = max((p[2] for p in classical_pairs), default=0.0)
    open_map_delta = noncommutation_matrix(
        {"Ti_z_dephasing": lib["Ti_z_dephasing"], "Fi_x_rotation": lib["Fi_x_rotation"]}, rho_cl
    )[1]["Ti_z_dephasing"]["Fi_x_rotation"]

    idK = [I2]
    id_deltas = {}
    for nm in names:
        ab = apply_channel(idK, apply_channel(lib[nm], rho0))
        ba = apply_channel(lib[nm], apply_channel(idK, rho0))
        id_deltas[nm] = trace_norm(ab - ba)
    identity_commutes_all = all(d <= TOL for d in id_deltas.values())

    perm = {names[i]: names[(i + 1) % len(names)] for i in range(len(names))}
    shuffled_lib = {perm[k]: lib[k] for k in names}
    _, mat_sh = noncommutation_matrix(shuffled_lib, rho0)
    label_shuffle_max_diff = 0.0
    for a in names:
        for b in names:
            label_shuffle_max_diff = max(label_shuffle_max_diff, abs(mat0[a][b] - mat_sh[perm[a]][perm[b]]))
    label_shuffle_invariant = label_shuffle_max_diff <= TOL

    map_commute = map_level_commutation(lib)
    by_construction_index = {
        "choi_psd_is_tautology": {"statement": "Choi-PSD holds for any Kraus list; not a CP discriminator. TP check is the load-bearing CPTP gate.", "load_bearing_for_CP": False},
        "diag_self_zero": {"statement": "delta[A][A]=0.", "holds_for_all": True},
        "matrix_symmetric": {"statement": "delta[A][B]=delta[B][A] (||M||_1=||-M||_1).", "holds_for_all": True},
        "identity_commutes_all": {"statement": "delta[id][X]=0 for all X.", "holds_for_all": True},
        "Lindblad_vs_Te_equals_GAMMA_for_all_rho": {"statement": "delta(La,Te,rho)=GAMMA for every rho (probe-independent; equals the parameter). Moved out of genuine discriminators.", "value_is_parameter": GAMMA, "probe_independent": True},
        "structural_zero_pairs_map_level": {"statement": "Pairs with max delta over the basis ~0 commute as superoperators by algebra (Fe-Ti, Ti-PP, Fe-PP, Fe-La, Fi-Te, Ti-Te, Te-PP)."},
        "probe_specific_zeros_on_rho0": {"statement": "~0 on rho0 but nonzero on other basis probes -> map-level NONCOMMUTING (state-null kernel on |+>).", "pairs": [r["pair"] for r in map_commute["pairs"] if r["rho0_zero_but_map_noncommutes"]]},
        "disc_b2_rho0_mixed_zeros_by_construction": {"statement": "Ti-Fi=0 on rho0=|+> and I/2 are fixed-point zeros; genuine probe-relativity is the nonzero on pole0/generic.", "genuine_probe_relative_evidence": ["pole0", "generic"]},
    }

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "computation_style": "torch_complex128_kraus_nuclear_norm_tracenorm",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": hashlib.sha256(src).hexdigest(),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_pytorch_results.json",
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
        "control_identity_map": {"id_deltas": id_deltas, "identity_commutes_all": identity_commutes_all},
        "control_label_shuffle": {"max_diff": label_shuffle_max_diff, "invariant": label_shuffle_invariant},
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "torch Kraus action + nuclear-norm API trace norm (distinct route)"},
        },
        "aligned_tools_load_bearing": ["torch"],
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_pytorch_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"pytorch leg wrote {out}")
    print(f"  all_maps_cptp={all_cptp} symmetric={symmetric} commuting={len(commuting0)} noncommuting={len(noncommuting0)}")
    print(f"  disc_b2 (Ti-Fi probe-relative)={disc_b2}")
    print(f"  classical_gap_max={classical_gap_max:.3e} reopens={open_map_delta:.3e}")
    print(f"  MAP-LEVEL: rho0_commuting={map_commute['n_rho0_commuting']} "
          f"map_level_commuting={map_commute['n_map_level_commuting']} "
          f"probe_specific_zeros={map_commute['n_probe_specific_zeros']}")


if __name__ == "__main__":
    main()
