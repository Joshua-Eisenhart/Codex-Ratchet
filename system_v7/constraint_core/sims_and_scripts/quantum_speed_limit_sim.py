"""
quantum_speed_limit_sim.py -- the engine's unitary drive obeys the QUANTUM SPEED LIMIT, the
physical bound that ties the model's two core axioms (FINITUDE, NONCOMMUTATION) to dynamics.
NOT a ToE validation -- a check that the engine's evolution obeys confirmed quantum bounds.

The minimum time to reach an ORTHOGONAL (fully distinguishable) state is bounded below by the
energy resource (hbar=1):
    Mandelstam-Tamm:  t >= (pi/2)/dE          (dE = energy std-dev = spread)
    Margolus-Levitin: t >= (pi/2)/(E - E0)    (mean energy above ground)
    Levitin-Toffoli:  t_min = (pi/2)/max(dE, E-E0)   (tight combined bound)

Two axioms, cleanly separated into the bound:
  * FINITUDE     -- bounded energy => bounded speed; t_orth = (pi/2)/dE saturates the bound
                    exactly, and larger dE evolves faster (linearly).
  * NONCOMMUTATION -- [H,rho]!=0  <=>  dE>0  <=>  the state EVOLVES (three equivalent
                    conditions). If H commutes with rho the state NEVER moves (QSL = infinity).
                    Reaching FULL orthogonality additionally needs |psi0> balanced across H's
                    eigenstates (an equal superposition); a tilted H evolves but only precesses
                    part-way. So noncommutation gates MOTION; the QSL constant bounds SPEED.

numpy-only. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL quantum_speed_limit_sim: missing tool ({e.name})")
    sys.exit(0)

sx=np.array([[0,1],[1,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
psi0=np.array([1,0],complex); rho0=np.outer(psi0,psi0.conj())
def evolve(H,psi,t):
    w,v=np.linalg.eigh(H); return v@np.diag(np.exp(-1j*w*t))@v.conj().T@psi
def fid(a,b): return abs(a.conj()@b)**2

# (1) saturation: t_orth = (pi/2)/dE at three energy scales
print("(1) QSL saturation (H = g*sx, balanced -> reaches orthogonality):")
ratios=[]
for g in [0.5,1.0,2.0]:
    H=g*sx; E=(psi0.conj()@H@psi0).real; dE=np.sqrt((psi0.conj()@(H@H)@psi0).real-E**2)
    w,_=np.linalg.eigh(H); bound=(np.pi/2)/max(dE,E-w[0])
    ts=np.linspace(0,8,40000); fids=np.array([fid(psi0,evolve(H,psi0,t)) for t in ts])
    below=np.where(fids<1e-6)[0]; t_orth=ts[below[0]]
    ratios.append(t_orth/bound)
    print(f"    g={g:.2f}: dE={dE:.4f}  t_orth={t_orth:.4f}  bound={bound:.4f}  ratio={t_orth/bound:.4f}")

# (2) noncommutation gates motion
print("(2) noncommutation <=> dE>0 <=> evolution:")
rows=[]
for name,H in [("g*sz commutes",1.0*sz),("g*sx balanced",1.0*sx),("0.6sz+0.8sx tilt",0.6*sz+0.8*sx)]:
    comm=np.linalg.norm(H@rho0-rho0@H)
    E=(psi0.conj()@H@psi0).real; dE=np.sqrt((psi0.conj()@(H@H)@psi0).real-E**2)
    ts=np.linspace(0,20,8000); minf=min(fid(psi0,evolve(H,psi0,t)) for t in ts)
    rows.append((name,comm,dE,dE>1e-9,minf<0.01))
    print(f"    {name:18s} [H,rho]={comm:.4f}  dE={dE:.4f}  evolves={dE>1e-9}  reaches_orth={minf<0.01}")

assert all(abs(r-1)<0.02 for r in ratios), "QSL must be saturated (ratio ~1) at all energies"
comm0,dE0=rows[0][1],rows[0][2]
assert comm0<1e-9 and dE0<1e-9 and not rows[0][3], "commuting H: no motion, dE=0"
assert rows[1][3] and rows[1][4], "balanced noncommuting H: evolves AND reaches orthogonality"
assert rows[2][3] and not rows[2][4], "tilted H: evolves but does NOT reach full orthogonality"
print("\nPASS quantum_speed_limit_sim")
