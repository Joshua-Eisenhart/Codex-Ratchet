using CliffordAlgebras, ITensors, ITensorMPS
N = 6
s = siteinds("S=1/2", N)
psi = random_mps(s; linkdims=8)
b = N ÷ 2
orthogonalize!(psi, b)
U,S,V = svd(psi[b], (linkind(psi,b-1), siteind(psi,b)))
SvN = 0.0
for n in 1:dim(S,1)
  p = S[n,n]^2
  p>1e-12 && (global SvN -= p*log2(p))
end
println("ITensors+ITensorMPS MPS N=$N maxlinkdim=", maxlinkdim(psi), " half-chain SvN=", round(SvN,digits=3))
println("SMOKE2 OK")
