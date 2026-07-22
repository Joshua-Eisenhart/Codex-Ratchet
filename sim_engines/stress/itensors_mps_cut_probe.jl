# UNOFFICIAL STRESS PROBE — Julia leg (ITensors/ITensorMPS + QuantumOptics cross-check).
# Called by itensors_mps_cut_probe.py; prints one JSON line to stdout.
#
# What ITensors does here that dense QuantumOptics matrices cannot scale to:
# entanglement entropy across an MPS cut via orthogonalize + bond SVD — the
# tensor-network path (cost ~ chi^3, not 2^N).
#
#   1. 8-site GHZ as an MPS on siteinds("S=1/2"): orthogonalize at the middle
#      cut (bond 4|5), SVD the bond, S = -sum p log2 p — expected exactly 1 bit;
#      bond dimension of the GHZ MPS expected exactly 2.
#   2. NEGATIVE CONTROL through the SAME MPS path: a random product state
#      (kron of random single-qubit states) — expected 0 bits.
#   3. INDEPENDENT CROSS-CHECK: 4-site GHZ dense via QuantumOptics
#      entropy_vn of the half-chain reduced density matrix — expected 1 bit.

using ITensors, ITensorMPS
using QuantumOptics
using LinearAlgebra
using Random
using JSON

"Entropy in bits across the cut left of bond b|b+1, via orthogonalize + bond SVD."
function mps_cut_entropy_bits(psi::MPS, b::Int)
    psi = orthogonalize(psi, b)
    U, S, V = svd(psi[b], (linkind(psi, b - 1), siteind(psi, b)))
    s = 0.0
    for n in 1:dim(S, 1)
        p = S[n, n]^2
        if p > 1e-14
            s -= p * log2(p)
        end
    end
    return s
end

N = 8
b = div(N, 2)                       # middle cut: bond 4|5
sites = siteinds("S=1/2", N)

# 1. GHZ_8 as MPS (dense amplitudes -> MPS; only |0...0> and |1...1> nonzero,
# so basis-ordering convention is irrelevant).
ampl = zeros(Float64, 2^N)
ampl[1] = 1 / sqrt(2)
ampl[end] = 1 / sqrt(2)
ghz = MPS(ampl, sites; cutoff=1e-12)
ghz_bits = mps_cut_entropy_bits(ghz, b)
ghz_bond_dim = maxlinkdim(ghz)

# 2. NEGATIVE CONTROL, same path: random product state (seeded).
Random.seed!(11)
qs = [normalize!(randn(2) .+ im .* randn(2)) for _ in 1:N]
v = qs[1]
for k in 2:N
    global v = kron(v, qs[k])
end
prod_psi = MPS(collect(v), sites; cutoff=1e-12)
prod_bits = mps_cut_entropy_bits(prod_psi, b)
prod_bond_dim = maxlinkdim(prod_psi)

# 3. INDEPENDENT CROSS-CHECK: 4-site GHZ dense via QuantumOptics (dim 16).
bs = SpinBasis(1 // 2)
up, dn = spinup(bs), spindown(bs)
ghz4 = (tensor(up, up, up, up) + tensor(dn, dn, dn, dn)) / sqrt(2)
rho_half = ptrace(dm(ghz4), [3, 4])           # reduce to half chain (sites 1,2)
qo_dense_bits = real(entropy_vn(rho_half)) / log(2)   # entropy_vn can return complex with ~0 imag

print(JSON.json(Dict(
    "ghz8_mps_cut_bits" => ghz_bits,
    "ghz8_bond_dim" => ghz_bond_dim,
    "product_mps_cut_bits" => prod_bits,
    "product_bond_dim" => prod_bond_dim,
    "qo_dense_ghz4_half_bits" => qo_dense_bits,
)))
