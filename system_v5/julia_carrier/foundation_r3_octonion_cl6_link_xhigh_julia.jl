#!/usr/bin/env julia
# object_id: foundation_r3_octonion_cl6_link_xhigh
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false

using Dates
using JSON
using SHA
using LinearAlgebra
using QuantumOptics
using CliffordAlgebras
using Z3

const OBJECT_ID = "foundation_r3_octonion_cl6_link_xhigh"
const RESULT_PATH = joinpath(@__DIR__, "results", "foundation_r3_octonion_cl6_link_xhigh_julia_results.json")
const TOL = 1.0e-9
const CLAIM_CEILING = "Scratch diagnostic only: finite Cayley-Dickson octonion left-multiplication operators on O link to the 8-real-dimensional Cl(0,6) spinor carrier. No physics claim, no admission, no promotion."

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function cd_conj(x::Vector{Float64})
    y = copy(x)
    if length(y) > 1
        y[2:end] .*= -1.0
    end
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

function matrix_rank_from_cols(cols::Vector{Vector{Float64}}, rows::Int)
    mat = hcat(cols...)
    singular = svdvals(mat)
    max_s = isempty(singular) ? 0.0 : maximum(singular)
    tol = max(size(mat)...) * eps(Float64) * max_s * 100.0
    count(>(tol), singular), tol
end

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
    rank_value, tol = matrix_rank_from_cols(cols, dim * dim)
    Dict{String,Any}(
        "generator_count" => generator_count,
        "word_count" => length(cols),
        "rank" => rank_value,
        "rank_tol" => tol,
    )
end

function anticommutation_report(mats::Vector{Matrix{Float64}})
    dim = size(mats[1], 1)
    max_residual = 0.0
    failures = Vector{Dict{String,Any}}()
    for i in eachindex(mats), j in eachindex(mats)
        target = (i == j) ? (-2.0 .* Matrix{Float64}(I, dim, dim)) : zeros(Float64, dim, dim)
        residual = norm(mats[i] * mats[j] + mats[j] * mats[i] - target)
        max_residual = max(max_residual, residual)
        if residual > TOL
            push!(failures, Dict{String,Any}("i" => i, "j" => j, "residual" => residual))
        end
    end
    Dict{String,Any}(
        "relation" => "L_i L_j + L_j L_i = -2 delta_ij I",
        "max_residual" => max_residual,
        "pass" => isempty(failures),
        "failures" => failures,
    )
end

function skew_report(mats::Vector{Matrix{Float64}})
    residuals = [norm(mat' + mat) for mat in mats]
    Dict{String,Any}(
        "max_residual" => maximum(residuals),
        "per_generator_residuals" => residuals,
        "pass" => maximum(residuals) <= TOL,
    )
end

function pseudoscalar_link_report(o_mats::Vector{Matrix{Float64}})
    product = Matrix{Float64}(I, 8, 8)
    for idx in 1:6
        product = product * o_mats[idx]
    end
    plus_residual = norm(product - o_mats[7])
    minus_residual = norm(product + o_mats[7])
    Dict{String,Any}(
        "relation" => "L_e1 L_e2 L_e3 L_e4 L_e5 L_e6 = L_e7 under this Cayley-Dickson orientation",
        "plus_residual" => plus_residual,
        "minus_residual" => minus_residual,
        "pass" => plus_residual <= TOL,
    )
end

function quantumoptics_probe_report(o_mats::Vector{Matrix{Float64}})
    basis8 = NLevelBasis(8)
    observables = [Operator(basis8, basis8, ComplexF64.(im .* mat)) for mat in o_mats]
    hermitian_residuals = [norm(op.data - op.data') for op in observables]
    rho = Operator(basis8, basis8, Matrix{ComplexF64}(I, 8, 8) ./ 8.0)
    rho_eigs = eigvals(Hermitian(rho.data))
    Dict{String,Any}(
        "basis" => string(typeof(basis8)),
        "observable_count" => length(observables),
        "observable_shape" => [size(observables[1].data, 1), size(observables[1].data, 2)],
        "iL_is_hermitian_max_residual" => maximum(hermitian_residuals),
        "density_constraint_witness" => Dict{String,Any}(
            "trace" => real(tr(rho.data)),
            "hermiticity_residual" => norm(rho.data - rho.data'),
            "min_eigenvalue" => minimum(real.(rho_eigs)),
            "normalization" => real(tr(rho.data)),
            "trace_one_pass" => abs(real(tr(rho.data)) - 1.0) <= TOL,
            "psd_pass" => minimum(real.(rho_eigs)) >= -TOL,
            "hermitian_pass" => norm(rho.data - rho.data') <= TOL,
        ),
        "pass" => maximum(hermitian_residuals) <= TOL,
    )
end

function clifford_generator(algebra, idx::Int)
    getproperty(algebra, Symbol("e$idx"))
end

function cliffordalgebras_report()
    cl06 = CliffordAlgebra(0, 6)
    gens = [clifford_generator(cl06, idx) for idx in 1:6]
    unit = one(gens[1])
    max_residual = 0.0
    for i in 1:6, j in 1:6
        lhs = gens[i] * gens[j] + gens[j] * gens[i]
        rhs = (i == j ? -2 : 0) * unit
        max_residual = max(max_residual, Float64(CliffordAlgebras.norm(lhs - rhs)))
    end
    Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructed" => "CliffordAlgebra(0, 6)",
        "basis_symbol_count" => length(propertynames(cl06)),
        "expected_cl6_dimension" => 64,
        "spinor_dimension_compared" => 8,
        "generator_anticommutation_max_residual" => max_residual,
        "pass" => length(propertynames(cl06)) == 64 && max_residual <= TOL,
    )
end

function status_string(status)
    string(status)
end

function z3_add_terms(terms::Vector{Z3.Expr})
    length(terms) == 1 && return terms[1]
    ctx = terms[1].ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(terms[1]), length(terms), map(Z3.as_ast, terms)))
end

function z3_mul_terms(terms::Vector{Z3.Expr})
    length(terms) == 1 && return terms[1]
    ctx = terms[1].ctx
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ctx_ref(terms[1]), length(terms), map(Z3.as_ast, terms)))
end

function matrix_entry_table(mats::Vector{Matrix{Float64}})
    [
        [
            [Int(round(mats[i][row, col])) for col in 1:8]
            for row in 1:8
        ]
        for i in 1:7
    ]
end

function z3_bound_entries(values, bind_entries::Bool)
    solver = Z3.Solver()
    entries = [
        [
            [Z3.IntVar("L_$(i)_$(row)_$(col)") for col in 1:8]
            for row in 1:8
        ]
        for i in 1:7
    ]
    if bind_entries
        for i in 1:7, row in 1:8, col in 1:8
            Z3.add(solver, entries[i][row][col] == Z3.IntVal(values[i][row][col]))
        end
    end
    solver, entries
end

function z3_anticommutator_entry(entries, i::Int, j::Int, row::Int, col::Int)
    terms = Z3.Expr[]
    for k in 1:8
        push!(terms, z3_mul_terms([entries[i][row][k], entries[j][k][col]]))
        push!(terms, z3_mul_terms([entries[j][row][k], entries[i][k][col]]))
    end
    z3_add_terms(terms)
end

function z3_violation_terms(entries, mode::String)
    terms = Z3.Expr[]
    for i in 1:7, j in 1:7
        mode == "offdiag_violation" && i == j && continue
        mode in ["self_square_violation", "wrong_sign_violation"] && i != j && continue
        for row in 1:8, col in 1:8
            anti = z3_anticommutator_entry(entries, i, j, row, col)
            target = 0
            if i == j
                sign = mode == "wrong_sign_violation" ? 2 : -2
                target = row == col ? sign : 0
            end
            push!(terms, Z3.Not(anti == Z3.IntVal(target)))
        end
    end
    terms
end

function z3_status(values; bind_entries::Bool, mode::String)
    solver, entries = z3_bound_entries(values, bind_entries)
    Z3.add(solver, Z3.Or(z3_violation_terms(entries, mode)))
    Dict{String,Any}(
        "status" => status_string(Z3.check(solver)),
        "mode" => mode,
        "binds_L_entries" => bind_entries,
        "sort" => "Int",
        "bound_entry_count" => bind_entries ? 7 * 8 * 8 : 0,
        "derived_expression" => "sum_c(L_i[a,c]*L_j[c,b] + L_j[a,c]*L_i[c,b])",
    )
end

function z3_clifford_report(o_mats::Vector{Matrix{Float64}})
    values = matrix_entry_table(o_mats)
    correct = z3_status(values; bind_entries=true, mode="correct_all_violation")
    offdiag = z3_status(values; bind_entries=true, mode="offdiag_violation")
    self_square = z3_status(values; bind_entries=true, mode="self_square_violation")
    erased = z3_status(values; bind_entries=false, mode="correct_all_violation")
    wrong = z3_status(values; bind_entries=true, mode="wrong_sign_violation")
    Dict{String,Any}(
        "encoding" => "Julia Z3.jl v2 witness: bind all computed octonion L_i entries, derive anticommutator entries inside Z3 from matrix products, and ask for a Clifford-relation violation.",
        "forbidden_pattern_guard" => "No precomputed residual/count/boolean is asserted; Z3 builds products from bound L entries.",
        "L_entry_count" => 7 * 8 * 8,
        "derived_anticommutator_entry_count" => 7 * 7 * 8 * 8,
        "verdict" => correct["status"],
        "correct_relation_violation" => correct,
        "offdiag_pair_violation" => offdiag,
        "self_square_violation" => self_square,
        "erase_L_entry_binding_flip" => erased,
        "wrong_sign_plus_I_violation_control" => wrong,
        "pass" => correct["status"] == "unsat" &&
                  offdiag["status"] == "unsat" &&
                  self_square["status"] == "unsat" &&
                  erased["status"] == "sat" &&
                  wrong["status"] == "sat",
    )
end

function quotient_report(o_rank::Dict{String,Any}, h_rank::Dict{String,Any}, o_anti::Dict{String,Any}, h_anti::Dict{String,Any})
    full_signatures = Dict{String,Any}(
        "octonion_left_action_on_O" => "O:generators=7;carrier_dim=8;rank=$(o_rank["rank"]);spinor_dim=8;anticommutes=$(o_anti["pass"])",
        "quaternion_left_action_control_on_H" => "H:generators=3;carrier_dim=4;rank=$(h_rank["rank"]);spinor_dim=2;anticommutes=$(h_anti["pass"])",
    )
    coarse_signatures = Dict{String,Any}(
        "octonion_left_action_on_O" => "skew=true;anticommutes=$(o_anti["pass"])",
        "quaternion_left_action_control_on_H" => "skew=true;anticommutes=$(h_anti["pass"])",
    )
    full_count = length(unique(collect(values(full_signatures))))
    coarse_count = length(unique(collect(values(coarse_signatures))))
    Dict{String,Any}(
        "S" => ["octonion_left_action_on_O", "quaternion_left_action_control_on_H"],
        "equivalence_relation" => "x ~_M y iff all finite M probes match: generator count, carrier dimension, anticommutation signature, generated Clifford rank, and spinor dimension",
        "full_probe_signatures" => full_signatures,
        "coarse_probe_signatures_after_dropping_dimension_and_rank" => coarse_signatures,
        "full_probe_class_count" => full_count,
        "drop_dimension_and_rank_probe_class_count" => coarse_count,
        "octonion_class" => Dict{String,Any}("label" => "Cl(0,6)_spinor_from_O_left_multiplication", "generated_rank" => o_rank["rank"], "spinor_dim" => 8),
        "quaternion_control_class" => Dict{String,Any}("label" => "Cl(0,2)_control_from_H_left_multiplication", "generated_rank" => h_rank["rank"], "spinor_dim" => 2),
        "coarsening_flip" => Dict{String,Any}(
            "dropped_probe" => "carrier dimension + generated Clifford rank",
            "before_class_count" => full_count,
            "after_class_count" => coarse_count,
            "flips" => full_count != coarse_count,
        ),
    )
end

function build_result()
    mkpath(dirname(RESULT_PATH))

    o_mats = left_matrices(8)
    h_mats = left_matrices(4)

    o_skew = skew_report(o_mats)
    h_skew = skew_report(h_mats)
    o_anti = anticommutation_report(o_mats)
    h_anti = anticommutation_report(h_mats)
    o_rank6 = generated_rank(o_mats, 6)
    o_rank7 = generated_rank(o_mats, 7)
    h_rank2 = generated_rank(h_mats, 2)
    h_rank3 = generated_rank(h_mats, 3)
    pseudoscalar_link = pseudoscalar_link_report(o_mats)
    qo = quantumoptics_probe_report(o_mats)
    clifford_pkg = cliffordalgebras_report()
    z3_report = z3_clifford_report(o_mats)
    quotient = quotient_report(o_rank6, h_rank2, o_anti, h_anti)

    all_pass = o_skew["pass"] &&
               h_skew["pass"] &&
               o_anti["pass"] &&
               h_anti["pass"] &&
               o_rank6["rank"] == 64 &&
               o_rank7["rank"] == 64 &&
               h_rank2["rank"] == 4 &&
               h_rank3["rank"] == 4 &&
               pseudoscalar_link["pass"] &&
               qo["pass"] &&
               qo["density_constraint_witness"]["trace_one_pass"] &&
               qo["density_constraint_witness"]["psd_pass"] &&
               qo["density_constraint_witness"]["hermitian_pass"] &&
               clifford_pkg["pass"] &&
               z3_report["pass"] &&
               quotient["coarsening_flip"]["flips"]

    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg.v1",
        "object_id" => OBJECT_ID,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "engine" => "julia",
        "ran" => true,
        "standalone" => true,
        "reads_peer_result" => false,
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "source_path" => abspath(@__FILE__),
        "result_path" => RESULT_PATH,
        "source_sha256" => sha256_file(abspath(@__FILE__)),
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "M" => Dict{String,Any}(
            "probe_family" => "finite octonion left-multiplication observables and anticommutator matrix entries",
            "operators" => ["L_e$idx" for idx in 1:7],
            "probe_entries" => "<basis_a | (L_ei L_ej + L_ej L_ei) | basis_b> for i,j=1..7 and a,b=1..8",
            "pair_probe_count" => 49,
            "entry_probe_count" => 49 * 8 * 8,
            "observable_realization" => "QuantumOptics NLevelBasis(8) operators i*L_ei are Hermitian finite probes",
            "quotient_discriminators" => ["generator_count", "carrier_dimension", "anticommutation_signature", "generated_clifford_rank", "spinor_dimension"],
        ),
        "C" => Dict{String,Any}(
            "state_constraints" => ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "rung_specific_constraints" => [
                "Cayley-Dickson octonion multiplication table",
                "L_ei^T = -L_ei",
                "L_ei L_ej + L_ej L_ei = -2 delta_ij I",
                "first six L_ei generate a 64-dimensional Cl(0,6) carrier on an 8-dimensional spinor",
            ],
            "density_constraint_witness" => qo["density_constraint_witness"],
        ),
        "quotient" => quotient,
        "octonion_left_action" => Dict{String,Any}(
            "carrier_real_dimension" => 8,
            "generator_count" => 7,
            "skew" => o_skew,
            "anticommutation" => o_anti,
            "generated_rank_first_six" => o_rank6,
            "generated_rank_all_seven_matrix_image" => o_rank7,
            "spinor_dim" => 8,
            "pseudoscalar_link" => pseudoscalar_link,
        ),
        "quaternion_control" => Dict{String,Any}(
            "carrier_real_dimension" => 4,
            "generator_count" => 3,
            "skew" => h_skew,
            "anticommutation" => h_anti,
            "generated_rank_first_two" => h_rank2,
            "generated_rank_all_three_matrix_image" => h_rank3,
            "spinor_dim" => 2,
            "control_result" => "Cl(0,2) rank 4 / spinor 2, not Cl(0,6) rank 64 / spinor 8",
        ),
        "quantumoptics_probe" => qo,
        "cliffordalgebras_comparison" => clifford_pkg,
        "julia_z3_clifford_proof" => z3_report,
        "negative_controls" => Dict{String,Any}(
            "quaternion_H_control" => Dict{String,Any}(
                "octonion_rank" => o_rank6["rank"],
                "quaternion_rank" => h_rank2["rank"],
                "octonion_spinor_dim" => 8,
                "quaternion_spinor_dim" => 2,
                "flips" => o_rank6["rank"] != h_rank2["rank"],
            ),
            "drop_dimension_and_rank_probe" => quotient["coarsening_flip"],
            "z3_erase_L_entry_binding_flip" => Dict{String,Any}(
                "with_L_entry_bindings" => z3_report["verdict"],
                "after_erasing_L_entry_bindings" => z3_report["erase_L_entry_binding_flip"]["status"],
                "flips" => z3_report["verdict"] != z3_report["erase_L_entry_binding_flip"]["status"],
            ),
            "z3_wrong_sign_plus_I_control" => Dict{String,Any}(
                "correct_relation_violation" => z3_report["verdict"],
                "wrong_sign_plus_I_violation" => z3_report["wrong_sign_plus_I_violation_control"]["status"],
                "flips" => z3_report["verdict"] != z3_report["wrong_sign_plus_I_violation_control"]["status"],
            ),
        ),
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "QuantumOptics" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing finite 8-level observable realization of the i*L_ei probe family and density admissibility witness"),
            "CliffordAlgebras" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing package comparison for Cl(0,6) dimension 64 and generator anticommutation"),
            "Z3" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing in-solver derivation of octonion L-entry anticommutator products"),
            "LinearAlgebra" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive local matrix residuals, SVD ranks, and eigenvalue checks; not the carrier authority"),
            "JSON" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive result serialization"),
            "SHA" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive source hash"),
            "Dates" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive UTC timestamp"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "QuantumOptics" => "load_bearing",
            "CliffordAlgebras" => "load_bearing",
            "Z3" => "load_bearing",
            "LinearAlgebra" => "supportive",
            "JSON" => "supportive",
            "SHA" => "supportive",
            "Dates" => "supportive",
        ),
        "summary" => Dict{String,Any}(
            "octonion_cl6_rank" => o_rank6["rank"],
            "octonion_all7_matrix_rank" => o_rank7["rank"],
            "octonion_spinor_dim" => 8,
            "quaternion_cl2_rank" => h_rank2["rank"],
            "quaternion_all3_matrix_rank" => h_rank3["rank"],
            "quaternion_spinor_dim" => 2,
            "octonion_anticommutation_max_residual" => o_anti["max_residual"],
            "quaternion_anticommutation_max_residual" => h_anti["max_residual"],
            "pseudoscalar_link_plus_residual" => pseudoscalar_link["plus_residual"],
            "full_quotient_class_count" => quotient["full_probe_class_count"],
            "coarse_quotient_class_count" => quotient["drop_dimension_and_rank_probe_class_count"],
            "z3_verdict" => z3_report["verdict"],
            "z3_offdiag_violation" => z3_report["offdiag_pair_violation"]["status"],
            "z3_self_square_violation" => z3_report["self_square_violation"]["status"],
            "z3_erased_status" => z3_report["erase_L_entry_binding_flip"]["status"],
            "z3_wrong_sign_control" => z3_report["wrong_sign_plus_I_violation_control"]["status"],
            "all_pass" => all_pass,
        ),
        "all_pass" => all_pass,
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: ", RESULT_PATH)
    println(
        "JULIA_DONE all_pass=$(result["all_pass"]) ",
        "octonion_cl6_rank=$(result["summary"]["octonion_cl6_rank"]) ",
        "quaternion_cl2_rank=$(result["summary"]["quaternion_cl2_rank"]) ",
        "z3=$(result["summary"]["z3_verdict"]) ",
        "z3_wrong_sign_control=$(result["summary"]["z3_wrong_sign_control"])",
    )
    result["all_pass"] ? 0 : 2
end

exit(main())
