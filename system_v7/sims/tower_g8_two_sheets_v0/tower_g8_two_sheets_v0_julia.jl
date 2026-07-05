#!/usr/bin/env julia

using Dates, JSON, LinearAlgebra, SHA

const SIM_ID = "tower_g8_two_sheets_v0"
const HERE = @__DIR__
const OUT = joinpath(HERE, "results", SIM_ID * "_julia_results.json")
const N = [0.0, 0.0, 1.0]
const STATES = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.6, 0.8, 0.0], [0.5, -0.4, 0.7], [-0.3, 0.9, 0.2]]
const DT = 1.0e-4
const STEPS = 240
const TOL = 3.0e-4

function evolve_point(r0, sign)
    r = copy(r0)
    points = Vector{Vector{Float64}}()
    for _ in 1:STEPS
        push!(points, copy(r))
        r = r .+ DT .* sign .* 2.0 .* cross(N, r)
    end
    return points
end

function fit_slope(times, angles)
    tbar = sum(times) / length(times)
    abar = sum(angles) / length(angles)
    return sum((times .- tbar) .* (angles .- abar)) / sum((times .- tbar) .^ 2)
end

function unwrap_angles(angles)
    out = copy(angles)
    for i in 2:length(out)
        while out[i] - out[i - 1] > pi
            out[i:end] .-= 2pi
        end
        while out[i] - out[i - 1] < -pi
            out[i:end] .+= 2pi
        end
    end
    return out
end

function measure_rates(sign)
    times = collect(0:STEPS-1) .* DT
    rates = Float64[]
    for state in STATES
        points = evolve_point(state, sign)
        angles = unwrap_angles([atan(p[2], p[1]) for p in points])
        push!(rates, fit_slope(times, angles))
    end
    return rates
end

function analytic_orientation(sign)
    return [sign * 2.0 * (r[1]^2 + r[2]^2) for r in STATES]
end

function sheet(sign)
    rates = measure_rates(sign)
    radii_sq = [r[1]^2 + r[2]^2 for r in STATES]
    orient = [rates[i] * radii_sq[i] for i in eachindex(rates)]
    expected = analytic_orientation(sign)
    return Dict(
        "hamiltonian_sign" => Int(sign),
        "law" => sign > 0 ? "r_dot=+2 n x r" : "r_dot=-2 n x r",
        "measured_rates" => rates,
        "orientation_values" => orient,
        "expected_values" => expected,
        "orientation_signs" => [Int(signbit(x) ? -1 : 1) for x in orient],
        "max_residual" => maximum(abs.(orient .- expected)),
        "tolerance" => TOL,
    )
end

function controls(left, right)
    zero_rates = measure_rates(0.0)
    zero_orient = [zero_rates[i] * (STATES[i][1]^2 + STATES[i][2]^2) for i in eachindex(STATES)]
    relabeled_right_values = [-x for x in right["orientation_values"]]
    perm = [3, 1, 5, 2, 4]
    shuffled_left = [left["orientation_values"][i] for i in perm]
    relabel_residual = maximum(abs.([relabeled_right_values[i] - left["orientation_values"][i] for i in eachindex(STATES)]))
    sign_residual = maximum(abs.([right["orientation_values"][i] + left["orientation_values"][i] for i in eachindex(STATES)]))
    return Dict(
        "H0_zero" => Dict("measured_rates" => zero_rates, "max_abs_rate" => maximum(abs.(zero_rates)), "max_abs_orientation" => maximum(abs.(zero_orient)), "sheets_indistinguishable" => maximum(abs.(zero_rates)) < TOL),
        "sign_flip_relabel" => Dict("applied_relabel" => "measured R orientation values multiplied by -1", "measured_right_values" => right["orientation_values"], "relabeled_measured_right_values" => relabeled_right_values, "max_residual_after_relabel" => relabel_residual, "left_becomes_right" => relabel_residual < TOL, "right_becomes_left" => sign_residual < TOL),
        "label_shuffle" => Dict("permutation" => [2, 0, 4, 1, 3], "shuffled_values" => shuffled_left, "multiset_preserved" => sort(round.(shuffled_left, digits=12)) == sort(round.(left["orientation_values"], digits=12))),
    )
end

function main()
    mkpath(dirname(OUT))
    left, right = sheet(1.0), sheet(-1.0)
    computed_controls = controls(left, right)
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
        "controls" => computed_controls,
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
    result["all_pass"] = left["max_residual"] < TOL && right["max_residual"] < TOL && all(x -> x > 0, left["orientation_values"]) && all(x -> x < 0, right["orientation_values"]) && computed_controls["H0_zero"]["sheets_indistinguishable"] && computed_controls["sign_flip_relabel"]["left_becomes_right"] && computed_controls["sign_flip_relabel"]["right_becomes_left"] && computed_controls["label_shuffle"]["multiset_preserved"]
    write(OUT, JSON.json(result, 2))
    println(JSON.json(Dict("engine" => "julia", "all_pass" => result["all_pass"], "out" => OUT)))
end

main()
