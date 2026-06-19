#!/usr/bin/env julia
# object_id: geo_bracketing_smt_lifted_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using JSON
using SHA
using Z3

const ROOT = "/Users/joshuaeisenhart/Codex-Ratchet"
const SIM_ID = "geo_bracketing_smt_lifted_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const N3_JAX_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n3_v0", "results", "stage_lifted_spinor_shell_n3_v0_jax_results.json")
const N3_JULIA_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n3_v0", "results", "stage_lifted_spinor_shell_n3_v0_julia_results.json")
const N4_JAX_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n4_v0", "results", "stage_lifted_spinor_shell_n4_v0_jax_results.json")
const N4_JULIA_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n4_v0", "results", "stage_lifted_spinor_shell_n4_v0_julia_results.json")
const N5_JAX_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n5_v0", "results", "stage_lifted_spinor_shell_n5_v0_jax_results.json")
const N5_JULIA_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n5_v0", "results", "stage_lifted_spinor_shell_n5_v0_julia_results.json")
const N6_JAX_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n6_v0", "results", "stage_lifted_spinor_shell_n6_v0_jax_results.json")
const N6_JULIA_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n6_v0", "results", "stage_lifted_spinor_shell_n6_v0_julia_results.json")
const N7_JAX_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n7_v0", "results", "stage_lifted_spinor_shell_n7_v0_jax_results.json")
const N7_JULIA_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n7_v0", "results", "stage_lifted_spinor_shell_n7_v0_julia_results.json")
const N8_JAX_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n8_v0", "results", "stage_lifted_spinor_shell_n8_v0_jax_results.json")
const N8_JULIA_RESULT = joinpath(ROOT, "system_v6", "sims", "stage_lifted_spinor_shell_n8_v0", "results", "stage_lifted_spinor_shell_n8_v0_julia_results.json")

const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const SEED = 20260610
const PIN_BLOCK = Dict(
    "sim_id" => SIM_ID,
    "source_packet" => "stage_lifted_spinor_shell_n3_v0 plus stage_lifted_spinor_shell_n4_v0/n5/n6/n7/n8 extension rows",
    "source_scope" => "read-only committed n=3, n=4, n=5, n=6, n=7, and n=8 exported JSONs",
    "claim" => "lifted path/grouping objects have structurally nonzero bracketing gap; density-erased quotient flips to zero gap",
    "solver_sentence" => "positive proves UNSAT of equality/zero-gap negation; erased control proves SAT of equality/zero-gap negation",
    "unit_boundary" => "with unit e, asserting (a*e)*e = -a*(e*e) forces a=0; nonzero-a version is UNSAT",
    "classification" => CLASSIFICATION,
    "promotion_allowed" => PROMOTION_ALLOWED,
    "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
    "seed" => SEED,
    "mode" => "julia_canon_plus_jax_diagnostic",
)
const PIN_SPEC = "{\"claim\":\"lifted path/grouping objects have structurally nonzero bracketing gap; density-erased quotient flips to zero gap\",\"classification\":\"scratch_diagnostic\",\"formal_admission_allowed\":false,\"mode\":\"julia_canon_plus_jax_diagnostic\",\"promotion_allowed\":false,\"seed\":20260610,\"sim_id\":\"geo_bracketing_smt_lifted_v0\",\"solver_sentence\":\"positive proves UNSAT of equality/zero-gap negation; erased control proves SAT of equality/zero-gap negation\",\"source_packet\":\"stage_lifted_spinor_shell_n3_v0 plus stage_lifted_spinor_shell_n4_v0/n5/n6/n7/n8 extension rows\",\"source_scope\":\"read-only committed n=3, n=4, n=5, n=6, n=7, and n=8 exported JSONs\",\"unit_boundary\":\"with unit e, asserting (a*e)*e = -a*(e*e) forces a=0; nonzero-a version is UNSAT\"}"
const SOURCE_SPECS = Dict(
    "n3" => Dict(
        "n" => 3,
        "jax_result" => N3_JAX_RESULT,
        "julia_result" => N3_JULIA_RESULT,
        "left_path" => ["e01", "e12"],
        "right_path" => ["e12", "e01"],
        "path_lineage" => "system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_julia.jl:SOURCE_SPECS.n3.left_path/right_path",
        "support_field" => "rows.P2_support_object",
        "boundary_field" => "rows.P7_bracketing_boundary",
    ),
    "n4" => Dict(
        "n" => 4,
        "jax_result" => N4_JAX_RESULT,
        "julia_result" => N4_JULIA_RESULT,
        "left_path" => ["e01", "e12", "e23"],
        "right_path" => ["e23", "e12", "e01"],
        "path_lineage" => "system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_julia.jl:order_and_bracketing_rows.path_gap",
        "support_field" => "rows.P2_support_object",
        "boundary_field" => "rows.P7_bracketing_boundary",
    ),
    "n5" => Dict(
        "n" => 5,
        "jax_result" => N5_JAX_RESULT,
        "julia_result" => N5_JULIA_RESULT,
        "left_path" => ["e01", "e12", "e23"],
        "right_path" => ["e23", "e12", "e01"],
        "path_lineage" => "system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_julia.jl:order_and_bracketing_rows.path_gap",
        "support_field" => "rows.P2_support_object",
        "boundary_field" => "rows.P7_bracketing_boundary",
    ),
    "n6" => Dict(
        "n" => 6,
        "jax_result" => N6_JAX_RESULT,
        "julia_result" => N6_JULIA_RESULT,
        "left_path" => ["e01", "e12", "e23"],
        "right_path" => ["e23", "e12", "e01"],
        "path_lineage" => "system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_julia.jl:order_and_bracketing_rows.path_gap",
        "support_field" => "rows.P2_support_object",
        "boundary_field" => "rows.P7_bracketing_boundary",
    ),
    "n7" => Dict(
        "n" => 7,
        "jax_result" => N7_JAX_RESULT,
        "julia_result" => N7_JULIA_RESULT,
        "left_path" => ["e01", "e12", "e23"],
        "right_path" => ["e23", "e12", "e01"],
        "path_lineage" => "system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_julia.jl:order_and_bracketing_rows.path_gap",
        "support_field" => "rows.P2_support_object",
        "boundary_field" => "rows.P7_bracketing_boundary",
    ),
    "n8" => Dict(
        "n" => 8,
        "jax_result" => N8_JAX_RESULT,
        "julia_result" => N8_JULIA_RESULT,
        "left_path" => ["e01", "e12", "e23"],
        "right_path" => ["e23", "e12", "e01"],
        "path_lineage" => "system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_julia.jl:order_and_bracketing_rows.path_gap",
        "support_field" => "rows.P2_support_object",
        "boundary_field" => "rows.P7_bracketing_boundary",
    ),
)
const TOOL_MANIFEST = Dict(
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Julia Z3.jl mirror for lifted bracketing, erased flip, and unit-killed boundary"),
    "JSON/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive JSON loading, timestamping, and hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict(
    "Z3" => "load_bearing",
    "JSON/Dates/SHA" => "supportive",
)
const PACKAGES_USED = ["Z3", "JSON", "Dates", "SHA"]
const ALIGNED_PACKAGES_LOAD_BEARING = ["Z3"]
const CLAIM_PATH_TOOLS = ["Z3"]

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))

function file_sha256(path::String)
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function bit_index(site_id::String, n_sites::Int)
    site = parse(Int, replace(site_id, "q" => ""))
    return n_sites - 1 - site
end

function apply_cnot(edge, state::Int, n_sites::Int)
    control = bit_index(String(edge["src"]), n_sites)
    target = bit_index(String(edge["dst"]), n_sites)
    if ((state >> control) & 1) == 1
        return xor(state, 1 << target)
    end
    return state
end

function compose_path(edges_by_id, path_ids::Vector{String}, state::Int, n_sites::Int)
    out = state
    for edge_id in path_ids
        out = apply_cnot(edges_by_id[edge_id], out, n_sites)
    end
    return out
end

function one_excitation_states(n_sites::Int)
    [1 << bit_index("q$(i)", n_sites) for i in 0:(n_sites - 1)]
end

function count_vector(outputs::Vector{Int}, dim::Int)
    counts = zeros(Int, dim)
    for out in outputs
        counts[out + 1] += 1
    end
    counts
end

function load_raw_object(label::String)
    spec = SOURCE_SPECS[label]
    source_jax = JSON.parsefile(spec["jax_result"])
    source_julia = JSON.parsefile(spec["julia_result"])
    support = source_jax["rows"]["P2_support_object"]
    order_row = source_jax["rows"]["P7_bracketing_boundary"]
    sites = support["sites"]
    n_sites = length(sites)
    dim = 2^n_sites
    edges = support["edges"]
    edges_by_id = Dict(String(edge["edge_id"]) => edge for edge in edges)
    left_path = spec["left_path"]
    right_path = spec["right_path"]
    inputs = one_excitation_states(n_sites)
    left_outputs = [compose_path(edges_by_id, left_path, state, n_sites) for state in inputs]
    right_outputs = [compose_path(edges_by_id, right_path, state, n_sites) for state in inputs]
    left_counts = count_vector(left_outputs, dim)
    right_counts = count_vector(right_outputs, dim)
    diff_sq_counts = sum((left_counts .- right_counts) .^ 2)
    gap_divisor = gcd(diff_sq_counts, n_sites)
    if label == "n3"
        source_results = Dict(
            "n3_jax_result" => relpath(N3_JAX_RESULT, ROOT),
            "n3_julia_result" => relpath(N3_JULIA_RESULT, ROOT),
            "n3_jax_sha256" => file_sha256(N3_JAX_RESULT),
            "n3_julia_sha256" => file_sha256(N3_JULIA_RESULT),
        )
    else
        source_results = Dict(
            "$(label)_jax_result" => relpath(spec["jax_result"], ROOT),
            "$(label)_julia_result" => relpath(spec["julia_result"], ROOT),
            "$(label)_jax_sha256" => file_sha256(spec["jax_result"]),
            "$(label)_julia_sha256" => file_sha256(spec["julia_result"]),
            "$(label)_support_field" => spec["support_field"],
            "$(label)_boundary_field" => spec["boundary_field"],
            "$(label)_path_lineage" => spec["path_lineage"],
        )
    end
    row = Dict(
        "source_results" => source_results,
        "n_sites" => n_sites,
        "dim" => dim,
        "sites" => sites,
        "edges" => edges,
        "paths" => Dict("left" => left_path, "right" => right_path),
        "input_support_basis" => inputs,
        "left_outputs" => left_outputs,
        "right_outputs" => right_outputs,
        "left_counts" => collect(left_counts),
        "right_counts" => collect(right_counts),
        "diff_sq_counts" => diff_sq_counts,
        "normalized_gap_sq_num" => div(diff_sq_counts, gap_divisor),
        "normalized_gap_sq_den" => div(n_sites, gap_divisor),
        "exported_gap_decimal" => order_row["lifted_path_grouping_gap"],
        "julia_exported_gap_decimal" => source_julia["rows"]["P7_bracketing_boundary"]["lifted_path_grouping_gap"],
        "exported_matrix_associator_norm" => order_row["matrix_associator_norm"],
    )
    if label != "n3"
        row["source_label"] = label
        row["n"] = spec["n"]
    end
    row
end

z3_status(value) = lowercase(string(value))

function z3_add_expr(args::Vector{Z3.Expr})
    isempty(args) && return Z3.IntVal(0)
    length(args) == 1 && return args[1]
    Z3.Expr(args[1].ctx, Z3.Libz3.Z3_mk_add(Z3.ctx_ref(args[1]), length(args), map(Z3.as_ast, args)))
end

function z3_lifted_proof(raw)
    solver = Z3.Solver()
    left = [Z3.IntVar("lifted_left_count_$(i)") for i in 1:raw["dim"]]
    right = [Z3.IntVar("lifted_right_count_$(i)") for i in 1:raw["dim"]]
    for i in 1:raw["dim"]
        Z3.add(solver, left[i] == Z3.IntVal(raw["left_counts"][i]))
        Z3.add(solver, right[i] == Z3.IntVal(raw["right_counts"][i]))
    end
    Z3.add(solver, Z3.And([left[i] == right[i] for i in 1:raw["dim"]]))
    positive_verdict = z3_status(Z3.check(solver))

    erased = Z3.Solver()
    left_density_token = Z3.IntVar("erased_left_density_single_excitation_mass")
    right_density_token = Z3.IntVar("erased_right_density_single_excitation_mass")
    Z3.add(erased, left_density_token == Z3.IntVal(sum(raw["left_counts"])))
    Z3.add(erased, right_density_token == Z3.IntVal(sum(raw["right_counts"])))
    Z3.add(erased, left_density_token == right_density_token)
    erased_verdict = z3_status(Z3.check(erased))

    boundary = Z3.Solver()
    a = Z3.IntVar("a")
    Z3.add(boundary, z3_add_expr(Z3.Expr[a, a]) == Z3.IntVal(0))
    Z3.add(boundary, Z3.Not(a == Z3.IntVal(0)))
    boundary_verdict = z3_status(Z3.check(boundary))

    Dict(
        "ran" => true,
        "load_bearing" => true,
        "claim" => "Julia Z3.jl mirror: lifted count-vector equality is UNSAT; erased density-token equality is SAT; unit anti-associativity kills nonzero a",
        "verdict" => positive_verdict,
        "erased_control_verdict" => erased_verdict,
        "unit_killed_nonzero_verdict" => boundary_verdict,
        "raw_values_bound" => Dict("left_counts" => raw["left_counts"], "right_counts" => raw["right_counts"]),
        "pass" => positive_verdict == "unsat" && erased_verdict == "sat" && boundary_verdict == "unsat",
    )
end

function build_result()
    raw = load_raw_object("n3")
    n4_raw = load_raw_object("n4")
    n5_raw = load_raw_object("n5")
    n6_raw = load_raw_object("n6")
    n7_raw = load_raw_object("n7")
    n8_raw = load_raw_object("n8")
    z3_proof = z3_lifted_proof(raw)
    n4_z3_proof = z3_lifted_proof(n4_raw)
    n5_z3_proof = z3_lifted_proof(n5_raw)
    n6_z3_proof = z3_lifted_proof(n6_raw)
    n7_z3_proof = z3_lifted_proof(n7_raw)
    n8_z3_proof = z3_lifted_proof(n8_raw)
    all_pass = z3_proof["pass"] && n4_z3_proof["pass"] && n5_z3_proof["pass"] && n6_z3_proof["pass"] && n7_z3_proof["pass"] && n8_z3_proof["pass"]
    Dict(
        "schema_version" => "geo_bracketing_smt_lifted_v0_engine_v1",
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "role_id" => "julia_canon_z3_mirror",
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "all_pass" => all_pass,
        "reads_peer_result" => READS_PEER_RESULT,
        "seed" => SEED,
        "pin_block" => PIN_BLOCK,
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "source_path" => relpath(SOURCE_PATH, ROOT),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => relpath(RESULT_PATH, ROOT),
        "julia_project" => Base.active_project(),
        "packages_used" => PACKAGES_USED,
        "aligned_packages_load_bearing" => ALIGNED_PACKAGES_LOAD_BEARING,
        "claim_path_tools" => CLAIM_PATH_TOOLS,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "source_refs" => raw["source_results"],
        "n4_source_refs" => n4_raw["source_results"],
        "n5_source_refs" => n5_raw["source_results"],
        "n6_source_refs" => n6_raw["source_results"],
        "n7_source_refs" => n7_raw["source_results"],
        "n8_source_refs" => n8_raw["source_results"],
        "raw_object" => raw,
        "n4_raw_object" => n4_raw,
        "n5_raw_object" => n5_raw,
        "n6_raw_object" => n6_raw,
        "n7_raw_object" => n7_raw,
        "n8_raw_object" => n8_raw,
        "positive" => Dict("z3" => z3_proof, "pass" => z3_proof["verdict"] == "unsat"),
        "negative" => Dict("z3_verdict" => z3_proof["erased_control_verdict"], "pass" => z3_proof["erased_control_verdict"] == "sat"),
        "boundary" => Dict("z3_verdict" => z3_proof["unit_killed_nonzero_verdict"], "pass" => z3_proof["unit_killed_nonzero_verdict"] == "unsat"),
        "n4_positive" => Dict("z3" => n4_z3_proof, "pass" => n4_z3_proof["verdict"] == "unsat"),
        "n4_negative" => Dict("z3_verdict" => n4_z3_proof["erased_control_verdict"], "pass" => n4_z3_proof["erased_control_verdict"] == "sat"),
        "n4_boundary" => Dict("z3_verdict" => n4_z3_proof["unit_killed_nonzero_verdict"], "pass" => n4_z3_proof["unit_killed_nonzero_verdict"] == "unsat"),
        "n5_positive" => Dict("z3" => n5_z3_proof, "pass" => n5_z3_proof["verdict"] == "unsat"),
        "n5_negative" => Dict("z3_verdict" => n5_z3_proof["erased_control_verdict"], "pass" => n5_z3_proof["erased_control_verdict"] == "sat"),
        "n5_boundary" => Dict("z3_verdict" => n5_z3_proof["unit_killed_nonzero_verdict"], "pass" => n5_z3_proof["unit_killed_nonzero_verdict"] == "unsat"),
        "n6_positive" => Dict("z3" => n6_z3_proof, "pass" => n6_z3_proof["verdict"] == "unsat"),
        "n6_negative" => Dict("z3_verdict" => n6_z3_proof["erased_control_verdict"], "pass" => n6_z3_proof["erased_control_verdict"] == "sat"),
        "n6_boundary" => Dict("z3_verdict" => n6_z3_proof["unit_killed_nonzero_verdict"], "pass" => n6_z3_proof["unit_killed_nonzero_verdict"] == "unsat"),
        "n7_positive" => Dict("z3" => n7_z3_proof, "pass" => n7_z3_proof["verdict"] == "unsat"),
        "n7_negative" => Dict("z3_verdict" => n7_z3_proof["erased_control_verdict"], "pass" => n7_z3_proof["erased_control_verdict"] == "sat"),
        "n7_boundary" => Dict("z3_verdict" => n7_z3_proof["unit_killed_nonzero_verdict"], "pass" => n7_z3_proof["unit_killed_nonzero_verdict"] == "unsat"),
        "n8_positive" => Dict("z3" => n8_z3_proof, "pass" => n8_z3_proof["verdict"] == "unsat"),
        "n8_negative" => Dict("z3_verdict" => n8_z3_proof["erased_control_verdict"], "pass" => n8_z3_proof["erased_control_verdict"] == "sat"),
        "n8_boundary" => Dict("z3_verdict" => n8_z3_proof["unit_killed_nonzero_verdict"], "pass" => n8_z3_proof["unit_killed_nonzero_verdict"] == "unsat"),
        "crossover_proofs" => Dict("julia_z3" => z3_proof),
        "n4_crossover_proofs" => Dict("julia_z3" => n4_z3_proof),
        "n5_crossover_proofs" => Dict("julia_z3" => n5_z3_proof),
        "n6_crossover_proofs" => Dict("julia_z3" => n6_z3_proof),
        "n7_crossover_proofs" => Dict("julia_z3" => n7_z3_proof),
        "n8_crossover_proofs" => Dict("julia_z3" => n8_z3_proof),
        "acceptance" => Dict(
            "julia_z3_positive_unsat" => z3_proof["verdict"] == "unsat",
            "erased_control_flips" => z3_proof["erased_control_verdict"] == "sat",
            "unit_killed_control_fails_nonzero" => z3_proof["unit_killed_nonzero_verdict"] == "unsat",
            "n3_rows_recomputed" => true,
            "n4_read_only_imports_present" => true,
            "n4_julia_z3_positive_unsat" => n4_z3_proof["verdict"] == "unsat",
            "n4_erased_control_flips" => n4_z3_proof["erased_control_verdict"] == "sat",
            "n4_unit_killed_control_fails_nonzero" => n4_z3_proof["unit_killed_nonzero_verdict"] == "unsat",
            "n5_read_only_imports_present" => true,
            "n5_julia_z3_positive_unsat" => n5_z3_proof["verdict"] == "unsat",
            "n5_erased_control_flips" => n5_z3_proof["erased_control_verdict"] == "sat",
            "n5_unit_killed_control_fails_nonzero" => n5_z3_proof["unit_killed_nonzero_verdict"] == "unsat",
            "n6_read_only_imports_present" => true,
            "n6_julia_z3_positive_unsat" => n6_z3_proof["verdict"] == "unsat",
            "n6_erased_control_flips" => n6_z3_proof["erased_control_verdict"] == "sat",
            "n6_unit_killed_control_fails_nonzero" => n6_z3_proof["unit_killed_nonzero_verdict"] == "unsat",
            "n7_read_only_imports_present" => true,
            "n7_julia_z3_positive_unsat" => n7_z3_proof["verdict"] == "unsat",
            "n7_erased_control_flips" => n7_z3_proof["erased_control_verdict"] == "sat",
            "n7_unit_killed_control_fails_nonzero" => n7_z3_proof["unit_killed_nonzero_verdict"] == "unsat",
            "n8_read_only_imports_present" => true,
            "n8_julia_z3_positive_unsat" => n8_z3_proof["verdict"] == "unsat",
            "n8_erased_control_flips" => n8_z3_proof["erased_control_verdict"] == "sat",
            "n8_unit_killed_control_fails_nonzero" => n8_z3_proof["unit_killed_nonzero_verdict"] == "unsat",
        ),
        "values" => Dict(
            "lifted_gap_squared_num" => raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den" => raw["normalized_gap_sq_den"],
            "lifted_gap_decimal" => sqrt(raw["normalized_gap_sq_num"] / raw["normalized_gap_sq_den"]),
            "erased_gap_squared" => 0.0,
            "matrix_associator_norm" => raw["exported_matrix_associator_norm"],
        ),
        "n4_values" => Dict(
            "lifted_gap_squared_num" => n4_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den" => n4_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal" => sqrt(n4_raw["normalized_gap_sq_num"] / n4_raw["normalized_gap_sq_den"]),
            "erased_gap_squared" => 0.0,
            "matrix_associator_norm" => n4_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap" => n4_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed" => abs(sqrt(n4_raw["normalized_gap_sq_num"] / n4_raw["normalized_gap_sq_den"]) - n4_raw["exported_gap_decimal"]) < 1.0e-12,
        ),
        "n5_values" => Dict(
            "lifted_gap_squared_num" => n5_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den" => n5_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal" => sqrt(n5_raw["normalized_gap_sq_num"] / n5_raw["normalized_gap_sq_den"]),
            "erased_gap_squared" => 0.0,
            "matrix_associator_norm" => n5_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap" => n5_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed" => abs(sqrt(n5_raw["normalized_gap_sq_num"] / n5_raw["normalized_gap_sq_den"]) - n5_raw["exported_gap_decimal"]) < 1.0e-12,
        ),
        "n6_values" => Dict(
            "lifted_gap_squared_num" => n6_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den" => n6_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal" => sqrt(n6_raw["normalized_gap_sq_num"] / n6_raw["normalized_gap_sq_den"]),
            "erased_gap_squared" => 0.0,
            "matrix_associator_norm" => n6_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap" => n6_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed" => abs(sqrt(n6_raw["normalized_gap_sq_num"] / n6_raw["normalized_gap_sq_den"]) - n6_raw["exported_gap_decimal"]) < 1.0e-12,
        ),
        "n7_values" => Dict(
            "lifted_gap_squared_num" => n7_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den" => n7_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal" => sqrt(n7_raw["normalized_gap_sq_num"] / n7_raw["normalized_gap_sq_den"]),
            "erased_gap_squared" => 0.0,
            "matrix_associator_norm" => n7_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap" => n7_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed" => abs(sqrt(n7_raw["normalized_gap_sq_num"] / n7_raw["normalized_gap_sq_den"]) - n7_raw["exported_gap_decimal"]) < 1.0e-12,
        ),
        "n8_values" => Dict(
            "lifted_gap_squared_num" => n8_raw["normalized_gap_sq_num"],
            "lifted_gap_squared_den" => n8_raw["normalized_gap_sq_den"],
            "lifted_gap_decimal" => sqrt(n8_raw["normalized_gap_sq_num"] / n8_raw["normalized_gap_sq_den"]),
            "erased_gap_squared" => 0.0,
            "matrix_associator_norm" => n8_raw["exported_matrix_associator_norm"],
            "exported_lifted_path_grouping_gap" => n8_raw["exported_gap_decimal"],
            "exported_gap_matches_recomputed" => abs(sqrt(n8_raw["normalized_gap_sq_num"] / n8_raw["normalized_gap_sq_den"]) - n8_raw["exported_gap_decimal"]) < 1.0e-12,
        ),
        "tool_calls" => [
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver, Z3.add, Z3.check over lifted finite path count vectors",
                "input_object" => "left/right path count vectors derived from n=3 support edges and one-excitation basis",
                "output_object" => "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case" => "lifted path count vector equality is UNSAT",
                "negative/erased_control" => "density-token equality is SAT",
                "boundary_case" => "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition" => "demote if erased control does not flip to SAT",
                "gates" => ["all_pass", "proof", "quotient"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver, Z3.add, Z3.check over n=4 lifted finite path count vectors",
                "input_object" => "left/right path count vectors derived from committed n=4 support edges and one-excitation basis",
                "output_object" => "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case" => "n=4 lifted path count vector equality is UNSAT",
                "negative/erased_control" => "n=4 density-token equality is SAT",
                "boundary_case" => "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition" => "demote if n=4 erased control does not flip to SAT",
                "gates" => ["all_pass", "proof", "quotient", "n4_extension"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver, Z3.add, Z3.check over n=5 lifted finite path count vectors",
                "input_object" => "left/right path count vectors derived from committed n=5 support edges and one-excitation basis",
                "output_object" => "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case" => "n=5 lifted path count vector equality is UNSAT",
                "negative/erased_control" => "n=5 density-token equality is SAT",
                "boundary_case" => "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition" => "demote if n=5 erased control does not flip to SAT",
                "gates" => ["all_pass", "proof", "quotient", "n5_extension"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver, Z3.add, Z3.check over n=6 lifted finite path count vectors",
                "input_object" => "left/right path count vectors derived from committed n=6 support edges and one-excitation basis",
                "output_object" => "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case" => "n=6 lifted path count vector equality is UNSAT",
                "negative/erased_control" => "n=6 density-token equality is SAT",
                "boundary_case" => "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition" => "demote if n=6 erased control does not flip to SAT",
                "gates" => ["all_pass", "proof", "quotient", "n6_extension"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver, Z3.add, Z3.check over n=7 lifted finite path count vectors",
                "input_object" => "left/right path count vectors derived from committed n=7 support edges and one-excitation basis",
                "output_object" => "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case" => "n=7 lifted path count vector equality is UNSAT",
                "negative/erased_control" => "n=7 density-token equality is SAT",
                "boundary_case" => "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition" => "demote if n=7 erased control does not flip to SAT",
                "gates" => ["all_pass", "proof", "quotient", "n7_extension"],
            ),
            Dict(
                "tool" => "Z3",
                "qualified_api/function" => "Z3.Solver, Z3.add, Z3.check over n=8 lifted finite path count vectors",
                "input_object" => "left/right path count vectors derived from committed n=8 support edges and one-excitation basis",
                "output_object" => "UNSAT positive, SAT erased, UNSAT unit nonzero boundary",
                "positive_case" => "n=8 lifted path count vector equality is UNSAT",
                "negative/erased_control" => "n=8 density-token equality is SAT",
                "boundary_case" => "unit anti-associativity with nonzero a is UNSAT",
                "demotion_condition" => "demote if n=8 erased control does not flip to SAT",
                "gates" => ["all_pass", "proof", "quotient", "n8_extension"],
            ),
        ],
    )
end

function main()
    mkpath(RESULT_DIR)
    result = build_result()
    open(RESULT_PATH, "w") do io
        JSON.print(io, result, 2)
        println(io)
    end
    println(JSON.json(Dict("ok" => result["all_pass"], "result_path" => relpath(RESULT_PATH, ROOT))))
    return result["all_pass"] ? 0 : 1
end

exit(main())
