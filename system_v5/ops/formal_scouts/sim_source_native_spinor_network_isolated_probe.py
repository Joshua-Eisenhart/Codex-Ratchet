#!/usr/bin/env python3
"""Isolated sim: source-native finite spinor network layer.

Layer (geometric constraint manifold): represent the manifold fabric as finite
left/right spinor states and finite edge/cut compatibility, before any downstream
readout. Sims this ONE layer alone; no stacking/bridge.

Math verbatim from the owner's spec:
  psi_v,s in C^2, ||psi_v,s||=1, rho_v,s = psi_v,s psi_v,s^dag, s in {L,R}
  edge compatibility w_uv = f(node states), 0 <= w_uv <= 1
  two-site cut state rho_uv in D(C^2 (x) C^2), Tr=1, rho_uv >= 0
  cut readouts: reduced/entanglement entropy, mutual information, negativity

Entropy is the manifold here: the cut readouts ARE the layer's content.
  S(rho) = -Tr(rho log rho);  S_u = S(Tr_v rho_uv)        (entanglement, pure cut)
  I(u:v) = S_u + S_v - S_uv                                (mutual information)
  negativity N = sum of |negative eigenvalues of rho_uv^{T_v}|  (PPT, quantum corr)

Controls (each must change the readout, measurably):
  - replace edge by a PRODUCT state          -> I(u:v) = 0, N = 0
  - erase phases (dephase the cut)           -> N -> 0 (quantum gone), classical I stays
  - dense random global state (no provenance)-> generically entangled, unlike product
  - randomize node states                    -> compatibility w changes

Load-bearing tool: sympy proves entropy additivity for products, S(A(x)B)=S(A)+S(B),
which forces a product cut to have I=0; the measured product I is checked against it.

classification: tool_lego_fit_probe (isolated; promotion_allowed=False)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

rng = np.random.default_rng(5)


def rand_psi():
    z = rng.normal(size=4)
    v = np.array([z[0] + 1j * z[1], z[2] + 1j * z[3]])
    return v / np.linalg.norm(v)


def rho1(psi):
    return np.outer(psi, np.conj(psi))


def S(rho):
    w = np.clip(np.linalg.eigvalsh(rho).real, 1e-15, None)
    return float(-(w * np.log(w)).sum())


def ptrace_v(rho4):                      # trace out the second qubit -> rho_u
    return np.einsum("ijkj->ik", rho4.reshape(2, 2, 2, 2))


def ptrace_u(rho4):                      # trace out the first qubit  -> rho_v
    return np.einsum("ijil->jl", rho4.reshape(2, 2, 2, 2))


def mutual_information(rho4):
    return S(ptrace_v(rho4)) + S(ptrace_u(rho4)) - S(rho4)


def negativity(rho4):                    # PPT: sum |negative eigs of partial transpose|
    pt = rho4.reshape(2, 2, 2, 2).transpose(0, 3, 2, 1).reshape(4, 4)
    ev = np.linalg.eigvalsh(0.5 * (pt + pt.conj().T)).real
    return float(-ev[ev < 0].sum())


def hbin(p):
    if p <= 0 or p >= 1:
        return 0.0
    return -(p * math.log(p) + (1 - p) * math.log(1 - p))


def sympy_product_additivity():
    """Load-bearing: S(diag(p,1-p) (x) diag(q,1-q)) = H(p) + H(q), so a product
    cut has zero mutual information. The measured product I is checked vs this."""
    import sympy as sp
    p, q = sp.symbols("p q", positive=True)
    eigs = [p * q, p * (1 - q), (1 - p) * q, (1 - p) * (1 - q)]
    S_ab = -sum(e * sp.log(e) for e in eigs)
    S_a = -(p * sp.log(p) + (1 - p) * sp.log(1 - p))
    S_b = -(q * sp.log(q) + (1 - q) * sp.log(1 - q))
    additive = bool(sp.simplify(sp.expand_log(S_ab - (S_a + S_b), force=True)) == 0)
    return {"product_entropy_additive": additive, "implies_product_mutual_info_zero": additive}


def main():
    theta = math.pi / 5

    # entangled pure cut: |Phi> = cos t |00> + sin t |11>
    phi = np.array([math.cos(theta), 0, 0, math.sin(theta)], dtype=complex)
    rho_ent = np.outer(phi, np.conj(phi))

    # product cut: rho_u (x) rho_v
    pu, pv = rand_psi(), rand_psi()
    rho_prod = np.kron(rho1(pu), rho1(pv))

    # phase-erased (dephased) entangled cut: kill coherences -> classical mixture
    rho_deph = np.diag(np.diag(rho_ent))

    # dense random global pure 2-qubit state (no local provenance)
    zc = rng.normal(size=8); pv4 = (zc[:4] + 1j * zc[4:]); pv4 /= np.linalg.norm(pv4)
    rho_dense = np.outer(pv4, np.conj(pv4))

    readouts = {}
    for name, r in [("entangled", rho_ent), ("product", rho_prod),
                    ("dephased", rho_deph), ("dense", rho_dense)]:
        readouts[name] = {"S_u": S(ptrace_v(r)), "S_v": S(ptrace_u(r)),
                          "S_uv": S(r), "mutual_information": mutual_information(r),
                          "negativity": negativity(r)}

    # node compatibility weight w = |<psi_u|psi_v>|^2 ; aligned vs orthogonal vs random
    e0 = np.array([1, 0], dtype=complex)
    e1 = np.array([0, 1], dtype=complex)
    w_aligned = float(abs(np.vdot(e0, e0)) ** 2)
    w_orth = float(abs(np.vdot(e0, e1)) ** 2)
    w_random = float(abs(np.vdot(rand_psi(), rand_psi())) ** 2)

    # local densities valid (Tr=1, PSD)
    nodes = [rho1(rand_psi()) for _ in range(6)]
    dens_valid = all(abs(np.trace(n).real - 1) < 1e-12
                     and np.linalg.eigvalsh(n).real.min() > -1e-12 for n in nodes)

    sym = sympy_product_additivity()
    schmidt_pred = hbin(math.cos(theta) ** 2)   # S_u of |Phi> = H(cos^2 t)

    # robustness: the measured Schmidt entropy must match H(cos^2 t) across a sweep of t
    def schmidt_entropy(t):
        v = np.array([math.cos(t), 0, 0, math.sin(t)], dtype=complex)
        return S(ptrace_v(np.outer(v, np.conj(v))))
    thetas = [0.2, 0.5, math.pi / 5, 1.0, 1.3]
    schmidt_sweep_ok = all(abs(schmidt_entropy(t) - hbin(math.cos(t) ** 2)) < 1e-9 for t in thetas)

    # couple sympy to runtime: the additivity identity must hold on the MEASURED product cut
    additivity_on_measured = abs(S(rho_prod) - (S(ptrace_v(rho_prod)) + S(ptrace_u(rho_prod)))) < 1e-9
    # cut states must be valid densities (Tr=1, PSD) so entropy isn't computed on garbage
    cut_states_valid = all(abs(np.trace(r).real - 1) < 1e-9
                           and np.linalg.eigvalsh(0.5 * (r + r.conj().T)).real.min() > -1e-12
                           for r in [rho_ent, rho_prod, rho_deph, rho_dense])

    verdicts = {
        "local_densities_valid": dens_valid,
        "cut_states_valid": cut_states_valid,
        "sympy_additivity_holds_on_measured_product": additivity_on_measured,
        "entangled_mutual_info_positive": readouts["entangled"]["mutual_information"] > 0.5,
        "product_mutual_info_zero": readouts["product"]["mutual_information"] < 1e-9,
        # measured entanglement entropy matches H(cos^2 t) across a sweep of t (robust)
        "entanglement_entropy_matches_schmidt_sweep": schmidt_sweep_ok,
        "negativity_detects_entanglement": readouts["entangled"]["negativity"] > 0.1
            and readouts["product"]["negativity"] < 1e-9,
        # phase erasure kills the QUANTUM correlation but keeps CLASSICAL correlation
        "phase_erasure_kills_quantum_keeps_classical": readouts["dephased"]["negativity"] < 1e-9
            and readouts["dephased"]["mutual_information"] > 0.3,
        # dense closure has no product structure -> generically correlated
        "dense_closure_differs_from_product": readouts["dense"]["mutual_information"] > 0.1,
        "compatibility_responds_to_states": w_aligned > 0.99 and w_orth < 1e-12 and w_random != w_aligned,
        "sympy_product_additivity_zero_MI": sym["implies_product_mutual_info_zero"],
    }

    result = {
        "name": "source_native_spinor_network_isolated",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "layer": "source-native finite spinor network",
        "finite_map": "SpinorNetworkStep: (nodes psi_v,s, edges rho_uv, weights w_e) -> cut readouts S/I/negativity",
        "domain": "finite spinor network: node densities in D(C^2), edge cut states in D(C^2 (x) C^2)",
        "codomain_or_output": "entanglement entropy, mutual information, negativity per cut; compatibility weights",
        "root_constraints": {"F01": "finite nodes/edges, dim-2 carriers",
                             "N01": "edge cut states carry noncommuting two-site correlations; product vs entangled is the order-free vs order-bearing distinction"},
        "native_scale": {"n_nodes": 6, "n_cut_types": 4, "qubit_dim": 2},
        "dynamic_step": "cut readouts evolve with the edge state; controls re-evaluate the cut",
        "cut_readouts": readouts,
        "schmidt_prediction_H_cos2theta": schmidt_pred,
        "compatibility_weights": {"aligned": w_aligned, "orthogonal": w_orth, "random": w_random},
        "load_bearing_sympy": sym,
        "verdicts": verdicts,
        "all_pass": all(verdicts.values()),
        "blocked_consumers": ["stacking", "order_tests", "Xi", "Phi0", "Axis0", "flux", "FEP", "physics"],
        "tool_manifest": {
            "numpy": {"used": True, "reason": "claim-bearing cut states, partial trace/transpose, entanglement measures"},
            "sympy": {"used": True, "reason": "load-bearing: proves product entropy additivity -> product cut has zero MI"},
        },
        "tool_integration_depth": "load_bearing",
    }

    result["negative_controls"] = {"product_cut_MI": readouts["product"]["mutual_information"],
                                   "dephased_cut_negativity": readouts["dephased"]["negativity"],
                                   "dense_cut_MI": readouts["dense"]["mutual_information"]}
    import contract_emit, torch
    _w = torch.linalg.eigvalsh(torch.tensor(ptrace_v(rho_ent), dtype=torch.complex128)).real.clamp(min=1e-15)
    contract_emit.attach(result, {"entangled_vs_product_mutual_info":
        (readouts["entangled"]["mutual_information"], readouts["product"]["mutual_information"])},
        "native QIT cut scale (qubit-pair cuts, theta sweep); 8/16/32/64 qubit ladder N/A.",
        torch_primary=float(-(_w * torch.log(_w)).sum()))

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "source_native_spinor_network_isolated_results.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"all_pass={result['all_pass']}  ({sum(verdicts.values())}/{len(verdicts)} verdicts)")
    for k, v in verdicts.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print("\ncut readouts (I = mutual info, N = negativity):")
    for n, r in readouts.items():
        print(f"  {n:10s} S_u={r['S_u']:.3f} S_uv={r['S_uv']:.3f} I={r['mutual_information']:.3f} N={r['negativity']:.3f}")
    print(f"schmidt S_u prediction H(cos^2 t)={schmidt_pred:.3f}  measured={readouts['entangled']['S_u']:.3f}")
    print(f"compatibility w: aligned={w_aligned} orth={w_orth} random={w_random:.3f}")
    print(f"sympy product additivity -> zero MI: {sym['implies_product_mutual_info_zero']}")
    print(f"result -> {out_path}")


if __name__ == "__main__":
    main()
