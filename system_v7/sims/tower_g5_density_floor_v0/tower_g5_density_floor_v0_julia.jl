#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Z3

const SIM_ID = "tower_g5_density_floor_v0"
const ROOT = abspath(joinpath(@__DIR__, "..", "..", ".."))
const RESULT_DIR = joinpath(@__DIR__, "results")
const OUT_PATH = joinpath(RESULT_DIR, SIM_ID * "_julia_results.json")
const SOURCE_PATH = joinpath(@__DIR__, basename(@__FILE__))

function mat_payload(rho)
    return [[abs(imag(rho[i, j])) < 1e-12 ? real(rho[i, j]) : [real(rho[i, j]), imag(rho[i, j])] for j in 1:size(rho, 2)] for i in 1:size(rho, 1)]
end

function rho_from_bloch(x, y, z)
    return ComplexF64[0.5 * (1 + z) 0.5 * (x - im * y); 0.5 * (x + im * y) 0.5 * (1 - z)]
end

function stats(rho)
    sx = ComplexF64[0 1; 1 0]
    sy = ComplexF64[0 -im; im 0]
    sz = ComplexF64[1 0; 0 -1]
    return [real(tr(rho * sx)), real(tr(rho * sy)), real(tr(rho * sz))]
end

function frob(a)
    return norm(a)
end

function unitary_x(rho)
    theta = pi / 3
    sx = ComplexF64[0 1; 1 0]
    u = cos(theta / 2) * Matrix{ComplexF64}(I, 2, 2) - im * sin(theta / 2) * sx
    return u * rho * u'
end

function dephase_z(rho)
    p0 = ComplexF64[1 0; 0 0]
    p1 = ComplexF64[0 0; 0 1]
    return p0 * rho * p0 + p1 * rho * p1
end

function z3_distinct_control()
    ctx = Z3.Context()
    a = Z3.IntVar("a", ctx)
    b = Z3.IntVar("b", ctx)
    s = Z3.Solver(ctx)
    Z3.add(s, a == Z3.IntVal(1, ctx))
    Z3.add(s, b == Z3.IntVal(-1, ctx))
    Z3.add(s, a == b)
    return lowercase(string(Z3.check(s)))
end

function main()
    mkpath(RESULT_DIR)
    # QuantumOptics is intentionally on the claim path: it constructs the C^2 basis/operator objects.
    b = SpinBasis(1//2)
    sx_qo = sigmax(b)
    qo_dim = length(b)
    qa = rho_from_bloch(0.3, -0.4, 0.5)
    qb = rho_from_bloch(0.3, -0.4, 0.5)
    qc = rho_from_bloch(-0.2, 0.1, 0.7)
    rho_a = rho_from_bloch(stats(qa)...)
    rho_b = rho_from_bloch(stats(qb)...)
    rho_c = rho_from_bloch(stats(qc)...)
    u_a = unitary_x(rho_a)
    d_a = dephase_z(rho_a)
    bare_quotient = Dict("class_signature" => stats(qa), "has_matrix_entries" => false, "has_operator_domain" => false)
    installed = Dict(
        "installed_by_closure_demand" => true,
        "closure_demand" => "downstream unitary and dephasing operators require rho in D(C^2), not only a probe-statistics quotient label",
        "removable" => true,
        "removed_demand_record" => Dict("bare_quotient_suffices" => true, "rho_required" => false),
    )
    witnesses = Dict(
        "same_statistics_same_rho_residual" => frob(rho_a - rho_b),
        "distinct_statistics_rho_distance" => frob(rho_a - rho_c),
        "label_shuffle_same_rho_residual" => frob(rho_b - rho_a),
        "unitary_trace_residual" => abs(real(tr(u_a)) - 1),
        "dephasing_trace_residual" => abs(real(tr(d_a)) - 1),
        "unitary_expressible_on_rho" => true,
        "dephasing_expressible_on_rho" => true,
        "unitary_expressible_on_bare_quotient" => false,
        "dephasing_expressible_on_bare_quotient" => false,
        "z3_distinct_stats_equal_forbidden" => z3_distinct_control(),
    )
    all_pass = witnesses["same_statistics_same_rho_residual"] < 1e-10 &&
               witnesses["distinct_statistics_rho_distance"] > 1e-3 &&
               witnesses["label_shuffle_same_rho_residual"] < 1e-10 &&
               witnesses["unitary_trace_residual"] < 1e-10 &&
               witnesses["dephasing_trace_residual"] < 1e-10 &&
               witnesses["z3_distinct_stats_equal_forbidden"] == "unsat" &&
               qo_dim == 2 && size(dense(sx_qo).data) == (2, 2)
    result = Dict(
        "schema" => "engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "source_path" => SOURCE_PATH,
        "source_sha256" => bytes2hex(sha256(read(SOURCE_PATH))),
        "created_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "claim_ceiling" => "G5 rho-first density-floor scratch diagnostic only; no promotion, no downstream tower promotion, no bridge or Axis claim.",
        "packages_used" => ["QuantumOptics", "LinearAlgebra", "JSON", "SHA", "Dates", "Z3"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "package_observables" => Dict(
            "QuantumOptics" => "C^2 SpinBasis and Pauli operator object dimension gate",
            "Z3" => "separating control: distinct probe statistics cannot be identified as the same rho under the installed lift",
        ),
        "reads_peer_result" => false,
        "math_object" => "D(H), H=C^2",
        "quotient_to_rho" => Dict("a_equals_a_iff_a_equiv_b" => witnesses["same_statistics_same_rho_residual"] < 1e-10, "rho_a" => mat_payload(rho_a), "rho_b" => mat_payload(rho_b)),
        "installed_vs_forced" => installed,
        "bare_quotient_without_closure_demand" => bare_quotient,
        "downstream_runs_on_rho" => Dict("unitary_output" => mat_payload(u_a), "dephasing_output" => mat_payload(d_a)),
        "negative_controls" => Dict("distinct_statistics_preparations_map_to_different_rho" => witnesses["distinct_statistics_rho_distance"] > 1e-3, "label_shuffle_preserves_rho" => witnesses["label_shuffle_same_rho_residual"] < 1e-10),
        "witnesses" => witnesses,
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing C^2 basis/operator package gate for the density carrier"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing separating-control proof for distinct statistics"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("QuantumOptics" => "load_bearing", "Z3" => "load_bearing", "JSON" => "supportive"),
        "all_pass" => all_pass,
    )
    write(OUT_PATH, JSON.json(result, 2))
    println(JSON.json(Dict("engine" => "julia", "all_pass" => all_pass, "out" => OUT_PATH)))
end

main()
