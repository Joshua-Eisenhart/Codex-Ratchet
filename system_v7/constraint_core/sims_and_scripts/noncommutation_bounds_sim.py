"""
noncommutation_bounds_sim.py -- two theorems where NONCOMMUTATION becomes a sharp, confirmed
bound on information and correlation. NOT ToE validation -- established math/physics reproduced
from the engine's core axiom. Both are inequalities (pure math) whose content is physical.

(1) ENTROPIC UNCERTAINTY (Maassen-Uffink): for two observables with eigenbases {|a>},{|b>},
    H(A) + H(B) >= log2(1/c),  c = max_{a,b} |<a|b>|^2.  H = Shannon entropy of outcomes (bits).
    c measures noncommutation: commuting bases (shared eigenbasis) c=1 -> bound 0 (no tradeoff);
    mutually unbiased (Z vs X) c=1/d -> bound log2(d) (maximal). The bound is TIGHT at the MUB
    limit. Noncommutation IS uncertainty, quantified in bits.

(2) CHSH / TSIRELSON: S = <A0 B0>+<A0 B1>+<A1 B0>-<A1 B1>. Local hidden-variable (classical,
    commuting) theories obey |S|<=2; quantum mechanics on an entangled state with NONCOMMUTING
    settings reaches |S| = 2 sqrt(2) (Tsirelson). Commuting settings cannot violate. The excess
    above 2 is the sharpest signature that identity is measurement-relative, not pre-assigned --
    the distinguishability/oracle root (a=a iff a~b).

numpy-only. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL noncommutation_bounds_sim: missing tool ({e.name})"); sys.exit(0)

def shannon_bits(p):
    p=p[p>1e-15]; return float(-np.sum(p*np.log2(p)))
def measure(psi,basis): return np.abs(basis.conj().T@psi)**2
def rot_basis(th): return np.array([[np.cos(th/2),-np.sin(th/2)],[np.sin(th/2),np.cos(th/2)]],complex)

# (1) entropic uncertainty
print("(1) Maassen-Uffink H(A)+H(B) >= log2(1/c):")
A=np.eye(2,dtype=complex); eu_ok=True; tight_mub=None
for th in [0.0,np.pi/6,np.pi/4,np.pi/3,np.pi/2]:
    B=rot_basis(th); c=np.max(np.abs(A.conj().T@B)**2); bound=np.log2(1/c) if c<1 else 0.0
    best=min(shannon_bits(measure(np.array([np.cos(p/2),np.exp(1j*l)*np.sin(p/2)]),A))
             +shannon_bits(measure(np.array([np.cos(p/2),np.exp(1j*l)*np.sin(p/2)]),B))
             for p in np.linspace(0,np.pi,60) for l in np.linspace(0,2*np.pi,60))
    print(f"    theta={th:.4f}: c={c:.4f} bound={bound:.4f} minH={best:.4f} holds={best>=bound-1e-3}")
    eu_ok = eu_ok and best>=bound-1e-3
    if abs(th-np.pi/2)<1e-9: tight_mub=(bound,best)

# (2) CHSH / Tsirelson
sx=np.array([[0,1],[1,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
psi=np.zeros(4,complex); psi[1]=1/np.sqrt(2); psi[2]=-1/np.sqrt(2)
md=lambda th: np.cos(th)*sz+np.sin(th)*sx
corr=lambda A,B:(psi.conj()@np.kron(A,B)@psi).real
A0,A1,B0,B1=md(0),md(np.pi/2),md(np.pi/4),md(-np.pi/4)
S=corr(A0,B0)+corr(A0,B1)+corr(A1,B0)-corr(A1,B1)
cl=max(abs(a0*b0+a0*b1+a1*b0-a1*b1) for a0 in(-1,1) for a1 in(-1,1) for b0 in(-1,1) for b1 in(-1,1))
Sc=corr(A0,B0)+corr(A0,B0)+corr(A0,B0)-corr(A0,B0)   # commuting control
print(f"(2) CHSH quantum |S|={abs(S):.6f} Tsirelson 2sqrt2={2*np.sqrt(2):.6f} classical={cl} commuting_control|S|={abs(Sc):.4f}")

assert eu_ok, "entropic uncertainty must hold at every angle"
assert abs(tight_mub[0]-1.0)<1e-6 and abs(tight_mub[1]-1.0)<1e-3, "MUB limit: bound=1 bit, tight"
assert abs(abs(S)-2*np.sqrt(2))<1e-6, "quantum CHSH must reach Tsirelson 2sqrt2"
assert cl==2, "classical CHSH bound must be 2"
assert abs(Sc)<=2+1e-9, "commuting settings cannot violate"
print("\nPASS noncommutation_bounds_sim")
