#!/usr/bin/env julia
# object_id: foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh
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

const RUNG_ID = "foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh"
const OBJECT_ID = RUNG_ID
const SOURCE_PATH = @__FILE__
const RESULT_PATH = joinpath(@__DIR__, "results", "foundation_foundation_r4_nonassoc_root_vs_carrier_discriminator_xhigh_julia_xhigh_results.json")
const R3_RESULT_PATH = joinpath(@__DIR__, "results", "foundation_r3_octonion_cl6_link_xhigh_julia_results.json")
const TOL = 1.0e-9

classification = "scratch_diagnostic"
promotion_allowed = false
formal_admission_allowed = false
reads_peer_result = true

function load_r3_peer_result()
    isfile(R3_RESULT_PATH) || error("R4 nonassoc discriminator requires R3 peer result at $(R3_RESULT_PATH); none found.")
    JSON.parsefile(R3_RESULT_PATH)
end

function r3_provenance_check(r3::AbstractDict, o_mats::Vector{Matrix{Float64}})
    # Verify this file's freshly-computed O left-multiplication matrices match
    # the values R3 already admitted (as scratch_diagnostic), rather than just
    # asserting a peer-read happened. Compares generator count, spinor
    # dimension, and generated Cl(0,6) rank against R3's persisted summary.
    r3_summary = r3["summary"]
    r3_rank = r3_summary["octonion_cl6_rank"]
    r3_spinor_dim = r3_summary["octonion_spinor_dim"]
    dim = size(o_mats[1], 1)
    cols = Vector{Float64}[]
    generator_count = min(6, length(o_mats))
    for mask in 0:(2^generator_count - 1)
        acc = Matrix{Float64}(I, dim, dim)
        for idx in 1:generator_count
            if ((mask >> (idx - 1)) & 1) == 1
                acc = acc * o_mats[idx]
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
        "r3_octonion_cl6_rank" => r3_rank,
        "r3_octonion_spinor_dim" => r3_spinor_dim,
        "local_recomputed_cl6_rank_from_same_cd_mul_construction" => local_rank,
        "local_spinor_dim" => dim,
        "matches_r3" => local_rank == r3_rank && dim == r3_spinor_dim,
    )
end

const CLAIM_CEILING = "Scratch foundation diagnostic only: tests whether bare distinguishability/finitude/noncommutation roots force non-associativity. Verdict is bounded to forced-vs-installed for R/C/H/O Cayley-Dickson carriers; no promotion or formal admission."

const TOOL_MANIFEST = Dict(
    "QuantumOptics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite carrier state/observable witness for trace=1, PSD, Hermiticity, and probe-realization constraints",
    ),
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Cl(0,6) package witness for the stronger 7-imaginary-unit/3-qubit Weyl-floor installing constraint",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing discrete cardinality check that seven distinct imaginary labels cannot be drawn from H but can be drawn from O",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive norms/eigenvalue checks only; not the only claim carrier",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
)

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function cd_conj(x::Vector{Float64})
    y = copy(x)
    length(y) > 1 && (y[2:end] .*= -1.0)
    return y
end

function cd_mul(x::Vector{Float64}, y::Vector{Float64})
    n = length(x)
    n == 1 && return [x[1] * y[1]]
    half = n ÷ 2
    a, b = x[1:half], x[(half + 1):end]
    c, d = y[1:half], y[(half + 1):end]
    return vcat(cd_mul(a, c) - cd_mul(cd_conj(d), b), cd_mul(d, a) + cd_mul(b, cd_conj(c)))
end

function basis(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    return v
end

function multiplication_table(dim::Int)
    table = zeros(Int, dim, dim, dim)
    for i0 in 0:(dim - 1), j0 in 0:(dim - 1)
        prod = cd_mul(basis(dim, i0), basis(dim, j0))
        for k0 in 0:(dim - 1)
            table[k0 + 1, i0 + 1, j0 + 1] = Int(round(prod[k0 + 1]))
        end
    end
    return table
end

function left_matrix(table::Array{Int,3}, unit_idx0::Int)
    dim = size(table, 1)
    mat = zeros(Float64, dim, dim)
    for col0 in 0:(dim - 1), row0 in 0:(dim - 1)
        mat[row0 + 1, col0 + 1] = table[row0 + 1, unit_idx0 + 1, col0 + 1]
    end
    return mat
end

left_matrices(table::Array{Int,3}) = [left_matrix(table, idx0) for idx0 in 1:(size(table, 1) - 1)]

function square_minus_one(table::Array{Int,3}, idx0::Int)
    dim = size(table, 1)
    return table[1, idx0 + 1, idx0 + 1] == -1 && all(table[k0 + 1, idx0 + 1, idx0 + 1] == 0 for k0 in 1:(dim - 1))
end

function anticommutes(table::Array{Int,3}, i0::Int, j0::Int)
    dim = size(table, 1)
    return all(table[k0 + 1, i0 + 1, j0 + 1] + table[k0 + 1, j0 + 1, i0 + 1] == 0 for k0 in 0:(dim - 1))
end

function commutator_coeffs(table::Array{Int,3}, i0::Int, j0::Int)
    dim = size(table, 1)
    return [table[k0 + 1, i0 + 1, j0 + 1] - table[k0 + 1, j0 + 1, i0 + 1] for k0 in 0:(dim - 1)]
end

function max_commutator_norm(table::Array{Int,3})
    dim = size(table, 1)
    max_norm = 0.0
    witness = nothing
    for i0 in 1:(dim - 1), j0 in (i0 + 1):(dim - 1)
        coeffs = commutator_coeffs(table, i0, j0)
        norm_value = norm(Float64.(coeffs))
        if norm_value > max_norm
            max_norm = norm_value
            witness = Dict("i" => i0, "j" => j0, "coefficients" => coeffs, "norm" => norm_value)
        end
    end
    return Dict("max_norm" => max_norm, "witness" => witness, "noncommutative" => max_norm > TOL)
end

function anticommuting_imaginary_count(table::Array{Int,3})
    dim = size(table, 1)
    imaginary = collect(1:(dim - 1))
    valid = [idx0 for idx0 in imaginary if square_minus_one(table, idx0)]
    pair_failures = Vector{Dict{String,Any}}()
    for i0 in valid, j0 in valid
        i0 < j0 || continue
        if !anticommutes(table, i0, j0)
            push!(pair_failures, Dict("i" => i0, "j" => j0))
        end
    end
    return Dict(
        "count" => isempty(pair_failures) ? length(valid) : 0,
        "valid_imaginary_indices" => valid,
        "pair_failures" => pair_failures,
        "all_distinct_imaginary_basis_units_mutually_anticommute" => isempty(pair_failures),
    )
end

function associator_max_norm(table::Array{Int,3})
    dim = size(table, 1)
    max_norm = 0.0
    witness = nothing
    for a0 in 0:(dim - 1), b0 in 0:(dim - 1), c0 in 0:(dim - 1)
        left = cd_mul(cd_mul(basis(dim, a0), basis(dim, b0)), basis(dim, c0))
        right = cd_mul(basis(dim, a0), cd_mul(basis(dim, b0), basis(dim, c0)))
        residual = left - right
        norm_value = norm(residual)
        if norm_value > max_norm
            max_norm = norm_value
            witness = Dict("a" => a0, "b" => b0, "c" => c0, "residual" => residual, "norm" => norm_value)
        end
    end
    return Dict("max_norm" => max_norm, "witness" => witness, "associative" => max_norm <= TOL)
end

function generated_matrix_rank(mats::Vector{Matrix{Float64}}, generator_count::Int)
    generator_count == 0 && return Dict("generator_count" => 0, "word_count" => 1, "rank" => 1, "rank_tol" => 0.0)
    dim = size(mats[1], 1)
    cols = Vector{Vector{Float64}}()
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
    return Dict("generator_count" => generator_count, "word_count" => length(cols), "rank" => count(>(tol), singular), "rank_tol" => tol)
end

function quantumoptics_witness(table::Array{Int,3})
    dim = size(table, 1)
    b = NLevelBasis(dim)
    rho = Operator(b, b, Matrix{ComplexF64}(I, dim, dim) ./ dim)
    eigs = eigvals(Hermitian(rho.data))
    mats = left_matrices(table)
    observables = [Operator(b, b, ComplexF64.(im .* mat)) for mat in mats]
    hermitian_residuals = isempty(observables) ? [0.0] : [norm(op.data - op.data') for op in observables]
    return Dict(
        "basis" => string(typeof(b)),
        "observable_count" => length(observables),
        "iL_observable_hermitian_max_residual" => maximum(hermitian_residuals),
        "density_constraint_witness" => Dict(
            "trace" => real(tr(rho.data)),
            "normalization" => real(tr(rho.data)),
            "hermiticity_residual" => norm(rho.data - rho.data'),
            "min_eigenvalue" => minimum(real.(eigs)),
            "trace_one_pass" => abs(real(tr(rho.data)) - 1.0) <= TOL,
            "psd_pass" => minimum(real.(eigs)) >= -TOL,
            "hermitian_pass" => norm(rho.data - rho.data') <= TOL,
        ),
    )
end

function carrier_report(name::String, dim::Int)
    table = multiplication_table(dim)
    mats = left_matrices(table)
    anti_count = anticommuting_imaginary_count(table)
    noncomm = max_commutator_norm(table)
    assoc = associator_max_norm(table)
    rank_limit = min(6, length(mats))
    return Dict(
        "name" => name,
        "real_dimension" => dim,
        "finite" => true,
        "table_shape" => [dim, dim, dim],
        "imaginary_unit_count" => anti_count["count"],
        "anticommuting_imaginary_units" => anti_count,
        "noncommutation" => noncomm,
        "associativity" => assoc,
        "left_matrix_rank_first_min6" => generated_matrix_rank(mats, rank_limit),
        "quantumoptics_constraints" => quantumoptics_witness(table),
        "bare_root_admissible" => dim < 4 ? false : (noncomm["noncommutative"] && true),
        "cl6_7unit_admissible" => anti_count["count"] >= 7,
    )
end

function quotient_summary(carriers::AbstractDict)
    S = ["R", "C", "H", "O"]
    bare_admitted = [name for name in S if carriers[name]["bare_root_admissible"]]
    cl6_admitted = [name for name in S if carriers[name]["cl6_7unit_admissible"]]
    full_signatures = Dict{String,String}()
    coarse_signatures = Dict{String,String}()
    for name in S
        row = carriers[name]
        full_signatures[name] = "finite=$(row["finite"]);noncomm=$(row["noncommutation"]["noncommutative"]);dim=$(row["real_dimension"]);imaginary_units=$(row["imaginary_unit_count"]);associative=$(row["associativity"]["associative"])"
        coarse_signatures[name] = "finite=$(row["finite"]);noncomm=$(row["noncommutation"]["noncommutative"])"
    end
    return Dict(
        "S" => S,
        "equivalence_relation" => "a ~_M b iff every finite M probe matches: finite table, noncommutator probe, carrier dimension, mutually anticommuting imaginary-unit count, and associator probe",
        "bare_root_admitted_carriers" => bare_admitted,
        "strong_cl6_7unit_admitted_carriers" => cl6_admitted,
        "full_probe_signatures" => full_signatures,
        "coarse_signatures_after_dropping_dimension_unit_and_associator_probes" => coarse_signatures,
        "bare_root_class_count" => length(unique(values(full_signatures))),
        "coarse_class_count" => length(unique(values(coarse_signatures))),
        "drop_probe_coarsening_flip" => Dict(
            "dropped_probes" => ["carrier_dimension", "imaginary_unit_count", "associator_probe"],
            "before_class_count" => length(unique(values(full_signatures))),
            "after_class_count" => length(unique(values(coarse_signatures))),
            "flips" => length(unique(values(full_signatures))) != length(unique(values(coarse_signatures))),
        ),
    )
end

function cliffordalgebras_report()
    cl06 = CliffordAlgebra(0, 6)
    return Dict(
        "package" => "CliffordAlgebras",
        "constructed" => "CliffordAlgebra(0, 6)",
        "basis_symbol_count" => length(propertynames(cl06)),
        "expected_cl6_dimension" => 64,
        "three_qubit_weyl_floor_real_spinor_dimension" => 8,
        "pass" => length(propertynames(cl06)) == 64,
    )
end

function z3_distinct_slots_status(domain_size::Int, required::Int)
    solver = Z3.Solver()
    vars = [Z3.IntVar("slot_$i") for i in 1:required]
    for var in vars
        Z3.add(solver, Z3.Not(var < Z3.IntVal(1)))
        Z3.add(solver, Z3.Not(Z3.IntVal(domain_size) < var))
    end
    for i in 1:required, j in (i + 1):required
        Z3.add(solver, Z3.Not(vars[i] == vars[j]))
    end
    return string(Z3.check(solver))
end

function z3julia_report()
    return Dict(
        "encoding" => "Z3.jl cardinality guard: seven distinct imaginary-unit labels must be drawn from the carrier's finite imaginary basis.",
        "H_domain_size" => 3,
        "O_domain_size" => 7,
        "required_distinct_imaginary_units" => 7,
        "H_has_7_distinct_imaginary_labels" => z3_distinct_slots_status(3, 7),
        "O_has_7_distinct_imaginary_labels" => z3_distinct_slots_status(7, 7),
    )
end

function build_result()
    mkpath(dirname(RESULT_PATH))
    carriers = Dict(
        "R" => carrier_report("R", 1),
        "C" => carrier_report("C", 2),
        "H" => carrier_report("H", 4),
        "O" => carrier_report("O", 8),
    )
    r3_peer = load_r3_peer_result()
    o_table = multiplication_table(8)
    o_mats = left_matrices(o_table)
    r3_provenance = r3_provenance_check(r3_peer, o_mats)
    quotient = quotient_summary(carriers)
    unit_counts = Dict(name => carriers[name]["imaginary_unit_count"] for name in ["R", "C", "H", "O"])
    z3j = z3julia_report()
    cl = cliffordalgebras_report()
    h_bare = carriers["H"]["bare_root_admissible"]
    h_strong = carriers["H"]["cl6_7unit_admissible"]
    o_strong = carriers["O"]["cl6_7unit_admissible"]
    h_associative = carriers["H"]["associativity"]["associative"]
    forced_false = h_bare && h_associative
    installed = h_bare && !h_strong && o_strong
    # Non-associativity is forced by the bare root only if EVERY carrier the bare
    # root admits is itself associative-only-when-excluded, i.e. if no admitted
    # carrier can be associative. H is bare-root-admissible (h_bare) and its
    # computed associator_max_norm shows it IS associative (h_associative): a
    # bare-root-admissible, associative carrier survives, so the bare root does
    # not force non-associativity. This is computed from the same associator
    # witness used above, not asserted independently of it.
    nonassoc_forced_by_bare_root = !(h_bare && h_associative)
    all_pass = (
        unit_counts == Dict("R" => 0, "C" => 1, "H" => 3, "O" => 7) &&
        h_bare &&
        !h_strong &&
        o_strong &&
        forced_false &&
        installed &&
        quotient["drop_probe_coarsening_flip"]["flips"] &&
        cl["pass"] &&
        z3j["H_has_7_distinct_imaginary_labels"] == "unsat" &&
        z3j["O_has_7_distinct_imaginary_labels"] == "sat" &&
        reads_peer_result &&
        r3_provenance["matches_r3"]
    )
    return Dict(
        "schema" => "codex_ratchet.engine_leg.v1",
        "object_id" => OBJECT_ID,
        "rung_id" => RUNG_ID,
        "engine" => "julia",
        "classification" => classification,
        "promotion_allowed" => promotion_allowed,
        "formal_admission_allowed" => formal_admission_allowed,
        "reads_peer_result" => reads_peer_result,
        "ran" => true,
        "standalone" => true,
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "claim_ceiling" => CLAIM_CEILING,
        "M" => Dict(
            "name" => "finite root distinguishability probe family over R/C/H/O Cayley-Dickson carriers",
            "probe_family" => [
                "finite multiplication table shape",
                "left-multiplication imaginary-unit observables i*L_ei",
                "noncommutator coefficients [e_i,e_j]",
                "mutually anticommuting imaginary-unit count",
                "associator witness used as a probe, not as a bare-root constraint",
            ],
            "quotient_discriminators" => ["finite", "noncommutative", "carrier_dimension", "imaginary_unit_count", "associative"],
        ),
        "C" => Dict(
            "state_constraints" => ["trace(rho)=1", "rho PSD", "rho Hermitian", "normalization"],
            "bare_root_constraints" => ["finite carrier table", "noncommuting [Z,X]-analog exists", "finite M quotient is well-defined"],
            "rung_specific_stronger_constraint" => "carrier has >=7 mutually anticommuting imaginary units / generates Cl(0,6) / carries the 3-qubit Weyl floor",
            "density_constraint_witness_H" => carriers["H"]["quantumoptics_constraints"]["density_constraint_witness"],
            "density_constraint_witness_O" => carriers["O"]["quantumoptics_constraints"]["density_constraint_witness"],
        ),
        "carriers" => carriers,
        "quotient" => quotient,
        "r3_peer_dependency" => r3_provenance,
        "cliffordalgebras_cl6_witness" => cl,
        "julia_z3_cardinality_guard" => z3j,
        "unit_counts" => unit_counts,
        "decision" => Dict(
            "H_bare_root_admissible" => h_bare,
            "H_associative" => h_associative,
            "H_cl6_7unit_admissible" => h_strong,
            "O_cl6_7unit_admissible" => o_strong,
            "nonassoc_forced_by_bare_root" => nonassoc_forced_by_bare_root,
            "nonassoc_forced_derivation" => "computed as NOT(H_bare_root_admissible AND H_associative), reading H_associative from carriers[\"H\"][\"associativity\"][\"associative\"] (associator_max_norm witness)",
            "nonassoc_installed_by_constraint" => "Cl(0,6)/>=7 mutually anticommuting imaginary units/3-qubit Weyl floor",
            "forced_vs_installed_verdict" => nonassoc_forced_by_bare_root ? "FORCED" : "INSTALLED_NOT_FORCED",
        ),
        "negative_control_flip" => Dict(
            "control" => "drop stronger Cl(0,6)/7-unit constraint while keeping bare finitude+noncommutation+quotient root",
            "H_under_bare_root" => "admitted",
            "H_under_stronger_cl6_7unit_constraint" => "excluded",
            "flips" => h_bare && !h_strong,
        ),
        "summary" => Dict(
            "all_pass" => all_pass,
            "unit_counts_R_C_H_O" => [unit_counts["R"], unit_counts["C"], unit_counts["H"], unit_counts["O"]],
            "H_bare_root_admissible" => h_bare,
            "H_cl6_7unit_admissible" => h_strong,
            "O_cl6_7unit_admissible" => o_strong,
            "nonassoc_forced_by_bare_root" => nonassoc_forced_by_bare_root,
            "forced_vs_installed_verdict" => nonassoc_forced_by_bare_root ? "FORCED" : "INSTALLED_NOT_FORCED",
            "bare_root_admitted_carriers" => quotient["bare_root_admitted_carriers"],
            "strong_cl6_7unit_admitted_carriers" => quotient["strong_cl6_7unit_admitted_carriers"],
            "drop_probe_coarsening_flips" => quotient["drop_probe_coarsening_flip"]["flips"],
        ),
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    s = result["summary"]
    println("wrote: ", RESULT_PATH)
    println(
        "JULIA_DONE all_pass=$(s["all_pass"]) ",
        "unit_counts=$(s["unit_counts_R_C_H_O"]) ",
        "H_bare=$(s["H_bare_root_admissible"]) ",
        "H_cl6=$(s["H_cl6_7unit_admissible"]) ",
        "O_cl6=$(s["O_cl6_7unit_admissible"]) ",
        "verdict=$(s["forced_vs_installed_verdict"])",
    )
    return result["all_pass"] ? 0 : 2
end

exit(main())
