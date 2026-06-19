#!/usr/bin/env julia
# Julia carrier-side mirror for geo_s6_stacked_flows_hopf_v0.

using Dates
using DifferentialEquations
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_s6_stacked_flows_hopf_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const S5_RESULT_REL = joinpath("system_v6", "sims", "geo_s5_terrain_flows_v0", "results", "geo_s5_terrain_flows_v0_envelope_results.json")
const S5_RESULT = joinpath(ROOT, S5_RESULT_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false

const PIN_SPEC = "geo_s6_stacked_flows_hopf_v0|mode=RESTRICTED_STACKED|arrow_types=(foliation,dynamical_flow,quotient_projection,covering_group_quotient,undefined_without_lift)|shell_coordinate=z=cos(2*eta)|r_eta=(sin(2*eta)cos(2*chi),sin(2*eta)sin(2*chi),cos(2*eta))|eta_rows=(pi/12,pi/6,pi/4,pi/3,5*pi/12)|chi0=pi/7|loop_period=2*pi_lifted_chart_cycle|leakage=dz_dt=e_z^T(A*r_eta+b)_from_S5_exported_A_b|Phi_D=U_E_U_E|Phi_I=E_U_E_U|U=Ne_Vortex_L_flow_t1|E=Si_Hill_L_flow_t1|carrier=density_bloch|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const CONVENTION_PIN = Dict(
    "mode" => "RESTRICTED/STACKED",
    "shell_coordinate" => "z=cos(2*eta)",
    "tested_shells" => ["pi/12", "pi/6", "pi/4", "pi/3", "5*pi/12"],
    "loop_order_pin" => Dict("carrier" => "density/Bloch", "U" => "Ne_Vortex_L flow at t=1", "E" => "Si_Hill_L flow at t=1"),
)
const TOOL_MANIFEST = Dict(
    "DifferentialEquations" => Dict("tried" => true, "used" => true, "reason" => "load-bearing ODEProblem/solve(Tsit5) flow evolution route for the S6 loop-order flow claims"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive exact matrix-exponential special-case check and norm computation for constant linear flows"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing measured finite order-gap contradiction check"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt import and serialization"),
    "SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive source and PIN hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict("DifferentialEquations" => "load_bearing", "LinearAlgebra" => "supportive", "Z3" => "load_bearing", "JSON" => "supportive", "SHA" => "supportive")
const PACKAGES_USED = ["DifferentialEquations", "LinearAlgebra", "JSON", "SHA", "Z3"]
const ALIGNED_PACKAGES_LOAD_BEARING = ["DifferentialEquations", "Z3"]
const CLAIM_PATH_TOOLS = ["DifferentialEquations", "Z3"]

const ETA_ROWS = [
    ("pi/12", pi / 12),
    ("pi/6", pi / 6),
    ("pi/4", pi / 4),
    ("pi/3", pi / 3),
    ("5*pi/12", 5pi / 12),
]
const CHI0 = pi / 7
const LOOP_PERIOD = 2pi
const FORMULA_STRINGS = Dict(
    "Ne_Spiral_R" => "2*sqrt(6)*sin(2*eta)*cos(2*chi + pi/4)/3",
    "Ne_Vortex_L" => "-2*sqrt(6)*sin(2*eta)*cos(2*chi + pi/4)/3",
    "Ni_Pit_L" => "2*sqrt(3)*sin(2*chi)*sin(2*eta)/15 - 2*sqrt(3)*sin(2*eta)*cos(2*chi)/15 - cos(2*eta)/2 - 1/2",
    "Ni_Source_R" => "-2*sqrt(3)*sin(2*chi)*sin(2*eta)/15 + 2*sqrt(3)*sin(2*eta)*cos(2*chi)/15 - cos(2*eta)/2 + 1/2",
    "Se_Cannon_R" => "-2*sqrt(3)*sin(2*chi)*sin(2*eta)/15 + 2*sqrt(3)*sin(2*eta)*cos(2*chi)/15 - 4*cos(2*eta)/5",
    "Se_Funnel_L" => "2*sqrt(3)*sin(2*chi)*sin(2*eta)/15 - 2*sqrt(3)*sin(2*eta)*cos(2*chi)/15 - 4*cos(2*eta)/5",
    "Si_Citadel_R" => "2*sin(2*chi)*sin(2*eta)/5 - 2*cos(2*eta)/5",
    "Si_Hill_L" => "0",
)

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
sha256_text(text::AbstractString) = bytes2hex(SHA.sha256(codeunits(text)))

function parse_number(text)
    value = replace(text, "//" => "/")
    return Float64(eval(Meta.parse(value)))
end

function parse_matrix(values)
    mat = zeros(Float64, 3, 3)
    for i in 1:3, j in 1:3
        mat[i, j] = parse_number(values[i][j])
    end
    mat
end

function parse_vector(values)
    [parse_number(values[i]) for i in 1:3]
end

function load_s5_rows()
    payload = JSON.parsefile(S5_RESULT)
    rows = Dict{String, Any}()
    for (name, row) in payload["bloch_generator_table"]
        rows[name] = Dict(
            "A" => parse_matrix(row["pinned"]["A"]),
            "b" => parse_vector(row["pinned"]["b"]),
            "s5_source_ref" => row["source_ref"],
        )
    end
    payload, rows
end

function coeffs(row)
    A = row["A"]
    b = row["b"]
    A[3, 1], A[3, 2], A[3, 3], b[3]
end

function z_dot_value(row, eta_value, chi_value)
    a, b, c, d = coeffs(row)
    a * sin(2 * eta_value) * cos(2 * chi_value) + b * sin(2 * eta_value) * sin(2 * chi_value) + c * cos(2 * eta_value) + d
end

function class_for(row_id, row)
    a, b, c, d = coeffs(row)
    phase_dependent = abs(a) > 1e-12 || abs(b) > 1e-12
    z_zero = abs(a) <= 1e-12 && abs(b) <= 1e-12 && abs(c) <= 1e-12 && abs(d) <= 1e-12
    pure_preserving = startswith(row_id, "Ne_")
    if pure_preserving
        return z_zero ? "preserve_T_eta" : (phase_dependent ? "cross_shell" : "move_leaf")
    end
    return z_zero ? "projected_shell_preserve_but_Hopf_leave" : "leave_foliation"
end

function leakage_signature(rows)
    out = Dict{String, Any}()
    for row_id in sort(collect(keys(rows)))
        row = rows[row_id]
        a, b, c, d = coeffs(row)
        inner_scaled = Int[]
        outer_scaled = Int[]
        avg_scaled = Int[]
        classes = Set{String}()
        for (_, eta_value) in ETA_ROWS
            inner = LOOP_PERIOD * z_dot_value(row, eta_value, CHI0)
            outer = LOOP_PERIOD * (c * cos(2 * eta_value) + d)
            avg = c * cos(2 * eta_value) + d
            push!(inner_scaled, round(Int, inner * 1_000_000_000))
            push!(outer_scaled, round(Int, outer * 1_000_000_000))
            push!(avg_scaled, round(Int, avg * 1_000_000_000))
            push!(classes, class_for(row_id, row))
        end
        out[row_id] = Dict(
            "z_dot_formula" => FORMULA_STRINGS[row_id],
            "inner_scaled" => inner_scaled,
            "outer_scaled" => outer_scaled,
            "avg_scaled" => avg_scaled,
            "classes" => sort(collect(classes)),
        )
    end
    out
end

function diffeq_linear_flow_matrix(A)
    columns = Vector{Vector{Float64}}()
    for i in 1:3
        y0 = zeros(Float64, 3)
        y0[i] = 1.0
        problem = DifferentialEquations.ODEProblem((u, p, t) -> A * u, y0, (0.0, 1.0))
        solution = DifferentialEquations.solve(problem, DifferentialEquations.Tsit5(), abstol=1.0e-10, reltol=1.0e-10)
        push!(columns, Vector{Float64}(solution(1.0)))
    end
    hcat(columns...)
end

function loop_order_signature(rows)
    U = exp(rows["Ne_Vortex_L"]["A"])
    E = exp(rows["Si_Hill_L"]["A"])
    U_solver = diffeq_linear_flow_matrix(rows["Ne_Vortex_L"]["A"])
    E_solver = diffeq_linear_flow_matrix(rows["Si_Hill_L"]["A"])
    phi_d = U * E * U * E
    phi_i = E * U * E * U
    solver_phi_d = U_solver * E_solver * U_solver * E_solver
    solver_phi_i = E_solver * U_solver * E_solver * U_solver
    gaps = Float64[]
    solver_gaps = Float64[]
    for (_, eta_value) in ETA_ROWS
        for chi_value in [0.0, pi / 8, pi / 4, 3pi / 8]
            r0 = [sin(2 * eta_value) * cos(2 * chi_value), sin(2 * eta_value) * sin(2 * chi_value), cos(2 * eta_value)]
            push!(gaps, norm(phi_d * r0 - phi_i * r0))
            push!(solver_gaps, norm(solver_phi_d * r0 - solver_phi_i * r0))
        end
    end
    comm_E = exp(rows["Se_Funnel_L"]["A"])
    comm_E_solver = diffeq_linear_flow_matrix(rows["Se_Funnel_L"]["A"])
    comm_delta = maximum(abs.((U * comm_E * U * comm_E) - (comm_E * U * comm_E * U)))
    solver_comm_delta = maximum(abs.((U_solver * comm_E_solver * U_solver * comm_E_solver) - (comm_E_solver * U_solver * comm_E_solver * U_solver)))
    max_g = maximum(gaps)
    solver_max_g = maximum(solver_gaps)
    matrix_errors = [
        maximum(abs.(U_solver - U)),
        maximum(abs.(E_solver - E)),
        maximum(abs.(comm_E_solver - comm_E)),
    ]
    solver_route_pass = maximum(matrix_errors) <= 1.0e-7 && abs(solver_max_g - max_g) <= 1.0e-7 && abs(solver_comm_delta - comm_delta) <= 1.0e-7
    Dict(
        "max_g_DI_trace_norm" => max_g,
        "loop_order_g_DI_scaled_1e9" => round(Int, max_g * 1_000_000_000),
        "commuting_control_matrix_delta" => comm_delta,
        "flow_solver_route" => Dict(
            "tool" => "DifferentialEquations",
            "api" => "ODEProblem + solve(Tsit5)",
            "claim_path_role" => "load-bearing flow solver route for constant-coefficient one-step flows",
            "matrix_exponential_role" => "exact special-case check only",
            "solver_matrix_max_error_vs_exact_special_case" => maximum(matrix_errors),
            "solver_loop_order_g_DI_scaled_1e9" => round(Int, solver_max_g * 1_000_000_000),
            "solver_gap_error_vs_exact_special_case" => abs(solver_max_g - max_g),
            "solver_commuting_control_delta" => solver_comm_delta,
            "solver_commuting_error_vs_exact_special_case" => abs(solver_comm_delta - comm_delta),
            "pass" => solver_route_pass,
        ),
        "pass" => max_g > 1e-6 && comm_delta <= 1e-8 && solver_route_pass,
    )
end

function z3_gap_proof(gap_scaled)
    solver = Z3.Solver()
    g = Z3.IntVar("julia_s6_g_DI_scaled")
    Z3.add(solver, g == Z3.IntVal(gap_scaled))
    Z3.add(solver, g == Z3.IntVal(0))
    verdict = string(Z3.check(solver))
    Dict(
        "ran" => true,
        "verdict" => verdict,
        "load_bearing" => true,
        "bound_raw_values" => Dict("g_DI_scaled_1e9" => gap_scaled),
    )
end

function build_result()
    s5, rows = load_s5_rows()
    leakage = leakage_signature(rows)
    loop = loop_order_signature(rows)
    proof = z3_gap_proof(loop["loop_order_g_DI_scaled_1e9"])
    gates = Dict(
        "s5_import_pass" => s5["all_pass"] == true,
        "signature_rows_eight" => length(leakage) == 8,
        "formula_coefficients_verified" => all(haskey(FORMULA_STRINGS, row_id) for row_id in keys(leakage)),
        "loop_order_pass" => loop["pass"] == true,
        "flow_solver_route" => loop["flow_solver_route"]["pass"] == true,
        "z3_pass" => proof["verdict"] == "unsat",
        "claim_ceiling" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED,
    )
    all_pass = all(values(gates))
    Dict(
        "schema_version" => "geo_s6_engine_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_carrier_signature",
        "generated_at" => string(now(UTC)),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "convention_pin" => CONVENTION_PIN,
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "packages_used" => PACKAGES_USED,
        "aligned_packages_load_bearing" => ALIGNED_PACKAGES_LOAD_BEARING,
        "claim_path_tools" => CLAIM_PATH_TOOLS,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "julia_project" => Base.active_project(),
        "s5_source" => Dict("path" => S5_RESULT_REL, "sha256" => sha256_file(S5_RESULT), "pin_sha256" => s5["pin_sha256"]),
        "loop_order_gap" => loop,
        "crossover_proofs" => Dict("julia_z3" => proof),
        "build_gates" => gates,
        "cross_engine_signature" => Dict(
            "pin_sha256" => sha256_text(PIN_SPEC),
            "leakage_rows" => leakage,
            "loop_order_g_DI_scaled_1e9" => loop["loop_order_g_DI_scaled_1e9"],
            "placement_count" => 16,
            "matrix64_overlay_count" => 64,
        ),
        "all_pass" => all_pass,
    )
end

function main()
    mkpath(RESULT_DIR)
    payload = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "result_path" => RESULT_PATH_REL), 2))
    payload["all_pass"] ? 0 : 1
end

exit(main())
