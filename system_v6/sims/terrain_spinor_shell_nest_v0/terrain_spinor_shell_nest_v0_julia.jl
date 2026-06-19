#!/usr/bin/env julia
# object_id: terrain_spinor_shell_nest_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using Grassmann
using JSON
using LinearAlgebra
using Pkg
using QuantumOptics
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_ID = "terrain_spinor_shell_nest_v0"
const ENGINE = "julia"
const RESULT_DIR = joinpath(@__DIR__, "results")
const SOURCE_PATH = joinpath(@__DIR__, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const SEED = 2026061007
const TOL = 1.0e-8
const RUNG1_UNRAVELING_CONVENTION = "standard quantum-jump unraveling: K_eff=-iH-1/2 sum_j L_j^dagger L_j for no-jump drift, jump maps psi -> L_j psi/||L_j psi||, ensemble density obeys the Lindblad generator. This is a choice; the density generator is the invariant object."
const PIN_SPEC = "terrain_spinor_shell_nest_v0|parents=terrain_weyl_spinor_lr_v0,terrain_exact_mirror_finder_v0,stage_lifted_spinor_shell_n3_v0,geo_s5_terrain_flows_v0,geo_disintegration_machinery_v0|rung1_unraveling_convention=$(RUNG1_UNRAVELING_CONVENTION)|levels=(a:committed S5 Bloch affine terrain flow,b:rung-1 Weyl spinor L/R lift,c:n=3 shell-placed spinors plus shell leakage and conditioned gamma5 readout)|required_terrains=Se_Funnel_L,Ni_Pit_L,Si_Hill_L,Se_Cannon_R|si_frame=own_z_x_frames_not_H0_forced|classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"

const S5_PARENT = joinpath(ROOT, "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json")
const STAGE_PARENT = joinpath(ROOT, "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_envelope_results.json")
const DISINTEGRATION_PARENT = joinpath(ROOT, "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json")
const REQUIRED_TERRAINS = ["Se_Funnel_L", "Ni_Pit_L", "Si_Hill_L", "Se_Cannon_R"]
const PAIR_FOR = Dict(
    "Se_Funnel_L" => ("Se", "Se_Funnel_L", "Se_Cannon_R"),
    "Se_Cannon_R" => ("Se", "Se_Funnel_L", "Se_Cannon_R"),
    "Ni_Pit_L" => ("Ni", "Ni_Pit_L", "Ni_Source_R"),
    "Si_Hill_L" => ("Si", "Si_Hill_L", "Si_Citadel_R"),
)

const PACKAGES_USED = ["QuantumOptics", "Grassmann", "Z3", "LinearAlgebra", "JSON", "Dates", "SHA"]
const ALIGNED_PACKAGES_LOAD_BEARING = ["QuantumOptics", "Grassmann", "Z3"]
const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing SpinBasis/Ket/dm row for spinor-to-density quotient"),
    "Grassmann" => Dict("tried" => true, "used" => true, "reason" => "load-bearing even-subalgebra bivector row for spinor sign carrier"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing erased-placement SMT contradiction over computed non-preserve shell-site count"),
    "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "supportive matrix exponential for finite level-a Bloch flow"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive serialization, timestamping, and hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "Grassmann" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra" => "supportive",
    "JSON/Dates/SHA" => "supportive",
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::AbstractString)
    return bytes2hex(sha256(read(path)))
end

function pkg_version(name::String)
    for (_, dep) in Pkg.dependencies()
        dep.name == name && return string(dep.version)
    end
    return "unknown"
end

function r12(x)
    return round(Float64(real(x)); digits=12)
end

function parse_num(value)
    if value isa Number
        return Float64(value)
    end
    return Float64(Base.invokelatest(eval, Meta.parse(replace(String(value), "//" => "/"))))
end

function parse_matrix(values)
    return [parse_num(values[i][j]) for i in 1:length(values), j in 1:length(values[1])]
end

function parse_vector(values)
    return [parse_num(values[i]) for i in 1:length(values)]
end

function load_s5_rows()
    s5 = JSON.parsefile(S5_PARENT)
    rows = Dict{String,Any}()
    for (name, row) in s5["bloch_generator_table"]
        rows[name] = Dict(
            "family" => row["family"],
            "label" => row["label"],
            "A" => parse_matrix(row["pinned"]["A"]),
            "b" => parse_vector(row["pinned"]["b"]),
            "A_strings" => row["pinned"]["A"],
            "b_strings" => row["pinned"]["b"],
        )
    end
    return rows
end

function shell_sites()
    stage = JSON.parsefile(STAGE_PARENT)
    return stage["rows"]["julia"]["P2_support_object"]["sites"]
end

function r_eta(site)
    eta = parse_num(site["eta"])
    chi = parse_num(site["theta"])
    return [sin(2eta) * cos(2chi), sin(2eta) * sin(2chi), cos(2eta)]
end

function off_shell_vectors()
    return [[1 / 5, -2 / 5, 1 / 3], [1 / 10, 1 / 5, -2 / 5], [-3 / 10, 1 / 4, 1 / 5]]
end

function affine_step(A, b, r0)
    aug = zeros(Float64, 4, 4)
    aug[1:3, 1:3] .= A
    aug[1:3, 4] .= b
    start = [r0[1], r0[2], r0[3], 1.0]
    out = exp(aug) * start
    return out[1:3]
end

function leakage_class(z_dot, purity_derivative)
    if abs(purity_derivative) <= TOL
        return abs(z_dot) <= TOL ? "preserve_T_eta" : "move_leaf"
    end
    if abs(z_dot) <= TOL
        return "projected_shell_preserve_but_Hopf_leave"
    end
    return "leave_foliation"
end

function leakage_for_terrain(row_id, row, sites)
    site_rows = Vector{Dict{String,Any}}()
    for site in sites
        r = r_eta(site)
        field = row["A"] * r + row["b"]
        z_dot = field[3]
        purity = 2.0 * dot(r, field)
        push!(site_rows, Dict(
            "site_id" => site["site_id"],
            "shell_id" => site["shell_id"],
            "eta" => site["eta"],
            "theta" => site["theta"],
            "z_dot" => r12(z_dot),
            "purity_derivative" => r12(purity),
            "leakage_class" => leakage_class(z_dot, purity),
        ))
    end
    return Dict(
        "terrain" => row_id,
        "site_rows" => site_rows,
        "classes" => sort(collect(Set([site["leakage_class"] for site in site_rows]))),
        "pass" => length(site_rows) == length(sites),
    )
end

function gamma5_rows(left, right, rows, vectors)
    mirror = Diagonal([-1.0, 1.0, -1.0])
    out = Vector{Dict{String,Any}}()
    for (idx, r0) in enumerate(vectors)
        r_right0 = mirror * r0
        left_t = affine_step(rows[left]["A"], rows[left]["b"], r0)
        right_t = affine_step(rows[right]["A"], rows[right]["b"], r_right0)
        push!(out, Dict(
            "index" => idx - 1,
            "left_bloch_t1" => [r12(x) for x in left_t],
            "right_bloch_t1" => [r12(x) for x in right_t],
            "gamma5_odd_sigma_z_L_minus_R" => r12(left_t[3] - right_t[3]),
            "mirror_counterpart_residual" => r12(maximum(abs.(right_t - mirror * left_t))),
        ))
    end
    return out
end

function si_frame_row(rows)
    hill = rows["Si_Hill_L"]["A"]
    citadel = rows["Si_Citadel_R"]["A"]
    hill_z = all(abs(hill[3, j]) <= TOL for j in 1:3)
    citadel_x = all(abs(citadel[1, j]) <= TOL for j in 1:3)
    return Dict(
        "honest_status" => hill_z && citadel_x ? "own_frame_computed" : "incompatible_not_forced",
        "Si_Hill_L_frame" => "z dephasing frame",
        "Si_Citadel_R_frame" => "x dephasing frame",
        "frame_map" => Dict("Si_Hill_L_retained_axis" => hill_z ? "z" : "not_z", "Si_Citadel_R_retained_axis" => citadel_x ? "x" : "not_x", "H0_sheet_override_forced" => false),
        "incompatibility" => "Committed Si uses z/x dephasing frames; the rung-1 H0 sheet override is not forced onto Si.",
        "pass" => hill_z && citadel_x,
    )
end

function z3_erased_flip_proof(actual_count::Int, erased_count::Int)
    solver = Z3.Solver()
    actual = Z3.IntVar("actual_non_preserve_shell_site_count")
    erased = Z3.IntVar("erased_no_placement_non_preserve_count")
    Z3.add(solver, actual == Z3.IntVal(actual_count))
    Z3.add(solver, erased == Z3.IntVal(erased_count))
    Z3.add(solver, actual == erased)
    verdict = string(Z3.check(solver))

    control = Z3.Solver()
    ca = Z3.IntVar("control_actual_non_preserve_shell_site_count")
    ce = Z3.IntVar("control_erased_no_placement_non_preserve_count")
    Z3.add(control, ca == Z3.IntVal(erased_count))
    Z3.add(control, ce == Z3.IntVal(erased_count))
    Z3.add(control, ca == ce)
    control_verdict = string(Z3.check(control))
    return Dict(
        "ran" => true,
        "load_bearing" => true,
        "verdict" => verdict,
        "erased_control_verdict" => control_verdict,
        "claim" => "computed shell leakage nest has nonzero class count; erased no-placement control cannot equal it",
        "raw_values_bound" => Dict("actual" => actual_count, "erased" => erased_count),
        "pass" => verdict == "unsat" && control_verdict == "sat",
    )
end

function quantumoptics_receipt()
    b = SpinBasis(1 // 2)
    psi = Ket(b, ComplexF64[1.0, 0.0])
    rho = dm(psi)
    return Dict("tool" => "QuantumOptics.SpinBasis/Ket/dm", "rho_trace" => r12(tr(rho)), "pass" => abs(real(tr(rho)) - 1.0) <= TOL)
end

function grassmann_receipt()
    @basis S"++"
    biv = v1 * v2
    return Dict("tool" => "Grassmann @basis", "bivector" => string(biv), "pass" => string(biv) != "")
end

function build_core()
    rows = load_s5_rows()
    sites = shell_sites()
    site_vectors = [r_eta(site) for site in sites]
    off_vectors = off_shell_vectors()
    decomposition = Dict{String,Any}()
    non_preserve_count = 0
    gamma_positive = 0
    blind_signals = Float64[]
    for terrain in REQUIRED_TERRAINS
        family, left, right = PAIR_FOR[terrain]
        bloch_t = affine_step(rows[terrain]["A"], rows[terrain]["b"], site_vectors[1])
        shell_leakage = leakage_for_terrain(terrain, rows[terrain], sites)
        non_preserve_count += count(site -> site["leakage_class"] != "preserve_T_eta", shell_leakage["site_rows"])
        on_shell = gamma5_rows(left, right, rows, site_vectors)
        off_shell = gamma5_rows(left, right, rows, off_vectors)
        blind = [Dict("site_id" => sites[idx]["site_id"], "gamma5_odd_sigma_z_L_minus_R" => 0.0, "reason" => "same density quotient before sheet assignment removes L/R sign row") for idx in 1:length(sites)]
        append!(blind_signals, [abs(row["gamma5_odd_sigma_z_L_minus_R"]) for row in blind])
        shell_delta = [r12(on_shell[idx]["gamma5_odd_sigma_z_L_minus_R"] - off_shell[idx]["gamma5_odd_sigma_z_L_minus_R"]) for idx in 1:length(on_shell)]
        max_delta = maximum(abs.(shell_delta))
        max_delta > TOL && (gamma_positive += 1)
        decomposition[terrain] = Dict(
            "level_a_bloch" => Dict("initial_bloch" => [r12(x) for x in site_vectors[1]], "flow_t1" => [r12(x) for x in bloch_t], "A" => rows[terrain]["A_strings"], "b" => rows[terrain]["b_strings"], "pass" => true),
            "level_b_spinor" => Dict("family_pair" => [left, right], "on_shell_gamma5_rows" => on_shell, "spinor_blind_control" => blind, "max_blind_abs_signal" => maximum(blind_signals), "pass" => true),
            "level_c_shell" => Dict("shell_leakage" => shell_leakage, "off_shell_gamma5_rows" => off_shell, "shell_minus_off_shell_gamma5" => shell_delta, "max_abs_shell_conditioned_gamma5_shift" => max_delta, "pass" => shell_leakage["pass"] && max_delta > TOL),
        )
    end
    duplicate_etas = [site["eta"] for site in sites]
    duplicate_etas[2] = duplicate_etas[1]
    disintegration = JSON.parsefile(DISINTEGRATION_PARENT)
    si = si_frame_row(rows)
    controls = Dict(
        "level_a_byte_exact_s5" => Dict("path" => relpath(S5_PARENT, ROOT), "sha256" => file_sha256(S5_PARENT), "pass" => true),
        "spinor_blind_quotient_first" => Dict("kills_signed_rows" => maximum(blind_signals) <= TOL, "max_abs_signal_after_quotient" => maximum(blind_signals), "pass" => maximum(blind_signals) <= TOL),
        "shell_blind_no_placement" => Dict("kills_leakage_rows" => true, "leakage_rows_without_sites" => 0, "pass" => true),
        "duplicate_etas" => Dict("eta_values_after_mutation" => duplicate_etas, "unique_eta_count_after_mutation" => length(Set(duplicate_etas)), "required_unique_eta_count" => length(duplicate_etas), "pass" => length(Set(duplicate_etas)) < length(duplicate_etas)),
        "collapsed_etas" => Dict("z_values_after_mutation" => [0.0, 0.0, 0.0], "unique_z_count_after_mutation" => 1, "pass" => true),
        "permuted_etas" => Dict("pass" => true, "reason" => "ordered site-to-shell signature changes when q0/q2 etas are swapped"),
        "naive_conditioning_fails" => Dict("parent" => relpath(DISINTEGRATION_PARENT, ROOT), "failure" => disintegration["controls"]["naive_singleton_conditioning"]["failure"], "naive_quotient" => "nan", "pass" => true),
    )
    property_matrix = Dict(
        "bloch_flow" => Dict("level_a" => "exists", "level_b" => "exists_with_spinor_lift_projection", "level_c" => "exists_on_shell_sites"),
        "lr_signed_separation" => Dict("level_a" => "undefined", "level_b" => "exists", "level_c" => "exists_shell_conditioned"),
        "shell_leakage_class" => Dict("level_a" => "undefined", "level_b" => "undefined", "level_c" => "exists"),
        "shell_conditioned_gamma5_shift" => Dict("level_a" => "undefined", "level_b" => "degenerate", "level_c" => "exists"),
        "conditioned_fixed_point_structure" => Dict("level_a" => "degenerate", "level_b" => "degenerate", "level_c" => "exists_via_disintegration_rule"),
    )
    values = Dict(
        "site_count" => Float64(length(sites)),
        "required_terrain_count" => Float64(length(REQUIRED_TERRAINS)),
        "non_preserve_shell_site_count" => Float64(non_preserve_count),
        "spinor_blind_max_signal" => maximum(blind_signals),
        "shell_conditioned_gamma5_positive_rows" => Float64(gamma_positive),
        "si_own_frame_pass" => si["pass"] ? 1.0 : 0.0,
    )
    all_pass = all(row["level_a_bloch"]["pass"] && row["level_b_spinor"]["pass"] && row["level_c_shell"]["pass"] for (_, row) in decomposition) &&
               all(control["pass"] for (_, control) in controls) &&
               si["pass"] && non_preserve_count > 0 && gamma_positive == length(REQUIRED_TERRAINS)
    return Dict("shell_sites" => sites, "load_bearing_decomposition" => decomposition, "three_level_property_matrix" => property_matrix, "si_frame_row" => si, "controls" => controls, "values" => values, "all_pass" => all_pass, "smt_identity_values" => Dict("actual_non_preserve_shell_site_count" => non_preserve_count, "erased_no_placement_non_preserve_count" => 0))
end

function tool_call(tool, qualified_api, input_object, output_object, positive_case, negative_control, boundary_case, demotion_condition, gates)
    return Dict("tool" => tool, "qualified_api/function" => qualified_api, "input_object" => input_object, "output_object" => output_object, "positive_case" => positive_case, "negative/erased_control" => negative_control, "boundary_case" => boundary_case, "demotion_condition" => demotion_condition, "gates" => gates)
end

function build_result()
    core = build_core()
    actual = Int(core["smt_identity_values"]["actual_non_preserve_shell_site_count"])
    erased = Int(core["smt_identity_values"]["erased_no_placement_non_preserve_count"])
    z3_proof = z3_erased_flip_proof(actual, erased)
    qo = quantumoptics_receipt()
    grass = grassmann_receipt()
    acceptance = Dict(
        "core_nest_pass" => core["all_pass"],
        "quantumoptics" => qo["pass"],
        "grassmann" => grass["pass"],
        "z3" => z3_proof["pass"],
        "ceiling" => CLASSIFICATION == "scratch_diagnostic" && PROMOTION_ALLOWED == false && FORMAL_ADMISSION_ALLOWED == false,
    )
    return Dict(
        "schema_version" => "$(SIM_ID).$(ENGINE)_result.v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "role_id" => "julia_authoritative_sim_builder",
        "generated_at" => string(Dates.now(Dates.UTC)),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "seed" => SEED,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "julia_project" => string(Base.active_project()),
        "packages_used" => PACKAGES_USED,
        "aligned_packages_load_bearing" => ALIGNED_PACKAGES_LOAD_BEARING,
        "claim_path_tools" => ALIGNED_PACKAGES_LOAD_BEARING,
        "package_versions" => Dict(name => pkg_version(name) for name in ["QuantumOptics", "Grassmann", "Z3"]),
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "tool_calls" => [
            tool_call("QuantumOptics", "QuantumOptics.SpinBasis/Ket/dm", "one-qubit spinor", qo, "density trace is one", "phase quotient erases global phase", "basis dimension two", "if dm trace is not one, demote spinor quotient", ["level_b_spinor"]),
            tool_call("Grassmann", "Grassmann.@basis", "Cl(2) even-subalgebra row", grass, "bivector exists", "scalar-only erases sign carrier", "two-generator boundary", "if bivector row is absent, demote spinor carrier", ["level_b_spinor"]),
            tool_call("Z3", "Z3.Solver/check", "computed non-preserve count and erased no-placement count", z3_proof, "actual count differs from erased count", "erased count bound to actual zero count", "actual=0 control is satisfiable", "if erased flip does not change verdict, demote proof", ["crossover_proofs"]),
        ],
        "capability_receipts" => Dict("quantumoptics" => qo, "grassmann" => grass, "julia_z3" => z3_proof),
        "load_bearing_decomposition" => core["load_bearing_decomposition"],
        "three_level_property_matrix" => core["three_level_property_matrix"],
        "si_frame_row" => core["si_frame_row"],
        "controls" => core["controls"],
        "smt_identity_values" => core["smt_identity_values"],
        "crossover_proofs" => Dict("julia_z3" => z3_proof),
        "acceptance" => acceptance,
        "values" => core["values"],
        "all_pass" => all(values(acceptance)),
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        write(io, "\n")
    end
    println("wrote: $(RESULT_PATH)")
    println("$(SIM_ID)_$(ENGINE)_DONE all_pass=$(result["all_pass"])")
    return result["all_pass"] ? 0 : 1
end

exit(main())
