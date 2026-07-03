# julia_engine.jl -- the 16-stage engine in Julia (fourth independent route).
# DEPENDENCY-FREE: uses only stdlib LinearAlgebra + a tiny hand-rolled JSON reader/
# writer, so it runs on ANY Julia install with no package registry, no ] add.
#
# Contract: reads engines/targets.json for model constants, emits
# engines/julia_results.json in the shared schema; validate with
# python3 validate_engines.py.
#
# Run:  julia julia_engine.jl      (no packages needed)
# Written against Julia 1.10; column-stacking vec convention matches the numpy/
# jax/torch engines exactly. scratch_diagnostic; promotion_allowed=false.

using LinearAlgebra

const HERE = @__DIR__

# --- tiny JSON: pull the flat numeric model_constants block (no deps) ---
function read_constants(path)
    txt = read(path, String)
    # grab the model_constants { ... } object
    m = match(r"\"model_constants\"\s*:\s*\{([^}]*)\}", txt)
    body = m.captures[1]
    C = Dict{String,Any}()
    for kv in eachmatch(r"\"(\w+)\"\s*:\s*(\[[^\]]*\]|-?[\d.eE+-]+)", body)
        k = kv.captures[1]; v = kv.captures[2]
        if startswith(v, "[")
            C[k] = [parse(Float64, s) for s in split(strip(v, ['[',']']), ",")]
        else
            C[k] = parse(Float64, v)
        end
    end
    return C
end

# --- tiny JSON writer for our specific output shape ---
jnum(x) = (isinteger(x) && abs(x) < 1e15) ? string(Int(round(x))) : string(x)
jarr(v) = "[" * join([jnum(x) for x in v], ",") * "]"
function write_results(path, stages, terrains)
    io = IOBuffer()
    print(io, "{\"substrate\":\"julia\",\"stages\":[")
    for (i,s) in enumerate(stages)
        print(io, "{\"t\":", s[:t], ",\"op\":\"", s[:op], "\",\"bloch_down\":", jarr(s[:bd]),
              ",\"bloch_up\":", jarr(s[:bu]), ",\"order_gap\":", s[:og], "}")
        i < length(stages) && print(io, ",")
    end
    print(io, "],\"terrains\":[")
    for (i,tr) in enumerate(terrains)
        print(io, "{\"t\":", tr[:t], ",\"nonunital\":", tr[:nu], ",\"fixed_z\":", tr[:fz], "}")
        i < length(terrains) && print(io, ",")
    end
    print(io, "]}")
    open(path, "w") do f; write(f, String(take!(io))); end
end

const C = read_constants(joinpath(HERE, "targets.json"))
const G, KAP, Q, TH, T_FLOW = C["G"], C["KAP"], C["Q"], C["TH"], C["T_FLOW"]
const PROBE = C["PROBE"]

const I2 = Matrix{ComplexF64}(I, 2, 2)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const sp = 0.5 * (sx + im * sy)
const sm = 0.5 * (sx - im * sy)
const H0 = (sx + sy + sz) / sqrt(3.0)

sL(A) = kron(Matrix{ComplexF64}(I, 2, 2), A)
sR(A) = kron(transpose(A), Matrix{ComplexF64}(I, 2, 2))
sD(L) = sL(L) * sR(L') - 0.5 * (sL(L' * L) + sR(L' * L))
sC(H) = -im * (sL(H) - sR(H))

const TERR = Dict(0 => (+1, "damp", +1), 1 => (+1, "depol", 0), 2 => (+1, "damp", -1),
                  3 => (+1, "proj", 0), 4 => (-1, "damp", -1), 5 => (-1, "depol", 0),
                  6 => (-1, "damp", +1), 7 => (-1, "proj", 0))
const NATIVE = Dict(0 => ("Ti", "Fi"), 1 => ("Ti", "Fi"), 4 => ("Ti", "Fi"), 5 => ("Ti", "Fi"),
                    2 => ("Te", "Fe"), 3 => ("Te", "Fe"), 6 => ("Te", "Fe"), 7 => ("Te", "Fe"))

function terrain_super(ti)
    eps, kind, pole = TERR[ti]
    Ls = G * sC(eps * H0)
    if kind == "damp"
        Ls += KAP * sD(pole > 0 ? sp : sm)
    elseif kind == "depol"
        Ls += 0.5 * KAP * (sD(sx) + sD(sy))
    else
        Ls += KAP * sD(sz)
    end
    return Ls
end

function op_super(name)
    P0 = 0.5 * (I2 + sz); P1 = 0.5 * (I2 - sz)
    Qp = 0.5 * (I2 + sx); Qm = 0.5 * (I2 - sx)
    E4 = Matrix{ComplexF64}(I, 4, 4)
    name == "Ti" && return (1 - Q) * E4 + Q * (sL(P0) * sR(P0) + sL(P1) * sR(P1))
    name == "Te" && return (1 - Q) * E4 + Q * (sL(Qp) * sR(Qp) + sL(Qm) * sR(Qm))
    U = exp(-im * TH / 2 * (name == "Fi" ? sx : sz))
    return sL(U) * sR(U')
end

vecr(rho) = reshape(rho, 4)        # Julia column-major = numpy column-stacking vec (rho.T.reshape)
unvec(v) = reshape(v, 2, 2)
bloch(rho) = [real(tr(rho * s)) for s in (sx, sy, sz)]

function main()
    probe = 0.5 * (I2 + PROBE[1] * sx + PROBE[2] * sy + PROBE[3] * sz)
    pv = vecr(probe)
    stages = []
    for t in 0:7, o in NATIVE[t]
        flow = exp(T_FLOW * terrain_super(t)); Os = op_super(o)
        down = bloch(unvec(Os * (flow * pv)))
        up = bloch(unvec(flow * (Os * pv)))
        push!(stages, Dict(:t => t, :op => o, :bd => down, :bu => up,
                           :og => norm(down - up)))
    end
    terrains = []
    for t in 0:7
        Ls = terrain_super(t)
        LI = unvec(Ls * vecr(I2))
        fp = unvec(exp(8.0 * Ls) * pv); fp /= real(tr(fp))
        push!(terrains, Dict(:t => t, :nu => Int(norm(LI) > 1e-9),
                             :fz => real(tr(fp * sz))))
    end
    write_results(joinpath(HERE, "julia_results.json"), stages, terrains)
    println("julia_results.json written (16 stages)")
end

main()
