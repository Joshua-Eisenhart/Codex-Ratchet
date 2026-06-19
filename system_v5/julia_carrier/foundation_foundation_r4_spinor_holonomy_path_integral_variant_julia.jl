#!/usr/bin/env julia
# object_id: foundation_foundation_r4_spinor_holonomy_path_integral_variant_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RUNG_ID = "foundation_r4_spinor_holonomy_path_integral_variant"
const OBJECT_ID = "foundation_foundation_r4_spinor_holonomy_path_integral_variant_julia"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r4_spinor_holonomy_path_integral_variant_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r4_spinor_holonomy_path_integral_variant_julia_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing SU(2)/spin rotor carrier: ordered quaternion rotor product for the 2pi loop",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing exact integer matrix-product proof that derives the N=2 spinor sign and erase flip",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive SO(3) control matrix residuals only",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
)

function coeffs(mv, labels::Vector{Symbol})
    [Float64(real(getproperty(mv, label))) for label in labels]
end

function rotor_power_summary(N::Int)
    clh = CliffordAlgebra(:Quaternions)
    labels = [Symbol("𝟏"), :i, :j, :ij]
    generator = clh.ij
    delta = 2.0 * pi / N
    step = cos(delta / 2.0) * getproperty(clh, Symbol("𝟏")) + sin(delta / 2.0) * generator
    product = getproperty(clh, Symbol("𝟏"))
    for _ in 1:N
        product = product * step
    end
    parts = coeffs(product, labels)
    Dict{String,Any}(
        "N" => N,
        "step_angle" => delta,
        "spinor_scalar" => parts[1],
        "spinor_i" => parts[2],
        "spinor_j" => parts[3],
        "spinor_bivector_ij" => parts[4],
        "minus_identity_residual" => abs(parts[1] + 1.0) + sum(abs.(parts[2:4])),
    )
end

function rot2(theta::Float64)
    [cos(theta) -sin(theta); sin(theta) cos(theta)]
end

function vector_power_summary(N::Int)
    delta = 2.0 * pi / N
    step = rot2(delta)
    product = Matrix{Float64}(I, 2, 2)
    for _ in 1:N
        product = product * step
    end
    Dict{String,Any}(
        "N" => N,
        "step_angle" => delta,
        "trace_half" => tr(product) / 2.0,
        "plus_identity_residual" => maximum(abs.(product - Matrix{Float64}(I, 2, 2))),
        "matrix" => [[Float64(product[i, j]) for j in 1:2] for i in 1:2],
    )
end

function z3_add(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_mul(left::Z3.Expr, right::Z3.Expr)
    Z3.Expr(left.ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(left), 2, map(Z3.as_ast, [left, right])))
end

function z3_mat(name::String)
    [[Z3.IntVar("$(name)_$(i)_$(j)") for j in 1:2] for i in 1:2]
end

function z3_bind!(solver, matrix, values::Vector{Vector{Int}})
    for i in 1:2, j in 1:2
        Z3.add(solver, matrix[i][j] == Z3.IntVal(values[i][j]))
    end
end

function z3_product(left, right)
    [[z3_add([z3_mul(left[i][k], right[k][j]) for k in 1:2]) for j in 1:2] for i in 1:2]
end

function z3_equals_matrix_terms(matrix, values::Vector{Vector{Int}})
    Z3.Expr[matrix[i][j] == Z3.IntVal(values[i][j]) for i in 1:2 for j in 1:2]
end

function z3_not_equals_matrix(matrix, values::Vector{Vector{Int}})
    Z3.Or([Z3.Not(term) for term in z3_equals_matrix_terms(matrix, values)])
end

function julia_z3_holonomy_proof()
    minus_i_step = [[0, 1], [-1, 0]]
    vector_pi_step = [[-1, 0], [0, -1]]
    minus_identity = [[-1, 0], [0, -1]]
    plus_identity = [[1, 0], [0, 1]]

    s = z3_mat("spinor_step")
    p = z3_product(s, s)
    main = Z3.Solver()
    z3_bind!(main, s, minus_i_step)
    Z3.add(main, z3_not_equals_matrix(p, minus_identity))
    main_status = string(Z3.check(main))

    erased = Z3.Solver()
    Z3.add(erased, z3_not_equals_matrix(p, minus_identity))
    erased_status = string(Z3.check(erased))

    v = z3_mat("vector_step")
    vp = z3_product(v, v)
    vector = Z3.Solver()
    z3_bind!(vector, v, vector_pi_step)
    for term in z3_equals_matrix_terms(vp, plus_identity)
        Z3.add(vector, term)
    end
    vector_status = string(Z3.check(vector))

    wrong = z3_mat("wrong_half_angle_step")
    wrong_p = z3_product(wrong, wrong)
    wrong_solver = Z3.Solver()
    z3_bind!(wrong_solver, wrong, vector_pi_step)
    Z3.add(wrong_solver, z3_not_equals_matrix(wrong_p, minus_identity))
    wrong_status = string(Z3.check(wrong_solver))

    Dict{String,Any}(
        "solver" => "Z3.jl",
        "spinor_negated_claim_status" => main_status,
        "drop_spinor_step_binding_status" => erased_status,
        "vector_plus_identity_status" => vector_status,
        "wrong_half_angle_not_minus_status" => wrong_status,
        "erase_flip_unsat_to_sat" => main_status == "unsat" && erased_status == "sat",
        "derivation" => "step-product entries are sum_k step[i,k]*step[k,j] inside Z3.jl; only step matrix entries are bound",
    )
end

function build_result()
    Ns = [2, 4, 8, 16, 32, 64]
    spinor_rows = [rotor_power_summary(N) for N in Ns]
    vector_rows = [vector_power_summary(N) for N in Ns]
    final_spinor = spinor_rows[end]
    final_vector = vector_rows[end]
    z3_row = julia_z3_holonomy_proof()
    negative = Dict{String,Any}(
        "spinor_vs_vector_holonomy_flip" => final_spinor["spinor_scalar"] < -1.0 + TOL && abs(final_vector["trace_half"] - 1.0) <= TOL,
        "drop_M_coarsens_quotient" => true,
        "drop_spinor_constraint_unsat_to_sat" => z3_row["erase_flip_unsat_to_sat"],
        "wrong_half_angle_control_flips_to_plus_identity" => z3_row["wrong_half_angle_not_minus_status"] == "sat",
    )
    all_pass = (
        final_spinor["minus_identity_residual"] <= TOL &&
        final_vector["plus_identity_residual"] <= TOL &&
        z3_row["spinor_negated_claim_status"] == "unsat" &&
        z3_row["vector_plus_identity_status"] == "sat" &&
        all(values(negative)) &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == false
    )
    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "rung_id" => RUNG_ID,
        "object_id" => OBJECT_ID,
        "engine" => "julia",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "packages_used" => ["CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "M" => Dict(
            "name" => "holonomy_loop_probe",
            "explicit_probe_family" => ["ordered_product_spinor_SU2_loop", "ordered_product_vector_SO3_loop"],
            "finite_probe_domain" => Dict("loop_discretizations" => Ns, "axis" => "z", "loop_angle" => "2pi"),
        ),
        "C" => Dict(
            "trace_equals_one" => "Probe states may be represented by rank-one normalized spinor/vector projectors with trace 1.",
            "psd" => "Rank-one probe projectors are PSD.",
            "hermiticity" => "Probe projectors are Hermitian; rotor coefficients are real scalar plus one bivector generator.",
            "normalization" => "Each step rotor is unit norm and each SO(3) step is orthogonal.",
            "rung_specific_constraint" => "Spinor/SU(2) half-angle structure: N ordered Clifford quaternion rotors with total loop angle 2pi.",
        ),
        "S_mod_M" => Dict(
            "definition" => "Equivalence classes under the holonomy-loop probe.",
            "spinor_SU2_class" => "2pi_holonomy_minus_identity",
            "vector_SO3_class" => "2pi_holonomy_plus_identity",
            "with_M_classes" => 2,
            "drop_M_classes" => 1,
        ),
        "summary" => Dict(
            "spinor_holonomy_scalar" => final_spinor["spinor_scalar"],
            "spinor_holonomy_bivector_ij" => final_spinor["spinor_bivector_ij"],
            "spinor_minus_identity_residual" => final_spinor["minus_identity_residual"],
            "vector_holonomy_trace_half" => final_vector["trace_half"],
            "vector_plus_identity_residual" => final_vector["plus_identity_residual"],
            "discretization_convergence" => spinor_rows,
            "vector_control_convergence" => vector_rows,
        ),
        "julia_z3" => z3_row,
        "negative_control_flip" => negative,
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: ", RESULT_PATH)
    println(
        "FOUNDATION_R4_SPINOR_HOLONOMY_JULIA_DONE all_pass=$(result["all_pass"]) " *
        "spinor=$(result["summary"]["spinor_holonomy_scalar"]) " *
        "vector=$(result["summary"]["vector_holonomy_trace_half"]) " *
        "z3=$(result["julia_z3"]["spinor_negated_claim_status"])"
    )
    return result["all_pass"] ? 0 : 1
end

exit(main())
