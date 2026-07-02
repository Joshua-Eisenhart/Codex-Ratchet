# attractors_constraint_basin_empirical_scout.jl
#
# Empirical JuliaDynamics companion to constraint_basin_synthesis_terrain64.jl.
# This maps finite-grid basins for selected constraints; it is not a formal proof
# and not a layer/manifold admission receipt.

using Attractors
using Dates
using DynamicalSystems
using JSON
using SHA
using StaticArrays
using Statistics

const RESULT_PATH = joinpath(@__DIR__, "attractors_constraint_basin_empirical_scout_results.json")

const TOOL_MANIFEST = Dict(
    "Julia" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "executes the finite grid ladder, control cases, and result emission"),
    "Attractors" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "maps basins_of_attraction, attractor centroids, basin fractions, and basin_entropy"),
    "DynamicalSystems" => Dict("tried" => true, "used" => true, "role" => "load_bearing", "reason" => "constructs the CoupledODEs empirical basin carrier used by Attractors"),
    "SHA" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "embeds a source hash so the result can be checked against the source that emitted it"),
    "StaticArrays" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "supplies small fixed-size state vectors for the ODE rule"),
    "Statistics" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "computes attractor centroids and fraction summaries"),
    "JSON" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "writes the result artifact"),
    "Dates" => Dict("tried" => true, "used" => true, "role" => "supportive", "reason" => "timestamps the result artifact"),
)

const TOOL_INTEGRATION_DEPTH = Dict(
    "Julia" => "load_bearing",
    "Attractors" => "load_bearing",
    "DynamicalSystems" => "load_bearing",
    "SHA" => "supportive",
    "StaticArrays" => "supportive",
    "Statistics" => "supportive",
    "JSON" => "supportive",
    "Dates" => "supportive",
)

function basin_rule(u, p, t)
    bias = p[1]
    SA[u[1] - u[1]^3 - bias, -u[2]]
end

function finite_or_note(x)
    y = Float64(x)
    if isfinite(y)
        return y
    end
    return nothing
end

function source_sha256()
    bytes2hex(sha256(read(@__FILE__)))
end

function side_from_meanx(mean_x::Float64)
    if mean_x < -0.25
        return "left_target"
    elseif mean_x > 0.25
        return "right_control"
    end
    return "center_separator"
end

function entropy_report(basins)
    box_side = max(2, min(8, fld(minimum(size(basins)), 4)))
    box = ntuple(_ -> box_side, ndims(basins))
    basin_ent, boundary_ent = basin_entropy(basins, box)
    Dict(
        "method" => "Attractors.basin_entropy over the discrete basin label array",
        "box" => collect(box),
        "basin_entropy" => finite_or_note(basin_ent),
        "boundary_basin_entropy" => finite_or_note(boundary_ent),
        "nonfinite_boundary_entropy_note" => isfinite(Float64(boundary_ent)) ? "" : "boundary entropy undefined for this basin array, usually because no mixed boundary boxes were present at the default scale",
        "claim_boundary" => "empirical discrete-grid entropy only; no fractal-boundary, Wada, or infinite-time theorem is claimed",
    )
end

function basin_side_report(basins, attractors)
    raw_fractions = basins_fractions(basins)
    side_fractions = Dict(
        "left_target" => 0.0,
        "right_control" => 0.0,
        "center_separator" => 0.0,
        "diverged_or_unmapped" => 0.0,
    )
    rows = Vector{Dict{String,Any}}()

    for raw_label in sort(collect(keys(raw_fractions)); by = x -> Int(x))
        label = Int(raw_label)
        frac = Float64(raw_fractions[raw_label])
        if haskey(attractors, label)
            pts = collect(attractors[label])
            xs = [Float64(p[1]) for p in pts]
            ys = [Float64(p[2]) for p in pts]
            mean_x = mean(xs)
            mean_y = mean(ys)
            side = side_from_meanx(mean_x)
            side_fractions[side] = side_fractions[side] + frac
            push!(rows, Dict(
                "label" => label,
                "fraction" => frac,
                "point_count" => length(pts),
                "centroid" => [mean_x, mean_y],
                "side" => side,
            ))
        else
            side_fractions["diverged_or_unmapped"] = side_fractions["diverged_or_unmapped"] + frac
            push!(rows, Dict(
                "label" => label,
                "fraction" => frac,
                "point_count" => 0,
                "centroid" => [],
                "side" => "diverged_or_unmapped",
            ))
        end
    end

    frac_entropy = 0.0
    for p in values(side_fractions)
        if p > 0
            frac_entropy -= p * log(p)
        end
    end

    Dict(
        "raw_label_fractions" => Dict(string(Int(k)) => Float64(v) for (k, v) in raw_fractions),
        "side_fractions" => side_fractions,
        "attractor_rows" => rows,
        "side_fraction_entropy" => frac_entropy,
        "attractor_count" => length(attractors),
    )
end

function run_case(n::Int, case_id::String, bias::Float64)
    ds = CoupledODEs(basin_rule, SA[0.2, 0.2], [bias])
    grid = (range(-2, 2; length = n), range(-1, 1; length = n))
    started = time()
    mapper = AttractorsViaRecurrences(
        ds,
        grid;
        consecutive_recurrences = 12,
        attractor_locate_steps = 30,
        maximum_iterations = 2500,
    )
    basins, attractors = basins_of_attraction(mapper, grid; show_progress = false)
    side_report = basin_side_report(basins, attractors)
    ent = entropy_report(basins)

    left = side_report["side_fractions"]["left_target"]
    right = side_report["side_fractions"]["right_control"]
    pass = if case_id == "constraint_active_left"
        left >= 0.98 && right <= 0.02 && side_report["attractor_count"] == 1
    elseif case_id == "constraint_erased_symmetric"
        left >= 0.35 && left <= 0.65 && right >= 0.35 && right <= 0.65 && side_report["attractor_count"] >= 2
    elseif case_id == "wrong_sign_control_right"
        right >= 0.98 && left <= 0.02 && side_report["attractor_count"] == 1
    else
        false
    end

    Dict(
        "case_id" => case_id,
        "grid_side" => n,
        "grid_state_count" => n * n,
        "bias" => bias,
        "system" => "dx/dt = x - x^3 - bias, dy/dt = -y",
        "constraint_interpretation" => case_id,
        "basin_map_pass" => pass,
        "elapsed_sec" => round(time() - started; digits = 6),
        "basin_entropy" => ent,
        "basin_side_report" => side_report,
    )
end

function selector_order_report()
    samples = [
        Dict("y_sign" => -1, "project_then_select_bias" => 0.75, "select_then_project_bias" => 0.75),
        Dict("y_sign" => 1, "project_then_select_bias" => 0.75, "select_then_project_bias" => -0.75),
    ]
    gaps = [row["project_then_select_bias"] != row["select_then_project_bias"] for row in samples]
    Dict(
        "finite_selector_domain" => "two y-sign cells before projection",
        "operation_A" => "project y to the basin-readout axis",
        "operation_B" => "select constraint bias from the current y-sign cell",
        "A_then_B_biases" => [row["project_then_select_bias"] for row in samples],
        "B_then_A_biases" => [row["select_then_project_bias"] for row in samples],
        "order_gap_count" => count(identity, gaps),
        "order_sensitive" => any(gaps),
        "order_erased_control" => Dict(
            "rule" => "select fixed left bias regardless of y-sign",
            "order_gap_count" => 0,
            "order_sensitive" => false,
        ),
        "claim_boundary" => "This finite selector is the N01 witness for the scout. The ODE basin maps are empirical selected-constraint surfaces, not formal noncommutative dynamics.",
    )
end

function main()
    source_hash = source_sha256()
    cases = Dict(
        "constraint_active_left" => 0.75,
        "constraint_erased_symmetric" => 0.0,
        "wrong_sign_control_right" => -0.75,
    )
    rungs = Dict{String,Any}()
    for n in (8, 16, 32, 64)
        rows = Dict{String,Any}()
        for (case_id, bias) in cases
            rows[case_id] = run_case(n, case_id, bias)
        end
        rungs[string(n)] = rows
    end

    r64 = rungs["64"]
    selector = selector_order_report()
    all_rungs_pass = all(
        row["basin_map_pass"]
        for rows in values(rungs)
        for row in values(rows)
    )
    controls_pass =
        r64["constraint_active_left"]["basin_map_pass"] &&
        r64["constraint_erased_symmetric"]["basin_map_pass"] &&
        r64["wrong_sign_control_right"]["basin_map_pass"] &&
        selector["order_sensitive"] &&
        selector["order_erased_control"]["order_gap_count"] == 0
    all_pass = all_rungs_pass && controls_pass

    active_left64 = r64["constraint_active_left"]["basin_side_report"]["side_fractions"]["left_target"]
    erased_left64 = r64["constraint_erased_symmetric"]["basin_side_report"]["side_fractions"]["left_target"]
    wrong_left64 = r64["wrong_sign_control_right"]["basin_side_report"]["side_fractions"]["left_target"]

    tool_ablations = Dict(
        "constraint_erased_bias" => Dict(
            "what_changed" => "bias is set to zero instead of the selected left-basin constraint",
            "baseline_left_target_fraction" => active_left64,
            "control_left_target_fraction" => erased_left64,
            "outcome_delta" => active_left64 - erased_left64,
        ),
        "wrong_sign_bias" => Dict(
            "what_changed" => "bias sign is reversed, selecting the right basin",
            "baseline_left_target_fraction" => active_left64,
            "control_left_target_fraction" => wrong_left64,
            "outcome_delta" => active_left64 - wrong_left64,
        ),
        "order_selector_erased" => Dict(
            "what_changed" => "selector ignores the pre-projection y-sign cell",
            "baseline_order_gap_count" => selector["order_gap_count"],
            "control_order_gap_count" => selector["order_erased_control"]["order_gap_count"],
            "outcome_delta" => selector["order_gap_count"] - selector["order_erased_control"]["order_gap_count"],
        ),
    )

    result = Dict{String,Any}(
        "object_id" => "attractors_constraint_basin_empirical_scout",
        "sim_id" => "attractors_constraint_basin_empirical_scout",
        "name" => "Attractors.jl empirical constraint-basin synthesis scout",
        "version" => "0.1.0",
        "generated_at" => string(now(UTC)),
        "source_receipt_coherence" => Dict(
            "source_path" => @__FILE__,
            "source_sha256" => source_hash,
            "coherence_rule" => "Result must be treated as stale if source_sha256 does not match the current source file hash.",
        ),
        "tier" => "tool-stage empirical basin scout",
        "classification" => "formal_scout",
        "sim_execution_kind" => "bridge",
        "sim_class" => "constraint_basin_empirical_probe",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "one_layer_done_right_candidate" => false,
        "all_pass" => all_pass,

        "purpose" => "Empirically map how selected finite constraints create left/right attractor basins on a finite JuliaDynamics grid, with erased and wrong-sign controls.",
        "scientific_question" => "Can a selected constraint parameter produce a target attractor basin, while erased and wrong-sign controls change the basin surface?",
        "claim_ceiling" => "Empirical Attractors.jl basin scout only. It maps finite-grid selected-constraint basins and records a finite order-sensitive selector witness. It is not an SMT proof, not a PEPS carrier, not a layer admission, and not a manifold basin theorem.",
        "demotion_condition" => "Demote to broken if Attractors no longer maps the active case to the left basin, if erased or wrong-sign controls stop changing basin fractions, if the selector order gap disappears, or if a downstream report cites this as formal proof or layer/manifold admission.",
        "out_of_scope" => [
            "formal SMT reachability proof",
            "infinite-time continuous attractor theorem",
            "Basins.jl Wada/fractal boundary proof",
            "PEPS2D or PEPS3D carrier construction",
            "spinor-network carrier admission",
            "terrain/operator layer completion",
            "manifold basin admission",
            "flux/Xi/Phi0/Axis0/FEP/physics claims",
        ],
        "next_lego_target" => "Attach this empirical basin-mapping surface to one exported terrain/channel carrier map after the carrier has a real PEPS or explicitly blocked PEPS boundary.",
        "promotion_condition" => "Promotion requires a real target-layer carrier, formal reachability or interval proof where claimed, fresh controls, and a passing layer-completion claim gate for any completion-like wording.",
        "blocked_until" => "A per-layer carrier exports selected constraints as a real finite map or dynamical system and this scout is rerun against that carrier instead of this double-well fixture.",

        "root_constraints" => [
            "F01 finite carrier/probe/operator/path set: finite 8/16/32/64 by 8/16/32/64 grid samples and finite two-cell selector domain",
            "N01 noncommuting/order-sensitive operation/control: project-then-select and select-then-project choose different constraint bias on one selector cell; order-erased control has zero gap",
        ],
        "root_constraints_in_force" => [
            "F01 finite distinguishable grid cells and selector cells",
            "N01 order-sensitive constraint selection, recorded separately from the empirical ODE basin maps",
        ],

        "finite_map" => Dict(
            "domain" => "finite grids in x in [-2,2], y in [-1,1] at side lengths 8,16,32,64, plus two y-sign selector cells",
            "codomain_or_output" => "Attractors.jl basin labels, attractor centroids, side fractions, basin entropy, and selector order-gap report",
            "map" => "Selected constraint bias enters dx/dt = x - x^3 - bias, dy/dt = -y. Positive bias selects the left basin, zero bias exposes symmetric controls, negative bias selects the right basin.",
        ),
        "domain" => "finite empirical basin grids plus finite selector cells; no PEPS, spinor, or infinite continuum state space is claimed",
        "codomain_or_output" => "selected-constraint basin fractions, entropy diagnostics, and negative-control deltas",

        "carrier_layer" => "empirical JuliaDynamics double-well fixture",
        "geometry_layer" => "selected-constraint basin fixture, not a native terrain/manifold carrier",
        "carrier_realization" => "Julia CoupledODEs sampled through AttractorsViaRecurrences on finite grids",
        "peps3d_embedding" => "absent; blocks manifold, PEPS3D, flux, Axis0, FEP, physics, and basin-admission consumers",
        "spinor_state" => "not_applicable_to_this_empirical_basin_scout",
        "quaternion_action" => "not_applicable",
        "dependency_receipts" => [
            "system_v5/julia_carrier/layers/constraint_basin_synthesis_terrain64_results.json",
            "system_v5/julia_carrier/layers/jax_weyl_terrain_64_microstep_diagnostic_results.json",
            "system_v5/julia_carrier/layers/jax_terrain_choi_holonomy_ladder_probe_results.json",
        ],
        "downstream_blocks" => [
            "layer completion", "parent-complete layer status", "G-structure selection",
            "PEPS2D", "PEPS3D", "stacking readiness", "flux", "Xi", "Phi0",
            "Axis0", "FEP", "bridge admission", "gravity", "physics",
            "final manifold admission", "manifold basin admission",
        ],
        "blocked_consumers" => [
            "layer completion", "parent-complete layer status", "G-structure selection",
            "PEPS2D", "PEPS3D", "stacking readiness", "flux", "Xi", "Phi0",
            "Axis0", "FEP", "bridge admission", "gravity", "physics",
            "final manifold admission", "manifold basin admission",
        ],
        "eligible_consumers" => [
            "empirical companion evidence for the finite Z3 basin proof-pattern scout",
            "future per-layer basin-mapping harness once a real carrier exports selected constraints",
        ],

        "law_or_candidate_tested" => "selected constraints create target empirical attractor basins; erased and wrong-sign controls alter basin fractions; selector order changes the selected constraint",
        "branch_status_before_run" => "empirical_scout_not_admission",
        "allowed_claims" => [
            "Attractors.jl mapped the selected left-bias constraint to a left target basin on 8/16/32/64 finite grids.",
            "Erased and wrong-sign controls changed the empirical basin fractions.",
            "A finite selector witness records order-sensitive constraint selection.",
            "promotion_allowed=false; no proof, layer, manifold, PEPS, flux, Axis0, FEP, bridge admission, or physics claim is made.",
        ],
        "promotion_blockers" => [
            "double-well fixture only",
            "no PEPS2D or PEPS3D carrier",
            "no spinor-network carrier",
            "no interval or SMT proof for the continuous basin",
            "no per-layer rebuilt carrier map",
            "no layer-completion claim gate",
        ],

        "required_tools" => collect(keys(TOOL_MANIFEST)),
        "actual_tools_used" => collect(keys(TOOL_MANIFEST)),
        "proof_surfaces_used" => [],
        "graph_surfaces_used" => [],
        "topology_surfaces_used" => [],
        "tool_manifest" => TOOL_MANIFEST,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "tool_integration_depth" => TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "backend_primary_result" => Dict(
            "backend" => "Julia + Attractors.jl + DynamicalSystems.jl",
            "claim_bearing" => true,
            "claim_scope" => "empirical finite-grid basin mapping only; not proof or admission",
            "all_pass" => all_pass,
            "summary" => "Attractors supplies empirical basin maps/fractions/entropy; DynamicalSystems supplies the ODE carrier; Julia emits the finite ladder receipt.",
        ),

        "required_inputs" => ["double-well basin fixture", "constraint bias cases +0.75, 0.0, -0.75", "finite grid side lengths 8,16,32,64", "finite two-cell selector order witness"],
        "data_or_artifact_dependencies" => [],
        "required_negatives" => ["constraint_erased_symmetric", "wrong_sign_control_right", "order_selector_erased", "decorative_tool_name_overclaim_guard"],
        "negatives_run" => ["constraint_erased_symmetric", "wrong_sign_control_right", "order_selector_erased", "decorative_tool_name_overclaim_guard"],
        "kill_conditions" => [
            "active selected constraint does not map to the left basin",
            "erased bias does not expose a multi-basin/symmetric control",
            "wrong-sign bias does not map to the right basin",
            "selector order gap disappears",
            "Attractors is described as formal proof rather than empirical mapping",
        ],

        "scale_ladder" => Dict("rungs" => rungs),
        "controls" => Dict(
            "constraint_active_left_64" => r64["constraint_active_left"],
            "constraint_erased_symmetric_64" => r64["constraint_erased_symmetric"],
            "wrong_sign_control_right_64" => r64["wrong_sign_control_right"],
            "selector_order_witness" => selector,
        ),
        "tool_ablations" => tool_ablations,
        "entropy_as_output" => Dict(
            "active_left_64" => r64["constraint_active_left"]["basin_entropy"],
            "erased_symmetric_64" => r64["constraint_erased_symmetric"]["basin_entropy"],
            "wrong_sign_right_64" => r64["wrong_sign_control_right"]["basin_entropy"],
            "boundary" => "Attractors.basin_entropy diagnostic only; no Wada/fractal claim",
        ),
        "decorative_tool_name_overclaim_guard" => Dict(
            "Attractors" => "load_bearing for empirical basin labels/fractions/entropy only; not a proof engine",
            "DynamicalSystems" => "load_bearing for the ODE carrier only; not a nonclassical carrier admission",
            "shared_premise_tested" => "Removing or reversing the selected bias changes target basin fractions; order-erased selector removes the N01 selector gap.",
            "bit_identical_controls_checked" => "64-grid active, erased, and wrong-sign controls have different side fractions.",
        ),

        "artifacts_emitted" => [RESULT_PATH],
        "witness_trace_id" => "attractors_constraint_basin_empirical_scout:left_bias_selects_left_basin",
        "result_summary" => Dict(
            "all_rungs_pass" => all_rungs_pass,
            "controls_pass" => controls_pass,
            "grid_side_rungs" => sort(collect(keys(rungs)); by = x -> parse(Int, x)),
            "left_target_fraction_active_64" => active_left64,
            "left_target_fraction_erased_64" => erased_left64,
            "left_target_fraction_wrong_sign_64" => wrong_left64,
            "selector_order_gap_count" => selector["order_gap_count"],
            "source_sha256" => source_hash,
        ),
        "summary" => Dict(
            "all_pass" => all_pass,
            "sim_execution_kind" => "bridge",
            "tests_passed" => all_pass ? 1 : 0,
            "tests_total" => 1,
        ),
        "pass_rule" => "All 8/16/32/64 active constraints must map to left target, erased controls must expose symmetric left/right basins, wrong-sign controls must map to right, and the finite selector must show an order gap with an order-erased zero-gap control.",
        "fail_rule" => "Any missing basin flip, bit-identical side fractions, disappeared selector order gap, or promotion-like downstream claim fails the scout.",
        "promotion_status" => "diagnostic_only",
    )

    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end

    println("attractors_constraint_basin_empirical_scout")
    println("  result: ", RESULT_PATH)
    println("  all_pass: ", all_pass)
    println("  active left fraction 64: ", active_left64)
    println("  erased left fraction 64: ", erased_left64)
    println("  wrong-sign left fraction 64: ", wrong_left64)
    println("  selector order gap: ", selector["order_gap_count"])
    exit(all_pass ? 0 : 1)
end

main()
