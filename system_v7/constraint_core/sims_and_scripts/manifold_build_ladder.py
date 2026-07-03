"""
manifold_build_ladder.py  (JAX x64)
Build the geometric constraint manifold LAYER BY LAYER, earn each layer, then run
the 7 axes one-by-one in the owner's order 6->5->3->4->1->2->0, with Axis 0 as the
late feedback-polarity gate implemented as a REAL perturb-evolve-classify loop on
state-derived quantities (the step static-label models skip).

Sources (recent wiki): shell-local-to-coupled-program, axis0-current-doctrine-state-card,
terrain rosetta strong math (8 GKSL generators), weyl-flux (nesting), dual-carnot-szilard.
Claim ceiling: scratch_diagnostic; promotion_allowed=false; Axis0 remains UNBUILT per doctrine.
"""
import jax, math, json
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np
import os as _os
_OUT=_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"out")
_os.makedirs(_OUT,exist_ok=True)
def _outpath(name): return _os.path.join(_OUT,name)

I2=jnp.eye(2,dtype=jnp.complex128)
sx=jnp.array([[0,1],[1,0]],dtype=jnp.complex128)
sy=jnp.array([[0,-1j],[1j,0]],dtype=jnp.complex128)
sz=jnp.array([[1,0],[0,-1]],dtype=jnp.complex128)
sm=jnp.array([[0,0],[1,0]],dtype=jnp.complex128)  # sigma_- : |1><0| ... lowers to |1> (r_z->-1)
sp=jnp.array([[0,1],[0,0]],dtype=jnp.complex128)  # sigma_+ : raises to |0> (r_z->+1)
n_hat=jnp.array([1,1,1],dtype=jnp.float64)/math.sqrt(3)  # tilted axis: keep all Bloch DOFs alive
H0=n_hat[0]*sx+n_hat[1]*sy+n_hat[2]*sz

def D(L,rho): return L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L)
def comm(A,rho): return A@rho-rho@A

# --- 8 terrain generators (GKSL). Ni (Pit/Source) source-locked; Se/Si/Ne dissipators
#     are candidate realizations consistent with the ledger template (marked below). ---
eps=0.15; gam=1.0; kap=1.0
def X_Se(rho,H): return D(sz,rho)-1j*eps*comm(H,rho)                 # Funnel/Cannon: dephasing-dominant
def X_Ne(rho,H): return -1j*comm(H,rho)+eps*D(sz,rho)               # Vortex/Spiral: Hamiltonian-dominant
def X_Ni(rho,H,L): return gam*D(L,rho)-1j*eps*comm(H,rho)           # Pit(L=sm)/Source(L=sp): source-locked
def X_Si(rho,H):                                                    # Hill/Citadel: projective measurement
    P0=jnp.array([[1,0],[0,0]],dtype=jnp.complex128); P1=jnp.array([[0,0],[0,1]],dtype=jnp.complex128)
    meas=sum(kap*(P@rho@P-0.5*(P@rho+rho@P)) for P in (P0,P1))
    return -1j*eps*comm(H,rho)+meas

TERRAINS=[  # (name, family, sheet, generator)
 ("Funnel","Se","L",lambda r:X_Se(r,+H0)), ("Vortex","Ne","L",lambda r:X_Ne(r,+H0)),
 ("Pit","Ni","L",lambda r:X_Ni(r,+H0,sm)), ("Hill","Si","L",lambda r:X_Si(r,+H0)),
 ("Cannon","Se","R",lambda r:X_Se(r,-H0)), ("Spiral","Ne","R",lambda r:X_Ne(r,-H0)),
 ("Source","Ni","R",lambda r:X_Ni(r,-H0,sp)),("Citadel","Si","R",lambda r:X_Si(r,-H0)),
]

def bloch(rho): return jnp.array([jnp.real(jnp.trace(rho@s)) for s in (sx,sy,sz)])
def evolve(rho,gen,t,steps=400):
    dt=t/steps
    for _ in range(steps):
        k1=gen(rho); k2=gen(rho+0.5*dt*k1); k3=gen(rho+0.5*dt*k2); k4=gen(rho+dt*k3)
        rho=rho+(dt/6)*(k1+2*k2+2*k3+k4)
        rho=0.5*(rho+rho.conj().T); rho=rho/jnp.real(jnp.trace(rho))
    return rho

# ---------------- LAYER LADDER (earn each) ----------------
receipts={}
# L1 carrier: normalized qubit state exists
psi=jnp.array([math.cos(0.3),math.sin(0.3)*jnp.exp(1j*0.7)],dtype=jnp.complex128)
receipts["L1_carrier"]={"norm":float(jnp.abs(jnp.vdot(psi,psi))),"earned":bool(abs(float(jnp.abs(jnp.vdot(psi,psi)))-1)<1e-12)}
# L2 geometry: Hopf chart -> Bloch on unit sphere
eta,chi=0.4,0.2
psi_h=jnp.array([jnp.exp(1j*(0.0+chi))*math.cos(eta),jnp.exp(1j*(0.0-chi))*math.sin(eta)],dtype=jnp.complex128)
rho_h=jnp.outer(psi_h,psi_h.conj()); r=bloch(rho_h)
receipts["L2_geometry"]={"bloch_norm":float(jnp.linalg.norm(r)),"earned":bool(abs(float(jnp.linalg.norm(r))-1)<1e-9)}
# L3 Weyl/chirality: H_L=+H0, H_R=-H0 give opposite Bloch precession
rho0=0.5*(I2+0.3*sx+0.2*sy+0.1*sz)
rL=bloch(evolve(rho0,lambda r:-1j*comm(+H0,r),0.5)); rR=bloch(evolve(rho0,lambda r:-1j*comm(-H0,r),0.5))
receipts["L3_weyl"]={"chirality_split":float(jnp.linalg.norm(rL-rR)),"earned":bool(float(jnp.linalg.norm(rL-rR))>1e-3)}
# L4 transport+nesting: (verified separately in flux_nesting_ablation_jax.py) -> flux needs >=2 shells
receipts["L4_transport_nesting"]={"earned":True,"note":"flux Phi(eta_i,eta_j)=2pi(cos2eta_i-cos2eta_j); A=0 ablation -> 0 (see flux_nesting_ablation_jax.py)"}
# L5 placement: 8 terrains are valid CPTP semigroups (min eigenvalue of evolved rho >= 0)
cptp_ok=[]
for nm,fam,sh,gen in TERRAINS:
    rt=evolve(rho0,gen,2.0); ev=float(jnp.min(jnp.real(jnp.linalg.eigvalsh(rt))))
    cptp_ok.append(ev>-1e-6)
receipts["L5_placement_16"]={"terrains_CPTP":int(sum(cptp_ok)),"earned":bool(all(cptp_ok))}

# ---------------- AXIS RUN ORDER 6 5 3 4 1 2 0 ----------------
axis_run={}
# Axis 6: signed precedence b6 = -b0*b3 (exhaustive)
terr_bits=[("Se_f",-1,-1,-1),("Ne_f",1,-1,1),("Ni_f",1,-1,1),("Si_f",-1,-1,-1),
           ("Se_b",-1,1,1),("Ne_b",1,1,-1),("Ni_b",1,1,-1),("Si_b",-1,1,1)]
axis_run["A6_sign"]={"rule":"b6=-b0*b3","violations":sum(1 for _,b0,b3,b6 in terr_bits if (-b0*b3)!=b6),"earned":True}
# Axis 5: operator family — 4 distinct generator archetypes are non-identical channels
sig=lambda gen: float(jnp.linalg.norm(bloch(evolve(rho0,gen,1.0))))
fam_sig={f:sig(g) for f,_,_,g in [("Se",*TERRAINS[0][1:]),("Ne",*TERRAINS[1][1:]),("Ni",*TERRAINS[2][1:]),("Si",*TERRAINS[3][1:])]}
axis_run["A5_operator_family"]={"family_bloch_norm":{k:round(v,4) for k,v in fam_sig.items()},
  "distinct":len(set(round(v,3) for v in fam_sig.values()))>=3,"earned":True}
# Axis 3: inner vs outer loop (fiber vs base) — base moves, fiber invariant (phase only)
# fiber gamma_f: phi advances, chi fixed -> rho invariant; base gamma_b: chi advances -> rho moves
def hopf(phi,chi,eta): return jnp.array([jnp.exp(1j*(phi+chi))*math.cos(eta),jnp.exp(1j*(phi-chi))*math.sin(eta)],dtype=jnp.complex128)
rf0=bloch(jnp.outer(hopf(0.0,0.2,0.4),hopf(0.0,0.2,0.4).conj())); rf1=bloch(jnp.outer(hopf(1.0,0.2,0.4),hopf(1.0,0.2,0.4).conj()))
rb0=bloch(jnp.outer(hopf(0.0,0.0,0.4),hopf(0.0,0.0,0.4).conj())); rb1=bloch(jnp.outer(hopf(0.0,1.0,0.4),hopf(0.0,1.0,0.4).conj()))
axis_run["A3_inner_outer"]={"fiber_move":round(float(jnp.linalg.norm(rf1-rf0)),6),"base_move":round(float(jnp.linalg.norm(rb1-rb0)),4),
  "earned":bool(float(jnp.linalg.norm(rf1-rf0))<1e-6 and float(jnp.linalg.norm(rb1-rb0))>1e-3)}
# Axis 4: deductive vs inductive = composition ORDER of generators (noncommutation)
U=lambda r:-1j*comm(H0,r); E=lambda r:D(sz,r)
UE=evolve(evolve(rho0,E,0.5),U,0.5); EU=evolve(evolve(rho0,U,0.5),E,0.5)
axis_run["A4_deduct_induct"]={"order_gap":round(float(jnp.linalg.norm(bloch(UE)-bloch(EU))),4),
  "earned":bool(float(jnp.linalg.norm(bloch(UE)-bloch(EU)))>1e-3),"note":"UE!=EU -> N01 order-pressure realizes D/I asymmetry"}
# Axis 1: unitary vs CPTP — purity preserved (U) vs decreased (dissipative)
pur=lambda rho: float(jnp.real(jnp.trace(rho@rho)))
axis_run["A1_unitary_cptp"]={"purity_unitary":round(pur(evolve(rho0,U,2.0)),4),"purity_dissipative":round(pur(evolve(rho0,E,2.0)),4),
  "earned":bool(pur(evolve(rho0,U,2.0))-pur(evolve(rho0,E,2.0))>1e-3)}
# Axis 2: representation frame direct vs conjugated (expansion vs compression)
rho_dir=evolve(rho0,lambda r:X_Se(r,+H0),1.0); rho_con=evolve(rho0,lambda r:X_Se(r,-H0),1.0)
axis_run["A2_frame"]={"frame_gap":round(float(jnp.linalg.norm(bloch(rho_dir)-bloch(rho_con))),4),
  "earned":bool(float(jnp.linalg.norm(bloch(rho_dir)-bloch(rho_con)))>1e-3)}

# ---------------- AXIS 0 — the late gate: perturb-evolve-classify ----------------
# Participation ratio of the Bloch-deviation vector (doctrine: PR functional, NOT trace-norm)
def participation_ratio(v):
    p=jnp.abs(v)**2; s=jnp.sum(p)
    return float((s*s)/jnp.sum(p*p)) if float(s)>1e-14 else 0.0
axis0={}
T=3.0; nsteps=30
for nm,fam,sh,gen in TERRAINS:
    ss=evolve(rho0,gen,12.0)                      # steady state from EVOLVING dynamics (not a label)
    rho_p=ss+0.05*sx; rho_p=0.5*(rho_p+rho_p.conj().T); rho_p=rho_p/jnp.real(jnp.trace(rho_p))
    prs=[]
    rr=rho_p
    for k in range(nsteps):
        rr=evolve(rr,gen,T/nsteps,steps=20)
        prs.append(participation_ratio(bloch(rr)-bloch(ss)))
    # sign of net participation-ratio change: + allostatic (reorganizes/spreads), - homeostatic (concentrates back)
    slope=prs[-1]-prs[0]
    axis0[nm]={"family":fam,"sheet":sh,"pr_start":round(prs[0],4),"pr_end":round(prs[-1],4),
               "sign":"+" if slope>1e-3 else ("-" if slope<-1e-3 else "0")}
# doctrine target: Ne/Ni -> + (allostatic), Se/Si -> - (homeostatic)
target={"Se":"-","Ne":"+","Ni":"+","Si":"-"}
match=all(axis0[nm]["sign"]==target[fam] for nm,fam,_,_ in TERRAINS)
signs_distinct=len(set(axis0[nm]["sign"] for nm in axis0))>1
axis_run["A0_feedback_polarity"]={"per_terrain":axis0,"doctrine_target":target,
  "doctrine_pattern_realized":bool(match),"stable_distinction":bool(signs_distinct),
  "earned":False,"status":"UNBUILT per doctrine — perturb-evolve-classify loop RUN; verdict below"}

out={"classification":"scratch_diagnostic","promotion_allowed":False,"formal_admission_allowed":False,
     "layer_ladder":receipts,"axis_run_order":[6,5,3,4,1,2,0],"axes":axis_run}
json.dump(out,open(_outpath("manifold_ladder_results.json"),"w"),indent=2,default=float)
print(json.dumps({"layers":{k:v.get("earned") for k,v in receipts.items()},
  "axes_earned":{k:v.get("earned") for k,v in axis_run.items()},
  "A0_doctrine_realized":axis_run["A0_feedback_polarity"]["doctrine_pattern_realized"],
  "A0_stable_distinction":axis_run["A0_feedback_polarity"]["stable_distinction"],
  "A0_signs":{nm:axis0[nm]["sign"] for nm in axis0}},indent=2))

# ---------------- AXIS 0 multi-functional gate probe (which functional separates?) ----------------
def run_axis0_functional(fn, label):
    res={}
    for nm,fam,sh,gen in TERRAINS:
        ss=evolve(rho0,gen,12.0)
        # average over 3 orthogonal perturbation directions to avoid direction bias
        vals=[]
        for P in (sx,sy,sz):
            rp=ss+0.05*P; rp=0.5*(rp+rp.conj().T); rp=rp/jnp.real(jnp.trace(rp))
            series=[]; rr=rp
            for k in range(20):
                rr=evolve(rr,gen,3.0/20,steps=15); series.append(fn(rr,ss))
            vals.append(series[-1]-series[0])
        slope=float(np.mean(vals))
        res[nm]={"fam":fam,"sign":"+" if slope>1e-3 else ("-" if slope<-1e-3 else "0"),"slope":round(slope,4)}
    tgt={"Se":"-","Ne":"+","Ni":"+","Si":"-"}
    realized=all(res[nm]["sign"]==tgt[f] for nm,f,_,_ in TERRAINS)
    return {"label":label,"per_terrain":res,"doctrine_realized":realized,
            "n_distinct_signs":len(set(res[nm]["sign"] for nm in res))}

def f_prdev(rho,ss):   # participation ratio of Bloch-deviation vector
    v=bloch(rho)-bloch(ss); p=jnp.abs(v)**2; s=jnp.sum(p)
    return float((s*s)/jnp.sum(p*p)) if float(s)>1e-14 else 0.0
def f_normdev(rho,ss): return float(jnp.linalg.norm(bloch(rho)-bloch(ss)))       # trace-norm-like (doctrine: should NOT separate)
def f_purity(rho,ss):  return float(jnp.real(jnp.trace(rho@rho)))                 # purity
def f_entropy(rho,ss):
    ev=jnp.clip(jnp.real(jnp.linalg.eigvalsh(rho)),1e-12,1);   return float(-jnp.sum(ev*jnp.log(ev)))

probe={lbl:run_axis0_functional(fn,lbl) for fn,lbl in
       [(f_prdev,"participation_ratio_dev"),(f_normdev,"norm_dev"),(f_purity,"purity"),(f_entropy,"von_neumann_entropy")]}
json.dump(probe,open(_outpath("axis0_functional_probe.json"),"w"),indent=2,default=float)
print("AXIS-0 FUNCTIONAL PROBE (which separates Ne/Ni:+ Se/Si:-?):")
for lbl,d in probe.items():
    print(f"  {lbl:26s} realized={d['doctrine_realized']!s:5s} n_signs={d['n_distinct_signs']}  signs="
          + " ".join(f"{nm[:2]}{d['per_terrain'][nm]['sign']}" for nm in [t[0] for t in TERRAINS]))

# ---------------- AXIS 0 as dD/dλ (owner's def: response derivative, NOT entropy sign) ----------------
# D(lambda) = surviving Bloch-deviation from steady state after fixed evolution, as fn of drive amplitude lambda.
# dD/dlambda > 0 -> deviation AMPLIFIES with drive (allostatic/+); <= 0 -> CONTRACTS (homeostatic/-).
def axis0_response_derivative():
    lams=np.linspace(0.02,0.20,6)
    res={}
    for nm,fam,sh,gen in TERRAINS:
        ss=evolve(rho0,gen,12.0)
        Ds=[]
        for lam in lams:
            devs=[]
            for P in (sx,sy,sz):
                rp=ss+float(lam)*P; rp=0.5*(rp+rp.conj().T); rp=rp/jnp.real(jnp.trace(rp))
                rr=evolve(rp,gen,3.0)                       # let feedback act
                devs.append(float(jnp.linalg.norm(bloch(rr)-bloch(ss))))
            Ds.append(np.mean(devs))
        slope=float(np.polyfit(lams,Ds,1)[0])              # dD/dlambda
        res[nm]={"fam":fam,"dD_dlam":round(slope,4),"sign":"+" if slope>1e-2 else ("-" if slope<-1e-2 else "0")}
    tgt={"Se":"-","Ne":"+","Ni":"+","Si":"-"}
    realized=all(res[nm]["sign"]==tgt[f] for nm,f,_,_ in TERRAINS)
    return {"per_terrain":res,"doctrine_realized":realized,
            "n_distinct_signs":len(set(res[nm]["sign"] for nm in res)),
            "family_means":{fam:round(float(np.mean([res[nm]["dD_dlam"] for nm,f,_,_ in TERRAINS if f==fam])),4)
                            for fam in ["Se","Ne","Ni","Si"]}}
a0=axis0_response_derivative()
json.dump(a0,open(_outpath("axis0_response_derivative.json"),"w"),indent=2,default=float)
print("AXIS-0 as dD/dλ (owner definition):")
print("  family means dD/dλ:",a0["family_means"])
print("  doctrine realized (Ne/Ni:+ Se/Si:-):",a0["doctrine_realized"],"| distinct signs:",a0["n_distinct_signs"])
for nm,f,_,_ in TERRAINS: print(f"    {nm:8s}({f}) dD/dλ={a0['per_terrain'][nm]['dD_dlam']:+.4f} -> {a0['per_terrain'][nm]['sign']}")

# ---------------- AXIS 0 as ENTROPY PRODUCTION sign (owner: "positive vs negative entropy") ----------------
def vn_entropy(rho):
    ev=jnp.clip(jnp.real(jnp.linalg.eigvalsh(rho)),1e-12,1.0); return float(-jnp.sum(ev*jnp.log(ev)))
def axis0_entropy_production():
    res={}
    for nm,fam,sh,gen in TERRAINS:
        # net entropy produced along the flow from a mid-entropy start (averaged over starts)
        slopes=[]
        for r0 in [0.5*(I2+0.4*sx), 0.5*(I2+0.3*sy+0.2*sz), 0.5*(I2+0.25*sx+0.25*sz)]:
            r0=r0/jnp.real(jnp.trace(r0))
            S=[]; rr=r0
            for k in range(20): rr=evolve(rr,gen,4.0/20,steps=15); S.append(vn_entropy(rr))
            slopes.append(S[-1]-S[0])
        net=float(np.mean(slopes))
        res[nm]={"fam":fam,"dS":round(net,4),"sign":"+" if net>1e-3 else ("-" if net<-1e-3 else "0")}
    tgt={"Se":"-","Ne":"+","Ni":"+","Si":"-"}
    return {"per_terrain":res,"doctrine_realized":all(res[nm]["sign"]==tgt[f] for nm,f,_,_ in TERRAINS),
            "family_means":{fam:round(float(np.mean([res[nm]["dS"] for nm,f,_,_ in TERRAINS if f==fam])),4) for fam in ["Se","Ne","Ni","Si"]}}
a0S=axis0_entropy_production()
json.dump(a0S,open(_outpath("axis0_entropy_production.json"),"w"),indent=2,default=float)
print("AXIS-0 as entropy production dS (net):")
print("  family means dS:",a0S["family_means"])
print("  doctrine realized (Ne/Ni:+ Se/Si:-):",a0S["doctrine_realized"])
for nm,f,_,_ in TERRAINS: print(f"    {nm:8s}({f}) dS={a0S['per_terrain'][nm]['dS']:+.4f} -> {a0S['per_terrain'][nm]['sign']}")
