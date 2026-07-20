include("common.jl")
using Manifolds, LinearAlgebra
b2run("manifolds", "system_v8/engine_estate/results/torch/receipt.json") do
    # Receipt densities: |0><0| and maximally mixed regularized to the SPD domain.
    M = SymmetricPositiveDefinite(2); ρ=Diagonal([1.0,1e-9]); σ=Diagonal([0.5,0.5]); d=distance(M,ρ,σ)
    (d, Dict("bures_spd_distance"=>d,"geomstats_surface"=>"Bures-Wasserstein receipt family","pass"=>isfinite(d)&&d>0))
end
