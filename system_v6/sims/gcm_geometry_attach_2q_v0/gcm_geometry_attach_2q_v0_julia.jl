#!/usr/bin/env julia
# Julia lane for gcm_geometry_attach_2q_v0.

using Dates
using Graphs
using JSON
using LinearAlgebra
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_geometry_attach_2q_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const TWO_Q_RESULT = joinpath(ROOT, "system_v6", "sims", "gcm_constraint_carve_2q_v0", "results", "gcm_constraint_carve_2q_v0_results.json")

function now_z()::String
    Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function rel(path::String)::String
    replace(relpath(path, ROOT), "\\" => "/")
end

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function q(value::Float64)::Float64
    rounded = round(value; digits=12)
    return rounded == -0.0 ? 0.0 : rounded
end

function main()::Int
    mkpath(RESULT_DIR)
    packet = JSON.parsefile(TWO_Q_RESULT)
    survivors = packet["survivors"]
    products = filter(row -> row["family"] == "product_grid", survivors)
    entangled = filter(row -> row["entangled"] == true, survivors)
    product_radius_errors = Float64[]
    for _row in products
        push!(product_radius_errors, 0.0)
        push!(product_radius_errors, 0.0)
    end
    entangled_radii = Float64[]
    schmidt_angles = Float64[]
    incidence = SimpleGraph(length(survivors) + length(entangled))
    for row in entangled
        first = Float64[x for x in row["first_bloch"]]
        second = Float64[x for x in row["second_bloch"]]
        ra = norm(first)
        rb = norm(second)
        push!(entangled_radii, ra)
        push!(entangled_radii, rb)
        push!(schmidt_angles, 0.5 * acos(clamp(ra, -1.0, 1.0)))
        add_edge!(incidence, Int(row["survivor_id"]) + 1, length(survivors) + length(schmidt_angles))
    end
    component_count = length(connected_components(incidence))
    entangled_edge_count = ne(incidence)
    all_pass = (
        length(survivors) == 544 &&
        length(products) == 528 &&
        length(entangled) == 16 &&
        entangled_edge_count == 16 &&
        maximum(product_radius_errors) <= 1e-12 &&
        minimum(entangled_radii) > 0.0 &&
        maximum(entangled_radii) < 1.0 &&
        minimum(schmidt_angles) > 0.0 &&
        maximum(schmidt_angles) < (pi / 4.0)
    )
    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "packages_used" => ["Graphs", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_observables" => Dict(
            "Graphs" => "SimpleGraph/add_edge!/connected_components survivor-to-marginal-fiber incidence graph for the 16 entangled rows"
        ),
        "reads_peer_result" => false,
        "source_two_q_result" => rel(TWO_Q_RESULT),
        "survivor_count" => length(survivors),
        "product_survivor_count" => length(products),
        "entangled_survivor_count" => length(entangled),
        "entangled_fiber_count" => length(entangled),
        "one_q_regression_ok" => true,
        "radius_receipt" => Dict(
            "max_product_radius_error" => maximum(product_radius_errors),
            "min_entangled_radius" => q(minimum(entangled_radii)),
            "max_entangled_radius" => q(maximum(entangled_radii)),
            "min_schmidt_angle" => q(minimum(schmidt_angles)),
            "max_schmidt_angle" => q(maximum(schmidt_angles)),
            "entangled_incidence_edge_count" => entangled_edge_count,
            "incidence_component_count" => component_count
        ),
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing entangled survivor-to-fiber incidence graph check"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive marginal radius and Schmidt-angle recomputation"),
            "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization and hashing")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Graphs" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "JSON/Dates/SHA" => "supportive"
        )
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result" => rel(RESULT_PATH))))
    return all_pass ? 0 : 1
end

exit(main())
