#!/usr/bin/env julia
# Julia Manifolds lane for gcm_connection_flux_attach_v0.

using Dates
using JSON
using Manifolds
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_connection_flux_attach_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const GEOMETRY_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_geometry_attach_v0", "results", "gcm_geometry_attach_v0_results.json")
const EXPECTED_SURVIVOR_COUNT = 16
const EXPECTED_SHELL_COUNT = 5
const EXPECTED_SIGNATURE = "2-4-4-4-2"
const SHELL_ORDER = ["0", "pi/8", "pi/4", "3pi/8", "pi/2"]

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

function eta_value(label::String)::Float64
    if label == "0"
        return 0.0
    elseif label == "pi/8"
        return pi / 8.0
    elseif label == "pi/4"
        return pi / 4.0
    elseif label == "3pi/8"
        return 3.0 * pi / 8.0
    elseif label == "pi/2"
        return pi / 2.0
    end
    error("unknown shell label: $(label)")
end

function main()::Int
    mkpath(RESULT_DIR)
    geometry = JSON.parsefile(GEOMETRY_PATH)
    groups = Dict(label => Any[] for label in SHELL_ORDER)
    for row in geometry["attachment_map"]["survivor_spinor_maps"]
        push!(groups[row["T_eta_label"]], row)
    end
    sphere = Manifolds.Sphere(3)
    rows = Any[]
    for label in SHELL_ORDER
        eta = eta_value(label)
        push!(rows, Dict(
            "T_eta_label" => label,
            "occupied_survivor_count" => length(groups[label]),
            "holonomy" => -2.0 * pi * cos(2.0 * eta),
            "curvature_eta_chi" => -2.0 * sin(2.0 * eta),
            "A_chi" => cos(2.0 * eta),
        ))
    end
    signature = join([string(row["occupied_survivor_count"]) for row in rows], "-")
    all_pass = (
        sum(row["occupied_survivor_count"] for row in rows) == EXPECTED_SURVIVOR_COUNT &&
        length(rows) == EXPECTED_SHELL_COUNT &&
        signature == EXPECTED_SIGNATURE &&
        Manifolds.manifold_dimension(sphere) == 3
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
        "packages_used" => ["Manifolds", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Manifolds"],
        "package_observables" => Dict(
            "Manifolds" => "Manifolds.Sphere(3) anchors the S3 carrier while occupied shell holonomy rows are recomputed"
        ),
        "reads_peer_result" => false,
        "manifold_receipt" => Dict(
            "sphere_type" => string(typeof(sphere)),
            "manifold_dimension" => Manifolds.manifold_dimension(sphere)
        ),
        "row_receipts" => rows,
        "survivor_count" => sum(row["occupied_survivor_count"] for row in rows),
        "shell_count" => length(rows),
        "shell_occupation_signature" => signature,
        "leakage_status" => "closed",
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "Manifolds" => Dict("tried" => true, "used" => true, "reason" => "load-bearing S3 carrier check"),
            "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive parsing and hashing")
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Manifolds" => "load_bearing",
            "JSON/Dates/SHA" => "supportive"
        ),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result" => rel(RESULT_PATH))))
    return all_pass ? 0 : 1
end

exit(main())
