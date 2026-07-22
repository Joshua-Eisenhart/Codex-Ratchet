# Authoritative Julia leg for the pure_to_vn arrow — QuantumOptics.jl carries
# the load-bearing witness; the Python side is jax-based.
#
# Witness: partial trace is one-way — two ORTHOGONAL global pure states map to
# the SAME reduced density operator (I/2), so von Neumann entropy is born at the
# cut and cannot be inverted back to the global state.
using QuantumOptics
using JSON

b = SpinBasis(1//2)
b2 = b ⊗ b

up = spinup(b)
dn = spindown(b)

# psi = Bell (|00> + |11>)/sqrt2 ; phi = (I⊗X) psi = (|01> + |10>)/sqrt2
psi = normalize(tensor(up, up) + tensor(dn, dn))
phi = normalize(tensor(up, dn) + tensor(dn, up))

rho_psi = dm(psi)
rho_phi = dm(phi)

rho_A_psi = ptrace(rho_psi, 2)   # trace out subsystem 2 -> reduced on subsystem 1
rho_A_phi = ptrace(rho_phi, 2)

S_psi = real(entropy_vn(rho_A_psi))            # expect ln2 = 0.6931...
S_phi = real(entropy_vn(rho_A_phi))

# marginals identical, globals orthogonal -> partial trace is non-injective
marginal_gap = tracedistance(rho_A_psi, rho_A_phi)           # 0.0 -> identical marginals
global_gap = tracedistance(rho_psi, rho_phi)                 # 1.0 -> orthogonal, distinct globals
marginal_fidelity = real(fidelity(rho_A_psi, rho_A_phi))     # 1.0 -> identical marginals

out = Dict(
    "engine" => "julia:QuantumOptics",
    "S_vn_reduced_nats" => S_psi,
    "S_vn_reduced_phi_nats" => S_phi,
    "ln2" => log(2.0),
    "marginal_trace_gap" => marginal_gap,
    "global_trace_gap_psi_phi" => global_gap,
    "marginal_fidelity_psi_phi" => marginal_fidelity,
    "one_way_witness" => (global_gap > 1.0 - 1e-9) && (marginal_gap < 1e-9) && (marginal_fidelity > 1.0 - 1e-9),
)
println(JSON.json(out))
