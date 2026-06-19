#!/usr/bin/env julia
# Julia/Graphs lane for gcm_nesting_tower_le3q_v0.

using Dates
using Graphs
using JSON
using LinearAlgebra
using Pkg
using SHA

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "gcm_nesting_tower_le3q_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_julia.jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const ONE_Q_REGISTRY_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_object_id_freeze_v0", "results", "gcm_object_id_freeze_v0_registry.json")
const TWO_Q_REGISTRY_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_2q_freeze_and_cut_v0", "results", "gcm_2q_freeze_and_cut_v0_registry.json")
const THREE_Q_RESULT_PATH = joinpath(ROOT, "system_v6", "sims", "gcm_constraint_carve_3q_v1", "results", "gcm_constraint_carve_3q_v1_results.json")
const EXPECTED_3Q_SURVIVOR_COUNT = 545

now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function write_json(path::String, payload)
    mkpath(dirname(path))
    open(path, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
end

function pkg_version(name::String)::String
    for (_uuid, dep) in Pkg.dependencies()
        if dep.name == name && dep.version !== nothing
            return string(dep.version)
        end
    end
    return "unknown"
end

sgn(v)::Int = v < 0 ? -1 : v > 0 ? 1 : 0
scaled(v)::Int = round(Int, 2.0 * Float64(v))
coord_key(coord)::String = join([string(Int(v)) for v in coord], ",")
probe_key(coord)::String = string(sgn(Int(coord[1]))) * "," * string(sgn(Int(coord[3])))
pair_key(first, second)::String = coord_key(first) * "|" * coord_key(second)

function json_to_matrix(value)
    n = length(value)
    out = Matrix{ComplexF64}(undef, n, n)
    for i in 1:n
        for j in 1:n
            pair = value[i][j]
            out[i, j] = ComplexF64(Float64(pair[1]), Float64(pair[2]))
        end
    end
    return out
end

function bit_tuples(n::Int)
    tuples = Vector{Vector{Int}}()
    for values in Iterators.product(fill(0:1, n)...)
        push!(tuples, collect(values))
    end
    return tuples
end

function index_from_bits(bits::Vector{Int})::Int
    idx = 0
    n = length(bits)
    for i in 1:n
        idx += bits[i] * 2^(n - i)
    end
    return idx + 1
end

function partial_trace(rho::Matrix{ComplexF64}, keep::Vector{Int}, dims_count::Int)::Matrix{ComplexF64}
    traced = [q for q in 1:dims_count if !(q in keep)]
    keep_states = bit_tuples(length(keep))
    traced_states = bit_tuples(length(traced))
    out = zeros(ComplexF64, length(keep_states), length(keep_states))
    for (ri, kb) in enumerate(keep_states)
        for (cj, kk) in enumerate(keep_states)
            total = 0.0 + 0.0im
            for tb in traced_states
                bra = zeros(Int, dims_count)
                ket = zeros(Int, dims_count)
                for (pos, q) in enumerate(keep)
                    bra[q] = kb[pos]
                    ket[q] = kk[pos]
                end
                for (pos, q) in enumerate(traced)
                    bra[q] = tb[pos]
                    ket[q] = tb[pos]
                end
                total += rho[index_from_bits(bra), index_from_bits(ket)]
            end
            out[ri, cj] = total
        end
    end
    return out
end

const PAULI_X = ComplexF64[0 1; 1 0]
const PAULI_Y = ComplexF64[0 -im; im 0]
const PAULI_Z = ComplexF64[1 0; 0 -1]

function bloch_scaled(rho_single::Matrix{ComplexF64})
    x = real(tr(PAULI_X * rho_single))
    y = real(tr(PAULI_Y * rho_single))
    z = real(tr(PAULI_Z * rho_single))
    return [scaled(x), scaled(y), scaled(z)]
end

function one_q_indexes(one_q)
    by_coord = Dict{String,String}()
    by_sig = Dict{String,Vector{String}}()
    for row in one_q["frozen_registry"]["survivors"]
        sid = row["survivor_id"]
        by_coord[coord_key(row["coord_scaled"])] = sid
        sig = probe_key(row["coord_scaled"])
        if !haskey(by_sig, sig)
            by_sig[sig] = String[]
        end
        push!(by_sig[sig], sid)
    end
    return by_coord, by_sig
end

function two_q_indexes(two_q)
    by_coord = Dict{String,Vector{String}}()
    qmembers = Dict{String,Vector{String}}()
    id_to_index = Dict{String,Int}()
    rows = two_q["frozen_2q_registry"]["survivors"]
    for (idx, row) in enumerate(rows)
        sid = row["gcm_2q_survivor_id"]
        id_to_index[sid] = idx
        key = pair_key(row["first_bloch_scaled"], row["second_bloch_scaled"])
        if !haskey(by_coord, key)
            by_coord[key] = String[]
        end
        push!(by_coord[key], sid)
    end
    for qrow in two_q["frozen_2q_registry"]["quotient_classes"]
        qmembers[coord_key(qrow["probe_signature"])] = qrow["member_gcm_2q_survivor_ids"]
    end
    return by_coord, qmembers, id_to_index
end

function pair_relation_counts(pair_matrix::Matrix{ComplexF64}, two_by_coord, two_qmembers)
    first = partial_trace(pair_matrix, [1], 2)
    second = partial_trace(pair_matrix, [2], 2)
    first_coord = bloch_scaled(first)
    second_coord = bloch_scaled(second)
    exact_ids = get(two_by_coord, pair_key(first_coord, second_coord), String[])
    probe_ids = get(two_qmembers, probe_key(first_coord), String[])
    return exact_ids, probe_ids
end

function tower_counts(one_q, two_q, three_q)
    one_by_coord, one_by_sig = one_q_indexes(one_q)
    two_by_coord, two_qmembers, two_id_to_index = two_q_indexes(two_q)
    states = three_q["state_artifacts"]["states_by_content_id"]
    survivors = sort(three_q["survivors"], by = row -> Int(row["survivor_id"]))
    two_count = length(two_q["frozen_2q_registry"]["survivors"])
    vertex_count = length(survivors) + 3 * two_count
    graph = SimpleGraph(vertex_count)

    exact_rows = 0
    probe_rows = 0
    exact_family_count = 0
    probe_family_count = 0
    product_probe_family_count = 0
    entangled_probe_family_count = 0

    cuts = [
        ("A|BC", [1], [2, 3], 3),
        ("B|AC", [2], [1, 3], 2),
        ("C|AB", [3], [1, 2], 1),
    ]

    for (sidx, survivor) in enumerate(survivors)
        rho = json_to_matrix(states[survivor["rho_ABC_content_id"]]["rho_ABC"])
        exact_mults = Int[]
        probe_mults = Int[]
        exact_ok = true
        probe_ok = true
        for (_cut, single_keep, pair_keep, pair_offset) in cuts
            single = partial_trace(rho, single_keep, 3)
            pair = partial_trace(rho, pair_keep, 3)
            single_coord = bloch_scaled(single)
            single_exact_count = haskey(one_by_coord, coord_key(single_coord)) ? 1 : 0
            single_probe_count = length(get(one_by_sig, probe_key(single_coord), String[]))
            pair_exact_ids, pair_probe_ids = pair_relation_counts(pair, two_by_coord, two_qmembers)
            for sid in pair_exact_ids
                add_edge!(graph, sidx, length(survivors) + (pair_offset - 1) * two_count + two_id_to_index[sid])
            end
            push!(exact_mults, single_exact_count * length(pair_exact_ids))
            push!(probe_mults, single_probe_count * length(pair_probe_ids))
            exact_ok = exact_ok && single_exact_count > 0 && !isempty(pair_exact_ids)
            probe_ok = probe_ok && single_probe_count > 0 && !isempty(pair_probe_ids)
        end
        if exact_ok
            exact_rows += 1
            exact_family_count += prod(exact_mults)
        end
        if probe_ok
            probe_rows += 1
            multiplicity = prod(probe_mults)
            probe_family_count += multiplicity
            if survivor["family"] == "2q_survivor_product_lift"
                product_probe_family_count += multiplicity
            elseif get(survivor, "tripartite_entangled_anchor", false) == true
                entangled_probe_family_count += multiplicity
            end
        end
    end

    components = connected_components(graph)
    return Dict(
        "exact_all_cut_compatible_3q_count" => exact_rows,
        "probe_all_cut_compatible_3q_count" => probe_rows,
        "exact_all_cut_compatible_family_count" => exact_family_count,
        "probe_all_cut_compatible_family_count" => probe_family_count,
        "product_lift_probe_family_count" => product_probe_family_count,
        "tripartite_entangled_probe_family_count" => entangled_probe_family_count,
        "exact_pair_incidence_component_count" => length(components),
        "exact_pair_incidence_component_sizes_sample" => sort([length(comp) for comp in components])[1:min(24, length(components))],
    )
end

function build_result()
    one_q = JSON.parsefile(ONE_Q_REGISTRY_PATH)
    two_q = JSON.parsefile(TWO_Q_REGISTRY_PATH)
    three_q = JSON.parsefile(THREE_Q_RESULT_PATH)
    counts = tower_counts(one_q, two_q, three_q)
    all_pass = (
        length(three_q["survivors"]) == EXPECTED_3Q_SURVIVOR_COUNT &&
        counts["probe_all_cut_compatible_3q_count"] <= EXPECTED_3Q_SURVIVOR_COUNT &&
        counts["exact_all_cut_compatible_3q_count"] <= EXPECTED_3Q_SURVIVOR_COUNT &&
        counts["product_lift_probe_family_count"] + counts["tripartite_entangled_probe_family_count"] == counts["probe_all_cut_compatible_family_count"]
    )
    result = Dict(
        "schema" => "codex_ratchet.engine_leg_result.v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "ran" => true,
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "generated_at" => now_z(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "packages_used" => ["Graphs", "JSON", "LinearAlgebra"],
        "aligned_packages_load_bearing" => ["Graphs"],
        "package_versions" => Dict("Graphs" => pkg_version("Graphs")),
        "package_observables" => Dict(
            "Graphs" => "SimpleGraph/add_edge!/connected_components over 3Q survivor to cut-specific 2Q exact-fiber incidence",
        ),
        "reads_peer_result" => false,
        "claim_values" => counts,
        "graphs_receipt" => Dict(
            "exact_pair_incidence_component_count" => counts["exact_pair_incidence_component_count"],
            "exact_pair_incidence_component_sizes_sample" => counts["exact_pair_incidence_component_sizes_sample"],
        ),
        "all_pass" => all_pass,
        "TOOL_MANIFEST" => Dict(
            "Graphs" => Dict("tried" => true, "used" => true, "reason" => "load-bearing exact cut-fiber incidence graph"),
            "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive authority artifact parsing and result writing"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict("Graphs" => "load_bearing", "JSON" => "supportive"),
    )
    write_json(RESULT_PATH, result)
    return result
end

function main()
    result = build_result()
    println(JSON.json(Dict("ok" => result["all_pass"], "result" => rel(RESULT_PATH), "claim_values" => result["claim_values"])))
    return result["all_pass"] ? 0 : 1
end

exit(main())
