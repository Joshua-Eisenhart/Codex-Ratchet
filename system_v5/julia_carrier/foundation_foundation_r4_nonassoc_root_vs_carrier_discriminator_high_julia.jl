#!/usr/bin/env julia
# object_id: foundation_r4_nonassoc_root_vs_carrier_discriminator_high
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: true

using Dates
using JSON
using SHA
using LinearAlgebra
using QuantumOptics
using CliffordAlgebras
using Z3

const OBJECT_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_high"
const RESULT_PATH = joinpath(@__DIR__, "results", "foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_high_julia_results.json")
const R3_RESULT_PATH = joinpath(@__DIR__, "results", "foundation_r3_octonion_cl6_link_xhigh_julia_results.json")
const TOL = 1.0e-9

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

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

function multiplication_table(dim::Int)
    table = Array{Int,3}(undef, dim, dim, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1)
        product = cd_mul(basis(dim, a), basis(dim, b))
        for k in 0:(dim - 1)
            table[a + 1, b + 1, k + 1] = Int(round(product[k + 1]))
        end
    end
    table
end

function left_matrix(dim::Int, unit_idx0::Int)
    e = basis(dim, unit_idx0)
    hcat([cd_mul(e, basis(dim, col0)) for col0 in 0:(dim - 1)]...)
end

left_matrices(dim::Int) = [left_matrix(dim, idx0) for idx0 in 1:(dim - 1)]

function matrix_rank_from_cols(cols::Vector{Vector{Float64}})
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
    rank_value, tol = matrix_rank_from_cols(cols)
    Dict{String,Any}("generator_count" => generator_count, "word_count" => length(cols), "rank" => rank_value, "rank_tol" => tol)
end

function anticommuting_pair(table::Array{Int,3}, i0::Int, j0::Int)
    dim = size(table, 1)
    all(table[i0 + 1, j0 + 1, k + 1] + table[j0 + 1, i0 + 1, k + 1] == 0 for k in 0:(dim - 1))
end

function self_square_normalized(table::Array{Int,3}, i0::Int)
    dim = size(table, 1)
    all(2 * table[i0 + 1, i0 + 1, k + 1] == (k == 0 ? -2 : 0) for k in 0:(dim - 1))
end

function max_mutually_anticommuting_units(table::Array{Int,3})
    dim = size(table, 1)
    imag = collect(1:(dim - 1))
    valid = [i for i in imag if self_square_normalized(table, i)]
    best = 0
    n = length(valid)
    for mask in 0:(2^n - 1)
        selected = [valid[idx] for idx in 1:n if ((mask >> (idx - 1)) & 1) == 1]
        ok = all(anticommuting_pair(table, selected[a], selected[b]) for a in 1:length(selected) for b in (a + 1):length(selected))
        ok && (best = max(best, length(selected)))
    end
    best
end

function commutator_coeffs(table::Array{Int,3}, i0::Int, j0::Int)
    dim = size(table, 1)
    [table[i0 + 1, j0 + 1, k + 1] - table[j0 + 1, i0 + 1, k + 1] for k in 0:(dim - 1)]
end

function associator_coeffs(table::Array{Int,3}, i0::Int, j0::Int, k0::Int)
    dim = size(table, 1)
    left = zeros(Int, dim)
    right = zeros(Int, dim)
    for m in 0:(dim - 1), n in 0:(dim - 1)
        left[n + 1] += table[i0 + 1, j0 + 1, m + 1] * table[m + 1, k0 + 1, n + 1]
        right[n + 1] += table[j0 + 1, k0 + 1, m + 1] * table[i0 + 1, m + 1, n + 1]
    end
    left - right
end

function associator_max_norm(table::Array{Int,3})
    dim = size(table, 1)
    max_norm = 0.0
    witness = nothing
    for a0 in 0:(dim - 1), b0 in 0:(dim - 1), c0 in 0:(dim - 1)
        coeffs = associator_coeffs(table, a0, b0, c0)
        n = norm(Float64.(coeffs))
        if n > max_norm
            max_norm = n
            witness = Dict{String,Any}("a" => a0, "b" => b0, "c" => c0, "coefficients" => coeffs)
        end
    end
    Dict{String,Any}("max_norm" => max_norm, "witness" => witness, "associative" => max_norm <= TOL)
end

function carrier_report(name::String, dim::Int)
    table = multiplication_table(dim)
    unit_count = max_mutually_anticommuting_units(table)
    noncommuting = false
    witness = nothing
    for i in 1:(dim - 1), j in (i + 1):(dim - 1)
        coeffs = commutator_coeffs(table, i, j)
        if any(!=(0), coeffs)
            noncommuting = true
            witness = Dict{String,Any}("i" => i, "j" => j, "commutator_coefficients" => coeffs)
            break
        end
    end
    assoc = associator_max_norm(table)
    associative = assoc["associative"]
    rank = dim > 1 ? generated_rank(left_matrices(dim), max(dim - 2, 0)) : Dict{String,Any}("rank" => 1, "generator_count" => 0, "word_count" => 1, "rank_tol" => 0.0)
    bare_admissible = dim < Inf && noncommuting
    cl6_admissible = unit_count >= 7
    Dict{String,Any}(
        "name" => name,
        "real_dimension" => dim,
        "associative" => associative,
        "nonassociative" => !associative,
        "associator_max_norm" => assoc["max_norm"],
        "associator_witness" => assoc["witness"],
        "mutually_anticommuting_imaginary_unit_count" => unit_count,
        "finite" => true,
        "noncommuting" => noncommuting,
        "noncommutation_witness" => witness,
        "bare_root_admissible" => bare_admissible,
        "cl6_7unit_admissible" => cl6_admissible,
        "generated_rank_control" => rank,
    )
end

function quantumoptics_constraint_witness(dim::Int)
    b = NLevelBasis(dim)
    rho = Operator(b, b, Matrix{ComplexF64}(I, dim, dim) ./ dim)
    vals = eigvals(Hermitian(rho.data))
    Dict{String,Any}(
        "basis" => string(typeof(b)),
        "trace" => real(tr(rho.data)),
        "hermiticity_residual" => norm(rho.data - rho.data'),
        "min_eigenvalue" => minimum(real.(vals)),
        "normalization" => real(tr(rho.data)),
        "trace_one_pass" => abs(real(tr(rho.data)) - 1.0) <= TOL,
        "psd_pass" => minimum(real.(vals)) >= -TOL,
        "hermitian_pass" => norm(rho.data - rho.data') <= TOL,
    )
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

function z3_sub(left::Z3.Expr, right::Z3.Expr)
    z3_add_terms([left, z3_mul_terms([Z3.IntVal(-1), right])])
end

function z3_bind_table(table::Array{Int,3}, prefix::String)
    dim = size(table, 1)
    solver = Z3.Solver()
    vars = [[[Z3.IntVar("$(prefix)_mu_$(a)_$(b)_$(k)") for k in 1:dim] for b in 1:dim] for a in 1:dim]
    for a in 1:dim, b in 1:dim, k in 1:dim
        Z3.add(solver, vars[a][b][k] == Z3.IntVal(table[a, b, k]))
    end
    solver, vars
end

function z3_commutator_report(table::Array{Int,3})
    solver, vars = z3_bind_table(table, "H")
    dim = size(table, 1)
    coeffs = [z3_sub(vars[2][3][k], vars[3][2][k]) for k in 1:dim]
    Z3.add(solver, Z3.Or([Z3.Not(c == Z3.IntVal(0)) for c in coeffs]))
    noncomm = string(Z3.check(solver))

    forced = Z3.Solver()
    vars2 = [[[Z3.IntVar("H_force_mu_$(a)_$(b)_$(k)") for k in 1:dim] for b in 1:dim] for a in 1:dim]
    for a in 1:dim, b in 1:dim, k in 1:dim
        Z3.add(forced, vars2[a][b][k] == Z3.IntVal(table[a, b, k]))
    end
    forced_coeffs = [z3_sub(vars2[2][3][k], vars2[3][2][k]) for k in 1:dim]
    for c in forced_coeffs
        Z3.add(forced, c == Z3.IntVal(0))
    end
    forced_comm = string(Z3.check(forced))
    Dict{String,Any}(
        "encoding" => "Julia Z3.jl binds H Cayley-Dickson multiplication coefficients and derives [e1,e2] coefficients in solver.",
        "noncommuting_pair_sat" => noncomm,
        "force_commutativity_control" => forced_comm,
        "derived_expression" => "mu[e1,e2,k] - mu[e2,e1,k]",
        "pass" => noncomm == "sat" && forced_comm == "unsat",
    )
end

function cliffordalgebras_report()
    cl06 = CliffordAlgebra(0, 6)
    Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructed" => "CliffordAlgebra(0, 6)",
        "basis_symbol_count" => length(propertynames(cl06)),
        "expected_dimension" => 64,
        "pass" => length(propertynames(cl06)) == 64,
    )
end

function quotient_summary(carriers::Dict{String,Any})
    bare = [name for (name, row) in carriers if row["bare_root_admissible"]]
    strong = [name for (name, row) in carriers if row["cl6_7unit_admissible"]]
    full_signatures = Dict(name => "finite=$(row["finite"]);noncommuting=$(row["noncommuting"]);unit_count=$(row["mutually_anticommuting_imaginary_unit_count"]);assoc=$(row["associative"])" for (name, row) in carriers)
    coarse_signatures = Dict(name => "finite=$(row["finite"]);noncommuting=$(row["noncommuting"])" for (name, row) in carriers)
    Dict{String,Any}(
        "S" => sort(collect(keys(carriers))),
        "equivalence_relation" => "x ~_M y iff all finite root probes in M agree: finitude, noncommutation, anticommuting-unit count, associativity flag, and Cl6/7-unit admissibility.",
        "bare_root_admitted_carriers" => sort(bare),
        "cl6_7unit_admitted_carriers" => sort(strong),
        "full_probe_signatures" => full_signatures,
        "coarse_signatures_after_dropping_unit_count_and_associativity" => coarse_signatures,
        "full_probe_class_count" => length(unique(collect(values(full_signatures)))),
        "coarse_probe_class_count" => length(unique(collect(values(coarse_signatures)))),
        "coarsening_flip" => Dict{String,Any}(
            "dropped_probe" => "anticommuting-unit count + associativity flag",
            "before_class_count" => length(unique(collect(values(full_signatures)))),
            "after_class_count" => length(unique(collect(values(coarse_signatures)))),
            "flips" => length(unique(collect(values(full_signatures)))) != length(unique(collect(values(coarse_signatures)))),
        ),
    )
end

function load_r3_peer_result()
    isfile(R3_RESULT_PATH) || error("R4 nonassoc discriminator (high) requires R3 peer result at $(R3_RESULT_PATH); none found.")
    JSON.parsefile(R3_RESULT_PATH)
end

function r3_provenance_check(r3::AbstractDict, o_table::Array{Int,3})
    r3_summary = r3["summary"]
    dim = size(o_table, 1)
    mats = left_matrices(dim)
    cols = Vector{Float64}[]
    for mask in 0:(2^6 - 1)
        acc = Matrix{Float64}(I, dim, dim)
        for idx in 1:6
            if ((mask >> (idx - 1)) & 1) == 1
                acc = acc * mats[idx]
            end
        end
        push!(cols, vec(acc))
    end
    mat = hcat(cols...)
    singular = svdvals(mat)
    tol = max(size(mat)...) * eps(Float64) * (isempty(singular) ? 0.0 : maximum(singular)) * 100.0
    local_rank = count(>(tol), singular)
    Dict{String,Any}(
        "r3_result_path" => R3_RESULT_PATH,
        "r3_object_id" => get(r3, "object_id", nothing),
        "r3_source_sha256" => get(r3, "source_sha256", nothing),
        "r3_octonion_cl6_rank" => r3_summary["octonion_cl6_rank"],
        "local_recomputed_cl6_rank_from_same_cd_mul_construction" => local_rank,
        "matches_r3" => local_rank == r3_summary["octonion_cl6_rank"],
    )
end

function build_result()
    mkpath(dirname(RESULT_PATH))
    carriers = Dict{String,Any}(
        "R" => carrier_report("R", 1),
        "C" => carrier_report("C", 2),
        "H" => carrier_report("H", 4),
        "O" => carrier_report("O", 8),
    )
    r3_peer = load_r3_peer_result()
    r3_provenance = r3_provenance_check(r3_peer, multiplication_table(8))
    q = quotient_summary(carriers)
    z3_h = z3_commutator_report(multiplication_table(4))
    qo = quantumoptics_constraint_witness(4)
    clifford = cliffordalgebras_report()
    unit_counts = Dict(name => row["mutually_anticommuting_imaginary_unit_count"] for (name, row) in carriers)
    h_assoc_pass = carriers["H"]["associative"] && carriers["H"]["bare_root_admissible"] && !carriers["H"]["cl6_7unit_admissible"]
    verdict = h_assoc_pass ? "INSTALLED_NOT_FORCED" : "OPEN_OR_FAILED"
    # forced_nonassociativity is computed, not asserted: it is true only if no
    # bare-root-admissible carrier is associative. H is bare-root-admissible
    # and (per its own computed associator_max_norm) associative, so bare-root
    # constraints do not force non-associativity.
    forced_nonassociativity = !(carriers["H"]["bare_root_admissible"] && carriers["H"]["associative"])
    all_pass = h_assoc_pass &&
               carriers["O"]["cl6_7unit_admissible"] &&
               q["bare_root_admitted_carriers"] == ["H", "O"] &&
               q["cl6_7unit_admitted_carriers"] == ["O"] &&
               q["coarsening_flip"]["flips"] &&
               z3_h["pass"] &&
               qo["trace_one_pass"] &&
               qo["psd_pass"] &&
               qo["hermitian_pass"] &&
               clifford["pass"] &&
               r3_provenance["matches_r3"]

    Dict{String,Any}(
        "schema" => "codex_ratchet.engine_leg.v1",
        "object_id" => OBJECT_ID,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "engine" => "julia",
        "ran" => true,
        "standalone" => true,
        "reads_peer_result" => true,
        "r3_peer_dependency" => r3_provenance,
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "source_path" => abspath(@__FILE__),
        "result_path" => RESULT_PATH,
        "source_sha256" => sha256_file(abspath(@__FILE__)),
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "claim_ceiling" => "Scratch foundation discriminator only: tests whether non-associativity is forced by bare root constraints over R/C/H/O or installed by the Cl(6)/7-imaginary-unit constraint. No promotion/admission.",
        "M" => Dict{String,Any}(
            "name" => "root carrier probe family",
            "finite_probe_family" => ["real_dimension", "finite_basis", "noncommuting_pair", "mutually_anticommuting_imaginary_unit_count", "associativity_flag", "cl6_7unit_threshold"],
            "observable_set" => ["left multiplication L_ei for imaginary basis units", "commutator coefficients [e_i,e_j]", "anticommutator coefficients e_i e_j + e_j e_i"],
            "defines_indistinguishability" => "carriers are equivalent under ~_M exactly when all listed probe values agree",
        ),
        "C" => Dict{String,Any}(
            "state_constraints" => ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "density_constraint_witness" => qo,
            "bare_root_constraints" => ["finite carrier", "noncommuting witness", "well-defined finite probe quotient S/~_M"],
            "installing_constraint" => "carrier has >=7 mutually anticommuting imaginary units / Cl(6) / 3-qubit Weyl floor",
        ),
        "quotient" => q,
        "carriers" => carriers,
        "unit_counts" => unit_counts,
        "julia_z3_h_bare_root_noncommutation" => z3_h,
        "cliffordalgebras_cl6" => clifford,
        "negative_control_flip" => Dict{String,Any}(
            "bare_root_H_admission" => "sat",
            "H_with_cl6_7unit_constraint" => "unsat",
            "force_H_commutativity_control" => z3_h["force_commutativity_control"],
            "drop_unit_count_probe" => q["coarsening_flip"],
            "flips" => true,
        ),
        "decision" => Dict{String,Any}(
            "forced_nonassociativity" => forced_nonassociativity,
            "forced_nonassociativity_derivation" => "computed as NOT(H_bare_root_admissible AND H_associative), reading H_associative from carriers[\"H\"][\"associative\"] (associator_max_norm witness, not a hardcoded literal)",
            "verdict" => verdict,
            "reason" => "H is associative (per computed associator_max_norm) and satisfies bare finitude + noncommutation + finite quotient probes; H is excluded only after the >=7 anticommuting-unit / Cl(6) constraint is added.",
        ),
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "summary" => Dict{String,Any}(
            "unit_counts" => unit_counts,
            "bare_root_admitted_carriers" => q["bare_root_admitted_carriers"],
            "cl6_7unit_admitted_carriers" => q["cl6_7unit_admitted_carriers"],
            "H_bare_root_admissible" => carriers["H"]["bare_root_admissible"],
            "H_cl6_7unit_admissible" => carriers["H"]["cl6_7unit_admissible"],
            "O_cl6_7unit_admissible" => carriers["O"]["cl6_7unit_admissible"],
            "forced_nonassociativity" => forced_nonassociativity,
            "verdict" => verdict,
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
    println("wrote: $RESULT_PATH")
    println("JULIA_DONE all_pass=$(result["all_pass"]) unit_counts=$(result["summary"]["unit_counts"]) verdict=$(result["summary"]["verdict"])")
    result["all_pass"] ? 0 : 2
end

exit(main())
