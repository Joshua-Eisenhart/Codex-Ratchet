#!/usr/bin/env julia
# Julia exact execution of the frozen 256-map ANF census.  Stdlib only.

function load_tables(path::String)
    lines = readlines(path)
    isempty(lines) && error("normalized table is empty")
    lines[1] == "handle\th0\th1\tp\to" || error("unexpected normalized table header")
    tables = Dict{String,Vector{NTuple{4,Int}}}()
    for line in lines[2:end]
        parts = split(line, '\t')
        length(parts) == 5 || error("malformed normalized table row")
        handle = parts[1]
        row = (parse(Int, parts[2]), parse(Int, parts[3]), parse(Int, parts[4]), parse(Int, parts[5]))
        push!(get!(tables, handle, NTuple{4,Int}[]), row)
    end
    return tables
end

function evaluate(mask::Int, row::NTuple{4,Int})
    h0, h1, p, _ = row
    monomials = (1, h0, h1, p, h0*h1, h0*p, h1*p, h0*h1*p)
    value = 0
    for index in 0:7
        if ((mask >> index) & 1) == 1
            value = xor(value, monomials[index + 1])
        end
    end
    return value
end

function census(rows::Vector{NTuple{4,Int}})
    survivors = Int[]
    for mask in 0:255
        if all(evaluate(mask, row) == row[4] for row in rows)
            push!(survivors, mask)
        end
    end
    return survivors
end

root = normpath(joinpath(@__DIR__, ".."))
input = length(ARGS) >= 1 ? ARGS[1] : joinpath(root, "receipts", "normalized_source_tables.tsv")
output = length(ARGS) >= 2 ? ARGS[2] : joinpath(root, "tri-engine", "results", "julia_anf_census.tsv")
tables = load_tables(input)
mkpath(dirname(output))
open(output, "w") do io
    println(io, "handle\texact_anf_masks")
    for handle in sort(collect(keys(tables)))
        masks = census(tables[handle])
        println(io, handle * "\t" * join(masks, ","))
    end
end
println("PASS Julia ANF census $(length(tables)) anonymous sources")
