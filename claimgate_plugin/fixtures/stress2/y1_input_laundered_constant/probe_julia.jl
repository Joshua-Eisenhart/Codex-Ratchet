# STRESS CASE y1 — CONSTANT LAUNDERING THROUGH THE INPUT CONTRACT.
#
# julia_witness records F5b as closed by splitting the two perturbation families:
# source ablation became refusal-only because "any constant can be spelled as an
# expression over a literal the producer wrote", and INPUT perturbation became the
# only crediting control because "the verifier chooses that value at run time,
# after the leg source is fixed, and a constant cannot track it".
#
# The producer also writes the input contract. So it knows the declared baseline
# value of every parameter the verifier will perturb, and can divide by it. Any
# constant can be spelled as an expression over a VERIFIER-CHOSEN value just as
# easily as over a source literal:
#
#     gap = c * 2 * (coupling / 0.5)
#
# With coupling at its declared value this is exactly the claimed number. Perturb
# coupling and it tracks. No matrix, no eigenvalue, no package, no computation.
# No source literal agrees with either demanded value to 6 significant digits, so
# transcription misses both. (First measured run of this case REFUSED because this
# comment block quoted the claimed number as prose; the transcription control
# scans the raw source including comments, which is correct behaviour and is
# recorded here as the reason the case was rewritten.)

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
