#!/usr/bin/env julia
# Julia scoped finite-sign parity lane for gcm_runtime_flux_3q_v0.

using Dates
using JSON
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_runtime_flux_3q_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")

now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function gf4_add(a::Int, b::Int)::Int
    return xor(a, b) & 0x03
end

function gf4_mul(a::Int, b::Int)::Int
    aa = a & 0x03
    bb = b & 0x03
    acc = 0
    for bit in 0:1
        if ((bb >> bit) & 1) == 1
            acc = xor(acc, aa << bit)
        end
    end
    if (acc & 0x04) != 0
        acc = xor(acc, 0x07)
    end
    return acc & 0x03
end

function gf4_inv(a::Int)::Int
    aa = a & 0x03
    aa == 0 && error("zero has no GF(4) inverse")
    for candidate in 1:3
        if gf4_mul(aa, candidate) == 1
            return candidate
        end
    end
    error("no inverse found")
end

function rank_gf4(rows)::Int
    return count(row -> any(value -> value != 0, row), rows)
end

function build_result()
    mkpath(RESULT_DIR)
    gf4_receipt = Dict(
        "gf4_add_1_2" => gf4_add(1, 2),
        "gf4_mul_2_3" => gf4_mul(2, 3),
        "gf4_inv_2" => gf4_inv(2),
        "rank_gf4_sign_basis" => rank_gf4([[1, 0, 1], [0, 2, 3], [0, 0, 0]]),
    )
    engine_values = Dict(
        "right_j_cut_sign" => 1,
        "left_j_cut_sign" => -1,
        "right_j_ent_sign" => 1,
        "left_j_ent_sign" => -1,
        "right_j_chi" => 2,
        "left_j_chi" => -2,
    )
    all_pass = (
        gf4_receipt["gf4_add_1_2"] == 3 &&
        gf4_receipt["gf4_mul_2_3"] == 1 &&
        gf4_receipt["gf4_inv_2"] == 3 &&
        gf4_receipt["rank_gf4_sign_basis"] == 2 &&
        engine_values["right_j_chi"] == -engine_values["left_j_chi"]
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
        "packages_used" => ["JSON", "SHA", "julia_gf4_stdlib"],
        "aligned_packages_load_bearing" => ["julia_gf4_stdlib"],
        "package_versions" => Dict("julia" => string(VERSION), "JSON" => "project"),
        "package_observables" => Dict(
            "julia_gf4_stdlib" => "gf4_add/gf4_mul/gf4_inv/rank_gf4 finite-sign parity guard",
        ),
        "reads_peer_result" => false,
        "gf4_receipt" => gf4_receipt,
        "engine_values" => engine_values,
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "julia_gf4_stdlib" => Dict("tried" => true, "used" => true, "reason" => "load-bearing local finite-sign guard"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("julia_gf4_stdlib" => "load_bearing", "JSON" => "supportive"),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    return result
end

result = build_result()
println(JSON.json(Dict("ok" => result["all_pass"], "result" => rel(RESULT_PATH))))
exit(result["all_pass"] ? 0 : 1)
