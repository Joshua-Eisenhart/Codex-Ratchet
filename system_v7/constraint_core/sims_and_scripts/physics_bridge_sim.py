"""
physics_bridge_sim.py -- the constraint core reproduces two pieces of ESTABLISHED,
experimentally-confirmed physics that sit exactly on the information<->physics seam.
NOT a ToE validation -- a check that the engine's own channels obey known physical law.

  (1) LANDAUER'S PRINCIPLE (the info<->physics bridge): erasing a bit costs >= kT ln2.
      The dissipative terrains RESET the qubit = logical erasure. In the pure-dissipation
      limit the entropy removed from the system is exactly 1 bit (S:1->0, purity->1), so
      the bath must absorb >= kT ln2. The coherent drive only makes erasure PARTIAL, never
      cheaper than the bound. Szilard's engine is the exact reverse (extract kT ln2 / bit).

  (2) EINSELECTION / pointer states (Zurek's predictability sieve): the environment SELECTS
      which states survive decoherence. Ti (z-dephasing) einselects {|0>,|1>}: only they stay
      pure; superpositions decay to purity 0.5. Te einselects {|+>,|->}. Made exact: the
      pointer states ARE the purity-1 FIXED POINTS of the channel (Liouvillian null space);
      coherences decay at rate 2. Einselection as an eigen-problem = "an attractor basin that
      selects for itself" in the language of decoherence -- selection built into the
      constraint, not added.

Uses QuTiP (standard QIT). scratch_diagnostic; promotion_allowed=false.
"""
import sys
try:
    import numpy as np, qutip as qt
except ImportError as e:
    print(f"SKIP_OPTIONAL physics_bridge_sim: missing tool ({e.name}); pip install qutip")
    sys.exit(0)

sx,sy,sz=qt.sigmax(),qt.sigmay(),qt.sigmaz(); I2=qt.qeye(2); sm=0.5*(sx-1j*sy)
def S_bits(r): return float(qt.entropy_vn(r,base=2))
def purity(r): return float((r*r).tr().real)

# (1) Landauer -- pure dissipation saturates the bound
rho0=I2/2
L_pure=qt.liouvillian(0*sz,[np.sqrt(1.0)*sm])
rf=qt.vector_to_operator((10.0*L_pure).expm()*qt.operator_to_vector(rho0)); rf=(rf+rf.dag())/2; rf=rf/rf.tr()
dS=S_bits(rf)-S_bits(rho0); bath_min=-dS; kTln2=1.380649e-23*300.0*np.log(2)
print(f"(1) Landauer: erase 1 bit, S {S_bits(rho0):.3f}->{S_bits(rf):.4f}; bath dump >= {bath_min:.4f} bit; purity {purity(rf):.4f}")
print(f"    kT ln2 @300K = {kTln2:.3e} J/bit")

# (2) Einselection -- each dephasing channel selects its own pointer basis
def surv(Lgen,b):
    r=0.5*(I2+b[0]*sx+b[1]*sy+b[2]*sz)
    rr=qt.vector_to_operator((3.0*Lgen).expm()*qt.operator_to_vector(r)); rr=(rr+rr.dag())/2; rr=rr/rr.tr()
    return purity(rr)
Lz=qt.liouvillian(0*sz,[np.sqrt(1.0)*sz]); Lx=qt.liouvillian(0*sz,[np.sqrt(1.0)*sx])
z_on_z, z_on_x = surv(Lz,(0,0,1)), surv(Lx,(0,0,1))
x_on_z, x_on_x = surv(Lz,(1,0,0)), surv(Lx,(1,0,0))
print(f"(2) einselection: |0> survives z-deph {z_on_z:.3f} / x-deph {z_on_x:.3f}; |+> survives z-deph {x_on_z:.3f} / x-deph {x_on_x:.3f}")
# pointer states = purity-1 fixed points of z-dephasing
w,v=np.linalg.eig(Lz.full()); rates=sorted(round(abs(x.real),3) for x in w)
pointers=[]
for i in [k for k in range(4) if abs(w[k])<1e-9]:
    op=v[:,i].reshape(2,2).T; op=(op+op.conj().T)/2; tr=np.trace(op).real
    if abs(tr)>1e-9:
        op=op/tr; pointers.append((round(np.trace(op@op).real,3),round(np.trace(op@sz.full()).real,3)))
print(f"    z-deph fixed points (purity,<sz>): {pointers}; decoherence rates {rates}")

assert bath_min>0.99 and purity(rf)>0.999, "Landauer must saturate at 1 bit in the pure limit"
assert abs(z_on_z-1)<1e-3 and abs(z_on_x-0.5)<1e-3, "z-deph must einselect the z-basis"
assert abs(x_on_x-1)<1e-3 and abs(x_on_z-0.5)<1e-3, "x-deph must einselect the x-basis"
assert sorted([p[1] for p in pointers])==[-1.0,1.0], "pointer states must be |0>,|1>"
print("\nPASS physics_bridge_sim")
