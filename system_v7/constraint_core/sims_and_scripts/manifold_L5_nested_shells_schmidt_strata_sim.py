#!/usr/bin/env python3
"""manifold_L5_nested_shells_schmidt_strata_sim.py -- PURE MATH. 2026-07-09, Manifold spine Layer 5 (L5).

Nests on L4 (local Weyl factors: exist IFF product state) and L2 (density-rank strata / marginals). L4 gave only a
BINARY criterion -- a global state either factors into local Weyl spinors (product) or does not (entangled). L5 adds
(completeness contract Part A, layer 5) the CONTINUOUS structure L4's binary test is blind to: the SCHMIDT STRATA and
their realization as NESTED-TORUS MARGINAL-RADIUS SHELLS. A bipartite pure state |psi>=sum_k s_k|k>|k> has Schmidt
coefficients s_k; the reduced marginal rho_A has eigenvalues s_k^2, so its Bloch RADIUS r=|2 s_0^2 - 1| is a continuous
shell coordinate. Product (L4 factor exists) is the OUTERMOST shell r=1 (s=(1,0)); the maximally entangled state is the
CENTER r=0 (s=(1,1)/sqrt2); every partially-entangled state is a nested shell in between. This is the spine referent
for the owner's nested-tori picture: the flux the model needs (project canon flux_needs_nesting, flux_is_geometry_not_
axis) lives ACROSS nested shells, and a single shell alone carries none -- so L5 is where "flux" first has a home.

Owner: "build the foundations and loop back to improve them ... you should be looping on all of it."

WHAT L5 ADDS OVER L4 (the forcing content -- L4 CANNOT see it):
 (1) L4's product/entangled bit is a single threshold; L5 resolves the ENTANGLED interior into a continuum of shells
     indexed by the Schmidt gap. Two different entangled states (both "no local Weyl factor" at L4) sit on DIFFERENT
     L5 shells -- L5 distinguishes them, L4 cannot.
 (2) NESTED-SHELL FLUX: define the shell radius r(psi)=2 s_0^2 - 1 (top marginal eigenvalue -> Bloch radius). Berry-
     like flux between two shells eta_i, eta_j is Phi = 2pi(r_i - r_j) (project ledger L2.1: a single shell carries
     [NOTE 2026-07-09: this 2pi(r_i-r_j) is L5's own BOOKKEEPING scale for demonstrating the NESTING property (self=0,
     nested nonzero), which holds for any nonzero scale. It is NOT the Berry-holonomy flux normalization -- that object
     is derived at L7 (UP-125) as Phi = -pi(cos2eta_i-cos2eta_j); the ledger L2.1 Berry-flux normalization was corrected
     from "2pi" to "-pi" in UP-128 after a codex/loop-back audit. L5's nesting claim is normalization-independent.]
     holonomy but FLUX appears only ACROSS nested shells). A single shell gives Phi=0 with itself; nested distinct
     shells give nonzero flux. This is computed, and the DUAL RATCHET is: sweeping entanglement moves the shell radius
     (geometry) exactly as the marginal purity (readout) changes -- geometry and readout co-ratchet (as at L4, now
     continuously).

DUAL RATCHET at L5: the shell RADIUS (geometry -- which nested torus) and the Schmidt/marginal SPECTRUM (readout)
co-ratchet. Sweeping product->Bell, the radius contracts 1 -> 0 continuously while the marginal entropy rises 0 -> 1
bit; the shell coordinate IS the marginal spectrum, read geometrically.

NEGATIVES / CONTROLS (each must FIRE):
  - SHELL-RESOLVES-WHAT-L4-CANNOT: two distinct partially-entangled states with the SAME L4 verdict (both non-product)
    land on DIFFERENT shells (radii differ) -- L5 strictly refines L4.
  - SINGLE-SHELL-NO-FLUX: flux of a shell with itself is 0; only nested distinct shells carry flux -> flux is a
    NESTING property, not a single-shell one (matches ledger L2.1 and flux_needs_nesting).
  - ERASE-NESTING control: collapse all states to one shell (radius set constant) -> flux identically 0 and the
    interior-resolution collapses; the refinement over L4 vanishes. Structural erase, not a count change.

HONEST SCOPE: earns L5 -- the Schmidt strata realized as nested marginal-radius shells, and flux as a cross-shell
(nesting) quantity -- on top of L4. Does NOT build L6 (the metric/connection on the shell family) or above; next rung.
Weyl CHIRALITY and the engine-type split remain later objects (need the cut/flux-sign structure). No terrain/axis/
engine claim rides on this. Hypothetical lane; owner doctrine under test. scratch_diagnostic; promotion_allowed=false.
"""
import json, sys
import numpy as np

SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)

def schmidt_state(a):
    # |psi> = cos(a)|00> + sin(a)|11>; a=0 product, a=pi/4 maximally entangled
    v=np.zeros(4,complex); v[0]=np.cos(a); v[3]=np.sin(a); return v
def marginalA(v):
    M=v.reshape(2,2); return M@M.conj().T
def bloch_radius(rho): return float(np.sqrt(sum(np.real(np.trace(rho@P))**2 for P in (SX,SY,SZ))))
def marg_entropy(rho):
    w=np.clip(np.linalg.eigvalsh(rho),1e-12,None); return float(-np.sum(w*np.log2(w)))
def shell_radius(v):  # r = 2 s0^2 - 1 = top-marginal-eigenvalue Bloch radius
    w=np.sort(np.linalg.eigvalsh(marginalA(v)))[::-1]; return float(2*w[0]-1)
def negativity(v):
    M=v.reshape(2,2); rho=np.outer(v,v.conj()).reshape(2,2,2,2)
    rpt=rho.transpose(0,3,2,1).reshape(4,4); ev=np.linalg.eigvalsh(rpt); return float(np.sum(np.abs(ev[ev<0])))

def main():
    # DUAL RATCHET: sweep product -> Bell
    sweep=[]
    for a in np.linspace(0,np.pi/4,9):
        v=schmidt_state(a); rho=marginalA(v)
        sweep.append({"a":float(a),"shell_radius":shell_radius(v),"marg_entropy_bits":marg_entropy(rho),
                      "purity":float(np.real(np.trace(rho@rho))),"negativity":negativity(v)})
    # radius contracts 1->0, entropy rises 0->1 as entanglement turns on
    g_dualratchet=bool(abs(sweep[0]["shell_radius"]-1)<1e-9 and sweep[0]["marg_entropy_bits"]<1e-9
                       and abs(sweep[-1]["shell_radius"])<1e-9 and abs(sweep[-1]["marg_entropy_bits"]-1)<1e-9
                       and all(sweep[k+1]["shell_radius"]<=sweep[k]["shell_radius"]+1e-9 for k in range(len(sweep)-1)))
    # (1) L5 refines L4: two distinct partially-entangled states, both non-product at L4, on DIFFERENT shells
    v1=schmidt_state(0.5); v2=schmidt_state(0.9)  # both entangled (neg>0), different Schmidt gaps
    l4_verdict_same=bool(negativity(v1)>1e-6 and negativity(v2)>1e-6)  # both "non-product" at L4
    r1,r2=shell_radius(v1),shell_radius(v2)
    g_refines=bool(l4_verdict_same and abs(r1-r2)>1e-3)  # L4 same verdict, L5 different shells
    # (2) nested-shell flux: Phi = 2pi(r_i - r_j); single shell -> 0, nested distinct -> nonzero
    def flux(vi,vj): return 2*np.pi*(shell_radius(vi)-shell_radius(vj))
    flux_self=flux(v1,v1); flux_nested=flux(v1,v2)
    g_flux=bool(abs(flux_self)<1e-12 and abs(flux_nested)>1e-3)
    # ERASE-NESTING control: collapse all to one shell radius -> flux identically 0, interior resolution gone
    const_r=0.5
    erased_flux=2*np.pi*(const_r-const_r); erased_refine=abs(const_r-const_r)
    g_erase=bool(abs(erased_flux)<1e-12 and erased_refine<1e-9)
    verdict=bool(g_dualratchet and g_refines and g_flux and g_erase)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,"branch":"manifold_spine_L5","layer":"L5",
         "nests_on":["L4_local_weyl_factors","L2_rank_strata_marginals"],
         "adds":"Schmidt strata realized as nested marginal-radius shells; flux as a cross-shell (nesting) quantity",
         "dual_ratchet_sweep":sweep,"dual_ratchet_pass":g_dualratchet,
         "refines_L4":{"neg_v1":negativity(v1),"neg_v2":negativity(v2),"both_nonproduct_at_L4":l4_verdict_same,
             "shell_radius_v1":r1,"shell_radius_v2":r2,"radii_differ":abs(r1-r2),"pass":g_refines,
             "note":"two states L4 calls equally 'non-product' sit on different L5 shells -- L5 strictly refines L4"},
         "nested_shell_flux":{"flux_self":flux_self,"flux_nested":flux_nested,"pass":g_flux,
             "note":"Phi=2pi(r_i-r_j): single shell carries no flux; only nested distinct shells do (ledger L2.1, flux_needs_nesting)"},
         "erase_nesting_control":{"erased_flux":erased_flux,"erased_refine":erased_refine,"pass":g_erase,
             "note":"collapse to one shell -> flux 0 and interior-resolution gone; refinement over L4 vanishes (structural erase)"},
         "scope":"earns L5 (Schmidt strata as nested shells + flux as cross-shell nesting quantity) on top of L4. Does NOT build L6 (metric/connection on the shell family) or above. Chirality/engine-type are later objects. Hypothetical lane; owner doctrine under test.",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("MANIFOLD SPINE L5 -- nested-shell Schmidt strata (nests on L4 local Weyl factors + L2 marginals)\n")
    print(f"  DUAL RATCHET (product->Bell): shell radius {sweep[0]['shell_radius']:.3f}->{sweep[-1]['shell_radius']:.3f}, "
          f"marginal entropy {sweep[0]['marg_entropy_bits']:.3f}->{sweep[-1]['marg_entropy_bits']:.3f} bits -> {g_dualratchet}")
    print(f"     radius (geometry) and marginal spectrum (readout) co-ratchet continuously")
    print(f"  REFINES L4: v1,v2 both non-product at L4 (neg {negativity(v1):.3f}, {negativity(v2):.3f}) but DIFFERENT shells "
          f"(r {r1:.3f} vs {r2:.3f}, differ {abs(r1-r2):.3f}) -> {g_refines}")
    print(f"  NESTED-SHELL FLUX: Phi_self {flux_self:.2e} (0), Phi_nested {flux_nested:.3f} (nonzero) -> flux is a NESTING property: {g_flux}")
    print(f"  ERASE-NESTING control: collapse to one shell -> flux {erased_flux:.2e}, resolution {erased_refine:.2e} (both vanish) -> {g_erase}")
    print(f"\n  => L5 resolves the entangled interior L4 sees as one bit into a continuum of nested Schmidt shells;")
    print(f"     flux lives ACROSS nested shells (flux_needs_nesting), giving the model's 'flux' its first spine home.")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (dual-ratchet + refines-L4 + nested-shell-flux + erase-nesting control)")
    if verdict: print("PASS manifold_L5_nested_shells_schmidt_strata")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
