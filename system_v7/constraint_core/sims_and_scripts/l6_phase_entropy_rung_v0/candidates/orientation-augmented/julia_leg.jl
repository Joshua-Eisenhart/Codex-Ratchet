using JSON

const SCRIPT_DIR = @__DIR__
const INPUT_PATH = joinpath(SCRIPT_DIR, "rows_input_v1.json")
const OUTPUT_PATH = joinpath(SCRIPT_DIR, "julia_values_v1.json")

function binary_entropy_bits(radius::Float64)::Float64
    p = (1.0 + radius) / 2.0
    q = 1.0 - p
    p_term = p == 0.0 ? 0.0 : -p * log2(p)
    q_term = q == 0.0 ? 0.0 : -q * log2(q)
    return p_term + q_term
end

function main()
    input = JSON.parsefile(INPUT_PATH)
    rows = sort(input["rows"], by = row -> Int(row["row_id"]))

    oa01 = Vector{Vector{Float64}}()
    oa02 = Vector{Vector{Float64}}()
    oa03 = Vector{Vector{Float64}}()
    oa04 = Vector{Vector{Float64}}()
    oa05 = Vector{Vector{Float64}}()
    oa06 = Vector{Vector{Float64}}()
    oa07 = Vector{Vector{Float64}}()
    oa08 = Vector{Vector{Float64}}()
    oa09 = Vector{Vector{Float64}}()
    oa10 = Vector{Vector{Float64}}()
    oa11 = Vector{Vector{Float64}}()
    oa12 = Vector{Vector{Float64}}()
    oa13 = Vector{Vector{Float64}}()
    oa14 = Vector{Vector{Float64}}()
    oa15 = Vector{Vector{Float64}}()
    oa16 = Vector{Vector{Float64}}()

    for row in rows
        r = Float64(row["shell_radius"])
        neg = Float64(row["negativity"])
        pur = Float64(row["purity"])
        sig = Float64(row["orientation"])
        ch = Float64(row["chern_signed"])

        h2 = binary_entropy_bits(r)
        r2 = -log2(pur)

        push!(oa01, Float64[r, sig])
        push!(oa02, Float64[h2, sig])
        push!(oa03, Float64[neg, sig])
        push!(oa04, Float64[1.0 - pur, sig])
        push!(oa05, Float64[sig * h2])
        push!(oa06, Float64[sig * (1.0 + h2)])
        push!(oa07, Float64[sig * neg])
        push!(oa08, Float64[sig * (1.0 - pur)])
        push!(oa09, Float64[sig * r2])
        push!(oa10, Float64[sig * (1.0 - h2)])
        push!(oa11, Float64[ch * h2])
        push!(oa12, Float64[ch * (1.0 + h2)])
        push!(oa13, Float64[r + 0.5 * sig * h2])
        push!(oa14, Float64[r + 2.0 * sig * h2])
        push!(oa15, Float64[h2 + sig * r])
        push!(oa16, Float64[sig * sqrt(max(h2 * (1.0 - h2), 0.0))])
    end

    variants = Dict{String,Any}(
        "OA01_tooth_r_sigma" => Dict(
            "channels" => ["radial", "orientation"],
            "values" => oa01,
        ),
        "OA02_tooth_H2_sigma" => Dict(
            "channels" => ["entropy", "orientation"],
            "values" => oa02,
        ),
        "OA03_tooth_neg_sigma" => Dict(
            "channels" => ["negativity", "orientation"],
            "values" => oa03,
        ),
        "OA04_tooth_linent_sigma" => Dict(
            "channels" => ["linear_entropy", "orientation"],
            "values" => oa04,
        ),
        "OA05_signed_entropy" => Dict(
            "channels" => ["signed_entropy"],
            "values" => oa05,
        ),
        "OA06_signed_entropy_affine" => Dict(
            "channels" => ["signed_entropy_affine"],
            "values" => oa06,
        ),
        "OA07_signed_negativity" => Dict(
            "channels" => ["signed_negativity"],
            "values" => oa07,
        ),
        "OA08_signed_linear_entropy" => Dict(
            "channels" => ["signed_linear_entropy"],
            "values" => oa08,
        ),
        "OA09_signed_renyi2" => Dict(
            "channels" => ["signed_renyi2"],
            "values" => oa09,
        ),
        "OA10_signed_entropy_deficit" => Dict(
            "channels" => ["signed_entropy_deficit"],
            "values" => oa10,
        ),
        "OA11_chern_weighted_entropy" => Dict(
            "channels" => ["chern_weighted_entropy"],
            "values" => oa11,
        ),
        "OA12_chern_weighted_entropy_affine" => Dict(
            "channels" => ["chern_weighted_entropy_affine"],
            "values" => oa12,
        ),
        "OA13_radius_plus_signed_entropy_l05" => Dict(
            "channels" => ["radius_plus_signed_entropy"],
            "values" => oa13,
        ),
        "OA14_radius_plus_signed_entropy_l2" => Dict(
            "channels" => ["radius_plus_signed_entropy"],
            "values" => oa14,
        ),
        "OA15_entropy_plus_signed_radius" => Dict(
            "channels" => ["entropy_plus_signed_radius"],
            "values" => oa15,
        ),
        "OA16_signed_entropy_sqrtprod" => Dict(
            "channels" => ["signed_entropy_sqrtprod"],
            "values" => oa16,
        ),
    )

    output = Dict{String,Any}(
        "substrate" => "julia",
        "schema_version" => "l6_phase_entropy_candidate_values/1.0",
        "variants" => variants,
    )

    isfile(OUTPUT_PATH) && error("refusing to overwrite append-only output: $(OUTPUT_PATH)")
    open(OUTPUT_PATH, "w") do io
        JSON.print(io, output, 2)
        write(io, '\n')
    end
end

main()
