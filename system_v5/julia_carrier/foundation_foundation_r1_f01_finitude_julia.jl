#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using Z3

const SOURCE_PATH = @__FILE__
const RESULT_PATH = joinpath(
    @__DIR__,
    "results",
    "foundation_foundation_r1_f01_finitude_julia_results.json",
)

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-10

function qo_operator(basis, matrix)
    Operator(basis, basis, Matrix{ComplexF64}(matrix))
end

function density_rank_qo(rho)
    vals = real.(eigenenergies(rho))
    count(vals .> TOL), vals
end

function z3_bound_case(; computed_dim::Int, computed_rank::Int, use_f01::Bool)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    d = Z3.IntVar("computed_dim_$(computed_rank)_$(use_f01)", ctx)
    r = Z3.IntVar("computed_rank_$(computed_rank)_$(use_f01)", ctx)

    Z3.add(solver, d == Z3.IntVal(computed_dim, ctx))
    Z3.add(solver, r == Z3.IntVal(computed_rank, ctx))
    Z3.add(solver, d == Z3.IntVal(computed_dim, ctx))
    Z3.add(solver, Z3.Not(r < Z3.IntVal(0, ctx)))
    if use_f01
        Z3.add(solver, Z3.Not(d < r))
    end
    string(Z3.check(solver))
end

function probe_vector(probes, rho)
    [real(tr(probe * rho)) for probe in probes]
end

function class_count(rows)
    length(Set(Tuple(round.(row; digits=12)) for row in rows))
end

function main()
    basis = NLevelBasis(3)
    padded_basis = NLevelBasis(4)

    p0 = qo_operator(basis, [1 0 0; 0 0 0; 0 0 0])
    p1 = qo_operator(basis, [0 0 0; 0 1 0; 0 0 0])
    p2 = qo_operator(basis, [0 0 0; 0 0 0; 0 0 1])
    x01 = qo_operator(basis, [0 0.5 0; 0.5 0 0; 0 0 0])
    probes = [p0, p1, p2, x01]
    probe_names = ["P0", "P1", "P2", "X01_half"]

    rho_a = qo_operator(basis, [0.5 0 0; 0 0.3 0; 0 0 0.2])
    rho_b = qo_operator(basis, [0.5 0.05 0; 0.05 0.3 0; 0 0 0.2])
    rho_c = qo_operator(basis, [0.5 0 0; 0 0.2 0; 0 0 0.3])
    admitted = [rho_a, rho_b, rho_c]
    admitted_names = ["rho_a_diag_503020", "rho_b_coherent_503020_x01_005", "rho_c_diag_502030"]

    rho_over = qo_operator(padded_basis, (1.0 / 4.0) * Matrix{Float64}(I, 4, 4))
    reference_dim = size(dense(rho_a).data, 1)
    padded_dim = size(dense(rho_over).data, 1)
    admitted_rank, admitted_eigs = density_rank_qo(rho_a)
    over_rank, over_eigs = density_rank_qo(rho_over)
    all_ranks = Int[]
    all_eigs = []
    for rho in admitted
        r, vals = density_rank_qo(rho)
        push!(all_ranks, r)
        push!(all_eigs, vals)
    end

    identity_residual = maximum(abs.(dense(sum(probes[1:3]) - one(p0)).data))
    vectors = [probe_vector(probes, rho) for rho in admitted]
    dropped_vectors = [row[1:3] for row in vectors]
    full_class_count = class_count(vectors)
    dropped_class_count = class_count(dropped_vectors)
    quotient_classes = Dict(
        "class_$(idx)" => Dict(
            "representative" => admitted_names[idx],
            "probe_vector" => vectors[idx],
            "members" => [admitted_names[idx]],
        )
        for idx in eachindex(admitted)
    )

    traces = [real(tr(rho)) for rho in admitted]
    hermitian_residuals = [
        maximum(abs.(dense(rho).data - dense(rho).data'))
        for rho in admitted
    ]
    min_eigs = [minimum(vals) for vals in all_eigs]

    z3_admitted = z3_bound_case(computed_dim=reference_dim, computed_rank=admitted_rank, use_f01=true)
    z3_over_with = z3_bound_case(computed_dim=reference_dim, computed_rank=over_rank, use_f01=true)
    z3_over_without = z3_bound_case(computed_dim=reference_dim, computed_rank=over_rank, use_f01=false)

    all_pass = (
        identity_residual <= TOL &&
        all(abs.(traces .- 1.0) .<= TOL) &&
        all(min_eigs .>= -TOL) &&
        all(hermitian_residuals .<= TOL) &&
        all(all_ranks .<= reference_dim) &&
        admitted_rank == reference_dim &&
        over_rank == reference_dim + 1 &&
        padded_dim == reference_dim + 1 &&
        z3_admitted == "sat" &&
        z3_over_with == "unsat" &&
        z3_over_without == "sat" &&
        dropped_class_count < full_class_count
    )

    payload = Dict(
        "schema_version" => "engine_leg_result_v1",
        "rung_id" => "foundation_r1_f01_finitude",
        "engine" => "julia",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => string(now(UTC)),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "julia_project" => Base.active_project(),
        "packages_used" => ["QuantumOptics", "Z3", "LinearAlgebra", "JSON", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "M" => Dict(
            "description" => "finite QuantumOptics probe family on a d=3 carrier",
            "probe_names" => probe_names,
            "probe_count" => length(probes),
            "carrier_dimension" => reference_dim,
            "identity_residual_projectors_only" => identity_residual,
            "identity_residual" => identity_residual,
            "resolves_identity" => identity_residual <= TOL,
            "probe_vectors" => vectors,
            "computed_dimension_source" => "size(dense(rho_a).data, 1)",
        ),
        "C" => Dict(
            "trace_equals_one" => all(abs.(traces .- 1.0) .<= TOL),
            "psd" => all(min_eigs .>= -TOL),
            "hermitian" => all(hermitian_residuals .<= TOL),
            "normalization" => identity_residual <= TOL,
            "rung_specific_constraint" => "F01 admits candidate iff computed support rank r <= reference carrier dimension d",
            "f01_support_bound" => "r <= d",
            "computed_admitted_ranks" => all_ranks,
            "computed_rank_source" => "QuantumOptics.eigenenergies(rho), count(eigenvalue > tol)",
        ),
        "quotient" => Dict(
            "relation" => "rho ~_M sigma iff all finite probe expectations in M match",
            "candidate_family" => admitted_names,
            "admitted_cardinality" => length(admitted),
            "class_count" => full_class_count,
            "classes" => quotient_classes,
            "drop_probe" => "X01_half",
            "drop_probe_class_count" => dropped_class_count,
        ),
        "computed_candidates" => Dict(
            "admitted_reference" => Dict(
                "name" => admitted_names[1],
                "carrier_dimension" => reference_dim,
                "computed_rank" => admitted_rank,
                "eigenvalues" => admitted_eigs,
                "f01_admitted" => admitted_rank <= reference_dim,
            ),
            "excluded_over_support" => Dict(
                "name" => "rho_over_padded_maximally_mixed_rank_4",
                "candidate_carrier_dimension" => padded_dim,
                "reference_f01_dimension" => reference_dim,
                "computed_rank" => over_rank,
                "eigenvalues" => over_eigs,
                "f01_admitted" => over_rank <= reference_dim,
            ),
        ),
        "z3" => Dict(
            "ran" => true,
            "load_bearing" => true,
            "admitted_with_f01" => z3_admitted,
            "over_support_with_f01" => z3_over_with,
            "over_support_without_f01" => z3_over_without,
            "bound_values" => Dict("d" => reference_dim, "admitted_r" => admitted_rank, "over_support_r" => over_rank),
            "integer_model" => "assert d == computed reference dimension; assert r == computed spectral rank; optional F01 asserts r <= d",
        ),
        "negative_control" => Dict(
            "erase" => "drop_f01_finite_support_constraint",
            "with_f01" => z3_over_with,
            "without_f01" => z3_over_without,
            "flipped" => z3_over_with == "unsat" && z3_over_without == "sat",
            "computed_rank_values" => Dict("d" => reference_dim, "over_support_r" => over_rank),
            "drop_probe_control" => Dict(
                "drop_probe" => "X01_half",
                "full_probe_class_count" => full_class_count,
                "drop_probe_class_count" => dropped_class_count,
                "coarsened" => dropped_class_count < full_class_count,
            ),
        ),
        "summary" => Dict(
            "all_pass" => all_pass,
            "finite_cardinality" => reference_dim,
            "computed_dim" => reference_dim,
            "computed_rank_admit" => admitted_rank,
            "computed_rank_over" => over_rank,
            "computed_padded_dim" => padded_dim,
            "all_admitted_have_finite_support" => all(all_ranks .<= reference_dim),
            "claim_ceiling" => "F01 finite support fence at micro scale; no promotion, no later-rung claim",
        ),
        "all_pass" => all_pass,
    )

    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println("wrote: $(RESULT_PATH)")
    println("JULIA_F01_DONE all_pass=$(all_pass) d=$(reference_dim) admitted_r=$(admitted_rank) over_r=$(over_rank) flip=$(z3_over_with)->$(z3_over_without)")
    return all_pass ? 0 : 2
end

exit(main())
