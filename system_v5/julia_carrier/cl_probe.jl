using CliffordAlgebras
cl = CliffordAlgebra(:Cl3)
R = exp(-0.5*0.7*(cl.e1*cl.e2))
println("R = ", R)
println("typeof R = ", typeof(R))
println("propertynames(R) = ", propertynames(R))
# try various coefficient accessors
for acc in [:e1e2, :e2e3, :e3e1]
  try; println("R.$acc = ", getproperty(R, acc)); catch e; println("R.$acc ERR"); end
end
try; println("coefficients(R) = ", CliffordAlgebras.coefficients(R)); catch e; println("coefficients ERR ", e); end
try; println("vector(R) = ", CliffordAlgebras.vector(R)); catch; println("vector ERR"); end
try; println("CliffordAlgebras.scalar(R) = ", CliffordAlgebras.scalar(R)); catch e; println("scalar ERR ", e); end
# matrix representation?
try; println("matrix(R) = ", CliffordAlgebras.matrix(R)); catch; println("no matrix()"); end
