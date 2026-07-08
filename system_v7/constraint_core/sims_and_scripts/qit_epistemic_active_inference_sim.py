#!/usr/bin/env python3
"""qit_epistemic_active_inference_sim -- the EXPLORE half of active inference on the engine: select actions that
REDUCE THE UNKNOWN, using the known/unknown surprise field (UP-102) as the drive.

The existing qit_active_inference_planning_sim does PRAGMATIC planning (min path-integral of surprise toward a KNOWN
goal prior). This sim adds the missing EPISTEMIC half, which is what "a new kind of information processing" needs and
what the v7 prediction-first / holodeck doctrine describes: the engine does not know which terrain it is in (hidden
state); it selects probe-actions that MAXIMALLY RESOLVE that unknown. This is FEP's epistemic value / expected
information gain, rendered in pure QIT -- no reward, no temperature, no classical probability beyond a belief
distribution over a finite hidden-state set.

SETUP (prediction-first loop, v7 doctrine: model predicts -> readout error corrects -> belief updates -> next action):
  - Hidden state: which of the 8 terrains is running (unknown to the agent). True terrain fixed by the environment.
  - Belief b: a distribution over the 8 terrains, uniform at start (maximal unknown).
  - Action: pick a PROBE input state rho_a from a small action set, run it one flow-step under the (unknown) terrain,
    read the output Bloch vector.
  - Update: Bayesian belief update -- for each candidate terrain, predict the output; the likelihood is
    exp(-||readout - predicted||^2 / 2sigma^2); posterior ∝ prior * likelihood.
  - EPISTEMIC VALUE of an action (BEFORE taking it) = EXPECTED reduction in belief entropy = mutual information
    between the hidden terrain and the action's readout, I(terrain; readout | b) = H(b) - E_readout[H(b|readout)].
    This is pure information gain: how much this probe is expected to collapse the unknown. NO goal, NO reward.
  - Policy: at each tick pick the action with the highest expected information gain (greedy epistemic policy).

THREE GATED CLAIMS, each with a control that can fail:
  (1) EPISTEMIC POLICY RESOLVES THE UNKNOWN: belief entropy H(b) falls to ~0 and the MAP terrain = the true hidden
      terrain, within a few ticks, averaged over all 8 hidden states.
  (2) IT BEATS RANDOM ACTIONS: the greedy expected-information-gain policy reaches certainty in FEWER ticks than a
      random-action policy (the epistemic drive is doing real work, not just any probing).
  (3) CONTROL THAT FAILS -- UNINFORMATIVE ACTIONS: restrict the action set to a probe that all terrains map near-
      identically (low mutual information). Belief entropy does NOT collapse; the unknown is not resolved. If it
      collapsed anyway, "information gain" would be vacuous.

scratch_diagnostic, promotion_allowed=false. Pure QIT + finite belief distribution; the only "surprise" is relative
entropy / Shannon entropy of the belief over the hidden-state set. Uses the exact terrain GKSL generators.
"""
import json, sys
import numpy as np

sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
I2=np.eye(2,dtype=complex); sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy)
G=0.35; KAP=1.0; T_STEP=0.5; SUBSTEPS=60; SIGMA=0.25
TERR={0:(+1,'damp',+1),1:(+1,'depol',0),2:(+1,'damp',-1),3:(+1,'proj',0),
      4:(-1,'damp',-1),5:(-1,'depol',0),6:(-1,'damp',+1),7:(-1,'proj',0)}
def Dgen(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def gen(ti):
    eps,kind,pole=TERR[ti]; H=eps*(sx+sy+sz)/np.sqrt(3)
    def X(r):
        out=-1j*G*(H@r-r@H)
        if kind=='damp': out=out+KAP*Dgen(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*KAP*(Dgen(sx,r)+Dgen(sy,r))
        else: out=out+KAP*Dgen(sz,r)
        return out
    return X
def flow_step(ti,r,t=T_STEP,steps=SUBSTEPS):
    X=gen(ti); dt=t/steps
    for _ in range(steps):
        k1=X(r);k2=X(r+.5*dt*k1);k3=X(r+.5*dt*k2);k4=X(r+dt*k3)
        r=r+(dt/6)*(k1+2*k2+2*k3+k4);r=.5*(r+r.conj().T);r/=np.trace(r).real
    return r
def bloch(r): return np.array([np.trace(r@s).real for s in (sx,sy,sz)])
def rho_from_bloch(v): return 0.5*(I2+v[0]*sx+v[1]*sy+v[2]*sz)
def Hsh(b):
    b=np.clip(b,1e-12,1); return float(-np.sum(b*np.log2(b)))

# action set: a family of probe input states (the agent's available "questions")
def action_set(seed=5,n=6,radius=0.8):
    rng=np.random.default_rng(seed); acts=[]
    for _ in range(n):
        v=rng.normal(size=3); v=radius*v/np.linalg.norm(v); acts.append(rho_from_bloch(v))
    return acts

def predicted_readout(ti,rho_a): return bloch(flow_step(ti,rho_a.copy()))

# The action->readout map is DETERMINISTIC per (terrain, action). Precompute it ONCE (the RK4 flow is the only
# expensive call), so every belief update and info-gain estimate becomes pure array math -- same claim, ~100x faster.
def build_pred_table(acts):
    # PRED[a] = (8x3) array of each terrain's predicted readout Bloch vector for action a
    return [np.array([predicted_readout(t,acts[a]) for t in range(8)]) for a in range(len(acts))]

def belief_update_fast(prior, preds_a, y):
    d2=np.sum((y[None,:]-preds_a)**2,axis=1)
    like=np.exp(-d2/(2*SIGMA**2))
    post=prior*like; s=post.sum()
    return post/s if s>0 else np.ones(8)/8

def expected_info_gain_fast(prior, preds_a, n_mc=24, rng=None):
    H0=Hsh(prior); Hpost=0.0
    for _ in range(n_mc):
        t=rng.choice(8,p=prior); y=preds_a[t]+rng.normal(0,SIGMA,3)
        Hpost+=Hsh(belief_update_fast(prior,preds_a,y))
    return H0-Hpost/n_mc

def run_episode(ti_true, acts, policy, PRED, max_ticks=16, seed=0):
    rng=np.random.default_rng(seed); b=np.ones(8)/8; traj=[Hsh(b)]
    unf_pred=np.array([predicted_readout(t,rho_from_bloch(np.array([0.02,0.0,0.0]))) for t in range(8)])
    for _ in range(max_ticks):
        if policy=="epistemic":
            ai=max(range(len(acts)),key=lambda a: expected_info_gain_fast(b,PRED[a],rng=rng)); preds_a=PRED[ai]
        elif policy=="random":
            ai=int(rng.integers(len(acts))); preds_a=PRED[ai]
        else:  # uninformative -- fixed low-info probe (I/2-ish, all terrains map similarly)
            preds_a=unf_pred
        y=preds_a[ti_true]+rng.normal(0,SIGMA,3)
        b=belief_update_fast(b,preds_a,y); traj.append(Hsh(b))
        if Hsh(b)<0.05: break
    map_terr=int(np.argmax(b)); return traj, map_terr, (map_terr==ti_true)

def ticks_to_certain(traj): 
    for i,h in enumerate(traj):
        if h<0.05: return i
    return len(traj)-1

def main():
    acts=action_set(); SEEDS=3; PRED=build_pred_table(acts)
    # average over SEEDS episodes per hidden terrain so the ticks-to-certainty is not seed-fragile; cap 16 so
    # neither the epistemic nor the random policy is censored (the depol/proj terrains are the hardest to resolve).
    epi_ticks=[]; epi_correct=[]; rnd_ticks=[]; unf_final_H=[]
    for ti in range(8):
        te=[]; ce=[]; tr=[]; uh=[]
        for s in range(SEEDS):
            tr_e,map_e,ok_e=run_episode(ti,acts,"epistemic",PRED,seed=100+ti*SEEDS+s)
            tr_r,map_r,ok_r=run_episode(ti,acts,"random",PRED,seed=100+ti*SEEDS+s)
            tr_u,map_u,ok_u=run_episode(ti,acts,"uninformative",PRED,seed=100+ti*SEEDS+s)
            te.append(ticks_to_certain(tr_e)); ce.append(ok_e); tr.append(ticks_to_certain(tr_r)); uh.append(tr_u[-1])
        epi_ticks.append(float(np.mean(te))); epi_correct.append(all(ce))
        rnd_ticks.append(float(np.mean(tr))); unf_final_H.append(float(np.mean(uh)))
    epi_mean=float(np.mean(epi_ticks)); rnd_mean=float(np.mean(rnd_ticks)); unf_H=float(np.mean(unf_final_H))
    all_resolved=bool(all(epi_correct) and epi_mean<16)
    beats_random=bool(epi_mean<rnd_mean)
    uninformative_fails=bool(unf_H>0.5)   # control: unknown NOT resolved with low-info probe

    verdict=bool(all_resolved and beats_random and uninformative_fails)
    out={"classification":"scratch_diagnostic","promotion_allowed":False,
         "definition":"epistemic active inference: select actions by expected information gain I(hidden terrain; readout)=H(b)-E[H(b|y)]; resolve the unknown, no reward/goal. Prediction-first loop per v7 holodeck doctrine.",
         "epistemic_policy":{"mean_ticks_to_certainty":round(epi_mean,3),"all_hidden_terrains_correctly_identified":bool(all(epi_correct)),
                             "per_terrain_ticks":epi_ticks,"per_terrain_correct":[bool(x) for x in epi_correct]},
         "beats_random":{"epistemic_mean_ticks":round(epi_mean,3),"random_mean_ticks":round(rnd_mean,3),"epistemic_faster":beats_random},
         "control_uninformative_fails":{"mean_final_belief_entropy_bits":round(unf_H,3),"unknown_not_resolved":uninformative_fails},
         "QIT_EPISTEMIC_ACTIVE_INFERENCE":verdict}
    path=__file__.replace(".py","_results.json"); json.dump(out,open(path,"w"),indent=1)
    print("EPISTEMIC active inference: select actions that RESOLVE THE UNKNOWN (expected information gain).\n")
    print("(1) EPISTEMIC POLICY resolves the hidden terrain:")
    for ti in range(8): print(f"    hidden terrain {ti}: {epi_ticks[ti]:.1f} ticks to certainty, correct MAP: {epi_correct[ti]}")
    print(f"    -> all resolved, mean {epi_mean:.2f} ticks: {all_resolved}\n")
    print(f"(2) BEATS RANDOM ACTIONS: epistemic {epi_mean:.2f} vs random {rnd_mean:.2f} ticks -> faster: {beats_random}\n")
    print(f"(3) CONTROL uninformative probe: mean final belief entropy {unf_H:.3f} bits -> unknown NOT resolved: {uninformative_fails}")
    print(f"\n  QIT EPISTEMIC ACTIVE INFERENCE: {verdict}")
    if verdict: print("PASS qit_epistemic_active_inference")
    print("ALL_GATES:","PASS" if verdict else "FAIL","->",path)
    sys.exit(0 if verdict else 1)

if __name__=="__main__":
    main()
