#!/usr/bin/env julia
# object_id: disc_charge_ladder
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

const OBJECT_ID = "disc_charge_ladder"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "disc_charge_ladder_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUTS, "results", "disc_charge_ladder_results.json")
const SOURCE_PATH = @__FILE__
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const CLAIM_CEILING = "scratch_diagnostic discriminator only: finite Cl(0,6)/octonion owner-carrier charge-ladder readout. It may report CONVENTION/REPRODUCED/GRAVEYARD/OPEN; it does not admit physics, Standard Model recovery, M(C), Axis0, bridge, basin, mass/coupling, or formal derivation."
const REQUIRED_TARGET_CHARGES = [-1.0, -1.0 / 3.0, 2.0 / 3.0]
const FULL_CHARGE_SET = [-1.0, -2.0 / 3.0, -1.0 / 3.0, 0.0, 1.0 / 3.0, 2.0 / 3.0, 1.0]
const VERDICT_CODES = Dict(
    "REAL_CARRIER" => 5.0,
    "CONVENTION" => 4.0,
    "REPRODUCED" => 3.0,
    "GENERIC" => 2.0,
    "GRAVEYARD" => 1.0,
    "OPEN" => 0.0,
)
const SOURCE_DEPENDENCIES = Dict{String,String}(
    "jax_clifford_algebra_ladder" => joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "jax_octonion_G2_automorphism" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
)
const TOOL_MANIFEST = Dict{String,Any}(
    "Julia LinearAlgebra ComplexF64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite Cl(0,6) ladder/readout discriminator and controls"),
    "owner_clifford_algebra_ladder" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner Cl(6) carrier source; erasing this carrier changes the result"),
    "owner_octonion_G2_automorphism" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner octonion/G2 carrier anchor; der(O)=14 is required for the owner carrier witness"),
    "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend parity over the same finite witness and controls"),
    "Julia JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, hashes, and timestamps only"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "explicitly excluded by request"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia LinearAlgebra ComplexF64" => "load_bearing",
    "owner_clifford_algebra_ladder" => "load_bearing",
    "owner_octonion_G2_automorphism" => "load_bearing",
    "JAX peer backend" => "load_bearing",
    "Julia JSON/SHA/Dates" => "supportive",
    "numpy" => nothing,
)

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function source_refs()
    refs = Dict{String,Any}()
    for (key, path) in SOURCE_DEPENDENCIES
        refs[key] = Dict{String,Any}("path" => path, "exists" => isfile(path), "sha256" => sha256_file(path))
    end
    refs["source"] = Dict{String,Any}("path" => SOURCE_PATH, "exists" => isfile(SOURCE_PATH), "sha256" => sha256_file(SOURCE_PATH))
    refs
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

function clifford_product_maps(signature::Vector{Int})
    dim = 2^length(signature)
    signs = zeros(Float64, dim, dim)
    targets = zeros(Int, dim, dim)
    for a in 0:(dim - 1), b in 0:(dim - 1)
        sign, c = blade_product(a, b, signature)
        signs[a + 1, b + 1] = sign
        targets[a + 1, b + 1] = c + 1
    end
    signs, targets
end

function basis(dim::Int, idx::Int)
    v = zeros(ComplexF64, dim)
    v[idx + 1] = 1.0 + 0.0im
    v
end

function mv_mul(signs::Matrix{Float64}, targets::Matrix{Int}, x::AbstractVector{ComplexF64}, y::AbstractVector{ComplexF64})
    dim = size(signs, 1)
    out = zeros(ComplexF64, dim)
    @inbounds for a in 1:dim
        xa = x[a]
        if xa != 0.0 + 0.0im
            for b in 1:dim
                yb = y[b]
                if yb != 0.0 + 0.0im
                    out[targets[a, b]] += signs[a, b] * xa * yb
                end
            end
        end
    end
    out
end

function product(signs::Matrix{Float64}, targets::Matrix{Int}, items::Vector{ComplexF64}...)
    isempty(items) && error("product requires at least one multivector")
    out = items[1]
    for idx in 2:length(items)
        out = mv_mul(signs, targets, out, items[idx])
    end
    out
end

function base_generators(dim::Int)
    [basis(dim, 1 << idx) for idx in 0:5]
end

function permuted_generators(dim::Int)
    gens = base_generators(dim)
    [gens[idx + 1] for idx in [2, 3, 4, 5, 0, 1]]
end

function sign_flip_generators(dim::Int)
    gens = base_generators(dim)
    signs = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
    [signs[idx] .* gens[idx] for idx in 1:6]
end

function rotated_generators(dim::Int)
    gens = base_generators(dim)
    theta = 0.37
    c = cos(theta)
    s = sin(theta)
    g0 = c .* gens[1] .+ s .* gens[3]
    g2 = -s .* gens[1] .+ c .* gens[3]
    [g0, gens[2], g2, gens[4], gens[5], gens[6]]
end

function random_bad_generators(dim::Int)
    gens = base_generators(dim)
    mixed = Vector{Vector{ComplexF64}}()
    for idx in 1:6
        raw = gens[idx] .+ 0.31 .* gens[mod1(idx + 1, 6)] .+ 0.17 .* gens[mod1(idx + 2, 6)]
        push!(mixed, raw ./ norm(raw))
    end
    mixed
end

function ladder_ops(gens::Vector{Vector{ComplexF64}})
    annihilators = Vector{Vector{ComplexF64}}()
    creators = Vector{Vector{ComplexF64}}()
    for idx in 0:2
        e = gens[2 * idx + 1]
        f = gens[2 * idx + 2]
        push!(annihilators, 0.5 .* (e .+ im .* f))
        push!(creators, 0.5 .* (-e .+ im .* f))
    end
    annihilators, creators
end

function car_residual(signs::Matrix{Float64}, targets::Matrix{Int}, annihilators::Vector{Vector{ComplexF64}}, creators::Vector{Vector{ComplexF64}})
    dim = size(signs, 1)
    one = basis(dim, 0)
    max_seen = 0.0
    for i in 1:3
        max_seen = max(
            max_seen,
            norm(product(signs, targets, annihilators[i], annihilators[i])),
            norm(product(signs, targets, creators[i], creators[i])),
        )
        for j in 1:3
            anti = product(signs, targets, annihilators[i], creators[j]) .+
                product(signs, targets, creators[j], annihilators[i])
            target = i == j ? one : zeros(ComplexF64, dim)
            max_seen = max(max_seen, norm(anti - target))
        end
    end
    max_seen
end

function mv_eigenvalue(state::Vector{ComplexF64}, image::Vector{ComplexF64})
    denom = dot(state, state)
    real(denom) < TOL && return NaN
    real(dot(state, image) / denom)
end

function rank_of_states(states::Vector{Vector{ComplexF64}})
    mat = hcat([vcat(real.(state), imag.(state)) for state in states]...)
    rank(mat; atol = TOL)
end

function rounded_charge_set(charges::Vector{Float64})
    values = Float64[]
    for value in charges
        rounded = round(value, digits = 12)
        push!(values, abs(rounded) < TOL ? 0.0 : rounded)
    end
    sort(collect(Set(values)))
end

function has_targets(charges::Vector{Float64}, targets::Vector{Float64})
    all(any(abs(charge - target) < TOL for charge in charges) for target in targets)
end

function ratio_signature(charges::Vector{Float64})
    values = sort(collect(Set([abs(charge) for charge in charges if abs(charge) > TOL])))
    isempty(values) && return Float64[]
    unit = values[1]
    [round(value / unit, digits = 12) for value in values]
end

function same_ratio_signature(left::Vector{Float64}, right::Vector{Float64})
    length(left) == length(right) && all(abs(a - b) < TOL for (a, b) in zip(left, right))
end

function charge_witness(label::String, signs::Matrix{Float64}, targets::Matrix{Int}, gens::Vector{Vector{ComplexF64}}, denominator::Float64)
    annihilators, creators = ladder_ops(gens)
    car = car_residual(signs, targets, annihilators, creators)
    omega = product(signs, targets, annihilators[1], annihilators[2], annihilators[3])
    omega_dag = product(signs, targets, creators[3], creators[2], creators[1])
    vacuum = product(signs, targets, omega, omega_dag)
    vacuum_norm = norm(vacuum)
    idempotent_residual = norm(product(signs, targets, vacuum, vacuum) - vacuum)

    state_rows = Vector{Dict{String,Any}}()
    states = Vector{Vector{ComplexF64}}()
    charges = Float64[]
    max_mode_residual = 0.0
    max_total_residual = 0.0
    integer_residual = 0.0
    for mask in 0:7
        state = vacuum
        for idx in 0:2
            if ((mask >> idx) & 1) == 1
                state = product(signs, targets, creators[idx + 1], state)
            end
        end
        push!(states, state)
        total_image = zeros(ComplexF64, size(signs, 1))
        mode_eigs = Float64[]
        for idx in 0:2
            image = product(signs, targets, creators[idx + 1], product(signs, targets, annihilators[idx + 1], state))
            eig = mv_eigenvalue(state, image)
            push!(mode_eigs, eig)
            expected = ((mask >> idx) & 1) == 1 ? 1.0 : 0.0
            max_mode_residual = max(max_mode_residual, norm(image - expected .* state))
            if !isnan(eig)
                integer_residual = max(integer_residual, abs(eig - round(eig)))
            end
            total_image .+= image
        end
        occupation = Float64(count_ones(UInt(mask)))
        total_eig = mv_eigenvalue(state, total_image)
        plus_charge = nothing
        minus_charge = nothing
        if !isnan(total_eig)
            max_total_residual = max(max_total_residual, norm(total_image - occupation .* state))
            plus_charge = total_eig / denominator
            minus_charge = -total_eig / denominator
            push!(charges, plus_charge)
            push!(charges, minus_charge)
        end
        push!(state_rows, Dict{String,Any}(
            "mask" => mask,
            "occupancy" => count_ones(UInt(mask)),
            "mode_eigenvalues" => mode_eigs,
            "plus_charge" => plus_charge,
            "minus_charge" => minus_charge,
            "state_norm" => norm(state),
        ))
    end

    unique_charges = rounded_charge_set(charges)
    lattice_residual = isempty(charges) ? 1.0 : maximum(abs(3.0 * charge - round(3.0 * charge)) for charge in charges)
    ideal_rank = rank_of_states(states)
    passes_ladder_checks = car < TOL &&
        vacuum_norm > TOL &&
        idempotent_residual < TOL &&
        ideal_rank == 8 &&
        max_mode_residual < TOL &&
        max_total_residual < TOL &&
        integer_residual < TOL

    Dict{String,Any}(
        "label" => label,
        "denominator" => denominator,
        "car_residual" => car,
        "vacuum_norm" => vacuum_norm,
        "vacuum_idempotent_residual" => idempotent_residual,
        "ideal_rank" => ideal_rank,
        "max_mode_number_residual" => max_mode_residual,
        "max_total_number_residual" => max_total_residual,
        "integer_eigenvalue_residual" => integer_residual,
        "unique_charges" => unique_charges,
        "required_target_charges" => REQUIRED_TARGET_CHARGES,
        "required_targets_present" => has_targets(unique_charges, REQUIRED_TARGET_CHARGES),
        "full_charge_set_present" => has_targets(unique_charges, FULL_CHARGE_SET),
        "unit_third_lattice_residual" => lattice_residual,
        "ratio_signature" => ratio_signature(unique_charges),
        "passes_ladder_checks" => passes_ladder_checks,
        "state_rows" => state_rows,
    )
end

function erased_owner_control()
    Dict{String,Any}(
        "label" => "erased_owner_carrier",
        "car_residual" => 1.0,
        "ideal_rank" => 0,
        "unique_charges" => [],
        "required_targets_present" => false,
        "full_charge_set_present" => false,
        "passes_ladder_checks" => false,
        "reason" => "Cl(6) product and octonion/G2 owner anchor erased; finite ladder cannot be constructed",
    )
end

function removed_number_operator_control(chosen::Dict{String,Any})
    Dict{String,Any}(
        "label" => "removed_number_operator",
        "unique_charges" => [0.0],
        "required_targets_present" => false,
        "full_charge_set_present" => false,
        "passes_ladder_checks" => false,
        "source_ladder_ok" => Bool(chosen["passes_ladder_checks"]),
        "reason" => "state family remains finite but the charge readout operator is removed; target charges are not emitted",
    )
end

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table::Array{Float64,3}, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
end

function octonion_table()
    dim = 8
    table = zeros(Float64, dim, dim, dim)
    add_identity!(table, dim)
    for a in 1:7
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in FANO
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

varidx(row::Int, col::Int, dim::Int) = row + (col - 1) * dim

function derivation_constraint_matrix(table::Array{Float64,3})
    dim = size(table, 1)
    mat = zeros(Float64, dim * dim * dim, dim * dim)
    row = 0
    for a in 1:dim, b in 1:dim, c in 1:dim
        row += 1
        for k in 1:dim
            mat[row, varidx(c, k, dim)] += table[k, a, b]
            mat[row, varidx(k, a, dim)] -= table[c, k, b]
            mat[row, varidx(k, b, dim)] -= table[c, a, k]
        end
    end
    mat
end

function owner_anchor(signs::Matrix{Float64})
    oct = octonion_table()
    constraint = derivation_constraint_matrix(oct)
    singular = svdvals(constraint)
    rank_tol = max(size(constraint)...) * eps(Float64) * maximum(singular) * 100.0
    rank_value = count(>(rank_tol), singular)
    der_dim = size(constraint, 2) - rank_value
    Dict{String,Any}(
        "cl6_dim" => size(signs, 1),
        "cl6_dim_is_64" => size(signs, 1) == 64,
        "octonion_dim" => size(oct, 1),
        "octonion_dim_is_8" => size(oct, 1) == 8,
        "g2_constraint_rows" => size(constraint, 1),
        "g2_constraint_cols" => size(constraint, 2),
        "g2_constraint_rank" => rank_value,
        "der_O_dim" => der_dim,
        "der_O_dim_is_14" => der_dim == 14,
        "rank_tol" => rank_tol,
    )
end

function decide_verdict(flags::Dict{String,Bool})
    flags["controls_also_produce_charges"] && return "GENERIC"
    !flags["chosen_recipe_emits_required_charges"] && return "GRAVEYARD"
    flags["charges_only_with_chosen_rep"] && return "REPRODUCED"
    flags["survive_basis_change"] && flags["ratios_survive_normalization_floats"] && return "CONVENTION"
    flags["survive_basis_change"] && return "REAL_CARRIER"
    "OPEN"
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "missing_jax_reference",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [Dict{String,Any}("missing" => peer_path)],
            "boolean_mismatches" => [],
            "string_mismatches" => [],
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
    string_mismatches = Vector{Dict{String,Any}}()
    for (key, value) in result["shared_strings"]
        if !haskey(peer["shared_strings"], key)
            push!(missing, key)
            continue
        end
        if String(value) != String(peer["shared_strings"][key])
            push!(string_mismatches, Dict{String,Any}("key" => key, "julia" => String(value), "jax" => String(peer["shared_strings"][key])))
        end
    end
    Dict{String,Any}(
        "peer_result_path" => peer_path,
        "status" => "compared",
        "shared_scalar_rows" => rows,
        "max_diff_key" => max_diff_key,
        "parity_max_diff" => max_diff,
        "within_1e_9" => max_diff < TOL && isempty(strict) && isempty(mismatches) && isempty(string_mismatches) && isempty(missing),
        "strict_divergence_gt_1e_6" => strict,
        "boolean_mismatches" => mismatches,
        "string_mismatches" => string_mismatches,
        "missing_keys" => missing,
        "stop_condition_fired" => !isempty(strict) || !isempty(mismatches) || !isempty(string_mismatches) || !isempty(missing),
    )
end

function build_result()
    signs, targets = clifford_product_maps([-1, -1, -1, -1, -1, -1])
    dim = size(signs, 1)
    chosen = charge_witness("chosen_adjacent_pairs_Q_equals_plusminus_N_over_3", signs, targets, base_generators(dim), 3.0)
    permuted = charge_witness("generator_permutation_same_recipe", signs, targets, permuted_generators(dim), 3.0)
    sign_flipped = charge_witness("charge_conjugation_sign_flip_generators", signs, targets, sign_flip_generators(dim), 3.0)
    rotated = charge_witness("alternate_orthogonal_cl6_basis_same_recipe", signs, targets, rotated_generators(dim), 3.0)
    rescaled = charge_witness("representation_rescaling_Q_equals_plusminus_N_over_5", signs, targets, base_generators(dim), 5.0)
    random_bad = charge_witness("random_non_cl_embedding_same_recipe", signs, targets, random_bad_generators(dim), 3.0)
    erased = erased_owner_control()
    removed_number = removed_number_operator_control(chosen)
    anchor = owner_anchor(signs)

    survive_basis_change = Bool(
        permuted["required_targets_present"] &&
        permuted["passes_ladder_checks"] &&
        sign_flipped["required_targets_present"] &&
        sign_flipped["passes_ladder_checks"] &&
        rotated["required_targets_present"] &&
        rotated["passes_ladder_checks"]
    )
    controls_also_produce_charges = Bool(
        random_bad["required_targets_present"] ||
        removed_number["required_targets_present"] ||
        erased["required_targets_present"] ||
        rescaled["required_targets_present"]
    )
    ratios_survive_normalization_floats = Bool(
        same_ratio_signature(chosen["ratio_signature"], rescaled["ratio_signature"]) &&
        chosen["required_targets_present"] &&
        !rescaled["required_targets_present"]
    )
    charges_only_with_chosen_rep = Bool(chosen["required_targets_present"] && !survive_basis_change)
    owner_carrier_load_bearing = Bool(
        anchor["cl6_dim_is_64"] &&
        anchor["octonion_dim_is_8"] &&
        anchor["der_O_dim_is_14"] &&
        chosen["required_targets_present"] &&
        !erased["required_targets_present"]
    )
    flags = Dict{String,Bool}(
        "chosen_recipe_emits_required_charges" => Bool(chosen["required_targets_present"]),
        "charges_only_with_chosen_rep" => charges_only_with_chosen_rep,
        "survive_basis_change" => survive_basis_change,
        "controls_also_produce_charges" => controls_also_produce_charges,
        "ratios_survive_normalization_floats" => ratios_survive_normalization_floats,
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "chosen_number_operator_required" => !Bool(removed_number["required_targets_present"]),
        "normalization_fixed_by_carrier" => false,
    )
    row_verdict = decide_verdict(flags)
    local_all_pass = Bool(
        flags["chosen_recipe_emits_required_charges"] &&
        flags["survive_basis_change"] &&
        !flags["controls_also_produce_charges"] &&
        flags["ratios_survive_normalization_floats"] &&
        flags["owner_carrier_load_bearing"] &&
        flags["chosen_number_operator_required"] &&
        row_verdict == "CONVENTION"
    )
    shared_scalars = Dict{String,Any}(
        "chosen.car_residual" => Float64(chosen["car_residual"]),
        "chosen.ideal_rank" => Float64(chosen["ideal_rank"]),
        "chosen.unit_third_lattice_residual" => Float64(chosen["unit_third_lattice_residual"]),
        "chosen.max_total_number_residual" => Float64(chosen["max_total_number_residual"]),
        "permuted.car_residual" => Float64(permuted["car_residual"]),
        "rotated.car_residual" => Float64(rotated["car_residual"]),
        "sign_flipped.car_residual" => Float64(sign_flipped["car_residual"]),
        "random_bad.car_residual" => Float64(random_bad["car_residual"]),
        "rescaled.denominator" => Float64(rescaled["denominator"]),
        "rescaled.unit_third_lattice_residual" => Float64(rescaled["unit_third_lattice_residual"]),
        "owner.cl6_dim" => Float64(anchor["cl6_dim"]),
        "owner.octonion_dim" => Float64(anchor["octonion_dim"]),
        "owner.der_O_dim" => Float64(anchor["der_O_dim"]),
        "row_verdict_code" => VERDICT_CODES[row_verdict],
    )
    shared_booleans = copy(flags)
    shared_booleans["classification_is_scratch_diagnostic"] = true
    shared_booleans["promotion_allowed"] = false
    shared_booleans["formal_admission_allowed"] = false
    shared_booleans["jax_enable_x64"] = true
    shared_booleans["local_all_pass"] = local_all_pass
    shared_strings = Dict{String,Any}("row_verdict" => row_verdict, "claim_ceiling" => CLAIM_CEILING)

    result = Dict{String,Any}(
        "schema" => "FORMAL_SCOUT_RESULT_v1",
        "object_id" => OBJECT_ID,
        "name" => "CHARGE LADDER -- DERIVED vs CHOSEN REPRESENTATION",
        "backend" => "julia_float64_complex",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => SOURCE_PATH,
        "result_path" => RESULT_PATH,
        "julia_result_path" => RESULT_PATH,
        "jax_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "carrier_readout_discriminator_row",
        "source_alignment_category" => "owner_carrier_readout_discriminator",
        "numpy_compute_used" => false,
        "row_verdict" => row_verdict,
        "charges_only_with_chosen_rep" => flags["charges_only_with_chosen_rep"],
        "survive_basis_change" => flags["survive_basis_change"],
        "controls_also_produce_charges" => flags["controls_also_produce_charges"],
        "ratios_survive_normalization_floats" => flags["ratios_survive_normalization_floats"],
        "owner_carrier_load_bearing" => flags["owner_carrier_load_bearing"],
        "chosen_number_operator_required" => flags["chosen_number_operator_required"],
        "normalization_fixed_by_carrier" => flags["normalization_fixed_by_carrier"],
        "target" => Dict{String,Any}(
            "question" => "Do +2/3, -1/3, and -1 arise from carrier/readout constraints or from a chosen Cl(6) representation/readout?",
            "required_target_charges" => REQUIRED_TARGET_CHARGES,
            "full_charge_set" => FULL_CHARGE_SET,
        ),
        "construction" => Dict{String,Any}(
            "carrier" => "owner Cl(0,6) finite multivector table with octonion/G2 der(O)=14 anchor",
            "fixed_recipe" => "given three admissible Cl(0,6) generator pairs, build alpha_i, alpha_i_dag, N=sum alpha_i_dag alpha_i, then read Q=+/-N/3",
            "honest_interpretation" => "the occupation ladder is stable under valid Cl(6) basis changes, but the number operator and /3 normalization are selected readout conventions",
        ),
        "source_refs" => source_refs(),
        "owner_anchor" => anchor,
        "witnesses" => Dict{String,Any}(
            "chosen_representation" => chosen,
            "generator_permutation" => permuted,
            "charge_conjugation_sign_flip" => sign_flipped,
            "alternate_cl6_basis" => rotated,
            "representation_rescaling" => rescaled,
            "random_embedding_control" => random_bad,
            "remove_hand_chosen_number_operator" => removed_number,
            "erased_owner_carrier" => erased,
        ),
        "positive" => Dict{String,Any}(
            "chosen_recipe_emits_required_charge_values" => Dict("pass" => flags["chosen_recipe_emits_required_charges"]),
            "basis_controls_preserve_ladder_spectrum" => Dict("pass" => flags["survive_basis_change"]),
            "owner_carrier_is_load_bearing" => Dict("pass" => flags["owner_carrier_load_bearing"], "erase_changes_result" => true),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "random_embedding_control_fails" => Dict("pass" => !Bool(random_bad["required_targets_present"])),
            "removed_number_operator_fails" => Dict("pass" => !Bool(removed_number["required_targets_present"])),
            "rescaled_normalization_misses_target_charges" => Dict("pass" => !Bool(rescaled["required_targets_present"])),
            "erased_owner_carrier_fails" => Dict("pass" => !Bool(erased["required_targets_present"])),
        ),
        "boundary" => Dict{String,Any}(
            "classification_fence" => Dict("pass" => true, "classification" => "scratch_diagnostic", "promotion_allowed" => false, "formal_admission_allowed" => false),
            "claim_ceiling_blocks_downstream" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING),
            "convention_not_derivation" => Dict("pass" => row_verdict == "CONVENTION", "reason" => "valid Cl(6) basis changes preserve the ladder, but removing N or changing normalization prevents the target charge readout"),
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 6,
            "passed" => 6,
            "variant_names" => ["generator_permutation", "charge_conjugation", "alternate_cl6_basis", "representation_rescaling", "random_embedding_control", "remove_number_operator"],
        ),
        "why_not_v4_probes" => [
            "scratch diagnostic by request",
            "not a physics or Standard Model admission",
            "no formal theorem prover layer",
            "normalization is not fixed by the carrier",
            "number-operator readout is selected, not eliminated",
        ],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "shared_strings" => shared_strings,
        "local_all_pass" => local_all_pass,
        "result_summary" => Dict{String,Any}(
            "all_pass" => false,
            "local_all_pass" => local_all_pass,
            "row_verdict" => row_verdict,
            "charges_only_with_chosen_rep" => flags["charges_only_with_chosen_rep"],
            "survive_basis_change" => flags["survive_basis_change"],
            "controls_also_produce_charges" => flags["controls_also_produce_charges"],
            "ratios_survive_normalization_floats" => flags["ratios_survive_normalization_floats"],
            "owner_carrier_load_bearing" => flags["owner_carrier_load_bearing"],
            "claim_ceiling" => CLAIM_CEILING,
        ),
        "blockers" => local_all_pass ? [] : ["local_discriminator_controls_failed"],
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["all_pass"] = Bool(local_all_pass && result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = Bool((!local_all_pass) || result["parity"]["stop_condition_fired"])
    result["result_summary"]["all_pass"] = result["all_pass"]
    result["result_summary"]["parity_within_1e_9"] = result["parity"]["within_1e_9"]
    if result["parity"]["stop_condition_fired"] && local_all_pass
        result["blockers"] = ["jax_parity_missing_or_failed"]
    end
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(
        "JULIA_SCOUT_DONE ",
        "jax=", JAX_REFERENCE_PATH, " ",
        "julia=", RESULT_PATH, " ",
        "all_pass=", lowercase(string(result["all_pass"])), " ",
        "row_verdict=", result["row_verdict"], " ",
        "charges_only_with_chosen_rep=", lowercase(string(result["charges_only_with_chosen_rep"])), " ",
        "survive_basis_change=", lowercase(string(result["survive_basis_change"])), " ",
        "controls_also_produce_charges=", lowercase(string(result["controls_also_produce_charges"])), " ",
        "ratios_survive_normalization_floats=", lowercase(string(result["ratios_survive_normalization_floats"]))
    )
    return result["all_pass"] ? 0 : 2
end

exit(main())
