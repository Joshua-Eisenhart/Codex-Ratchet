"""
fluctuation_theorem_sim.py -- the engine's UNITARY drive obeys the modern nonequilibrium
fluctuation theorems (Jarzynski + Crooks), the exact generalization of the Szilard/Landauer
bound to ARBITRARY driving speed (near OR far from equilibrium). NOT a ToE validation --
a check that the engine's driven dynamics obey confirmed statistical mechanics.

Two-point measurement (TPM) protocol on a driven qubit:
  1. sample thermal state at beta with H_i, projectively measure energy -> E_i
  2. drive UNITARILY H_i -> H_f over time tau (engine's coherent evolution)
  3. projectively measure energy of H_f -> E_j;  work of that trajectory W = E_j - E_i

  JARZYNSKI:  <e^{-beta W}> = e^{-beta dF}   exact at EVERY tau (fast=far-from-eq, slow=near)
  CROOKS:     P_F(W) / P_R(-W) = e^{beta(W - dF)}   for the forward vs time-reversed protocol
  2nd law:    <W> >= dF   (dissipated work W_diss = <W> - dF >= 0)

Chosen with a GENUINE free-energy change (dF != 0, different energy gaps) so the equality is
nontrivial. scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np
except ImportError as e:
    print(f"SKIP_OPTIONAL fluctuation_theorem_sim: missing tool ({e.name})")
    sys.exit(0)
from collections import defaultdict

sx=np.array([[0,1],[1,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
beta=1.0
Hi=1.0*sz                    # gap 2
Hf=1.8*sz+0.6*sx             # different gap -> dF != 0 (nontrivial)
def eig(H): w,v=np.linalg.eigh(H); return w,v
def F(H): w,_=eig(H); return -np.log(np.sum(np.exp(-beta*w)))/beta
dF=F(Hf)-F(Hi)
def U_drive(Ha,Hb,tau,nsteps=600):
    U=np.eye(2,dtype=complex); dt=tau/nsteps
    for k in range(nsteps):
        s=(k+0.5)/nsteps; H=(1-s)*Ha+s*Hb
        w,v=np.linalg.eigh(H); U=v@np.diag(np.exp(-1j*w*dt))@v.conj().T@U
    return U
def work_dist(Ha,Hb,tau):
    wa,va=eig(Ha); wb,vb=eig(Hb)
    pa=np.exp(-beta*wa)/np.sum(np.exp(-beta*wa)); U=U_drive(Ha,Hb,tau)
    return [(wb[j]-wa[i], pa[i]*abs(vb[:,j].conj()@(U@va[:,i]))**2) for i in range(2) for j in range(2)]

# Jarzynski at several driving speeds
print(f"dF = {dF:+.5f};  e^(-beta dF) = {np.exp(-beta*dF):.5f}")
jerr=0.0
for tau in [0.05,0.5,2.0,10.0]:
    d=work_dist(Hi,Hf,tau); lhs=sum(P*np.exp(-beta*W) for W,P in d); meanW=sum(P*W for W,P in d)
    jerr=max(jerr,abs(lhs-np.exp(-beta*dF)))
    print(f"  tau={tau:<6.2f}  <e^-bW>={lhs:.5f}  <W>={meanW:+.4f}>=dF ({meanW>=dF-1e-9})  W_diss={meanW-dF:.4f}")

# Crooks across all work bins
fwd=work_dist(Hi,Hf,0.7); rev=work_dist(Hf,Hi,0.7)
Fd=defaultdict(float); Rd=defaultdict(float)
for W,P in fwd: Fd[round(W,4)]+=P
for W,P in rev: Rd[round(W,4)]+=P
cerr=0.0
print("  Crooks P_F(W)/P_R(-W) vs e^(b(W-dF)):")
for W in sorted(Fd):
    pf=Fd[W]; pr=Rd.get(round(-W,4),0)
    if pf>1e-12 and pr>1e-12:
        cerr=max(cerr,abs(np.log(pf/pr)-beta*(W-dF)))
        print(f"    W={W:+.4f}: {pf/pr:10.4f} vs {np.exp(beta*(W-dF)):10.4f}")
print(f"\n Jarzynski max err = {jerr:.1e};  Crooks max log-err = {cerr:.1e}")

assert jerr<1e-10, "Jarzynski must hold to machine precision at every drive speed"
assert cerr<1e-3,  "Crooks must hold across all work bins (Trotter-limited)"
d10=work_dist(Hi,Hf,10.0); assert sum(P*W for W,P in d10)>=dF-1e-9, "2nd law <W> >= dF"
print("\nPASS fluctuation_theorem_sim")
