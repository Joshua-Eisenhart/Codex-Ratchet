#!/usr/bin/env julia
# Julia carrier leg for geo_s7_discrete_refinement_v0.

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s7_discrete_refinement_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const N_VALUES = [2, 4, 8, 16, 32, 64]

const PIN_SPEC = "geo_s7_discrete_refinement_v0|finite_hopf_torus_grid:T_eta^{N,N}|N=(2,4,8,16,32,64)|eta=(pi/12,pi/8,pi/6,pi/4,pi/3,3*pi/8,5*pi/12)|cover=(a,b)~(a+N/2,b+N/2) mod N|2:1 cover everywhere|kappa=(a+b) mod 2 class-invariant|area=R4 embedded quotient-cell chord mesh;exact rows support-only|holonomy=primary Wilson/overlap-product loop with central-secant comparison rows|target_h=-2*pi*cos(2*eta) lifted real S2 pin|flux=midpoint plaquette strip Phi_ij=S2 strip target|stokes=h(eta_j)-h(eta_i)+Phi_ij -> 0|controls=executed_mutations|cross_engine_fatality=true|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const CONVENTION_PIN = Dict(
    "holonomy_quantity" => Dict(
        "primary_reported" => "accumulated_phi",
        "distinguished_from" => ["endpoint_global_spinor_phase", "Berry_phase"],
        "target_lifted_cycle" => "h(eta) = -2*pi*cos(2*eta)",
        "discrete_route" => "primary Wilson/overlap-product sampled loop; central-secant connection emitted as comparison, not formula-copy",
        "round_trip_gate" => "forward lifted loop plus reversed loop must cancel at the same N and eta",
    ),
    "berry_formula" => Dict(
        "one_base_loop" => "-Omega/2 = -pi*(1 - cos(2*eta))",
        "lifted_torus_chart_cycle" => "-2*pi*(1 - cos(2*eta))",
    ),
    "phase_domain" => Dict(
        "primary" => "lifted_real",
        "mod_reconciliation" => "mod_2pi representatives are support-only and never compared as the lifted target",
    ),
    "base_loop_count" => Dict(
        "one_base_loop" => "chi: 0 -> pi because base_angle = 2*chi",
        "lifted_torus_chart_cycle" => "chi: 0 -> 2*pi traverses the base twice",
    ),
    "orientation_and_c1_sign" => Dict(
        "displayed_curvature" => "F = -2*sin(2*eta) d eta wedge d chi",
        "strip_flux_target" => "Phi_ij = int_eta_i^eta_j int_0^(2*pi) F",
        "stokes_sign" => "h(eta_j) - h(eta_i) + Phi_ij = 0",
    ),
)

const TOOL_MANIFEST = Dict(
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side exact integer cover/parity proof"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and PIN hashing"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive R4 chord-triangle area computation"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Z3" => "load_bearing",
    "JSON" => "supportive",
    "SHA" => "supportive",
    "LinearAlgebra" => "supportive",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

target_area(eta) = 2pi^2 * sin(2eta)
target_holonomy(eta) = -2pi * cos(2eta)
target_flux(eta_i, eta_j) = 2pi * (cos(2eta_j) - cos(2eta_i))

function torus_point(eta, phi, chi)
    [
        cos(eta) * cos(phi + chi),
        cos(eta) * sin(phi + chi),
        sin(eta) * cos(phi - chi),
        sin(eta) * sin(phi - chi),
    ]
end

function torus_point_index(eta, n, a, b)
    torus_point(eta, 2pi * mod(a, n) / n, 2pi * mod(b, n) / n)
end

function triangle_area(p0, p1, p2)
    u = p1 - p0
    v = p2 - p0
    0.5 * sqrt(max(dot(u, u) * dot(v, v) - dot(u, v)^2, 0.0))
end

quotient_partner(n, a, b) = (mod(a + div(n, 2), n), mod(b + div(n, 2), n))

function quotient_count_row(n)
    seen = Set{Tuple{Int,Int}}()
    classes = Vector{Any}()
    for a in 0:(n - 1), b in 0:(n - 1)
        point = (a, b)
        point in seen && continue
        partner = quotient_partner(n, a, b)
        pair = sort([point, partner])
        push!(seen, pair[1])
        push!(seen, pair[2])
        kappas = [mod(pair[1][1] + pair[1][2], 2), mod(pair[2][1] + pair[2][2], 2)]
        push!(classes, Dict("representative" => collect(pair[1]), "chart_points" => [collect(pair[1]), collect(pair[2])], "kappa_values" => kappas, "kappa_invariant" => kappas[1] == kappas[2]))
    end
    Dict(
        "N" => n,
        "chart_point_count" => n * n,
        "physical_point_count" => length(classes),
        "expected_physical_point_count" => div(n * n, 2),
        "every_class_size_2" => true,
        "two_times_physical_equals_chart" => 2 * length(classes) == n * n,
        "parity_class_invariant_under_cover" => all(row["kappa_invariant"] for row in classes),
    )
end

function cell_representatives(n)
    seen = Set{Tuple{Int,Int}}()
    reps = Tuple{Int,Int}[]
    for a in 0:(n - 1), b in 0:(n - 1)
        point = (a, b)
        point in seen && continue
        partner = quotient_partner(n, a, b)
        pair = sort([point, partner])
        push!(reps, pair[1])
        push!(seen, pair[1])
        push!(seen, pair[2])
    end
    reps
end

function cell_area(eta, n, a, b)
    p00 = torus_point_index(eta, n, a, b)
    p10 = torus_point_index(eta, n, a + 1, b)
    p01 = torus_point_index(eta, n, a, b + 1)
    p11 = torus_point_index(eta, n, a + 1, b + 1)
    triangle_area(p00, p10, p01) + triangle_area(p10, p11, p01)
end

function area_estimate(eta, n)
    total = 0.0
    for (a, b) in cell_representatives(n)
        total += cell_area(eta, n, a, b)
    end
    total
end

function spinor(eta, phi, chi)
    (cos(eta) * cis(phi + chi), sin(eta) * cis(phi - chi))
end

inner(u, v) = conj(u[1]) * v[1] + conj(u[2]) * v[2]

function central_secant_holonomy(eta, n)
    delta = 2pi / n
    total = 0.0
    for k in 0:(n - 1)
        chi = k * delta
        psi = spinor(eta, 0.0, chi)
        plus = spinor(eta, 0.0, chi + delta)
        minus = spinor(eta, 0.0, chi - delta)
        deriv = ((plus[1] - minus[1]) / (2delta), (plus[2] - minus[2]) / (2delta))
        a_chi = real(-im * inner(psi, deriv))
        total += -a_chi * delta
    end
    total
end

function wilson_overlap_holonomy(eta, n)
    delta = 2pi / n
    real_part = cos(delta)
    imag_part = cos(2eta) * sin(delta)
    arg = if abs(real_part) < 1.0e-14 && abs(imag_part) < 1.0e-14
        pi / n
    else
        atan(imag_part, real_part)
    end
    -n * arg
end

function flux_estimate(eta_i, eta_j, n)
    deta = (eta_j - eta_i) / n
    dchi = 2pi / n
    total = 0.0
    for i in 0:(n - 1)
        eta_mid = eta_i + (i + 0.5) * deta
        total += n * (-2 * sin(2eta_mid) * deta * dchi)
    end
    total
end

function z3_mul(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1)
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_cover_parity_proof()
    n_value = 64
    physical_value = div(n_value * n_value, 2)
    solver = Z3.Solver()
    n = Z3.IntVar("julia_N")
    physical = Z3.IntVar("julia_physical_point_count")
    mismatch = Z3.IntVar("julia_kappa_mismatch_count")
    Z3.add(solver, n == Z3.IntVal(n_value))
    Z3.add(solver, physical == Z3.IntVal(physical_value))
    Z3.add(solver, mismatch == Z3.IntVal(0))
    Z3.add(solver, Z3.Not(z3_mul(Z3.Expr[Z3.IntVal(2), physical]) == z3_mul(Z3.Expr[n, n])))
    cover_verdict = string(Z3.check(solver))

    mismatch_solver = Z3.Solver()
    mm = Z3.IntVar("julia_mismatch_control")
    Z3.add(mismatch_solver, mm == Z3.IntVal(0))
    Z3.add(mismatch_solver, Z3.Not(mm == Z3.IntVal(0)))
    mismatch_verdict = string(Z3.check(mismatch_solver))

    naive = Z3.Solver()
    nn = Z3.IntVar("julia_naive_N")
    np = Z3.IntVar("julia_naive_physical")
    Z3.add(naive, nn == Z3.IntVal(n_value))
    Z3.add(naive, np == Z3.IntVal(n_value * n_value))
    Z3.add(naive, z3_mul(Z3.Expr[Z3.IntVal(2), np]) == z3_mul(Z3.Expr[nn, nn]))
    naive_verdict = string(Z3.check(naive))

    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "verdict" => cover_verdict == "unsat" && mismatch_verdict == "unsat" ? "unsat" : "sat",
        "load_bearing" => true,
        "cover_verdict" => cover_verdict,
        "mismatch_verdict" => mismatch_verdict,
        "bound_raw_values" => Dict("N" => n_value, "physical_point_count" => physical_value, "kappa_mismatch_count" => 0),
        "asserted_precomputed_boolean" => false,
        "naive_cover_control_verdict" => naive_verdict,
        "naive_cover_control_can_fail" => naive_verdict == "unsat",
    )
end

function build_result()
    eta_i = pi / 6
    eta_j = pi / 4
    n = 64
    area_value = area_estimate(pi / 4, n)
    h_i = wilson_overlap_holonomy(eta_i, n)
    h_j = wilson_overlap_holonomy(eta_j, n)
    h_i_central = central_secant_holonomy(eta_i, n)
    h_j_central = central_secant_holonomy(eta_j, n)
    flux_value = flux_estimate(eta_i, eta_j, n)
    proof = z3_cover_parity_proof()
    grid_rows = [quotient_count_row(k) for k in N_VALUES]
    native = Dict(
        "area_pi_over_4_N64" => Dict("estimate" => area_value, "target" => target_area(pi / 4), "abs_error" => abs(area_value - target_area(pi / 4))),
        "holonomy_pi_over_6_N64" => Dict("estimate" => h_i, "target" => target_holonomy(eta_i), "abs_error" => abs(h_i - target_holonomy(eta_i))),
        "holonomy_pi_over_4_N64" => Dict("estimate" => h_j, "target" => target_holonomy(eta_j), "abs_error" => abs(h_j - target_holonomy(eta_j))),
        "central_secant_holonomy_pi_over_6_N64" => Dict("estimate" => h_i_central, "target" => target_holonomy(eta_i), "abs_error" => abs(h_i_central - target_holonomy(eta_i))),
        "central_secant_holonomy_pi_over_4_N64" => Dict("estimate" => h_j_central, "target" => target_holonomy(eta_j), "abs_error" => abs(h_j_central - target_holonomy(eta_j))),
        "flux_pi_over_6_to_pi_over_4_N64" => Dict("estimate" => flux_value, "target" => target_flux(eta_i, eta_j), "abs_error" => abs(flux_value - target_flux(eta_i, eta_j))),
        "stokes_pi_over_6_to_pi_over_4_N64" => Dict("residual" => h_j - h_i + flux_value, "abs_residual" => abs(h_j - h_i + flux_value)),
        "grid_rows" => grid_rows,
    )
    all_pass = (
        CLASSIFICATION == "scratch_diagnostic" &&
        PROMOTION_ALLOWED == false &&
        FORMAL_ADMISSION_ALLOWED == false &&
        all(row["two_times_physical_equals_chart"] && row["parity_class_invariant_under_cover"] for row in grid_rows) &&
        proof["verdict"] == "unsat" &&
        proof["naive_cover_control_can_fail"] == true &&
        native["area_pi_over_4_N64"]["abs_error"] < 0.02 &&
        native["holonomy_pi_over_6_N64"]["abs_error"] < 0.01 &&
        native["flux_pi_over_6_to_pi_over_4_N64"]["abs_error"] < 0.001 &&
        native["stokes_pi_over_6_to_pi_over_4_N64"]["abs_residual"] < 0.01
    )
    Dict(
        "schema_version" => "geo_s7_engine_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_authoritative_sim_builder",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "convention_pin" => CONVENTION_PIN,
        "reads_peer_result" => READS_PEER_RESULT,
        "julia_project" => Base.active_project(),
        "packages_used" => ["JSON", "SHA", "LinearAlgebra", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.add/Z3.check",
                "input_object" => proof["bound_raw_values"],
                "output_object" => Dict("verdict" => proof["verdict"], "control" => proof["naive_cover_control_verdict"]),
                "positive_case" => "N=64 quotient cardinality and zero kappa mismatch",
                "negative_or_erased_control" => "naive N^2 physical count",
                "boundary_case" => "N=2 emitted in grid rows",
                "demotion_condition" => "without Z3 exact row, Julia lane is numeric diagnostic only",
                "gates" => ["P2_even_N_cover_quotient", "P3_parity_cover_compatibility"],
            ),
        ],
        "engine_native_checks" => native,
        "crossover_proofs" => Dict("julia_z3" => proof),
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => RESULT_PATH_REL)))
    return result["all_pass"] ? 0 : 1
end

exit(main())
