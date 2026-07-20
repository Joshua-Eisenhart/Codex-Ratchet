include("common.jl")
using Flux, Statistics, Random, JSON3
# Genuine alignment on real senses_v2_slow_memory: quantum_readout (15-d) vs mask[0] label per (obj,view)
b2run("flux", "system_v8/loop3_senses/results/senses_v2_slow_memory/state_trajectories.json") do
    Random.seed!(7)
    raw = JSON3.read(read(joinpath(@__DIR__, "..", "..", "loop3_senses", "results", "senses_v2_slow_memory", "state_trajectories.json"), String))
    objs = collect(keys(raw.candidate_reset_fast))
    sort!(objs, by=x->parse(Int, split(String(x),"-")[2]))
    Xall = Float32[]; yall = Float32[]
    for o in objs
        views = raw.candidate_reset_fast[o]
        for v in views
            feats = Float32.(collect(v.quantum_readout))
            lab = Float32(v.mask[1] ? 1 : 0)  # mask[0] (1-based in Julia)
            append!(Xall, feats); push!(yall, lab)
        end
    end
    n = length(yall); n >= 32 || error("insufficient real samples")
    Xmat = reshape(Xall, 15, n); y = yall
    # object-disjoint split: train on first ~48 objs, heldout last ~16
    n_train = 48 * 6
    Xtr = Xmat[:,1:n_train]; ytr = y[1:n_train]
    Xho = Xmat[:,n_train+1:end]; yho = y[n_train+1:end]
    m = Chain(Dense(15,1), sigmoid); opt = Flux.setup(Descent(0.15), m)
    for _ in 1:120
        gs = Flux.gradient(m) do mm; Flux.Losses.logitbinarycrossentropy(mm(Xtr), reshape(ytr,1,:)) end
        Flux.update!(opt, m, gs[1])
    end
    pred_ho = vec(m(Xho)) .> 0.5; acc = mean(pred_ho .== (yho .> 0.5))
    (acc, Dict("heldout_accuracy"=>acc, "chance"=>0.5, "pass"=>acc>0.5, "n_samples"=>n, "n_heldout"=>length(yho), "real_object_used"=>"candidate_reset_fast quantum_readout vs mask[0]"))
end
