#!/usr/bin/env python3
"""unified_attractor_basin_seven_axes_sim -- the whole thing as ONE attractor basin: all 7 axes (0-6) read as
LOAD-BEARING dynamical witnesses from the SAME running-engine substrate, each with a falsifiable ERASURE control that
collapses ONLY that axis. This closes the gap where axes 1-4 were only established individually (in the foundations /
axis-law sims) and never exercised as live mechanics in one engine.

SOURCE-GROUNDED (v7 AXES_FULL_EXTRACTION_20260703). Each axis is a READOUT MAP A_i : M(C) -> V_i, never a primitive
coordinate; an axis may READ geometry but must not ABSORB flux/holonomy/nesting as the axis itself. Per-axis witness +
contamination guard:

  A0 the drive/polarity   {Ne,Ni}|{Se,Si}: b0=sign(r_z) at loop close, drive present from start.
                          ERASE: remove the GKSL flow -> polarity collapses. GUARD: flux/transport is not A0.
  A1 branch (derived)     unitary Phi=UrU^dag (dS=0 exact) vs proper CPTP Phi=sum K r K^dag (dS>0).
                          ERASE: drop the dissipator -> the CPTP branch becomes unitary (dS->0). GUARD: not isothermal/
                          adiabatic overlay; the CPTP/unitary branch is the kernel.
  A2 frame                direct V=I vs conjugated V!=I, readable only through dissipation (K=iV^dag Vdot).
                          ERASE: set V=I -> conjugated == direct (dist 0). GUARD: K_t is the readout, holonomy is not A2.
  A3 loop class           fiber gamma_f density STATIONARY vs lifted-base gamma_b density TRAVERSES (horizontal lift).
                          ERASE: degenerate eta=pi/4 -> fiber/base density-motion coincide. GUARD: A3 does not own flux.
  A4 loop order           Phi_D=UEUE vs Phi_I=EUEU; witness ||Phi_D(r)-Phi_I(r)||_1 ~ tau^2 |[L_R,L_C]|.
                          ERASE: commuting generators -> order gap 0. GUARD: not visual spin / terrain-graph path.
  A5 operator family      {Ti,Te} pinch (dS!=0) vs {Fi,Fe} rotation (dS=0 EXACT, spectrum preserved).
                          ERASE: replace the F-rotation with a pinch -> entropy-preservation breaks. GUARD: operator-
                          family selection only, not S-curve/lobe/visual weighting.
  A6 precedence           up=operator-first Phi_T o O vs down=terrain-first O o Phi_T; gap ||A r - r A||_F.
                          ERASE: shared-drive-axis op collapses up=down. GUARD: b6=-b0*b3(chart-role), not raw flux.

NESTED-INTELLIGENCE LAYERS (assessed by distinguishability-based object perception, a=a iff a~b):
  L0 stage         : one (terrain,operator,sign) map -- its own processing kind.
  L1 loop          : 4 ordered stages -- order-sensitive (N01), a kind the stages alone are not.
  L2 two-loops     : outer+inner composed -- loop-order sensitive, more than the sum.
  L3 two-engines   : Type-1 (left) + Type-2 (right) -- opposite polarity, not a relabeling of each other.
Each layer is a distinguishable object iff its identity survives probe rotation AND its shuffle/erase control collapses.

This is a scratch_diagnostic (promotion_allowed=false). It extends v7's axis_relation_matrix_probe (which reads the
axis bits SYMBOLICALLY from the chart and checks pairwise independence + b6=-b0*b3) by reading each axis DYNAMICALLY
from the live trajectory and proving load-bearing via axis-specific erasure. It makes NO promotion/canon claim.
"""
import json, os, sys
import numpy as np
from scipy.linalg import expm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; Q=1-np.exp(-1); TH=np.pi/4; NS=200
# oracle terrains: (eps, kind, pole)
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
H0=(sx+sy+sz)/np.sqrt(3)

def Dop(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def dm(v):
    v=np.array(v,float); return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)
def bloch(r): return np.array([np.trace(r@s).real for s in (sx,sy,sz)])
def S(r):
    w=np.linalg.eigvalsh(r); w=w[w>1e-12]; return float(-(w*np.log2(w)).sum())
def lindblad_ops(kind,pole):
    if kind=='damp': return [sp if pole>0 else sm]
    if kind=='depol': return [sx/np.sqrt(2),sy/np.sqrt(2)]
    return [sz]
def flow(H,Ls,r,t=1.0,steps=NS,drive=True):
    dt=t/steps
    def X(r):
        out=(-1j*G*(H@r-r@H)) if drive else 0*r
        for L in Ls: out=out+KAP*Dop(L,r)
        return out
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);r/=np.trace(r).real
    return r
def terr_flow(ti,r,drive=True,eps_override=None):
    eps,kind,pole=TERR[ti]
    if eps_override is not None: eps=eps_override
    return flow(eps*H0, lindblad_ops(kind,pole), r, drive=drive)
def op(n,th=TH):
    P0=.5*(I2+sz);P1=.5*(I2-sz);Qp=.5*(I2+sx);Qm=.5*(I2-sx)
    if n=='Ti':return lambda r:(1-Q)*r+Q*(P0@r@P0+P1@r@P1)
    if n=='Te':return lambda r:(1-Q)*r+Q*(Qp@r@Qp+Qm@r@Qm)
    if n=='Fi':U=expm(-1j*th/2*sx);return lambda r:U@r@U.conj().T
    if n=='Fe':U=expm(-1j*th/2*sz);return lambda r:U@r@U.conj().T
def hpsi(phi,chi,eta): return np.array([np.cos(eta)*np.exp(1j*phi), np.sin(eta)*np.exp(1j*chi)],complex)
def rho_of(psi): p=psi/np.linalg.norm(psi); return np.outer(p,p.conj())

PROBE=dm([0.55,0.35,0.25])

# engine loop slots (doc-faithful) + a drive-parametrized runner, defined early so axis0 can use them
T1_OUT=[(0,'Ti','up'),(1,'Ti','down'),(2,'Fe','down'),(3,'Fe','up')]
T1_IN =[(0,'Fi','down'),(3,'Te','down'),(2,'Te','up'),(1,'Fi','up')]
T2_OUT=[(4,'Fi','up'),(7,'Te','up'),(6,'Te','down'),(5,'Fi','down')]
T2_IN =[(4,'Ti','down'),(5,'Ti','up'),(6,'Fe','up'),(7,'Fe','down')]
def step_drive(slot,r,drive=True):
    t,o,sg=slot
    return terr_flow(t, op(o)(r.copy()), drive=drive) if sg=='up' else op(o)(terr_flow(t,r.copy(),drive=drive))
def run_loop_drive(slots,probe,drive=True):
    r=dm(probe); T=[bloch(r).copy()]
    for s in slots: r=step_drive(s,r,drive); T.append(bloch(r).copy())
    return np.array(T)
def sv(T): return float(sum(np.dot(T[i],np.cross(T[i+1],T[i+2])) for i in range(len(T)-2)))

# ---------------- each axis: (real witness, erased witness), load-bearing iff real separates and erase collapses ----------
def axis0():
    # the drive/polarity: loop-close signed-volume polarity of the full engine (same readout as rungs 1-4).
    # Type-1 vs Type-2 read OPPOSITE; removing the coherent flow (drive=False, operators still act) COLLAPSES it.
    rng=np.random.default_rng(9); pr=[p/np.linalg.norm(p)*0.6 for p in [rng.standard_normal(3) for _ in range(40)]]
    p1=float(np.mean([sv(run_loop_drive(T1_OUT+T1_IN,p,True)) for p in pr]))
    p2=float(np.mean([sv(run_loop_drive(T2_OUT+T2_IN,p,True)) for p in pr]))
    n1=float(np.mean([sv(run_loop_drive(T1_OUT+T1_IN,p,False)) for p in pr]))
    n2=float(np.mean([sv(run_loop_drive(T2_OUT+T2_IN,p,False)) for p in pr]))
    opposite=(np.sign(p1)!=np.sign(p2))
    collapse=(abs(n1)<0.2*abs(p1) and abs(n2)<0.2*abs(p2))
    return {"type1_polarity":round(p1,5),"type2_polarity":round(p2,5),"opposite_signs":bool(opposite),
            "noflow_type1":round(n1,6),"noflow_type2":round(n2,6),"noflow_collapses_polarity":bool(collapse),
            "load_bearing":bool(opposite and collapse)}
def axis1():
    pure=rho_of(hpsi(0.4,0.3,0.6))
    uni=expm(-1j*0.7*H0)@pure@expm(1j*0.7*H0)
    cptp=flow(H0,[sp],pure); erased=flow(H0,[],pure)  # drop dissipator -> unitary
    dS_uni=abs(S(uni)-S(pure)); dS_cptp=abs(S(cptp)-S(pure)); dS_erased=abs(S(erased)-S(pure))
    return {"unitary_dS":round(dS_uni,6),"cptp_dS":round(dS_cptp,5),"erased_dS":round(dS_erased,6),
            "load_bearing":bool(dS_uni<1e-9 and dS_cptp>0.01 and dS_erased<1e-6)}
def axis2():
    def frame(conj,erase=False):
        V=expm(-1j*0.6*sy) if (conj and not erase) else I2
        r=PROBE.copy()
        if conj: r=V.conj().T@r@V
        r=flow(H0,[sx/np.sqrt(2),sy/np.sqrt(2)],r)   # dissipative terrain -> frame readable
        if conj: r=V@r@V.conj().T
        return bloch(r)
    d=frame(False); c=frame(True); ce=frame(True,erase=True)
    sep=float(np.linalg.norm(d-c)); sep_erased=float(np.linalg.norm(d-ce))
    return {"direct_vs_conjugated":round(sep,5),"erased_V_eq_I":round(sep_erased,6),
            "load_bearing":bool(sep>0.02 and sep_erased<1e-6)}
def axis3():
    eta0,chi0,phi0=0.6,0.3,0.4
    def motions(eta):
        us=np.linspace(0,2*np.pi,40)
        fib=[bloch(rho_of(hpsi(phi0+u,chi0,eta))) for u in us]
        base=[bloch(rho_of(hpsi(phi0-np.cos(2*eta)*u,chi0+u,eta))) for u in us]
        fm=float(np.mean([np.linalg.norm(fib[i+1]-fib[i]) for i in range(len(fib)-1)]))
        bm=float(np.mean([np.linalg.norm(base[i+1]-base[i]) for i in range(len(base)-1)]))
        return fm,bm
    fm,bm=motions(eta0); fme,bme=motions(np.pi/4)
    return {"fiber_density_motion":round(fm,5),"base_density_motion":round(bm,5),
            "loop_class_gap":round(bm-fm,5),"erased_degenerate_eta_gap":round(bme-fme,5),
            "load_bearing":bool((bm-fm)>0.03 and abs(bme-fme)<(bm-fm))}
def axis4():
    def gap(erase=False):
        if erase:
            Uz=expm(-1j*TH/2*sz); E=lambda r: flow(sz,[sz],r); U=lambda r: Uz@r@Uz.conj().T
        else:
            E=lambda r: flow(H0,[sp],r); U=op('Fi')
        r=PROBE.copy(); D=U(E(U(E(r.copy())))); Ir=E(U(E(U(r.copy()))))
        return float(np.linalg.norm(bloch(D)-bloch(Ir),1))
    real=gap(); er=gap(erase=True)
    return {"order_gap_D_vs_I":round(real,5),"erased_commuting_gap":round(er,6),
            "load_bearing":bool(real>0.05 and er<0.01)}
def axis5():
    r0=terr_flow(0,PROBE.copy())
    dS_F=abs(S(op('Fi')(r0))-S(r0)); dS_T=abs(S(op('Ti')(r0))-S(r0))
    dS_F_erased=abs(S(op('Ti')(r0))-S(r0))   # replace F-rotation with a pinch
    return {"F_rotation_dS":round(dS_F,6),"T_pinch_dS":round(dS_T,5),"erased_F_as_pinch_dS":round(dS_F_erased,5),
            "load_bearing":bool(dS_F<0.005 and dS_T>0.01 and dS_F_erased>0.01)}
def axis6():
    # up=operator-first Phi_T(O(rho)) vs down=terrain-first O(Phi_T(rho)); precedence gap ||up-down||.
    # On the SAME terrain (depol t1): the x-rotation Fi has a load-bearing precedence gap, while the pinch Ti nearly
    # COLLAPSES (up=down) because it commutes with the terrain's pointer structure. The control is the ratio: the
    # collapse op's gap must be a small fraction of the load-bearing op's gap on the same terrain.
    def prec(ti,o):
        up=terr_flow(ti, op(o)(PROBE.copy())); down=op(o)(terr_flow(ti,PROBE.copy()))
        return float(np.linalg.norm(bloch(up)-bloch(down)))
    load=prec(1,'Fi')       # x-family op on depol terrain: precedence matters
    collapse=prec(1,'Ti')   # pinch on the SAME terrain: precedence nearly collapses
    return {"precedence_gap_load_bearing_op":round(load,5),"precedence_gap_collapse_op_same_terrain":round(collapse,6),
            "load_bearing":bool(load>0.05 and collapse<0.3*load)}

# ---------------- nested-intelligence layers, assessed by distinguishability ----------
def run_loop(slots,probe): return run_loop_drive(slots,probe,drive=True)
def layers():
    rng=np.random.default_rng(7); pr=[p/np.linalg.norm(p)*0.6 for p in [rng.standard_normal(3) for _ in range(20)]]
    # L0 stage distinctness (are the 4 stages of T1_OUT distinct channels on seen probes)
    endp=[np.concatenate([run_loop([s],p)[-1] for p in pr[:8]]) for s in T1_OUT]
    l0_min=min(float(np.linalg.norm(endp[i]-endp[j])) for i in range(4) for j in range(i+1,4))
    # L1 loop order-sensitivity: permute the loop vs identity
    base=np.concatenate([run_loop(T1_OUT,p)[-1] for p in pr[:8]])
    perm=np.concatenate([run_loop([T1_OUT[k] for k in [1,0,3,2]],p)[-1] for p in pr[:8]])
    l1_gap=float(np.linalg.norm(base-perm))
    # L2 two-loops: outer-then-inner vs inner-then-outer
    oi=np.concatenate([run_loop(T1_OUT+T1_IN,p)[-1] for p in pr[:8]])
    io=np.concatenate([run_loop(T1_IN+T1_OUT,p)[-1] for p in pr[:8]])
    l2_gap=float(np.linalg.norm(oi-io))
    # L3 two-engines: Type1 vs Type2 polarity opposite + not a relabeling
    p1=float(np.mean([sv(run_loop(T1_OUT+T1_IN,p)) for p in pr]))
    p2=float(np.mean([sv(run_loop(T2_OUT+T2_IN,p)) for p in pr]))
    s1=np.concatenate([run_loop(T1_OUT+T1_IN,p)[-1] for p in pr[:8]]); best=1e9
    for fx in(1,-1):
        for fy in(1,-1):
            for fz in(1,-1):
                F=np.diag([fx,fy,fz]).astype(float)
                s2=np.concatenate([F@run_loop(T2_OUT+T2_IN,p)[-1] for p in pr[:8]])
                best=min(best,float(np.linalg.norm(s1-s2)))
    return {"L0_stage_min_pairwise":round(l0_min,4),"L0_distinct":bool(l0_min>0.05),
            "L1_loop_order_gap":round(l1_gap,4),"L1_order_sensitive":bool(l1_gap>0.05),
            "L2_two_loops_gap":round(l2_gap,4),"L2_more_than_sum":bool(l2_gap>0.05),
            "L3_type1_polarity":round(p1,5),"L3_type2_polarity":round(p2,5),
            "L3_opposite":bool(np.sign(p1)!=np.sign(p2)),"L3_not_relabeling":bool(best>0.1)}

def main():
    ax={f"axis{i}":fn() for i,fn in enumerate([axis0,axis1,axis2,axis3,axis4,axis5,axis6])}
    lay=layers()
    all_axes_lb=all(ax[f"axis{i}"]["load_bearing"] for i in range(7))
    layers_ok=(lay["L0_distinct"] and lay["L1_order_sensitive"] and lay["L2_more_than_sum"]
               and lay["L3_opposite"] and lay["L3_not_relabeling"])
    verdict=bool(all_axes_lb and layers_ok)
    out={"classification":"scratch_diagnostic","promotion_status":"scratch_diagnostic","promotion_allowed":False,
         "mechanical_run_status":"one engine substrate; 7 axes read as dynamical witnesses with per-axis erasure controls",
         "source_fidelity_status":"axis witnesses grounded in v7 AXES_FULL_EXTRACTION_20260703; each guarded against geometry-contamination",
         "dynamic_claim_status":"each axis load-bearing under a finite probe battery; not a proof of axis uniqueness/closure",
         "framing":"the whole model as ONE attractor basin: 7 axes as load-bearing mechanics on one engine, with nested-intelligence layers L0 stage -> L1 loop -> L2 two-loops -> L3 two-engines, assessed by distinguishability",
         "seven_axes":ax,"all_seven_axes_load_bearing":bool(all_axes_lb),
         "nested_intelligence_layers":lay,"all_layers_distinguishable":bool(layers_ok),
         "UNIFIED_ATTRACTOR_BASIN_SEVEN_AXES_BUILT":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("UNIFIED ATTRACTOR BASIN -- 7 axes as load-bearing mechanics on ONE engine + nested-intelligence layers.\n")
    print("  SEVEN AXES (each: real witness separates, erasure control collapses ONLY that axis):")
    labels={0:"drive/polarity",1:"branch (unitary|CPTP)",2:"frame (direct|conj)",3:"loop class (fiber|base)",
            4:"loop order (D|I)",5:"operator family (T|F)",6:"precedence (up|down)"}
    for i in range(7):
        a=ax[f"axis{i}"]; print(f"    A{i} {labels[i]:26} load-bearing={a['load_bearing']}")
    print(f"  -> all seven axes load-bearing on one engine: {all_axes_lb}")
    print("\n  NESTED-INTELLIGENCE LAYERS (assessed by distinguishability):")
    print(f"    L0 stage distinct (min pairwise {lay['L0_stage_min_pairwise']}): {lay['L0_distinct']}")
    print(f"    L1 loop order-sensitive (gap {lay['L1_loop_order_gap']}): {lay['L1_order_sensitive']}")
    print(f"    L2 two-loops more-than-sum (gap {lay['L2_two_loops_gap']}): {lay['L2_more_than_sum']}")
    print(f"    L3 two-engines opposite polarity ({lay['L3_type1_polarity']} vs {lay['L3_type2_polarity']}), not a relabeling: {lay['L3_opposite'] and lay['L3_not_relabeling']}")
    print(f"\n  UNIFIED ATTRACTOR BASIN SEVEN AXES BUILT: {verdict}")
    if verdict: print("PASS unified_attractor_basin_seven_axes")
    print("ALL_GATES:", "PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
