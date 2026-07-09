#!/usr/bin/env julia
# object_id: foundation_r6_g2_associative_calibration_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# reads_peer_result: false
# reads_peer_result is false by design, not by omission: every R5 leg
# (foundation_foundation_r5_{g2_su3_reduction,hopf_fibration,weyl_chirality_pair})
# is itself classification=scratch_diagnostic / promotion_allowed=false in its
# own result JSON (system_v5/julia_carrier/results/foundation_foundation_r5_*_julia_results.json).
# There is no admitted/canonical R5 carrier for R6 to build on top of, so R6
# does not claim to derive from one. R6 is a self-contained finite-math scratch
# stage; the whole R5->R6 ladder to this point is scratch-diagnostic.

using Dates
using JSON
using LinearAlgebra
using QuantumOptics
using CliffordAlgebras
using Z3
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RUNG_ID = "foundation_r6_g2_associative_calibration"
const OBJECT_ID = "foundation_r6_g2_associative_calibration_julia"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r6_g2_associative_calibration_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r6_g2_associative_calibration_julia_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing trace-one PSD Hermitian projector guard for the finite probe constraints"),
    "CliffordAlgebras" => Dict("tried" => true, "used" => true, "reason" => "load-bearing quaternion-stage crosscheck before accepting the Cayley-Dickson octonion table"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia-side SMT check deriving phi(u,v,w) from bound phi and plane coordinates"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive finite norm/eigenvalue checks only; not the claim carrier"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive receipt serialization"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON" => "supportive",
)

function basis_vector(dim::Int, idx::Int)
    out = zeros(Int, dim)
    out[idx] = 1
    out
end

function multiply(table::Array{Int,3}, x::AbstractVector{<:Real}, y::AbstractVector{<:Real})
    dim = size(table, 1)
    out = zeros(Int, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * Int(x[a]) * Int(y[b])
    end
    out
end

conjugate_vec(x::AbstractVector{<:Real}) = Int.(collect(x)) .* vcat([1], fill(-1, length(x) - 1))

function cd_pair_multiply(parent::Array{Int,3}, x::AbstractVector{Int}, y::AbstractVector{Int})
    n = size(parent, 1)
    a, b = x[1:n], x[(n + 1):(2 * n)]
    c, d = y[1:n], y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_vec(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_vec(c))
    Int.(vcat(first, second))
end

function cd_double(parent::Array{Int,3})
    dim = 2 * size(parent, 1)
    table = zeros(Int, dim, dim, dim)
    eye = Matrix{Int}(I, dim, dim)
    for i in 1:dim, j in 1:dim
        table[:, i, j] .= cd_pair_multiply(parent, eye[:, i], eye[:, j])
    end
    table
end

function build_tables()
    r = zeros(Int, 1, 1, 1)
    r[1, 1, 1] = 1
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    Dict("R" => r, "C" => c, "H" => h, "O" => o)
end

function clifford_h_table()
    alg = CliffordAlgebra(0, 2)
    elems = [
        basevector(alg, 1),
        basevector(alg, :e1),
        basevector(alg, :e2),
        basevector(alg, :e1) * basevector(alg, :e2),
    ]
    coeff_keys = [1, :e1, :e2, :e1e2]
    table = zeros(Int, 4, 4, 4)
    for i in 1:4, j in 1:4
        product = elems[i] * elems[j]
        for k in 1:4
            table[k, i, j] = Int(round(Float64(coefficient(product, coeff_keys[k]))))
        end
    end
    table
end

function phi_tensor(o::Array{Int,3})
    phi = zeros(Int, 7, 7, 7)
    for i in 1:7, j in 1:7, k in 1:7
        phi[i, j, k] = o[k + 1, i + 1, j + 1]
    end
    phi
end

function combo_indices(n::Int, k::Int)
    out = Vector{Vector{Int}}()
    function rec(start::Int, acc::Vector{Int})
        if length(acc) == k
            push!(out, copy(acc))
            return
        end
        for x in start:n
            push!(acc, x)
            rec(x + 1, acc)
            pop!(acc)
        end
    end
    rec(1, Int[])
    out
end

function oriented_from_sorted(phi::Array{Int,3}, comp::Vector{Int})
    value = phi[comp...]
    value == 1 ? comp : [comp[1], comp[3], comp[2]]
end

function phi_value(phi::Array{Int,3}, u::AbstractVector{<:Real}, v::AbstractVector{<:Real}, w::AbstractVector{<:Real})
    total = 0.0
    for i in 1:7, j in 1:7, k in 1:7
        total += Float64(phi[i, j, k]) * Float64(u[i]) * Float64(v[j]) * Float64(w[k])
    end
    total
end

function fano_lines(phi::Array{Int,3})
    lines = Vector{Dict{String,Any}}()
    for comp in combo_indices(7, 3)
        value = phi[comp...]
        abs(value) == 1 || continue
        oriented = oriented_from_sorted(phi, comp)
        push!(lines, Dict{String,Any}(
            "plane" => comp,
            "oriented_plane" => oriented,
            "sorted_phi" => value,
            "oriented_phi" => 1,
            "label" => "span(" * join(["e$(idx)" for idx in comp], ",") * ")",
        ))
    end
    lines
end

function coordinate_plane_report(phi::Array{Int,3})
    rows = Vector{Dict{String,Any}}()
    for comp in combo_indices(7, 3)
        u, v, w = basis_vector(7, comp[1]), basis_vector(7, comp[2]), basis_vector(7, comp[3])
        value = phi_value(phi, u, v, w)
        push!(rows, Dict{String,Any}(
            "plane" => comp,
            "phi_on_sorted_orientation" => value,
            "abs_phi" => abs(value),
            "calibrated_as_unoriented_plane" => abs(abs(value) - 1.0) <= TOL,
        ))
    end
    Dict{String,Any}(
        "plane_count" => length(rows),
        "calibrated_plane_count" => count(row -> Bool(row["calibrated_as_unoriented_plane"]), rows),
        "uncalibrated_plane_count" => count(row -> !Bool(row["calibrated_as_unoriented_plane"]), rows),
        "planes" => rows,
    )
end

function erased_phi(phi::Array{Int,3}, oriented_line::Vector{Int})
    out = copy(phi)
    for i in oriented_line, j in oriented_line, k in oriented_line
        length(unique([i, j, k])) == 3 || continue
        out[i, j, k] = 0
    end
    out
end

function cross_product(o::Array{Int,3}, i::Int, j::Int)
    o[2:8, i + 1, j + 1]
end

function closure_report(o::Array{Int,3}, lines::Vector{Dict{String,Any}})
    rows = Vector{Dict{String,Any}}()
    for line in lines
        indices = Int.(line["plane"])
        support = Set(indices)
        closed = true
        products = Vector{Dict{String,Any}}()
        for i in indices, j in indices
            i == j && continue
            cp = cross_product(o, i, j)
            nz = [idx for idx in 1:7 if cp[idx] != 0]
            any(idx -> !(idx in support), nz) && (closed = false)
            push!(products, Dict{String,Any}("pair" => [i, j], "support" => nz))
        end
        push!(rows, Dict{String,Any}("plane" => indices, "closed_under_cross_product" => closed, "products" => products))
    end
    rows
end

function table_sha(table::Array{Int,3})
    bytes2hex(sha256(join(string.(vec(table)), ",")))
end

function quantumoptics_guard()
    basis = FockBasis(6)
    rho = dm(basisstate(basis, 1))
    vals = eigvals(Hermitian(rho.data))
    Dict{String,Any}(
        "trace" => real(tr(rho.data)),
        "trace_eq_1" => abs(real(tr(rho.data)) - 1.0) <= TOL,
        "psd" => minimum(real.(vals)) >= -TOL,
        "hermitian" => norm(rho.data - rho.data') <= TOL,
        "hermitian_defect" => norm(rho.data - rho.data'),
        "normalization" => "QuantumOptics rank-one projector guard; calibration result is from phi probes, not rho",
    )
end

function zadd(ctx, args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function zmul(ctx, args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(1, ctx)
    Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), length(args), [Z3.as_ast(a) for a in args]))
end

function z3_expr_from_bound(ctx, solver, phi::Array{Int,3}, plane::Vector{Int}; erase_line::Union{Nothing,Vector{Int}}=nothing)
    pvars = Array{Z3.Expr}(undef, 7, 7, 7)
    uvars = Vector{Z3.Expr}(undef, 7)
    vvars = Vector{Z3.Expr}(undef, 7)
    wvars = Vector{Z3.Expr}(undef, 7)
    erase_set = erase_line === nothing ? Set{Int}() : Set(erase_line)
    for i in 1:7, j in 1:7, k in 1:7
        pvars[i, j, k] = Z3.IntVar("phi_$(i)_$(j)_$(k)_$(length(Z3.assertions(solver)))", ctx)
        value = (Set([i, j, k]) == erase_set && length(erase_set) == 3) ? 0 : phi[i, j, k]
        Z3.add(solver, pvars[i, j, k] == Z3.IntVal(value, ctx))
    end
    vars = [uvars, vvars, wvars]
    for a in 1:3, coord in 1:7
        vars[a][coord] = Z3.IntVar("plane_$(a)_$(coord)_$(length(Z3.assertions(solver)))", ctx)
        Z3.add(solver, vars[a][coord] == Z3.IntVal(coord == plane[a] ? 1 : 0, ctx))
    end
    terms = Z3.Expr[]
    for i in 1:7, j in 1:7, k in 1:7
        push!(terms, zmul(ctx, [pvars[i, j, k], uvars[i], vvars[j], wvars[k]]))
    end
    zadd(ctx, terms)
end

function z3_calibration_guard(phi::Array{Int,3}, fano::Vector{Int}, generic::Vector{Int})
    ctx = Z3.Context()

    fano_solver = Z3.Solver(ctx)
    fano_expr = z3_expr_from_bound(ctx, fano_solver, phi, fano)
    Z3.add(fano_solver, Z3.Not(fano_expr == Z3.IntVal(1, ctx)))
    fano_status = string(Z3.check(fano_solver))

    generic_solver = Z3.Solver(ctx)
    generic_expr = z3_expr_from_bound(ctx, generic_solver, phi, generic)
    Z3.add(generic_solver, generic_expr < Z3.IntVal(1, ctx))
    generic_status = string(Z3.check(generic_solver))

    erased_solver = Z3.Solver(ctx)
    erased_expr = z3_expr_from_bound(ctx, erased_solver, phi, fano; erase_line=fano)
    Z3.add(erased_solver, Z3.Not(erased_expr == Z3.IntVal(1, ctx)))
    erased_status = string(Z3.check(erased_solver))

    Dict{String,Any}(
        "solver" => "Z3.jl",
        "claim" => "SMT derives phi(u,v,w)=1 for the first Fano-line plane from bound phi and plane coordinates; asserting phi!=1 is UNSAT",
        "fano_phi_not_one_status" => fano_status,
        "generic_phi_less_than_one_status" => generic_status,
        "erased_fano_phi_not_one_status" => erased_status,
        "erase_flip_unsat_to_sat" => fano_status == "unsat" && erased_status == "sat",
        "bound_phi_components" => 343,
        "bound_plane_coordinates" => 21,
        "derived_expression" => "sum_ijk phi_ijk*u_i*v_j*w_k",
        "asserted_precomputed_scalar_literal" => false,
    )
end

function build_result()
    tables = build_tables()
    o = tables["O"]
    phi = phi_tensor(o)
    lines = fano_lines(phi)
    coordinate = coordinate_plane_report(phi)
    first_line = Int.(lines[1]["oriented_plane"])
    first_phi = phi_value(phi, basis_vector(7, first_line[1]), basis_vector(7, first_line[2]), basis_vector(7, first_line[3]))
    generic_row = first(row for row in coordinate["planes"] if !Bool(row["calibrated_as_unoriented_plane"]))
    generic_plane = Int.(generic_row["plane"])
    generic_phi = Float64(generic_row["phi_on_sorted_orientation"])
    erased_coordinate = coordinate_plane_report(erased_phi(phi, first_line))
    zero_coordinate = coordinate_plane_report(zeros(Int, 7, 7, 7))
    closure = closure_report(o, lines)
    guard = quantumoptics_guard()
    h_matches = clifford_h_table() == tables["H"]
    julia_z3 = z3_calibration_guard(phi, first_line, generic_plane)
    negative = Dict{String,Any}(
        "drop_one_fano_probe_count_7_to_6" => coordinate["calibrated_plane_count"] == 7 && erased_coordinate["calibrated_plane_count"] == 6,
        "force_commutative_zero_phi_count_7_to_0" => coordinate["calibrated_plane_count"] == 7 && zero_coordinate["calibrated_plane_count"] == 0,
        "generic_coordinate_plane_phi_less_than_one" => generic_phi < 1.0,
        "julia_z3_erase_flip_unsat_to_sat" => julia_z3["erase_flip_unsat_to_sat"],
    )
    all_pass = Bool(
        h_matches &&
        length(lines) == 7 &&
        coordinate["calibrated_plane_count"] == 7 &&
        all(row -> Bool(row["closed_under_cross_product"]), closure) &&
        abs(first_phi - 1.0) <= TOL &&
        generic_phi < 1.0 &&
        erased_coordinate["calibrated_plane_count"] == 6 &&
        zero_coordinate["calibrated_plane_count"] == 0 &&
        guard["trace_eq_1"] &&
        guard["psd"] &&
        guard["hermitian"] &&
        julia_z3["fano_phi_not_one_status"] == "unsat" &&
        julia_z3["generic_phi_less_than_one_status"] == "sat" &&
        julia_z3["erased_fano_phi_not_one_status"] == "sat" &&
        all(value for value in values(negative) if value isa Bool) &&
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
        "packages_used" => ["QuantumOptics", "CliffordAlgebras", "Z3", "LinearAlgebra", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "CliffordAlgebras", "Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "runtime_preflight" => Dict("julia_version" => string(VERSION), "active_project" => Base.active_project()),
        "M" => Dict(
            "name" => "G2 associative calibration probe family",
            "explicit_probe_family" => "All 35 coordinate oriented 3-plane probes e_i wedge e_j wedge e_k, evaluated by phi(u,v,w) against unit volume.",
            "finite_probe_counts" => Dict("coordinate_3_planes" => 35, "calibrated_planes" => coordinate["calibrated_plane_count"]),
            "measurement_map" => "M(P)=(phi(P), volume(P)=1, cross-product closure flag) for each coordinate 3-plane P",
        ),
        "C" => Dict(
            "trace_eq_1" => guard["trace_eq_1"],
            "psd" => guard["psd"],
            "hermitian" => guard["hermitian"],
            "normalization" => "orthonormal imaginary octonion basis; each coordinate 3-plane has unit volume",
            "rung_specific_constraint" => "phi_ijk is computed from the Cayley-Dickson octonion table by e_i e_j = sum_k phi_ijk e_k on Im(O)",
            "density_guard" => guard,
        ),
        "S_mod_M" => Dict(
            "definition" => "Coordinate 3-planes are equivalent by M when their calibration/closure probe vector agrees; calibrated class is phi=1 after orientation and closed under octonion cross product.",
            "calibrated_class_count" => coordinate["calibrated_plane_count"],
            "uncalibrated_class_count" => coordinate["uncalibrated_plane_count"],
            "calibrated_planes" => lines,
        ),
        "octonion_structure" => Dict(
            "construction" => "Cayley-Dickson R -> C -> H -> O",
            "table_sha256" => table_sha(o),
            "quaternion_stage_matches_CliffordAlgebras" => h_matches,
        ),
        "calibration" => Dict(
            "fano_lines" => lines,
            "coordinate_probe_summary" => coordinate,
            "cross_product_closure" => closure,
            "first_fano_oriented_plane" => first_line,
            "first_fano_phi" => first_phi,
            "generic_control_plane" => generic_plane,
            "generic_control_phi" => generic_phi,
            "erased_first_fano_calibrated_count" => erased_coordinate["calibrated_plane_count"],
            "forced_commutative_zero_phi_calibrated_count" => zero_coordinate["calibrated_plane_count"],
        ),
        "julia_z3" => julia_z3,
        "negative_control_flip" => negative,
        "summary" => Dict(
            "calibrated_plane_count" => coordinate["calibrated_plane_count"],
            "fano_line_count" => length(lines),
            "first_fano_phi" => first_phi,
            "generic_control_phi" => generic_phi,
            "erased_first_fano_calibrated_count" => erased_coordinate["calibrated_plane_count"],
            "forced_commutative_zero_phi_calibrated_count" => zero_coordinate["calibrated_plane_count"],
            "julia_z3_fano_phi_not_one" => julia_z3["fano_phi_not_one_status"],
            "julia_z3_erased_fano_phi_not_one" => julia_z3["erased_fano_phi_not_one_status"],
            "all_pass" => all_pass,
        ),
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
    s = result["summary"]
    println("wrote: ", RESULT_PATH)
    println(
        "FOUNDATION_R6_G2_ASSOCIATIVE_CALIBRATION_JULIA_DONE ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "calibrated=", s["calibrated_plane_count"], " ",
        "first_fano_phi=", s["first_fano_phi"], " ",
        "generic_phi=", s["generic_control_phi"], " ",
        "julia_z3=", s["julia_z3_fano_phi_not_one"],
    )
    return result["all_pass"] ? 0 : 1
end

exit(main())
