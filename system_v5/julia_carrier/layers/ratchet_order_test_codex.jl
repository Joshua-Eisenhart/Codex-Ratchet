# ratchet_order_test_codex.jl
#
# Pairwise noncommutative-order scaffold for the geometry-layer ratchet.
#
# This file is intentionally a scaffold, not a parent-complete nesting receipt.
# It runs the requested AB vs BA finite-order harness over explicit finite
# F01/N01 toy maps, while reading the best currently available local layer
# objects as provenance. The map implementation remains stubbed until the
# parent-complete layer maps are admitted by the layer gates.

using LinearAlgebra
using JSON
using Dates

const ROOT = normpath(joinpath(@__DIR__, ".."))
const RESULT_PATH = joinpath(@__DIR__, "ratchet_order_test_codex_results.json")
const TOL = 1.0e-9

const DOC_QUOTES = [
    Dict(
        "file" => "system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
        "section" => "Corrected Program",
        "lines" => "11-16",
        "quote" => "make the geometry layers as independent working legos\nprove each has real finite action and controls\nthen test admissible nesting/order\nthen let the surviving order become the ratchet",
    ),
    Dict(
        "file" => "system_v5/ops/MANIFOLD_GEOMETRY_LAYER_STACK_NONCOMMUTATIVE_ORDER_20260528.md",
        "section" => "What Allows Stacking",
        "lines" => "146-152",
        "quote" => "Layer A then Layer B   vs   Layer B then Layer A\nA∘B == B∘A                      -> no ratchet at that pair\nA∘B != B∘A and controls collapse -> real order pressure at that pair",
    ),
    Dict(
        "file" => "system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md",
        "section" => "Stage 2 - Pairwise Nested-Layer Test",
        "lines" => "180-185",
        "quote" => "NestedPairTest_Li_Lj:\n  (completed parent Li, completed parent Lj, common carrier projection P,\n   admissible nesting orders [Li then Lj, Lj then Li], controls)\n  -> paired output signatures, survivor sets, entropy/readout deltas,\n     order gaps, failed controls, blockers",
    ),
    Dict(
        "file" => "system_v5/ops/NONCOMMUTATION_AND_NESTED_LAYER_TEST_GATE_20260528.md",
        "section" => "Enforcement Rule",
        "lines" => "295-296",
        "quote" => "If `parent_completion_status` is missing, stale, or only `bounded_scout`, the\norder/nesting test is blocked.",
    ),
]

struct LayerSpec
    id::String
    label::String
    source_file::String
    result_file::String
    source_status::String
    parent_status::String
    map_status::String
end

mutable struct CarrierState
    payload::Vector{ComplexF64}
    phase::Float64
    chirality::Int
    carrier_anchor::String
    order_trace::Vector{String}
end

struct LayerMap
    spec::LayerSpec
    matrix::Matrix{ComplexF64}
    phase_twist::Float64
    chirality_flip::Bool
end

function rel_layer(path::String)
    return joinpath("layers", path)
end

function read_json(path::String)
    isfile(path) || return Dict{String,Any}()
    try
        return JSON.parsefile(path)
    catch err
        return Dict{String,Any}("json_error" => string(err))
    end
end

function truthy(x)
    x === true && return true
    x isa AbstractString && return lowercase(x) in ("true", "pass", "passes", "passes local rerun")
    return false
end

function infer_source_status(result_path::String)
    data = read_json(joinpath(@__DIR__, result_path))
    all_pass = truthy(get(data, "all_pass", false))
    promotion_allowed = get(data, "promotion_allowed", nothing)
    classification = string(get(data, "classification", "missing"))
    status = string(get(data, "status", get(data, "honest_status", get(data, "honest_status_ladder", "missing"))))
    if isempty(data)
        return "missing_result"
    elseif get(data, "json_error", nothing) !== nothing
        return "result_json_error"
    elseif all_pass || occursin("passes", lowercase(status))
        return "real_source_available_bounded_" * classification
    else
        return "source_available_not_passing_" * classification * "_promotion_allowed_" * string(promotion_allowed)
    end
end

function infer_parent_status(result_path::String)
    data = read_json(joinpath(@__DIR__, result_path))
    pcs = get(data, "parent_completion_status", missing)
    if !ismissing(pcs)
        return string(pcs)
    end
    return "missing_parent_completion_status"
end

function layer_specs()
    rows = [
        ("R0",  "root finite carrier/probe",               "R0_layer.jl",                     "R0_layer_results.json"),
        ("L0",  "finite response/effect/path quotient",     "L0_layer.jl",                     "L0_layer_results.json"),
        ("L1",  "spinor/density carrier",                  "L1_layer.jl",                     "L1_layer_results.json"),
        ("L2",  "S3 spinor carrier",                       "G_S3_spinor_carrier.jl",          "G_S3_spinor_carrier_results.json"),
        ("L3",  "S2 projective/Hopf base",                 "G_S2_hopf_base.jl",               "G_S2_hopf_base_results.json"),
        ("L4",  "Hopf fibration S3->S2 U(1)",              "G_hopf_fibration.jl",             "G_hopf_fibration_results.json"),
        ("L5",  "nested Hopf tori / torus leaf family",    "G_nested_hopf_tori.jl",           "G_nested_hopf_tori_results.json"),
        ("L6",  "connection / holonomy geometry",          "L6_layer_codex.jl",               "L6_layer_codex_results.json"),
        ("L7",  "Weyl spinor bundle",                      "L7_layer.jl",                     "L7_layer_results.json"),
        ("L8",  "chirality orientation cover",             "L8_layer.jl",                     "L8_layer_results.json"),
        ("L9",  "Clifford / quaternion module layer",      "L9_layer_codex.jl",               "L9_layer_codex_results.json"),
        ("L10", "terrain / channel / generator layer",     "L10_layer_codex.jl",              "L10_layer_codex_results.json"),
        ("L11", "operator-substage local cell layer",      "L11_layer_codex.jl",              "L11_layer_codex_results.json"),
        ("L12", "entropy / cut / communication layer",     "L12_layer_codex.jl",              "L12_layer_codex_results.json"),
        ("L13", "gluing / groupoid / dynamic transition",  "L13_layer_codex.jl",              "L13_layer_codex_results.json"),
    ]
    specs = LayerSpec[]
    for (id, label, src, res) in rows
        parent_status = infer_parent_status(res)
        map_status = parent_status in (
            "complete_for_intrinsic_order_test",
            "complete_for_pairwise_nesting_test",
            "complete_for_multi_layer_nesting_test",
        ) ? "real_parent_map_required_but_not_imported" : "stubbed_map_pending_parent_completion"
        push!(specs, LayerSpec(id, label, rel_layer(src), rel_layer(res), infer_source_status(res), parent_status, map_status))
    end
    return specs
end

function pauli_family()
    I2 = ComplexF64[1 0; 0 1]
    X = ComplexF64[0 1; 1 0]
    Y = ComplexF64[0 -im; im 0]
    Z = ComplexF64[1 0; 0 -1]
    H = (1 / sqrt(2)) * ComplexF64[1 1; 1 -1]
    S = ComplexF64[1 0; 0 im]
    R = ComplexF64[cos(0.37) -sin(0.37); sin(0.37) cos(0.37)]
    return [X, Y, Z, H, S, R, X * S, H * S, S * H, X * H, Y * H, Z * S, R * X, R * Y, R * Z]
end

function build_layer_maps(specs::Vector{LayerSpec})
    mats = pauli_family()
    maps = LayerMap[]
    for (idx, spec) in enumerate(specs)
        M = mats[mod1(idx, length(mats))]
        # The scaffold makes phase/chirality/carrier metadata load-bearing so
        # erasure controls can collapse the N01 gap. Real parent maps must
        # replace this with admitted layer maps and measured erasure deltas.
        phase_twist = 0.07 * idx
        chirality_flip = isodd(idx)
        push!(maps, LayerMap(spec, M, phase_twist, chirality_flip))
    end
    return maps
end

function initial_state()
    raw = ComplexF64[1.0 + 0.0im, 0.31 + 0.17im]
    psi = raw ./ norm(raw)
    return CarrierState(psi, 0.23, 1, "finite PEPS3D K=(V,E,F,C) scaffold anchor", String[])
end

function copy_state(s::CarrierState)
    return CarrierState(copy(s.payload), s.phase, s.chirality, s.carrier_anchor, copy(s.order_trace))
end

function apply_layer(s::CarrierState, lm::LayerMap; erase_phase=false, erase_chirality=false, erase_carrier=false)
    t = copy_state(s)
    erased_control = erase_phase || erase_chirality || erase_carrier
    carrier_active = !erased_control && t.carrier_anchor != "erased"
    phase_active = !erased_control
    chirality_active = !erased_control
    effective = carrier_active && phase_active && chirality_active ? lm.matrix : Matrix{ComplexF64}(I, 2, 2)
    phase = carrier_active && phase_active ? exp(im * (t.phase + lm.phase_twist)) : 1.0 + 0.0im
    ch = carrier_active && chirality_active ? t.chirality : 1
    t.payload = phase * ch * (effective * t.payload)
    norm(t.payload) > 0 && (t.payload ./= norm(t.payload))
    t.phase = phase_active ? mod(t.phase + lm.phase_twist, 2pi) : 0.0
    t.chirality = (chirality_active && lm.chirality_flip) ? -t.chirality : t.chirality
    t.carrier_anchor = carrier_active ? t.carrier_anchor : "erased"
    push!(t.order_trace, lm.spec.id)
    return t
end

function run_order(first::LayerMap, second::LayerMap; erase_phase=false, erase_chirality=false, erase_carrier=false)
    s = initial_state()
    return apply_layer(
        apply_layer(s, first; erase_phase=erase_phase, erase_chirality=erase_chirality, erase_carrier=erase_carrier),
        second; erase_phase=erase_phase, erase_chirality=erase_chirality, erase_carrier=erase_carrier,
    )
end

function signature(s::CarrierState)
    return [
        real(s.payload[1]), imag(s.payload[1]),
        real(s.payload[2]), imag(s.payload[2]),
        s.phase,
        Float64(s.chirality),
        s.carrier_anchor == "erased" ? 0.0 : 1.0,
    ]
end

gap(a::CarrierState, b::CarrierState) = norm(signature(a) .- signature(b))

function pair_result(a::LayerMap, b::LayerMap)
    ab = run_order(a, b)
    ba = run_order(b, a)
    base_gap = gap(ab, ba)
    controls = Dict(
        "erase_order" => 0.0,
        "erase_phase" => gap(run_order(a, b; erase_phase=true), run_order(b, a; erase_phase=true)),
        "erase_chirality" => gap(run_order(a, b; erase_chirality=true), run_order(b, a; erase_chirality=true)),
        "erase_carrier" => gap(run_order(a, b; erase_carrier=true), run_order(b, a; erase_carrier=true)),
    )
    controls_collapse = all(v <= TOL for v in values(controls))
    parent_gate_open = a.spec.parent_status in ("complete_for_pairwise_nesting_test", "complete_for_multi_layer_nesting_test") &&
                       b.spec.parent_status in ("complete_for_pairwise_nesting_test", "complete_for_multi_layer_nesting_test")
    survives_scaffold = base_gap > TOL && controls_collapse
    return Dict(
        "pair" => [a.spec.id, b.spec.id],
        "source_files" => [a.spec.source_file, b.spec.source_file],
        "result_files" => [a.spec.result_file, b.spec.result_file],
        "AB_trace" => ab.order_trace,
        "BA_trace" => ba.order_trace,
        "order_gap" => base_gap,
        "controls" => controls,
        "controls_collapse" => controls_collapse,
        "scaffold_survives" => survives_scaffold,
        "real_run_gate_open" => parent_gate_open,
        "real_run_status" => parent_gate_open ? "ready_for_real_parent_maps" : "blocked_missing_pairwise_parent_completion",
    )
end

function main()
    specs = layer_specs()
    maps = build_layer_maps(specs)
    pairs = Dict{String,Any}[]
    for i in 1:(length(maps)-1), j in (i+1):length(maps)
        push!(pairs, pair_result(maps[i], maps[j]))
    end
    scaffold_edges = [p["pair"] for p in pairs if p["scaffold_survives"]]
    real_edges = [p["pair"] for p in pairs if p["scaffold_survives"] && p["real_run_gate_open"]]
    required_real_layers = [s.id for s in specs]
    layer_table = [
        Dict(
            "id" => s.id,
            "label" => s.label,
            "source_file" => s.source_file,
            "result_file" => s.result_file,
            "source_status" => s.source_status,
            "parent_completion_status" => s.parent_status,
            "map_status" => s.map_status,
        ) for s in specs
    ]
    result = Dict(
        "artifact" => "ratchet_order_test_codex",
        "generated_at" => string(now()),
        "classification" => "scaffold_only",
        "promotion_allowed" => false,
        "claim_ceiling" => "F01/N01 pairwise-order harness scaffold only. Local layer sources are provenance; pairwise nesting remains blocked until parent_completion_status is complete_for_pairwise_nesting_test or stronger for both parents.",
        "f01" => Dict(
            "finite_carrier" => "2-component ComplexF64 spinor payload plus finite metadata",
            "probe_set" => ["payload real/imag", "phase", "chirality", "carrier anchor"],
            "operator_path_set" => "finite pair orders [A then B, B then A]",
        ),
        "n01" => Dict(
            "witness" => "noncommuting finite 2x2 operators in stub layer maps",
            "order_test" => "norm(signature(A(B(state))) - signature(B(A(state))))",
            "controls" => ["erase_order", "erase_phase", "erase_chirality", "erase_carrier"],
        ),
        "doc_quotes" => DOC_QUOTES,
        "layer_table" => layer_table,
        "pairs_tested" => length(pairs),
        "surviving_order_graph_scaffold" => scaffold_edges,
        "surviving_order_graph_real" => real_edges,
        "real_graph_status" => isempty(real_edges) ? "blocked_no_pair_has_parent_completion_status" : "has_real_ready_edges",
        "required_parent_complete_layers_for_full_real_ratchet" => required_real_layers,
        "pair_results" => pairs,
        "blocked_consumers" => ["layer_stacking_admission", "flux", "Xi", "Phi0", "Axis0", "FEP", "physics", "final_manifold_admission"],
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("ratchet_order_test_codex")
    println("result_path: ", RESULT_PATH)
    println("classification: scaffold_only")
    println("pairs_tested: ", length(pairs))
    println("scaffold_surviving_edges: ", length(scaffold_edges))
    println("real_surviving_edges: ", length(real_edges))
    println("real_graph_status: ", result["real_graph_status"])
    println("required_parent_complete_layers_for_full_real_ratchet: ", join(required_real_layers, ", "))
end

main()
