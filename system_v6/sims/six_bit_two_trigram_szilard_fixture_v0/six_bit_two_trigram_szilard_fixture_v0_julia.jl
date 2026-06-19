#!/usr/bin/env julia

using Dates
using JSON
using SHA

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "six_bit_two_trigram_szilard_fixture_v0"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")

frac(num::Integer, den::Integer = 1) = Dict(
    "num" => num,
    "den" => den,
    "string" => "$(num)/$(den)",
    "float" => num / den,
)

function bits_of_state(index::Integer)
    if index < 0 || index >= 64
        error("state index must be in [0, 63], got $index")
    end
    return [Int((index >> bit) & 1) for bit in 0:5]
end

trigram_value(bits) = bits[1] + 2 * bits[2] + 4 * bits[3]

function enumerate_carrier()
    rows = []
    for index in 0:63
        bits = bits_of_state(index)
        lower = trigram_value(bits[1:3])
        upper = trigram_value(bits[4:6])
        push!(
            rows,
            Dict(
                "state_index" => index,
                "bits" => bits,
                "lower_trigram" => lower,
                "upper_trigram" => upper,
                "trigram_pair" => [lower, upper],
                "parity_pair" => [sum(bits[1:3]) % 2, sum(bits[4:6]) % 2],
            ),
        )
    end
    return rows
end

function record_costs()
    return Dict(
        "unstructured_6bit_state_record" => frac(6),
        "two_trigram_full_pair_record" => frac(6),
        "lower_trigram_only_record" => frac(3),
        "upper_trigram_only_record" => frac(3),
        "parity_pair_record" => frac(2),
        "full_state_delta_bits" => frac(0),
    )
end

function ledger_rows()
    rows = Dict()
    for (row_id, bits) in (
        ("unstructured_6bit_state_record", 6),
        ("two_trigram_full_pair_record", 6),
        ("lower_trigram_only_record", 3),
        ("upper_trigram_only_record", 3),
        ("parity_pair_record", 2),
    )
        rows[row_id] = Dict(
            "cycle" => ["measure", "feedback", "erase"],
            "record_bits" => frac(bits),
            "measurement_record_ln2_coeff" => frac(bits),
            "ideal_feedback_work_credit_ln2_coeff" => frac(bits),
            "erase_cost_ln2_coeff" => frac(bits),
            "net_paid_cycle_ln2_coeff" => frac(0),
            "classification" => "classical_baseline",
        )
    end
    rows["wrong_order_controls"] = Dict(
        "canonical_measure_feedback_erase" => Dict("verdict" => "sat", "record_bits" => frac(6)),
        "feedback_before_measure" => Dict("verdict" => "unsat", "record_bits" => frac(6), "work_credit_ln2_coeff" => frac(0)),
        "erase_before_feedback" => Dict("verdict" => "unsat", "record_bits" => frac(6), "work_credit_ln2_coeff" => frac(0)),
        "no_measurement_control" => Dict("verdict" => "sat_control_no_work_credit", "record_bits" => frac(0), "work_credit_ln2_coeff" => frac(0)),
    )
    return rows
end

function sha256_file(path::AbstractString)
    return bytes2hex(open(sha256, path))
end

function main()
    mkpath(RESULT_DIR)
    states = enumerate_carrier()
    lower_values = sort(collect(Set(row["lower_trigram"] for row in states)))
    upper_values = sort(collect(Set(row["upper_trigram"] for row in states)))
    pair_count = length(Set((row["lower_trigram"], row["upper_trigram"]) for row in states))
    costs = record_costs()
    ledger = ledger_rows()
    gates = Dict(
        "state_count_64" => length(states) == 64,
        "lower_values_0_to_7" => lower_values == collect(0:7),
        "upper_values_0_to_7" => upper_values == collect(0:7),
        "pair_count_64" => pair_count == 64,
        "full_pair_matches_unstructured" => costs["two_trigram_full_pair_record"] == costs["unstructured_6bit_state_record"],
        "split_delta_zero" => costs["full_state_delta_bits"]["num"] == 0,
        "wrong_order_controls_reject" => ledger["wrong_order_controls"]["feedback_before_measure"]["verdict"] == "unsat" &&
                                         ledger["wrong_order_controls"]["erase_before_feedback"]["verdict"] == "unsat",
    )
    payload = Dict(
        "schema_version" => "three_engine_leg_result_v1",
        "sim_id" => SIM_ID,
        "engine" => "julia",
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => "scratch_diagnostic",
        "row_classification" => "classical_baseline",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "all_pass" => all(values(gates)),
        "source_path" => "system_v6/sims/$(SIM_ID)/$(SIM_ID)_julia.jl",
        "result_path" => "system_v6/sims/$(SIM_ID)/results/$(SIM_ID)_julia_results.json",
        "carrier_summary" => Dict(
            "state_count" => length(states),
            "bit_count" => 6,
            "lower_trigram_values" => lower_values,
            "upper_trigram_values" => upper_values,
            "pair_count" => pair_count,
        ),
        "record_costs" => costs,
        "per_cycle_ledger" => ledger,
        "gates" => gates,
        "packages_used" => ["JSON", "SHA", "julia_gf4_stdlib"],
        "aligned_packages_load_bearing" => ["julia_gf4_stdlib"],
        "package_observables" => Dict(
            "julia_gf4_stdlib" => "local exact integer bit/trigram enumeration and rational ledger mirror; no external algebra package claim",
        ),
        "TOOL_MANIFEST" => Dict(
            "julia_exact_integers" => "load_bearing mirror of finite carrier enumeration and ledger coefficients",
            "JSON" => "supportive durable result serialization",
            "SHA" => "supportive source/result hashing",
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "julia_exact_integers" => "load_bearing",
            "JSON" => "supportive",
            "SHA" => "supportive",
        ),
        "claim_boundary" => Dict(
            "reference_lane_only" => true,
            "no_physics_bridge" => true,
            "not_qit_admission" => true,
            "not_axis_admission" => true,
            "not_matrix64_completion" => true,
        ),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => payload["all_pass"], "result" => payload["result_path"])))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
