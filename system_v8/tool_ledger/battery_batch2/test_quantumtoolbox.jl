include("common.jl")
using QuantumToolbox, LinearAlgebra
b2run("quantumtoolbox", "system_v8/engine_estate/results/integration/handoff_jax.json") do
    # The real seven-node manifold excitation profile is the initial channel state.
    handoff = JSON3.read(read(joinpath(@__DIR__, "..", "..", "engine_estate", "results", "integration", "handoff_jax.json"), String))
    e, T, gamma = Float64.(handoff.excitation_profile), Float64(handoff.T), Float64(handoff.gamma_star)
    # Qobj mesolve is deliberately attempted on the real amplitude-damping law.
    b = basis(2, 1); sm = destroy(2); H = 0.0 * sm
    vals = Float64[]
    for p in e
        rho0 = p * ket2dm(b) + (1-p) * ket2dm(basis(2, 0))
        sol = mesolve(H, rho0, [0.0, T], [sqrt(gamma) * sm])
        push!(vals, real(expect(ket2dm(b), sol.states[end])))
    end
    expected = e .* exp(-gamma*T)
    dev = maximum(abs.(vals .- expected))
    (dev, Dict("max_population_error"=>dev, "S_master_reference"=>4.799504063233, "gate"=>1e-8,
               "pass"=>dev < 1e-8, "n_real_nodes"=>length(e)))
end
