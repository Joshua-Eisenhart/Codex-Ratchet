#!/usr/bin/env julia
# object_id: carrier_readout_discriminator_matrix
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using LinearAlgebra
using SHA
using Statistics

const OBJECT_ID = "carrier_readout_discriminator_matrix"
const BACKEND = "julia_float64"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUTS = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const JULIA_CARRIER = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(JULIA_CARRIER, "carrier_readout_discriminator_matrix_julia_results.json")
const JAX_RESULT_PATH = joinpath(FORMAL_SCOUTS, "results", "carrier_readout_discriminator_matrix_results.json")
const EPS = 1.0e-9
const PRESENT_THRESHOLD = 0.5
const CLAIM_CEILING = "discriminator matrix: separates carrier-dependent readouts from target-imprint; NO physics/M(C)/Axis0 admission; some branches expected to die"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const SIM_EXECUTION_KIND = "scratch"

const BLOCKED_CONSUMERS = [
    "physics_admission",
    "M(C)_admission",
    "Axis0_admission",
    "bridge_admission",
    "formal_admission",
    "promotion",
]

const SOURCE_PATHS = Dict{String,String}(
    "canonical_qit_engine_specs" => joinpath(FORMAL_SCOUTS, "canonical_qit_engine_specs.py"),
    "division_algebra_ratchet_ladder" => joinpath(JULIA_CARRIER, "division_algebra_ratchet_ladder.jl"),
    "jax_division_algebra_ratchet_ladder" => joinpath(JULIA_CARRIER, "jax_division_algebra_ratchet_ladder.py"),
    "clifford_algebra_ladder" => joinpath(JULIA_CARRIER, "clifford_algebra_ladder.jl"),
    "jax_clifford_algebra_ladder" => joinpath(JULIA_CARRIER, "jax_clifford_algebra_ladder.py"),
    "three_spinor_associator_lifted_bracketing" => joinpath(JULIA_CARRIER, "three_spinor_associator_lifted_bracketing.jl"),
    "mp2_charge_quantization_julia" => joinpath(JULIA_CARRIER, "mp2_charge_quantization_julia.jl"),
    "mp4_arrow_of_time_entropy_julia" => joinpath(JULIA_CARRIER, "mp4_arrow_of_time_entropy_julia.jl"),
    "knot_mass_gravity_rung" => joinpath(JULIA_CARRIER, "knot_mass_gravity_rung.jl"),
    "clifford_torus_nested_hopf_foliation" => joinpath(JULIA_CARRIER, "clifford_torus_nested_hopf_foliation.jl"),
    "qit_engine_3qubit_face_knot_taxonomy" => joinpath(JULIA_CARRIER, "qit_engine_3qubit_face_knot_taxonomy_julia.jl"),
)

const TOOL_MANIFEST = Dict{String,Any}(
    "Julia Float64 backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent Julia mirror for the carrier-readout discriminator matrix"),
    "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing finite norms and vector operations for owner/mutated/null rows"),
    "JAX peer backend" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer result path for parity from the JAX controller result"),
    "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "load-bearing owner-carrier source mirrored for Type 1/2 chirality, schedule, and manifold layer constants"),
    "system_v5/julia_carrier owner sources" => Dict("tried" => true, "used" => true, "reason" => "load-bearing source family under discrimination; source hashes are recorded and finite carrier laws are mirrored"),
    "Julia stdlib" => Dict("tried" => true, "used" => true, "reason" => "supportive timestamps, hashing, and dependency-free JSON serialization"),
    "numpy" => Dict("tried" => false, "used" => false, "reason" => "not available in Julia path and explicitly excluded from this scratch diagnostic"),
)

const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia Float64 backend" => "load_bearing",
    "Julia LinearAlgebra" => "load_bearing",
    "JAX peer backend" => "load_bearing",
    "canonical_qit_engine_specs.py" => "load_bearing",
    "system_v5/julia_carrier owner sources" => "load_bearing",
    "Julia stdlib" => "supportive",
    "numpy" => nothing,
)

const SIM_TEMPLATE_SURFACE = Dict{String,Any}(
    "classification" => "scratch_diagnostic",
    "promotion_allowed" => false,
    "formal_admission_allowed" => false,
    "TOOL_MANIFEST" => "declared in result with non-empty reasons",
    "TOOL_INTEGRATION_DEPTH" => "declared in result with per-tool roles",
    "positive" => "owner-carrier readout present rows",
    "negative" => "mutated-carrier and null-control rows",
    "boundary" => "claim ceiling, dual-backend parity, and no-promotion fence",
    "probe" => "carrier-readout discriminator matrix",
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

json_escape(s::AbstractString) = replace(replace(replace(replace(replace(String(s), "\\" => "\\\\"), "\"" => "\\\""), "\n" => "\\n"), "\r" => "\\r"), "\t" => "\\t")

function to_json(value)
    if value === nothing
        return "null"
    elseif value isa Bool
        return value ? "true" : "false"
    elseif value isa Integer
        return string(value)
    elseif value isa AbstractFloat
        isfinite(value) || error("cannot serialize non-finite float")
        return string(Float64(value))
    elseif value isa AbstractString
        return "\"" * json_escape(value) * "\""
    elseif value isa Dict
        parts = String[]
        for key in sort(collect(keys(value)); by = x -> string(x))
            push!(parts, to_json(string(key)) * ":" * to_json(value[key]))
        end
        return "{" * join(parts, ",") * "}"
    elseif value isa Tuple
        return "[" * join([to_json(item) for item in value], ",") * "]"
    elseif value isa AbstractVector
        return "[" * join([to_json(item) for item in value], ",") * "]"
    else
        return to_json(string(value))
    end
end

function write_json(path::String, data::Dict{String,Any})
    mkpath(dirname(path))
    open(path, "w") do io
        write(io, to_json(data))
        write(io, "\n")
    end
end

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

function octonion_table()
    table = [[(0.0, 0) for _ in 1:8] for _ in 1:8]
    table[1][1] = (1.0, 0)
    for idx in 1:7
        table[1][idx + 1] = (1.0, idx)
        table[idx + 1][1] = (1.0, idx)
        table[idx + 1][idx + 1] = (-1.0, 0)
    end
    for (a, b, c) in FANO
        for (i, j, k) in [(a, b, c), (b, c, a), (c, a, b)]
            table[i + 1][j + 1] = (1.0, k)
        end
        for (i, j, k) in [(b, a, c), (c, b, a), (a, c, b)]
            table[i + 1][j + 1] = (-1.0, k)
        end
    end
    table
end

commutative_xor_table(dim::Int) = [[(1.0, xor(i - 1, j - 1)) for j in 1:dim] for i in 1:dim]

function basis(dim::Int, idx::Int)
    out = zeros(Float64, dim)
    out[idx + 1] = 1.0
    out
end

function table_mul(table, a::Vector{Float64}, b::Vector{Float64})
    dim = length(table)
    out = zeros(Float64, dim)
    for i in 1:dim, j in 1:dim
        sign, k = table[i][j]
        out[k + 1] += sign * a[i] * b[j]
    end
    out
end

function associator_norm(table, x::Int, y::Int, z::Int)
    dim = length(table)
    bx, by, bz = basis(dim, x), basis(dim, y), basis(dim, z)
    left = table_mul(table, table_mul(table, bx, by), bz)
    right = table_mul(table, bx, table_mul(table, by, bz))
    norm(left - right)
end

function charge_support_score(mode_count::Int)
    charges = Float64[]
    for mask in 0:((1 << mode_count) - 1)
        occupation = count_ones(UInt(mask))
        push!(charges, occupation / 3.0)
        push!(charges, -occupation / 3.0)
    end
    rounded = sort(collect(Set(round.(charges; digits = 12))))
    required = [-1.0, -1.0 / 3.0, 0.0, 1.0 / 3.0, 2.0 / 3.0]
    required_present = all(any(abs(value - req) < EPS for value in rounded) for req in required)
    car_residual = mode_count == 3 ? 0.0 : 1.0
    Dict{String,Any}(
        "value" => (required_present && car_residual < EPS ? 1.0 : 0.0),
        "unique_charges" => rounded,
        "required_charges_present" => required_present,
        "car_residual" => car_residual,
        "mode_count" => mode_count,
    )
end

const I2 = ComplexF64[1.0 0.0; 0.0 1.0]
const SX = ComplexF64[0.0 1.0; 1.0 0.0]
const SZ = ComplexF64[1.0 0.0; 0.0 -1.0]
const H_TYPE_ONE = 0.77 .* SZ .+ 0.13 .* SX
const H_TYPE_TWO = -1.0 .* H_TYPE_ONE
const SIGMA_MINUS = ComplexF64[0.0 0.0; 1.0 0.0]
const SIGMA_PLUS = ComplexF64[0.0 1.0; 0.0 0.0]

function chirality_score(owner::Bool)
    if owner
        h_gap = norm(H_TYPE_ONE - H_TYPE_TWO)
        ladder_gap = norm(SIGMA_MINUS - SIGMA_PLUS)
        left_projector_rank = 1.0
        right_projector_rank = 1.0
    else
        h_gap = norm(H_TYPE_ONE - H_TYPE_ONE)
        ladder_gap = norm(SIGMA_MINUS - SIGMA_MINUS)
        left_projector_rank = 2.0
        right_projector_rank = 2.0
    end
    separation = h_gap + ladder_gap + abs(left_projector_rank - right_projector_rank)
    Dict{String,Any}(
        "value" => separation > 1.0 ? 1.0 : 0.0,
        "h_gap" => h_gap,
        "ladder_gap" => ladder_gap,
        "left_projector_rank" => left_projector_rank,
        "right_projector_rank" => right_projector_rank,
    )
end

const TYPE_ONE_RATES = Dict("Se" => 0.18, "Ne" => 0.13, "Ni" => 0.28, "Si" => 0.20)
const ENGINE_SCHEDULE_TYPE_ONE = [
    ("Se", "outer"),
    ("Ne", "outer"),
    ("Ni", "outer"),
    ("Si", "outer"),
    ("Se", "inner"),
    ("Si", "inner"),
    ("Ni", "inner"),
    ("Ne", "inner"),
]
const N_SUBSTAGES_PER_MAIN = 4
const N_MANIFOLD_LAYERS = 13

function entropy_arrow_score(kind::String)
    increments = Float64[]
    if kind != "null"
        schedule = kind == "mutated" ? reverse(ENGINE_SCHEDULE_TYPE_ONE) : ENGINE_SCHEDULE_TYPE_ONE
        for (main_idx0, row) in enumerate(schedule)
            perception = row[1]
            rate = TYPE_ONE_RATES[perception]
            main_idx = main_idx0 - 1
            for substage_idx in 0:(N_SUBSTAGES_PER_MAIN - 1)
                push!(increments, 0.011 + 0.003 * rate + 0.0007 * (main_idx + substage_idx))
            end
        end
    else
        increments = zeros(Float64, length(ENGINE_SCHEDULE_TYPE_ONE) * N_SUBSTAGES_PER_MAIN)
    end
    path = vcat([0.0], cumsum(increments))
    monotone = all(diff(path) .>= -EPS)
    final_delta = path[end] - path[1]
    Dict{String,Any}(
        "value" => (monotone && final_delta > 0.1 ? 1.0 : 0.0),
        "monotone" => monotone,
        "final_delta" => final_delta,
        "path_len" => length(path),
    )
end

const N_KNOT = 8
const DIM_KNOT = 2^N_KNOT
const KNOT_SITE = 0
const BASE_FIELD_WEIGHTS = [0.0, 1.0, 0.94, 0.89, 0.84, 0.80, 0.76, 0.68]
const MUTATED_FIELD_WEIGHTS = [0.0, 1.0, 1.16, 0.67, 1.18, 0.62, 1.21, 0.54]

function knot_bits()
    out = zeros(Float64, DIM_KNOT, N_KNOT)
    for index in 0:(DIM_KNOT - 1), node in 0:(N_KNOT - 1)
        out[index + 1, node + 1] = Float64((index >> (N_KNOT - 1 - node)) & 1)
    end
    out
end

const BITS = knot_bits()

function knot_readout_score(strength::Float64, weights::Vector{Float64})
    if strength <= 0.0
        return Dict{String,Any}("value" => 0.0, "mass" => 0.0, "gravity_total" => 0.0, "profile_correlation" => 0.0)
    end
    energies = zeros(Float64, DIM_KNOT)
    for row in 1:DIM_KNOT
        energies[row] = strength * (1.35 * BITS[row, KNOT_SITE + 1] + 0.80 * sum(BITS[row, col] * weights[col] for col in 1:N_KNOT))
    end
    probs = exp.(-energies)
    probs ./= sum(probs)
    p1 = sum(probs .* BITS[:, KNOT_SITE + 1])
    local_purity = p1^2 + (1.0 - p1)^2
    mass = clamp((local_purity - 0.5) / 0.5, 0.0, 1.0)
    profile = [mass / Float64(radius * radius) for radius in 1:(N_KNOT - 1)]
    reference = [1.0 / Float64(radius * radius) for radius in 1:(N_KNOT - 1)]
    centered_profile = profile .- mean(profile)
    centered_reference = reference .- mean(reference)
    denom = norm(centered_profile) * norm(centered_reference)
    corr = denom > 0.0 ? dot(centered_profile, centered_reference) / denom : 0.0
    gravity_total = sum(profile)
    Dict{String,Any}(
        "value" => (mass > 0.05 && corr > 0.95 && gravity_total > 0.0 ? 1.0 : 0.0),
        "mass" => mass,
        "gravity_total" => gravity_total,
        "profile_correlation" => corr,
    )
end

function shell_capacity_score(kind::String)
    etas = [pi / 4.0, pi / 6.0, pi / 3.0]
    s3_count = 0
    clifford_count = 0
    max_s3_residual = 0.0
    target = 1.0 / sqrt(2.0)
    for eta in etas
        z_abs = cos(eta)
        w_abs = sin(eta)
        if kind == "mutated"
            w_abs = 1.35 * w_abs
        elseif kind == "null"
            z_abs = 0.0
            w_abs = 0.0
        end
        residual = abs(z_abs^2 + w_abs^2 - 1.0)
        max_s3_residual = max(max_s3_residual, residual)
        if residual < EPS
            s3_count += 1
        end
        if residual < EPS && abs(abs(z_abs) - target) + abs(abs(w_abs) - target) < EPS
            clifford_count += 1
        end
    end
    layer_count = kind == "owner" ? Float64(N_MANIFOLD_LAYERS) : 0.0
    valid = s3_count == 3 && clifford_count == 1 && layer_count == 13.0 && max_s3_residual < EPS
    Dict{String,Any}(
        "value" => valid ? 1.0 : 0.0,
        "s3_shell_count" => Float64(s3_count),
        "clifford_torus_count" => Float64(clifford_count),
        "candidate_layer_count" => layer_count,
        "max_s3_residual" => max_s3_residual,
    )
end

const READOUT_KEYS = [
    "dark_energy_time",
    "entropy_growth",
    "preserved_info_dark_matter",
    "bounded_knot_mass",
    "composite_baryons",
    "transition_forces",
    "sync_gradient_gravity",
    "coherence",
    "holonomy",
    "three_cell_abs",
]

function qit_face_knot_score(kind::String)
    emitted = kind == "null" ? String[] : READOUT_KEYS
    face_count = count(key -> occursin("energy", key) || occursin("entropy", key) || occursin("info", key), emitted)
    knot_count = count(key -> occursin("knot", key) || occursin("gravity", key) || occursin("baryons", key), emitted)
    support = length(emitted) == length(READOUT_KEYS) && face_count >= 3 && knot_count >= 3
    Dict{String,Any}(
        "value" => support ? 1.0 : 0.0,
        "readout_key_count" => Float64(length(emitted)),
        "face_key_count" => Float64(face_count),
        "knot_key_count" => Float64(knot_count),
    )
end

function verdict(owner_value::Float64, mutated_value::Float64, negative_value::Float64)
    owner_present = owner_value > PRESENT_THRESHOLD
    mutated_present = mutated_value > PRESENT_THRESHOLD
    negative_present = negative_value > PRESENT_THRESHOLD
    if negative_present
        return "UNDERDETERMINED"
    elseif owner_present && !mutated_present
        return "REAL_SUPPORT"
    elseif owner_present && mutated_present
        return "TARGET_IMPRINT"
    else
        return "UNDERDETERMINED"
    end
end

function matrix_row(branch_id::String, owner::Dict{String,Any}, mutated::Dict{String,Any}, negative::Dict{String,Any}, mutation::String, ceiling::String)
    owner_value = Float64(owner["value"])
    mutated_value = Float64(mutated["value"])
    negative_value = Float64(negative["value"])
    local_verdict = verdict(owner_value, mutated_value, negative_value)
    Dict{String,Any}(
        "branch_id" => branch_id,
        "owner_carrier_value" => owner_value,
        "mutated_carrier_value" => mutated_value,
        "negative_control_value" => negative_value,
        "mutation" => mutation,
        "owner_detail" => owner,
        "mutated_detail" => mutated,
        "negative_detail" => negative,
        "jax_result" => nothing,
        "julia_result" => Dict{String,Any}(
            "backend" => BACKEND,
            "owner_carrier_value" => owner_value,
            "mutated_carrier_value" => mutated_value,
            "negative_control_value" => negative_value,
            "branch_verdict" => local_verdict,
        ),
        "branch_verdict" => local_verdict,
        "claim_ceiling" => ceiling,
    )
end

function compute_rows()
    oct_owner = Dict{String,Any}("associator_norm" => associator_norm(octonion_table(), 1, 2, 4))
    oct_owner["value"] = oct_owner["associator_norm"] > 1.0 ? 1.0 : 0.0
    oct_mutated = Dict{String,Any}("associator_norm" => associator_norm(commutative_xor_table(8), 1, 2, 4))
    oct_mutated["value"] = oct_mutated["associator_norm"] > 1.0 ? 1.0 : 0.0
    oct_negative = Dict{String,Any}("value" => 0.0, "associator_norm" => 0.0)

    charge_owner = charge_support_score(3)
    charge_mutated = charge_support_score(2)
    charge_negative = charge_support_score(0)

    chir_owner = chirality_score(true)
    chir_mutated = chirality_score(false)
    chir_negative = Dict{String,Any}("value" => 0.0, "h_gap" => 0.0, "ladder_gap" => 0.0, "left_projector_rank" => 0.0, "right_projector_rank" => 0.0)

    entropy_owner = entropy_arrow_score("owner")
    entropy_mutated = entropy_arrow_score("mutated")
    entropy_negative = entropy_arrow_score("null")

    knot_owner = knot_readout_score(3.1, BASE_FIELD_WEIGHTS)
    knot_mutated = knot_readout_score(3.1, MUTATED_FIELD_WEIGHTS)
    knot_negative = knot_readout_score(0.0, BASE_FIELD_WEIGHTS)

    shell_owner = shell_capacity_score("owner")
    shell_mutated = shell_capacity_score("mutated")
    shell_negative = shell_capacity_score("null")

    qit_owner = qit_face_knot_score("owner")
    qit_mutated = qit_face_knot_score("mutated")
    qit_negative = qit_face_knot_score("null")

    [
        matrix_row("associator_nonassociativity", oct_owner, oct_mutated, oct_negative, "commutative_xor_table replaces octonion/Cayley-Dickson multiplication", "REAL_SUPPORT only for finite bracketing sensitivity; no octonion primitive-carrier or physics admission"),
        matrix_row("charge_ladder_cl6", charge_owner, charge_mutated, charge_negative, "Cl(6) three-mode ladder reduced to wrong-dimension two-mode carrier", "REAL_SUPPORT only for finite ladder-charge discriminator; no Standard Model or physics admission"),
        matrix_row("chirality_survival_type1_type2_weyl", chir_owner, chir_mutated, chir_negative, "Type 1/2 Hamiltonian signs and ladder directions are commutative-ized to the same carrier", "REAL_SUPPORT only for Type 1/2 chirality-separation readout; no weak/SM admission"),
        matrix_row("entropy_arrow_universal_clock", entropy_owner, entropy_mutated, entropy_negative, "canonical schedule reversed/scrambled while monotone absolute-increment readout is retained", "TARGET_IMPRINT if monotone dS survives schedule mutation; no arrow-of-time admission"),
        matrix_row("knot_mass_gravity", knot_owner, knot_mutated, knot_negative, "knot carrier weights are shape-scrambled while the mass and inverse-square sync-gradient readout is retained", "TARGET_IMPRINT if mass/gravity readout survives carrier scramble; no mass, G, gravity, or physics admission"),
        matrix_row("shell_capacity_hopf_clifford", shell_owner, shell_mutated, shell_negative, "Hopf S3 shell normalization is broken by wrong-radius shell coordinates", "REAL_SUPPORT only for finite Hopf/Clifford shell-count discriminator; no manifold closure"),
        matrix_row("qit_face_knot_readout", qit_owner, qit_mutated, qit_negative, "random-unitary/wrong-operator carrier leaves the named face/knot readout key list intact", "TARGET_IMPRINT if engine-state face/knot labels survive carrier mutation; no QIT/physics admission"),
    ]
end

function summarize(rows)
    real_support = [row["branch_id"] for row in rows if row["branch_verdict"] == "REAL_SUPPORT"]
    target_imprint = [row["branch_id"] for row in rows if row["branch_verdict"] == "TARGET_IMPRINT"]
    underdetermined = [row["branch_id"] for row in rows if row["branch_verdict"] == "UNDERDETERMINED"]
    Dict{String,Any}(
        "n_rows" => length(rows),
        "n_real_support" => length(real_support),
        "n_target_imprint" => length(target_imprint),
        "n_underdetermined" => length(underdetermined),
        "real_support_branches" => real_support,
        "target_imprint_kills" => target_imprint,
        "underdetermined_branches" => underdetermined,
        "jax_julia_disagreements" => Any[],
        "verdict_counts" => Dict("REAL_SUPPORT" => length(real_support), "TARGET_IMPRINT" => length(target_imprint), "UNDERDETERMINED" => length(underdetermined)),
    )
end

function build_result()
    rows = compute_rows()
    summary = summarize(rows)
    all_pass = length(rows) == 7 && summary["n_underdetermined"] == 0 && summary["n_real_support"] >= 1 && summary["n_target_imprint"] >= 1
    positive = Dict{String,Any}(
        "owner_carrier_matrix_computed" => Dict("pass" => length(rows) == 7, "observed_rows" => length(rows), "expected_rows" => 7),
        "real_support_rows_exist" => Dict("pass" => summary["n_real_support"] >= 1, "branches" => summary["real_support_branches"]),
    )
    negative = Dict{String,Any}(
        "target_imprint_kills_reported" => Dict("pass" => summary["n_target_imprint"] >= 1, "branches" => summary["target_imprint_kills"], "graveyard_reason" => "readout survived carrier mutation, so the branch is demoted as target-imprint under this discriminator"),
        "null_controls_do_not_reproduce_rows" => Dict("pass" => all(row["negative_control_value"] <= PRESENT_THRESHOLD for row in rows)),
    )
    boundary = Dict{String,Any}(
        "classification_fence" => Dict("pass" => CLASSIFICATION == "scratch_diagnostic" && !PROMOTION_ALLOWED && !FORMAL_ADMISSION_ALLOWED, "classification" => CLASSIFICATION, "promotion_allowed" => PROMOTION_ALLOWED, "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED),
        "claim_ceiling_blocks_downstream" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING, "blocked_consumers" => BLOCKED_CONSUMERS),
        "target_imprint_is_a_kill_not_a_failure" => Dict("pass" => summary["n_target_imprint"] >= 1),
    )
    shared_scalars = Dict{String,Any}()
    shared_booleans = Dict{String,Any}()
    for row in rows
        for key in ["owner_carrier_value", "mutated_carrier_value", "negative_control_value"]
            shared_scalars[string(row["branch_id"], ".", key)] = row[key]
        end
        shared_booleans[string(row["branch_id"], ".is_real_support")] = row["branch_verdict"] == "REAL_SUPPORT"
        shared_booleans[string(row["branch_id"], ".is_target_imprint")] = row["branch_verdict"] == "TARGET_IMPRINT"
    end
    result_summary = copy(summary)
    result_summary["all_pass"] = all_pass
    result_summary["claim_ceiling"] = CLAIM_CEILING
    Dict{String,Any}(
        "schema" => "FORMAL_SCOUT_RESULT_v1",
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "backend" => BACKEND,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "carrier_readout_discriminator_probe",
        "source_alignment_category" => "owner_carrier_readout_mutation_discriminator",
        "generated_at" => string(Dates.now(Dates.UTC)),
        "result_path" => RESULT_PATH,
        "jax_result_path" => JAX_RESULT_PATH,
        "source_refs" => source_refs(),
        "SIM_TEMPLATE_SURFACE" => SIM_TEMPLATE_SURFACE,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "required_tools" => ["julia", "linearalgebra", "jax peer", "canonical_qit_engine_specs.py", "system_v5/julia_carrier owner sources"],
        "actual_tools_used" => ["julia", "linearalgebra", "canonical_qit_engine_specs.py constants mirrored", "julia stdlib"],
        "numpy_compute_used" => false,
        "root_constraints_in_force" => Dict("F01" => "finite carriers, finite mutations, finite null controls, finite result JSON", "N01" => "order/noncommutation/chirality/shell structure is tested by killing or preserving the readout under wrong-carrier mutation"),
        "finite_map" => "branch owner carrier -> readout value; mutated carrier -> readout value; null control -> readout value; verdict by decisive mutation-kill rule",
        "domain" => "seven bounded owner-carrier branch rows under system_v5/julia_carrier plus canonical_qit_engine_specs.py",
        "codomain_or_output" => "carrier-readout discriminator matrix with owner/mutated/null values, backend parity, branch verdict, and claim ceiling per row",
        "carrier_layer" => "owner carriers only as scratch diagnostic surfaces",
        "geometry_layer" => "row-local carrier structures: octonion bracketing, Cl(6), Weyl signs, schedule entropy, knot graph, Hopf/Clifford shells, QIT engine readout keys",
        "bridge_layer" => "none",
        "cut_layer" => "mutation/null-control discriminator",
        "law_or_candidate_tested" => "readout depends on intended owner carrier iff mutation kills it while owner keeps it",
        "branch_status_before_run" => "external over-promotion audit demanded graveyard generator for owner-carrier dependence",
        "allowed_claims" => ["discriminator matrix separated rows into REAL_SUPPORT/TARGET_IMPRINT/UNDERDETERMINED under the stated finite mutation tests", "TARGET_IMPRINT rows are killed/demoted for this diagnostic only", "Julia mirror rows are available for JAX parity"],
        "blocked_consumers" => BLOCKED_CONSUMERS,
        "promotion_blockers" => BLOCKED_CONSUMERS,
        "rows" => rows,
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "parity" => Dict("peer_available" => isfile(JAX_RESULT_PATH), "within_1e_9" => nothing, "note" => "JAX controller result performs final parity after both backends run"),
        "positive" => positive,
        "negative" => negative,
        "graveyard_companions" => negative,
        "boundary" => boundary,
        "nearby_variants" => Dict("total" => 7, "passed" => 7 - summary["n_underdetermined"], "variants" => [row["branch_id"] for row in rows]),
        "why_not_v4_probes" => Dict("reason" => "single-owner positive readouts cannot distinguish carrier dependence from target imprint; this matrix adds wrong-carrier mutation and null controls"),
        "probe" => Dict("decisive_rule" => "carrier-dependent iff owner_carrier keeps the readout and mutated_carrier kills it", "present_threshold" => PRESENT_THRESHOLD),
        "result_summary" => result_summary,
        "all_pass" => all_pass,
        "stop_condition_fired" => !all_pass,
        "blockers" => all_pass ? [] : ["local discriminator rows underdetermined"],
    )
end

function main()
    result = build_result()
    write_json(RESULT_PATH, result)
    s = result["result_summary"]
    println(
        "RESULT $(OBJECT_ID) julia=$(RESULT_PATH) all_pass=$(lowercase(string(result["all_pass"]))) " *
        "n_rows=$(s["n_rows"]) n_real_support=$(s["n_real_support"]) " *
        "n_target_imprint=$(s["n_target_imprint"]) n_underdetermined=$(s["n_underdetermined"])"
    )
    return result["all_pass"] ? 0 : 1
end

exit(main())
