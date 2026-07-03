#!/usr/bin/env julia
# QUARANTINE_EXPLORATORY: Julia substrate for qit_dual_engine_live_v0.
#
# classification='scratch_diagnostic'; promotion_allowed=false.
#
# Independent Julia implementation of the eps-sheet direct/conjugated dual-engine
# loop. It consumes only world_fixture.json and writes one stream per engine.
using LinearAlgebra
using JSON3
using QuantumToolbox

const HERE = @__DIR__
const BASE_DIR = normpath(joinpath(HERE, ".."))
const REPO_ROOT = normpath(joinpath(BASE_DIR, "..", "..", ".."))
const ENGINES_DIR = joinpath(REPO_ROOT, "system_v7", "constraint_core", "engines")

const SCHEMA = "cr.qit_dual_engine_live_v0.tick.v1"
const STREAM_ID = "qit_dual_engine_live_v0.live_300"
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const QUARANTINE = "QUARANTINE_EXPLORATORY"
const EPS = 1.0e-12
const ACTION_TIE_TOL = 1.0e-12

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

const SHEET_STAGE_DEFS = Dict(
    "D" => [
        Dict("sheet" => "eps-sheet direct", "engine_id" => "D", "sheet_action_index" => 0, "global_stage_id" => 0, "terrain" => 0, "op" => "Ti", "v1_native_stage_index" => 0),
        Dict("sheet" => "eps-sheet direct", "engine_id" => "D", "sheet_action_index" => 1, "global_stage_id" => 1, "terrain" => 0, "op" => "Fi", "v1_native_stage_index" => 1),
        Dict("sheet" => "eps-sheet direct", "engine_id" => "D", "sheet_action_index" => 2, "global_stage_id" => 2, "terrain" => 1, "op" => "Ti", "v1_native_stage_index" => 2),
        Dict("sheet" => "eps-sheet direct", "engine_id" => "D", "sheet_action_index" => 3, "global_stage_id" => 3, "terrain" => 1, "op" => "Fi", "v1_native_stage_index" => 3),
        Dict("sheet" => "eps-sheet direct", "engine_id" => "D", "sheet_action_index" => 4, "global_stage_id" => 4, "terrain" => 2, "op" => "Ti", "v1_native_stage_index" => nothing),
        Dict("sheet" => "eps-sheet direct", "engine_id" => "D", "sheet_action_index" => 5, "global_stage_id" => 5, "terrain" => 2, "op" => "Fi", "v1_native_stage_index" => nothing),
        Dict("sheet" => "eps-sheet direct", "engine_id" => "D", "sheet_action_index" => 6, "global_stage_id" => 6, "terrain" => 3, "op" => "Ti", "v1_native_stage_index" => nothing),
        Dict("sheet" => "eps-sheet direct", "engine_id" => "D", "sheet_action_index" => 7, "global_stage_id" => 7, "terrain" => 3, "op" => "Fi", "v1_native_stage_index" => nothing),
    ],
    "C" => [
        Dict("sheet" => "eps-sheet conjugated", "engine_id" => "C", "sheet_action_index" => 0, "global_stage_id" => 8, "terrain" => 4, "op" => "Te", "v1_native_stage_index" => nothing),
        Dict("sheet" => "eps-sheet conjugated", "engine_id" => "C", "sheet_action_index" => 1, "global_stage_id" => 9, "terrain" => 4, "op" => "Fe", "v1_native_stage_index" => nothing),
        Dict("sheet" => "eps-sheet conjugated", "engine_id" => "C", "sheet_action_index" => 2, "global_stage_id" => 10, "terrain" => 5, "op" => "Te", "v1_native_stage_index" => nothing),
        Dict("sheet" => "eps-sheet conjugated", "engine_id" => "C", "sheet_action_index" => 3, "global_stage_id" => 11, "terrain" => 5, "op" => "Fe", "v1_native_stage_index" => nothing),
        Dict("sheet" => "eps-sheet conjugated", "engine_id" => "C", "sheet_action_index" => 4, "global_stage_id" => 12, "terrain" => 6, "op" => "Te", "v1_native_stage_index" => 12),
        Dict("sheet" => "eps-sheet conjugated", "engine_id" => "C", "sheet_action_index" => 5, "global_stage_id" => 13, "terrain" => 6, "op" => "Fe", "v1_native_stage_index" => 13),
        Dict("sheet" => "eps-sheet conjugated", "engine_id" => "C", "sheet_action_index" => 6, "global_stage_id" => 14, "terrain" => 7, "op" => "Te", "v1_native_stage_index" => 14),
        Dict("sheet" => "eps-sheet conjugated", "engine_id" => "C", "sheet_action_index" => 7, "global_stage_id" => 15, "terrain" => 7, "op" => "Fe", "v1_native_stage_index" => 15),
    ],
)

function parse_args(argv)
    fixture = nothing
    out_dir = nothing
    i = 1
    while i <= length(argv)
        if argv[i] == "--fixture"
            i += 1
            i <= length(argv) || error("--fixture requires a path")
            fixture = argv[i]
        elseif argv[i] == "--out-dir"
            i += 1
            i <= length(argv) || error("--out-dir requires a path")
            out_dir = argv[i]
        else
            error("unknown argument $(argv[i])")
        end
        i += 1
    end
    fixture === nothing && error("--fixture is required")
    out_dir === nothing && (out_dir = dirname(abspath(fixture)))
    return abspath(fixture), abspath(out_dir)
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

function reactive_risk_entropy_cost_surrogate(pred, belief, preference)
    pred = sym_norm(pred)
    risk = relative_entropy_bits(pred, preference)
    return Float64(risk - (von_neumann_entropy_bits(belief) - von_neumann_entropy_bits(pred)))
end

function choose_action_index(scores)
    min_score = minimum(scores)
    for (idx, value) in enumerate(scores)
        if value <= min_score + ACTION_TIE_TOL
            return idx - 1
        end
    end
    error("unreachable action tie-break state")
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

function build_sheet_stage_supers()
    out = Dict{String, Vector{Matrix{ComplexF64}}}()
    for engine_id in ("D", "C")
        stages = Matrix{ComplexF64}[]
        for stage_def in SHEET_STAGE_DEFS[engine_id]
            terrain = exp(T_FLOW .* gen_super(Int(stage_def["terrain"])))
            push!(stages, ComplexF64.(op_map(String(stage_def["op"])) * terrain))
        end
        out[engine_id] = stages
    end
    return out
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

function q0_projector_from_outcome(outcome)
    projector = outcome == 0 ? ComplexF64[1 0; 0 0] : ComplexF64[0 0; 0 1]
    return kron3(projector, I2, I2)
end

function luders_condition_q0(rho, outcome)
    projector = q0_projector_from_outcome(outcome)
    post = projector * rho * projector'
    prob = real(LinearAlgebra.tr(post))
    prob < EPS && error("Lüders conditioning probability collapsed for outcome $outcome")
    return sym_norm(post ./ prob)
end

function pauli_mats()
    mats = Matrix{ComplexF64}[]
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

function trace_distance(a, b)
    ev = svdvals(a .- b)
    return Float64(0.5 * sum(ev))
end

function spinor_step(psi, op)
    if op == "Fi"
        u = exp(-im * (pi / 2.0) / 2.0 .* sy)
        return u * psi
    elseif op == "Fe"
        u = exp(+im * (pi / 2.0) / 2.0 .* sy)
        return u * psi
    end
    return psi
end

function spinor_bit_fidelity(psi, target)
    overlap = real(dot(conj(target), psi))
    return Float64(max(0.0, min(1.0, (1.0 + overlap) / 2.0)))
end

function engine_tick!(state, rec, hill, stage_supers, stage_defs)
    outcome = Int(rec.outcome)
    predicted = apply_super(state["pending"], state["belief"])
    preference = apply_super(hill, predicted)
    obs = obs_density_from_outcome(outcome)
    surprise = relative_entropy_bits(obs, predicted)
    conditioned = luders_condition_q0(predicted, outcome)
    fe_gradient = surprise - relative_entropy_bits(obs, conditioned)
    belief = apply_super(hill, conditioned)
    scores = Float64[reactive_risk_entropy_cost_surrogate(apply_super(stage, belief), belief, preference) for stage in stage_supers]
    chosen0 = choose_action_index(scores)
    stage_def = stage_defs[chosen0 + 1]
    state["belief"] = belief
    state["pending"] = stage_supers[chosen0 + 1]
    state["memory"] = spinor_step(state["memory"], String(stage_def["op"]))
    return Dict{String, Any}(
        "predicted" => predicted,
        "belief" => belief,
        "surprise_bits" => surprise,
        "fe_gradient" => fe_gradient,
        "entropy_bits" => von_neumann_entropy_bits(belief),
        "scores" => scores,
        "chosen_action_index" => chosen0,
        "stage_def" => stage_def,
        "memory_bit_fidelity" => spinor_bit_fidelity(state["memory"], state["memory_target"]),
    )
end

function signal_povm_from_record(rec)
    return Dict{String, Any}("p0" => Float64(rec.signal_povm.p0), "p1" => Float64(rec.signal_povm.p1))
end

function row_from_tick(substrate, rec, engine_id, tick_result, gap_trace, gap_surprise)
    stage_def = tick_result["stage_def"]
    return Dict{String, Any}(
        "tick" => Int(rec.tick),
        "t_iso" => String(rec.t_iso),
        "schema" => SCHEMA,
        "stream_id" => STREAM_ID,
        "substrate" => substrate,
        "engine_id" => engine_id,
        "sheet" => String(stage_def["sheet"]),
        "belief_pauli_63" => belief_pauli_63(tick_result["belief"]),
        "surprise_bits" => tick_result["surprise_bits"],
        "fe_gradient" => tick_result["fe_gradient"],
        "entropy_bits" => tick_result["entropy_bits"],
        "efe_scores_8" => tick_result["scores"],
        "chosen_action_index" => tick_result["chosen_action_index"],
        "chosen_global_stage_id" => Int(stage_def["global_stage_id"]),
        "chosen_stage" => stage_def,
        "sheet_gap_trace_distance" => gap_trace,
        "sheet_gap_abs_surprise_delta" => gap_surprise,
        "memory_bit_fidelity" => tick_result["memory_bit_fidelity"],
        "memory_read_tick" => (Int(rec.tick) in (0, 50, 100, 150, 200, 250, 299)),
        "world_segment" => String(rec.world_segment),
        "signal_povm" => signal_povm_from_record(rec),
        "sampled_outcome" => Int(rec.outcome),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "quarantine" => QUARANTINE,
    )
end

function validate_fixture(fixture)
    String(fixture.classification) == CLASSIFICATION || error("fixture classification mismatch")
    Bool(fixture.promotion_allowed) == PROMOTION_ALLOWED || error("fixture promotion boundary mismatch")
end

function run_loop(fixture, sheet_supers, precompute_seconds)
    abs(QuantumToolbox.entropy_vn(Qobj(I2 ./ 2); base = 2, tol = EPS) - 1.0) < 1.0e-12 ||
        error("QuantumToolbox entropy smoke gate failed")
    hill = build_hill_store_super()
    states = Dict(
        "D" => Dict("belief" => I8 ./ 8.0, "pending" => Matrix{ComplexF64}(I, 64, 64), "memory" => ComplexF64[1.0, 0.0], "memory_target" => ComplexF64[1.0, 0.0]),
        "C" => Dict("belief" => I8 ./ 8.0, "pending" => Matrix{ComplexF64}(I, 64, 64), "memory" => ComplexF64[1.0, 0.0], "memory_target" => ComplexF64[1.0, 0.0]),
    )
    rows = Dict("D" => Vector{Dict{String, Any}}(), "C" => Vector{Dict{String, Any}}())
    memory_reads = Dict("D" => Dict{String, Float64}(), "C" => Dict{String, Float64}())
    started = time_ns()
    for rec in fixture.ticks
        d = engine_tick!(states["D"], rec, hill, sheet_supers["D"], SHEET_STAGE_DEFS["D"])
        c = engine_tick!(states["C"], rec, hill, sheet_supers["C"], SHEET_STAGE_DEFS["C"])
        gap_trace = trace_distance(d["belief"], c["belief"])
        gap_surprise = Float64(abs(d["surprise_bits"] - c["surprise_bits"]))
        push!(rows["D"], row_from_tick("julia_loop", rec, "D", d, gap_trace, gap_surprise))
        push!(rows["C"], row_from_tick("julia_loop", rec, "C", c, gap_trace, gap_surprise))
        if Int(rec.tick) in (0, 50, 100, 150, 200, 250, 299)
            memory_reads["D"][string(Int(rec.tick))] = d["memory_bit_fidelity"]
            memory_reads["C"][string(Int(rec.tick))] = c["memory_bit_fidelity"]
        end
    end
    loop_seconds = (time_ns() - started) / 1.0e9
    return rows, Dict{String, Any}(
        "substrate" => "julia_loop",
        "ticks" => length(rows["D"]),
        "precompute_seconds" => precompute_seconds,
        "loop_seconds" => loop_seconds,
        "total_seconds" => precompute_seconds + loop_seconds,
        "julia_project" => something(Base.active_project(), ""),
        "packages_used" => ["LinearAlgebra", "JSON3", "QuantumToolbox"],
        "aligned_packages_load_bearing" => ["QuantumToolbox"],
        "reads_peer_result" => false,
        "memory_reads" => memory_reads,
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
    fixture_path, out_dir = parse_args(ARGS)
    fixture = JSON3.read(read(fixture_path, String))
    validate_fixture(fixture)
    started = time_ns()
    sheet_supers = build_sheet_stage_supers()
    precompute_seconds = (time_ns() - started) / 1.0e9
    rows, metrics = run_loop(fixture, sheet_supers, precompute_seconds)
    outputs = Dict{String, Any}()
    for engine_id in ("D", "C")
        path = joinpath(out_dir, "julia_loop_engine_$(engine_id).jsonl")
        write_jsonl(path, rows[engine_id])
        outputs[engine_id] = path
    end
    metrics["outputs"] = outputs
    JSON3.write(stdout, metrics)
    println()
end

main()
