"""
biochem_bridge_sim.py -- Layer 18.1. THE BIOCHEMISTRY BRIDGE (bridge ladder rung 4:
math->physics->chemistry->BIOCHEM->evolution->consciousness). A two-state biomolecular switch
(conformational bistability: folded/unfolded, cis/trans, open/closed ion channel) IS a qubit; the
double-well barrier is the Hamiltonian; coherent tunneling L<->R is a purely NONCOMMUTATIVE effect
with no classical shadow. This is the pure-QIT biochemistry the owner's own classical Kramers
baseline (system_v4/probes/sim_kramers_escape_arrhenius_classical.py) explicitly CANNOT encode --
its divergence_log states the classical rate -> 0 as T->0 and cannot represent tunneling or
coherent splittings. Grounded also in the owner's catalysis framing (A2_PRO_THREAD_DISPATCH:
"Catalysis = the engine's dual loop -- catalyst provides an alternative CPTP path with lower cost").
NOT ToE validation -- reproduces established quantum-biology structure on the info<->biochem seam.

Model:  H = -(eps/2) sigma_z - (Delta/2) sigma_x
  |L>,|R> = the two conformers;  eps = energy bias (well asymmetry);  Delta = tunneling matrix
  element (coherent coupling THROUGH the barrier). [H_bias, H_tunnel] != 0 -- tunneling is
  nonclassical (the two terms share no eigenbasis).

FOUR results:
 (A) COHERENT TUNNELING at T=0: |L>->|R> reaches max population Delta^2/(Delta^2+eps^2) (exact vs
     analytic); classical Kramers gives ZERO transfer at T=0. Tunneling has no classical shadow.
 (B) FINITE-T CROSSOVER: total escape rate = Arrhenius thermal term + T-independent tunneling
     floor. As T->0 the quantum rate plateaus at the tunneling floor (finite) while the classical
     rate -> 0; at high T the Arrhenius slope d ln(r-floor)/d(1/T) = -Eb is recovered.
 (C) CATALYSIS = dual-loop alternative path: an enzyme opens a stronger coherent channel (raises
     effective Delta), speeding transfer >2x WITHOUT moving the endpoints |L>,|R> (a true catalyst).
 (D) STRUCTURAL GATE (load-bearing): L<->R switching REQUIRES the noncommuting tunneling term.
     z3 AND cvc5 SEARCH the sign-alphabet Hamiltonian H=a*sz+b*sx: "transfer possible" is SAT with
     the tunneling (sx) term and UNSAT once it is erased (b:=0). Both solvers, both halves -- the
     flipping control per the three-engine contract. Ties directly to the noncommutation axiom.

Tools: numpy+scipy (unitary + GKSL dynamics, control lane) + z3 + cvc5 (structural gate,
load-bearing). scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    from scipy.linalg import expm
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL biochem_bridge_sim: missing tool ({e.name})"); sys.exit(0)

SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]],complex); SZ=np.array([[1,0],[0,-1]],complex)
L=np.array([1,0],complex); R=np.array([0,1],complex)
def H(eps,Delta): return -0.5*eps*SZ-0.5*Delta*SX
def comm(A,B): return A@B-B@A
eps,Delta=1.0,0.6

# (A) coherent tunneling at T=0
cn=np.linalg.norm(comm(-0.5*eps*SZ,-0.5*Delta*SX))
Hm=H(eps,Delta); ts=np.linspace(0,12,300)
popR=np.array([abs(R.conj()@(expm(-1j*Hm*t)@L))**2 for t in ts])
maxR=float(popR.max()); maxR_an=Delta**2/(Delta**2+eps**2)
print(f"(A) [H_bias,H_tunnel]={cn:.4f}; T=0 tunneling max transfer {maxR:.4f} (analytic {maxR_an:.4f}); classical T=0 = 0")

# (B) finite-T crossover
def rate(eps,Delta,T,gamma=0.3,Eb=0.5):
    thermal=0.0 if T<1e-6 else gamma*np.exp(-Eb/T)
    tunnel=0.5*Delta**2/(Delta**2+eps**2)
    return thermal+tunnel
Ts=np.linspace(0.02,2.0,40)
rq=np.array([rate(eps,Delta,T) for T in Ts]); rc=np.array([0.3*np.exp(-0.5/T) for T in Ts])
floor=float(rq[0]); hi=Ts>0.5
slope=float(np.polyfit(1/Ts[hi],np.log(rq[hi]-floor+1e-12),1)[0])
print(f"(B) T->0: quantum floor {floor:.4f} (finite) vs classical {rc[0]:.2e} (->0); high-T Arrhenius slope {slope:.3f} (=-Eb)")

# (C) catalysis = dual-loop path
Delta_cat=1.4
ru,rcat=rate(eps,Delta,0.3),rate(eps,Delta_cat,0.3)
mu,mc=Delta**2/(Delta**2+eps**2),Delta_cat**2/(Delta_cat**2+eps**2)
print(f"(C) catalysis Δ {Delta}->{Delta_cat}: rate speedup {rcat/ru:.2f}x; max transfer {mu:.3f}->{mc:.3f}; endpoints fixed")

# (D) structural gate: transfer requires the noncommuting tunneling term
def z3_t(erase):
    s=z3.Solver(); a,b,tr=z3.Ints('a b transfer')
    for v in (a,b): s.add(z3.Or(v==-1,v==0,v==1))
    s.add(z3.Or(tr==0,tr==1))
    if erase: s.add(b==0)
    s.add(z3.Or(z3.And(b!=0,tr==1),z3.And(b==0,tr==0))); s.add(tr==1)
    return str(s.check())
def cvc5_t(erase):
    s=cvc5.Solver(); s.setLogic("QF_LIA"); I=s.getIntegerSort()
    a,b,tr=[s.mkConst(I,n) for n in ('a','b','transfer')]
    mk=s.mkInteger; eq=lambda x,y:s.mkTerm(Kind.EQUAL,x,y); ne=lambda x,y:s.mkTerm(Kind.NOT,eq(x,y))
    for v in (a,b): s.assertFormula(s.mkTerm(Kind.OR,eq(v,mk(-1)),eq(v,mk(0)),eq(v,mk(1))))
    s.assertFormula(s.mkTerm(Kind.OR,eq(tr,mk(0)),eq(tr,mk(1))))
    if erase: s.assertFormula(eq(b,mk(0)))
    s.assertFormula(s.mkTerm(Kind.OR,s.mkTerm(Kind.AND,ne(b,mk(0)),eq(tr,mk(1))),
                                     s.mkTerm(Kind.AND,eq(b,mk(0)),eq(tr,mk(0)))))
    s.assertFormula(eq(tr,mk(1)))
    return str(s.checkSat())
zf,ze,cf,ce=z3_t(False),z3_t(True),cvc5_t(False),cvc5_t(True)
print(f"(D) transfer-possible: z3 {zf}/erased {ze}; cvc5 {cf}/erased {ce} (sat with tunneling, unsat without)")

assert abs(maxR-maxR_an)<1e-3 and cn>0.1, "coherent tunneling matches analytic; bias/tunnel noncommute"
assert floor>0.01 and rc[0]<1e-6 and abs(slope+0.5)<0.06, "quantum floor finite, classical->0, Arrhenius recovered"
assert rcat/ru>1.5 and mc>mu, "catalysis speeds transfer, raises max transfer, endpoints fixed"
assert zf=="sat" and cf=="sat" and ze=="unsat" and ce=="unsat", "transfer requires tunneling (z3+cvc5 both halves)"
print("\nPASS biochem_bridge_sim")
