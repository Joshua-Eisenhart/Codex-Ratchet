
using JSON
mods = ["QuantumOptics", "QuantumToolbox", "Yao", "QXTools", "QXZoo", "QXGraphDecompositions", "Attractors", "DynamicalSystems", "Basins", "Z3", "CVC5", "CliffordAlgebras", "Grassmann", "Octonions", "Quaternions", "StaticArrays", "Manifolds", "CombinatorialSpaces", "DifferentialEquations", "ITensors", "ITensorMPS", "ITensorNetworks", "TensorOperations", "Symbolics", "Graphs", "PythonCall", "DLPack", "CUDA", "Reactant", "Enzyme", "Flux", "Lux", "GraphNeuralNetworks", "GraphNeuralNets"]
rows = Any[]
for m in mods
    ok = false; err = nothing
    try
        @eval using $(Symbol(m))
        ok = true
    catch e
        err = string(typeof(e), ": ", e)
    end
    push!(rows, Dict("module"=>m, "ok"=>ok, "error"=> ok ? nothing : first(err, min(lastindex(err), 220))))
end
open("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/evidence/sim_tool_library_coverage_julia_tmp.json", "w") do io
    JSON.print(io, Dict("julia"=>Sys.BINDIR*"/julia", "active_project"=>Base.active_project(), "modules"=>rows))
end
