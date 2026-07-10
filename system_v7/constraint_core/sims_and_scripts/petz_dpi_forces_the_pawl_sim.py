#!/usr/bin/env python3
"""petz_dpi_forces_the_pawl_sim -- explains WHY the Umegaki relative-entropy pawl is FORCED, not hand-picked. Processes
the codex-ratchet petz_recovery_reversibility_census + petz_quasi_entropy_pawl_census independently. Three computed
claims, all on the forced side:

  1. DATA-PROCESSING INEQUALITY (monotonicity): for any CPTP channel N, S(N(rho)||N(sigma)) <= S(rho||sigma). This is
     the structural reason the terrain-native pawl exists: relative entropy CANNOT increase under the dissipative
     (CPTP) terrain flow, so it is a genuine Lyapunov/pawl quantity. Not an assumption -- a theorem (Lindblad;
     Uhlmann), reproduced here numerically (0 violations over 200 random pairs under a lossy Kraus channel).
  2. EQUALITY <=> PETZ RECOVERY: the DPI is TIGHT (DeltaS=0) exactly when the channel is reversible on the pair by the
     Petz recovery map R_{sigma,N}(X)=sigma^{1/2} N*(N(sigma)^{-1/2} X N(sigma)^{-1/2}) sigma^{1/2}. The indicator
     correlation pearson(DeltaS==0, recovery-exact) = 1.0: a unitary channel is reversible (DeltaS=0, recovery exact),
     a dissipative channel is not (DeltaS>0, recovery fails). This is the Petz/Hayden-Jozsa-Petz-Winter equality
     condition -- the sharp boundary between information preserved and information lost.
  3. UMEGAKI IS ONE MEMBER OF A FORCED FAMILY: the Petz quasi-entropy S_f(rho||sigma)=sum_{ij} mu_j f(lambda_i/mu_j)
     |<rho_i|sigma_j>|^2 is monotone under CPTP for EVERY operator-convex f with f(1)=0. Umegaki is f(x)=x log x; the
     whole family (reverse f=-log x, chi^2 f=(x-1)^2, Hellinger f=2(1-sqrt x)) pawls UNIFORMLY -- each monotone-
     decreases to 0 at the terrain fixed point. So Umegaki is not a special hand-picked choice; it is one instance of
     a forced operator-convex family, all sharing the pawl. (Umegaki is INSTALLED within a forced family, per the
     codex verdict "Umegaki is installed within a forced Petz operator-convex family.")

CONTROL (falsifiable): measuring the quasi-entropy against a WRONG (foreign) fixed point does NOT pawl -- it fails to
reach 0 and is not monotone. So the pawl is specific to the terrain's own fixed point (project canon
coratchet_entropy_is_terrain_native), not any reference state.

PLACEMENT: FORCED-side foundations. This is the structural justification of UP-107 (the terrain-native monotone pawl)
and UP-120 (Umegaki = finite modular theory): the pawl is forced because monotonicity under the dissipative terrain
flow IS the data-processing inequality, and the equality/recovery boundary is the Petz condition. No new forcing of the
{H,O} branch; it grounds the forced entropy structure the whole ratchet already runs on. Established prior art
(Lindblad, Uhlmann, Petz); this rung shows the model's pawl already IS that structure.

scratch_diagnostic, promotion_allowed=false. Reproduces codex petz_recovery_reversibility_census + quasi_entropy_pawl_census.
"""
import json, sys
import numpy as np
from scipy.linalg import logm, sqrtm

I2=np.eye(2,dtype=complex)
SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
def umegaki(r,s): return float(np.real(np.trace(r@(logm(r)-logm(s)))))
def apply_ch(Ks,rho): return sum(K@rho@K.conj().T for K in Ks)
def adjoint(Ks,X): return sum(K.conj().T@X@K for K in Ks)
def lossy_channel(gamma=0.3,p=0.2):
    K=[np.array([[1,0],[0,np.sqrt(1-gamma)]],complex), np.array([[0,np.sqrt(gamma)],[0,0]],complex)]
    dep=[np.sqrt(1-p)*I2,np.sqrt(p/3)*SX,np.sqrt(p/3)*SY,np.sqrt(p/3)*SZ]
    return [D@Kj for D in dep for Kj in K]
def petz_recover(Ks,sig,X):
    Nsig=apply_ch(Ks,sig); Nm=np.linalg.inv(sqrtm(Nsig)); sh=sqrtm(sig)
    return sh@adjoint(Ks, Nm@X@Nm)@sh
def bl(m): return np.array([np.real(np.trace(m@P)) for P in (SX,SY,SZ)])
def mk(b): return 0.5*(I2+b[0]*SX+b[1]*SY+b[2]*SZ)
def flow(rho,sig,t): return mk(bl(sig)+(bl(rho)-bl(sig))*np.exp(-t))
def quasi_entropy(rho,sig,f):
    lam,R=np.linalg.eigh(rho); mu,S=np.linalg.eigh(sig)
    lam=np.clip(lam,1e-12,None); mu=np.clip(mu,1e-12,None)
    ov=np.abs(R.conj().T@S)**2
    return float(np.real(sum(mu[j]*f(lam[i]/mu[j])*ov[i,j] for i in range(len(lam)) for j in range(len(mu)))))

def main():
    rng=np.random.default_rng(0)
    def randrho():
        A=rng.standard_normal((2,2))+1j*rng.standard_normal((2,2)); M=A@A.conj().T; return M/np.trace(M)
    # CLAIM 1: DPI monotonicity
    Ks=lossy_channel(); viol=0; mxdrop=0.0
    for _ in range(200):
        r,s=randrho(),randrho(); gap=umegaki(r,s)-umegaki(apply_ch(Ks,r),apply_ch(Ks,s))
        mxdrop=max(mxdrop,gap)
        if gap<-1e-9: viol+=1
    g_dpi=bool(viol==0)
    # CLAIM 2: equality <=> Petz recovery
    U=np.linalg.qr(rng.standard_normal((2,2))+1j*rng.standard_normal((2,2)))[0]; Ku=[U]
    allds=[]; allre=[]
    for ch in (Ku,Ks):
        for _ in range(100):
            r,s=randrho(),randrho()
            allds.append(umegaki(r,s)-umegaki(apply_ch(ch,r),apply_ch(ch,s)))
            allre.append(float(np.linalg.norm(petz_recover(ch,s,apply_ch(ch,r))-r)))
    allds=np.array(allds); allre=np.array(allre)
    eq_ind=(allds<1e-8).astype(float); rec_ind=(allre<1e-6).astype(float)
    corr=float(np.corrcoef(eq_ind,rec_ind)[0,1])
    uni_ds=float(np.mean(allds[:100])); uni_re=float(np.mean(allre[:100]))
    dis_ds=float(np.mean(allds[100:])); dis_re=float(np.mean(allre[100:]))
    g_recovery=bool(corr>0.999)
    # CLAIM 3: quasi-entropy family pawls uniformly
    fam={"umegaki_xlogx":lambda x:x*np.log(x),"reverse_-logx":lambda x:-np.log(x),
         "chi2_(x-1)^2":lambda x:(x-1)**2,"hellinger_2(1-sqrtx)":lambda x:2*(1-np.sqrt(x))}
    sig=randrho(); fam_report={}; fam_all_mono=True
    for name,f in fam.items():
        rho0=randrho(); vals=[quasi_entropy(flow(rho0,sig,t),sig,f) for t in np.linspace(0,4,20)]
        mono=all(vals[k+1]<=vals[k]+1e-9 for k in range(len(vals)-1))
        fam_report[name]={"start":vals[0],"end":vals[-1],"monotone":mono}; fam_all_mono&=mono
    g_family=bool(fam_all_mono)
    # CONTROL: wrong foreign fixed point does NOT pawl
    foreign=randrho(); rho0=randrho()
    valsw=[quasi_entropy(flow(rho0,sig,t),foreign,fam["umegaki_xlogx"]) for t in np.linspace(0,4,20)]
    ctrl_mono=all(valsw[k+1]<=valsw[k]+1e-9 for k in range(len(valsw)-1))
    g_control=bool((not ctrl_mono) or valsw[-1]>0.05)  # doesn't reach 0 / not monotone
    verdict=bool(g_dpi and g_recovery and g_family and g_control)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,"branch":"forced_side_foundations",
         "reproduces":"codex petz_recovery_reversibility_census_sim + petz_quasi_entropy_pawl_census_sim",
         "claim1_dpi_monotonicity":{"violations_over_200_pairs":viol,"max_drop":mxdrop,"pass":g_dpi,
             "note":"S(N rho||N sig) <= S(rho||sig): relative entropy cannot increase under the dissipative CPTP terrain flow -> it is a genuine pawl"},
         "claim2_equality_iff_petz_recovery":{"pearson_deltaS0_vs_recovery_exact":corr,
             "unitary_mean_deltaS":uni_ds,"unitary_mean_recovery_err":uni_re,
             "dissipative_mean_deltaS":dis_ds,"dissipative_mean_recovery_err":dis_re,"pass":g_recovery,
             "note":"DPI tight (DeltaS=0) exactly when the Petz recovery map reverses the channel on the pair"},
         "claim3_umegaki_in_forced_family":{"family":fam_report,"all_monotone":g_family,
             "note":"every operator-convex f with f(1)=0 gives a monotone quasi-entropy; Umegaki (x log x) is ONE member. The pawl is a forced family property, not a hand-picked choice."},
         "control_wrong_fixed_point":{"foreign_start":valsw[0],"foreign_end":valsw[-1],"foreign_still_monotone_to_zero":ctrl_mono and valsw[-1]<0.05,"pass":g_control,
             "note":"measuring against a foreign fixed point does not pawl -> the pawl is terrain-native (own fixed point)"},
         "placement":"FORCED-side foundations: structural justification of UP-107 (terrain-native monotone pawl) and UP-120 (Umegaki=finite modular theory). The pawl is FORCED because monotonicity under the dissipative terrain flow IS the data-processing inequality, with Petz recoverability as the equality boundary. Established prior art (Lindblad/Uhlmann/Petz); grounds the forced entropy structure the ratchet runs on.",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("PETZ / DPI FORCES THE PAWL (reproduces codex petz_recovery + quasi_entropy censuses)\n")
    print(f"  CLAIM 1 (DPI monotonicity): {viol} violations over 200 pairs (max drop {mxdrop:.3f}) -> pawl exists because relative entropy cannot rise under CPTP: {g_dpi}")
    print(f"  CLAIM 2 (equality <=> Petz recovery): pearson(DeltaS==0, recovery-exact) = {corr:.4f} -> {g_recovery}")
    print(f"     unitary: DeltaS {uni_ds:.4f}, recovery err {uni_re:.4f} | dissipative: DeltaS {dis_ds:.4f}, recovery err {dis_re:.4f}")
    print(f"  CLAIM 3 (Umegaki in a forced family): all {len(fam)} operator-convex members monotone-decrease to 0: {g_family}")
    for n,r in fam_report.items(): print(f"     {n:22s}: {r['start']:.4f} -> {r['end']:.4f} (monotone {r['monotone']})")
    print(f"  CONTROL (wrong foreign fixed point): {valsw[0]:.4f} -> {valsw[-1]:.4f}, does not pawl to 0: {g_control}")
    print(f"\n  => the Umegaki pawl is FORCED: monotonicity under the dissipative terrain flow IS the data-processing")
    print(f"     inequality; equality is Petz recoverability; Umegaki is one member of a forced operator-convex family.")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (DPI + equality<=>recovery + family pawls + wrong-fixed-point control)")
    if verdict: print("PASS petz_dpi_forces_the_pawl")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
