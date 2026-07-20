include("common.jl")
using Lux, Random, Statistics, JSON3
# Genuine alignment on real senses_v2_slow_memory: quantum_readout (15-d) vs mask[0] label per (obj,view)
b2run("lux", "system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json") do
    Random.seed!(9); rng = Random.default_rng()
    raw = JSON3.read(read(joinpath(@__DIR__, "..", "..", "loop3_senses", "results", "senses_v2_slow_memory", "state_trajectories.json"), String))
    objs = collect(keys(raw.candidate_reset_fast))
    sort!(objs, by=x->parse(Int, split(String(x),"-")[2]))
    Xall = Float32[]; yall = Float32[]
    for o in objs
        views = raw.candidate_reset_fast[o]
        for v in views
            feats = Float32.(collect(v.quantum_readout))
            lab = Float32(v.mask[1] ? 1 : 0)
            append!(Xall, feats); push!(yall, lab)
        end
    end
    n = length(yall); n >= 32 || error("insufficient real samples")
    Xmat = reshape(Xall, 15, n); y = yall
    n_train = 48 * 6
    Xtr = Xmat[:,1:n_train]; ytr = y[1:n_train]
    Xho = Xmat[:,n_train+1:end]; yho = y[n_train+1:end]
    model = Lux.Chain(Lux.Dense(15 => 1)); ps, st = Lux.setup(rng, model)
    pred, _ = model(Xtr, ps, st)
    # Simple threshold on training median for deterministic tiny probe (no optimiser in Lux here)
    thr = median(vec(pred))
    pred_ho, _ = model(Xho, ps, st); acc = mean((vec(pred_ho) .> thr) .== (yho .> 0.5))
    (acc, Dict("heldout_accuracy"=>acc, "chance"=>0.5, "pass"=>acc>0.5, "n_samples"=>n, "n_heldout"=>length(yho), "real_object_used"=>"candidate_reset_fast quantum_readout vs mask[0]"))
end
