using ITensors, ITensorMPS, LinearAlgebra
# Qubit sites; build LINKED state: bell(A_i, C_i) = H(A_i), CNOT(A_i->C_i). long-range via apply auto-swap.
L = 3; N = 3L
s = siteinds("Qubit", N)
A = collect(1:L); B = collect(L+1:2L); C = collect(2L+1:3L)   # 1-indexed
function build(kind)
  psi = MPS(s, "0")
  for i in 1:L
    a = A[i]; c = C[i]; b = B[i]
    psi = apply(op("H", s, a), psi)
    tgt = kind=="linked" ? c : b
    psi = apply(op("CNOT", s, a, tgt), psi; cutoff=1e-14, maxdim=64)
  end
  return psi
end
# reduced density matrix of region (A ∪ C) -> dense, then partial transpose log-negativity
function region_logneg(psi, A, C)
  reg = sort(vcat(A,C))
  ρ = reduced_density_matrix(psi, reg)         # ITensorMPS: dense RDM as ITensor
  return ρ
end
linked = build("linked"); unlinked = build("unlinked")
println("linked maxlinkdim=", maxlinkdim(linked), " unlinked maxlinkdim=", maxlinkdim(unlinked))
# entanglement entropy A|rest as a sanity carrier-depth check
orthogonalize!(linked, L)
U,S,V = svd(linked[L], (linkind(linked,L-1), siteind(linked,L)))
println("has reduced_density_matrix: ", isdefined(ITensorMPS, :reduced_density_matrix))
