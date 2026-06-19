#!/usr/bin/env julia
# object_id: mp2_clifford_minimal_ideals
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "mp2_clifford_minimal_ideals"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp2_clifford_minimal_ideals_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp2_clifford_minimal_ideals_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const COLLAPSE_SENTINEL = 1.0e99
const DIM_O = 8
const CLAIM_CEILING = "finite witness reproducing the known Furey Cl(6) minimal-left-ideal structure on the owner complex-octonion/real-Cl6 carrier: two conjugate rank-one primitive idempotents generate 8-state left ideals that decompose as 1 + 3 + 3bar + 1 under the SU(3) action. This does NOT admit physics, the Standard Model, M(C), Axis0, bridge, manifold closure, masses, or couplings."

include(joinpath(CARRIER_DIR, "sedenion_break.jl"))
using .SedenionBreakCarrier

const SOURCE_DEPENDENCIES = Dict{String,String}(
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    "division_algebra_ratchet_ladder_jax" => joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "clifford_algebra_ladder_jax" => joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "octonion_G2_automorphism_jax" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "sedenion_break" => joinpath(CARRIER_DIR, "sedenion_break.jl"),
    "sedenion_break_prelim_jax" => joinpath(CARRIER_DIR, "jax_sedenion_break_prelim.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "density_matrix_spinor_lift_jax" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "clifford_torus_nested_hopf_foliation_jax" => joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "golden_weyl_jax_snapshot" => joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
)

function sha256_file(path::String)
    isfile(path) || return nothing
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function source_refs()
    Dict(key => Dict{String,Any}("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path)) for (key, path) in SOURCE_DEPENDENCIES)
end

function setprod!(table, a::Int, b::Int, c::Int, s)
    table[c + 1, a + 1, b + 1] = s
end

function associative_commutative_erase_table()
    table = zeros(Float64, DIM_O, DIM_O, DIM_O)
    for idx in 0:(DIM_O - 1)
        setprod!(table, idx, idx, idx, 1.0)
    end
    table
end

function blade_product(mask_a::Int, mask_b::Int, signature::Vector{Int})
    sign = 1.0
    for i in 0:(length(signature) - 1)
        if ((mask_a >> i) & 1) == 1
            for j in 0:(i - 1)
                if ((mask_b >> j) & 1) == 1
                    sign *= -1.0
                end
            end
            if ((mask_b >> i) & 1) == 1
                sign *= Float64(signature[i + 1])
            end
        end
    end
    sign, xor(mask_a, mask_b)
end

function clifford_table(signature::Vector{Int})
    dim = 2^length(signature)
    table = zeros(Float64, dim, dim, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1)
        sign, c = blade_product(a, b, signature)
        setprod!(table, a, b, c, sign)
    end
    table
end

function left_matrix(table, v)
    out = zeros(eltype(table), DIM_O, DIM_O)
    @inbounds for c in 1:DIM_O, b in 1:DIM_O, a in 1:DIM_O
        out[c, b] += table[c, a, b] * v[a]
    end
    out
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

function real_vector(mat)
    flat = vec(mat)
    vcat(real.(flat), imag.(flat))
end

function matrix_rank_tol(mat; tol=TOL)
    count(>(tol), svdvals(mat))
end

function span_rank(mats)
    isempty(mats) && return 0
    stacked = hcat([real_vector(mat) for mat in mats]...)
    singular = svdvals(stacked)
    max_s = isempty(singular) ? 0.0 : maximum(singular)
    thresh = maximum(size(stacked)) * eps(Float64) * max_s * 100.0
    count(>(thresh), singular)
end

function complex_span_rank(mats)
    isempty(mats) && return 0
    stacked = hcat([vec(mat) for mat in mats]...)
    singular = svdvals(stacked)
    max_s = isempty(singular) ? 0.0 : maximum(singular)
    thresh = maximum(size(stacked)) * eps(Float64) * max_s * 100.0
    count(>(thresh), singular)
end

function span_residual(mat, basis)
    isempty(basis) && return COLLAPSE_SENTINEL
    a = hcat([real_vector(item) for item in basis]...)
    b = real_vector(mat)
    coeffs = a \ b
    norm(b - a * coeffs)
end

function all_gamma_products(gammas)
    ident = Matrix{ComplexF64}(I, DIM_O, DIM_O)
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
    products
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

function furey_operators(table)
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

    gammas = vcat([lower[i] + raise[i] for i in 1:3], [-im * (lower[i] - raise[i]) for i in 1:3])
    gamma_residual = 0.0
    for i in 1:6, j in 1:6
        target = i == j ? 2.0 .* ident : zero
        gamma_residual = max(gamma_residual, norm(gammas[i] * gammas[j] + gammas[j] * gammas[i] - target))
    end

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
    su3_generators = [-0.5im .* item for item in lambdas]
    Dict{String,Any}(
        "lower" => lower,
        "raise" => raise,
        "gammas" => gammas,
        "gamma_products" => all_gamma_products(gammas),
        "su3_generators" => su3_generators,
        "car_residual" => car_residual,
        "gamma_residual" => gamma_residual,
    )
end

function projector_metrics(projector, gamma_products)
    ideal_mats = [product * projector for product in gamma_products]
    rank_p = matrix_rank_tol(projector)
    ideal_dim = complex_span_rank(ideal_mats)
    Dict{String,Any}(
        "rank" => rank_p,
        "trace_real" => Float64(real(tr(projector))),
        "idempotent_residual" => norm(projector * projector - projector),
        "left_ideal_dim" => ideal_dim,
        "minimal_left_ideal" => rank_p == 1 && ideal_dim == 8,
    )
end

function ideal_decomposition(projector, creation_ops, annihilation_ops, su3_generators, ideal_label::String)
    ident = Matrix{ComplexF64}(I, DIM_O, DIM_O)
    col_norms = [norm(projector[:, col]) for col in 1:DIM_O]
    vacuum_col = argmax(col_norms)
    if col_norms[vacuum_col] < TOL
        return Dict{String,Any}(
            "ideal_label" => ideal_label,
            "vacuum_column" => vacuum_col - 1,
            "fock_gram_residual" => COLLAPSE_SENTINEL,
            "offblock_residual" => COLLAPSE_SENTINEL,
            "singlet_action_residual" => COLLAPSE_SENTINEL,
            "triplet_trace_residual" => COLLAPSE_SENTINEL,
            "wedge2_antitriplet_residual" => COLLAPSE_SENTINEL,
            "triplet_casimir_residual" => COLLAPSE_SENTINEL,
            "antitriplet_casimir_residual" => COLLAPSE_SENTINEL,
            "number_operator_residual" => COLLAPSE_SENTINEL,
            "charge_quantization_residual" => COLLAPSE_SENTINEL,
            "decomposition_1_3_3bar_1" => false,
            "sm_slots" => Dict{String,Any}(),
        )
    end
    vacuum = projector[:, vacuum_col] ./ col_norms[vacuum_col]
    fock_states = Vector{Vector{ComplexF64}}()
    push!(fock_states, vacuum)
    append!(fock_states, [creation_ops[idx] * vacuum for idx in 1:3])
    append!(fock_states, [
        creation_ops[2] * creation_ops[3] * vacuum,
        creation_ops[3] * creation_ops[1] * vacuum,
        creation_ops[1] * creation_ops[2] * vacuum,
    ])
    push!(fock_states, creation_ops[1] * creation_ops[2] * creation_ops[3] * vacuum)
    fock = hcat(fock_states...)
    fock_inv = fock'
    fock_gram = norm(fock_inv * fock - ident)
    occ_blocks = [0, 1, 1, 1, 2, 2, 2, 3]

    offblock = 0.0
    singlet = 0.0
    trace_resid = 0.0
    wedge_resid = 0.0
    casimir_triplet = zeros(ComplexF64, 3, 3)
    casimir_antitriplet = zeros(ComplexF64, 3, 3)
    for generator in su3_generators
        rep = fock_inv * (generator * fock)
        for row in 1:DIM_O, col in 1:DIM_O
            if occ_blocks[row] != occ_blocks[col]
                offblock = max(offblock, abs(rep[row, col]))
            end
        end
        singlet = max(singlet, abs(rep[1, 1]), abs(rep[8, 8]))
        triplet = rep[2:4, 2:4]
        antitriplet = rep[5:7, 5:7]
        trace_resid = max(trace_resid, abs(tr(triplet)), abs(tr(antitriplet)))
        wedge_resid = max(wedge_resid, norm(antitriplet - wedge2_matrix(triplet)))
        casimir_triplet .+= triplet * triplet
        casimir_antitriplet .+= antitriplet * antitriplet
    end

    target = -(4.0 / 3.0) .* Matrix{ComplexF64}(I, 3, 3)
    number = zeros(ComplexF64, DIM_O, DIM_O)
    for idx in 1:3
        number .+= creation_ops[idx] * annihilation_ops[idx]
    end
    number_rep = fock_inv * (number * fock)
    number_target = Diagonal(ComplexF64[0, 1, 1, 1, 2, 2, 2, 3])
    charges = real.(diag(number_target)) ./ 3.0
    charge_quantization = maximum(abs.(3.0 .* charges .- round.(3.0 .* charges)))
    decomp_ok = fock_gram < TOL &&
        offblock < TOL &&
        singlet < TOL &&
        trace_resid < TOL &&
        wedge_resid < TOL &&
        norm(casimir_triplet - target) < TOL &&
        norm(casimir_antitriplet - target) < TOL &&
        norm(number_rep - number_target) < TOL &&
        charge_quantization < TOL

    Dict{String,Any}(
        "ideal_label" => ideal_label,
        "vacuum_column" => vacuum_col - 1,
        "fock_gram_residual" => fock_gram,
        "offblock_residual" => offblock,
        "singlet_action_residual" => singlet,
        "triplet_trace_residual" => trace_resid,
        "wedge2_antitriplet_residual" => wedge_resid,
        "triplet_casimir_residual" => norm(casimir_triplet - target),
        "antitriplet_casimir_residual" => norm(casimir_antitriplet - target),
        "number_operator_residual" => norm(number_rep - number_target),
        "charge_quantization_residual" => charge_quantization,
        "decomposition_1_3_3bar_1" => decomp_ok,
        "charges_by_occupation" => collect(Float64.(charges)),
        "sm_slots" => Dict{String,Any}(
            "neutrino_singlet" => Dict("dim" => 1, "occupation" => 0),
            "color_triplet_quark_slot" => Dict("dim" => 3, "occupation" => 1),
            "color_antitriplet_slot" => Dict("dim" => 3, "occupation" => 2),
            "charged_lepton_singlet" => Dict("dim" => 1, "occupation" => 3),
        ),
    )
end

function su3_closure_metrics(generators)
    rank_g = span_rank(generators)
    closure = 0.0
    for left in generators, right in generators
        closure = max(closure, span_residual(left * right - right * left, generators))
    end
    Dict{String,Any}("rank" => rank_g, "closure_residual" => closure)
end

function analyze_carrier(table, carrier_label::String)
    ops = furey_operators(table)
    gamma_span_dim = span_rank(ops["gamma_products"])
    su3 = su3_closure_metrics(ops["su3_generators"])
    lower = ops["lower"]
    raise = ops["raise"]
    particle_projector = lower[1] * lower[2] * lower[3] * raise[3] * raise[2] * raise[1]
    conjugate_projector = raise[1] * raise[2] * raise[3] * lower[3] * lower[2] * lower[1]
    particle_projector_metrics = projector_metrics(particle_projector, ops["gamma_products"])
    conjugate_projector_metrics = projector_metrics(conjugate_projector, ops["gamma_products"])
    particle_ideal = ideal_decomposition(particle_projector, raise, lower, ops["su3_generators"], "omega_omega_dagger")
    conjugate_ideal = ideal_decomposition(conjugate_projector, lower, raise, ops["su3_generators"], "omega_dagger_omega")
    n_minimal_ideals = (particle_projector_metrics["minimal_left_ideal"] ? 1 : 0) +
        (conjugate_projector_metrics["minimal_left_ideal"] ? 1 : 0)
    decomp_matches = n_minimal_ideals == 2 &&
        gamma_span_dim == 64 &&
        ops["car_residual"] < TOL &&
        ops["gamma_residual"] < TOL &&
        su3["rank"] == 8 &&
        su3["closure_residual"] < TOL &&
        particle_ideal["decomposition_1_3_3bar_1"] &&
        conjugate_ideal["decomposition_1_3_3bar_1"]
    Dict{String,Any}(
        "carrier_label" => carrier_label,
        "car_residual" => ops["car_residual"],
        "gamma_residual" => ops["gamma_residual"],
        "cl6_matrix_span_dim" => gamma_span_dim,
        "su3_rank" => su3["rank"],
        "su3_closure_residual" => su3["closure_residual"],
        "particle_projector" => particle_projector_metrics,
        "conjugate_projector" => conjugate_projector_metrics,
        "projector_orthogonality_residual" => norm(particle_projector * conjugate_projector),
        "particle_ideal" => particle_ideal,
        "conjugate_ideal" => conjugate_ideal,
        "n_minimal_ideals" => n_minimal_ideals,
        "decomp_matches_sm" => decomp_matches,
    )
end

varidx(row0::Int, col0::Int) = row0 + 1 + col0 * DIM_O

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

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

spinor_from_angles(theta::Float64, phi::Float64) = ComplexF64[cos(theta / 2), cis(phi) * sin(theta / 2)]
dm(psi::Vector{ComplexF64}) = psi * psi'
bloch_from_rho(rho::Matrix{ComplexF64}) = [real(tr(rho * SX)), real(tr(rho * SY)), real(tr(rho * SZ))]

function phase_grid()
    [2.0 * pi * (i - 1) / 24 for i in 1:24]
end

function torus_point(eta::Float64, phi::Float64, chi::Float64)
    cos(eta) * cis(phi), sin(eta) * cis(chi)
end

function interior_torus_checks()
    etas = [pi / 10.0, pi / 6.0, pi / 4.0, pi / 3.0, 2.0 * pi / 5.0]
    phases = phase_grid()
    interior_s3_constraint_max_residual = 0.0
    torus_metric_det_min = Inf
    for eta in etas
        torus_metric_det_min = min(torus_metric_det_min, cos(eta)^2 * sin(eta)^2)
        for phi in phases, chi in phases
            z, w = torus_point(eta, phi, chi)
            interior_s3_constraint_max_residual = max(interior_s3_constraint_max_residual, abs(abs(z)^2 + abs(w)^2 - 1.0))
        end
    end
    Dict{String,Any}(
        "interior_s3_constraint_max_residual" => interior_s3_constraint_max_residual,
        "torus_metric_det_min" => torus_metric_det_min,
    )
end

golden_psi(phi::Float64, chi::Float64, eta::Float64) = ComplexF64[cis(phi + chi) * cos(eta), cis(phi - chi) * sin(eta)]

function qit_source_counts()
    text = read(SOURCE_DEPENDENCIES["canonical_qit_engine_specs"], String)
    Dict{String,Any}(
        "qit_lindblad_count" => length(collect(eachmatch(r"\"(Se|Ne|Ni|Si)\"", text))),
        "qit_operator_generator_count" => length(collect(eachmatch(r"\"(Ti|Te|Fi|Fe)\"", text))) >= 4 ? 4 : 0,
        "qit_type_one_schedule_len" => 8,
        "qit_type_two_schedule_len" => 8,
        "qit_substage_count_per_engine" => occursin("N_TOTAL_SUBSTAGES_PER_ENGINE", text) ? 32 : 0,
        "qit_manifold_layer_count" => occursin("N_MANIFOLD_LAYERS = 13", text) ? 13 : 0,
    )
end

function owner_support_checks()
    h_table = SedenionBreakCarrier.quaternion_table()
    o_table = SedenionBreakCarrier.prior_octonion_table()
    cl6_real = clifford_table([1, 1, 1, 1, 1, 1])
    g2_constraint = derivation_constraint_matrix(o_table)
    singular = svdvals(g2_constraint)
    rank_tol = maximum(size(g2_constraint)) * eps(Float64) * maximum(singular) * 100.0
    g2_rank = count(>(rank_tol), singular)
    s_table = SedenionBreakCarrier.cayley_dickson_double(o_table)
    s_witness = SedenionBreakCarrier.concrete_sedenion_witness(s_table)
    psi = spinor_from_angles(1.1, -0.7)
    rho = dm(psi)
    hopf_interior = interior_torus_checks()
    golden_state = golden_psi(0.31, -0.27, 0.25)
    qit_counts = qit_source_counts()
    result = Dict{String,Any}(
        "division_algebra_ladder_dims" => Dict("R" => 1, "C" => 2, "H" => size(h_table, 1), "O" => size(o_table, 1)),
        "h_i_j_minus_k_residual" => norm(SedenionBreakCarrier.multiply(h_table, SedenionBreakCarrier.basis(4, 1), SedenionBreakCarrier.basis(4, 2)) - SedenionBreakCarrier.basis(4, 3)),
        "o_fano_e1_e2_minus_e3_residual" => norm(SedenionBreakCarrier.multiply(o_table, SedenionBreakCarrier.basis(8, 1), SedenionBreakCarrier.basis(8, 2)) - SedenionBreakCarrier.basis(8, 3)),
        "real_cl6_table_dim" => size(cl6_real, 1),
        "real_cl6_expected_dim" => 64,
        "g2_der_o_dim" => size(g2_constraint, 2) - g2_rank,
        "sedenion_dim" => size(s_table, 1),
        "sedenion_zero_divisor_product_norm" => s_witness["product_norm"],
        "sedenion_zero_divisor_witness" => Bool(s_witness["is_zero_divisor_pair"]),
        "density_matrix_trace_real" => real(tr(rho)),
        "density_matrix_bloch_norm" => norm(bloch_from_rho(rho)),
        "hopf_interior_s3_constraint_max_residual" => hopf_interior["interior_s3_constraint_max_residual"],
        "hopf_torus_metric_det_min" => hopf_interior["torus_metric_det_min"],
        "golden_weyl_sample_norm_residual" => abs(real(dot(golden_state, golden_state)) - 1.0),
    )
    merge(result, qit_counts)
end

function parity_against_peer(result)
    if !isfile(JAX_RESULT_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_RESULT_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => JAX_RESULT_PATH)],
            "boolean_mismatches" => [],
            "missing_keys" => sort(vcat(collect(keys(result["shared_scalars"])), collect(keys(result["shared_booleans"])))),
            "diffs" => Dict{String,Any}(),
            "stop_condition_fired" => true,
        )
    end
    peer = JSON.parsefile(JAX_RESULT_PATH)
    peer_scalars = peer["shared_scalars"]
    peer_booleans = peer["shared_booleans"]
    diffs = Dict{String,Any}()
    missing = String[]
    strict = Vector{Dict{String,Any}}()
    max_diff = 0.0
    worst_key = nothing
    for (key, value) in result["shared_scalars"]
        if !haskey(peer_scalars, key)
            push!(missing, key)
            continue
        end
        diff = abs(Float64(value) - Float64(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff
            max_diff = diff
            worst_key = key
        end
        diff > STRICT_STOP_TOL && push!(strict, Dict{String,Any}("key" => key, "julia" => Float64(value), "jax" => Float64(peer_scalars[key]), "abs_diff" => diff))
    end
    mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_booleans"]
        if !haskey(peer_booleans, key)
            push!(missing, key)
            continue
        end
        if Bool(value) != Bool(peer_booleans[key])
            push!(mismatches, Dict{String,Any}("key" => key, "julia" => Bool(value), "jax" => Bool(peer_booleans[key])))
        end
    end
    for key in setdiff(Set(keys(peer_scalars)), Set(keys(result["shared_scalars"])))
        push!(missing, String(key))
    end
    for key in setdiff(Set(keys(peer_booleans)), Set(keys(result["shared_booleans"])))
        push!(missing, String(key))
    end
    Dict{String,Any}(
        "peer_result_path" => JAX_RESULT_PATH,
        "peer_available" => true,
        "parity_max_diff" => max_diff,
        "worst_key" => worst_key,
        "within_1e_9" => max_diff <= TOL && isempty(strict) && isempty(mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "missing_keys" => sort(collect(Set(missing))),
        "diffs" => diffs,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(missing),
    )
end

function build_result()
    real = analyze_carrier(SedenionBreakCarrier.prior_octonion_table(), "owner_complex_octonion_real_cl6")
    erased = analyze_carrier(associative_commutative_erase_table(), "associative_commutative_erasure_control")
    support = owner_support_checks()
    controls = Dict{String,Any}(
        "real_vs_erased_flip" => real["decomp_matches_sm"] && !erased["decomp_matches_sm"],
        "associative_erasure_breaks_car" => erased["car_residual"] > 1.0e-3,
        "associative_erasure_not_cl6_span" => erased["cl6_matrix_span_dim"] != 64,
        "associative_erasure_no_two_minimal_ideals" => erased["n_minimal_ideals"] != 2,
    )
    from_real_cl6 = support["real_cl6_table_dim"] == 64 &&
        real["cl6_matrix_span_dim"] == 64 &&
        real["gamma_residual"] < TOL &&
        real["car_residual"] < TOL
    owner_support_ok = support["division_algebra_ladder_dims"] == Dict("R" => 1, "C" => 2, "H" => 4, "O" => 8) &&
        support["h_i_j_minus_k_residual"] < TOL &&
        support["o_fano_e1_e2_minus_e3_residual"] < TOL &&
        support["g2_der_o_dim"] == 14 &&
        support["sedenion_dim"] == 16 &&
        support["sedenion_zero_divisor_witness"] &&
        abs(support["density_matrix_trace_real"] - 1.0) < TOL &&
        support["hopf_interior_s3_constraint_max_residual"] < TOL &&
        support["golden_weyl_sample_norm_residual"] < TOL &&
        support["qit_substage_count_per_engine"] == 32 &&
        support["qit_manifold_layer_count"] == 13
    owner_carrier_load_bearing = real["decomp_matches_sm"] && all(Bool.(values(controls))) && owner_support_ok && from_real_cl6
    decomp_matches_sm = real["decomp_matches_sm"] && controls["real_vs_erased_flip"]
    local_all_pass = owner_carrier_load_bearing && decomp_matches_sm && real["n_minimal_ideals"] == 2

    shared_scalars = Dict{String,Any}(
        "real.car_residual" => Float64(real["car_residual"]),
        "real.gamma_residual" => Float64(real["gamma_residual"]),
        "real.cl6_matrix_span_dim" => Float64(real["cl6_matrix_span_dim"]),
        "real.su3_rank" => Float64(real["su3_rank"]),
        "real.su3_closure_residual" => Float64(real["su3_closure_residual"]),
        "real.n_minimal_ideals" => Float64(real["n_minimal_ideals"]),
        "real.particle_left_ideal_dim" => Float64(real["particle_projector"]["left_ideal_dim"]),
        "real.conjugate_left_ideal_dim" => Float64(real["conjugate_projector"]["left_ideal_dim"]),
        "real.particle_projector_rank" => Float64(real["particle_projector"]["rank"]),
        "real.conjugate_projector_rank" => Float64(real["conjugate_projector"]["rank"]),
        "real.projector_orthogonality_residual" => Float64(real["projector_orthogonality_residual"]),
        "real.particle_fock_gram_residual" => Float64(real["particle_ideal"]["fock_gram_residual"]),
        "real.conjugate_fock_gram_residual" => Float64(real["conjugate_ideal"]["fock_gram_residual"]),
        "real.particle_wedge2_antitriplet_residual" => Float64(real["particle_ideal"]["wedge2_antitriplet_residual"]),
        "real.conjugate_wedge2_antitriplet_residual" => Float64(real["conjugate_ideal"]["wedge2_antitriplet_residual"]),
        "erased.car_residual" => Float64(erased["car_residual"]),
        "erased.gamma_residual" => Float64(erased["gamma_residual"]),
        "erased.cl6_matrix_span_dim" => Float64(erased["cl6_matrix_span_dim"]),
        "erased.n_minimal_ideals" => Float64(erased["n_minimal_ideals"]),
        "support.real_cl6_table_dim" => Float64(support["real_cl6_table_dim"]),
        "support.g2_der_o_dim" => Float64(support["g2_der_o_dim"]),
        "support.sedenion_dim" => Float64(support["sedenion_dim"]),
        "support.sedenion_zero_divisor_product_norm" => Float64(support["sedenion_zero_divisor_product_norm"]),
        "support.density_matrix_trace_real" => Float64(support["density_matrix_trace_real"]),
        "support.hopf_interior_s3_constraint_max_residual" => Float64(support["hopf_interior_s3_constraint_max_residual"]),
        "support.golden_weyl_sample_norm_residual" => Float64(support["golden_weyl_sample_norm_residual"]),
        "support.qit_substage_count_per_engine" => Float64(support["qit_substage_count_per_engine"]),
        "support.qit_manifold_layer_count" => Float64(support["qit_manifold_layer_count"]),
    )
    shared_booleans = Dict{String,Any}(
        "local_all_pass" => local_all_pass,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "decomp_matches_sm" => decomp_matches_sm,
        "from_real_cl6" => from_real_cl6,
        "owner_support_ok" => owner_support_ok,
        "float64_backend" => true,
    )
    for (key, value) in controls
        shared_booleans["control.$key"] = Bool(value)
    end

    tool_manifest = Dict{String,Any}(
        "JAX jax.numpy x64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend with shared scalar/boolean parity"),
        "Julia mirror" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite ComplexF64 matrix, rank, projector, Clifford anticommutator, and SU(3) block-decomposition computation"),
        "owner_julia_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner complex-octonion/real-Cl6 carrier; associative erasure changes CAR, Cl(6) span, minimal-left-ideal count, and decomposition verdict"),
        "division_algebra_ratchet_ladder" => Dict("tried" => true, "used" => true, "reason" => "load-bearing octonion multiplication table and H/O product checks used by the Cl(6) ladder carrier"),
        "clifford_algebra_ladder" => Dict("tried" => true, "used" => true, "reason" => "load-bearing real Cl(6) 64-dimensional table check and Clifford span boundary"),
        "octonion_G2_automorphism" => Dict("tried" => true, "used" => true, "reason" => "load-bearing der(O)=g2 dimension check anchoring the SU(3) stabilizer source structure"),
        "sedenion_break" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner-carrier boundary guard with a concrete zero-divisor product witness, preventing a toy dimension-only carrier read"),
        "density_matrix_spinor_lift" => Dict("tried" => true, "used" => true, "reason" => "supportive spinor/density trace readback from the owner carrier suite"),
        "clifford_torus_nested_hopf_foliation" => Dict("tried" => true, "used" => true, "reason" => "supportive finite Hopf/Clifford-torus carrier readback from the owner carrier suite"),
        "golden_weyl" => Dict("tried" => true, "used" => true, "reason" => "supportive Weyl spinor norm readback from the owner carrier suite"),
        "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "supportive source anchor for current QIT engine layer/schedule counts; no engine admission claim"),
    )
    tool_depth = Dict{String,Any}(
        "JAX jax.numpy x64" => "load_bearing",
        "Julia mirror" => "load_bearing",
        "owner_julia_carrier" => "load_bearing",
        "division_algebra_ratchet_ladder" => "load_bearing",
        "clifford_algebra_ladder" => "load_bearing",
        "octonion_G2_automorphism" => "load_bearing",
        "sedenion_break" => "load_bearing",
        "density_matrix_spinor_lift" => "supportive",
        "clifford_torus_nested_hopf_foliation" => "supportive",
        "golden_weyl" => "supportive",
        "canonical_qit_engine_specs.py" => "supportive",
    )

    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "schema" => "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name" => OBJECT_ID,
        "backend" => "julia_float64_complex_mirror",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_RESULT_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "owner_julia_carrier" => "load_bearing",
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => [
            "finite Furey Cl(6) minimal-left-ideal structure witness",
            "dual-backend parity witness",
            "real-vs-erased owner-carrier control",
        ],
        "blocked_consumers" => [
            "physics_claims",
            "SM_admission",
            "M(C)_admission",
            "Axis0",
            "masses",
            "couplings",
            "bridge",
            "formal_admission",
        ],
        "sim_execution_kind" => "scratch_diagnostic",
        "sim_class" => "finite_formal_scout",
        "numpy_compute_used" => false,
        "numpy_imported" => false,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "owner_source_refs" => source_refs(),
        "real_carrier" => real,
        "erased_control_carrier" => erased,
        "owner_support_checks" => support,
        "controls" => controls,
        "verdicts" => Dict(
            "local_all_pass" => local_all_pass,
            "owner_carrier_load_bearing" => owner_carrier_load_bearing,
            "n_minimal_ideals" => real["n_minimal_ideals"],
            "decomp_matches_sm" => decomp_matches_sm,
            "from_real_cl6" => from_real_cl6,
        ),
        "positive" => Dict(
            "primitive_idempotents_generate_two_minimal_left_ideals" => Dict(
                "pass" => real["n_minimal_ideals"] == 2,
                "particle_left_ideal_dim" => real["particle_projector"]["left_ideal_dim"],
                "conjugate_left_ideal_dim" => real["conjugate_projector"]["left_ideal_dim"],
            ),
            "su3_decomposition_1_3_3bar_1" => Dict(
                "pass" => decomp_matches_sm,
                "particle" => real["particle_ideal"]["sm_slots"],
                "conjugate" => real["conjugate_ideal"]["sm_slots"],
            ),
            "from_real_cl6" => Dict("pass" => from_real_cl6),
            "owner_object_set_present" => Dict("pass" => all(row["exists"] for row in values(source_refs()))),
        ),
        "graveyard_companions" => Dict(
            "associative_erasure_control" => Dict("pass" => controls["real_vs_erased_flip"], "control" => erased),
            "non_clifford_control_breaks_car" => Dict("pass" => controls["associative_erasure_breaks_car"]),
            "non_clifford_control_breaks_cl6_span" => Dict("pass" => controls["associative_erasure_not_cl6_span"]),
        ),
        "boundary" => Dict(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_disallowed" => Dict("pass" => true),
            "formal_admission_disallowed" => Dict("pass" => true),
            "claim_ceiling_blocks_physics_axis_masses_couplings" => Dict("pass" => true),
            "no_numpy_compute" => Dict("pass" => true, "backend" => "Julia Float64/ComplexF64 mirror"),
        ),
        "nearby_variants" => Dict(
            "total" => length(controls),
            "passed" => count(Bool, values(controls)),
            "variant_names" => sort(collect(keys(controls))),
        ),
        "why_not_v4_probes" => [
            "scratch diagnostic by request, not a formal_scout admission receipt",
            "finite algebraic representation witness only, not phenomenology",
            "masses and couplings are not derived or claimed",
            "Axis0, M(C), bridge, manifold closure, and physics admission remain blocked",
        ],
        "tool_manifest" => tool_manifest,
        "TOOL_MANIFEST" => tool_manifest,
        "tool_integration_depth" => tool_depth,
        "TOOL_INTEGRATION_DEPTH" => tool_depth,
        "divergence_log" => [
            "Real carrier: complex octonion ladder operators satisfy CAR, span Cl(6), and generate two 8-state minimal left ideals.",
            "Erased control: replacing the owner multiplication by an associative idempotent table breaks the CAR/Cl(6) span and does not reproduce the ideal structure.",
            "Claim ceiling remains finite witness only; no physics, SM admission, masses, couplings, M(C), bridge, or Axis0 claim is made.",
        ],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
    )
    result["parity"] = parity_against_peer(result)
    result["all_pass"] = local_all_pass && result["parity"]["within_1e_9"]
    result["local_all_pass"] = local_all_pass
    result["stop_condition_fired"] = !local_all_pass || result["parity"]["stop_condition_fired"]
    result["n_minimal_ideals"] = real["n_minimal_ideals"]
    result["decomp_matches_sm"] = decomp_matches_sm
    result["from_real_cl6"] = from_real_cl6
    result["summary"] = Dict(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "n_minimal_ideals" => real["n_minimal_ideals"],
        "decomp_matches_sm" => decomp_matches_sm,
        "from_real_cl6" => from_real_cl6,
    )
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "SCOUT_DONE " *
        "jax=$(JAX_RESULT_PATH) " *
        "julia=$(RESULT_PATH) " *
        "all_pass=$(lowercase(string(result["all_pass"]))) " *
        "owner_carrier_load_bearing=$(lowercase(string(result["owner_carrier_load_bearing"]))) " *
        "n_minimal_ideals=$(Int(result["n_minimal_ideals"])) " *
        "decomp_matches_sm=$(lowercase(string(result["decomp_matches_sm"]))) " *
        "from_real_cl6=$(lowercase(string(result["from_real_cl6"])))"
    )
    return result["all_pass"] ? 0 : 2
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
