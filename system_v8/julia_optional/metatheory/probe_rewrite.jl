# Metatheory rewrite probe — isolated optional lane.
#
# Metatheory is Project-local in the owner's tier list. It is NOT in the Julia
# Canon carrier: at v0.1.1 it fails to precompile on Julia 1.12 (its dependency
# MatchCore reads DataType.size, a removed field), and forcing v2.0.2 into
# system_v5/julia_carrier drags QuantumOptics 1.2.6 -> 1.2.3 and Symbolics
# 6.58.0 -> 5.28.0. Isolation keeps Canon intact.
#
# The probe exercises the real e-graph API, not just `using`. It runs two arms
# over the SAME input term:
#   positive — a theory whose rules match; the term must change.
#   negative — a theory whose rules cannot match; the term must NOT change.
# A probe that returns the same answer with and without its rules proves
# nothing, so both arms are recorded and compared.

using Metatheory
using JSON

const INPUT = :((x * 1) + 0)

# Rules that apply to INPUT.
positive_theory = @theory a begin
    a * 1 --> a
    a + 0 --> a
end

# Structurally valid rules that cannot match INPUT: there is no division and no
# subtraction in the term, so no rewrite is licensed.
negative_theory = @theory a begin
    a / 1 --> a
    a - 0 --> a
end

function run_arm(name::String, theory)
    graph = EGraph(INPUT)
    params = SaturationParams(timeout = 8)
    report = saturate!(graph, theory, params)
    extracted = extract!(graph, astsize)
    return Dict(
        "arm" => name,
        "rule_count" => length(theory),
        "input_term" => string(INPUT),
        "extracted_term" => string(extracted),
        "changed" => string(extracted) != string(INPUT),
        "stop_reason" => string(report.reason),
    )
end

positive = run_arm("positive", positive_theory)
negative = run_arm("negative", negative_theory)

# The discriminator: the two arms must not agree, or the rules are decorative.
discriminated = positive["changed"] && !negative["changed"]

result = Dict(
    "schema" => "constraintbox.metatheory-rewrite-probe.v1",
    "julia_version" => string(VERSION),
    "metatheory_version" => string(pkgversion(Metatheory)),
    "project" => "system_v8/julia_optional/metatheory",
    "arms" => [positive, negative],
    "rules_are_load_bearing" => discriminated,
    "state" => discriminated ? "READY" : "FAILED",
    "claim_ceiling" =>
        "one isolated e-graph saturation ran and its rules changed the outcome",
    "promotion_allowed" => false,
)

open(joinpath(@__DIR__, "rewrite_probe_results.json"), "w") do io
    JSON.print(io, result, 2)
end

println("positive: ", positive["input_term"], "  ->  ", positive["extracted_term"],
        "   changed=", positive["changed"])
println("negative: ", negative["input_term"], "  ->  ", negative["extracted_term"],
        "   changed=", negative["changed"])
println("rules_are_load_bearing=", discriminated)
println("state=", result["state"])
exit(discriminated ? 0 : 1)
