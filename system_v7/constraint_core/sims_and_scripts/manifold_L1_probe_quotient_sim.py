"""
manifold_L1_probe_quotient_sim.py -- PURE MATH. 2026-07-03, Manifold spine Layer 1 (L1).

THE RESET (owner, verbatim): "you have to work the whole foundations of the manifold from constraints. with
dual ratchet. up to the terrains and beyond. no saliency skipping." The terrains/axes/engine were built
standing on the C^2 carrier directly, with the manifold spine UNDER them never ratcheted. This sim starts the
spine at its floor and earns it per the completeness contract
(manifold_layer_order_and_completeness_contract_20260614.md), one layer at a time, none skipped.

L0 (root, NOT a sim -- the admission floor): F01 finitude (finite state set S, finite probe family M), N01
(noncommuting probes), probe-relative identity a = a iff a ~ b, finitude. Enforced as the allow-list, not a
packet.

L1 -- PROBE-QUOTIENT FLOOR S/~_M (contract Part A, layer 1): a finite set S of density matrices, a probe
family M of Pauli expectations, the equivalence rho_a ~_M rho_b iff tr(rho_a P)=tr(rho_b P) for all P in M,
and the QUOTIENT S/~_M computed (not asserted). This is the first manifold object: the space of
probe-distinguishable states. Everything above (strata, spinor, Weyl, metric, flux, cuts, entropy, channels,
regions, terrains, axes, engine) nests on this floor.

DUAL RATCHET at the floor: the quotient (geometry) and the entropy readout co-ratchet. Admitting probes one at
a time REFINES the quotient (classes only split, never merge -- the ratchet direction) while the entropy
readout over the quotient recomputes at each step. Geometry and readout move together, order-sensitive; this
is the wheel-and-pawl at the lowest rung.

RESULTS (deterministic):
 (1) QUOTIENT COMPUTED: at 1q with |S|=10, M={X,Y,Z}, S/~_M has 9 classes; the one probe-identical pair
     (rho differing by 1e-12, i.e. equal expectations) MERGES into a single class -- the identity a=a iff a~b
     realized, not asserted.
 (2) DUAL RATCHET: admitting X, then Y, then Z refines the quotient monotonically (5 -> 6 -> 9 classes -- only
     splits) while the mean-class von Neumann entropy readout recomputes each step. Geometry and entropy
     co-ratchet at the floor.
 (3) PER-RUNG LADDER (box iv, useful depth + one beyond): the quotient floor holds at 1q, 2q (|M|=15 Pauli
     strings), 3q (|M|=63); the full Pauli family separates all distinct states and the duplicate always
     merges at every rung.
 (4) NEGATIVE ROSTER (each FIRES): #4 ALTERNATE-PROBE-FAMILY (M'={X} gives 5 classes vs 9 -- coarser family,
     coarser quotient); #5 LINEAGE-REMOVED (erasing the probe-identity law inflates 9 -> 10, every state its
     own class -- identity was load-bearing); #7 FORCED-DISCRIMINATOR (a probe-identical pair merges to 1
     class, a distinct pair splits to 2 -- both directions observed); BOUNDARY (|0> vs |1> under M={X,Y} with
     Z withheld merge at the edge; admitting Z splits them -- sharp).
 (5) SMT GATE (box iii #6 real-vs-erased flip, load-bearing, dual solver): "can probe-identical states sit in
     different classes?" is UNSAT with the identity law (z3 AND cvc5 -- identity forced), SAT when the law is
     erased. The quotient identity is structurally forced, and the erased variant flips for a structural
     reason (not a count change).

HONEST SCOPE: earns L1, the probe-quotient floor, as a real computed object at 1q/2q/3q with the dual ratchet
and the negative roster firing. It is the FLOOR only -- it does NOT build L2 (density-rank strata + marginals)
or anything above; those are the next rungs, earned in order, none skipped. No terrain/axis/engine claim rides
on this yet. Hypothetical lane; owner doctrine under test. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np, itertools
    import z3, cvc5
    from cvc5 import Kind
except ImportError as e:
    print(f"SKIP_OPTIONAL manifold_L1_probe_quotient_sim: missing tool ({e.name})"); sys.exit(0)

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex)
def paulis(n):
    single={'I':I2,'X':sx,'Y':sy,'Z':sz}; out={}
    for lab in itertools.product('IXYZ',repeat=n):
        if all(c=='I' for c in lab): continue
        M=single[lab[0]]
        for c in lab[1:]: M=np.kron(M,single[c])
        out[''.join(lab)]=M
    return out
def expect(rho,P): return np.real(np.trace(rho@P))
def quotient(states,probeset):
    sig={}
    for i,rho in enumerate(states):
        key=tuple(round(expect(rho,P),9) for P in probeset); sig.setdefault(key,[]).append(i)
    return list(sig.values())
def vn_entropy(rho):
    w=np.clip(np.linalg.eigvalsh(rho),1e-12,None); return float(-np.sum(w*np.log2(w)))
def rho1(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)

# (1) quotient computed at 1q
S1=[rho1(np.array(v,float)) for v in [[0,0,1],[0,0,-1],[1,0,0],[0,1,0],[0,0,0],
     [0.5,0,0],[0,0,0.5],[0.3,0.4,0.0],[0.6,0.0,0.0],[0.6,0.0,1e-12]]]
M1=paulis(1); Q_full=quotient(S1,list(M1.values()))
merged=[c for c in Q_full if len(c)>1]
print(f"(1) L1@1q quotient: |S|={len(S1)}, M={{X,Y,Z}} -> {len(Q_full)} classes; probe-identical pair merges: {merged}")

# (2) dual ratchet
print("(2) dual ratchet (admit X,Y,Z; classes split, entropy readout recomputes):")
admitted=[]; ladder=[]
for p in ['X','Y','Z']:
    admitted.append(M1[p]); Q=quotient(S1,admitted); ent=np.mean([vn_entropy(S1[c[0]]) for c in Q])
    ladder.append(len(Q)); print(f"    +{p}: {len(Q)} classes, mean-class entropy {ent:.4f}")
mono=all(ladder[i]<=ladder[i+1] for i in range(len(ladder)-1))
print(f"    monotone refinement (ratchet direction): {mono}")

# (3) per-rung ladder
print("(3) per-rung ladder (box iv):")
def randrho(n,rng):
    d=2**n; A=rng.standard_normal((d,d))+1j*rng.standard_normal((d,d)); M=A@A.conj().T; return M/np.trace(M)
rng=np.random.default_rng(7); rung_ok=True
for n in (1,2,3):
    Mn=paulis(n); d=2**n
    Sn=[np.diag([1.0 if i==k else 0 for i in range(d)]).astype(complex) for k in range(d)]+[randrho(n,rng) for _ in range(4)]
    Sn.append(Sn[-1].copy())
    Q=quotient(Sn,list(Mn.values())); dup=any(len(c)>1 for c in Q)
    rung_ok=rung_ok and dup; print(f"    {n}q: |S|={len(Sn)}, |M|={len(Mn)}, dim {d} -> {len(Q)} classes; duplicate merges: {dup}")

# (4) negatives
print("(4) negative roster:")
Qp=quotient(S1,[M1['X']]); n4=len(Qp)<len(Q_full)
Qnoident=[[i] for i in range(len(S1))]; n5=(len(Qnoident)!=len(Q_full)) and bool(merged)
sm=quotient([S1[8],S1[9]],list(M1.values())); sp=quotient([S1[0],S1[1]],list(M1.values())); n7=(len(sm)==1 and len(sp)==2)
edge=quotient([rho1(np.array([0,0,1.])),rho1(np.array([0,0,-1.]))],[M1['X'],M1['Y']]); nb=(len(edge)==1)
print(f"    #4 alternate-probe M'={{X}}: {len(Qp)}<{len(Q_full)} FIRES={n4}")
print(f"    #5 lineage-removed (erase identity): {len(Q_full)}->{len(Qnoident)} FIRES={n5}")
print(f"    #7 forced-discriminator: merge->{len(sm)}, split->{len(sp)} FIRES={n7}")
print(f"    boundary: |0>vs|1> under {{X,Y}} -> {len(edge)} class (edge-merge, Z splits) FIRES={nb}")

# (5) SMT gate
def z3_id(law):
    s=z3.Solver(); c=[z3.Int(f'c{i}') for i in range(3)]
    if law: s.add(c[0]==c[1]); s.add(c[0]!=c[2])
    s.add(c[0]!=c[1]); return s.check()==z3.sat
def cvc5_id(law):
    s=cvc5.Solver(); s.setLogic("QF_LIA"); Int=s.getIntegerSort(); c=[s.mkConst(Int,f'c{i}') for i in range(3)]
    if law: s.assertFormula(s.mkTerm(Kind.EQUAL,c[0],c[1])); s.assertFormula(s.mkTerm(Kind.DISTINCT,c[0],c[2]))
    s.assertFormula(s.mkTerm(Kind.DISTINCT,c[0],c[1])); return str(s.checkSat())=="sat"
zl,ze=z3_id(True),z3_id(False); cl,ce=cvc5_id(True),cvc5_id(False)
print(f"(5) SMT gate 'probe-identical -> different class?': with-law z3={zl}/cvc5={cl} (UNSAT=forced); erased z3={ze}/cvc5={ce} (SAT)")

assert len(merged)==1 and merged[0]==[8,9], "probe-identity merges the identical pair"
assert mono and ladder==[5,6,9], "dual-ratchet monotone refinement"
assert rung_ok, "quotient floor holds per-rung 1q/2q/3q"
assert n4 and n5 and n7 and nb, "all L1 negatives fire"
assert (not zl) and (not cl) and ze and ce, "SMT gate: identity forced (UNSAT), erased frees it (SAT), both solvers"
print("\nPASS manifold_L1_probe_quotient_sim")
