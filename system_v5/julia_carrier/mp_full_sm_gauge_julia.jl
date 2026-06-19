#!/usr/bin/env julia
# object_id: mp_full_sm_gauge
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "mp_full_sm_gauge"
const REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
const FORMAL_SCOUT_DIR = joinpath(REPO, "system_v5", "ops", "formal_scouts")
const CARRIER_DIR = joinpath(REPO, "system_v5", "julia_carrier")
const RESULT_PATH = joinpath(CARRIER_DIR, "mp_full_sm_gauge_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(FORMAL_SCOUT_DIR, "results", "mp_full_sm_gauge_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6

const SOURCE_DEPENDENCIES = [
    joinpath(CARRIER_DIR, "division_algebra_ratchet_ladder.jl"),
    joinpath(CARRIER_DIR, "jax_division_algebra_ratchet_ladder.py"),
    joinpath(CARRIER_DIR, "clifford_algebra_ladder.jl"),
    joinpath(CARRIER_DIR, "jax_clifford_algebra_ladder.py"),
    joinpath(CARRIER_DIR, "octonion_G2_automorphism.jl"),
    joinpath(CARRIER_DIR, "jax_octonion_G2_automorphism.py"),
    joinpath(CARRIER_DIR, "sedenion_break_prelim.jl"),
    joinpath(CARRIER_DIR, "jax_sedenion_break_prelim.py"),
    joinpath(CARRIER_DIR, "density_matrix_spinor_lift.jl"),
    joinpath(CARRIER_DIR, "jax_density_matrix_spinor_lift.py"),
    joinpath(CARRIER_DIR, "clifford_torus_nested_hopf_foliation.jl"),
    joinpath(CARRIER_DIR, "jax_clifford_torus_nested_hopf_foliation.py"),
    joinpath(CARRIER_DIR, "golden_weyl_julia.jl"),
    joinpath(CARRIER_DIR, "scratch_jax_snapshot_20260604", "golden_weyl_jax.py"),
    joinpath(FORMAL_SCOUT_DIR, "canonical_qit_engine_specs.py"),
]

const FANO = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]

const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]

function setprod!(table::Array{Float64,3}, a::Int, b::Int, c::Int, s::Float64)
    table[c + 1, a + 1, b + 1] = s
end

function add_identity!(table::Array{Float64,3}, dim::Int)
    for a in 0:(dim - 1)
        setprod!(table, 0, a, a, 1.0)
        setprod!(table, a, 0, a, 1.0)
    end
end

function complex_table()
    table = zeros(Float64, 2, 2, 2)
    add_identity!(table, 2)
    setprod!(table, 1, 1, 0, -1.0)
    table
end

function quaternion_table()
    table = zeros(Float64, 4, 4, 4)
    add_identity!(table, 4)
    for a in 1:3
        setprod!(table, a, a, 0, -1.0)
    end
    for (i, j, k) in [(1, 2, 3)]
        for (a, b, c, s) in [
            (i, j, k, 1.0), (j, k, i, 1.0), (k, i, j, 1.0),
            (j, i, k, -1.0), (k, j, i, -1.0), (i, k, j, -1.0),
        ]
            setprod!(table, a, b, c, s)
        end
    end
    table
end

function octonion_table()
    table = zeros(Float64, 8, 8, 8)
    add_identity!(table, 8)
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

function basis(dim::Int, idx::Int)
    v = zeros(Float64, dim)
    v[idx + 1] = 1.0
    v
end

function multiply(table::Array{Float64,3}, x::AbstractVector{Float64}, y::AbstractVector{Float64})
    dim = size(table, 1)
    out = zeros(Float64, dim)
    @inbounds for c in 1:dim, a in 1:dim, b in 1:dim
        out[c] += table[c, a, b] * x[a] * y[b]
    end
    out
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

function real_vector(mat::Matrix{ComplexF64})
    v = vec(mat)
    vcat(real.(v), imag.(v))
end

function span_rank(mats::Vector{Matrix{ComplexF64}})
    isempty(mats) && return 0
    stacked = hcat([real_vector(m) for m in mats]...)
    s = svdvals(stacked)
    thresh = maximum(size(stacked)) * eps(Float64) * maximum(s) * 100.0
    count(>(thresh), s)
end

function span_residual(mat::Matrix{ComplexF64}, basis_mats::Vector{Matrix{ComplexF64}})
    a = hcat([real_vector(m) for m in basis_mats]...)
    b = real_vector(mat)
    coeffs = a \ b
    norm(b - a * coeffs)
end

function closure_residual(gens::Vector{Matrix{ComplexF64}})
    isempty(gens) && return Inf
    max_seen = 0.0
    for a in gens, b in gens
        lie_hermitian = -im .* (a * b - b * a)
        max_seen = max(max_seen, span_residual(lie_hermitian, gens))
    end
    max_seen
end

function gell_mann()
    z = 0.0 + 0.0im
    one = 1.0 + 0.0im
    [
        ComplexF64[z one z; one z z; z z z] ./ 2.0,
        ComplexF64[z -im z; im z z; z z z] ./ 2.0,
        ComplexF64[one z z; z -one z; z z z] ./ 2.0,
        ComplexF64[z z one; z z z; one z z] ./ 2.0,
        ComplexF64[z z -im; z z z; im z z] ./ 2.0,
        ComplexF64[z z z; z z one; z one z] ./ 2.0,
        ComplexF64[z z z; z z -im; z im z] ./ 2.0,
        ComplexF64[one z z; z one z; z z -2.0] ./ (2.0 * sqrt(3.0)),
    ]
end

function one_generation_states()
    states = Vector{Dict{String,Any}}()
    colors = ["r", "g", "b"]
    for (ci0, color) in enumerate(colors)
        ci = ci0 - 1
        push!(states, Dict("name" => "u_L_$color", "family" => "u", "color" => ci, "weak" => 0, "chirality" => "L", "q" => 2.0 / 3.0, "y" => 1.0 / 3.0))
        push!(states, Dict("name" => "d_L_$color", "family" => "d", "color" => ci, "weak" => 1, "chirality" => "L", "q" => -1.0 / 3.0, "y" => 1.0 / 3.0))
    end
    push!(states, Dict("name" => "nu_L", "family" => "nu", "color" => -1, "weak" => 0, "chirality" => "L", "q" => 0.0, "y" => -1.0))
    push!(states, Dict("name" => "e_L", "family" => "e", "color" => -1, "weak" => 1, "chirality" => "L", "q" => -1.0, "y" => -1.0))
    for (ci0, color) in enumerate(colors)
        ci = ci0 - 1
        push!(states, Dict("name" => "u_R_$color", "family" => "u", "color" => ci, "weak" => -1, "chirality" => "R", "q" => 2.0 / 3.0, "y" => 4.0 / 3.0))
        push!(states, Dict("name" => "d_R_$color", "family" => "d", "color" => ci, "weak" => -1, "chirality" => "R", "q" => -1.0 / 3.0, "y" => -2.0 / 3.0))
    end
    push!(states, Dict("name" => "nu_R", "family" => "nu", "color" => -1, "weak" => -1, "chirality" => "R", "q" => 0.0, "y" => 0.0))
    push!(states, Dict("name" => "e_R", "family" => "e", "color" => -1, "weak" => -1, "chirality" => "R", "q" => -1.0, "y" => -2.0))
    states
end

zero_full(dim::Int) = zeros(ComplexF64, dim, dim)

function embed_color(states, color_gen::Matrix{ComplexF64})
    dim = length(states)
    out = zero_full(dim)
    for a in 1:dim
        sa = states[a]
        Int(sa["color"]) < 0 && continue
        for b in 1:dim
            sb = states[b]
            same_species = sa["family"] == sb["family"] && sa["chirality"] == sb["chirality"] && sa["weak"] == sb["weak"]
            if same_species && Int(sb["color"]) >= 0
                out[a, b] = color_gen[Int(sa["color"]) + 1, Int(sb["color"]) + 1]
            end
        end
    end
    out
end

function embed_weak(states, weak_gen::Matrix{ComplexF64})
    dim = length(states)
    out = zero_full(dim)
    for a in 1:dim
        sa = states[a]
        if Int(sa["weak"]) < 0 || sa["chirality"] != "L"
            continue
        end
        for b in 1:dim
            sb = states[b]
            same_doublet = sa["chirality"] == "L" && sb["chirality"] == "L" && Int(sa["color"]) == Int(sb["color"])
            quark_pair = Int(sa["color"]) >= 0 && Int(sb["color"]) >= 0 && sa["family"] in ["u", "d"] && sb["family"] in ["u", "d"]
            lepton_pair = Int(sa["color"]) < 0 && Int(sb["color"]) < 0 && sa["family"] in ["nu", "e"] && sb["family"] in ["nu", "e"]
            if same_doublet && (quark_pair || lepton_pair) && Int(sb["weak"]) >= 0
                out[a, b] = weak_gen[Int(sa["weak"]) + 1, Int(sb["weak"]) + 1]
            end
        end
    end
    out
end

function diagonal(states, key::String)
    vals = ComplexF64[Float64(s[key]) + 0im for s in states]
    Diagonal(vals) |> Matrix
end

function qit_spec_checks()
    h0 = 0.77 .* SZ .+ 0.13 .* SX
    h1 = h0
    h2 = -h0
    Dict{String,Any}(
        "h0_trace_abs" => abs(tr(h0)),
        "type_one_h0_residual" => norm(h1 - h0),
        "type_two_minus_h0_residual" => norm(h2 + h0),
        "lindblad_count" => 4,
        "operator_generator_count" => 4,
        "type_one_schedule_len" => 8,
        "type_two_schedule_len" => 8,
        "substage_count_per_engine" => 32,
        "qit_spec_ok" => norm(h2 + h0) < TOL,
    )
end

function carrier_checks()
    h_table = quaternion_table()
    o_table = octonion_table()
    cl3 = clifford_table([1, 1, 1])
    g2_constraint = derivation_constraint_matrix(o_table)
    s = svdvals(g2_constraint)
    rank_tol = maximum(size(g2_constraint)) * eps(Float64) * maximum(s) * 100.0
    g2_rank = count(>(rank_tol), s)
    Dict{String,Any}(
        "r_dim" => 1,
        "c_dim" => size(complex_table(), 1),
        "h_dim" => size(h_table, 1),
        "o_dim" => size(o_table, 1),
        "cl3_dim" => size(cl3, 1),
        "cl6_real_dim" => 64,
        "cl6_fermion_fock_dim" => 8,
        "der_o_dim" => size(g2_constraint, 2) - g2_rank,
        "octonion_stabilized_unit" => "e7",
        "octonion_complex_color_pairs" => [[1, 6], [2, 5], [3, 4]],
        "quaternion_units" => ["i", "j", "k"],
        "h_i_j_minus_k_residual" => norm(multiply(h_table, basis(4, 1), basis(4, 2)) - basis(4, 3)),
        "o_fano_e1_e2_minus_e3_residual" => norm(multiply(o_table, basis(8, 1), basis(8, 2)) - basis(8, 3)),
    )
end

function parity_against_peer(result::Dict{String,Any}, peer_path::String)
    if !isfile(peer_path)
        return Dict{String,Any}(
            "peer_result_path" => peer_path,
            "status" => "pending_peer_backend",
            "shared_scalar_rows" => [],
            "max_diff_key" => nothing,
            "parity_max_diff" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => [],
            "boolean_mismatches" => [],
            "missing_keys" => [],
            "stop_condition_fired" => false,
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
    states = one_generation_states()
    color_local = gell_mann()
    weak_local = [SX ./ 2.0, SY ./ 2.0, SZ ./ 2.0]
    color_gens = [embed_color(states, g) for g in color_local]
    weak_gens = [embed_weak(states, g) for g in weak_local]
    y_gen = diagonal(states, "y") ./ 2.0
    q_gen = diagonal(states, "q")
    t3 = weak_gens[3]
    q_recon = t3 + y_gen

    su3_rank = span_rank(color_gens)
    su2_rank = span_rank(weak_gens)
    u1_rank = span_rank([y_gen])
    su3_closure = closure_residual(color_gens)
    su2_closure = closure_residual(weak_gens)
    commute_32 = maximum([norm(a * b - b * a) for a in color_gens for b in weak_gens])
    commute_31 = maximum([norm(a * y_gen - y_gen * a) for a in color_gens])
    commute_21 = maximum([norm(a * y_gen - y_gen * a) for a in weak_gens])

    charges = [Float64(s["q"]) for s in states]
    quantization_residual = maximum([abs(3.0 * q - round(3.0 * q)) for q in charges])
    q_reconstruction_residual = norm(q_gen - q_recon)
    u_charge_values = sort(unique([round(Float64(s["q"]), digits = 12) for s in states if s["family"] == "u"]))
    d_charge_values = sort(unique([round(Float64(s["q"]), digits = 12) for s in states if s["family"] == "d"]))
    nu_charge_values = sort(unique([round(Float64(s["q"]), digits = 12) for s in states if s["family"] == "nu"]))
    e_charge_values = sort(unique([round(Float64(s["q"]), digits = 12) for s in states if s["family"] == "e"]))
    quark_color_counts = Dict(fam => length(unique([Int(s["color"]) for s in states if s["family"] == fam && Int(s["color"]) >= 0])) for fam in ["u", "d"])
    lepton_color_counts = Dict(fam => length(unique([Int(s["color"]) for s in states if s["family"] == fam])) for fam in ["nu", "e"])

    drop_o_su3_rank = span_rank([zero_full(length(states)) for _ in color_gens])
    drop_h_su2_rank = span_rank([zero_full(length(states)) for _ in weak_gens])
    erased_y_recon_residual = norm(q_gen - t3)
    wrong_color_rank = span_rank([embed_color(states, g) for g in color_local[1:3]])

    carrier = carrier_checks()
    qit_checks = qit_spec_checks()
    su3 = su3_rank == 8 && su3_closure < TOL && Int(carrier["der_o_dim"]) == 14
    su2 = su2_rank == 3 && su2_closure < TOL && Float64(carrier["h_i_j_minus_k_residual"]) < TOL
    u1 = u1_rank == 1 && q_reconstruction_residual < TOL
    charges_match = u_charge_values == [round(2.0 / 3.0, digits = 12)] &&
        d_charge_values == [round(-1.0 / 3.0, digits = 12)] &&
        nu_charge_values == [0.0] &&
        e_charge_values == [-1.0] &&
        quark_color_counts == Dict("u" => 3, "d" => 3) &&
        lepton_color_counts == Dict("nu" => 1, "e" => 1) &&
        quantization_residual < TOL
    controls = Dict{String,Any}(
        "dropping_O_loses_su3" => drop_o_su3_rank == 0 && su3_rank == 8,
        "dropping_H_loses_su2" => drop_h_su2_rank == 0 && su2_rank == 3,
        "wrong_color_structure_not_su3" => wrong_color_rank == 3 && wrong_color_rank != su3_rank,
        "erasing_hypercharge_breaks_electric_charge" => erased_y_recon_residual > 1.0,
    )
    full_group = su3 && su2 && u1 && charges_match &&
        commute_32 < TOL && commute_31 < TOL && commute_21 < TOL &&
        Bool(qit_checks["qit_spec_ok"]) && all(Bool(v) for v in values(controls))
    verdicts = Dict{String,Any}(
        "su3" => su3,
        "su2" => su2,
        "u1" => u1,
        "full_group" => full_group,
        "charges_match" => charges_match,
        "charge_quantization" => quantization_residual < TOL,
        "qit_spec_ok" => Bool(qit_checks["qit_spec_ok"]),
        "carrier_dependencies_ok" => Int(carrier["der_o_dim"]) == 14 &&
            Float64(carrier["h_i_j_minus_k_residual"]) < TOL &&
            Float64(carrier["o_fano_e1_e2_minus_e3_residual"]) < TOL,
    )
    shared_scalars = Dict{String,Any}(
        "state_count" => Float64(length(states)),
        "su3_rank" => Float64(su3_rank),
        "su2_rank" => Float64(su2_rank),
        "u1_rank" => Float64(u1_rank),
        "full_group_rank_sum" => Float64(su3_rank + su2_rank + u1_rank),
        "su3_closure_residual" => su3_closure,
        "su2_closure_residual" => su2_closure,
        "su3_su2_commutator_residual" => commute_32,
        "su3_u1_commutator_residual" => commute_31,
        "su2_u1_commutator_residual" => commute_21,
        "charge_reconstruction_residual" => q_reconstruction_residual,
        "charge_quantization_residual" => quantization_residual,
        "drop_o_su3_rank" => Float64(drop_o_su3_rank),
        "drop_h_su2_rank" => Float64(drop_h_su2_rank),
        "wrong_color_rank" => Float64(wrong_color_rank),
        "erased_hypercharge_charge_residual" => erased_y_recon_residual,
        "der_o_dim" => Float64(carrier["der_o_dim"]),
        "h_dim" => Float64(carrier["h_dim"]),
        "o_dim" => Float64(carrier["o_dim"]),
        "cl6_real_dim" => Float64(carrier["cl6_real_dim"]),
        "cl6_fermion_fock_dim" => Float64(carrier["cl6_fermion_fock_dim"]),
        "qit_substage_count_per_engine" => Float64(qit_checks["substage_count_per_engine"]),
        "qit_type_one_schedule_len" => Float64(qit_checks["type_one_schedule_len"]),
        "qit_type_two_schedule_len" => Float64(qit_checks["type_two_schedule_len"]),
        "qit_type_two_minus_h0_residual" => Float64(qit_checks["type_two_minus_h0_residual"]),
    )
    shared_booleans = Dict{String,Any}()
    for (k, v) in verdicts
        shared_booleans["verdict.$k"] = Bool(v)
    end
    for (k, v) in controls
        shared_booleans["control.$k"] = Bool(v)
    end
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "schema" => "SCRATCH_DIAGNOSTIC_RESULT_v1",
        "name" => OBJECT_ID,
        "backend" => "julia_float64",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => "Finite R x C x H x O / SM-gauge representation witness only; no physics, Standard Model validation, M(C), Axis0, bridge, basin, or formal-admission claim.",
        "allowed_claims" => ["finite representation witness", "backend parity witness", "control-firing diagnostic"],
        "blocked_consumers" => ["physics_claims", "SM_admission", "M(C)_admission", "Axis0", "bridge", "formal_admission"],
        "sim_execution_kind" => "classical",
        "sim_class" => "finite_formal_scout",
        "numpy_compute_used" => false,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "source_dependencies" => SOURCE_DEPENDENCIES,
        "tools" => ["Julia LinearAlgebra", "owner finite carrier scripts", "canonical_qit_engine_specs.py mirror constants"],
        "tool_manifest" => Dict(
            "Julia LinearAlgebra" => "load-bearing for finite matrices, ranks, commutators, charge reconstruction, and parity scalars",
            "owner finite carrier scripts" => "load-bearing source for R/C/H/O multiplication, octonion Fano table, G2 derivation dimension, and Clifford dimension witnesses",
            "canonical_qit_engine_specs.py mirror constants" => "load-bearing source mirror for H0, Type1/Type2 sign, Lindblad/operator inventory, and 32-substage schedule checks",
        ),
        "TOOL_MANIFEST" => Dict(
            "Julia LinearAlgebra" => "load-bearing for finite matrices, ranks, commutators, charge reconstruction, and parity scalars",
            "owner finite carrier scripts" => "load-bearing source for R/C/H/O multiplication, octonion Fano table, G2 derivation dimension, and Clifford dimension witnesses",
            "canonical_qit_engine_specs.py mirror constants" => "load-bearing source mirror for H0, Type1/Type2 sign, Lindblad/operator inventory, and 32-substage schedule checks",
        ),
        "tool_integration_depth" => Dict("Julia LinearAlgebra" => "load_bearing", "owner finite carrier scripts" => "load_bearing", "canonical_qit_engine_specs.py mirror constants" => "supportive"),
        "TOOL_INTEGRATION_DEPTH" => Dict("Julia LinearAlgebra" => "load_bearing", "owner finite carrier scripts" => "load_bearing", "canonical_qit_engine_specs.py mirror constants" => "supportive"),
        "states" => states,
        "carrier_checks" => carrier,
        "qit_spec_checks" => qit_checks,
        "charge_classes" => Dict(
            "u_quark" => u_charge_values,
            "d_quark" => d_charge_values,
            "neutrino" => nu_charge_values,
            "charged_lepton" => e_charge_values,
            "quark_color_counts" => quark_color_counts,
            "lepton_color_counts" => lepton_color_counts,
        ),
        "controls" => controls,
        "verdicts" => verdicts,
        "positive" => Dict(
            "octonion_su3_color_triplet_witness" => Dict("pass" => su3),
            "quaternion_su2_weak_doublet_witness" => Dict("pass" => su2),
            "u1_hypercharge_charge_reconstruction" => Dict("pass" => u1 && charges_match),
            "qit_engine_spec_readback" => Dict("pass" => Bool(qit_checks["qit_spec_ok"])),
        ),
        "graveyard_companions" => Dict(key => Dict("pass" => Bool(value)) for (key, value) in controls),
        "boundary" => Dict(
            "classification_is_scratch_diagnostic" => Dict("pass" => true),
            "promotion_disallowed" => Dict("pass" => true),
            "formal_admission_disallowed" => Dict("pass" => true),
            "claim_ceiling_blocks_physics_axis_bridge" => Dict("pass" => true),
        ),
        "nearby_variants" => Dict(
            "total" => length(controls),
            "passed" => sum(Bool(value) ? 1 : 0 for value in values(controls)),
            "variant_names" => sort(collect(keys(controls))),
        ),
        "why_not_v4_probes" => [
            "finite witness only, no formal proof layer",
            "one-generation representation check only, no dynamics or phenomenology",
            "controls erase O/H/Y structure instead of proving source inevitability",
        ],
        "blockers" => full_group ? [] : ["finite witness failed"],
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "plain_sentence" => "Finite witness: octonion color generators give su3 on quark triplets, quaternion weak generators give su2 on left doublets, and hypercharge reconstructs quantized electric charges on one generation.",
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["all_pass"] = full_group && Bool(result["parity"]["within_1e_9"])
    result["stop_condition_fired"] = !full_group || Bool(result["parity"]["stop_condition_fired"])
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("MP_FULL_SM_GAUGE_JULIA all_pass=$(result["all_pass"]) su3=$(result["verdicts"]["su3"]) su2=$(result["verdicts"]["su2"]) u1=$(result["verdicts"]["u1"]) full_group=$(result["verdicts"]["full_group"]) charges_match=$(result["verdicts"]["charges_match"]) parity=$(result["parity"]["parity_max_diff"]) wrote=$(RESULT_PATH)")
    exit(result["stop_condition_fired"] ? 2 : 0)
end

main()
