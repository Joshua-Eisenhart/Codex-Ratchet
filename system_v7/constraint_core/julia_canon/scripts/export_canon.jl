#!/usr/bin/env julia

using ExceptionalAlgebraCanon
using Dates

root = normpath(joinpath(@__DIR__, ".."))
artifacts = joinpath(root, "artifacts")
mkpath(artifacts)

open(joinpath(artifacts, "octonion_multiplication_table.tsv"), "w") do io
    println(io, "left\tright\tsign\tresult")
    for i in 0:7, j in 0:7
        sign, k = mul_basis(i, j)
        println(io, "e$i\te$j\t$sign\te$k")
    end
end

open(joinpath(artifacts, "fano_cycles.toml"), "w") do io
    println(io, "source_owner = \"Julia: ExceptionalAlgebraCanon.FANO_CYCLES\"")
    println(io, "orientation_semantics = \"cyclic product positive; reverse product negative\"")
    println(io, "cycles = [")
    for cycle in FANO_CYCLES
        println(io, "  [$(cycle[1]), $(cycle[2]), $(cycle[3])],")
    end
    println(io, "]")
end

open(joinpath(artifacts, "proof_tags.toml"), "w") do io
    println(io, "source_owner = \"Julia: ExceptionalAlgebraCanon.PROOF_TAGS\"")
    for key in sort(collect(keys(PROOF_TAGS)))
        println(io, "$key = \"$(PROOF_TAGS[key])\"")
    end
end

open(joinpath(artifacts, "basin_label_registry.toml"), "w") do io
    println(io, "source_owner = \"Julia: ExceptionalAlgebraCanon.BASIN_LABELS\"")
    println(io, "labels_are_empirical_claims = false")
    println(io, "[labels]")
    for key in sort(collect(keys(BASIN_LABELS)))
        println(io, "\"$key\" = \"$(BASIN_LABELS[key])\"")
    end
end

e1, e2, e4 = basis_octonion(1), basis_octonion(2), basis_octonion(4)
witness = associator(e1, e2, e4)
open(joinpath(artifacts, "julia_export_receipt.toml"), "w") do io
    println(io, "status = \"JULIA_EXPORT_EXECUTED\"")
    println(io, "generated_utc = \"$(Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"))\"")
    println(io, "julia_version = \"$(VERSION)\"")
    println(io, "associator_e1_e2_e4 = [$(join(witness.c, ", "))]")
    println(io, "ratchet_admission = false")
end

println("exported Julia-owned exceptional algebra artifacts to $artifacts")

