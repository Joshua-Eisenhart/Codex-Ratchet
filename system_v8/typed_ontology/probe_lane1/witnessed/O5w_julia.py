using LinearAlgebra
p = [0.25, 0.25, 0.25, 0.25]
rank_p = count(x -> x > 1e-12, p)
S0 = log2(Float64(rank_p))
S2 = -log2(dot(p, p))
println("{\"S_0_bits\":", S0, ",\"S_2_bits\":", S2, ",\"trace\":", sum(p), "}")
