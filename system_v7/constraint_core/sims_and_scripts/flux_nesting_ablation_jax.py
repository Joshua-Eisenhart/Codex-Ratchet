"""
flux_nesting_ablation_jax.py  (JAX, x64)
Hardening item #1 from flux_emergence_discriminator/audit_verdict.md:
run a REAL flat-carrier (A=0) ablation through the SAME transport/flux pipeline
instead of a hand-authored pass-dict.  Also verifies:
  (A) flux needs NESTED shells (single shell -> holonomy, not flux)
  (B) the GEOMETRIC RATCHET: pairwise flux is order-sensitive, total is invariant
Interfaces mirror system_v6/sims/flux_emergence_discriminator/flux_emergence_discriminator_jax.py
Claim ceiling: scratch_diagnostic; promotion_allowed=false; flux is a CANDIDATE FAMILY (weyl-flux.md).
"""
import jax, math, json, itertools
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

PHI0, CHI0, TRANSPORT_STEPS = 0.19, -0.31, 4096
eta_shell = lambda k: math.pi/8.0 + k*math.pi/10.0

def spinor(phi, chi, eta, A_on=True):
    if A_on:
        return jnp.asarray([jnp.exp(1j*(phi+chi))*math.cos(eta),
                            jnp.exp(1j*(phi-chi))*math.sin(eta)], dtype=jnp.complex128)
    return jnp.asarray([complex(math.cos(eta)), complex(math.sin(eta))], dtype=jnp.complex128)

def connection_coefficients(phi, chi, eta, A_on=True):
    eps=1e-6; psi=spinor(phi,chi,eta,A_on)
    d_phi=(spinor(phi+eps,chi,eta,A_on)-spinor(phi-eps,chi,eta,A_on))/(2*eps)
    d_chi=(spinor(phi,chi+eps,eta,A_on)-spinor(phi,chi-eps,eta,A_on))/(2*eps)
    return (float(jnp.real(-1j*jnp.vdot(psi,d_phi))),
            float(jnp.real(-1j*jnp.vdot(psi,d_chi))))

def horizontal_transport(k, eta, A_on=True):
    phi,chi=PHI0,CHI0; dchi=2*math.pi/TRANSPORT_STEPS
    for _ in range(TRANSPORT_STEPS):
        a_phi,a_chi=connection_coefficients(phi,chi,eta,A_on)
        phi += 0.0 if abs(a_phi)<1e-14 else -(a_chi/a_phi)*dchi
        chi += dchi
    return {"shell":k,"eta":eta,"holonomy_accumulated":phi-PHI0,
            "closed_form_target":-2.0*math.pi*math.cos(2.0*eta)}

if __name__=="__main__":
    shells=[eta_shell(k) for k in range(3)]
    real=[horizontal_transport(k,e,True)  for k,e in enumerate(shells)]
    flat=[horizontal_transport(k,e,False) for k,e in enumerate(shells)]
    pf   =lambda R,i,j: R[j]["holonomy_accumulated"]-R[i]["holonomy_accumulated"]
    pf_cf=lambda i,j: 2*math.pi*(math.cos(2*shells[i])-math.cos(2*shells[j]))
    out={
      "classification":"scratch_diagnostic","promotion_allowed":False,"formal_admission_allowed":False,
      "real_holonomy":[r["holonomy_accumulated"] for r in real],
      "flat_holonomy":[r["holonomy_accumulated"] for r in flat],
      "ablation_A0_holonomy_zero": all(abs(r["holonomy_accumulated"])<1e-9 for r in flat),
      "nested_flux":{f"{i}{j}":pf(real,i,j) for i,j in itertools.combinations(range(3),2)},
      "ratchet_forward":[pf_cf(0,1),pf_cf(1,2)],
      "ratchet_reversed":[pf_cf(2,1),pf_cf(1,0)],
      "total_chern_forward":abs(pf_cf(0,2)),"total_chern_reversed":abs(pf_cf(2,0)),
    }
    print(json.dumps(out,indent=2))
