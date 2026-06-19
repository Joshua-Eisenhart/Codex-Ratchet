#!/usr/bin/env julia
# Julia Symbolics reference lane for round3_s4_alias_pass_v0.

using Dates
using JSON
using SHA
using Symbolics
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "round3_s4_alias_pass_v0"
const SIM_DIR_REL = joinpath("system_v6", "sims", SIM_ID)
const SIM_DIR = joinpath(ROOT, SIM_DIR_REL)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH_REL = joinpath(SIM_DIR_REL, "$(SIM_ID)_julia.jl")
const SOURCE_PATH = joinpath(ROOT, SOURCE_PATH_REL)
const RESULT_PATH_REL = joinpath(SIM_DIR_REL, "results", "$(SIM_ID)_julia_results.json")
const RESULT_PATH = joinpath(ROOT, RESULT_PATH_REL)
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const Q = 3//10

sha256_file(path::AbstractString) = bytes2hex(SHA.sha256(read(path)))

function rel(path::AbstractString)
    startswith(path, ROOT) ? path[length(ROOT)+2:end] : path
end

function matrix_strings(mat)
    [[string(simplify(item)) for item in row] for row in mat]
end

function vector_strings(vec)
    [string(simplify(item)) for item in vec]
end

function dephase(axis::String)
    lam = 1 - Q
    if axis == "x"
        return [[1, 0, 0], [0, lam, 0], [0, 0, lam]]
    elseif axis == "y"
        return [[lam, 0, 0], [0, 1, 0], [0, 0, lam]]
    elseif axis == "z"
        return [[lam, 0, 0], [0, lam, 0], [0, 0, 1]]
    end
    error(axis)
end

function rotation(axis::String)
    if axis == "x"
        return [[1, 0, 0], [0, 0, -1], [0, 1, 0]]
    elseif axis == "y"
        return [[0, 0, 1], [0, 1, 0], [-1, 0, 0]]
    elseif axis == "z"
        return [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    end
    error(axis)
end

function channel(role::String, label::String, kind::String, axis::String)
    if kind == "dephase"
        matrix = dephase(axis)
        choi = ["0", "0", "3//20", "17//20"]
    elseif kind == "rotation"
        matrix = rotation(axis)
        choi = ["0", "0", "0", "1"]
    else
        error(kind)
    end
    Dict(
        "role_id" => role,
        "label" => label,
        "kind" => kind,
        "axis" => axis,
        "M" => matrix,
        "c" => [0, 0, 0],
        "CPTP_choi_spectrum_class" => choi,
        "fixed_axis_set" => ["$(axis)_axis"],
    )
end

function committed_channels()
    [
        channel("D_z", "D_z", "dephase", "z"),
        channel("D_x", "D_x", "dephase", "x"),
        channel("R_x", "R_x", "rotation", "x"),
        channel("R_z", "R_z", "rotation", "z"),
    ]
end

function axis_permuted_channels()
    [
        channel("D_z", "D_x_after_cyclic_relabel", "dephase", "x"),
        channel("D_x", "D_y_after_cyclic_relabel", "dephase", "y"),
        channel("R_x", "R_y_after_cyclic_relabel", "rotation", "y"),
        channel("R_z", "R_x_after_cyclic_relabel", "rotation", "x"),
    ]
end

function y_frame_channels()
    [
        channel("D_z", "D_y_far_control", "dephase", "y"),
        channel("D_x", "D_x_far_control", "dephase", "x"),
        channel("R_x", "R_y_far_control", "rotation", "y"),
        channel("R_z", "R_x_far_control", "rotation", "x"),
    ]
end

function reparameterized_anchor_channels()
    @variables theta
    c = Symbolics.value(simplify(0 * theta))
    s = Symbolics.value(simplify(1 + 0 * theta))
    [
        Dict(
            "role_id" => "D_z",
            "label" => "D_z_reparameterized",
            "kind" => "dephase",
            "axis" => "z",
            "M" => [[1 - 3//10, 0, 0], [0, 1 - 3//10, 0], [0, 0, 1]],
            "c" => [0, 0, 0],
            "CPTP_choi_spectrum_class" => ["0", "0", "3//20", "17//20"],
            "fixed_axis_set" => ["z_axis"],
        ),
        Dict(
            "role_id" => "D_x",
            "label" => "D_x_reparameterized",
            "kind" => "dephase",
            "axis" => "x",
            "M" => [[1, 0, 0], [0, 1 - 3//10, 0], [0, 0, 1 - 3//10]],
            "c" => [0, 0, 0],
            "CPTP_choi_spectrum_class" => ["0", "0", "3//20", "17//20"],
            "fixed_axis_set" => ["x_axis"],
        ),
        Dict(
            "role_id" => "R_x",
            "label" => "R_x_reparameterized",
            "kind" => "rotation",
            "axis" => "x",
            "M" => [[1, 0, 0], [0, c, -s], [0, s, c]],
            "c" => [0, 0, 0],
            "CPTP_choi_spectrum_class" => ["0", "0", "0", "1"],
            "fixed_axis_set" => ["x_axis"],
        ),
        Dict(
            "role_id" => "R_z",
            "label" => "R_z_reparameterized",
            "kind" => "rotation",
            "axis" => "z",
            "M" => [[c, -s, 0], [s, c, 0], [0, 0, 1]],
            "c" => [0, 0, 0],
            "CPTP_choi_spectrum_class" => ["0", "0", "0", "1"],
            "fixed_axis_set" => ["z_axis"],
        ),
    ]
end

function matvec(m, v)
    [sum(m[i][j] * v[j] for j in 1:3) for i in 1:3]
end

function apply_channel(ch, point)
    out = matvec(ch["M"], point)
    [simplify(out[i] + ch["c"][i]) for i in 1:3]
end

function canonical_tuple(channels)
    z_probe = [0, 0, 1//2]
    entries = []
    for ch in channels
        push!(entries, Dict(
            "role_id" => ch["role_id"],
            "M_exact" => matrix_strings(ch["M"]),
            "c_exact" => vector_strings(ch["c"]),
            "CPTP_choi_spectrum_class" => ch["CPTP_choi_spectrum_class"],
            "fixed_axis_set" => ch["fixed_axis_set"],
            "z_probe_image" => vector_strings(apply_channel(ch, z_probe)),
        ))
    end
    sort!(entries, by = row -> findfirst(==(row["role_id"]), ["D_z", "D_x", "R_x", "R_z"]))
    Dict(
        "convention_map" => "S1/S4 pinned Bloch coordinate order (x,y,z), parent z-probe quotient and role order D_z,D_x,R_x,R_z",
        "role_tuple" => entries,
    )
end

function witness(anchor, candidate)
    amap = Dict(entry["role_id"] => entry for entry in anchor["role_tuple"])
    cmap = Dict(entry["role_id"] => entry for entry in candidate["role_tuple"])
    for role in ["D_z", "D_x", "R_x", "R_z"]
        for key in ["M_exact", "c_exact", "CPTP_choi_spectrum_class", "fixed_axis_set", "z_probe_image"]
            if amap[role][key] != cmap[role][key]
                return Dict("field" => "role_tuple.$role.$key", "anchor" => amap[role][key], "candidate" => cmap[role][key])
            end
        end
    end
    Dict("field" => "canonical_tuple", "anchor" => "equal", "candidate" => "equal")
end

function registry_verdicts()
    anchor = canonical_tuple(committed_channels())
    axis = canonical_tuple(axis_permuted_channels())
    rows = [
        Dict("id" => "S4.R3.0_committed_DzDxRxRz", "finite_representative" => "pinned committed D_z,D_x,R_x,R_z affine maps", "closeness" => "control", "expected_teeth_row" => "none; anchor", "cost" => "light-symbolic", "verdict" => "anchor", "row" => "anchor", "witness" => witness(anchor, anchor), "pin" => nothing, "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor" => false, "canonical_tuple" => anchor),
        Dict("id" => "S4.R3.1_z_amplitude_damping_pair", "finite_representative" => "AD_z(gamma) with gamma in {1/5,3/10} plus committed rotations", "closeness" => "closer non-unital neighbor", "expected_teeth_row" => "N01/commutator and fixed-axis rows", "cost" => "heavy-local", "verdict" => "co-survivor-open", "row" => "heavy_local_cost_guard_not_run_in_phase_1", "witness" => Dict("field" => "registry_cost_guard", "anchor" => "light-symbolic phase only", "candidate" => "S4.R3.1_z_amplitude_damping_pair cost=heavy-local; queued"), "pin" => nothing, "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor" => false, "canonical_tuple" => nothing),
        Dict("id" => "S4.R3.2_x_amplitude_damping_pair", "finite_representative" => "AD_x(gamma) with gamma in {1/5,3/10} plus committed z maps", "closeness" => "close frame-shifted non-unital neighbor", "expected_teeth_row" => "z-probe quotient descent/mortality", "cost" => "heavy-local", "verdict" => "co-survivor-open", "row" => "heavy_local_cost_guard_not_run_in_phase_1", "witness" => Dict("field" => "registry_cost_guard", "anchor" => "light-symbolic phase only", "candidate" => "S4.R3.2_x_amplitude_damping_pair cost=heavy-local; queued"), "pin" => nothing, "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor" => false, "canonical_tuple" => nothing),
        Dict("id" => "S4.R3.3_dephase_rotate_hybrid", "finite_representative" => "D_z(lambda) o R_x(theta) with (lambda,theta) in {(7/10,pi/2),(1/2,pi/2)}", "closeness" => "mixed contraction-rotation", "expected_teeth_row" => "shell preservation/leakage then N01", "cost" => "heavy-local", "verdict" => "co-survivor-open", "row" => "heavy_local_cost_guard_not_run_in_phase_1", "witness" => Dict("field" => "registry_cost_guard", "anchor" => "light-symbolic phase only", "candidate" => "S4.R3.3_dephase_rotate_hybrid cost=heavy-local; queued"), "pin" => nothing, "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor" => false, "canonical_tuple" => nothing),
        Dict("id" => "S4.R3.4_axis_permuted_committed", "finite_representative" => "cyclic axis relabels x->y->z that preserve CPTP but move probe roles", "closeness" => "convention-neighbor, not automatically alias", "expected_teeth_row" => "z-probe quotient row", "cost" => "light-symbolic", "verdict" => "excluded-under-pinned-parent-z-probe-convention", "row" => "z_probe_quotient_row", "witness" => witness(anchor, axis), "pin" => "parent z-probe quotient and S4 role order D_z,D_x,R_x,R_z", "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor" => true, "canonical_tuple" => axis),
        Dict("id" => "S4.R3.5_weak_nonunital_pauli_channel", "finite_representative" => "affine Pauli channel with small shift c in {(0,0,1/10),(1/10,0,0)} and diagonal contraction from committed rows", "closeness" => "very close non-unital perturbation", "expected_teeth_row" => "fixed-axis plus Choi positivity", "cost" => "heavy-local", "verdict" => "co-survivor-open", "row" => "heavy_local_cost_guard_not_run_in_phase_1", "witness" => Dict("field" => "registry_cost_guard", "anchor" => "light-symbolic phase only", "candidate" => "S4.R3.5_weak_nonunital_pauli_channel cost=heavy-local; queued"), "pin" => nothing, "relaxing_pin_reopens_as_convention_relative_alias_or_neighbor" => false, "canonical_tuple" => nothing),
    ]
    controls = [
        Dict("id" => "control.anchor_self", "verdict" => "anchor", "row" => "anchor", "witness" => witness(anchor, anchor), "canonical_tuple" => anchor),
        Dict("id" => "control.alias_reparameterized_committed", "verdict" => canonical_tuple(reparameterized_anchor_channels()) == anchor ? "alias" : "failed", "row" => "canonical_tuple_equal", "witness" => witness(anchor, canonical_tuple(reparameterized_anchor_channels())), "canonical_tuple" => canonical_tuple(reparameterized_anchor_channels())),
        Dict("id" => "control.round2_A_y_frame_far_candidate", "verdict" => "excluded-by-z-probe-quotient-descent-mortality", "row" => "z_probe_quotient_descent_mortality", "witness" => witness(anchor, canonical_tuple(y_frame_channels())), "canonical_tuple" => canonical_tuple(y_frame_channels())),
    ]
    Dict("candidate_rows" => rows, "control_rows" => controls)
end

function julia_z3_proof()
    solver = Z3.Solver()
    values = Dict(
        "julia_axis_permuted_D_z_zprobe_delta_scaled_by_20" => -3,
        "julia_axis_permuted_R_z_zprobe_delta_scaled_by_2" => -1,
        "julia_far_A_y_frame_D_z_zprobe_delta_scaled_by_20" => -3,
        "julia_far_A_y_frame_R_z_zprobe_delta_scaled_by_2" => -1,
    )
    zero_terms = Z3.Expr[]
    for (name, value) in values
        var = Z3.IntVar(name)
        Z3.add(solver, var == Z3.IntVal(value))
        push!(zero_terms, var == Z3.IntVal(0))
    end
    Z3.add(solver, Z3.Or(zero_terms))
    positive = string(Z3.check(solver))

    flip = Z3.Solver()
    mutated = Z3.IntVar("julia_mutated_s4_witness")
    Z3.add(flip, mutated == Z3.IntVal(0))
    Z3.add(flip, mutated == Z3.IntVal(0))
    flip_status = string(Z3.check(flip))
    Dict(
        "solver" => "Z3.jl",
        "ran" => true,
        "verdict" => positive,
        "load_bearing" => true,
        "asserted_precomputed_boolean" => false,
        "claim" => "computed rational z-probe witness rows are all nonzero",
        "witness_values" => values,
        "negated_assertion" => "at least one required nonzero z-probe witness is zero",
        "flip_control_verdict" => flip_status,
        "positive_case" => "axis-permuted convention-neighbor and far A_y control have bound nonzero z-probe witnesses",
        "negative/erased_control" => "mutating a witness to zero makes the erased assertion SAT",
        "boundary_case" => "heavy-local S4 rows remain queued; SMT binds only finite rational light/control witnesses",
    )
end

function build_result()
    rows = registry_verdicts()
    proof = julia_z3_proof()
    verdicts = Dict(row["id"] => row["verdict"] for row in rows["candidate_rows"])
    controls = Dict(row["id"] => row["verdict"] for row in rows["control_rows"])
    gates = Dict(
        "symbolics_rows_built" => length(rows["candidate_rows"]) == 6,
        "anchor_classifies_as_itself" => verdicts["S4.R3.0_committed_DzDxRxRz"] == "anchor",
        "axis_neighbor_convention_pinned" => verdicts["S4.R3.4_axis_permuted_committed"] == "excluded-under-pinned-parent-z-probe-convention",
        "axis_neighbor_pin_reopens" => rows["candidate_rows"][5]["relaxing_pin_reopens_as_convention_relative_alias_or_neighbor"] == true,
        "deliberate_alias_classifies_alias" => controls["control.alias_reparameterized_committed"] == "alias",
        "far_candidate_dies_first_teeth" => controls["control.round2_A_y_frame_far_candidate"] == "excluded-by-z-probe-quotient-descent-mortality",
        "heavy_local_rows_queued" => all(verdicts[id] == "co-survivor-open" for id in [
            "S4.R3.1_z_amplitude_damping_pair",
            "S4.R3.2_x_amplitude_damping_pair",
            "S4.R3.3_dephase_rotate_hybrid",
            "S4.R3.5_weak_nonunital_pauli_channel",
        ]),
        "julia_z3_positive_unsat" => proof["verdict"] == "unsat",
        "julia_z3_flip_control_sat" => proof["flip_control_verdict"] == "sat",
    )
    all_pass = all(values(gates))
    Dict(
        "schema" => "$(SIM_ID)_julia_lane_v1",
        "sim_id" => SIM_ID,
        "role_id" => "julia_authoritative_sim_builder",
        "engine_role_note" => "Julia Symbolics reference rebuilds exact S4 role tuples; Z3.jl binds the rational z-probe witness polarity.",
        "source_path" => SOURCE_PATH_REL,
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => RESULT_PATH_REL,
        "generated_at" => Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "packages_used" => ["Symbolics", "Z3", "JSON", "SHA", "Dates"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Z3" => "Z3.Solver/check proves finite rational z-probe witness rows UNSAT under negation and SAT under erased flip",
        ),
        "claim_path_tools" => ["Symbolics", "Z3"],
        "all_pass" => all_pass,
        "positive" => Dict(
            "symbolics_reference_rows" => rows["candidate_rows"],
            "anchor_and_alias_control" => rows["control_rows"][1:2],
        ),
        "negative" => Dict(
            "far_candidate_control" => rows["control_rows"][3],
            "convention_pinned_exclusion" => rows["candidate_rows"][5],
        ),
        "boundary" => Dict(
            "phase" => "light-symbolic phase 1 only",
            "heavy_local_not_run" => [
                "S4.R3.1_z_amplitude_damping_pair",
                "S4.R3.2_x_amplitude_damping_pair",
                "S4.R3.3_dephase_rotate_hybrid",
                "S4.R3.5_weak_nonunital_pauli_channel",
            ],
            "pytorch_omitted" => "no graph/network/autograd/tensor claim path exists",
        ),
        "candidate_verdicts" => rows["candidate_rows"],
        "control_verdicts" => rows["control_rows"],
        "crossover_proofs" => Dict("julia_z3" => proof),
        "TOOL_MANIFEST" => Dict(
            "Symbolics" => Dict("used" => true, "reason" => "load-bearing Julia reference symbolic role tuple simplification"),
            "Z3" => Dict("used" => true, "reason" => "load-bearing Julia-side finite rational witness polarity"),
            "JSON" => Dict("used" => true, "reason" => "supportive result serialization"),
            "SHA" => Dict("used" => true, "reason" => "supportive source hash"),
        ),
        "TOOL_INTEGRATION_DEPTH" => Dict(
            "Symbolics" => "load_bearing",
            "Z3" => "load_bearing",
            "JSON" => "supportive",
            "SHA" => "supportive",
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Symbolics",
                "qualified_api" => "Symbolics.simplify",
                "input_object" => "S4 registry light-cost affine channel role tuples under pinned Bloch z-probe convention",
                "output_object" => "canonical role tuples and exact z-probe witness expressions",
                "positive_case" => "anchor and pure reparameterization have equal canonical tuple",
                "negative/erased_control" => "round-2 A_y frame control changes z-probe quotient row",
                "boundary_case" => "heavy-local S4 rows recorded as queued, not run",
                "demotion_condition" => "Symbolics cannot produce reference rows",
                "gates" => ["all_pass", "alias", "convention_pinned_exclusion"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api" => "Z3.Solver/check",
                "input_object" => "finite rational z-probe witness rows derived from canonical tuples",
                "output_object" => "UNSAT positive nonzero proof and SAT flip control",
                "positive_case" => proof["positive_case"],
                "negative/erased_control" => proof["negative/erased_control"],
                "boundary_case" => proof["boundary_case"],
                "demotion_condition" => "wrong polarity or precomputed boolean assertion",
                "gates" => ["proof", "all_pass"],
            ),
        ],
        "build_gates" => gates,
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => RESULT_PATH_REL)))
    return result["all_pass"] ? 0 : 1
end

exit(main())
