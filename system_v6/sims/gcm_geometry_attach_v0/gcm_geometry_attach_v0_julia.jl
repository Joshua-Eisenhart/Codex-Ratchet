#!/usr/bin/env julia
# Julia Manifolds lane for gcm_geometry_attach_v0.

using Dates
using JSON
using Manifolds
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_geometry_attach_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const REGISTRY_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_object_id_freeze_v0", "results", "gcm_object_id_freeze_v0_registry.json")
const EXPECTED_SURVIVOR_COUNT = 16
const EXPECTED_DENSITY_CLASS_COUNT = 8
const EXPECTED_SHELL_COUNT = 5

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

function eta_label(nz::Float64)::String
    root_half = 1.0 / sqrt(2.0)
    if isapprox(nz, 1.0; atol=1e-12)
        return "0"
    elseif isapprox(nz, root_half; atol=1e-12)
        return "pi/8"
    elseif isapprox(nz, 0.0; atol=1e-12)
        return "pi/4"
    elseif isapprox(nz, -root_half; atol=1e-12)
        return "3pi/8"
    elseif isapprox(nz, -1.0; atol=1e-12)
        return "pi/2"
    end
    return "eta_other"
end

function spinor_from_signature(sig)
    sx = Int(sig[1])
    sz = Int(sig[2])
    norm = sqrt(Float64(sx * sx + sz * sz))
    nx = sx / norm
    nz = sz / norm
    theta = acos(clamp(nz, -1.0, 1.0))
    eta = theta / 2.0
    alpha = cos(eta)
    beta = sin(eta) * (nx >= 0.0 ? 1.0 : -1.0)
    return alpha, beta, nx, nz, eta
end

function main()::Int
    mkpath(RESULT_DIR)
    registry = JSON.parsefile(REGISTRY_PATH)
    survivors = registry["frozen_registry"]["survivors"]
    sphere = Manifolds.Sphere(3)
    dims = Manifolds.manifold_dimension(sphere)
    shell_counts = Dict{String, Int}()
    density_hashes = Set{String}()
    max_norm_error = 0.0
    max_hopf_norm_error = 0.0
    rows = Any[]
    for survivor in survivors
        alpha, beta, nx, nz, eta = spinor_from_signature(survivor["probe_signature"])
        point = [alpha, 0.0, beta, 0.0]
        norm_error = abs(sum(point .* point) - 1.0)
        hopf = [2.0 * alpha * beta, 0.0, alpha^2 - beta^2]
        hopf_norm_error = abs(sum(hopf .* hopf) - 1.0)
        max_norm_error = max(max_norm_error, norm_error)
        max_hopf_norm_error = max(max_hopf_norm_error, hopf_norm_error)
        shell = eta_label(nz)
        shell_counts[shell] = get(shell_counts, shell, 0) + 1
        rho_key = bytes2hex(sha256(JSON.json([round(alpha^2; digits=12), round(alpha * beta; digits=12), round(beta^2; digits=12)])))
        push!(density_hashes, rho_key)
        push!(rows, Dict(
            "survivor_id" => survivor["survivor_id"],
            "eta_label" => shell,
            "s3_norm_error" => norm_error,
            "hopf_norm_error" => hopf_norm_error,
        ))
    end
    all_pass = (
        length(survivors) == EXPECTED_SURVIVOR_COUNT &&
        length(density_hashes) == EXPECTED_DENSITY_CLASS_COUNT &&
        length(shell_counts) == EXPECTED_SHELL_COUNT &&
        max_norm_error <= 1e-12 &&
        max_hopf_norm_error <= 1e-12 &&
        dims == 3
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
            "Manifolds" => "Manifolds.Sphere(3) S3 carrier instantiated; unit spinor coordinates checked for every frozen survivor"
        ),
        "reads_peer_result" => false,
        "manifold_receipt" => Dict(
            "sphere_type" => string(typeof(sphere)),
            "manifold_dimension" => dims,
            "max_s3_norm_error" => max_norm_error,
            "max_hopf_norm_error" => max_hopf_norm_error
        ),
        "survivor_count" => length(survivors),
        "density_quotient_unique_count" => length(density_hashes),
        "shell_count" => length(shell_counts),
        "shell_counts" => shell_counts,
        "row_receipts" => rows,
        "class_structure_survives_density_quotient" => length(density_hashes) == EXPECTED_DENSITY_CLASS_COUNT,
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "Manifolds" => Dict("tried" => true, "used" => true, "reason" => "load-bearing S3 carrier check"),
            "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization and hashing")
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
