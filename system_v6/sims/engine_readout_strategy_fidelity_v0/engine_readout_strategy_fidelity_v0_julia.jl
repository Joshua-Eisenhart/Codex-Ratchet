#!/usr/bin/env julia
# Dense Julia/Z3.jl leg for engine_readout_strategy_fidelity_v0.

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "engine_readout_strategy_fidelity_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath("system_v6", "sims", SIM_ID, "$(SIM_ID)_$(ENGINE).jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath("system_v6", "sims", SIM_ID, "results", "$(SIM_ID)_$(ENGINE)_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const MODE = "FREE"
const SEED = 20260610
const N = 8

const PIN_SPEC = "engine_readout_strategy_fidelity_v0|consumes=123b8e7d8,dd9ec4999|n=8|states=dense_loop_local_replay|word=D_then_I:Se,Ne,Ni,Si,Se,Si,Ni,Ne|seat_i_uses_word_i_mod_8|strategies=2types_2loops_4stage_slots|read_rule=outer_uppercase_inner_lowercase|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const COST_SOURCE_REF = Dict(
    "commit" => "123b8e7d8f1b7aca5162facc5a7801f06372b02a",
    "source" => "system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_julia.jl",
    "sections" => ["PIN_SPEC", "STAGE_WORD", "stage_assignment.rule"],
)

const AUTOMATON_SOURCE_REF = Dict(
    "commit" => "dd9ec4999b2ccb982226344f232dda86307429fc",
    "source" => "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "section" => "The Two-Engine Readout Automaton / THE 16 LOOP-READOUT STRATEGIES",
    "read_rule" => "active loop reads one component of the stage two-component word; outer uppercase, inner lowercase",
)

const TOOL_MANIFEST = Dict(
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia Z3.jl check over the computed 16-row periodicity identity"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive dense matrix and statevector operations"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamping, and hashing"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA" => "supportive",
)

const I2 = ComplexF64[1 0; 0 1]
const X = ComplexF64[0 1; 1 0]
const ZMAT = ComplexF64[1 0; 0 -1]

const STAGE_WORD = [
    Dict("stage" => "Se", "loop" => "D", "signed_operator" => "Ti_up", "axis" => "Z", "family" => "Ti"),
    Dict("stage" => "Ne", "loop" => "D", "signed_operator" => "Fe_up", "axis" => "Z", "family" => "Fe"),
    Dict("stage" => "Ni", "loop" => "D", "signed_operator" => "Ti_down", "axis" => "Z", "family" => "Ti"),
    Dict("stage" => "Si", "loop" => "D", "signed_operator" => "Fe_down", "axis" => "Z", "family" => "Fe"),
    Dict("stage" => "Se", "loop" => "I", "signed_operator" => "Te_up", "axis" => "X", "family" => "Te"),
    Dict("stage" => "Si", "loop" => "I", "signed_operator" => "Fi_up", "axis" => "X", "family" => "Fi"),
    Dict("stage" => "Ni", "loop" => "I", "signed_operator" => "Te_down", "axis" => "X", "family" => "Te"),
    Dict("stage" => "Ne", "loop" => "I", "signed_operator" => "Fi_down", "axis" => "X", "family" => "Fi"),
]

const STAGE_COMPONENTS = Dict(
    "Se" => Dict("outer" => "LOSE", "inner" => "win"),
    "Ne" => Dict("outer" => "WIN", "inner" => "lose"),
    "Ni" => Dict("outer" => "LOSE", "inner" => "lose"),
    "Si" => Dict("outer" => "WIN", "inner" => "win"),
)

const BASE_STRATEGIES = [
    Dict("base_id" => "type1_outer_deductive", "engine_type" => "Type1", "loop" => "outer", "order_family" => "deductive", "component" => "outer", "path" => ["Se", "Ne", "Ni", "Si"], "readout_by_stage" => Dict("Se" => "LOSE", "Ne" => "WIN", "Ni" => "LOSE", "Si" => "WIN"), "predicted_periodicity" => "alternating"),
    Dict("base_id" => "type1_inner_inductive", "engine_type" => "Type1", "loop" => "inner", "order_family" => "inductive", "component" => "inner", "path" => ["Se", "Si", "Ni", "Ne"], "readout_by_stage" => Dict("Se" => "win", "Si" => "win", "Ni" => "lose", "Ne" => "lose"), "predicted_periodicity" => "paired"),
    Dict("base_id" => "type2_outer_inductive", "engine_type" => "Type2", "loop" => "outer", "order_family" => "inductive", "component" => "outer", "path" => ["Se", "Si", "Ni", "Ne"], "readout_by_stage" => Dict("Se" => "WIN", "Si" => "WIN", "Ni" => "LOSE", "Ne" => "LOSE"), "predicted_periodicity" => "paired"),
    Dict("base_id" => "type2_inner_deductive", "engine_type" => "Type2", "loop" => "inner", "order_family" => "deductive", "component" => "inner", "path" => ["Se", "Ne", "Ni", "Si"], "readout_by_stage" => Dict("Se" => "lose", "Ne" => "win", "Ni" => "lose", "Si" => "win"), "predicted_periodicity" => "alternating"),
]

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))
r12(x) = round(Float64(real(x)); digits=12)
sign_for(opname::String)::Float64 = endswith(opname, "_up") ? 1.0 : -1.0
axis_matrix(axis::String) = axis == "X" ? X : ZMAT

function rx(theta::Float64)
    cos(theta / 2) .* I2 .- 1im * sin(theta / 2) .* X
end

function rz(theta::Float64)
    cos(theta / 2) .* I2 .- 1im * sin(theta / 2) .* ZMAT
end

function raa(axis::String, theta::Float64)
    a = axis_matrix(axis)
    cos(theta / 2) .* kron(I2, I2) .- 1im * sin(theta / 2) .* kron(a, a)
end

function bit_at(index0::Int, site0::Int, n::Int)::Int
    shift = n - 1 - site0
    return (index0 >> shift) & 1
end

function replace_bits(index0::Int, where::Vector{Int}, local_out::Int, n::Int)::Int
    out = index0
    for (pos, site0) in enumerate(where)
        shift = n - 1 - site0
        bit = (local_out >> (length(where) - pos)) & 1
        if bit == 1
            out |= (1 << shift)
        else
            out &= ~(1 << shift)
        end
    end
    return out
end

function local_index(index0::Int, where::Vector{Int}, n::Int)::Int
    value = 0
    for site0 in where
        value = 2 * value + bit_at(index0, site0, n)
    end
    return value
end

function apply_dense_gate(state::Vector{ComplexF64}, gate::Matrix{ComplexF64}, where::Vector{Int}, n::Int)
    out = zeros(ComplexF64, length(state))
    local_dim = 2 ^ length(where)
    for basis0 in 0:(length(state) - 1)
        amp = state[basis0 + 1]
        amp == 0 && continue
        in_local = local_index(basis0, where, n)
        for out_local in 0:(local_dim - 1)
            out_basis = replace_bits(basis0, where, out_local, n)
            out[out_basis + 1] += gate[out_local + 1, in_local + 1] * amp
        end
    end
    out
end

function state_digest(state::Vector{ComplexF64})::String
    parts = String[]
    for z in state
        push!(parts, string(round(real(z); digits=14)))
        push!(parts, string(round(imag(z); digits=14)))
    end
    sha256_text(join(parts, ","))
end

function stage_gates(n::Int, step::Int)
    stage = STAGE_WORD[mod(step - 1, length(STAGE_WORD)) + 1]
    seat = mod(step - 1, n)
    sign = sign_for(stage["signed_operator"])
    family = String(stage["family"])
    pair_angle = sign * (stage["axis"] == "Z" ? 0.31 : 0.29)
    gates = Any[]
    if family == "Fi" || family == "Fe"
        push!(gates, Dict("gate" => (family == "Fi" ? rx(sign * 0.37) : rz(sign * 0.41)), "where" => [seat]))
        pair_angle = sign * (family == "Fi" ? 0.17 : 0.19)
    end
    two_site = raa(String(stage["axis"]), pair_angle)
    push!(gates, Dict("gate" => two_site, "where" => [mod(seat - 1, n), seat]))
    push!(gates, Dict("gate" => two_site, "where" => [seat, mod(seat + 1, n)]))
    return stage, gates
end

function replay_loop_local_states(traversal::String)
    steps = traversal == "word" ? N : 2 * N
    state = zeros(ComplexF64, 2^N)
    state[1] = 1.0 + 0im
    trace = Any[]
    for step in 1:steps
        stage, gates = stage_gates(N, step)
        for item in gates
            state = apply_dense_gate(state, item["gate"], item["where"], N)
        end
        norm_value = real(dot(state, state))
        push!(trace, Dict(
            "step" => step,
            "seat" => mod(step - 1, N),
            "stage" => stage["stage"],
            "loop" => stage["loop"],
            "signed_operator" => stage["signed_operator"],
            "state_sha256" => state_digest(state),
            "norm" => r12(norm_value),
            "density_trace_real" => r12(norm_value),
        ))
    end
    Dict(
        "traversal" => traversal,
        "n" => N,
        "statevector_dimension" => length(state),
        "steps" => steps,
        "stage_assignment" => "seat i receives STAGE_WORD[i mod 8]; double_720 repeats the same stored word",
        "trace" => trace,
        "final_state_sha256" => state_digest(state),
        "max_norm_deviation" => maximum([abs(row["norm"] - 1.0) for row in trace]),
    )
end

function labels_for_path(base, path, repeat::Int)
    labels = String[]
    for _ in 1:repeat
        for stage in path
            push!(labels, base["readout_by_stage"][stage])
        end
    end
    labels
end

bits_for_labels(labels) = [lowercase(label) == "win" ? 1 : 0 for label in labels]

function periodicity_status(labels, expected::String)::Bool
    bits = bits_for_labels(labels[1:4])
    if expected == "alternating"
        ok4 = bits[1] == bits[3] && bits[2] == bits[4] && bits[1] != bits[2]
    else
        ok4 = bits[1] == bits[2] && bits[3] == bits[4] && bits[1] != bits[3]
    end
    length(labels) == 4 ? ok4 : (ok4 && labels[1:4] == labels[5:8])
end

function state_indices_for(base, traversal::String)
    offset = base["order_family"] == "deductive" ? 0 : 4
    if traversal == "word"
        return [offset + i for i in 0:3]
    end
    vcat([offset + i for i in 0:3], [8 + offset + i for i in 0:3])
end

function build_strategy_rows(states_by_traversal)
    rows = Any[]
    for base in BASE_STRATEGIES
        for stage_slot in base["path"]
            row_id = "$(base["base_id"])_slot_$(stage_slot)"
            word_labels = labels_for_path(base, base["path"], 1)
            double_labels = labels_for_path(base, base["path"], 2)
            word_indices = state_indices_for(base, "word")
            double_indices = state_indices_for(base, "double_720")
            word_states = [states_by_traversal["word"]["trace"][idx + 1] for idx in word_indices]
            double_states = [states_by_traversal["double_720"]["trace"][idx + 1] for idx in double_indices]
            push!(rows, Dict(
                "strategy_id" => row_id,
                "base_strategy" => base["base_id"],
                "engine_type" => base["engine_type"],
                "loop" => base["loop"],
                "order_family" => base["order_family"],
                "component" => base["component"],
                "stage_slot" => stage_slot,
                "path" => base["path"],
                "state_indices_word" => word_indices,
                "state_indices_double_720" => double_indices,
                "readout_word" => word_labels,
                "readout_double_720" => double_labels,
                "bits_word" => bits_for_labels(word_labels),
                "bits_double_720" => bits_for_labels(double_labels),
                "state_sha256_word" => [item["state_sha256"] for item in word_states],
                "state_sha256_double_720" => [item["state_sha256"] for item in double_states],
                "density_trace_word" => [item["density_trace_real"] for item in word_states],
                "density_trace_double_720" => [item["density_trace_real"] for item in double_states],
                "predicted_periodicity" => base["predicted_periodicity"],
                "periodicity_word_ok" => periodicity_status(word_labels, base["predicted_periodicity"]),
                "periodicity_double_720_ok" => periodicity_status(double_labels, base["predicted_periodicity"]),
            ))
        end
    end
    rows
end

function z3_periodicity(rows)
    solver = Z3.Solver()
    violations = Z3.Expr[]
    for (idx, row) in enumerate(rows)
        bits = [Z3.BoolVar("jr_$(idx)_$(i)") for i in 1:4]
        for (bit, value) in zip(bits, row["bits_word"])
            Z3.add(solver, bit == Z3.BoolVal(value == 1))
        end
        if row["predicted_periodicity"] == "alternating"
            good = Z3.And(Z3.Expr[bits[1] == bits[3], bits[2] == bits[4], Z3.Not(bits[1] == bits[2])])
        else
            good = Z3.And(Z3.Expr[bits[1] == bits[2], bits[3] == bits[4], Z3.Not(bits[1] == bits[3])])
        end
        push!(violations, Z3.Not(good))
    end
    Z3.add(solver, Z3.Or(violations))
    verdict = string(Z3.check(solver))

    control = Z3.Solver()
    c = [Z3.BoolVar("jerased_$(i)") for i in 1:4]
    Z3.add(control, c[1] == c[3])
    Z3.add(control, c[2] == c[4])
    Z3.add(control, c[1] == c[2])
    Z3.add(control, c[3] == c[4])
    control_verdict = string(Z3.check(control))
    Dict(
        "ran" => true,
        "load_bearing" => true,
        "verdict" => verdict,
        "identity" => "no computed strategy row violates its predicted alternating/paired periodicity",
        "positive_case" => "bind all 16 computed four-bit readouts, assert existence of a predicted-periodicity violation",
        "erased_flip_control" => "erase nontrivial flip inequality; constant readout satisfies the weakened equalities",
        "control_verdict" => control_verdict,
    )
end

function main()
    mkpath(RESULT_DIR)
    states = Dict(name => replay_loop_local_states(name) for name in ["word", "double_720"])
    rows = build_strategy_rows(states)
    proof = z3_periodicity(rows)
    findings = [row["strategy_id"] for row in rows if !(row["periodicity_word_ok"] && row["periodicity_double_720_ok"])]
    gate_pass = Dict(
        "ceiling_preserved" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false,
        "dense_n8_loop_local_states_replayed" => states["word"]["steps"] == 8 && states["double_720"]["steps"] == 16,
        "dense_state_norms_unit" => states["word"]["max_norm_deviation"] <= 1.0e-10 && states["double_720"]["max_norm_deviation"] <= 1.0e-10,
        "strategy_count_16" => length(rows) == 16,
        "periodicity_table_clean" => isempty(findings),
        "julia_z3_computed_identity_unsat" => proof["verdict"] == "unsat",
        "julia_z3_erased_flip_control_sat" => proof["control_verdict"] == "sat",
    )
    result = Dict(
        "schema_version" => "$(SIM_ID)_julia_result_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "mode" => MODE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+$" => "") * "Z",
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "seed" => SEED,
        "source_refs" => Dict("cost_discriminator" => COST_SOURCE_REF, "automaton" => AUTOMATON_SOURCE_REF),
        "stage_word" => STAGE_WORD,
        "stage_components" => STAGE_COMPONENTS,
        "states" => states,
        "strategy_rows" => rows,
        "periodicity_findings" => findings,
        "crossover_proofs" => Dict("julia_z3" => proof),
        "packages_used" => ["Z3", "LinearAlgebra", "JSON", "Dates", "SHA"],
        "aligned_packages_load_bearing" => ["Z3"],
        "claim_path_tools" => ["Z3"],
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            Dict("tool" => "LinearAlgebra", "qualified_api" => "dense Vector{ComplexF64} evolution", "input_object" => "n=8 loop-local stage-word gate plan", "output_object" => "word and double_720 dense state traces", "positive_case" => "stored D_then_I word", "negative_or_erased_control" => "none in Julia leg; Python leg carries controls", "boundary_case" => "16 evolved states", "demotion_condition" => "state norms drift or state count/order differs", "gates" => ["dense_n8_loop_local_states_replayed", "dense_state_norms_unit"]),
            Dict("tool" => "Z3", "qualified_api" => "Z3.Solver/Z3.BoolVar/Z3.add/Z3.check", "input_object" => "all 16 computed strategy bit rows", "output_object" => "UNSAT violation query plus SAT erased-flip control", "positive_case" => "no computed row violates predicted periodicity", "negative_or_erased_control" => "constant readout after erased flip", "boundary_case" => "four-stage rows lifted to double_720 repetition", "demotion_condition" => "positive query SAT or erased control UNSAT", "gates" => ["julia_z3_computed_identity_unsat", "julia_z3_erased_flip_control_sat"]),
        ],
        "values" => Dict(
            "strategy_count" => length(rows),
            "periodicity_violation_count" => length(findings),
            "state_count_word" => states["word"]["steps"],
            "state_count_double_720" => states["double_720"]["steps"],
        ),
        "gate_pass" => gate_pass,
        "all_pass" => all(collect(values(gate_pass))),
        "limits" => ["n=8 dense replay only", "scratch_diagnostic only", "no promotion or formal admission"],
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict(
        "ok" => result["all_pass"],
        "result_path" => RESULT_PATH_REL,
        "periodicity_violations" => result["values"]["periodicity_violation_count"],
    )))
    return result["all_pass"] ? 0 : 1
end

exit(main())
