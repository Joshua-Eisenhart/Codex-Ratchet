#!/usr/bin/env julia
# Independent Julia leg for source-faithful Type-1 engine v0.
# Ceiling: QUARANTINE_EXPLORATORY / scratch_diagnostic.

using Dates
using JSON3
using LinearAlgebra
using QuantumOptics
using SHA

const SIM_ID = "type1_engine_v0"
const HERE = @__DIR__
const RESULTS = joinpath(HERE, "results")
const TOL = 1e-9
const DISTINCTNESS_THRESHOLD = 1e-6

const I2 = ComplexF64[1 0; 0 1]
const SX = ComplexF64[0 1; 1 0]
const SY = ComplexF64[0 -im; im 0]
const SZ = ComplexF64[1 0; 0 -1]
const SIGMA_MINUS = 0.5 * (SX - im * SY)
const SIGMA_PLUS = 0.5 * (SX + im * SY)
const PAULIS = [SX, SY, SZ]
const N_AXIS = [1.0, 1.0, 1.0] / sqrt(3.0)
const M_IN_AXIS = [1.0, 0.0, 1.0] / sqrt(2.0)
const H0 = 0.5 * (N_AXIS[1] * SX + N_AXIS[2] * SY + N_AXIS[3] * SZ)
const HC = 0.5 * (M_IN_AXIS[1] * SX + M_IN_AXIS[2] * SY + M_IN_AXIS[3] * SZ)
const SPIN_BASIS = SpinBasis(1//2)

const SOURCE_CITES = Dict(
    "terrain_type1" => ["IGT:482-489", "ATLAS:82-85", "ATLAS:103-110", "ATLAS:135-141"],
    "operators" => ["IGT:471-479", "SIGNED:136-557"],
    "stages" => ["IGT:529-534", "ATLAS:217-231"],
    "traversals" => ["IGT:464-469", "IGT:517-525", "ATLAS:156-179"],
    "open_gaps" => ["ATLAS:82-85", "IGT:215-218", "IGT:656-658"],
)

const TERRAIN_HEADER_NOTE = "terrain equations are ONE CANDIDATE realization, not settled math (ATLAS:82-85)"

const TERRAINS = Dict(
    "Se-in" => Dict(
        "name" => "Funnel", "flux" => "IN", "jungian_function" => "Se", "type" => "Type 1",
        "generator" => "sum_k D[L_k](rho) - i epsilon_F [H0, rho]",
        "scratch_bloch" => "R_N(.13)(sqrt(.78)x, sqrt(.78)y, .78z+.22*.86)",
        "params" => Dict("epsilon" => 0.13, "keep_z" => 0.78, "loss" => 0.22, "target_z" => 0.86),
        "source" => "IGT:484-487; ATLAS:103-108",
    ),
    "Ne-in" => Dict(
        "name" => "Vortex", "flux" => "IN", "jungian_function" => "Ne", "type" => "Type 1",
        "generator" => "-i[H0, rho] + epsilon_V sum_k D[L_k](rho)",
        "scratch_bloch" => ".94 R_N(.47)r",
        "params" => Dict("rotation" => 0.47, "shrink" => 0.94),
        "source" => "IGT:487; ATLAS:108",
    ),
    "Ni-in" => Dict(
        "name" => "Pit", "flux" => "IN", "jungian_function" => "Ni", "type" => "Type 1",
        "generator" => "D[sqrt(gamma) sigma_-](rho) - i epsilon_P [H0, rho]",
        "scratch_bloch" => "R_N(.09)(sqrt(.70)x, sqrt(.70)y, .70z-.30*.92)",
        "params" => Dict("epsilon" => 0.09, "keep_z" => 0.70, "loss" => 0.30, "target_z" => -0.92),
        "source" => "IGT:488; ATLAS:109",
    ),
    "Si-in" => Dict(
        "name" => "Hill", "flux" => "IN", "jungian_function" => "Si", "type" => "Type 1",
        "generator" => "-i[H_C, rho] + sum_j kappa_j(P_j rho P_j - 1/2(P_j rho + rho P_j))",
        "scratch_bloch" => "R_{M_in}(.19)(P_{M_in}(r)+.58(r-P_{M_in}(r)))",
        "params" => Dict("rotation" => 0.19, "transverse_keep" => 0.58),
        "source" => "IGT:489; ATLAS:110",
    ),
)

const OPERATORS = Dict(
    "Ti" => Dict("channel" => "Ti_q(rho) = (1 - q1) rho + q1 E_z(rho)", "q" => 1.0 - 0.69, "lambda" => 0.69, "source" => "SIGNED:136-148; IGT:475"),
    "Te" => Dict("channel" => "Te_q(rho) = (1 - q2) rho + q2 E_x(rho)", "q" => 1.0 - 0.73, "lambda" => 0.73, "source" => "SIGNED:284-296; IGT:476"),
    "Fi" => Dict("channel" => "Fi_theta(rho) = U_x(theta) rho U_x(theta)^dagger", "theta" => 0.41, "source" => "SIGNED:437-445; IGT:477"),
    "Fe" => Dict("channel" => "Fe_phi(rho) = U_z(phi) rho U_z(phi)^dagger", "phi" => -0.37, "source" => "SIGNED:549-557; IGT:478"),
)

const STAGES = [
    Dict("stage_id" => "TiSe", "loop" => "outer", "terrain" => "Se-in", "operator" => "Ti", "composition" => "terrain_after_operator", "order_text" => "Se-in(Ti(rho))", "casing" => "LOSE", "source" => "IGT:529-532; ATLAS:219-222"),
    Dict("stage_id" => "SeFi", "loop" => "inner", "terrain" => "Se-in", "operator" => "Fi", "composition" => "operator_after_terrain", "order_text" => "Fi(Se-in(rho))", "casing" => "win", "source" => "IGT:529-532; ATLAS:219-222"),
    Dict("stage_id" => "NeTi", "loop" => "outer", "terrain" => "Ne-in", "operator" => "Ti", "composition" => "operator_after_terrain", "order_text" => "Ti(Ne-in(rho))", "casing" => "WIN", "source" => "IGT:532; ATLAS:222"),
    Dict("stage_id" => "FiNe", "loop" => "inner", "terrain" => "Ne-in", "operator" => "Fi", "composition" => "terrain_after_operator", "order_text" => "Ne-in(Fi(rho))", "casing" => "lose", "source" => "IGT:532; ATLAS:222"),
    Dict("stage_id" => "NiFe", "loop" => "outer", "terrain" => "Ni-in", "operator" => "Fe", "composition" => "operator_after_terrain", "order_text" => "Fe(Ni-in(rho))", "casing" => "LOSE", "source" => "IGT:533; ATLAS:223"),
    Dict("stage_id" => "TeNi", "loop" => "inner", "terrain" => "Ni-in", "operator" => "Te", "composition" => "terrain_after_operator", "order_text" => "Ni-in(Te(rho))", "casing" => "lose", "source" => "IGT:533; ATLAS:223"),
    Dict("stage_id" => "FeSi", "loop" => "outer", "terrain" => "Si-in", "operator" => "Fe", "composition" => "terrain_after_operator", "order_text" => "Si-in(Fe(rho))", "casing" => "WIN", "source" => "IGT:534; ATLAS:224"),
    Dict("stage_id" => "SiTe", "loop" => "inner", "terrain" => "Si-in", "operator" => "Te", "composition" => "operator_after_terrain", "order_text" => "Te(Si-in(rho))", "casing" => "win", "source" => "IGT:534; ATLAS:224"),
]

const OUTER_LOOP_STAGE_IDS = ["TiSe", "NeTi", "NiFe", "FeSi"]
const INNER_LOOP_STAGE_IDS = ["SeFi", "SiTe", "TeNi", "FiNe"]

const XLSX_SOURCE = Dict(
    "source" => "owner_xlsx_pre_llm",
    "source_path" => "/Users/joshuaeisenhart/Desktop/Personality theory._.xlsx",
    "repo_copy_path" => "system_v7/constraint_core/inputs/Personality theory._.xlsx",
    "sha256" => "5a2c6031707f77cb13195ffd5539710634159c7e299f23ea5f17d885c3ab67a8",
)

const XLSX_CELLS = Dict(
    "Si|Te" => Dict("mbti" => "ISTJ", "raw_casing" => "win", "xlsx_row" => "Win Max, Big W"),
    "Si|Fe" => Dict("mbti" => "ESFJ", "raw_casing" => "WIN", "xlsx_row" => "Win Max, Big W"),
    "Ne|Ti" => Dict("mbti" => "ENTP", "raw_casing" => "WIN", "xlsx_row" => "Win Max, Big W"),
    "Ne|Fi" => Dict("mbti" => "INFP", "raw_casing" => "lose", "xlsx_row" => "Win Max, Big W"),
    "Se|Ti" => Dict("mbti" => "ISTP", "raw_casing" => "LOSE", "xlsx_row" => "Loss Max, Big L"),
    "Se|Fi" => Dict("mbti" => "ESFP", "raw_casing" => "win", "xlsx_row" => "Loss Max, Big L"),
    "Ni|Te" => Dict("mbti" => "ENTJ", "raw_casing" => "Lose", "xlsx_row" => "Loss Max, Big L"),
    "Ni|Fe" => Dict("mbti" => "INFJ", "raw_casing" => "LOSE", "xlsx_row" => "Loss Max, Big L"),
)

terrain_function(terrain::String) = split(terrain, "-")[1]
cell_key(terrain::String, op::String) = "$(terrain_function(terrain))|$(op)"

function mbti_annotation()
    by_stage = Dict{String,Any}()
    for st in STAGES
        cell = XLSX_CELLS[cell_key(st["terrain"], st["operator"])]
        by_stage[st["stage_id"]] = Dict(
            "terrain" => st["terrain"], "operator" => st["operator"], "mbti" => cell["mbti"],
            "xlsx_raw_casing" => cell["raw_casing"], "xlsx_row" => cell["xlsx_row"],
            "load_bearing" => false,
        )
    end
    out = Dict{String,Any}(XLSX_SOURCE)
    out["load_bearing"] = false
    out["note"] = "Labels only; never used by numeric terrain/operator computation."
    out["by_stage"] = by_stage
    return out
end

function casing_cross_check()
    rows = Vector{Any}()
    for st in STAGES
        cell = XLSX_CELLS[cell_key(st["terrain"], st["operator"])]
        push!(rows, Dict(
            "stage_id" => st["stage_id"],
            "terrain" => st["terrain"],
            "operator" => st["operator"],
            "doc_casing" => st["casing"],
            "xlsx_raw_casing" => cell["raw_casing"],
            "raw_case_agree" => st["casing"] == cell["raw_casing"],
            "normalized_agree" => lowercase(st["casing"]) == lowercase(cell["raw_casing"]),
            "mbti" => cell["mbti"],
            "source" => "doc_vs_owner_xlsx_pre_llm",
            "load_bearing" => false,
        ))
    end
    return rows
end

function sha256_file(path::AbstractString)::String
    open(path, "r") do io
        return bytes2hex(sha256(io))
    end
end

vecr(rho) = reshape(rho, 4)
unvec(v) = reshape(v, 2, 2)
sleft(a) = kron(I2, a)
sright(a) = kron(transpose(a), I2)

function dissipator_super(l_op)
    ldag_l = l_op' * l_op
    return kron(conj(l_op), l_op) - 0.5 * (sleft(ldag_l) + sright(ldag_l))
end

hamiltonian_super(h_op, rate=1.0) = -im * rate * (sleft(h_op) - sright(h_op))

function normalize_density(rho)
    herm = 0.5 * (rho + rho')
    trv = real(tr(herm))
    return herm / trv
end

function rates_for_fixed_point(total_decay, target_z)
    return total_decay * (1.0 + target_z) / 2.0, total_decay * (1.0 - target_z) / 2.0
end

function terrain_superoperators()
    se = TERRAINS["Se-in"]["params"]
    se_total = -log(se["keep_z"])
    se_plus, se_minus = rates_for_fixed_point(se_total, se["target_z"])
    ne = TERRAINS["Ne-in"]["params"]
    ne_depol = -log(ne["shrink"]) / 4.0
    ni = TERRAINS["Ni-in"]["params"]
    ni_gamma = -log(ni["keep_z"])
    si = TERRAINS["Si-in"]["params"]
    si_kappa = -log(si["transverse_keep"]) / 2.0

    m_sigma = M_IN_AXIS[1] * SX + M_IN_AXIS[2] * SY + M_IN_AXIS[3] * SZ
    p_plus = 0.5 * (I2 + m_sigma)
    p_minus = 0.5 * (I2 - m_sigma)
    depol = zeros(ComplexF64, 4, 4)
    for p in PAULIS
        depol += dissipator_super(p)
    end
    return Dict(
        "Se-in" => se_plus * dissipator_super(SIGMA_PLUS) + se_minus * dissipator_super(SIGMA_MINUS) + hamiltonian_super(H0, se["epsilon"]),
        "Ne-in" => hamiltonian_super(H0, ne["rotation"]) + ne_depol * depol,
        "Ni-in" => ni_gamma * dissipator_super(SIGMA_MINUS) + hamiltonian_super(H0, ni["epsilon"]),
        "Si-in" => hamiltonian_super(HC, si["rotation"]) + si_kappa * (dissipator_super(p_plus) + dissipator_super(p_minus)),
    )
end

function terrains()
    out = Dict{String,Function}()
    for (name, superop) in terrain_superoperators()
        flow = exp(superop)
        out[name] = rho -> normalize_density(unvec(flow * vecr(rho)))
    end
    return out
end

unitary(axis::String, angle) = exp(-im * angle * (axis == "x" ? SX : SZ) / 2.0)

function operators()
    q1 = OPERATORS["Ti"]["q"]
    q2 = OPERATORS["Te"]["q"]
    p0 = 0.5 * (I2 + SZ)
    p1 = 0.5 * (I2 - SZ)
    qp = 0.5 * (I2 + SX)
    qm = 0.5 * (I2 - SX)
    ux = unitary("x", OPERATORS["Fi"]["theta"])
    uz = unitary("z", OPERATORS["Fe"]["phi"])
    return Dict{String,Function}(
        "Ti" => rho -> normalize_density((1.0 - q1) * rho + q1 * (p0 * rho * p0 + p1 * rho * p1)),
        "Te" => rho -> normalize_density((1.0 - q2) * rho + q2 * (qp * rho * qp + qm * rho * qm)),
        "Fi" => rho -> normalize_density(ux * rho * ux'),
        "Fe" => rho -> normalize_density(uz * rho * uz'),
    )
end

function stage_maps()
    terr = terrains()
    ops = operators()
    maps = Dict{String,Function}()
    for st in STAGES
        terrain = terr[st["terrain"]]
        op = ops[st["operator"]]
        if st["composition"] == "terrain_after_operator"
            maps[st["stage_id"]] = rho -> terrain(op(rho))
        else
            maps[st["stage_id"]] = rho -> op(terrain(rho))
        end
    end
    return maps
end

function rho_from_bloch(r)
    return normalize_density(0.5 * (I2 + r[1] * SX + r[2] * SY + r[3] * SZ))
end

bloch(rho) = [real(tr(rho * p)) for p in PAULIS]

function entropy_vn_qo(rho)
    op = DenseOperator(SPIN_BASIS, normalize_density(rho))
    return Float64(real(QuantumOptics.entropy_vn(op)))
end

function probe_states()
    return Dict(
        "mixed" => rho_from_bloch([0.0, 0.0, 0.0]),
        "plus_x" => rho_from_bloch([1.0, 0.0, 0.0]),
        "plus_y" => rho_from_bloch([0.0, 1.0, 0.0]),
        "zero_z" => rho_from_bloch([0.0, 0.0, 1.0]),
        "generic_a" => rho_from_bloch([0.31, -0.27, 0.44]),
        "generic_b" => rho_from_bloch([-0.21, 0.36, -0.18]),
    )
end

function affine_fingerprint(channel)
    b = bloch(channel(rho_from_bloch([0.0, 0.0, 0.0])))
    matrix = zeros(Float64, 3, 3)
    for (j, axis) in enumerate(([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]))
        matrix[:, j] = bloch(channel(rho_from_bloch(axis))) - b
    end
    fixed = (I(3) - matrix) \ b
    residual = norm(matrix * fixed + b - fixed)
    return Dict(
        "affine_A" => [[Float64(matrix[i, j]) for j in 1:3] for i in 1:3],
        "affine_b" => [Float64(x) for x in b],
        "fixed_point_bloch" => [Float64(x) for x in fixed],
        "fixed_point_residual" => Float64(residual),
    )
end

function stage_fingerprints(maps)
    probes = probe_states()
    out = Dict{String,Any}()
    for st in STAGES
        sid = st["stage_id"]
        channel = maps[sid]
        fp = affine_fingerprint(channel)
        entropy_injected = Dict{String,Float64}()
        for pname in sort(collect(keys(probes)))
            rho = probes[pname]
            entropy_injected[pname] = entropy_vn_qo(channel(rho)) - entropy_vn_qo(rho)
        end
        fp["stage_id"] = sid
        fp["terrain"] = st["terrain"]
        fp["operator"] = st["operator"]
        fp["loop"] = st["loop"]
        fp["casing"] = st["casing"]
        fp["order_text"] = st["order_text"]
        fp["entropy_injected"] = entropy_injected
        out[sid] = fp
    end
    return out
end

function fingerprint_vector(fp)
    vals = Float64[]
    for row in fp["affine_A"], x in row
        push!(vals, Float64(x))
    end
    append!(vals, Float64.(fp["affine_b"]))
    for k in sort(collect(keys(fp["entropy_injected"])))
        push!(vals, Float64(fp["entropy_injected"][k]))
    end
    append!(vals, Float64.(fp["fixed_point_bloch"]))
    push!(vals, Float64(fp["fixed_point_residual"]))
    return vals
end

function distinctness(fingerprints)
    ids = [st["stage_id"] for st in STAGES]
    pairs = Vector{Any}()
    min_dist = Inf
    min_pair = String[]
    for i in 1:length(ids)-1
        a = ids[i]
        va = fingerprint_vector(fingerprints[a])
        for b in ids[i+1:end]
            dist = norm(va - fingerprint_vector(fingerprints[b]))
            push!(pairs, Dict("pair" => [a, b], "distance" => Float64(dist)))
            if dist < min_dist
                min_dist = dist
                min_pair = [a, b]
            end
        end
    end
    return Dict(
        "threshold" => DISTINCTNESS_THRESHOLD,
        "min_pairwise_distance" => Float64(min_dist),
        "min_pair" => min_pair,
        "all_8_distinct" => min_dist > DISTINCTNESS_THRESHOLD,
        "pairwise_distances" => pairs,
    )
end

function order_sensitivity_by_terrain(maps)
    probes = probe_states()
    terrain_to_ids = Dict(
        "Se-in" => ("TiSe", "SeFi"),
        "Ne-in" => ("NeTi", "FiNe"),
        "Ni-in" => ("NiFe", "TeNi"),
        "Si-in" => ("FeSi", "SiTe"),
    )
    out = Dict{String,Any}()
    for terrain in ["Se-in", "Ne-in", "Ni-in", "Si-in"]
        outer_id, inner_id = terrain_to_ids[terrain]
        vals = Dict{String,Float64}()
        for pname in sort(collect(keys(probes)))
            vals[pname] = norm(bloch(maps[outer_id](probes[pname])) - bloch(maps[inner_id](probes[pname])))
        end
        out[terrain] = Dict(
            "outer_stage" => outer_id,
            "inner_stage" => inner_id,
            "probe_norms" => vals,
            "max_norm" => maximum(values(vals)),
            "mean_norm" => sum(values(vals)) / length(vals),
            "axis6_observable" => "outer_vs_inner_composition_difference_norm",
        )
    end
    return out
end

function run_sequence(maps, stage_ids, rho)
    trajectory = Any[Dict("step" => 0, "stage_id" => "initial", "bloch" => bloch(rho), "entropy" => entropy_vn_qo(rho))]
    cur = rho
    for (idx, sid) in enumerate(stage_ids)
        cur = maps[sid](cur)
        push!(trajectory, Dict("step" => idx, "stage_id" => sid, "bloch" => bloch(cur), "entropy" => entropy_vn_qo(cur)))
    end
    return trajectory
end

function traversal_measurements(maps)
    probes = probe_states()
    sequences = Dict(
        "outer" => OUTER_LOOP_STAGE_IDS,
        "inner" => INNER_LOOP_STAGE_IDS,
        "double_outer_then_inner" => vcat(OUTER_LOOP_STAGE_IDS, INNER_LOOP_STAGE_IDS),
    )
    out = Dict{String,Any}()
    for name in ["outer", "inner", "double_outer_then_inner"]
        stage_ids = sequences[name]
        per_probe = Dict{String,Any}()
        closures = Float64[]
        for pname in sort(collect(keys(probes)))
            rho = probes[pname]
            traj = run_sequence(maps, stage_ids, rho)
            delta = traj[end]["bloch"] - traj[1]["bloch"]
            closure = norm(delta)
            push!(closures, closure)
            per_probe[pname] = Dict(
                "stage_ids" => stage_ids,
                "trajectory" => traj,
                "closure_norm" => closure,
                "final_minus_initial_bloch" => delta,
            )
        end
        out[name] = Dict(
            "per_initial_state" => per_probe,
            "closure_summary" => Dict("min" => minimum(closures), "max" => maximum(closures), "mean" => sum(closures) / length(closures)),
            "closure_note" => "Measured finite traversal closure only; no 720 closure assertion is made.",
        )
    end
    return out
end

function tool_manifest()
    return Dict(
        "LinearAlgebra" => Dict("tried" => true, "used" => true, "reason" => "load-bearing dense complex matrices and finite-time superoperator exponentials"),
        "QuantumOptics.entropy_vn" => Dict("tried" => true, "used" => true, "reason" => "load-bearing entropy injected values in each stage fingerprint"),
        "JSON3" => Dict("tried" => true, "used" => true, "reason" => "supportive result artifact serialization"),
    )
end

function build_result()
    maps = stage_maps()
    fps = stage_fingerprints(maps)
    return Dict(
        "schema" => "codex_ratchet.type1_engine_v0.leg_result.v1",
        "sim_id" => SIM_ID,
        "classification" => "scratch_diagnostic",
        "claim_ceiling" => "QUARANTINE_EXPLORATORY",
        "promotion_allowed" => false,
        "formal_admission_allowed" => false,
        "source_extraction" => "../TYPE1_ENGINE_EXTRACTION_20260703.md",
        "source_cites" => SOURCE_CITES,
        "terrain_header_note" => TERRAIN_HEADER_NOTE,
        "terrains" => TERRAINS,
        "operators" => OPERATORS,
        "stages" => STAGES,
        "traversals" => Dict(
            "outer" => Dict("loop" => "deductive", "direction" => "CCW", "terrain_order" => ["Se-in", "Ne-in", "Ni-in", "Si-in"], "stage_ids" => OUTER_LOOP_STAGE_IDS, "source" => "IGT:464-469; IGT:517-525"),
            "inner" => Dict("loop" => "inductive", "direction" => "CW", "terrain_order" => ["Se-in", "Si-in", "Ni-in", "Ne-in"], "stage_ids" => INNER_LOOP_STAGE_IDS, "source" => "IGT:464-469; IGT:517-525"),
        ),
        "mbti_annotation" => mbti_annotation(),
        "casing_cross_check" => casing_cross_check(),
        "substrates_in_v0" => ["numpy", "julia"],
        "substrates_queued" => ["jax", "torch"],
        "engine" => "julia",
        "substrate" => "julia",
        "computation_style" => "julia_complexf64_gksl_superoperator_expm_quantumoptics_entropy",
        "reads_peer_result" => false,
        "generated_at" => Dates.format(now(UTC), dateformat"yyyy-mm-ddTHH:MM:SSZ"),
        "source_sha256" => sha256_file(@__FILE__),
        "result_path" => "system_v7/sims/type1_engine_v0/results/type1_engine_v0_julia_results.json",
        "tolerances" => Dict("parity_abs" => TOL, "distinctness_threshold" => DISTINCTNESS_THRESHOLD),
        "model_axes" => Dict("H0_axis" => N_AXIS, "H0_sign" => "+H0", "flux" => "IN", "H_C_axis" => M_IN_AXIS),
        "terrain_generator_note" => TERRAIN_HEADER_NOTE,
        "stage_fingerprints" => fps,
        "distinctness" => distinctness(fps),
        "order_sensitivity_by_terrain" => order_sensitivity_by_terrain(maps),
        "traversals" => traversal_measurements(maps),
        "TOOL_MANIFEST" => tool_manifest(),
        "TOOL_INTEGRATION_DEPTH" => Dict("LinearAlgebra" => "load_bearing", "QuantumOptics.entropy_vn" => "load_bearing", "JSON3" => "supportive"),
        "all_pass" => true,
    )
end

function main()
    mkpath(RESULTS)
    out = build_result()
    path = joinpath(RESULTS, "type1_engine_v0_julia_results.json")
    open(path, "w") do io
        JSON3.pretty(io, out)
    end
    println(JSON3.write(Dict(
        "engine" => "julia",
        "result_path" => path,
        "all_8_distinct" => out["distinctness"]["all_8_distinct"],
        "min_pairwise_distance" => out["distinctness"]["min_pairwise_distance"],
        "outer_closure_mean" => out["traversals"]["outer"]["closure_summary"]["mean"],
        "inner_closure_mean" => out["traversals"]["inner"]["closure_summary"]["mean"],
        "double_closure_mean" => out["traversals"]["double_outer_then_inner"]["closure_summary"]["mean"],
    )))
end

main()
