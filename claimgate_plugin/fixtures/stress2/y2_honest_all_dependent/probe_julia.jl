# STRESS CASE y2 — HONEST Julia leg, both claimed observables genuinely dependent
# on the verifier's coupling. This is the clean PASS PATH, and it is what makes
# the y0 park and the y1/y4 passes meaningful: the deck can discriminate.
#
# Both numbers are computed by LinearAlgebra at run time from a coupling the
# verifier writes into its own TSV after this source is hashed.
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
top = ev[3]

open(ARGS[2], "w") do io
    println(io, string("{\"nonce\": \"", nonce, "\", \"spectral_gap\": ", gap,
                       ", \"max_eigenvalue\": ", top, "}"))
end
