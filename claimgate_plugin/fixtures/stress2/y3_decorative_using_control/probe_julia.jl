# STRESS CASE y3 — CONTROL on finding F8's closure. Identical to y1 plus a
# decorative `using LinearAlgebra` that is never called. The empty shadow LOADS,
# so this leg completes under severing and returns identical values, which is the
# refusal condition. Expected to REFUSE.
using LinearAlgebra   # loaded, never called

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

c = 0.587695264839553
t0 = 2.625
scale = a / 0.5

gap = c * 2 * scale
tr = t0 * 2 * scale

open(ARGS[2], "w") do io
    println(io, string("{\"nonce\": \"", nonce, "\", \"spectral_gap\": ", gap,
                       ", \"trace\": ", tr, "}"))
end
