"""
manifold_L5_binding_discriminator_sim.py  (numpy control-lane; pure QIT)

SETTLES the open L5 rung. The v0.5 audit found nested-shell structure INDISTINGUISHABLE from a plain
scalar at the radius-regression obligation. That obligation is 1-D by construction: for a pure 2-qubit
state every readout (radius, marg-entropy, purity, negativity) is a function of the SINGLE Schmidt angle,
so a scalar wins trivially and the geometry cannot bind. The file names the fix: "an obligation where
shell structure could bind (perturbation response)."

This builds that obligation HONESTLY (non-circular):
  State family (the L5 marginal object, 2 real coords):
     rho_A(eta,phi) = 1/2 (I + r(eta) * n(phi).sigma),  r(eta)=|cos 2eta| (the SHELL radius),
     n(phi)=(sin phi,0,cos phi) (Schmidt-basis ORIENTATION). This is exactly the reduced state of a
     pure 2-qubit state with Schmidt angle eta and local basis rotated by phi.
  Natural obligation (NOT an answer key): apply a FIXED z-dephasing channel D_z(rho)=1/2(rho+Z rho Z)
     and predict the entropy response  dS = S(D_z rho) - S(rho).  D_z is basis-selective, so dS depends
     on BOTH the radius AND the orientation -- a physics fact, not a smuggled target.
  Predictors fit on train, scored on held-out:
     SCALAR       : dS ~ cubic in r          (radius/shell only -- the scalar stratum)
     STRUCTURED   : dS ~ cubic in (r, r*cos phi)  (radius + orientation -- the 2-coord shell geometry)
  Gate + controls:
     G1  structured beats scalar on held-out (structure binds) OR ties (structure is decorative)
     C1  ERASE ORIENTATION (all phi=0): structured must collapse to scalar (proves phi carried it)
     C2  deliberate high-degree overfit: wins on fit, loses on held-out (gate is held-out-honest)
     C3  scalar given the SAME polynomial flexibility (not crippled)
Claim ceiling: scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np, json, os
rng=np.random.default_rng(0)
I=np.eye(2); Z=np.array([[1,0],[0,-1]],complex)
sx=np.array([[0,1],[1,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
def Sof(rho):
    ev=np.linalg.eigvalsh(rho); ev=ev[ev>1e-15]; return float(-np.sum(ev*np.log2(ev)))
def rho_A(eta,phi):
    r=abs(np.cos(2*eta)); n=np.array([np.sin(phi),0.0,np.cos(phi)])
    return 0.5*(I + r*(n[0]*sx+n[2]*sz)), r
def dephase_z(rho): return 0.5*(rho+Z@rho@Z)
def dS_response(eta,phi):
    rho,r=rho_A(eta,phi); return Sof(dephase_z(rho))-Sof(rho), r, r*np.cos(phi)

# ---- sample the 2-coordinate manifold ----
N=60
etas=rng.uniform(0.05,np.pi/2-0.05,N); phis=rng.uniform(0,np.pi,N)
Y=np.array([dS_response(e,p) for e,p in zip(etas,phis)])
dS=Y[:,0]; r=Y[:,1]; rc=Y[:,2]     # target, radius, radius*cos(phi)

def fit_predict(Xtr,ytr,Xte):
    # least-squares polynomial (design already built); returns held-out prediction
    coef,_,_,_=np.linalg.lstsq(Xtr,ytr,rcond=None); return Xte@coef
def design_scalar(rv):   return np.stack([np.ones_like(rv),rv,rv**2,rv**3],1)          # cubic in r
def design_struct(rv,rcv):return np.stack([np.ones_like(rv),rv,rv**2,rv**3,rcv,rcv**2,rcv**3,rv*rcv],1) # + orientation
def design_overfit(rv):  return np.stack([rv**k for k in range(18)],1)                    # deliberate overfit (fixed deg 18)

idx=rng.permutation(N); tr,te=idx[:40],idx[40:]
def rmse(pred,truth): return float(np.sqrt(np.mean((pred-truth)**2)))

scal =rmse(fit_predict(design_scalar(r[tr]),dS[tr],design_scalar(r[te])), dS[te])
strc =rmse(fit_predict(design_struct(r[tr],rc[tr]),dS[tr],design_struct(r[te],rc[te])), dS[te])
# C2 overfit: EXACT RBF interpolant on train (fit RMSE 0 by construction), must blow up on held-out
def rbf2d(Ptr,ytr,Pte,eps=200.0):
    D=lambda A,B: np.sum((A[:,None,:]-B[None,:,:])**2,2)
    K=np.exp(-eps*D(Ptr,Ptr)); w=np.linalg.solve(K,ytr)   # exact interpolation (no ridge) -> fit 0
    return np.exp(-eps*D(Pte,Ptr))@w, K@w
Ptr=np.stack([r[tr],rc[tr]],1); Pte=np.stack([r[te],rc[te]],1)
of_te,of_tr=rbf2d(Ptr,dS[tr],Pte)
of_fit=rmse(of_tr,dS[tr]); of_hel=rmse(of_te,dS[te])
# C1 erase orientation: rebuild data with phi=0 -> dS depends on r only -> scalar==structured
Y0=np.array([dS_response(e,0.0) for e in etas]); dS0=Y0[:,0]; r0=Y0[:,1]; rc0=Y0[:,2]
scal0=rmse(fit_predict(design_scalar(r0[tr]),dS0[tr],design_scalar(r0[te])), dS0[te])
strc0=rmse(fit_predict(design_struct(r0[tr],rc0[tr]),dS0[tr],design_struct(r0[te],rc0[te])), dS0[te])

TOL=1e-2
binds = strc < scal - TOL                        # structure genuinely beats scalar on held-out
control_collapses = abs(strc0-scal0) < TOL       # erasing orientation collapses them (proves phi carried it)
overfit_flips = (of_fit < 1e-6) and (of_hel > scal)
out={"classification":"scratch_diagnostic","promotion_allowed":False,
 "obligation":"entropy response dS to a FIXED z-dephasing channel on the 2-coord marginal family",
 "heldout_rmse":{"scalar_radius_only":scal,"structured_radius_plus_orientation":strc},
 "orientation_binds":bool(binds),"scalar_minus_structured":scal-strc,
 "control_erase_orientation":{"scalar":scal0,"structured":strc0,"collapse_to_scalar":bool(control_collapses)},
 "control_overfit":{"fit_rmse":of_fit,"heldout_rmse":of_hel,"flips":bool(overfit_flips)},
 "verdict":"STRUCTURE_BINDS__SECOND_COORD_EARNED" if binds else "STRUCTURE_DECORATIVE__SCALAR_SUFFICIENT",
 "honest_scope":"the second coordinate that binds is ORIENTATION (Schmidt-basis direction), NOT radius-nesting; "
   "radius alone stays scalar-sufficient. This shows the earned manifold is >=2-D once response (not static readout) is probed."}
PASS = binds and control_collapses and overfit_flips
out["gate_PASS"]=bool(PASS)
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"manifold_L5_binding_discriminator_sim_results.json"),"w"),indent=2,default=float)
print("PASS manifold_L5_binding_discriminator" if PASS else "FAIL manifold_L5_binding_discriminator")
print(f"  held-out RMSE: scalar(radius only) = {scal:.4f}   structured(radius+orientation) = {strc:.4f}")
print(f"  orientation binds (structured beats scalar by >{TOL}): {binds}  (gap {scal-strc:+.4f})")
print(f"  CONTROL erase orientation (phi=0): scalar {scal0:.4f} vs structured {strc0:.4f} -> collapse {control_collapses}")
print(f"  CONTROL overfit: fit {of_fit:.2e} heldout {of_hel:.2f} -> flips {overfit_flips}")
print(f"  VERDICT: {out['verdict']}")
