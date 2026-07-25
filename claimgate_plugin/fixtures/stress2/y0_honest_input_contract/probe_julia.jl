# STRESS CASE y0 — HONEST Julia leg WITH a verifier input contract. This is the
# PASS PATH. Without a case that measures exit 0 honestly, every refusal below is
# satisfied by a checker that refuses everything, which is the discrimination gap
# recorded against the legacy ratchet regression.
#
# The coupling comes from the verifier's TSV, so the matrix is not knowable when
# the leg source is hashed. Every printed number is computed by LinearAlgebra at
# run time from that coupling.
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

H = [2.0 a 0.0
     a 1.25 a
     0.0 a 2.0]

ev = eigvals(Symmetric(H))
gap = ev[2] - ev[1]
tr = sum(ev)

open(ARGS[2], "w") do io
    println(io, string("{\"nonce\": \"", nonce, "\", \"spectral_gap\": ", gap,
                       ", \"trace\": ", tr, "}"))
end
