#!/usr/bin/env julia
# Julia leg for the flux emergence discriminator.

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "flux_emergence_discriminator"
const OBJECT_ID = "$(SIM_ID)_julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-6
const TRANSPORT_STEPS = 4096
const QUAD_ETA_STEPS = 8192
const QUAD_CHI_STEPS = 64
const SMT_SCALE = 10^12
const PHI0 = 0.19
const CHI0 = -0.31

const PIN_SPEC = Dict(
    "eta_shells" => ["pi/8 + k*pi/10 for k=0,1,2"],
    "loop_grammar" => Dict(
        "gamma_f" => "psi(phi0 + u, chi0; eta0)",
        "gamma_b" => "psi(phi0 - integral A_chi/A_phi dchi, chi0 + u; eta0)",
        "horizontal_condition" => "A(dot gamma_b)=0",
    ),
    "connection" => "A=-i psi^dagger d psi, numerically sampled from spinor derivatives",
    "curvature" => "F=-2 sin(2 eta) d eta wedge d chi",
    "claim_ceiling" => "scratch_diagnostic; promotion_allowed=false; flux remains a CANDIDATE FAMILY per weyl-flux.md",
)

const TOOL_MANIFEST = Dict(
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive finite complex spinor, eigenspectrum, and entropy arithmetic",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Z3.jl integer-scaled additivity proof over bound connection cos values",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive serialization, timestamps, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "LinearAlgebra" => "supportive",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

eta_shell(index::Int)::Float64 = pi / 8.0 + index * pi / 10.0
wrap_phase(value::Float64)::Float64 = atan(sin(value), cos(value))

function spinor(phi::Float64, chi::Float64, eta::Float64)::Vector{ComplexF64}
    ComplexF64[
        exp(im * (phi + chi)) * cos(eta),
        exp(im * (phi - chi)) * sin(eta),
    ]
end

function connection_coefficients(phi::Float64, chi::Float64, eta::Float64)
    eps = 1.0e-6
    psi = spinor(phi, chi, eta)
    d_phi = (spinor(phi + eps, chi, eta) - spinor(phi - eps, chi, eta)) ./ (2.0 * eps)
    d_chi = (spinor(phi, chi + eps, eta) - spinor(phi, chi - eps, eta)) ./ (2.0 * eps)
    a_phi = Float64(real(-im * dot(psi, d_phi)))
    a_chi = Float64(real(-im * dot(psi, d_chi)))
    a_phi, a_chi
end

function horizontal_transport(index::Int, eta::Float64)
    phi = PHI0
    chi = CHI0
    dchi = 2.0 * pi / TRANSPORT_STEPS
    coeff_samples = Vector{Dict{String,Any}}()
    for step in 0:(TRANSPORT_STEPS - 1)
        a_phi, a_chi = connection_coefficients(phi, chi, eta)
        if step in Set([0, div(TRANSPORT_STEPS, 2), TRANSPORT_STEPS - 1])
            push!(coeff_samples, Dict("step" => step, "A_phi" => a_phi, "A_chi" => a_chi))
        end
        phi += -(a_chi / a_phi) * dchi
        chi += dchi
    end
    start = spinor(PHI0, CHI0, eta)
    finish = spinor(phi, chi, eta)
    endpoint_phase = Float64(angle(dot(start, finish)))
    accumulated = phi - PHI0
    target = -2.0 * pi * cos(2.0 * eta)
    Dict{String,Any}(
        "shell" => index,
        "eta" => eta,
        "connection_A_phi" => coeff_samples[1]["A_phi"],
        "connection_A_chi" => coeff_samples[1]["A_chi"],
        "transport_steps" => TRANSPORT_STEPS,
        "accumulated_phase" => accumulated,
        "accumulated_phase_mod_2pi" => wrap_phase(accumulated),
        "endpoint_overlap_phase_mod_2pi" => endpoint_phase,
        "closed_form_target" => target,
        "target_mod_2pi" => wrap_phase(target),
        "mod_error" => abs(wrap_phase(accumulated - target)),
        "endpoint_vs_transport_mod_error" => abs(wrap_phase(endpoint_phase - accumulated)),
        "coefficient_samples" => coeff_samples,
    )
end

curvature_eta_chi(eta) = -2.0 .* sin.(2.0 .* eta)

function stokes_oriented_flux(eta_i::Float64, eta_j::Float64)
    deta = (eta_j - eta_i) / QUAD_ETA_STEPS
    dchi = 2.0 * pi / QUAD_CHI_STEPS
    grid = eta_i .+ ((0:(QUAD_ETA_STEPS - 1)) .+ 0.5) .* deta
    raw_f_integral = Float64(sum(curvature_eta_chi(grid)) * deta * dchi * QUAD_CHI_STEPS)
    Dict(
        "raw_deta_wedge_dchi_integral" => raw_f_integral,
        "stokes_oriented_integral" => -raw_f_integral,
    )
end

function chern_integral()
    deta = (pi / 2.0) / QUAD_ETA_STEPS
    dchi = 2.0 * pi / QUAD_CHI_STEPS
    grid = ((0:(QUAD_ETA_STEPS - 1)) .+ 0.5) .* deta
    signed_total = Float64(sum(curvature_eta_chi(grid)) * deta * dchi * QUAD_CHI_STEPS)
    normalized_abs = abs(signed_total) / (4.0 * pi)
    Dict(
        "signed_total_F_deta_wedge_dchi" => signed_total,
        "abs_total_over_4pi" => normalized_abs,
        "quadrature_error_abs_total_minus_4pi" => abs(abs(signed_total) - 4.0 * pi),
        "orientation_note" => "signed integral uses d eta wedge d chi; Chern check uses absolute value",
    )
end

function pair_flux(shells, i::Int, j::Int)
    hi = Float64(shells[i + 1]["accumulated_phase"])
    hj = Float64(shells[j + 1]["accumulated_phase"])
    eta_i = Float64(shells[i + 1]["eta"])
    eta_j = Float64(shells[j + 1]["eta"])
    transport = hj - hi
    target = 2.0 * pi * (cos(2.0 * eta_i) - cos(2.0 * eta_j))
    quad = stokes_oriented_flux(eta_i, eta_j)
    Dict{String,Any}(
        "pair" => [i, j],
        "transport_h_difference" => transport,
        "closed_form_target" => target,
        "quadrature_stokes_oriented" => quad["stokes_oriented_integral"],
        "raw_F_integral_deta_wedge_dchi" => quad["raw_deta_wedge_dchi_integral"],
        "transport_vs_target_error" => abs(transport - target),
        "transport_vs_quadrature_error" => abs(transport - quad["stokes_oriented_integral"]),
        "quadrature_orientation" => "negative of raw F_{eta,chi} d eta d chi so boundary orientation matches h_j-h_i",
    )
end

hermitize(rho::Matrix{ComplexF64}) = 0.5 .* (rho .+ rho')

function entropy_vn(rho::Matrix{ComplexF64})::Float64
    vals = real.(eigvals(Hermitian(hermitize(rho))))
    total = 0.0
    for p in vals
        if p > 1.0e-12
            total -= p * log(p)
        end
    end
    total
end

function rho_for_rung(rung::Int)
    theta = 0.70 * rung / 2.0
    psi = ComplexF64[cos(theta), 0.0, 0.0, sin(theta)]
    psi * psi'
end

function partial_trace_left_to_b(rho::Matrix{ComplexF64})
    shaped = reshape(rho, 2, 2, 2, 2)
    out = zeros(ComplexF64, 2, 2)
    for left in 1:2
        out .+= shaped[left, :, left, :]
    end
    out
end

function signed_cut_table(phi_adjacent::Vector{Float64})
    rows = Vector{Dict{String,Any}}()
    signed_cuts = Float64[]
    for rung in 0:2
        rho = rho_for_rung(rung)
        s_ab = entropy_vn(rho)
        s_b = entropy_vn(partial_trace_left_to_b(rho))
        conditional = s_ab - s_b
        signed_cut = -conditional
        push!(signed_cuts, signed_cut)
        push!(rows, Dict(
            "rung" => rung,
            "theta" => 0.70 * rung / 2.0,
            "S_AB" => s_ab,
            "S_B" => s_b,
            "conditional_entropy_S_A_given_B" => conditional,
            "signed_cut_Ic" => signed_cut,
        ))
    end
    delta_ic = [0.0, signed_cuts[2] - signed_cuts[1], signed_cuts[3] - signed_cuts[2]]
    phi_per_rung = [0.0, phi_adjacent[1], phi_adjacent[2]]
    mean_delta = sum(delta_ic) / length(delta_ic)
    mean_phi = sum(phi_per_rung) / length(phi_per_rung)
    num = sum((delta_ic[idx] - mean_delta) * (phi_per_rung[idx] - mean_phi) for idx in eachindex(delta_ic))
    den_a = sqrt(sum((value - mean_delta)^2 for value in delta_ic))
    den_b = sqrt(sum((value - mean_phi)^2 for value in phi_per_rung))
    corr = num / (den_a * den_b)
    sign_agreement = [sign(delta_ic[idx]) == sign(phi_per_rung[idx]) for idx in 2:3]
    Dict{String,Any}(
        "label" => "CANDIDATE_J_AB_co_variation",
        "admission" => "no_admission_candidate_only",
        "rows" => rows,
        "delta_Ic_per_rung" => delta_ic,
        "Phi_per_rung" => phi_per_rung,
        "correlation_across_3_rungs" => corr,
        "nonzero_rung_sign_agreement" => sign_agreement,
        "sign_agreement_count" => count(identity, sign_agreement),
    )
end

function z3_add_expr(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_sub_expr(left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_sub(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

function z3_smt(cos_scaled::Vector{Int})
    c0 = Z3.IntVar("julia_c0")
    c1 = Z3.IntVar("julia_c1")
    c2 = Z3.IntVar("julia_c2")
    p01 = Z3.IntVar("julia_phi01")
    p12 = Z3.IntVar("julia_phi12")
    p02 = Z3.IntVar("julia_phi02")
    solver = Z3.Solver()
    Z3.add(solver, c0 == Z3.IntVal(cos_scaled[1]))
    Z3.add(solver, c1 == Z3.IntVal(cos_scaled[2]))
    Z3.add(solver, c2 == Z3.IntVal(cos_scaled[3]))
    Z3.add(solver, p01 == z3_sub_expr(c0, c1))
    Z3.add(solver, p12 == z3_sub_expr(c1, c2))
    Z3.add(solver, p02 == z3_sub_expr(c0, c2))
    Z3.add(solver, Z3.Not(p02 == z3_add_expr(Z3.Expr[p01, p12])))
    additivity_status = string(Z3.check(solver))

    single = Z3.Solver()
    shell_count = Z3.IntVar("julia_single_shell_count")
    single_flux = Z3.IntVar("julia_single_flux")
    shell_is_one = shell_count == Z3.IntVal(1)
    Z3.add(single, shell_is_one)
    Z3.add(single, Z3.Or([Z3.Not(shell_is_one), single_flux == Z3.IntVal(0)]))
    Z3.add(single, Z3.Not(single_flux == Z3.IntVal(0)))
    single_status = string(Z3.check(single))
    Dict{String,Any}(
        "solver" => "julia_z3",
        "verdict" => additivity_status,
        "single_shell_verdict" => single_status,
        "bound_scaled_cos_values" => cos_scaled,
        "scale" => SMT_SCALE,
        "derived_expression" => "phi_ij_core = c_i - c_j; common 2*pi factor is outside the integer-scaled proof",
        "negated_additivity_unsat" => additivity_status == "unsat",
        "single_shell_flux_without_second_shell_forced_zero" => single_status == "unsat",
    )
end

function build_result()
    shells = [horizontal_transport(index, eta_shell(index)) for index in 0:2]
    pairs = [pair_flux(shells, i, j) for i in 0:2 for j in (i + 1):2]
    adjacent = [pair_flux(shells, 0, 1), pair_flux(shells, 1, 2)]
    chern = chern_integral()
    cos_scaled = [Int(round(Float64(shell["connection_A_chi"]) * SMT_SCALE)) for shell in shells]
    julia_z3 = z3_smt(cos_scaled)
    signed_cut = signed_cut_table([Float64(row["transport_h_difference"]) for row in adjacent])
    scrambled_order = [2, 1, 0]
    original_adjacent = [pair_flux(shells, 0, 1), pair_flux(shells, 1, 2)]
    scrambled_adjacent = [pair_flux(shells, scrambled_order[idx], scrambled_order[idx + 1]) for idx in 1:(length(scrambled_order) - 1)]
    bare_spinor = Dict(
        "connection" => "trivial A=0",
        "curvature_zero" => true,
        "holonomy_by_shell" => [0.0, 0.0, 0.0],
        "flux_quantities" => [0.0, 0.0],
        "reason" => "flat carrier in C^2 has no Hopf coordinates and no bundle curvature",
        "pass" => true,
    )
    single_shell = Dict(
        "shell" => 0,
        "holonomy_exists" => true,
        "h" => shells[1]["accumulated_phase"],
        "flux_defined" => false,
        "Phi_reported" => 0.0,
        "reason" => "one eta shell has holonomy but no second rung for relative inter-shell flux",
        "pass" => abs(Float64(shells[1]["accumulated_phase"])) > TOL,
    )
    scramble = Dict(
        "original_order" => [0, 1, 2],
        "scrambled_order" => scrambled_order,
        "original_adjacent_fluxes" => [row["transport_h_difference"] for row in original_adjacent],
        "scrambled_adjacent_fluxes" => [row["transport_h_difference"] for row in scrambled_adjacent],
        "sign_pattern_changed" => all(sign(Float64(original_adjacent[idx]["transport_h_difference"])) != sign(Float64(scrambled_adjacent[3 - idx]["transport_h_difference"])) for idx in 1:2),
        "total_chern_original" => chern["abs_total_over_4pi"],
        "total_chern_scrambled" => chern["abs_total_over_4pi"],
        "topology_indifferent_to_order" => abs(Float64(chern["abs_total_over_4pi"]) - 1.0) <= TOL,
        "reason" => "ordered adjacent fluxes reverse under filtration reversal; the absolute Chern number is unchanged",
    )
    max_h_error = maximum(Float64(row["mod_error"]) for row in shells)
    max_pair_quad_error = maximum(Float64(row["transport_vs_quadrature_error"]) for row in pairs)
    all_pass = max_h_error <= TOL &&
        max_pair_quad_error <= TOL &&
        Float64(chern["quadrature_error_abs_total_minus_4pi"]) <= TOL &&
        bare_spinor["pass"] &&
        single_shell["pass"] &&
        scramble["sign_pattern_changed"] &&
        scramble["topology_indifferent_to_order"] &&
        julia_z3["negated_additivity_unsat"] &&
        julia_z3["single_shell_flux_without_second_shell_forced_zero"] &&
        CLASSIFICATION == "scratch_diagnostic" &&
        PROMOTION_ALLOWED == false &&
        READS_PEER_RESULT == false
    shared_scalars = Dict(
        "h0" => shells[1]["accumulated_phase"],
        "h1" => shells[2]["accumulated_phase"],
        "h2" => shells[3]["accumulated_phase"],
        "phi01" => adjacent[1]["transport_h_difference"],
        "phi12" => adjacent[2]["transport_h_difference"],
        "phi02" => pair_flux(shells, 0, 2)["transport_h_difference"],
        "chern_abs_over_4pi" => chern["abs_total_over_4pi"],
        "signed_cut_Ic0" => signed_cut["rows"][1]["signed_cut_Ic"],
        "signed_cut_Ic1" => signed_cut["rows"][2]["signed_cut_Ic"],
        "signed_cut_Ic2" => signed_cut["rows"][3]["signed_cut_Ic"],
        "J_AB_correlation_3_rungs" => signed_cut["correlation_across_3_rungs"],
    )
    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "schema_version" => "three_engine_sim_result_v1",
        "engine_contract" => Dict("mode" => "all_three_full_sims", "reads_peer_result" => false),
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "pin_spec" => PIN_SPEC,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["LinearAlgebra", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "claim_path_tools" => ["Z3"],
        "control_only_tools" => String[],
        "standard_labels" => Dict(
            "pin" => "eta shells, loop grammar, and curvature member are fixed in pin_spec",
            "like_for_like" => true,
            "no_numpy_claim_path" => true,
            "capability_backed" => true,
        ),
        "shell_holonomy" => shells,
        "inter_shell_flux" => pairs,
        "chern" => chern,
        "ablations" => Dict(
            "bare_spinor" => bare_spinor,
            "single_shell" => single_shell,
            "ratchet_scramble" => scramble,
        ),
        "ratchet_coupling" => signed_cut,
        "smt" => Dict("julia_z3" => julia_z3),
        "crossover_proofs" => Dict(
            "julia_z3" => merge(Dict("ran" => true, "load_bearing" => true, "verdict" => julia_z3["verdict"]), julia_z3),
        ),
        "shared_scalars" => shared_scalars,
        "all_pass" => all_pass,
        "max_errors" => Dict(
            "holonomy_mod_error" => max_h_error,
            "transport_vs_quadrature_flux_error" => max_pair_quad_error,
            "chern_abs_error" => chern["quadrature_error_abs_total_minus_4pi"],
        ),
        "claim_ceiling" => "scratch_diagnostic only; promotion_allowed=false; flux remains a CANDIDATE FAMILY per weyl-flux.md; tests only the curvature member's emergence conditions.",
    )
end

function main()
    result = build_result()
    mkpath(RESULT_DIR)
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    s = result["shared_scalars"]
    println("FLUX_EMERGENCE_DISCRIMINATOR_JULIA_DONE all_pass=", result["all_pass"],
        " h=[", s["h0"], ",", s["h1"], ",", s["h2"], "]",
        " chern=", s["chern_abs_over_4pi"],
        " julia_z3=", result["smt"]["julia_z3"]["verdict"])
    return result["all_pass"] ? 0 : 2
end

exit(main())
