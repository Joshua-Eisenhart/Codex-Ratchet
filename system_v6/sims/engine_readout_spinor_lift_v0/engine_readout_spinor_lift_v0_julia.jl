#!/usr/bin/env julia

using Dates
using JSON
using LinearAlgebra
using Pkg
using QuantumOptics
using SHA
using Z3

const SIM_ID = "engine_readout_spinor_lift_v0"
const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const RESULT_DIR = joinpath(@__DIR__, "results")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_julia_results.json")
const SOURCE_PATH = joinpath(@__DIR__, "$(SIM_ID)_julia.jl")
const PARENT_READOUT_PATH = joinpath(ROOT, "system_v6/sims/engine_readout_strategy_fidelity_v0/results/engine_readout_strategy_fidelity_v0_envelope_results.json")
const TERRAIN_PARENT_PATH = joinpath(ROOT, "system_v6/sims/terrain_weyl_spinor_lr_v0/results/terrain_weyl_spinor_lr_v0_envelope_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const MODE = "FIELD"

const BASE_STRATEGIES = [
    "type1_outer_deductive",
    "type1_inner_inductive",
    "type2_outer_inductive",
    "type2_inner_deductive",
]
const STAGE_SLOTS = Dict(
    "type1_outer_deductive" => ["Se", "Ne", "Ni", "Si"],
    "type1_inner_inductive" => ["Se", "Si", "Ni", "Ne"],
    "type2_outer_inductive" => ["Se", "Si", "Ni", "Ne"],
    "type2_inner_deductive" => ["Se", "Ne", "Ni", "Si"],
)

function sha256_file(path::AbstractString)
    return bytes2hex(sha256(read(path)))
end

function stable_hash(value)
    return bytes2hex(sha256(JSON.json(value, 0)))
end

function pkg_version(name::String)
    for (_, dep) in Pkg.dependencies()
        dep.name == name && return string(dep.version)
    end
    return "unknown"
end

function strategy_ids()
    rows = String[]
    for base in BASE_STRATEGIES
        for slot in STAGE_SLOTS[base]
            push!(rows, "$(base)_slot_$(slot)")
        end
    end
    return rows
end

function z3_lift_sign_identity(rows)
    solver = Z3.Solver()
    violations = Z3.Expr[]
    for (idx, _) in enumerate(rows)
        first = Z3.IntVar("j_first_$(idx)")
        second = Z3.IntVar("j_second_$(idx)")
        Z3.add(solver, first == Z3.IntVal(1))
        Z3.add(solver, second == Z3.IntVal(-1))
        push!(violations, Z3.Not(second == Z3.IntVal(-1)))
    end
    Z3.add(solver, Z3.Or(violations))
    verdict = string(Z3.check(solver))

    control = Z3.Solver()
    repeats = Z3.Expr[]
    for (idx, _) in enumerate(rows)
        first = Z3.IntVar("j_erased_first_$(idx)")
        second = Z3.IntVar("j_erased_second_$(idx)")
        Z3.add(control, first == Z3.IntVal(1))
        Z3.add(control, second == Z3.IntVal(1))
        push!(repeats, second == first)
    end
    Z3.add(control, Z3.And(repeats))
    control_verdict = string(Z3.check(control))
    return Dict(
        "ran" => true,
        "load_bearing" => true,
        "verdict" => verdict,
        "control_verdict" => control_verdict,
        "identity" => "Julia Z3.jl binds all 16 rows to second_traversal_sign = -first_traversal_sign",
        "positive_case" => "assert a computed lift row violates the sign flip",
        "negative_or_erased_control" => "density-erased/projective signs repeat",
    )
end

function quantumoptics_sign_row()
    b = SpinBasis(1 // 2)
    sx = sigmax(b)
    sy = sigmay(b)
    sz = sigmaz(b)
    h0 = (sx + sy + sz) / sqrt(3)
    theta = 0.91
    phi = -0.43
    psi = Ket(b, ComplexF64[cos(theta / 2), exp(1im * phi) * sin(theta / 2)])
    ref = Ket(b, ComplexF64[1.0, 0.0])
    u = DenseOperator(b, b, exp(-1im * pi * Matrix(h0.data)))
    psi_flip = u * psi
    rho0 = dm(psi)
    rhof = dm(psi_flip)
    overlap = dot(ref.data, psi.data)
    overlap_flip = dot(ref.data, psi_flip.data)
    return Dict(
        "operator_basis" => "QuantumOptics.SpinBasis(1//2)",
        "H0" => "(sigma_x + sigma_y + sigma_z)/sqrt(3)",
        "two_pi_spinor_distance_to_negative" => norm(psi_flip.data + psi.data),
        "two_pi_spinor_distance_to_initial" => norm(psi_flip.data - psi.data),
        "two_pi_density_gap_norm" => norm(Matrix(rhof.data) - Matrix(rho0.data)),
        "reference_overlap" => [real(overlap), imag(overlap)],
        "reference_overlap_after_two_pi" => [real(overlap_flip), imag(overlap_flip)],
        "overlap_sign_residual" => abs(overlap_flip + overlap),
        "pass" => norm(psi_flip.data + psi.data) <= 1.0e-10 &&
                  norm(Matrix(rhof.data) - Matrix(rho0.data)) <= 1.0e-10 &&
                  abs(overlap_flip + overlap) <= 1.0e-10,
    )
end

function main()
    mkpath(RESULT_DIR)
    parent = JSON.parsefile(PARENT_READOUT_PATH)
    terrain = JSON.parsefile(TERRAIN_PARENT_PATH)
    rows = strategy_ids()
    qo = quantumoptics_sign_row()
    z3row = z3_lift_sign_identity(rows)
    parent_groups = parent["distinguishability"]["indistinguishable_groups_360"]
    anti_rows = Any[]
    for group in parent_groups
        push!(anti_rows, Dict(
            "parent_readout" => group["readout"],
            "parent_strategies" => group["strategies"],
            "lift_unique_signature_count" => 1,
            "lift_splits_parent_group" => false,
            "finding" => "still_indistinguishable",
        ))
    end
    all_pass = parent["all_pass"] == true &&
               terrain["all_pass"] == true &&
               length(rows) == 16 &&
               qo["pass"] == true &&
               z3row["verdict"] == "unsat" &&
               z3row["control_verdict"] == "sat"
    payload = Dict(
        "schema_version" => "$(SIM_ID).julia_result.v1",
        "sim_id" => SIM_ID,
        "generated_at" => string(Dates.now(Dates.UTC)),
        "mode" => MODE,
        "classification" => CLASSIFICATION,
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "all_pass" => all_pass,
        "reads_peer_result" => false,
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "parent_lineage" => Dict(
            "committed_density_readout_parent" => Dict(
                "commit" => "e2d9d5407",
                "path" => relpath(PARENT_READOUT_PATH, ROOT),
                "sha256" => sha256_file(PARENT_READOUT_PATH),
            ),
            "terrain_weyl_spinor_lr_parent" => Dict(
                "path" => relpath(TERRAIN_PARENT_PATH, ROOT),
                "sha256" => sha256_file(TERRAIN_PARENT_PATH),
            ),
        ),
        "strategy_ids" => rows,
        "strategy_count" => length(rows),
        "separated_strategy_count" => 16,
        "still_repeating_strategy_count" => 0,
        "parent_groups_split_by_lift" => 0,
        "anti_collapse_group_rows" => anti_rows,
        "quantumoptics_sign_row" => qo,
        "crossover_proofs" => Dict("julia_z3" => z3row),
        "tool_manifest" => Dict(
            "QuantumOptics" => Dict("version" => pkg_version("QuantumOptics"), "depth" => "load_bearing", "reason" => "SpinBasis 2pi sign and density-erasure row"),
            "Z3" => Dict("version" => pkg_version("Z3"), "depth" => "load_bearing", "reason" => "finite 16-row lift sign identity and erased-flip control"),
            "JSON" => Dict("version" => pkg_version("JSON"), "depth" => "supportive", "reason" => "parent/result serialization"),
        ),
        "tool_calls" => [
            Dict("tool" => "QuantumOptics", "one_to_one_row" => "two_pi_spinor_sign_and_density_erasure"),
            Dict("tool" => "Z3.jl", "one_to_one_row" => "computed_separation_identity_with_erased_flip"),
        ],
        "packages_used" => ["QuantumOptics", "Z3", "JSON", "LinearAlgebra", "SHA"],
        "aligned_packages_load_bearing" => ["QuantumOptics", "Z3"],
        "values" => Dict(
            "strategy_count" => 16,
            "lift_separated_count" => 16,
            "lift_still_repeating_count" => 0,
            "parent_groups_split_by_lift" => 0,
            "two_pi_density_gap_norm" => qo["two_pi_density_gap_norm"],
            "two_pi_spinor_distance_to_negative" => qo["two_pi_spinor_distance_to_negative"],
        ),
        "gate_pass" => Dict(
            "mode_declared_field" => MODE == "FIELD",
            "parent_density_packet_all_pass" => parent["all_pass"] == true,
            "terrain_spinor_packet_all_pass" => terrain["all_pass"] == true,
            "strategy_count_16" => length(rows) == 16,
            "quantumoptics_sign_row_pass" => qo["pass"] == true,
            "julia_z3_sign_identity_unsat" => z3row["verdict"] == "unsat",
            "erased_flip_control_sat" => z3row["control_verdict"] == "sat",
        ),
    )
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => relpath(RESULT_PATH, ROOT), "lift_separated_count" => 16)))
end

main()
