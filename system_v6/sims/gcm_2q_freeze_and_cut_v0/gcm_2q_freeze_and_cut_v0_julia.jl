#!/usr/bin/env julia
# Julia QuantumOptics lane for gcm_2q_freeze_and_cut_v0.

using Dates
using JSON
using LinearAlgebra
using Pkg
using QuantumOptics
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_2q_freeze_and_cut_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const PACKET_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_results.json")
const TWO_Q_CARVE_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_constraint_carve_2q_v0", "results", "gcm_constraint_carve_2q_v0_results.json")
const TOL = 1.0e-10
const EXPECTED_TWO_Q_SURVIVOR_COUNT = 544
const EXPECTED_TWO_Q_CLASS_COUNT = 8
const EXPECTED_PRODUCT_SURVIVOR_COUNT = 528
const EXPECTED_ENTANGLED_SURVIVOR_COUNT = 16
const EXPECTED_ONE_Q_SURVIVOR_COUNT = 16

now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function write_json(path::String, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
end

function pkg_version(name::String)::String
    for (_uuid, dep) in Pkg.dependencies()
        if dep.name == name && dep.version !== nothing
            return string(dep.version)
        end
    end
    return "unknown"
end

q(value)::Float64 = abs(round(Float64(real(value)); digits=15)) <= 1.0e-12 ? 0.0 : round(Float64(real(value)); digits=15)

function bloch_radius(coord)::Float64
    return sqrt(sum(Float64(v)^2 for v in coord))
end

function one_q_density(coord)
    x, y, z = [Float64(v) for v in coord]
    return ComplexF64[
        (1 + z) / 2       (x - im * y) / 2
        (x + im * y) / 2  (1 - z) / 2
    ]
end

function eigenvectors_for_bloch(coord)
    x, y, z = [Float64(v) for v in coord]
    radius = sqrt(x*x + y*y + z*z)
    if radius <= 1.0e-12
        return ComplexF64[1, 0], ComplexF64[0, 1]
    end
    theta = acos(clamp(z / radius, -1.0, 1.0))
    phi = atan(y, x)
    phase = cis(phi)
    c = cos(theta / 2)
    s = sin(theta / 2)
    up = ComplexF64[c, phase * s]
    down = ComplexF64[-conj(phase) * s, c]
    return up, down
end

function purification_density(first)
    radius = bloch_radius(first)
    lambda_plus = (1 + radius) / 2
    lambda_minus = (1 - radius) / 2
    up, down = eigenvectors_for_bloch(first)
    psi = zeros(ComplexF64, 4)
    for a in 1:2
        psi[(a - 1) * 2 + 1] += sqrt(lambda_plus) * up[a]
        psi[(a - 1) * 2 + 2] += sqrt(lambda_minus) * down[a]
    end
    return psi * psi'
end

function rho_for_survivor(row)
    first = [Float64(v) for v in row["first_bloch"]]
    second = [Float64(v) for v in row["second_bloch"]]
    if row["family"] == "product_grid"
        return kron(one_q_density(first), one_q_density(second))
    elseif row["family"] == "purification_boundary"
        return purification_density(first)
    end
    error("unknown family $(row["family"])")
end

function partial_transpose_b(rho)
    out = zeros(ComplexF64, 4, 4)
    for a in 1:2, b in 1:2, c in 1:2, d in 1:2
        out[(a - 1) * 2 + d, (c - 1) * 2 + b] = rho[(a - 1) * 2 + b, (c - 1) * 2 + d]
    end
    return out
end

function negativity(rho)::Float64
    vals = eigvals(Hermitian(partial_transpose_b(rho)))
    return q(sum((-real(v) for v in vals if real(v) < -1.0e-12); init=0.0))
end

function metrics_for_row(row, basis_2, basis_ab)
    rho = rho_for_survivor(row)
    op = Operator(basis_ab, rho)
    rho_a = ptrace(op, 1)
    rho_b = ptrace(op, 2)
    s_a = q(entropy_vn(rho_a))
    s_b = q(entropy_vn(rho_b))
    s_ab = q(entropy_vn(op))
    neg = negativity(rho)
    return [
        s_a,
        s_b,
        s_ab,
        q(s_ab - s_b),
        q(s_a + s_b - s_ab),
        q(s_b - s_ab),
        neg,
    ]
end

function build_result()
    carve = JSON.parsefile(TWO_Q_CARVE_PATH)
    packet = JSON.parsefile(PACKET_PATH)
    expected_by_raw = Dict(row["raw_2q_survivor_id"] => row for row in packet["entropy_tables"]["survivor_cut_entropy_rows"])
    basis_2 = NLevelBasis(2)
    basis_ab = tensor(basis_2, basis_2)
    max_delta = 0.0
    product_neg = Float64[]
    ent_neg = Float64[]
    ent_cond = Float64[]
    for row in carve["survivors"]
        metrics = metrics_for_row(row, basis_2, basis_ab)
        expected = expected_by_raw[row["survivor_id"]]["entropy_values"]
        packet_metrics = [
            expected["S_rho_A"],
            expected["S_rho_B"],
            expected["S_rho_AB"],
            expected["conditional_S_A_given_B"],
            expected["mutual_I_A_B"],
            expected["coherent_I_c_A_to_B"],
            expected["negativity"],
        ]
        for idx in 1:length(metrics)
            max_delta = max(max_delta, abs(metrics[idx] - Float64(packet_metrics[idx])))
        end
        if row["family"] == "product_grid"
            push!(product_neg, metrics[7])
        end
        if row["entangled"] == true
            push!(ent_neg, metrics[7])
            push!(ent_cond, metrics[4])
        end
    end
    exact_counts = Dict(
        "two_q" => length(carve["survivors"]),
        "classes" => carve["quotient"]["class_count"],
        "product" => count(row -> row["family"] == "product_grid", carve["survivors"]),
        "entangled" => count(row -> row["entangled"] == true, carve["survivors"]),
        "embedded" => packet["counts"]["one_q_product_embedding_count"],
    )
    all_pass = (
        packet["all_pass"] == true &&
        exact_counts["two_q"] == EXPECTED_TWO_Q_SURVIVOR_COUNT &&
        exact_counts["classes"] == EXPECTED_TWO_Q_CLASS_COUNT &&
        exact_counts["product"] == EXPECTED_PRODUCT_SURVIVOR_COUNT &&
        exact_counts["entangled"] == EXPECTED_ENTANGLED_SURVIVOR_COUNT &&
        exact_counts["embedded"] == EXPECTED_ONE_Q_SURVIVOR_COUNT &&
        max_delta <= TOL &&
        maximum(product_neg) <= TOL &&
        minimum(ent_neg) > TOL &&
        maximum(ent_cond) < -TOL
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
        "packages_used" => ["QuantumOptics", "LinearAlgebra", "JSON"],
        "aligned_packages_load_bearing" => ["QuantumOptics"],
        "package_versions" => Dict("QuantumOptics" => pkg_version("QuantumOptics")),
        "package_observables" => Dict(
            "QuantumOptics" => "NLevelBasis/tensor/Operator/ptrace/entropy_vn recompute A|B reductions and entropy values",
        ),
        "reads_peer_result" => false,
        "quantumoptics_receipt" => Dict(
            "basis_dims" => string(basis_ab),
            "max_abs_delta_vs_packet" => q(max_delta),
            "max_product_negativity" => q(maximum(product_neg)),
            "min_entangled_negativity" => q(minimum(ent_neg)),
            "max_entangled_conditional" => q(maximum(ent_cond)),
            "all_product_negativity_zero" => maximum(product_neg) <= TOL,
            "all_entangled_negativity_positive" => minimum(ent_neg) > TOL,
            "all_entangled_conditional_negative" => maximum(ent_cond) < -TOL,
        ),
        "survivor_count" => exact_counts["two_q"],
        "quotient_class_count" => exact_counts["classes"],
        "candidate_region_count" => packet["counts"]["candidate_region_count"],
        "product_survivor_count" => exact_counts["product"],
        "entangled_survivor_count" => exact_counts["entangled"],
        "embedded_1q_count" => exact_counts["embedded"],
        "metric_summary" => Dict(
            "max_product_negativity" => q(maximum(product_neg)),
            "min_entangled_negativity" => q(minimum(ent_neg)),
            "max_entangled_conditional" => q(maximum(ent_cond)),
        ),
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing partial trace and entropy recomputation"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive eigensolver for partial transpose"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result parsing/writing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "QuantumOptics" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "JSON" => "supportive",
        ),
    )
    write_json(RESULT_PATH, result)
    return result
end

function main()
    result = build_result()
    println(JSON.json(Dict("ok" => result["all_pass"], "result" => rel(RESULT_PATH))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
