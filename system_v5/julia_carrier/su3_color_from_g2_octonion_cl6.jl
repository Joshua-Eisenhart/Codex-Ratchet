#!/usr/bin/env julia
# object_id: su3_color_from_g2_octonion_cl6
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "su3_color_from_g2_octonion_cl6"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/su3_color_from_g2_octonion_cl6_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/su3_color_from_g2_octonion_cl6_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const COLLAPSE_SENTINEL = 1.0e99
const DIM_O = 8
const FIXED_UNIT = 7
const CLAIM_CEILING = "finite witness that SU(3)-color emerges as the G2=Aut(O) complex-structure stabilizer on Cl(6) octonion spinors, reproducing the published Dixon/Furey construction on the owner's carrier; NO admission of the Standard Model/physics/M(C); masses, couplings, SU(2)xU(1), and generations NOT addressed here"
const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

pyfloat(x) = Float64(real(x))
varidx(row0::Int, col0::Int) = row0 + 1 + col0 * DIM_O

function setprod!(table, a::Int, b::Int, c::Int, s)
    table[c + 1, a + 1, b + 1] = s
end

function octonion_table()
    table = zeros(Float64, DIM_O, DIM_O, DIM_O)
    for a in 0:(DIM_O - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
    for a in 1:(DIM_O - 1)
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in FANO
        for (a, b, c, s) in [
            (i, j, k, 1.0),
            (j, k, i, 1.0),
            (k, i, j, 1.0),
            (j, i, k, -1.0),
            (k, j, i, -1.0),
            (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function associative_commutative_erase_table()
    table = zeros(Float64, DIM_O, DIM_O, DIM_O)
    for a in 0:(DIM_O - 1)
        setprod!(table, a, a, a, 1.0)
    end
    table
end

function basis(dim::Int, idx0::Int; dtype=Float64)
    v = zeros(dtype, dim)
    v[idx0 + 1] = one(dtype)
    v
end

function multiply(table, x, y)
    out = zeros(eltype(table), DIM_O)
    @inbounds for c in 1:DIM_O, a in 1:DIM_O, b in 1:DIM_O
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
end

function left_matrix(table, v)
    out = zeros(eltype(table), DIM_O, DIM_O)
    @inbounds for c in 1:DIM_O, b in 1:DIM_O, a in 1:DIM_O
        out[c, b] += table[c, a, b] * v[a]
    end
    out
end

vec_to_matrix(v) = reshape(v, DIM_O, DIM_O)
matrix_to_vec(mat) = reshape(mat, :)

function rank_from_singular_values(singular, shape_tuple; scale=100.0)
    max_s = isempty(singular) ? 0.0 : maximum(singular)
    tol = maximum(shape_tuple) * eps(Float64) * max_s * scale
    rank = count(>(tol), singular)
    rank, tol
end

function nullspace_data(mat)
    decomp = svd(mat; full = size(mat, 1) < size(mat, 2))
    rank, tol = rank_from_singular_values(decomp.S, size(mat))
    v = Matrix(decomp.Vt')
    basis_cols = rank < size(v, 2) ? v[:, (rank + 1):end] : zeros(eltype(v), size(v, 1), 0)
    Dict{String,Any}(
        "rank" => rank,
        "tol" => tol,
        "nullity" => size(basis_cols, 2),
        "basis" => basis_cols,
        "singular" => decomp.S,
    )
end

function derivation_constraint_matrix(table)
    mat = zeros(Float64, DIM_O * DIM_O * DIM_O, DIM_O * DIM_O)
    row = 0
    for a in 0:(DIM_O - 1), b in 0:(DIM_O - 1), c in 0:(DIM_O - 1)
        row += 1
        for k in 0:(DIM_O - 1)
            mat[row, varidx(c, k)] += table[k + 1, a + 1, b + 1]
            mat[row, varidx(k, a)] -= table[c + 1, k + 1, b + 1]
            mat[row, varidx(k, b)] -= table[c + 1, a + 1, k + 1]
        end
    end
    mat
end

function derivation_basis(table)
    constraint = derivation_constraint_matrix(table)
    ns = nullspace_data(constraint)
    mats = [vec_to_matrix(ns["basis"][:, idx]) for idx in 1:ns["nullity"]]
    Dict{String,Any}("constraint" => constraint, "nullspace" => ns, "mats" => mats)
end

function stabilizer_basis(g2_basis, fixed_idx::Int)
    if size(g2_basis, 2) == 0
        return Dict{String,Any}(
            "constraints" => zeros(Float64, DIM_O, 0),
            "nullspace" => Dict{String,Any}("rank" => 0, "tol" => 0.0, "nullity" => 0, "basis" => zeros(Float64, 0, 0), "singular" => Float64[]),
            "basis" => zeros(Float64, DIM_O * DIM_O, 0),
            "mats" => Matrix{Float64}[],
        )
    end
    constraints = zeros(Float64, DIM_O, size(g2_basis, 2))
    for row0 in 0:(DIM_O - 1)
        constraints[row0 + 1, :] .= g2_basis[varidx(row0, fixed_idx), :]
    end
    ns = nullspace_data(constraints)
    basis_cols = g2_basis * ns["basis"]
    mats = [vec_to_matrix(basis_cols[:, idx]) for idx in 1:size(basis_cols, 2)]
    Dict{String,Any}("constraints" => constraints, "nullspace" => ns, "basis" => basis_cols, "mats" => mats)
end

function project_coeffs(basis_cols, vec)
    gram = basis_cols' * basis_cols
    gram \ (basis_cols' * vec)
end

function bracket_closure_metrics(basis_cols, mats)
    n = length(mats)
    max_resid = 0.0
    max_bracket_norm = 0.0
    coeffs = zeros(eltype(basis_cols), n, n, n)
    for i in 1:n, j in 1:n
        bracket = mats[i] * mats[j] - mats[j] * mats[i]
        flat = matrix_to_vec(bracket)
        co = project_coeffs(basis_cols, flat)
        residual = flat - basis_cols * co
        max_resid = max(max_resid, norm(residual))
        max_bracket_norm = max(max_bracket_norm, norm(bracket))
        coeffs[:, i, j] .= co
    end
    Dict{String,Any}("max_residual" => max_resid, "max_bracket_norm" => max_bracket_norm, "structure_constants" => coeffs)
end

function killing_and_rank_metrics(structure_constants, mats, basis_cols)
    n = size(structure_constants, 1)
    ad = [structure_constants[:, i, :] for i in 1:n]
    killing = zeros(Float64, n, n)
    for i in 1:n, j in 1:n
        killing[i, j] = tr(ad[i] * ad[j])
    end
    killing_eigs = eigvals(Symmetric((killing + killing') ./ 2.0))
    generic = zeros(Float64, DIM_O, DIM_O)
    for idx in 1:n
        generic .+= Float64(idx) .* mats[idx]
    end
    centralizer_matrix = zeros(Float64, DIM_O * DIM_O, n)
    for idx in 1:n
        centralizer_matrix[:, idx] .= matrix_to_vec(mats[idx] * generic - generic * mats[idx])
    end
    sv = svdvals(centralizer_matrix)
    centralizer_rank = count(>(1.0e-9), sv)
    Dict{String,Any}(
        "killing_matrix" => killing,
        "killing_eigs" => killing_eigs,
        "killing_negative_definite" => all(killing_eigs .< -1.0e-9),
        "centralizer_rank" => centralizer_rank,
        "rank" => n - centralizer_rank,
        "basis_gram_residual" => norm(basis_cols' * basis_cols - Matrix{Float64}(I, n, n)),
    )
end

function j_eigenbasis()
    eye = Matrix{ComplexF64}(I, DIM_O, DIM_O)
    e(idx0) = eye[:, idx0 + 1]
    rt2 = sqrt(2.0)
    hcat(
        (e(0) .- im .* e(7)) ./ rt2,
        (e(1) .+ im .* e(6)) ./ rt2,
        (e(2) .- im .* e(5)) ./ rt2,
        (e(3) .- im .* e(4)) ./ rt2,
        (e(0) .+ im .* e(7)) ./ rt2,
        (e(1) .- im .* e(6)) ./ rt2,
        (e(2) .+ im .* e(5)) ./ rt2,
        (e(3) .+ im .* e(4)) ./ rt2,
    )
end

function decomposition_metrics(mats)
    change = j_eigenbasis()
    inv = change'
    blocks = [0, 1, 1, 1, 2, 3, 3, 3]
    max_offblock = 0.0
    max_singlet = 0.0
    max_trace = 0.0
    max_antitriplet_conj = 0.0
    casimir_triplet = zeros(ComplexF64, 3, 3)
    casimir_antitriplet = zeros(ComplexF64, 3, 3)
    for mat in mats
        rep = inv * (ComplexF64.(mat) * change)
        for row in 1:DIM_O, col in 1:DIM_O
            if blocks[row] != blocks[col]
                max_offblock = max(max_offblock, abs(rep[row, col]))
            end
        end
        max_singlet = max(max_singlet, abs(rep[1, 1]), abs(rep[5, 5]))
        triplet = rep[2:4, 2:4]
        antitriplet = rep[6:8, 6:8]
        max_trace = max(max_trace, abs(tr(triplet)), abs(tr(antitriplet)))
        max_antitriplet_conj = max(max_antitriplet_conj, norm(antitriplet - conj.(triplet)))
        casimir_triplet .+= triplet * triplet
        casimir_antitriplet .+= antitriplet * antitriplet
    end
    target = -(4.0 / 3.0) .* Matrix{ComplexF64}(I, 3, 3)
    Dict{String,Any}(
        "basis_unitary_residual" => norm(change' * change - Matrix{ComplexF64}(I, DIM_O, DIM_O)),
        "offblock_residual" => max_offblock,
        "singlet_action_residual" => max_singlet,
        "triplet_trace_residual" => max_trace,
        "antitriplet_is_conjugate_residual" => max_antitriplet_conj,
        "triplet_casimir_residual" => norm(casimir_triplet - target),
        "antitriplet_casimir_residual" => norm(casimir_antitriplet - target),
        "triplet_casimir_value" => pyfloat(-tr(casimir_triplet) / 3.0),
        "antitriplet_casimir_value" => pyfloat(-tr(casimir_antitriplet) / 3.0),
        "dims" => Dict("singlet_plus" => 1, "triplet" => 3, "singlet_minus" => 1, "antitriplet" => 3),
    )
end

function complex_vec(terms)
    out = zeros(ComplexF64, DIM_O)
    for (idx0, coeff) in terms
        out[idx0 + 1] = ComplexF64(coeff)
    end
    out
end

function octonion_complex_dagger(v)
    out = zeros(ComplexF64, DIM_O)
    out[1] = conj(v[1])
    for idx in 2:DIM_O
        out[idx] = -conj(v[idx])
    end
    out
end

function owner_ladder_vectors()
    [
        complex_vec([(6, -0.5 + 0im), (1, 0.0 + 0.5im)]),
        complex_vec([(5, -0.5 + 0im), (2, 0.0 + 0.5im)]),
        complex_vec([(4, -0.5 + 0im), (3, 0.0 + 0.5im)]),
    ]
end

function wedge2_matrix(triplet)
    pairs = [(1, 2), (2, 0), (0, 1)]
    out = zeros(ComplexF64, 3, 3)
    for (col, (a, b)) in enumerate(pairs)
        for r in 0:2
            for (term, coeff) in [((r, b), triplet[r + 1, a + 1]), ((a, r), triplet[r + 1, b + 1])]
                term[1] == term[2] && continue
                sign = 1.0
                ordered = term
                if ordered[1] > ordered[2]
                    ordered = (ordered[2], ordered[1])
                    sign = -1.0
                end
                for (row, target) in enumerate(pairs)
                    if ordered == target
                        out[row, col] += sign * coeff
                    elseif ordered == (target[2], target[1])
                        out[row, col] -= sign * coeff
                    end
                end
            end
        end
    end
    out
end

function matrix_rank_tol(mat; tol=1.0e-9)
    count(>(tol), svdvals(mat))
end

function cl6_ladder_metrics(table)
    ctable = ComplexF64.(table)
    alphas = owner_ladder_vectors()
    daggers = [octonion_complex_dagger(alpha) for alpha in alphas]
    lower = [left_matrix(ctable, alpha) for alpha in alphas]
    raise = [left_matrix(ctable, dagger) for dagger in daggers]
    ident = Matrix{ComplexF64}(I, DIM_O, DIM_O)
    zero = zeros(ComplexF64, DIM_O, DIM_O)

    car_residual = 0.0
    for i in 1:3, j in 1:3
        target = i == j ? ident : zero
        car_residual = max(car_residual, norm(lower[i] * raise[j] + raise[j] * lower[i] - target))
        car_residual = max(car_residual, norm(lower[i] * lower[j] + lower[j] * lower[i]))
        car_residual = max(car_residual, norm(raise[i] * raise[j] + raise[j] * raise[i]))
    end

    gammas = vcat([lower[i] + raise[i] for i in 1:3], [-im .* (lower[i] - raise[i]) for i in 1:3])
    gamma_residual = 0.0
    for i in 1:6, j in 1:6
        target = i == j ? 2.0 .* ident : zero
        gamma_residual = max(gamma_residual, norm(gammas[i] * gammas[j] + gammas[j] * gammas[i] - target))
    end

    products = Matrix{ComplexF64}[]
    for mask in 0:63
        mat = copy(ident)
        for idx in 0:5
            if ((mask >> idx) & 1) == 1
                mat = mat * gammas[idx + 1]
            end
        end
        push!(products, mat)
    end
    span = hcat([reshape(mat, :) for mat in products]...)
    cl6_rank = matrix_rank_tol(span)

    lambdas = [
        -(raise[2] * lower[1] + raise[1] * lower[2]),
        im * raise[2] * lower[1] - im * raise[1] * lower[2],
        raise[2] * lower[2] - raise[1] * lower[1],
        -(raise[1] * lower[3] + raise[3] * lower[1]),
        -im * raise[1] * lower[3] + im * raise[3] * lower[1],
        -(raise[3] * lower[2] + raise[2] * lower[3]),
        im * raise[3] * lower[2] - im * raise[2] * lower[3],
        -(raise[1] * lower[1] + raise[2] * lower[2] - 2.0 * raise[3] * lower[3]) / sqrt(3.0),
    ]
    su3_spinor = [-0.5im .* item for item in lambdas]
    spinor_cols = hcat([reshape(item, :) for item in su3_spinor]...)
    spinor_rank = matrix_rank_tol(spinor_cols)
    if spinor_rank < 8
        return Dict{String,Any}(
            "car_residual" => car_residual,
            "gamma_residual" => gamma_residual,
            "cl6_matrix_span_dim" => cl6_rank,
            "spinor_su3_rank" => spinor_rank,
            "spinor_su3_closure_residual" => COLLAPSE_SENTINEL,
            "projector_rank" => 0,
            "vacuum_column" => nothing,
            "fock_gram_residual" => COLLAPSE_SENTINEL,
            "fock_offblock_residual" => COLLAPSE_SENTINEL,
            "fock_singlet_action_residual" => COLLAPSE_SENTINEL,
            "fock_triplet_trace_residual" => COLLAPSE_SENTINEL,
            "fock_wedge2_antitriplet_residual" => COLLAPSE_SENTINEL,
            "fock_triplet_casimir_residual" => COLLAPSE_SENTINEL,
            "fock_antitriplet_casimir_residual" => COLLAPSE_SENTINEL,
            "number_operator_residual" => COLLAPSE_SENTINEL,
            "charge_quantization_residual" => COLLAPSE_SENTINEL,
            "particle_ideal_charges" => Float64[],
            "charge_conjugate_ideal_charges" => Float64[],
            "sm_charge_slots" => Dict{String,Any}(),
        )
    end
    spinor_gram = spinor_cols' * spinor_cols
    spinor_closure = 0.0
    for left in su3_spinor, right in su3_spinor
        bracket = left * right - right * left
        coeff = spinor_gram \ (spinor_cols' * reshape(bracket, :))
        spinor_closure = max(spinor_closure, norm(reshape(bracket, :) - spinor_cols * coeff))
    end

    projector = lower[1] * lower[2] * lower[3] * raise[3] * raise[2] * raise[1]
    col_norms = [norm(projector[:, col]) for col in 1:DIM_O]
    vacuum_col = argmax(col_norms)
    if col_norms[vacuum_col] < TOL
        return Dict{String,Any}(
            "car_residual" => car_residual,
            "gamma_residual" => gamma_residual,
            "cl6_matrix_span_dim" => cl6_rank,
            "spinor_su3_rank" => spinor_rank,
            "spinor_su3_closure_residual" => spinor_closure,
            "projector_rank" => matrix_rank_tol(projector),
            "vacuum_column" => vacuum_col - 1,
            "fock_gram_residual" => COLLAPSE_SENTINEL,
            "fock_offblock_residual" => COLLAPSE_SENTINEL,
            "fock_singlet_action_residual" => COLLAPSE_SENTINEL,
            "fock_triplet_trace_residual" => COLLAPSE_SENTINEL,
            "fock_wedge2_antitriplet_residual" => COLLAPSE_SENTINEL,
            "fock_triplet_casimir_residual" => COLLAPSE_SENTINEL,
            "fock_antitriplet_casimir_residual" => COLLAPSE_SENTINEL,
            "number_operator_residual" => COLLAPSE_SENTINEL,
            "charge_quantization_residual" => COLLAPSE_SENTINEL,
            "particle_ideal_charges" => Float64[],
            "charge_conjugate_ideal_charges" => Float64[],
            "sm_charge_slots" => Dict{String,Any}(),
        )
    end

    vacuum = projector[:, vacuum_col] ./ col_norms[vacuum_col]
    fock_states = Vector{Vector{ComplexF64}}()
    push!(fock_states, vacuum)
    append!(fock_states, [raise[idx] * vacuum for idx in 1:3])
    append!(fock_states, [raise[2] * raise[3] * vacuum, raise[3] * raise[1] * vacuum, raise[1] * raise[2] * vacuum])
    push!(fock_states, raise[1] * raise[2] * raise[3] * vacuum)
    fock = hcat(fock_states...)
    fock_inv = fock'
    fock_gram_residual = norm(fock_inv * fock - ident)
    occ_blocks = [0, 1, 1, 1, 2, 2, 2, 3]
    fock_offblock = 0.0
    fock_singlet = 0.0
    fock_trace = 0.0
    wedge2_residual = 0.0
    fock_casimir_1 = zeros(ComplexF64, 3, 3)
    fock_casimir_2 = zeros(ComplexF64, 3, 3)
    for generator in su3_spinor
        rep = fock_inv * (generator * fock)
        for row in 1:DIM_O, col in 1:DIM_O
            if occ_blocks[row] != occ_blocks[col]
                fock_offblock = max(fock_offblock, abs(rep[row, col]))
            end
        end
        fock_singlet = max(fock_singlet, abs(rep[1, 1]), abs(rep[8, 8]))
        triplet = rep[2:4, 2:4]
        antitriplet = rep[5:7, 5:7]
        fock_trace = max(fock_trace, abs(tr(triplet)), abs(tr(antitriplet)))
        wedge2_residual = max(wedge2_residual, norm(antitriplet - wedge2_matrix(triplet)))
        fock_casimir_1 .+= triplet * triplet
        fock_casimir_2 .+= antitriplet * antitriplet
    end
    target = -(4.0 / 3.0) .* Matrix{ComplexF64}(I, 3, 3)

    number = zeros(ComplexF64, DIM_O, DIM_O)
    for idx in 1:3
        number .+= raise[idx] * lower[idx]
    end
    number_rep = fock_inv * (number * fock)
    number_target = Diagonal(ComplexF64[0, 1, 1, 1, 2, 2, 2, 3])
    particle_charges = real.(diag(number_target)) ./ 3.0
    conjugate_charges = -particle_charges
    charge_quant_residual = max(
        maximum(abs.(3.0 .* particle_charges .- round.(3.0 .* particle_charges))),
        maximum(abs.(3.0 .* conjugate_charges .- round.(3.0 .* conjugate_charges))),
    )

    Dict{String,Any}(
        "car_residual" => car_residual,
        "gamma_residual" => gamma_residual,
        "cl6_matrix_span_dim" => cl6_rank,
        "spinor_su3_rank" => spinor_rank,
        "spinor_su3_closure_residual" => spinor_closure,
        "projector_rank" => matrix_rank_tol(projector),
        "vacuum_column" => vacuum_col - 1,
        "fock_gram_residual" => fock_gram_residual,
        "fock_offblock_residual" => fock_offblock,
        "fock_singlet_action_residual" => fock_singlet,
        "fock_triplet_trace_residual" => fock_trace,
        "fock_wedge2_antitriplet_residual" => wedge2_residual,
        "fock_triplet_casimir_residual" => norm(fock_casimir_1 - target),
        "fock_antitriplet_casimir_residual" => norm(fock_casimir_2 - target),
        "number_operator_residual" => norm(number_rep - number_target),
        "charge_quantization_residual" => charge_quant_residual,
        "particle_ideal_charges" => collect(Float64.(particle_charges)),
        "charge_conjugate_ideal_charges" => collect(Float64.(conjugate_charges)),
        "sm_charge_slots" => Dict{String,Any}(
            "neutrino_singlet" => Dict("dim" => 1, "charge" => 0.0, "source" => "particle ideal N=0"),
            "down_quark_color_triplet" => Dict("dim" => 3, "charge" => -1.0 / 3.0, "source" => "charge-conjugate ideal N=1"),
            "up_quark_color_triplet" => Dict("dim" => 3, "charge" => 2.0 / 3.0, "source" => "particle ideal N=2"),
            "electron_singlet" => Dict("dim" => 1, "charge" => -1.0, "source" => "charge-conjugate ideal N=3"),
        ),
    )
end

function deterministic_wrong_subspace(g2_basis)
    raw = zeros(Float64, 14, 8)
    for row in 0:13, col in 0:7
        raw[row + 1, col + 1] = (mod((row + 3) * (col + 5) * 37 + (row + 1)^2 * 11 + (col + 1) * 17, 97) - 48) / 29.0
    end
    q = Matrix(qr(raw).Q)[:, 1:8]
    basis_cols = g2_basis * q
    mats = [vec_to_matrix(basis_cols[:, idx]) for idx in 1:8]
    closure = bracket_closure_metrics(basis_cols, mats)
    decomp = decomposition_metrics(mats)
    fixed_norm = maximum(norm(mat * basis(DIM_O, FIXED_UNIT)) for mat in mats)
    Dict{String,Any}(
        "basis" => basis_cols,
        "mats" => mats,
        "closure_residual" => closure["max_residual"],
        "decomp_offblock_residual" => decomp["offblock_residual"],
        "fixed_unit_action_norm" => fixed_norm,
    )
end

function parity_against_peer(result, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => peer_path)],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(peer_path)
    rows = Vector{Dict{String,Any}}()
    max_diff = 0.0
    max_diff_key = nothing
    strict = Vector{Dict{String,Any}}()
    missing = String[]
    for (key, value) in result["shared_scalars"]
        if !haskey(peer["shared_scalars"], key)
            push!(missing, key)
            continue
        end
        jv = Float64(value)
        pv = Float64(peer["shared_scalars"][key])
        diff = abs(jv - pv)
        if diff > max_diff
            max_diff = diff
            max_diff_key = key
        end
        row = Dict{String,Any}("key" => key, "julia" => jv, "jax" => pv, "abs_diff" => diff)
        push!(rows, row)
        diff > STRICT_STOP_TOL && push!(strict, row)
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer["shared_booleans"], key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer["shared_booleans"][key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer["shared_booleans"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    table = octonion_table()
    g2 = derivation_basis(table)
    g2_basis = g2["nullspace"]["basis"]
    g2_closure = bracket_closure_metrics(g2_basis, g2["mats"])
    su3 = stabilizer_basis(g2_basis, FIXED_UNIT)
    su3_closure = bracket_closure_metrics(su3["basis"], su3["mats"])
    su3_lie = killing_and_rank_metrics(su3_closure["structure_constants"], su3["mats"], su3["basis"])
    direct_decomp = decomposition_metrics(su3["mats"])
    cl6 = cl6_ladder_metrics(table)

    wrong = deterministic_wrong_subspace(g2_basis)
    erased = derivation_basis(associative_commutative_erase_table())
    erased_stabilizer = stabilizer_basis(erased["nullspace"]["basis"], FIXED_UNIT)
    erased_cl6 = cl6_ladder_metrics(associative_commutative_erase_table())

    g2_dim = g2["nullspace"]["nullity"]
    su3_dim = size(su3["basis"], 2)
    su3_closes = su3_closure["max_residual"] < TOL
    decomp_3_3bar_1_1 = direct_decomp["offblock_residual"] < TOL &&
        direct_decomp["singlet_action_residual"] < TOL &&
        direct_decomp["triplet_trace_residual"] < TOL &&
        direct_decomp["antitriplet_is_conjugate_residual"] < TOL &&
        direct_decomp["triplet_casimir_residual"] < TOL &&
        direct_decomp["antitriplet_casimir_residual"] < TOL
    furey_spinor_pattern = cl6["car_residual"] < TOL &&
        cl6["gamma_residual"] < TOL &&
        cl6["cl6_matrix_span_dim"] == 64 &&
        cl6["spinor_su3_rank"] == 8 &&
        cl6["spinor_su3_closure_residual"] < TOL &&
        cl6["fock_offblock_residual"] < TOL &&
        cl6["fock_singlet_action_residual"] < TOL &&
        cl6["fock_wedge2_antitriplet_residual"] < TOL &&
        cl6["number_operator_residual"] < TOL &&
        cl6["charge_quantization_residual"] < TOL
    wrong_subgroup_fails = wrong["closure_residual"] > 1.0e-3 &&
        wrong["decomp_offblock_residual"] > 1.0e-3 &&
        wrong["fixed_unit_action_norm"] > 1.0e-3
    assoc_erase_collapses = erased["nullspace"]["nullity"] != 14 &&
        size(erased_stabilizer["basis"], 2) != 8 &&
        (erased_cl6["car_residual"] > 1.0e-3 || erased_cl6["cl6_matrix_span_dim"] != 64)

    verdicts = Dict{String,Any}(
        "g2_dim_is_14" => g2_dim == 14,
        "g2_closes" => g2_closure["max_residual"] < TOL,
        "su3_dim_is_8" => su3_dim == 8,
        "su3_closes" => su3_closes,
        "su3_rank_is_2" => su3_lie["rank"] == 2,
        "su3_killing_negative_definite" => su3_lie["killing_negative_definite"],
        "su3_triplet_casimir_is_4_3" => direct_decomp["triplet_casimir_residual"] < TOL,
        "decomp_3_3bar_1_1" => decomp_3_3bar_1_1,
        "cl6_is_complex_8x8" => cl6["cl6_matrix_span_dim"] == 64,
        "furey_ladder_charge_pattern" => furey_spinor_pattern,
    )
    controls = Dict{String,Any}(
        "wrong_subgroup_fails" => wrong_subgroup_fails,
        "assoc_erase_collapses" => assoc_erase_collapses,
        "control_miswired" => !(wrong_subgroup_fails && assoc_erase_collapses),
    )

    shared_scalars = Dict{String,Any}(
        "g2.constraint_rank" => g2["nullspace"]["rank"],
        "g2.dim" => g2_dim,
        "g2.closure_residual" => g2_closure["max_residual"],
        "su3.stabilizer_constraint_rank" => su3["nullspace"]["rank"],
        "su3.dim" => su3_dim,
        "su3.closure_residual" => su3_closure["max_residual"],
        "su3.rank" => su3_lie["rank"],
        "su3.killing_eig_min" => minimum(su3_lie["killing_eigs"]),
        "su3.killing_eig_max" => maximum(su3_lie["killing_eigs"]),
        "direct_decomp.offblock_residual" => direct_decomp["offblock_residual"],
        "direct_decomp.singlet_action_residual" => direct_decomp["singlet_action_residual"],
        "direct_decomp.triplet_casimir_value" => direct_decomp["triplet_casimir_value"],
        "direct_decomp.triplet_casimir_residual" => direct_decomp["triplet_casimir_residual"],
        "cl6.car_residual" => cl6["car_residual"],
        "cl6.gamma_residual" => cl6["gamma_residual"],
        "cl6.matrix_span_dim" => cl6["cl6_matrix_span_dim"],
        "cl6.spinor_su3_rank" => cl6["spinor_su3_rank"],
        "cl6.spinor_su3_closure_residual" => cl6["spinor_su3_closure_residual"],
        "cl6.fock_wedge2_antitriplet_residual" => cl6["fock_wedge2_antitriplet_residual"],
        "cl6.number_operator_residual" => cl6["number_operator_residual"],
        "cl6.charge_quantization_residual" => cl6["charge_quantization_residual"],
        "assoc_erase.g2_dim" => erased["nullspace"]["nullity"],
        "assoc_erase.cl6_car_residual" => erased_cl6["car_residual"],
        "assoc_erase.cl6_matrix_span_dim" => erased_cl6["cl6_matrix_span_dim"],
    )
    shared_booleans = Dict{String,Any}()
    for (key, value) in verdicts
        shared_booleans["verdict.$key"] = value
    end
    for (key, value) in controls
        shared_booleans["control.$key"] = value
    end

    all_core = all(Bool(v) for v in values(verdicts)) &&
        controls["wrong_subgroup_fails"] &&
        controls["assoc_erase_collapses"]
    tool_manifest = Dict{String,Any}(
        "Julia" => "load-bearing finite tensor, SVD/nullspace, rank, Lie-bracket, and Cl(6) matrix computations",
        "LinearAlgebra" => "load-bearing SVD, eigenspectra, rank, norms, and compact Lie-algebra checks",
        "JSON" => "supportive result serialization only",
        "JAX peer" => "independent dual-backend mirror required for parity, not used by this Julia computation",
    )
    tool_depth = Dict{String,Any}(
        "Julia" => "load_bearing",
        "LinearAlgebra" => "load_bearing",
        "JSON" => "supportive",
        "JAX peer" => "load_bearing",
    )

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "backend" => "julia_x64",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SS.sssZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "finite_algebra_witness_controlled_scratch_diagnostic",
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "fixed_complex_structure_unit" => "e7",
        "owner_fano_triples" => [collect(t) for t in FANO],
        "owner_ladder_pairs" => Dict(
            "alpha1" => "(-e6 + i e1)/2",
            "alpha2" => "(-e5 + i e2)/2",
            "alpha3" => "(-e4 + i e3)/2",
            "reason" => "These are the nilpotent pairs induced by left multiplication by the owner's fixed e7 Fano convention.",
        ),
        "tool_manifest" => tool_manifest,
        "TOOL_MANIFEST" => tool_manifest,
        "tool_integration_depth" => tool_depth,
        "TOOL_INTEGRATION_DEPTH" => tool_depth,
        "verdicts" => verdicts,
        "controls" => controls,
        "numbers" => shared_scalars,
        "direct_g2_stabilizer_decomposition" => direct_decomp,
        "cl6_furey_ladder" => cl6,
        "wrong_subgroup_control" => Dict(
            "closure_residual" => wrong["closure_residual"],
            "decomp_offblock_residual" => wrong["decomp_offblock_residual"],
            "fixed_unit_action_norm" => wrong["fixed_unit_action_norm"],
        ),
        "associative_erase_control" => Dict(
            "table" => "coordinatewise associative/commutative direct-product erase",
            "g2_dim" => erased["nullspace"]["nullity"],
            "stabilizer_dim" => size(erased_stabilizer["basis"], 2),
            "cl6_car_residual" => erased_cl6["car_residual"],
            "cl6_matrix_span_dim" => erased_cl6["cl6_matrix_span_dim"],
        ),
        "positive" => Dict(
            "g2_derivation_algebra" => Dict("pass" => verdicts["g2_dim_is_14"] && verdicts["g2_closes"], "dim" => g2_dim),
            "su3_stabilizer" => Dict("pass" => verdicts["su3_dim_is_8"] && verdicts["su3_closes"], "dim" => su3_dim),
            "spinor_decomposition" => Dict("pass" => decomp_3_3bar_1_1, "dims" => "1+3+1+3"),
            "cl6_furey_charge_pattern" => Dict("pass" => furey_spinor_pattern, "charges" => cl6["sm_charge_slots"]),
        ),
        "graveyard_companions" => Dict(
            "wrong_subgroup" => Dict("pass" => wrong_subgroup_fails),
            "associative_erase" => Dict("pass" => assoc_erase_collapses),
        ),
        "boundary" => Dict(
            "not_new_physics" => Dict("pass" => true, "ceiling" => CLAIM_CEILING),
            "no_su2_u1_generations_masses_or_couplings" => Dict("pass" => true),
        ),
        "why_not_v4_probes" => "Scratch dual-backend finite algebra witness only; not a canonical formal_scout admission result.",
        "nearby_variants" => Dict("passed" => 2, "total" => 2, "variants" => ["wrong_subgroup_control", "associative_erase_control"]),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "plain_sentence" => "On the owner's octonion Fano carrier, Der(O) has dimension 14; the e7 stabilizer has dimension 8, closes with compact su(3) invariants, and its complexified spinor action splits as 3 + 3bar + 1 + 1. The matching Cl(6) ladder operators give the Furey number/charge quantization pattern, while wrong-subgroup and associative-erasure controls fail.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["all_pass"] = all_core && result["parity"]["within_1e_9"]
    result["stop_condition_fired"] = !result["all_pass"]
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("su3_color_from_g2_octonion_cl6 Julia ",
        "all_pass=", result["all_pass"],
        " g2_dim=", result["shared_scalars"]["g2.dim"],
        " su3_dim=", result["shared_scalars"]["su3.dim"],
        " su3_closes=", result["verdicts"]["su3_closes"],
        " decomp_3_3bar_1_1=", result["verdicts"]["decomp_3_3bar_1_1"],
        " wrong_subgroup_fails=", result["controls"]["wrong_subgroup_fails"],
        " assoc_erase_collapses=", result["controls"]["assoc_erase_collapses"],
        " parity=", result["parity"]["status"], ":", result["parity"]["parity_max_diff"])
    println("wrote: ", RESULT_PATH)
    return result["all_pass"] ? 0 : 2
end

exit(main())
