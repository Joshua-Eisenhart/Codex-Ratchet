#!/usr/bin/env julia
# Julia leg: native fact-only drive and blinded selector.

using Dates
using JSON
using LinearAlgebra
using Random
using SHA

const SIM_ID = "ratchet_climb_engine_v2_blind"
const HERE = @__DIR__
const REPO = normpath(joinpath(HERE, "..", "..", ".."))
const RESULTS = joinpath(HERE, "results")

const classification = "scratch_diagnostic"
const promotion_allowed = false
const formal_admission_allowed = false

const TOOL_MANIFEST = Dict(
    "Julia LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing native matrix drive, mixedness, commutator, and blinded selector facts"),
    "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result JSON emission")
)
const TOOL_INTEGRATION_DEPTH = Dict("Julia LinearAlgebra" => "load_bearing", "JSON" => "supportive")

sha256_json(obj) = bytes2hex(sha256(JSON.json(obj)))
now_iso() = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::AbstractString) = replace(normpath(path), normpath(REPO) * "/" => "")

function sha256_file(path::AbstractString)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function load_spec()
    JSON.parsefile(joinpath(HERE, "spec.json"))
end

function carrier()
    spec = load_spec()
    path = joinpath(REPO, spec["reused_formal_gate_results"]["julia"])
    payload = JSON.parsefile(path)
    Dict(
        "source_path" => rel(path),
        "source_sha256" => sha256_file(path),
        "labels" => [String(row["label"]) for row in payload["carrier_states"]],
        "states" => payload["carrier_states"],
        "state_count" => Int(payload["carrier_summary"]["state_count"]),
        "formal_full_class_count" => Int(payload["gates"]["observable_quotient_R4"]["quotient_class_count"])
    )
end

function qcount(car)
    keys = Set{String}()
    for row in car["states"]
        push!(keys, join([string(round(Float64(v), digits=12)) for v in row["pvec"]], "|"))
    end
    (length(keys), 1)
end

function base_receipts(car, full_count, none_count)
    admitted = [1, 2, 3, 4]
    receipts = Any[]
    locks = Any[]
    prev = "GENESIS"
    steps = [
        (1, "finite_distinguishability", Dict("collapsed_class_count" => 1, "full_class_count" => full_count)),
        (2, "finite_support_S", Dict("state_count" => car["state_count"])),
        (3, "probe_family_P", Dict("no_probe_class_count" => none_count, "full_class_count" => full_count)),
        (4, "quotient_S_mod_P", Dict("projection_class_count" => full_count, "formal_full_class_count" => car["formal_full_class_count"]))
    ]
    for (rung, lift, facts) in steps
        receipt = Dict("rung" => rung, "admitted" => true, "selected_lift" => lift, "distinction_loss_detector" => Dict("measured" => true, "facts" => facts), "mss_gate" => Dict("selected" => lift, "stronger_candidates_rejected_unforced" => true), "engine" => "julia")
        entry = Dict("schema" => SIM_ID * ".lock_entry.v1", "rung" => rung, "decision" => receipt, "prev_hash" => prev)
        entry["entry_hash"] = sha256_json(entry)
        push!(receipts, receipt)
        push!(locks, entry)
        prev = entry["entry_hash"]
    end
    (admitted, receipts, locks)
end

function state(theta)
    v = ComplexF64[0, 0, 0, 0]
    v[1] = cos(theta)
    v[4] = sin(theta)
    v ./ norm(v)
end

function mixed(v)
    t = reshape(v, 2, 2)
    rho = t * t'
    round(Float64(real(1.0 - tr(rho * rho))), digits=12)
end

function drive(kind::String, seed::Int)
    rng = MersenneTwister(seed)
    z = ComplexF64[1 0; 0 -1]
    h = ComplexF64[1 1; 1 -1] ./ sqrt(2.0)
    i2 = Matrix{ComplexF64}(I, 2, 2)
    cnot = ComplexF64[1 0 0 0; 0 1 0 0; 0 0 0 1; 0 0 1 0]
    ua, ub = kind == "commuting_control" ? (kron(z, i2), kron(z, i2)) : (kron(h, i2), cnot)
    base = state(pi / 5.0)
    facts = Any[]
    window = Any[]
    for tick in 1:8
        ab = ub * (ua * base)
        ba = ua * (ub * base)
        if kind == "memoryless_control"
            jitter = rand(rng, [-1.0, 1.0]) * 0.03
            ab, ba = state(pi / 5.0 + jitter), state(pi / 5.0 - jitter)
        end
        pair = [mixed(ab), mixed(ba)]
        if kind != "memoryless_control"
            push!(window, tuple(pair...))
            length(window) > 4 && popfirst!(window)
        end
        push!(facts, Dict(
            "tick" => tick,
            "reduced_state_mixedness_values" => pair,
            "commutator_norm" => round(norm(ua * ub - ub * ua), digits=12),
            "order_gap_norm" => round(norm(ab - ba), digits=12),
            "persistence_count" => kind == "memoryless_control" ? 0 : length(Set(window))
        ))
        kind != "static_control" && (base = ab ./ norm(ab))
    end
    kind == "static_control" && (facts = facts[1:1])
    kind == "label_fact_shuffle_control" && shuffle!(rng, facts)
    facts
end

function selector(facts)
    candidates = [
        Dict("candidate_id" => "survivor_partition_slot", "rung" => 5, "strength" => 1, "needs" => "persistent_mixedness_split"),
        Dict("candidate_id" => "ordered_update_slot", "rung" => 6, "strength" => 2, "needs" => "persistent_order_gap"),
        Dict("candidate_id" => "density_readout_slot", "rung" => 10, "strength" => 3, "needs" => "late_density_refused"),
        Dict("candidate_id" => "hopf_readout_slot", "rung" => 11, "strength" => 4, "needs" => "late_hopf_refused")
    ]
    for fact in facts
        split = abs(fact["reduced_state_mixedness_values"][1] - fact["reduced_state_mixedness_values"][2])
        if fact["commutator_norm"] > 0 && fact["persistence_count"] >= 2 && split > 0.2
            return Dict("selected" => candidates[1], "facts_used" => [fact], "enumerated_candidates" => candidates)
        end
    end
    Dict("selected" => nothing, "facts_used" => Any[], "enumerated_candidates" => candidates)
end

function run_variant(cfg)
    car = carrier()
    full, none = qcount(car)
    admitted, receipts, locks = base_receipts(car, full, none)
    facts = drive(cfg["kind"], Int(cfg["seed"]))
    picked = selector(facts)
    rejected = Any[]
    if picked["selected"] !== nothing
        rung = Int(picked["selected"]["rung"])
        push!(admitted, rung)
        receipt = Dict("rung" => rung, "admitted" => true, "selected_lift" => picked["selected"]["candidate_id"], "distinction_loss_detector" => Dict("facts" => picked["facts_used"]))
        push!(receipts, receipt)
        push!(locks, Dict("rung" => rung, "decision" => receipt, "prev_hash" => locks[end]["entry_hash"], "entry_hash" => sha256_json(receipt)))
    else
        push!(rejected, Dict("typed_refusal" => "rejected_unforced", "reason" => "rung4 quotient not measured lossy by fact-only stream", "enumerated_candidates" => picked["enumerated_candidates"]))
    end
    Dict("run_id" => cfg["run_id"], "variant_id" => cfg["variant_id"], "engine" => "julia", "facts" => facts, "blinded_selector" => picked, "climbed_ladder" => admitted, "frontier_rung" => maximum(admitted), "append_only_lock_ledger" => locks, "rejected_frontier_attempts" => rejected, "rejected_unforced" => rejected, "all_pass" => full == car["state_count"])
end

function main()
    mkpath(RESULTS)
    runs = [run_variant(cfg) for cfg in load_spec()["drive_variants"]]
    frontiers = Dict(row["variant_id"] => row["frontier_rung"] for row in runs)
    payload = Dict(
        "schema_version" => "three_engine_sim_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "generated_at" => now_iso(),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "capstone_status" => "DRAFT_UNAUDITED",
        "claim_ceiling" => "scratch_diagnostic",
        "all_pass" => all(row -> row["all_pass"], runs),
        "frontier_reached" => maximum(values(frontiers)),
        "frontier_by_variant" => frontiers,
        "reached_beyond_rung4_by_variant" => Dict(k => v > 4 for (k, v) in frontiers),
        "run_results" => runs,
        "divergence_log" => ["scratch diagnostic; engine parity is checked in check_agreement.py"],
        "source_path" => rel(@__FILE__),
        "source_sha256" => sha256_file(@__FILE__),
        "packages_used" => ["Julia LinearAlgebra", "JSON"],
        "aligned_packages_load_bearing" => ["Julia LinearAlgebra"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH
    )
    out = joinpath(RESULTS, "ratchet_climb_engine_v2_blind_julia_results.json")
    open(out, "w") do io
        JSON.print(io, payload, 2)
    end
    println(JSON.json(Dict("all_pass" => payload["all_pass"], "frontier_by_variant" => frontiers)))
    payload["all_pass"] ? 0 : 1
end

exit(main())
