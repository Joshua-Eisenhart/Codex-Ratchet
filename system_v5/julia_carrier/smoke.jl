using CliffordAlgebras, ITensors
println("=== CliffordAlgebras smoke ===")
# build a 3D Euclidean Clifford algebra Cl(3,0)
cl = CliffordAlgebra(:Cl3)
println("algebra: ", cl)
e1 = cl.e1; e2 = cl.e2; e3 = cl.e3
println("e1*e2 = ", e1*e2, " | e1^2 = ", e1*e1)
# a rotor R = exp(-θ/2 e1 e2) rotates vectors; Hopf-style sandwich R v ~R
R = exp(-0.5*0.7*(e1*e2))
v = e3
println("rotor sandwich R e3 R~ = ", R*v*reverse(R))
println()
println("=== ITensors smoke ===")
N = 6
s = siteinds("S=1/2", N)
psi = random_mps(s; linkdims=8)
# entanglement entropy at the half cut
b = N ÷ 2
orthogonalize!(psi, b)
U,S,V = svd(psi[b], (linkind(psi,b-1), siteind(psi,b)))
SvN = 0.0
for n in 1:dim(S,1)
  p = S[n,n]^2
  p>1e-12 && (global SvN -= p*log2(p))
end
println("ITensors MPS N=$N linkdim=", maxlinkdim(psi), " half-chain SvN=", round(SvN, digits=3))
println("SMOKE OK")
