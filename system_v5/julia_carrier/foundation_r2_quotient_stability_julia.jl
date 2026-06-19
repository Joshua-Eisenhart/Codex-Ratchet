#!/usr/bin/env julia
# object_id: foundation_r2_quotient_stability_v2
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using Z3

const OBJECT_ID = "foundation_r2_quotient_stability_v2"
const ENGINE = "julia"
const RUNG_ID = "foundation_r2_quotient_stability_v2"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_r2_quotient_stability_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_r2_quotient_stability_julia_results.json")
const TOL = 1.0e-10
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const BASIS = NLevelBasis(2)

rounded(x; digits = 12) = round(Float64(real(x)); digits = digits)

function ket(label::String)
    z0 = basisstate(BASIS, 1)
    z1 = basisstate(BASIS, 2)
    if label == "z0"
        return z0
    elseif label == "z1"
        return z1
    elseif label == "x_plus"
        return normalize(z0 + z1)
    elseif label == "x_minus"
        return normalize(z0 - z1)
    elseif label == "y_plus"
        return normalize(z0 + im * z1)
    elseif label == "y_minus"
        return normalize(z0 - im * z1)
    end
    error("unknown ket label: $label")
end

density(label::String) = dm(ket(label))

function candidates()
    id2 = identityoperator(BASIS)
    [
        Dict{String,Any}("id" => "pure_z0", "rho" => density("z0")),
        Dict{String,Any}("id" => "pure_z1", "rho" => density("z1")),
        Dict{String,Any}("id" => "pure_x_plus", "rho" => density("x_plus")),
        Dict{String,Any}("id" => "pure_x_minus", "rho" => density("x_minus")),
        Dict{String,Any}("id" => "pure_y_plus", "rho" => density("y_plus")),
        Dict{String,Any}("id" => "pure_y_minus", "rho" => density("y_minus")),
        Dict{String,Any}("id" => "maximally_mixed", "rho" => 0.5 * id2),
    ]
end

function active_probe_family()
    [Dict{String,Any}("name" => "Z0", "effect" => dm(ket("z0")), "description" => "computational-basis |0><0| projector")]
end

function expectation_table(rows::AbstractVector, probes::AbstractVector)
    [[rounded(expect(probe["effect"], row["rho"])) for probe in probes] for row in rows]
end

function apply_unitary(rho, unitary)
    unitary * rho * dagger(unitary)
end

function image_rows(rows::AbstractVector, unitary)
    [Dict{String,Any}("id" => row["id"], "rho" => apply_unitary(row["rho"], unitary)) for row in rows]
end

signature_key(sig) = JSON.json(sig)

function quotient(rows::AbstractVector, probes::AbstractVector, name::String)
    table = isempty(probes) ? [Any[] for _ in rows] : expectation_table(rows, probes)
    classes = Dict{String,Dict{String,Any}}()
    for (row, sig) in zip(rows, table)
        key = signature_key(sig)
        if !haskey(classes, key)
            classes[key] = Dict{String,Any}("members" => String[], "signature" => sig)
        end
        push!(classes[key]["members"], String(row["id"]))
    end
    ordered = Any[]
    for (idx, key) in enumerate(sort(collect(keys(classes))))
        push!(ordered, Dict{String,Any}(
            "class_id" => "$(name)_q$(idx - 1)",
            "members" => sort(classes[key]["members"]),
            "signature" => classes[key]["signature"],
        ))
    end
    Dict{String,Any}("name" => name, "probe_names" => [probe["name"] for probe in probes], "class_count" => length(ordered), "classes" => ordered)
end

function relation_from_table(table::AbstractVector)
    n = length(table)
    [table[i] == table[j] for i in 1:n, j in 1:n]
end

function relation_report(rel::Matrix{Bool})
    n = size(rel, 1)
    reflexive = all(rel[i, i] for i in 1:n)
    symmetric = all((!rel[i, j]) || rel[j, i] for i in 1:n, j in 1:n)
    transitive = all((!rel[i, j]) || (!rel[j, k]) || rel[i, k] for i in 1:n, j in 1:n, k in 1:n)
    Dict{String,Any}("reflexive" => reflexive, "symmetric" => symmetric, "transitive" => transitive, "is_equivalence_relation" => reflexive && symmetric && transitive)
end

function stability_report(base_rel::Matrix{Bool}, image_rel::Matrix{Bool}, ids::Vector{String})
    violating = Any[]
    for i in eachindex(ids), j in eachindex(ids)
        if base_rel[i, j] && !image_rel[i, j]
            push!(violating, Dict{String,Any}("left" => ids[i], "right" => ids[j]))
        end
    end
    Dict{String,Any}("stable" => isempty(violating), "violating_pairs" => violating)
end

function constraints_report(rows::AbstractVector, probes::AbstractVector)
    details = Any[]
    for row in rows
        mat = Matrix(row["rho"].data)
        eigs = eigvals(Hermitian((mat + mat') / 2))
        push!(details, Dict{String,Any}(
            "id" => row["id"],
            "trace_residual" => abs(real(tr(mat)) - 1.0),
            "hermitian_residual" => norm(mat - mat'),
            "min_eigenvalue" => minimum(real.(eigs)),
            "active_expectations" => [rounded(expect(probe["effect"], row["rho"])) for probe in probes],
            "psd" => minimum(real.(eigs)) >= -TOL,
        ))
    end
    Dict{String,Any}(
        "trace_one" => all(row["trace_residual"] <= TOL for row in details),
        "hermitian" => all(row["hermitian_residual"] <= TOL for row in details),
        "psd" => all(row["psd"] for row in details),
        "details" => details,
    )
end

function unitary_residual(unitary)
    mat = Matrix(unitary.data)
    norm(mat' * mat - Matrix(I, 2, 2))
end

function real_sort(ctx)
    Z3.Sort(ctx, Z3.Libz3.Z3_mk_real_sort(Z3.ref(ctx)))
end

function real_var(ctx, name::String)
    rs = real_sort(ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_const(Z3.ref(ctx), Z3.to_symbol(name, ctx), rs.ast))
end

function real_val(ctx, value)
    rs = real_sort(ctx)
    if abs(value - 0.0) <= TOL
        literal = "0"
    elseif abs(value - 0.5) <= TOL
        literal = "1/2"
    elseif abs(value - 1.0) <= TOL
        literal = "1"
    else
        literal = string(round(Float64(value); digits = 12))
    end
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_numeral(Z3.ref(ctx), literal, rs.ast))
end

function z3_vars(ctx, prefix::String, table::AbstractVector)
    vars = [[real_var(ctx, "$(prefix)_e_$(i)_$(m)") for m in eachindex(table[i])] for i in eachindex(table)]
    constraints = Z3.Expr[]
    for i in eachindex(table), m in eachindex(table[i])
        push!(constraints, vars[i][m] == real_val(ctx, table[i][m]))
    end
    vars, constraints
end

function z3_rel(ctx, vars, i::Int, j::Int)
    terms = Z3.Expr[vars[i][m] == vars[j][m] for m in eachindex(vars[i])]
    isempty(terms) ? Z3.BoolVal(true, ctx) : Z3.And(terms)
end

function z3_no_violation(base_table::AbstractVector, image_table::AbstractVector)
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    base_vars, base_constraints = z3_vars(ctx, "base", base_table)
    image_vars, image_constraints = z3_vars(ctx, "image", image_table)
    for req in vcat(base_constraints, image_constraints)
        Z3.add(solver, req)
    end
    n = length(base_table)
    violations = Z3.Expr[]
    for i in 1:n
        push!(violations, Z3.Not(z3_rel(ctx, base_vars, i, i)))
    end
    for i in 1:n, j in 1:n
        push!(violations, Z3.And(Z3.Expr[z3_rel(ctx, base_vars, i, j), Z3.Not(z3_rel(ctx, base_vars, j, i))]))
    end
    for i in 1:n, j in 1:n, k in 1:n
        push!(violations, Z3.And(Z3.Expr[z3_rel(ctx, base_vars, i, j), z3_rel(ctx, base_vars, j, k), Z3.Not(z3_rel(ctx, base_vars, i, k))]))
    end
    for i in 1:n, j in 1:n
        push!(violations, Z3.And(Z3.Expr[z3_rel(ctx, base_vars, i, j), Z3.Not(z3_rel(ctx, image_vars, i, j))]))
    end
    Z3.add(solver, Z3.Or(violations))
    Dict{String,Any}("verdict" => string(Z3.check(solver)), "asserted_real_equalities" => length(base_constraints) + length(image_constraints), "violation_terms" => length(violations))
end

function z3_stability_violation(base_table::AbstractVector, image_table::AbstractVector, ids::Vector{String})
    ctx = Z3.Context()
    solver = Z3.Solver(ctx)
    base_vars, base_constraints = z3_vars(ctx, "bad_base", base_table)
    image_vars, image_constraints = z3_vars(ctx, "bad_image", image_table)
    for req in vcat(base_constraints, image_constraints)
        Z3.add(solver, req)
    end
    n = length(base_table)
    terms = Z3.Expr[]
    pairs = Any[]
    for i in 1:n, j in 1:n
        push!(terms, Z3.And(Z3.Expr[z3_rel(ctx, base_vars, i, j), Z3.Not(z3_rel(ctx, image_vars, i, j))]))
        push!(pairs, Dict{String,Any}("indices" => [i - 1, j - 1], "ids" => [ids[i], ids[j]]))
    end
    Z3.add(solver, Z3.Or(terms))
    verdict = string(Z3.check(solver))
    witness = nothing
    if verdict == "sat"
        base_rel = relation_from_table(base_table)
        image_rel = relation_from_table(image_table)
        for idx in eachindex(pairs)
            i = pairs[idx]["indices"][1] + 1
            j = pairs[idx]["indices"][2] + 1
            if base_rel[i, j] && !image_rel[i, j]
                witness = pairs[idx]
                break
            end
        end
    end
    Dict{String,Any}("verdict" => verdict, "witness" => witness, "asserted_real_equalities" => length(base_constraints) + length(image_constraints))
end

function main()
    rows = candidates()
    probes = active_probe_family()
    ids = [String(row["id"]) for row in rows]
    phase = DenseOperator(BASIS, ComplexF64[1 0; 0 im])
    hadamard = DenseOperator(BASIS, ComplexF64[1 1; 1 -1] ./ sqrt(2.0))

    base_table = expectation_table(rows, probes)
    admitted_table = expectation_table(image_rows(rows, phase), probes)
    nonadmitted_table = expectation_table(image_rows(rows, hadamard), probes)
    base_rel = relation_from_table(base_table)
    admitted_rel = relation_from_table(admitted_table)
    nonadmitted_rel = relation_from_table(nonadmitted_table)
    q = quotient(rows, probes, "active_M_Z0")
    dropped_q = quotient(rows, Any[], "dropped_M_empty")
    constraints = constraints_report(rows, probes)
    equivalence = relation_report(base_rel)
    admitted_stability = stability_report(base_rel, admitted_rel, ids)
    nonadmitted_stability = stability_report(base_rel, nonadmitted_rel, ids)
    z3_main = z3_no_violation(base_table, admitted_table)
    z3_bad_op = z3_stability_violation(base_table, nonadmitted_table, ids)
    proof_encoding_note = "Julia Z3.jl creates Real expectation variables e[i,O] and e_post[i,O], asserts they equal QuantumOptics-computed Tr(rho_i O) values, and defines rho_i ~ rho_j inside Z3 as conjunctions of Real equalities; no precomputed Bool relation matrix is bound to solver Bools. cvc5 is run in the JAX crossover leg."
    all_pass = constraints["trace_one"] &&
        constraints["hermitian"] &&
        constraints["psd"] &&
        equivalence["is_equivalence_relation"] &&
        admitted_stability["stable"] &&
        !nonadmitted_stability["stable"] &&
        q["class_count"] == 3 &&
        dropped_q["class_count"] == 1 &&
        z3_main["verdict"] == "unsat" &&
        z3_bad_op["verdict"] == "sat"

    result = Dict{String,Any}(
        "schema_version" => "engine_leg_result_v1",
        "object_id" => OBJECT_ID,
        "engine" => ENGINE,
        "rung_id" => RUNG_ID,
        "classification" => CLASSIFICATION,
        "generated_at" => string(now(UTC)),
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "packages_used" => ["QuantumOptics", "Z3", "JSON", "LinearAlgebra", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "M" => Dict{String,Any}("active_probe_family" => ["Z0"], "probes" => [Dict{String,Any}("name" => "Z0", "effect" => "|0><0|")], "dropped_probe_family" => []),
        "C" => Dict{String,Any}(
            "state_constraints" => ["trace=1", "PSD", "Hermitian"],
            "admitted_operation" => "phase_Z_pi_over_2",
            "nonadmitted_control_operation" => "Hadamard",
            "rung_specific_constraint" => "active-M equivalence must be stable under admitted operations",
            "constraints_hold" => constraints,
            "operation_constraints_hold" => Dict{String,Any}(
                "admitted_unitary_residual" => unitary_residual(phase),
                "nonadmitted_control_unitary_residual" => unitary_residual(hadamard),
                "admitted_operation_stable" => admitted_stability["stable"],
                "nonadmitted_operation_stable" => nonadmitted_stability["stable"],
            ),
        ),
        "S" => Dict{String,Any}("ids" => ids, "size" => length(ids), "density_matrix_shape" => [2, 2]),
        "expectations" => Dict{String,Any}("active_M" => base_table, "post_admitted_operation" => admitted_table, "post_nonadmitted_operation" => nonadmitted_table, "row_ids" => ids, "probe_order" => ["Z0"]),
        "quotient" => q,
        "S_quotient" => Dict{String,Any}("classes" => q["classes"], "class_count" => q["class_count"]),
        "equivalence" => equivalence,
        "stability" => Dict{String,Any}("admitted_operation" => admitted_stability, "nonadmitted_operation" => nonadmitted_stability),
        "smt" => Dict{String,Any}(
            "julia_z3" => Dict{String,Any}(
                "main_no_violation_verdict" => z3_main["verdict"],
                "main_asserted_real_equalities" => z3_main["asserted_real_equalities"],
                "main_violation_terms" => z3_main["violation_terms"],
                "nonadmitted_stability_violation_verdict" => z3_bad_op["verdict"],
                "nonadmitted_stability_witness" => z3_bad_op["witness"],
                "load_bearing" => true,
            ),
        ),
        "negative_control_flip" => Dict{String,Any}(
            "active_M_class_count" => q["class_count"],
            "drop_M_class_count" => dropped_q["class_count"],
            "drop_M_changed_quotient" => q["class_count"] > dropped_q["class_count"],
            "admitted_operation_stable" => admitted_stability["stable"],
            "nonadmitted_operation_stable" => nonadmitted_stability["stable"],
            "z3_main_verdict" => z3_main["verdict"],
            "cvc5_main_verdict" => "run_in_jax_crossover_leg",
            "z3_nonadmitted_violation_verdict" => z3_bad_op["verdict"],
            "cvc5_nonadmitted_violation_verdict" => "run_in_jax_crossover_leg",
        ),
        "proof_encoding_note" => proof_encoding_note,
        "values" => Dict{String,Any}(
            "class_count" => q["class_count"],
            "drop_M_class_count" => dropped_q["class_count"],
            "admitted_stable" => admitted_stability["stable"],
            "nonadmitted_stable" => nonadmitted_stability["stable"],
            "z3_main_verdict" => z3_main["verdict"],
            "z3_nonadmitted_violation_verdict" => z3_bad_op["verdict"],
        ),
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict{String,Any}(
            "QuantumOptics" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing density matrices, projective expectations, and unitary image computation"),
            "Z3" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "load-bearing Real expectation-variable proof over QuantumOptics-computed Tr(rho O) values"),
            "LinearAlgebra" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive Hermitian/PSD residual checks"),
            "JSON" => Dict{String,Any}("tried" => true, "used" => true, "reason" => "supportive result serialization"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}("QuantumOptics" => "load_bearing", "Z3" => "load_bearing", "LinearAlgebra" => "supportive", "JSON" => "supportive"),
    )
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("FOUNDATION_R2_JULIA_V2_DONE all_pass=$(all_pass) class_count=$(q["class_count"]) drop_M_class_count=$(dropped_q["class_count"]) z3_main=$(z3_main["verdict"]) bad_op_z3=$(z3_bad_op["verdict"])")
    return all_pass ? 0 : 2
end

exit(main())
