#!/usr/bin/env julia
# object_id: foundation_nested_hopf_weyl_signed_cut_ratchet
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using SHA
using Z3

const PIN_SPEC = """object_id=foundation_nested_hopf_weyl_signed_cut_ratchet
rung_count=3
eta_shells_rad=[eta_1=1.17,eta_2=0.86,eta_3=0.53] with eta_1 > eta_2 > eta_3 nested Hopf tori in S^3
stacking_order=Stack_r = Phi_r after Phi_{r-1} after ... after Phi_1; adjacent order test compares Phi_r after Phi_{r+1} vs Phi_{r+1} after Phi_r on rho_probe=rho_2
constraint_filters_left_sheet=K_1=[[1,0],[0,-1]], K_2=[[1,1],[1,-1]], K_3=[[1,1],[0,1]], Phi_r(rho)=normalize((K_r kron I_R) rho (K_r kron I_R)^adjoint)
rho_family=rho_r=|psi_r><psi_r|, |psi_r>=cos(theta_r)|L0 R0>+sin(theta_r)|L1 R1>, theta_r=0.70*(r-1)/2 for r=1,2,3
separable_control=rho_sep_r=diag(cos(theta_r)^2,sin(theta_r)^2)_L kron diag(cos(theta_r)^2,sin(theta_r)^2)_R
cut=A|B is Weyl-L sheet vs Weyl-R sheet
entropy_log_base=e
probe_sets=M_1=[Z_L Z_R]; M_2=M_1+[X_L X_R]; M_3=M_2+[Z_L,Z_R,Y_L Y_R]
claim_ceiling=scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false; feeds Xi/Axis-0 bridge problem but does not close bridge, Axis0, manifold, or M(C)
"""

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const OBJECT_ID = "foundation_nested_hopf_weyl_signed_cut_ratchet"
const ENGINE = "julia"
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_nested_hopf_weyl_signed_cut_ratchet_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "results", "foundation_nested_hopf_weyl_signed_cut_ratchet_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const KAPPA = 0.70
const TOL = 1.0e-9
const BASIS_LR = QuantumOptics.tensor(QuantumOptics.SpinBasis(1 // 2), QuantumOptics.SpinBasis(1 // 2))

const SOURCE_DEPENDENCIES = [
    joinpath(ROOT, "system_v5", "julia_carrier", "clifford_torus_nested_hopf_foliation.jl"),
    joinpath(ROOT, "system_v5", "julia_carrier", "jax_clifford_torus_nested_hopf_foliation.py"),
    joinpath(ROOT, "system_v5", "julia_carrier", "weyl_sheet_pair_probe.jl"),
    joinpath(ROOT, "system_v5", "julia_carrier", "jax_weyl_sheet_pair_probe.py"),
    joinpath(ROOT, "system_v5", "ops", "formal_scouts", "foundation_qit_operator_composition_mcp_jax.py"),
]

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive carrier-project QIT surface for Operator, ptrace, and entropy_vn; no separate capability-probe receipt, so not declared load_bearing",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Z3.jl matrix-entry proof that forcing rung-2 adjacent filters to commute is UNSAT",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive matrix products, eigenspectrum residuals, trace norms, and finite probe expectations",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization, timestamps, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "supportive",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA" => "supportive",
)

const I2 = ComplexF64[1 0; 0 1]
const X = ComplexF64[0 1; 1 0]
const Y = ComplexF64[0 -im; im 0]
const Z = ComplexF64[1 0; 0 -1]
const K_FILTERS = Dict{Int,Matrix{ComplexF64}}(
    1 => Z,
    2 => ComplexF64[1 1; 1 -1],
    3 => ComplexF64[1 1; 0 1],
)
const COMMUTING_FILTERS = Dict{Int,Matrix{ComplexF64}}(
    1 => ComplexF64[1 0; 0 0.80],
    2 => ComplexF64[1 0; 0 0.60],
    3 => ComplexF64[1 0; 0 0.40],
)
const ETA_SHELLS = Dict(1 => 1.17, 2 => 0.86, 3 => 0.53)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

theta(rung::Int) = KAPPA * (rung - 1) / 2.0

function rho_for_rung(rung::Int)
    th = theta(rung)
    psi = ComplexF64[cos(th), 0.0, 0.0, sin(th)]
    psi * psi'
end

function separable_rho_for_rung(rung::Int)
    th = theta(rung)
    probs = Float64[cos(th)^2, sin(th)^2]
    kron(ComplexF64[probs[1] 0; 0 probs[2]], ComplexF64[probs[1] 0; 0 probs[2]])
end

hermitize(rho::Matrix{ComplexF64}) = 0.5 .* (rho .+ rho')
trace_real(rho::Matrix{ComplexF64}) = Float64(real(tr(rho)))

function normalize_density(rho::Matrix{ComplexF64})
    herm = hermitize(rho)
    herm ./ trace_real(herm)
end

function apply_filter(rho::Matrix{ComplexF64}, filter_matrix::Matrix{ComplexF64})
    lifted = kron(filter_matrix, I2)
    normalize_density(lifted * rho * lifted')
end

function stack_state(rung::Int, rho::Matrix{ComplexF64}, filters::Dict{Int,Matrix{ComplexF64}})
    out = rho
    for idx in 1:rung
        out = apply_filter(out, filters[idx])
    end
    out
end

function entropy_matrix(rho::Matrix{ComplexF64})
    op = QuantumOptics.Operator(BASIS_LR, BASIS_LR, hermitize(rho))
    Float64(real(QuantumOptics.entropy_vn(op)))
end

function entropy_b(rho::Matrix{ComplexF64})
    op = QuantumOptics.Operator(BASIS_LR, BASIS_LR, hermitize(rho))
    reduced_b = QuantumOptics.ptrace(op, [1])
    Float64(real(QuantumOptics.entropy_vn(reduced_b)))
end

conditional_entropy(rho::Matrix{ComplexF64}) = entropy_matrix(rho) - entropy_b(rho)

function entropy_components(rho::Matrix{ComplexF64})
    Dict{String,Any}(
        "S_AB" => entropy_matrix(rho),
        "S_B" => entropy_b(rho),
    )
end

function trace_norm_hermitian(matrix::Matrix{ComplexF64})
    sum(abs.(eigvals(Hermitian(hermitize(matrix)))))
end

function order_gap(first::Matrix{ComplexF64}, second::Matrix{ComplexF64}, rho_probe::Matrix{ComplexF64})
    left = apply_filter(apply_filter(rho_probe, second), first)
    right = apply_filter(apply_filter(rho_probe, first), second)
    Float64(trace_norm_hermitian(left - right))
end

function probe_ops()
    Dict{String,Matrix{ComplexF64}}(
        "Z_L Z_R" => kron(Z, Z),
        "X_L X_R" => kron(X, X),
        "Z_L" => kron(Z, I2),
        "Z_R" => kron(I2, Z),
        "Y_L Y_R" => kron(Y, Y),
    )
end

function probe_family(rung::Int)
    if rung == 1
        return ["Z_L Z_R"]
    elseif rung == 2
        return ["Z_L Z_R", "X_L X_R"]
    end
    ["Z_L Z_R", "X_L X_R", "Z_L", "Z_R", "Y_L Y_R"]
end

expectation(rho::Matrix{ComplexF64}, op::Matrix{ComplexF64}) = Float64(real(tr(op * rho)))

function class_count(vectors::Vector{Vector{Float64}})
    classes = Vector{Vector{Float64}}()
    for vector in vectors
        seen = false
        for existing in classes
            if all(abs(vector[i] - existing[i]) <= 1.0e-8 for i in eachindex(vector))
                seen = true
                break
            end
        end
        !seen && push!(classes, vector)
    end
    length(classes)
end

function quotient_report()
    ops = probe_ops()
    rhos = [rho_for_rung(r) for r in 1:3]
    report = Dict{String,Any}()
    for rung in 1:3
        family = probe_family(rung)
        vectors = [[expectation(rho, ops[name]) for name in family] for rho in rhos]
        report["M_$(rung)"] = Dict{String,Any}(
            "operators" => family,
            "operator_count" => length(family),
            "distinguishable_class_count" => class_count(vectors),
            "expectation_vectors_by_rung" => Dict(string(idx) => vectors[idx] for idx in 1:3),
        )
    end
    report
end

function z3_add(args)
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul(args)
    isempty(args) && return Z3.IntVal(1)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_force_commute_status(a_values::Vector{Vector{Int}}, b_values::Vector{Vector{Int}}, label::String)
    solver = Z3.Solver()
    a = [Z3.IntVar("$(label)_a_$(i)_$(j)") for i in 1:2, j in 1:2]
    b = [Z3.IntVar("$(label)_b_$(i)_$(j)") for i in 1:2, j in 1:2]
    for i in 1:2, j in 1:2
        Z3.add(solver, a[i, j] == Z3.IntVal(a_values[i][j]))
        Z3.add(solver, b[i, j] == Z3.IntVal(b_values[i][j]))
    end
    ab = [z3_add([z3_mul([a[i, 1], b[1, j]]), z3_mul([a[i, 2], b[2, j]])]) for i in 1:2, j in 1:2]
    ba = [z3_add([z3_mul([b[i, 1], a[1, j]]), z3_mul([b[i, 2], a[2, j]])]) for i in 1:2, j in 1:2]
    for i in 1:2, j in 1:2
        Z3.add(solver, ab[i, j] == ba[i, j])
    end
    status = string(Z3.check(solver))
    Dict{String,Any}(
        "solver" => "Z3.jl",
        "level" => "filter_level",
        "force_commute_verdict" => status,
        "verdict" => status,
        "bound_entries" => 8,
        "derived_products" => "AB and BA entries are computed inside Z3.jl from bound matrix entries",
        "asserted_precomputed_scalar" => false,
    )
end

function transpose_terms(matrix)
    [matrix[j, i] for i in 1:size(matrix, 2), j in 1:size(matrix, 1)]
end

function z3_matmul(left, right)
    [z3_add([z3_mul([left[i, k], right[k, j]]) for k in 1:size(right, 1)]) for i in 1:size(left, 1), j in 1:size(right, 2)]
end

function z3_lift_left_filter(filter_terms)
    [iseven(row - col) ? filter_terms[div(row + 1, 2), div(col + 1, 2)] : Z3.IntVal(0) for row in 1:4, col in 1:4]
end

function z3_channel_action(filter_terms, rho_terms)
    lifted = z3_lift_left_filter(filter_terms)
    z3_matmul(z3_matmul(lifted, rho_terms), transpose_terms(lifted))
end

function rho_probe_scaled_entries(rho_probe::Matrix{ComplexF64})
    scale = 10^12
    entries = [[Int(round(real(rho_probe[i, j]) * scale)) for j in 1:4] for i in 1:4]
    entries, scale
end

function z3_force_channel_commute_status(
    a_values::Vector{Vector{Int}}, b_values::Vector{Vector{Int}}, rho_values::Vector{Vector{Int}}, rho_scale::Int, label::String
)
    solver = Z3.Solver()
    a = [Z3.IntVal(a_values[i][j]) for i in 1:2, j in 1:2]
    b = [Z3.IntVal(b_values[i][j]) for i in 1:2, j in 1:2]
    rho = [Z3.IntVar("$(label)_rho_$(i)_$(j)") for i in 1:4, j in 1:4]
    for i in 1:4, j in 1:4
        Z3.add(solver, rho[i, j] == Z3.IntVal(rho_values[i][j]))
    end
    ab = z3_channel_action(a, z3_channel_action(b, rho))
    ba = z3_channel_action(b, z3_channel_action(a, rho))
    for i in 1:4, j in 1:4
        Z3.add(solver, ab[i, j] == ba[i, j])
    end
    status = string(Z3.check(solver))
    Dict{String,Any}(
        "solver" => "Z3.jl",
        "level" => "channel_level",
        "normalization" => "unnormalized_channel_action",
        "force_channel_commute_verdict" => status,
        "verdict" => status,
        "bound_filter_entries" => 8,
        "bound_rho_probe_entries" => 16,
        "bound_entries" => 24,
        "rho_probe_source" => "rho_2 real entries scaled to Int for Z3.jl",
        "rho_probe_integer_scale" => rho_scale,
        "derived_products" => "Phi_a(Phi_b(rho_probe)) and Phi_b(Phi_a(rho_probe)) 4x4 entries are constructed inside Z3.jl from bound filter and scaled rho entries",
        "asserted_precomputed_scalar" => false,
    )
end

function smt_report(rho_probe::Matrix{ComplexF64})
    a = [[1, 1], [1, -1]]
    b = [[1, 1], [0, 1]]
    ca = [[1, 0], [0, 3]]
    cb = [[2, 0], [0, 5]]
    rho_values, rho_scale = rho_probe_scaled_entries(rho_probe)
    z3_non = z3_force_commute_status(a, b, "rung2_noncommuting")
    z3_ctrl = z3_force_commute_status(ca, cb, "rung2_commuting_control")
    z3_channel_non = z3_force_channel_commute_status(a, b, rho_values, rho_scale, "rung2_channel_noncommuting")
    z3_channel_ctrl = z3_force_channel_commute_status(ca, cb, rho_values, rho_scale, "rung2_channel_commuting_control")
    Dict{String,Any}(
        "rung2_adjacent_pair" => Dict(
            "A" => a,
            "B" => b,
            "filter_level" => Dict("z3" => z3_non),
            "channel_level" => Dict("z3" => z3_channel_non),
            "z3" => z3_channel_non,
        ),
        "commuting_control" => Dict(
            "A" => ca,
            "B" => cb,
            "filter_level" => Dict("z3" => z3_ctrl),
            "channel_level" => Dict("z3" => z3_channel_ctrl),
            "z3" => z3_channel_ctrl,
        ),
    )
end

function density_diagnostics(rho::Matrix{ComplexF64})
    vals = eigvals(Hermitian(hermitize(rho)))
    Dict{String,Any}(
        "trace" => trace_real(rho),
        "min_eigenvalue" => Float64(minimum(vals)),
        "hermitian_residual" => Float64(maximum(abs.(rho - rho'))),
        "psd" => minimum(vals) >= -1.0e-9,
    )
end

function build_result()
    quotients = quotient_report()
    rhos = Dict(r => rho_for_rung(r) for r in 1:3)
    sep_rhos = Dict(r => separable_rho_for_rung(r) for r in 1:3)
    rho_probe = rhos[2]
    conditional = Dict(r => conditional_entropy(rhos[r]) for r in 1:3)
    signed_cut = Dict(r => -conditional[r] for r in 1:3)
    sep_conditional = Dict(r => conditional_entropy(sep_rhos[r]) for r in 1:3)
    carrier_components = Dict(r => entropy_components(rhos[r]) for r in 1:3)
    sep_components = Dict(r => entropy_components(sep_rhos[r]) for r in 1:3)
    gaps = Dict{String,Any}(
        "r1_r2" => order_gap(K_FILTERS[1], K_FILTERS[2], rho_probe),
        "r2_r3" => order_gap(K_FILTERS[2], K_FILTERS[3], rho_probe),
    )
    commuting_gaps = Dict{String,Any}(
        "r1_r2" => order_gap(COMMUTING_FILTERS[1], COMMUTING_FILTERS[2], rho_probe),
        "r2_r3" => order_gap(COMMUTING_FILTERS[2], COMMUTING_FILTERS[3], rho_probe),
    )
    smt = smt_report(rho_probe)
    negative_crossings = [r for r in 1:3 if conditional[r] < -TOL]
    class_counts = [Int(quotients["M_$(r)"]["distinguishable_class_count"]) for r in 1:3]
    source_deps = Dict{String,Any}(replace(path, ROOT * "/" => "") => file_sha256(path) for path in SOURCE_DEPENDENCIES)
    shared_scalars = Dict{String,Any}(
        "conditional_entropy_r1" => conditional[1],
        "conditional_entropy_r2" => conditional[2],
        "conditional_entropy_r3" => conditional[3],
        "signed_cut_Ic_r1" => signed_cut[1],
        "signed_cut_Ic_r2" => signed_cut[2],
        "signed_cut_Ic_r3" => signed_cut[3],
        "separable_conditional_entropy_r1" => sep_conditional[1],
        "separable_conditional_entropy_r2" => sep_conditional[2],
        "separable_conditional_entropy_r3" => sep_conditional[3],
        "carrier_S_AB_r1" => carrier_components[1]["S_AB"],
        "carrier_S_AB_r2" => carrier_components[2]["S_AB"],
        "carrier_S_AB_r3" => carrier_components[3]["S_AB"],
        "carrier_S_B_r1" => carrier_components[1]["S_B"],
        "carrier_S_B_r2" => carrier_components[2]["S_B"],
        "carrier_S_B_r3" => carrier_components[3]["S_B"],
        "separable_control_S_AB_r1" => sep_components[1]["S_AB"],
        "separable_control_S_AB_r2" => sep_components[2]["S_AB"],
        "separable_control_S_AB_r3" => sep_components[3]["S_AB"],
        "separable_control_S_B_r1" => sep_components[1]["S_B"],
        "separable_control_S_B_r2" => sep_components[2]["S_B"],
        "separable_control_S_B_r3" => sep_components[3]["S_B"],
        "order_gap_r1_r2" => gaps["r1_r2"],
        "order_gap_r2_r3" => gaps["r2_r3"],
        "commuting_order_gap_r1_r2" => commuting_gaps["r1_r2"],
        "commuting_order_gap_r2_r3" => commuting_gaps["r2_r3"],
        "quotient_class_count_M1" => Float64(class_counts[1]),
        "quotient_class_count_M2" => Float64(class_counts[2]),
        "quotient_class_count_M3" => Float64(class_counts[3]),
        "negative_crossing_rung" => Float64(isempty(negative_crossings) ? 0 : negative_crossings[1]),
        "boundary_rung1_conditional_entropy" => conditional[1],
    )
    controls = Dict{String,Any}(
        "separable_nonnegative_every_rung" => all(value >= -TOL for value in values(sep_conditional)),
        "commuting_control_zero_order_gap" => all(Float64(value) <= TOL for value in values(commuting_gaps)),
        "commuting_control_classification" => "not_a_ratchet_zero_order_gap",
        "boundary_rung_count_1_no_signed_cut_crossing" => conditional[1] >= -TOL,
        "carrier_conditional_entropy_strictly_decreases" => conditional[1] > conditional[2] > conditional[3],
        "carrier_crosses_negative" => !isempty(negative_crossings),
        "order_gap_nonzero_every_adjacent_pair" => all(Float64(value) > TOL for value in values(gaps)),
        "quotient_tightens" => class_counts[1] < class_counts[2] && class_counts[2] <= class_counts[3],
        "julia_z3_filter_level_noncommuting_unsat" => smt["rung2_adjacent_pair"]["filter_level"]["z3"]["verdict"] == "unsat",
        "julia_z3_filter_level_commuting_control_sat" => smt["commuting_control"]["filter_level"]["z3"]["verdict"] == "sat",
        "julia_z3_channel_level_noncommuting_unsat" => smt["rung2_adjacent_pair"]["channel_level"]["z3"]["verdict"] == "unsat",
        "julia_z3_channel_level_commuting_control_sat" => smt["commuting_control"]["channel_level"]["z3"]["verdict"] == "sat",
    )
    rungs = Vector{Dict{String,Any}}()
    for rung in 1:3
        stack = stack_state(rung, rhos[rung], K_FILTERS)
        push!(rungs, Dict{String,Any}(
            "rung" => rung,
            "eta" => ETA_SHELLS[rung],
            "theta" => theta(rung),
            "probe_family" => probe_family(rung),
            "density" => density_diagnostics(rhos[rung]),
            "stacked_density" => density_diagnostics(stack),
            "conditional_entropy_S_A_given_B" => conditional[rung],
            "entropy_components" => carrier_components[rung],
            "signed_cut_Ic" => signed_cut[rung],
            "separable_control_S_A_given_B" => sep_conditional[rung],
            "separable_control_entropy_components" => sep_components[rung],
            "density_quotient" => quotients["M_$(rung)"],
        ))
    end
    all_pass = all(Bool(density_diagnostics(rhos[r])["psd"]) for r in 1:3) &&
        all(Bool(value) for value in values(controls) if value isa Bool) &&
        READS_PEER_RESULT == false &&
        CLASSIFICATION == "scratch_diagnostic" &&
        PROMOTION_ALLOWED == false &&
        FORMAL_ADMISSION_ALLOWED == false
    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "schema_version" => "three_engine_sim_result_v1",
        "engine_contract" => Dict("mode" => "all_three_full_sims", "reads_peer_result" => false),
        "object_id" => OBJECT_ID,
        "engine" => ENGINE,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "source_dependencies" => source_deps,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["QuantumOptics", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "control_only_tools" => String[],
        "rungs" => rungs,
        "quotient" => quotients,
        "signed_cut" => Dict{String,Any}(
            "cut" => "Weyl-L sheet | Weyl-R sheet",
            "log_base" => "e",
            "conditional_entropy_by_rung" => Dict(string(k) => v for (k, v) in conditional),
            "signed_cut_Ic_by_rung" => Dict(string(k) => v for (k, v) in signed_cut),
            "headline_claim_under_test" => "S(A|B) decreases monotonically and goes negative once nesting forces L/R entanglement",
        ),
        "order_gaps" => gaps,
        "controls" => controls,
        "negative_controls" => Dict{String,Any}(
            "separable" => Dict(string(k) => v for (k, v) in sep_conditional),
            "commuting" => commuting_gaps,
            "boundary" => Dict("rung_count" => 1, "conditional_entropy" => conditional[1], "crosses_negative" => conditional[1] < -TOL),
        ),
        "smt" => smt,
        "crossover_proofs" => Dict{String,Any}(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "verdict" => smt["rung2_adjacent_pair"]["z3"]["verdict"],
                "commuting_control_verdict" => smt["commuting_control"]["z3"]["verdict"],
                "filter_level" => smt["rung2_adjacent_pair"]["filter_level"]["z3"],
                "channel_level" => smt["rung2_adjacent_pair"]["channel_level"]["z3"],
                "commuting_control_filter_level" => smt["commuting_control"]["filter_level"]["z3"],
                "commuting_control_channel_level" => smt["commuting_control"]["channel_level"]["z3"],
                "claim" => "Z3.jl binds rung-2 adjacent filters and scaled rho_probe entries, derives channel-level noncommutation because forcing unnormalized Phi_a(Phi_b(rho_probe)) == Phi_b(Phi_a(rho_probe)) is UNSAT",
            ),
        ),
        "shared_scalars" => shared_scalars,
        "shared_observable_keys" => sort(collect(keys(shared_scalars))),
        "all_pass" => all_pass,
        "claim_ceiling" => "scratch_diagnostic only; promotion_allowed=false; formal_admission_allowed=false; no bridge, Axis0, manifold, or M(C) closure.",
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    s = result["shared_scalars"]
    println("wrote: ", RESULT_PATH)
    println("FOUNDATION_NESTED_HOPF_WEYL_SIGNED_CUT_RATCHET_JULIA_DONE all_pass=", result["all_pass"],
        " S=[", s["conditional_entropy_r1"], ",", s["conditional_entropy_r2"], ",", s["conditional_entropy_r3"], "]",
        " gaps=[", s["order_gap_r1_r2"], ",", s["order_gap_r2_r3"], "]",
        " julia_z3=", result["crossover_proofs"]["julia_z3"]["verdict"])
    return result["all_pass"] ? 0 : 2
end

exit(main())
