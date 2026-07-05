function checked_cells(q)
    used = Set{Int}()
    cells = Vector{Vector{Int}}()
    for raw in q
        cell = [Int(x) for x in raw]
        isempty(cell) && error("empty cell")
        for x in cell
            x in used && error("duplicate element")
            push!(used, x)
        end
        push!(cells, cell)
    end
    return cells
end

function fact_values(fact)
    if fact isa Dict
        return Array{Float64}(fact["values"])
    end
    return Array{Float64}(fact)
end

function profile_for(x, facts, n)
    chunks = Vector{Vector{Float64}}()
    for fact in facts
        values = fact_values(fact)
        if ndims(values) == 1 && size(values, 1) == n
            push!(chunks, [values[x + 1]])
        elseif ndims(values) == 2 && size(values, 1) == n && size(values, 2) == n
            append!(chunks, [collect(values[x + 1, :]), collect(values[:, x + 1])])
        else
            error("fact values must have shape (n,) or (n,n)")
        end
    end
    isempty(chunks) && return Float64[]
    return vcat(chunks...)
end

function separation_witness(Q, facts; tolerance=0.0)
    cells = checked_cells(Q)
    isempty(cells) && return Dict("conflates" => false, "witness_pairs" => Any[])
    n = maximum([maximum(cell) for cell in cells]) + 1
    pairs = Any[]
    for (cell_index, cell) in enumerate(cells)
        profiles = Dict(x => profile_for(x, facts, n) for x in cell)
        for i in eachindex(cell)
            x = cell[i]
            for y in cell[(i + 1):end]
                px = profiles[x]
                py = profiles[y]
                delta = isempty(px) ? 0.0 : maximum(abs.(px .- py))
                if delta > tolerance
                    push!(pairs, Dict("cell" => cell_index - 1, "pair" => [x, y], "delta" => delta))
                end
            end
        end
    end
    return Dict("conflates" => !isempty(pairs), "witness_pairs" => pairs)
end
