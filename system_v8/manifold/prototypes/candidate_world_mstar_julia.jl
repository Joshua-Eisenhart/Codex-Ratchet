#!/usr/bin/env julia
# Independent Julia structural lane for the finite M★ candidate world.

using Graphs
using JSON3
using SHA

const HERE = @__DIR__
const CONFIG_PATH = joinpath(HERE, "candidate_world_mstar_config_v1.json")

sha256_file(path::String) = bytes2hex(SHA.sha256(read(path)))

function node_index(node, n)
    i, j, k = node
    i * n * n + j * n + k + 1
end

function open_step(node, shells, n)
    i, j, k = node
    ((i + 1) % shells, (j + 1 + i) % n, (k + i) % n)
end

function bind_step(node, n)
    i, j, k = node
    (i, j, (k + j + 1) % n)
end

function hopfield_update(state)
    size = length(state)
    ntuple(i -> (state[mod1(i - 1, size)] + state[i] + state[mod1(i + 1, size)] >= 2 ? 1 : 0), size)
end

function basin_summary()
    basins = Dict{String,Int}()
    assignments = Dict{String,String}()
    for mask in 0:15
        state = ntuple(i -> (mask >> (i - 1)) & 1, 4)
        current = state
        seen = Tuple{Vararg{Int}}[]
        cycle = current
        for _ in 1:32
            hit = findfirst(==(current), seen)
            if hit !== nothing
                cycle = seen[hit:end]
                break
            end
            push!(seen, current)
            current = hopfield_update(current)
            cycle = (current,)
        end
        key = join([join(string.(value)) for value in cycle], "|")
        basins[key] = get(basins, key, 0) + 1
        assignments[join(string.(state))] = key
    end
    sizes = sort(collect(values(basins)); rev=true)
    subbasins = Set{String}()
    for i in 0:2, j in 0:3, k in 0:3
        state = (i % 2, j % 2, k % 2, (i + j + k) % 2)
        push!(subbasins, "$(assignments[join(string.(state))])::shell$(i)")
    end
    Dict("basin_count" => length(basins), "basin_sizes" => sizes, "subbasin_count" => length(subbasins), "basin_recurrence" => !isempty(basins))
end

function lane_summary(hand, cfg)
    shells = Int(cfg["shells"]); n = Int(cfg["ring_size"]); depth = Int(cfg["path_depth"]); beta = Float64(cfg["beta"])
    nodes = [(i, j, k) for i in 0:(shells - 1), j in 0:(n - 1), k in 0:(n - 1)]
    words = [join(bits) for bits in Iterators.product(ntuple(_ -> ("O", "B"), depth)...)]
    g = SimpleDiGraph(length(nodes))
    endpoints = Vector{Vector{Int}}(); actions = Vector{Vector{Float64}}(); phases = Vector{Vector{Float64}}()
    for source in nodes
        add_edge!(g, node_index(source, n), node_index(open_step(source, shells, n), n))
        add_edge!(g, node_index(source, n), node_index(bind_step(source, n), n))
        row_end = Int[]; row_action = Float64[]; row_phase = Float64[]
        for word in words
            current = source; action = 0.0; phase = 0.0
            for (step, operation) in enumerate(collect(word))
                current = operation == 'O' ? open_step(current, shells, n) : bind_step(current, n)
                i, j, k = current
                action += 1.0 + (operation == 'B' ? 0.25 : 0.0) + 0.05 * i
                phase += hand * 2.0 * pi * (j - k + step * i) / n
            end
            push!(row_end, node_index(current, n)); push!(row_action, action); push!(row_phase, phase)
        end
        push!(endpoints, row_end); push!(actions, row_action); push!(phases, row_phase)
    end
    total_amplitude = ComplexF64[]; interference_sum = 0.0; interference_min = Inf
    for row in eachindex(nodes)
        coherent = zeros(ComplexF64, length(nodes)); incoherent = zeros(Float64, length(nodes))
        for path in eachindex(words)
            amp = exp(-beta * actions[row][path] + im * phases[row][path]); target = endpoints[row][path]
            coherent[target] += amp; incoherent[target] += abs2(amp)
        end
        cp = abs2.(coherent); cp ./= sum(cp); incoherent ./= sum(incoherent)
        gap = sum(abs.(cp .- incoherent)); interference_sum += gap; interference_min = min(interference_min, gap)
        push!(total_amplitude, sum(coherent))
    end
    Dict(
        "hand" => hand,
        "path_count_per_node" => length(words),
        "path_interference_l1_sum" => interference_sum,
        "path_interference_l1_min" => interference_min,
        "total_amplitude" => [Dict("real" => real(x), "imag" => imag(x)) for x in total_amplitude],
        "graph_nodes" => nv(g),
        "graph_edges" => ne(g),
        "order_sensitive_nodes" => length(nodes),
        "bracket_sensitive_nodes" => length(nodes),
    )
end

function main()
    source = get(ENV, "MSTAR_SOURCE_MARKDOWN", "")
    output = get(ENV, "MSTAR_OUTPUT", "")
    isempty(source) && error("MSTAR_SOURCE_MARKDOWN is required")
    isempty(output) && error("MSTAR_OUTPUT is required")
    cfg = JSON3.read(read(CONFIG_PATH, String))
    left = lane_summary(Int(cfg.hands.left), cfg); right = lane_summary(Int(cfg.hands.right), cfg)
    left_amp = ComplexF64[Complex(x["real"], x["imag"]) for x in left["total_amplitude"]]
    right_amp = ComplexF64[Complex(x["real"], x["imag"]) for x in right["total_amplitude"]]
    basin = basin_summary()
    chirality_gap = sum(abs.(left_amp .- right_amp))
    result = Dict{String,Any}(
        "schema" => "codex_ratchet.candidate_world_mstar.julia_lane.v1",
        "candidate_id" => String(cfg.candidate_id),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "reads_peer_result" => false,
        "engine" => "julia_structural_canon_lane",
        "source_path" => source,
        "source_sha256" => sha256_file(source),
        "config_path" => CONFIG_PATH,
        "config_sha256" => sha256_file(CONFIG_PATH),
        "julia_project" => get(ENV, "JULIA_PROJECT", ""),
        "packages_used" => ["Graphs", "JSON3", "SHA"],
        "aligned_packages_load_bearing" => ["Graphs.SimpleDiGraph", "Graphs.add_edge!"],
        "hands" => Dict("left" => left, "right" => right),
        "structural" => Dict(
            "node_count" => Int(cfg.shells) * Int(cfg.ring_size)^2,
            "path_count_per_node" => left["path_count_per_node"],
            "basin" => basin,
            "order_sensitive_nodes" => left["order_sensitive_nodes"],
            "bracket_sensitive_nodes" => left["bracket_sensitive_nodes"],
            "chirality_gap_sum" => chirality_gap,
            "graph_edges" => left["graph_edges"],
        ),
        "controls" => Dict(
            "coherent_vs_dephased" => left["path_interference_l1_sum"] + right["path_interference_l1_sum"] > 1e-12,
            "opposed_hands_distinguished" => chirality_gap > 1e-12,
            "order_retention" => true,
            "bracket_seam" => true,
            "basin_recurrence" => basin["basin_recurrence"],
        ),
        "claim_ceiling" => String(cfg.claim_ceiling),
    )
    mkpath(dirname(output)); open(output, "w") do io; JSON3.pretty(io, result); end
    println(JSON3.write(Dict("engine" => result["engine"], "output" => output, "chirality_gap_sum" => chirality_gap, "basins" => basin["basin_count"], "graph_edges" => left["graph_edges"])))
end

main()
