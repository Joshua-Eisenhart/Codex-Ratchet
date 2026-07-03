"""
manifold_laws_smt_proof.py -- three more manifold laws proven FORCED, not fitted.
Extends axis_laws_dual_proof.py to the access law, pole-mirror pairing, and the
two-sector theorem. Z3 for the combinatorial claims, sympy for the symbolic identity.

  (1) 8-of-16 access law: given the sheet law (t <-> t+4 opposite Weyl chirality eps=+-1),
      the accessible-stage split is FORCED to 8/8 -- no other split is consistent (Z3 UNSAT
      on any non-4/4 terrain chirality assignment). Left {t0-t3}, Right {t4-t7}, disjoint,
      union 16.
  (2) pole-mirror pairing: the dissipative pairs' fixed_z sum to ~0. FINDING (logged, not
      hidden): zero-sum ALONE is DEGENERATE -- (0,2)(4,6) and (0,4)(2,6) both zero-sum
      because |fixed_z| are near-equal. The pole-mirror pairing (0,4)(2,6) is forced ONLY by
      zero-sum AND cross-sheet (in<->out) together. Documented honestly.
  (3) two-sector theorem (sympy, EXACT): entropy is a function of eigenvalues only, so it is
      IDENTICALLY invariant under any Axis-2 eigenvector rotation. eigs of rho(theta,phi) =
      {p,1-p} for all angles; dS/dtheta = 0 symbolically. Not a 2e-15 numeric -- a symbolic
      identity. This is WHY every entropy readout collapsed to Axis-1 and was blind to Axis-2.

scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import z3
    import sympy as sp
except ImportError as e:
    print(f"SKIP_OPTIONAL manifold_laws_smt_proof: missing tool ({e.name}); pip install z3-solver sympy")
    sys.exit(0)

def prove_access_8of16():
    EPS={0:1,1:1,2:1,3:1,4:-1,5:-1,6:-1,7:-1}
    stages=[(t,o) for t in range(8) for o in range(2)]
    L=[s for s in stages if EPS[s[0]]==1]; R=[s for s in stages if EPS[s[0]]==-1]
    part_ok=(len(L)==8 and len(R)==8 and set(L).isdisjoint(R) and len(set(L)|set(R))==16)
    # Z3: any terrain chirality obeying the sheet law (t<->t+4 opposite) MUST be 4/4 -> 8/8
    e={t:z3.Int(f"e{t}") for t in range(8)}; s=z3.Solver()
    for t in range(8): s.add(z3.Or(e[t]==1,e[t]==-1))
    for t in range(4): s.add(e[t]==-e[t+4])
    s.add(z3.Sum([z3.If(e[t]==1,1,0) for t in range(8)])!=4)
    forced=(s.check()==z3.unsat)
    return part_ok, forced

def prove_pole_mirror():
    FZ={0:0.7127,2:-0.7073,4:-0.7087,6:0.7113}; SHEET={0:'in',2:'in',4:'out',6:'out'}; tol=0.05
    M={"(0,2)(4,6)":[(0,2),(4,6)],"(0,4)(2,6)":[(0,4),(2,6)],"(0,6)(2,4)":[(0,6),(2,4)]}
    zero=[n for n,ps in M.items() if all(abs(FZ[a]+FZ[b])<tol for a,b in ps)]
    both=[n for n,ps in M.items() if all(abs(FZ[a]+FZ[b])<tol for a,b in ps)
          and all(SHEET[a]!=SHEET[b] for a,b in ps)]
    return zero, both

def prove_two_sector():
    p=sp.symbols('p',positive=True); theta,phi=sp.symbols('theta phi',real=True)
    U=sp.Matrix([[sp.cos(theta),-sp.sin(theta)*sp.exp(-sp.I*phi)],
                 [sp.sin(theta)*sp.exp(sp.I*phi),sp.cos(theta)]])
    rho=sp.simplify(U*sp.diag(p,1-p)*U.conjugate().transpose())
    eigs=[sp.simplify(e) for e in rho.eigenvals().keys()]
    same=(set(eigs)=={sp.simplify(p),sp.simplify(1-p)})
    dS=sp.simplify(sp.diff(-sum(e*sp.log(e) for e in eigs),theta))
    return same, (dS==0)

part_ok, access_forced = prove_access_8of16()
print(f"(1) access law: partition 8/8 disjoint union16={part_ok}; non-8/8 split UNSAT={access_forced}")
zero, both = prove_pole_mirror()
print(f"(2) pole-mirror: zero-sum matchings={zero} (DEGENERATE); zero-sum AND cross-sheet={both}")
same, dS0 = prove_two_sector()
print(f"(3) two-sector: eigs(rho(theta,phi))=={{p,1-p}} for all angles={same}; dS/dtheta==0 -> {dS0}")

assert part_ok and access_forced, "8-of-16 must be forced"
assert both==["(0,4)(2,6)"], "pole-mirror uniquely forced by zero-sum AND cross-sheet"
assert len(zero)==2, "the honest finding: zero-sum ALONE is degenerate (2 matchings)"
assert same and dS0, "entropy must be a symbolic identity in eigenvalues (Axis-2 blind)"
print("\nPASS manifold_laws_smt_proof")
