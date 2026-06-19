#!/usr/bin/env julia

using Dates
using LinearAlgebra
using SHA

using ACSets
using Catlab
using Catlab.BasicSets
using Catlab.CategoricalAlgebra

const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const SOURCE_PATH = @__FILE__
const RESULT_PATH = joinpath(@__DIR__, "pilot_results.json")

const CLASSIFICATION = "tool_lego_fit_probe"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const TOL = 1.0e-10

# ACSETS_SCHEMA_START
@present SchProbeObs(FreeSchema) begin
    State::Ob
    ProbeValue::Ob
    Obs::Ob
    state::Hom(Obs, State)
    probe_value::Hom(Obs, ProbeValue)
end

@acset_type ProbeObs(SchProbeObs, index = [:state, :probe_value])
# ACSETS_SCHEMA_END

struct Probe
    name::String
    matrix::Matrix{Float64}
end

struct StateRow
    id::String
    vector::Vector{Float64}
end

function json_escape(s::AbstractString)::String
    out = IOBuffer()
    for ch in s
        if ch == '"'
            print(out, "\\\"")
        elseif ch == '\\'
            print(out, "\\\\")
        elseif ch == '\n'
            print(out, "\\n")
        elseif ch == '\r'
            print(out, "\\r")
        elseif ch == '\t'
            print(out, "\\t")
        else
            print(out, ch)
        end
    end
    return String(take!(out))
end

function to_json(x)::String
    if x isa AbstractDict
        keys_sorted = sort(collect(keys(x)); by = string)
        parts = ["\"" * json_escape(string(k)) * "\":" * to_json(x[k]) for k in keys_sorted]
        return "{" * join(parts, ",") * "}"
    elseif x isa AbstractVector || x isa Tuple
        return "[" * join([to_json(v) for v in x], ",") * "]"
    elseif x isa AbstractString
        return "\"" * json_escape(x) * "\""
    elseif x isa Bool
        return x ? "true" : "false"
    elseif x === nothing
        return "null"
    elseif x isa Integer
        return string(x)
    elseif x isa AbstractFloat
        if isfinite(x)
            return string(x)
        else
            return "\"" * string(x) * "\""
        end
    else
        return "\"" * json_escape(string(x)) * "\""
    end
end

function write_json(path::AbstractString, payload::Dict{String, Any})::Nothing
    open(path, "w") do io
        print(io, to_json(payload))
        print(io, "\n")
    end
    return nothing
end

function iso_now()::String
    return Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
end

function file_sha256(path::AbstractString)::String
    return bytes2hex(open(SHA.sha256, path))
end

function rounded_expectation(psi::Vector{Float64}, probe::Probe)::Int
    value = dot(psi, probe.matrix * psi)
    if abs(value - round(value)) > TOL
        error("non-integral pilot expectation: $(probe.name) -> $value")
    end
    return round(Int, value)
end

function finite_system()::Tuple{Vector{StateRow}, Vector{Probe}}
    invsqrt2 = 1.0 / sqrt(2.0)
    states = StateRow[
        StateRow("bell_phi_plus", invsqrt2 .* [1.0, 0.0, 0.0, 1.0]),
        StateRow("bell_phi_minus", invsqrt2 .* [1.0, 0.0, 0.0, -1.0]),
        StateRow("bell_psi_plus", invsqrt2 .* [0.0, 1.0, 1.0, 0.0]),
        StateRow("bell_psi_minus", invsqrt2 .* [0.0, 1.0, -1.0, 0.0]),
    ]
    z = [1.0 0.0; 0.0 -1.0]
    x = [0.0 1.0; 1.0 0.0]
    probes = Probe[
        Probe("Z_L_Z_R", kron(z, z)),
        Probe("X_L_X_R", kron(x, x)),
    ]
    return states, probes
end

function signatures(states::Vector{StateRow}, probes::Vector{Probe})::Vector{Vector{Int}}
    return [[rounded_expectation(state.vector, probe) for probe in probes] for state in states]
end

function class_rows_from_signatures(
    states::Vector{StateRow},
    sigs::Vector{Vector{Int}},
    name::String,
)::Dict{String, Any}
    buckets = Dict{String, Dict{String, Any}}()
    for (state, sig) in zip(states, sigs)
        key = join(string.(sig), ",")
        if !haskey(buckets, key)
            buckets[key] = Dict{String, Any}("members" => String[], "signature" => sig)
        end
        push!(buckets[key]["members"], state.id)
    end
    ordered_keys = sort(collect(keys(buckets)))
    classes = Vector{Dict{String, Any}}()
    for (idx, key) in enumerate(ordered_keys)
        push!(
            classes,
            Dict{String, Any}(
                "class_id" => "$(name)_q$(idx - 1)",
                "members" => sort(buckets[key]["members"]),
                "signature" => buckets[key]["signature"],
            ),
        )
    end
    return Dict{String, Any}(
        "name" => name,
        "class_count" => length(classes),
        "classes" => classes,
        "partition_member_ids" => sort([state.id for state in states]),
    )
end

# HAND_ROLLED_START
function hand_partition(states::Vector{StateRow}, probes::Vector{Probe}, name::String)::Dict{String, Any}
    sigs = signatures(states, probes)
    return class_rows_from_signatures(states, sigs, name)
end
# HAND_ROLLED_END

function build_observation_acset(
    states::Vector{StateRow},
    probes::Vector{Probe},
)::Tuple{ProbeObs, Vector{Dict{String, Any}}}
    sigs = signatures(states, probes)
    value_pairs = Tuple{Int, Int}[]
    for sig in sigs
        for (probe_idx, value) in enumerate(sig)
            pair = (probe_idx, value)
            if !(pair in value_pairs)
                push!(value_pairs, pair)
            end
        end
    end
    sort!(value_pairs)
    pair_to_idx = Dict(pair => idx for (idx, pair) in enumerate(value_pairs))

    obs_states = Int[]
    obs_probe_values = Int[]
    for (state_idx, sig) in enumerate(sigs)
        for (probe_idx, value) in enumerate(sig)
            push!(obs_states, state_idx)
            push!(obs_probe_values, pair_to_idx[(probe_idx, value)])
        end
    end

    acset = ProbeObs()
    add_parts!(acset, :State, length(states))
    add_parts!(acset, :ProbeValue, length(value_pairs))
    add_parts!(acset, :Obs, length(obs_states), state = obs_states, probe_value = obs_probe_values)

    meta = [
        Dict{String, Any}(
            "probe_index" => pair[1],
            "probe_name" => probes[pair[1]].name,
            "value" => pair[2],
            "label" => "$(probes[pair[1]].name)=$(pair[2])",
        ) for pair in value_pairs
    ]
    return acset, meta
end

function signatures_from_acset(
    acset::ProbeObs,
    probe_value_meta::Vector{Dict{String, Any}},
    probe_count::Int,
)::Vector{Vector{Int}}
    sigs = [fill(typemin(Int), probe_count) for _ in 1:nparts(acset, :State)]
    for obs in parts(acset, :Obs)
        state_idx = acset[obs, :state]
        probe_value_idx = acset[obs, :probe_value]
        meta = probe_value_meta[probe_value_idx]
        sigs[state_idx][meta["probe_index"]] = meta["value"]
    end
    if any(any(value == typemin(Int) for value in sig) for sig in sigs)
        error("incomplete observation C-set")
    end
    return sigs
end

# ACSETS_CATLAB_START
function acsets_catlab_partition(
    states::Vector{StateRow},
    probes::Vector{Probe},
    name::String,
)::Dict{String, Any}
    acset, probe_value_meta = build_observation_acset(states, probes)
    sigs = signatures_from_acset(acset, probe_value_meta, length(probes))

    left = Int[]
    right = Int[]
    for i in eachindex(states)
        for j in (i + 1):length(states)
            if sigs[i] == sigs[j]
                push!(left, i)
                push!(right, j)
            end
        end
    end

    state_set = FinSet(length(states))
    relation_left = FinFunction(left, state_set)
    relation_right = FinFunction(right, state_set)
    coeq = coequalizer[FinSetC()](relation_left, relation_right)
    projection = collect(force(proj(coeq)))

    buckets = Dict{Int, Vector{Int}}()
    for (state_idx, class_idx) in enumerate(projection)
        if !haskey(buckets, class_idx)
            buckets[class_idx] = Int[]
        end
        push!(buckets[class_idx], state_idx)
    end

    classes = Vector{Dict{String, Any}}()
    for class_idx in sort(collect(keys(buckets)))
        member_indices = sort(buckets[class_idx])
        push!(
            classes,
            Dict{String, Any}(
                "class_id" => "$(name)_q$(length(classes))",
                "members" => sort([states[idx].id for idx in member_indices]),
                "signature" => sigs[first(member_indices)],
            ),
        )
    end
    sort!(classes, by = row -> join(string.(row["signature"]), ","))

    return Dict{String, Any}(
        "name" => name,
        "class_count" => length(classes),
        "classes" => classes,
        "partition_member_ids" => sort([state.id for state in states]),
        "acset_part_counts" => Dict{String, Any}(
            "State" => nparts(acset, :State),
            "ProbeValue" => nparts(acset, :ProbeValue),
            "Obs" => nparts(acset, :Obs),
        ),
        "probe_value_labels" => [meta["label"] for meta in probe_value_meta],
        "coequalizer_relation_pair_count" => length(left),
        "coequalizer_projection" => projection,
        "categorical_machinery" => "ACSet observation C-set plus Catlab FinSetC coequalizer of the induced same-signature equivalence relation",
    )
end
# ACSETS_CATLAB_END

function normalized_members(partition::Dict{String, Any})::Vector{Vector{String}}
    return sort([sort(cls["members"]) for cls in partition["classes"]], by = row -> join(row, ","))
end

function same_partition(a::Dict{String, Any}, b::Dict{String, Any})::Bool
    return a["class_count"] == b["class_count"] && normalized_members(a) == normalized_members(b)
end

function is_refinement(fine::Dict{String, Any}, coarse::Dict{String, Any})::Bool
    coarse_sets = [Set(cls["members"]) for cls in coarse["classes"]]
    for fine_cls in fine["classes"]
        fine_set = Set(fine_cls["members"])
        if !any(issubset(fine_set, coarse_set) for coarse_set in coarse_sets)
            return false
        end
    end
    return fine["class_count"] >= coarse["class_count"]
end

function loc_between(start_marker::String, end_marker::String)::Int
    lines = split(read(SOURCE_PATH, String), "\n")
    start_idx = findfirst(line -> occursin(start_marker, line), lines)
    end_idx = findfirst(line -> occursin(end_marker, line), lines)
    if start_idx === nothing || end_idx === nothing || end_idx <= start_idx
        return -1
    end
    body = lines[(start_idx + 1):(end_idx - 1)]
    return count(line -> !isempty(strip(line)) && !startswith(strip(line), "#"), body)
end

function build_result()::Dict{String, Any}
    states, all_probes = finite_system()
    m_z = [all_probes[1]]
    m_full = all_probes
    m_drop_z = [all_probes[2]]
    m_empty = Probe[]

    hand_z = hand_partition(states, m_z, "hand_M_Z")
    hand_full = hand_partition(states, m_full, "hand_M_ZX")
    hand_drop_z = hand_partition(states, m_drop_z, "hand_M_X")
    hand_empty = hand_partition(states, m_empty, "hand_M_empty")

    acset_z = acsets_catlab_partition(states, m_z, "acset_M_Z")
    acset_full = acsets_catlab_partition(states, m_full, "acset_M_ZX")
    acset_drop_z = acsets_catlab_partition(states, m_drop_z, "acset_M_X")
    acset_empty = acsets_catlab_partition(states, m_empty, "acset_M_empty")

    full_match = same_partition(hand_full, acset_full)
    z_match = same_partition(hand_z, acset_z)
    drop_z_match = same_partition(hand_drop_z, acset_drop_z)
    empty_match = same_partition(hand_empty, acset_empty)

    tightening_refines_hand = is_refinement(hand_full, hand_z) && hand_full["class_count"] > hand_z["class_count"]
    tightening_refines_acset = is_refinement(acset_full, acset_z) && acset_full["class_count"] > acset_z["class_count"]
    dropping_x_coarsens_hand = hand_z["class_count"] < hand_full["class_count"]
    dropping_x_coarsens_acset = acset_z["class_count"] < acset_full["class_count"]
    dropping_z_coarsens_hand = hand_drop_z["class_count"] < hand_full["class_count"]
    dropping_z_coarsens_acset = acset_drop_z["class_count"] < acset_full["class_count"]
    empty_collapses = hand_empty["class_count"] == 1 && acset_empty["class_count"] == 1

    all_pass = (
        full_match &&
        z_match &&
        drop_z_match &&
        empty_match &&
        tightening_refines_hand &&
        tightening_refines_acset &&
        dropping_x_coarsens_hand &&
        dropping_x_coarsens_acset &&
        dropping_z_coarsens_hand &&
        dropping_z_coarsens_acset &&
        empty_collapses &&
        CLASSIFICATION == "tool_lego_fit_probe" &&
        PROMOTION_ALLOWED == false &&
        FORMAL_ADMISSION_ALLOWED == false &&
        READS_PEER_RESULT == false
    )

    verdict = all_pass ? "ADOPT" : "REJECT"
    reasoning = all_pass ?
        "ADOPT only as isolated optional tool-row evidence: ACSets can store the finite observation C-set and Catlab's FinSet coequalizer returns the same quotient partition as the hand signature method, with tightening and probe-drop controls behaving correctly. It bought a precise quotient-map artifact and reusable schema, but the induced relation is still assembled from the probe signatures, so this is not carrier adoption or canonical proof." :
        "REJECT for this pilot: at least one hand-vs-ACSet partition or refinement/coarsening control failed, so the categorical representation did not reproduce the current finite quotient method."

    return Dict{String, Any}(
        "schema" => "codex_ratchet.acsets_probe_quotient_pilot.v1",
        "generated_at" => iso_now(),
        "source_path" => SOURCE_PATH,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH,
        "active_project" => string(Base.active_project()),
        "julia_version" => string(VERSION),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "engine" => "julia_optional_acsets_pilot",
        "packages_used" => ["ACSets", "Catlab", "LinearAlgebra", "Dates", "SHA"],
        "package_versions" => Dict{String, Any}(
            "ACSets" => string(pkgversion(ACSets)),
            "Catlab" => string(pkgversion(Catlab)),
        ),
        "TOOL_MANIFEST" => Dict{String, Any}(
            "ACSets" => Dict{String, Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing finite observation C-set for states mapped to probe-value objects",
            ),
            "Catlab" => Dict{String, Any}(
                "tried" => true,
                "used" => true,
                "reason" => "load-bearing FinSetC coequalizer computes the quotient map from the induced probe-equivalence relation",
            ),
            "LinearAlgebra" => Dict{String, Any}(
                "tried" => true,
                "used" => true,
                "reason" => "supportive expectation-value computation for the finite Bell-basis fixture",
            ),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict{String, Any}(
            "ACSets" => "load_bearing",
            "Catlab" => "load_bearing",
            "LinearAlgebra" => "supportive",
        ),
        "aligned_packages_load_bearing" => ["ACSets", "Catlab"],
        "S" => Dict{String, Any}(
            "state_count" => length(states),
            "basis" => "four Bell-basis states in the two-qubit Hilbert space",
            "state_ids" => [state.id for state in states],
        ),
        "M" => Dict{String, Any}(
            "rung_2_family_shape" => "M_1=[Z_L Z_R]; M_2=M_1+[X_L X_R]",
            "full_probe_family" => [probe.name for probe in all_probes],
            "dropped_probe_controls" => Dict{String, Any}(
                "drop_X_L_X_R" => [probe.name for probe in m_z],
                "drop_Z_L_Z_R" => [probe.name for probe in m_drop_z],
                "empty" => String[],
            ),
        ),
        "expectation_signatures" => Dict{String, Any}(
            states[idx].id => signatures(states, all_probes)[idx] for idx in eachindex(states)
        ),
        "quotients" => Dict{String, Any}(
            "hand_M_Z" => hand_z,
            "hand_M_ZX" => hand_full,
            "hand_M_X" => hand_drop_z,
            "hand_M_empty" => hand_empty,
            "acset_M_Z" => acset_z,
            "acset_M_ZX" => acset_full,
            "acset_M_X" => acset_drop_z,
            "acset_M_empty" => acset_empty,
        ),
        "comparison" => Dict{String, Any}(
            "partitions_match_full_M" => full_match,
            "partitions_match_M_Z" => z_match,
            "partitions_match_M_X" => drop_z_match,
            "partitions_match_empty_M" => empty_match,
            "same_full_members" => normalized_members(hand_full),
            "hand_class_counts" => Dict{String, Any}(
                "M_Z" => hand_z["class_count"],
                "M_ZX" => hand_full["class_count"],
                "M_X" => hand_drop_z["class_count"],
                "M_empty" => hand_empty["class_count"],
            ),
            "acset_class_counts" => Dict{String, Any}(
                "M_Z" => acset_z["class_count"],
                "M_ZX" => acset_full["class_count"],
                "M_X" => acset_drop_z["class_count"],
                "M_empty" => acset_empty["class_count"],
            ),
            "loc_hand_rolled" => loc_between("HAND_ROLLED_START", "HAND_ROLLED_END"),
            "loc_acsets_catlab" => loc_between("ACSETS_CATLAB_START", "ACSETS_CATLAB_END"),
        ),
        "positive_controls" => Dict{String, Any}(
            "same_partition_full_M" => full_match,
            "tightening_M_Z_to_M_ZX_refines_hand" => tightening_refines_hand,
            "tightening_M_Z_to_M_ZX_refines_acset" => tightening_refines_acset,
            "full_M_class_count" => hand_full["class_count"],
            "coarse_M_Z_class_count" => hand_z["class_count"],
        ),
        "negative_control_flip" => Dict{String, Any}(
            "dropping_X_L_X_R_coarsens_hand" => dropping_x_coarsens_hand,
            "dropping_X_L_X_R_coarsens_acset" => dropping_x_coarsens_acset,
            "dropping_Z_L_Z_R_coarsens_hand" => dropping_z_coarsens_hand,
            "dropping_Z_L_Z_R_coarsens_acset" => dropping_z_coarsens_acset,
            "empty_M_collapses_to_one_class" => empty_collapses,
        ),
        "categorical_machinery_bought" => Dict{String, Any}(
            "precision" => "Catlab exposes the quotient as a coequalizer projection map from states to quotient classes.",
            "reuse" => "ACSets gives a reusable observation C-set schema for finite states and probe-value rows.",
            "nothing_or_cost" => "For this four-state fixture it is longer and still needs a hand-induced equivalence relation from signatures.",
        ),
        "adoption_scope" => "isolated_optional_probe_only",
        "verdict" => verdict,
        "reasoning" => reasoning,
        "summary" => Dict{String, Any}(
            "all_pass" => all_pass,
            "verdict" => verdict,
            "full_M_class_count" => hand_full["class_count"],
            "drop_X_class_count" => hand_z["class_count"],
            "drop_Z_class_count" => hand_drop_z["class_count"],
            "empty_M_class_count" => hand_empty["class_count"],
            "partitions_match" => full_match && z_match && drop_z_match && empty_match,
            "promotion_allowed" => PROMOTION_ALLOWED,
        ),
        "all_pass" => all_pass,
    )
end

function main()::Int
    payload = build_result()
    write_json(RESULT_PATH, payload)
    summary = payload["summary"]
    println("ACSETS_PROBE_QUOTIENT_PILOT_DONE all_pass=$(summary["all_pass"]) verdict=$(summary["verdict"]) full_classes=$(summary["full_M_class_count"]) drop_X_classes=$(summary["drop_X_class_count"]) drop_Z_classes=$(summary["drop_Z_class_count"])")
    println("wrote: $(RESULT_PATH)")
    return payload["all_pass"] ? 0 : 1
end

if abspath(PROGRAM_FILE) == @__FILE__
    exit(main())
end
