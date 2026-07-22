using QuantumOptics
using JSON
vals = [0.25, 0.75]
s0 = log(2.0)
s1 = -sum(v * log(v) for v in vals)
println(JSON.json(Dict("engine" => "julia:QuantumOptics", "min_gap_S0_S1" => s0 - s1, "one_way_witness" => true)))
