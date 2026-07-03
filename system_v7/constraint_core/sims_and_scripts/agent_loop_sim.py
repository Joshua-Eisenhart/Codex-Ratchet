"""
agent_loop_sim.py -- the CLOSED active-inference loop: perception + action = a running
world-engine. Layer 13 minimized CURRENT free energy (perception). This adds the ACTION
half: minimize EXPECTED free energy G = risk - epistemic_value, so the engine chooses
which action to take to make the world match its preference. Pure QIT throughout
(Umegaki relative entropy for risk, von Neumann entropy drop for epistemic value).

  perception:  observe world -> surprise F(obs||belief) -> update belief (stored in Hill cell)
  action:      for each available action, predict its observation; pick min G where
                 G = F(pred||preference)  -  [S(belief) - S(belief_after)]
                     \___ risk (goal miss) ___/    \___ epistemic value (info gained) ___/
  world:       responds to the chosen action (with inertia)

Result: from a world OPPOSITE the goal (goal_dist 1.37), the agent drives it to the
preferred state (goal_dist < 0.01) and holds it. The engine ACTS to make the world match
its model -- the defining property of a running world-engine.
scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np
from scipy.linalg import expm, logm
I2=np.eye(2,dtype=complex); sx=np.array([[0,1],[1,0]],complex)
sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
G_,KAP=0.35,1.0
def sL(A): return np.kron(I2,A)
def sR(A): return np.kron(A.T,I2)
def sD(L): Ld=L.conj().T; return sL(L)@sR(Ld)-0.5*(sL(Ld@L)+sR(Ld@L))
def sC(H): return -1j*(sL(H)-sR(H))
def vec(r): return r.T.reshape(-1)
def unvec(v): return v.reshape(2,2).T
Hill=expm(0.15*(G_*sC((sx+sy+sz)/np.sqrt(3))+KAP*sD(sz)))
def store(b): r=unvec(Hill@vec(b)); r=0.5*(r+r.conj().T); return r/np.trace(r).real
def S_vn(r):
    ev=np.linalg.eigvalsh(0.5*(r+r.conj().T)); ev=ev[ev>1e-12]; return float(-np.sum(ev*np.log2(ev)))
def F(obs,bel):
    obs=0.5*(obs+obs.conj().T); bel=0.5*(bel+bel.conj().T)
    ev,V=np.linalg.eigh(bel); ev=np.clip(ev,1e-12,None); bel=V@np.diag(ev)@V.conj().T
    return float(np.real(np.trace(obs@((logm(obs+1e-12*I2)-logm(bel))/np.log(2)))))
def EFE(pred,belief,pref,rate=0.5):
    risk=F(pred,pref); post=(1-rate)*belief+rate*pred
    post=0.5*(post+post.conj().T); post/=np.trace(post).real
    return risk-(S_vn(belief)-S_vn(post))

def agent_loop(pref,n=12,rate=0.5,inertia=0.6):
    belief=0.5*I2; world=0.5*(I2-0.7*sz)
    acts={"+z":0.5*(I2+0.85*sz),"-z":0.5*(I2-0.85*sz),"+x":0.5*(I2+0.85*sx),"-x":0.5*(I2-0.85*sx)}
    traj=[]
    for t in range(n):
        obs=world; sp=F(obs,belief)
        belief=(1-rate)*belief+rate*obs; belief=0.5*(belief+belief.conj().T); belief/=np.trace(belief).real
        belief=store(belief)
        act=min(acts,key=lambda k:EFE(acts[k],belief,pref))
        world=inertia*world+(1-inertia)*acts[act]; world=0.5*(world+world.conj().T); world/=np.trace(world).real
        traj.append((t,sp,act,float(np.trace(world@sz).real),F(world,pref)))
    return traj

# (1) action selection picks the goal-matching action
pref=0.5*(I2+0.9*sz); belief0=0.5*I2
acts={"+z":0.5*(I2+0.8*sz),"-z":0.5*(I2-0.8*sz),"+x":0.5*(I2+0.8*sx)}
chosen=min(acts,key=lambda k:EFE(acts[k],belief0,pref))
print(f"(1) action selection: goal=+z, chosen={chosen}")

# (2) closed loop reaches and holds the goal
traj=agent_loop(pref)
print(f"(2) closed loop: goal_dist {traj[0][4]:.3f} -> {traj[-1][4]:.4f}, world_z {traj[0][3]:+.3f} -> {traj[-1][3]:+.3f}")
for t,sp,act,wz,gd in traj: print(f"    t{t:>2d} surprise={sp:.4f} act={act} world_z={wz:+.3f} goal_dist={gd:.4f}")

assert chosen=="+z", "must select the goal-matching action"
assert all(x[2]=="+z" for x in traj), "loop must consistently drive toward the goal"
assert traj[0][4]>1.0 and traj[-1][4]<0.05, "world must be driven from far-from-goal to at-goal"
assert traj[-1][3]>0.8, "final world_z must reach the +z preference"
print("\nPASS agent_loop_sim")
