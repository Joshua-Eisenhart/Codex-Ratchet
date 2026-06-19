#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra

const OBJECT_ID = "rosetta_igt_qit_convergence_probe"
const RESULT_PATH = joinpath(@__DIR__, "rosetta_igt_qit_convergence_probe_julia_results.json")
const JAX_REFERENCE_PATH = joinpath(@__DIR__, "rosetta_igt_qit_convergence_probe_jax_results.json")
const TOL = 1.0e-9
const STRICT_STOP_TOL = 1.0e-6
const QIT_DT = 0.01
const QIT_STEPS = 512

const VERTEX_LABELS = [
    ("win", "WIN"),
    ("win", "LOSE"),
    ("lose", "WIN"),
    ("lose", "LOSE"),
]
const VERTEX_COORDS = [
    (1.0, 1.0),
    (1.0, -1.0),
    (-1.0, 1.0),
    (-1.0, -1.0),
]
const N_GENERIC = normalize(Float64[0.37, -0.51, 0.78])
const R0 = Float64[0.23, -0.31, 0.17]

bool_scalar(x::Bool) = x ? 1.0 : 0.0

function vec_payload(v)
    [Float64(x) for x in v]
end

function hamming(a, b)
    count = 0
    for idx in 1:length(a)
        if a[idx] != b[idx]
            count += 1
        end
    end
    count
end

function permutations(v::Vector{Int})
    if length(v) <= 1
        return [copy(v)]
    end
    out = Vector{Vector{Int}}()
    for idx in eachindex(v)
        head = v[idx]
        rest = [v[j] for j in eachindex(v) if j != idx]
        for tail in permutations(rest)
            push!(out, vcat([head], tail))
        end
    end
    out
end

function adjacent(i::Int, j::Int)
    hamming(VERTEX_LABELS[i], VERTEX_LABELS[j]) == 1
end

function is_hamiltonian_cycle(cycle::Vector{Int})
    length(cycle) == 4 || return false
    length(Set(cycle)) == 4 || return false
    for idx in 1:length(cycle)
        a = cycle[idx]
        b = cycle[mod1(idx + 1, length(cycle))]
        adjacent(a, b) || return false
    end
    true
end

function rotations(cycle::Vector{Int})
    [vcat(cycle[idx:end], cycle[1:idx-1]) for idx in 1:length(cycle)]
end

cycle_key(cycle::Vector{Int}) = join(string.(cycle), ",")

function normalize_rotation(cycle::Vector{Int})
    sort(rotations(cycle), by=cycle_key)[1]
end

function enumerate_directed_hamiltonian_cycles()
    [p for p in permutations(collect(1:4)) if is_hamiltonian_cycle(p)]
end

function inequivalent_cycles_up_to_rotation(all_cycles)
    seen = Set{String}()
    out = Vector{Vector{Int}}()
    for cycle in all_cycles
        normalized = normalize_rotation(cycle)
        key = cycle_key(normalized)
        if !(key in seen)
            push!(seen, key)
            push!(out, normalized)
        end
    end
    sort!(out, by=cycle_key)
    out
end

function signed_area2(cycle::Vector{Int}, coords)
    area2 = 0.0
    for idx in 1:length(cycle)
        a = coords[cycle[idx]]
        b = coords[cycle[mod1(idx + 1, length(cycle))]]
        area2 += a[1] * b[2] - a[2] * b[1]
    end
    area2
end

function chirality_from_cycle(cycle::Vector{Int}, coords)
    area2 = signed_area2(cycle, coords)
    if area2 < -TOL
        return 1
    elseif area2 > TOL
        return -1
    end
    0
end

function axis_flip_sequence(cycle::Vector{Int})
    seq = String[]
    for idx in 1:length(cycle)
        a = VERTEX_LABELS[cycle[idx]]
        b = VERTEX_LABELS[cycle[mod1(idx + 1, length(cycle))]]
        if a[1] != b[1]
            push!(seq, "lowercase_winlose_axis")
        elseif a[2] != b[2]
            push!(seq, "uppercase_WINLOSE_axis")
        else
            push!(seq, "none")
        end
    end
    seq
end

function cycle_payload(cycle::Vector{Int}, coords)
    chi = chirality_from_cycle(cycle, coords)
    Dict{String,Any}(
        "cycle_vertices_1_based" => cycle,
        "cycle_labels" => [[VERTEX_LABELS[i][1], VERTEX_LABELS[i][2]] for i in cycle],
        "axis_flip_sequence" => axis_flip_sequence(cycle),
        "signed_area2" => Float64(signed_area2(cycle, coords)),
        "chirality" => chi,
        "orientation_readout" => chi == 1 ? "cw_derived_from_negative_signed_area" :
            (chi == -1 ? "ccw_derived_from_positive_signed_area" : "degenerate_zero_area"),
    )
end

function build_igt()
    all_cycles = enumerate_directed_hamiltonian_cycles()
    cycles = inequivalent_cycles_up_to_rotation(all_cycles)
    payloads = [cycle_payload(cycle, VERTEX_COORDS) for cycle in cycles]
    signs = [Int(p["chirality"]) for p in payloads]
    Dict{String,Any}(
        "vertices" => [
            Dict("id" => idx, "label" => [VERTEX_LABELS[idx][1], VERTEX_LABELS[idx][2]], "coord" => [VERTEX_COORDS[idx][1], VERTEX_COORDS[idx][2]])
            for idx in 1:4
        ],
        "edges" => [[i, j] for i in 1:4 for j in i+1:4 if adjacent(i, j)],
        "directed_hamiltonian_cycle_count" => length(all_cycles),
        "inequivalent_directed_cycles_up_to_rotation_count" => length(cycles),
        "exactly_two_igt_cycles" => length(cycles) == 2,
        "cycles" => payloads,
        "igt_chirality" => signs,
        "igt_chirality_signed" => length(signs) == 2 && sort(signs) == [-1, 1],
    )
end

function engine_s(engine::String; no_flip_control::Bool=false)
    if no_flip_control || engine == "type1"
        return 1.0
    end
    -1.0
end

function bloch_rhs(engine::String, r::Vector{Float64}; no_flip_control::Bool=false)
    2.0 * engine_s(engine; no_flip_control=no_flip_control) .* cross(N_GENERIC, r)
end

function rk4_bloch_step(engine::String, r::Vector{Float64}; no_flip_control::Bool=false)
    f(x) = bloch_rhs(engine, x; no_flip_control=no_flip_control)
    k1 = f(r)
    k2 = f(r .+ 0.5 .* QIT_DT .* k1)
    k3 = f(r .+ 0.5 .* QIT_DT .* k2)
    k4 = f(r .+ QIT_DT .* k3)
    r .+ (QIT_DT / 6.0) .* (k1 .+ 2.0 .* k2 .+ 2.0 .* k3 .+ k4)
end

function qit_chirality(engine::String; no_flip_control::Bool=false)
    r = copy(R0)
    circulation_sum = 0.0
    min_circulation = Inf
    max_circulation = -Inf
    for _ in 1:QIT_STEPS
        rdot = bloch_rhs(engine, r; no_flip_control=no_flip_control)
        circulation = dot(cross(r, rdot), N_GENERIC)
        circulation_sum += circulation
        min_circulation = min(min_circulation, circulation)
        max_circulation = max(max_circulation, circulation)
        r = rk4_bloch_step(engine, r; no_flip_control=no_flip_control)
    end
    mean_circulation = circulation_sum / QIT_STEPS
    sign_value = mean_circulation > TOL ? 1 : (mean_circulation < -TOL ? -1 : 0)
    Dict{String,Any}(
        "engine" => engine,
        "s_from_dynamics" => engine_s(engine; no_flip_control=no_flip_control),
        "no_flip_control" => no_flip_control,
        "mean_circulation" => Float64(mean_circulation),
        "min_circulation" => Float64(min_circulation),
        "max_circulation" => Float64(max_circulation),
        "terminal_bloch" => vec_payload(r),
        "chirality" => sign_value,
    )
end

function build_qit()
    type1 = qit_chirality("type1")
    type2 = qit_chirality("type2")
    no_flip_type1 = qit_chirality("type1"; no_flip_control=true)
    no_flip_type2 = qit_chirality("type2"; no_flip_control=true)
    signs = [Int(type1["chirality"]), Int(type2["chirality"])]
    no_flip_signs = [Int(no_flip_type1["chirality"]), Int(no_flip_type2["chirality"])]
    Dict{String,Any}(
        "terrain_equation_source" => "Hamiltonian circulation channel of the engine_noncollapse_probe terrain equations: d rho/dt = -i[H0,rho] for Type1 and +i[H0,rho] for Type2, expressed as rdot = +/- 2 n x r.",
        "h0_generic_n" => vec_payload(N_GENERIC),
        "initial_bloch" => vec_payload(R0),
        "dt" => QIT_DT,
        "steps" => QIT_STEPS,
        "type1" => type1,
        "type2" => type2,
        "qit_chirality" => signs,
        "qit_chirality_signed" => length(signs) == 2 && sort(signs) == [-1, 1],
        "no_flip_control" => Dict(
            "type1" => no_flip_type1,
            "type2" => no_flip_type2,
            "qit_chirality" => no_flip_signs,
            "unique_chirality_count" => length(Set(no_flip_signs)),
            "correspondence_collapses" => length(Set(no_flip_signs)) < 2,
        ),
    )
end

function residual_for(igt_signs, qit_signs, correspondence::String)
    if correspondence == "identity"
        return sum(abs(Float64(igt_signs[idx] - qit_signs[idx])) for idx in 1:2)
    elseif correspondence == "swap"
        return abs(Float64(igt_signs[1] - qit_signs[2])) + abs(Float64(igt_signs[2] - qit_signs[1]))
    end
    Inf
end

function test_correspondences(igt_signs, qit_signs)
    identity_residual = residual_for(igt_signs, qit_signs, "identity")
    swap_residual = residual_for(igt_signs, qit_signs, "swap")
    selected = if identity_residual <= TOL && swap_residual > TOL
        "identity"
    elseif swap_residual <= TOL && identity_residual > TOL
        "swap"
    elseif identity_residual <= TOL && swap_residual <= TOL
        "both"
    else
        "none"
    end
    Dict{String,Any}(
        "identity_residual" => Float64(identity_residual),
        "swap_residual" => Float64(swap_residual),
        "selected" => selected,
        "aligned" => selected in ["identity", "swap"],
    )
end

function randomized_winlose_control(cycles, qit_signs, fixed_correspondence::String)
    perms = permutations(collect(1:4))
    rows = Vector{Dict{String,Any}}()
    fixed_matches = 0
    any_matches = 0
    degenerate = 0
    nonidentity_count = 0
    nonidentity_fixed_matches = 0
    for perm in perms
        coords = [VERTEX_COORDS[perm[idx]] for idx in 1:4]
        signs = [chirality_from_cycle(cycle, coords) for cycle in cycles]
        identity_residual = residual_for(signs, qit_signs, "identity")
        swap_residual = residual_for(signs, qit_signs, "swap")
        fixed_residual = residual_for(signs, qit_signs, fixed_correspondence)
        is_identity_perm = perm == collect(1:4)
        if !is_identity_perm
            nonidentity_count += 1
            if fixed_residual <= TOL
                nonidentity_fixed_matches += 1
            end
        end
        fixed_matches += fixed_residual <= TOL ? 1 : 0
        any_matches += min(identity_residual, swap_residual) <= TOL ? 1 : 0
        degenerate += any(sign == 0 for sign in signs) ? 1 : 0
        push!(rows, Dict{String,Any}(
            "permutation_1_based" => perm,
            "is_original" => is_identity_perm,
            "scrambled_igt_chirality" => signs,
            "identity_residual" => Float64(identity_residual),
            "swap_residual" => Float64(swap_residual),
            "fixed_correspondence_residual" => Float64(fixed_residual),
        ))
    end
    decorrelates = nonidentity_fixed_matches < nonidentity_count
    Dict{String,Any}(
        "mode" => "exhaustive_24_vertex_label_scrambles",
        "total_scrambles" => length(perms),
        "nonidentity_scrambles" => nonidentity_count,
        "fixed_correspondence" => fixed_correspondence,
        "fixed_correspondence_match_count" => fixed_matches,
        "nonidentity_fixed_correspondence_match_count" => nonidentity_fixed_matches,
        "any_correspondence_match_count" => any_matches,
        "degenerate_zero_area_count" => degenerate,
        "fixed_correspondence_match_rate" => fixed_matches / length(perms),
        "nonidentity_fixed_correspondence_match_rate" => nonidentity_fixed_matches / max(nonidentity_count, 1),
        "decorrelates" => decorrelates,
        "control_fired" => decorrelates,
        "rows" => rows,
    )
end

function random_sign_assignment_control(qit_signs)
    assignments = [[a, b] for a in [-1, 1] for b in [-1, 1]]
    any_work = 0
    identity_work = 0
    opposite_pairs = 0
    opposite_any_work = 0
    rows = Vector{Dict{String,Any}}()
    for signs in assignments
        identity_residual = residual_for(signs, qit_signs, "identity")
        swap_residual = residual_for(signs, qit_signs, "swap")
        any_ok = min(identity_residual, swap_residual) <= TOL
        identity_ok = identity_residual <= TOL
        any_work += any_ok ? 1 : 0
        identity_work += identity_ok ? 1 : 0
        if signs[1] != signs[2]
            opposite_pairs += 1
            opposite_any_work += any_ok ? 1 : 0
        end
        push!(rows, Dict{String,Any}(
            "random_igt_signs" => signs,
            "identity_residual" => Float64(identity_residual),
            "swap_residual" => Float64(swap_residual),
            "any_correspondence_works" => any_ok,
        ))
    end
    Dict{String,Any}(
        "assignment_count" => length(assignments),
        "any_correspondence_work_count" => any_work,
        "identity_work_count" => identity_work,
        "any_correspondence_work_rate" => any_work / length(assignments),
        "identity_work_rate" => identity_work / length(assignments),
        "opposite_signed_pair_count" => opposite_pairs,
        "opposite_signed_pair_any_correspondence_work_count" => opposite_any_work,
        "random_opposite_signed_pair_always_works_under_one_of_two_correspondences" =>
            opposite_pairs > 0 && opposite_any_work == opposite_pairs,
        "would_also_work" => any_work > 0,
        "uninformative_warning" =>
            "A two-item random opposite-sign assignment also aligns under identity or swap; signed two-ness alone is not enough for admission.",
        "rows" => rows,
    )
end

function parity_block(result::Dict{String,Any})
    if !isfile(JAX_REFERENCE_PATH)
        return Dict{String,Any}(
            "peer_result_path" => JAX_REFERENCE_PATH,
            "peer_available" => false,
            "parity_max_diff" => nothing,
            "worst_key" => nothing,
            "within_1e_9" => false,
            "strict_divergence_gt_1e_6" => false,
            "missing_from_peer" => collect(keys(result["shared_scalars"])),
            "missing_from_self" => String[],
            "diffs" => Dict{String,Any}(),
            "status" => "pending_peer",
        )
    end
    peer = JSON.parsefile(JAX_REFERENCE_PATH)
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sort(collect(setdiff(Set(keys(self_scalars)), Set(keys(peer_scalars)))))
    missing_from_self = sort(collect(setdiff(Set(keys(peer_scalars)), Set(keys(self_scalars)))))
    diffs = Dict{String,Any}()
    max_diff = 0.0
    worst_key = ""
    for key in sort(collect(intersect(Set(keys(self_scalars)), Set(keys(peer_scalars)))))
        diff = abs(Float64(self_scalars[key]) - Float64(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff
            max_diff = diff
            worst_key = key
        end
    end
    within = isempty(missing_from_peer) && isempty(missing_from_self) && max_diff < TOL
    strict_divergence = !isempty(missing_from_peer) || !isempty(missing_from_self) || max_diff > STRICT_STOP_TOL
    Dict{String,Any}(
        "peer_result_path" => JAX_REFERENCE_PATH,
        "peer_available" => true,
        "parity_max_diff" => Float64(max_diff),
        "worst_key" => worst_key,
        "within_1e_9" => within,
        "strict_divergence_gt_1e_6" => strict_divergence,
        "missing_from_peer" => missing_from_peer,
        "missing_from_self" => missing_from_self,
        "diffs" => diffs,
        "status" => within ? "pass" : "fail_closed",
    )
end

function build_result()
    igt = build_igt()
    qit = build_qit()
    cycles = inequivalent_cycles_up_to_rotation(enumerate_directed_hamiltonian_cycles())
    igt_signs = [Int(x) for x in igt["igt_chirality"]]
    qit_signs = [Int(x) for x in qit["qit_chirality"]]
    rosetta = test_correspondences(igt_signs, qit_signs)
    no_flip_rosetta = test_correspondences(igt_signs, qit["no_flip_control"]["qit_chirality"])
    randomized = randomized_winlose_control(cycles, qit_signs, String(rosetta["selected"]))
    random_sign = random_sign_assignment_control(qit_signs)

    fixed_alignment_controls_pass =
        (rosetta["aligned"]::Bool) &&
        (randomized["control_fired"]::Bool) &&
        (qit["no_flip_control"]["correspondence_collapses"]::Bool)
    shared_signed_invariant =
        fixed_alignment_controls_pass &&
        !(random_sign["random_opposite_signed_pair_always_works_under_one_of_two_correspondences"]::Bool)
    rosetta_is_trivial_2ness =
        !shared_signed_invariant &&
        (random_sign["random_opposite_signed_pair_always_works_under_one_of_two_correspondences"]::Bool)

    verdicts = Dict{String,Any}(
        "exactly_two_igt_cycles" => igt["exactly_two_igt_cycles"],
        "igt_chirality_signed" => igt["igt_chirality_signed"],
        "qit_chirality_signed" => qit["qit_chirality_signed"],
        "rosetta_correspondence" => rosetta["selected"],
        "fixed_correspondence_aligns" => rosetta["aligned"],
        "randomized_winlose_control_decorrelates" => randomized["decorrelates"],
        "no_flip_control_collapses" => qit["no_flip_control"]["correspondence_collapses"],
        "random_sign_assignment_would_also_work" => random_sign["would_also_work"],
        "fixed_alignment_controls_pass" => fixed_alignment_controls_pass,
        "shared_signed_invariant" => shared_signed_invariant,
        "rosetta_is_trivial_2ness" => rosetta_is_trivial_2ness,
    )

    shared_scalars = Dict{String,Any}(
        "igt_directed_hamiltonian_cycle_count" => Float64(igt["directed_hamiltonian_cycle_count"]),
        "igt_inequivalent_cycles_up_to_rotation_count" => Float64(igt["inequivalent_directed_cycles_up_to_rotation_count"]),
        "igt_cycle_1_chirality" => Float64(igt_signs[1]),
        "igt_cycle_2_chirality" => Float64(igt_signs[2]),
        "igt_cycle_1_signed_area2" => Float64(igt["cycles"][1]["signed_area2"]),
        "igt_cycle_2_signed_area2" => Float64(igt["cycles"][2]["signed_area2"]),
        "qit_type1_chirality" => Float64(qit_signs[1]),
        "qit_type2_chirality" => Float64(qit_signs[2]),
        "qit_type1_mean_circulation" => Float64(qit["type1"]["mean_circulation"]),
        "qit_type2_mean_circulation" => Float64(qit["type2"]["mean_circulation"]),
        "qit_no_flip_type1_chirality" => Float64(qit["no_flip_control"]["qit_chirality"][1]),
        "qit_no_flip_type2_chirality" => Float64(qit["no_flip_control"]["qit_chirality"][2]),
        "qit_no_flip_unique_chirality_count" => Float64(qit["no_flip_control"]["unique_chirality_count"]),
        "rosetta_identity_residual" => Float64(rosetta["identity_residual"]),
        "rosetta_swap_residual" => Float64(rosetta["swap_residual"]),
        "no_flip_identity_residual" => Float64(no_flip_rosetta["identity_residual"]),
        "no_flip_swap_residual" => Float64(no_flip_rosetta["swap_residual"]),
        "randomized_nonidentity_fixed_match_rate" => Float64(randomized["nonidentity_fixed_correspondence_match_rate"]),
        "randomized_degenerate_zero_area_count" => Float64(randomized["degenerate_zero_area_count"]),
        "random_sign_any_correspondence_work_rate" => Float64(random_sign["any_correspondence_work_rate"]),
        "random_sign_identity_work_rate" => Float64(random_sign["identity_work_rate"]),
        "verdict_exactly_two_igt_cycles" => bool_scalar(verdicts["exactly_two_igt_cycles"]::Bool),
        "verdict_igt_chirality_signed" => bool_scalar(verdicts["igt_chirality_signed"]::Bool),
        "verdict_qit_chirality_signed" => bool_scalar(verdicts["qit_chirality_signed"]::Bool),
        "verdict_fixed_correspondence_aligns" => bool_scalar(verdicts["fixed_correspondence_aligns"]::Bool),
        "verdict_randomized_winlose_control_decorrelates" => bool_scalar(verdicts["randomized_winlose_control_decorrelates"]::Bool),
        "verdict_no_flip_control_collapses" => bool_scalar(verdicts["no_flip_control_collapses"]::Bool),
        "verdict_random_sign_assignment_would_also_work" => bool_scalar(verdicts["random_sign_assignment_would_also_work"]::Bool),
        "verdict_shared_signed_invariant" => bool_scalar(verdicts["shared_signed_invariant"]::Bool),
        "verdict_rosetta_is_trivial_2ness" => bool_scalar(verdicts["rosetta_is_trivial_2ness"]::Bool),
        "numpy_compute_used_flag" => 0.0,
        "promotion_allowed_flag" => 0.0,
    )

    tool_manifest = Dict(
        "Julia LinearAlgebra" => Dict(
            "tried" => true,
            "used" => true,
            "role" => "reference_native_linearalgebra",
            "reason" => "load-bearing for Bloch circulation integration, vector cross products, norms, and signed QIT chirality readouts",
        ),
        "JAX jax.numpy x64" => Dict(
            "tried" => true,
            "used" => false,
            "role" => "peer_mirror_expected",
            "reason" => "supportive peer parity lane read from its result JSON when present; no JAX compute is used inside Julia",
        ),
    )
    tool_depth = Dict(
        "Julia LinearAlgebra" => "load_bearing",
        "JAX jax.numpy x64" => "supportive",
    )

    result = Dict{String,Any}(
        "sim_id" => OBJECT_ID,
        "object_id" => OBJECT_ID,
        "name" => OBJECT_ID,
        "version" => "1.0.0",
        "backend" => "julia",
        "backend_roles" => Dict(
            "julia" => "reference_native_linearalgebra_no_pycall_no_numpy",
            "jax" => "mirror_stress_jnp_x64_no_numpy",
        ),
        "classification" => "scratch_diagnostic",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "PROMOTION_ALLOWED" => false,
        "FORMAL_ADMISSION_ALLOWED" => false,
        "sim_execution_kind" => "nonclassical",
        "sim_class" => "dual_backend_rosetta_convergence_probe",
        "carrier_layer" => "igt_four_ring_and_single_qubit_bloch_engine_chirality",
        "geometry_layer" => "signed_square_orientation_vs_signed_bloch_circulation",
        "claim_ceiling" => "Scratch diagnostic only: independent IGT cycle chirality and QIT engine circulation chirality comparison; no QIT, engine, axis, bridge, or formal admission claim.",
        "allowed_claims" => [
            "IGT side enumerates the four-ring directed Hamiltonian cycles and derives signed orientation from traversal only",
            "QIT side integrates signed Bloch circulation from Type1/Type2 engine dynamics only",
            "Rosetta side tests identity/swap correspondences after independent invariants are computed",
            "controls report whether the sign-only match is informative or trivial",
        ],
        "blocked_consumers" => [
            "QIT_engine_admission",
            "Axis0",
            "bridge",
            "formal_admission",
            "promotion",
            "canonical_engine_evidence",
        ],
        "out_of_scope" => [
            "QIT admission",
            "engine promotion",
            "Axis0",
            "bridge",
            "gravity",
            "win/lose as dynamics",
        ],
        "created_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_path" => @__FILE__,
        "result_path" => RESULT_PATH,
        "peer_result_path" => JAX_REFERENCE_PATH,
        "source_alignment" => Dict(
            "igt_structure_source" => "system_v4/probes/sim_igt_atom_2_structure.py",
            "qit_engine_source" => "system_v5/julia_carrier/engine_noncollapse_probe.jl",
            "genealogy_rule" => "/Users/joshuaeisenhart/wiki/concepts/igt-to-qit-engine-genealogy.md: Sim both independently; do not assert the connection in advance; let the pattern speak.",
        ),
        "tol" => TOL,
        "strict_stop_tol" => STRICT_STOP_TOL,
        "igt" => igt,
        "qit" => qit,
        "rosetta_test" => rosetta,
        "controls" => Dict(
            "randomized_winlose" => randomized,
            "no_flip" => Dict(
                "qit_no_flip" => qit["no_flip_control"],
                "rosetta_under_no_flip" => no_flip_rosetta,
                "control_fired" => qit["no_flip_control"]["correspondence_collapses"],
            ),
            "random_sign_assignment" => random_sign,
        ),
        "verdicts" => verdicts,
        "shared_scalars" => shared_scalars,
        "tools" => ["Julia LinearAlgebra", "JAX jax.numpy x64"],
        "tool_manifest" => tool_manifest,
        "TOOL_MANIFEST" => tool_manifest,
        "tool_integration_depth" => tool_depth,
        "TOOL_INTEGRATION_DEPTH" => tool_depth,
        "numpy_compute_used" => false,
        "jax_x64_enabled" => nothing,
        "divergence_log" => [
            "IGT chirality is derived from directed cycle traversal signed area on the win/lose x WIN/LOSE square.",
            "QIT chirality is derived from integrated Bloch circulation dot((r x rdot), n), using the Type1/Type2 commutator sign from the terrain equations.",
            "The randomized WIN/LOSE control exhaustively scrambles semantic vertex labels and checks whether the fixed correspondence remains correlated.",
            "The no-flip control removes the Weyl sign flip, making both QIT engine circulation signs the same and collapsing the two-element correspondence.",
            "The random-sign baseline is intentionally reported: a two-item opposite-sign random assignment can also align under identity or swap, so sign-only agreement remains uninformative for admission.",
        ],
        "honest_caveat" => "The fixed identity correspondence aligns the independently computed signs, and both requested controls fire, but the random opposite-sign baseline means this scratch probe must not be treated as an admitted shared invariant.",
        "plain_sentence" => "The IGT 2-ring and QIT engine independently align as a signed two-chirality pair under identity, but this sign-only Rosetta test is still vulnerable to trivial two-ness because a random opposite-sign pair would also align under one of the two correspondences.",
    )
    result["parity"] = parity_block(result)
    result["all_pass"] =
        !(result["numpy_compute_used"]::Bool) &&
        (verdicts["exactly_two_igt_cycles"]::Bool) &&
        (verdicts["igt_chirality_signed"]::Bool) &&
        (verdicts["qit_chirality_signed"]::Bool) &&
        (verdicts["randomized_winlose_control_decorrelates"]::Bool) &&
        (verdicts["no_flip_control_collapses"]::Bool) &&
        (result["parity"]["within_1e_9"]::Bool)
    result["stop_condition_fired"] = result["parity"]["strict_divergence_gt_1e_6"]::Bool
    result
end

function main()
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    s = result["shared_scalars"]
    println("rosetta_igt_qit_convergence_probe julia wrote $(RESULT_PATH)")
    println("exactly_two_igt_cycles=$(result["verdicts"]["exactly_two_igt_cycles"]) igt_chirality=[$(s["igt_cycle_1_chirality"]), $(s["igt_cycle_2_chirality"])]")
    println("qit_chirality=[$(s["qit_type1_chirality"]), $(s["qit_type2_chirality"])] correspondence=$(result["verdicts"]["rosetta_correspondence"]) identity_residual=$(s["rosetta_identity_residual"]) swap_residual=$(s["rosetta_swap_residual"])")
    println("controls randomized_decorrelates=$(result["verdicts"]["randomized_winlose_control_decorrelates"]) no_flip_collapses=$(result["verdicts"]["no_flip_control_collapses"]) random_sign_would_work=$(result["verdicts"]["random_sign_assignment_would_also_work"])")
    println("shared_signed_invariant=$(result["verdicts"]["shared_signed_invariant"]) rosetta_is_trivial_2ness=$(result["verdicts"]["rosetta_is_trivial_2ness"]) parity_max_diff=$(result["parity"]["parity_max_diff"]) numpy_compute_used=$(result["numpy_compute_used"])")
    if result["stop_condition_fired"]
        println("STOP_CONDITION_FIRED rosetta_igt_qit_convergence_probe julia")
        exit(1)
    end
end

main()
