"""
eps_even_a2_dissipation_foothold_sim.py -- PURE MATH, no jargon. 2026-07-02, Phase-X item V.2.

STATE_OF_THE_MODEL.md open-ledger V.2 proposed: "an eps-even functional reading the INSTALLED frame
through dissipation (the 0.22-vs-0 sensitivity is the foothold), then rerun the 7m decisive test."
This sim BUILDS that instrument and tests it honestly. It resolves the foothold NEGATIVELY, for a
structural reason -- which is a useful ratchet result (failure is signal), not a closure.

The instrument: F(t) = | chi2( V . D_t(probe) . V^dag ) - chi2( D_t(probe) ) |, i.e. dissipate the
probe, then view it in the terrain's INSTALLED frame (V=I for direct a2=0, V=W Hadamard for
conjugated a2=1), and measure how far the frame moves the leading eigenvector (a chi2 Bargmann
phase). eps-symmetrized over the eps-mirror terrain to be eps-even.

THREE HONEST TESTS (deterministic, seeded):
 (1) SEPARATION IS CIRCULAR. The eps-even F separates a2 perfectly (direct all 0.0000, conjugated
     0.2285-0.5257) -- but ONLY because a2 IS the installed-frame flag (V=I vs V!=I) fed in by hand.
     Detecting "is the frame nontrivial" reads the a2 label back out. This is the circular readout the
     fourth audit ruled out, not a discovery.
 (2) THE DISSIPATION GATE FAILS. V.2 hoped the frame is readable THROUGH dissipation and invisible
     without it. It is not: the same conjugated frame on UNITARY dynamics also fires (t2 unitary
     ~0.89 > dissipative ~0.79), because the eigenvector of the mixed probe moves under the frame
     regardless of dissipation. No 0.22-vs-0 gate survives.
 (3) NOT a2-SPECIFIC. Any nontrivial frame fires: V=W on a DIRECT terrain gives ~0.26, an arbitrary
     Vrand gives ~0.03. The instrument reads "installed-frame nontriviality," not an a2 charge.

CONCLUSION: the dissipation foothold does NOT yield an eps-even a2-specific instrument. a2 remains an
installed-frame flag (terrain layer) / exact W-covariance label (operator layer, 7t), NOT a channel-
intrinsic charge readable off the terrain generators. V.2's decisive-test hope resolves negatively,
reinforcing eps_even_a2_specificity_sim's prior structural finding. No new instrument is earned.
scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
    from scipy.linalg import expm
except ImportError as e:
    print(f"SKIP_OPTIONAL eps_even_a2_dissipation_foothold_sim: missing tool ({e.name})"); sys.exit(0)

I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy); g,kap=0.35,1.0
comm=lambda A,r:A@r-r@A
D=lambda L,r:L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
terr={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
a2_target={0:0,1:0,2:1,3:1,4:0,5:0,6:1,7:1}; mirror={0:4,1:5,2:6,3:7,4:0,5:1,6:2,7:3}
W=(sx+sz)/np.sqrt(2)
def frame(ti): return I2 if a2_target[ti]==0 else W
def diss(ti):
    eps,kind,pole=terr[ti]
    def Dp(r):
        if kind=='damp': return kap*D(sp if pole>0 else sm,r)
        elif kind=='depol': return 0.5*kap*(D(sx,r)+D(sy,r))
        else: return kap*D(sz,r)
    return Dp
def unit(ti):
    eps=terr[ti][0]; return lambda r:-1j*g*comm(eps*sz,r)
def flow(X,r,t,steps=200):
    dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4); r=.5*(r+r.conj().T); r/=np.trace(r).real
    return r
r0=np.array([1,0],complex); rref=np.array([1,1],complex)/np.sqrt(2)
def chi2(rho):
    w,U=np.linalg.eigh(rho); e=U[:,np.argmax(w)]
    return -np.angle(np.vdot(r0,e)*np.vdot(e,rref)*np.vdot(rref,r0))
probe=0.5*(I2+0.55*sx+0.35*sy+0.25*sz)
def instr(ti,V=None,dyn=diss):
    X=dyn(ti); Vv=frame(ti) if V is None else V; vals=[]
    for tt in (0.4,0.8,1.2):
        d=flow(X,probe.copy(),tt); dv=Vv@d@Vv.conj().T; vals.append(abs(chi2(dv)-chi2(d)))
    return sum(vals)/len(vals)

raw={t:instr(t) for t in range(8)}; sym={t:(raw[t]+raw[mirror[t]])/2 for t in range(8)}
direct=[sym[t] for t in range(8) if a2_target[t]==0]; conj=[sym[t] for t in range(8) if a2_target[t]==1]
sep = min(conj)>max(direct)
print(f"(1) eps-even F separates a2 [direct {min(direct):.4f}-{max(direct):.4f} | conj {min(conj):.4f}-{max(conj):.4f}] sep={sep} -- but CIRCULAR (a2 = the installed frame, fed in)")

gate_diss=instr(2,dyn=diss); gate_unit=instr(2,dyn=unit)
print(f"(2) dissipation gate FAILS: conj t2 dissipative F={gate_diss:.4f}, unitary F={gate_unit:.4f} (unitary also fires -> no 0.22-vs-0 gate)")

fW=instr(0,V=W); Vrand=expm(-1j*0.7*(0.3*sx+0.6*sy+0.2*sz)); fR=instr(0,V=Vrand)
print(f"(3) NOT a2-specific: direct t0 with V=I gives {instr(0,V=I2):.4f}, with V=W gives {fW:.4f}, with Vrand gives {fR:.4f} (any nontrivial V fires)")

assert sep, "the eps-even functional separates a2 AS GIVEN (but circularly -- a2 is the installed frame)"
assert gate_unit>0.1, "dissipation gate FAILS: unitary dynamics also lets the frame move the eigenvector (no dissipation-only readability)"
assert fW>0.1 and instr(0,V=I2)<1e-9, "NOT a2-specific: a wrong nontrivial frame fires on a direct terrain; only V=I (its own frame) reads 0"
print("\nPASS eps_even_a2_dissipation_foothold_sim")
