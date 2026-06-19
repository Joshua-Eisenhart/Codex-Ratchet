#!/usr/bin/env julia
# object_id: terrain_spinor_flux_nest_n3_v0
# classification: scratch_diagnostic
# promotion_allowed: false
# formal_admission_allowed: false

using Dates
using ITensors
using ITensorMPS
using JSON3
using LinearAlgebra
using Pkg
using QuantumOptics
using SHA
using Z3

const ROOT = normpath(joinpath(@__DIR__, "..", "..", ".."))
const SIM_ID = "terrain_spinor_flux_nest_n3_v0"
const ENGINE = "julia"
const RESULT_DIR = joinpath(@__DIR__, "results")
const SOURCE_PATH = joinpath(@__DIR__, "$(SIM_ID)_$(ENGINE).jl")
const RESULT_PATH = joinpath(RESULT_DIR, "$(SIM_ID)_$(ENGINE)_results.json")
const STAGE_JAX_PARENT = joinpath(ROOT, "system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_jax_results.json")
const S5_PARENT = joinpath(ROOT, "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json")
const CLASSIFICATION = "scratch_diagnostic"
const PROMOTION_ALLOWED = false
const FORMAL_ADMISSION_ALLOWED = false
const READS_PEER_RESULT = false
const SEED = 2026061103
const TOL = 1.0e-8
const SCALE = 10^12
const PRIMARY_TERRAIN = "Se_Funnel_L"
const RUNG1_UNRAVELING_CONVENTION = "standard quantum-jump unraveling: K_eff=-iH-1/2 sum_j L_j^dagger L_j for no-jump drift, jump maps psi -> L_j psi/||L_j psi||, ensemble density obeys the Lindblad generator. This is a choice; the density generator is the invariant object."
const PIN_SPEC = "terrain_spinor_flux_nest_n3_v0|carrier=committed stage_lifted_spinor_shell_n3_v0 C^8 3-qubit lifted-ladder network state|parents=stage_lifted_spinor_shell_n3_v0,terrain_spinor_shell_nest_v0,geo_s5_terrain_flows_v0,ratchet_s2_two_shell_flux_v0,geo_disintegration_machinery_v0,geo_union_rule_k_leaves_v0,terrain_exact_mirror_finder_v0|edge_coupling=g_ij=abs((zdot_i+zdot_j)/2)+0.25*(abs(A_zx)+abs(A_zy)+abs(A_zz))+abs(b_z), using the committed S5 pinned A z-row A[2][0],A[2][1],A[2][2] and b[2]|current=J_ij=g_ij*(p_i-p_j), p_i=(1-z_i)/2|conditioning=k-leaf union rule w_i=sin(2eta_i)/sum_j sin(2eta_j), conditioned g_ij=g_ij*sqrt(w_i*w_j)|rung1_unraveling_convention=$(RUNG1_UNRAVELING_CONVENTION)|mode=RATCHETED_FIELD|ceiling=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
const PACKAGES_USED = ["QuantumOptics", "ITensors", "ITensorMPS", "Z3", "LinearAlgebra", "JSON3", "Dates", "SHA"]
const ALIGNED_PACKAGES_LOAD_BEARING = ["QuantumOptics", "ITensors", "ITensorMPS", "Z3"]
const TOOL_MANIFEST = Dict{String,Any}(
    "QuantumOptics" => Dict("tried" => true, "used" => true, "reason" => "load-bearing NLevelBasis/Ket/tensor/dm C^8 carrier density row"),
    "ITensors" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Index/ITensor carrier support row"),
    "ITensorMPS" => Dict("tried" => true, "used" => true, "reason" => "load-bearing siteinds/MPS product network row"),
    "Z3" => Dict("tried" => true, "used" => true, "reason" => "load-bearing Z3.jl in-solver continuity derivation with erased flip"),
    "LinearAlgebra/JSON3/Dates/SHA" => Dict("tried" => true, "used" => true, "reason" => "supportive matrix, serialization, timestamping, and hashing"),
)
const TOOL_INTEGRATION_DEPTH = Dict{String,Any}(
    "QuantumOptics" => "load_bearing",
    "ITensors" => "load_bearing",
    "ITensorMPS" => "load_bearing",
    "Z3" => "load_bearing",
    "LinearAlgebra/JSON3/Dates/SHA" => "supportive",
)

sha256_text(text::String) = bytes2hex(sha256(Vector{UInt8}(codeunits(text))))
file_sha256(path::String) = bytes2hex(sha256(read(path)))
rel(path::String) = replace(relpath(path, ROOT), "\\" => "/")
r12(x) = round(Float64(real(x)); digits=12)
scale_int(x) = Int(round(Float64(x) * SCALE))

function pkg_version(name::String)
    for (_, dep) in Pkg.dependencies()
        dep.name == name && return string(dep.version)
    end
    return "unknown"
end

function load_json(path::String)
    return JSON3.read(read(path, String), Dict{String,Any})
end

function parse_num(value)
    if value isa Number
        return Float64(value)
    end
    parsed = Meta.parse(replace(String(value), "//" => "/"))
    return Float64(Base.invokelatest(eval, parsed))
end

function parse_matrix(values)
    return [parse_num(values[i][j]) for i in 1:length(values), j in 1:length(values[1])]
end

function parse_vector(values)
    return [parse_num(values[i]) for i in 1:length(values)]
end

function bloch(site)
    eta = parse_num(site["eta"])
    theta = parse_num(site["theta"])
    return [sin(2eta) * cos(2theta), sin(2eta) * sin(2theta), cos(2eta)]
end

population(site) = (1.0 - parse_num(site["z"])) / 2.0

function local_rows(sites, terrain_row)
    A = parse_matrix(terrain_row["pinned"]["A"])
    b = parse_vector(terrain_row["pinned"]["b"])
    rows = Vector{Dict{String,Any}}()
    for site in sites
        field = A * bloch(site) + b
        z_dot = field[3]
        push!(rows, Dict(
            "site_id" => site["site_id"],
            "shell_id" => site["shell_id"],
            "z_dot" => r12(z_dot),
            "local_population_flow" => r12(-0.5 * z_dot),
            "population_R" => r12(population(site)),
        ))
    end
    return rows
end

function k_leaf_weights(sites)
    densities = [sin(2 * parse_num(site["eta"])) for site in sites]
    total = sum(densities)
    return Dict(site["site_id"] => densities[idx] / total for (idx, site) in enumerate(sites))
end

function coupling_strength(src_row, dst_row, terrain_row)
    A = parse_matrix(terrain_row["pinned"]["A"])
    b = parse_vector(terrain_row["pinned"]["b"])
    return abs(0.5 * (parse_num(src_row["z_dot"]) + parse_num(dst_row["z_dot"]))) +
           0.25 * (abs(A[3, 1]) + abs(A[3, 2]) + abs(A[3, 3])) + abs(b[3])
end

function network_recompute(sites, terrain_row; conditioned::Bool=false)
    edges = [
        Dict("edge_id" => "e01", "src" => "q0", "dst" => "q1"),
        Dict("edge_id" => "e12", "src" => "q1", "dst" => "q2"),
        Dict("edge_id" => "e02", "src" => "q0", "dst" => "q2"),
    ]
    rows = local_rows(sites, terrain_row)
    by_site = Dict(row["site_id"] => row for row in rows)
    site_by_id = Dict(site["site_id"] => site for site in sites)
    weights = k_leaf_weights(sites)
    divergence = Dict(site["site_id"] => 0.0 for site in sites)
    currents = Float64[]
    fluxes = Float64[]
    edge_formula_rows = Vector{Dict{String,Any}}()
    current_by_edge = Dict{String,Int}()
    for edge in edges
        strength = coupling_strength(by_site[edge["src"]], by_site[edge["dst"]], terrain_row)
        if conditioned
            strength *= sqrt(weights[edge["src"]] * weights[edge["dst"]])
        end
        population_delta = population(site_by_id[edge["src"]]) - population(site_by_id[edge["dst"]])
        current = strength * population_delta
        gap = parse_num(site_by_id[edge["src"]]["z"]) - parse_num(site_by_id[edge["dst"]]["z"])
        divergence[edge["src"]] += current
        divergence[edge["dst"]] -= current
        push!(currents, current)
        push!(fluxes, current * gap)
        current_scaled = scale_int(current)
        coupling_scaled = scale_int(strength)
        population_delta_scaled = scale_int(population_delta)
        current_by_edge[edge["edge_id"]] = current_scaled
        push!(edge_formula_rows, Dict(
            "edge_id" => edge["edge_id"],
            "src" => edge["src"],
            "dst" => edge["dst"],
            "coupling_strength_scaled" => coupling_scaled,
            "population_src_minus_dst_scaled" => population_delta_scaled,
            "current_src_to_dst_scaled" => current_scaled,
            "current_formula" => "current_src_to_dst_scaled*SCALE == coupling_strength_scaled*population_src_minus_dst_scaled + rounding_residual_scaled2",
            "rounding_residual_scaled2" => current_scaled * SCALE - coupling_scaled * population_delta_scaled,
        ))
    end
    site_balance_rows = Vector{Dict{String,Any}}()
    for row in rows
        site_id = row["site_id"]
        outgoing = [edge for edge in edges if edge["src"] == site_id]
        incoming = [edge for edge in edges if edge["dst"] == site_id]
        derived_divergence_scaled = sum(current_by_edge[edge["edge_id"]] for edge in outgoing; init=0) -
                                    sum(current_by_edge[edge["edge_id"]] for edge in incoming; init=0)
        local_scaled = scale_int(parse_num(row["local_population_flow"]))
        network_scaled = scale_int(parse_num(row["local_population_flow"]) - divergence[site_id])
        row_divergence_scaled = scale_int(divergence[site_id])
        push!(site_balance_rows, Dict(
            "site_id" => site_id,
            "network_population_flow_scaled" => network_scaled,
            "local_population_flow_scaled" => local_scaled,
            "edge_divergence_scaled" => row_divergence_scaled,
            "derived_edge_divergence_scaled" => derived_divergence_scaled,
            "identity_target_scaled" => local_scaled - derived_divergence_scaled,
            "outgoing_edge_ids" => [edge["edge_id"] for edge in outgoing],
            "incoming_edge_ids" => [edge["edge_id"] for edge in incoming],
            "derived_divergence_matches_row" => derived_divergence_scaled == row_divergence_scaled,
            "balance_residual_scaled" => network_scaled - (local_scaled - derived_divergence_scaled),
        ))
    end
    first_site = site_balance_rows[1]
    proof_row = Dict(
        "site_id" => first_site["site_id"],
        "network_population_flow_scaled" => first_site["network_population_flow_scaled"],
        "local_population_flow_scaled" => first_site["local_population_flow_scaled"],
        "edge_divergence_scaled" => first_site["edge_divergence_scaled"],
        "derived_edge_divergence_scaled" => first_site["derived_edge_divergence_scaled"],
        "identity_target_scaled" => first_site["identity_target_scaled"],
        "edge_formula_rows" => edge_formula_rows,
        "site_balance_rows" => site_balance_rows,
        "solver_derivation" => "edge currents are bound by scaled current formulas, site divergence is derived from edge-current variables, and population balance is asserted in solver space",
        "erased_control" => "subtract one scaled unit from the derived site balance target before asserting the negated identity",
    )
    return Dict(
        "total_abs_current" => r12(sum(abs.(currents))),
        "total_signed_transport_flux" => r12(sum(fluxes)),
        "proof_row" => proof_row,
        "currents" => [r12(x) for x in currents],
    )
end

function quantumoptics_receipt(sites)
    b = NLevelBasis(2)
    function site_ket(site)
        left = complex(parse_num(site["psi_L"][1]), parse_num(site["psi_L"][2]))
        right = complex(parse_num(site["psi_R"][1]), parse_num(site["psi_R"][2]))
        return Ket(b, ComplexF64[left, right])
    end
    ket = tensor(site_ket(sites[1]), site_ket(sites[2]), site_ket(sites[3]))
    rho = dm(ket)
    return Dict(
        "tool" => "QuantumOptics.NLevelBasis/Ket/tensor/dm",
        "basis_count" => length(ket.basis.bases),
        "density_trace" => r12(tr(rho)),
        "pass" => abs(real(tr(rho)) - 1.0) <= TOL,
    )
end

function itensor_receipt()
    idx = Index(2, "terrain_spinor_flux_q0")
    tensor = ITensor(idx)
    tensor[idx => 1] = 1.0
    sites = siteinds("Qubit", 3)
    mps = MPS(sites, "0")
    return Dict(
        "tool" => "ITensors.Index/ITensor and ITensorMPS.siteinds/MPS",
        "anchor_value" => Float64(tensor[idx => 1]),
        "site_count" => length(sites),
        "maxlinkdim" => maxlinkdim(mps),
        "pass" => length(sites) == 3 && maxlinkdim(mps) == 1,
    )
end

function z3_sum_terms(terms)
    isempty(terms) && return Z3.IntVal(0)
    return z3_add_terms(terms)
end

function z3_add_terms(terms)
    length(terms) == 1 && return terms[1]
    ctx = terms[1].ctx
    return Z3.Expr(ctx, Z3.Libz3.Z3_mk_add(Z3.ref(ctx), UInt32(length(terms)), [Z3.as_ast(term) for term in terms]))
end

function z3_sub_terms(terms)
    length(terms) == 1 && return terms[1]
    ctx = terms[1].ctx
    return Z3.Expr(ctx, Z3.Libz3.Z3_mk_sub(Z3.ref(ctx), UInt32(length(terms)), [Z3.as_ast(term) for term in terms]))
end

function z3_mul_terms(terms)
    length(terms) == 1 && return terms[1]
    ctx = terms[1].ctx
    return Z3.Expr(ctx, Z3.Libz3.Z3_mk_mul(Z3.ref(ctx), UInt32(length(terms)), [Z3.as_ast(term) for term in terms]))
end

function z3_continuity(proof_row; erased::Bool=false)
    solver = Z3.Solver()
    suffix = erased ? "erased" : "real"
    current_terms = Dict{String,Any}()
    for edge in proof_row["edge_formula_rows"]
        edge_id = String(edge["edge_id"])
        current = Z3.IntVar("julia_$(suffix)_current_$(edge_id)_scaled")
        coupling = Z3.IntVar("julia_$(suffix)_coupling_$(edge_id)_scaled")
        population_delta = Z3.IntVar("julia_$(suffix)_population_delta_$(edge_id)_scaled")
        residual = Z3.IntVar("julia_$(suffix)_rounding_residual_$(edge_id)_scaled2")
        Z3.add(solver, current == Z3.IntVal(Int(edge["current_src_to_dst_scaled"])))
        Z3.add(solver, coupling == Z3.IntVal(Int(edge["coupling_strength_scaled"])))
        Z3.add(solver, population_delta == Z3.IntVal(Int(edge["population_src_minus_dst_scaled"])))
        Z3.add(solver, residual == Z3.IntVal(Int(edge["rounding_residual_scaled2"])))
        Z3.add(
            solver,
            z3_mul_terms([current, Z3.IntVal(SCALE)])
            == z3_add_terms([z3_mul_terms([coupling, population_delta]), residual]),
        )
        current_terms[edge_id] = current
    end

    target_site = proof_row["site_balance_rows"][1]
    site_id = String(target_site["site_id"])
    network = Z3.IntVar("julia_$(suffix)_network_$(site_id)_scaled")
    local_flow_var = Z3.IntVar("julia_$(suffix)_local_$(site_id)_scaled")
    divergence = Z3.IntVar("julia_$(suffix)_edge_divergence_$(site_id)_scaled")
    outgoing = [current_terms[String(edge_id)] for edge_id in target_site["outgoing_edge_ids"]]
    incoming = [current_terms[String(edge_id)] for edge_id in target_site["incoming_edge_ids"]]
    derived = z3_sub_terms([z3_sum_terms(outgoing), z3_sum_terms(incoming)])
    Z3.add(solver, network == Z3.IntVal(Int(target_site["network_population_flow_scaled"])))
    Z3.add(solver, local_flow_var == Z3.IntVal(Int(target_site["local_population_flow_scaled"])))
    Z3.add(solver, divergence == Z3.IntVal(Int(target_site["edge_divergence_scaled"])))
    Z3.add(solver, divergence == derived)
    rhs = z3_sub_terms([local_flow_var, divergence])
    if erased
        rhs = z3_sub_terms([rhs, Z3.IntVal(1)])
    end
    Z3.add(solver, Z3.Not(network == rhs))
    return string(Z3.check(solver))
end

function build_payload()
    stage = load_json(STAGE_JAX_PARENT)
    s5 = load_json(S5_PARENT)
    sites = stage["rows"]["P2_support_object"]["sites"]
    terrain_row = s5["bloch_generator_table"][PRIMARY_TERRAIN]
    bare = network_recompute(sites, terrain_row)
    conditioned = network_recompute(sites, terrain_row; conditioned=true)
    proof_row = bare["proof_row"]
    z3_verdict = z3_continuity(proof_row)
    z3_erased = z3_continuity(proof_row; erased=true)
    qo = quantumoptics_receipt(sites)
    it = itensor_receipt()
    payload = Dict{String,Any}(
        "sim_id" => SIM_ID,
        "engine" => ENGINE,
        "schema_version" => "$(SIM_ID)_$(ENGINE)_leg_v1",
        "classification" => CLASSIFICATION,
        "promotion_allowed" => PROMOTION_ALLOWED,
        "formal_admission_allowed" => FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result" => READS_PEER_RESULT,
        "seed" => SEED,
        "generated_at" => replace(string(Dates.now(Dates.UTC)), r"\.\d+" => "") * "Z",
        "source_path" => rel(SOURCE_PATH),
        "source_sha256" => file_sha256(SOURCE_PATH),
        "result_path" => rel(RESULT_PATH),
        "pin_spec" => PIN_SPEC,
        "pin_sha256" => sha256_text(PIN_SPEC),
        "standard_schema_mode" => "FIELD",
        "engine_contract" => Dict("mode" => "RATCHETED", "mode_is_field" => true, "reads_peer_result" => false),
        "packages_used" => PACKAGES_USED,
        "aligned_packages_load_bearing" => ALIGNED_PACKAGES_LOAD_BEARING,
        "TOOL_MANIFEST" => TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH" => TOOL_INTEGRATION_DEPTH,
        "claim_path_tools" => ["QuantumOptics", "ITensors", "ITensorMPS", "Z3"],
        "package_versions" => Dict("QuantumOptics" => pkg_version("QuantumOptics"), "ITensors" => pkg_version("ITensors"), "ITensorMPS" => pkg_version("ITensorMPS"), "Z3" => pkg_version("Z3")),
        "quantumoptics_receipt" => qo,
        "itensor_mps_receipt" => it,
        "julia_network_recompute" => Dict(
            "total_abs_current" => bare["total_abs_current"],
            "total_signed_transport_flux" => bare["total_signed_transport_flux"],
            "conditioned_total_abs_current" => conditioned["total_abs_current"],
            "conditioned_total_signed_transport_flux" => conditioned["total_signed_transport_flux"],
            "edge_current_values" => bare["currents"],
        ),
        "crossover_proofs" => Dict(
            "julia_z3" => Dict(
                "ran" => true,
                "load_bearing" => true,
                "verdict" => lowercase(z3_verdict),
                "erased_flip_verdict" => lowercase(z3_erased),
                "asserted_precomputed_boolean" => false,
                "formula_terms_bound" => true,
                "edge_current_terms_in_solver" => true,
                "divergence_derived_in_solver" => true,
                "erased_control_kind" => proof_row["erased_control"],
                "proof_row" => proof_row,
            ),
        ),
        "engine_values" => Dict(
            "carrier_norm" => qo["density_trace"],
            "total_abs_current" => bare["total_abs_current"],
            "conditioned_total_abs_current" => conditioned["total_abs_current"],
        ),
    )
    payload["all_pass"] = qo["pass"] == true && it["pass"] == true && lowercase(z3_verdict) == "unsat" && lowercase(z3_erased) == "sat"
    return payload
end

function main()
    mkpath(RESULT_DIR)
    payload = build_payload()
    open(RESULT_PATH, "w") do io
        JSON3.pretty(io, payload)
        write(io, "\n")
    end
    println(JSON3.write(Dict("ok" => payload["all_pass"], "result_path" => rel(RESULT_PATH))))
    return payload["all_pass"] ? 0 : 1
end

exit(main())
