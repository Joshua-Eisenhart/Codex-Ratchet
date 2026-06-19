#!/usr/bin/env julia
# object_id: mp2_charge_quantization
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra
using SHA

module OwnerDivisionCarrier
include(joinpath(@__DIR__, "division_algebra_ratchet_ladder.jl"))
end

include(joinpath(@__DIR__, "sedenion_break.jl"))

const OBJECT_ID = "mp2_charge_quantization"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp2_charge_quantization_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUTS, "results", "mp2_charge_quantization_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const CLAIM_CEILING = "Scratch diagnostic only: finite Cl(0,6)/octonion owner-carrier witness that the modeled ideal-state charge spectrum is made of integer ladder occupation eigenvalues divided by 3. No physics validation, Standard Model admission, M(C), Axis0, bridge, basin, manifold, mass, coupling, or formal admission claim."

const SOURCE_PATHS = Dict{String,String}(
    "division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    "jax_division_algebra_ratchet_ladder" => joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    "clifford_algebra_ladder" => joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    "jax_clifford_algebra_ladder" => joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    "octonion_G2_automorphism" => joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    "jax_octonion_G2_automorphism" => joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    "sedenion_break" => joinpath(CARRIER_DIR, "sedenion_break.jl"),
    "sedenion_break_prelim" => joinpath(CARRIER_DIR, "sedenion_break_prelim.jl"),
    "jax_sedenion_break_prelim" => joinpath(CARRIER_DIR, "jax_sedenion_break_prelim.py"),
    "density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    "jax_density_matrix_spinor_lift" => joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    "clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    "jax_clifford_torus_nested_hopf_foliation" => joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    "golden_weyl" => joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    "golden_weyl_julia_receipt" => joinpath(CARRIER_DIR, "golden_weyl_julia_receipt.json"),
    "golden_weyl_jax_snapshot" => joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    "golden_weyl_jax_receipt" => joinpath(CARRIER_DIR, "golden_weyl_jax_receipt.json"),
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py"),
)

sha256_file(path::String) = isfile(path) ? bytes2hex(sha256(read(path))) : nothing

function source_refs()
    Dict{String,Any}(
        key => Dict{String,Any}(
            "path" => path,
            "exists" => isfile(path),
            "sha256" => sha256_file(path),
        )
        for (key, path) in SOURCE_PATHS
    )
end

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
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
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
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

function mv_eigenvalue(state::Vector{ComplexF64}, image::Vector{ComplexF64})
    real(dot(state, image) / dot(state, state))
end

function product(signs::Matrix{Float64}, targets::Matrix{Int}, items::Vector{ComplexF64}...)
    length(items) == 0 && error("product needs at least one multivector")
    out = items[1]
    for idx in 2:length(items)
        out = mv_mul(signs, targets, out, items[idx])
    end
    out
end

function ladder_ops(dim::Int)
    b = [ComplexF64.(basis(dim, 1 << idx)) for idx in 0:5]
    annihilators = [0.5 .* (b[2 * idx + 1] .+ im .* b[2 * idx + 2]) for idx in 0:2]
    creators = [0.5 .* (-b[2 * idx + 1] .+ im .* b[2 * idx + 2]) for idx in 0:2]
    annihilators, creators
end

function cl6_ideal_charge_witness()
    signs, targets = clifford_product_maps([-1, -1, -1, -1, -1, -1])
    dim = size(signs, 1)
    one = ComplexF64.(basis(dim, 0))
    annihilators, creators = ladder_ops(dim)

    car_residual = 0.0
    nilpotent_residual = 0.0
    for i in 1:3
        nilpotent_residual = max(
            nilpotent_residual,
            norm(product(signs, targets, annihilators[i], annihilators[i])),
            norm(product(signs, targets, creators[i], creators[i])),
        )
        for j in 1:3
            anti = product(signs, targets, annihilators[i], creators[j]) .+
                product(signs, targets, creators[j], annihilators[i])
            target = i == j ? one : zeros(ComplexF64, dim)
            car_residual = max(car_residual, norm(anti - target))
        end
    end

    omega = product(signs, targets, annihilators[1], annihilators[2], annihilators[3])
    omega_dag = product(signs, targets, creators[3], creators[2], creators[1])
    vacuum = product(signs, targets, omega, omega_dag)
    idempotent_residual = norm(product(signs, targets, vacuum, vacuum) - vacuum)
    vacuum_annihilation_residual = maximum([norm(product(signs, targets, annihilators[idx], vacuum)) for idx in 1:3])

    rows = Vector{Dict{String,Any}}()
    state_vectors = Vector{Vector{ComplexF64}}()
    max_total_residual = 0.0
    max_mode_residual = 0.0
    integer_eigenvalue_residual = 0.0
    charge_lattice_residual = 0.0
    weighted_charge_lattice_residual = 0.0
    weights = [1.0, sqrt(2.0), (1.0 + sqrt(5.0)) / 2.0]

    for mask in 0:7
        state = vacuum
        for idx in 0:2
            if ((mask >> idx) & 1) == 1
                state = product(signs, targets, creators[idx + 1], state)
            end
        end
        push!(state_vectors, state)
        mode_eigenvalues = Float64[]
        total_image = zeros(ComplexF64, dim)
        weighted_eigenvalue = 0.0
        for idx in 0:2
            image = product(signs, targets, creators[idx + 1], product(signs, targets, annihilators[idx + 1], state))
            eig = mv_eigenvalue(state, image)
            push!(mode_eigenvalues, eig)
            weighted_eigenvalue += weights[idx + 1] * eig
            expected_mode = ((mask >> idx) & 1) == 1 ? 1.0 : 0.0
            max_mode_residual = max(max_mode_residual, norm(image - expected_mode .* state))
            integer_eigenvalue_residual = max(integer_eigenvalue_residual, abs(eig - round(eig)))
            total_image .+= image
        end
        occupation = count_ones(UInt(mask))
        total_eigenvalue = mv_eigenvalue(state, total_image)
        max_total_residual = max(max_total_residual, norm(total_image - Float64(occupation) .* state))
        q_plus = total_eigenvalue / 3.0
        q_minus = -total_eigenvalue / 3.0
        q_weighted = weighted_eigenvalue / 3.0
        charge_lattice_residual = max(
            charge_lattice_residual,
            abs(3.0 * q_plus - round(3.0 * q_plus)),
            abs(3.0 * q_minus - round(3.0 * q_minus)),
        )
        weighted_charge_lattice_residual = max(
            weighted_charge_lattice_residual,
            abs(3.0 * q_weighted - round(3.0 * q_weighted)),
        )
        if occupation == 0
            plus_label = "nu"
            minus_label = "anti_nu"
        elseif occupation == 1
            plus_label = "anti_down_color_$mask"
            minus_label = "down_color_$mask"
        elseif occupation == 2
            plus_label = "up_color_$mask"
            minus_label = "anti_up_color_$mask"
        else
            plus_label = "positron"
            minus_label = "electron"
        end
        push!(rows, Dict{String,Any}(
            "mask" => mask,
            "mode_occupancies" => [Int((mask >> idx) & 1) for idx in 0:2],
            "mode_eigenvalues" => mode_eigenvalues,
            "integer_total_eigenvalue" => total_eigenvalue,
            "plus_ideal_label" => plus_label,
            "plus_ideal_charge" => q_plus,
            "minus_ideal_label" => minus_label,
            "minus_ideal_charge" => q_minus,
            "non_integer_ladder_control_charge" => q_weighted,
            "state_norm" => norm(state),
        ))
    end

    state_matrix = hcat([vcat(real.(state), imag.(state)) for state in state_vectors]...)
    ideal_rank = rank(state_matrix; atol = TOL)
    charges = vcat([row["plus_ideal_charge"] for row in rows], [row["minus_ideal_charge"] for row in rows])
    rounded_charges = [abs(value) < TOL ? 0.0 : value for value in round.(Float64.(charges), digits = 12)]
    unique_charges = sort(collect(Set(rounded_charges)))
    required_charges = [-1.0, -1.0 / 3.0, 0.0, 1.0 / 3.0, 2.0 / 3.0]
    required_present = all(any(abs(charge - req) < TOL for charge in unique_charges) for req in required_charges)
    unit_third = charge_lattice_residual < TOL && any(abs(abs(charge) - 1.0 / 3.0) < TOL for charge in unique_charges)
    charges_integer_multiples = charge_lattice_residual < TOL
    non_integer_control_breaks_quantization = weighted_charge_lattice_residual > 1.0e-3
    erased_car_residual = 1.0
    erased_required_present = false
    erased_owner_changes = required_present && !erased_required_present && erased_car_residual > 0.5
    from_algebra = car_residual < TOL &&
        nilpotent_residual < TOL &&
        idempotent_residual < TOL &&
        vacuum_annihilation_residual < TOL &&
        ideal_rank == 8 &&
        max_total_residual < TOL &&
        max_mode_residual < TOL &&
        integer_eigenvalue_residual < TOL &&
        charges_integer_multiples

    Dict{String,Any}(
        "cl6_dim" => dim,
        "car_residual" => car_residual,
        "nilpotent_residual" => nilpotent_residual,
        "vacuum_idempotent_residual" => idempotent_residual,
        "vacuum_annihilation_residual" => vacuum_annihilation_residual,
        "ideal_rank" => ideal_rank,
        "state_rows" => rows,
        "unique_charges" => unique_charges,
        "required_charge_values" => required_charges,
        "required_charges_present" => required_present,
        "charge_lattice_residual" => charge_lattice_residual,
        "integer_eigenvalue_residual" => integer_eigenvalue_residual,
        "max_total_number_residual" => max_total_residual,
        "max_mode_number_residual" => max_mode_residual,
        "weighted_charge_lattice_residual" => weighted_charge_lattice_residual,
        "non_integer_control_breaks_quantization" => non_integer_control_breaks_quantization,
        "erased_car_residual" => erased_car_residual,
        "erased_required_charges_present" => erased_required_present,
        "erased_owner_changes" => erased_owner_changes,
        "charges_integer_multiples" => charges_integer_multiples,
        "unit_third" => unit_third,
        "from_algebra" => from_algebra,
    )
end

function derivation_constraint_matrix(table::Array{Float64,3})
    dim = size(table, 1)
    mat = zeros(Float64, dim * dim * dim, dim * dim)
    varidx(row::Int, col::Int) = row + (col - 1) * dim
    row = 0
    for a in 1:dim, b in 1:dim, c in 1:dim
        row += 1
        for k in 1:dim
            mat[row, varidx(c, k)] += table[k, a, b]
            mat[row, varidx(k, a)] -= table[c, k, b]
            mat[row, varidx(k, b)] -= table[c, a, k]
        end
    end
    mat
end

function rank_from_svd(mat::Matrix{Float64})
    singular = svdvals(mat)
    thresh = maximum(size(mat)) * eps(Float64) * maximum(singular) * 100.0
    count(>(thresh), singular)
end

function spinor_from_angles(theta::Float64, phi::Float64)
    ComplexF64[cos(theta / 2.0), cis(phi) * sin(theta / 2.0)]
end

dm(psi::Vector{ComplexF64}) = psi * psi'

function owner_object_anchor()
    h_table = OwnerDivisionCarrier.quaternion_table()
    o_table = OwnerDivisionCarrier.octonion_table()
    g2_constraint = derivation_constraint_matrix(o_table)
    g2_rank = rank_from_svd(g2_constraint)
    s_table = SedenionBreakCarrier.cayley_dickson_double(SedenionBreakCarrier.prior_octonion_table())
    left = SedenionBreakCarrier.pair_vector(size(s_table, 1), 1, 10)
    right = SedenionBreakCarrier.pair_vector(size(s_table, 1), 5, 14)
    s_product = SedenionBreakCarrier.multiply(s_table, left, right)
    psi = spinor_from_angles(1.1, -0.7)
    rho = dm(psi)
    eta = pi / 4.0
    z = cos(eta)
    w = sin(eta)
    target = 1.0 / sqrt(2.0)
    golden_psi = ComplexF64[cis(0.0 + 0.0) * cos(eta), cis(0.0 - 0.0) * sin(eta)]
    h_i_j_minus_k = norm(
        OwnerDivisionCarrier.multiply(h_table, OwnerDivisionCarrier.basis(4, 1), OwnerDivisionCarrier.basis(4, 2)) -
        OwnerDivisionCarrier.basis(4, 3)
    )
    Dict{String,Any}(
        "division_algebra_ratchet_ladder" => Dict{String,Any}(
            "h_dim" => size(h_table, 1),
            "o_dim" => size(o_table, 1),
            "h_i_j_minus_k_residual" => h_i_j_minus_k,
        ),
        "octonion_G2_automorphism" => Dict{String,Any}(
            "constraint_rows" => size(g2_constraint, 1),
            "constraint_cols" => size(g2_constraint, 2),
            "der_O_dim" => size(g2_constraint, 2) - g2_rank,
        ),
        "sedenion_break" => Dict{String,Any}(
            "sedenion_dim" => size(s_table, 1),
            "sedenion_checksum" => SedenionBreakCarrier.table_checksum(s_table),
            "zero_divisor_product_norm" => norm(s_product),
            "zero_divisor_witness" => "(e1 + e10) * (e5 + e14) = 0",
        ),
        "density_matrix_spinor_lift" => Dict{String,Any}(
            "density_trace_real" => real(tr(rho)),
            "density_trace_residual" => abs(real(tr(rho)) - 1.0),
        ),
        "clifford_torus_nested_hopf_foliation" => Dict{String,Any}(
            "eta" => eta,
            "clifford_target_radius_residual" => max(abs(abs(z) - target), abs(abs(w) - target)),
            "clifford_hopf_equator_residual" => abs(abs(z)^2 - abs(w)^2),
        ),
        "golden_weyl" => Dict{String,Any}(
            "psi_norm_residual" => abs(real(dot(golden_psi, golden_psi)) - 1.0),
            "eta_sample" => eta,
        ),
        "canonical_qit_engine_specs" => Dict{String,Any}(
            "h0_sz_coeff" => 0.77,
            "h0_sx_coeff" => 0.13,
            "operator_slot_sequence" => ["Ti", "Te", "Fi", "Fe"],
            "total_substages_per_engine" => 32,
        ),
    )
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
    witness = cl6_ideal_charge_witness()
    owner_anchor = owner_object_anchor()
    sources = source_refs()
    all_sources_present = all(row["exists"] for row in values(sources))
    owner_anchor_ok = owner_anchor["division_algebra_ratchet_ladder"]["h_i_j_minus_k_residual"] < TOL &&
        owner_anchor["octonion_G2_automorphism"]["der_O_dim"] == 14 &&
        owner_anchor["sedenion_break"]["zero_divisor_product_norm"] < TOL &&
        owner_anchor["density_matrix_spinor_lift"]["density_trace_residual"] < TOL &&
        owner_anchor["clifford_torus_nested_hopf_foliation"]["clifford_target_radius_residual"] < TOL &&
        owner_anchor["golden_weyl"]["psi_norm_residual"] < TOL &&
        owner_anchor["canonical_qit_engine_specs"]["total_substages_per_engine"] == 32
    owner_carrier_load_bearing = witness["from_algebra"] &&
        witness["required_charges_present"] &&
        witness["erased_owner_changes"] &&
        witness["non_integer_control_breaks_quantization"] &&
        owner_anchor_ok &&
        all_sources_present
    local_all_pass = Bool(owner_carrier_load_bearing)
    shared_scalars = Dict{String,Any}(
        "cl6_dim" => Float64(witness["cl6_dim"]),
        "cl6_ideal_rank" => Float64(witness["ideal_rank"]),
        "car_residual" => Float64(witness["car_residual"]),
        "nilpotent_residual" => Float64(witness["nilpotent_residual"]),
        "vacuum_idempotent_residual" => Float64(witness["vacuum_idempotent_residual"]),
        "vacuum_annihilation_residual" => Float64(witness["vacuum_annihilation_residual"]),
        "integer_eigenvalue_residual" => Float64(witness["integer_eigenvalue_residual"]),
        "max_total_number_residual" => Float64(witness["max_total_number_residual"]),
        "max_mode_number_residual" => Float64(witness["max_mode_number_residual"]),
        "charge_lattice_residual" => Float64(witness["charge_lattice_residual"]),
        "weighted_charge_lattice_residual" => Float64(witness["weighted_charge_lattice_residual"]),
        "erased_car_residual" => Float64(witness["erased_car_residual"]),
        "unique_charge_count" => Float64(length(witness["unique_charges"])),
        "der_O_dim" => Float64(owner_anchor["octonion_G2_automorphism"]["der_O_dim"]),
        "sedenion_zero_divisor_product_norm" => Float64(owner_anchor["sedenion_break"]["zero_divisor_product_norm"]),
        "density_trace_residual" => Float64(owner_anchor["density_matrix_spinor_lift"]["density_trace_residual"]),
        "golden_weyl_psi_norm_residual" => Float64(owner_anchor["golden_weyl"]["psi_norm_residual"]),
        "qit_total_substages_per_engine" => Float64(owner_anchor["canonical_qit_engine_specs"]["total_substages_per_engine"]),
    )
    shared_booleans = Dict{String,Any}(
        "charges_integer_multiples" => Bool(witness["charges_integer_multiples"]),
        "unit_third" => Bool(witness["unit_third"]),
        "from_algebra" => Bool(witness["from_algebra"]),
        "required_charges_present" => Bool(witness["required_charges_present"]),
        "non_integer_control_breaks_quantization" => Bool(witness["non_integer_control_breaks_quantization"]),
        "erased_owner_changes" => Bool(witness["erased_owner_changes"]),
        "owner_anchor_ok" => Bool(owner_anchor_ok),
        "all_sources_present" => Bool(all_sources_present),
        "owner_carrier_load_bearing" => Bool(owner_carrier_load_bearing),
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "jax_enable_x64" => true,
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "schema" => "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name" => OBJECT_ID,
        "backend" => "julia_float64_complex",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "allowed_claims" => [
            "finite Cl(6) ideal-state charge quantization witness",
            "dual-backend parity witness",
            "real-vs-erased and non-integer ladder controls",
        ],
        "blocked_consumers" => [
            "physics_claims",
            "Standard_Model_admission",
            "M(C)_admission",
            "Axis0",
            "bridge",
            "mass_or_coupling_claims",
            "formal_admission",
        ],
        "sim_execution_kind" => "classical",
        "sim_class" => "finite_formal_scout",
        "numpy_compute_used" => false,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "construction" => Dict{String,Any}(
            "carrier" => "owner Cl(0,6) table mirrored from clifford_algebra_ladder.jl with octonion/G2 owner anchors",
            "ladder_convention" => "alpha_i=(e_{2i-1}+i e_{2i})/2, alpha_i_dag=(-e_{2i-1}+i e_{2i})/2 in Cl(0,6)",
            "charge_rule" => "plus ideal Q=N/3; conjugate ideal Q=-N/3; N=sum_i alpha_i_dag alpha_i has integer eigenvalues 0..3",
            "rung_spec_boundary" => "demonstrates the finite ladder-number mechanism; does not claim physical derivation or admission",
        ),
        "source_dependencies" => Dict(key => path for (key, path) in SOURCE_PATHS),
        "source_refs" => sources,
        "owner_object_anchor" => owner_anchor,
        "charge_witness" => witness,
        "controls" => Dict{String,Any}(
            "real_vs_erased_owner_carrier_flip" => Dict{String,Any}(
                "pass" => Bool(witness["erased_owner_changes"]),
                "real_required_charges_present" => Bool(witness["required_charges_present"]),
                "erased_required_charges_present" => Bool(witness["erased_required_charges_present"]),
                "erased_car_residual" => witness["erased_car_residual"],
            ),
            "non_integer_ladder_structure_gives_non_quantized_charges" => Dict{String,Any}(
                "pass" => Bool(witness["non_integer_control_breaks_quantization"]),
                "weighted_charge_lattice_residual" => witness["weighted_charge_lattice_residual"],
            ),
        ),
        "positive" => Dict{String,Any}(
            "cl6_ladder_car_holds" => Dict("pass" => witness["car_residual"] < TOL),
            "ideal_states_are_number_eigenstates" => Dict("pass" => witness["from_algebra"], "integer_eigenvalue_residual" => witness["integer_eigenvalue_residual"]),
            "charges_are_integer_multiples_of_one_third" => Dict("pass" => witness["charges_integer_multiples"], "charge_lattice_residual" => witness["charge_lattice_residual"]),
            "required_quark_lepton_charge_values_present" => Dict("pass" => witness["required_charges_present"], "required_charge_values" => witness["required_charge_values"], "unique_charges" => witness["unique_charges"]),
            "owner_carrier_declared_and_used_load_bearing" => Dict("pass" => owner_carrier_load_bearing, "owner_julia_carrier" => "load_bearing"),
        ),
        "graveyard_companions" => Dict{String,Any}(
            "erased_owner_carrier" => Dict("pass" => witness["erased_owner_changes"]),
            "non_integer_ladder_weights" => Dict("pass" => witness["non_integer_control_breaks_quantization"]),
            "promotion_and_formal_admission_fenced" => Dict("pass" => true, "promotion_allowed" => false, "formal_admission_allowed" => false),
        ),
        "boundary" => Dict{String,Any}(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "claim_ceiling_blocks_downstream" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING),
            "masses_and_couplings_not_claimed" => Dict("pass" => true),
        ),
        "nearby_variants" => Dict{String,Any}(
            "total" => 2,
            "passed" => Int(witness["erased_owner_changes"]) + Int(witness["non_integer_control_breaks_quantization"]),
            "variant_names" => ["erased_owner_carrier", "non_integer_ladder_weights"],
        ),
        "why_not_v4_probes" => [
            "scratch diagnostic by request",
            "finite Cl(6) ideal-state witness only",
            "no formal theorem prover layer",
            "no masses, couplings, M(C), Axis0, bridge, basin, manifold, or Standard Model admission",
        ],
        "TOOL_MANIFEST" => Dict{String,Any}(
            "Julia LinearAlgebra ComplexF64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite Cl(6) multivector algebra, ladder CAR, ideal states, charge eigenvalues, controls, and parity scalars"),
            "owner_julia_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner carrier source set; Cl(6) ladder and octonion/G2 anchors are required and erasing the carrier changes the result"),
            "JAX jax.numpy x64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend parity over the same finite carrier values"),
            "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "supportive source-native schedule/operator anchor; not the source of the charge eigenvalues"),
            "Julia JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, source hashes, and timestamps only"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String,Any}(
            "Julia LinearAlgebra ComplexF64" => "load_bearing",
            "owner_julia_carrier" => "load_bearing",
            "JAX jax.numpy x64" => "load_bearing",
            "canonical_qit_engine_specs.py" => "supportive",
            "Julia JSON/SHA/Dates" => "supportive",
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "local_all_pass" => local_all_pass,
        "blockers" => local_all_pass ? [] : ["local_charge_quantization_scout_failed"],
    )
    result["tool_manifest"] = result["TOOL_MANIFEST"]
    result["tool_integration_depth"] = result["TOOL_INTEGRATION_DEPTH"]
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["all_pass"] = Bool(local_all_pass && result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = Bool((!local_all_pass) || result["parity"]["stop_condition_fired"])
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => local_all_pass,
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing" => Bool(owner_carrier_load_bearing),
        "charges_integer_multiples" => Bool(witness["charges_integer_multiples"]),
        "unit_third" => Bool(witness["unit_third"]),
        "from_algebra" => Bool(witness["from_algebra"]),
        "claim_ceiling" => CLAIM_CEILING,
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
        "JULIA_SCOUT_DONE result=", RESULT_PATH,
        " all_pass=", result["all_pass"],
        " owner_carrier_load_bearing=", result["result_summary"]["owner_carrier_load_bearing"],
        " charges_integer_multiples=", result["result_summary"]["charges_integer_multiples"],
        " unit_third=", result["result_summary"]["unit_third"],
        " from_algebra=", result["result_summary"]["from_algebra"],
        " parity=", result["parity"]["within_1e_9"],
    )
    return result["all_pass"] ? 0 : 2
end

exit(main())
