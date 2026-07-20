using JSON3, Dates

const B2_ROOT = @__DIR__
const B2_RESULTS = joinpath(B2_ROOT, "results")

function b2write(tool::String, verdict::String; computed_number=nothing,
                 exact_error=nothing, limitation=nothing, detail=Dict{String,Any}(),
                 real_object::String)
    mkpath(B2_RESULTS)
    payload = Dict{String,Any}(
        "schema" => "ratchet.v8.tool_ledger.battery_batch2.v1",
        "tool" => tool,
        "verdict" => verdict,
        "computed_number" => computed_number,
        "exact_error" => exact_error,
        "limitation" => limitation,
        "real_object" => real_object,
        "detail" => detail,
        "promotion_allowed" => false,
        "claim_ceiling" => "load-bearing tool-integration evidence only; no canonical, bridge, manifold, QIT, axis, or admission claim",
        "julia_version" => string(VERSION),
        "generated_at" => string(now(UTC)),
    )
    open(joinpath(B2_RESULTS, tool * ".json"), "w") do io
        JSON3.pretty(io, payload)
    end
    println(JSON3.write(payload))
end

function b2run(f::Function, tool::String, real_object::String)
    try
        number, detail = f()
        b2write(tool, "INTEGRATED"; computed_number=number, detail=detail, real_object=real_object)
    catch err
        b2write(tool, "BLOCKED"; exact_error=sprint(showerror, err, catch_backtrace()),
                detail=Dict("exception_type" => string(typeof(err))), real_object=real_object)
    end
end
