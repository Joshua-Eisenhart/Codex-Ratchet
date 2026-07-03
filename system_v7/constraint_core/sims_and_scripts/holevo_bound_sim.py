"""
holevo_bound_sim.py -- FINITUDE of readout: the HOLEVO BOUND caps how much CLASSICAL
information can be extracted from a quantum state, no matter how it is encoded or measured.
NOT ToE validation -- established quantum information theory from the engine's own states.

Encode classical symbol x (prob p_x) as state rho_x. Accessible information (mutual info
I(X:Y) over ANY measurement) is bounded:
    I(X:Y) <= chi = S(sum_x p_x rho_x) - sum_x p_x S(rho_x)   (Holevo quantity)
and chi <= log2(dim). A d-dim system carries at most log2(d) accessible bits.

Ties to the axioms:
  * FINITUDE -- the probe cannot extract more than the dimension allows; cramming 4 symbols into
    a qubit still yields only 1 accessible bit (chi=1 for 4 tetrahedral pure states).
  * a=a iff a~b (distinguishability/oracle) -- identity is probe-relative; NON-ORTHOGONAL
    (noncommuting) signal states LOSE accessible info because no probe can perfectly separate
    them (chi<1 as the Bloch angle shrinks from pi to 0).
  * Holevo is a TRUE upper bound: the best measurement over all angles never beats chi.

numpy-only. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL holevo_bound_sim: missing tool ({e.name})"); sys.exit(0)

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]]); sz=np.array([[1,0],[0,-1]],complex)
def S_bits(rho):
    w=np.linalg.eigvalsh(rho); w=w[w>1e-15]; return float(-np.sum(w*np.log2(w)))
def bloch(nx,ny,nz):
    n=np.array([nx,ny,nz],float); n=n/np.linalg.norm(n)
    return 0.5*(np.eye(2)+n[0]*sx+n[1]*sy+n[2]*sz)
def holevo(states,probs):
    avg=sum(p*r for p,r in zip(probs,states)); return S_bits(avg)-sum(p*S_bits(r) for p,r in zip(probs,states))
def proj(vec): v=np.array(vec,complex); v=v/np.linalg.norm(v); return np.outer(v,v.conj())
def mutual_info_bits(states,probs,povm):
    pxy=np.array([[probs[x]*np.trace(states[x]@povm[y]).real for y in range(len(povm))] for x in range(len(states))])
    px=pxy.sum(1,keepdims=True); py=pxy.sum(0,keepdims=True); I=0.0
    for x in range(pxy.shape[0]):
        for y in range(pxy.shape[1]):
            if pxy[x,y]>1e-15: I+=pxy[x,y]*np.log2(pxy[x,y]/(px[x,0]*py[0,y]))
    return I

# (1) chi vs signal-state overlap (1-bit code, 2 pure states, angle theta)
print("(1) chi for a 1-bit code, 2 pure states separated by angle theta:")
chi_rows=[]
for theta in [0.0,np.pi/4,np.pi/2,3*np.pi/4,np.pi]:
    r0=bloch(0,0,1); r1=bloch(np.sin(theta),0,np.cos(theta)); chi=holevo([r0,r1],[0.5,0.5])
    chi_rows.append((theta,chi)); print(f"    theta={theta:.4f}: chi={chi:.4f} bits (<=1: {chi<=1+1e-9})")

# (2) Holevo is a true bound: best measured I(X:Y) over all angles <= chi
print("(2) best measured I(X:Y) over measurement angles vs chi:")
bound_ok=True
for theta in [np.pi/4,np.pi/2,3*np.pi/4]:
    r0=bloch(0,0,1); r1=bloch(np.sin(theta),0,np.cos(theta)); st=[r0,r1]; pr=[0.5,0.5]; chi=holevo(st,pr)
    bestI=max(mutual_info_bits(st,pr,[proj([np.cos(m/2),np.sin(m/2)]),np.eye(2)-proj([np.cos(m/2),np.sin(m/2)])])
              for m in np.linspace(0,np.pi,200))
    print(f"    theta={theta:.4f}: chi={chi:.4f} maxI={bestI:.4f} I<=chi={bestI<=chi+1e-6}")
    bound_ok = bound_ok and bestI<=chi+1e-6

# (3) dimension caps accessible info: 4 tetrahedral pure states, 4 symbols -> chi=1 bit (not 2)
tetra=[bloch(*n) for n in [(1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1)]]
assert all(abs(np.trace(r@r).real-1)<1e-9 for r in tetra), "tetrahedral states must be pure"
chi_t=holevo(tetra,[0.25]*4)
print(f"(3) 4 tetrahedral pure states, 4 symbols: chi={chi_t:.4f} bits <= log2(2)=1")

assert abs(chi_rows[0][1])<1e-6, "identical states carry 0 accessible bits"
assert abs(chi_rows[-1][1]-1.0)<1e-6, "orthogonal states carry exactly 1 bit (=log2 d)"
assert all(c<=1+1e-9 for _,c in chi_rows), "chi <= log2(d) always"
assert bound_ok, "Holevo must upper-bound the best measured I(X:Y)"
assert abs(chi_t-1.0)<1e-6, "4 symbols in a qubit still cap at 1 accessible bit (finitude)"
print("\nPASS holevo_bound_sim")
