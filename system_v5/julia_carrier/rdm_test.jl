using ITensors, ITensorMPS, LinearAlgebra
L = 3; N = 3L
s = siteinds("Qubit", N)
A = collect(1:L); B = collect(L+1:2L); C = collect(2L+1:3L)
function build(kind)
  psi = MPS(s, "0")
  for i in 1:L
    a=A[i]; c=C[i]; b=B[i]
    psi = apply(op("H", s, a), psi)
    psi = apply(op("CNOT", s, a, kind=="linked" ? c : b), psi; cutoff=1e-14, maxdim=64)
  end
  psi
end
# RDM of region `reg` from MPS: contract full tensor, prime kept site indices on the conj, contract.
function rdm_mat(psi, reg, s)
    T = prod(psi)
    Tc = dag(T)
    for i in reg; Tc = prime(Tc, s[i]); end
    ρ = T * Tc                      # indices: primed-kept (rows), unprimed-kept (cols)
    rows = ITensor[]
    return ρ
end
function logneg(psi, A, C, s)
    reg = vcat(A,C)
    T = prod(psi); Tc = dag(T)
    for i in reg; Tc = prime(Tc, s[i]); end
    ρ = T*Tc
    # partial transpose on C: swap primed<->unprimed for C site indices
    ρpt = ρ
    for i in C; ρpt = swapinds(ρpt, (prime(s[i]),), (s[i],)); end
    # build matrix: rows = primed kept, cols = unprimed kept
    rinds = [prime(s[i]) for i in reg]; cinds = [s[i] for i in reg]
    Cr = combiner(rinds...); Cc = combiner(cinds...)
    M = matrix(ρpt * Cr * Cc, combinedind(Cr), combinedind(Cc))
    ev = real(eigvals(0.5*(M+M')))
    return log2(sum(abs.(ev)))
end
linked = build("linked"); unlinked = build("unlinked"); prod_st = MPS(s,"0")
println("LN(A:C) linked   = ", round(logneg(linked, A, C, s), digits=4), "  (bond ", maxlinkdim(linked), ")")
println("LN(A:C) unlinked = ", round(logneg(unlinked, A, C, s), digits=4))
println("LN(A:C) product  = ", round(logneg(prod_st, A, C, s), digits=4))
