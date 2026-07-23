# Authoritative Julia leg for real_vs_complex_tomography — QuantumOptics.jl.
#
# Independent recompute, no echo: builds the qubit/rebit tomography frames as
# QuantumOptics density matrices, real-vectorizes them, and computes the span
# ranks that operationalize local tomography on states: the joint state-space
# dimension vs the span of product density matrices. The discriminating scalar
# is real_tomography_gap = real_d2 - real_product_span (10 - 9 = 1 for two
# rebits; the complex branch closes at 16 - 16 = 0). Deterministic.
using QuantumOptics
using JSON
using LinearAlgebra

const RANK_TOL = 1.0e-8
const SQ2 = 1.0 / sqrt(2.0)

basis = SpinBasis(1//2)
up = spinup(basis)
dn = spindown(basis)

realvec(rho) = vcat(vec(real(Matrix(rho.data))), vec(imag(Matrix(rho.data))))
span_rank(dms) = count(>(RANK_TOL), svdvals(hcat([realvec(o) for o in dms]...)))

# --- single-qubit complex frame: the six Pauli eigenstates (span {I,X,Y,Z}) ---
qubit_kets = [up, dn,
              normalize(up + dn), normalize(up - dn),
              normalize(up + 1im * dn), normalize(up - 1im * dn)]
qubit_dms = [dm(k) for k in qubit_kets]

# --- single-rebit frame: real-amplitude states cos(t)|0> + sin(t)|1> (span {I,X,Z}) ---
thetas = [0.0, pi / 8, pi / 4, 3 * pi / 8, pi / 2]
rebit_dms = [dm(cos(t) * up + sin(t) * dn) for t in thetas]

# --- joint families: products, and products + (real-amplitude) Bell projectors ---
product_c = [tensor(a, b) for a in qubit_dms for b in qubit_dms]
product_r = [tensor(a, b) for a in rebit_dms for b in rebit_dms]
bell_phi_plus  = dm(normalize(tensor(up, up) + tensor(dn, dn)))   # (|00>+|11>)/sqrt2, real
bell_psi_plus  = dm(normalize(tensor(up, dn) + tensor(dn, up)))   # (|01>+|10>)/sqrt2, real
bell_phi_minus = dm(normalize(tensor(up, up) - tensor(dn, dn)))
bell_psi_minus = dm(normalize(tensor(up, dn) - tensor(dn, up)))

complex_d1 = span_rank(qubit_dms)
real_d1 = span_rank(rebit_dms)
complex_product_span = span_rank(product_c)
complex_d2 = span_rank(vcat(product_c, [bell_phi_plus, bell_psi_plus, bell_phi_minus, bell_psi_minus]))
real_product_span = span_rank(product_r)
real_d2 = span_rank(vcat(product_r, [bell_phi_plus, bell_psi_plus]))  # real Bells stay symmetric

complex_gap = complex_d2 - complex_product_span
real_gap = real_d2 - real_product_span

out = Dict(
    "engine" => "julia:QuantumOptics",
    "complex_d1" => complex_d1,
    "complex_d2" => complex_d2,
    "complex_product_span" => complex_product_span,
    "complex_tomography_gap" => complex_gap,
    "real_d1" => real_d1,
    "real_d2" => real_d2,
    "real_product_span" => real_product_span,
    "real_tomography_gap" => real_gap,
    "complex_local_tomography" => (complex_gap == 0 && complex_product_span == complex_d1^2),
    "real_local_tomography" => (real_gap == 0 && real_product_span == real_d1^2),
)
println(JSON.json(out))
