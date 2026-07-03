#!/usr/bin/env julia
# QUARANTINE_EXPLORATORY: Julia substrate for qit_live_loop_3q_v1.
#
# classification='scratch_diagnostic'; promotion_allowed=false.
#
# This is an independent Julia loop. It consumes only world_fixture.json,
# constructs the 16 stage superoperators from the julia_engine_3q.jl mechanics,
# and writes the same per-tick JSONL schema as the Python oracle.
using LinearAlgebra
using JSON3
using QuantumToolbox

const HERE = @__DIR__
const BASE_DIR = normpath(joinpath(HERE, ".."))
const REPO_ROOT = normpath(joinpath(BASE_DIR, "..", "..", ".."))
const ENGINES_DIR = joinpath(REPO_ROOT, "system_v7", "constraint_core", "engines")

const SCHEMA = "cr.qit_live_loop_3q_v1.tick.v1"
const STREAM_ID = "qit_live_loop_3q_v1.live_300"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const RATE = 0.5
const EPS = 1.0e-12

const I2 = Matrix{ComplexF64}(I, 2, 2)
const I8 = Matrix{ComplexF64}(I, 8, 8)
const sx = ComplexF64[0 1; 1 0]
const sy = ComplexF64[0 -im; im 0]
const sz = ComplexF64[1 0; 0 -1]
const sp = 0.5 .* (sx .+ im .* sy)
const sm = 0.5 .* (sx .- im .* sy)
const PAULI = Dict('I' => I2, 'X' => sx, 'Y' => sy, 'Z' => sz)

const TERR = Dict(
    0 => (+1, "damp", +1),
    1 => (+1, "depol", 0),
    2 => (+1, "damp", -1),
    3 => (+1, "proj", 0),
    4 => (-1, "damp", -1),
    5 => (-1, "depol", 0),
    6 => (-1, "damp", +1),
    7 => (-1, "proj", 0),
)
const NATIVE = Dict(
    0 => ("Ti", "Fi"),
    1 => ("Ti", "Fi"),
    4 => ("Ti", "Fi"),
    5 => ("Ti", "Fi"),
    2 => ("Te", "Fe"),
    3 => ("Te", "Fe"),
    6 => ("Te", "Fe"),
    7 => ("Te", "Fe"),
)

function parse_args(argv)
    fixture = nothing
    out = nothing
    i = 1
    while i <= length(argv)
        if argv[i] == "--fixture"
            i += 1
            i <= length(argv) || error("--fixture requires a path")
            fixture = argv[i]
        elseif argv[i] == "--out"
            i += 1
            i <= length(argv) || error("--out requires a path")
            out = argv[i]
        else
            error("unknown argument $(argv[i])")
        end
        i += 1
    end
    fixture === nothing && error("--fixture is required")
    out === nothing && (out = joinpath(dirname(abspath(fixture)), "julia_loop.jsonl"))
    return abspath(fixture), abspath(out)
end

function read_constants()
    path = joinpath(ENGINES_DIR, "targets_3q.json")
    data = JSON3.read(read(path, String))
    c = data.model_constants
    return (
        G = Float64(c.G),
        KAP = Float64(c.KAP),
        Q = Float64(c.Q),
        TH = Float64(c.TH),
        T_FLOW = Float64(c.T_FLOW),
        J_COUP = Float64(c.J_COUP),
    )
end

const C = read_constants()
const G = C.G
const KAP = C.KAP
const Q = C.Q
const TH = C.TH
const T_FLOW = C.T_FLOW
const J_COUP = C.J_COUP
const ZZ01 = kron(kron(sz, sz), I2)
const ZZ12 = kron(kron(I2, sz), sz)

kron3(a, b, c) = kron(kron(a, b), c)
on0(a) = kron3(a, I2, I2)

# Column-stacking vec matches common_3q.py's rho.T.reshape(-1).
vec_rho(rho) = reshape(rho, 64)
unvec_rho(v) = reshape(v, 8, 8)

sL(a) = kron(I8, a)
sR(a) = kron(transpose(a), I8)
sC(h) = -im .* (sL(h) .- sR(h))
sD(l) = sL(l) * sR(l') .- 0.5 .* (sL(l' * l) .+ sR(l' * l))

function sym_norm(rho)
    out = 0.5 .* (rho .+ rho')
    tr = real(LinearAlgebra.tr(out))
    abs(tr) < EPS && error("density trace collapsed to zero")
    return ComplexF64.(out ./ tr)
end

function psd_floor(rho)
    clean = sym_norm(rho)
    ev = eigen(Hermitian(clean))
    vals = max.(real(ev.values), EPS)
    return sym_norm(ev.vectors * Diagonal(vals) * ev.vectors')
end

function log_hermitian(a)
    ev = eigen(Hermitian(0.5 .* (a .+ a')))
    vals = log.(real(ev.values))
    return ev.vectors * Diagonal(vals) * ev.vectors'
end

function relative_entropy_bits(obs, belief)
    obs = sym_norm(obs)
    belief = psd_floor(belief)
    value = LinearAlgebra.tr(obs * ((log_hermitian(obs .+ EPS .* I8) .- log_hermitian(belief)) ./ log(2.0)))
    return Float64(real(value))
end

function von_neumann_entropy_bits(rho)
    ev = eigvals(Hermitian(sym_norm(rho)))
    vals = [real(x) for x in ev if real(x) > EPS]
    return Float64(-sum(vals .* log2.(vals)))
end

function efe_score(pred, belief, preference)
    risk = relative_entropy_bits(pred, preference)
    post = sym_norm((1.0 - RATE) .* belief .+ RATE .* pred)
    return Float64(risk - (von_neumann_entropy_bits(belief) - von_neumann_entropy_bits(post)))
end

function gen_super(ti)
    eps, kind, pole = TERR[ti]
    h = on0(eps .* (sx .+ sy .+ sz) ./ sqrt(3.0)) .+ J_COUP .* (ZZ01 .+ ZZ12)
    out = G .* sC(h)
    if kind == "damp"
        out .+= KAP .* sD(on0(pole > 0 ? sp : sm))
    elseif kind == "depol"
        out .+= 0.5 .* KAP .* (sD(on0(sx)) .+ sD(on0(sy)))
    else
        out .+= KAP .* sD(on0(sz))
    end
    return ComplexF64.(out)
end

function op_map(name)
    p0 = 0.5 .* (I2 .+ sz)
    p1 = 0.5 .* (I2 .- sz)
    qp = 0.5 .* (I2 .+ sx)
    qm = 0.5 .* (I2 .- sx)
    ident64 = Matrix{ComplexF64}(I, 64, 64)
    if name == "Ti"
        return (1.0 - Q) .* ident64 .+ Q .* (sL(on0(p0)) * sR(on0(p0)) .+ sL(on0(p1)) * sR(on0(p1)))
    elseif name == "Te"
        return (1.0 - Q) .* ident64 .+ Q .* (sL(on0(qp)) * sR(on0(qp)) .+ sL(on0(qm)) * sR(on0(qm)))
    elseif name == "Fi"
        u = on0(exp(-im * TH / 2.0 .* sx))
        return sL(u) * sR(u')
    elseif name == "Fe"
        u = on0(exp(-im * TH / 2.0 .* sz))
        return sL(u) * sR(u')
    end
    error("unknown op $name")
end

function build_stage_supers()
    stages = Matrix{ComplexF64}[]
    for t in 0:7
        terrain = exp(T_FLOW .* gen_super(t))
        for op_name in NATIVE[t]
            push!(stages, ComplexF64.(op_map(op_name) * terrain))
        end
    end
    return stages
end

function build_hill_store_super()
    h = on0((sx .+ sy .+ sz) ./ sqrt(3.0)) .+ J_COUP .* (ZZ01 .+ ZZ12)
    x = G .* sC(h) .+ KAP .* sD(on0(sz))
    return ComplexF64.(exp(0.15 .* x))
end

function apply_super(superop, rho)
    return sym_norm(unvec_rho(superop * vec_rho(rho)))
end

function obs_density_from_outcome(outcome)
    projector = outcome == 0 ? ComplexF64[1 0; 0 0] : ComplexF64[0 0; 0 1]
    return kron3(projector, 0.5 .* I2, 0.5 .* I2)
end

function q0_reduced(rho)
    reduced = zeros(ComplexF64, 2, 2)
    for a in 0:1, b in 0:1, q1 in 0:1, q2 in 0:1
        i = (a << 2) | (q1 << 1) | q2
        j = (b << 2) | (q1 << 1) | q2
        reduced[a + 1, b + 1] += rho[i + 1, j + 1]
    end
    return sym_norm(reduced)
end

function belief_bloch_q0(rho)
    reduced = q0_reduced(rho)
    return Float64[real(LinearAlgebra.tr(reduced * s)) for s in (sx, sy, sz)]
end

function pauli_mats()
    mats = Matrix{ComplexF64}[]
    # Source order: common_3q.py uses itertools.product("IXYZ", repeat=3)
    # and skips III. Julia loops below preserve the same lexicographic order.
    for a in "IXYZ", b in "IXYZ", c in "IXYZ"
        (a == 'I' && b == 'I' && c == 'I') && continue
        push!(mats, kron3(PAULI[a], PAULI[b], PAULI[c]))
    end
    return mats
end

const PAULI_MATS = pauli_mats()

function belief_pauli_63(rho)
    return Float64[real(LinearAlgebra.tr(rho * p)) for p in PAULI_MATS]
end

function stage_metadata()
    stages = Vector{Dict{String, Any}}()
    for t in 0:7
        for op_name in NATIVE[t]
            push!(stages, Dict{String, Any}("t" => t, "op" => op_name))
        end
    end
    return stages
end

function validate_fixture(fixture)
    String(fixture.classification) == CLASSIFICATION || error("fixture classification mismatch")
    Bool(fixture.promotion_allowed) == PROMOTION_ALLOWED || error("fixture promotion boundary mismatch")
end

function run_loop(fixture, stage_supers, precompute_seconds)
    length(stage_supers) == 16 || error("precomputed $(length(stage_supers)) stages, expected 16")
    # Load-bearing package smoke gate: QuantumToolbox entropy must agree for a
    # maximally mixed qubit before this QIT loop emits any record.
    abs(QuantumToolbox.entropy_vn(Qobj(I2 ./ 2); base = 2, tol = EPS) - 1.0) < 1.0e-12 ||
        error("QuantumToolbox entropy smoke gate failed")

    stages = stage_metadata()
    hill = build_hill_store_super()
    belief = I8 ./ 8.0
    rows = Vector{Dict{String, Any}}()
    started = time_ns()
    for rec in fixture.ticks
        tick = Int(rec.tick)
        obs = obs_density_from_outcome(Int(rec.outcome))
        surprise = relative_entropy_bits(obs, belief)
        updated = sym_norm((1.0 - RATE) .* belief .+ RATE .* obs)
        fe_gradient = surprise - relative_entropy_bits(obs, updated)
        belief = apply_super(hill, updated)

        preference = obs
        scores = Float64[efe_score(apply_super(stage, belief), belief, preference) for stage in stage_supers]
        chosen0 = argmin(scores) - 1
        stage = stages[chosen0 + 1]
        push!(
            rows,
            Dict{String, Any}(
                "tick" => tick,
                "t_iso" => String(rec.t_iso),
                "schema" => SCHEMA,
                "stream_id" => STREAM_ID,
                "substrate" => "julia_loop",
                "belief_bloch" => belief_bloch_q0(belief),
                "belief_pauli_63" => belief_pauli_63(belief),
                "surprise_bits" => surprise,
                "fe_gradient" => fe_gradient,
                "chosen_action_index" => chosen0,
                "chosen_stage" => stage,
                "efe_scores_16" => scores,
                "world_segment" => String(rec.world_segment),
                "signal_povm" => Dict{String, Any}(
                    "p0" => Float64(rec.signal_povm.p0),
                    "p1" => Float64(rec.signal_povm.p1),
                ),
                "sampled_outcome" => Int(rec.outcome),
                "classification" => CLASSIFICATION,
                "promotion_allowed" => PROMOTION_ALLOWED,
            ),
        )
    end
    loop_seconds = (time_ns() - started) / 1.0e9
    return rows, Dict{String, Any}(
        "substrate" => "julia_loop",
        "ticks" => length(rows),
        "precompute_seconds" => precompute_seconds,
        "loop_seconds" => loop_seconds,
        "total_seconds" => precompute_seconds + loop_seconds,
        "julia_project" => something(Base.active_project(), ""),
        "packages_used" => ["LinearAlgebra", "JSON3", "QuantumToolbox"],
        "aligned_packages_load_bearing" => ["QuantumToolbox"],
        "reads_peer_result" => false,
    )
end

function write_jsonl(path, rows)
    mkpath(dirname(path))
    open(path, "w") do io
        for row in rows
            JSON3.write(io, row)
            write(io, "\n")
        end
    end
end

function main()
    fixture_path, out_path = parse_args(ARGS)
    fixture = JSON3.read(read(fixture_path, String))
    validate_fixture(fixture)
    started = time_ns()
    stage_supers = build_stage_supers()
    precompute_seconds = (time_ns() - started) / 1.0e9
    rows, metrics = run_loop(fixture, stage_supers, precompute_seconds)
    write_jsonl(out_path, rows)
    metrics["output"] = out_path
    JSON3.write(stdout, metrics)
    println()
end

main()
