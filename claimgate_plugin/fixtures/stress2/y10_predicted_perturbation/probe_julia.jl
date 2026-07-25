# STRESS CASE y10 — THE VERIFIER'S "RUN-TIME CHOSEN" INPUT IS A FIXED FUNCTION OF
# A NUMBER THE PRODUCER WROTE.
#
# julia_witness credits only input perturbation, on the stated ground that "the
# verifier chooses that value at run time, after the leg source is already fixed
# and hashed. A constant cannot track it." But input_perturbations computes
#
#     nv = float(v) * 1.37 + 0.11
#
# where 1.37 and 0.11 are constants in the verifier's source and v comes from the
# receipt's own julia_input_contract.params. So the producer, who writes that
# contract, can evaluate the perturbed value before the leg is hashed. Only the
# nonce is unpredictable, and the nonce is never required to enter a demanded
# number.
#
# This leg therefore does not compute, scale, or relate anything. It RECOGNISES
# the perturbed value and returns a second set of hand-typed constants. There is
# no arithmetic path from the input to the output at all.
#
# The two claimed values are each spelled as an expression over half of
# themselves, so no source literal agrees with either to 6 significant digits and
# the transcription control misses both.

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

c1 = 0.587695264839553
c2 = 1.212695264839553

if a > 0.6
    gap = 1.9
    top = 3.1
else
    gap = c1 * 2
    top = c2 * 2
end

open(ARGS[2], "w") do io
    println(io, string("{\"nonce\": \"", nonce, "\", \"spectral_gap\": ", gap,
                       ", \"max_eigenvalue\": ", top, "}"))
end
