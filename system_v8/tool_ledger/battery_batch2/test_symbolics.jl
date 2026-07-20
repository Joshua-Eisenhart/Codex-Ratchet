include("common.jl")
using Symbolics
b2run("symbolics", "system_v8/deep_integration/results/dynamics_fields/receipt.json") do
    @variables t γ x; D = Differential(t); eq = expand_derivatives(D(x) ~ -γ*x)
    # correct extraction: Equation has .rhs (no Symbolics.rhs)
    rhs = eq.rhs; ok = isequal(rhs, -γ*x)
    (-1.0, Dict("derived_law"=>string(eq),"pysindy_reference_coefficient"=>"-gamma","pass"=>ok,"extracted_rhs"=>string(rhs)))
end
