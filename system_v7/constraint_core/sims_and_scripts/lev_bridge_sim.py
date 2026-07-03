"""
lev_bridge_sim.py -- the QIT engine as a signal source a Leviathan graph consumes.
Foundations-up, no coupling to Lev internals: defines the STREAM CONTRACT (what the
engine emits each tick) and proves the signals behave as world-engine control inputs.

Each tick the engine (belief in the Hill projective memory cell, Layers 12-13) emits:
  belief_bloch   the current belief state [x,y,z]
  surprise_bits  free energy S(observation || belief) -- novelty / prediction error
  fe_gradient    free-energy reduction this tick -- the learning drive (how hard it updated)

A graph node subscribes to this stream. surprise is the control signal: near-zero while
the world is predictable, spikes on a regime shift, decays as the engine relearns. That is
the hook for Lev attention/action allocation. PURE QIT (Umegaki relative entropy).

ADAPTER (LevBridge) exposes .tick(observation)->record and .subscribe(callback), the minimal
surface a graph edge needs. scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm, logm
I2=np.eye(2,dtype=complex); sx=np.array([[0,1],[1,0]],complex)
sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
G,KAP=0.35,1.0
def _sL(A): return np.kron(I2,A)
def _sR(A): return np.kron(A.T,I2)
def _sD(L): Ld=L.conj().T; return _sL(L)@_sR(Ld)-0.5*(_sL(Ld@L)+_sR(Ld@L))
def _sC(H): return -1j*(_sL(H)-_sR(H))
def _vec(r): return r.T.reshape(-1)
def _unvec(v): return v.reshape(2,2).T
_HILL=expm(0.15*(G*_sC((sx+sy+sz)/np.sqrt(3))+KAP*_sD(sz)))
def _store(b): r=_unvec(_HILL@_vec(b)); r=0.5*(r+r.conj().T); return r/np.trace(r).real
def _F(obs,bel):
    obs=0.5*(obs+obs.conj().T); bel=0.5*(bel+bel.conj().T)
    ev,V=np.linalg.eigh(bel); ev=np.clip(ev,1e-12,None); bel=V@np.diag(ev)@V.conj().T
    return float(np.real(np.trace(obs@((logm(obs+1e-12*I2)-logm(bel))/np.log(2)))))
def _bloch(r): return [float(np.trace(r@s).real) for s in (sx,sy,sz)]

class LevBridge:
    """minimal adapter: an active-inference engine node for a Leviathan graph."""
    def __init__(self, rate=0.5):
        self.bel=0.5*I2; self.rate=rate; self.tick_n=0; self._subs=[]
    def subscribe(self, cb): self._subs.append(cb)
    def tick(self, obs):
        F=_F(obs,self.bel)
        bn=(1-self.rate)*self.bel+self.rate*obs; bn=0.5*(bn+bn.conj().T); bn/=np.trace(bn).real
        grad=F-_F(obs,bn); self.bel=_store(bn)
        rec={"tick":self.tick_n,"belief_bloch":[round(x,4) for x in _bloch(self.bel)],
             "surprise_bits":round(F,4),"fe_gradient":round(grad,4)}
        self.tick_n+=1
        for cb in self._subs: cb(rec)
        return rec

def _demo():
    def world(t): return 0.5*(I2+0.7*sz) if t<6 else 0.5*(I2-0.6*sz+0.3*sx)
    br=LevBridge(); events=[]; br.subscribe(events.append)
    stream=[br.tick(world(t)) for t in range(14)]
    sp=[r["surprise_bits"] for r in stream]
    print("tick surprise fe_grad belief_z")
    for r in stream: print(f"  {r['tick']:>2d}  {r['surprise_bits']:>7.4f} {r['fe_gradient']:>7.4f}  {r['belief_bloch'][2]:>+.3f}")
    print(f"\nsettled(pre)={sp[5]:.4f}  spike(shift)={sp[6]:.4f}  relearned={sp[13]:.4f}")
    assert len(events)==14, "subscriber must receive every tick"
    assert sp[5]<0.05, "surprise must settle on a stable world"
    assert sp[6]>1.0, "surprise must spike on regime shift (novelty signal)"
    assert sp[13]<0.1, "surprise must decay as the engine relearns"
    assert all(set(r)=={"tick","belief_bloch","surprise_bits","fe_gradient"} for r in stream), "stream schema fixed"
    print("PASS lev_bridge_sim")

if __name__=="__main__": _demo()
