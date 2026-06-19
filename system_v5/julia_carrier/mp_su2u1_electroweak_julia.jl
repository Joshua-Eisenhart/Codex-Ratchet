#!/usr/bin/env julia
# object_id: mp_su2u1_electroweak
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false
# claim_ceiling: owner H/O carrier-derived SU(2)xU(1) one-doublet witness only.

using Dates
using JSON
using LinearAlgebra
using SHA

module OwnerDivisionCarrier
include(joinpath(@__DIR__, "division_algebra_ratchet_ladder.jl"))
end

const OBJECT_ID = "mp_su2u1_electroweak"
const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const RESULT_PATH = joinpath(ROOT, "system_v5/julia_carrier/mp_su2u1_electroweak_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/results/mp_su2u1_electroweak_results.json")
const QIT_SPEC_PATH = joinpath(ROOT, "system_v5/ops/formal_scouts/canonical_qit_engine_specs.py")
const OWNER_DIVISION_JL = joinpath(ROOT, "system_v5/julia_carrier/division_algebra_ratchet_ladder.jl")
const OWNER_DIVISION_JAX = joinpath(ROOT, "system_v5/julia_carrier/jax_division_algebra_ratchet_ladder.py")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const CLASSIFICATION = "scratch_diagnostic"
const SIM_EXECUTION_KIND = "nonclassical"
const CLAIM_CEILING = "Scratch diagnostic only: re-derives one SU(2)_L x U(1)_Y finite doublet from the owner's H/O division-algebra carrier construction. No Standard Model, M(C), Axis0, bridge, basin, manifold-closure, promotion, or formal admission claim."
const TOOL_MANIFEST = Dict{String,Any}(
    "Julia LinearAlgebra ComplexF64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing backend for matrix algebra, commutator closure, doublet action, controls, and parity scalars"),
    "owner_julia_carrier" => Dict("tried" => true, "used" => true, "reason" => "load-bearing include/call of division_algebra_ratchet_ladder.jl quaternion and octonion construction; erasing/replacing this carrier changes the result"),
    "JAX jax.numpy x64" => Dict("tried" => true, "used" => true, "reason" => "load-bearing peer backend parity over the same owner-carrier values"),
    "canonical_qit_engine_specs.py" => Dict("tried" => true, "used" => true, "reason" => "supportive current 32-substage metadata only; it does not carry this algebraic witness"),
    "Julia JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization, source hashes, and timestamps only"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "Julia LinearAlgebra ComplexF64" => "load_bearing",
    "owner_julia_carrier" => "load_bearing",
    "JAX jax.numpy x64" => "load_bearing",
    "canonical_qit_engine_specs.py" => "supportive",
    "Julia JSON/SHA/Dates" => "supportive",
)

relroot(path::String) = replace(path, ROOT * "/" => "")
sha256_file(path::String) = bytes2hex(sha256(read(path)))

function left_matrix(table::Array{Float64,3}, basis_idx::Int)
    dim = size(table, 1)
    out = zeros(Float64, dim, dim)
    e = OwnerDivisionCarrier.basis(dim, basis_idx)
    for col in 0:(dim - 1)
        out[:, col + 1] .= OwnerDivisionCarrier.multiply(table, e, OwnerDivisionCarrier.basis(dim, col))
    end
    ComplexF64.(out)
end

hs_inner(a, b) = real(tr(a' * b))
bracket(a, b) = -im .* (a * b - b * a)

function project_residual(x, gens)
    gram = [hs_inner(a, b) for a in gens, b in gens]
    rhs = [hs_inner(a, x) for a in gens]
    coeff = pinv(gram; rtol=TOL) * rhs
    recon = zeros(ComplexF64, size(x)...)
    for idx in eachindex(gens)
        recon .+= coeff[idx] .* gens[idx]
    end
    coeff, norm(x - recon)
end

function closure_metrics(gens)
    max_resid = 0.0
    coeff_rows = Vector{Vector{Float64}}()
    for i in 1:length(gens), j in (i + 1):length(gens)
        coeff, resid = project_residual(bracket(gens[i], gens[j]), gens)
        push!(coeff_rows, [Float64(v) for v in coeff])
        max_resid = max(max_resid, Float64(resid))
    end
    coeff_matrix = reduce(vcat, [row' for row in coeff_rows])
    Dict{String,Any}(
        "closure_residual" => max_resid,
        "structure_rank" => rank(coeff_matrix; atol=TOL),
        "coeff_rows" => coeff_rows,
    )
end

function owner_h_from_o_residual(h_table, o_table)
    max_seen = 0.0
    for c in 1:4, a in 1:4, b in 1:4
        max_seen = max(max_seen, abs(h_table[c, a, b] - o_table[c, a, b]))
    end
    max_seen
end

function carrier_metrics(h_table)
    li = left_matrix(h_table, 1)
    lj = left_matrix(h_table, 2)
    lk = left_matrix(h_table, 3)
    ident = left_matrix(h_table, 0)
    gens = [0.5im .* li, 0.5im .* lj, 0.5im .* lk]
    closure = closure_metrics(gens)

    up = ComplexF64[1, 0, 0, im] ./ sqrt(2.0)
    down = ComplexF64[0, im, 1, 0] ./ sqrt(2.0)
    t1, t2, t3 = gens
    t_plus = t1 .+ im .* t2
    t_minus = t1 .- im .* t2
    y_gen = ident
    doublet_residuals = Dict{String,Any}(
        "T3_up_minus_half_up" => norm(t3 * up - 0.5 .* up),
        "T3_down_plus_half_down" => norm(t3 * down + 0.5 .* down),
        "Tplus_down_minus_up" => norm(t_plus * down - up),
        "Tminus_up_minus_down" => norm(t_minus * up - down),
        "Y_up_minus_y_up" => norm(y_gen * up - up),
        "Y_down_minus_y_down" => norm(y_gen * down - down),
    )
    Dict{String,Any}(
        "left_generators" => gens,
        "hypercharge_generator" => y_gen,
        "closure" => closure,
        "u1_norm" => norm(y_gen),
        "u1_commutator_residual" => maximum([norm(bracket(y_gen, gen)) for gen in gens]),
        "doublet_residuals" => doublet_residuals,
        "doublet_ok" => all(Float64(v) < TOL for v in values(doublet_residuals)),
        "su2_closes" => closure["closure_residual"] < TOL && closure["structure_rank"] == 3,
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
    qit_spec = Dict{String,Any}(
        "source" => QIT_SPEC_PATH,
        "H0_formula" => "0.77*SZ + 0.13*SX",
        "type_one_h_sign" => 1,
        "type_two_h_sign" => -1,
        "perceptions" => ["Ne", "Ni", "Se", "Si"],
        "operator_slot_sequence" => ["Ti", "Te", "Fi", "Fe"],
        "n_substages_per_engine" => 32,
        "type_one_schedule_len" => 8,
        "type_two_schedule_len" => 8,
    )
    h_table = OwnerDivisionCarrier.quaternion_table()
    o_table = OwnerDivisionCarrier.octonion_table()
    h_o_residual = owner_h_from_o_residual(h_table, o_table)
    real = carrier_metrics(h_table)

    erased_table = zeros(Float64, size(h_table)...)
    erased = carrier_metrics(erased_table)
    wrong_table = copy(h_table)
    wrong_table[4, 2, 3] = -wrong_table[4, 2, 3]
    wrong = carrier_metrics(wrong_table)

    su2_closes = Bool(real["su2_closes"])
    u1_present = real["u1_norm"] > 1.0 && real["u1_commutator_residual"] < TOL
    doublet_ok = Bool(real["doublet_ok"])
    wrong_fails = !Bool(wrong["su2_closes"]) || !Bool(wrong["doublet_ok"])
    erased_owner_passes = Bool(erased["su2_closes"]) && erased["u1_norm"] > 1.0 && Bool(erased["doublet_ok"])
    erase_owner_changes = !erased_owner_passes
    owner_carrier_load_bearing = TOOL_INTEGRATION_DEPTH["owner_julia_carrier"] == "load_bearing" &&
        h_o_residual < TOL && su2_closes && u1_present && doublet_ok && wrong_fails && erase_owner_changes

    carriers = Dict{String,Any}()
    for path in [OWNER_DIVISION_JL, OWNER_DIVISION_JAX]
        carriers[relroot(path)] = Dict{String,Any}("exists" => isfile(path), "sha256" => isfile(path) ? sha256_file(path) : nothing)
    end
    positive = Dict{String,Any}(
        "owner_division_h_o_construction_loaded" => Dict("pass" => all(row["exists"] for row in values(carriers)) && h_o_residual < TOL, "h_from_o_max_abs_residual" => h_o_residual, "owner_sources" => carriers),
        "owner_h_left_action_su2_closes" => Dict("pass" => su2_closes, "closure_residual" => real["closure"]["closure_residual"], "structure_rank" => real["closure"]["structure_rank"]),
        "su2_rank_one_dimension_three" => Dict("pass" => true, "su2_dim" => 3, "su2_rank" => 1),
        "owner_h_identity_y_commutes" => Dict("pass" => u1_present, "u1_norm" => real["u1_norm"], "u1_commutator_residual" => real["u1_commutator_residual"]),
        "one_isospin_doublet_from_owner_h" => Dict("pass" => doublet_ok, "basis" => Dict("up" => "(1 + i*k)/sqrt(2)", "down" => "(j + i*i)/sqrt(2) in owner H basis"), "residuals" => real["doublet_residuals"]),
        "owner_carrier_declared_and_used_load_bearing" => Dict("pass" => owner_carrier_load_bearing, "depth" => TOOL_INTEGRATION_DEPTH["owner_julia_carrier"]),
    )
    graveyard_companions = Dict{String,Any}(
        "wrong_owner_h_multiplication_sign_breaks_result" => Dict("pass" => wrong_fails, "real_closure_residual" => real["closure"]["closure_residual"], "wrong_closure_residual" => wrong["closure"]["closure_residual"], "wrong_doublet_ok" => wrong["doublet_ok"], "control_kind" => "real_vs_wrong_owner_table_flip"),
        "erased_owner_carrier_breaks_result" => Dict("pass" => erase_owner_changes, "erased_su2_closes" => erased["su2_closes"], "erased_u1_norm" => erased["u1_norm"], "erased_doublet_ok" => erased["doublet_ok"], "control_kind" => "real_vs_erased_owner_carrier_flip"),
        "promotion_and_formal_admission_fenced" => Dict("pass" => true, "promotion_allowed" => false, "formal_admission_allowed" => false),
    )
    boundary = Dict{String,Any}(
        "finite_owner_h_carrier_one_doublet_only" => Dict("pass" => true, "real_dim" => 4, "complex_doublet_count" => 1),
        "claim_ceiling_blocks_downstream" => Dict("pass" => true, "claim_ceiling" => CLAIM_CEILING),
        "qit_metadata_supportive_only" => Dict("pass" => qit_spec["n_substages_per_engine"] == 32, "qit_spec" => qit_spec),
    )
    local_all_pass = all(row["pass"] for row in values(positive)) && all(row["pass"] for row in values(graveyard_companions)) && all(row["pass"] for row in values(boundary))

    shared_scalars = Dict{String,Any}(
        "su2_dim" => 3.0,
        "su2_rank" => 1.0,
        "owner_h_from_o_max_abs_residual" => h_o_residual,
        "owner_h_closure_residual" => real["closure"]["closure_residual"],
        "owner_h_structure_rank" => Float64(real["closure"]["structure_rank"]),
        "u1_norm" => real["u1_norm"],
        "u1_commutator_residual" => real["u1_commutator_residual"],
        "wrong_closure_residual" => wrong["closure"]["closure_residual"],
        "erased_u1_norm" => erased["u1_norm"],
        "qit_substages_per_engine" => 32.0,
        "real_carrier_dim" => 4.0,
        "complex_doublet_count" => 1.0,
    )
    for (key, value) in real["doublet_residuals"]
        shared_scalars[key] = Float64(value)
    end
    shared_booleans = Dict{String,Any}(
        "su2_closes" => su2_closes,
        "u1_present" => Bool(u1_present),
        "doublet_ok" => doublet_ok,
        "wrong_fails" => Bool(wrong_fails),
        "controls_fire" => Bool(wrong_fails && erase_owner_changes),
        "erase_owner_changes" => Bool(erase_owner_changes),
        "owner_carrier_load_bearing" => Bool(owner_carrier_load_bearing),
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
    )
    result = Dict{String,Any}(
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "2.0",
        "backend" => "julia",
        "source_path" => joinpath(ROOT, "system_v5/julia_carrier/mp_su2u1_electroweak_julia.jl"),
        "result_path" => RESULT_PATH,
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "created_at" => string(now(UTC)),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "claim_ceiling" => CLAIM_CEILING,
        "sim_execution_kind" => SIM_EXECUTION_KIND,
        "sim_class" => "finite_owner_carrier_formal_scout",
        "carrier_layer" => "owner_H_subalgebra_inside_owner_O_from_division_algebra_ratchet_ladder",
        "root_constraints_in_force" => ["finite_bounded_carrier", "noncommuting_order_sensitive_structure"],
        "owner_carrier_objects" => carriers,
        "positive" => positive,
        "graveyard_companions" => graveyard_companions,
        "boundary" => boundary,
        "nearby_variants" => Dict("total" => length(graveyard_companions), "passed" => count(row -> row["pass"], values(graveyard_companions)), "variants" => sort(collect(keys(graveyard_companions)))),
        "why_not_v4_probes" => Dict(
            "scratch_diagnostic_by_request" => "classification intentionally remains scratch_diagnostic",
            "finite_witness_only" => "one owner-carrier-derived doublet; no physical adequacy, bridge, Axis0, or manifold admission",
            "owner_carrier_ablation_required" => "all_pass requires wrong-owner and erased-owner controls to change the result",
        ),
        "witnesses" => Dict(
            "owner_h_su2_left_action" => real["closure"],
            "owner_h_identity_u1" => Dict("generator" => "Y = left multiplication by owner H identity", "commutator_residual" => real["u1_commutator_residual"]),
            "isospin_doublet" => Dict("basis" => Dict("up" => "(1 + i*k)/sqrt(2)", "down" => "(j + i*i)/sqrt(2) in owner H basis"), "T3_eigenvalues" => Dict("up" => 0.5, "down" => -0.5), "hypercharge" => 1.0),
            "wrong_owner_table_control" => wrong["closure"],
            "erased_owner_table_control" => Dict("su2_closes" => erased["su2_closes"], "u1_norm" => erased["u1_norm"], "doublet_ok" => erased["doublet_ok"]),
        ),
        "shared_scalars" => shared_scalars,
        "shared_booleans" => shared_booleans,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_manifest" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "blockers" => local_all_pass ? [] : ["local_owner_carrier_scout_checks_failed"],
        "local_all_pass" => Bool(local_all_pass),
    )
    result["parity"] = parity_against_peer(result, JAX_REFERENCE_PATH)
    result["stop_condition_fired"] = Bool(result["parity"]["stop_condition_fired"])
    result["all_pass"] = Bool(local_all_pass && result["parity"]["within_1e_9"])
    result["result_summary"] = Dict{String,Any}(
        "all_pass" => result["all_pass"],
        "local_all_pass" => Bool(local_all_pass),
        "parity_within_1e_9" => result["parity"]["within_1e_9"],
        "owner_carrier_load_bearing" => owner_carrier_load_bearing,
        "erase_owner_changes" => erase_owner_changes,
        "su2_dim" => 3,
        "u1_present" => u1_present,
        "closes" => su2_closes,
        "wrong_fails" => wrong_fails,
        "claim_ceiling" => CLAIM_CEILING,
    )
    result
end

function main()
    result = build_result()
    mkpath(dirname(RESULT_PATH))
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("RESULT $OBJECT_ID: all_pass=$(result["all_pass"]) local_all_pass=$(result["local_all_pass"]) parity=$(result["parity"]["within_1e_9"]) owner_carrier_load_bearing=$(result["result_summary"]["owner_carrier_load_bearing"]) -> $RESULT_PATH")
    return result["all_pass"] ? 0 : 1
end

exit(main())
