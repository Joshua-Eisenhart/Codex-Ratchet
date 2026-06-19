#!/usr/bin/env python3
"""cut_lattice_schmidt_entropy_v0 -- PyTorch leg (complex-tensor backend).

Independent torch recomputation of the cut lattice + Schmidt strata + per-cut entropy for
n in {2,3,4}, using complex128 tensors and torch.linalg.eigvalsh. No peer reads.
"""

from __future__ import annotations

import itertools
import json
import math
from pathlib import Path

import torch

torch.set_default_dtype(torch.float64)

SIM_ID = "cut_lattice_schmidt_entropy_v0"
ROOT = Path(__file__).resolve().parent
RESULT = ROOT / "results" / f"{SIM_ID}_pytorch_results.json"
EIG_TOL = 1e-9
CDT = torch.complex128


def cuts(n):
    return [A for r in range(1, n) for A in itertools.combinations(range(n), r) if 0 in A]


def basis(n, bits):
    v = torch.zeros(2 ** n, dtype=CDT)
    v[bits] = 1.0
    return v


def product_state(n):
    return basis(n, 0)


def ghz(n):
    v = torch.zeros(2 ** n, dtype=CDT)
    v[0] = 1 / math.sqrt(2)
    v[-1] = 1 / math.sqrt(2)
    return v


def w_state(n):
    v = torch.zeros(2 ** n, dtype=CDT)
    for q in range(n):
        v[1 << q] = 1 / math.sqrt(n)
    return v


def bell_pair_then_zero(n):
    v = torch.zeros(2 ** n, dtype=CDT)
    v[0] = 1 / math.sqrt(2)
    v[(1 << (n - 1)) | (1 << (n - 2))] = 1 / math.sqrt(2)
    return v


def max_entangled_22(n):
    assert n == 4
    v = torch.zeros(16, dtype=CDT)
    for k in range(4):
        v[k * 4 + k] = 0.5
    return v


def _ry(t):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return torch.tensor([[c, -s], [s, c]], dtype=CDT)


def _apply1(psi, n, q, U):
    psi = psi.reshape([2] * n)
    psi = torch.tensordot(U, psi, dims=([1], [q]))
    psi = torch.movedim(psi, 0, q)
    return psi.reshape(-1)


def _apply_cz(psi, n, a, b):
    psi = psi.reshape([2] * n).clone()
    idx = [slice(None)] * n
    idx[a] = 1
    idx[b] = 1
    psi[tuple(idx)] *= -1
    return psi.reshape(-1)


def scramble(n):
    psi = product_state(n)
    th = [0.5 + 0.9 * q for q in range(n)]
    for q in range(n):
        psi = _apply1(psi, n, q, _ry(th[q]))
    for q in range(n):
        psi = _apply_cz(psi, n, q, (q + 1) % n)
    for q in range(n):
        psi = _apply1(psi, n, q, _ry(0.6 + 0.5 * q))
    return psi / torch.linalg.norm(psi)


def rdm(psi, n, A):
    B = [q for q in range(n) if q not in A]
    M = psi.reshape([2] * n).permute(*(list(A) + B)).reshape(2 ** len(A), 2 ** len(B))
    return M @ M.conj().T


def schmidt_rank(rho):
    w = torch.linalg.eigvalsh(rho)
    return int(torch.sum(w > EIG_TOL).item())


def vn_entropy(rho):
    w = torch.linalg.eigvalsh(rho)
    w = w[w > EIG_TOL]
    s = float(-torch.sum(w * torch.log2(w)).item())
    return s + 0.0  # normalize -0.0 -> 0.0 (rank-1 cut: eigenvalue 1 gives -1*log2(1) = -0.0)


def negativity(psi, n, A):
    dA, B = 2 ** len(A), [q for q in range(n) if q not in A]
    dB = 2 ** len(B)
    rho = torch.outer(psi, psi.conj()).reshape([2] * (2 * n))
    perm = list(A) + B + [q + n for q in A] + [q + n for q in B]
    rho = rho.permute(*perm).reshape(dA, dB, dA, dB)
    rho_ta = rho.permute(2, 1, 0, 3).reshape(dA * dB, dA * dB)
    ev = torch.linalg.eigvalsh(rho_ta)
    return float(torch.sum(torch.abs(ev[ev < 0])).item())


def profile(psi, n):
    return {str(A): {"S": vn_entropy(rdm(psi, n, A)),
                     "rank": schmidt_rank(rdm(psi, n, A)),
                     "neg": negativity(psi, n, A)} for A in cuts(n)}


def round_profile(prof, nd=9):
    return {k: round(v["S"], nd) for k, v in prof.items()}


def main() -> int:
    n_cuts = {n: len(cuts(n)) for n in (2, 3, 4)}

    p2 = profile(product_state(2), 2)
    b2 = profile(basis(2, 0) / math.sqrt(2) + basis(2, 3) / math.sqrt(2), 2)
    p3 = profile(product_state(3), 3)
    g3 = profile(ghz(3), 3)
    w3 = profile(w_state(3), 3)
    bp3 = profile(bell_pair_then_zero(3), 3)
    s3 = profile(scramble(3), 3)
    g3S, w3S = round_profile(g3), round_profile(w3)
    ghz_w_gap_n3 = max(abs(g3[c]["S"] - w3[c]["S"]) for c in g3)

    p4 = profile(product_state(4), 4)
    g4 = profile(ghz(4), 4)
    w4 = profile(w_state(4), 4)
    m4 = profile(max_entangled_22(4), 4)
    s4 = profile(scramble(4), 4)
    g4S, w4S = round_profile(g4), round_profile(w4)
    g4_vals = sorted(set(round(v, 6) for v in g4S.values()))
    w4_vals = sorted(set(round(v, 6) for v in w4S.values()))
    n4_max_cut = max(m4[c]["S"] for c in m4)
    n4_max_rank = max(m4[c]["rank"] for c in m4)

    def sym_dev(psi, n):
        dev = 0.0
        full = set(range(n))
        for A in cuts(n):
            B = tuple(sorted(full - set(A)))
            dev = max(dev, abs(vn_entropy(rdm(psi, n, A)) - vn_entropy(rdm(psi, n, B))))
        return dev
    purity_dev = max(sym_dev(ghz(3), 3), sym_dev(w_state(4), 4), sym_dev(scramble(4), 4))

    # NOT load-bearing: S_AB=0 (global pure) makes both reduce to the Schmidt symmetry identity
    # S_A==S_B, which holds for ANY correct pure-state reduction. Consistency check only.
    def mi_ic_consistency(psi, n):
        ok = True
        for A in cuts(n):
            S_A = vn_entropy(rdm(psi, n, A))
            B = tuple(sorted(set(range(n)) - set(A)))
            S_B = vn_entropy(rdm(psi, n, B))
            mi = S_A + S_B
            ic = S_B
            ok = ok and abs(mi - 2 * S_A) < 1e-9 and abs(ic - S_A) < 1e-9
        return ok
    mi_ic_ok = all(mi_ic_consistency(p, n) for p, n in
                   [(ghz(3), 3), (w_state(3), 3), (w_state(4), 4)])

    # A/B subsystem-orientation discriminator: catches a rho_B-instead-of-rho_A swap that the
    # entropy/rank suite is blind to (pure-state Schmidt symmetry: S_A==S_B, rank_A==rank_B).
    # On the unequal cut (|A|=1, |B|=3) of the asymmetric-marginal W4 state, rho_A must be 2x2
    # (a swap returns 8x8) AND its diagonal must equal the axis-0 single-qubit marginal computed
    # independently from |psi|^2 (0.25 on |1>, asymmetric -> not an identity). Could fail.
    def subsystem_orientation_ok():
        psi = w_state(4)
        rho_A = rdm(psi, 4, (0,))
        if tuple(rho_A.shape) != (2, 2):
            return False, None, None
        probs = (psi.abs() ** 2)
        marg_pop1 = float(sum(probs[i].item() for i in range(16) if (i >> (4 - 1)) & 1))
        rdm_pop1 = float(rho_A[1, 1].real.item())
        ok = abs(rdm_pop1 - marg_pop1) < 1e-9 and abs(marg_pop1 - 0.25) < 1e-9
        return ok, round(rdm_pop1, 9), round(marg_pop1, 9)
    orient_ok, orient_rdm_pop1, orient_marg_pop1 = subsystem_orientation_ok()

    invariants = {
        "n_cuts_n2": n_cuts[2], "n_cuts_n3": n_cuts[3], "n_cuts_n4": n_cuts[4],
        "n2_product_max_S": round(max(v["S"] for v in p2.values()), 9),
        "n2_bell_S_cut0": round(b2["(0,)"]["S"], 9),
        "n3_product_max_S": round(max(v["S"] for v in p3.values()), 9),
        "n3_ghz_profile": g3S,
        "n3_w_profile": w3S,
        "n3_ghz_w_max_gap": round(ghz_w_gap_n3, 9),
        "n3_bell_cut0_S": round(bp3["(0,)"]["S"], 9),
        "n3_bell_cut01_S": round(bp3["(0, 1)"]["S"], 9),
        "n4_ghz_uniform": (len(g4_vals) == 1 and abs(g4_vals[0] - 1.0) < 1e-9),
        "n4_w_nonuniform": (len(w4_vals) > 1),
        "n4_w_vals": w4_vals,
        "n4_max_cut_S": round(n4_max_cut, 9),
        "n4_max_cut_rank": n4_max_rank,
        "product_negativity_max": round(max(
            max(v["neg"] for v in p2.values()),
            max(v["neg"] for v in p3.values()),
            max(v["neg"] for v in p4.values())), 9),
        "ghz_negativity_cut0": round(g3["(0,)"]["neg"], 9),
        "purity_symmetry_max_dev": round(purity_dev, 9),
        "scramble_S_cut0_n3": round(s3["(0,)"]["S"], 9),
        "scramble_S_cut0_n4": round(s4["(0,)"]["S"], 9),
        "schmidt_rank_product": max(
            max(v["rank"] for v in p2.values()),
            max(v["rank"] for v in p3.values()),
            max(v["rank"] for v in p4.values())),
        "w4_cut0_marginal_pop1": orient_marg_pop1,
        "w4_cut0_rdm_pop1": orient_rdm_pop1,
    }

    tests = {
        "cut_lattice_count_n2_n3_n4": [n_cuts[2], n_cuts[3], n_cuts[4]] == [1, 3, 7],
        "product_zero_entropy_every_cut": (invariants["n2_product_max_S"] < 1e-9
                                           and invariants["n3_product_max_S"] < 1e-9
                                           and invariants["schmidt_rank_product"] == 1),
        "n3_ghz_all_cuts_one": all(abs(v - 1.0) < 1e-9 for v in g3S.values()),
        "n3_w_all_cuts_log3_form": all(abs(v - (math.log2(3) - 2 / 3)) < 1e-9 for v in w3S.values()),
        "n4_ghz_uniform_one": invariants["n4_ghz_uniform"],
        "n4_w_nonuniform_profile": invariants["n4_w_nonuniform"],
        "max_entangled_cut_hits_log2_dim": abs(invariants["n4_max_cut_S"] - 2.0) < 1e-9
                                           and invariants["n4_max_cut_rank"] == 4,
        "bell_pair_full_on_cut0": abs(invariants["n2_bell_S_cut0"] - 1.0) < 1e-9,
        "subsystem_orientation_no_AB_swap": orient_ok,
    }

    # by-construction pure-state identities -- reported, NOT gating all_tests_pass
    by_construction_identities = {
        "purity_symmetry_SA_eq_SB": invariants["purity_symmetry_max_dev"] < 1e-9,
        "mutual_coherent_pure_identities": mi_ic_ok,
    }

    controls = {
        "product_negativity_zero": invariants["product_negativity_max"] < 1e-9,
        "entangled_vs_separable_divergence": (g3["(0,)"]["S"] - p3["(0,)"]["S"]) > 0.5,
        "ghz_vs_w_profile_divergence": (invariants["n3_ghz_w_max_gap"] > 0.05
                                        and invariants["n4_w_nonuniform"]),
        "bell_pair_cut_dependence": (abs(invariants["n3_bell_cut0_S"] - 1.0) < 1e-9
                                     and invariants["n3_bell_cut01_S"] < 1e-9),
        "scramble_moves_entropy": (invariants["scramble_S_cut0_n3"] > 0.1
                                   and invariants["scramble_S_cut0_n4"] > 0.1),
        "max_cut_hits_ceiling": abs(invariants["n4_max_cut_S"] - 2.0) < 1e-9,
        "ghz_negativity_nonzero": invariants["ghz_negativity_cut0"] > 0.1,
    }
    all_tests = all(tests.values())
    all_controls = all(controls.values())

    result = {
        "schema": "codex_ratchet.sim_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "engine": "pytorch_complex_tensor",
        "root_lineage": {
            "F01_finite_support": True,
            "N01_order_sensitivity": "the cut lattice is the order-of-partition structure; per-cut entropy is a distinguishability readout S/~ over the bipartition, not a forward dynamic",
        },
        "source_target": "manifold-tower L8/L9/L10 cut-lattice + Schmidt strata + per-cut entropy",
        "claim": "the cut lattice of n-qubit pure states (n=2,3,4) admits per-cut Schmidt-rank/entropy/negativity readouts whose STATE-DEPENDENT discriminators hold and could have come out otherwise",
        "support_parameters": {"n_values": [2, 3, 4], "cut_counts": [n_cuts[2], n_cuts[3], n_cuts[4]]},
        "invariants": invariants,
        "tests": tests,
        "by_construction_identities": by_construction_identities,
        "controls": controls,
        "all_tests_pass": all_tests,
        "all_controls_pass": all_controls,
        "ablation_outcome_delta": {
            "product_S_cut0": round(p3["(0,)"]["S"], 9),
            "ghz_S_cut0": round(g3["(0,)"]["S"], 9),
            "delta": round(g3["(0,)"]["S"] - p3["(0,)"]["S"], 9),
        },
        "honest_scope": {
            "earns": "independent PyTorch (complex128) recomputation of the cut lattice / Schmidt strata / per-cut entropy discriminators; tensor backend leg, scratch ceiling",
            "does_not_earn": "M(C), Axis0 closure, QIT engine, smooth manifold, physics; needs cross-engine agreement + fleet audit",
        },
        "TOOL_MANIFEST": {
            "pytorch": {"tried": True, "used": True,
                        "reason": "complex128 state vectors, permute partial trace, torch.linalg.eigvalsh for Schmidt rank + von Neumann entropy + partial-transpose negativity; tensor backend"},
            "python_stdlib": {"tried": True, "used": True,
                              "reason": "finite cut-lattice enumeration, profile bookkeeping"},
        },
        "TOOL_INTEGRATION_DEPTH": "supportive",
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"wrote {RESULT}")
    print(f"all_tests_pass={all_tests} all_controls_pass={all_controls}")
    print(f"n3 GHZ {g3S}  W {w3S}  gap {ghz_w_gap_n3:.6f}")
    print(f"n4 max cut S {n4_max_cut:.9f} rank {n4_max_rank}; product neg {invariants['product_negativity_max']:.2e}")
    return 0 if all_tests and all_controls else 1


if __name__ == "__main__":
    raise SystemExit(main())
