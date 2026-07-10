#!/usr/bin/env python3
"""umegaki_pawl_is_finite_modular_theory_sim -- ties the FORCED side of the model to Tomita-Takesaki modular theory.
Shows the Umegaki relative entropy S(rho||sigma) -- the ONE genuinely forced anchor of the octonion-fork arc (the
monotone pawl of UP-107/115) -- IS the finite case of the relative modular operator:
    S(rho||sigma) = -<xi_rho, log(Delta_{sigma|rho}) xi_rho>,   Delta_{sigma|rho}=L_sigma R_rho^{-1},  xi_rho=vec(rho^{1/2})
This reproduces the codex-ratchet araki_modular_umegaki_crosscheck_sim independently and connects it to the
surface-identity work (the terrain entropy/geometry face is the BKM information metric = Connes-Rovelli thermal time;
project canon surface_identity_is_BKM / surface_identity_prior_art). The relative modular operator Delta is exactly the
finite-dimensional Tomita-Takesaki modular structure, so the forced Umegaki pawl and the surface-identity thermal-time
structure are the SAME modular object seen from two angles.

Owner: "deep work the foundations and consider all the new math we have covered."

WHY THIS IS ON THE FORCED SIDE (unlike UP-119, which built unforced exceptional structure). The Umegaki relative
entropy is the forced terrain-native ratcheting pawl: monotone to the terrain's own fixed point under its Axis-5
T-operator (UP-107, project canon coratchet_entropy_is_terrain_native), and the one anchor UP-115 identified as
genuinely earned by {F01,N01} rather than living on the {H,O} branch. Modular theory is likewise established prior art
(Tomita-Takesaki; Araki's relative entropy; Connes-Rovelli thermal time). So this rung does NOT claim new forcing --
it shows the forced pawl already IS a piece of modular theory, tightening the model's own internal consistency.

COMPUTED (all from linear algebra on vectorized M_2(C), 4-dim):
  1. CONVENTION/CLASSICAL GATE: for a diagonal pair rho=diag(.7,.3), sigma=diag(.4,.6), the modular formula equals the
     KL divergence to ~1e-16, with Delta eigenvalues {4/7, 6/7, 4/3, 2} (the ratios sigma_i/rho_j).
  2. NON-COMMUTING QUANTUM GATE (stronger than the classical case, the real content): for random non-commuting
     density pairs, the modular formula equals the direct Umegaki Tr[rho(log rho - log sigma)] to ~1e-14. This is the
     genuine Tomita-Takesaki identity; for commuting pairs it would reduce trivially to KL.
  3. BLOCH-BALL COVERAGE GATE: on a representative set of density matrices spanning the Bloch ball (NOT loaded from any
     terrain sim -- an inline coverage set), the modular formula agrees with direct Umegaki to ~1e-15, confirming the
     identity holds across the state space the engine's density matrices live in. (This does NOT claim these are the
     engine's actual terrain fixed points; it is a coverage check, not a terrain-provenance claim.)

CONTROLS (falsifiable):
  - SWAPPED-DELTA (wrong convention L_rho R_sigma^{-1}): mismatches the KL by ~0.37, so the identity is specific to the
    correct relative modular operator, not any vectorized product.
  - SINGULAR SIGMA (sigma=diag(1,0), not full rank): Delta is not invertible / log Delta ill-defined -> the identity is
    correctly flagged ill-defined without regularization (matching S(rho||sigma)=+inf when supp(rho) not subset supp(sigma)).

scratch_diagnostic, promotion_allowed=false. FORCED-side consistency result (no NEW forcing claim); reproduces codex
araki_modular_umegaki_crosscheck independently.
"""
import json, sys
import numpy as np
from scipy.linalg import logm, sqrtm

def vec(A): return A.reshape(-1,order='F')
def Lm(A): return np.kron(np.eye(A.shape[0]),A)
def Rm(A): return np.kron(A.T,np.eye(A.shape[0]))
def umegaki(rho,sig): return float(np.real(np.trace(rho@(logm(rho)-logm(sig)))))
def araki(rho,sig):
    if np.min(np.real(np.linalg.eigvalsh(sig)))<1e-12:
        return None, None, "ill_defined_singular_sigma"
    Delta=Lm(sig)@np.linalg.inv(Rm(rho)); xi=vec(sqrtm(rho))
    val=-float(np.real(np.vdot(xi, logm(Delta)@xi)))
    eig=np.sort(np.real(np.linalg.eigvals(Delta)))
    return val, eig, "finite"

def main():
    rng=np.random.default_rng(1)
    def randrho():
        A=rng.standard_normal((2,2))+1j*rng.standard_normal((2,2)); M=A@A.conj().T; return M/np.trace(M)
    # 1. classical convention gate
    rho=np.diag([0.7,0.3]).astype(complex); sig=np.diag([0.4,0.6]).astype(complex)
    a,eig,st=araki(rho,sig); kl=0.7*np.log(0.7/0.4)+0.3*np.log(0.3/0.6)
    g_classical=bool(st=="finite" and abs(a-kl)<1e-12)
    # 2. non-commuting quantum gate (the real content)
    qmax=0.0
    for _ in range(12):
        r,s=randrho(),randrho(); ar,_,stt=araki(r,s)
        if stt=="finite": qmax=max(qmax,abs(ar-umegaki(r,s)))
    g_quantum=bool(qmax<1e-11)
    # 3. Bloch-ball coverage gate: representative density matrices spanning the Bloch ball (an inline coverage set,
    #    NOT loaded from any terrain sim), modular == direct Umegaki against a common full-rank reference sigma.
    def bloch(x,y,z): return 0.5*np.array([[1+z,x-1j*y],[x+1j*y,1-z]],complex)
    cover=[bloch(0,0,0.6),bloch(0.5,0,0.2),bloch(0,0.5,-0.3),bloch(0.3,0.3,0.3),
           bloch(0,0,-0.5),bloch(-0.4,0,0.1),bloch(0,-0.4,0.2),bloch(0.2,-0.2,-0.2)]
    ref=bloch(0.05,0.05,0.1)  # common full-rank reference
    tmax=0.0
    for t in cover:
        ar,_,stt=araki(t,ref)
        if stt=="finite": tmax=max(tmax,abs(ar-umegaki(t,ref)))
    g_coverage=bool(tmax<1e-10)
    # controls
    Dsw=Lm(rho)@np.linalg.inv(Rm(sig)); xi=vec(sqrtm(rho))
    asw=-float(np.real(np.vdot(xi,logm(Dsw)@xi)))
    g_swap=bool(abs(asw-kl)>1e-3)
    _,_,st_sing=araki(np.diag([0.6,0.4]).astype(complex), np.diag([1.0,0.0]).astype(complex))
    g_singular=bool(st_sing=="ill_defined_singular_sigma")
    verdict=bool(g_classical and g_quantum and g_coverage and g_swap and g_singular)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,"branch":"forced_side_consistency",
         "reproduces":"system_v7/constraint_core/sims_and_scripts/araki_modular_umegaki_crosscheck_sim.py (codex-ratchet)",
         "identity":"S(rho||sigma) = -<vec(sqrt(rho)), log(L_sigma R_rho^{-1}) vec(sqrt(rho))> = Umegaki relative entropy = finite Tomita-Takesaki",
         "classical_gate":{"araki":a,"kl":kl,"abs_diff":abs(a-kl),"delta_eigenvalues":list(eig),"pass":g_classical},
         "quantum_noncommuting_gate":{"max_abs_araki_minus_umegaki":qmax,"n_pairs":12,"pass":g_quantum,
             "note":"the real content -- the modular identity holds for NON-commuting rho,sigma, not just the classical/diagonal (KL) case"},
         "bloch_ball_coverage_gate":{"max_abs_modular_minus_umegaki":tmax,"n_density_matrices":len(cover),"pass":g_coverage,
             "note":"coverage check over representative density matrices spanning the Bloch ball (an inline set, NOT the engine's actual terrain fixed points); confirms the identity across the state space, not a terrain-provenance claim"},
         "controls":{"swapped_delta_mismatch":abs(asw-kl),"swapped_nonmatching":g_swap,
             "singular_sigma_status":st_sing,"singular_flagged_ill_defined":g_singular},
         "placement":"FORCED-side consistency: the Umegaki pawl (UP-107/115, the one genuinely forced anchor) IS the finite relative modular operator (Tomita-Takesaki). Connects to the surface-identity work (terrain entropy/geometry face = BKM metric = Connes-Rovelli thermal time). No NEW forcing claim; tightens internal consistency between the forced pawl and the thermal-time surface identity.",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("THE UMEGAKI PAWL IS THE FINITE CASE OF MODULAR THEORY (reproduces codex araki_modular_umegaki_crosscheck)\n")
    print(f"  identity: S(rho||sigma) = -<vec(sqrt rho), log(L_sigma R_rho^-1) vec(sqrt rho)>  (finite Tomita-Takesaki)")
    print(f"  CLASSICAL gate: araki {a:.15f} == KL {kl:.15f} (abs diff {abs(a-kl):.1e}); Delta eigs {list(np.round(eig,4))} -> {g_classical}")
    print(f"  QUANTUM (non-commuting) gate: max |araki - Umegaki| over 12 random pairs = {qmax:.1e} -> {g_quantum} (the real content)")
    print(f"  BLOCH-ball coverage gate: max |modular - Umegaki| over {len(cover)} density matrices = {tmax:.1e} -> {g_coverage}")
    print(f"  CONTROL swapped-delta: mismatch from KL {abs(asw-kl):.4f} (nonmatching {g_swap})")
    print(f"  CONTROL singular sigma: {st_sing} (flagged ill-defined {g_singular})")
    print(f"\n  PLACEMENT: FORCED-side consistency -- the forced Umegaki pawl IS finite modular theory, connecting to the")
    print(f"  surface-identity (BKM / Connes-Rovelli thermal-time) work. No new forcing; internal consistency tightened.")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (classical + non-commuting quantum + Bloch-ball coverage + both controls)")
    if verdict: print("PASS umegaki_pawl_is_finite_modular_theory")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
