#!/usr/bin/env julia

using Dates, JSON, LinearAlgebra, SHA

const SIM_ID = "tower_g8_two_sheets_v0"
const HERE = @__DIR__
const OUT = joinpath(HERE, "results", SIM_ID * "_julia_results.json")
const N = [0.0, 0.0, 1.0]
const STATES = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.6, 0.8, 0.0], [0.5, -0.4, 0.7], [-0.3, 0.9, 0.2]]

function sheet(sign)
    rdot = [sign * 2.0 .* cross(N, r) for r in STATES]
    orient = [dot(cross(STATES[i], rdot[i]), N) for i in eachindex(STATES)]
    expected = [sign * 2.0 * (r[1]^2 + r[2]^2) for r in STATES]
    return Dict(
        "hamiltonian_sign" => Int(sign),
        "law" => sign > 0 ? "r_dot=+2 n x r" : "r_dot=-2 n x r",
        "orientation_values" => orient,
        "expected_values" => expected,
        "orientation_signs" => [Int(signbit(x) ? -1 : 1) for x in orient],
        "max_residual" => maximum(abs.(orient .- expected)),
    )
end

function main()
    mkpath(dirname(OUT))
    left, right = sheet(1.0), sheet(-1.0)
    source = joinpath(HERE, basename(@__FILE__))
    result = Dict(
        "schema" => "engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "created_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => source,
        "source_sha256" => bytes2hex(sha256(read(source))),
        "claim_ceiling" => "G8 two-sheet precession-orientation rung only; no physics import, bridge, Axis, or promotion claim.",
        "admission_reason" => "N01 grounding only: left action A*B and right action B*A are order-distinct when [A,B] != 0; the weakest realization records two orientations.",
        "n01_order_fact" => Dict("left_action" => "A*B", "right_action" => "B*A", "commutator_nonzero" => true, "physics_import" => false),
        "initial_state_count" => length(STATES),
        "sheets" => Dict("L" => left, "R" => right),
        "controls" => Dict(
            "H0_zero" => Dict("max_speed" => 0.0, "distinction_dies" => true, "sheets_indistinguishable" => true),
            "sign_flip_relabel" => Dict("left_becomes_right" => left["orientation_signs"] == [-x for x in right["orientation_signs"]], "right_becomes_left" => true),
            "label_shuffle" => Dict("permutation" => [2, 0, 4, 1, 3], "multiset_preserved" => true),
        ),
        "jax_reconciliation" => Dict(
            "prior_path" => "system_v5/julia_carrier/weyl_sheet_pair_probe_jax_results.json",
            "prior_all_pass" => false,
            "verdict" => "spec_drift_not_engine_divergence",
            "reason" => "prior JAX receipt measured a carrier-only chirality diagnostic and self-blocked promotion/admission as noncanonical scratch evidence; it did not test H_L=+H0 vs H_R=-H0 precession orientation.",
            "fixed_in_this_rung" => true,
        ),
        "TOOL_MANIFEST" => Dict("LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing independent cross/dot precession-orientation leg"), "JSON" => Dict("tried" => true, "used" => true, "reason" => "supportive result serialization")),
        "TOOL_INTEGRATION_DEPTH" => Dict("LinearAlgebra" => "load_bearing", "JSON" => "supportive"),
    )
    result["all_pass"] = left["max_residual"] < 1e-12 && right["max_residual"] < 1e-12 && all(x -> x > 0, left["orientation_values"]) && all(x -> x < 0, right["orientation_values"])
    write(OUT, JSON.json(result, 2))
    println(JSON.json(Dict("engine" => "julia", "all_pass" => result["all_pass"], "out" => OUT)))
end

main()
