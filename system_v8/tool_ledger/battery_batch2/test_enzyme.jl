include("common.jl")
using Enzyme
b2run("enzyme", "system_v8/nested_manifold/results/manifold_one_julia/receipt.json") do
    # correct annotation attempt: Const(f) for the closure (no deriv through captured target), Duplicated for primal arg
    x = [0.2, -0.1, 0.4]; target=[0.1,0.2,0.3]; f(z)=sum((z .- target).^2)
    dx=zero(x)
    # If Enzyme genuinely cannot differentiate this closure class under static activity, the resulting exception makes BLOCKED honest.
    Enzyme.autodiff(Enzyme.Reverse, Const(f), Active, Duplicated(x, dx))
    analytic=2 .* (x .- target); err=maximum(abs.(dx.-analytic)); (err, Dict("gradient_max_error_vs_analytic"=>err,"pass"=>err<1e-10))
end
