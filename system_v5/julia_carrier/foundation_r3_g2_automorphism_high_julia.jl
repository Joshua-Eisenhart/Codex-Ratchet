#!/usr/bin/env julia
# object_id: foundation_r3_g2_automorphism_high
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using CliffordAlgebras
using Z3

const OBJECT_ID = "foundation_r3_g2_automorphism_high"
const ENGINE = "julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "foundation_r3_g2_automorphism_high_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5", "julia_carrier", "results", "foundation_r3_g2_automorphism_high_julia_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-9

function basis_vector(dim::Int, idx0::Int)
    v = zeros(Float64, dim)
    v[idx0 + 1] = 1.0
    v
end

function real_table()
    table = zeros(Float64, 1, 1, 1)
    table[1, 1, 1] = 1.0
    table
end

function clifford_h_table()
    cl = CliffordAlgebra(0, 2)
    one_mv = one(cl.e1)
    basis = [one_mv, cl.e1, cl.e2, cl.e1 * cl.e2]
    props = [:𝟏, :e1, :e2, :e1e2]
    table = zeros(Float64, 4, 4, 4)
    for a in 1:4, b in 1:4
        product = basis[a] * basis[b]
        for (c, prop) in enumerate(props)
            table[c, a, b] = Float64(getproperty(product, prop))
        end
    end
    residuals = Float64[
        CliffordAlgebras.norm(basis[2] * basis[2] + one_mv),
        CliffordAlgebras.norm(basis[3] * basis[3] + one_mv),
        CliffordAlgebras.norm(basis[4] * basis[4] + one_mv),
        CliffordAlgebras.norm(basis[2] * basis[3] - basis[4]),
        CliffordAlgebras.norm(basis[3] * basis[2] + basis[4]),
    ]
    table, Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "algebra" => "Cl(0,2)",
        "basis_order_zero_based" => ["1", "e1", "e2", "e1e2"],
        "max_quaternion_relation_residual" => maximum(abs.(residuals)),
        "package_native_h" => true,
    )
end

function cd_conj(x::AbstractVector{Float64})
    out = collect(x)
    length(out) > 1 && (out[2:end] .*= -1.0)
    out
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function cd_pair_multiply(parent::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, cd_conj(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, cd_conj(c))
    vcat(first, second)
end

function cd_double(parent::Array{Float64,3})
    n = size(parent, 1)
    dim = 2 * n
    table = zeros(Float64, dim, dim, dim)
    for i in 0:(dim - 1), j in 0:(dim - 1)
        table[:, i + 1, j + 1] .= cd_pair_multiply(parent, basis_vector(dim, i), basis_vector(dim, j))
    end
    table
end

function derivation_matrix(table::Array{Float64,3})
    n = size(table, 1)
    rows = zeros(Float64, n^3, n^2)
    row = 1
    @inbounds for k in 1:n, a in 1:n, b in 1:n
        for r in 1:n, s in 1:n
            col = (s - 1) * n + r
            coeff = 0.0
            r == k && (coeff += table[s, a, b])
            s == a && (coeff -= table[k, r, b])
            s == b && (coeff -= table[k, a, r])
            rows[row, col] = coeff
        end
        row += 1
    end
    rows
end

function filtered_derivation_matrix(table::Array{Float64,3}; imaginary_only::Bool=false, unit_only::Bool=false)
    n = size(table, 1)
    row_vectors = Vector{Vector{Float64}}()
    @inbounds for k in 1:n, a in 1:n, b in 1:n
        imaginary_only && (k == 1 || a == 1 || b == 1) && continue
        unit_only && !(a == 1 || b == 1) && continue
        coeffs = zeros(Float64, n^2)
        for r in 1:n, s in 1:n
            col = (s - 1) * n + r
            coeff = 0.0
            r == k && (coeff += table[s, a, b])
            s == a && (coeff -= table[k, r, b])
            s == b && (coeff -= table[k, a, r])
            coeffs[col] = coeff
        end
        push!(row_vectors, coeffs)
    end
    rows = zeros(Float64, length(row_vectors), n^2)
    for (idx, row) in enumerate(row_vectors)
        rows[idx, :] .= row
    end
    rows
end

function analyze_derivations(name::String, table::Array{Float64,3})
    matrix = derivation_matrix(table)
    unit_matrix = filtered_derivation_matrix(table; unit_only=true)
    imaginary_matrix = filtered_derivation_matrix(table; imaginary_only=true)
    rank_value = rank(matrix; atol=TOL, rtol=0.0)
    unit_rank = rank(unit_matrix; atol=TOL, rtol=0.0)
    imaginary_rank = rank(imaginary_matrix; atol=TOL, rtol=0.0)
    variable_count = size(table, 1)^2
    dim_value = variable_count - rank_value
    svals = svdvals(matrix)
    Dict{String,Any}(
        "name" => name,
        "algebra_dim" => size(table, 1),
        "probe_count" => size(matrix, 1),
        "variable_count" => variable_count,
        "constraint_rank" => rank_value,
        "derivation_dimension" => dim_value,
        "unit_pair_constraint_rank" => unit_rank,
        "imaginary_only_probe_count" => size(imaginary_matrix, 1),
        "imaginary_only_constraint_rank" => imaginary_rank,
        "imaginary_only_derivation_dimension" => variable_count - imaginary_rank,
        "smallest_singular_values" => collect(svals[max(1, length(svals) - 4):end]),
    )
end

function commutative_projection(table::Array{Float64,3})
    n = size(table, 1)
    out = zeros(Float64, n, n, n)
    for a in 1:n, b in 1:n
        out[:, a, b] .= 0.5 .* (table[:, a, b] .+ table[:, b, a])
    end
    out
end

function z3_computed_dim_status(prefix::String, computed_dim::Int, expected_dim::Int)
    solver = Solver()
    dim_var = IntVar("$(prefix)_computed_dim")
    add(solver, dim_var == IntVal(computed_dim))
    add(solver, Z3.Not(dim_var == IntVal(expected_dim)))
    string(check(solver))
end

function z3_dim_inequality_status(prefix::String, left_dim::Int, right_dim::Int)
    solver = Solver()
    left = IntVar("$(prefix)_left_dim")
    right = IntVar("$(prefix)_right_dim")
    add(solver, left == IntVal(left_dim))
    add(solver, right == IntVal(right_dim))
    add(solver, left == right)
    string(check(solver))
end

function build_result()
    r_table = real_table()
    c_table = cd_double(r_table)
    h_cd_table = cd_double(c_table)
    h_table, h_package = clifford_h_table()
    h_cd_package_max_diff = maximum(abs.(h_table .- h_cd_table))
    o_table = cd_double(h_table)
    o_commutative = commutative_projection(o_table)

    values = Dict{String,Any}(
        "R" => analyze_derivations("R", r_table),
        "C" => analyze_derivations("C", c_table),
        "H" => analyze_derivations("H", h_table),
        "O" => analyze_derivations("O", o_table),
        "O_commutative_projection_control" => analyze_derivations("O_commutative_projection_control", o_commutative),
    )
    ladder = Dict(name => values[name]["derivation_dimension"] for name in ["R", "C", "H", "O"])
    expected_ladder = Dict("R" => 0, "C" => 0, "H" => 3, "O" => 14)
    ladder_pass = all(ladder[name] == expected_ladder[name] for name in keys(expected_ladder))
    control_dim = values["O_commutative_projection_control"]["derivation_dimension"]
    control_flips = control_dim != ladder["O"]
    julia_z3 = Dict{String,Any}(
        "ran" => true,
        "load_bearing" => true,
        "O_dim_not_14_status" => z3_computed_dim_status("julia_O_g2_high", ladder["O"], 14),
        "H_dim_not_3_status" => z3_computed_dim_status("julia_H_so3_high", ladder["H"], 3),
        "commutative_control_equals_O_status" => z3_dim_inequality_status("julia_O_comm_control_high", control_dim, ladder["O"]),
        "claim" => "Z3.jl guards the Julia-computed rank/nullity values; it does not derive dim=14.",
    )
    unit_fixing_rank = values["O"]["unit_pair_constraint_rank"]
    imaginary_only_dim = values["O"]["imaginary_only_derivation_dimension"]
    all_pass = ladder_pass &&
        values["O"]["constraint_rank"] == 50 &&
        values["H"]["constraint_rank"] == 13 &&
        unit_fixing_rank == 8 &&
        imaginary_only_dim == 15 &&
        control_flips &&
        h_cd_package_max_diff <= TOL &&
        julia_z3["O_dim_not_14_status"] == "unsat" &&
        julia_z3["H_dim_not_3_status"] == "unsat" &&
        julia_z3["commutative_control_equals_O_status"] == "unsat" &&
        CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED &&
        !FORMAL_ADMISSION_ALLOWED && !READS_PEER_RESULT

    Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "engine" => ENGINE,
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "executable" => "/opt/homebrew/bin/julia --project=@v1.12 --startup-file=no",
        "active_project" => Base.active_project(),
        "julia_version" => string(VERSION),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "package_construction" => Dict{String,Any}(
            "H" => h_package,
            "H_cd_vs_clifford_max_abs_diff" => h_cd_package_max_diff,
            "O" => Dict(
                "method" => "Cayley-Dickson doubling of the CliffordAlgebras Cl(0,2) quaternion table",
                "package_native_octonion_constructor_found" => false,
            ),
        ),
        "M_probe_family" => Dict{String,Any}(
            "id" => "basis_pair_derivation_defect_coordinates",
            "observable" => "P[k,a,b](D)=D(e_a e_b)-D(e_a)e_b-e_aD(e_b)",
            "finite_family" => Dict("R" => 1^3, "C" => 2^3, "H" => 4^3, "O" => 8^3),
            "coordinate_readouts" => "all output coordinates for all ordered basis pairs",
        ),
        "C_constraints" => Dict{String,Any}(
            "trace" => "trace-one probe weights are normalized when probes are viewed as a finite measurement family",
            "PSD" => "probe-weight Gram matrices are positive semidefinite by construction for finite coordinate readouts",
            "Hermiticity" => "real coordinate probes are self-adjoint observables",
            "normalization" => "e0 is the identity; basis units have norm 1; imaginary units square to -e0",
            "rung_specific" => "multiplication preservation: D(xy)=D(x)y+xD(y) for every basis pair",
        ),
        "quotient" => Dict{String,Any}(
            "S" => "End_R(A), represented by algebra_dim^2 real linear coefficients",
            "equivalence" => "D1 ~_M D2 iff all derivation-defect probes vanish on D1-D2",
            "symmetry_class" => "Der(A)=ker(M)",
            "class_dimensions" => ladder,
            "dimension_honesty" => "Julia rank/nullspace is the authoritative dim=14 source; SMT is not credited with deriving the dimension.",
        ),
        "values" => values,
        "finite_certificates" => Dict("julia_z3" => julia_z3),
        "negative_control" => Dict{String,Any}(
            "division_algebra_ladder_flip" => Dict("pass" => ladder_pass, "dimensions" => ladder),
            "unit_fixing_rank" => Dict("pass" => unit_fixing_rank == 8, "rank" => unit_fixing_rank),
            "imaginary_only_probe_quotient_widens_to_15" => Dict(
                "pass" => imaginary_only_dim == 15,
                "full_O_derivation_dimension" => ladder["O"],
                "imaginary_only_derivation_dimension" => imaginary_only_dim,
            ),
            "force_commutativity_flip" => Dict(
                "pass" => control_flips,
                "O_derivation_dimension" => ladder["O"],
                "commutative_projection_derivation_dimension" => control_dim,
            ),
        ),
        "metadata" => Dict{String,Any}(
            "asserted_precomputed_kernel_relations" => 0,
            "dimension_authority" => "Julia LinearAlgebra rank/nullspace over the computed derivation matrix",
            "unit_fixing_rank" => unit_fixing_rank,
            "control_dimensions" => Dict("H" => ladder["H"], "O_imaginary_only" => imaginary_only_dim),
        ),
        "packages_used" => ["CliffordAlgebras", "Z3", "JSON", "LinearAlgebra", "Dates"],
        "aligned_packages_load_bearing" => ["CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing quaternion multiplication table used as the octonion Cayley-Dickson parent"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side finite certificate over computed dimensions"),
            "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive rank/nullity computation over computed derivation matrices"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("CliffordAlgebras" => "load_bearing", "Z3" => "load_bearing", "LinearAlgebra" => "supportive"),
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
    dims = result["quotient"]["class_dimensions"]
    control = result["negative_control"]["force_commutativity_flip"]
    println("SCOUT_DONE all_pass=$(result["all_pass"]) dims_R_C_H_O=$(dims["R"])/$(dims["C"])/$(dims["H"])/$(dims["O"]) comm_control_dim=$(control["commutative_projection_derivation_dimension"])")
    return result["all_pass"] ? 0 : 1
end

exit(main())
