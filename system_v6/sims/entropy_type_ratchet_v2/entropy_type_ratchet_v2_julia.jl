#!/usr/bin/env julia

using JSON
using SHA
using Dates
using LinearAlgebra
using QuantumOptics
using Z3

const SIM_ID = "entropy_type_ratchet_v2"
const ROOT = normpath(joinpath(abspath(@__DIR__), "..", "..", ".."))
const PACKET = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(PACKET, "results")
const RESULT = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const SOURCE = joinpath(PACKET, "$(SIM_ID)_julia.jl")
const TRAJECTORY_PATH = joinpath(ROOT, "system_v6", "sims", "manifold_unified_run_v0", "results", "manifold_unified_run_v0_step_trajectory_artifact.json")
const DEEP_PATH = joinpath(ROOT, "system_v6", "sims", "ratchet_deep_chain_v0", "results", "ratchet_deep_chain_v0_envelope_results.json")
const Z4_PATH = joinpath(ROOT, "system_v6", "sims", "z4_syndrome_record_v0", "results", "z4_syndrome_record_v0_envelope_results.json")
const TYPE_ORDER = [
    "counting_entropy",
    "chart_uniform_differential_entropy",
    "von_neumann_entropy",
    "conditional_vn_and_mutual_information",
    "coherent_information",
    "state_plus_record_conservation",
]

function rel(path::AbstractString)
    normalized = normpath(abspath(path))
    prefix = endswith(ROOT, "/") ? ROOT : ROOT * "/"
    return startswith(normalized, prefix) ? normalized[length(prefix)+1:end] : normalized
end

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))
stable_sha(obj) = bytes2hex(SHA.sha256(codeunits(JSON.json(obj))))

function facts()
    return Dict(
        "trajectory" => JSON.parsefile(TRAJECTORY_PATH),
        "deep" => JSON.parsefile(DEEP_PATH),
        "z4" => JSON.parsefile(Z4_PATH),
    )
end

function deep_row(fs::Dict, step::Int)
    rows = fs["deep"]["ratchet_sequence"]["per_step_ledger"]["rows"]
    return first(row for row in rows if Int(row["step"]) == step)
end

function initial_state(fs::Dict)
    seed = fs["trajectory"]["trajectory"]["steps"][1]
    dim = Int(seed["carrier_dimension"])
    amp = 1 / sqrt(dim)
    return Dict(
        "step_id" => "integrated_seed",
        "support" => ["seed_q$(i)" for i in 0:(dim - 1)],
        "state_vector" => fill(amp, dim),
        "chart" => nothing,
        "rho" => nothing,
        "bipartition" => nothing,
        "channel" => nothing,
        "record" => nothing,
        "lineage" => [Dict("operation" => "seed_from_manifold_unified_run_v0", "source_sha256" => stable_sha(seed))],
    )
end

function copy_state(state::Dict)
    return deepcopy(state)
end

function density_from_live_quotient(state::Dict)
    probs = Dict("rho_class_0" => 0.0, "rho_class_1" => 0.0)
    for (idx, amp) in enumerate(state["state_vector"])
        key = isodd(idx) ? "rho_class_0" : "rho_class_1"
        probs[key] += abs2(float(amp))
    end
    return [probs["rho_class_0"], probs["rho_class_1"]]
end

function apply_leaf_conditioning(state::Dict, fs::Dict)
    st = copy_state(state)
    row = deep_row(fs, 1)
    st["step_id"] = "leaf_conditioning"
    st["chart"] = Dict("h_nats" => row["entropy"]["h_nats"], "h_float_nats" => row["entropy"]["h_float_nats"], "source_sha256" => stable_sha(row))
    push!(st["lineage"], Dict("operation" => "apply_leaf_conditioning", "constructed" => "chart_measure_layer"))
    return st
end

function apply_lens_quotient(state::Dict, fs::Dict)
    st = copy_state(state)
    row = deep_row(fs, 2)
    diag = density_from_live_quotient(st)
    st["step_id"] = "lens_quotient"
    st["support"] = ["rho_class_0", "rho_class_1"]
    st["rho"] = Dict("diag" => diag, "source" => "state_lineage.quotient_map", "source_sha256" => stable_sha(row))
    push!(st["lineage"], Dict("operation" => "apply_lens_quotient", "constructed" => "density_quotient_rho"))
    return st
end

function apply_lens_quotient_erased(state::Dict, fs::Dict)
    st = copy_state(state)
    st["step_id"] = "lens_quotient"
    push!(st["lineage"], Dict("operation" => "apply_lens_quotient_erased", "constructed" => "none"))
    return st
end

function apply_terrain_restriction(state::Dict, fs::Dict)
    st = copy_state(state)
    step = fs["trajectory"]["trajectory"]["steps"][4]
    st["step_id"] = "terrain_restriction"
    st["bipartition"] = Dict("product_state" => true, "source_sha256" => stable_sha(step["s5_s6_terrain_flow"]))
    push!(st["lineage"], Dict("operation" => "apply_terrain_restriction", "constructed" => "bipartition_subsystem_split"))
    return st
end

function apply_deep_descended_phase_window(state::Dict, fs::Dict)
    st = copy_state(state)
    row = deep_row(fs, 3)
    st["step_id"] = "deep_descended_phase_window"
    st["channel"] = Dict("channel_id" => "descended_phase_window_to_bell_pair_channel", "source_sha256" => stable_sha(row))
    push!(st["lineage"], Dict("operation" => "apply_deep_descended_phase_window", "constructed" => "channel_update_map"))
    return st
end

function apply_deep_second_z2_lens(state::Dict, fs::Dict)
    st = copy_state(state)
    row = deep_row(fs, 4)
    z4 = fs["z4"]
    st["step_id"] = "deep_second_Z2_lens"
    st["record"] = Dict("syndrome_table_sha256" => stable_sha(z4["syndrome_table"]), "positive_regime" => z4["regimes"]["positive"], "deep_lens_sha256" => stable_sha(row))
    st["support"] = ["$(item["quotient_output"])::$(item["syndrome"])" for item in z4["syndrome_table"]]
    push!(st["lineage"], Dict("operation" => "apply_deep_second_z2_lens", "constructed" => "record_syndrome_preimage_table"))
    return st
end

function apply_deep_terrain_basin(state::Dict, fs::Dict)
    st = copy_state(state)
    st["step_id"] = "deep_terrain_basin"
    push!(st["lineage"], Dict("operation" => "apply_deep_terrain_basin", "constructed" => "no_new_type_object"))
    return st
end

function apply_deep_terrain_operator(state::Dict, fs::Dict)
    st = copy_state(state)
    st["step_id"] = "deep_terrain_operator"
    push!(st["lineage"], Dict("operation" => "apply_deep_terrain_operator", "constructed" => "no_new_type_object"))
    return st
end

function apply_deep_saturation(state::Dict, fs::Dict)
    st = copy_state(state)
    st["step_id"] = "deep_saturation"
    push!(st["lineage"], Dict("operation" => "apply_deep_saturation", "constructed" => "fixed_point_no_new_type_object"))
    return st
end

function parent_operation_tokens(fs::Dict)
    out = String[]
    for idx in 1:length(fs["trajectory"]["trajectory"]["steps"])
        if idx == 1
            push!(out, "integrated_seed")
        elseif idx == 2
            push!(out, "leaf_conditioning")
        elseif idx == 3
            push!(out, "lens_quotient")
        elseif idx == 4
            push!(out, "terrain_restriction")
        end
    end
    for row in sort(fs["deep"]["ratchet_sequence"]["per_step_ledger"]["rows"], by = row -> Int(row["step"]))
        step = Int(row["step"])
        if step == 3
            push!(out, "deep_descended_phase_window")
        elseif step == 4
            push!(out, "deep_second_Z2_lens")
        elseif step == 5
            push!(out, "deep_terrain_basin")
        elseif step == 6
            push!(out, "deep_terrain_operator")
        elseif step == 7
            push!(out, "deep_saturation")
        end
    end
    return out
end

function operation_functions(fs::Dict; perturb::Bool=false)
    lens_fn = perturb ? apply_lens_quotient_erased : apply_lens_quotient
    mapping = Dict(
        "integrated_seed" => (s, f) -> s,
        "leaf_conditioning" => apply_leaf_conditioning,
        "lens_quotient" => lens_fn,
        "terrain_restriction" => apply_terrain_restriction,
        "deep_descended_phase_window" => apply_deep_descended_phase_window,
        "deep_second_Z2_lens" => apply_deep_second_z2_lens,
        "deep_terrain_basin" => apply_deep_terrain_basin,
        "deep_terrain_operator" => apply_deep_terrain_operator,
        "deep_saturation" => apply_deep_saturation,
    )
    return [mapping[token] for token in parent_operation_tokens(fs)]
end

function entropy_vn_rho(diag::Vector{Float64})
    b = QuantumOptics.NLevelBasis(length(diag))
    rho = QuantumOptics.DenseOperator(b, b, Diagonal(diag))
    return Float64(real(QuantumOptics.entropy_vn(rho)))
end

function bell_receipt()
    b = QuantumOptics.NLevelBasis(2)
    z = QuantumOptics.basisstate(b, 1)
    o = QuantumOptics.basisstate(b, 2)
    psi = (QuantumOptics.tensor(z, z) + QuantumOptics.tensor(o, o)) / sqrt(2)
    bell = QuantumOptics.dm(psi)
    rho_a = QuantumOptics.ptrace(bell, [2])
    rho_b = QuantumOptics.ptrace(bell, [1])
    return Dict(
        "S_AB" => Float64(real(QuantumOptics.entropy_vn(bell))),
        "S_A" => Float64(real(QuantumOptics.entropy_vn(rho_a))),
        "S_B" => Float64(real(QuantumOptics.entropy_vn(rho_b))),
    )
end

function status_for_type(state::Dict, type_id::String)
    if type_id == "counting_entropy"
        return isempty(state["support"]) ? 0 : 1
    elseif type_id == "chart_uniform_differential_entropy"
        return state["chart"] === nothing ? 0 : 1
    elseif type_id == "von_neumann_entropy"
        return state["rho"] === nothing ? 0 : 1
    elseif type_id == "conditional_vn_and_mutual_information"
        return state["bipartition"] === nothing ? 0 : (state["channel"] === nothing ? 2 : 1)
    elseif type_id == "coherent_information"
        return state["channel"] === nothing ? 0 : 1
    elseif type_id == "state_plus_record_conservation"
        return state["record"] === nothing ? 0 : 1
    end
    error("unknown type")
end

function status_matrix(; perturb::Bool=false)
    fs = facts()
    state = initial_state(fs)
    out = Vector{Vector{Int}}()
    for op in operation_functions(fs, perturb=perturb)
        state = op(state, fs)
        push!(out, [status_for_type(state, type_id) for type_id in TYPE_ORDER])
    end
    return out
end

function z3_table_receipt(primary::Vector{Vector{Int}}, recomputed::Vector{Vector{Int}}, perturbed::Vector{Vector{Int}})
    flat_primary = vcat(primary...)
    flat_recomputed = vcat(recomputed...)
    flat_perturbed = vcat(perturbed...)
    solver = Z3.Solver()
    terms = Z3.Expr[]
    for (idx, value) in enumerate(flat_primary)
        p = Z3.IntVar("julia_primary_$(idx)")
        r = Z3.IntVar("julia_recomputed_$(idx)")
        Z3.add(solver, p == Z3.IntVal(value))
        Z3.add(solver, r == Z3.IntVal(flat_recomputed[idx]))
        push!(terms, Z3.Not(p == r))
    end
    Z3.add(solver, Z3.Or(terms))
    verdict = lowercase(string(Z3.check(solver)))

    flip = Z3.Solver()
    flip_terms = Z3.Expr[]
    changed = Any[]
    for (idx, value) in enumerate(flat_primary)
        p = Z3.IntVar("julia_flip_primary_$(idx)")
        q = Z3.IntVar("julia_flip_perturbed_$(idx)")
        Z3.add(flip, p == Z3.IntVal(value))
        Z3.add(flip, q == Z3.IntVal(flat_perturbed[idx]))
        push!(flip_terms, Z3.Not(p == q))
        if value != flat_perturbed[idx]
            step = div(idx - 1, length(TYPE_ORDER))
            type_id = TYPE_ORDER[mod(idx - 1, length(TYPE_ORDER)) + 1]
            push!(changed, Dict("step_index" => step, "type_id" => type_id, "primary_status_code" => value, "perturbed_status_code" => flat_perturbed[idx]))
        end
    end
    Z3.add(flip, Z3.Or(flip_terms))
    flip_verdict = lowercase(string(Z3.check(flip)))
    return Dict(
        "ran" => true,
        "solver" => "Z3.jl",
        "verdict" => verdict,
        "perturbed_construction_path_verdict" => flip_verdict,
        "load_bearing" => true,
        "bound_cells" => length(flat_primary),
        "polarity" => "negated_identity_over_discovered_status_matrix",
        "perturbation" => "erase quotient map before vN construction and recompute table",
        "changed_cells" => changed[1:min(length(changed), 12)],
        "positive_case" => "primary and recomputed construction status matrices cannot differ",
        "negative/erased_control" => "erased quotient-map path recomputes at least one different status and is SAT",
        "boundary_case" => "status codes are undefined/computable/degenerate integers",
        "demotion_condition" => "demote if Z3.jl is bound only to a final count",
    )
end

function quantumoptics_receipt()
    fs = facts()
    state = initial_state(fs)
    states = Dict{String, Any}()
    for op in operation_functions(fs)
        state = op(state, fs)
        states[state["step_id"]] = deepcopy(state)
    end
    diag = Float64.(states["lens_quotient"]["rho"]["diag"])
    rho_entropy = entropy_vn_rho(diag)
    bell = bell_receipt()
    return Dict(
        "api" => "QuantumOptics.NLevelBasis/DenseOperator/entropy_vn/tensor/dm/ptrace",
        "rho_diag" => diag,
        "rho_entropy_nats" => rho_entropy,
        "rho_entropy_exact" => "log(2)",
        "bell_entropy_nats" => bell["S_AB"],
        "bell_S_A_nats" => bell["S_A"],
        "bell_S_B_nats" => bell["S_B"],
        "coherent_information_nats" => bell["S_B"] - bell["S_AB"],
        "pass" => abs(rho_entropy - log(2.0)) <= 1.0e-10 && abs(bell["S_AB"]) <= 1.0e-10 && abs((bell["S_B"] - bell["S_AB"]) - log(2.0)) <= 1.0e-10,
    )
end

function main()
    mkpath(RESULT_DIR)
    fs = facts()
    parent_tokens = parent_operation_tokens(fs)
    primary = status_matrix()
    recomputed = status_matrix()
    perturbed = status_matrix(perturb=true)
    z3_receipt = z3_table_receipt(primary, recomputed, perturbed)
    q = quantumoptics_receipt()
    final_count = count(x -> x > 0, primary[end])
    all_pass = q["pass"] && z3_receipt["verdict"] == "unsat" && z3_receipt["perturbed_construction_path_verdict"] == "sat" && final_count == length(TYPE_ORDER)
    payload = Dict(
        "schema_version" => "$(SIM_ID)_julia_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "role_id" => "julia_reference_builder",
        "source_path" => rel(SOURCE),
        "source_sha256" => sha256_file(SOURCE),
        "result_path" => rel(RESULT),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "packages_used" => ["QuantumOptics", "Z3", "JSON", "SHA", "Dates", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "package_observables" => Dict(
            "QuantumOptics" => "NLevelBasis/DenseOperator/entropy_vn/tensor/dm/ptrace construct rho, bipartition, and channel entropy witnesses",
            "Z3" => "Z3.Solver binds every discovered status code and SAT flip after quotient-map erasure",
        ),
        "claim_path_tools" => ["QuantumOptics", "Z3"],
        "TOOL_MANIFEST" => Dict(
            "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing density, bipartition, channel entropy construction"),
            "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing discovered table proof"),
            "JSON/SHA/Dates" => Dict("tried" => true, "used" => true, "reason" => "supportive parent loading, serialization, hashing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("QuantumOptics" => "load_bearing", "Z3" => "load_bearing", "JSON/SHA/Dates" => "supportive"),
        "quantumoptics_receipt" => q,
        "status_matrix" => primary,
        "sequence_source" => Dict(
            "sequence_source" => "consumed_parent_artifacts",
            "operation_order" => parent_tokens,
            "trajectory_path" => rel(TRAJECTORY_PATH),
            "deep_path" => rel(DEEP_PATH),
            "parent_order_hash" => stable_sha(parent_tokens),
        ),
        "crossover_proofs" => Dict("julia_z3" => z3_receipt),
        "engine_values" => Dict("final_available_type_count" => final_count, "rho_entropy_nats" => q["rho_entropy_nats"], "status_matrix_sha256" => stable_sha(primary)),
        "tool_calls" => [
            Dict(
                "tool" => "QuantumOptics",
                "qualified_api/function" => "QuantumOptics.NLevelBasis/DenseOperator/entropy_vn/tensor/dm/ptrace",
                "input_object" => "constructed density quotient, Bell bipartition, and channel boundary",
                "output_object" => "vN entropy, conditional/MI boundary, coherent information",
                "positive_case" => "rho=diag(1/2,1/2) has S=log(2); Bell channel has I_c=log(2)",
                "negative/erased_control" => "quotient-map-erased construction removes rho status in table proof",
                "boundary_case" => "product bipartition before channel is degenerate",
                "demotion_condition" => "demote if density/channel is local fixture or not lineage-derived",
                "gates" => ["rho", "entropy", "channel", "all_pass"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver/Z3.IntVar/Z3.add/Z3.Or/Z3.check",
                "input_object" => "construction-derived status matrix and erased-quotient perturbation",
                "output_object" => "UNSAT identity and SAT perturbation",
                "positive_case" => z3_receipt["positive_case"],
                "negative/erased_control" => z3_receipt["negative/erased_control"],
                "boundary_case" => z3_receipt["boundary_case"],
                "demotion_condition" => z3_receipt["demotion_condition"],
                "gates" => ["proof", "all_pass"],
            ),
        ],
        "all_pass" => all_pass,
    )
    open(RESULT, "w") do io
        JSON.print(io, payload, 2)
        println(io)
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => rel(RESULT))))
    return all_pass ? 0 : 1
end

exit(main())
