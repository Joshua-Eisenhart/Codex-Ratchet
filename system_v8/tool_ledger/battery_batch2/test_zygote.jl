include("common.jl")
using Zygote, JSON3
b2run("zygote", "system_v8/nested_manifold/results/manifold_one_julia/receipt.json") do
    # real key that exists: data.max_abs_diff_vs_numpy_receipt.S_L (scalar)
    rec = JSON3.read(read(joinpath(@__DIR__, "..", "..", "nested_manifold", "results", "manifold_one_julia", "receipt.json"), String))
    target_val = Float64(rec.data.max_abs_diff_vs_numpy_receipt.S_L)
    x = [0.2, -0.1, 0.4]; loss(z) = sum((z .- target_val).^2) + 0.0  # scalar target replicated
    g = Zygote.gradient(loss, x)[1]; h=1e-6; fd=[(loss(x .+ h.*(1:3 .== i))-loss(x .- h.*(1:3 .== i)))/(2h) for i in 1:3]
    err=maximum(abs.(g.-fd)); (err, Dict("gradient_max_error_vs_finite_difference"=>err,"pass"=>err<1e-6,"used_key"=>"data.max_abs_diff_vs_numpy_receipt.S_L"))
end
