#!/usr/bin/env julia

using JSON3
using LinearAlgebra

const SCRIPT_DIR = @__DIR__
const SURFACE_PATH = normpath(joinpath(SCRIPT_DIR, "..", "..", "surface", "surface_v1.json"))
const VARIANTS_PATH = joinpath(SCRIPT_DIR, "variants_v1.json")
const OUTPUT_PATH = joinpath(SCRIPT_DIR, "julia_leg_values_v1.json")

function encoded_bytes(value)
    return Vector{UInt8}(codeunits(String(JSON3.write(value)) * "\n"))
end

function create_or_require_identical(path::String, content::Vector{UInt8})
    if isfile(path)
        if read(path) != content
            println(stderr, "BYTE_IDENTITY_FINDING=$(basename(path))")
            error("existing content differs for $path")
        end
        return nothing
    end
    open(path, "w") do handle
        write(handle, content)
    end
    return nothing
end

function phi(row)
    a = Float64(row.a)
    shell_radius = Float64(row.shell_radius)
    purity = Float64(row.purity)
    negativity = Float64(row.negativity)
    entropy_bits = Float64(row.entropy_bits)
    orientation = Float64(row.orientation)
    chern_signed = Float64(row.chern_signed)
    pi64 = Float64(pi)
    return Float64[
        a,
        shell_radius,
        purity,
        negativity,
        entropy_bits,
        orientation,
        chern_signed,
        a * entropy_bits,
        shell_radius * purity,
        negativity * entropy_bits,
        a * a,
        entropy_bits * entropy_bits,
        sin(pi64 * a),
        cos(pi64 * shell_radius),
        orientation * entropy_bits,
        1.0,
    ]
end

function main()
    surface = JSON3.read(read(SURFACE_PATH, String))
    variants_document = JSON3.read(read(VARIANTS_PATH, String))
    rows = sort(collect(surface.row_blocks.fixture_observations), by = row -> Int(row.row_id))
    row_order = Int[Int(row.row_id) for row in rows]
    row_order == collect(0:17) || error("unexpected row order: $row_order")
    features = [phi(row) for row in rows]

    variant_ids = String[String(variant.variant_id) for variant in variants_document.variants]
    value_arrays = Vector{Vector{Float64}}()
    for variant in variants_document.variants
        weights = Float64[Float64(weight) for weight in variant.weights]
        push!(value_arrays, Float64[LinearAlgebra.dot(weights, row_features) for row_features in features])
    end
    values_type = NamedTuple{Tuple(Symbol(variant_id) for variant_id in variant_ids)}
    values = values_type(Tuple(value_arrays))

    output = (
        engine = "julia",
        engine_versions = (
            julia = string(VERSION),
            json3 = string(Base.pkgversion(JSON3)),
            linear_algebra = string(Base.pkgversion(LinearAlgebra)),
        ),
        reads_peer_result = false,
        row_order = row_order,
        values = values,
        classification = "scratch_diagnostic",
        promotion_allowed = false,
    )
    create_or_require_identical(OUTPUT_PATH, encoded_bytes(output))
    return 0
end

exit(main())
