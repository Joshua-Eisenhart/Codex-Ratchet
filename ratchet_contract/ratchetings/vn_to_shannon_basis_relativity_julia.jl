# Authoritative Julia leg for the vn_to_shannon basis-relativity disclosure —
# QuantumOptics.jl basis rotation. Witness: the SAME dephasing/pinching channel
# raises entropy in the FIXED computational (pointer) basis but acts as the
# identity in the state's OWN eigenbasis — the one-way arrow is basis-relative.
using QuantumOptics
using JSON

b = SpinBasis(1//2)
rho = Operator(b, ComplexF64[0.5 0.25; 0.25 0.5])

# Pinch in the FIXED computational basis (the pointer basis vn_to_shannon commits to):
m = rho.data
d_comp = Operator(b, ComplexF64[m[1, 1] 0.0; 0.0 m[2, 2]])

# Basis rotation: pinch after rotating into rho's OWN eigenbasis — keep the
# diagonal weights <v_i|rho|v_i> on the eigenprojectors |v_i><v_i|, rotate back.
evals, ekets = eigenstates(dense(rho))
d_eigen = sum(real(dagger(ekets[i]) * rho * ekets[i]) * projector(ekets[i]) for i in 1:2)

S_rho = real(entropy_vn(rho))
S_comp = real(entropy_vn(d_comp))
S_eigen = real(entropy_vn(d_eigen))
recon = maximum(abs.((d_eigen - rho).data))

out = Dict(
    "engine" => "julia:QuantumOptics",
    "vn_entropy_rho" => S_rho,
    "comp_dephased_entropy" => S_comp,
    "comp_basis_entropy_gap" => S_comp - S_rho,
    "eigen_dephased_entropy" => S_eigen,
    "eigenbasis_gap" => abs(S_eigen - S_rho),
    "eigen_reconstruction_error" => recon,
    "basis_relative_witness" => (S_comp - S_rho > 1e-9) && (abs(S_eigen - S_rho) < 1e-9) && (recon < 1e-9),
)
println(JSON.json(out))
