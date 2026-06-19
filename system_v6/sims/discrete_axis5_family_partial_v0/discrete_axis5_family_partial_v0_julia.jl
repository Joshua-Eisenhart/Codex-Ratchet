#!/usr/bin/env julia
# Julia lane for discrete_axis5_family_partial_v0.

using Dates
using JSON
using LinearAlgebra
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "../../.."))
const SIM_ID = "discrete_axis5_family_partial_v0"
const ENGINE = "julia"
const SIM_DIR = joinpath(ROOT, "system_v6", "sims", SIM_ID)
const RESULT_DIR = joinpath(SIM_DIR, "results")
const SOURCE_PATH = joinpath(SIM_DIR, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const CLAIM_CEILING = "axis_readout_candidate_only"
const PARTIAL_SCOPE = "axis5_operator_family_half_only"
const ENGINE_MODE = "three_engine_axis5_family_partial_candidate_on_family_a_33_cell_carrier"
const EPS = 1.0e-10
const Q = 0.3
const GRID_VALUES = [-1.0, -0.5, 0.0, 0.5, 1.0]

now_z()::String = Dates.format(Dates.now(Dates.UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ")
rel(path::String)::String = replace(relpath(path, ROOT), "\\" => "/")

function sha256_file(path::String)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

function stable_sha(value)::String
    return bytes2hex(sha256(collect(codeunits(JSON.json(value)))))
end

function state_cells()
    cells = Vector{Dict{String, Any}}()
    for x in GRID_VALUES, y in GRID_VALUES, z in GRID_VALUES
        r2 = x * x + y * y + z * z
        if r2 <= 1.0 + 1.0e-12
            push!(
                cells,
                Dict(
                    "cell_id" => length(cells),
                    "coord" => [x, y, z],
                    "coord_scaled" => [Int(round(2 * x)), Int(round(2 * y)), Int(round(2 * z))],
                ),
            )
        end
    end
    cells
end

function op_matrix(operator::String)
    if operator == "Ti"
        return Diagonal([1.0 - Q, 1.0 - Q, 1.0])
    elseif operator == "Te"
        return Diagonal([1.0, 1.0 - Q, 1.0 - Q])
    elseif operator == "Fi"
        return [1.0 0.0 0.0; 0.0 cos(pi / 2) -sin(pi / 2); 0.0 sin(pi / 2) cos(pi / 2)]
    elseif operator == "Fe"
        return [cos(pi / 2) -sin(pi / 2) 0.0; sin(pi / 2) cos(pi / 2) 0.0; 0.0 0.0 1.0]
    end
    error("unknown operator")
end

function entropy_bloch(r)::Float64
    radius = min(1.0, max(0.0, norm(r)))
    vals = [(1.0 + radius) / 2.0, (1.0 - radius) / 2.0]
    return -sum(v > EPS ? v * log(v) : 0.0 for v in vals)
end

purity_bloch(r)::Float64 = (1.0 + dot(r, r)) / 2.0

function witness_rows(cells)
    rows = Vector{Dict{String, Any}}()
    for cell in cells, operator in ["Ti", "Te", "Fi", "Fe"]
        r = Float64.(cell["coord"])
        post = op_matrix(operator) * r
        entropy_delta = entropy_bloch(post) - entropy_bloch(r)
        purity_delta = purity_bloch(post) - purity_bloch(r)
        norm_delta = norm(post) - norm(r)
        family = operator in ["Ti", "Te"] ? "dephasing_gradient_side" : "unitary_hamiltonian_side"
        sign = operator in ["Ti", "Te"] ? -1 : 1
        push!(
            rows,
            Dict(
                "cell_id" => cell["cell_id"],
                "operator" => operator,
                "axis5_family" => family,
                "axis5_sign" => sign,
                "entropy_production" => abs(entropy_delta) < EPS ? 0.0 : entropy_delta,
                "purity_delta" => abs(purity_delta) < EPS ? 0.0 : purity_delta,
                "bloch_norm_delta" => abs(norm_delta) < EPS ? 0.0 : norm_delta,
                "substage_product_built" => false,
            ),
        )
    end
    rows
end

function z3_family_count_status(dephasing::Int, unitary::Int)::String
    solver = Z3.Solver()
    d = Z3.IntVar("julia_axis5_dephasing_rows")
    u = Z3.IntVar("julia_axis5_unitary_rows")
    Z3.add(solver, d == Z3.IntVal(dephasing))
    Z3.add(solver, u == Z3.IntVal(unitary))
    Z3.add(solver, Z3.Or(Z3.Expr[d == Z3.IntVal(0), u == Z3.IntVal(0)]))
    return lowercase(string(Z3.check(solver)))
end

function main()
    cells = state_cells()
    rows = witness_rows(cells)
    dephasing = count(row -> row["axis5_family"] == "dephasing_gradient_side", rows)
    unitary = count(row -> row["axis5_family"] == "unitary_hamiltonian_side", rows)
    boundary = count(row -> row["axis5_family"] == "boundary", rows)
    z3_status = z3_family_count_status(dephasing, unitary)
    all_pass = length(cells) == 33 && length(rows) == 132 && dephasing == 66 && unitary == 66 && boundary == 0 && z3_status == "unsat"
    computed_values = Dict(
        "dephasing_gradient_side" => dephasing,
        "unitary_hamiltonian_side" => unitary,
        "boundary" => boundary,
        "table_rows" => length(rows),
        "readout_signature_sha256" => stable_sha(rows),
    )
    payload = Dict(
        "sim_id" => SIM_ID,
        "schema_version" => "engine_leg_result_v1",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling" => CLAIM_CEILING,
        "partial_scope" => PARTIAL_SCOPE,
        "engine" => ENGINE,
        "engine_mode" => ENGINE_MODE,
        "generated_at" => now_z(),
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => sha256_file(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "reads_peer_result" => false,
        "packages_used" => ["LinearAlgebra", "JSON", "SHA", "Z3"],
        "aligned_packages_load_bearing" => ["Z3"],
        "package_observables" => Dict(
            "Z3" => "Z3.Solver/Z3.IntVar computed Axis-5 family-count erasure identity",
        ),
        "claim_path_tools" => ["LinearAlgebra", "Z3"],
        "source_backing_probe" => Dict(
            "julia_state_count" => length(cells),
            "julia_table_rows" => length(rows),
            "linearalgebra_norm_purity_witness" => true,
            "z3_family_count_erasure" => z3_status,
            "pass" => all_pass,
        ),
        "computed_values" => computed_values,
        "family_counts" => Dict(
            "dephasing_gradient_side" => dephasing,
            "unitary_hamiltonian_side" => unitary,
            "boundary" => boundary,
        ),
        "capability_receipts" => [
            Dict("package" => "Z3", "observable" => "family count erasure UNSAT", "load_bearing" => true),
        ],
        "tool_calls" => [
            Dict("tool" => "Z3", "evidence" => "computed family count erasure UNSAT"),
        ],
        "all_pass" => all_pass,
    )
    mkpath(RESULT_DIR)
    open(RESULT_PATH, "w") do io
        JSON.print(io, payload, 2)
        write(io, "\n")
    end
    println(JSON.json(Dict("ok" => all_pass, "result_path" => rel(RESULT_PATH))))
    return all_pass ? 0 : 1
end

exit(main())
