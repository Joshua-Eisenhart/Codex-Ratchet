"""
no_cloning_sim.py -- the NO-CLONING THEOREM: no unitary copies an unknown quantum state. A
linearity + finitude consequence, and the reason the memory layer can STORE but not DUPLICATE a
state. NOT ToE validation -- established quantum info theory, constructed and measured (not asserted).

Three parts:
  (1) unitarity constraint: a cloner needs <a|b> = <a|b>^2, so |<a|b>| in {0,1}. Only ORTHOGONAL
      (distinguishable) or IDENTICAL states are clonable -- copyable iff classically distinct
      (a=a iff a~b). Non-orthogonal states cannot be cloned by ANY unitary.
  (2) a basis cloner (CNOT) copies |0>,|1> perfectly (fidelity 1) but MANGLES |+> (fidelity 0.5,
      an entangled output, not two copies) -- no universal cloner exists.
  (3) the optimal universal 1->2 qubit cloner (Buzek-Hillery) is CONSTRUCTED explicitly and its
      fidelity MEASURED over the Bloch sphere: F = 5/6 for EVERY input (std ~1e-16). Finitude
      caps duplication fidelity strictly below 1.

Consequence: you cannot beat the data-processing inequality (16.9) by copying first -- no-cloning
is what makes information monotonicity un-cheatable. numpy-only. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL no_cloning_sim: missing tool ({e.name})"); sys.exit(0)

def overlap(a,b): return abs(np.vdot(a,b))
# (1) unitarity constraint
print("(1) cloner unitarity needs <a|b>=<a|b>^2 (=> orthogonal or identical only):")
clonable=[]
for th in [0.0,np.pi/4,np.pi/2,np.pi]:
    a=np.array([1,0],complex); b=np.array([np.cos(th/2),np.sin(th/2)],complex)
    ov=overlap(a,b); ok=abs(ov-ov**2)<1e-9; clonable.append((th,ov,ok))
    print(f"    theta={th:.4f}: |<a|b>|={ov:.4f} consistent={ok}")

# (2) CNOT basis-cloner fails on |+>
CNOT=np.array([[1,0,0,0],[0,1,0,0],[0,0,0,1],[0,0,1,0]],complex)
def cnot_clone(psi): return CNOT@np.kron(psi,np.array([1,0],complex))
def fid_prod(out,psi): return abs(np.vdot(np.kron(psi,psi),out))**2
print("(2) CNOT cloner: perfect on basis, fails on superposition:")
f0=fid_prod(cnot_clone(np.array([1,0],complex)),np.array([1,0],complex))
fp=fid_prod(cnot_clone(np.array([1,1],complex)/np.sqrt(2)),np.array([1,1],complex)/np.sqrt(2))
print(f"    F(|0>)={f0:.4f}  F(|+>)={fp:.4f}")

# (3) Buzek-Hillery universal cloner: constructed + measured
s23,s16=np.sqrt(2/3),np.sqrt(1/6)
def ket(bits): v=np.zeros(8,complex); v[int(bits,2)]=1; return v
out0=s23*ket("000")+s16*(ket("011")+ket("101"))
out1=s23*ket("111")+s16*(ket("010")+ket("100"))
def clone(psi): return psi[0]*out0+psi[1]*out1
def reducedA(state):
    T=state.reshape(2,2,2); rho=np.einsum('abc,ABC->aAbBcC',T,T.conj())
    return np.einsum('aAbbcc->aA',rho)
Fs=[]
for th in np.linspace(0,np.pi,25):
    for ph in np.linspace(0,2*np.pi,25):
        psi=np.array([np.cos(th/2),np.exp(1j*ph)*np.sin(th/2)])
        Fs.append((psi.conj()@reducedA(clone(psi))@psi).real)
print(f"(3) Buzek-Hillery UQCM: <out0|out1>={overlap(out0,out1):.1e}, F mean={np.mean(Fs):.5f} std={np.std(Fs):.1e} (target 5/6={5/6:.5f})")

assert clonable[0][2] and clonable[-1][2], "identical & orthogonal states clonable"
assert not clonable[1][2] and not clonable[2][2], "non-orthogonal states NOT clonable"
assert abs(f0-1.0)<1e-9 and abs(fp-0.5)<1e-9, "CNOT: perfect on basis, 0.5 on |+>"
assert overlap(out0,out1)<1e-9, "BH cloner branches must be orthogonal (unitarity)"
assert np.std(Fs)<1e-6 and abs(np.mean(Fs)-5/6)<1e-6, "universal cloner F=5/6 constant"
print("\nPASS no_cloning_sim")
