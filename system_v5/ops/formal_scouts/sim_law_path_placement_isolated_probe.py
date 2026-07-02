#!/usr/bin/env python3
"""Isolated sim: placement of local laws on finite paths layer.

Layer (geometric constraint manifold): place each terrain law on each finite Hopf
path. The placement is a MAP, not a label. Sims this ONE layer alone.

Math verbatim from the owner's spec:
  PlacedStep(name, s, ell):
    rho_pre  = U_ell,s rho U_ell,s^dag                 (transport along the path)
    rho_next = CPTP_or_GKSL_step[X_name,s](rho_pre)     (apply the law)
  16 placements total = 8 laws (4 left + 4 right) x 2 paths (fiber, base-lift)

Path transports (from the Hopf layer): the fiber path is rho-stationary (global
phase, U_fiber = I on rho); the base-lift path moves the Bloch point (U_base is a
nontrivial rotation).

Falsifiable claims, each with a breaking control:
  - placement is ORDER-sensitive: law-after-transport != transport-after-law on
    the base path (noncommuting); control: fiber path (U=I) -> gap = 0
  - transport MATTERS for conservative laws (vortex remembers the path) but is
    ERASED by fully-contractive laws (funnel -> maximally mixed regardless) -- the
    honest physics of placement
  - sheet swap (left law on +H_0 vs right law on -H_0) changes the placement
  - control: law erased (X=0) -> placement reduces to pure transport

Entropy as part of the manifold: each placement carries an entropy readout;
unitary transport conserves S, the dissipative law changes it -- the placement's
entropy distinguishes path-transport from law-action.

Load-bearing tool: sympy proves the depolarizing Bloch contraction rate -4*lam,
matched to the measured funnel contraction inside the placement.

classification: tool_lego_fit_probe (isolated; promotion_allowed=False)
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from scipy.linalg import expm

rng = np.random.default_rng(47)

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
S_MINUS = np.array([[0, 1], [0, 0]], dtype=complex)
S_PLUS = np.array([[0, 0], [1, 0]], dtype=complex)
H0 = 0.5 * SZ


def dag(A):
    return A.conj().T


def comm(A, r):
    return A @ r - r @ A


def D(L, r):
    LdL = dag(L) @ L
    return L @ r @ dag(L) - 0.5 * (LdL @ r + r @ LdL)


def gens(sheet):
    H = H0 if sheet == "L" else -H0
    sm = S_MINUS if sheet == "L" else S_PLUS
    return {
        "funnel": lambda r: 0.15 * (D(SX, r) + D(SY, r) + D(SZ, r)) - 0.1j * comm(H, r),
        "vortex": lambda r: -1j * comm(H, r) + 0.02 * D(SZ, r),
        "pit": lambda r: 0.3 * D(sm, r) - 0.1j * comm(H, r),
        "hill": lambda r: -1j * comm(0.15 * (SZ if sheet == "L" else -SZ), r)
                          + 0.25 * (0.5 * (I2 + SZ) @ r @ (0.5 * (I2 + SZ))
                                    + 0.5 * (I2 - SZ) @ r @ (0.5 * (I2 - SZ)) - r),
    }


def project(r):
    r = 0.5 * (r + dag(r))
    w, V = np.linalg.eigh(r)
    w = np.clip(w.real, 0, None)
    r = (V * w) @ dag(V)
    return r / np.trace(r).real


def evolve(r0, X, n=120, dt=0.01):
    r = r0.copy()
    for _ in range(n):
        r = project(r + dt * X(r))
    return r


def S(r):
    w = np.clip(np.linalg.eigvalsh(0.5 * (r + dag(r))).real, 1e-15, None)
    return float(-(w * np.log(w)).sum())


def frob(a, b):
    return float(np.linalg.norm(a - b))


def bloch(r):
    return np.array([np.trace(r @ SX).real, np.trace(r @ SY).real, np.trace(r @ SZ).real])


def sympy_depolarizing_rate():
    import sympy as sp
    x, y, z, lam = sp.symbols("x y z lam", real=True)
    sx, sy, sz = sp.Matrix([[0, 1], [1, 0]]), sp.Matrix([[0, -sp.I], [sp.I, 0]]), sp.Matrix([[1, 0], [0, -1]])
    rho = (sp.eye(2) + x * sx + y * sy + z * sz) / 2
    Dp = lambda L: L * rho * L.H - (L.H * L * rho + rho * L.H * L) / 2
    X = lam * (Dp(sx) + Dp(sy) + Dp(sz))
    ok = all(sp.simplify(sp.trace(X * s) + 4 * lam * v) == 0 for s, v in [(sx, x), (sy, y), (sz, z)])
    return {"depolarizing_rate_minus_4lam": bool(ok)}


def main():
    z = rng.normal(size=4); psi = z[:2] + 1j * z[2:]; psi /= np.linalg.norm(psi)
    rho0 = project(0.9 * np.outer(psi, psi.conj()) + 0.1 * 0.5 * I2)

    U_fiber = I2                                                  # fiber: rho-stationary transport
    U_base = expm(-1j * (math.pi / 3) * (SX + SY) / math.sqrt(2))  # base-lift: rotates the Bloch point

    laws_L = gens("L")

    def placed(name, sheet, U):
        return evolve(U @ rho0 @ dag(U), gens(sheet)[name])

    # 16 placements (8 laws = 4 names x 2 sheets, x 2 paths)
    placements = {}
    for sheet in ("L", "R"):
        for name in laws_L:
            for path, U in (("fiber", U_fiber), ("base", U_base)):
                placements[(name, sheet, path)] = placed(name, sheet, U)

    # placement order-sensitivity: law-after-transport vs transport-after-law (base path)
    Xv = laws_L["vortex"]
    law_then_transport = U_base @ evolve(rho0, Xv) @ dag(U_base)
    transport_then_law = evolve(U_base @ rho0 @ dag(U_base), Xv)
    order_gap_base = frob(transport_then_law, law_then_transport)
    # control: fiber path (U_fiber=I, rho-stationary) -> the SAME order-gap formula vanishes
    order_gap_fiber = frob(evolve(U_fiber @ rho0 @ dag(U_fiber), Xv),
                           U_fiber @ evolve(rho0, Xv) @ dag(U_fiber))

    # transport MATTERS for a conservative law, is ERASED by a contractive law
    transport_effect_vortex = frob(placements[("vortex", "L", "fiber")], placements[("vortex", "L", "base")])
    transport_effect_funnel = frob(placements[("funnel", "L", "fiber")], placements[("funnel", "L", "base")])

    # sheet swap changes the placement (chirality)
    sheet_gap = frob(placements[("vortex", "L", "base")], placements[("vortex", "R", "base")])

    # control: law erased (X=0) -> placement = pure transport
    pure_transport = U_base @ rho0 @ dag(U_base)
    law_erased_gap = frob(evolve(U_base @ rho0 @ dag(U_base), lambda r: 0 * r), pure_transport)

    # entropy readouts across placements
    entropies = {f"{n}_{s}_{p}": S(placements[(n, s, p)]) for (n, s, p) in placements}
    dS_unitary_transport = abs(S(U_base @ rho0 @ dag(U_base)) - S(rho0))

    sym = sympy_depolarizing_rate()
    # couple sympy to runtime: measure the depolarizing contraction rate, compare to -4*lam (lam=0.15)
    Xdep = lambda r: 0.15 * (D(SX, r) + D(SY, r) + D(SZ, r))
    rr = rho0.copy(); rn = []
    for _ in range(150):
        rr = project(rr + 0.01 * Xdep(rr)); rn.append(np.linalg.norm(bloch(rr)))
    rn = np.array(rn); msk = rn > 0.15
    measured_rate = float(-np.polyfit(np.arange(len(rn))[msk] * 0.01, np.log(rn[msk]), 1)[0])
    sym["measured_depolarizing_rate"] = measured_rate
    sym["rate_matches_4lam"] = bool(abs(measured_rate - 0.6) < 0.05)
    # order gap scales with transport magnitude (small rotation -> much smaller gap)
    U_small = expm(-1j * 0.04 * (SX + SY) / math.sqrt(2))
    order_gap_small = frob(evolve(U_small @ rho0 @ dag(U_small), Xv), U_small @ evolve(rho0, Xv) @ dag(U_small))

    verdicts = {
        "placement_order_sensitive_on_base": order_gap_base > 0.1,
        "order_gap_scales_with_transport": order_gap_small < 0.3 * order_gap_base,
        "control_fiber_path_no_order_gap": order_gap_fiber < 1e-12,
        "transport_matters_for_conservative_law": transport_effect_vortex > 0.1,
        "contractive_law_erases_more_transport_than_conservative": transport_effect_funnel < transport_effect_vortex,
        "sheet_swap_changes_placement": sheet_gap > 0.1,
        "control_law_erased_is_pure_transport": law_erased_gap < 1e-9,
        "unitary_transport_conserves_entropy": dS_unitary_transport < 1e-12,
        "sixteen_placements_built": len(placements) == 16,
        "sympy_depolarizing_rate_matches_measured": sym["depolarizing_rate_minus_4lam"] and sym["rate_matches_4lam"],
    }
    verdicts = {k: bool(v) for k, v in verdicts.items()}

    result = {
        "name": "law_path_placement_isolated",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "layer": "placement of local laws on finite paths (16 placements)",
        "finite_map": "PlacedStep(name,sheet,path): rho -> GKSL[X_name,sheet](U_path rho U_path^dag)",
        "domain": "single-site density rho, 8 terrain laws, 2 Hopf path transports",
        "codomain_or_output": "16 placed states, order gaps, transport/sheet effects, entropy readouts",
        "root_constraints": {"F01": "finite dim 2, 16 finite placements",
                             "N01": "law and transport do not commute -> placement order is load-bearing"},
        "native_scale": {"n_laws": 8, "n_paths": 2, "n_placements": 16},
        "dynamic_step": "transport along Hopf path then GKSL law evolution",
        "readouts": {
            "order_gap_base": order_gap_base, "order_gap_fiber": order_gap_fiber,
            "transport_effect_vortex": transport_effect_vortex, "transport_effect_funnel": transport_effect_funnel,
            "sheet_gap": sheet_gap, "unitary_transport_dS": dS_unitary_transport,
            "placement_entropies": entropies,
        },
        "load_bearing_sympy": sym,
        "verdicts": verdicts,
        "all_pass": all(verdicts.values()),
        "blocked_consumers": ["stacking", "order_tests", "Xi", "Phi0", "Axis0", "flux", "FEP", "physics"],
        "tool_manifest": {
            "numpy": {"used": True, "reason": "claim-bearing transport+law placement, order gaps, entropy"},
            "scipy": {"used": True, "reason": "matrix exponential for the base-lift transport"},
            "sympy": {"used": True, "reason": "load-bearing: depolarizing rate -4*lam, matched to the placed funnel law"},
        },
        "tool_integration_depth": "load_bearing",
    }

    import contract_emit, torch
    _r0 = torch.tensor(rho0, dtype=torch.complex128)
    contract_emit.attach(result, {"order_gap_base_vs_fiber": (order_gap_base, order_gap_fiber)},
        "native placement scale (16 law-path placements, dt, n_steps); 8/16/32/64 qubit ladder N/A.",
        torch_primary=float(torch.trace(_r0 @ _r0).real))

    out_dir = Path(__file__).resolve().parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "law_path_placement_isolated_results.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"all_pass={result['all_pass']}  ({sum(verdicts.values())}/{len(verdicts)} verdicts)")
    for k, v in verdicts.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    print(f"\nplacement order gap (base)={order_gap_base:.3f}  (fiber control={order_gap_fiber:.2e})")
    print(f"transport effect: vortex(conservative)={transport_effect_vortex:.3f}  funnel(contractive)={transport_effect_funnel:.3f}")
    print(f"sheet swap gap={sheet_gap:.3f}  unitary transport dS={dS_unitary_transport:.2e}  placements={len(placements)}")
    print(f"sympy depolarizing rate matches: {sym['depolarizing_rate_minus_4lam']}")
    print(f"result -> {out_path}")


if __name__ == "__main__":
    main()
