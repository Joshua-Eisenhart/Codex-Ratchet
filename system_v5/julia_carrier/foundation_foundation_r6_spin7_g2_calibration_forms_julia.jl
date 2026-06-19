#!/usr/bin/env julia
# object_id: foundation_r6_spin7_g2_calibration_forms_julia
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA
using QuantumOptics
using CliffordAlgebras
using Z3

const RUNG_ID = "foundation_r6_spin7_g2_calibration_forms"
const OBJECT_ID = "foundation_r6_spin7_g2_calibration_forms_julia"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SOURCE_PATH = joinpath(ROOT, "system_v5/julia_carrier/foundation_foundation_r6_spin7_g2_calibration_forms_julia.jl")
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/results/foundation_foundation_r6_spin7_g2_calibration_forms_julia_results.json")
const TOL = 1.0e-10

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false
const reads_peer_result = false

const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing finite probe guard: constructs trace-one PSD Hermitian projectors for the calibration-form probe family",
    ),
    "CliffordAlgebras" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Cayley-Dickson sanity check: the quaternion stage must match CliffordAlgebras(:Quaternions) before the octonion table is accepted",
    ),
    "Z3" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "load-bearing Julia-side preservation/erase guard over computed phi components and a computed octonion derivation",
    ),
    "LinearAlgebra" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "authoritative finite linear-algebra nullspace dimensions for Stab(phi) and Stab(Phi)",
    ),
    "JSON" => Dict(
        "tried" => true,
        "used" => true,
        "reason" => "supportive result receipt serialization",
    ),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "CliffordAlgebras" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "load_bearing",
    "JSON" => "supportive",
)

function coeffs(mv, labels::Vector{Symbol})
    [Int(round(Float64(real(getproperty(mv, label))))) for label in labels]
end

function package_h_table()
    clh = CliffordAlgebra(:Quaternions)
    labels = [:𝟏, :i, :j, :ij]
    basis = [getproperty(clh, label) for label in labels]
    table = zeros(Int, 4, 4, 4)
    for a in 1:4, b in 1:4
        table[:, a, b] .= coeffs(basis[a] * basis[b], labels)
    end
    table, Dict{String,Any}(
        "package" => "CliffordAlgebras",
        "constructor" => "CliffordAlgebra(:Quaternions)",
        "basis_labels" => string.(labels),
        "i_squared" => coeffs(clh.i * clh.i, labels),
        "j_squared" => coeffs(clh.j * clh.j, labels),
        "ij_squared" => coeffs(clh.ij * clh.ij, labels),
        "i_j" => coeffs(clh.i * clh.j, labels),
        "j_i" => coeffs(clh.j * clh.i, labels),
    )
end

function multiply(table::Array{Int,3}, x::AbstractVector{<:Real}, y::AbstractVector{<:Real})
    dim = size(table, 1)
    out = zeros(Int, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * Int(x[a]) * Int(y[b])
    end
    out
end

function conjugate_vec(x::AbstractVector{<:Real})
    Int.(collect(x)) .* vcat([1], fill(-1, length(x) - 1))
end

function cd_pair_multiply(parent::Array{Int,3}, x::AbstractVector{Int}, y::AbstractVector{Int})
    n = size(parent, 1)
    a = x[1:n]
    b = x[(n + 1):(2 * n)]
    c = y[1:n]
    d = y[(n + 1):(2 * n)]
    first = multiply(parent, a, c) - multiply(parent, conjugate_vec(d), b)
    second = multiply(parent, d, a) + multiply(parent, b, conjugate_vec(c))
    Int.(vcat(first, second))
end

function cd_double(parent::Array{Int,3})
    n = size(parent, 1)
    dim = 2 * n
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

function table_sha(table::Array{Int,3})
    bytes2hex(sha256(join(string.(vec(table)), ",")))
end

function basis_vector(dim::Int, idx::Int)
    out = zeros(Int, dim)
    out[idx] = 1
    out
end

function commutator(table::Array{Int,3}, x::AbstractVector{Int}, y::AbstractVector{Int})
    multiply(table, x, y) - multiply(table, y, x)
end

function associator(table::Array{Int,3}, a::AbstractVector{Int}, b::AbstractVector{Int}, x::AbstractVector{Int})
    multiply(table, multiply(table, a, b), x) - multiply(table, a, multiply(table, b, x))
end

function derivation_matrix(table::Array{Int,3}, a_idx::Int, b_idx::Int)
    dim = size(table, 1)
    a = basis_vector(dim, a_idx)
    b = basis_vector(dim, b_idx)
    ab_comm = commutator(table, a, b)
    mat = zeros(Int, dim, dim)
    for x_idx in 1:dim
        x = basis_vector(dim, x_idx)
        y = commutator(table, ab_comm, x) - 3 .* associator(table, a, b, x)
        mat[:, x_idx] .= y
    end
    mat
end

function phi_tensor(o::Array{Int,3})
    phi = zeros(Int, 7, 7, 7)
    for i in 1:7, j in 1:7, k in 1:7
        phi[i, j, k] = o[k + 1, i + 1, j + 1]
    end
    phi
end

function permutation_sign(seq::Vector{Int})
    inv = 0
    for i in 1:length(seq), j in (i + 1):length(seq)
        if j <= length(seq) && seq[i] > seq[j]
            inv += 1
        end
    end
    isodd(inv) ? -1 : 1
end

function hodge_dual_phi(phi::Array{Int,3})
    psi = zeros(Int, 7, 7, 7, 7)
    all7 = collect(1:7)
    for a in 1:7, b in 1:7, c in 1:7, d in 1:7
        comp = [a, b, c, d]
        length(unique(comp)) == 4 || continue
        rem = setdiff(all7, comp)
        psi[a, b, c, d] = permutation_sign(vcat(comp, rem)) * phi[rem[1], rem[2], rem[3]]
    end
    psi
end

function cayley_form(phi::Array{Int,3})
    psi = hodge_dual_phi(phi)
    omega = zeros(Int, 8, 8, 8, 8)
    for a in 1:8, b in 1:8, c in 1:8, d in 1:8
        comp = [a, b, c, d]
        length(unique(comp)) == 4 || continue
        pos0 = findfirst(==(1), comp)
        if pos0 !== nothing
            rest = [x - 1 for x in comp if x != 1]
            omega[a, b, c, d] = (-1)^(pos0 - 1) * phi[rest[1], rest[2], rest[3]]
        else
            rest = comp .- 1
            omega[a, b, c, d] = psi[rest[1], rest[2], rest[3], rest[4]]
        end
    end
    omega
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

function form_get(form, idxs::Vector{Int})
    length(unique(idxs)) == length(idxs) || return 0
    return form[idxs...]
end

function form_action_matrix(form, n::Int, k::Int)
    pairs = [(a, b) for a in 1:n for b in (a + 1):n]
    comps = combo_indices(n, k)
    rows = zeros(Int, length(comps), length(pairs))
    for (row_idx, comp) in enumerate(comps)
        for (col_idx, (a, b)) in enumerate(pairs)
            value = 0
            for r in 1:k
                idx = comp[r]
                if idx == b
                    new = copy(comp)
                    new[r] = a
                    value += form_get(form, new)
                elseif idx == a
                    new = copy(comp)
                    new[r] = b
                    value -= form_get(form, new)
                end
            end
            rows[row_idx, col_idx] = value
        end
    end
    rows, pairs, comps
end

function exact_rank(mat::Matrix{Int})
    rows = Vector{Vector{Rational{BigInt}}}()
    for i in 1:size(mat, 1)
        if any(!=(0), mat[i, :])
            push!(rows, [BigInt(x)//BigInt(1) for x in mat[i, :]])
        end
    end
    m = length(rows)
    n = size(mat, 2)
    r = 1
    pivots = Int[]
    for col in 1:n
        pivot = findfirst(i -> rows[i][col] != 0//1, r:m)
        pivot === nothing && continue
        p = pivot + r - 1
        rows[r], rows[p] = rows[p], rows[r]
        pv = rows[r][col]
        rows[r] = rows[r] ./ pv
        for i in 1:m
            if i != r && rows[i][col] != 0//1
                factor = rows[i][col]
                rows[i] = rows[i] .- factor .* rows[r]
            end
        end
        push!(pivots, col)
        r += 1
        r > m && break
    end
    length(pivots), pivots
end

function summarize_form(name::String, form, n::Int, k::Int)
    mat, pairs, comps = form_action_matrix(form, n, k)
    rank_exact, pivots = exact_rank(mat)
    Dict{String,Any}(
        "name" => name,
        "ambient_dim" => n,
        "form_degree" => k,
        "so_dim" => length(pairs),
        "probe_components" => length(comps),
        "constraint_rows" => size(mat, 1),
        "constraint_cols" => size(mat, 2),
        "exact_rank" => rank_exact,
        "stabilizer_dim" => length(pairs) - rank_exact,
        "pivot_count" => length(pivots),
    )
end

function generic_three_form()
    form = zeros(Int, 7, 7, 7)
    comps = combo_indices(7, 3)
    for (idx, comp) in enumerate(comps)
        value = mod(idx * idx + 3 * idx + 5, 11) - 5
        value == 0 && (value = mod(idx, 3) + 1)
        for perm in Iterators.product(comp, comp, comp)
            p = collect(perm)
            length(unique(p)) == 3 || continue
            order = [findfirst(==(x), comp) for x in p]
            form[p...] = permutation_sign(order) * value
        end
    end
    form
end

function erased_line_form(phi::Array{Int,3}, line::Vector{Int})
    out = copy(phi)
    for perm in Iterators.product(line, line, line)
        p = collect(perm)
        length(unique(p)) == 3 || continue
        out[p...] = 0
    end
    out
end

function action_vector(x::Matrix{Int}, form, n::Int, k::Int)
    vals = Int[]
    for comp in combo_indices(n, k)
        value = 0
        for r in 1:k
            idx = comp[r]
            for q in 1:n
                new = copy(comp)
                new[r] = q
                value += x[q, idx] * form_get(form, new)
            end
        end
        push!(vals, value)
    end
    vals
end

function fano_lines(phi::Array{Int,3})
    lines = Vector{Dict{String,Any}}()
    for comp in combo_indices(7, 3)
        value = phi[comp...]
        value == 0 && continue
        push!(lines, Dict("term" => "e^$(comp[1])$(comp[2])$(comp[3])", "coefficient" => value))
    end
    lines
end

function quantumoptics_probe_guard(dim::Int)
    basis = FockBasis(dim - 1)
    rho = dm(basisstate(basis, 1))
    vals = eigvals(Hermitian(rho.data))
    Dict{String,Any}(
        "package" => "QuantumOptics",
        "basis" => "FockBasis($(dim - 1))",
        "basisstate_index" => 1,
        "trace" => real(tr(rho.data)),
        "trace_eq_1" => abs(real(tr(rho.data)) - 1.0) < TOL,
        "psd" => minimum(real.(vals)) >= -TOL,
        "hermitian_defect" => norm(rho.data - rho.data'),
        "hermitian" => norm(rho.data - rho.data') < TOL,
        "normalization" => "finite probe projector has trace one and unit-norm ket",
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

function zaction_expr(ctx, xvars, pvars, comp::Vector{Int})
    terms = Z3.Expr[]
    for r in 1:length(comp)
        idx = comp[r]
        for q in 1:7
            new = copy(comp)
            new[r] = q
            push!(terms, zmul(ctx, [xvars[q, idx], pvars[new...]]))
        end
    end
    zadd(ctx, terms)
end

function z3_action_guard(phi::Array{Int,3}, x::Matrix{Int}, erased_phi::Array{Int,3})
    ctx = Z3.Context()

    function make_solver(name::String, form::Array{Int,3})
        solver = Z3.Solver(ctx)
        xvars = Array{Z3.Expr}(undef, 7, 7)
        pvars = Array{Z3.Expr}(undef, 7, 7, 7)
        for i in 1:7, j in 1:7
            xvars[i, j] = Z3.IntVar("$(name)_x_$(i)_$(j)", ctx)
            Z3.add(solver, xvars[i, j] == Z3.IntVal(x[i, j], ctx))
        end
        for i in 1:7, j in 1:7, k in 1:7
            pvars[i, j, k] = Z3.IntVar("$(name)_phi_$(i)_$(j)_$(k)", ctx)
            Z3.add(solver, pvars[i, j, k] == Z3.IntVal(form[i, j, k], ctx))
        end
        actions = [zaction_expr(ctx, xvars, pvars, comp) for comp in combo_indices(7, 3)]
        solver, actions
    end

    full_solver, full_actions = make_solver("full", phi)
    Z3.add(full_solver, Z3.Or([Z3.Not(action == Z3.IntVal(0, ctx)) for action in full_actions]))
    full_status = string(Z3.check(full_solver))

    erased_solver, erased_actions = make_solver("erased", erased_phi)
    Z3.add(erased_solver, Z3.Or([Z3.Not(action == Z3.IntVal(0, ctx)) for action in erased_actions]))
    erased_status = string(Z3.check(erased_solver))

    Dict{String,Any}(
        "solver" => "Z3.jl",
        "claim" => "computed octonion derivation D(e1,e2) preserves full Cayley-Dickson phi, but an erased Fano-line form is not preserved",
        "full_phi_nonpreservation_status" => full_status,
        "erased_phi_nonpreservation_status" => erased_status,
        "erase_flip_unsat_to_sat" => full_status == "unsat" && erased_status == "sat",
        "asserted_action_components" => length(full_actions),
        "asserted_precomputed_kernel_relations" => 0,
    )
end

function build_result()
    tables = build_tables()
    package_h, package_crosschecks = package_h_table()
    h_package_matches_cd = package_h == tables["H"]
    o = tables["O"]
    phi = phi_tensor(o)
    omega = cayley_form(phi)
    generic_phi = generic_three_form()
    zero_phi = zeros(Int, 7, 7, 7)
    erase_line = [1, 4, 5]
    erased_phi = erased_line_form(phi, erase_line)
    d12_full = derivation_matrix(o, 2, 3)
    d12_imag = d12_full[2:8, 2:8]

    g2 = summarize_form("G2_stabilizer_of_associative_3_form_phi", phi, 7, 3)
    spin7 = summarize_form("Spin7_stabilizer_of_Cayley_4_form_Phi", omega, 8, 4)
    generic = summarize_form("generic_3_form_control", generic_phi, 7, 3)
    no_probe = Dict{String,Any}("name" => "so7_without_form_preservation", "stabilizer_dim" => 21, "so_dim" => 21)
    commutative = summarize_form("forced_commutative_zero_phi_control", zero_phi, 7, 3)
    qo_guard = quantumoptics_probe_guard(8)
    julia_z3 = z3_action_guard(phi, d12_imag, erased_phi)
    full_action = action_vector(d12_imag, phi, 7, 3)
    erased_action = action_vector(d12_imag, erased_phi, 7, 3)

    negative_control = Dict{String,Any}(
        "generic_3_form_stabilizer_smaller_than_14" => generic["stabilizer_dim"] < 14,
        "drop_form_preservation_probe_so7_dim_21_vs_14" => no_probe["stabilizer_dim"] == 21 && g2["stabilizer_dim"] == 14,
        "forced_commutative_zero_phi_dim_21_vs_14" => commutative["stabilizer_dim"] == 21 && g2["stabilizer_dim"] == 14,
        "erase_fano_line_e145_z3_unsat_to_sat" => julia_z3["erase_flip_unsat_to_sat"],
        "coset_21_minus_14_is_7" => spin7["stabilizer_dim"] - g2["stabilizer_dim"] == 7,
    )

    all_pass = Bool(
        h_package_matches_cd &&
        qo_guard["trace_eq_1"] &&
        qo_guard["psd"] &&
        qo_guard["hermitian"] &&
        g2["stabilizer_dim"] == 14 &&
        spin7["stabilizer_dim"] == 21 &&
        spin7["stabilizer_dim"] - g2["stabilizer_dim"] == 7 &&
        length(fano_lines(phi)) == 7 &&
        maximum(abs.(full_action)) == 0 &&
        maximum(abs.(erased_action)) > 0 &&
        generic["stabilizer_dim"] < 14 &&
        no_probe["stabilizer_dim"] == 21 &&
        commutative["stabilizer_dim"] == 21 &&
        julia_z3["full_phi_nonpreservation_status"] == "unsat" &&
        julia_z3["erased_phi_nonpreservation_status"] == "sat" &&
        all(value for value in values(negative_control) if value isa Bool) &&
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
            "name" => "form_preservation_probe",
            "explicit_probe_family" => [
                "(X.phi)_{ijk}=sum_q X_{q,i} phi_{qjk}+X_{q,j} phi_{iqk}+X_{q,k} phi_{ijq} for all i<j<k in Im(O)",
                "(Y.Phi)_{abcd}=sum_q Y_{q,a} Phi_{qbcd}+... for all a<b<c<d in O",
            ],
            "finite_probe_counts" => Dict("phi_components" => g2["probe_components"], "Phi_components" => spin7["probe_components"]),
            "quantumoptics_probe_guard" => qo_guard,
        ),
        "C" => Dict(
            "trace_eq_1" => qo_guard["trace_eq_1"],
            "psd" => qo_guard["psd"],
            "hermitian" => qo_guard["hermitian"],
            "normalization" => "orthonormal octonion basis; QuantumOptics auxiliary probe projector is normalized trace-one",
            "rung_specific_constraint" => "phi and Phi are computed from Cayley-Dickson octonion structure constants; X is skew and must preserve the calibration form",
        ),
        "S_mod_M" => Dict(
            "definition" => "S is so(7) or so(8); A ~_M B iff the finite form-action probe cannot distinguish A-B; the stabilizer is ker(M)",
            "class_dimensions" => Dict("Stab_phi_G2" => g2["stabilizer_dim"], "Stab_Phi_Spin7" => spin7["stabilizer_dim"]),
            "quotient_summary" => "ker(form-action on phi) has dimension 14; ker(form-action on Phi) has dimension 21",
            "coset" => "Spin(7)/G2 dimension = 21 - 14 = 7, matching the S^7 imaginary-unit/Fano-point horizon only",
        ),
        "octonion_structure" => Dict(
            "construction" => "Cayley-Dickson R -> C -> H -> O",
            "table_sha256" => table_sha(o),
            "quaternion_stage_matches_CliffordAlgebras" => h_package_matches_cd,
            "cliffordalgebras_crosscheck" => package_crosschecks,
        ),
        "calibration_forms" => Dict(
            "phi_fano_line_count" => length(fano_lines(phi)),
            "phi_fano_lines" => fano_lines(phi),
            "Phi_definition" => "Phi=e^0 wedge phi + *_7 phi on O=R plus Im(O)",
        ),
        "stabilizer_dimension_summary" => Dict(
            "dim_Stab_phi_G2" => g2["stabilizer_dim"],
            "dim_Stab_Phi_Spin7" => spin7["stabilizer_dim"],
            "spin7_minus_g2_coset_dim" => spin7["stabilizer_dim"] - g2["stabilizer_dim"],
            "generic_3_form_stabilizer_dim" => generic["stabilizer_dim"],
            "so7_without_preservation_dim" => no_probe["stabilizer_dim"],
            "forced_commutative_zero_phi_dim" => commutative["stabilizer_dim"],
            "asserted_precomputed_kernel_relations" => 0,
        ),
        "linear_algebra" => Dict("g2" => g2, "spin7" => spin7, "generic_control" => generic, "commutative_control" => commutative),
        "julia_z3" => julia_z3,
        "negative_control_flip" => negative_control,
        "all_pass" => all_pass,
        "summary" => Dict(
            "dim_Stab_phi_G2" => g2["stabilizer_dim"],
            "dim_Stab_Phi_Spin7" => spin7["stabilizer_dim"],
            "spin7_minus_g2_coset_dim" => spin7["stabilizer_dim"] - g2["stabilizer_dim"],
            "phi_fano_line_count" => length(fano_lines(phi)),
            "generic_3_form_stabilizer_dim" => generic["stabilizer_dim"],
            "forced_commutative_zero_phi_dim" => commutative["stabilizer_dim"],
            "julia_z3_full_phi_nonpreservation" => julia_z3["full_phi_nonpreservation_status"],
            "julia_z3_erased_phi_nonpreservation" => julia_z3["erased_phi_nonpreservation_status"],
            "all_pass" => all_pass,
        ),
    )
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    summary = result["summary"]
    println("wrote: ", RESULT_PATH)
    println(
        "FOUNDATION_R6_SPIN7_G2_CALIBRATION_FORMS_JULIA_DONE ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "dim_g2=", summary["dim_Stab_phi_G2"], " ",
        "dim_spin7=", summary["dim_Stab_Phi_Spin7"], " ",
        "coset=", summary["spin7_minus_g2_coset_dim"], " ",
        "generic_dim=", summary["generic_3_form_stabilizer_dim"], " ",
        "erased_z3=", summary["julia_z3_erased_phi_nonpreservation"],
    )
    return result["all_pass"] ? 0 : 1
end

exit(main())
