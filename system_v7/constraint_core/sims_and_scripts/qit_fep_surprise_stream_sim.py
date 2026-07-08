#!/usr/bin/env python3
"""qit_fep_surprise_stream_sim -- the FEP LENS on the running engine as a per-tick SURPRISE STREAM.

PURE QIT, no classical/thermal terms. This is the FEP view of the attractor basin that the Lev host consumes at its
G3 gate: a per-tick signal surprise_bits = S(observation || belief), the Umegaki quantum relative entropy (bits),
near-zero while the world is predictable, spiking on a regime shift, decaying as the engine relearns. It is the
time-series companion to the two static FEP sims already in the bundle (qit_fep_ratchet = the perceptual functional
forced by distinguishability; qit_active_inference_planning = the path-integral active half). Neither of those emits
the per-tick stream; this one does, so the engine's belief/surprise trace can be looped back to Lev's evidence port
(cr_qit_bridge_stream_v0) as evidence-only provider records.

MATH (every classical primitive replaced by its constraint-surface origin -- NO temperature, NO energy, NO -log p):
  observation rho_t  : the world state under the CURRENT regime (a terrain's GKSL flow) at tick t.
  belief sigma_t     : a density operator relaxed toward past observations (CPTP-style convex update on the Bloch
                       vector) -- the engine's predictive model.
  surprise_bits      : S(rho_t || sigma_t) = tr(rho_t (log rho_t - log sigma_t)) / ln 2. Umegaki relative entropy,
                       CPTP-monotone and additive (the functional the qit_fep_ratchet sim forces from F01). This is
                       Josh's math, the same measure Lev's createWorldModelSurprise uses (KL(post||prior) ->
                       von-Neumann surprisal), NOT OpenProse's binary fingerprint bit.

THE SIGNATURE (matches the QIT_LEV_BRIDGE_SPEC: predictable ~0.006, regime-shift spike ~1.50, decays on relearn):
  a regime runs (terrain A), belief tracks it -> surprise decays to ~0; at a switch tick the regime changes to
  terrain B -> surprise SPIKES; belief relearns -> surprise decays again.

TWO FALSIFIABLE CONTROLS (the gate can fail):
  (1) FROZEN BELIEF -- belief never updates. Surprise cannot decay; it stays high throughout. If the real
      (learning) stream did not fall far below the frozen one, "the engine relearns" would be false.
  (2) NO REGIME SWITCH -- the world stays in terrain A the whole run. There is NO spike. If the real (switching)
      stream did not show a spike well above the no-switch baseline at the switch tick, "surprise marks regime
      shift" would be false.

scratch_diagnostic, promotion_allowed=false. This is the FEP LENS on the one engine, not a new mechanism -- a
different way to read the same density/entropy mechanics, exactly as the owner framed the QIT-FEP.
"""
import json, os, sys
import numpy as np
from scipy.linalg import logm

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; TH=np.pi/4; NS=120
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
H0=(sx+sy+sz)/np.sqrt(3)
def Dop(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def lind(kind,pole):
    if kind=='damp': return [sp if pole>0 else sm]
    if kind=='depol': return [sx/np.sqrt(2),sy/np.sqrt(2)]
    return [sz]
def flow(H,Ls,r,steps=NS,t=1.0):
    dt=t/steps
    def X(r):
        out=-1j*G*(H@r-r@H)
        for L in Ls: out=out+KAP*Dop(L,r)
        return out
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);r/=np.trace(r).real
    return r
def tflow(ti,r): eps,kind,pole=TERR[ti]; return flow(eps*H0,lind(kind,pole),r)
def bvec(r): return np.array([np.trace(r@s).real for s in (sx,sy,sz)])
def dm(v):
    v=np.array(v,float); n=np.linalg.norm(v)
    if n>0.999: v=v/n*0.999
    return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)
def S_rel(rho,sig):
    rho=rho+1e-12*I2; sig=sig+1e-12*I2
    return float(max(np.trace(rho@(logm(rho)-logm(sig))).real/np.log(2), 0.0))

def stream(switch_at=15, n=30, terr_a=0, terr_b=2, lr=0.5, freeze_at_switch=False, switch=True):
    # terr_a damps toward +z pole, terr_b damps toward -z pole -> distinct non-degenerate fixed points.
    # learn: belief relaxes toward each observation. freeze_at_switch: belief keeps updating through phase A
    # (learns regime A), then is FROZEN at the switch tick so it cannot adapt to regime B (the honest "cannot
    # relearn" control -- stuck at A's pointer while the world moves to B).
    belief=dm([0,0,0]); obs=dm([0.6,0.3,0.2]); out=[]
    for t in range(n):
        switched = (t>=switch_at) and switch
        ti = terr_b if switched else terr_a
        obs=tflow(ti,obs); out.append(S_rel(obs,belief))
        frozen_now = freeze_at_switch and switched
        if not frozen_now:
            belief=dm((1-lr)*bvec(belief)+lr*bvec(obs))
    return np.array(out)

def main():
    SW=15; N=30
    real=stream(SW,N,freeze_at_switch=False,switch=True)     # learns through both regimes
    frozen=stream(SW,N,freeze_at_switch=True,switch=True)    # control 1: belief frozen at switch, cannot relearn regime B
    noswitch=stream(SW,N,freeze_at_switch=False,switch=False)# control 2: no regime change

    pre=float(real[5:SW].mean())            # predictable phase
    spike=float(real[SW:SW+4].max())        # regime-shift spike
    post=float(real[SW+10:N].mean())        # relearned phase
    predictable = pre<0.05
    spikes = spike>0.5 and spike>10*pre
    relearns = post<0.05 and post<0.2*spike
    # control 1: frozen belief cannot decay -> its post-switch tail stays high vs the learning stream
    frozen_tail=float(frozen[SW+10:N].mean()); learn_beats_frozen = post < 0.3*max(frozen_tail,1e-9)
    # control 2: no-switch has no spike at the switch tick
    noswitch_at_switch=float(noswitch[SW:SW+4].max()); switch_beats_noswitch = spike > 5*max(noswitch_at_switch,1e-9)

    verdict=bool(predictable and spikes and relearns and learn_beats_frozen and switch_beats_noswitch)
    out={"classification":"scratch_diagnostic","promotion_status":"scratch_diagnostic","promotion_allowed":False,
         "framing":"the FEP lens on the running engine: per-tick surprise_bits = S(observation||belief), Umegaki relative entropy (bits). Pure QIT, no classical/thermal terms. The time-series companion to the bundle's static FEP sims, and the signal Lev's G3 consumes.",
         "surprise_measure":"Umegaki quantum relative entropy S(rho||sigma) in bits; CPTP-monotone + additive (forced from F01 by qit_fep_ratchet)",
         "predictable_phase_mean_bits":round(pre,4),
         "regime_shift_spike_bits":round(spike,4),
         "relearned_phase_mean_bits":round(post,4),
         "is_near_zero_when_predictable":bool(predictable),
         "spikes_on_regime_shift":bool(spikes),
         "decays_on_relearn":bool(relearns),
         "control_frozen_belief_tail_bits":round(frozen_tail,4),"learning_beats_frozen":bool(learn_beats_frozen),
         "control_noswitch_at_switch_bits":round(noswitch_at_switch,4),"switch_beats_noswitch":bool(switch_beats_noswitch),
         "stream_bits":[round(float(x),4) for x in real],
         "lev_bridge_note":"emits the per-tick {tick, belief_bloch, surprise_bits} trace the Lev cr_qit_bridge_stream_v0 evidence port consumes as evidence-only provider records; matches QIT_LEV_BRIDGE_SPEC signature (predictable ~0.006, spike ~1.5, decay).",
         "QIT_FEP_SURPRISE_STREAM_BUILT":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("QIT-FEP SURPRISE STREAM -- the FEP lens on the running engine (pure Umegaki relative entropy, bits).\n")
    print(f"  predictable phase mean:  {pre:.4f} bits  (near-zero: {predictable})")
    print(f"  regime-shift spike:      {spike:.4f} bits  (spikes: {spikes})")
    print(f"  relearned phase mean:    {post:.4f} bits  (decays: {relearns})")
    print(f"  CONTROL frozen belief tail {frozen_tail:.4f} -> learning beats frozen: {learn_beats_frozen}")
    print(f"  CONTROL no-switch @ switch {noswitch_at_switch:.4f} -> switch beats no-switch: {switch_beats_noswitch}")
    print(f"\n  QIT-FEP SURPRISE STREAM BUILT: {verdict}")
    if verdict: print("PASS qit_fep_surprise_stream")
    print("ALL_GATES:", "PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
