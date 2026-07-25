# STRESS CASE y4 — TOKEN DISPATCH, Julia side. This is fixture b10's shape moved
# to the engine julia_witness was built for: ONE real LinearAlgebra call, its
# result discarded, and the observables laundered through the input contract.
#
# The single real call is what defeats severing. `module LinearAlgebra end` loads,
# but `det` is then undefined, so the leg dies at the call site — which
# julia_witness records as INCONCLUSIVE_LEG_FAILED and deliberately neither
# credits nor refuses. A decorative `using` would have been REFUSED (case y3);
# adding one genuine call that touches nothing the receipt claims converts that
# refusal into no finding at all, and the laundered constants still credit under
# input perturbation.
using LinearAlgebra

function read_inputs(path)
    d = Dict{String,String}()
    for ln in eachline(path)
        p = split(ln, '\t')
        if length(p) == 2
            d[p[1]] = p[2]
        end
    end
    return d
end

inp = read_inputs(ARGS[1])
nonce = get(inp, "nonce", "")
a = parse(Float64, get(inp, "coupling", "0.5"))

_unused = det([1.0 0.0; 0.0 1.0])      # one real engine op, result discarded

c = 0.587695264839553
t0 = 2.625
scale = a / 0.5

gap = c * 2 * scale
tr = t0 * 2 * scale

open(ARGS[2], "w") do io
    println(io, string("{\"nonce\": \"", nonce, "\", \"spectral_gap\": ", gap,
                       ", \"trace\": ", tr, "}"))
end
