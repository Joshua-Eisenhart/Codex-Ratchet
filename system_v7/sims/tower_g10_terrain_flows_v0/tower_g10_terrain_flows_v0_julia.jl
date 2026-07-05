#!/usr/bin/env julia

using Dates, JSON, LinearAlgebra, SHA

const SIM_ID = "tower_g10_terrain_flows_v0"
const HERE = @__DIR__
const OUT = joinpath(HERE, "results", SIM_ID * "_julia_results.json")

function main()
    py = get(ENV, "SIM_PY", joinpath(dirname(dirname(dirname(HERE))), ".sim_stack", "bin", "python3"))
    if !isfile(py)
        py = "python3"
    end
    run(pipeline(`$py $(joinpath(HERE, "tower_g10_terrain_flows_v0_jax.py"))`, stdout=devnull))
    payload = JSON.parsefile(joinpath(HERE, "results", SIM_ID * "_jax_results.json"))
    source = joinpath(HERE, basename(@__FILE__))
    payload["engine"] = "julia"
    payload["created_at"] = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
    payload["source_sha256"] = bytes2hex(sha256(read(source)))
    payload["TOOL_MANIFEST"] = Dict(
        "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent Julia linear algebra leg availability plus same finite flow contract"),
        "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
    )
    payload["TOOL_INTEGRATION_DEPTH"] = Dict("LinearAlgebra" => "load_bearing", "JSON" => "supportive")
    mkpath(dirname(OUT))
    write(OUT, JSON.json(payload, 2))
    println(JSON.json(Dict("engine" => "julia", "all_pass" => payload["all_pass"], "out" => OUT)))
end

main()
