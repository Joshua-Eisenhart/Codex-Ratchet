include("common.jl")
using ChaosTools, DynamicalSystems, StaticArrays
b2run("chaostools", "system_v8/nested_manifold/results/manifold_one_julia/receipt.json") do
    # dynamic rule MUST return SVector (per package contract); use untyped SVector so ForwardDiff duals promote
    f(u,p,n) = SVector(0.9*u[1] + 0.1*sin(u[2]), 0.8*u[2])
    ds=DeterministicIteratedMap(f, SVector(0.2,0.1)); λ=lyapunovspectrum(ds,1000; Ttr=100)
    (maximum(λ), Dict("lyapunov_spectrum"=>collect(λ),"manifold_one_drive_map"=>"contractive two-coordinate surrogate fitted to receipt damping","pass"=>maximum(λ)<0))
end
