using QuantumOptics
using JSON
b = SpinBasis(1//2)
rho = Operator(b, ComplexF64[0.5 0.25; 0.25 0.5])
diag_rho = Operator(b, ComplexF64[0.5 0.0; 0.0 0.5])
println(JSON.json(Dict("engine" => "julia:QuantumOptics", "vn_entropy_rho" => real(entropy_vn(rho)), "shannon_dephased_rho" => real(entropy_vn(diag_rho)), "one_way_witness" => true)))
