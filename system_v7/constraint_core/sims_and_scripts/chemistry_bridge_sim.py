"""
chemistry_bridge_sim.py -- the CHEMICAL BOND from the constraint core's axioms, via the
HUBBARD DIMER: the minimal exactly-solvable model of a covalent bond (the "H2 molecule" of
quantum chemistry). NOT a ToE validation -- a check that the engine's axioms reproduce
established quantum chemistry.

Ties three axioms to chemistry:
  * NONCOMMUTATION -> fermionic anticommutation {c_i, c_j^dag} = delta_ij, i.e. PAULI
    EXCLUSION. Enforced exactly via Jordan-Wigner (all fermion signs exact to 0).
  * The bond is a SPIN SINGLET (S^2 = 0) at every interaction strength -- forced by the
    antisymmetry of the two-electron wavefunction.
  * The chemical BOND IS ENTANGLEMENT -- the site-1 reduced state has S > 0 for all U; the
    two atoms are non-separable. Limits: S(site1) = 2 bits at U=0 (charge+spin fluctuations)
    -> 1 bit at U>>t (pure spin entanglement, Heitler-London / Mott localized limit).
  * COVALENT -> IONIC crossover: double occupancy <n_up n_dn> = 0.25 at U=0 -> 0 at U>>t.

H = -t sum_s (c1s^dag c2s + h.c.) + U sum_i n_iup n_idn ; ground state in N=2, Sz=0.
Ground energy matches the exact analytic singlet (U - sqrt(U^2 + 16 t^2))/2.
numpy-only. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL chemistry_bridge_sim: missing tool ({e.name})"); sys.exit(0)

I2=np.eye(2); Zp=np.array([[1,0],[0,-1]],float); sm=np.array([[0,0],[1,0]],float)
def op_on(k,local,nm=4):
    mats=[Zp]*k+[local]+[I2]*(nm-k-1); out=mats[0]
    for m in mats[1:]: out=np.kron(out,m)
    return out
c=[op_on(k,sm) for k in range(4)]; cd=[m.T.conj() for m in c]; n=[cd[k]@c[k] for k in range(4)]
def anticomm(a,b): return a@b+b@a
def H(t,U):
    return (-t*(cd[0]@c[2]+cd[2]@c[0]+cd[1]@c[3]+cd[3]@c[1]) + U*(n[0]@n[1]+n[2]@n[3]))
Sp=cd[0]@c[1]+cd[2]@c[3]; Szop=0.5*(n[0]+n[2]-n[1]-n[3])
S2=Sp.T.conj()@Sp + Szop@Szop + Szop; Nt=sum(n)
def S_bits(rho):
    w=np.linalg.eigvalsh(rho); w=w[w>1e-12]; return float(-np.sum(w*np.log2(w)))
def gs(t,U):
    w,v=np.linalg.eigh(H(t,U))
    for idx in np.argsort(w):
        psi=v[:,idx]
        if abs(psi.conj()@Nt@psi-2)<1e-6 and abs(psi.conj()@Szop@psi)<1e-6: return w[idx],psi
def rdm1(psi):
    T=psi.reshape(2,2,2,2); return np.einsum('abij,cdij->abcd',T,T.conj()).reshape(4,4)

# (0) fermionic algebra exact
maxoff=max(np.abs(anticomm(c[i],cd[j])-(np.eye(16) if i==j else 0)).max() for i in range(4) for j in range(4))
print(f"(0) fermionic {{c_i,c_j^dag}}=delta_ij exact to {maxoff:.1e} (noncommutation->Pauli)")
t=1.0; rows=[]
print("(1-3) Hubbard dimer ground state vs U/t:")
for U in [0.0,1.0,2.0,4.0,8.0,20.0]:
    E,psi=gs(t,U); Ean=(U-np.sqrt(U**2+16*t**2))/2
    s2=(psi.conj()@S2@psi).real; Sent=S_bits(rdm1(psi)); docc=(psi.conj()@(n[0]@n[1])@psi).real
    rows.append((U,E,Ean,s2,Sent,docc))
    print(f"    U/t={U:>4.1f}: E={E:+.5f} (exact {Ean:+.5f}) S^2={s2:.2e} S(site1)={Sent:.4f}b <docc>={docc:.4f}")

assert maxoff<1e-12, "fermionic anticommutation must be exact"
assert all(abs(E-Ean)<1e-6 for _,E,Ean,_,_,_ in rows), "E_gs must match analytic singlet"
assert all(abs(s2)<1e-6 for *_,s2,_,_ in [(r[0],r[1],r[2],r[3],r[4],r[5]) for r in rows]), "must be spin singlet"
assert all(Sent>1e-6 for *_,Sent,_ in [(r[0],r[1],r[2],r[3],r[4],r[5]) for r in rows]), "bond is entanglement"
assert rows[0][5]>0.24 and rows[-1][5]<0.01, "covalent->ionic crossover in double occupancy"
assert abs(rows[0][4]-2.0)<1e-6, "U=0 limit S(site1)=2 bits (charge+spin)"
print("\nPASS chemistry_bridge_sim")
