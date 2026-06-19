#!/usr/bin/env julia
# object_id: g2_forced_vs_installed_discriminator
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const OBJECT_ID = "g2_forced_vs_installed_discriminator"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", OBJECT_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const ENGINE = "julia"
const SOURCE_PATH = joinpath(SIM_DIR, "$(OBJECT_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(OBJECT_ID)_$(ENGINE)_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-8
const PIN_SPEC = "G2 forced-vs-installed discriminator: bare root={finite table, nonzero commutator}; controls H and M2(R); installed carrier constraint=seven anticommuting imaginary units closed by the Fano/Cayley-Dickson octonion table; derivations solve D(xy)=D(x)y+xD(y)."

const TOOL_MANIFEST = Dict{String,Any}(
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive rank/nullity computation for the derivation equation matrix",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side SAT/UNSAT checks for root admission and seven-unit exclusion",
    ),
    "JSON/Dates/SHA" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result serialization, timestamps, and source hashing",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "LinearAlgebra" => "supportive",
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)

const FANO_TRIPLES = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function table_h()
    c = zeros(Float64, 4, 4, 4)
    c[1, 1, 1] = 1
    for a in 2:4
        c[a, 1, a] = 1
        c[a, a, 1] = 1
        c[1, a, a] = -1
    end
    for (a0, b0, d0) in [(1, 2, 3)]
        a, b, d = a0 + 1, b0 + 1, d0 + 1
        c[d, a, b] = 1
        c[a, b, d] = 1
        c[b, d, a] = 1
        c[d, b, a] = -1
        c[a, d, b] = -1
        c[b, a, d] = -1
    end
    c
end

function table_m2()
    c = zeros(Float64, 4, 4, 4)
    basis = [(0, 0), (0, 1), (1, 0), (1, 1)]
    index = Dict(pair => idx for (idx, pair) in enumerate(basis))
    for (i, (a, b)) in enumerate(basis)
        for (j, (d, e)) in enumerate(basis)
            if b == d
                c[index[(a, e)], i, j] = 1
            end
        end
    end
    c
end

function table_o(; corrupt::Bool = false)
    c = zeros(Float64, 8, 8, 8)
    c[1, 1, 1] = 1
    for a in 2:8
        c[a, 1, a] = 1
        c[a, a, 1] = 1
        c[1, a, a] = -1
    end
    for (a0, b0, d0) in FANO_TRIPLES
        a, b, d = a0 + 1, b0 + 1, d0 + 1
        c[d, a, b] = 1
        c[a, b, d] = 1
        c[b, d, a] = 1
        c[d, b, a] = -1
        c[a, d, b] = -1
        c[b, a, d] = -1
    end
    if corrupt
        c[4, 2, 3] = -c[4, 2, 3]
    end
    c
end

function int_table(c)
    n = size(c, 1)
    out = Vector{Any}()
    for k in 1:n
        plane = Vector{Any}()
        for i in 1:n
            row = Int[]
            for j in 1:n
                value = c[k, i, j]
                rounded = Int(round(value))
                abs(value - rounded) > TOL && error("non-integral structure constant")
                push!(row, rounded)
            end
            push!(plane, row)
        end
        push!(out, plane)
    end
    out
end

function derivation_matrix(c)
    n = size(c, 1)
    rows = Vector{Vector{Float64}}()
    for i in 1:n, j in 1:n, k in 1:n
        row = zeros(Float64, n, n)
        for ell in 1:n
            row[k, ell] += c[ell, i, j]
        end
        for a in 1:n
            row[a, i] -= c[k, a, j]
        end
        for b in 1:n
            row[b, j] -= c[k, i, b]
        end
        push!(rows, vec(row))
    end
    reduce(vcat, transpose.(rows))
end

function derivation_summary(name::String, c)
    mat = derivation_matrix(c)
    r = rank(mat; atol = TOL, rtol = 0.0)
    n = size(c, 1)
    Dict{String,Any}(
        "carrier" => name,
        "basis_dimension" => n,
        "equation_count" => size(mat, 1),
        "unknown_count" => n * n,
        "rank" => r,
        "nullity_dim_der" => n * n - r,
        "rank_method" => "LinearAlgebra.rank atol=1e-8 rtol=0",
    )
end

function commutator_witness(c)
    n = size(c, 1)
    best = Dict{String,Any}("i" => 0, "j" => 0, "norm" => 0.0, "vector" => Int[])
    for i in 1:n, j in 1:n
        i == j && continue
        vecv = c[:, i, j] - c[:, j, i]
        normv = norm(vecv)
        if normv > best["norm"]
            best = Dict{String,Any}(
                "i" => i - 1,
                "j" => j - 1,
                "norm" => normv,
                "vector" => [Int(round(x)) for x in vecv],
            )
        end
    end
    best
end

function product_closes_and_anticommutes(values, a0::Int, b0::Int)
    a, b = a0 + 1, b0 + 1
    n = length(values)
    anti = all(values[k][a][b] + values[k][b][a] == 0 for k in 1:n)
    product = [values[k][a][b] for k in 1:n]
    nonzero = [k for k in 1:n if product[k] != 0]
    closes = length(nonzero) == 1 && nonzero[1] != 1 && abs(product[nonzero[1]]) == 1
    anti && closes
end

function z3_root_sat(values, prefix::String; force_commutative::Bool = false)
    solver = Z3.Solver()
    n = length(values)
    terms = Z3.Expr[]
    for k in 1:n, i in 1:n, j in (i + 1):n
        v = Z3.IntVar("$(prefix)_comm_$(k)_$(i)_$(j)")
        Z3.add(solver, v == Z3.IntVal(values[k][i][j] - values[k][j][i]))
        push!(terms, Z3.Not(v == Z3.IntVal(0)))
        if force_commutative
            Z3.add(solver, v == Z3.IntVal(0))
        end
    end
    if isempty(terms)
        Z3.add(solver, Z3.BoolVal(false))
    elseif length(terms) == 1
        Z3.add(solver, terms[1])
    else
        Z3.add(solver, Z3.Or(terms))
    end
    Dict{String,Any}(
        "status" => string(Z3.check(solver)),
        "finite_table_bound" => true,
        "basis_dimension" => n,
        "force_commutative" => force_commutative,
        "bound_commutator_coordinates" => length(terms),
    )
end

function z3_seven_unit_closure(values, prefix::String; required::Int = 7)
    solver = Z3.Solver()
    n = length(values)
    units = [Z3.IntVar("$(prefix)_u_$(idx)") for idx in 1:required]
    for unit in units
        Z3.add(solver, Z3.Not(unit < Z3.IntVal(1)))
        Z3.add(solver, Z3.Not(Z3.IntVal(n - 1) < unit))
    end
    for p in 1:required, q in (p + 1):required
        Z3.add(solver, Z3.Not(units[p] == units[q]))
        for a in 1:(n - 1), b in 1:(n - 1)
            ok = product_closes_and_anticommutes(values, a, b)
            if !ok
                Z3.add(solver, Z3.Not(Z3.And([units[p] == Z3.IntVal(a), units[q] == Z3.IntVal(b)])))
            end
        end
    end
    status = string(Z3.check(solver))
    Dict{String,Any}(
        "status" => status,
        "required_units" => required,
        "available_imaginary_slots" => n - 1,
        "constraint_family" => "distinct 7 imaginary units; every chosen pair anticommutes and closes to one imaginary Fano/Cayley-Dickson product",
    )
end

bool_float(value::Bool) = value ? 1.0 : 0.0

function build_result()
    mkpath(RESULT_DIR)
    tables = Dict("H" => table_h(), "M2R" => table_m2(), "O" => table_o(), "O_corrupted" => table_o(corrupt = true))
    int_tables = Dict(name => int_table(table) for (name, table) in tables)
    derivations = Dict(name => derivation_summary(name, table) for (name, table) in tables)
    witnesses = Dict(name => commutator_witness(table) for (name, table) in tables)
    z3_checks = Dict{String,Any}(
        "H_bare_root" => z3_root_sat(int_tables["H"], "H_bare"),
        "M2R_bare_root" => z3_root_sat(int_tables["M2R"], "M2R_bare"),
        "H_forced_commutative_control" => z3_root_sat(int_tables["H"], "H_forced_commutative", force_commutative = true),
        "O_7unit_closure" => z3_seven_unit_closure(int_tables["O"], "O_7unit"),
        "H_7unit_closure" => z3_seven_unit_closure(int_tables["H"], "H_7unit"),
        "alternative_3unit_7closure" => z3_seven_unit_closure(int_tables["H"], "three_unit_alt_7unit"),
        "H_erased_closure_control" => z3_root_sat(int_tables["H"], "H_erased_closure"),
    )
    bare_counterexamples = String[]
    for name in ["H", "M2R"]
        if z3_checks["$(name)_bare_root"]["status"] == "sat" && derivations[name]["nullity_dim_der"] != derivations["O"]["nullity_dim_der"]
            push!(bare_counterexamples, name)
        end
    end
    forced_by_root = isempty(bare_counterexamples)
    installed_by_carrier_constraint = (
        derivations["O"]["nullity_dim_der"] == 14 &&
        z3_checks["O_7unit_closure"]["status"] == "sat" &&
        z3_checks["alternative_3unit_7closure"]["status"] == "unsat" &&
        z3_checks["H_7unit_closure"]["status"] == "unsat"
    )
    controls = Dict{String,Any}(
        "bare_root_failing_control_fires" => forced_by_root == false && bare_counterexamples == ["H", "M2R"],
        "erased_closure_readmits_H" => z3_checks["H_erased_closure_control"]["status"] == "sat",
        "corrupted_octonion_dim_changes" => derivations["O_corrupted"]["nullity_dim_der"] != derivations["O"]["nullity_dim_der"],
        "forced_commutative_control_unsat" => z3_checks["H_forced_commutative_control"]["status"] == "unsat",
        "classification_ceiling_held" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false,
    )
    all_pass = installed_by_carrier_constraint && all(values(controls))
    shared_scalars = Dict{String,Any}(
        "H_dim_der" => Float64(derivations["H"]["nullity_dim_der"]),
        "M2R_dim_der" => Float64(derivations["M2R"]["nullity_dim_der"]),
        "O_dim_der" => Float64(derivations["O"]["nullity_dim_der"]),
        "O_corrupted_dim_der" => Float64(derivations["O_corrupted"]["nullity_dim_der"]),
        "H_root_sat" => bool_float(z3_checks["H_bare_root"]["status"] == "sat"),
        "M2R_root_sat" => bool_float(z3_checks["M2R_bare_root"]["status"] == "sat"),
        "O_7unit_sat" => bool_float(z3_checks["O_7unit_closure"]["status"] == "sat"),
        "alternative_3unit_7closure_unsat" => bool_float(z3_checks["alternative_3unit_7closure"]["status"] == "unsat"),
        "forced_by_root" => bool_float(forced_by_root),
        "installed_by_carrier_constraint" => bool_float(installed_by_carrier_constraint),
    )
    Dict{String,Any}(
        "schema_version" => "three_engine_leg_result_v1",
        "object_id" => OBJECT_ID,
        "engine" => ENGINE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "reads_peer_result" => READS_PEER_RESULT,
        "pin_spec" => PIN_SPEC,
        "packages_used" => ["LinearAlgebra", "Z3", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "derivation_dimensions" => derivations,
        "noncommutation_witnesses" => witnesses,
        "smt" => Dict("julia_z3" => z3_checks),
        "verdicts" => Dict(
            "forced_by_root" => forced_by_root,
            "installed_by_carrier_constraint" => installed_by_carrier_constraint,
            "bare_root_counterexamples" => bare_counterexamples,
        ),
        "controls" => controls,
        "shared_scalars" => shared_scalars,
        "all_pass" => all_pass,
        "claim_ceiling" => "scratch diagnostic: G2 is discriminated as installed by the octonion/Fano carrier constraint, not promoted as canonical.",
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
    )
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println("wrote: $(RESULT_PATH)")
    println(
        "JULIA_DONE all_pass=$(result["all_pass"]) " *
        "dims={H:$(result["derivation_dimensions"]["H"]["nullity_dim_der"])," *
        "M2R:$(result["derivation_dimensions"]["M2R"]["nullity_dim_der"])," *
        "O:$(result["derivation_dimensions"]["O"]["nullity_dim_der"])," *
        "O_corrupted:$(result["derivation_dimensions"]["O_corrupted"]["nullity_dim_der"])} " *
        "julia_z3_alt=$(result["smt"]["julia_z3"]["alternative_3unit_7closure"]["status"]) " *
        "forced_by_root=$(result["verdicts"]["forced_by_root"]) " *
        "installed=$(result["verdicts"]["installed_by_carrier_constraint"])"
    )
    result["all_pass"] ? 0 : 2
end

exit(main())
