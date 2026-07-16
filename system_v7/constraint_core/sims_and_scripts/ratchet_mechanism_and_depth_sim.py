"""
ratchet_mechanism_and_depth_sim.py  (numpy control-lane; pure QIT, no jargon labels)

THE RATCHET AND THE MANIFOLD, in actual mathematics. No personal notation, no downstream axes.
Root primitive: constrained distinguishability = Umegaki relative entropy S(rho||sig)=Tr[rho(log rho-log sig)].
  1. PAWL  = data-processing inequality (CPTP contracts S, unitary preserves; reverse is non-CPTP).
  2. DRIVE = relative-entropy gradient to the fixed point; ->0 at demand-closure ("no gradient no ratchet").
  3. SURFACE identity: BKM(Kubo-Mori) metric == Hessian of relative entropy (entropy IS geometry).
  4. DEPTH  = MSS on the Cayley-Dickson tower: N01 forces C->H (=su(2)); O (nonassoc) NOT forced.
  5. FLOOR  = qubit bracket is Lie (Jacobi=0); Im(O) is Malcev (Jacobi!=0) -> octonions constructible not forced.
Claim ceiling: scratch_diagnostic; promotion_allowed=false.
"""
import numpy as np, json, os
def logH(A):
    w,V=np.linalg.eigh(A); w=np.clip(w,1e-300,None); return (V*np.log(w))@V.conj().T
def relent(rho,sig): return float(np.real(np.trace(rho@(logH(rho)-logH(sig)))))
def cptp(rho,Ks): return sum(K@rho@K.conj().T for K in Ks)
def norm(x): return float(np.linalg.norm(x))
out={"classification":"scratch_diagnostic","promotion_allowed":False,"units":"nats"}

# 1. PAWL
rho=np.array([[0.72,0.20+0.05j],[0.20-0.05j,0.28]],complex); sig=np.array([[0.55,0],[0,0.45]],complex)
g=0.35; AD=[np.array([[1,0],[0,np.sqrt(1-g)]],complex),np.array([[0,np.sqrt(g)],[0,0]],complex)]
p=0.4; DEPOL=[np.sqrt(1-3*p/4)*np.eye(2)]+[np.sqrt(p/4)*P for P in
      (np.array([[0,1],[1,0]],complex),np.array([[0,-1j],[1j,0]],complex),np.array([[1,0],[0,-1]],complex))]
U=np.array([[np.cos(.6),-np.sin(.6)],[np.sin(.6),np.cos(.6)]],complex); b=relent(rho,sig)
out["pawl_DPI"]={"S_before":b,"after_damping":relent(cptp(rho,AD),cptp(sig,AD)),
  "after_depol":relent(cptp(rho,DEPOL),cptp(sig,DEPOL)),"after_unitary":relent(U@rho@U.conj().T,U@sig@U.conj().T)}
out["pawl_DPI"]["monotone_contracts_and_unitary_preserves"]=bool(
  out["pawl_DPI"]["after_damping"]<b-1e-9 and out["pawl_DPI"]["after_depol"]<b-1e-9 and abs(out["pawl_DPI"]["after_unitary"]-b)<1e-9)

# 2. DRIVE
rs=np.eye(2)/2; r=rho.copy(); traj=[]
for _ in range(9): traj.append(relent(r,rs)); r=cptp(r,DEPOL)
grads=[traj[i]-traj[i-1] for i in range(1,len(traj))]
out["drive_gradient"]={"S_trajectory":[round(x,6) for x in traj],"gradients":[round(x,6) for x in grads],
  "monotone_to_zero":bool(all(gr<0 for gr in grads) and traj[-1]<1e-3)}

# 3. SURFACE = BKM = Hessian
def rho_of(th,rr=0.8):
    nx,nz=np.sin(th),np.cos(th)
    return .5*(np.eye(2)+rr*(nx*np.array([[0,1],[1,0]],complex)+nz*np.array([[1,0],[0,-1]],complex)))
th0,h=0.6,1e-4; d=(rho_of(th0+h)-rho_of(th0-h))/(2*h); ev,V=np.linalg.eigh(rho_of(th0)); dR=V.conj().T@d@V
c=np.array([[(np.log(ev[i])-np.log(ev[j]))/(ev[i]-ev[j]) if abs(ev[i]-ev[j])>1e-12 else 1/ev[i] for j in range(2)] for i in range(2)])
gb=float(np.sum(np.abs(dR)**2*c)); f=lambda t: relent(rho_of(t),rho_of(th0)); hs=(f(th0+h)-2*f(th0)+f(th0-h))/h**2
out["surface_entropy_is_geometry"]={"g_BKM":gb,"hessian_relent":hs,"abs_diff":abs(gb-hs),"same_tensor":bool(abs(gb-hs)<1e-6)}

# 4-5. DEPTH + FLOOR
def qmul(a,b):
    a0,a1,a2,a3=a;b0,b1,b2,b3=b
    return np.array([a0*b0-a1*b1-a2*b2-a3*b3,a0*b1+a1*b0+a2*b3-a3*b2,a0*b2-a1*b3+a2*b0+a3*b1,a0*b3+a1*b2-a2*b1+a3*b0])
tr=[(1,2,3),(1,4,5),(1,7,6),(2,4,6),(2,5,7),(3,4,7),(3,6,5)];IDX=np.zeros((8,8),int);SGN=np.zeros((8,8))
for i in range(8):IDX[0,i]=i;SGN[0,i]=1;IDX[i,0]=i;SGN[i,0]=1
for i in range(1,8):IDX[i,i]=0;SGN[i,i]=-1
for a,bb,cc in tr:
    for x,y,z in[(a,bb,cc),(bb,cc,a),(cc,a,bb)]:IDX[x,y]=z;SGN[x,y]=1;IDX[y,x]=z;SGN[y,x]=-1
def omul(u,v):
    w=np.zeros(8)
    for i in range(8):
        if u[i]==0:continue
        for j in range(8):
            if v[j]==0:continue
            w[IDX[i,j]]+=SGN[i,j]*u[i]*v[j]
    return w
rng=np.random.default_rng(0)
def st(mul,dim):
    cm=[];asz=[]
    for _ in range(200):
        a=rng.standard_normal(dim);bb=rng.standard_normal(dim);cc=rng.standard_normal(dim)
        cm.append(norm(mul(a,bb)-mul(bb,a)));asz.append(norm(mul(mul(a,bb),cc)-mul(a,mul(bb,cc))))
    return float(np.mean(cm)),float(np.mean(asz))
cH,aH=st(qmul,4);cO,aO=st(omul,8)
sx=np.array([[0,1],[1,0]],complex);sy=np.array([[0,-1j],[1j,0]],complex);sz=np.array([[1,0],[0,-1]],complex)
def brm(A,B):return A@B-B@A
jsu2=norm(brm(brm(1j*sx,1j*sy),1j*sz)+brm(brm(1j*sy,1j*sz),1j*sx)+brm(brm(1j*sz,1j*sx),1j*sy))
def obr(u,v):return omul(u,v)-omul(v,u)
e=lambda i:np.eye(8)[i]
joct=norm(obr(obr(e(1),e(2)),e(4))+obr(obr(e(2),e(4)),e(1))+obr(obr(e(4),e(1)),e(2)))
out["depth_tower"]={"H_comm":cH,"H_assoc":aH,"O_comm":cO,"O_assoc":aO,
  "N01_forces_C_to_H":bool(cH>1e-3 and aH<1e-9),"O_requires_forced_T01":bool(aO>1e-3)}
out["floor_lie_vs_malcev"]={"su2_jacobiator":jsu2,"octonion_jacobiator":joct,
  "qubit_is_lie":bool(jsu2<1e-9),"octonion_is_malcev_not_lie":bool(joct>1e-3),
  "octonions_constructible_not_forced":bool(jsu2<1e-9 and joct>1e-3)}

PASS=(out["pawl_DPI"]["monotone_contracts_and_unitary_preserves"] and out["drive_gradient"]["monotone_to_zero"]
      and out["surface_entropy_is_geometry"]["same_tensor"] and out["depth_tower"]["N01_forces_C_to_H"]
      and out["floor_lie_vs_malcev"]["octonions_constructible_not_forced"])
out["verdict"]="PASS" if PASS else "FAIL"
json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"ratchet_mechanism_and_depth_sim_results.json"),"w"),indent=2,default=float)
print("PASS ratchet_mechanism_and_depth" if PASS else "FAIL")
print(f"  pawl: S {out['pawl_DPI']['S_before']:.4f} -> damp {out['pawl_DPI']['after_damping']:.4f}, unitary {out['pawl_DPI']['after_unitary']:.4f} (preserved)")
print(f"  drive: S_traj[-1]={traj[-1]:.2e} gradient->0")
print(f"  surface: g_BKM {gb:.8f} == hessian {hs:.8f} (diff {abs(gb-hs):.1e})")
print(f"  depth: H comm {cH:.3f}/assoc {aH:.1e}; O assoc {aO:.3f}; su2 Jacobi {jsu2:.1e}; O Jacobi {joct:.3f}")
