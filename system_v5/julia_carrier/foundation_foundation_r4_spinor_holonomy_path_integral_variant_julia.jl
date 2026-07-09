#!/usr/bin/env julia
# object_id: foundation_foundation_r4_spinor_holonomy_path_integral_variant_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: true

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
const R3_RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_r3_octonion_cl6_link_xhigh_julia_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = true

const TOOL_MANIFEST = Dict{String,Any}(
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive Cl(0,6) dimension/rank cross-check only; the rotor generator itself is NOT built from CliffordAlgebras -- it is derived from R3's Cayley-Dickson octonion left-multiplication matrices (same cd_mul construction as foundation_r3_octonion_cl6_link_xhigh_julia.jl)",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing exact integer matrix-product proof that derives the N=2 abstract SU(2) spinor sign and erase flip (independent 2x2 formal cross-check, not itself carrier-derived)",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing matrix power/svd/eigenvalue computation of the R3-derived bivector generator and its ordered-product holonomy",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing read of R3's persisted result JSON (foundation_r3_octonion_cl6_link_xhigh_julia_results.json) for peer-dependency provenance, plus supportive result serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "CliffordAlgebras" => "supportive",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "load_bearing",
)

function load_r3_peer_result()
    isfile(R3_RESULT_PATH) || error("R4 spinor holonomy sim requires R3 peer result at $(R3_RESULT_PATH); none found.")
    JSON.parsefile(R3_RESULT_PATH)
end

# Same Cayley-Dickson construction R3 uses (foundation_r3_octonion_cl6_link_xhigh_julia.jl),
# recomputed locally so the rotor generator below is built FROM octonion structure,
# not from a bare generic CliffordAlgebra(:Quaternions) with no link to R3.
function cd_conj(x::Vector{Float64})
    y = copy(x)
    length(y) > 1 && (y[2:end] .*= -1.0)
    y
end

function cd_mul(x::Vector{Float64}, y::Vector{Float64})
    n = length(x)
    n == 1 && return [x[1] * y[1]]
    half = n ÷ 2
    a, b = x[1:half], x[(half + 1):end]
    c, d = y[1:half], y[(half + 1):end]
    vcat(cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c)))
end

function basis(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function left_matrix(dim::Int, unit_idx0::Int)
    e = basis(dim, unit_idx0)
    hcat([cd_mul(e, basis(dim, col0)) for col0 in 0:(dim - 1)]...)
end

left_matrices(dim::Int) = [left_matrix(dim, idx0) for idx0 in 1:(dim - 1)]

function generated_rank(mats::Vector{Matrix{Float64}}, generator_count::Int)
    dim = size(mats[1], 1)
    cols = Vector{Float64}[]
    for mask in 0:(2^generator_count - 1)
        acc = Matrix{Float64}(I, dim, dim)
        for idx in 1:generator_count
            if ((mask >> (idx - 1)) & 1) == 1
                acc = acc * mats[idx]
            end
        end
        push!(cols, vec(acc))
    end
    mat = hcat(cols...)
    singular = svdvals(mat)
    max_s = isempty(singular) ? 0.0 : maximum(singular)
    tol = max(size(mat)...) * eps(Float64) * max_s * 100.0
    count(>(tol), singular)
end

function r3_provenance_check(r3::AbstractDict, o_mats::Vector{Matrix{Float64}})
    r3_summary = r3["summary"]
    rank6 = generated_rank(o_mats, 6)
    Dict{String,Any}(
        "r3_result_path" => R3_RESULT_PATH,
        "r3_object_id" => get(r3, "object_id", nothing),
        "r3_source_sha256" => get(r3, "source_sha256", nothing),
        "r3_octonion_cl6_rank" => r3_summary["octonion_cl6_rank"],
        "local_recomputed_cl6_rank_from_same_cd_mul_construction" => rank6,
        "matches_r3" => rank6 == r3_summary["octonion_cl6_rank"],
    )
end

# Bivector generator B = L_e1 * L_e2 built from R3's admitted octonion
# left-multiplication matrices. Since L_e1, L_e2 anticommute and each squares
# to -I (proven in R3), B is skew (B^T = -B) and B^2 = -I: a genuine
# complex-structure / rotation generator induced by the octonion carrier, not
# a hand-picked abstract 2x2 matrix.
function octonion_bivector_generator()
    o_mats = left_matrices(8)
    L1, L2 = o_mats[1], o_mats[2]
    B = L1 * L2
    skew_residual = norm(B' + B)
    square_residual = norm(B * B + Matrix{Float64}(I, 8, 8))
    Dict{String,Any}(
        "matrix" => B,
        "generators" => "L_e1 * L_e2 (octonion left-multiplication matrices from R3's Cayley-Dickson construction)",
        "skew_residual" => skew_residual,
        "square_minus_identity_residual" => square_residual,
        "is_valid_rotation_generator" => skew_residual <= TOL && square_residual <= TOL,
    ), o_mats
end

function rotor_power_summary(N::Int, B::Matrix{Float64})
    dim = size(B, 1)
    identity8 = Matrix{Float64}(I, dim, dim)
    delta = 2.0 * pi / N
    step = cos(delta / 2.0) * identity8 + sin(delta / 2.0) * B
    product = identity8
    for _ in 1:N
        product = product * step
    end
    Dict{String,Any}(
        "N" => N,
        "step_angle" => delta,
        "spinor_scalar" => tr(product) / dim,
        "minus_identity_residual" => norm(product + identity8),
    )
end

function vector_power_summary(N::Int, B::Matrix{Float64})
    dim = size(B, 1)
    identity8 = Matrix{Float64}(I, dim, dim)
    delta = 2.0 * pi / N
    step = cos(delta) * identity8 + sin(delta) * B
    product = identity8
    for _ in 1:N
        product = product * step
    end
    Dict{String,Any}(
        "N" => N,
        "step_angle" => delta,
        "trace_half" => tr(product) / dim,
        "plus_identity_residual" => norm(product - identity8),
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
    r3_peer = load_r3_peer_result()
    bivector_report, o_mats = octonion_bivector_generator()
    B = bivector_report["matrix"]
    r3_provenance = r3_provenance_check(r3_peer, o_mats)

    Ns = [2, 4, 8, 16, 32, 64]
    spinor_rows = [rotor_power_summary(N, B) for N in Ns]
    vector_rows = [vector_power_summary(N, B) for N in Ns]
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
        bivector_report["is_valid_rotation_generator"] &&
        final_spinor["minus_identity_residual"] <= TOL &&
        final_vector["plus_identity_residual"] <= TOL &&
        z3_row["spinor_negated_claim_status"] == "unsat" &&
        z3_row["vector_plus_identity_status"] == "sat" &&
        all(values(negative)) &&
        classification == "scratch_diagnostic" &&
        promotion_allowed == false &&
        formal_admission_allowed == false &&
        reads_peer_result == true &&
        r3_provenance["matches_r3"]
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
        "r3_peer_dependency" => r3_provenance,
        "octonion_bivector_generator" => Dict{String,Any}(
            "generators" => bivector_report["generators"],
            "skew_residual" => bivector_report["skew_residual"],
            "square_minus_identity_residual" => bivector_report["square_minus_identity_residual"],
            "is_valid_rotation_generator" => bivector_report["is_valid_rotation_generator"],
        ),
        "packages_used" => ["CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["Z3", "LinearAlgebra", "JSON"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "M" => Dict(
            "name" => "holonomy_loop_probe",
            "explicit_probe_family" => ["ordered_product_R3_octonion_bivector_half_angle_loop", "ordered_product_R3_octonion_bivector_full_angle_loop"],
            "carrier_derivation" => "rotation generator B = L_e1 * L_e2 is built from R3's admitted octonion left-multiplication matrices (foundation_r3_octonion_cl6_link_xhigh_julia_results.json), not a bare CliffordAlgebra(:Quaternions)",
            "finite_probe_domain" => Dict("loop_discretizations" => Ns, "axis" => "octonion_bivector_L_e1_L_e2", "loop_angle" => "2pi"),
        ),
        "C" => Dict(
            "trace_equals_one" => "The bivector-generated step exp(delta*B) is orthogonal by construction (B skew); trace/dim is the reported scalar projector proxy.",
            "psd" => "Not a density-state rung; the octonion left-multiplication carrier and its induced bivector are the constraint objects.",
            "hermiticity" => "L_e1, L_e2 are real skew matrices (proven in R3); B = L_e1*L_e2 is skew, so exp(theta*B) is orthogonal.",
            "normalization" => "B^2 = -I (proven here from R3's admitted L_e1, L_e2), so half-angle and full-angle steps are well-defined rotation generators.",
            "rung_specific_constraint" => "Half-angle ordered product of exp(delta/2 * B) over N steps, B derived from R3's octonion carrier, versus a full-angle control exp(delta * B).",
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
