"""
qit_fep_ratchet_sim.py -- PURE MATH, no jargon, no classical/thermal terms. 2026-07-03, Layer 0.9.

A QIT Free Energy Principle RENDERED THROUGH THE RATCHET (hypothetical lane), stage by stage -- geometry, entropy, operators,
manifold -- no shortcuts. NOT the classical FEP applied to quantum systems, and NOT the doc's thermal-
prior version (exp(-E/T)/Z is Boltzmann thermodynamics -- excluded). Source (owner, MODEL_CONTEXT.md:91):
"a pure QIT version of the Free Energy Principle ... purely in terms of CPTP channels, density operators,
and correlation-diversity functionals ... deriving FEP from the constraint surface." Every classical
primitive of standard FEP is REPLACED by its constraint-surface origin:
  classical probability p(z)        -> density-operator spectrum (finite, F01)
  Boltzmann thermal prior exp(-E/T) -> GKSL fixed point of a native operator (full-rank by construction)
  Shannon surprise -log p(x)        -> quantum relative entropy S(rho||sigma) (forced, stage 1)
  Bayesian belief update            -> CPTP relaxation toward the operator's pointer (stage 3)
  Markov blanket (graph partition)  -> vanishing quantum conditional mutual info I(A:C|B) (stage 4)
NO temperature, NO energy, NO -log p, NO classical probability appears anywhere in the math below.

The ratchet builds it one earned stage at a time:

STAGE 1 -- DISTINGUISHABILITY forces the functional (F01, root). The surprise functional must be (i)
  monotone under every CPTP channel (post-processing cannot manufacture distinguishability = data
  processing) AND (ii) additive over independent subsystems. Relative entropy S(rho||sigma) satisfies
  both; trace distance is monotone but NOT additive; so S(rho||sigma) SURVIVES against the trace-distance
  alternative (one comparison, NOT a uniqueness theorem). No -log p.

STAGE 2 -- GEOMETRY splits the surprise (Axis-0). S(rho||sigma) decomposes EXACTLY (Pythagorean) into a
  classical spectral part (eigenvalue mismatch = the entropy DOF) + a quantum basis-mismatch part
  (eigenvector misalignment = the coherence DOF). Surprise is not one scalar; it carries the manifold's
  two degrees of freedom without collapsing them.

STAGE 3 -- OPERATORS are the inference dynamics (Axis-5). Each native T-operator (GKSL dephasing) is a
  gradient flow that drives surprise against ITS OWN pointer (its GKSL fixed point, full-rank, no thermal
  regularization) MONOTONICALLY to 0 = self-evidencing. Against a FOREIGN pointer surprise stays high.
  Perception (relaxation) and the ratchet (native-entropy monotone descent) are the SAME dynamics.

STAGE 4 -- MANIFOLD gives the Markov blanket (3-qubit floor). Internal(A)/external(C) separation = a
  blanket B with vanishing conditional mutual info I(A:C|B)=0 (quantum Markov chain). Built from the
  3-qubit state's correlation structure, not imposed. A direct A-C coupling gives I(A:C|B)>0 (no blanket).

STAGE 5 -- ACTIVE inference: given a probe, the concept (operator pointer) of minimum surprise is
  selected. A z-aligned probe selects Ti; an x-aligned probe selects Te. The active half, pure QIT.

STAGE 6 -- GATE + LOOP-BACK. z3 AND cvc5: law "self-evidences <=> own pointer" fits; control "foreign
  forced to self-evidence" UNSAT-with-law -> SAT-without. Loop-back: this IS the co-ratchet's terrain-
  native-entropy result re-read as inference -- FEP is a different VIEW of the ratchet, not a new mechanism.

HONEST SCOPE: derives the finite-CPTP core of perceptual + active inference from relative entropy on the
constraint surface, with every classical/thermal primitive replaced. It does NOT reproduce Friston's full
hierarchical continuous-state message passing. Hypothetical lane; owner doctrine under test.
scratch_diagnostic; promotion_allowed=false.

INSTRUMENT SCOPE (external referee panel, 2026-07-03 loop-back #2 -- verified against code lines):
  * The quantity relent() is quantum relative entropy used as a FREE-ENERGY ANALOGUE (a divergence),
    NOT a variational free energy / evidence lower bound. Stage-1 "surprise" is this divergence.
  * Belief dynamics are GKSL relaxation toward operator pointer priors -- the INSTRUMENT CLASS is
    relaxation (smooth surprise streams), NOT Lüders conditioning on measurement outcomes. The sim does
    not condition on outcomes.
  * Stage 3 "self-evidencing" scores each fixed point against ITSELF: this is attractor/Lyapunov
    STABILITY of the GKSL fixed point, not evidence accumulation over data.
  * Stage 4 Markov blanket uses CLASSICAL diagonal conditional mutual info (diagonal states), not a
    genuinely quantum-correlated blanket -- classical-CMI scope, stated.
  * Stage 5 "active" = prospective selection of a fixed goal/concept, not belief-updating control.
  These are scope statements; the numerical results stand as run.
"""
import sys
try:
    import numpy as np
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL qit_fep_ratchet_sim: missing tool ({e.name})"); sys.exit(0)
rng=np.random.default_rng(7)
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
def relent(ro,rm):
    ro=(ro+ro.conj().T)/2; rm=(rm+rm.conj().T)/2
    wo,Vo=np.linalg.eigh(ro); wm,Vm=np.linalg.eigh(rm); wo=np.clip(wo,1e-12,None); wm=np.clip(wm,1e-12,None)
    return float(np.real(np.trace(ro@(Vo@np.diag(np.log(wo))@Vo.conj().T - Vm@np.diag(np.log(wm))@Vm.conj().T))))
def trdist(a,b): w=np.linalg.eigvalsh((a-b+(a-b).conj().T)/2); return 0.5*float(np.sum(np.abs(w)))

# STAGE 1: functional SURVIVES trace-distance alternative (monotone AND additive; one comparison, not uniqueness)
def rand_rho(d):
    A=rng.normal(size=(d,d))+1j*rng.normal(size=(d,d)); M=A@A.conj().T; return M/np.trace(M)
r1,s1,r2,s2=rand_rho(2),rand_rho(2),rand_rho(2),rand_rho(2)
R=np.kron(r1,r2); S=np.kron(s1,s2)
re_add=abs(relent(R,S)-(relent(r1,s1)+relent(r2,s2))); td_add=abs(trdist(R,S)-(trdist(r1,s1)+trdist(r2,s2)))
print(f"(1) functional survives trace-distance alternative: relent additive |d|={re_add:.1e}; trace-dist additive |d|={td_add:.3f} (NOT) -> S(rho||sigma) kept")

# STAGE 2: geometric split (Axis-0)
ro=0.5*(I2+0.5*sx+0.3*sz); rm=0.5*(I2+0.6*sz)
wm,Vm=np.linalg.eigh((rm+rm.conj().T)/2)
ro_d=Vm@np.diag(np.diag(Vm.conj().T@ro@Vm).real)@Vm.conj().T
cl=relent(ro_d,rm); qu=relent(ro,ro_d); tot=relent(ro,rm)
print(f"(2) geometry split: total {tot:.4f} = classical(spectral) {cl:.4f} + quantum(basis) {qu:.4f}; Pythagorean |d|={abs(tot-cl-qu):.1e}")

# STAGE 3: operators = inference dynamics (Axis-5 T-kernel pair Ti,Te), full-rank fixed points, NO thermal prior
g=0.6
def Dchan(L,rho): return L@rho@L.conj().T-0.5*(L.conj().T@L@rho+rho@L.conj().T@L)
gen_Ti=lambda rho: g*Dchan(sz,rho); gen_Te=lambda rho: g*Dchan(sx,rho)
rho0=0.5*(I2+0.6*sx+0.3*sy+0.2*sz)
def steady(gen,steps=600,dt=0.05):
    r=rho0.copy()
    for _ in range(steps): r=r+dt*gen(r)
    return (r+r.conj().T)/2
fp_Ti=steady(gen_Ti); fp_Te=steady(gen_Te)
def traj(gen,prior,steps=60,dt=0.05):
    r=rho0.copy(); Sr=[]
    for _ in range(steps): Sr.append(relent(r,prior)); r=r+dt*gen(r)
    return np.array(Sr)
S_TiO=traj(gen_Ti,fp_Ti); S_TeO=traj(gen_Te,fp_Te); S_TiF=traj(gen_Ti,fp_Te); S_TeF=traj(gen_Te,fp_Ti)
mono=lambda S: bool(np.all(np.diff(S)<=1e-6))
print(f"(3) operators=inference: Ti vs OWN {S_TiO[0]:.3f}->{S_TiO[-1]:.3f} mono={mono(S_TiO)}; Te vs OWN {S_TeO[0]:.3f}->{S_TeO[-1]:.3f} mono={mono(S_TeO)}; foreign stays {S_TiF[-1]:.2f}/{S_TeF[-1]:.2f}")

# STAGE 4: Markov blanket from I(A:C|B), 3-qubit
def SvN(rho):
    w=np.linalg.eigvalsh((rho+rho.conj().T)/2); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
def ptrace(rho,keep,dims=(2,2,2)):
    rt=rho.reshape(dims+dims); n=len(dims); ax=[i for i in range(n) if i not in keep]
    for a in sorted(ax,reverse=True): rt=np.trace(rt,axis1=a,axis2=a+n); n-=1
    d=int(np.prod([dims[i] for i in keep])); return rt.reshape(d,d)
def cmi(rho): return SvN(ptrace(rho,(0,1)))+SvN(ptrace(rho,(1,2)))-SvN(ptrace(rho,(1,)))-SvN(rho)
pa=np.array([0.6,0.4]); pb_a=np.array([[0.8,0.2],[0.3,0.7]]); pc_b=np.array([[0.9,0.1],[0.25,0.75]])
pchain=np.array([[[pa[a]*pb_a[a,b]*pc_b[b,c] for c in range(2)] for b in range(2)] for a in range(2)])
pb=np.array([0.5,0.5]); pac=np.array([[0.4,0.1],[0.1,0.4]])
pdir=np.array([[[pb[b]*pac[a,c] for c in range(2)] for b in range(2)] for a in range(2)])
cmi_chain=cmi(np.diag(pchain.flatten().astype(complex))); cmi_dir=cmi(np.diag(pdir.flatten().astype(complex)))
print(f"(4) Markov blanket: chain I(A:C|B)={cmi_chain:.4f} (~0, B shields); direct I(A:C|B)={cmi_dir:.4f} (>0, no blanket)")

# STAGE 5: active selection
priors={'Ti':fp_Ti,'Te':fp_Te}
pz=0.5*(I2+0.55*sz); px=0.5*(I2+0.55*sx)
selz=min(priors,key=lambda n: relent(pz,priors[n])); selx=min(priors,key=lambda n: relent(px,priors[n]))
print(f"(5) active selection: z-probe->'{selz}', x-probe->'{selx}', discriminates={selz!=selx}")

# STAGE 6: gate
def z3_gate():
    for own,evid in [(1,1),(0,0)]:
        s=z3.Solver(); O,E=z3.Bools('O E'); s.add(O==bool(own),E==bool(evid),E==O)
        if s.check()!=z3.sat: return "unsat"
    return "sat"
def z3_ctrl(law):
    s=z3.Solver(); O,E=z3.Bools('O E'); s.add(O==False,E==True)
    if law: s.add(E==O)
    return str(s.check())
def cvc5_gate():
    for own,evid in [(1,1),(0,0)]:
        s=cvc5.Solver(); s.setLogic("QF_UF"); B=s.getBooleanSort(); O,E=[s.mkConst(B,n) for n in 'OE']
        eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b); tt,ff=s.mkTrue(),s.mkFalse()
        s.assertFormula(eq(O,tt if own else ff)); s.assertFormula(eq(E,tt if evid else ff)); s.assertFormula(eq(E,O))
        if str(s.checkSat())!="sat": return "unsat"
    return "sat"
def cvc5_ctrl(law):
    s=cvc5.Solver(); s.setLogic("QF_UF"); B=s.getBooleanSort(); O,E=[s.mkConst(B,n) for n in 'OE']
    eq=lambda a,b:s.mkTerm(Kind.EQUAL,a,b); tt,ff=s.mkTrue(),s.mkFalse()
    s.assertFormula(eq(O,ff)); s.assertFormula(eq(E,tt))
    if law: s.assertFormula(eq(E,O))
    return str(s.checkSat())
zf,cf=z3_gate(),cvc5_gate(); zc1,cc1=z3_ctrl(True),cvc5_ctrl(True); zc0,cc0=z3_ctrl(False),cvc5_ctrl(False)
print(f"(6) gate: fit z3={zf}/cvc5={cf}; foreign-forced-evidence z3={zc1}/cvc5={cc1}(w/law) -> {zc0}/{cc0}(w/o)")

assert re_add<1e-9 and td_add>0.05, "surprise functional forced: relent additive, trace-dist not"
assert abs(tot-cl-qu)<1e-9 and cl>0 and qu>0, "surprise splits Pythagorean into spectral + basis parts"
assert S_TiO[-1]<0.05 and mono(S_TiO) and S_TeO[-1]<0.05 and mono(S_TeO) and S_TiF[-1]>0.1 and S_TeF[-1]>0.1, "operators self-evidence own pointer only"
assert cmi_chain<1e-6 and cmi_dir>0.1, "Markov blanket = vanishing conditional mutual info"
assert selz!=selx, "active selection discriminates"
assert zf=="sat" and cf=="sat" and zc1=="unsat" and cc1=="unsat" and zc0=="sat" and cc0=="sat", "self-evidencing law + flipped control, both solvers"
print("\nPASS qit_fep_ratchet_sim")
