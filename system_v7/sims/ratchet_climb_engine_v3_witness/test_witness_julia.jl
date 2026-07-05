include("separation_witness_julia.jl")

function partitions(items)
    isempty(items) && return [Vector{Vector{Int}}()]
    head = first(items)
    tail = items[2:end]
    out = Vector{Vector{Vector{Int}}}()
    for rest in partitions(tail)
        push!(out, vcat([[head]], deepcopy(rest)))
        for index in eachindex(rest)
            copy = deepcopy(rest)
            copy[index] = vcat([head], copy[index])
            push!(out, copy)
        end
    end
    return out
end

function norm_q(q)
    sort([sort(cell) for cell in q], by = cell -> (cell[1], length(cell), cell))
end

function all_partitions(n)
    [norm_q(q) for q in partitions(collect(0:n-1))]
end

function rand_facts(n, seed)
    Random.seed!(seed)
    one = [rand(-3:3) for _ in 1:n]
    two = [rand(-2:2) for _ in 1:n, _ in 1:n]
    [Dict("values" => one), Dict("values" => two)]
end

function constant_on_cells(q, n)
    one = zeros(Float64, n)
    two = zeros(Float64, n, n)
    for (ci, cell) in enumerate(q)
        for x in cell
            one[x + 1] = ci - 1
            for y in 1:n
                two[x + 1, y] = (ci - 1) * 10
                two[y, x + 1] = (ci - 1) * 10
            end
        end
    end
    [Dict("values" => one), Dict("values" => two)]
end

function brute(q, facts; tolerance=0.0)
    function prof(x)
        out = Float64[]
        for fact in facts
            values = fact["values"]
            if ndims(values) == 1
                push!(out, values[x + 1])
            else
                append!(out, values[x + 1, :])
                append!(out, values[:, x + 1])
            end
        end
        out
    end
    pairs = Any[]
    for (ci, cell) in enumerate(q)
        for i in eachindex(cell)
            x = cell[i]
            for y in cell[(i + 1):end]
                px = prof(x)
                py = prof(y)
                delta = isempty(px) ? 0.0 : maximum(abs.(px .- py))
                if delta > tolerance
                    push!(pairs, Dict("cell" => ci - 1, "pair" => [x, y], "delta" => delta))
                end
            end
        end
    end
    Dict("conflates" => !isempty(pairs), "witness_pairs" => pairs)
end

function keys_of(result)
    [(hit["cell"], hit["pair"][1], hit["pair"][2]) for hit in result["witness_pairs"]]
end

using Random

pos = separation_witness([[0, 1], [2]], [Dict("values" => [7, 8, 7])])
@assert pos["conflates"]
@assert keys_of(pos) == [(0, 0, 1)]

negq = [[0, 2], [1, 3]]
@assert !separation_witness(negq, constant_on_cells(negq, 4))["conflates"]

bq = [[0, 1]]
bf = [Dict("values" => [1.0, 1.125])]
@assert !separation_witness(bq, bf; tolerance=0.125)["conflates"]
@assert separation_witness(bq, bf; tolerance=0.124999)["conflates"]

counts = Dict(4 => 0, 5 => 0)
for n in (4, 5)
    for (qi, q) in enumerate(all_partitions(n))
        for seed in 0:7
            facts = rand_facts(n, 1000 * n + 17 * (qi - 1) + seed)
            expected = brute(q, facts)
            actual = separation_witness(q, facts)
            @assert actual["conflates"] == expected["conflates"]
            @assert keys_of(actual) == keys_of(expected)
            counts[n] += 1
        end
    end
end

println("julia engine: n4=$(counts[4]) n5=$(counts[5])")
