#!/usr/bin/env python3
"""four_substrate_agreement_harness -- PURE MATH, NO JARGON. 2026-07-10. Certifies that the load-bearing QIT kernels of
the constraint core are SUBSTRATE-INDEPENDENT: the same density-matrix mathematics run in numpy, JAX(x64), PyTorch, and
Julia (LinearAlgebra stdlib) must agree to ~1e-9 on every terrain. This is the project substrate doctrine made into a
failable gate: "julia canon arbiter everywhere; jax+julia standing pair; torch load-bearing wherever learning; all four
when a result gets stamped" (substrate_split), and "numpy has too much classical presumption" (numpy_classical_presumption).

WHY THIS EXISTS. An external review found the active estate was ~136/145 sims numpy-ONLY (only 2 JAX, 1 Torch, 1 Julia).
Re-running the SAME linear algebra in another substrate does not change any verdict -- but it (a) proves the results are
not artifacts of one library's presumptions, and (b) catches real substrate bugs. A live example this build caught: JAX
defaults to complex64 (float32) and SILENTLY TRUNCATES complex128 unless jax_enable_x64 is set -- a numpy result that
disagreed at float32 would be a genuine latent bug. This harness pins x64 and checks agreement.

WHAT IS COMPUTED. For each of the 8 canonical terrains (project TERR table), each substrate independently computes from
the SAME GKSL generator: (i) the fixed-point Bloch vector after t=12 flow, (ii) the von Neumann entropy at the fixed
point, (iii) the terrain channel's Liouville-spectrum |eigenvalues|. numpy is the reference; JAX(x64), Torch, and Julia
are compared against it. Julia runs as a subprocess (dependency-free LinearAlgebra), parsed from stdout.

VERDICT GATES (failable; agreement is a measured max-abs-difference, not a hand-picked pass count):
  (A) JAX(x64) agrees with numpy to < 1e-9 on all terrains x all readouts.
  (B) Torch(float64) agrees with numpy to < 1e-9 on all terrains x all readouts.
  (C) Julia agrees with numpy to < 1e-9 on all terrains x all readouts (arbiter; independent language, column-major).
  CONTROL THAT FLIPS (proves the gate can fail): the same JAX kernel run WITHOUT x64 (complex64) is ALSO measured; its
  max difference is REPORTED and must be materially larger than the x64 difference (the float32 truncation the doctrine
  warns about). If float32 agreed to 1e-9 too, the tolerance would be meaningless.

HONEST SCOPE. Earns: substrate-independence of the core kernels (fixed points, entropy, Liouville spectra) across four
independent implementations, and the concrete float32-vs-float64 artifact. Does NOT claim any NEW physics -- identical
numbers are the point. Does NOT re-run all 145 sims file-by-file (that would be cosmetic; the kernels ARE the load-
bearing content). scratch_diagnostic, promotion_allowed=false, but this one is REGISTERED because the gate is failable
and the doctrine requires standing substrate certification.
"""
import json, os, sys, subprocess
os.environ["JAX_ENABLE_X64"]="1"
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__))
KDIR=os.path.join(os.path.dirname(HERE),"substrate_kernels")
sys.path.insert(0,KDIR)
import kernels_np as K

def np_readouts():
    out={}
    for ti in range(8):
        fp=K.fixed_point(ti)
        bl=[float(np.real(np.trace(fp@s))) for s in (K.sx,K.sy,K.sz)]
        out[ti]={"bloch":bl,"vn":K.vn_entropy(fp),"liou":list(map(float,K.liouville_spectrum(ti)))}
    return out

def jax_readouts(x64=True):
    import importlib
    if not x64: os.environ["JAX_ENABLE_X64"]="0"
    import jax; jax.config.update("jax_enable_x64", x64); import jax.numpy as jnp
    dt=jnp.complex128 if x64 else jnp.complex64
    sx=jnp.array([[0,1],[1,0]],dtype=dt);sy=jnp.array([[0,-1j],[1j,0]],dtype=dt);sz=jnp.array([[1,0],[0,-1]],dtype=dt);I2=jnp.eye(2,dtype=dt)
    sp=0.5*(sx+1j*sy);sm=0.5*(sx-1j*sy);G=0.35;KAP=1.0
    TERR=K.TERR
    def Dop(L,r):return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
    def step(ti,r,dt_):
        eps,kind,pole=TERR[ti];H=eps*(sx+sy+sz)/jnp.sqrt(3.0)
        out=-1j*G*(H@r-r@H)
        if kind=='damp':out=out+KAP*Dop(sp if pole>0 else sm,r)
        elif kind=='depol':out=out+0.5*KAP*(Dop(sx,r)+Dop(sy,r))
        else:out=out+KAP*Dop(sz,r)
        return r+dt_*out
    def flow(ti,r,t=12.0,steps=3600):
        d=t/steps
        for _ in range(steps):r=step(ti,r,d)
        return r
    def vn(r):
        w=jnp.linalg.eigvalsh(r);w=w[w>1e-12];return float(-jnp.sum(w*jnp.log(w)))
    out={}
    for ti in range(8):
        fp=flow(ti,0.5*I2); bl=[float(jnp.real(jnp.trace(fp@s))) for s in (sx,sy,sz)]
        B=[I2/jnp.sqrt(2.0),sx/jnp.sqrt(2.0),sy/jnp.sqrt(2.0),sz/jnp.sqrt(2.0)]
        eps,kind,pole=TERR[ti];H=eps*(sx+sy+sz)/jnp.sqrt(3.0);M=jnp.zeros((4,4),dtype=dt)
        cols=[]
        for j,b in enumerate(B):
            img=-1j*G*(H@b-b@H)
            if kind=='damp':img=img+KAP*Dop(sp if pole>0 else sm,b)
            elif kind=='depol':img=img+0.5*KAP*(Dop(sx,b)+Dop(sy,b))
            else:img=img+KAP*Dop(sz,b)
            cols.append(jnp.array([jnp.trace(c.conj().T@img) for c in B]))
        M=jnp.stack(cols,axis=1)
        liou=sorted([float(x) for x in jnp.abs(jnp.linalg.eigvals(M))],reverse=True)
        out[ti]={"bloch":bl,"vn":vn(fp),"liou":liou}
    return out

def torch_readouts():
    import torch, math; torch.set_default_dtype(torch.float64)
    dt=torch.complex128; SQRT3=math.sqrt(3.0); SQRT2=math.sqrt(2.0)
    sx=torch.tensor([[0,1],[1,0]],dtype=dt);sy=torch.tensor([[0,-1j],[1j,0]],dtype=dt);sz=torch.tensor([[1,0],[0,-1]],dtype=dt);I2=torch.eye(2,dtype=dt)
    sp=0.5*(sx+1j*sy);sm=0.5*(sx-1j*sy);G=0.35;KAP=1.0;TERR=K.TERR
    def Dop(L,r):return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
    def step(ti,r,dt_):
        eps,kind,pole=TERR[ti];H=eps*(sx+sy+sz)/SQRT3
        out=-1j*G*(H@r-r@H)
        if kind=='damp':out=out+KAP*Dop(sp if pole>0 else sm,r)
        elif kind=='depol':out=out+0.5*KAP*(Dop(sx,r)+Dop(sy,r))
        else:out=out+KAP*Dop(sz,r)
        return r+dt_*out
    def flow(ti,r,t=12.0,steps=3600):
        d=t/steps
        for _ in range(steps):r=step(ti,r,d)
        return r
    def vn(r):
        w=torch.linalg.eigvalsh(r);w=w[w>1e-12];return float(-torch.sum(w*torch.log(w)))
    out={}
    for ti in range(8):
        fp=flow(ti,0.5*I2);bl=[float(torch.real(torch.trace(fp@s))) for s in (sx,sy,sz)]
        B=[I2/SQRT2,sx/SQRT2,sy/SQRT2,sz/SQRT2]
        eps,kind,pole=TERR[ti];H=eps*(sx+sy+sz)/SQRT3
        cols=[]
        for b in B:
            img=-1j*G*(H@b-b@H)
            if kind=='damp':img=img+KAP*Dop(sp if pole>0 else sm,b)
            elif kind=='depol':img=img+0.5*KAP*(Dop(sx,b)+Dop(sy,b))
            else:img=img+KAP*Dop(sz,b)
            cols.append(torch.stack([torch.trace(c.conj().T@img) for c in B]))
        M=torch.stack(cols,dim=1)
        liou=sorted([float(x) for x in torch.abs(torch.linalg.eigvals(M))],reverse=True)
        out[ti]={"bloch":bl,"vn":vn(fp),"liou":liou}
    return out

def julia_readouts():
    jl=os.environ.get("JULIA_BIN") or __import__("shutil").which("julia") or ("/opt/homebrew/bin/julia" if os.path.exists("/opt/homebrew/bin/julia") else "/tmp/julia_install/bin/julia")  # portability repair 2026-07-11: resolve the real runtime, container default last
    if not os.path.exists(jl): return None
    p=subprocess.run([jl,os.path.join(KDIR,"julia_kernels.jl")],capture_output=True,text=True,timeout=300)
    out={}
    for line in p.stdout.splitlines():
        if not line.startswith("t"): continue
        parts=line.split()
        ti=int(parts[0][1:])
        bl=[float(parts[2]),float(parts[3]),float(parts[4])]; vn=float(parts[6])
        liou=[float(parts[8]),float(parts[9]),float(parts[10]),float(parts[11])]
        out[ti]={"bloch":bl,"vn":vn,"liou":liou}
    return out if out else None

def maxdiff(a,b):
    d=0.0
    for ti in range(8):
        for k in ("bloch","vn","liou"):
            av=a[ti][k]; bv=b[ti][k]
            if isinstance(av,float): d=max(d,abs(av-bv))
            else: d=max(d,max(abs(x-y) for x,y in zip(av,bv)))
    return d

def main():
    path=os.path.join(HERE,"four_substrate_agreement_harness_sim_results.json")
    ref=np_readouts()
    jx=jax_readouts(x64=True); d_jax=maxdiff(ref,jx)
    tc=torch_readouts(); d_torch=maxdiff(ref,tc)
    ju=julia_readouts(); d_julia=maxdiff(ref,ju) if ju else None
    # control: float32 jax
    try: jx32=jax_readouts(x64=False); d_jax32=maxdiff(ref,jx32)
    except Exception as e: d_jax32=None
    TOL=1e-9
    A=bool(d_jax<TOL); B=bool(d_torch<TOL); C=bool(d_julia is not None and d_julia<TOL)
    ctrl=bool(d_jax32 is not None and d_jax32>1e3*d_jax)  # float32 materially worse
    verdict=bool(A and B and C and ctrl)
    out={"classification":"port_fidelity_certification","promotion_allowed":False,
      "framing":"PORT-FIDELITY certification (NOT a forced-physics claim -- an adversarial panel correctly noted that agreement of correctly-ported identical float64 GKSL linear algebra is near-automatic and certifies software-port fidelity, not physically forced structure). What is earned: the four independent implementations (numpy, JAX(x64), Torch(f64), Julia LinearAlgebra) agree to <1e-9 on all 8 terrains (fixed point, vN entropy, Liouville spectrum), so no core result is an artifact of ONE library's numerics, AND the float32 truncation the doctrine warns about is caught. The physics MODEL is defined once (kernels_np) and ported; this certifies the PORTS agree, it does NOT independently re-derive the model in each substrate. Doctrine served: jax+julia standing pair + torch, all four cross-checked when a result is stamped.",
      "max_abs_diff_vs_numpy":{"jax_x64":d_jax,"torch_f64":d_torch,"julia":d_julia},
      "gate_A_jax_agrees":A,"gate_B_torch_agrees":B,"gate_C_julia_agrees":C,
      "control_float32_materially_worse":{"jax_float32_maxdiff":d_jax32,"jax_x64_maxdiff":d_jax,"ratio_gt_1e3":ctrl,
        "note":"JAX complex64 (float32) silently truncates; must be >>1e-9 while x64 is <1e-9 -- proves the tolerance is a real gate, not vacuous."},
      "tolerance":TOL,"pass":verdict,
      "honest_scope":"PORT-FIDELITY only: identical numbers ARE the deliverable (the four ports of the same model agree + the float32 artifact is caught). This is reproducibility engineering, NOT a forced structural rung -- agreement of correctly-ported float64 linear algebra is near-automatic and certifies port fidelity, not physics. The model is defined once and ported, so this does NOT prove each substrate independently re-derived the physics. Not a file-by-file rewrite of all 145 sims -- the kernels are the load-bearing content and are now cross-substrate certified.",
      "panel_accepted":"Fixed a numpy-constant leak in the torch port (np.sqrt->math.sqrt); reclassified from 'substrate_independence of physics' to 'port_fidelity_certification' per unanimous panel catch that identical-code agreement is not forced structure.",
      "policy_eval":{"kernel_ports_agree_to_1e-9":verdict,"float32_artifact_caught":ctrl}}
    json.dump(out,open(path,"w"),indent=2)
    print("GATE -- four-substrate agreement on load-bearing QIT kernels (8 terrains):")
    print(f"  max|Δ vs numpy|:  JAX(x64) {d_jax:.2e}   Torch(f64) {d_torch:.2e}   Julia {d_julia if d_julia is None else format(d_julia,'.2e')}")
    print(f"  (A) JAX agrees <1e-9: {A}   (B) Torch agrees <1e-9: {B}   (C) Julia agrees <1e-9: {C}")
    print(f"  control: JAX float32 max|Δ| {d_jax32 if d_jax32 is None else format(d_jax32,'.2e')} >> x64 (ratio>1e3): {ctrl} (float32 truncation caught)")
    print(f"  VERDICT: {'PASS' if verdict else 'FAIL'} (PORT-FIDELITY: four ports of the same model agree <1e-9; float32 artifact caught -- reproducibility engineering, not forced physics)")
    if verdict: print("PASS four_substrate_agreement_harness")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
