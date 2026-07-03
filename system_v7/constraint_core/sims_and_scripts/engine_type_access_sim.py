"""
Engine-type access law (the eight-of-sixteen law) as pure structure.
No jargon in the math: indices t0..t7, operators Ti/Te/Fi/Fe, sheet sign eps in {+1,-1}.
Rosetta names live in rosetta_layer.json. scratch_diagnostic; promotion_allowed=false.

Claim: the 16 stages (8 terrains x 2 native operators) split into two engines by Weyl
chirality eps. Each engine accesses exactly 8. The engine type is the GLOBAL SIGN of the
loop geometric phase (Left all +, Right all -). Forcing a stage onto the wrong sheet flips
its geometric phase (8/8) -> the two 8-sets are genuinely non-transferable pole-mirrors.
Requires: numpy.
"""
import numpy as np
I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex); sy=np.array([[0,-1j],[1j,0]],complex); sz=np.array([[1,0],[0,-1]],complex)
sp=0.5*(sx+1j*sy); sm=0.5*(sx-1j*sy); H0=sz.copy()
def D(L,r): return L@r@L.conj().T-0.5*(L.conj().T@L@r+r@L.conj().T@L)
def comm(A,r): return A@r-r@A
def bloch(r): return np.array([np.trace(r@s).real for s in (sx,sy,sz)])
kap=1.0; g=0.35
# terrain[index] = (native_eps, pole_dir, kind); in-terrains t0-3 native eps=+1, out t4-7 eps=-1
terr={0:(+1,+1,'damp'),1:(+1,0,'depol'),2:(+1,-1,'damp'),3:(+1,0,'proj'),
      4:(-1,-1,'damp'),5:(-1,0,'depol'),6:(-1,+1,'damp'),7:(-1,0,'proj')}
native_ops={0:('Ti','Fi'),1:('Ti','Fi'),4:('Ti','Fi'),5:('Ti','Fi'),
            2:('Te','Fe'),3:('Te','Fe'),6:('Te','Fe'),7:('Te','Fe')}
def terrain_gen(ti,eps):
    _,pole,kind=terr[ti]
    def X(r):
        out=-1j*g*comm(eps*H0,r)
        if kind=='damp': out=out+kap*D(sp if pole>0 else sm,r)
        elif kind=='depol': out=out+0.5*kap*(D(sx,r)+D(sy,r))
        elif kind=='proj': out=out+kap*D(sz,r)
        return out
    return X
def op_gen(name):
    if name=='Ti': return lambda r:0.6*D(sz,r)
    if name=='Te': return lambda r:0.6*D(sx,r)
    if name=='Fi': return lambda r:-1j*comm(0.5*sx,r)
    if name=='Fe': return lambda r:-1j*comm(0.5*sz,r)
def stage_loop_area(ti,op,eps,steps=400):
    Xt=terrain_gen(ti,eps); Xo=op_gen(op); r=0.5*(I2+0.6*sx); pts=[]
    for k in range(steps):
        u=2*np.pi*k/steps
        drive=lambda r: Xt(r)+np.cos(u)*Xo(r)-1j*np.sin(u)*eps*comm(0.5*H0,r)
        r=r+0.01*drive(r); r=0.5*(r+r.conj().T); r=r/np.trace(r).real; pts.append(bloch(r))
    p=np.array(pts); x,y=p[:,0],p[:,1]
    return 0.5*np.sum(x[:-1]*y[1:]-x[1:]*y[:-1])
if __name__=="__main__":
    L=[(t,op) for t in range(0,4) for op in native_ops[t]]
    R=[(t,op) for t in range(4,8) for op in native_ops[t]]
    print("Left engine (eps=+1) accesses t0-t3, Right (eps=-1) accesses t4-t7; 8 each, 16 total.")
    La=[stage_loop_area(t,op,+1) for t,op in L]; Ra=[stage_loop_area(t,op,-1) for t,op in R]
    print("Left  geometric phases:",np.round(La,3)," all>0:",all(a>0 for a in La))
    print("Right geometric phases:",np.round(Ra,3)," all<0:",all(a<0 for a in Ra))
    flips=sum(np.sign(stage_loop_area(t,op,+1))!=np.sign(stage_loop_area(t,op,-1)) for t,op in L)
    print(f"access violation (Left stages on Right sheet): geometric phase flips {flips}/8")
