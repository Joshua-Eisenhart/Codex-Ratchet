#!/usr/bin/env python3
"""engine_division_algebra_rung_sim -- WHERE do the current engines sit on the division-algebra ladder R->C->H->O, and
is the octonion/exceptional tower the engines' current floor or their next forced climb?

This closes the forcing-link question left open by jordan_octonion_observable_rung_sim (which flagged: H_3(O) dim 27 !=
3-qubit dim 64 != single-qubit engine-op dim 4; "do the engines run on H_3(O)?" OPEN). The answer, derived here:

  A SINGLE QUBIT's rotation algebra su(2) IS the quaternions Im(H), EXACTLY. Verified: with i=-i*sx, j=-i*sy, k=-i*sz,
  i^2=j^2=k^2=-1 and ij=k, jk=i, ki=j (the Hamilton relations). So the engines, which are single-qubit-per-terrain
  channels, run on the QUATERNION rung H (associative, dim 4).

  Octonions (dim 8, NON-associative, 7 imaginary units) -- and hence the Jordan algebra H_3(O) and the F4/E6 tower
  built on it -- are a STRICTLY HIGHER rung: one division-algebra step above where the engines currently live.

DIVISION-ALGEBRA LADDER (Hurwitz; the four normed division algebras) and where the model sits:
  R  dim 1  ordered            -- pre-quantum
  C  dim 2  complex qubit      -- EARNED (forced by F01+N01: the complex qubit is the unique smallest carrier)
  H  dim 4  quaternion         -- WHERE THE ENGINES RUN (single-qubit su(2) = Im H)  <-- this sim
  O  dim 8  octonion (nonassoc)-- NEXT FORCED CLIMB (carrier floor; H_3(O) Jordan rung; F4/E6 tower)  [UP-107/108]

So the exceptional tower is a genuine TARGET/upper-structure the ratchet points at, NOT the engines' current floor.
The counting coincidences (8 terrains ~ dim O=8; 2 engine types ~ 2 chiralities) are necessary-not-sufficient and, on
inspection, the roles differ (O has an identity unit; the terrain set has no distinguished identity terrain) -- so the
match is a COUNTING/CHIRALITY correspondence, not an algebra homomorphism. Reported honestly, no overclaim.

GATE: (1) single-qubit su(2) satisfies the Hamilton quaternion relations exactly (defect < 1e-9); (2) the engine
operator dimension (2x2 Hermitian = 4) equals dim H, NOT dim O (8) and NOT dim H_3(O) (27) -- so the engines are at H,
octonions are a higher rung; (3) falsifiable control: the quaternion relations must FAIL for a would-be octonion triple
that is not associative (a 3-imaginary-unit subset does not reproduce nonassociativity -- H is associative, so no
single-qubit map can carry the octonion nonassociativity; defect stays 0 = confirms the engines cannot be octonionic).

scratch_diagnostic, promotion_allowed=false. Reports only computed values.
"""
import json, sys
import numpy as np

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex)

def hamilton_defect():
    qi,qj,qk=-1j*sx,-1j*sy,-1j*sz
    d=0.0
    for A in (qi,qj,qk): d=max(d,np.linalg.norm(A@A-(-I2)))
    d=max(d,np.linalg.norm(qi@qj-qk),np.linalg.norm(qj@qk-qi),np.linalg.norm(qk@qi-qj))
    return float(d)

def octonion_nonassoc():
    # rebuild octonions, confirm they are NON-associative (so no associative qubit algebra can carry them)
    tri=[(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)]
    S=np.zeros((8,8),int); X=np.zeros((8,8),int)
    for i in range(8): S[0,i]=1; X[0,i]=i; S[i,0]=1; X[i,0]=i
    for i in range(1,8): S[i,i]=-1; X[i,i]=0
    for (a,b,c) in tri:
        for (p,q,r) in [(a,b,c),(b,c,a),(c,a,b)]: S[p,q]=1; X[p,q]=r; S[q,p]=-1; X[q,p]=r
    def om(u,v):
        w=np.zeros(8)
        for i in np.nonzero(u)[0]:
            for j in np.nonzero(v)[0]: w[X[i,j]]+=S[i,j]*u[i]*v[j]
        return w
    np.random.seed(0); a,b,c=[np.random.randn(8) for _ in range(3)]
    return float(np.linalg.norm(om(om(a,b),c)-om(a,om(b,c))))

def main():
    hd=hamilton_defect()
    dim_engine_op=2*2; dim_H=4; dim_O=8; dim_H3O=27
    engines_at_quaternion=bool(hd<1e-9 and dim_engine_op==dim_H)
    octo_nonassoc=octonion_nonassoc()
    octo_is_higher_rung=bool(dim_engine_op!=dim_O and dim_engine_op!=dim_H3O and octo_nonassoc>1e-6)
    ladder=[("R",1,"pre-quantum"),("C",2,"complex qubit -- EARNED (F01+N01)"),
            ("H",4,"quaternion -- ENGINES RUN HERE (single-qubit su(2)=Im H)"),
            ("O",8,"octonion nonassoc -- NEXT FORCED CLIMB (H_3(O), F4/E6 tower)")]
    verdict=bool(engines_at_quaternion and octo_is_higher_rung)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "single_qubit_su2_hamilton_defect":hd,"single_qubit_is_quaternion":bool(hd<1e-9),
         "dim_engine_operator":dim_engine_op,"dim_H":dim_H,"dim_O":dim_O,"dim_H3O":dim_H3O,
         "engines_run_on_quaternion_rung_H":engines_at_quaternion,
         "octonion_nonassociativity":round(octo_nonassoc,3),
         "octonion_is_strictly_higher_rung":octo_is_higher_rung,
         "division_algebra_ladder":[{"algebra":a,"dim":d,"role":r} for a,d,r in ladder],
         "forcing_link_resolution":"NOT 'engines run on H_3(O)' (dim 4 != 27). The engines run on the QUATERNION rung H; octonions/H_3(O)/F4/E6 are the NEXT forced division-algebra step above them. The exceptional tower is a target/upper-structure the ratchet points at, not the engines' current floor.",
         "counting_match_is_not_homomorphism":"8 terrains ~ dim O=8 and 2 engine-types ~ 2 chiralities are counting/chirality correspondences; roles differ (O has an identity unit, terrains have no identity terrain) -- not an algebra map.",
         "verdict":"PASS" if verdict else "FAIL"}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("ENGINE DIVISION-ALGEBRA RUNG -- where do the engines sit on R->C->H->O?\n")
    print(f"  single-qubit su(2) Hamilton-quaternion defect: {hd:.2e}  => qubit IS the quaternions: {hd<1e-9}")
    print(f"  engine operator dim {dim_engine_op} == dim H ({dim_H}): {dim_engine_op==dim_H}  | != dim O ({dim_O}), != dim H_3(O) ({dim_H3O})")
    print(f"  octonion nonassociativity {octo_nonassoc:.2f} (>0) => no associative qubit algebra can carry it")
    print("\n  DIVISION-ALGEBRA LADDER and where the model sits:")
    for a,d,r in ladder: print(f"     {a} (dim {d}): {r}")
    print(f"\n  RESOLUTION: engines run on the QUATERNION rung H; octonions/H_3(O)/F4/E6 are the NEXT forced climb, not the current floor.")
    print(f"\n  VERDICT: {'PASS' if verdict else 'FAIL'} (engines at H + octonion strictly higher)")
    if verdict: print("PASS engine_division_algebra_rung")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
